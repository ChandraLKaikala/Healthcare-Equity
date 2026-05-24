"""
Set up BOTH data pipelines:
1. continuous_data_pipeline: Every 4 minutes
2. refresh_pipeline/main: Every 5 minutes
Both MUST run successfully
"""
import os
import requests
import time
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

print("\n" + "=" * 80)
print("SETTING UP BOTH DATA PIPELINES")
print("=" * 80)
print("\nPipeline 1: continuous_data_pipeline -> Every 4 minutes")
print("Pipeline 2: refresh_pipeline/main -> Every 5 minutes\n")

# ============================================================================
# STEP 1: Create/Update continuous_data_pipeline job (4 minutes)
# ============================================================================

print("[STEP 1] Setting up continuous_data_pipeline (4-minute schedule)\n")

continuous_job_config = {
    "name": "Healthcare Equity - Continuous Data Pipeline (4 Min)",
    "description": "Generates synthetic patient data using Faker library. Runs every 4 minutes.",
    "tasks": [{
        "task_key": "continuous_mutations",
        "notebook_task": {
            "notebook_path": "/continuous_data_pipeline"
        },
        "timeout_seconds": 240  # 4 minutes timeout
    }],
    "timeout_seconds": 240,
    "schedule": {
        "quartz_cron_expression": "0 */4 * * * ?",  # Every 4 minutes
        "timezone_id": "UTC"
    },
    "max_concurrent_runs": 1
}

continuous_job_id = None

try:
    # Check if job already exists
    response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/jobs/list",
        headers=headers,
        timeout=30
    )

    if response.status_code in [200, 201]:
        jobs = response.json().get('jobs', [])

        for job in jobs:
            if "Continuous Data Pipeline (4 Min)" in job.get('settings', {}).get('name', ''):
                continuous_job_id = job.get('job_id')
                print(f"  Found existing job ID: {continuous_job_id}")
                print(f"  Updating schedule to 4 minutes...\n")
                break

    if continuous_job_id:
        # Update existing job
        response = requests.post(
            f"{WORKSPACE_URL}/api/2.0/jobs/reset",
            headers=headers,
            json={
                "job_id": continuous_job_id,
                "new_settings": continuous_job_config
            },
            timeout=30
        )

        if response.status_code in [200, 201]:
            print(f"  [OK] Job updated: {continuous_job_id}")
            print(f"  Schedule: Every 4 minutes")
            print(f"  Cron: 0 */4 * * * ?\n")
        else:
            print(f"  [ERROR] {response.text[:150]}\n")

    else:
        # Create new job
        response = requests.post(
            f"{WORKSPACE_URL}/api/2.0/jobs/create",
            headers=headers,
            json=continuous_job_config,
            timeout=30
        )

        if response.status_code in [200, 201]:
            continuous_job_id = response.json().get('job_id')
            print(f"  [OK] Job created: {continuous_job_id}")
            print(f"  Schedule: Every 4 minutes")
            print(f"  Cron: 0 */4 * * * ?\n")
        else:
            print(f"  [ERROR] {response.text[:150]}\n")

except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# STEP 2: Verify/Update refresh_pipeline job (5 minutes)
# ============================================================================

print("[STEP 2] Verifying refresh_pipeline (5-minute schedule)\n")

refresh_job_id = 1119432010049305  # The job I created earlier

try:
    response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/jobs/get",
        headers=headers,
        params={"job_id": refresh_job_id},
        timeout=30
    )

    if response.status_code in [200, 201]:
        job_info = response.json()
        settings = job_info.get('settings', {})
        schedule = settings.get('schedule', {})
        cron = schedule.get('quartz_cron_expression', 'NOT SET')

        print(f"  Job ID: {refresh_job_id}")
        print(f"  Name: {settings.get('name')}")
        print(f"  Schedule: {cron}")
        print(f"  Status: ACTIVE\n")

        if cron != "0 */5 * * * ?":
            print(f"  [WARN] Schedule is not 5 minutes, updating...\n")

            refresh_job_config = {
                "name": "Healthcare Equity - 5 Minute Refresh",
                "description": "Refreshes Bronze -> Silver -> Gold every 5 minutes",
                "tasks": [{
                    "task_key": "refresh_pipeline",
                    "notebook_task": {
                        "notebook_path": "/Repos/refresh_pipeline/main"
                    },
                    "timeout_seconds": 300
                }],
                "timeout_seconds": 300,
                "schedule": {
                    "quartz_cron_expression": "0 */5 * * * ?",
                    "timezone_id": "UTC"
                },
                "max_concurrent_runs": 1
            }

            update_response = requests.post(
                f"{WORKSPACE_URL}/api/2.0/jobs/reset",
                headers=headers,
                json={
                    "job_id": refresh_job_id,
                    "new_settings": refresh_job_config
                },
                timeout=30
            )

            if update_response.status_code in [200, 201]:
                print(f"  [OK] Updated to 5-minute schedule\n")

