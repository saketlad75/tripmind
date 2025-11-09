#!/bin/bash
# Start backend server with verbose logging

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server with detailed logging
echo "🚀 Starting TripMind Backend Server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📝 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    --access-log

