# Comprehensive Seed Strategy for DawsOS

**Date:** January 14, 2025  
**Purpose:** Define comprehensive seed strategy to enable full system functionality

---

## Executive Summary

**Problem:**
- Currency attribution requires **252 days** of historical pricing packs
- Factor analysis requires historical portfolio returns
- Risk metrics require historical portfolio values
- Current seed script only seeds FX rates, sectors, and corporate actions

**Solution:**
- Generate **300 days** of historical pricing packs (252 + 48 buffer)
- Generate prices for all securities in each pack
- Generate FX rates for all packs (already done)
- Generate portfolio daily values for historical periods
- Ensure data coherence and realistic relationships

**Estimated Time:** 8-12 hours  
**Priority:** HIGH - System cannot function without historical data

---

## Data Requirements Analysis

### 1. Currency Attribution Service

**Requirements:**
- **252 days** of historical pricing packs (default `lookback_days=252`)
- Prices for all securities in start and end packs
- FX rates for start and end packs
- Portfolio holdings with quantities

**Current Status:** ❌ **BLOCKING** - Returns zeros when no historical packs exist

**Location:** `backend/app/services/currency_attribution.py:133`

```python
start_date = end_date - timedelta(days=lookback_days)  # 252 days back
# Requires pricing pack for start_date
```

---

### 2. Risk Metrics Service

**Requirements:**
- **252 days** of historical portfolio returns
- Portfolio daily values (`portfolio_daily_values` table)
- Benchmark prices (if tracking error calculated)

**Current Status:** ⚠️ **PARTIAL** - Can query `portfolio_daily_values` but may be empty

**Location:** `backend/app/services/risk_metrics.py:414`

```python
# Queries portfolio_daily_values for 252 days
SELECT valuation_date as asof_date, total_value
FROM portfolio_daily_values
WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
```

---

### 3. Factor Analysis Service

**Requirements:**
- **252 days** of historical portfolio returns
- **252 days** of economic indicators (if factor analysis includes macro factors)
- Portfolio daily values

**Current Status:** ⚠️ **PARTIAL** - Can query but may have insufficient data

**Location:** `backend/app/services/factor_analysis.py:290`

```python
# Queries portfolio_daily_values for 252 days
SELECT valuation_date as asof_date, total_value
FROM portfolio_daily_values
WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
```

---

### 4. Metrics Service (TWR, MWR, Sharpe)

**Requirements:**
- **252 days** of historical portfolio returns
- Portfolio daily values
- Cash flows (for MWR calculation)

**Current Status:** ⚠️ **PARTIAL** - Can query but may have insufficient data

---

## Seed Strategy

### Phase 1: Historical Pricing Packs (CRITICAL)

**Objective:** Generate 300 days of historical pricing packs

**Steps:**
1. **Identify date range**
   - Start: `today - 300 days`
   - End: `today`
   - Generate packs for every trading day (exclude weekends)

2. **For each date:**
   - Create pricing pack with status `'fresh'`
   - Generate prices for all active securities
   - Generate FX rates (already done by existing seed script)
   - Link prices and FX rates to pack

3. **Price generation strategy:**
   - Start with realistic base prices (e.g., AAPL = $180, MSFT = $380)
   - Apply realistic daily variations (±0.5% to ±2%)
   - Add some trending (bull/bear market periods)
   - Ensure prices don't go negative
   - Include volume data

4. **Data coherence:**
   - Prices should trend realistically (not random)
   - Correlations between securities (e.g., tech stocks move together)
   - FX rates should move gradually (not jump 10% in a day)

**Script:** `backend/scripts/seed_historical_pricing_packs.py`

**Estimated Time:** 4-6 hours

---

### Phase 2: Portfolio Daily Values (CRITICAL)

**Objective:** Generate historical portfolio values for all portfolios

**Steps:**
1. **For each portfolio:**
   - Get all holdings (lots with `quantity_open > 0`)
   - For each historical date:
     - Calculate portfolio value = sum(quantity × price × fx_rate)
     - Store in `portfolio_daily_values` table

2. **Data generation:**
   - Query prices from historical pricing packs
   - Query FX rates from historical pricing packs
   - Calculate total value in base currency
   - Include cash balance, positions value, cash flows

3. **Ensure consistency:**
   - Portfolio values should change smoothly (not jump drastically)
   - Reflect portfolio changes (trades, dividends)
   - Match actual holdings at each date

**Script:** `backend/scripts/seed_portfolio_daily_values.py`

**Estimated Time:** 2-3 hours

---

### Phase 3: Economic Indicators (MEDIUM PRIORITY)

**Objective:** Generate historical economic indicators for factor analysis

**Steps:**
1. **Identify required indicators:**
   - Interest rates (10Y Treasury)
   - Inflation (CPI)
   - Unemployment (UNRATE)
   - Manufacturing PMI
   - GDP growth

