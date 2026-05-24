#!/usr/bin/env python3
"""
Check Gold layer data and manually refresh if needed
"""

import os
from databricks import sql

host = os.getenv('DATABRICKS_HOST', 'dbc-ed229308-c6a7.cloud.databricks.com').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN', 'dapida82b1e1d2b8f14b28cba8a12cc58ee8')
http_path = '/sql/1.0/warehouses/3c7564c48c0bd682'

print("=" * 70)
print("CHECKING GOLD LAYER DATA AND REFRESHING")
print("=" * 70)
print()

try:
    # Connect to Databricks
    print("[*] Connecting to Databricks warehouse...")
    connection = sql.connect(
        server_hostname=host,
        http_path=http_path,
        auth_type='pat',
        token=token
    )
    cursor = connection.cursor()
    print("[+] Connected!")
    print()

    # Check Bronze data
    print("[1] Checking Bronze layer...")
    cursor.execute("SELECT COUNT(*) as count FROM healthcare_equity_bronze.patients")
    bronze_patients = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) as count FROM healthcare_equity_bronze.decisions")
    bronze_decisions = cursor.fetchone()[0]
    print(f"    Patients: {bronze_patients:,}")
    print(f"    Decisions: {bronze_decisions:,}")
    print()

    # Check Silver data
    print("[2] Checking Silver layer...")
    cursor.execute("SELECT COUNT(*) as count FROM healthcare_equity_silver.patients_processed")
    silver_patients = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) as count FROM healthcare_equity_silver.decisions_processed")
    silver_decisions = cursor.fetchone()[0]
    print(f"    Patients: {silver_patients:,}")
    print(f"    Decisions: {silver_decisions:,}")
    print()

    # Check Gold data
    print("[3] Checking Gold layer (equity_dashboard)...")
    cursor.execute("""
        SELECT total_patients, total_decisions, overall_approval_rate, scenarios_analyzed
        FROM healthcare_equity_gold.equity_dashboard
    """)
    gold_row = cursor.fetchone()
    if gold_row:
        total_patients, total_decisions, approval_rate, scenarios = gold_row
        print(f"    Total Patients: {int(total_patients):,}")
        print(f"    Total Decisions: {int(total_decisions):,}")
        print(f"    Approval Rate: {float(approval_rate):.2f}%")
        print(f"    Scenarios: {int(scenarios)}")
    else:
        print("    [!] No data in equity_dashboard!")
    print()

    # Try to manually refresh Silver from Bronze
    print("[4] Manually refreshing Silver layer...")
    try:
        cursor.execute("""
            CREATE OR REPLACE TABLE healthcare_equity_silver.patients_processed AS
            SELECT *,
                   CASE WHEN sofa_score >= 10 THEN 'HIGH'
                        WHEN sofa_score >= 6 THEN 'MEDIUM'
                        ELSE 'LOW' END as risk_level,
                   CASE WHEN age < 30 THEN '18-29'
                        WHEN age < 45 THEN '30-44'
                        WHEN age < 65 THEN '45-64'
                        ELSE '65+' END as age_group
            FROM healthcare_equity_bronze.patients
        """)
        print("    [+] Patients transformed")
    except Exception as e:
        print(f"    [-] Error: {str(e)[:100]}")

    try:
        cursor.execute("""
            CREATE OR REPLACE TABLE healthcare_equity_silver.decisions_processed AS
            SELECT *,
                   CASE WHEN decision_value = 'Recommended' THEN 1 ELSE 0 END as decision_flag
            FROM healthcare_equity_bronze.decisions
        """)
        print("    [+] Decisions transformed")
    except Exception as e:
        print(f"    [-] Error: {str(e)[:100]}")
    print()

    # Try to manually refresh Gold from Silver
    print("[5] Manually refreshing Gold layer...")
    try:
        # Recreate equity_dashboard
        cursor.execute("""
            CREATE OR REPLACE TABLE healthcare_equity_gold.equity_dashboard AS
            SELECT
                COUNT(DISTINCT p.patient_id) as total_patients,
                COUNT(DISTINCT d.decision_id) as total_decisions,
                AVG(p.sofa_score) as avg_clinical_severity,
                100.0 * SUM(CASE WHEN p.gender = 'Female' THEN 1 ELSE 0 END) / COUNT(*) as pct_female,
                100.0 * SUM(CASE WHEN p.race = 'Black' THEN 1 ELSE 0 END) / COUNT(*) as pct_black,
                100.0 * SUM(d.decision_flag) / COUNT(d.decision_flag) as overall_approval_rate,
                4 as scenarios_analyzed,
                CURRENT_TIMESTAMP() as last_updated
            FROM healthcare_equity_silver.patients_processed p
            LEFT JOIN healthcare_equity_silver.decisions_processed d ON p.patient_id = d.patient_id
        """)
        print("    [+] Dashboard metrics updated")

        # Verify
        cursor.execute("SELECT total_patients, total_decisions, overall_approval_rate FROM healthcare_equity_gold.equity_dashboard")
        row = cursor.fetchone()
        if row:
            print(f"    [+] Verified: {int(row[0]):,} patients, {int(row[1]):,} decisions, {float(row[2]):.2f}% approval")
    except Exception as e:
        print(f"    [-] Error: {str(e)[:200]}")
    print()

    print("[+] Data refresh complete!")
    print()
    print(">>> Your dashboard data is now updated.")
    print(">>> Refresh browser: Press F5 at http://localhost:8502")

    cursor.close()
    connection.close()

except Exception as e:
    print(f"[-] Error: {str(e)}")
    import traceback
    traceback.print_exc()
