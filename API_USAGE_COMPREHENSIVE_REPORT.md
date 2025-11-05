# Comprehensive API Usage Report: DawsOS Executor API

**Date:** November 5, 2025  
**Purpose:** Deep analysis of API usage patterns, architecture, and recent refactoring  
**Status:** ✅ **COMPLETE ANALYSIS**

---

## 📊 Executive Summary

The DawsOS Executor API is a **pattern-driven execution system** that orchestrates multi-step workflows through agent capabilities. The system has undergone significant refactoring in recent phases (Phase 2: Custom Exceptions, Phase 3: Agent Consolidation), resulting in a more robust and maintainable architecture.

**Key Findings:**
- ✅ **Single Entry Point**: `POST /v1/execute` handles all pattern execution
- ✅ **Pattern-Driven**: 13 JSON pattern definitions orchestrate business workflows
- ✅ **Multi-Layer Architecture**: API → Orchestrator → Runtime → Agents → Services
- ✅ **Context-Driven**: RequestCtx ensures reproducibility with pricing_pack_id + ledger_commit_hash
- ⚠️ **Integration Gap**: API layer still uses `pack_queries` directly instead of `PricingService` (Phase 2 finding)
- ⚠️ **Error Handling**: Custom exceptions not fully integrated into API layer (Phase 2 finding)

---

## 🏗️ Architecture Overview

### Request Flow

```
UI (full_ui.html)
  ↓ HTTP POST /v1/execute
Executor API (executor.py)
  ↓ Request Validation + Context Construction
Pattern Orchestrator (pattern_orchestrator.py)
  ↓ Pattern Loading + Step Execution
Agent Runtime (agent_runtime.py)
  ↓ Capability Routing + Retry Logic
Agents (FinancialAnalyst, MacroHound, DataHarvester, ClaudeAgent)
  ↓ Capability Execution
Services (pricing, metrics, scenarios, etc.)
  ↓ Database Queries
PostgreSQL + TimescaleDB
```

### Component Responsibilities

| Component | Lines | Responsibility |
|-----------|-------|----------------|
| **executor.py** | 932 | API endpoint, authentication, context construction, error handling |
| **pattern_orchestrator.py** | 1,120 | Pattern loading, step execution, template substitution, tracing |
| **agent_runtime.py** | 712 | Agent registration, capability routing, retry logic, caching |
| **Agents** | ~3,500 | Capability implementations (28 + 17 + 8 + 6 = 59 capabilities) |
| **Services** | ~2,000 | Business logic (pricing, metrics, scenarios, attribution) |

---

## 🔌 API Endpoints

### 1. POST /v1/execute (Primary Endpoint)

**Purpose:** Execute JSON pattern with full orchestration

**Request Structure:**
```json
{
  "pattern_id": "portfolio_overview",
  "inputs": {
    "portfolio_id": "uuid-here",
    "lookback_days": 252
  },
  "require_fresh": true,
  "asof_date": "2025-11-05",
  "portfolio_id": "uuid-here",
  "security_id": "uuid-here"
}
```

**Response Structure:**
```json
{
  "result": {
    "perf_metrics": {...},
    "currency_attr": {...},
    "valued_positions": [...],
    "sector_allocation": {...},
    "historical_nav": [...]
  },
  "metadata": {
    "pricing_pack_id": "PP_2025-11-05",
    "ledger_commit_hash": "abc123...",
    "pattern_id": "portfolio_overview",
    "asof_date": "2025-11-05",
    "duration_ms": 1234.56,
    "timestamp": "2025-11-05T12:00:00Z"
  },
  "warnings": [],
  "trace_id": "request-uuid"
}
```

**Authentication:**
- Requires JWT token in `Authorization: Bearer <token>` header
- Token must contain `user_id`, `email`, `role` claims
- Uses `verify_token` dependency for validation

**Authorization:**
- Portfolio access checked via RLS policies
- Users can only access their own portfolios (unless ADMIN)
- Access check performed before pattern execution

