# Field Naming Consistency Refactoring Plan

**Date:** January 14, 2025  
**Status:** 📋 **COMPREHENSIVE PLAN** (Updated with Deep Analysis)  
**Purpose:** Standardize quantity field naming across entire application base

**Related Documents:**
- `FIELD_NAMING_SYSTEM_ANALYSIS.md` - Current system analysis
- `FIELD_NAMING_COMPREHENSIVE_ANALYSIS.md` - Deep analysis with duplicates, anti-patterns, and history

---

## 📊 Executive Summary

**Current State:** Field naming is inconsistent across layers:
- ✅ **Database**: `quantity_open`, `quantity_original` (standardized)
- ✅ **Agent Layer**: `quantity` (standardized)
- ⚠️ **Service Layer**: `qty` (internal API)
- ⚠️ **API Layer**: Mixed (`qty` in trades, `quantity` in transactions, both in lots)
- ❌ **Pattern System**: `quantity` (correct, but not consistent with API)

**Goal:** Standardize all quantity fields to use `quantity` across the entire application base.

**Rationale:**
- Agent layer already uses `quantity` (source of truth)
- Pattern system uses `quantity` (already correct)
- UI expects `quantity` (from pattern system)
- API should match for consistency

---

## 🔍 Current Field Name Usage Analysis

### Layer 1: Database ✅ **ALREADY STANDARDIZED**

**Columns:**
- `lots.quantity_open` - Current open quantity
- `lots.quantity_original` - Original quantity
- `lots.quantity` - Legacy quantity (deprecated)
- `transactions.quantity` - Transaction quantity

**Status:** ✅ **NO CHANGES NEEDED**

---

### Layer 2: Agent Capabilities ✅ **ALREADY STANDARDIZED**

**Return Structure:**
- `ledger.positions` → `quantity`
- `pricing.apply_pack` → `quantity`
- All other agents → `quantity`

**Status:** ✅ **NO CHANGES NEEDED**

---

### Layer 3: Service Layer ⚠️ **USES `qty` (INTERNAL)**

**Files:**
1. `backend/app/services/trade_execution.py`
   - Method signatures: `qty` parameter
   - Return values: `qty` field
   - Internal dict keys: `qty`

**Current Usage:**
```python
# Method signature
async def execute_buy(self, ..., qty: Decimal, ...)

# Return value
{
    "qty": qty,
    ...
}

# get_portfolio_positions
{
    "qty": row["qty"],  # From SQL alias
    ...
}
```

**Rationale for Keeping `qty`:**
- Internal service layer API
- Not exposed to external consumers
- Used only within backend
- Can keep as-is OR change for consistency

**Recommendation:** Change to `quantity` for consistency (low risk since internal)

---

### Layer 4: API Layer ⚠️ **MIXED USAGE (NEEDS STANDARDIZATION)**

#### 4.1 Trade API (`/v1/trades`) - Uses `qty`

**Models:**
- `TradeRequest.qty` - Request field
- `TradeResponse.qty` - Response field
- `PositionItem.qty` - Position field
- `LotInfo.qty_closed` - Lot field

**Current:**
```python
class TradeRequest(BaseModel):
    qty: Decimal  # ← Uses qty

class TradeResponse(BaseModel):
    qty: Decimal  # ← Uses qty

class PositionItem(BaseModel):
    qty: Decimal  # ← Uses qty

class LotInfo(BaseModel):
    qty_closed: Optional[Decimal]  # ← Uses qty_closed
```

**Impact:** External API - breaking change if changed

---

#### 4.2 Transaction API (`/v1/trades`) - Uses `quantity`

**Models:**
- `TransactionListItem.quantity` - Transaction field

**Current:**
```python
class TransactionListItem(BaseModel):
    quantity: Optional[Decimal]  # ← Uses quantity
```

**Status:** ✅ **ALREADY CORRECT**

---

#### 4.3 Lot API (`/v1/trades/lots`) - Uses `quantity_*`