2. **Generate data:**
   - Start with realistic base values
   - Apply realistic variations
   - Ensure economic relationships (e.g., inflation affects interest rates)

3. **Store in `economic_indicators` table:**
   - Link to pricing packs by date
   - Include source, unit, series_id

**Script:** `backend/scripts/seed_economic_indicators.py`

**Estimated Time:** 1-2 hours

**Note:** This may already exist - verify first

---

### Phase 4: Enhance Existing Seed Script (LOW PRIORITY)

**Objective:** Improve existing seed script

**Changes:**
1. **FX rates:**
   - Don't delete all FMP rates (use more specific WHERE clause)
   - Only seed rates for packs that don't have them

2. **Sector classifications:**
   - Verify table schema matches migrations
   - Use existing `securities.sector` if available

3. **Corporate actions:**
   - Generate more historical corporate actions
   - Link to historical pricing packs

**Script:** Update `backend/scripts/seed_missing_reference_data.py`

**Estimated Time:** 1 hour

---

## Implementation Plan

### Step 1: Create Historical Pricing Pack Generator

**File:** `backend/scripts/seed_historical_pricing_packs.py`

**Key Functions:**
- `generate_historical_packs(start_date, end_date)` - Generate packs for date range
- `generate_prices_for_pack(pack_id, pack_date)` - Generate prices for all securities
- `ensure_price_coherence(prices_dict)` - Ensure prices are realistic and coherent

**Price Generation Strategy:**
```python
# Base prices (realistic starting values)
BASE_PRICES = {
    'AAPL': 180.00,
    'MSFT': 380.00,
    'GOOGL': 140.00,
    'AMZN': 150.00,
    # ... more securities
}

# Daily variation (realistic market movements)
daily_variation = random.uniform(-0.02, 0.02)  # ±2% per day

# Trend (add some directionality)
trend = 0.001 if bull_market else -0.001  # 0.1% daily trend

new_price = base_price * (1 + daily_variation + trend)
```

**Estimated Time:** 4-6 hours

---

### Step 2: Create Portfolio Daily Values Generator

**File:** `backend/scripts/seed_portfolio_daily_values.py`

**Key Functions:**
- `generate_portfolio_daily_values(portfolio_id, start_date, end_date)` - Generate values for portfolio
- `calculate_portfolio_value(portfolio_id, pack_id)` - Calculate value from holdings and prices
- `ensure_value_coherence(values_dict)` - Ensure values change smoothly

**Value Calculation:**
```python
# For each date:
# 1. Get pricing pack for date
# 2. Get all holdings (lots with quantity_open > 0)
# 3. For each holding:
#    - Get price from pack
#    - Get FX rate from pack
#    - Calculate value = quantity × price × fx_rate
# 4. Sum all values = total_value
# 5. Store in portfolio_daily_values
```

**Estimated Time:** 2-3 hours

---

### Step 3: Integrate with Existing Seed Script

**File:** Update `backend/scripts/seed_missing_reference_data.py`

