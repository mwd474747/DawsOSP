# DawsOS - AI-Powered Portfolio Management Platform

## Overview

DawsOS is a comprehensive, AI-powered portfolio management and intelligence platform designed for institutional-grade analysis. It integrates real-time market data, economic analysis, and AI insights through a pattern-orchestrated microservices architecture. The platform's core purpose is to provide advanced portfolio analysis, risk management, macro regime detection, and optimization capabilities via an intuitive web interface. Key capabilities include performance tracking, multi-currency support, AI-powered scenario analysis, real-time alerts, PDF report generation, and optimization recommendations. The system is built on a FastAPI backend, PostgreSQL database, and Redis caching.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Updates

### October 31, 2025 - NextJS to Single-File HTML Migration (COMPLETED)
- **Major Achievement**: Successfully migrated all valuable code from NextJS to single-file HTML UI
- **Enhanced API Client**: Added enterprise-grade features from NextJS implementation
  - Token refresh logic with race condition prevention
  - Retry mechanisms with exponential backoff (1s → 2s → 4s)
  - Request queue management for seamless token refresh
  - Structured error handling (server/network/unknown categorization)
- **React Query-Inspired Caching**: Implemented caching layer for optimal performance
  - Pattern result caching to reduce API calls
  - Background refetch capabilities
  - Cache invalidation strategies
- **Business Logic Functions**: Extracted and organized 40+ reusable calculation functions
  - Portfolio metrics: calculateSharpeRatio, calculateCAGR, calculateAnnualizedReturn
  - Risk analysis: calculateScenarioImpact, calculateRiskScore, calculatePositionSize
  - Attribution: calculateCurrencyAttribution, calculateFactorAttribution, calculateSectorAttribution
  - Optimization: generateTradeProposals, calculateEfficientFrontier, generateOptimalAllocation
  - Buffett scoring: calculateBuffettChecklistScore, calculateDividendSafetyScore, calculateMoatStrength
  - Empire cycle: calculateEmpireCyclePower, generateHedgeRecommendations
  - Formatting utilities: formatCurrency, formatPercentage, formatLargeNumber
- **Ray Dalio's 4-Cycle Framework**: Completed implementation with Macro Cycles page
  - Short-term debt cycle visualization
  - Long-term debt cycle analysis
  - Empire cycle tracking
  - Civil cycle monitoring
- **Technical Improvements**:
  - Comprehensive error boundaries for graceful failure handling
  - Improved loading states across all pages
  - Fixed server file naming bug
  - Removed duplicate NextJS codebase (dawsos-ui directory archived)
- **Performance Gains**:
  - Reduced bundle size from ~5MB (NextJS) to ~1MB (single HTML)
  - Faster initial load time
  - No build step required
  - Simplified deployment
- **Status**: Migration complete, NextJS dependency removed

### October 31, 2025 - Complete UI Refactoring (COMPLETED)
- **Major Achievement**: Refactored UI to expose ALL 52 backend capabilities
- **Navigation System**: Implemented comprehensive sidebar with 16 pages across 4 sections
- **Pattern Integration**: Connected all 12 backend patterns to UI pages
- **Professional Design**: Bloomberg Terminal-style dark theme with glass morphism
- **Features Added**:
  - Dashboard with portfolio overview
  - Macro Cycles with Ray Dalio's 3-cycle framework
  - Scenarios for stress testing
  - Risk Analytics with VaR and concentration
  - Optimizer for trade proposals
  - Ratings with Buffett checklist
  - AI Insights with Claude chat
  - Market Data with real-time quotes
  - Alerts, Reports, Corporate Actions, Settings
- **Technical Improvements**:
  - JWT authentication with protected routes
  - API integration for all endpoints
  - Loading states and error handling
  - Responsive design with mobile support
- **Status**: All features fully exposed and accessible through navigation

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

### Single-File HTML UI Architecture
- **Architecture**: Single HTML file (`full_ui.html`) containing entire frontend application
- **No Build Step**: Direct browser execution without compilation or bundling
- **React Without JSX**: Uses React.createElement for component creation
- **Client-Side Routing**: Custom router implementation for SPA navigation
- **Enhanced API Client**: Enterprise-grade features integrated directly
  - Token refresh with singleton pattern to prevent race conditions
  - Exponential backoff retry logic (1s, 2s, 4s, max 30s)
  - Request queue management for failed requests
  - Structured error categorization (server/network/unknown)
- **Caching Layer**: React Query-inspired caching implementation
  - Pattern result caching to minimize API calls
  - Cache invalidation strategies
  - Background refetch capabilities
- **Business Logic Functions**: 40+ reusable calculation functions organized by domain
  - Portfolio metrics and performance calculations
  - Risk analysis and scenario modeling
  - Attribution and optimization algorithms
  - Formatting utilities for financial data
