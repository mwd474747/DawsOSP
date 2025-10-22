# Schema Specialist Agent

**Role**: Authoritative reference for database schema, migrations, and data integrity
**Reports to**: [ORCHESTRATOR](../ORCHESTRATOR.md)
**Collaborates with**: All agents (cross-cutting concern)
**Status**: Active - Referenced by all implementation agents
**Priority**: P0

---

## Mission

Serve as the **single source of truth** for:
1. Production database schema (tables, columns, constraints, indexes)
2. RLS policies and multi-tenancy patterns
3. Migration strategy and version control
4. Data integrity constraints and validation rules
5. Query patterns and performance considerations

**Key Principle**: Any agent working with the database **MUST** consult this specialist to avoid schema drift.

---

## Schema Reference (Production v1.0 + Migrations)

### Core Schema Documentation

**Base Schema**: Production PostgreSQL 15 + TimescaleDB 2.x
**Validation Report**: [.claude/analysis/SCHEMA_VALIDATION.md](../../analysis/SCHEMA_VALIDATION.md)
**Migration Files**: [.claude/migrations/](../../migrations/)

---

## Table Catalog (By Domain)

### 1. Tenancy & Identity

#### `users`
```sql
CREATE TABLE users (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email        TEXT NOT NULL UNIQUE,
  auth_provider TEXT,
  base_ccy     CHAR(3) NOT NULL DEFAULT 'CAD',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```
**Purpose**: User accounts with OAuth provider tracking
**RLS**: Not enabled (global reference table)
**Used by**: All portfolio-scoped tables via `portfolios.user_id`

---

#### `portfolios`
```sql
CREATE TABLE portfolios (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  base_ccy     CHAR(3) NOT NULL,
  benchmark_id UUID REFERENCES benchmarks(id),
  settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  ledger_path  TEXT,                              -- Migration 001
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_read ON portfolios
  FOR SELECT USING (user_id::text = current_setting('app.user_id', true));
```
**Purpose**: Portfolio metadata and settings
**RLS**: ✅ Enabled - Users can only see their own portfolios
**Used by**: All portfolio-scoped analytics tables
**Migration 001 adds**: `ledger_path` (Beancount journal location)

---

#### `benchmarks`
```sql
CREATE TABLE benchmarks (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code         TEXT NOT NULL UNIQUE,        -- e.g. "SPXT:CAD"
  name         TEXT NOT NULL,
  currency     CHAR(3) NOT NULL,
  hedged_flag  BOOLEAN NOT NULL DEFAULT FALSE
);
```
**Purpose**: Benchmark definitions (hedged vs unhedged)
**RLS**: Not enabled (global reference)
**Used by**: `portfolios.benchmark_id`, `benchmark_returns`

---

#### `securities`
```sql
CREATE TABLE securities (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol            TEXT NOT NULL,
  name              TEXT,
  exchange          TEXT,
  trading_currency  CHAR(3) NOT NULL,
  dividend_currency CHAR(3),
  type              instrument_type_enum NOT NULL,
  domicile_country  CHAR(2),
  figi              TEXT,
  cusip             TEXT,
  UNIQUE(symbol, exchange)
);
```
**Purpose**: Security master (stocks, ETFs, bonds)
**RLS**: Not enabled (global reference)
**Multi-currency note**: `trading_currency` for prices, `dividend_currency` for ADR dividends
**Used by**: `lots`, `transactions`, `prices`, `ratings`

---

### 2. Pricing & Market Data (Immutable)

#### `pricing_pack`
```sql
CREATE TABLE pricing_pack (
  id                 TEXT PRIMARY KEY,              -- e.g. 'PP-2025-10-21'
  date               DATE NOT NULL UNIQUE,
  policy             TEXT NOT NULL,                 -- 'WM4PM_CAD'
  sources_json       JSONB NOT NULL,
  hash               TEXT NOT NULL,
  superseded_by      TEXT REFERENCES pricing_pack(id),
  ledger_commit_hash TEXT,                          -- Migration 001
  is_fresh           BOOLEAN DEFAULT FALSE,         -- Migration 001
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (policy <> '')
);

CREATE INDEX idx_pack_fresh ON pricing_pack (date DESC) WHERE is_fresh = TRUE;
```
**Purpose**: Immutable daily pricing snapshots with FX rates
**RLS**: Not enabled (global reference)
**Immutability**: Rows NEVER updated; use `superseded_by` for restatements
**Migration 001 adds**: `ledger_commit_hash` (Git commit of ledger repo), `is_fresh` (pre-warm flag)
**Used by**: All analytics tables for reproducibility

