#!/bin/bash
#
# DawsOS UI Launcher
#
# Purpose: Start Streamlit UI with full navigation (main.py)
# Updated: 2025-10-23 (Deduplication improvements)
#
# Usage:
#   ./run_ui.sh                    # Run with real API (default)
#   ./run_ui.sh --mock             # Run with mock data (testing only)
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments - Default to real API (aligned with frontend/main.py)
USE_MOCK="false"
if [[ "$1" == "--mock" ]]; then
    USE_MOCK="true"
    echo "🎭 Using mock data (testing mode)"
else
    echo "📡 Using real API at http://localhost:8000"
fi

# Set environment variables
export USE_MOCK_CLIENT="$USE_MOCK"
export EXECUTOR_API_URL="${EXECUTOR_API_URL:-http://localhost:8000}"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Check if streamlit is installed in venv
STREAMLIT_BIN="${PROJECT_ROOT}/venv/bin/streamlit"
if [ ! -f "$STREAMLIT_BIN" ]; then
    echo "❌ Streamlit not installed in venv"
    echo "   Install with: source venv/bin/activate && pip install streamlit"
    exit 1
fi

# Launch Streamlit
echo "🚀 Starting DawsOS Portfolio Overview UI..."
echo "   URL: http://localhost:8501"
echo ""

cd "$PROJECT_ROOT"

"$STREAMLIT_BIN" run frontend/main.py \
    --server.port 8501 \
    --server.address localhost \
    --browser.gatherUsageStats false \
    --theme.base dark \
    --theme.primaryColor "#00d9ff" \
    --theme.backgroundColor "#1e2329" \
    --theme.secondaryBackgroundColor "#252c33"
