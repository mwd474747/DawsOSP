# DawsOS - AI-Powered Portfolio Management Platform

## Overview

DawsOS is a comprehensive portfolio management and intelligence platform that combines real-time market data, economic analysis, and AI-powered insights. The system uses a microservices architecture with FastAPI backend, Next.js frontend, PostgreSQL database, and Redis caching.

**Core Purpose**: Provide institutional-grade portfolio analysis, risk management, macro regime detection, and optimization capabilities through an intuitive web interface.

**Key Capabilities**:
- Portfolio performance tracking and attribution analysis
- Multi-currency support with FX attribution
- Macro regime detection using economic indicators
- AI-powered scenario analysis and stress testing
- Real-time alerts and notifications
- PDF report generation
- Portfolio optimization recommendations

## Recent Updates

### October 29, 2025 - Macro Dashboard Enhancement
- **New Navigation Item**: Added "Macro Dashboard" as the 8th tab in the navigation bar
- **Dedicated Page**: Moved macro economic insights from modal popup to full-page dashboard
- **Enhanced Visualization**: 
  - Grid layout for economic indicators with visual status indicators
  - Market outlook sections for near-term and medium-term forecasts
  - Color-coded risk levels and regime indicators
- **Interactive Features**: "Refresh Macro Data" button for manual updates
- **Database Integration**: Fully migrated from mock data to PostgreSQL with comprehensive seed data

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture (FastAPI)

**Framework**: FastAPI with async/await for high-performance API endpoints

**API Layer**:
- RESTful endpoints with OpenAPI/Swagger documentation
- JWT-based authentication with role-based access control (RBAC)
- CORS middleware configured for Next.js frontend
- Health check endpoints for container monitoring

**Service Layer**:
- `AuthService`: User authentication and JWT token management
- `AlertService`: Alert condition evaluation and notification triggering
- `MacroService`: Economic regime detection and classification
- `OptimizerService`: Portfolio optimization using Riskfolio-lib
- `NotificationService`: Multi-channel notification delivery
- `AlertDeliveryService`: Delivery tracking with retry logic and DLQ

**Data Access Layer**:
- Async PostgreSQL queries using asyncpg
- Connection pooling for performance
- Parameterized queries for SQL injection protection
- Pricing pack queries for immutable historical data

**Background Jobs**:
- `build_pricing_pack.py`: Daily pricing data collection from Polygon API
- `compute_macro.py`: Nightly macro regime detection using FRED data
- `evaluate_alerts.py`: Alert condition evaluation and notification
- `alert_retry_worker.py`: Failed notification retry with exponential backoff

**Compliance System**:
- `RightsRegistry`: Data source usage rights and export restrictions
- `ExportBlocker`: Enforce export restrictions (e.g., NewsAPI view-only)
- `AttributionManager`: Generate proper data source attributions
- `WatermarkSystem`: Apply watermarks to exported data

### Frontend Architecture (Next.js)

**Framework**: Next.js 15 with App Router and TypeScript

**UI Components**:
- React 18 with TypeScript for type safety
- Radix UI primitives for accessible components
- TailwindCSS with custom design system (Fibonacci spacing, golden ratio colors)
- Recharts for data visualization

**State Management**:
- React Query (TanStack Query) for server state management
- Automatic caching and background refetching
- Optimistic updates for better UX
- React Query DevTools for debugging

**API Integration**:
- Axios HTTP client with interceptors
- Automatic JWT token injection
- Error handling and retry logic
- Type-safe API client with TypeScript interfaces

**Design System**:
- Fibonacci sequence spacing (2px, 3px, 5px, 8px, 13px, 21px, 34px, 55px, 89px, 144px)
- Golden angle color distribution for visual harmony
- Responsive breakpoints for mobile/tablet/desktop
- Dark theme optimized for financial data

### Database Architecture (PostgreSQL)

**Primary Database**: PostgreSQL 14+ with async connection pooling

**Core Schema**:
- `users`: User accounts with role-based permissions
- `portfolios`: Portfolio definitions and metadata
- `securities`: Security master (stocks, ETFs, bonds)
- `transactions`: Transaction history (buys, sells, dividends)
- `pricing_packs`: Immutable daily pricing snapshots
- `portfolio_metrics`: Computed performance metrics
- `alerts`: User-defined alert conditions
- `macro_snapshots`: Daily macro regime classifications

**Key Design Decisions**:

1. **Immutable Pricing Packs**: Historical price data is never modified, only superseded with explicit chain tracking. This ensures audit trail and reproducibility.

2. **Pricing Pack Architecture**: Daily pricing snapshots (PP_YYYY-MM-DD) contain all prices and FX rates. Benefits include O(1) lookup, cache efficiency, and historical accuracy.

3. **Multi-Currency Support**: All positions stored in local currency, converted to base currency using pricing pack FX rates. Enables accurate currency attribution.

