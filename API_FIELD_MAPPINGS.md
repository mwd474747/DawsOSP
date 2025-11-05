# API Field Mappings Documentation

**Date:** January 14, 2025  
**Status:** ✅ **DOCUMENTATION COMPLETE**  
**Purpose:** Document all field mappings between layers for field naming consistency

---

## 📊 Executive Summary

This document maps field names across all layers of the DawsOS application to ensure consistency and provide reference for future API versioning.

**Field Naming Standard:**
- **Database:** `quantity_open`, `quantity_original` (full names)
- **Agent Layer:** `quantity` (standardized, full name)
- **Service Layer:** Currently mixed (`qty`, `quantity_open`, `quantity`) - **TO BE STANDARDIZED**
- **API Layer:** Currently mixed (`qty` in trades, `quantity` in transactions) - **DEFERRED**

---

## 🔄 Field Mapping Between Layers

### Quantity Field Mapping

#### Database → Agent Layer

**Database Column:** `lots.quantity_open`  
**Agent Return:** `quantity`  
**Mapping:** `l.quantity_open AS qty` → `"quantity": qty` (normalized in Python)

**Example:**
```python
# Database query
SELECT l.quantity_open AS qty FROM lots l

# Agent return
{
    "quantity": Decimal("100.0"),  # Normalized from qty
    ...
}
```

**Status:** ✅ **CORRECT** - Agent layer normalizes to `quantity`

---

#### Agent Layer → Service Layer

**Agent Return:** `quantity`  
**Service Layer:** Currently mixed (`qty`, `quantity_open`, `quantity`)  
**Mapping:** Depends on service

**Examples:**

1. **Trade Execution Service:**
   - **Expects:** `qty` (parameter)
   - **Returns:** `qty` (internal API)
   - **Status:** ⚠️ **INCONSISTENT** - Should use `quantity`

2. **Currency Attribution Service:**
   - **Expects:** `quantity_open` (from database query)
   - **Returns:** Uses `quantity_open` directly
   - **Status:** ⚠️ **INCONSISTENT** - Should normalize to `quantity`

3. **Optimizer Service:**
   - **Expects:** `quantity` (from agent or service)
   - **Returns:** `quantity` (normalized)
   - **Status:** ✅ **CORRECT**

**Status:** ⚠️ **MIXED** - To be standardized in Phase 3

---

#### Service Layer → API Layer

**Service Layer:** Currently mixed (`qty`, `quantity_open`, `quantity`)  
**API Layer:** Currently mixed (`qty` in trades, `quantity` in transactions)

**Examples:**

1. **Trade API (`/v1/trades`):**
   - **Service Returns:** `qty`
   - **API Model:** `PositionItem.qty`
   - **Status:** ⚠️ **USES `qty`** - Breaking change if changed

2. **Transaction API (`/v1/trades`):**
   - **Service Returns:** `quantity`
   - **API Model:** `TransactionListItem.quantity`
   - **Status:** ✅ **USES `quantity`** - Correct

3. **Lot API (`/v1/trades/lots`):**
   - **Service Returns:** `quantity_original`, `quantity_open`, `quantity`
   - **API Model:** `LotListItem.quantity_original`, `LotListItem.quantity_open`, `LotListItem.quantity`
   - **Status:** ✅ **CORRECT** - Matches database columns

**Status:** ⚠️ **MIXED** - Deferred for backward compatibility

---

## 📋 Complete Field Mapping Table

