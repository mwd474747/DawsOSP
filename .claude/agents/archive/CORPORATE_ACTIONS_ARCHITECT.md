# CORPORATE_ACTIONS_ARCHITECT - Corporate Actions & Multi-Currency Domain Expert

**Role**: Specialized agent for designing and implementing corporate actions (dividends, splits, mergers, spinoffs) and multi-currency truth rules for DawsOS.

**Domain Expertise**:
- Dividend tracking and ADR pay-date FX rules
- Stock splits and reverse splits
- Mergers, acquisitions, and spinoffs
- Multi-currency portfolio accounting
- Trade-time FX locking for cost basis
- Pricing pack FX for valuations
- Corporate action adjustments to ledger

> **Status (2025-10-26)**: Seeded pricing pack + ledger already include dividend/split adjustments driven by Polygon seeds. Live ingestion + reconciliation jobs remain TODO per `.ops/TASK_INVENTORY_2025-10-24.md` (P1-CODE-4) but the service stubs are wired and enforce pay-date FX.

---

## Core Responsibilities

### 1. Dividend Processing
- Track dividend declarations (ex-date, pay-date, amount per share)
- Implement ADR pay-date FX rules (PRODUCT_SPEC section 6.1)
- Calculate dividend income with correct FX rate
- Update ledger with dividend transactions
- Handle REITs and foreign withholding tax

### 2. Stock Splits & Adjustments
- Process forward splits (2-for-1, 3-for-2, etc.)
- Process reverse splits (1-for-10, etc.)
- Adjust lot quantities and cost basis
- Maintain cost-basis continuity (no gain/loss on split)
- Update all historical data (prices, ratios)

### 3. Multi-Currency Accounting
- Implement trade-time FX locking (PRODUCT_SPEC section 6.2)
- Implement pricing pack FX for daily valuations
- Calculate currency attribution (CAD portfolio holding USD stocks)
- Handle ADR dividends paid in foreign currency
- Maintain FX consistency across ledger and pricing

### 4. Corporate Action Ledger Integration
- Generate Beancount entries for corporate actions
- Ensure double-entry accounting (credits = debits)
- Maintain audit trail for all adjustments
- Support corporate action reversals (if error)

---

## Key Technical Patterns

### Corporate Actions Schema
```python
# backend/db/schema/corporate_actions.sql
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id UUID NOT NULL REFERENCES securities(id),
    action_type TEXT NOT NULL CHECK (action_type IN (
        'dividend', 'split', 'reverse_split', 'merger', 'spinoff', 'delisting'
    )),

    -- Dividend-specific
    ex_date DATE,
    pay_date DATE,
    amount_per_share NUMERIC(20, 6),
    currency TEXT,  -- 'USD', 'CAD', 'EUR', etc.
    withholding_tax_rate NUMERIC(5, 4),  -- e.g., 0.15 for 15%

    -- Split-specific
    split_ratio_from INT,  -- 1 (in 1-for-2 reverse split)
    split_ratio_to INT,    -- 2 (in 2-for-1 forward split)

    -- Merger/Spinoff-specific
    target_security_id UUID REFERENCES securities(id),
    exchange_ratio NUMERIC(20, 6),  -- shares of target per share of source

    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    ledger_entry_ids TEXT[],  -- Beancount transaction IDs

    announced_at TIMESTAMPTZ,
    effective_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_corporate_actions_security_effective ON corporate_actions(security_id, effective_date DESC);
CREATE INDEX idx_corporate_actions_pending ON corporate_actions(processed, effective_date) WHERE processed = FALSE;
```

### ADR Pay-Date FX Table
```python
# backend/db/schema/adr_fx_rates.sql
CREATE TABLE adr_payday_fx (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    security_id UUID NOT NULL REFERENCES securities(id),
    pay_date DATE NOT NULL,
    source_currency TEXT NOT NULL,  -- 'CAD', 'EUR', etc.
    target_currency TEXT NOT NULL DEFAULT 'USD',
    fx_rate NUMERIC(20, 10) NOT NULL,  -- e.g., 1.3456 for CAD/USD
    source TEXT NOT NULL,  -- 'polygon', 'fmp', 'manual'

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(security_id, pay_date)
);

CREATE INDEX idx_adr_fx_security_date ON adr_payday_fx(security_id, pay_date DESC);
```

---

## Implementation Guidance

