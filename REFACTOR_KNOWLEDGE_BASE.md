# Refactor Knowledge Base - Complete Context

**Date**: 2025-01-15  
**Status**: 📚 **KNOWLEDGE BASE READY**  
**Purpose**: Comprehensive knowledge base for refactoring work, referencing all relevant documentation, past errors, regressions, and guardrails  
**Last Updated**: 2025-01-15

---

## Executive Summary

This knowledge base consolidates:
- **Architecture Patterns** from ARCHITECTURE.md and DATABASE.md
- **Past Errors & Regressions** from REPLIT_CHANGES_ANALYSIS.md, ANTI_PATTERN_ANALYSIS.md, ROOT_CAUSE_ANALYSIS.md
- **Critical Guardrails** learned from past refactors
- **Database Schema** from actual schema files
- **Field Name Patterns** from DATABASE.md
- **Anti-Patterns** to avoid
- **Patterns to Maintain** from successful refactors

**Purpose**: Provide complete context for safe, effective refactoring that doesn't regress to past mistakes.

---

## Architecture Context

### Pattern-Driven Agent Orchestration

**Reference**: `ARCHITECTURE.md` (Lines 1-150)

**Key Concepts**:
- **Patterns**: Declarative JSON files defining multi-step workflows (15 patterns)
- **Capabilities**: Agent methods exposed as "category.operation" strings (72 capabilities)
  - **Naming Convention**: Category-based naming (e.g., `ratings.*`, `optimizer.*`, `charts.*`)
  - **NOT** agent-prefixed naming (e.g., `financial_analyst.*`) - migrated January 15, 2025
- **Template Substitution**: Dynamic values using `{{inputs.x}}`, `{{step_result}}`, `{{ctx.z}}`
- **Request Context (RequestCtx)**: Immutable context ensuring reproducibility

**Pattern Output Format**:
- **Format 1 (Standard)**: `["output1", "output2", ...]` - List of keys
- **Format 2 (Legacy)**: `{"output1": {...}, "output2": {...}}` - Dict (deprecated)
- **Format 3 (Legacy)**: `{"panels": [...]}` - Panels (deprecated)
- **Current State**: All 15 patterns use Format 1

**Template Reference Style**:
- Patterns use direct references: `{{valued_positions.positions}}`
- NOT nested namespace: `{{state.foo}}` (deprecated)

---

## Database Schema Context

### Critical Field Names (VERIFIED)

**Reference**: `DATABASE.md` (Lines 180-230), `backend/db/schema/001_portfolios_lots_transactions.sql`

#### Transactions Table

**Schema File**: `backend/db/schema/001_portfolios_lots_transactions.sql` (Lines 104-147)

**Correct Field Names**:
```sql
CREATE TABLE transactions (
    -- ...
    transaction_type TEXT NOT NULL CHECK (
        transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'TRANSFER_IN', 'TRANSFER_OUT', 'FEE')
    ),
    -- ...
    transaction_date DATE NOT NULL,  -- ✅ CORRECT (NOT trade_date)
    -- ...
);
```

**Migration 017**: `backend/db/migrations/017_add_realized_pl_field.sql` (Line 14)
```sql
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS realized_pl NUMERIC(20, 2) DEFAULT NULL;  -- ✅ CORRECT (NOT realized_pnl)
```

**Field Name Mappings** (Code → Database):
- ❌ `trade_date` → ✅ `transaction_date`
- ❌ `action` → ✅ `transaction_type`
- ❌ `realized_pnl` → ✅ `realized_pl`

#### Portfolio Cash Flows Table

**Schema File**: `backend/db/schema/portfolio_cash_flows.sql` (Line 9)

**Correct Field Name**:
```sql
CREATE TABLE portfolio_cash_flows (
    -- ...
    flow_date DATE NOT NULL,  -- ✅ CORRECT (NOT trade_date)
    -- ...
);
```

**Field Name Mapping** (Code → Database):
- ❌ `trade_date` → ✅ `flow_date`

#### Fundamentals Data Structure

**Reference**: `backend/app/services/fundamentals_transformer.py:158`, `backend/app/agents/data_harvester.py:1184`

