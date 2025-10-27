# OBSERVABILITY_ARCHITECT — Telemetry & Monitoring Specialist

**Agent Type**: Platform
**Phase**: Week 0.5 (Foundation - runs parallel to all work)
**Priority**: P0 (Critical for SLO enforcement)
**Status**: ⚠️ Instrumentation exists but is disabled by default (`ENABLE_OBSERVABILITY=false`)
**Created**: 2025-10-21

---

> **Reality check (2025-10-26)**: OpenTelemetry/Prometheus wiring is merged, yet no Jaeger/Prom targets ship in the default `.env`. Engineers must opt in locally; production activation is blocked on `.ops/TASK_INVENTORY_2025-10-24.md#P1-DOCS-3`.

## Mission

Build **comprehensive observability stack** with OpenTelemetry distributed tracing, Prometheus metrics, structured logging, and alerting to enforce SLOs (warm p95 ≤ 1.2s, cold p95 ≤ 2.0s, alert median ≤ 60s) and enable rapid incident response once the feature flag is enabled.

---

## Scope & Responsibilities

### In Scope

1. **Distributed Tracing (OpenTelemetry)**
   - Instrument all API endpoints, database queries, provider calls
   - Trace propagation via `traceparent` header (W3C standard)
   - Export to Jaeger for visualization

2. **Metrics (Prometheus)**
   - SLO enforcement metrics (p95 latency, error rate, pack build duration)
   - Business metrics (portfolio count, trade volume, alert delivery rate)
   - System metrics (CPU, memory, DB connections, cache hit rate)

3. **Structured Logging**
   - JSON logs with trace_id correlation
   - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Centralized logging (e.g., Elasticsearch or CloudWatch)

4. **Alerting (Alertmanager + PagerDuty)**
   - SLO breach alerts (p95 latency > 1.2s for 5 minutes)
   - Critical errors (pricing pack failure, ledger reconciliation failure)
   - Circuit breaker state changes (provider outage)

### Out of Scope

- ❌ Custom metric dashboards (handled by ops team)
- ❌ Cost optimization (separate concern)
- ❌ User-facing analytics (handled by REPORTING_ARCHITECT)

---

## Acceptance Criteria

### AC-1: OpenTelemetry Trace Propagation
**Given**: User requests `/v1/portfolios/{id}/valuation`
**When**: Trace ID generated at API gateway
**Then**:
- Trace ID propagated to all downstream calls (DB, cache, providers)
- Full trace visible in Jaeger with spans:
  - `http.request` (API handler)
  - `db.query` (portfolio lookup)
  - `db.query` (lots + prices join)
  - `cache.get` (pricing pack fetch)
  - `calculation` (valuation math)
- Total span count ≥ 5

**Integration Test**: `tests/integration/test_trace_propagation.py`

---

### AC-2: SLO Enforcement (Warm p95 ≤ 1.2s)
**Given**: 100 requests to `/v1/portfolios/{id}/valuation` (pre-warmed pack)
**When**: Measure p95 latency via Prometheus
**Then**:
- Prometheus query returns p95 ≤ 1200ms:
  ```promql
  histogram_quantile(0.95,
    rate(http_request_duration_seconds_bucket{endpoint="/valuation"}[5m])
  ) <= 1.2
  ```
- If breached for > 5 minutes → alert fires to PagerDuty

**Load Test**: `tests/performance/test_slo_warm_latency.py`

---

### AC-3: Pricing Pack Build Monitoring
**Given**: Nightly pricing pack build job starts at 00:00
**When**: Job completes successfully at 00:12
**Then**:
- Prometheus metrics recorded:
  - `pricing_pack_build_duration_seconds = 720` (12 minutes)
  - `pricing_pack_build_success_total += 1`
  - `pricing_pack_is_fresh{date="2024-10-21"} = 1`
- If build fails or exceeds 00:15 → critical alert (RB-01)

**Golden Test**: `tests/golden/jobs/pricing_pack_build_metrics.json`

---

### AC-4: Alert Delivery Latency (Median ≤ 60s)
**Given**: Portfolio value drops > 5% (triggers alert rule)
**When**: Alert evaluation job runs
**Then**:
- Alert delivered to webhook within 60s (median)
- Prometheus histogram tracks latency:
  ```promql
  histogram_quantile(0.50,
    rate(alert_delivery_duration_seconds_bucket[5m])
  ) <= 60
  ```
