# Run/Validate Commands - Execution Architect S1-W2

**Quick reference for testing the execution architecture implementation**

---

## Prerequisites

```bash
# Install dependencies
pip install fastapi uvicorn pydantic opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp \
    prometheus-client pyyaml pytest pytest-asyncio

# Or from requirements.txt (when created)
pip install -r requirements.txt
```

---

## 1. Start API Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     DawsOS Executor API started successfully
# INFO:     AgentRuntime initialized
# INFO:     Registered agent example_agent with 2 capabilities
```

---

## 2. Test Health Endpoint

```bash
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "ok",
#   "timestamp": "2025-10-21T...",
#   "version": "1.0.0"
# }
```

---

## 3. Test Pattern Listing

```bash
curl http://localhost:8000/patterns

# Expected response (if patterns/ directory has files):
# [
#   {
#     "id": "portfolio_overview",
#     "name": "Portfolio Overview",
#     "description": "...",
#     "category": "analysis"
#   }
# ]

# If no patterns yet:
# []
```

---

## 4. Test /execute Endpoint

### Test with Fresh Pack (expect 200)

```bash
curl -X POST http://localhost:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "pattern_id": "example_pattern",
    "inputs": {}
  }'

# Expected response:
# {
#   "data": {...},
#   "charts": [],
#   "trace": {
#     "pattern_id": "example_pattern",
#     "pricing_pack_id": "20241021_v1",
#     "ledger_commit_hash": "...",
#     "agents_used": [],
#     "capabilities_used": [],
#     "sources": [],
#     "per_panel_staleness": [],
#     "steps": []
#   }
# }
```

### Test Freshness Gate (mock warming pack)

This requires modifying the code temporarily or using the test suite.
See `tests/integration/test_freshness_gate.py` for automated testing.

---

## 5. Test Prometheus Metrics

```bash
curl http://localhost:8000/metrics

