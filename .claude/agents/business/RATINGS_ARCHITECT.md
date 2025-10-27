# RATINGS_ARCHITECT — Buffett Quality Scoring Specialist

**Agent Type**: Business Logic
**Phase**: Future Enhancement
**Priority**: P2 (Future - Core differentiator when implemented)
**Status**: ✅ Operational (Production Ready)
**Created**: 2025-10-21
**Last Updated**: October 27, 2025

---

## Current Status (2025-10-26)

### ✅ Agent + Service Shipping (Seeded Mode)
- `backend/app/agents/ratings_agent.py` and `backend/app/services/ratings.py` are live and wired through the orchestrator.
- `rating_rubrics` schema + seeds load via `scripts/seed_loader.py --domain ratings` (commits `5d24e04`, `8fd4d9e`, `e5cf939`).
- `macro.run_scenario`/ScenarioService outputs include `ratings.*` metadata so patterns can display sourcing + version.

### ⚠️ Known Limitations
- Fundamentals ingest uses the new FMP transform (`fa8bcf8`), but caching + UI wiring are pending; the Streamlit surface still shows seeded snapshots.
- Ratings persistence is tied to the nightly job; ad-hoc recalculations run in-memory until the persistence gate lands.
- `buffett_checklist` outputs are available via `/v1/execute`, yet UI panels still label the experience as "Preview".

---

## Mission

Implement **Warren Buffett's quality framework** with three quantitative scores (0-10 scale): **Dividend Safety**, **Moat Strength**, and **Resilience**, using fundamental data from FMP and stored ratings rubrics from seeds.

---

## Scope & Responsibilities

### In Scope

1. **Dividend Safety Rating (0-10)**
   - Payout ratio trend (5-year lookback)
   - FCF coverage (FCF / dividends paid)
   - Dividend growth streak
   - Net cash position

2. **Moat Strength Rating (0-10)**
   - ROE consistency (5-year avg > 15%)
   - Gross margin stability
   - Intangible assets / total assets
   - Switching costs (qualitative scoring via component weights)

3. **Resilience Rating (0-10)**
   - Debt/Equity ratio
   - Interest coverage (EBIT / interest expense)
   - Current ratio (liquidity)
   - Operating margin stability

4. **Rating Persistence & Audit Trail**
   - Store ratings in `ratings` table with `pricing_pack_id`, `inputs_json`, `method_version`
   - Seed rubrics from `data/SEEDS/ratings/` (rating thresholds and component weights)

### Out of Scope

- ❌ Custom user-defined ratings (use predefined rubrics only)
- ❌ Real-time rating updates (batch nightly only)
- ❌ Sector-specific adjustments (use generic framework)

---

## Acceptance Criteria

### AC-1: Dividend Safety Rating (Golden Test)
**Given**: AAPL fundamentals as of 2024-10-20
- Payout ratio: 15.2% (5-year avg)
- FCF / dividends: 6.8x coverage
- Dividend growth streak: 12 years
- Net cash: $51B

**When**: Calculate dividend_safety rating
**Then**:
- Rating = **9.2 / 10**
- Component scores:
  - Payout ratio: 10/10 (< 50%)
  - FCF coverage: 10/10 (> 2x)
  - Growth streak: 9/10 (> 10 years)
  - Net cash: 9/10 (> $10B)
- Inputs stored in `ratings.inputs_json`

**Golden Test**: `tests/golden/ratings/dividend_safety_AAPL.json`

---

### AC-2: Moat Strength Rating (Golden Test)
**Given**: JNJ (Johnson & Johnson) fundamentals
- ROE (5-year avg): 24.3%
- Gross margin (5-year avg): 66.2%
- Intangible assets / total assets: 42%
- Brand value (qualitative): High (scored 9/10 via rubric)

**When**: Calculate moat_strength rating
**Then**:
- Rating = **9.5 / 10**
- Component scores:
  - ROE consistency: 10/10 (> 20%)
  - Gross margin: 10/10 (> 60%)
  - Intangibles: 8/10 (> 30%)
  - Switching costs: 10/10 (healthcare/pharma)

