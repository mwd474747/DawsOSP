# Database Data Requirements

**Date:** November 2, 2025  
**Purpose:** Document what data is required in the database for each system to work  
**Status:** 📋 ANALYSIS ONLY (No Code Changes)

---

## 📊 Executive Summary

This document outlines the **minimum data requirements** for each system/agent/pattern to function correctly. It covers:
- **Required Tables** - Database tables that must exist
- **Required Records** - Minimum data records needed
- **Data Dependencies** - What data must exist before other data can be created
- **System-Specific Requirements** - Data needed for each agent/pattern

---

## 🗄️ Core Database Tables

### ✅ Required Core Tables (13 tables actively used)

#### 1. **users** (Authentication & User Management)
**Required:** ✅ **YES** - Must exist for authentication  
**Initial Data:** At least 1 user record  
**Dependencies:** None (foundation table)

**Minimum Required:**
- `id` (UUID) - User identifier
- `email` - User email (for login)
- `password_hash` - Hashed password (for JWT auth)
- `default_portfolio_id` (optional) - Default portfolio UUID

**Usage:**
- Authentication (JWT tokens)
- User context (RLS isolation)
- Default portfolio selection

---

#### 2. **portfolios** (Portfolio Management)
**Required:** ✅ **YES** - Core table for all portfolio operations  
**Initial Data:** At least 1 portfolio record  
**Dependencies:** Requires `users` table (foreign key)

**Minimum Required:**
- `id` (UUID) - Portfolio identifier
- `user_id` (UUID) - Owner user (foreign key to `users`)
- `name` - Portfolio name
- `currency` - Base currency (e.g., 'CAD', 'USD')
- `created_at` - Creation timestamp

**Usage:**
- All portfolio patterns require `portfolio_id`
- RLS isolation (users only see their portfolios)
- Portfolio context for all operations

**Critical:** **ALL 11 portfolio patterns require at least 1 portfolio record**

---

#### 3. **securities** (Security Master Data)
**Required:** ✅ **YES** - Required for holdings, pricing, ratings  
**Initial Data:** At least 1 security record (for testing)  
**Dependencies:** None (foundation table)

**Minimum Required:**
- `id` (UUID) - Security identifier
- `symbol` - Ticker symbol (e.g., 'AAPL', 'MSFT')
- `name` - Security name
- `currency` - Trading currency
- `security_type` - Type (e.g., 'EQUITY', 'ETF')
- `sector` (optional) - Sector classification
- `exchange` (optional) - Exchange code

**Usage:**
- Holdings reference (`lots` table)
- Pricing lookups (`prices` table)
- Ratings analysis (`buffett_checklist` pattern)
- Portfolio attribution

**Critical:** **All portfolio operations require securities to exist**

---

#### 4. **lots** (Position Holdings)
**Required:** ✅ **YES** - Required for portfolio operations  
**Initial Data:** At least 1 lot record (for testing)  
**Dependencies:** Requires `portfolios` and `securities` tables

**Minimum Required:**
- `id` (UUID) - Lot identifier
- `portfolio_id` (UUID) - Portfolio (foreign key)
- `security_id` (UUID) - Security (foreign key)
- `quantity` - Share quantity
- `acquisition_date` - Purchase date
- `acquisition_cost` - Cost basis

**Usage:**
- `ledger.positions` capability (all portfolio patterns)
- Position valuation
- Trade proposals (optimizer)
- Portfolio metrics

**Critical:** **All portfolio patterns require positions (lots) to exist**

---

#### 5. **transactions** (Trade History)
**Required:** ✅ **YES** - Required for transaction history  
**Initial Data:** Optional (for testing)  
**Dependencies:** Requires `portfolios`, `securities` tables

**Minimum Required:**
- `id` (UUID) - Transaction identifier
- `portfolio_id` (UUID) - Portfolio (foreign key)
- `security_id` (UUID) - Security (foreign key)
- `transaction_type` - Type ('BUY', 'SELL', 'DIVIDEND', etc.)
- `quantity` - Share quantity
- `price` - Transaction price
- `transaction_date` - Date of transaction

**Usage:**
- Transaction history page
- Audit trail
- Trade execution

---

#### 6. **pricing_packs** (Pricing Data Context)
**Required:** ✅ **YES** - Required for all portfolio valuation  
**Initial Data:** At least 1 pricing pack record  
**Dependencies:** None (but should match security prices)

