# Phase 2: Singleton Removal - Completion Plan

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Purpose:** Complete Phase 2 singleton removal and DI integration

---

## Executive Summary

Phase 2 is **~40% complete**. The DI container and service initializer have been created, and `combined_server.py` has been updated. However, `executor.py` still uses singletons, and singleton factory functions have not been removed.

**Key Remaining Work:**
1. Update `executor.py` to use DI container
2. Remove singleton factory functions (~14 functions)
3. Update services to use DI instead of `get_*_service()`
4. Add tests for DI container

---

## Current State Assessment

### ✅ What's Done

1. **DI Container Created** (`backend/app/core/di_container.py`)
   - Service registration and resolution
   - Dependency order management
   - Lazy initialization
   - Singleton, transient, scoped lifetimes

2. **Service Initializer Created** (`backend/app/core/service_initializer.py`)
   - Service registration in dependency order
   - Initialization sequence
   - Dependency resolution

3. **Combined Server Updated** (`combined_server.py`)
   - Uses DI container for `get_agent_runtime()`
   - Uses DI container for `get_pattern_orchestrator()`
   - Removed global singleton variables

### ❌ What's NOT Done

1. **Executor.py NOT Updated**
   - Still uses singleton pattern (`_agent_runtime`, `_pattern_orchestrator`)
   - Still calls `get_agent_runtime()` and `get_pattern_orchestrator()` directly
   - Not using DI container

2. **Singleton Functions NOT Removed**
   - ~14 `get_*_service()` functions still exist
   - Services still call `get_*_service()` internally
   - Agents still create services directly

3. **No Testing**
   - No tests for DI container
   - No tests for service initialization
   - No tests for dependency resolution

---

## Dependency Analysis

### Current Dependency Graph

```
Layer 0: Infrastructure
  - db_pool
  - fred_provider
  - news_provider

Layer 1: Core Services (No Dependencies)
  - fred_transformation_service
  - indicator_config_manager
  - rights_registry
  - alert_delivery_service
  - playbooks_service
  - auth_service

Layer 2: Core Services (Infrastructure Dependencies)
  - pricing_service (depends on db_pool)
  - ratings_service (depends on db_pool)
  - optimizer_service (depends on db_pool)
  - notifications_service (depends on db_pool)
  - audit_service (depends on db_pool)

Layer 3: Core Services (Service Dependencies)
  - macro_service (depends on fred_provider, fred_transformation_service, db_pool)
  - scenarios_service (depends on db_pool, pricing_service)
  - metrics_service (depends on pricing_service)
  - currency_attribution_service (depends on pricing_service)
  - risk_metrics_service (depends on pricing_service)
  - factor_analysis_service (depends on pricing_service)
  - benchmarks_service (depends on pricing_service)
  - alerts_service (depends on db_pool, notifications_service, alert_delivery_service)
  - cycles_service (depends on indicator_config_manager)
  - reports_service (depends on rights_registry)

Layer 4: Composite Services
  - macro_aware_scenarios_service (depends on scenarios_service, macro_service, db_pool)

Layer 5: Agents
  - macro_hound_agent (depends on macro_service, scenarios_service, macro_aware_scenarios_service, alerts_service, cycles_service, playbooks_service)
  - financial_analyst_agent (depends on pricing_service, currency_attribution_service, optimizer_service, ratings_service)
  - data_harvester_agent (depends on pricing_service, news_provider)
  - claude_agent (depends on minimal services)

Layer 6: Runtime
  - agent_runtime (depends on all agents)
  - pattern_orchestrator (depends on agent_runtime)
```

---

## Implementation Plan

### Step 1: Update Executor.py to Use DI Container

**File:** `backend/app/api/executor.py`

**Current State:**
```python
_agent_runtime = None
_pattern_orchestrator = None

def get_agent_runtime(reinit_services: bool = False) -> AgentRuntime:
    global _agent_runtime
    if _agent_runtime is None:
        # Create runtime with singletons
        ...
    return _agent_runtime

def get_pattern_orchestrator() -> PatternOrchestrator:
    global _pattern_orchestrator
    if _pattern_orchestrator is None:
        runtime = get_agent_runtime()
        _pattern_orchestrator = PatternOrchestrator(agent_runtime=runtime)
    return _pattern_orchestrator
```

