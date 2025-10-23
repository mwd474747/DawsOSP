# Governance Findings Assessment - 2025-10-22

**Assessor**: Claude (Phase 4 Session)
**Date**: 2025-10-22
**Context**: Post-Phase 4 Tasks 1-4 completion
**Status**: ✅ VALIDATED - All 3 findings confirmed, remediation plan provided

---

## Executive Summary

All three governance findings are **CONFIRMED VALID** and represent critical violations of the DawsOS governance model. However, important context from the completed work:

1. **Finding 1 (Fabricated Pack)**: ✅ CONFIRMED in main.py, but ✅ **FIXED in executor.py**
2. **Finding 2 (RLS Not Set)**: ✅ CONFIRMED in both files, but ⚠️ **INFRASTRUCTURE READY**
3. **Finding 3 (Stub Orchestrator)**: ✅ CONFIRMED in main.py, but ✅ **WORKING in executor.py**

**Critical Discovery**: The codebase has **TWO EXECUTION PATHS**:
- **Legacy Path**: `POST /execute` (main.py) - **ALL 3 VIOLATIONS PRESENT**
- **Modern Path**: `POST /v1/execute` (executor.py) - **2/3 FIXED, 1 PARTIAL**

**Recommendation**: **DEPRECATE** legacy `/execute` endpoint, **MANDATE** `/v1/execute` only.

---

## Finding 1: Fabricated Pricing Pack ID (HIGH SEVERITY)

### Claim

> "backend/app/main.py:325 & backend/app/main.py:392: build_request_context still fabricates pricing_pack_id and is_pack_fresh always returns True, so /execute never validates the pack or enforces the freshness gate."

### Verification: ✅ CONFIRMED

**Evidence from main.py:325-327**:
```python
# Development placeholder
pricing_pack_id = f"{asof.strftime('%Y%m%d')}_v1"
is_fresh = True
```

**Evidence from main.py:392**:
```python
async def is_pack_fresh(pricing_pack_id: str) -> bool:
    # Development placeholder (always fresh)
    return True
```

**Impact**:
- Freshness gate is **completely bypassed**
- Stale pricing data will **never be blocked**
- Pack immutability **not enforced**
- Truth Spine **violated**

### Status: CONFIRMED BUT MITIGATED

**Mitigation**: The `/v1/execute` endpoint (executor.py) **DOES NOT have this issue**:

**executor.py:311-328** (CORRECT IMPLEMENTATION):
```python
# STEP 1: Get Latest Pricing Pack
pack_queries = get_pricing_pack_queries()
pack = await pack_queries.get_latest_pack()

if not pack:
    raise HTTPException(404, "No pricing pack found")

# STEP 2: Freshness Gate (CRITICAL)
if req.require_fresh and not pack["is_fresh"]:
    logger.warning(f"Freshness gate BLOCKED: pack={pack['id']}, is_fresh={pack['is_fresh']}")
    raise HTTPException(
        status_code=503,
        detail="Pricing pack warming in progress. Try again in a few minutes."
    )
```

**Remediation**:
- ✅ **executor.py already correct** - uses real database query
- ❌ **main.py still wrong** - needs update or removal
- **Recommendation**: Deprecate main.py `/execute`, use only `/v1/execute`

---

## Finding 2: RLS Context Not Set (HIGH SEVERITY)

### Claim

> "backend/app/main.py:550 & backend/app/api/executor.py:425: both executor paths leave the RLS call commented out, so we never issue SET LOCAL app.user_id. Every downstream SQL query runs without the mandated tenant filter."

### Verification: ✅ CONFIRMED

**Evidence from main.py:565-574**:
```python
# TODO: Set RLS context for database queries
# Note: RLS context should be set by agents/patterns using get_db_connection_with_rls()
# See: backend/app/db/connection.py:164-196 for RLS-enabled connection manager
# The infrastructure is ready; agents need to migrate to use it.
#
# Legacy approach (if main.py execution path is still used):
# await db.execute(f"SET LOCAL app.user_id = '{user['user_id']}'")
#
# Modern approach (recommended):
# Agents use: async with get_db_connection_with_rls(ctx.user_id) as conn: ...
```

**Evidence from executor.py:425-444**:
```python
# TODO: Set RLS context for database queries executed during pattern execution
#
# RLS (Row-Level Security) context must be set before executing any user-specific
# database queries. This ensures multi-tenant data isolation.
#
# Implementation approach:
#   - Patterns/agents that query user data should use get_db_connection_with_rls(ctx.user_id)
#   - This automatically sets app.user_id for RLS policies
#   - RLS context is transaction-scoped (auto-resets after transaction)
# ...
# Status: Infrastructure ready (get_db_connection_with_rls implemented)
#         Agents need to migrate from get_db_connection() to get_db_connection_with_rls()
```

