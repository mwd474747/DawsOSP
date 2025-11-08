# DawsOS Domain Model Analysis - Transaction & Cash Flow Architecture

**Date**: 2025-11-08
**Purpose**: Comprehensive analysis of transaction→cash flow→valuation domain model
**Context**: Phase 0 preparation after Replit findings

---

## Executive Summary

**Key Finding**: The current system has a **correct domain model** but **incomplete implementation**.

- ✅ **Domain Model**: Correct (cash flows = external money movements only)
- ❌ **Implementation**: Incomplete (seed data only, no automatic extraction)
- 🎯 **Gap**: Missing transaction→cash flow extraction logic

---

## Database Statistics (from Replit)

```
Transactions: 65 total
├── TRANSFER_IN: 30
├── BUY: 17
├── SELL: 4
└── DIVIDEND: 14

Cash Flows: 31 total
└── Type: Not reported (but seed only created TRANSFER_IN → DEPOSIT)

Expected Cash Flows: 30 (TRANSFER_IN) + 14 (DIVIDEND) = 44
Actual Cash Flows: 31
Missing: 13 cash flows (likely all DIVIDENDs)
```

---

## Domain Model: Transactions vs Cash Flows

### Fundamental Concept

**Portfolio** = Container with two components:
1. **Cash balance** (liquid)
2. **Security positions** (equity/bonds/etc.)

**Total NAV** = Cash + Market Value of Positions

### Transaction Types & Their Impact

#### Type 1: External Cash Flows (affect NAV)

These change the portfolio's total value:

**TRANSFER_IN** (External deposit)
```
Before: NAV = $10,000 (cash: $1,000, securities: $9,000)
Deposit: +$5,000 cash
After:  NAV = $15,000 (cash: $6,000, securities: $9,000)

→ Creates cash flow: +$5,000 DEPOSIT
```

**TRANSFER_OUT** (External withdrawal)
```
Before: NAV = $15,000 (cash: $6,000, securities: $9,000)
Withdraw: -$2,000 cash
After:  NAV = $13,000 (cash: $4,000, securities: $9,000)

→ Creates cash flow: -$2,000 WITHDRAWAL
```

**DIVIDEND** (Income received)
```
Before: NAV = $13,000 (cash: $4,000, securities: $9,000)
Dividend: +$100 cash
After:  NAV = $13,100 (cash: $4,100, securities: $9,000)

→ Creates cash flow: +$100 DIVIDEND
```

**FEE** (Management fee paid)
```
Before: NAV = $13,100 (cash: $4,100, securities: $9,000)
Fee: -$50 cash
After:  NAV = $13,050 (cash: $4,050, securities: $9,000)

→ Creates cash flow: -$50 FEE
```

#### Type 2: Internal Transactions (NAV unchanged)

These MOVE VALUE within portfolio, don't change total:

**BUY** (Convert cash → securities)
```
Before: NAV = $13,050 (cash: $4,050, securities: $9,000)
Buy: $1,000 of AAPL
After:  NAV = $13,050 (cash: $3,050, securities: $10,000)

→ NO cash flow (internal reallocation)
```

**SELL** (Convert securities → cash)
```
Before: NAV = $13,050 (cash: $3,050, securities: $10,000)
Sell: $500 of AAPL
After:  NAV = $13,050 (cash: $3,550, securities: $9,500)

→ NO cash flow (internal reallocation)
```

**SPLIT** (Change share count)
```
Before: NAV = $13,050 (100 shares AAPL @ $100 = $10,000)
Split: 2-for-1
After:  NAV = $13,050 (200 shares AAPL @ $50 = $10,000)

→ NO cash flow (just accounting adjustment)
```

---

## Why MWR/IRR Only Uses External Cash Flows

**Money-Weighted Return (MWR)** answers:
> "What return did the INVESTOR achieve, accounting for when they added/removed money?"

**Formula**:
```
NPV = 0 = CF₀ + CF₁/(1+r)^t₁ + CF₂/(1+r)^t₂ + ... + Final_Value/(1+r)^T
```

