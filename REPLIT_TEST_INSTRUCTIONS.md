# Replit Backend Testing Instructions

**Created:** 2025-11-05
**Purpose:** Step-by-step instructions for testing backend services on Replit after bug fixes

---

## Context

After fixing the critical SQL bug (commit 89e2617), we need to verify:
1. ✅ All SQL queries use correct field name pattern (verified locally)
2. ⏳ FactorAnalyzer service works with real data
3. ⏳ Risk metrics calculations complete successfully
4. ⏳ Pattern orchestration runs without errors

---

## Test 1: Run Field Name Consistency Tests

**What it does:** Regression tests to prevent future field name bugs
**Time:** 2-3 minutes
**Priority:** P0 (Critical)

### Steps:

```bash
# Run the new regression test suite
pytest backend/tests/test_field_name_consistency.py -v

# Expected output: All tests pass ✅
# - test_portfolio_daily_values_schema
# - test_query_pattern_validation
# - test_broken_query_pattern_fails
# - test_risk_metrics_query
# - test_metrics_service_queries
# - test_factor_analysis_query
# - test_financial_analyst_query
# - test_all_queries_use_correct_pattern
# - test_e2e_portfolio_metrics
```

### Success Criteria:
- ✅ All 9 tests pass
- ✅ No SQL errors about missing columns
- ✅ End-to-end test completes

### If Tests Fail:
1. Check error message for specific query that failed
2. Verify the query uses `valuation_date as asof_date` pattern
3. Check that portfolio_daily_values table exists and has data

---

## Test 2: Test FactorAnalyzer Service (CRITICAL - 40 Hour Decision)

**What it does:** Tests if existing FactorAnalyzer service works or needs reimplementation
**Time:** 5-10 minutes
**Priority:** P0 (Blocks 40 hours of work)

### Background:
The FactorAnalyzer service exists but may return stub data. If it works with real data, we save 40 hours of reimplementation. If broken, we need to reimplement from scratch.

### Steps:

```bash
# Create test script
cat > test_factor_analyzer.py << 'EOF'
"""
Test FactorAnalyzer Service

Decision point: Does FactorAnalyzer work with real data?
- YES → Save 40 hours (use existing service)
- NO → Reimplement from scratch (40 hour task)
"""

import asyncio
from app.services.factor_analysis import FactorAnalyzer
from app.db.connection import get_db_pool

async def test_factor_analyzer():
    print("=" * 60)
    print("TESTING FACTORANALYZER SERVICE")
    print("=" * 60)

    # Initialize database
    db = await get_db_pool()
    analyzer = FactorAnalyzer(db)

    print("\n1. Checking for test data...")

    # Get a test portfolio
    portfolio_row = await db.fetchrow(
        "SELECT portfolio_id FROM portfolios LIMIT 1"
    )

    if not portfolio_row:
        print("❌ No portfolios found - create a test portfolio first")
        return

    portfolio_id = str(portfolio_row["portfolio_id"])
    print(f"✅ Found portfolio: {portfolio_id}")

    # Get latest pricing pack
    pack_row = await db.fetchrow(
        "SELECT pack_id, date FROM pricing_packs ORDER BY date DESC LIMIT 1"
    )

    if not pack_row:
        print("❌ No pricing packs found - run pricing pipeline first")
        return

    pack_id = str(pack_row["pack_id"])
    pack_date = pack_row["date"]
    print(f"✅ Found pricing pack: {pack_id} (date: {pack_date})")

    # Check for economic indicators (required for factor analysis)
    try:
        econ_count = await db.fetchval(
            "SELECT COUNT(*) FROM economic_indicators"
        )
        print(f"✅ Economic indicators: {econ_count} records")

        if econ_count == 0:
            print("⚠️  WARNING: No economic indicators data")
            print("   Factor analysis needs FRED data ingestion")
    except Exception as e:
        print(f"❌ economic_indicators table missing: {e}")
        print("   Run migration: 015_add_economic_indicators.sql")
        return

    # Check for portfolio daily values
    pdv_count = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM portfolio_daily_values
        WHERE portfolio_id = $1
        """,
        portfolio_row["portfolio_id"]
    )

    print(f"✅ Portfolio daily values: {pdv_count} records")

    if pdv_count < 30:
        print(f"⚠️  WARNING: Only {pdv_count} days of data (need 30+ for factor analysis)")

    print("\n2. Testing FactorAnalyzer.compute_factor_exposure()...")

    try:
        result = await analyzer.compute_factor_exposure(
            portfolio_id=portfolio_id,
            pack_id=pack_id,
            lookback_days=252
        )

        print("\n3. Result received:")
        print("-" * 60)

        # Check if result contains stub data indicators
        if "_provenance" in result:
            prov = result["_provenance"]
            if prov.get("type") == "stub":
                print("❌ RESULT: STUB DATA DETECTED")
                print(f"   Source: {prov.get('source', 'unknown')}")
                print(f"   Warnings: {prov.get('warnings', [])}")
                print("\n   DECISION: Need to reimplement FactorAnalyzer (40 hours)")
                return "REIMPLEMENT"
            else:
                print("✅ RESULT: REAL DATA")
                print(f"   Source: {prov.get('source', 'computation')}")
                print(f"   Confidence: {prov.get('confidence', 'unknown')}")

        # Check for error field
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            print("\n   DECISION: Need to fix or reimplement FactorAnalyzer")
            return "FIX_OR_REIMPLEMENT"

        # Display factor exposures
        if "factors" in result:
            print(f"✅ Factor exposures computed:")
            for factor_name, exposure in result["factors"].items():
                print(f"   - {factor_name}: {exposure:.4f}")

        if "r_squared" in result:
            print(f"✅ R-squared: {result['r_squared']:.4f}")

        if "data_points" in result:
            print(f"✅ Data points used: {result['data_points']}")

        print("\n" + "=" * 60)
        print("✅ DECISION: FactorAnalyzer works! Use existing service (save 40 hours)")
        print("=" * 60)
        return "USE_EXISTING"

    except Exception as e:
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
        print("\n   DECISION: Need to fix or reimplement FactorAnalyzer")
        import traceback
        traceback.print_exc()
        return "FIX_OR_REIMPLEMENT"

if __name__ == "__main__":
    result = asyncio.run(test_factor_analyzer())
    print(f"\n\nFINAL DECISION: {result}")
EOF

# Run the test
python test_factor_analyzer.py
```

