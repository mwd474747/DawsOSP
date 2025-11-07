# Tax Capabilities Implementation Assessment

**Date:** January 14, 2025  
**Status:** 🔍 **ASSESSMENT COMPLETE**  
**Purpose:** Assess work required to implement 10 missing tax capabilities

---

## Executive Summary

**Total Missing Capabilities:** 10  
**Estimated Total Work:** 3-4 days (24-32 hours)  
**Complexity:** Medium to High  
**Dependencies:** Database schema ready, core logic exists

**Existing Infrastructure:**
- ✅ `transactions` table has `realized_pl` field (Migration 017)
- ✅ `trade_execution.py` already calculates realized P&L
- ✅ `lots` table has all lot tracking fields (`quantity_open`, `quantity_original`, `cost_basis`, `acquisition_date`, `closed_date`)
- ✅ Unrealized P&L calculation exists in `financial_analyst.py`
- ✅ Lot selection methods (FIFO, LIFO, HIFO, SPECIFIC) implemented in `trade_execution.py`

**Missing Infrastructure:**
- ❌ Wash sale detection logic (30-day window check)
- ❌ Tax year aggregation queries
- ❌ Tax benefit calculation formulas
- ❌ Tax summary report generation

---

## Detailed Capability Assessment

### Pattern 1: `tax_harvesting_opportunities.json`

#### 1.1 `metrics.unrealized_pl` (MEDIUM - 2-3 hours)

**Purpose:** Calculate unrealized P&L for current positions.

**Current State:**
- ✅ Unrealized P&L already calculated in `financial_analyst.py` (line 500, 1663)
- ✅ Formula: `unrealized_pnl = market_value - cost_basis`
- ✅ Already returned in `portfolio_get_valued_positions` and `get_position_details`

**What's Needed:**
- Create capability method `metrics_unrealized_pl` in `FinancialAnalyst`
- Accept `positions` list (from `ledger.positions`)
- Calculate unrealized P&L for each position
- Return aggregated summary

**Implementation:**
```python
@capability(
    name="metrics.unrealized_pl",
    inputs={"positions": list},
    outputs={"unrealized_pl": dict, "total_unrealized_pl": float},
    description="Calculate unrealized P&L for positions"
)
async def metrics_unrealized_pl(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    positions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate unrealized P&L for positions."""
    # Extract positions from input (may be nested)
    if isinstance(positions, dict) and "positions" in positions:
        positions = positions["positions"]
    
    total_unrealized_pl = Decimal("0")
    by_symbol = {}
    
    for pos in positions:
        symbol = pos.get("symbol")
        cost_basis = Decimal(str(pos.get("cost_basis", 0)))
        market_value = Decimal(str(pos.get("market_value", 0)))
        unrealized_pl = market_value - cost_basis
        
        by_symbol[symbol] = {
            "symbol": symbol,
            "cost_basis": float(cost_basis),
            "market_value": float(market_value),
            "unrealized_pl": float(unrealized_pl),
            "unrealized_pl_pct": float((unrealized_pl / cost_basis * 100) if cost_basis > 0 else 0)
        }
        total_unrealized_pl += unrealized_pl
    
    return {
        "unrealized_pl": by_symbol,
        "total_unrealized_pl": float(total_unrealized_pl),
        "position_count": len(positions)
    }
```

**Work Estimate:** 2-3 hours (mostly wrapping existing logic)

---

#### 1.2 `tax.identify_losses` (MEDIUM - 2-3 hours)

**Purpose:** Identify positions with unrealized losses above threshold.

**Current State:**
- ✅ Unrealized P&L calculation exists
- ❌ No filtering by loss threshold

**What's Needed:**
- Filter positions with `unrealized_pl < 0`
- Filter by `min_loss` threshold
- Return loss positions with metadata

