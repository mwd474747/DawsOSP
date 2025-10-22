# Provider Integrator S1-W2 Implementation - Partial Completion

**Date**: 2025-10-21
**Agent**: PROVIDER_INTEGRATOR
**Phase**: Sprint 1, Week 2
**Status**: 🟡 PARTIAL (Base Infrastructure Complete, Provider Facades Pending)

---

## Executive Summary

Successfully implemented the **base provider infrastructure** with circuit breakers, DLQ, and rate limiting. The foundation is ready for individual provider facades (FMP, Polygon, FRED, NewsAPI).

### ✅ Completed (3 files):
1. **base_provider.py** - Base class with circuit breaker, DLQ, rights checks
2. **rate_limiter.py** - Token bucket rate limiting with jittered backoff, bandwidth tracking

### ⏳ Remaining Work:
3. **fmp_provider.py** - FMP facade with bandwidth budget alarms
4. **polygon_provider.py** - Polygon facade
5. **fred_provider.py** - FRED facade
6. **news_provider.py** - NewsAPI facade
7. **tests/integration/test_providers.py** - Integration tests with fixtures

---

## Files Created

### 1. backend/app/integrations/base_provider.py (458 lines)

**Purpose**: Base class for all provider facades

**Features**:
- ✅ Circuit Breaker with 3 states (CLOSED, OPEN, HALF_OPEN)
- ✅ Dead Letter Queue with exponential backoff (1s, 2s, 4s + jitter)
- ✅ Rights pre-flight checks
- ✅ OpenTelemetry tracing
- ✅ Prometheus metrics:
  - `provider_requests_total{provider, endpoint, status}`
  - `provider_latency_seconds{provider, endpoint}`
  - `provider_errors_total{provider, endpoint, error_type}`
  - `circuit_breaker_state{provider}`
  - `dlq_size{provider}`
- ✅ Cached/stale data serving when circuit open
- ✅ Abstract `call()` method for subclasses

**Circuit Breaker Logic**:
```python
# State transitions:
# CLOSED → OPEN: After 3 failures
# OPEN → HALF_OPEN: After 60s timeout
# HALF_OPEN → CLOSED: After successful request
# HALF_OPEN → OPEN: After failure in recovery
```

**DLQ Retry Logic**:
```python
# Exponential backoff with jitter:
# Attempt 1: 1s ± 20%
# Attempt 2: 2s ± 20%
# Attempt 3: 4s ± 20%
# After 3 failures: Move to failed_queue for manual review
```

---

### 2. backend/app/integrations/rate_limiter.py (285 lines)

**Purpose**: Rate limiting with token bucket algorithm

**Features**:
- ✅ Token Bucket rate limiter
  - Configurable capacity and refill rate
  - Jittered delays (±10%) when tokens exhausted
  - Per-provider buckets managed globally
- ✅ `@rate_limit(requests_per_minute=N)` decorator
- ✅ Exponential backoff on 429 errors (1s, 2s, 4s + 20% jitter)
- ✅ Bandwidth Budget Tracker for FMP
  - Monthly limit tracking (e.g., 50 GB)
  - Alerts at 70%, 85%, 95% thresholds
  - Auto-reset on new month
- ✅ Prometheus metrics:
  - `rate_limit_hits_total{provider}`
  - `rate_limit_429_total{provider}`
  - `bandwidth_used_bytes{provider}`
  - `bandwidth_remaining_pct{provider}`

**Token Bucket Algorithm**:
```python
# Example: 120 requests/minute = 2 tokens/second
# Capacity: 120 tokens
# Refill rate: 2 tokens/sec
# Each request consumes 1 token
# If tokens < 1: block until refilled
```

**Bandwidth Budget Example**:
```python
budget = BandwidthBudget(monthly_limit_gb=50.0)
budget.add_usage(bytes_used=1024 * 1024 * 100)  # 100 MB

# Alerts:
# 70% (35 GB): INFO log
# 85% (42.5 GB): WARNING log
# 95% (47.5 GB): ERROR log + fallback to cache
```

