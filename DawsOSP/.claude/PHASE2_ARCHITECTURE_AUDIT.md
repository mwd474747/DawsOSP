# Phase 2 Architecture Audit Report

**Date**: 2025-10-22
**Auditor**: Claude (Orchestrator Agent)
**Status**: ⚠️ CONFLICTS DETECTED

---

## Executive Summary

**Phase 2 Work Completed**:
- ✅ Task 1 Complete: Executor API with freshness gate (5 files, 1,614 lines)
- ✅ Task 2 Complete: Pattern Orchestrator with template resolution (5 files, 1,369 lines)
- ⏳ Task 3-6: Not yet started

**Critical Findings**:
1. ⚠️ **DUPLICATE FILES**: Phase 2 created files that overlap with existing backend/app/ structure
2. ⚠️ **ARCHITECTURE FORK**: Two parallel implementations exist (backend/api vs backend/app)
3. ✅ **NO VIOLATIONS**: Phase 2 code follows PRODUCT_SPEC v2.0 architecture correctly
4. ✅ **PATTERN ALIGNMENT**: Patterns align with project goals (portfolio-first, reproducibility)

**Recommendation**: **CONSOLIDATE** - Merge Phase 2 files into backend/app/ structure, remove duplicates

---

## Detailed Findings

### 1. File Conflicts (CRITICAL)

#### Duplicate: types.py

**Phase 2 File** (NEW):
- Location: `backend/core/types.py`
- Lines: 400
- Purpose: Executor API types (ExecReq, ExecResp, ExecError, PackHealth)
- Date: 2025-10-22
- Focus: **API contracts for executor and orchestrator**

**Existing File** (OLD):
- Location: `backend/app/core/types.py`
- Lines: 691
- Purpose: Domain types (RequestCtx, ValuationRequest, QualityScore, etc.)
- Date: 2025-10-21
- Focus: **Domain models and capability protocols**

**Analysis**:
- ❌ **CONFLICT**: Both define `RequestCtx` (immutable context)
- ✅ **COMPLEMENTARY**: Phase 2 adds API types missing from existing file
- 🔧 **RESOLUTION**: Merge both files into single `backend/app/core/types.py`

**RequestCtx Differences**:

| Field | Phase 2 (backend/core) | Existing (backend/app) | Conflict? |
|-------|------------------------|------------------------|-----------|
| user_id | str | UUID | ❌ YES |
| pricing_pack_id | str | str | ✅ OK |
| ledger_commit_hash | str | str | ✅ OK |
| trace_id | Optional[str] | str | ⚠️ MINOR |
| request_id | Optional[str] | str | ⚠️ MINOR |
| asof_date | date (required) | - | ⚠️ MISSING |
| require_fresh | bool | - | ⚠️ MISSING |
| portfolio_id | Optional[str] | Optional[UUID] | ⚠️ TYPE |
| base_currency | Optional[str] | str (default="USD") | ⚠️ MINOR |
| rights_profile | - | Optional[str] | ⚠️ MISSING |

**Verdict**: **INCOMPATIBLE** - RequestCtx must be unified with correct types

---

#### Duplicate: orchestrator.py

**Phase 2 File** (NEW):
- Location: `backend/patterns/orchestrator.py`
- Lines: 396
- Purpose: Pattern execution with template resolution
- Date: 2025-10-22
- Focus: **Sequential DAG execution for patterns**

**Existing File** (OLD):
- Location: `backend/app/core/pattern_orchestrator.py`
- Lines: 501
- Purpose: Pattern execution with tracing
- Date: 2025-10-21
- Focus: **Pattern execution with Trace class**

**Analysis**:
- ✅ **SIMILAR**: Both implement pattern execution
- ⚠️ **DIFFERENCES**: Phase 2 is simpler (no Redis, no complex tracing)
- 🔧 **RESOLUTION**: Keep existing file, add Phase 2 improvements (better template resolution)

**Key Differences**:

| Feature | Phase 2 | Existing | Best? |
|---------|---------|----------|-------|
| Template resolution | ✅ Recursive, clean | ✅ Basic | Phase 2 |
| Tracing | ❌ Basic | ✅ Comprehensive | Existing |
| Caching | ❌ None | ✅ Redis | Existing |
| Conditional steps | ✅ Simple eval | ✅ eval | Both |
| State management | ✅ Clean | ✅ Clean | Both |

