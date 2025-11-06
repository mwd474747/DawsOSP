# Comprehensive Architecture Refactoring Plan

**Date:** November 6, 2025
**Purpose:** Complete data architecture redesign based on specialist agent analysis
**Status:** 📋 **PLANNING COMPLETE - READY FOR EXECUTION**

---

## Executive Summary

Based on comprehensive analysis by three specialized agents (Database Schema Analysis, Architecture Pattern Analysis, and Financial Domain Validation), this plan addresses critical architectural issues, field name inconsistencies, regulatory compliance gaps, and technical debt.

### Critical Findings

**🔴 P0 - Critical (Blocking Production):**
1. Database field name mismatch: `qty_open` vs `quantity_open` (SQL errors imminent)
2. Realized vs unrealized P&L not separated (tax reporting violation)
3. Cost basis method not tracked (IRS compliance gap)
4. LIFO allowed for stocks (regulatory violation)
5. Import errors: `FactorAnalysisService` doesn't exist (56 LSP errors)

**🟡 P1 - High (Architecture Violations):**
1. Monolithic combined_server.py (6,196 lines, 58 routes)
2. Business logic in API routes (violates separation of concerns)
3. Direct SQL in services (no repository layer)
4. Global singletons overused (19 services)
5. Connection pool via sys.modules (non-standard pattern)

**⚠️ P2 - Medium (Feature Gaps):**
1. Wash sale rules not implemented
2. Brinson-Fachler attribution missing
3. Factor attribution not displayed in UI
4. Average cost basis method not implemented
5. Hedge recommendations not displayed

### Estimated Effort

- **P0 Critical Fixes:** 20-25 hours (Week 1)
- **P1 Architecture Refactoring:** 40-50 hours (Weeks 2-3)
- **P2 Feature Implementation:** 60-80 hours (Weeks 4-6)
- **Total:** 120-155 hours (4-6 weeks)

---

## Part 1: Database Schema Truth & Standardization

### 1.1 Current State Analysis

**Agent Finding:** Database schema has critical inconsistency between Migration 001 claims and actual database state.

**The Confusion:**
```markdown
DATABASE.md claims:
- Migration 001 renamed qty_open → quantity_open ✅ (completed)
- Database uses quantity_open, quantity_original

Field Standardization Plan says:
- Database uses qty_open, qty_original (abbreviated form)
- This is the "source of truth" from Migration 007

Actual Code Usage:
- 5 files use quantity_open (expecting Migration 001 was run)
- 0 files use qty_open with proper aliases
- Result: SQL errors "column does not exist"
```

**Root Cause:** Migration 001 exists but was NEVER EXECUTED. Code was written assuming it ran.

### 1.2 Schema Truth Determination

**Definitive Answer (from Agent Analysis):**

Based on Migration 007 (which WAS executed):
```sql
-- Migration 007 added these columns:
ALTER TABLE lots ADD COLUMN qty_original NUMERIC(20,8);
ALTER TABLE lots ADD COLUMN qty_open NUMERIC(20,8);
ALTER TABLE lots ADD COLUMN closed_date DATE;
```

**Database Reality:**
- ✅ `lots.qty_open` (exists, from Migration 007)
- ✅ `lots.qty_original` (exists, from Migration 007)
- ✅ `lots.quantity` (exists, deprecated)
- ❌ `lots.quantity_open` (does NOT exist - Migration 001 never ran)
- ❌ `lots.quantity_original` (does NOT exist - Migration 001 never ran)

**Code Expectation:**
- 5 files query `quantity_open` → **WILL FAIL**
- 5 files query `quantity_original` → **WILL FAIL**

### 1.3 Resolution Strategy

**Decision:** Use abbreviated names (`qty_open`, `qty_original`) as source of truth.