---

## Architecture Overview

### Provider Call Flow

```
UI/Agent Request
    ↓
call_with_circuit_breaker()
    ↓
Circuit Breaker Check
    ├─ OPEN → Serve cached/stale data
    ├─ HALF_OPEN → Limited requests (test recovery)
    └─ CLOSED → Proceed
         ↓
@rate_limit decorator
    ├─ Acquire token from bucket
    └─ Wait if tokens exhausted (jittered delay)
         ↓
call() [implemented by subclass]
    ├─ Pre-flight rights check
    ├─ HTTP request to provider
    ├─ Record telemetry (OTel + Prometheus)
    └─ Return ProviderResponse
         ↓
Success → Cache response, record metrics
Failure → Enqueue in DLQ, fallback to cache
```

### Resilience Patterns

1. **Circuit Breaker**:
   - Prevents cascading failures
   - Serves stale data when provider unavailable
   - Auto-recovery after timeout

2. **Dead Letter Queue**:
   - Retries transient failures (network issues, 500 errors)
   - Exponential backoff prevents thundering herd
   - Failed requests moved to manual review queue

3. **Rate Limiting**:
   - Prevents license violations (429 errors)
   - Token bucket ensures smooth request distribution
   - Jittered delays prevent synchronization

4. **Bandwidth Budget**:
   - Tracks monthly data usage (FMP specific)
   - Alerts before hitting limits
   - Fallback to cache at 95% usage

---

## Remaining Implementation

### 3. FMP Provider (`backend/app/integrations/fmp_provider.py`)

```python
import httpx
from app.integrations.base_provider import BaseProvider, ProviderRequest, ProviderResponse
from app.integrations.rate_limiter import rate_limit, BandwidthBudget

class FMPProvider(BaseProvider):
    """Financial Modeling Prep provider."""

    def __init__(self, api_key: str):
        super().__init__(
            name="fmp",
            api_key=api_key,
            base_url="https://financialmodelingprep.com/api/v3"
        )
        self.bandwidth_budget = BandwidthBudget(monthly_limit_gb=50.0)

    @rate_limit(requests_per_minute=120)  # FMP premium tier
    async def call(self, request: ProviderRequest) -> ProviderResponse:
        """Execute FMP API call."""
        # Pre-flight rights check
        if request.rights_check:
            await self._check_rights(request.ctx, request.rights_check)

        # Build URL
        url = f"{self.base_url}{request.endpoint}"
        params = {**request.params, "apikey": self.api_key}

        # Execute with timeout
        start_time = time.time()
        async with httpx.AsyncClient(timeout=request.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()

        latency_ms = (time.time() - start_time) * 1000

        # Track bandwidth
        content_length = int(resp.headers.get("content-length", 0))
        self.bandwidth_budget.add_usage(content_length)

        # Record metrics
        self._record_metrics(request.endpoint, resp.status_code, latency_ms)

        return ProviderResponse(
            data=resp.json(),
            provider=self.name,
            endpoint=request.endpoint,
            status_code=resp.status_code,
            latency_ms=latency_ms,
        )

    # Specific FMP endpoints
    async def get_quote(self, symbol: str, ctx: RequestCtx) -> Dict:
        """Get real-time quote."""
        request = ProviderRequest(
            endpoint=f"/quote/{symbol}",
            params={},
            ctx=ctx,
        )
        response = await self.call_with_circuit_breaker(request)
        return response.data[0] if response.data else {}

    async def get_fundamentals(self, symbol: str, ctx: RequestCtx) -> Dict:
        """Get company fundamentals."""
        request = ProviderRequest(
            endpoint=f"/profile/{symbol}",
            params={},
            ctx=ctx,
            rights_check="fundamentals",
        )
        response = await self.call_with_circuit_breaker(request)
        return response.data[0] if response.data else {}
```

---

### 4. Polygon Provider (`backend/app/integrations/polygon_provider.py`)

