# DawsOS Database Documentation

**Version:** 5.0 (With Field Scaling & Format Conventions)  
**Last Updated:** January 15, 2025  
**Database:** PostgreSQL 14+ with TimescaleDB Extension (Neon-backed on Replit)  
**Status:** ✅ PRODUCTION READY (32 Active Tables, 19 Migrations Executed)

---

## 🚀 REPLIT-SPECIFIC DATABASE INFORMATION

### How PostgreSQL Works on Replit

DawsOS uses Replit's fully managed PostgreSQL database built on **Neon serverless infrastructure**:

- **Auto-scaling:** Database scales automatically based on usage
- **Cost-efficient:** Only charged when database is active (receiving requests + 5 min after)
- **Storage:** 33MB minimum, 10 GiB maximum per database
- **Connection:** Automatic credential management via environment variables
- **Rollback Support:** Database snapshots created with code checkpoints

### Environment Variables (Auto-configured by Replit)

```bash
DATABASE_URL        # Full connection string (contains all credentials)
PGHOST             # Database host
PGUSER             # Database username  
PGPASSWORD         # Database password
PGDATABASE         # Database name (usually 'neondb')
PGPORT             # Port (usually 5432)
```

**⚠️ CRITICAL:** Never expose DATABASE_URL in logs or frontend code - it contains full credentials!

### Connecting to Database in DawsOS

```python
# Pattern used throughout DawsOS backend
import os
from asyncpg import create_pool

# Replit automatically provides DATABASE_URL
DATABASE_URL = os.environ['DATABASE_URL']

# Create connection pool (done once in combined_server.py)
pool = await create_pool(
    DATABASE_URL,
    min_size=2,
    max_size=10,
    command_timeout=60
)

# Register for cross-module access
from backend.app.db.connection import register_external_pool
register_external_pool(pool)
```

---

## 📊 FIELD SCALING & FORMAT CONVENTIONS

### ⚠️ CRITICAL: All Percentages Stored as Decimals

**Universal Rule:** All percentage values in the database are stored as **decimal values** where 1.0 = 100%

| Value Type | Database Storage | Backend Returns | Frontend Expects | Display Format |
|------------|-----------------|-----------------|------------------|----------------|
| **Percentage** | 0.1450 | 0.1450 | 0.1450 | "14.50%" |
| **Currency** | 125000.00 | 125000.00 | 125000.00 | "$125.0K" |
| **Ratio** | 1.5000 | 1.5000 | 1.5000 | "1.50" |
| **Count** | 100 | 100 | 100 | "100" |

### 1. Percentage Fields (ALWAYS as Decimals)

All percentage-based metrics use **decimal format** (0.15 = 15%, NOT 15.0):

| Field | Table | Database Type | Example | Meaning | Frontend Display |
|-------|-------|--------------|---------|---------|------------------|
| `twr_1d` | portfolio_metrics | NUMERIC(12,8) | 0.0235 | 2.35% daily return | "2.35%" |
| `twr_ytd` | portfolio_metrics | NUMERIC(12,8) | 0.1450 | 14.50% YTD return | "14.50%" |
| `twr_1y` | portfolio_metrics | NUMERIC(12,8) | 0.2150 | 21.50% annual return | "21.50%" |
| `volatility_1y` | portfolio_metrics | NUMERIC(12,8) | 0.1500 | 15% volatility | "15.00%" |
| `max_drawdown_1y` | portfolio_metrics | NUMERIC(12,8) | -0.2500 | -25% max drawdown | "-25.00%" |
| `sharpe_ratio` | portfolio_metrics | NUMERIC(12,8) | 1.5000 | Sharpe of 1.5 | "1.50" |
| `win_rate_1y` | portfolio_metrics | NUMERIC(5,4) | 0.6500 | 65% win rate | "65.00%" |