**Target State:**
```python
from app.core.di_container import DIContainer
from app.core.service_initializer import ServiceInitializer

# Initialize DI container on startup
_container: Optional[DIContainer] = None
_initializer: Optional[ServiceInitializer] = None

def get_di_container() -> DIContainer:
    """Get or initialize DI container."""
    global _container, _initializer
    if _container is None:
        _container = DIContainer()
        _initializer = ServiceInitializer(_container)
        _initializer.initialize_all()
    return _container

def get_agent_runtime(reinit_services: bool = False) -> AgentRuntime:
    """Get agent runtime from DI container."""
    container = get_di_container()
    return container.resolve("agent_runtime")

def get_pattern_orchestrator() -> PatternOrchestrator:
    """Get pattern orchestrator from DI container."""
    container = get_di_container()
    return container.resolve("pattern_orchestrator")
```

**Changes Required:**
1. Import DI container and service initializer
2. Initialize DI container on startup
3. Replace singleton calls with DI container resolution
4. Remove singleton variables

---

### Step 2: Register All Services in Service Initializer

**File:** `backend/app/core/service_initializer.py`

**Current State:**
- Service initializer exists but may not have all services registered

**Target State:**
- All services registered in dependency order
- All agents registered
- Runtime registered

**Services to Register:**
1. Infrastructure (Layer 0)
2. Core Services (Layer 1-3)
3. Composite Services (Layer 4)
4. Agents (Layer 5)
5. Runtime (Layer 6)

---

### Step 3: Remove Singleton Factory Functions

**Files to Update:**
- All service files with `get_*_service()` functions
- All agent files with `get_*_agent()` functions

**Process:**
1. Find all call sites of `get_*_service()` functions
2. Replace with DI container resolution
3. Remove factory functions
4. Remove singleton variables

**Example:**
```python
# BEFORE:
from app.services.pricing import get_pricing_service
pricing_service = get_pricing_service()

# AFTER:
from app.core.di_container import get_di_container
container = get_di_container()
pricing_service = container.resolve("pricing")
```

---

### Step 4: Update Services to Accept Dependencies via Constructor

**Current State:**
- Services create dependencies internally or use `get_*_service()`

**Target State:**
- Services accept dependencies via constructor
- Dependencies injected by DI container

**Example:**
```python
# BEFORE:
class PricingService:
    def __init__(self, use_db: bool = True, db_pool=None):
        if db_pool is None:
            from app.db.connection import get_db_pool
            db_pool = get_db_pool()
        self.db_pool = db_pool

# AFTER:
class PricingService:
    def __init__(self, db_pool):
        self.db_pool = db_pool  # Injected by DI container
```

---

### Step 5: Update Agents to Accept Dependencies via Constructor

**Current State:**
- Agents create services internally or use `get_*_service()`

**Target State:**
- Agents accept services via constructor
- Services injected by DI container

**Example:**
```python
# BEFORE:
class MacroHound(BaseAgent):
    def __init__(self, name: str, services: Dict[str, Any]):
        self.macro_service = MacroService()
        self.scenarios_service = ScenarioService()

# AFTER:
class MacroHound(BaseAgent):
    def __init__(self, name: str, macro_service, scenarios_service, ...):
        self.macro_service = macro_service  # Injected by DI container
        self.scenarios_service = scenarios_service  # Injected by DI container
```

---

### Step 6: Add Tests for DI Container

**Test Files to Create:**
1. `tests/test_di_container.py` - Test container registration and resolution
2. `tests/test_service_initializer.py` - Test service initialization
3. `tests/test_dependency_resolution.py` - Test dependency resolution

**Test Cases:**
1. Service registration
2. Dependency resolution
3. Service initialization order
4. Circular dependency detection
5. Service lifetime management

---

## Migration Strategy

### Phase 2.1: Update Executor.py (Critical)

**Priority:** P0 (Critical)

**Steps:**
1. Import DI container and service initializer
2. Initialize DI container on startup
3. Replace `get_agent_runtime()` to use DI container
4. Replace `get_pattern_orchestrator()` to use DI container
5. Remove singleton variables
6. Test that executor still works

**Estimated Duration:** 2-4 hours

---

### Phase 2.2: Register All Services (Critical)

**Priority:** P0 (Critical)

**Steps:**
1. Review service initializer
2. Register all services in dependency order
3. Register all agents
4. Register runtime
5. Test service initialization

**Estimated Duration:** 2-4 hours

---

### Phase 2.3: Remove Singleton Functions (High Priority)

**Priority:** P1 (High)

**Steps:**
1. Find all call sites of `get_*_service()` functions
2. Replace with DI container resolution
3. Remove factory functions
4. Remove singleton variables
5. Test after each removal

**Estimated Duration:** 4-8 hours

---

### Phase 2.4: Update Services to Use DI (High Priority)

