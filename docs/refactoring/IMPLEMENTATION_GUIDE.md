# Technical Debt Removal - Implementation Guide

**Date:** January 15, 2025  
**Purpose:** Step-by-step implementation guide for technical debt removal

---

## Prerequisites

### Knowledge Sources
1. **ARCHITECTURE.md** - System architecture overview
2. **PATTERN_SYSTEM_DEEP_DIVE.md** - Pattern system understanding
3. **NAMESPACE_ARCHITECTURE.md** - Namespace structure
4. **CURRENT_STATE_ASSESSMENT.md** - Current state inventory
5. **UI_REFACTORING_COMPLETE.md** - Recent UI refactoring work
6. **PHASE_1_STUB_REMOVAL_COMPLETE.md** - Stub removal work
7. **PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md** - Service stub review

### Tools Required
- Python 3.11+
- Node.js (for frontend work)
- Git (for version control)
- Code editor with Python/JavaScript support

---

## Phase 1: Exception Handling Standardization

### Step 1.1: Create Exception Hierarchy

**File:** `backend/app/core/exceptions.py` (NEW)

```python
"""
DawsOS Exception Hierarchy

Purpose: Standardized exceptions for better error handling
Created: 2025-01-15
"""


class DawsOSError(Exception):
    """Base exception for all DawsOS errors."""
    pass


class DatabaseError(DawsOSError):
    """Database operation failed."""
    pass


class ValidationError(DawsOSError):
    """Input validation failed."""
    pass


class ServiceError(DawsOSError):
    """Service operation failed."""
    pass


class ConfigurationError(DawsOSError):
    """Configuration error."""
    pass


class ExternalAPIError(DawsOSError):
    """External API call failed."""
    pass


class CapabilityError(DawsOSError):
    """Capability execution failed."""
    pass


class PatternError(DawsOSError):
    """Pattern execution failed."""
    pass
```

### Step 1.2: Replace Broad Exception Handlers

**Pattern:**
```python
# BEFORE:
try:
    result = await some_operation()
except Exception as e:
    logger.warning(f"Operation failed: {e}")
    return default_value

# AFTER:
try:
    result = await some_operation()
except DatabaseError as e:
    logger.error(f"Database operation failed: {e}", exc_info=True)
    raise
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    return {"error": str(e)}
except ExternalAPIError as e:
    logger.error(f"External API failed: {e}", exc_info=True)
    raise ServiceError(f"Service unavailable: {e}") from e
except Exception as e:
    # Only for truly unexpected errors
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise DawsOSError(f"Unexpected error in {operation_name}") from e
```

**Files to Update:**
1. `backend/app/services/alerts.py` (19 instances)
2. `backend/app/services/scenarios.py` (2 instances)
3. `backend/app/services/reports.py` (4 instances)
4. `backend/app/services/ratings.py` (1 instance)
5. `backend/app/services/pricing.py` (6 instances)
6. `backend/app/services/optimizer.py` (5 instances)
7. Others (16 files, ~88 instances)

**Testing:**
- Test each service independently
- Verify error propagation
- Check error messages are clear

---

## Phase 2: Remove Global Singletons

### Step 2.1: Identify All Singleton Functions

**Command:**
```bash
grep -r "def get_.*_service" backend/app/services/
```

**Expected Results:**
- `get_optimizer_service()` - `optimizer.py:1706`
- `get_ratings_service()` - `ratings.py:688`
- `get_pricing_service()` - `pricing.py:770`
- `get_scenario_service()` - `scenarios.py:957`
- `get_alert_service()` - `alerts.py:1470`
- `get_risk_service()` - `risk.py:627`
- `get_reports_service()` - `reports.py:775`
- Others as found

### Step 2.2: Find All Callers

**Command:**
```bash
grep -r "get_.*_service()" backend/app/
```

**Expected Results:**
- 21+ locations using deprecated functions

### Step 2.3: Replace with Direct Instantiation

**Pattern:**
```python
# BEFORE:
from app.services.pricing import get_pricing_service
pricing_service = get_pricing_service()

# AFTER:
from app.services.pricing import PricingService
pricing_service = PricingService(use_db=True, db_pool=db_pool)
```

**Files to Update:**
1. All service files that call other services
2. All agent files that use services
3. All API routes that use services

### Step 2.4: Remove Singleton Functions

