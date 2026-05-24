#!/usr/bin/env python3
"""
Trigger Job #3 to refresh all data
"""

import os
import requests
import time

# Load credentials
host = os.getenv('DATABRICKS_HOST', 'dbc-ed229308-c6a7.cloud.databricks.com')
token = os.getenv('DATABRICKS_TOKEN', 'dapida82b1e1d2b8f14b28cba8a12cc58ee8')

if not host.startswith('https://'):
    host = f'https://{host}'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

JOB_3_ID = 432861690444081

print("=" * 70)
print("TRIGGERING JOB #3: COMPLETE PIPELINE")
print("=" * 70)
print()

# Trigger job
url = f'{host}/api/2.0/jobs/run-now'
payload = {'job_id': JOB_3_ID}

print(f"[*] Starting Job #{JOB_3_ID}...")
response = requests.post(url, json=payload, headers=headers, timeout=30)

if response.status_code == 200:
    result = response.json()
    run_id = result.get('run_id')
    print(f"[+] SUCCESS! Job started")
    print(f"    Run ID: {run_id}")
    print()

    # Monitor job
    print("[*] Monitoring job progress...")
    print()

    start_time = time.time()
    max_wait = 600  # 10 minutes

    while time.time() - start_time < max_wait:
        # Get job status
        status_url = f'{host}/api/2.0/jobs/runs/get'
        status_response = requests.get(
            status_url,
            params={'run_id': run_id},
            headers=headers,
            timeout=10
        )

        if status_response.status_code == 200:
            status_data = status_response.json()
            state = status_data.get('state')
            elapsed = int(time.time() - start_time)

            print(f"    [{elapsed:3d}s] State: {state}")

            if state == 'TERMINATED':
                state_message = status_data.get('state_message', '')
                print()
                print("[+] JOB COMPLETED SUCCESSFULLY!")
                print(f"    Final state: {state}")
                print(f"    Message: {state_message}")
                print()
                print("Data has been refreshed:")
                print("    [*] Bronze: New mutations added (INSERT/UPSERT/DELETE)")
                print("    [*] Silver: Transformed with enriched data")
                print("    [*] Gold: Bias metrics aggregated and updated")
                print()
                print(">>> Refresh your dashboard: Press F5 at http://localhost:8502")
                break
            elif state in ['INTERNAL_ERROR', 'SKIPPED']:
                print()
                print(f"[-] Job failed: {state}")
                print(f"    Message: {status_data.get('state_message', '')}")
                break

        time.sleep(5)

else:
    print(f"[-] Error: {response.status_code}")
    print(f"    {response.text[:300]}")
