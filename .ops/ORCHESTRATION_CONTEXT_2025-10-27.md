# DawsOS Agent Orchestration Context - October 27, 2025

## Executive Summary

**System Status**: ~80-85% Complete (Phase 2.75 - Advanced Macro Features Ready)
**Architecture**: Trinity 3.0 - Pattern-based multi-agent execution
**Current Focus**: P1 remaining work (Optimizer integration) + P2 polish (Charts, Observability)

### Key Achievement: All 7 Agents Registered ✅

As of 2025-10-27, **ALL** agents are registered in executor.py:
1. **financial_analyst** (18 capabilities) - Portfolio data, metrics, risk analysis
2. **macro_hound** (13 capabilities) - Regime detection, cycles, scenarios, DaR
3. **data_harvester** (6 capabilities) - Provider integration (FMP, Polygon, FRED, NewsAPI)
4. **claude** (4 capabilities) - AI explanations and analysis
5. **ratings** (4 capabilities) - Buffett-style quality ratings
6. **optimizer** (4 capabilities) - Portfolio optimization and rebalancing
7. **reports** (3 capabilities) - PDF/CSV export generation

**Total**: 52 declared capabilities across 7 agents

---

## How Agent Orchestration Works

### The Sacred Execution Path

```
UI Request → Executor API → Pattern Orchestrator → Agent Runtime → Agent → Service → Database
```

**NO** bypassing allowed. Every workflow must go through patterns.

### Step-by-Step Flow

#### 1. Pattern Definition (JSON)

Location: `backend/patterns/*.json` (12 patterns)

Example: [portfolio_overview.json](../backend/patterns/portfolio_overview.json)
```json
{
  "id": "portfolio_overview",
  "name": "Portfolio Overview",
  "category": "analysis",
  "inputs": {
    "portfolio_id": {"type": "uuid", "required": true}
  },
  "steps": [
    {
      "capability": "ledger.positions",
      "as": "positions",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}"}
    },
    {
      "capability": "pricing.apply_pack",
      "as": "valued_positions",
      "args": {
        "positions": "{{state.positions}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      }
    },
    {
      "capability": "metrics.compute_twr",
      "as": "perf_metrics",
      "args": {
        "positions": "{{state.valued_positions}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      }
    }
  ],
  "outputs": ["positions", "valued_positions", "perf_metrics"]
}
```

**Key Concepts**:
- **Template substitution**: `{{inputs.portfolio_id}}`, `{{state.positions}}`, `{{ctx.pricing_pack_id}}`
- **Step chaining**: Each step stores result with `"as": "key"` for next step
- **Immutable context**: `ctx.pricing_pack_id` and `ctx.ledger_commit_hash` ensure reproducibility

#### 2. Executor API Receives Request

File: [backend/app/api/executor.py](../backend/app/api/executor.py)

```python
POST /v1/execute
{
  "pattern_id": "portfolio_overview",
  "inputs": {"portfolio_id": "11111111-1111-1111-1111-111111111111"},
  "require_fresh": true,
  "asof_date": "2025-10-27"
}
```

**What Executor Does**:
1. ✅ **Freshness Gate**: Checks if pricing pack is fresh (blocks if stale)
2. ✅ **Context Construction**: Creates `RequestCtx` with:
   - `pricing_pack_id` (e.g., "PP_2025-10-27")
   - `ledger_commit_hash` (from reconciliation)
   - `trace_id`, `request_id` (for observability)
   - `user_id`, `portfolio_id` (from headers/inputs)
3. ✅ **Pattern Routing**: Calls `PatternOrchestrator.run_pattern()`

#### 3. Pattern Orchestrator Executes Steps

File: [backend/app/core/pattern_orchestrator.py](../backend/app/core/pattern_orchestrator.py)

**For each step**:
```python
# 1. Resolve template arguments
args = self._resolve_args(step["args"], state)
# {{state.positions}} → actual positions data
# {{ctx.pricing_pack_id}} → "PP_2025-10-27"

# 2. Route capability to agent runtime
result = await self.agent_runtime.execute_capability(
    capability="ledger.positions",
    ctx=ctx,
    state=state,
    **args  # portfolio_id="11111111-..."
)

# 3. Store result in state for next step
state["positions"] = result
```

