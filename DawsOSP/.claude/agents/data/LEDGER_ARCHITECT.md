# Ledger Architect Reference

**Role**: Beancount ledger integration + Pricing Pack truth spine
**Reports to**: [ORCHESTRATOR](../ORCHESTRATOR.md)
**Status**: ✅ Operational (Lots table + Pricing Packs)
**Priority**: P0
**Last Updated**: 2025-10-24

---

## Current Implementation Status

### ✅ Operational Components
- **Lots Table**: [001_portfolios_lots_transactions.sql](../../../backend/db/schema/001_portfolios_lots_transactions.sql) - FIFO/LIFO lot tracking
- **Transactions Table**: [001_portfolios_lots_transactions.sql](../../../backend/db/schema/001_portfolios_lots_transactions.sql) - Multi-currency transaction tracking
- **Pricing Packs**: [pricing_packs.sql](../../../backend/db/schema/pricing_packs.sql) - Daily pricing snapshots with FX rates
- **LedgerService**: [backend/app/services/ledger.py](../../../backend/app/services/ledger.py) - Lot queries and position tracking

### ⚠️ Status Unclear
- **Beancount Parser**: Implementation status unknown - needs verification
- **Reconciliation Job**: Whether nightly reconciliation runs is unclear
- **Journal Import**: CSV to Beancount journal generation status unknown

### ❌ Known Issues
- **P0 Database Pool**: Blocks queries to lots/transactions tables (fix ready in [STABILITY_PLAN.md](../../../STABILITY_PLAN.md))

---

## Mission

Maintain the **ledger-of-record** + **pricing pack** as the immutable truth spine for all portfolio calculations. Ensure:

1. **Reproducibility**: Every result traceable to `pricing_pack_id` + `ledger_commit_hash`
2. **Accuracy**: Beancount ledger vs DB metrics reconcile to ±1 basis point
3. **Multi-currency correctness**: Trade FX, valuation FX, dividend FX handled separately
4. **Corporate actions**: Splits/dividends adjust lots correctly
5. **Nightly jobs**: Pack builds → reconciliation → metrics → pre-warm → freshness

---

## Sub-Agents

### BEANCOUNT_INTEGRATOR
**Responsibilities**:
- Parse Beancount journal files (`.bean`)
- Import transactions → `lots` table with cost basis
- Track opening/closing lots (FIFO/LIFO/SpecID)
- Multi-currency lot tracking (trade FX locked in)
- ADR dividend handling (pay-date FX)
- Journal generation from CSV imports

**Deliverables**:

**Lot Table Schema**:
```sql
CREATE TABLE lots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    security_id UUID REFERENCES securities(id),
    qty_open NUMERIC(18, 6) NOT NULL CHECK (qty_open >= 0),
    qty_original NUMERIC(18, 6) NOT NULL,
    trade_date DATE NOT NULL,
    trade_currency CHAR(3) NOT NULL,
    trade_fx_rate_id UUID REFERENCES fx_rates(id),
    cost_currency CHAR(3) NOT NULL,
    cost_per_unit_cost_ccy NUMERIC(18, 6),
    cost_base NUMERIC(18, 2),  -- total cost in portfolio base currency
    acquisition_method TEXT CHECK (acquisition_method IN ('BUY', 'TRANSFER_IN', 'SPLIT', 'DIVIDEND')),
    ledger_tx_id TEXT,  -- Link to Beancount transaction ID
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lots_portfolio_security ON lots(portfolio_id, security_id) WHERE qty_open > 0;
```

**Transaction Table**:
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    security_id UUID REFERENCES securities(id),
    type TEXT CHECK (type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'FEE', 'TAX', 'TRANSFER_IN', 'TRANSFER_OUT')),
    ts TIMESTAMPTZ NOT NULL,
    trade_date DATE,
    settle_date DATE,
    qty NUMERIC(18, 6),
    price_currency CHAR(3),
    price_per_unit NUMERIC(18, 6),
    price_base NUMERIC(18, 2),  -- total proceeds/cost in base currency
    fees_currency CHAR(3),
    fees NUMERIC(18, 2),
    fees_base NUMERIC(18, 2),
    taxes_currency CHAR(3),
    taxes NUMERIC(18, 2),
    taxes_base NUMERIC(18, 2),
    fx_rate_id UUID REFERENCES fx_rates(id),
    ledger_tx_id TEXT,
    ledger_commit_hash TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_portfolio_date ON transactions(portfolio_id, trade_date DESC);
