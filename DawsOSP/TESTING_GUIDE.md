# DawsOS Testing Guide

**Date**: 2025-10-23
**Purpose**: Instructions for testing the seeded end-to-end integration
**Status**: Seeded flows ready; macro scenarios/optimizer pending implementation

---

## 🎯 Quick Start

> **Container names**: The full docker stack uses `dawsos-postgres` / `dawsos-redis`; the lightweight stack (`docker-compose.simple.yml`) runs as `dawsos-dev-postgres` / `dawsos-dev-redis`. Commands below reference the full-stack names—adjust if you are running the simple database compose file.

### Step 1: Run the Integration Test

```bash
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP
./test_integration.sh
```

This will:
- ✅ Check Docker containers (PostgreSQL, Redis)
- ✅ Verify database connectivity and schema
- ✅ Test backend API endpoints (if running)
- ✅ Test frontend UI (if running)
- ✅ Verify end-to-end integration

### Step 2: Start the Backend API

**In Terminal 1:**
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP
./backend/run_api.sh
```

This will:
- Activate virtual environment
- Install dependencies (if needed)
- Start PostgreSQL/Redis containers (if not running)
- Launch Executor API on **http://localhost:8000**

**Expected output:**
```
========================================
DawsOS Executor API Launcher
========================================

Activating virtual environment...
Checking dependencies...
Checking database connection...
Setting environment variables...

Configuration:
  Database URL: postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos
  API URL: http://localhost:8000
  CORS Origins: http://localhost:8501,http://127.0.0.1:8501
  Environment: development

Starting Executor API on http://localhost:8000

Available endpoints:
  POST http://localhost:8000/v1/execute     - Execute patterns
  GET  http://localhost:8000/health         - Health check
  GET  http://localhost:8000/patterns       - List patterns
  GET  http://localhost:8000/metrics        - Prometheus metrics
```

### Step 3: Start the Frontend UI

**In Terminal 2:**
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP
./frontend/run_ui.sh
```

This will:
- Activate virtual environment
- Launch Streamlit UI on **http://localhost:8501**

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Step 4: Open the UI in Browser

```bash
# macOS
open http://localhost:8501

# Linux
xdg-open http://localhost:8501

# Or manually navigate to: http://localhost:8501
```

---

## 🧪 Testing User Scenarios

### Scenario 1: Portfolio Overview ✅

**Goal**: View portfolio metrics, currency attribution, and holdings

**Steps**:
1. Open UI at http://localhost:8501
2. Navigate to "Portfolio Overview" (should be default page)
3. Verify you see:
   - KPI metrics (Total Value, Day Change, YTD Return, Sharpe Ratio)
   - Currency attribution chart
   - Holdings table with symbols, quantities, prices
   - Pricing pack ID and ledger commit hash at bottom

**Expected Result**:
- Real data from database (not mock data)
- Holdings: AAPL, RY, XIU (from seed data)
- Portfolio ID: starts with "11111111-1111-1111-1111-..."

**Verify Pattern Execution**:
- Check Terminal 1 (API logs) for:
  ```
  Pattern executed successfully: portfolio_overview, request_id=...
  ```

---

### Scenario 2: Holdings Deep-Dive ✅

**Goal**: Select a holding and view detailed analysis

**Steps**:
1. Navigate to "Holdings" page
2. See list of holdings (AAPL, RY, XIU)
3. Click on a symbol (e.g., AAPL)
4. Verify you see:
   - Buffett Ratings section (DivSafety, Moat, Resilience)
   - Fundamentals section (placeholder - service not implemented yet)
   - News section (placeholder - service not implemented yet)

**Expected Result**:
- Holdings list displayed from `portfolio_overview` pattern
- Deep-dive loads with `holding_deep_dive` pattern
- Ratings show placeholder message (ratings service not yet implemented)

**Verify Pattern Execution**:
- Check Terminal 1 (API logs) for:
  ```
  Pattern executed successfully: holding_deep_dive, request_id=...
  ```