**Correct Field Name**:
- ✅ `debt_equity_ratio` (NOT `debt_to_equity`)

**Field Name Mapping** (Code → Data Structure):
- ❌ `debt_to_equity` → ✅ `debt_equity_ratio`

---

## Past Errors & Regressions

### Error #1: Singleton Factory Function Reintroduction

**Reference**: `ANTI_PATTERN_ANALYSIS.md`, `REPLIT_CHANGES_ANALYSIS.md`

**What Happened**:
- Replit reintroduced `get_scenario_service()` factory function
- This contradicted Phase 2 refactoring (singleton removal)
- Caused import failure cascade: `RequestCtx = None` → runtime error

**Root Cause**:
- Import failure: `from app.services.scenarios import get_scenario_service` failed
- Cascade effect: Entire import block failed
- Fallback: `RequestCtx = None` was set
- Runtime error: `RequestCtx()` called on `None` object

**Lesson Learned**:
- ❌ **NEVER** reintroduce singleton factory functions
- ✅ **ALWAYS** use DI container or direct instantiation
- ✅ **ALWAYS** use granular import error handling

**Prevention**:
- Architecture validator checks for singleton factory functions
- CI/CD runs architecture validation on every commit
- Documentation clearly states singleton pattern is removed

---

### Error #2: Broad Import Error Handling

**Reference**: `REPLIT_CHANGES_ANALYSIS.md` (Lines 38-60)

**What Happened**:
- All imports caught in one try/except block
- Critical imports (RequestCtx) set to None
- No distinction between critical and optional imports
- Can't identify which specific import failed

**Root Cause**:
```python
# ❌ WRONG - Too broad
try:
    from app.core.types import RequestCtx
    from app.services.scenarios import get_scenario_service
    # ... all imports
except ImportError as e:
    RequestCtx = None  # ❌ Causes runtime errors!
    get_scenario_service = None
```

**Lesson Learned**:
- ❌ **NEVER** catch all imports in one try/except block
- ✅ **ALWAYS** use granular import error handling
- ✅ **ALWAYS** distinguish critical vs optional imports
- ✅ **ALWAYS** fail fast for critical imports (RequestCtx, etc.)

**Prevention**:
- Granular try/except blocks for each import
- Critical imports fail fast (raise RuntimeError)
- Optional imports degrade gracefully with warnings

---

### Error #3: Field Name Mismatches

**Reference**: `CONSOLE_LOG_ISSUES_ANALYSIS.md` (Issues 1, 4), `DATABASE.md` (Lines 180-230)

**What Happened**:
- Code uses `trade_date` but database has `transaction_date`
- Code uses `action` but database has `transaction_type`
- Code uses `realized_pnl` but database has `realized_pl`
- Code uses `debt_to_equity` but data structure has `debt_equity_ratio`

**Root Cause**:
- Code not updated to match database schema
- Field names assumed without verification
- No validation against actual schema files

**Lesson Learned**:
- ❌ **NEVER** assume field names - always verify against schema
- ✅ **ALWAYS** check actual schema files before using field names
- ✅ **ALWAYS** use database field names, not code field names
- ✅ **ALWAYS** verify field names against actual schema files

**Prevention**:
- Always read schema files before using field names
- Use schema files as source of truth
- Validate field names against actual database schema

---

### Error #4: Missing Function Imports

**Reference**: `CONSOLE_LOG_ISSUES_ANALYSIS.md` (Issue 13)

**What Happened**:
- `formatDate` defined in `frontend/utils.js` as `Utils.formatDate`
- Used directly as `formatDate` without prefix in `frontend/pages.js`
- Caused `ReferenceError: formatDate is not defined`

**Root Cause**:
- Function not imported after module extraction
- Module extraction didn't preserve imports

**Lesson Learned**:
- ✅ **ALWAYS** verify all function imports after module extraction
- ✅ **ALWAYS** check for missing imports after refactoring
- ✅ **ALWAYS** test page rendering after module changes

**Prevention**:
- Verify all function imports after module extraction
- Test page rendering after refactoring
- Check for missing imports in frontend code

---

### Error #5: Pattern Dependency Issues

**Reference**: `CONSOLE_LOG_ISSUES_ANALYSIS.md` (Issue 3)

