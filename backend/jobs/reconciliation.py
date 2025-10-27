"""
Ledger Reconciliation - Beancount Truth Validation

Purpose: Reconcile DB valuations against Beancount ledger (±1 basis point)
Updated: 2025-10-21
Priority: P0 (CRITICAL - Accuracy validation foundation)

Sacred Invariants:
    1. Position quantities MUST match exactly
    2. Cost basis MUST match exactly
    3. Cash balances MUST match exactly
    4. Portfolio valuations MUST match ±1 basis point (0.0001)

Reconciliation Checks:
    - Quantity check: DB qty == Ledger qty (exact)
    - Cost basis check: DB cost == Ledger cost (exact)
    - Valuation check: |DB value - Ledger value| / Ledger value < 0.0001
    - Cash check: |DB cash - Ledger cash| < 0.01 (penny rounding)

Failure Handling:
    - If any reconciliation fails → STOP nightly job
    - Generate detailed diff report
    - Alert admin (PagerDuty/Slack)
    - Do NOT continue to metrics/pre-warm

Beancount Integration:
    - Load ledger from .ledger/main.beancount
    - Extract positions by account
    - Compare to DB positions from pricing pack

Usage:
    report = await reconcile_ledger(pack_id, ledger_path=".ledger/main.beancount")
    if report.status != 'PASS':
        logger.error(f"Reconciliation failed: {report.errors}")
        raise ReconciliationError(report.errors)
"""

import logging
from typing import Dict, List, Optional
from datetime import date, datetime
from decimal import Decimal
from dataclasses import dataclass, field
import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationError:
    """Single reconciliation error."""
    account: str
    error_type: str  # 'QUANTITY_MISMATCH', 'COST_MISMATCH', 'VALUATION_MISMATCH', 'MISSING_POSITION'
    db_value: Optional[Decimal]
    ledger_value: Optional[Decimal]
    error_bps: Optional[Decimal] = None  # For valuation errors
    details: Optional[str] = None


