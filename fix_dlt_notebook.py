"""
Replace DLT notebook with corrected version
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

env_path = os.path.join(Path(__file__).parent, '.env.databricks')
load_dotenv(env_path)

HOST = os.getenv('DATABRICKS_HOST')
TOKEN = os.getenv('DATABRICKS_TOKEN')

WORKSPACE_URL = f"https://{HOST.replace('https://', '')}"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("FIXING DLT NOTEBOOK")
print("=" * 80 + "\n")

# Corrected DLT code (simpler, more robust)
dlt_code = '''# Databricks notebook source
import dlt
from pyspark.sql.functions import *

# Bronze tables (raw input)
@dlt.table
def patients_raw():
    return spark.read.table("healthcare_equity_bronze.patients_source")

@dlt.table
def decisions_raw():
    return spark.read.table("healthcare_equity_bronze.decisions_source")

# Silver tables (cleaned)
@dlt.table
def patients_processed():
    return (dlt.read("patients_raw")
        .filter(col("patient_id").isNotNull())
        .dropDuplicates(["patient_id"]))

@dlt.table
def decisions_processed():
    return (dlt.read("decisions_raw")
        .filter(col("patient_id").isNotNull())
        .dropDuplicates(["patient_id", "scenario_type"]))

# Gold table (aggregated metrics)
@dlt.table
def disparate_impact():
    patients = dlt.read("patients_processed")
    decisions = dlt.read("decisions_processed")

    combined = (decisions
        .join(patients, "patient_id")
        .groupBy("scenario_type", "race")
        .agg(
            (sum(col("decision_flag")) / count("*")).alias("approval_rate"),
            count("*").alias("count")))

    stats = combined.groupBy("scenario_type").agg(
        min(col("approval_rate")).alias("min_rate"),
        max(col("approval_rate")).alias("max_rate"))

    return (combined
        .join(stats, "scenario_type")
        .select(
            col("scenario_type"),
            col("race"),
            col("approval_rate"),
            round(when(col("max_rate") > 0, col("min_rate") / col("max_rate")).otherwise(0), 4).alias("disparate_impact_ratio"),
            when(col("min_rate") / col("max_rate") < 0.80, lit("VIOLATION")).otherwise(lit("OK")).alias("eighty_percent_rule_status"),
            current_timestamp().alias("updated_timestamp")))
'''

print("[STEP 1] Uploading corrected DLT notebook...\n")

notebook_path = "/Repos/dlt_pipeline/main"
notebook_hex = dlt_code.encode('utf-8').hex()

try:
    response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/workspace/import",
        headers=headers,
        json={
            "path": notebook_path,
            "format": "SOURCE",
            "language": "PYTHON",
            "content": notebook_hex,
            "overwrite": True
        },
        timeout=30
    )

    if response.status_code in [200, 201]:
        print(f"  [SUCCESS] Notebook updated at {notebook_path}\n")
    else:
        print(f"  [ERROR] {response.text[:200]}\n")
        exit(1)

except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}\n")
    exit(1)

# ============================================================================
# Run the job again
# ============================================================================

print("[STEP 2] Re-running DLT job...\n")

try:
    # Find the job
    jobs_response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/jobs/list",
        headers=headers,
        timeout=30
    )

    if jobs_response.status_code in [200, 201]:
        jobs = jobs_response.json().get('jobs', [])
        job_id = None

        for job in jobs:
            if 'Healthcare Equity DLT' in job.get('settings', {}).get('name', ''):
                job_id = job.get('job_id')
                break

        if job_id:
            print(f"  Found job: {job_id}")

            # Run the job
            run_response = requests.post(
                f"{WORKSPACE_URL}/api/2.0/jobs/run-now",
                headers=headers,
                json={"job_id": job_id},
                timeout=30
            )

            if run_response.status_code in [200, 201]:
                run_result = run_response.json()
                run_id = run_result.get('run_id')
                print(f"  Job started!")
                print(f"  Run ID: {run_id}\n")

                # Monitor briefly
                print("[STEP 3] Waiting for job to complete...\n")

                import time
                for i in range(60):  # Poll for up to 10 minutes
                    time.sleep(10)

                    status_response = requests.get(
                        f"{WORKSPACE_URL}/api/2.0/jobs/runs/get",
                        headers=headers,
                        params={"run_id": run_id},
                        timeout=30
                    )

                    if status_response.status_code in [200, 201]:
                        status = status_response.json()
                        state = status.get('state', {})
                        life_cycle = state.get('life_cycle_state')
                        result = state.get('result_state')

                        elapsed = (i + 1) * 10

                        if life_cycle == 'RUNNING':
                            print(f"  [{elapsed}s] Status: RUNNING")
                        elif life_cycle == 'PENDING':
                            print(f"  [{elapsed}s] Status: PENDING")
                        elif life_cycle == 'TERMINATED':
                            if result == 'SUCCESS':
                                print(f"  [{elapsed}s] Status: SUCCESS!")
                                break
                            else:
                                print(f"  [{elapsed}s] Status: {result}")
                                break

            else:
                print(f"  [ERROR] Could not start job")

        else:
            print("  [ERROR] Job not found")

except Exception as e:
    print(f"  [ERROR] {str(e)[:100]}")

print("\n" + "=" * 80)
print("DONE - Check dashboard now:")
print("  http://localhost:8501")
print("  Click 'Refresh Now' button")
print("=" * 80)