**Cash Flows** (CF):
- Positive = Money IN (TRANSFER_IN, DIVIDEND)
- Negative = Money OUT (TRANSFER_OUT, FEE)
- BUY/SELL = NOT included (internal moves)

**Example**:
```
Jan 1: Deposit $10,000 (CF = +$10,000)
Feb 1: Buy $5,000 of AAPL (CF = $0, not external)
Mar 1: AAPL pays $50 dividend (CF = +$50)
Apr 1: Sell $2,000 of AAPL (CF = $0, not external)
May 1: Withdraw $1,000 (CF = -$1,000)
May 1: Portfolio value = $11,500

MWR calculation uses:
- CF₀ = +$10,000 (deposit)
- CF₁ = +$50 (dividend)
- CF₂ = -$1,000 (withdrawal)
- Final = -$11,500 (ending value)

NOT included: BUY and SELL (internal portfolio movements)
```

---

## Current Implementation Analysis

### What Exists ✅

**1. Database Schema** (Correct)
```sql
-- Transactions table: All portfolio activity
CREATE TABLE transactions (
    transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT',
                         'TRANSFER_IN', 'TRANSFER_OUT', 'FEE'),
    amount NUMERIC NOT NULL,  -- Signed (+ = inflow, - = outflow)
    transaction_date DATE NOT NULL,
    ...
);

-- Cash flows table: External money movements only
CREATE TABLE portfolio_cash_flows (
    flow_type IN ('DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST', 'FEE'),
    amount NUMERIC NOT NULL,  -- Signed (+ = inflow, - = outflow)
    flow_date DATE NOT NULL,
    transaction_id UUID REFERENCES transactions(id),  -- Link to source
    ...
);
```

**2. MWR Calculation** (Correct)
- Uses `portfolio_cash_flows` table
- Computes IRR from external cash flows
- Adds terminal value as final cash flow

**3. Seed Data** (Partial)
- Extracts TRANSFER_IN → DEPOSIT
- Creates 30 cash flows for 30 TRANSFER_IN transactions

### What's Missing ❌

**1. Automatic Cash Flow Extraction**

Currently: Seed script manually extracts TRANSFER_IN
```python
# backend/scripts/seed_coherent_portfolio_data.py
flows = await conn.fetch("""
    SELECT transaction_date, amount
    FROM transactions
    WHERE portfolio_id = $1 AND transaction_type = 'TRANSFER_IN'
""")

for flow in flows:
    await conn.execute("""
        INSERT INTO portfolio_cash_flows (
            portfolio_id, flow_date, flow_type, amount
        ) VALUES ($1, $2, 'CONTRIBUTION', $3)
    """, portfolio_id, flow['transaction_date'], flow['amount'])
```

**Problem**: Only TRANSFER_IN extracted, DIVIDEND/FEE missing

**2. Transaction Event Handlers**

No automatic cash flow creation when transactions inserted:
- ✅ User creates DIVIDEND transaction
- ❌ No cash flow record created automatically
- ❌ MWR calculation incomplete

**3. Cash Flow Types Mismatch**

Seed uses 'CONTRIBUTION', schema expects 'DEPOSIT':
```python
# Seed script (WRONG)
flow_type = 'CONTRIBUTION'  # Not in CHECK constraint!

# Schema (CORRECT)
flow_type IN ('DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST', 'FEE')
```

---

## Replit's Data Analysis

### Transaction Breakdown

```sql
SELECT transaction_type, COUNT(*) FROM transactions GROUP BY transaction_type;
```

| Type | Count | Should Create Cash Flow? | Cash Flow Type |
|------|-------|--------------------------|----------------|
| TRANSFER_IN | 30 | ✅ YES | DEPOSIT |
| BUY | 17 | ❌ NO | - |
| DIVIDEND | 14 | ✅ YES | DIVIDEND |
| SELL | 4 | ❌ NO | - |

**Expected Cash Flows**: 30 + 14 = **44**
**Actual Cash Flows**: **31**
**Missing**: **13** (likely all DIVIDEND transactions)

### Lot Status Analysis

