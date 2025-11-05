# Backend Implementation Plan for DawsOS Refactoring
*Created: November 4, 2025*

## Executive Summary

The backend is **already using snake_case consistently** throughout the database and Python code. The primary work is to:
1. Add a compatibility layer for frontend camelCase requests
2. Implement data integrity improvements
3. Optimize performance
4. Ensure clean API contracts

## Current State Analysis

### ✅ Already Correct (No Changes Needed)
- **Database**: All tables use snake_case (portfolio_id, user_id, created_at, etc.)
- **Backend Python**: All services use snake_case
- **Pattern JSON**: All patterns use snake_case (portfolio_id, lookback_days, twr_1y)
- **Combined Server**: Uses snake_case internally

### 🔧 Backend Work Required

## Week 1: Compatibility Layer & API Standardization

### Day 1-2: Create Field Translation Layer

**Location**: `combined_server.py`

```python
# Add at line ~50 after imports
from typing import Any, Dict
import re

def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase"""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def convert_keys_to_snake(data: Any) -> Any:
    """Recursively convert all dict keys from camelCase to snake_case"""
    if isinstance(data, dict):
        return {camel_to_snake(k): convert_keys_to_snake(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_snake(item) for item in data]
    return data

def convert_keys_to_camel(data: Any) -> Any:
    """Recursively convert all dict keys from snake_case to camelCase"""
    if isinstance(data, dict):
        return {snake_to_camel(k): convert_keys_to_camel(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_camel(item) for item in data]
    return data

# Feature flag for gradual migration
USE_FIELD_COMPATIBILITY = os.getenv('USE_FIELD_COMPATIBILITY', 'true').lower() == 'true'
```

### Day 3: Update All API Endpoints

**Wrap Request/Response Handling**:

```python
# Update each endpoint to handle both formats
@app.post("/api/patterns/execute")
async def execute_pattern(request: Request, user=Depends(require_auth)):
    body = await request.json()
    
    # Convert incoming camelCase to snake_case
    if USE_FIELD_COMPATIBILITY:
        body = convert_keys_to_snake(body)
    
    # ... existing logic using snake_case ...
    
    # Convert response back to camelCase for frontend
    if USE_FIELD_COMPATIBILITY:
        response_data = convert_keys_to_camel(result)
    else:
        response_data = result
    
    return JSONResponse(content=response_data)
```

**API Endpoints to Update**:
- [ ] `/api/patterns/execute` (line ~1087)
- [ ] `/api/auth/login` (line ~1327)
- [ ] `/api/auth/refresh` (line ~1373)
- [ ] `/api/metrics/{portfolio_id}` (line ~1523)
- [ ] `/api/portfolio` (line ~1557)
- [ ] `/api/holdings` (line ~1698)
- [ ] `/api/transactions` (line ~1852)
- [ ] `/api/alerts` (line ~1939)
- [ ] `/v1/portfolios/*` endpoints
- [ ] `/v1/trades` endpoint

### Day 4: Create API Contract Documentation

**File**: `API_CONTRACT.md`

```markdown
# API Contract for Frontend-Backend Communication

## Field Naming Convention
- **Backend Internal**: snake_case (portfolio_id, user_id, created_at)
- **API Response Format**: Configurable via USE_FIELD_COMPATIBILITY
  - If true: Returns camelCase for frontend compatibility
  - If false: Returns snake_case (target state)

## Standard Field Mappings
| Frontend (camelCase) | Backend (snake_case) |
|---------------------|---------------------|
| portfolioId         | portfolio_id        |
| userId              | user_id             |
| createdAt           | created_at          |
| updatedAt           | updated_at          |
| marketValue         | market_value        |
| totalValue          | total_value         |
| costBasis           | cost_basis          |
| sharpeRatio         | sharpe_ratio        |
| maxDrawdown         | max_drawdown        |
```

## Week 2: Data Integrity & Reliability

### Day 5-6: Add Database Constraints

**File**: `migrations/002_add_constraints.sql`

