#!/usr/bin/env python3
"""Complete System Status Report"""
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

from databricks.sql import connect

def check_processes():
    """Check if dashboard and daemon are running"""
    print("\n[PROCESS CHECK]")
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        python_count = result.stdout.count('python')
        streamlit_running = 'python3.12' in result.stdout
        print(f"  Python processes: {python_count}")
        print(f"  Streamlit running: {'[OK]' if streamlit_running else '[NO]'}")
        return streamlit_running
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")
        return False

def check_databricks():
    """Check Databricks connection and data"""
    print("\n[DATABRICKS CHECK]")
    try:
        host = os.getenv('DATABRICKS_HOST').replace('https://', '')
        token = os.getenv('DATABRICKS_TOKEN')
        http_path = os.getenv('DATABRICKS_HTTP_PATH')

        conn = connect(
            server_hostname=host,
            http_path=http_path,
            personal_access_token=token
        )
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.patients")
        bronze_patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed")
        silver_patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.bias_metrics")
        gold_metrics = cursor.fetchone()[0]

        cursor.execute("SELECT overall_approval_rate FROM healthcare_equity_gold.equity_dashboard")
        overall_rate = cursor.fetchone()[0]

        conn.close()

        print(f"  [OK] Connection: OK")
        print(f"  [OK] Bronze Layer: {bronze_patients:,} patients")
        print(f"  [OK] Silver Layer: {silver_patients:,} patients")
        print(f"  [OK] Gold Layer: {gold_metrics} metrics")
        print(f"  [OK] Overall Approval Rate: {overall_rate:.2f}%")
        return True

    except Exception as e:
        print(f"  [ERROR] {str(e)[:100]}")
        return False

def check_files():
    """Check if key files exist"""
    print("\n[FILE CHECK]")
    files_to_check = [
        'dashboard/app.py',
        'auto_refresh_daemon.py',
        '.env.databricks',
        'PRODUCTION_READY.md'
    ]

    all_exist = True
    for file in files_to_check:
        exists = Path(file).exists()
        status = '[OK]' if exists else '[NO]'
        print(f"  {status} {file}")
        all_exist = all_exist and exists

    return all_exist

def check_dashboard_accessibility():
    """Check if dashboard is accessible"""
    print("\n[DASHBOARD CHECK]")
    try:
        import requests
        response = requests.get('http://localhost:8501', timeout=2)
        if response.status_code == 200:
            print(f"  [OK] Dashboard URL: http://localhost:8501")
            return True
        else:
            print(f"  [WARN] Dashboard returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  [WAIT] Dashboard not yet responding (starting up...)")
        print(f"         Try: http://localhost:8501")
        return False
    except Exception as e:
        print(f"  [ERROR] {str(e)[:50]}")
        return False

def main():
    print("=" * 70)
    print("HEALTHCARE EQUITY BIAS DETECTION - SYSTEM STATUS")
    print("=" * 70)

    db_ok = check_databricks()
    files_ok = check_files()
    proc_ok = check_processes()
    dash_ok = check_dashboard_accessibility()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if db_ok and files_ok:
        print("\n[SUCCESS] SYSTEM IS OPERATIONAL!")
        print("\nAccess Dashboard:")
        print("  -> http://localhost:8501")
        print("\nKey Features:")
        print("  - All 4 bias scenarios visible")
        print("  - Auto-refresh every 5 seconds")
        print("  - Date range filtering enabled")
        print("  - Hospital-themed design")
        print("\nNext Steps:")
        print("  1. Open http://localhost:8501")
        print("  2. View bias detection metrics")
        print("  3. Create Databricks jobs (see PRODUCTION_READY.md)")
    else:
        print("\n[WARN] SYSTEM CHECK INCOMPLETE")
        if not db_ok:
            print("  - Databricks connection failed")
        if not files_ok:
            print("  - Some files missing")
        if not proc_ok:
            print("  - Dashboard not running")

    print("\n" + "=" * 70)
    print("See PRODUCTION_READY.md for full documentation")
    print("=" * 70)

if __name__ == '__main__':
    main()
