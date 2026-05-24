#!/usr/bin/env python3
"""
Upload fixed notebooks to Databricks workspace
"""

import os
import base64
import requests
from urllib.parse import urljoin

host = os.getenv('DATABRICKS_HOST', 'dbc-ed229308-c6a7.cloud.databricks.com')
token = os.getenv('DATABRICKS_TOKEN', 'dapida82b1e1d2b8f14b28cba8a12cc58ee8')

if not host.startswith('https://'):
    host = f'https://{host}'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

def upload_notebook(file_path, notebook_path):
    """Upload a Python file as a Databricks notebook"""
    print(f"[*] Uploading {file_path} to {notebook_path}...")

    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()

    # Base64 encode
    encoded_content = base64.b64encode(content.encode()).decode()

    # Upload
    url = f'{host}/api/2.0/workspace/import'
    payload = {
        'path': notebook_path,
        'format': 'SOURCE',
        'language': 'PYTHON',
        'overwrite': True,
        'content': encoded_content
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            print(f"    [+] Uploaded successfully!")
            return True
        else:
            print(f"    [-] Error: {response.status_code}")
            print(f"        {response.text[:200]}")
            return False
    except Exception as e:
        print(f"    [-] Exception: {str(e)[:200]}")
        return False

def main():
    print("=" * 70)
    print("UPLOADING FIXED NOTEBOOKS TO DATABRICKS")
    print("=" * 70)
    print()

    # Upload fixed notebooks
    success = True

    success = upload_notebook(
        'continuous_data_pipeline.py',
        '/continuous_data_pipeline'
    ) and success

    success = upload_notebook(
        'transform_pipeline.py',
        '/transform_pipeline'
    ) and success

    print()
    if success:
        print("[+] All notebooks uploaded successfully!")
        print()
        print("The fixed notebooks are now in Databricks:")
        print("    /continuous_data_pipeline - Fixed column names")
        print("    /transform_pipeline - Fixed to use decision_value column")
        print()
        print("You can now re-run Job #3 without errors.")
    else:
        print("[-] Some uploads failed. Check errors above.")

if __name__ == '__main__':
    main()