```python
class PolygonProvider(BaseProvider):
    """Polygon.io provider."""

    def __init__(self, api_key: str):
        super().__init__(
            name="polygon",
            api_key=api_key,
            base_url="https://api.polygon.io"
        )

    @rate_limit(requests_per_minute=100)  # Polygon stocks tier
    async def call(self, request: ProviderRequest) -> ProviderResponse:
        # Similar to FMP but different URL structure
        url = f"{self.base_url}{request.endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # ... implementation

    async def get_options_flow(self, symbol: str, ctx: RequestCtx) -> Dict:
        """Get options unusual activity."""
        request = ProviderRequest(
            endpoint=f"/v2/aggs/ticker/{symbol}/range/1/day/...",
            params={},
            ctx=ctx,
            rights_check="options_data",
        )
        response = await self.call_with_circuit_breaker(request)
        return response.data
```

---

### 5. FRED Provider (`backend/app/integrations/fred_provider.py`)

```python
class FREDProvider(BaseProvider):
    """Federal Reserve Economic Data provider."""

    def __init__(self, api_key: str):
        super().__init__(
            name="fred",
            api_key=api_key,
            base_url="https://api.stlouisfed.org/fred"
        )

    @rate_limit(requests_per_minute=60)  # FRED free tier
    async def call(self, request: ProviderRequest) -> ProviderResponse:
        url = f"{self.base_url}{request.endpoint}"
        params = {**request.params, "api_key": self.api_key, "file_type": "json"}
        # ... implementation (timeout=10.0 for economic data)

    async def get_series(self, series_id: str, ctx: RequestCtx) -> Dict:
        """Get economic indicator series."""
        request = ProviderRequest(
            endpoint="/series/observations",
            params={"series_id": series_id},
            ctx=ctx,
            timeout=10.0,
        )
        response = await self.call_with_circuit_breaker(request)
        return response.data
```

---

### 6. NewsAPI Provider (`backend/app/integrations/news_provider.py`)

```python
class NewsAPIProvider(BaseProvider):
    """NewsAPI.org provider."""

    def __init__(self, api_key: str, tier: str = "developer"):
        super().__init__(
            name="newsapi",
            api_key=api_key,
            base_url="https://newsapi.org/v2"
        )
        self.tier = tier

    @rate_limit(requests_per_minute=60)  # Developer tier
    async def call(self, request: ProviderRequest) -> ProviderResponse:
        # Rights check: developer tier does NOT allow exports
        if request.rights_check and self.tier == "developer":
            raise RightsViolationError(
                action=request.rights_check,
                rights_profile="newsapi_developer"
            )

        url = f"{self.base_url}{request.endpoint}"
        headers = {"X-Api-Key": self.api_key}
        # ... implementation (timeout=3.0 for news)

    async def get_headlines(self, query: str, ctx: RequestCtx) -> Dict:
        """Get news headlines."""
        request = ProviderRequest(
            endpoint="/everything",
            params={"q": query, "sortBy": "publishedAt"},
            ctx=ctx,
        )
        response = await self.call_with_circuit_breaker(request)
        return response.data
```

---

### 7. Integration Tests (`tests/integration/test_providers.py`)

```python
import pytest
from backend.app.integrations.fmp_provider import FMPProvider
from backend.app.core.types import RequestCtx
from datetime import datetime
from uuid import uuid4

# Use fixtures instead of mocks (per specification)
@pytest.fixture
def recorded_fmp_quote():
    """Recorded FMP quote fixture (no live API call in tests)."""
    return {
        "symbol": "AAPL",
        "price": 150.25,
        "volume": 50000000,
        "timestamp": "2024-10-20T16:00:00Z"
    }

@pytest.mark.asyncio
async def test_fmp_quote_with_fixture(recorded_fmp_quote):
    """Test FMP quote using recorded fixture."""
    # Load fixture instead of calling live API
    # This avoids mocks while ensuring tests are fast and reliable
    assert recorded_fmp_quote["symbol"] == "AAPL"
    assert recorded_fmp_quote["price"] > 0

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after 3 failures."""
    provider = FMPProvider(api_key="test_key")

    # Simulate 3 failures
    for i in range(3):
        provider.circuit_breaker.record_failure()

    # Circuit should be OPEN
    assert provider.circuit_breaker.is_open() is True

@pytest.mark.asyncio
async def test_rate_limiter_delays_requests():
    """Test rate limiter enforces delays."""
    # Create rate limiter with low limit (5 req/min for testing)
    # Make 10 requests rapidly
    # Assert total time > expected minimum based on rate limit

@pytest.mark.asyncio
async def test_bandwidth_budget_alerts():
    """Test bandwidth budget alerts at thresholds."""
    budget = BandwidthBudget(monthly_limit_gb=1.0)

    # Use 0.7 GB (70% threshold)
    budget.add_usage(int(0.7 * 1024**3))
    # Assert INFO log emitted

    # Use 0.85 GB (85% threshold)
    budget.add_usage(int(0.15 * 1024**3))
    # Assert WARNING log emitted
```

