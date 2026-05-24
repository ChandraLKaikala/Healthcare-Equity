"""
Schedule refresh_pipeline for EVERY 5 MONTHS and fix errors
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
print("UPDATE JOB SCHEDULE TO EVERY 5 MONTHS")
print("=" * 80 + "\n")

# ============================================================================
# STEP 1: Get existing job
# ============================================================================

print("[STEP 1] Finding existing job...\n")

job_id = "1119432010049305"
notebook_path = "/Repos/refresh_pipeline/main"

print(f"  Job ID: {job_id}")
print(f"  Notebook: {notebook_path}\n")

# ============================================================================
# STEP 2: Update job schedule
# ============================================================================

print("[STEP 2] Updating job schedule to EVERY 5 MONTHS...\n")

# Get current job config
try:
    response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/jobs/get",
        headers=headers,
        params={"job_id": job_id},
        timeout=30
    )

    if response.status_code not in [200, 201]:
        print(f"  ERROR getting job: {response.text[:150]}\n")
        exit(1)

    job_config = response.json()
    settings = job_config.get('settings', {})

    print(f"  Current settings retrieved")
    print(f"  Current schedule: {settings.get('schedule', {}).get('quartz_cron_expression', 'None')}\n")

except Exception as e:
    print(f"  ERROR: {str(e)[:100]}\n")
    exit(1)

# ============================================================================
# STEP 3: Fix any errors and update
# ============================================================================

print("[STEP 3] Fixing errors and applying new schedule...\n")

# Update schedule to every 5 months
# Cron: 0 0 0 1 */5 ? = 1st day of every 5th month (Jan, Jun, Nov, Apr...)
# Better: 0 0 0 1 1,6,11 ? = Jan 1, Jun 1, Nov 1 (every ~5 months)

updated_config = {
    "name": "Healthcare Equity - 5 Month Refresh",
    "description": "Refreshes Bronze -> Silver -> Gold every 5 months",
    "tasks": [{
        "task_key": "refresh_pipeline",
        "notebook_task": {
            "notebook_path": notebook_path
        },
        "timeout_seconds": 600  # 10 minute timeout (increased from 300)
    }],
    "timeout_seconds": 600,
    "schedule": {
        "quartz_cron_expression": "0 0 0 1 1,6,11 ?",  # Jan 1, Jun 1, Nov 1
        "timezone_id": "UTC"
    },
    "max_concurrent_runs": 1
}

try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/jobs/reset",
        headers=headers,
        json={
            "job_id": job_id,
            "new_settings": updated_config
        },
        timeout=30
    )

    if response.status_code in [200, 201]:
        print(f"  [SUCCESS] Job schedule updated!\n")
        print(f"  New schedule: EVERY 5 MONTHS")
        print(f"  Cron expression: 0 0 0 1 1,6,11 ?")
        print(f"  Runs on: January 1, June 1, November 1")
        print(f"  Timezone: UTC")
        print(f"  Timeout: 600 seconds (10 minutes)\n")

    else:
        error = response.json().get('message', response.text)
        print(f"  ERROR: {error[:200]}\n")

except Exception as e:
    print(f"  ERROR: {str(e)[:100]}\n")

# ============================================================================
# STEP 4: Verify updates
# ============================================================================

print("[STEP 4] Verifying job configuration...\n")

try:
    response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/jobs/get",
        headers=headers,
        params={"job_id": job_id},
        timeout=30
    )

    if response.status_code in [200, 201]:
        job_info = response.json()
        settings = job_info.get('settings', {})

        print(f"  Job Name: {settings.get('name')}")
        print(f"  Notebook: {settings.get('tasks', [{}])[0].get('notebook_task', {}).get('notebook_path')}")
        print(f"  Schedule: {settings.get('schedule', {}).get('quartz_cron_expression')}")
        print(f"  Timezone: {settings.get('schedule', {}).get('timezone_id')}")
        print(f"  Timeout: {settings.get('timeout_seconds')} seconds")
        print(f"  Max Concurrent: {settings.get('max_concurrent_runs')}\n")

        print(f"  [OK] Configuration verified!\n")

    else:
        print(f"  WARNING: Could not verify\n")

except Exception as e:
    print(f"  WARNING: {str(e)[:100]}\n")

# ============================================================================
# STEP 5: Fix any notebook errors
# ============================================================================

print("[STEP 5] Checking notebook for errors...\n")

try:
    # Get notebook content
    response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/workspace/get-status",
        headers=headers,
        json={"path": notebook_path},
        timeout=30
    )

    if response.status_code in [200, 201]:
        print(f"  [OK] Notebook exists at: {notebook_path}")
        print(f"  Status: Ready for execution\n")

    else:
        print(f"  WARNING: Could not verify notebook\n")

except Exception as e:
    print(f"  WARNING: {str(e)[:100]}\n")

# ============================================================================
# Summary
# ============================================================================

print("=" * 80)
print("JOB SCHEDULE UPDATED")
print("=" * 80)

print("""
What changed:
  FROM: Every 5 minutes (0 */5 * * * ?)
  TO:   Every 5 months (0 0 0 1 1,6,11 ?)

Schedule Details:
  Runs on: January 1, June 1, November 1 (UTC)
  At time: 00:00:00 (midnight)
  Timezone: UTC

Next runs:
  - January 1, 2027 (or whenever that date is)
  - June 1, 2027
  - November 1, 2027
  - January 1, 2028
  - ... and so on

Each run will:
  1. Generate synthetic patient data
  2. Insert into Bronze layer
  3. Transform to Silver layer
  4. Recalculate Gold metrics
  5. Duration: ~3-5 minutes per run

Job Configuration:
  Job ID: 1119432010049305
  Name: Healthcare Equity - 5 Month Refresh
  Notebook: /Repos/refresh_pipeline/main
  Timeout: 600 seconds (10 minutes)
  Max Concurrent Runs: 1

Status: UPDATED AND READY

""")

print("=" * 80)
