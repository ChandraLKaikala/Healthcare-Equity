#!/usr/bin/env python3
"""
Create actual Databricks Jobs (not just YAML files)
"""
import os
import sys
import json
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

from databricks.sql import connect

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

print("Creating Databricks Jobs...")
conn = connect(
    server_hostname=host,
    http_path=http_path,
    personal_access_token=token
)
cursor = conn.cursor()

# Job 1: Daily Bias Detection
print("\n[JOB 1] Creating daily bias detection job...")
cursor.execute("""
CREATE JOB IF NOT EXISTS daily_bias_detection AS
SCHEDULE '0 0 * * ?' WITH
  SELECT
    scenario_type,
    race,
    gender,
    approval_rate,
    ROUND(approval_rate / MAX(approval_rate) OVER (PARTITION BY scenario_type) * 100, 2) as dir_percentage,
    CURRENT_TIMESTAMP() as analyzed_at
  FROM healthcare_equity_gold.bias_metrics
  ORDER BY dir_percentage ASC
""")
print("[OK] daily_bias_detection")

# Job 2: Weekly Reports
print("[JOB 2] Creating weekly reports job...")
cursor.execute("""
CREATE JOB IF NOT EXISTS weekly_equity_reports AS
SCHEDULE '0 0 ? * MON' WITH
  SELECT
    COUNT(*) as patients_analyzed,
    COUNT(DISTINCT race) as demographics_tracked,
    AVG(approval_rate) as avg_approval_rate,
    MIN(approval_rate) as min_approval_rate,
    CURRENT_TIMESTAMP() as report_date
  FROM healthcare_equity_gold.bias_metrics
""")
print("[OK] weekly_equity_reports")

# Job 3: Data Quality
print("[JOB 3] Creating data quality checks job...")
cursor.execute("""
CREATE JOB IF NOT EXISTS data_quality_checks AS
SCHEDULE '0 */6 * * ?' WITH
  SELECT
    'BRONZE' as layer,
    COUNT(*) as record_count,
    COUNT(DISTINCT patient_id) as unique_patients,
    CURRENT_TIMESTAMP() as checked_at
  FROM healthcare_equity_bronze.patients
  UNION ALL
  SELECT
    'SILVER' as layer,
    COUNT(*) as record_count,
    COUNT(DISTINCT patient_id) as unique_patients,
    CURRENT_TIMESTAMP() as checked_at
  FROM healthcare_equity_silver.patients_processed
""")
print("[OK] data_quality_checks")

conn.close()

print("\n" + "="*60)
print("Jobs created in Databricks!")
print("="*60)
print("\nSchedules:")
print("  1. Daily Bias Detection: 00:00 UTC daily")
print("  2. Weekly Reports: 00:00 UTC Mondays")
print("  3. Data Quality: Every 6 hours")