4. **Supersede Chain**: When historical data needs correction, create new pack with `superseded_by` pointer. Never mutate existing packs.

**Performance Optimizations**:
- Indexes on portfolio_id, security_id, trade_date for fast queries
- Connection pooling with asyncpg (10-20 connections)
- Materialized views for complex aggregations (future enhancement)

### Authentication & Authorization

**Authentication**: JWT tokens with 24-hour expiration

**Password Security**: Bcrypt hashing with salt

**Authorization**: Role-based access control with 4 levels:
- `ADMIN`: Full system access (user management, configuration)
- `MANAGER`: Portfolio management and reporting
- `USER`: Standard portfolio access
- `VIEWER`: Read-only access

**Super Admin Account**:
- Email: michael@dawsos.com
- Password: admin123
- Role: ADMIN

**Security Features**:
- JWT middleware validation on protected routes
- Input validation using Pydantic models
- SQL injection protection via parameterized queries
- HTTPS enforcement in production

### Data Flow Architecture

**Request Flow**:
1. User action in Next.js UI
2. API call via Axios with JWT token
3. FastAPI middleware validates JWT
4. Service layer executes business logic
5. Data layer queries PostgreSQL
6. Response serialized as JSON
7. React Query updates UI state

**Background Job Flow**:
1. APScheduler triggers nightly jobs
2. Fetch data from external APIs (Polygon, FRED)
3. Compute metrics and analytics
4. Store results in PostgreSQL
5. Trigger alerts if conditions met
6. Send notifications via channels

**Alert Flow**:
1. User creates alert condition in UI
2. Nightly job evaluates all active alerts
3. Check cooldown periods to prevent spam
4. Send notifications via configured channels
5. Failed deliveries pushed to DLQ
6. Retry worker processes DLQ with exponential backoff

## External Dependencies

### Third-Party APIs

**Polygon.io** (Market Data):
- Real-time stock quotes and historical prices
- Options data and Greeks
- FX rates (WM Reuters 4PM fixing)
- API key required: `POLYGON_API_KEY`
- Rate limits: 5 requests/minute (free tier)

**FRED (Federal Reserve Economic Data)**:
- Economic indicators (unemployment, GDP, inflation)
- Macro regime detection factors
- Public domain data with attribution
- API key required: `FRED_API_KEY`

**Financial Modeling Prep (FMP)**:
- Fundamental data (balance sheets, income statements)
- Company profiles and metadata
- Historical financials
- API key required: `FMP_API_KEY`
- Attribution required for exports

**NewsAPI**:
- Market news and sentiment
- View-only (no export per TOS)
- API key required: `NEWS_API_KEY`

**Anthropic Claude**:
- AI-powered analysis and insights
- Scenario generation
- Natural language queries
- API key required: `ANTHROPIC_API_KEY`

### Databases & Caching

**PostgreSQL**:
- Primary data store
- Connection string: `DATABASE_URL`
- Minimum version: 14+
- Optional: TimescaleDB extension for time-series optimization

**Redis**:
- API response caching
- Rate limiting state
- Session storage
- Connection: `REDIS_URL` or localhost:6379

### Infrastructure Services

**Docker & Docker Compose**:
- Container orchestration for all services
- Development and production deployments
- Health checks and auto-restart

**APScheduler**:
- Background job scheduling
- Nightly pricing pack builds (00:15)
- Macro computation (00:20)
- Metrics calculation (00:30)
- Alert evaluation (00:35)

### Python Libraries

**Core Framework**:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `asyncpg`: Async PostgreSQL driver

**Data Processing**:
- `pandas`: Data manipulation
- `numpy`: Numerical computing
- `scikit-learn`: Statistical models

**Portfolio Optimization**:
- `riskfolio-lib`: Mean-variance optimization
- `scipy`: Optimization algorithms

**Authentication**:
- `passlib[bcrypt]`: Password hashing
- `python-jose`: JWT token handling
- `email-validator`: Email validation

**API Clients**:
- `httpx`: Async HTTP client
- `aiohttp`: Alternative async HTTP
- `requests`: Synchronous HTTP fallback

### Frontend Libraries

**Core Framework**:
- `next`: Next.js framework
- `react`: UI library
- `typescript`: Type safety

**UI Components**:
- `@radix-ui/*`: Accessible component primitives
- `tailwindcss`: Utility-first CSS
- `class-variance-authority`: Component variants

**Data Fetching**:
- `@tanstack/react-query`: Server state management
- `axios`: HTTP client

**Visualization**:
- `recharts`: Chart library

### Development Tools

**Testing**:
- `pytest`: Python test framework
- `pytest-asyncio`: Async test support

**Code Quality**:
- `eslint`: JavaScript/TypeScript linting
- `autoprefixer`: CSS vendor prefixes
- `postcss`: CSS transformations

**Monitoring** (Optional):
- `prometheus-client`: Metrics collection
- `opentelemetry-*`: Distributed tracing
- `sentry-sdk`: Error tracking