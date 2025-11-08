"""
Alert Condition Validators

Purpose: Validate alert condition JSON schemas
Updated: 2025-10-23
Priority: P1 (Sprint 3 Week 6)

Features:
    - JSON schema validation for each condition type
    - Operator validation (>, <, >=, <=, ==, !=)
    - Field validation (required fields, types)
    - Value range validation

Condition Types:
    - macro: VIX > 30, unemployment < 4%
    - metric: max_drawdown_1y > 0.15, sharpe_1y < 1.0
    - rating: dividend_safety < 6, quality_score < 7
    - price: AAPL price < 150, AAPL change_pct > 0.05
    - news_sentiment: AAPL sentiment < -0.5

Usage:
    from app.core.alert_validators import validate_alert_condition

    condition = {
        "type": "macro",
        "entity": "VIX",
        "metric": "level",
        "op": ">",
        "value": 30
    }

    is_valid, errors = validate_alert_condition(condition)
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("DawsOS.AlertValidators")


# Valid operators
VALID_OPERATORS = [">", "<", ">=", "<=", "==", "!="]

# Valid condition types
VALID_CONDITION_TYPES = ["macro", "metric", "rating", "price", "news_sentiment"]

# Valid macro entities (FRED series)
VALID_MACRO_ENTITIES = [
    "VIX",
    "DGS10",
    "DGS2",
    "UNRATE",
    "CPI",
    "T10YIE",
    "DFII10",
    "BAMLC0A0CM",
    "DTWEXBGS",
]

# Valid portfolio metrics
VALID_PORTFOLIO_METRICS = [
    "twr_1d",
    "twr_mtd",
    "twr_qtd",
    "twr_ytd",
    "twr_1y",
    "twr_3y_ann",
    "twr_5y_ann",
    "twr_inception_ann",
    "mwr_ytd",
    "mwr_1y",
    "mwr_3y_ann",
    "mwr_inception_ann",
    "volatility_30d",
    "volatility_60d",
    "volatility_90d",
    "volatility_1y",
    "sharpe_30d",
    "sharpe_60d",
    "sharpe_90d",
    "sharpe_1y",
    "max_drawdown_1y",
    "max_drawdown_3y",
    "alpha_1y",
    "alpha_3y_ann",
    "beta_1y",
    "beta_3y",
    "tracking_error_1y",
    "information_ratio_1y",
    "win_rate_1y",
    "avg_win",
    "avg_loss",
]

# Valid security ratings
VALID_RATING_METRICS = [
    "quality_score",
    "moat_score",
    "balance_sheet_score",
    "management_score",
    "valuation_score",
    "dividend_safety",
    "overall_rating",
]

# Valid price metrics
VALID_PRICE_METRICS = [
    "close",
    "open",
    "high",
    "low",
    "volume",
    "change_pct",
    "change_abs",
]


def validate_alert_condition(condition: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate alert condition JSON.

    Args:
        condition: Alert condition JSON

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check required field: type
    if "type" not in condition:
        errors.append("Missing required field: 'type'")
        return False, errors

    condition_type = condition["type"]

    # Check valid condition type
    if condition_type not in VALID_CONDITION_TYPES:
        errors.append(
            f"Invalid condition type: '{condition_type}'. "
            f"Valid types: {VALID_CONDITION_TYPES}"
        )
        return False, errors

    # Validate based on type
    if condition_type == "macro":
        is_valid, type_errors = validate_macro_condition(condition)
    elif condition_type == "metric":
        is_valid, type_errors = validate_metric_condition(condition)
    elif condition_type == "rating":
        is_valid, type_errors = validate_rating_condition(condition)
    elif condition_type == "price":
        is_valid, type_errors = validate_price_condition(condition)
    elif condition_type == "news_sentiment":
        is_valid, type_errors = validate_news_sentiment_condition(condition)
    else:
        is_valid = False
        type_errors = [f"Unknown condition type: {condition_type}"]

    errors.extend(type_errors)

    return len(errors) == 0, errors


def validate_macro_condition(condition: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate macro indicator condition.

    Required fields:
    - type: "macro"
    - entity: FRED series ID (VIX, DGS10, etc.)
    - metric: "level" (default)
    - op: comparison operator
    - value: threshold value

    Example:
        {
            "type": "macro",
            "entity": "VIX",
            "metric": "level",
            "op": ">",
            "value": 30
        }
    """
    errors = []

    # Required fields
    required_fields = ["entity", "op", "value"]
    for field in required_fields:
        if field not in condition:
            errors.append(f"Missing required field for macro condition: '{field}'")

    # Validate entity
    entity = condition.get("entity")
    if entity and entity not in VALID_MACRO_ENTITIES:
        errors.append(
            f"Invalid macro entity: '{entity}'. "
            f"Valid entities: {VALID_MACRO_ENTITIES}"
        )

    # Validate operator
    op = condition.get("op")
    if op and op not in VALID_OPERATORS:
        errors.append(f"Invalid operator: '{op}'. Valid operators: {VALID_OPERATORS}")

    # Validate value
    value = condition.get("value")
    if value is not None and not isinstance(value, (int, float)):
        errors.append(f"Value must be a number, got: {type(value).__name__}")

    return len(errors) == 0, errors