**Backend Example:**
```python
# ✅ CORRECT - Return as decimal
return {
    "twr_1y": 0.2150,        # 21.50% as decimal
    "volatility": 0.1500,    # 15% as decimal
    "max_drawdown": -0.2500  # -25% as decimal
}

# ❌ WRONG - Never multiply by 100
return {
    "twr_1y": 21.50,         # WRONG!
    "volatility": 15.00      # WRONG!
}
```

**Frontend Example:**
```javascript
// ✅ CORRECT - Pass decimal directly to formatPercentage
formatPercentage(data.twr_1y);  // 0.2150 → "21.50%"

// ❌ WRONG - Don't divide by 100 (current bug!)
formatPercentage(data.twr_1y / 100);  // WRONG!
```

### 2. Currency Fields (Absolute Values)

Currency stored in base units with 2 decimal places:

| Field | Table | Type | Example | Display |
|-------|-------|------|---------|---------|
| `portfolio_value_base` | portfolio_metrics | NUMERIC(20,2) | 125000.00 | "$125.0K" |
| `market_value` | valued_positions | NUMERIC(20,2) | 15625.50 | "$15,625.50" |
| `unrealized_pnl` | valued_positions | NUMERIC(20,2) | -2500.00 | "-$2,500.00" |

### 3. Ratio Fields (Unitless)

Stored as plain numbers without percentage scaling:

| Field | Table | Type | Example | Meaning |
|-------|-------|------|---------|---------|
| `sharpe_1y` | portfolio_metrics | NUMERIC(12,8) | 1.5000 | Sharpe ratio 1.5 |
| `beta_1y` | portfolio_metrics | NUMERIC(12,8) | 1.2000 | Beta of 1.2 |
| `pe_ratio` | security_fundamentals | NUMERIC(12,4) | 18.5000 | P/E of 18.5 |

### 4. Frontend Format Functions

```javascript
// formatPercentage - Expects DECIMAL input (multiplies by 100)
Utils.formatPercentage = function(value, decimals = 2) {
    // Input: 0.1450 (decimal)
    // Output: "14.50%" (multiplies by 100 internally)
    return (value * 100).toFixed(decimals) + '%';
};

// formatCurrency - Expects absolute value
Utils.formatCurrency = function(value, decimals = 2) {
    // Input: 125000.00
    // Output: "$125.0K" (with abbreviation)
    // Handles B/M/K abbreviations automatically
};

// formatNumber - Expects raw number
Utils.formatNumber = function(value, decimals = 2) {
    // Input: 1.5000
    // Output: "1.50"
};
```

### 5. Complete Data Flow Example

```sql
-- Database stores decimal
SELECT twr_ytd FROM portfolio_metrics;
-- Returns: 0.1450
```

```python
# Backend returns decimal (NO multiplication)
async def metrics_compute_twr():
    return {"twr_ytd": 0.1450}  # ✅ CORRECT
```

```javascript
// Frontend formats correctly (NO division)
const ytdReturn = formatPercentage(data.twr_ytd);  // ✅ CORRECT
// Result: "14.50%"
```

### 6. Known Scaling Issues (TO BE FIXED)

| File | Line | Current (Bug) | Should Be |
|------|------|---------------|-----------|
| `frontend/pages.js` | 317 | `formatPercentage(data.change_pct / 100)` | `formatPercentage(data.change_pct)` |
| `frontend/pages.js` | 326 | `formatPercentage(data.ytd_return / 100)` | `formatPercentage(data.ytd_return)` |
| `frontend/pages.js` | 404 | `formatPercentage(holding.weight / 100)` | `formatPercentage(holding.weight)` |
| `frontend/pages.js` | 406 | `formatPercentage(holding.return_pct / 100)` | `formatPercentage(holding.return_pct)` |
| `financial_analyst.py` | 1209 | `metrics.get("max_drawdown_1y", 0) * 100` | `metrics.get("max_drawdown_1y", 0)` |

---

## ⚠️ CRITICAL WARNINGS FOR DEVELOPERS

### 1. Field Naming Convention - MUST READ!