**Trace Building**:
- Tracks every step execution
- Records agents used, capabilities called, data sources
- Includes timing, errors, skipped steps
- Returned in `trace` field of response

#### 4. Agent Runtime Routes to Correct Agent

File: [backend/app/core/agent_runtime.py](../backend/app/core/agent_runtime.py)

```python
# Capability map (built during registration)
capability_map = {
    "ledger.positions": "financial_analyst",
    "pricing.apply_pack": "financial_analyst",
    "metrics.compute_twr": "financial_analyst",
    "macro.detect_regime": "macro_hound",
    "ratings.moat_strength": "ratings",
    # ... 52 total capabilities
}

# Route to agent
agent_name = capability_map["ledger.positions"]  # → "financial_analyst"
agent = agents[agent_name]

# Execute capability
result = await agent.execute("ledger.positions", ctx, state, portfolio_id="...")
```

**Circuit Breaker**:
- Tracks agent failures (threshold: 5 failures)
- Opens circuit on threshold (blocks requests for 60s)
- Half-open recovery state
- Prevents cascading failures

**Rights Enforcement** (NEW):
- Extracts data sources from result metadata
- Adds `__attributions__` field with provider credits
- Validates against rights registry

#### 5. Agent Executes Method

File: [backend/app/agents/financial_analyst.py](../backend/app/agents/financial_analyst.py)

**Capability Declaration**:
```python
def get_capabilities(self) -> List[str]:
    return [
        "ledger.positions",
        "pricing.apply_pack",
        # ... 16 more capabilities
    ]
```

**Capability Execution**:
```python
async def ledger_positions(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get portfolio positions from Beancount ledger.

    Capability: ledger.positions
    """
    portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

    logger.info(f"ledger.positions: portfolio_id={portfolio_id_uuid}")

    # Call service
    from backend.app.services.ledger import get_ledger_service
    ledger_service = get_ledger_service()

    result = await ledger_service.get_positions(
        portfolio_id_uuid,
        asof_date=ctx.asof_date or date.today()
    )

    # Attach metadata for tracing
    metadata = self._create_metadata(
        source=f"ledger:{ctx.ledger_commit_hash}",
        asof=ctx.asof_date,
        ttl=300  # Cache for 5 minutes
    )

    return self._attach_metadata(result, metadata)
```

**Key Points**:
- Method name: `capability.replace(".", "_")` → `ledger.positions` → `ledger_positions`
- Thin agent: Calls service, attaches metadata, returns
- Metadata includes: source, asof date, TTL, pricing_pack_id, ledger_commit_hash

#### 6. Service Performs Business Logic

File: [backend/app/services/ledger.py](../backend/app/services/ledger.py)

```python
async def get_positions(
    self,
    portfolio_id: UUID,
    asof_date: date
) -> Dict[str, Any]:
    """
    Get portfolio positions from lots table.

    Returns:
        Dict with positions array and summary
    """
    async with self.db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                l.security_id,
                s.symbol,
                SUM(l.quantity) as quantity,
                l.currency,
                l.acquisition_date
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = $1
              AND l.acquisition_date <= $2
              AND (l.disposition_date IS NULL OR l.disposition_date > $2)
            GROUP BY l.security_id, s.symbol, l.currency, l.acquisition_date
            HAVING SUM(l.quantity) > 0
        """, portfolio_id, asof_date)

        positions = [dict(row) for row in rows]

        return {
            "positions": positions,
            "count": len(positions),
            "asof_date": str(asof_date)
        }
```

#### 7. Response Assembly

**Pattern Orchestrator** combines outputs:
```python
return {
    "data": {
        "positions": [...],
        "valued_positions": [...],
        "perf_metrics": {...}
    },
    "charts": [...],
    "trace": {
        "pattern_id": "portfolio_overview",
        "pricing_pack_id": "PP_2025-10-27",
        "ledger_commit_hash": "abc123",
        "agents_used": ["financial_analyst"],
        "capabilities_used": ["ledger.positions", "pricing.apply_pack", "metrics.compute_twr"],
        "sources": ["ledger:abc123", "pricing_pack:PP_2025-10-27"],
        "steps": [...]
    }
}
```