**Error Responses:**
- `401 Unauthorized` - Missing or invalid JWT token
- `403 Forbidden` - Portfolio access denied
- `503 Service Unavailable` - Pricing pack warming (try again later)
- `404 Not Found` - Pattern not found
- `500 Internal Server Error` - Server error

### 2. GET /health (Health Check)

**Purpose:** Basic health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-05T12:00:00Z"
}
```

### 3. GET /health/pack (Pricing Pack Health)

**Purpose:** Check pricing pack freshness status for monitoring

**Response:**
```json
{
  "status": "fresh",
  "pack_id": "PP_2025-11-05",
  "is_fresh": true,
  "prewarm_done": true,
  "updated_at": "2025-11-05T12:00:00Z",
  "estimated_ready": null
}
```

**Status Codes:**
- `200 OK` - Pack is fresh and ready
- `503 Service Unavailable` - Pack is warming (not ready yet)
- `500 Internal Server Error` - Pack error or not found

**Note:** Currently uses `pack_queries.get_latest_pack()` directly (should use `PricingService.get_latest_pack()` for consistency)

---

## 🔄 Request Execution Flow

### Step 1: Authentication & Request Validation

**Location:** `executor.py:409` (`execute` function)

**Process:**
1. Extract JWT token from `Authorization` header
2. Validate token via `verify_token` dependency
3. Extract user claims (`user_id`, `email`, `role`)
4. Generate `request_id` for tracing
5. Start tracing context (if observability available)

**Error Handling:**
- `HTTPException 401` if token missing/invalid
- Logged and re-raised

### Step 2: Pricing Pack Resolution

**Location:** `executor.py:516` (`_execute_pattern_internal`)

**Current Implementation:**
```python
pack_queries = get_pricing_pack_queries()
pack = await pack_queries.get_latest_pack()

if not pack:
    raise HTTPException(500, ExecError(PACK_NOT_FOUND, ...))
```

**Issue Identified (Phase 2):**
- ⚠️ Uses `pack_queries` directly instead of `PricingService`
- ⚠️ Doesn't catch `PricingPackNotFoundError` or `PricingPackStaleError`
- ⚠️ Manual error handling instead of service layer exceptions

**Recommended Implementation:**
```python
from app.services.pricing import get_pricing_service

pricing_service = get_pricing_service()
try:
    pack = await pricing_service.get_latest_pack(
        require_fresh=False,  # Check freshness separately
        raise_if_not_found=True
    )
except PricingPackNotFoundError as e:
    raise HTTPException(503, ExecError(PACK_NOT_FOUND, ...))
except PricingPackStaleError as e:
    raise HTTPException(503, ExecError(PACK_WARMING, ...))