---

### Scenario 3: Macro Dashboard ✅

**Goal**: View current macro regime and economic cycles

**Steps**:
1. Navigate to "Macro Dashboard" page
2. Verify you see:
   - Current regime (one of 5: Early/Mid/Late Expansion, Early/Deep Contraction)
   - Regime confidence score
   - Economic indicators (T10Y2Y, UNRATE, CPIAUCSL, etc.)
   - Cycle phases (STDC, LTDC, Empire)

**Expected Result**:
- Real regime detection from macro indicators
- Cycle phases from database seed data
- Visual indicators with color coding

**Verify Pattern Execution**:
- Check Terminal 1 (API logs) for:
  ```
  Pattern executed successfully: portfolio_macro_overview, request_id=...
  ```

---

### Scenario 4: Scenario Stress Testing (Pending)

**Goal**: Confirm the UI surfaces the current placeholder response while MacroHound scenario services are incomplete.

**Steps**:
1. Navigate to the "Scenarios" page (if the screen is enabled).
2. Run any preset scenario (e.g., "📈 Rates +100bps").
3. Observe the API response payload.

**Expected Result**:
- Response includes `{"error": "Scenario service not yet implemented"}` from `macro.run_scenario`.
- No portfolio impact metrics are returned yet.
- Terminal logs show the capability invocation without stack traces.

**Verify Pattern Execution**:
- Look for the placeholder response in Terminal 1 (API logs). Failures here should be logged in `.ops/TASK_INVENTORY_2025-10-24.md`.

---

### Scenario 5: Custom Scenario Builder (Pending)

**Goal**: Verify custom scenario execution still returns the placeholder response and does not crash.

**Steps**:
1. Open the "Custom Scenario" tab (if exposed in the UI).
2. Submit any combination of factor shocks.

**Expected Result**:
- API returns `{"error": "Scenario service not yet implemented"}`.
- UI surfaces a placeholder message; no trades or hedges are computed yet.

**Verify Pattern Execution**:
- Confirm `macro.run_scenario` is invoked with the provided parameters in the API logs.

---

## 🔍 API Testing (Manual)

### Test Health Check

```bash
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T...",
  "version": "1.0.0"
}
```

### Test Patterns List

```bash
curl http://localhost:8000/patterns
```

**Expected output:**
```json
{
  "patterns": [
    "portfolio_overview",
    "holding_deep_dive",
    "portfolio_macro_overview",
    "portfolio_scenario_analysis",
    ...
  ]
}
```

### Test Pattern Execution

```bash
# Get portfolio ID from database
PORTFOLIO_ID=$(docker exec dawsos-postgres psql -U dawsos -d dawsos -t -c "SELECT id FROM portfolios LIMIT 1;" | tr -d ' ')

# Execute pattern
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d "{
    \"pattern_id\": \"portfolio_overview\",
    \"inputs\": {\"portfolio_id\": \"$PORTFOLIO_ID\"},
    \"require_fresh\": false
  }"
```

**Expected output:**
```json
{
  "request_id": "req-...",
  "data": {
    "perf_metrics": { ... },
    "currency_attr": { ... },
    "valued_positions": [ ... ]
  },
  "metadata": {
    "pattern_id": "portfolio_overview",
    "pricing_pack_id": "...",
    "ledger_commit_hash": "...",
    "execution_time_ms": 245.2
  }
}
```

---

## 📊 Database Verification

### Check Seed Data

```bash
# Connect to database
docker exec -it dawsos-postgres psql -U dawsos -d dawsos

# Check portfolios
SELECT id, name, base_currency FROM portfolios;

# Check holdings
SELECT symbol, quantity, cost_basis FROM lots;

# Check macro indicators
SELECT * FROM macro_indicators ORDER BY date DESC LIMIT 5;

# Check cycle phases
SELECT * FROM cycle_phases ORDER BY date DESC LIMIT 3;

# Exit
\q
```

