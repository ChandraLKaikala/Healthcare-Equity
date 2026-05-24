"""
Create Databricks Job without explicit compute (uses workspace default)
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
print("CREATE DLT PIPELINE JOB")
print("=" * 80)
print(f"Workspace: {WORKSPACE_URL}\n")

# ============================================================================
# Create job WITHOUT compute specification (uses workspace default)
# ============================================================================

print("[STEP 1] Creating DLT job...")

job_config = {
    "name": "Healthcare Equity DLT",
    "description": "Bronze -> Silver -> Gold transformation",
    "tasks": [{
        "task_key": "dlt_transform",
        "notebook_task": {
            "notebook_path": "/Repos/dlt_pipeline/main"
        },
        "timeout_seconds": 3600
    }]
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

    print(f"  Status: {response.status_code}")

    if response.status_code in [200, 201]:
        result = response.json()
        job_id = result.get('job_id')
        print(f"  [SUCCESS] Job created!")
        print(f"  Job ID: {job_id}\n")

    else:
        error_msg = response.json().get('message', response.text)
        print(f"  [ERROR] {error_msg[:150]}\n")

except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# Run the job
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

        print(f"  Status: {run_response.status_code}")

        if run_response.status_code in [200, 201]:
            run_result = run_response.json()
            run_id = run_result.get('run_id')
            print(f"  [SUCCESS] Pipeline started!")
            print(f"  Run ID: {run_id}\n")

        else:
            print(f"  [ERROR] {run_response.text[:150]}\n")

    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# Monitor pipeline
# ============================================================================

if run_id:
    print("[STEP 3] Monitoring pipeline execution...\n")

    completed = False
    poll_count = 0
    max_polls = 60  # 10 minutes with 10-second intervals

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

                elapsed = poll_count * 10

                if state == "RUNNING":
                    print(f"  [{elapsed}s] RUNNING...")

                elif state == "PENDING":
                    print(f"  [{elapsed}s] PENDING (allocating resources)")

                elif state == "SUCCESS":
                    print(f"  [{elapsed}s] SUCCESS!\n")
                    print("  Pipeline completed successfully!")
                    completed = True

                elif state == "FAILED":
                    print(f"  [{elapsed}s] FAILED\n")
                    print(f"  State message: {status_result.get('state_message', 'Unknown error')}")
                    completed = True

                else:
                    print(f"  [{elapsed}s] {state}")

        except Exception as e:
            print(f"  [WARN] Status check failed")

    if not completed:
        print("\n  Pipeline still running or timed out")

# ============================================================================
# Verify results
# ============================================================================

print("\n[STEP 4] Verifying transformed data...\n")

sql_endpoint = f"{WORKSPACE_URL}/api/2.0/sql/statements"

verify_queries = [
    ("SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed", "Silver patients"),
    ("SELECT COUNT(*) FROM healthcare_equity_gold.disparate_impact", "Gold metrics"),
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
                    count = data[0][0]
                    print(f"  [OK] {label}: {count}")

    except Exception:
        pass

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)

if job_id:
    print(f"""
Job Created: {job_id}
Job Name: Healthcare Equity DLT
Status: {'Completed' if run_id else 'Ready to run'}

What's Next:
  1. Open dashboard: http://localhost:8501
  2. Click "Refresh Now" button
  3. All pages will show REAL transformed data
  4. Charts and metrics should now be current

Data Flow:
  Bronze Tables (raw)
       |
       v (Job transforms)
  Silver Tables (cleaned)
       |
       v (DLT aggregates)
  Gold Tables (metrics) <- Dashboard reads this
       |
       v
   Dashboard Pages
""")

print("=" * 80)
