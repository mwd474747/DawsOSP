#!/bin/bash
#
# DawsOS UI Launcher
#
# Purpose: Start Streamlit UI for Portfolio Overview
# Updated: 2025-10-22 (Phase 4 Task 3)
#
# Usage:
#   ./run_ui.sh                    # Run with mock data
#   ./run_ui.sh --api              # Run with real API
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
USE_MOCK="true"
if [[ "$1" == "--api" ]]; then
    USE_MOCK="false"
    echo "📡 Using real API at http://localhost:8000"
else
    echo "🎭 Using mock data (no API connection)"
    echo "   Use './run_ui.sh --api' to connect to real API"
fi

# Set environment variables
export USE_MOCK_CLIENT="$USE_MOCK"
export EXECUTOR_API_URL="${EXECUTOR_API_URL:-http://localhost:8000}"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not installed"
    echo "   Install with: pip install streamlit"
    exit 1
fi

# Launch Streamlit
echo "🚀 Starting DawsOS Portfolio Overview UI..."
echo "   URL: http://localhost:8501"
echo ""

cd "$PROJECT_ROOT"

streamlit run frontend/ui/screens/portfolio_overview.py \
    --server.port 8501 \
    --server.address localhost \
    --browser.gatherUsageStats false \
    --theme.base dark \
    --theme.primaryColor "#00d9ff" \
    --theme.backgroundColor "#1e2329" \
    --theme.secondaryBackgroundColor "#252c33"
