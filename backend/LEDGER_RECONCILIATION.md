# Beancount Ledger Reconciliation - DawsOS

**Status**: Implemented (Phase 1 - Truth Spine Complete)
**Updated**: 2025-10-23
**Owner**: Backend Team

---

## Executive Summary

DawsOS implements the **"Ledger as Truth"** principle: the Beancount ledger stored in Git is the immutable source of truth for all portfolio transactions. The database is a derivative view that **must reconcile to ±1 basis point** nightly.

This document describes the ledger format, reconciliation process, and acceptance criteria.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Ledger Format](#ledger-format)
3. [Database Schema](#database-schema)
4. [Reconciliation Process](#reconciliation-process)
5. [NAV Computation](#nav-computation)
6. [Multi-Currency Handling](#multi-currency-handling)
7. [ADR Pay-Date FX](#adr-pay-date-fx)
8. [Acceptance Criteria](#acceptance-criteria)
9. [Operational Procedures](#operational-procedures)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Truth Spine Principle

```
┌─────────────────────────────────────────────────────┐
│           BEANCOUNT LEDGER (Git)                    │
│         ✓ Immutable Source of Truth                 │
│         ✓ Auditable (git history)                   │
│         ✓ Versioned (commit hash)                   │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Nightly Parse
                  ▼
┌─────────────────────────────────────────────────────┐
│         LEDGER SNAPSHOTS (Database)                 │
│         - Parsed postings                           │
│         - Indexed for queries                       │
│         - Linked to commit hash                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Compare
                  ▼
┌─────────────────────────────────────────────────────┐
│         PORTFOLIO TRANSACTIONS (Database)           │
│         - User-entered or imported                  │
│         - Derivative view                           │
│         - Must reconcile to ledger ±1bp             │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Reconciliation Job
                  ▼
┌─────────────────────────────────────────────────────┐
│         RECONCILIATION RESULTS                      │
│         Status: pass (≤1bp) | fail (>1bp)           │
│         Alert: if fail                              │
└─────────────────────────────────────────────────────┘
```

### Data Flow

1. **Nightly 00:05**: Parse Beancount ledger from Git
2. **Nightly 00:10**: Reconcile ledger NAV vs DB NAV
3. **Nightly 00:15**: Alert if reconciliation fails

---

## Ledger Format

### Account Structure

DawsOS uses the following Beancount account hierarchy:

```
Assets:Portfolio:<portfolio_uuid>:<symbol>   # Holdings
Assets:Portfolio:<portfolio_uuid>:Cash       # Cash positions
Income:Dividends:<symbol>                    # Dividend income
Expenses:Fees                                # Portfolio fees
Equity:Opening-Balances                      # Initial capital
```

### Example Transaction (Buy)

```beancount
2024-01-15 * "Buy 100 shares AAPL @ $150.00 USD"
  Assets:Portfolio:11111111-1111-1111-1111-111111111111:AAPL    100 AAPL {150.00 USD}
  Assets:Portfolio:11111111-1111-1111-1111-111111111111:Cash  -20100.00 CAD
    ; Trade FX rate: 1.34 USD/CAD
    ; Cost: 100 * 150.00 * 1.34 = 20,100 CAD
```

### Example Transaction (Dividend with Pay-Date FX)

```beancount
2024-08-15 * "AAPL dividend payment - 100 shares @ $0.24 USD" #dividend
  Income:Dividends:AAPL                                          -24.00 USD
  Assets:Portfolio:11111111-1111-1111-1111-111111111111:Cash     32.64 CAD
    ; Pay-date FX: 1.36 USD/CAD (CRITICAL: must use pay-date FX, not ex-date)
  pay_date: "2024-08-15"
  ex_date: "2024-08-01"
  pay_fx_rate: 1.36
```

### Example Transaction (Sell)

```beancount
2024-10-01 * "Sell 50 shares AAPL @ $180.00 USD"
  Assets:Portfolio:11111111-1111-1111-1111-111111111111:AAPL    -50 AAPL {150.00 USD}
  Assets:Portfolio:11111111-1111-1111-1111-111111111111:Cash  12240.00 CAD
    ; Sell FX rate: 1.36 USD/CAD
    ; Proceeds: 50 * 180.00 * 1.36 = 12,240 CAD
    ; Capital gain: 12,240 - 10,050 = 2,190 CAD (realized)
```

### Balance Assertions

```beancount
2024-10-31 balance Assets:Portfolio:11111111-1111-1111-1111-111111111111:Cash  54264.68 CAD
2024-10-31 balance Assets:Portfolio:11111111-1111-1111-1111-111111111111:AAPL      50 AAPL
```

Balance assertions validate ledger integrity and help catch errors early.

---

## Database Schema

### Tables

#### `ledger_snapshots`
Stores metadata about parsed ledger snapshots.

```sql
CREATE TABLE ledger_snapshots (
    id UUID PRIMARY KEY,
    commit_hash TEXT NOT NULL UNIQUE,
    repository_url TEXT,
    parsed_at TIMESTAMPTZ NOT NULL,
    transaction_count INT NOT NULL,
    account_count INT NOT NULL,
    earliest_date DATE,
    latest_date DATE,
    file_hash TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'parsing', 'parsed', 'failed', 'superseded'
    superseded_by UUID REFERENCES ledger_snapshots(id)
);
```

#### `ledger_transactions`
Stores individual postings from the ledger (expanded to rows).

```sql
CREATE TABLE ledger_transactions (
    id UUID PRIMARY KEY,
    ledger_snapshot_id UUID NOT NULL REFERENCES ledger_snapshots(id),
    transaction_date DATE NOT NULL,
    transaction_index INT NOT NULL,
    narration TEXT,
    payee TEXT,
    tags TEXT[],
    account TEXT NOT NULL,
    commodity TEXT,
    quantity NUMERIC,
    price NUMERIC,
    price_commodity TEXT,
    cost NUMERIC,
    cost_commodity TEXT,
    metadata JSONB,
    transaction_type TEXT
);
```

#### `reconciliation_results`
Stores nightly reconciliation results with full provenance.

```sql
CREATE TABLE reconciliation_results (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),
    asof_date DATE NOT NULL,
    ledger_commit_hash TEXT NOT NULL,
    ledger_snapshot_id UUID NOT NULL REFERENCES ledger_snapshots(id),
    pricing_pack_id TEXT NOT NULL,
    ledger_nav NUMERIC NOT NULL,
    db_nav NUMERIC NOT NULL,
    difference NUMERIC NOT NULL,
    error_bp NUMERIC NOT NULL,  -- Error in basis points
    status TEXT NOT NULL,  -- 'pass', 'fail', 'warning'
    tolerance_bp NUMERIC NOT NULL DEFAULT 1.0,
    reconciled_at TIMESTAMPTZ NOT NULL,
    UNIQUE (portfolio_id, asof_date, ledger_commit_hash, pricing_pack_id)
);
```

---

## Reconciliation Process

### Nightly Job Flow

```python
# backend/jobs/reconcile_ledger.py

@scheduler.scheduled_job("cron", hour=0, minute=10)
async def reconcile_all_portfolios():
    """
    Nightly reconciliation job.

    Runs after pricing pack build (00:05) completes.
    """
    service = ReconciliationService()
    results = await service.reconcile_all_portfolios(as_of_date=date.today())

    # Alert on failures
    for result in results:
        if not result.passed:
            send_alert(f"Reconciliation FAILED for {result.portfolio_id}: {result.error_bps:.2f}bp")
```

### Reconciliation Steps

1. **Parse Ledger**: Extract postings from Beancount ledger at latest commit
2. **Compute Ledger NAV**: Sum holdings from ledger using pricing pack
3. **Compute DB NAV**: Sum holdings from database using same pricing pack
4. **Compare**: Compute error in basis points: `|ledger_nav - db_nav| / ledger_nav * 10000`
5. **Validate**: Error must be ≤ 1.0 bp
6. **Store**: Save reconciliation result with full provenance
7. **Alert**: Send alert if reconciliation fails

### Tolerance

- **Pass**: Error ≤ 1.0 basis point (0.01%)
- **Fail**: Error > 1.0 basis point

Example: For a portfolio NAV of $100,000, tolerance is ±$10.00.

---

## NAV Computation

### Ledger NAV

```python
# backend/app/services/ledger.py

async def compute_ledger_nav(
    portfolio_id: UUID,
    asof_date: date,
    commit_hash: str,
    pricing_pack_id: str,
) -> Decimal:
    """
    Compute NAV from ledger postings.

    Steps:
    1. Sum quantities by commodity (symbol) for all postings ≤ asof_date
    2. Get prices from pricing pack
    3. Multiply quantity × price for each holding
    4. Convert to base currency using FX rates from pricing pack
    5. Sum all holdings to get total NAV
    """
```

### Database NAV

```python
# backend/jobs/reconcile_ledger.py

async def compute_db_nav(
    portfolio_id: UUID,
    as_of_date: date,
    pricing_pack_id: str,
) -> Decimal:
    """
    Compute NAV from database lots.

    Steps:
    1. Sum quantities by symbol from lots table (is_open=true, acquisition_date ≤ asof_date)
    2. Get prices from pricing pack (same pack as ledger NAV)
    3. Multiply quantity × price for each holding
    4. Convert to base currency using same FX rates
    5. Sum all holdings to get total NAV
    """
```

### Key Invariants

- **Same Pricing Pack**: Ledger NAV and DB NAV must use identical pricing pack
- **Same FX Rates**: Both must use same FX rates from pricing pack
- **Same Date**: Both computed as of same asof_date
- **Reproducible**: Same inputs → identical outputs

---

## Multi-Currency Handling

### Currency Layers

DawsOS tracks three currency layers:

1. **Trading Currency**: Currency of the security (e.g., USD for AAPL)
2. **Cost Currency**: Currency of cost basis (e.g., CAD for Canadian account)
3. **Base Currency**: Portfolio base currency for NAV (e.g., CAD)

### FX Conversion

```python
# Valuation formula
value_base = quantity × price_trading × fx_rate_trading_to_base
```

Example:
```
AAPL: 100 shares @ $150.00 USD
FX rate: 1.34 USD/CAD
Value in CAD = 100 × 150.00 × 1.34 = 20,100 CAD
```

### FX Rate Sources

- **Trade FX**: Locked at trade time (stored in lot)
- **Valuation FX**: From pricing pack (WM 4pm rates)
- **Pay-Date FX**: For dividends (stored in transaction metadata)

---

## ADR Pay-Date FX

### Critical Accuracy Rule

**ADR dividends MUST use pay-date FX, not ex-date FX.**

This is a critical accuracy requirement from PRODUCT_SPEC.md §6.

### Example: AAPL Dividend

```
Dividend:         $0.24/share × 100 shares = $24.00 USD

Ex-date:          2024-08-01
Ex-date FX:       1.34 USD/CAD → $32.16 CAD (WRONG ❌)

Pay-date:         2024-08-15
Pay-date FX:      1.36 USD/CAD → $32.64 CAD (CORRECT ✓)

Accuracy impact:  $0.48 CAD per transaction
```

### Golden Test

See `backend/tests/test_ledger_reconciliation.py::test_adr_paydate_fx_accuracy` for validation.

### Implementation

```beancount
2024-08-15 * "AAPL dividend payment" #dividend
  Income:Dividends:AAPL                      -24.00 USD
  Assets:Portfolio:...:Cash                   32.64 CAD
  pay_date: "2024-08-15"
  pay_fx_rate: 1.36  ; CRITICAL: use pay-date FX
```

---

## Acceptance Criteria

### Phase 1 Gates (Sprint 1 Week 1)

- [x] Ledger schema created (`ledger.sql`)
- [x] Ledger parser service (`ledger.py`)
- [x] Reconciliation job (`reconcile_ledger.py`)
- [x] Sample ledger fixture (`sample_ledger.beancount`)
- [x] Reconciliation tests (`test_ledger_reconciliation.py`)
- [ ] Parser successfully reads .beancount files
- [ ] Ledger transactions stored in DB with commit hash
- [ ] NAV computation matches Beancount's balance command
- [ ] Reconciliation detects mismatches > 1bp
- [ ] Sample ledger reconciles to ±1bp
- [ ] ADR pay-date FX test passes

### Reconciliation SLO

```
Ledger NAV vs DB NAV: ±1 basis point (100% of portfolios)
```

This is a **hard requirement**. Any portfolio that fails reconciliation triggers an alert.

### Test Coverage

1. ✓ Ledger parsing and snapshot creation
2. ✓ Portfolio transaction extraction
3. ✓ Ledger NAV computation
4. ✓ Database NAV computation
5. ✓ Full reconciliation (ledger vs DB)
6. ✓ ADR pay-date FX accuracy
7. ✓ Missing position detection
8. ✓ Quantity mismatch detection

---

## Operational Procedures

### Daily Operations

#### Nightly Job Schedule

```
00:05 - build_pack()              Build pricing pack
00:10 - reconcile_ledger()        Reconcile ledger vs DB
00:15 - compute_daily_metrics()   Compute TWR, MWR, etc.
00:20 - prewarm_factors()         Pre-warm factor fits
00:25 - mark_pack_fresh()         Enable freshness gate
00:30 - evaluate_alerts()         Check alert conditions
```

#### Manual Reconciliation

```bash
# Single portfolio
python -m backend.jobs.reconcile_ledger \
  --portfolio-id 11111111-1111-1111-1111-111111111111 \
  --as-of-date 2024-10-31

# All portfolios
python -m backend.jobs.reconcile_ledger --all

# Parse ledger only
python -m backend.app.services.ledger \
  --ledger-path /app/ledger \
  --ledger-file main.beancount
```

#### Monitoring Queries

```sql
-- Check latest reconciliation status
SELECT
    portfolio_id,
    asof_date,
    status,
    error_bp,
    ledger_nav,
    db_nav,
    difference
FROM reconciliation_results
WHERE asof_date = CURRENT_DATE
ORDER BY error_bp DESC;

-- Find failing reconciliations
SELECT * FROM reconciliation_summary
WHERE status = 'fail'
ORDER BY reconciled_at DESC
LIMIT 10;

-- Check ledger snapshot status
SELECT * FROM latest_ledger_snapshot;
```

---

## Troubleshooting

### Common Issues

#### 1. Reconciliation Fails (>1bp error)

**Symptoms**: `status = 'fail'`, `error_bp > 1.0`

**Causes**:
- Missing positions in DB
- Quantity mismatches
- Price mismatches (wrong pricing pack)
- FX rate mismatches
- ADR dividend using ex-date FX instead of pay-date FX

**Resolution**:
1. Check `missing_in_db` and `missing_in_ledger` arrays in reconciliation result
2. Compare quantities: query ledger transactions vs lots table
3. Verify same pricing pack used for both NAV calculations
4. Check FX rates match between ledger and pricing pack
5. For ADR dividends, verify pay-date FX used (not ex-date)

#### 2. Ledger Parse Fails

**Symptoms**: `ledger_snapshots.status = 'failed'`

**Causes**:
- Beancount syntax errors
- Missing account declarations
- Balance assertion failures
- Git repo not found

**Resolution**:
1. Check `error_message` in `ledger_snapshots` table
2. Run `bean-check` on ledger file locally
3. Verify git repo is cloned and commit hash exists
4. Check Beancount library installed (`pip install beancount`)

#### 3. Missing Positions

**Symptoms**: Holdings in ledger not in DB (or vice versa)

**Causes**:
- Manual trades not entered in DB
- Ledger not synced with DB
- Corporate actions (splits) not applied

**Resolution**:
1. Check `missing_in_db` array in reconciliation result
2. Manually enter missing transactions in DB
3. Re-import transactions from broker feed
4. Verify corporate actions applied to both ledger and DB

#### 4. ADR Dividend FX Error

**Symptoms**: Reconciliation fails for portfolios with ADR dividends

**Cause**: Using ex-date FX instead of pay-date FX

**Resolution**:
1. Check dividend transaction metadata for `pay_fx_rate`
2. Verify FX rate matches pay-date, not ex-date
3. Update transaction to use correct FX rate
4. Re-run reconciliation

---

## Reproducibility Guarantee

Every result includes:
- `ledger_commit_hash`: Git commit of ledger
- `pricing_pack_id`: Pricing pack used for valuation
- `asof_date`: Date of reconciliation

**Guarantee**: Same `ledger_commit_hash` + `pricing_pack_id` + `asof_date` → **identical NAV**.

This is the core value proposition of DawsOS.

---

## References

- **PRODUCT_SPEC.md §0**: Truth Spine Principle
- **PRODUCT_SPEC.md §2**: Reproducibility Guarantee
- **PRODUCT_SPEC.md §6**: Multi-Currency & Corporate Actions
- **Beancount Documentation**: https://beancount.github.io/docs/
- **DawsOS Transaction Schema**: `backend/db/schema/001_portfolios_lots_transactions.sql`
- **Ledger Schema**: `backend/db/schema/ledger.sql`
- **Sample Ledger**: `backend/tests/fixtures/sample_ledger.beancount`

---

## Change Log

| Date       | Change                                    | Author      |
|------------|-------------------------------------------|-------------|
| 2025-10-23 | Initial implementation complete           | Backend Team|
| 2025-10-23 | Added ADR pay-date FX golden test         | Backend Team|
| 2025-10-23 | Added reconciliation diagnostics          | Backend Team|

---

**End of Document**