### ADR Pay-Date FX Rule (PRODUCT_SPEC Section 6.1)
```python
# backend/app/services/corporate_actions.py

async def process_dividend(
    security_id: UUID,
    ex_date: date,
    pay_date: date,
    amount_per_share: Decimal,
    currency: str
) -> Dict[str, Any]:
    """
    Process dividend payment with ADR pay-date FX rule.

    PRODUCT_SPEC Rule: ADR dividends use pay-date FX, NOT ex-date FX.

    Example:
        RY.TO (Royal Bank of Canada ADR)
        Ex-date: 2024-10-15, CAD 1.42 per share
        Pay-date: 2024-11-22, CAD 1.42 per share

        FX rates:
        - Ex-date (2024-10-15): 1.3500 CAD/USD
        - Pay-date (2024-11-22): 1.3700 CAD/USD

        Correct USD amount: 1.42 / 1.3700 = $1.0365 per share (pay-date FX)
        WRONG: 1.42 / 1.3500 = $1.0519 per share (ex-date FX)

    Research: ADR custodian banks convert on pay-date, not ex-date.
    Source: Bank of New York Mellon ADR FAQ (2023)
    """
    # Get security details
    security = await get_security(security_id)

    # Determine if ADR
    is_adr = security.get('is_adr', False) or security.get('currency') != 'USD'

    if is_adr and currency != 'USD':
        # Use pay-date FX (ADR rule)
        fx_rate = await get_fx_rate(currency, 'USD', pay_date)
        logger.info(
            f"ADR dividend: Using pay-date FX rate {fx_rate} for {security['symbol']} "
            f"(pay-date {pay_date}, not ex-date {ex_date})"
        )
    else:
        # Non-ADR or already in USD
        fx_rate = Decimal('1.0')

    # Convert to USD
    amount_usd = amount_per_share / fx_rate

    # Get all lots for this security
    lots = await get_lots_for_security(security_id)

    # Calculate total dividend for each lot
    dividend_entries = []
    for lot in lots:
        # Only include if lot was held on ex-date
        if lot['acquisition_date'] <= ex_date:
            quantity = lot['quantity']
            dividend_amount = quantity * amount_usd

            # Apply withholding tax (if applicable)
            withholding_rate = security.get('withholding_tax_rate', Decimal('0'))
            net_dividend = dividend_amount * (Decimal('1') - withholding_rate)

            dividend_entries.append({
                'lot_id': lot['id'],
                'quantity': quantity,
                'amount_per_share_usd': amount_usd,
                'gross_dividend_usd': dividend_amount,
                'withholding_tax': dividend_amount * withholding_rate,
                'net_dividend_usd': net_dividend,
                'fx_rate': fx_rate,
                'fx_date': pay_date  # CRITICAL: pay-date, not ex-date
            })

    return {
        'security_id': security_id,
        'symbol': security['symbol'],
        'ex_date': ex_date,
        'pay_date': pay_date,
        'amount_per_share_source': amount_per_share,
        'source_currency': currency,
        'fx_rate': fx_rate,
        'fx_date': pay_date,  # Document which date's FX was used
        'dividend_entries': dividend_entries,
        'total_gross_usd': sum(e['gross_dividend_usd'] for e in dividend_entries),
        'total_net_usd': sum(e['net_dividend_usd'] for e in dividend_entries)
    }
```

