# CLEAN DASHBOARD STARTUP
# This kills all Python, clears caches, and starts fresh

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CLEAN DASHBOARD STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Kill ALL Python processes
Write-Host "`n[1/5] Killing all Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process python3 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process python3.12 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "[DONE] All Python processes terminated" -ForegroundColor Green

# Step 2: Clear Streamlit caches
Write-Host "`n[2/5] Clearing Streamlit caches..." -ForegroundColor Yellow
Remove-Item "$env:USERPROFILE\.streamlit" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\streamlit" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\streamlit*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[DONE] Streamlit caches cleared" -ForegroundColor Green

# Step 3: Clear browser cache locations
Write-Host "`n[3/5] Clearing browser caches..." -ForegroundColor Yellow
Remove-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\Microsoft\Internet Explorer\Cache" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[DONE] Browser caches cleared" -ForegroundColor Green

# Step 4: Close all browsers
Write-Host "`n[4/5] Closing all browsers..." -ForegroundColor Yellow
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process msedge -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "[DONE] All browsers closed" -ForegroundColor Green

# Step 5: Start dashboard
Write-Host "`n[5/5] Starting dashboard..." -ForegroundColor Yellow
Write-Host "`nDASHBOARD STARTING IN 3 SECONDS..." -ForegroundColor Cyan
Write-Host "DO NOT navigate to localhost:8020" -ForegroundColor Red
Write-Host "ONLY open: http://localhost:8501" -ForegroundColor Green
Start-Sleep -Seconds 3

cd "C:\Users\lokes\Downloads\Equity_Bias_Detection"
python -m streamlit run dashboard/app.py --server.headless=true --logger.level=debug
