# DawsOS Database Documentation

**Version:** 2.1 (Phase 2 Data Layer Improvements)  
**Last Updated:** November 3, 2025  
**Database:** PostgreSQL 14+ with TimescaleDB Extension  
**Status:** ✅ PRODUCTION READY (33 Tables Verified)

---

## 🚀 Phase 2 Data Layer Improvements (November 3, 2025)

### Completed Refactoring
1. **Fixed Duplicate Capability Registration** - Removed charts.overview from ChartsAgent to prevent conflicts with FinancialAnalyst
2. **Fixed Nested Storage Pattern** - Removed smart unwrapping in pattern_orchestrator.py to prevent double-nesting (result.result.data bug)
3. **Improved Corporate Actions Endpoint** - Made portfolio_id required with UUID validation
4. **Cleaned Agent Code** - Removed unused imports across all 10 agent files
5. **Verified Pattern Execution** - All patterns working correctly with clean data flow

### Architecture Stability Achieved
- ✅ 9 agents successfully initialized with unique capabilities
- ✅ Pattern orchestrator consistently stores results without unwrapping
- ✅ No duplicate capability registration errors  
- ✅ Corporate actions endpoint returns honest empty data with proper validation
- ✅ All 12 patterns execute without errors

---

## 📊 Database Overview

DawsOS uses PostgreSQL with TimescaleDB for time-series data optimization. The database employs a hybrid pattern of real-time computation and cached storage for optimal performance.

### Key Statistics
- **Total Tables:** 33 (including 6+ hypertables)
- **Total Views:** 3 (latest_ledger_snapshot, portfolio_currency_attributions, v_derived_indicators)
- **Core Domain Tables:** 15
- **System/Support Tables:** 18
- **Connection Method:** Cross-module pool using `sys.modules` storage

### Architecture Pattern
- **Compute-First:** Services calculate data on-demand by default
- **Cache-Optional:** Tables like `factor_exposures` and `currency_attribution` exist for future caching
- **Hybrid Approach:** Can switch between computed and stored based on performance needs

---

## 🗄️ Complete Table Inventory (Verified via SQL Inspection)

### Core Portfolio Management Tables

#### 1. **portfolios**
Primary portfolio definition table.
```sql
- id: UUID (Primary Key)
- name: TEXT NOT NULL
- base_currency: TEXT NOT NULL (e.g., 'USD', 'CAD')
- owner_id: UUID REFERENCES users(id)
- created_at: TIMESTAMP WITH TIME ZONE
- updated_at: TIMESTAMP WITH TIME ZONE
```

#### 2. **lots** 
Tax lot tracking for portfolio positions.
```sql
- id: UUID (Primary Key)
- portfolio_id: UUID REFERENCES portfolios(id)
- security_id: UUID REFERENCES securities(id)
- symbol: TEXT
- qty_open: NUMERIC(20,8) -- Open quantity (UI shows as "quantity")
- qty_original: NUMERIC(20,8) -- Original purchase quantity
- cost_basis: NUMERIC(20,2)
- acquisition_date: DATE
- currency: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
```
**Note:** Field naming issue - `qty_open` in DB becomes `quantity` in UI

#### 3. **transactions**
All portfolio transactions (buy, sell, dividend, etc).
```sql
- id: UUID (Primary Key)
- portfolio_id: UUID REFERENCES portfolios(id)
- transaction_type: TEXT -- 'BUY', 'SELL', 'DIVIDEND', etc.
- security_id: UUID REFERENCES securities(id)
- symbol: TEXT
- transaction_date: DATE
- settlement_date: DATE
- quantity: NUMERIC(20,8)
- price: NUMERIC(20,8)
- amount: NUMERIC(20,2)
- currency: TEXT
- fee: NUMERIC(20,2)
- narration: TEXT
- source: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
```

#### 4. **securities**
Master security reference data.
```sql
- id: UUID (Primary Key)
- symbol: TEXT UNIQUE
- name: TEXT
- security_type: TEXT -- 'EQUITY', 'BOND', 'ETF', etc.
- currency: TEXT
- sector: TEXT
- industry: TEXT
- exchange: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
- updated_at: TIMESTAMP WITH TIME ZONE
```

