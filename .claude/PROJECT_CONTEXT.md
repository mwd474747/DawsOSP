# DawsOS Project Context for Claude IDE

**Last Updated:** November 7, 2025 (Post-UI Refactoring)
**Purpose:** Help Claude Code understand the current application state and development priorities

---

## 🔴 CRITICAL: Recent Changes (November 7, 2025)

### UI Refactoring - ARCHITECTURE CHANGED
**BREAKING CHANGES ALERT:** The UI was completely refactored on November 7, 2025.

**What Changed:**
- ✅ `full_ui.html` split into 10 modular JavaScript files
- ✅ File reduced from 12,021 lines to 1,559 lines (87% reduction)
- ✅ Core systems extracted: CacheManager, ErrorHandler, FormValidator
- ✅ Fixed critical dependency inversion bug
- ✅ All 21 pages preserved, all features intact

**New Frontend Structure:**
```
frontend/
├── cache-manager.js      (560 lines) - Stale-while-revalidate caching
├── error-handler.js      (146 lines) - Error classification & messaging
├── form-validator.js     (67 lines)  - Form validation utilities
├── api-client.js         (386 lines) - API client & TokenManager
├── utils.js              (579 lines) - 14 utility functions
├── panels.js             (907 lines) - 13 panel components
├── context.js            (359 lines) - Portfolio context management
├── pattern-system.js     (996 lines) - 13 pattern configs & orchestration
├── pages.js              (4,553 lines) - 21 page components
└── styles.css            (1,842 lines) - All CSS styles

full_ui.html              (1,559 lines) - Minimal app shell
```

**Critical Module Load Order:**
1. Core systems (cache-manager, error-handler, form-validator) load FIRST
2. Base layer (api-client, utils, panels) load second
3. Context & patterns load third
4. Pages load last
5. full_ui.html imports all and renders App

**Known Issues Fixed:**
- ✅ React.createElement undefined in context.js (fixed commit 036f575)
- ✅ Dependency inversion (CacheManager) (fixed commit 5db15b8)
- ✅ Module load order errors (fixed commit 4d9d7cd)

**Documentation:**
- See [UI_REFACTORING_STATUS.md](../UI_REFACTORING_STATUS.md) for complete analysis
- See [PHASE_2.5_COMPLETE.md](../PHASE_2.5_COMPLETE.md) for Phase 2.5 details
- See [ARCHITECTURE_VERDICT.md](../ARCHITECTURE_VERDICT.md) for architectural analysis

---

## 🔴 CRITICAL: Replit Deployment Guardrails

**READ THIS FIRST:** This application deploys on Replit. Certain files are SACRED and MUST NOT be modified.

**Full Documentation:** [REPLIT_DEPLOYMENT_GUARDRAILS.md](../.archive/deprecated/REPLIT_DEPLOYMENT_GUARDRAILS.md)

**DO NOT MODIFY:**
- ❌ `.replit` - Deployment configuration (run command, ports)
- ❌ `combined_server.py` - Application entry point (Replit runs this)
- ❌ Port 5000 (hardcoded in server and .replit)

**MODIFY WITH EXTREME CAUTION:**
- ⚠️ `full_ui.html` - Now minimal shell (1,559 lines), imports all frontend modules
- ⚠️ `frontend/*.js` - Module system (NEW as of Nov 7, any changes affect all pages)
- ⚠️ `requirements.txt` - Missing packages break imports
- ⚠️ `backend/app/db/connection.py` - Database pool management
- ⚠️ `backend/app/core/agent_runtime.py` - Agent system core
- ⚠️ `backend/app/core/pattern_orchestrator.py` - Pattern execution
- ⚠️ `backend/patterns/*.json` - Business logic definitions

**SAFE TO MODIFY:**
- ✅ Test files, documentation, scripts, archive files
- ✅ Backend services (with tests)
- ✅ Database migrations (with backups)

---

## 🎯 Current State (As of Nov 7, 2025)

### Production Stack
- **Server**: `combined_server.py` - Single FastAPI application (6,043 lines, 53 functional endpoints)
- **UI**: Modular React 18 SPA (11,902 total lines across 10 modules + HTML)
  - `full_ui.html` - App shell (1,559 lines)
  - `frontend/*.js` - 9 JavaScript modules (10,343 lines)
  - 21 pages (LoginPage + 20 authenticated pages)
  - No build step required
- **Database**: PostgreSQL 14+ with TimescaleDB
- **Agents**: 4 specialized agents providing ~70 capabilities
- **Patterns**: 15 JSON pattern definitions

### Key Entry Points
- **Production**: `python combined_server.py` → http://localhost:8000
- **Testing**: `cd backend && uvicorn app.api.executor:executor_app --port 8001`
- **DO NOT USE**: `backend/api_server.py`, `backend/simple_api.py` (archived)

