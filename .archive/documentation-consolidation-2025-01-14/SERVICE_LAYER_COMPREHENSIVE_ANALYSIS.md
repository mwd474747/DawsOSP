# Service Layer Comprehensive Analysis

**Date:** November 5, 2025  
**Analyzer:** Claude IDE Agent  
**Status:** ✅ **COMPREHENSIVE ANALYSIS COMPLETE**

---

## 📊 Executive Summary

The service layer contains **28 service files** (~18,274 lines total) with **significant duplication**, **inconsistent patterns**, and **anti-patterns** that create maintenance burden and technical debt.

**Key Findings:**
- 🔴 **Critical Duplication:** `_get_pack_date()` method duplicated across 5 services with inconsistent field names
- 🔴 **Critical Anti-Pattern:** Direct database queries bypassing `PricingService` 
- 🔴 **Critical Inconsistency:** Field name mismatch (`date` vs `asof_date`) causing bugs
- 🔴 **Critical Inconsistency:** Exception handling inconsistency (`ValueError` vs custom exceptions)
- ⚠️ **Medium Duplication:** `_get_portfolio_value()` duplicated across services
- ⚠️ **Medium Anti-Pattern:** Inconsistent singleton patterns
- ⚠️ **Medium Anti-Pattern:** Mixed dependency injection patterns

**Impact:** **HIGH** - Creates bugs, maintenance burden, and makes code harder to understand.

---

## 🏗️ Service Inventory & Classification

### Service Files (28 total)

**Core Business Services (10):**
1. `pricing.py` (795 lines) - Pricing pack queries, prices, FX rates
2. `metrics.py` (537 lines) - Performance metrics (TWR, Sharpe, drawdown)
3. `currency_attribution.py` (452 lines) - Currency attribution (local + FX + interaction)
4. `scenarios.py` (966 lines) - Scenario stress testing
5. `risk_metrics.py` (508 lines) - VaR, CVaR, tracking error
6. `factor_analysis.py` (435 lines) - Factor exposures via regression
7. `optimizer.py` (1,650 lines) - Portfolio optimization (Riskfolio-Lib)
8. `ratings.py` - Quality ratings (Buffett checklist)
9. `benchmarks.py` - Benchmark comparison
10. `risk.py` - Risk analysis

**Infrastructure Services (6):**
11. `auth.py` - JWT authentication, user management
12. `audit.py` - Audit logging
13. `trade_execution.py` - Trade execution
14. `corporate_actions.py` - Corporate actions (dividends, splits)
15. `notifications.py` - Notification delivery
16. `reports.py` - PDF/CSV report generation

**Macro/Economic Services (4):**
17. `macro.py` - Macro indicators, regime detection
18. `macro_aware_scenarios.py` - Regime-aware scenario analysis
19. `cycles.py` - Macro cycle detection (STDC, LTDC, Empire)
20. `macro_data_agent.py` - Macro data fetching

**Data Transformation Services (3):**
21. `fred_transformation.py` - FRED data transformation
22. `fundamentals_transformer.py` - FMP fundamentals transformation
23. `indicator_config.py` - Indicator configuration

**Alerting Services (2):**
24. `alerts.py` - Alert evaluation
25. `alert_delivery.py` - Alert delivery

**Other Services (3):**
26. `rights_registry.py` - Rights management
27. `playbooks.py` - Playbook execution
28. `dlq.py` - Dead letter queue

**Total:** 28 services, ~18,274 lines

---

## 🔍 Service Patterns Analysis

### Pattern 1: Singleton Services ✅

**Services Using Singleton Pattern:**
- `pricing.py` - `get_pricing_service()` / `init_pricing_service()`
- `scenarios.py` - `get_scenario_service()`
- `optimizer.py` - `get_optimizer_service()`
- `macro_aware_scenarios.py` - `get_macro_aware_scenario_service()`
- `macro.py` - `get_macro_service()`
- `fred_transformation.py` - `get_transformation_service()`
- `reports.py` - `get_reports_service()`
- `audit.py` - `get_audit_service()`
- `cycles.py` - `get_cycles_service()`
- `benchmarks.py` - `get_benchmark_service()` / `init_benchmark_service()`
- `alerts.py` - `get_alert_service()`

**Pattern:**
```python
_service: Optional[Service] = None

def get_service() -> Service:
    global _service
    if _service is None:
        _service = Service()
    return _service
```

