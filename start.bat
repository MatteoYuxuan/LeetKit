@echo off
cd /d "%~dp0"
set PYTHON=.venv\Scripts\python.exe
start http://localhost:8001
%PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
