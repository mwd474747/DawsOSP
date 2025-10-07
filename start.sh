#!/bin/bash
# DawsOS Streamlit App Launcher
# Handles setup and launch of the Trinity financial intelligence system

set -e  # Exit on error

echo "🚀 DawsOS Launcher - Trinity Architecture v2.0"
echo "=============================================="
echo

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "✓ Python version: $PYTHON_VERSION (3.10+ required, 3.13+ recommended)"

# Check if virtual environment exists
if [ ! -d "dawsos/venv" ]; then
    echo "📦 Virtual environment not found. Creating..."
    python3 -m venv dawsos/venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo "📦 Checking dependencies..."
if ! dawsos/venv/bin/pip list | grep -q streamlit; then
    echo "Installing dependencies (this may take a minute)..."
    dawsos/venv/bin/pip install -r requirements.txt -q
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed"
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    echo "✓ .env created (edit to add API keys for live data)"
else
    echo "✓ .env file exists"
fi

# Check for existing Streamlit processes
if lsof -ti:8501 > /dev/null 2>&1; then
    echo "⚠️  Port 8501 is already in use"
    read -p "Kill existing process and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:8501 | xargs kill -9 2>/dev/null || true
        echo "✓ Killed existing process"
        sleep 2
    else
        echo "❌ Exiting. Stop the existing process manually."
        exit 1
    fi
fi

echo
echo "🌐 Starting DawsOS Streamlit App..."
echo "   Local:    http://localhost:8501"
echo "   Network:  http://$(hostname -I | awk '{print $1}'):8501"
echo
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo

# Launch Streamlit
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501 --server.headless=false
