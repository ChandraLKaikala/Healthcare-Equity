#!/usr/bin/env python3
"""Debug job format"""
import json

warehouse_id = "3c7564c48c0bd682"

job = {
    "name": "Daily Healthcare Equity Bias Detection",
    "description": "Analyze healthcare disparities across all 4 scenarios daily",
    "schedule": {
        "quartz_cron_expression": "0 0 * * ?",
        "timezone_id": "UTC",
        "pause_status": "UNPAUSED"
    },
    "tasks": [
        {
            "task_key": "bias_analysis",
            "description": "Run bias detection analysis",
            "sql_task": {
                "query": "SELECT scenario_type FROM healthcare_equity_gold.bias_metrics",
                "warehouse_id": warehouse_id
            }
        }
    ]
}

print("Job JSON:")
print(json.dumps(job, indent=2))

# Check specific field
print(f"\nschedule type: {type(job['schedule'])}")
print(f"schedule value: {job['schedule']}")
print(f"tasks type: {type(job['tasks'])}")
print(f"sql_task type: {type(job['tasks'][0]['sql_task'])}")
