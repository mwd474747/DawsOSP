# Currency Attribution Test & Analysis

**Date:** January 14, 2025  
**Purpose:** Test currency attribution with seeded data from both code and finance perspectives

---

## Executive Summary

**Test Status:** 🔍 **TESTING IN PROGRESS**

**Critical Bug Found:**
- ⚠️ **Weight calculation missing** - All weights are 0.0, causing all contributions to be 0.0
- ⚠️ **Contribution calculation missing** - Contributions are never calculated from weights

**Finance Perspective:**
- ✅ **Formula is correct** - Currency identity: `r_base = r_local + r_fx + (r_local × r_fx)`
- ❌ **Implementation incomplete** - Weights and contributions not calculated

---

## Code Perspective Analysis

### Data Requirements Check

**Required Data:**
1. ✅ **Pricing packs** - Start and end packs for 252-day lookback
2. ✅ **Prices** - Security prices in start and end packs
3. ✅ **FX rates** - FX rates in start and end packs
4. ✅ **Holdings** - Portfolio positions with quantities
5. ✅ **Portfolio base currency** - Base currency for attribution

**Current Status:**
- Need to verify if all data exists in database

---

### Code Flow Analysis

**Current Implementation (`currency_attribution.py`):**

```python
# Line 204-206: Compute attribution for each holding
for holding in holdings:
    attr = self._compute_holding_attribution(holding, base_ccy)
    attributions.append(attr)

# Line 218-221: Aggregate by currency (using contributions)
by_currency[ccy]["local"] += attr["local_contribution"]
by_currency[ccy]["fx"] += attr["fx_contribution"]
by_currency[ccy]["interaction"] += attr["interaction_contribution"]
by_currency[ccy]["weight"] += attr["weight"]

# Line 224-227: Aggregate totals (using contributions)
total_local = sum(a["local_contribution"] for a in attributions)
total_fx = sum(a["fx_contribution"] for a in attributions)
total_interaction = sum(a["interaction_contribution"] for a in attributions)
```

**Problem:**
- `_compute_holding_attribution` returns `weight = 0.0` (line 329)
- `_compute_holding_attribution` returns `local_contribution = 0.0` (line 340)
- `_compute_holding_attribution` returns `fx_contribution = 0.0` (line 341)
- `_compute_holding_attribution` returns `interaction_contribution = 0.0` (line 342)

**Result:**
- All contributions are 0.0
- All totals are 0.0
- Currency attribution returns zeros

---

### Bug Fix Required

**Location:** `backend/app/services/currency_attribution.py:200-227`

**Fix:**
1. Calculate total portfolio value from all positions
2. Calculate weights for each position
3. Calculate weighted contributions

**Corrected Code:**
```python
# Compute attribution for each holding
attributions = []
by_currency = {}

# First pass: Calculate all position values
total_portfolio_value = Decimal('0')
for holding in holdings:
    attr = self._compute_holding_attribution(holding, base_ccy)
    attributions.append(attr)
    total_portfolio_value += Decimal(str(attr["position_value"]))

# Second pass: Calculate weights and contributions
for i, holding in enumerate(holdings):
    attr = attributions[i]
    
    # Calculate weight
    if total_portfolio_value > 0:
        weight = float(Decimal(str(attr["position_value"])) / total_portfolio_value)
    else:
        weight = 0.0
    
    # Calculate weighted contributions
    attr["weight"] = weight
    attr["local_contribution"] = attr["local_return"] * weight
    attr["fx_contribution"] = attr["fx_return"] * weight
    attr["interaction_contribution"] = attr["interaction"] * weight
    
    # Aggregate by currency
    ccy = holding["local_ccy"]
    if ccy not in by_currency:
        by_currency[ccy] = {
            "local": 0.0,
            "fx": 0.0,
            "interaction": 0.0,
            "weight": 0.0,
        }
    
    by_currency[ccy]["local"] += attr["local_contribution"]
    by_currency[ccy]["fx"] += attr["fx_contribution"]
    by_currency[ccy]["interaction"] += attr["interaction_contribution"]
    by_currency[ccy]["weight"] += attr["weight"]
```

---

## Finance Perspective Analysis

### Currency Attribution Formula

**Mathematical Identity:**
```
r_base = (1 + r_local) × (1 + r_fx) - 1
```

**Expanded:**
```
r_base = r_local + r_fx + (r_local × r_fx)
```

**Where:**
- `r_base` = Return in portfolio base currency
- `r_local` = Return in security's local currency (price change only)
- `r_fx` = FX rate change (local currency → base currency)
- `r_local × r_fx` = Interaction term (cross-product of local and FX returns)

