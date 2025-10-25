# DawsOS Application Stability Plan

**Date**: 2025-10-24
**Priority**: P0 (Critical)  
**Goal**: Complete the remaining implementation plan and ship a stable, explainable portfolio assistant.

---

## Executive Summary

The connection-pool issue has been resolved (lazy AsyncPG initialisation). The platform now boots cleanly, seeds data, and returns valuations via the pricing pack. Remaining stability work centres on finishing agent capabilities, nightly orchestration, observability, and coverage so we can sign off on the “done” criteria in `PRODUCT_SPEC.md`. The granular backlog is maintained in [.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md); this plan highlights the stability-critical cuts of that list.

### Current State (October 24, 2025)

**✅ Working**
- FastAPI executor `/v1/execute` with freshness gate and tracing
- Pattern orchestrator executing seeded patterns (portfolio overview, holdings)
- Pricing service + seed loader (`python scripts/seed_loader.py --all`)
- Streamlit UI reading pattern outputs
- AsyncPG pool reused across requests (no reload bug)

**🚧 In Progress**
- Macro scenarios & drawdown-at-risk (MacroHound agent)
- Buffett ratings and optimizer services/patterns
- Rights-registry enforcement for PDF exports & alerts
- Nightly job orchestration (build pack → reconcile → metrics → alerts)
- Observability dashboards + expanded automated tests

---

## Stabilisation Plan

### 1. Complete Critical Capabilities (P0)
| Area | Tasks | Target |
|------|-------|--------|
| Macro | Implement `macro_run_scenario`, `macro_compute_dar`, seed scenario_shocks | Sprint 2 milestone |
| Ratings | Build `ratings` service + patterns (dividend safety, moat, resilience) | Sprint 3 |
| Optimizer | Service + pattern using Riskfolio-Lib; integrate with UI | Sprint 3 |
| Exports/Alerts | Rights-enforced PDF exports, alerts delivery + DLQ | Sprint 4 |

### 2. Nightly Pack Pipeline
1. Build pack from providers/seeds (migration from stub)  
2. Reconcile vs ledger (±1 bp)  
3. Compute metrics + currency attribution  
4. Prewarm factors/ratings  
5. Evaluate alerts; mark pack fresh  
6. Emit telemetry (OTel + Prometheus)  

Provide runbook automation (`backend/jobs/scheduler.py`) and CI hooks.

### 3. Observability & Tests
- Add end-to-end Playwright/pytest coverage for portfolio overview, holdings, macro screens  
- Wire OpenTelemetry exporters + Prometheus dashboards  
- Set SLO alerts (Warm p95 ≤ 1.2 s, Cold p95 ≤ 2.0 s)  
- Expand unit tests for pricing service, macro scenarios, ratings

### 4. Deployment Readiness
- Harden `docker-compose.prod.yml` and Helm charts  
- Introduce JWT auth + RBAC gates leveraging `AUTH_JWT_SECRET`  
- Populate runbooks (alerts storm, rights violation, pack failure) with latest workflow  
- Final UAT checklist per `IMPLEMENTATION_ROADMAP_V2.md`

---

## Verification Checklist

| Item | Status | Command |
|------|--------|---------|
| Seed data loads | ✅ | `python scripts/seed_loader.py --all` |
| Executor health | ✅ | `curl http://localhost:8000/health` |
| Portfolio overview pattern | ✅ | `curl -X POST http://localhost:8000/v1/execute ...` |
| Macro dashboard | 🚧 | Pending scenario/DaR implementation |
| Ratings/optimizer | 🚧 | Pending services + seeds |
| Nightly job chain | 🚧 | Implement real providers + orchestration |
| Observability | 🚧 | Add OTel exporter, Prom dashboards |
| Test coverage ≥60 % | 🚧 | Expand backend & UI tests |
```bash
# backend/run_api_prod.sh
#!/bin/bash
gunicorn app.api.executor:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
```

**Benefits:**
- Process-based workers (not thread-based)
- Each worker has its own pool initialization
- Production-grade stability
- Graceful restarts

---

### Phase 4: Verify Data Flow (30 minutes)

**Test Checklist:**

1. **Backend Health**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Pattern Execution**
   ```bash
   curl -X POST "http://localhost:8000/v1/execute" \
     -H "Content-Type: application/json" \
     -d '{"pattern_id":"portfolio_overview","inputs":{"portfolio_id":"11111111-1111-1111-1111-111111111111","lookback_days":252}}' \
     | python3 -m json.tool
   ```

3. **Verify Real Data**
   - `ledger.positions` should return 3 positions (AAPL, RY, XIU)
   - `valued_positions` should show positions with market values
   - `perf_metrics` should return database metrics (not "pool not initialized" error)

4. **Frontend Integration**
   ```bash
   ./frontend/run_ui.sh
   # Navigate to Portfolio Overview
   # Should display real positions and metrics
   ```