**Implementation:**
```python
@capability(
    name="tax.identify_losses",
    inputs={"positions": list, "unrealized_pl": dict, "min_loss": float},
    outputs={"loss_positions": list},
    description="Identify positions with unrealized losses"
)
async def tax_identify_losses(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    positions: List[Dict[str, Any]],
    unrealized_pl: Dict[str, Any],
    min_loss: float = 1000.0,
) -> Dict[str, Any]:
    """Identify positions with unrealized losses above threshold."""
    # Extract positions
    if isinstance(positions, dict) and "positions" in positions:
        positions = positions["positions"]
    
    # Extract unrealized P&L data
    if isinstance(unrealized_pl, dict) and "unrealized_pl" in unrealized_pl:
        unrealized_pl_data = unrealized_pl["unrealized_pl"]
    else:
        unrealized_pl_data = unrealized_pl
    
    loss_positions = []
    for pos in positions:
        symbol = pos.get("symbol")
        pl_data = unrealized_pl_data.get(symbol, {})
        unrealized_pl_value = pl_data.get("unrealized_pl", 0)
        
        # Filter for losses above threshold
        if unrealized_pl_value < 0 and abs(unrealized_pl_value) >= min_loss:
            loss_positions.append({
                "symbol": symbol,
                "security_id": pos.get("security_id"),
                "quantity": pos.get("quantity"),
                "cost_basis": pos.get("cost_basis"),
                "market_value": pos.get("market_value"),
                "unrealized_pl": unrealized_pl_value,
                "unrealized_pl_pct": pl_data.get("unrealized_pl_pct", 0),
                "acquisition_date": pos.get("acquisition_date"),
            })
    
    # Sort by loss amount (largest losses first)
    loss_positions.sort(key=lambda x: x["unrealized_pl"])
    
    return {
        "loss_positions": loss_positions,
        "total_loss_count": len(loss_positions),
        "total_loss_amount": sum(p["unrealized_pl"] for p in loss_positions)
    }
```

**Work Estimate:** 2-3 hours (filtering and sorting logic)

---

#### 1.3 `tax.wash_sale_check` (HIGH - 4-6 hours)

**Purpose:** Check if selling loss positions would create wash sale violations.

**Current State:**
- ❌ No wash sale detection logic exists
- ✅ `transactions` table has `transaction_date` field
- ✅ `lots` table has `acquisition_date` and `closed_date` fields

**What's Needed:**
- Query transactions for same symbol within 30 days before/after proposed sale
- Check for "substantially identical" securities (same symbol)
- Return wash sale risks with dates and amounts

**Implementation:**
```python
@capability(
    name="tax.wash_sale_check",
    inputs={"portfolio_id": str, "positions": list},
    outputs={"wash_sale_risks": list},
    description="Check for wash sale violations"
)
async def tax_wash_sale_check(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: str,
    positions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Check if selling loss positions would create wash sale violations."""
    portfolio_uuid = self._to_uuid(portfolio_id, "portfolio_id")
    
    # Extract positions
    if isinstance(positions, dict) and "loss_positions" in positions:
        positions = positions["loss_positions"]
    elif isinstance(positions, list):
        positions = positions
    else:
        positions = []
    
    db_pool = self.services.get("db")
    if not db_pool:
        raise RuntimeError("Database pool not available")
    
    wash_sale_risks = []
    
    async with db_pool.acquire() as conn:
        for pos in positions:
            symbol = pos.get("symbol")
            acquisition_date = pos.get("acquisition_date")
            
            if not acquisition_date:
                continue
            
            # Check for transactions within 30 days before/after acquisition
            # Wash sale rule: Cannot claim loss if repurchase within 30 days
            from datetime import timedelta
            
            check_start = acquisition_date - timedelta(days=30)
            check_end = acquisition_date + timedelta(days=30)
            
            # Check for BUY transactions within 30-day window
            buy_transactions = await conn.fetch(
                """
                SELECT transaction_date, quantity, price, amount
                FROM transactions
                WHERE portfolio_id = $1
                  AND symbol = $2
                  AND transaction_type = 'BUY'
                  AND transaction_date BETWEEN $3 AND $4
                ORDER BY transaction_date
                """,
                portfolio_uuid,
                symbol,
                check_start,
                check_end,
            )
            
            if buy_transactions:
                wash_sale_risks.append({
                    "symbol": symbol,
                    "acquisition_date": str(acquisition_date),
                    "risk_type": "wash_sale",
                    "risk_reason": f"BUY transaction within 30 days of acquisition",
                    "transactions": [
                        {
                            "date": str(t["transaction_date"]),
                            "quantity": float(t["quantity"]),
                            "price": float(t["price"]),
                        }
                        for t in buy_transactions
                    ],
                    "days_until_safe": max(30 - (acquisition_date - buy_transactions[-1]["transaction_date"]).days, 0)
                })
    
    return {
        "wash_sale_risks": wash_sale_risks,
        "total_risks": len(wash_sale_risks),
        "safe_positions": len(positions) - len(wash_sale_risks)
    }
```

