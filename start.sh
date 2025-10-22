#!/bin/bash
# Trinity 3.0 Launcher
# Advanced Financial Intelligence System

set -e  # Exit on error

echo "🚀 Trinity 3.0 - Advanced Financial Intelligence System"
echo "======================================================="
echo

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "✓ Python version: $PYTHON_VERSION (3.10+ required, 3.13+ recommended)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo "📦 Checking dependencies..."
if ! venv/bin/pip list | grep -q streamlit; then
    echo "Installing dependencies (this may take a minute)..."
    venv/bin/pip install -r requirements.txt -q
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed"
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ .env created (edit to add API keys for live data)"
    else
        echo "⚠️  .env.example not found, creating minimal .env"
        touch .env
    fi
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
echo "🌐 Starting Trinity 3.0..."
echo "   Local:    http://localhost:8501"
echo "   Network:  http://$(hostname -I | awk '{print $1}'):8501"
echo
echo "✨ Features:"
echo "   ✓ 5-tab professional UI (Market, Economic, Stock Analysis, Prediction Lab, Settings)"
echo "   ✓ Enhanced quick actions (categorical tabs)"
echo "   ✓ Sector rotation heatmap with momentum signals"
echo "   ✓ Market sentiment dashboard (VIX, Put/Call, A/D ratio)"
echo "   ✓ Dalio economic cycle gauges (short-term + long-term)"
echo "   ✓ Intelligence layer (instructor + Anthropic Claude)"
echo "   ✓ Real-time data integration (OpenBB + mock services)"
echo "   ✓ Professional Bloomberg Terminal theme"
echo
echo "Press Ctrl+C to stop the server"
echo "======================================================="
echo

# Launch Streamlit
venv/bin/streamlit run main.py --server.port=8501 --server.headless=false
