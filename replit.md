# DawsOS - AI-Powered Portfolio Management Platform

## Overview

DawsOS is an AI-powered portfolio management platform that provides comprehensive portfolio analysis, macro economic cycle tracking, and investment quality ratings. The system uses a pattern-driven agent orchestration architecture where specialized agents execute declarative JSON workflow patterns.

**Core Capabilities:**
- Real-time portfolio tracking with multi-currency support
- AI-powered analysis using Claude API
- Macro economic cycle analysis (4 Ray Dalio cycles)
- Buffett-style quality ratings for holdings
- Risk analysis and scenario testing
- PDF report generation

**Technology Stack:**
- Backend: FastAPI (Python 3.9+)
- Frontend: React 18 (no build step, served from single HTML file)
- Database: PostgreSQL 14+ with TimescaleDB extension
- AI: Anthropic Claude API
- Deployment: Replit-first (no Docker)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Entry Points

**Production Server:**
- File: `combined_server.py` (6,046 lines)
- Single FastAPI application serving both API and UI
- 59 REST endpoints at `/api/*`
- Serves `full_ui.html` at root `/`
- Command: `python combined_server.py`
- Port: 8000

**Frontend:**
- File: `full_ui.html` (14,075 lines)
- Self-contained React 18 SPA with no build step
- 17 complete UI pages
- Uses UMD builds of React from CDN
- API client in `frontend/api-client.js`

### Pattern Orchestration System

The core architectural pattern is **declarative workflow execution**:

1. **Pattern Definitions** (JSON files in `backend/patterns/`)
   - 12 patterns total: `portfolio_overview`, `buffett_checklist`, `macro_cycles_overview`, etc.
   - Define multi-step workflows with template substitution
   - Use `{{inputs.x}}`, `{{state.y}}`, `{{ctx.z}}` syntax

2. **Pattern Orchestrator** (`backend/app/core/pattern_orchestrator.py`)
   - Loads JSON patterns
   - Executes steps sequentially as DAG
   - Resolves template variables
   - Routes capability calls to agents
   - Returns structured results with execution traces

3. **Agent Runtime** (`backend/app/core/agent_runtime.py`)
   - Manages 9 specialized agents
   - Routes capability strings like `"ledger.positions"` to agent methods
   - Provides immutable `RequestCtx` for reproducibility

### Agent Architecture

**9 Specialized Agents** (registered in `combined_server.py:239-304`):

1. **FinancialAnalyst** - Portfolio positions, pricing, metrics, attribution
2. **MacroHound** - Economic cycles, regime detection, scenarios
3. **DataHarvester** - External data (FMP, FRED, NewsAPI, Polygon)
4. **ClaudeAgent** - AI explanations and insights
5. **RatingsAgent** - Quality ratings (moat, dividend safety, resilience)
6. **OptimizerAgent** - Portfolio optimization and rebalancing
7. **AlertAgent** - Monitoring and notifications
8. **ReportAgent** - PDF generation
9. **ComplianceAgent** - Access control and attribution

**Agent Capability Pattern:**
```python
# Pattern calls capability by string
{"capability": "ratings.aggregate", "args": {...}, "as": "ratings"}

# Runtime routes to agent method
RatingsAgent.aggregate(ctx, security_id) -> dict
```

### Database Schema

**Core Tables:**
- `portfolios` - Portfolio metadata and ownership
- `securities` - Stock/asset master data
- `lots` - Tax lot tracking with FIFO/LIFO/HIFO support
- `transactions` - Buy/sell/dividend/split events
- `prices` - Time-series pricing data
- `pricing_packs` - Snapshot consistency mechanism
- `portfolio_daily_values` - TimescaleDB hypertable for NAV
- `portfolio_cash_flows` - Cash flow tracking for MWR

**Design Decisions:**
- TimescaleDB for time-series efficiency on daily values
- Pricing packs ensure consistent snapshots across queries
- Row-Level Security (RLS) for multi-tenancy
- Tax lot accounting supports multiple cost basis methods

### Authentication & Authorization

