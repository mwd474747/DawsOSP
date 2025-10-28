# Parallel Execution Plan - Pattern Capability Remediation
**Date**: 2025-10-27
**Strategy**: 3 independent agents executing in parallel
**Total Est. Time**: 10-14 hours (parallel) vs. 24-32 hours (sequential)
**Efficiency Gain**: 58-70% time reduction

---

## Pre-Execution Validation Complete ✅

### Impacted Patterns Analysis

| Pattern | Missing Capabilities | Status |
|---------|---------------------|--------|
| `portfolio_macro_overview.json` | `charts.macro_overview` | ❌ BLOCKED |
| `portfolio_scenario_analysis.json` | `charts.scenario_deltas` | ❌ BLOCKED |
| `macro_trend_monitor.json` | `alerts.suggest_presets` | ❌ BLOCKED |
| `news_impact_analysis.json` | `alerts.create_if_threshold` | ❌ BLOCKED |

**Total**: 4 patterns blocked (33% of all patterns)

### Existing Services Verified ✅

| Service | Status | Methods Available |
|---------|--------|-------------------|
| `backend/app/services/alerts.py` | ✅ EXISTS (249 lines) | `evaluate_condition()`, `should_trigger()`, `deliver_alert()` |
| `backend/app/services/playbooks.py` | ✅ EXISTS (410 lines) | `generate_dar_breach_playbook()`, `generate_regime_shift_playbook()` |
| `backend/app/agents/financial_analyst.py` | ✅ HAS charts_overview() | Returns allocation/performance/risk charts |

**Validation**: Services are implemented, just need agent wiring

### Test Path Issues Verified ✅

| File | Issue | Impact |
|------|-------|--------|
| `backend/tests/test_database_schema.py` | Hardcoded `/DawsOSB/DawsOSP` path (line 29) | Tests fail on other machines |
| `backend/tests/test_portfolio_overview_pattern.py` | Hardcoded `/DawsOSB/DawsOSP` paths (lines 29, 48) | Pattern orchestrator tests broken |
| `backend/test_pdf_export.py` | Not in `tests/` directory | Not integrated into pytest suite |

**Total**: 3 files needing fixes

---

## Three-Agent Parallel Execution Strategy

### Agent 1: ALERTS_CHARTS_AGENT (P0 - Critical)
**Estimated Time**: 8-10 hours
**Blocking**: 4 patterns
**Dependencies**: None (fully independent)

**Deliverables**:
1. `backend/app/agents/alerts_agent.py` (~400 lines)
2. `backend/app/agents/charts_agent.py` (~300 lines)
3. Registration in `backend/app/api/executor.py`
4. Unit tests (~200 lines)

**Acceptance Criteria**:
- [ ] AlertsAgent implements `alerts.suggest_presets` and `alerts.create_if_threshold`
- [ ] ChartsAgent implements `charts.macro_overview` and `charts.scenario_deltas`
- [ ] Both agents registered in executor.py (lines 140-150)
- [ ] All 4 blocked patterns execute without capability errors
- [ ] 10+ unit tests passing (pytest backend/tests/unit/test_alerts_agent.py)

---

### Agent 2: TEST_PATH_FIXER (P0 - Critical)
**Estimated Time**: 2-3 hours
**Blocking**: CI/CD pipeline
**Dependencies**: None (fully independent)

**Deliverables**:
1. Fix `test_database_schema.py` (remove hardcoded path)
2. Fix `test_portfolio_overview_pattern.py` (remove hardcoded paths)
3. Move `test_pdf_export.py` → `tests/unit/test_pdf_export.py`
4. Add pytest markers for integration tests

**Acceptance Criteria**:
- [ ] No references to `/DawsOSB/` in any test file
- [ ] Tests use relative imports (`from backend.app...`)
- [ ] PDF export test integrated into pytest suite
- [ ] All existing tests still pass (649 tests collected)

---

### Agent 3: REQUEST_CACHE_ARCHITECT (P2 - Optimization)
**Estimated Time**: 6-8 hours
**Blocking**: None (optimization only)
**Dependencies**: None (fully independent)

**Deliverables**:
1. Add `capability_cache: Dict[str, Any]` to `RequestCtx`
2. Wrap capability execution in cache check/write
3. Add cache hit metrics to trace
4. Unit tests for cache behavior

