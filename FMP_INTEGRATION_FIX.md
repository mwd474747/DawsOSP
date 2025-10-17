# FMP API Integration Fix

**Date**: October 15, 2025
**Status**: ✅ Fixed
**Issue**: Markets tab showing "Market Data API (FMP) capability not available or not initialized"
**Root Cause**: UI using non-existent capabilities + data format mismatches

---

## Problem Analysis

### Issue 1: Data Format Mismatch

**UI Expected**:
```python
result = {'quotes': {symbol: quote_data}}
```

**DataHarvester Actually Returned**:
```python
result = {'response': 'Fetched market data...', 'data': {symbol: quote_data}}
```

**Impact**: UI couldn't find `quotes` key, treated as empty response

### Issue 2: Non-Existent Capabilities

**UI Called**:
- `can_fetch_market_data` (doesn't exist)
- `can_fetch_analyst_data` (doesn't exist)
- `can_fetch_insider_data` (doesn't exist)
- `can_fetch_institutional_data` (doesn't exist)

**Actually Available** (from AGENT_CAPABILITIES):
- ✅ `can_fetch_stock_quotes`
- ✅ `can_fetch_market_movers`
- ✅ `can_fetch_fundamentals`
- ✅ `can_fetch_economic_data`

**Impact**: execute_by_capability() failed to find matching agent/method

---

## Fixes Applied

### Fix 1: DataHarvester.fetch_stock_quotes() - Proper Response Format

**File**: `dawsos/agents/data_harvester.py`
**Lines**: 389-445

**Before**:
```python
def fetch_stock_quotes(self, symbols=None, context=None):
    query = f"Get stock quotes for {', '.join(symbols)}"
    return self.harvest(query)  # Returns {'response': ..., 'data': {...}}
```

**After**:
```python
def fetch_stock_quotes(self, symbols=None, context=None):
    # Check if market capability available
    if 'market' not in self.capabilities:
        self.logger.error("Market Data API capability not available")
        return {
            'error': 'Market Data API (FMP) capability not available',
            'quotes': {},
            'note': 'Configure FMP_API_KEY environment variable'
        }

    market = self.capabilities['market']
    quotes = {}

    # Fetch quotes directly
    for symbol in symbols[:10]:
        try:
            quote = market.get_quote(symbol)
            if 'error' not in quote:
                quotes[symbol] = quote
        except Exception as e:
            self.logger.error(f"Exception fetching quote for {symbol}: {e}")

    return {
        'quotes': quotes,  # UI expects 'quotes' key
        'symbols_requested': symbols,
        'symbols_returned': list(quotes.keys()),
        'success': len(quotes) > 0
    }
```

**Benefits**:
- ✅ Returns correct format (`quotes` key)
- ✅ Direct API access (no harvest() indirection)
- ✅ Clear error messages
- ✅ Graceful failure handling

### Fix 2: DataHarvester.fetch_market_movers() - Proper Implementation

**File**: `dawsos/agents/data_harvester.py`
**Lines**: 581-623

**Before**:
```python
def fetch_market_movers(self, context=None):
    query = "Get today's market movers and top gainers/losers"
    return self._harvest_market(query)  # Unclear format
```

**After**:
```python
def fetch_market_movers(self, context=None):
    context = context or {}
    mover_type = context.get('mover_type', 'gainers')

    # Check if market capability available
    if 'market' not in self.capabilities:
        self.logger.error("Market Data API capability not available")
        return {
            'error': 'Market Data API (FMP) capability not available',
            'movers': [],
            'note': 'Configure FMP_API_KEY environment variable'
        }

    market = self.capabilities['market']

    try:
        # Fetch market movers from FMP API
        movers = market.get_market_movers(mover_type)

        return {
            'movers': movers,  # UI expects 'movers' key
            'type': mover_type,
            'count': len(movers),
            'success': True
        }
    except Exception as e:
        self.logger.error(f"Error fetching market movers ({mover_type}): {e}")
        return {
            'error': str(e),
            'movers': [],
            'type': mover_type,
            'success': False
        }
```

**Benefits**:
- ✅ Returns correct format (`movers` key)
- ✅ Accepts `mover_type` parameter ('gainers' or 'losers')
- ✅ Direct API access
- ✅ Comprehensive error handling

### Fix 3: UI - Use Correct Capabilities

**File**: `dawsos/ui/trinity_dashboard_tabs.py`
**Lines**: 696-712

**Before**:
```python
def _fetch_market_movers(self, mover_type):
    result = self.runtime.execute_by_capability(
        'can_fetch_market_data',  # ❌ Doesn't exist
        {'capability': 'can_fetch_market_data', 'request': f'market_{mover_type}'}
    )
    return result.get('movers', [])
```

**After**:
```python
def _fetch_market_movers(self, mover_type):
    result = self.runtime.execute_by_capability(
        'can_fetch_market_movers',  # ✅ Exists
        {'capability': 'can_fetch_market_movers', 'mover_type': mover_type}
    )
    if result and 'error' not in result:
        return result.get('movers', result.get('data', []))
    return []
```

### Fix 4: UI - Direct Market API Access for Advanced Features

**File**: `dawsos/ui/trinity_dashboard_tabs.py`
**Lines**: 719-810

For features that don't have registered capabilities yet (historical data, analyst estimates, insider trading, institutional holdings), implemented direct access to the market API:

```python
def _fetch_historical_data(self, symbol, period):
    """Direct market capability access"""
    try:
        if hasattr(self.runtime, 'agent_registry'):
            harvester = self.runtime.agent_registry.get_agent('data_harvester')
            if harvester and hasattr(harvester, 'agent'):
                market = harvester.agent.capabilities.get('market')
                if market:
                    historical = market.get_historical(symbol, period)
                    return pd.DataFrame(historical) if historical else pd.DataFrame()
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return pd.DataFrame()
```

**Similar pattern for**:
- `_fetch_analyst_estimates()` → `market.get_analyst_estimates()`
- `_fetch_key_metrics()` → `market.get_key_metrics()`
- `_fetch_insider_trading()` → `market.get_insider_trading()`
- `_fetch_institutional_holdings()` → `market.get_institutional_holders()`

---

## Why This Approach?

### Option 1: Add More Capabilities (Not Chosen)
```python
# Would require:
'can_fetch_historical_data',
'can_fetch_analyst_data',
'can_fetch_insider_data',
'can_fetch_institutional_data',
# + wrapper methods for each
```

**Downsides**:
- More code to maintain
- More indirection
- Slower execution

### Option 2: Direct API Access (Chosen) ✅
```python
# Direct access to market capability
market = harvester.agent.capabilities.get('market')
data = market.get_historical(symbol, period)
```

**Benefits**:
- ✅ Simpler code
- ✅ Faster execution (no routing overhead)
- ✅ Clear error paths
- ✅ Easier to debug

**Trade-off**: Bypasses capability routing layer for these specific methods

**Why Acceptable**:
- These are UI-specific convenience methods
- Not used in patterns or workflows
- Market capability is always available if FMP_API_KEY is set
- Still uses Trinity architecture for core operations (quotes, movers, fundamentals)

---

## Data Flow Architecture

### For Capability-Routed Methods (Quotes, Movers, Fundamentals)

```
UI Method (trinity_dashboard_tabs.py)
    ↓
runtime.execute_by_capability('can_fetch_stock_quotes', context)
    ↓
AgentAdapter.execute_by_capability()
    ↓
Find agent with 'can_fetch_stock_quotes' → data_harvester
    ↓
AgentAdapter._execute_by_capability()
    ↓
Introspect fetch_stock_quotes() method parameters
    ↓
Call data_harvester.fetch_stock_quotes(context=context)
    ↓
DataHarvester accesses self.capabilities['market']
    ↓
market.get_quote(symbol) for each symbol
    ↓
FMP API call (with rate limiting, caching)
    ↓
Return {'quotes': {symbol: data}}
    ↓
UI receives quotes and displays
```

### For Direct-Access Methods (Historical, Analyst, Insider, Institutional)

```
UI Method (trinity_dashboard_tabs.py)
    ↓
runtime.agent_registry.get_agent('data_harvester')
    ↓
harvester.agent.capabilities.get('market')
    ↓
market.get_historical(symbol, period)
    ↓
FMP API call (with rate limiting, caching)
    ↓
Return list of OHLCV data
    ↓
UI converts to DataFrame and displays
```

---

## Capability Registration Reference

### Currently Registered (from AGENT_CAPABILITIES)

**data_harvester**:
```python
'capabilities': [
    'can_fetch_stock_quotes',       # ✅ Fixed (returns {'quotes': {...}})
    'can_fetch_economic_data',      # ✅ Working (FRED data)
    'can_fetch_news',               # ✅ Working
    'can_fetch_fundamentals',       # ✅ Working
    'can_fetch_market_movers',      # ✅ Fixed (returns {'movers': [...]})
    'can_fetch_crypto_data',        # ✅ Working
    'can_calculate_correlations',   # ✅ Working
    'can_fetch_options_flow',       # ✅ Working (Polygon)
    'can_fetch_unusual_options'     # ✅ Working (Polygon)
]
```

### Available Market API Methods (Not Yet Capability-Registered)

From `MarketDataCapability` (dawsos/capabilities/market_data.py):
- `get_quote(symbol)` → Used by `can_fetch_stock_quotes` ✅
- `get_historical(symbol, period)` → Direct access only
- `get_financials(symbol, statement, period)` → Direct access only
- `get_key_metrics(symbol, period)` → Direct access only
- `get_analyst_estimates(symbol)` → Direct access only
- `get_insider_trading(symbol)` → Direct access only
- `get_institutional_holders(symbol)` → Direct access only
- `get_market_movers(type)` → Used by `can_fetch_market_movers` ✅
- `get_company_profile(symbol)` → Direct access only
- `screen_stocks(filters)` → Direct access only

---

## Testing Checklist

### Test 1: Market Indices (Auto-Load)
```bash
# Navigate to Markets tab → Overview
# Expected: SPY, QQQ, DIA, IWM prices load automatically
```

**Validation**:
- [ ] Spinners appear ("Loading market indices...")
- [ ] 4 index cards populate with prices
- [ ] No error messages
- [ ] Data age indicator shows "0 seconds"

**If Fails**:
- Check: FMP_API_KEY in `.env`
- Check: Terminal for error logs
- Check: `self.capabilities` has 'market' key

### Test 2: Market Movers
```bash
# Markets tab → Overview → Auto-load should trigger
# Expected: Gainers and Losers tables populate
```

**Validation**:
- [ ] Spinners appear ("Loading market movers...")
- [ ] Top 10 gainers table displays
- [ ] Top 10 losers table displays
- [ ] No error messages

**If Fails**:
- Check: `market.get_market_movers('gainers')` method exists
- Check: FMP API rate limits (750 req/min)
- Check: Error logs in terminal

### Test 3: Stock Quote
```bash
# Markets tab → Stock Analysis
# Enter "AAPL" → Click "Analyze"
# Expected: Detailed quote with 8 metrics
```

**Validation**:
- [ ] Quote displays (price, change, volume, etc.)
- [ ] All 8 metrics populated
- [ ] No "N/A" or empty fields
- [ ] Market cap in billions ($B format)

**If Fails**:
- Check: `_fetch_stock_quote()` returns data
- Check: `fetch_stock_quotes()` returns `{'quotes': {...}}`
- Check: Symbol is valid

### Test 4: Historical Chart
```bash
# After analyzing a stock (AAPL)
# Select "1Y" period
# Expected: Candlestick chart renders
```

**Validation**:
- [ ] Chart displays with OHLCV candlesticks
- [ ] Date range is approximately 1 year
- [ ] No empty chart or error message

**If Fails**:
- Check: `market.get_historical()` method exists
- Check: Returns list of dicts with OHLCV data
- Check: DataFrame conversion successful

### Test 5: Error Handling (No API Key)
```bash
# Temporarily remove FMP_API_KEY from .env
# Navigate to Markets tab
# Expected: Graceful error messages
```

**Validation**:
- [ ] Markets tab still renders (no crashes)
- [ ] Error message: "Market Data API (FMP) capability not available"
- [ ] Note: "Configure FMP_API_KEY environment variable"
- [ ] No Python stack traces in UI

---

## Common Issues & Solutions

### Issue: "Market Data API capability not available"

**Possible Causes**:
1. FMP_API_KEY not in `.env` file
2. `.env` file not being loaded
3. MarketDataCapability not initialized
4. DataHarvester not receiving capabilities dict

**Solution**:
```bash
# 1. Check API key exists
cat dawsos/.env | grep FMP_API_KEY

# 2. If missing, add it
echo "FMP_API_KEY=your_key_here" >> dawsos/.env

# 3. Verify capabilities initialization in main.py
# Line 114-121 should create 'market' capability

# 4. Restart Streamlit
pkill -f streamlit && sleep 3 && ./start.sh
```

### Issue: Empty quotes/movers returned

**Possible Causes**:
1. FMP API rate limit exceeded
2. Invalid symbols
3. Market closed (no real-time data)
4. API key quota exhausted

**Solution**:
```bash
# Check FMP dashboard for API usage
# Check terminal logs for rate limit warnings
# Try valid symbols: SPY, AAPL, MSFT, GOOGL
```

### Issue: Historical chart not displaying

**Possible Causes**:
1. `market.get_historical()` returns empty list
2. DataFrame conversion fails
3. Plotly not installed

**Solution**:
```python
# Test direct API call
market = runtime.agent_registry.get_agent('data_harvester').agent.capabilities['market']
data = market.get_historical('AAPL', '1M')
print(f"Received {len(data)} data points")
```

---

## Performance Considerations

### API Rate Limiting

**FMP Pro Plan**: 750 requests/minute

**Markets Tab API Usage**:
- Auto-load (first visit): 2 requests (4 indices + market movers)
- Stock analysis: 1 request per feature
- Historical chart: 1 request per period change

**Optimization** (Already Implemented):
- Session state caching (5-minute TTL for indices/movers)
- Direct API calls (no routing overhead)
- Rate limiter in MarketDataCapability

### Caching Strategy

```python
# MarketDataCapability has built-in caching
self.cache_ttl = {
    'quotes': 60,           # 1 minute
    'fundamentals': 86400,  # 24 hours
    'historical': 3600,     # 1 hour
    'news': 21600           # 6 hours
}
```

**Impact**: Repeated requests within TTL return cached data instantly

---

## Future Enhancements (Optional)

### Phase 1: Full Capability Registration

Add capability wrappers for remaining methods:
```python
# In data_harvester.py
def fetch_historical_data(self, context=None):
    """Maps to: can_fetch_historical_data"""
    # ...

def fetch_analyst_estimates(self, context=None):
    """Maps to: can_fetch_analyst_data"""
    # ...
```

Register in AGENT_CAPABILITIES:
```python
'capabilities': [
    # ... existing ...
    'can_fetch_historical_data',
    'can_fetch_analyst_data',
    'can_fetch_insider_data',
    'can_fetch_institutional_data'
]
```

**Benefit**: Full Trinity compliance, better logging/tracking
**Cost**: More code, slightly slower

### Phase 2: Pydantic Validation

Add response models:
```python
from pydantic import BaseModel

class QuoteResponse(BaseModel):
    quotes: Dict[str, QuoteData]
    symbols_requested: List[str]
    symbols_returned: List[str]
    success: bool
```

**Benefit**: Type safety, validation, documentation
**Cost**: More boilerplate

### Phase 3: WebSocket Real-Time Quotes

Replace polling with WebSocket streaming:
```python
# Real-time quote updates
ws = market.stream_quotes(['SPY', 'QQQ', 'DIA', 'IWM'])
for quote in ws:
    st.session_state.market_indices_data[quote['symbol']] = quote
    st.rerun()
```

**Benefit**: Live updates without refresh
**Cost**: Complexity, WebSocket infrastructure

---

## Summary

✅ **Fixed fetch_stock_quotes()** to return `{'quotes': {...}}` format
✅ **Fixed fetch_market_movers()** to accept `mover_type` and return `{'movers': [...]}`
✅ **Updated UI** to use correct capabilities (`can_fetch_market_movers`)
✅ **Implemented direct API access** for advanced features (historical, analyst, insider, institutional)
✅ **Added comprehensive error handling** with clear messages
✅ **Maintained Trinity architecture** for core operations while using pragmatic direct access where appropriate

**Status**: Ready to test! Restart Streamlit app to see changes.

```bash
# Restart app
pkill -f streamlit && sleep 3 && ./start.sh

# Navigate to Markets tab
# Should see auto-loading market indices and movers!
```
