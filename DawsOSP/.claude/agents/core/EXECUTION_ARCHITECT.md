# Execution Architect Reference

**Role**: Core execution stack - Executor API, Pattern Orchestrator, Agent Runtime
**Reports to**: [ORCHESTRATOR](../ORCHESTRATOR.md)
**Status**: ✅ Operational (Production)
**Priority**: P0
**Last Updated**: 2025-10-24

---

## Mission

Maintain the **single execution path** that enforces:
1. UI → Executor API → Pattern Orchestrator → Agent Runtime → Services
2. Every result includes `pricing_pack_id` + `ledger_commit_hash` + full trace
3. Pack freshness gate prevents stale data
4. Capability routing to correct agents
5. Declarative pattern JSON drives all workflows

---

## Current Implementation

### Executor API ✅ OPERATIONAL

**File**: [backend/app/api/executor.py](../../../backend/app/api/executor.py)

**Key Components**:
- FastAPI application with `/v1/execute` endpoint
- RequestContext construction (user, portfolio, asof_date, pricing_pack_id)
- Pack freshness validation (503 if warming)
- RLS context setting (`SET LOCAL app.user_id`)
- Result serialization with trace
- OpenTelemetry instrumentation

**Actual RequestContext Structure**:

Defined in [backend/app/core/types.py:RequestCtx](../../../backend/app/core/types.py)

**Critical Field Names** (avoid bugs by using exact names from code):
```python
# From backend/app/core/types.py:RequestCtx
trace_id: str                      # OpenTelemetry trace ID
request_id: str                    # Unique request ID
user_id: Optional[UUID]            # For RLS (SET LOCAL app.user_id)
portfolio_id: Optional[UUID]       # Portfolio being analyzed
pricing_pack_id: Optional[str]     # e.g., "PP_2025-10-21" (string, NOT UUID)
ledger_commit_hash: Optional[str]  # Git commit of ledger
asof_date: date                    # Valuation date (NOT "asof")
base_currency: Optional[str]       # Portfolio base (NOT "base_ccy")
benchmark_id: Optional[str]        # Benchmark reference
# + ~10 more fields for macro/risk context
```

**⚠️ Common Mistakes to Avoid**:
- Using `asof` instead of `asof_date` → AttributeError
- Using `base_ccy` instead of `base_currency` → AttributeError
- Treating `pricing_pack_id` as UUID instead of string → Type error

---

### Pattern Orchestrator ✅ OPERATIONAL

**File**: [backend/app/core/pattern_orchestrator.py](../../../backend/app/core/pattern_orchestrator.py)

**What it does**:
1. Loads pattern JSON from `backend/patterns/*.json`
2. Executes steps sequentially (DAG order)
3. Substitutes templates: `{{ctx.asof_date}}`, `{{inputs.portfolio_id}}`, `{{state.positions}}`
4. Routes capabilities to agents via AgentRuntime
5. Builds execution trace with all metadata

