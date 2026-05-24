#!/usr/bin/env python3
"""
Healthcare Equity System - Databricks Production Launch
Fortune 500 Enterprise Deployment
"""
import os
import sys
import time
import subprocess

sys.path.insert(0, '.')

print("\n" + "="*70)
print("HEALTHCARE EQUITY BIAS DETECTION - DATABRICKS DEPLOYMENT")
print("="*70 + "\n")

# Step 1: Load environment
print("[1/5] Loading Databricks credentials...")
from dotenv import load_dotenv
load_dotenv('.env.databricks')

# Step 2: Connect to Databricks
print("[2/5] Connecting to Databricks...")
from databricks.sql import connect

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

conn = connect(
    server_hostname=host,
    http_path=http_path,
    personal_access_token=token,
    use_redirects=True
)
cursor = conn.cursor()

# Verify connection
cursor.execute("SELECT 1")
print("[OK] Connected to Databricks")

# Create schemas
print("[3/5] Creating schemas...")
cursor.execute("CREATE DATABASE IF NOT EXISTS healthcare_equity_bronze")
cursor.execute("CREATE DATABASE IF NOT EXISTS healthcare_equity_silver")
cursor.execute("CREATE DATABASE IF NOT EXISTS healthcare_equity_gold")
print("[OK] Schemas created")

# Generate 1M synthetic patients
print("[4/5] Generating 1M synthetic patients in Databricks...")
cursor.execute("""
CREATE OR REPLACE TABLE healthcare_equity_bronze.patients AS
SELECT
  ROW_NUMBER() OVER (ORDER BY (SELECT 1)) as patient_id,
  CASE WHEN RAND() < 0.5 THEN 'M' ELSE 'F' END as gender,
  CASE
    WHEN RAND() < 0.12 THEN 'Black'
    WHEN RAND() < 0.19 THEN 'Hispanic'
    WHEN RAND() < 0.05 THEN 'AIAN'
    WHEN RAND() < 0.03 THEN 'Asian'
    ELSE 'White'
  END as race,
  CASE WHEN RAND() < 0.05 THEN 'LGBTQ' ELSE 'Heterosexual' END as sexual_orientation,
  (18 + INT(RAND() * 75)) as age,
  CASE
    WHEN RAND() < 0.2 THEN 'Medicaid'
    WHEN RAND() < 0.3 THEN 'Medicare'
    WHEN RAND() < 0.4 THEN 'Commercial'
    ELSE 'Uninsured'
  END as insurance_type,
  INT(RAND() * 24) as sofa_score,
  INT(RAND() * 5) as cci_score,
  INT(RAND() * 5 + 1) as ses_quintile,
  CURRENT_TIMESTAMP() as created_at
FROM (SELECT EXPLODE(SEQUENCE(1, 1000000)) as num)
LIMIT 1000000
""")
print("[OK] 1M patients generated")

# Generate treatment decisions
cursor.execute("""
CREATE OR REPLACE TABLE healthcare_equity_bronze.decisions AS
SELECT
  ROW_NUMBER() OVER (ORDER BY (SELECT 1)) as decision_id,
  INT(RAND() * 1000000) + 1 as patient_id,
  CASE
    WHEN RAND() < 0.25 THEN 'cardiac_catheterization'
    WHEN RAND() < 0.50 THEN 'pain_management'
    WHEN RAND() < 0.75 THEN 'mental_health_referral'
    ELSE 'hospital_admission'
  END as scenario_type,
  CASE WHEN RAND() < 0.5 THEN 'Recommended' ELSE 'Not Recommended' END as decision,
  CURRENT_TIMESTAMP() as decision_date
FROM (SELECT EXPLODE(SEQUENCE(1, 1500000)) as num)
LIMIT 1500000
""")

# Generate outcomes
cursor.execute("""
CREATE OR REPLACE TABLE healthcare_equity_bronze.outcomes AS
SELECT
  ROW_NUMBER() OVER (ORDER BY (SELECT 1)) as outcome_id,
  INT(RAND() * 1000000) + 1 as patient_id,
  INT(RAND() * 1500000) + 1 as decision_id,
  CASE WHEN RAND() < 0.85 THEN 'Success' WHEN RAND() < 0.95 THEN 'Complication' ELSE 'Failure' END as outcome_type,
  CASE WHEN RAND() < 0.92 THEN 0 ELSE 1 END as thirty_day_readmission,
  CASE WHEN RAND() < 0.97 THEN 0 ELSE 1 END as in_hospital_mortality,
  CURRENT_TIMESTAMP() as outcome_date
FROM (SELECT EXPLODE(SEQUENCE(1, 800000)) as num)
LIMIT 800000
""")

conn.close()
print("[OK] All data tables created in Databricks")

# Launch dashboard
print("[5/5] Launching Streamlit dashboard...")
print("\n" + "="*70)
print("PRODUCTION SYSTEM READY")
print("="*70)
print("\nDashboard: http://localhost:8501")
print("Data: 1M patients, 1.5M treatment decisions, 800k outcomes")
print("Database: Databricks Community Edition (default warehouse)")
print("\nPress Ctrl+C to stop\n")

subprocess.run(["streamlit", "run", "dashboard/app.py"])