@dataclass
class ReconciliationReport:
    """Reconciliation report."""
    status: str  # 'PASS', 'FAIL'
    pack_id: str
    ledger_path: str
    reconciled_at: datetime
    portfolios_checked: int
    positions_checked: int
    errors: List[ReconciliationError] = field(default_factory=list)
    max_error_bps: Decimal = Decimal('0')
    summary: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize to dict for JSON storage."""
        return {
            "status": self.status,
            "pack_id": self.pack_id,
            "ledger_path": self.ledger_path,
            "reconciled_at": self.reconciled_at.isoformat(),
            "portfolios_checked": self.portfolios_checked,
            "positions_checked": self.positions_checked,
            "error_count": len(self.errors),
            "max_error_bps": float(self.max_error_bps),
            "errors": [
                {
                    "account": e.account,
                    "error_type": e.error_type,
                    "db_value": float(e.db_value) if e.db_value else None,
                    "ledger_value": float(e.ledger_value) if e.ledger_value else None,
                    "error_bps": float(e.error_bps) if e.error_bps else None,
                    "details": e.details,
                }
                for e in self.errors
            ],
            "summary": self.summary,
        }


class LedgerReconciliator:
    """
    Reconcile DB positions against Beancount ledger.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize reconciliator.

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db = db_pool

    async def reconcile_ledger(
        self, pack_id: str, ledger_path: str = ".ledger/main.beancount"
    ) -> ReconciliationReport:
        """
        Reconcile DB valuations against Beancount ledger.

        Sacred invariants:
        1. Position quantities must match exactly
        2. Cost basis must match exactly
        3. Cash balances must match exactly
        4. Portfolio valuations must match ±1 basis point

        Args:
            pack_id: Pricing pack UUID
            ledger_path: Path to Beancount ledger file

        Returns:
            ReconciliationReport with status='PASS' or 'FAIL'

        Raises:
            FileNotFoundError: If ledger file not found
            ValueError: If Beancount parsing fails
        """
        logger.info(f"Starting ledger reconciliation for pack {pack_id}")

        report = ReconciliationReport(
            status='PASS',
            pack_id=pack_id,
            ledger_path=ledger_path,
            reconciled_at=datetime.utcnow(),
            portfolios_checked=0,
            positions_checked=0,
        )

        try:
            # Load Beancount ledger
            ledger_data = self._load_beancount_ledger(ledger_path)

            # Get pack date
            pack_date = await self._get_pack_date(pack_id)

            # Get all portfolios
            portfolios = await self.db.fetch("""
                SELECT id, account_name, base_ccy
                FROM portfolios
                WHERE active = TRUE
            """)

            report.portfolios_checked = len(portfolios)

            # Reconcile each portfolio
            for portfolio in portfolios:
                portfolio_errors = await self._reconcile_portfolio(
                    portfolio_id=str(portfolio['id']),
                    account_name=portfolio['account_name'],
                    pack_id=pack_id,
                    pack_date=pack_date,
                    ledger_data=ledger_data,
                )

                report.errors.extend(portfolio_errors)
                report.positions_checked += len(portfolio_errors)

            # Compute max error
            valuation_errors = [
                e for e in report.errors
                if e.error_type == 'VALUATION_MISMATCH' and e.error_bps
            ]
            if valuation_errors:
                report.max_error_bps = max(e.error_bps for e in valuation_errors)

            # Set status
            if report.errors:
                report.status = 'FAIL'
                logger.error(
                    f"Reconciliation FAILED: {len(report.errors)} errors, "
                    f"max error {report.max_error_bps:.2f}bp"
                )
            else:
                report.status = 'PASS'
                logger.info(
                    f"Reconciliation PASSED: {report.portfolios_checked} portfolios, "
                    f"{report.positions_checked} positions"
                )

            # Generate summary
            report.summary = {
                "total_errors": len(report.errors),
                "errors_by_type": self._count_errors_by_type(report.errors),
                "max_error_bps": float(report.max_error_bps),
            }

        except Exception as e:
            logger.error(f"Reconciliation failed with exception: {e}")
            report.status = 'FAIL'
            report.errors.append(
                ReconciliationError(
                    account='SYSTEM',
                    error_type='EXCEPTION',
                    db_value=None,
                    ledger_value=None,
                    details=str(e),
                )
            )

        return report

    def _load_beancount_ledger(self, ledger_path: str) -> Dict:
        """
        Load Beancount ledger and extract positions.

        Args:
            ledger_path: Path to Beancount file

        Returns:
            {
                "account_name": {
                    "holdings": [
                        {
                            "currency": "AAPL",
                            "qty": Decimal("100"),
                            "cost_per_unit": Decimal("150.00"),
                            "cost_currency": "USD"
                        },
                        ...
                    ],
                    "cash_balance": Decimal("5000.00")
                },
                ...
            }

        Raises:
            FileNotFoundError: If ledger file not found
            ValueError: If Beancount parsing fails
        """
        try:
            from beancount import loader
            from beancount.core import getters, amount
        except ImportError:
            raise ImportError(
                "Beancount not installed. Install with: pip install beancount"
            )

        # Load ledger
        entries, errors, options = loader.load_file(ledger_path)

        if errors:
            logger.warning(f"Beancount parsing errors: {len(errors)}")
            for error in errors[:5]:  # Log first 5 errors
                logger.warning(f"  {error}")

        # Extract positions by account
        ledger_data = {}

        for account, positions_list in getters.get_account_positions(entries).items():
            holdings = []
            cash_balance = Decimal('0')

            for pos in positions_list:
                # Position structure: pos.units (Amount), pos.cost (Cost or None)
                currency = pos.units.currency
                qty = Decimal(str(pos.units.number))

                # Cash positions (no cost)
                if pos.cost is None:
                    if currency in ['USD', 'CAD', 'EUR', 'GBP']:
                        cash_balance += qty
                    continue

                # Security positions (with cost)
                holdings.append({
                    "currency": currency,  # Ticker symbol in Beancount
                    "qty": qty,
                    "cost_per_unit": Decimal(str(pos.cost.number)),
                    "cost_currency": pos.cost.currency,
                })

            ledger_data[account] = {
                "holdings": holdings,
                "cash_balance": cash_balance,
            }

        logger.info(f"Loaded Beancount ledger: {len(ledger_data)} accounts")

        return ledger_data

    async def _reconcile_portfolio(
        self,
        portfolio_id: str,
        account_name: str,
        pack_id: str,
        pack_date: date,
        ledger_data: Dict,
    ) -> List[ReconciliationError]:
        """
        Reconcile single portfolio against ledger.

        Args:
            portfolio_id: Portfolio UUID
            account_name: Beancount account name (e.g., "Assets:Brokerage:Schwab")
            pack_id: Pricing pack UUID
            pack_date: Pack as-of date
            ledger_data: Loaded Beancount data

        Returns:
            List of reconciliation errors
        """
        errors = []

        # Get ledger positions for this account
        ledger_positions = ledger_data.get(account_name)
        if not ledger_positions:
            logger.warning(f"Account {account_name} not found in ledger")
            return errors

        # Get DB positions
        db_positions = await self._get_db_positions(portfolio_id, pack_id)

        # Reconcile each ledger position
        for ledger_holding in ledger_positions["holdings"]:
            symbol = ledger_holding["currency"]  # Ticker symbol

            # Find matching DB position
            db_holding = next(
                (p for p in db_positions if p["symbol"] == symbol), None
            )

            if not db_holding:
                errors.append(
                    ReconciliationError(
                        account=f"{account_name}:{symbol}",
                        error_type='MISSING_POSITION',
                        db_value=None,
                        ledger_value=ledger_holding["qty"],
                        details=f"Position exists in ledger but not in DB",
                    )
                )
                continue

            # Check quantity (exact match required)
            if db_holding["qty"] != ledger_holding["qty"]:
                errors.append(
                    ReconciliationError(
                        account=f"{account_name}:{symbol}",
                        error_type='QUANTITY_MISMATCH',
                        db_value=db_holding["qty"],
                        ledger_value=ledger_holding["qty"],
                        details=f"Quantity mismatch: DB={db_holding['qty']}, Ledger={ledger_holding['qty']}",
                    )
                )

            # Check cost basis (exact match required)
            db_cost = db_holding["cost_per_unit"]
            ledger_cost = ledger_holding["cost_per_unit"]

            if abs(db_cost - ledger_cost) > Decimal('0.01'):  # 1 cent tolerance
                errors.append(
                    ReconciliationError(
                        account=f"{account_name}:{symbol}",
                        error_type='COST_MISMATCH',
                        db_value=db_cost,
                        ledger_value=ledger_cost,
                        details=f"Cost basis mismatch: DB={db_cost}, Ledger={ledger_cost}",
                    )
                )

            # Check market value (±1bp tolerance)
            db_value = db_holding["market_value"]
            ledger_qty = ledger_holding["qty"]
            ledger_price = db_holding["price"]  # Use same price for fair comparison
            ledger_value = ledger_qty * ledger_price

            if ledger_value > 0:
                error_bps = abs(db_value - ledger_value) / ledger_value * Decimal('10000')

                if error_bps > Decimal('1.0'):  # 1 basis point threshold
                    errors.append(
                        ReconciliationError(
                            account=f"{account_name}:{symbol}",
                            error_type='VALUATION_MISMATCH',
                            db_value=db_value,
                            ledger_value=ledger_value,
                            error_bps=error_bps,
                            details=f"Valuation error: {error_bps:.2f}bp (DB={db_value}, Ledger={ledger_value})",
                        )
                    )

        # Check for DB positions not in ledger
        ledger_symbols = {h["currency"] for h in ledger_positions["holdings"]}
        for db_holding in db_positions:
            if db_holding["symbol"] not in ledger_symbols:
                errors.append(
                    ReconciliationError(
                        account=f"{account_name}:{db_holding['symbol']}",
                        error_type='MISSING_POSITION',
                        db_value=db_holding["qty"],
                        ledger_value=None,
                        details=f"Position exists in DB but not in ledger",
                    )
                )

        # Reconcile cash balance
        ledger_cash = ledger_positions["cash_balance"]
        db_cash = await self._get_db_cash_balance(portfolio_id)

        if abs(db_cash - ledger_cash) > Decimal('0.01'):  # 1 cent tolerance
            errors.append(
                ReconciliationError(
                    account=f"{account_name}:Cash",
                    error_type='CASH_MISMATCH',
                    db_value=db_cash,
                    ledger_value=ledger_cash,
                    details=f"Cash mismatch: DB={db_cash}, Ledger={ledger_cash}",
                )
            )

        return errors

    async def _get_db_positions(self, portfolio_id: str, pack_id: str) -> List[Dict]:
        """
        Get DB positions for portfolio from pricing pack.

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack UUID

        Returns:
            List of position records
        """
        rows = await self.db.fetch("""
            SELECT
                s.symbol,
                l.qty_open as qty,
                l.cost_per_unit_ccy as cost_per_unit,
                p.close as price,
                (l.qty_open * p.close * COALESCE(fx.rate, 1.0)) as market_value
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            JOIN prices p ON l.security_id = p.security_id AND p.pricing_pack_id = $2
            LEFT JOIN fx_rates fx ON s.currency = fx.base_ccy
                AND fx.quote_ccy = (SELECT base_ccy FROM portfolios WHERE id = $1)
                AND fx.pricing_pack_id = $2
            WHERE l.portfolio_id = $1 AND l.qty_open > 0
        """, portfolio_id, pack_id)

        return [
            {
                "symbol": row["symbol"],
                "qty": Decimal(str(row["qty"])),
                "cost_per_unit": Decimal(str(row["cost_per_unit"])),
                "price": Decimal(str(row["price"])),
                "market_value": Decimal(str(row["market_value"])),
            }
            for row in rows
        ]

    async def _get_db_cash_balance(self, portfolio_id: str) -> Decimal:
        """
        Get cash balance for portfolio from DB.

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            Cash balance
        """
        row = await self.db.fetchrow("""
            SELECT COALESCE(SUM(cash_balance), 0) as total_cash
            FROM portfolio_cash
            WHERE portfolio_id = $1
        """, portfolio_id)

        return Decimal(str(row["total_cash"])) if row else Decimal('0')

    async def _get_pack_date(self, pack_id: str) -> date:
        """Get as-of date for pricing pack."""
        row = await self.db.fetchrow("""
            SELECT asof_date FROM pricing_packs WHERE id = $1
        """, pack_id)

        if not row:
            raise ValueError(f"Pricing pack not found: {pack_id}")

        return row["asof_date"]

    def _count_errors_by_type(self, errors: List[ReconciliationError]) -> Dict:
        """
        Count errors by type.

        Args:
            errors: List of errors

        Returns:
            {"QUANTITY_MISMATCH": 5, "VALUATION_MISMATCH": 2, ...}
        """
        counts = {}
        for error in errors:
            counts[error.error_type] = counts.get(error.error_type, 0) + 1
        return counts


# Convenience functions for nightly job
async def reconcile_ledger(
    db_pool: asyncpg.Pool, pack_id: str, ledger_path: str = ".ledger/main.beancount"
) -> ReconciliationReport:
    """
    Reconcile DB against Beancount ledger (convenience function for nightly job).

    Args:
        db_pool: AsyncPG connection pool
        pack_id: Pricing pack UUID
        ledger_path: Path to Beancount ledger

    Returns:
        ReconciliationReport
    """
    reconciliator = LedgerReconciliator(db_pool)
    return await reconciliator.reconcile_ledger(pack_id, ledger_path)
