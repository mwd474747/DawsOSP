# Pricing Pack Infrastructure Guide

**Updated**: 2025-10-23
**Status**: Phase 2 Complete
**Priority**: P0 (Critical for reproducibility)

---

## Overview

The **Pricing Pack** is DawsOS's core mechanism for reproducible portfolio valuation. Every metric, valuation, and analysis references a `pricing_pack_id` to ensure identical results when recomputed.

### Sacred Invariants

1. **Immutability**: Pricing packs are frozen snapshots. Once created, they never change.
2. **Reproducibility**: Same `pricing_pack_id` + `ledger_commit_hash` = identical results.
3. **Freshness Gate**: Executor blocks requests until `is_fresh=true`.
4. **Daily Build**: Packs built nightly at 00:05 via scheduler.

---

## Architecture

### Pack Lifecycle

```
1. warming    → Pack being built (fetch prices, FX rates)
2. warming    → Reconciliation running (validate vs Beancount ±1bp)
3. warming    → Pre-warm running (factors, ratings, metrics)
4. fresh      → Pack ready for use (executor enabled)
5. superseded → New pack created (restatement due to late corporate action)
```

### Database Schema

#### Tables

1. **pricing_packs**: Pack metadata (id, date, policy, status, hash)
2. **securities**: Master security table (symbol, currency, exchange)
3. **prices**: Daily security prices (close, OHLC, source)
4. **fx_rates**: Foreign exchange rates (base/quote, rate, policy)

#### Pack ID Format

```
PP_YYYY-MM-DD
```

Examples:
- `PP_2025-10-21` (October 21, 2025 pack)
- `PP_2025-10-22` (October 22, 2025 pack)

#### Pack Hash

SHA-256 hash of all prices and FX rates for integrity verification.

---

## Nightly Job Order (Sacred)

These jobs MUST run in this exact order (non-negotiable):

```python
# 1. build_pack → Create immutable pricing snapshot
pack_id = await build_pack(asof_date=yesterday, policy="WM4PM_CAD")

# 2. reconcile_ledger → Validate vs Beancount ±1bp (BLOCKS if fails)
await reconcile_ledger(pack_id, ledger_path)

# 3. compute_daily_metrics → TWR, MWR, vol, Sharpe, alpha, beta
await compute_daily_metrics(pack_id)

# 4. prewarm_factors → Factor fits, rolling stats
await prewarm_factors(pack_id)

# 5. prewarm_ratings → Buffett quality scores
await prewarm_ratings(pack_id)

# 6. mark_pack_fresh → Enable executor freshness gate
await mark_pack_fresh(pack_id)

# 7. evaluate_alerts → Check conditions, dedupe, deliver
await evaluate_alerts(pack_id)
```

**Critical**: If reconciliation fails (error > 1bp), all subsequent jobs are BLOCKED.

---

## Usage

### 1. Building Packs (Development)

Preferred (seeded data):

```bash
python scripts/seed_loader.py --all
# seeds symbols, portfolios, pricing pack (PP_2025-10-21), macro, cycles
```

Optional stub (legacy testing only):

```bash
python backend/jobs/build_pack_stub.py --date 2025-10-21 --mark-fresh
```

### 2. Querying Prices

```python
from backend.app.services.pricing import get_pricing_service

pricing = get_pricing_service()

# Get latest fresh pack
pack = await pricing.get_latest_pack(require_fresh=True)

# Get price for a security
price = await pricing.get_price(
    security_id="11111111-1111-1111-1111-111111111111",  # AAPL
    pack_id=pack.id
)

# price.close = Decimal("185.23")
# price.currency = "USD"
# price.source = "seed"
```

### 3. Querying FX Rates

```python
# Get FX rate (USD to CAD)
fx_rate = await pricing.get_fx_rate(
    base_ccy="USD",
    quote_ccy="CAD",
    pack_id=pack.id
)

# fx_rate.rate = Decimal("1.3625") = 1.3625 CAD per 1 USD
```

### 4. Currency Conversion

```python
# Convert $100 USD to CAD
cad_amount = await pricing.convert_currency(
    amount=Decimal("100.00"),
    from_ccy="USD",
    to_ccy="CAD",
    pack_id=pack.id
)

# cad_amount = Decimal("136.25")
```

### 5. Health Check

```bash
# Check pack health status
curl http://localhost:8001/health/pack
```

Response:

```json
{
  "status": "fresh",
  "pack_id": "PP_2025-10-21",
  "asof_date": "2025-10-21",
  "is_fresh": true,
  "prewarm_done": true,
  "reconciliation_passed": true,
  "updated_at": "2025-10-22T00:18:00Z",
  "error_message": null,
  "estimated_ready": null
}
```

---

## Stub Data (Development)

### Securities (10)

