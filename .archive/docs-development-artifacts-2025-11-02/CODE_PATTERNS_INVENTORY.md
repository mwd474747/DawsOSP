# DawsOS Code Patterns Inventory

## Executive Summary

DawsOS employs a comprehensive set of architectural patterns, design patterns, and financial domain patterns that create a robust, maintainable, and scalable portfolio management platform. The codebase demonstrates mature software engineering practices with clear separation of concerns, immutable data handling, and sophisticated financial calculations.

## 1. Architectural Patterns

### 1.1 Microservices Architecture
- **Implementation**: Service-oriented design with clear boundaries
- **Components**: 
  - Frontend (Next.js)
  - Backend (FastAPI)  
  - Database (PostgreSQL)
  - Cache (Redis)
  - Background Jobs (APScheduler)
- **Benefits**: Independent scaling, deployment flexibility, technology diversity

### 1.2 Layered Architecture (Backend)
```
API Layer (FastAPI Routes)
    ↓
Service Layer (Business Logic)
    ↓
Data Access Layer (Repository Pattern)
    ↓
Database Layer (PostgreSQL)
```

### 1.3 Event-Driven Architecture
- **Job Scheduler**: Nightly processing pipeline
- **Alert System**: Event-triggered notifications
- **Circuit Breaker**: State-based behavior changes

## 2. Design Patterns

### 2.1 Singleton Pattern
**Usage**: Ensures single instance for shared resources

**Implementations**:
- `PoolManager` (database connections)
- `AgentRuntime` (agent orchestration)
- `OptimizerService` (portfolio optimization)
- `MacroService` (economic analysis)
- `RightsRegistry` (compliance)
- Various service classes

