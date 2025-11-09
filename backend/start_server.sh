#!/bin/bash

echo "Starting TripMind Backend Server..."
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

python main.py

