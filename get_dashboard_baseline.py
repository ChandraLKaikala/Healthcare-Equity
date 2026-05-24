#!/usr/bin/env python3
"""
Get current baseline metrics to track changes over time
"""

import os
from datetime import datetime
from databricks import sql

host = os.getenv('DATABRICKS_HOST', 'dbc-ed229308-c6a7.cloud.databricks.com').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN', 'dapida82b1e1d2b8f14b28cba8a12cc58ee8')
http_path = '/sql/1.0/warehouses/3c7564c48c0bd682'

print("=" * 80)
print("DASHBOARD BASELINE METRICS - SNAPSHOT FOR COMPARISON")
print("=" * 80)
print()
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

try:
    connection = sql.connect(
        server_hostname=host,
        http_path=http_path,
        auth_type='pat',
        token=token
    )
    cursor = connection.cursor()

    # ========================================================================
    # EXECUTIVE SUMMARY METRICS (Page 1)
    # ========================================================================
    print("[1] EXECUTIVE SUMMARY PAGE - KPI Cards")
    print("-" * 80)

    cursor.execute("""
        SELECT
            total_patients,
            total_decisions,
            overall_approval_rate,
            pct_female,
            pct_black,
            scenarios_analyzed
        FROM healthcare_equity_gold.equity_dashboard
    """)
    summary = cursor.fetchone()
    if summary:
        patients, decisions, approval_rate, pct_female, pct_black, scenarios = summary
        print(f"    Total Patients:        {int(patients):>10,}")
        print(f"    Total Decisions:       {int(decisions):>10,}")
        print(f"    Overall Approval Rate: {float(approval_rate):>10.2f}%")
        print(f"    % Female:              {float(pct_female):>10.2f}%")
        print(f"    % Black:               {float(pct_black):>10.2f}%")
        print(f"    Scenarios Analyzed:    {int(scenarios):>10}")
    print()

    # ========================================================================
    # BIAS DETECTION METRICS (Page 2)
    # ========================================================================
    print("[2] BIAS DETECTION PAGE - Disparate Impact by Scenario")
    print("-" * 80)

    cursor.execute("""
        SELECT
            scenario_type,
            ROUND(disparate_impact_ratio, 4) as dir,
            eighty_percent_rule_status
        FROM healthcare_equity_gold.disparate_impact
        ORDER BY scenario_type
    """)

    results = cursor.fetchall()
    for row in results:
        scenario, dir_val, status = row
        print(f"    {scenario:30s} DIR: {float(dir_val):6.4f}  [{status}]")
    print()

    # ========================================================================
    # BIAS METRICS DETAIL (Page 2)
    # ========================================================================
    print("[3] BIAS DETECTION PAGE - Approval Rates by Race & Scenario")
    print("-" * 80)

    cursor.execute("""
        SELECT
            scenario_type,
            race,
            ROUND(100.0 * SUM(CASE WHEN decision_flag = 1 THEN 1 ELSE 0 END) /
                  NULLIF(COUNT(*), 0), 2) as approval_rate,
            COUNT(*) as sample_size
        FROM healthcare_equity_silver.patients_processed p
        LEFT JOIN healthcare_equity_silver.decisions_processed d
            ON p.patient_id = d.patient_id
        WHERE d.scenario_type IS NOT NULL AND p.race IN ('White', 'Black')
        GROUP BY scenario_type, race
        ORDER BY scenario_type, race DESC
    """)

    results = cursor.fetchall()
    for row in results:
        scenario, race, approval, sample = row
        print(f"    {scenario:30s} {race:8s} Approval: {float(approval):6.2f}%  N={int(sample):5,}")
    print()

    # ========================================================================
    # PROVIDER ACCOUNTABILITY (Page 4)
    # ========================================================================
    print("[4] OUTCOME TRACKING PAGE - Provider Equity Scores")
    print("-" * 80)

    cursor.execute("""
        SELECT *
        FROM healthcare_equity_gold.provider_accountability
        LIMIT 5
    """)

    results = cursor.fetchall()
    if results:
        cols = [desc[0] for desc in cursor.description]
        for i, row in enumerate(results):
            print(f"    Provider {i+1}: {dict(zip(cols, row))}")
    else:
        print("    [No provider data yet]")
    print()

    # ========================================================================
    # WHAT TO WATCH FOR CHANGES
    # ========================================================================
    print("[WHAT TO WATCH] Metrics That Change When Data Refreshes")
    print("-" * 80)
    print("""
    THESE WILL INCREASE (every 1-2 minutes with new mutations):

    1. Total Patients count
       - Current: {patients}
       - Will grow by ~100 every minute
       - Watch at: Executive Summary page, top left KPI card

    2. Total Decisions count
       - Current: {decisions}
       - Will grow by ~150 every minute
       - Watch at: Executive Summary page, second KPI card

    3. Approval Rate (might shift slightly)
       - Current: {approval_rate:.2f}%
       - Will stay ~50% due to consistent bias injection
       - Watch at: Executive Summary page, third KPI card

    ========================================================================

    THESE WILL VARY (fluctuate with demographic mix of new patients):

    4. Race/Gender breakdown percentages
       - Current: {pct_female:.2f}% Female, {pct_black:.2f}% Black
       - Will vary by ±1-2% as new data added
       - Watch at: Executive Summary page, demographic cards

    5. Disparate Impact Ratios (by scenario)
       - Current: ~0.627 for Cardiac Cath (SEVERE)
       - Will stay similar due to hardcoded bias patterns
       - Watch at: Bias Detection page, forest plot chart

    6. Sample sizes in demographic breakdowns
       - Will increase as more decisions accumulate
       - Watch at: Bias Detection page, bottom table

    """.format(
        patients=int(patients) if summary else "?",
        decisions=int(decisions) if summary else "?",
        approval_rate=float(approval_rate) if summary else 0,
        pct_female=float(pct_female) if summary else 0,
        pct_black=float(pct_black) if summary else 0
    ))

    print("=" * 80)
    print("TO TEST DATA REFRESH:")
    print("=" * 80)
    print("""
    1. Note down the "Total Patients" number above: {patients}

    2. Wait 2-3 minutes (or run Job #3)

    3. Refresh your dashboard (F5)

    4. Check Executive Summary page

    5. "Total Patients" should be HIGHER (increased by ~200-300)

    If the number is HIGHER → Dashboard is working and data is refreshing
    If the number is SAME → Data isn't flowing or dashboard isn't refreshing

    """.format(patients=int(patients) if summary else "?"))

    cursor.close()
    connection.close()

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