**Acceptance Criteria**:
- [ ] `RequestCtx` has `capability_cache` attribute
- [ ] Agent runtime checks cache before executing capability
- [ ] Cache respects capability uniqueness (same args = cache hit)
- [ ] Trace shows cache hit rate
- [ ] 5+ unit tests for cache logic

---

## Detailed Task Breakdown

### AGENT 1: ALERTS_CHARTS_AGENT

#### Task 1.1: Create AlertsAgent (4-5 hours)

**File**: `backend/app/agents/alerts_agent.py`

**Implementation**:
```python
from backend.app.agents.base_agent import BaseAgent
from backend.app.services.alerts import AlertService
from backend.app.services.playbooks import PlaybookGenerator

class AlertsAgent(BaseAgent):
    def get_capabilities(self) -> List[str]:
        return [
            "alerts.suggest_presets",
            "alerts.create_if_threshold"
        ]

    async def alerts_suggest_presets(self, ctx, state, trend_analysis, portfolio_id):
        """
        Suggest alert presets based on trend analysis.

        Pattern: macro_trend_monitor.json
        Logic:
            1. Analyze trend_analysis for regime shifts, factor changes
            2. Generate playbooks using PlaybookGenerator
            3. Return structured alert suggestions
        """
        playbook_gen = PlaybookGenerator()

        suggestions = []

        # If regime shifting
        if trend_analysis.get("regime_shift_detected"):
            playbook = playbook_gen.generate_regime_shift_playbook(
                old_regime=trend_analysis["old_regime"],
                new_regime=trend_analysis["new_regime"]
            )
            suggestions.append({
                "type": "regime_shift",
                "condition": {
                    "type": "macro",
                    "entity": "regime",
                    "op": "!=",
                    "value": trend_analysis["old_regime"]
                },
                "playbook": playbook
            })

        # If DaR increasing
        if trend_analysis.get("dar_increasing"):
            playbook = playbook_gen.generate_dar_breach_playbook(...)
            suggestions.append({...})

        return {"suggestions": suggestions, "count": len(suggestions)}

    async def alerts_create_if_threshold(self, ctx, state, portfolio_id, news_impact):
        """
        Create alert if news impact exceeds threshold.

        Pattern: news_impact_analysis.json
        Logic:
            1. Check if news_impact.total_impact > threshold
            2. If yes, create alert via AlertService
            3. Return alert_created status
        """
        alert_service = AlertService()

        threshold = 0.05  # 5% portfolio impact
        total_impact = abs(news_impact.get("total_impact", 0))

        if total_impact > threshold:
            alert = await alert_service.evaluate_condition({
                "type": "news_sentiment",
                "entity": portfolio_id,
                "op": ">",
                "value": threshold
            }, {"asof_date": ctx.asof_date})

            return {"alert_created": True, "alert": alert}

        return {"alert_created": False, "reason": "Below threshold"}
```

**Dependencies**:
- `backend/app/services/alerts.py` (✅ exists)
- `backend/app/services/playbooks.py` (✅ exists)

**Tests**: `backend/tests/unit/test_alerts_agent.py`
- Test suggest_presets with regime shift
- Test suggest_presets with DaR increase
- Test create_if_threshold above threshold
- Test create_if_threshold below threshold
- Test error handling

---

#### Task 1.2: Create ChartsAgent (3-4 hours)

**File**: `backend/app/agents/charts_agent.py`

