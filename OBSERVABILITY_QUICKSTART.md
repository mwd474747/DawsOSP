# DawsOS Observability Quickstart Guide

**Date**: October 27, 2025
**Purpose**: Complete guide to monitoring DawsOS with Prometheus, Grafana, and Jaeger
**Time to Complete**: 10 minutes

---

## Overview

DawsOS includes a complete observability stack:
- **Prometheus** - Metrics collection and storage
- **Grafana** - Dashboards and visualization
- **Jaeger** - Distributed tracing
- **OpenTelemetry Collector** - Unified telemetry pipeline

---

## Quick Start (3 minutes)

### Step 1: Start Observability Stack

```bash
# Start all services including observability
docker compose --profile observability up -d

# Or start only observability services
docker compose --profile observability up -d prometheus grafana jaeger otel-collector
```

### Step 2: Verify Services

```bash
# Check status
docker compose ps

# Should show:
# dawsos-prometheus    running    0.0.0.0:9090->9090/tcp
# dawsos-grafana       running    0.0.0.0:3000->3000/tcp
# dawsos-jaeger        running    0.0.0.0:16686->16686/tcp
# dawsos-otel-collector running   0.0.0.0:4317->4317/tcp
```

### Step 3: Access UIs

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger** | http://localhost:16686 | - |

---

## Grafana Dashboards

### Pre-configured Dashboards

DawsOS includes 3 pre-built dashboards:

1. **API Overview** - Request rates, latency, error rates, pattern executions
2. **Agent Performance** - Agent invocations, latency, circuit breaker status
3. **Alert Delivery & DLQ** - Delivery rates, DLQ size, retry metrics

### Access Dashboards

1. Open Grafana: http://localhost:3000
2. Login (admin / admin)
3. Navigate: **Dashboards** → **DawsOS** folder
4. Select a dashboard

### Dashboard Highlights

**API Overview Dashboard**:
- Request rate (requests/sec)
- Error rate (% of failed requests)
- P95 latency (milliseconds)
- Pattern execution breakdown
- Latency percentiles (P50, P95, P99)

**Agent Performance Dashboard**:
- Agent invocation rate
- Agent error rate
- Circuit breaker status table
- Per-agent latency metrics
- Per-capability invocation breakdown

**Alert Delivery & DLQ Dashboard**:
- Total alert deliveries
- Delivery failure rate
- DLQ size (pending retries)
- Average retry count
- Failed alerts table (top 10)
- Recent successful deliveries

---

## Prometheus Metrics

### Available Metrics

**API Metrics**:
```promql
# Request rate
rate(api_requests_total[5m])

# Error rate
rate(api_requests_total{status=~"4..|5.."}[5m]) / rate(api_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(api_latency_bucket[5m]))
```

**Pattern Metrics**:
```promql
# Pattern execution rate
rate(pattern_executions_total[5m])

# Pattern error rate
rate(pattern_executions_total{status="error"}[5m]) / rate(pattern_executions_total[5m])

# Pattern step duration
histogram_quantile(0.95, rate(pattern_step_duration_bucket[5m]))
```

**Agent Metrics**:
```promql
# Agent invocation rate
rate(agent_invocations_total[5m])

# Agent error rate
rate(agent_invocations_total{status="error"}[5m]) / rate(agent_invocations_total[5m])

# Agent latency (P95)
histogram_quantile(0.95, rate(agent_latency_bucket[5m]))

# Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
circuit_breaker_state
```

**Alert Delivery Metrics**:
```promql
# Alert delivery rate
rate(agent_invocations_total{agent_name="alert_retry_worker"}[5m])

# Alert delivery failure rate
rate(agent_invocations_total{agent_name="alert_retry_worker", status="error"}[5m]) /
rate(agent_invocations_total{agent_name="alert_retry_worker"}[5m])
```

### Query Prometheus

1. Open Prometheus: http://localhost:9090
2. Enter a PromQL query in the expression browser
3. Click **Execute**
4. View **Table** or **Graph** results

