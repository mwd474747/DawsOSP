# Observability Agent - Implementation Specification

**Agent Type**: OBSERVABILITY_AGENT  
**Priority**: P1 (High)  
**Estimated Time**: 12 hours  
**Status**: 🚧 Ready for Implementation  

---

## Mission

Enable comprehensive observability for DawsOS by configuring OpenTelemetry tracing, Prometheus metrics collection, and Sentry error tracking. This will provide production-grade monitoring, alerting, and debugging capabilities.

---

## Current State Analysis

### ✅ What's Already Implemented
- **OpenTelemetry Dependencies**: All packages installed in requirements.txt
- **Prometheus Client**: Already available for metrics
- **Sentry SDK**: Installed with FastAPI integration
- **Configuration Framework**: Environment-based toggles exist
- **Instrumentation Hooks**: Basic structure in place

### ⚠️ What Needs Implementation
- **OpenTelemetry Configuration**: Proper setup and export configuration
- **Prometheus Metrics**: Custom metrics for DawsOS-specific operations
- **Sentry Integration**: Error tracking and performance monitoring
- **Grafana Dashboards**: Visualization of metrics and traces
- **Alert Rules**: Prometheus alerting rules for critical metrics
- **Jaeger Integration**: Distributed tracing visualization

---

## Implementation Tasks

### Task 1: OpenTelemetry Configuration (4 hours)

**File**: `backend/app/observability/tracing.py`

**Create comprehensive tracing setup**:
```python
import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

class TracingConfig:
    def __init__(self):
        self.enabled = os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true"
        self.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
        self.service_name = os.getenv("SERVICE_NAME", "dawsos-backend")
        self.service_version = os.getenv("SERVICE_VERSION", "0.7.0")
    
    def setup_tracing(self):
        """Configure OpenTelemetry tracing."""
        if not self.enabled:
            logger.info("Observability disabled via ENABLE_OBSERVABILITY=false")
            return
        
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Instrument libraries
        FastAPIInstrumentor.instrument_app(app)
        AsyncPGInstrumentor().instrument()
        RedisInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        
        logger.info(f"OpenTelemetry tracing enabled for {self.service_name}")
    
    def get_tracer(self, name: str):
        """Get a tracer instance."""
        return trace.get_tracer(name)
```

### Task 2: Prometheus Metrics (3 hours)

**File**: `backend/app/observability/metrics.py`