**Models:**
- `LotListItem.quantity_original` - Original quantity
- `LotListItem.quantity_open` - Open quantity
- `LotListItem.quantity` - Legacy quantity

**Current:**
```python
class LotListItem(BaseModel):
    quantity_original: Decimal  # ← Uses quantity_original
    quantity_open: Decimal      # ← Uses quantity_open
    quantity: Decimal           # ← Uses quantity (legacy)
```

**Status:** ✅ **CORRECT** (matches database columns)

---

#### 4.4 Pattern System - Uses `quantity`

**Models:**
- `Position.quantity` - Position field

**Current:**
```python
class Position(BaseModel):
    quantity: Decimal  # ← Uses quantity
```

**Status:** ✅ **ALREADY CORRECT**

---

## 🎯 Standardization Strategy

### Option 1: Full Standardization (Recommended)

**Goal:** Use `quantity` everywhere except database column names and lot-specific fields.

**Standard:**
- **Agent returns**: `quantity` ✅ (already correct)
- **Pattern system**: `quantity` ✅ (already correct)
- **API position fields**: `quantity` (change from `qty`)
- **API trade fields**: `quantity` (change from `qty`)
- **Service layer**: `quantity` (change from `qty`)
- **Lot-specific fields**: `quantity_open`, `quantity_original` (keep as-is)

**Rationale:**
- Matches agent layer (source of truth)
- Matches pattern system (already standardized)
- Clearer and more descriptive
- Consistent with database naming pattern

---

### Option 2: Keep API as-is (Pragmatic)

**Goal:** Keep API layer using `qty` for backwards compatibility, but fix agent consumption bugs.

**Standard:**
- **Agent returns**: `quantity` ✅ (already correct)
- **Pattern system**: `quantity` ✅ (already correct)
- **API layer**: Keep `qty` (no breaking changes)
- **Service layer**: Keep `qty` (internal API)
- **Agent consumption**: Fix bugs (use `quantity`)

**Rationale:**
- No breaking API changes
- Fixes immediate bugs
- Less risk
- Can standardize later with API versioning

---

## 📋 Recommended Refactoring Plan

**Note:** This plan has been expanded based on comprehensive analysis. See `FIELD_NAMING_COMPREHENSIVE_ANALYSIS.md` for details on duplicates, anti-patterns, and development history.

### Phase 1: Fix Critical Bugs (IMMEDIATE)

**Priority:** P0 - Fixes broken functionality

**Changes:**
1. Fix `corporate_actions.upcoming` (line 2839) - Change `qty` to `quantity`
2. Fix `corporate_actions.calculate_impact` (lines 2993, 2996) - Change `qty` to `quantity`
3. Fix `scenarios.py` SQL queries (lines 318, 396, 773, 777) - Change `quantity` to `quantity_open`
4. Fix `financial_analyst.py` return field (line 1395) - Change `quantity_open` to `quantity`
5. Remove transitional support from `pricing.apply_pack` (line 392)

**Files:**
- `backend/app/agents/data_harvester.py`
- `backend/app/agents/financial_analyst.py`

**Impact:** Low risk - internal fixes only

---

### Phase 2: Create Helper Functions (HIGH VALUE)

**Priority:** P1 - Reduces duplication and anti-patterns

**Changes:**
1. Create `extract_symbols()` helper in `portfolio_helpers.py`
2. Create `extract_holdings_map()` helper in `portfolio_helpers.py`
3. Create `get_portfolio_positions_with_prices()` helper in `portfolio_helpers.py`
4. Update all services to use new helpers (eliminates 6+ duplicate SQL queries)

**Files:**
- `backend/app/services/portfolio_helpers.py` (add new functions)
- `backend/app/services/currency_attribution.py`
- `backend/app/services/risk_metrics.py`
- `backend/app/services/optimizer.py`
- `backend/app/services/scenarios.py`
- `backend/app/agents/data_harvester.py`

**Impact:** Medium risk - refactoring, but eliminates duplication and anti-patterns

---

### Phase 3: Standardize Service Layer (RECOMMENDED)