---

## Testing Strategy

### Fixtures vs Mocks

Per specification: **No runtime mocks**. Use **recorded fixtures** in tests only.

**Approach**:
1. Record real API responses once (manually or via VCR.py)
2. Save as JSON fixtures in `tests/fixtures/providers/`
3. Load fixtures in tests (no live API calls)
4. Tests are fast, deterministic, and don't require API keys

**Example Fixture** (`tests/fixtures/providers/fmp_quote_aapl.json`):
```json
{
  "request": {
    "endpoint": "/quote/AAPL",
    "params": {},
    "timestamp": "2024-10-20T16:00:00Z"
  },
  "response": {
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 50000000,
    "change": 1.25,
    "changesPercentage": 0.84
  },
  "latency_ms": 245,
  "status_code": 200
}
```

---

## Dependencies Required

Add to `requirements.txt`:

```
httpx==0.25.1              # Async HTTP client
httpx[http2]==0.25.1       # HTTP/2 support
tenacity==8.2.3            # Retry library (alternative to custom backoff)
```

**Decision**: Check if any of these are new dependencies not already in the project. If so, emit ADR and pause (per specification).

---

## Environment Variables

Add to `.env`:

```bash
# FMP
FMP_API_KEY=your_fmp_key
FMP_BASE_URL=https://financialmodelingprep.com/api/v3
FMP_TIMEOUT_SECONDS=5
FMP_BANDWIDTH_LIMIT_GB=50

# Polygon
POLYGON_API_KEY=your_polygon_key
POLYGON_BASE_URL=https://api.polygon.io
POLYGON_TIMEOUT_SECONDS=5

# FRED
FRED_API_KEY=your_fred_key
FRED_BASE_URL=https://api.stlouisfed.org/fred
FRED_TIMEOUT_SECONDS=10

# NewsAPI
NEWS_API_KEY=your_news_key
NEWS_BASE_URL=https://newsapi.org/v2
NEWS_TIMEOUT_SECONDS=3
NEWS_TIER=developer  # or "business"
```

---

## Next Steps

1. **Check Dependencies**: Verify if `httpx` and `tenacity` are new. If new, emit ADR.
2. **Implement Provider Facades**: Complete FMP, Polygon, FRED, NewsAPI (4 files, ~200 lines each)
3. **Create Test Fixtures**: Record real API responses, save as JSON
4. **Write Integration Tests**: Test all AC scenarios with fixtures
5. **Wire into Agent Runtime**: Register providers in `main.py` lifespan
6. **Validate Observability**: Verify OTel traces and Prometheus metrics

---

**Status**: 🟡 **PARTIAL COMPLETION**
**Files Created**: 3/9 (base_provider, rate_limiter, __init__)
**Files Remaining**: 6 (4 providers + integration tests + rights tests)
**Blockers**: None (base infrastructure ready)
**Estimated Completion**: 4-6 hours for remaining implementation

---

**Implementation Date**: 2025-10-21
**Implemented By**: Claude (Anthropic)
**Specification**: `.claude/agents/integration/PROVIDER_INTEGRATOR.md`
