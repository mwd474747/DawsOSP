# Constants Extraction - Executive Summary

**Status**: 🎯 READY TO START IN PARALLEL WITH PHASE 2 (UPDATED)
**Plan**: [DOMAIN_DRIVEN_CONSTANTS_PLAN.md](DOMAIN_DRIVEN_CONSTANTS_PLAN.md)
**Scope**: **200+ magic numbers** (from Replit comprehensive analysis)

---

## Can I Work in Parallel? YES ✅

**Main IDE Agent** (Phase 2): Dependency Injection
- Files: `combined_server.py`, `core/di_container.py`, `core/agent_runtime.py`
- Focus: Service initialization, singleton removal

**Constants Extraction** (This Agent): Domain-driven constants
- Files: `services/*.py`, `integrations/*.py`, `frontend/full_ui.html`, creating `core/constants/`
- Focus: Extracting 200+ magic numbers to named constants (backend + frontend)

**Zero Overlap** - Different files, different concerns

---

## Key Differences from Generic Approach

### ❌ Generic Constants File (Basic)
```python
# constants.py
TRADING_DAYS = 252
CONFIDENCE_95 = 0.95
```

### ✅ Domain-Driven Architecture (DawsOS) - UPDATED

**Backend Constants** (Python):
```python
# backend/app/core/constants/
├── financial.py      # Portfolio valuation (40+ instances: 252, 365, annualization)
├── risk.py          # VaR/CVaR (35+ instances: 0.95, 0.05, factor thresholds)
├── macro.py         # Regime detection (15+ instances: z-scores, weights)
├── scenarios.py     # Monte Carlo (20+ instances: paths, tolerances)
├── integration.py   # API limits (25+ instances: timeouts, retries, rate limits)
├── validation.py    # Data quality (30+ instances: bounds, freshness)
├── time_periods.py  # Reusable conversions (10+ instances)
├── network.py       # Port numbers, connection config (8+ instances)
├── http_status.py   # HTTP status codes with descriptions (15+ instances)
└── versions.py      # Version numbers, compatibility (5+ instances)
```

**Frontend Constants** (JavaScript):
```javascript
# frontend/constants/
└── ui.js            # UI dimensions, fonts, opacity (50+ instances)
```

**Total**: 200+ magic numbers organized into 11 domain-specific modules

**Why Better**:
- ✅ Domain experts can find and update relevant constants
- ✅ Constants map to business concepts (not just numbers)
- ✅ Supports data validation and contracts
- ✅ Aligns with DawsOS architecture (5 core domains)
- ✅ Includes infrastructure concerns (network, HTTP, versions)
- ✅ Covers frontend UI consistency (NEW)

---

## Example: Financial Domain

### Current State (metrics.py:184)
```python
vol = float(np.std(returns) * np.sqrt(252))  # What is 252?
```

### After Migration
```python
from app.core.constants.financial import TRADING_DAYS_PER_YEAR

vol = float(np.std(returns) * np.sqrt(TRADING_DAYS_PER_YEAR))
```

**Documentation in constant**:
```python
# Industry Standard: 252 trading days per year (NYSE/NASDAQ calendar)
# Source: Excludes weekends + major holidays (~104 weekend days + 9 holidays)
TRADING_DAYS_PER_YEAR = 252
```

---

## DawsOS Domain Analysis

### 1. Portfolio Valuation Domain
**Services**: PricingService, MetricsService
**Key Constants**:
- `TRADING_DAYS_PER_YEAR = 252` (volatility annualization)
- `ANNUALIZATION_DAYS = 365` (TWR/MWR calculations)
- `LOOKBACK_1_YEAR = 252` (performance periods)

### 2. Risk Analytics Domain
**Services**: RiskMetricsService, FactorAnalysisService
**Key Constants**:
- `CONFIDENCE_LEVEL_95 = 0.95` (VaR calculation)
- `Z_SCORE_THRESHOLD_MODERATE = 2.0` (outlier detection)
- `MIN_SIGNIFICANT_FACTOR_LOADING = 0.05` (factor exposure)

### 3. Macro Regime Domain
**Services**: MacroService, CyclesService
**Key Constants**:
- `REGIME_CHANGE_Z_SCORE_THRESHOLD = 1.5` (regime detection)
- `MIN_REGIME_DURATION_DAYS = 90` (stability requirement)
- `DEFAULT_INDICATOR_WEIGHT = 1.0 / 7` (composite indicators)

### 4. Scenario Analysis Domain
**Services**: ScenariosService, OptimizerService
**Key Constants**:
- `MONTE_CARLO_PATHS_DEFAULT = 10000` (simulation accuracy)
- `DEFAULT_MAX_WEIGHT = 0.30` (diversification)
- `DEFAULT_SOLVER_TOLERANCE = 1e-6` (optimization convergence)

