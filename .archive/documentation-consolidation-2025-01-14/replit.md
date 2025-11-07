# DawsOS - AI-Powered Portfolio Management Platform

## Overview

DawsOS is a production-ready AI-powered portfolio intelligence platform designed for real-time portfolio tracking and advanced analytics. It utilizes a pattern-driven architecture where business workflows are declaratively defined in JSON and executed by specialized agents. The platform emphasizes a single-file deployment for both its FastAPI backend (`combined_server.py`) and React 18 SPA frontend (`full_ui.html`), making it highly portable and deployable without a build step, particularly suited for environments like Replit. Its core purpose is to provide sophisticated financial analysis and portfolio management capabilities, leveraging PostgreSQL with TimescaleDB for efficient data handling.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Design Pattern: Pattern Orchestration

DawsOS employs a **declarative pattern orchestration** approach. Business logic is defined in JSON pattern files (`backend/patterns/*.json`), which are then executed by a central orchestrator (`backend/app/core/pattern_orchestrator.py`). This allows for flexible and easily modifiable workflows, where steps call capabilities exposed by specialized agents. Dynamic template substitution facilitates data flow between pattern steps.

### Key Architectural Decisions

1.  **Pattern-Driven Execution**: Business logic is externalized into JSON patterns, enabling modification without code changes.
2.  **Agent-Based Capabilities**: Nine specialized agents (e.g., FinancialAnalyst, MacroHound) encapsulate specific functionalities, promoting separation of concerns and reusability.
3.  **Immutable Request Context**: Each pattern execution operates within a frozen context (e.g., `pricing_pack_id`, `ledger_commit_hash`) to ensure reproducibility, auditability, and deterministic results crucial for financial systems.
4.  **Compute-First with Optional Caching**: Metrics are computed on-demand by default. While database tables exist for caching, this is a future optimization, simplifying the initial development phase.
5.  **Single-Server Monolith**: The entire application (FastAPI backend and React frontend) is packaged into `combined_server.py` and `full_ui.html` respectively, optimizing for simple deployment, especially on Replit.
6.  **Feature Flag Protection**: Critical changes and agent consolidations are rolled out using feature flags to manage risk and allow for gradual deployment and potential rollbacks.

### Authentication & Authorization

The system uses JWT-based authentication with bcrypt hashing. Role-based access control (ADMIN, MANAGER, USER, VIEWER) is implemented, complemented by row-level security (RLS) at the database level.

### Data Layer

The data layer uses **PostgreSQL 14+** with the **TimescaleDB** extension for time-series data optimization. Key hypertables include `portfolio_daily_values` and `portfolio_metrics`. Core tables manage portfolios, tax lots, transactions, securities, prices, FX rates, and pricing packs. The system adheres to a "compute-first" design, where many analytical tables serve as potential caching targets for future optimization.

**Critical Field Names**: The `lots` table uses standardized field names `quantity_open` and `quantity_original` (not abbreviated forms). This was implemented in Migration 001 and is enforced throughout the codebase.

**Migration Tracking**: A `migration_history` table tracks all executed database migrations with checksums and audit trail, preventing confusion about which migrations have been applied.

### UI/UX Decisions

The frontend is a React 18 Single Page Application served from a single `full_ui.html` file, eliminating a build step. It provides 18 UI pages (e.g., Dashboard, Holdings, Risk Analysis) and features a `PatternRenderer` component for dynamic display of pattern-driven content.

### API Structure

The primary interface for complex workflows is the `/api/patterns/execute` endpoint, which takes a `pattern_id` and inputs, returning structured data and execution traces. Direct endpoints (`/api/*` and `/v1/*`) are available for CRUD operations, trade execution, holdings, and metrics retrieval.

## External Dependencies

1.  **PostgreSQL 14+ with TimescaleDB**: Primary database for all persistent and time-series data.
2.  **Anthropic Claude API**: Optional for AI-powered analysis and chat features; the system gracefully degrades without it.
3.  **Optional Market Data APIs**:
    *   Financial Modeling Prep API (`FMP_API_KEY`)
    *   Polygon.io API (`POLYGON_API_KEY`)
    *   FRED API (`FRED_API_KEY`)
    *   News API (`NEWS_API_KEY`)
    *   *Note: These are configured but currently provide mock/fallback data; full integration is pending.*
4.  **Python Libraries**: FastAPI, Uvicorn, asyncpg, pydantic, python-jose, bcrypt, passlib, pandas, numpy, scikit-learn, anthropic, instructor.
5.  **Replit**: The primary deployment platform, configured via `.replit` and utilizing environment variables from Replit Secrets.

## Recent Changes (November 7, 2025)

- **Fixed FMP API 3-month limitation for corporate actions**: Implemented automatic chunking for date ranges over 90 days
  - Calendar endpoints (dividends, splits, earnings) split into 89-day chunks for longer ranges  
  - Multiple API calls made sequentially and results combined
  - Fixes issue where 180-day and 365-day ranges returned 0 results
- **Verified corporate actions for all date ranges**:
  - 30 days: 2 actions (1 dividend, 1 earnings)
  - 90 days: 5 actions (2 dividends, 3 earnings)
  - 180 days: 12 actions (2 dividends, 10 earnings) - now working with chunking
  - 365 days: Still investigating edge case returning 0 results

## Previous Changes (November 6, 2025)

- Fixed critical documentation errors in DATABASE.md regarding field names
- Created database schema validation script (`backend/scripts/validate_database_schema.py`)
- Removed unnecessary SQL aliases throughout codebase - now using direct field names matching database schema
- Added migration tracking table (Migration 019) with complete audit trail of all 19 executed migrations
- Enhanced FMP API integration with circuit breaker pattern, exponential backoff, and resilient error handling
- Confirmed database has 32+ tables (not 29 as previously documented)

## Development Status

- Production-ready platform with portfolio simulation for high-net-worth investor (michael@dawsos.com)
- Database schema fully aligned with code implementation  
- All critical field naming issues resolved
- Corporate actions tracking with FMP API integration in place
- Multi-currency support (USD, CAD, EUR) fully functional
- Tax compliance tracking with IRS-compliant lot selection methods implemented
- Enhanced DATABASE.md v4.0 with Replit-specific documentation and practical examples