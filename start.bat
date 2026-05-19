@echo off
title LeetKit
cd /d "%~dp0"

echo Starting LeetKit...
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 goto :error
)

echo.
echo Installing dependencies...
echo.
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 goto :error
echo.

echo Opening browser...
start http://localhost:8001

echo Starting server on port 8001...
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

pause
exit

:error
echo.
echo Failed! Please check Python is installed.
pause
