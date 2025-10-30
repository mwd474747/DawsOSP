# Simulating Beancount Portfolio Replacement - Impact Analysis

## Executive Summary
Replacing current portfolio functions with Beancount would fundamentally transform DawsOS from a **position-tracking system** to a **double-entry accounting system**. This would impact every layer of the architecture, changing data flow from API-driven to ledger-driven, and shifting from mutable database state to immutable ledger truth.

---

## 1. Current Architecture vs. Beancount Architecture

### Current System (Database-Centric)
```
API Data → Database (Mutable) → Calculations → Display
   ↓            ↓                    ↓           ↓
Polygon    PostgreSQL          Hardcoded    Frontend
Prices     Holdings            Metrics      Shows Data
```

### With Beancount (Ledger-Centric)
```
Ledger Files → Parser → Immutable Snapshots → Calculations → Display
     ↓           ↓              ↓                  ↓           ↓
  Git Repo   Beancount    Database Cache    Real Metrics   Frontend
  (Truth)     Engine      (Derivative)      from History   Shows Truth
```

---

## 2. Data Flow Transformation

### Current Data Flow
```python
# Current: Pull latest prices and multiply
async def get_portfolio():
    holdings = db.fetch("SELECT * FROM lots")
    prices = fetch_latest_prices()
    total_value = sum(h.quantity * prices[h.symbol])
    return {"value": total_value, "sharpe": 0.8}  # Fake metrics
```

### Beancount Data Flow
```python
# Beancount: Parse ledger, apply prices, calculate from history
async def get_portfolio():
    ledger = parse_beancount_file("portfolio.beancount")
    positions = ledger.get_holdings_at_date(date.today())
    prices = pricing_pack.get_prices(date.today())
    
    # Real calculations from transaction history
    nav_series = calculate_nav_series(ledger, pricing_packs)
    returns = calculate_returns(nav_series)
    sharpe = calculate_sharpe_ratio(returns)
    
    return {"value": nav, "sharpe": sharpe}  # Real metrics!
```

---

## 3. File System Changes

### New Directory Structure Required
```
/ledger/
├── main.beancount          # Main ledger file
├── accounts.beancount      # Account definitions
├── commodities.beancount   # Security definitions
├── prices/
│   ├── 2025-01.beancount  # Monthly price files
│   └── 2025-02.beancount
└── transactions/
    ├── trades.beancount    # Buy/Sell transactions
    └── dividends.beancount # Income transactions
```

### Sample Beancount Ledger Entry
```beancount
; main.beancount
include "accounts.beancount"
include "commodities.beancount"
include "transactions/*.beancount"
include "prices/*.beancount"

; Account Definitions
2025-01-01 open Assets:Portfolio:Stocks
2025-01-01 open Assets:Cash:USD
2025-01-01 open Income:Dividends
2025-01-01 open Expenses:Fees

; Transaction Example
2025-01-15 * "Buy AAPL"
  Assets:Portfolio:Stocks    100 AAPL {150.00 USD}
  Assets:Cash:USD         -15000.00 USD

2025-02-01 * "AAPL Dividend"
  Assets:Cash:USD             63.00 USD
  Income:Dividends           -63.00 USD

; Price Entry
2025-10-30 price AAPL 185.00 USD
```

---

## 4. Database Schema Impact

### Tables That Become Obsolete
```sql
-- These would be REPLACED by ledger
DROP TABLE lots;           -- Ledger tracks positions
DROP TABLE transactions;   -- Ledger is transaction source
DROP TABLE holdings;       -- Calculated from ledger
```

### New Tables Required
```sql
-- Cache tables for performance
CREATE TABLE ledger_cache (
    date DATE,
    account TEXT,
    commodity TEXT,
    quantity DECIMAL,
    cost_basis DECIMAL,
    market_value DECIMAL,
    PRIMARY KEY (date, account, commodity)
);

CREATE TABLE nav_timeseries (
    portfolio_id UUID,
    date DATE,
    nav DECIMAL,
    cash_flow DECIMAL,
    PRIMARY KEY (portfolio_id, date)
);

CREATE TABLE return_cache (
    portfolio_id UUID,
    date DATE,
    twr_1d DECIMAL,
    mwr_1d DECIMAL,
    PRIMARY KEY (portfolio_id, date)
);
```

---

## 5. API Endpoint Changes

### Current Endpoints (Would Change)
```python
# BEFORE: Direct database queries
@app.get("/api/portfolio")
async def get_portfolio():
    return db.fetch("SELECT * FROM holdings")

@app.post("/api/transactions")
async def add_transaction(trade: TradeModel):
    db.insert("transactions", trade)  # Direct DB write
```

