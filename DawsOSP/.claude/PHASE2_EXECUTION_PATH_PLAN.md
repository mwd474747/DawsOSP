# Phase 2: Execution Path + Observability + Rights - ORCHESTRATION PLAN

**Date**: 2025-10-22
**Status**: 🔄 READY TO START
**Duration**: 5 days (40 hours estimated)
**Sprint**: S1-W2 (Week 2 of Sprint 1)

---

## Executive Summary

Phase 2 implements the **execution path** from UI → Executor API → Pattern Orchestrator → Agent Runtime → Services → Data.

**Critical Deliverables**:
1. Executor API with **freshness gate** (blocks if pack warming)
2. Pattern Orchestrator (DAG runner)
3. Agent Runtime (capability routing)
4. Observability skeleton (OTel, Prometheus, Sentry)
5. Rights enforcement (export blocking)
6. Pack health endpoint (`/health/pack`)

**Agent Orchestration**: Use Claude agents to implement each component in parallel streams.

---

## Phase 1 Verification ✅

### Files Verified (11 Total)

**Provider Facades** ✅:
- `backend/app/integrations/fmp_provider.py` (362 lines) - FMP Premium API
- `backend/app/integrations/polygon_provider.py` (354 lines) - Prices + corporate actions + **pay_date**
- `backend/app/integrations/fred_provider.py` (375 lines) - FRED macro data
- `backend/app/integrations/news_provider.py` (329 lines) - NewsAPI with tier-aware rights

**Jobs** ✅:
- `backend/jobs/pricing_pack.py` (509 lines) - Immutable pricing snapshots
- `backend/jobs/reconciliation.py` (529 lines) - ±1bp accuracy validation
- `backend/jobs/metrics.py` (513 lines) - TWR, MWR, vol, Sharpe, alpha, beta
- `backend/jobs/factors.py` (562 lines) - Dalio factor exposures
- `backend/jobs/scheduler.py` (618 lines) - Sacred job order orchestration

**Tests** ✅:
- `backend/tests/golden/multi_currency/adr_paydate_fx.json` (130 lines) - Golden fixture
- `backend/tests/golden/test_adr_paydate_fx.py` (450 lines) - 42¢ accuracy validation

### Key Features Verified ✅

**1. Pay-Date FX Field** (polygon_provider.py:218, 259):
```python
"pay_date": div["pay_date"],  # CRITICAL for ADR FX accuracy
```

**2. Blocking Logic** (scheduler.py:195, 206):
```python
# JOB 2: Reconcile Ledger (CRITICAL - BLOCKS IF FAILS)
if not job2_result.success:
    report.blocked_at = "reconcile_ledger"
    return report  # STOP HERE
```

**3. ±1bp Accuracy** (reconciliation.py:55, 178):
```python
error_bps: Optional[Decimal] = None  # For valuation errors
if error_bps > Decimal('1.0'):  # 1 basis point threshold
```

**Architecture Compliance**: ✅ All Phase 1 components follow PRODUCT_SPEC v2.0 patterns

---

## Phase 2 Requirements (from PRODUCT_SPEC.md)

### Sprint 1 Week 2: Execution Path + Observability + Rights

**Deliverables**:
- Executor API (`/v1/execute` with freshness gate)
- Pattern Orchestrator (DAG runner stub)
- Observability skeleton (OTel, Prom, Sentry)
- Rights gate enforcement (staging)
- Pack health endpoint wired (`/health/pack` returns real status)

**Acceptance Criteria**:
- ✅ Executor rejects requests when pack not fresh (503 error)
- ✅ OTel traces visible in Jaeger with `pricing_pack_id`, `ledger_commit_hash`, `pattern_id`
- ✅ Prometheus metrics scraped (API latency by pattern, pack build duration)
- ✅ Rights gate blocks NewsAPI export in staging
- ✅ Pack health endpoint returns `{"status":"fresh"}` after pre-warm

---

## Agent Orchestration Strategy

### Available Agents

**Base Agent Framework** ✅:
- `backend/app/agents/base_agent.py` - Abstract base class with capability contract
- `backend/app/agents/__init__.py` - Agent registry

**Agent Contract**:
```python
class BaseAgent(ABC):
    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return list of capability IDs this agent provides."""
        pass

    async def execute_capability(self, capability_id: str, ctx: RequestCtx, state: Dict, **kwargs) -> Any:
        """Execute a capability by ID."""
        # Routes to specific method (e.g., ledger.positions → ledger_positions)
        pass
```

