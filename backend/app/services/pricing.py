"""
Pricing Service - Query prices and FX rates from pricing packs

Purpose: Service layer for pricing pack queries (prices, FX rates, pack metadata)
Updated: 2025-10-23
Priority: P0 (Critical for valuation and metrics)

Sacred Invariants:
    1. All prices and FX rates are tied to pricing_pack_id
    2. Pricing packs are IMMUTABLE once created
    3. Executor MUST use latest fresh pack for valuation
    4. Every metric/valuation carries pricing_pack_id for reproducibility

Usage:
    pricing_service = PricingService()

    # Get latest fresh pack
    pack = await pricing_service.get_latest_pack()

    # Get price for a security
    price = await pricing_service.get_price(security_id, pack_id)

    # Get FX rate
    fx_rate = await pricing_service.get_fx_rate("USD", "CAD", pack_id)

    # Check if pack is fresh
    is_fresh = await pricing_service.is_pack_fresh(pack_id)
"""

import logging
from datetime import date, datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from dataclasses import dataclass

from backend.app.db.pricing_pack_queries import get_pricing_pack_queries
from backend.app.db.connection import execute_query_one, execute_query

logger = logging.getLogger("DawsOS.PricingService")


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class PricingPack:
    """Pricing pack metadata."""
    id: str
    date: date
    policy: str
    hash: str
    status: str
    is_fresh: bool
    prewarm_done: bool
    reconciliation_passed: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class SecurityPrice:
    """Security price from pricing pack."""
    security_id: str
    pricing_pack_id: str
    asof_date: date
    close: Decimal
    currency: str
    source: str
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    volume: Optional[int] = None


@dataclass
class FXRate:
    """Foreign exchange rate from pricing pack."""
    base_ccy: str
    quote_ccy: str
    pricing_pack_id: str
    asof_ts: datetime
    rate: Decimal
    source: str
    policy: Optional[str] = None


# ============================================================================
# Pricing Service
# ============================================================================