**Create custom metrics for DawsOS**:
```python
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
import time
from functools import wraps

# API Metrics
api_requests_total = Counter(
    'dawsos_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration = Histogram(
    'dawsos_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Pattern Execution Metrics
pattern_executions_total = Counter(
    'dawsos_pattern_executions_total',
    'Total pattern executions',
    ['pattern_id', 'status']
)

pattern_execution_duration = Histogram(
    'dawsos_pattern_execution_duration_seconds',
    'Pattern execution duration',
    ['pattern_id']
)

# Agent Metrics
agent_capability_calls_total = Counter(
    'dawsos_agent_capability_calls_total',
    'Total agent capability calls',
    ['agent_name', 'capability', 'status']
)

agent_capability_duration = Histogram(
    'dawsos_agent_capability_duration_seconds',
    'Agent capability execution duration',
    ['agent_name', 'capability']
)

# Service Metrics
service_calls_total = Counter(
    'dawsos_service_calls_total',
    'Total service calls',
    ['service_name', 'method', 'status']
)

service_call_duration = Histogram(
    'dawsos_service_call_duration_seconds',
    'Service call duration',
    ['service_name', 'method']
)

# Database Metrics
db_queries_total = Counter(
    'dawsos_db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration = Histogram(
    'dawsos_db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

db_connections_active = Gauge(
    'dawsos_db_connections_active',
    'Active database connections'
)

# Provider Metrics
provider_requests_total = Counter(
    'dawsos_provider_requests_total',
    'Total provider API requests',
    ['provider', 'endpoint', 'status']
)

provider_request_duration = Histogram(
    'dawsos_provider_request_duration_seconds',
    'Provider request duration',
    ['provider', 'endpoint']
)

provider_rate_limit_remaining = Gauge(
    'dawsos_provider_rate_limit_remaining',
    'Provider rate limit remaining',
    ['provider']
)

# Pricing Pack Metrics
pricing_pack_build_duration = Histogram(
    'dawsos_pricing_pack_build_duration_seconds',
    'Pricing pack build duration'
)

pricing_pack_size = Gauge(
    'dawsos_pricing_pack_size_bytes',
    'Pricing pack size in bytes'
)

pricing_pack_freshness = Gauge(
    'dawsos_pricing_pack_freshness_seconds',
    'Seconds since pricing pack was marked fresh'
)

# Alert Metrics
alerts_evaluated_total = Counter(
    'dawsos_alerts_evaluated_total',
    'Total alerts evaluated',
    ['alert_type', 'status']
)

alerts_delivered_total = Counter(
    'dawsos_alerts_delivered_total',
    'Total alerts delivered',
    ['delivery_method', 'status']
)

# System Info
system_info = Info(
    'dawsos_system_info',
    'System information'
)

class MetricsCollector:
    def __init__(self):
        self.enabled = os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true"
        self.metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    
    def setup_metrics(self):
        """Start Prometheus metrics server."""
        if not self.enabled:
            logger.info("Metrics collection disabled via ENABLE_OBSERVABILITY=false")
            return
        
        start_http_server(self.metrics_port)
        system_info.info({
            'version': '0.7.0',
            'python_version': sys.version,
            'environment': os.getenv('ENVIRONMENT', 'development')
        })
        
        logger.info(f"Prometheus metrics server started on port {self.metrics_port}")
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics."""
        api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_pattern_execution(self, pattern_id: str, status: str, duration: float):
        """Record pattern execution metrics."""
        pattern_executions_total.labels(pattern_id=pattern_id, status=status).inc()
        pattern_execution_duration.labels(pattern_id=pattern_id).observe(duration)
    
    def record_agent_capability(self, agent_name: str, capability: str, status: str, duration: float):
        """Record agent capability metrics."""
        agent_capability_calls_total.labels(agent_name=agent_name, capability=capability, status=status).inc()
        agent_capability_duration.labels(agent_name=agent_name, capability=capability).observe(duration)
    
    def record_service_call(self, service_name: str, method: str, status: str, duration: float):
        """Record service call metrics."""
        service_calls_total.labels(service_name=service_name, method=method, status=status).inc()
        service_call_duration.labels(service_name=service_name, method=method).observe(duration)
    
    def record_db_query(self, operation: str, table: str, duration: float):
        """Record database query metrics."""
        db_queries_total.labels(operation=operation, table=table).inc()
        db_query_duration.labels(operation=operation, table=table).observe(duration)
    
    def record_provider_request(self, provider: str, endpoint: str, status: str, duration: float):
        """Record provider request metrics."""
        provider_requests_total.labels(provider=provider, endpoint=endpoint, status=status).inc()
        provider_request_duration.labels(provider=provider, endpoint=endpoint).observe(duration)
    
    def update_pricing_pack_metrics(self, size_bytes: int, freshness_seconds: float):
        """Update pricing pack metrics."""
        pricing_pack_size.set(size_bytes)
        pricing_pack_freshness.set(freshness_seconds)
    
    def update_db_connections(self, active_count: int):
        """Update database connection count."""
        db_connections_active.set(active_count)
```

### Task 3: Sentry Integration (2 hours)

**File**: `backend/app/observability/error_tracking.py`

**Configure Sentry for error tracking**:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.asyncpg import AsyncPGIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import os

