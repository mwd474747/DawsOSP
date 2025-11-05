# Comprehensive Testing Plan: DawsOS System

**Date:** November 4, 2025  
**Author:** Claude IDE Agent (incorporating Replit Agent feedback)  
**Purpose:** Comprehensive testing plan for 53+ API endpoints, database consistency, and error propagation  
**Status:** 📋 **PLAN READY FOR EXECUTION**

---

## 📊 Executive Summary

**System Scope:**
- **53+ API Endpoints** across 10 categories
- **15+ Database Tables** (PostgreSQL + TimescaleDB)
- **13 Pattern Workflows** with orchestrated capabilities
- **4 Consolidated Agents** with capability routing
- **Complex Error Propagation** requiring validation

**Critical Issues Identified:**
1. ⚠️ Pattern failures: `optimizer.suggest_hedges` capability missing (legacy from Phase 3)
2. ⚠️ Auth failures: 401 errors not properly refreshing tokens
3. ⚠️ Database failures: Connection pool access issues between agents
4. ⚠️ API failures: FMP rate limiting (120 req/min) not always respected
5. ⚠️ UI error handling: Generic error messages not always helpful

**Testing Strategy:**
- **Phase 1:** API Endpoint Testing (53+ endpoints)
- **Phase 2:** Database Consistency Testing (15+ tables)
- **Phase 3:** Pattern Workflow Testing (13 patterns)
- **Phase 4:** Error Propagation Testing (5 critical issues)
- **Phase 5:** Integration Testing (End-to-end flows)

---

## 🔍 API Categories & Endpoints

### 1. Pattern Execution (13 patterns)

**Patterns:**
1. `portfolio_overview` - Portfolio snapshot
2. `portfolio_scenario_analysis` - Scenario stress testing
3. `portfolio_cycle_risk` - Cycle-based risk analysis
4. `macro_cycles_overview` - Macro cycle analysis
5. `macro_trend_monitor` - Trend monitoring with alerts
6. `buffett_checklist` - Quality ratings
7. `news_impact_analysis` - News sentiment analysis
8. `holding_deep_dive` - Single position analysis
9. `policy_rebalance` - Portfolio optimization
10. `cycle_deleveraging_scenarios` - Deleveraging playbooks
11. `export_portfolio_report` - PDF report generation
12. `portfolio_macro_overview` - Macro context
13. `corporate_actions_upcoming` - Corporate actions

**Endpoints:**
- `POST /api/patterns/execute` - Execute pattern workflow

**Testing Requirements:**
- ✅ Execute all 13 patterns with valid inputs
- ✅ Validate pattern outputs match expected structure
- ✅ Test pattern failure scenarios (missing capabilities, invalid inputs)
- ✅ Verify capability routing (feature flags)
- ✅ Validate trace and data provenance

**Critical Issues:**
- ⚠️ `optimizer.suggest_hedges` → `financial_analyst.suggest_hedges` (Phase 3 consolidation)
- ✅ **VERIFIED:** Feature flag `optimizer_to_financial` is enabled (100% rollout)
- ✅ **VERIFIED:** Capability mapping exists in `CAPABILITY_CONSOLIDATION_MAP`
- ⚠️ **NEEDS TESTING:** Verify routing works in runtime (test pattern execution)

---

### 2. Authentication (3 endpoints)

