#!/usr/bin/env python3
"""
Start Continuous Data Pipeline
Runs every minute forever, generating INSERT/UPSERT/DELETE mutations
"""
import time
import subprocess
import sys
from datetime import datetime

print("=" * 80)
print("CONTINUOUS DATA PIPELINE - STARTING")
print("=" * 80)
print("\nThis will run every minute forever:")
print("  - Generate new patients (INSERT)")
print("  - Update existing patients (UPSERT)")
print("  - Update decisions (UPSERT)")
print("  - Insert new decisions (INSERT)")
print("  - Delete old records (DELETE)")
print("  - Refresh Silver and Gold layers")
print("  - Dashboard updates automatically!")
print("\nPress Ctrl+C to stop\n")

run_count = 0

try:
    while True:
        run_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n[RUN #{run_count}] {timestamp}")
        print("-" * 80)

        # Run the pipeline
        result = subprocess.run(
            [sys.executable, 'continuous_data_pipeline.py'],
            cwd='.',
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline completed successfully")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline had issues")

        # Wait 60 seconds before next run
        print(f"\nWaiting 60 seconds until next run...", end="", flush=True)
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                print(f" {60-i}s", end="", flush=True)

        print(" RUNNING NEXT ITERATION\n")

except KeyboardInterrupt:
    print(f"\n\n[STOPPED] Pipeline halted after {run_count} runs")
    print("=" * 80)