**Golden Test**: `tests/golden/ratings/moat_strength_JNJ.json`

---

### AC-3: Resilience Rating (Golden Test)
**Given**: KO (Coca-Cola) fundamentals
- Debt/Equity: 1.8x
- Interest coverage: 12.5x
- Current ratio: 1.1x
- Operating margin (5-year std dev): 0.8% (stable)

**When**: Calculate resilience rating
**Then**:
- Rating = **8.0 / 10**
- Component scores:
  - Debt/Equity: 7/10 (1.5-2.0x range)
  - Interest coverage: 10/10 (> 5x)
  - Current ratio: 8/10 (> 1.0x)
  - Margin stability: 9/10 (std dev < 2%)

**Golden Test**: `tests/golden/ratings/resilience_KO.json`

---

### AC-4: Rating Seed Data Integration
**Given**: Rubric files in `data/SEEDS/ratings/`
- `dividend_safety_v1.json` - Component weights and thresholds
- `moat_strength_v1.json` - Sector-agnostic scoring rules
- `resilience_v1.json` - Balance sheet thresholds

**When**: Load rubrics via seeding script
**Then**:
- Rubrics stored in `rating_rubrics` table
- Version tracked (`method_version = "v1"`)
- Ratings calculations reference active rubric version

**Integration Test**: `tests/integration/test_rating_rubric_seeding.py`

---

### AC-5: Batch Rating Calculation (Nightly Job)
**Given**: Portfolio P1 with AAPL, JNJ, KO holdings
**When**: Nightly rating job runs (after pricing pack build)
**Then**:
- All 3 ratings calculated for each holding
- Ratings stored with `pricing_pack_id` for reproducibility
- Overall quality score = weighted avg (dividend 0.35, moat 0.40, resilience 0.25)
- Execution time < 30s for 100 securities

**Performance Test**: `tests/performance/test_rating_batch_performance.py`

---

## Implementation Specifications

### Rating Calculator (Core Logic)

