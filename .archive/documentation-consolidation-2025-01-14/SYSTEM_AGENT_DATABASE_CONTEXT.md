# System Agent Database Context

**Date:** January 14, 2025  
**Purpose:** Database schema reference for system agents  
**Deployment:** Replit (production environment)

---

## Critical Database Schema Information

### Field Naming Standards

**IMPORTANT:** Migration 001 **WAS EXECUTED** on the Replit database.

**Database Columns (Actual):**
- `lots.quantity_open` - Remaining open quantity (renamed from `qty_open` by Migration 001)
- `lots.quantity_original` - Original purchase quantity (renamed from `qty_original` by Migration 001)
- `lots.quantity` - **DEPRECATED** (kept for backwards compatibility, do not use)

**Code Layer:**
- SQL queries should use `quantity_open` and `quantity_original` (full names)
- No SQL aliases needed - database has full names
- Python code should access results as `row["quantity_open"]` and `row["quantity_original"]`

**Legacy Field:**
- `lots.quantity` is deprecated (see Migration 014 deprecation comment)
- Do not use in new code

---

## Database Schema: `lots` Table

```sql
CREATE TABLE lots (
    id UUID PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),
    security_id UUID NOT NULL REFERENCES securities(id),
    symbol TEXT NOT NULL,
    
    -- Quantity Fields (STANDARDIZED)
    quantity NUMERIC(20,8) NOT NULL,  -- DEPRECATED (use quantity_open)
    quantity_open NUMERIC(20,8) NOT NULL,  -- Open quantity (from Migration 001)
    quantity_original NUMERIC(20,8) NOT NULL,  -- Original purchase quantity (from Migration 001)
    
    -- Cost Basis
    cost_basis NUMERIC(20,2) NOT NULL,
    cost_basis_per_share NUMERIC(20,2) NOT NULL,
    
    -- Dates
    acquisition_date DATE NOT NULL,
    closed_date DATE,  -- Date when lot was fully closed (quantity_open = 0)
    
    -- Currency
    currency TEXT NOT NULL DEFAULT 'USD',
    
    -- Status
    is_open BOOLEAN DEFAULT TRUE,  -- False when lot is fully sold
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT lots_qty_open_nonnegative CHECK (quantity_open >= 0),
    CONSTRAINT lots_qty_open_lte_original CHECK (quantity_open <= quantity_original)
);
```

**Indexes:**
- `idx_lots_quantity_open` - Index on `quantity_open` WHERE `quantity_open > 0`
- `idx_lots_portfolio_id` - Index on `portfolio_id`
- `idx_lots_security_id` - Index on `security_id`

---

## Migration History

### Migration 001: Field Standardization ✅ **COMPLETED**
- **Status:** Successfully executed on Replit database
- **Changes:**
  - Renamed `qty_open` → `quantity_open`
  - Renamed `qty_original` → `quantity_original`
- **Impact:** All SQL queries should use full field names

### Migration 007: Add Lot Quantity Tracking ✅ **COMPLETED**
- **Status:** Successfully executed
- **Changes:**
  - Added `qty_open` and `qty_original` columns (later renamed by Migration 001)
  - Added `closed_date` column
  - Created `reduce_lot()` function

### Migration 002b: Fix Quantity Indexes ✅ **COMPLETED**
- **Status:** Successfully executed
- **Changes:**
  - Renamed index: `idx_lots_qty_open` → `idx_lots_quantity_open`
  - Updated index to reference `quantity_open` column

### Migration 002c: Fix reduce_lot() Function ✅ **COMPLETED**
- **Status:** Successfully executed
- **Changes:**
  - Updated function to use `quantity_open` instead of `qty_open`
  - Added row-level locking for concurrency safety

---

## SQL Query Patterns

### Correct Pattern (Use Full Field Names)

```sql
-- ✅ CORRECT: Use quantity_open and quantity_original
SELECT
    l.security_id,
    l.symbol,
    l.quantity_open,
    l.quantity_original,
    l.cost_basis,
    l.currency
FROM lots l
WHERE l.portfolio_id = $1
  AND l.quantity_open > 0
ORDER BY l.acquisition_date ASC;
```

### Incorrect Pattern (Do NOT Use Abbreviated Names)

```sql
-- ❌ WRONG: Do not use qty_open or qty_original
SELECT
    l.qty_open,  -- ❌ Field doesn't exist (was renamed by Migration 001)
    l.qty_original  -- ❌ Field doesn't exist (was renamed by Migration 001)
FROM lots l;
```

---

## Python Code Patterns

### Correct Pattern (Access Full Field Names)

```python
# ✅ CORRECT: Access quantity_open and quantity_original
rows = await conn.fetch(
    """
    SELECT
        l.security_id,
        l.symbol,
        l.quantity_open,
        l.quantity_original,
        l.cost_basis
    FROM lots l
    WHERE l.portfolio_id = $1
      AND l.quantity_open > 0
    """,
    portfolio_id
)

for row in rows:
    qty_open = Decimal(str(row["quantity_open"]))  # ✅ Correct
    qty_original = Decimal(str(row["quantity_original"]))  # ✅ Correct
```

### Incorrect Pattern (Do NOT Access Abbreviated Names)

```python
# ❌ WRONG: Do not access qty_open or qty_original
qty_open = row["qty_open"]  # ❌ KeyError: field doesn't exist
qty_original = row["qty_original"]  # ❌ KeyError: field doesn't exist
```

---

## Common Issues & Solutions

### Issue: "column 'qty_open' does not exist"

**Cause:** Code is using abbreviated field names that were renamed by Migration 001.

**Solution:** Update SQL queries to use `quantity_open` and `quantity_original` (full names).

### Issue: "column 'quantity_open' does not exist"

**Cause:** Migration 001 was not executed on the database.

**Solution:** Run Migration 001 to rename fields from `qty_open` to `quantity_open`.

### Issue: KeyError when accessing `row["qty_open"]`

**Cause:** Python code is accessing abbreviated field names.

**Solution:** Update Python code to access `row["quantity_open"]` and `row["quantity_original"]`.

---

## Database Connection

**Deployment:** Replit (production environment)

**Connection String:**
```bash
DATABASE_URL="postgresql://user:password@host:5432/dawsos"
```

**Connection Management:**
- Cross-module pool storage using `sys.modules['__dawsos_db_pool_storage__']`
- Pool registered in `combined_server.py`
- Access via `get_db_pool()` from `app.db.connection`

---

## Verification Queries

### Check Field Names

```sql
-- Verify field names exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'lots'
  AND column_name IN ('quantity_open', 'quantity_original', 'qty_open', 'qty_original')
ORDER BY column_name;

-- Expected result:
-- quantity_open (exists) ✅
-- quantity_original (exists) ✅
-- qty_open (does not exist) ❌
-- qty_original (does not exist) ❌
```

### Check Constraints

```sql
-- Verify constraints reference correct field names
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'lots'::regclass
  AND conname LIKE '%qty%';

-- Expected: Constraints reference quantity_open and quantity_original
```

---

## Summary

**Database Schema (Replit Production):**
- ✅ Uses `quantity_open` and `quantity_original` (full names)
- ✅ Migration 001 was executed successfully
- ✅ All constraints and indexes reference full field names

**Code Requirements:**
- ✅ SQL queries must use `quantity_open` and `quantity_original`
- ✅ Python code must access `row["quantity_open"]` and `row["quantity_original"]`
- ❌ Do NOT use `qty_open` or `qty_original` (abbreviated names)

**Status:** ✅ **PRODUCTION READY** - Schema is standardized and consistent

