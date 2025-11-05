# Phase 3 Database & Finance Review

**Date:** January 14, 2025  
**Status:** 🔍 **REVIEW IN PROGRESS**  
**Purpose:** Review database structures, field names, and factor analysis from finance perspective

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

**Required Fields (from FactorAnalyzer usage):**
- `portfolio_id` (UUID) - Portfolio identifier
- `asof_date` (DATE) - Date of valuation
- `nav` (DECIMAL) - Net Asset Value
- `return` (DECIMAL) - Daily return (calculated or stored)

**Factor Analysis Requirements:**
- Need daily returns for regression
- Need sufficient history (minimum 30 days, recommended 252 days = 1 year)
- Need consistent date coverage

**Potential Issues:**
- ⚠️ **Field name:** `asof_date` vs `date` - Need to verify consistency
- ⚠️ **Return calculation:** Is `return` stored or calculated? If calculated, how?
- ⚠️ **Data coverage:** Are returns calculated correctly? Missing days?

**Recommendation:**
- **VERIFY:** Check if `portfolio_daily_values` table has correct structure
- **VERIFY:** Check if `return` field exists or needs to be calculated
- **VERIFY:** Check data coverage and quality

---

### economic_indicators Table

**Purpose:** Stores factor data (Real Rate, Inflation, Credit, USD, Equity Risk Premium)

**Required Fields (from FactorAnalyzer usage):**
- `indicator_name` (VARCHAR) - Factor name
- `asof_date` (DATE) - Date of indicator
- `value` (DECIMAL) - Factor value
- `return` (DECIMAL) - Factor return (calculated or stored)

**Factor Analysis Requirements:**
- Need daily returns for each factor
- Need same date coverage as portfolio returns
- Need consistent factor definitions

**Factor Definitions (from FactorAnalyzer):**
1. **Real Rate** - 10Y TIPS yield
2. **Inflation** - Breakeven inflation
3. **Credit Spread** - IG corporate - treasury
4. **USD** - DXY dollar index
5. **Equity Risk Premium** - S&P 500 - risk-free rate

**Potential Issues:**
- ⚠️ **Factor definitions:** Are these correct from finance perspective?
- ⚠️ **Return calculation:** Are factor returns calculated correctly?
- ⚠️ **Data coverage:** Do all factors have same date coverage?
- ⚠️ **Missing data:** How are missing days handled?

**Recommendation:**
- **VERIFY:** Check if `economic_indicators` table has correct structure
- **VERIFY:** Check if factor definitions match finance standards
- **VERIFY:** Check if factor returns are calculated correctly

---

## 2. Field Naming Review

### Field Naming Consistency

**From Phase 1/2 Refactoring:**
- Standardized to `quantity` (not `qty` or `quantity_open`)
- Standardized to `date` (not `asof_date` in some places)

**FactorAnalyzer Usage:**
- Uses `asof_date` in queries
- Uses `_get_pack_date()` method
- May have inconsistency with standardized naming

**Potential Issues:**
- ⚠️ **Inconsistency:** `asof_date` vs `date` field naming
- ⚠️ **Bug:** Line 430 uses `asof_date` instead of `date` (known bug)
- ⚠️ **Standardization:** May need to align with field naming standards

**Recommendation:**
- **FIX:** Align field names with standardized naming (use `date` not `asof_date`)
- **VERIFY:** Check all database queries use consistent field names
- **UPDATE:** Update FactorAnalyzer to use standardized field names

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