**Verdict**: **MERGE** - Keep existing file, port Phase 2 template resolver

---

### 2. New Files (Phase 2)

#### backend/api/executor.py (358 lines) ✅

**Status**: ✅ NEW - No conflicts
**Purpose**: Main entry point for pattern execution
**Architecture Compliance**: ✅ PASS

**Key Features**:
- POST /v1/execute endpoint with freshness gate
- Blocks when pack.is_fresh=false (returns 503)
- Constructs immutable RequestCtx
- Integrates with PatternOrchestrator

**Architecture Review**:
- ✅ Follows PRODUCT_SPEC v2.0 execution flow
- ✅ Implements freshness gate correctly (critical)
- ✅ Error handling (4xx client, 5xx server)
- ✅ Reproducibility (pricing_pack_id + ledger_commit_hash in metadata)

**Issues**:
- ⚠️ Uses `backend.patterns.orchestrator` (Phase 2) instead of `backend.app.core.pattern_orchestrator` (existing)
- ⚠️ Should be in `backend/app/api/executor.py` (not `backend/api/`)

---

#### backend/api/health.py (199 lines) ✅

**Status**: ✅ NEW - No conflicts
**Purpose**: Pack health monitoring endpoint
**Architecture Compliance**: ✅ PASS

**Key Features**:
- GET /health/pack endpoint
- Returns pack status (warming/fresh/error/stale)
- Includes estimated_ready time

**Architecture Review**:
- ✅ Follows observability best practices
- ✅ Status mapping correct (is_fresh → fresh, !is_fresh → warming)
- ✅ Error handling

**Issues**:
- ⚠️ Should be in `backend/app/api/health.py` (not `backend/api/`)

---

#### backend/db/pricing_pack_queries.py (279 lines) ✅

**Status**: ✅ NEW - No conflicts
**Purpose**: Database queries for pricing pack operations
**Architecture Compliance**: ✅ PASS

**Key Features**:
- get_latest_pack() - Get most recent pack
- get_pack_health() - Get pack status
- mark_pack_fresh() - Update after pre-warm
- get_ledger_commit_hash() - Get git hash

**Architecture Review**:
- ✅ Stub implementation with TODO markers (correct for Phase 2)
- ✅ Parameterized queries (no SQL injection)
- ✅ Pack status derived from multiple fields

**Issues**:
- ⚠️ Should be in `backend/app/db/` (not `backend/db/`)
- ℹ️ Stubs need implementation (expected, marked with TODO)

---

#### backend/patterns/loader.py (310 lines) ✅

**Status**: ✅ NEW - No conflicts
**Purpose**: Pattern loading with validation
**Architecture Compliance**: ✅ PASS

**Key Features**:
- Load patterns from JSON files
- Schema validation
- In-memory caching

**Architecture Review**:
- ✅ Clean implementation
- ✅ Validation prevents malformed patterns
- ✅ Cache improves performance

**Issues**:
- ⚠️ Should be in `backend/app/patterns/` (not `backend/patterns/`)

---

#### backend/patterns/portfolio_overview.json (66 lines) ✅

**Status**: ✅ NEW - No conflicts
**Purpose**: Sample pattern for testing
**Architecture Compliance**: ✅ PASS

**Pattern Structure**:
```json
{
  "id": "portfolio_overview",
  "version": "1.0",
  "steps": [
    {"capability": "ledger.positions", ...},
    {"capability": "pricing.apply_pack", ...},
    {"capability": "metrics.compute_twr", ...}
  ],
  "outputs": ["perf_metrics", "valued_positions", "charts"]
}
```

**Architecture Review**:
- ✅ Follows pattern schema
- ✅ Template variables used correctly ({{inputs.x}}, {{state.y}}, {{ctx.z}})
- ✅ Sequential execution (DAG)

**Issues**:
- ⚠️ Should be in `backend/app/patterns/` (not `backend/patterns/`)

---

### 3. Architecture Violations

#### ❌ VIOLATION #1: Directory Structure Fork

**Issue**: Phase 2 created parallel directory structure

