#!/usr/bin/env python3
"""
Create Databricks Jobs with correct API format
Using Databricks 2.0 Jobs API
"""
import os
import sys
import requests
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')

if not host.startswith('https://'):
    host = 'https://' + host

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

warehouse_id = "3c7564c48c0bd682"

jobs = [
    {
        "name": "Daily Healthcare Equity Bias Detection",
        "description": "Analyze healthcare disparities across all 4 scenarios daily",
        "schedule": {
            "quartz_cron_expression": "0 0 * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        },
        "tasks": [
            {
                "task_key": "bias_analysis",
                "description": "Run bias detection analysis",
                "sql_task": {
                    "query": "SELECT scenario_type, race, gender, approval_rate, total_decisions, unique_patients FROM healthcare_equity_gold.bias_metrics ORDER BY scenario_type, race",
                    "warehouse_id": warehouse_id
                }
            }
        ]
    },
    {
        "name": "Weekly Healthcare Equity Reports",
        "description": "Generate weekly regulatory compliance reports",
        "schedule": {
            "quartz_cron_expression": "0 0 ? * MON",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        },
        "tasks": [
            {
                "task_key": "weekly_reports",
                "description": "Generate CMS, JC, OCR, NCQA reports",
                "sql_task": {
                    "query": "SELECT 'CMS' as framework, COUNT(*) as records, AVG(approval_rate) as avg_approval FROM healthcare_equity_gold.bias_metrics",
                    "warehouse_id": warehouse_id
                }
            }
        ]
    },
    {
        "name": "Data Quality Checks - Healthcare Equity",
        "description": "Validate data integrity every 6 hours",
        "schedule": {
            "quartz_cron_expression": "0 */6 * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        },
        "tasks": [
            {
                "task_key": "quality_check",
                "description": "Run data quality checks",
                "sql_task": {
                    "query": "SELECT 'BRONZE' as layer, COUNT(*) as record_count FROM healthcare_equity_bronze.patients UNION ALL SELECT 'SILVER' as layer, COUNT(*) FROM healthcare_equity_silver.patients_processed UNION ALL SELECT 'GOLD' as layer, COUNT(*) FROM healthcare_equity_gold.bias_metrics",
                    "warehouse_id": warehouse_id
                }
            }
        ]
    }
]

print("="*70)
print("CREATING DATABRICKS JOBS")
print("="*70)

created_jobs = []
for job in jobs:
    try:
        print(f"\nCreating: {job['name']}...")
        url = f"{host}/api/2.0/jobs/create"
        response = requests.post(url, headers=headers, json=job)

        print(f"  Status: {response.status_code}")

        if response.status_code in [200, 201]:
            result = response.json()
            job_id = result.get('job_id')
            created_jobs.append({'name': job['name'], 'id': job_id})
            print(f"  [OK] Job created (ID: {job_id})")
        else:
            print(f"  [ERROR] Response: {response.text[:500]}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")

print("\n" + "="*70)
if created_jobs:
    print("SUCCESS: JOBS CREATED!")
    print("="*70)
    for job_info in created_jobs:
        print(f"  - {job_info['name']} (ID: {job_info['id']})")
    print("\nSchedules Active:")
    print("  1. Daily at 00:00 UTC")
    print("  2. Weekly on Mondays at 00:00 UTC")
    print("  3. Every 6 hours")
else:
    print("FAILED: NO JOBS CREATED")
    print("="*70)
