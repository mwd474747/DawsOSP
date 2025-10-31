# DawsOS - AI-Powered Portfolio Management Platform

## Overview
DawsOS is a comprehensive, AI-powered portfolio management and intelligence platform for institutional-grade analysis. It integrates real-time market data, economic analysis, and AI insights through a pattern-orchestrated microservices architecture. The platform provides advanced portfolio analysis, risk management, macro regime detection, and optimization via an intuitive web interface. Key capabilities include performance tracking, multi-currency support, AI-powered scenario analysis, real-time alerts, PDF report generation, and optimization recommendations. The system is built on a FastAPI backend, PostgreSQL database, and Redis caching.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes (October 31, 2025)

### Completed: Metrics Infrastructure Implementation
- **Database**: Created `portfolio_daily_values` and `portfolio_cash_flows` tables with TimescaleDB hypertables
- **Historical Data**: Backfilled 700+ days (Dec 2023 - Oct 2025) of portfolio valuations
- **Metrics Pipeline**: Functional TWR/MWR calculations using real data - $1.6M portfolio with accurate performance metrics
- **UI Transactions**: Fixed to display 35 real ledger transactions instead of mock data
- **Technical Debt**: Eliminated all simulated NAV generation and stub patterns - metrics now fail explicitly on missing data
- **Manual Process**: Metrics updated via `compute_metrics_simple.py` (automated scheduling deferred)

## System Architecture

### Core Architecture
The system follows a Pattern Orchestrator → Agent Runtime → Services architecture. It uses 12 JSON workflow patterns to define business logic and 6 specialized agents that execute a total of 52 capabilities. All API endpoints are routed through a pattern orchestrator.

### Single-File HTML UI Architecture
The frontend is a single HTML file (`full_ui.html`) containing the entire application. It uses React without JSX (`React.createElement`), a custom client-side router, and an enhanced API client with token refresh, retry mechanisms, and structured error handling. It includes a React Query-inspired caching layer for pattern results, background refetching, and cache invalidation. Over 40 reusable business logic functions are organized by domain. The UI features comprehensive error boundaries and graceful degradation.

### Backend Architecture (FastAPI)
- **Framework**: FastAPI with async/await.
- **API Layer**: RESTful endpoints, OpenAPI/Swagger, JWT authentication with RBAC, CORS middleware, health checks.
- **Service Layer**: Dedicated services for authentication, alerts, macro analysis, optimization, and notifications.
- **Data Access Layer**: Async PostgreSQL queries using `asyncpg`, connection pooling, parameterized queries.
- **Background Jobs**: Scheduled tasks for data collection, macro regime detection, alert evaluation, and notification retries using APScheduler.
- **Compliance System**: Manages data usage rights, export restrictions, attribution, and watermarking.

### Frontend Architecture (Single-File HTML)
- **Framework**: Pure HTML/CSS/JavaScript with React 18 (UMD builds, no build step).
- **Architecture Benefits**: Zero build time, single-file deployment, no dependency management, reduced bundle size (~1MB), faster initial load.
- **UI Components**: React components using `createElement`, custom component library, Chart.js for visualizations, glass morphism effects.
- **State Management**: Local component state, pattern result caching, background data refresh, optimistic UI updates.
- **API Integration**: Enhanced Axios client with JWT token management (automatic refresh), exponential backoff retry logic, request queue, comprehensive error handling.
- **Design System**: Bloomberg Terminal-inspired dark theme, IBM Plex Sans/Mono fonts, consistent color semantics, glass morphism sidebar, responsive grid layouts.

### Database Architecture (PostgreSQL)
- **Primary Database**: PostgreSQL 14+ with async connection pooling.
- **Core Schema**: Tables for users, portfolios, securities, transactions, immutable pricing packs, portfolio metrics, alerts, and macro snapshots.
- **Key Design Decisions**: Immutable Pricing Packs (historical snapshots with supersede chain), Multi-Currency Support (positions in local currency converted to base).
- **Performance Optimizations**: Indexes and connection pooling.

### Authentication & Authorization
- **Authentication**: JWT tokens (24-hour expiration).
- **Password Security**: Bcrypt hashing with salt.
- **Authorization**: Role-based access control (ADMIN, MANAGER, USER, VIEWER).
- **Security Features**: JWT middleware validation, Pydantic model validation, SQL injection protection, HTTPS enforcement.

### Data Flow Architecture
- **Request Flow**: UI action → API call (Enhanced Axios + JWT) → FastAPI (middleware, service layer) → PostgreSQL → JSON response → UI update.
- **Background Job Flow**: APScheduler triggers jobs → Data fetching (external APIs) → Metrics computation → PostgreSQL storage → Alert triggering → Notifications.
- **Alert Flow**: User creates alert → Nightly job evaluates conditions → Cooldown checks → Notifications (configured channels).

## External Dependencies

### Third-Party APIs
-   **Polygon.io**: Real-time market data, historical prices, options, FX rates.
-   **FRED (Federal Reserve Economic Data)**: Economic indicators, macro regime detection.
-   **Financial Modeling Prep (FMP)**: Fundamental data, company profiles.
-   **NewsAPI**: Market news and sentiment.
-   **Anthropic Claude**: AI-powered analysis, scenario generation, natural language queries.

### Databases & Caching
-   **PostgreSQL**: Primary data store.
-   **Redis**: API response caching, rate limiting, session storage.

### Infrastructure Services
-   **Docker & Docker Compose**: Containerization.
-   **APScheduler**: Background job scheduling.

### Python Libraries
-   **Core Framework**: `fastapi`, `uvicorn`, `pydantic`, `asyncpg`.
-   **Data Processing**: `pandas`, `numpy`, `scikit-learn`.
-   **Portfolio Optimization**: `riskfolio-lib`, `scipy`.
-   **Authentication**: `passlib[bcrypt]`, `python-jose`, `email-validator`.
-   **API Clients**: `httpx`, `aiohttp`, `requests`.

### Frontend Libraries
-   **Core Framework**: React 18 (UMD builds via CDN).
-   **HTTP Client**: Axios (via CDN).
-   **Visualization**: Chart.js (via CDN).
-   **Fonts**: IBM Plex Sans/Mono (Google Fonts).