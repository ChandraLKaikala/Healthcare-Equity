"""
Complete System Health Check
Verifies all components are working correctly
"""
import sys
sys.path.insert(0, '.')

from databricks_client import get_databricks_connection
from dotenv import load_dotenv
from pathlib import Path
import os

print("\n" + "=" * 80)
print("HEALTHCARE EQUITY BIAS DETECTION SYSTEM - HEALTH CHECK")
print("=" * 80 + "\n")

# Load credentials
env_path = os.path.join(Path('.'), '.env.databricks')
load_dotenv(env_path)

HOST = os.getenv('DATABRICKS_HOST')
TOKEN = os.getenv('DATABRICKS_TOKEN')

checks_passed = 0
checks_failed = 0

# ============================================================================
# 1. Databricks Connection
# ============================================================================
print("[1] Databricks Connection...")
try:
    conn = get_databricks_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchall()
    if result:
        print("    [PASS] Connected to Databricks warehouse\n")
        checks_passed += 1
    else:
        print("    [FAIL] No response from warehouse\n")
        checks_failed += 1
    conn.close()
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# 2. Bronze Layer Data
# ============================================================================
print("[2] Bronze Layer Data (Raw Input)...")
try:
    conn = get_databricks_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.patients_source")
    patient_count = cursor.fetchall()[0][0]

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_bronze.decisions_source")
    decision_count = cursor.fetchall()[0][0]

    conn.close()

    print(f"    - Patients: {patient_count}")
    print(f"    - Decisions: {decision_count}")

    if patient_count > 0 and decision_count > 0:
        print("    [PASS] Bronze layer populated\n")
        checks_passed += 1
    else:
        print("    [FAIL] Bronze layer empty\n")
        checks_failed += 1
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# 3. Silver Layer Data
# ============================================================================
print("[3] Silver Layer Data (Cleaned)...")
try:
    conn = get_databricks_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed")
    patient_count = cursor.fetchall()[0][0]

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_silver.decisions_processed")
    decision_count = cursor.fetchall()[0][0]

    conn.close()

    print(f"    - Processed Patients: {patient_count}")
    print(f"    - Processed Decisions: {decision_count}")

    if patient_count > 0 and decision_count > 0:
        print("    [PASS] Silver layer populated\n")
        checks_passed += 1
    else:
        print("    [WARN] Silver layer empty (may not have run DLT yet)\n")
        checks_failed += 1
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# 4. Gold Layer Metrics
# ============================================================================
print("[4] Gold Layer Metrics (Disparate Impact)...")
try:
    conn = get_databricks_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM healthcare_equity_gold.disparate_impact")
    metric_count = cursor.fetchall()[0][0]

    cursor.execute("SELECT DISTINCT scenario_type FROM healthcare_equity_gold.disparate_impact")
    scenarios = [row[0] for row in cursor.fetchall()]

    conn.close()

    print(f"    - Disparate Impact records: {metric_count}")
    print(f"    - Scenarios: {scenarios}")

    if metric_count > 0:
        print("    [PASS] Gold layer has disparities\n")
        checks_passed += 1
    else:
        print("    [WARN] Gold layer empty (may not have run DLT yet)\n")
        checks_failed += 1
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# 5. Dashboard Query - Executive Summary
# ============================================================================
print("[5] Dashboard Query - Executive Summary...")
try:
    conn = get_databricks_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        COUNT(DISTINCT race) as demographics,
        ROUND(AVG(approval_rate), 2) as avg_approval_rate,
        COUNT(*) as total_metrics
    FROM healthcare_equity_gold.disparate_impact
    """

    cursor.execute(query)
    results = cursor.fetchall()

    if results and results[0][0]:
        row = results[0]
        print(f"    - Demographics: {row[0]}")
        print(f"    - Avg Approval Rate: {row[1]}%")
        print(f"    - Total Metrics: {row[2]}")
        print("    [PASS] Executive summary query works\n")
        checks_passed += 1
    else:
        print("    [FAIL] No data for summary\n")
        checks_failed += 1

    conn.close()
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# 6. Dashboard Query - Bias Detection
# ============================================================================
print("[6] Dashboard Query - Bias Detection (Cardiac)...")
try:
    conn = get_databricks_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        race,
        ROUND(100.0 * SUM(CASE WHEN decision_flag = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as approval_rate,
        COUNT(*) as total_decisions
    FROM healthcare_equity_silver.patients_processed p
    LEFT JOIN healthcare_equity_silver.decisions_processed d
        ON p.patient_id = d.patient_id
    WHERE d.scenario_type = 'cardiac_catheterization'
    AND p.race IS NOT NULL
    GROUP BY race
    ORDER BY race
    """

    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        print(f"    - Results: {len(results)} demographic groups")
        for row in results[:3]:
            print(f"      {row[0]}: {row[1]}% approval rate ({row[2]:,} decisions)")
        print("    [PASS] Bias detection query works\n")
        checks_passed += 1
    else:
        print("    [FAIL] No results for cardiac catheterization\n")
        checks_failed += 1

    conn.close()
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# 7. Environment Variables
# ============================================================================
print("[7] Environment Configuration...")
try:
    if HOST and TOKEN:
        print(f"    - Databricks Host: {'[SET]' if HOST else '[MISSING]'}")
        print(f"    - API Token: {'[SET]' if TOKEN else '[MISSING]'}")
        print("    [PASS] Credentials configured\n")
        checks_passed += 1
    else:
        print("    [FAIL] Missing credentials\n")
        checks_failed += 1
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# 8. Dashboard Client
# ============================================================================
print("[8] Dashboard HTTP Client...")
try:
    from databricks_client import DatabricksConnection
    conn = DatabricksConnection()
    print(f"    - Client initialized: Yes")
    print(f"    - Auth method: Bearer token (no OAuth)")
    print("    [PASS] Dashboard client ready\n")
    checks_passed += 1
except Exception as e:
    print(f"    [FAIL] {str(e)[:80]}\n")
    checks_failed += 1

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 80)
print("HEALTH CHECK SUMMARY")
print("=" * 80)
print(f"\nTests Passed: {checks_passed}/8")
print(f"Tests Failed: {checks_failed}/8")

if checks_failed == 0:
    print("\n[SUCCESS] All systems operational!")
    print("\nYou can now:")
    print("  1. Start dashboard: streamlit run dashboard/app.py")
    print("  2. Open: http://localhost:8501")
    print("  3. All 6 pages should work with REAL Databricks data")
    print("\nOptional:")
    print("  - Create DLT pipeline for automated daily refresh")
    print("  - Export regulatory reports for compliance")
    print("  - Generate AI summaries for clinical teams")
elif checks_failed <= 2:
    print("\n[WARNING] Most systems operational")
    print("  - Dashboard will work but with limited data")
    print("  - May need to run DLT pipeline for full metrics")
    print("  - Check SYSTEM_READY_REPORT.md for troubleshooting")
else:
    print("\n[ERROR] Multiple systems offline")
    print("  - Check .env.databricks credentials")
    print("  - Verify Databricks workspace is accessible")
    print("  - Run: python create_dlt_pipeline_api.py")

print("\n" + "=" * 80)