**Minimum Required:**
- `id` (UUID) - Pack identifier
- `asof_date` - Pricing date
- `status` - Status ('PENDING', 'COMPLETE')
- `created_at` - Creation timestamp

**Usage:**
- All portfolio patterns require `pricing_pack_id`
- Price context for valuation
- Reproducibility (same pack = same prices)

**Critical:** **Pattern orchestrator requires `pricing_pack_id` in context**

---

#### 7. **prices** (Security Prices)
**Required:** ✅ **YES** - Required for portfolio valuation  
**Initial Data:** Prices for securities in portfolios  
**Dependencies:** Requires `securities` and `pricing_packs` tables

**Minimum Required:**
- `id` (UUID) - Price identifier
- `security_id` (UUID) - Security (foreign key)
- `pack_id` (UUID) - Pricing pack (foreign key)
- `price` - Price value
- `currency` - Price currency
- `asof_date` - Pricing date

**Usage:**
- `pricing.apply_pack` capability
- Portfolio valuation
- Position value calculations

**Critical:** **All portfolio patterns require prices for portfolio securities**

---

#### 8. **fx_rates** (Currency Exchange Rates)
**Required:** ✅ **YES** - Required for multi-currency portfolios  
**Initial Data:** FX rates for relevant currency pairs  
**Dependencies:** Requires `pricing_packs` table

**Minimum Required:**
- `id` (UUID) - Rate identifier
- `from_currency` - Source currency (e.g., 'USD')
- `to_currency` - Target currency (e.g., 'CAD')
- `rate` - Exchange rate
- `pack_id` (UUID) - Pricing pack (foreign key)
- `asof_date` - Rate date

**Usage:**
- Currency conversion
- Currency attribution (`attribution.currency` capability)
- Multi-currency portfolio valuation

**Critical:** **Currency attribution requires FX rates**

---

#### 9. **portfolio_metrics** (Daily Portfolio Metrics)
**Required:** ✅ **YES** - Required for performance calculations  
**Initial Data:** Optional (calculated by jobs)  
**Dependencies:** Requires `portfolios` table

**Minimum Required:**
- `portfolio_id` (UUID) - Portfolio (foreign key)
- `asof_date` - Metric date (TimescaleDB hypertable)
- `nav` - Net asset value
- `twr_1d`, `twr_mtd`, `twr_ytd`, `twr_1y` - Time-weighted returns
- `sharpe_1y` - Sharpe ratio

**Usage:**
- `metrics.compute_twr` capability
- Performance page
- Historical NAV tracking

**Note:** This is a TimescaleDB hypertable for time-series data

---

#### 10. **portfolio_daily_values** (NAV Time-Series)
**Required:** ✅ **YES** - Required for historical charts  
**Initial Data:** Optional (calculated by jobs)  
**Dependencies:** Requires `portfolios` table

**Minimum Required:**
- `portfolio_id` (UUID) - Portfolio (foreign key)
- `asof_date` - Value date (TimescaleDB hypertable)
- `nav` - Net asset value
- `contributions` - Cash contributions
- `withdrawals` - Cash withdrawals

**Usage:**
- Historical NAV charts
- `metrics.historical_nav` capability
- Performance visualization

**Note:** This is a TimescaleDB hypertable for time-series data

---

#### 11. **portfolio_cash_flows** (Cash Flow Tracking)
**Required:** ✅ **YES** - Required for MWR calculations  
**Initial Data:** Optional (populated by transactions)  
**Dependencies:** Requires `portfolios` table

**Minimum Required:**
- `portfolio_id` (UUID) - Portfolio (foreign key)
- `asof_date` - Flow date (TimescaleDB hypertable)
- `flow_type` - Type ('CONTRIBUTION', 'WITHDRAWAL', 'DIVIDEND')
- `amount` - Cash amount
- `currency` - Flow currency

**Usage:**
- Money-weighted return (MWR) calculations
- Cash flow analysis

**Note:** This is a TimescaleDB hypertable for time-series data

---

#### 12. **macro_indicators** (Economic Indicators)
**Required:** ✅ **YES** - Required for macro cycles analysis  
**Initial Data:** Historical indicator data  
**Dependencies:** None (but requires historical data)

**Minimum Required:**
- `id` (UUID) - Indicator identifier
- `indicator_code` - Code (e.g., 'GDP', 'UNRATE', 'CPIAUCSL')
- `value` - Indicator value
- `asof_date` - Data date (TimescaleDB hypertable)
- `source` - Data source (e.g., 'FRED')
- `frequency` - Frequency ('MONTHLY', 'QUARTERLY', 'ANNUAL')