---

## Jaeger Tracing

### View Traces

1. Open Jaeger: http://localhost:16686
2. Select **Service**: `dawsos`
3. Select **Operation**:
   - `/v1/patterns/{pattern_id}` - Pattern execution
   - `agent_invoke` - Agent invocation
4. Click **Find Traces**

### Trace Details

Each trace shows:
- **Total duration** - End-to-end execution time
- **Spans** - Individual operations (pattern orchestrator, agent runtime, service calls)
- **Tags** - Metadata (pattern_id, agent_name, capability)
- **Logs** - Debug information
- **Errors** - Exception details

### Example: Pattern Execution Trace

```
Trace: /v1/patterns/portfolio_overview
├── pattern_orchestrator.execute (500ms)
│   ├── Step 1: agent_runtime.invoke (200ms)
│   │   └── financial_analyst.ledger_positions (150ms)
│   ├── Step 2: agent_runtime.invoke (200ms)
│   │   └── financial_analyst.portfolio_metrics (150ms)
│   └── Step 3: agent_runtime.invoke (100ms)
│       └── macro_hound.regime_detect (50ms)
```

---

## OpenTelemetry Collector

### Purpose

The OTel Collector acts as a central telemetry pipeline:
- **Receives** traces, metrics, and logs from backend
- **Processes** (sampling, filtering, enrichment)
- **Exports** to Jaeger (traces) and Prometheus (metrics)

### Configuration

**File**: `observability/otel/otel-collector-config.yml`

**Key Features**:
- Batch processing for performance
- Memory limiter to prevent OOM
- Probabilistic sampling (100% in dev, configurable for prod)
- Resource attributes (service.name, environment, cluster)
- Metric filtering (removes noisy health checks)

### Health Check

```bash
# Check collector health
curl http://localhost:13133

# Expected output:
# {"status":"Server available","upSince":"..."}
```

### Collector Metrics

The collector exports its own metrics:

```bash
# View collector metrics
curl http://localhost:8888/metrics

# Key metrics:
# - otelcol_receiver_accepted_spans
# - otelcol_receiver_refused_spans
# - otelcol_exporter_sent_spans
# - otelcol_processor_batch_batch_send_size
```

---

## Production Configuration

### Environment Variables

**Backend (docker-compose.yml)**:
```yaml
environment:
  OTLP_ENDPOINT: http://jaeger:4317  # Jaeger OTLP receiver
  SENTRY_DSN: ${SENTRY_DSN:-}        # Error tracking (optional)
```

### Prometheus Retention

**Default**: 30 days

**Change**:
```yaml
# docker-compose.yml
prometheus:
  command:
    - '--storage.tsdb.retention.time=90d'  # 90 days
```

### Trace Sampling

**Development**: 100% sampling (all traces)

**Production**: Reduce sampling to save resources

**File**: `observability/otel/otel-collector-config.yml`
```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 10  # 10% sampling in production
```

### Resource Limits

Add resource limits to prevent runaway consumption:

```yaml
# docker-compose.yml
prometheus:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'

grafana:
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '0.5'

jaeger:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '0.5'
```

---

## Alerting (Optional)

### Prometheus Alertmanager

**Add to docker-compose.yml**:
```yaml
alertmanager:
  image: prom/alertmanager:v0.26.0
  container_name: dawsos-alertmanager
  ports:
    - "9093:9093"
  volumes:
    - ./observability/prometheus/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
  networks:
    - dawsos-network
  profiles:
    - observability
```

**Create alert rules**: `observability/prometheus/alerts/api.yml`
```yaml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~"5.."}[5m]) / rate(api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(api_latency_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency detected"
          description: "P95 latency is {{ $value }}s"
```

**Update prometheus.yml**:
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - "alerts/*.yml"
```

---

## Troubleshooting

### Issue: Grafana shows "No data"

**Solution**:
```bash
# 1. Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# 2. Check backend /metrics endpoint
curl http://localhost:8000/metrics

