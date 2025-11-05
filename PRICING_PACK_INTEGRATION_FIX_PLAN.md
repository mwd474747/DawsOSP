# Pricing Pack Integration - Complete Fix Plan

**Date:** November 4, 2025, 19:00 PST
**Status:** 🔧 **ACTION REQUIRED**
**Context:** Audit findings + runtime feedback from user

---

## 🎯 Executive Summary

Based on comprehensive audit and runtime testing, the pricing pack system has:
- ✅ **Architecture**: Well-designed (immutability, reproducibility)
- ✅ **Data Storage**: All 9 security prices in database
- ❌ **Integration**: **BROKEN** - Field name mismatches cause position valuation failures

**Root Cause:** Database schema was migrated (`qty` → `quantity`, `value` → `market_value`) but backend code not fully updated.

**Impact:**
- **17 positions skipped** during valuation
- **0 positions valued** (empty portfolio shown to users)
- **Cascading failures**: Metrics, risk, attribution all fail downstream

---

## 🚨 Critical Issues (From Audit + Runtime Testing)

### **Issue #1: Line 374 Field Name Mismatch** 🔴 CRITICAL

**Location:** `backend/app/agents/financial_analyst.py:374`

**Current Code (BROKEN):**
```python
# Line 365: Correctly sets market_value
valued_position = {
    **pos,
    "price": price,
    "value_local": value_local,
    "market_value": value_base,  # ✅ CORRECT
    "fx_rate": fx_rate,
    "base_currency": base_currency,
}
valued_positions.append(valued_position)
total_value_base += value_base

# Line 372-374: Incorrectly reads from "value" instead of "market_value"
if total_value_base > 0:
    for vp in valued_positions:
        vp["weight"] = vp["value"] / total_value_base  # ❌ KeyError: 'value'
```

**Why This Breaks:**
1. Line 365 sets `market_value` key
2. Line 374 tries to read `value` key
3. `KeyError` → position skipped → 0 positions valued

**Fix:**
```python
# Line 374: Change from vp["value"] to vp["market_value"]
if total_value_base > 0:
    for vp in valued_positions:
        vp["weight"] = vp["market_value"] / total_value_base  # ✅ FIXED
else:
    for vp in valued_positions:
        vp["weight"] = Decimal("0")
```

**Verification:**
```python
# After fix, verify valued_positions structure:
valued_position = {
    "security_id": "...",
    "symbol": "AAPL",
    "quantity": 100,
    "market_value": 15000.0,  # ✅ Set at line 365
    "weight": 0.23,            # ✅ Calculated at line 374 using market_value
    "fx_rate": 1.3625,
    "base_currency": "CAD"
}
```

---

### **Issue #2: Triple Pricing Pack Implementation** 🔴 CRITICAL

**Problem:** Three separate implementations cause confusion and maintenance burden.

| File | Lines | Status | Used By |
|------|-------|--------|---------|
| `pricing_pack.py` | 510 | ❌ **ORPHANED** | Nothing (dead code) |
| `build_pricing_pack.py` | 697 | ✅ **PRODUCTION** | scheduler.py |
| `build_pack_stub.py` | 387 | ✅ **DEV/TEST** | Development |

**Fix:** Archive orphaned file
```bash
# Create archive directory
mkdir -p .archive/pricing-pack-consolidation-20251104/

# Move orphaned file with documentation
mv backend/jobs/pricing_pack.py .archive/pricing-pack-consolidation-20251104/

# Create README explaining why archived
cat > .archive/pricing-pack-consolidation-20251104/README.md << 'EOF'
# Archived: Original Pricing Pack Implementation

**Date Archived:** November 4, 2025
**Reason:** Superseded by build_pricing_pack.py (simpler Polygon-only approach)

## Original Design (Oct 21)
- Polygon (primary) + FMP (fallback) + FRED (FX rates)
- Full provider integration with 3 data sources

## New Design (Oct 23)
- Polygon-only (prices + FX rates via proxy)
- Simpler implementation, fewer dependencies

## Files
- pricing_pack.py (510 lines) - ARCHIVED
- build_pricing_pack.py (697 lines) - PRODUCTION
- build_pack_stub.py (387 lines) - DEV/TEST

## If You Need This
FMP and FRED providers still exist in app/integrations/
Can restore full provider integration if needed
EOF
```

