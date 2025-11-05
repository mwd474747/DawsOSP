"""
Portfolio Helper Functions

Purpose: Shared helper functions for portfolio calculations
Created: 2025-11-05
Priority: P1 (Reduce code duplication)

Functions:
    - get_portfolio_value: Calculate total portfolio value from pricing pack
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


async def get_portfolio_value(
    db,
    portfolio_id: str,
    pack_id: str,
) -> Decimal:
    """
    Get total portfolio value from pricing pack.

    Sums: quantity_open × price × fx_rate for all positions.

    Args:
        db: Database connection pool (asyncpg Pool or connection)
        portfolio_id: Portfolio UUID
        pack_id: Pricing pack ID

    Returns:
        Total portfolio value in base currency (Decimal)

    Raises:
        ValueError: If portfolio not found
        PricingPackNotFoundError: If pricing pack not found (via PricingService)
    """
    # Get portfolio base currency
    base_ccy_row = await db.fetchrow(
        "SELECT base_currency FROM portfolios WHERE id = $1", portfolio_id
    )
    if not base_ccy_row:
        raise ValueError(f"Portfolio not found: {portfolio_id}")
    base_ccy = base_ccy_row["base_currency"]

    # Get positions with prices and FX rates
    positions = await db.fetch(
        """
        SELECT l.quantity_open, p.close, COALESCE(fx.rate, 1.0) as fx_rate
        FROM lots l
        JOIN prices p ON l.security_id = p.security_id AND p.pricing_pack_id = $2
        LEFT JOIN fx_rates fx ON l.currency = fx.base_ccy
            AND fx.quote_ccy = $3
            AND fx.pricing_pack_id = $2
        WHERE l.portfolio_id = $1 AND l.quantity_open > 0
        """,
        portfolio_id,
        pack_id,
        base_ccy,
    )

    total = sum(
        Decimal(str(pos["quantity_open"]))
        * Decimal(str(pos["close"]))
        * Decimal(str(pos["fx_rate"]))
        for pos in positions
    )

    return Decimal(total) if total else Decimal(0)

