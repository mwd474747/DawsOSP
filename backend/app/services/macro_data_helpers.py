"""
Macro Data Helpers

Purpose: Helper functions to query macro indicators from database
Pattern: Similar to execute_query() - simple, focused helpers
Status: NEW - Part of constants refactor (Phase 1)

Usage:
    from app.services.macro_data_helpers import get_risk_free_rate

    # Get current risk-free rate
    rf_rate = await get_risk_free_rate()
    sharpe = (portfolio_return - float(rf_rate)) / portfolio_vol

Architecture:
    This module leverages existing DawsOS infrastructure:
    - MacroService already fetches FRED data
    - macro_indicators table already stores DGS10, UNRATE, etc.
    - execute_query() pattern already used throughout codebase

    We're NOT creating new architecture - just making existing data reusable.

Related:
    - backend/app/services/macro.py (MacroService.get_latest_indicator)
    - backend/db/schema/macro_indicators.sql (table schema)
    - CONSTANTS_REFACTOR_PLAN_CONSERVATIVE.md (implementation plan)
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from app.db.connection import execute_query_one, execute_query
from app.core.constants.financial import TRADING_DAYS_PER_YEAR

logger = logging.getLogger("DawsOS.MacroDataHelpers")


# =============================================================================
# RISK-FREE RATE HELPERS
# =============================================================================


async def get_risk_free_rate(as_of_date: Optional[date] = None) -> Decimal:
    """
    Get risk-free rate from DGS10 (10-Year Treasury Constant Maturity).

    This function queries the macro_indicators table for the latest DGS10 value,
    which is already being fetched and stored by MacroService from FRED API.

    Args:
        as_of_date: Get rate as of this date (default: latest available)

    Returns:
        Risk-free rate as decimal (e.g., Decimal('0.045') for 4.5%)
        Falls back to 0.03 (3%) if no data available

    Example:
        # Get current risk-free rate
        rf_rate = await get_risk_free_rate()

        # Use in Sharpe ratio
        sharpe = (portfolio_return - float(rf_rate)) / portfolio_vol

        # Get historical rate for backtesting
        rf_rate_2024 = await get_risk_free_rate(date(2024, 1, 1))

    Database Query:
        SELECT value FROM macro_indicators
        WHERE indicator_id = 'DGS10'
        ORDER BY date DESC LIMIT 1

    Data Source:
        - FRED API series: DGS10 (10-Year Treasury Constant Maturity Rate)
        - Fetched by: MacroService.fetch_indicators()
        - Stored in: macro_indicators table
        - Units: Percent (e.g., 4.5 means 4.5%)
        - Frequency: Daily

    Notes:
        - DGS10 is stored as decimal (transformed by FREDTransformationService)
        - Database stores 0.0408 for 4.08%, no conversion needed
        - Uses conservative 3% fallback if no data available
        - Logs warning if fallback is used (check FRED data freshness)
    """
    dgs10 = await get_latest_indicator_value("DGS10", as_of_date)

    if dgs10 is not None:
        # DGS10 is already stored as decimal by FREDTransformationService (e.g., 0.0408 for 4.08%)
        # No conversion needed - use value as-is
        # Fixed: Removed ÷100 that caused double conversion bug (SCALE-BUG-002)
        return dgs10

    # Fallback: Conservative 3% if no data
    logger.warning(
        f"DGS10 not available for {as_of_date or 'latest'}, "
        f"using 3% fallback. Check FRED data freshness."
    )
    return Decimal("0.03")


# =============================================================================
# GENERIC INDICATOR HELPERS
# =============================================================================


async def get_latest_indicator_value(
    indicator_id: str,
    as_of_date: Optional[date] = None
) -> Optional[Decimal]:
    """
    Get latest value for a macro indicator from database.

    This is a low-level helper that queries the macro_indicators table.
    For specific indicators, use dedicated helpers like get_risk_free_rate().

    Args:
        indicator_id: FRED series ID (e.g., "DGS10", "UNRATE", "CPIAUCSL")
        as_of_date: Get value as of this date (default: latest available)

    Returns:
        Indicator value as Decimal (in original units), or None if not found

    Example:
        # Get latest unemployment rate
        unrate = await get_latest_indicator_value("UNRATE")
        if unrate:
            print(f"Unemployment rate: {unrate}%")

        # Get historical CPI
        cpi = await get_latest_indicator_value("CPIAUCSL", date(2024, 1, 1))

    Available Indicators (from MacroService):
        - DGS10: 10-Year Treasury rate (percent)
        - DGS2: 2-Year Treasury rate (percent)
        - T10Y2Y: 10Y-2Y Treasury spread (percent)
        - UNRATE: Unemployment rate (percent)
        - CPIAUCSL: Consumer Price Index (index)
        - BAA10Y: Baa corporate bond spread (percent)
        - And 20+ more FRED series

    Database Schema:
        Table: macro_indicators
        - indicator_id: TEXT (e.g., "DGS10")
        - date: DATE
        - value: NUMERIC
        - units: TEXT (e.g., "Percent")

    Notes:
        - Returns value in original units (e.g., DGS10 = 4.5 means 4.5%)
        - Use specific helpers for unit conversions
        - Returns None if indicator not found (not an error)
    """
    if as_of_date:
        query = """
            SELECT value
            FROM macro_indicators
            WHERE indicator_id = $1
                AND date <= $2
            ORDER BY date DESC
            LIMIT 1
        """
        row = await execute_query_one(query, indicator_id, as_of_date)
    else:
        query = """
            SELECT value
            FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        row = await execute_query_one(query, indicator_id)

    if row:
        return Decimal(str(row["value"]))
    return None