- **Error Handling Architecture**: Comprehensive error management
  - Error boundaries for component isolation
  - Graceful degradation strategies
  - User-friendly error messages with recovery options

### Backend Architecture (FastAPI)
- **Framework**: FastAPI with async/await.
- **API Layer**: RESTful endpoints, OpenAPI/Swagger, JWT-based authentication with RBAC, CORS middleware, health checks.
- **Service Layer**: Dedicated services for authentication, alerts, macro analysis, optimization, and notifications.
- **Data Access Layer**: Async PostgreSQL queries using `asyncpg`, connection pooling, parameterized queries, and pricing pack queries.
- **Background Jobs**: Scheduled tasks for pricing data collection, macro regime detection, alert evaluation, and notification retries using APScheduler.
- **Compliance System**: Manages data usage rights, export restrictions (`ExportBlocker`), attribution (`AttributionManager`), and watermarking.

### Frontend Architecture (Single-File HTML)
- **Framework**: Pure HTML/CSS/JavaScript with React 18 (UMD builds, no build step required)
- **Architecture Benefits**:
  - Zero build time - instant development feedback
  - Single file deployment - copy and serve
  - No dependency management complexity
  - Reduced bundle size from ~5MB to ~1MB
  - Faster initial page load
- **UI Components**: 
  - React components using createElement (no JSX compilation)
  - Custom component library with 16 page components
  - Chart.js for data visualizations
  - Glass morphism effects with backdrop filters
- **State Management**: 
  - Local component state for UI interactions
  - Pattern result caching inspired by React Query
  - Background data refresh capabilities
  - Optimistic UI updates
- **API Integration**: 
  - Enhanced Axios client with enterprise features
  - JWT token management with automatic refresh
  - Exponential backoff retry logic
  - Request queue for failed requests
  - Comprehensive error handling
- **Design System**: 
  - Bloomberg Terminal-inspired dark theme (#0f172a background)
  - IBM Plex Sans/Mono professional fonts
  - Consistent color semantics (green for profits, red for losses)
  - Glass morphism sidebar navigation
  - Responsive grid layouts with mobile support

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
- **Request Flow**: User action in UI → API call (Enhanced Axios + JWT) → FastAPI (middleware, service layer) → PostgreSQL → JSON response → UI update (cached if applicable).
- **Background Job Flow**: APScheduler triggers jobs → Data fetching (external APIs) → Metrics computation → PostgreSQL storage → Alert triggering → Notifications.
- **Alert Flow**: User creates alert → Nightly job evaluates conditions → Cooldown checks → Notifications (configured channels) → Failed deliveries to DLQ for retry.

## Migration Summary

### NextJS to Single-File HTML Migration
The platform successfully migrated from a complex NextJS architecture to a streamlined single-file HTML implementation, achieving significant improvements in performance, maintainability, and deployment simplicity.

#### What Was Migrated
- **All UI Components**: 16 pages with complete functionality
- **API Client Logic**: Token refresh, retry mechanisms, error handling
- **Caching Layer**: React Query-inspired caching implementation
- **Business Logic**: 40+ calculation functions extracted and organized
- **Authentication Flow**: JWT management with automatic refresh
- **Routing System**: Client-side navigation without page reloads
- **Design System**: Bloomberg Terminal theme preserved

#### Key Improvements Made
- **Eliminated Build Process**: No webpack, no transpilation, instant development
- **Simplified Deployment**: Single file to serve, no node_modules
- **Enhanced Error Handling**: Comprehensive error boundaries and recovery
- **Better API Resilience**: Exponential backoff and automatic retries
- **Race Condition Prevention**: Singleton pattern for token refresh
- **Organized Business Logic**: Reusable functions for all calculations

#### Performance Enhancements
- **Bundle Size**: Reduced from ~5MB to ~1MB (80% reduction)
- **Load Time**: Faster initial page load with no JavaScript bundling
- **Development Speed**: Zero build time, instant refresh
- **Memory Usage**: Lower footprint without NextJS runtime
- **Network Efficiency**: Caching layer reduces API calls

#### Architectural Simplification
- **Dependencies**: From 100+ npm packages to zero
- **Configuration**: No webpack, babel, or TypeScript configs
- **Maintenance**: Single file to update vs. complex directory structure
- **Testing**: Direct browser testing without build artifacts
- **Version Control**: Cleaner diffs, easier code reviews

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
-   **Core Framework**: React 18 (UMD builds via CDN).
-   **HTTP Client**: Axios (via CDN).
-   **Visualization**: Chart.js (via CDN).
-   **Fonts**: IBM Plex Sans/Mono (Google Fonts).
-   **No NPM Dependencies**: Zero package.json, pure CDN-based approach.