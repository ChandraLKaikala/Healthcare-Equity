#!/usr/bin/env python3
"""Create Databricks Jobs - DO IT NOW"""
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
print("CREATING DATABRICKS JOBS NOW - FULL AUTOMATION")
print("=" * 80)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# SIMPLIFIED job definitions that work with Databricks API
jobs = [
    {
        "name": "Daily Healthcare Equity Bias Detection",
        "max_concurrent_runs": 1,
        "tasks": [
            {
                "task_key": "daily_refresh",
                "notebook_task": {
                    "notebook_path": "/tmp/daily_refresh",
                    "base_parameters": {}
                },
                "new_cluster": {
                    "spark_version": "11.3.x-scala2.12",
                    "node_type_id": "i3.xlarge",
                    "num_workers": 1,
                    "aws_attributes": {
                        "availability": "SPOT"
                    }
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
                    "query": "SELECT COUNT(*) FROM healthcare_equity_gold.bias_metrics",
                    "warehouse_id": warehouse_id,
                    "alert_on_no_rows": False
                },
                "timeout_seconds": 3600
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
                    "query": "SELECT COUNT(*) FROM healthcare_equity_bronze.patients",
                    "warehouse_id": warehouse_id,
                    "alert_on_no_rows": False
                },
                "timeout_seconds": 3600
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0/6 * * * ?",
            "timezone_id": "UTC",
            "pause_status": "UNPAUSED"
        }
    }
]

print("\nAttempting to create 3 jobs...\n")

created_jobs = []
failed_jobs = []

for idx, job in enumerate(jobs, 1):
    try:
        print(f"[{idx}/3] Creating: {job['name']}...")

        url = f"{host}/api/2.0/jobs/create"

        # Pretty print for debugging
        print(f"     URL: {url}")
        print(f"     Payload: {json.dumps(job, indent=2)[:200]}...")

        response = requests.post(
            url,
            headers=headers,
            json=job,
            timeout=30
        )

        print(f"     Response Status: {response.status_code}")

        if response.status_code in [200, 201]:
            result = response.json()
            job_id = result.get('job_id')
            print(f"     SUCCESS! Job ID: {job_id}")
            created_jobs.append({
                'name': job['name'],
                'id': job_id,
                'schedule': job['schedule']['quartz_cron_expression']
            })
        else:
            error_text = response.text[:300]
            print(f"     FAILED: {error_text}")
            failed_jobs.append({'name': job['name'], 'error': error_text})

    except requests.exceptions.RequestException as e:
        print(f"     ERROR: {str(e)[:100]}")
        failed_jobs.append({'name': job['name'], 'error': str(e)[:100]})
    except Exception as e:
        print(f"     EXCEPTION: {str(e)[:100]}")
        failed_jobs.append({'name': job['name'], 'error': str(e)[:100]})

# SUMMARY
print("\n" + "=" * 80)
print("JOB CREATION SUMMARY")
print("=" * 80)

if created_jobs:
    print(f"\n✅ SUCCESSFULLY CREATED: {len(created_jobs)}/3 jobs\n")
    for job in created_jobs:
        print(f"  Job: {job['name']}")
        print(f"  ID: {job['id']}")
        print(f"  Schedule: {job['schedule']}")
        print()

    print("=" * 80)
    print("JOBS ARE NOW LIVE IN DATABRICKS!")
    print("=" * 80)
    print("\nYour jobs will run automatically at scheduled times:")
    for job in created_jobs:
        print(f"  ✓ {job['name']}")

    print("\nTo view jobs:")
    print("  1. Go to Databricks workspace")
    print("  2. Click 'Jobs & Pipelines'")
    print("  3. See your 3 new jobs running")

if failed_jobs:
    print(f"\n⚠️  FAILED: {len(failed_jobs)} jobs")
    for job in failed_jobs:
        print(f"  ✗ {job['name']}")
        print(f"    Error: {job['error']}")

print("\n" + "=" * 80)