**What Happened**:
- Pattern step result structure doesn't match expectations
- Error message uses old agent-prefixed naming
- Step dependency validation fails

**Root Cause**:
- Error message not updated after capability naming migration
- Step result structure mismatch between pattern and code

**Lesson Learned**:
- ✅ **ALWAYS** update error messages during refactoring
- ✅ **ALWAYS** verify step result structures match pattern expectations
- ✅ **ALWAYS** use category-based naming consistently

**Prevention**:
- Update all error messages during refactoring
- Verify step result structures match pattern expectations
- Use category-based naming consistently

---

## Critical Guardrails (Lessons Learned)

### ❌ Patterns We CANNOT Regress To

#### 1. Singleton Factory Functions

**Why**: Replit reintroduced this anti-pattern, causing import failures

**Pattern**:
```python
# ❌ WRONG - Never do this
def get_scenario_service():
    """Factory function to return ScenarioService instance."""
    return ScenarioService()
```

**Correct Pattern**:
```python
# ✅ CORRECT - Use DI container
from app.core.di_container import get_container
container = get_container()
service = container.resolve("scenarios")

# ✅ OR - Use direct instantiation
from app.services.scenarios import ScenarioService
service = ScenarioService(db_pool=db_pool)
```

**Prevention**:
- Architecture validator checks for singleton factory functions
- CI/CD runs architecture validation on every commit
- Documentation clearly states singleton pattern is removed

---

#### 2. Database Field Name Mismatches

**Why**: Code using wrong field names causes 500 errors

**Pattern**:
```python
# ❌ WRONG - Assumes field name
SELECT trade_date, action, realized_pnl
FROM transactions
```

**Correct Pattern**:
```python
# ✅ CORRECT - Verify against schema
# Schema file: backend/db/schema/001_portfolios_lots_transactions.sql
# Verified: transaction_date, transaction_type, realized_pl
SELECT transaction_date, transaction_type, realized_pl
FROM transactions
```

**Prevention**:
- Always read schema files before using field names
- Use schema files as source of truth
- Validate field names against actual database schema

---

#### 3. Broad Import Error Handling

**Why**: Broad error handling masks specific failures

**Pattern**:
```python
# ❌ WRONG - Too broad
try:
    from app.core.types import RequestCtx
    from app.services.scenarios import get_scenario_service
    # ... all imports
except ImportError as e:
    RequestCtx = None  # ❌ Causes runtime errors!
```

**Correct Pattern**:
```python
# ✅ CORRECT - Granular error handling
# Critical imports - fail fast
try:
    from app.core.types import RequestCtx
    REQUEST_CTX_AVAILABLE = True
except ImportError as e:
    logger.error(f"CRITICAL: RequestCtx not available: {e}")
    raise RuntimeError(f"Cannot start server: {e}") from e

# Optional imports - degrade gracefully
try:
    from app.services.scenarios import ScenarioService
    SCENARIO_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ScenarioService not available: {e}")
    ScenarioService = None
    SCENARIO_SERVICE_AVAILABLE = False
```

**Prevention**:
- Granular try/except blocks for each import
- Critical imports fail fast (raise RuntimeError)
- Optional imports degrade gracefully with warnings

---

#### 4. None Value Validation

**Why**: None values cause cryptic runtime errors

**Pattern**:
```python
# ❌ WRONG - No validation
def __init__(self, agent_runtime, db, redis=None):
    self.agent_runtime = agent_runtime  # Could be None!
    self.db = db  # Could be None!
```

**Correct Pattern**:
```python
# ✅ CORRECT - Validate None values
def __init__(self, agent_runtime, db, redis=None):
    if agent_runtime is None:
        raise ValueError("agent_runtime cannot be None - required for pattern execution")
    if db is None:
        raise ValueError("db cannot be None - required for database operations")
    self.agent_runtime = agent_runtime
    self.db = db
```

**Prevention**:
- Always validate None values in constructors
- Fail fast with clear error messages
- Add None validation to critical constructors

---

### ✅ Patterns We MUST Maintain

#### 1. DI Container Architecture

**Reference**: `ARCHITECTURE.md` (Lines 106-148)

