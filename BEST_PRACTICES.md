# DawsOS Development Best Practices

**Last Updated:** January 14, 2025  
**Purpose:** Comprehensive guide to best practices for stable development

---

## 🎯 Core Principles

### 1. Fail Fast, Fail Explicitly

**Principle:** Programming errors should surface immediately, not be masked.

**✅ GOOD:**
```python
try:
    result = await service.method()
except PricingPackNotFoundError as e:
    logger.error(f"Pricing pack not found: {e}")
    raise  # Re-raise to surface error
except (ValueError, TypeError, KeyError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except asyncpg.PostgresError as e:
    # Database errors - handle gracefully
    logger.warning(f"Database error: {e}")
    return {"error": "Database error", "provenance": "error"}
```

**❌ BAD:**
```python
try:
    result = await service.method()
except Exception as e:
    logger.warning(f"Error: {e}")
    return {"error": "Unknown error"}  # Masks bugs!
```

---

### 2. Use Specific Exceptions

**Principle:** Use domain-specific exceptions, not generic ones.

**✅ GOOD:**
```python
from app.services.pricing import PricingPackNotFoundError

if not pricing_pack:
    raise PricingPackNotFoundError(pack_id)
```

**❌ BAD:**
```python
if not pricing_pack:
    raise ValueError("No pricing pack")  # Too generic
```

**Available Custom Exceptions:**
- `PricingPackNotFoundError` - Pricing pack not found
- `PricingPackValidationError` - Pricing pack validation failed
- `PricingPackStaleError` - Pricing pack is stale
- `PortfolioNotFoundError` - Portfolio not found
- `SecurityNotFoundError` - Security not found
- `InvalidTradeError` - Invalid trade
- `InsufficientSharesError` - Insufficient shares

---

### 3. Parameterized Database Queries

**Principle:** Always use parameterized queries to prevent SQL injection.

**✅ GOOD:**
```python
async with pool.acquire() as conn:
    rows = await conn.fetch(
        "SELECT * FROM lots WHERE portfolio_id = $1 AND qty_open > $2",
        portfolio_id,
        Decimal("0")
    )
```

**❌ BAD:**
```python
# SQL injection risk!
query = f"SELECT * FROM lots WHERE portfolio_id = '{portfolio_id}'"
rows = await conn.fetch(query)
```

---

### 4. Type Hints Everywhere

**Principle:** Use type hints for all function parameters and return values.

**✅ GOOD:**
```python
from typing import Dict, List, Optional
from app.core.types import RequestCtx

async def my_capability(
    self,
    ctx: RequestCtx,
    state: Dict,
    portfolio_id: str,
    lookback_days: int = 252,
    **kwargs
) -> Dict[str, Any]:
    """Method with complete type hints."""
    pass
```

**❌ BAD:**
```python
async def my_capability(self, ctx, state, portfolio_id, lookback_days=252):
    pass  # No type hints
```

---

### 5. Structured Logging

**Principle:** Use structured logging with context, not print statements.

**✅ GOOD:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing portfolio {portfolio_id}", extra={
    "portfolio_id": portfolio_id,
    "trace_id": ctx.trace_id,
    "pricing_pack_id": ctx.pricing_pack_id
})
```

**❌ BAD:**
```python
print(f"Processing portfolio {portfolio_id}")  # Don't use print()!
```

---

## 🏗️ Architecture Patterns

### 1. Agent Capability Pattern

**Standard Pattern:**
```python
from app.agents.base_agent import BaseAgent
from app.core.capability_contract import capability
from app.core.types import RequestCtx

class MyAgent(BaseAgent):
    def get_capabilities(self) -> List[str]:
        return ["my.capability"]
    
    @capability(
        inputs={"portfolio_id": "uuid"},
        outputs={"result": "dict"},
        status="production"
    )
    async def my_capability(
        self,
        ctx: RequestCtx,
        state: Dict,
        portfolio_id: str,
        **kwargs
    ) -> Dict:
        """Capability implementation."""
        # 1. Validate inputs
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        
        # 2. Get services
        pool = self.services.get("db")
        if not pool:
            raise RuntimeError("Database pool not available")
        
        # 3. Execute business logic
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM portfolios WHERE id = $1",
                portfolio_id
            )
        
        # 4. Return structured result
        return {
            "portfolio_id": portfolio_id,
            "data": [dict(row) for row in rows]
        }