```sql
SELECT COUNT(*) FROM lots WHERE quantity_open = 0;
-- Result: 0 (none closed)

SELECT COUNT(*) FROM lots WHERE quantity_open > 0;
-- Result: 17 (all open)
```

**Analysis**:
- 4 SELL transactions exist
- But ALL 17 lots remain open (quantity_open > 0)
- **Conclusion**: SELL transactions NOT closing lots properly

---

## Domain Issues Identified

### Issue 1: Missing DIVIDEND Cash Flows 🔴

**Problem**: 14 DIVIDEND transactions, but cash flows only show 31 total

**Root Cause**: Seed script only extracts TRANSFER_IN

**Impact**:
- MWR calculation WRONG (missing dividend income)
- Underestimates returns
- Portfolio performance metrics incorrect

**Fix Required**: Extract DIVIDEND → DIVIDEND cash flows

### Issue 2: Lots Not Closing on SELL 🔴

**Problem**: 4 SELL transactions, but all 17 lots remain open

**Root Cause**: Check lot closing logic in trade execution

**Impact**:
- Position quantities incorrect
- Cost basis tracking broken
- Realized P&L not calculated

**Fix Required**: Verify and fix lot closing in execute_sell()

### Issue 3: Cash Flow Type Mismatch ⚠️

**Problem**: Seed uses 'CONTRIBUTION', schema expects 'DEPOSIT'

**Root Cause**: Schema updated, seed script not updated

**Impact**:
- May cause constraint violation
- Inconsistent data

**Fix Required**: Update seed to use 'DEPOSIT'

### Issue 4: No Automatic Cash Flow Extraction 🔴

**Problem**: Cash flows only created by seed, not by transaction INSERT

**Root Cause**: No trigger or service logic

**Impact**:
- Future user transactions won't create cash flows
- System not production-ready

**Fix Required**: Implement automatic extraction

---

## Proper Architecture Design

### Option 1: Database Trigger (Recommended)

**Pros**: Automatic, always consistent, hard to forget
**Cons**: Logic in database, harder to test

```sql
CREATE OR REPLACE FUNCTION sync_cash_flows_from_transaction()
RETURNS TRIGGER AS $$
BEGIN
    -- Only for transaction types that create external cash flows
    IF NEW.transaction_type IN ('TRANSFER_IN', 'TRANSFER_OUT', 'DIVIDEND', 'FEE') THEN
        INSERT INTO portfolio_cash_flows (
            portfolio_id,
            flow_date,
            flow_type,
            amount,
            currency,
            transaction_id,
            description
        ) VALUES (
            NEW.portfolio_id,
            NEW.transaction_date,
            CASE NEW.transaction_type
                WHEN 'TRANSFER_IN' THEN 'DEPOSIT'
                WHEN 'TRANSFER_OUT' THEN 'WITHDRAWAL'
                WHEN 'DIVIDEND' THEN 'DIVIDEND'
                WHEN 'FEE' THEN 'FEE'
            END,
            NEW.amount,
            NEW.currency,
            NEW.id,
            NEW.narration
        )
        ON CONFLICT (portfolio_id, flow_date, flow_type, transaction_id)
        DO UPDATE SET
            amount = EXCLUDED.amount,
            description = EXCLUDED.description;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER transaction_cash_flow_sync
    AFTER INSERT OR UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION sync_cash_flows_from_transaction();
```

### Option 2: Service Layer (Alternative)

**Pros**: Business logic in application, easier to test
**Cons**: Can forget to call, requires discipline

