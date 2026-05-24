"""
Minimal DLT Pipeline Creation - Direct API approach
"""
import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

env_path = os.path.join(Path(__file__).parent, '.env.databricks')
load_dotenv(env_path)

HOST = os.getenv('DATABRICKS_HOST')
TOKEN = os.getenv('DATABRICKS_TOKEN')
HTTP_PATH = os.getenv('DATABRICKS_HTTP_PATH')

WORKSPACE_URL = f"https://{HOST.replace('https://', '')}"
WAREHOUSE_ID = HTTP_PATH.split('/')[-1]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("Creating DLT Pipeline (Minimal Configuration)...")
print(f"Workspace: {WORKSPACE_URL}\n")

# Minimal pipeline configuration
pipeline_config = {
    "name": "Healthcare Equity DLT",
    "storage": "/dlt/healthcare_equity_gold",
    "configuration": {
        "notebook_path": "/Repos/dlt_pipeline/main"
    },
    "target": "healthcare_equity_gold"
}

print(f"Pipeline name: {pipeline_config['name']}")
print(f"Notebook path: {pipeline_config['configuration']['notebook_path']}")
print(f"Target schema: {pipeline_config['target']}\n")

# Try API 2.1
print("[Try 1] Using /api/2.1/pipelines...")
try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.1/pipelines",
        headers=headers,
        json=pipeline_config,
        timeout=30
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}\n")

    if response.status_code in [200, 201]:
        result = response.json()
        pipeline_id = result.get('pipeline_id')
        print(f"[SUCCESS] Pipeline created: {pipeline_id}")

        # Start it
        print("\nStarting pipeline...")
        response = requests.post(
            f"{WORKSPACE_URL}/api/2.1/pipelines/{pipeline_id}/updates",
            headers=headers,
            json={},
            timeout=30
        )
        if response.status_code in [200, 201]:
            print("[SUCCESS] Pipeline started!")
            print("\nWait 2-5 minutes for transformation to complete.")
            print("Then refresh dashboard at http://localhost:8501")
    else:
        print(f"[FAIL] Status {response.status_code}")

except Exception as e:
    print(f"[ERR] {str(e)}\n")

# Try API 2.0
print("[Try 2] Using /api/2.0/jobs create job to run notebook...")
try:
    job_config = {
        "name": "Healthcare Equity DLT Runner",
        "new_cluster": {
            "spark_version": "14.2.x-scala2.12",
            "node_type_id": "i3.xlarge",
            "num_workers": 2,
            "aws_attributes": {
                "availability": "SPOT_WITH_FALLBACK"
            }
        },
        "notebook_task": {
            "notebook_path": "/Repos/dlt_pipeline/main",
            "base_parameters": {}
        },
        "timeout_seconds": 3600,
        "max_concurrent_runs": 1
    }

    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/jobs/create",
        headers=headers,
        json=job_config,
        timeout=30
    )

    print(f"Status: {response.status_code}")

    if response.status_code in [200, 201]:
        result = response.json()
        job_id = result.get('job_id')
        print(f"[OK] Job created: {job_id}")
        print("Note: This runs the notebook but is NOT a DLT pipeline.")
        print("A proper DLT pipeline requires Databricks UI creation.")
    else:
        print(f"Response: {response.text[:200]}\n")

except Exception as e:
    print(f"[ERR] {str(e)}\n")

print("\n" + "=" * 70)
print("RECOMMENDATION: DLT Pipeline API is limited in Community Edition")
print("=" * 70)
print("""
The DLT pipeline creation via API has limitations.

SIMPLEST FIX - Go to Databricks and use UI (takes 30 seconds):

1. https://dbc-ed229308-c6a7.cloud.databricks.com
2. Click: Workflows -> Delta Live Tables
3. Click: Create Pipeline
4. Name: Healthcare Equity DLT
5. Notebook path: /Repos/dlt_pipeline/main
6. Target schema: healthcare_equity_gold
7. Click: Create Pipeline
8. Click: Start

That's it. Pipeline will run in 2-5 minutes, then dashboard will show real data.

OR continue with dashboard using current Bronze data (100 records).
All pages work, just with smaller dataset.
""")
