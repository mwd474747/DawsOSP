# Phase 2: Singleton Removal - Implementation Plan

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Purpose:** Detailed plan for migrating from singleton pattern to dependency injection

---

## Executive Summary

Phase 2 will migrate all singleton patterns to dependency injection using a DI container. This will:
- Fix initialization order issues
- Eliminate circular dependencies
- Improve testability
- Enable proper lifecycle management

**Migration Strategy:**
1. Create DI container
2. Register services in dependency order
3. Migrate agents to use DI
4. Remove singleton patterns
5. Update initialization code

---

## Implementation Steps

### Step 1: Create DI Container ✅
- ✅ Created `backend/app/core/di_container.py`
- ✅ Service registration and resolution
- ✅ Dependency order management
- ✅ Lazy initialization

### Step 2: Register Infrastructure Services
- ⏳ Register `db_pool`
- ⏳ Register `fred_provider`
- ⏳ Register `news_provider`
- ⏳ Register other infrastructure services

### Step 3: Register Core Services (No Dependencies)
- ⏳ Register `fred_transformation_service`
- ⏳ Register `indicator_config_manager`
- ⏳ Register `rights_registry`
- ⏳ Register `alert_delivery_service`
- ⏳ Register `playbooks_service`
- ⏳ Register `auth_service`

### Step 4: Register Core Services (Infrastructure Dependencies)
- ⏳ Register `pricing_service` (depends on `db_pool`)
- ⏳ Register `ratings_service` (depends on `db_pool`)
- ⏳ Register `optimizer_service` (depends on `db_pool`)
- ⏳ Register `notifications_service` (depends on `db_pool`)
- ⏳ Register `audit_service` (depends on `db_pool`)

### Step 5: Register Core Services (Service Dependencies)
- ⏳ Register `macro_service` (depends on `fred_provider`, `fred_transformation_service`, `db_pool`)
- ⏳ Register `scenarios_service` (depends on `db_pool`, `pricing_service`)
- ⏳ Register `metrics_service` (depends on `pricing_service`)
- ⏳ Register `currency_attribution_service` (depends on `pricing_service`)
- ⏳ Register `risk_metrics_service` (depends on `pricing_service`)
- ⏳ Register `factor_analysis_service` (depends on `pricing_service`)
- ⏳ Register `benchmarks_service` (depends on `pricing_service`)
- ⏳ Register `alerts_service` (depends on `db_pool`, `notifications_service`, `alert_delivery_service`)
- ⏳ Register `cycles_service` (depends on `indicator_config_manager`)
- ⏳ Register `reports_service` (depends on `rights_registry`)

### Step 6: Register Composite Services
- ⏳ Register `macro_aware_scenarios_service` (depends on `scenarios_service`, `macro_service`, `db_pool`)

### Step 7: Register Agents
- ⏳ Register `macro_hound_agent` (depends on multiple services)
- ⏳ Register `financial_analyst_agent` (depends on multiple services)
- ⏳ Register `data_harvester_agent` (depends on minimal services)
- ⏳ Register `claude_agent` (depends on minimal services)

### Step 8: Register Runtime
- ⏳ Register `agent_runtime` (depends on all agents)
- ⏳ Register `pattern_orchestrator` (depends on `agent_runtime`)

### Step 9: Update Initialization Code
- ⏳ Update `combined_server.py` to use DI container
- ⏳ Update `backend/app/api/executor.py` to use DI container
- ⏳ Remove singleton factory functions

### Step 10: Remove Singleton Patterns
- ⏳ Remove singleton variables (`_*_service = None`)
- ⏳ Remove factory functions (`get_*_service()`)
- ⏳ Update all call sites to use DI

---

## Migration Order

### Phase 2.1: Infrastructure (Step 1-2)
1. Create DI container ✅
2. Register infrastructure services

### Phase 2.2: Core Services (Step 3-5)
3. Register core services (no dependencies)
4. Register core services (infrastructure dependencies)
5. Register core services (service dependencies)

### Phase 2.3: Composite Services (Step 6)
6. Register composite services

### Phase 2.4: Agents (Step 7)
7. Register agents

### Phase 2.5: Runtime (Step 8)
8. Register runtime

### Phase 2.6: Integration (Step 9-10)
9. Update initialization code
10. Remove singleton patterns

---

## Service Registration Examples

### Infrastructure Service
```python
container.register("db_pool", db_pool)
```

### Core Service (No Dependencies)
```python
container.register_service(
    "fred_transformation",
    FREDTransformationService,
)
```

### Core Service (Infrastructure Dependency)
```python
container.register_service(
    "pricing",
    PricingService,
    db_pool="db_pool",
)
```

### Core Service (Service Dependency)
```python
container.register_service(
    "scenarios",
    ScenarioService,
    db_pool="db_pool",
    pricing_service="pricing",
)
```

### Agent (Multiple Dependencies)
```python
container.register_service(
    "macro_hound",
    MacroHound,
    macro_service="macro",
    scenarios_service="scenarios",
    macro_aware_service="macro_aware_scenarios",
    alerts_service="alerts",
    cycles_service="cycles",
    playbooks_service="playbooks",
)
```

---

## Testing Strategy

### Unit Tests
- Test DI container registration and resolution
- Test dependency resolution
- Test service lifecycle

### Integration Tests
- Test service initialization order
- Test agent registration
- Test pattern execution

### Migration Tests
- Test backward compatibility during migration
- Test service replacement
- Test singleton removal

---

## Rollback Plan

If issues arise during migration:
1. Keep singleton patterns as fallback
2. Use feature flag to switch between DI and singleton
3. Gradually migrate services one at a time
4. Test after each migration

---

## Next Steps

1. **Create Service Initialization Module:**
   - Create `backend/app/core/service_initializer.py`
   - Implement service registration in dependency order
   - Implement initialization sequence

2. **Update Combined Server:**
   - Replace singleton initialization with DI container
   - Register all services in dependency order
   - Update agent registration

3. **Migrate Services:**
   - Start with leaf services (no dependencies)
   - Work up dependency tree
   - Test after each migration

---

**Status:** 🚧 IN PROGRESS  
**Last Updated:** January 15, 2025  
**Next Step:** Create service initializer and begin migration