```sql
-- ✅ CORRECT (What's actually in database after Migration 001)
lots.quantity_open      -- Current open quantity
lots.quantity_original  -- Original purchase quantity

-- ❌ WRONG (Common mistakes)
lots.qty_open          -- This was renamed!
lots.qty_original      -- This was renamed!
lots.quantity          -- DEPRECATED - do not use!
```

**Rule:** Always use full field names (`quantity_open`, `quantity_original`) - no abbreviations!

### 2. ID Column Types - NEVER CHANGE!

```sql
-- ⚠️ DANGER: Changing ID types breaks everything!
-- If a table has UUID, keep it UUID
-- If a table has SERIAL, keep it SERIAL
-- NEVER convert between types!

-- Example of what NOT to do:
ALTER TABLE users ALTER COLUMN id TYPE UUID; -- ❌ BREAKS DATA!
```

### 3. Time Field Inconsistency

```sql
-- Most tables use 'asof_date'
factor_exposures.asof_date ✅
currency_attribution.asof_date ✅

-- But portfolio_daily_values uses 'valuation_date'  
portfolio_daily_values.valuation_date ⚠️ INCONSISTENT

-- Always check which field name each table uses!
```

---

## 📊 Database Overview

### Key Statistics (Verified November 7, 2025)
- **Total Tables:** 32 active (not 29 as previously documented)
- **Total Views:** 2 
- **Migrations Executed:** 19 (tracked in migration_history table)
- **Connection Method:** Cross-module pool using `sys.modules` storage
- **Hypertables:** 6 TimescaleDB-optimized tables for time-series data

### Architecture Pattern
```python
# DawsOS uses a hybrid compute/cache pattern:

# 1. Compute-first (default)
result = service.compute_metric(portfolio_id)  # Fresh calculation

# 2. Cache-optional (future optimization)
result = service.get_or_compute(portfolio_id)  # Check cache first

# 3. Store-always (time-series data)
service.store_daily_value(portfolio_id, value)  # Always persist
```

---

## 🗄️ Complete Table Inventory (32 Tables)

### Migration Tracking Table (Added Migration 019)

#### **migration_history** ⭐ NEW
Tracks all executed database migrations with checksums.
```sql
- id: SERIAL (Primary Key)
- migration_number: INTEGER NOT NULL
- migration_name: TEXT NOT NULL
- checksum: TEXT -- MD5 hash of migration file
- executed_at: TIMESTAMP WITH TIME ZONE
- execution_time_ms: INTEGER
- success: BOOLEAN
- error_message: TEXT -- NULL if successful
```

**Current Status:** 19 migrations tracked:
- 001: Field standardization (quantity_open/quantity_original)
- 002-002d: Constraints and indexes
- 003: Table cleanup
- 005-018: Feature additions
- 019: Migration tracking table itself

### Critical Tables for Frontend/Backend Development

#### 1. **lots** - Tax Lot Tracking (MOST IMPORTANT!)
```sql
CREATE TABLE lots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(id),
    security_id UUID REFERENCES securities(id),
    symbol TEXT,
    
    -- ⚠️ CRITICAL FIELD NAMES - USE THESE EXACTLY!
    quantity_open NUMERIC(20,8),      -- Current open quantity
    quantity_original NUMERIC(20,8),  -- Original purchase quantity
    quantity NUMERIC(20,8),            -- DEPRECATED - DO NOT USE!
    
    cost_basis NUMERIC(20,2),
    cost_basis_per_share NUMERIC(20,2),
    acquisition_date DATE,
    closed_date DATE,
    currency TEXT,
    is_open BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_lots_portfolio_open ON lots(portfolio_id) WHERE quantity_open > 0;
CREATE INDEX idx_lots_quantity_open ON lots(quantity_open) WHERE quantity_open > 0;
```

**Usage Example:**
```python
# ✅ CORRECT Python code
async with pool.acquire() as conn:
    positions = await conn.fetch("""
        SELECT 
            symbol,
            SUM(quantity_open) as total_quantity,  -- USE quantity_open!
            SUM(quantity_open * cost_basis_per_share) as total_cost
        FROM lots
        WHERE portfolio_id = $1 AND quantity_open > 0
        GROUP BY symbol
    """, portfolio_id)

# ❌ WRONG - Don't use quantity or qty_open!
```

