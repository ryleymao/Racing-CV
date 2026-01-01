#!/bin/bash

# Quick script to run CV input with proper setup

cd "$(dirname "$0")"

echo "🚀 Starting Face Tracking CV Input..."
echo ""

# Check if venv exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv and run
cd backend
source venv/bin/activate

# Check if server is running (optional)
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Server doesn't seem to be running on port 8000"
    echo "   Start it with: uvicorn backend.main:app --host 0.0.0.0 --port 8000"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run CV input
cd ..
python3 -m backend.services.cv_input

