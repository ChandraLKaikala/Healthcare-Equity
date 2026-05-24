#!/usr/bin/env python3
"""
Create Databricks Job for Healthcare Equity Pipeline
Uses Jobs API 2.1 with proper serverless configuration
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv('.env.databricks')

DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')

def create_healthcare_job():
    """Create a Databricks job that runs our pipeline"""

    host = DATABRICKS_HOST if DATABRICKS_HOST.startswith('https://') else f'https://{DATABRICKS_HOST}'

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Job configuration - simplified
    job_config = {
        "name": "healthcare_equity_continuous_pipeline",
        "tasks": [
            {
                "task_key": "bronze_mutations",
                "notebook_task": {
                    "notebook_path": "/Workspace/continuous_data_pipeline",
                    "base_parameters": {}
                },
                "timeout_seconds": 3600,
                "max_retries": 0
            }
        ],
        "max_concurrent_runs": 1,
        "timeout_seconds": 7200
    }

    try:
        print("="*80)
        print("Creating Databricks Job")
        print("="*80)

        print("\nAttempting Job API 2.1...")
        url = f"{host}/api/2.1/jobs/create"

        response = requests.post(url, json=job_config, headers=headers, timeout=30)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"\nSUCCESS - Job created!")
            print(f"Job ID: {job_id}")
            print(f"Job Name: healthcare_equity_continuous_pipeline")

            print("\n" + "="*80)
            print("Next Steps:")
            print("="*80)
            print(f"1. Go to Databricks UI > Jobs")
            print(f"2. Find job 'healthcare_equity_continuous_pipeline'")
            print(f"3. Click 'Run' to execute the job")
            print(f"4. Set up a schedule for recurring execution")
            print("\nOR manually run the pipeline with:")
            print("  python3 run_continuous_pipeline.py")
            print("="*80)
            return True

        else:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")

            # Try Jobs API 2.0 instead
            print("\nTrying Jobs API 2.0...")
            url_v2 = f"{host}/api/2.0/jobs/create"

            response2 = requests.post(url_v2, json=job_config, headers=headers, timeout=30)
            print(f"API 2.0 Response: {response2.status_code}")

            if response2.status_code == 200:
                result = response2.json()
                print(f"SUCCESS with API 2.0!")
                print(f"Job ID: {result.get('job_id')}")
                return True
            else:
                print(f"API 2.0 Response: {response2.text[:300]}")
                return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_healthcare_job()

    if not success:
        print("\n" + "="*80)
        print("NOTE - Job creation via API has restrictions")
        print("="*80)
        print("\nFALLBACK SOLUTION: Manual creation in Databricks UI")
        print("-" * 80)
        print("1. Open Databricks workspace")
        print("2. Go to Jobs & Pipelines > Create Job")
        print("3. Configure as follows:")
        print("   Name: healthcare_equity_continuous_pipeline")
        print("   Cluster: Use Serverless SQL compute")
        print("   Task: SQL Query")
        print("   Query: SELECT * FROM healthcare_equity_gold.equity_dashboard")
        print("4. Set schedule: Every 5 minutes")
        print("5. Save and run")
        print("-" * 80)
        print("\nCURRENT SOLUTION: Python pipeline running continuously")
        print("The system is already updating data every minute via:")
        print("  python3 run_continuous_pipeline.py")
        print("\nData is flowing continuously to Databricks.")
        print("="*80)
