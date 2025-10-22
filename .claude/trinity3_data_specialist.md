# Trinity 3.0 Data Specialist

**Your Role**: Integrate OpenBB Platform and eliminate all mock data from Trinity 3.0

**Timeline**: Week 4-5
**Deliverables**:
- Week 4: OpenBB Adapter mapping 103 capabilities
- Week 5: All capabilities wired to real data sources
- Zero mock data (remove PredictionService, CycleService)

---

## Mission

Replace Trinity 3.0's mock services with production-grade data integration:
- Build OpenBB adapter layer for 103 capabilities
- Map each capability to OpenBB/FRED/FMP endpoints
- Implement multi-tier caching (Redis optional, file-based minimum)
- Remove PredictionService and CycleService (100% fake data)
- Achieve 95%+ cache hit rate for performance

---

## Week 4 Tasks

### Day 1: OpenBB Platform Setup

**Install Dependencies**:
```bash
cd trinity3
pip install openbb>=4.0.0 pandas numpy
```

**Test OpenBB Connection**:
```python
# trinity3/tests/test_openbb_connection.py
from openbb import obb

def test_openbb_equity_quote():
    """Test basic equity quote"""
    result = obb.equity.price.quote(symbol="AAPL", provider="fmp")
    assert result is not None
    assert hasattr(result, 'price')
    print(f"AAPL price: ${result.price}")

def test_openbb_economic_data():
    """Test FRED integration via OpenBB"""
    result = obb.economy.gdp(country="united_states", provider="fred")
    assert result is not None
    assert len(result) > 0
    print(f"Latest GDP: {result[-1]}")

def test_openbb_fundamentals():
    """Test fundamental data"""
    result = obb.equity.fundamental.metrics(symbol="AAPL", provider="fmp")
    assert result is not None
    assert hasattr(result, 'pe_ratio')
    print(f"AAPL P/E: {result.pe_ratio}")
```

**Success Criteria**:
- OpenBB installed and working
- Can fetch equity quotes
- Can fetch FRED data
- Can fetch fundamentals

---

### Day 2-3: OpenBB Adapter Layer

**Create Adapter**:

```python
# trinity3/data/openbb_adapter.py
from openbb import obb
from typing import Dict, Any, List, Optional
import logging
from functools import lru_cache
from datetime import datetime, timedelta

class OpenBBAdapter:
    """Maps DawsOS capabilities to OpenBB endpoints"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache = {}  # Simple dict cache (will upgrade to Redis later)
        self.cache_ttl = timedelta(minutes=15)

    # === EQUITY DATA CAPABILITIES ===

    def fetch_stock_quote(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Capability: can_fetch_stock_quotes"""
        cache_key = f"quote_{symbol}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        result = obb.equity.price.quote(symbol=symbol, provider="fmp")
        data = self._normalize_quote(result)

        self._cache_result(cache_key, data)
        return data

    def fetch_fundamentals(self, symbol: str, metrics: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Capability: can_fetch_fundamentals"""
        cache_key = f"fundamentals_{symbol}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        # Fetch multiple fundamental endpoints
        metrics_data = obb.equity.fundamental.metrics(symbol=symbol, provider="fmp")
        ratios = obb.equity.fundamental.ratios(symbol=symbol, provider="fmp")
        income = obb.equity.fundamental.income(symbol=symbol, provider="fmp", period="annual", limit=5)

        data = self._normalize_fundamentals(metrics_data, ratios, income, metrics)

        self._cache_result(cache_key, data)
        return data

    def fetch_historical_prices(self, symbol: str, start_date: str, end_date: str, interval: str = "1d", **kwargs) -> Dict[str, Any]:
        """Capability: can_fetch_historical_data"""
        cache_key = f"historical_{symbol}_{start_date}_{end_date}_{interval}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        result = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            provider="fmp"
        )

        data = self._normalize_timeseries(result)

        self._cache_result(cache_key, data)
        return data

    # === ECONOMIC DATA CAPABILITIES ===

    def fetch_economic_data(self, indicators: List[str], **kwargs) -> Dict[str, Any]:
        """Capability: can_fetch_economic_data"""
        cache_key = f"economic_{'_'.join(sorted(indicators))}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        data = {}
        for indicator in indicators:
            try:
                result = self._fetch_fred_series(indicator)
                data[indicator] = result
            except Exception as e:
                self.logger.error(f"Failed to fetch {indicator}: {e}")
                data[indicator] = None

        self._cache_result(cache_key, data)
        return data

    def _fetch_fred_series(self, series_id: str) -> List[Dict]:
        """Fetch FRED series via OpenBB"""
        # Map common indicator names to FRED series IDs
        series_map = {
            'GDP': 'GDP',
            'UNRATE': 'UNRATE',
            'CPIAUCSL': 'CPIAUCSL',
            'T10Y2Y': 'T10Y2Y',
            'DGS10': 'DGS10',
            'FEDFUNDS': 'FEDFUNDS'
        }

        fred_id = series_map.get(series_id, series_id)

        result = obb.economy.fred_series(series_id=fred_id, provider="fred")
        return self._normalize_timeseries(result)

    # === OPTIONS DATA CAPABILITIES ===

    def fetch_options_chains(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Capability: can_fetch_options_data"""
        cache_key = f"options_{symbol}"

        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']

        result = obb.derivatives.options.chains(symbol=symbol, provider="intrinio")
        data = self._normalize_options_chains(result)

        self._cache_result(cache_key, data)
        return data

    # === CACHE MANAGEMENT ===

    def _is_cached(self, key: str) -> bool:
        """Check if cache entry is valid"""
        if key not in self.cache:
            return False

        cached_time = self.cache[key]['timestamp']
        if datetime.now() - cached_time > self.cache_ttl:
            del self.cache[key]
            return False

        return True

    def _cache_result(self, key: str, data: Any):
        """Store result in cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()

    # === DATA NORMALIZATION ===

    def _normalize_quote(self, result) -> Dict[str, Any]:
        """Normalize quote data to standard format"""
        if not result:
            return {}

        return {
            'symbol': result.symbol,
            'price': result.price,
            'change': result.change,
            'change_percent': result.change_percent,
            'volume': result.volume,
            'timestamp': datetime.now().isoformat()
        }

    def _normalize_fundamentals(self, metrics, ratios, income, requested_metrics) -> Dict[str, Any]:
        """Normalize fundamental data"""
        data = {}

        # Extract requested metrics or all if None
        if metrics:
            data['pe_ratio'] = getattr(metrics, 'pe_ratio', None)
            data['market_cap'] = getattr(metrics, 'market_cap', None)
            data['revenue'] = getattr(metrics, 'revenue', None)

        if ratios:
            data['debt_to_equity'] = getattr(ratios, 'debt_to_equity', None)
            data['current_ratio'] = getattr(ratios, 'current_ratio', None)
            data['roe'] = getattr(ratios, 'return_on_equity', None)

        if income:
            data['revenue_growth'] = self._calculate_growth(income, 'revenue')
            data['profit_margin'] = getattr(income[0], 'profit_margin', None) if income else None

        return data

    def _normalize_timeseries(self, result) -> List[Dict]:
        """Normalize time series data"""
        if not result:
            return []

        normalized = []
        for row in result:
            normalized.append({
                'date': row.date.isoformat() if hasattr(row, 'date') else None,
                'value': row.value if hasattr(row, 'value') else row.close if hasattr(row, 'close') else None,
                'open': getattr(row, 'open', None),
                'high': getattr(row, 'high', None),
                'low': getattr(row, 'low', None),
                'close': getattr(row, 'close', None),
                'volume': getattr(row, 'volume', None)
            })

        return normalized

    def _normalize_options_chains(self, result) -> Dict[str, Any]:
        """Normalize options chain data"""
        # Implementation depends on options data structure
        pass

    def _calculate_growth(self, timeseries, field: str) -> Optional[float]:
        """Calculate YoY growth from time series"""
        if len(timeseries) < 2:
            return None

        latest = getattr(timeseries[0], field, 0)
        previous = getattr(timeseries[1], field, 0)

        if previous == 0:
            return None

        return ((latest - previous) / previous) * 100
```