---

## Historical Fix Options (Archived)

> The current implementation uses the lazy pool singleton. Retain these options for future architectural discussions.

### Option B: Architectural Refactor (Future-Proof)

### Phase 1: Pool as Dependency (4 hours)

**Approach**: Pass pool explicitly through call chain.

**Changes Required:**

1. **Pattern Orchestrator**
   ```python
   async def run_pattern(self, pattern_id, ctx, inputs, pool):
       # Store pool in execution state
       state = {
           "ctx": ctx.to_dict(),
           "inputs": inputs,
           "pool": pool,  # Add pool to state
       }
       # Pass to agent runtime
       result = await self.agent_runtime.execute_capability(
           capability, args, state, pool=pool
       )
   ```

2. **Agent Runtime**
   ```python
   async def execute_capability(self, capability, args, state, pool):
       agent = self.get_agent(agent_name)
       return await agent.execute(capability, args, state, pool)
   ```

3. **Agents**
   ```python
   async def ledger_positions(self, ctx, state, pool, portfolio_id=None):
       async with pool.acquire() as conn:
           rows = await conn.fetch("SELECT * FROM lots WHERE ...")
   ```

4. **Executor**
   ```python
   @app.post("/v1/execute")
   async def execute(req: ExecuteRequest):
       pool = get_db_pool()  # Get once at API boundary
       result = await orchestrator.run_pattern(
           req.pattern_id, ctx, req.inputs, pool
       )
   ```

**Benefits:**
- Explicit dependencies (testable)
- No global state
- Works with any server configuration

**Drawbacks:**
- Requires changing 50+ method signatures
- Breaks existing patterns/capability interfaces
- Large refactoring effort

---

### Option C: Hybrid Approach (Pragmatic + Testable)

### Phase 1: Lazy Pool Singleton (2 hours)

**Approach**: Each module that needs pool gets it lazily from a shared singleton.

**Implementation:**

```python
# backend/app/db/pool_manager.py (NEW FILE)
"""
Centralized Pool Manager - Singleton Pattern

This ensures ONE pool instance is accessible across all modules,
regardless of import order or uvicorn reloading.
"""
import asyncpg
import logging
from typing import Optional

logger = logging.getLogger("DawsOS.PoolManager")

class PoolManager:
    """Singleton pool manager"""
    _instance = None
    _pool: Optional[asyncpg.Pool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, database_url: str, **kwargs):
        """Initialize pool (idempotent)"""
        if self._pool is not None:
            logger.warning("Pool already initialized")
            return self._pool

        self._pool = await asyncpg.create_pool(database_url, **kwargs)
        logger.info("Pool initialized successfully")
        return self._pool

    def get_pool(self) -> asyncpg.Pool:
        """Get pool (raises if not initialized)"""
        if self._pool is None:
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        return self._pool

    async def close(self):
        """Close pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None

# Global singleton instance
_pool_manager = PoolManager()

def get_pool_manager() -> PoolManager:
    """Get global pool manager singleton"""
    return _pool_manager
```

**Update connection.py:**

```python
# backend/app/db/connection.py
from backend.app.db.pool_manager import get_pool_manager

async def init_db_pool(database_url, **kwargs):
    """Initialize database pool via singleton manager"""
    manager = get_pool_manager()
    return await manager.initialize(database_url, **kwargs)

def get_db_pool():
    """Get database pool via singleton manager"""
    manager = get_pool_manager()
    return manager.get_pool()

# All helper functions remain unchanged (execute_query, etc.)
```

**Benefits:**
- Singleton pattern works across module instances
- No changes to existing code (drop-in replacement)
- Testable (can inject mock manager)

**Drawbacks:**
- Still uses singleton pattern (global state)
- Slightly more complex than Option A

---

## Recommended Path: Option A + Option C Phase 1

### Week 1: Stability (Option A)
1. Disable auto-reload → Test → Verify
2. Production mode with Gunicorn
3. Full end-to-end testing

### Week 2: Robustness (Option C Phase 1)
1. Implement PoolManager singleton
2. Test with both reload on/off
3. Document for future contributors

### Future: Refactoring (Option B)
- After application is stable and shipping features
- Incremental migration to dependency injection
- One module/agent at a time

---

## Critical Issues to Fix

### Issue 1: Duplicate Lots Data
**Status**: Found 6 lots for test portfolio (should be 3)
**Cause**: Seed data loaded twice
**Fix**:
```sql
DELETE FROM lots
WHERE id NOT IN (
  SELECT MIN(id) FROM lots
  GROUP BY portfolio_id, symbol, acquisition_date
);
```

### Issue 2: Empty Positions in Pattern Response
**Status**: `valued_positions.positions = []`
**Root Cause**: Database pool access failure
**Fix**: Implement Option A (disable reload)