```

**Key Points:**
- ✅ Use `@capability` decorator for contract definition
- ✅ Follow naming: `category.operation` → `category_operation` method
- ✅ Always validate inputs
- ✅ Use database pool from `self.services["db"]`
- ✅ Return structured data (dict)

---

### 2. Pattern Development Pattern

**Standard Pattern Structure:**
```json
{
  "id": "my_pattern",
  "name": "My Pattern",
  "description": "What this pattern does",
  "version": "1.0.0",
  "category": "analysis",
  "inputs": {
    "portfolio_id": {
      "type": "uuid",
      "required": true,
      "description": "Portfolio UUID"
    }
  },
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "positions",
      "description": "Get portfolio positions"
    },
    {
      "capability": "my.analysis",
      "args": {
        "positions": "{{positions.positions}}"
      },
      "as": "analysis",
      "description": "Analyze positions"
    }
  ],
  "outputs": ["positions", "analysis"]
}
```

**Key Points:**
- ✅ Use template substitution: `{{inputs.field}}`, `{{step_name.field}}`
- ✅ Use `"as"` key to name step results
- ✅ Reference previous steps by their `"as"` name
- ✅ Validate JSON before committing

---

### 3. Error Handling Pattern

**Standard Pattern:**
```python
async def my_capability(self, ctx: RequestCtx, state: Dict, **kwargs) -> Dict:
    try:
        # Business logic
        result = await service.method()
        return {"status": "success", "data": result}
    
    except PricingPackNotFoundError as e:
        # Domain-specific error - re-raise
        logger.error(f"Pricing pack not found: {e}")
        raise
    
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - re-raise immediately
        logger.error(f"Programming error: {e}", exc_info=True)
        raise
    
    except asyncpg.PostgresError as e:
        # Database errors - handle gracefully
        logger.warning(f"Database error: {e}")
        return {
            "status": "error",
            "error": "Database error",
            "provenance": "error"
        }
    
    except Exception as e:
        # Unexpected errors - log and return error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "Unexpected error",
            "provenance": "error"
        }
```

**Key Points:**
- ✅ Catch specific exceptions first
- ✅ Re-raise programming errors (ValueError, TypeError, etc.)
- ✅ Handle domain errors appropriately
- ✅ Log all errors with context

---

## 🔒 Security Best Practices

### 1. Authentication

**✅ ALWAYS use centralized auth:**
```python
from backend.app.auth.dependencies import require_auth

@app.get("/api/protected")
async def protected_route(user: dict = Depends(require_auth)):
    # user = {"email": "...", "role": "...", "portfolio_id": "..."}
    return SuccessResponse(data={})
```

**❌ NEVER use legacy auth:**
```python
# ❌ OLD PATTERN (removed)
user = await get_current_user(request)
if not user:
    raise HTTPException(401)
```

---

### 2. Input Validation

**✅ ALWAYS validate inputs:**
```python
async def my_capability(self, ctx: RequestCtx, state: Dict, portfolio_id: str, **kwargs):
    # Validate at method entry
    if not portfolio_id:
        raise ValueError("portfolio_id is required")
    
    # Validate UUID format
    try:
        UUID(portfolio_id)
    except ValueError:
        raise ValueError(f"Invalid UUID format: {portfolio_id}")
```

---

### 3. Secrets Management

**✅ ALWAYS use environment variables:**
```python
import os

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    logger.warning("ANTHROPIC_API_KEY not set - AI features disabled")
```

**❌ NEVER hardcode secrets:**
```python
# ❌ BAD: Hardcoded secret
api_key = "sk-ant-api03-abc123"  # Never do this!
```

---

## 🧪 Testing Best Practices

### 1. Unit Testing

**Test Agent Capabilities:**
```python
# tests/test_agents.py
import pytest
from app.agents.financial_analyst import FinancialAnalyst
from app.core.types import RequestCtx

@pytest.mark.asyncio
async def test_ledger_positions():
    # Setup
    services = {"db": mock_pool}
    agent = FinancialAnalyst("financial_analyst", services)
    ctx = RequestCtx(
        pricing_pack_id="PP_2025-01-14",
        ledger_commit_hash="abc123",
        trace_id="trace-123",
        user_id=UUID("...")
    )
    
    # Execute
    result = await agent.ledger_positions(ctx, {}, portfolio_id="...")
    
    # Assert
    assert result["status"] == "success"
    assert "positions" in result
```

---

### 2. Integration Testing

**Test Pattern Execution:**
```python
# tests/test_patterns.py
@pytest.mark.asyncio
async def test_portfolio_overview_pattern():
    # Setup
    pattern_name = "portfolio_overview"
    inputs = {"portfolio_id": "..."}
    
    # Execute
    result = await orchestrator.run_pattern(pattern_name, inputs, ctx)
    
    # Assert
    assert result["status"] == "success"
    assert "valued_positions" in result["data"]
    assert "perf_metrics" in result["data"]
```

---

### 3. Manual Testing

**Test API Endpoints:**
```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"michael@dawsos.com","password":"mozzuq-byfqyQ-5tefvu"}' \
  | jq -r .access_token)

# Test pattern
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern_name":"portfolio_overview","inputs":{"portfolio_id":"..."}}'
```

---

## 📊 Performance Best Practices

### 1. Database Query Optimization

**✅ Use indexes:**
```sql
-- Create index for frequently queried columns
CREATE INDEX idx_lots_portfolio_open ON lots(portfolio_id) WHERE qty_open > 0;
```

**✅ Limit result sets:**
```python
# Limit large queries
rows = await conn.fetch(
    "SELECT * FROM transactions WHERE portfolio_id = $1 ORDER BY transaction_date DESC LIMIT 100",
    portfolio_id
)
```

**✅ Use batch operations:**
```python
# Batch inserts
async with conn.transaction():
    await conn.executemany(
        "INSERT INTO portfolio_metrics (portfolio_id, date, metric_type, value) VALUES ($1, $2, $3, $4)",
        batch_data
    )