```python
class TransactionService:
    async def create_transaction(
        self,
        portfolio_id: UUID,
        transaction_type: str,
        amount: Decimal,
        transaction_date: date,
        ...
    ) -> UUID:
        """Create transaction and sync cash flow if applicable"""
        async with self.conn.transaction():
            # Insert transaction
            transaction_id = await self.conn.fetchval("""
                INSERT INTO transactions (...)
                VALUES (...)
                RETURNING id
            """, ...)

            # Sync cash flow if external transaction
            if transaction_type in ('TRANSFER_IN', 'TRANSFER_OUT', 'DIVIDEND', 'FEE'):
                await self._create_cash_flow(
                    portfolio_id=portfolio_id,
                    transaction_id=transaction_id,
                    transaction_type=transaction_type,
                    amount=amount,
                    date=transaction_date
                )

            return transaction_id

    async def _create_cash_flow(self, ...):
        """Create cash flow from transaction"""
        flow_type_map = {
            'TRANSFER_IN': 'DEPOSIT',
            'TRANSFER_OUT': 'WITHDRAWAL',
            'DIVIDEND': 'DIVIDEND',
            'FEE': 'FEE'
        }

        await self.conn.execute("""
            INSERT INTO portfolio_cash_flows (...)
            VALUES (...)
            ON CONFLICT (...) DO UPDATE ...
        """, ...)
```

