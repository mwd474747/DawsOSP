"""
Alert Evaluation Service

Purpose: Evaluate user-defined alert conditions against portfolio metrics
Updated: 2025-01-15 (Phase 1: Exception handling improvements)
Priority: P1 (Core business logic for alert evaluation)

**Architecture Note:** This service is an implementation detail of the MacroHound agent.
Patterns should use `macro_hound` agent capabilities (e.g., `macro_hound.suggest_alert_presets`),
not this service directly. The service is used internally by MacroHound to implement
alert evaluation logic.

**Production Guard:** Stub mode (use_db=False) is prevented in production environments.

Features:
    - Condition evaluation (macro, metric, rating, price, news_sentiment)
    - Cooldown enforcement (prevent notification spam)
    - Value retrieval from database
    - Support for multiple operators (>, <, >=, <=, ==, !=)

Alert Condition Types:
    - macro: VIX > 30, unemployment < 4%
    - metric: max_drawdown_1y > 0.15, sharpe_1y < 1.0
    - rating: dividend_safety < 6, quality_score < 7
    - price: AAPL price < 150, AAPL change_pct > 0.05
    - news_sentiment: AAPL sentiment < -0.5

Usage:
    from app.services.alerts import AlertService

    alert_svc = AlertService()

    # Evaluate condition
    condition = {
        "type": "macro",
        "entity": "VIX",
        "metric": "level",
        "op": ">",
        "value": 30,
        "window": "intraday"
    }

    ctx = {"asof_date": date.today()}
    result = await alert_svc.evaluate_condition(condition, ctx)

    # Check if alert should trigger
    alert = {"id": "...", "condition_json": condition, "cooldown_hours": 24, "last_fired_at": ...}
    should_trigger = await alert_svc.should_trigger(alert, ctx)
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.services.notifications import NotificationService
from app.services.alert_delivery import AlertDeliveryService
from app.core.exceptions import DatabaseError, ExternalAPIError
from app.core.constants.validation import (
    DEFAULT_ALERT_COOLDOWN_HOURS,
    DEFAULT_ALERT_LOOKBACK_HOURS,
    MOCK_DATA_RANDOM_MIN,
    MOCK_DATA_RANDOM_MAX,
)
from app.services.alert_validation import (
    validate_portfolio_metric_name,
    validate_rating_metric_name,
    validate_price_metric_name,
    validate_uuid,
    validate_symbol,
)

logger = logging.getLogger("DawsOS.Alerts")


class AlertService:
    """
    Alert evaluation service.

    **Architecture Note:** This service is an implementation detail of the MacroHound agent.
    Patterns should use `macro_hound` agent capabilities, not this service directly.

    Evaluates user-defined conditions against:
    - Macro indicators (VIX, unemployment, rates)
    - Portfolio metrics (TWR, Sharpe, drawdown)
    - Security ratings (quality, dividend safety)
    - Prices (equity quotes, price changes)
    - News sentiment
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize alert service.

        **Architecture Note:** This service is an implementation detail of the MacroHound agent.
        Patterns should use `macro_hound` agent capabilities, not this service directly.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
            
        Raises:
            ValueError: If use_db=False in production environment
        """
        import os
        
        # Production guard: prevent stub mode in production
        if not use_db and os.getenv("ENVIRONMENT") == "production":
            raise ValueError(
                "Cannot use stub mode (use_db=False) in production environment. "
                "Stub mode is only available for development and testing."
            )
        
        self.use_db = use_db

        if use_db:
            try:
                from app.db.connection import execute_query_one, execute_query
                from app.db.metrics_queries import get_metrics_queries

                self.execute_query_one = execute_query_one
                self.execute_query = execute_query
                self.metrics_queries = get_metrics_queries()
                logger.info("AlertService initialized with database integration")

            except (ValueError, TypeError, KeyError, AttributeError) as e:
                # Programming errors - should not happen, log and re-raise
                logger.error(f"Programming error in database initialization: {e}", exc_info=True)
                raise
            except Exception as e:
                # Database connection errors - handle based on environment
                import os
                if os.getenv("ENVIRONMENT") == "production":
                    logger.error(f"Failed to initialize database connections in production: {e}", exc_info=True)
                    raise DatabaseError(f"Failed to initialize database connections in production: {e}", retryable=True) from e
                # Only fall back to stub mode in development/testing
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode (development/testing only)."
                )
                # Don't raise DatabaseError here - graceful degradation is intentional
                self.use_db = False
        else:
            import os
            if os.getenv("ENVIRONMENT") != "production":
                logger.info("AlertService initialized in stub mode (development/testing only)")
            else:
                # This should never happen due to production guard above, but log if it does
                logger.error("AlertService stub mode attempted in production - this should be prevented by production guard")

    async def evaluate_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate alert condition.

        Args:
            condition: Alert condition JSON
            ctx: Evaluation context (asof_date, portfolio_id, etc.)

        Returns:
            True if condition is met, False otherwise

        Example condition:
            {
                "type": "macro",
                "entity": "VIX",
                "metric": "level",
                "op": ">",
                "value": 30,
                "window": "intraday"
            }
        """
        condition_type = condition.get("type")

        if condition_type == "macro":
            return await self._evaluate_macro_condition(condition, ctx)
        elif condition_type == "metric":
            return await self._evaluate_metric_condition(condition, ctx)
        elif condition_type == "rating":
            return await self._evaluate_rating_condition(condition, ctx)
        elif condition_type == "price":
            return await self._evaluate_price_condition(condition, ctx)
        elif condition_type == "news_sentiment":
            return await self._evaluate_news_sentiment_condition(condition, ctx)
        elif condition_type == "dar_breach":
            return await self._evaluate_dar_breach_condition(condition, ctx)
        elif condition_type == "drawdown_limit":
            return await self._evaluate_drawdown_limit_condition(condition, ctx)
        elif condition_type == "regime_shift":
            return await self._evaluate_regime_shift_condition(condition, ctx)
        else:
            logger.warning(f"Unknown condition type: {condition_type}")
            return False

    async def get_alert_value(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Optional[Decimal]:
        """
        Get current value for alert condition (for notifications).

        Args:
            condition: Alert condition JSON
            ctx: Evaluation context

        Returns:
            Current value or None if unavailable
        """
        condition_type = condition.get("type")

        if condition_type == "macro":
            return await self._get_macro_value(condition, ctx)
        elif condition_type == "metric":
            return await self._get_metric_value(condition, ctx)
        elif condition_type == "rating":
            return await self._get_rating_value(condition, ctx)
        elif condition_type == "price":
            return await self._get_price_value(condition, ctx)
        elif condition_type == "news_sentiment":
            return await self._get_news_sentiment_value(condition, ctx)
        else:
            return None

    async def should_trigger(
        self,
        alert: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Check if alert should trigger.

        Combines condition evaluation + cooldown check.

        Args:
            alert: Alert record from database
            ctx: Evaluation context

        Returns:
            True if alert should trigger, False otherwise
        """
        # Evaluate condition
        condition = alert.get("condition_json", {})
        condition_met = await self.evaluate_condition(condition, ctx)

        if not condition_met:
            return False

        # Check cooldown
        last_fired_at = alert.get("last_fired_at")
        cooldown_hours = alert.get("cooldown_hours", DEFAULT_ALERT_COOLDOWN_HOURS)

        cooldown_passed = self.check_cooldown(
            alert_id=alert.get("id"),
            last_fired_at=last_fired_at,
            cooldown_hours=cooldown_hours,
        )

        return cooldown_passed

    def check_cooldown(
        self,
        alert_id: str,
        last_fired_at: Optional[datetime],
        cooldown_hours: int = DEFAULT_ALERT_COOLDOWN_HOURS,
    ) -> bool:
        """
        Check if cooldown period has passed.

        Args:
            alert_id: Alert ID (for logging)
            last_fired_at: Last time alert was triggered
            cooldown_hours: Cooldown period in hours

        Returns:
            True if cooldown passed (can send notification), False otherwise
        """
        if last_fired_at is None:
            # Never fired before
            return True

        # Compute time since last fire
        now = datetime.utcnow()
        time_since_fire = now - last_fired_at
        cooldown_delta = timedelta(hours=cooldown_hours)

        if time_since_fire >= cooldown_delta:
            logger.debug(
                f"Alert {alert_id}: cooldown passed "
                f"({time_since_fire.total_seconds() / 3600:.1f}h > {cooldown_hours}h)"
            )
            return True
        else:
            remaining = (cooldown_delta - time_since_fire).total_seconds() / 3600
            logger.debug(
                f"Alert {alert_id}: cooldown active "
                f"({remaining:.1f}h remaining)"
            )
            return False

    def normalize_channels(self, alert: Dict[str, Any]) -> Dict[str, bool]:
        """
        Normalize alert channels to unified format.

        Supports both legacy format (notify_email, notify_inapp booleans)
        and new format (channels JSONB dict).

        Args:
            alert: Alert configuration dict

        Returns:
            Channels dict {"inapp": bool, "email": bool}
        """
        # Check for new format first
        if "channels" in alert:
            return alert["channels"]

        # Fall back to legacy format
        return {
            "inapp": alert.get("notify_inapp", True),
            "email": alert.get("notify_email", False),
        }

    async def deliver_alert(
        self,
        alert: Dict[str, Any],
        user_id: str,
        message: str,
    ) -> bool:
        """
        Deliver alert to user via configured channels.

        Includes delivery tracking and DLQ integration.

        Args:
            alert: Alert configuration dict (includes id, name, condition)
                   Channels can be specified as:
                   - "channels": {"inapp": True, "email": False} (new format)
                   - "notify_inapp": True, "notify_email": False (legacy format)
            user_id: User UUID
            message: Alert message to deliver

        Returns:
            True if delivery succeeded, False otherwise

        Usage:
            # New format
            alert = {
                "id": "alert-123",
                "name": "VIX Alert",
                "condition_json": {...},
                "channels": {"inapp": True, "email": False}
            }
            success = await alert_service.deliver_alert(alert, user_id, "VIX exceeded 30")

            # Legacy format (from database)
            alert = {
                "id": "alert-123",
                "name": "VIX Alert",
                "condition_json": {...},
                "notify_inapp": True,
                "notify_email": False
            }
            success = await alert_service.deliver_alert(alert, user_id, "VIX exceeded 30")
        """
        alert_id = alert.get("id")
        alert_name = alert.get("name", "Alert")
        channels = self.normalize_channels(alert)

        logger.info(
            f"Delivering alert {alert_id} to user {user_id} "
            f"(channels: {channels})"
        )

        # Get delivery service for tracking and DLQ
        delivery_service = AlertDeliveryService(use_db=self.use_db)

        # Check for duplicate delivery (content-based)
        alert_data = {
            "condition": alert.get("condition_json"),
            "message": message,
            "user_id": user_id,
        }
        content_hash = delivery_service.compute_content_hash(alert_data)

        is_duplicate = await delivery_service.check_duplicate_delivery(
            alert_id=alert_id,
            content_hash=content_hash,
            lookback_hours=DEFAULT_ALERT_LOOKBACK_HOURS,
        )

        if is_duplicate:
            logger.warning(
                f"Alert {alert_id} already delivered recently "
                "(content-based deduplication)"
            )
            return False

        # Get notification service
        notification_service = NotificationService(use_db=self.use_db)

        # Send notification with DLQ error handling
        try:
            success = await notification_service.send_notification(
                user_id=user_id,
                alert_id=alert_id,
                message=message,
                channels=channels,
                alert_name=alert_name,
            )

            if success:
                # Track successful delivery
                await delivery_service.track_delivery(
                    alert_id=alert_id,
                    alert_data=alert_data,
                    delivery_methods=[k for k, v in channels.items() if v],
                )
                logger.info(f"Alert {alert_id} delivered successfully to user {user_id}")
            else:
                logger.warning(
                    f"Alert {alert_id} not delivered (deduplication or channel unavailable)"
                )

            return success

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in alert delivery: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service/API errors - push to DLQ for retry
            logger.error(f"Failed to deliver alert {alert_id}: {e}", exc_info=True)
            # Don't raise exception here - push to DLQ is intentional
            await delivery_service.push_to_dlq(
                alert_id=alert_id,
                alert_data=alert_data,
                error_message=str(e),
            )

            # Re-raise for caller to handle
            raise

    # ========================================================================
    # Macro Condition Evaluation
    # ========================================================================

    async def _evaluate_macro_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate macro indicator condition.

        Example:
            {"type": "macro", "entity": "VIX", "metric": "level", "op": ">", "value": 30}
        """
        value = await self._get_macro_value(condition, ctx)

        if value is None:
            logger.warning(f"Macro value not available: {condition}")
            return False

        threshold = Decimal(str(condition.get("value", 0)))
        operator = condition.get("op", ">")

        return self._compare_values(value, operator, threshold)

    async def _get_macro_value(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Optional[Decimal]:
        """Get macro indicator value from database."""
        if not self.use_db:
            # Stub: return random value (for testing only)
            import random
            return Decimal(str(random.uniform(10, 50)))

        entity = condition.get("entity")  # VIX, DGS10, UNRATE, etc.
        asof_date = ctx.get("asof_date", date.today())

        # Map entity to FRED series ID
        series_map = {
            "VIX": "VIXCLS",
            "DGS10": "DGS10",
            "DGS2": "DGS2",
            "UNRATE": "UNRATE",
            "CPI": "CPIAUCSL",
            "T10YIE": "T10YIE",
            "DFII10": "DFII10",
            "BAMLC0A0CM": "BAMLC0A0CM",
            "DTWEXBGS": "DTWEXBGS",
        }

        series_id = series_map.get(entity, entity)

        # Query macro_indicators table
        query = """
            SELECT value
            FROM macro_indicators
            WHERE series_id = $1
              AND asof_date <= $2
            ORDER BY asof_date DESC
            LIMIT 1
        """

        try:
            row = await self.execute_query_one(query, series_id, asof_date)
            if row and row["value"] is not None:
                return Decimal(str(row["value"]))
            else:
                logger.warning(f"Macro indicator not found: {series_id}")
                return None
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in get_macro_value for {series_id}: {e}", exc_info=True)
            raise
        except Exception as e:
            # Database or other service errors - log and return None (graceful degradation)
            logger.error(f"Failed to get macro value for {series_id}: {e}")
            # Don't raise DatabaseError here - graceful degradation is intentional
            return None

    # ========================================================================
    # Metric Condition Evaluation
    # ========================================================================

    async def _evaluate_metric_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate portfolio metric condition.

        Example:
            {"type": "metric", "portfolio_id": "portfolio-uuid-here", "metric": "max_drawdown_1y", "op": ">", "value": 0.15}
        """
        value = await self._get_metric_value(condition, ctx)

        if value is None:
            # Log detailed context about why value is None
            logger.warning(
                f"Metric value not available for condition: {condition}. "
                f"This may indicate missing data, calculation error, or database issue. "
                f"Check portfolio_id={condition.get('portfolio_id')}, metric={condition.get('metric')}"
            )
            return False

        threshold = Decimal(str(condition.get("value", 0)))
        operator = condition.get("op", ">")

        return self._compare_values(value, operator, threshold)

    async def _get_metric_value(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Optional[Decimal]:
        """Get portfolio metric value from database."""
        if not self.use_db:
            # Stub: return random value (for testing only)
            import random
            return Decimal(str(random.uniform(MOCK_DATA_RANDOM_MIN, MOCK_DATA_RANDOM_MAX)))

        portfolio_id = condition.get("portfolio_id")
        metric_name = condition.get("metric")  # twr_ytd, sharpe_1y, max_drawdown_1y, etc.
        asof_date = ctx.get("asof_date", date.today())

        # Validate inputs to prevent SQL injection
        if not portfolio_id or not metric_name:
            logger.warning(f"Invalid metric condition: {condition}")
            return None
        
        if not validate_uuid(portfolio_id):
            logger.warning(f"Invalid portfolio_id format: {portfolio_id}")
            return None
        
        if not validate_portfolio_metric_name(metric_name):
            logger.warning(f"Invalid metric name (potential SQL injection attempt): {metric_name}")
            return None

        # Query portfolio_metrics table
        # Column name validated against whitelist to prevent SQL injection
        query = f"""
            SELECT {metric_name}
            FROM portfolio_metrics
            WHERE portfolio_id = $1::uuid
              AND asof_date <= $2
            ORDER BY asof_date DESC
            LIMIT 1
        """

        try:
            row = await self.execute_query_one(query, portfolio_id, asof_date)
            if row and row[metric_name] is not None:
                return Decimal(str(row[metric_name]))
            else:
                logger.warning(f"Metric not found: {metric_name} for portfolio {portfolio_id}")
                return None
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in get_metric_value for {portfolio_id}.{metric_name}: {e}", exc_info=True)
            raise
        except Exception as e:
            # Database or other service errors - log and return None (graceful degradation)
            logger.error(f"Failed to get metric value for {portfolio_id}.{metric_name}: {e}")
            return None

    # ========================================================================
    # Rating Condition Evaluation
    # ========================================================================

    async def _evaluate_rating_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate security rating condition.

        Example:
            {"type": "rating", "portfolio_id": "portfolio-uuid-here", "symbol": "AAPL", "metric": "dividend_safety", "op": "<", "value": 6}
        """
        value = await self._get_rating_value(condition, ctx)

        if value is None:
            # Log detailed context about why value is None
            logger.warning(
                f"Rating value not available for condition: {condition}. "
                f"This may indicate missing data, calculation error, or database issue. "
                f"Check portfolio_id={condition.get('portfolio_id')}, symbol={condition.get('symbol')}, "
                f"metric={condition.get('metric')}"
            )
            return False

        threshold = Decimal(str(condition.get("value", 0)))
        operator = condition.get("op", "<")

        return self._compare_values(value, operator, threshold)

    async def _get_rating_value(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Optional[Decimal]:
        """Get security rating value from database."""
        if not self.use_db:
            # Stub: return random value (0-10 scale) (acceptable for deprecated service)
            # Note: This service is deprecated and will be removed once migration to MacroHound is complete
            import random
            return Decimal(str(random.randint(0, 10)))

        symbol = condition.get("symbol")
        metric_name = condition.get("metric")  # dividend_safety, quality_score, moat_score, etc.
        asof_date = ctx.get("asof_date", date.today())

        # Validate inputs to prevent SQL injection
        if not symbol or not metric_name:
            logger.warning(f"Invalid rating condition: {condition}")
            return None
        
        if not validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
        
        if not validate_rating_metric_name(metric_name):
            logger.warning(f"Invalid rating metric name (potential SQL injection attempt): {metric_name}")
            return None

        # Query security_ratings table
        # TODO: Create security_ratings table in schema
        # Column name validated against whitelist to prevent SQL injection
        query = f"""
            SELECT {metric_name}
            FROM security_ratings
            WHERE symbol = $1
              AND asof_date <= $2
            ORDER BY asof_date DESC
            LIMIT 1
        """

        try:
            row = await self.execute_query_one(query, symbol, asof_date)
            if row and row[metric_name] is not None:
                return Decimal(str(row[metric_name]))
            else:
                logger.warning(f"Rating not found: {metric_name} for {symbol}")
                return None
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in get_rating_value for {symbol}.{metric_name}: {e}", exc_info=True)
            raise
        except Exception as e:
            # Database or other service errors - log and return None (graceful degradation)
            logger.error(f"Failed to get rating value for {symbol}.{metric_name}: {e}")
            return None

    # ========================================================================
    # Price Condition Evaluation
    # ========================================================================

    async def _evaluate_price_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate price condition.

        Example:
            {"type": "price", "symbol": "AAPL", "metric": "close", "op": "<", "value": 150}
            {"type": "price", "symbol": "AAPL", "metric": "change_pct", "op": ">", "value": 0.05}
        """
        value = await self._get_price_value(condition, ctx)

        if value is None:
            logger.warning(f"Price value not available: {condition}")
            return False

        threshold = Decimal(str(condition.get("value", 0)))
        operator = condition.get("op", ">")

        return self._compare_values(value, operator, threshold)

    async def _get_price_value(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Optional[Decimal]:
        """Get price value from database."""
        if not self.use_db:
            # Stub: return random value (for testing only)
            import random
            metric = condition.get("metric", "close")
            if metric == "change_pct":
                return Decimal(str(random.uniform(-0.10, 0.10)))
            else:
                return Decimal(str(random.uniform(100, 200)))

        symbol = condition.get("symbol")
        metric_name = condition.get("metric", "close")  # close, open, high, low, change_pct
        asof_date = ctx.get("asof_date", date.today())

        if not symbol:
            logger.warning(f"Invalid price condition: {condition}")
            return None

        # Query pricing_packs_prices table
        # Get latest pricing pack for asof_date
        # Use PricingService to find pack by date
        # Note: PricingService doesn't have get_pack_by_date(), so we query directly
        # but this is acceptable for alerts service as it's a date-based lookup
        pack_query = """
            SELECT id
            FROM pricing_packs
            WHERE date <= $1
            ORDER BY date DESC
            LIMIT 1
        """

        try:
            pack_row = await self.execute_query_one(pack_query, asof_date)
            if not pack_row:
                logger.warning(f"No pricing pack found for {asof_date}")
                return None

            # Validate pack_id using PricingService (from DI container)
            from app.core.di_container import get_container
            from app.core.service_initializer import initialize_services
            from app.db.connection import get_db_pool
            container = get_container()
            if not container._initialized:
                db_pool = get_db_pool()
                initialize_services(container, db_pool=db_pool)
            pricing_service = container.resolve("pricing")
            pack = await pricing_service.get_pack_by_id(pack_row["id"], raise_if_not_found=False)
            if not pack:
                logger.warning(f"Pricing pack {pack_row['id']} not found or invalid")
                return None

            pack_id = pack.id

            # Get price from pricing_packs_prices
            if metric_name == "change_pct":
                # Compute change_pct from close prices
                price_query = """
                    WITH prices AS (
                        SELECT symbol, close, date,
                               LAG(close) OVER (PARTITION BY symbol ORDER BY date) AS prev_close
                        FROM pricing_packs_prices
                        WHERE pack_id = $1
                          AND symbol = $2
                        ORDER BY date DESC
                        LIMIT 1
                    )
                    SELECT (close - prev_close) / prev_close AS change_pct
                    FROM prices
                    WHERE prev_close IS NOT NULL
                """
                row = await self.execute_query_one(price_query, pack_id, symbol)
                if row and row["change_pct"] is not None:
                    return Decimal(str(row["change_pct"]))
            else:
                # Validate metric name to prevent SQL injection
                if not validate_price_metric_name(metric_name):
                    logger.warning(f"Invalid price metric name (potential SQL injection attempt): {metric_name}")
                    return None
                
                # Get specific price field
                # Column name validated against whitelist to prevent SQL injection
                price_query = f"""
                    SELECT {metric_name}
                    FROM pricing_packs_prices
                    WHERE pack_id = $1
                      AND symbol = $2
                    LIMIT 1
                """
                row = await self.execute_query_one(price_query, pack_id, symbol)
                if row and row[metric_name] is not None:
                    return Decimal(str(row[metric_name]))

            logger.warning(f"Price not found: {symbol}.{metric_name}")
            return None

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in get_price_value for {symbol}.{metric_name}: {e}", exc_info=True)
            raise
        except Exception as e:
            # Database or other service errors - log and return None (graceful degradation)
            logger.error(f"Failed to get price value for {symbol}.{metric_name}: {e}")
            return None

    # ========================================================================
    # News Sentiment Condition Evaluation
    # ========================================================================

    async def _evaluate_news_sentiment_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate news sentiment condition.

        Example:
            {"type": "news_sentiment", "symbol": "AAPL", "metric": "sentiment", "op": "<", "value": -0.5}
        """
        value = await self._get_news_sentiment_value(condition, ctx)

        if value is None:
            logger.warning(f"News sentiment value not available: {condition}")
            return False

        threshold = Decimal(str(condition.get("value", 0)))
        operator = condition.get("op", "<")

        return self._compare_values(value, operator, threshold)

    async def _get_news_sentiment_value(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> Optional[Decimal]:
        """Get news sentiment value from database."""
        if not self.use_db:
            # Stub: return random value (-1 to 1) (acceptable for deprecated service)
            # Note: This service is deprecated and will be removed once migration to MacroHound is complete
            import random
            return Decimal(str(random.uniform(-1.0, 1.0)))

        symbol = condition.get("symbol")
        asof_date = ctx.get("asof_date", date.today())

        if not symbol:
            logger.warning(f"Invalid news sentiment condition: {condition}")
            return None

        # Query news_sentiment table
        # TODO: Create news_sentiment table in schema
        query = """
            SELECT AVG(sentiment_score) AS avg_sentiment
            FROM news_sentiment
            WHERE symbol = $1
              AND published_at >= $2 - INTERVAL '7 days'
              AND published_at <= $2
        """

        try:
            row = await self.execute_query_one(query, symbol, asof_date)
            if row and row["avg_sentiment"] is not None:
                return Decimal(str(row["avg_sentiment"]))
            else:
                logger.warning(f"News sentiment not found for {symbol}")
                return None
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in get_news_sentiment for {symbol}: {e}", exc_info=True)
            raise
        except Exception as e:
            # Database or other service errors - log and return None (graceful degradation)
            logger.error(f"Failed to get news sentiment for {symbol}: {e}")
            return None

    # ========================================================================
    # Comparison Operators
    # ========================================================================

    def _compare_values(
        self,
        value: Decimal,
        operator: str,
        threshold: Decimal,
    ) -> bool:
        """
        Compare value against threshold using operator.

        Args:
            value: Current value
            operator: Comparison operator (>, <, >=, <=, ==, !=)
            threshold: Threshold value

        Returns:
            True if comparison is true, False otherwise
        """
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    # ========================================================================
    # DaR Breach Condition Evaluation (ALERTS_ARCHITECT)
    # ========================================================================
    # Added: 2025-10-26
    # Purpose: Evaluate Drawdown at Risk threshold breaches
    # Source: Bridgewater risk framework, Dalio methodology
    # ========================================================================

    async def _evaluate_dar_breach_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate DaR breach condition.

        Computes current DaR for portfolio and checks if it exceeds threshold.

        Example:
            {
                "type": "dar_breach",
                "portfolio_id": "portfolio-uuid-here",
                "threshold": 0.15,  # 15%
                "confidence": 0.95,  # 95%
                "horizon_days": 30
            }
        """
        portfolio_id = condition.get("portfolio_id")
        threshold = Decimal(str(condition.get("threshold", 0.15)))
        confidence = condition.get("confidence", 0.95)
        horizon_days = condition.get("horizon_days", 30)

        if not portfolio_id:
            logger.warning("DaR breach condition missing portfolio_id")
            return False

        # Validate threshold using AlertThresholdValidator
        try:
            from app.core.alert_validators import AlertThresholdValidator
            AlertThresholdValidator.validate_threshold('dar_breach', threshold)
        except ValueError as e:
            logger.error(f"Invalid DaR threshold: {e}")
            return False

        # Compute DaR using scenarios service (from DI container)
        try:
            from app.core.di_container import get_container
            from app.core.service_initializer import initialize_services
            from app.db.connection import get_db_pool
            container = get_container()
            if not container._initialized:
                db_pool = get_db_pool()
                initialize_services(container, db_pool=db_pool)
            scenario_service = container.resolve("scenarios")
            macro_service = container.resolve("macro")

            # Detect current regime for conditioning
            asof_date = ctx.get("asof_date", date.today())
            try:
                regime_classification = await macro_service.detect_current_regime(asof_date=asof_date)
                regime = regime_classification.regime.value
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                # Programming errors - should not happen, log and use fallback
                logger.error(f"Programming error in regime detection: {e}", exc_info=True)
                regime = "MID_EXPANSION"
            except Exception as e:
                # Service errors - use fallback regime
                logger.warning(f"Could not detect regime: {e}")
                # Don't raise exception here - fallback regime is intentional
                regime = "MID_EXPANSION"

            # Compute DaR
            dar_result = await scenario_service.compute_dar(
                portfolio_id=portfolio_id,
                regime=regime,
                confidence=confidence,
                horizon_days=horizon_days,
                as_of_date=asof_date,
            )

            # Check for errors
            if "error" in dar_result or dar_result.get("dar_value") is None:
                logger.error(f"DaR computation failed: {dar_result.get('error')}")
                return False

            dar_value = abs(Decimal(str(dar_result["dar_value"])))  # DaR is negative, take absolute

            # Store DaR result in context for playbook generation
            ctx["dar_result"] = dar_result
            ctx["dar_actual"] = dar_value

            # Check if DaR exceeds threshold
            breach = dar_value > threshold
            if breach:
                logger.warning(
                    f"DaR breach detected: {dar_value:.2%} > {threshold:.2%} "
                    f"(worst scenario: {dar_result.get('worst_scenario')})"
                )

            return breach

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in DaR breach evaluation: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service errors - log and return False (graceful degradation)
            logger.error(f"Failed to evaluate DaR breach condition: {e}", exc_info=True)
            # Don't raise DatabaseError here - graceful degradation is intentional
            return False

    async def _evaluate_drawdown_limit_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate drawdown limit condition.

        Checks if current portfolio drawdown exceeds configured limit.

        Example:
            {
                "type": "drawdown_limit",
                "portfolio_id": "portfolio-uuid-here",
                "limit": 0.20  # 20%
            }
        """
        portfolio_id = condition.get("portfolio_id")
        limit = Decimal(str(condition.get("limit", 0.20)))

        if not portfolio_id:
            logger.warning("Drawdown limit condition missing portfolio_id")
            return False

        # Validate threshold
        try:
            from app.core.alert_validators import AlertThresholdValidator
            AlertThresholdValidator.validate_threshold('drawdown_limit', limit)
        except ValueError as e:
            logger.error(f"Invalid drawdown limit: {e}")
            return False

        # Query portfolio_metrics for current drawdown
        if not self.use_db:
            return False

        asof_date = ctx.get("asof_date", date.today())

        query = """
            SELECT max_drawdown_1y
            FROM portfolio_metrics
            WHERE portfolio_id = $1::uuid
              AND asof_date <= $2
            ORDER BY asof_date DESC
            LIMIT 1
        """

        try:
            row = await self.execute_query_one(query, portfolio_id, asof_date)
            if row and row["max_drawdown_1y"] is not None:
                current_drawdown = abs(Decimal(str(row["max_drawdown_1y"])))  # Drawdown is negative
                ctx["current_drawdown"] = current_drawdown

                breach = current_drawdown > limit
                if breach:
                    logger.warning(
                        f"Drawdown limit breach: {current_drawdown:.2%} > {limit:.2%}"
                    )
                return breach
            else:
                logger.warning(f"Drawdown not found for portfolio {portfolio_id}")
                return False

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in drawdown limit evaluation: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service errors - log and return False (graceful degradation)
            logger.error(f"Failed to evaluate drawdown limit: {e}")
            return False

    async def _evaluate_regime_shift_condition(
        self,
        condition: Dict[str, Any],
        ctx: Dict[str, Any],
    ) -> bool:
        """
        Evaluate regime shift condition.

        Detects if macro regime has shifted since last evaluation.

        Example:
            {
                "type": "regime_shift",
                "confidence": 0.90,  # 90% minimum confidence
                "min_distance": 2    # At least 2 regimes apart
            }
        """
        confidence_threshold = Decimal(str(condition.get("confidence", 0.90)))
        min_distance = condition.get("min_distance", 2)

        # Validate threshold
        try:
            from app.core.alert_validators import AlertThresholdValidator
            AlertThresholdValidator.validate_threshold('regime_shift', confidence_threshold)
        except ValueError as e:
            logger.error(f"Invalid regime shift confidence: {e}")
            return False

        # Detect current regime
        try:
            from app.services.macro import get_macro_service

            # Get macro service from DI container
            from app.core.di_container import get_container
            from app.core.service_initializer import initialize_services
            from app.db.connection import get_db_pool
            container = get_container()
            if not container._initialized:
                db_pool = get_db_pool()
                initialize_services(container, db_pool=db_pool)
            macro_service = container.resolve("macro")
            asof_date = ctx.get("asof_date", date.today())

            regime_classification = await macro_service.detect_current_regime(asof_date=asof_date)
            current_regime = regime_classification.regime.value
            confidence = Decimal(str(regime_classification.confidence))

            # Check confidence threshold
            if confidence < confidence_threshold:
                logger.debug(
                    f"Regime confidence {confidence:.2%} below threshold {confidence_threshold:.2%}"
                )
                return False

            # Get previous regime from database (last regime detection)
            if not self.use_db:
                return False

            query = """
                SELECT regime
                FROM regime_history
                WHERE asof_date < $1
                ORDER BY asof_date DESC
                LIMIT 1
            """

            row = await self.execute_query_one(query, asof_date)
            if row:
                previous_regime = row["regime"]
            else:
                # No previous regime - first detection
                logger.info("First regime detection - no shift to evaluate")
                return False

            # Check if regime shifted
            regime_shift = current_regime != previous_regime

            if regime_shift:
                # Optionally check regime distance (e.g., EARLY_EXPANSION → LATE_CONTRACTION = 4 regimes apart)
                # For now, just detect any shift
                logger.warning(
                    f"Regime shift detected: {previous_regime} → {current_regime} "
                    f"(confidence: {confidence:.2%})"
                )
                ctx["old_regime"] = previous_regime
                ctx["new_regime"] = current_regime
                ctx["regime_confidence"] = confidence

            return regime_shift

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in regime shift evaluation: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service errors - log and return False (graceful degradation)
            logger.error(f"Failed to evaluate regime shift: {e}", exc_info=True)
            return False

    # ========================================================================
    # Alert Delivery System (Legacy - Deprecated)
    # ========================================================================
    # NOTE: This legacy implementation is deprecated.
    # Use deliver_alert() (line 272) which integrates with NotificationService
    # and AlertDeliveryService for proper delivery tracking and DLQ management.
    # This method is kept for backward compatibility only.

    async def _deliver_alert_legacy(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        delivery_methods: List[str] = None,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Use deliver_alert() instead.

        Legacy alert delivery implementation (stub).

        Args:
            alert_id: Alert ID
            alert_data: Alert data including condition, context, etc.
            delivery_methods: List of delivery methods (email, sms, webhook)
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts

        Returns:
            Delivery result with status and details
        """
        if delivery_methods is None:
            delivery_methods = ["email"]  # Default delivery method

        # Check for duplicates
        if await self._is_duplicate_alert(alert_id, alert_data):
            logger.info(f"Duplicate alert detected: {alert_id}")
            return {
                "status": "duplicate",
                "alert_id": alert_id,
                "message": "Alert already delivered recently"
            }

        # Attempt delivery
        delivery_result = await self._attempt_delivery(
            alert_id, alert_data, delivery_methods
        )

        # Handle delivery failures
        if not delivery_result["success"]:
            if retry_count < max_retries:
                logger.warning(
                    f"Delivery failed for alert {alert_id}, retrying ({retry_count + 1}/{max_retries})"
                )
                # Schedule retry
                await self._schedule_retry(alert_id, alert_data, delivery_methods, retry_count + 1)
                return {
                    "status": "retry_scheduled",
                    "alert_id": alert_id,
                    "retry_count": retry_count + 1,
                    "message": f"Delivery failed, retry scheduled"
                }
            else:
                # Move to Dead Letter Queue
                logger.error(f"Alert {alert_id} failed after {max_retries} retries, moving to DLQ")
                await self._move_to_dlq(alert_id, alert_data, delivery_result["error"])
                return {
                    "status": "dlq",
                    "alert_id": alert_id,
                    "message": "Alert moved to Dead Letter Queue"
                }

        # Success - log delivery
        await self._log_delivery_success(alert_id, alert_data, delivery_result)
        return {
            "status": "delivered",
            "alert_id": alert_id,
            "delivery_methods": delivery_methods,
            "message": "Alert delivered successfully"
        }

    async def _is_duplicate_alert(self, alert_id: str, alert_data: Dict[str, Any]) -> bool:
        """
        Check if alert is a duplicate based on content and recent delivery.

        Args:
            alert_id: Alert ID
            alert_data: Alert data

        Returns:
            True if duplicate, False otherwise
        """
        try:
            # Create content hash for deduplication
            import hashlib
            import json
            
            content_hash = hashlib.md5(
                json.dumps(alert_data, sort_keys=True).encode()
            ).hexdigest()

            # Check recent deliveries (last 1 hour)
            query = """
                SELECT COUNT(*) as count
                FROM alert_deliveries
                WHERE alert_id = $1
                  AND content_hash = $2
                  AND delivered_at > NOW() - INTERVAL '1 hour'
            """

            if self.use_db:
                row = await self.execute_query_one(query, alert_id, content_hash)
                return row["count"] > 0
            else:
                # Stub mode - no deduplication
                return False

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in duplicate alert check: {e}", exc_info=True)
            raise
        except Exception as e:
            # Database errors - log and return False (assume not duplicate)
            logger.error(f"Failed to check duplicate alert: {e}")
            # Don't raise DatabaseError here - fail open is intentional
            return False

    async def _attempt_delivery(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        delivery_methods: List[str]
    ) -> Dict[str, Any]:
        """
        Attempt to deliver alert via specified methods.

        Args:
            alert_id: Alert ID
            alert_data: Alert data
            delivery_methods: List of delivery methods

        Returns:
            Delivery result with success status and details
        """
        delivery_results = []
        overall_success = True
        error_details = []

        for method in delivery_methods:
            try:
                if method == "email":
                    result = await self._deliver_email(alert_id, alert_data)
                elif method == "sms":
                    result = await self._deliver_sms(alert_id, alert_data)
                elif method == "webhook":
                    result = await self._deliver_webhook(alert_id, alert_data)
                else:
                    result = {"success": False, "error": f"Unknown delivery method: {method}"}

                delivery_results.append({
                    "method": method,
                    "success": result["success"],
                    "error": result.get("error")
                })

                if not result["success"]:
                    overall_success = False
                    error_details.append(f"{method}: {result.get('error', 'Unknown error')}")

            except (ValueError, TypeError, KeyError, AttributeError) as e:
                # Programming errors - should not happen, log and re-raise
                logger.error(f"Programming error in delivery method {method}: {e}", exc_info=True)
                raise
            except Exception as e:
                # Service/API errors - log and continue with other methods
                logger.error(f"Delivery method {method} failed: {e}")
                # Don't raise exception here - continue with other methods is intentional
                delivery_results.append({
                    "method": method,
                    "success": False,
                    "error": str(e)
                })
                overall_success = False
                error_details.append(f"{method}: {str(e)}")

        return {
            "success": overall_success,
            "results": delivery_results,
            "error": "; ".join(error_details) if error_details else None
        }

    async def _deliver_email(self, alert_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver alert via email.

        Args:
            alert_id: Alert ID
            alert_data: Alert data

        Returns:
            Delivery result
        """
        try:
            # TODO: Integrate with email service (SendGrid, SES, etc.)
            # For now, log the email content
            email_content = self._format_email_content(alert_id, alert_data)
            logger.info(f"EMAIL ALERT {alert_id}: {email_content}")
            
            return {"success": True, "message": "Email logged (not sent)"}
            
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in email delivery: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service/API errors - return error result
            logger.error(f"Email delivery failed: {e}")
            # Don't raise ExternalAPIError here - return error result is intentional
            return {"success": False, "error": str(e)}

    async def _deliver_sms(self, alert_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver alert via SMS.

        Args:
            alert_id: Alert ID
            alert_data: Alert data

        Returns:
            Delivery result
        """
        try:
            # TODO: Integrate with SMS service (Twilio, etc.)
            # For now, log the SMS content
            sms_content = self._format_sms_content(alert_id, alert_data)
            logger.info(f"SMS ALERT {alert_id}: {sms_content}")
            
            return {"success": True, "message": "SMS logged (not sent)"}
            
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in SMS delivery: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service/API errors - return error result
            logger.error(f"SMS delivery failed: {e}")
            return {"success": False, "error": str(e)}

    async def _deliver_webhook(self, alert_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver alert via webhook.

        Args:
            alert_id: Alert ID
            alert_data: Alert data

        Returns:
            Delivery result
        """
        try:
            # TODO: Implement webhook delivery
            # For now, log the webhook payload
            webhook_payload = self._format_webhook_payload(alert_id, alert_data)
            logger.info(f"WEBHOOK ALERT {alert_id}: {webhook_payload}")
            
            return {"success": True, "message": "Webhook logged (not sent)"}
            
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in webhook delivery: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service/API errors - return error result
            logger.error(f"Webhook delivery failed: {e}")
            return {"success": False, "error": str(e)}

    def _format_email_content(self, alert_id: str, alert_data: Dict[str, Any]) -> str:
        """Format alert data for email delivery."""
        condition = alert_data.get("condition", {})
        context = alert_data.get("context", {})
        
        return f"""
Alert: {alert_id}
Condition: {condition.get('type', 'unknown')} - {condition.get('entity', 'N/A')}
Value: {context.get('current_value', 'N/A')}
Threshold: {condition.get('value', 'N/A')}
Time: {context.get('timestamp', 'N/A')}
        """.strip()

    def _format_sms_content(self, alert_id: str, alert_data: Dict[str, Any]) -> str:
        """Format alert data for SMS delivery."""
        condition = alert_data.get("condition", {})
        context = alert_data.get("context", {})
        
        return f"ALERT {alert_id}: {condition.get('type', 'unknown')} breach - {context.get('current_value', 'N/A')}"

    def _format_webhook_payload(self, alert_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format alert data for webhook delivery."""
        return {
            "alert_id": alert_id,
            "timestamp": alert_data.get("context", {}).get("timestamp"),
            "condition": alert_data.get("condition", {}),
            "context": alert_data.get("context", {}),
            "severity": alert_data.get("severity", "medium")
        }

    async def _schedule_retry(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        delivery_methods: List[str],
        retry_count: int
    ):
        """Schedule alert for retry delivery."""
        try:
            # TODO: Implement retry scheduling (Redis, Celery, etc.)
            # For now, just log the retry
            logger.info(f"Retry scheduled for alert {alert_id} (attempt {retry_count})")
            
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and re-raise
            logger.error(f"Programming error in retry scheduling: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service errors - log and continue (retry scheduling is best-effort)
            logger.error(f"Failed to schedule retry for alert {alert_id}: {e}")
            # Don't raise exception here - best-effort is intentional

    async def _move_to_dlq(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        error_message: str
    ):
        """Move failed alert to Dead Letter Queue."""
        try:
            if self.use_db:
                import json
                from app.db.connection import execute_statement
                await execute_statement(
                    """
                    INSERT INTO alert_dlq (
                        alert_id, alert_data, error_message, created_at
                    ) VALUES ($1, $2, $3, NOW())
                    """,
                    alert_id,
                    json.dumps(alert_data),
                    error_message
                )
            else:
                logger.info(f"Alert {alert_id} moved to DLQ: {error_message}")
                
        except Exception as e:
            # Database/service errors - log and continue (DLQ is best-effort)
            logger.error(f"Failed to move alert {alert_id} to DLQ: {e}")
            # Don't raise DatabaseError here - best-effort is intentional

    async def _log_delivery_success(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        delivery_result: Dict[str, Any]
    ):
        """Log successful alert delivery."""
        try:
            import hashlib
            import json
            
            content_hash = hashlib.md5(
                json.dumps(alert_data, sort_keys=True).encode()
            ).hexdigest()

            if self.use_db:
                from app.db.connection import execute_statement
                await execute_statement(
                    """
                    INSERT INTO alert_deliveries (
                        alert_id, content_hash, delivery_methods, delivered_at
                    ) VALUES ($1, $2, $3, NOW())
                    """,
                    alert_id,
                    content_hash,
                    json.dumps(delivery_result.get("results", []))
                )
            else:
                logger.info(f"Alert {alert_id} delivered successfully")
                
        except Exception as e:
            # Database errors - log and continue (logging is best-effort)
            logger.error(f"Failed to log delivery success for alert {alert_id}: {e}")
            # Don't raise DatabaseError here - best-effort is intentional


# ============================================================================
# Service Factory
# ============================================================================

def get_alert_service(use_db: bool = True) -> AlertService:
    """
    Get AlertService singleton instance.

    **DEPRECATED:** Use `AlertService(use_db=...)` directly instead of this singleton function.
    This function is deprecated as part of the singleton pattern removal (Phase 2).

    **Architecture Note:** AlertService itself is an implementation detail of the MacroHound agent.
    Patterns should use `macro_hound` agent capabilities, not this service directly.

    Args:
        use_db: If True, use real database. If False, use stubs for testing.
                Stub mode is only available in development/testing environments.

    Returns:
        AlertService instance
        
    Raises:
        ValueError: If use_db=False in production environment
    """
    import os
    import warnings
    
    # Production guard: prevent stub mode in production
    if not use_db and os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            "Cannot use stub mode (use_db=False) in production environment. "
            "Stub mode is only available for development and testing."
        )
    
    warnings.warn(
        "get_alert_service() is deprecated. Use AlertService(use_db=...) directly instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    global _alert_service_db, _alert_service_stub
    
    if use_db:
        if _alert_service_db is None:
            _alert_service_db = AlertService(use_db=True)
        return _alert_service_db
    else:
        if _alert_service_stub is None:
            _alert_service_stub = AlertService(use_db=False)
        return _alert_service_stub


# Singleton instances - separate for db and stub modes
_alert_service_db = None
_alert_service_stub = None
