# Tax Patterns Architecture & Implementation Status

**Date:** January 14, 2025
**Status:** Patterns Created, Capabilities NOT Implemented
**Business Impact:** $200K ARR potential (blocked until implementation)

---

## Executive Summary

**What Exists:**
- ✅ 2 tax pattern JSON files (perfect structure)
- ✅ Pattern orchestrator can load them
- ❌ 0 of 9 required capabilities implemented

**What's Missing:**
- ❌ TaxAnalyst agent class
- ❌ 9 tax capability methods
- ❌ UI components to trigger patterns

**Current State:** Patterns are **non-functional** but **don't break the app** (not exposed in UI)

---

## Pattern Overview

### Pattern 1: Portfolio Tax Report
**File:** `backend/patterns/portfolio_tax_report.json`
**Purpose:** Generate IRS Form 1099-B compliant tax reporting

**Inputs:**
```json
{
  "portfolio_id": "string (required)",
  "tax_year": "integer (default: 2025)",
  "lot_selection_method": "fifo|lifo|hifo|specific (default: fifo)",
  "include_wash_sales": "boolean (default: true)"
}
```

**Steps:**
1. `tax.realized_gains` - Calculate realized P&L for tax year
2. `tax.wash_sales` - Identify IRS wash sale violations
3. `tax.lot_details` - Generate lot-level detail report
4. `tax.summary` - Aggregate tax summary with short/long term breakdown

**Expected Outputs:**
```json
{
  "realized_gains": {
    "short_term": {...},
    "long_term": {...},
    "by_security": [...]
  },
  "wash_sales": [
    {
      "security_id": "...",
      "sale_date": "...",
      "repurchase_date": "...",
      "disallowed_loss": 1500.00
    }
  ],
  "tax_lots": [...],
  "tax_summary": {
    "total_realized_gains": 50000.00,
    "short_term_gains": 20000.00,
    "long_term_gains": 30000.00,
    "wash_sale_adjustments": -1500.00
  }
}
```

---

### Pattern 2: Tax Harvesting Opportunities
**File:** `backend/patterns/tax_harvesting_opportunities.json`
**Purpose:** Identify tax-loss harvesting opportunities to reduce tax burden

**Inputs:**
```json
{
  "portfolio_id": "string (required)",
  "min_loss_threshold": "number (default: 1000)",
  "avoid_wash_sales": "boolean (default: true)",
  "tax_rate": "number (default: 0.32)"
}
```

**Steps:**
1. `ledger.positions` - Get current portfolio positions ✅ **IMPLEMENTED**
2. `metrics.unrealized_pl` - Calculate unrealized P&L ❌ **MISSING**
3. `tax.identify_losses` - Filter positions with losses above threshold ❌ **MISSING**
4. `tax.wash_sale_check` - Check 30-day window for wash sale risk ❌ **MISSING**
5. `tax.calculate_benefit` - Estimate tax savings from harvesting ❌ **MISSING**
6. `tax.rank_opportunities` - Rank by tax benefit potential ❌ **MISSING**

**Expected Outputs:**
```json
{
  "opportunities": [
    {
      "security_id": "...",
      "symbol": "XYZ",
      "unrealized_loss": -5000.00,
      "tax_benefit": 1600.00,
      "wash_sale_risk": false,
      "recommended_action": "SELL",
      "priority_rank": 1
    }
  ],
  "total_potential_savings": 15000.00
}
```

---

## Missing Capabilities Analysis

### Category 1: Tax Compliance Capabilities (TaxAnalyst Agent)

**Agent File:** `backend/app/agents/tax_analyst.py` ❌ **DOES NOT EXIST**

#### 1. `tax.realized_gains`
**Purpose:** Calculate realized gains/losses for tax year
**Complexity:** HIGH (lot accounting, FIFO/LIFO/HIFO logic)
**Estimated Effort:** 4 hours

**Implementation Requirements:**
- Query `transactions` table for SELL transactions in tax year
- Apply lot selection method (FIFO, LIFO, HIFO, SPECIFIC_LOT)
- Calculate cost basis using Migration 017's `realized_pl` field
- Separate short-term (<1 year) vs long-term (>=1 year) gains
- Handle corporate actions (splits, dividends, spinoffs)