**Usage:**
- `macro.current_cycles` capability
- `macro.detect_regime` capability
- Macro cycles dashboard
- Cycle risk analysis

**Critical:** **MacroHound agent requires macro indicator data**

**Note:** This is a TimescaleDB hypertable for time-series data

---

#### 13. **regime_history** (Macro Regime Classifications)
**Required:** ✅ **YES** - Required for regime detection  
**Initial Data:** Optional (calculated by macro agent)  
**Dependencies:** Requires `macro_indicators` table

**Minimum Required:**
- `id` (UUID) - Regime identifier
- `asof_date` - Regime date (TimescaleDB hypertable)
- `regime_type` - Type ('EXPANSION', 'RECESSION', 'STAGFLATION', etc.)
- `confidence` - Confidence score
- `indicators_used` - JSON array of indicator codes

**Usage:**
- `macro.detect_regime` capability
- Regime-based analysis
- Macro context for portfolios

**Note:** This is a TimescaleDB hypertable for time-series data

---

#### 14. **rating_rubrics** (Quality Rating Weights)
**Required:** ✅ **YES** - Required for Buffett ratings  
**Initial Data:** Rating weight configuration  
**Dependencies:** None

**Minimum Required:**
- `id` (UUID) - Rubric identifier
- `factor_name` - Factor name (e.g., 'moat_strength', 'div_safety')
- `weight` - Weight value (0-1)
- `category` - Category (e.g., 'QUALITY', 'VALUE')

**Usage:**
- `ratings.aggregate` capability
- `buffett_checklist` pattern
- Quality scoring

**Critical:** **RatingsAgent requires rating rubrics configuration**

---

### ⚠️ Optional Tables (Created but not actively queried)

#### 15. **currency_attribution** (Currency Attribution Results)
**Required:** ⚠️ **OPTIONAL** - Schema exists, service implemented  
**Initial Data:** Calculated by attribution service  
**Dependencies:** Requires `portfolios` table

**Usage:**
- `attribution.currency` capability stores results here
- Currency attribution analysis

**Note:** Service exists but may not be actively storing results

---

#### 16. **factor_exposures** (Factor Exposure Analysis)
**Required:** ⚠️ **OPTIONAL** - Schema exists, service implemented  
**Initial Data:** Calculated by factor analysis service  
**Dependencies:** Requires `portfolios` table

**Usage:**
- Future factor analysis feature
- Currently schema exists but not actively used

---

#### 17. **alerts** (Alert Definitions)
**Required:** ⚠️ **OPTIONAL** - Schema exists, but evaluation not active  
**Initial Data:** User-defined alert rules  
**Dependencies:** Requires `portfolios` table

**Usage:**
- `alerts.create_if_threshold` capability
- Alert management
- Currently schema exists but evaluation may not be active

---

#### 18. **notifications** (Alert Notifications)
**Required:** ⚠️ **OPTIONAL** - Schema exists, but not actively used  
**Initial Data:** Generated by alert evaluation  
**Dependencies:** Requires `alerts` table

---

#### 19. **audit_log** (Audit Trail)
**Required:** ⚠️ **OPTIONAL** - Schema exists, but logging not active  
**Initial Data:** Generated by audit service  
**Dependencies:** None

**Usage:**
- Audit trail logging
- Currently schema exists but logging may not be active

---

## 📋 System-Specific Data Requirements

### Pattern: `portfolio_overview`

**Required Tables:**
1. ✅ `portfolios` - At least 1 portfolio
2. ✅ `lots` - At least 1 position (lot)
3. ✅ `securities` - Securities referenced by lots
4. ✅ `pricing_packs` - At least 1 pricing pack
5. ✅ `prices` - Prices for portfolio securities
6. ✅ `fx_rates` - FX rates (if multi-currency)
7. ✅ `portfolio_metrics` - Daily metrics (for performance)
8. ✅ `portfolio_daily_values` - NAV history (for charts)

**Required Records:**
- 1+ portfolio record
- 1+ lot records (positions)
- 1+ security records (for positions)
- 1+ pricing pack record
- Price records for all portfolio securities
- FX rate records (for currency pairs used)

**Data Flow:**
1. `ledger.positions` → Queries `lots` table (needs portfolios, securities)
2. `pricing.apply_pack` → Queries `prices` table (needs pricing_packs, securities)
3. `metrics.compute_twr` → Queries `portfolio_metrics` table
4. `attribution.currency` → Queries `fx_rates` table
5. `metrics.historical_nav` → Queries `portfolio_daily_values` table