### Beancount-Based Endpoints
```python
# AFTER: Ledger as source of truth
@app.get("/api/portfolio")
async def get_portfolio():
    ledger = await ledger_service.get_latest_snapshot()
    holdings = ledger.compute_holdings(date.today())
    return holdings

@app.post("/api/transactions")
async def add_transaction(trade: TradeModel):
    # Generate Beancount entry
    entry = f"""
    {trade.date} * "{trade.description}"
      Assets:Portfolio:Stocks  {trade.quantity} {trade.symbol} {{{trade.price} USD}}
      Assets:Cash:USD  {-trade.total} USD
    """
    
    # Append to ledger file
    await ledger_service.append_transaction(entry)
    
    # Commit to git
    await git_service.commit(f"Trade: {trade.symbol} x{trade.quantity}")
    
    # Trigger reconciliation
    await reconciliation_service.reconcile()
```

---

## 6. Performance Calculation Changes

### Current (Fake) Calculations
```python
def calculate_portfolio_risk_metrics(holdings):
    # Everything is hardcoded!
    return {
        "sharpe_ratio": 0.8,      # Always 0.8
        "max_drawdown": -0.08,     # Always -8%
        "var_95": value * 0.02     # Always 2%
    }
```

### With Beancount (Real) Calculations
```python
async def calculate_portfolio_metrics(ledger):
    # Build NAV timeseries from ledger
    nav_series = []
    for date in date_range(inception, today):
        holdings = ledger.get_holdings_at_date(date)
        prices = pricing_pack.get_prices(date)
        nav = sum(h.quantity * prices[h.commodity] for h in holdings)
        nav_series.append((date, nav))
    
    # Calculate real returns
    returns = []
    for i in range(1, len(nav_series)):
        r = (nav_series[i][1] - nav_series[i-1][1]) / nav_series[i-1][1]
        returns.append(r)
    
    # Real Sharpe ratio
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    sharpe = (mean_return - risk_free_rate) / std_return
    
    # Real maximum drawdown
    peak = nav_series[0][1]
    max_dd = 0
    for date, nav in nav_series:
        peak = max(peak, nav)
        drawdown = (nav - peak) / peak
        max_dd = min(max_dd, drawdown)
    
    # Real VaR from historical returns
    var_95 = np.percentile(returns, 5) * current_nav
    
    return {
        "sharpe_ratio": sharpe,     # Actual Sharpe!
        "max_drawdown": max_dd,      # Actual drawdown!
        "var_95": var_95            # Actual VaR!
    }
```

---

## 7. Reconciliation System Activation

### Current State
```python
# No reconciliation - database is truth
holdings = db.fetch("SELECT * FROM holdings")
# Trust it blindly
```

### With Beancount
```python
async def nightly_reconciliation():
    """Run every night at midnight"""
    
    # 1. Parse ledger (source of truth)
    ledger = parse_beancount_file("main.beancount")
    ledger_nav = ledger.compute_nav(date.today())
    
    # 2. Calculate database NAV
    db_holdings = await db.fetch("SELECT * FROM cached_positions")
    db_nav = sum(h.quantity * h.price for h in db_holdings)
    
    # 3. Compare with ±1bp tolerance
    difference = abs(ledger_nav - db_nav)
    error_bps = (difference / ledger_nav) * 10000
    
    if error_bps > 1.0:
        # CRITICAL: Reconciliation failed!
        await alert_service.send_critical(
            f"Reconciliation FAILED: {error_bps:.2f} bps error"
        )
        
        # Rebuild cache from ledger
        await rebuild_cache_from_ledger()
    
    # 4. Store result
    await db.insert("reconciliation_results", {
        "date": date.today(),
        "ledger_nav": ledger_nav,
        "db_nav": db_nav,
        "error_bps": error_bps,
        "status": "PASS" if error_bps <= 1.0 else "FAIL"
    })
```

---

## 8. Frontend Impact

### Minimal Frontend Changes
```javascript
// Frontend mostly unchanged - still calls same APIs
async function loadPortfolioData() {
    const response = await fetch('/api/portfolio');
    const data = await response.json();
    
    // But now data contains REAL metrics!
    displayMetrics({
        sharpe: data.sharpe_ratio,  // Real Sharpe, not 0.8
        drawdown: data.max_drawdown, // Real DD, not -0.08
        returns: data.returns        // Real returns, not 0
    });
}
```

### New Features Possible
```javascript
// Could add ledger-specific features
async function viewLedgerEntry(transactionId) {
    // Show actual Beancount entry
    const entry = await fetch(`/api/ledger/transaction/${transactionId}`);
    displayBeancount(entry.beancount_text);
}

async function auditTrail() {
    // Show git history of ledger changes
    const history = await fetch('/api/ledger/history');
    displayCommits(history.commits);
}
```

---

## 9. Benefits of Beancount Migration

### Data Integrity
- **Immutable ledger** as source of truth
- **Git history** for complete audit trail
- **Double-entry** guarantees balanced books
- **±1bp reconciliation** ensures accuracy

### Real Performance Metrics
- **Actual TWR** from transaction history
- **Real Sharpe** from return volatility
- **True drawdowns** from peak-to-trough
- **Accurate VaR** from historical distribution