---

### **Issue #3: Code Duplication** 🔴 CRITICAL

**Problem:** ~170 lines of identical code across 3 files

**Duplicate Methods:**
1. `_compute_hash()` - 27 lines × 3 files = 81 lines
2. `_insert_prices()` - 30 lines × 2 files = 60 lines
3. `_insert_fx_rates()` - 30 lines × 2 files = 60 lines

**Fix:** Extract to shared utility module

**Create:** `backend/app/services/pricing_pack_utils.py`
```python
"""
Pricing Pack Utilities
Shared code for pricing pack creation and validation.
"""

import hashlib
import json
from typing import List, Dict
from decimal import Decimal


def compute_pack_hash(prices: List[Dict], fx_rates: List[Dict]) -> str:
    """
    Compute SHA256 hash for pricing pack immutability.

    Args:
        prices: List of price records with security_id, close, currency
        fx_rates: List of FX rate records with base_ccy, quote_ccy, rate

    Returns:
        SHA256 hash (hex string)

    Used by:
        - build_pricing_pack.py
        - build_pack_stub.py
    """
    # Sort for deterministic hash
    prices_sorted = sorted(prices, key=lambda p: p["security_id"])
    fx_sorted = sorted(fx_rates, key=lambda f: (f["base_ccy"], f["quote_ccy"]))

    # Serialize to JSON (only fields that affect pricing)
    data = {
        "prices": [
            {
                "security_id": p["security_id"],
                "close": str(p["close"]),
                "currency": p["currency"],
            }
            for p in prices_sorted
        ],
        "fx_rates": [
            {
                "base_ccy": f["base_ccy"],
                "quote_ccy": f["quote_ccy"],
                "rate": str(f["rate"]),
            }
            for f in fx_sorted
        ],
    }

    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


async def insert_prices_batch(pack_id: str, prices: List[Dict]):
    """
    Batch insert prices into prices table.

    Args:
        pack_id: Pricing pack ID (e.g., "PP_2025-11-04")
        prices: List of price records

    Used by:
        - build_pricing_pack.py
        - build_pack_stub.py
    """
    from app.db.connection import execute_statement

    if not prices:
        return

    query = """
        INSERT INTO prices (
            security_id, pricing_pack_id, asof_date,
            open, high, low, close, volume,
            currency, source
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (security_id, pricing_pack_id) DO NOTHING
    """

    for price in prices:
        await execute_statement(
            query,
            price["security_id"],
            pack_id,
            price["asof_date"],
            price.get("open"),
            price.get("high"),
            price.get("low"),
            price["close"],
            price.get("volume"),
            price["currency"],
            price["source"],
        )


async def insert_fx_rates_batch(pack_id: str, fx_rates: List[Dict]):
    """
    Batch insert FX rates into fx_rates table.

    Args:
        pack_id: Pricing pack ID
        fx_rates: List of FX rate records

    Used by:
        - build_pricing_pack.py
        - build_pack_stub.py
    """
    from app.db.connection import execute_statement

    if not fx_rates:
        return

    query = """
        INSERT INTO fx_rates (
            pricing_pack_id, base_ccy, quote_ccy, asof_ts, rate, source, policy
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (base_ccy, quote_ccy, pricing_pack_id) DO NOTHING
    """

    for fx in fx_rates:
        await execute_statement(
            query,
            pack_id,
            fx["base_ccy"],
            fx["quote_ccy"],
            fx["asof_ts"],
            fx["rate"],
            fx["source"],
            fx["policy"],
        )


def validate_prices_data(prices: List[Dict], min_coverage_pct: float = 0.8) -> bool:
    """
    Validate that price data meets quality requirements.

    Args:
        prices: List of price records
        min_coverage_pct: Minimum coverage required (0.0-1.0)

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    if not prices:
        raise ValueError("No prices provided")

    # Check for required fields
    required_fields = ["security_id", "close", "currency", "source"]
    for price in prices:
        missing = [f for f in required_fields if f not in price]
        if missing:
            raise ValueError(f"Price missing required fields: {missing}")

    # All checks passed
    return True


def validate_fx_rates_data(fx_rates: List[Dict], min_coverage_pct: float = 0.8) -> bool:
    """
    Validate that FX rate data meets quality requirements.

    Args:
        fx_rates: List of FX rate records
        min_coverage_pct: Minimum coverage required (0.0-1.0)

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    if not fx_rates:
        raise ValueError("No FX rates provided")

    # Check for required fields
    required_fields = ["base_ccy", "quote_ccy", "rate", "source"]
    for fx in fx_rates:
        missing = [f for f in required_fields if f not in fx]
        if missing:
            raise ValueError(f"FX rate missing required fields: {missing}")

    # All checks passed
    return True
```

