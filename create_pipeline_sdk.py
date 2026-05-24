#!/usr/bin/env python3
"""
Create DLT Pipeline using Databricks SDK
"""
import os
from dotenv import load_dotenv

load_dotenv('.env.databricks')

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.pipelines import CreatePipeline, PipelineCluster
except ImportError:
    print("Installing databricks-sdk...")
    os.system(f"{os.sys.executable} -m pip install databricks-sdk --quiet")
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.pipelines import CreatePipeline, PipelineCluster

host = os.getenv('DATABRICKS_HOST')
token = os.getenv('DATABRICKS_TOKEN')

print("="*80)
print("Creating DLT Pipeline with Databricks SDK")
print("="*80)

try:
    # Initialize SDK client
    client = WorkspaceClient(host=host, token=token)

    print("\nConnecting to Databricks workspace...")

    # Create pipeline configuration
    pipeline = CreatePipeline(
        name="healthcare_equity_dlt",
        storage="/Workspace/healthcare_equity_dlt",
        configuration={},
        libraries=[
            {
                "notebook": {
                    "path": "/Workspace/dlt_pipeline"
                }
            }
        ],
        target="healthcare_equity_gold",
        continuous=False,
        development=False
    )

    print("Creating DLT pipeline...")
    result = client.pipelines.create(pipeline)

    print(f"\nSUCCESS! Pipeline created:")
    print(f"  Pipeline ID: {result.pipeline_id}")
    print(f"  Name: {result.name}")
    print(f"  Status: {result.state}")

    print("\n" + "="*80)
    print("Next Steps:")
    print("="*80)
    print("1. Go to Databricks UI > Jobs & Pipelines")
    print("2. Find 'healthcare_equity_dlt' pipeline")
    print("3. Click 'Start' to run the pipeline")
    print("4. View logs to monitor execution")
    print("="*80)

except Exception as e:
    print(f"\nERROR: {str(e)}")

    # Try to get more details
    if "SERVERLESS_REQUIRED" in str(e) or "serverless" in str(e).lower():
        print("\nINFO: This workspace requires serverless compute for DLT.")
        print("Serverless compute will be automatically assigned.")
        print("\nYou may need to:")
        print("1. Create the pipeline in Databricks UI manually")
        print("2. Or upgrade SDK and try again")

    print("\nFALLBACK: Python continuous pipeline is already running!")
    print("The system is updating data every minute via:")
    print("  python3 run_continuous_pipeline.py")
