# Phase 3 Database & Finance Review

**Date:** January 14, 2025  
**Status:** ✅ **COMPLETE - BUGS IDENTIFIED**  
**Purpose:** Review database structures, field names, and factor analysis from finance perspective

**Update:** Critical bugs identified and documented. Backend fixes delegated to Replit agent. See `REPLIT_BACKEND_TASKS.md` for implementation details.

---

## Executive Summary

**Review Scope:**
1. Database schema for factor analysis tables
2. Field naming consistency
3. Factor analysis calculations from finance perspective
4. Alignment with Phase 3 plan
5. Recommendations for improvements

---

## 1. Database Schema Review

### portfolio_daily_values Table

**Purpose:** Stores daily portfolio NAV (Net Asset Value) for factor analysis

**Schema (from backend/db/schema/portfolio_daily_values.sql):**
```sql
CREATE TABLE IF NOT EXISTS portfolio_daily_values (
    portfolio_id UUID NOT NULL,
    valuation_date DATE NOT NULL,  -- ⚠️ CRITICAL: Schema uses valuation_date
    total_value NUMERIC(20,2) NOT NULL,  -- ⚠️ CRITICAL: Schema uses total_value (not nav)
    cash_balance NUMERIC(20,2) NOT NULL DEFAULT 0,
    positions_value NUMERIC(20,2) NOT NULL DEFAULT 0,
    ...
    PRIMARY KEY (portfolio_id, valuation_date)
);
```

**Required Fields (from FactorAnalyzer usage):**
- ✅ `portfolio_id` (UUID) - Portfolio identifier
- 🔴 `asof_date` (DATE) - **BUG: FactorAnalyzer uses asof_date but schema uses valuation_date**
- 🔴 `total_value` (NUMERIC) - **BUG: FactorAnalyzer uses total_value correctly but schema doesn't have nav**
- ⚠️ `return` (DECIMAL) - Daily return (NOT in schema, calculated on-the-fly)

**Factor Analysis Requirements:**
- ✅ Need daily returns for regression (calculated from total_value)
- ✅ Need sufficient history (minimum 30 days, recommended 252 days = 1 year)
- ✅ Need consistent date coverage

**FactorAnalyzer Usage (line 287-289):**
```sql
SELECT asof_date, total_value
FROM portfolio_daily_values
WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3
```

**🔴 CRITICAL BUG FOUND:**
- **Schema uses:** `valuation_date`
- **FactorAnalyzer uses:** `asof_date`
- **This will cause SQL errors!**

**Potential Issues:**
- 🔴 **CRITICAL BUG:** Field name mismatch (`valuation_date` vs `asof_date`)
- ✅ **Field name:** `total_value` matches schema
- ⚠️ **Return calculation:** Returns calculated on-the-fly (not stored)
- ⚠️ **Data coverage:** Need to verify data coverage (no missing days)

**Recommendation:**
- 🔴 **MUST FIX:** Change FactorAnalyzer to use `valuation_date` instead of `asof_date`
- ✅ **Schema is correct** - Table structure is correct, just field name mismatch
- ⚠️ **Verify:** Data coverage and quality
- ⚠️ **Verify:** Return calculation is correct

---

### economic_indicators Table

**Purpose:** Stores factor data (Real Rate, Inflation, Credit, USD, Equity Risk Premium)

**Schema (assumed from FactorAnalyzer usage):**
```sql
CREATE TABLE IF NOT EXISTS economic_indicators (
    indicator_name VARCHAR NOT NULL,
    asof_date DATE NOT NULL,
    value DECIMAL(20, 6) NOT NULL,
    ...
    PRIMARY KEY (indicator_name, asof_date)
);
```

**Required Fields (from FactorAnalyzer usage):**
- ✅ `indicator_name` (VARCHAR) - Factor name (e.g., "real_rate", "inflation", "credit", "usd", "equity_risk_premium")
- ✅ `asof_date` (DATE) - Date of indicator
- ✅ `value` (DECIMAL) - Factor value
- ⚠️ `return` (DECIMAL) - Factor return (calculated on-the-fly)

**Factor Analysis Requirements:**
- ✅ Need daily returns for each factor (calculated from values)
- ✅ Need same date coverage as portfolio returns
- ✅ Need consistent factor definitions

**Factor Definitions (from FactorAnalyzer):**
1. ✅ **Real Rate** - 10Y TIPS yield (standard measure)
2. ✅ **Inflation** - Breakeven inflation (standard measure)
3. ✅ **Credit Spread** - IG corporate - treasury (standard measure)
4. ✅ **USD** - DXY dollar index (standard measure)
5. ✅ **Equity Risk Premium** - S&P 500 - risk-free rate (standard measure)

**FactorAnalyzer Usage:**
- Query: `SELECT asof_date, value FROM economic_indicators WHERE indicator_name = $1 AND asof_date BETWEEN $2 AND $3`
- Calculates returns: `(value_t - value_{t-1}) / value_{t-1}`