**Work Estimate:** 4-6 hours (complex logic, requires careful date calculations)

---

#### 1.4 `tax.calculate_benefit` (MEDIUM - 2-3 hours)

**Purpose:** Calculate tax benefit from harvesting losses.

**Current State:**
- ❌ No tax benefit calculation exists

**What's Needed:**
- Calculate tax savings: `loss_amount × tax_rate`
- Account for wash sale disallowances
- Return benefit breakdown

**Implementation:**
```python
@capability(
    name="tax.calculate_benefit",
    inputs={"loss_positions": list, "tax_rate": float, "wash_sale_risks": list},
    outputs={"tax_benefits": dict},
    description="Calculate tax benefit from harvesting losses"
)
async def tax_calculate_benefit(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    loss_positions: List[Dict[str, Any]],
    tax_rate: float = 0.32,
    wash_sale_risks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Calculate tax benefit from harvesting losses."""
    # Extract positions
    if isinstance(loss_positions, dict) and "loss_positions" in loss_positions:
        positions = loss_positions["loss_positions"]
    elif isinstance(loss_positions, list):
        positions = loss_positions
    else:
        positions = []
    
    # Extract wash sale risks
    if isinstance(wash_sale_risks, dict) and "wash_sale_risks" in wash_sale_risks:
        risks = wash_sale_risks["wash_sale_risks"]
    elif isinstance(wash_sale_risks, list):
        risks = wash_sale_risks
    else:
        risks = []
    
    # Create risk lookup
    risk_symbols = {r["symbol"] for r in risks}
    
    total_loss = Decimal("0")
    total_benefit = Decimal("0")
    by_symbol = {}
    
    for pos in positions:
        symbol = pos.get("symbol")
        loss_amount = abs(Decimal(str(pos.get("unrealized_pl", 0))))
        
        # Check if wash sale risk exists
        has_wash_sale_risk = symbol in risk_symbols
        
        # Calculate benefit (loss × tax_rate)
        benefit = loss_amount * Decimal(str(tax_rate))
        
        # If wash sale risk, benefit is reduced (loss may be disallowed)
        if has_wash_sale_risk:
            benefit = benefit * Decimal("0.5")  # Assume 50% disallowance
        
        by_symbol[symbol] = {
            "symbol": symbol,
            "loss_amount": float(loss_amount),
            "tax_rate": tax_rate,
            "benefit": float(benefit),
            "has_wash_sale_risk": has_wash_sale_risk,
        }
        
        total_loss += loss_amount
        total_benefit += benefit
    
    return {
        "tax_benefits": by_symbol,
        "total_loss": float(total_loss),
        "total_benefit": float(total_benefit),
        "effective_tax_rate": float(total_benefit / total_loss) if total_loss > 0 else 0,
        "positions_with_benefit": len(by_symbol),
        "positions_with_wash_sale_risk": len([s for s in by_symbol.values() if s["has_wash_sale_risk"]])
    }
```

**Work Estimate:** 2-3 hours (straightforward calculation)

---

#### 1.5 `tax.rank_opportunities` (LOW - 1-2 hours)