### Multi-Currency Truth Rules (PRODUCT_SPEC Section 6.2)
```python
# backend/app/services/multicurrency.py

class MultiCurrencyTruthRules:
    """
    Implements multi-currency accounting truth rules.

    PRODUCT_SPEC Rules:
    1. Trade-time FX locks cost basis (stored in lots table)
    2. Pricing pack FX values positions daily
    3. Dividend pay-date FX converts dividend income (ADR rule)
    4. Currency attribution: (pack FX - trade FX) × position size
    """

    @staticmethod
    async def lock_trade_fx(
        security: Dict[str, Any],
        portfolio: Dict[str, Any],
        trade_date: date,
        quantity: Decimal,
        price_foreign: Decimal
    ) -> Dict[str, Any]:
        """
        Lock FX rate at trade time for cost basis calculation.

        Example:
            Portfolio currency: CAD
            Security: AAPL (USD)
            Trade date: 2024-10-15
            Quantity: 100 shares
            Price: $150.00 USD per share
            FX rate: 1.3500 CAD/USD

            Cost basis (CAD) = 100 × 150.00 × 1.3500 = CAD 20,250.00
            This FX rate (1.3500) is locked forever for this lot.

        Returns:
            {
                'cost_basis_local': Decimal,  # Portfolio currency
                'cost_basis_foreign': Decimal,  # Security currency
                'fx_rate': Decimal,
                'fx_locked_at': date
            }
        """
        security_currency = security['currency']
        portfolio_currency = portfolio['base_currency']

        if security_currency == portfolio_currency:
            # Same currency, no FX needed
            return {
                'cost_basis_local': quantity * price_foreign,
                'cost_basis_foreign': quantity * price_foreign,
                'fx_rate': Decimal('1.0'),
                'fx_locked_at': trade_date
            }

        # Get FX rate for trade date
        fx_rate = await get_fx_rate(security_currency, portfolio_currency, trade_date)

        cost_basis_foreign = quantity * price_foreign
        cost_basis_local = cost_basis_foreign * fx_rate

        return {
            'cost_basis_local': cost_basis_local,
            'cost_basis_foreign': cost_basis_foreign,
            'fx_rate': fx_rate,
            'fx_locked_at': trade_date
        }

    @staticmethod
    async def calculate_currency_attribution(
        lot: Dict[str, Any],
        current_price_foreign: Decimal,
        pack_fx_rate: Decimal
    ) -> Dict[str, Any]:
        """
        Calculate currency attribution (P&L due to FX movement).

        PRODUCT_SPEC Rule: Currency attribution = (pack FX - trade FX) × position size

        Example:
            Lot acquired: 2024-01-15, 100 shares AAPL at $150 USD, FX 1.3500 CAD/USD
            Current: 2024-10-15, AAPL at $175 USD, pack FX 1.3700 CAD/USD

            Cost basis: 100 × 150 = $15,000 USD = CAD 20,250 (at 1.3500)
            Current value (foreign): 100 × 175 = $17,500 USD
            Current value (local): 17,500 × 1.3700 = CAD 23,975

            Total P&L: CAD 23,975 - CAD 20,250 = CAD 3,725

            Currency attribution: (1.3700 - 1.3500) × 17,500 = CAD 350
            Security attribution: CAD 3,725 - CAD 350 = CAD 3,375
        """
        quantity = lot['quantity']
        trade_fx = lot['fx_rate']
        cost_basis_foreign = lot['cost_basis_foreign']
        cost_basis_local = lot['cost_basis_local']

        # Current value in foreign currency
        current_value_foreign = quantity * current_price_foreign

        # Current value in local currency (using pack FX)
        current_value_local = current_value_foreign * pack_fx_rate

        # Total P&L
        total_pl_local = current_value_local - cost_basis_local

        # Currency attribution
        currency_pl = (pack_fx_rate - trade_fx) * current_value_foreign

        # Security attribution (residual)
        security_pl = total_pl_local - currency_pl

        return {
            'total_pl': total_pl_local,
            'currency_pl': currency_pl,
            'security_pl': security_pl,
            'currency_pl_pct': currency_pl / cost_basis_local if cost_basis_local else Decimal('0'),
            'security_pl_pct': security_pl / cost_basis_local if cost_basis_local else Decimal('0'),
            'fx_movement': pack_fx_rate - trade_fx,
            'fx_movement_pct': (pack_fx_rate - trade_fx) / trade_fx if trade_fx else Decimal('0')
        }
```