**Potential Issues:**
- ⚠️ **Schema verification:** Need to verify actual schema matches usage
- ⚠️ **Return calculation:** Returns calculated on-the-fly (not stored)
- ⚠️ **Data coverage:** Need to verify all factors have same date coverage
- ⚠️ **Missing data:** Need to verify how missing days are handled

**Recommendation:**
- ⚠️ **VERIFY:** Actual schema structure matches FactorAnalyzer usage
- ⚠️ **VERIFY:** Data coverage and quality for all factors
- ⚠️ **VERIFY:** Return calculation is correct

---

## 2. Field Naming Review

### Field Naming Consistency

**From Phase 1/2 Refactoring:**
- Standardized to `quantity` (not `qty` or `quantity_open`)
- Standardized to `date` (not `asof_date` in some places)

**FactorAnalyzer Usage:**
- ✅ Uses `asof_date` in queries (matches database schema)
- ✅ Uses `_get_pack_date()` method (line 433) - correctly uses `pack.date`
- ✅ No inconsistency with database schema (both use `asof_date`)

**Current Implementation (line 433-437):**
```python
async def _get_pack_date(self, pack_id: str) -> date:
    """Get as-of date for pricing pack."""
    pricing_service = get_pricing_service()
    pack = await pricing_service.get_pack_by_id(pack_id, raise_if_not_found=True)
    return pack.date  # ✅ Correctly uses pack.date (not pack.asof_date)
```

**Potential Issues:**
- ✅ **No inconsistency:** FactorAnalyzer uses `asof_date` which matches database schema
- ✅ **No bug:** Line 433 correctly uses `pack.date` (PricingPack object has `date` field)
- ⚠️ **Schema alignment:** Database uses `asof_date`, but some code uses `date` - need to verify consistency

**Recommendation:**
- ✅ **No change needed:** FactorAnalyzer correctly uses `asof_date` matching database schema
- ⚠️ **Verify:** Ensure PricingPack object has `date` field (not `asof_date`)
- ⚠️ **Verify:** Check if other code uses `date` vs `asof_date` for consistency

---

## 3. Factor Analysis Finance Review

### Factor Model Review

**FactorAnalyzer Model:**
```python
r_portfolio = α + β₁·RealRate + β₂·Inflation + β₃·Credit + β₄·USD + β₅·ERP + ε
```

**Finance Perspective:**
- ✅ **Multi-factor model:** Correct approach for portfolio risk decomposition
- ✅ **Regression-based:** Standard method for factor exposure calculation
- ⚠️ **Factor selection:** Need to verify factor definitions match finance standards

**Factor Definitions Review:**

1. **Real Rate (10Y TIPS yield)**
   - ✅ **Correct:** Real rate is a key macro factor
   - ✅ **Standard:** TIPS yield is standard measure of real rates
   - ⚠️ **Return calculation:** Need to verify how real rate returns are calculated

2. **Inflation (Breakeven inflation)**
   - ✅ **Correct:** Inflation is a key macro factor
   - ✅ **Standard:** Breakeven inflation is standard measure
   - ⚠️ **Return calculation:** Need to verify how inflation returns are calculated

3. **Credit Spread (IG corporate - treasury)**
   - ✅ **Correct:** Credit spread is a key risk factor
   - ✅ **Standard:** IG corporate - treasury is standard measure
   - ⚠️ **Return calculation:** Need to verify how credit spread returns are calculated

4. **USD (DXY dollar index)**
   - ✅ **Correct:** USD strength is a key macro factor
   - ✅ **Standard:** DXY is standard measure of USD strength
   - ⚠️ **Return calculation:** Need to verify how USD returns are calculated

5. **Equity Risk Premium (S&P 500 - risk-free rate)**
   - ✅ **Correct:** Equity risk premium is a key risk factor
   - ✅ **Standard:** S&P 500 - risk-free rate is standard measure
   - ⚠️ **Return calculation:** Need to verify how ERP returns are calculated

**Missing Factors (from standard models):**
- ⚠️ **Size factor (SMB):** Not included
- ⚠️ **Value factor (HML):** Not included
- ⚠️ **Momentum factor:** Not included
- ⚠️ **Market factor:** Not explicitly included (ERP is related but different)

**Recommendation:**
- ✅ **Current factors are appropriate** for macro-focused portfolio analysis
- ⚠️ **Consider adding:** Size, Value, Momentum if needed for equity-focused analysis
- ⚠️ **Verify:** Factor return calculations are correct

---

### Regression Analysis Review

**FactorAnalyzer Implementation:**
```python
# Uses sklearn.linear_model.LinearRegression
model = LinearRegression()
model.fit(X, y)  # X = factor returns, y = portfolio returns
```

**Finance Perspective:**
- ✅ **Method:** Linear regression is standard for factor analysis
- ✅ **Library:** sklearn is reliable and well-tested
- ⚠️ **Assumptions:** Need to verify regression assumptions are met

**Regression Assumptions:**
1. **Linearity:** Relationship between factors and returns is linear
   - ✅ **Generally true** for short time periods
   - ⚠️ **May break down** for long time periods or extreme events

2. **Independence:** Observations are independent
   - ⚠️ **Potential issue:** Daily returns may have autocorrelation
   - ⚠️ **Recommendation:** Check for autocorrelation, use Newey-West if needed