```

### Step 3: Freshness Gate Enforcement

**Location:** `executor.py:534`

**Process:**
1. Check if `require_fresh=true` (default: true)
2. Check if `pack["is_fresh"]` is true
3. If not fresh, calculate `estimated_ready` time
4. Raise `HTTPException 503` with `PACK_WARMING` error

**Error Response:**
```json
{
  "error": "pricing_pack_warming",
  "message": "Pricing pack warming in progress. Try again in a few minutes.",
  "details": {
    "pack_id": "PP_2025-11-05",
    "status": "warming",
    "prewarm_done": false,
    "estimated_ready": "2025-11-05T12:15:00Z"
  },
  "request_id": "request-uuid",
  "timestamp": "2025-11-05T12:00:00Z"
}
```

**Reconciliation Check:**
- If `pack["reconciliation_failed"]` is true, raise `HTTPException 500` with `PACK_ERROR`

### Step 4: RequestCtx Construction

**Location:** `executor.py:607`

**Context Fields:**
```python
ctx = RequestCtx(
    user_id=UUID(user_id),           # From JWT claims
    pricing_pack_id=pack["id"],      # From latest pack
    ledger_commit_hash=ledger_hash,   # From pack_queries
    trace_id=request_id,              # Same as request_id
    request_id=request_id,             # Generated UUID
    timestamp=started_at,              # Request start time
    asof_date=asof_date,              # From pack date or request
    require_fresh=req.require_fresh,   # From request
    portfolio_id=UUID(portfolio_id), # From request (if provided)
)
```

**Purpose:**
- **Reproducibility**: All results traceable to specific pricing pack + ledger state
- **Multi-Tenancy**: `user_id` used for RLS enforcement
- **Tracing**: `trace_id` and `request_id` for distributed tracing
- **Audit**: `timestamp` and `asof_date` for compliance

### Step 5: Portfolio Access Check

**Location:** `executor.py:640`

**Process:**
1. If `portfolio_id` provided and user is not ADMIN
2. Query `portfolios` table for ownership
3. If no access, raise `HTTPException 403` with `FORBIDDEN` error
4. Log access granted/denied for audit

**RLS Enforcement:**
- All database queries MUST use `get_db_connection_with_rls(ctx.user_id)`
- Sets `app.user_id` for RLS policies
- Transaction-scoped (auto-resets after transaction)

### Step 6: Pattern Execution

**Location:** `executor.py:707` → `pattern_orchestrator.py:564`

**Process:**
1. Load pattern JSON from `backend/patterns/{pattern_id}.json`
2. Validate pattern structure
3. Apply input defaults
4. Initialize execution state (`ctx`, `inputs`)
5. Execute steps sequentially:
   - Resolve template arguments (`{{inputs.x}}`, `{{ctx.y}}`, `{{step_result}}`)
   - Route capability to agent runtime
   - Execute capability with retry logic
   - Store result in state with key from `"as"` field
   - Add step to trace
6. Build execution trace
7. Return result with metadata

**Template Resolution:**
- `{{inputs.portfolio_id}}` → `inputs["portfolio_id"]`
- `{{ctx.pricing_pack_id}}` → `ctx.pricing_pack_id`
- `{{positions.positions}}` → `state["positions"]["positions"]` (from step with `"as": "positions"`)

**Error Handling:**
- `FileNotFoundError` → `HTTPException 404` (pattern not found)
- `ValueError` → `HTTPException 500` (pattern execution error)
- Capability errors → Propagated to orchestrator → API layer

### Step 7: Audit Logging

**Location:** `executor.py:720`

**Process:**
1. Log pattern execution to audit service
2. Include: `user_id`, `pattern_id`, `portfolio_id`, `pricing_pack_id`, `ledger_commit_hash`, `inputs`, `execution_time_ms`
3. Never fail request due to audit logging failure (logged but not re-raised)

### Step 8: Response Construction

**Location:** `executor.py:740`

**Response Includes:**
- `result`: Pattern execution results (from orchestrator)
- `metadata`: Pricing pack ID, ledger hash, pattern ID, asof date, duration, timestamp
- `warnings`: List of warnings (if any)
- `trace_id`: Request ID for tracing

---

## 📋 Pattern Definitions

### Pattern Structure

**13 Patterns Defined:**
1. `portfolio_overview` - Comprehensive portfolio snapshot
2. `portfolio_scenario_analysis` - Stress testing with macro scenarios
3. `portfolio_cycle_risk` - Cycle-based risk analysis
4. `portfolio_macro_overview` - Macro economic integration
5. `holding_deep_dive` - Individual security analysis
6. `corporate_actions_upcoming` - Dividends, splits, corporate actions
7. `macro_cycles_overview` - 4 economic cycles (STDC, LTDC, Empire, Civil)
8. `macro_trend_monitor` - Macro trend tracking
9. `news_impact_analysis` - News sentiment analysis
10. `buffett_checklist` - Quality assessment (A-F grades)
11. `policy_rebalance` - Portfolio optimization
12. `export_portfolio_report` - PDF report generation
13. `cycle_deleveraging_scenarios` - Deleveraging scenario analysis

### Pattern Example

**portfolio_overview.json:**
```json
{
  "id": "portfolio_overview",
  "name": "Portfolio Overview",
  "description": "Comprehensive portfolio snapshot",
  "version": "1.0.0",
  "category": "portfolio",
  "inputs": {
    "portfolio_id": {
      "type": "uuid",
      "required": true
    },
    "lookback_days": {
      "type": "integer",
      "default": 252
    }
  },
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "positions"
    },
    {
      "capability": "pricing.apply_pack",
      "args": {
        "positions": "{{positions.positions}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "as": "valued_positions"
    },
    {
      "capability": "metrics.compute_twr",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "perf_metrics"
    }
  ],
  "outputs": ["perf_metrics", "currency_attr", "valued_positions", "sector_allocation", "historical_nav"]
}
```

### Pattern Execution Flow

1. **Load Pattern** - Read JSON from `backend/patterns/{pattern_id}.json`
2. **Validate Structure** - Check required fields (`id`, `name`, `steps`, `outputs`)
3. **Apply Input Defaults** - Merge request inputs with pattern defaults
4. **Initialize State** - `{"ctx": ctx.to_dict(), "inputs": inputs}`
5. **Execute Steps** - For each step:
   - Resolve template arguments
   - Route to agent runtime
   - Execute capability
   - Store result in state with `"as"` key
   - Add to trace
6. **Build Trace** - Aggregate agents, capabilities, sources, warnings
7. **Return Result** - Extract outputs from state

---

## 🔄 Agent Runtime Integration

### Capability Routing

**Location:** `agent_runtime.py:478` (`execute_capability`)

**Process:**
1. Check request-level cache (if enabled)
2. Find agent for capability (from `capability_map`)
3. Retry with exponential backoff (max 3 retries, 1s/2s/4s delays)
4. Execute capability with dependency injection
5. Cache result (if enabled)
6. Return result with metadata preserved

**Capability Mapping:**
- `ledger.positions` → `FinancialAnalyst.ledger_positions()`
- `pricing.apply_pack` → `FinancialAnalyst.pricing_apply_pack()`
- `macro.run_scenario` → `MacroHound.run_scenario()`
- `data.fetch_news` → `DataHarvester.fetch_news()`

**Retry Logic:**
- Max 3 retries with exponential backoff
- Retry delays: 1s, 2s, 4s
- Logs failures and metrics
- No circuit breaker (removed for simplicity)

**Caching:**
- Request-level cache (cleared after request completes)
- Cache key: MD5 hash of `capability + sorted(args)`
- Cache stats: hits, misses, hit_rate

---

## 🚨 Error Handling Patterns

### Error Propagation Flow

```
Service Layer (pricing.py)
  ↓ Raises PricingPackNotFoundError