**Changes:**
- Add call to historical pricing pack generator
- Add call to portfolio daily values generator
- Improve FX rate seeding (don't delete all FMP rates)

**Estimated Time:** 1 hour

---

### Step 4: Create Master Seed Script

**File:** `backend/scripts/seed_all_data.py`

**Purpose:** Orchestrate all seed scripts in correct order

**Order:**
1. Historical pricing packs (needs to exist first)
2. FX rates (references pricing packs)
3. Portfolio daily values (references pricing packs and FX rates)
4. Economic indicators (references pricing packs)
5. Sector classifications (independent)
6. Corporate actions (references pricing packs)

**Estimated Time:** 30 minutes

---

## Data Quality Requirements

### 1. Price Coherence

**Requirements:**
- Prices should not jump > 10% per day (except for splits)
- Prices should trend realistically (not completely random)
- Correlations between securities should be maintained
- Volume should vary realistically

**Validation:**
- Check price changes: `abs(price[t] - price[t-1]) / price[t-1] < 0.10`
- Check price trends: moving average should show direction
- Check correlations: tech stocks should move together

---

### 2. Portfolio Value Coherence

**Requirements:**
- Portfolio values should change smoothly (no sudden jumps)
- Should reflect actual holdings at each date
- Should match sum of position values

**Validation:**
- Check value changes: `abs(value[t] - value[t-1]) / value[t-1] < 0.15`
- Verify: `sum(positions) == total_value` (within rounding)

---

### 3. FX Rate Coherence

**Requirements:**
- FX rates should move gradually (not jump 10% in a day)
- Inverse rates should be consistent: `1 / USD/CAD ≈ CAD/USD`
- Rates should be realistic (e.g., USD/CAD ≈ 1.30-1.40)

**Validation:**
- Check rate changes: `abs(rate[t] - rate[t-1]) / rate[t-1] < 0.05`
- Verify inverse rates: `USD/CAD × CAD/USD ≈ 1.0`

---

## Execution Plan

### Week 1: Critical Data (HIGH PRIORITY)

1. **Day 1-2:** Historical Pricing Packs Generator
   - Create `seed_historical_pricing_packs.py`
   - Test with 10 days of data
   - Validate price coherence

2. **Day 3:** Portfolio Daily Values Generator
   - Create `seed_portfolio_daily_values.py`
   - Test with one portfolio
   - Validate value coherence

3. **Day 4:** Integration
   - Update existing seed script
   - Create master seed script
   - Test end-to-end

4. **Day 5:** Validation
   - Run currency attribution (should work now)
   - Run risk metrics (should work now)
   - Run factor analysis (should work now)

**Total Time:** 5 days (40 hours)

---

### Week 2: Enhancement (MEDIUM PRIORITY)

1. **Day 6-7:** Economic Indicators
   - Create `seed_economic_indicators.py`
   - Test with factor analysis

2. **Day 8:** Improve Existing Seed Script
   - Fix FX rate deletion issue
   - Add more corporate actions

3. **Day 9-10:** Documentation and Testing
   - Document seed strategy
   - Create seed data validation tests
   - Add seed data quality checks

**Total Time:** 5 days (40 hours)

---

## Validation Strategy

### 1. Data Completeness

**Check:**
- All portfolios have 300 days of daily values
- All active securities have 300 days of prices
- All pricing packs have FX rates

**Query:**
```sql
-- Check portfolio daily values
SELECT portfolio_id, COUNT(*) as days
FROM portfolio_daily_values
GROUP BY portfolio_id
HAVING COUNT(*) < 300;

-- Check security prices
SELECT security_id, COUNT(*) as days
FROM prices
GROUP BY security_id
HAVING COUNT(*) < 300;
```

---

### 2. Data Coherence

**Check:**
- Price changes are reasonable
- Portfolio values change smoothly
- FX rates are consistent

**Script:** `backend/scripts/validate_seed_data.py`

---

### 3. Functional Validation

**Test:**
- Currency attribution returns non-zero values
- Risk metrics calculate correctly
- Factor analysis works
- Metrics (TWR, MWR, Sharpe) calculate correctly

**Manual Test:**
```python
# Test currency attribution
attribution = await currency_attributor.compute_attribution(
    portfolio_id="...",
    pack_id="PP_2025-01-14",
    lookback_days=252
)
assert attribution["total_return"] != 0.0
```

---

## Risk Mitigation

### 1. Data Volume

**Risk:** Generating 300 days × 100 securities × 10 portfolios = 300,000 price records

**Mitigation:**
- Use batch inserts
- Generate in chunks (e.g., 50 days at a time)
- Use database transactions
- Add progress logging

---

### 2. Performance

**Risk:** Seed script takes too long to run

**Mitigation:**
- Use async/await for concurrent operations
- Use batch inserts
- Generate data in parallel where possible
- Add timeout limits

---

### 3. Data Quality

**Risk:** Generated data is unrealistic or incoherent

**Mitigation:**
- Validate after generation
- Use realistic base values
- Apply realistic variations
- Test with small datasets first

---

## Success Criteria

### ✅ Phase 1 Complete When:

1. **300 days of historical pricing packs exist**
2. **All active securities have prices in all packs**
3. **All pricing packs have FX rates**
4. **All portfolios have 300 days of daily values**

### ✅ Phase 2 Complete When:

1. **Currency attribution returns non-zero values**
2. **Risk metrics calculate correctly**
3. **Factor analysis works**
4. **All metrics (TWR, MWR, Sharpe) calculate correctly**

---

## Next Steps

1. **Create historical pricing pack generator** (4-6 hours)
2. **Create portfolio daily values generator** (2-3 hours)
3. **Test with small dataset** (1 hour)
4. **Run full seed** (1 hour)
5. **Validate functionality** (1 hour)

**Total Estimated Time:** 9-12 hours

---

## Files to Create

1. `backend/scripts/seed_historical_pricing_packs.py` (NEW)
2. `backend/scripts/seed_portfolio_daily_values.py` (NEW)
3. `backend/scripts/seed_all_data.py` (NEW)
4. `backend/scripts/validate_seed_data.py` (NEW)
5. Update `backend/scripts/seed_missing_reference_data.py` (EXISTING)

---

## Dependencies

- Existing pricing pack structure
- Existing `portfolio_daily_values` schema
- Existing `prices` and `fx_rates` tables
- Existing `lots` table (for holdings)

---

**Status:** 📋 **PLAN READY** - Ready for implementation