**Priority:** P1 (High)

**Steps:**
1. Update service constructors to accept dependencies
2. Update service initializer to inject dependencies
3. Remove internal `get_*_service()` calls
4. Test after each update

**Estimated Duration:** 4-8 hours

---

### Phase 2.5: Update Agents to Use DI (High Priority)

**Priority:** P1 (High)

**Steps:**
1. Update agent constructors to accept services
2. Update service initializer to inject services
3. Remove internal service creation
4. Test after each update

**Estimated Duration:** 4-8 hours

---

### Phase 2.6: Add Tests (Required)

**Priority:** P0 (Critical - Required by V3 Plan)

**Steps:**
1. Create test files
2. Write unit tests for DI container
3. Write integration tests for service initialization
4. Write tests for dependency resolution
5. Run tests and fix any issues

**Estimated Duration:** 4-8 hours

---

## Risk Assessment

### High Risk Items

1. **Executor.py Update:**
   - **Risk:** Breaking pattern execution
   - **Mitigation:** Test thoroughly, keep singleton as fallback initially
   - **Testing:** Test pattern execution after update

2. **Service Initialization Order:**
   - **Risk:** Circular dependencies or initialization failures
   - **Mitigation:** Validate dependency graph, test initialization
   - **Testing:** Test service initialization in correct order

3. **Singleton Removal:**
   - **Risk:** Breaking existing code that uses singletons
   - **Mitigation:** Update all call sites, test after each removal
   - **Testing:** Test all affected code paths

### Medium Risk Items

1. **Service Constructor Updates:**
   - **Risk:** Breaking service initialization
   - **Mitigation:** Update gradually, test after each update
   - **Testing:** Test service functionality after updates

2. **Agent Constructor Updates:**
   - **Risk:** Breaking agent capabilities
   - **Mitigation:** Update gradually, test after each update
   - **Testing:** Test agent capabilities after updates

---

## Testing Strategy

### Unit Tests

1. **DI Container Tests:**
   - Test service registration
   - Test dependency resolution
   - Test service lifetime management
   - Test circular dependency detection

2. **Service Initializer Tests:**
   - Test service initialization order
   - Test dependency resolution
   - Test initialization failures

### Integration Tests

1. **Service Initialization Tests:**
   - Test all services initialize correctly
   - Test dependency resolution works
   - Test initialization order is correct

2. **Pattern Execution Tests:**
   - Test pattern execution still works
   - Test agent capabilities still work
   - Test service interactions still work

### Regression Tests

1. **Full Test Suite:**
   - Run all existing tests
   - Verify no functionality broken
   - Fix any broken tests

---

## Success Criteria

### Quantitative Metrics

- ✅ Zero singleton factory functions (after removal)
- ✅ Zero singleton variables (after removal)
- ✅ All services registered in DI container
- ✅ All agents registered in DI container
- ✅ Runtime registered in DI container
- ✅ Executor.py uses DI container
- ✅ All tests pass

### Qualitative Metrics

- ✅ Application works without errors
- ✅ Pattern execution works
- ✅ Agent capabilities work
- ✅ Service interactions work
- ✅ Better testability (can mock services)
- ✅ Better maintainability (clear dependencies)

---

## Timeline

**Estimated Duration:** 1-2 days

**Breakdown:**
- Phase 2.1: Update Executor.py (2-4 hours)
- Phase 2.2: Register All Services (2-4 hours)
- Phase 2.3: Remove Singleton Functions (4-8 hours)
- Phase 2.4: Update Services (4-8 hours)
- Phase 2.5: Update Agents (4-8 hours)
- Phase 2.6: Add Tests (4-8 hours)

**Total:** 20-40 hours (2.5-5 days)

---

## Next Steps

### Immediate (This Session)

1. **Update Executor.py:**
   - Import DI container and service initializer
   - Initialize DI container on startup
   - Replace singleton calls with DI container resolution
   - Remove singleton variables
   - Test pattern execution

2. **Register All Services:**
   - Review service initializer
   - Register all services in dependency order
   - Register all agents
   - Register runtime
   - Test service initialization

### Short-term (Next Session)

3. **Remove Singleton Functions:**
   - Find all call sites
   - Replace with DI container resolution
   - Remove factory functions
   - Test after each removal

4. **Add Tests:**
   - Create test files
   - Write unit tests
   - Write integration tests
   - Run tests and fix issues

---

**Status:** 🚧 IN PROGRESS  
**Last Updated:** January 15, 2025  
**Next Step:** Update executor.py to use DI container