---

## ⚠️ Known Issues & Technical Debt

### 1. Phantom Capabilities (CRITICAL - Users See "N/A")
**Severity**: 🔴 HIGH - Affects user experience

**Problem**: `tax_harvesting_opportunities` pattern calls 6 capabilities that don't exist:
```json
{
  "tax.identify_losses",          // ❌ Does not exist
  "tax.wash_sale_check",          // ❌ Does not exist
  "tax.calculate_harvest",        // ❌ Does not exist
  "tax.switching_cost",           // ❌ Does not exist
  "tax.estimate_impact",          // ❌ Does not exist
  "tax.generate_recommendations"  // ❌ Does not exist
}
```

**Impact**:
- Pattern orchestrator allows execution despite missing capabilities
- Silent failures cascade into "N/A" displays
- Users don't know they're seeing incomplete data

**Status**: Documented but not fixed
**See**: [PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md](../PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md)

### 2. Stub Data in Production (CRITICAL - Fake Data)
**Severity**: 🔴 HIGH - Users see hardcoded fake data

**Confirmed Stub Data:**
- `switching_cost_score = 5` (hardcoded for ALL companies) - line 1140 in data_harvester.py
- Factor analysis has real 438-line implementation but `risk_compute_factor_exposures` uses stub data
- Multiple capabilities return placeholder data instead of calculations

**Impact**:
- Every company gets same switching cost (not real analysis)
- Factor exposures showing fake data despite real service existing
- Users making decisions based on incorrect data

**Status**: Documented but not fully remediated
**See**: [PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md](../PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md)

### 3. Zombie Consolidation Code (MEDIUM Priority)
**Severity**: 🟡 MEDIUM - Technical debt blocking refactoring

**Problem**:
- Phase 3 consolidation (Nov 3) left 2,345 lines of scaffolding code
- Feature flags at 100% rollout (no gradual deployment happening)
- Capability mapping maps deleted agents (old agents gone)

**Impact**:
- Clutters codebase, makes navigation harder
- Blocks future refactoring work
- Confuses new developers

**Status**: Documented but not cleaned up
**See**: [ZOMBIE_CODE_VERIFICATION_REPORT.md](../ZOMBIE_CODE_VERIFICATION_REPORT.md)

### 4. FactorAnalyzer Service Not Used (MEDIUM Priority)
**Severity**: 🟡 MEDIUM - Wasted implementation

**Discovery**:
- `backend/app/services/factor_analysis.py` (438 lines) EXISTS with real implementation
- `risk_compute_factor_exposures` uses stub data instead of calling this service
- `risk_get_factor_exposure_history` DOES use the real service (inconsistency)

**Impact**:
- 438 lines of working code not being used
- Users see stub data when real data available
- Inconsistent behavior across similar capabilities

**Status**: Needs testing and integration
**See**: [COMPREHENSIVE_REFACTORING_PLAN.md](../COMPREHENSIVE_REFACTORING_PLAN.md) Phase 0 Task 0.5

---

## 📐 Architecture Understanding

### Pattern-Driven Orchestration
```
User Request (full_ui.html)
  ↓
POST /api/patterns/execute
  ↓
combined_server.py:execute_pattern_orchestrator()
  ↓
PatternOrchestrator.run_pattern()
  ↓
AgentRuntime.get_agent_for_capability()
  ↓
Agent.execute() (e.g., FinancialAnalyst, MacroHound)
  ↓
Service.method() (e.g., ratings.py, optimizer.py)
  ↓
Database query via get_db_connection_with_rls()
  ↓ (uses pool from sys.modules['__dawsos_db_pool_storage__'])
✅ Pool accessible across all module instances (fixed Nov 2, 2025)
```

### 4 Active Agents (Phase 3 Consolidation Complete)

**Registered in**: `backend/app/api/executor.py` and `combined_server.py`

1. **FinancialAnalyst** - Portfolio ledger, pricing, metrics, attribution, optimization, ratings, charts (~35+ capabilities)
   - **Consolidated from:** OptimizerAgent, RatingsAgent, ChartsAgent
   - **Capabilities**: `ledger.*`, `pricing.*`, `metrics.*`, `attribution.*`, `charts.*`, `risk.*`, `portfolio.*`, `optimizer.*`, `ratings.*`
   - **Services**: ledger, pricing, metrics, attribution, optimizer, ratings, risk, charts

2. **MacroHound** - Macro economic cycles, scenarios, regime detection, alerts (~17+ capabilities)
   - **Consolidated from:** AlertsAgent
   - **Configuration**: `backend/config/macro_indicators_defaults.json` (~40 economic indicators)
   - **Capabilities**: `macro.*`, `scenarios.*`, `cycles.*`, `alerts.*`
   - **Services**: macro_cycles, scenarios, alerts