### Issue 3: Metrics Errors
**Status**: "Database pool not initialized" in metrics.compute_twr
**Root Cause**: Same as Issue 2
**Fix**: Implement Option A

### Issue 4: Currency Attribution Error
**Status**: Missing `position_attributions` argument
**Priority**: P1 (after pool issue resolved)
**Fix**: Update method signature in [currency_attribution.py](backend/jobs/currency_attribution.py)

---

## Testing Protocol

### Level 1: Backend Only
```bash
# Start backend (no reload)
cd backend && ./run_api.sh

# Test health
curl http://localhost:8000/health

# Test pattern
curl -X POST "http://localhost:8000/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{"pattern_id":"portfolio_overview","inputs":{"portfolio_id":"11111111-1111-1111-1111-111111111111","lookback_days":252}}'
```

**Success Criteria:**
- ✅ Response contains `valued_positions.positions` with 3 items
- ✅ No "Database pool not initialized" errors
- ✅ `perf_metrics` contains real values (not null/error)

### Level 2: Frontend Integration
```bash
# Start backend
cd backend && ./run_api.sh

# Start frontend (different terminal)
cd frontend && ./run_ui.sh

# Open browser: http://localhost:8501
```

**Success Criteria:**
- ✅ Portfolio Overview screen displays positions
- ✅ Metrics show real TWR, Sharpe, volatility
- ✅ No errors in console logs

### Level 3: End-to-End Pattern Execution
```bash
# Test all patterns
for pattern in portfolio_overview holding_deep_dive portfolio_cycle_risk; do
  echo "Testing $pattern..."
  curl -X POST "http://localhost:8000/v1/execute" \
    -H "Content-Type: application/json" \
    -d "{\"pattern_id\":\"$pattern\",\"inputs\":{\"portfolio_id\":\"11111111-1111-1111-1111-111111111111\"}}" \
    | jq '.result | keys'
done
```

**Success Criteria:**
- ✅ All patterns return data (not errors)
- ✅ Execution time < 500ms for simple patterns
- ✅ No database errors in logs

---

## Implementation Schedule

### Day 1 (Today): Immediate Stability
- [ ] Clean up duplicate lots data (15 min)
- [ ] Implement Option A Phase 1 (disable reload) (30 min)
- [ ] Test backend pattern execution (15 min)
- [ ] Verify real data returned (15 min)
- [ ] Document findings (15 min)

**Deliverable**: Working backend with real data queries

### Day 2: Production Readiness
- [ ] Implement Gunicorn production setup (1 hour)
- [ ] Create dev vs prod startup scripts (30 min)
- [ ] End-to-end testing checklist (1 hour)
- [ ] Frontend integration testing (1 hour)

**Deliverable**: Production-ready deployment configuration

### Day 3: Documentation & Handoff
- [ ] Architecture decision record (ADR) for pool management (30 min)
- [ ] Developer guide for local setup (30 min)
- [ ] Production deployment guide (30 min)
- [ ] Known issues and workarounds (30 min)

**Deliverable**: Complete documentation package

### Week 2: Robustness (Optional)
- [ ] Implement Option C (PoolManager singleton)
- [ ] Add comprehensive error handling
- [ ] Performance profiling and optimization
- [ ] Integration test suite

---

## Success Metrics

### Application Stability
- Backend uptime > 99%
- No "pool not initialized" errors
- Pattern execution success rate > 95%

### Data Integrity
- All portfolio positions load from database
- Metrics calculations use real transaction data
- No stub/mock data in production responses

### Developer Experience
- Clear separation of dev vs prod modes
- Fast local development iteration
- Comprehensive error messages

---

## Rollback Plan

If Option A fails:
1. Revert connection.py to previous version
2. Use stub data endpoints temporarily
3. Implement Option C as fallback
4. Schedule Option B for next sprint

---

## Next Steps

**Immediate Action**: Implement Option A Phase 1
- Edit `backend/run_api.sh` (remove `--reload` flag)
- Restart backend
- Test pattern execution
- Verify positions returned

**Success Checkpoint**: Pattern execution returns 3 positions for test portfolio

---

## References

- [PRODUCT_SPEC.md](PRODUCT_SPEC.md) – guardrails, architecture, done criteria
- [.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md) – canonical backlog and ownership
- [.ops/IMPLEMENTATION_ROADMAP_V2.md](.ops/IMPLEMENTATION_ROADMAP_V2.md) – historical sequencing context
- [.ops/RUNBOOKS.md](.ops/RUNBOOKS.md) – operational response playbooks
- [backend/app/db/connection.py](backend/app/db/connection.py) – current pool implementation

---

**Decision**: OPTION A (Pragmatic Fix)
**Rationale**: Fastest path to stability, production-ready, minimal code changes
**Timeline**: 2-3 hours to working application
**Risk**: Low (reversible, well-tested pattern)
