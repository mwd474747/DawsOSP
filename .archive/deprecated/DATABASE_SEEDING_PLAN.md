# Database Seeding Plan

**Date:** November 2, 2025  
**Purpose:** Comprehensive plan for seeding database with research-based, business-contextual data  
**Status:** 📋 PLANNING ONLY (No Code Changes)

---

## 📊 Executive Summary

This document outlines a comprehensive seeding plan that:
- **Uses existing research** from agent capabilities and business context
- **Respects dependencies** between data tables
- **Provides business value** for testing and demonstration
- **Enables all patterns** to work correctly

The plan is organized by **dependency order** and **business priority**.

---

## 🔗 Dependency Chain Analysis

### Foundation Layer (No Dependencies)
1. **users** - Authentication foundation
2. **securities** - Security master data (independent)
3. **rating_rubrics** - Rating configuration (independent)
4. **macro_indicators** - Economic data (independent, but needs historical data)

### Portfolio Layer (Depends on Foundation)
5. **portfolios** - Requires `users.user_id`
6. **pricing_packs** - Independent, but needed for prices
7. **prices** - Requires `securities.security_id` + `pricing_packs.pack_id`
8. **fx_rates** - Requires `pricing_packs.pack_id`
9. **lots** - Requires `portfolios.portfolio_id` + `securities.security_id`

### Transaction Layer (Depends on Portfolio)
10. **transactions** - Requires `portfolios.portfolio_id` + `securities.security_id` + optionally `lots.lot_id`

### Time-Series Layer (Depends on Portfolio)
11. **portfolio_metrics** - Requires `portfolios.portfolio_id` (calculated by jobs)
12. **portfolio_daily_values** - Requires `portfolios.portfolio_id` (calculated by jobs)
13. **portfolio_cash_flows** - Requires `portfolios.portfolio_id` (populated by transactions)
14. **regime_history** - Depends on `macro_indicators` (calculated by macro agent)

### Configuration Layer (Independent)
15. **alerts** - Requires `portfolios.portfolio_id` (user-defined)

---

## 📋 Seeding Plan by Priority

### Priority 1: Foundation Data (Required for Everything)

#### 1.1 Users (Authentication Foundation)
**Status:** ✅ **Already Seeded** (from `010_add_users_and_audit_log.sql`)

**Existing Seed Data:**
- `admin@dawsos.com` (ADMIN role, password: `admin123`)
- `user@dawsos.com` (USER role, password: `user123`)
- `michael@dawsos.com` (likely exists in production)

**Recommendation:**
- ✅ Keep existing seeds
- ✅ Document default passwords clearly
- ⚠️ Add warning to change passwords in production

**Business Context:**
- Provides authentication foundation
- Enables RLS isolation (users only see their portfolios)
- Default users allow quick testing

---

#### 1.2 Securities (Security Master Data)
**Status:** 🟡 **Partially Seeded** (from `seed_portfolio_data.sql`)

**Existing Seed Data:**
- BRK.B (Berkshire Hathaway)
- CNR (Canadian National Railway)
- BAM (Brookfield Asset Management)
- BBUC (BlackRock USD Cash Fund)
- BTI (British American Tobacco)
- EVO (Evolution Gaming)
- NKE (Nike Inc)
- PYPL (PayPal Holdings)
- HHC (Howard Hughes Corporation)

**Research-Based Additional Securities:**
Based on agent capabilities and business context, add:

**High-Quality Dividend Stocks (for Dividend Safety Ratings):**
- JNJ (Johnson & Johnson) - Healthcare, consistent dividend
- PG (Procter & Gamble) - Consumer staples, dividend aristocrat
- KO (Coca-Cola) - Buffett favorite, long dividend history
- MCD (McDonald's) - Consumer discretionary, reliable dividend

**Growth Stocks (for Moat Strength Ratings):**
- AAPL (Apple) - Technology, strong moat
- GOOGL (Google/Alphabet) - Technology, network effects
- AMZN (Amazon) - E-commerce, platform moat
- TSLA (Tesla) - Technology, brand moat

**Value Stocks (for Resilience Ratings):**
- BRK.B (already exists) - Diversified holding company
- WFC (Wells Fargo) - Financial services
- BAC (Bank of America) - Financial services

**International Stocks (for Currency Attribution):**
- ASML (ASML Holding) - Dutch semiconductor equipment
- SAP (SAP SE) - German enterprise software
- TSX:CNQ (Canadian Natural Resources) - Canadian energy

**Recommendation:**
1. ✅ Keep existing 9 securities
2. ✅ Add 12 additional securities (total: ~21 securities)
3. ✅ Include diverse sectors, currencies, and quality levels
4. ✅ Enable comprehensive testing of all agent capabilities

**Business Context:**
- Diverse portfolio enables testing of:
  - Quality ratings (A-F grades)
  - Currency attribution (multi-currency)
  - Sector allocation
  - Moat strength analysis
  - Dividend safety analysis

---

#### 1.3 Rating Rubrics (Quality Rating Configuration)
**Status:** ✅ **Already Seeded** (from `001_rating_rubrics.sql` + JSON files)

**Existing Seed Data:**
- `dividend_safety_v1.json` - Dividend safety weights/thresholds
- `moat_strength_v1.json` - Moat strength weights/thresholds
- `resilience_v1.json` - Balance sheet resilience weights/thresholds

**Research Basis:**
Based on Buffett investment philosophy:
- **Dividend Safety:** FCF coverage, payout ratio, growth streak, net cash
- **Moat Strength:** ROE consistency, gross margins, intangibles, switching costs
- **Resilience:** Debt-to-equity, current ratio, interest coverage, margin stability

**Recommendation:**
1. ✅ Verify JSON files are loaded into `rating_rubrics` table
2. ✅ Ensure all 3 rating types have seed data
3. ✅ Verify weights sum to 1.0
4. ✅ Document research basis in comments

**Business Context:**
- Enables `buffett_checklist` pattern
- Required for `policy_rebalance` pattern (quality filtering)
- Powers quality scoring across all securities

---

#### 1.4 Macro Indicators (Economic Data)
**Status:** 🟡 **Partially Seeded** (from `macro_indicators_defaults.json`)

**Existing Seed Data:**
- Configuration exists in `backend/config/macro_indicators_defaults.json`
- Default values for key indicators

**Required Historical Data:**
Based on cycle detection requirements:

**Short-Term Debt Cycle (STDC):**
- Needs: 5-10 years of monthly data
- Indicators: GDP, UNRATE, CPIAUCSL, DGS10, DGS2
- ~60-120 data points per indicator

**Long-Term Debt Cycle (LTDC):**
- Needs: 50-75 years of quarterly/annual data
- Indicators: GDP, DEBT/GDP ratio, credit growth
- ~200-300 data points per indicator

**Empire Cycle:**
- Needs: 50+ years of annual data
- Indicators: Military spending, trade balance, education metrics
- ~50-75 data points per indicator

**Internal Order Cycle (Civil):**
- Needs: 50+ years of annual data
- Indicators: Income inequality (Gini), political polarization, trust metrics
- ~50-75 data points per indicator

**Core Indicators (Required for All Cycles):**
- `T10Y2Y` - 10Y-2Y Treasury spread (yield curve)
- `UNRATE` - Unemployment rate
- `CPIAUCSL` - Consumer Price Index
- `GDP` - Gross Domestic Product
- `DGS10` - 10-Year Treasury rate
- `DGS2` - 2-Year Treasury rate

**Recommendation:**
1. ✅ Seed default current values from `macro_indicators_defaults.json`
2. ✅ Add historical data fetching script (FRED API integration)
3. ✅ Seed minimum 5 years of historical data for STDC
4. ✅ Seed minimum 50 years for LTDC, Empire, Civil cycles (if available)
5. ⚠️ Note: Full historical data requires FRED API access

**Business Context:**
- Enables `macro_cycles_overview` pattern
- Required for `portfolio_cycle_risk` pattern
- Powers regime detection and cycle phase analysis

---

### Priority 2: Portfolio Setup (Enables Portfolio Operations)

#### 2.1 Portfolios
**Status:** 🟡 **Partially Seeded** (from CSV files)

**Existing Seed Data:**
- CSV files exist in `/data/seeds/portfolios/portfolios.csv`

**Business Context:**
Based on typical portfolio management scenarios:

**Recommended Portfolios:**
1. **Main Portfolio** - User's primary portfolio
   - Name: "Main Portfolio"
   - Currency: CAD (or user's base currency)
   - Benchmark: SPY or custom
   - Status: Active

2. **Retirement Portfolio** (Optional)
   - Name: "Retirement Portfolio"
   - Currency: CAD
   - Benchmark: VTI
   - Status: Active

**Recommendation:**
1. ✅ Create at least 1 portfolio per user
2. ✅ Use diverse currencies (CAD, USD, EUR) for multi-currency testing
3. ✅ Include benchmark assignments
4. ✅ Set appropriate base currencies

**Dependencies:**
- Requires `users` table to have user records
- Foreign key: `user_id` → `users.id`

---

#### 2.2 Pricing Packs
**Status:** ❌ **Not Seeded** (created by jobs)

**Business Context:**
Pricing packs are created by nightly jobs, but for initial setup:

**Required:**
- At least 1 pricing pack for current date
- Status: 'fresh' (so patterns can execute)
- Policy: 'WM4PM_CAD' (or user's preferred policy)

**Recommendation:**
1. ✅ Create initial pricing pack for current date
2. ✅ Mark as 'fresh' so executor doesn't block
3. ✅ Include all securities from securities table
4. ⚠️ Note: Prices should come from external providers or stub data

**Dependencies:**
- None (independent table)
- But needed by `prices` and `fx_rates` tables

---

#### 2.3 Prices
**Status:** ❌ **Not Seeded** (created by pricing pack builder)

**Business Context:**
Prices are created by pricing pack builder, but for initial setup:

**Required:**
- Prices for all securities in pricing pack
- Current date prices (for immediate use)
- Historical prices (for performance calculations)

**Research-Based Prices:**
- Use realistic current market prices
- For stub data, use recent market data approximations
- Ensure prices match security currencies

**Recommendation:**
1. ✅ Seed prices for all seeded securities
2. ✅ Use current market prices (from external API or approximations)
3. ✅ Ensure prices match security currencies
4. ✅ Include price history for performance calculations (optional but recommended)

**Dependencies:**
- Requires `securities` table
- Requires `pricing_packs` table
- Foreign keys: `security_id` → `securities.id`, `pack_id` → `pricing_packs.id`

---

#### 2.4 FX Rates
**Status:** ❌ **Not Seeded** (created by pricing pack builder)

**Business Context:**
FX rates are created by pricing pack builder, but for initial setup:

**Required Currency Pairs:**
Based on multi-currency portfolio needs:
- USD/CAD (most common)
- EUR/USD
- EUR/CAD
- GBP/USD
- GBP/CAD

**Research-Based Rates:**
- Use current market rates (WM 4PM fixing or approximations)
- Ensure rates are bidirectional (USD/CAD and CAD/USD)
- Include historical rates for attribution calculations

**Recommendation:**
1. ✅ Seed FX rates for common currency pairs
2. ✅ Use current market rates (from external API or approximations)
3. ✅ Include bidirectional rates
4. ✅ Include historical rates for attribution (optional but recommended)

**Dependencies:**
- Requires `pricing_packs` table
- Foreign key: `pack_id` → `pricing_packs.id`

---

#### 2.5 Lots (Positions)
**Status:** 🟡 **Partially Seeded** (from CSV files)

**Existing Seed Data:**
- CSV files exist in `/data/seeds/portfolios/lots.csv`

**Business Context:**
Based on typical portfolio configurations:

**Recommended Positions:**
1. **Diversified Portfolio** - 10-15 positions across sectors
   - Mix of high-quality stocks (JNJ, KO, PG)
   - Growth stocks (AAPL, GOOGL, AMZN)
   - Value stocks (BRK.B, WFC)
   - International exposure (ASML, SAP)

2. **Quality-Focused Portfolio** - 5-10 high-quality positions
   - Focus on A-B rated securities
   - Dividend aristocrats
   - Strong moat companies

**Position Sizes:**
- Realistic position sizes (not too small, not too large)
- Diversified weights (no single position > 30%)
- Total portfolio value: $250K - $500K (realistic range)

**Recommendation:**
1. ✅ Seed 10-15 positions per portfolio
2. ✅ Use diverse securities (from seeded securities)
3. ✅ Realistic position sizes and weights
4. ✅ Include cost basis information
5. ✅ Vary acquisition dates (some older, some recent)

**Dependencies:**
- Requires `portfolios` table
- Requires `securities` table
- Foreign keys: `portfolio_id` → `portfolios.id`, `security_id` → `securities.security_id`

---

### Priority 3: Transaction History (Enables Audit Trail)

#### 3.1 Transactions
**Status:** 🟡 **Partially Seeded** (from CSV files)

**Existing Seed Data:**
- CSV files exist in `/data/seeds/portfolios/transactions.csv`

**Business Context:**
Based on typical transaction patterns:

**Recommended Transactions:**
1. **Historical Buys** - Initial position acquisitions
   - Dates: 1-2 years ago
   - Types: BUY transactions
   - Linked to lots (for cost basis)

2. **Recent Activity** - More recent transactions
   - Dates: Last 6 months
   - Types: BUY, SELL, DIVIDEND
   - Show active portfolio management

3. **Dividends** - Dividend payments
   - Regular dividend payments
   - Quarterly/annual frequencies
   - Show income generation

**Transaction Patterns:**
- Initial buys: Larger purchases (position building)
- Regular buys: Smaller additions (dollar-cost averaging)
- Sells: Position reductions or rebalancing
- Dividends: Regular income

**Recommendation:**
1. ✅ Seed 20-30 transactions per portfolio
2. ✅ Include diverse transaction types (BUY, SELL, DIVIDEND, FEE)
3. ✅ Historical dates (1-2 years back)
4. ✅ Realistic quantities and prices
5. ✅ Link to lots where applicable (for tax lot accounting)

**Dependencies:**
- Requires `portfolios` table
- Requires `securities` table
- Optionally requires `lots` table (for tax lot linking)

---

### Priority 4: Time-Series Data (Enables Performance Analytics)

#### 4.1 Portfolio Metrics
**Status:** ❌ **Not Seeded** (calculated by jobs)

**Business Context:**
Portfolio metrics are calculated by nightly jobs, but for initial setup:

**Required Metrics:**
- Daily NAV (Net Asset Value)
- Time-weighted returns (1d, MTD, YTD, 1y)
- Sharpe ratio (1y)
- Volatility metrics

**Historical Data:**
- At least 1 year of daily metrics
- Enables performance charts
- Enables attribution analysis

**Recommendation:**
1. ⚠️ Calculate via jobs (not direct seeding)
2. ✅ Ensure jobs can backfill historical metrics
3. ✅ Seed initial metrics for portfolio start date
4. ✅ Include enough history for charts (30+ days minimum)

**Dependencies:**
- Requires `portfolios` table
- Requires `pricing_packs` table (for calculations)
- Calculated from positions, prices, and transactions

---

#### 4.2 Portfolio Daily Values
**Status:** ❌ **Not Seeded** (calculated by jobs)

**Business Context:**
Daily NAV values are calculated by jobs, but for initial setup:

**Required:**
- Daily NAV snapshots
- Contributions/withdrawals history
- At least 30 days of history for charts

**Recommendation:**
1. ⚠️ Calculate via jobs (not direct seeding)
2. ✅ Ensure jobs can backfill daily values
3. ✅ Seed initial NAV for portfolio start date
4. ✅ Include contribution/withdrawal transactions

**Dependencies:**
- Requires `portfolios` table
- Derived from positions, prices, and cash flows

---

#### 4.3 Portfolio Cash Flows
**Status:** ❌ **Not Seeded** (populated by transactions)

**Business Context:**
Cash flows are populated from transactions, but for initial setup:

**Required:**
- Contribution transactions (initial funding)
- Withdrawal transactions (if any)
- Dividend cash flows (from dividend transactions)

**Recommendation:**
1. ✅ Populate from transactions (automatic)
2. ✅ Ensure dividend transactions create cash flows
3. ✅ Include initial contribution for portfolio start

**Dependencies:**
- Requires `portfolios` table
- Populated from `transactions` table

---

#### 4.4 Regime History
**Status:** ❌ **Not Seeded** (calculated by macro agent)

**Business Context:**
Regime history is calculated by macro agent, but for initial setup:

**Required:**
- Historical regime classifications
- At least 1 year of daily regimes
- Confidence scores

**Recommendation:**
1. ⚠️ Calculate via macro agent (not direct seeding)
2. ✅ Ensure macro agent can backfill regime history
3. ✅ Seed initial regime for current date
4. ✅ Include enough history for regime transition analysis

**Dependencies:**
- Requires `macro_indicators` table
- Calculated from macro indicators by `RegimeDetector`

---

### Priority 5: Configuration Data (Enables Advanced Features)

#### 5.1 Alerts
**Status:** ❌ **Not Seeded** (user-defined)

**Business Context:**
Alerts are typically user-defined, but for demonstration:

**Recommended Alert Types:**
1. **Price Alerts** - Price threshold breaches
2. **Performance Alerts** - Return threshold breaches
3. **Concentration Alerts** - Position size warnings
4. **Quality Alerts** - Rating downgrades

**Recommendation:**
1. ⚠️ Usually user-defined (not seeded)
2. ✅ Optionally seed example alerts for demonstration
3. ✅ Include diverse alert types

**Dependencies:**
- Requires `portfolios` table
- Foreign key: `portfolio_id` → `portfolios.id`

---

## 🎯 Seeding Execution Plan

### Phase 1: Foundation (No Dependencies)
**Goal:** Enable basic functionality
**Time:** 30 minutes
**Priority:** P0 (Critical)

1. ✅ **Users** - Already seeded (verify exists)
2. ✅ **Rating Rubrics** - Already seeded (verify JSON files loaded)
3. 🟡 **Securities** - Partially seeded (add 12 more for diversity)
4. 🟡 **Macro Indicators** - Partially seeded (add historical data)

**Actions:**
- Verify existing seeds are loaded
- Add additional securities (12 high-quality, diverse stocks)
- Seed macro indicator defaults + fetch historical data (via FRED API or manual)

---

### Phase 2: Portfolio Setup (Depends on Foundation)
**Goal:** Enable portfolio operations
**Time:** 45 minutes
**Priority:** P0 (Critical)

1. 🟡 **Portfolios** - Partially seeded (verify + ensure 1 per user)
2. ❌ **Pricing Packs** - Create initial pack for current date
3. ❌ **Prices** - Seed prices for all securities in pack
4. ❌ **FX Rates** - Seed FX rates for common pairs
5. 🟡 **Lots** - Partially seeded (verify + ensure 10-15 positions)

**Actions:**
- Verify portfolio CSV is loaded
- Create initial pricing pack (mark as 'fresh')
- Seed prices for all securities (use current market prices or approximations)
- Seed FX rates for common currency pairs
- Verify lots CSV is loaded + ensure 10-15 positions per portfolio

---

### Phase 3: Transaction History (Depends on Portfolio)
**Goal:** Enable audit trail
**Time:** 30 minutes
**Priority:** P1 (High)

1. 🟡 **Transactions** - Partially seeded (verify + ensure 20-30 per portfolio)

**Actions:**
- Verify transactions CSV is loaded
- Ensure diverse transaction types (BUY, SELL, DIVIDEND)
- Link transactions to lots where applicable

---

### Phase 4: Time-Series Data (Depends on Portfolio + Jobs)
**Goal:** Enable performance analytics
**Time:** 2 hours (mostly automated)
**Priority:** P1 (High)

1. ❌ **Portfolio Metrics** - Run metrics calculation jobs
2. ❌ **Portfolio Daily Values** - Run daily values backfill
3. ❌ **Portfolio Cash Flows** - Auto-populate from transactions
4. ❌ **Regime History** - Run macro agent regime detection

**Actions:**
- Run `compute_metrics_simple.py` job for historical metrics
- Run `backfill_daily_values.py` job for NAV history
- Verify cash flows are populated from transactions
- Run macro agent regime detection for historical regimes

---

### Phase 5: Configuration (Optional)
**Goal:** Enable advanced features
**Time:** 15 minutes
**Priority:** P2 (Medium)

1. ❌ **Alerts** - Optionally seed example alerts

**Actions:**
- Optionally seed 2-3 example alerts per portfolio

---

## 📊 Research-Based Seeding Recommendations

### Based on Agent Capabilities

#### FinancialAnalyst Agent
**Needs:**
- Positions (lots) with prices
- FX rates for currency attribution
- Portfolio metrics for performance

**Seed:**
- ✅ Diverse positions across sectors
- ✅ Multi-currency positions (for attribution testing)
- ✅ Sufficient positions for meaningful metrics

---

#### RatingsAgent
**Needs:**
- Rating rubrics (weights/thresholds)
- Securities with fundamentals (optional, can use stub)

**Seed:**
- ✅ Rating rubrics (already seeded)
- ✅ Securities diverse enough for quality range (A-F ratings)

---

#### OptimizerAgent
**Needs:**
- Positions with prices
- Ratings for quality filtering
- Portfolio context

**Seed:**
- ✅ Positions with quality range (enables filtering)
- ✅ Ratings rubrics (for quality scoring)

---

#### MacroHound Agent
**Needs:**
- Macro indicators with historical data
- Sufficient history for cycle detection

**Seed:**
- ✅ Current macro indicator values
- ✅ Historical macro indicator data (5-50+ years depending on cycle)

---

### Based on Business Context

#### Typical Portfolio Management User
**Expects:**
- Realistic portfolio (not toy data)
- Meaningful positions (not trivial amounts)
- Historical context (some positions aged)

**Seed:**
- ✅ Portfolio value: $250K-$500K (realistic range)
- ✅ Position count: 10-15 (diversified)
- ✅ Position ages: Mix of 1-2 year old and recent
- ✅ Transaction history: 1-2 years back

---

#### Investment Advisor Context
**Expects:**
- Quality-focused portfolio
- Performance tracking capability
- Multi-currency support

**Seed:**
- ✅ High-quality securities (A-B rated)
- ✅ Performance metrics history
- ✅ Multi-currency positions (CAD, USD, EUR)

---

## 🔍 Verification Checklist

### Foundation Verification
- [ ] Users table has at least 1 user
- [ ] Securities table has 20+ securities (diverse sectors, currencies)
- [ ] Rating rubrics table has 3 rating types (dividend_safety, moat_strength, resilience)
- [ ] Macro indicators table has current values + 5+ years of history

### Portfolio Verification
- [ ] Portfolios table has 1+ portfolio per user
- [ ] Pricing packs table has 1+ fresh pack
- [ ] Prices table has prices for all securities in pack
- [ ] FX rates table has rates for common currency pairs
- [ ] Lots table has 10-15 positions per portfolio

### Transaction Verification
- [ ] Transactions table has 20-30 transactions per portfolio
- [ ] Transactions include diverse types (BUY, SELL, DIVIDEND)
- [ ] Transactions span 1-2 years of history

### Time-Series Verification
- [ ] Portfolio metrics table has 30+ days of metrics
- [ ] Portfolio daily values table has 30+ days of NAV
- [ ] Portfolio cash flows table has contribution/withdrawal records
- [ ] Regime history table has 30+ days of regimes

---

## 🎯 Seeding Script Organization

### Script 1: Foundation Seeds
**File:** `scripts/seed_foundation.py`
**Purpose:** Seed users, securities, rating rubrics, macro indicators
**Dependencies:** None
**Time:** 30 minutes

---

### Script 2: Portfolio Seeds
**File:** `scripts/seed_portfolios.py`
**Purpose:** Seed portfolios, pricing packs, prices, FX rates, lots
**Dependencies:** Foundation seeds
**Time:** 45 minutes

---

### Script 3: Transaction Seeds
**File:** `scripts/seed_transactions.py`
**Purpose:** Seed transactions, link to lots
**Dependencies:** Portfolio seeds
**Time:** 30 minutes

---

### Script 4: Time-Series Seeds
**File:** `scripts/seed_timeseries.py`
**Purpose:** Run jobs to calculate metrics, daily values, regimes
**Dependencies:** Portfolio seeds
**Time:** 2 hours (mostly automated)

---

## 📋 Research Sources

### Rating Rubrics
**Source:** Buffett investment philosophy
**References:**
- Dividend safety: FCF coverage, payout sustainability
- Moat strength: ROE consistency, pricing power, switching costs
- Resilience: Balance sheet strength, interest coverage

**Weights:**
- Loaded from `/data/seeds/ratings/*.json`
- Based on research-backed thresholds

---

### Macro Indicators
**Source:** FRED API + Dalio framework
**References:**
- Short-Term Debt Cycle: GDP, credit growth, unemployment
- Long-Term Debt Cycle: Debt/GDP ratio, deleveraging phases
- Empire Cycle: Military spending, trade balance, education
- Internal Order Cycle: Income inequality, polarization, trust

**Default Values:**
- Loaded from `backend/config/macro_indicators_defaults.json`
- Current market values (approximations if FRED unavailable)

---

### Securities Selection
**Source:** Business context + agent testing needs
**Criteria:**
- High-quality stocks (for rating testing)
- Growth stocks (for moat testing)
- Dividend stocks (for dividend safety testing)
- International stocks (for currency attribution testing)

**Selected Securities:**
- Quality: JNJ, KO, PG, MCD
- Growth: AAPL, GOOGL, AMZN, TSLA
- Value: BRK.B, WFC, BAC
- International: ASML, SAP, CNQ

---

## 🚨 Critical Dependencies

### For OptimizerPage to Work
1. ✅ **Users** - At least 1 user
2. ✅ **Portfolios** - At least 1 portfolio
3. ✅ **Securities** - At least 1 security
4. ✅ **Lots** - At least 1 position (lot)
5. ✅ **Pricing Packs** - At least 1 fresh pack
6. ✅ **Prices** - Prices for all portfolio securities
7. ✅ **Rating Rubrics** - All 3 rating types seeded

**If Any Missing:**
- Pattern execution fails
- Empty or incomplete data
- Potential crashes (from division by undefined)

---

### For Macro Cycles to Work
1. ✅ **Macro Indicators** - Current values + 5+ years history
2. ✅ **Regime History** - Optional but recommended

**If Missing:**
- Cycle detection fails
- Empty cycle states
- No historical context

---

## 📈 Seeding Volume Recommendations

### Minimum Viable Setup
- **Users:** 1-2
- **Securities:** 10-15
- **Portfolios:** 1 per user
- **Lots:** 5-10 per portfolio
- **Transactions:** 10-15 per portfolio
- **Pricing Packs:** 1 (current date)
- **Prices:** All securities in pack
- **FX Rates:** 3-5 currency pairs
- **Rating Rubrics:** 3 rating types
- **Macro Indicators:** Current values only

**Time:** ~1 hour
**Enables:** Basic portfolio operations

---

### Recommended Setup (Business Value)
- **Users:** 2-3
- **Securities:** 20-25 (diverse sectors, currencies)
- **Portfolios:** 1-2 per user
- **Lots:** 10-15 per portfolio
- **Transactions:** 20-30 per portfolio
- **Pricing Packs:** 1-2 (current + recent)
- **Prices:** All securities + 30 days history
- **FX Rates:** 5-8 currency pairs + 30 days history
- **Rating Rubrics:** 3 rating types (verified)
- **Macro Indicators:** Current + 5+ years history

**Time:** ~3 hours
**Enables:** Full feature testing + demonstrations

---

### Comprehensive Setup (Full Testing)
- **Users:** 3-5
- **Securities:** 30-40 (comprehensive coverage)
- **Portfolios:** 2-3 per user
- **Lots:** 15-20 per portfolio
- **Transactions:** 30-50 per portfolio
- **Pricing Packs:** 5-10 (spanning 1 month)
- **Prices:** All securities + 1 year history
- **FX Rates:** 10+ currency pairs + 1 year history
- **Rating Rubrics:** 3 rating types + alternative versions
- **Macro Indicators:** Current + 50+ years history (full cycles)

**Time:** ~8 hours
**Enables:** Full production-like testing

---

## 🔄 Automated Seeding Workflow

### Step 1: Foundation Seeds (Automated)
```bash
python scripts/seed_foundation.py
```
**Output:** Users, securities, rating rubrics, macro indicators

---

### Step 2: Portfolio Seeds (Automated)
```bash
python scripts/seed_portfolios.py
```
**Output:** Portfolios, pricing packs, prices, FX rates, lots

---

### Step 3: Transaction Seeds (Automated)
```bash
python scripts/seed_transactions.py
```
**Output:** Transactions, linked to lots

---

### Step 4: Time-Series Jobs (Automated)
```bash
python backend/jobs/compute_metrics_simple.py --backfill
python backend/jobs/backfill_daily_values.py
python backend/jobs/compute_macro.py --regime-history
```
**Output:** Portfolio metrics, daily values, regime history

---

## 📊 Data Quality Checks

### After Seeding Foundation
- [ ] All users have valid emails and password hashes
- [ ] All securities have valid symbols and currencies
- [ ] All rating rubrics have weights summing to 1.0
- [ ] All macro indicators have valid values and dates

---

### After Seeding Portfolio
- [ ] All portfolios have valid user_id references
- [ ] All lots have valid portfolio_id and security_id references
- [ ] All prices have valid security_id and pack_id references
- [ ] All FX rates have valid pack_id references
- [ ] Pricing pack is marked as 'fresh'

---

### After Seeding Transactions
- [ ] All transactions have valid portfolio_id and security_id references
- [ ] Transaction dates are chronological
- [ ] Transaction quantities match lot quantities (where linked)

---

### After Running Jobs
- [ ] Portfolio metrics are calculated correctly
- [ ] Daily values match portfolio NAV
- [ ] Regime history is populated
- [ ] Cash flows match transactions

---

## 🎯 Business Value Assessment

### Seeding Enables:
1. ✅ **Full Pattern Testing** - All 12 patterns can execute
2. ✅ **Agent Capability Testing** - All agents can run with real data
3. ✅ **UI Demonstration** - All 17 pages show meaningful data
4. ✅ **Performance Analysis** - Historical metrics enable charts
5. ✅ **Quality Ratings** - Diverse securities enable A-F rating range
6. ✅ **Currency Attribution** - Multi-currency positions enable attribution
7. ✅ **Macro Cycles** - Historical data enables cycle detection
8. ✅ **Optimization** - Quality ratings enable policy rebalancing

---

## 📋 Next Steps

### Immediate Actions (No Code Changes)
1. ✅ **Review existing seed data** - Verify what's already loaded
2. ✅ **Identify gaps** - What's missing for full functionality
3. ✅ **Plan dependencies** - What needs to be seeded in what order

### Future Implementation
1. ⚠️ **Create seeding scripts** - Automated seeding workflow
2. ⚠️ **Add historical data** - FRED API integration for macro indicators
3. ⚠️ **Verify business context** - Ensure seeds match user expectations
4. ⚠️ **Document seeding process** - Clear instructions for setup

---

**Last Updated:** November 2, 2025  
**Status:** 📋 PLANNING COMPLETE - Ready for Implementation Review

**Key Findings:**
1. Foundation data is mostly seeded (users, rating rubrics)
2. Portfolio data is partially seeded (CSV files exist)
3. Macro indicators need historical data (5-50+ years)
4. Time-series data requires job execution (automated calculation)
5. Dependencies are clear and manageable
6. Business context supports realistic, diverse seed data