3. **DataHarvester** - External data fetching, news, reports, corporate actions (~8+ capabilities)
   - **Capabilities**: `data.*`, `news.*`, `reports.*`, `corporate_actions.*`
   - **External APIs**: FMP, FRED, Polygon, NewsAPI
   - **Services**: data_harvester, reports

4. **AIInsights** - AI-powered analysis, insights, summaries, recommendations (~10+ capabilities)
   - **Capabilities**: `ai.*`
   - **Services**: ai_insights
   - **Note**: May use external AI APIs (OpenAI, Anthropic)

**Total Capabilities**: ~70 across 4 agents

---

## 📊 Pattern System (15 Patterns)

**Location**: `backend/patterns/*.json`

**Active Patterns** (confirmed to exist):
1. `portfolio_overview` - Dashboard overview with metrics, holdings, performance
2. `holdings_analysis` - Detailed holdings breakdown and analysis
3. `performance_attribution` - Performance attribution analysis
4. `risk_metrics` - Risk analytics and exposure analysis
5. `scenario_analysis` - Scenario modeling and stress testing
6. `macro_cycles_overview` - Macro cycle analysis and positioning
7. `optimizer_results` - Portfolio optimization recommendations
8. `ai_insights` - AI-generated insights and analysis
9. `market_summary` - Market data and trends
10. `alerts_summary` - Active alerts and notifications
11. `corporate_actions_upcoming` - Upcoming corporate actions
12. `buffett_checklist` - Buffett investment checklist analysis
13. `holding_deep_dive` - Deep dive analysis on specific holding
14. `tax_harvesting_opportunities` - ⚠️ Calls 6 non-existent capabilities
15. `portfolio_tax_report` - Tax reporting (may have capability gaps)

**Pattern Configs Also Exist** (but may not be actively used):
- `cycle_deleveraging_scenarios`
- `export_portfolio_report`
- `macro_trend_monitor`
- `news_impact_analysis`
- `policy_rebalance`
- `portfolio_cycle_risk`
- `portfolio_macro_overview`
- `portfolio_scenario_analysis`

---

## 🏗️ Frontend Architecture (Post Nov 7 Refactoring)

### Module Loading Order (CRITICAL - Order Matters)
```html
1. React, Axios, Chart.js (CDN)
2. cache-manager.js      ← Defines CacheManager FIRST
3. error-handler.js      ← Defines ErrorHandler
4. form-validator.js     ← Defines FormValidator
5. api-client.js         ← Uses ErrorHandler
6. utils.js              ← Uses CacheManager (validated import)
7. panels.js             ← Uses React, utils
8. context.js            ← Uses React, apiClient (fixed Nov 7)
9. pattern-system.js     ← Uses CacheManager, context, panels (validated)
10. pages.js             ← Uses all above modules
11. full_ui.html inline  ← Imports all, renders App
```

**Why Order Matters**: Dependencies must load before consumers. Breaking this order causes undefined reference errors.

### 21 Pages (All Preserved)
1. LoginPage
2. MacroCyclesPage (946 lines - largest)
3. DashboardPage (uses PatternRenderer)
4. DashboardPageLegacy (custom implementation)
5. HoldingsPage
6. TransactionsPage
7. PerformancePage
8. ScenariosPage
9. ScenariosPageLegacy
10. RiskPage
11. AttributionPage
12. OptimizerPage (494 lines)
13. RatingsPage (415 lines)
14. AIInsightsPage
15. AIAssistantPage (376 lines)
16. AlertsPage (368 lines)
17. ReportsPage (273 lines)
18. CorporateActionsPage
19. MarketDataPage
20. SecurityDetailPage (bonus page)
21. SettingsPage

**Pattern Integration**: 16/21 pages (76%) use PatternRenderer for declarative data loading

### 13 Panel Components
1. MetricsGridPanel - Metrics grid display
2. TablePanel (DataTablePanel) - Data tables
3. LineChartPanel (TimeSeriesChartPanel) - Line/time series charts
4. PieChartPanel - Pie charts
5. DonutChartPanel - Donut charts (wraps PieChartPanel)
6. BarChartPanel - Bar charts
7. ActionCardsPanel - Action cards grid
8. CycleCardPanel - Business cycle cards
9. ScorecardPanel - Scorecard displays
10. DualListPanel - Winners/Losers lists
11. NewsListPanel - News displays (2 variants)
12. ReportViewerPanel - Embedded report viewer
13. HoldingsTable - Holdings table (support component)

---

## 🔌 External Integrations

### Data Providers (Live APIs)
1. **Financial Modeling Prep (FMP)**
   - Pricing, fundamentals, company data
   - API Key: Required in environment
   - Rate Limits: Apply

2. **FRED (Federal Reserve Economic Data)**
   - Economic indicators, macro data
   - Free tier available
   - Rate Limits: Generous