**Data Sources:**
- `transactions` table (with `realized_pl` field from Migration 017)
- `lots` table (for cost basis tracking)
- `securities` table (for security details)

**SQL Query Pattern:**
```sql
SELECT
    t.security_id,
    s.symbol,
    t.quantity,
    t.price,
    t.realized_pl,
    t.transaction_date,
    l.acquisition_date,
    EXTRACT(YEAR FROM AGE(t.transaction_date, l.acquisition_date)) as holding_period
FROM transactions t
JOIN securities s ON t.security_id = s.id
JOIN lots l ON t.lot_id = l.id
WHERE t.type = 'SELL'
  AND t.portfolio_id = $1
  AND EXTRACT(YEAR FROM t.transaction_date) = $2
ORDER BY t.transaction_date
```

---

#### 2. `tax.wash_sales`
**Purpose:** Identify IRS wash sale violations (30-day rule)
**Complexity:** MEDIUM
**Estimated Effort:** 3 hours

**Implementation Requirements:**
- Detect sales at a loss within 30 days of repurchase
- Flag "substantially identical" securities
- Calculate disallowed loss amount
- Adjust cost basis of replacement shares

**IRS Rule:**
> If you sell stock at a loss and buy substantially identical stock within 30 days
> before or after the sale, the loss is disallowed for current tax year.

**SQL Query Pattern:**
```sql
WITH sales_at_loss AS (
    SELECT * FROM transactions
    WHERE type = 'SELL' AND realized_pl < 0
),
repurchases AS (
    SELECT * FROM transactions
    WHERE type = 'BUY'
)
SELECT
    s.security_id,
    s.transaction_date as sale_date,
    r.transaction_date as repurchase_date,
    s.realized_pl as disallowed_loss
FROM sales_at_loss s
JOIN repurchases r ON s.security_id = r.security_id
WHERE r.transaction_date BETWEEN (s.transaction_date - INTERVAL '30 days')
                              AND (s.transaction_date + INTERVAL '30 days')
```

---

#### 3. `tax.lot_details`
**Purpose:** Generate lot-level detail report
**Complexity:** LOW
**Estimated Effort:** 2 hours

**Implementation Requirements:**
- Query `lots` table for all open and closed lots
- Include acquisition date, quantity, cost basis
- Show current market value and unrealized P&L
- Format for tax reporting

---

#### 4. `tax.summary`
**Purpose:** Aggregate tax summary
**Complexity:** LOW
**Estimated Effort:** 1 hour

**Implementation Requirements:**
- Sum short-term and long-term gains
- Apply wash sale adjustments
- Calculate total tax liability estimate
- Format for IRS Form 1099-B

---

### Category 2: Metrics Capabilities (FinancialAnalyst Agent)

#### 5. `metrics.unrealized_pl`
**Purpose:** Calculate unrealized profit/loss for current positions
**Complexity:** MEDIUM
**Estimated Effort:** 2 hours

**Current Status:** ❌ **NOT in FinancialAnalyst.get_capabilities()**
**Should Be Added To:** `backend/app/agents/financial_analyst.py:95-147`

**Implementation Requirements:**
- Get current positions from `lots` table
- Fetch latest prices from pricing pack
- Calculate: `unrealized_pl = (current_price - cost_basis) * quantity_open`
- Handle multi-currency positions with FX rates

**SQL Query Pattern:**
```sql
SELECT
    l.security_id,
    l.quantity_open,
    l.cost_basis,
    p.close as current_price,
    (p.close - l.cost_basis) * l.quantity_open as unrealized_pl
FROM lots l
JOIN prices p ON l.security_id = p.security_id
WHERE l.portfolio_id = $1
  AND l.quantity_open > 0
  AND p.pricing_pack_id = $2
```

---

### Category 3: Tax Optimization Capabilities (TaxAnalyst Agent)