class SentryConfig:
    def __init__(self):
        self.enabled = os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true"
        self.dsn = os.getenv("SENTRY_DSN")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.release = os.getenv("SERVICE_VERSION", "0.7.0")
    
    def setup_sentry(self):
        """Configure Sentry error tracking."""
        if not self.enabled or not self.dsn:
            logger.info("Sentry disabled: ENABLE_OBSERVABILITY=false or SENTRY_DSN not set")
            return
        
        sentry_sdk.init(
            dsn=self.dsn,
            environment=self.environment,
            release=self.release,
            integrations=[
                FastApiIntegration(auto_enabling_instrumentations=False),
                AsyncioIntegration(),
                AsyncPGIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            before_send=self._before_send,
        )
        
        logger.info(f"Sentry initialized for environment: {self.environment}")
    
    def _before_send(self, event, hint):
        """Filter sensitive data before sending to Sentry."""
        # Remove sensitive headers
        if 'request' in event and 'headers' in event['request']:
            sensitive_headers = ['authorization', 'x-api-key', 'x-user-id']
            for header in sensitive_headers:
                event['request']['headers'].pop(header.lower(), None)
        
        # Remove sensitive data from extra context
        if 'extra' in event:
            sensitive_keys = ['password', 'token', 'secret', 'key']
            for key in sensitive_keys:
                event['extra'].pop(key, None)
        
        return event
    
    def add_user_context(self, user_id: str, email: str = None, role: str = None):
        """Add user context to Sentry."""
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "role": role
        })
    
    def add_tags(self, **tags):
        """Add custom tags to Sentry."""
        sentry_sdk.set_tags(tags)
    
    def capture_exception(self, exception: Exception, **kwargs):
        """Capture exception with context."""
        return sentry_sdk.capture_exception(exception, **kwargs)
    
    def capture_message(self, message: str, level: str = "info", **kwargs):
        """Capture message with context."""
        return sentry_sdk.capture_message(message, level=level, **kwargs)
```

### Task 4: Middleware Integration (2 hours)

**File**: `backend/app/middleware/observability_middleware.py`

**Create observability middleware**:
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from backend.app.observability.metrics import MetricsCollector
from backend.app.observability.error_tracking import SentryConfig

class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, metrics_collector: MetricsCollector, sentry_config: SentryConfig):
        super().__init__(app)
        self.metrics_collector = metrics_collector
        self.sentry_config = sentry_config
    
    async def dispatch(self, request: Request, call_next):
        """Process request with observability."""
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        user_id = request.headers.get("X-User-ID", "anonymous")
        
        # Add Sentry context
        if self.sentry_config.enabled:
            self.sentry_config.add_user_context(user_id)
            self.sentry_config.add_tags(
                method=method,
                path=path,
                user_id=user_id
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics_collector.record_api_request(
                method=method,
                endpoint=path,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            self.metrics_collector.record_api_request(
                method=method,
                endpoint=path,
                status_code=500,
                duration=duration
            )
            
            # Capture in Sentry
            if self.sentry_config.enabled:
                self.sentry_config.capture_exception(e)
            
            raise
```

### Task 5: Grafana Dashboards (1 hour)

**File**: `observability/grafana/dashboards/dawsos-overview.json`