**Query Patterns**:
```sql
-- Get current fresh pack
SELECT id, date FROM pricing_pack
WHERE is_fresh = TRUE ORDER BY date DESC LIMIT 1;

-- Resolve pack for date
SELECT id FROM pricing_pack WHERE date = '2025-10-21';

-- Check if pack is superseded
SELECT superseded_by FROM pricing_pack WHERE id = 'PP-2025-10-21';
```

---

#### `prices`
```sql
CREATE TABLE prices (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  security_id     UUID NOT NULL REFERENCES securities(id) ON DELETE CASCADE,
  asof_date       DATE NOT NULL,
  close           NUMERIC(28,10) NOT NULL,
  currency        CHAR(3) NOT NULL,
  source          TEXT NOT NULL,              -- 'polygon', 'fmp', 'yfinance'
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  UNIQUE (security_id, asof_date, pricing_pack_id)
);

CREATE INDEX idx_prices_sec_date ON prices (security_id, asof_date);
CREATE INDEX idx_prices_pack_sec ON prices (pricing_pack_id, security_id, asof_date);
```
**Purpose**: Security prices (split-adjusted only; dividends in transactions)
**RLS**: Not enabled (global reference)
**Important**: Prices are split-adjusted but NOT dividend-adjusted (total return calculated separately)
**Used by**: Pricing pack valuation, TWR calculation

---

#### `fx_rates`
```sql
CREATE TABLE fx_rates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asof_ts         TIMESTAMPTZ NOT NULL,
  base_ccy        CHAR(3) NOT NULL,
  quote_ccy       CHAR(3) NOT NULL,
  rate            NUMERIC(20,10) NOT NULL,
  source          TEXT NOT NULL,
  policy          TEXT NOT NULL,              -- 'WM4PM_CAD'
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  UNIQUE (base_ccy, quote_ccy, asof_ts, pricing_pack_id)
);

CREATE INDEX idx_fx_pair_ts ON fx_rates (base_ccy, quote_ccy, asof_ts);
CREATE INDEX idx_fx_pack_pair_ts ON fx_rates (pricing_pack_id, base_ccy, quote_ccy, asof_ts);
```
**Purpose**: FX rates per pricing pack (WM/Reuters 4PM London)
**RLS**: Not enabled (global reference)
**Multi-currency note**: Three use cases:
1. **Trade-time FX**: Locked in `lots.trade_fx_rate_id`
2. **Valuation FX**: From `pricing_pack_id` (current value)
3. **Pay-date FX**: Locked in `transactions.pay_fx_rate_id` (ADR dividends)

**Query Pattern**:
```sql
-- Get FX rate from pack
SELECT rate FROM fx_rates
WHERE pricing_pack_id = 'PP-2025-10-21'
  AND base_ccy = 'USD' AND quote_ccy = 'CAD'
ORDER BY asof_ts DESC LIMIT 1;
```

---

### 3. Ledger & Holdings (Multi-Currency Truth)

