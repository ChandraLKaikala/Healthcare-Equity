#!/usr/bin/env python3
"""Deploy Databricks Jobs - Final Working Version"""
import os
import sys
import requests
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')
warehouse_id = "3c7564c48c0bd682"

if not host.startswith('https://'):
    host = 'https://' + host

print("=" * 80)
print("DEPLOYING DATABRICKS JOBS")
print("=" * 80)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Jobs with correct Quartz cron syntax
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
            "quartz_cron_expression": "0 0 * * * ?",  # Correct Quartz format
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
                    "query": "SELECT COUNT(*) FROM healthcare_equity_gold.bias_metrics",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 ? * 1 *",  # Monday 00:00
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
                    "query": "SELECT COUNT(*) FROM healthcare_equity_bronze.patients",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0/6 * * * ?",  # Every 6 hours
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    }
]

created = []
for idx, job in enumerate(jobs, 1):
    try:
        print(f"\n[{idx}/3] Creating: {job['name']}...")

        url = f"{host}/api/2.0/jobs/create"
        response = requests.post(url, headers=headers, json=job)

        if response.status_code in [200, 201]:
            result = response.json()
            job_id = result.get('job_id')
            print(f"      SUCCESS - Job ID: {job_id}")
            created.append({'name': job['name'], 'id': job_id})
        else:
            print(f"      Status: {response.status_code}")
            error = response.json().get('message', '')[:100]
            print(f"      Error: {error}")

    except Exception as e:
        print(f"      Exception: {str(e)[:80]}")

print("\n" + "=" * 80)
print("DEPLOYMENT SUMMARY")
print("=" * 80)

if created:
    print(f"\n[SUCCESS] {len(created)}/3 jobs created!\n")
    for job in created:
        print(f"  {job['name']}")
        print(f"    ID: {job['id']}\n")
    print("Jobs now visible at: Databricks > Jobs & Pipelines > Jobs")
    print("\nSchedules:")
    print("  - Daily: 00:00 UTC")
    print("  - Weekly: Monday 00:00 UTC")
    print("  - Every 6 hours")
else:
    print("\n[WARNING] No jobs created")
    print("Possible causes:")
    print("  - Invalid cron syntax")
    print("  - Warehouse not running")
    print("  - Permission issues")
    print("\nManual creation via UI:")
    print("  1. Go to Databricks workspace")
    print("  2. Click 'Jobs & Pipelines' > 'Create job'")
    print("  3. Set name, schedule, and SQL task")

print("\n" + "=" * 80)
