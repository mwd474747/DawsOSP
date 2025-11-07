"""
Macro Regime Detection Service

Purpose: Detect macro economic regimes from indicators (Dalio-inspired methodology)
Updated: 2025-11-02
Priority: P0 (Critical for risk management)

Features:
    - 5-regime classification (Early/Mid/Late Expansion, Early/Deep Contraction)
    - Z-score normalization with 252-day rolling window
    - FRED API integration for real-time indicators
    - Probabilistic regime classification (not binary)
    - Historical regime tracking and transitions
    - FRED data transformation for consistent units

Regimes:
    1. EARLY_EXPANSION: Recovery phase, yield curve steepening, unemployment falling
    2. MID_EXPANSION: Growth phase, stable indicators
    3. LATE_EXPANSION: Overheating, inflation rising, yield curve flattening
    4. EARLY_CONTRACTION: Slowdown begins, yield curve inverted
    5. DEEP_CONTRACTION: Recession, unemployment rising sharply

Key Indicators (PRODUCT_SPEC.md §7):
    - T10Y2Y: 10Y-2Y Treasury spread (yield curve)
    - UNRATE: Unemployment rate
    - CPIAUCSL: Consumer Price Index (inflation)
    - BAA10Y: Credit spreads (Baa corporate - 10Y Treasury)

Z-Score Calculation:
    z = (value - rolling_mean_252d) / rolling_std_252d

Architecture:
    FRED API → MacroService → FREDTransformation → RegimeDetector → Database

Usage:
    from app.providers.fred_client import get_fred_client
    from app.services.macro import get_macro_service

    # Fetch latest indicators from FRED
    client = get_fred_client()
    service = get_macro_service()
    await service.fetch_indicators(asof_date=date.today())

    # Detect regime
    regime = await service.detect_regime(asof_date=date.today())
"""

import logging
import os
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics

from app.db.connection import execute_query, execute_statement, execute_query_one
from app.integrations.fred_provider import FREDProvider
from app.services.fred_transformation import FREDTransformationService

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
    """Regime classification result (probabilistic)."""

    regime: Regime  # Most likely regime
    regime_name: str  # Human-readable regime name
    confidence: float  # 0-1 (probability of most likely regime)
    date: date
    indicators: Dict[str, float]  # Raw indicator values
    zscores: Dict[str, float]  # Z-score normalized
    regime_probabilities: Dict[str, float]  # Probability for each regime (sums to 1.0)
    drivers: Dict[str, str]  # Key drivers for this regime (e.g., {"yield_curve": "steep", "unemployment": "falling"})


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
    Macro regime detector using Dalio-inspired methodology.

    Uses z-score normalized indicators to probabilistically classify the current macro regime.
    Based on 4 key indicators: T10Y2Y, UNRATE, CPIAUCSL, BAA10Y.

    Regime Rules (simplified from PRODUCT_SPEC.md §7):
        - EARLY_EXPANSION: Curve steep (+), unemployment falling (-), inflation low (-)
        - MID_EXPANSION: Curve positive, unemployment low, inflation rising
        - LATE_EXPANSION: Curve flattening/inverted (-), unemployment very low, inflation high (+)
        - EARLY_CONTRACTION: Curve inverted, unemployment rising (+), spreads widening (+)
        - DEEP_CONTRACTION: Curve steep (flight to safety), unemployment high (+), spreads very wide (+)
    """

    # Regime rules based on z-scores
    # Each rule maps indicator → (min_zscore, max_zscore, weight)
    REGIME_RULES = {
        Regime.EARLY_EXPANSION: {
            "T10Y2Y": (0.5, None, 2.0),  # Yield curve steep (above average)
            "UNRATE": (None, -0.5, 1.5),  # Unemployment falling (below average)
            "CPIAUCSL": (None, 0.0, 1.0),  # Inflation low/stable
            "BAA10Y": (None, 0.0, 1.0),  # Credit spreads normal/tight
        },
        Regime.MID_EXPANSION: {
            "T10Y2Y": (0.0, 1.5, 1.5),  # Yield curve positive
            "UNRATE": (-1.5, 0.0, 1.5),  # Unemployment low
            "CPIAUCSL": (-0.5, 0.5, 1.0),  # Inflation moderate
            "BAA10Y": (-0.5, 0.5, 1.0),  # Credit spreads normal
        },
        Regime.LATE_EXPANSION: {
            "T10Y2Y": (-1.0, 0.5, 2.0),  # Yield curve flattening
            "UNRATE": (-2.0, -0.5, 1.5),  # Unemployment very low
            "CPIAUCSL": (0.5, None, 2.0),  # Inflation high/rising
            "BAA10Y": (0.0, 1.0, 1.0),  # Credit spreads widening slightly
        },
        Regime.EARLY_CONTRACTION: {
            "T10Y2Y": (None, -0.5, 2.5),  # Yield curve inverted
            "UNRATE": (0.0, 1.0, 1.5),  # Unemployment rising
            "CPIAUCSL": (None, 1.0, 0.5),  # Inflation peaking/falling
            "BAA10Y": (0.5, None, 2.0),  # Credit spreads widening
        },
        Regime.DEEP_CONTRACTION: {
            "T10Y2Y": (0.5, None, 1.0),  # Yield curve steep (flight to safety)
            "UNRATE": (1.0, None, 2.5),  # Unemployment high/rising
            "CPIAUCSL": (None, 0.0, 1.0),  # Inflation low (demand shock)
            "BAA10Y": (1.5, None, 2.5),  # Credit spreads very wide
        },
    }

    # Regime display names
    REGIME_NAMES = {
        Regime.EARLY_EXPANSION: "Early Expansion",
        Regime.MID_EXPANSION: "Mid Expansion",
        Regime.LATE_EXPANSION: "Late Expansion",
        Regime.EARLY_CONTRACTION: "Early Contraction",
        Regime.DEEP_CONTRACTION: "Deep Contraction",
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
        zscores: Dict[str, float],
    ) -> float:
        """
        Score a regime based on z-scores using probabilistic rules.

        Args:
            regime: Regime to score
            zscores: Z-score normalized indicators

        Returns:
            Regime score (0-100, higher is better match)
        """
        rules = self.REGIME_RULES[regime]
        total_score = 0.0
        total_weight = 0.0

        for indicator_id, (min_z, max_z, weight) in rules.items():
            zscore = zscores.get(indicator_id, 0.0)

            # Check if z-score falls within regime range
            in_range = True
            if min_z is not None and zscore < min_z:
                in_range = False
            if max_z is not None and zscore > max_z:
                in_range = False

            # Soft scoring: full weight if in range, partial weight if close
            if in_range:
                total_score += weight
            else:
                # Compute distance from range
                if min_z is not None and zscore < min_z:
                    distance = min_z - zscore
                elif max_z is not None and zscore > max_z:
                    distance = zscore - max_z
                else:
                    distance = 0.0

                # Penalize based on distance (exponential decay)
                # If 0.5 stdev away, get 60% weight; 1.0 stdev away, get 37%; 2.0 stdev away, get 13%
                penalty = max(0.0, (2 ** (-distance)))
                total_score += weight * penalty

            total_weight += weight

        # Normalize to 0-100
        if total_weight > 0:
            return (total_score / total_weight) * 100
        return 0.0

    def _identify_drivers(self, zscores: Dict[str, float]) -> Dict[str, str]:
        """
        Identify key drivers from z-scores.

        Args:
            zscores: Z-score normalized indicators

        Returns:
            Dict of driver descriptions
        """
        drivers = {}

        # Yield curve
        if "T10Y2Y" in zscores:
            z = zscores["T10Y2Y"]
            if z > 1.0:
                drivers["yield_curve"] = "steep"
            elif z < -1.0:
                drivers["yield_curve"] = "inverted"
            elif z > 0:
                drivers["yield_curve"] = "positive"
            else:
                drivers["yield_curve"] = "flattening"

        # Unemployment
        if "UNRATE" in zscores:
            z = zscores["UNRATE"]
            if z > 1.5:
                drivers["unemployment"] = "high"
            elif z > 0.5:
                drivers["unemployment"] = "rising"
            elif z < -1.5:
                drivers["unemployment"] = "very_low"
            elif z < -0.5:
                drivers["unemployment"] = "low"
            else:
                drivers["unemployment"] = "normal"

        # Inflation
        if "CPIAUCSL" in zscores:
            z = zscores["CPIAUCSL"]
            if z > 1.0:
                drivers["inflation"] = "high"
            elif z > 0.5:
                drivers["inflation"] = "rising"
            elif z < -0.5:
                drivers["inflation"] = "low"
            else:
                drivers["inflation"] = "moderate"

        # Credit spreads
        if "BAA10Y" in zscores:
            z = zscores["BAA10Y"]
            if z > 1.5:
                drivers["credit_spreads"] = "very_wide"
            elif z > 0.5:
                drivers["credit_spreads"] = "widening"
            elif z < -0.5:
                drivers["credit_spreads"] = "tight"
            else:
                drivers["credit_spreads"] = "normal"

        return drivers

    async def detect_regime(
        self,
        indicators: Dict[str, float],
        as_of_date: date,
    ) -> RegimeClassification:
        """
        Detect current macro regime using probabilistic classification.

        Args:
            indicators: Current indicator values (e.g., {"T10Y2Y": 0.52, "UNRATE": 3.7})
            as_of_date: Date for regime classification

        Returns:
            RegimeClassification with regime, probabilities, and drivers
        """
        # Compute z-scores for all indicators
        zscores = {}
        for indicator_id, value in indicators.items():
            zscore = await self.compute_zscore(indicator_id, value, as_of_date)
            zscores[indicator_id] = zscore

        # Score all regimes
        regime_scores = {}
        for regime in Regime:
            score = self.score_regime(regime, zscores)
            regime_scores[regime.value] = score

        # Convert scores to probabilities (softmax)
        total_score = sum(regime_scores.values())
        regime_probabilities = {}
        if total_score > 0:
            for regime_name, score in regime_scores.items():
                regime_probabilities[regime_name] = score / total_score
        else:
            # Equal probability if no clear signal
            for regime_name in regime_scores.keys():
                regime_probabilities[regime_name] = 1.0 / len(regime_scores)

        # Find most likely regime
        best_regime = max(regime_probabilities, key=regime_probabilities.get)
        confidence = regime_probabilities[best_regime]

        # Identify key drivers
        drivers = self._identify_drivers(zscores)

        logger.info(
            f"Regime detected: {best_regime} (probability: {confidence:.2%})"
        )
        logger.debug(f"Regime probabilities: {regime_probabilities}")
        logger.debug(f"Drivers: {drivers}")

        return RegimeClassification(
            regime=Regime(best_regime),
            regime_name=self.REGIME_NAMES[Regime(best_regime)],
            confidence=confidence,
            date=as_of_date,
            indicators=indicators,
            zscores=zscores,
            regime_probabilities=regime_probabilities,
            drivers=drivers,
        )


# ============================================================================
# Macro Service
# ============================================================================


class MacroService:
    """
    Macro economic service.

    Fetches indicators from FRED and detects current regime using Dalio-inspired methodology.
    """

    # Core indicators for regime detection (PRODUCT_SPEC.md §7)
    CORE_INDICATORS = {
        "T10Y2Y": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity",
        "UNRATE": "Unemployment Rate",
        "CPIAUCSL": "Consumer Price Index for All Urban Consumers: All Items",
        "BAA10Y": "Moody's Seasoned Baa Corporate Bond Yield Relative to Yield on 10-Year Treasury Constant Maturity",
    }

    # Additional indicators for context
    ADDITIONAL_INDICATORS = {
        "DGS10": "10-Year Treasury Constant Maturity Rate",
        "DGS2": "2-Year Treasury Constant Maturity Rate",
        "CPILFESL": "Consumer Price Index for All Urban Consumers: All Items Less Food and Energy",
    }

    def __init__(self, fred_client: Optional[FREDProvider] = None, db_pool=None):
        """
        Initialize macro service.

        Args:
            fred_client: FRED API client (optional, will create if not provided)
            db_pool: AsyncPG connection pool (optional, will get from connection module if not provided)
        """
        if fred_client is None:
            api_key = os.getenv("FRED_API_KEY")
            if not api_key:
                raise ValueError("FRED_API_KEY not configured")
            fred_client = FREDProvider(api_key=api_key)
        self.fred_client = fred_client
        self.db_pool = db_pool
        self.detector = RegimeDetector()
        self.transformation_service = FREDTransformationService()

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

    async def compute_derived_indicators(self, asof_date: Optional[date] = None):
        """
        Compute derived indicators from base FRED indicators.
        
        This calls the SQL function that calculates:
        - Real interest rate (nominal - inflation)
        - GDP gap (actual vs potential)
        - Employment gap (unemployment vs natural rate)
        - Money velocity (GDP/M2)
        - Fiscal impulse (YoY change in deficit)
        - Credit impulse (change in credit growth)
        
        Args:
            asof_date: Date to compute indicators for (None = all dates)
        """
        logger.info(f"Computing derived indicators for date: {asof_date or 'all dates'}")
        
        try:
            # Call the SQL function to compute derived indicators
            query = "SELECT compute_derived_indicators($1)"
            await execute_statement(query, asof_date)
            
            # Get summary of what was calculated
            summary_query = """
                SELECT 
                    indicator_id,
                    COUNT(*) as record_count,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM macro_indicators
                WHERE source = 'calculated'
                    AND ($1 IS NULL OR date = $1)
                GROUP BY indicator_id
                ORDER BY indicator_id
            """
            rows = await execute_query(summary_query, asof_date)
            
            if rows:
                logger.info("Computed derived indicators:")
                for row in rows:
                    logger.info(
                        f"  {row['indicator_id']}: {row['record_count']} records "
                        f"({row['earliest_date']} to {row['latest_date']})"
                    )
            else:
                logger.warning("No derived indicators were computed - check if base indicators are available")
                
        except Exception as e:
            logger.error(f"Failed to compute derived indicators: {e}", exc_info=True)
            raise

    async def fetch_indicators(
        self,
        asof_date: Optional[date] = None,
        lookback_days: int = 365,
    ) -> Dict[str, List[MacroIndicator]]:
        """
        Fetch macro indicators from FRED API.

        Args:
            asof_date: Fetch indicators as of this date (default: today)
            lookback_days: Fetch last N days of data (default: 365)

        Returns:
            Dict mapping indicator_id to list of MacroIndicator objects
        """
        if asof_date is None:
            asof_date = date.today()

        start_date = asof_date - timedelta(days=lookback_days)

        logger.info(
            f"Fetching indicators from FRED: {start_date} to {asof_date}"
        )

        results = {}
        all_indicators = {**self.CORE_INDICATORS, **self.ADDITIONAL_INDICATORS}

        for indicator_id, indicator_name in all_indicators.items():
            try:
                # Fetch from FRED
                observations = await self.fred_client.get_series(
                    series_id=indicator_id,
                    start_date=start_date,
                    end_date=asof_date,
                )

                # Convert to MacroIndicator objects
                indicators = []
                # Store all observations for YoY calculations
                historical_values = []
                
                for obs in observations:
                    # Skip missing values
                    if obs.get("value") == ".":
                        continue

                    try:
                        raw_value = float(obs["value"])
                        obs_date = datetime.strptime(obs["date"], "%Y-%m-%d").date()
                        
                        # Add to historical values for transformation context
                        historical_values.append({
                            'date': obs["date"],
                            'value': raw_value
                        })
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(
                            f"Skipping invalid observation for {indicator_id}: {e}"
                        )
                        continue
                
                # Now process all observations with transformation
                for i, obs in enumerate(observations):
                    # Skip missing values
                    if obs.get("value") == ".":
                        continue

                    try:
                        raw_value = float(obs["value"])
                        obs_date = datetime.strptime(obs["date"], "%Y-%m-%d").date()
                        
                        # Apply transformation using historical context
                        # (excluding current value from historical for YoY calculations)
                        historical_for_transform = historical_values[:i]
                        
                        transformed_value = self.transformation_service.transform_fred_value(
                            series_id=indicator_id,
                            value=raw_value,
                            date_str=obs["date"],
                            historical_values=historical_for_transform if len(historical_for_transform) > 0 else None
                        )
                        
                        # Use transformed value if available, otherwise use raw value
                        final_value = transformed_value if transformed_value is not None else raw_value
                        
                        if transformed_value is not None and abs(transformed_value - raw_value) > 0.001:
                            logger.debug(
                                f"Transformed {indicator_id} on {obs_date}: {raw_value:.4f} → {final_value:.6f}"
                            )

                        indicator = MacroIndicator(
                            indicator_id=indicator_id,
                            indicator_name=indicator_name,
                            date=obs_date,
                            value=final_value,
                            source="FRED",
                        )

                        indicators.append(indicator)

                        # Store in database with transformed value
                        await self.store_indicator(indicator)

                    except (ValueError, KeyError) as e:
                        logger.warning(
                            f"Skipping invalid observation for {indicator_id}: {e}"
                        )
                        continue

                results[indicator_id] = indicators
                logger.info(
                    f"Fetched {len(indicators)} observations for {indicator_id}"
                )

            except Exception as e:
                logger.error(f"Failed to fetch {indicator_id}: {e}")
                results[indicator_id] = []

        return results

    async def get_indicators(
        self,
        asof_date: Optional[date] = None,
    ) -> Dict[str, float]:
        """
        Get latest indicator values (raw values, not z-scores).

        Args:
            asof_date: Get indicators as of this date (default: today)

        Returns:
            Dict mapping indicator_id to value
        """
        if asof_date is None:
            asof_date = date.today()

        indicators = {}
        for indicator_id in self.CORE_INDICATORS.keys():
            indicator = await self.get_latest_indicator(indicator_id)
            if indicator and indicator.date <= asof_date:
                indicators[indicator_id] = indicator.value

        return indicators

    async def detect_regime(
        self,
        asof_date: Optional[date] = None,
    ) -> RegimeClassification:
        """
        Detect macro regime for a specific date.

        Args:
            asof_date: Date for regime detection (default: today)

        Returns:
            RegimeClassification with probabilities and drivers
        """
        if asof_date is None:
            asof_date = date.today()

        # Get indicators for this date
        indicators = await self.get_indicators(asof_date)

        if not indicators:
            raise ValueError(f"No indicators found for date {asof_date}")

        # Ensure we have all core indicators
        missing = set(self.CORE_INDICATORS.keys()) - set(indicators.keys())
        if missing:
            logger.warning(f"Missing indicators: {missing}")

        # Detect regime
        classification = await self.detector.detect_regime(indicators, asof_date)

        # Store regime snapshot
        await self.store_regime_snapshot(classification)

        return classification

    async def detect_current_regime(self) -> RegimeClassification:
        """
        Detect current macro regime from latest indicators.

        Returns:
            RegimeClassification
        """
        return await self.detect_regime(date.today())

    async def store_regime_snapshot(
        self,
        classification: RegimeClassification,
    ):
        """
        Store regime classification snapshot in database.

        Args:
            classification: RegimeClassification to store
        """
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

        await execute_statement(
            query,
            classification.date,
            classification.regime.value,
            Decimal(str(classification.confidence)),
            json.dumps(classification.indicators),
            json.dumps(classification.zscores),
            json.dumps(classification.regime_probabilities),
        )

        logger.info(
            f"Stored regime snapshot: {classification.regime.value} "
            f"(date: {classification.date}, confidence: {classification.confidence:.2%})"
        )

    async def get_regime_history(
        self,
        start_date: date,
        end_date: Optional[date] = None,
    ) -> List[RegimeClassification]:
        """
        Get historical regime classifications.

        Args:
            start_date: Start date
            end_date: End date (default: today)

        Returns:
            List of RegimeClassification objects
        """
        if end_date is None:
            end_date = date.today()

        query = """
            SELECT
                date,
                regime,
                confidence,
                indicators_json,
                zscores_json,
                regime_scores_json
            FROM regime_history
            WHERE date >= $1 AND date <= $2
            ORDER BY date ASC
        """

        rows = await execute_query(query, start_date, end_date)

        results = []
        for row in rows:
            regime = Regime(row["regime"])
            results.append(
                RegimeClassification(
                    regime=regime,
                    regime_name=self.detector.REGIME_NAMES[regime],
                    confidence=float(row["confidence"]),
                    date=row["date"],
                    indicators=row["indicators_json"],
                    zscores=row["zscores_json"],
                    regime_probabilities=row["regime_scores_json"],
                    drivers={},  # Not stored in DB
                )
            )

        return results


# ============================================================================
# Singleton
# ============================================================================


_macro_service: Optional[MacroService] = None


def get_macro_service(fred_client: Optional[FREDProvider] = None, db_pool=None) -> MacroService:
    """
    DEPRECATED: Use MacroService(fred_client=..., db_pool=...) directly instead.

    Migration:
        OLD: macro_service = get_macro_service()
        NEW: macro_service = MacroService(fred_client=fred_client, db_pool=db_pool)
    """
    import warnings
    warnings.warn(
        "get_macro_service() is deprecated. Use MacroService(fred_client=..., db_pool=...) directly.",
        DeprecationWarning,
        stacklevel=2
    )
    global _macro_service
    if _macro_service is None:
        _macro_service = MacroService(fred_client=fred_client, db_pool=db_pool)
    return _macro_service