**Executor API** adds HTTP wrapper:
```json
{
  "request_id": "uuid",
  "timestamp": "2025-10-27T10:00:00Z",
  "result": { ... },
  "metadata": {
    "pricing_pack_id": "PP_2025-10-27",
    "ledger_commit_hash": "abc123"
  }
}
```

---

## Agent Capability Matrix

### 1. Financial Analyst (18 capabilities)

| Capability | Status | Service Used |
|------------|--------|--------------|
| `ledger.positions` | ✅ | LedgerService |
| `pricing.apply_pack` | ✅ | PricingService |
| `metrics.compute` | ✅ | MetricsQueries (wrapper) |
| `metrics.compute_twr` | ✅ | MetricsQueries |
| `metrics.compute_sharpe` | ✅ | MetricsQueries |
| `attribution.currency` | ✅ | AttributionService |
| `charts.overview` | ⚠️ | PlaceholderService (P2) |
| `risk.compute_factor_exposures` | ✅ | RiskService |
| `risk.get_factor_exposure_history` | ✅ | RiskService |
| `risk.overlay_cycle_phases` | ✅ | RiskService + CyclesService |
| `get_position_details` | ⚠️ | PlaceholderService (P2) |
| `compute_position_return` | ✅ | LedgerService + MetricsQueries |
| `compute_portfolio_contribution` | ✅ | AttributionService |
| `compute_position_currency_attribution` | ✅ | AttributionService |
| `compute_position_risk` | ✅ | RiskService |
| `get_transaction_history` | ✅ | LedgerService |
| `get_security_fundamentals` | ⚠️ | DataHarvester (delegation) |
| `get_comparable_positions` | ⚠️ | PlaceholderService (P2) |

### 2. Macro Hound (13 capabilities)

| Capability | Status | Service Used |
|------------|--------|--------------|
| `macro.detect_regime` | ✅ | MacroService |
| `macro.compute_cycles` | ✅ | CyclesService |
| `macro.get_indicators` | ✅ | MacroService + FRED Provider |
| `macro.run_scenario` | ✅ | ScenariosService (22 scenarios seeded) |
| `macro.compute_dar` | ✅ | ScenariosService (regime-conditional) |
| `macro.get_regime_history` | ✅ | MacroService |
| `macro.detect_trend_shifts` | ✅ | MacroService |
| `cycles.compute_short_term` | ✅ | CyclesService |
| `cycles.compute_long_term` | ✅ | CyclesService |
| `cycles.compute_empire` | ✅ | CyclesService (Dalio framework) |
| `cycles.aggregate_overview` | ✅ | CyclesService |
| `scenarios.deleveraging_austerity` | ✅ | ScenariosService |
| `scenarios.deleveraging_default` | ✅ | ScenariosService |

### 3. Data Harvester (6 capabilities)

| Capability | Status | Service Used |
|------------|--------|--------------|
| `provider.fetch_quote` | ✅ | Polygon Provider |
| `provider.fetch_fundamentals` | ✅ | FMP Provider |
| `provider.fetch_news` | ✅ | NewsAPI Provider |
| `provider.fetch_macro` | ✅ | FRED Provider |
| `provider.fetch_ratios` | ✅ | FMP Provider |
| `fundamentals.load` | ✅ | FMP Provider + Transformation Pipeline |

### 4. Claude Agent (4 capabilities)

| Capability | Status | Service Used |
|------------|--------|--------------|
| `claude.explain` | ⚠️ | Anthropic API (placeholder if no key) |
| `claude.summarize` | ⚠️ | Anthropic API (placeholder if no key) |
| `claude.analyze` | ⚠️ | Anthropic API (placeholder if no key) |
| `ai.explain` | ⚠️ | Anthropic API (alias for claude.explain) |

### 5. Ratings Agent (4 capabilities)

| Capability | Status | Service Used |
|------------|--------|--------------|
| `ratings.dividend_safety` | ✅ | RatingsService + rating_rubrics table |
| `ratings.moat_strength` | ✅ | RatingsService + rating_rubrics table |
| `ratings.resilience` | ✅ | RatingsService + rating_rubrics table |
| `ratings.aggregate` | ✅ | RatingsService (weighted composite) |