### Success Criteria - Option A (Best Case):
```
✅ DECISION: FactorAnalyzer works! Use existing service (save 40 hours)
   - Factor exposures computed with real data
   - R-squared is reasonable (0.2-0.8 range)
   - No stub data indicators
   - No errors
```

### Success Criteria - Option B (Need to Reimplement):
```
❌ DECISION: Need to reimplement FactorAnalyzer (40 hours)
   - Returns stub data
   - Missing economic_indicators table
   - Throws exceptions
```

### Next Steps Based on Result:

**If "USE_EXISTING":**
1. ✅ Mark Phase 0 Task 0.5 as DONE (save 40 hours)
2. Remove stub data generation code
3. Continue with Phase 1 refactoring

**If "FIX_OR_REIMPLEMENT":**
1. Investigate specific error
2. If quick fix (<2 hours): Fix it
3. If complex: Reimplement from scratch (40 hours)
4. Update COMPREHENSIVE_REFACTORING_PLAN.md with decision

**If "REIMPLEMENT":**
1. Add 40-hour task to Phase 0
2. Implement FactorAnalyzer from scratch using:
   - `backend/app/services/factor_analysis.py` as template
   - FRED economic indicators as factors
   - Regression: portfolio_returns ~ factor_returns
3. Remove stub data code

---

## Test 3: Test Risk Metrics Service

**What it does:** Verifies risk metrics calculations work after SQL fix
**Time:** 3-5 minutes
**Priority:** P1 (High)

### Steps:

```bash
# Create test script
cat > test_risk_metrics.py << 'EOF'
import asyncio
from app.services.risk_metrics import RiskMetrics
from app.db.connection import get_db_pool

async def test_risk_metrics():
    print("Testing RiskMetrics Service")
    print("=" * 60)

    db = await get_db_pool()
    risk = RiskMetrics(db)

    # Get test data
    portfolio_row = await db.fetchrow("SELECT portfolio_id FROM portfolios LIMIT 1")
    pack_row = await db.fetchrow("SELECT pack_id FROM pricing_packs ORDER BY date DESC LIMIT 1")

    if not portfolio_row or not pack_row:
        print("❌ Missing test data")
        return

    portfolio_id = str(portfolio_row["portfolio_id"])
    pack_id = str(pack_row["pack_id"])

    print(f"Portfolio: {portfolio_id}")
    print(f"Pack: {pack_id}\n")

    # Test VaR calculation (this was broken before fix)
    print("1. Testing compute_var()...")
    try:
        var_result = await risk.compute_var(
            portfolio_id=portfolio_id,
            pack_id=pack_id,
            confidence=0.95,
            lookback_days=252
        )

        if "error" in var_result:
            print(f"⚠️  Warning: {var_result['error']}")
        else:
            print(f"✅ VaR (1-day): {var_result['var_1d']:.4f}")
            print(f"✅ VaR (10-day): {var_result['var_10d']:.4f}")
            print(f"✅ Data points: {var_result['data_points']}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return

    # Test CVaR calculation
    print("\n2. Testing compute_cvar()...")
    try:
        cvar_result = await risk.compute_cvar(
            portfolio_id=portfolio_id,
            pack_id=pack_id,
            confidence=0.95,
            lookback_days=252
        )

        if "error" in cvar_result:
            print(f"⚠️  Warning: {cvar_result['error']}")
        else:
            print(f"✅ CVaR (1-day): {cvar_result['cvar_1d']:.4f}")
            print(f"✅ VaR (1-day): {cvar_result['var_1d']:.4f}")
            print(f"✅ Tail observations: {cvar_result['tail_observations']}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return

    print("\n" + "=" * 60)
    print("✅ RiskMetrics service working correctly")

asyncio.run(test_risk_metrics())
EOF

python test_risk_metrics.py
```

