# DawsOS Architecture

**Version**: 2.0.0 | **Status**: Production Ready

---

## System Overview

DawsOS is an AI-powered portfolio management platform built on a **pattern-driven agent orchestration architecture**. The system uses specialized agents that provide capabilities, which are composed into executable patterns defined in JSON.

**Production Stack**:
- **Server**: `combined_server.py` - Single FastAPI application (6,043 lines, 53 functional endpoints)
- **UI**: `full_ui.html` - React 18 SPA (11,594 lines, 18 pages including login, no build step)
- **Database**: PostgreSQL 14+ with TimescaleDB extension
- **Agents**: 4 specialized agents providing 59+ capabilities
  - **Note:** Phase 3 consolidation complete (November 3, 2025) - 9 agents → 4 agents
- **Patterns**: 12 pattern definitions for business workflows

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
    {"capability": "ledger.positions", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}, "as": "positions"},
    {"capability": "pricing.apply_pack", "args": {"positions": "{{positions.positions}}"}, "as": "valued_positions"},
    {"capability": "metrics.compute_twr", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}, "as": "perf_metrics"}
  ]
}
```

**Template Reference Style**: Patterns use direct references to step results via the step's `"as"` key. For example, if a step has `"as": "positions"`, subsequent steps can reference it as `{{positions}}` or access nested properties as `{{positions.positions}}`. This is simpler than the previous `{{state.foo}}` style which required a nested namespace.

### 2. Agent Runtime Layer

**AgentRuntime** ([backend/app/core/agent_runtime.py](backend/app/core/agent_runtime.py))

Routes capability calls to the appropriate agent method:

```
Capability Request ("ledger.positions") → Runtime Lookup → FinancialAnalyst.ledger_positions() → Response
```

**Registered Agents** (4 total - Phase 3 consolidation complete):
1. **FinancialAnalyst** - Portfolio ledger, pricing, metrics, attribution, optimization, ratings, charts (~35+ capabilities)
   - Capabilities: `ledger.*`, `pricing.*`, `metrics.*`, `attribution.*`, `charts.*`, `risk.*`, `portfolio.*`, `optimizer.*`, `ratings.*`
   - **Consolidated from:** OptimizerAgent, RatingsAgent, ChartsAgent (Phase 3 Weeks 1-3, November 3, 2025)
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
- `GET /api/portfolios` - List portfolios
- `GET /api/metrics/{portfolio_id}` - Performance metrics
- `GET /api/macro` - Macro economic data
- `GET /api/buffett-ratings` - Quality ratings
- `GET /api/docs` - OpenAPI documentation

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
2. Holdings (`/holdings`) - Position details using `holding_deep_dive` pattern
3. Transactions (`/transactions`) - Complete audit trail with pagination
4. Performance (`/performance`) - Time-weighted returns using `portfolio_overview` pattern
5. Corporate Actions (`/corporate-actions`) - Dividends, splits, corporate actions

**Analysis Section (4 pages):**
6. Macro Cycles (`/macro-cycles`) - 4 economic cycles (STDC, LTDC, Empire, Civil) using `macro_cycles_overview` and `macro_trend_monitor` patterns
7. Scenarios (`/scenarios`) - What-if analysis using `portfolio_scenario_analysis` pattern
8. Risk Analytics (`/risk`) - Stress testing, VaR using `portfolio_cycle_risk` pattern
9. Attribution (`/attribution`) - Currency and sector breakdown

**Intelligence Section (4 pages):**
10. Optimizer (`/optimizer`) - Portfolio optimization using `policy_rebalance` and `cycle_deleveraging_scenarios` patterns
11. Ratings (`/ratings`) - Buffett quality assessment (A-F grades) using `buffett_checklist` pattern
12. AI Insights (`/ai-insights`) - Claude-powered analysis using `news_impact_analysis` pattern
13. Market Data (`/market-data`) - Economic indicators and market data

**Operations Section (3 pages):**
14. Alerts (`/alerts`) - Real-time monitoring and alert management
15. Reports (`/reports`) - PDF generation using `export_portfolio_report` and `portfolio_macro_overview` patterns
16. Settings (`/settings`) - User preferences and configuration

**Authentication:**
17. Login - JWT authentication

**Pattern Registry:** 12 patterns defined in `full_ui.html` patternRegistry (lines 2784-3117)

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
- `005_audit.sql` - Audit logging
- `006_alerts.sql` - Alert system

**Core Tables**:
- `portfolios` - Portfolio metadata
- `lots` - Position holdings
- `transactions` - Trade history
- `pricing_packs` - Market data snapshots
- `users` - Authentication
- `audit_log` - Full audit trail

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
6. Execute Step 1: capability="ledger.positions"
   → AgentRuntime routes to FinancialAnalyst.ledger_positions()
   → Query: SELECT * FROM lots WHERE portfolio_id = 'abc-123'
   → Returns: positions
   ↓
7. Execute Step 2: capability="pricing.apply_pack"
   → AgentRuntime routes to FinancialAnalyst.pricing_apply_pack()
   → Enriches positions with market prices
   → Returns: valued_positions
   ↓
8. Execute Step 3: capability="metrics.compute_twr"
   → AgentRuntime routes to FinancialAnalyst.metrics_compute_twr()
   → Calculates time-weighted return
   → Returns: perf_metrics
   ↓
9. Orchestrator aggregates all step outputs
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
- **Analysis:** See [DATABASE.md](DATABASE.md) for database operations documentation

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
