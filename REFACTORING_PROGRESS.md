# Aggressive Refactoring Progress

**Date:** January 14, 2025  
**Status:** 🔄 **IN PROGRESS**

---

## ✅ Completed

### Phase 1: Critical Fixes
- ✅ **Tax patterns archived** - Moved to `.archive/tax-patterns-2025-01-14/`
- ✅ **Removed `metrics.compute`** - Removed from capabilities list (not implemented) - **COMPLETED 2025-01-14**
- ✅ **Added `@capability` decorators** - Added to 4 methods - **COMPLETED 2025-01-14**:
  - `metrics.compute_mwr` - Added decorator with inputs/outputs
  - `metrics.compute_sharpe` - Added decorator with inputs/outputs
  - `charts.overview` - Added decorator with inputs/outputs
  - `risk.overlay_cycle_phases` - Added decorator with inputs/outputs

### Phase 2: Zombie Code Removal
- ✅ **Removed singleton patterns** - Removed from:
  - `OptimizerService` - Removed `get_optimizer_service()` singleton
  - `RatingsService` - Removed `get_ratings_service()` singleton
  - `PricingService` - Marked `get_pricing_service()` as deprecated
- ✅ **Updated dependency injection** - Updated `FinancialAnalyst` to:
  - Import service classes directly (not getters)
  - Instantiate services with `db_pool` from `self.services.get("db")`
  - Removed all `get_optimizer_service()` and `get_ratings_service()` calls
  - Updated `get_pricing_service()` to use dependency injection

### Phase 3: Service Updates
- ✅ **Updated OptimizerService** - Added `db_pool` parameter to `__init__`
- ✅ **Updated PricingService** - Added `db_pool` parameter to `__init__`
- ✅ **RatingsService** - Already accepts `db_pool` parameter

---

## 🔄 In Progress

### Phase 4: UI Integration
- ✅ **HoldingsPage** - Refactored to use `PatternRenderer` with callback for summary stats
- ✅ **PerformancePage** - Already uses `PatternRenderer`
- ✅ **ScenariosPage** - Already uses `PatternRenderer`
- ✅ **AttributionPage** - Already uses `PatternRenderer`
- ✅ **OptimizerPage** - Already uses `PatternRenderer`
- ✅ **TransactionsPage** - Refactored to use `PatternRenderer` for portfolio overview
- ✅ **RatingsPage** - Refactored to use `PatternRenderer` for holdings and detailed ratings
- ⚠️ **MacroCyclesPage** - Already uses `PatternRenderer` (needs validation)
- ⚠️ **MarketDataPage** - Uses direct API calls for prices (PatternRenderer for news)
- ⚠️ **AlertsPage** - Uses `PatternRenderer` for suggested alerts, direct API for CRUD
- ⚠️ **AIInsightsPage** - Being addressed in separate refactor plan

### Phase 5: Legacy Code Cleanup
- ✅ **ScenariosPageLegacy** - Removed
- ✅ **DashboardPageLegacy** - Removed

---

## 📋 Remaining Work

### High Priority
1. ✅ **Remove legacy functions** - Deleted `ScenariosPageLegacy` and `DashboardPageLegacy`
2. ✅ **Refactor RatingsPage** - Replaced direct API calls with `PatternRenderer`
3. ✅ **Refactor TransactionsPage** - Replaced direct API calls with `PatternRenderer`
4. ⚠️ **Refactor MarketDataPage** - Partially refactored (news uses PatternRenderer, prices still direct API)
5. ⚠️ **Refactor AlertsPage** - Partially refactored (suggested alerts use PatternRenderer, CRUD still direct API)

### Medium Priority
1. **Remove other singleton patterns** - Check remaining services:
   - `ScenarioService` - User reverted to singleton pattern (kept as-is)
   - `MacroService` - User reverted to singleton pattern (kept as-is)
   - `AlertService`
   - `CyclesService`
   - `RiskService`
   - `ReportsService`
   - `BenchmarkService`
   - `AuthService`
   - `AuditService`
2. ✅ **Fix UI data structure mismatches** - Updated chart components to handle nested structures - **COMPLETED 2025-01-14**
3. ✅ **Document pattern output format standards** - Created `PATTERN_OUTPUT_FORMAT_STANDARDS.md` - **COMPLETED 2025-01-14**
4. **Standardize capability naming** - Document and plan refactoring

### Low Priority
1. **Template variable validation** - Add validation in pattern orchestrator
2. **Document capability return structures** - Add documentation
3. **Clean up unused capabilities** - Document or remove

---

## 🎯 Next Steps

1. Remove legacy functions from `full_ui.html`
2. Refactor remaining pages to use `PatternRenderer`
3. Remove remaining singleton patterns from services
4. Fix UI data structure mismatches
5. Standardize capability naming

---

**Files Modified:**
- `backend/app/agents/financial_analyst.py` - Added decorators, removed `metrics.compute` from capabilities
- `backend/app/services/optimizer.py` - Removed singleton, added `db_pool` parameter
- `backend/app/services/ratings.py` - Removed singleton
- `backend/app/services/pricing.py` - Marked singleton as deprecated, added `db_pool` parameter
- `backend/patterns/tax_harvesting_opportunities.json` - Archived
- `backend/patterns/portfolio_tax_report.json` - Archived
- `full_ui.html` - Improved chart components to handle nested structures defensively
- `PATTERN_OUTPUT_FORMAT_STANDARDS.md` - Created documentation for pattern output formats