```python
# backend/app/analytics/ratings_calculator.py

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any
from app.core.types import RequestCtx, QualityRatingRequest, QualityRatingResponse, QualityScore

@dataclass(frozen=True)
class RatingRubric:
    """Rating rubric with component weights and thresholds."""
    rating_type: str  # dividend_safety, moat_strength, resilience
    method_version: str
    components: Dict[str, "ComponentRubric"]
    overall_weights: Dict[str, Decimal]  # component → weight (sums to 1.0)

@dataclass(frozen=True)
class ComponentRubric:
    """Single component scoring rules."""
    name: str
    thresholds: Dict[str, Decimal]  # e.g., {"excellent": 10, "good": 7, "poor": 3}
    metric: str  # e.g., "payout_ratio", "roe_5y_avg"

class RatingsCalculator:
    """Buffett quality ratings calculator."""

    def __init__(self):
        # Load rubrics from database (seeded from data/SEEDS/ratings/)
        self.rubrics = self._load_rubrics()

    def calculate_dividend_safety(
        self,
        ctx: RequestCtx,
        symbol: str,
        fundamentals: Dict[str, Any],
    ) -> Decimal:
        """
        Calculate dividend safety (0-10 scale).

        Inputs:
        - payout_ratio_5y_avg: Decimal
        - fcf_dividend_coverage: Decimal
        - dividend_growth_streak_years: int
        - net_cash_position: Decimal

        Returns:
        - Rating (0-10)
        """
        rubric = self.rubrics["dividend_safety"]

        # Component 1: Payout ratio
        payout_ratio = fundamentals["payout_ratio_5y_avg"]
        if payout_ratio < Decimal("0.30"):
            payout_score = Decimal("10")
        elif payout_ratio < Decimal("0.50"):
            payout_score = Decimal("7")
        elif payout_ratio < Decimal("0.70"):
            payout_score = Decimal("5")
        else:
            payout_score = Decimal("2")

        # Component 2: FCF coverage
        fcf_coverage = fundamentals["fcf_dividend_coverage"]
        if fcf_coverage > Decimal("3.0"):
            fcf_score = Decimal("10")
        elif fcf_coverage > Decimal("2.0"):
            fcf_score = Decimal("7")
        elif fcf_coverage > Decimal("1.0"):
            fcf_score = Decimal("5")
        else:
            fcf_score = Decimal("2")

        # Component 3: Growth streak
        streak = fundamentals["dividend_growth_streak_years"]
        if streak >= 20:
            streak_score = Decimal("10")
        elif streak >= 10:
            streak_score = Decimal("9")
        elif streak >= 5:
            streak_score = Decimal("7")
        else:
            streak_score = Decimal("5")

        # Component 4: Net cash position
        net_cash = fundamentals["net_cash_position"]
        if net_cash > Decimal("50_000_000_000"):  # $50B
            cash_score = Decimal("10")
        elif net_cash > Decimal("10_000_000_000"):  # $10B
            cash_score = Decimal("8")
        elif net_cash > Decimal("1_000_000_000"):  # $1B
            cash_score = Decimal("6")
        else:
            cash_score = Decimal("4")

        # Weighted average (from rubric)
        weights = rubric.overall_weights
        overall = (
            payout_score * weights["payout_ratio"] +
            fcf_score * weights["fcf_coverage"] +
            streak_score * weights["growth_streak"] +
            cash_score * weights["net_cash"]
        )

        return overall

    def calculate_moat_strength(
        self,
        ctx: RequestCtx,
        symbol: str,
        fundamentals: Dict[str, Any],
    ) -> Decimal:
        """
        Calculate moat strength (0-10 scale).

        Inputs:
        - roe_5y_avg: Decimal
        - gross_margin_5y_avg: Decimal
        - intangible_assets_ratio: Decimal
        - switching_cost_score: Decimal (qualitative, from rubric)

        Returns:
        - Rating (0-10)
        """
        rubric = self.rubrics["moat_strength"]

        # Component 1: ROE consistency
        roe = fundamentals["roe_5y_avg"]
        if roe > Decimal("0.20"):  # > 20%
            roe_score = Decimal("10")
        elif roe > Decimal("0.15"):
            roe_score = Decimal("8")
        elif roe > Decimal("0.10"):
            roe_score = Decimal("6")
        else:
            roe_score = Decimal("4")

        # Component 2: Gross margin
        gm = fundamentals["gross_margin_5y_avg"]
        if gm > Decimal("0.60"):
            gm_score = Decimal("10")
        elif gm > Decimal("0.40"):
            gm_score = Decimal("8")
        elif gm > Decimal("0.25"):
            gm_score = Decimal("6")
        else:
            gm_score = Decimal("4")

        # Component 3: Intangible assets
        intangibles = fundamentals["intangible_assets_ratio"]
        if intangibles > Decimal("0.30"):
            intang_score = Decimal("8")
        elif intangibles > Decimal("0.15"):
            intang_score = Decimal("6")
        else:
            intang_score = Decimal("4")

        # Component 4: Switching costs (qualitative, from sector/industry lookup)
        switching_cost_score = fundamentals.get("switching_cost_score", Decimal("5"))

        # Weighted average
        weights = rubric.overall_weights
        overall = (
            roe_score * weights["roe_consistency"] +
            gm_score * weights["gross_margin"] +
            intang_score * weights["intangibles"] +
            switching_cost_score * weights["switching_costs"]
        )

        return overall

    def calculate_resilience(
        self,
        ctx: RequestCtx,
        symbol: str,
        fundamentals: Dict[str, Any],
    ) -> Decimal:
        """
        Calculate resilience (0-10 scale).

        Inputs:
        - debt_equity_ratio: Decimal
        - interest_coverage: Decimal
        - current_ratio: Decimal
        - operating_margin_std_dev: Decimal (5-year)

        Returns:
        - Rating (0-10)
        """
        rubric = self.rubrics["resilience"]

        # Component 1: Debt/Equity
        de = fundamentals["debt_equity_ratio"]
        if de < Decimal("0.50"):
            de_score = Decimal("10")
        elif de < Decimal("1.00"):
            de_score = Decimal("8")
        elif de < Decimal("2.00"):
            de_score = Decimal("6")
        else:
            de_score = Decimal("3")

        # Component 2: Interest coverage
        ic = fundamentals["interest_coverage"]
        if ic > Decimal("10.0"):
            ic_score = Decimal("10")
        elif ic > Decimal("5.0"):
            ic_score = Decimal("8")
        elif ic > Decimal("2.0"):
            ic_score = Decimal("6")
        else:
            ic_score = Decimal("3")

        # Component 3: Current ratio
        cr = fundamentals["current_ratio"]
        if cr > Decimal("2.0"):
            cr_score = Decimal("10")
        elif cr > Decimal("1.5"):
            cr_score = Decimal("8")
        elif cr > Decimal("1.0"):
            cr_score = Decimal("7")
        else:
            cr_score = Decimal("4")

        # Component 4: Operating margin stability
        om_std = fundamentals["operating_margin_std_dev"]
        if om_std < Decimal("0.02"):  # < 2%
            om_score = Decimal("10")
        elif om_std < Decimal("0.05"):
            om_score = Decimal("8")
        elif om_std < Decimal("0.10"):
            om_score = Decimal("6")
        else:
            om_score = Decimal("4")

        # Weighted average
        weights = rubric.overall_weights
        overall = (
            de_score * weights["debt_equity"] +
            ic_score * weights["interest_coverage"] +
            cr_score * weights["current_ratio"] +
            om_score * weights["margin_stability"]
        )

        return overall

    async def calculate_all_ratings(
        self,
        ctx: RequestCtx,
        request: QualityRatingRequest,
    ) -> QualityRatingResponse:
        """Calculate all ratings for given symbols."""
        ratings = {}

        for symbol in request.symbols:
            # Fetch fundamentals from FMP (via PROVIDER_INTEGRATOR)
            fundamentals = await self._fetch_fundamentals(ctx, symbol)

            # Calculate all 3 ratings
            dividend_safety = self.calculate_dividend_safety(ctx, symbol, fundamentals)
            moat_strength = self.calculate_moat_strength(ctx, symbol, fundamentals)
            resilience = self.calculate_resilience(ctx, symbol, fundamentals)

            # Overall quality score (weighted average)
            overall = (
                dividend_safety * Decimal("0.35") +
                moat_strength * Decimal("0.40") +
                resilience * Decimal("0.25")
            )

            ratings[symbol] = QualityScore(
                symbol=symbol,
                dividend_safety=dividend_safety,
                moat_strength=moat_strength,
                resilience=resilience,
                overall=overall,
                supporting_metrics=fundamentals,
            )

            # Store in database
            await self._store_rating(ctx, symbol, ratings[symbol])

        return QualityRatingResponse(ratings=ratings, ctx=ctx)

    async def _fetch_fundamentals(self, ctx: RequestCtx, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental metrics from FMP provider."""
        fmp_provider = get_provider("fmp")

        # Get financial ratios
        ratios_resp = await fmp_provider.call(ProviderRequest(
            endpoint=f"/ratios/{symbol}",
            params={"limit": 5},  # 5 years
            ctx=ctx,
        ))

        # Get key metrics
        metrics_resp = await fmp_provider.call(ProviderRequest(
            endpoint=f"/key-metrics/{symbol}",
            params={"limit": 5},
            ctx=ctx,
        ))

        # Extract and calculate 5-year averages
        fundamentals = {
            "payout_ratio_5y_avg": self._calc_avg([r["payoutRatio"] for r in ratios_resp.data]),
            "fcf_dividend_coverage": metrics_resp.data[0]["freeCashFlowPerShare"] / ratios_resp.data[0]["dividendPerShare"],
            "dividend_growth_streak_years": self._calc_growth_streak(ratios_resp.data),
            "net_cash_position": metrics_resp.data[0]["netCash"],
            "roe_5y_avg": self._calc_avg([r["returnOnEquity"] for r in ratios_resp.data]),
            "gross_margin_5y_avg": self._calc_avg([r["grossProfitMargin"] for r in ratios_resp.data]),
            "intangible_assets_ratio": metrics_resp.data[0]["intangiblesRatio"],
            "debt_equity_ratio": ratios_resp.data[0]["debtEquityRatio"],
            "interest_coverage": ratios_resp.data[0]["interestCoverage"],
            "current_ratio": ratios_resp.data[0]["currentRatio"],
            "operating_margin_std_dev": self._calc_std_dev([r["operatingProfitMargin"] for r in ratios_resp.data]),
        }

        return fundamentals

    async def _store_rating(self, ctx: RequestCtx, symbol: str, quality_score: QualityScore):
        """Store rating in database with reproducibility metadata."""
        await db.execute("""
            INSERT INTO ratings (
                security_id, rating_type, value, inputs_json, method_version,
                pricing_pack_id, ledger_commit_hash, created_at
            )
            VALUES (
                (SELECT id FROM securities WHERE symbol = :symbol),
                'overall_quality', :overall, :inputs_json, :method_version,
                :pricing_pack_id, :ledger_commit_hash, NOW()
            )
            ON CONFLICT (security_id, rating_type, pricing_pack_id)
            DO UPDATE SET value = EXCLUDED.value, inputs_json = EXCLUDED.inputs_json
        """, {
            "symbol": symbol,
            "overall": quality_score.overall,
            "inputs_json": json.dumps(quality_score.supporting_metrics),
            "method_version": "buffett_v1",
            "pricing_pack_id": ctx.pricing_pack_id,
            "ledger_commit_hash": ctx.ledger_commit_hash,
        })
```

