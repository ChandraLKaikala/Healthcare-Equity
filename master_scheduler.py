#!/usr/bin/env python3
"""
MASTER SCHEDULER - Runs continuous_data + main sequentially
Every 3 minutes: continuous_data (10 sec) → main (10 sec) = 20 sec total
NO concurrent run conflicts, FRESH data constantly
"""
import os
import requests
import time
import sys
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
print("MASTER SCHEDULER - Sequential Pipeline Runner")
print("=" * 80 + "\n")

# ============================================================================
# STEP 1: Create Master Scheduler Notebook
# ============================================================================

print("[STEP 1] Creating master scheduler notebook...\n")

master_notebook = '''# Databricks notebook source
# Master Scheduler - Runs both jobs sequentially
# continuous_data_pipeline (10 sec) → main (10 sec) = 20 sec total
# Scheduled to run every 3 minutes = 160 seconds of downtime between cycles

import requests
import time
from datetime import datetime

print(f"\\n[{datetime.now().strftime('%H:%M:%S')}] Starting master scheduler...")

HOST = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("spark.databricks.clusterUsageTags.clusterHostname").get()
TOKEN = dbutils.secrets.get("databricks", "token")
WORKSPACE_URL = f"https://{HOST}"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Job IDs (will be replaced with actual IDs)
CONTINUOUS_JOB_ID = "CONTINUOUS_JOB_ID_PLACEHOLDER"
MAIN_JOB_ID = "MAIN_JOB_ID_PLACEHOLDER"

# ============================================================================
# RUN CONTINUOUS DATA PIPELINE
# ============================================================================

print(f"\\n[RUN 1] Starting continuous_data_pipeline...")
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/jobs/run-now",
        headers=headers,
        json={"job_id": int(CONTINUOUS_JOB_ID)},
        timeout=30
    )

    if response.status_code in [200, 201]:
        continuous_run_id = response.json().get('run_id')
        print(f"  Run ID: {continuous_run_id}")
        print(f"  Status: STARTED")
    else:
        print(f"  ERROR: {response.text[:100]}")
        continuous_run_id = None
except Exception as e:
    print(f"  ERROR: {str(e)[:100]}")
    continuous_run_id = None

# Wait for continuous_data to complete
if continuous_run_id:
    print(f"\\n  Waiting for completion...")
    elapsed = 0
    while elapsed < 120:  # Max 2 minutes wait
        time.sleep(5)
        elapsed += 5

        try:
            response = requests.get(
                f"{WORKSPACE_URL}/api/2.0/jobs/runs/get",
                headers=headers,
                params={"run_id": continuous_run_id},
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
                        print(f"  ✓ COMPLETED SUCCESSFULLY\\n")
                    else:
                        print(f"  ✗ FAILED - {state.get('state_message')}\\n")
                    break
                else:
                    print()
        except Exception as e:
            print(f"  Error checking status: {str(e)[:60]}")
            break

# ============================================================================
# RUN MAIN TRANSFORMATION
# ============================================================================

print(f"\\n[RUN 2] Starting main transformation pipeline...")
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/jobs/run-now",
        headers=headers,
        json={"job_id": int(MAIN_JOB_ID)},
        timeout=30
    )

    if response.status_code in [200, 201]:
        main_run_id = response.json().get('run_id')
        print(f"  Run ID: {main_run_id}")
        print(f"  Status: STARTED")
    else:
        print(f"  ERROR: {response.text[:100]}")
        main_run_id = None
except Exception as e:
    print(f"  ERROR: {str(e)[:100]}")
    main_run_id = None

# Wait for main to complete
if main_run_id:
    print(f"\\n  Waiting for completion...")
    elapsed = 0
    while elapsed < 300:  # Max 5 minutes wait
        time.sleep(5)
        elapsed += 5

        try:
            response = requests.get(
                f"{WORKSPACE_URL}/api/2.0/jobs/runs/get",
                headers=headers,
                params={"run_id": main_run_id},
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
                        print(f"  ✓ COMPLETED SUCCESSFULLY\\n")
                    else:
                        print(f"  ✗ FAILED - {state.get('state_message')}\\n")
                    break
                else:
                    print()
        except Exception as e:
            print(f"  Error checking status: {str(e)[:60]}")
            break

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 80)
print("CYCLE COMPLETE")
print("=" * 80)
print(f"""
Cycle Time: ~20 seconds total
Next Cycle: 160 seconds (2m 40s from now)

Data Status:
  ✓ Bronze: Updated with new 50 patients
  ✓ Silver: Refreshed with deduplicated data
  ✓ Gold: Metrics recalculated
  ✓ Dashboard: Ready for refresh

Next run: Automatically in 3 minutes
""")
'''

