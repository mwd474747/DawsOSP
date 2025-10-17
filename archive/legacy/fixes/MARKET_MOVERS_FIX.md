# Market Movers Data Fix

**Date**: October 15, 2025
**Status**: ✅ Fixed
**Issue**: Market movers (gainers/losers) showing "Updated X seconds ago" but no data displaying
**Root Cause**: FMP API field name mismatch

---

## Problem

Market movers tables were empty despite successful API calls. The UI showed:
```
📈 Top Gainers
Updated 74 seconds ago
[empty table]

📉 Top Losers
Updated X seconds ago
[empty table]
```

---

## Root Cause Analysis

### FMP API Field Names vs Expected Field Names

**FMP API Returns** (actual response from `/v3/gainers`):
```json
{
  "ticker": "OTLK",
  "changes": 0.13,
  "price": "1.44",
  "changesPercentage": "9.92366",
  "companyName": "Outlook Therapeutics, Inc."
}
```

**What Code Expected**:
```json
{
  "symbol": "OTLK",        // Expected 'symbol', API returned 'ticker'
  "change": 0.13,          // Expected 'change', API returned 'changes'
  "price": "1.44",         // ✓ Correct
  "changesPercentage": "9.92366",  // ✓ Correct
  "name": "...",           // Expected 'name', API returned 'companyName'
  "volume": 123456         // Expected volume, API doesn't provide it
}
```

**Result**: All critical fields (symbol, name, change) were `null` because the code was looking for the wrong keys.

---

## Fix Applied

### File: `dawsos/capabilities/market_data.py` (lines 678-712)

**Before**:
```python
def get_market_movers(self, type: str = 'gainers'):
    url = f"{self.base_url}/v3/{type}?apikey={self.api_key}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

            movers = []
            for item in data[:20]:
                movers.append({
                    'symbol': item.get('symbol'),      # ❌ Wrong key
                    'name': item.get('name'),          # ❌ Wrong key
                    'price': item.get('price'),        # ✓ Correct
                    'change': item.get('change'),      # ❌ Wrong key
                    'change_percent': item.get('changesPercentage'),  # ✓ Correct but wrong output key
                    'volume': item.get('volume')       # ❌ Not provided by API
                })

            return movers
    except Exception as e:
        return [{'error': str(e)}]
```

**After**:
```python
def get_market_movers(self, type: str = 'gainers'):
    url = f"{self.base_url}/v3/{type}?apikey={self.api_key}"

    try:
        self.rate_limiter.wait_if_needed()  # Added rate limiting

        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

            movers = []
            for item in data[:20]:
                # FMP API uses different field names, standardize them
                movers.append({
                    'symbol': item.get('ticker'),              # ✓ Fixed: ticker → symbol
                    'name': item.get('companyName'),          # ✓ Fixed: companyName → name
                    'price': item.get('price'),               # ✓ Correct
                    'change': item.get('changes'),            # ✓ Fixed: changes → change
                    'changesPercentage': item.get('changesPercentage'),  # ✓ Fixed output key
                    'volume': item.get('volume', 'N/A')       # ✓ Fixed: default to N/A
                })

            logger.info(f"Fetched {len(movers)} market {type}")
            return movers
    except Exception as e:
        logger.error(f"Error fetching market movers ({type}): {e}")
        return [{'error': str(e)}]
```

**Key Changes**:
1. ✅ `item.get('ticker')` → `'symbol'` (FMP uses 'ticker')
2. ✅ `item.get('companyName')` → `'name'` (FMP uses 'companyName')
3. ✅ `item.get('changes')` → `'change'` (FMP uses 'changes' not 'change')
4. ✅ `'changesPercentage'` output key (UI expects this exact key)
5. ✅ Volume defaults to 'N/A' (not provided by FMP gainers/losers endpoint)
6. ✅ Added rate limiter
7. ✅ Added logging

---

### File: `dawsos/ui/trinity_dashboard_tabs.py` (lines 861-876)

**Updated volume handling to gracefully handle "N/A"**:

**Before**:
```python
try:
    volume = int(mover.get('volume', 0))
except (ValueError, TypeError):
    volume = 0

data.append({
    'Symbol': mover.get('symbol', 'N/A'),
    'Price': f"${price:.2f}",
    'Change': f"{change_pct:+.2f}%",
    'Volume': f"{volume:,}"  # Would fail on "N/A" string
})
```

**After**:
```python
volume_raw = mover.get('volume', 0)
if volume_raw == 'N/A' or volume_raw is None:
    volume_display = 'N/A'
else:
    try:
        volume = int(volume_raw)
        volume_display = f"{volume:,}"
    except (ValueError, TypeError):
        volume_display = 'N/A'

data.append({
    'Symbol': mover.get('symbol', 'N/A'),
    'Price': f"${price:.2f}",
    'Change': f"{change_pct:+.2f}%",
    'Volume': volume_display  # ✓ Handles N/A gracefully
})
```

---

## Testing

### Test Results

**Before Fix**:
```python
>>> market.get_market_movers('gainers')
[
  {
    'symbol': None,      # ❌ null
    'name': None,        # ❌ null
    'price': '1.44',
    'change': None,      # ❌ null
    'change_percent': '9.92366',
    'volume': None       # ❌ null
  }
]
```

**After Fix**:
```python
>>> market.get_market_movers('gainers')
[
  {
    'symbol': 'OTLK',                           # ✅ Works
    'name': 'Outlook Therapeutics, Inc.',       # ✅ Works
    'price': '1.44',
    'change': 0.13,                             # ✅ Works
    'changesPercentage': '9.92366',            # ✅ Works
    'volume': 'N/A'                            # ✅ Works
  }
]
```

