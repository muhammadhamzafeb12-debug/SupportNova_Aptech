#!/usr/bin/env bash

# Go to project directory
cd "$(dirname "$0")"

echo "========================================================"
echo "🚀 Starting SupportNova Backend & Frontend..."
echo "========================================================"

# Find Python executable
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
else
    PYTHON_BIN="python"
fi

# Clean up any leftover processes on port 8000 and 3000
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true

# Start Backend API Server in background
echo "1. Starting Backend API on http://localhost:8000 ..."
PYTHONPATH=. $PYTHON_BIN -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Trap Ctrl+C (INT) and termination (TERM) to stop backend on exit
trap "echo 'Stopping Backend...'; kill -9 $BACKEND_PID 2>/dev/null; fuser -k 8000/tcp 2>/dev/null; exit 0" INT TERM

# Wait 2 seconds for backend initialization
sleep 2

# Start Frontend Dev Server
echo "2. Starting Frontend Dashboard on http://localhost:3000 ..."
echo "--------------------------------------------------------"
echo "👉 Open your browser at: http://localhost:3000"
echo "👉 API Documentation:   http://localhost:8000/docs"
echo "--------------------------------------------------------"

cd frontend && npm run dev
