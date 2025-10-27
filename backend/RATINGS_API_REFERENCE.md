# Ratings Service API Reference

Quick reference for using the DawsOS Ratings Service

---

## Import

```python
from backend.app.services.ratings import get_ratings_service
from decimal import Decimal
from uuid import UUID
```

---

## Initialize Service

```python
service = get_ratings_service()  # Singleton - safe to call multiple times
```

---

## Method 1: Dividend Safety

Calculate dividend sustainability rating (0-100 scale with A-F grade)

```python
result = await service.calculate_dividend_safety(
    symbol="JNJ",
    fundamentals={
        "payout_ratio_5y_avg": Decimal("0.45"),        # 45% payout
        "fcf_dividend_coverage": Decimal("2.8"),        # 2.8x coverage
        "dividend_growth_streak_years": 25,             # 25 years
        "net_cash_position": Decimal("15000000000"),    # $15B
    },
    security_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")  # Optional
)

# Returns:
{
  "overall": Decimal("7.75"),           # 0-10 scale
  "rating_100": Decimal("77.5"),        # 0-100 scale
  "grade": "C",                         # A-F grade
  "rating_type": "dividend_safety",
  "symbol": "JNJ",
  "security_id": "aaaaaaaa-...",
  "_metadata": {
    "weights_source": "rubric",         # or "fallback"
    "method_version": "v1"
  },
  "components": {
    "payout_ratio": {
      "score": Decimal("7.0"),
      "value": Decimal("0.45"),
      "weight": Decimal("0.30"),
      "label": "Payout Ratio (5Y Avg)"
    },
    // ... 3 more components
  }
}
```

---

## Method 2: Moat Strength

Calculate economic moat (competitive advantage) rating (0-100 scale)

```python
result = await service.calculate_moat_strength(
    symbol="AAPL",
    fundamentals={
        "roe_5y_avg": Decimal("0.28"),              # 28% ROE
        "gross_margin_5y_avg": Decimal("0.65"),     # 65% margin
        "intangible_assets_ratio": Decimal("0.35"), # 35% intangibles
        "switching_cost_score": Decimal("9"),       # 0-10 qualitative
    },
    security_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
)

# Returns: Same structure as dividend_safety, with moat-specific components
```

---

## Method 3: Resilience

Calculate financial resilience rating (0-100 scale)

```python
result = await service.calculate_resilience(
    symbol="PG",
    fundamentals={
        "debt_equity_ratio": Decimal("0.45"),           # 0.45x leverage
        "interest_coverage": Decimal("15.0"),           # 15x coverage
        "current_ratio": Decimal("2.2"),                # 2.2x liquidity
        "operating_margin_std_dev": Decimal("0.015"),   # 1.5% volatility
    },
    security_id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
)

# Returns: Same structure, with resilience-specific components
```

---

## Method 4: Aggregate Rating

Calculate overall quality rating combining all three dimensions

```python
result = await service.aggregate(
    symbol="JNJ",
    fundamentals={
        # All fields from methods 1-3 combined
        "payout_ratio_5y_avg": Decimal("0.45"),
        "fcf_dividend_coverage": Decimal("2.8"),
        "dividend_growth_streak_years": 25,
        "net_cash_position": Decimal("15000000000"),

        "roe_5y_avg": Decimal("0.28"),
        "gross_margin_5y_avg": Decimal("0.65"),
        "intangible_assets_ratio": Decimal("0.35"),
        "switching_cost_score": Decimal("9"),

        "debt_equity_ratio": Decimal("0.45"),
        "interest_coverage": Decimal("15.0"),
        "current_ratio": Decimal("2.2"),
        "operating_margin_std_dev": Decimal("0.015"),
    },
    security_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
)

# Returns:
{
  "overall_rating": Decimal("91.38"),   # 0-100 scale
  "overall_grade": "A",                 # A-F grade
  "symbol": "JNJ",
  "security_id": "aaaaaaaa-...",
  "aggregation_weights": {
    "moat_strength": Decimal("0.40"),   # 40% weight
    "resilience": Decimal("0.35"),      # 35% weight
    "dividend_safety": Decimal("0.25")  # 25% weight
  },
  "moat": {
    "overall": Decimal("9.25"),
    "rating_100": Decimal("92.5"),
    "grade": "A",
    "components": { ... }
  },
  "resilience": { ... },
  "dividend": { ... }
}
```

---

## Grading Scale

