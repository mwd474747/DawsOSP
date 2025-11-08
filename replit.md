# DawsOS - AI-Powered Portfolio Management Platform

## Overview

DawsOS is a production-ready portfolio management platform that combines financial analysis, risk assessment, and AI-powered insights. The system uses a pattern-driven architecture where business workflows are defined in JSON files and executed through specialized agents that provide ~70 capabilities.

**Key Characteristics:**
- **Single-file deployment**: Both server (`combined_server.py`) and UI (`full_ui.html`) are monolithic files
- **No build step**: React 18 SPA runs directly in browser using UMD builds
- **Pattern-driven**: Business logic defined in 15 JSON pattern files
- **Agent-based**: 4 specialized agents provide portfolio analysis, macro analysis, data harvesting, and AI insights
- **Replit-optimized**: Designed for serverless PostgreSQL (Neon-backed) with automatic scaling

**Current State:**
- Production-ready with 59 functional endpoints
- 20 complete UI pages including dashboard, analytics, and reporting
- TimescaleDB-powered time-series analysis
- JWT authentication with role-based access control

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Components

**1. Pattern Orchestration System**

The application uses a declarative pattern system where business workflows are defined in JSON files:

```
Pattern Definition (JSON) → Template Substitution → Agent Capability Calls → Result Aggregation
```

- **Pattern files**: 15 JSON files in `backend/patterns/` define multi-step workflows
- **PatternOrchestrator**: Executes patterns by calling agent capabilities and substituting template variables
- **Request Context (RequestCtx)**: Immutable context ensures reproducibility (pricing_pack_id, ledger_commit_hash, trace_id)
- **Template system**: Dynamic values using `{{inputs.x}}`, `{{step_result}}`, `{{ctx.z}}`

**Key architectural decision**: Patterns are the primary way to compose capabilities. This keeps business logic separate from implementation and allows non-developers to modify workflows.

**2. Agent Architecture (4 Specialized Agents)**

After Phase 3 consolidation (November 2025), the system uses 4 agents:

- **FinancialAnalyst** (~35+ capabilities): Portfolio valuation, performance metrics, attribution analysis, factor analysis
- **MacroHound** (~17+ capabilities): Economic cycle detection, macro regime analysis, scenario analysis
- **DataHarvester** (~8+ capabilities): External data fetching (prices, fundamentals, news, economic data)
- **ClaudeAgent** (~6 capabilities): AI-powered insights, explanations, and analysis using Anthropic's Claude

**Why 4 agents?** Originally 9 agents, consolidated to reduce complexity while maintaining clear separation of concerns. Each agent has a focused domain and minimal dependencies.

**3. Database Architecture**

PostgreSQL 14+ with TimescaleDB extension on Neon serverless infrastructure:

- **Compute-first pattern**: Most metrics computed on-demand from base tables (`lots`, `transactions`, `securities`)
- **Selective caching**: Some tables exist for future optimization but aren't actively used (e.g., `factor_exposures`, `currency_attribution`)
- **Pricing packs**: Immutable snapshots of prices + FX rates for reproducible analysis
- **Row-Level Security (RLS)**: User-scoped data enforces multi-tenancy at database level

**Connection patterns**:
- Pattern A: RLS-aware connections for user data (`get_db_connection_with_rls(user_id)`)
- Pattern B: Helper functions for system data (`execute_query()`, `execute_statement()`)

**Why compute-first?** Avoids storage bloat for infrequently accessed data. Can switch to caching hot data when needed without schema changes.

**4. Single-File Deployments**

- **Server**: `combined_server.py` (6,043 lines) - FastAPI monolith with all endpoints
- **UI**: `full_ui.html` (11,594 lines) - React 18 SPA with no build step

**Why monolithic?** Optimized for Replit deployment where splitting files adds complexity without benefits. The entire application starts with `python combined_server.py`.

**5. Authentication & Authorization**

- **JWT tokens**: Generated on login, stored in localStorage
- **Role-based access**: ADMIN, MANAGER, USER, VIEWER roles
- **Centralized auth**: `Depends(require_auth)` pattern across all protected endpoints
- **Audit logging**: All actions logged to `audit_log` table

### Key Design Decisions