**Purpose:** Rank tax harvesting opportunities by benefit.

**Current State:**
- ❌ No ranking logic exists

**What's Needed:**
- Sort positions by tax benefit
- Include metadata (loss amount, wash sale risk, etc.)

**Implementation:**
```python
@capability(
    name="tax.rank_opportunities",
    inputs={"positions": list, "benefits": dict},
    outputs={"opportunities": list},
    description="Rank tax harvesting opportunities by benefit"
)
async def tax_rank_opportunities(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    positions: List[Dict[str, Any]],
    benefits: Dict[str, Any],
) -> Dict[str, Any]:
    """Rank tax harvesting opportunities by benefit."""
    # Extract positions
    if isinstance(positions, dict) and "loss_positions" in positions:
        positions = positions["loss_positions"]
    elif isinstance(positions, list):
        positions = positions
    else:
        positions = []
    
    # Extract benefits
    if isinstance(benefits, dict) and "tax_benefits" in benefits:
        benefits_data = benefits["tax_benefits"]
    else:
        benefits_data = benefits
    
    # Combine positions with benefits
    opportunities = []
    for pos in positions:
        symbol = pos.get("symbol")
        benefit_data = benefits_data.get(symbol, {})
        
        opportunities.append({
            "symbol": symbol,
            "security_id": pos.get("security_id"),
            "loss_amount": pos.get("unrealized_pl", 0),
            "tax_benefit": benefit_data.get("benefit", 0),
            "has_wash_sale_risk": benefit_data.get("has_wash_sale_risk", False),
            "quantity": pos.get("quantity"),
            "cost_basis": pos.get("cost_basis"),
            "market_value": pos.get("market_value"),
            "acquisition_date": pos.get("acquisition_date"),
        })
    
    # Sort by tax benefit (highest first)
    opportunities.sort(key=lambda x: x["tax_benefit"], reverse=True)
    
    # Add rank
    for i, opp in enumerate(opportunities, 1):
        opp["rank"] = i
    
    return {
        "opportunities": opportunities,
        "total_opportunities": len(opportunities),
        "total_benefit": sum(o["tax_benefit"] for o in opportunities)
    }
```

**Work Estimate:** 1-2 hours (simple sorting and ranking)

---

### Pattern 2: `portfolio_tax_report.json`

#### 2.1 `tax.realized_gains` (MEDIUM - 3-4 hours)

**Purpose:** Calculate realized gains/losses by tax year.

**Current State:**
- ✅ `transactions` table has `realized_pl` field (Migration 017)
- ✅ `trade_execution.py` already calculates realized P&L
- ❌ No aggregation by tax year

**What's Needed:**
- Query `transactions` table for SELL transactions in tax year
- Group by symbol and lot selection method
- Calculate short-term vs long-term gains
- Return realized gains summary