**Pattern**:
```python
# ✅ CORRECT - Use DI container
from app.core.service_initializer import initialize_services
from app.core.di_container import get_container
from app.db.connection import get_db_pool

# Get DI container
container = get_container()

# Get database pool
db_pool = get_db_pool()

# Initialize all services in dependency order
initialize_services(container, db_pool=db_pool)

# Services are now available via container.resolve()
pricing_service = container.resolve("pricing")
ratings_service = container.resolve("ratings")
```

**Why**: 
- Centralized service management
- Dependency injection for testability
- Consistent initialization order

---

#### 2. Database Connection Patterns

**Reference**: `DATABASE.md` (Lines 35-56), `ARCHITECTURE.md`

**Pattern for User-Scoped Data**:
```python
# ✅ CORRECT - Use RLS connection for user-scoped data
from app.db.connection import get_db_connection_with_rls

async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    transactions = await conn.fetch(
        """
        SELECT transaction_date, transaction_type, realized_pl
        FROM transactions
        WHERE portfolio_id = $1 AND security_id = $2
        ORDER BY transaction_date DESC
        LIMIT $3
        """,
        portfolio_uuid,
        security_uuid,
        limit,
    )
```

**Pattern for Service Constructors**:
```python
# ✅ CORRECT - Accept db_pool parameter
class MetricsService:
    def __init__(self, db_pool=None):
        self.db_pool = db_pool or get_db_pool()
```

**Why**:
- Row-level security (RLS) for multi-tenant data isolation
- Consistent connection pool management
- Proper user context for data access

---

#### 3. Error Handling Patterns

**Reference**: `REPLIT_CHANGES_ANALYSIS.md` (Lines 273-303)

**Pattern**:
```python
# ✅ CORRECT - Granular error handling
# Critical imports - fail fast
try:
    from app.core.types import RequestCtx
    REQUEST_CTX_AVAILABLE = True
except ImportError as e:
    logger.error(f"CRITICAL: RequestCtx not available: {e}")
    raise RuntimeError(f"Cannot start server: {e}") from e

# Optional imports - degrade gracefully
try:
    from app.services.scenarios import ScenarioService
    SCENARIO_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ScenarioService not available: {e}")
    ScenarioService = None
    SCENARIO_SERVICE_AVAILABLE = False

# Usage checks
if not REQUEST_CTX_AVAILABLE:
    logger.error("CRITICAL: RequestCtx not available - cannot create request context")
    return {"success": False, "error": "RequestCtx not available"}
```

**Why**:
- Identifies which specific import failed
- Allows graceful degradation for optional imports
- Fails fast for critical imports

---

#### 4. Deployment Guardrails

**Reference**: `docs/reference/REPLIT_DEPLOYMENT_GUARDRAILS.md`

**Pattern**:
- ✅ **NEVER** modify `.replit` file
- ✅ **NEVER** modify `combined_server.py` structure
- ✅ **NEVER** change port 5000
- ✅ **NEVER** modify deployment configuration

**Why**: Deployment will break if these are modified

---

## Field Name Verification Checklist

### Before Using Any Database Field Name:

1. ✅ **Read Schema File**: Check actual schema file for field name
   - `backend/db/schema/001_portfolios_lots_transactions.sql` for transactions table
   - `backend/db/schema/portfolio_cash_flows.sql` for cash flows table
   - `backend/db/migrations/017_add_realized_pl_field.sql` for realized_pl field

2. ✅ **Verify Field Name**: Ensure field name matches schema exactly
   - Case-sensitive: `transaction_date` not `Transaction_Date`
   - Exact spelling: `realized_pl` not `realized_pnl`

3. ✅ **Check Migrations**: Verify field name in migration files
   - Migration 017 adds `realized_pl` (not `realized_pnl`)

4. ✅ **Update All References**: Update all code references to match schema
   - SQL queries
   - Result dictionaries
   - Pattern JSON files (presentation configs)

5. ✅ **Test Thoroughly**: Test all affected patterns after fix
   - Test holdings page deep dive
   - Test transaction history
   - Test MWR calculation
   - Test buffett_checklist pattern

---

## Capability Naming Convention

### Category-Based Naming (Standard)

**Reference**: `ARCHITECTURE.md` (Lines 35-38)

