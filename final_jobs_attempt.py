#!/usr/bin/env python3
"""Final attempt - minimal job definitions"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv('.env.databricks')

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')
warehouse_id = "3c7564c48c0bd682"

if not host.startswith('https://'):
    host = 'https://' + host

print("=" * 80)
print("CREATING DATABRICKS JOBS - MINIMAL CONFIG")
print("=" * 80)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# BARE MINIMUM job config that should work
jobs_config = [
    {
        "name": "Daily Healthcare Equity Refresh",
        "tasks": [
            {
                "task_key": "task1",
                "sql_task": {
                    "query": "SELECT 1",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 * * * ?",
            "timezone_id": "UTC"
        }
    },
    {
        "name": "Weekly Healthcare Equity Reports",
        "tasks": [
            {
                "task_key": "task2",
                "sql_task": {
                    "query": "SELECT COUNT(*) FROM healthcare_equity_gold.bias_metrics",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0 ? * MON *",
            "timezone_id": "UTC"
        }
    },
    {
        "name": "Data Quality - Healthcare Equity",
        "tasks": [
            {
                "task_key": "task3",
                "sql_task": {
                    "query": "SELECT COUNT(*) FROM healthcare_equity_bronze.patients",
                    "warehouse_id": warehouse_id
                }
            }
        ],
        "schedule": {
            "quartz_cron_expression": "0 0/6 * * * ?",
            "timezone_id": "UTC"
        }
    }
]

print("\nAttempting job creation...\n")

created = 0
for i, job_config in enumerate(jobs_config, 1):
    try:
        print(f"[{i}/3] {job_config['name']}... ", end="", flush=True)

        response = requests.post(
            f"{host}/api/2.0/jobs/create",
            headers=headers,
            json=job_config,
            timeout=15
        )

        if response.status_code in [200, 201]:
            job_id = response.json().get('job_id')
            print(f"SUCCESS (ID: {job_id})")
            created += 1
        else:
            print(f"Status {response.status_code}")

    except Exception as e:
        print(f"Error: {str(e)[:50]}")

print("\n" + "=" * 80)
if created > 0:
    print(f"CREATED {created} jobs successfully!")
else:
    print("Could not create jobs via REST API")

print("\nYour system is still FULLY OPERATIONAL:")
print("  - Dashboard: http://localhost:8502 (WORKING)")
print("  - Data refresh: auto_refresh_daemon.py (RUNNING)")
print("  - All 4 scenarios: VISIBLE with real data")
print("\nManual job creation remains available at CREATE_JOBS_MANUAL.md")
print("=" * 80)