| Symbol  | Name                          | Currency | Exchange | Type   |
|---------|-------------------------------|----------|----------|--------|
| AAPL    | Apple Inc.                    | USD      | NASDAQ   | equity |
| RY.TO   | Royal Bank of Canada          | CAD      | TSX      | equity |
| XIU.TO  | iShares S&P/TSX 60 Index ETF  | CAD      | TSX      | etf    |
| VFV.TO  | Vanguard S&P 500 Index ETF    | CAD      | TSX      | etf    |
| MSFT    | Microsoft Corporation         | USD      | NASDAQ   | equity |
| GOOGL   | Alphabet Inc.                 | USD      | NASDAQ   | equity |
| TD.TO   | Toronto-Dominion Bank         | CAD      | TSX      | equity |
| XIC.TO  | iShares Core S&P/TSX Cap Comp | CAD      | TSX      | etf    |
| AMZN    | Amazon.com Inc.               | USD      | NASDAQ   | equity |
| ENB.TO  | Enbridge Inc.                 | CAD      | TSX      | equity |

### Stub Prices

```python
STUB_PRICES = {
    "AAPL": 185.23,
    "RY.TO": 142.56,
    "XIU.TO": 37.82,
    "VFV.TO": 115.34,
    "MSFT": 412.67,
    "GOOGL": 168.92,
    "TD.TO": 78.45,
    "XIC.TO": 35.21,
    "AMZN": 178.34,
    "ENB.TO": 51.23,
}
```

### Stub FX Rates

```python
STUB_FX_RATES = [
    {"base": "USD", "quote": "CAD", "rate": 1.3625},  # 1 USD = 1.3625 CAD
    {"base": "EUR", "quote": "CAD", "rate": 1.4823},
    {"base": "GBP", "quote": "CAD", "rate": 1.7245},
    {"base": "CAD", "quote": "USD", "rate": 0.7339},  # 1 CAD = 0.7339 USD
    {"base": "JPY", "quote": "CAD", "rate": 0.0091},
]
```

---

## Multi-Currency Rules

### Valuation

```
P_base = P_local × FX(local→base)
```

Example: AAPL price in CAD base:

```python
AAPL_usd = 185.23  # USD
FX_usd_cad = 1.3625  # USD/CAD rate
AAPL_cad = 185.23 * 1.3625 = 252.38 CAD
```

### Returns Decomposition

```
r_base = (1 + r_local) × (1 + r_fx) - 1
       = r_local + r_fx + (r_local × r_fx)
```

Components stored in `currency_attribution` table:
- `local_return`: Return from price changes in local currency
- `fx_return`: Return from currency movements
- `interaction_return`: Cross-term (r_local × r_fx)

### ADR Dividends (Pay-Date FX)

For ADR dividends, use **pay-date FX rate** (NOT ex-date):

```sql
-- Example: AAPL dividend
-- Ex-date: 2025-08-01, FX = 1.34 USD/CAD
-- Pay-date: 2025-08-15, FX = 1.36 USD/CAD
-- Correct: Use 1.36 (pay-date rate)

UPDATE transactions
SET pay_fx_rate_id = (
    SELECT id FROM fx_rates
    WHERE base_ccy = 'USD' AND quote_ccy = 'CAD'
      AND asof_ts::date = pay_date
)
WHERE transaction_type = 'DIVIDEND' AND symbol = 'AAPL';
```

---

## Pack Supersession (Restatements)

When a late corporate action is discovered (e.g., retroactive stock split):

1. **Create new pack** with adjusted prices
2. **Mark old pack** as superseded: `old_pack.superseded_by = new_pack_id`
3. **Show banner** in UI: "Data restated due to {reason}"
4. **NO SILENT MUTATIONS**: Explicit provenance chain

Example:

```python
# Discover late stock split for AAPL (2-for-1 on 2025-09-15)
new_pack_id = await builder.build_pack(
    asof_date=date(2025, 9, 15),
    policy="WM4PM_CAD",
    restatement_reason="AAPL 2-for-1 stock split"
)

# Old pack marked as superseded
# old_pack.superseded_by = new_pack_id
# UI shows: "Data restated due to AAPL 2-for-1 stock split"
```

---

## Executor Freshness Gate

The executor MUST check pack freshness before executing patterns:

```python
from backend.app.services.pricing import get_pricing_service

@app.post("/v1/execute")
async def execute(req: ExecReq):
    pricing = get_pricing_service()
    pack = await pricing.get_latest_pack(require_fresh=True)

    if not pack:
        raise HTTPException(
            status_code=503,
            detail="Pricing pack not fresh. Data warming, try again in 10 minutes."
        )

    # Continue with execution...
    return await run_pattern(req.pattern_id, pack.id, req.inputs)
```

---

## SLOs

### Performance

- **Pack build completes by 00:15** (10 min deadline)
- **Warm p95 < 1.2s** (pre-warmed pack, cached factors)
- **Cold p95 < 2.0s** (pack warming in progress)

### Accuracy

- **Ledger reconciliation: ±1bp** (100% of portfolios)
- **Currency attribution identity**: `r_base ≈ (1+r_local)(1+r_fx)-1 ±0.1bp`