| Layer | Field Name | Usage | Status | Notes |
|-------|-----------|-------|--------|-------|
| **Database** | `quantity_open` | Current open quantity | ✅ Standardized | Column name |
| **Database** | `quantity_original` | Original quantity | ✅ Standardized | Column name |
| **Database** | `quantity` | Legacy field | ⚠️ Deprecated | Kept for backwards compatibility |
| **Agent Layer** | `quantity` | Position quantity | ✅ Standardized | Agent return structure |
| **Service Layer** | `qty` | Internal API | ⚠️ Inconsistent | Trade execution service |
| **Service Layer** | `quantity_open` | Database column | ⚠️ Inconsistent | Some services use directly |
| **Service Layer** | `quantity` | Normalized | ✅ Correct | Optimizer service |
| **API Layer** | `qty` | Trade API | ⚠️ Inconsistent | Breaking change if changed |
| **API Layer** | `quantity` | Transaction API | ✅ Correct | Matches agent layer |
| **API Layer** | `quantity_open` | Lot API | ✅ Correct | Matches database |

---

## 🔍 Detailed Layer Mappings

### Layer 1: Database

**Table:** `lots`

**Columns:**
- `quantity_open` - Current open quantity (standardized)
- `quantity_original` - Original quantity when lot was created (standardized)
- `quantity` - Legacy field (deprecated, kept for backwards compatibility)

**Status:** ✅ **STANDARDIZED** - Migration complete

---

### Layer 2: Agent Capabilities

**Capabilities:**
- `ledger.positions` → Returns `quantity`
- `pricing.apply_pack` → Returns `quantity`
- `portfolio.get_valued_positions` → Returns `quantity`
- `portfolio.get_position_details` → Returns `quantity_open` ⚠️ **INCONSISTENT**

**Standard:** All agent capabilities should return `quantity`

**Status:** ⚠️ **MOSTLY STANDARDIZED** - One exception to fix

---

### Layer 3: Service Layer

**Services:**

1. **TradeExecutionService:**
   - Method signatures: `qty` (parameter)
   - Return values: `qty` (field)
   - Status: ⚠️ **USES `qty`** - To be standardized

2. **CurrencyAttributionService:**
   - Uses: `quantity_open` (from database)
   - Status: ⚠️ **USES `quantity_open`** - To be normalized

3. **RiskMetricsService:**
   - Uses: `quantity_open` (from database)
   - Status: ⚠️ **USES `quantity_open`** - To be normalized

4. **OptimizerService:**
   - Uses: `quantity` (normalized)
   - Status: ✅ **USES `quantity`** - Correct

5. **ScenariosService:**
   - Uses: `quantity` (but queries legacy `quantity` field) ⚠️ **BUG**
   - Status: ❌ **BUG** - Should use `quantity_open` in queries

**Status:** ⚠️ **MIXED** - To be standardized in Phase 3

---

### Layer 4: API Layer

**Endpoints:**

1. **`POST /v1/trades` (TradeRequest):**
   - Field: `qty`
   - Status: ⚠️ **USES `qty`** - Breaking change if changed

2. **`GET /v1/trades` (TradeResponse):**
   - Field: `qty`
   - Status: ⚠️ **USES `qty`** - Breaking change if changed

3. **`GET /v1/trades/positions` (PositionItem):**
   - Field: `qty`
   - Status: ⚠️ **USES `qty`** - Breaking change if changed

4. **`GET /v1/trades` (TransactionListItem):**
   - Field: `quantity`
   - Status: ✅ **USES `quantity`** - Correct

5. **`GET /v1/trades/lots` (LotListItem):**
   - Fields: `quantity_original`, `quantity_open`, `quantity`
   - Status: ✅ **CORRECT** - Matches database columns

**Status:** ⚠️ **MIXED** - Deferred for backward compatibility

---

## 🔄 Migration Path (Future)

### Current State (v1)

**API Layer:**
- Trade API: `qty`
- Transaction API: `quantity`
- Lot API: `quantity_original`, `quantity_open`, `quantity`

**Service Layer:**
- Mixed usage (`qty`, `quantity_open`, `quantity`)

---

### Future State (v2 - Proposed)

**API Layer:**
- Trade API: `quantity` (breaking change)
- Transaction API: `quantity` (no change)
- Lot API: `quantity_original`, `quantity_open`, `quantity` (no change)

**Service Layer:**
- Standardized to `quantity` everywhere

---

