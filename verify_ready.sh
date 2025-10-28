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

# Check 3: Database Services
echo "3. Database Services:"
if docker ps | grep -q "dawsos-postgres"; then
    PG_STATUS=$(docker ps --filter "name=dawsos-postgres" --format "{{.Status}}")
    echo "   ✅ PostgreSQL: $PG_STATUS"
else
    echo "   ❌ PostgreSQL not running"
    READY=false
fi

if docker ps | grep -q "dawsos-redis"; then
    REDIS_STATUS=$(docker ps --filter "name=dawsos-redis" --format "{{.Status}}")
    echo "   ✅ Redis: $REDIS_STATUS"
else
    echo "   ❌ Redis not running"
    READY=false
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

# Check 6: Observability Configuration
echo "6. Observability Stack:"
if [ -f "observability/prometheus/prometheus.yml" ]; then
    echo "   ✅ Prometheus configuration"
fi

if [ -f "observability/grafana/provisioning/datasources/prometheus.yml" ]; then
    echo "   ✅ Grafana datasources"
fi

DASHBOARD_COUNT=$(ls -1 observability/grafana/dashboards/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ $DASHBOARD_COUNT Grafana dashboards"

if [ -f "observability/otel/otel-collector-config.yml" ]; then
    echo "   ✅ OpenTelemetry Collector config"
fi
echo ""

# Check 7: Documentation
echo "7. Documentation:"
DOC_COUNT=0
for doc in READY_TO_LAUNCH.md LAUNCH_GUIDE.md ENVIRONMENT_SETUP_COMPLETE.md API_KEYS_CONFIGURED.md OBSERVABILITY_QUICKSTART.md; do
    if [ -f "$doc" ]; then
        DOC_COUNT=$((DOC_COUNT + 1))
    fi
done
echo "   ✅ $DOC_COUNT documentation files"
echo ""

# Check 8: Tests
echo "8. Tests:"
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
    echo "  Option 2: Full Stack (Docker)"
    echo "  ----------------------------------------"
    echo "  docker compose --profile observability up -d"
    echo ""
    echo "  Access:"
    echo "    • Frontend:   http://localhost:8501"
    echo "    • Backend:    http://localhost:8000"
    echo "    • API Docs:   http://localhost:8000/docs"
    echo "    • Grafana:    http://localhost:3000"
    echo "    • Prometheus: http://localhost:9090"
    echo "    • Jaeger:     http://localhost:16686"
    echo ""
    echo "For detailed instructions, see: READY_TO_LAUNCH.md"
    echo ""
else
    echo "❌ NOT READY - FIX ISSUES ABOVE"
    echo "========================================="
    exit 1
fi
