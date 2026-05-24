#!/usr/bin/env python3
"""Create Databricks Jobs - Working Solution"""
import os
import sys
import requests
import json
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')

if not host.startswith('https://'):
    host = 'https://' + host

print("=" * 80)
print("CREATING DATABRICKS JOBS")
print("=" * 80)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Job configurations
jobs = [
    {
        "name": "Daily Healthcare Equity Bias Detection",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "refresh_bias_metrics",
                "description": "Refresh bias metrics daily",
                "notebook_task": {
                    "notebook_path": "/Users/admin/daily_bias_refresh"
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    },
    {
        "name": "Weekly Healthcare Equity Reports",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "weekly_compliance",
                "description": "Generate weekly compliance reports"
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 ? * MON",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    },
    {
        "name": "Data Quality Checks - Healthcare Equity",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "quality_validation",
                "description": "Run data quality checks every 6 hours"
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 */6 * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    }
]

created = []
for job in jobs:
    try:
        print(f"\nCreating: {job['name']}...")

        # Try 2.0 endpoint
        url = f"{host}/api/2.0/jobs/create"
        response = requests.post(url, headers=headers, json=job)

        if response.status_code in [200, 201]:
            result = response.json()
            job_id = result.get('job_id')
            print(f"  [SUCCESS] Job ID: {job_id}")
            created.append({'name': job['name'], 'id': job_id})
        else:
            print(f"  [WARN] Status {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")

print("\n" + "=" * 80)
if created:
    print("JOBS CREATED SUCCESSFULLY!")
    for job_info in created:
        print(f"  {job_info['name']}: ID {job_info['id']}")
    print("\nJobs are now visible in Databricks > Jobs & Pipelines")
else:
    print("NO JOBS CREATED - Check Databricks workspace permissions")
print("=" * 80)