3. **Polygon.io**
   - Market data, real-time quotes
   - API Key: Required
   - Rate Limits: Tier-dependent

4. **NewsAPI**
   - News articles, sentiment
   - API Key: Required
   - Rate Limits: Apply

### Database Schema
- **Primary Database**: PostgreSQL 14+ with TimescaleDB extension
- **Row-Level Security (RLS)**: Enforced via `get_db_connection_with_rls(user_id, portfolio_id)`
- **Connection Pooling**: Managed via `__dawsos_db_pool_storage__` module storage

**Known Schema Issues**:
- `lots` table: Uses `acquisition_date` (not `open_date` as some code expects)
- Data contracts exist but enforcement is inconsistent

---

## 🧪 Testing & Development

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/

# Specific service tests
pytest tests/test_factor_analysis.py -v

# UI testing
# Load http://localhost:8000 and check browser console
```

### Development Commands
```bash
# Start development server
python combined_server.py

# Check for stub data
# Use Claude command: /check-stub-data

# Verify environment setup
# Use Claude command: /verify-setup
```

### Debugging Tips
1. **UI Issues**: Check browser console for module loading errors
2. **Pattern Issues**: Check `combined_server.py` logs for pattern orchestrator errors
3. **Agent Issues**: Check agent_runtime.py for capability resolution failures
4. **Database Issues**: Check connection pool status in logs

---

## 📚 Key Documentation Files

### Current State Documentation
- [UI_REFACTORING_STATUS.md](../UI_REFACTORING_STATUS.md) - Complete UI refactoring status (Nov 7)
- [PHASE_2.5_COMPLETE.md](../PHASE_2.5_COMPLETE.md) - Phase 2.5 core systems extraction
- [ARCHITECTURE_VERDICT.md](../ARCHITECTURE_VERDICT.md) - Architectural analysis & recommendations

### Known Issues Documentation
- [PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md](../PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md) - Stub data & phantom capabilities
- [ZOMBIE_CODE_VERIFICATION_REPORT.md](../ZOMBIE_CODE_VERIFICATION_REPORT.md) - Zombie code from Phase 3

### Historical Documentation
- [COMPREHENSIVE_REFACTORING_PLAN.md](../COMPREHENSIVE_REFACTORING_PLAN.md) - Master refactoring plan
- [REFACTORING_PROGRESS.md](../REFACTORING_PROGRESS.md) - Refactoring progress tracking

---

## 🎯 Development Priorities

### Immediate (This Week)
1. **Browser test UI refactoring** - Validate Nov 7 changes work in production
2. **Fix phantom tax capabilities** - Either implement or remove from pattern
3. **Connect FactorAnalyzer service** - Stop using stub data, use real service

### Short-Term (Next Sprint)
1. **Clean up zombie code** - Remove 2,345 lines of scaffolding
2. **Audit all stub data** - Document what's real vs fake
3. **Add capability validation** - Fail fast if pattern calls non-existent capability

### Long-Term (Future Phases)
1. **UI testing suite** - Add automated tests for modules
2. **API documentation** - OpenAPI/Swagger for all endpoints
3. **Performance optimization** - Add metrics, identify bottlenecks

---

## ⚠️ Common Pitfalls

### 1. Modifying full_ui.html Without Understanding Module System
**Problem**: full_ui.html is now just an app shell. Real code is in frontend/*.js
**Solution**: Edit the appropriate frontend module, not full_ui.html

### 2. Breaking Module Load Order
**Problem**: Changing script tag order in full_ui.html breaks dependencies
**Solution**: Keep load order (core systems → base → context → patterns → pages)

### 3. Assuming Capabilities Exist
**Problem**: Pattern orchestrator silently allows non-existent capabilities
**Solution**: Check agent.py files for actual capability implementations before using

### 4. Trusting All Data is Real
**Problem**: Multiple services return stub data without warnings
**Solution**: Verify service implementation before trusting data in UI

### 5. Editing Archived Code
**Problem**: .archive/ contains old code that's no longer active
**Solution**: Only edit code in main directories (backend/, frontend/, root)

---

## 📞 Getting Help

### Claude Commands
- `/check-stub-data` - Find capabilities returning fake data
- `/verify-setup` - Verify development environment
- `/data-expert` - Activate Data Integration Expert agent
- `/phase-status` - Check refactoring phase status

### Documentation Locations
- **Project Root**: Master plans, status reports, architectural docs
- **.claude/knowledge/**: Financial domain knowledge, data contracts, API docs
- **.claude/commands/**: Custom Claude commands for common tasks
- **.archive/**: Historical code and documentation (reference only)

---

**Last Updated**: November 7, 2025
**Next Review**: After browser testing of UI refactoring
**Maintained By**: Development team + Claude Code assistance
