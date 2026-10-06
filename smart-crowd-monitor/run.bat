@echo off
title Smart Crowd Detection and Monitoring System
echo =====================================================================
echo       Smart Crowd Detection and Monitoring System (AI Ops)
echo =====================================================================
echo.
echo [1/2] Activating Python environment...
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    echo Python runtime found.
) else (
    echo Virtual environment not found. Please install dependencies first.
    pause
    exit /b 1
)

echo.
echo [2/2] Starting FastAPI Server on http://127.0.0.1:8000 ...
echo Opening web browser...
start http://127.0.0.1:8000
echo.
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