**Pattern**:
- ✅ `ratings.dividend_safety` (NOT `financial_analyst.dividend_safety`)
- ✅ `optimizer.propose_trades` (NOT `financial_analyst.propose_trades`)
- ✅ `charts.macro_overview` (NOT `financial_analyst.macro_overview_charts`)
- ✅ `alerts.suggest_presets` (NOT `macro_hound.suggest_alert_presets`)

**Why**:
- Patterns don't know which agent implements capabilities
- Allows agent implementation to change without pattern changes
- Better abstraction and separation of concerns

**Migration**: All patterns migrated to category-based naming (January 15, 2025)

---

## Pattern Step Result Structure

### Template Reference Style

**Reference**: `ARCHITECTURE.md` (Line 74)

**Pattern**:
```json
{
  "steps": [
    {
      "capability": "portfolio.get_valued_positions",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}"},
      "as": "valued_positions"
    },
    {
      "capability": "ratings.aggregate",
      "args": {"positions": "{{valued_positions.positions}}"},
      "as": "ratings"
    }
  ]
}
```

**Key Points**:
- Step result referenced via `"as"` key: `{{valued_positions}}`
- Nested properties accessed directly: `{{valued_positions.positions}}`
- NOT nested namespace: `{{state.foo}}` (deprecated)

---

## Frontend Module System

### Module Loading Order

**Reference**: `full_ui.html` (Lines 20-50)

**Correct Order**:
1. Version Management (`version.js`)
2. Logger Module (`logger.js`)
3. Module Dependency Validation (`module-dependencies.js`)
4. API Client Module (`api-client.js`)
5. Form Validator Module (`form-validator.js`)
6. Error Handler Module (`error-handler.js`)
7. Utility Functions Module (`utils.js`)
8. Panel Components Module (`panels.js`)
9. Context System Module (`context.js`) - **MUST load before pattern-system and pages**
10. Pattern System Module (`pattern-system.js`)
11. Page Components Module (`pages.js`)
12. Namespace Validation (`namespace-validator.js`)

**Why**: 
- Context must load before pattern-system and pages (they depend on it)
- Panels must load before pattern-system (it uses panel components)
- Utils must load before pages (pages use format functions)

---

## Frontend Function Imports

### Format Functions

**Reference**: `frontend/utils.js` (Lines 71-86)

**Pattern**:
```javascript
// ✅ CORRECT - Import from Utils namespace
const formatDate = Utils.formatDate || ((dateString) => dateString || '-');
const formatCurrency = Utils.formatCurrency || ((value) => value || '0');
const formatPercentage = Utils.formatPercentage || ((value) => value || '0%');
```

**Usage**:
```javascript
// ✅ CORRECT - Use imported function
e('td', null, formatDate(tx.date))

// ❌ WRONG - Direct use without import
e('td', null, formatDate(tx.date))  // ReferenceError: formatDate is not defined
```

**Why**: 
- Functions defined in `Utils` namespace after module extraction
- Must import or alias before use
- Prevents `ReferenceError: formatDate is not defined`

---

## Database Field Name Reference

### Complete Field Name Mappings

#### Transactions Table

| Code Uses (WRONG) | Database Schema (CORRECT) | Location |
|-------------------|---------------------------|----------|
| `trade_date` | `transaction_date` | `financial_analyst.py:2289` |
| `action` | `transaction_type` | `financial_analyst.py:2290` |
| `realized_pnl` | `realized_pl` | `financial_analyst.py:2295` |

**Schema File**: `backend/db/schema/001_portfolios_lots_transactions.sql` (Lines 110, 119)
**Migration File**: `backend/db/migrations/017_add_realized_pl_field.sql` (Line 14)

#### Portfolio Cash Flows Table

| Code Uses (WRONG) | Database Schema (CORRECT) | Location |
|-------------------|---------------------------|----------|
| `trade_date` | `flow_date` | `metrics.py:274` |

**Schema File**: `backend/db/schema/portfolio_cash_flows.sql` (Line 9)

#### Fundamentals Data Structure

| Code Uses (WRONG) | Data Structure (CORRECT) | Location |
|-------------------|---------------------------|----------|
| `debt_to_equity` | `debt_equity_ratio` | `ratings.py:493` |

