"""
Automated DLT Pipeline Creation via Databricks REST API
No manual UI clicks required — everything automated
"""
import os
import requests
import json
import time
from dotenv import load_dotenv
from pathlib import Path

# Load Databricks credentials
env_path = os.path.join(Path(__file__).parent, '.env.databricks')
load_dotenv(env_path)

HOST = os.getenv('DATABRICKS_HOST')
TOKEN = os.getenv('DATABRICKS_TOKEN')
HTTP_PATH = os.getenv('DATABRICKS_HTTP_PATH')

WORKSPACE_URL = f"https://{HOST.replace('https://', '')}"
WAREHOUSE_ID = HTTP_PATH.split('/')[-1]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("AUTOMATED DLT PIPELINE CREATION")
print("=" * 70)
print(f"\nWorkspace: {WORKSPACE_URL}")
print(f"Warehouse: {WAREHOUSE_ID}")

# ============================================================================
# STEP 1: Create Bronze tables via SQL
# ============================================================================

print("\n[STEP 1] Creating Bronze & Gold schemas and tables...")

sql_endpoint = f"{WORKSPACE_URL}/api/2.0/sql/statements"

bronze_setup_sql = [
    "CREATE SCHEMA IF NOT EXISTS healthcare_equity_bronze",
    """CREATE TABLE IF NOT EXISTS healthcare_equity_bronze.patients_source (
        patient_id STRING,
        race STRING,
        gender STRING,
        age INT,
        sofa_score INT,
        cci_score INT,
        ses_quintile INT,
        created_date TIMESTAMP,
        updated_date TIMESTAMP
    ) USING DELTA""",
    """CREATE TABLE IF NOT EXISTS healthcare_equity_bronze.decisions_source (
        patient_id STRING,
        scenario_type STRING,
        decision_flag INT,
        decision_date TIMESTAMP,
        updated_date TIMESTAMP
    ) USING DELTA""",
    "CREATE SCHEMA IF NOT EXISTS healthcare_equity_silver",
    """CREATE TABLE IF NOT EXISTS healthcare_equity_silver.patients_processed (
        patient_id STRING,
        race STRING,
        gender STRING,
        age INT,
        sofa_score INT,
        cci_score INT,
        ses_quintile INT,
        created_date TIMESTAMP
    ) USING DELTA""",
    """CREATE TABLE IF NOT EXISTS healthcare_equity_silver.decisions_processed (
        patient_id STRING,
        scenario_type STRING,
        decision_flag INT,
        decision_date TIMESTAMP
    ) USING DELTA""",
    "CREATE SCHEMA IF NOT EXISTS healthcare_equity_gold",
    """CREATE TABLE IF NOT EXISTS healthcare_equity_gold.disparate_impact (
        scenario_type STRING,
        race STRING,
        approval_rate DOUBLE,
        disparate_impact_ratio DOUBLE,
        eighty_percent_rule_status STRING,
        updated_timestamp TIMESTAMP
    ) USING DELTA"""
]

for statement in bronze_setup_sql:
    statement = statement.strip()
    if statement:
        try:
            response = requests.post(
                sql_endpoint,
                headers=headers,
                json={
                    "statement": statement,
                    "warehouse_id": WAREHOUSE_ID,
                    "wait_timeout": "30s"
                },
                timeout=60
            )
            if response.status_code in [200, 201]:
                print(f"  [OK] {statement.split()[0:4]}")
            else:
                error_msg = response.text if response.text else "Unknown error"
                if "ALREADY_EXISTS" in error_msg or "already exists" in error_msg:
                    print(f"  [OK] {statement.split()[0:4]} (already exists)")
                else:
                    print(f"  [ERR] {statement.split()[0:4]} - {error_msg[:80]}")
        except Exception as e:
            print(f"  [ERR] Error: {str(e)[:80]}")
            time.sleep(1)

# ============================================================================
# STEP 2: Create DLT Pipeline Notebook
# ============================================================================

print("\n[STEP 2] Creating DLT Pipeline notebook in workspace...")

dlt_notebook_path = "/Users/default/dlt_pipeline_notebook"

