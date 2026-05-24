@echo off
REM Clean Dashboard Startup - Windows Batch

echo ========================================
echo HEALTHCARE EQUITY DASHBOARD STARTUP
echo ========================================

cd /d "C:\Users\lokes\Downloads\Equity_Bias_Detection"

REM Kill any existing Python processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM python3.exe >nul 2>&1
timeout /t 2 /nobreak

echo.
echo Starting dashboard...
echo.
echo IMPORTANT:
echo   - Open ONLY: http://localhost:8501
echo   - DO NOT open: localhost:8020
echo   - If port 8501 is in use, close other instances
echo.
echo Dashboard URL: http://localhost:8501
echo ========================================
echo.

python -m streamlit run dashboard/app.py --server.port=8501 --server.headless=true --logger.level=info

pause