---

### Pattern: `policy_rebalance` (Optimizer)

**Required Tables:**
1. ✅ `portfolios` - At least 1 portfolio
2. ✅ `lots` - At least 1 position (lot)
3. ✅ `securities` - Securities referenced by lots
4. ✅ `pricing_packs` - At least 1 pricing pack
5. ✅ `prices` - Prices for portfolio securities
6. ✅ `rating_rubrics` - Rating weights configuration
7. ✅ `securities` - With sector/quality data (for ratings)

**Required Records:**
- 1+ portfolio record
- 1+ lot records (positions)
- 1+ security records (for positions)
- 1+ pricing pack record
- Price records for all portfolio securities
- Rating rubric records (for quality scoring)

**Data Flow:**
1. `ledger.positions` → Queries `lots` table
2. `pricing.apply_pack` → Queries `prices` table
3. `ratings.aggregate` → Queries `rating_rubrics` table + security data
4. `optimizer.propose_trades` → Uses positions, prices, ratings
5. `optimizer.analyze_impact` → Uses positions, trades

**Critical:** **Rating rubrics must exist for quality scoring**

---

### Pattern: `portfolio_cycle_risk`

**Required Tables:**
1. ✅ `portfolios` - At least 1 portfolio
2. ✅ `lots` - At least 1 position (lot)
3. ✅ `securities` - Securities referenced by lots
4. ✅ `pricing_packs` - At least 1 pricing pack
5. ✅ `prices` - Prices for portfolio securities
6. ✅ `macro_indicators` - Economic indicator data
7. ✅ `regime_history` - Regime classifications

**Required Records:**
- 1+ portfolio record
- 1+ lot records (positions)
- 1+ security records (for positions)
- 1+ pricing pack record
- Price records for all portfolio securities
- **Historical macro indicator data** (for cycle detection)
- Regime history records (for regime detection)

**Data Flow:**
1. `ledger.positions` → Queries `lots` table
2. `pricing.apply_pack` → Queries `prices` table
3. `risk.factor_exposures` → Calculates factor exposures
4. `macro.current_cycles` → Queries `macro_indicators` table
5. `risk.overlay_cycle_phases` → Uses cycles + factor exposures
6. `macro.compute_dar` → Uses cycles + portfolio data

**Critical:** **Macro indicators with historical data required for cycle detection**

---

### Pattern: `macro_cycles_overview`

**Required Tables:**
1. ✅ `macro_indicators` - Economic indicator data
2. ✅ `regime_history` - Regime classifications (optional)

**Required Records:**
- **Historical macro indicator data** (for cycle calculation)
- Indicator codes used by macro agent (GDP, UNRATE, CPIAUCSL, etc.)
- Multiple data points per indicator (time-series)

**Data Flow:**
1. `macro.current_cycles` → Queries `macro_indicators` table
2. `macro.detect_regime` → Queries `regime_history` table (optional)

**Critical:** **Macro indicators with sufficient historical data required**

---

### Pattern: `news_impact_analysis`

**Required Tables:**
1. ✅ `portfolios` - At least 1 portfolio
2. ✅ `lots` - At least 1 position (lot)
3. ✅ `securities` - Securities referenced by lots
4. ✅ `pricing_packs` - At least 1 pricing pack
5. ✅ `prices` - Prices for portfolio securities

**Required Records:**
- 1+ portfolio record
- 1+ lot records (positions)
- 1+ security records (for positions)
- 1+ pricing pack record
- Price records for all portfolio securities

**Data Flow:**
1. `ledger.positions` → Queries `lots` table
2. `pricing.apply_pack` → Queries `prices` table
3. `news.search` → External API (NewsAPI)
4. `news.compute_portfolio_impact` → Uses positions + news

**Note:** News data comes from external API, not database

---

### Pattern: `buffett_checklist`

**Required Tables:**
1. ✅ `portfolios` - At least 1 portfolio
2. ✅ `lots` - At least 1 position (lot)
3. ✅ `securities` - Securities referenced by lots
4. ✅ `rating_rubrics` - Rating weights configuration
5. ✅ `pricing_packs` - At least 1 pricing pack
6. ✅ `prices` - Prices for portfolio securities