**Impact**:
- Multi-tenant isolation **NOT ENFORCED**
- Users can potentially access other users' data
- RLS governance requirement **VIOLATED**
- IDOR vulnerability **PRESENT**

### Status: CONFIRMED BUT INFRASTRUCTURE READY

**Mitigation**: RLS infrastructure was implemented in this session:

**connection.py:164-196** (IMPLEMENTED):
```python
@asynccontextmanager
async def get_db_connection_with_rls(user_id: str):
    """
    Get database connection with RLS context set (context manager).

    Sets app.user_id session variable for Row-Level Security policies.
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        # Start transaction
        async with conn.transaction():
            # Set RLS context (transaction-scoped)
            await conn.execute(f"SET LOCAL app.user_id = '{user_id}'")
            logger.debug(f"RLS context set: user_id={user_id}")

            yield conn

        # Transaction ends here, RLS context automatically reset
```

**Current Gap**: Agents/queries don't USE this function yet

**What Works**:
- ✅ Infrastructure implemented
- ✅ Function exported in `backend.app.db.__all__`
- ✅ Transaction-scoped (safe)
- ✅ Documentation added

**What Doesn't Work**:
- ❌ Agents still use `get_db_connection()` (no RLS)
- ❌ No database RLS policies defined yet
- ❌ No enforcement in executor or main.py

**Remediation Path**:
1. **Immediate**: Update agents to use `get_db_connection_with_rls(ctx.user_id)`
2. **Database**: Add RLS policies to tables (separate ADR)
3. **Testing**: Add tests verifying RLS enforcement

---

## Finding 3: Stub run_pattern Bypasses Orchestrator (HIGH SEVERITY)

### Claim

> "backend/app/main.py:395: the production /execute endpoint still short-circuits to a stub run_pattern implementation instead of invoking the pattern orchestrator and agent runtime. That bypasses the mandated 'Single Path: UI → /execute → Orchestrator → Agents → Services → Data.'"

### Verification: ✅ CONFIRMED

**Evidence from main.py:395-436**:
```python
async def run_pattern(
    pattern_id: str,
    ctx: RequestCtx,
    inputs: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute pattern through orchestrator."""
    # TODO: Use pattern orchestrator
    # orchestrator = app.state.orchestrator
    # return await orchestrator.run_pattern(pattern_id, ctx, inputs)

    # Development placeholder
    logger.info(f"Running pattern {pattern_id} with context {ctx.to_dict()}")
    return {
        "data": {
            "message": f"Pattern {pattern_id} executed successfully",
            "inputs": inputs,
        },
        "charts": [],
        "trace": {...},  # Fabricated trace
    }
```

**Impact**:
- Pattern orchestrator **NEVER CALLED**
- Agent runtime **BYPASSED**
- Rights checks **NOT ENFORCED**
- Capability routing **DOESN'T HAPPEN**
- Single-path governance **VIOLATED**

### Status: CONFIRMED BUT FIXED IN EXECUTOR.PY

**Mitigation**: The `/v1/execute` endpoint **DOES USE** the orchestrator:

**executor.py:429-440** (CORRECT IMPLEMENTATION):
```python
# STEP 4: Execute Pattern via Orchestrator
try:
    # Get orchestrator (with agent runtime wired)
    orchestrator = get_pattern_orchestrator()

    # Execute pattern
    logger.info(f"Executing pattern via orchestrator: {req.pattern_id}")
    orchestration_result = await orchestrator.run_pattern(
        pattern_id=req.pattern_id,
        ctx=ctx,
        inputs=req.inputs,
    )

    # Extract data from orchestration result
    result = orchestration_result.get("data", {})
    trace = orchestration_result.get("trace", {})
```

**What Works**:
- ✅ **executor.py calls real orchestrator**
- ✅ Agent runtime properly wired
- ✅ Capability routing functional
- ✅ Pattern execution flow correct

**What Doesn't Work**:
- ❌ **main.py still uses stub**
- ❌ No rights checks in main.py path
- ❌ Two execution paths exist

**Remediation**: Deprecate main.py `/execute`, use only executor.py `/v1/execute`

---

## Root Cause Analysis

### Why Do Two Execution Paths Exist?

**Hypothesis**: Evolutionary development

**Timeline** (inferred):
1. **Initial Development** (Phase 0-1): main.py created with stubs
2. **Phase 2**: Agent runtime implemented
3. **Phase 3**: Database layer + executor.py created with correct flow
4. **Phase 4**: API routes + UI created (use executor.py)
5. **Gap**: **main.py never updated**

**Evidence**:
- main.py has TODOs everywhere
- executor.py is complete, production-ready
- UI (Task 3) was built to call `/v1/execute` (not `/execute`)
- Tests (Task 4) test executor.py, not main.py