---

## 🐛 Troubleshooting

### Backend API Won't Start

**Symptom**: `./backend/run_api.sh` fails

**Solutions**:
```bash
# 1. Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# 2. Check if database is running
docker ps | grep dawsos-postgres

# 3. Start database if needed
docker-compose -f docker-compose.simple.yml up -d

# 4. Check virtual environment
source venv/bin/activate
pip install -r backend/requirements.txt

# 5. Try running directly
cd backend
uvicorn app.api.executor:app --host 0.0.0.0 --port 8000
```

---

### Frontend UI Won't Start

**Symptom**: `./frontend/run_ui.sh` fails

**Solutions**:
```bash
# 1. Check if port 8501 is in use
lsof -ti:8501 | xargs kill -9

# 2. Check virtual environment
source venv/bin/activate
pip install streamlit

# 3. Try running directly
streamlit run frontend/main.py --server.port 8501
```

---

### UI Shows Mock Data Instead of Real Data

**Symptom**: UI displays "Mock Data Mode" or hardcoded values

**Cause**: Backend API not running or UI not configured to use API

**Solutions**:
```bash
# 1. Verify backend API is running
curl http://localhost:8000/health

# 2. Check UI environment variable
# In frontend/main.py, verify:
USE_MOCK_CLIENT = os.getenv("USE_MOCK_CLIENT", "false").lower() == "true"

# Should be "false" (default)

# 3. Check API URL in UI logs
# Look for: "DawsOSClient initialized with base_url=http://localhost:8000"

# 4. Restart UI
pkill -f streamlit
./frontend/run_ui.sh
```

---

### Pattern Execution Fails

**Symptom**: API returns 500 error or UI shows error message

**Solutions**:
```bash
# 1. Check API logs (Terminal 1)
# Look for error messages and stack traces

# 2. Check if agents are registered
# In API logs, look for:
# "Agent runtime initialized with 4 agents: financial_analyst, macro_hound, data_harvester, claude"

# 3. Check database connection
docker exec dawsos-postgres psql -U dawsos -d dawsos -c "SELECT 1;"

# 4. Check if pattern exists
curl http://localhost:8000/patterns

# 5. Try with require_fresh=false
# In UI code or API call, set require_fresh=false to bypass freshness gate
```

---

### Database Connection Error

**Symptom**: "could not connect to server" or "connection refused"

**Solutions**:
```bash
# 1. Check if PostgreSQL container is running
docker ps | grep dawsos-postgres

# 2. Start containers if not running
docker-compose -f docker-compose.simple.yml up -d

# 3. Wait for database to be healthy
docker ps | grep dawsos-postgres
# Should show "(healthy)" in status

# 4. Check connection string
# In .env.database:
DATABASE_URL=postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos

# 5. Test connection
docker exec dawsos-postgres psql -U dawsos -d dawsos -c "SELECT COUNT(*) FROM portfolios;"
```

---

## 🎯 Expected Test Results

### Full Stack Operational

When running `./test_integration.sh` with all services running:

```
========================================
DawsOS Integration Test
========================================

Step 1: Infrastructure Checks
✅ PASS: PostgreSQL container running
✅ PASS: Redis container running
✅ PASS: Database connection successful
✅ PASS: Database schema exists (20+ tables)
✅ PASS: Seed data exists (1+ portfolios)

Step 2: Backend API Checks
✅ PASS: Health check endpoint (HTTP 200)
✅ PASS: Patterns list endpoint (HTTP 200)
✅ PASS: Prometheus metrics endpoint (HTTP 200)
✅ PASS: Execute portfolio_overview pattern (HTTP 200)

Step 3: Frontend UI Checks
✅ PASS: Streamlit UI running on port 8501

Step 4: End-to-End Integration
✅ PASS: End-to-end stack operational

========================================
Test Summary
========================================
Total Tests: 10
Passed: 10
Failed: 0
Pass Rate: 100%

========================================
🎉 ALL TESTS PASSED!
========================================

✅ DawsOS is fully operational!

Access the application:
  UI:  http://localhost:8501
  API: http://localhost:8000
```

