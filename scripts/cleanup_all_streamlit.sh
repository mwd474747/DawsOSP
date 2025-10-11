#!/bin/bash
# Comprehensive Streamlit cleanup script

echo "🧹 Cleaning up all Streamlit processes..."

# Method 1: Kill by process name
echo "Method 1: Killing by process name..."
killall -9 streamlit 2>/dev/null && echo "  ✓ Killed streamlit processes" || echo "  ⚠ No streamlit processes found"

# Method 2: Kill by pattern
echo "Method 2: Killing by pattern match..."
pkill -9 -f "streamlit run" 2>/dev/null && echo "  ✓ Killed streamlit run processes" || echo "  ⚠ No streamlit run processes found"

# Method 3: Kill by port
echo "Method 3: Killing processes on port 8501..."
lsof -ti:8501 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Killed processes on port 8501" || echo "  ⚠ No processes on port 8501"

# Method 4: Kill Python processes running Streamlit
echo "Method 4: Killing Python processes with streamlit..."
ps aux | grep "[s]treamlit run" | awk '{print $2}' | xargs kill -9 2>/dev/null && echo "  ✓ Killed Python streamlit processes" || echo "  ⚠ No Python streamlit processes found"

# Method 5: Kill all python processes on port 8501
echo "Method 5: Killing all python on port 8501..."
lsof -i:8501 -t 2>/dev/null | xargs kill -9 2>/dev/null && echo "  ✓ Killed port 8501 processes" || echo "  ⚠ No port 8501 processes"

# Check remaining processes
echo ""
echo "📊 Checking for remaining Streamlit processes..."
REMAINING=$(ps aux | grep "[s]treamlit" | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ All Streamlit processes cleaned up successfully!"
else
    echo "⚠️  Warning: $REMAINING Streamlit process(es) still running"
    echo "Listing remaining processes:"
    ps aux | grep "[s]treamlit"
fi

echo ""
echo "✓ Cleanup script complete"
