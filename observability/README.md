# DawsOS Observability Quick Start

**Status**: Production Ready
**Last Updated**: 2025-10-26

---

## 🚀 Quick Start (5 minutes)

### 1. Start Observability Stack

```bash
# From project root
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Verify services
docker ps | grep dawsos
```

### 2. Access UIs

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Backend API** | http://localhost:8000 | None | Execute patterns |
| **Metrics** | http://localhost:8000/metrics | None | Raw Prometheus metrics |
| **Jaeger** | http://localhost:16686 | None | View distributed traces |
| **Prometheus** | http://localhost:9090 | None | Query metrics, check alerts |
| **Alertmanager** | http://localhost:9093 | None | View/silence alerts |
| **Grafana** | http://localhost:3000 | admin/admin | SLO dashboards |

### 3. Execute Pattern and View Trace

```bash
# Execute pattern
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 11111111-1111-1111-1111-111111111111" \
  -d '{
    "pattern_id": "portfolio_overview",
    "inputs": {"portfolio_id": "11111111-1111-1111-1111-111111111111"}
  }'

# View trace in Jaeger
# 1. Open http://localhost:16686
# 2. Service: dawsos-executor
# 3. Operation: execute_pattern
# 4. Click "Find Traces"
# 5. Click on a trace to see spans
```

### 4. View Metrics in Prometheus

```bash
# Open Prometheus
open http://localhost:9090

# Try these PromQL queries:
# - API latency p99:
histogram_quantile(0.99, rate(dawsos_api_request_duration_seconds_bucket[5m]))

# - Request rate:
sum(rate(dawsos_requests_total[5m])) by (pattern_id)

# - Error rate:
sum(rate(dawsos_request_errors_total[5m])) / sum(rate(dawsos_requests_total[5m]))
```

### 5. View SLO Dashboard in Grafana

```bash
# Open Grafana
open http://localhost:3000
# Login: admin/admin

# Navigate: Dashboards → DawsOS → DawsOS SLO Overview
```

---

## 📊 What's Being Monitored

### API Performance
- ✅ Latency (p50, p95, p99) by pattern
- ✅ Request rate by pattern
- ✅ Error rate by pattern/error type
- ✅ Request duration distribution

### Pricing Pack Health
- ✅ Pack freshness status (warming/fresh/error/stale)
- ✅ Pack build duration (SLO: <10 minutes)
- ✅ Reconciliation status

### Agent Performance
- ✅ Agent invocations by agent/capability
- ✅ Agent execution duration
- ✅ Circuit breaker state (closed/open/half_open)
- ✅ Circuit breaker failure rate

### Pattern Execution
- ✅ Pattern execution count by pattern/status
- ✅ Pattern step duration by step/capability

---

## 🚨 Alerts Configured

### SLO Alerts (Warning)
- API latency p99 > 500ms for 5 minutes
- API latency p95 > 300ms for 5 minutes
- Pack build duration > 10 minutes

### Error Alerts
- Error rate > 1% for 5 minutes (Warning)
- Error rate > 5% for 2 minutes (Critical)

### Pack Health Alerts
- Pack not fresh for >30 minutes (Warning)
- Pack in error state (Critical)

### Circuit Breaker Alerts
- Circuit breaker open for >2 minutes (Warning)
- Circuit breaker failures spike (Warning)

### Service Health Alerts
- Backend service down for >1 minute (Critical)
- Low request volume for >10 minutes (Info)

---

## 🔧 Configuration

### Enable Observability (Optional)

Add to `.env` file:

```bash
# Enable tracing and error tracking (optional - graceful degradation if not set)
ENABLE_OBSERVABILITY=true
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
SENTRY_DSN=https://your-key@sentry.io/your-project

# Environment
ENVIRONMENT=production  # or development/staging

# Sampling rates
TRACES_SAMPLE_RATE=0.1   # 10% of requests traced (production)
PROFILES_SAMPLE_RATE=0.1 # 10% of requests profiled
```

**Note**: Metrics are always enabled (Prometheus client). Tracing and error tracking are optional.

### Configure Alertmanager

Edit `observability/alertmanager.yml` to add notification channels:

```yaml
# Slack example
- name: 'warning'
  slack_configs:
    - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
      channel: '#dawsos-alerts'
      title: '⚠️ WARNING: {{ .CommonAnnotations.summary }}'
      text: '{{ .CommonAnnotations.description }}'

# PagerDuty example
- name: 'critical'
  pagerduty_configs:
    - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
      severity: '{{ .CommonLabels.severity }}'
      description: '{{ .CommonAnnotations.summary }}'
```

Then restart Alertmanager:
```bash
docker compose -f docker-compose.observability.yml restart alertmanager
```

---

## 🧪 Testing

### Test Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Expected output** (sample):
```prometheus
# HELP dawsos_api_request_duration_seconds API request duration in seconds
# TYPE dawsos_api_request_duration_seconds histogram
dawsos_api_request_duration_seconds_bucket{pattern_id="portfolio_overview",status="success",le="0.5"} 42
...
```