---

### Pricing & Market Data Tables

#### 5. **pricing_packs**
Consistent pricing snapshots for point-in-time valuation.
```sql
- id: TEXT (Primary Key) -- e.g., 'PP_2025-11-03'
- date: DATE NOT NULL
- status: TEXT -- 'PENDING', 'COMPLETE', 'FAILED'
- securities_count: INTEGER
- fx_pairs_count: INTEGER
- created_at: TIMESTAMP WITH TIME ZONE
```

#### 6. **prices**
Security prices tied to pricing packs.
```sql
- pricing_pack_id: TEXT REFERENCES pricing_packs(id)
- security_id: UUID REFERENCES securities(id)
- date: DATE
- open: NUMERIC(20,8)
- high: NUMERIC(20,8)
- low: NUMERIC(20,8)
- close: NUMERIC(20,8)
- volume: BIGINT
- currency: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (pricing_pack_id, security_id)
```

#### 7. **fx_rates**
Foreign exchange rates for multi-currency support.
```sql
- pricing_pack_id: TEXT REFERENCES pricing_packs(id)
- base_ccy: TEXT -- Base currency (e.g., 'CAD')
- quote_ccy: TEXT -- Quote currency (e.g., 'USD')
- rate: NUMERIC(20,8)
- source: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (pricing_pack_id, base_ccy, quote_ccy)
```
**Current Data:** 63 FX rate records (CAD/USD: 0.73, EUR/USD: 1.08)

---

### Time-Series Analytics Tables (Hypertables)

#### 8. **portfolio_daily_values** 🕐
Daily portfolio NAV tracking (TimescaleDB hypertable).
```sql
- portfolio_id: UUID
- date: DATE
- nav: NUMERIC(20,2) -- Net Asset Value
- cash: NUMERIC(20,2)
- securities_value: NUMERIC(20,2)
- total_pl: NUMERIC(20,2)
- daily_pl: NUMERIC(20,2)
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (portfolio_id, date)
-- Hypertable on 'date' column
```

#### 9. **portfolio_metrics** 🕐
Performance metrics time-series (TimescaleDB hypertable).
```sql
- portfolio_id: UUID
- date: DATE
- metric_type: TEXT -- 'RETURN', 'SHARPE', 'VOLATILITY', etc.
- value: NUMERIC(20,8)
- period: TEXT -- '1D', '1M', '1Y', etc.
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (portfolio_id, date, metric_type, period)
-- Hypertable on 'date' column
```

#### 10. **portfolio_cash_flows** 🕐
Cash flow tracking for MWR calculations (TimescaleDB hypertable).
```sql
- portfolio_id: UUID
- date: DATE
- flow_type: TEXT -- 'INFLOW', 'OUTFLOW', 'DIVIDEND'
- amount: NUMERIC(20,2)
- currency: TEXT
- description: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (portfolio_id, date, flow_type)
-- Hypertable on 'date' column
```

#### 11. **macro_indicators** 🕐
Economic indicators for regime detection (TimescaleDB hypertable).
```sql
- indicator_name: TEXT -- e.g., 'GDP_GROWTH', 'INFLATION'
- date: DATE
- value: NUMERIC(20,8)
- unit: TEXT
- source: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (indicator_name, date)
-- Hypertable on 'date' column
-- Contains 102 rows of active indicator data
```

#### 12. **currency_attribution** 🕐
Currency performance attribution (TimescaleDB hypertable).
```sql
- portfolio_id: UUID
- asof_date: DATE
- pricing_pack_id: TEXT REFERENCES pricing_packs(id)
- local_return: NUMERIC(12,8) NOT NULL
- fx_return: NUMERIC(12,8) NOT NULL
- interaction_return: NUMERIC(12,8) NOT NULL
- total_return: NUMERIC(12,8) NOT NULL
- base_return_actual: NUMERIC(12,8)
- error_bps: NUMERIC(12,8)
- attribution_by_currency: JSONB
- base_currency: TEXT NOT NULL
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (portfolio_id, asof_date)
-- NOTE: Table exists but service computes from lots directly
```
**Architecture Note:** Currently computed on-demand, table for future caching

