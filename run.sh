#!/bin/bash

# Setup cleanup on script exit (terminates both backend and frontend processes)
cleanup() {
    echo ""
    echo "Stopping CRM Development Environment..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null
    fi
    exit 0
}

trap cleanup INT TERM EXIT

echo "Starting Telecom CRM Development Environment..."

# 1. Start Backend
echo "Starting Backend..."
cd backend || exit 1

# Detect virtual environment if present
if [ -d ".venv" ]; then
    PYTHON_BIN=".venv/bin/python3"
elif [ -d "venv" ]; then
    PYTHON_BIN="venv/bin/python3"
else
    PYTHON_BIN="python3"
fi

echo "Using python binary: $PYTHON_BIN"
$PYTHON_BIN -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# 2. Wait for backend to be healthy
echo "Waiting for backend API to be healthy..."
healthy=false
for i in {1..30}; do
    if curl -s http://localhost:8000/health | grep -q '"status":"ok"'; then
        healthy=true
        break
    fi
    sleep 2
done

if [ "$healthy" = false ]; then
    echo "Error: Backend did not become healthy in time."
    cleanup
fi

echo "Backend API is healthy!"

# 3. Start Frontend
echo "Starting Frontend..."
cd frontend || exit 1

# Add portable node if exists in current workspace
if [ -d "node" ]; then
    export PATH="$(pwd)/node:$PATH"
fi

npm run dev &
FRONTEND_PID=$!
cd ..

echo "Telecom CRM is running!"
echo " - Backend API: http://localhost:8000"
echo " - Frontend app: http://localhost:3000"
echo "Press Ctrl+C to stop both servers."

# Wait for background jobs to finish
wait