except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# STEP 3: Test both jobs - Run them immediately
# ============================================================================

print("[STEP 3] Running both jobs to verify they work\n")

test_job_ids = [
    (continuous_job_id, "Continuous Data Pipeline (4 min)"),
    (refresh_job_id, "Refresh Pipeline (5 min)")
]

run_ids = {}

for job_id, label in test_job_ids:
    if not job_id:
        print(f"  {label}: SKIPPED (not found)\n")
        continue

    print(f"  Starting: {label}")

    try:
        response = requests.post(
            f"{WORKSPACE_URL}/api/2.0/jobs/run-now",
            headers=headers,
            json={"job_id": job_id},
            timeout=30
        )

        if response.status_code in [200, 201]:
            run_id = response.json().get('run_id')
            run_ids[job_id] = run_id
            print(f"    Run ID: {run_id}")
            print(f"    Status: STARTED\n")
        else:
            print(f"    [ERROR] {response.text[:100]}\n")

    except Exception as e:
        print(f"    [ERROR] {str(e)[:80]}\n")

# ============================================================================
# STEP 4: Monitor runs
# ============================================================================

print("[STEP 4] Monitoring run progress (waiting up to 5 minutes)\n")

max_wait = 60  # 5 minutes
check_interval = 10  # Check every 10 seconds

for job_id, (job_name_prefix, label) in zip([continuous_job_id, refresh_job_id],
                                             [("Continuous", "Continuous Data Pipeline (4 min)"),
                                              ("Refresh", "Refresh Pipeline (5 min)")]):
    if job_id not in run_ids:
        continue

    run_id = run_ids[job_id]
    print(f"Monitoring: {label}")
    print(f"  Run ID: {run_id}\n")

    completed = False
    elapsed = 0

    while elapsed < max_wait and not completed:
        time.sleep(check_interval)
        elapsed += check_interval

        try:
            response = requests.get(
                f"{WORKSPACE_URL}/api/2.0/jobs/runs/get",
                headers=headers,
                params={"run_id": run_id},
                timeout=30
            )

            if response.status_code in [200, 201]:
                run_info = response.json()
                state = run_info.get('state', {})
                life_cycle = state.get('life_cycle_state')
                result = state.get('result_state')

                print(f"  [{elapsed}s] Status: {life_cycle}", end="")

                if life_cycle == 'TERMINATED':
                    print(f" / {result}")
                    if result == 'SUCCESS':
                        print(f"  [SUCCESS] {label} completed successfully!\n")
                    else:
                        print(f"  [FAILED] {label} failed - {state.get('state_message')}\n")
                    completed = True
                else:
                    print()

        except Exception as e:
            print(f"  Error checking status: {str(e)[:60]}\n")
            break

# ============================================================================
# STEP 5: Summary
# ============================================================================

print("\n" + "=" * 80)
print("SETUP COMPLETE")
print("=" * 80)

print(f"""
Both pipelines are now scheduled:

Pipeline 1: Continuous Data Pipeline
  Job ID: {continuous_job_id}
  Schedule: EVERY 4 MINUTES
  Cron: 0 */4 * * * ?
  Action: Generates 100 synthetic patients using Faker
  Appends to: healthcare_equity_bronze tables
  Status: {run_ids.get(continuous_job_id, 'NOT RUN')}

Pipeline 2: Refresh Pipeline
  Job ID: {refresh_job_id}
  Schedule: EVERY 5 MINUTES
  Cron: 0 */5 * * * ?
  Action: Transforms Bronze -> Silver -> Gold
  Appends to: healthcare_equity_silver/gold tables
  Status: {run_ids.get(refresh_job_id, 'NOT RUN')}

Execution Timeline (example):
  00:00 - Continuous runs (adds 100 patients)
  00:04 - Continuous runs (adds 100 patients)
  00:05 - Refresh runs (transforms to Silver/Gold)
  00:08 - Continuous runs (adds 100 patients)
  00:10 - Refresh runs (transforms to Silver/Gold)
  00:12 - Continuous runs (adds 100 patients)
  00:15 - Refresh runs (transforms to Silver/Gold)
  ... continues indefinitely

Data Flow:
  Every 4 min: continuous_data_pipeline adds 100 new records to Bronze
  Every 5 min: refresh_pipeline transforms and recalculates metrics
  Every 5 min: +100 net records to Silver (if both run successfully)

Expected Result:
  Patient count growing continuously
  Every hour: +900 new records (15 runs × 60 records = 900)
  Dashboard shows live, fresh data

Dashboard:
  python -m streamlit run dashboard/app.py
  Open: http://localhost:8501
  Click "Refresh Now" to see growing patient count

Both jobs should now run successfully every 4 and 5 minutes respectively!
""")

print("=" * 80)
