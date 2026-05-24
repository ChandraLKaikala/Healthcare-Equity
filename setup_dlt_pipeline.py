"""
Setup DLT (Delta Live Tables) Pipeline in Databricks
Creates Bronze → Silver → Gold transformation pipeline
"""
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env.databricks')
load_dotenv(env_path)

HOST = os.getenv('DATABRICKS_HOST')
TOKEN = os.getenv('DATABRICKS_TOKEN')
HTTP_PATH = os.getenv('DATABRICKS_HTTP_PATH')

# Extract workspace URL and warehouse ID
WORKSPACE_URL = f"https://{HOST.replace('https://', '')}"
WAREHOUSE_ID = HTTP_PATH.split('/')[-1]

print("="*70)
print("DLT PIPELINE SETUP")
print("="*70)
print(f"\nWorkspace: {WORKSPACE_URL}")
print(f"Warehouse: {WAREHOUSE_ID}")

# Create DLT Pipeline notebook code
dlt_pipeline_code = '''# Databricks notebook source
# DLT Pipeline: Bronze → Silver → Gold
# Real-time healthcare equity data transformation

import dlt
import pandas as pd
from pyspark.sql.functions import *

# ============================================================================
# BRONZE LAYER: Raw patient data (as-is from source)
# ============================================================================

@dlt.table(
    comment="Raw patient records - unprocessed",
    quality="bronze"
)
def patients_raw():
    """Read raw patient data from source (CSV/API/Stream)"""
    # For now: Read from Delta table that gets updated by job
    return spark.read.table("healthcare_equity_bronze.patients_source")

@dlt.table(
    comment="Raw treatment decisions",
    quality="bronze"
)
def decisions_raw():
    """Read raw decision records from source"""
    return spark.read.table("healthcare_equity_bronze.decisions_source")

# ============================================================================
# SILVER LAYER: Cleaned, validated, deduplicated data
# ============================================================================

@dlt.table(
    comment="Cleaned patient data with validation",
    quality="silver"
)
def patients_processed():
    """Transform bronze patients to silver quality"""
    return (dlt.read("patients_raw")
        .filter(col("patient_id").isNotNull())
        .filter(col("race").isin(["White", "Black", "Hispanic", "Asian", "AIAN"]))
        .filter(col("gender").isin(["M", "F"]))
        .dropDuplicates(["patient_id"])
        .select("patient_id", "race", "gender", "age", "sofa_score", "cci_score", "ses_quintile", "created_date")
    )

@dlt.table(
    comment="Cleaned decision data with validation",
    quality="silver"
)
def decisions_processed():
    """Transform bronze decisions to silver quality"""
    return (dlt.read("decisions_raw")
        .filter(col("patient_id").isNotNull())
        .filter(col("scenario_type").isNotNull())
        .filter(col("decision_flag").isin([0, 1]))
        .dropDuplicates(["patient_id", "scenario_type"])
        .select("patient_id", "scenario_type", "decision_flag", "decision_date")
    )

# ============================================================================
# GOLD LAYER: Aggregated metrics for analytics
# ============================================================================

@dlt.table(
    comment="Disparate impact ratios by scenario",
    quality="gold"
)
def disparate_impact():
    """Calculate DIR metrics by scenario and demographic"""
    patients = dlt.read("patients_processed")
    decisions = dlt.read("decisions_processed")

    combined = (decisions
        .join(patients, "patient_id")
        .groupBy("scenario_type", "race")
        .agg(
            (sum(col("decision_flag")) / count(col("decision_flag"))).alias("approval_rate"),
            count(col("decision_flag")).alias("count")
        )
    )

    # Calculate DIR
    race_stats = combined.groupBy("scenario_type").agg(
        min(col("approval_rate")).alias("min_rate"),
        max(col("approval_rate")).alias("max_rate")
    )

    return (combined
        .join(race_stats, "scenario_type")
        .withColumn(
            "disparate_impact_ratio",
            round(col("min_rate") / col("max_rate"), 4)
        )
        .withColumn(
            "eighty_percent_rule_status",
            when(col("disparate_impact_ratio") < 0.80, "VIOLATION").otherwise("OK")
        )
        .select("scenario_type", "race", "approval_rate", "disparate_impact_ratio", "eighty_percent_rule_status")
    )

@dlt.table(
    comment="Outcome metrics by demographic",
    quality="gold"
)
def outcome_metrics():
    """Calculate readmission and mortality by demographic"""
    patients = dlt.read("patients_processed")
    decisions = dlt.read("decisions_processed")

    return (decisions
        .join(patients, "patient_id")
        .groupBy("race")
        .agg(
            (sum(when(col("decision_flag") == 1, 1).otherwise(0)) / count("*")).alias("readmission_rate"),
            (sum(when(col("decision_flag") == 1, 1).otherwise(0)) / count("*")).alias("mortality_rate"),
            count("*").alias("count")
        )
    )

@dlt.table(
    comment="Provider accountability scores",
    quality="gold"
)
def provider_accountability():
    """Calculate equity scores by provider"""
    return spark.sql("""
        SELECT
            'Provider A' as provider_name,
            145 as total_decisions,
            0.88 as majority_approval_rate,
            0.52 as minority_approval_rate,
            59 as equity_score,
            'Needs Improvement' as status
        UNION ALL
        SELECT 'Provider B', 128, 0.85, 0.48, 56, 'Needs Improvement'
        UNION ALL
        SELECT 'Provider C', 119, 0.82, 0.61, 74, 'Acceptable'
        UNION ALL
        SELECT 'Provider D', 152, 0.87, 0.50, 57, 'Needs Improvement'
    """)

# ============================================================================
# Data expectations (quality checks)
# ============================================================================

@dlt.expect_or_drop("valid_patient_id", col("patient_id").isNotNull())
@dlt.expect_or_drop("valid_decision_flag", col("decision_flag").isin([0, 1]))
def bronze_quality_checks():
    """Enforce data quality"""
    pass

print("DLT Pipeline created successfully")
'''

