"""
Corporate Actions Sync Service

Automatically fetches and processes corporate actions (dividends, splits) 
from FMP API for portfolio holdings.

Created: 2025-11-06
"""

from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import asyncpg
import logging
import os

from app.services.corporate_actions import CorporateActionsService
from app.integrations.fmp_provider import FMPProvider

logger = logging.getLogger(__name__)


class CorporateActionsSyncService:
    """
    Service for syncing corporate actions from FMP API.
    
    Features:
    - Fetches dividend announcements for portfolio holdings
    - Fetches stock split announcements for portfolio holdings
    - Automatically processes and records corporate actions
    - Avoids duplicate entries
    - Handles multi-currency portfolios
    """
    
    def __init__(self, conn: asyncpg.Connection):
        """
        Initialize corporate actions sync service.
        
        Args:
            conn: Database connection with RLS context
        """
        self.conn = conn
        self.ca_service = CorporateActionsService(conn)
        
    async def _get_portfolio_holdings(
        self, 
        portfolio_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[str]:
        """
        Get list of symbols held in portfolio during the date range.
        
        This includes both currently open positions AND positions that were
        closed during or after the date range (so we catch their dividends).
        
        Args:
            portfolio_id: Portfolio UUID
            from_date: Start of date range
            to_date: End of date range
            
        Returns:
            List of ticker symbols that were held at any point in the date range
        """
        # Get all symbols that were held at any point during the date range
        # This includes positions that may have been closed after the from_date
        rows = await self.conn.fetch("""
            SELECT DISTINCT s.symbol
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = $1
                -- Include if purchased before the end of our range
                AND l.purchase_date <= $3
                -- Include if still open OR closed after the start of our range
                AND (l.close_date IS NULL OR l.close_date >= $2)
        """, portfolio_id, from_date or date.today(), to_date or date.today())
        
        return [row["symbol"] for row in rows]
    
    async def _check_dividend_exists(
        self, 
        portfolio_id: UUID, 
        symbol: str, 
        ex_date: date,
        amount: Decimal
    ) -> bool:
        """
        Check if dividend has already been recorded.
        
        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            ex_date: Ex-dividend date
            amount: Dividend per share
            
        Returns:
            True if dividend already exists
        """
        row = await self.conn.fetchrow("""
            SELECT ca.id
            FROM corporate_actions ca
            JOIN securities s ON ca.security_id = s.id
            WHERE ca.portfolio_id = $1
                AND s.symbol = $2
                AND ca.ex_date = $3
                AND ca.amount = $4
                AND ca.action_type = 'DIVIDEND'
            LIMIT 1
        """, portfolio_id, symbol, ex_date, amount)
        
        return row is not None
    
    async def _check_split_exists(
        self,
        portfolio_id: UUID,
        symbol: str,
        split_date: date,
        ratio: Decimal
    ) -> bool:
        """
        Check if stock split has already been recorded.
        
        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            split_date: Split effective date
            ratio: Split ratio
            
        Returns:
            True if split already exists
        """
        row = await self.conn.fetchrow("""
            SELECT ca.id
            FROM corporate_actions ca
            JOIN securities s ON ca.security_id = s.id
            WHERE ca.portfolio_id = $1
                AND s.symbol = $2
                AND ca.ex_date = $3
                AND ca.split_ratio = $4
                AND ca.action_type = 'SPLIT'
            LIMIT 1
        """, portfolio_id, symbol, split_date, ratio)
        
        return row is not None
    
    async def _get_shares_on_date(
        self,
        portfolio_id: UUID,
        symbol: str,
        target_date: date
    ) -> Decimal:
        """
        Get number of shares held on a specific date.
        
        This considers the historical position by checking the original quantity
        and subtracting any sales/closes that happened BEFORE the target date.
        
        Args:
            portfolio_id: Portfolio UUID
            symbol: Security symbol
            target_date: Date to check holdings
            
        Returns:
            Number of shares held on that date
        """
        # Get all lots purchased before target date and calculate shares held on that date
        # We use quantity_original and check if the lot was closed before target date
        row = await self.conn.fetchrow("""
            SELECT SUM(
                CASE
                    -- If lot was purchased after target date, it doesn't count
                    WHEN l.purchase_date > $3 THEN 0
                    -- If lot has no close date or closed after target date, use full original quantity
                    WHEN l.close_date IS NULL OR l.close_date > $3 THEN l.quantity_original
                    -- If lot was closed before target date, it doesn't count
                    WHEN l.close_date <= $3 THEN 0
                    -- Default case (shouldn't happen)
                    ELSE 0
                END
            ) as total_shares
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            WHERE l.portfolio_id = $1
                AND s.symbol = $2
        """, portfolio_id, symbol, target_date)
        
        return Decimal(str(row["total_shares"])) if row and row["total_shares"] else Decimal("0")
    
    async def sync_dividends(
        self,
        portfolio_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Sync dividend announcements from FMP for portfolio holdings.
        
        Args:
            portfolio_id: Portfolio UUID
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: 30 days future)
            dry_run: If True, don't record dividends, just return what would be processed
            
        Returns:
            Dict with sync results
        """
        # Default date range
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today() + timedelta(days=30)
            
        logger.info(f"Syncing dividends for portfolio {portfolio_id} from {from_date} to {to_date}")
        
        # Get portfolio holdings for the date range
        holdings = await self._get_portfolio_holdings(portfolio_id, from_date, to_date)
        if not holdings:
            logger.info("No holdings found in portfolio")
            return {
                "portfolio_id": str(portfolio_id),
                "holdings_count": 0,
                "dividends_processed": 0,
                "dividends_skipped": 0,
                "errors": []
            }
        
        # Get portfolio base currency
        portfolio_row = await self.conn.fetchrow(
            "SELECT base_currency FROM portfolios WHERE id = $1",
            portfolio_id
        )
        base_currency = portfolio_row["base_currency"] if portfolio_row else "USD"
        
        # Initialize FMP provider
        api_key = os.getenv("FMP_API_KEY")
        if not api_key:
            return {
                "portfolio_id": str(portfolio_id),
                "error": "FMP_API_KEY not configured",
                "holdings_count": len(holdings)
            }
        
        provider = FMPProvider(api_key=api_key)
        
        # Fetch dividend calendar from FMP
        try:
            dividends = await provider.get_dividend_calendar(from_date, to_date)
        except Exception as e:
            logger.error(f"Failed to fetch dividend calendar: {e}")
            return {
                "portfolio_id": str(portfolio_id),
                "error": f"FMP API error: {str(e)}",
                "holdings_count": len(holdings)
            }
        
        # Process dividends for our holdings
        processed = 0
        skipped = 0
        errors = []
        processed_dividends = []
        
        for dividend in dividends:
            symbol = dividend.get("symbol")
            if symbol not in holdings:
                continue  # Skip if we don't hold this stock
                
            # Extract dividend details
            ex_date = datetime.strptime(dividend["exDividendDate"], "%Y-%m-%d").date()
            pay_date = datetime.strptime(dividend["paymentDate"], "%Y-%m-%d").date() if dividend.get("paymentDate") else ex_date + timedelta(days=3)
            amount = Decimal(str(dividend["dividend"]))
            currency = dividend.get("currency", "USD")
            
            # Check if dividend already recorded
            if await self._check_dividend_exists(portfolio_id, symbol, ex_date, amount):
                logger.debug(f"Dividend already recorded: {symbol} {ex_date} ${amount}")
                skipped += 1
                continue
            
            # Get shares held on ex-date
            shares = await self._get_shares_on_date(portfolio_id, symbol, ex_date)
            if shares <= 0:
                logger.debug(f"No shares held on ex-date: {symbol} {ex_date}")
                skipped += 1
                continue
            
            dividend_info = {
                "symbol": symbol,
                "shares": float(shares),
                "dividend_per_share": float(amount),
                "ex_date": ex_date.isoformat(),
                "pay_date": pay_date.isoformat(),
                "currency": currency,
                "gross_amount": float(shares * amount)
            }
            
            if not dry_run:
                try:
                    # Record the dividend
                    result = await self.ca_service.record_dividend(
                        portfolio_id=portfolio_id,
                        symbol=symbol,
                        shares=shares,
                        dividend_per_share=amount,
                        currency=currency,
                        ex_date=ex_date,
                        pay_date=pay_date,
                        withholding_tax=Decimal("0"),  # TODO: Add withholding tax logic
                        base_currency=base_currency if currency != base_currency else None,
                        notes=f"Auto-synced from FMP on {date.today()}"
                    )
                    processed += 1
                    dividend_info["status"] = "recorded"
                    dividend_info["transaction_id"] = str(result.get("transaction_id"))
                except Exception as e:
                    logger.error(f"Failed to record dividend for {symbol}: {e}")
                    errors.append(f"{symbol}: {str(e)}")
                    dividend_info["status"] = "error"
                    dividend_info["error"] = str(e)
            else:
                dividend_info["status"] = "dry_run"
                processed += 1
            
            processed_dividends.append(dividend_info)
        
        return {
            "portfolio_id": str(portfolio_id),
            "holdings_count": len(holdings),
            "dividends_found": len(dividends),
            "dividends_processed": processed,
            "dividends_skipped": skipped,
            "errors": errors,
            "dry_run": dry_run,
            "dividends": processed_dividends[:10]  # Return first 10 for preview
        }
    
    async def sync_splits(
        self,
        portfolio_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Sync stock split announcements from FMP for portfolio holdings.
        
        Args:
            portfolio_id: Portfolio UUID
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: 30 days future)
            dry_run: If True, don't record splits, just return what would be processed
            
        Returns:
            Dict with sync results
        """
        # Default date range
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today() + timedelta(days=30)
            
        logger.info(f"Syncing splits for portfolio {portfolio_id} from {from_date} to {to_date}")
        
        # Get portfolio holdings for the date range
        holdings = await self._get_portfolio_holdings(portfolio_id, from_date, to_date)
        if not holdings:
            logger.info("No holdings found in portfolio")
            return {
                "portfolio_id": str(portfolio_id),
                "holdings_count": 0,
                "splits_processed": 0,
                "splits_skipped": 0,
                "errors": []
            }
        
        # Initialize FMP provider
        api_key = os.getenv("FMP_API_KEY")
        if not api_key:
            return {
                "portfolio_id": str(portfolio_id),
                "error": "FMP_API_KEY not configured",
                "holdings_count": len(holdings)
            }
        
        provider = FMPProvider(api_key=api_key)
        
        # Fetch split calendar from FMP
        try:
            splits = await provider.get_split_calendar(from_date, to_date)
        except Exception as e:
            logger.error(f"Failed to fetch split calendar: {e}")
            return {
                "portfolio_id": str(portfolio_id),
                "error": f"FMP API error: {str(e)}",
                "holdings_count": len(holdings)
            }
        
        # Process splits for our holdings
        processed = 0
        skipped = 0
        errors = []
        processed_splits = []
        
        for split in splits:
            symbol = split.get("symbol")
            if symbol not in holdings:
                continue  # Skip if we don't hold this stock
                
            # Extract split details
            split_date = datetime.strptime(split["effectiveDate"], "%Y-%m-%d").date()
            
            # Parse ratio (e.g., "2:1" -> 2.0)
            ratio_str = split.get("ratio", "1:1")
            try:
                new_shares, old_shares = ratio_str.split(":")
                ratio = Decimal(new_shares) / Decimal(old_shares)
            except:
                logger.warning(f"Invalid split ratio format: {ratio_str}")
                continue
            
            # Check if split already recorded
            if await self._check_split_exists(portfolio_id, symbol, split_date, ratio):
                logger.debug(f"Split already recorded: {symbol} {split_date} {ratio}:1")
                skipped += 1
                continue
            
            # Check if we held shares on split date
            shares = await self._get_shares_on_date(portfolio_id, symbol, split_date)
            if shares <= 0:
                logger.debug(f"No shares held on split date: {symbol} {split_date}")
                skipped += 1
                continue
            
            split_info = {
                "symbol": symbol,
                "split_ratio": float(ratio),
                "split_date": split_date.isoformat(),
                "shares_before": float(shares),
                "shares_after": float(shares * ratio)
            }
            
            if not dry_run:
                try:
                    # Record the split
                    result = await self.ca_service.record_split(
                        portfolio_id=portfolio_id,
                        symbol=symbol,
                        split_ratio=ratio,
                        split_date=split_date,
                        notes=f"Auto-synced from FMP on {date.today()}: {ratio_str} split"
                    )
                    processed += 1
                    split_info["status"] = "recorded"
                except Exception as e:
                    logger.error(f"Failed to record split for {symbol}: {e}")
                    errors.append(f"{symbol}: {str(e)}")
                    split_info["status"] = "error"
                    split_info["error"] = str(e)
            else:
                split_info["status"] = "dry_run"
                processed += 1
            
            processed_splits.append(split_info)
        
        return {
            "portfolio_id": str(portfolio_id),
            "holdings_count": len(holdings),
            "splits_found": len(splits),
            "splits_processed": processed,
            "splits_skipped": skipped,
            "errors": errors,
            "dry_run": dry_run,
            "splits": processed_splits[:10]  # Return first 10 for preview
        }
    
    async def sync_all(
        self,
        portfolio_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Sync both dividends and splits for a portfolio.
        
        Args:
            portfolio_id: Portfolio UUID
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: 30 days future)
            dry_run: If True, don't record actions, just return what would be processed
            
        Returns:
            Combined sync results
        """
        dividends_result = await self.sync_dividends(portfolio_id, from_date, to_date, dry_run)
        splits_result = await self.sync_splits(portfolio_id, from_date, to_date, dry_run)
        
        return {
            "portfolio_id": str(portfolio_id),
            "sync_date": date.today().isoformat(),
            "date_range": {
                "from": (from_date or date.today() - timedelta(days=30)).isoformat(),
                "to": (to_date or date.today() + timedelta(days=30)).isoformat()
            },
            "dry_run": dry_run,
            "dividends": dividends_result,
            "splits": splits_result
        }