# DawsOS Architecture

**Version**: 6.0.1 | **Status**: Production Ready

---

## System Overview

DawsOS is an AI-powered portfolio management platform built on a **pattern-driven agent orchestration architecture**. The system uses specialized agents that provide capabilities, which are composed into executable patterns defined in JSON.

**Production Stack**:
- **Server**: `combined_server.py` - Single FastAPI application (6,043 lines, 53 functional endpoints)
- **UI**: `full_ui.html` - React 18 SPA (11,594 lines, 18 pages including login, no build step)
- **Database**: PostgreSQL 14+ with TimescaleDB extension
- **Agents**: 4 specialized agents providing ~70 capabilities
  - **Note:** Phase 3 consolidation complete (November 3, 2025) - 9 agents → 4 agents
- **Patterns**: 13 pattern definitions for business workflows

---

## Core Components

### 1. Pattern Orchestration Layer

**PatternOrchestrator** ([backend/app/core/pattern_orchestrator.py](backend/app/core/pattern_orchestrator.py))

The orchestrator executes business workflows defined in JSON pattern files:

```
Pattern Definition (JSON) → Template Substitution → Agent Capability Calls → Result Aggregation
```

**Key Concepts**:
- **Patterns**: Declarative JSON files defining multi-step workflows
- **Capabilities**: Agent methods exposed as "capability.method" strings (e.g., "ledger.positions", "pricing.apply_pack")
- **Template Substitution**: Dynamic values using `{{inputs.x}}`, `{{step_result}}`, `{{ctx.z}}`
- **Request Context (RequestCtx)**: Immutable context ensuring reproducibility (pricing_pack_id, ledger_commit_hash, trace_id)

**Example Pattern** ([backend/patterns/portfolio_overview.json](backend/patterns/portfolio_overview.json)):
```json
{
  "id": "portfolio_overview",
  "steps": [
    {
      "capability": "portfolio.get_valued_positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "as": "valued_positions"
    },
    {
      "capability": "metrics.compute_twr",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}"},
      "as": "perf_metrics"
    }
  ]
}
```

**Pattern Optimization (Week 3/4 - November 2025):** The `portfolio.get_valued_positions` capability combines the common pattern of getting positions from the ledger and pricing them with a pricing pack. This eliminates duplication across 6 patterns that previously used the 2-step sequence of `ledger.positions` → `pricing.apply_pack`.

**Template Reference Style**: Patterns use direct references to step results via the step's `"as"` key. For example, if a step has `"as": "valued_positions"`, subsequent steps can reference it as `{{valued_positions}}` or access nested properties as `{{valued_positions.positions}}`. This is simpler than the previous `{{state.foo}}` style which required a nested namespace.

### 2. Agent Runtime Layer

**AgentRuntime** ([backend/app/core/agent_runtime.py](backend/app/core/agent_runtime.py))

Routes capability calls to the appropriate agent method:

```
Capability Request ("ledger.positions") → Runtime Lookup → FinancialAnalyst.ledger_positions() → Response
```

**Registered Agents** (4 total - Phase 3 consolidation complete):
1. **FinancialAnalyst** - Portfolio ledger, pricing, metrics, attribution, optimization, ratings, charts (29 capabilities)
   - Capabilities: `ledger.*`, `pricing.*`, `metrics.*`, `attribution.*`, `charts.*`, `risk.*`, `portfolio.*`, `optimizer.*`, `ratings.*`
   - **Consolidated from:** OptimizerAgent, RatingsAgent, ChartsAgent (Phase 3 Weeks 1-3, November 3, 2025)
   - **Week 3/4 additions:** `portfolio.get_valued_positions`, `metrics.compute_mwr` (November 5, 2025)
   - **Total:** 19 original + 9 consolidated + 2 new = 30 capabilities (updated count)
2. **MacroHound** - Macro economic cycles, scenarios, regime detection, alerts (~17+ capabilities)
   - Capabilities: `macro.*`, `scenarios.*`, `cycles.*`, `alerts.*`
   - **Consolidated from:** AlertsAgent (Phase 3 Week 4, November 3, 2025)
3. **DataHarvester** - External data fetching, news integration, reports (~8+ capabilities)
   - Capabilities: `data.*`, `news.*`, `reports.*`, `corporate_actions.*`
   - **Consolidated from:** ReportsAgent (Phase 3 Week 5, November 3, 2025)