Agent Layer (financial_analyst.py)
  ↓ Catches and re-raises
Agent Runtime (agent_runtime.py)
  ↓ Propagates exception
Pattern Orchestrator (pattern_orchestrator.py)
  ↓ Catches and adds to trace
Executor API (executor.py)
  ↓ Catches ValueError/FileNotFoundError
  ↓ Converts to HTTPException
Client (UI)
  ↓ Receives HTTP error response
```

### Error Types

**Service Layer Errors:**
- `PricingPackValidationError` - Invalid pack ID format
- `PricingPackNotFoundError` - Pack doesn't exist
- `PricingPackStaleError` - Pack not fresh

**API Layer Errors:**
- `HTTPException 401` - Authentication failure
- `HTTPException 403` - Authorization failure
- `HTTPException 404` - Pattern not found
- `HTTPException 500` - Internal server error
- `HTTPException 503` - Service unavailable (pack warming)

**Pattern Execution Errors:**
- `FileNotFoundError` → `404 Pattern Not Found`
- `ValueError` → `500 Pattern Execution Error`
- `CapabilityError` → Propagated to API layer

### Error Response Structure

```json
{
  "error": "pricing_pack_warming",
  "message": "Pricing pack warming in progress. Try again in a few minutes.",
  "details": {
    "pack_id": "PP_2025-11-05",
    "status": "warming",
    "prewarm_done": false,
    "estimated_ready": "2025-11-05T12:15:00Z"
  },
  "request_id": "request-uuid",
  "timestamp": "2025-11-05T12:00:00Z"
}
```

### Error Handling Gaps (Phase 2 Findings)

**Issue 1: API Layer Doesn't Catch Custom Exceptions**
- **Location:** `executor.py:516`
- **Current:** Uses `pack_queries.get_latest_pack()` directly
- **Problem:** Doesn't catch `PricingPackNotFoundError` or `PricingPackStaleError`
- **Impact:** Errors propagate as generic `500 Internal Server Error` instead of specific `503 Service Unavailable`

**Issue 2: Health Check Uses Old Pattern**
- **Location:** `executor.py:863` (`health_pack` endpoint)
- **Current:** Uses `pack_queries.get_latest_pack()` directly
- **Problem:** Inconsistent with service layer pattern
- **Impact:** Low (works but inconsistent)

---

## 🔐 Security & Authentication

### JWT Authentication

**Token Structure:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "USER|ADMIN",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Validation:**
- Token verified via `verify_token` dependency
- Expiration checked
- Claims extracted and passed to request handler

**Authorization:**
- Portfolio access checked before pattern execution
- RLS policies enforce multi-tenant data isolation
- Admin users bypass portfolio access checks

### Row-Level Security (RLS)

**Enforcement:**
- All database queries use `get_db_connection_with_rls(ctx.user_id)`
- Sets `app.user_id` for RLS policies
- Transaction-scoped (auto-resets after transaction)

**RLS Policies:**
- Defined in `backend/db/migrations/005_create_rls_policies.sql`
- Enforce multi-tenant data isolation
- Users can only access their own portfolios

---

## 📊 Observability & Tracing

### Request Tracing

**Trace ID Flow:**
1. API generates `request_id` (UUID)
2. `request_id` used as `trace_id` in `RequestCtx`
3. Trace propagated through all layers
4. Trace included in response `metadata`

**Trace Structure:**
```json
{
  "pattern_id": "portfolio_overview",
  "pricing_pack_id": "PP_2025-11-05",
  "ledger_commit_hash": "abc123...",
  "trace_id": "request-uuid",
  "request_id": "request-uuid",
  "steps": [
    {
      "capability": "ledger.positions",
      "duration_seconds": 0.123,
      "agent": "financial_analyst",
      "provenance": {
        "type": "real",
        "sources": ["database"]
      }
    }
  ],
  "agents_used": ["financial_analyst"],
  "capabilities_used": ["ledger.positions", "pricing.apply_pack"],
  "sources": ["database", "pricing_pack"],
  "data_provenance": {
    "overall": "real",
    "types_used": ["real"],
    "warnings": []
  },
  "cache_stats": {
    "hits": 2,
    "misses": 3,
    "total": 5,
    "hit_rate": 0.4
  }
}
```

### Metrics (Optional)

**If Observability Available:**
- Pattern execution duration
- Step execution duration
- Cache hit/miss rates
- Pack freshness status
- Error rates by error type

**Graceful Degradation:**
- If observability not available, metrics disabled
- No failures, just no metrics collected

---

## 🔄 Recent Refactoring Impact

### Phase 2: Custom Exceptions (November 4-5, 2025)

**Changes:**
- ✅ Added `PricingPackValidationError`, `PricingPackNotFoundError`, `PricingPackStaleError`
- ✅ Updated `PricingService` to use custom exceptions
- ✅ Updated `BaseAgent` to use custom exceptions
- ✅ Updated `FinancialAnalyst` to catch and re-raise custom exceptions
- ✅ Updated `ScenariosService` to use custom exceptions

**Impact on API:**
- ⚠️ API layer still uses `pack_queries` directly (not updated)
- ⚠️ Custom exceptions not caught in API layer
- ⚠️ Error responses still use generic `500` instead of specific `503`

**Recommendation:**
- Update `executor.py` to use `PricingService.get_latest_pack()`
- Catch custom exceptions and convert to appropriate HTTP status codes

### Phase 3: Agent Consolidation (November 3, 2025)

**Changes:**
- ✅ Consolidated 9 agents → 4 agents
- ✅ OptimizerAgent → FinancialAnalyst
- ✅ RatingsAgent → FinancialAnalyst
- ✅ ChartsAgent → FinancialAnalyst
- ✅ AlertsAgent → MacroHound
- ✅ ReportsAgent → DataHarvester

**Impact on API:**
- ✅ No changes required (agent runtime handles routing)
- ✅ Patterns continue to work (capability names unchanged)
- ✅ Better performance (fewer agent instances)

---

## 🎯 Integration Patterns

### Frontend Integration

**UI Pattern:**
```javascript
const response = await fetch('/v1/execute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    pattern_id: 'portfolio_overview',
    inputs: {
      portfolio_id: portfolioId,
      lookback_days: 252
    },
    require_fresh: true
  })
});

