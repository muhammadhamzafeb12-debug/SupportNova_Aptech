#!/bin/bash

echo "================================================="
echo " Starting SupportNova Backend & Frontend Services"
echo "================================================="

PROJECT_DIR="/home/hamza/SupportNova_Aptech"
cd "$PROJECT_DIR" || exit 1

# Kill any existing processes using ports 8000 and 3000
echo "1. Cleaning up existing server instances..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 1

# 2. Start Backend FastAPI Server
echo "2. Launching FastAPI Backend on http://0.0.0.0:8000..."
nohup "$PROJECT_DIR/.venv/bin/python" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# 3. Start Frontend Next.js Dev Server
echo "3. Launching Next.js Frontend on http://localhost:3000..."
cd "$PROJECT_DIR/frontend" || exit 1
chmod +x node_modules/.bin/* 2>/dev/null || true
nohup npm run dev -- -p 3000 > "$PROJECT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# 4. Wait for both servers to be ready
cd "$PROJECT_DIR" || exit 1
echo "4. Verifying server readiness..."
for i in {1..15}; do
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    
    if [ "$BACKEND_STATUS" -eq 200 ] && [ "$FRONTEND_STATUS" -eq 200 ]; then
        echo "================================================="
        echo " ✅ SupportNova Services ARE LIVE AND ACTIVE!"
        echo " - Frontend Dashboard: http://localhost:3000"
        echo " - Backend API Docs:   http://localhost:8000/docs"
        echo "================================================="
        exit 0
    fi
    echo "   Waiting for servers... (Backend: $BACKEND_STATUS, Frontend: $FRONTEND_STATUS)"
    sleep 2
done

echo "⚠️ Warning: One or both servers took longer than expected. Logs:"
tail -n 10 "$PROJECT_DIR/backend.log"
tail -n 10 "$PROJECT_DIR/frontend.log"
