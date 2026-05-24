"""
Check what error occurred in the DLT job
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

env_path = os.path.join(Path(__file__).parent, '.env.databricks')
load_dotenv(env_path)

HOST = os.getenv('DATABRICKS_HOST')
TOKEN = os.getenv('DATABRICKS_TOKEN')

WORKSPACE_URL = f"https://{HOST.replace('https://', '')}"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("CHECKING JOB FAILURE")
print("=" * 80 + "\n")

# Get all jobs
print("[STEP 1] Finding Healthcare Equity DLT job...\n")

try:
    response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/jobs/list",
        headers=headers,
        timeout=30
    )

    if response.status_code in [200, 201]:
        jobs = response.json().get('jobs', [])

        job_id = None
        for job in jobs:
            if 'Healthcare Equity DLT' in job.get('settings', {}).get('name', ''):
                job_id = job.get('job_id')
                print(f"Found job: {job.get('settings', {}).get('name')}")
                print(f"Job ID: {job_id}\n")
                break

        if not job_id:
            print("[WARN] Healthcare Equity DLT job not found")
            print("Available jobs:")
            for job in jobs[:5]:
                print(f"  - {job.get('settings', {}).get('name')} (ID: {job.get('job_id')})")
            exit(1)

        # ============================================================================
        # Get job runs
        # ============================================================================

        print("[STEP 2] Getting recent runs...\n")

        runs_response = requests.get(
            f"{WORKSPACE_URL}/api/2.0/jobs/runs/list",
            headers=headers,
            params={"job_id": job_id, "limit": 10},
            timeout=30
        )

        if runs_response.status_code in [200, 201]:
            runs = runs_response.json().get('runs', [])

            if not runs:
                print("[WARN] No runs found for this job")
                exit(1)

            # Get the most recent run
            latest_run = runs[0]
            run_id = latest_run.get('run_id')
            state = latest_run.get('state')

            print(f"Latest Run ID: {run_id}")
            print(f"State: {state}")
            print(f"State Message: {latest_run.get('state_message', 'N/A')}\n")

            # ============================================================================
            # Get detailed run info
            # ============================================================================

            print("[STEP 3] Getting detailed error info...\n")

            detail_response = requests.get(
                f"{WORKSPACE_URL}/api/2.0/jobs/runs/get",
                headers=headers,
                params={"run_id": run_id},
                timeout=30
            )

            if detail_response.status_code in [200, 201]:
                run_detail = detail_response.json()

                print("Run Details:")
                print(f"  State: {run_detail.get('state')}")
                print(f"  State Message: {run_detail.get('state_message')}")
                print(f"  Start Time: {run_detail.get('start_time')}")
                print(f"  End Time: {run_detail.get('end_time')}")

                # Get task runs
                tasks = run_detail.get('tasks', [])
                if tasks:
                    print(f"\nTask Details:")
                    for task in tasks:
                        print(f"  Task Key: {task.get('task_key')}")
                        print(f"  State: {task.get('state')}")
                        print(f"  State Message: {task.get('state_message')}")

                # Try to get logs
                print("\n[STEP 4] Attempting to fetch logs...\n")

                log_response = requests.get(
                    f"{WORKSPACE_URL}/api/2.0/jobs/runs/get-output",
                    headers=headers,
                    params={"run_id": run_id},
                    timeout=30
                )

                if log_response.status_code in [200, 201]:
                    logs = log_response.json()
                    if 'logs' in logs:
                        print("Logs:")
                        print(logs['logs'][:2000])
                    if 'error' in logs:
                        print("\nError:")
                        print(logs['error'])
                else:
                    print(f"Could not fetch logs: {log_response.status_code}")

except Exception as e:
    print(f"[ERROR] {str(e)}\n")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
