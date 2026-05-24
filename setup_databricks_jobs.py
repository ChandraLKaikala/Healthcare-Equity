#!/usr/bin/env python3
"""
Setup Databricks Jobs via REST API - Fixed Version
"""
import os
import sys
import requests
import json
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')

# Ensure host has https://
if not host.startswith('https://'):
    host = 'https://' + host

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

base_url = f"{host}/api/2.1/jobs"

jobs = [
    {
        "name": "Daily Healthcare Equity Bias Detection",
        "description": "Analyze healthcare disparities across all 4 scenarios daily",
        "tasks": [{
            "task_key": "bias_analysis",
            "description": "Run bias detection analysis",
            "sql_task": {
                "query": """
                SELECT
                    scenario_type,
                    race,
                    gender,
                    approval_rate,
                    total_decisions,
                    unique_patients,
                    CURRENT_TIMESTAMP() as analyzed_at
                FROM healthcare_equity_gold.bias_metrics
                ORDER BY scenario_type, race
                """,
                "warehouse_id": "3c7564c48c0bd682"
            }
        }],
        "schedule": {
            "quartz_cron_expression": "0 0 * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    },
    {
        "name": "Weekly Healthcare Equity Reports",
        "description": "Generate weekly regulatory compliance reports",
        "tasks": [{
            "task_key": "weekly_reports",
            "description": "Generate CMS, JC, OCR, NCQA reports",
            "sql_task": {
                "query": """
                SELECT
                    'CMS' as framework,
                    COUNT(*) as records,
                    AVG(approval_rate) as avg_approval,
                    MIN(approval_rate) as min_approval,
                    CURRENT_TIMESTAMP() as report_date
                FROM healthcare_equity_gold.bias_metrics
                """,
                "warehouse_id": "3c7564c48c0bd682"
            }
        }],
        "schedule": {
            "quartz_cron_expression": "0 0 ? * MON",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    },
    {
        "name": "Data Quality Checks - Healthcare Equity",
        "description": "Validate data integrity every 6 hours",
        "tasks": [{
            "task_key": "quality_check",
            "description": "Run data quality checks",
            "sql_task": {
                "query": """
                SELECT
                    'BRONZE' as layer,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT patient_id) as unique_patients
                FROM healthcare_equity_bronze.patients
                UNION ALL
                SELECT
                    'SILVER' as layer,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT patient_id) as unique_patients
                FROM healthcare_equity_silver.patients_processed
                UNION ALL
                SELECT
                    'GOLD' as layer,
                    COUNT(*) as record_count,
                    0 as unique_patients
                FROM healthcare_equity_gold.bias_metrics
                """,
                "warehouse_id": "3c7564c48c0bd682"
            }
        }],
        "schedule": {
            "quartz_cron_expression": "0 */6 * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    }
]

print("="*70)
print("SETTING UP DATABRICKS JOBS VIA REST API")
print("="*70)
print(f"Host: {host}")
print(f"Base URL: {base_url}\n")

created_jobs = []
for job in jobs:
    try:
        print(f"Creating: {job['name']}...")
        response = requests.post(base_url, headers=headers, json=job)

        if response.status_code in [200, 201]:
            job_id = response.json().get('job_id')
            created_jobs.append({'name': job['name'], 'id': job_id})
            print(f"  [OK] Job created (ID: {job_id})")
        else:
            print(f"  [ERROR] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] {str(e)[:200]}")

print("\n" + "="*70)
print("JOBS SETUP COMPLETE!")
print("="*70)

if created_jobs:
    print("\nSuccessfully created jobs:")
    for job_info in created_jobs:
        print(f"  - {job_info['name']} (ID: {job_info['id']})")

print("\nTo view jobs in Databricks:")
print("  1. Go to https://community.databricks.com")
print("  2. Click 'Jobs' in the sidebar")
print("  3. Look for the newly created jobs")
print("\nSchedules:")
print("  1. Daily Bias Detection: 00:00 UTC daily")
print("  2. Weekly Reports: 00:00 UTC Mondays")
print("  3. Data Quality: Every 6 hours")