**Pattern:**
```python
# DELETE entire function:
_optimizer_service: Optional[OptimizerService] = None

def get_optimizer_service(use_db: bool = True, db_pool=None) -> OptimizerService:
    """DEPRECATED: Use OptimizerService(db_pool=...) directly instead."""
    # ... entire function ...
```

**Files to Update:**
- All service files with singleton functions

**Testing:**
- Test each service independently
- Verify dependency injection works
- Check no global state remains

---

## Phase 3: Extract Duplicate Code

### Step 3.1: Verify Existing Helpers

**File:** `backend/app/agents/base_agent.py`

**Existing Helpers:**
- `_resolve_portfolio_id()` (lines 277-302) ✅
- `_require_pricing_pack_id()` (lines 304-323) ✅
- `_resolve_pricing_pack_id()` (lines 325-340) ✅
- `_to_uuid()` (lines 256-275) ✅
- `_resolve_asof_date()` (lines 244-254) ✅

### Step 3.2: Replace Duplicate Usage

**Command:**
```bash
grep -r "portfolio_id.*str(ctx.portfolio_id)" backend/app/agents/
grep -r "UUID(portfolio_id)" backend/app/agents/
```

**Pattern:**
```python
# BEFORE:
if not portfolio_id:
    portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
if not portfolio_id:
    raise ValueError("portfolio_id required")
portfolio_uuid = UUID(portfolio_id)

# AFTER:
portfolio_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "capability_name")
```

### Step 3.3: Extract Policy Merging Logic

**File:** `backend/app/services/optimizer.py` (NEW helper)

```python
def _merge_policies(
    policies: Optional[List[Dict[str, Any]]],
    constraints: Optional[Dict[str, Any]]
) -> PolicyConstraints:
    """
    Merge policy list and constraints dict into PolicyConstraints.
    
    Standardizes policy merging logic used in multiple places.
    """
    # Extract from optimizer.py:123-158
    # Use in both OptimizerService and FinancialAnalyst
```

### Step 3.4: Extract Ratings Extraction Pattern

**File:** `backend/app/services/ratings.py` (NEW helper)

```python
def _extract_ratings_from_state(
    state: Dict[str, Any],
    positions: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Extract ratings from state or compute from positions.
    
    Standardizes ratings extraction used in multiple places.
    """
```

---

## Phase 4: Remove Legacy Artifacts

### Step 4.1: Delete Archived Agents

**Command:**
```bash
rm -rf backend/app/agents/.archive/
```

**Files Deleted:**
- `alerts_agent.py` (345 lines)
- `charts_agent.py` (907 lines)
- `optimizer_agent.py` (1,654 lines)
- `ratings_agent.py` (681 lines)
- `reports_agent.py` (772 lines)

**Total:** 4,359 lines removed

### Step 4.2: Remove/Refactor AlertService

**Option A: Delete Entire File** (if migration complete)
```bash
rm backend/app/services/alerts.py  # 1,517 lines
```

**Option B: Minimal Stub** (if still referenced)
- Keep only interface methods that delegate to `MacroHound`
- Remove all implementation
- Add deprecation warnings

### Step 4.3: Remove Example Pattern

**File:** `backend/app/core/pattern_orchestrator.py`

**Delete:**
- Lines 1253-1296 (EXAMPLE_PATTERN definition)

### Step 4.4: Remove Legacy UI Code

**File:** `frontend/pages.js`

**Delete:**
- Lines 1370-1849 (DashboardPageLegacy function)
- Lines 1849-1937 (Legacy ScenariosPage implementation)

### Step 4.5: Remove Compliance Module References

**File:** `backend/app/core/agent_runtime.py`

**Delete:**
- Lines 37-50 (try/except for compliance modules)

---

## Phase 5: Frontend Cleanup

### Step 5.1: Create Frontend Logger

**File:** `frontend/utils.js` (add to existing)

```javascript
const FrontendLogger = {
    debug: (message, ...args) => {
        if (process.env.NODE_ENV === 'development') {
            console.log(`[DEBUG] ${message}`, ...args);
        }
    },
    info: (message, ...args) => {
        if (process.env.NODE_ENV === 'development') {
            console.log(`[INFO] ${message}`, ...args);
        }
    },
    warn: (message, ...args) => {
        console.warn(`[WARN] ${message}`, ...args);
    },
    error: (message, ...args) => {
        console.error(`[ERROR] ${message}`, ...args);
    }
};
```

### Step 5.2: Replace Console.log Statements

**Files to Update:**
- `frontend/utils.js` (2 instances)
- `frontend/pattern-system.js` (4 instances)
- `frontend/pages.js` (19 instances)