const data = await response.json();
// data.result contains pattern results
// data.metadata contains pricing_pack_id, ledger_commit_hash, etc.
```

**Error Handling:**
```javascript
if (!response.ok) {
  const error = await response.json();
  if (error.error === 'pricing_pack_warming') {
    // Show retry message with estimated_ready time
    showRetryMessage(error.details.estimated_ready);
  } else if (error.error === 'pricing_pack_not_found') {
    // Show error message
    showError('No pricing pack available');
  }
}
```

### Service Layer Integration

**Pricing Service Pattern:**
```python
from app.services.pricing import get_pricing_service

pricing_service = get_pricing_service()
try:
    pack = await pricing_service.get_latest_pack(
        require_fresh=True,
        raise_if_not_found=True
    )
except PricingPackNotFoundError:
    # Handle no pack available
    raise HTTPException(503, ...)
except PricingPackStaleError:
    # Handle pack not fresh
    raise HTTPException(503, ...)
```

---

## 📝 Recommendations

### Priority 1: API Layer Integration (HIGH)

**Update `executor.py` to use `PricingService`:**
1. Replace `pack_queries.get_latest_pack()` with `PricingService.get_latest_pack()`
2. Catch `PricingPackNotFoundError` and convert to `HTTPException 503`
3. Catch `PricingPackStaleError` and convert to `HTTPException 503`
4. Use `require_fresh=True` for freshness enforcement

**Update `health_pack` endpoint:**
1. Replace `pack_queries.get_latest_pack()` with `PricingService.get_latest_pack()`
2. Catch custom exceptions and convert to appropriate HTTP status codes

### Priority 2: Error Handling Consistency (MEDIUM)

**Standardize Error Responses:**
1. All pricing pack errors should use `503 Service Unavailable`
2. Include `estimated_ready` time for warming packs
3. Include `pack_id` and `status` in error details

### Priority 3: Documentation Updates (LOW)

**Update API Documentation:**
1. Document custom exceptions in API docstring
2. Update error response examples
3. Add integration examples for service layer

---

## ✅ Summary

**Current State:**
- ✅ **Pattern-Driven Architecture** - 13 patterns orchestrate business workflows
- ✅ **Multi-Layer Design** - API → Orchestrator → Runtime → Agents → Services
- ✅ **Context-Driven** - RequestCtx ensures reproducibility
- ✅ **Security** - JWT authentication + RLS enforcement
- ✅ **Observability** - Tracing and metrics (optional)

**Identified Gaps:**
- ⚠️ **API Layer Integration** - Uses `pack_queries` directly instead of `PricingService`
- ⚠️ **Error Handling** - Custom exceptions not fully integrated
- ⚠️ **Consistency** - Some endpoints use old patterns

**Recommendations:**
- 🔧 **Priority 1**: Update API layer to use `PricingService` and catch custom exceptions
- 🔧 **Priority 2**: Standardize error responses across all endpoints
- 🔧 **Priority 3**: Update documentation for custom exceptions

**Overall Assessment:**
The API architecture is **well-designed and robust**, with clear separation of concerns and good error handling. The identified gaps are **minor and easily addressable**, primarily around consistency with recent Phase 2 changes (custom exceptions).