**Implementation:**
```python
@capability(
    name="tax.realized_gains",
    inputs={"portfolio_id": str, "tax_year": int, "lot_method": str},
    outputs={"realized_gains": dict},
    description="Calculate realized gains by tax year"
)
async def tax_realized_gains(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: str,
    tax_year: int = 2025,
    lot_method: str = "fifo",
) -> Dict[str, Any]:
    """Calculate realized gains/losses by tax year."""
    portfolio_uuid = self._to_uuid(portfolio_id, "portfolio_id")
    
    db_pool = self.services.get("db")
    if not db_pool:
        raise RuntimeError("Database pool not available")
    
    async with db_pool.acquire() as conn:
        # Query SELL transactions for tax year
        transactions = await conn.fetch(
            """
            SELECT
                t.id,
                t.symbol,
                t.transaction_date,
                t.quantity,
                t.price,
                t.amount,
                t.realized_pl,
                t.currency,
                l.acquisition_date,
                l.cost_basis_per_share,
                CASE
                    WHEN (t.transaction_date - l.acquisition_date) > 365 THEN 'long_term'
                    ELSE 'short_term'
                END as holding_period
            FROM transactions t
            JOIN lots l ON l.closing_transaction_id = t.id
            WHERE t.portfolio_id = $1
              AND t.transaction_type = 'SELL'
              AND EXTRACT(YEAR FROM t.transaction_date) = $2
              AND t.realized_pl IS NOT NULL
            ORDER BY t.transaction_date, t.symbol
            """,
            portfolio_uuid,
            tax_year,
        )
        
        # Aggregate by symbol and holding period
        by_symbol = {}
        short_term_total = Decimal("0")
        long_term_total = Decimal("0")
        
        for txn in transactions:
            symbol = txn["symbol"]
            realized_pl = Decimal(str(txn["realized_pl"]))
            holding_period = txn["holding_period"]
            
            if symbol not in by_symbol:
                by_symbol[symbol] = {
                    "symbol": symbol,
                    "short_term_gains": Decimal("0"),
                    "long_term_gains": Decimal("0"),
                    "transactions": [],
                }
            
            if holding_period == "short_term":
                by_symbol[symbol]["short_term_gains"] += realized_pl
                short_term_total += realized_pl
            else:
                by_symbol[symbol]["long_term_gains"] += realized_pl
                long_term_total += realized_pl
            
            by_symbol[symbol]["transactions"].append({
                "transaction_id": str(txn["id"]),
                "date": str(txn["transaction_date"]),
                "quantity": float(txn["quantity"]),
                "price": float(txn["price"]),
                "proceeds": float(txn["amount"]),
                "cost_basis": float(txn["cost_basis_per_share"] * txn["quantity"]),
                "realized_pl": float(realized_pl),
                "holding_period": holding_period,
            })
        
        # Convert to float for JSON serialization
        for symbol_data in by_symbol.values():
            symbol_data["short_term_gains"] = float(symbol_data["short_term_gains"])
            symbol_data["long_term_gains"] = float(symbol_data["long_term_gains"])
        
        return {
            "realized_gains": by_symbol,
            "tax_year": tax_year,
            "total_short_term": float(short_term_total),
            "total_long_term": float(long_term_total),
            "total_realized": float(short_term_total + long_term_total),
            "lot_method": lot_method,
        }
```

**Work Estimate:** 3-4 hours (SQL query with joins, aggregation logic)

---

#### 2.2 `tax.wash_sales` (HIGH - 4-6 hours)

**Purpose:** Identify wash sales by tax year.

**Current State:**
- ❌ No wash sale detection logic exists
- ✅ `transactions` table has all transaction data

**What's Needed:**
- Query transactions for same symbol within 30-day window
- Identify loss transactions followed by repurchase
- Calculate disallowed loss amounts
- Return wash sale report