### 5. Data Integration Domain
**Services**: FRED/FMP/Polygon Providers
**Key Constants**:
- `FRED_RATE_LIMIT_REQUESTS = 120` (API limits)
- `DEFAULT_HTTP_TIMEOUT = 30.0` (network timeouts)
- `DEFAULT_MAX_RETRIES = 3` (retry policy)

---

## Integration with Broader Refactoring

### Synergy with Phase 1 (Exception Handling)
Constants enable better validation:
```python
from app.core.constants.validation import MAX_VALID_VOLATILITY

if volatility > MAX_VALID_VOLATILITY:
    raise ValueError(f"Volatility {volatility} exceeds max {MAX_VALID_VOLATILITY}")
```

### Synergy with Phase 2 (Dependency Injection)
Constants as service configuration:
```python
container.register_service(
    "pricing",
    PricingService,
    trading_days_per_year=TRADING_DAYS_PER_YEAR,  # Injected config
)
```

### Synergy with Data Quality (Future)
Constants define data contracts:
```python
PORTFOLIO_VALUE_CONTRACT = {
    "min_value": MIN_PORTFOLIO_VALUE,
    "max_value": MAX_PORTFOLIO_VALUE,
}
```

---

## Implementation Timeline - UPDATED

### Week 1: High-Value Domains + Infrastructure (25-32 hours)
1. Create constants infrastructure (backend + frontend)
2. Migrate Financial domain (40+ instances: `services/metrics.py`, `services/pricing.py`)
3. Migrate Risk domain (35+ instances: `services/risk_metrics.py`)
4. Migrate Integration domain (25+ instances: `integrations/*_provider.py`)
5. Migrate Infrastructure (23+ instances: HTTP status, ports, network)

### Week 2-3: Complete Backend Migration (8-12 hours)
6. Migrate Macro domain (15+ instances: `services/cycles.py`)
7. Migrate Scenarios domain (20+ instances: `services/scenarios.py`, `services/optimizer.py`)
8. Add validation using constants (30+ instances)

### Week 3: Frontend Migration (6-8 hours) - NEW
9. Create `frontend/constants/ui.js` (50+ instances)
10. Migrate UI magic numbers from `full_ui.html`
11. Update component styling to use constants

### Week 4: Finalize (4-6 hours)
12. Code review with domain experts
13. Integration testing (backend + frontend)
14. Merge to main

**Total**: 39-52 hours spread over 3-4 weeks (up from 27-36 hours)

---

## Testing Strategy

### Per-Domain Tests
Ensure numeric outputs match exactly:
```python
def test_sharpe_ratio_unchanged():
    # Old calculation
    old = returns.mean() * 252 / (returns.std() * np.sqrt(252))

    # New calculation
    new = returns.mean() * TRADING_DAYS_PER_YEAR / (
        returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    )

    assert abs(old - new) < 1e-10  # Identical
```

### Integration Tests
Run full suite after each domain:
```bash
pytest tests/test_metrics.py -v
pytest tests/test_risk_metrics.py -v
```

---

## Success Criteria

**Quantitative**:
- ✅ Zero magic numbers in migrated files
- ✅ All constants documented with domain context
- ✅ All tests pass (numeric outputs identical)
- ✅ 100% type hint coverage

**Qualitative**:
- ✅ Domain experts can understand constants
- ✅ Constants map to business concepts
- ✅ Code reads like domain language
- ✅ Supports data validation

---

## Risk Level: LOW ✅

**Why Low Risk**:
- No logic changes (just naming)
- Easy to verify (numeric outputs identical)
- Easy to rollback (git revert)
- No initialization changes
- No dependency injection changes
- Works independently of Phase 2

---

## Ready to Start?

**Answer: YES ✅**

**First Steps**:
1. Create `backend/app/core/constants/` directory structure
2. Implement `financial.py` module
3. Migrate `services/metrics.py` as pilot
4. Run tests to verify
5. Proceed with remaining domains

See [DOMAIN_DRIVEN_CONSTANTS_PLAN.md](DOMAIN_DRIVEN_CONSTANTS_PLAN.md) for complete details.

---

**Status**: 🎯 READY TO START (UPDATED with Replit Analysis)
**Scope**: 200+ magic numbers (doubled from initial estimate)
**Alignment**: Phase 7 of TECHNICAL_DEBT_REMOVAL_PLAN_V3.md
**Can Work in Parallel**: YES ✅

**Key Updates from Replit Analysis**:
- ✅ Identified 200+ instances (up from ~100 initial estimate)
- ✅ Added 4 new constants modules (network, http_status, versions, frontend/ui)
- ✅ Expanded timeline to 39-52 hours (reflects 200+ scope)
- ✅ Added Phase 4 for frontend UI constants migration
- ✅ Enhanced cache configuration with purpose-specific TTLs
- ✅ Comprehensive HTTP status code coverage for better error handling

**Next Steps**:
1. Get user approval to proceed
2. Create backend constants infrastructure (10 modules)
3. Create frontend constants infrastructure (1 module)
4. Begin Phase 1 migration (Financial domain)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