async def get_indicator_history(
    indicator_id: str,
    lookback_days: int = TRADING_DAYS_PER_YEAR,
    as_of_date: Optional[date] = None
) -> List[dict]:
    """
    Get historical values for an indicator over lookback window.

    Args:
        indicator_id: FRED series ID
        lookback_days: Number of days to look back (default: TRADING_DAYS_PER_YEAR = 252)
        as_of_date: End date for history (default: today)

    Returns:
        List of dicts with 'date' and 'value' keys, sorted descending by date

    Example:
        # Get last year of DGS10 data
        history = await get_indicator_history("DGS10", 365)
        for row in history:
            print(f"{row['date']}: {row['value']}%")

    Database Query:
        SELECT date, value FROM macro_indicators
        WHERE indicator_id = $1 AND date >= $2
        ORDER BY date DESC

    Notes:
        - Returns empty list if no data found
        - Useful for calculating percentiles, moving averages, z-scores
    """
    end_date = as_of_date or date.today()
    start_date = end_date - timedelta(days=lookback_days)

    query = """
        SELECT date, value
        FROM macro_indicators
        WHERE indicator_id = $1
            AND date >= $2
            AND date <= $3
        ORDER BY date DESC
    """
    rows = await execute_query(query, indicator_id, start_date, end_date)

    return [
        {"date": row["date"], "value": float(row["value"])}
        for row in rows
    ]


async def get_indicator_percentile(
    indicator_id: str,
    percentile: int,
    lookback_days: int = TRADING_DAYS_PER_YEAR,
    as_of_date: Optional[date] = None
) -> Optional[Decimal]:
    """
    Calculate percentile value for an indicator over lookback window.

    Args:
        indicator_id: FRED series ID (e.g., "VIX", "UNRATE")
        percentile: Percentile to calculate (0-100)
        lookback_days: Historical window (default: TRADING_DAYS_PER_YEAR = 252)
        as_of_date: End date for calculation (default: today)

    Returns:
        Percentile value as Decimal, or None if insufficient data

    Example:
        # Get 80th percentile VIX over last year
        vix_80th = await get_indicator_percentile("VIX", 80, 252)
        if vix_80th:
            print(f"VIX 80th percentile: {vix_80th}")

        # Get 60th percentile unemployment
        unrate_60th = await get_indicator_percentile("UNRATE", 60)

    Use Cases:
        - Dynamic alert thresholds (e.g., VIX > 80th percentile)
        - Adaptive regime detection
        - Market condition classification

    Notes:
        - Requires at least 30 data points
        - Returns None if insufficient data (not an error)
        - Uses simple percentile calculation (not weighted)
    """
    history = await get_indicator_history(indicator_id, lookback_days, as_of_date)

    if not history or len(history) < 30:  # Need minimum data points
        logger.warning(
            f"Insufficient data for percentile: {indicator_id} "
            f"(found {len(history)} points, need 30+)"
        )
        return None

    values = [row["value"] for row in history]
    values.sort()

    # Calculate percentile index
    index = int((percentile / 100.0) * len(values))
    index = min(index, len(values) - 1)

    return Decimal(str(values[index]))


# =============================================================================
# VALIDATION HELPERS
# =============================================================================


async def validate_indicator_freshness(
    indicator_id: str,
    max_age_days: int = 7
) -> bool:
    """
    Check if an indicator has recent data.

    Args:
        indicator_id: FRED series ID
        max_age_days: Maximum acceptable age in days (default: 7)

    Returns:
        True if fresh data available, False otherwise

    Example:
        # Check if DGS10 is fresh
        is_fresh = await validate_indicator_freshness("DGS10", max_age_days=3)
        if not is_fresh:
            logger.warning("DGS10 data is stale, run MacroService.fetch_indicators()")

    Use Cases:
        - Pre-flight checks before calculations
        - Data quality monitoring
        - Alert on stale data
    """
    query = """
        SELECT MAX(date) as latest_date
        FROM macro_indicators
        WHERE indicator_id = $1
    """
    row = await execute_query_one(query, indicator_id)

    if not row or not row["latest_date"]:
        logger.warning(f"No data found for indicator: {indicator_id}")
        return False

    latest_date = row["latest_date"]
    age_days = (date.today() - latest_date).days

    if age_days > max_age_days:
        logger.warning(
            f"Indicator {indicator_id} is stale: "
            f"latest data is {age_days} days old (max: {max_age_days})"
        )
        return False

    return True


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Risk-free rate (most common use case)
    "get_risk_free_rate",

    # Generic indicator queries
    "get_latest_indicator_value",
    "get_indicator_history",
    "get_indicator_percentile",

    # Validation
    "validate_indicator_freshness",
]
