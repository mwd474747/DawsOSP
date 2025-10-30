# DawsOS - AI-Powered Portfolio Management Platform

## Overview

DawsOS is a comprehensive, AI-powered portfolio management and intelligence platform designed for institutional-grade analysis. It integrates real-time market data, economic analysis, and AI insights through a pattern-orchestrated microservices architecture. The platform's core purpose is to provide advanced portfolio analysis, risk management, macro regime detection, and optimization capabilities via an intuitive web interface. Key capabilities include performance tracking, multi-currency support, AI-powered scenario analysis, real-time alerts, PDF report generation, and optimization recommendations. The system is built on a FastAPI backend, PostgreSQL database, and Redis caching.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Updates

### October 31, 2025 - Database Pool Bridge Implementation (COMPLETED)
- **Critical Issue Resolved**: Fixed disconnected database access patterns causing agent failures
  - combined_server.py creates its own asyncpg pool directly
  - Backend agents expect get_db_pool() from RedisPoolCoordinator pattern  
  - Previously: "Database pool not initialized" errors, circuit breakers opening
- **Root Cause**: Evolution without coordination - different components developed independently
- **Solution Implemented**: "Share the Pool" approach successfully bridges the gap
  - ✅ Bridged combined_server pool to backend PoolManager singleton
  - ✅ Modified get_db_pool() to check PoolManager first, then Redis fallback
  - ✅ Circuit breakers properly reset after successful initialization
- **Testing Results**:
  - Database pool successfully shared between frontend and backend patterns
  - All 6 agents registered with 52 total capabilities
  - Pattern orchestrator executing with real data
  - API endpoints returning portfolio data successfully
- **Documentation Created**:
  - REFACTORING_PLAN.md: Detailed implementation steps
  - ARCHITECTURE_DECISIONS.md: ADRs explaining rationale and lessons learned
- **Status**: System stabilized and fully functional

## System Architecture

### Core Architecture
The system follows a Pattern Orchestrator → Agent Runtime → Services architecture. It utilizes 12 JSON workflow patterns to define business logic and 6 specialized agents that execute a total of 52 capabilities. All API endpoints are routed through a pattern orchestrator for consistency.

### Backend Architecture (FastAPI)
- **Framework**: FastAPI with async/await.
- **API Layer**: RESTful endpoints, OpenAPI/Swagger, JWT-based authentication with RBAC, CORS middleware, health checks.
- **Service Layer**: Dedicated services for authentication, alerts, macro analysis, optimization, and notifications.
- **Data Access Layer**: Async PostgreSQL queries using `asyncpg`, connection pooling, parameterized queries, and pricing pack queries.
- **Background Jobs**: Scheduled tasks for pricing data collection, macro regime detection, alert evaluation, and notification retries using APScheduler.
- **Compliance System**: Manages data usage rights, export restrictions (`ExportBlocker`), attribution (`AttributionManager`), and watermarking.

### Frontend Architecture (Next.js)
- **Framework**: Next.js 15 with App Router and TypeScript.
- **UI Components**: React 18, Radix UI primitives, TailwindCSS with a custom design system (Fibonacci spacing, golden ratio colors), Recharts for visualizations.
- **State Management**: React Query (TanStack Query) for server state management, including caching, background refetching, and optimistic updates.
- **API Integration**: Axios HTTP client with interceptors for JWT injection, error handling, and retry logic.
- **Design System**: Professional dark theme with sophisticated dark navy and slate gray, glass morphism navigation, consistent button styles, and monospace fonts for financial data, inspired by Bloomberg Terminal aesthetics.

### Database Architecture (PostgreSQL)
- **Primary Database**: PostgreSQL 14+ with async connection pooling.
- **Core Schema**: Tables for users, portfolios, securities, transactions, immutable pricing packs, portfolio metrics, alerts, and macro snapshots.
- **Key Design Decisions**:
    1.  **Immutable Pricing Packs**: Historical price data is stored in daily snapshots, ensuring audit trails and reproducibility, with a supersede chain for corrections.
    2.  **Multi-Currency Support**: Positions are stored in local currency and converted to base currency using pricing pack FX rates for accurate attribution.
- **Performance Optimizations**: Indexes on key fields and connection pooling.

### Authentication & Authorization
- **Authentication**: JWT tokens with 24-hour expiration.
- **Password Security**: Bcrypt hashing with salt.
- **Authorization**: Role-based access control (ADMIN, MANAGER, USER, VIEWER).
- **Security Features**: JWT middleware validation, Pydantic model validation, SQL injection protection, HTTPS enforcement.

### Data Flow Architecture
- **Request Flow**: User action in UI → API call (Axios + JWT) → FastAPI (middleware, service layer) → PostgreSQL → JSON response → UI update (React Query).
- **Background Job Flow**: APScheduler triggers jobs → Data fetching (external APIs) → Metrics computation → PostgreSQL storage → Alert triggering → Notifications.
- **Alert Flow**: User creates alert → Nightly job evaluates conditions → Cooldown checks → Notifications (configured channels) → Failed deliveries to DLQ for retry.

## External Dependencies

### Third-Party APIs
-   **Polygon.io**: Real-time market data, historical prices, options, FX rates.
-   **FRED (Federal Reserve Economic Data)**: Economic indicators, macro regime detection.
-   **Financial Modeling Prep (FMP)**: Fundamental data, company profiles.
-   **NewsAPI**: Market news and sentiment (view-only).
-   **Anthropic Claude**: AI-powered analysis, scenario generation, natural language queries.

### Databases & Caching
-   **PostgreSQL**: Primary data store.
-   **Redis**: API response caching, rate limiting, session storage.

### Infrastructure Services
-   **Docker & Docker Compose**: Containerization for development and production.
-   **APScheduler**: Background job scheduling.

### Python Libraries
-   **Core Framework**: `fastapi`, `uvicorn`, `pydantic`, `asyncpg`.
-   **Data Processing**: `pandas`, `numpy`, `scikit-learn`.
-   **Portfolio Optimization**: `riskfolio-lib`, `scipy`.
-   **Authentication**: `passlib[bcrypt]`, `python-jose`, `email-validator`.
-   **API Clients**: `httpx`, `aiohttp`, `requests`.

### Frontend Libraries
-   **Core Framework**: `next`, `react`, `typescript`.
-   **UI Components**: `@radix-ui/*`, `tailwindcss`, `class-variance-authority`.
-   **Data Fetching**: `@tanstack/react-query`, `axios`.
-   **Visualization**: `recharts`.