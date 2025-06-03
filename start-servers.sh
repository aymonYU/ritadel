#!/bin/bash

echo "Starting Ritadel servers..."

# Function to kill background processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $API_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start API server in background
echo "Starting backend API server..."
cd backend
poetry run python src/webui.py --api &
API_PID=$!
cd ..

# Wait a moment for API to start
sleep 3

# Start frontend in background
echo "Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Servers started successfully!"
echo "- Backend API: http://localhost:5000"
echo "- Frontend UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait 