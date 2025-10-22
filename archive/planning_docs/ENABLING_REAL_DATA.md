# Enabling Real Data - OpenBB Integration Guide

**Document Version**: 1.0
**Last Updated**: October 20, 2025
**Status**: Post-Migration Guide
**Audience**: Developers, System Administrators

This guide explains how to enable real market data in Trinity 3.0 after completing the Week 6 migration. Currently, the system uses MockDataService for testing. Follow these steps to switch to OpenBBService for real market data.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Install OpenBB Platform](#step-1-install-openbb-platform)
4. [Step 2: Configure API Keys](#step-2-configure-api-keys)
5. [Step 3: Enable Real Data](#step-3-enable-real-data)
6. [Step 4: Test Integration](#step-4-test-integration)
7. [Step 5: Pattern Validation](#step-5-pattern-validation)
8. [Troubleshooting](#troubleshooting)
9. [API Provider Details](#api-provider-details)
10. [Performance Optimization](#performance-optimization)

---

## Overview

### Current State (Week 6 Complete)

**Data Flow**:
```
Pattern → execute_through_registry → CapabilityRouter → MockDataService → Mock Data
```

**Mock Data Coverage**:
- 10 stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, JPM, V, WMT)
- 6 economic indicators (GDP, CPI, unemployment, Fed rate, 10Y/2Y Treasuries)
- Historical prices (30 days, simulated)
- News headlines (realistic mock)

### Target State (After This Guide)

**Data Flow**:
```
Pattern → execute_through_registry → CapabilityRouter → OpenBBService → Real Data
```

**Real Data Coverage**:
- 10,000+ stocks (all US exchanges)
- 1,000+ economic indicators (FRED, BEA, BLS)
- Real-time quotes (15-min delay free, real-time with API key)
- Historical data (decades of history)
- Options chains, analyst estimates, insider trading, etc.

### Enablement Effort

| Task | Time Required | Difficulty |
|------|---------------|------------|
| Install OpenBB | 5-10 minutes | Easy |
| Configure API Keys | 15-30 minutes | Easy (registration required) |
| Enable Real Data | < 1 minute | Trivial (one line change) |
| Test Integration | 5-10 minutes | Easy |
| **Total** | **30-60 minutes** | **Easy** |

---

## Prerequisites

### System Requirements

- **Python**: 3.11+ (OpenBB requires Python 3.11 or newer)
- **pip**: Latest version (`python3 -m pip install --upgrade pip`)
- **OS**: macOS, Linux, or Windows
- **Memory**: 4GB+ RAM recommended
- **Disk**: 2GB free space for OpenBB and dependencies

### Environment

- **Virtual Environment**: Recommended (avoid PEP 668 issues)
- **Git**: Required for Trinity 3.0 repository
- **Internet**: Required for API calls and package installation

### Current Working State

Before proceeding, verify Trinity 3.0 is operational with mock data:

```bash
cd /path/to/DawsOSB
python3 -c "
import sys
sys.path.insert(0, 'trinity3')
from core.capability_router import CapabilityRouter
router = CapabilityRouter(use_real_data=False)
result = router.route('can_fetch_stock_quotes', {'symbol': 'AAPL'})
assert result['error'] is None
print('✅ Trinity 3.0 mock data working')
"
```

**Expected Output**: `✅ Trinity 3.0 mock data working`

---

## Step 1: Install OpenBB Platform

### Option A: Using Virtual Environment (Recommended)

**Advantages**:
- Avoids PEP 668 restrictions
- Isolated dependencies
- Clean uninstall

**Steps**:

```bash
# Navigate to Trinity 3.0 directory
cd /path/to/DawsOSB/trinity3

# Create virtual environment
python3 -m venv openbb_env

# Activate virtual environment
source openbb_env/bin/activate  # macOS/Linux
# OR
openbb_env\Scripts\activate  # Windows

# Upgrade pip
python -m pip install --upgrade pip

# Install OpenBB Platform
pip install openbb

# Verify installation
python -c "from openbb import obb; print('✅ OpenBB installed successfully')"
```

**Expected Output**: `✅ OpenBB installed successfully`

---

### Option B: Using --user Flag

**Advantages**:
- No virtual environment needed
- System-wide availability

**Disadvantages**:
- May have PATH issues
- Harder to uninstall

**Steps**:

```bash
# Install with --user flag (bypasses PEP 668)
python3 -m pip install --user openbb

# Verify installation
python3 -c "from openbb import obb; print('✅ OpenBB installed successfully')"
```

**If you see "command not found"**:
```bash
# Add user site-packages to PATH
export PATH="$PATH:$(python3 -m site --user-base)/bin"

# Test again
python3 -c "from openbb import obb; print('✅ OpenBB installed successfully')"
```

---

### Option C: System Python (Not Recommended)

**Only if Options A & B fail**:

```bash
# This may require sudo and bypasses security restrictions
sudo python3 -m pip install --break-system-packages openbb

# Verify
python3 -c "from openbb import obb; print('✅ OpenBB installed successfully')"
```

⚠️ **Warning**: This modifies system Python packages. Use with caution.

---

### Verification

After installation, verify OpenBB works:

```bash
python3 -c "
from openbb import obb

# Test basic functionality
quote = obb.equity.price.quote('AAPL', provider='yfinance')
print(f'✅ OpenBB working: AAPL quote fetched')
print(f'   Price: \${quote.results[0].last_price if quote.results else \"N/A\"}')
"
```

**Expected Output**:
```
✅ OpenBB working: AAPL quote fetched
   Price: $178.25
```

---

## Step 2: Configure API Keys

OpenBB works with free providers (yfinance) but premium providers offer better data quality and coverage.

### Recommended API Keys (Free Tier)

| Provider | Data Type | Free Tier | Sign Up |
|----------|-----------|-----------|---------|
| **FRED** | Economic data | Unlimited | https://fred.stlouisfed.org/ |
| **FMP** | Stock data, fundamentals | 250 req/day | https://site.financialmodelingprep.com/ |
| **NewsAPI** | Financial news | 100 req/day | https://newsapi.org/ |
| **Polygon** | Real-time quotes, options | 5 calls/min | https://polygon.io/ |

### Optional API Keys (Paid)

| Provider | Data Type | Cost | Benefits |
|----------|-----------|------|----------|
| Alpha Vantage | Premium fundamentals | $50/mo | Real-time, higher limits |
| Finnhub | Stock data, news | $30/mo | Real-time news |
| Benzinga | News, analyst ratings | $100/mo | Premium news |

---

### Registering for FRED API (Recommended - Free)

**FRED provides economic data (GDP, CPI, unemployment, etc.)**

1. Go to https://fred.stlouisfed.org/
2. Click "My Account" → "API Keys"
3. Click "Request API Key"
4. Fill out form (name, email, organization)
5. **Copy your API key** (looks like: `abcd1234efgh5678ijkl9012mnop3456`)

**Set environment variable**:
```bash
# Add to ~/.bashrc or ~/.zshrc
export FRED_API_KEY="your_fred_api_key_here"

# Reload shell or source file
source ~/.bashrc  # or ~/.zshrc
```

**Verify**:
```bash
echo $FRED_API_KEY
# Should print your API key
```

---

### Registering for FMP API (Recommended - Free)

**FMP provides stock quotes, fundamentals, financial statements**

1. Go to https://site.financialmodelingprep.com/developer/docs
2. Click "Get Your Free API Key"
3. Sign up with email
4. Verify email
5. **Copy your API key** from dashboard

**Set environment variable**:
```bash
export FMP_API_KEY="your_fmp_api_key_here"
```

---

### Registering for NewsAPI (Optional - Free)

**NewsAPI provides financial news headlines**

1. Go to https://newsapi.org/
2. Click "Get API Key"
3. Sign up with email
4. **Copy your API key**

**Set environment variable**:
```bash
export NEWSAPI_KEY="your_newsapi_key_here"
```

---

### Configuring OpenBB with API Keys

OpenBB automatically picks up environment variables. Verify configuration:

```bash
python3 -c "
from openbb import obb
import os

# Check which API keys are configured
api_keys = {
    'FRED_API_KEY': os.getenv('FRED_API_KEY'),
    'FMP_API_KEY': os.getenv('FMP_API_KEY'),
    'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
    'POLYGON_API_KEY': os.getenv('POLYGON_API_KEY'),
}

print('=== API Key Configuration ===')
for key, value in api_keys.items():
    if value:
        print(f'✅ {key}: Configured')
    else:
        print(f'❌ {key}: Not set')

# Test FRED API (if configured)
if api_keys['FRED_API_KEY']:
    try:
        gdp = obb.economy.gdp(provider='fred')
        print(f'\n✅ FRED API working: GDP data fetched')
    except Exception as e:
        print(f'\n❌ FRED API error: {e}')
"
```

**Expected Output**:
```
=== API Key Configuration ===
✅ FRED_API_KEY: Configured
✅ FMP_API_KEY: Configured
❌ NEWSAPI_KEY: Not set
❌ POLYGON_API_KEY: Not set

✅ FRED API working: GDP data fetched
```

---

## Step 3: Enable Real Data

### The One-Line Change

**File**: `trinity3/core/actions/execute_through_registry.py`

**Current Code** (line 57):
```python
self._capability_router = CapabilityRouter(use_real_data=False)  # Mock data
```

**Change To**:
```python
self._capability_router = CapabilityRouter(use_real_data=True)  # Real data via OpenBB
```

**That's it!** All patterns now use real market data.

---

### Making the Change

```bash
# Navigate to Trinity 3.0 directory
cd /path/to/DawsOSB

# Edit the file
nano trinity3/core/actions/execute_through_registry.py
# OR
vim trinity3/core/actions/execute_through_registry.py
# OR use your preferred editor

# Find line 57 (search for "use_real_data=False")
# Change False → True
# Save and exit
```

**Automated Change** (if you prefer command line):
```bash
# Backup original file
cp trinity3/core/actions/execute_through_registry.py trinity3/core/actions/execute_through_registry.py.bak

# Make the change
sed -i '' 's/use_real_data=False/use_real_data=True/g' trinity3/core/actions/execute_through_registry.py

# Verify change
grep "use_real_data" trinity3/core/actions/execute_through_registry.py
# Should show: use_real_data=True
```

---

## Step 4: Test Integration

### Quick Test

**Test 1: CapabilityRouter with Real Data**:
```bash
python3 -c "
import sys
sys.path.insert(0, 'trinity3')

from core.capability_router import CapabilityRouter

# Initialize with real data
router = CapabilityRouter(use_real_data=True)

# Check service info
info = router.get_service_info()
print(f'Service Type: {info[\"service_type\"]}')
print(f'Service Class: {info[\"service_class\"]}')

# Test stock quote
result = router.route('can_fetch_stock_quotes', {'symbol': 'AAPL'})
if result['error']:
    print(f'❌ Error: {result[\"error\"]}')
else:
    print(f'✅ Real quote fetched: {result[\"data\"][\"symbol\"]} - \${result[\"data\"][\"last_price\"]}')
"
```

**Expected Output**:
```
Service Type: OpenBB
Service Class: OpenBBService
✅ Real quote fetched: AAPL - $178.25
```

---

**Test 2: Economic Data**:
```bash
python3 -c "
import sys
sys.path.insert(0, 'trinity3')

from core.capability_router import CapabilityRouter

router = CapabilityRouter(use_real_data=True)

# Test economic indicators
result = router.route('can_fetch_economic_data', {
    'indicators': ['GDP', 'CPIAUCSL', 'UNRATE']
})

if result['error']:
    print(f'❌ Error: {result[\"error\"]}')
else:
    print('✅ Economic data fetched:')
    for indicator, data in result['data'].items():
        print(f'   {indicator}: {data[\"value\"]} {data.get(\"units\", \"\")}')
"
```

**Expected Output**:
```
✅ Economic data fetched:
   GDP: 27850.0 Billions of Dollars
   CPIAUCSL: 315.2 Index
   UNRATE: 3.8 Percent
```

---

## Step 5: Pattern Validation

Test patterns with real data to ensure everything works:

### Test Pattern 1: smart_economic_briefing

**Pattern File**: `trinity3/patterns/smart/smart_economic_briefing.json`

**Test Execution** (requires full Trinity runtime - simplified test here):
```bash
python3 -c "
import sys
sys.path.insert(0, 'trinity3')

# Simulate pattern step execution
from core.capability_router import CapabilityRouter

router = CapabilityRouter(use_real_data=True)

# Step 1: Fetch core indicators (from pattern)
result = router.route('can_fetch_economic_data', {
    'indicators': ['GDP', 'CPIAUCSL', 'UNRATE', 'FEDFUNDS'],
    'start_date': '2023-01-01'
})

if result['error']:
    print(f'❌ Pattern step failed: {result[\"error\"]}')
else:
    print('✅ Pattern step 1 (fetch economic data) successful')
    print(f'   Indicators fetched: {list(result[\"data\"].keys())}')
"
```

**Expected Output**:
```
✅ Pattern step 1 (fetch economic data) successful
   Indicators fetched: ['GDP', 'CPIAUCSL', 'UNRATE', 'FEDFUNDS']
```

---

### Test Pattern 2: smart_stock_analysis

**Simulate Pattern Steps**:
```bash
python3 -c "
import sys
sys.path.insert(0, 'trinity3')

from core.capability_router import CapabilityRouter

router = CapabilityRouter(use_real_data=True)

# Step 1: Fetch stock quote
quote_result = router.route('can_fetch_stock_quotes', {'symbol': 'AAPL'})
assert quote_result['error'] is None
print(f'✅ Step 1: Quote fetched - AAPL @ \${quote_result[\"data\"][\"last_price\"]}')

# Step 2: Fetch fundamentals
fund_result = router.route('can_fetch_fundamentals', {'symbol': 'AAPL'})
assert fund_result['error'] is None
print(f'✅ Step 2: Fundamentals fetched - PE {fund_result[\"data\"][\"pe_ratio\"]}')

# Step 3: Fetch news
news_result = router.route('can_fetch_news', {'symbol': 'AAPL', 'limit': 3})
assert news_result['error'] is None
print(f'✅ Step 3: News fetched - {len(news_result[\"data\"])} headlines')

print('\n✅ smart_stock_analysis pattern steps validated with real data')
"
```

---

## Troubleshooting

### Issue 1: OpenBB Import Error

**Error**: `ModuleNotFoundError: No module named 'openbb'`

**Solution**:
```bash
# Verify OpenBB is installed
python3 -m pip list | grep openbb

# If not listed, install:
python3 -m pip install --user openbb

# OR use virtual environment (recommended)
python3 -m venv openbb_env
source openbb_env/bin/activate
pip install openbb
```

---

### Issue 2: API Key Not Working

**Error**: `401 Unauthorized` or `Invalid API Key`

**Solution**:
```bash
# Verify environment variable is set
echo $FRED_API_KEY

# If empty, export it:
export FRED_API_KEY="your_key_here"

# Test API key directly
python3 -c "
from openbb import obb
import os

# Configure credentials
obb.user.credentials.fred_api_key = os.getenv('FRED_API_KEY')

# Test
gdp = obb.economy.gdp(provider='fred')
print('✅ API key works')
"
```

---

### Issue 3: Rate Limiting

**Error**: `429 Too Many Requests`

**Solution**:
- Free tier APIs have rate limits (e.g., FMP: 250 req/day)
- Wait and retry, or upgrade to paid tier
- Use caching in OpenBBService (5-minute TTL already implemented)

---

### Issue 4: No Data for Symbol

**Error**: `Data not available for symbol: XYZ`

**Solution**:
- Verify symbol exists (use yfinance as fallback)
- Check provider supports symbol (e.g., FRED only has US economic data)
- OpenBBService has multi-provider fallback (automatic)

---

## API Provider Details

### FRED (Federal Reserve Economic Data)

**Best For**: Economic indicators (GDP, CPI, unemployment, Fed rate, etc.)

**Coverage**: 1,000+ US economic time series

**Free Tier**: Unlimited requests

**Documentation**: https://fred.stlouisfed.org/docs/api/

**Example Request**:
```python
gdp = obb.economy.gdp(provider='fred')
cpi = obb.economy.cpi(provider='fred')
unemployment = obb.economy.unemployment(provider='fred')
```

---

### FMP (Financial Modeling Prep)

**Best For**: Stock quotes, fundamentals, financial statements

**Coverage**: 50,000+ stocks (US, global)

**Free Tier**: 250 requests/day

**Documentation**: https://site.financialmodelingprep.com/developer/docs

**Example Request**:
```python
quote = obb.equity.price.quote('AAPL', provider='fmp')
fundamentals = obb.equity.fundamental.metrics('AAPL', provider='fmp')
```

---

### yfinance (Yahoo Finance - Fallback)

**Best For**: Fallback when no API key configured

**Coverage**: Most global stocks

**Free Tier**: Unlimited (but rate-limited)

**Limitations**: No official support, may be unreliable

**Example Request**:
```python
quote = obb.equity.price.quote('AAPL', provider='yfinance')
```

---

## Performance Optimization

### Caching (Already Implemented)

OpenBBService includes built-in caching:

**File**: `trinity3/services/openbb_service.py`

```python
self.cache = {}
self.cache_expiry = 300  # 5 minutes
```

**Cache Behavior**:
- Real-time quotes: 5-minute TTL
- Fundamentals: 1-day TTL (configurable)
- Economic indicators: 1-day TTL

**No action needed** - caching works automatically.

---

### Rate Limit Management

**Multi-Provider Fallback** (automatic):

```python
self.provider_hierarchy = {
    'realtime_quotes': ['fmp', 'polygon', 'alpha_vantage', 'finnhub', 'yfinance'],
    'fundamentals': ['fmp', 'polygon', 'yfinance'],
    'economic': ['fred', 'yfinance'],
}
```

**Behavior**:
- If FMP fails (rate limit), automatically tries Polygon
- If all paid providers fail, falls back to yfinance
- User sees seamless experience

---

## Summary Checklist

### Before Enabling Real Data

- [ ] Trinity 3.0 works with mock data
- [ ] Python 3.11+ installed
- [ ] pip up to date

### Installation

- [ ] OpenBB Platform installed (via venv or --user)
- [ ] OpenBB import verified (`from openbb import obb` works)

### API Keys (Minimum)

- [ ] FRED API key registered and configured
- [ ] FMP API key registered and configured (optional but recommended)
- [ ] Environment variables exported (FRED_API_KEY, FMP_API_KEY)
- [ ] API keys tested (FRED API returns data)

### Enable Real Data

- [ ] `execute_through_registry.py` modified (use_real_data=True)
- [ ] File saved

### Testing

- [ ] CapabilityRouter initializes with OpenBBService
- [ ] Stock quotes fetch successfully
- [ ] Economic indicators fetch successfully
- [ ] Patterns validated (smart_economic_briefing, smart_stock_analysis)

### Post-Enablement

- [ ] Monitor API usage (stay within free tier limits)
- [ ] Review logs for errors
- [ ] Update API keys if expired

---

## Rollback Instructions

If real data causes issues, revert to mock data:

**Step 1: Change execute_through_registry.py**:
```python
self._capability_router = CapabilityRouter(use_real_data=False)  # Back to mock
```

**Step 2: Restart application**

**Step 3: Verify mock data works**:
```bash
python3 -c "
import sys
sys.path.insert(0, 'trinity3')
from core.capability_router import CapabilityRouter
router = CapabilityRouter(use_real_data=False)
info = router.get_service_info()
print(f'Service: {info[\"service_type\"]}')  # Should show 'Mock'
"
```

---

## Support Resources

### Documentation
- **OpenBB Docs**: https://docs.openbb.co/
- **Trinity 3.0 Docs**: See `CLAUDE.md` in project root
- **Migration Status**: See `MIGRATION_STATUS.md`

### Community
- **OpenBB Discord**: https://discord.gg/openbb
- **DawsOS GitHub Issues**: https://github.com/yourusername/DawsOSB/issues

### Troubleshooting
- **OpenBB FAQ**: https://docs.openbb.co/platform/faq
- **API Provider Support**: Contact respective provider (FRED, FMP, etc.)

---

**End of Enabling Real Data Guide**

**Last Updated**: October 20, 2025
**Document Version**: 1.0
**Next Review**: When OpenBB Platform updates (quarterly)