**Rationale:**
1. Migration 007 was executed (columns exist)
2. Migration 001 was never executed (columns don't exist)
3. Changing code is lower risk than database migration
4. No production users to impact
5. Abbreviated names are PostgreSQL convention

**Action Items:**

**Task 1.1: Update All SQL Queries** (4 hours)

Files to fix:
1. `backend/app/services/trade_execution.py` (8 locations)
2. `backend/app/services/corporate_actions.py` (10 locations)
3. `backend/app/services/corporate_actions_sync.py` (2 locations)
4. `backend/app/api/routes/trades.py` (3 locations)
5. `backend/tests/integration/conftest.py` (4 locations)

Change pattern:
```sql
-- BEFORE (broken):
SELECT quantity_open, quantity_original
FROM lots
WHERE quantity_open > 0

-- AFTER (correct):
SELECT qty_open AS quantity_open, qty_original AS quantity_original
FROM lots
WHERE qty_open > 0
```

**Task 1.2: Update DATABASE.md** (1 hour)

Correct the documentation:
```markdown
## lots Table (CORRECTED)

**Actual Field Names (from Migration 007):**
- qty_open: NUMERIC(20,8) -- Open quantity
- qty_original: NUMERIC(20,8) -- Original purchase quantity
- quantity: NUMERIC(20,8) -- DEPRECATED (do not use)

**Application Layer:**
- SQL queries use aliases: qty_open AS quantity_open
- Python code uses: row["quantity_open"] (from alias)
- API responses use: "quantity" (transformed from quantity_open)
```

**Task 1.3: Delete Migration 001** (30 minutes)

Remove the confusing, never-executed migration:
```bash
# If it exists, delete it to prevent future confusion
rm backend/db/migrations/001_field_standardization.sql

# Update migration documentation
```

### 1.4 Date Field Standardization

**Issue:** Inconsistent date field naming across time-series tables.

**Current State:**
| Table | Date Field | Status |
|-------|-----------|--------|
| `portfolio_daily_values` | `valuation_date` | ⚠️ Inconsistent |
| `portfolio_metrics` | `asof_date` | ✅ Standard |
| `currency_attribution` | `asof_date` | ✅ Standard |
| `factor_exposures` | `asof_date` | ✅ Standard |
| `pricing_packs` | `asof_date` | ✅ Standard |

**Decision:** Standardize ALL time-series tables to use `asof_date`.

**Task 1.4: Rename valuation_date to asof_date** (2 hours)

```sql
-- Migration 016_standardize_date_fields.sql
BEGIN;

-- Rename column
ALTER TABLE portfolio_daily_values
    RENAME COLUMN valuation_date TO asof_date;

-- Update indexes
DROP INDEX IF EXISTS idx_portfolio_daily_values_date;
CREATE INDEX idx_portfolio_daily_values_date
    ON portfolio_daily_values(asof_date DESC);

DROP INDEX IF EXISTS idx_portfolio_daily_values_portfolio;
CREATE INDEX idx_portfolio_daily_values_portfolio
    ON portfolio_daily_values(portfolio_id, asof_date DESC);

COMMENT ON COLUMN portfolio_daily_values.asof_date IS
    'As-of date for portfolio valuation (standardized with other time-series tables)';

COMMIT;
```

**Affected Files:**
- `backend/app/services/factor_analysis.py` (remove aliases, use asof_date directly)
- `backend/app/services/metrics.py` (remove aliases, use asof_date directly)
- `backend/db/schema/portfolio_daily_values.sql` (update schema definition)

---

## Part 2: Critical Financial Compliance Gaps

### 2.1 Realized vs Unrealized P&L Separation

**Agent Finding:** 🔴 CRITICAL - No separation of realized vs unrealized gains (tax reporting violation)

**Current State:**
- Realized P&L calculated in code but not persisted
- UI shows `totalPnL = currentValue - costBasis` (treats all as unrealized)
- Cannot generate Form 1099-B or tax reports

**Impact:**
- Tax reporting errors
- GAAP violation (ASC 320 requires separation)
- Investor misrepresentation of taxable income

**Task 2.1: Add realized_pl Field** (4 hours)

```sql
-- Migration 017_add_realized_pl.sql
BEGIN;

-- Add realized P&L to transactions table
ALTER TABLE transactions
    ADD COLUMN realized_pl NUMERIC(20,2) DEFAULT NULL;

COMMENT ON COLUMN transactions.realized_pl IS
    'Realized profit/loss for SELL transactions (proceeds - cost basis)';

-- Add index for tax reporting queries
CREATE INDEX idx_transactions_realized_pl
    ON transactions(portfolio_id, transaction_date)
    WHERE realized_pl IS NOT NULL;

COMMIT;
```

**Update Service:**
```python
# backend/app/services/trade_execution.py (Line 507)

# Current (realized P&L not stored):
realized_pnl = proceeds_closed - cost_basis_closed

# New (persist to database):
await self.conn.execute(
    """
    UPDATE transactions
    SET realized_pl = $1
    WHERE id = $2
    """,
    realized_pnl,
    transaction_id
)
```

**Add API Endpoint:**
```python
# backend/app/api/routes/portfolios.py

@router.get("/{portfolio_id}/realized-pl")
async def get_realized_pl(
    portfolio_id: UUID,
    start_date: date,
    end_date: date,
    user: dict = Depends(verify_token)
):
    """Get realized P&L for tax reporting."""
    # Query transactions WHERE realized_pl IS NOT NULL
    # Group by short-term vs long-term (acquisition_date)
    # Return tax lot detail
```

### 2.2 Cost Basis Method Tracking

**Agent Finding:** 🔴 CRITICAL - No cost_basis_method field (IRS compliance gap)

**Current State:**
- Code supports FIFO/LIFO/HIFO/Specific Lot
- No enforcement of user's selected method
- Method can change between trades (IRS violation)

**Impact:**
- Regulatory compliance risk
- Tax calculation errors
- IRS requires consistent application

**Task 2.2: Add cost_basis_method Field** (2 hours)

```sql
-- Migration 018_add_cost_basis_method.sql
BEGIN;

-- Add cost basis method to portfolios
ALTER TABLE portfolios
    ADD COLUMN cost_basis_method VARCHAR(20) NOT NULL DEFAULT 'FIFO';

ALTER TABLE portfolios
    ADD CONSTRAINT check_cost_basis_method
    CHECK (cost_basis_method IN ('FIFO', 'LIFO', 'HIFO', 'AVERAGE_COST', 'SPECIFIC_LOT'));

COMMENT ON COLUMN portfolios.cost_basis_method IS
    'IRS cost basis method (must be consistently applied within tax year)';

COMMIT;
```

**Update Service:**
```python
# backend/app/services/trade_execution.py

async def execute_sell(self, ..., lot_selection_method: Optional[str] = None):
    # Get portfolio's cost basis method
    portfolio = await self.conn.fetchrow(
        "SELECT cost_basis_method FROM portfolios WHERE id = $1",
        portfolio_id
    )

    # Use specified method or fall back to portfolio default
    method = lot_selection_method or portfolio["cost_basis_method"]

    # Validate method matches portfolio setting (unless specific lot)
    if method != "SPECIFIC_LOT" and method != portfolio["cost_basis_method"]:
        raise ValueError(
            f"Cost basis method {method} doesn't match portfolio setting "
            f"{portfolio['cost_basis_method']}. Cannot change method mid-year."
        )
```

### 2.3 LIFO Restriction for Stocks

**Agent Finding:** ⚠️ HIGH - LIFO allowed for stocks (regulatory violation since 2011)

**Current State:**
- Code allows LIFO for all securities
- IRS prohibits LIFO for stocks (only commodities/futures)

**Task 2.3: Add LIFO Validation** (1 hour)

```python
# backend/app/services/trade_execution.py

async def _get_open_lots(self, portfolio_id, symbol, method):
    # Get security type
    security = await self.conn.fetchrow(
        "SELECT security_type FROM securities WHERE symbol = $1",
        symbol
    )

    # Validate LIFO not used for stocks
    if method == "LIFO" and security["security_type"] == "EQUITY":
        raise ValueError(
            f"LIFO cost basis method not allowed for stocks (IRS Reg § 1.6045-1). "
            f"Use FIFO, HIFO, or SPECIFIC_LOT instead."
        )

    # Continue with lot selection...
```

### 2.4 Wash Sale Rule Implementation

**Agent Finding:** ❌ MEDIUM - No wash sale detection (P2 feature)

**Deferred to Phase 2** - Not blocking production but required for tax reporting.

**Placeholder Task 2.4: Implement Wash Sale Detection** (12 hours - Phase 2)

Logic:
1. On SELL transaction with loss, check for purchases of same symbol
2. Window: 30 days before OR after sale date
3. If found: Disallow loss, add to new lot's cost basis
4. Mark transaction with `wash_sale_disallowed` flag

---

## Part 3: Architecture Layer Separation

### 3.1 Current Anti-Pattern: Monolithic combined_server.py

**Agent Finding:** 6,196 lines with 58 route definitions + business logic

**Problem:**
```python
# combined_server.py (Lines 1647-1822)
@app.get("/api/metrics/{portfolio_id}")
async def get_metrics(portfolio_id: str):
    # 175 lines of business logic
    # Direct database queries
    # Complex calculations
    # Should be in MetricsService
```

**Recommendation:** Extract all routes to dedicated router modules.

### 3.2 Proper Layered Architecture

**Target Architecture:**

```
┌─────────────────────────────────────┐
│     API Layer (routes/)             │
│  - HTTP request/response            │
│  - Authentication (JWT)             │
│  - Validation (Pydantic)            │
│  - Delegates to services            │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│   Service Layer (services/)         │
│  - Business logic                   │
│  - Orchestrates repositories        │
│  - Transaction management           │
│  - NO direct SQL                    │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Repository Layer (repositories/)   │  ← NEW LAYER
│  - Database access ONLY             │
│  - CRUD operations                  │
│  - Query building                   │
│  - Returns domain models            │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│     Database (PostgreSQL)           │
└─────────────────────────────────────┘
```

### 3.3 Repository Pattern Implementation

**Task 3.1: Create Repository Base Class** (4 hours)

```python
# backend/app/repositories/base.py

from abc import ABC
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncpg

class BaseRepository(ABC):
    """Base repository with common CRUD operations."""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_by_id(self, id: UUID) -> Optional[Dict]:
        """Get single record by ID."""
        raise NotImplementedError

    async def get_all(self, filters: Dict = None) -> List[Dict]:
        """Get all records matching filters."""
        raise NotImplementedError

    async def create(self, data: Dict) -> UUID:
        """Create new record."""
        raise NotImplementedError

    async def update(self, id: UUID, data: Dict) -> bool:
        """Update existing record."""
        raise NotImplementedError

    async def delete(self, id: UUID) -> bool:
        """Delete record."""
        raise NotImplementedError
```

**Task 3.2: Create Lots Repository** (6 hours)

```python
# backend/app/repositories/lots_repository.py

from .base import BaseRepository
from typing import List, Dict
from uuid import UUID
from decimal import Decimal

class LotsRepository(BaseRepository):
    """Repository for lot operations."""

    async def get_open_lots(
        self,
        portfolio_id: UUID,
        symbol: str,
        method: str = "FIFO"
    ) -> List[Dict]:
        """
        Get open lots for a symbol using specified method.

        Returns lots with qty_open aliased as quantity_open for service layer.
        """
        order_clause = {
            "FIFO": "acquisition_date ASC, created_at ASC",
            "LIFO": "acquisition_date DESC, created_at DESC",
            "HIFO": "(cost_basis / qty_original) DESC"
        }.get(method, "acquisition_date ASC")

        query = f"""
            SELECT
                id,
                portfolio_id,
                security_id,
                symbol,
                qty_open AS quantity_open,
                qty_original AS quantity_original,
                cost_basis,
                cost_basis_per_share,
                acquisition_date,
                currency
            FROM lots
            WHERE portfolio_id = $1
              AND symbol = $2
              AND is_open = true
              AND qty_open > 0
            ORDER BY {order_clause}
        """

        return await self.conn.fetch(query, portfolio_id, symbol)

    async def reduce_lot(
        self,
        lot_id: UUID,
        qty_to_reduce: Decimal
    ) -> None:
        """
        Reduce lot quantity (thread-safe with row lock).
        """
        await self.conn.execute(
            """
            UPDATE lots
            SET
                qty_open = qty_open - $2,
                updated_at = CURRENT_TIMESTAMP,
                is_open = CASE WHEN qty_open - $2 <= 0 THEN false ELSE true END,
                closed_date = CASE WHEN qty_open - $2 <= 0 THEN CURRENT_DATE ELSE NULL END
            WHERE id = $1
              AND qty_open >= $2  -- Validation
            """,
            lot_id,
            qty_to_reduce
        )

    async def get_lots_for_symbol_at_date(
        self,
        portfolio_id: UUID,
        symbol: str,
        target_date: date
    ) -> List[Dict]:
        """Get historical lots held on a specific date."""
        return await self.conn.fetch(
            """
            SELECT
                id,
                qty_original AS quantity_original,
                acquisition_date,
                closed_date
            FROM lots
            WHERE portfolio_id = $1
              AND symbol = $2
              AND acquisition_date <= $3
              AND (closed_date IS NULL OR closed_date > $3)
            """,
            portfolio_id,
            symbol,
            target_date
        )
```

**Task 3.3: Update Services to Use Repositories** (20 hours)

```python
# backend/app/services/trade_execution.py (REFACTORED)

from app.repositories.lots_repository import LotsRepository

class TradeExecutionService:
    def __init__(self, conn):
        self.conn = conn
        self.lots_repo = LotsRepository(conn)

    async def execute_sell(self, ...):
        # Get portfolio cost basis method
        portfolio = await self._get_portfolio(portfolio_id)
        method = portfolio["cost_basis_method"]

        # Use repository instead of direct SQL
        open_lots = await self.lots_repo.get_open_lots(
            portfolio_id,
            symbol,
            method
        )

        # Business logic (unchanged)
        for lot in open_lots:
            # Use aliased field name from repository
            qty_available = lot["quantity_open"]
            # ...
```

### 3.4 Extract Routes from combined_server.py

**Task 3.4: Move Routes to Dedicated Modules** (30 hours)

**Priority Routes to Extract:**

1. **Metrics Routes** → `backend/app/api/routes/metrics.py`
   - Lines 1647-1822 (175 lines)
   - Extract business logic to MetricsService

2. **Corporate Actions Routes** → `backend/app/api/routes/corporate_actions.py`
   - Lines 4750-4889 (139 lines)
   - Already has router module, move endpoints there

3. **Portfolio Routes** → Already in `backend/app/api/routes/portfolios.py`
   - Verify no duplicates in combined_server.py

4. **Analytics Routes** → New `backend/app/api/routes/analytics.py`
   - Extract scenario, attribution, risk endpoints

**Target State:**
```python
# combined_server.py (REFACTORED - ~200 lines)

from fastapi import FastAPI
from backend.app.api.routes import (
    portfolios,
    trades,
    metrics,
    corporate_actions,
    analytics,
    macro,
    patterns,
    auth
)

app = FastAPI(title="DawsOS")

# Register routers
app.include_router(portfolios.router, prefix="/api/v1/portfolios", tags=["portfolios"])
app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(corporate_actions.router, prefix="/api/v1/corporate-actions", tags=["corporate-actions"])
# ... etc

@app.on_event("startup")
async def startup_event():
    # Database pool initialization
    # Middleware setup

@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup
```

---

## Part 4: Dependency Injection Pattern

### 4.1 Replace Global Singletons

**Agent Finding:** 19 services use global singleton pattern (testing nightmare)

**Current Anti-Pattern:**
```python
# backend/app/services/pricing.py
_pricing_service = None  # Global variable

def get_pricing_service():
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()
    return _pricing_service
```

**Problems:**
- Tight coupling
- Difficult to mock in tests
- State persists across tests
- Not thread-safe

**Task 4.1: Implement FastAPI Dependency Injection** (16 hours)

```python
# backend/app/dependencies.py (NEW)

from fastapi import Depends
from app.db.connection import get_db_connection_with_rls
from app.repositories.lots_repository import LotsRepository
from app.services.pricing import PricingService
from app.services.trade_execution import TradeExecutionService

async def get_lots_repository(
    conn = Depends(get_db_connection_with_rls)
) -> LotsRepository:
    """Dependency for LotsRepository."""
    return LotsRepository(conn)

async def get_pricing_service() -> PricingService:
    """Dependency for PricingService."""
    return PricingService()

async def get_trade_execution_service(
    conn = Depends(get_db_connection_with_rls),
    lots_repo: LotsRepository = Depends(get_lots_repository)
) -> TradeExecutionService:
    """Dependency for TradeExecutionService."""
    return TradeExecutionService(conn, lots_repo)
```

**Update Routes:**
```python
# backend/app/api/routes/trades.py

from app.dependencies import get_trade_execution_service

@router.post("/sell")
async def execute_sell(
    request: SellRequest,
    trade_service: TradeExecutionService = Depends(get_trade_execution_service),
    user: dict = Depends(verify_token)
):
    """Execute sell trade."""
    result = await trade_service.execute_sell(
        portfolio_id=request.portfolio_id,
        symbol=request.symbol,
        qty=request.quantity,
        price=request.price
    )
    return result
```

### 4.2 Replace sys.modules Connection Pool

**Agent Finding:** Non-standard `sys.modules['__dawsos_db_pool_storage__']` pattern

**Task 4.2: Implement Proper Connection Pool Manager** (4 hours)

```python
# backend/app/db/pool_manager.py (NEW)

from typing import Optional
import asyncpg

class ConnectionPoolManager:
    """Singleton connection pool manager."""

    _instance: Optional['ConnectionPoolManager'] = None
    _pool: Optional[asyncpg.Pool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, database_url: str):
        """Initialize connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20
            )

    def get_pool(self) -> asyncpg.Pool:
        """Get connection pool."""
        if self._pool is None:
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        return self._pool

    async def close(self):
        """Close connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

# Singleton instance
pool_manager = ConnectionPoolManager()
```

**Update combined_server.py:**
```python
# combined_server.py

from app.db.pool_manager import pool_manager

@app.on_event("startup")
async def startup_event():
    await pool_manager.initialize(os.getenv("DATABASE_URL"))

@app.on_event("shutdown")
async def shutdown_event():
    await pool_manager.close()
```

---

## Part 5: Implementation Roadmap

### Phase 1: Critical Fixes (Week 1 - 25 hours)

**Day 1-2: Database Schema Fixes**
- [ ] Task 1.1: Update all SQL queries (qty_open aliases) - 4h
- [ ] Task 1.2: Update DATABASE.md - 1h
- [ ] Task 1.3: Delete Migration 001 - 0.5h
- [ ] Task 1.4: Rename valuation_date to asof_date - 2h
- [ ] Run migration, test all queries

**Day 3-4: Financial Compliance**
- [ ] Task 2.1: Add realized_pl field - 4h
- [ ] Task 2.2: Add cost_basis_method field - 2h
- [ ] Task 2.3: Add LIFO validation - 1h
- [ ] Test realized P&L calculation
- [ ] Test cost basis method enforcement

**Day 5: Testing & Validation**
- [ ] Integration tests for lot operations
- [ ] Test FIFO/LIFO/HIFO methods
- [ ] Test realized P&L persistence
- [ ] Verify no SQL errors
- [ ] **Total: 14.5 hours**

### Phase 2: Architecture Refactoring (Weeks 2-3 - 50 hours)

**Week 2: Repository Layer**
- [ ] Task 3.1: Create BaseRepository - 4h
- [ ] Task 3.2: Create LotsRepository - 6h
- [ ] Create TransactionsRepository - 6h
- [ ] Create PortfoliosRepository - 6h
- [ ] Create SecuritiesRepository - 4h
- [ ] **Total: 26 hours**

**Week 3: Service Layer Refactoring**
- [ ] Task 3.3: Update TradeExecutionService - 6h
- [ ] Update CorporateActionsService - 4h
- [ ] Update PricingService - 4h
- [ ] Update MetricsService - 4h
- [ ] Task 3.4: Extract routes from combined_server.py - 30h
  - Metrics routes - 8h
  - Corporate actions routes - 6h
  - Analytics routes - 10h
  - Refactor business logic - 6h
- [ ] **Total: 48 hours**

### Phase 3: Dependency Injection (Week 4 - 20 hours)

**Week 4: DI Pattern**
- [ ] Task 4.1: Implement FastAPI dependencies - 16h
  - Create dependencies.py - 4h
  - Update all route modules - 8h
  - Remove global singletons - 4h
- [ ] Task 4.2: Replace sys.modules pool - 4h
- [ ] **Total: 20 hours**

### Phase 4: Feature Implementation (Weeks 5-6 - 60 hours)

**Week 5: Attribution & Risk**
- [ ] Implement Brinson-Fachler attribution - 20h
- [ ] Display factor attribution in UI - 8h
- [ ] Display hedge recommendations - 6h
- [ ] Add DaR trend visualization - 6h
- [ ] **Total: 40 hours**

**Week 6: Tax Compliance**
- [ ] Implement wash sale detection - 12h
- [ ] Implement average cost method - 8h
- [ ] Add holding period tracking - 6h
- [ ] Fractional share handling - 4h
- [ ] **Total: 30 hours**

---

## Part 6: Testing Strategy

### 6.1 Unit Tests

**Repository Tests:**
```python
# backend/tests/repositories/test_lots_repository.py

async def test_get_open_lots_fifo():
    """Test FIFO lot selection."""
    repo = LotsRepository(conn)
    lots = await repo.get_open_lots(portfolio_id, "AAPL", "FIFO")

    # Verify oldest lot first
    assert lots[0]["acquisition_date"] < lots[1]["acquisition_date"]

async def test_reduce_lot_thread_safety():
    """Test concurrent lot reduction."""
    # Simulate race condition
    # Verify row lock prevents overselling
```

**Service Tests:**
```python
# backend/tests/services/test_trade_execution.py

async def test_execute_sell_fifo():
    """Test sell execution with FIFO."""
    service = TradeExecutionService(conn, lots_repo)

    # Mock repository
    lots_repo.get_open_lots = AsyncMock(return_value=[...])

    result = await service.execute_sell(...)

    # Verify correct lot selected
    # Verify realized P&L calculated
    # Verify transaction recorded
```

### 6.2 Integration Tests

**Database Integration:**
```python
# backend/tests/integration/test_lot_lifecycle.py

async def test_buy_sell_lifecycle():
    """Test complete buy-sell-report lifecycle."""
    # 1. Execute buy (creates lot)
    # 2. Execute sell (reduces lot, calculates realized P&L)
    # 3. Query realized P&L for tax report
    # 4. Verify numbers match
```

### 6.3 Financial Validation Tests

**Tax Compliance:**
```python
# backend/tests/financial/test_tax_compliance.py

async def test_cost_basis_consistency():
    """Verify cost basis method enforced."""
    # Set portfolio to FIFO
    # Attempt LIFO sell
    # Verify error raised

async def test_realized_pl_accuracy():
    """Verify realized P&L calculation."""
    # Create lot: 100 shares @ $50
    # Sell 50 shares @ $60
    # Verify realized P&L = 50 * ($60 - $50) = $500

async def test_lifo_stock_restriction():
    """Verify LIFO blocked for stocks."""
    # Attempt LIFO on EQUITY security
    # Verify ValueError raised
```

---

## Part 7: Success Criteria

### 7.1 P0 Criteria (Production Blocking)

✅ **Database Schema:**
- [ ] All SQL queries use correct field names (qty_open, qty_original)
- [ ] All time-series tables use asof_date consistently
- [ ] No "column does not exist" errors

✅ **Financial Compliance:**
- [ ] Realized P&L separated from unrealized
- [ ] Cost basis method tracked and enforced
- [ ] LIFO restricted to non-equity securities
- [ ] Realized P&L API endpoint returns accurate data

✅ **Code Quality:**
- [ ] No import errors (FactorAnalysisService → FactorAnalyzer)
- [ ] All unit tests pass
- [ ] All integration tests pass

### 7.2 P1 Criteria (Architecture)

✅ **Layer Separation:**
- [ ] Repository layer created (5+ repositories)
- [ ] Services use repositories (no direct SQL)
- [ ] Routes delegate to services (no business logic)
- [ ] combined_server.py reduced to <300 lines

✅ **Dependency Injection:**
- [ ] Global singletons replaced with FastAPI Depends()
- [ ] sys.modules pool replaced with proper manager
- [ ] Services testable in isolation

### 7.3 P2 Criteria (Features)

✅ **Attribution:**
- [ ] Brinson-Fachler attribution implemented
- [ ] Factor attribution displayed in UI
- [ ] Hedge recommendations displayed

✅ **Tax Compliance:**
- [ ] Wash sale detection implemented
- [ ] Average cost method implemented
- [ ] Holding period tracking implemented

---

## Part 8: Risk Mitigation

### 8.1 Rollback Plan

**Database Changes:**
```sql
-- If Migration 016 fails, rollback:
ALTER TABLE portfolio_daily_values RENAME COLUMN asof_date TO valuation_date;

-- If Migration 017 fails, rollback:
ALTER TABLE transactions DROP COLUMN realized_pl;

-- If Migration 018 fails, rollback:
ALTER TABLE portfolios DROP COLUMN cost_basis_method;
```

**Code Changes:**
- Git branches for each phase
- Can revert individual commits
- Comprehensive testing before merge

### 8.2 Deployment Strategy

**Phase 1 (Critical Fixes):**
1. Run migrations on dev database
2. Test all queries locally
3. Run full test suite
4. Deploy to staging
5. Smoke test critical paths
6. Deploy to production (if applicable)

**Phase 2-4 (Architecture):**
1. Feature flags for new code paths
2. Gradual rollout (repository layer first)
3. Monitor error rates
4. Rollback if errors spike

---

## Part 9: Documentation Updates

### 9.1 Required Documentation

**Technical Docs:**
- [ ] Update DATABASE.md with correct schema
- [ ] Document repository pattern
- [ ] Document dependency injection usage
- [ ] Update API documentation

**Financial Docs:**
- [ ] Document cost basis methods
- [ ] Document realized vs unrealized P&L
- [ ] Document tax reporting capabilities
- [ ] Update FINANCIAL_DOMAIN_KNOWLEDGE.md

**Developer Docs:**
- [ ] Architecture decision records (ADRs)
- [ ] Migration guide (old → new patterns)
- [ ] Testing guide
- [ ] Contribution guidelines

---

## Part 10: Conclusion

This comprehensive refactoring plan addresses all critical issues identified by the specialist agents:

**Database Schema:** Field name standardization, migration correction
**Financial Compliance:** Tax reporting, IRS compliance, GAAP requirements
**Architecture:** Proper layering, repository pattern, dependency injection
**Code Quality:** Eliminate anti-patterns, improve testability

**Total Estimated Effort:** 120-155 hours (4-6 weeks)

**Priority Execution:**
1. Week 1: Critical schema and compliance fixes (production blocking)
2. Weeks 2-3: Architecture refactoring (technical debt reduction)
3. Week 4: Dependency injection (testability improvement)
4. Weeks 5-6: Feature implementation (competitive advantage)

**Next Step:** Review this plan with stakeholders and obtain approval to proceed.

---

**Status:** ✅ **PLANNING COMPLETE - READY FOR EXECUTION**
