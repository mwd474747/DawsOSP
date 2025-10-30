# Beancount Integration & Performance Calculation Analysis

## Executive Summary
**Beancount is NOT actively in use** in the current DawsOS implementation. While comprehensive Beancount integration code exists in the codebase, it is **not installed, not configured, and not being executed**. Performance calculations are currently using **placeholder/mock values** rather than actual financial calculations.

---

## 1. Beancount Integration Status

### Code Exists But Not Active
- **Location**: `backend/app/services/ledger.py` and `backend/jobs/reconcile_ledger.py`
- **Status**: Code written but NOT operational
- **Evidence**: 
  - Beancount package is not installed (`pip list | grep bean` returns empty)
  - No Beancount files detected in the filesystem
  - No ledger parsing jobs running
  - BEANCOUNT_AVAILABLE flag defaults to False

### Intended Architecture (Not Implemented)
```
Git Repo with Beancount Files → Parser → Database → NAV Calculation → Reconciliation
                                   ↓
                             Immutable Ledger
                                Snapshots
                                   ↓
                           ±1bp Reconciliation
                              Tolerance
```

### Key Components (Written but Unused)
1. **LedgerService** (`backend/app/services/ledger.py`):
   - Parse Beancount ledger files
   - Extract transactions and postings
   - Store snapshots with git commit hash provenance
   - Calculate NAV from ledger positions

2. **ReconciliationService** (`backend/jobs/reconcile_ledger.py`):
   - Compare ledger NAV vs database NAV
   - ±1 basis point tolerance validation
   - Generate reconciliation reports
   - Alert on discrepancies

3. **Database Tables (Exist but Empty)**:
   - `ledger_snapshots` - Would store parsed ledger state
   - `ledger_transactions` - Would store individual transactions
   - `reconciliation_results` - Would store NAV comparisons

---

## 2. Current Performance Calculation

### Reality: Hardcoded Placeholder Values

The current implementation **does NOT calculate real performance**. Instead, it uses:

#### Portfolio Risk Metrics (`combined_server.py` lines 509-557)
```python
def calculate_portfolio_risk_metrics(holdings):
    # ...
    # Placeholder values - NOT REAL CALCULATIONS
    sharpe_ratio = 0.8  # Hardcoded!
    max_drawdown = -0.08  # Hardcoded!
    var_95 = total_value * 0.02  # Simple 2% of portfolio value
    
    # Only weighted beta is actually calculated
    portfolio_beta = weighted average of holding betas
    portfolio_volatility = beta * 0.15  # Assumes 15% market volatility
```

#### Missing Performance Metrics
The API returns these fields but **they don't exist in calculations**:
- `unrealized_pnl` - Not calculated anywhere
- `returns_1d` - Not calculated
- `returns_ytd` - Not calculated
- `returns_mtd` - Not calculated

The frontend handles this by defaulting missing values to 0.

---

## 3. Designed but Unimplemented Performance Calculations

### Time-Weighted Return (TWR) - Code Exists, Not Used
**Location**: `backend/jobs/metrics.py` lines 507-600

Intended Formula:
```
TWR = (1+r₁) × (1+r₂) × ... × (1+rₙ) - 1
```

Features if implemented:
- Daily return geometric linking
- Period calculations (1D, MTD, QTD, YTD, 1Y, 3Y, 5Y)
- Annualized long-term returns
- Cash flow independent

**Current Status**: Function exists but is never called. No daily returns are being stored.

### Money-Weighted Return (MWR/IRR) - Placeholder Only
**Location**: `backend/jobs/metrics.py` lines 602-613

```python
def _compute_mwr_metrics(self, ...):
    # TODO: Implement IRR calculation
    # Returns hardcoded zeros
    return {
        "mwr_ytd": Decimal("0.0"),
        "mwr_1y": Decimal("0.0"),
        "mwr_3y_ann": Decimal("0.0"),
        "mwr_inception_ann": Decimal("0.0"),
    }
```

**Status**: Completely unimplemented. Returns zeros.