```
backend/
├── api/                    ← Phase 2 (NEW)
│   ├── executor.py
│   └── health.py
├── core/                   ← Phase 2 (NEW)
│   └── types.py
├── db/                     ← Phase 2 (NEW)
│   └── pricing_pack_queries.py
├── patterns/               ← Phase 2 (NEW)
│   ├── loader.py
│   ├── orchestrator.py
│   └── portfolio_overview.json
└── app/                    ← Existing (OLD)
    ├── api/
    ├── core/
    │   ├── types.py        ← DUPLICATE
    │   ├── pattern_orchestrator.py  ← DUPLICATE
    │   └── agent_runtime.py
    ├── integrations/
    └── agents/
```

**Why This Happened**:
- Phase 2 plan didn't specify `backend/app/` prefix
- Implementation stubs showed `backend/api/` (not `backend/app/api/`)
- No context about existing backend/app/ structure

**Impact**:
- ⚠️ Imports will break (module resolution)
- ⚠️ Duplicates cause confusion
- ⚠️ Tests reference wrong modules

**Resolution**:
1. Move all Phase 2 files into `backend/app/` structure
2. Merge duplicate types.py
3. Merge duplicate orchestrator.py
4. Update imports in all Phase 2 files

---

#### ❌ VIOLATION #2: RequestCtx Type Incompatibility

**Issue**: Phase 2 RequestCtx uses `str` for user_id, existing uses `UUID`

**Phase 2** (backend/core/types.py):
```python
@dataclass(frozen=True)
class RequestCtx:
    user_id: str  # ← String
    pricing_pack_id: str
    ledger_commit_hash: str
    asof_date: date
    require_fresh: bool = True
    portfolio_id: Optional[str] = None
```

**Existing** (backend/app/core/types.py):
```python
@dataclass(frozen=True)
class RequestCtx:
    user_id: UUID  # ← UUID
    pricing_pack_id: str
    ledger_commit_hash: str
    trace_id: str
    request_id: str
    portfolio_id: Optional[UUID] = None
```

**Why This Matters**:
- Database uses UUIDs for user_id, portfolio_id
- Type safety broken if using strings
- Existing code expects UUIDs

**Resolution**:
- Use UUID types (existing file is correct)
- Add missing fields from Phase 2 (asof_date, require_fresh)

---

#### ✅ NO VIOLATION: Architecture Pattern Compliance

**Verified Against PRODUCT_SPEC v2.0**:

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Freshness gate blocks when pack warming | ✅ PASS | executor.py:183-208 blocks on !is_fresh |
| RequestCtx is immutable | ✅ PASS | frozen=True dataclass |
| Reproducibility (pack ID + ledger hash) | ✅ PASS | Metadata includes both |
| Sequential execution | ✅ PASS | Orchestrator runs steps in order |
| Template resolution | ✅ PASS | {{inputs.x}}, {{state.y}}, {{ctx.z}} work |
| Error handling (4xx/5xx) | ✅ PASS | Correct HTTP status codes |

**Verdict**: ✅ Phase 2 code follows architecture correctly

---

### 4. Pattern Alignment with Project Goals

**Project Goals** (from PRODUCT_SPEC v2.0):
1. **Portfolio-first**: Every request scoped to portfolio
2. **Reproducibility**: Same pack + ledger → same results
3. **Compliance**: Data usage rights enforced
4. **Performance**: <2s cold, <1.2s warm

**Pattern Review**: portfolio_overview.json

| Goal | Status | Evidence |
|------|--------|----------|
| Portfolio-first | ✅ PASS | Requires portfolio_id input |
| Reproducibility | ✅ PASS | Uses ctx.pricing_pack_id, ctx.ledger_commit_hash |
| Compliance | ⏳ TODO | Rights gate not yet implemented (Task 5) |
| Performance | ⏳ TODO | No caching yet (sequential only) |

**Pattern Structure**:
```json
{
  "id": "portfolio_overview",
  "inputs": {"portfolio_id": {"required": true}},
  "steps": [
    {"capability": "ledger.positions", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}},
    {"capability": "pricing.apply_pack", "args": {"pack_id": "{{ctx.pricing_pack_id}}"}},
    {"capability": "metrics.compute_twr", ...}
  ],
  "outputs": ["perf_metrics", "valued_positions", "charts"]
}
```

**Analysis**:
- ✅ **Portfolio-scoped**: Requires portfolio_id, passes through all steps
- ✅ **Immutable pack**: Uses ctx.pricing_pack_id (no live prices)
- ✅ **Clear outputs**: Declares what data returned
- ✅ **Composable**: Steps call capabilities (not direct code)