**Implementation:**
```python
@capability(
    name="tax.wash_sales",
    inputs={"portfolio_id": str, "tax_year": int},
    outputs={"wash_sales": list},
    description="Identify wash sales by tax year"
)
async def tax_wash_sales(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: str,
    tax_year: int = 2025,
) -> Dict[str, Any]:
    """Identify wash sales by tax year."""
    portfolio_uuid = self._to_uuid(portfolio_id, "portfolio_id")
    
    db_pool = self.services.get("db")
    if not db_pool:
        raise RuntimeError("Database pool not available")
    
    async with db_pool.acquire() as conn:
        # Query SELL transactions with losses in tax year
        sell_transactions = await conn.fetch(
            """
            SELECT
                t.id,
                t.symbol,
                t.transaction_date,
                t.quantity,
                t.price,
                t.realized_pl,
                l.acquisition_date
            FROM transactions t
            JOIN lots l ON l.closing_transaction_id = t.id
            WHERE t.portfolio_id = $1
              AND t.transaction_type = 'SELL'
              AND EXTRACT(YEAR FROM t.transaction_date) = $2
              AND t.realized_pl < 0  -- Only losses
            ORDER BY t.transaction_date
            """,
            portfolio_uuid,
            tax_year,
        )
        
        wash_sales = []
        
        for sell_txn in sell_transactions:
            symbol = sell_txn["symbol"]
            sell_date = sell_txn["transaction_date"]
            loss_amount = abs(Decimal(str(sell_txn["realized_pl"])))
            
            # Check for BUY transactions within 30 days after sale
            from datetime import timedelta
            
            check_start = sell_date
            check_end = sell_date + timedelta(days=30)
            
            buy_transactions = await conn.fetch(
                """
                SELECT
                    id,
                    transaction_date,
                    quantity,
                    price,
                    amount
                FROM transactions
                WHERE portfolio_id = $1
                  AND symbol = $2
                  AND transaction_type = 'BUY'
                  AND transaction_date BETWEEN $3 AND $4
                ORDER BY transaction_date
                """,
                portfolio_uuid,
                symbol,
                check_start,
                check_end,
            )
            
            if buy_transactions:
                # Calculate disallowed loss (proportional to repurchase quantity)
                total_repurchased = sum(Decimal(str(t["quantity"])) for t in buy_transactions)
                sold_quantity = Decimal(str(sell_txn["quantity"]))
                
                # Disallow loss if repurchase >= sale quantity
                if total_repurchased >= sold_quantity:
                    disallowed_loss = loss_amount
                else:
                    # Proportional disallowance
                    disallowed_loss = loss_amount * (total_repurchased / sold_quantity)
                
                wash_sales.append({
                    "symbol": symbol,
                    "sale_date": str(sell_date),
                    "sale_transaction_id": str(sell_txn["id"]),
                    "sold_quantity": float(sold_quantity),
                    "loss_amount": float(loss_amount),
                    "repurchase_transactions": [
                        {
                            "transaction_id": str(t["id"]),
                            "date": str(t["transaction_date"]),
                            "quantity": float(t["quantity"]),
                            "price": float(t["price"]),
                        }
                        for t in buy_transactions
                    ],
                    "total_repurchased": float(total_repurchased),
                    "disallowed_loss": float(disallowed_loss),
                    "days_until_safe": (buy_transactions[-1]["transaction_date"] - sell_date).days
                })
        
        total_disallowed = sum(ws["disallowed_loss"] for ws in wash_sales)
        
        return {
            "wash_sales": wash_sales,
            "tax_year": tax_year,
            "total_wash_sales": len(wash_sales),
            "total_disallowed_loss": float(total_disallowed),
        }
```

**Work Estimate:** 4-6 hours (complex date logic, proportional calculations)

---

#### 2.3 `tax.lot_details` (MEDIUM - 2-3 hours)

**Purpose:** Get lot-level details for tax reporting.

**Current State:**
- ✅ `lots` table has all lot tracking fields
- ✅ `transactions` table links to lots

**What's Needed:**
- Query lots with transaction details
- Include acquisition date, cost basis, disposition date
- Return lot-level breakdown