**Pattern:**
```javascript
// BEFORE:
console.log('Executing pattern:', pattern);

// AFTER:
FrontendLogger.debug('Executing pattern:', pattern);
```

### Step 5.3: Remove Debug-Only Logs

**Delete:**
```javascript
// DELETE debug-only logs:
console.log('[PortfolioOverview] Data source:', dataSource, data);
console.log('[HoldingsTable] Data source:', dataSource, holdings);
```

---

## Phase 6: Fix TODOs

### Step 6.1: Implement Critical TODOs

**Priority Order:**
1. `financial_analyst.py:1831-1834` - Position return calculation
2. `financial_analyst.py:2376-2380` - Sector-based security lookup
3. `optimizer.py:580, 641` - Expected return calculations
4. `data_harvester.py:1139` - Sector-based switching costs
5. `macro_hound.py:747` - Cycle-adjusted DaR
6. `auth.py:154, 155, 373, 374` - Real IP/user agent

### Step 6.2: Document Future Enhancements

**Create:** `docs/TODOS_FUTURE.md`

**Document:**
- `alerts.py:1305` - Email service integration
- `alerts.py:1327` - SMS service integration
- `alerts.py:1349` - Webhook delivery
- `alerts.py:1398` - Retry scheduling
- `auth.py:383` - Actual creation time
- `full_ui.html:6430` - Trace data source display

---

## Phase 7: Standardize Patterns

### Step 7.1: Create Constants Module

**File:** `backend/app/core/constants.py` (NEW)

```python
"""
DawsOS Constants

Purpose: Centralized constants to replace magic numbers
Created: 2025-01-15
"""

# Time constants (seconds)
ONE_DAY = 86400
ONE_HOUR = 3600
FIVE_MINUTES = 300

# JWT expiration
JWT_EXPIRATION_SECONDS = 86400  # 24 hours

# Cache TTL
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 3600  # 1 hour
CACHE_TTL_LONG = 86400  # 1 day
```

### Step 7.2: Replace Magic Numbers

**Files to Update:**
- `backend/app/api/routes/auth.py` (JWT expiration)
- `backend/app/services/alerts.py` (cooldown calculations)
- Others as found

**Pattern:**
```python
# BEFORE:
expires_in = 86400

# AFTER:
from app.core.constants import JWT_EXPIRATION_SECONDS
expires_in = JWT_EXPIRATION_SECONDS
```

### Step 7.3: Standardize Pattern Output Format

**Target Format:**
```json
{
  "outputs": {
    "panels": [
      {"id": "panel1", "dataPath": "step_result1"},
      {"id": "panel2", "dataPath": "step_result2"}
    ],
    "data": {
      "step_result1": "{{step_result1}}",
      "step_result2": "{{step_result2}}"
    }
  }
}
```

**Files to Update:**
- All 15 pattern JSON files
- `backend/app/core/pattern_orchestrator.py` (output extraction logic)
- `frontend/pattern-system.js` (pattern registry)

---

## Testing Strategy

### Unit Tests
- Test exception handling paths
- Test dependency injection
- Test helper functions
- Test TODO implementations

### Integration Tests
- Test pattern execution with new output format
- Test service interactions without singletons
- Test error propagation

### Regression Tests
- Run existing test suite
- Verify no functionality broken
- Check performance impact

---

## Success Criteria

### Quantitative
- ✅ Zero broad exception handlers (except truly unexpected)
- ✅ Zero deprecated singleton functions
- ✅ Zero duplicate code patterns
- ✅ Zero legacy artifacts
- ✅ Zero console.log in production
- ✅ Zero incomplete TODOs (implemented or documented)
- ✅ 100% pattern format standardization
- ✅ All magic numbers extracted to constants

### Qualitative
- ✅ Cleaner codebase
- ✅ Better error handling
- ✅ Improved maintainability
- ✅ Consistent patterns
- ✅ Better developer experience

---

## Rollback Plan

### If Issues Arise
1. **Git revert** - Revert to previous commit
2. **Incremental rollback** - Revert specific phase
3. **Feature flags** - Use feature flags for gradual rollout

### Backup Strategy
- Create branch before starting: `git checkout -b technical-debt-removal`
- Commit after each phase: `git commit -m "Phase X: Description"`
- Tag stable points: `git tag phase-x-complete`

---

**Status:** Implementation Guide Complete  
**Last Updated:** January 15, 2025