**Status:** ✅ **Appropriate** - Singleton pattern for stateless services

---

### Pattern 2: Constructor-Based Services ⚠️

**Services Using Constructor Pattern:**
- `metrics.py` - `PerformanceCalculator(db)`
- `currency_attribution.py` - `CurrencyAttributor(db)`
- `risk_metrics.py` - `RiskMetrics(db)`
- `factor_analysis.py` - `FactorAnalyzer(db)`

**Pattern:**
```python
class Service:
    def __init__(self, db):
        self.db = db
```

**Status:** ⚠️ **Inconsistent** - Some services use singletons, others use constructors

**Issue:** Mixed patterns make it harder to understand how services are instantiated

---

### Pattern 3: Direct Database Access ⚠️

**Services Accessing Database Directly:**
- `metrics.py` - `self.db.fetchrow()`, `self.db.fetch()`
- `currency_attribution.py` - `self.db.fetchrow()`, `self.db.fetch()`
- `risk_metrics.py` - `self.db.fetchrow()`, `self.db.fetch()`
- `factor_analysis.py` - `self.db.fetchrow()`, `self.db.fetch()`
- `scenarios.py` - `execute_query()`, `execute_query_one()`
- `pricing.py` - `execute_query_one()`, `execute_query()`

**Pattern:**
```python
# Direct database queries
row = await self.db.fetchrow("SELECT ... FROM pricing_packs WHERE id = $1", pack_id)
```

**Status:** ⚠️ **Inconsistent** - Some services use `PricingService`, others query directly

**Issue:** Bypasses `PricingService` abstraction, creates duplication

---

### Pattern 4: Service-to-Service Dependencies ✅

**Services Using Other Services:**
- `scenarios.py` - Uses `PricingService.get_latest_pack()`
- `financial_analyst.py` - Uses `PricingService`, `CurrencyAttributor`, `OptimizerService`, `RatingsService`
- `alerts.py` - Uses `MacroService` (via import)

**Pattern:**
```python
from app.services.pricing import get_pricing_service

pricing_service = get_pricing_service()
pack = await pricing_service.get_latest_pack()
```

**Status:** ✅ **Appropriate** - Services should use other services when appropriate

**Issue:** Not all services follow this pattern (some query directly)

---

## 🔴 Critical Duplications Found

### Duplication 1: `_get_pack_date()` Method (CRITICAL)

**Duplicated in 5 services:**
1. `metrics.py:500` - Uses `SELECT date FROM pricing_packs`
2. `currency_attribution.py:401` - Uses `SELECT date FROM pricing_packs`
3. `risk_metrics.py:500` - Uses `SELECT asof_date FROM pricing_packs` ⚠️ **FIELD NAME MISMATCH**
4. `factor_analysis.py:427` - Uses `SELECT asof_date FROM pricing_packs` ⚠️ **FIELD NAME MISMATCH**
5. `optimizer.py:1538` - Uses `SELECT date FROM pricing_packs`

**Current Implementation (metrics.py):**
```python
async def _get_pack_date(self, pack_id: str) -> date:
    """Get as-of date for pricing pack."""
    row = await self.db.fetchrow(
        "SELECT date FROM pricing_packs WHERE id = $1", pack_id
    )
    if not row:
        raise ValueError(f"Pricing pack not found: {pack_id}")
    return row["date"]
```

**Current Implementation (risk_metrics.py) - FIELD NAME MISMATCH:**
```python
async def _get_pack_date(self, pack_id: str) -> date:
    """Get as-of date for pricing pack."""
    row = await self.db.fetchrow(
        "SELECT asof_date FROM pricing_packs WHERE id = $1", pack_id
    )
    if not row:
        raise ValueError(f"Pricing pack not found: {pack_id}")
    return row["asof_date"]
```

**Issues:**
1. ⚠️ **Field Name Inconsistency:** Some use `date`, others use `asof_date` (likely causes bugs)
2. ⚠️ **Exception Handling:** All raise `ValueError` instead of `PricingPackNotFoundError`
3. ⚠️ **Direct Database Access:** Bypasses `PricingService` abstraction
4. ⚠️ **Code Duplication:** Same logic repeated 5 times

**Impact:** **HIGH** - Field name mismatch likely causes runtime errors

**Recommended Fix:**
```python
# Use PricingService instead
from app.services.pricing import get_pricing_service

pricing_service = get_pricing_service()
pack = await pricing_service.get_pack_by_id(pack_id, raise_if_not_found=True)
end_date = pack.date  # Use PricingPack object
```

