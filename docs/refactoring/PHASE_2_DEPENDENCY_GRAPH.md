# Phase 2: Dependency Graph Analysis

**Date:** January 15, 2025  
**Status:** ✅ COMPLETE  
**Purpose:** Map all dependencies and identify circular dependencies

---

## Executive Summary

**Key Findings:**
- ✅ **No Direct Circular Dependencies:** Services don't import agents, agents import services
- ⚠️ **Indirect Circular Dependencies:** Through singleton pattern (services → agents → services)
- ✅ **Clear Dependency Hierarchy:** Database → Services → Agents → Runtime
- ⚠️ **Singleton Pattern Issues:** Services call `get_*_service()` creating implicit dependencies

---

## Dependency Graph

### Layer 0: Infrastructure (No Dependencies)

```
db_pool (connection.py)
fred_provider (integrations)
news_provider (integrations)
```

### Layer 1: Core Services (Depend on Infrastructure)

```
pricing_service
  └── db_pool

ratings_service
  └── db_pool

scenarios_service
  └── db_pool
  └── pricing_service (via get_pricing_service())

macro_service
  └── fred_provider
  └── db_pool
  └── fred_transformation_service

fred_transformation_service
  └── (no dependencies)

indicator_config_manager
  └── (no dependencies)

cycles_service
  └── indicator_config_manager

optimizer_service
  └── db_pool

metrics_service
  └── pricing_service (via get_pricing_service())
  └── portfolio_helpers

currency_attribution_service
  └── pricing_service (via get_pricing_service())
  └── portfolio_helpers

risk_metrics_service
  └── pricing_service (via get_pricing_service())

factor_analysis_service
  └── pricing_service (via get_pricing_service())

benchmarks_service
  └── pricing_service

alerts_service
  └── db_pool
  └── notifications_service
  └── alert_delivery_service

notifications_service
  └── db_pool

alert_delivery_service
  └── (no dependencies)

reports_service
  └── rights_registry

rights_registry
  └── (no dependencies)

audit_service
  └── db_pool

auth_service
  └── (no dependencies)

playbooks_service
  └── (no dependencies)
```

### Layer 2: Composite Services (Depend on Core Services)

```
macro_aware_scenarios_service
  └── scenarios_service
  └── macro_service
  └── db_pool
```

### Layer 3: Agents (Depend on Services)

```
macro_hound_agent
  └── macro_service
  └── scenarios_service
  └── macro_aware_scenarios_service
  └── alerts_service
  └── cycles_service
  └── playbooks_service

financial_analyst_agent
  └── pricing_service
  └── optimizer_service
  └── ratings_service
  └── currency_attribution_service
  └── fundamentals_transformer

data_harvester_agent
  └── fundamentals_transformer
  └── (minimal dependencies)

claude_agent
  └── (minimal dependencies)
```

### Layer 4: Runtime (Depends on Agents)

```
agent_runtime
  └── agents (macro_hound, financial_analyst, data_harvester, claude)

pattern_orchestrator
  └── agent_runtime
```

---

## Circular Dependencies Analysis

### ✅ No Direct Circular Dependencies

**Analysis:**
- Services don't import agents
- Agents import services
- Clear unidirectional dependency flow

### ⚠️ Indirect Circular Dependencies (Through Singletons)

**Problem:**
Services call `get_*_service()` which creates implicit dependencies:

```python
# In scenarios_service.py
pricing_service = get_pricing_service()  # Implicit dependency

# In macro_aware_scenarios_service.py
scenario_service = get_scenario_service()  # Implicit dependency
macro_service = get_macro_service()  # Implicit dependency
```

**Impact:**
- Initialization order becomes critical
- Race conditions possible
- Testing becomes difficult

**Solution:**
- Replace `get_*_service()` calls with dependency injection
- Pass dependencies explicitly in constructors
- Remove singleton pattern

---

## Singleton Pattern Issues

### 1. Implicit Dependencies

**Problem:**
```python
# In metrics_service.py
def compute_twr(...):
    pricing_service = get_pricing_service()  # Implicit dependency
    # ...
```

**Solution:**
```python
# In metrics_service.py
class MetricsService:
    def __init__(self, pricing_service: PricingService):
        self.pricing_service = pricing_service
    
    def compute_twr(...):
        # Use self.pricing_service
        # ...
```

### 2. Initialization Order