```sql
-- Add foreign key constraints
ALTER TABLE portfolios 
  ADD CONSTRAINT fk_portfolios_user 
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE transactions 
  ADD CONSTRAINT fk_transactions_portfolio 
  FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE;

ALTER TABLE lots 
  ADD CONSTRAINT fk_lots_portfolio 
  FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE;

-- Add check constraints
ALTER TABLE transactions 
  ADD CONSTRAINT chk_quantity_positive CHECK (quantity > 0);

ALTER TABLE lots 
  ADD CONSTRAINT chk_cost_basis_positive CHECK (cost_basis >= 0);

-- Add unique constraints
ALTER TABLE securities 
  ADD CONSTRAINT unq_securities_symbol UNIQUE (symbol);

-- Add indexes for performance
CREATE INDEX idx_transactions_portfolio_date ON transactions(portfolio_id, transaction_date);
CREATE INDEX idx_lots_portfolio_open ON lots(portfolio_id, is_open);
CREATE INDEX idx_portfolio_values_portfolio_date ON portfolio_daily_values(portfolio_id, date);
```

### Day 7: Input Validation Layer

**Location**: `combined_server.py` (add validation middleware)

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import date
from decimal import Decimal

# Add Pydantic models for validation
class TransactionInput(BaseModel):
    portfolio_id: str = Field(..., regex='^[0-9a-f-]{36}$')
    transaction_type: str = Field(..., regex='^(BUY|SELL|DIVIDEND|SPLIT)$')
    symbol: str = Field(..., max_length=10)
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    transaction_date: date
    
    @validator('portfolio_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid portfolio ID format')
        return v

# Apply to endpoints
@app.post("/v1/trades")
async def create_trade(trade: TransactionInput, user=Depends(require_auth)):
    # Input is now validated automatically
    ...
```

### Day 8: Add Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Apply to sensitive endpoints
@app.post("/api/patterns/execute")
@limiter.limit("100/minute")
async def execute_pattern(request: Request, user=Depends(require_auth)):
    ...

@app.post("/v1/trades")
@limiter.limit("50/minute")
async def create_trade(...):
    ...
```

## Week 3: Performance Optimization

### Day 9-10: Database Query Optimization

**Optimize Slow Queries**:

```python
# Before: N+1 query problem
async def get_portfolio_holdings(portfolio_id):
    lots = await db.fetch("SELECT * FROM lots WHERE portfolio_id = $1", portfolio_id)
    for lot in lots:
        security = await db.fetchrow("SELECT * FROM securities WHERE id = $1", lot['security_id'])
        lot['security'] = security

# After: Single query with JOIN
async def get_portfolio_holdings(portfolio_id):
    query = """
        SELECT l.*, s.symbol, s.name, s.security_type, s.sector
        FROM lots l
        JOIN securities s ON l.security_id = s.id
        WHERE l.portfolio_id = $1 AND l.is_open = true
    """
    return await db.fetch(query, portfolio_id)
```

### Day 11: Implement Caching

```python
from functools import lru_cache
import hashlib
import json

# In-memory cache for frequently accessed data
cache = {}
cache_ttl = {}

async def get_cached_or_compute(key: str, compute_func, ttl: int = 300):
    """Generic caching wrapper"""
    now = datetime.now()
    
    if key in cache and key in cache_ttl:
        if (now - cache_ttl[key]).seconds < ttl:
            return cache[key]
    
    result = await compute_func()
    cache[key] = result
    cache_ttl[key] = now
    return result

# Apply to expensive operations
async def get_portfolio_metrics(portfolio_id: str, pack_id: str):
    cache_key = f"metrics:{portfolio_id}:{pack_id}"
    return await get_cached_or_compute(
        cache_key,
        lambda: compute_portfolio_metrics(portfolio_id, pack_id),
        ttl=600  # 10 minutes
    )
```

### Day 12: Connection Pool Optimization

```python
# Update database pool configuration
DATABASE_POOL_CONFIG = {
    "min_size": 5,      # Minimum connections
    "max_size": 20,     # Maximum connections (was 10)
    "max_queries": 50000,
    "max_inactive_connection_lifetime": 300.0,
    "timeout": 60.0,
    "command_timeout": 60.0,
    "statement_cache_size": 0,  # Disable for better memory usage
    "max_cached_statement_lifetime": 0,
}

# Add connection health checks
async def ensure_healthy_connections():
    """Periodically check and refresh connections"""
    while True:
        await asyncio.sleep(60)  # Every minute
        try:
            async with app.state.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        except Exception as e:
            logger.error(f"Connection health check failed: {e}")
            # Pool will automatically recreate bad connections
```

## Database Schema Documentation