**Or create shared helper:**
```python
# backend/app/services/pricing_helpers.py
async def get_pack_date(pack_id: str) -> date:
    """Get as-of date for pricing pack."""
    from app.services.pricing import get_pricing_service
    pricing_service = get_pricing_service()
    pack = await pricing_service.get_pack_by_id(pack_id, raise_if_not_found=True)
    return pack.date
```

---

### Duplication 2: `_get_portfolio_value()` Method (MEDIUM)

**Duplicated in 2 services:**
1. `metrics.py:509` - Portfolio value calculation
2. `currency_attribution.py:419` - Portfolio value calculation

**Current Implementation (metrics.py):**
```python
async def _get_portfolio_value(self, portfolio_id: str, pack_id: str) -> Decimal:
    """
    Get total portfolio value from pricing pack.
    Sums: quantity_open × price × fx_rate for all positions.
    """
    positions = await self.db.fetch(
        """
        SELECT l.quantity_open, p.close, COALESCE(fx.rate, 1.0) as fx_rate
        FROM lots l
        JOIN prices p ON l.security_id = p.security_id AND p.pricing_pack_id = $2
        LEFT JOIN fx_rates fx ON p.currency = fx.base_ccy
            AND fx.quote_ccy = (SELECT base_currency FROM portfolios WHERE id = $1)
            AND fx.pricing_pack_id = $2
        WHERE l.portfolio_id = $1 AND l.quantity_open > 0
        """,
        portfolio_id,
        pack_id,
    )
    total = sum(...)
    return Decimal(str(total))
```

**Current Implementation (currency_attribution.py):**
```python
async def _get_portfolio_value(
    self, portfolio_id: str, pack_id: str
) -> Decimal:
    """
    Get total portfolio value from pricing pack.
    Sums: quantity_open × price × fx_rate for all positions.
    """
    base_ccy = await self._get_base_currency(portfolio_id)
    positions = await self.db.fetch(
        """
        SELECT
            l.security_id,
            l.quantity_open,
            p.close as price,
            COALESCE(fx.rate, 1.0) as fx_rate
        FROM lots l
        JOIN prices p ON l.security_id = p.security_id AND p.pricing_pack_id = $2
        LEFT JOIN fx_rates fx ON p.currency = fx.base_ccy
            AND fx.quote_ccy = $3
            AND fx.pricing_pack_id = $2
        WHERE l.portfolio_id = $1 AND l.quantity_open > 0
        """,
        portfolio_id,
        pack_id,
        base_ccy,
    )
    total = sum(...)
    return Decimal(str(total))
```

**Issues:**
1. ⚠️ **Code Duplication:** Same logic with slight variations
2. ⚠️ **Maintenance Burden:** Changes need to be made in multiple places
3. ⚠️ **Potential Bugs:** Variations might cause inconsistent results

**Impact:** **MEDIUM** - Duplication creates maintenance burden

**Recommended Fix:**
- Extract to shared helper in `pricing.py` or create `portfolio_helpers.py`
- Or add to `PricingService` as `get_portfolio_value(portfolio_id, pack_id)`

---

### Duplication 3: `_get_base_currency()` Method (LOW)

**Duplicated in 1 service:**
- `currency_attribution.py:410` - Gets portfolio base currency

**Current Implementation:**
```python
async def _get_base_currency(self, portfolio_id: str) -> str:
    """Get portfolio base currency."""
    row = await self.db.fetchrow(
        "SELECT base_currency FROM portfolios WHERE id = $1", portfolio_id
    )
    if not row:
        raise ValueError(f"Portfolio not found: {portfolio_id}")
    return row["base_currency"]
```

**Issues:**
1. ⚠️ **Exception Handling:** Raises `ValueError` instead of custom exception
2. ⚠️ **Potential Duplication:** Might be used elsewhere

**Impact:** **LOW** - Single occurrence, but could be shared if needed

---

## 🔴 Critical Anti-Patterns Found

### Anti-Pattern 1: Direct Database Queries Bypassing PricingService (CRITICAL)