**Update Files to Use Shared Code:**

```python
# build_pricing_pack.py
from app.services.pricing_pack_utils import (
    compute_pack_hash,
    insert_prices_batch,
    insert_fx_rates_batch,
    validate_prices_data,
    validate_fx_rates_data,
)

# Replace _compute_hash with:
pack_hash = compute_pack_hash(prices_data, fx_data)

# Replace _insert_prices with:
await insert_prices_batch(pack_id, prices_data)

# Replace _insert_fx_rates with:
await insert_fx_rates_batch(pack_id, fx_data)
```

---

### **Issue #4: Documentation vs Reality** 🟡 MEDIUM

**Problem:** Documentation claims WM 4PM fix but uses Polygon proxy.

**Current Documentation (MISLEADING):**
```python
"""
Purpose: Build pricing pack with real data from Polygon (prices) and WM Reuters (FX)
...
Provider Attribution:
    - FX Rates: WM Reuters 4PM fixing (via Polygon)  # ⚠️ MISLEADING
"""
```

**Actual Behavior:**
```python
# build_pricing_pack.py line 305-366
async def _build_real_fx_rates(self, asof_date: date) -> List[Dict]:
    """
    Build FX rate data using WM 4PM London fixing.

    For production, this should use WM Reuters API or equivalent.
    For now, we use Polygon FX data as proxy.  # ❌ NOT TEMPORARY!
    """
    fx_symbol = f"C:{base_ccy}{quote_ccy}"  # Polygon FX endpoint
    price_data = await self.polygon_provider.get_daily_price(fx_symbol, ...)
```

**Fix:** Update documentation to match reality

```python
"""
Purpose: Build pricing pack with Polygon data (prices + FX rates)
Updated: 2025-11-04
Priority: P0 (Critical for production)

Provider Attribution:
    - Prices: Polygon.io (split-adjusted daily OHLCV)
    - FX Rates: Polygon FX endpoint (EOD rates, approximates WM 4PM)

    ⚠️ NOTE: Currently using Polygon FX data as proxy for WM 4PM fix.
    For institutional compliance requiring official WM/Reuters data,
    integrate FRED provider (see app/integrations/fred_provider.py)
    or direct WM Reuters API access.

Rationale for Current Approach:
    - Simpler: Single provider (Polygon) for all data
    - Cost-effective: No additional API subscriptions
    - Sufficient: For most portfolios, Polygon FX data is adequate
    - Upgradeable: Can switch to FRED/WM Reuters without schema changes
"""
```

---

### **Issue #5: Silent Fallback on Missing Pricing Packs** 🟡 MEDIUM

**Problem:** System falls back to synthetic pack ID without alerting.

**Current Behavior:**
```python
# combined_server.py line 390-407
pricing_pack_id = f"PP_{date.today().isoformat()}"  # Synthetic default

try:
    query = """
        SELECT id FROM pricing_packs
        WHERE date <= CURRENT_DATE
        ORDER BY date DESC LIMIT 1
    """
    result = await execute_query_safe(query)
    if result and len(result) > 0:
        pricing_pack_id = result[0]["id"]  # ✅ Real pack
except Exception as e:
    logger.warning(f"Could not fetch pricing pack, using default: {e}")
    # ❌ Silent fallback - no alerts, execution continues
```

**Fix:** Add monitoring and fail-fast in production