### Agent Assignment for Phase 2

**EXECUTOR_AGENT** (backend architect):
- Implement Executor API (`/v1/execute`)
- Pack freshness gate
- RequestCtx construction
- Error handling (503 when warming)

**PATTERN_AGENT** (orchestration specialist):
- Implement Pattern Orchestrator
- DAG runner (sequential step execution)
- State management
- Pattern loading from JSON

**RUNTIME_AGENT** (capability router):
- Implement Agent Runtime
- Capability registration
- Capability resolution
- Agent invocation

**OBSERVABILITY_AGENT** (monitoring specialist):
- OpenTelemetry setup
- Prometheus metrics
- Sentry error tracking
- Trace context propagation

**RIGHTS_AGENT** (compliance specialist):
- Rights registry enforcement
- Export blocking logic
- Attribution text injection
- Watermarking for restricted tiers

**HEALTH_AGENT** (status reporter):
- Pack health endpoint
- Status aggregation
- Freshness checks
- Error reporting

---

## Phase 2 Task Breakdown (6 Tasks)

### Task 1: Executor API with Freshness Gate
**Owner**: EXECUTOR_AGENT
**Priority**: P0 (Critical Path)
**Duration**: 8 hours
**Dependencies**: None (uses Phase 1 scheduler)

**Deliverables**:
1. `backend/api/executor.py` (400 lines)
   - POST `/v1/execute` endpoint
   - Pack freshness check (503 if warming)
   - RequestCtx construction
   - Error handling

2. `backend/api/health.py` (200 lines)
   - GET `/health/pack` endpoint
   - Pack status aggregation
   - Freshness validation

3. `backend/core/types.py` (300 lines)
   - `RequestCtx` dataclass
   - `ExecReq` dataclass
   - `ExecResp` dataclass

**Acceptance Criteria**:
- ✅ Executor blocks requests when `pack.is_fresh = false` (returns 503)
- ✅ Executor includes `pricing_pack_id`, `ledger_commit_hash` in response
- ✅ `/health/pack` returns real pack status from DB

**Implementation Stub**:
```python
# backend/api/executor.py
@app.post("/v1/execute")
async def execute(req: ExecReq, user: User = Depends(get_current_user)):
    # 1. Get latest pack
    pack = await get_latest_pack()

    # 2. Check freshness (CRITICAL GATE)
    if not pack.is_fresh and req.require_fresh:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "pricing_pack_warming",
                "message": "Pricing pack warming in progress. Try again in a few minutes.",
                "pack_id": pack.id,
                "status": pack.status,
                "estimated_ready": pack.updated_at + timedelta(minutes=15),
            }
        )

    # 3. Build request context
    ctx = RequestCtx(
        user_id=user.id,
        pricing_pack_id=pack.id,
        ledger_commit_hash=await get_ledger_commit(),
        asof_date=pack.date,
        require_fresh=req.require_fresh,
    )

    # 4. Execute pattern
    result = await pattern_orchestrator.run(
        pattern_id=req.pattern_id,
        ctx=ctx,
        inputs=req.inputs,
    )

    return ExecResp(
        result=result,
        metadata={
            "pricing_pack_id": pack.id,
            "ledger_commit_hash": ctx.ledger_commit_hash,
            "pattern_id": req.pattern_id,
            "asof_date": str(pack.date),
        }
    )
```

---

### Task 2: Pattern Orchestrator (DAG Runner)
**Owner**: PATTERN_AGENT
**Priority**: P0 (Critical Path)
**Duration**: 8 hours
**Dependencies**: Task 1 (RequestCtx)

**Deliverables**:
1. `backend/patterns/orchestrator.py` (500 lines)
   - Pattern loading from JSON
   - DAG execution (sequential steps)
   - State management
   - Error handling

2. `backend/patterns/loader.py` (200 lines)
   - Pattern schema validation
   - Pattern caching
   - Pattern versioning

**Pattern JSON Schema** (from PRODUCT_SPEC):
```json
{
  "id": "portfolio_overview",
  "version": "1.0",
  "steps": [
    {
      "id": "get_positions",
      "capability": "ledger.positions",
      "agent": "financial_analyst",
      "inputs": {"portfolio_id": "{{inputs.portfolio_id}}"},
      "outputs": ["positions"]
    },
    {
      "id": "apply_pack",
      "capability": "pricing.apply_pack",
      "agent": "financial_analyst",
      "inputs": {
        "positions": "{{state.positions}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "outputs": ["valuations"]
    }
  ]
}
```