**Services Querying pricing_packs Directly:**
1. `metrics.py:503` - `SELECT date FROM pricing_packs WHERE id = $1`
2. `currency_attribution.py:404` - `SELECT date FROM pricing_packs WHERE id = $1`
3. `currency_attribution.py:125` - `SELECT id FROM pricing_packs WHERE date = $1`
4. `risk_metrics.py:503` - `SELECT asof_date FROM pricing_packs WHERE id = $1`
5. `factor_analysis.py:430` - `SELECT asof_date FROM pricing_packs WHERE id = $1`
6. `optimizer.py:1540` - `SELECT date FROM pricing_packs WHERE id = $1`
7. `alerts.py:650` - `SELECT id FROM pricing_packs WHERE date <= $1`

**Issue:**
- Bypasses `PricingService` abstraction
- No validation of pack_id format
- No exception handling consistency
- Field name mismatch (`date` vs `asof_date`)

**Impact:** **HIGH** - Creates bugs, maintenance burden, inconsistency

**Recommended Fix:**
```python
# Instead of:
row = await self.db.fetchrow("SELECT date FROM pricing_packs WHERE id = $1", pack_id)

# Use:
from app.services.pricing import get_pricing_service
pricing_service = get_pricing_service()
pack = await pricing_service.get_pack_by_id(pack_id, raise_if_not_found=True)
end_date = pack.date
```

---

### Anti-Pattern 2: Exception Handling Inconsistency (CRITICAL)

**Services Raising ValueError:**
1. `metrics.py:506` - `raise ValueError(f"Pricing pack not found: {pack_id}")`
2. `currency_attribution.py:115` - `raise ValueError(f"pack_id is required and cannot be empty")`
3. `currency_attribution.py:407` - `raise ValueError(f"Pricing pack not found: {pack_id}")`
4. `risk_metrics.py:506` - `raise ValueError(f"Pricing pack not found: {pack_id}")`
5. `factor_analysis.py:433` - `raise ValueError(f"Pricing pack not found: {pack_id}")`

**Services Using Custom Exceptions:**
1. `pricing.py` - Uses `PricingPackNotFoundError`, `PricingPackValidationError`, `PricingPackStaleError`
2. `scenarios.py` - Uses `PricingPackNotFoundError`, `PricingPackStaleError`

**Issue:**
- Inconsistent exception types
- API layer must catch both `ValueError` and custom exceptions
- Makes error handling more complex

**Impact:** **HIGH** - Creates complexity in error handling

**Recommended Fix:**
- Update all services to use custom exceptions from `app.core.types`
- Use `PricingPackNotFoundError` instead of `ValueError`

---

### Anti-Pattern 3: Field Name Inconsistency (CRITICAL)

**Field Name Mismatch:**
- `metrics.py:503` - Uses `SELECT date FROM pricing_packs` ✅
- `currency_attribution.py:404` - Uses `SELECT date FROM pricing_packs` ✅
- `optimizer.py:1540` - Uses `SELECT date FROM pricing_packs` ✅
- `risk_metrics.py:503` - Uses `SELECT asof_date FROM pricing_packs` ❌ **WRONG FIELD**
- `factor_analysis.py:430` - Uses `SELECT asof_date FROM pricing_packs` ❌ **WRONG FIELD**

**Issue:**
- `pricing_packs` table has `date` column, not `asof_date`
- `risk_metrics.py` and `factor_analysis.py` will fail at runtime
- This is a **critical bug**

**Impact:** **CRITICAL** - Runtime errors when these services are used

**Recommended Fix:**
- Change `risk_metrics.py:503` to use `date` instead of `asof_date`
- Change `factor_analysis.py:430` to use `date` instead of `asof_date`
- Or better: Use `PricingService.get_pack_by_id()` which returns `PricingPack.date`

---

### Anti-Pattern 4: Inconsistent Singleton Patterns (MEDIUM)

**Singleton Services:**
- `pricing.py` - `get_pricing_service()` / `init_pricing_service()`
- `scenarios.py` - `get_scenario_service()`
- `optimizer.py` - `get_optimizer_service()`
- `macro.py` - `get_macro_service()`
- `reports.py` - `get_reports_service()`
- `audit.py` - `get_audit_service()`
- `cycles.py` - `get_cycles_service()`
- `benchmarks.py` - `get_benchmark_service()` / `init_benchmark_service()`
- `alerts.py` - `get_alert_service()`

**Constructor-Based Services:**
- `metrics.py` - `PerformanceCalculator(db)`
- `currency_attribution.py` - `CurrencyAttributor(db)`
- `risk_metrics.py` - `RiskMetrics(db)`
- `factor_analysis.py` - `FactorAnalyzer(db)`