#### 2. **transactions** - All Portfolio Activity
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(id),
    transaction_type TEXT,  -- 'BUY', 'SELL', 'DIVIDEND', etc.
    security_id UUID REFERENCES securities(id),
    symbol TEXT,
    transaction_date DATE,
    settlement_date DATE,
    quantity NUMERIC(20,8),  -- ✅ Uses 'quantity' (not quantity_open)
    price NUMERIC(20,8),
    amount NUMERIC(20,2),
    currency TEXT,
    fee NUMERIC(20,2),
    realized_pl NUMERIC(20,2),  -- Added in Migration 017
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Usage Example:**
```python
# Create a buy transaction
async def record_buy_transaction(conn, portfolio_id, symbol, quantity, price):
    await conn.execute("""
        INSERT INTO transactions 
        (portfolio_id, transaction_type, symbol, quantity, price, amount, transaction_date)
        VALUES ($1, 'BUY', $2, $3, $4, $5, CURRENT_DATE)
    """, portfolio_id, symbol, quantity, price, quantity * price)
```

#### 3. **portfolios** - Portfolio Configuration
```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    base_currency TEXT NOT NULL DEFAULT 'USD',
    owner_id UUID REFERENCES users(id),
    cost_basis_method TEXT DEFAULT 'FIFO',  -- Added Migration 018
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cost basis methods: FIFO, LIFO, HIFO, SPECIFIC_ID
-- Note: LIFO restricted for stocks per IRS rules
```

---

## 💡 PRACTICAL CODE EXAMPLES

### 1. Getting Current Holdings (User-Scoped Data - Use RLS)

**✅ CORRECT (Standardized Pattern - January 14, 2025):**
```python
from app.db.connection import get_db_connection_with_rls

async def get_holdings(portfolio_id: str, user_id: str):
    """Get current holdings with proper field names and RLS"""
    async with get_db_connection_with_rls(user_id) as conn:
        return await conn.fetch("""
            SELECT 
                l.symbol,
                s.name as security_name,
                SUM(l.quantity_open) as quantity,  -- ✅ quantity_open!
                SUM(l.quantity_open * l.cost_basis_per_share) as total_cost,
                AVG(l.cost_basis_per_share) as avg_cost
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = $1 
                AND l.quantity_open > 0  -- ✅ quantity_open!
            GROUP BY l.symbol, s.name
            ORDER BY total_cost DESC
        """, portfolio_id)
```

**Why RLS?** User-scoped data (lots, portfolios, transactions) requires Row-Level Security to enforce data isolation.

### 2. Recording a Trade with Tax Lot (User-Scoped Data - Use RLS)

**✅ CORRECT (Standardized Pattern - January 14, 2025):**
```python
from app.db.connection import get_db_connection_with_rls

async def execute_trade(portfolio_id: str, trade_type: str, symbol: str, quantity: float, price: float, user_id: str):
    """Execute trade with proper lot tracking and RLS"""
    async with get_db_connection_with_rls(user_id) as conn:
        async with conn.transaction():
            # Record transaction
            tx_id = await conn.fetchval("""
                INSERT INTO transactions 
                (portfolio_id, transaction_type, symbol, quantity, price, amount, transaction_date)
                VALUES ($1, $2, $3, $4, $5, $6, CURRENT_DATE)
                RETURNING id
            """, portfolio_id, trade_type, symbol, quantity, price, quantity * price)
            
            if trade_type == 'BUY':
                # Create new lot with proper field names
                await conn.execute("""
                    INSERT INTO lots 
                    (portfolio_id, symbol, quantity_open, quantity_original, 
                     cost_basis_per_share, cost_basis, acquisition_date)
                    VALUES ($1, $2, $3, $3, $4, $5, CURRENT_DATE)
                """, portfolio_id, symbol, quantity, price, quantity * price)
            
            elif trade_type == 'SELL':
                # Reduce lots using FIFO (proper field names)
                remaining = quantity
                lots = await conn.fetch("""
                    SELECT id, quantity_open 
                    FROM lots
                    WHERE portfolio_id = $1 
                        AND symbol = $2 
                        AND quantity_open > 0
                    ORDER BY acquisition_date ASC  -- FIFO
                    FOR UPDATE
                """, portfolio_id, symbol)
                
                for lot in lots:
                    if remaining <= 0:
                        break
                    
                    reduce_amount = min(remaining, lot['quantity_open'])
                    await conn.execute("""
                        UPDATE lots 
                        SET quantity_open = quantity_open - $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                    """, reduce_amount, lot['id'])
                    
                    remaining -= reduce_amount
```