---

## 4. Data Flow Reality vs. Design

### Designed Flow (Not Active)
```
External APIs → Pricing Packs → Portfolio Metrics → TWR/MWR Calculation
       ↓              ↓                ↓                    ↓
   FRED/Polygon   Immutable      Stored in DB      Performance Metrics
                   Snapshots
```

### Actual Current Flow
```
Mock Data Generator → Hardcoded Values → API Response
         ↓                   ↓               ↓
   Random Holdings      Sharpe=0.8      No Real Returns
```

---

## 5. Critical Findings

### What's Actually Working
1. **Authentication**: JWT tokens functioning
2. **Database Structure**: Tables exist and are well-designed
3. **API Endpoints**: Properly structured and returning data
4. **Frontend Display**: Shows data gracefully with fallbacks

### What's NOT Working
1. **No Real Performance Calculation**: All returns are missing or zero
2. **No Beancount Integration**: Despite extensive code, Beancount is not installed or configured
3. **No Pricing Pack System**: The immutable pricing pack architecture is not operational
4. **No Transaction History**: No real trades being tracked
5. **No Reconciliation**: The ±1bp reconciliation system is inactive

### Risk Metrics Status
| Metric | Status | Implementation |
|--------|--------|----------------|
| Portfolio Beta | ✅ Calculated | Weighted average of holdings |
| Portfolio Volatility | ⚠️ Estimated | Beta × 0.15 assumption |
| Sharpe Ratio | ❌ Hardcoded | Always returns 0.8 |
| Max Drawdown | ❌ Hardcoded | Always returns -8% |
| VaR (95%) | ⚠️ Simplified | 2% of portfolio value |
| TWR | ❌ Not Calculated | Function exists, not called |
| MWR | ❌ Not Calculated | Returns zeros |

---

## 6. Why Beancount Integration Failed to Launch

### Missing Prerequisites
1. **No Beancount Installation**: Package never installed
2. **No Ledger Files**: No `.beancount` files in the system
3. **No Git Repository**: Ledger repo path doesn't exist
4. **No Scheduled Jobs**: Reconciliation jobs not scheduled
5. **No Pricing Packs**: The pricing pack build job isn't running

### Architectural Complexity
The designed system is sophisticated but requires:
- Git repository with Beancount files as source of truth
- Nightly pricing pack builds from external APIs
- Complex reconciliation logic
- Multiple background jobs coordinating

---

## 7. Recommendations

### For Immediate Functionality
1. **Option A: Implement Simple Performance Tracking**
   - Store daily NAVs in database
   - Calculate actual TWR from NAV series
   - Implement basic return calculations

2. **Option B: Activate Mock Performance**
   - Generate realistic return patterns
   - Calculate Sharpe from mock returns
   - Simulate drawdowns

### For Full Beancount Integration
1. Install Beancount: `pip install beancount`
2. Create sample ledger files
3. Configure ledger repository path
4. Schedule reconciliation jobs
5. Implement pricing pack builds

### For Production Use
1. **Remove Placeholder Values**: Don't show fake Sharpe ratios
2. **Implement Real Calculations**: At minimum, calculate returns from price changes
3. **Add Transaction Tracking**: Store actual trades, not just holdings
4. **Build Performance History**: Need time series data for meaningful metrics

---

## 8. Conclusion

The DawsOS platform has an **ambitious but unimplemented** Beancount-based architecture. The current system shows the UI and API structure of a sophisticated portfolio management platform but **lacks the computational engine** to calculate actual performance metrics.

The codebase reveals a two-tier design:
1. **Tier 1** (Active): Basic portfolio display with mock data
2. **Tier 2** (Inactive): Sophisticated Beancount ledger reconciliation system

Currently operating at Tier 1 with hardcoded values masquerading as financial calculations. The Beancount integration represents significant engineering effort that was never activated.

**Bottom Line**: Performance is not being calculated at all. The system displays static placeholder values (Sharpe = 0.8, Drawdown = -8%) regardless of actual portfolio composition or market movements.