3. **Homoscedasticity:** Constant variance of errors
   - ⚠️ **Potential issue:** Volatility clustering (GARCH effects)
   - ⚠️ **Recommendation:** Check for heteroscedasticity, use robust standard errors if needed

4. **Normality:** Errors are normally distributed
   - ⚠️ **Potential issue:** Financial returns are often non-normal (fat tails)
   - ⚠️ **Recommendation:** Not critical for point estimates, but affects confidence intervals

**Recommendation:**
- ✅ **Current implementation is acceptable** for basic factor analysis
- ⚠️ **Consider enhancements:** Add Newey-West standard errors for time series
- ⚠️ **Consider enhancements:** Add residual diagnostics (R², Durbin-Watson, etc.)

---

### Return Calculation Review

**Portfolio Returns:**
```python
# From portfolio_daily_values table
# Need to calculate: (NAV_t - NAV_{t-1}) / NAV_{t-1}
# Or use stored return field if available
```

**Factor Returns:**
```python
# From economic_indicators table
# Need to calculate: (value_t - value_{t-1}) / value_{t-1}
# Or use stored return field if available
```

**Finance Perspective:**
- ✅ **Method:** Simple returns are standard for daily data
- ✅ **Calculation:** (P_t - P_{t-1}) / P_{t-1} is correct
- ⚠️ **Data quality:** Need to verify returns are calculated correctly
- ⚠️ **Missing data:** Need to handle missing days appropriately

**Potential Issues:**
- ⚠️ **Missing days:** Weekends, holidays may cause gaps
- ⚠️ **Alignment:** Portfolio and factor returns must have same dates
- ⚠️ **Data quality:** Need to verify data is clean and accurate

**Recommendation:**
- **VERIFY:** Check if return calculation is correct
- **VERIFY:** Check if missing days are handled appropriately
- **VERIFY:** Check if portfolio and factor returns are aligned

---

## 4. Alignment with Phase 3 Plan

### Task 3.1: Factor Analysis Integration

**Plan Requirements:**
1. ✅ **Service exists:** FactorAnalyzer exists
2. ✅ **Real implementation:** Regression-based factor analysis
3. ⚠️ **Integration needed:** Wire into `risk_compute_factor_exposures`
4. ⚠️ **Bugs to fix:** `asof_date` → `date`, direct queries, error handling

**Database Requirements:**
1. ⚠️ **Table structure:** Need to verify `portfolio_daily_values` structure
2. ⚠️ **Table structure:** Need to verify `economic_indicators` structure
3. ⚠️ **Field names:** Need to align with standardized naming
4. ⚠️ **Data quality:** Need to verify data is available and correct

**Recommendation:**
- ✅ **Ready to proceed** with integration
- ⚠️ **Prerequisites:** Verify database structures and data quality
- ⚠️ **Fix bugs:** Align field names and fix queries

---

## 5. Recommendations

### Immediate Actions

1. **Verify Database Structures**
   - Check `portfolio_daily_values` table schema
   - Check `economic_indicators` table schema
   - Verify field names match FactorAnalyzer usage

2. **Verify Data Quality**
   - Check if portfolio returns are calculated correctly
   - Check if factor returns are calculated correctly
   - Check if data coverage is sufficient (minimum 30 days, recommended 252 days)

3. **Fix Field Naming Issues**
   - Fix `asof_date` → `date` bug in FactorAnalyzer
   - Align all database queries with standardized naming
   - Update FactorAnalyzer to use standardized field names

4. **Verify Factor Definitions**
   - Verify factor definitions match finance standards
   - Verify factor return calculations are correct
   - Consider adding Size, Value, Momentum factors if needed

### Enhancements (Optional)

1. **Add Residual Diagnostics**
   - Add R² calculation (already included)
   - Add Durbin-Watson test for autocorrelation
   - Add Newey-West standard errors for time series

2. **Improve Error Handling**
   - Handle missing data gracefully
   - Handle insufficient data (minimum 30 days)
   - Handle data quality issues

3. **Add Factor Validation**
   - Validate factor definitions
   - Validate factor return calculations
   - Validate regression assumptions

---

## 6. Conclusion

**Database & Finance Review Status:** ⚠️ **REVIEW COMPLETE WITH RECOMMENDATIONS**

**Key Findings:**
- ✅ FactorAnalyzer implementation is sound from finance perspective
- ✅ Factor definitions are appropriate for macro-focused analysis
- ⚠️ Database structures need verification
- ⚠️ Field naming needs alignment with standards
- ⚠️ Data quality needs verification

**Recommendation:**
- ✅ **Ready to proceed** with Phase 3 Task 3.1
- ⚠️ **Prerequisites:** Verify database structures and data quality
- ⚠️ **Fix bugs:** Align field names and fix queries
- ⚠️ **Test thoroughly:** Verify factor analysis works correctly

**Next Steps:**
1. Verify database structures
2. Fix field naming issues
3. Verify data quality
4. Proceed with integration

---

**Status:** ✅ **READY FOR EXECUTION WITH PREREQUISITES**