**Priority:** P1 - Improves consistency

**Changes:**
1. Change `TradeExecutionService` method signatures from `qty` to `quantity`
2. Change return values from `qty` to `quantity`
3. Normalize database column names to `quantity` in return values
4. Update all service return values to use `quantity`

**Files:**
- `backend/app/services/trade_execution.py`
- `backend/app/services/currency_attribution.py`
- `backend/app/services/risk_metrics.py`
- All other services using positions

**Impact:** Medium risk - service layer is internal but used by API routes

---

### Phase 4: Standardize API Layer (OPTIONAL - Breaking Change)

**Priority:** P2 - Full consistency (requires API versioning)

**Changes:**
1. Change `TradeRequest.qty` → `TradeRequest.quantity`
2. Change `TradeResponse.qty` → `TradeResponse.quantity`
3. Change `PositionItem.qty` → `PositionItem.quantity`
4. Change `LotInfo.qty_closed` → `LotInfo.quantity_closed`

**Files:**
- `backend/app/api/routes/trades.py`
- `backend/app/services/trade_execution.py` (already updated in Phase 2)

**Impact:** High risk - breaking API change, requires:
- API versioning (e.g., `/v2/trades`)
- Deprecation notice for `/v1/trades`
- Client migration guide
- Backwards compatibility period

**Alternative:** Keep `/v1/trades` with `qty`, introduce `/v2/trades` with `quantity`

---

## 🔧 Detailed Refactoring Steps

### Step 1: Fix Corporate Actions Bugs (Phase 1)

**File:** `backend/app/agents/data_harvester.py`

**Line 2839:**
```python
# BEFORE
symbols = [p.get("symbol") for p in positions if p.get("qty", 0) > 0]

# AFTER
symbols = [p.get("symbol") for p in positions if p.get("quantity", 0) > 0]
```

**Line 2993:**
```python
# BEFORE
holdings = {p.get("symbol"): float(p.get("qty", 0)) for p in positions}

# AFTER
holdings = {p.get("symbol"): float(p.get("quantity", 0)) for p in positions}
```

**Line 2996:**
```python
# BEFORE
holdings = {p.get("symbol"): float(p.get("qty", 0)) for p in holdings}

# AFTER
holdings = {p.get("symbol"): float(p.get("quantity", 0)) for p in holdings}
```

**File:** `backend/app/agents/financial_analyst.py`

**Line 392:**
```python
# BEFORE
qty = pos.get("quantity", pos.get("qty", Decimal("0")))  # Support both field names

# AFTER
qty = pos.get("quantity", Decimal("0"))  # Only use quantity (standardized)
```

---

### Step 2: Standardize Service Layer (Phase 2)

**File:** `backend/app/services/trade_execution.py`

**Method Signatures:**
```python
# BEFORE
async def execute_buy(self, ..., qty: Decimal, ...)
async def execute_sell(self, ..., qty: Decimal, ...)

# AFTER
async def execute_buy(self, ..., quantity: Decimal, ...)
async def execute_sell(self, ..., quantity: Decimal, ...)
```

**Return Values:**
```python
# BEFORE
{
    "qty": qty,
    ...
}

# AFTER
{
    "quantity": quantity,
    ...
}
```

**SQL Aliases:**
```python
# BEFORE
SELECT SUM(quantity_open) as qty, ...

# AFTER
SELECT SUM(quantity_open) as quantity, ...
```

**Update All References:**
- Change all `qty` to `quantity` in method bodies
- Update docstrings
- Update variable names (optional, but recommended)

---

### Step 3: Standardize API Layer (Phase 3 - Optional)

**File:** `backend/app/api/routes/trades.py`

