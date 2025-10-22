#!/bin/bash
# Trinity 3.0 Streamlit Deployment Script

echo "🚀 Trinity 3.0 - Streamlit Deployment"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from trinity3/ directory."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "📦 Installing Trinity 3.0 dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Some dependencies failed to install (this is OK for optional packages)"
    echo "   Installing core dependencies only..."
    pip install streamlit pandas numpy plotly networkx python-dotenv --quiet
    pip install instructor pydantic anthropic --quiet 2>/dev/null || echo "   (Intelligence layer dependencies optional)"
fi

echo "✅ Dependencies installed"

# Check for API keys
echo ""
echo "🔑 Checking API keys..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set (intelligence layer will be limited)"
    echo "   Set it with: export ANTHROPIC_API_KEY='your_key_here'"
else
    echo "✅ ANTHROPIC_API_KEY configured"
fi

if [ -z "$OPENBB_API_KEY" ]; then
    echo "⚠️  OPENBB_API_KEY not set (using free data sources)"
else
    echo "✅ OPENBB_API_KEY configured"
fi

# Launch Streamlit
echo ""
echo "🚀 Launching Trinity 3.0 UI..."
echo "======================================"
echo ""
echo "📊 Dashboard will open at: http://localhost:8501"
echo ""
echo "To stop the server, press Ctrl+C"
echo ""
echo "======================================"
echo ""

# Run Streamlit
streamlit run main.py \
    --server.port=8501 \
    --server.address=localhost \
    --browser.gatherUsageStats=false \
    --server.enableXsrfProtection=true

# Deactivate on exit
deactivate