**Implementation**:
```python
from backend.app.agents.base_agent import BaseAgent

class ChartsAgent(BaseAgent):
    def get_capabilities(self) -> List[str]:
        return [
            "charts.macro_overview",
            "charts.scenario_deltas"
        ]

    async def charts_macro_overview(self, ctx, state, regime, indicators, factor_exposures, dar):
        """
        Format macro data for visualization.

        Pattern: portfolio_macro_overview.json
        Returns: Chart specifications for regime card, factor bars, DaR gauge
        """
        return {
            "regime_card": {
                "type": "regime_probabilities",
                "data": regime.get("regime_scores", {}),
                "current": regime.get("regime_name"),
                "confidence": regime.get("confidence")
            },
            "factor_exposures": {
                "type": "horizontal_bar",
                "data": [
                    {"factor": k, "exposure": v}
                    for k, v in factor_exposures.get("exposures", {}).items()
                ]
            },
            "dar_widget": {
                "type": "gauge",
                "value": dar.get("dar_pct", 0),
                "threshold": dar.get("confidence_level", 0.95),
                "regime_context": regime.get("regime_name")
            }
        }

    async def charts_scenario_deltas(self, ctx, state, base, shocked):
        """
        Format scenario delta tables for visualization.

        Pattern: portfolio_scenario_analysis.json
        Returns: Delta comparison tables
        """
        # Compare base vs shocked valuations
        deltas = []

        for position in base.get("positions", []):
            shocked_pos = next(
                (p for p in shocked.get("positions", []) if p["security_id"] == position["security_id"]),
                None
            )

            if shocked_pos:
                delta = {
                    "symbol": position["symbol"],
                    "base_value": position["market_value"],
                    "shocked_value": shocked_pos["market_value"],
                    "delta_value": shocked_pos["market_value"] - position["market_value"],
                    "delta_pct": (shocked_pos["market_value"] - position["market_value"]) / position["market_value"]
                }
                deltas.append(delta)

        return {
            "position_deltas": deltas,
            "portfolio_delta": {
                "base_nav": sum(p["market_value"] for p in base.get("positions", [])),
                "shocked_nav": sum(p["market_value"] for p in shocked.get("positions", [])),
                "total_impact": sum(d["delta_value"] for d in deltas)
            }
        }
```

**Dependencies**: None (pure formatting logic)

**Tests**: `backend/tests/unit/test_charts_agent.py`
- Test macro_overview with valid regime data
- Test scenario_deltas with position changes
- Test handling missing data
- Test calculation accuracy

---

#### Task 1.3: Register Agents in Executor (0.5 hours)

**File**: `backend/app/api/executor.py`

**Changes**:
```python
# Line 140 (after reports_agent)
        # 8. Alerts Agent - Alert suggestions and threshold-based creation
        from backend.app.agents.alerts_agent import AlertsAgent
        alerts_agent = AlertsAgent("alerts", services)
        _agent_runtime.register_agent(alerts_agent)

        # 9. Charts Agent - Chart formatting and visualization specs
        from backend.app.agents.charts_agent import ChartsAgent
        charts_agent = ChartsAgent("charts", services)
        _agent_runtime.register_agent(charts_agent)

        logger.info(
            "Agent runtime initialized with 9 agents: "
            "financial_analyst, macro_hound, data_harvester, claude, ratings, optimizer, reports, alerts, charts"
        )
```

**Verification**:
```bash
grep -c "register_agent" backend/app/api/executor.py
# Should return: 9
```

---

### AGENT 2: TEST_PATH_FIXER

#### Task 2.1: Fix test_database_schema.py (0.5 hours)

**File**: `backend/tests/test_database_schema.py`

**Change**:
```python
# BEFORE (line 29):
sys.path.insert(0, "/Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP")

# AFTER:
# No sys.path.insert needed - pytest handles imports
```

**Verification**:
```bash
grep -c "DawsOSB" backend/tests/test_database_schema.py
# Should return: 0
```

---

#### Task 2.2: Fix test_portfolio_overview_pattern.py (1 hour)

**File**: `backend/tests/test_portfolio_overview_pattern.py`

**Changes**:
```python
# BEFORE (line 29):
sys.path.insert(0, "/Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP")

# AFTER:
# No sys.path.insert needed

# BEFORE (line 48):
pattern_path = Path("/Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP/backend/app/patterns/portfolio_overview.json")

# AFTER:
pattern_path = Path(__file__).parent.parent / "patterns" / "portfolio_overview.json"
```

**Verification**:
```bash
grep -c "DawsOSB" backend/tests/test_portfolio_overview_pattern.py
# Should return: 0
```

---

#### Task 2.3: Move PDF export test (1 hour)

**Actions**:
1. Move `backend/test_pdf_export.py` → `backend/tests/unit/test_pdf_export.py`
2. Remove `sys.path.insert` lines
3. Convert to pytest format (fixtures instead of manual mocks)
4. Add pytest markers

**Example**:
```python
import pytest
from backend.app.services.reports import ReportService

@pytest.fixture
def mock_portfolio_data():
    return {
        "portfolio_name": "Test Growth Portfolio",
        # ... rest of mock data
    }

@pytest.mark.asyncio
async def test_pdf_generation(mock_portfolio_data):
    report_service = ReportService(use_db=False)
    result = await report_service.render_pdf(mock_portfolio_data)
    assert result["success"] is True
```

