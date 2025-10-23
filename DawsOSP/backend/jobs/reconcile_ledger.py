"""
Ledger Reconciliation Job

Purpose: Reconcile ledger NAV vs pricing pack NAV (±1bp tolerance)
Updated: 2025-10-22
Priority: P0 (Critical for Sprint 1 - Truth Spine)

Features:
    - Compare ledger NAV vs pricing pack NAV
    - ±1bp tolerance
    - Store reconciliation results
    - Alert on reconciliation failure
    - Nightly scheduler

Architecture:
    Ledger Service → Holdings → Pricing Pack → Reconciliation → Database

Usage:
    # Manual run
    python -m backend.jobs.reconcile_ledger --portfolio-id <uuid>

    # Nightly scheduler (APScheduler)
    @scheduler.scheduled_job("cron", hour=1, minute=0)
    async def reconcile_all_portfolios():
        ...
"""

import argparse
import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from backend.app.services.ledger import get_ledger_service, LedgerService
from backend.app.db.pricing_pack_queries import get_pricing_pack_queries
from backend.app.db.connection import execute_statement, execute_query
from backend.app.db.connection import get_db_pool

logger = logging.getLogger("DawsOS.ReconciliationJob")
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)


# ============================================================================
# Data Models
# ============================================================================


class ReconciliationResult:
    """Reconciliation result for a portfolio."""

    def __init__(
        self,
        portfolio_id: UUID,
        pricing_pack_id: str,
        ledger_commit_hash: str,
        ledger_nav: Decimal,
        pricing_nav: Decimal,
        difference: Decimal,
        error_bps: Decimal,
        passed: bool,
    ):
        self.portfolio_id = portfolio_id
        self.pricing_pack_id = pricing_pack_id
        self.ledger_commit_hash = ledger_commit_hash
        self.ledger_nav = ledger_nav
        self.pricing_nav = pricing_nav
        self.difference = difference
        self.error_bps = error_bps
        self.passed = passed

    def to_dict(self) -> Dict:
        return {
            "portfolio_id": str(self.portfolio_id),
            "pricing_pack_id": self.pricing_pack_id,
            "ledger_commit_hash": self.ledger_commit_hash,
            "ledger_nav": float(self.ledger_nav),
            "pricing_nav": float(self.pricing_nav),
            "difference": float(self.difference),
            "error_bps": float(self.error_bps),
            "passed": self.passed,
        }


# ============================================================================
# Reconciliation Service
# ============================================================================