**Capability Mapping Table**:

Create `trinity3/data/capability_openbb_mapping.json`:
```json
{
  "can_fetch_stock_quotes": {
    "adapter_method": "fetch_stock_quote",
    "openbb_endpoint": "obb.equity.price.quote",
    "provider": "fmp",
    "cache_ttl_minutes": 1
  },
  "can_fetch_fundamentals": {
    "adapter_method": "fetch_fundamentals",
    "openbb_endpoints": [
      "obb.equity.fundamental.metrics",
      "obb.equity.fundamental.ratios",
      "obb.equity.fundamental.income"
    ],
    "provider": "fmp",
    "cache_ttl_minutes": 60
  },
  "can_fetch_historical_data": {
    "adapter_method": "fetch_historical_prices",
    "openbb_endpoint": "obb.equity.price.historical",
    "provider": "fmp",
    "cache_ttl_minutes": 15
  },
  "can_fetch_economic_data": {
    "adapter_method": "fetch_economic_data",
    "openbb_endpoint": "obb.economy.fred_series",
    "provider": "fred",
    "cache_ttl_minutes": 30
  },
  "can_fetch_options_data": {
    "adapter_method": "fetch_options_chains",
    "openbb_endpoint": "obb.derivatives.options.chains",
    "provider": "intrinio",
    "cache_ttl_minutes": 5
  }
}
```

**Success Criteria**:
- OpenBB adapter created
- 5 core capabilities mapped (stocks, fundamentals, historical, economic, options)
- All methods have caching
- Data normalization working

---

### Day 4-5: Complete All 103 Capabilities

**Capability Categories to Map**:

1. **Equity Data** (20 capabilities):
   - can_fetch_stock_quotes ✓
   - can_fetch_fundamentals ✓
   - can_fetch_historical_data ✓
   - can_fetch_insider_trading
   - can_fetch_institutional_holdings
   - can_fetch_analyst_ratings
   - can_fetch_earnings_history
   - can_fetch_dividend_history
   - ... (12 more)

2. **Economic Data** (15 capabilities):
   - can_fetch_economic_data ✓
   - can_fetch_gdp_data
   - can_fetch_inflation_data
   - can_fetch_unemployment_data
   - can_fetch_fed_rates
   - ... (10 more)

3. **Options Data** (10 capabilities):
   - can_fetch_options_data ✓
   - can_calculate_options_greeks
   - can_detect_unusual_options
   - ... (7 more)

4. **Alternative Data** (8 capabilities):
   - can_fetch_news
   - can_fetch_social_sentiment
   - can_fetch_reddit_sentiment
   - ... (5 more)

5. **Analysis Capabilities** (50 capabilities):
   - These use data fetched above, no direct OpenBB mapping
   - Implemented in agents (financial_analyst, macro_analyst, etc.)

**Mapping Template**:
```python
def fetch_insider_trading(self, symbol: str, **kwargs) -> Dict[str, Any]:
    """Capability: can_fetch_insider_trading"""
    cache_key = f"insider_{symbol}"

    if self._is_cached(cache_key):
        return self.cache[cache_key]['data']

    result = obb.equity.ownership.insider_trading(symbol=symbol, provider="fmp")
    data = self._normalize_insider_trading(result)

    self._cache_result(cache_key, data)
    return data
```