**Problem:**
Services initialized on first access:
```python
# In pricing.py
_pricing_service = None

def get_pricing_service():
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()  # Created on first access
    return _pricing_service
```

**Solution:**
Explicit initialization in dependency order:
```python
# In combined_server.py
def init_app():
    # Initialize in dependency order
    db_pool = init_db_pool()
    pricing_service = PricingService(db_pool=db_pool)
    metrics_service = MetricsService(pricing_service=pricing_service)
    # ...
```

### 3. Testing Issues

**Problem:**
Cannot mock services easily:
```python
# In test_metrics.py
def test_compute_twr():
    # Cannot mock get_pricing_service() easily
    metrics_service = MetricsService()
    # ...
```

**Solution:**
Dependency injection allows easy mocking:
```python
# In test_metrics.py
def test_compute_twr():
    mock_pricing = Mock(spec=PricingService)
    metrics_service = MetricsService(pricing_service=mock_pricing)
    # ...
```

---

## Migration Strategy

### Phase 2.1: Analyze Dependencies ✅
- ✅ Inventory all singletons
- ✅ Map dependency graph
- ✅ Identify circular dependencies
- ✅ Document initialization order

### Phase 2.2: Fix Circular Dependencies
- ⏳ Replace `get_*_service()` calls with constructor injection
- ⏳ Extract shared dependencies
- ⏳ Refactor to use interfaces

### Phase 2.3: Fix Initialization Order
- ⏳ Create explicit initialization sequence
- ⏳ Ensure dependencies initialized before dependents
- ⏳ Add initialization validation

### Phase 2.4: Migrate to Dependency Injection
- ⏳ Create DI container
- ⏳ Register all services
- ⏳ Replace `get_*_service()` calls with DI
- ⏳ Remove singleton patterns

---

## Dependency Order (Initialization Sequence)

### Step 1: Infrastructure
1. `db_pool` (connection.py)
2. `fred_provider` (integrations)
3. `news_provider` (integrations)

### Step 2: Core Services (No Service Dependencies)
1. `fred_transformation_service`
2. `indicator_config_manager`
3. `rights_registry`
4. `alert_delivery_service`
5. `playbooks_service`
6. `auth_service`

### Step 3: Core Services (Infrastructure Dependencies Only)
1. `pricing_service` (depends on db_pool)
2. `ratings_service` (depends on db_pool)
3. `optimizer_service` (depends on db_pool)
4. `notifications_service` (depends on db_pool)
5. `audit_service` (depends on db_pool)

### Step 4: Core Services (Service Dependencies)
1. `macro_service` (depends on fred_provider, fred_transformation_service, db_pool)
2. `scenarios_service` (depends on db_pool, pricing_service)
3. `metrics_service` (depends on pricing_service)
4. `currency_attribution_service` (depends on pricing_service)
5. `risk_metrics_service` (depends on pricing_service)
6. `factor_analysis_service` (depends on pricing_service)
7. `benchmarks_service` (depends on pricing_service)
8. `alerts_service` (depends on db_pool, notifications_service, alert_delivery_service)
9. `cycles_service` (depends on indicator_config_manager)
10. `reports_service` (depends on rights_registry)

### Step 5: Composite Services
1. `macro_aware_scenarios_service` (depends on scenarios_service, macro_service, db_pool)

### Step 6: Agents
1. `macro_hound_agent` (depends on macro_service, scenarios_service, macro_aware_scenarios_service, alerts_service, cycles_service, playbooks_service)
2. `financial_analyst_agent` (depends on pricing_service, optimizer_service, ratings_service, currency_attribution_service)
3. `data_harvester_agent` (depends on fundamentals_transformer)
4. `claude_agent` (minimal dependencies)

### Step 7: Runtime
1. `agent_runtime` (depends on all agents)
2. `pattern_orchestrator` (depends on agent_runtime)

---

## Next Steps

1. **Create DI Container:**
   - Design container interface
   - Implement service registration
   - Implement dependency resolution

2. **Migrate Services:**
   - Start with leaf services (no dependencies)
   - Work up dependency tree
   - Test after each migration

3. **Remove Singleton Patterns:**
   - Replace `get_*_service()` calls with DI
   - Remove singleton variables
   - Remove factory functions

---

**Status:** ✅ COMPLETE  
**Last Updated:** January 15, 2025  
**Next Step:** Create DI container and begin migration