**Issue:**
- Inconsistent patterns make it harder to understand how services are instantiated
- Some services require `db` parameter, others don't
- Makes dependency injection more complex

**Impact:** **MEDIUM** - Creates confusion, harder to maintain

**Recommended Fix:**
- Standardize on singleton pattern for stateless services
- Or standardize on constructor pattern for services that need `db`

---

### Anti-Pattern 5: Mixed Database Access Patterns (MEDIUM)

**Services Using Direct Database Access:**
- `metrics.py` - `self.db.fetchrow()`, `self.db.fetch()`
- `currency_attribution.py` - `self.db.fetchrow()`, `self.db.fetch()`
- `risk_metrics.py` - `self.db.fetchrow()`, `self.db.fetch()`
- `factor_analysis.py` - `self.db.fetchrow()`, `self.db.fetch()`

**Services Using Connection Helpers:**
- `scenarios.py` - `execute_query()`, `execute_query_one()`, `execute_statement()`
- `pricing.py` - `execute_query_one()`, `execute_query()`

**Services Using PricingService:**
- `scenarios.py` - Uses `PricingService.get_latest_pack()`

**Issue:**
- Three different patterns for database access
- Makes code harder to understand and maintain

**Impact:** **MEDIUM** - Creates confusion, harder to maintain

**Recommended Fix:**
- Standardize on `execute_query()`, `execute_query_one()`, `execute_statement()` from `app.db.connection`
- Or standardize on service-to-service calls (e.g., `PricingService`)

---

## 📋 Service Purpose Analysis

### Core Business Services

**1. PricingService (`pricing.py`)**
- **Purpose:** Query prices and FX rates from pricing packs
- **Pattern:** Singleton with `get_pricing_service()`
- **Status:** ✅ **Well-designed** - Uses custom exceptions, proper validation
- **Issues:** None identified

**2. PerformanceCalculator (`metrics.py`)**
- **Purpose:** Calculate TWR, MWR, Sharpe, Max Drawdown
- **Pattern:** Constructor-based (`PerformanceCalculator(db)`)
- **Status:** ⚠️ **Has Issues** - Direct database queries, `ValueError` exceptions, duplicated `_get_pack_date()`
- **Issues:**
  - Direct database queries bypassing `PricingService`
  - Uses `ValueError` instead of custom exceptions
  - Duplicated `_get_pack_date()` method

**3. CurrencyAttributor (`currency_attribution.py`)**
- **Purpose:** Decompose multi-currency portfolio returns into local + FX + interaction
- **Pattern:** Constructor-based (`CurrencyAttributor(db)`)
- **Status:** ⚠️ **Has Issues** - Direct database queries, `ValueError` exceptions, duplicated methods
- **Issues:**
  - Direct database queries bypassing `PricingService`
  - Uses `ValueError` instead of custom exceptions
  - Duplicated `_get_pack_date()` and `_get_portfolio_value()` methods

**4. ScenarioService (`scenarios.py`)**
- **Purpose:** Apply macro shocks to portfolio and suggest hedges
- **Pattern:** Singleton with `get_scenario_service()`
- **Status:** ✅ **Well-designed** - Uses `PricingService`, custom exceptions
- **Issues:** None identified (uses `PricingService` correctly)

**5. RiskMetrics (`risk_metrics.py`)**
- **Purpose:** Compute VaR, CVaR, tracking error, risk decomposition
- **Pattern:** Constructor-based (`RiskMetrics(db)`)
- **Status:** 🔴 **Has Critical Issues** - Field name mismatch, direct queries, `ValueError` exceptions
- **Issues:**
  - **CRITICAL:** Uses `asof_date` instead of `date` (will fail at runtime)
  - Direct database queries bypassing `PricingService`
  - Uses `ValueError` instead of custom exceptions
  - Duplicated `_get_pack_date()` method

**6. FactorAnalyzer (`factor_analysis.py`)**
- **Purpose:** Compute factor exposures and attribution via regression
- **Pattern:** Constructor-based (`FactorAnalyzer(db)`)
- **Status:** 🔴 **Has Critical Issues** - Field name mismatch, direct queries, `ValueError` exceptions
- **Issues:**
  - **CRITICAL:** Uses `asof_date` instead of `date` (will fail at runtime)
  - Direct database queries bypassing `PricingService`
  - Uses `ValueError` instead of custom exceptions
  - Duplicated `_get_pack_date()` method

