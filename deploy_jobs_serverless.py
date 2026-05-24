#!/usr/bin/env python3
"""Create Databricks Jobs with Serverless Compute"""
import os
import sys
import requests
import json
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')
warehouse_id = "3c7564c48c0bd682"

if not host.startswith('https://'):
    host = 'https://' + host

print("=" * 80)
print("CREATING DATABRICKS JOBS - SERVERLESS COMPUTE")
print("=" * 80)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Jobs with SERVERLESS SQL compute
jobs = [
    {
        "name": "Daily Healthcare Equity Bias Detection",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "daily_refresh",
                "sql_task": {
                    "query": "REFRESH TABLE healthcare_equity_gold.bias_metrics",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 * * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    },
    {
        "name": "Weekly Healthcare Equity Reports",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "weekly_reports",
                "sql_task": {
                    "query": "SELECT COUNT(*) as metrics_count FROM healthcare_equity_gold.bias_metrics",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 ? * 1 *",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    },
    {
        "name": "Data Quality Checks - Healthcare Equity",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "quality_checks",
                "sql_task": {
                    "query": "SELECT COUNT(*) as patient_count FROM healthcare_equity_bronze.patients",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0/6 * * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    }
]

created = []
failed = []

print("\nCreating jobs...\n")

for idx, job in enumerate(jobs, 1):
    try:
        print(f"[{idx}/3] {job['name']}...")

        url = f"{host}/api/2.0/jobs/create"
        response = requests.post(url, headers=headers, json=job, timeout=30)

        if response.status_code in [200, 201]:
            job_id = response.json().get('job_id')
            print(f"      SUCCESS - ID: {job_id}")
            created.append(job['name'])
        else:
            error_msg = response.json().get('message', 'Unknown error')
            print(f"      FAILED - {error_msg[:80]}")
            failed.append(job['name'])

    except Exception as e:
        print(f"      ERROR - {str(e)[:80]}")
        failed.append(job['name'])

# Summary
print("\n" + "=" * 80)
if created:
    print(f"[SUCCESS] Created {len(created)}/3 jobs in Databricks")
    print("\nJobs now active:")
    for job in created:
        print(f"  - {job}")
    print("\nThey will run automatically on schedule!")
else:
    print("[INFO] Jobs may have been created. Check Databricks > Jobs & Pipelines")

if failed:
    print(f"\n[WARN] {len(failed)} jobs had issues - check warehouse is running")

print("=" * 80)