**Create comprehensive dashboard**:
```json
{
  "dashboard": {
    "id": null,
    "title": "DawsOS Overview",
    "tags": ["dawsos"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(dawsos_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(dawsos_api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(dawsos_api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Pattern Execution Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(dawsos_pattern_executions_total[5m])",
            "legendFormat": "{{pattern_id}}"
          }
        ]
      },
      {
        "id": 4,
        "title": "Database Query Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(dawsos_db_query_duration_seconds_bucket[5m]))",
            "legendFormat": "{{operation}} {{table}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Provider API Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(dawsos_provider_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{provider}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "Pricing Pack Freshness",
        "type": "stat",
        "targets": [
          {
            "expr": "dawsos_pricing_pack_freshness_seconds",
            "legendFormat": "Seconds since fresh"
          }
        ]
      },
      {
        "id": 7,
        "title": "Active Database Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "dawsos_db_connections_active",
            "legendFormat": "Active connections"
          }
        ]
      },
      {
        "id": 8,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(dawsos_api_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### Task 6: Alert Rules (1 hour)

**File**: `observability/prometheus/alerts.yml`

**Create alerting rules**:
```yaml
groups:
  - name: dawsos.rules
    rules:
      - alert: HighErrorRate
        expr: rate(dawsos_api_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(dawsos_api_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: PricingPackStale
        expr: dawsos_pricing_pack_freshness_seconds > 3600
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Pricing pack is stale"
          description: "Pricing pack has been stale for {{ $value }} seconds"

      - alert: DatabaseConnectionsHigh
        expr: dawsos_db_connections_active > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connection count"
          description: "{{ $value }} active database connections"

      - alert: ProviderRateLimitLow
        expr: dawsos_provider_rate_limit_remaining < 100
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Provider rate limit low"
          description: "{{ $labels.provider }} has {{ $value }} requests remaining"

      - alert: PatternExecutionFailure
        expr: rate(dawsos_pattern_executions_total{status="error"}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Pattern execution failures"
          description: "Pattern {{ $labels.pattern_id }} failing at {{ $value }} failures per second"
```

---

## Integration Points

### FastAPI App Integration
**File**: `backend/app/api/executor.py`

Add observability to the main app:
```python
from backend.app.observability.tracing import TracingConfig
from backend.app.observability.metrics import MetricsCollector
from backend.app.observability.error_tracking import SentryConfig
from backend.app.middleware.observability_middleware import ObservabilityMiddleware

# Initialize observability
tracing_config = TracingConfig()
metrics_collector = MetricsCollector()
sentry_config = SentryConfig()

# Setup observability
tracing_config.setup_tracing()
metrics_collector.setup_metrics()
sentry_config.setup_sentry()

# Add middleware
app.add_middleware(
    ObservabilityMiddleware,
    metrics_collector=metrics_collector,
    sentry_config=sentry_config
)
```

### Service Integration
**File**: `backend/app/services/base_service.py`

Add metrics to base service:
```python
from backend.app.observability.metrics import MetricsCollector

class BaseService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.metrics = MetricsCollector()
    
    async def _record_service_call(self, method_name: str, duration: float, status: str = "success"):
        """Record service call metrics."""
        self.metrics.record_service_call(
            service_name=self.__class__.__name__,
            method=method_name,
            status=status,
            duration=duration
        )
```

### Agent Integration
**File**: `backend/app/agents/base_agent.py`

Add metrics to base agent:
```python
from backend.app.observability.metrics import MetricsCollector

class BaseAgent:
    def __init__(self, name: str, services: Dict[str, Any]):
        self.name = name
        self.services = services
        self.metrics = MetricsCollector()
    
    async def _record_capability_call(self, capability: str, duration: float, status: str = "success"):
        """Record capability call metrics."""
        self.metrics.record_agent_capability(
            agent_name=self.name,
            capability=capability,
            status=status,
            duration=duration
        )
```

---

## Environment Configuration

**File**: `.env`

Add observability configuration:
```bash
# Observability Configuration
ENABLE_OBSERVABILITY=true
SERVICE_NAME=dawsos-backend
SERVICE_VERSION=0.7.0
ENVIRONMENT=development

# Jaeger Configuration
JAEGER_ENDPOINT=http://localhost:14268/api/traces
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831

# Prometheus Configuration
METRICS_PORT=8001

# Sentry Configuration
SENTRY_DSN=your-sentry-dsn-here
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

---

## Docker Compose Integration

**File**: `docker-compose.observability.yml`

Add observability services:
```yaml
version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./observability/prometheus:/etc/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./observability/grafana:/var/lib/grafana
```

---

## Success Criteria

### Functional Requirements
- [ ] OpenTelemetry tracing works with Jaeger
- [ ] Prometheus metrics collection functional
- [ ] Sentry error tracking operational
- [ ] Grafana dashboards display data
- [ ] Alert rules trigger correctly

### Performance Requirements
- [ ] Tracing overhead <5% of request time
- [ ] Metrics collection <1% CPU usage
- [ ] Dashboard load time <2 seconds
- [ ] Alert evaluation <10 seconds

### Operational Requirements
- [ ] All services start without errors
- [ ] Metrics persist across restarts
- [ ] Alerts deliver to configured channels
- [ ] Dashboards auto-refresh correctly

---

## Testing Strategy

### Unit Tests
- Metrics collection accuracy
- Tracing span creation
- Error capture functionality
- Configuration validation

### Integration Tests
- End-to-end tracing flow
- Metrics aggregation
- Alert rule evaluation
- Dashboard data accuracy

### Load Tests
- Performance impact measurement
- Memory usage monitoring
- Concurrent request handling
- Long-running stability

---

**Estimated Completion**: 12 hours  
**Priority**: P1 (High - Production readiness)  
**Dependencies**: None (all packages installed)  
**Risk Level**: Low (well-established tools)
