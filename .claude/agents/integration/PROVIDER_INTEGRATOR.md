# PROVIDER_INTEGRATOR — Data Source Integration Specialist

**Agent Type**: Integration
**Phase**: Week 1-2 (Foundation + Data Pipeline)
**Priority**: P0 (Critical for market data)
**Status**: ✅ Facades + transform layer implemented (`5e28827`); live provider quotas + nightly ingestion tracked as ongoing work
**Created**: 2025-10-21

---

## Mission

Build **resilient, rights-aware facades** for all external data providers (FMP, Polygon, FRED, NewsAPI), with circuit breakers, DLQ retry, and usage throttling to prevent cascading failures and license violations.

---

## Scope & Responsibilities

### In Scope

1. **Provider Facades** (4 providers)
   - FMP (Financial Modeling Prep) — quotes, fundamentals, earnings
   - Polygon — options flow, unusual activity
   - FRED (Federal Reserve) — economic indicators
   - NewsAPI — sentiment data

2. **Resilience Patterns**
   - Circuit breaker (3 failures → OPEN for 60s)
   - Exponential backoff retry (3 attempts: 1s, 2s, 4s)
   - Dead Letter Queue (DLQ) for failed requests
   - Graceful degradation (serve cached/stale data)

3. **Rights Management**
   - Pre-flight rights check (before provider call)
   - Usage throttling per license tier
   - Audit trail (provider, endpoint, timestamp, rights_profile)

4. **Observability**
   - OpenTelemetry traces (provider latency, success rate)
   - Prometheus metrics (`provider_requests_total`, `provider_errors_total`, `circuit_breaker_state`)

### Out of Scope

- ❌ Data transformation logic (handled by downstream capabilities)
- ❌ Pricing pack build orchestration (handled by INFRASTRUCTURE_ARCHITECT)
- ❌ Knowledge graph ingestion (handled by KNOWLEDGE_ARCHITECT)

---

## Acceptance Criteria

### AC-1: FMP Provider Facade
**Given**: FMP API key configured
**When**: Request real-time quote for AAPL
**Then**:
- Response returned in < 500ms (cached) or < 2s (live)
- OpenTelemetry trace includes `provider=fmp`, `endpoint=/quote`, `status=200`
- Circuit breaker state tracked in Prometheus

**Golden Test**: `tests/golden/providers/fmp_quote_aapl.json`

---

### AC-2: Circuit Breaker Engagement
**Given**: FMP API returns 3 consecutive 503 errors
**When**: 4th request attempted
**Then**:
- Circuit breaker opens (no request sent to FMP)
- Cached data served with `X-Data-Stale: true` header
- Prometheus metric `circuit_breaker_state{provider="fmp"} = 1` (OPEN)
- Circuit closes after 60s timeout

**Chaos Test**: `tests/chaos/test_provider_outage.py`

---

### AC-3: DLQ Retry for Transient Failures
**Given**: FMP API returns 429 (rate limit)
**When**: Request enqueued in DLQ
**Then**:
- Retry after 1s (exponential backoff)
- After 3 failures, publish to `dlq_failed` topic for manual review
- Audit log entry created

**Integration Test**: `tests/integration/test_dlq_replay.py`

---

### AC-4: Rights-Aware API Calls
**Given**: User has `rights_profile = "basic"` (no options data)
**When**: Request Polygon options flow
**Then**:
- Pre-flight check blocks request (403 Forbidden)
- Audit log entry: `{action: "options_flow", rights_profile: "basic", allowed: false}`
- No provider call made (prevents license violation)

**Regression Test**: `tests/regression/test_rights_enforcement.py`

---

### AC-5: Multi-Provider Aggregation
**Given**: Request for AAPL earnings (available in FMP and Polygon)
**When**: Primary provider (FMP) times out
**Then**:
- Fallback to Polygon automatically
- Response metadata includes `provider_used: "polygon_fallback"`
- Total latency < 3s (SLO for cold requests)

**Integration Test**: `tests/integration/test_provider_fallback.py`

---

## Implementation Specifications

### Provider Facade Interface