**Recommendation**: Use **Option 1 (Database Trigger)** because:
- Guarantees consistency (can't forget)
- Works even if transactions inserted directly
- Simpler (no service layer changes needed)
- Standard pattern for derived data

---

## Lot Closing Analysis

### Expected Behavior

**When SELL transaction created**:
1. Find lot(s) to close (FIFO/LIFO/HIFO)
2. Reduce `quantity_open` by sold quantity
3. Set `closed_date` if fully closed
4. Calculate realized P&L
5. Update transaction with realized_pl

### Current Issue

**Replit found**: All 17 lots have `quantity_open > 0`, none closed

**Possible Causes**:
1. execute_sell() not actually closing lots
2. Lot selection logic broken
3. SELL transactions created outside trade execution service
4. Seed data created SELL transactions without closing lots

### Investigation Needed

Check trade execution service:

```python
# backend/app/services/trade_execution.py

async def execute_sell(self, portfolio_id, symbol, qty, price, ...):
    """Should close lots and reduce quantity_open"""

    # Does this actually get called?
    # Does it update quantity_open?
    # Does it set closed_date?
    ...
```

---

## Portfolio Valuation Flow

### How Portfolio Value is Calculated

**1. Current Holdings** (from lots table):
```sql
SELECT
    symbol,
    SUM(quantity_open) as total_shares
FROM lots
WHERE portfolio_id = $1 AND quantity_open > 0
GROUP BY symbol;
```

**2. Current Prices** (from pricing_pack):
```sql
SELECT
    security_id,
    price
FROM prices
WHERE pricing_pack_id = $1;
```

**3. Market Value**:
```
Market Value = Σ (quantity_open × current_price)
```

**4. Cash Balance**:
```
Cash = Initial TRANSFER_IN + DIVIDEND - BUY amounts + SELL amounts - FEE
```

**5. Total NAV**:
```
NAV = Market Value + Cash Balance
```

### Critical Dependencies

**For accurate NAV**:
1. ✅ `quantity_open` must be correct (requires lot closing)
2. ✅ Prices must be current (pricing_pack updated)
3. ✅ All transactions recorded

**For accurate MWR**:
1. ✅ Cash flows must include all TRANSFER_IN/OUT
2. ✅ Cash flows must include all DIVIDEND
3. ✅ Cash flows must include all FEE
4. ❌ Currently missing DIVIDEND cash flows

---

## Phase 0 Action Plan (Updated)

### Task 0.1: Fix Missing Cash Flows (CRITICAL) 🔴

**Priority**: P0 (blocks accurate performance calculation)

**Actions**:
1. Create database trigger for automatic cash flow extraction
2. Backfill missing DIVIDEND cash flows (14 transactions)
3. Verify all 44 expected cash flows exist

**Effort**: 2-3 hours

**Success Criteria**:
- Query returns 44 cash flows (30 DEPOSIT + 14 DIVIDEND)
- MWR calculation includes dividend income
- Future transactions auto-create cash flows

### Task 0.2: Fix Lot Closing Logic (CRITICAL) 🔴

**Priority**: P0 (blocks accurate position tracking)

**Actions**:
1. Investigate why SELL transactions don't close lots
2. Fix execute_sell() if broken
3. Backfill lot closures for 4 SELL transactions
4. Verify quantity_open updated correctly

**Effort**: 2-3 hours

**Success Criteria**:
- SELL transactions reduce quantity_open
- Some lots have quantity_open = 0 (if fully sold)
- Position quantities match expected values

### Task 0.3: Test Pattern Execution (Phase 0 original)

**Priority**: P1 (follows after data fixes)

**Actions**:
1. Run test_patterns.sh
2. Document which patterns work/fail
3. Identify stub data patterns

**Effort**: 2-3 hours

### Task 0.4: Replace Stub Data

**Priority**: P1 (after patterns tested)

**Actions**:
1. Implement real factor analysis
2. Implement real DaR calculation
3. Test with fixed data

**Effort**: 4-6 hours

---

## Questions for Replit

To validate this analysis and guide fixes:

### Query 1: Cash Flow Types
```sql
SELECT flow_type, COUNT(*) as count
FROM portfolio_cash_flows
GROUP BY flow_type
ORDER BY count DESC;
```

**Question**: What flow_types exist? Do we see 'CONTRIBUTION' or 'DEPOSIT'?

### Query 2: DIVIDEND Cash Flows
```sql
SELECT COUNT(*) FROM portfolio_cash_flows
WHERE flow_type = 'DIVIDEND';
```

**Question**: How many DIVIDEND cash flows exist? (Expected: 14)

### Query 3: Transaction→Cash Flow Mapping
```sql
SELECT
    t.transaction_type,
    COUNT(DISTINCT t.id) as transactions,
    COUNT(DISTINCT cf.id) as cash_flows,
    COUNT(DISTINCT t.id) - COUNT(DISTINCT cf.id) as missing
FROM transactions t
LEFT JOIN portfolio_cash_flows cf ON cf.transaction_id = t.id
WHERE t.transaction_type IN ('TRANSFER_IN', 'TRANSFER_OUT', 'DIVIDEND', 'FEE')
GROUP BY t.transaction_type
ORDER BY missing DESC;
```

**Question**: Which transaction types have missing cash flows?

### Query 4: Lot Quantities After SELL
```sql
-- Get lots for securities that were sold
SELECT
    l.symbol,
    l.quantity_original,
    l.quantity_open,
    l.closed_date,
    COUNT(t.id) as sell_count,
    SUM(CASE WHEN t.transaction_type = 'SELL' THEN t.quantity ELSE 0 END) as total_sold
FROM lots l
LEFT JOIN transactions t ON t.symbol = l.symbol AND t.transaction_type = 'SELL'
WHERE l.portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c'
GROUP BY l.symbol, l.quantity_original, l.quantity_open, l.closed_date
HAVING COUNT(t.id) > 0
ORDER BY l.symbol;
```

**Question**: Do lots with SELL transactions have reduced quantity_open?

---

## Summary

### Current State

| Component | Status | Issue |
|-----------|--------|-------|
| Domain Model | ✅ Correct | Proper separation of external vs internal flows |
| Database Schema | ✅ Correct | Tables and constraints properly designed |
| MWR Calculation | ✅ Correct | Uses external cash flows only |
| Cash Flow Extraction | ❌ Broken | Only TRANSFER_IN extracted, missing DIVIDEND |
| Lot Closing | ❌ Broken | SELL transactions not closing lots |
| Automatic Sync | ❌ Missing | No trigger/service for auto cash flow creation |

### Root Cause

**Seed data approach**: System was bootstrapped with seed scripts that manually created cash flows, but:
1. Only extracted TRANSFER_IN (incomplete)
2. No automatic extraction implemented
3. SELL transactions created without closing lots

**Result**: Data inconsistencies that break calculations

### Fix Strategy

**Phase 0 Priority Changes**:
1. **FIRST**: Fix data integrity (cash flows, lot closing)
2. **SECOND**: Test patterns with correct data
3. **THIRD**: Replace stub data

**Why**: Patterns depend on accurate data. Fix foundation first.

---

**Created**: 2025-11-08
**Status**: Analysis complete, ready for implementation
**Next Step**: Implement cash flow extraction trigger + backfill
