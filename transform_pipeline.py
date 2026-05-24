#!/usr/bin/env python3
"""
Data Transformation Pipeline
Handles Bronze → Silver → Gold transformation
Can be run standalone or as part of a Databricks job/DLT pipeline
"""
import os
import sys
from datetime import datetime
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

from databricks.sql import connect

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

def transform_pipeline():
    """Execute the transformation from Bronze → Silver → Gold"""
    try:
        conn = connect(
            server_hostname=host,
            http_path=http_path,
            personal_access_token=token
        )
        cursor = conn.cursor()

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting data transformation pipeline...")

        # ======================================================================
        # SILVER LAYER: Clean and transform Bronze data
        # ======================================================================

        print("  [1/3] Transforming patients to Silver layer...")
        cursor.execute("""
        CREATE OR REPLACE TABLE healthcare_equity_silver.patients_processed AS
        SELECT
            patient_id,
            gender,
            race,
            sexual_orientation,
            age,
            insurance_type,
            sofa_score,
            cci_score,
            ses_quintile,
            CASE
                WHEN sofa_score >= 15 THEN 'HIGH'
                WHEN sofa_score >= 10 THEN 'MEDIUM'
                ELSE 'LOW'
            END as risk_level,
            CASE
                WHEN age < 30 THEN '18-29'
                WHEN age < 45 THEN '30-44'
                WHEN age < 65 THEN '45-64'
                ELSE '65+'
            END as age_group,
            CURRENT_TIMESTAMP() as processed_at
        FROM healthcare_equity_bronze.patients
        WHERE patient_id IS NOT NULL
        """)

        print("  [2/3] Transforming decisions to Silver layer...")
        cursor.execute("""
        CREATE OR REPLACE TABLE healthcare_equity_silver.decisions_processed AS
        SELECT
            decision_id,
            patient_id,
            scenario_type,
            decision,
            CASE WHEN decision = 'Recommended' THEN 1 ELSE 0 END as decision_flag,
            decision_date,
            CURRENT_TIMESTAMP() as processed_at
        FROM healthcare_equity_bronze.decisions
        WHERE decision_id IS NOT NULL AND patient_id IS NOT NULL
        """)

        # Outcomes transformation (if table exists)
        try:
            print("  [3/3] Transforming outcomes to Silver layer...")
            cursor.execute("""
            CREATE OR REPLACE TABLE healthcare_equity_silver.outcomes_processed AS
            SELECT
                outcome_id,
                decision_id,
                patient_id,
                outcome_type,
                outcome_date,
                CURRENT_TIMESTAMP() as processed_at
            FROM healthcare_equity_bronze.outcomes
            WHERE outcome_id IS NOT NULL
            """)
        except:
            print("  [3/3] Outcomes table not found - skipping")

        # ======================================================================
        # GOLD LAYER: Aggregated analytics and metrics
        # ======================================================================

        print("  [4/4] Creating bias metrics aggregation...")
        cursor.execute("""
        CREATE OR REPLACE TABLE healthcare_equity_gold.bias_metrics AS
        SELECT
            d.scenario_type,
            p.race,
            p.gender,
            COUNT(DISTINCT d.decision_id) as total_decisions,
            SUM(d.decision_flag) as approved_count,
            ROUND(SUM(d.decision_flag) / COUNT(*) * 100, 2) as approval_rate,
            COUNT(DISTINCT p.patient_id) as unique_patients,
            ROUND(AVG(p.sofa_score), 2) as avg_severity,
            MIN(d.decision_date) as first_decision_date,
            MAX(d.decision_date) as last_decision_date,
            CURRENT_TIMESTAMP() as calculated_at
        FROM healthcare_equity_silver.decisions_processed d
        JOIN healthcare_equity_silver.patients_processed p ON d.patient_id = p.patient_id
        GROUP BY d.scenario_type, p.race, p.gender
        """)

        print("  [5/4] Creating equity dashboard metrics...")
        cursor.execute("""
        CREATE OR REPLACE TABLE healthcare_equity_gold.equity_dashboard AS
        WITH patient_stats AS (
            SELECT
                COUNT(*) as total_patients,
                ROUND(100.0 * SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_female,
                ROUND(100.0 * SUM(CASE WHEN race = 'Black' THEN 1 ELSE 0 END) / COUNT(*), 2) as pct_black,
                ROUND(AVG(sofa_score), 2) as avg_severity
            FROM healthcare_equity_silver.patients_processed
        ),
        decision_stats AS (
            SELECT
                COUNT(*) as total_decisions,
                ROUND(100.0 * SUM(decision_flag) / COUNT(*), 2) as approval_rate,
                COUNT(DISTINCT scenario_type) as scenarios_analyzed
            FROM healthcare_equity_silver.decisions_processed
        )
        SELECT
            ps.total_patients,
            ds.total_decisions,
            ps.avg_severity as avg_clinical_severity,
            ps.pct_female,
            ps.pct_black,
            ds.approval_rate as overall_approval_rate,
            ds.scenarios_analyzed,
            CURRENT_TIMESTAMP() as last_updated
        FROM patient_stats ps
        CROSS JOIN decision_stats ds
        """)

        print("  [6/4] Creating disparate impact analysis...")
        cursor.execute("""
        CREATE OR REPLACE TABLE healthcare_equity_gold.disparate_impact AS
        SELECT
            scenario_type,
            ROUND(AVG(CASE WHEN race = 'Black' THEN approval_rate ELSE NULL END), 2) as black_approval_rate,
            ROUND(AVG(CASE WHEN race = 'White' THEN approval_rate ELSE NULL END), 2) as white_approval_rate,
            ROUND(
                AVG(CASE WHEN race = 'Black' THEN approval_rate ELSE NULL END) /
                AVG(CASE WHEN race = 'White' THEN approval_rate ELSE NULL END),
                4
            ) as disparate_impact_ratio,
            CASE
                WHEN ROUND(
                    AVG(CASE WHEN race = 'Black' THEN approval_rate ELSE NULL END) /
                    AVG(CASE WHEN race = 'White' THEN approval_rate ELSE NULL END),
                    4
                ) < 0.80 THEN 'FLAGGED'
                ELSE 'OK'
            END as eighty_percent_rule_status,
            CURRENT_TIMESTAMP() as calculated_at
        FROM healthcare_equity_gold.bias_metrics
        GROUP BY scenario_type
        """)

        print("  [7/4] Creating provider accountability scorecard...")
        cursor.execute("""
        CREATE OR REPLACE TABLE healthcare_equity_gold.provider_accountability AS
        SELECT
            scenario_type,
            COUNT(DISTINCT race) as demographic_groups_analyzed,
            ROUND(AVG(approval_rate), 2) as avg_approval_rate,
            ROUND(MAX(approval_rate), 2) as highest_approval_rate,
            ROUND(MIN(approval_rate), 2) as lowest_approval_rate,
            ROUND(MAX(approval_rate) - MIN(approval_rate), 2) as equity_gap,
            SUM(total_decisions) as total_decisions_analyzed,
            CURRENT_TIMESTAMP() as calculated_at
        FROM healthcare_equity_gold.bias_metrics
        GROUP BY scenario_type
        """)

        conn.close()

        print(f"  [SUCCESS] Data transformation completed!")
        print(f"  Bronze > Silver > Gold pipeline finished at {datetime.now().strftime('%H:%M:%S')}")
        return True

    except Exception as e:
        print(f"  [ERROR] {str(e)[:300]}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = transform_pipeline()
    sys.exit(0 if success else 1)