**1. No frontend build step**

Uses React UMD builds loaded from CDN. Components written in plain JavaScript using React.createElement(). 

**Rationale**: Eliminates build complexity, makes UI changes instant, reduces deployment dependencies.

**2. Pattern-driven business logic**

Business workflows defined in JSON rather than hardcoded in Python/JavaScript.

**Rationale**: Non-developers can modify workflows, business logic is testable independently of implementation, easier to audit and version control.

**3. Pricing pack immutability**

Every analysis uses a specific pricing pack (snapshot of prices + FX rates). Same pack = identical results.

**Rationale**: Ensures reproducibility - running the same analysis twice produces identical results regardless of when it's run.

**4. Compute-first with optional storage**

Most metrics computed from base tables on-demand. Cache tables exist but aren't actively used.

**Rationale**: Reduces storage bloat, keeps data fresh, allows future optimization without schema changes. TimescaleDB makes historical queries fast enough.

**5. Agent consolidation (9 → 4)**

Originally had 9 agents with overlapping responsibilities. Consolidated to 4 focused agents.

**Rationale**: Reduces complexity, eliminates duplication, maintains separation of concerns. Each agent has clear domain and minimal dependencies.

### Known Limitations & Future Work

**Current limitations**:
- Some patterns return stub data with provenance warnings (factor analysis, DaR computation)
- Tax harvesting features archived (deferred implementation)
- No real-time updates (manual refresh required)
- Limited caching (redundant pattern executions)

**Refactoring status** (as of January 2025):
- Phase 0-3: Complete (zombie code removal, field standardization, agent consolidation)
- Phase 4: Pending (end-to-end testing, stub removal, UI polish)

## External Dependencies

### Required Services

**Database**: 
- PostgreSQL 14+ with TimescaleDB extension
- Provided by Replit (Neon serverless infrastructure)
- Auto-scaling, cost-efficient (charges only when active)
- Credentials auto-configured via `DATABASE_URL` environment variable

**Authentication**:
- JWT secret key required (`AUTH_JWT_SECRET` environment variable)
- Generated with: `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`

### Optional External APIs

**Data providers** (all optional, system degrades gracefully):

- **FMP (Financial Modeling Prep)**: Fundamentals data, company information
  - Environment variable: `FMP_API_KEY`
  - Used by: DataHarvester agent, fundamentals analysis

- **Polygon.io**: Real-time and historical price data
  - Environment variable: `POLYGON_API_KEY`
  - Used by: DataHarvester agent, pricing pack population

- **FRED (Federal Reserve Economic Data)**: Economic indicators, FX rates
  - Environment variable: `FRED_API_KEY`
  - Used by: MacroHound agent, economic cycle detection

- **Anthropic Claude**: AI-powered insights and explanations
  - Environment variable: `ANTHROPIC_API_KEY`
  - Used by: ClaudeAgent, AI insights page

**Graceful degradation**: If API keys aren't provided, features show warnings or fall back to limited functionality. Core portfolio management works without any external APIs.

### Python Dependencies

Key packages (see `requirements.txt`):

- **FastAPI + Uvicorn**: Web framework and ASGI server
- **asyncpg**: Async PostgreSQL driver with connection pooling
- **pyjwt + passlib**: Authentication (JWT tokens, password hashing)
- **httpx**: Async HTTP client for external APIs
- **anthropic**: Claude AI SDK (optional)
- **pandas + numpy**: Data analysis
- **scikit-learn**: Factor analysis, regression models
- **weasyprint + reportlab**: PDF report generation

### Frontend Dependencies

Loaded from CDN (no npm/build required):

- **React 18.2.0** (UMD build)
- **React DOM 18.2.0** (UMD build)
- **Axios 1.6.2**: HTTP client
- **Chart.js 4.4.0**: Visualizations
- **IBM Plex fonts**: Typography

### Replit-Specific Configuration

**Critical files** (DO NOT MODIFY):
- `.replit`: Deployment configuration (run command, ports)
- Port 5000: Hardcoded in server and `.replit` file

**Auto-configured**:
- Database credentials via environment variables
- Connection pooling (2-10 connections)
- Automatic snapshots with code checkpoints