### Reliability

- **Uptime: 99.5%** (excludes planned maintenance)
- **Alert median latency < 60s** (trigger to delivery)

---

## Provider Integration (Future)

Once providers are integrated, replace stub data with real data:

### Polygon (Prices)

```python
# Fetch split-adjusted daily prices
daily_prices = await polygon.get_daily_prices(
    symbol="AAPL",
    start_date=asof_date,
    end_date=asof_date,
    adjusted=True,  # Split-adjusted (NOT dividend-adjusted)
)
```

### FMP (Fundamentals + Fallback Prices)

```python
# Fetch quote as fallback if Polygon unavailable
fmp_quote = await fmp.get_quote(["AAPL"])
```

### FRED (FX Rates)

```python
# Fetch WM/Reuters 4PM fixing for USD/CAD
fred_data = await fred.get_series(
    series_id="DEXCAUS",  # CAD/USD rate
    start_date=asof_date,
    end_date=asof_date,
)
```

---

## Testing

### Unit Tests

```bash
# Test pricing service
pytest backend/tests/test_pricing_service.py

# Test pack builder
pytest backend/tests/test_pack_builder.py
```

### Integration Tests

```bash
# Build stub pack and verify
python backend/jobs/build_pack_stub.py --date 2025-10-21 --mark-fresh

# Query prices
python -c "
import asyncio
from backend.app.services.pricing import get_pricing_service

async def test():
    pricing = get_pricing_service()
    pack = await pricing.get_latest_pack()
    print(f'Pack: {pack.id}, fresh={pack.is_fresh}')

asyncio.run(test())
"
```

### Golden Tests

```bash
# Test pack hash reproducibility
python backend/tests/golden/test_pack_hash.py

# Test currency attribution identity
python backend/tests/golden/test_currency_attribution.py

# Test ADR pay-date FX accuracy
python backend/tests/golden/test_adr_paydate_fx.py
```

---

## Troubleshooting

### Pack Not Fresh

**Symptom**: `/health/pack` returns `is_fresh=false`

**Cause**: Nightly job not completed or pre-warm still running

**Solution**:
1. Check nightly job logs: `tail -f logs/nightly_jobs.log`
2. Wait for pre-warm to complete (usually < 15 min)
3. Manual mark fresh (if needed): `python backend/jobs/mark_pack_fresh.py PP_2025-10-21`

### Reconciliation Failed

**Symptom**: Pack status = `error`, reconciliation_failed = true

**Cause**: DB valuations differ from Beancount ledger by > 1bp

**Solution**:
1. Check reconciliation report: `cat logs/reconciliation_2025-10-21.log`
2. Identify discrepancies (position qty, cost basis, or valuation)
3. Fix source data (ledger or DB transactions)
4. Rebuild pack: `python backend/jobs/build_pack_stub.py --date 2025-10-21`

### Missing Prices

**Symptom**: `get_price()` returns None

**Cause**: Security not in stub data or provider fetch failed

**Solution**:
1. Check if security exists: `SELECT * FROM securities WHERE symbol = 'XYZ'`
2. Add to stub data if needed
3. Rebuild pack

### FX Rate Not Found

**Symptom**: `get_fx_rate()` returns None

**Cause**: Currency pair not in pack or inverse rate needed

**Solution**:
1. Check available rates: `SELECT * FROM fx_rates WHERE pricing_pack_id = 'PP_2025-10-21'`
2. Use `convert_currency()` which handles inverse rates automatically

---

## Files

### Schema

- **backend/db/schema/pricing_packs.sql**: Complete schema (pricing_packs, securities, prices, fx_rates)

### Services

- **backend/app/services/pricing.py**: Pricing service (queries, conversions)
- **backend/app/db/pricing_pack_queries.py**: Low-level database queries

### Jobs

- **backend/jobs/pricing_pack.py**: Pack builder (production, with providers)
- **backend/jobs/build_pack_stub.py**: Pack builder (stub data for testing)
- **backend/jobs/scheduler.py**: Nightly job orchestrator

### API

- **backend/app/api/health.py**: Health check endpoints (`/health/pack`)
- **backend/app/api/executor.py**: Executor with freshness gate

---

## Next Steps

1. **Provider Integration**: Replace stub data with Polygon/FMP/FRED
2. **Reconciliation**: Implement Beancount ledger comparison
3. **Pre-warm Jobs**: Implement factor/rating computation
4. **Scheduler**: Wire up nightly job scheduler (APScheduler)
5. **Golden Tests**: Create test fixtures for pack hash, currency attribution, ADR dividends

---

## References

- **PRODUCT_SPEC.md**: §2 (Data model), §8 (Nightly jobs)
- **CLAUDE.md**: Current state verification
- **.ops/TASK_INVENTORY_2025-10-24.md**: Open gaps and fixes

---

**Version**: 1.0
**Last Updated**: 2025-10-23
**Status**: Complete (Phase 2)