**Acceptance Criteria**:
- ✅ Orchestrator loads patterns from `backend/patterns/*.json`
- ✅ Steps execute sequentially
- ✅ State passed between steps
- ✅ Errors propagate with trace context

**Implementation Stub**:
```python
# backend/patterns/orchestrator.py
class PatternOrchestrator:
    async def run(self, pattern_id: str, ctx: RequestCtx, inputs: Dict) -> Any:
        # 1. Load pattern
        pattern = await self.loader.load(pattern_id)

        # 2. Initialize state
        state = {"ctx": ctx, "inputs": inputs}

        # 3. Execute steps sequentially
        for step in pattern["steps"]:
            # Resolve template variables
            step_inputs = self._resolve_templates(step["inputs"], state)

            # Execute capability via agent runtime
            result = await self.runtime.execute_capability(
                capability_id=step["capability"],
                agent_name=step["agent"],
                ctx=ctx,
                **step_inputs
            )

            # Store outputs in state
            for output_key in step["outputs"]:
                state[output_key] = result.get(output_key)

        return state
```

---

### Task 3: Agent Runtime (Capability Routing)
**Owner**: RUNTIME_AGENT
**Priority**: P0 (Critical Path)
**Duration**: 8 hours
**Dependencies**: Task 1 (RequestCtx), Task 2 (Orchestrator)

**Deliverables**:
1. `backend/app/agents/runtime.py` (400 lines)
   - Agent registration
   - Capability resolution
   - Agent invocation
   - Error handling

2. `backend/app/agents/financial_analyst.py` (600 lines)
   - Implements: `ledger.positions`, `pricing.apply_pack`, `metrics.compute`
   - Capability methods
   - Metadata attachment

3. `backend/app/agents/macro_hound.py` (400 lines)
   - Implements: `fred.fetch`, `regime.detect`, `factors.compute`
   - FRED integration
   - Regime detection

**Acceptance Criteria**:
- ✅ Runtime registers agents
- ✅ Runtime resolves capability → agent
- ✅ Runtime invokes agent method
- ✅ Results include `__metadata__` (agent_name, capability_id, duration)

**Implementation Stub**:
```python
# backend/app/agents/runtime.py
class AgentRuntime:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.capability_map: Dict[str, str] = {}  # capability_id → agent_name

    def register_agent(self, agent: BaseAgent):
        """Register agent and build capability map."""
        self.agents[agent.name] = agent

        for capability_id in agent.get_capabilities():
            self.capability_map[capability_id] = agent.name

    async def execute_capability(
        self,
        capability_id: str,
        agent_name: Optional[str],
        ctx: RequestCtx,
        **kwargs
    ) -> Any:
        """Execute capability via agent."""
        # Resolve agent (explicit or via capability map)
        agent_name = agent_name or self.capability_map.get(capability_id)
        if not agent_name:
            raise ValueError(f"No agent registered for capability: {capability_id}")

        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")

        # Execute capability
        result = await agent.execute_capability(
            capability_id=capability_id,
            ctx=ctx,
            state={},
            **kwargs
        )

        return result
```

---

### Task 4: Observability Skeleton (OTel, Prom, Sentry)
**Owner**: OBSERVABILITY_AGENT
**Priority**: P1 (High - Required for S1-W2 gate)
**Duration**: 6 hours
**Dependencies**: Task 1 (Executor), Task 2 (Orchestrator)

**Deliverables**:
1. `backend/observability/tracing.py` (300 lines)
   - OpenTelemetry setup
   - Trace context propagation
   - Span creation
   - Attribute injection

2. `backend/observability/metrics.py` (200 lines)
   - Prometheus metrics
   - Histogram for API latency (by pattern)
   - Counter for requests
   - Gauge for pack freshness

3. `backend/observability/errors.py` (150 lines)
   - Sentry integration
   - Error capture
   - Context enrichment
   - Sampling rules

**Acceptance Criteria**:
- ✅ OTel traces visible in Jaeger
- ✅ Traces include `pricing_pack_id`, `ledger_commit_hash`, `pattern_id`
- ✅ Prometheus scrapes `/metrics` endpoint
- ✅ API latency histogram emitted (labelled by `pattern_id`)
- ✅ Sentry captures errors (no PII in error bodies)