#### 6. `tax.identify_losses`
**Purpose:** Filter positions with unrealized losses above threshold
**Complexity:** LOW
**Estimated Effort:** 1 hour

**Implementation Requirements:**
- Filter `unrealized_pl` results where `unrealized_pl < -min_loss_threshold`
- Sort by loss magnitude
- Include security details

---

#### 7. `tax.wash_sale_check`
**Purpose:** Check if selling position would create wash sale
**Complexity:** MEDIUM
**Estimated Effort:** 2 hours

**Implementation Requirements:**
- For each loss position, check transaction history
- Look for purchases in 30-day window (before and after today)
- Flag positions with wash sale risk
- Consider pending orders (if system tracks them)

---

#### 8. `tax.calculate_benefit`
**Purpose:** Estimate tax savings from harvesting loss
**Complexity:** LOW
**Estimated Effort:** 1 hour

**Implementation Requirements:**
- Apply tax rate to unrealized loss: `benefit = abs(unrealized_loss) * tax_rate`
- Reduce benefit if wash sale risk exists
- Consider state tax rates (optional)

**Formula:**
```
tax_benefit = abs(unrealized_loss) * marginal_tax_rate
```

**Example:**
```
Unrealized loss: -$5,000
Tax rate: 32%
Tax benefit: $5,000 × 0.32 = $1,600
```

---

#### 9. `tax.rank_opportunities`
**Purpose:** Rank harvesting opportunities by benefit
**Complexity:** LOW
**Estimated Effort:** 1 hour

**Implementation Requirements:**
- Sort positions by `tax_benefit` descending
- Assign priority rank (1 = highest benefit)
- Filter out positions with wash sale risk if `avoid_wash_sales = true`

---

## Implementation Roadmap

### Phase 1: Core Tax Capabilities (8 hours)

**1.1 Create TaxAnalyst Agent** (1 hour)
- File: `backend/app/agents/tax_analyst.py`
- Inherit from `BaseAgent`
- Register 7 tax capabilities
- Set up dependency injection (db, services)

**1.2 Implement Tax Compliance** (7 hours)
- `tax.realized_gains` (4h) - Most complex, lot accounting logic
- `tax.wash_sales` (3h) - IRS rule implementation

### Phase 2: Tax Optimization (5 hours)

**2.1 Add Metrics Capability** (2 hours)
- Add `metrics.unrealized_pl` to FinancialAnalyst
- Update `get_capabilities()` list

**2.2 Implement Harvesting Logic** (3 hours)
- `tax.identify_losses` (1h)
- `tax.wash_sale_check` (1h)
- `tax.calculate_benefit` (0.5h)
- `tax.rank_opportunities` (0.5h)

### Phase 3: Reporting & UI (3 hours)

**3.1 Simple Reporting** (2 hours)
- `tax.lot_details` (1h)
- `tax.summary` (1h)

**3.2 Register TaxAnalyst** (1 hour)
- Update `combined_server.py` to register TaxAnalyst
- Test pattern execution via API
- Verify error handling

**Total Estimated Effort:** 16 hours

---

## Alternative: Stub Implementation (2 hours)

If you want to unblock UI development without full implementation:

### Stub Approach

**Benefits:**
- Patterns become functional immediately
- UI can be built and tested
- Users see placeholder data
- Can iterate on UX before backend complete

**Implementation:**
```python
# backend/app/agents/tax_analyst.py (STUB VERSION)

class TaxAnalyst(BaseAgent):
    """Stub TaxAnalyst for UI development"""

    def get_capabilities(self):
        return [
            "tax.realized_gains",
            "tax.wash_sales",
            "tax.lot_details",
            "tax.summary",
            "tax.identify_losses",
            "tax.wash_sale_check",
            "tax.calculate_benefit",
            "tax.rank_opportunities"
        ]

    async def tax_realized_gains(self, ctx, state, portfolio_id, tax_year, lot_method):
        return {
            "short_term": {"total": 10000.00, "count": 5},
            "long_term": {"total": 25000.00, "count": 3},
            "_provenance": {"type": "stub", "warnings": ["Using placeholder data"]}
        }

    # ... similar stub methods for other capabilities
```