```python
# backend/app/integrations/base_provider.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from app.core.types import RequestCtx

@dataclass(frozen=True)
class ProviderRequest:
    """Generic provider request."""
    endpoint: str
    params: Dict[str, Any]
    ctx: RequestCtx
    rights_check: Optional[str] = None  # e.g., "export_pdf"

@dataclass(frozen=True)
class ProviderResponse:
    """Generic provider response."""
    data: Any
    provider: str
    endpoint: str
    status_code: int
    latency_ms: float
    cached: bool = False
    stale: bool = False

class BaseProvider(ABC):
    """Base provider facade with circuit breaker and DLQ."""

    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key
        self.circuit_breaker = CircuitBreaker(name=name, threshold=3, timeout=60)
        self.dlq = DeadLetterQueue(name=f"{name}_dlq")

    @abstractmethod
    async def call(self, request: ProviderRequest) -> ProviderResponse:
        """Execute provider call with resilience patterns."""
        ...

    async def call_with_circuit_breaker(self, request: ProviderRequest) -> ProviderResponse:
        """Wrap call with circuit breaker."""
        if self.circuit_breaker.is_open():
            # Serve cached/stale data
            cached = await self._get_cached(request)
            if cached:
                return cached.with_stale_flag()
            raise ProviderTimeoutError(self.name, timeout_seconds=0)

        try:
            response = await self.call(request)
            self.circuit_breaker.record_success()
            return response
        except Exception as e:
            self.circuit_breaker.record_failure()
            # Enqueue in DLQ for retry
            await self.dlq.enqueue(request, error=str(e))
            raise
```

---

### FMP Provider Implementation

```python
# backend/app/integrations/fmp_provider.py

from app.integrations.base_provider import BaseProvider, ProviderRequest, ProviderResponse
import httpx

class FMPProvider(BaseProvider):
    """Financial Modeling Prep provider."""

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    async def call(self, request: ProviderRequest) -> ProviderResponse:
        """Execute FMP API call."""
        url = f"{self.BASE_URL}{request.endpoint}"
        params = {**request.params, "apikey": self.api_key}

        # Pre-flight rights check
        if request.rights_check:
            await self._check_rights(request.ctx, request.rights_check)

        # Execute call with timeout
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)

        latency_ms = (time.time() - start) * 1000

        # Record telemetry
        self._record_metrics(request.endpoint, resp.status_code, latency_ms)

        return ProviderResponse(
            data=resp.json(),
            provider="fmp",
            endpoint=request.endpoint,
            status_code=resp.status_code,
            latency_ms=latency_ms,
        )

    async def _check_rights(self, ctx: RequestCtx, action: str):
        """Pre-flight rights check."""
        if not ctx.rights_profile:
            return  # No restrictions

        allowed = await check_rights(ctx.rights_profile, action)
        if not allowed:
            raise RightsViolationError(action, ctx.rights_profile)
```

---

### Circuit Breaker Implementation

```python
# backend/app/integrations/circuit_breaker.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = 0  # Normal operation
    OPEN = 1    # Blocking requests
    HALF_OPEN = 2  # Testing recovery

@dataclass
class CircuitBreaker:
    """Circuit breaker for provider resilience."""
    name: str
    threshold: int = 3  # Open after 3 failures
    timeout: int = 60  # Close after 60s
    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None

    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self.state == CircuitState.OPEN:
            # Check timeout
            if self.last_failure_time and \
               datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
                return False
            return True
        return False

    def record_success(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0

    def record_failure(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            # Emit metric
            metrics.gauge(f"circuit_breaker_state", 1, tags={"provider": self.name})
```

---

### Dead Letter Queue (DLQ)

```python
# backend/app/integrations/dlq.py

from dataclasses import dataclass, field
from typing import List
import asyncio

@dataclass
class DLQEntry:
    """Dead letter queue entry."""
    request: ProviderRequest
    error: str
    retry_count: int = 0
    enqueued_at: datetime = field(default_factory=datetime.utcnow)

class DeadLetterQueue:
    """Dead letter queue for failed provider requests."""

    def __init__(self, name: str, max_retries: int = 3):
        self.name = name
        self.max_retries = max_retries
        self.queue: List[DLQEntry] = []

    async def enqueue(self, request: ProviderRequest, error: str):
        """Enqueue failed request for retry."""
        entry = DLQEntry(request=request, error=error)
        self.queue.append(entry)

        # Start background retry
        asyncio.create_task(self._retry_with_backoff(entry))

    async def _retry_with_backoff(self, entry: DLQEntry):
        """Retry with exponential backoff (1s, 2s, 4s)."""
        delays = [1, 2, 4]

        for delay in delays:
            await asyncio.sleep(delay)
            entry.retry_count += 1

            try:
                # Retry the original request
                provider = get_provider(entry.request.ctx)
                await provider.call(entry.request)
                # Success - remove from queue
                self.queue.remove(entry)
                return
            except Exception as e:
                if entry.retry_count >= self.max_retries:
                    # Move to failed queue for manual review
                    await self._publish_to_failed_queue(entry)
                    self.queue.remove(entry)
                    return
```

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit/integrations/ \
  -k "test_circuit_breaker or test_dlq or test_rights_check"