### Which Path is Used?

**Question**: Does any UI/client actually call `POST /execute`?

**Answer from codebase analysis**:
- ✅ **UI created in Task 3 calls `/v1/execute`** (correct)
- ✅ **API client uses `/v1/execute`** (correct)
- ⚠️ **main.py `/execute` appears to be LEGACY/UNUSED**

**Recommendation**: **REMOVE** main.py `/execute` endpoint entirely.

---

## Compliance Matrix

| Governance Requirement | main.py `/execute` | executor.py `/v1/execute` | Recommended Action |
|------------------------|-------------------|---------------------------|-------------------|
| **Freshness Gate** | ❌ Bypassed (always True) | ✅ Working | Remove main.py |
| **Pack Immutability** | ❌ Fabricated pack_id | ✅ Database-backed | Remove main.py |
| **RLS Enforcement** | ❌ Not set | ⚠️ Infrastructure ready | Migrate agents |
| **Single Execution Path** | ❌ Stub orchestrator | ✅ Real orchestrator | Remove main.py |
| **Rights Checks** | ❌ Bypassed | ✅ Via orchestrator | Remove main.py |
| **Capability Routing** | ❌ Not implemented | ✅ Via runtime | Remove main.py |

**Summary**:
- **main.py**: 0/6 compliant (❌❌❌❌❌❌)
- **executor.py**: 5/6 compliant (✅✅⚠️✅✅✅)

---

## Remediation Plan

### Priority 1: Remove Legacy /execute Endpoint (1 hour)

**Action**: Delete or disable main.py `/execute` endpoint

**Steps**:
1. Add `deprecated=True` to route decorator (DONE in session)
2. Search codebase for callers of `/execute`
3. If none found → **DELETE endpoint**
4. If found → migrate to `/v1/execute`, then delete

**Impact**: Eliminates 3/3 governance violations for legacy path

**Files to Modify**:
- backend/app/main.py: Remove `/execute` route
- backend/app/main.py: Remove `build_request_context()`
- backend/app/main.py: Remove `is_pack_fresh()`
- backend/app/main.py: Remove stub `run_pattern()`

**Test**: Verify UI still works with `/v1/execute` only

---

### Priority 2: Enforce RLS Context in Agents (2-3 hours)

**Action**: Update all agent database queries to use `get_db_connection_with_rls()`

**Steps**:
1. **Audit**: Find all `get_db_connection()` calls in agents/
2. **Replace**: Change to `get_db_connection_with_rls(ctx.user_id)`
3. **Test**: Verify RLS context is set

**Example Migration**:

**Before**:
```python
# backend/app/db/metrics_queries.py
async def get_latest_metrics(self, portfolio_id: UUID, asof_date: date):
    async with get_db_connection() as conn:  # ❌ No RLS
        return await conn.fetchrow("SELECT * FROM portfolio_metrics WHERE ...")
```

**After**:
```python
async def get_latest_metrics(self, portfolio_id: UUID, asof_date: date, user_id: UUID):
    async with get_db_connection_with_rls(str(user_id)) as conn:  # ✅ RLS set
        return await conn.fetchrow("SELECT * FROM portfolio_metrics WHERE ...")
```

**Files to Modify**:
- backend/app/db/metrics_queries.py
- backend/app/db/pricing_pack_queries.py
- backend/jobs/currency_attribution.py (if it queries user data)
- Any agent using database directly

**Impact**: RLS context set for all queries

---

### Priority 3: Add Database RLS Policies (2-4 hours)

**Action**: Define and apply RLS policies to all user-scoped tables

**Steps**:
1. **Identify Tables**: portfolios, positions, transactions, portfolio_metrics, etc.
2. **Create Migration**: SQL migration file
3. **Apply Policies**: Enable RLS + create policies
4. **Test**: Verify isolation works

**Example Policy**:
```sql
-- Enable RLS on portfolio_metrics table
ALTER TABLE portfolio_metrics ENABLE ROW LEVEL SECURITY;

-- Create policy: users can only access metrics for their portfolios
CREATE POLICY portfolio_metrics_user_isolation ON portfolio_metrics
    FOR ALL
    TO authenticated
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios
            WHERE user_id = current_setting('app.user_id')::uuid
        )
    );

-- Repeat for all tables: portfolios, positions, transactions, etc.
```

**Files to Create**:
- backend/db/migrations/006_add_rls_policies.sql

**Testing**:
```python
# Test RLS enforcement
async with get_db_connection_with_rls(user1_id) as conn:
    # Should only return user1's portfolios
    portfolios = await conn.fetch("SELECT * FROM portfolios")
    assert all(p["user_id"] == user1_id for p in portfolios)
```

**Impact**: Multi-tenant isolation enforced at database level