**Implementation Stub**:
```python
# backend/observability/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing():
    """Setup OpenTelemetry tracing."""
    provider = TracerProvider()
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

def trace_execution(pattern_id: str, ctx: RequestCtx):
    """Create span for pattern execution."""
    with tracer.start_as_current_span("pattern_execution") as span:
        span.set_attribute("pattern_id", pattern_id)
        span.set_attribute("pricing_pack_id", ctx.pricing_pack_id)
        span.set_attribute("ledger_commit_hash", ctx.ledger_commit_hash)
        span.set_attribute("user_id", ctx.user_id)
        span.set_attribute("asof_date", str(ctx.asof_date))
        yield span
```

---

### Task 5: Rights Enforcement (Export Blocking)
**Owner**: RIGHTS_AGENT
**Priority**: P1 (High - Required for S1-W2 gate)
**Duration**: 6 hours
**Dependencies**: Task 1 (Executor), provider facades (Phase 1)

**Deliverables**:
1. `backend/compliance/rights_enforcer.py` (400 lines)
   - Rights registry loading (YAML)
   - Export permission checks
   - Attribution text injection
   - Watermarking for restricted tiers

2. `backend/compliance/rights_registry.yaml` (50 lines)
   - Provider rights definitions
   - Export rules
   - Attribution templates

3. `backend/api/export.py` (300 lines)
   - Export endpoints (PDF, CSV)
   - Rights gate enforcement
   - Attribution footers

**Rights Registry** (from DawsOS_Seeding_Plan):
```yaml
FMP:
  export: restricted
  require_license: true
  attribution: "Financial data © Financial Modeling Prep"

Polygon:
  export: restricted
  require_license: true
  attribution: "© Polygon.io"

FRED:
  export: allow
  require_license: false
  attribution: "Source: FRED®"

NewsAPI:
  export: restricted
  require_license: true
  attribution: "News metadata via NewsAPI.org"
  dev_tier_watermark: "Metadata only - Business tier required for full content"
```

**Acceptance Criteria**:
- ✅ Rights gate blocks NewsAPI export (no license)
- ✅ Rights gate allows FRED export (public data)
- ✅ Attribution footers included in exports
- ✅ Watermark applied to dev tier NewsAPI data

**Implementation Stub**:
```python
# backend/compliance/rights_enforcer.py
class RightsEnforcer:
    def __init__(self, registry_path: str = "backend/compliance/rights_registry.yaml"):
        self.registry = self._load_registry(registry_path)

    def check_export_permission(self, provider: str, user_tier: str) -> bool:
        """Check if export is allowed for provider."""
        rights = self.registry.get(provider)
        if not rights:
            return False

        # Check export permission
        if rights["export"] == "restricted":
            # Check if user has license
            return rights.get("require_license") and self._has_license(user_tier, provider)
        elif rights["export"] == "allow":
            return True
        else:
            return False

    def get_attribution(self, provider: str) -> str:
        """Get attribution text for provider."""
        rights = self.registry.get(provider, {})
        return rights.get("attribution", "")

    def apply_watermark(self, provider: str, user_tier: str, data: Any) -> Any:
        """Apply watermark if required."""
        rights = self.registry.get(provider, {})
        if user_tier == "dev" and "dev_tier_watermark" in rights:
            # Apply watermark
            data["__watermark__"] = rights["dev_tier_watermark"]
        return data
```

---

### Task 6: Pack Health Endpoint
**Owner**: HEALTH_AGENT
**Priority**: P1 (High - Required for S1-W2 gate)
**Duration**: 4 hours
**Dependencies**: Task 1 (Executor), Phase 1 (scheduler)

**Deliverables**:
1. `backend/api/health.py` (extended to 300 lines)
   - GET `/health/pack` endpoint
   - Pack status aggregation
   - Freshness validation
   - Error reporting

**Health Response Schema** (from PRODUCT_SPEC):
```json
{
  "status": "warming|fresh|error",
  "pack_id": "2024-10-21-WM4PM-CAD",
  "updated_at": "2024-10-21T00:12:00Z",
  "prewarm_done": true,
  "is_fresh": true
}
```

**Acceptance Criteria**:
- ✅ `/health/pack` returns real pack status from DB
- ✅ Status = "warming" when `is_fresh = false`
- ✅ Status = "fresh" when `is_fresh = true`
- ✅ Status = "error" when reconciliation failed