---

## 📝 Test Checklist

### Infrastructure
- [ ] PostgreSQL container running and healthy
- [ ] Redis container running and healthy
- [ ] Database schema created (20+ tables)
- [ ] Seed data loaded (portfolios, lots, macro data)

### Backend API
- [ ] API starts without errors
- [ ] Health check returns 200
- [ ] Patterns list returns available patterns
- [ ] Pattern execution returns 200 with data
- [ ] Agents registered (4 agents: financial_analyst, macro_hound, data_harvester, claude)

### Frontend UI
- [ ] UI starts without errors
- [ ] UI accessible at http://localhost:8501
- [ ] No "Mock Data Mode" warnings
- [ ] API client configured with http://localhost:8000

### End-to-End Integration
- [ ] Portfolio Overview loads real data
- [ ] Holdings screen displays holdings
- [ ] Macro Dashboard shows regime
- [ ] Scenarios execute and show delta P&L
- [ ] Provenance metadata displayed (pricing_pack_id, ledger_commit_hash)

### Pattern Execution
- [ ] `portfolio_overview` pattern executes successfully
- [ ] `holding_deep_dive` pattern executes successfully
- [ ] `portfolio_macro_overview` pattern executes successfully
- [ ] `portfolio_scenario_analysis` pattern executes successfully

---

## 🚀 Next Steps After Testing

### If All Tests Pass ✅

1. **Explore the UI** - Try all screens and features
2. **Review API logs** - Understand pattern execution flow
3. **Check database** - Query tables to see stored data
4. **Read documentation** - See [UI_WIRING_COMPLETE.md](UI_WIRING_COMPLETE.md) for implementation details

### If Tests Fail ❌

1. **Check error messages** - Read logs carefully
2. **Follow troubleshooting guide** - See section above
3. **Verify prerequisites** - Database, Docker, Python packages
4. **Report issues** - Document errors and steps to reproduce

---

## 📚 Related Documentation

1. [UI_WIRING_COMPLETE.md](UI_WIRING_COMPLETE.md) - Implementation summary
2. [UAT_READINESS_AUDIT.md](UAT_READINESS_AUDIT.md) - Comprehensive audit
3. [UI_LAUNCHED.md](UI_LAUNCHED.md) - UI launch guide
4. [PRODUCT_SPEC.md](PRODUCT_SPEC.md) - Product specification

---

## 🆘 Getting Help

### Logs to Check

**Backend API Logs** (Terminal 1):
- Pattern execution traces
- Database queries
- Error stack traces

**Frontend UI Logs** (Terminal 2):
- Streamlit output
- API client requests
- UI component rendering

**Database Logs**:
```bash
docker logs -f dawsos-postgres
```

### Common Questions

**Q: Why is the UI showing placeholder data for Buffett Ratings?**
A: The ratings service is not yet implemented (P0 gap identified in audit). Holdings screen is ready, but ratings calculation is pending.

**Q: Why does scenario analysis show "No data available"?**
A: The scenario service is implemented in backend, but may need factor betas populated in database. Check `position_factor_betas` table.

**Q: How do I know if the UI is using real API vs. mock data?**
A: Check the API logs (Terminal 1). You should see pattern execution messages when UI makes requests. Also, UI will show pricing_pack_id and ledger_commit_hash at bottom of screens.

**Q: What if I see "503 Service Unavailable" error?**
A: This is the freshness gate blocking execution because pricing pack is stale. Set `require_fresh=false` in the pattern execution call, or pre-warm the pricing pack.

---

**Last Updated**: 2025-10-23
**Status**: Ready for testing
**Required Services**: PostgreSQL, Redis, Backend API, Frontend UI
**Estimated Test Time**: 15-20 minutes