**Implementation:**
```python
@capability(
    name="tax.lot_details",
    inputs={"portfolio_id": str},
    outputs={"tax_lots": list},
    description="Get lot-level details for tax reporting"
)
async def tax_lot_details(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: str,
) -> Dict[str, Any]:
    """Get lot-level details for tax reporting."""
    portfolio_uuid = self._to_uuid(portfolio_id, "portfolio_id")
    
    db_pool = self.services.get("db")
    if not db_pool:
        raise RuntimeError("Database pool not available")
    
    async with db_pool.acquire() as conn:
        # Query all lots (open and closed)
        lots = await conn.fetch(
            """
            SELECT
                l.id,
                l.symbol,
                l.acquisition_date,
                l.quantity_original,
                l.quantity_open,
                l.cost_basis,
                l.cost_basis_per_share,
                l.closed_date,
                l.is_open,
                t.id as closing_transaction_id,
                t.transaction_date as disposition_date,
                t.realized_pl
            FROM lots l
            LEFT JOIN transactions t ON t.id = (
                SELECT id FROM transactions
                WHERE portfolio_id = l.portfolio_id
                  AND symbol = l.symbol
                  AND transaction_type = 'SELL'
                  AND transaction_date >= l.acquisition_date
                ORDER BY transaction_date
                LIMIT 1
            )
            WHERE l.portfolio_id = $1
            ORDER BY l.symbol, l.acquisition_date
            """,
            portfolio_uuid,
        )
        
        tax_lots = []
        for lot in lots:
            tax_lots.append({
                "lot_id": str(lot["id"]),
                "symbol": lot["symbol"],
                "acquisition_date": str(lot["acquisition_date"]),
                "quantity_original": float(lot["quantity_original"]),
                "quantity_open": float(lot["quantity_open"]),
                "quantity_closed": float(lot["quantity_original"] - lot["quantity_open"]),
                "cost_basis": float(lot["cost_basis"]),
                "cost_basis_per_share": float(lot["cost_basis_per_share"]),
                "is_open": lot["is_open"],
                "closed_date": str(lot["closed_date"]) if lot["closed_date"] else None,
                "disposition_date": str(lot["disposition_date"]) if lot["disposition_date"] else None,
                "realized_pl": float(lot["realized_pl"]) if lot["realized_pl"] else None,
            })
        
        return {
            "tax_lots": tax_lots,
            "total_lots": len(tax_lots),
            "open_lots": len([l for l in tax_lots if l["is_open"]]),
            "closed_lots": len([l for l in tax_lots if not l["is_open"]]),
        }
```

**Work Estimate:** 2-3 hours (SQL query with LEFT JOIN)

---

#### 2.4 `tax.summary` (LOW - 1-2 hours)

**Purpose:** Generate tax summary report.

**Current State:**
- ❌ No summary generation exists

**What's Needed:**
- Aggregate realized gains and wash sales
- Calculate net taxable gains
- Return summary report

**Implementation:**
```python
@capability(
    name="tax.summary",
    inputs={"realized_gains": dict, "wash_sales": list, "tax_year": int},
    outputs={"tax_summary": dict},
    description="Generate tax summary report"
)
async def tax_summary(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    realized_gains: Dict[str, Any],
    wash_sales: Dict[str, Any],
    tax_year: int = 2025,
) -> Dict[str, Any]:
    """Generate tax summary report."""
    # Extract data
    if isinstance(realized_gains, dict) and "realized_gains" in realized_gains:
        gains_data = realized_gains["realized_gains"]
        total_short_term = realized_gains.get("total_short_term", 0)
        total_long_term = realized_gains.get("total_long_term", 0)
    else:
        gains_data = realized_gains
        total_short_term = sum(
            g.get("short_term_gains", 0) for g in gains_data.values()
            if isinstance(g, dict)
        )
        total_long_term = sum(
            g.get("long_term_gains", 0) for g in gains_data.values()
            if isinstance(g, dict)
        )
    
    if isinstance(wash_sales, dict) and "wash_sales" in wash_sales:
        wash_sales_list = wash_sales["wash_sales"]
        total_disallowed = wash_sales.get("total_disallowed_loss", 0)
    else:
        wash_sales_list = wash_sales if isinstance(wash_sales, list) else []
        total_disallowed = sum(ws.get("disallowed_loss", 0) for ws in wash_sales_list)
    
    # Calculate net taxable gains
    net_short_term = total_short_term - total_disallowed
    net_long_term = total_long_term
    net_total = net_short_term + net_long_term
    
    return {
        "tax_summary": {
            "tax_year": tax_year,
            "realized_gains": {
                "short_term": total_short_term,
                "long_term": total_long_term,
                "total": total_short_term + total_long_term,
            },
            "wash_sales": {
                "count": len(wash_sales_list),
                "disallowed_loss": total_disallowed,
            },
            "net_taxable_gains": {
                "short_term": net_short_term,
                "long_term": net_long_term,
                "total": net_total,
            },
            "symbols_affected": len(gains_data),
        }
    }
```

**Work Estimate:** 1-2 hours (simple aggregation)

---

## Work Summary