---

## Seed Data Integration

### Rating Rubrics (from DawsOS_Seeding_Plan)

**`data/SEEDS/ratings/rating_schema.json`**
```json
{
  "schema_version": "1.0",
  "factors": {
    "dividend_safety": {"min": 0, "max": 10},
    "moat_strength": {"min": 0, "max": 10},
    "resilience": {"min": 0, "max": 10}
  }
}
```

**`data/SEEDS/ratings/dividend_safety_v1.json`**
```json
{
  "method_version": "buffett_v1",
  "rating_type": "dividend_safety",
  "components": {
    "payout_ratio": {
      "metric": "payout_ratio_5y_avg",
      "thresholds": {"excellent": 0.30, "good": 0.50, "acceptable": 0.70}
    },
    "fcf_coverage": {
      "metric": "fcf_dividend_coverage",
      "thresholds": {"excellent": 3.0, "good": 2.0, "acceptable": 1.0}
    },
    "growth_streak": {
      "metric": "dividend_growth_streak_years",
      "thresholds": {"excellent": 20, "good": 10, "acceptable": 5}
    },
    "net_cash": {
      "metric": "net_cash_position",
      "thresholds": {"excellent": 50000000000, "good": 10000000000, "acceptable": 1000000000}
    }
  },
  "overall_weights": {
    "payout_ratio": 0.30,
    "fcf_coverage": 0.35,
    "growth_streak": 0.20,
    "net_cash": 0.15
  }
}
```