class PricingService:
    """
    Service for querying prices and FX rates from pricing packs.

    All methods use pricing_pack_id to ensure reproducibility.
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize pricing service.

        Args:
            use_db: Use database connection (default: True, False for testing)
        """
        self.use_db = use_db
        self.pack_queries = get_pricing_pack_queries(use_db=use_db)

    # ========================================================================
    # Pack Queries
    # ========================================================================

    async def get_latest_pack(self, require_fresh: bool = True) -> Optional[PricingPack]:
        """
        Get the most recent pricing pack.

        Args:
            require_fresh: If True, only return fresh packs (default: True)

        Returns:
            PricingPack object or None if no pack found
        """
        pack_data = await self.pack_queries.get_latest_pack()

        if not pack_data:
            logger.warning("No pricing pack found")
            return None

        # Filter by freshness if required
        if require_fresh and not pack_data.get("is_fresh"):
            logger.warning(f"Latest pack {pack_data['id']} is not fresh (status={pack_data['status']})")
            return None

        return PricingPack(
            id=pack_data["id"],
            date=pack_data["date"],
            policy=pack_data["policy"],
            hash=pack_data["hash"],
            status=pack_data["status"],
            is_fresh=pack_data["is_fresh"],
            prewarm_done=pack_data["prewarm_done"],
            reconciliation_passed=pack_data["reconciliation_passed"],
            created_at=pack_data["created_at"],
            updated_at=pack_data["updated_at"],
        )

    async def get_pack_by_id(self, pack_id: str) -> Optional[PricingPack]:
        """
        Get pricing pack by ID.

        Args:
            pack_id: Pricing pack ID (e.g., "PP_2025-10-21")

        Returns:
            PricingPack object or None if not found
        """
        pack_data = await self.pack_queries.get_pack_by_id(pack_id)

        if not pack_data:
            return None

        return PricingPack(
            id=pack_data["id"],
            date=pack_data["date"],
            policy=pack_data["policy"],
            hash=pack_data["hash"],
            status=pack_data["status"],
            is_fresh=pack_data["is_fresh"],
            prewarm_done=pack_data["prewarm_done"],
            reconciliation_passed=pack_data["reconciliation_passed"],
            created_at=pack_data["created_at"],
            updated_at=pack_data["updated_at"],
        )

    async def is_pack_fresh(self, pack_id: str) -> bool:
        """
        Check if pricing pack is fresh (ready for use).

        Args:
            pack_id: Pricing pack ID

        Returns:
            True if pack is fresh, False otherwise
        """
        pack = await self.get_pack_by_id(pack_id)
        return pack.is_fresh if pack else False

    # ========================================================================
    # Price Queries
    # ========================================================================

    async def get_price(
        self,
        security_id: str,
        pack_id: str,
    ) -> Optional[SecurityPrice]:
        """
        Get price for a security from pricing pack.

        Args:
            security_id: Security UUID
            pack_id: Pricing pack ID

        Returns:
            SecurityPrice object or None if not found
        """
        if not self.use_db:
            logger.warning(f"get_price({security_id}, {pack_id}): Using stub implementation")
            # Stub: Return mock price
            return SecurityPrice(
                security_id=security_id,
                pricing_pack_id=pack_id,
                asof_date=date(2025, 10, 21),
                close=Decimal("100.00"),
                currency="USD",
                source="stub",
            )

        query = """
            SELECT
                security_id,
                pricing_pack_id,
                date as asof_date,
                close,
                open,
                high,
                low,
                volume,
                currency,
                source
            FROM prices
            WHERE security_id = $1 AND pricing_pack_id = $2
        """

        try:
            row = await execute_query_one(query, security_id, pack_id)

            if not row:
                logger.warning(f"No price found for security {security_id} in pack {pack_id}")
                return None

            return SecurityPrice(
                security_id=str(row["security_id"]),
                pricing_pack_id=row["pricing_pack_id"],
                asof_date=row["asof_date"],
                close=row["close"],
                currency=row["currency"],
                source=row["source"],
                open=row.get("open"),
                high=row.get("high"),
                low=row.get("low"),
                volume=row.get("volume"),
            )

        except Exception as e:
            logger.error(f"Failed to get price for {security_id}: {e}", exc_info=True)
            raise

    async def get_prices_for_securities(
        self,
        security_ids: List[str],
        pack_id: str,
    ) -> Dict[str, SecurityPrice]:
        """
        Get prices for multiple securities from pricing pack.

        Args:
            security_ids: List of security UUIDs
            pack_id: Pricing pack ID

        Returns:
            Dict mapping security_id to SecurityPrice (only for found securities)
        """
        if not self.use_db:
            logger.warning(f"get_prices_for_securities: Using stub implementation")
            return {
                sec_id: SecurityPrice(
                    security_id=sec_id,
                    pricing_pack_id=pack_id,
                    asof_date=date(2025, 10, 21),
                    close=Decimal("100.00"),
                    currency="USD",
                    source="stub",
                )
                for sec_id in security_ids
            }

        query = """
            SELECT
                security_id,
                pricing_pack_id,
                date as asof_date,
                close,
                open,
                high,
                low,
                volume,
                currency,
                source
            FROM prices
            WHERE security_id = ANY($1) AND pricing_pack_id = $2
        """

        try:
            rows = await execute_query(query, security_ids, pack_id)

            prices = {}
            for row in rows:
                sec_id = str(row["security_id"])
                prices[sec_id] = SecurityPrice(
                    security_id=sec_id,
                    pricing_pack_id=row["pricing_pack_id"],
                    asof_date=row["asof_date"],
                    close=row["close"],
                    currency=row["currency"],
                    source=row["source"],
                    open=row.get("open"),
                    high=row.get("high"),
                    low=row.get("low"),
                    volume=row.get("volume"),
                )

            return prices

        except Exception as e:
            logger.error(f"Failed to get prices for securities: {e}", exc_info=True)
            raise

    async def get_prices_as_decimals(
        self,
        security_ids: List[str],
        pack_id: str,
    ) -> Dict[str, Decimal]:
        """
        Get prices for multiple securities as plain Decimals (performance optimized).

        This is more efficient than get_prices_for_securities() when you only need
        the close price, as it avoids creating/unpacking SecurityPrice dataclasses.

        Args:
            security_ids: List of security UUIDs
            pack_id: Pricing pack ID

        Returns:
            Dict mapping security_id (str) to close price (Decimal)

        Example:
            prices = await pricing_service.get_prices_as_decimals([...], "PP_2025-10-21")
            # {"uuid-1": Decimal("227.48"), "uuid-2": Decimal("115.23")}
        """
        if not self.use_db:
            logger.warning(f"get_prices_as_decimals: Using stub implementation")
            return {sec_id: Decimal("100.00") for sec_id in security_ids}

        query = """
            SELECT security_id, close
            FROM prices
            WHERE security_id = ANY($1) AND pricing_pack_id = $2
        """

        try:
            rows = await execute_query(query, security_ids, pack_id)

            # Return plain dict of Decimals (no dataclass overhead)
            prices = {
                str(row["security_id"]): Decimal(str(row["close"]))
                for row in rows
            }

            logger.debug(f"Loaded {len(prices)} prices as Decimals from pack {pack_id}")
            return prices

        except Exception as e:
            logger.error(f"Failed to get prices as decimals: {e}", exc_info=True)
            raise

    async def get_all_prices(self, pack_id: str) -> List[SecurityPrice]:
        """
        Get all prices from pricing pack.

        Args:
            pack_id: Pricing pack ID

        Returns:
            List of SecurityPrice objects
        """
        if not self.use_db:
            logger.warning(f"get_all_prices({pack_id}): Using stub implementation")
            return []

        query = """
            SELECT
                security_id,
                pricing_pack_id,
                date as asof_date,
                close,
                open,
                high,
                low,
                volume,
                currency,
                source
            FROM prices
            WHERE pricing_pack_id = $1
            ORDER BY security_id
        """

        try:
            rows = await execute_query(query, pack_id)

            prices = []
            for row in rows:
                prices.append(SecurityPrice(
                    security_id=str(row["security_id"]),
                    pricing_pack_id=row["pricing_pack_id"],
                    asof_date=row["asof_date"],
                    close=row["close"],
                    currency=row["currency"],
                    source=row["source"],
                    open=row.get("open"),
                    high=row.get("high"),
                    low=row.get("low"),
                    volume=row.get("volume"),
                ))

            return prices

        except Exception as e:
            logger.error(f"Failed to get all prices for pack {pack_id}: {e}", exc_info=True)
            raise

    # ========================================================================
    # FX Rate Queries
    # ========================================================================

    async def get_fx_rate(
        self,
        base_ccy: str,
        quote_ccy: str,
        pack_id: str,
    ) -> Optional[FXRate]:
        """
        Get FX rate from pricing pack.

        Rate is expressed as: quote_ccy per 1 unit of base_ccy
        Example: get_fx_rate("USD", "CAD") returns 1.36 CAD per 1 USD

        Args:
            base_ccy: Base currency (e.g., "USD")
            quote_ccy: Quote currency (e.g., "CAD")
            pack_id: Pricing pack ID

        Returns:
            FXRate object or None if not found
        """
        if not self.use_db:
            logger.warning(f"get_fx_rate({base_ccy}/{quote_ccy}, {pack_id}): Using stub")
            return FXRate(
                base_ccy=base_ccy,
                quote_ccy=quote_ccy,
                pricing_pack_id=pack_id,
                asof_ts=datetime(2025, 10, 21, 16, 0),
                rate=Decimal("1.3625"),
                source="stub",
                policy="WM4PM_CAD",
            )

        query = """
            SELECT
                base_ccy,
                quote_ccy,
                pricing_pack_id,
                date,
                rate
            FROM fx_rates
            WHERE base_ccy = $1 AND quote_ccy = $2 AND pricing_pack_id = $3
        """

        try:
            row = await execute_query_one(query, base_ccy, quote_ccy, pack_id)

            if not row:
                logger.warning(f"No FX rate found for {base_ccy}/{quote_ccy} in pack {pack_id}")
                return None

            return FXRate(
                base_ccy=row["base_ccy"],
                quote_ccy=row["quote_ccy"],
                pricing_pack_id=row["pricing_pack_id"],
                asof_ts=datetime.combine(row["date"], datetime.min.time()),  # Convert date to datetime
                rate=row["rate"],
                source="database",  # Column doesn't exist, use default
                policy=None,  # Column doesn't exist
            )

        except Exception as e:
            logger.error(f"Failed to get FX rate {base_ccy}/{quote_ccy}: {e}", exc_info=True)
            raise

    async def get_all_fx_rates(self, pack_id: str) -> List[FXRate]:
        """
        Get all FX rates from pricing pack.

        Args:
            pack_id: Pricing pack ID

        Returns:
            List of FXRate objects
        """
        if not self.use_db:
            logger.warning(f"get_all_fx_rates({pack_id}): Using stub implementation")
            return []

        query = """
            SELECT
                base_ccy,
                quote_ccy,
                pricing_pack_id,
                date,
                rate
            FROM fx_rates
            WHERE pricing_pack_id = $1
            ORDER BY base_ccy, quote_ccy
        """

        try:
            rows = await execute_query(query, pack_id)

            fx_rates = []
            for row in rows:
                fx_rates.append(FXRate(
                    base_ccy=row["base_ccy"],
                    quote_ccy=row["quote_ccy"],
                    pricing_pack_id=row["pricing_pack_id"],
                    asof_ts=datetime.combine(row["date"], datetime.min.time()),  # Convert date to datetime
                    rate=row["rate"],
                    source="database",  # Column doesn't exist, use default
                    policy=None,  # Column doesn't exist
                ))

            return fx_rates

        except Exception as e:
            logger.error(f"Failed to get all FX rates for pack {pack_id}: {e}", exc_info=True)
            raise

    # ========================================================================
    # Currency Conversion
    # ========================================================================

    async def convert_currency(
        self,
        amount: Decimal,
        from_ccy: str,
        to_ccy: str,
        pack_id: str,
    ) -> Decimal:
        """
        Convert amount from one currency to another using pack FX rates.

        Args:
            amount: Amount to convert
            from_ccy: Source currency
            to_ccy: Target currency
            pack_id: Pricing pack ID

        Returns:
            Converted amount in target currency

        Raises:
            ValueError: If FX rate not found
        """
        # Same currency = no conversion
        if from_ccy == to_ccy:
            return amount

        # Get FX rate
        fx_rate = await self.get_fx_rate(from_ccy, to_ccy, pack_id)

        if not fx_rate:
            # Try inverse rate
            inverse_rate = await self.get_fx_rate(to_ccy, from_ccy, pack_id)
            if inverse_rate:
                # Invert the rate
                rate = Decimal("1") / inverse_rate.rate
            else:
                raise ValueError(f"No FX rate found for {from_ccy}/{to_ccy} in pack {pack_id}")
        else:
            rate = fx_rate.rate

        return amount * rate


# ============================================================================
# Global Instance
# ============================================================================

# Singleton instance
_pricing_service: Optional[PricingService] = None


def get_pricing_service(use_db: bool = True) -> PricingService:
    """
    Get singleton PricingService instance.

    Args:
        use_db: Use database connection (default: True)

    Returns:
        PricingService instance
    """
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService(use_db=use_db)
    return _pricing_service


def init_pricing_service(use_db: bool = True, force: bool = False) -> PricingService:
    """
    Initialize PricingService (with optional singleton reset).

    Args:
        use_db: Use database connection (default: True)
        force: Force reinitialization even if singleton exists (default: False)

    Returns:
        PricingService instance

    Note:
        In production, ALWAYS call with use_db=True and force=True during startup
        to ensure freshness gate uses real database instead of cached stub.
    """
    global _pricing_service

    if force or _pricing_service is None:
        logger.info(f"Initializing pricing service with use_db={use_db}")
        _pricing_service = PricingService(use_db=use_db)

    return _pricing_service