- Outlier alerts (p95 > 120s) logged for investigation

**Integration Test**: `tests/integration/test_alert_delivery_latency.py`

---

### AC-5: Circuit Breaker State Tracking
**Given**: FMP provider fails 3 consecutive requests
**When**: Circuit breaker opens
**Then**:
- Prometheus gauge updated:
  ```promql
  circuit_breaker_state{provider="fmp"} = 1  # OPEN
  ```
- Alert fires: "FMP circuit breaker OPEN"
- After 60s timeout → state transitions to HALF_OPEN (value = 2)
- After successful request → CLOSED (value = 0)

**Chaos Test**: `tests/chaos/test_circuit_breaker_monitoring.py`

---

## Implementation Specifications

### OpenTelemetry Setup

```python
# backend/app/core/telemetry.py

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Initialize tracer
tracer_provider = TracerProvider(
    resource=Resource.create({"service.name": "dawsos-backend"})
)
trace.set_tracer_provider(tracer_provider)

# Export to Jaeger
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Auto-instrument SQLAlchemy
SQLAlchemyInstrumentor().instrument(engine=db_engine)

# Global tracer
tracer = trace.get_tracer(__name__)
```

### Custom Span Instrumentation

```python
# Example: Instrument valuation calculation
from app.core.telemetry import tracer

async def calculate_portfolio_valuation(ctx: RequestCtx, portfolio_id: UUID):
    with tracer.start_as_current_span("portfolio.valuation") as span:
        # Add context attributes
        span.set_attribute("portfolio_id", str(portfolio_id))
        span.set_attribute("pricing_pack_id", ctx.pricing_pack_id)
        span.set_attribute("user_id", str(ctx.user_id))

        # Nested span: Load holdings
        with tracer.start_as_current_span("db.load_holdings"):
            holdings = await db.query(...)

        # Nested span: Calculate values
        with tracer.start_as_current_span("calculation.valuate"):
            total_value = sum(h.qty * prices[h.security_id] for h in holdings)

        span.set_attribute("position_count", len(holdings))
        span.set_attribute("total_value", float(total_value))

        return total_value
```

---

### Prometheus Metrics

```python
# backend/app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge, Info

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 1.2, 2.0, 5.0, 10.0]  # SLO-aligned buckets
)

# Pricing pack metrics
pricing_pack_build_duration_seconds = Histogram(
    "pricing_pack_build_duration_seconds",
    "Pricing pack build duration",
    buckets=[60, 300, 600, 900, 1200]  # 1m, 5m, 10m, 15m, 20m
)

pricing_pack_build_success_total = Counter(
    "pricing_pack_build_success_total",
    "Successful pricing pack builds"
)

pricing_pack_build_failures_total = Counter(
    "pricing_pack_build_failures_total",
    "Failed pricing pack builds"
)

pricing_pack_is_fresh = Gauge(
    "pricing_pack_is_fresh",
    "Whether pricing pack is fresh (1=fresh, 0=stale)",
    ["date"]
)

# Alert metrics
alert_delivery_duration_seconds = Histogram(
    "alert_delivery_duration_seconds",
    "Alert delivery latency",
    ["delivery_method"],
    buckets=[1, 5, 10, 30, 60, 120, 300]  # SLO: median ≤ 60s
)

alert_delivery_success_total = Counter(
    "alert_delivery_success_total",
    "Successful alert deliveries",
    ["delivery_method"]
)

alert_delivery_failures_total = Counter(
    "alert_delivery_failures_total",
    "Failed alert deliveries",
    ["delivery_method", "error"]
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    ["provider"]
)

# Provider metrics
provider_requests_total = Counter(
    "provider_requests_total",
    "Total provider API requests",
    ["provider", "endpoint", "status"]
)

provider_latency_seconds = Histogram(
    "provider_latency_seconds",
    "Provider API latency",
    ["provider", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Business metrics
portfolio_count_total = Gauge(
    "portfolio_count_total",
    "Total number of portfolios"
)

trade_volume_total = Counter(
    "trade_volume_total",
    "Total trade volume",
    ["action"]  # buy, sell, dividend
)

# System info
system_info = Info(
    "dawsos_system",
    "DawsOS system information"
)
system_info.info({
    "version": "1.0.0",
    "environment": os.getenv("ENVIRONMENT", "development"),
    "pricing_pack_id": "latest",
})
```