#### 13. **factor_exposures** 🕐
Portfolio factor exposures for risk analysis (TimescaleDB hypertable).
```sql
- portfolio_id: UUID
- asof_date: DATE
- pricing_pack_id: TEXT REFERENCES pricing_packs(id)
- beta_real_rate: NUMERIC(12,8)
- beta_inflation: NUMERIC(12,8)
- beta_credit: NUMERIC(12,8)
- beta_fx: NUMERIC(12,8)
- beta_market: NUMERIC(12,8)
- beta_size: NUMERIC(12,8)
- beta_value: NUMERIC(12,8)
- beta_momentum: NUMERIC(12,8)
- var_factor: NUMERIC(12,8)
- var_idiosyncratic: NUMERIC(12,8)
- r_squared: NUMERIC(12,8)
- factor_contributions: JSONB
- estimation_window_days: INTEGER
- benchmark_id: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (portfolio_id, asof_date)
-- NOTE: Table exists but RiskService computes on-demand
```
**Architecture Note:** Currently computed on-demand, table for future caching

---

### Risk & Scenario Analysis Tables

#### 14. **regime_history**
Historical economic regime detection results.
```sql
- id: UUID (Primary Key)
- date: DATE
- regime: TEXT -- 'GOLDILOCKS', 'STAGFLATION', etc.
- confidence: NUMERIC(5,4)
- indicators_json: JSONB
- zscores_json: JSONB
- regime_scores_json: JSONB
- created_at: TIMESTAMP WITH TIME ZONE
-- Contains 2 rows of regime data
```

#### 15. **scenario_shocks**
Shock scenarios for stress testing.
```sql
- scenario_id: TEXT (Primary Key)
- factor_name: TEXT
- shock_size: NUMERIC(12,8)
- shock_type: TEXT -- 'ABSOLUTE', 'RELATIVE'
- description: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
```

#### 16. **position_factor_betas**
Security-level factor exposures.
```sql
- security_id: UUID REFERENCES securities(id)
- asof_date: DATE
- beta_real_rates: NUMERIC(12,8)
- beta_inflation: NUMERIC(12,8)
- beta_credit: NUMERIC(12,8)
- beta_usd: NUMERIC(12,8)
- beta_equity: NUMERIC(12,8)
- estimation_error: NUMERIC(12,8)
- created_at: TIMESTAMP WITH TIME ZONE
PRIMARY KEY (security_id, asof_date)
```

#### 17. **cycle_phases**
Economic cycle phase tracking.
```sql
- id: UUID (Primary Key)
- cycle_type: TEXT -- 'STDC', 'LTDC', 'EMPIRE', 'CIVIL'
- date: DATE
- phase: TEXT
- score: NUMERIC(5,4)
- indicators: JSONB
- created_at: TIMESTAMP WITH TIME ZONE
```

---

### System & Support Tables

#### 18. **users**
Application user accounts.
```sql
- id: UUID (Primary Key)
- email: TEXT UNIQUE NOT NULL
- password_hash: TEXT NOT NULL
- role: TEXT -- 'ADMIN', 'MANAGER', 'USER', 'VIEWER'
- created_at: TIMESTAMP WITH TIME ZONE
- last_login: TIMESTAMP WITH TIME ZONE
```

#### 19. **audit_log**
Comprehensive audit trail.
```sql
- id: SERIAL (Primary Key)
- user_id: UUID REFERENCES users(id)
- action: TEXT
- entity_type: TEXT
- entity_id: UUID
- changes: JSONB
- ip_address: INET
- user_agent: TEXT
- created_at: TIMESTAMP WITH TIME ZONE
```

#### 20-23. **Alert System Tables**
```sql
alerts               -- Alert definitions
alert_deliveries     -- Delivery tracking
alert_retries       -- Retry management  
alert_dlq           -- Alert dead letter queue
```