### Test Trace Creation

```bash
# Execute pattern
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 11111111-1111-1111-1111-111111111111" \
  -d '{"pattern_id": "portfolio_overview", "inputs": {}}'

# Check Jaeger
# Should see trace with spans containing:
# - pricing_pack_id
# - ledger_commit_hash
# - pattern_id
# - agent_name
# - capability
```

### Test Pack Build Metrics

```bash
# Build pack
python backend/jobs/build_pricing_pack.py --date 2025-10-26 --mark-fresh

# Check metric
curl -s http://localhost:8000/metrics | grep pack_build_duration
```

**Expected output**:
```prometheus
dawsos_pack_build_duration_seconds{pack_id="PP_2025-10-26"} 123.45
```

---

## 📖 Architecture

### Metrics Flow
```
Backend API (FastAPI)
  ↓ /metrics endpoint
Prometheus (scrapes every 10s)
  ↓ evaluates alerts
Alertmanager (routes alerts)
  ↓ sends notifications
Slack / PagerDuty / Email
```

### Tracing Flow
```
Backend API (OpenTelemetry SDK)
  ↓ creates spans
Jaeger Collector (receives traces)
  ↓ stores traces
Jaeger UI (visualizes traces)
```

### Dashboards Flow
```
Prometheus (stores metrics)
  ↓ datasource
Grafana (queries metrics)
  ↓ renders dashboards
Browser (displays SLO dashboard)
```

---

## 🔐 Security & Privacy

### No PII in Observability

✅ **User IDs**: Hashed in Sentry, omitted from metrics
✅ **Portfolio IDs**: Hashed in Sentry, included in traces (for debugging)
✅ **Financial amounts**: Redacted from Sentry
✅ **API keys**: Redacted from logs/errors

### Data Retention

- **Traces**: 7 days (Jaeger default)
- **Metrics**: 30 days (Prometheus config)
- **Logs**: Not centralized (future: 30 days in CloudWatch)

### Access Control

- **Grafana**: Username/password authentication
- **Prometheus**: No authentication (internal network only)
- **Jaeger**: No authentication (internal network only)
- **Production**: Use OAuth/SAML for all UIs

---

## 🛠️ Troubleshooting

### Metrics endpoint returns 404

**Problem**: Metrics not exposed

**Solution**:
```bash
# Check if prometheus-client installed
pip show prometheus-client

# Check executor startup logs
docker logs dawsos-backend | grep "Metrics"
```

### Jaeger shows no traces

**Problem**: Tracing not enabled or Jaeger not reachable

**Solution**:
```bash
# Check environment variable
echo $ENABLE_OBSERVABILITY  # Should be "true"
echo $JAEGER_ENDPOINT       # Should be set

# Check Jaeger is running
docker ps | grep jaeger

# Check backend logs
docker logs dawsos-backend | grep "OpenTelemetry"
```

### Prometheus not scraping

**Problem**: Backend not reachable or `/metrics` endpoint not exposed

**Solution**:
```bash
# Check Prometheus targets
# Open http://localhost:9090/targets
# dawsos-backend should be "UP"

# Check backend is reachable from Prometheus container
docker exec dawsos-prometheus wget -q -O - http://backend:8000/metrics
```

### Grafana dashboard empty

**Problem**: No data in Prometheus or dashboard not loaded

**Solution**:
```bash
# Check Prometheus has data
# Open http://localhost:9090
# Query: up{job="dawsos-backend"}
# Should return 1

# Check dashboard is loaded
# Grafana → Configuration → Data Sources
# Prometheus should be listed and "working"

# Refresh dashboard
# Grafana → Dashboards → DawsOS SLO Overview
# Click refresh icon
```

---

## 📚 Additional Resources

- **OpenTelemetry Docs**: https://opentelemetry.io/docs/
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **Jaeger Docs**: https://www.jaegertracing.io/docs/

---

## 🎯 Next Steps

1. **Configure Alert Integrations**
   - Add Slack webhook to `alertmanager.yml`
   - Add PagerDuty service key for critical alerts

2. **Create Custom Dashboards**
   - Business metrics (portfolio count, trade volume)
   - Provider performance (Polygon latency, FMP error rate)

3. **Add More Jobs to Metrics**
   - Instrument `reconcile_ledger.py`
   - Instrument `compute_macro.py`
   - Instrument `evaluate_alerts.py`

4. **Production Deployment**
   - Use managed Grafana Cloud
   - Use managed Prometheus (AWS Managed Prometheus)
   - Use managed Jaeger (Grafana Cloud Traces)
   - Configure HTTPS for all endpoints
   - Enable authentication for all UIs

---

**Questions?** Check `.ops/OBSERVABILITY_IMPLEMENTATION_REPORT.md` for detailed documentation.