### Migration Strategy

**Phase 1:** Standardize service layer (internal, no breaking changes)
- ✅ Low risk - internal API only

**Phase 2:** Create API v2 with `quantity` fields
- ⚠️ Medium risk - new API version

**Phase 3:** Deprecate API v1
- ⚠️ High risk - requires client migration

**Phase 4:** Remove API v1
- ⚠️ High risk - breaking change

**Timeline:** TBD - Currently deferred

---

## 📝 Field Name Rationale

### Why `quantity` in Agent Layer?

**Rationale:**
- Clearer and more descriptive than `qty`
- Consistent with pattern system expectations
- Matches UI expectations
- Full word is more readable in code

**Decision:** Standardize agent layer to `quantity`

---

### Why `quantity_open` in Database?

**Rationale:**
- Distinguishes from `quantity_original` (original purchase quantity)
- Clear semantic meaning (open = current holdings)
- Matches accounting terminology

**Decision:** Keep database columns as `quantity_open` and `quantity_original`

---

### Why `qty` in Trade API?

**Rationale:**
- Historical naming convention
- Shorter field name (convenience)
- Already in use (backward compatibility)

**Decision:** Keep `qty` in v1 API for backward compatibility, consider `quantity` in v2

---

## 🔍 Cross-Layer Field Access Patterns

### Pattern 1: Database → Agent

**Query:**
```sql
SELECT l.quantity_open AS qty FROM lots l
```

**Python:**
```python
qty = Decimal(str(row["qty"]))  # Read from SQL alias
return {"quantity": qty}  # Normalize to quantity
```

**Status:** ✅ **CORRECT** - Normalizes to `quantity`

---

### Pattern 2: Agent → Service

**Agent Return:**
```python
{
    "quantity": Decimal("100.0"),
    ...
}
```

**Service Access:**
```python
# Correct pattern (optimizer service)
quantity = pos["quantity"]

# Incorrect pattern (corporate actions - bug)
qty = pos.get("qty", 0)  # ❌ BUG - should be "quantity"
```

**Status:** ⚠️ **MIXED** - Some services have bugs

---

### Pattern 3: Service → API

**Service Return:**
```python
{
    "qty": Decimal("100.0"),  # Trade execution service
    ...
}
```

**API Model:**
```python
class PositionItem(BaseModel):
    qty: Decimal  # Matches service return
```

**Status:** ⚠️ **INCONSISTENT** - Uses `qty` instead of `quantity`

---

## 📋 Recommendations

### Immediate (Phase 1)

1. ✅ Fix agent layer bugs (use `quantity` instead of `qty`)
2. ✅ Fix service layer bugs (use `quantity_open` in queries, not legacy `quantity`)
3. ✅ Normalize service layer returns to `quantity`

### Short-term (Phase 2-3)

1. ⚠️ Standardize service layer to `quantity` (internal API)
2. ⚠️ Create helper functions to eliminate duplication

### Long-term (Phase 4)

1. 🔮 Create API v2 with `quantity` fields
2. 🔮 Deprecate API v1
3. 🔮 Migrate clients to API v2
4. 🔮 Remove API v1

**Status:** Currently deferred for backward compatibility

---

## ✅ Summary

**Current State:**
- ✅ Database: Standardized to `quantity_open`/`quantity_original`
- ✅ Agent Layer: Standardized to `quantity` (one exception)
- ⚠️ Service Layer: Mixed usage (`qty`, `quantity_open`, `quantity`)
- ⚠️ API Layer: Mixed usage (`qty` in trades, `quantity` in transactions)

**Future State:**
- ✅ Database: Keep `quantity_open`/`quantity_original` (no change)
- ✅ Agent Layer: Standardized to `quantity` (fix exception)
- ✅ Service Layer: Standardized to `quantity` (Phase 3)
- 🔮 API Layer: Standardized to `quantity` (Phase 4 - deferred)

**Migration Path:** Documented for future API versioning