```

---

### 2. Caching

**Use capability caching:**
```python
from app.agents.base_agent import cache_capability

@cache_capability(ttl=300)  # Cache for 5 minutes
async def expensive_computation(self, ctx, state, **kwargs):
    # Expensive computation
    return result
```

---

### 3. Async Operations

**✅ Use async/await:**
```python
async def my_capability(self, ctx: RequestCtx, state: Dict, **kwargs):
    # Async database query
    rows = await conn.fetch("SELECT * FROM ...")
    
    # Async service call
    result = await service.method()
    
    return result
```

**❌ Don't block:**
```python
# ❌ BAD: Blocking operation
import time
time.sleep(5)  # Blocks event loop!
```

---

## 🐛 Debugging Best Practices

### 1. Enable Debug Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

### 2. Use Execution Traces

**Pattern responses include trace:**
```json
{
  "data": {...},
  "trace": {
    "pattern_id": "portfolio_overview",
    "steps": [...],
    "agents_used": ["financial_analyst"],
    "capabilities_used": ["ledger.positions", "pricing.apply_pack"]
  }
}
```

---

### 3. Log Analysis

```bash
# Find errors
grep -i "error\|exception" logs/app.log | tail -20

# Find pattern executions
grep "pattern.*execute" logs/app.log

# Find slow operations
grep "duration\|latency" logs/app.log
```

---

## 📝 Code Style

### 1. Naming Conventions

- **Agents:** `FinancialAnalyst`, `MacroHound` (PascalCase)
- **Capabilities:** `ledger.positions`, `pricing.apply_pack` (lowercase.dot)
- **Methods:** `ledger_positions`, `pricing_apply_pack` (snake_case)
- **Variables:** `portfolio_id`, `lookback_days` (snake_case)
- **Constants:** `CACHE_TTL_DAY`, `MAX_RETRIES` (UPPER_SNAKE_CASE)

---

### 2. Documentation

**✅ GOOD: Comprehensive docstrings:**
```python
async def my_capability(
    self,
    ctx: RequestCtx,
    state: Dict,
    portfolio_id: str,
    lookback_days: int = 252,
    **kwargs
) -> Dict:
    """
    Compute portfolio metrics.
    
    Args:
        ctx: Request context (pricing_pack_id, ledger_commit_hash, trace_id)
        state: Execution state from previous steps
        portfolio_id: Portfolio UUID
        lookback_days: Historical period in days (default: 252)
    
    Returns:
        Dict with metrics data:
        - portfolio_id: Portfolio UUID
        - metrics: List of metric values
        - lookback_days: Period used
    
    Raises:
        ValueError: If portfolio_id is invalid
        PricingPackNotFoundError: If pricing pack not found
    
    Example:
        >>> result = await agent.my_capability(ctx, {}, portfolio_id="...", lookback_days=365)
        >>> print(result["metrics"])
    """
    pass
```

---

## 🚫 Anti-Patterns to Avoid

### 1. Broad Exception Catches

**❌ BAD:**
```python
try:
    result = await service.method()
except Exception as e:
    logger.warning(f"Error: {e}")
    return {"error": "Unknown error"}
```

**✅ GOOD:**
```python
try:
    result = await service.method()
except (ValueError, TypeError) as e:
    raise  # Re-raise programming errors
except asyncpg.PostgresError as e:
    logger.warning(f"Database error: {e}")
    return {"error": "Database error"}
```

---

### 2. String Formatting in SQL

**❌ BAD:**
```python
query = f"SELECT * FROM lots WHERE portfolio_id = '{portfolio_id}'"
```

**✅ GOOD:**
```python
rows = await conn.fetch(
    "SELECT * FROM lots WHERE portfolio_id = $1",
    portfolio_id
)
```

---

### 3. Missing Input Validation

**❌ BAD:**
```python
async def my_capability(self, ctx, state, portfolio_id, **kwargs):
    # No validation - could fail later
    rows = await conn.fetch("SELECT * FROM ... WHERE id = $1", portfolio_id)
```

**✅ GOOD:**
```python
async def my_capability(self, ctx, state, portfolio_id: str, **kwargs):
    # Validate at entry
    if not portfolio_id:
        raise ValueError("portfolio_id is required")
    
    try:
        UUID(portfolio_id)
    except ValueError:
        raise ValueError(f"Invalid UUID: {portfolio_id}")
    
    rows = await conn.fetch("SELECT * FROM ... WHERE id = $1", portfolio_id)
```

---

## 📚 Additional Resources

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Troubleshooting guide
- **[DATABASE.md](DATABASE.md)** - Database operations

---

**Last Updated:** January 14, 2025