### Core Tables (Already Correct - No Changes)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT DEFAULT 'USER',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolios table  
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    base_currency TEXT DEFAULT 'USD',
    benchmark_id TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Securities table
CREATE TABLE securities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    security_type TEXT,
    exchange TEXT,
    trading_currency TEXT,
    sector VARCHAR(100),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    transaction_type TEXT NOT NULL,
    security_id UUID REFERENCES securities(id),
    symbol TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    settlement_date DATE,
    quantity NUMERIC NOT NULL,
    price NUMERIC,
    amount NUMERIC,
    currency TEXT,
    fee NUMERIC DEFAULT 0,
    commission NUMERIC DEFAULT 0,
    lot_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lots table (tax lot accounting)
CREATE TABLE lots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id),
    security_id UUID REFERENCES securities(id),
    symbol TEXT NOT NULL,
    acquisition_date DATE NOT NULL,
    quantity NUMERIC NOT NULL,
    cost_basis NUMERIC NOT NULL,
    cost_basis_per_share NUMERIC,
    currency TEXT,
    is_open BOOLEAN DEFAULT true,
    qty_original NUMERIC,
    qty_open NUMERIC,
    closed_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Testing & Validation

### Unit Tests to Add

```python
# test_field_conversion.py
def test_camel_to_snake():
    assert camel_to_snake("portfolioId") == "portfolio_id"
    assert camel_to_snake("userId") == "user_id"
    assert camel_to_snake("createdAt") == "created_at"
    assert camel_to_snake("sharpeRatio") == "sharpe_ratio"

def test_snake_to_camel():
    assert snake_to_camel("portfolio_id") == "portfolioId"
    assert snake_to_camel("user_id") == "userId"
    assert snake_to_camel("created_at") == "createdAt"

def test_deep_conversion():
    input_data = {
        "portfolioId": "123",
        "userData": {
            "userId": "456",
            "createdAt": "2025-01-01"
        }
    }
    expected = {
        "portfolio_id": "123",
        "user_data": {
            "user_id": "456",
            "created_at": "2025-01-01"
        }
    }
    assert convert_keys_to_snake(input_data) == expected
```

### Integration Tests

```python
# test_api_compatibility.py
async def test_pattern_execution_compatibility():
    """Test that patterns work with both field naming conventions"""
    
    # Test with camelCase input
    camel_request = {
        "patternId": "portfolio_overview",
        "inputs": {
            "portfolioId": "test-portfolio-id",
            "lookbackDays": 30
        }
    }
    
    response = await client.post("/api/patterns/execute", json=camel_request)
    assert response.status_code == 200
    
    # Should return camelCase when compatibility is on
    data = response.json()
    assert "portfolioId" in data["data"]
```

## Deployment Strategy

### Phase 1: Deploy with Compatibility (Day 13)
```bash
# Deploy with compatibility layer enabled
USE_FIELD_COMPATIBILITY=true
```

### Phase 2: Frontend Migration (Claude's work)
- Frontend updates all components to use snake_case
- Tests with compatibility layer still on

### Phase 3: Remove Compatibility (Day 20)
```bash
# After frontend is fully migrated
USE_FIELD_COMPATIBILITY=false
```

## Success Metrics

- [ ] All API endpoints handle both camelCase and snake_case inputs
- [ ] Database constraints prevent invalid data
- [ ] Rate limiting prevents API abuse
- [ ] Query performance improved by 30%
- [ ] Cache hit rate > 80% for read operations
- [ ] Zero field naming errors in production
- [ ] All tests passing (unit + integration)

## Coordination Points with Frontend (Claude)

1. **Day 1**: Share field mapping documentation
2. **Day 3**: Confirm API compatibility layer is working
3. **Day 5**: Frontend can start testing with new endpoints
4. **Day 10**: Coordinate on removing compatibility layer timeline
5. **Day 13**: Joint testing before production deployment

## Rollback Plan

If issues arise:
1. Set `USE_FIELD_COMPATIBILITY=true` immediately
2. Revert any database migrations if needed
3. Roll back code to previous version
4. Investigate issues in staging environment

## Files to Modify

1. `combined_server.py` - Add compatibility layer and validation
2. `migrations/002_add_constraints.sql` - New constraints
3. `requirements.txt` - Add slowapi for rate limiting
4. `API_CONTRACT.md` - New documentation
5. `tests/test_field_conversion.py` - New tests
6. `tests/test_api_compatibility.py` - Integration tests