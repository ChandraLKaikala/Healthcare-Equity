#!/usr/bin/env python3
"""
Run Databricks jobs immediately to refresh all data.
This triggers Job #3 (complete pipeline) which auto-chains:
  Job 1: Bronze mutations (INSERT/UPSERT/DELETE)
  Job 2: Silver/Gold transformation
"""

import os
import requests
import json
import time
from urllib.parse import urljoin

# Load Databricks credentials
host = os.getenv('DATABRICKS_HOST', 'dbc-ed229308-c6a7.cloud.databricks.com')
token = os.getenv('DATABRICKS_TOKEN', 'dapida82b1e1d2b8f14b28cba8a12cc58ee8')

# Ensure host has https://
if not host.startswith('https://'):
    host = f'https://{host}'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Job IDs
JOB_3_ID = 432861690444081  # Complete chained pipeline

def run_job(job_id):
    """Run a Databricks job immediately"""
    url = urljoin(host, f'/api/2.1/jobs/run_now')
    payload = {
        'job_id': job_id
    }

    print(f"[*] Triggering Job #{job_id}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        run_id = result.get('run_id')
        print(f"[+] Job started successfully!")
        print(f"    Run ID: {run_id}")
        return run_id
    except requests.exceptions.RequestException as e:
        print(f"[-] Error starting job: {str(e)[:200]}")
        return None

def get_job_status(run_id):
    """Check job execution status"""
    url = urljoin(host, f'/api/2.1/jobs/runs/get')
    params = {'run_id': run_id}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        state = result.get('state', 'UNKNOWN')
        state_message = result.get('state_message', '')

        return state, state_message
    except requests.exceptions.RequestException as e:
        print(f"[-] Error checking status: {str(e)[:100]}")
        return None, None

def wait_for_job(run_id, max_wait=600):
    """Wait for job to complete (max 10 minutes)"""
    start = time.time()
    poll_interval = 5  # Check every 5 seconds

    while time.time() - start < max_wait:
        state, msg = get_job_status(run_id)

        if state is None:
            print("[!] Could not check status, waiting...")
            time.sleep(poll_interval)
            continue

        print(f"    Status: {state}")

        if state in ['TERMINATED', 'SKIPPED', 'INTERNAL_ERROR']:
            print(f"    Message: {msg}")
            return state

        time.sleep(poll_interval)

    print("[!] Job timeout - still running in background")
    return 'TIMEOUT'

def main():
    print("=" * 70)
    print("DATABRICKS PIPELINE TRIGGER - REFRESH ALL DATA")
    print("=" * 70)
    print()

    # Run Job #3 (complete chained pipeline)
    print("[1/3] Running Job #3: Complete Pipeline (Bronze > Silver > Gold)")
    print("-" * 70)
    run_id = run_job(JOB_3_ID)

    if run_id:
        print()
        print("[2/3] Waiting for job to complete...")
        print("-" * 70)
        final_state = wait_for_job(run_id)

        print()
        print("[3/3] Job execution summary")
        print("-" * 70)
        print(f"Final State: {final_state}")

        if final_state == 'TERMINATED':
            print("[+] Pipeline completed successfully!")
            print()
            print("Data should now be refreshed:")
            print("  [*] Bronze layer: Updated with INSERT/UPSERT/DELETE mutations")
            print("  [*] Silver layer: Transformed with risk_level, age_group, decision_flag")
            print("  [*] Gold layer: Aggregated with bias metrics and disparate impact ratios")
            print()
            print("Next: Refresh your dashboard (F5) to see updated data")
        elif final_state == 'TIMEOUT':
            print("[!] Job is still running in background (taking > 10 min)")
            print("    Check Databricks UI for progress")
        else:
            print(f"[!] Job finished with state: {final_state}")
    else:
        print("[-] Failed to start job")

if __name__ == '__main__':
    main()