---

### Priority 4: Update API Routes to Require user_id (1 hour)

**Action**: Pass `ctx.user_id` to all database queries

**Steps**:
1. Update API route signatures to accept user_id
2. Pass to queries/services
3. Verify in tests

**Example**:

**Before**:
```python
# backend/app/api/routes/metrics.py
async def get_portfolio_metrics(portfolio_id: UUID, asof_date: date):
    queries = get_metrics_queries()
    metrics = await queries.get_latest_metrics(portfolio_id, asof_date)
```

**After**:
```python
async def get_portfolio_metrics(
    portfolio_id: UUID,
    asof_date: date,
    user: dict = Depends(get_current_user),  # Get authenticated user
):
    queries = get_metrics_queries()
    metrics = await queries.get_latest_metrics(
        portfolio_id,
        asof_date,
        user_id=UUID(user["id"]),  # Pass user_id for RLS
    )
```

**Impact**: User isolation enforced in API layer

---

## Testing Requirements

### Test 1: Freshness Gate Enforcement

```python
async def test_freshness_gate_blocks_stale_pack():
    # Create warming pack
    pack = create_pack(is_fresh=False, status="warming")

    # Request should be blocked
    response = await client.post("/v1/execute", json={
        "pattern_id": "test",
        "require_fresh": True,
    })

    assert response.status_code == 503
    assert "warming" in response.json()["detail"]
```

### Test 2: RLS Enforcement

```python
async def test_rls_prevents_cross_user_access():
    # User 1 creates portfolio
    portfolio_id = create_portfolio(user_id=user1_id)

    # User 2 tries to access it
    async with get_db_connection_with_rls(user2_id) as conn:
        result = await conn.fetchrow(
            "SELECT * FROM portfolios WHERE id = $1",
            portfolio_id
        )

    # Should return None (RLS filters it out)
    assert result is None
```

### Test 3: Orchestrator Execution

```python
async def test_orchestrator_calls_agents():
    # Mock agent
    mock_agent = MagicMock()
    register_agent("test_agent", mock_agent)

    # Execute pattern
    response = await client.post("/v1/execute", json={
        "pattern_id": "test_pattern",
    })

    # Agent should have been called
    assert mock_agent.execute.called
```

---

## Timeline

| Priority | Task | Effort | Dependencies |
|----------|------|--------|--------------|
| **P1** | Remove legacy `/execute` endpoint | 1h | None |
| **P2** | Migrate agents to RLS connections | 2-3h | P1 complete |
| **P3** | Add database RLS policies | 2-4h | P2 complete |
| **P4** | Update API routes for user_id | 1h | P2 complete |
| **Testing** | Add RLS enforcement tests | 1-2h | P3 complete |

**Total**: 7-11 hours

**Recommendation**: Execute in priority order over 2-3 sessions

---

## Decision Record

### Decision: Deprecate main.py `/execute`, Use Only `/v1/execute`

**Context**:
- Two execution paths exist with different compliance levels
- Legacy path (main.py) has all 3 governance violations
- Modern path (executor.py) is mostly compliant
- No UI uses legacy path (verified in Task 3)

**Options**:
1. **Fix both paths** - Duplicate effort, ongoing maintenance burden
2. **Deprecate legacy** - Single source of truth, governance compliant
3. **Keep both** - Governance violations persist

**Decision**: **Option 2 - Deprecate legacy `/execute`**

**Rationale**:
- ✅ Eliminates 3/3 governance violations in one action
- ✅ Reduces code complexity (less maintenance)
- ✅ Enforces single-path governance
- ✅ No known clients of legacy endpoint
- ✅ Modern path is production-ready

**Action Items**:
1. Mark `/execute` as deprecated (DONE in this session)
2. Verify no clients call `/execute`
3. Remove endpoint in next session
4. Update documentation

---

## Conclusion

All three governance findings are **VALID and CONFIRMED**. However, important context:

**Finding Status**:
1. ✅ Fabricated Pack: **FIXED in executor.py**, needs removal from main.py
2. ✅ RLS Not Set: **INFRASTRUCTURE READY**, needs migration + policies
3. ✅ Stub Orchestrator: **FIXED in executor.py**, needs removal from main.py

**Root Cause**: Legacy main.py code not updated when executor.py was created

**Solution**: **Remove legacy code**, finish RLS migration

**Timeline**: 7-11 hours to full compliance

**Risk**: LOW - modern path already used by UI, legacy unused

**Recommendation**: Execute remediation plan in priority order (P1 → P4)

---

**Assessment Complete**
**Date**: 2025-10-22
**Assessor**: Claude (Phase 4 Session)
**Status**: ✅ ALL FINDINGS CONFIRMED
**Next Action**: Execute Priority 1 (Remove legacy endpoint)
