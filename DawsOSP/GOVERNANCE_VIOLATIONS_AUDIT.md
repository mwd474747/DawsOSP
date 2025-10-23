# DawsOS Governance Violations Audit

**Date**: 2025-10-22
**Auditor**: Claude (Phase 4 Task 1 Post-Completion)
**Status**: CRITICAL - 3 High-Priority Violations Confirmed
**Impact**: Production deployment BLOCKED until resolved

---

## Executive Summary

All three governance violations are **CONFIRMED VALID** with critical security and architectural implications:

1. **Freshness Gate Bypass** - Pack ID fabricated, freshness check unconditionally returns True
2. **RLS Context Not Set** - Database queries execute without user isolation (security violation)
3. **Authentication Stub Returns Invalid UUID** - Causes 500 errors when constructing RequestCtx

**Production Risk**: CRITICAL
**Recommended Action**: BLOCK Phase 4 deployment until violations resolved

---

## Violation 1: Freshness Gate Bypass

**Severity**: HIGH
**Status**: CONFIRMED
**Impact**: Stale pricing data can be served, violating Truth Spine guarantee

### Evidence

**File**: [backend/app/main.py:313-327](backend/app/main.py#L313-L327)

```python
async def build_request_context(
    req: ExecuteRequest,
    user: Dict[str, Any],
    trace_id: str,
) -> RequestCtx:
    """Build immutable request context with reproducibility guarantees."""
    asof = req.asof or date.today()

    # TODO: Query pricing pack from database
    # pack = await db.fetchrow("SELECT id, is_fresh FROM pricing_packs WHERE asof_date = $1", asof)
    # if not pack:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"No pricing pack found for {asof}"
    #     )
    # pricing_pack_id = str(pack["id"])
    # is_fresh = pack["is_fresh"]

    # Development placeholder
    pricing_pack_id = f"{asof.strftime('%Y%m%d')}_v1"  # ❌ FABRICATED
    is_fresh = True  # ❌ UNCONDITIONALLY TRUE
```

**File**: [backend/app/main.py:377-392](backend/app/main.py#L377-L392)

```python
async def is_pack_fresh(pricing_pack_id: str) -> bool:
    """
    Check if pricing pack is fresh (pre-warming completed).

    Args:
        pricing_pack_id: Pricing pack ID to check

    Returns:
        True if pack is fresh, False if still warming
    """
    # TODO: Query database for pack freshness
    # pack = await db.fetchrow("SELECT is_fresh FROM pricing_packs WHERE id = $1", pricing_pack_id)
    # return pack["is_fresh"] if pack else False

    # Development placeholder (always fresh)
    return True  # ❌ UNCONDITIONALLY TRUE
```

### Architectural Impact

The **Freshness Gate** is a core Truth Spine component designed to:
1. Block requests when pricing pack is warming (pre-computation in progress)
2. Ensure reproducible outputs by guaranteeing pack immutability
3. Prevent stale data from being served

**Current state**: Both functions bypass the database and unconditionally allow requests, completely defeating the freshness gate.

### Comparison with New Code

**File**: [backend/app/api/executor.py:324-353](backend/app/api/executor.py#L324-L353)

The executor.py I reviewed during this audit shows the **CORRECT** implementation:

```python
# ========================================
# STEP 2: Freshness Gate (CRITICAL)
# ========================================

if req.require_fresh and not pack["is_fresh"]:
    logger.warning(
        f"Freshness gate BLOCKED: pack={pack['id']}, is_fresh={pack['is_fresh']}, "
        f"prewarm_done={pack['prewarm_done']}"
    )

    # Calculate estimated ready time
    from datetime import timedelta
    estimated_ready = pack["updated_at"] + timedelta(minutes=15)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=ExecError(
            code=ErrorCode.PACK_WARMING,
            message="Pricing pack warming in progress. Try again in a few minutes.",
            details={
                "pack_id": pack["id"],
                "status": pack["status"],
                "prewarm_done": pack["prewarm_done"],
                "estimated_ready": estimated_ready.isoformat(),
            },
            request_id=request_id,
        ).to_dict(),
    )
```

This correctly:
- Queries actual pack from database (line 311: `pack = await pack_queries.get_latest_pack()`)
- Checks `pack["is_fresh"]` boolean
- Blocks with HTTP 503 if warming
- Provides estimated ready time

### Root Cause

The `main.py` file contains **legacy/stub code** predating the Phase 3 database layer implementation. The correct implementation exists in `executor.py` but `main.py` was not updated.

### Fix Required

**Option 1** (Recommended): Remove `build_request_context()` and `is_pack_fresh()` from main.py entirely
- These functions are superseded by executor.py
- main.py should not be handling execution flow (violates single-path governance)

**Option 2**: Update main.py to use Phase 3 database layer
- Replace fabricated pack_id with `pack_queries.get_latest_pack()`
- Implement actual freshness check

**Recommended**: Option 1 + verify main.py does not bypass executor.py

---

## Violation 2: RLS Context Not Set

**Severity**: HIGH
**Status**: CONFIRMED
**Impact**: Database queries execute without user isolation (multi-tenant security violation)

### Evidence

**File**: [backend/app/main.py:550-551](backend/app/main.py#L550-L551)

```python
# TODO: Set RLS context for database queries
# await db.execute(f"SET LOCAL app.user_id = '{user['user_id']}'")
```

**Search Results**: No other occurrences of `SET LOCAL app.user_id` in entire backend codebase.

### Architectural Impact

**Row-Level Security (RLS)** is a PostgreSQL feature that enforces user isolation by filtering queries based on session variables. The DawsOS governance model requires:

1. Every database session sets `app.user_id` before executing queries
2. RLS policies on all tables filter by `current_setting('app.user_id')`
3. Users can ONLY access their own portfolios, positions, metrics

**Current state**: The `SET LOCAL` command is commented out, meaning:
- All users share the same database session context
- RLS policies cannot filter by user (no user_id set)
- Users could potentially access other users' data (if RLS policies exist)

### Security Risk

**Risk Level**: CRITICAL for multi-tenant production deployment

**If RLS policies are enabled** (unknown - need to audit schema):
- All queries will fail (no user_id set → RLS denies access)

**If RLS policies are NOT enabled**:
- All users can access all data (complete security bypass)

### Comparison with Governance Requirements

**DawsOS_Codex_Governance.md** explicitly requires:
> "RLS enforced for all queries"

The code does NOT comply with this requirement.

### Fix Required

1. **Audit database schema** for RLS policy existence
2. **Uncomment** line 551 in main.py (at minimum)
3. **Add RLS context to executor.py** (currently also missing)
4. **Add RLS context to all database query modules**:
   - backend/app/db/metrics_queries.py
   - backend/app/db/pricing_pack_queries.py
   - backend/jobs/currency_attribution.py (if it queries user data)
5. **Write integration tests** verifying RLS enforcement

### Additional Search Required

Need to verify if database connection pooling is used, as RLS context must be set:
- After every connection checkout (if using session pooling)
- OR using a connection wrapper that auto-sets context

---

## Violation 3: Authentication Stub Returns Invalid UUID

**Severity**: HIGH
**Status**: CONFIRMED
**Impact**: 500 errors when constructing RequestCtx, blocks all authenticated requests

### Evidence

**File**: [backend/app/api/executor.py:172-182](backend/app/api/executor.py#L172-L182)

```python
async def get_current_user():
    """
    Get current user from authentication.

    TODO: Implement actual authentication (JWT, OAuth, etc.)

    Returns:
        User object
    """
    # Stub: Return mock user
    return {"id": "U1", "email": "user@example.com"}  # ❌ "U1" is NOT a UUID
```

**File**: [backend/app/api/executor.py:398](backend/app/api/executor.py#L398)

```python
ctx = RequestCtx(
    user_id=UUID(user["id"]) if isinstance(user["id"], str) else user["id"],  # ❌ ValueError
    pricing_pack_id=pack["id"],
    ledger_commit_hash=ledger_commit_hash,
    trace_id=request_id,
    request_id=request_id,
    timestamp=started_at,
    asof_date=asof_date,
    require_fresh=req.require_fresh,
    portfolio_id=UUID(req.portfolio_id) if req.portfolio_id else None,
)
```

### Error Behavior

When line 398 executes `UUID(user["id"])` with `user["id"] = "U1"`:

```python
>>> from uuid import UUID
>>> UUID("U1")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python3.11/uuid.py", line 184, in __init__
    raise ValueError('badly formed hexadecimal UUID string')
ValueError: badly formed hexadecimal UUID string
```

This triggers the exception handler in executor.py:285-292:

```python
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail=ExecError(
        code=ErrorCode.INTERNAL_ERROR,
        message=f"Internal server error: {str(e)}",
        request_id=request_id,
    ).to_dict(),
)
```

**Result**: Every request to `/v1/execute` returns HTTP 500.

### Architectural Impact

This makes the **entire executor API non-functional** in its current state. The auth stub was likely written before RequestCtx required UUID typing.

### Fix Required

**Option 1** (Quick fix for testing):
```python
return {
    "id": "00000000-0000-0000-0000-000000000001",  # Valid UUID
    "email": "user@example.com"
}
```

**Option 2** (Recommended):
```python
from uuid import uuid4

return {
    "id": str(uuid4()),  # Generate random UUID per request
    "email": "user@example.com"
}
```

**Option 3** (Production):
- Implement actual authentication (JWT, OAuth2, etc.)
- Return real user UUID from user database

### Additional Issue

Line 398 has a defensive check:
```python
user_id=UUID(user["id"]) if isinstance(user["id"], str) else user["id"],
```

This suggests an attempt to handle both string and UUID types, but:
- If `user["id"]` is already a UUID, this works
- If `user["id"]` is a string, `UUID(user["id"])` will fail with invalid format
- The check does NOT fix the invalid UUID format

**Better pattern**:
```python
user_id=user["id"] if isinstance(user["id"], UUID) else UUID(user["id"]),
```

But this still fails with "U1". The real fix is making the stub return a valid UUID string.

---

## Comparison: main.py vs executor.py

There appear to be **TWO execution paths** in the codebase:

### Path 1: main.py (Legacy/Stub)
- Location: backend/app/main.py
- Functions: `build_request_context()`, `is_pack_fresh()`
- Status: Uses TODOs and placeholders
- Governance Compliance: FAILING (fabricated pack, no RLS)

### Path 2: executor.py (New/Phase 3+)
- Location: backend/app/api/executor.py
- Functions: `execute()`, `_execute_pattern_internal()`
- Status: Uses actual database layer (Phase 3)
- Governance Compliance: PARTIAL (correct freshness gate, missing RLS, broken auth)

### Hypothesis

The DawsOS codebase underwent architectural evolution:
1. **Initial version**: main.py with stubs (pre-Phase 3)
2. **Phase 3**: Created database layer, executor.py with correct flow
3. **Gap**: main.py never updated to use new database layer

### Governance Violation

**DawsOS_Codex_Governance.md** requires:
> "Single path: UI → /execute → Pattern → Agents → Services"

**Current state**: TWO execution paths exist, violating single-path governance.

### Remediation Required

**Audit Task**: Determine which code paths are actually used by the UI
- Does UI call main.py functions directly?
- Does UI call `/v1/execute` endpoint (executor.py)?
- Are there multiple entry points bypassing the execution stack?

**If main.py is used**: Update it to use Phase 3 database layer
**If main.py is NOT used**: Remove dead code to prevent confusion
**If BOTH are used**: This is a critical architecture violation requiring immediate remediation

---

## Impact Assessment

### Development Impact
- Phase 4 Task 1 (REST API endpoints) created in this session are VALID
- They correctly use Phase 3 database layer
- BUT they inherit the RLS context issue (no user_id set)

### Testing Impact
- Current code cannot pass integration tests
- Authentication will cause 500 errors
- Freshness gate cannot be tested (always passes)
- RLS enforcement cannot be tested (not enabled)

### Production Deployment Impact
- **BLOCKED**: Cannot deploy with these violations
- Multi-tenant security is non-functional
- Truth Spine guarantees are not enforced
- Authentication is broken

### Phase 4 Continuation Impact
- **Task 2** (Agent Capability Wiring): Can proceed (agents don't need auth)
- **Task 3** (UI Portfolio Overview): BLOCKED (needs working API)
- **Task 4** (E2E Integration Tests): BLOCKED (auth broken)
- **Task 5** (Backfill Rehearsal Tool): Can proceed (batch job)
- **Task 6** (Visual Regression Tests): BLOCKED (needs working UI)

**Recommendation**: Fix violations before continuing Phase 4 Tasks 3, 4, 6.

---

## Recommended Fix Order

### Priority 1 (Blocking): Fix Authentication Stub
**Why first**: Blocks ALL testing and development
**Effort**: 1 line change
**File**: backend/app/api/executor.py:182

```python
return {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "user@example.com"
}
```

### Priority 2 (Security): Add RLS Context
**Why second**: Security-critical for multi-tenant deployment
**Effort**: 5-10 lines across 3-4 files
**Files**:
- backend/app/main.py:551 (uncomment)
- backend/app/api/executor.py:~410 (add after RequestCtx construction)
- backend/app/db/*.py (add to query methods)

**Pattern**:
```python
# After constructing RequestCtx, before executing queries
async with db.acquire() as conn:
    await conn.execute(f"SET LOCAL app.user_id = '{ctx.user_id}'")
    # Now execute queries
```

### Priority 3 (Architecture): Fix Freshness Gate
**Why third**: Architecture compliance, but less urgent than auth/security
**Effort**: Remove dead code from main.py OR update to use Phase 3 layer
**Files**:
- backend/app/main.py (remove or update functions)

**Decision Required**: Is main.py execution path still used? (Audit needed)

---

## Testing Requirements

After fixes, the following tests must pass:

### Authentication Tests
```python
def test_auth_stub_returns_valid_uuid():
    user = await get_current_user()
    assert UUID(user["id"])  # Should not raise ValueError

def test_request_context_accepts_auth_user():
    user = await get_current_user()
    ctx = RequestCtx(user_id=UUID(user["id"]), ...)
    assert ctx.user_id is not None
```

### RLS Tests
```python
async def test_rls_context_set_before_query():
    ctx = RequestCtx(user_id=UUID("..."), ...)

    # Set RLS context
    await conn.execute(f"SET LOCAL app.user_id = '{ctx.user_id}'")

    # Query should only return this user's data
    result = await conn.fetchval("SELECT current_setting('app.user_id')")
    assert UUID(result) == ctx.user_id
```

### Freshness Gate Tests
```python
async def test_freshness_gate_blocks_warming_pack():
    # Create a pack with is_fresh=False
    pack = await create_warming_pack()

    # Request with require_fresh=True
    req = ExecuteRequest(pattern_id="test", require_fresh=True)

    # Should raise HTTP 503
    with pytest.raises(HTTPException) as exc:
        await execute(req)

    assert exc.value.status_code == 503
    assert "warming" in exc.value.detail["message"].lower()
```

---

## ADR Recommendation

**Decision**: Create Architecture Decision Record for fix strategy

**Options**:
1. **Quick Fix**: Patch stubs for development continuity
2. **Full Fix**: Implement production-grade auth + RLS immediately
3. **Hybrid**: Fix stubs now, implement prod auth in separate task

**Recommendation**: Hybrid approach
- Fix auth stub to valid UUID (5 minutes)
- Add RLS context setting with TODO for policy audit (30 minutes)
- Remove dead code from main.py (15 minutes)
- Continue Phase 4 with working stubs
- Schedule production auth implementation in Phase 5

**Rationale**: Unblocks development while maintaining awareness of production gaps.

---

## Governance Compliance Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Single execution path | ❌ FAILING | Two paths exist (main.py + executor.py) |
| Freshness gate enforced | ❌ FAILING | main.py bypasses, executor.py works |
| RLS context set | ❌ FAILING | No `SET LOCAL app.user_id` anywhere |
| Pack immutability | ⚠️  PARTIAL | executor.py correct, main.py fabricates |
| Authentication working | ❌ FAILING | Stub returns invalid UUID |

**Overall Compliance**: 0/5 requirements met

---

## Conclusion

All three governance violations are **CONFIRMED VALID** and represent critical gaps in the codebase:

1. **Freshness Gate**: Bypassed in main.py (legacy code), working in executor.py
2. **RLS Context**: Never set anywhere in the codebase (security hole)
3. **Authentication**: Stub returns invalid format (breaks all requests)

**Immediate Action Required**:
1. Fix authentication stub (1 line)
2. Add RLS context setting (3-4 files)
3. Audit/remove dead code in main.py

**Phase 4 Status**: Tasks 1-2 can proceed with fixes; Tasks 3-4-6 blocked until resolution.

**Production Readiness**: NOT READY - critical security and architecture gaps must be addressed.

---

**Report Generated**: 2025-10-22
**Next Step**: Await user decision on fix priority and approach