**Load via seeding script:**
```bash
make seed:ratings
# Runs: python scripts/seed_load.py rating_rubrics data/SEEDS/ratings/*.json
```

---

## Nightly Job Integration

```python
# jobs/nightly.py

@sched.scheduled_job("cron", hour=0, minute=5)
def nightly():
    """
    SACRED ORDER:
    1. build_pack
    2. reconcile_ledger
    3. compute_daily_metrics
    4. prewarm_factors
    5. ** prewarm_ratings **  ← NEW
    6. mark_pack_fresh
    7. evaluate_alerts
    """
    pack = build_pack()
    reconcile_ledger(pack)
    compute_daily_metrics(pack)
    prewarm_factors(pack)
    prewarm_ratings(pack)  # Calculate ratings for all portfolio holdings
    mark_pack_fresh(pack)
    evaluate_alerts()

def prewarm_ratings(pack: PricingPack):
    """Calculate ratings for all securities in active portfolios."""
    ctx = RequestCtx(
        pricing_pack_id=pack.id,
        ledger_commit_hash=get_ledger_commit_hash(),
        trace_id=generate_trace_id(),
        user_id=UUID("00000000-0000-0000-0000-000000000000"),  # System user
        request_id=generate_request_id(),
    )

    # Get all unique securities across portfolios
    securities = db.query("SELECT DISTINCT symbol FROM portfolio_holdings")

    request = QualityRatingRequest(symbols=[s["symbol"] for s in securities])
    ratings_calculator = RatingsCalculator()
    await ratings_calculator.calculate_all_ratings(ctx, request)
```