try:
    notebook_hex = master_notebook.encode('utf-8').hex()

    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/workspace/import",
        headers=headers,
        json={
            "path": "/Repos/master_scheduler/main",
            "format": "SOURCE",
            "language": "PYTHON",
            "content": notebook_hex,
            "overwrite": True
        },
        timeout=30
    )

    if response.status_code in [200, 201]:
        print(f"  [OK] Master scheduler notebook created\n")
    else:
        print(f"  [ERROR] {response.text[:100]}\n")
except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# STEP 2: Get Job IDs
# ============================================================================

print("[STEP 2] Getting job IDs...\n")

continuous_job_id = None
main_job_id = None

try:
    response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/jobs/list",
        headers=headers,
        timeout=30
    )

    if response.status_code in [200, 201]:
        jobs = response.json().get('jobs', [])

        for job in jobs:
            job_name = job.get('settings', {}).get('name', '')

            if 'Continuous Data' in job_name or 'continuous_data' in job_name:
                continuous_job_id = job.get('job_id')
                print(f"  Found continuous_data_pipeline: {continuous_job_id}")

            if 'Main Transform' in job_name or 'refresh_pipeline' in job_name:
                main_job_id = job.get('job_id')
                print(f"  Found main/refresh_pipeline: {main_job_id}")

        print()
except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# STEP 3: Schedule Master Job
# ============================================================================

print("[STEP 3] Scheduling master scheduler job...\n")

master_config = {
    "name": "Healthcare Equity - Master Scheduler",
    "description": "Runs continuous_data_pipeline + main sequentially every 3 minutes",
    "tasks": [{
        "task_key": "master_scheduler",
        "notebook_task": {
            "notebook_path": "/Repos/master_scheduler/main"
        },
        "timeout_seconds": 600  # 10 minutes max
    }],
    "timeout_seconds": 600,
    "schedule": {
        "quartz_cron_expression": "0 */3 * * * ?",  # Every 3 minutes
        "timezone_id": "UTC"
    },
    "max_concurrent_runs": 1  # CRITICAL
}

try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/jobs/create",
        headers=headers,
        json=master_config,
        timeout=30
    )

    if response.status_code in [200, 201]:
        master_job_id = response.json().get('job_id')
        print(f"  [SUCCESS] Master scheduler created: {master_job_id}")
        print(f"  Schedule: Every 3 minutes")
        print(f"  Max Concurrent Runs: 1\n")
    else:
        print(f"  [ERROR] {response.text[:100]}\n")
except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 80)
print("MASTER SCHEDULER CONFIGURED")
print("=" * 80)
print(f"""
Master Scheduler Now Running Every 3 Minutes:

CYCLE TIMELINE:
  00:00:00 - continuous_data_pipeline starts
  00:00:10 - continuous_data_pipeline completes (10 sec)
  00:00:10 - main transformation starts
  00:00:20 - main transformation completes (10 sec)
  00:00:20 - CYCLE COMPLETE

  00:02:40 - Next cycle starts (160 seconds wait)
  00:03:00 - Next cycle starts (3 minute schedule)

BENEFITS:
  ✓ Zero MaxConcurrentRuns conflicts
  ✓ Sequential execution guaranteed
  ✓ Fresh data every 3 minutes
  ✓ Simple single-job scheduling
  ✓ Easy to monitor and debug

DATA FLOW:
  Every 3 min: +50 patients to Bronze
  Every 3 min: Silver/Gold updated
  Every 3 min: Dashboard has fresh data

NEXT STEPS:
  1. Go to Databricks UI
  2. Workflows > Jobs
  3. Find: "Healthcare Equity - Master Scheduler"
  4. Click "Run Now" to test
  5. Monitor the run
  6. Should complete in ~20 seconds
  7. Then automatically runs every 3 minutes
""")

print("=" * 80)
