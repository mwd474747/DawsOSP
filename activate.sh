#!/bin/bash
# DawsOS Virtual Environment Activation Script
# Usage: source activate.sh

# Activate virtual environment
source venv/bin/activate

# Load .env file
if [ -f ".env" ]; then
    set -a
    source .env
    set +a

    echo "✅ Virtual environment activated with API keys"
    echo ""
    echo "📡 API Provider Status:"
    [ -n "$FMP_API_KEY" ] && echo "  ✅ FMP (Fundamentals) - ${FMP_API_KEY:0:10}***"
    [ -n "$POLYGON_API_KEY" ] && echo "  ✅ Polygon (Prices) - ${POLYGON_API_KEY:0:10}***"
    [ -n "$FRED_API_KEY" ] && echo "  ✅ FRED (Macro) - ${FRED_API_KEY:0:10}***"
    [ -n "$NEWSAPI_KEY" ] && echo "  ✅ NewsAPI - ${NEWSAPI_KEY:0:10}***"
    [ -n "$ANTHROPIC_API_KEY" ] && echo "  ✅ Anthropic Claude - ${ANTHROPIC_API_KEY:0:15}***"
    echo ""
    echo "💾 Database:"
    echo "  ✅ PostgreSQL: localhost:5432/dawsos"
    echo "  ✅ Redis: localhost:6379/0"
    echo ""
    echo "🚀 Ready to launch!"
    echo "   Backend: ./backend/run_api.sh"
    echo "   Frontend: ./frontend/run_ui.sh"
    echo ""
else
    echo "⚠️  .env file not found"
    echo "   Run: cp .env.example .env"
fi