**JWT-based authentication:**
- Login: `POST /api/auth/login` returns access token
- Refresh: `POST /api/auth/refresh` extends token
- Token stored in localStorage by frontend
- Role-based access control (ADMIN, MANAGER, USER, VIEWER)

**Security mechanisms:**
- Password hashing with bcrypt
- JWT secret from environment variable `AUTH_JWT_SECRET`
- Database RLS policies enforce user isolation
- API endpoints check token and role permissions

### Request Flow Pattern

```
User Action (full_ui.html)
  ↓
API Call with JWT token
  ↓
FastAPI endpoint (combined_server.py)
  ↓
Pattern Orchestrator (for /api/patterns/execute)
  ↓
Agent Runtime → Agent → Service Layer
  ↓
Database via asyncpg connection pool
  ↓
Response with data + trace
```

### Data Provenance System

All data results include `_provenance` metadata:
```json
{
  "data": {...},
  "_provenance": {
    "type": "real|stub|cached",
    "source": "fmp|fred|database",
    "confidence": "high|medium|low",
    "timestamp": "ISO-8601",
    "warnings": []
  }
}
```

This ensures transparency about data quality and source for AI-driven decisions.

### PDF Report Generation

- Uses `reportlab` library
- Template in `backend/app/services/pdf_generator.py`
- Includes portfolio metrics, holdings, performance charts
- Watermarking support for access tracking
- Export via `export_portfolio_report` pattern

## External Dependencies

### Database

**PostgreSQL 14+ with TimescaleDB:**
- Environment variable: `DATABASE_URL`
- Connection pooling via asyncpg
- TimescaleDB extension required for hypertables
- Replit provides managed PostgreSQL service

### API Keys (Optional for Real Data)

All external APIs have stub fallbacks, so the application works without keys:

**Financial Data:**
- `FMP_API_KEY` - Financial Modeling Prep (fundamentals, financials)
- `POLYGON_API_KEY` - Polygon.io (market data)
- `FRED_API_KEY` - Federal Reserve Economic Data (macro indicators)

**News & AI:**
- `NEWS_API_KEY` - NewsAPI.org (company news)
- `ANTHROPIC_API_KEY` - Claude API (AI explanations)

**Data Fallback Strategy:**
- DataHarvester checks for API keys
- Returns stub data with `_provenance.type = "stub"` if unavailable
- Stub data is differentiated by security to enable realistic testing

### External Services Integration

**FMP (Financial Modeling Prep):**
- Fundamentals, income statements, balance sheets
- Integration: `backend/app/integrations/fmp_provider.py`

**FRED (Federal Reserve):**
- Macro indicators (GDP, inflation, unemployment, etc.)
- Integration: `backend/app/integrations/fred_provider.py`

**NewsAPI:**
- Company-specific news articles
- Integration: `backend/app/integrations/news_provider.py`

**Polygon.io:**
- Real-time and historical market data
- Integration: `backend/app/integrations/polygon_provider.py`

**Anthropic Claude:**
- AI-powered explanations and insights
- Integration: `backend/app/integrations/claude_provider.py`

### Python Package Dependencies

See `backend/requirements.txt` and root `requirements.txt`:

**Core:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `asyncpg` - PostgreSQL async driver
- `pydantic` - Data validation

**Data & ML:**
- `pandas`, `numpy` - Data processing
- `scikit-learn` - Machine learning utilities
- `riskfolio-lib` - Portfolio optimization

**External Integrations:**
- `httpx`, `aiohttp`, `requests` - HTTP clients
- `anthropic` - Claude API client

**Auth & Security:**
- `python-jose` - JWT handling
- `passlib[bcrypt]` - Password hashing

### Environment Configuration

Required environment variables for production:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dawsos
AUTH_JWT_SECRET=your-secret-key-here

# Optional - enables real data
FMP_API_KEY=your-fmp-key
POLYGON_API_KEY=your-polygon-key
FRED_API_KEY=your-fred-key
NEWS_API_KEY=your-news-key
ANTHROPIC_API_KEY=your-anthropic-key
```

Set in Replit Secrets tab or `.env` file (gitignored).