**Pydantic Models:**
```python
# BEFORE
class TradeRequest(BaseModel):
    qty: Decimal

class TradeResponse(BaseModel):
    qty: Decimal

class PositionItem(BaseModel):
    qty: Decimal

class LotInfo(BaseModel):
    qty_closed: Optional[Decimal]

# AFTER
class TradeRequest(BaseModel):
    quantity: Decimal  # Changed from qty

class TradeResponse(BaseModel):
    quantity: Decimal  # Changed from qty

class PositionItem(BaseModel):
    quantity: Decimal  # Changed from qty

class LotInfo(BaseModel):
    quantity_closed: Optional[Decimal]  # Changed from qty_closed
```

**Route Handlers:**
```python
# BEFORE
result = await service.execute_buy(..., qty=trade.qty, ...)
return TradeResponse(..., qty=result["qty"], ...)

# AFTER
result = await service.execute_buy(..., quantity=trade.quantity, ...)
return TradeResponse(..., quantity=result["quantity"], ...)
```

---

## 📊 Impact Assessment

### Phase 1: Fix Bugs
- **Risk:** Low
- **Impact:** Positive (fixes broken functionality)
- **Breaking Changes:** None
- **Testing:** Internal agent tests

---

### Phase 2: Service Layer
- **Risk:** Medium
- **Impact:** Positive (improves consistency)
- **Breaking Changes:** Internal API only (no external impact)
- **Testing:** Service layer tests, API route tests

---

### Phase 3: API Layer
- **Risk:** High
- **Impact:** Positive (full consistency, but breaking change)
- **Breaking Changes:** Yes - external API consumers affected
- **Testing:** Full API integration tests, client migration tests

---

## 🧪 Testing Strategy

### Phase 1 Testing
1. Unit tests for `corporate_actions.upcoming`
2. Unit tests for `corporate_actions.calculate_impact`
3. Integration test: Execute `corporate_actions_upcoming` pattern
4. Verify symbols are extracted correctly
5. Verify actions are filtered by portfolio holdings

---

### Phase 2 Testing
1. Unit tests for `TradeExecutionService`
2. Integration tests for trade execution
3. Verify API routes still work (they consume service layer)
4. Test all trade scenarios (buy, sell, multi-currency)

---

### Phase 3 Testing
1. Full API integration tests
2. Verify backwards compatibility (if keeping v1)
3. Test client migration (if migrating to v2)
4. Load testing to ensure no performance impact

---

## ✅ Recommendation

**Recommended Approach:** Execute Phase 1 immediately, Phase 2 next, Phase 3 later with API versioning.

**Rationale:**
1. **Phase 1** fixes critical bugs (no risk)
2. **Phase 2** improves consistency without breaking changes (medium risk, manageable)
3. **Phase 3** requires careful planning with API versioning (high risk, needs client coordination)

**Timeline:**
- **Phase 1:** 1 day (immediate - fixes broken functionality)
- **Phase 2:** 2-3 days (high value - eliminates duplication)
- **Phase 3:** 3-5 days (recommended - improves consistency)
- **Phase 4:** 1-2 weeks (optional - requires API versioning and client migration)

---

## 🔍 Additional Findings from Deep Analysis

**Comprehensive Analysis:** See `FIELD_NAMING_COMPREHENSIVE_ANALYSIS.md` for:
- **251 occurrences** across **24 files** analyzed
- **6+ duplicate SQL queries** identified
- **5 anti-patterns** documented
- **Development history** and rationale
- **Detailed code examples** and fixes

---

## 📝 Summary

**Yes, it can be refactored to be consistent across the application base.**

**Current Inconsistencies:**
- Agent layer: ✅ Uses `quantity` (correct)
- Pattern system: ✅ Uses `quantity` (correct)
- Service layer: ⚠️ Uses `qty` (internal, can change)
- API layer: ⚠️ Mixed (`qty` in trades, `quantity` in transactions)

**Recommended Standard:**
- Use `quantity` everywhere except database columns and lot-specific fields
- Keep `quantity_open`, `quantity_original` for lot-specific data (matches database)

**Phased Approach:**
1. **Phase 1:** Fix bugs (immediate, low risk)
2. **Phase 2:** Standardize service layer (next, medium risk)
3. **Phase 3:** Standardize API layer (later, high risk - requires API versioning)