### Professional Features
- **Multi-currency** with proper FX accounting
- **Tax lots** with FIFO/LIFO/Specific ID
- **Corporate actions** (splits, dividends) handled correctly
- **Cost basis tracking** for tax reporting

---

## 10. Challenges & Risks

### Implementation Complexity
| Component | Effort | Risk |
|-----------|--------|------|
| Beancount Parser Setup | Medium | Parse errors on complex transactions |
| Git Integration | Medium | Merge conflicts in concurrent updates |
| Migration of Existing Data | High | Data loss if not mapped correctly |
| Reconciliation System | High | False positives/negatives |
| Performance (Speed) | High | Parsing ledger is slower than DB queries |

### Operational Changes
1. **Transaction Entry**: Must generate valid Beancount syntax
2. **Price Updates**: Need daily price entries in ledger
3. **Backup Strategy**: Must backup git repo, not just database
4. **User Training**: Staff must understand double-entry

---

## 11. Migration Path Simulation

### Phase 1: Parallel Run (1 month)
```python
# Keep existing system, add Beancount in parallel
async def get_portfolio():
    db_result = await get_portfolio_from_db()       # Current
    ledger_result = await get_portfolio_from_ledger() # New
    
    # Log differences for analysis
    log_reconciliation(db_result, ledger_result)
    
    return db_result  # Still return DB version
```

### Phase 2: Shadow Mode (1 month)
```python
# Use Beancount but fall back to DB
async def get_portfolio():
    try:
        return await get_portfolio_from_ledger()  # Try ledger first
    except Exception as e:
        log_error(f"Ledger failed: {e}")
        return await get_portfolio_from_db()      # Fallback
```

### Phase 3: Cutover (1 week)
```python
# Full Beancount, no fallback
async def get_portfolio():
    return await get_portfolio_from_ledger()  # Ledger only!
```

---

## 12. Performance Impact

### Query Performance
| Operation | Current (DB) | Beancount | Impact |
|-----------|-------------|-----------|---------|
| Get Holdings | 5ms | 50ms | 10x slower |
| Add Transaction | 10ms | 100ms | 10x slower |
| Calculate NAV | 20ms | 200ms | 10x slower |
| Full Reconciliation | N/A | 5 seconds | New overhead |

### Mitigation Strategies
1. **Aggressive Caching**: Cache parsed ledger in memory
2. **Incremental Parsing**: Only parse new transactions
3. **Background Processing**: Parse asynchronously
4. **Database Cache**: Maintain DB cache for reads

---

## 13. Code Architecture Changes

### Service Layer Transformation
```python
# BEFORE: Direct database service
class PortfolioService:
    async def get_holdings(self):
        return await db.fetch("SELECT * FROM holdings")

# AFTER: Ledger-based service
class PortfolioService:
    def __init__(self):
        self.ledger_service = LedgerService()
        self.cache_service = CacheService()
    
    async def get_holdings(self):
        # Check cache first
        cached = await self.cache_service.get_holdings()
        if cached and not self._is_stale(cached):
            return cached
        
        # Parse ledger if cache miss/stale
        ledger = await self.ledger_service.parse()
        holdings = ledger.compute_holdings()
        
        # Update cache
        await self.cache_service.set_holdings(holdings)
        
        return holdings
```

---

## 14. Final State Architecture

```
┌──────────────────────────────────────────────────────┐
│                    User Interface                      │
└────────────────────┬───────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼───────────────────────────────────┐
│                  API Layer (FastAPI)                    │
│  - Auth  - Portfolio  - Transactions  - Reconciliation │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────┐
│               Service Layer                             │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │LedgerService│ │CacheService  │ │ReconcileService│  │
│  └─────┬───────┘ └──────┬───────┘ └────────┬───────┘  │
└────────┼────────────────┼──────────────────┼──────────┘
         │                │                  │
┌────────▼────────┐ ┌─────▼──────┐ ┌────────▼───────────┐
│  Beancount      │ │PostgreSQL  │ │  Pricing Packs     │
│  Ledger Files   │ │   Cache    │ │  (Immutable)       │
│  (Git Repo)     │ │            │ │                    │
└─────────────────┘ └────────────┘ └────────────────────┘
         ↑                               ↑
         └───────────────────────────────┘
            Reconciliation (±1bp nightly)
```

---

## Conclusion

Replacing portfolio functions with Beancount would:

1. **Transform the data model** from mutable database to immutable ledger
2. **Enable real performance calculations** replacing all hardcoded values
3. **Add operational complexity** but ensure data integrity
4. **Slow down real-time queries** but provide audit trail
5. **Require significant migration effort** but deliver professional-grade accuracy

The system would shift from a **web application with a database** to a **financial accounting system with a web interface**. This is a fundamental architectural change that would make DawsOS a true institutional-grade portfolio management platform.