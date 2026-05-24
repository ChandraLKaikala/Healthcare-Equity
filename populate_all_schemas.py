#!/usr/bin/env python3
"""
Populate Silver and Gold schemas from Bronze data
One session to avoid OAuth issues
"""
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

from databricks.sql import connect

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

print("Connecting to Databricks...")
conn = connect(
    server_hostname=host,
    http_path=http_path,
    personal_access_token=token
)
cursor = conn.cursor()

# SILVER LAYER - Transform Bronze to Silver
print("\n[SILVER LAYER] Creating silver tables from bronze...")

# Silver patients
print("  Creating silver_patients_processed...")
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
print("  [OK] silver_patients_processed")

# Silver decisions
print("  Creating silver_decisions_processed...")
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
WHERE decision_id IS NOT NULL
""")
print("  [OK] silver_decisions_processed")

# Silver outcomes
print("  Creating silver_outcomes_processed...")
cursor.execute("""
CREATE OR REPLACE TABLE healthcare_equity_silver.outcomes_processed AS
SELECT
    outcome_id,
    patient_id,
    decision_id,
    outcome_type,
    thirty_day_readmission,
    in_hospital_mortality,
    CASE
        WHEN outcome_type = 'Success' THEN 1
        WHEN outcome_type = 'Complication' THEN 0
        ELSE 0
    END as positive_outcome,
    outcome_date,
    CURRENT_TIMESTAMP() as processed_at
FROM healthcare_equity_bronze.outcomes
WHERE outcome_id IS NOT NULL
""")
print("  [OK] silver_outcomes_processed")

# GOLD LAYER - Analytics aggregations
print("\n[GOLD LAYER] Creating gold analytics tables...")

# Gold: Bias metrics by scenario and race
print("  Creating gold_bias_metrics...")
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
print("  [OK] gold_bias_metrics")

# Gold: Disparate Impact Ratios
print("  Creating gold_disparate_impact...")
cursor.execute("""
CREATE OR REPLACE TABLE healthcare_equity_gold.disparate_impact AS
SELECT
    scenario_type,
    race,
    approval_rate,
    ROUND(approval_rate / MAX(approval_rate) OVER (PARTITION BY scenario_type) * 100, 2) as dir_percentage,
    CASE
        WHEN approval_rate / MAX(approval_rate) OVER (PARTITION BY scenario_type) < 0.80 THEN 'CRITICAL'
        WHEN approval_rate / MAX(approval_rate) OVER (PARTITION BY scenario_type) < 0.90 THEN 'HIGH'
        ELSE 'NORMAL'
    END as dir_severity,
    CURRENT_TIMESTAMP() as calculated_at
FROM healthcare_equity_gold.bias_metrics
""")
print("  [OK] gold_disparate_impact")

# Gold: Provider accountability
print("  Creating gold_provider_accountability...")
cursor.execute("""
CREATE OR REPLACE TABLE healthcare_equity_gold.provider_accountability AS
SELECT
    p.race,
    p.gender,
    p.age_group,
    COUNT(DISTINCT d.decision_id) as total_decisions,
    SUM(d.decision_flag) as approved_decisions,
    ROUND(SUM(d.decision_flag) / COUNT(*) * 100, 2) as approval_pct,
    ROUND(AVG(o.thirty_day_readmission), 3) as readmission_rate,
    ROUND(AVG(o.in_hospital_mortality), 3) as mortality_rate,
    CURRENT_TIMESTAMP() as updated_at
FROM healthcare_equity_silver.patients_processed p
LEFT JOIN healthcare_equity_silver.decisions_processed d ON p.patient_id = d.patient_id
LEFT JOIN healthcare_equity_silver.outcomes_processed o ON d.decision_id = o.decision_id
GROUP BY p.race, p.gender, p.age_group
""")
print("  [OK] gold_provider_accountability")

# Gold: Daily summary dashboard
print("  Creating gold_equity_dashboard...")
cursor.execute("""
CREATE OR REPLACE TABLE healthcare_equity_gold.equity_dashboard AS
SELECT
    COUNT(DISTINCT p.patient_id) as total_patients,
    COUNT(DISTINCT d.decision_id) as total_decisions,
    ROUND(AVG(p.sofa_score), 2) as avg_clinical_severity,
    ROUND(SUM(CASE WHEN p.gender = 'F' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as pct_female,
    ROUND(SUM(CASE WHEN p.race = 'Black' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as pct_black,
    ROUND(SUM(CASE WHEN p.race = 'Hispanic' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as pct_hispanic,
    ROUND(SUM(d.decision_flag) / COUNT(d.decision_id) * 100, 2) as overall_approval_rate,
    COUNT(DISTINCT d.scenario_type) as scenarios_analyzed,
    CURRENT_TIMESTAMP() as last_updated
FROM healthcare_equity_silver.patients_processed p
LEFT JOIN healthcare_equity_silver.decisions_processed d ON p.patient_id = d.patient_id
""")
print("  [OK] gold_equity_dashboard")

# Verify data
print("\n[VERIFICATION] Checking all schemas...")

print("\n[BRONZE]")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.patients")
print(f"  Patients: {cursor.fetchone()[0]:,}")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.decisions")
print(f"  Decisions: {cursor.fetchone()[0]:,}")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.outcomes")
print(f"  Outcomes: {cursor.fetchone()[0]:,}")

print("\n[SILVER]")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed")
print(f"  Patients: {cursor.fetchone()[0]:,}")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.decisions_processed")
print(f"  Decisions: {cursor.fetchone()[0]:,}")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.outcomes_processed")
print(f"  Outcomes: {cursor.fetchone()[0]:,}")

print("\n[GOLD]")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.bias_metrics")
print(f"  Bias Metrics: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.disparate_impact")
print(f"  Disparate Impact: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.provider_accountability")
print(f"  Provider Accountability: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.equity_dashboard")
print(f"  Dashboard Metrics: {cursor.fetchone()[0]}")

conn.close()

print("\n" + "="*60)
print("SUCCESS: All schemas populated!")
print("="*60)
print("\nSummary:")
print("  Bronze: 1M patients + 1.5M decisions + 800k outcomes")
print("  Silver: Cleaned and processed data")
print("  Gold: Analytics-ready aggregations")
print("\nReady for dashboard and analysis!")
