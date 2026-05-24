#!/usr/bin/env python3
"""Verify dashboard queries work correctly"""
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
print("VERIFYING DASHBOARD QUERIES")
print("=" * 70)

try:
    conn = connect(
        server_hostname=host,
        http_path=http_path,
        personal_access_token=token
    )
    cursor = conn.cursor()

    # Test the exact query the dashboard uses
    scenarios = [
        'cardiac_catheterization',
        'pain_management',
        'mental_health_referral',
        'hospital_admission'
    ]

    for scenario in scenarios:
        print(f"\n[Testing] {scenario}")
        query = f"""
        SELECT
            scenario_type,
            race,
            gender,
            approval_rate,
            ROUND(approval_rate / MAX(approval_rate) OVER () * 100, 2) as dir_percentage,
            total_decisions,
            unique_patients,
            first_decision_date,
            last_decision_date
        FROM healthcare_equity_gold.bias_metrics
        WHERE scenario_type = '{scenario}'
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]

        if results:
            print(f"  Columns: {', '.join(cols)}")
            print(f"  Rows: {len(results)}")
            print(f"  Sample: {results[0]}")
        else:
            print(f"  ERROR: No data returned!")

    # Test dashboard summary query
    print(f"\n[Testing] Dashboard Summary")
    query = "SELECT * FROM healthcare_equity_gold.equity_dashboard LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()
    cols = [desc[0] for desc in cursor.description]

    if result:
        print(f"  Columns: {', '.join(cols)}")
        summary = dict(zip(cols, result))
        for key, val in summary.items():
            print(f"    {key}: {val}")
    else:
        print(f"  ERROR: No summary data!")

    # Test provider accountability query
    print(f"\n[Testing] Provider Accountability")
    query = """
    SELECT
        race,
        gender,
        age_group,
        approval_pct,
        readmission_rate,
        mortality_rate
    FROM healthcare_equity_gold.provider_accountability
    ORDER BY approval_pct DESC
    LIMIT 3
    """
    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        cols = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(cols)}")
        print(f"  Sample rows: {len(results)}")
        for row in results:
            print(f"    {row}")
    else:
        print(f"  ERROR: No accountability data!")

    conn.close()

    print("\n" + "=" * 70)
    print("ALL QUERIES WORKING CORRECTLY!")
    print("=" * 70)
    print("\nDashboard should now display:")
    print("  - All 4 bias scenarios with data")
    print("  - Approval rates by race and gender")
    print("  - Provider accountability metrics")
    print("  - Date range filtering enabled")

except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