### 3. Getting Portfolio Metrics (User-Scoped Data - Use RLS)

**✅ CORRECT (Standardized Pattern - January 14, 2025):**
```python
from app.db.connection import get_db_connection_with_rls

async def get_portfolio_metrics(portfolio_id: str, user_id: str):
    """Get metrics using correct time field names and RLS"""
    async with get_db_connection_with_rls(user_id) as conn:
        # Note: portfolio_daily_values uses 'valuation_date'
        nav_history = await conn.fetch("""
            SELECT valuation_date, total_value  
            FROM portfolio_daily_values
            WHERE portfolio_id = $1
            ORDER BY valuation_date DESC
            LIMIT 252
        """, portfolio_id)
        
        # But factor_exposures uses 'asof_date'
        factor_exposures = await conn.fetchrow("""
            SELECT asof_date, beta_real_rate, beta_market, r_squared
            FROM factor_exposures
            WHERE portfolio_id = $1
            ORDER BY asof_date DESC
            LIMIT 1
        """, portfolio_id)
        
        return {
            'nav_history': nav_history,
            'factor_exposures': factor_exposures
        }
```

**Why RLS?** Portfolio metrics are user-scoped data and require Row-Level Security.

### 4. Getting Securities (System-Level Data - Use Helper Functions)

**✅ CORRECT (Standardized Pattern - January 14, 2025):**
```python
from app.db.connection import execute_query, execute_query_one

# Get all securities (system-level data - no RLS needed)
async def get_securities(symbol: str = None):
    """Get securities using helper functions"""
    if symbol:
        return await execute_query_one("""
            SELECT * FROM securities WHERE symbol = $1
        """, symbol)
    else:
        return await execute_query("""
            SELECT * FROM securities ORDER BY symbol
        """)
```

**Why Helper Functions?** Securities are system-level data (shared across all users), so no RLS needed.

---

## 🔄 Time-Series Tables (Hypertables)

DawsOS uses TimescaleDB for efficient time-series data:

```sql
-- Creating a hypertable (already done for these tables)
SELECT create_hypertable('portfolio_daily_values', 'valuation_date');
SELECT create_hypertable('portfolio_metrics', 'date');
SELECT create_hypertable('macro_indicators', 'date');
```

### Hypertable List:
1. `portfolio_daily_values` - Daily NAV (uses `valuation_date` ⚠️)
2. `portfolio_metrics` - Performance metrics (uses `date`)
3. `portfolio_cash_flows` - Cash flows (uses `date`)
4. `macro_indicators` - Economic data (uses `date`)
5. `currency_attribution` - FX attribution (uses `asof_date`)
6. `factor_exposures` - Risk factors (uses `asof_date`)

---

## 🔧 Common Database Operations

### Check Connection on Replit
```python
# Test database connection
import asyncpg
import os

async def test_connection():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        version = await conn.fetchval('SELECT version()')
        print(f"Connected! PostgreSQL {version}")
        
        # Check TimescaleDB
        timescale = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname='timescaledb'")
        print(f"TimescaleDB version: {timescale}")
        
        # Count tables
        table_count = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        print(f"Total tables: {table_count}")
        
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

# Run test
import asyncio
asyncio.run(test_connection())
```