**7. OptimizerService (`optimizer.py`)**
- **Purpose:** Portfolio optimization using Riskfolio-Lib
- **Pattern:** Singleton with `get_optimizer_service()`
- **Status:** ⚠️ **Has Issues** - Direct database queries, duplicated `_get_pack_date()`
- **Issues:**
  - Direct database queries bypassing `PricingService`
  - Duplicated `_get_pack_date()` method

---

## 🔄 Service Integration Patterns

### Pattern: Agent → Service

**Example:**
```python
# financial_analyst.py
from app.services.pricing import get_pricing_service
from app.services.currency_attribution import CurrencyAttributor
from app.services.optimizer import get_optimizer_service
from app.services.ratings import get_ratings_service

# Agent capability calls service
pricing_service = get_pricing_service()
pack = await pricing_service.get_latest_pack()
```

**Status:** ✅ **Appropriate** - Agents use services for business logic

**Issue:** Not all services follow this pattern (some use constructors)

---

### Pattern: Service → Service

**Example:**
```python
# scenarios.py
from app.services.pricing import get_pricing_service

pricing_service = get_pricing_service()
latest_pack = await pricing_service.get_latest_pack(
    require_fresh=True,
    raise_if_not_found=True
)
```

**Status:** ✅ **Appropriate** - Services should use other services when appropriate

**Issue:** Not all services follow this pattern (some query directly)

---

### Pattern: Service → Database

**Example:**
```python
# metrics.py
row = await self.db.fetchrow(
    "SELECT date FROM pricing_packs WHERE id = $1", pack_id
)
```

**Status:** ⚠️ **Inconsistent** - Some services use `PricingService`, others query directly

**Issue:** Creates duplication and inconsistency

---

## 🎯 Service Dependency Graph

```
PricingService (core)
  ↓
  ├─→ ScenarioService (uses get_latest_pack)
  ├─→ FinancialAnalyst (uses get_latest_pack, get_price)
  └─→ [Should be used by but aren't:]
      ├─→ PerformanceCalculator (queries directly)
      ├─→ CurrencyAttributor (queries directly)
      ├─→ RiskMetrics (queries directly)
      ├─→ FactorAnalyzer (queries directly)
      └─→ OptimizerService (queries directly)
```

**Issue:** Most services bypass `PricingService` and query directly

---

## 📊 Anti-Pattern Summary

| Anti-Pattern | Severity | Services Affected | Impact |
|--------------|----------|------------------|--------|
| **Field Name Mismatch** | 🔴 CRITICAL | `risk_metrics.py`, `factor_analysis.py` | Runtime errors |
| **Direct Database Queries** | 🔴 CRITICAL | 7 services | Bypasses abstraction, creates bugs |
| **Exception Handling Inconsistency** | 🔴 CRITICAL | 5 services | Complex error handling |
| **Duplicated `_get_pack_date()`** | 🔴 CRITICAL | 5 services | Maintenance burden, bugs |
| **Duplicated `_get_portfolio_value()`** | ⚠️ MEDIUM | 2 services | Maintenance burden |
| **Inconsistent Singleton Patterns** | ⚠️ MEDIUM | All services | Confusion |
| **Mixed Database Access Patterns** | ⚠️ MEDIUM | All services | Confusion |

---

## 🎯 Recommended Refactoring Plan

### Phase 1: Critical Fixes (IMMEDIATE)

**Priority 1: Fix Field Name Mismatch (CRITICAL)**
- Fix `risk_metrics.py:503` - Change `asof_date` → `date`
- Fix `factor_analysis.py:430` - Change `asof_date` → `date`
- Test to ensure no runtime errors

**Priority 2: Replace Direct Queries with PricingService (CRITICAL)**
- Update `metrics.py` to use `PricingService.get_pack_by_id()`
- Update `currency_attribution.py` to use `PricingService.get_pack_by_id()`
- Update `risk_metrics.py` to use `PricingService.get_pack_by_id()`
- Update `factor_analysis.py` to use `PricingService.get_pack_by_id()`
- Update `optimizer.py` to use `PricingService.get_pack_by_id()`
- Update `alerts.py` to use `PricingService.get_pack_by_id()`

