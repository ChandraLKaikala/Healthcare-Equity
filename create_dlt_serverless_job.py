"""
Create DLT Job with Serverless Compute (Databricks Community Edition)
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
print("CREATE DLT PIPELINE - SERVERLESS VERSION")
print("=" * 80)
print(f"Workspace: {WORKSPACE_URL}\n")

# ============================================================================
# STEP 1: Create job with serverless compute
# ============================================================================

print("[STEP 1] Creating DLT job with serverless compute...")

job_config = {
    "name": "Healthcare Equity DLT Pipeline",
    "description": "Transforms Bronze -> Silver -> Gold layers",
    "tasks": [{
        "task_key": "dlt_run",
        "notebook_task": {
            "notebook_path": "/Repos/dlt_pipeline/main"
        },
        "timeout_seconds": 3600,
        "max_retries": 1,
        "compute_key": "serverless"
    }],
    "timeout_seconds": 3600
}

job_id = None
run_id = None

try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/jobs/create",
        headers=headers,
        json=job_config,
        timeout=30
    )

    print(f"  Status Code: {response.status_code}")

    if response.status_code in [200, 201]:
        result = response.json()
        job_id = result.get('job_id')
        print(f"  [SUCCESS] Job created!")
        print(f"  Job ID: {job_id}\n")

    else:
        error_msg = response.text
        print(f"  [ERROR] {error_msg[:200]}\n")

except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# STEP 2: Start the job immediately
# ============================================================================

if job_id:
    print("[STEP 2] Starting DLT pipeline...")

    try:
        run_response = requests.post(
            f"{WORKSPACE_URL}/api/2.0/jobs/run-now",
            headers=headers,
            json={"job_id": job_id},
            timeout=30
        )

        print(f"  Status Code: {run_response.status_code}")

        if run_response.status_code in [200, 201]:
            run_result = run_response.json()
            run_id = run_result.get('run_id')
            print(f"  [SUCCESS] Pipeline started!")
            print(f"  Run ID: {run_id}\n")

        else:
            print(f"  [ERROR] {run_response.text[:200]}\n")

    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# STEP 3: Monitor pipeline
# ============================================================================

if run_id:
    print("[STEP 3] Monitoring DLT pipeline...")
    print("  Polling status every 10 seconds...\n")

    completed = False
    poll_count = 0
    max_polls = 60  # 10 minutes

    while not completed and poll_count < max_polls:
        time.sleep(10)
        poll_count += 1

        try:
            status_response = requests.get(
                f"{WORKSPACE_URL}/api/2.0/jobs/runs/get",
                headers=headers,
                params={"run_id": run_id},
                timeout=30
            )

            if status_response.status_code in [200, 201]:
                status_result = status_response.json()
                state = status_result.get('state', 'UNKNOWN')
                state_msg = status_result.get('state_message', '')

                elapsed = poll_count * 10

                if state == "RUNNING":
                    print(f"  [{elapsed}s] Status: RUNNING - {state_msg}")

                elif state == "PENDING":
                    print(f"  [{elapsed}s] Status: PENDING - Waiting for cluster")

                elif state == "SUCCESS":
                    print(f"  [{elapsed}s] Status: SUCCESS!")
                    print(f"  Message: {state_msg}\n")
                    completed = True

                elif state == "FAILED":
                    print(f"  [{elapsed}s] Status: FAILED")
                    print(f"  Message: {state_msg}\n")
                    completed = True

                elif state == "TERMINATED":
                    print(f"  [{elapsed}s] Status: TERMINATED")
                    print(f"  Message: {state_msg}\n")
                    completed = True

                else:
                    print(f"  [{elapsed}s] Status: {state}")

        except Exception as e:
            print(f"  [WARN] Error checking status: {str(e)[:80]}")

    if not completed:
        print("\n  [INFO] Pipeline still running...")
        print("  Check Databricks UI for real-time status")
        print(f"  Job ID: {job_id}")
        print(f"  Run ID: {run_id}\n")

# ============================================================================
# STEP 4: Verify data was transformed
# ============================================================================

if job_id or run_id:
    print("[STEP 4] Verifying transformed data...\n")

    sql_endpoint = f"{WORKSPACE_URL}/api/2.0/sql/statements"

    verify_queries = [
        ("SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed", "Silver patients"),
        ("SELECT COUNT(*) FROM healthcare_equity_silver.decisions_processed", "Silver decisions"),
        ("SELECT COUNT(*) FROM healthcare_equity_gold.disparate_impact", "Gold metrics"),
        ("SELECT DISTINCT scenario_type FROM healthcare_equity_gold.disparate_impact", "Scenarios"),
    ]

    for query, label in verify_queries:
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
                    data = result['result']['data_array']
                    if data:
                        if "COUNT(*)" in query:
                            count = data[0][0]
                            print(f"  [OK] {label}: {count}")
                        else:
                            print(f"  [OK] {label}:")
                            for row in data[:10]:
                                print(f"       - {row[0]}")

        except Exception as e:
            pass

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("DLT PIPELINE CREATION SUMMARY")
print("=" * 80)

if job_id:
    print(f"""
[SUCCESS] DLT Job Created!

Job Details:
  Job ID: {job_id}
  Name: Healthcare Equity DLT Pipeline
  Compute: Serverless
  Notebook: /Repos/dlt_pipeline/main

Pipeline Execution:
  {f'Run ID: {run_id}' if run_id else 'Ready to run'}
  Status: {'Running/Completed' if run_id else 'Not started'}
  Next Run: Can run manually or schedule

What Happens:
  1. Bronze layer data (patients_source, decisions_source)
  2. Transform to Silver layer (cleaned, deduplicated)
  3. Aggregate to Gold layer (disparate_impact metrics)
  4. Results available for dashboard

Next Steps:
  1. Open dashboard: http://localhost:8501
  2. Click "Refresh Now" button
  3. All pages will show updated metrics
  4. Schedule job to run daily (optional)

Schedule Daily Refresh (Optional):
  python schedule_dlt_daily.py
  OR
  Go to Databricks -> Jobs -> {job_id} -> Edit -> Add schedule
""")
else:
    print("""
[ERROR] Could not create DLT job

Troubleshooting:
  1. Check Databricks workspace is accessible
  2. Verify credentials in .env.databricks
  3. Check that /Repos/dlt_pipeline/main notebook exists
  4. Try manually creating pipeline in Databricks UI

Manual Creation (30 seconds):
  1. Go to: https://dbc-ed229308-c6a7.cloud.databricks.com
  2. Click: Workflows -> Delta Live Tables
  3. Click: Create Pipeline
  4. Name: Healthcare Equity DLT
  5. Notebook: /Repos/dlt_pipeline/main
  6. Target: healthcare_equity_gold
  7. Click: Create Pipeline
  8. Click: Start
""")

print("=" * 80)
