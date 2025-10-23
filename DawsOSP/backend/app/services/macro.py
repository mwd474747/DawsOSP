"""
Macro Regime Detection Service

Purpose: Detect macro economic regimes from indicators (Sprint 3 Week 5)
Updated: 2025-10-22
Priority: P1 (Sprint 3)

Features:
    - 5-regime classification (Early/Mid/Late Expansion, Early/Deep Contraction)
    - Z-score normalization for indicators
    - FRED API integration
    - Historical regime tracking

Regimes:
    1. EARLY_EXPANSION: Recovery phase, yield curve steepening, unemployment falling
    2. MID_EXPANSION: Growth phase, stable indicators
    3. LATE_EXPANSION: Overheating, inflation rising, yield curve flattening
    4. EARLY_CONTRACTION: Slowdown begins, yield curve inverted
    5. DEEP_CONTRACTION: Recession, unemployment rising sharply

Architecture:
    FRED API → MacroService → RegimeDetector → Database

Usage:
    service = MacroService()
    await service.update_indicators()  # Fetch latest from FRED
    regime = await service.detect_current_regime()
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import statistics

from backend.app.db.connection import execute_query, execute_statement, execute_query_one

logger = logging.getLogger("DawsOS.MacroService")


# ============================================================================
# Enums and Data Models
# ============================================================================


class Regime(str, Enum):
    """Macro economic regimes."""

    EARLY_EXPANSION = "EARLY_EXPANSION"
    MID_EXPANSION = "MID_EXPANSION"
    LATE_EXPANSION = "LATE_EXPANSION"
    EARLY_CONTRACTION = "EARLY_CONTRACTION"
    DEEP_CONTRACTION = "DEEP_CONTRACTION"


@dataclass
class RegimeClassification:
    """Regime classification result."""

    regime: Regime
    confidence: float  # 0-1
    date: date
    indicators: Dict[str, float]  # Raw indicator values
    zscores: Dict[str, float]  # Z-score normalized
    regime_scores: Dict[str, float]  # Score for each regime


@dataclass
class MacroIndicator:
    """Macro economic indicator."""

    indicator_id: str
    indicator_name: str
    date: date
    value: float
    units: Optional[str] = None
    frequency: Optional[str] = None
    source: str = "FRED"


# ============================================================================
# Regime Detection Logic
# ============================================================================


class RegimeDetector:
    """
    Macro regime detector.

    Uses z-score normalized indicators to classify the current macro regime.
    """

    # Indicator weights for regime scoring
    REGIME_RULES = {
        Regime.EARLY_EXPANSION: {
            "T10Y2Y": ("positive", 2.0),  # Yield curve steepening
            "UNRATE_change": ("negative", 1.5),  # Unemployment falling
            "GDP_growth": ("positive", 1.0),  # GDP growing
            "CPIAUCSL_yoy": ("low", 0.5),  # Inflation low/stable
        },
        Regime.MID_EXPANSION: {
            "T10Y2Y": ("positive", 1.0),  # Yield curve positive
            "UNRATE": ("low", 1.5),  # Unemployment low
            "GDP_growth": ("positive", 2.0),  # Strong growth
            "CPIAUCSL_yoy": ("moderate", 1.0),  # Inflation moderate
        },
        Regime.LATE_EXPANSION: {
            "T10Y2Y": ("flattening", 2.0),  # Yield curve flattening
            "UNRATE": ("very_low", 1.5),  # Unemployment very low
            "CPIAUCSL_yoy": ("high", 2.0),  # Inflation rising
            "GDP_growth": ("positive", 0.5),  # Growth slowing
        },
        Regime.EARLY_CONTRACTION: {
            "T10Y2Y": ("negative", 2.5),  # Yield curve inverted
            "UNRATE_change": ("positive", 1.0),  # Unemployment rising
            "GDP_growth": ("slowing", 2.0),  # Growth slowing
            "CPIAUCSL_yoy": ("moderate", 0.5),  # Inflation peaking
        },
        Regime.DEEP_CONTRACTION: {
            "T10Y2Y": ("negative", 1.0),  # Yield curve inverted
            "UNRATE": ("high", 2.5),  # Unemployment high
            "UNRATE_change": ("positive", 2.0),  # Unemployment rising fast
            "GDP_growth": ("negative", 2.5),  # GDP contracting
        },
    }

    def __init__(self, lookback_days: int = 252):
        """
        Initialize regime detector.

        Args:
            lookback_days: Lookback window for z-score (default: 252 trading days = 1 year)
        """
        self.lookback_days = lookback_days

    async def compute_zscore(
        self,
        indicator_id: str,
        current_value: float,
        as_of_date: date,
    ) -> float:
        """
        Compute z-score for an indicator.

        Args:
            indicator_id: Indicator ID (e.g., "T10Y2Y")
            current_value: Current indicator value
            as_of_date: Date for z-score calculation

        Returns:
            Z-score (standard deviations from mean)
        """
        # Query historical values for lookback window
        query = """
            SELECT value
            FROM macro_indicators
            WHERE indicator_id = $1
              AND date <= $2
              AND date >= $3
            ORDER BY date DESC
        """
        lookback_start = as_of_date - timedelta(days=self.lookback_days)
        rows = await execute_query(query, indicator_id, as_of_date, lookback_start)

        if not rows or len(rows) < 30:  # Need at least 30 data points
            logger.warning(
                f"Insufficient data for z-score: {indicator_id} "
                f"(found {len(rows) if rows else 0} points, need 30+)"
            )
            return 0.0

        values = [float(row["value"]) for row in rows]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)

        if stdev == 0:
            return 0.0

        zscore = (current_value - mean) / stdev
        return zscore

    def score_regime(
        self,
        regime: Regime,
        indicators: Dict[str, float],
        zscores: Dict[str, float],
    ) -> float:
        """
        Score a regime based on current indicators.

        Args:
            regime: Regime to score
            indicators: Raw indicator values
            zscores: Z-score normalized indicators

        Returns:
            Regime score (0-100)
        """
        rules = self.REGIME_RULES[regime]
        total_score = 0.0
        total_weight = 0.0

        for indicator_key, (condition, weight) in rules.items():
            # Get indicator value (raw or z-score)
            if indicator_key.endswith("_change"):
                # Rate of change indicator
                base_indicator = indicator_key.replace("_change", "")
                value = indicators.get(f"{base_indicator}_change", 0.0)
            else:
                value = indicators.get(indicator_key, 0.0)

            zscore = zscores.get(indicator_key, 0.0)

            # Evaluate condition
            condition_met = self._evaluate_condition(condition, value, zscore)
            if condition_met:
                total_score += weight
            total_weight += weight

        # Normalize to 0-100
        if total_weight > 0:
            return (total_score / total_weight) * 100
        return 0.0

    def _evaluate_condition(
        self,
        condition: str,
        value: float,
        zscore: float,
    ) -> bool:
        """
        Evaluate a regime rule condition.

        Args:
            condition: Condition type (e.g., "positive", "negative", "high", "low")
            value: Raw indicator value
            zscore: Z-score

        Returns:
            True if condition is met
        """
        if condition == "positive":
            return value > 0
        elif condition == "negative":
            return value < 0
        elif condition == "high":
            return zscore > 1.0  # More than 1 stdev above mean
        elif condition == "very_high":
            return zscore > 2.0
        elif condition == "low":
            return zscore < -1.0
        elif condition == "very_low":
            return zscore < -2.0
        elif condition == "moderate":
            return abs(zscore) < 0.5
        elif condition == "flattening":
            return 0 < value < 0.5  # Positive but low
        elif condition == "slowing":
            return -0.5 < value < 0.5  # Near zero
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    async def detect_regime(
        self,
        indicators: Dict[str, float],
        as_of_date: date,
    ) -> RegimeClassification:
        """
        Detect current macro regime.

        Args:
            indicators: Current indicator values (e.g., {"T10Y2Y": 0.52, "UNRATE": 3.7})
            as_of_date: Date for regime classification

        Returns:
            RegimeClassification with regime, confidence, and scores
        """
        # Compute z-scores for all indicators
        zscores = {}
        for indicator_id, value in indicators.items():
            zscore = await self.compute_zscore(indicator_id, value, as_of_date)
            zscores[indicator_id] = zscore

        # Score all regimes
        regime_scores = {}
        for regime in Regime:
            score = self.score_regime(regime, indicators, zscores)
            regime_scores[regime.value] = score

        # Find highest scoring regime
        best_regime = max(regime_scores, key=regime_scores.get)
        best_score = regime_scores[best_regime]

        # Compute confidence (gap between best and second-best)
        sorted_scores = sorted(regime_scores.values(), reverse=True)
        if len(sorted_scores) >= 2 and sorted_scores[0] > 0:
            confidence = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0]
        else:
            confidence = 0.0

        logger.info(
            f"Regime detected: {best_regime} (confidence: {confidence:.2f}, "
            f"score: {best_score:.1f})"
        )

        return RegimeClassification(
            regime=Regime(best_regime),
            confidence=confidence,
            date=as_of_date,
            indicators=indicators,
            zscores=zscores,
            regime_scores=regime_scores,
        )


# ============================================================================
# Macro Service
# ============================================================================


class MacroService:
    """
    Macro economic service.

    Fetches indicators from FRED and detects current regime.
    """

    # Core indicators to track
    INDICATORS = {
        "T10Y2Y": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity",
        "UNRATE": "Unemployment Rate",
        "CPIAUCSL": "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
        "GDP": "Gross Domestic Product",
        "PAYEMS": "All Employees, Total Nonfarm",
        "INDPRO": "Industrial Production: Total Index",
        "HOUST": "Housing Starts: Total: New Privately Owned Housing Units Started",
    }

    def __init__(self, fred_api_key: Optional[str] = None):
        """
        Initialize macro service.

        Args:
            fred_api_key: FRED API key (optional, for API calls)
        """
        self.fred_api_key = fred_api_key
        self.detector = RegimeDetector()

    async def get_latest_indicator(self, indicator_id: str) -> Optional[MacroIndicator]:
        """
        Get latest value for an indicator from database.

        Args:
            indicator_id: Indicator ID (e.g., "T10Y2Y")

        Returns:
            MacroIndicator or None if not found
        """
        query = """
            SELECT
                indicator_id,
                indicator_name,
                date,
                value,
                units,
                frequency,
                source
            FROM macro_indicators
            WHERE indicator_id = $1
            ORDER BY date DESC
            LIMIT 1
        """
        row = await execute_query_one(query, indicator_id)

        if not row:
            return None

        return MacroIndicator(
            indicator_id=row["indicator_id"],
            indicator_name=row["indicator_name"],
            date=row["date"],
            value=float(row["value"]),
            units=row["units"],
            frequency=row["frequency"],
            source=row["source"],
        )

    async def store_indicator(self, indicator: MacroIndicator):
        """
        Store indicator value in database.

        Args:
            indicator: MacroIndicator to store
        """
        query = """
            INSERT INTO macro_indicators (
                indicator_id,
                indicator_name,
                date,
                value,
                units,
                frequency,
                source,
                last_updated
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            ON CONFLICT (indicator_id, date)
            DO UPDATE SET
                value = EXCLUDED.value,
                last_updated = NOW()
        """
        await execute_statement(
            query,
            indicator.indicator_id,
            indicator.indicator_name,
            indicator.date,
            Decimal(str(indicator.value)),
            indicator.units,
            indicator.frequency,
            indicator.source,
        )

        logger.info(
            f"Stored indicator: {indicator.indicator_id} = {indicator.value} "
            f"(date: {indicator.date})"
        )

    async def detect_current_regime(self) -> RegimeClassification:
        """
        Detect current macro regime from latest indicators.

        Returns:
            RegimeClassification
        """
        # Fetch latest indicators
        indicators = {}
        latest_date = None

        for indicator_id in ["T10Y2Y", "UNRATE", "CPIAUCSL"]:
            indicator = await self.get_latest_indicator(indicator_id)
            if indicator:
                indicators[indicator_id] = indicator.value
                if latest_date is None or indicator.date > latest_date:
                    latest_date = indicator.date

        if not indicators:
            raise ValueError("No indicators found in database")

        if latest_date is None:
            latest_date = date.today()

        # Compute derived indicators (year-over-year changes, etc.)
        # TODO: Add UNRATE_change, GDP_growth, CPIAUCSL_yoy

        # Detect regime
        classification = await self.detector.detect_regime(indicators, latest_date)

        # Store regime in history
        await self._store_regime(classification)

        return classification

    async def _store_regime(self, classification: RegimeClassification):
        """Store regime classification in history."""
        query = """
            INSERT INTO regime_history (
                date,
                regime,
                confidence,
                indicators_json,
                zscores_json,
                regime_scores_json
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (date)
            DO UPDATE SET
                regime = EXCLUDED.regime,
                confidence = EXCLUDED.confidence,
                indicators_json = EXCLUDED.indicators_json,
                zscores_json = EXCLUDED.zscores_json,
                regime_scores_json = EXCLUDED.regime_scores_json
        """
        import json

        await execute_statement(
            query,
            classification.date,
            classification.regime.value,
            Decimal(str(classification.confidence)),
            json.dumps(classification.indicators),
            json.dumps(classification.zscores),
            json.dumps(classification.regime_scores),
        )

        logger.info(f"Stored regime: {classification.regime.value} ({classification.date})")


# ============================================================================
# Singleton
# ============================================================================


_macro_service: Optional[MacroService] = None


def get_macro_service(fred_api_key: Optional[str] = None) -> MacroService:
    """
    Get macro service singleton.

    Args:
        fred_api_key: FRED API key (optional)

    Returns:
        MacroService singleton
    """
    global _macro_service
    if _macro_service is None:
        _macro_service = MacroService(fred_api_key=fred_api_key)
    return _macro_service