```

**Coverage**:
- Circuit breaker state transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
- DLQ retry with exponential backoff
- Rights pre-flight checks (allow/deny)

---

### Integration Tests
```bash
pytest tests/integration/test_provider_integration.py
```

**Scenarios**:
1. FMP quote fetch (live API)
2. Polygon options flow (live API)
3. FRED economic indicators (live API)
4. Provider fallback (FMP timeout → Polygon)
5. DLQ replay after provider recovery

---

### Chaos Tests
```bash
pytest tests/chaos/test_provider_outage.py
```

**Scenarios**:
1. All providers down (circuit breakers open)
2. Intermittent timeouts (DLQ retries)
3. Rate limiting (429 errors, exponential backoff)

---

## Observability

### OpenTelemetry Traces

```python
# Trace all provider calls
with tracer.start_as_current_span("provider.call") as span:
    span.set_attribute("provider", "fmp")
    span.set_attribute("endpoint", "/quote")
    span.set_attribute("symbol", "AAPL")
    response = await fmp_provider.call(request)
    span.set_attribute("latency_ms", response.latency_ms)
    span.set_attribute("status_code", response.status_code)
```

### Prometheus Metrics

```python
# Counter: Total provider requests
provider_requests_total = Counter(
    "provider_requests_total",
    "Total provider API requests",
    ["provider", "endpoint", "status"]
)

# Histogram: Provider latency
provider_latency_seconds = Histogram(
    "provider_latency_seconds",
    "Provider API latency",
    ["provider", "endpoint"]
)

# Gauge: Circuit breaker state
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    ["provider"]
)
```

---

## Configuration

### Environment Variables

```bash
# FMP
FMP_API_KEY=your_fmp_key
FMP_BASE_URL=https://financialmodelingprep.com/api/v3
FMP_TIMEOUT_SECONDS=5
FMP_CIRCUIT_BREAKER_THRESHOLD=3
FMP_CIRCUIT_BREAKER_TIMEOUT=60

# Polygon
POLYGON_API_KEY=your_polygon_key
POLYGON_BASE_URL=https://api.polygon.io
POLYGON_TIMEOUT_SECONDS=5

# FRED
FRED_API_KEY=your_fred_key
FRED_BASE_URL=https://api.stlouisfed.org/fred
FRED_TIMEOUT_SECONDS=10  # Economic data can be slower

# NewsAPI
NEWS_API_KEY=your_news_key
NEWS_BASE_URL=https://newsapi.org/v2
NEWS_TIMEOUT_SECONDS=3
```

---

## Handoff to Downstream Agents

### Inputs Provided
- Real-time quotes (FMP, Polygon)
- Economic indicators (FRED)
- News sentiment (NewsAPI)

### Outputs Consumed By
- **INFRASTRUCTURE_ARCHITECT** — Pricing pack build (ingest provider data)
- **MACRO_ARCHITECT** — Regime detection (FRED indicators)
- **KNOWLEDGE_ARCHITECT** — News ingestion (sentiment analysis)

---

## Related Documents

- **[PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)** — Section 3: Data Sources
- **[RUNBOOKS.md](../../../.ops/RUNBOOKS.md)** — RB-02: Provider Outage
- **[CI_CD_PIPELINE.md](../../../.ops/CI_CD_PIPELINE.md)** — Stage 5: Integration Tests
- **[types.py](../../../backend/app/core/types.py)** — ProviderTimeoutError, RightsViolationError

---

**Last Updated**: 2025-10-21
**Agent Owner**: Integration Team
**Review Cycle**: After each provider outage (RB-02)
