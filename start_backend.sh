#!/bin/bash

# Start Backend Server
echo "Starting FNOL Backend Server..."
echo "Make sure GEMINI_API_KEY is set in your environment"
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Check for API key in .env file or environment
if [ ! -f ".env" ] && [ -z "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "WARNING: GEMINI_API_KEY not set!"
    echo "Please create a .env file with: GEMINI_API_KEY=your-key-here"
    echo "Or set it as environment variable: export GEMINI_API_KEY='your-key-here'"
    echo ""
fi

# Start server
echo "Starting server on http://localhost:8000"
uvicorn main:app --reload --port 8000