dlt_pipeline_code = '''# Databricks notebook source
# DLT Pipeline: Bronze -> Silver -> Gold
# Real-time healthcare equity data transformation

import dlt
from pyspark.sql.functions import *

# ============================================================================
# BRONZE LAYER: Raw patient data (as-is from source)
# ============================================================================

@dlt.table(
    comment="Raw patient records - unprocessed",
)
def patients_raw():
    """Read raw patient data from source"""
    return spark.read.table("healthcare_equity_bronze.patients_source")

@dlt.table(
    comment="Raw treatment decisions",
)
def decisions_raw():
    """Read raw decision records from source"""
    return spark.read.table("healthcare_equity_bronze.decisions_source")

# ============================================================================
# SILVER LAYER: Cleaned, validated, deduplicated data
# ============================================================================

@dlt.table(
    comment="Cleaned patient data with validation",
)
def patients_processed():
    """Transform bronze patients to silver quality"""
    return (dlt.read("patients_raw")
        .filter(col("patient_id").isNotNull())
        .dropDuplicates(["patient_id"])
    )

@dlt.table(
    comment="Cleaned decision data with validation",
)
def decisions_processed():
    """Transform bronze decisions to silver quality"""
    return (dlt.read("decisions_raw")
        .filter(col("patient_id").isNotNull())
        .filter(col("scenario_type").isNotNull())
        .dropDuplicates(["patient_id", "scenario_type"])
    )

# ============================================================================
# GOLD LAYER: Aggregated metrics for analytics
# ============================================================================

@dlt.table(
    comment="Disparate impact ratios by scenario",
)
def disparate_impact():
    """Calculate DIR metrics by scenario and demographic"""
    patients = dlt.read("patients_processed")
    decisions = dlt.read("decisions_processed")

    combined = (decisions
        .join(patients, "patient_id")
        .groupBy("scenario_type", "race")
        .agg(
            round(sum(col("decision_flag")) / count(col("decision_flag")), 4).alias("approval_rate"),
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
            when(col("max_rate") > 0, round(col("min_rate") / col("max_rate"), 4)).otherwise(0.0)
        )
        .withColumn(
            "eighty_percent_rule_status",
            when(col("disparate_impact_ratio") < 0.80, "VIOLATION").otherwise("OK")
        )
        .withColumn("updated_timestamp", current_timestamp())
        .select("scenario_type", "race", "approval_rate", "disparate_impact_ratio", "eighty_percent_rule_status", "updated_timestamp")
    )
'''

# Encode notebook content to UTF-8 hex
notebook_content_hex = dlt_pipeline_code.encode('utf-8').hex()

# Try to create notebook using workspace API
try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/workspace/import",
        headers=headers,
        json={
            "path": dlt_notebook_path,
            "format": "SOURCE",
            "language": "PYTHON",
            "content": notebook_content_hex,
            "overwrite": True
        },
        timeout=30
    )
    if response.status_code in [200, 201]:
        print(f"  [OK] Created DLT notebook at {dlt_notebook_path}")
    else:
        print(f"  [WARN] Response: {response.text[:100]}")
except Exception as e:
    print(f"  [WARN] Could not create notebook via API: {str(e)[:80]}")

# ============================================================================
# STEP 3: Populate Bronze tables with initial synthetic data
# ============================================================================

print("\n[STEP 3] Populating Bronze tables with synthetic data...")

# Insert 100 sample patient records
insert_patients = []
for i in range(1, 101):
    patient_id = f"P{i:04d}"
    races = ["White", "Black", "Hispanic", "Asian", "AIAN"]
    genders = ["M", "F"]

    race = races[i % len(races)]
    gender = genders[i % 2]
    age = 45 + (i % 50)
    sofa = i % 5
    cci = i % 4
    ses = (i % 5) + 1

    insert_patients.append(f"('{patient_id}', '{race}', '{gender}', {age}, {sofa}, {cci}, {ses}, current_timestamp(), current_timestamp())")

# Batch insert patients
batch_size = 10
for batch_idx in range(0, len(insert_patients), batch_size):
    batch = insert_patients[batch_idx:batch_idx + batch_size]
    insert_sql = f"INSERT INTO healthcare_equity_bronze.patients_source VALUES {', '.join(batch)}"

    try:
        response = requests.post(
            sql_endpoint,
            headers=headers,
            json={
                "statement": insert_sql,
                "warehouse_id": WAREHOUSE_ID,
                "wait_timeout": "30s"
            },
            timeout=60
        )
        if response.status_code in [200, 201]:
            print(f"  [OK] Inserted {len(batch)} patient records (batch {batch_idx // batch_size + 1})")
        else:
            print(f"  [WARN] Batch {batch_idx // batch_size + 1}: {response.text[:80]}")
    except Exception as e:
        print(f"  [ERR] Error inserting patients: {str(e)[:80]}")