**Example**:
```python
class PoolManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### 2.2 Factory Pattern
**Usage**: Controlled object creation

**Implementations**:
- `get_auth_service()`
- `get_optimizer_service()`
- `get_macro_service()`
- `get_db_pool()`
- `get_risk_service()`

**Purpose**: Lazy initialization, dependency injection, singleton access

### 2.3 Repository Pattern
**Usage**: Abstract data access from business logic

**Implementations**:
- `execute_query_safe()` - Safe database operations
- `PricingPackQueries` - Pricing data access
- `MetricsQueries` - Metrics data access
- Portfolio data functions

**Benefits**: SQL injection protection, connection pooling, error handling

### 2.4 Decorator Pattern
**Usage**: Add behavior without modifying structure

**Implementations**:
- `@rate_limit` - API rate limiting
- `@trace_context` - Distributed tracing
- `@field_validator` - Pydantic validation
- FastAPI route decorators (`@app.get`, `@app.post`)

### 2.5 Middleware Pattern
**Usage**: Request/response processing pipeline

**Implementations**:
- `CORSMiddleware` - Cross-origin handling
- JWT authentication middleware
- Exception handlers (HTTP, validation, general)
- Database initialization middleware

### 2.6 Strategy Pattern
**Usage**: Interchangeable algorithms

**Implementations**:
- Optimization methods (mean_variance, risk_parity, equal_weight)
- Tax lot selection (FIFO, LIFO, HIFO)
- Circuit breaker states (CLOSED, OPEN, HALF_OPEN)

### 2.7 Circuit Breaker Pattern
**Usage**: Prevent cascading failures

**States**:
- **CLOSED**: Normal operation
- **OPEN**: Reject requests after threshold failures
- **HALF_OPEN**: Test recovery with single request

**Configuration**: 3 failures → OPEN for 60 seconds

### 2.8 Context Manager Pattern
**Usage**: Resource management

**Implementations**:
- `get_db_connection()` - Database connections
- `get_db_connection_with_rls()` - Row-level security
- Transaction management

## 3. Frontend Patterns

### 3.1 Component Patterns
- **Framework**: React 18 with TypeScript
- **UI Library**: Radix UI primitives
- **Styling**: TailwindCSS with Fibonacci spacing
- **Design System**: Golden ratio colors, consistent spacing

**Component Types**:
- Presentation components (MetricCard, RegimeCard)
- Container components (with business logic)
- Chart components (Recharts integration)

### 3.2 State Management Patterns
- **Server State**: React Query (TanStack Query)
  - Automatic caching
  - Background refetching
  - Optimistic updates
  - Stale-while-revalidate
- **Local State**: React hooks (useState, useEffect)
- **Global State**: Context API (where needed)

### 3.3 Data Fetching Patterns
- **HTTP Client**: Axios with interceptors
- **Authentication**: Automatic JWT injection
- **Error Handling**: Retry logic with exponential backoff
- **Type Safety**: TypeScript interfaces

**React Query Configuration**:
```typescript
{
  staleTime: 5 * 60 * 1000,      // 5 minutes
  gcTime: 10 * 60 * 1000,         // 10 minutes cache
  retry: 3,                        // Max retries
  refetchOnWindowFocus: true,     // Auto-refresh
  refetchOnReconnect: true        // Network recovery
}
```

### 3.4 Hook Patterns
- Custom hooks for data fetching (`usePortfolioOverview`, `useMacroDashboard`)
- Query key management for cache invalidation
- Mutation hooks with optimistic updates

## 4. Security Patterns

### 4.1 Authentication Pattern
- **Method**: JWT tokens (HS256 algorithm)
- **Expiration**: 24 hours
- **Storage**: Client-side (localStorage/cookies)
- **Refresh**: Token refresh endpoint

### 4.2 Authorization Pattern
- **RBAC**: Role-Based Access Control
- **Roles Hierarchy**:
  - ADMIN: Full system access
  - MANAGER: Portfolio management
  - USER: Standard access
  - VIEWER: Read-only

### 4.3 Password Security
- **Hashing**: SHA256 with salt (Note: Should upgrade to bcrypt)
- **Validation**: Minimum 8 characters
- **Failed Attempts**: Tracking for brute-force prevention

### 4.4 API Security
- **CORS**: Configured middleware
- **Rate Limiting**: Token bucket algorithm
- **SQL Injection**: Parameterized queries
- **Input Validation**: Pydantic models

### 4.5 Secret Management
- **API Keys**: Environment variables
- **JWT Secret**: Environment variable
- **Database URL**: Environment variable
- **Third-party APIs**: Secure key storage

## 5. Data Patterns

### 5.1 Immutable Data Pattern
**Pricing Packs**: Historical data never modified
- Supersede chain for corrections
- Audit trail preservation
- Point-in-time accuracy

**Benefits**:
- Reproducibility guarantee
- Historical accuracy
- Regulatory compliance

### 5.2 Connection Pooling Pattern
- **Library**: asyncpg
- **Configuration**:
  - Min connections: 5
  - Max connections: 20
  - Command timeout: 60s
  - Idle timeout: 300s

### 5.3 Async/Await Pattern
- **Framework**: FastAPI with async routes
- **Database**: Async PostgreSQL queries
- **HTTP**: Async client requests
- **Concurrency**: asyncio for parallel operations

### 5.4 Caching Pattern
- **Redis**: API response caching
- **React Query**: Frontend cache
- **Stale-while-revalidate**: Background updates
- **Cache keys**: Structured naming convention

## 6. Financial Domain Patterns

### 6.1 Pricing Pack Architecture
```
Daily Snapshot (PP_YYYY-MM-DD)
    ├── All security prices
    ├── FX rates (4PM WM/Reuters)
    ├── Immutable once created
    └── O(1) lookup performance
```

### 6.2 Tax Lot Accounting
- **Methods**: FIFO, LIFO, HIFO
- **Tracking**: Cost basis per lot
- **P&L**: Realized on lot closure
- **Multi-currency**: FX gain/loss separation

### 6.3 Portfolio Valuation
```python
valuation_flow:
  1. Get latest pricing pack
  2. Load open lots
  3. Apply current prices
  4. Convert to base currency
  5. Sum total value
```

### 6.4 Performance Metrics
- **TWR**: Time-Weighted Returns
- **MWR**: Money-Weighted Returns (IRR)
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Peak-to-trough loss
- **Rolling Windows**: 30d, 90d, 1y

### 6.5 Currency Attribution
**Decomposition Formula**:
```
r_base = r_local + r_fx + (r_local × r_fx)

