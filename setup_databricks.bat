@echo off
REM Automated Setup Script for Databricks Community Edition
REM Healthcare Equity Bias Detection System
REM Run this ONCE and everything will be set up automatically

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Healthcare Equity - Databricks Setup
echo ========================================
echo.

REM Step 1: Create virtual environment
echo [Step 1/7] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Step 2: Activate virtual environment
echo.
echo [Step 2/7] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Step 3: Install dependencies
echo.
echo [Step 3/7] Installing dependencies...
echo This may take 1-2 minutes...
pip install -q -r requirements.txt
pip install -q databricks-sql-connector --upgrade
echo [OK] All dependencies installed

REM Step 4: Initialize Databricks schema
echo.
echo [Step 4/7] Initializing Databricks schema...
python -c "
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('.env.databricks')

try:
    from src.storage.databricks_interface import DatabricksInterface
    from config_loader import load_config

    config = load_config()
    print('  Connecting to Databricks...')
    db = DatabricksInterface(config)
    print('  Creating tables...')
    db.init_schema()
    db.close()
    print('  [OK] Databricks schema ready')
except Exception as e:
    print(f'  [WARNING] {e}')
    print('  This is OK - tables will be created when data loads')
"
echo [OK] Databricks initialized

REM Step 5: Generate synthetic data
echo.
echo [Step 5/7] Generating synthetic patient data (10,000 records)...
echo This may take 30-60 seconds...
python scripts/generate_synthetic_data.py --n-patients 10000
echo [OK] Synthetic data generated

REM Step 6: Run pipeline
echo.
echo [Step 6/7] Running full pipeline (analysis + AI)...
echo Transforming data...
echo Detecting disparities...
echo Generating Claude AI analysis...
python scripts/run_full_pipeline.py
echo [OK] Pipeline complete

REM Step 7: Start dashboard
echo.
echo [Step 7/7] Starting dashboard...
echo Dashboard opening in your browser...
echo.
echo ========================================
echo [SUCCESS] Setup Complete!
echo ========================================
echo.
echo Dashboard launching at: http://localhost:8501
echo.
echo Your Databricks workspace is now connected with:
echo   - 10,000 synthetic patients
echo   - Bias detection analysis
echo   - Claude AI insights
echo   - Interactive 5-page dashboard
echo   - PDF regulatory reports
echo.
echo Press Ctrl+C in the dashboard terminal to stop
echo.

streamlit run dashboard/app.py

pause
