# Phase 2: Singleton Removal - Preparation

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Purpose:** Comprehensive inventory of singleton patterns and dependency analysis

---

## Executive Summary

Phase 2 will remove all singleton patterns and migrate to dependency injection. This document inventories all singleton instances and analyzes their dependencies.

**Key Findings:**
- **Total Singleton Instances:** ~28 across 25 files
- **Singleton Factory Functions:** ~14 `get_*_service()` functions
- **Agent Singletons:** 3 instances (macro_hound, claude_agent, data_harvester)
- **Service Singletons:** ~20 instances
- **Database Query Singletons:** 3 instances
- **Registry Singletons:** 2 instances

---

## Singleton Inventory

### 1. Agent Singletons (3 instances)

#### `backend/app/agents/macro_hound.py`
- **Variable:** `_macro_hound_instance = None`
- **Factory:** `get_macro_hound(services: Optional[Dict[str, Any]] = None) -> MacroHound`
- **Dependencies:** Services dict (macro_service, scenario_service, alert_service)
- **Usage:** Pattern execution, agent runtime

#### `backend/app/agents/claude_agent.py`
- **Variable:** `_claude_agent_instance = None`
- **Factory:** `get_claude_agent(services: Optional[Dict[str, Any]] = None) -> ClaudeAgent`
- **Dependencies:** Services dict (minimal)
- **Usage:** Pattern execution, agent runtime

#### `backend/app/agents/data_harvester.py`
- **Variable:** `_data_harvester_instance = None`
- **Factory:** `get_data_harvester(services: Optional[Dict[str, Any]] = None) -> DataHarvester`
- **Dependencies:** Services dict (pricing_service, news_provider, fred_provider)
- **Usage:** Pattern execution, agent runtime

---

### 2. Service Singletons (~20 instances)

#### Core Services

##### `backend/app/services/pricing.py`
- **Variable:** `_pricing_service: Optional[PricingService] = None`
- **Factory:** `get_pricing_service(use_db: bool = True, db_pool=None) -> PricingService`
- **Dependencies:** `db_pool` (optional)
- **Usage:** Used by agents, other services

##### `backend/app/services/ratings.py`
- **Variable:** `_ratings_service = None`
- **Factory:** `get_ratings_service(use_db: bool = True, db_pool=None) -> RatingsService`
- **Dependencies:** `db_pool` (optional)
- **Usage:** Used by financial_analyst agent

##### `backend/app/services/scenarios.py`
- **Variable:** `_scenario_service: Optional[ScenarioService] = None`
- **Factory:** `get_scenario_service(db_pool=None) -> ScenarioService`
- **Dependencies:** `db_pool` (optional)
- **Usage:** Used by macro_hound agent

##### `backend/app/services/macro.py`
- **Variable:** `_macro_service: Optional[MacroService] = None`
- **Factory:** `get_macro_service(fred_client: Optional[FREDProvider] = None, db_pool=None) -> MacroService`
- **Dependencies:** `fred_client` (optional), `db_pool` (optional)
- **Usage:** Used by macro_hound agent

##### `backend/app/services/macro_aware_scenarios.py`
- **Variable:** `_macro_aware_service = None`
- **Factory:** `get_macro_aware_scenario_service(use_db: bool = True) -> MacroAwareScenarioService`
- **Dependencies:** `use_db` flag
- **Usage:** Used by macro_hound agent

##### `backend/app/services/alerts.py`
- **Variable:** `_alert_service_db = None`, `_alert_service_stub = None`
- **Factory:** `get_alert_service(use_db: bool = True) -> AlertService`
- **Dependencies:** `use_db` flag
- **Usage:** Used by macro_hound agent

##### `backend/app/services/optimizer.py`
- **Variable:** `_optimizer_service: Optional[OptimizerService] = None`
- **Factory:** `get_optimizer_service(use_db: bool = True, db_pool=None) -> OptimizerService`
- **Dependencies:** `db_pool` (optional)
- **Usage:** Used by financial_analyst agent

##### `backend/app/services/reports.py`
- **Variable:** `_reports_service = None`
- **Factory:** `get_reports_service() -> ReportService`
- **Dependencies:** None (minimal)
- **Usage:** Used by agents for report generation

##### `backend/app/services/risk.py`
- **Variable:** `_risk_service: Optional[RiskService] = None`
- **Factory:** `get_risk_service() -> RiskService`
- **Dependencies:** None (minimal)
- **Usage:** Used by agents for risk analysis

##### `backend/app/services/cycles.py`
- **Variable:** `_cycles_service: Optional[CyclesService] = None`
- **Factory:** `get_cycles_service(db_pool=None) -> CyclesService`
- **Dependencies:** `db_pool` (optional)
- **Usage:** Used by macro_hound agent

##### `backend/app/services/benchmarks.py`
- **Variable:** `_benchmark_service: Optional[BenchmarkService] = None`
- **Factory:** `get_benchmark_service(use_db: bool = True) -> BenchmarkService`
- **Dependencies:** `use_db` flag
- **Usage:** Used by agents for benchmark comparison

##### `backend/app/services/auth.py`
- **Variable:** `_auth_service = None`
- **Factory:** `get_auth_service() -> AuthService`
- **Dependencies:** None (minimal)
- **Usage:** Used by API routes for authentication

##### `backend/app/services/audit.py`
- **Variable:** `_audit_service = None`
- **Factory:** `get_audit_service(db_pool: Optional[asyncpg.Pool] = None) -> AuditService`
- **Dependencies:** `db_pool` (optional)
- **Usage:** Used by API routes for audit logging

