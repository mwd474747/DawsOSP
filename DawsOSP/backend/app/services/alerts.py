"""
Alert Evaluation Service

Purpose: Evaluate user-defined alert conditions against portfolio metrics
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

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
    from backend.app.services.alerts import AlertService

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

logger = logging.getLogger("DawsOS.Alerts")


class AlertService:
    """
    Alert evaluation service.

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

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        if use_db:
            try:
                from backend.app.db.connection import execute_query_one, execute_query
                from backend.app.db.metrics_queries import get_metrics_queries

                self.execute_query_one = execute_query_one
                self.execute_query = execute_query
                self.metrics_queries = get_metrics_queries()
                logger.info("AlertService initialized with database integration")

            except Exception as e:
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode."
                )
                self.use_db = False
        else:
            logger.info("AlertService initialized in stub mode")

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
        cooldown_hours = alert.get("cooldown_hours", 24)

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
        cooldown_hours: int = 24,
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
            # Stub: return random value
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
        except Exception as e:
            logger.error(f"Failed to get macro value for {series_id}: {e}")
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
            {"type": "metric", "portfolio_id": "xxx", "metric": "max_drawdown_1y", "op": ">", "value": 0.15}
        """
        value = await self._get_metric_value(condition, ctx)

        if value is None:
            logger.warning(f"Metric value not available: {condition}")
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
            # Stub: return random value
            import random
            return Decimal(str(random.uniform(0.0, 0.3)))

        portfolio_id = condition.get("portfolio_id")
        metric_name = condition.get("metric")  # twr_ytd, sharpe_1y, max_drawdown_1y, etc.
        asof_date = ctx.get("asof_date", date.today())

        if not portfolio_id or not metric_name:
            logger.warning(f"Invalid metric condition: {condition}")
            return None

        # Query portfolio_metrics table
        # Use column name directly from condition
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
        except Exception as e:
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
            {"type": "rating", "portfolio_id": "xxx", "symbol": "AAPL", "metric": "dividend_safety", "op": "<", "value": 6}
        """
        value = await self._get_rating_value(condition, ctx)

        if value is None:
            logger.warning(f"Rating value not available: {condition}")
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
            # Stub: return random value (0-10 scale)
            import random
            return Decimal(str(random.randint(0, 10)))

        symbol = condition.get("symbol")
        metric_name = condition.get("metric")  # dividend_safety, quality_score, moat_score, etc.
        asof_date = ctx.get("asof_date", date.today())

        if not symbol or not metric_name:
            logger.warning(f"Invalid rating condition: {condition}")
            return None

        # Query security_ratings table
        # TODO: Create security_ratings table in schema
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
        except Exception as e:
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
            # Stub: return random value
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

            pack_id = pack_row["id"]

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
                # Get specific price field
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

        except Exception as e:
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
            # Stub: return random value (-1 to 1)
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
        except Exception as e:
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