| Grade | Range   | Interpretation |
|-------|---------|----------------|
| **A** | 90-100  | Exceptional quality - Buffett's "wonderful company" |
| **B** | 80-89   | Strong quality - Buffett's "good company" |
| **C** | 70-79   | Acceptable quality - requires fair price |
| **D** | 60-69   | Below average - avoid unless deeply discounted |
| **F** | <60     | Poor quality - stay away |

---

## Component Weights

### Dividend Safety (25% of overall)

| Component | Weight | Threshold |
|-----------|--------|-----------|
| FCF Coverage | 35% | >3.0=10, >2.0=7, >1.0=5, ≤1.0=2 |
| Payout Ratio | 30% | <30%=10, <50%=7, <70%=5, ≥70%=2 |
| Growth Streak | 20% | ≥20yr=10, ≥10yr=9, ≥5yr=7, <5yr=5 |
| Net Cash | 15% | >$50B=10, >$10B=8, >$1B=6, ≤$1B=4 |

### Moat Strength (40% of overall)

| Component | Weight | Threshold |
|-----------|--------|-----------|
| ROE Consistency | 40% | >20%=10, >15%=8, >10%=6, ≤10%=4 |
| Gross Margin | 30% | >60%=10, >40%=8, >25%=6, ≤25%=4 |
| Intangibles | 20% | >30%=8, >15%=6, ≤15%=4 |
| Switching Costs | 10% | Qualitative 0-10 (sector-based) |

### Resilience (35% of overall)

| Component | Weight | Threshold |
|-----------|--------|-----------|
| Debt/Equity | 40% | <0.5=10, <1.0=8, <2.0=6, ≥2.0=3 |
| Current Ratio | 25% | >2.0=10, >1.5=8, >1.0=7, ≤1.0=4 |
| Interest Coverage | 20% | >10x=10, >5x=8, >2x=6, ≤2x=3 |
| Margin Stability | 15% | <2%=10, <5%=8, <10%=6, ≥10%=4 |

---

## Error Handling

Service uses graceful degradation:

```python
# If database unavailable, uses fallback equal weights
# Logs warning but continues execution
logger.warning("Rubric not found for dividend_safety, using fallback equal weights")

# Returns result with metadata indicating fallback used
"_metadata": {
    "weights_source": "fallback"  # Instead of "rubric"
}
```

---

## Testing

Run comprehensive test suite:

```bash
PYTHONPATH=/path/to/DawsOSP python3 backend/test_ratings_complete.py
```

Expected output: 3 test cases (A-grade, D-grade, F-grade companies)

---

## Database Setup

Seed rubrics with research-based weights:

```bash
psql -U dawsos_app -d dawsos -f backend/db/seeds/001_rating_rubrics.sql
```

Verify seeding:

```sql
SELECT rating_type, method_version, description
FROM rating_rubrics
WHERE method_version = 'v1';
```

---

## Integration Example

Full workflow from security lookup to rating:

```python
from backend.app.services.ratings import get_ratings_service
from backend.app.agents.data_harvester import DataHarvester
from backend.app.core.types import RequestCtx
from uuid import UUID
from datetime import date

async def rate_security(symbol: str) -> dict:
    """Rate a security using fundamentals from FMP."""

    # 1. Create context
    ctx = RequestCtx(
        portfolio_id=UUID("00000000-0000-0000-0000-000000000000"),
        pricing_pack_id="PP_2025-10-26",
        asof_date=date.today()
    )

    # 2. Fetch fundamentals via Data Harvester
    harvester = DataHarvester("data_harvester", {})
    state = {}

    fundamentals_result = await harvester.provider_fetch_fundamentals(
        ctx, state, symbol=symbol
    )

    # 3. Calculate rating
    ratings_service = get_ratings_service()
    rating = await ratings_service.aggregate(
        symbol=symbol,
        fundamentals=fundamentals_result,
        security_id=None  # Or lookup from securities table
    )

    return rating

# Usage
rating = await rate_security("AAPL")
print(f"Overall Rating: {rating['overall_rating']}/100 (Grade: {rating['overall_grade']})")
```

---

## Performance Notes

- **Caching**: Rubrics are cached after first load (singleton pattern)
- **Database Queries**: 1 query on first call, then cached
- **Fallback**: Zero database queries if fallback weights used
- **Execution Time**: <10ms per rating (cached rubrics)

---

## Future Enhancements

1. **Database Persistence**: Store ratings in `ratings` table
2. **Historical Tracking**: Track rating changes over time
3. **Sector Adjustments**: Industry-specific thresholds
4. **Qualitative Scores**: Management quality, governance
5. **Peer Rankings**: Percentile within sector

---

**Version**: v1
**Last Updated**: October 26, 2025
**Maintained By**: DawsOS Team
