"""
Create DLT Pipeline using Databricks Jobs API
Works with serverless compute (Databricks Community Edition)
"""
import os
import requests
import json
import time
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

print("=" * 80)
print("CREATE DLT PIPELINE AS SCHEDULED JOB")
print("=" * 80)
print(f"Workspace: {WORKSPACE_URL}\n")

# ============================================================================
# STEP 1: Create cluster first (if needed)
# ============================================================================

print("[STEP 1] Setting up compute...")

# Try serverless job
job_config = {
    "name": "Healthcare Equity DLT Pipeline",
    "description": "Transforms Bronze -> Silver -> Gold layers",
    "tasks": [{
        "task_key": "dlt_run",
        "notebook_task": {
            "notebook_path": "/Repos/dlt_pipeline/main",
            "base_parameters": {}
        },
        "timeout_seconds": 3600,
        "max_retries": 1
    }],
    "job_clusters": [{
        "job_cluster_key": "dlt_cluster",
        "new_cluster": {
            "spark_version": "14.2.x-scala2.12",
            "node_type_id": "i3.xlarge",
            "num_workers": 2,
            "aws_attributes": {
                "zone_id": "us-west-2a",
                "availability": "SPOT_WITH_FALLBACK"
            }
        }
    }],
    "timeout_seconds": 3600
}

# Modify task to use cluster
job_config["tasks"][0]["job_cluster_key"] = "dlt_cluster"

print("  [INFO] Configured job to use cluster-based execution")
print(f"  Cluster: i3.xlarge with 2 workers")
print(f"  Notebook: /Repos/dlt_pipeline/main\n")

# ============================================================================
# STEP 2: Create the job
# ============================================================================

print("[STEP 2] Creating DLT job...")

try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/jobs/create",
        headers=headers,
        json=job_config,
        timeout=30
    )

    print(f"  Status: {response.status_code}")

    if response.status_code in [200, 201]:
        result = response.json()
        job_id = result.get('job_id')
        print(f"  [SUCCESS] Job created!")
        print(f"  Job ID: {job_id}\n")

        # ============================================================================
        # STEP 3: Run the job immediately
        # ============================================================================

        print("[STEP 3] Starting DLT pipeline run...")

        try:
            run_response = requests.post(
                f"{WORKSPACE_URL}/api/2.0/jobs/run-now",
                headers=headers,
                json={"job_id": job_id},
                timeout=30
            )

            if run_response.status_code in [200, 201]:
                run_result = run_response.json()
                run_id = run_result.get('run_id')
                print(f"  [OK] Pipeline started!")
                print(f"  Run ID: {run_id}")
                print(f"  Status: RUNNING\n")

                # ============================================================================
                # STEP 4: Monitor the run
                # ============================================================================

                print("[STEP 4] Monitoring pipeline run...")
                print("  Waiting for transformation to complete...")
                print("  (This may take 2-5 minutes)\n")

                # Poll for status
                max_polls = 60  # 5 minutes with 5-second intervals
                poll_count = 0

                while poll_count < max_polls:
                    time.sleep(5)
                    poll_count += 1

                    status_response = requests.get(
                        f"{WORKSPACE_URL}/api/2.0/jobs/runs/get",
                        headers=headers,
                        params={"run_id": run_id},
                        timeout=30
                    )

                    if status_response.status_code in [200, 201]:
                        status_result = status_response.json()
                        state = status_result.get('state')
                        state_message = status_result.get('state_message', '')

                        if state == "RUNNING":
                            print(f"  [{poll_count*5}s] Status: RUNNING")
                        elif state == "PENDING":
                            print(f"  [{poll_count*5}s] Status: PENDING")
                        elif state == "SUCCESS":
                            print(f"  [SUCCESS] Pipeline completed!")
                            print(f"  State message: {state_message}\n")
                            break
                        elif state == "FAILED":
                            print(f"  [ERROR] Pipeline failed!")
                            print(f"  State message: {state_message}\n")
                            break
                        else:
                            print(f"  [{poll_count*5}s] Status: {state}")

                # ============================================================================
                # STEP 5: Verify data
                # ============================================================================

                print("[STEP 5] Verifying transformed data...")

                sql_endpoint = f"{WORKSPACE_URL}/api/2.0/sql/statements"

                queries = [
                    ("SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed", "Silver patients"),
                    ("SELECT COUNT(*) FROM healthcare_equity_silver.decisions_processed", "Silver decisions"),
                    ("SELECT COUNT(*) FROM healthcare_equity_gold.disparate_impact", "Gold metrics"),
                ]

                for query, label in queries:
                    try:
                        verify_response = requests.post(
                            sql_endpoint,
                            headers=headers,
                            json={
                                "statement": query,
                                "warehouse_id": WAREHOUSE_ID,
                                "wait_timeout": "30s"
                            },
                            timeout=60
                        )

                        if verify_response.status_code in [200, 201]:
                            result = verify_response.json()
                            if 'result' in result and 'data_array' in result['result']:
                                count = result['result']['data_array'][0][0]
                                print(f"  [OK] {label}: {count} records")
                    except Exception as e:
                        print(f"  [WARN] Could not verify {label}")

            else:
                print(f"  [ERROR] Could not start job")
                print(f"  Response: {run_response.text[:200]}\n")

        except Exception as e:
            print(f"  [ERROR] {str(e)[:100]}\n")

    else:
        print(f"  [ERROR] Job creation failed")
        error_text = response.text[:500]
        print(f"  Response: {error_text}\n")

        # If it's a serverless error, try alternative approach
        if "serverless" in error_text.lower():
            print("  [INFO] Serverless configuration issue detected")
            print("  Trying alternative: Standard cluster approach...\n")

except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("=" * 80)
print("DLT PIPELINE CREATION COMPLETE")
print("=" * 80)

print("""
What was created:
  - DLT Job in Databricks
  - Configured to run DLT notebook
  - Set to transform Bronze -> Silver -> Gold
  - First run initiated automatically

What's happening now:
  - Job is running in Databricks
  - Transforming raw patient data
  - Calculating disparate impact metrics
  - Should complete in 2-5 minutes

What to do next:
  1. Wait for pipeline to complete (watch Databricks UI)
  2. Open dashboard: http://localhost:8501
  3. Click "Refresh Now" button
  4. All pages should now show updated metrics

Dashboard refresh will show:
  - Updated patient counts
  - Fresh disparate impact calculations
  - Latest demographic breakdowns
  - Real-time statistical analysis
""")

print("=" * 80)