---

## Golden Tests

**`tests/golden/ratings/dividend_safety_AAPL.json`**
```json
{
  "symbol": "AAPL",
  "fundamentals": {
    "payout_ratio_5y_avg": 0.152,
    "fcf_dividend_coverage": 6.8,
    "dividend_growth_streak_years": 12,
    "net_cash_position": 51000000000
  },
  "expected_rating": 9.2,
  "expected_components": {
    "payout_ratio": 10.0,
    "fcf_coverage": 10.0,
    "growth_streak": 9.0,
    "net_cash": 9.0
  }
}
```

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/unit/ratings/ -k "dividend_safety or moat_strength or resilience"
```

**Coverage**:
- Component scoring logic (thresholds, edge cases)
- Weighted average calculation
- Rubric loading and version tracking

---

### Golden Tests
```bash
pytest tests/golden/ratings/ --golden-update=never
```

**Scenarios**:
- AAPL (dividend safety: 9.2, moat: 8.5, resilience: 7.0)
- JNJ (dividend safety: 8.5, moat: 9.5, resilience: 8.0)
- KO (dividend safety: 8.0, moat: 9.0, resilience: 8.0)

---

### Integration Tests
```bash
pytest tests/integration/test_ratings_integration.py
```

**Flows**:
1. Seed rating rubrics → load into database
2. Fetch FMP fundamentals → calculate ratings
3. Store ratings with pricing_pack_id → verify reproducibility

---

## Observability

### Prometheus Metrics
```python
rating_calculations_total = Counter(
    "rating_calculations_total",
    "Total rating calculations",
    ["rating_type", "symbol"]
)

rating_calculation_duration_seconds = Histogram(
    "rating_calculation_duration_seconds",
    "Rating calculation duration",
    ["rating_type"]
)
```

---

## Handoff to Downstream Agents

### Inputs Required
- Fundamental data (FMP via PROVIDER_INTEGRATOR)
- Rating rubrics (seeded from `data/SEEDS/ratings/`)
- Pricing pack (for reproducibility)

### Outputs Consumed By
- **OPTIMIZER_ARCHITECT** — Use ratings as constraints (e.g., min quality score = 6.0)
- **UI_ARCHITECT** — Display rating badges, component breakdowns
- **REPORTING_ARCHITECT** — Include ratings in PDF reports
- **Alert system** — Trigger alerts on rating downgrades

---

## Related Documents

- **[PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)** — Section 4: Buffett Checklist
- **[DawsOS_Seeding_Plan](../../DawsOS_Seeding_Plan)** — Section 3.6: Ratings & Optimizer
- **[PROVIDER_INTEGRATOR.md](../integration/PROVIDER_INTEGRATOR.md)** — FMP fundamentals
- **[types.py](../../../backend/app/core/types.py)** — QualityRatingRequest/Response, QualityScore

---

**Last Updated**: 2025-10-21
**Agent Owner**: Business Logic Team
**Review Cycle**: Quarterly (rubric validation)
