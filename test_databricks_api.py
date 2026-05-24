#!/usr/bin/env python3
"""
Test Databricks API connection and list available jobs
"""

import os
import requests
from urllib.parse import urljoin

# Load credentials
host = os.getenv('DATABRICKS_HOST', 'dbc-ed229308-c6a7.cloud.databricks.com')
token = os.getenv('DATABRICKS_TOKEN', 'dapida82b1e1d2b8f14b28cba8a12cc58ee8')

# Ensure host has https://
if not host.startswith('https://'):
    host = f'https://{host}'

print(f"Host: {host}")
print(f"Token: {token[:20]}...")
print()

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Test 1: Try to list jobs
print("[*] Testing /api/2.1/jobs/list...")
try:
    url = f'{host}/api/2.1/jobs/list'
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        jobs = response.json()
        print(f"[+] Found {len(jobs.get('jobs', []))} jobs")
        for job in jobs.get('jobs', [])[:5]:
            print(f"    - {job['settings']['name']} (ID: {job['job_id']})")
    else:
        print(f"[-] Error: {response.text[:200]}")
except Exception as e:
    print(f"[-] Exception: {str(e)[:200]}")

print()

# Test 2: Try alternative endpoint format
print("[*] Testing /api/2.0/jobs/list...")
try:
    url = f'{host}/api/2.0/jobs/list'
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        jobs = response.json()
        print(f"[+] Found {len(jobs.get('jobs', []))} jobs")
        for job in jobs.get('jobs', [])[:5]:
            print(f"    - {job['settings']['name']} (ID: {job['job_id']})")
    else:
        print(f"[-] Error: {response.text[:200]}")
except Exception as e:
    print(f"[-] Exception: {str(e)[:200]}")

print()

# Test 3: Try the Warehouse API
print("[*] Testing warehouse connection...")
try:
    # Try to query a simple table
    from databricks import sql

    connection = sql.connect(
        server_hostname=host.replace('https://', ''),
        http_path='/sql/1.0/warehouses/3c7564c48c0bd682',
        auth_type='pat',
        token=token
    )
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.equity_dashboard")
    result = cursor.fetchone()
    print(f"[+] Warehouse connected! Gold table has {result[0]} row(s)")
    cursor.close()
    connection.close()
except ImportError:
    print("[-] databricks SQL module not installed")
except Exception as e:
    print(f"[-] Error: {str(e)[:200]}")