### 6. Optimizer Agent (4 capabilities)

| Capability | Status | Service Used |
|------------|--------|--------------|
| `optimizer.propose_trades` | ⚠️ | OptimizerService (NOT wired to patterns) |
| `optimizer.analyze_impact` | ⚠️ | OptimizerService (NOT wired to patterns) |
| `optimizer.suggest_hedges` | ⚠️ | OptimizerService (NOT wired to patterns) |
| `optimizer.suggest_deleveraging_hedges` | ⚠️ | OptimizerService (NOT wired to patterns) |

**Blocker**: Riskfolio-Lib integration incomplete (P1-1, 40h remaining)

### 7. Reports Agent (3 capabilities)

| Capability | Status | Service Used |
|------------|--------|--------------|
| `reports.render_pdf` | ⚠️ | ReportsService (WeasyPrint not tested) |
| `reports.export_csv` | ✅ | ReportsService |
| `reports.export_excel` | 🔜 | ReportsService (future) |

**Blocker**: WeasyPrint templates untested (P1-2, 16h remaining)

---

## Pattern Status (12 Patterns)

### ✅ Fully Working Patterns (7)

1. **portfolio_overview** - Portfolio snapshot with metrics
2. **macro_trend_monitor** - Regime detection + FRED indicators
3. **portfolio_cycle_risk** - Regime-conditional DaR calculation
4. **portfolio_scenario_analysis** - 22 stress test scenarios
5. **macro_cycles_overview** - Dalio cycle analysis
6. **cycle_deleveraging_scenarios** - Deleveraging stress tests
7. **news_impact_analysis** - NewsAPI integration

### ⚠️ Partially Working Patterns (4)

8. **buffett_checklist** - Works but UI not surfacing results properly
9. **holding_deep_dive** - Works but placeholder charts (P2)
10. **export_portfolio_report** - Works but PDF generation untested (P1-2)
11. **portfolio_macro_overview** - Works but scenario persistence missing

### 🔴 Blocked Patterns (1)

12. **policy_rebalance** - Blocked on optimizer integration (P1-1, 40h)

---

## Remaining Work Breakdown

### P0 (Critical - Must Ship)

**Status**: ✅ ALL COMPLETE (Rating rubrics, FMP transformation, database init)

### P1 (High Priority - Next Sprint)

#### P1-1: Optimizer Integration (40 hours)
**Status**: ⚠️ Service exists (1,283 LOC), agent exists (514 LOC), NOT wired to patterns

**Tasks**:
1. Install riskfolio-lib dependency (1h)
2. Test optimizer service methods in isolation (4h)
3. Wire `policy_rebalance` pattern to `optimizer.propose_trades` (8h)
4. Test pattern execution end-to-end (4h)
5. Add optimizer UI screen (12h)
6. Create integration tests (8h)
7. Documentation and examples (3h)

**Acceptance**:
- `policy_rebalance` pattern executes successfully
- Returns proposed trades with Riskfolio-Lib optimization
- UI screen displays rebalance recommendations
- Integration tests passing

#### P1-2: Rights-Enforced PDF Exports (16 hours)
**Status**: ⚠️ Service exists (584 LOC), templates exist, WeasyPrint not tested

**Tasks**:
1. Install weasyprint dependency (1h)
2. Test PDF generation with templates (4h)
3. Test rights enforcement (attribution footers, watermarks) (4h)
4. Wire to `export_portfolio_report` pattern (4h)
5. Add export tests (3h)

**Acceptance**:
- PDF exports generate successfully
- Rights attribution included in footers
- Watermarks applied for restricted data
- Export tests passing

#### P1-3: Authentication & RBAC (20 hours)
**Status**: ⚠️ Service exists (399 LOC), NOT wired to executor

**Tasks**:
1. Replace stub X-User-ID with JWT validation middleware (8h)
2. Wire RBAC permission checks to pattern execution (6h)
3. Test role enforcement (VIEWER/USER/MANAGER/ADMIN) (4h)
4. Audit logging for sensitive operations (2h)