### View Migration History
```sql
-- Check which migrations have been executed
SELECT 
    migration_number,
    migration_name,
    executed_at,
    success,
    error_message
FROM migration_history
ORDER BY migration_number;

-- Verify critical Migration 001 (field renaming)
SELECT * FROM migration_history 
WHERE migration_number = 1;
```

### Debug Field Names
```sql
-- Check actual column names in lots table
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'lots'
ORDER BY ordinal_position;

-- Verify quantity_open exists (should return data)
SELECT COUNT(*) FROM lots WHERE quantity_open > 0;
```

---

## 🐛 Troubleshooting Guide

### Issue: "column qty_open does not exist"
**Cause:** Code using old field names  
**Solution:** Use `quantity_open` and `quantity_original` (full names)

### Issue: "No agent registered for capability tax.realized_gains"
**Cause:** Tax agent not properly initialized  
**Solution:** Check agent registration in combined_server.py

### Issue: Database connection drops after 5 minutes
**Cause:** Replit/Neon auto-sleep feature  
**Solution:** This is normal - connection auto-restores on next request

### Issue: "relation does not exist" 
**Cause:** Migration not executed  
**Solution:** Check migration_history table, run missing migrations

### Issue: Different field names at each layer
**Problem:**
```python
# Database: quantity_open
# Python: qty_open
# Frontend: quantity
```
**Solution:** Standardize to database field names everywhere

---

## 📝 Migration Management

### Check Migration Status
```python
async def check_migrations():
    async with pool.acquire() as conn:
        # Get executed migrations
        executed = await conn.fetch("""
            SELECT migration_number, migration_name, executed_at
            FROM migration_history
            ORDER BY migration_number
        """)
        
        print("Executed Migrations:")
        for m in executed:
            print(f"  {m['migration_number']:03d}: {m['migration_name']} ({m['executed_at']})")
        
        # Check for pending migrations
        migration_files = os.listdir('backend/db/migrations')
        executed_numbers = {m['migration_number'] for m in executed}
        
        pending = []
        for file in migration_files:
            if file.endswith('.sql'):
                num = int(file.split('_')[0])
                if num not in executed_numbers:
                    pending.append(file)
        
        if pending:
            print(f"\nPending Migrations: {pending}")
        else:
            print("\nAll migrations executed ✅")
```

### Execute Migration Safely
```python
async def run_migration(migration_file: str):
    """Execute a migration with proper tracking"""
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                # Read migration file
                with open(f'backend/db/migrations/{migration_file}', 'r') as f:
                    sql = f.read()
                
                # Calculate checksum
                import hashlib
                checksum = hashlib.md5(sql.encode()).hexdigest()
                
                # Check if already executed
                exists = await conn.fetchval("""
                    SELECT 1 FROM migration_history 
                    WHERE migration_number = $1 OR checksum = $2
                """, migration_number, checksum)
                
                if exists:
                    print(f"Migration {migration_file} already executed")
                    return
                
                # Execute migration
                start_time = time.time()
                await conn.execute(sql)
                execution_time = int((time.time() - start_time) * 1000)
                
                # Record in history
                await conn.execute("""
                    INSERT INTO migration_history 
                    (migration_number, migration_name, checksum, execution_time_ms, success)
                    VALUES ($1, $2, $3, $4, true)
                """, migration_number, migration_name, checksum, execution_time)
                
                print(f"✅ Migration {migration_file} executed successfully")
                
            except Exception as e:
                # Record failure
                await conn.execute("""
                    INSERT INTO migration_history 
                    (migration_number, migration_name, error_message, success)
                    VALUES ($1, $2, $3, false)
                """, migration_number, migration_name, str(e))
                raise
```

---

## 🎯 Best Practices for DawsOS Development

### 1. Always Use Transactions for Multi-Step Operations
```python
async with conn.transaction():
    # All queries here succeed or fail together
    await conn.execute(query1)
    await conn.execute(query2)
```