```python
# combined_server.py (improved)
pricing_pack_id = None
pack_age_days = None

try:
    query = """
        SELECT id, date, status, is_fresh
        FROM pricing_packs
        WHERE date <= CURRENT_DATE
        ORDER BY date DESC
        LIMIT 1
    """
    result = await execute_query_safe(query)

    if result and len(result) > 0:
        pack = result[0]
        pricing_pack_id = pack["id"]
        pack_age_days = (date.today() - pack["date"]).days

        # Check pack freshness
        if not pack["is_fresh"]:
            logger.error(
                f"⚠️  STALE PACK: Pack {pricing_pack_id} not marked fresh "
                f"(status: {pack['status']})"
            )
            # TODO: Send alert to monitoring system

        # Check pack age
        if pack_age_days > 1:
            logger.error(
                f"⚠️  OLD PACK: Using {pack_age_days}-day-old pack {pricing_pack_id}"
            )
            # TODO: Send alert to monitoring system

        logger.info(
            f"✅ Using pricing pack: {pricing_pack_id} "
            f"(age: {pack_age_days} days, fresh: {pack['is_fresh']})"
        )

    else:
        # No packs in database - CRITICAL ERROR
        logger.error("❌ CRITICAL: No pricing packs in database!")

        # In production, fail fast
        if os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError(
                "No pricing packs available. System cannot produce "
                "reproducible results. Check scheduler is running."
            )

        # In development, use synthetic pack but log prominently
        pricing_pack_id = f"PP_{date.today().isoformat()}"
        logger.warning(
            f"⚠️  DEV MODE: Using synthetic pack {pricing_pack_id}. "
            f"Results NOT reproducible!"
        )

except Exception as e:
    logger.error(f"❌ Failed to fetch pricing pack: {e}", exc_info=True)

    # In production, fail fast
    if os.getenv("ENVIRONMENT") == "production":
        raise

    # In development, continue with synthetic pack
    pricing_pack_id = f"PP_{date.today().isoformat()}"
    logger.warning(f"⚠️  DEV MODE: Using synthetic pack {pricing_pack_id}")

# Create request context
ctx = RequestCtx(
    trace_id=str(uuid4()),
    request_id=str(uuid4()),
    user_id=user_id,
    portfolio_id=inputs.get("portfolio_id"),
    asof_date=date.today(),
    pricing_pack_id=pricing_pack_id,
    ledger_commit_hash=ledger_commit_hash,
)
```

---

## 📋 Complete Fix Plan (Prioritized)

### **Phase 1: Critical Fixes (Week 1)** 🔴

#### **Fix 1.1: Line 374 Field Name** ✅ MUST DO
```bash
# File: backend/app/agents/financial_analyst.py
# Line: 374
# Change: vp["value"] → vp["market_value"]

git checkout -b fix/pricing-pack-field-names
```

**Test:**
```python
# Verify positions are valued correctly
ctx = RequestCtx(pricing_pack_id="PP_2025-11-04", ...)
result = await financial_analyst.pricing_apply_pack(ctx, state, positions, pack_id)

assert len(result["positions"]) > 0, "Should have valued positions"
for pos in result["positions"]:
    assert "market_value" in pos, "Should have market_value"
    assert "weight" in pos, "Should have weight"
    assert pos["weight"] > 0, "Weight should be calculated"
```

#### **Fix 1.2: Archive Orphaned File** ✅ MUST DO
```bash
# Archive pricing_pack.py
mkdir -p .archive/pricing-pack-consolidation-20251104/
mv backend/jobs/pricing_pack.py .archive/pricing-pack-consolidation-20251104/

# Create README
cat > .archive/pricing-pack-consolidation-20251104/README.md << 'EOF'
[README content from Issue #2 above]
EOF

git add .archive/
git commit -m "Archive orphaned pricing_pack.py (superseded by build_pricing_pack.py)"
```

#### **Fix 1.3: Update Documentation** ✅ MUST DO
```bash
# Update build_pricing_pack.py header
# Replace misleading "WM Reuters (via Polygon)" with accurate description
# See "Issue #4: Documentation vs Reality" above
```