**Effort:** 2 hours to create all 9 stub methods

---

## Database Schema Support

### Existing Tables (Already Support Tax Features)

#### `transactions` Table
```sql
-- Migration 017 added this field:
ALTER TABLE transactions
ADD COLUMN realized_pl NUMERIC(20, 2) DEFAULT NULL;
```
✅ **Ready for tax calculations**

#### `lots` Table
```sql
-- Has all fields needed for lot accounting:
- id UUID
- portfolio_id UUID
- security_id UUID
- quantity_open NUMERIC(20,8)  -- Migration 001 standardized
- quantity_original NUMERIC(20,8)
- acquisition_date DATE
- cost_basis NUMERIC(20,2)
```
✅ **Ready for tax lot tracking**

#### `portfolios` Table
```sql
-- Migration 018 added:
ALTER TABLE portfolios
ADD COLUMN cost_basis_method VARCHAR(20) DEFAULT 'FIFO'
    CHECK (cost_basis_method IN ('FIFO', 'LIFO', 'HIFO', 'SPECIFIC_LOT', 'AVERAGE_COST'));
```
✅ **Ready for lot selection methods**

### No Additional Migrations Needed

All database schema required for tax features already exists thanks to Migrations 017 and 018.

---

## Business Value Analysis

### Revenue Potential: $200K ARR

**Target Market:** RIA/Advisors managing client portfolios

**Value Proposition:**
- Automated tax-loss harvesting (saves clients money)
- IRS Form 1099-B compliant reporting (reduces advisor workload)
- Wash sale detection (prevents compliance violations)
- End-of-year tax planning (competitive differentiator)

**Pricing Model:**
- Premium tier feature: $50/month/portfolio
- 333 portfolios needed for $200K ARR
- Or: $500/month for 10-portfolio advisory firm (40 firms = $200K)

**Competitive Advantage:**
- Most portfolio platforms charge separately for tax reporting
- Integrated tax optimization is rare in sub-$1M platforms
- Real-time wash sale checking is premium feature

### ROI Analysis

**Implementation Cost:**
- 16 hours × $150/hr = $2,400 (full implementation)
- Or: 2 hours × $150/hr = $300 (stub version)

**Time to Revenue:**
- Stub version: 2 hours → UI ready → sales demos enabled
- Full version: 16 hours → production-ready → customer deployments

**Break-even:**
- Need 1-2 customers to cover development cost
- Payback period: <1 month

---

## Testing Requirements

### Unit Tests Needed (5 hours)

**Tax Calculations:**
```python
# tests/test_tax_analyst.py

async def test_realized_gains_fifo():
    """Test FIFO lot selection produces correct gains"""
    # Setup: Portfolio with multiple lots
    # Execute: tax.realized_gains with FIFO
    # Assert: Oldest lots sold first, correct cost basis

async def test_wash_sale_detection():
    """Test wash sale detection within 30-day window"""
    # Setup: Sell at loss on Day 15
    # Setup: Repurchase on Day 35 (no wash sale)
    # Setup: Repurchase on Day 20 (wash sale)
    # Assert: Only Day 20 repurchase flagged

async def test_tax_benefit_calculation():
    """Test tax benefit formula"""
    # Setup: Position with -$5000 unrealized loss
    # Execute: tax.calculate_benefit with tax_rate=0.32
    # Assert: benefit = $1600
```

### Integration Tests (3 hours)

**Pattern Execution:**
```python
async def test_portfolio_tax_report_pattern():
    """Test full portfolio_tax_report pattern"""
    # Execute pattern through orchestrator
    # Verify all 4 steps complete
    # Verify output structure matches schema

async def test_tax_harvesting_pattern():
    """Test full tax_harvesting_opportunities pattern"""
    # Execute pattern through orchestrator
    # Verify 6 steps complete
    # Verify opportunities ranked correctly
```

---

## Current Workarounds

### What Users Can Do Today (Without Tax Features)