---

### AGENT 3: REQUEST_CACHE_ARCHITECT

#### Task 3.1: Add Cache to RequestCtx (2 hours)

**File**: `backend/app/core/types.py`

**Changes**:
```python
@dataclass
class RequestCtx:
    # ... existing fields ...

    # NEW: Capability result cache
    capability_cache: Dict[str, Any] = field(default_factory=dict)
    cache_stats: Dict[str, int] = field(default_factory=lambda: {"hits": 0, "misses": 0})

    def cache_key(self, capability: str, args: Dict[str, Any]) -> str:
        """Generate cache key for capability + args."""
        import hashlib
        import json

        # Sort args for consistent hashing
        sorted_args = json.dumps(args, sort_keys=True)
        key_str = f"{capability}:{sorted_args}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_cached(self, capability: str, args: Dict[str, Any]) -> Optional[Any]:
        """Get cached result if exists."""
        key = self.cache_key(capability, args)
        if key in self.capability_cache:
            self.cache_stats["hits"] += 1
            return self.capability_cache[key]
        self.cache_stats["misses"] += 1
        return None

    def set_cached(self, capability: str, args: Dict[str, Any], result: Any):
        """Cache capability result."""
        key = self.cache_key(capability, args)
        self.capability_cache[key] = result
```

---

#### Task 3.2: Wrap Agent Runtime Execution (3-4 hours)

**File**: `backend/app/core/agent_runtime.py`

**Changes**:
```python
async def execute_capability(
    self,
    capability: str,
    ctx: RequestCtx,
    state: Dict[str, Any],
    **kwargs
) -> Any:
    """Execute capability with caching."""

    # Check cache first
    cached_result = ctx.get_cached(capability, kwargs)
    if cached_result is not None:
        logger.debug(f"Cache HIT: {capability} (args hash: {ctx.cache_key(capability, kwargs)[:8]})")
        return cached_result

    logger.debug(f"Cache MISS: {capability}")

    # Execute capability
    result = await self._execute_capability_uncached(capability, ctx, state, **kwargs)

    # Cache result
    ctx.set_cached(capability, kwargs, result)

    return result
```

---

#### Task 3.3: Add Cache Metrics to Trace (1 hour)

**File**: `backend/app/core/pattern_orchestrator.py`

**Changes**:
```python
# After pattern execution completes
trace["cache_stats"] = {
    "hits": ctx.cache_stats["hits"],
    "misses": ctx.cache_stats["misses"],
    "hit_rate": ctx.cache_stats["hits"] / (ctx.cache_stats["hits"] + ctx.cache_stats["misses"]) if (ctx.cache_stats["hits"] + ctx.cache_stats["misses"]) > 0 else 0
}
```

---

## Execution Sequence (Parallel)

### Week 1 (Parallel Execution)

**Day 1-2** (Parallel):
- Agent 1: Start AlertsAgent implementation
- Agent 2: Fix all test paths (complete in 2-3 hours)
- Agent 3: Start RequestCtx cache implementation

**Day 3-4** (Parallel):
- Agent 1: Complete ChartsAgent + registration
- Agent 2: ✅ DONE (waiting)
- Agent 3: Complete agent runtime wrapping

**Day 5** (Integration):
- Agent 1: Write unit tests + verify patterns execute
- Agent 3: Add cache metrics to trace

**Day 6** (Validation):
- Run full test suite (649+ tests)
- Verify all 4 blocked patterns work
- Measure cache hit rates

---

## Success Metrics

### Agent 1 Success Criteria
- [ ] 4 blocked patterns execute without errors
- [ ] `grep -c "register_agent" backend/app/api/executor.py` returns 9
- [ ] 10+ unit tests passing for alerts/charts agents
- [ ] Zero capability routing errors in pattern execution

### Agent 2 Success Criteria
- [ ] `grep -r "DawsOSB" backend/tests/` returns 0 results
- [ ] `pytest backend/tests/ --collect-only` shows 650+ tests (including PDF test)
- [ ] All existing tests still pass