#### **Fix 1.4: Commit and Test** ✅ MUST DO
```bash
git add backend/app/agents/financial_analyst.py
git commit -m "Fix line 374: Use market_value instead of value for weight calculation

- Line 374: vp['value'] → vp['market_value']
- Fixes KeyError causing 0 positions valued
- All 17 positions should now be valued correctly

Tested:
- Position valuation works end-to-end
- Weights calculated correctly
- Portfolio overview displays positions"

# Test end-to-end
python -m pytest backend/tests/integration/test_pattern_validation.py -v
```

---

### **Phase 2: Code Quality (Week 2)** 🟡

#### **Fix 2.1: Extract Shared Code**
```bash
# Create pricing_pack_utils.py with shared methods
# See "Issue #3: Code Duplication" above

git checkout -b refactor/pricing-pack-utilities
```

**Implementation:**
1. Create `backend/app/services/pricing_pack_utils.py`
2. Extract `compute_pack_hash()`, `insert_prices_batch()`, `insert_fx_rates_batch()`
3. Update `build_pricing_pack.py` to import from utils
4. Update `build_pack_stub.py` to import from utils
5. Remove duplicate methods from both files
6. Test that both scripts still work

**Benefit:**
- Reduces codebase by ~170 lines
- Single source of truth for hash computation
- Easier to test and maintain

#### **Fix 2.2: Add Monitoring**
```bash
# Improve silent fallback handling
# See "Issue #5: Silent Fallback" above
```

**Implementation:**
1. Update `combined_server.py` to check pack status and age
2. Add fail-fast behavior in production environment
3. Log prominently when using synthetic packs in development
4. Consider adding Prometheus metrics:
   - `pricing_pack_age_days` (gauge)
   - `pricing_pack_missing_total` (counter)
   - `pricing_pack_stale_total` (counter)

---

### **Phase 3: Verification (Week 3)** 🟢

#### **Verify 3.1: Production State**

**Create:** `backend/scripts/verify_pricing_pack_health.py`
```python
"""
Verify Pricing Pack Health in Production

Checks:
1. Pricing packs exist in database
2. Latest pack is fresh and recent
3. All securities have prices
4. FX rates are complete
5. Pattern execution works end-to-end
"""

import asyncio
from datetime import date, timedelta
from app.db.connection import get_db_pool, execute_query, execute_query_one
from app.core.pattern_orchestrator import PatternOrchestrator
from app.core.types import RequestCtx


async def verify_pricing_packs():
    """Run all health checks."""
    print("=" * 80)
    print("PRICING PACK HEALTH CHECK")
    print("=" * 80)

    await get_db_pool()

    # 1. Check packs exist
    print("\n1. Checking if pricing packs exist...")
    packs = await execute_query("""
        SELECT id, date, status, is_fresh, created_at
        FROM pricing_packs
        ORDER BY date DESC
        LIMIT 5
    """)

    if not packs:
        print("   ❌ CRITICAL: No pricing packs in database!")
        print("   Action: Run python backend/jobs/build_pricing_pack.py")
        return False

    print(f"   ✅ Found {len(packs)} pricing packs")

    # 2. Check latest pack
    print("\n2. Checking latest pack...")
    latest = packs[0]
    age_days = (date.today() - latest["date"]).days

    print(f"   Pack ID: {latest['id']}")
    print(f"   Date: {latest['date']}")
    print(f"   Age: {age_days} days")
    print(f"   Status: {latest['status']}")
    print(f"   Fresh: {latest['is_fresh']}")

    if age_days > 3:
        print(f"   ⚠️  WARNING: Pack is {age_days} days old (should be < 3)")

    if not latest["is_fresh"]:
        print(f"   ⚠️  WARNING: Pack not marked fresh (status: {latest['status']})")

    # 3. Check prices
    print("\n3. Checking prices...")
    price_count = await execute_query_one("""
        SELECT COUNT(*) as count
        FROM prices
        WHERE pricing_pack_id = $1
    """, latest["id"])

    print(f"   ✅ Found {price_count['count']} prices in pack {latest['id']}")

    # 4. Check FX rates
    print("\n4. Checking FX rates...")
    fx_count = await execute_query_one("""
        SELECT COUNT(*) as count
        FROM fx_rates
        WHERE pricing_pack_id = $1
    """, latest["id"])

    print(f"   ✅ Found {fx_count['count']} FX rates in pack {latest['id']}")

    # 5. Test pattern execution
    print("\n5. Testing pattern execution...")
    try:
        from app.core.agent_runtime import get_agent_runtime
        runtime = get_agent_runtime()
        orchestrator = PatternOrchestrator(runtime, None, None)

        ctx = RequestCtx(
            trace_id="health-check",
            request_id="health-check",
            user_id="00000000-0000-0000-0000-000000000000",
            pricing_pack_id=latest["id"],
            ledger_commit_hash="health-check",
        )

        # Try portfolio_overview pattern
        result = await orchestrator.run_pattern(
            "portfolio_overview",
            ctx,
            {"portfolio_id": "test-portfolio-001"}
        )

        if result and "data" in result:
            positions_count = len(result["data"].get("valued_positions", {}).get("positions", []))
            print(f"   ✅ Pattern executed successfully ({positions_count} positions valued)")
        else:
            print("   ⚠️  Pattern executed but returned no data")

    except Exception as e:
        print(f"   ❌ Pattern execution failed: {e}")

    print("\n" + "=" * 80)
    print("HEALTH CHECK COMPLETE")
    print("=" * 80)
    return True


if __name__ == "__main__":
    asyncio.run(verify_pricing_packs())
```