**Finance Theory:**
- This is the standard currency attribution formula used in institutional portfolio management
- The interaction term is typically small (< 0.01%) but must be included for accuracy
- The formula must hold to within ±1 basis point for reconciliation

---

### Portfolio-Level Attribution

**Formula:**
```
r_portfolio = Σ(w_i × r_i)
```

**Where:**
- `w_i` = Weight of position i in portfolio
- `r_i` = Return of position i

**Decomposition:**
```
r_local_portfolio = Σ(w_i × r_local_i)
r_fx_portfolio = Σ(w_i × r_fx_i)
r_interaction_portfolio = Σ(w_i × r_interaction_i)
```

**Finance Theory:**
- Portfolio return is the weighted average of position returns
- Weights must sum to 1.0 (or 100%)
- Contributions are weighted returns (return × weight)

---

### Expected Results

**For a multi-currency portfolio:**

**Example Portfolio:**
- 60% USD securities (e.g., AAPL, MSFT)
- 25% EUR securities (e.g., SAP, ASML)
- 15% CAD securities (e.g., TD.TO, RY.TO)
- Base currency: CAD

**Expected Attribution:**
- **Local return:** ~8-12% (typical equity return)
- **FX return:** ~-2% to +2% (USD/CAD and EUR/CAD movements)
- **Interaction:** ~0.01% to 0.1% (small cross-product term)
- **Total return:** Local + FX + Interaction

**Reasonable Ranges:**
- Total return: -20% to +30% (for 252-day period)
- FX return: -5% to +5% (for major currency pairs)
- Interaction: -0.5% to +0.5% (typically much smaller)

---

## Test Plan

### Step 1: Check Seeded Data

**Check:**
1. Historical pricing packs exist (300 days)
2. Prices exist for all securities in all packs
3. FX rates exist for all packs
4. Portfolio holdings exist
5. Portfolio daily values exist (optional, for validation)

**Script:**
```bash
python backend/scripts/test_currency_attribution.py
```

---

### Step 2: Test Currency Attribution

**Test:**
1. Execute currency attribution
2. Check for errors
3. Verify returns are non-zero
4. Verify currency identity holds

**Expected Output:**
- Non-zero returns (if data exists)
- Currency identity holds (within 1bp)
- Reasonable return values

---

### Step 3: Validate Finance Formulas

**Validate:**
1. Currency identity: `r_base = r_local + r_fx + (r_local × r_fx)`
2. Weights sum to ~1.0
3. Contributions are weighted returns
4. Returns are reasonable (finance perspective)

**Expected:**
- Identity holds within 1bp
- Weights sum to 1.0 (±0.01)
- Contributions = return × weight

---

## Test Execution

### Prerequisites

1. **Database connection** - `DATABASE_URL` environment variable set
2. **Seeded data** - Historical pricing packs, prices, FX rates
3. **Portfolio** - At least one portfolio with holdings

---

### Running Tests

```bash
# Test currency attribution
cd backend
python scripts/test_currency_attribution.py

# Test with specific portfolio
python scripts/test_currency_attribution.py --portfolio-id <uuid>

# Test with specific pack
python scripts/test_currency_attribution.py --pack-id PP_2025-01-14
```

---

## Expected Test Results

### ✅ Success Criteria

**Code Perspective:**
1. ✅ All data requirements met
2. ✅ Attribution executes without errors
3. ✅ Returns are non-zero (if data exists)
4. ✅ No exceptions thrown

**Finance Perspective:**
1. ✅ Currency identity holds (error < 1bp)
2. ✅ Weights sum to ~1.0
3. ✅ Returns are reasonable (-20% to +30%)
4. ✅ Contributions are weighted correctly

---

### ❌ Failure Scenarios

**Code Perspective:**
1. ❌ Missing pricing packs → Returns zeros
2. ❌ Missing prices → Returns zeros
3. ❌ Missing FX rates → Returns zeros
4. ❌ Missing holdings → Returns error

**Finance Perspective:**
1. ❌ Currency identity violated (error > 1bp) → Calculation bug
2. ❌ Weights don't sum to 1.0 → Weight calculation bug
3. ❌ Returns unreasonable (> 100%) → Data quality issue
4. ❌ Contributions not weighted → Implementation bug

---

## Next Steps

1. **Fix weight calculation bug** in `currency_attribution.py`
2. **Run test script** to verify data exists
3. **Test currency attribution** after fix
4. **Validate finance formulas** after fix

---

**Status:** 📋 **TEST PLAN READY** - Ready for execution after bug fix

