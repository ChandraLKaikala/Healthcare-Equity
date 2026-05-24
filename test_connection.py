#!/usr/bin/env python3
"""Test Databricks connection and verify data"""
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

from databricks.sql import connect

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

print("=" * 70)
print("TESTING DATABRICKS CONNECTION")
print("=" * 70)
print(f"\nHost: {host}")
print(f"HTTP Path: {http_path}")
print(f"Token: {token[:20]}...")

try:
    print("\nConnecting to Databricks...")
    conn = connect(
        server_hostname=host,
        http_path=http_path,
        personal_access_token=token
    )
    cursor = conn.cursor()
    print("[OK] Connected successfully!")

    # Check BRONZE layer
    print("\n[BRONZE LAYER]")
    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.patients")
    patients_count = cursor.fetchone()[0]
    print(f"  Patients: {patients_count:,}")

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.decisions")
    decisions_count = cursor.fetchone()[0]
    print(f"  Decisions: {decisions_count:,}")

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.outcomes")
    outcomes_count = cursor.fetchone()[0]
    print(f"  Outcomes: {outcomes_count:,}")

    # Check SILVER layer
    print("\n[SILVER LAYER]")
    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed")
    silver_patients = cursor.fetchone()[0]
    print(f"  Patients: {silver_patients:,}")

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.decisions_processed")
    silver_decisions = cursor.fetchone()[0]
    print(f"  Decisions: {silver_decisions:,}")

    # Check GOLD layer
    print("\n[GOLD LAYER]")
    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.bias_metrics")
    bias_metrics = cursor.fetchone()[0]
    print(f"  Bias Metrics: {bias_metrics}")

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.equity_dashboard")
    dashboard = cursor.fetchone()[0]
    print(f"  Dashboard: {dashboard}")

    # Check columns in bias_metrics
    print("\n[BIAS_METRICS COLUMNS]")
    cursor.execute("SELECT * FROM healthcare_equity_gold.bias_metrics LIMIT 1")
    cols = [desc[0] for desc in cursor.description]
    for col in cols:
        print(f"  - {col}")

    # Check a sample row
    print("\n[SAMPLE DATA from bias_metrics]")
    cursor.execute("""
    SELECT
        scenario_type,
        race,
        gender,
        approval_rate,
        total_decisions,
        unique_patients
    FROM healthcare_equity_gold.bias_metrics
    LIMIT 3
    """)

    for row in cursor.fetchall():
        print(f"  {row}")

    # Check scenarios
    print("\n[SCENARIOS IN DATA]")
    cursor.execute("SELECT DISTINCT scenario_type FROM healthcare_equity_gold.bias_metrics")
    scenarios = cursor.fetchall()
    for scenario in scenarios:
        print(f"  - {scenario[0]}")

    conn.close()
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)

except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
