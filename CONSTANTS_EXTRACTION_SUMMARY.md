# Constants Extraction - Executive Summary

**Status**: 🎯 READY TO START IN PARALLEL WITH PHASE 2
**Plan**: [DOMAIN_DRIVEN_CONSTANTS_PLAN.md](DOMAIN_DRIVEN_CONSTANTS_PLAN.md)

---

## Can I Work in Parallel? YES ✅

**Main IDE Agent** (Phase 2): Dependency Injection
- Files: `combined_server.py`, `core/di_container.py`, `core/agent_runtime.py`
- Focus: Service initialization, singleton removal

**Constants Extraction** (This Agent): Domain-driven constants
- Files: `services/*.py`, `integrations/*.py`, creating `core/constants/`
- Focus: Extracting magic numbers to named constants

**Zero Overlap** - Different files, different concerns

---

## Key Differences from Generic Approach

### ❌ Generic Constants File (Basic)
```python
# constants.py
TRADING_DAYS = 252
CONFIDENCE_95 = 0.95
```

### ✅ Domain-Driven Architecture (DawsOS)
```python
# core/constants/
├── financial.py      # Portfolio valuation (252, 365, annualization)
├── risk.py          # VaR/CVaR (0.95, 0.05, factor thresholds)
├── macro.py         # Regime detection (z-scores, weights)
├── scenarios.py     # Monte Carlo (paths, tolerances)
├── integration.py   # API limits (timeouts, retries, rate limits)
├── validation.py    # Data quality (bounds, freshness)
└── time_periods.py  # Reusable conversions
```

**Why Better**:
- ✅ Domain experts can find and update relevant constants
- ✅ Constants map to business concepts (not just numbers)
- ✅ Supports data validation and contracts
- ✅ Aligns with DawsOS architecture (5 core domains)

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

## Implementation Timeline

### Week 1: High-Value Domains (15-20 hours)
1. Create constants infrastructure
2. Migrate Financial domain (`services/metrics.py`, `services/pricing.py`)
3. Migrate Risk domain (`services/risk_metrics.py`)
4. Migrate Integration domain (`integrations/*_provider.py`)

### Week 2: Complete Migration (8-12 hours)
5. Migrate Macro domain (`services/cycles.py`)
6. Migrate Scenarios domain (`services/scenarios.py`, `services/optimizer.py`)
7. Add validation using constants

### Week 3: Finalize (4-6 hours)
8. Code review with domain experts
9. Integration testing
10. Merge to main

**Total**: 27-36 hours spread over 3 weeks

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

**Status**: 🎯 AWAITING APPROVAL TO START
**Alignment**: Phase 7 of TECHNICAL_DEBT_REMOVAL_PLAN_V3.md
**Can Work in Parallel**: YES ✅

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
