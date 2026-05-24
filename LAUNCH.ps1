# PRODUCTION LAUNCH - Databricks Only
Write-Host "Healthcare Equity - Databricks Enterprise Deployment" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Kill hanging processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Remove old venv
if (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
}

Write-Host "Creating venv..." -ForegroundColor Green
python -m venv venv

$pythonPath = Join-Path $scriptDir "venv\Scripts\python.exe"
$pipPath = Join-Path $scriptDir "venv\Scripts\pip.exe"

Write-Host "Installing packages..." -ForegroundColor Green
& $pipPath install --upgrade pip setuptools wheel -q 2>&1 | Out-Null
& $pipPath install databricks-sql-connector anthropic python-dotenv pydantic pandas numpy scipy matplotlib plotly streamlit pyyaml -q 2>&1 | Out-Null

Write-Host "Connecting to Databricks..." -ForegroundColor Green
& $pythonPath -c "
import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env.databricks')
from databricks.sql import connect
host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')
conn = connect(server_hostname=host, http_path=http_path, personal_access_token=token)
cursor = conn.cursor()
cursor.execute('SELECT 1')
cursor.execute('CREATE DATABASE IF NOT EXISTS main.healthcare_equity_bronze')
cursor.execute('CREATE DATABASE IF NOT EXISTS main.healthcare_equity_silver')
cursor.execute('CREATE DATABASE IF NOT EXISTS main.healthcare_equity_gold')
print('OK: Databricks connected and schemas created')
conn.close()
"

Write-Host "Generating 1M synthetic patients..." -ForegroundColor Green
& $pythonPath -c "
import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env.databricks')
from databricks.sql import connect
host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')
conn = connect(server_hostname=host, http_path=http_path, personal_access_token=token)
cursor = conn.cursor()
cursor.execute('''
CREATE OR REPLACE TABLE main.healthcare_equity_bronze.patients AS
SELECT ROW_NUMBER() OVER (ORDER BY (SELECT 1)) as patient_id,
  CASE WHEN RAND() < 0.5 THEN 'M' ELSE 'F' END as gender,
  CASE WHEN RAND() < 0.12 THEN 'Black' WHEN RAND() < 0.19 THEN 'Hispanic' WHEN RAND() < 0.05 THEN 'AIAN' WHEN RAND() < 0.03 THEN 'Asian' ELSE 'White' END as race,
  CASE WHEN RAND() < 0.05 THEN 'LGBTQ' ELSE 'Heterosexual' END as sexual_orientation,
  (18 + INT(RAND() * 75)) as age,
  CASE WHEN RAND() < 0.2 THEN 'Medicaid' WHEN RAND() < 0.3 THEN 'Medicare' WHEN RAND() < 0.4 THEN 'Commercial' ELSE 'Uninsured' END as insurance_type,
  INT(RAND() * 24) as sofa_score,
  INT(RAND() * 5) as cci_score,
  INT(RAND() * 5 + 1) as ses_quintile,
  CURRENT_TIMESTAMP() as created_at
FROM (SELECT EXPLODE(SEQUENCE(1, 1000000)) as num)
LIMIT 1000000
''')
print('OK: 1M patients generated in Databricks')
conn.close()
"

Write-Host "Launching Dashboard..." -ForegroundColor Green
& $pythonPath -m streamlit run dashboard/app.py