**Priority 3: Replace ValueError with Custom Exceptions (CRITICAL)**
- Update `metrics.py:506` to use `PricingPackNotFoundError`
- Update `currency_attribution.py:115,407` to use `PricingPackValidationError` / `PricingPackNotFoundError`
- Update `risk_metrics.py:506` to use `PricingPackNotFoundError`
- Update `factor_analysis.py:433` to use `PricingPackNotFoundError`

### Phase 2: Extract Shared Helpers (MEDIUM)

**Priority 4: Extract `_get_pack_date()` to Shared Helper**
- Create `backend/app/services/pricing_helpers.py`
- Move `_get_pack_date()` to shared helper
- Update all services to use shared helper
- Or better: Use `PricingService.get_pack_by_id()` directly

**Priority 5: Extract `_get_portfolio_value()` to Shared Helper**
- Create `backend/app/services/portfolio_helpers.py`
- Move `_get_portfolio_value()` to shared helper
- Update all services to use shared helper
- Or add to `PricingService` as `get_portfolio_value(portfolio_id, pack_id)`

### Phase 3: Standardize Patterns (LOW)

**Priority 6: Standardize Singleton Patterns**
- Decide on singleton vs constructor pattern
- Migrate all services to consistent pattern
- Update documentation

**Priority 7: Standardize Database Access**
- Decide on direct queries vs service-to-service calls
- Migrate all services to consistent pattern
- Update documentation

---

## 📝 Detailed Findings by Service

### metrics.py (537 lines)

**Purpose:** Calculate TWR, MWR, Sharpe, Max Drawdown

**Pattern:** Constructor-based (`PerformanceCalculator(db)`)

**Issues:**
1. 🔴 Direct database query: `SELECT date FROM pricing_packs WHERE id = $1` (line 503)
2. 🔴 Raises `ValueError` instead of `PricingPackNotFoundError` (line 506)
3. 🔴 Duplicated `_get_pack_date()` method (line 500)
4. ⚠️ Duplicated `_get_portfolio_value()` method (line 509)

**Dependencies:**
- Requires `db` parameter in constructor
- No service dependencies

**Recommendation:**
- Use `PricingService.get_pack_by_id()` instead of direct query
- Use `PricingPackNotFoundError` instead of `ValueError`
- Extract `_get_portfolio_value()` to shared helper

---

### currency_attribution.py (452 lines)

**Purpose:** Decompose multi-currency portfolio returns into local + FX + interaction

**Pattern:** Constructor-based (`CurrencyAttributor(db)`)

**Issues:**
1. 🔴 Direct database query: `SELECT date FROM pricing_packs WHERE id = $1` (line 404)
2. 🔴 Raises `ValueError` instead of `PricingPackNotFoundError` / `PricingPackValidationError` (lines 115, 407)
3. 🔴 Duplicated `_get_pack_date()` method (line 401)
4. ⚠️ Duplicated `_get_portfolio_value()` method (line 419)
5. ⚠️ Duplicated `_get_base_currency()` method (line 410)

**Dependencies:**
- Requires `db` parameter in constructor
- No service dependencies

**Recommendation:**
- Use `PricingService.get_pack_by_id()` instead of direct query
- Use custom exceptions instead of `ValueError`
- Extract shared helpers for portfolio operations

---

### risk_metrics.py (508 lines)

**Purpose:** Compute VaR, CVaR, tracking error, risk decomposition

**Pattern:** Constructor-based (`RiskMetrics(db)`)

**Issues:**
1. 🔴 **CRITICAL BUG:** Uses `asof_date` instead of `date` (line 503) - **WILL FAIL AT RUNTIME**
2. 🔴 Direct database query: `SELECT asof_date FROM pricing_packs WHERE id = $1` (line 503)
3. 🔴 Raises `ValueError` instead of `PricingPackNotFoundError` (line 506)
4. 🔴 Duplicated `_get_pack_date()` method (line 500)

**Dependencies:**
- Requires `db` parameter in constructor
- No service dependencies

**Recommendation:**
- **IMMEDIATE FIX:** Change `asof_date` → `date` (line 503)
- Use `PricingService.get_pack_by_id()` instead of direct query
- Use `PricingPackNotFoundError` instead of `ValueError`

---

### factor_analysis.py (435 lines)

**Purpose:** Compute factor exposures and attribution via regression

**Pattern:** Constructor-based (`FactorAnalyzer(db)`)