**Endpoints:**
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/me` - Current user info

**Testing Requirements:**
- ✅ Login with valid credentials
- ✅ Login with invalid credentials
- ✅ Token refresh before expiry
- ✅ Token refresh after expiry
- ✅ JWT validation (expired tokens, invalid signatures)
- ✅ 401 error handling with automatic token refresh

**Critical Issues:**
- ⚠️ **401 errors not properly refreshing tokens** - UI should automatically refresh on 401
- ⚠️ Verify token refresh logic in `apiClient`

---

### 3. Portfolio Management (8+ endpoints)

**Endpoints:**
- `GET /api/portfolios` - List portfolios
- `GET /api/portfolios/{id}` - Get portfolio details
- `POST /api/portfolios` - Create portfolio
- `PUT /api/portfolios/{id}` - Update portfolio
- `DELETE /api/portfolios/{id}` - Delete portfolio
- `GET /api/portfolios/{id}/holdings` - Get holdings
- `GET /api/portfolios/{id}/transactions` - Get transactions
- `GET /api/portfolios/{id}/metrics` - Get metrics

**Testing Requirements:**
- ✅ CRUD operations for portfolios
- ✅ Holdings retrieval and validation
- ✅ Transactions retrieval and validation
- ✅ Metrics computation and validation
- ✅ Portfolio deletion cascade (lots, transactions)

**Database Tables:**
- `portfolios` - Core portfolio data
- `lots` - Tax lot accounting
- `transactions` - Transaction history
- `portfolio_daily_values` - TimescaleDB hypertable
- `portfolio_metrics` - TimescaleDB hypertable

---

### 4. Risk Analysis (5+ endpoints)

**Endpoints:**
- `POST /api/risk/var` - Value at Risk
- `POST /api/risk/concentration` - Concentration analysis
- `POST /api/risk/decomposition` - Risk decomposition
- `POST /api/risk/factor_exposures` - Factor exposures
- `GET /api/risk/factor_exposures/{portfolio_id}` - Get factor exposures

**Testing Requirements:**
- ✅ VaR computation with different confidence levels
- ✅ Concentration analysis validation
- ✅ Risk decomposition validation
- ✅ Factor exposure computation
- ✅ Factor exposure retrieval

**Database Tables:**
- `factor_exposures` - Factor exposure cache (currently unused)
- `portfolio_metrics` - Risk metrics storage

**Critical Issues:**
- ⚠️ **Database connection pool access issues** - Verify connection pool limits and agent access patterns

---

### 5. Corporate Actions (5+ endpoints)

**Endpoints:**
- `GET /api/corporate-actions` - Get upcoming corporate actions
- `GET /api/corporate-actions/dividends` - Get dividends
- `GET /api/corporate-actions/splits` - Get splits
- `GET /api/corporate-actions/earnings` - Get earnings
- `POST /api/corporate-actions/calculate-impact` - Calculate impact

**Testing Requirements:**
- ✅ Corporate actions retrieval (FMP API)
- ✅ Dividend calendar retrieval
- ✅ Split calendar retrieval
- ✅ Earnings calendar retrieval
- ✅ Impact calculation based on holdings
- ✅ FMP rate limiting (120 req/min)

**Critical Issues:**
- ⚠️ **FMP rate limiting (120 req/min) not always respected** - Verify rate limiting in `FMPProvider`
- ⚠️ Verify FMP API key is configured and valid

---

### 6. AI/Claude Integration (3+ endpoints)

**Endpoints:**
- `POST /api/ai/chat` - Chat interface
- `POST /api/ai/insights` - Generate insights
- `POST /api/ai/analyze` - Analyze data

**Testing Requirements:**
- ✅ Chat interface functionality
- ✅ Insights generation
- ✅ Data analysis
- ✅ Claude API error handling
- ✅ Claude API rate limiting

---

### 7. Optimization (3+ endpoints)

**Endpoints:**
- `POST /api/optimizer/propose-trades` - Propose trades
- `POST /api/optimizer/analyze-impact` - Analyze impact
- `POST /api/optimizer/efficient-frontier` - Efficient frontier

**Testing Requirements:**
- ✅ Trade proposal generation
- ✅ Impact analysis
- ✅ Efficient frontier computation
- ✅ Optimization constraints validation
- ✅ Verify capability routing to `financial_analyst.*`

**Critical Issues:**
- ⚠️ **Pattern failures: `optimizer.suggest_hedges` capability missing** - Verify routing to `financial_analyst.suggest_hedges`

---

### 8. Macro/Market Data (5+ endpoints)

**Endpoints:**
- `GET /api/macro/regime` - Current regime
- `GET /api/macro/regime-history` - Regime history
- `GET /api/macro/indicators` - Macro indicators
- `GET /api/macro/cycles` - Cycle phases
- `GET /api/market/quotes` - Market quotes

**Testing Requirements:**
- ✅ Regime detection and history
- ✅ Macro indicators retrieval
- ✅ Cycle phase computation
- ✅ Market quotes retrieval
- ✅ FRED API integration (if used)

---

### 9. Alerts & Notifications (5+ endpoints)

**Endpoints:**
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert
- `PUT /api/alerts/{id}` - Update alert
- `DELETE /api/alerts/{id}` - Delete alert
- `POST /api/alerts/evaluate` - Evaluate alerts

**Testing Requirements:**
- ✅ Alert CRUD operations
- ✅ Alert evaluation
- ✅ Notification delivery (DLQ)
- ✅ DLQ retry logic
- ✅ Alert condition evaluation

**Database Tables:**
- `alerts` - Alert definitions
- `notifications` - Notification queue
- `dlq` - Dead letter queue

---

### 10. Settings & API Keys (3+ endpoints)

**Endpoints:**
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings
- `GET /api/settings/api-keys` - Get API keys
- `PUT /api/settings/api-keys` - Update API keys

**Testing Requirements:**
- ✅ Settings retrieval and update
- ✅ API key management
- ✅ Secret validation (FMP, Polygon, Claude, NewsAPI)
- ✅ Settings persistence

---

## 🗄️ Database Consistency Testing

### Core Tables (PostgreSQL)

**1. `portfolios`**
- ✅ Portfolio creation and deletion
- ✅ Foreign key constraints
- ✅ Portfolio deletion cascade (lots, transactions)

**2. `lots`**
- ✅ Tax lot accounting
- ✅ Quantity tracking (`qty`, `qty_open`, `qty_original`)
- ✅ Cost basis tracking
- ✅ Foreign key to `portfolios` and `securities`

**3. `transactions`**
- ✅ Transaction history
- ✅ Transaction types (BUY, SELL, DIVIDEND, etc.)
- ✅ Foreign key to `portfolios`

**4. `securities`**
- ✅ Security master data
- ✅ Symbol and ISIN tracking
- ✅ Security creation and updates

**5. `prices`**
- ✅ Price data (OHLCV)
- ✅ Foreign key to `securities` (missing FK constraint)
- ✅ Pricing pack tracking

**6. `fx_rates`**
- ✅ FX rate data
- ✅ Currency pair tracking
- ✅ Pricing pack tracking

### TimescaleDB Hypertables

**7. `portfolio_daily_values`**
- ✅ Hypertable configuration
- ✅ Time-series data insertion
- ✅ Time-based queries
- ✅ Retention policies

**8. `portfolio_metrics`**
- ✅ Hypertable configuration
- ✅ Metrics computation and storage
- ✅ Time-series queries
- ✅ Retention policies

**9. `pricing_packs`**
- ✅ Pricing pack creation
- ✅ Pricing pack versioning
- ✅ Pricing pack deletion

### Cache Tables (Currently Unused)

**10. `factor_exposures`**
- ⚠️ **Currently unused** - Verify if should be used or removed
- ✅ Factor exposure computation
- ✅ Factor exposure storage

**11. `currency_attribution`**
- ⚠️ **Currently unused** - Verify if should be used or removed
- ✅ Currency attribution computation
- ✅ Currency attribution storage

### System Tables

**12. `notifications`**
- ✅ Notification queue
- ✅ Notification delivery
- ✅ Notification status tracking

**13. `alerts`**
- ✅ Alert definitions
- ✅ Alert condition storage
- ✅ Alert status tracking

**14. `dlq`**
- ✅ Dead letter queue
- ✅ Retry logic
- ✅ DLQ status tracking

**15. `audit_log`**
- ✅ Audit logging
- ✅ Audit log queries
- ✅ Audit log retention

---

## 🔄 Pattern Workflow Testing

### Pattern Execution Flow

**1. Pattern Loading**
- ✅ Pattern JSON validation
- ✅ Pattern schema validation
- ✅ Pattern inputs validation

**2. Pattern Execution**
- ✅ Step execution order
- ✅ Capability routing
- ✅ State management
- ✅ Template resolution

**3. Pattern Outputs**
- ✅ Output structure validation
- ✅ Data provenance tracking
- ✅ Trace generation

**4. Pattern Errors**
- ✅ Missing capability handling
- ✅ Invalid input handling
- ✅ Agent failure handling
- ✅ Database error handling

### Critical Patterns

**1. `portfolio_overview`**
- ✅ All 5 steps execute successfully
- ✅ `valued_positions.positions` structure correct
- ✅ `currency_attr` structure correct
- ✅ `sector_allocation` structure correct
- ✅ `historical_nav` structure correct

**2. `macro_trend_monitor`**
- ✅ `alert_suggestions.suggestions` structure correct
- ✅ Alert preset generation
- ✅ Trend analysis validation

**3. `policy_rebalance`**
- ✅ `optimizer.propose_trades` → `financial_analyst.propose_trades` routing
- ✅ Trade proposal structure correct
- ✅ Impact analysis validation

**4. `corporate_actions_upcoming`**
- ✅ FMP API integration
- ✅ Impact calculation
- ✅ Holdings lookup

---

## ⚠️ Error Propagation Testing

### Issue 1: Pattern Failures

**Problem:** `optimizer.suggest_hedges` capability missing (legacy from Phase 3)

**Testing:**
- ✅ Verify `optimizer.suggest_hedges` routes to `financial_analyst.suggest_hedges`
- ✅ Verify feature flag `optimizer_to_financial` is enabled
- ✅ Test pattern execution with `optimizer.suggest_hedges` capability
- ✅ Verify error messages are helpful

**Status:**
- ✅ **VERIFIED:** `CAPABILITY_CONSOLIDATION_MAP` includes `optimizer.suggest_hedges` → `financial_analyst.suggest_hedges`
- ✅ **VERIFIED:** `feature_flags.json` has `optimizer_to_financial: enabled: true, rollout_percentage: 100`
- ✅ **VERIFIED:** Routing logic in `AgentRuntime._get_capability_routing_override()` checks all conditions correctly
- ✅ **VERIFIED:** Target method `financial_analyst_suggest_hedges()` exists and is implemented
- ✅ **VERIFIED:** Pattern `portfolio_scenario_analysis.json` uses capability correctly
- ⚠️ **NEEDS RUNTIME TESTING:** Execute pattern to verify routing works in runtime
- 📋 **TEST SCRIPT:** `test_optimizer_routing.py` - Static validation complete, ready for runtime testing

---

### Issue 2: Auth Failures

**Problem:** 401 errors not properly refreshing tokens

**Testing:**
- ✅ Test 401 error handling in `apiClient`
- ✅ Test automatic token refresh on 401
- ✅ Test token refresh failure scenarios
- ✅ Test UI error messages for auth failures

**Fix:**
- Verify `apiClient` has automatic token refresh on 401
- Verify `apiClient.refreshToken()` is called on 401
- Verify UI shows helpful error messages

---

### Issue 3: Database Failures

**Problem:** Connection pool access issues between agents

**Testing:**
- ✅ Test database connection pool limits
- ✅ Test concurrent agent access
- ✅ Test connection pool exhaustion
- ✅ Test connection pool recovery

**Fix:**
- Verify database connection pool configuration
- Verify connection pool limits are appropriate
- Verify connection pool recovery logic

---

### Issue 4: API Failures

**Problem:** FMP rate limiting (120 req/min) not always respected

**Testing:**
- ✅ Test FMP rate limiting logic
- ✅ Test rate limit exceeded scenarios
- ✅ Test rate limit recovery
- ✅ Test error messages for rate limit exceeded

**Fix:**
- Verify `FMPProvider` has rate limiting logic
- Verify rate limit tracking and enforcement
- Verify error messages for rate limit exceeded

---

### Issue 5: UI Error Handling

**Problem:** Generic error messages not always helpful

**Testing:**
- ✅ Test UI error messages for all error types
- ✅ Test error message specificity
- ✅ Test error message helpfulness
- ✅ Test error message actions (retry, etc.)

**Fix:**
- Verify `PatternRenderer` shows helpful error messages
- Verify error messages include actionable information
- Verify error messages include retry options where appropriate

---

## 📋 Testing Execution Plan

### Phase 1: API Endpoint Testing (Week 1)

**Days 1-2: Pattern Execution**
- Test all 13 patterns
- Validate pattern outputs
- Test pattern failure scenarios

**Days 3-4: Authentication & Portfolio Management**
- Test authentication endpoints
- Test portfolio CRUD operations
- Test holdings and transactions

**Days 5-7: Risk Analysis & Corporate Actions**
- Test risk analysis endpoints
- Test corporate actions endpoints
- Test FMP API integration

---

### Phase 2: Database Consistency Testing (Week 2)

**Days 1-3: Core Tables**
- Test portfolio, lots, transactions
- Test securities and prices
- Test foreign key constraints

**Days 4-5: TimescaleDB Hypertables**
- Test portfolio_daily_values
- Test portfolio_metrics
- Test time-series queries

**Days 6-7: Cache & System Tables**
- Test factor_exposures and currency_attribution
- Test notifications, alerts, dlq
- Test audit logging

---

### Phase 3: Pattern Workflow Testing (Week 3)

**Days 1-3: Pattern Execution Flow**
- Test pattern loading and validation
- Test pattern execution and outputs
- Test pattern error handling

**Days 4-5: Critical Patterns**
- Test portfolio_overview
- Test macro_trend_monitor
- Test policy_rebalance

**Days 6-7: Corporate Actions Pattern**
- Test corporate_actions_upcoming
- Test FMP API integration
- Test impact calculation

---

### Phase 4: Error Propagation Testing (Week 4)

**Days 1-2: Pattern Failures**
- Test optimizer.suggest_hedges routing
- Test feature flag routing
- Test error messages

**Days 3-4: Auth & Database Failures**
- Test 401 error handling
- Test token refresh
- Test database connection pool

**Days 5-7: API & UI Error Handling**
- Test FMP rate limiting
- Test UI error messages
- Test error recovery

---

### Phase 5: Integration Testing (Week 5)

**Days 1-3: End-to-End Flows**
- Test complete user workflows
- Test UI integration
- Test data flow validation

**Days 4-5: Performance Testing**
- Test API response times
- Test database query performance
- Test concurrent user access

**Days 6-7: Regression Testing**
- Test all previously working features
- Test bug fixes
- Test edge cases

---

## 📊 Testing Checklist

### API Endpoint Testing

- [ ] Pattern Execution (13 patterns)
- [ ] Authentication (3 endpoints)
- [ ] Portfolio Management (8+ endpoints)
- [ ] Risk Analysis (5+ endpoints)
- [ ] Corporate Actions (5+ endpoints)
- [ ] AI/Claude Integration (3+ endpoints)
- [ ] Optimization (3+ endpoints)
- [ ] Macro/Market Data (5+ endpoints)
- [ ] Alerts & Notifications (5+ endpoints)
- [ ] Settings & API Keys (3+ endpoints)

### Database Consistency Testing

- [ ] Core Tables (portfolios, lots, transactions, securities, prices, fx_rates)
- [ ] TimescaleDB Hypertables (portfolio_daily_values, portfolio_metrics, pricing_packs)
- [ ] Cache Tables (factor_exposures, currency_attribution)
- [ ] System Tables (notifications, alerts, dlq, audit_log)

### Pattern Workflow Testing

- [ ] Pattern Loading and Validation
- [ ] Pattern Execution Flow
- [ ] Pattern Outputs Validation
- [ ] Pattern Error Handling
- [ ] Critical Patterns (portfolio_overview, macro_trend_monitor, policy_rebalance, corporate_actions_upcoming)

### Error Propagation Testing

- [ ] Pattern Failures (optimizer.suggest_hedges routing)
- [ ] Auth Failures (401 token refresh)
- [ ] Database Failures (connection pool)
- [ ] API Failures (FMP rate limiting)
- [ ] UI Error Handling (helpful error messages)

### Integration Testing

- [ ] End-to-End Flows
- [ ] UI Integration
- [ ] Data Flow Validation
- [ ] Performance Testing
- [ ] Regression Testing

---

## 🎯 Success Criteria

### Phase 1: API Endpoint Testing
- ✅ All 53+ endpoints tested
- ✅ All endpoints return expected responses
- ✅ All error scenarios handled correctly

### Phase 2: Database Consistency Testing
- ✅ All 15+ tables tested
- ✅ All foreign key constraints validated
- ✅ All cascade deletions working

### Phase 3: Pattern Workflow Testing
- ✅ All 13 patterns tested
- ✅ All pattern outputs validated
- ✅ All pattern errors handled

### Phase 4: Error Propagation Testing
- ✅ All 5 critical issues addressed
- ✅ All error scenarios tested
- ✅ All error messages helpful

### Phase 5: Integration Testing
- ✅ All end-to-end flows working
- ✅ All UI integration validated
- ✅ All performance requirements met

---

## 📝 Notes

### Replit Agent Feedback

**Key Findings:**
1. ⚠️ Pattern failures: `optimizer.suggest_hedges` capability missing (legacy from Phase 3)
2. ⚠️ Auth failures: 401 errors not properly refreshing tokens
3. ⚠️ Database failures: Connection pool access issues between agents
4. ⚠️ API failures: FMP rate limiting (120 req/min) not always respected
5. ⚠️ UI error handling: Generic error messages not always helpful

**Recommended Actions:**
1. Fix `optimizer.suggest_hedges` routing to `financial_analyst.suggest_hedges`
2. Implement automatic token refresh on 401 errors
3. Review and fix database connection pool configuration
4. Implement proper FMP rate limiting
5. Improve UI error messages with actionable information

---

**Last Updated:** November 4, 2025  
**Status:** 📋 **PLAN READY FOR EXECUTION**