Where:
- r_local: Local currency return
- r_fx: FX return
- interaction: Cross term (typically <0.01%)
```

### 6.6 Risk Calculations
- **Portfolio Beta**: Weighted average of holdings
- **VaR (95%)**: Value at Risk calculation
- **CVaR**: Conditional VaR (tail risk)
- **DaR**: Drawdown at Risk
- **Factor Analysis**: 5-factor model (rates, inflation, credit, USD, equity)

### 6.7 Scenario Analysis
**Scenarios**:
- Market Crash (-20% equity)
- Rate Hike (+200bps rates)
- High Inflation (+5% CPI)
- Tech Crash (-30% tech)
- Recovery Rally (+15% broad)
- Credit Crunch (+300bps spreads)

**Regime Conditioning**: Adjust probabilities based on macro regime

### 6.8 Factor Model
```
r_portfolio = α + β₁·RealRate + β₂·Inflation + β₃·Credit + β₄·USD + β₅·ERP + ε
```

## 7. Integration Patterns

### 7.1 Provider Facade Pattern
- **Base Class**: `BaseProvider`
- **Features**:
  - Circuit breaker protection
  - Rate limiting
  - Dead Letter Queue (DLQ)
  - Rights management
  - Bandwidth tracking

### 7.2 API Integration Pattern
**Third-party APIs**:
- Polygon.io (market data)
- FRED (economic data)
- FMP (fundamentals)
- NewsAPI (sentiment)
- Anthropic (AI analysis)

**Common Features**:
- Exponential backoff
- Error recovery
- Quota management
- Attribution tracking

## 8. Background Processing Patterns

### 8.1 Job Scheduling Pattern
**Nightly Pipeline** (APScheduler):
1. 00:15 - Build pricing pack
2. 00:20 - Compute macro regime
3. 00:25 - Currency attribution
4. 00:30 - Calculate metrics
5. 00:35 - Evaluate alerts
6. 00:40 - Generate reports

### 8.2 Retry Pattern
- **DLQ**: Failed request queue
- **Exponential Backoff**: 2^n seconds
- **Max Retries**: 5 attempts
- **Permanent Failure**: Move to failed queue

## 9. Observability Patterns

### 9.1 Distributed Tracing
- **OpenTelemetry**: Trace context propagation
- **Trace ID**: Request correlation
- **Span Attributes**: Metadata collection

### 9.2 Metrics Collection
- **Prometheus**: Time-series metrics
- **Counters**: Request counts, errors
- **Histograms**: Latency distribution
- **Gauges**: Current values (queue size, connections)

### 9.3 Structured Logging
- **Logger**: Python logging module
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: User ID, request ID, trace ID
- **Format**: JSON for parsing

## 10. Compliance Patterns

### 10.1 Rights Management
- **Registry**: Track data source rights
- **Restrictions**: Export limitations
- **Attribution**: Required citations
- **Watermarking**: PDF exports

### 10.2 Audit Trail
- **Immutable Logs**: Transaction history
- **User Actions**: Authentication, trades
- **Data Changes**: Versioned updates
- **Compliance Reports**: Regulatory requirements

## 11. Testing Patterns

### 11.1 Stub Pattern
- **Database Stubs**: Test without DB connection
- **Mock Services**: Isolated unit tests
- **Fixture Data**: Consistent test data

### 11.2 Integration Testing
- **Test Database**: Separate instance
- **API Testing**: Full request/response cycle
- **End-to-End**: User journey validation

## 12. Performance Patterns

### 12.1 Query Optimization
- **Indexes**: On foreign keys, date columns
- **Connection Pooling**: Reuse connections
- **Batch Operations**: Bulk inserts/updates
- **Query Timeout**: Prevent long-running queries

### 12.2 Lazy Loading
- **Pagination**: Limit result sets
- **On-Demand**: Load data when needed
- **Progressive Enhancement**: Load critical first

## Key Observations

### Strengths
1. **Comprehensive Pattern Usage**: Demonstrates mature software engineering
2. **Financial Domain Expertise**: Sophisticated calculations and models
3. **Security First**: Multiple layers of protection
4. **Performance Optimized**: Caching, pooling, async operations
5. **Maintainable**: Clear separation of concerns

### Areas for Enhancement
1. **Password Hashing**: Upgrade from SHA256 to bcrypt/argon2
2. **Performance Metrics**: Replace hardcoded values with real calculations
3. **Test Coverage**: Expand unit and integration tests
4. **Documentation**: Add inline documentation for complex algorithms
5. **Error Recovery**: Enhance circuit breaker patterns

### Pattern Maturity
- **Production Ready**: Authentication, API, Database patterns
- **Well Implemented**: Financial calculations, async patterns
- **Needs Refinement**: Some mock data still present in metrics

## Conclusion

DawsOS demonstrates a sophisticated understanding of software architecture patterns, combining general software engineering best practices with domain-specific financial patterns. The codebase shows clear evolution from initial implementation to production-ready system, with most patterns properly implemented and only minor areas requiring enhancement.

The use of immutable data structures, comprehensive error handling, and sophisticated financial models positions this as an institutional-grade portfolio management platform. The pattern inventory reveals a system designed for reliability, performance, and regulatory compliance.