4. **ClaudeAgent** - AI-powered explanations and insights (~6 capabilities)
   - Capabilities: `claude.*`, `ai.*`

**Agent Registration** (combined_server.py:261-300):
```python
def get_agent_runtime(reinit_services: bool = False) -> AgentRuntime:
    services = {"db": db_pool, "redis": None}
    _agent_runtime = AgentRuntime(services)
    
    # Register Financial Analyst (handles ledger, pricing, metrics, attribution)
    financial_analyst = FinancialAnalyst("financial_analyst", services)
    _agent_runtime.register_agent(financial_analyst)
    
    # Register Macro Hound (handles macro cycles and scenarios)
    macro_hound = MacroHound("macro_hound", services)
    _agent_runtime.register_agent(macro_hound)
    
    # Register remaining 2 agents
    # DataHarvester, ClaudeAgent
    
    return _agent_runtime
```

### 3. Backend (FastAPI)

**Primary Entry Point**: [combined_server.py](combined_server.py) (6,043 lines)

**Architecture**:
- **Monolithic Design**: Single file containing all endpoints
- **Singleton Pattern**: Global agent_runtime and pattern_orchestrator
- **Lifespan Management**: Async context managers for database pool and agent initialization
- **Static File Serving**: Serves full_ui.html at root path

**Key Endpoints** (53 functional endpoints):
- `GET /` - Serves full_ui.html
- `POST /api/patterns/execute` - Execute pattern (main endpoint)
- `POST /api/auth/login` - JWT authentication
- `POST /api/auth/refresh` - Refresh token
- `GET /api/portfolios` - List portfolios
- `GET /api/portfolio` - Get portfolio details
- `GET /api/metrics/{portfolio_id}` - Performance metrics
- `GET /api/macro` - Macro economic data
- `GET /api/buffett-ratings` - Quality ratings
- `GET /api/docs` - OpenAPI documentation
- `GET /health` - Health check

**Note:** Complete API documentation available at `/docs` endpoint when server is running. This list shows key endpoints only.

**Alternative Entry Point**: [backend/app/api/executor.py](backend/app/api/executor.py) (922 lines)
- Modular backend structure (not used in production)
- Can run independently on port 8001 for testing
- Uses `executor_app` instead of `app` to avoid naming conflicts

### 4. Frontend (React SPA)

**Primary UI**: [full_ui.html](full_ui.html) (11,594 lines)

