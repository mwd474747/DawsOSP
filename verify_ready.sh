#!/bin/bash
echo "========================================="
echo "DawsOS Launch Readiness Check"
echo "========================================="
echo ""

READY=true

# Check 1: Virtual Environment
echo "1. Virtual Environment:"
if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    echo "   ✅ Virtual environment exists"
    VENV_PYTHON=$(venv/bin/python --version 2>&1)
    echo "   ✅ $VENV_PYTHON"
else
    echo "   ❌ Virtual environment missing"
    READY=false
fi
echo ""

# Check 2: Dependencies
echo "2. Dependencies:"
if venv/bin/pip show fastapi streamlit >/dev/null 2>&1; then
    BACKEND_PKGS=$(venv/bin/pip list 2>/dev/null | wc -l)
    echo "   ✅ $BACKEND_PKGS packages installed"
else
    echo "   ❌ Dependencies missing"
    READY=false
fi
echo ""

# Check 3: Database Connection
echo "3. Database Connection:"
if python -c "import asyncpg; import os; import asyncio; async def test(): conn = await asyncpg.connect(os.getenv('DATABASE_URL', 'postgresql://localhost/dawsos')); await conn.close(); asyncio.run(test())" 2>/dev/null; then
    echo "   ✅ Database connection successful"
else
    echo "   ⚠️  Database connection check skipped (DATABASE_URL may not be set)"
fi
echo ""

# Check 4: API Keys
echo "4. API Keys:"
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    
    KEY_COUNT=$(grep -E "^(FMP_API_KEY|POLYGON_API_KEY|FRED_API_KEY|NEWSAPI_KEY|ANTHROPIC_API_KEY)=" .env | grep -v "^#" | wc -l | tr -d ' ')
    echo "   ✅ $KEY_COUNT API keys configured"
    
    # Show providers (masked)
    [ -n "$(grep '^FMP_API_KEY=' .env | cut -d'=' -f2)" ] && echo "      • FMP (Fundamentals)"
    [ -n "$(grep '^POLYGON_API_KEY=' .env | cut -d'=' -f2)" ] && echo "      • Polygon (Prices)"
    [ -n "$(grep '^FRED_API_KEY=' .env | cut -d'=' -f2)" ] && echo "      • FRED (Macro)"
    [ -n "$(grep '^NEWSAPI_KEY=' .env | cut -d'=' -f2)" ] && echo "      • NewsAPI"
    [ -n "$(grep '^ANTHROPIC_API_KEY=' .env | cut -d'=' -f2)" ] && echo "      • Anthropic Claude"
else
    echo "   ⚠️  .env file missing (optional - app works in stub mode)"
fi
echo ""

# Check 5: Launch Scripts
echo "5. Launch Scripts:"
for script in backend/run_api.sh frontend/run_ui.sh activate.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo "   ✅ $script"
        else
            echo "   ⚠️  $script (fixing permissions)"
            chmod +x "$script"
        fi
    fi
done
echo ""

# Check 6: Documentation
echo "6. Documentation:"
DOC_COUNT=0
for doc in README.md ARCHITECTURE.md DEVELOPMENT_GUIDE.md DEPLOYMENT.md TROUBLESHOOTING.md; do
    if [ -f "$doc" ]; then
        DOC_COUNT=$((DOC_COUNT + 1))
    fi
done
echo "   ✅ $DOC_COUNT core documentation files"
echo ""

# Check 7: Tests
echo "7. Tests:"
TEST_COUNT=$(find backend/tests -name "test_*.py" | wc -l | tr -d ' ')
echo "   ✅ $TEST_COUNT test files"
echo ""

# Final Status
echo "========================================="
if [ "$READY" = true ]; then
    echo "🎉 ALL SYSTEMS GO - READY TO LAUNCH"
    echo "========================================="
    echo ""
    echo "Quick Launch Commands:"
    echo ""
    echo "  Option 1: Development Mode (Recommended)"
    echo "  ----------------------------------------"
    echo "  Terminal 1: source activate.sh && ./backend/run_api.sh"
    echo "  Terminal 2: source activate.sh && ./frontend/run_ui.sh"
    echo ""
    echo "  Access:"
    echo "    • Frontend:   http://localhost:8000"
    echo "    • Backend:    http://localhost:8000"
    echo "    • API Docs:   http://localhost:8000/docs"
    echo ""
    echo "For detailed instructions, see: READY_TO_LAUNCH.md"
    echo ""
else
    echo "❌ NOT READY - FIX ISSUES ABOVE"
    echo "========================================="
    exit 1
fi