**Required Records:**
- 1+ portfolio record
- 1+ lot records (positions)
- 1+ security records (for positions)
- 1+ pricing pack record
- Price records for all portfolio securities
- **Rating rubric records** (for quality scoring)

**Data Flow:**
1. `ledger.positions` → Queries `lots` table
2. `pricing.apply_pack` → Queries `prices` table
3. `ratings.aggregate` → Queries `rating_rubrics` table + security data

**Critical:** **Rating rubrics must exist for quality scoring**

---

## 🔗 Data Dependencies

### Dependency Chain:

```
1. users (no dependencies)
   ↓
2. portfolios (requires users.user_id)
   ↓
3. securities (no dependencies, but needed by lots)
   ↓
4. lots (requires portfolios.portfolio_id, securities.security_id)
   ↓
5. pricing_packs (no dependencies, but needed by prices)
   ↓
6. prices (requires securities.security_id, pricing_packs.pack_id)
   ↓
7. fx_rates (requires pricing_packs.pack_id)
   ↓
8. portfolio_metrics (requires portfolios.portfolio_id)
   ↓
9. portfolio_daily_values (requires portfolios.portfolio_id)
   ↓
10. portfolio_cash_flows (requires portfolios.portfolio_id)
    ↓
11. macro_indicators (no dependencies, but needed by macro cycles)
    ↓
12. regime_history (uses macro_indicators data)
    ↓
13. rating_rubrics (no dependencies, but needed by ratings)
```

---

## 📊 Minimum Viable Setup

### For Basic Portfolio Functionality:

**Required:**
1. ✅ **1 user record** - For authentication
2. ✅ **1 portfolio record** - For portfolio context
3. ✅ **1+ security records** - For holdings
4. ✅ **1+ lot records** - For positions
5. ✅ **1 pricing pack record** - For price context
6. ✅ **Price records** - For all portfolio securities
7. ✅ **FX rate records** - If multi-currency

**This enables:**
- `portfolio_overview` pattern
- `holding_deep_dive` pattern
- Basic portfolio operations

---

### For Optimizer Functionality:

**Additional Required:**
8. ✅ **Rating rubric records** - For quality scoring

**This enables:**
- `policy_rebalance` pattern
- `buffett_checklist` pattern

---

### For Macro Cycles Functionality:

**Additional Required:**
9. ✅ **Macro indicator records** - Historical economic data
10. ✅ **Regime history records** - Regime classifications (optional)

**This enables:**
- `macro_cycles_overview` pattern
- `portfolio_cycle_risk` pattern
- `macro_trend_monitor` pattern

---

### For News Analysis Functionality:

**Additional Required:**
11. ⚠️ **External API** - NewsAPI key and access

**This enables:**
- `news_impact_analysis` pattern

**Note:** News data comes from external API, not database

---

## 🔍 Seed Data Locations

### Found Seed Data:

1. **Ratings Rubrics:** `/data/seeds/ratings/` (3 JSON files)
   - Rating weight configurations
   - Quality scoring factors

2. **Macro Data:** `/data/seeds/macro/` (1 JSON file)
   - Macro indicator data
   - Economic cycle configurations

3. **Macro Cycles:** `/data/seeds/macro_cycles/` (1 JSON file)
   - Cycle state definitions

4. **Portfolios:** `/data/seeds/portfolios/` (directory exists)
   - Portfolio seed data

5. **Scenarios:** `/data/seeds/scenarios/` (3 JSON files)
   - Scenario configurations

---

## 🚨 Critical Data Dependencies

### 1. Portfolio Operations Require:
- ✅ User exists
- ✅ Portfolio exists
- ✅ At least 1 position (lot) exists
- ✅ Securities referenced by lots exist
- ✅ Pricing pack exists
- ✅ Prices for securities exist

**Without These:**
- Portfolio patterns will fail
- `ledger.positions` returns empty
- `pricing.apply_pack` fails or returns empty

---

### 2. Optimizer Requires:
- ✅ All portfolio operation requirements
- ✅ Rating rubrics exist

**Without Rating Rubrics:**
- `ratings.aggregate` returns empty or defaults
- Quality scoring doesn't work
- Optimizer may fail or produce invalid results

---

### 3. Macro Cycles Require:
- ✅ Macro indicators with historical data
- ✅ Sufficient data points per indicator (for trend calculation)

**Without Macro Indicators:**
- `macro.current_cycles` returns empty or defaults
- Cycle detection doesn't work
- Macro cycles dashboard shows no data