#### 24. **dlq**
General dead letter queue.
```sql
- id: UUID (Primary Key)
- queue_name: TEXT
- message: JSONB
- error: TEXT
- retry_count: INTEGER
- created_at: TIMESTAMP WITH TIME ZONE
-- Currently empty (normal state)
```

#### 25. **rating_rubrics**
Quality rating criteria definitions.
```sql
- id: UUID (Primary Key)
- rating_type: TEXT -- 'MOAT', 'DIVIDEND_SAFETY', 'RESILIENCE'
- criteria: JSONB
- weights: JSONB
- created_at: TIMESTAMP WITH TIME ZONE
-- ⚠️ Currently empty - service uses hardcoded fallback weights
```

#### 26-27. **Operational Tables**
```sql
rebalance_suggestions    -- Portfolio rebalancing recommendations
reconciliation_results   -- Data reconciliation audit
```

#### 28-30. **Ledger System Tables**
```sql
holdings                 -- Current holdings snapshot
ledger_snapshots        -- Point-in-time ledger state
ledger_transactions     -- Detailed ledger records
```

---

## 📐 Database Views

#### 1. **latest_ledger_snapshot**
Current ledger state per portfolio.

#### 2. **portfolio_currency_attributions**
Aggregated currency attribution across portfolios.

#### 3. **v_derived_indicators**
Computed macro indicators (real interest rate, term spread, etc.)

---

## 🔄 Data Flow & Architecture Patterns

### Computation vs Storage Strategy

```mermaid
graph LR
    Request[API Request] --> Cache{Cached?}
    Cache -->|Yes, Fresh| Return[Return Cached]
    Cache -->|No/Stale| Compute[Compute Fresh]
    Compute --> Store[Store Result]
    Store --> Return
```

**Current Implementation:**
| Pattern | Tables | Status |
|---------|--------|--------|
| **Computed On-Demand** | factor_exposures, currency_attribution | Services calculate fresh |
| **Stored & Retrieved** | portfolio_metrics, portfolio_daily_values | Written and queried |
| **Hybrid (Future)** | Could cache computed results with TTL | Not implemented |

### Anti-Patterns & Refactoring Needs

#### 1. **Unused Cache Tables**
- **Issue:** Tables created but not used (factor_exposures, currency_attribution)
- **Solution:** Implement TTL-based caching or remove tables

#### 2. **Field Name Transformations**
- **Issue:** `qty_open` → `qty` → `quantity` (different at each layer)
- **Solution:** Standardize field names across layers

#### 3. **Missing Data Seeds**
- **Issue:** `rating_rubrics` empty (fallback to hardcoded)
- **Solution:** Seed with proper rubric data

#### 4. **Service Layer Mixing**
- **Issue:** Services both compute AND access DB directly
- **Solution:** Separate compute logic from storage logic

---

## 🚀 Recommended Refactoring Strategy

### Phase 1: Stabilize Current Patterns
1. **Document Intent:** Clarify which tables are for caching vs active use
2. **Standardize Names:** Create field mapping layer for consistent naming
3. **Seed Missing Data:** Populate rating_rubrics and other empty tables

### Phase 2: Implement Clear Patterns
```python
# Proposed Three-Layer Pattern
class CurrencyAttributionService:
    def compute(self, portfolio_id, pack_id) -> Dict:
        """Pure computation, no DB access"""
        
    def store(self, attribution_data) -> None:
        """Save to currency_attribution table"""
        
    def get_or_compute(self, portfolio_id, pack_id) -> Dict:
        """Cache-first strategy with TTL"""
```

### Phase 3: Optimize Performance
1. **Add TTL columns** to cache tables
2. **Implement cache invalidation** on data changes
3. **Monitor query patterns** and add indexes

---

## 📊 Current Data Population

| Table | Row Count | Status | Action Needed |
|-------|-----------|--------|---------------|
| portfolios | 1 | ✅ Active | None |
| lots | 17 | ✅ Active | None |
| securities | 17 | ✅ Active | None |
| prices | 500+ | ✅ Active | None |
| fx_rates | 63 | ✅ Fixed | Monitor for new pairs |
| macro_indicators | 102 | ✅ Active | None |
| factor_exposures | 1 | ⚠️ Minimal | Decide: use or remove |
| currency_attribution | 1 | ⚠️ Minimal | Decide: use or remove |
| rating_rubrics | 0 | ❌ Empty | Seed data needed |
| regime_history | 2 | ⚠️ Minimal | Build history |

