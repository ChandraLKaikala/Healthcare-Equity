#!/usr/bin/env python3
"""
Continuous Data Pipeline Orchestrator
Runs Bronze mutations every minute with Silver/Gold transformation
"""
import os
import sys
import subprocess
import time
from datetime import datetime

print("="*80)
print("HEALTHCARE EQUITY BIAS DETECTION - CONTINUOUS PIPELINE")
print("="*80)
print("\nThis system will continuously:")
print("  1. Generate realistic patient data mutations (INSERT/UPSERT/DELETE)")
print("  2. Transform Bronze > Silver > Gold layers")
print("  3. Update bias metrics and analytics every minute")
print("  4. Keep dashboard data fresh")
print("\nPress Ctrl+C to stop\n")

cycle_count = 0

try:
    while True:
        cycle_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"\n[RUN #{cycle_count}] {timestamp}")
        print("-" * 80)

        # Run the complete continuous pipeline (Bronze mutations + transformation)
        result = subprocess.run(
            [sys.executable, 'continuous_data_pipeline.py'],
            cwd=os.getcwd(),
            capture_output=False
        )

        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline cycle completed")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline had issues (continuing...)")

        # Wait 60 seconds before next run
        print(f"\nWaiting 60 seconds until next run...", end="", flush=True)
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                print(f" {60-i}s", end="", flush=True)

        print(" RUNNING NEXT ITERATION\n")

except KeyboardInterrupt:
    print(f"\n\n[STOPPED] Pipeline halted after {cycle_count} cycles")
    print("="*80)