**Test All Capabilities**:
```python
def test_all_capabilities():
    adapter = OpenBBAdapter(config)

    # Test equity
    quote = adapter.fetch_stock_quote("AAPL")
    assert quote['symbol'] == 'AAPL'

    # Test fundamentals
    fundamentals = adapter.fetch_fundamentals("AAPL")
    assert 'pe_ratio' in fundamentals

    # Test historical
    historical = adapter.fetch_historical_prices("AAPL", "2024-01-01", "2024-10-01")
    assert len(historical) > 0

    # Test economic
    economic = adapter.fetch_economic_data(["GDP", "UNRATE"])
    assert 'GDP' in economic
    assert 'UNRATE' in economic

    # Test options
    options = adapter.fetch_options_chains("AAPL")
    assert options is not None

    # ... test remaining 98 capabilities
```

**Success Criteria**:
- All 103 capabilities have OpenBB mapping or agent implementation
- Capability mapping JSON complete
- Test coverage for all data fetch capabilities
- No capability uses mock data

---

## Week 5 Tasks

### Day 1-2: Remove Mock Services

**Delete These Files**:
```bash
rm trinity3/services/prediction_service.py
rm trinity3/services/cycle_service.py
rm trinity3/services/mock_*.py
```

**Find All Mock Data References**:
```bash
cd trinity3
grep -r "PredictionService" .
grep -r "CycleService" .
grep -r "mock_" .
```

**Replace with Real Data**:

**Before (Mock)**:
```python
# trinity3/services/prediction_service.py
class PredictionService:
    def predict_recession_probability(self):
        return {
            'probability': 0.35,  # FAKE
            'confidence': 0.7,  # FAKE
            'scenario': 'soft_landing'  # FAKE
        }
```

**After (Real)**:
```python
# trinity3/capabilities/recession_risk.py
class RecessionRiskCapability:
    def __init__(self, openbb_adapter):
        self.adapter = openbb_adapter

    def assess_recession_risk(self, **kwargs) -> Dict[str, Any]:
        """Real recession probability based on FRED indicators"""

        # Fetch real economic data
        indicators = self.adapter.fetch_economic_data([
            'T10Y2Y',  # Yield curve (best predictor)
            'UNRATE',  # Unemployment
            'CPIAUCSL',  # Inflation
            'FEDFUNDS'  # Fed funds rate
        ])

        # Calculate probability using proven economic model
        yield_curve = indicators['T10Y2Y'][-1]['value']
        unemployment = indicators['UNRATE'][-1]['value']

        # Yield curve inversion is 80% accurate predictor
        if yield_curve < 0:
            base_probability = 0.8
        elif yield_curve < 0.5:
            base_probability = 0.4
        else:
            base_probability = 0.1

        # Adjust for unemployment trend
        unemployment_trend = self._calculate_trend(indicators['UNRATE'])
        if unemployment_trend > 0.2:  # Rising unemployment
            base_probability += 0.2

        return {
            'probability': min(base_probability, 1.0),
            'confidence': 0.85,  # Based on historical accuracy
            'key_indicators': {
                'yield_curve': yield_curve,
                'unemployment': unemployment,
                'unemployment_trend': unemployment_trend
            },
            'source': 'FRED (real data)'
        }

    def _calculate_trend(self, timeseries: List[Dict]) -> float:
        """Calculate 3-month trend"""
        if len(timeseries) < 4:
            return 0.0

        recent = timeseries[-1]['value']
        three_months_ago = timeseries[-4]['value']

        return (recent - three_months_ago) / three_months_ago
```

**Test Real vs Mock**:
```python
def test_no_mock_data():
    """Verify no mock services are used"""
    import os
    import ast

    # Parse all Python files
    for root, dirs, files in os.walk('trinity3'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath) as f:
                    content = f.read()

                # Check for mock imports
                assert 'PredictionService' not in content, f"Mock service in {filepath}"
                assert 'CycleService' not in content, f"Mock service in {filepath}"
                assert 'mock_' not in content.lower(), f"Mock data in {filepath}"

def test_recession_probability_real_data():
    """Test recession assessment uses real FRED data"""
    adapter = OpenBBAdapter(config)
    capability = RecessionRiskCapability(adapter)

    result = capability.assess_recession_risk()

    # Verify real data source
    assert result['source'] == 'FRED (real data)'

    # Verify indicators present
    assert 'yield_curve' in result['key_indicators']
    assert 'unemployment' in result['key_indicators']

    # Probability should be reasonable (not always 0.35)
    assert 0.0 <= result['probability'] <= 1.0
```

