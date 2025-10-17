#!/bin/bash
# Full clean restart script - clears all caches and restarts fresh

echo "🧹 Full Clean Restart"
echo "===================="

# 1. Kill all processes
echo "1. Killing all Streamlit/Python processes..."
killall -9 streamlit 2>/dev/null
killall -9 python 2>/dev/null
killall -9 python3 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null
sleep 2

# 2. Clear Python cache
echo "2. Clearing Python cache..."
find dawsos -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find dawsos -name "*.pyc" -delete 2>/dev/null
find dawsos -name "*.pyo" -delete 2>/dev/null

# 3. Clear Streamlit cache
echo "3. Clearing Streamlit cache..."
rm -rf ~/.streamlit/cache 2>/dev/null
rm -rf .streamlit 2>/dev/null

# 4. Wait
echo "4. Waiting for ports to free..."
sleep 3

echo "✅ Clean complete!"
echo ""
echo "Now start the app with: ./start.sh"
echo "Then open: http://localhost:8501"
echo ""
echo "In your browser:"
echo "  - Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)"
echo "  - Or: Click ☰ menu → Clear cache → Refresh"