#### `lots`
```sql
CREATE TABLE lots (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id      UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  security_id       UUID NOT NULL REFERENCES securities(id) ON DELETE CASCADE,
  qty_open          NUMERIC(28,10) NOT NULL,
  trade_ccy         CHAR(3) NOT NULL,
  trade_fx_rate_id  UUID REFERENCES fx_rates(id),    -- FX at trade time
  cost_ccy          CHAR(3) NOT NULL,
  cost_per_unit_ccy NUMERIC(28,10) NOT NULL,
  cost_base         NUMERIC(28,10) NOT NULL,
  trade_date        DATE NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_lots_portfolio_sec ON lots (portfolio_id, security_id);

-- RLS
ALTER TABLE lots ENABLE ROW LEVEL SECURITY;
CREATE POLICY lots_rw ON lots
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Open lot positions (FIFO/LIFO tracking)
**RLS**: ✅ Enabled - Users can only see their portfolio's lots
**Multi-currency**: `trade_fx_rate_id` locks FX at trade time (never changes)
**Used by**: Position valuation, realized P&L calculation

**Query Pattern**:
```sql
-- Get open positions for portfolio
SELECT s.symbol, l.qty_open, l.cost_base
FROM lots l
JOIN securities s ON l.security_id = s.id
WHERE l.portfolio_id = :portfolio_id AND l.qty_open > 0;
```

---

#### `transactions`
```sql
CREATE TABLE transactions (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id       UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  security_id        UUID REFERENCES securities(id),
  type               txn_type_enum NOT NULL,
  qty                NUMERIC(28,10),
  price_ccy          NUMERIC(28,10),
  price_base         NUMERIC(28,10),
  trade_ccy          CHAR(3),
  trade_fx_rate_id   UUID REFERENCES fx_rates(id),
  -- ADR/Dividend fields
  gross_ccy          NUMERIC(28,10),
  gross_base         NUMERIC(28,10),
  withholding_ccy    NUMERIC(28,10),
  withholding_base   NUMERIC(28,10),
  net_ccy            NUMERIC(28,10),
  net_base           NUMERIC(28,10),
  pay_date           DATE,
  pay_fx_rate_id     UUID REFERENCES fx_rates(id),    -- FX at pay date
  fees_ccy           NUMERIC(28,10),
  fees_base          NUMERIC(28,10),
  taxes_ccy          NUMERIC(28,10),
  taxes_base         NUMERIC(28,10),
  txn_ts             TIMESTAMPTZ NOT NULL,
  ledger_tx_id       TEXT,                            -- Migration 001
  meta_json          JSONB NOT NULL DEFAULT '{}'::jsonb,
  CHECK (NOT(type IN ('dividend','coupon') AND pay_fx_rate_id IS NULL))
);

CREATE INDEX idx_txn_portfolio_ts ON transactions (portfolio_id, txn_ts DESC);
CREATE INDEX idx_txn_portfolio_type ON transactions (portfolio_id, type);

-- RLS
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY txn_rw ON transactions
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: All cash/position-changing events (buys, sells, dividends, fees)
**RLS**: ✅ Enabled
**Multi-currency**: Separate FX for trades (`trade_fx_rate_id`) vs dividends (`pay_fx_rate_id`)
**ADR-safe**: `gross_ccy`, `withholding_ccy`, `net_ccy` + `pay_fx_rate_id` for proper accounting
**Migration 001 adds**: `ledger_tx_id` (Beancount transaction ID for provenance)

**Important**: CHECK constraint enforces `pay_fx_rate_id` for dividend/coupon types

---