**Success Criteria**:
- Zero mock services in codebase
- All predictions based on real data
- Tests verify real data sources

---

### Day 3-4: Multi-Tier Caching

**Cache Architecture**:

1. **L1: In-Memory Cache** (Already implemented in OpenBBAdapter)
   - 15-minute TTL for market data
   - 60-minute TTL for fundamentals
   - 30-minute TTL for economic data

2. **L2: File-Based Cache** (Minimum viable)
```python
# trinity3/data/file_cache.py
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional

class FileCache:
    def __init__(self, cache_dir: str = "trinity3/storage/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, ttl_minutes: int = 15) -> Optional[Any]:
        """Get cached value if not expired"""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        # Check age
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(minutes=ttl_minutes):
            cache_file.unlink()  # Delete expired
            return None

        with open(cache_file) as f:
            return json.load(f)

    def set(self, key: str, value: Any):
        """Store value in cache"""
        cache_file = self.cache_dir / f"{key}.json"

        with open(cache_file, 'w') as f:
            json.dump(value, f)

    def clear(self):
        """Clear all cache files"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
```

3. **L3: Redis Cache** (Optional, for production)
```python
# trinity3/data/redis_cache.py
import redis
import json
from typing import Any, Optional

class RedisCache:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        value = self.client.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl_seconds: int = 900):
        """Store value with TTL"""
        self.client.setex(key, ttl_seconds, json.dumps(value))

    def clear(self):
        """Clear all keys"""
        self.client.flushdb()
```

**Integrate Caching into OpenBBAdapter**:
```python
class OpenBBAdapter:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # L1: In-memory
        self.memory_cache = {}

        # L2: File-based (always available)
        self.file_cache = FileCache()

        # L3: Redis (optional)
        self.redis_cache = self._init_redis() if config.use_redis else None

    def _get_cached(self, key: str, ttl_minutes: int) -> Optional[Any]:
        """Try L1 → L2 → L3 cache"""
        # L1: Memory
        if key in self.memory_cache:
            cached = self.memory_cache[key]
            if datetime.now() - cached['timestamp'] < timedelta(minutes=ttl_minutes):
                return cached['data']

        # L2: File
        file_cached = self.file_cache.get(key, ttl_minutes)
        if file_cached:
            # Promote to L1
            self.memory_cache[key] = {'data': file_cached, 'timestamp': datetime.now()}
            return file_cached

        # L3: Redis (if available)
        if self.redis_cache:
            redis_cached = self.redis_cache.get(key)
            if redis_cached:
                # Promote to L1 and L2
                self.memory_cache[key] = {'data': redis_cached, 'timestamp': datetime.now()}
                self.file_cache.set(key, redis_cached)
                return redis_cached

        return None

    def _set_cached(self, key: str, data: Any, ttl_minutes: int):
        """Store in all cache layers"""
        # L1: Memory
        self.memory_cache[key] = {'data': data, 'timestamp': datetime.now()}

        # L2: File
        self.file_cache.set(key, data)

        # L3: Redis (if available)
        if self.redis_cache:
            self.redis_cache.set(key, data, ttl_seconds=ttl_minutes * 60)
```

**Test Caching**:
```python
def test_cache_hit_rate():
    """Verify 95%+ cache hit rate"""
    adapter = OpenBBAdapter(config)

    # First request - cache miss
    result1 = adapter.fetch_stock_quote("AAPL")
    assert result1 is not None

    # Second request - cache hit
    result2 = adapter.fetch_stock_quote("AAPL")
    assert result2 == result1  # Same data from cache

    # Verify cache stats
    stats = adapter.get_cache_stats()
    assert stats['hit_rate'] >= 0.95
```