**Verdict**: ✅ Pattern aligns with project goals

---

## Architecture Decision Analysis

### Decision 1: Sequential vs Parallel Execution

**Phase 2 Implementation**: Sequential only

**Justification**:
- PRODUCT_SPEC Sprint 1 Week 2: "DAG runner stub (sequential only)"
- Parallel execution planned for Sprint 2 Week 1
- Correct decision for Phase 2 scope

**Verdict**: ✅ CORRECT

---

### Decision 2: Stub Database Queries

**Phase 2 Implementation**: Mock queries with TODO markers

**Justification**:
- Phase 1 completed data layer (jobs, reconciliation)
- Phase 2 focuses on execution path (API → orchestrator → runtime)
- Database wiring planned for Sprint 1 Week 3

**Verdict**: ✅ CORRECT

---

### Decision 3: No Redis Caching

**Phase 2 Implementation**: No caching in orchestrator

**Justification**:
- Existing orchestrator (backend/app/core/) has Redis support
- Phase 2 focused on core execution flow
- Caching is optimization, not critical path

**Verdict**: ⚠️ ACCEPTABLE (will merge with existing)

---

### Decision 4: Template Resolution Approach

**Phase 2 Implementation**: Recursive resolver with {{syntax}}

**Analysis**:
- ✅ Clean implementation
- ✅ Supports nested dicts/lists
- ✅ Clear error messages
- ⚠️ Uses eval() for conditions (security concern)

**Recommendation**: Keep Phase 2 resolver, replace eval() with safe expression evaluator

**Verdict**: ✅ GOOD (with eval() caveat)

---

## Code Quality Review

### Positive Findings ✅

1. **Clean Code**: All Phase 2 files well-structured, commented
2. **Type Safety**: Uses dataclasses, type hints throughout
3. **Error Handling**: Proper exception handling, HTTP status codes
4. **Logging**: Comprehensive logging for debugging
5. **Documentation**: Docstrings for all functions
6. **Testing**: 8 executor tests, 9 orchestrator tests (all pass)

### Issues Found ⚠️

1. **Directory Structure**: Files in wrong locations
2. **Duplicate Types**: RequestCtx defined twice with conflicts
3. **Duplicate Orchestrator**: Two implementations
4. **eval() Usage**: Security risk in condition evaluation
5. **Import Paths**: Will break when files moved

---

## Cleanup Plan

### Phase 1: Move Files to Correct Locations

```bash
# Create directories
mkdir -p backend/app/api
mkdir -p backend/app/db
mkdir -p backend/app/patterns

# Move Phase 2 files
mv backend/api/executor.py backend/app/api/executor.py
mv backend/api/health.py backend/app/api/health.py
mv backend/db/pricing_pack_queries.py backend/app/db/pricing_pack_queries.py
mv backend/patterns/loader.py backend/app/patterns/loader.py
mv backend/patterns/portfolio_overview.json backend/app/patterns/portfolio_overview.json

# Remove empty directories
rmdir backend/api
rmdir backend/db
```

### Phase 2: Merge types.py

**Strategy**: Merge into `backend/app/core/types.py`

**Add from Phase 2**:
- ExecReq, ExecResp, ExecError
- ErrorCode enum
- PackStatus, PackHealth
- PatternStep, Pattern
- CapabilityResult, AgentCapability
- ExecutionTrace

**Fix RequestCtx**:
- Use UUID for user_id, portfolio_id (existing is correct)
- Add asof_date field (from Phase 2)
- Add require_fresh field (from Phase 2)
- Keep all existing fields

### Phase 3: Merge orchestrator.py

**Strategy**: Enhance `backend/app/core/pattern_orchestrator.py` with Phase 2 improvements

**Port from Phase 2**:
- Improved template resolver (recursive, cleaner)
- Better error messages

**Keep from Existing**:
- Redis caching
- Comprehensive tracing
- Circuit breaker integration

### Phase 4: Update Imports

**Files to Update**:
- backend/app/api/executor.py
- backend/app/api/health.py
- backend/app/db/pricing_pack_queries.py
- backend/app/patterns/loader.py
- backend/tests/test_executor_freshness_gate.py
- backend/tests/test_pattern_orchestrator.py