**Acceptance**:
- JWT tokens required for all /v1/execute calls
- Role-based access enforced
- Audit log populated for sensitive operations
- Security tests passing

#### P1-4: Nightly Job Orchestration Testing (12 hours)
**Status**: ⚠️ Scheduler enhanced (545 LOC), jobs exist, NOT tested end-to-end

**Tasks**:
1. Test sacred job order in isolation (4h)
2. Test pack freshness gate (3h)
3. Test error handling (job failures, retries) (3h)
4. Documentation of nightly workflow (2h)

**Acceptance**:
- Jobs execute in correct order
- Pack freshness gate enforced
- Failed jobs don't break pipeline
- Runbook documented

**Total P1**: 88 hours (11 days with 1 engineer, or 5.5 days with 2 engineers)

### P2 (Medium Priority - Next 2 Sprints)

#### P2-1: Chart Placeholders (60 hours)
Implement visualization capabilities for holding_deep_dive pattern

#### P2-2: Observability Wiring (24 hours)
Wire OpenTelemetry exporter, Prometheus dashboards, alert routing

#### P2-3: Provider Integration Hardening (16 hours)
Test providers under failure scenarios (rate limits, outages, malformed data)

**Total P2**: 100 hours (12.5 days with 1 engineer)

---

## How to Add a New Capability (Checklist)

### 1. Decide on Capability Name
- Use dot notation: `category.operation`
- Examples: `risk.compute_var`, `alerts.create_threshold`

### 2. Check if Service Method Exists
```bash
grep -r "def compute_var" backend/app/services/risk.py
```
If exists, skip to step 4. If not, implement service first (step 3).

### 3. Implement Service Method (if needed)
```python
# backend/app/services/risk.py
async def compute_var(
    portfolio_id: UUID,
    confidence: float = 0.95
) -> Dict[str, Any]:
    """Compute Value at Risk."""
    # Business logic here
    return {"var_amount": Decimal("1000.00"), "var_pct": Decimal("0.02")}
```

### 4. Add to Agent's get_capabilities()
```python
# backend/app/agents/financial_analyst.py
def get_capabilities(self) -> List[str]:
    return [
        "ledger.positions",
        # ... existing capabilities
        "risk.compute_var",  # ADD HERE
    ]
```

### 5. Implement Agent Method
```python
# backend/app/agents/financial_analyst.py
async def risk_compute_var(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    confidence: float = 0.95,
) -> Dict[str, Any]:
    """
    Compute Value at Risk.

    Capability: risk.compute_var
    """
    portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

    logger.info(f"risk.compute_var: portfolio_id={portfolio_id_uuid}")

    # Call service
    from backend.app.services.risk import get_risk_service
    risk_service = get_risk_service()

    result = await risk_service.compute_var(portfolio_id_uuid, confidence)

    # Attach metadata
    metadata = self._create_metadata(
        source=f"risk_service:{ctx.pricing_pack_id}",
        asof=ctx.asof_date,
        ttl=300
    )

    return self._attach_metadata(result, metadata)
```

### 6. Add to Pattern (if needed)
```json
// backend/patterns/portfolio_risk_analysis.json
{
  "id": "portfolio_risk_analysis",
  "steps": [
    {
      "capability": "risk.compute_var",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "confidence": 0.95
      },
      "as": "var_1d"
    }
  ],
  "outputs": ["var_1d"]
}
```

### 7. Test End-to-End
```bash
# Test capability directly
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_risk_analysis",
    "inputs": {"portfolio_id": "11111111-1111-1111-1111-111111111111"}
  }'
```

### 8. Verification Checklist
- [ ] Service method implemented and tested
- [ ] Capability added to `get_capabilities()`
- [ ] Agent method implemented (name: dots → underscores)
- [ ] Method attaches metadata
- [ ] Pattern JSON created/updated
- [ ] Python syntax verified: `python3 -m py_compile agent_file.py`
- [ ] End-to-end test passes

---

## Debugging Guide

### Problem: "No agent registered for capability X"

**Check**:
1. Is capability declared in `get_capabilities()`?
2. Is agent registered in executor.py?
3. Is method name correct? (`capability.replace(".", "_")`)