# 3. Verify Prometheus datasource
# Grafana → Configuration → Data Sources → Prometheus
# Test connection
```

### Issue: No traces in Jaeger

**Solution**:
```bash
# 1. Check OTLP_ENDPOINT is set
docker compose exec backend env | grep OTLP

# 2. Check Jaeger OTLP receiver
curl http://localhost:4317

# 3. Check OTel Collector logs
docker compose logs otel-collector

# 4. Generate trace by executing pattern
curl -X POST http://localhost:8000/v1/patterns/portfolio_overview \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 11111111-1111-1111-1111-111111111111" \
  -d '{"portfolio_id": "p1", "asof_date": "2025-01-15"}'
```

### Issue: High memory usage

**Solution**:
```bash
# 1. Check container stats
docker stats dawsos-prometheus dawsos-grafana dawsos-jaeger

# 2. Reduce Prometheus retention
# Edit docker-compose.yml: --storage.tsdb.retention.time=7d

# 3. Enable trace sampling
# Edit observability/otel/otel-collector-config.yml:
# probabilistic_sampler: sampling_percentage: 10

# 4. Restart services
docker compose --profile observability restart
```

### Issue: Dashboard not loading

**Solution**:
```bash
# 1. Check dashboard files exist
ls -la observability/grafana/dashboards/

# 2. Check provisioning config
cat observability/grafana/provisioning/dashboards/dashboards.yml

# 3. Check Grafana logs
docker compose logs grafana

# 4. Manually import dashboard
# Grafana → Dashboards → Import → Upload JSON file
```

---

## Useful Commands

```bash
# Start observability stack
docker compose --profile observability up -d

# Stop observability stack
docker compose --profile observability down

# View logs
docker compose logs -f prometheus
docker compose logs -f grafana
docker compose logs -f jaeger
docker compose logs -f otel-collector

# Restart service
docker compose restart prometheus

# Remove all data (WARNING: deletes metrics and traces)
docker compose --profile observability down -v

# Check disk usage
docker system df
docker volume ls

# Backup Grafana dashboards
docker compose exec grafana grafana-cli admin export-dashboard \
  --homePath=/usr/share/grafana > backup.json
```

---

## Performance Tips

### 1. Reduce Scrape Intervals

**For low-traffic environments**:
```yaml
# prometheus.yml
global:
  scrape_interval: 30s  # Increase from 15s
  evaluation_interval: 30s
```

### 2. Use Recording Rules

**Pre-compute expensive queries**:
```yaml
# prometheus.yml
groups:
  - name: dawsos_recording_rules
    interval: 60s
    rules:
      - record: dawsos:api_errors:rate5m
        expr: rate(api_requests_total{status=~"5.."}[5m])

      - record: dawsos:agent_latency:p95
        expr: histogram_quantile(0.95, rate(agent_latency_bucket[5m]))
```

### 3. Limit Metric Cardinality

**Avoid high-cardinality labels** (user_id, trace_id, timestamps):
```python
# Good
metrics.api_requests.labels(endpoint="/v1/patterns", status="200").inc()

# Bad (high cardinality)
metrics.api_requests.labels(user_id="123", request_id="abc", timestamp="...").inc()
```

---

## Next Steps

1. **Customize Dashboards**: Edit JSON files in `observability/grafana/dashboards/`
2. **Add Alerts**: Create alert rules in `observability/prometheus/alerts/`
3. **Explore Traces**: Run patterns and view execution details in Jaeger
4. **Monitor DLQ**: Check Alert Delivery dashboard for failed alerts
5. **Optimize**: Adjust sampling rates and retention periods for production

---

## Additional Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Dashboards**: https://grafana.com/grafana/dashboards/
- **Jaeger Documentation**: https://www.jaegertracing.io/docs/
- **OpenTelemetry**: https://opentelemetry.io/docs/
- **PromQL Cheat Sheet**: https://promlabs.com/promql-cheat-sheet/

---

**Last Updated**: October 27, 2025
**Maintained By**: DawsOS Team
