# DawsOS Architecture

**Version**: 2.0.0 | **Status**: Production Ready

---

## System Overview

DawsOS is an AI-powered portfolio management platform built on a **pattern-driven agent orchestration architecture**. The system uses specialized agents that provide capabilities, which are composed into executable patterns defined in JSON.

**Production Stack**:
- **Server**: `combined_server.py` - Single FastAPI application (6,046 lines, 59 endpoints)
- **UI**: `full_ui.html` - React 18 SPA (14,075 lines, 17 pages, no build step)
- **Database**: PostgreSQL 14+ with TimescaleDB extension
- **Agents**: 9 specialized agents providing 59+ capabilities
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
- **Template Substitution**: Dynamic values using `{{inputs.x}}`, `{{state.y}}`, `{{ctx.z}}`
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

### 2. Agent Runtime Layer

**AgentRuntime** ([backend/app/core/agent_runtime.py](backend/app/core/agent_runtime.py))

Routes capability calls to the appropriate agent method:

```
Capability Request ("ledger.positions") → Runtime Lookup → LedgerAgent.positions() → Response
```

**Registered Agents** (9 total):
1. **LedgerAgent**: Position tracking, transaction history (ledger.*)
2. **PricingAgent**: Market data, valuation (pricing.*)
3. **MetricsAgent**: Performance calculation, TWR, volatility (metrics.*)
4. **AttributionAgent**: Return attribution by currency, sector (attribution.*)
5. **PortfolioAgent**: Portfolio metadata, allocations (portfolio.*)
6. **MacroHound**: Economic cycle analysis, STDC/LTDC (macro.*)
7. **FinancialAnalyst**: Buffett ratings, quality assessment (analyst.*)
8. **DataHarvester**: External data fetching (data.*)
9. **ClaudeAgent**: AI-powered explanations, insights (claude.*)

**Agent Registration** (combined_server.py:239-304):
```python
def get_agent_runtime() -> AgentRuntime:
    runtime = AgentRuntime(db=db_pool, redis=None)
    runtime.register(LedgerAgent(db=db_pool))
    runtime.register(PricingAgent(db=db_pool))
    # ... 7 more agents
    return runtime
```

### 3. Backend (FastAPI)

**Primary Entry Point**: [combined_server.py](combined_server.py) (6,046 lines)

**Architecture**:
- **Monolithic Design**: Single file containing all endpoints
- **Singleton Pattern**: Global agent_runtime and pattern_orchestrator
- **Lifespan Management**: Async context managers for database pool and agent initialization
- **Static File Serving**: Serves full_ui.html at root path

**Key Endpoints** (59 total):
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

**Primary UI**: [full_ui.html](full_ui.html) (14,075 lines, 508 KB)

**Architecture**:
- **Single-Page Application**: Complete React 18 app in one HTML file
- **No Build Step**: Uses React UMD builds from CDN
- **Client-Side Routing**: Hash-based routing (#/dashboard, #/holdings, etc.)
- **API Client**: Centralized [frontend/api-client.js](frontend/api-client.js) with caching

**17 Pages**:
1. Login - JWT authentication
2. Dashboard - Portfolio overview
3. Holdings - Position details with Buffett ratings
4. Transactions - Complete audit trail with pagination
5. Performance - Time-weighted returns, charts
6. Scenarios - What-if analysis
7. Risk - Stress testing, VaR
8. Attribution - Currency and sector breakdown
9. Optimizer - Portfolio optimization
10. Ratings - Buffett quality assessment (A-F grades)
11. AI Insights - Claude-powered analysis
12. Alerts - Real-time monitoring
13. Reports - PDF generation
14. Macro Cycles - 4 economic cycles (STDC, LTDC, Empire, Civil)
15. Corporate Actions - Dividends, splits
16. Market Data - Economic indicators
17. Settings - User preferences

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
   → AgentRuntime routes to LedgerAgent.positions()
   → Query: SELECT * FROM lots WHERE portfolio_id = 'abc-123'
   → Returns: positions
   ↓
7. Execute Step 2: capability="pricing.apply_pack"
   → AgentRuntime routes to PricingAgent.apply_pack()
   → Enriches positions with market prices
   → Returns: valued_positions
   ↓
8. Execute Step 3: capability="metrics.compute_twr"
   → AgentRuntime routes to MetricsAgent.compute_twr()
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
- **Endpoint Protection**: JWT middleware on all /api/* routes (except /api/auth/login)
- **Pattern-Level Rights**: Patterns can require specific rights (e.g., "portfolio_read")

### Data Protection
- **Input Validation**: FastAPI Pydantic models
- **SQL Injection Prevention**: Parameterized queries via asyncpg
- **XSS Prevention**: React's built-in escaping
- **CORS**: Configured for production domain

### Default Credentials (CHANGE IN PRODUCTION!)
- Email: michael@dawsos.com
- Password: mozzuq-byfqyQ-5tefvu

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
```bash
DATABASE_URL="postgresql://user:pass@localhost/dawsos"
ANTHROPIC_API_KEY="sk-ant-..."  # Optional - for AI features
FRED_API_KEY="..."              # Optional - for economic data
AUTH_JWT_SECRET="your-secret-key-change-in-production"
```

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

## Future Considerations

- **Redis Integration**: Currently None, can be added for distributed caching
- **Horizontal Scaling**: Single server currently, can add load balancer
- **Microservices**: Modular backend structure in backend/app/ ready for extraction
- **Message Queue**: For async pattern execution (long-running workflows)
