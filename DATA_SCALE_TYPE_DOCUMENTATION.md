# Data Scale & Type Reference Documentation

**Last Updated:** 2025-11-08
**Purpose:** Comprehensive guide to data scales, units, and type conversions across DawsOS
**Audience:** Developers integrating APIs, calculating metrics, or debugging scale issues

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [API Response Formats](#api-response-formats)
3. [Constants Scale Reference](#constants-scale-reference)
4. [Common Conversions](#common-conversions)
5. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
6. [Validation Rules](#validation-rules)
7. [Troubleshooting](#troubleshooting)

---

## Quick Reference

### Scale Cheat Sheet

| Data Type | Format | Example Value | Meaning | Conversion |
|-----------|--------|---------------|---------|------------|
| **FRED Percentages** | Whole number | 4.5 | 4.5% | `÷ 100 → 0.045` |
| **FMP Ratios** | Decimal | 1.72 | 172% | Already decimal |
| **FMP Yields** | Decimal | 0.0045 | 0.45% | Already decimal |
| **Basis Points** | Integer | 100 | 1% | `÷ 10000 → 0.01` |
| **Confidence Levels** | Decimal | 0.95 | 95% | `× 100 → 95` |
| **Unix Timestamps** | Milliseconds | 1699364400000 | Nov 7, 2023 | `÷ 1000 → seconds` |
| **Money** | Dollars | 1234.56 | $1,234.56 | No conversion |
| **Trading Days** | Integer | 252 | 1 year | 252 trading days = 1 year |

### Critical Rules

1. **FRED API**: Always returns percentages as whole numbers - MUST divide by 100
2. **FMP API**: Returns ratios as decimals (1.72 = 172%) - DO NOT divide by 100
3. **Constants**: All percentage-based constants use decimal format (0.95, not 95)
4. **Display**: Convert to percentage only at UI boundary using f-strings: `f"{value:.2%}"`

---

## API Response Formats

### FRED (Federal Reserve Economic Data)

**Official Documentation**: https://fred.stlouisfed.org/docs/api/fred/

**Response Format**: Percentages as whole numbers

```json
{
  "observations": [{
    "date": "2025-11-07",
    "value": "4.08"  // ← This is 4.08%, not 0.0408
  }]
}
```

**Series Requiring Conversion**:
- `DGS10` (10-Year Treasury): 4.08 → 0.0408 (÷100)
- `DGS2` (2-Year Treasury): 3.92 → 0.0392 (÷100)
- `UNRATE` (Unemployment): 3.7 → 0.037 (÷100)
- `T10Y2Y` (10Y-2Y Spread): 0.50 → 0.005 (÷100)
- `DFF` (Federal Funds Rate): 5.33 → 0.0533 (÷100)

**Series NOT Requiring Conversion**:
- `CPIAUCSL` (CPI Index): 324.368 → 324.368 (keep as-is, index value)
- `DCOILWTICO` (Oil Price): 75.43 → 75.43 (keep as-is, $/barrel)
- `VIXCLS` (VIX): 13.45 → 13.45 (keep as-is, volatility index)

**Implementation**:
```python
# File: backend/app/services/macro_data_helpers.py
async def get_risk_free_rate(as_of_date: Optional[date] = None) -> Decimal:
    dgs10 = await get_latest_indicator_value("DGS10", as_of_date)
    if dgs10 is not None:
        return dgs10 / Decimal("100")  # ← CRITICAL: Convert percent to decimal
    return Decimal("0.03")  # Fallback
```

**Systematic Handling**:
See `backend/app/services/fred_transformation.py` - Centralized transformation service with comprehensive documentation in `backend/docs/FRED_SCALING_DOCUMENTATION.md`.

---

### FMP (Financial Modeling Prep)

**Official Documentation**: https://site.financialmodelingprep.com/developer/docs/

**Response Format**: Ratios as decimals, NOT percentages

**Financial Ratios** (`/v3/ratios`):
```json
{
  "returnOnEquity": 1.72,         // ← 172% ROE (decimal format, NOT percentage)
  "returnOnAssets": 0.28,         // ← 28% ROA
  "netProfitMargin": 0.25,        // ← 25% margin
  "grossProfitMargin": 0.43,      // ← 43% margin
  "dividendYield": 0.0045,        // ← 0.45% yield (note: very small decimal)
  "currentRatio": 1.07,           // ← 1.07:1 (pure ratio, not percentage)
  "debtToEquity": 1.97,           // ← 1.97:1 (pure ratio)
  "priceToEarningsRatio": 31.5    // ← 31.5x (multiple, not percentage)
}
```

**CRITICAL**:
- `returnOnEquity: 1.72` means **172% ROE**, not 1.72%
- DO NOT divide by 100 - already in decimal format
- High ROE (>1.0 = >100%) is rare but valid for exceptional companies

**Implementation**:
```python
# File: backend/app/agents/data_harvester.py (line 1122)
# Values used directly without conversion - CORRECT
roe = ratio_data["returnOnEquity"]  # Already decimal (1.72 = 172%)
margin = ratio_data["netProfitMargin"]  # Already decimal (0.25 = 25%)

# For display:
print(f"ROE: {roe:.2%}")  # → "ROE: 172.00%"
print(f"Margin: {margin:.2%}")  # → "Margin: 25.00%"
```

**Quote Data** (`/v3/quote`):
```json
{
  "symbol": "AAPL",
  "price": 175.43,             // ← Dollars (no conversion)
  "volume": 58923456,          // ← Share count (integer)
  "changesPercentage": 1.24    // ← 1.24% change (percentage format)
}
```

**Note**: `changesPercentage` is returned as percentage (1.24 = 1.24%), not decimal.

---

### Polygon.io

**Response Format**: Standard financial data

**Aggregates** (`/v2/aggs/ticker/{symbol}/range`):
```json
{
  "results": [{
    "o": 175.12,    // ← Open price (dollars)
    "h": 176.45,    // ← High price (dollars)
    "l": 174.89,    // ← Low price (dollars)
    "c": 175.43,    // ← Close price (dollars)
    "v": 58923456,  // ← Volume (share count)
    "t": 1699364400000  // ← Timestamp (Unix milliseconds)
  }]
}
```

**Timestamp Conversion**:
```python
# File: backend/app/integrations/polygon_provider.py (line 162)
from datetime import datetime
dt = datetime.fromtimestamp(bar["t"] / 1000)  # ← Divide by 1000 to convert milliseconds to seconds
```

---

## Constants Scale Reference

### Percentage-Based Constants (Decimal Format)

All percentage constants use **decimal format** (0-1 scale):

```python
# File: backend/app/core/constants/risk.py
CONFIDENCE_LEVEL_95 = 0.95  # 95% confidence, stored as 0.95 (not 95)

# File: backend/app/core/constants/scenarios.py
MONEY_PRINTING_USD_PCT = -0.12     # -12% USD shock
MONEY_PRINTING_EQUITY_PCT = 0.05    # +5% equity shock
```

**Usage**:
```python
# Calculation (use directly):
var_95 = np.percentile(returns, (1 - CONFIDENCE_LEVEL_95) * 100)

# Display (convert to percentage):
print(f"Confidence: {CONFIDENCE_LEVEL_95:.0%}")  # → "Confidence: 95%"
```

### Basis Points Constants

Basis points stored as raw BPS value:

```python
# File: backend/app/core/constants/scenarios.py
MONEY_PRINTING_REAL_RATES_BPS = 25.0    # 25 basis points
MONEY_PRINTING_INFLATION_BPS = 150.0    # 150 basis points (1.5%)
RATES_UP_100BP = 100.0                   # 100 basis points (1%)
```

**Conversion**:
```python
# File: backend/app/services/scenarios.py (line 542)
shock_decimal = Decimal(str(shock.real_rates_bps / 10000))  # 100bp → 0.01 (1%)
```

### Trading Days Constants

```python
# File: backend/app/core/constants/financial.py
TRADING_DAYS_PER_YEAR = 252  # Industry standard (252 trading days = 1 calendar year)

# File: backend/app/core/constants/macro.py
DEFAULT_MACRO_LOOKBACK_DAYS = 252  # 1 year of trading data
```

**Note**: 252 is universally understood as "1 trading year" (excludes weekends + holidays).

---

## Common Conversions

### Percentage Conversions

```python
# Percentage (whole number) → Decimal
def percent_to_decimal(percent: float) -> float:
    """4.5 → 0.045"""
    return percent / 100.0

# Decimal → Percentage (whole number)
def decimal_to_percent(decimal: float) -> float:
    """0.045 → 4.5"""
    return decimal * 100.0

# Display formatting (preferred)
value = 0.045
print(f"{value:.2%}")  # → "4.50%"
```

### Basis Points Conversions

```python
# Basis Points → Decimal
def bps_to_decimal(bps: float) -> float:
    """100bp → 0.01 (1%)"""
    return bps / 10000.0

# Decimal → Basis Points
def decimal_to_bps(decimal: float) -> float:
    """0.01 → 100bp"""
    return decimal * 10000.0

# Display formatting
bps = 150
decimal = bps / 10000  # 0.015 (1.5%)
print(f"{bps:.0f}bp ({decimal:.2%})")  # → "150bp (1.50%)"
```

### Timestamp Conversions

```python
# Unix Milliseconds → datetime
from datetime import datetime
timestamp_ms = 1699364400000
dt = datetime.fromtimestamp(timestamp_ms / 1000)

# Unix Seconds → datetime (already in seconds)
timestamp_s = 1699364400
dt = datetime.fromtimestamp(timestamp_s)
```

---

## Anti-Patterns to Avoid

### ❌ BAD: Hardcoded Magic Numbers

```python
# DON'T DO THIS
risk_free = dgs10 / 100  # Magic number!
shock_value = bps / 10000  # What does 10000 mean?
```

### ✅ GOOD: Named Conversions

```python
# DO THIS
risk_free = percent_to_decimal(dgs10)  # Clear intent

# OR use constants
from app.core.utils.conversions import PERCENT_TO_DECIMAL_DIVISOR
risk_free = dgs10 / PERCENT_TO_DECIMAL_DIVISOR
```

### ❌ BAD: Inconsistent Display Formatting

```python
# DON'T DO THIS
print(f"Confidence: {confidence * 100}%")  # Manual conversion
print(f"Margin: {margin}")  # Inconsistent (no %)
```

### ✅ GOOD: Consistent f-string Formatting

```python
# DO THIS
print(f"Confidence: {confidence:.0%}")  # "95%"
print(f"Margin: {margin:.2%}")  # "25.00%"
```

### ❌ BAD: Mixing Scales

```python
# DON'T DO THIS
CONFIDENCE_95_PERCENT = 95  # Percentage format
CONFIDENCE_99_DECIMAL = 0.99  # Decimal format
# ← Inconsistent! Pick one scale
```

### ✅ GOOD: Consistent Scale

```python
# DO THIS - All decimals
CONFIDENCE_LEVEL_95 = 0.95
CONFIDENCE_LEVEL_99 = 0.99
```

---

## Validation Rules

### FRED Data Validation

```python
# After fetching from FRED
if series_id in ["DGS10", "DGS2", "UNRATE", "DFF"]:
    # These should be percentages (0-20 range reasonable)
    assert 0 <= value <= 20, f"{series_id} value {value} outside expected range"

# After conversion
decimal_value = value / 100.0
assert 0 <= decimal_value <= 0.20, f"Converted value {decimal_value} unreasonable"
```

### FMP Ratio Validation

```python
# Financial ratios should be decimals (not percentages)
roe = ratio_data["returnOnEquity"]
assert 0.01 <= roe <= 10.0, f"ROE {roe} outside expected range (1%-1000%)"

margin = ratio_data["netProfitMargin"]
assert -0.5 <= margin <= 1.0, f"Margin {margin} outside expected range (-50%-100%)"

div_yield = ratio_data.get("dividendYield", 0)
assert 0 <= div_yield <= 0.20, f"Dividend yield {div_yield} outside expected range (0%-20%)"
```

### Database Storage Validation

```sql
-- File: backend/db/schema/macro_indicators.sql
-- Validate percentages stored in database
CREATE OR REPLACE FUNCTION validate_indicator_value()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.units = 'Percent' AND (NEW.value < -100 OR NEW.value > 1000) THEN
        RAISE WARNING 'Percentage value % outside expected range for %',
            NEW.value, NEW.indicator_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## Frontend Data Handling

### formatPercentage() Function

**Location:** [frontend/utils.js:55-58](frontend/utils.js#L55-L58)

```javascript
Utils.formatPercentage = function(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) return '-';
    return (value * 100).toFixed(decimals) + '%';  // Expects decimal input
};
```

**Expected Input:** Decimal (e.g., 0.145)
**Processing:** Multiplies by 100
**Output:** String with % (e.g., "14.50%")

### Critical UI Rule

✅ **DO**: Pass decimals directly to formatPercentage
```javascript
// Backend returns: 0.145 (14.5%)
formatPercentage(data.ytd_return)  // ✅ "14.50%"
```

❌ **DON'T**: Divide by 100 before calling formatPercentage
```javascript
// Backend returns: 0.145 (14.5%)
formatPercentage(data.ytd_return / 100)  // ❌ "0.14%" (WRONG - 100x too small)
```

### Backend Returns Decimals

**All backend APIs return decimals:**
- Performance metrics (TWR, volatility): `0.145` = 14.5%
- Weights/allocations: `0.25` = 25%
- Change percentages: `0.0235` = 2.35%
- Macro indicators: `0.0408` = 4.08%

**Source:** [backend/app/services/metrics.py:87-94](backend/app/services/metrics.py#L87-L94)

```python
async def compute_twr(...) -> Dict:
    """
    Returns:
        - twr: Total return over period (decimal, e.g., 0.15 = 15%)
        - ann_twr: Annualized return (decimal)
        - vol: Annualized volatility (decimal)
    """
```

### UI Scaling Bugs Fixed

**Date:** 2025-11-08

Fixed 8 critical double-conversion bugs where frontend incorrectly divided by 100:
- Portfolio overview (change_pct, ytd_return)
- Holdings table (weight, return_pct)
- Transactions page (totalPnLPct)
- Scenarios page (impactPct)
- Optimizer page (turnoverPct, teImpact, concentration metrics)

**Details:** [UI_DATA_SCALING_CRITICAL_ISSUES.md](UI_DATA_SCALING_CRITICAL_ISSUES.md)

---

## Troubleshooting

### Problem: Results are 100x too large/small

**Symptoms**:
- Sharpe ratio of 95 instead of 0.95
- Returns of 450% instead of 4.5%

**Diagnosis**:
```python
# Check if value is percentage vs decimal
if value > 10:
    print(f"WARNING: Value {value} looks like percentage, not decimal")
```

**Solution**: Check API source
- FRED? Divide by 100
- FMP? Already decimal, don't divide
- Constants? Check naming convention (ends in _PCT or _BPS?)

### Problem: VaR calculation returns None

**Symptoms**: `np.percentile()` fails with error

**Diagnosis**:
```python
confidence = 95  # Wrong! Should be 0.95
percentile = (1 - confidence) * 100  # -9400 (invalid!)
```

**Solution**: Use decimal format
```python
confidence = 0.95  # Correct
percentile = (1 - confidence) * 100  # 5 (correct)
```

### Problem: Basis points conversion wrong

**Symptoms**: 100bp shock moves portfolio by 100% instead of 1%

**Diagnosis**:
```python
shock = bps / 100  # WRONG! Treating as percentage
```

**Solution**: Divide by 10000, not 100
```python
shock = bps / 10000  # 100bp → 0.01 (1%)
```

---

## Migration Guide: cycles.py Hardcoded Scaling

### Problem (CRITICAL)

`cycles.py` has hardcoded scaling logic that conflicts with `FREDTransformationService`:

```python
# File: backend/app/services/cycles.py (lines 729-745)
# ❌ DUPLICATE/CONFLICTING LOGIC
if code_key == "inflation":
    db_indicators[code_key] = raw_value / 10000.0  # Why 10000? Should be 100
elif code_key == "gdp_growth":
    db_indicators[code_key] = raw_value / 100.0
```

### Solution

Use centralized transformation service:

```python
# DELETE hardcoded scaling (lines 729-745)

# ADD proper transformation
from app.services.fred_transformation import get_transformation_service

transformation_service = get_transformation_service()

for row in rows:
    db_name = row["indicator_id"]
    if db_name in name_mapping:
        code_key = name_mapping[db_name]
        raw_value = float(row["value"])

        # Use centralized, documented transformation
        transformed = transformation_service.transform_fred_value(
            series_id=db_name,
            value=raw_value,
            date_str=str(row["date"]),
            historical_values=historical_data.get(db_name, [])
        )

        db_indicators[code_key] = transformed if transformed is not None else raw_value
```

---

## Summary

### Golden Rules

1. **FRED API**: Returns percentages as whole numbers - ALWAYS divide by 100
2. **FMP API**: Returns ratios as decimals - NEVER divide by 100
3. **Constants**: Store percentages as decimals (0.95, not 95)
4. **Display**: Convert only at UI boundary using f-strings (`f"{value:.2%}"`)
5. **Basis Points**: Divide by 10000 to get decimal (100bp = 0.01 = 1%)
6. **Validate**: Assert reasonable ranges after conversion
7. **Document**: Always comment conversion rationale

### Testing Checklist

- [ ] FRED data converts percentages correctly (÷100)
- [ ] FMP ratios used as-is (no conversion)
- [ ] Basis points convert to decimals (÷10000)
- [ ] Display formatting uses f-strings not manual `*100`
- [ ] Confidence levels in decimal format (0.95 not 95)
- [ ] Database units field validated
- [ ] Integration tests verify API response format

### References

- FRED API: https://fred.stlouisfed.org/docs/api/fred/
- FMP API: https://site.financialmodelingprep.com/developer/docs/
- FRED Scaling Documentation: `backend/docs/FRED_SCALING_DOCUMENTATION.md`
- Transformation Service: `backend/app/services/fred_transformation.py`
- Macro Data Helpers: `backend/app/services/macro_data_helpers.py`

---

**Document Status**: Living document - update when API formats change
**Last Verified**: 2025-11-07 with AAPL/DGS10 real data
**Maintained By**: Data Integration Team