### Agent 3 Success Criteria
- [ ] Cache hit rate >50% on repeated pattern executions
- [ ] Trace includes cache_stats section
- [ ] 5+ unit tests for cache logic passing
- [ ] No performance regression (p95 latency)

---

## Risk Mitigation

### Risk 1: Agents interfere with each other
**Mitigation**: All 3 agents work on completely separate files (no overlaps)

### Risk 2: Test failures during integration
**Mitigation**: Agent 2 completes first (2-3 hours), unblocking CI/CD

### Risk 3: Cache introduces bugs
**Mitigation**: Cache is P2 (optional), can be disabled via feature flag

---

## Delegation Instructions

### For ALERTS_CHARTS_AGENT

**Context Files to Read**:
1. `backend/app/services/alerts.py` - Understand alert evaluation methods
2. `backend/app/services/playbooks.py` - Understand playbook generation
3. `backend/patterns/macro_trend_monitor.json` - See expected inputs/outputs
4. `backend/patterns/portfolio_macro_overview.json` - See chart requirements

**Deliverables**:
- `backend/app/agents/alerts_agent.py`
- `backend/app/agents/charts_agent.py`
- Updated `backend/app/api/executor.py` (registration)
- `backend/tests/unit/test_alerts_agent.py`
- `backend/tests/unit/test_charts_agent.py`

**Verification Commands**:
```bash
# Syntax check
python3 -m py_compile backend/app/agents/alerts_agent.py
python3 -m py_compile backend/app/agents/charts_agent.py

# Registration check
grep -c "register_agent" backend/app/api/executor.py  # Should be 9

# Test execution
pytest backend/tests/unit/test_alerts_agent.py -v
pytest backend/tests/unit/test_charts_agent.py -v
```

---

### For TEST_PATH_FIXER

**Context Files to Read**:
1. `backend/tests/test_database_schema.py` - See hardcoded paths
2. `backend/tests/test_portfolio_overview_pattern.py` - See pattern path issues
3. `backend/test_pdf_export.py` - See standalone test structure

**Deliverables**:
- Fixed `backend/tests/test_database_schema.py`
- Fixed `backend/tests/test_portfolio_overview_pattern.py`
- Moved `backend/tests/unit/test_pdf_export.py`

**Verification Commands**:
```bash
# Path check
grep -r "DawsOSB" backend/tests/  # Should return empty

# Collection check
pytest backend/tests/ --collect-only -q | tail -1  # Should show 650+ tests

# Execution check
pytest backend/tests/test_database_schema.py -v
pytest backend/tests/test_portfolio_overview_pattern.py -v
pytest backend/tests/unit/test_pdf_export.py -v
```

---

### For REQUEST_CACHE_ARCHITECT

**Context Files to Read**:
1. `backend/app/core/types.py` - Understand RequestCtx structure
2. `backend/app/core/agent_runtime.py` - Understand capability execution flow
3. `backend/app/core/pattern_orchestrator.py` - Understand trace structure

**Deliverables**:
- Updated `backend/app/core/types.py` (cache fields + methods)
- Updated `backend/app/core/agent_runtime.py` (cache wrapper)
- Updated `backend/app/core/pattern_orchestrator.py` (cache metrics)
- `backend/tests/unit/test_request_cache.py`

**Verification Commands**:
```bash
# Syntax check
python3 -m py_compile backend/app/core/types.py
python3 -m py_compile backend/app/core/agent_runtime.py

# Test cache behavior
pytest backend/tests/unit/test_request_cache.py -v

# Integration test (should show cache stats in trace)
pytest backend/tests/test_portfolio_overview_pattern.py -v -s
```

---

## Timeline Summary

| Agent | Task | Hours | Days (Parallel) |
|-------|------|-------|----------------|
| Agent 1 | AlertsAgent + ChartsAgent + Tests | 8-10h | 2-3 days |
| Agent 2 | Fix Test Paths | 2-3h | 0.5 days |
| Agent 3 | Request Cache | 6-8h | 2 days |
| **TOTAL** | **All Tasks** | **16-21h** | **3 days (parallel)** |

**Sequential Estimate**: 3+ weeks
**Parallel Estimate**: 3-4 days
**Efficiency Gain**: 80-85%

---

**Status**: Ready for delegation
**Next Action**: Assign agents to start parallel execution
**Estimated Completion**: 2025-10-30