class ReconciliationService:
    """
    Ledger reconciliation service.

    Compares ledger NAV vs pricing pack NAV with ±1bp tolerance.
    """

    def __init__(self):
        self.ledger_service = get_ledger_service()
        self.pack_queries = get_pricing_pack_queries()

    async def compute_ledger_nav(
        self,
        portfolio_id: UUID,
        as_of_date: date,
        ledger_commit_hash: str,
        base_currency: str = "CAD",
    ) -> Decimal:
        """
        Compute portfolio NAV from ledger transactions.

        Args:
            portfolio_id: Portfolio UUID
            as_of_date: NAV as-of date
            ledger_commit_hash: Ledger commit hash
            base_currency: Base currency for NAV

        Returns:
            NAV in base currency
        """
        # Get balances from ledger
        balances = await self.ledger_service.get_portfolio_balance(
            portfolio_id,
            as_of_date,
            ledger_commit_hash,
        )

        if not balances:
            logger.warning(f"No ledger balances found for portfolio {portfolio_id}")
            return Decimal("0")

        # If single currency and matches base, return directly
        if len(balances) == 1 and base_currency in balances:
            return balances[base_currency]

        # Multi-currency: convert all to base currency
        # TODO: Fetch FX rates from pricing pack
        # For now, assume single currency or return first currency
        if base_currency in balances:
            nav = balances[base_currency]
        else:
            # Return first currency (warning: may not be base currency)
            nav = list(balances.values())[0]
            logger.warning(
                f"Base currency {base_currency} not found in ledger balances, "
                f"using {list(balances.keys())[0]}"
            )

        logger.debug(f"Ledger NAV for {portfolio_id}: {nav} {base_currency}")
        return nav

    async def compute_pricing_nav(
        self,
        portfolio_id: UUID,
        pack_id: str,
        base_currency: str = "CAD",
    ) -> Decimal:
        """
        Compute portfolio NAV from pricing pack.

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack ID
            base_currency: Base currency for NAV

        Returns:
            NAV in base currency
        """
        # Query holdings (lots) with symbol for price lookup
        query_lots = """
            SELECT
                l.security_id,
                l.symbol,
                l.currency,
                SUM(l.quantity) AS total_qty
            FROM lots l
            WHERE l.portfolio_id = $1
              AND l.is_open = true
              AND l.quantity > 0
            GROUP BY l.security_id, l.symbol, l.currency
        """
        lots = await execute_query(query_lots, portfolio_id)

        if not lots:
            logger.warning(f"No holdings found for portfolio {portfolio_id}")
            return Decimal("0")

        # Get pricing pack
        pack = await self.pack_queries.get_pack_by_id(pack_id)
        if not pack:
            raise ValueError(f"Pricing pack {pack_id} not found")

        total_nav = Decimal("0")

        # TODO: This needs prices table implementation
        # For now, use cost basis as fallback (will be replaced when prices table exists)
        # When prices table is implemented, query:
        # SELECT price FROM pack_prices WHERE pack_id = $1 AND symbol = $2

        query_cost_basis = """
            SELECT
                SUM(l.quantity * l.cost_basis_per_share) AS total_value
            FROM lots l
            WHERE l.portfolio_id = $1
              AND l.is_open = true
              AND l.quantity > 0
        """
        result = await execute_query(query_cost_basis, portfolio_id)

        if result and len(result) > 0 and result[0]["total_value"]:
            total_nav = Decimal(str(result[0]["total_value"]))

        logger.debug(f"Pricing NAV for {portfolio_id}: {total_nav} {base_currency}")
        logger.warning(
            f"Using cost basis for NAV calculation (prices table not yet implemented). "
            f"Portfolio {portfolio_id}: {total_nav} {base_currency}"
        )

        return total_nav

    async def reconcile_portfolio(
        self,
        portfolio_id: UUID,
        as_of_date: date,
        pack_id: Optional[str] = None,
        ledger_commit_hash: Optional[str] = None,
    ) -> ReconciliationResult:
        """
        Reconcile portfolio ledger vs pricing pack.

        Args:
            portfolio_id: Portfolio UUID
            as_of_date: Reconciliation as-of date
            pack_id: Pricing pack ID (latest if None)
            ledger_commit_hash: Ledger commit hash (latest if None)

        Returns:
            ReconciliationResult
        """
        # Get latest pack if not provided
        if not pack_id:
            pack = await self.pack_queries.get_latest_pack()
            if not pack:
                raise ValueError("No pricing packs found")
            pack_id = pack["id"]

        # Get ledger commit hash if not provided
        if not ledger_commit_hash:
            ledger_commit_hash = self.ledger_service.get_commit_hash()

        logger.info(
            f"Reconciling portfolio {portfolio_id} "
            f"(pack: {pack_id}, ledger: {ledger_commit_hash[:8]})"
        )

        # Compute NAVs
        ledger_nav = await self.compute_ledger_nav(
            portfolio_id,
            as_of_date,
            ledger_commit_hash,
        )

        pricing_nav = await self.compute_pricing_nav(
            portfolio_id,
            pack_id,
        )

        # Calculate difference and error
        difference = ledger_nav - pricing_nav

        if pricing_nav != 0:
            error_bps = abs(difference / pricing_nav * 10000)  # Basis points
        else:
            error_bps = Decimal("999999")  # Infinite error

        passed = error_bps <= Decimal("1.0")  # ±1bp tolerance

        result = ReconciliationResult(
            portfolio_id=portfolio_id,
            pricing_pack_id=pack_id,
            ledger_commit_hash=ledger_commit_hash,
            ledger_nav=ledger_nav,
            pricing_nav=pricing_nav,
            difference=difference,
            error_bps=error_bps,
            passed=passed,
        )

        logger.info(
            f"Reconciliation {'PASSED' if passed else 'FAILED'}: "
            f"error={error_bps:.2f}bp (ledger={ledger_nav}, pricing={pricing_nav})"
        )

        return result

    async def store_reconciliation_result(self, result: ReconciliationResult):
        """
        Store reconciliation result in database.

        Args:
            result: ReconciliationResult object
        """
        query = """
            INSERT INTO reconciliation_results (
                id,
                portfolio_id,
                pricing_pack_id,
                ledger_commit_hash,
                error_bps,
                passed,
                ledger_nav,
                pricing_nav,
                difference,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        """

        from uuid import uuid4

        await execute_statement(
            query,
            uuid4(),
            result.portfolio_id,
            result.pricing_pack_id,
            result.ledger_commit_hash,
            result.error_bps,
            result.passed,
            result.ledger_nav,
            result.pricing_nav,
            result.difference,
        )

        logger.info(f"Stored reconciliation result for portfolio {result.portfolio_id}")

    async def reconcile_all_portfolios(
        self,
        as_of_date: Optional[date] = None,
    ) -> List[ReconciliationResult]:
        """
        Reconcile all portfolios (nightly job).

        Args:
            as_of_date: Reconciliation date (today if None)

        Returns:
            List of ReconciliationResult objects
        """
        if not as_of_date:
            as_of_date = date.today()

        logger.info(f"Starting nightly reconciliation for {as_of_date}")

        # Get all portfolios
        query_portfolios = "SELECT id FROM portfolios WHERE is_active = true"
        portfolios = await execute_query(query_portfolios)

        if not portfolios:
            logger.warning("No active portfolios found")
            return []

        results = []
        passed_count = 0
        failed_count = 0

        for portfolio_row in portfolios:
            portfolio_id = portfolio_row["id"]

            try:
                result = await self.reconcile_portfolio(
                    portfolio_id,
                    as_of_date,
                )

                await self.store_reconciliation_result(result)
                results.append(result)

                if result.passed:
                    passed_count += 1
                else:
                    failed_count += 1
                    # TODO: Send alert for failed reconciliation
                    logger.error(
                        f"❌ Reconciliation FAILED for portfolio {portfolio_id}: "
                        f"error={result.error_bps:.2f}bp"
                    )

            except Exception as e:
                logger.error(f"Reconciliation error for portfolio {portfolio_id}: {e}")
                failed_count += 1

        logger.info(
            f"Nightly reconciliation complete: "
            f"{passed_count} passed, {failed_count} failed"
        )

        return results