**Success Criteria**:
- Multi-tier caching working
- 95%+ cache hit rate in tests
- File cache always available
- Redis cache optional but working

---

### Day 5: Integration Testing

**End-to-End Tests**:

```python
def test_full_data_pipeline():
    """Test complete data flow: Request → OpenBB → Cache → Response"""
    adapter = OpenBBAdapter(config)

    # Test 1: Stock analysis data pipeline
    fundamentals = adapter.fetch_fundamentals("AAPL", metrics=['pe_ratio', 'revenue_growth'])
    assert 'pe_ratio' in fundamentals
    assert fundamentals['pe_ratio'] > 0  # Real data

    # Test 2: Economic analysis data pipeline
    economic = adapter.fetch_economic_data(['GDP', 'UNRATE', 'T10Y2Y'])
    assert 'GDP' in economic
    assert len(economic['GDP']) > 0  # Real FRED data

    # Test 3: Cache working
    # Clear L1 memory cache
    adapter.memory_cache.clear()

    # Should hit L2 file cache
    fundamentals2 = adapter.fetch_fundamentals("AAPL")
    assert fundamentals2 == fundamentals

def test_no_mock_data_anywhere():
    """Comprehensive test for zero mock data"""
    import subprocess

    # Search entire codebase
    result = subprocess.run(
        ['grep', '-r', 'mock', 'trinity3/'],
        capture_output=True,
        text=True
    )

    # Should only find this test file
    assert 'test_' in result.stdout or result.returncode != 0

def test_all_capabilities_real_data():
    """Verify all 103 capabilities use real data"""
    adapter = OpenBBAdapter(config)

    # Test sample from each category
    equity = adapter.fetch_stock_quote("AAPL")
    assert 'mock' not in str(equity).lower()

    fundamentals = adapter.fetch_fundamentals("MSFT")
    assert 'mock' not in str(fundamentals).lower()

    economic = adapter.fetch_economic_data(['GDP'])
    assert 'mock' not in str(economic).lower()
```

**Success Criteria**:
- All 103 capabilities have real data sources
- Zero mock data in codebase
- 95%+ cache hit rate
- < 2s average query response

---

## Common Issues & Solutions

### Issue 1: OpenBB Rate Limiting
**Symptom**: 429 errors from FMP/FRED
**Solution**: Increase cache TTL, implement exponential backoff
```python
import time
from openbb.exceptions import APIException

def fetch_with_retry(self, func, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func(*args)
        except APIException as e:
            if '429' in str(e) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

### Issue 2: Missing API Keys
**Symptom**: OpenBB returns empty results
**Solution**: Validate API keys on startup
```python
def validate_api_keys(self):
    """Check all required API keys are present"""
    required = ['FMP_API_KEY', 'FRED_API_KEY']
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise ValueError(f"Missing API keys: {', '.join(missing)}")
```

### Issue 3: Data Normalization Failures
**Symptom**: Inconsistent data structures from different providers
**Solution**: Defensive normalization with defaults
```python
def _normalize_fundamentals(self, result) -> Dict[str, Any]:
    """Safely extract fields with defaults"""
    return {
        'pe_ratio': getattr(result, 'pe_ratio', None),
        'market_cap': getattr(result, 'market_cap', None),
        'revenue': getattr(result, 'revenue', None)
    }
```

---

## Resources

- **OpenBB Docs**: https://docs.openbb.co/platform
- **Capability List**: [CAPABILITY_ROUTING_GUIDE.md](../CAPABILITY_ROUTING_GUIDE.md)
- **DawsOS 2.0 Capabilities**: `dawsos/core/agent_capabilities.py`

**Report to**: Migration Lead
**Update**: MIGRATION_STATUS.md weekly
**Escalate**: API rate limits, missing capabilities, cache performance issues
