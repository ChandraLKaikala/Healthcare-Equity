#!/usr/bin/env python3
"""
Create Databricks Jobs using Python SDK
"""
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import (
    Task, SqlTask, CronSchedule, PauseStatus, CreateJob
)

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')

print("="*70)
print("CREATING DATABRICKS JOBS USING PYTHON SDK")
print("="*70)

try:
    # Initialize client
    client = WorkspaceClient(host=host, token=token)
    print(f"\n[OK] Connected to {host}")

    warehouse_id = "3c7564c48c0bd682"

    jobs_config = [
        {
            "name": "Daily Healthcare Equity Bias Detection",
            "description": "Analyze healthcare disparities across all 4 scenarios daily",
            "query": "SELECT scenario_type, race, gender, approval_rate, total_decisions FROM healthcare_equity_gold.bias_metrics",
            "cron": "0 0 * * ?",
            "task_key": "bias_analysis"
        },
        {
            "name": "Weekly Healthcare Equity Reports",
            "description": "Generate weekly regulatory compliance reports",
            "query": "SELECT COUNT(*), AVG(approval_rate) FROM healthcare_equity_gold.bias_metrics",
            "cron": "0 0 ? * MON",
            "task_key": "weekly_reports"
        },
        {
            "name": "Data Quality Checks - Healthcare Equity",
            "description": "Validate data integrity every 6 hours",
            "query": "SELECT COUNT(*) FROM healthcare_equity_bronze.patients UNION ALL SELECT COUNT(*) FROM healthcare_equity_silver.patients_processed UNION ALL SELECT COUNT(*) FROM healthcare_equity_gold.bias_metrics",
            "cron": "0 */6 * * ?",
            "task_key": "quality_check"
        }
    ]

    created_jobs = []

    for job_config in jobs_config:
        try:
            print(f"\nCreating: {job_config['name']}...")

            # Create job definition
            job = CreateJob(
                name=job_config['name'],
                description=job_config['description'],
                tasks=[
                    Task(
                        task_key=job_config['task_key'],
                        description=job_config['description'],
                        sql_task=SqlTask(
                            query=job_config['query'],
                            warehouse_id=warehouse_id
                        )
                    )
                ],
                schedule=CronSchedule(
                    quartz_cron_expression=job_config['cron'],
                    timezone_id='UTC',
                    pause_status=PauseStatus.UNPAUSED
                )
            )

            # Create the job
            response = client.jobs.create(job)
            job_id = response.job_id
            created_jobs.append({'name': job_config['name'], 'id': job_id})
            print(f"  [OK] Job created (ID: {job_id})")

        except Exception as e:
            print(f"  [ERROR] {str(e)[:200]}")

    print("\n" + "="*70)
    if created_jobs:
        print("SUCCESS: JOBS CREATED!")
        print("="*70)
        for job_info in created_jobs:
            print(f"  - {job_info['name']} (ID: {job_info['id']})")
        print("\nSchedules Active:")
        print("  1. Daily Bias Detection: 00:00 UTC daily")
        print("  2. Weekly Reports: 00:00 UTC Mondays")
        print("  3. Data Quality: Every 6 hours")
    else:
        print("FAILED: NO JOBS CREATED")
        print("="*70)

except Exception as e:
    print(f"[ERROR] Failed to connect: {str(e)}")
    import traceback
    traceback.print_exc()