# ============================================================================
# Singleton
# ============================================================================


_reconciliation_service_instance = None


def get_reconciliation_service() -> ReconciliationService:
    """
    Get singleton ReconciliationService instance.

    Returns:
        ReconciliationService singleton
    """
    global _reconciliation_service_instance

    if _reconciliation_service_instance is None:
        _reconciliation_service_instance = ReconciliationService()

    return _reconciliation_service_instance


# ============================================================================
# Scheduler Integration
# ============================================================================


# Uncomment when APScheduler is configured
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
#
# scheduler = AsyncIOScheduler()
#
# @scheduler.scheduled_job("cron", hour=1, minute=0)
# async def reconcile_all_portfolios_nightly():
#     """Nightly reconciliation job at 1:00 AM."""
#     service = get_reconciliation_service()
#     await service.reconcile_all_portfolios()


# ============================================================================
# CLI Entry Point
# ============================================================================


async def main():
    """CLI entry point for reconciliation."""
    parser = argparse.ArgumentParser(description="Reconcile ledger vs pricing pack")

    parser.add_argument(
        "--portfolio-id",
        type=str,
        help="Portfolio UUID to reconcile",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Reconcile all portfolios",
    )

    parser.add_argument(
        "--as-of-date",
        type=str,
        help="Reconciliation date (YYYY-MM-DD, default: today)",
    )

    args = parser.parse_args()

    # Parse date
    if args.as_of_date:
        as_of_date = date.fromisoformat(args.as_of_date)
    else:
        as_of_date = date.today()

    service = get_reconciliation_service()

    if args.all:
        # Reconcile all portfolios
        results = await service.reconcile_all_portfolios(as_of_date)

        print("\n=== Reconciliation Summary ===")
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        print(f"Total: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if failed > 0:
            print("\nFailed Reconciliations:")
            for result in results:
                if not result.passed:
                    print(
                        f"  {result.portfolio_id}: "
                        f"error={result.error_bps:.2f}bp "
                        f"(ledger={result.ledger_nav}, pricing={result.pricing_nav})"
                    )

    elif args.portfolio_id:
        # Reconcile single portfolio
        portfolio_id = UUID(args.portfolio_id)

        result = await service.reconcile_portfolio(
            portfolio_id,
            as_of_date,
        )

        await service.store_reconciliation_result(result)

        print("\n=== Reconciliation Result ===")
        print(f"Portfolio: {result.portfolio_id}")
        print(f"Pack: {result.pricing_pack_id}")
        print(f"Ledger: {result.ledger_commit_hash[:8]}")
        print(f"Ledger NAV: {result.ledger_nav:,.2f}")
        print(f"Pricing NAV: {result.pricing_nav:,.2f}")
        print(f"Difference: {result.difference:,.2f}")
        print(f"Error: {result.error_bps:.2f} bp")
        print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