**Architecture**:
- **Single-Page Application**: Complete React 18 app in one HTML file
- **No Build Step**: Uses React UMD builds from CDN
- **Client-Side Routing**: Hash-based routing (#/dashboard, #/holdings, etc.)
- **API Client**: Centralized [frontend/api-client.js](frontend/api-client.js) with caching

**18 Pages** (organized by navigation sections):

**Portfolio Section (5 pages):**
1. Dashboard (`/dashboard`) - Portfolio overview using `portfolio_overview` pattern
2. Holdings (`/holdings`) - Position details using `portfolio_overview` pattern (shows holdings table)
3. Transactions (`/transactions`) - Complete audit trail with pagination
4. Performance (`/performance`) - Time-weighted returns using `portfolio_overview` pattern
5. Corporate Actions (`/corporate-actions`) - Dividends, splits, corporate actions using `corporate_actions_upcoming` pattern

**Analysis Section (4 pages):**
6. Macro Cycles (`/macro-cycles`) - 4 economic cycles (STDC, LTDC, Empire, Civil) using `macro_cycles_overview` and `macro_trend_monitor` patterns
7. Scenarios (`/scenarios`) - What-if analysis using `portfolio_scenario_analysis` pattern
8. Risk Analytics (`/risk`) - Stress testing, VaR using `portfolio_cycle_risk` pattern
9. Attribution (`/attribution`) - Currency and sector breakdown

**Intelligence Section (4 pages):**
10. Optimizer (`/optimizer`) - Portfolio optimization using `policy_rebalance` pattern
11. Ratings (`/ratings`) - Buffett quality assessment (A-F grades) using `buffett_checklist` pattern
12. AI Insights (`/ai-insights`) - Claude-powered analysis using `news_impact_analysis` pattern
13. Market Data (`/market-data`) - Economic indicators and market data

**Operations Section (3 pages):**
14. Alerts (`/alerts`) - Real-time monitoring and alert management
15. Reports (`/reports`) - PDF generation using `export_portfolio_report` pattern
16. Settings (`/settings`) - User preferences and configuration

**Corporate Actions Feature (January 14, 2025):**
- Uses `corporate_actions_upcoming` pattern with FMP Pro API integration
- Fetches dividends, splits, and earnings calendars
- Filters by portfolio holdings automatically
- Calculates portfolio impact (dividend amounts, split ratios)
- **Implementation:** Enhanced diagnostic logging and robust quantity handling for symbol extraction

**Note:** Some patterns are defined in the registry but not currently used in UI pages:
- `holding_deep_dive` - Defined but not used (may be used in future)
- `cycle_deleveraging_scenarios` - Defined but not used (may be used in future)
- `portfolio_macro_overview` - Defined but not used (may be used in future)

**Authentication:**
17. Login - JWT authentication

**Pattern Registry:** 13 patterns defined in `full_ui.html` patternRegistry (lines 2784-3117)

**Technology**:
- React 18.2.0 (UMD build)
- Chart.js 4.4.0 for visualizations
- IBM Plex Sans/Mono fonts
- Professional dark theme (#1a1a1a background)

### 5. Database Layer

**PostgreSQL 14+ with TimescaleDB**

**Schema** ([backend/db/schema/](backend/db/schema/)):
- `001_portfolios_lots_transactions.sql` - Core tables
- `002_pricing.sql` - Market data
- `003_metrics.sql` - Performance calculations
- `004_auth.sql` - User authentication
- `006_alerts.sql` - Alert system

**Note:** Schema file `005_audit.sql` was removed as part of Migration 003 (November 4, 2025) along with the `audit_log` table.

**Field Naming Standards (January 14, 2025):**
- **Database Columns:** `quantity_open`, `quantity_original` (standardized from `qty_open`, `qty_original`)
- **Agent Return Fields:** `quantity` (standardized across all agent capabilities)
- **Service Layer:** `qty` (internal API, acceptable for service-to-service communication)
- **Rationale:** Clear separation between database schema (verbose names) and agent API (standardized `quantity`)

**Phase 1 Completion (January 14, 2025):**
- **Provenance Warnings:** Added `_provenance` field to stub data in `risk.compute_factor_exposures` and `macro.compute_dar`
  - Stub data now explicitly marked with `type: "stub"`, `confidence: 0.0`, and warnings
  - UI displays warning banner when stub data is detected (see `full_ui.html` ProvenanceWarningBanner component)
- **Pattern Output Extraction:** Fixed orchestrator to handle 3 output formats (list, dict, dict with panels)
  - Updated 6 patterns to use standard list format: `["output1", "output2", ...]`
  - All patterns now return correct data instead of falling back to `portfolio_overview`
- **Scenario Analysis:** Fixed SQL queries and AttributeError handling
  - Migration 009 applied: `position_factor_betas` table created
  - All 12 scenarios execute successfully with DaR calculations

**Core Tables**:
- `portfolios` - Portfolio metadata
- `lots` - Position holdings
- `transactions` - Trade history
- `pricing_packs` - Market data snapshots
- `users` - Authentication

**Note:** The `audit_log` table was removed in Migration 003 (November 4, 2025) as it was never implemented.

**Design Principles**:
- UUID primary keys
- Timestamp audit fields (created_at, updated_at)
- CASCADE foreign keys
- Proper indexing on frequently queried columns

---

## Data Flow

### Pattern Execution Flow

```
1. User clicks "View Portfolio" in full_ui.html
   ↓
2. frontend/api-client.js calls POST /api/patterns/execute
   {pattern: "portfolio_overview", inputs: {portfolio_id: "abc-123"}}
   ↓
3. combined_server.py receives request (Line 1028)
   ↓
4. PatternOrchestrator loads portfolio_overview.json
   ↓
5. Template substitution: {{inputs.portfolio_id}} → "abc-123"
   ↓
6. Execute Step 1: capability="portfolio.get_valued_positions"
   → AgentRuntime routes to FinancialAnalyst.portfolio_get_valued_positions()
   → Internally calls ledger_positions() + pricing_apply_pack()
   → Query: SELECT * FROM lots WHERE portfolio_id = 'abc-123'
   → Enriches positions with market prices from pricing pack
   → Returns: valued_positions (with positions, total_value, currency)
   ↓
7. Execute Step 2: capability="metrics.compute_twr"
   → AgentRuntime routes to FinancialAnalyst.metrics_compute_twr()
   → Calculates time-weighted return
   → Returns: perf_metrics
   ↓
8. Orchestrator aggregates all step outputs
   ↓
10. Response sent to frontend
    {
      "status": "success",
      "data": {positions, valued_positions, perf_metrics},
      "trace_id": "xyz-789"
    }
    ↓
11. full_ui.html renders dashboard with data
```

### Authentication Flow

```
1. User enters email/password in full_ui.html
   ↓
2. POST /api/auth/login
   ↓
3. combined_server.py validates credentials (bcrypt)
   ↓
4. JWT token generated (24-hour expiration)
   ↓
5. Token stored in localStorage
   ↓
6. All subsequent requests include Authorization: Bearer {token}
   ↓
7. JWT middleware validates token on protected routes
```

---

## Security Architecture

### Authentication
- **JWT Tokens**: 24-hour expiration
- **Password Hashing**: bcrypt with salt
- **Token Storage**: localStorage (client-side)
- **Refresh Tokens**: Available via POST /api/auth/refresh

### Authorization
- **Role-Based Access Control (RBAC)**: ADMIN, MANAGER, USER, VIEWER
- **Endpoint Protection**: JWT validation via `Depends(require_auth)` on 44 protected endpoints (83% coverage)
- **Authentication Pattern**: Centralized dependency injection (see `backend/app/auth/dependencies.py`)
- **Pattern-Level Rights**: Patterns can require specific rights (e.g., "portfolio_read")

**Note:** 2 endpoints still use legacy `get_current_user()` pattern and should be migrated to `require_auth`.

### Data Protection
- **Input Validation**: FastAPI Pydantic models
- **SQL Injection Prevention**: Parameterized queries via asyncpg (NEVER string formatting)
- **XSS Prevention**: React's built-in escaping
- **CORS**: Configured for specific origins (see combined_server.py)
  - ⚠️ **CRITICAL**: Never use `allow_origins=["*"]` with `allow_credentials=True`

### Default Credentials

**⚠️ DEVELOPMENT ONLY - CHANGE IN PRODUCTION!**

- Email: michael@dawsos.com
- Password: mozzuq-byfqyQ-5tefvu

**See README.md for production security checklist.**

---

## Deployment Architecture

### Development
```bash
# Single command startup
python combined_server.py

# Serves on http://localhost:8000/
```

### Production (Replit)
```bash
# Replit automatically runs combined_server.py
# Make sure to set environment variables in Secrets tab
python combined_server.py
```

### Environment Variables

**⚠️ REQUIRED (Application will not start without these):**
```bash
# Database connection
DATABASE_URL="postgresql://user:pass@localhost/dawsos"

# JWT authentication secret (32+ characters)
# Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
AUTH_JWT_SECRET="<generated-secure-random-key>"
```

**Optional (Feature-specific):**
```bash
# AI-powered insights and explanations
# Used by: ClaudeAgent (claude.* capabilities)
# Features: AI Insights page, news impact analysis, pattern explanations
ANTHROPIC_API_KEY="sk-ant-api03-..."

# Federal Reserve economic data
# Used by: MacroHound agent for macro indicators
# Features: Macro Cycles page, economic indicator updates
FRED_API_KEY="your-fred-api-key"

# CORS allowed origins (comma-separated)
# Default: http://localhost:8000
CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Logging level
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Default: INFO
LOG_LEVEL="INFO"
```

**Development Only:**
```bash
# Enable debug mode (detailed error pages)
DEBUG="true"

# Enable auto-reload on code changes
RELOAD="true"
```

**Note:** All environment variables can be set via `.env` file (supported via python-dotenv) or exported in shell.

---

## Alternative Architecture (Available but Not Used)

A modular backend structure exists in [backend/app/](backend/app/) that can be used as an alternative entry point:

```bash
# Alternative: Modular backend (experimental)
cd backend
uvicorn app.api.executor:executor_app --reload --port 8001
```

**Structure**:
```
backend/app/
├── api/
│   ├── executor.py          # Alternative FastAPI app
│   └── routes/              # Modular route definitions
├── agents/                  # Agent implementations
├── core/                    # AgentRuntime, PatternOrchestrator
├── services/                # Business logic
└── db/                      # Database layer
```

**Status**: Not the production entry point. Use `combined_server.py` for production.

---

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React (UMD) | 18.2.0 |
| Backend | FastAPI | 0.104+ |
| Language | Python | 3.11+ |
| Database | PostgreSQL + TimescaleDB | 14+ |
| AI | Anthropic Claude API | claude-3-sonnet |
| Charts | Chart.js | 4.4.0 |
| Auth | JWT | PyJWT |

---

## Design Patterns

1. **Pattern-Driven Architecture**: Business logic defined declaratively in JSON, executed by orchestrator
2. **Singleton Pattern**: Global agent_runtime and pattern_orchestrator instances
3. **Capability Routing**: String-based routing ("agent.method") to Python methods
4. **Template Substitution**: Dynamic value injection using {{}} syntax
5. **Request Context**: Immutable context object for reproducibility
6. **Audit Logging**: All operations logged with trace_id for debugging

---

## Performance Considerations

- **Caching**: Client-side caching with configurable TTL (2-5 minutes)
- **Connection Pooling**: AsyncPG connection pool for database
- **Lazy Loading**: Patterns loaded on-demand, not at startup
- **Pagination**: Transaction history paginated (default 100 items)
- **Async I/O**: FastAPI async/await throughout

---

## Database Connection Architecture

### Standardized Connection Patterns (January 14, 2025) ✅

**Status:** ✅ **STANDARDIZED** - All database connections follow consistent patterns

**Two Standard Patterns:**

#### Pattern A: RLS-Aware Connection (User-Scoped Data) ⭐

**Use for:** User-scoped data (portfolios, lots, transactions, metrics)

**Implementation:**
```python
from app.db.connection import get_db_connection_with_rls

# User-scoped data requires RLS (Row-Level Security)
async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
    rows = await conn.fetch("""
        SELECT * FROM lots
        WHERE portfolio_id = $1
    """, portfolio_id)
```

**Why RLS?**
- Enforces data isolation at database level
- Prevents users from accessing other users' data
- Automatically filters queries by `user_id`
- Required for multi-tenant security

**Usage:**
- Agent methods accessing user data
- API routes accessing portfolios/transactions
- Any query on `portfolios`, `lots`, `transactions`, `portfolio_metrics`, etc.

#### Pattern B: Helper Functions (System-Level Data)

**Use for:** System-level data (securities, pricing_packs, fx_rates, users)

**Implementation:**
```python
from app.db.connection import execute_query, execute_query_one, execute_statement

# System-level data (no RLS needed)
rows = await execute_query("""
    SELECT * FROM securities
    WHERE symbol = $1
""", symbol)

# Single row
row = await execute_query_one("""
    SELECT * FROM securities WHERE id = $1
""", security_id)

# Insert/Update/Delete
await execute_statement("""
    INSERT INTO securities (symbol, name) VALUES ($1, $2)
""", symbol, name)
```

**Why Helper Functions?**
- Simpler API (no connection management)
- Automatic connection pooling
- Consistent error handling
- No RLS overhead for system data

**Usage:**
- Service methods accessing system data
- Job scripts accessing pricing/securities
- Admin operations

### Pool Management (Fixed Nov 2, 2025)

**Challenge:** Module instance separation prevented pool sharing across agents

**Solution:** Cross-module storage using sys.modules

**Implementation** (`backend/app/db/connection.py` lines 35-56):
```python
# Cross-module pool storage
POOL_STORAGE_KEY = '__dawsos_db_pool_storage__'

def _get_pool_storage():
    """Get or create cross-module pool storage."""
    if POOL_STORAGE_KEY not in sys.modules:
        storage = types.SimpleNamespace(pool=None)
        sys.modules[POOL_STORAGE_KEY] = storage
    return sys.modules[POOL_STORAGE_KEY]

def register_external_pool(pool: asyncpg.Pool):
    """Register pool accessible across all module instances."""
    storage = _get_pool_storage()
    storage.pool = pool
```

**Why This Works:**
- `sys.modules` shared across all Python imports
- Pool stored once, accessible everywhere
- No module boundary issues
- Simpler than previous 5-priority fallback

**Historical Context:**
- **Problem:** Module-level variables reset in new import instances (commits before e54da93)
- **Old Approach:** Complex 5-priority fallback (600 lines, unreliable)
- **New Approach:** sys.modules storage (382 lines, reliable)
- **Standardization:** All connections standardized (January 14, 2025)
- **Analysis:** See [DATABASE.md](DATABASE.md) for database operations documentation
- **Completion Report:** See [DATABASE_CONNECTION_STANDARDIZATION_COMPLETE.md](DATABASE_CONNECTION_STANDARDIZATION_COMPLETE.md)

---

## Macro Indicator Configuration System

**Added:** November 2, 2025 (Commits d5d6945, 51b92f3)

### Overview

Centralized JSON-based configuration for ~40 macro economic indicators used in cycle detection (STDC, LTDC, Empire, Civil).

### Components

**Configuration File:** [backend/config/macro_indicators_defaults.json](backend/config/macro_indicators_defaults.json) (640 lines)
- 6 categories: Global, STDC, LTDC, Empire, Civil, Market
- ~40 indicators with full metadata (value, source, confidence, range, aliases)
- 4 pre-configured scenarios (recession, inflation shock, debt crisis, current baseline)
- Data quality tracking (confidence levels, last updated, notes)

**Configuration Manager:** [backend/app/services/indicator_config.py](backend/app/services/indicator_config.py) (471 lines)
- `IndicatorConfigManager` class with singleton pattern
- Accessed via `get_config_manager()` function
- Fallback mechanism: Database → Config → Hardcoded defaults
- Validation & scaling rules
- Alias resolution (e.g., GDP_growth = gdp_growth)

**Documentation:** [backend/config/INDICATOR_CONFIG_README.md](backend/config/INDICATOR_CONFIG_README.md) (122 lines)

### Data Flow

```
1. CyclesService.get_latest_indicators()
   ↓
2. IndicatorConfigManager loads defaults from JSON
   ↓
3. Queries database for latest indicator values
   ↓
4. Merges DB values with config (DB takes precedence)
   ↓
5. Applies scaling rules (percentages to decimals)
   ↓
6. Populates aliases for compatibility
   ↓
7. Returns validated, scaled indicators
   ↓
8. MacroHound uses indicators for cycle detection
```

### Benefits

- ✅ **No Code Changes:** Update indicator values without modifying Python code
- ✅ **Transparency:** Clear documentation of data sources and quality
- ✅ **Flexibility:** Easy scenario testing and overrides
- ✅ **Validation:** Automatic range checking prevents bad data
- ✅ **Version Control:** Track changes through git history

### Example Configuration

```json
"gdp_growth": {
  "value": 0.038,
  "unit": "decimal",
  "display_unit": "percentage",
  "range": {"min": -0.10, "max": 0.15},
  "source": "BEA/FRED",
  "confidence": "high",
  "last_updated": "2025-11-01",
  "notes": "Real GDP growth rate, seasonally adjusted annual rate",
  "aliases": ["GDP_growth"]
}
```

### Usage

```python
from app.services.indicator_config import get_config_manager

# Get configuration manager
config_manager = get_config_manager()

# Get indicator value
gdp_growth = config_manager.get_indicator("gdp_growth")

# Get with metadata
gdp_metadata = config_manager.get_indicator("gdp_growth", with_metadata=True)

# Apply scenario
recession_indicators = config_manager.get_scenario_indicators("recession_scenario")
```

### Files

- **Configuration:** backend/config/macro_indicators_defaults.json
- **Manager:** backend/app/services/indicator_config.py
- **Service:** backend/app/services/cycles.py (uses configuration)
- **Agent:** backend/app/agents/macro_hound.py (consumes indicators)
- **Documentation:** backend/config/INDICATOR_CONFIG_README.md

---

## Future Considerations

- **Redis Integration**: Currently None, can be added for distributed caching
- **Horizontal Scaling**: Single server currently, can add load balancer
- **Microservices**: Modular backend structure in backend/app/ ready for extraction
- **Message Queue**: For async pattern execution (long-running workflows)