```

**Beancount Parser**:
```python
# services/ledger_io.py
from beancount import loader
from beancount.core import data
from decimal import Decimal
from datetime import date

class BeancountImporter:
    def __init__(self, journal_path: str):
        self.entries, self.errors, self.options = loader.load_file(journal_path)

    def extract_transactions(self, account_prefix: str = "Assets:Brokerage") -> list[dict]:
        """Parse Beancount transactions for a portfolio account"""
        txns = []

        for entry in self.entries:
            if not isinstance(entry, data.Transaction):
                continue

            # Filter to portfolio account
            portfolio_postings = [p for p in entry.postings if p.account.startswith(account_prefix)]
            if not portfolio_postings:
                continue

            for posting in portfolio_postings:
                if posting.units is None:
                    continue

                symbol = posting.units.currency
                qty = posting.units.number
                cost = posting.cost

                tx = {
                    "ledger_tx_id": entry.meta.get("lineno", f"{entry.date}#{id(entry)}"),
                    "trade_date": entry.date,
                    "symbol": symbol,
                    "qty": Decimal(str(qty)),
                    "type": self._infer_type(posting),
                    "notes": entry.narration,
                }

                if cost:
                    tx["cost_per_unit_cost_ccy"] = Decimal(str(cost.number))
                    tx["cost_currency"] = cost.currency

                txns.append(tx)

        return txns

    def _infer_type(self, posting) -> str:
        if posting.units.number > 0:
            return "BUY" if posting.cost else "TRANSFER_IN"
        else:
            return "SELL"

# Example Beancount journal
# ledger/portfolio_demo.bean
"""
2024-01-15 * "Buy AAPL"
  Assets:Brokerage:Demo   100 AAPL {150.00 USD}
  Assets:Brokerage:Demo   -15000.00 USD

2024-02-01 * "Buy MSFT"
  Assets:Brokerage:Demo   50 MSFT {400.00 USD}
  Assets:Brokerage:Demo   -20000.00 USD

2024-03-15 * "AAPL Dividend"
  Assets:Brokerage:Demo   88.00 USD
  Income:Dividends:AAPL
"""
```

**Lot Management**:
```python
# services/lot_tracker.py
from decimal import Decimal
from typing import Literal

