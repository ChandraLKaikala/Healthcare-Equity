#!/usr/bin/env python3
"""
Create All Databricks Jobs for Healthcare Equity Pipeline
Creates 3 jobs for complete data flow
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.databricks')

DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')

def create_job(job_name, task_description):
    """Create a single Databricks job"""

    host = DATABRICKS_HOST if DATABRICKS_HOST.startswith('https://') else f'https://{DATABRICKS_HOST}'

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Job configurations
    jobs_config = {
        "bronze_data_mutations": {
            "name": "healthcare_equity_bronze_mutations",
            "tasks": [{
                "task_key": "mutations",
                "notebook_task": {
                    "notebook_path": "/Workspace/continuous_data_pipeline"
                },
                "timeout_seconds": 600,
                "max_retries": 1
            }],
            "timeout_seconds": 900
        },
        "silver_gold_transform": {
            "name": "healthcare_equity_transform_pipeline",
            "tasks": [{
                "task_key": "transform",
                "notebook_task": {
                    "notebook_path": "/Workspace/transform_pipeline"
                },
                "timeout_seconds": 600,
                "max_retries": 1
            }],
            "timeout_seconds": 900
        },
        "refresh_analytics": {
            "name": "healthcare_equity_refresh_analytics",
            "tasks": [{
                "task_key": "refresh",
                "sql_task": {
                    "query": "REFRESH TABLE healthcare_equity_gold.bias_metrics; REFRESH TABLE healthcare_equity_gold.equity_dashboard; REFRESH TABLE healthcare_equity_gold.disparate_impact;"
                },
                "timeout_seconds": 300
            }],
            "timeout_seconds": 600
        }
    }

    if job_name not in jobs_config:
        print(f"Unknown job: {job_name}")
        return None

    job_config = jobs_config[job_name]
    job_config["max_concurrent_runs"] = 1

    try:
        url = f"{host}/api/2.1/jobs/create"
        response = requests.post(url, json=job_config, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"SUCCESS - Created: {job_config['name']}")
            print(f"  Job ID: {job_id}")
            return job_id
        else:
            print(f"FAILED - {job_config['name']}")
            print(f"  Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"ERROR - {job_config['name']}: {str(e)}")
        return None

if __name__ == "__main__":
    print("="*80)
    print("Creating Healthcare Equity Databricks Jobs")
    print("="*80 + "\n")

    jobs_created = []

    # Create all jobs
    print("[1/3] Creating Bronze Layer Mutation Job...")
    job1 = create_job("bronze_data_mutations", "Generates INSERT/UPSERT/DELETE mutations")
    if job1:
        jobs_created.append(("bronze_mutations", job1))

    print("\n[2/3] Creating Silver/Gold Transform Job...")
    job2 = create_job("silver_gold_transform", "Transforms Bronze to Silver and Gold layers")
    if job2:
        jobs_created.append(("transform", job2))

    print("\n[3/3] Creating Analytics Refresh Job...")
    job3 = create_job("refresh_analytics", "Refreshes Gold layer analytics tables")
    if job3:
        jobs_created.append(("refresh", job3))

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if jobs_created:
        print(f"\nSuccessfully created {len(jobs_created)} jobs:")
        for name, job_id in jobs_created:
            print(f"  - {name}: ID {job_id}")

        print("\n" + "="*80)
        print("NEXT STEPS - SCHEDULE THE JOBS")
        print("="*80)
        print("\n1. Open Databricks UI > Jobs")
        print("2. Find each job and click 'Edit'")
        print("3. Add schedule:")
        print("   - bronze_mutations: Every 1 minute")
        print("   - transform: Every 5 minutes (after mutations)")
        print("   - refresh: Every 5 minutes")
        print("4. Save schedules")
        print("\nOR run manually anytime from the Jobs page")
        print("\n" + "="*80)

    else:
        print("\nFailed to create jobs via API.")
        print("Please create jobs manually in Databricks UI:")
        print("  1. Jobs & Pipelines > Create Job")
        print("  2. Set task to run continuous_data_pipeline notebook")
        print("  3. Schedule: Every 1 minute")
        print("\nThe Python pipeline is already running automatically!")
        print("="*80)