# Expected output (Prometheus text format):
# pattern_latency_seconds_bucket{pattern_id="example",status="success",le="0.1"} 1.0
# pattern_latency_seconds_bucket{pattern_id="example",status="success",le="0.25"} 1.0
# ...
# executor_requests_total{pattern_id="example",status="success"} 1.0
# freshness_gate_blocks_total{pack_id="20241021_v1"} 0.0
```

Filter for specific metrics:

```bash
curl http://localhost:8000/metrics | grep -E "(pattern_latency|freshness_gate)"
```

---

## 6. Test Rights Registry Loading

```bash
python -c "
from backend.app.services.rights_registry import RightsRegistry
registry = RightsRegistry.load_from_yaml('.ops/RIGHTS_REGISTRY.yaml')
print(f'Loaded {len(registry.providers)} providers')
for provider in registry.list_providers():
    print(f\"  {provider['id']}: PDF={'✓' if provider['allows_pdf_export'] else '✗'}, CSV={'✓' if provider['allows_csv_export'] else '✗'}\")
"

# Expected output:
# Loaded 5 providers
#   FMP: PDF=✓, CSV=✓
#   Polygon: PDF=✓, CSV=✓
#   FRED: PDF=✓, CSV=✓
#   NewsAPI: PDF=✗, CSV=✗
#   NewsAPI_Business: PDF=✓, CSV=✓
```

---

## 7. Test Rights Enforcement

### Test Allowed Export (FMP)

```bash
python -c "
from backend.app.services.reports import ReportService
import asyncio

async def test():
    service = ReportService('staging')
    pdf = await service.generate_pdf(
        data={'portfolio_value': 100000},
        providers=['FMP'],
        title='Test Report'
    )
    print(f'✓ Success: {len(pdf)} bytes')

asyncio.run(test())
"

# Expected output:
# INFO:     Generating PDF report: 'Test Report' with providers ['FMP']
# INFO:     Export ALLOWED: pdf export with providers ['FMP'] in staging
# ✓ Success: 334 bytes
```

### Test Blocked Export (NewsAPI)

```bash
python -c "
from backend.app.services.reports import ReportService
from backend.app.core.types import RightsViolationError
import asyncio

async def test():
    service = ReportService('staging')
    try:
        pdf = await service.generate_pdf(
            data={'sentiment': 0.7},
            providers=['NewsAPI'],
            title='Test Report'
        )
        print('✗ Should have been blocked!')
    except RightsViolationError as e:
        print(f'✓ Blocked (expected): {e}')

asyncio.run(test())
"

# Expected output:
# WARNING:  Export BLOCKED: pdf export with providers ['NewsAPI'] in staging
# ✓ Blocked (expected): Rights violation: action 'pdf_export' not permitted under 'staging'
```

---

## 8. Run Integration Tests

### Freshness Gate Tests

```bash
pytest tests/integration/test_freshness_gate.py -v

# Expected output:
# test_freshness_gate_blocks_warming_pack PASSED
# test_freshness_gate_allows_fresh_pack PASSED
# test_freshness_gate_metrics_recorded PASSED
# test_freshness_gate_retry_after_fresh PASSED
```

### Rights Enforcement Tests

```bash
pytest tests/rights/test_reports.py -v

# Expected output:
# test_pdf_export_fmp_allowed PASSED
# test_pdf_export_polygon_allowed PASSED
# test_pdf_export_fred_allowed PASSED
# test_pdf_export_newsapi_blocked PASSED
# test_pdf_export_mixed_with_newsapi_blocked PASSED
# test_pdf_export_mixed_without_newsapi_allowed PASSED
# test_csv_export_fmp_allowed PASSED
# test_csv_export_newsapi_blocked PASSED
# test_attribution_collection PASSED
# test_staging_enforcement PASSED
# test_production_enforcement PASSED
# test_rights_registry_loading PASSED
# test_rights_check_scenarios PASSED
```

### Run All Tests

```bash
pytest tests/ -v

# Or with coverage
pytest tests/ --cov=backend/app --cov-report=html
```

---

## 9. Test Agent Runtime

```bash
python -c "
from backend.app.core.agent_runtime import AgentRuntime, create_runtime_with_agents

# Create runtime with example agent
services = {}
runtime = create_runtime_with_agents(services)

# List registered agents
print('Registered agents:')
for agent_info in runtime.list_agents():
    print(f\"  {agent_info['name']}: {agent_info['capabilities']}\")

# List capabilities
print('\nRegistered capabilities:')
caps = runtime.list_capabilities()
for cap, agent in caps.items():
    print(f'  {cap} → {agent}')
"

# Expected output:
# Registered agents:
#   example_agent: ['example.echo', 'example.double']
#
# Registered capabilities:
#   example.echo → example_agent
#   example.double → example_agent
```

---

## 10. Test Pattern Orchestrator

```bash
python -c "
from backend.app.core.pattern_orchestrator import PatternOrchestrator
from backend.app.core.agent_runtime import create_runtime_with_agents
from backend.app.core.types import RequestCtx
from datetime import datetime
from uuid import uuid4
import asyncio

async def test():
    # Create runtime and orchestrator
    services = {}
    runtime = create_runtime_with_agents(services)
    orchestrator = PatternOrchestrator(runtime, None, None)

    # Create request context
    ctx = RequestCtx(
        pricing_pack_id='20241021_v1',
        ledger_commit_hash='abc123',
        trace_id='test-trace',
        user_id=uuid4(),
        request_id='test-req',
        timestamp=datetime.utcnow()
    )

    # Run example pattern
    pattern = orchestrator.patterns.get('example') or {
        'id': 'example',
        'name': 'Example',
        'steps': [
            {
                'capability': 'example.echo',
                'as': 'result',
                'args': {'message': 'Hello, DawsOS!'}
            }
        ],
        'outputs': ['result']
    }

    # Execute
    result = await orchestrator.run_pattern('example', ctx, {})
    print(f\"✓ Pattern executed successfully\")
    print(f\"  Trace: {result['trace']['trace_id']}\")
    print(f\"  Pack ID: {result['trace']['pricing_pack_id']}\")
    print(f\"  Capabilities used: {result['trace']['capabilities_used']}\")

asyncio.run(test())
"
```

---

## 11. Test Circuit Breaker

```bash
python -c "
from backend.app.core.agent_runtime import CircuitBreaker

# Create circuit breaker
cb = CircuitBreaker(failure_threshold=3, timeout=60)

# Simulate failures
print('Simulating failures...')
for i in range(5):
    cb.record_failure('test_agent')
    status = cb.get_status('test_agent')
    print(f\"  Failure {i+1}: {status['state']} ({status['failures']} failures)\")

# Check if circuit is open
if cb.is_open('test_agent'):
    print('✓ Circuit breaker opened after threshold')

# Simulate success (will remain open until timeout)
cb.record_success('test_agent')
status = cb.get_status('test_agent')
print(f\"After success: {status['state']} (still open until timeout)\")
"

# Expected output:
#   Failure 1: CLOSED (1 failures)
#   Failure 2: CLOSED (2 failures)
#   Failure 3: OPEN (3 failures)
#   Failure 4: OPEN (4 failures)
#   Failure 5: OPEN (5 failures)
# ✓ Circuit breaker opened after threshold
# After success: OPEN (still open until timeout)
```

---

## 12. Verify File Structure

```bash
# Check all created files exist
ls -lh backend/app/main.py
ls -lh backend/app/core/pattern_orchestrator.py
ls -lh backend/app/core/agent_runtime.py
ls -lh backend/app/core/capability_registry.py
ls -lh backend/app/agents/base_agent.py
ls -lh backend/app/services/rights_registry.py
ls -lh backend/app/services/reports.py
ls -lh tests/integration/test_freshness_gate.py
ls -lh tests/rights/test_reports.py

# Count lines of code
wc -l backend/app/main.py
wc -l backend/app/core/*.py
wc -l backend/app/agents/*.py
wc -l backend/app/services/*.py
wc -l tests/**/*.py
```

---

## 13. Validate OpenTelemetry (if OTLP endpoint configured)

```bash
# Set OTLP endpoint
export OTLP_ENDPOINT=http://localhost:4317

# Start API
cd backend
uvicorn app.main:app --reload

# Make request
curl -X POST http://localhost:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{"pattern_id": "example", "inputs": {}}'

# Check OTLP exporter logs
# Should see traces exported to OTLP endpoint
```

---

## 14. Acceptance Criteria Checklist

Run through all acceptance criteria:

- [ ] `/execute` endpoint responds with 200 or 503
- [ ] RequestContext includes pricing_pack_id and ledger_commit_hash
- [ ] Freshness gate blocks when pack warming (503)
- [ ] Pattern orchestrator loads patterns from patterns/ directory
- [ ] Template substitution works ({{state.foo}}, {{ctx.bar}})
- [ ] Agent runtime routes capabilities correctly
- [ ] Circuit breaker opens after 5 failures
- [ ] Trace includes all required fields
- [ ] Rights enforcement blocks NewsAPI exports
- [ ] Reports service calls ensure_allowed()
- [ ] Prometheus metrics available at /metrics
- [ ] OpenTelemetry spans created (if OTLP configured)
- [ ] Integration tests pass
- [ ] Rights tests pass

---

## Troubleshooting

### Import Errors

```bash
# Add project root to PYTHONPATH
export PYTHONPATH=/Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP:$PYTHONPATH

# Or run from project root
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP
python -m backend.app.main
```

### Missing Dependencies

```bash
# Install all dependencies
pip install fastapi uvicorn pydantic opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp \
    prometheus-client pyyaml pytest pytest-asyncio
```

### Rights Registry Not Found

```bash
# Check file exists
ls -lh .ops/RIGHTS_REGISTRY.yaml

# Set environment variable
export RIGHTS_REGISTRY_PATH=.ops/RIGHTS_REGISTRY.yaml
```

### Patterns Directory Not Found

```bash
# Create patterns directory
mkdir -p patterns/analysis patterns/workflows patterns/economy

# Pattern orchestrator will log warning but continue
```

---

## Next Steps

After validating this implementation:

1. **Integrate database**: Implement `get_db()` and database queries
2. **Implement agents**: FinancialAnalyst, MacroHound, DataHarvester
3. **Create patterns**: Add production patterns to patterns/ directory
4. **Enhance reports**: Implement PDF/CSV generation with reportlab/pandas

See `.claude/sessions/EXECUTION_ARCHITECT_S1W2_COMPLETE.md` for full details.

---

**Last Updated**: 2025-10-21
**Implementation**: Sprint 1, Week 2 (EXECUTION_ARCHITECT)
**Status**: ✅ COMPLETE