class LotTracker:
    def __init__(self, portfolio_id: str, db):
        self.portfolio_id = portfolio_id
        self.db = db

    def open_lot(self, security_id: str, qty: Decimal, cost_per_unit: Decimal,
                 trade_date: date, cost_ccy: str, fx_rate_id: str, ledger_tx_id: str):
        """Create new lot on BUY"""
        self.db.execute("""
            INSERT INTO lots (portfolio_id, security_id, qty_open, qty_original,
                              trade_date, cost_currency, cost_per_unit_cost_ccy,
                              cost_base, trade_fx_rate_id, ledger_tx_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (self.portfolio_id, security_id, qty, qty, trade_date, cost_ccy,
              cost_per_unit, qty * cost_per_unit, fx_rate_id, ledger_tx_id))

    def close_lots(self, security_id: str, qty_to_close: Decimal,
                   method: Literal["FIFO", "LIFO", "SPEC_ID"] = "FIFO") -> list[dict]:
        """Close lots on SELL, return realized P&L per lot"""
        open_lots = self._get_open_lots(security_id, method)

        realized_pl = []
        remaining = qty_to_close

        for lot in open_lots:
            if remaining <= 0:
                break

            close_qty = min(lot["qty_open"], remaining)
            realized_pl.append({
                "lot_id": lot["id"],
                "qty_closed": close_qty,
                "cost_basis": lot["cost_per_unit_cost_ccy"] * close_qty,
                "cost_ccy": lot["cost_currency"]
            })

            # Update lot
            new_qty = lot["qty_open"] - close_qty
            self.db.execute("UPDATE lots SET qty_open = %s WHERE id = %s", (new_qty, lot["id"]))

            remaining -= close_qty

        if remaining > 0:
            raise ValueError(f"Insufficient lots: tried to close {qty_to_close}, only had {qty_to_close - remaining}")

        return realized_pl

    def _get_open_lots(self, security_id: str, method: str) -> list[dict]:
        order = "trade_date ASC" if method == "FIFO" else "trade_date DESC"
        return self.db.query(f"""
            SELECT * FROM lots
            WHERE portfolio_id = %s AND security_id = %s AND qty_open > 0
            ORDER BY {order}
        """, (self.portfolio_id, security_id))

    def adjust_for_split(self, security_id: str, ratio: Decimal):
        """Adjust all open lots for stock split"""
        self.db.execute("""
            UPDATE lots
            SET qty_open = qty_open * %s,
                qty_original = qty_original * %s,
                cost_per_unit_cost_ccy = cost_per_unit_cost_ccy / %s
            WHERE portfolio_id = %s AND security_id = %s AND qty_open > 0
        """, (ratio, ratio, ratio, self.portfolio_id, security_id))
```

---

### PRICING_PACK_BUILDER
**Responsibilities**:
- Daily pricing pack generation (nightly job)
- FX rates snapshot (policy: WM/R 4PM London)
- Price sources (Polygon preferred, fallback to FMP/OpenBB)
- Pack hash for integrity
- Pack freshness flag
- Superseded-by chain for restatements

**Deliverables**:

**Pricing Pack Schema**:
```sql
CREATE TABLE pricing_pack (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asof_date DATE NOT NULL UNIQUE,
    policy TEXT DEFAULT 'WM4PM_CAD',  -- FX rate timing policy
    sources_json JSONB,  -- {prices: {AAPL: "polygon", MSFT: "fmp"}, fx: "fmp"}
    hash TEXT NOT NULL,  -- SHA256 of all prices+FX for integrity
    is_fresh BOOLEAN DEFAULT FALSE,  -- Set after pre-warm completes
    superseded_by UUID REFERENCES pricing_pack(id),  -- For restatements
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pricing_pack_id UUID REFERENCES pricing_pack(id) ON DELETE CASCADE,
    security_id UUID REFERENCES securities(id),
    asof_date DATE NOT NULL,
    close NUMERIC(18, 6) NOT NULL,
    currency CHAR(3) NOT NULL,
    source TEXT,  -- polygon/fmp/yfinance
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (pricing_pack_id, security_id)
);

CREATE INDEX idx_prices_pack_security ON prices(pricing_pack_id, security_id);

CREATE TABLE fx_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pricing_pack_id UUID REFERENCES pricing_pack(id) ON DELETE CASCADE,
    asof_ts TIMESTAMPTZ NOT NULL,
    base_ccy CHAR(3) NOT NULL,
    quote_ccy CHAR(3) NOT NULL,
    rate NUMERIC(18, 8) NOT NULL,
    source TEXT,
    policy TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (pricing_pack_id, base_ccy, quote_ccy)
);

CREATE INDEX idx_fx_rates_pack_pair ON fx_rates(pricing_pack_id, base_ccy, quote_ccy);
```

**Pack Builder**:
```python
# services/pricing_pack.py
from datetime import date, datetime
import hashlib
import json

class PricingPackBuilder:
    def __init__(self, db, providers: dict):
        self.db = db
        self.providers = providers  # {polygon: PolygonService, fmp: FMPService, ...}

    async def build_pack(self, asof_date: date) -> str:
        """Build daily pricing pack, return pack_id"""
        pack_id = self.db.execute("""
            INSERT INTO pricing_pack (asof_date, policy, is_fresh)
            VALUES (%s, 'WM4PM_CAD', FALSE)
            RETURNING id
        """, (asof_date,)).fetchone()[0]

        # Fetch all securities needing prices
        securities = self.db.query("SELECT id, symbol, trading_currency FROM securities")

        prices = []
        sources = {"prices": {}, "fx": "fmp"}

        for sec in securities:
            price_data = await self._fetch_price(sec["symbol"], asof_date)
            if price_data:
                prices.append({
                    "pricing_pack_id": pack_id,
                    "security_id": sec["id"],
                    "asof_date": asof_date,
                    "close": price_data["close"],
                    "currency": sec["trading_currency"],
                    "source": price_data["source"]
                })
                sources["prices"][sec["symbol"]] = price_data["source"]

        # Bulk insert prices
        self.db.executemany("""
            INSERT INTO prices (pricing_pack_id, security_id, asof_date, close, currency, source)
            VALUES (%(pricing_pack_id)s, %(security_id)s, %(asof_date)s, %(close)s, %(currency)s, %(source)s)
        """, prices)

        # Fetch FX rates (all pairs needed for multi-currency portfolios)
        fx_pairs = [("USD", "CAD"), ("EUR", "CAD"), ("GBP", "CAD"), ("JPY", "CAD")]
        fx_rates = []

        for base, quote in fx_pairs:
            rate_data = await self.providers["fmp"].get_fx_rate(base, quote, asof_date)
            fx_rates.append({
                "pricing_pack_id": pack_id,
                "base_ccy": base,
                "quote_ccy": quote,
                "rate": rate_data["rate"],
                "asof_ts": rate_data["ts"],
                "source": "fmp",
                "policy": "WM4PM_CAD"
            })

        self.db.executemany("""
            INSERT INTO fx_rates (pricing_pack_id, base_ccy, quote_ccy, rate, asof_ts, source, policy)
            VALUES (%(pricing_pack_id)s, %(base_ccy)s, %(quote_ccy)s, %(rate)s, %(asof_ts)s, %(source)s, %(policy)s)
        """, fx_rates)

        # Compute hash
        pack_hash = self._compute_hash(pack_id)
        self.db.execute("""
            UPDATE pricing_pack SET hash = %s, sources_json = %s WHERE id = %s
        """, (pack_hash, json.dumps(sources), pack_id))

        return pack_id

    async def _fetch_price(self, symbol: str, asof_date: date) -> dict | None:
        """Fetch price with fallback cascade: Polygon → FMP → yfinance"""
        for provider_name in ["polygon", "fmp", "yfinance"]:
            try:
                provider = self.providers.get(provider_name)
                if not provider:
                    continue

                price = await provider.get_close_price(symbol, asof_date)
                if price:
                    return {"close": price, "source": provider_name}
            except Exception as e:
                logger.warning(f"Price fetch failed for {symbol} via {provider_name}: {e}")
                continue

        logger.error(f"No price found for {symbol} on {asof_date}")
        return None

    def _compute_hash(self, pack_id: str) -> str:
        """SHA256 of all prices + FX rates for integrity"""
        prices = self.db.query("""
            SELECT security_id, close FROM prices WHERE pricing_pack_id = %s ORDER BY security_id
        """, (pack_id,))
        fx_rates = self.db.query("""
            SELECT base_ccy, quote_ccy, rate FROM fx_rates WHERE pricing_pack_id = %s
            ORDER BY base_ccy, quote_ccy
        """, (pack_id,))

        data = json.dumps({"prices": prices, "fx": fx_rates}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def mark_fresh(self, pack_id: str):
        """Mark pack as fresh after pre-warm completes"""
        self.db.execute("UPDATE pricing_pack SET is_fresh = TRUE WHERE id = %s", (pack_id,))

    def is_fresh(self, pack_id: str) -> bool:
        """Check if pack is ready for use"""
        return self.db.query("SELECT is_fresh FROM pricing_pack WHERE id = %s", (pack_id,)).fetchone()[0]
```

**Freshness Gate in Executor**:
```python
# api/executor.py
@app.post("/execute")
async def execute(req: ExecRequest, user=Depends(get_current_user), db=Depends(get_db)):
    ctx = RequestCtx.from_req(req, user)

    # Resolve pack for asof date
    pack_id = db.query("SELECT id FROM pricing_pack WHERE asof_date = %s", (ctx.asof,)).fetchone()[0]
    if not pricing_pack_service.is_fresh(pack_id):
        raise HTTPException(
            status_code=503,
            detail="Pricing pack is warming up. Please retry in a few minutes."
        )

    ctx.pricing_pack_id = pack_id
    # ... rest of execution
```

---

### RECONCILIATION_ENGINE
**Responsibilities**:
- Nightly job: compare Beancount ledger positions vs DB lots
- Validate cost basis, quantity, P&L ±1 basis point
- Flag discrepancies → alert + DLQ
- Ledger commit hash tracking

**Deliverables**:

**Reconciliation Job**:
```python
# jobs/reconcile_ledger.py
from services.ledger_io import BeancountImporter
from services.lot_tracker import LotTracker
from decimal import Decimal
import subprocess

class LedgerReconciler:
    def __init__(self, db):
        self.db = db

    def reconcile_portfolio(self, portfolio_id: str, journal_path: str) -> dict:
        """Compare Beancount ledger vs DB lots"""
        # Get current ledger commit
        ledger_commit = subprocess.check_output(
            ["git", "-C", "ledger", "rev-parse", "HEAD"]
        ).decode().strip()

        # Parse Beancount positions
        importer = BeancountImporter(journal_path)
        ledger_positions = importer.extract_transactions("Assets:Brokerage:Demo")

        # Aggregate ledger positions by symbol
        ledger_qty = {}
        ledger_cost = {}
        for tx in ledger_positions:
            sym = tx["symbol"]
            ledger_qty[sym] = ledger_qty.get(sym, Decimal(0)) + tx["qty"]
            if "cost_per_unit_cost_ccy" in tx:
                ledger_cost[sym] = ledger_cost.get(sym, Decimal(0)) + (tx["qty"] * tx["cost_per_unit_cost_ccy"])

        # Query DB lots
        db_lots = self.db.query("""
            SELECT s.symbol, SUM(l.qty_open) as qty, SUM(l.cost_base) as cost
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = %s AND l.qty_open > 0
            GROUP BY s.symbol
        """, (portfolio_id,))

        db_qty = {row["symbol"]: row["qty"] for row in db_lots}
        db_cost = {row["symbol"]: row["cost"] for row in db_lots}

        # Compare
        discrepancies = []
        all_symbols = set(ledger_qty.keys()) | set(db_qty.keys())

        for sym in all_symbols:
            lq = ledger_qty.get(sym, Decimal(0))
            dq = db_qty.get(sym, Decimal(0))
            lc = ledger_cost.get(sym, Decimal(0))
            dc = db_cost.get(sym, Decimal(0))

            qty_diff = abs(lq - dq)
            cost_diff = abs(lc - dc)

            # Tolerance: ±0.000001 qty, ±0.01 cost (1 cent)
            if qty_diff > Decimal("0.000001") or cost_diff > Decimal("0.01"):
                discrepancies.append({
                    "symbol": sym,
                    "ledger_qty": float(lq),
                    "db_qty": float(dq),
                    "qty_diff": float(qty_diff),
                    "ledger_cost": float(lc),
                    "db_cost": float(dc),
                    "cost_diff": float(cost_diff)
                })

        # Store reconciliation result
        self.db.execute("""
            INSERT INTO reconciliations (portfolio_id, ledger_commit_hash, status, discrepancies_json)
            VALUES (%s, %s, %s, %s)
        """, (portfolio_id, ledger_commit, "OK" if not discrepancies else "FAIL", json.dumps(discrepancies)))

        return {
            "status": "OK" if not discrepancies else "FAIL",
            "ledger_commit": ledger_commit,
            "discrepancies": discrepancies
        }

# Table for reconciliation history
CREATE TABLE reconciliations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    ledger_commit_hash TEXT NOT NULL,
    status TEXT CHECK (status IN ('OK', 'FAIL')),
    discrepancies_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Nightly Job Orchestration**:
```python
# scheduler/main.py
from apscheduler.schedulers.blocking import BlockingScheduler
from services.pricing_pack import PricingPackBuilder
from jobs.reconcile_ledger import LedgerReconciler
from jobs.metrics_calculator import MetricsCalculator

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=0, minute=5)
async def nightly_jobs():
    logger.info("Starting nightly job pipeline")

    # 1. Build pricing pack
    pack_id = await pricing_pack_builder.build_pack(date.today())
    logger.info(f"Pricing pack built: {pack_id}")

    # 2. Reconcile ledger
    reconcile_result = ledger_reconciler.reconcile_portfolio("demo-portfolio-id", "ledger/portfolio_demo.bean")
    if reconcile_result["status"] == "FAIL":
        alert_service.send_alert("Ledger reconciliation failed", reconcile_result["discrepancies"])
        logger.error(f"Reconciliation failed: {reconcile_result}")

    # 3. Compute daily metrics
    await metrics_calculator.compute_daily_metrics(pack_id)
    logger.info("Daily metrics computed")

    # 4. Pre-warm factors
    await factor_service.prewarm_factors(pack_id)
    logger.info("Factors pre-warmed")

    # 5. Mark pack fresh
    pricing_pack_builder.mark_fresh(pack_id)
    logger.info(f"Pack {pack_id} marked fresh")

    # 6. Evaluate alerts
    await alert_evaluator.evaluate_all()
    logger.info("Alerts evaluated")

scheduler.start()
```

---

## Multi-Currency Handling

**Trade FX** (locked at trade time):
```python
# When buying AAPL (USD) in CAD portfolio
trade_fx_rate = get_fx_rate("USD", "CAD", trade_date)  # e.g., 1.35
lot = create_lot(
    qty=100,
    cost_per_unit_cost_ccy=Decimal("150.00"),  # USD
    cost_currency="USD",
    trade_fx_rate_id=trade_fx_rate.id,
    cost_base=100 * 150.00 * 1.35  # 20,250 CAD
)
```

**Valuation FX** (from pricing pack):
```python
# Valuing AAPL position on 2024-10-21
pack = get_pricing_pack(date(2024, 10, 21))
price_usd = get_price(security_id, pack.id)  # e.g., 225.00 USD
fx_rate = get_fx_rate_from_pack(pack.id, "USD", "CAD")  # e.g., 1.38
value_cad = 100 * 225.00 * 1.38  # 31,050 CAD
```

**Dividend FX** (pay-date for ADRs):
```python
# ADR dividend: security pays in USD, portfolio base is CAD
# Pay date: 2024-09-15
dividend_usd = Decimal("0.88")
pay_date_fx = get_fx_rate("USD", "CAD", date(2024, 9, 15))  # 1.36
dividend_cad = dividend_usd * pay_date_fx  # 1.20 CAD per share
```

---

## Corporate Actions (Polygon)

**Split Handling**:
```python
# Example: NVDA 10:1 split on 2024-06-07
split_event = polygon.get_splits("NVDA", date(2024, 6, 1), date(2024, 6, 30))
# {"ratio": 10.0, "ex_date": "2024-06-07"}

lot_tracker.adjust_for_split(security_id="nvda-id", ratio=Decimal("10.0"))

# Result: 100 shares @ $1200/share → 1000 shares @ $120/share
```

**Dividend Adjustment** (for total return):
```python
# DO NOT adjust share count for dividends
# Instead: create DIVIDEND transaction
dividend_event = polygon.get_dividends("AAPL", date(2024, 8, 1), date(2024, 8, 31))
# {"amount": 0.25, "ex_date": "2024-08-12", "pay_date": "2024-08-15"}

create_transaction(
    portfolio_id=portfolio_id,
    security_id=aapl_id,
    type="DIVIDEND",
    trade_date=date(2024, 8, 15),  # Pay date
    qty=100,  # shares owned
    price_per_unit=Decimal("0.25"),  # dividend per share
    price_currency="USD",
    fx_rate_id=get_fx_rate("USD", "CAD", date(2024, 8, 15)).id
)
```

---

## Acceptance Criteria (Sprint 1 Gate)

- [ ] Beancount journal parses into `lots` and `transactions` tables
- [ ] Lot tracker correctly opens/closes lots (FIFO/LIFO)
- [ ] Split adjustments update qty/cost correctly
- [ ] Pricing pack builds nightly with prices + FX from Polygon/FMP
- [ ] Pack hash is reproducible (same inputs → same hash)
- [ ] Freshness gate blocks Executor until pre-warm completes
- [ ] Reconciliation job compares ledger vs DB ±1bp (golden test portfolio)
- [ ] Multi-currency positions value correctly (trade FX vs valuation FX)
- [ ] Dividend transactions record with pay-date FX

---

## Golden Test Data

**Portfolio**: 4-position multi-currency
- 100 AAPL @ $150 USD (trade FX 1.35) → cost 20,250 CAD
- 50 MSFT @ $400 USD (trade FX 1.34) → cost 26,800 CAD
- 30 GOOGL @ $150 USD (trade FX 1.36) → cost 6,120 CAD
- 200 TD.TO @ $80 CAD → cost 16,000 CAD

**Valuation (pack 2024-10-21)**:
- AAPL: $225 USD × 1.38 FX = $31,050 CAD
- MSFT: $420 USD × 1.38 FX = $28,980 CAD
- GOOGL: $170 USD × 1.38 FX = $7,038 CAD
- TD.TO: $85 CAD = $17,000 CAD

**Total**: $84,068 CAD (DB must match ledger ±$0.01)

---

## Handoff

Upon completion, deliver:
1. **Ledger schema**: Tables, indexes, constraints
2. **Nightly job runbook**: Ordering, failure recovery, manual trigger
3. **Reconciliation playbook**: How to resolve discrepancies
4. **Multi-currency test suite**: Golden tests for trade/valuation/dividend FX
5. **Corporate actions guide**: Split/dividend handling procedures