| Capability | Complexity | Hours | Dependencies |
|------------|-----------|-------|--------------|
| `metrics.unrealized_pl` | MEDIUM | 2-3 | Existing unrealized P&L calculation |
| `tax.identify_losses` | MEDIUM | 2-3 | `metrics.unrealized_pl` |
| `tax.wash_sale_check` | HIGH | 4-6 | Transaction queries, date logic |
| `tax.calculate_benefit` | MEDIUM | 2-3 | `tax.identify_losses`, `tax.wash_sale_check` |
| `tax.rank_opportunities` | LOW | 1-2 | `tax.calculate_benefit` |
| `tax.realized_gains` | MEDIUM | 3-4 | Transaction queries, lot joins |
| `tax.wash_sales` | HIGH | 4-6 | Transaction queries, date logic |
| `tax.lot_details` | MEDIUM | 2-3 | Lot queries with transaction joins |
| `tax.summary` | LOW | 1-2 | `tax.realized_gains`, `tax.wash_sales` |
| **TOTAL** | **MEDIUM-HIGH** | **23-32** | **3-4 days** |

---

## Implementation Strategy

### Phase 1: Foundation (1 day)
1. Implement `metrics.unrealized_pl` (2-3 hours)
2. Implement `tax.identify_losses` (2-3 hours)
3. Implement `tax.lot_details` (2-3 hours)

### Phase 2: Wash Sale Logic (1 day)
1. Implement `tax.wash_sale_check` (4-6 hours)
2. Implement `tax.wash_sales` (4-6 hours)

### Phase 3: Tax Reporting (1 day)
1. Implement `tax.realized_gains` (3-4 hours)
2. Implement `tax.calculate_benefit` (2-3 hours)
3. Implement `tax.rank_opportunities` (1-2 hours)
4. Implement `tax.summary` (1-2 hours)

### Phase 4: Testing & Integration (0.5 day)
1. Test all capabilities
2. Update patterns
3. Integration testing

---

## Dependencies & Prerequisites

**Database Schema:**
- ✅ `transactions.realized_pl` field exists (Migration 017)
- ✅ `lots` table has all required fields
- ✅ Indexes exist for tax year queries

**Existing Code:**
- ✅ `trade_execution.py` calculates realized P&L
- ✅ `financial_analyst.py` calculates unrealized P&L
- ✅ Lot selection methods implemented

**Missing:**
- ❌ Wash sale detection logic
- ❌ Tax year aggregation queries
- ❌ Tax benefit calculation formulas

---

## Risk Assessment

**Low Risk:**
- `metrics.unrealized_pl` - Wraps existing logic
- `tax.identify_losses` - Simple filtering
- `tax.calculate_benefit` - Straightforward calculation
- `tax.rank_opportunities` - Simple sorting
- `tax.summary` - Simple aggregation

**Medium Risk:**
- `tax.lot_details` - SQL query complexity
- `tax.realized_gains` - SQL query with joins

**High Risk:**
- `tax.wash_sale_check` - Complex date logic, edge cases
- `tax.wash_sales` - Complex date logic, proportional calculations

**Mitigation:**
- Test wash sale logic thoroughly with edge cases
- Validate date calculations (30-day windows)
- Test with various lot selection methods

---

## Recommendation

**Option 1: Implement All Capabilities (Recommended)**
- **Work:** 3-4 days (24-32 hours)
- **Benefit:** Full tax compliance features
- **Risk:** Medium (wash sale logic is complex)

**Option 2: Implement Core Capabilities Only**
- **Work:** 2 days (16 hours)
- **Capabilities:** `metrics.unrealized_pl`, `tax.identify_losses`, `tax.realized_gains`, `tax.lot_details`, `tax.summary`
- **Benefit:** Basic tax reporting without wash sale detection
- **Risk:** Low

**Option 3: Archive Patterns**
- **Work:** 30 minutes
- **Benefit:** No broken patterns
- **Risk:** None

---

**Status:** ✅ **ASSESSMENT COMPLETE** - Ready for decision

