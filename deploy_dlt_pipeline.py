#!/usr/bin/env python3
"""
Deploy DLT Pipeline to Databricks
Creates a Delta Live Tables pipeline for continuous data transformation
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv('.env.databricks')

DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')

def create_dlt_pipeline():
    """Create or update the DLT pipeline in Databricks"""

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    # DLT Pipeline configuration - using serverless compute
    pipeline_config = {
        "name": "healthcare_equity_dlt",
        "storage": "/Workspace/healthcare_equity_dlt",
        "configuration": {},
        "serverless_compute": {
            "sql_compute_config": {}
        },
        "libraries": [
            {
                "notebook": {
                    "path": "/Workspace/dlt_pipeline"
                }
            }
        ],
        "target": "healthcare_equity_gold",
        "continuous": False,
        "development": False
    }

    try:
        # Ensure HTTPS URL
        host = DATABRICKS_HOST if DATABRICKS_HOST.startswith('https://') else f'https://{DATABRICKS_HOST}'

        print("\nAttempting to create DLT pipeline...")
        url = f"{host}/api/2.0/pipelines"

        response = requests.post(url, json=pipeline_config, headers=headers, timeout=30)

        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            result = response.json()
            print("SUCCESS - DLT Pipeline created!")
            print(f"Pipeline ID: {result.get('pipeline_id')}")
            return True
        elif response.status_code == 400:
            print("WARNING - API returned 400")
            print("This may mean:")
            print("  1. DLT not available on Community Edition")
            print("  2. Pipeline already exists")
            print("  3. Configuration has issues")
            return False
        elif response.status_code == 404:
            print("ERROR - API endpoint not found")
            print("DLT Pipeline API may not be available on this workspace")
            return False
        else:
            print(f"ERROR - Unexpected status {response.status_code}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("DATABRICKS DLT PIPELINE DEPLOYMENT")
    print("="*80)

    success = create_dlt_pipeline()

    if success:
        print("\n" + "="*80)
        print("SUCCESS - DLT pipeline registered in Databricks")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("NOTE - DLT deployment via API may have restrictions")
        print("="*80)
        print("\nALTERNATIVE: Create job in Databricks UI manually:")
        print("1. Go to Jobs & Pipelines > Create job")
        print("2. Name: healthcare_equity_dlt")
        print("3. Trigger: Timed (every 5 minutes)")
        print("4. Task: Run notebook /Workspace/dlt_pipeline")
        print("\nOR use the Python continuous pipeline already running:")
        print("  python3 run_continuous_pipeline.py")