**Minimum Historical Data:**
- **Short-Term Debt Cycle:** Needs 5-10 years of GDP, credit data
- **Long-Term Debt Cycle:** Needs 50-75 years of debt/GDP data
- **Empire Cycle:** Needs 50+ years of military, trade data
- **Internal Order Cycle:** Needs 50+ years of inequality data

---

### 4. Currency Attribution Requires:
- ✅ FX rates exist for relevant currency pairs
- ✅ Multi-currency positions exist

**Without FX Rates:**
- `attribution.currency` fails or returns zero
- Currency breakdown shows no data

---

## 📋 Data Initialization Checklist

### Minimum Required for Application to Work:

**Foundation Tables:**
- [ ] `users` table exists with at least 1 user
- [ ] `securities` table exists (can be empty initially)
- [ ] `rating_rubrics` table exists with seed data

**Portfolio Tables:**
- [ ] `portfolios` table exists with at least 1 portfolio
- [ ] `lots` table exists with at least 1 position
- [ ] `pricing_packs` table exists with at least 1 pack
- [ ] `prices` table exists with prices for portfolio securities
- [ ] `fx_rates` table exists (if multi-currency)

**Time-Series Tables:**
- [ ] `portfolio_metrics` table exists (TimescaleDB hypertable)
- [ ] `portfolio_daily_values` table exists (TimescaleDB hypertable)
- [ ] `portfolio_cash_flows` table exists (TimescaleDB hypertable)

**Macro Tables:**
- [ ] `macro_indicators` table exists (TimescaleDB hypertable)
- [ ] `regime_history` table exists (TimescaleDB hypertable)

**Optional Tables:**
- [ ] `transactions` table exists (for transaction history)
- [ ] `currency_attribution` table exists (for attribution storage)
- [ ] `factor_exposures` table exists (for factor analysis)
- [ ] `alerts` table exists (for alert management)

---

## 🎯 System Startup Requirements

### For OptimizerPage to Work (Based on Crash Analysis):

**Required Data:**
1. ✅ User exists
2. ✅ Portfolio exists (with valid UUID)
3. ✅ At least 1 position (lot) exists
4. ✅ Securities exist for positions
5. ✅ Pricing pack exists
6. ✅ Prices exist for portfolio securities
7. ✅ Rating rubrics exist (for quality scoring)

**Data Flow:**
1. User loads OptimizerPage
2. PatternRenderer calls `policy_rebalance` pattern
3. Pattern requires `portfolio_id` → Must exist in `portfolios` table
4. Pattern calls `ledger.positions` → Queries `lots` table → Must have records
5. Pattern calls `pricing.apply_pack` → Queries `prices` table → Must have prices
6. Pattern calls `ratings.aggregate` → Queries `rating_rubrics` → Must have rubrics

**If Any Missing:**
- Pattern execution fails
- PatternRenderer receives error or empty data
- `processOptimizationData` receives incomplete data
- Division operations may produce `NaN`
- **Site crashes**

---

## 📊 Data Volume Requirements

### Minimum Data for Testing:

**Users:**
- 1 user record

**Portfolios:**
- 1 portfolio record

**Securities:**
- 5-10 security records (for diversity)

**Lots:**
- 5-10 lot records (positions)

**Pricing Packs:**
- 1 pricing pack record

**Prices:**
- Price records for all 5-10 securities

**Rating Rubrics:**
- 10-15 rubric records (for quality scoring)

**Macro Indicators:**
- 20-30 indicator codes
- 5-10 years of monthly data per indicator (~600-1,200 records per indicator)
- Total: ~12,000-36,000 indicator records

**FX Rates:**
- 3-5 currency pairs
- Daily rates for 1 year (~1,000-1,500 records)

---

## 🔍 Data Quality Requirements

### For Patterns to Work Correctly:

**Securities:**
- Must have valid `symbol` (for pricing lookups)
- Must have `currency` (for FX conversion)
- Should have `sector` (for sector allocation)

**Prices:**
- Must match `pricing_pack` date
- Must match security currency
- Must be valid numeric values

**Lots:**
- Must reference valid `portfolio_id`
- Must reference valid `security_id`
- Must have positive `quantity`
- Must have valid `acquisition_cost`

**Macro Indicators:**
- Must have consistent `indicator_code`
- Must have chronological `asof_date`
- Must have valid numeric `value`
- Must have sufficient history (5-10+ years)

---

**Last Updated:** November 2, 2025  
**Status:** 📋 ANALYSIS COMPLETE - Database Requirements Documented

