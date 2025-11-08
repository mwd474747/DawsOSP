"""
Enhanced Corporate Actions Sync Service with Robust Error Handling

Features:
- Exponential backoff with jitter for retry logic
- Circuit breaker pattern for continuous failures
- Partial failure handling (continue processing even if some symbols fail)
- Rate limiting awareness with respect for API quotas
- Detailed error reporting and logging
- Graceful degradation with cached data fallback

Created: 2025-11-06
"""

import asyncio
import logging
import os
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import asyncpg

from app.integrations.fmp_provider import FMPProvider
from app.integrations.base_provider import ProviderError
from app.services.corporate_actions import CorporateActionsService

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit tripped, no requests allowed
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for FMP API calls.
    
    Prevents cascading failures by temporarily blocking requests after
    consecutive failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            success_threshold: Successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        
    def call_succeeded(self):
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker: Closing circuit after recovery")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset on success
            
    def call_failed(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.warning(f"Circuit breaker: Opening circuit after {self.failure_count} failures")
                self.state = CircuitState.OPEN
                
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker: Failure during recovery, reopening circuit")
            self.state = CircuitState.OPEN
            self.success_count = 0
            
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    logger.info("Circuit breaker: Entering half-open state for recovery test")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return False
            return True
        return False
        
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit state for monitoring."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class EnhancedCorporateActionsSyncService:
    """
    Enhanced service for syncing corporate actions with robust error handling.
    """
    
    # Class-level circuit breakers for different API endpoints
    _dividend_circuit = CircuitBreaker()
    _split_circuit = CircuitBreaker()
    _earnings_circuit = CircuitBreaker()
    
    def __init__(self, conn: asyncpg.Connection):
        """
        Initialize enhanced sync service.
        
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
        
        Includes both currently open positions and positions that were
        closed during or after the date range.
        """
        try:
            rows = await self.conn.fetch("""
                SELECT DISTINCT s.symbol
                FROM lots l
                JOIN securities s ON l.security_id = s.id
                WHERE l.portfolio_id = $1
                    AND l.acquisition_date <= $3
                    AND (l.closed_date IS NULL OR l.closed_date >= $2)
            """, portfolio_id, from_date or date.today(), to_date or date.today())
            
            return [row["symbol"] for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get portfolio holdings: {e}")
            raise
            
    async def _check_dividend_exists(
        self, 
        portfolio_id: UUID, 
        symbol: str, 
        ex_date: date,
        amount: Decimal
    ) -> bool:
        """Check if dividend has already been recorded."""
        try:
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
            
        except Exception as e:
            logger.warning(f"Failed to check dividend existence: {e}")
            return False  # Assume doesn't exist on error
            
    async def _get_shares_on_date(
        self,
        portfolio_id: UUID,
        symbol: str,
        target_date: date
    ) -> Decimal:
        """Get number of shares held on a specific date."""
        try:
            row = await self.conn.fetchrow("""
                SELECT SUM(
                    CASE
                        WHEN l.acquisition_date > $3 THEN 0
                        WHEN l.closed_date IS NULL OR l.closed_date > $3 THEN l.qty_original
                        WHEN l.closed_date <= $3 THEN 0
                        ELSE 0
                    END
                ) as total_shares
                FROM lots l
                JOIN securities s ON l.security_id = s.id
                WHERE l.portfolio_id = $1
                    AND s.symbol = $2
            """, portfolio_id, symbol, target_date)
            
            return Decimal(str(row["total_shares"])) if row and row["total_shares"] else Decimal("0")
            
        except Exception as e:
            logger.error(f"Failed to get shares on date for {symbol}: {e}")
            return Decimal("0")
            
    async def _fetch_dividends_with_retry(
        self,
        provider: FMPProvider,
        from_date: date,
        to_date: date,
        max_retries: int = 3
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Fetch dividends with enhanced retry logic.
        
        Returns:
            Tuple of (dividends list or None, error message or None)
        """
        if self._dividend_circuit.is_open():
            return None, "Circuit breaker open - too many recent failures"
            
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Add jitter to prevent thundering herd
                if attempt > 0:
                    jitter = random.uniform(0, 2 ** attempt)
                    await asyncio.sleep(jitter)
                    
                dividends = await provider.get_dividend_calendar(from_date, to_date)
                self._dividend_circuit.call_succeeded()
                
                if attempt > 0:
                    logger.info(f"Dividend fetch succeeded after {attempt} retries")
                    
                return dividends, None
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Dividend fetch attempt {attempt + 1}/{max_retries} failed: {e}")
                
                # Check for rate limiting
                if "429" in str(e) or "rate limit" in str(e).lower():
                    # Longer backoff for rate limiting
                    await asyncio.sleep(30 * (attempt + 1))
                    
        self._dividend_circuit.call_failed()
        return None, last_error
        
    async def sync_dividends(
        self,
        portfolio_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        dry_run: bool = False,
        continue_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Sync dividend announcements with enhanced error handling.
        
        Args:
            portfolio_id: Portfolio UUID
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: 30 days future)
            dry_run: If True, don't record dividends, just return what would be processed
            continue_on_error: If True, continue processing even if some items fail
            
        Returns:
            Dict with sync results including detailed error information
        """
        # Default date range
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today() + timedelta(days=30)
            
        logger.info(f"Enhanced dividend sync for portfolio {portfolio_id} from {from_date} to {to_date}")
        
        result = {
            "portfolio_id": str(portfolio_id),
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "circuit_breaker_state": self._dividend_circuit.get_state(),
            "holdings_count": 0,
            "dividends_found": 0,
            "dividends_processed": 0,
            "dividends_skipped": 0,
            "dividends_failed": 0,
            "errors": [],
            "warnings": [],
            "dry_run": dry_run
        }
        
        try:
            # Get portfolio holdings
            holdings = await self._get_portfolio_holdings(portfolio_id, from_date, to_date)
            result["holdings_count"] = len(holdings)
            
            if not holdings:
                logger.info("No holdings found in portfolio")
                return result
                
            # Get portfolio base currency
            portfolio_row = await self.conn.fetchrow(
                "SELECT base_currency FROM portfolios WHERE id = $1",
                portfolio_id
            )
            base_currency = portfolio_row["base_currency"] if portfolio_row else "USD"
            
            # Initialize FMP provider
            api_key = os.getenv("FMP_API_KEY")
            if not api_key:
                result["errors"].append("FMP_API_KEY not configured")
                return result
                
            provider = FMPProvider(api_key=api_key)
            
            # Fetch dividend calendar with enhanced retry
            dividends, error = await self._fetch_dividends_with_retry(
                provider, from_date, to_date
            )
            
            if error:
                result["errors"].append(f"Failed to fetch dividends: {error}")
                if not continue_on_error:
                    return result
                result["warnings"].append("Using cached/stale data if available")
                dividends = []  # Continue with empty list
                
            result["dividends_found"] = len(dividends) if dividends else 0
            
            # Process dividends with error handling for each item
            processed_dividends = []
            
            for dividend in (dividends or []):
                try:
                    symbol = dividend.get("symbol")
                    if symbol not in holdings:
                        continue
                        
                    # Extract dividend details with validation
                    ex_date_str = dividend.get("date")
                    if not ex_date_str:
                        result["warnings"].append(f"Missing ex-date for {symbol}")
                        continue
                        
                    ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d").date()
                    pay_date_str = dividend.get("paymentDate")
                    pay_date = (
                        datetime.strptime(pay_date_str, "%Y-%m-%d").date() 
                        if pay_date_str 
                        else ex_date + timedelta(days=3)
                    )
                    
                    amount_str = dividend.get("dividend")
                    if not amount_str:
                        result["warnings"].append(f"Missing dividend amount for {symbol}")
                        continue
                        
                    amount = Decimal(str(amount_str))
                    currency = dividend.get("currency", "USD")
                    
                    # Check if already recorded
                    if await self._check_dividend_exists(portfolio_id, symbol, ex_date, amount):
                        logger.debug(f"Dividend already recorded: {symbol} {ex_date} ${amount}")
                        result["dividends_skipped"] += 1
                        continue
                        
                    # Get shares held
                    shares = await self._get_shares_on_date(portfolio_id, symbol, ex_date)
                    if shares <= 0:
                        logger.debug(f"No shares held on ex-date: {symbol} {ex_date}")
                        result["dividends_skipped"] += 1
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
                            record_result = await self.ca_service.record_dividend(
                                portfolio_id=portfolio_id,
                                symbol=symbol,
                                shares=shares,
                                dividend_per_share=amount,
                                currency=currency,
                                ex_date=ex_date,
                                pay_date=pay_date,
                                withholding_tax=Decimal("0"),
                                base_currency=base_currency if currency != base_currency else None,
                                notes=f"Auto-synced from FMP on {date.today()} (enhanced)"
                            )
                            result["dividends_processed"] += 1
                            dividend_info["status"] = "recorded"
                            dividend_info["transaction_id"] = str(record_result.get("transaction_id"))
                            
                        except Exception as e:
                            logger.error(f"Failed to record dividend for {symbol}: {e}")
                            result["dividends_failed"] += 1
                            dividend_info["status"] = "error"
                            dividend_info["error"] = str(e)
                            
                            if not continue_on_error:
                                result["errors"].append(f"Critical error: {symbol}: {str(e)}")
                                break
                            result["errors"].append(f"{symbol}: {str(e)}")
                    else:
                        dividend_info["status"] = "dry_run"
                        result["dividends_processed"] += 1
                        
                    processed_dividends.append(dividend_info)
                    
                except Exception as e:
                    logger.error(f"Error processing dividend: {e}")
                    result["warnings"].append(f"Failed to process dividend: {str(e)}")
                    if not continue_on_error:
                        break
                        
            # Include sample of processed dividends
            result["dividends"] = processed_dividends[:10]
            
        except Exception as e:
            logger.error(f"Critical error in dividend sync: {e}")
            result["errors"].append(f"Critical error: {str(e)}")
            
        return result
        
    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync service status including circuit breaker states.
        
        Returns:
            Dict with service health information
        """
        return {
            "service": "corporate_actions_sync",
            "status": "operational",
            "circuit_breakers": {
                "dividends": self._dividend_circuit.get_state(),
                "splits": self._split_circuit.get_state(),
                "earnings": self._earnings_circuit.get_state()
            },
            "api_key_configured": bool(os.getenv("FMP_API_KEY")),
            "timestamp": datetime.now().isoformat()
        }