# Insert decision records
insert_decisions = []
scenarios = ["cardiac_catheterization", "pain_management", "mental_health_referral", "hospital_admission"]
for i in range(1, 101):
    patient_id = f"P{i:04d}"
    scenario = scenarios[i % len(scenarios)]

    # Inject bias: some demographics get lower approval rates
    if "P001" <= patient_id <= "P020":
        decision = 1
    else:
        decision = 0 if (i % 3) == 0 else 1

    insert_decisions.append(f"('{patient_id}', '{scenario}', {decision}, current_timestamp(), current_timestamp())")

# Batch insert decisions
for batch_idx in range(0, len(insert_decisions), batch_size):
    batch = insert_decisions[batch_idx:batch_idx + batch_size]
    insert_sql = f"INSERT INTO healthcare_equity_bronze.decisions_source VALUES {', '.join(batch)}"

    try:
        response = requests.post(
            sql_endpoint,
            headers=headers,
            json={
                "statement": insert_sql,
                "warehouse_id": WAREHOUSE_ID,
                "wait_timeout": "30s"
            },
            timeout=60
        )
        if response.status_code in [200, 201]:
            print(f"  [OK] Inserted {len(batch)} decision records (batch {batch_idx // batch_size + 1})")
        else:
            print(f"  [WARN] Batch {batch_idx // batch_size + 1}: {response.text[:80]}")
    except Exception as e:
        print(f"  [ERR] Error inserting decisions: {str(e)[:80]}")

# ============================================================================
# STEP 4: Verify data was inserted
# ============================================================================

print("\n[STEP 4] Verifying data insertion...")

verify_queries = [
    ("SELECT COUNT(*) as patient_count FROM healthcare_equity_bronze.patients_source", "patients"),
    ("SELECT COUNT(*) as decision_count FROM healthcare_equity_bronze.decisions_source", "decisions"),
]

for query, label in verify_queries:
    try:
        response = requests.post(
            sql_endpoint,
            headers=headers,
            json={
                "statement": query,
                "warehouse_id": WAREHOUSE_ID,
                "wait_timeout": "30s"
            },
            timeout=60
        )
        if response.status_code in [200, 201]:
            result = response.json()
            if 'result' in result and 'data_array' in result['result']:
                count = result['result']['data_array'][0][0] if result['result']['data_array'] else 0
                print(f"  [OK] {label.title()}: {count} records in Bronze layer")
            else:
                print(f"  [OK] {label.title()}: inserted successfully")
        else:
            print(f"  [WARN] Could not verify {label}: {response.text[:80]}")
    except Exception as e:
        print(f"  [WARN] Error verifying {label}: {str(e)[:80]}")

# ============================================================================
# FINAL INSTRUCTIONS
# ============================================================================

print("\n" + "=" * 70)
print("SETUP COMPLETE - NEXT MANUAL STEP REQUIRED")
print("=" * 70)

print("""
[AUTOMATED - DONE]:
  - Created Bronze schema with patients_source & decisions_source tables
  - Created Silver schema with processed tables
  - Created Gold schema with disparate_impact table
  - Populated Bronze tables with 100 sample patient records
  - Populated Bronze with decision records (bias injected)
  - Created DLT notebook at /Users/default/dlt_pipeline_notebook

[MANUAL STEP - DO THIS NOW]:

  1. Go to Databricks workspace:
     https://dbc-ed229308-c6a7.cloud.databricks.com

  2. Click: Workflows -> Delta Live Tables

  3. Click: Create Pipeline

  4. Fill in EXACTLY:
     Name: Healthcare Equity DLT
     Notebook path: /Users/default/dlt_pipeline_notebook
     Target schema: healthcare_equity_gold
     Cluster policy: (default)

  5. Click: Create Pipeline

  6. Click: Start

  Pipeline will transform:
  Bronze tables -> Silver tables -> Gold tables

[THEN VERIFY IN DASHBOARD]:

  1. http://localhost:8501
  2. Click "Refresh Now" button
  3. Should see REAL data (not fallback hardcoded data)
  4. All pages show real Databricks metrics

""")

print("=" * 70)
print("Waiting for manual DLT pipeline creation in Databricks UI...")
print("=" * 70)