**Data Source**: `fundamentals_transformer.py:158`, `data_harvester.py:1184`

---

## Pattern Execution Context

### Request Context (RequestCtx)

**Reference**: `ARCHITECTURE.md` (Line 40)

**Purpose**: Immutable context ensuring reproducibility

**Fields**:
- `trace_id`: Unique trace ID for request
- `request_id`: Unique request ID
- `user_id`: User ID for RLS
- `portfolio_id`: Portfolio ID (optional)
- `asof_date`: Analysis date
- `pricing_pack_id`: Immutable pricing pack ID
- `ledger_commit_hash`: Immutable ledger commit hash

**Usage**:
```python
ctx = RequestCtx(
    trace_id=str(uuid4()),
    request_id=str(uuid4()),
    user_id=user_id or SYSTEM_USER_ID,
    portfolio_id=inputs.get("portfolio_id"),
    asof_date=date.today(),
    pricing_pack_id=pricing_pack_id,
    ledger_commit_hash=ledger_commit_hash
)
```

**Why**: Ensures reproducible analysis with immutable pricing packs and ledger commits

---

## Anti-Patterns to Avoid

### 1. Singleton Factory Functions

**Pattern**:
```python
# ❌ WRONG - Never do this
def get_scenario_service():
    """Factory function to return ScenarioService instance."""
    return ScenarioService()
```

**Why**: Contradicts DI container architecture, causes import failures

---

### 2. Database Field Name Assumptions

**Pattern**:
```python
# ❌ WRONG - Assumes field name
SELECT trade_date, action, realized_pnl
FROM transactions
```

**Why**: Code must match schema, not vice versa

---

### 3. Broad Import Error Handling

**Pattern**:
```python
# ❌ WRONG - Too broad
try:
    from app.core.types import RequestCtx
    from app.services.scenarios import get_scenario_service
    # ... all imports
except ImportError as e:
    RequestCtx = None  # ❌ Causes runtime errors!
```

**Why**: Masks specific failures, causes runtime errors

---

### 4. Missing None Value Validation

**Pattern**:
```python
# ❌ WRONG - No validation
def __init__(self, agent_runtime, db, redis=None):
    self.agent_runtime = agent_runtime  # Could be None!
```

**Why**: Causes cryptic runtime errors

---

## Patterns to Maintain

### 1. DI Container Architecture

**Pattern**:
```python
# ✅ CORRECT - Use DI container
container = get_container()
service = container.resolve("service_name")
```

**Why**: Centralized service management, dependency injection for testability

---

### 2. Database Connection Patterns

**Pattern**:
```python
# ✅ CORRECT - Use RLS connection for user-scoped data
async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    # ... query user-scoped data
```

**Why**: Row-level security for multi-tenant data isolation

---

### 3. Granular Import Error Handling

**Pattern**:
```python
# ✅ CORRECT - Granular error handling
try:
    from app.core.types import RequestCtx
    REQUEST_CTX_AVAILABLE = True
except ImportError as e:
    raise RuntimeError(f"Cannot start server: {e}") from e
```

**Why**: Identifies specific failures, fails fast for critical imports

---

### 4. None Value Validation

**Pattern**:
```python
# ✅ CORRECT - Validate None values
def __init__(self, agent_runtime, db, redis=None):
    if agent_runtime is None:
        raise ValueError("agent_runtime cannot be None")
    self.agent_runtime = agent_runtime
```

**Why**: Fails fast with clear error messages

---

## Related Documents

- **Architecture**: `ARCHITECTURE.md`
- **Database**: `DATABASE.md`
- **Anti-Patterns**: `ANTI_PATTERN_ANALYSIS.md`
- **Replit Changes**: `REPLIT_CHANGES_ANALYSIS.md`
- **Root Cause Analysis**: `ROOT_CAUSE_ANALYSIS.md`
- **Console Log Issues**: `CONSOLE_LOG_ISSUES_ANALYSIS.md`
- **Unified Refactor Plan**: `UNIFIED_REFACTOR_PLAN.md`

---

**Status**: 📚 **KNOWLEDGE BASE READY**  
**Last Updated**: 2025-01-15