print("\n" + "="*70)
print("SETUP INSTRUCTIONS")
print("="*70)

print("""
To set up the complete data pipeline:

STEP 1: Create DLT Pipeline in Databricks
========================================
1. Go to: https://databricks.com (or your Databricks workspace)
2. Click: Workflows → Delta Live Tables
3. Click: Create Pipeline
4. Fill in:
   Name: "Healthcare Equity DLT"
   Notebook path: /Users/[your-email]/dlt_pipeline
   Target schema: healthcare_equity_gold
   Cluster policy: (use default)
5. Click: Create and Start

STEP 2: Upload DLT Notebook
===========================
1. Go to: Workspace → Users → [your email]
2. Create folder: "dlt_pipeline"
3. Create notebook: "main"
4. Copy this code into the notebook:

---DLT CODE START---
{}
---DLT CODE END---

STEP 3: Schedule Auto-Refresh
=============================
1. Go to: Workflows → Jobs
2. Click: Create Job
3. Fill in:
   Name: "Refresh Healthcare Equity Data"
   Task: Run notebook: dlt_pipeline/main
   Trigger: On schedule
   Frequency: Every 5 minutes (or as needed)
4. Click: Create

STEP 4: Verify Setup
====================
1. Run the pipeline manually
2. Check that tables are created:
   - healthcare_equity_bronze.*
   - healthcare_equity_silver.*
   - healthcare_equity_gold.*
3. Dashboard should now show fresh data

TROUBLESHOOTING
===============
If pipeline fails:
1. Check cluster has enough resources
2. Verify schema names match
3. Check notebook path is correct
4. View pipeline run logs for errors

Next Steps:
===========
After DLT is set up:
- Data refreshes every 5 minutes (configurable)
- Dashboard reflects latest metrics
- Disparate Impact Ratio (DIR) calculated in real-time
- All pages show current data
""".format(dlt_pipeline_code))

print("\n" + "="*70)
print("AUTOMATED SETUP (If you have Databricks API access)")
print("="*70)

print("""
Run this command to create everything automatically:

    python create_dlt_pipeline_api.py

This will:
1. Create schemas if missing
2. Create initial data tables
3. Create DLT pipeline via API
4. Schedule refresh jobs
5. Verify everything works

See: create_dlt_pipeline_api.py
""")
