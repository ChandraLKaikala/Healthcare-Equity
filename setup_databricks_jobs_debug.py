#!/usr/bin/env python3
"""
Setup Databricks Jobs - Debug Version
Test different API endpoints
"""
import os
import sys
import requests
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')

# Ensure host has https://
if not host.startswith('https://'):
    host = 'https://' + host

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

print("="*70)
print("DEBUGGING DATABRICKS API")
print("="*70)
print(f"Host: {host}\n")

# Try different API endpoints
endpoints = [
    f"{host}/api/2.0/jobs/list",
    f"{host}/api/2.1/jobs/list",
]

for endpoint in endpoints:
    print(f"\nTrying endpoint: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")

# Try listing workspaces
print("\n\nTrying workspace API:")
try:
    response = requests.get(f"{host}/api/2.0/workspace/get-status",
                           headers=headers,
                           params={"path": "/"})
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"  Error: {str(e)[:100]}")

# Try the simple test endpoint
print("\n\nTrying simple API test:")
try:
    response = requests.get(f"{host}/api/2.0/clusters/list",
                           headers=headers)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  [OK] API is working!")
    else:
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"  Error: {str(e)[:100]}")