### Metrics Middleware (FastAPI)

```python
# backend/app/middleware/metrics.py

from fastapi import Request
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record HTTP metrics for all requests."""
    start_time = time.time()

    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as e:
        status = 500
        raise
    finally:
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

    return response
```

---

### Structured Logging

```python
# backend/app/core/logger.py

import logging
import json
from datetime import datetime
from app.core.types import RequestCtx

class StructuredLogger:
    """JSON structured logger with trace correlation."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def log(self, level: str, message: str, ctx: RequestCtx = None, **extra):
        """Log with structured JSON output."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "trace_id": ctx.trace_id if ctx else None,
            "request_id": ctx.request_id if ctx else None,
            "user_id": str(ctx.user_id) if ctx else None,
            **extra
        }

        if level == "DEBUG":
            self.logger.debug(json.dumps(log_entry))
        elif level == "INFO":
            self.logger.info(json.dumps(log_entry))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_entry))
        elif level == "ERROR":
            self.logger.error(json.dumps(log_entry))
        elif level == "CRITICAL":
            self.logger.critical(json.dumps(log_entry))

# Usage
logger = StructuredLogger("dawsos")

async def some_function(ctx: RequestCtx):
    logger.log("INFO", "Portfolio valuation requested", ctx=ctx, portfolio_id="uuid-123")
```

---

### Alerting Configuration (Prometheus Alertmanager)

```yaml
# alertmanager/alerts.yml

groups:
  - name: SLO Alerts
    interval: 1m
    rules:
      # Warm latency SLO breach
      - alert: WarmLatencyP95Breach
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket{endpoint="/valuation"}[5m])
          ) > 1.2
        for: 5m
        labels:
          severity: warning
          slo: warm_p95
        annotations:
          summary: "Warm p95 latency > 1.2s"
          description: "p95 latency is {{ $value }}s (SLO: 1.2s)"

      # Cold latency SLO breach
      - alert: ColdLatencyP95Breach
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket{cache_hit="false"}[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: warning
          slo: cold_p95
        annotations:
          summary: "Cold p95 latency > 2.0s"
          description: "p95 latency is {{ $value }}s (SLO: 2.0s)"

      # Pricing pack build failure
      - alert: PricingPackBuildFailure
        expr: increase(pricing_pack_build_failures_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Pricing pack build failed"
          description: "Check RB-01 runbook"

      # Pricing pack build deadline missed
      - alert: PricingPackBuildDeadlineMissed
        expr: |
          (time() % 86400) > 900 and  # After 00:15 local time
          pricing_pack_is_fresh{date=~".*"} == 0
        labels:
          severity: critical
        annotations:
          summary: "Pricing pack not fresh by 00:15"
          description: "SLO breach: pack must be ready by 00:15"

      # Circuit breaker open
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state{provider=~".*"} == 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker OPEN for {{ $labels.provider }}"
          description: "Provider outage detected (RB-02)"

      # Alert delivery SLO breach
      - alert: AlertDeliverySlowMedian
        expr: |
          histogram_quantile(0.50,
            rate(alert_delivery_duration_seconds_bucket[5m])
          ) > 60
        for: 5m
        labels:
          severity: warning
          slo: alert_median
        annotations:
          summary: "Alert delivery median > 60s"
          description: "Median latency is {{ $value }}s (SLO: 60s)"

  - name: Business Alerts
    interval: 5m
    rules:
      # Ledger reconciliation failure
      - alert: LedgerReconciliationFailure
        expr: increase(reconciliation_failures_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Ledger reconciliation failed (±1bp breach)"
          description: "Check RB-04 runbook"

      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Error rate > 1%"
          description: "Current error rate: {{ $value }}%"
```

### Alertmanager Routing

```yaml
# alertmanager/config.yml

route:
  receiver: pagerduty
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Critical alerts → PagerDuty (immediate)
    - match:
        severity: critical
      receiver: pagerduty
      continue: true

    # Warning alerts → Slack (batched)
    - match:
        severity: warning
      receiver: slack
      group_wait: 30s
      group_interval: 15m

receivers:
  - name: pagerduty
    pagerduty_configs:
      - service_key: <PAGERDUTY_SERVICE_KEY>
        severity: '{{ .CommonLabels.severity }}'
        description: '{{ .CommonAnnotations.summary }}'

  - name: slack
    slack_configs:
      - api_url: <SLACK_WEBHOOK_URL>
        channel: '#dawsos-alerts'
        title: '{{ .CommonAnnotations.summary }}'
        text: '{{ .CommonAnnotations.description }}'
```