### 2. Use Prepared Statements (Parameterized Queries)
```python
# ✅ SAFE - Prevents SQL injection
await conn.execute("SELECT * FROM lots WHERE portfolio_id = $1", portfolio_id)

# ❌ UNSAFE - Never do this!
await conn.execute(f"SELECT * FROM lots WHERE portfolio_id = '{portfolio_id}'")
```

### 3. Handle Replit Database Sleep
```python
async def execute_with_retry(query, *args, max_retries=3):
    """Handle Replit/Neon database wake-up"""
    for attempt in range(max_retries):
        try:
            async with pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except asyncpg.PostgresConnectionError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)  # Wait for database to wake up
```

### 4. Use Correct Field Names
```python
FIELD_MAPPING = {
    # Always use database field names
    'lots': {
        'open_quantity': 'quantity_open',      # ✅
        'original_quantity': 'quantity_original',  # ✅
        'quantity': None,  # ❌ DEPRECATED
    },
    'portfolio_daily_values': {
        'date': 'valuation_date',  # ⚠️ Inconsistent
    },
    'factor_exposures': {
        'date': 'asof_date',  # ✅ Standard
    }
}
```

### 5. Monitor Connection Pool
```python
# In combined_server.py
@app.get("/api/db/health")
async def db_health():
    pool = get_db_pool()
    return {
        "min_size": pool._minsize,
        "max_size": pool._maxsize,
        "current_size": pool._size,
        "free_connections": pool._freesize,
        "database": "PostgreSQL on Replit/Neon"
    }
```

---

## 📊 Data Statistics (Current Production)

| Table | Row Count | Purpose | Status |
|-------|-----------|---------|--------|
| migration_history | 19 | Migration tracking | ✅ All migrations tracked |
| portfolios | 1 | Michael's portfolio | ✅ Active |
| users | 2 | michael@dawsos.com, test@dawsos.com | ✅ Active |
| lots | 17 | Open positions | ✅ Using quantity_open |
| transactions | 43 | Trade history | ✅ With realized P&L |
| securities | 17 | Security master | ✅ Active |
| prices | 500+ | Price history | ✅ In pricing packs |
| fx_rates | 63 | FX rates | ✅ CAD/USD, EUR/USD |
| portfolio_daily_values | 179 | NAV history | ✅ Daily updates |
| macro_indicators | 102 | Economic data | ✅ For regime detection |

---

## 🚀 Quick Start for New Developers

1. **Check Database Connection:**
```bash
# In Replit Shell
echo $DATABASE_URL  # Should show connection string
```

2. **Verify Field Names:**
```sql
-- Run in Replit Database pane
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'lots';
-- Should show: quantity_open, quantity_original (NOT qty_open!)
```

3. **Test Pattern Execution:**
```python
# Test in Python console
from backend.app.core.pattern_orchestrator import PatternOrchestrator
orchestrator = PatternOrchestrator()
result = await orchestrator.execute('portfolio_overview', {
    'portfolio_id': '64ff3be6-0ed1-4990-a32b-4ded17f0320c'
})
print(f"Pattern result: {result}")
```

4. **Common Portfolio ID for Testing:**
```python
MICHAEL_PORTFOLIO_ID = '64ff3be6-0ed1-4990-a32b-4ded17f0320c'
```

---

## 📚 Related Documentation

- Frontend Integration: See `frontend/api-client.js`
- Pattern Definitions: See `backend/patterns/*.json`
- Agent Capabilities: See `backend/app/agents/`
- Migration Files: See `backend/db/migrations/`

---

## ⚠️ Final Critical Reminders

1. **NEVER use `qty_open` or `qty_original`** - Use `quantity_open` and `quantity_original`
2. **NEVER change ID column types** - Keep UUID as UUID, SERIAL as SERIAL
3. **ALWAYS check which date field** - Some use `asof_date`, others use `valuation_date`
4. **NEVER expose DATABASE_URL** - Contains full credentials
5. **ALWAYS use transactions** - For multi-step operations
6. **CHECK migration_history table** - Before assuming migrations are missing

---

*This documentation reflects the actual production database state as of November 7, 2025, with all 19 migrations executed and 32 tables active.*