**Import Changes**:
```python
# Before
from backend.core.types import RequestCtx
from backend.patterns.orchestrator import PatternOrchestrator

# After
from backend.app.core.types import RequestCtx
from backend.app.core.pattern_orchestrator import PatternOrchestrator
```

### Phase 5: Remove Duplicates

```bash
# Remove Phase 2 duplicates
rm backend/core/types.py
rm backend/patterns/orchestrator.py
rmdir backend/core
rmdir backend/patterns
```

### Phase 6: Run Tests

```bash
# Run all tests to verify no breakage
python -m pytest backend/tests/test_executor_freshness_gate.py -v
python -m pytest backend/tests/test_pattern_orchestrator.py -v
```

---

## Testing Status

### Phase 2 Tests Created

**executor tests** (8 tests, 378 lines):
- ✅ Test 1: Blocks when pack warming (503)
- ✅ Test 2: Allows when pack fresh (200)
- ✅ Test 3: Returns metadata with pack ID + ledger hash
- ✅ Test 4: Pattern not found (404)
- ✅ Test 5: Reconciliation failed (500)
- ✅ Test 6: Fresh override (require_fresh=false)
- ✅ Test 7: Invalid asof_date format (400)
- ✅ Test 8: Pattern execution error (500)

**orchestrator tests** (9 tests, 184 lines):
- ✅ Test 1: Pattern loading
- ✅ Test 2: Sequential execution
- ✅ Test 3: Template resolver (inputs)
- ✅ Test 4: Template resolver (state)
- ✅ Test 5: Template resolver (ctx)
- ✅ Test 6: Nested template resolution
- ✅ Test 7: Conditional steps
- ✅ Test 8: Error handling
- ✅ Test 9: State preservation

**All tests pass** ✅

### Tests Need Updates After Cleanup

- Update import paths after file moves
- Re-run to verify no breakage

---

## Risk Assessment

### Low Risk ✅

**Phase 2 Code Quality**:
- Well-structured, tested, documented
- Follows architecture patterns
- No security issues (except eval())

**Phase 2 Alignment**:
- Matches PRODUCT_SPEC v2.0
- Patterns align with project goals
- Correct scope for Sprint 1 Week 2

### Medium Risk ⚠️

**File Conflicts**:
- Duplicate types.py with incompatible RequestCtx
- Duplicate orchestrator.py with different features
- **Mitigation**: Careful merge preserving best of both

**Import Path Changes**:
- Moving files will break imports
- Tests will fail until updated
- **Mitigation**: Update all imports, re-test

### High Risk (Mitigated) ⚠️

**Architecture Fork**:
- Two parallel implementations (backend/api vs backend/app/)
- **Mitigation**: Consolidate now before continuing
- **Impact if ignored**: Increasing divergence, confusion, bugs

---

## Recommendations

### Immediate Actions (Before Task 3)

1. ✅ **STOP** - Do not continue with Task 3 until cleanup complete
2. 🔧 **CONSOLIDATE** - Merge Phase 2 into backend/app/ structure
3. 🔧 **MERGE TYPES** - Unify RequestCtx with correct types (UUID)
4. 🔧 **UPDATE IMPORTS** - Fix all import paths
5. ✅ **TEST** - Verify all tests pass after changes

### Medium Term (Sprint 1 Week 3)

1. Replace eval() with safe expression evaluator
2. Wire database queries (remove stubs)
3. Add Redis caching to orchestrator
4. Implement remaining tasks (3-6)

### Long Term (Sprint 2+)

1. Parallel execution in orchestrator
2. Advanced template features
3. Pattern versioning
4. Pattern marketplace

---

## Conclusion

**Phase 2 Status**: ✅ WORK QUALITY EXCELLENT, ⚠️ LOCATION WRONG

**Architecture Compliance**: ✅ PASS - No violations in implementation logic

**Pattern Alignment**: ✅ PASS - Patterns follow project goals

**Critical Issue**: ⚠️ Duplicate files in wrong locations

**Action Required**: 🔧 **CONSOLIDATE** before continuing with Task 3

---

**Next Steps**:
1. Execute cleanup plan (6 phases)
2. Verify all tests pass
3. Continue with Task 3 (Agent Runtime)

---

**Status**: ⚠️ CLEANUP REQUIRED
**Last Updated**: 2025-10-22
**Next Action**: Execute cleanup plan, then continue Phase 2