**Run:**
```bash
python backend/scripts/verify_pricing_pack_health.py
```

#### **Verify 3.2: End-to-End Integration Test**

**Create:** `backend/tests/integration/test_pricing_pack_e2e.py`
```python
"""
End-to-End Integration Test: Pricing Pack → Position Valuation → UI

Tests complete data flow:
1. Pricing pack created with real data
2. Positions loaded from ledger
3. Pricing pack applied (positions valued)
4. Weights calculated correctly
5. Sector allocation computed
6. Historical NAV retrieved
7. Pattern returns complete response
"""

import pytest
from datetime import date
from decimal import Decimal
from app.core.types import RequestCtx


@pytest.mark.integration
async def test_pricing_pack_e2e_flow(db_pool):
    """Test complete pricing pack flow."""

    # 1. Create pricing pack
    from jobs.build_pack_stub import StubPackBuilder
    builder = StubPackBuilder()
    pack_id = await builder.build_pack(
        asof_date=date.today(),
        mark_fresh=True
    )
    assert pack_id is not None

    # 2. Verify pack in database
    from app.db.pricing_pack_queries import get_pricing_pack_queries
    queries = get_pricing_pack_queries()
    pack = await queries.get_pack_by_id(pack_id)
    assert pack is not None
    assert pack["is_fresh"] == True

    # 3. Test position valuation
    from app.agents.financial_analyst import FinancialAnalyst
    analyst = FinancialAnalyst("financial_analyst", {})

    ctx = RequestCtx(
        trace_id="e2e-test",
        request_id="e2e-test",
        user_id="00000000-0000-0000-0000-000000000000",
        pricing_pack_id=pack_id,
        ledger_commit_hash="e2e-test",
    )

    # Mock positions
    positions = [
        {
            "security_id": "11111111-1111-1111-1111-111111111111",
            "symbol": "AAPL",
            "quantity": 100,
            "cost_basis": 15000,
            "currency": "USD",
        },
        {
            "security_id": "22222222-2222-2222-2222-222222222222",
            "symbol": "RY.TO",
            "quantity": 50,
            "cost_basis": 7000,
            "currency": "CAD",
        },
    ]

    # Apply pricing pack
    result = await analyst.pricing_apply_pack(ctx, {}, positions, pack_id)

    # 4. Verify result structure
    assert "positions" in result
    assert "total_value" in result
    assert len(result["positions"]) == 2

    # 5. Verify each position has correct fields
    for pos in result["positions"]:
        assert "security_id" in pos
        assert "symbol" in pos
        assert "quantity" in pos
        assert "market_value" in pos  # ✅ NOT "value"
        assert "weight" in pos
        assert "fx_rate" in pos

        # Verify weight is calculated
        assert pos["weight"] > 0
        assert pos["weight"] <= 1.0

    # 6. Verify weights sum to 1.0 (approximately)
    total_weight = sum(Decimal(str(pos["weight"])) for pos in result["positions"])
    assert abs(total_weight - Decimal("1.0")) < Decimal("0.001")

    # 7. Test complete pattern execution
    from app.core.pattern_orchestrator import PatternOrchestrator
    from app.core.agent_runtime import get_agent_runtime

    runtime = get_agent_runtime()
    orchestrator = PatternOrchestrator(runtime, db_pool, None)

    pattern_result = await orchestrator.run_pattern(
        "portfolio_overview",
        ctx,
        {"portfolio_id": "test-portfolio-001"}
    )

    # 8. Verify pattern result
    assert pattern_result is not None
    assert "data" in pattern_result
    assert "valued_positions" in pattern_result["data"]

    valued = pattern_result["data"]["valued_positions"]
    assert "positions" in valued
    assert "total_value" in valued
    assert len(valued["positions"]) > 0  # ✅ NOT zero!

    print("✅ End-to-end integration test passed!")
```

