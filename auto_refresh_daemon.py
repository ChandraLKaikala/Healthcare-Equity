
#!/usr/bin/env python3
import os
import time
import sys
from dotenv import load_dotenv
load_dotenv('.env.databricks')
from databricks.sql import connect

host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

def refresh_data():
    try:
        conn = connect(server_hostname=host, http_path=http_path, personal_access_token=token)
        cursor = conn.cursor()
        cursor.execute('CREATE OR REPLACE TABLE healthcare_equity_gold.bias_metrics AS SELECT d.scenario_type, p.race, p.gender, COUNT(DISTINCT d.decision_id) as total_decisions, SUM(d.decision_flag) as approved_count, ROUND(SUM(d.decision_flag) / COUNT(*) * 100, 2) as approval_rate, COUNT(DISTINCT p.patient_id) as unique_patients, ROUND(AVG(p.sofa_score), 2) as avg_severity, MIN(d.decision_date) as first_decision_date, MAX(d.decision_date) as last_decision_date, CURRENT_TIMESTAMP() as calculated_at FROM healthcare_equity_silver.decisions_processed d JOIN healthcare_equity_silver.patients_processed p ON d.patient_id = p.patient_id GROUP BY d.scenario_type, p.race, p.gender')
        conn.close()
        print(f'[{time.strftime("%H:%M:%S")}] Data refreshed successfully')
    except Exception as e:
        print(f'[{time.strftime("%H:%M:%S")}] Error: {str(e)[:100]}')

if __name__ == '__main__':
    while True:
        refresh_data()
        time.sleep(300)