def validate_metric_condition(condition: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate portfolio metric condition.

    Required fields:
    - type: "metric"
    - portfolio_id: Portfolio UUID
    - metric: Metric name (twr_ytd, sharpe_1y, etc.)
    - op: comparison operator
    - value: threshold value

    Example:
        {
            "type": "metric",
            "portfolio_id": "portfolio-uuid-here",
            "metric": "max_drawdown_1y",
            "op": ">",
            "value": 0.15
        }
    """
    errors = []

    # Required fields
    required_fields = ["portfolio_id", "metric", "op", "value"]
    for field in required_fields:
        if field not in condition:
            errors.append(f"Missing required field for metric condition: '{field}'")

    # Validate portfolio_id (must be UUID-like)
    portfolio_id = condition.get("portfolio_id")
    if portfolio_id and not isinstance(portfolio_id, str):
        errors.append(f"portfolio_id must be a string (UUID), got: {type(portfolio_id).__name__}")

    # Validate metric
    metric = condition.get("metric")
    if metric and metric not in VALID_PORTFOLIO_METRICS:
        errors.append(
            f"Invalid portfolio metric: '{metric}'. "
            f"Valid metrics: {VALID_PORTFOLIO_METRICS}"
        )

    # Validate operator
    op = condition.get("op")
    if op and op not in VALID_OPERATORS:
        errors.append(f"Invalid operator: '{op}'. Valid operators: {VALID_OPERATORS}")

    # Validate value
    value = condition.get("value")
    if value is not None and not isinstance(value, (int, float)):
        errors.append(f"Value must be a number, got: {type(value).__name__}")

    return len(errors) == 0, errors


def validate_rating_condition(condition: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate security rating condition.

    Required fields:
    - type: "rating"
    - portfolio_id: Portfolio UUID (optional)
    - symbol: Security symbol
    - metric: Rating metric (quality_score, dividend_safety, etc.)
    - op: comparison operator
    - value: threshold value (0-10 scale)

    Example:
        {
            "type": "rating",
            "portfolio_id": "portfolio-uuid-here",
            "symbol": "AAPL",
            "metric": "dividend_safety",
            "op": "<",
            "value": 6
        }
    """
    errors = []

    # Required fields
    required_fields = ["symbol", "metric", "op", "value"]
    for field in required_fields:
        if field not in condition:
            errors.append(f"Missing required field for rating condition: '{field}'")

    # Validate symbol
    symbol = condition.get("symbol")
    if symbol and not isinstance(symbol, str):
        errors.append(f"symbol must be a string, got: {type(symbol).__name__}")

    # Validate metric
    metric = condition.get("metric")
    if metric and metric not in VALID_RATING_METRICS:
        errors.append(
            f"Invalid rating metric: '{metric}'. "
            f"Valid metrics: {VALID_RATING_METRICS}"
        )

    # Validate operator
    op = condition.get("op")
    if op and op not in VALID_OPERATORS:
        errors.append(f"Invalid operator: '{op}'. Valid operators: {VALID_OPERATORS}")

    # Validate value (rating scores are 0-10)
    value = condition.get("value")
    if value is not None:
        if not isinstance(value, (int, float)):
            errors.append(f"Value must be a number, got: {type(value).__name__}")
        elif not (0 <= value <= 10):
            errors.append(f"Rating value must be between 0 and 10, got: {value}")

    return len(errors) == 0, errors


def validate_price_condition(condition: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate price condition.

    Required fields:
    - type: "price"
    - symbol: Security symbol
    - metric: Price metric (close, change_pct, etc.)
    - op: comparison operator
    - value: threshold value

    Example:
        {
            "type": "price",
            "symbol": "AAPL",
            "metric": "close",
            "op": "<",
            "value": 150
        }
    """
    errors = []

    # Required fields
    required_fields = ["symbol", "metric", "op", "value"]
    for field in required_fields:
        if field not in condition:
            errors.append(f"Missing required field for price condition: '{field}'")

    # Validate symbol
    symbol = condition.get("symbol")
    if symbol and not isinstance(symbol, str):
        errors.append(f"symbol must be a string, got: {type(symbol).__name__}")

    # Validate metric
    metric = condition.get("metric")
    if metric and metric not in VALID_PRICE_METRICS:
        errors.append(
            f"Invalid price metric: '{metric}'. "
            f"Valid metrics: {VALID_PRICE_METRICS}"
        )

    # Validate operator
    op = condition.get("op")
    if op and op not in VALID_OPERATORS:
        errors.append(f"Invalid operator: '{op}'. Valid operators: {VALID_OPERATORS}")

    # Validate value
    value = condition.get("value")
    if value is not None and not isinstance(value, (int, float)):
        errors.append(f"Value must be a number, got: {type(value).__name__}")

    return len(errors) == 0, errors


def validate_news_sentiment_condition(condition: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate news sentiment condition.

    Required fields:
    - type: "news_sentiment"
    - symbol: Security symbol
    - metric: "sentiment" (default)
    - op: comparison operator
    - value: threshold value (-1 to 1)

    Example:
        {
            "type": "news_sentiment",
            "symbol": "AAPL",
            "metric": "sentiment",
            "op": "<",
            "value": -0.5
        }
    """
    errors = []

    # Required fields
    required_fields = ["symbol", "op", "value"]
    for field in required_fields:
        if field not in condition:
            errors.append(f"Missing required field for news_sentiment condition: '{field}'")

    # Validate symbol
    symbol = condition.get("symbol")
    if symbol and not isinstance(symbol, str):
        errors.append(f"symbol must be a string, got: {type(symbol).__name__}")

    # Validate operator
    op = condition.get("op")
    if op and op not in VALID_OPERATORS:
        errors.append(f"Invalid operator: '{op}'. Valid operators: {VALID_OPERATORS}")

    # Validate value (sentiment scores are -1 to 1)
    value = condition.get("value")
    if value is not None:
        if not isinstance(value, (int, float)):
            errors.append(f"Value must be a number, got: {type(value).__name__}")
        elif not (-1 <= value <= 1):
            errors.append(f"Sentiment value must be between -1 and 1, got: {value}")

    return len(errors) == 0, errors


def validate_cooldown_hours(cooldown_hours: Optional[int]) -> Tuple[bool, List[str]]:
    """
    Validate cooldown hours.

    Args:
        cooldown_hours: Cooldown period in hours

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if cooldown_hours is None:
        # Cooldown is optional, default to 24 hours
        return True, []

    if not isinstance(cooldown_hours, int):
        errors.append(f"cooldown_hours must be an integer, got: {type(cooldown_hours).__name__}")
        return False, errors

    if cooldown_hours < 0:
        errors.append(f"cooldown_hours must be non-negative, got: {cooldown_hours}")

    if cooldown_hours > 8760:  # 1 year
        errors.append(f"cooldown_hours cannot exceed 8760 (1 year), got: {cooldown_hours}")

    return len(errors) == 0, errors


def validate_notification_channels(
    notify_email: Optional[bool],
    notify_inapp: Optional[bool],
) -> Tuple[bool, List[str]]:
    """
    Validate notification channels.

    At least one channel must be enabled.

    Args:
        notify_email: Email notification enabled
        notify_inapp: In-app notification enabled

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Default values
    email = notify_email if notify_email is not None else False
    inapp = notify_inapp if notify_inapp is not None else True

    # At least one channel must be enabled
    if not email and not inapp:
        errors.append("At least one notification channel must be enabled (email or inapp)")

    return len(errors) == 0, errors


# ============================================================================
# THRESHOLD VALIDATORS (ALERTS_ARCHITECT PATTERNS)
# ============================================================================
# Added: 2025-10-26
# Purpose: Prevent spam and false positives via research-based thresholds
# Source: Bridgewater Associates risk framework, JAMA 2018 alert fatigue research
# ============================================================================

from decimal import Decimal


class AlertThresholdValidator:
    """
    Validates alert thresholds to prevent spam and false positives.

    Threshold Ranges (Research-Based):
    - dar_breach: 5%-50% (minimum 5% to avoid noise, max 50% for extreme events)
    - drawdown_limit: 10%-40% (minimum 10% to avoid market volatility noise)
    - regime_shift: 80% confidence (minimum to ensure meaningful regime changes)

    Source: Bridgewater Associates risk management framework
    """

    # Threshold configuration
    THRESHOLDS = {
        'dar_breach': {
            'min_threshold': Decimal('0.05'),  # 5% minimum
            'max_threshold': Decimal('0.50'),  # 50% maximum
            'default': Decimal('0.15'),  # 15% default (conservative)
            'description': 'Drawdown at Risk breach threshold',
            'unit': 'percentage',
        },
        'drawdown_limit': {
            'min_threshold': Decimal('0.10'),  # 10% minimum
            'max_threshold': Decimal('0.40'),  # 40% maximum
            'default': Decimal('0.20'),  # 20% default
            'description': 'Maximum drawdown limit',
            'unit': 'percentage',
        },
        'regime_shift': {
            'confidence_threshold': Decimal('0.80'),  # 80% confidence minimum
            'regime_distance': 2,  # At least 2 regimes apart
            'default_confidence': Decimal('0.90'),  # 90% default
            'description': 'Macro regime shift detection',
            'unit': 'confidence',
        },
        'volatility_spike': {
            'min_threshold': Decimal('0.20'),  # 20% minimum
            'max_threshold': Decimal('2.00'),  # 200% maximum
            'default': Decimal('0.50'),  # 50% default
            'description': 'Volatility spike threshold',
            'unit': 'percentage',
        },
    }

    @classmethod
    def validate_threshold(
        cls,
        alert_type: str,
        threshold: Decimal,
    ) -> bool:
        """
        Validate threshold is within reasonable bounds.

        Args:
            alert_type: Type of alert (dar_breach, drawdown_limit, etc.)
            threshold: Threshold value to validate

        Returns:
            True if valid

        Raises:
            ValueError: If threshold is outside bounds or alert_type is unknown
        """
        if alert_type not in cls.THRESHOLDS:
            raise ValueError(f"Unknown alert type: {alert_type}")

        bounds = cls.THRESHOLDS[alert_type]

        # Special handling for regime_shift (uses confidence_threshold)
        if alert_type == 'regime_shift':
            min_confidence = bounds['confidence_threshold']
            if threshold < min_confidence:
                raise ValueError(
                    f"{alert_type} confidence {threshold} below minimum {min_confidence}"
                )
            return True

        # Standard threshold validation
        if 'min_threshold' in bounds:
            min_val = bounds['min_threshold']
            max_val = bounds['max_threshold']

            if threshold < min_val or threshold > max_val:
                raise ValueError(
                    f"{alert_type} threshold {threshold} outside bounds "
                    f"[{min_val}, {max_val}]"
                )

        return True

    @classmethod
    def get_default_threshold(cls, alert_type: str) -> Decimal:
        """Get default threshold for alert type."""
        if alert_type not in cls.THRESHOLDS:
            raise ValueError(f"Unknown alert type: {alert_type}")

        bounds = cls.THRESHOLDS[alert_type]

        if alert_type == 'regime_shift':
            return bounds['default_confidence']

        return bounds['default']

    @classmethod
    def get_bounds(cls, alert_type: str) -> Dict[str, Any]:
        """Get threshold bounds for alert type."""
        if alert_type not in cls.THRESHOLDS:
            raise ValueError(f"Unknown alert type: {alert_type}")

        return cls.THRESHOLDS[alert_type].copy()


class AlertDeduplicationValidator:
    """
    Validates alert deduplication to prevent spam.

    Deduplication Strategy:
    - 24h window per (portfolio_id, alert_type, severity)
    - Composite key: f"{portfolio_id}|{alert_type}|{severity}"

    Research Basis: "Managing Alert Fatigue in Healthcare" (JAMA 2018)
    """

    DEFAULT_WINDOW_HOURS = 24

    @staticmethod
    def generate_dedupe_key(
        portfolio_id: str,
        alert_type: str,
        severity: str,
    ) -> str:
        """Generate deduplication key."""
        return f"{portfolio_id}|{alert_type}|{severity}"

    @staticmethod
    def get_severity_for_threshold_breach(
        alert_type: str,
        actual_value: Decimal,
        threshold: Decimal,
    ) -> str:
        """
        Determine alert severity based on threshold breach magnitude.

        Severity Levels:
        - info: Breach within 10% of threshold
        - warning: Breach 10%-50% above threshold
        - critical: Breach >50% above threshold
        """
        if actual_value <= threshold:
            return 'info'  # No breach

        # Calculate breach percentage
        if threshold > 0:
            breach_pct = (actual_value - threshold) / threshold
        else:
            breach_pct = Decimal('1.0')

        if breach_pct <= Decimal('0.10'):
            return 'info'
        elif breach_pct <= Decimal('0.50'):
            return 'warning'
        else:
            return 'critical'
