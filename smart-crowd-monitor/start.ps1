# Smart Crowd Detection and Monitoring System PowerShell Launcher
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "       Smart Crowd Detection and Monitoring System (AI Ops)" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$pythonPath = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (-Not (Test-Path $pythonPath)) {
    Write-Host "Virtual environment not detected at $pythonPath" -ForegroundColor Red
    exit 1
}

Write-Host "Starting server on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process "http://127.0.0.1:8000"

& $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