**Implementation Stub**:
```python
# backend/api/health.py
@app.get("/health/pack")
async def pack_health():
    """Get pricing pack health status."""
    # Get latest pack from DB
    pack = await db.get_latest_pricing_pack()

    if not pack:
        return {
            "status": "error",
            "error": "No pricing pack found",
        }

    # Determine status
    if pack.reconciliation_failed:
        status = "error"
    elif pack.is_fresh:
        status = "fresh"
    else:
        status = "warming"

    return {
        "status": status,
        "pack_id": pack.id,
        "updated_at": pack.updated_at.isoformat(),
        "prewarm_done": pack.prewarm_done,
        "is_fresh": pack.is_fresh,
    }
```

---

## Parallel Execution Strategy

### Week 1 (Days 1-3): Foundation Layer
**Day 1**:
- Task 1: Executor API (EXECUTOR_AGENT) - 8 hours
- Task 6: Pack Health Endpoint (HEALTH_AGENT) - 4 hours

**Day 2**:
- Task 2: Pattern Orchestrator (PATTERN_AGENT) - 8 hours

**Day 3**:
- Task 3: Agent Runtime (RUNTIME_AGENT) - 8 hours

### Week 2 (Days 4-5): Observability + Rights
**Day 4**:
- Task 4: Observability (OBSERVABILITY_AGENT) - 6 hours
- Task 5: Rights Enforcement (RIGHTS_AGENT) - 6 hours

**Day 5**:
- Integration testing
- Acceptance gate validation
- Documentation

**Total**: 40 hours over 5 days

---

## Critical Path Dependencies

```
Task 1 (Executor) ─┬─→ Task 2 (Orchestrator) ──→ Task 3 (Runtime)
                   │                                     │
                   ├─→ Task 4 (Observability) ──────────┤
                   │                                     │
                   ├─→ Task 5 (Rights) ─────────────────┤
                   │                                     │
                   └─→ Task 6 (Health) ──────────────────┘
                                                         │
                                                         ▼
                                            Integration Testing
```

**Critical Path**: Task 1 → Task 2 → Task 3 (24 hours)
**Parallel Streams**: Task 4, Task 5, Task 6 can run concurrently with Task 3

---

## Acceptance Gates (S1-W2)

| Gate | Requirement | Owner | Validation |
|------|-------------|-------|------------|
| **Freshness Gate** | Executor blocks when pack warming (503) | EXECUTOR_AGENT | Integration test |
| **OTel Traces** | Traces visible in Jaeger with metadata | OBSERVABILITY_AGENT | Manual verification |
| **Prometheus Metrics** | API latency histogram scraped | OBSERVABILITY_AGENT | `/metrics` endpoint |
| **Rights Enforcement** | NewsAPI export blocked in staging | RIGHTS_AGENT | Rights drill test |
| **Pack Health** | `/health/pack` returns fresh status | HEALTH_AGENT | Integration test |

---

## Implementation Order

### Phase 2.1: Executor + Health (Day 1)
1. Create `backend/core/types.py` (RequestCtx, ExecReq, ExecResp)
2. Create `backend/api/executor.py` (execute endpoint)
3. Create `backend/api/health.py` (pack health endpoint)
4. Create `backend/db/pricing_pack_queries.py` (DB queries for pack status)
5. Test: `/v1/execute` blocks when pack warming
6. Test: `/health/pack` returns real status

### Phase 2.2: Pattern Orchestrator (Day 2)
1. Create `backend/patterns/orchestrator.py` (DAG runner)
2. Create `backend/patterns/loader.py` (pattern loading)
3. Create `backend/patterns/portfolio_overview.json` (test pattern)
4. Test: Pattern loads from JSON
5. Test: Steps execute sequentially
6. Test: State passed between steps

### Phase 2.3: Agent Runtime (Day 3)
1. Create `backend/app/agents/runtime.py` (capability routing)
2. Create `backend/app/agents/financial_analyst.py` (implement capabilities)
3. Create `backend/app/agents/macro_hound.py` (implement capabilities)
4. Test: Runtime registers agents
5. Test: Runtime resolves capability → agent
6. Test: Agent methods invoked correctly

### Phase 2.4: Observability (Day 4)
1. Create `backend/observability/tracing.py` (OTel setup)
2. Create `backend/observability/metrics.py` (Prometheus)
3. Create `backend/observability/errors.py` (Sentry)
4. Integrate: Add tracing to executor, orchestrator, runtime
5. Test: Traces visible in Jaeger
6. Test: Metrics scraped from `/metrics`

