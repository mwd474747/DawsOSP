# MACRO_ARCHITECT — Dalio Framework Implementation Specialist

**Agent Type**: Analytics
**Phase**: Week 3-4 (Analytics & Intelligence)
**Priority**: P1 (High - Core differentiator)
**Status**: Specification Complete
**Created**: 2025-10-21

---

## Mission

Implement **Ray Dalio's macro framework** (regime → factor → scenario analysis) with historical regime classification, factor exposure calculation, and Drawdown-at-Risk (DaR) scenario stress testing.

---

## Scope & Responsibilities

### In Scope

1. **Economic Regime Detection**
   - Classify current regime: Early/Mid/Late Expansion, Early/Deep Contraction
   - Input indicators: GDP growth, unemployment, inflation, yield curve, PMI
   - Output: Regime label + confidence score (0.0 - 1.0)

2. **Factor Exposure Analysis**
   - Portfolio factor tilts: Growth, Value, Momentum, Quality, Size
   - Benchmark comparison (e.g., 60/40 vs S&P 500/AGG)
   - Factor correlations and regime-conditional returns

3. **Scenario Analysis (DaR)**
   - Historical analog matching (e.g., 2008 crisis, dot-com bubble, COVID)
   - Expected drawdown calculation with confidence intervals
   - Position-level impact attribution

4. **Regime-Based Watchlists**
   - Auto-update `storage/knowledge/econ_regime_watchlist.json`
   - Surface opportunities/risks based on regime transitions

### Out of Scope

- ❌ Portfolio optimization (handled by OPTIMIZER_ARCHITECT)
- ❌ Real-time streaming analytics (batch nightly jobs only)
- ❌ Custom user-defined regimes (predefined framework only)

---

## Acceptance Criteria

### AC-1: Regime Detection (Dalio Framework)
**Given**: Economic indicators as of 2024-10-20
- GDP growth: 2.5% YoY
- Unemployment: 3.8%
- CPI inflation: 3.2%
- 10Y-2Y yield curve: +0.35%
- PMI: 52.1

**When**: Classify regime
**Then**:
- Regime = "Late Expansion" (confidence ≥ 0.75)
- Supporting evidence: Low unemployment + positive yield curve + expansionary PMI
- Golden test match: `tests/golden/macro/regime_late_expansion_2024Q4.json`

**Golden Test**: `tests/golden/macro/regime_detection_*.json` (5 scenarios)

---

### AC-2: Historical Regime Classification
**Given**: Historical indicator data (1980-2024)
**When**: Classify all historical regimes
**Then**:
- 2008 Q4: "Deep Contraction" (confidence ≥ 0.90)
- 2000 Q1: "Late Expansion" (dot-com peak)
- 2020 Q2: "Deep Contraction" (COVID crash)
- All classifications stored in `storage/knowledge/dalio_cycles.json`

**Validation**: Compare to known NBER recession dates (should align ±1 quarter)

---