### Success Criteria:
- ✅ No SQL errors about missing columns
- ✅ VaR and CVaR computed successfully
- ✅ Results are reasonable numbers (not NaN or infinity)

---

## Test 4: Test Pattern Orchestration End-to-End

**What it does:** Verifies entire pattern → agent → service → database flow
**Time:** 5-10 minutes
**Priority:** P1 (High)

### Steps:

```bash
# Use existing integration tests
pytest backend/tests/integration/test_pattern_execution.py -v -k "risk"

# Or test specific pattern
curl -X POST http://localhost:8000/api/v1/patterns/execute \
  -H "Authorization: Bearer $TEST_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_cycle_risk",
    "context": {
      "portfolio_id": "YOUR_PORTFOLIO_ID",
      "pricing_pack_id": "LATEST_PACK_ID"
    }
  }'
```

### Success Criteria:
- ✅ Pattern executes without errors
- ✅ Risk analytics data returned
- ✅ No stub data indicators in response
- ✅ Response time < 5 seconds

---

## Test 5: Manual Verification in UI

**What it does:** Verify Risk Analytics page shows real data
**Time:** 2-3 minutes
**Priority:** P1 (User-facing validation)

### Steps:

1. **Open DawsOS frontend**
2. **Navigate to:** Portfolio → Risk Analytics
3. **Check for:**
   - ✅ Factor exposures chart displays
   - ✅ VaR and CVaR values shown
   - ✅ No "No data available" messages
   - ✅ No console errors in browser DevTools

### Expected Result:
```
Risk Analytics Dashboard
========================

Factor Exposures:
- Inflation Risk: 0.25
- Real Rates: -0.15
- Credit Spread: 0.40
...

Value at Risk (95%):
- 1-day VaR: -2.5%
- 10-day VaR: -7.9%

Conditional VaR: -3.5%
```

### Red Flags (Indicates Stub Data):
- ❌ All factor exposures exactly 0.0
- ❌ "Simulated data" disclaimer
- ❌ Unrealistic values (VaR = 0%)

---

## Summary Checklist

After completing all tests, verify:

- [ ] ✅ Field name consistency tests pass (Test 1)
- [ ] ✅ FactorAnalyzer decision made (Test 2)
  - [ ] If works: Remove stub data code
  - [ ] If broken: Add 40h reimplement task
- [ ] ✅ Risk metrics calculations work (Test 3)
- [ ] ✅ Pattern orchestration runs (Test 4)
- [ ] ✅ UI shows real data (Test 5)

---

## Troubleshooting

### Issue: "economic_indicators table does not exist"

**Solution:**
```bash
# Run missing migration
psql $DATABASE_URL -f backend/migrations/015_add_economic_indicators.sql

# Ingest FRED data
python backend/scripts/ingest_fred_data.py
```

### Issue: "Insufficient data (minimum 30 days required)"

**Solution:**
```bash
# Backfill portfolio daily values
python backend/scripts/backfill_portfolio_values.py --days 365
```

### Issue: "No pricing packs found"

**Solution:**
```bash
# Run pricing pipeline
python backend/scripts/run_pricing_pipeline.py
```

### Issue: Tests pass but UI shows stub data

**Root Cause:** Pattern JSON still points to old stub capability

**Solution:**
1. Check pattern JSON: `backend/patterns/portfolio_cycle_risk.json`
2. Verify capability names match real implementations
3. Restart backend server to reload patterns

---

## Next Steps After Testing

### If All Tests Pass:
1. ✅ Mark Phase 0 complete
2. Update COMPREHENSIVE_REFACTORING_PLAN.md
3. Start Phase 1: Standardize response formats
4. Remove all stub data generation code

### If Tests Fail:
1. Document specific failure in GitHub issue
2. Update REPLIT_BACKEND_TASKS.md with findings
3. Prioritize fixes before continuing refactoring

---

**Last Updated:** 2025-11-05
**Related Files:**
- `backend/tests/test_field_name_consistency.py` (new regression tests)
- `COMPREHENSIVE_REFACTORING_PLAN.md` (refactoring roadmap)
- `REPLIT_BACKEND_TASKS.md` (backend task list)
- `.claude/commands/test-factor-analyzer.md` (slash command for local testing)