### Phase 2.5: Rights Enforcement (Day 4)
1. Create `backend/compliance/rights_enforcer.py` (enforcement logic)
2. Create `backend/compliance/rights_registry.yaml` (provider rights)
3. Create `backend/api/export.py` (export endpoints)
4. Integrate: Add rights checks to provider facades
5. Test: NewsAPI export blocked
6. Test: FRED export allowed with attribution

### Phase 2.6: Integration Testing (Day 5)
1. End-to-end test: UI → Executor → Orchestrator → Runtime → Agent
2. Freshness gate test: Block when warming, allow when fresh
3. Observability test: Verify traces + metrics
4. Rights drill test: Export blocking + attribution
5. Load test: 100 concurrent requests
6. Documentation: Update ARCHITECTURE.md

---

## File Manifest (Phase 2)

### API Layer (900 lines)
- `backend/api/executor.py` (400 lines) - Executor API with freshness gate
- `backend/api/health.py` (300 lines) - Pack health endpoint
- `backend/api/export.py` (200 lines) - Export endpoints with rights gate

### Core (300 lines)
- `backend/core/types.py` (300 lines) - RequestCtx, ExecReq, ExecResp

### Patterns (700 lines)
- `backend/patterns/orchestrator.py` (500 lines) - DAG runner
- `backend/patterns/loader.py` (200 lines) - Pattern loading

### Agents (1,400 lines)
- `backend/app/agents/runtime.py` (400 lines) - Capability routing
- `backend/app/agents/financial_analyst.py` (600 lines) - Financial capabilities
- `backend/app/agents/macro_hound.py` (400 lines) - Macro capabilities

### Observability (650 lines)
- `backend/observability/tracing.py` (300 lines) - OpenTelemetry
- `backend/observability/metrics.py` (200 lines) - Prometheus
- `backend/observability/errors.py` (150 lines) - Sentry

### Compliance (450 lines)
- `backend/compliance/rights_enforcer.py` (400 lines) - Rights enforcement
- `backend/compliance/rights_registry.yaml` (50 lines) - Provider rights

### Patterns (100 lines)
- `backend/patterns/portfolio_overview.json` (100 lines) - Test pattern

### Total: 13 files, 4,500 lines

---

## Risk Mitigation

### Risk 1: Agent Runtime Complexity
**Risk**: Capability routing may be complex with multiple agents
**Mitigation**: Start with 2 agents (financial_analyst, macro_hound), add more later
**Fallback**: Hardcode capability → agent mapping for MVP

### Risk 2: Observability Overhead
**Risk**: OTel/Prom may add latency
**Mitigation**: Use sampling (10% trace rate), batch span exports
**Fallback**: Disable tracing for MVP, enable in staging

### Risk 3: Rights Enforcement Edge Cases
**Risk**: Complex rules for multi-provider exports
**Mitigation**: Start with simple allow/block rules, add complexity later
**Fallback**: Block all exports except FRED for MVP

### Risk 4: Pattern Orchestrator Edge Cases
**Risk**: Complex DAG dependencies (parallel, conditional)
**Mitigation**: Start with sequential-only execution, add parallelism later
**Fallback**: Hardcode pattern execution for MVP

---

## Success Criteria

**Phase 2 Complete When**:
- ✅ All 6 tasks delivered
- ✅ All S1-W2 acceptance gates passed
- ✅ Integration tests green
- ✅ Documentation complete

**Ready for Phase 3 When**:
- ✅ Executor API stable (no critical bugs)
- ✅ Pattern Orchestrator executes 3+ patterns
- ✅ Agent Runtime routes 5+ capabilities
- ✅ Observability traces visible in Jaeger
- ✅ Rights enforcement blocks unauthorized exports

---

## Next Phase: Sprint 2 Week 3

**Phase 3: Metrics + Currency Attribution**

Deliverables:
- TWR/MWR/Sharpe calculations (implement TODO stubs from Phase 1)
- Currency attribution (local/FX/interaction with ±0.1bp invariant)
- Continuous aggregates (30-day rolling vol, TimescaleDB)
- Property tests (currency identity, FX triangulation)

**Estimated Duration**: 5 days (40 hours)

---

**Phase 2 Status**: 🔄 READY TO START
**Prerequisites**: ✅ Phase 1 Complete
**Agent Orchestration**: ✅ Ready (6 agents assigned)
**Critical Path**: Task 1 → Task 2 → Task 3 (24 hours)

**Last Updated**: 2025-10-22