```bash
# Verify capability declaration
grep -A 15 "def get_capabilities" backend/app/agents/*.py | grep "your.capability"

# Verify agent registration
grep "register_agent" backend/app/api/executor.py

# Verify method exists
grep "async def your_capability" backend/app/agents/*.py
```

### Problem: "Capability execution fails"

**Check**:
1. Does service method exist and work?
2. Is database pool accessible?
3. Are method arguments correct?

```bash
# Test service directly
python3 -c "
from backend.app.services.your_service import get_service
import asyncio
service = get_service()
result = asyncio.run(service.your_method(args))
print(result)
"
```

### Problem: "Pattern references wrong capability name"

**Check**: Pattern JSON uses dots, agent method uses underscores
```json
// Pattern uses: "capability": "risk.compute_var"
// Agent method:  async def risk_compute_var(...)
```

### Problem: "Circuit breaker open"

**Check**: Agent failure count exceeded threshold
```bash
# Check circuit breaker status
curl http://localhost:8000/health/agents
```

**Fix**: Reset circuit breaker or fix underlying agent issue

---

## Key Files Reference

### Core Infrastructure
- [backend/app/api/executor.py](../backend/app/api/executor.py) - Main entry point, agent registration
- [backend/app/core/pattern_orchestrator.py](../backend/app/core/pattern_orchestrator.py) - Pattern execution
- [backend/app/core/agent_runtime.py](../backend/app/core/agent_runtime.py) - Capability routing
- [backend/app/agents/base_agent.py](../backend/app/agents/base_agent.py) - Base agent class

### Agent Files (7)
- [backend/app/agents/financial_analyst.py](../backend/app/agents/financial_analyst.py) - 63KB, 18 capabilities
- [backend/app/agents/macro_hound.py](../backend/app/agents/macro_hound.py) - 37KB, 13 capabilities
- [backend/app/agents/data_harvester.py](../backend/app/agents/data_harvester.py) - 53KB, 6 capabilities
- [backend/app/agents/claude_agent.py](../backend/app/agents/claude_agent.py) - 8.6KB, 4 capabilities
- [backend/app/agents/ratings_agent.py](../backend/app/agents/ratings_agent.py) - 20KB, 4 capabilities
- [backend/app/agents/optimizer_agent.py](../backend/app/agents/optimizer_agent.py) - 19KB, 4 capabilities
- [backend/app/agents/reports_agent.py](../backend/app/agents/reports_agent.py) - 10KB, 3 capabilities

### Service Files (20+)
- [backend/app/services/ledger.py](../backend/app/services/ledger.py) - 657 LOC
- [backend/app/services/macro.py](../backend/app/services/macro.py) - 647 LOC
- [backend/app/services/ratings.py](../backend/app/services/ratings.py) - 584 LOC
- [backend/app/services/optimizer.py](../backend/app/services/optimizer.py) - 1,283 LOC
- [backend/app/services/scenarios.py](../backend/app/services/scenarios.py) - 538 LOC
- [backend/app/services/risk.py](../backend/app/services/risk.py) - 526 LOC
- ... (14 more services)

### Pattern Files (12)
All in [backend/patterns/](../backend/patterns/)

---

## Success Metrics

### Current State (2025-10-27)
- ✅ All 7 agents registered
- ✅ 52 capabilities declared
- ✅ 12 patterns defined
- ✅ 7/12 patterns fully working
- ✅ P0 remediation complete
- ⚠️ P1 25% complete (3 of 4 items remaining)
- ⏳ P2 not started

### Target State (2 weeks)
- ✅ All 12 patterns working
- ✅ P1 100% complete
- ✅ Coverage ≥ 70%
- ✅ System ready for staging deployment

### Production Ready (4 weeks)
- ✅ P2 100% complete
- ✅ All charts implemented
- ✅ Observability fully wired
- ✅ Provider hardening complete
- ✅ Coverage ≥ 80%

---

**Last Updated**: October 27, 2025
**Purpose**: Comprehensive context for AI assistants working on DawsOS orchestration
**Next Review**: After P1 completion