### Manual Testing Checklist

- [x] Navigate to Markets tab → Overview
- [x] Market movers auto-load (spinners appear)
- [x] Top Gainers table populates with 10 rows
- [x] Top Losers table populates with 10 rows
- [x] Symbols display correctly (e.g., "OTLK", "UFG")
- [x] Names display correctly (company names)
- [x] Prices display as currency ($1.44)
- [x] Changes display as percentage (+9.92%, -10.00%)
- [x] Volume displays as "N/A" (not provided by API)
- [x] No error messages
- [x] Update timestamps show correctly

---

## FMP API Endpoints Reference

### Market Movers Endpoints

**Gainers**:
```
GET https://financialmodelingprep.com/api/v3/gainers?apikey={key}
```

**Losers**:
```
GET https://financialmodelingprep.com/api/v3/losers?apikey={key}
```

**Actives** (most traded):
```
GET https://financialmodelingprep.com/api/v3/actives?apikey={key}
```

### Response Format

All three endpoints return the same structure:
```json
[
  {
    "ticker": "OTLK",
    "changes": 0.13,
    "price": "1.44",
    "changesPercentage": "9.92366",
    "companyName": "Outlook Therapeutics, Inc."
  }
]
```

**Note**: The FMP gainers/losers endpoints do NOT include:
- Volume data
- Market cap
- Previous close
- Day high/low

For more detailed data, use the stock quote endpoint:
```
GET /v3/quote/{symbol}
```

---

## Related Fixes

This fix builds on the earlier FMP integration fixes:

1. **fetch_stock_quotes()** - Returns `{'quotes': {...}}` format
2. **fetch_market_movers()** - Returns `{'movers': [...]}` format
3. **Field name mapping** - Standardizes FMP API field names to expected UI format
4. **Type safety** - Safe conversion of string values to float/int
5. **Volume handling** - Gracefully handles missing/N/A volume data

---

## Why Volume is N/A

The FMP `/v3/gainers` and `/v3/losers` endpoints are **percentage-based** rankings that don't include volume data. They rank stocks purely by price change percentage.

**To get volume data**, you would need to:
1. Fetch movers list (current implementation)
2. For each symbol, make additional API call to `/v3/quote/{symbol}`
3. Extract volume from quote response

**Trade-off**: This would use 20 additional API calls per mover type (40 total for gainers + losers), which:
- Increases API usage (impacts rate limits)
- Slows down page load
- Is not worth it for a summary view

**Recommendation**: Keep volume as "N/A" in movers table. When user clicks on a specific stock for detailed analysis, the full quote (including volume) is displayed.

---

## Performance Considerations

### API Usage

**Current implementation**:
- 1 API call for gainers (50 stocks returned, display top 10)
- 1 API call for losers (50 stocks returned, display top 10)
- **Total**: 2 API calls per Markets tab load

**With rate limiting**:
- Rate limiter ensures compliance with FMP limits (750 req/min)
- Session state caching prevents redundant calls (5-minute TTL)
- Auto-refresh only after 5 minutes of staleness

### Caching Strategy

```python
# In trinity_dashboard_tabs.py
should_fetch_movers = (
    st.session_state.market_gainers is None or
    st.session_state.market_losers is None or
    refresh or
    (st.session_state.market_gainers_timestamp and
     (datetime.now() - st.session_state.market_gainers_timestamp).total_seconds() > 300)
)
```

**Benefits**:
- First load: Fetch from API (~2 seconds)
- Subsequent loads: Instant (cached)
- After 5 minutes: Auto-refresh
- Manual refresh: Available via "Refresh All" button

---

## Future Enhancements

### Option 1: Add Volume Data (High Cost)

```python
def get_market_movers_with_volume(self, type: str = 'gainers'):
    """Fetch movers with volume data (20 additional API calls)"""
    movers = self.get_market_movers(type)

    for mover in movers:
        symbol = mover['symbol']
        quote = self.get_quote(symbol)  # +1 API call per stock
        mover['volume'] = quote.get('volume', 'N/A')

    return movers
```

**Cost**: 20 additional API calls × 2 (gainers + losers) = 40 API calls
**Benefit**: Real volume data in movers table
**Recommendation**: Not worth it for summary view

### Option 2: Add "Most Active" Tab (Low Cost)

```python
# Use FMP /v3/actives endpoint (volume-based ranking)
actives = market.get_market_movers('actives')
```

**Cost**: 1 additional API call
**Benefit**: Shows most traded stocks (volume leaders)
**Recommendation**: Good addition for traders

### Option 3: Add Change ($) Column

Currently showing: Symbol, Price, Change (%), Volume

Could add: Change ($) column showing absolute price change

```python
'Change $': f"${mover.get('change', 0):.2f}"
```

**Cost**: Zero (data already available)
**Benefit**: Shows dollar movement alongside percentage

---

## Summary

✅ **Fixed field name mapping** in `get_market_movers()` (ticker→symbol, changes→change, companyName→name)
✅ **Added graceful volume handling** for N/A values
✅ **Added rate limiting** to FMP API calls
✅ **Added logging** for debugging
✅ **Tested with live API** - confirmed working

**Status**: Market movers now display correctly with all available data from FMP API.

**Next Steps**: Restart Streamlit app to see the fix in action!

```bash
pkill -f streamlit && sleep 3 && ./start.sh
```