**Issues:**
1. 🔴 **CRITICAL BUG:** Uses `asof_date` instead of `date` (line 430) - **WILL FAIL AT RUNTIME**
2. 🔴 Direct database query: `SELECT asof_date FROM pricing_packs WHERE id = $1` (line 430)
3. 🔴 Raises `ValueError` instead of `PricingPackNotFoundError` (line 433)
4. 🔴 Duplicated `_get_pack_date()` method (line 427)

**Dependencies:**
- Requires `db` parameter in constructor
- No service dependencies

**Recommendation:**
- **IMMEDIATE FIX:** Change `asof_date` → `date` (line 430)
- Use `PricingService.get_pack_by_id()` instead of direct query
- Use `PricingPackNotFoundError` instead of `ValueError`

---

### optimizer.py (1,650 lines)

**Purpose:** Portfolio optimization using Riskfolio-Lib

**Pattern:** Singleton with `get_optimizer_service()`

**Issues:**
1. ⚠️ Direct database query: `SELECT date FROM pricing_packs WHERE id = $1` (line 1540)
2. ⚠️ Duplicated `_get_pack_date()` method (line 1538)

**Dependencies:**
- No constructor parameters (singleton)
- No service dependencies

**Recommendation:**
- Use `PricingService.get_pack_by_id()` instead of direct query

---

### scenarios.py (966 lines)

**Purpose:** Apply macro shocks to portfolio and suggest hedges

**Pattern:** Singleton with `get_scenario_service()`

**Status:** ✅ **Well-designed**
- Uses `PricingService.get_latest_pack()` correctly (line 760)
- Uses custom exceptions (`PricingPackNotFoundError`, `PricingPackStaleError`)
- No direct database queries for pricing packs

**Issues:** None identified

---

### alerts.py (1,430 lines)

**Purpose:** Alert evaluation service

**Pattern:** Singleton with `get_alert_service()`

**Issues:**
1. ⚠️ Direct database query: `SELECT id FROM pricing_packs WHERE date <= $1` (line 650)

**Dependencies:**
- Uses `MacroService` (via import)

**Recommendation:**
- Use `PricingService` to find pack by date instead of direct query

---

## 📊 Summary Statistics

**Total Services:** 28
**Total Lines:** ~18,274
**Services with Issues:** 7 (25%)
**Critical Issues:** 5 services
**Medium Issues:** 2 services

**Duplications:**
- `_get_pack_date()`: 5 occurrences
- `_get_portfolio_value()`: 2 occurrences
- `_get_base_currency()`: 1 occurrence

**Direct Database Queries:**
- Pricing pack queries: 7 services
- Portfolio queries: Multiple services
- Security queries: Multiple services

**Exception Handling:**
- Using `ValueError`: 5 services
- Using custom exceptions: 2 services (`pricing.py`, `scenarios.py`)

---

## 🎯 Priority Recommendations

### Immediate Actions (This Week)

1. **Fix Field Name Mismatch** (CRITICAL - 30 minutes)
   - `risk_metrics.py:503` - Change `asof_date` → `date`
   - `factor_analysis.py:430` - Change `asof_date` → `date`
   - Test to ensure no runtime errors

2. **Update Exception Handling** (CRITICAL - 2 hours)
   - Update all services to use `PricingPackNotFoundError` instead of `ValueError`
   - Update all services to use `PricingPackValidationError` for validation errors

3. **Replace Direct Queries with PricingService** (CRITICAL - 3 hours)
   - Update `metrics.py`, `currency_attribution.py`, `risk_metrics.py`, `factor_analysis.py`, `optimizer.py`, `alerts.py`
   - Use `PricingService.get_pack_by_id()` instead of direct queries

### Short-Term Actions (Next Week)

4. **Extract Shared Helpers** (MEDIUM - 2 hours)
   - Extract `_get_pack_date()` to shared helper or use `PricingService`
   - Extract `_get_portfolio_value()` to shared helper

5. **Standardize Patterns** (LOW - 4 hours)
   - Decide on singleton vs constructor pattern
   - Standardize database access patterns

---

## 📝 Conclusion

The service layer has **significant technical debt** with:
- 🔴 **Critical bugs** (field name mismatch causing runtime errors)
- 🔴 **Critical duplications** (5 instances of `_get_pack_date()`)
- 🔴 **Critical anti-patterns** (direct database queries bypassing `PricingService`)
- 🔴 **Critical inconsistencies** (exception handling)

**Recommendation:** Address critical issues immediately (Phase 1) to prevent runtime errors and reduce maintenance burden.