### AC-3: Factor Exposure Calculation
**Given**: Portfolio with 70% stocks (60% US, 10% Int'l), 30% bonds
**When**: Calculate factor exposures
**Then**:
- Growth tilt: +0.45 (vs benchmark +0.20)
- Value tilt: -0.15 (vs benchmark 0.00)
- Momentum: +0.30
- Quality: +0.55
- Size: +0.10 (large-cap bias)

**Golden Test**: `tests/golden/macro/factor_exposure_60_40.json`

---

### AC-4: Scenario Analysis (DaR)
**Given**: Portfolio from AC-3
**When**: Run "2008 recession" scenario
**Then**:
- Expected drawdown: -35.2% (DaR)
- Confidence interval: (-42.1%, -28.3%) at 90% CI
- Position impacts:
  - AAPL: -$12,500 (tech drawdown)
  - AGG (bonds): +$3,200 (flight to quality)
  - Total portfolio: -$35,200 on $100k

**Golden Test**: `tests/golden/macro/scenario_2008_recession.json`

---

### AC-5: Regime Transition Alerting
**Given**: Previous regime = "Mid Expansion", current = "Late Expansion"
**When**: Regime detection runs (nightly job)
**Then**:
- Alert triggered: "Regime transition detected"
- Watchlist updated with late-expansion plays (e.g., defensive sectors, TIPS)
- Alert delivered within 60s median (SLO)

**Integration Test**: `tests/integration/test_regime_transition_alert.py`

---

## Implementation Specifications

### Regime Detection Logic

```python
# backend/app/analytics/regime_detector.py

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Literal
from app.core.types import RequestCtx, RegimeRequest, RegimeResponse

@dataclass(frozen=True)
class EconomicIndicators:
    """Dalio regime indicators."""
    gdp_growth_yoy: Decimal  # %
    unemployment_rate: Decimal  # %
    cpi_inflation_yoy: Decimal  # %
    yield_curve_10y_2y: Decimal  # bps
    pmi_manufacturing: Decimal  # index

Regime = Literal[
    "early_expansion",
    "mid_expansion",
    "late_expansion",
    "early_contraction",
    "deep_contraction",
]

class RegimeDetector:
    """Dalio economic regime classifier."""

    def detect(self, indicators: EconomicIndicators) -> tuple[Regime, Decimal]:
        """
        Classify economic regime with confidence score.

        Returns:
            (regime, confidence) where confidence ∈ [0.0, 1.0]
        """
        # Rule-based classification (Dalio framework)
        if indicators.gdp_growth_yoy < 0:
            if indicators.unemployment_rate > 6.0:
                return "deep_contraction", Decimal("0.95")
            else:
                return "early_contraction", Decimal("0.80")

        # Expansion phases
        if indicators.yield_curve_10y_2y < 0:
            # Inverted yield curve = late expansion warning
            return "late_expansion", Decimal("0.85")

        if indicators.unemployment_rate < 4.5 and indicators.gdp_growth_yoy > 2.0:
            if indicators.pmi_manufacturing > 55:
                return "mid_expansion", Decimal("0.90")
            else:
                return "late_expansion", Decimal("0.75")

        # Default: early expansion
        return "early_expansion", Decimal("0.70")

    async def detect_from_fred(self, ctx: RequestCtx, asof_date: date) -> RegimeResponse:
        """Fetch indicators from FRED and classify regime."""
        # Fetch indicators via PROVIDER_INTEGRATOR
        fred_provider = get_provider("fred")

        gdp = await fred_provider.call(ProviderRequest(
            endpoint="/series/observations",
            params={"series_id": "GDP", "observation_start": asof_date},
            ctx=ctx,
        ))

        unemployment = await fred_provider.call(ProviderRequest(
            endpoint="/series/observations",
            params={"series_id": "UNRATE", "observation_start": asof_date},
            ctx=ctx,
        ))

        # ... fetch CPI, yield curve, PMI

        indicators = EconomicIndicators(
            gdp_growth_yoy=Decimal(gdp.data[-1]["value"]),
            unemployment_rate=Decimal(unemployment.data[-1]["value"]),
            # ... other indicators
        )

        regime, confidence = self.detect(indicators)

        return RegimeResponse(
            asof_date=asof_date,
            regime=regime,
            confidence=confidence,
            indicators={
                "gdp_growth_yoy": indicators.gdp_growth_yoy,
                "unemployment_rate": indicators.unemployment_rate,
                # ... all indicators
            },
            ctx=ctx,
        )
```

---

### Factor Exposure Calculation

```python
# backend/app/analytics/factor_analyzer.py

from app.core.types import FactorExposureRequest, FactorExposureResponse
from decimal import Decimal

class FactorAnalyzer:
    """Portfolio factor exposure calculator."""

    FACTOR_DEFINITIONS = {
        "growth": lambda holding: holding.pe_ratio > 25,
        "value": lambda holding: holding.pb_ratio < 2.0,
        "momentum": lambda holding: holding.return_6m > 0.15,
        "quality": lambda holding: holding.roe > 0.15,
        "size": lambda holding: holding.market_cap > 100_000_000_000,  # Large-cap
    }

    async def calculate_exposures(
        self,
        ctx: RequestCtx,
        request: FactorExposureRequest,
    ) -> FactorExposureResponse:
        """Calculate factor exposures for portfolio."""
        # Load portfolio holdings
        holdings = await load_holdings(ctx, request.portfolio_id)

        exposures = {}
        for factor in request.factors:
            factor_fn = self.FACTOR_DEFINITIONS[factor]

            # Calculate weighted exposure
            total_value = sum(h.value for h in holdings)
            factor_value = sum(h.value for h in holdings if factor_fn(h))

            exposure = Decimal(factor_value / total_value) - Decimal("0.5")  # Center at 0
            exposures[factor] = exposure

        return FactorExposureResponse(
            portfolio_id=request.portfolio_id,
            exposures=exposures,
            ctx=ctx,
        )
```

---

### Scenario Analysis (DaR)

```python
# backend/app/analytics/scenario_analyzer.py

from app.core.types import ScenarioRequest, ScenarioResponse, PositionImpact
from decimal import Decimal

class ScenarioAnalyzer:
    """Drawdown-at-Risk (DaR) scenario stress tester."""

    SCENARIOS = {
        "recession": {
            "SPY": Decimal("-0.40"),  # -40% equities
            "AGG": Decimal("0.05"),    # +5% bonds (flight to quality)
            "GLD": Decimal("0.15"),    # +15% gold
        },
        "inflation_shock": {
            "SPY": Decimal("-0.15"),
            "AGG": Decimal("-0.10"),   # Bonds hurt by rising rates
            "GLD": Decimal("0.25"),
            "TIP": Decimal("0.10"),    # TIPS outperform
        },
        "rate_hike": {
            "SPY": Decimal("-0.10"),
            "AGG": Decimal("-0.08"),
            "USD": Decimal("0.05"),    # Dollar strengthens
        },
    }

    async def run_scenario(
        self,
        ctx: RequestCtx,
        request: ScenarioRequest,
    ) -> ScenarioResponse:
        """Run scenario stress test."""
        holdings = await load_holdings(ctx, request.portfolio_id)

        # Apply shocks
        shocks = request.custom_shocks or self.SCENARIOS[request.scenario]

        position_impacts = []
        total_impact = Decimal("0")

        for holding in holdings:
            shock = shocks.get(holding.symbol, Decimal("0"))
            impact = holding.value * shock

            position_impacts.append(PositionImpact(
                security_id=holding.security_id,
                symbol=holding.symbol,
                current_value=holding.value,
                scenario_value=holding.value + impact,
                impact=impact,
            ))

            total_impact += impact

        # Calculate expected drawdown (DaR)
        total_value = sum(h.value for h in holdings)
        expected_drawdown = total_impact / total_value

        # Confidence interval (Monte Carlo simulation - simplified here)
        ci_lower = expected_drawdown * Decimal("1.2")  # Pessimistic
        ci_upper = expected_drawdown * Decimal("0.8")  # Optimistic

        return ScenarioResponse(
            portfolio_id=request.portfolio_id,
            scenario=request.scenario,
            expected_return=expected_drawdown,  # Negative for drawdown
            expected_drawdown=abs(expected_drawdown),
            confidence_interval=(ci_lower, ci_upper),
            position_impacts=position_impacts,
            ctx=ctx,
        )
```

---

## Golden Tests

### Regime Detection
```json
// tests/golden/macro/regime_late_expansion_2024Q4.json
{
  "asof_date": "2024-10-20",
  "regime": "late_expansion",
  "confidence": 0.75,
  "indicators": {
    "gdp_growth_yoy": 2.5,
    "unemployment_rate": 3.8,
    "cpi_inflation_yoy": 3.2,
    "yield_curve_10y_2y": 0.35,
    "pmi_manufacturing": 52.1
  }
}
```

### Factor Exposure
```json
// tests/golden/macro/factor_exposure_60_40.json
{
  "portfolio_id": "uuid-placeholder",
  "exposures": {
    "growth": 0.45,
    "value": -0.15,
    "momentum": 0.30,
    "quality": 0.55,
    "size": 0.10
  }
}
```

### Scenario (2008 Recession)
```json
// tests/golden/macro/scenario_2008_recession.json
{
  "portfolio_id": "uuid-placeholder",
  "scenario": "recession",
  "expected_drawdown": 0.352,
  "confidence_interval": [-0.421, -0.283],
  "position_impacts": [
    {
      "symbol": "AAPL",
      "current_value": 50000,
      "scenario_value": 37500,
      "impact": -12500
    },
    {
      "symbol": "AGG",
      "current_value": 30000,
      "scenario_value": 33200,
      "impact": 3200
    }
  ]
}
```

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit/analytics/ -k "regime or factor or scenario"
```

**Coverage**:
- Regime classification logic (5 regimes, edge cases)
- Factor exposure calculations (5 factors)
- Scenario shock application

---

### Golden Tests
```bash
pytest tests/golden/macro/ --golden-update=never
```

**Scenarios**:
- Regime: 2008 Q4 (deep contraction), 2000 Q1 (late expansion), 2020 Q2 (COVID)
- Factor: 60/40 portfolio, 100% equities, risk parity
- Scenario: 2008 recession, 2020 COVID, 1970s stagflation

---

### Integration Tests
```bash
pytest tests/integration/test_macro_integration.py
```

**Flows**:
1. Fetch FRED indicators → classify regime
2. Load portfolio → calculate factor exposures
3. Run scenario → generate DaR report

---

## Observability

### Prometheus Metrics

```python
# Regime detection
regime_classification_total = Counter(
    "regime_classification_total",
    "Total regime classifications",
    ["regime"]
)

# Factor exposure
factor_exposure_calculated = Histogram(
    "factor_exposure_calculated",
    "Factor exposure values",
    ["factor"]
)

# Scenario runs
scenario_runs_total = Counter(
    "scenario_runs_total",
    "Total scenario stress tests",
    ["scenario"]
)
```

---

## Knowledge Graph Integration

### Auto-Update Regime Watchlist

```python
# Nightly job: Update regime watchlist
async def update_regime_watchlist(ctx: RequestCtx):
    """Update regime-based watchlist (nightly)."""
    regime_response = await regime_detector.detect_from_fred(ctx, date.today())

    # Load regime-specific opportunities
    if regime_response.regime == "late_expansion":
        watchlist = [
            "XLU",  # Utilities (defensive)
            "TIP",  # TIPS (inflation protection)
            "GLD",  # Gold (safe haven)
        ]
    elif regime_response.regime == "early_expansion":
        watchlist = [
            "XLF",  # Financials (benefit from growth)
            "XLI",  # Industrials
            "SPY",  # Broad equities
        ]
    # ... other regimes

    # Update knowledge graph
    await knowledge_graph.update_node(
        "econ_regime_watchlist",
        {
            "regime": regime_response.regime,
            "asof_date": regime_response.asof_date,
            "watchlist": watchlist,
            "confidence": regime_response.confidence,
        }
    )
```

---

## Handoff to Downstream Agents

### Inputs Required
- Economic indicators (FRED via PROVIDER_INTEGRATOR)
- Portfolio holdings (INFRASTRUCTURE_ARCHITECT)
- Benchmark definitions (stored in `storage/knowledge/`)

### Outputs Consumed By
- **OPTIMIZER_ARCHITECT** — Regime-aware rebalancing rules
- **UI_ARCHITECT** — Economic dashboard visualizations
- **REPORTING_ARCHITECT** — Macro commentary in reports
- **Alert system** — Regime transition notifications

---

## Related Documents

- **[PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)** — Section 5: Dalio Macro Framework
- **[PROVIDER_INTEGRATOR.md](../integration/PROVIDER_INTEGRATOR.md)** — FRED data source
- **[types.py](../../../backend/app/core/types.py)** — RegimeRequest/Response, ScenarioRequest/Response
- **[storage/knowledge/dalio_cycles.json](../../../storage/knowledge/dalio_cycles.json)** — Historical regime data

---

**Last Updated**: 2025-10-21
**Agent Owner**: Analytics Team
**Review Cycle**: Quarterly (regime framework validation)