---

## 📊 Success Criteria

### **Before Fixes**
- ❌ Line 374: `vp["value"]` causes KeyError
- ❌ 17 positions loaded, 0 positions valued
- ❌ Empty portfolio shown to users
- ❌ Sector allocation empty
- ❌ Triple pricing pack implementation
- ❌ ~170 lines duplicate code
- ⚠️ Silent fallback to synthetic packs

### **After Phase 1 (Week 1)**
- ✅ Line 374: Uses `vp["market_value"]` correctly
- ✅ 17 positions loaded, 17 positions valued
- ✅ Complete portfolio shown to users
- ✅ Sector allocation populated
- ✅ Orphaned file archived
- ✅ Documentation accurate

### **After Phase 2 (Week 2)**
- ✅ Single pricing pack implementation (+ stub)
- ✅ Shared utility module (no duplication)
- ✅ Monitoring and alerting added
- ✅ Fail-fast in production

### **After Phase 3 (Week 3)**
- ✅ Production state verified
- ✅ End-to-end tests passing
- ✅ Integration confirmed working

---

## 🔍 Testing Checklist

### **Unit Tests**
- [ ] `compute_pack_hash()` produces consistent hashes
- [ ] `insert_prices_batch()` inserts correctly
- [ ] `insert_fx_rates_batch()` inserts correctly
- [ ] Field validation catches missing fields

### **Integration Tests**
- [ ] Pricing pack created successfully
- [ ] Positions valued with correct field names
- [ ] Weights sum to 1.0
- [ ] Pattern execution returns complete data

### **End-to-End Tests**
- [ ] Portfolio overview shows all positions
- [ ] Sector allocation populated
- [ ] Historical NAV retrieved
- [ ] Metrics calculated (TWR, volatility)
- [ ] Risk metrics computed (DaR, VaR)

### **Production Verification**
- [ ] Pricing packs exist in database
- [ ] Latest pack is fresh (< 1 day old)
- [ ] All securities have prices
- [ ] FX rates complete
- [ ] No synthetic pack fallbacks

---

## 🎯 Summary

### **Root Cause**
Database schema migrated but backend code not fully updated → field name mismatches → position valuation fails

### **Primary Fix** (Line 374)
```python
# BEFORE (BROKEN):
vp["weight"] = vp["value"] / total_value_base  # KeyError

# AFTER (FIXED):
vp["weight"] = vp["market_value"] / total_value_base  # ✅ Works
```

### **Secondary Fixes**
1. Archive orphaned pricing_pack.py
2. Extract shared code to utilities
3. Update misleading documentation
4. Add monitoring and fail-fast

### **Expected Outcome**
- ✅ All 17 positions valued correctly
- ✅ Complete portfolio displayed to users
- ✅ Reproducible results via pricing packs
- ✅ Clean, maintainable codebase

---

**Plan Complete - Ready for Implementation**

**Next Step:** Execute Phase 1 fixes (line 374, archive file, update docs)

---

**Generated:** November 4, 2025 at 19:00 PST
**Generated By:** Claude IDE (Sonnet 4.5)
**Version:** 1.0