---

## Grafana Dashboards

### SLO Overview Dashboard

```json
{
  "dashboard": {
    "title": "DawsOS SLO Overview",
    "panels": [
      {
        "title": "Warm p95 Latency (SLO: ≤1.2s)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint=\"/valuation\"}[5m]))"
          }
        ],
        "thresholds": [1.2]
      },
      {
        "title": "Cold p95 Latency (SLO: ≤2.0s)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{cache_hit=\"false\"}[5m]))"
          }
        ],
        "thresholds": [2.0]
      },
      {
        "title": "Alert Delivery Median (SLO: ≤60s)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(alert_delivery_duration_seconds_bucket[5m]))"
          }
        ],
        "thresholds": [60]
      },
      {
        "title": "Pricing Pack Build Duration",
        "targets": [
          {
            "expr": "pricing_pack_build_duration_seconds"
          }
        ],
        "thresholds": [900]
      }
    ]
  }
}
```

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit/telemetry/ -k "metrics or logging"
```

**Coverage**:
- Metric recording (counters, histograms, gauges)
- Structured logging (JSON format, trace correlation)

---

### Integration Tests
```bash
pytest tests/integration/test_observability.py
```

**Scenarios**:
1. Trace propagation (API → DB → cache)
2. Metric collection (HTTP latency, provider calls)
3. Alert delivery (webhook, email)
4. Circuit breaker state tracking

---

### Load Tests (SLO Validation)
```bash
locust -f tests/performance/locustfile.py --host=https://staging.dawsos.internal
```

**Targets**:
- 100 RPS sustained for 10 minutes
- p95 latency ≤ 1.2s (warm)
- p95 latency ≤ 2.0s (cold)

---

## Deployment

### Docker Compose (Local Dev)

```yaml
# docker-compose.observability.yml

version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:1.50
    ports:
      - "16686:16686"  # UI
      - "6831:6831/udp"  # Agent (Thrift)

  prometheus:
    image: prom/prometheus:v2.47.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
    ports:
      - "9090:9090"

  alertmanager:
    image: prom/alertmanager:v0.26.0
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"

  grafana:
    image: grafana/grafana:10.1.0
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    ports:
      - "3000:3000"
```

---

## Handoff to All Agents

### Observability Requirements (All Agents)

Every agent MUST:
1. **Propagate trace_id** in all function calls (via RequestCtx)
2. **Record metrics** for all operations (duration, success/failure count)
3. **Log structured JSON** with trace_id correlation
4. **Expose health check** endpoint (`/health`) with dependency status

### Example Pattern (All Capabilities)

```python
from app.core.telemetry import tracer
from app.core.metrics import http_request_duration_seconds
from app.core.logger import logger

async def some_capability(ctx: RequestCtx, request: SomeRequest) -> SomeResponse:
    with tracer.start_as_current_span("capability.some_capability") as span:
        span.set_attribute("request_id", ctx.request_id)

        start = time.time()
        try:
            # Execute capability logic
            result = await do_work(ctx, request)

            # Record success metric
            http_request_duration_seconds.labels(
                method="POST",
                endpoint="/some_capability"
            ).observe(time.time() - start)

            logger.log("INFO", "Capability executed successfully", ctx=ctx)
            return result

        except Exception as e:
            logger.log("ERROR", f"Capability failed: {e}", ctx=ctx, exception=str(e))
            raise
```

---

## Related Documents

- **[PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)** — Section 8: SLOs
- **[RUNBOOKS.md](../../../.ops/RUNBOOKS.md)** — All runbooks reference observability
- **[CI_CD_PIPELINE.md](../../../.ops/CI_CD_PIPELINE.md)** — Stage 11: UAT (SLO validation)
- **[types.py](../../../backend/app/core/types.py)** — RequestCtx with trace_id

---

**Last Updated**: 2025-10-21
**Agent Owner**: Platform Team
**Review Cycle**: After each SLO breach incident