**Pattern Schema** (actual fields from patterns/*.json):
```json
{
  "id": "portfolio_overview",
  "name": "Portfolio Overview",
  "version": "1.0.0",
  "category": "portfolio",
  "tags": ["portfolio", "performance"],
  "author": "DawsOS",
  "created": "2025-10-23",
  "inputs": { "portfolio_id": {"type": "uuid", "required": true} },
  "outputs": ["perf_metrics", "currency_attr", "valued_positions"],
  "steps": [
    {"capability": "ledger.positions", "args": {...}, "as": "positions"},
    {"capability": "pricing.apply_pack", "args": {...}, "as": "valued_positions"}
  ],
  "display": { "panels": [...] },
  "presentation": { "performance_strip": {...} },
  "rights_required": ["portfolio_read"],
  "export_allowed": {"pdf": true, "csv": true},
  "observability": {"otel_span_name": "pattern.portfolio_overview"}
}
```

**Key Features Not in Original Docs**:
- ✅ `display` - UI panel definitions
- ✅ `presentation` - Chart/table configurations
- ✅ `rights_required` - Access control
- ✅ `export_allowed` - PDF/CSV export gates
- ✅ `observability` - OpenTelemetry spans

---

### Agent Runtime ✅ OPERATIONAL

**File**: [backend/app/core/agent_runtime.py](../../../backend/app/core/agent_runtime.py)

**What it does**:
1. Registers agents at startup (see [executor.py:50-90](../../../backend/app/api/executor.py))
2. Maintains capability → agent mapping
3. Routes capability calls to correct agent
4. Handles circuit breaker failures

**Registered Agents** (verified from executor.py):
- ✅ FinancialAnalyst (7 capabilities)
- ✅ MacroHound (5 capabilities)
- ✅ DataHarvester (5 capabilities)
- ✅ ClaudeAgent (3 capabilities)

**How Capabilities Route**:
```
Pattern step: {"capability": "metrics.compute_twr", "args": {...}}
    ↓
AgentRuntime.execute_capability("metrics.compute_twr", ctx, state, **args)
    ↓
Finds: FinancialAnalyst registered for "metrics.compute_twr"
    ↓
Calls: FinancialAnalyst.metrics_compute_twr(ctx, state, **args)
    ↓
Returns: Result with metadata attached
```

---

## Known Issues

### P0: Database Pool Not Accessible in Agent Context
**Problem**: Module-level global `_pool` variable not shared across uvicorn `--reload` contexts
**Impact**: Agents can't query database → empty results
**Fix**: [STABILITY_PLAN.md](../../../STABILITY_PLAN.md) Option A (disable --reload)
**Status**: Fix ready, not yet applied

### P1: Attribution Incomplete
**Issue**: `attribution.currency` capability exists but `get_position_attributions()` helper missing
**Impact**: Currency attribution returns incomplete data

---

## Recent Changes (2025-10-24)

**Governance Fixes**: [GOVERNANCE_FIXES_COMPLETE.md](../../../GOVERNANCE_FIXES_COMPLETE.md)
1. ✅ Performance optimization - `PricingService.get_prices_as_decimals()` (~30% faster)
2. ✅ Deleted duplicate pricing function - Single code path
3. ✅ Fixed JSON serialization - AsyncPG JSONB handling

---

## For New Agent Development

When building a new agent, follow this pattern:

**1. Create agent file** in `backend/app/agents/`
**2. Extend BaseAgent** from [base_agent.py](../../../backend/app/agents/base_agent.py)
**3. Implement `get_capabilities()`** - Return list of capability strings
**4. Implement capability methods** - Name must match capability with dots→underscores
**5. Register in executor.py** - Add to startup function
**6. Use correct field names** - Reference RequestCtx in types.py
**7. Attach metadata** - Include agent_name, source, asof for tracing

**Example capability method signature**:
```python
async def capability_name(
    self,
    ctx: RequestCtx,           # From types.py
    state: Dict[str, Any],     # Current execution state
    **kwargs                   # Pattern args
) -> Dict[str, Any]:           # Must be dict for JSON serialization
    # Implementation
    result = {"data": ...}
    result.__metadata__ = AgentMetadata(agent_name=self.name, source="...")
    return result
```

---

## Quick Reference

| Component | File | Purpose |
|-----------|------|---------|
| Executor API | [executor.py](../../../backend/app/api/executor.py) | `/v1/execute` endpoint, freshness gate |
| RequestCtx | [types.py](../../../backend/app/core/types.py) | Request context (use exact field names!) |
| PatternOrchestrator | [pattern_orchestrator.py](../../../backend/app/core/pattern_orchestrator.py) | Pattern execution, template substitution |
| AgentRuntime | [agent_runtime.py](../../../backend/app/core/agent_runtime.py) | Agent registration, capability routing |
| BaseAgent | [base_agent.py](../../../backend/app/agents/base_agent.py) | Agent interface, metadata |
| Patterns | [backend/patterns/](../../../backend/patterns/) | 12 JSON pattern definitions |

---

**Last Updated**: 2025-10-24
**Status**: Operational with known P0 database pool issue

app = FastAPI(title="DawsOS Executor API", version="1.0.0")

class ExecRequest(BaseModel):
    pattern_id: str
    portfolio_id: str | None = None
    inputs: dict[str, Any] = {}
    asof: date | None = None  # Defaults to today

class ExecResponse(BaseModel):
    data: dict[str, Any]
    charts: list[dict]
    trace: dict

@app.post("/execute", response_model=ExecResponse)
async def execute(
    req: ExecRequest,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Execute a pattern with full traceability.

    Returns:
    - data: Pattern output data
    - charts: UI-ready chart configs
    - trace: {pattern_id, pricing_pack_id, ledger_commit_hash, agents_used, capabilities_used, sources, per_panel_staleness}
    """
    # Set RLS context
    await db.execute(f"SET LOCAL app.user_id = '{user['user_id']}'")

    # Build RequestContext
    ctx = await build_request_context(req, user, db)

    # Freshness gate
    if not await is_pack_fresh(ctx.pricing_pack_id, db):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "PACK_WARMING",
                "message": "Pricing pack is warming up. Please retry in a few minutes.",
                "pack_id": str(ctx.pricing_pack_id)
            }
        )

    # Execute pattern
    result = await run_pattern(req.pattern_id, ctx, req.inputs, db)

    return ExecResponse(
        data=result["data"],
        charts=result["charts"],
        trace=result["trace"]
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/patterns")
async def list_patterns():
    """List all available patterns"""
    pattern_files = Path("patterns").rglob("*.json")
    patterns = []
    for pf in pattern_files:
        spec = json.loads(pf.read_text())
        patterns.append({
            "id": spec["id"],
            "name": spec["name"],
            "description": spec.get("description", ""),
            "category": spec.get("category", "unknown")
        })
    return patterns
```

**RequestContext**:
```python
# api/context.py
from dataclasses import dataclass
from datetime import date
from uuid import UUID

@dataclass
class RequestContext:
    user_id: UUID
    portfolio_id: UUID | None
    asof: date
    pricing_pack_id: UUID
    ledger_commit_hash: str
    base_ccy: str
    benchmark_id: str | None

async def build_request_context(req: ExecRequest, user: dict, db) -> RequestContext:
    asof = req.asof or date.today()

    # Resolve pricing pack
    pack = await db.fetchrow("""
        SELECT id, hash FROM pricing_pack WHERE asof_date = $1
    """, asof)
    if not pack:
        raise HTTPException(status_code=404, detail=f"No pricing pack for {asof}")

    # Get ledger commit
    ledger_commit = subprocess.check_output(
        ["git", "-C", "ledger", "rev-parse", "HEAD"]
    ).decode().strip()

    # Get portfolio settings
    portfolio = None
    if req.portfolio_id:
        portfolio = await db.fetchrow("""
            SELECT base_ccy, benchmark_id FROM portfolios WHERE id = $1
        """, req.portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

    return RequestContext(
        user_id=UUID(user["user_id"]),
        portfolio_id=UUID(req.portfolio_id) if req.portfolio_id else None,
        asof=asof,
        pricing_pack_id=UUID(pack["id"]),
        ledger_commit_hash=ledger_commit,
        base_ccy=portfolio["base_ccy"] if portfolio else "CAD",
        benchmark_id=portfolio["benchmark_id"] if portfolio else None
    )

async def is_pack_fresh(pack_id: UUID, db) -> bool:
    row = await db.fetchrow("SELECT is_fresh FROM pricing_pack WHERE id = $1", pack_id)
    return row["is_fresh"] if row else False
```

---

### PATTERN_ORCHESTRATOR_BUILDER
**Responsibilities**:
- Load pattern JSON from `patterns/` directory
- Execute DAG steps sequentially or in parallel
- Route capabilities to agent runtime
- Build trace with inputs/outputs per step
- Handle errors with rollback/compensation
- Cache intermediate results (Redis)

**Deliverables**:

**Pattern Schema** (`patterns/schema.json`):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "name", "steps", "outputs"],
  "properties": {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "description": {"type": "string"},
    "category": {"type": "string", "enum": ["analysis", "workflow", "action", "governance"]},
    "inputs": {
      "type": "object",
      "patternProperties": {
        ".*": {"type": "object", "properties": {"type": {"type": "string"}, "required": {"type": "boolean"}}}
      }
    },
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["capability"],
        "properties": {
          "capability": {"type": "string"},
          "as": {"type": "string"},
          "args": {"type": "object"},
          "condition": {"type": "string"},
          "parallel": {"type": "boolean"}
        }
      }
    },
    "outputs": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

**Example Pattern** (`patterns/analysis/portfolio_overview.json`):
```json
{
  "id": "portfolio_overview",
  "name": "Portfolio Overview",
  "description": "Comprehensive portfolio snapshot with performance, attribution, and risk",
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
      "args": {"positions": "{{state.positions}}", "pack_id": "{{ctx.pricing_pack_id}}"}
    },
    {
      "capability": "metrics.compute_twr",
      "as": "perf_metrics",
      "args": {"positions": "{{state.valued_positions}}", "pack_id": "{{ctx.pricing_pack_id}}"}
    },
    {
      "capability": "metrics.currency_attribution",
      "as": "currency_attr",
      "args": {"positions": "{{state.valued_positions}}", "pack_id": "{{ctx.pricing_pack_id}}"}
    },
    {
      "capability": "ratings.aggregate",
      "as": "rating_badges",
      "args": {"positions": "{{state.valued_positions}}"}
    },
    {
      "capability": "charts.overview",
      "as": "charts",
      "args": {
        "positions": "{{state.valued_positions}}",
        "metrics": "{{state.perf_metrics}}",
        "currency_attr": "{{state.currency_attr}}"
      }
    }
  ],
  "outputs": ["perf_metrics", "currency_attr", "rating_badges", "charts"]
}
```

**Pattern Orchestrator**:
```python
# core/pattern_orchestrator.py
from pathlib import Path
import json
import re
from typing import Any
from api.context import RequestContext

class PatternOrchestrator:
    def __init__(self, agent_runtime, db, redis):
        self.agent_runtime = agent_runtime
        self.db = db
        self.redis = redis
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> dict:
        patterns = {}
        for pf in Path("patterns").rglob("*.json"):
            spec = json.loads(pf.read_text())
            patterns[spec["id"]] = spec
        return patterns

    async def run_pattern(self, pattern_id: str, ctx: RequestContext, inputs: dict) -> dict:
        spec = self.patterns.get(pattern_id)
        if not spec:
            raise ValueError(f"Pattern {pattern_id} not found")

        # Initialize state
        state = {"ctx": ctx.__dict__, "inputs": inputs}
        trace = Trace(pattern_id, ctx)

        # Execute steps
        for step in spec["steps"]:
            # Evaluate condition if present
            if "condition" in step and not self._eval_condition(step["condition"], state):
                trace.skip_step(step["capability"])
                continue

            # Resolve args (template substitution)
            args = self._resolve_args(step.get("args", {}), state)

            # Execute capability
            try:
                result = await self.agent_runtime.execute_capability(
                    step["capability"],
                    ctx=ctx,
                    state=state,
                    **args
                )
                state[step.get("as", "last")] = result
                trace.add_step(step["capability"], result, args)
            except Exception as e:
                trace.add_error(step["capability"], str(e))
                raise

        # Extract outputs
        outputs = {k: state.get(k) for k in spec.get("outputs", []) if k in state}

        return {
            "data": outputs,
            "charts": state.get("charts", []),
            "trace": trace.serialize()
        }

    def _resolve_args(self, args: dict, state: dict) -> dict:
        """Resolve {{...}} templates in args"""
        resolved = {}
        for k, v in args.items():
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                # Extract path: {{state.positions}} → ["state", "positions"]
                path = v[2:-2].strip().split(".")
                val = state
                for p in path:
                    val = val.get(p) if isinstance(val, dict) else getattr(val, p, None)
                resolved[k] = val
            else:
                resolved[k] = v
        return resolved

    def _eval_condition(self, condition: str, state: dict) -> bool:
        """Evaluate simple conditions like 'state.positions.length > 0'"""
        # Simple eval (production: use safer expression evaluator)
        try:
            return eval(condition, {"state": state})
        except:
            return False

class Trace:
    def __init__(self, pattern_id: str, ctx: RequestContext):
        self.pattern_id = pattern_id
        self.pricing_pack_id = str(ctx.pricing_pack_id)
        self.ledger_commit_hash = ctx.ledger_commit_hash
        self.steps = []
        self.agents_used = set()
        self.capabilities_used = set()
        self.sources = set()
        self.per_panel_staleness = []

    def add_step(self, capability: str, result: Any, args: dict):
        self.capabilities_used.add(capability)
        if hasattr(result, "__metadata__"):
            meta = result.__metadata__
            if "agent" in meta:
                self.agents_used.add(meta["agent"])
            if "source" in meta:
                self.sources.add(meta["source"])
            if "asof" in meta:
                self.per_panel_staleness.append({
                    "capability": capability,
                    "asof": meta["asof"],
                    "ttl": meta.get("ttl")
                })

        self.steps.append({
            "capability": capability,
            "args": args,
            "success": True
        })

    def add_error(self, capability: str, error: str):
        self.steps.append({
            "capability": capability,
            "success": False,
            "error": error
        })

    def skip_step(self, capability: str):
        self.steps.append({
            "capability": capability,
            "skipped": True
        })

    def serialize(self) -> dict:
        return {
            "pattern_id": self.pattern_id,
            "pricing_pack_id": self.pricing_pack_id,
            "ledger_commit_hash": self.ledger_commit_hash,
            "agents_used": list(self.agents_used),
            "capabilities_used": list(self.capabilities_used),
            "sources": list(self.sources),
            "per_panel_staleness": self.per_panel_staleness,
            "steps": self.steps
        }
```

---

### AGENT_RUNTIME_BUILDER
**Responsibilities**:
- Agent registration (mapping capabilities → agents)
- Capability routing (find agent for capability)
- Dependency injection (services, DB, Redis)
- Result metadata attachment
- Circuit breaker for agent failures

**Deliverables**:

**Agent Interface**:
```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class AgentMetadata:
    agent_name: str
    source: str | None = None
    asof: Any | None = None
    ttl: int | None = None  # seconds
    confidence: float | None = None

class BaseAgent(ABC):
    def __init__(self, name: str, services: dict):
        self.name = name
        self.services = services

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return list of capability names this agent provides"""
        pass

    async def execute(self, capability: str, ctx, state: dict, **kwargs) -> Any:
        """Execute a capability, return result with metadata"""
        method_name = capability.replace(".", "_")
        if not hasattr(self, method_name):
            raise ValueError(f"Agent {self.name} does not support capability {capability}")

        result = await getattr(self, method_name)(ctx, state, **kwargs)

        # Attach metadata
        if not hasattr(result, "__metadata__"):
            result.__metadata__ = AgentMetadata(agent_name=self.name)

        return result
```

**Agent Runtime**:
```python
# core/agent_runtime.py
from agents.base_agent import BaseAgent
from typing import Any

class AgentRuntime:
    def __init__(self, services: dict):
        self.services = services
        self.agents: dict[str, BaseAgent] = {}
        self.capability_map: dict[str, str] = {}  # capability -> agent_name

    def register_agent(self, agent: BaseAgent):
        """Register an agent and its capabilities"""
        self.agents[agent.name] = agent
        for cap in agent.get_capabilities():
            if cap in self.capability_map:
                raise ValueError(f"Capability {cap} already registered by {self.capability_map[cap]}")
            self.capability_map[cap] = agent.name

    async def execute_capability(self, capability: str, ctx, state: dict, **kwargs) -> Any:
        """Route capability to correct agent"""
        agent_name = self.capability_map.get(capability)
        if not agent_name:
            raise ValueError(f"No agent registered for capability {capability}")

        agent = self.agents[agent_name]
        return await agent.execute(capability, ctx, state, **kwargs)

    def list_capabilities(self) -> dict[str, str]:
        """Return capability -> agent mapping"""
        return self.capability_map.copy()
```

**Example Agent** (Financial Analyst):
```python
# agents/financial_analyst.py
from agents.base_agent import BaseAgent, AgentMetadata
from decimal import Decimal
import numpy as np

class FinancialAnalyst(BaseAgent):
    def get_capabilities(self) -> list[str]:
        return [
            "ledger.positions",
            "pricing.apply_pack",
            "metrics.compute_twr",
            "metrics.currency_attribution",
            "ratings.aggregate"
        ]

    async def ledger_positions(self, ctx, state, portfolio_id: str):
        """Get current positions from lots table"""
        rows = await self.services["db"].fetch("""
            SELECT l.id, s.symbol, s.name, l.qty_open, l.cost_base, s.trading_currency
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = $1 AND l.qty_open > 0
        """, portfolio_id)

        positions = [dict(r) for r in rows]
        positions.__metadata__ = AgentMetadata(agent_name=self.name, source="ledger")
        return positions

    async def pricing_apply_pack(self, ctx, state, positions: list, pack_id: str):
        """Apply pricing pack to positions"""
        for pos in positions:
            # Get price from pack
            price_row = await self.services["db"].fetchrow("""
                SELECT close, currency FROM prices WHERE pricing_pack_id = $1 AND security_id = (
                    SELECT id FROM securities WHERE symbol = $2
                )
            """, pack_id, pos["symbol"])

            if price_row:
                pos["price"] = Decimal(str(price_row["close"]))
                pos["price_currency"] = price_row["currency"]

                # Get FX rate if needed
                if pos["price_currency"] != ctx.base_ccy:
                    fx_row = await self.services["db"].fetchrow("""
                        SELECT rate FROM fx_rates
                        WHERE pricing_pack_id = $1 AND base_ccy = $2 AND quote_ccy = $3
                    """, pack_id, pos["price_currency"], ctx.base_ccy)
                    pos["fx_rate"] = Decimal(str(fx_row["rate"]))
                else:
                    pos["fx_rate"] = Decimal("1.0")

                pos["value_base"] = pos["qty_open"] * pos["price"] * pos["fx_rate"]

        positions.__metadata__ = AgentMetadata(
            agent_name=self.name,
            source=f"pricing_pack:{pack_id}",
            asof=ctx.asof
        )
        return positions

    async def metrics_compute_twr(self, ctx, state, positions: list, pack_id: str):
        """Compute time-weighted return"""
        # Simplified: query historical values and compute geometric return
        total_value = sum(p["value_base"] for p in positions)
        total_cost = sum(p["cost_base"] for p in positions)

        twr = float((total_value / total_cost) - 1) if total_cost > 0 else 0.0

        result = {
            "twr": twr,
            "total_value": float(total_value),
            "total_cost": float(total_cost),
            "unrealized_pl": float(total_value - total_cost)
        }
        result.__metadata__ = AgentMetadata(
            agent_name=self.name,
            source=f"pricing_pack:{pack_id}",
            asof=ctx.asof
        )
        return result

    async def metrics_currency_attribution(self, ctx, state, positions: list, pack_id: str):
        """Decompose return into local + FX + interaction"""
        # Simplified attribution logic
        # r_base = (1 + r_local)(1 + r_fx) - 1
        # interaction = r_local * r_fx

        attribution = {
            "local_return": 0.05,  # Placeholder
            "fx_return": 0.02,
            "interaction": 0.001,
            "total": 0.071
        }
        attribution.__metadata__ = AgentMetadata(
            agent_name=self.name,
            source=f"pricing_pack:{pack_id}",
            asof=ctx.asof
        )
        return attribution

    async def ratings_aggregate(self, ctx, state, positions: list):
        """Aggregate ratings across positions"""
        # Placeholder: weighted average of ratings
        badges = {
            "avg_dividend_safety": 7.5,
            "avg_moat_strength": 6.8,
            "avg_resilience": 7.2
        }
        badges.__metadata__ = AgentMetadata(agent_name=self.name)
        return badges
```

**Agent Registration** (in API startup):
```python
# api/main.py
from core.agent_runtime import AgentRuntime
from agents.financial_analyst import FinancialAnalyst
from agents.macro_hound import MacroHound
from agents.data_harvester import DataHarvester

@app.on_event("startup")
async def startup():
    # Initialize services
    db = await create_db_pool()
    redis = await create_redis_pool()
    services = {
        "db": db,
        "redis": redis,
        "polygon": PolygonService(),
        "fmp": FMPService(),
        "fred": FREDService()
    }

    # Create agent runtime
    runtime = AgentRuntime(services)

    # Register agents
    runtime.register_agent(FinancialAnalyst("financial_analyst", services))
    runtime.register_agent(MacroHound("macro_hound", services))
    runtime.register_agent(DataHarvester("data_harvester", services))

    # Create pattern orchestrator
    orchestrator = PatternOrchestrator(runtime, db, redis)

    app.state.orchestrator = orchestrator
    app.state.runtime = runtime

async def run_pattern(pattern_id: str, ctx, inputs: dict, db) -> dict:
    return await app.state.orchestrator.run_pattern(pattern_id, ctx, inputs)
```

---

## Caching Strategy

**Redis Cache for Expensive Capabilities**:
```python
# core/cache_decorator.py
import hashlib
import json
from functools import wraps

def cache_capability(ttl: int = 300):
    """Cache capability results in Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, state, **kwargs):
            # Build cache key
            key_data = {
                "capability": func.__name__,
                "ctx": {"pack_id": str(ctx.pricing_pack_id), "asof": str(ctx.asof)},
                "kwargs": kwargs
            }
            cache_key = f"cap:{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"

            # Check cache
            cached = await self.services["redis"].get(cache_key)
            if cached:
                result = json.loads(cached)
                result.__metadata__ = AgentMetadata(agent_name=self.name, source="cache")
                return result

            # Execute and cache
            result = await func(self, ctx, state, **kwargs)
            await self.services["redis"].setex(cache_key, ttl, json.dumps(result))
            return result

        return wrapper
    return decorator

# Usage
class FinancialAnalyst(BaseAgent):
    @cache_capability(ttl=600)
    async def metrics_compute_twr(self, ctx, state, positions: list, pack_id: str):
        # ... expensive calculation
```

---

## Error Handling & Circuit Breaker

```python
# core/circuit_breaker.py
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = {}
        self.open_until = {}

    def is_open(self, agent_name: str) -> bool:
        if agent_name in self.open_until:
            if datetime.now() < self.open_until[agent_name]:
                return True
            else:
                # Reset after timeout
                del self.open_until[agent_name]
                self.failures[agent_name] = 0
        return False

    def record_failure(self, agent_name: str):
        self.failures[agent_name] = self.failures.get(agent_name, 0) + 1
        if self.failures[agent_name] >= self.failure_threshold:
            self.open_until[agent_name] = datetime.now() + timedelta(seconds=self.timeout)

    def record_success(self, agent_name: str):
        if agent_name in self.failures:
            self.failures[agent_name] = 0

# Integration in AgentRuntime
class AgentRuntime:
    def __init__(self, services: dict):
        # ...
        self.circuit_breaker = CircuitBreaker()

    async def execute_capability(self, capability: str, ctx, state: dict, **kwargs):
        agent_name = self.capability_map[capability]

        if self.circuit_breaker.is_open(agent_name):
            raise HTTPException(503, f"Agent {agent_name} circuit breaker is open")

        try:
            result = await self.agents[agent_name].execute(capability, ctx, state, **kwargs)
            self.circuit_breaker.record_success(agent_name)
            return result
        except Exception as e:
            self.circuit_breaker.record_failure(agent_name)
            raise
```

---

## Acceptance Criteria (Sprint 1 Gate)

- [ ] `/execute` endpoint receives request, builds RequestContext, enforces freshness
- [ ] Pattern orchestrator loads JSON patterns, executes steps in order
- [ ] Template substitution resolves `{{state.foo}}` correctly
- [ ] Agent runtime routes capabilities to correct agents
- [ ] Trace includes `pricing_pack_id`, `ledger_commit_hash`, agents/capabilities/sources
- [ ] Circuit breaker opens after 5 failures, recovers after timeout
- [ ] Can execute `portfolio_overview` pattern end-to-end
- [ ] Result includes per-panel staleness metadata

---

## Handoff

Upon completion, deliver:
1. **API documentation**: OpenAPI spec with examples
2. **Pattern authoring guide**: How to create new patterns
3. **Agent development guide**: How to build and register agents
4. **Capability registry**: List of all registered capabilities
5. **Error handling playbook**: Circuit breaker recovery, retry strategies