#### `reconciliations` (Migration 002)
```sql
CREATE TABLE reconciliations (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id       UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_date          DATE NOT NULL,
  ledger_commit_hash TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('OK', 'FAIL')),
  discrepancies_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (portfolio_id, asof_date)
);

CREATE INDEX idx_reconciliations_portfolio_date ON reconciliations (portfolio_id, asof_date DESC);

-- RLS
ALTER TABLE reconciliations ENABLE ROW LEVEL SECURITY;
CREATE POLICY reconciliations_rw ON reconciliations
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Track nightly ledger vs DB reconciliation results (±1bp validation)
**RLS**: ✅ Enabled
**Used by**: Reconciliation job, alerting on discrepancies
**Migration**: 002

---

### 4. Analytics (Timescale Hypertables)

#### `portfolio_daily_values` (Migration 003)
```sql
CREATE TABLE portfolio_daily_values (
  portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_date       DATE NOT NULL,
  total_value     NUMERIC(28,10) NOT NULL,
  cash_flows      NUMERIC(28,10) NOT NULL DEFAULT 0,
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

SELECT create_hypertable('portfolio_daily_values', 'asof_date', if_not_exists => TRUE);
CREATE INDEX ON portfolio_daily_values (portfolio_id, asof_date DESC);

-- RLS
ALTER TABLE portfolio_daily_values ENABLE ROW LEVEL SECURITY;
CREATE POLICY daily_values_rw ON portfolio_daily_values
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Daily portfolio valuations + cash flows for TWR calculation
**RLS**: ✅ Enabled
**Hypertable**: ✅ Time-series optimized
**Used by**: TWR calculation (Section 13 spec formula)
**Migration**: 003

**TWR Formula**:
```
r_i = (V_i - V_{i-1} - CF_i) / (V_{i-1} + CF_i)
TWR = [(1+r_1)(1+r_2)...(1+r_n)] - 1
```

---

#### `portfolio_metrics`
```sql
CREATE TABLE portfolio_metrics (
  portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_date       DATE NOT NULL,
  twr             NUMERIC(18,8) NOT NULL,
  mwr             NUMERIC(18,8),
  vol             NUMERIC(18,8),
  sharpe          NUMERIC(18,8),
  beta            NUMERIC(18,8),
  max_dd          NUMERIC(18,8),
  base_ccy        CHAR(3) NOT NULL,
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

SELECT create_hypertable('portfolio_metrics', 'asof_date', if_not_exists => TRUE);
CREATE INDEX ON portfolio_metrics (portfolio_id, asof_date DESC);

-- RLS
ALTER TABLE portfolio_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY metrics_rw ON portfolio_metrics
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Computed performance metrics (outputs of calculation)
**RLS**: ✅ Enabled
**Hypertable**: ✅ Time-series optimized
**Used by**: Portfolio overview UI, performance charts

---

#### `currency_attribution`
```sql
CREATE TABLE currency_attribution (
  portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_date       DATE NOT NULL,
  local_ret       NUMERIC(18,8) NOT NULL,
  fx_ret          NUMERIC(18,8) NOT NULL,
  interaction_ret NUMERIC(18,8) NOT NULL,
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

SELECT create_hypertable('currency_attribution', 'asof_date', if_not_exists => TRUE);
CREATE INDEX ON currency_attribution (portfolio_id, asof_date DESC);

-- RLS
ALTER TABLE currency_attribution ENABLE ROW LEVEL SECURITY;
CREATE POLICY attr_rw ON currency_attribution
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Return decomposition (local + FX + interaction)
**RLS**: ✅ Enabled
**Hypertable**: ✅ Time-series optimized
**Formula**: `r_base = (1 + r_local)(1 + r_fx) - 1 = r_local + r_fx + (r_local × r_fx)`

---

#### `factor_exposures`
```sql
CREATE TABLE factor_exposures (
  portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_date       DATE NOT NULL,
  betas_json      JSONB NOT NULL,        -- {"real_rate": 0.3, "inflation": -0.2, ...}
  var_share_json  JSONB NOT NULL,        -- {"systematic": 0.7, "idiosyncratic": 0.3}
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (portfolio_id, asof_date, pricing_pack_id)
);

SELECT create_hypertable('factor_exposures', 'asof_date', if_not_exists => TRUE);
CREATE INDEX ON factor_exposures (portfolio_id, asof_date DESC);

-- RLS
ALTER TABLE factor_exposures ENABLE ROW LEVEL SECURITY;
CREATE POLICY expo_rw ON factor_exposures
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Factor beta decomposition (real rate, inflation, credit, USD)
**RLS**: ✅ Enabled
**Hypertable**: ✅ Time-series optimized
**Used by**: Macro analysis, scenario shocks

---

#### `benchmark_returns` (Migration 004)
```sql
CREATE TABLE benchmark_returns (
  benchmark_id    UUID NOT NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
  asof_date       DATE NOT NULL,
  return          NUMERIC(18,8) NOT NULL,
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (benchmark_id, asof_date, pricing_pack_id)
);

SELECT create_hypertable('benchmark_returns', 'asof_date', if_not_exists => TRUE);
CREATE INDEX ON benchmark_returns (benchmark_id, asof_date DESC);
```
**Purpose**: Daily benchmark returns (for beta calculation)
**RLS**: Not enabled (global reference)
**Hypertable**: ✅ Time-series optimized
**Used by**: Beta calculation, hedged vs unhedged comparison
**Migration**: 004

---

### 5. Ratings & News

#### `ratings`
```sql
CREATE TABLE ratings (
  portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  security_id     UUID NOT NULL REFERENCES securities(id) ON DELETE CASCADE,
  asof_date       DATE NOT NULL,
  rating_type     rating_type_enum NOT NULL,    -- dividend_safety, moat_strength, recession_resilience
  value           NUMERIC(6,2) NOT NULL,         -- 0-10 scale
  inputs_json     JSONB NOT NULL,                -- Versioned inputs for explainability
  method          TEXT NOT NULL,                 -- e.g., 'div_safety_v1'
  pricing_pack_id TEXT NOT NULL REFERENCES pricing_pack(id) ON DELETE RESTRICT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (portfolio_id, security_id, rating_type, asof_date)
);

SELECT create_hypertable('ratings', 'asof_date', if_not_exists => TRUE);

-- RLS
ALTER TABLE ratings ENABLE ROW LEVEL SECURITY;
CREATE POLICY ratings_rw ON ratings
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Buffett quality ratings (0-10 scale)
**RLS**: ✅ Enabled
**Hypertable**: ✅ Time-series optimized
**Explainability**: `inputs_json` + `method` version for provenance

---

#### `news_impact`
```sql
CREATE TABLE news_impact (
  portfolio_id  UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  asof_ts       TIMESTAMPTZ NOT NULL,
  article_id    TEXT NOT NULL,
  entities_json JSONB NOT NULL,
  sentiment     NUMERIC(8,4) NOT NULL,
  impact_score  NUMERIC(8,4) NOT NULL,    -- sentiment × portfolio weight
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (portfolio_id, article_id)
);

CREATE INDEX idx_news_impact_time ON news_impact (portfolio_id, asof_ts DESC);

-- RLS
ALTER TABLE news_impact ENABLE ROW LEVEL SECURITY;
CREATE POLICY news_rw ON news_impact
  USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)));
```
**Purpose**: Portfolio-weighted news sentiment impact
**RLS**: ✅ Enabled
**Used by**: News impact pattern

---

### 6. Alerts & Notifications

#### `alerts`
```sql
CREATE TABLE alerts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  type            alert_type_enum NOT NULL,
  condition_json  JSONB NOT NULL,
  notify_inapp    BOOLEAN NOT NULL DEFAULT TRUE,
  notify_email    BOOLEAN NOT NULL DEFAULT FALSE,
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  cooldown_minutes INT DEFAULT 15,                  -- Migration 001
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_alerts_user_active ON alerts (user_id, active);

-- RLS
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY alerts_rw ON alerts
  USING (user_id::text = current_setting('app.user_id', true));
```
**Purpose**: Alert definitions (conditions + delivery preferences)
**RLS**: ✅ Enabled
**Migration 001 adds**: `cooldown_minutes` (rate limiting)

---

#### `notifications`
```sql
CREATE TABLE notifications (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  alert_id     UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  payload_json JSONB NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  read         BOOLEAN NOT NULL DEFAULT FALSE
);

-- Dedupe: One notification per alert per day
CREATE UNIQUE INDEX uq_notify_user_alert_day
  ON notifications (user_id, alert_id, (date_trunc('day', created_at)));

CREATE INDEX idx_notify_user_unread ON notifications (user_id, read, created_at DESC);

-- RLS
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY notify_rw ON notifications
  USING (user_id::text = current_setting('app.user_id', true));
```
**Purpose**: Delivered notifications (deduped)
**RLS**: ✅ Enabled
**Deduplication**: Unique index prevents multiple notifications per alert per day

---

### 7. Knowledge Graph (Migration 005)

#### `kg_nodes`
```sql
CREATE TABLE kg_nodes (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type       TEXT NOT NULL CHECK (type IN (
    'macro_var', 'regime', 'factor', 'sector', 'company', 'instrument',
    'pattern', 'series_id', 'event', 'analysis_snapshot'
  )),
  data_json  JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_kg_nodes_type ON kg_nodes (type);
CREATE INDEX idx_kg_nodes_data ON kg_nodes USING GIN (data_json);
```
**Purpose**: Knowledge graph nodes (patterns, analysis snapshots, macro vars)
**RLS**: Not enabled (global reference)
**Migration**: 005

---

#### `kg_edges`
```sql
CREATE TABLE kg_edges (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id     UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
  target_id     UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
  relation      TEXT NOT NULL CHECK (relation IN (
    'influences', 'sensitive_to', 'belongs_to', 'hedged_by',
    'derived_from', 'computed_by', 'correlates_with'
  )),
  weight        NUMERIC(8,4),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source_id, target_id, relation)
);

CREATE INDEX idx_kg_edges_source ON kg_edges (source_id, relation);
CREATE INDEX idx_kg_edges_target ON kg_edges (target_id, relation);
```
**Purpose**: Knowledge graph edges (relationships)
**RLS**: Not enabled (global reference)
**Migration**: 005

---

## RLS Policy Template

**Pattern for all portfolio-scoped tables**:

```sql
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

CREATE POLICY {table_name}_rw ON {table_name}
  USING (portfolio_id IN (
    SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)
  ))
  WITH CHECK (portfolio_id IN (
    SELECT id FROM portfolios WHERE user_id::text = current_setting('app.user_id', true)
  ));
```

**Tables with RLS**:
- `portfolios`
- `lots`
- `transactions`
- `portfolio_daily_values`
- `portfolio_metrics`
- `currency_attribution`
- `factor_exposures`
- `scenario_runs`
- `ratings`
- `news_impact`
- `alerts`
- `notifications`
- `reconciliations`
- `analytics_events`
- `audit_log`

**Tables WITHOUT RLS** (global references):
- `users`
- `benchmarks`
- `securities`
- `pricing_pack`
- `prices`
- `fx_rates`
- `benchmark_returns`
- `macro_regime_snapshots`
- `kg_nodes`
- `kg_edges`
- `provider_rights`
- `dlq_jobs`

---

## Migration Checklist

### Migration 001: Reproducibility Enhancements (Week 0.5)
- [ ] `pricing_pack.ledger_commit_hash`
- [ ] `pricing_pack.is_fresh`
- [ ] `portfolios.ledger_path`
- [ ] `transactions.ledger_tx_id`
- [ ] `alerts.cooldown_minutes`
- [ ] `analytics_events.trace_id`
- [ ] `audit_log.trace_id`

### Migration 002: Reconciliation Tracking (Week 0.5)
- [ ] `reconciliations` table with RLS

### Migration 003: Portfolio Daily Values (Sprint 1)
- [ ] `portfolio_daily_values` hypertable with RLS
- [ ] Continuous aggregate: `ca_portfolio_7d_avg_value`

### Migration 004: Benchmark Returns (Sprint 1)
- [ ] `benchmark_returns` hypertable
- [ ] Continuous aggregate: `ca_portfolio_rolling_beta_30d`

### Migration 005: Knowledge Graph (Sprint 3)
- [ ] `kg_nodes` table
- [ ] `kg_edges` table
- [ ] Helper functions: `kg_neighbors()`, `kg_reverse_neighbors()`

---

## Query Best Practices

### Performance Rules

1. **Always filter by partition key first** (hypertables):
   ```sql
   -- GOOD
   SELECT * FROM portfolio_metrics
   WHERE portfolio_id = :id AND asof_date > :start_date;

   -- BAD (no partition key)
   SELECT * FROM portfolio_metrics WHERE twr > 0.05;
   ```

2. **Use indexes**:
   ```sql
   -- GOOD (uses idx_prices_pack_sec)
   SELECT close FROM prices
   WHERE pricing_pack_id = :pack_id AND security_id = :sec_id;
   ```

3. **Leverage continuous aggregates**:
   ```sql
   -- Use pre-computed view instead of raw calculation
   SELECT * FROM ca_portfolio_rolling_vol WHERE portfolio_id = :id;
   ```

4. **RLS context MUST be set**:
   ```python
   await db.execute(f"SET LOCAL app.user_id = '{user_id}'")
   ```

### Multi-Currency Patterns

**Valuation (current value)**:
```sql
SELECT l.qty_open * p.close * fx.rate AS value_base
FROM lots l
JOIN prices p ON l.security_id = p.security_id AND p.pricing_pack_id = :pack_id
JOIN fx_rates fx ON p.currency = fx.base_ccy AND fx.pricing_pack_id = :pack_id
WHERE l.portfolio_id = :portfolio_id AND fx.quote_ccy = :base_ccy;
```

**Realized P&L (trade FX vs exit FX)**:
```sql
SELECT
  (exit_price * exit_fx.rate - entry_price * entry_fx.rate) AS price_pl,
  entry_price * (exit_fx.rate - entry_fx.rate) AS fx_pl
FROM lots l
JOIN fx_rates entry_fx ON l.trade_fx_rate_id = entry_fx.id
JOIN fx_rates exit_fx ON ...;
```

**ADR Dividends with Pay-Date FX** (Critical for accuracy):

**Problem**: American Depositary Receipts (ADRs) declare dividends on ex-date but **pay on pay-date** with different FX rate. Must track gross, withholding tax, and net amounts separately.

**Solution** (`transactions` table ADR-specific fields):
```sql
-- transactions table (extended for ADR dividends)
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  security_id UUID NOT NULL REFERENCES securities(id) ON DELETE RESTRICT,
  type TEXT NOT NULL CHECK (type IN ('buy','sell','dividend','split','transfer','fee','coupon')),

  -- Standard fields
  qty NUMERIC(18,8),
  price_ccy NUMERIC(28,10),
  price_base NUMERIC(28,10),
  trade_ccy TEXT,
  trade_fx_rate_id UUID REFERENCES fx_rates(id),

  -- ADR-specific dividend fields
  gross_ccy NUMERIC(28,10),          -- Gross dividend in dividend currency
  gross_base NUMERIC(28,10),         -- Gross dividend in base currency
  withholding_ccy NUMERIC(28,10),    -- Withholding tax in dividend currency
  withholding_base NUMERIC(28,10),   -- Withholding tax in base currency
  net_ccy NUMERIC(28,10),            -- Net dividend (gross - withholding) in div currency
  net_base NUMERIC(28,10),           -- Net dividend in base currency
  pay_date DATE,                     -- Dividend payment date
  pay_fx_rate_id UUID REFERENCES fx_rates(id),  -- FX rate at pay_date

  txn_ts TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- CHECK constraint ensures pay_fx_rate_id present for dividends
  CONSTRAINT dividend_pay_fx CHECK (
    NOT(type IN ('dividend','coupon') AND pay_fx_rate_id IS NULL)
  )
);
```

**Example** (Apple ADR dividend to CAD portfolio):
```sql
-- Step 1: Insert pay-date FX rate (2024-08-15, pay date)
INSERT INTO fx_rates (id, asof_ts, base_ccy, quote_ccy, rate, source, policy, pricing_pack_id)
VALUES (
  'FX_2024-08-15_USDCAD',
  '2024-08-15T21:00:00Z',
  'USD',
  'CAD',
  1.36,
  'WM_REUTERS',
  'WM4PM',
  'PP_2024-08-15'
);

-- Step 2: Record dividend transaction
INSERT INTO transactions (
  portfolio_id, security_id, type,
  gross_ccy, gross_base,
  withholding_ccy, withholding_base,
  net_ccy, net_base,
  pay_date, pay_fx_rate_id,
  trade_ccy, txn_ts
)
VALUES (
  'P1',                          -- Portfolio
  'SEC_AAPL',                    -- Apple
  'dividend',
  25.00,                         -- Gross: $25.00 USD (100 shares × $0.25)
  34.00,                         -- Gross in CAD: $25 × 1.36 = $34.00
  3.75,                          -- Withholding: $25 × 15% = $3.75 USD
  5.10,                          -- Withholding in CAD: $3.75 × 1.36 = $5.10
  21.25,                         -- Net: $25 - $3.75 = $21.25 USD
  28.90,                         -- Net in CAD: $21.25 × 1.36 = $28.90
  '2024-08-15',                  -- Pay date
  'FX_2024-08-15_USDCAD',        -- Pay-date FX rate (NOT ex-date FX!)
  'USD',
  '2024-08-15T20:00:00Z'
);
```

**Key Insight**:
- Ex-date FX (2024-08-01) might be 1.34 USD/CAD
- Pay-date FX (2024-08-15) is 1.36 USD/CAD ← **USE THIS ONE**
- Net dividend in CAD = **$28.90** (not $28.48 if using ex-date FX)
- **Accuracy impact**: 42¢ per transaction (significant at scale)

**Validation Query**:
```sql
-- Verify all dividends have pay_fx_rate_id (should return 0)
SELECT id, security_id, type, pay_date, pay_fx_rate_id
FROM transactions
WHERE type IN ('dividend','coupon')
  AND pay_fx_rate_id IS NULL;
```

**Seed Data Reference**: See `DawsOS_Seeding_Plan` Section 3.3 for ADR dividend test case.

---

## Data Integrity Rules

### Constraints

1. **No orphans**: All `pricing_pack_id` foreign keys use `ON DELETE RESTRICT`
2. **RLS coverage**: All portfolio-scoped tables have RLS policies
3. **Immutability**: `pricing_pack` rows never updated (use `superseded_by`)
4. **Deduplication**: `notifications` unique constraint prevents duplicates
5. **ADR safety**: CHECK constraint on `transactions` enforces `pay_fx_rate_id` for dividends

### Validation Queries

```sql
-- Check for RLS coverage (should return 0)
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE '%portfolio%'
  AND tablename NOT IN (
    SELECT tablename FROM pg_policies WHERE schemaname = 'public'
  );

-- Check for orphaned pricing pack references (should return 0)
SELECT COUNT(*) FROM portfolio_metrics pm
WHERE NOT EXISTS (SELECT 1 FROM pricing_pack pp WHERE pp.id = pm.pricing_pack_id);

-- Check for superseded packs still marked fresh (should return 0)
SELECT COUNT(*) FROM pricing_pack WHERE superseded_by IS NOT NULL AND is_fresh = TRUE;
```

---

## Usage by Other Agents

### For LEDGER_ARCHITECT
- **Consult**: `lots`, `transactions`, `reconciliations`, `portfolio_daily_values`
- **Multi-currency**: Use `trade_fx_rate_id`, `pay_fx_rate_id` correctly
- **Migration**: Apply 001, 002, 003

### For METRICS_ARCHITECT
- **Consult**: `portfolio_daily_values`, `portfolio_metrics`, `currency_attribution`, `factor_exposures`
- **Hypertables**: Write to time-series tables efficiently
- **Migration**: Apply 003, 004

### For MACRO_ARCHITECT
- **Consult**: `factor_exposures`, `macro_regime_snapshots`, `scenario_runs`
- **Knowledge Graph**: Use `kg_nodes`, `kg_edges` (Migration 005)

### For RATINGS_ARCHITECT
- **Consult**: `ratings`, `securities`
- **Explainability**: Always populate `inputs_json` + `method`

### For PROVIDER_INTEGRATOR
- **Consult**: `prices`, `fx_rates`, `benchmark_returns`
- **Immutability**: Never update `pricing_pack` rows

### For UI_ARCHITECT
- **Consult**: All analytics tables
- **RLS**: Ensure UI sets `app.user_id` context via API

### For TEST_ARCHITECT
- **Validation**: Use validation queries above
- **Golden tests**: Compare against Beancount ledger ±1bp
- **Security tests**: IDOR fuzz via random portfolio UUIDs

---

## Handoff

Upon request from any agent, provide:
1. Exact table DDL
2. RLS policy template
3. Query patterns for specific use case
4. Migration script if needed

**Contact**: Reference this document in any agent implementation
**Status**: Active - Updated with all migrations
**Last Updated**: 2025-10-21