**Alternative 1: Manual Export + Excel**
- Export transactions via `/api/transactions`
- Calculate realized gains manually in Excel
- Not scalable, error-prone

**Alternative 2: Third-Party Tax Software**
- Export to TurboTax/TaxAct format
- Requires manual data formatting
- No real-time wash sale checking

**Alternative 3: Accountant Review**
- Send transaction history to CPA
- Expensive ($500-2000/year per portfolio)
- No proactive tax optimization

**Why Built-In Tax Features Matter:**
- Real-time wash sale prevention (avoid $1000s in penalties)
- Proactive tax-loss harvesting (save 20-40% on taxes)
- Automated IRS reporting (save 10-20 hours/year)
- Competitive advantage for advisors (justify fees)

---

## Risk Analysis

### If Tax Patterns Remain Unimplemented

**Technical Risk:** ✅ **LOW**
- Patterns not exposed in UI (no user access)
- Pattern orchestrator handles missing capabilities gracefully
- No impact on existing functionality
- App continues working perfectly

**Business Risk:** ⚠️ **MEDIUM-HIGH**
- Lost revenue opportunity ($200K ARR)
- Competitive disadvantage (competitors offer tax features)
- Cannot pursue RIA/advisor market effectively
- End-of-year 2025 planning opportunity missed

**Compliance Risk:** ✅ **NONE**
- Not advertising tax features
- No user expectations to meet
- No regulatory obligations

### If Implemented with Stubs

**Technical Risk:** ⚠️ **MEDIUM**
- Users see placeholder data (could be confusing)
- Must clearly label as "Preview" or "Coming Soon"
- Need to prevent users from making tax decisions on stub data

**Business Risk:** ✅ **LOW**
- Can demo features to prospects
- UI development unblocked
- Can gather user feedback early

**Compliance Risk:** ⚠️ **MEDIUM**
- Must include disclaimers: "Not for tax filing purposes"
- Cannot advertise as IRS-compliant until real implementation

### If Fully Implemented

**Technical Risk:** ✅ **LOW**
- Well-defined requirements
- Database schema already exists
- Similar patterns already working

**Business Risk:** ✅ **LOW**
- Unlocks $200K ARR potential
- Competitive positioning improved
- Can target Q1 2025 tax planning season

**Compliance Risk:** ⚠️ **MEDIUM**
- Need CPA review of calculations
- Must include tax disclaimers
- Should get legal review of IRS compliance claims

---

## Recommendations

### Option 1: Full Implementation (Recommended)
**Effort:** 16 hours
**Timeline:** 2 days (with testing)
**When:** Before end-of-year 2025 tax planning season
**Why:** Unlocks $200K ARR, competitive advantage, complete feature

### Option 2: Stub Implementation
**Effort:** 2 hours
**Timeline:** Same day
**When:** If UI development is blocked and sales needs demos
**Why:** Unblocks UI work, enables sales conversations, low cost

### Option 3: Remove Patterns (Quick Clean-Up)
**Effort:** 30 minutes
**Timeline:** Immediate
**When:** If tax features deprioritized for 6+ months
**Why:** Reduces confusion, cleaner codebase, clear roadmap

### Option 4: Do Nothing (Current State)
**Effort:** 0 hours
**Timeline:** N/A
**When:** If other priorities are higher
**Why:** App works fine, no user impact, defer to later sprint

---

## Next Steps (If Proceeding with Implementation)

1. **Review & Approve** this architecture document
2. **Decide:** Full implementation vs stub vs remove
3. **Create** `backend/app/agents/tax_analyst.py`
4. **Implement** capabilities in priority order:
   - Start with `tax.realized_gains` (hardest, most value)
   - Add `metrics.unrealized_pl` to FinancialAnalyst
   - Implement wash sale detection
   - Add harvesting optimization logic
5. **Test** with real portfolio data
6. **Get CPA review** of tax calculations
7. **Add disclaimers** to UI
8. **Deploy** to production

---

**Document Status:** Complete - Ready for Decision
**Author:** Claude Code IDE Agent
**Created:** January 14, 2025
**Last Updated:** January 14, 2025
