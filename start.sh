#!/bin/bash
cd "$(dirname "$0")"

echo "Starting LeetKit..."
echo

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.10+"
    exit 1
fi

if [ ! -f ".venv/bin/python" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
fi

echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo
echo "Opening http://localhost:8001 ..."
echo "Press Ctrl+C to stop"
echo

sleep 2
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