##### `backend/app/services/fred_transformation.py`
- **Variable:** `_transformation_service = None`
- **Factory:** `get_transformation_service() -> FREDTransformationService`
- **Dependencies:** None (minimal)
- **Usage:** Used by macro service for data transformation

##### `backend/app/services/indicator_config.py`
- **Variable:** `_config_manager: Optional[IndicatorConfigManager] = None`
- **Factory:** `get_config_manager() -> IndicatorConfigManager`
- **Dependencies:** None (minimal)
- **Usage:** Used by macro service for indicator configuration

##### `backend/app/services/playbooks.py`
- **Variable:** `_playbook_generator = None`
- **Factory:** `get_playbook_generator() -> PlaybookGenerator`
- **Dependencies:** None (minimal)
- **Usage:** Used by agents for playbook generation

##### `backend/app/services/rights_registry.py`
- **Variable:** `_registry: Optional[RightsRegistry] = None`
- **Factory:** `get_rights_registry() -> RightsRegistry` (if exists)
- **Dependencies:** None (minimal)
- **Usage:** Used by agents for rights checking

---

### 3. Database Query Singletons (3 instances)

##### `backend/app/db/pricing_pack_queries.py`
- **Variable:** `_pricing_pack_queries: Optional[PricingPackQueries] = None`
- **Factory:** `get_pricing_pack_queries(use_db: bool = True) -> PricingPackQueries`
- **Dependencies:** `use_db` flag
- **Usage:** Used by pricing service, executor

##### `backend/app/db/metrics_queries.py`
- **Variable:** `_metrics_queries: Optional[MetricsQueries] = None`
- **Factory:** `get_metrics_queries() -> MetricsQueries`
- **Dependencies:** None (minimal)
- **Usage:** Used by metrics service

##### `backend/app/db/continuous_aggregate_manager.py`
- **Variable:** `_continuous_aggregate_manager: Optional[ContinuousAggregateManager] = None`
- **Factory:** `get_continuous_aggregate_manager() -> ContinuousAggregateManager`
- **Dependencies:** None (minimal)
- **Usage:** Used by database maintenance tasks

---

### 4. Registry Singletons (2 instances)

##### `backend/app/core/rights_registry.py`
- **Variable:** `_rights_registry_instance = None`
- **Factory:** `get_rights_registry() -> RightsRegistry`
- **Dependencies:** None (minimal)
- **Usage:** Used by agents for rights checking

##### `backend/app/integrations/provider_registry.py`
- **Variable:** `_registry: Optional[ProviderRegistry] = None`
- **Factory:** `get_provider_registry() -> ProviderRegistry`
- **Dependencies:** None (minimal)
- **Usage:** Used by agents for provider management

---

### 5. Core Singletons (2 instances)

##### `backend/app/api/executor.py`
- **Variable:** `_agent_runtime = None`, `_pattern_orchestrator = None`
- **Factory:** None (created in `init_app()`)
- **Dependencies:** Services dict
- **Usage:** Pattern execution, agent runtime

---

## Dependency Analysis

### Dependency Graph

```
db_pool (connection.py)
  ├── pricing_service
  ├── ratings_service
  ├── scenarios_service
  ├── macro_service
  ├── optimizer_service
  ├── metrics_queries
  ├── pricing_pack_queries
  └── audit_service

fred_provider
  └── macro_service

macro_service
  └── macro_hound_agent

scenario_service
  └── macro_hound_agent

alert_service
  └── macro_hound_agent

pricing_service
  └── data_harvester_agent

news_provider
  └── data_harvester_agent

ratings_service
  └── financial_analyst_agent

optimizer_service
  └── financial_analyst_agent
```

### Circular Dependencies

**Potential Circular Dependencies:**
1. **Services → Agents → Services:**
   - `macro_service` → `macro_hound_agent` → `scenario_service` → `macro_service` (indirect)
   - `pricing_service` → `data_harvester_agent` → `pricing_service` (indirect)

2. **Services → Services:**
   - `macro_service` → `macro_aware_scenario_service` → `macro_service` (potential)
   - `pricing_service` → `ratings_service` → `pricing_service` (potential)

**Note:** Need to verify actual circular dependencies by analyzing imports.

---

## Initialization Order Issues

### Current Initialization Order

1. **Database Pool** (`connection.py`)
2. **Services** (created on-demand via `get_*_service()`)
3. **Agents** (created on-demand via `get_*_agent()`)
4. **Agent Runtime** (created in `executor.py`)

### Problems

1. **Race Conditions:**
   - Services created on first access
   - No guarantee of initialization order
   - Multiple threads/requests can create multiple instances

2. **Testing Issues:**
   - Cannot mock services easily
   - Cannot reset state between tests
   - Global state persists across tests

3. **Memory Leaks:**
   - Services never cleaned up
   - Global state accumulates over time

---

## Migration Strategy

### Phase 2.1: Analyze Dependencies (Current)
- ✅ Inventory all singletons
- ⏳ Map dependency graph
- ⏳ Identify circular dependencies
- ⏳ Document initialization order

### Phase 2.2: Fix Circular Dependencies
- ⏳ Break circular dependencies
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

## Next Steps

1. **Map Dependency Graph:**
   - Analyze imports in each file
   - Create dependency graph
   - Identify circular dependencies

2. **Create DI Container:**
   - Design container interface
   - Implement service registration
   - Implement dependency resolution

3. **Migrate Services:**
   - Start with leaf services (no dependencies)
   - Work up dependency tree
   - Test after each migration

---

**Status:** 🚧 IN PROGRESS  
**Last Updated:** January 15, 2025  
**Next Step:** Map dependency graph and identify circular dependencies

