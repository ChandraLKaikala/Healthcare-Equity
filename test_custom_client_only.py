#!/usr/bin/env python3
"""
Minimal test - verify custom client works WITHOUT any OAuth triggers
"""
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Load credentials
from dotenv import load_dotenv
load_dotenv('.env.databricks')

print("=" * 60)
print("TEST: Custom Databricks Client (NO SDK)")
print("=" * 60)

# Test the custom client
try:
    from databricks_client import get_databricks_connection
    print("[OK] Successfully imported custom client (NO SDK)")

    # Try to get a connection
    conn = get_databricks_connection()
    print("[OK] Connection object created")

    # Get a cursor
    cursor = conn.cursor()
    print("[OK] Cursor created")

    # Execute a simple test query
    print("\nExecuting test query: SELECT 1 as test_result")
    cursor.execute("SELECT 1 as test_result")
    print("[OK] Query executed")

    # Fetch result
    result = cursor.fetchone()
    print(f"[OK] Result: {result}")

    if result == (1,):
        print("\n" + "="*60)
        print("SUCCESS: Custom client works perfectly!")
        print("="*60)
    else:
        print(f"\nWarning: Unexpected result: {result}")

    conn.close()

except Exception as e:
    print(f"\n[FAIL] ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