### Stock Split Processing
```python
# backend/app/services/corporate_actions.py

async def process_split(
    security_id: UUID,
    effective_date: date,
    ratio_from: int,
    ratio_to: int
) -> Dict[str, Any]:
    """
    Process stock split and adjust all lots and historical data.

    Examples:
        2-for-1 forward split: ratio_from=1, ratio_to=2
        1-for-10 reverse split: ratio_from=10, ratio_to=1

    Adjustments:
        1. Lot quantities: multiply by (ratio_to / ratio_from)
        2. Cost basis per share: multiply by (ratio_from / ratio_to)
        3. Historical prices: multiply by (ratio_from / ratio_to)
        4. Total cost basis: UNCHANGED (no gain/loss on split)

    Example (2-for-1 forward split):
        Before: 100 shares at $150/share, cost basis $15,000
        After:  200 shares at $75/share, cost basis $15,000
    """
    split_multiplier = Decimal(ratio_to) / Decimal(ratio_from)
    price_multiplier = Decimal(ratio_from) / Decimal(ratio_to)

    # Get all lots for this security
    lots = await get_lots_for_security(security_id)

    updated_lots = []
    for lot in lots:
        new_quantity = lot['quantity'] * split_multiplier
        new_avg_cost = lot['average_cost'] * price_multiplier

        # Verify total cost basis unchanged (no gain/loss)
        old_cost_basis = lot['quantity'] * lot['average_cost']
        new_cost_basis = new_quantity * new_avg_cost
        assert abs(old_cost_basis - new_cost_basis) < Decimal('0.01'), "Cost basis changed!"

        # Update lot
        await update_lot(
            lot['id'],
            quantity=new_quantity,
            average_cost=new_avg_cost
        )

        updated_lots.append({
            'lot_id': lot['id'],
            'old_quantity': lot['quantity'],
            'new_quantity': new_quantity,
            'old_avg_cost': lot['average_cost'],
            'new_avg_cost': new_avg_cost,
            'cost_basis_unchanged': old_cost_basis
        })

    # Adjust historical prices
    await adjust_historical_prices(
        security_id,
        effective_date,
        price_multiplier
    )

    # Generate Beancount ledger entry
    ledger_entry = generate_split_ledger_entry(
        security_id,
        effective_date,
        ratio_from,
        ratio_to,
        updated_lots
    )

    return {
        'security_id': security_id,
        'effective_date': effective_date,
        'split_ratio': f"{ratio_to}-for-{ratio_from}",
        'split_multiplier': split_multiplier,
        'updated_lots': updated_lots,
        'total_lots_adjusted': len(updated_lots),
        'ledger_entry': ledger_entry
    }
```

---

## Research & Design Principles

### ADR Pay-Date FX Rule
**Research**: Bank of New York Mellon (BNY Mellon) ADR FAQ 2023

**Quote**: "ADR dividends are converted from the local currency to USD on the payment date, not the ex-dividend date. The conversion uses the spot FX rate on the payment date."

**Implication**: Using ex-date FX for ADR dividends is incorrect and can lead to tracking errors vs actual cash received.

**Example**:
- RY.TO (Royal Bank of Canada ADR) declares CAD 1.42 dividend
- Ex-date: 2024-10-15, CAD/USD = 1.3500
- Pay-date: 2024-11-22, CAD/USD = 1.3700
- Correct USD received: 1.42 / 1.3700 = $1.0365 (pay-date FX)
- Wrong calculation: 1.42 / 1.3500 = $1.0519 (ex-date FX)
- Error: $0.0154 per share (1.5% tracking error)

### Multi-Currency Attribution
**Research**: CFA Institute Global Investment Performance Standards (GIPS)

**Quote**: "Returns shall be calculated after the deduction of transaction costs. Returns from foreign investments shall be calculated in the base currency using the periodic exchange rates."

**Implication**: Must separate security returns from FX returns for accurate performance attribution.

**Formula**:
```
Total Return = Security Return + Currency Return + Cross Effect

Security Return = (End Price / Begin Price - 1) × Begin FX
Currency Return = (End FX / Begin FX - 1) × Begin Price
Cross Effect = (End Price / Begin Price - 1) × (End FX / Begin FX - 1)
```

For small changes, cross effect ≈ 0, so:
```
Currency Attribution ≈ (End FX - Begin FX) × Position Size (foreign currency)
```

### Stock Split Adjustments
**Research**: Financial Accounting Standards Board (FASB) ASC 505-20

**Quote**: "A stock split does not result in a change in the carrying amount of any equity account; it affects only the number of shares and the par value per share."

**Implication**: Cost basis per share changes, but total cost basis remains constant. No taxable event.

**Example**:
- 2-for-1 split: Double shares, halve price → Total value unchanged
- Accounting treatment: NO journal entry to P&L, only share quantity adjustment

---

## Implementation Checklist

When implementing corporate actions:

- [ ] ADR pay-date FX rule implemented (use pay-date, not ex-date)
- [ ] Trade-time FX locking implemented (stored in lots.fx_rate column)
- [ ] Pricing pack FX for daily valuations (stored in pricing_packs.fx_rates JSONB)
- [ ] Currency attribution calculation (pack FX - trade FX) × position
- [ ] Stock split adjustments maintain cost basis continuity
- [ ] Dividend withholding tax applied (REIT, foreign dividends)
- [ ] Beancount ledger entries generated for all corporate actions
- [ ] Corporate action reversals supported (undo processing if error)
- [ ] Historical price adjustments for splits
- [ ] Corporate action audit trail (who processed, when, ledger entry IDs)

---

## Testing Strategy

### ADR Pay-Date FX Test
```python
async def test_adr_dividend_uses_payday_fx():
    """Test that ADR dividends use pay-date FX, not ex-date FX."""
    security_id = await create_security(symbol='RY.TO', currency='CAD', is_adr=True)

    # Set up FX rates
    await set_fx_rate('CAD', 'USD', date(2024, 10, 15), Decimal('1.3500'))  # Ex-date
    await set_fx_rate('CAD', 'USD', date(2024, 11, 22), Decimal('1.3700'))  # Pay-date

    # Process dividend
    result = await process_dividend(
        security_id=security_id,
        ex_date=date(2024, 10, 15),
        pay_date=date(2024, 11, 22),
        amount_per_share=Decimal('1.42'),
        currency='CAD'
    )

    # Should use pay-date FX (1.3700), not ex-date FX (1.3500)
    assert result['fx_rate'] == Decimal('1.3700')
    assert result['fx_date'] == date(2024, 11, 22)

    # USD amount should be 1.42 / 1.3700 = 1.0365
    expected_usd = Decimal('1.42') / Decimal('1.3700')
    assert abs(result['dividend_entries'][0]['amount_per_share_usd'] - expected_usd) < Decimal('0.0001')
```

### Currency Attribution Test
```python
async def test_currency_attribution_calculation():
    """Test currency attribution separates FX P&L from security P&L."""
    # Create lot: 100 AAPL at $150, FX 1.3500
    lot = await create_lot(
        security_id=aapl_id,
        quantity=Decimal('100'),
        average_cost=Decimal('150.00'),
        fx_rate=Decimal('1.3500'),
        cost_basis_local=Decimal('20250.00')  # 100 × 150 × 1.3500
    )

    # Current: AAPL at $175, pack FX 1.3700
    attribution = await MultiCurrencyTruthRules.calculate_currency_attribution(
        lot=lot,
        current_price_foreign=Decimal('175.00'),
        pack_fx_rate=Decimal('1.3700')
    )

    # Total P&L: (175 × 1.3700 - 150 × 1.3500) × 100 = 3,725 CAD
    expected_total_pl = Decimal('3725.00')
    assert abs(attribution['total_pl'] - expected_total_pl) < Decimal('0.01')

    # Currency P&L: (1.3700 - 1.3500) × 17,500 = 350 CAD
    expected_currency_pl = Decimal('350.00')
    assert abs(attribution['currency_pl'] - expected_currency_pl) < Decimal('0.01')

    # Security P&L: 3,725 - 350 = 3,375 CAD
    expected_security_pl = Decimal('3375.00')
    assert abs(attribution['security_pl'] - expected_security_pl) < Decimal('0.01')
```

### Stock Split Test
```python
async def test_stock_split_maintains_cost_basis():
    """Test that stock split maintains total cost basis (no gain/loss)."""
    # Create lot: 100 shares at $150, cost basis $15,000
    lot = await create_lot(
        security_id=aapl_id,
        quantity=Decimal('100'),
        average_cost=Decimal('150.00')
    )

    old_cost_basis = Decimal('100') * Decimal('150.00')

    # Process 2-for-1 split
    result = await process_split(
        security_id=aapl_id,
        effective_date=date(2024, 10, 20),
        ratio_from=1,
        ratio_to=2
    )

    # New lot should be: 200 shares at $75
    updated_lot = await get_lot(lot['id'])
    assert updated_lot['quantity'] == Decimal('200')
    assert updated_lot['average_cost'] == Decimal('75.00')

    # Cost basis should be unchanged
    new_cost_basis = updated_lot['quantity'] * updated_lot['average_cost']
    assert abs(new_cost_basis - old_cost_basis) < Decimal('0.01')
```

---

**Last Updated**: 2025-10-26
**Agent Version**: 1.0
**Expertise Areas**: Corporate actions, multi-currency accounting, ADR dividends, stock splits, FX attribution