---

## 🔐 Database Configuration

### Connection Management

**Pattern:** Cross-module pool storage
```python
# Register pool (in combined_server.py)
from backend.app.db.connection import register_external_pool
register_external_pool(pool)

# Access pool (in any module)
from backend.app.db.connection import get_db_pool
pool = get_db_pool()  # Returns same pool across all modules
```

**Why:** Python creates separate module instances on import. Solution: Store pool in `sys.modules['__dawsos_db_pool_storage__']`

### Connection String
```bash
DATABASE_URL="postgresql://user:password@host:5432/dawsos"
```

### Required Extensions
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
```

---

## 🔧 Setup & Maintenance

### Initial Setup
```bash
# Create database
createdb dawsos

# Enable TimescaleDB
psql -d dawsos -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"

# Run migrations in order
psql -d dawsos < backend/db/migrations/001_core_schema.sql
psql -d dawsos < backend/db/migrations/002_seed_data.sql
psql -d dawsos < backend/db/migrations/003_create_portfolio_metrics.sql
# ... continue with all migrations
```

### Performance Optimization

**Critical Indexes:**
```sql
-- Frequently queried patterns
CREATE INDEX idx_lots_portfolio_open ON lots(portfolio_id) WHERE qty_open > 0;
CREATE INDEX idx_prices_security_pack ON prices(security_id, pricing_pack_id);
CREATE INDEX idx_fx_rates_pack ON fx_rates(pricing_pack_id);

-- Time-series optimization
CREATE INDEX idx_portfolio_values_date ON portfolio_daily_values(date DESC);
CREATE INDEX idx_macro_indicators_date ON macro_indicators(date DESC);
```

**Hypertable Compression:**
```sql
-- Enable compression for older data
SELECT add_compression_policy('portfolio_daily_values', INTERVAL '30 days');
SELECT add_compression_policy('macro_indicators', INTERVAL '90 days');
```

---

## ⚠️ Known Issues & Action Items

### Critical Issues
1. **Empty rating_rubrics** - Blocks customization of rating calculations
2. **Unused cache tables** - Wastes resources, confuses architecture
3. **Field naming inconsistency** - Creates confusion across layers

### Improvement Opportunities
1. **Implement caching strategy** with TTL for computed data
2. **Separate compute from storage** in service layer
3. **Standardize response format** across all endpoints
4. **Add monitoring** for cache hit rates

### Architecture Decisions Needed
1. **Cache Strategy:** When to compute vs retrieve?
2. **Table Usage:** Keep unused tables for future or remove?
3. **Data Freshness:** What's acceptable staleness for each data type?

---

## 📚 Migration & Troubleshooting

### Migration Files Location
`backend/db/migrations/` - Sequential numbered files

### Common Issues

**"Database connection failed"**
- Check DATABASE_URL environment variable
- Verify PostgreSQL is running
- Ensure pool is registered

**"Table already exists"**
- Migration already run, check with `\dt`

**"Missing table"**
- Run migrations in order (001, 002, 003...)

**"Pool registration issue"**
- Ensure pool registered in combined_server.py
- Check sys.modules['__dawsos_db_pool_storage__']

---

## 🎯 Summary

The DawsOS database is **more complete than previously documented**, with 33 tables implemented. The main architectural challenge is not missing tables, but rather:

1. **Unclear computation vs storage patterns** - Some tables exist but aren't used
2. **Inconsistent field naming** - Different names at each layer
3. **Missing seed data** - Some tables empty despite being referenced

The system is **production-ready** but would benefit from:
- Clear caching strategy implementation
- Service layer refactoring for separation of concerns
- Standardization of field names and response formats

**Last Validated:** November 3, 2025 via direct SQL inspection  
**Validation Method:** Direct database queries against running system  
**Total Tables Confirmed:** 33 (all structures verified)