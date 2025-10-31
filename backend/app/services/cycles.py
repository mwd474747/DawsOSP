"""
Macro Cycles Service

Purpose: Detect macro cycle phases (STDC, LTDC, Empire) (Sprint 3 Week 5)
Updated: 2025-10-22
Priority: P1 (Sprint 3)

Features:
    - STDC (Short-Term Debt Cycle): 5-10 year business cycles
    - LTDC (Long-Term Debt Cycle): 50-75 year debt super cycles
    - Empire Cycle: Rise and decline of global powers
    - Composite score computation
    - Phase matching logic

Cycles:
    STDC (5-10 years):
        1. Early Recovery
        2. Mid Expansion
        3. Late Expansion / Boom
        4. Early Recession
        5. Deep Recession

    LTDC (50-75 years):
        1. Deleveraging
        2. Reflation
        3. Expansion
        4. Bubble
        5. Top
        6. Debt Crisis
        7. Depression

    Empire (200-300 years):
        1. Rise
        2. Peak
        3. Decline
        4. Collapse

Architecture:
    Indicators → CycleDetector → CompositeScore → Phase → Database

Usage:
    service = CyclesService()
    stdc_phase = await service.detect_stdc_phase()
    ltdc_phase = await service.detect_ltdc_phase()
    empire_phase = await service.detect_empire_phase()
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json as json_module

from app.db.connection import execute_query, execute_statement, execute_query_one

logger = logging.getLogger("DawsOS.CyclesService")


# ============================================================================
# Enums and Data Models
# ============================================================================


class CycleType(str, Enum):
    """Macro cycle types."""

    STDC = "STDC"  # Short-Term Debt Cycle
    LTDC = "LTDC"  # Long-Term Debt Cycle
    EMPIRE = "EMPIRE"  # Empire Cycle


@dataclass
class CyclePhase:
    """Cycle phase classification."""

    cycle_type: CycleType
    phase: str
    phase_number: int
    composite_score: float
    date: date
    indicators: Dict[str, float]


# ============================================================================
# Cycle Phase Definitions
# ============================================================================

# STDC (Short-Term Debt Cycle) phases
STDC_PHASES = {
    1: "Early Recovery",
    2: "Mid Expansion",
    3: "Late Expansion / Boom",
    4: "Early Recession",
    5: "Deep Recession",
}

# LTDC (Long-Term Debt Cycle) phases
LTDC_PHASES = {
    1: "Deleveraging",
    2: "Reflation",
    3: "Expansion",
    4: "Bubble",
    5: "Top",
    6: "Debt Crisis",
    7: "Depression",
}

# Empire Cycle phases
EMPIRE_PHASES = {
    1: "Rise",
    2: "Peak",
    3: "Decline",
    4: "Collapse",
}


# ============================================================================
# Cycle Detectors
# ============================================================================


class STDCDetector:
    """
    Short-Term Debt Cycle (STDC) detector.

    5-10 year business cycles driven by credit expansion and contraction.
    """

    # Indicator weights for STDC phases
    PHASE_WEIGHTS = {
        "Early Recovery": {
            "T10Y2Y": 2.5,  # Yield curve steepening (strong signal)
            "UNRATE_change": 1.5,  # Unemployment falling
            "INDPRO_change": 1.0,  # Industrial production rising
            "credit_growth": 0.5,  # Credit starting to grow
        },
        "Mid Expansion": {
            "GDP_growth": 2.0,  # Strong GDP growth
            "PAYEMS_change": 1.5,  # Job growth strong
            "credit_growth": 1.0,  # Credit accelerating
            "T10Y2Y": 1.0,  # Yield curve positive
        },
        "Late Expansion / Boom": {
            "CPIAUCSL_yoy": 2.0,  # Inflation rising
            "T10Y2Y": -2.0,  # Yield curve flattening/inverting (negative weight)
            "credit_growth": 1.5,  # Credit growth peaking
            "UNRATE": -1.0,  # Unemployment very low (negative = tight labor)
        },
        "Early Recession": {
            "T10Y2Y": -2.5,  # Yield curve inverted (strong signal)
            "GDP_growth": -1.5,  # GDP growth slowing (negative)
            "INDPRO_change": -1.0,  # Industrial production falling
            "credit_growth": -0.5,  # Credit contracting
        },
        "Deep Recession": {
            "UNRATE_change": 2.5,  # Unemployment rising sharply
            "GDP_growth": -2.0,  # GDP contracting (negative)
            "credit_growth": -2.0,  # Credit contracting sharply
            "PAYEMS_change": -1.5,  # Job losses
        },
    }

    def compute_composite_score(
        self,
        phase_name: str,
        indicators: Dict[str, float],
    ) -> float:
        """
        Compute composite score for a phase.

        Args:
            phase_name: Phase name (e.g., "Early Recovery")
            indicators: Indicator values

        Returns:
            Composite score (weighted sum, normalized 0-100)
        """
        weights = self.PHASE_WEIGHTS.get(phase_name, {})
        total_score = 0.0
        total_weight = 0.0

        for indicator_key, weight in weights.items():
            value = indicators.get(indicator_key, 0.0)

            # Apply weight (positive or negative)
            if weight > 0:
                # Positive weight: higher value = higher score
                contribution = value * weight if value > 0 else 0
            else:
                # Negative weight: lower value = higher score
                contribution = -value * abs(weight) if value < 0 else 0

            total_score += contribution
            total_weight += abs(weight)

        # Normalize to 0-1 (consistent with macro regime confidence scores)
        if total_weight > 0:
            normalized = (total_score / total_weight) / 100
            return max(0.0, min(1.0, normalized))  # Clamp to 0-1
        return 0.0

    def detect_phase(self, indicators: Dict[str, float], as_of_date: date) -> CyclePhase:
        """
        Detect current STDC phase.

        Args:
            indicators: Current indicator values
            as_of_date: Date for phase classification

        Returns:
            CyclePhase
        """
        # Score all phases
        phase_scores = {}
        for phase_number, phase_name in STDC_PHASES.items():
            score = self.compute_composite_score(phase_name, indicators)
            phase_scores[phase_number] = score

        # Find highest scoring phase
        best_phase_num = max(phase_scores, key=phase_scores.get)
        best_score = phase_scores[best_phase_num]

        logger.info(
            f"STDC phase detected: {STDC_PHASES[best_phase_num]} "
            f"(score: {best_score:.1f})"
        )

        return CyclePhase(
            cycle_type=CycleType.STDC,
            phase=STDC_PHASES[best_phase_num],
            phase_number=best_phase_num,
            composite_score=best_score,
            date=as_of_date,
            indicators=indicators,
        )


class LTDCDetector:
    """
    Long-Term Debt Cycle (LTDC) detector.

    50-75 year debt super cycles.
    """

    PHASE_WEIGHTS = {
        "Deleveraging": {
            "debt_to_gdp": -2.5,  # Debt/GDP falling (negative = deleveraging)
            "real_rates": 2.0,  # Real rates high
            "GDP_growth": -1.0,  # Growth weak
        },
        "Reflation": {
            "money_supply_growth": 2.0,  # Money supply growing
            "real_rates": -1.5,  # Real rates negative (negative weight)
            "credit_growth": 1.0,  # Credit starting to expand
        },
        "Expansion": {
            "debt_to_gdp": 1.5,  # Debt/GDP rising moderately
            "GDP_growth": 2.0,  # Strong GDP growth
            "productivity_growth": 1.0,  # Productivity rising
        },
        "Bubble": {
            "debt_to_gdp": 2.5,  # Debt/GDP rising rapidly
            "asset_prices": 2.0,  # Asset prices inflating
            "credit_growth": 2.0,  # Credit bubble
        },
        "Top": {
            "debt_service_ratio": 2.5,  # Debt service costs peaking
            "real_rates": 2.0,  # Real rates rising
            "GDP_growth": -1.0,  # Growth slowing
        },
        "Debt Crisis": {
            "default_rate": 2.5,  # Defaults spiking
            "credit_spread": 2.0,  # Credit spreads widening
            "asset_prices": -2.0,  # Asset prices falling
        },
        "Depression": {
            "GDP_growth": -2.5,  # GDP contracting severely
            "UNRATE": 2.5,  # Unemployment very high
            "debt_to_gdp": -1.5,  # Forced deleveraging
        },
    }

    def compute_composite_score(
        self,
        phase_name: str,
        indicators: Dict[str, float],
    ) -> float:
        """Compute composite score for LTDC phase."""
        weights = self.PHASE_WEIGHTS.get(phase_name, {})
        total_score = 0.0
        total_weight = 0.0

        for indicator_key, weight in weights.items():
            value = indicators.get(indicator_key, 0.0)

            if weight > 0:
                contribution = value * weight if value > 0 else 0
            else:
                contribution = -value * abs(weight) if value < 0 else 0

            total_score += contribution
            total_weight += abs(weight)

        if total_weight > 0:
            normalized = (total_score / total_weight) / 100
            return max(0.0, min(1.0, normalized))
        return 0.0

    def detect_phase(self, indicators: Dict[str, float], as_of_date: date) -> CyclePhase:
        """Detect current LTDC phase."""
        phase_scores = {}
        for phase_number, phase_name in LTDC_PHASES.items():
            score = self.compute_composite_score(phase_name, indicators)
            phase_scores[phase_number] = score

        best_phase_num = max(phase_scores, key=phase_scores.get)
        best_score = phase_scores[best_phase_num]

        logger.info(
            f"LTDC phase detected: {LTDC_PHASES[best_phase_num]} "
            f"(score: {best_score:.1f})"
        )

        return CyclePhase(
            cycle_type=CycleType.LTDC,
            phase=LTDC_PHASES[best_phase_num],
            phase_number=best_phase_num,
            composite_score=best_score,
            date=as_of_date,
            indicators=indicators,
        )


class EmpireDetector:
    """
    Empire Cycle detector.

    200-300 year cycles of rise and decline of global powers.
    """

    PHASE_WEIGHTS = {
        "Rise": {
            "education_investment": 2.0,  # Education spending high
            "innovation_rate": 2.0,  # Innovation accelerating
            "military_strength": 1.5,  # Military growing
            "reserve_currency_share": 1.0,  # Reserve currency adoption
        },
        "Peak": {
            "reserve_currency_share": 2.5,  # Dominant reserve currency
            "military_strength": 2.0,  # Military dominance
            "GDP_share": 2.0,  # High share of global GDP
            "innovation_rate": 1.0,  # Innovation still strong
        },
        "Decline": {
            "debt_to_gdp": 2.0,  # High debt burden
            "reserve_currency_share": -2.0,  # Losing reserve status (negative)
            "education_investment": -1.5,  # Education investment falling
            "inequality": 1.5,  # Rising inequality
        },
        "Collapse": {
            "internal_conflict": 2.5,  # Internal strife
            "reserve_currency_share": -2.5,  # Lost reserve status
            "military_strength": -2.0,  # Military decline
            "GDP_share": -2.0,  # Shrinking GDP share
        },
    }

    def compute_composite_score(
        self,
        phase_name: str,
        indicators: Dict[str, float],
    ) -> float:
        """Compute composite score for Empire phase."""
        weights = self.PHASE_WEIGHTS.get(phase_name, {})
        total_score = 0.0
        total_weight = 0.0

        for indicator_key, weight in weights.items():
            value = indicators.get(indicator_key, 0.0)

            if weight > 0:
                contribution = value * weight if value > 0 else 0
            else:
                contribution = -value * abs(weight) if value < 0 else 0

            total_score += contribution
            total_weight += abs(weight)

        if total_weight > 0:
            normalized = (total_score / total_weight) / 100
            return max(0.0, min(1.0, normalized))
        return 0.0

    def detect_phase(self, indicators: Dict[str, float], as_of_date: date) -> CyclePhase:
        """Detect current Empire phase."""
        phase_scores = {}
        for phase_number, phase_name in EMPIRE_PHASES.items():
            score = self.compute_composite_score(phase_name, indicators)
            phase_scores[phase_number] = score

        best_phase_num = max(phase_scores, key=phase_scores.get)
        best_score = phase_scores[best_phase_num]

        logger.info(
            f"Empire phase detected: {EMPIRE_PHASES[best_phase_num]} "
            f"(score: {best_score:.1f})"
        )

        return CyclePhase(
            cycle_type=CycleType.EMPIRE,
            phase=EMPIRE_PHASES[best_phase_num],
            phase_number=best_phase_num,
            composite_score=best_score,
            date=as_of_date,
            indicators=indicators,
        )


# ============================================================================
# Civil Order Detector
# ============================================================================


class CivilOrderDetector:
    """
    Civil/Internal Order Cycle detector.
    
    Tracks internal social and political stability through 6 stages:
    1. Harmony - Strong social cohesion, low inequality
    2. Rising Tensions - Increasing inequality, declining trust
    3. Polarization - Deep political divisions, social unrest
    4. Crisis - Institutional breakdown, conflict risk
    5. Conflict/Revolution - Active internal conflict
    6. Reconstruction - Rebuilding institutions and trust
    """

    # Civil order phases
    CIVIL_PHASES = {
        1: "Harmony",
        2: "Rising Tensions", 
        3: "Polarization",
        4: "Crisis",
        5: "Conflict/Revolution",
        6: "Reconstruction"
    }

    # Phase detection thresholds
    PHASE_THRESHOLDS = {
        "Harmony": {
            "gini_coefficient": (0.0, 0.30),  # Low inequality
            "institutional_trust": (0.7, 1.0),  # High trust
            "polarization_index": (0.0, 0.3),  # Low polarization
        },
        "Rising Tensions": {
            "gini_coefficient": (0.30, 0.38),  # Moderate inequality
            "institutional_trust": (0.5, 0.7),  # Moderate trust
            "polarization_index": (0.3, 0.45),  # Rising polarization
        },
        "Polarization": {
            "gini_coefficient": (0.38, 0.42),  # High inequality
            "institutional_trust": (0.35, 0.5),  # Declining trust
            "polarization_index": (0.45, 0.65),  # High polarization
        },
        "Crisis": {
            "gini_coefficient": (0.42, 0.48),  # Very high inequality
            "institutional_trust": (0.2, 0.35),  # Very low trust
            "polarization_index": (0.65, 0.80),  # Very high polarization
        },
        "Conflict/Revolution": {
            "gini_coefficient": (0.48, 1.0),  # Extreme inequality
            "institutional_trust": (0.0, 0.2),  # Collapsed trust
            "polarization_index": (0.80, 1.0),  # Extreme polarization
        },
        "Reconstruction": {
            # Special phase - detected by improving metrics after conflict
            "gini_coefficient": (-0.05, 0.0),  # Improving (delta)
            "institutional_trust": (0.05, 0.2),  # Improving (delta)
            "polarization_index": (-0.1, 0.0),  # Improving (delta)
        }
    }

    def compute_composite_score(self, indicators: Dict[str, float]) -> Tuple[str, float]:
        """
        Compute civil order phase and confidence score.
        
        Args:
            indicators: Dict with gini_coefficient, institutional_trust, polarization_index
            
        Returns:
            Tuple of (phase_name, confidence_score)
        """
        # Extract key indicators with defaults
        gini = indicators.get("GINI", indicators.get("gini_coefficient", 0.418))
        trust = indicators.get("institutional_trust", 0.38)
        polarization = indicators.get("polarization_index", 0.78)
        
        # Normalize indicators to 0-1 scale if needed
        if gini > 1.0:  # Likely in percentage form
            gini = gini / 100.0
            
        # Score each phase based on how well indicators match
        phase_scores = {}
        
        for phase_name in ["Harmony", "Rising Tensions", "Polarization", "Crisis", "Conflict/Revolution"]:
            thresholds = self.PHASE_THRESHOLDS[phase_name]
            score = 0.0
            count = 0
            
            # Check Gini coefficient
            if "gini_coefficient" in thresholds:
                min_val, max_val = thresholds["gini_coefficient"]
                if min_val <= gini <= max_val:
                    score += 1.0
                elif gini < min_val:
                    score += max(0, 1.0 - (min_val - gini) * 5)
                else:
                    score += max(0, 1.0 - (gini - max_val) * 5)
                count += 1
                
            # Check institutional trust
            if "institutional_trust" in thresholds:
                min_val, max_val = thresholds["institutional_trust"]
                if min_val <= trust <= max_val:
                    score += 1.0
                elif trust < min_val:
                    score += max(0, 1.0 - (min_val - trust) * 5)
                else:
                    score += max(0, 1.0 - (trust - max_val) * 5)
                count += 1
                
            # Check polarization index
            if "polarization_index" in thresholds:
                min_val, max_val = thresholds["polarization_index"]
                if min_val <= polarization <= max_val:
                    score += 1.0
                elif polarization < min_val:
                    score += max(0, 1.0 - (min_val - polarization) * 5)
                else:
                    score += max(0, 1.0 - (polarization - max_val) * 5)
                count += 1
                
            phase_scores[phase_name] = score / count if count > 0 else 0.0
            
        # Check for reconstruction phase (requires historical comparison)
        # For now, use Crisis as default if indicators suggest improvement
        if gini < 0.40 and trust > 0.3 and polarization < 0.7:
            if phase_scores.get("Crisis", 0) > 0.5:
                phase_scores["Reconstruction"] = 0.6  # Transition phase
                
        # Find best matching phase
        best_phase = max(phase_scores, key=phase_scores.get)
        confidence = phase_scores[best_phase]
        
        return best_phase, confidence

    def detect_phase(self, indicators: Dict[str, float], as_of_date: date) -> CyclePhase:
        """
        Detect current civil order phase.
        
        Args:
            indicators: Current macro/social indicators
            as_of_date: Date for phase classification
            
        Returns:
            CyclePhase
        """
        phase_name, confidence = self.compute_composite_score(indicators)
        
        # Get phase number
        phase_number = 4  # Default to Crisis
        for num, name in self.CIVIL_PHASES.items():
            if name == phase_name:
                phase_number = num
                break
                
        # Create detailed indicators dict
        civil_indicators = {
            "gini_coefficient": float(indicators.get("GINI", indicators.get("gini_coefficient", 0.418))),
            "institutional_trust": float(indicators.get("institutional_trust", 0.38)),
            "polarization_index": float(indicators.get("polarization_index", 0.78)),
            "social_unrest_score": float(indicators.get("social_unrest_score", 0.30)),
            "fiscal_deficit_gdp": float(indicators.get("FYFSGDA188S", indicators.get("fiscal_deficit", -6.20))),
        }
        
        return CyclePhase(
            cycle_type=CycleType.EMPIRE,  # Use EMPIRE for now as CIVIL not defined
            phase=phase_name,
            phase_number=phase_number,
            composite_score=confidence,
            date=as_of_date,
            indicators=civil_indicators
        )


# ============================================================================
# Cycles Service
# ============================================================================


class CyclesService:
    """
    Macro cycles service.

    Detects STDC, LTDC, and Empire cycle phases.
    """

    def __init__(self):
        self.stdc_detector = STDCDetector()
        self.ltdc_detector = LTDCDetector()
        self.empire_detector = EmpireDetector()
        self.civil_detector = CivilOrderDetector()

    async def get_latest_indicators(self) -> Dict[str, float]:
        """
        Get latest macro indicators from database.

        Returns:
            Dictionary of indicator values
        """
        query = """
            SELECT
                indicator_id,
                value
            FROM macro_indicators
            WHERE (indicator_id, date) IN (
                SELECT indicator_id, MAX(date)
                FROM macro_indicators
                GROUP BY indicator_id
            )
        """
        rows = await execute_query(query)

        indicators = {}
        for row in rows:
            indicators[row["indicator_id"]] = float(row["value"])

        # TODO: Compute derived indicators (changes, ratios, etc.)
        # For now, use stub values for missing indicators
        return indicators

    async def detect_stdc_phase(self, as_of_date: Optional[date] = None) -> CyclePhase:
        """
        Detect current STDC phase.

        Args:
            as_of_date: Date for phase classification (default: today)

        Returns:
            CyclePhase
        """
        if as_of_date is None:
            as_of_date = date.today()
        elif isinstance(as_of_date, str):
            # Convert string to date if needed
            from datetime import datetime
            as_of_date = datetime.fromisoformat(as_of_date).date()

        indicators = await self.get_latest_indicators()
        phase = self.stdc_detector.detect_phase(indicators, as_of_date)

        # Store in database
        await self._store_phase(phase)

        return phase

    async def detect_ltdc_phase(self, as_of_date: Optional[date] = None) -> CyclePhase:
        """Detect current LTDC phase."""
        if as_of_date is None:
            as_of_date = date.today()
        elif isinstance(as_of_date, str):
            # Convert string to date if needed
            from datetime import datetime
            as_of_date = datetime.fromisoformat(as_of_date).date()

        indicators = await self.get_latest_indicators()
        phase = self.ltdc_detector.detect_phase(indicators, as_of_date)

        await self._store_phase(phase)

        return phase

    async def detect_empire_phase(self, as_of_date: Optional[date] = None) -> CyclePhase:
        """Detect current Empire phase."""
        if as_of_date is None:
            as_of_date = date.today()
        elif isinstance(as_of_date, str):
            # Convert string to date if needed
            from datetime import datetime
            as_of_date = datetime.fromisoformat(as_of_date).date()

        indicators = await self.get_latest_indicators()
        phase = self.empire_detector.detect_phase(indicators, as_of_date)

        await self._store_phase(phase)

        return phase

    async def detect_civil_phase(self, as_of_date: Optional[date] = None) -> CyclePhase:
        """
        Detect current Civil/Internal Order phase.
        
        Args:
            as_of_date: Date for phase classification (default: today)
            
        Returns:
            CyclePhase
        """
        if as_of_date is None:
            as_of_date = date.today()
        elif isinstance(as_of_date, str):
            # Convert string to date if needed
            from datetime import datetime
            as_of_date = datetime.fromisoformat(as_of_date).date()

        indicators = await self.get_latest_indicators()
        
        # Add default values for civil-specific indicators if not present
        if "institutional_trust" not in indicators:
            indicators["institutional_trust"] = 0.38
        if "polarization_index" not in indicators:
            indicators["polarization_index"] = 0.78
        if "social_unrest_score" not in indicators:
            indicators["social_unrest_score"] = 0.30
            
        phase = self.civil_detector.detect_phase(indicators, as_of_date)

        await self._store_phase(phase)

        return phase

    async def _store_phase(self, phase: CyclePhase):
        """Store cycle phase in database."""
        query = """
            INSERT INTO cycle_phases (
                cycle_type,
                date,
                phase,
                phase_number,
                composite_score,
                indicators_json
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (cycle_type, date)
            DO UPDATE SET
                phase = EXCLUDED.phase,
                phase_number = EXCLUDED.phase_number,
                composite_score = EXCLUDED.composite_score,
                indicators_json = EXCLUDED.indicators_json
        """
        await execute_statement(
            query,
            phase.cycle_type.value,
            phase.date,
            phase.phase,
            phase.phase_number,
            Decimal(str(phase.composite_score)),
            json_module.dumps(phase.indicators),
        )

        logger.info(
            f"Stored {phase.cycle_type.value} phase: {phase.phase} ({phase.date})"
        )


# ============================================================================
# Singleton
# ============================================================================


_cycles_service: Optional[CyclesService] = None


def get_cycles_service() -> CyclesService:
    """
    Get cycles service singleton.

    Returns:
        CyclesService singleton
    """
    global _cycles_service
    if _cycles_service is None:
        _cycles_service = CyclesService()
    return _cycles_service
