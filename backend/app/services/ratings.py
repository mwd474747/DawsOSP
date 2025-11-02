"""
DawsOS Ratings Service - Buffett Quality Scoring

Purpose: Calculate quality ratings (dividend safety, moat strength, resilience) on 0-10 scale
Specification: .claude/agents/business/RATINGS_ARCHITECT.md (lines 175-407)
Governance: P0-CODE-1 remediation (2025-10-26)

Architecture:
    Agent → RatingsService → rating_rubrics table → Database

Implemented Features:
    - ✅ Calculate ratings using correct thresholds from spec
    - ✅ Load research-based weights from rating_rubrics table (database-driven)
    - ✅ Graceful fallback to hardcoded weights if database unavailable
    - ✅ Return component scores for agent formatting (no duplication)
    - ✅ Accept fundamentals dict (FMP integration in progress)

Rubric Weights (Loaded from Database):
    - dividend_safety: fcf_coverage=35%, payout_ratio=30%, growth_streak=20%, net_cash=15%
    - moat_strength: roe_consistency=35%, gross_margin=30%, intangibles=20%, switching_costs=15%
    - resilience: debt_equity=40%, current_ratio=25%, interest_coverage=20%, margin_stability=15%

Future Scope:
    - Integrate with FMP provider for real fundamental data transformation
    - Add database persistence for calculated ratings (ratings table)
    - Add caching layer for performance optimization

CRITICAL: This service returns component scores to prevent duplication in agent layer.
"""

import json
import logging
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger("DawsOS.RatingsService")

# Singleton instance
_ratings_service = None


class RatingsService:
    """
    Ratings calculation service.

    Returns Dict with component scores (not just overall rating).
    This prevents duplication - agent layer only formats, doesn't recalculate.
    """

    def __init__(self, use_db: bool = True, db_pool=None):
        """
        Initialize ratings service.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
            db_pool: AsyncPG connection pool (optional, will get from connection module if not provided)
        """
        self.use_db = use_db
        self.db_pool = db_pool
        self.rubrics = {}  # Cache for loaded rubrics
        
        if not use_db:
            logger.info("RatingsService initialized in stub mode")
        else:
            logger.info("RatingsService initialized")

    async def _load_rubrics(self) -> Dict[str, Dict]:
        """
        Load rating rubrics from database.

        Returns:
            Dict mapping rating_type to rubric data:
            {
                "dividend_safety": {"overall_weights": {...}, "component_thresholds": {...}, ...},
                "moat_strength": {...},
                "resilience": {...}
            }
        """
        if not self.db_pool:
            # Lazy import to avoid circular dependency
            from app.db.connection import get_db_pool
            self.db_pool = get_db_pool()

        query = """
            SELECT
                rating_type,
                method_version,
                overall_weights,
                component_thresholds,
                description,
                research_basis
            FROM rating_rubrics
            WHERE method_version = 'v1'
            ORDER BY rating_type
        """

        rubrics = {}
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query)
            for row in rows:
                rating_type = row["rating_type"]
                rubrics[rating_type] = {
                    "method_version": row["method_version"],
                    "overall_weights": row["overall_weights"],  # Already a dict from asyncpg
                    "component_thresholds": row["component_thresholds"],  # Already a dict from asyncpg
                    "description": row["description"],
                    "research_basis": row["research_basis"],
                }

        logger.info(f"Loaded {len(rubrics)} rating rubrics from database: {list(rubrics.keys())}")
        return rubrics

    async def _get_weights(self, rating_type: str) -> tuple[Dict[str, Decimal], str]:
        """
        Get component weights for a rating type.

        Loads from database if not cached. Falls back to hardcoded weights if database load fails.

        Args:
            rating_type: One of 'dividend_safety', 'moat_strength', 'resilience'

        Returns:
            Tuple of (weights dict, source):
                - weights: Dict mapping component names to Decimal weights
                - source: "rubric" if loaded from database, "fallback" if using hardcoded weights
        """
        # Load rubrics if not already cached
        if not self.rubrics:
            try:
                self.rubrics = await self._load_rubrics()
            except Exception as e:
                logger.error(f"Failed to load rubrics from database: {e}")
                self.rubrics = {}  # Empty dict triggers fallback

        # Get weights from rubric, or use fallback
        if rating_type in self.rubrics:
            weights_data = self.rubrics[rating_type]["overall_weights"]

            # Handle both dict (from asyncpg JSONB) and string (from JSON parsing)
            if isinstance(weights_data, str):
                weights_dict = json.loads(weights_data)
            else:
                weights_dict = weights_data

            # Convert to Decimal
            weights = {k: Decimal(str(v)) for k, v in weights_dict.items()}
            return (weights, "rubric")
        else:
            logger.warning(f"Rubric not found for {rating_type}, using fallback equal weights")
            weights = self._get_fallback_weights(rating_type)
            return (weights, "fallback")

    def _get_fallback_weights(self, rating_type: str) -> Dict[str, Decimal]:
        """
        Get hardcoded fallback weights when database rubrics unavailable.

        Args:
            rating_type: One of 'dividend_safety', 'moat_strength', 'resilience'

        Returns:
            Dict mapping component names to equal Decimal weights (25% each)
        """
        if rating_type == "dividend_safety":
            # Dividend safety has spec-defined weights (SPEC LINES 548-553)
            return {
                "payout_ratio": Decimal("0.30"),
                "fcf_coverage": Decimal("0.35"),
                "growth_streak": Decimal("0.20"),
                "net_cash": Decimal("0.15"),
            }
        elif rating_type == "moat_strength":
            return {
                "roe_consistency": Decimal("0.25"),
                "gross_margin": Decimal("0.25"),
                "intangibles": Decimal("0.25"),
                "switching_costs": Decimal("0.25"),
            }
        elif rating_type == "resilience":
            return {
                "debt_equity": Decimal("0.25"),
                "interest_coverage": Decimal("0.25"),
                "current_ratio": Decimal("0.25"),
                "margin_stability": Decimal("0.25"),
            }
        else:
            raise ValueError(f"Unknown rating_type: {rating_type}")

    async def calculate_dividend_safety(
        self,
        symbol: str,
        fundamentals: Dict[str, Any],
        security_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Calculate dividend safety (0-10 scale).

        Specification: .claude/agents/business/RATINGS_ARCHITECT.md lines 217-269

        Components (SPEC LINES 217-247):
            1. Payout ratio (5-year avg): <30%=10, <50%=7, <70%=5, else=2
            2. FCF coverage: >3.0=10, >2.0=7, >1.0=5, else=2
            3. Dividend growth streak: >=20=10, >=10=9, >=5=7, else=5
            4. Net cash position: >$50B=10, >$10B=8, >$1B=6, else=4

        Weights (SPEC LINES 548-553):
            - payout_ratio: 30%
            - fcf_coverage: 35%
            - growth_streak: 20%
            - net_cash: 15%

        Args:
            symbol: Security symbol (for logging)
            fundamentals: Dict with keys:
                - payout_ratio_5y_avg: Decimal
                - fcf_dividend_coverage: Decimal
                - dividend_growth_streak_years: int
                - net_cash_position: Decimal
            security_id: Optional security UUID (for future database persistence)

        Returns:
            Dict with:
                - overall: Decimal (0-10 weighted average)
                - components: Dict[str, Dict] with score/value/weight for each component
                - symbol: str
                - rating_type: str
        """
        # Component 1: Payout ratio (SPEC LINES 217-224)
        payout_ratio = Decimal(str(fundamentals.get("payout_ratio_5y_avg", 0)))
        if payout_ratio < Decimal("0.30"):
            payout_score = Decimal("10")
        elif payout_ratio < Decimal("0.50"):
            payout_score = Decimal("7")
        elif payout_ratio < Decimal("0.70"):
            payout_score = Decimal("5")
        else:
            payout_score = Decimal("2")

        # Component 2: FCF coverage (SPEC LINES 225-232)
        fcf_coverage = Decimal(str(fundamentals.get("fcf_dividend_coverage", 0)))
        if fcf_coverage > Decimal("3.0"):
            fcf_score = Decimal("10")
        elif fcf_coverage > Decimal("2.0"):
            fcf_score = Decimal("7")
        elif fcf_coverage > Decimal("1.0"):
            fcf_score = Decimal("5")
        else:
            fcf_score = Decimal("2")

        # Component 3: Dividend growth streak (SPEC LINES 233-240)
        streak_years = fundamentals.get("dividend_growth_streak_years", 0)
        if streak_years >= 20:
            streak_score = Decimal("10")
        elif streak_years >= 10:
            streak_score = Decimal("9")
        elif streak_years >= 5:
            streak_score = Decimal("7")
        else:
            streak_score = Decimal("5")

        # Component 4: Net cash position (SPEC LINES 241-247)
        net_cash = Decimal(str(fundamentals.get("net_cash_position", 0)))
        if net_cash > Decimal("50000000000"):  # $50B
            cash_score = Decimal("10")
        elif net_cash > Decimal("10000000000"):  # $10B
            cash_score = Decimal("8")
        elif net_cash > Decimal("1000000000"):  # $1B
            cash_score = Decimal("6")
        else:
            cash_score = Decimal("4")

        # Load weights from database (SPEC LINES 548-553)
        weights, weights_source = await self._get_weights("dividend_safety")

        # Weighted average (SPEC LINES 259-266)
        overall = (
            payout_score * weights["payout_ratio"]
            + fcf_score * weights["fcf_coverage"]
            + streak_score * weights["growth_streak"]
            + cash_score * weights["net_cash"]
        )

        # Return components for agent formatting (prevents duplication)
        return {
            "overall": overall,
            "rating_type": "dividend_safety",
            "symbol": symbol,
            "security_id": str(security_id) if security_id else None,
            "_metadata": {
                "weights_source": weights_source,  # "rubric" or "fallback"
                "method_version": "v1"
            },
            "components": {
                "payout_ratio": {
                    "score": payout_score,
                    "value": payout_ratio,
                    "weight": weights["payout_ratio"],
                    "label": "Payout Ratio (5Y Avg)",
                },
                "fcf_coverage": {
                    "score": fcf_score,
                    "value": fcf_coverage,
                    "weight": weights["fcf_coverage"],
                    "label": "FCF Dividend Coverage",
                },
                "growth_streak": {
                    "score": streak_score,
                    "value": streak_years,
                    "weight": weights["growth_streak"],
                    "label": "Dividend Growth Streak (Years)",
                },
                "net_cash": {
                    "score": cash_score,
                    "value": net_cash,
                    "weight": weights["net_cash"],
                    "label": "Net Cash Position",
                },
            },
        }

    async def calculate_moat_strength(
        self,
        symbol: str,
        fundamentals: Dict[str, Any],
        security_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Calculate economic moat strength (0-10 scale).

        Specification: .claude/agents/business/RATINGS_ARCHITECT.md lines 275-333

        Components (SPEC LINES 290-322):
            1. ROE consistency (5Y): >20%=10, >15%=8, >10%=6, else=4
            2. Gross margin (5Y): >60%=10, >40%=8, >25%=6, else=4
            3. Intangible assets ratio: >30%=8, >15%=6, else=4
            4. Switching costs: Qualitative score from rubric (default 5)

        Weights (Loaded from Database):
            Research-based weights from rating_rubrics.overall_weights:
                - roe_consistency: 35% (Buffett's key competitive advantage indicator)
                - gross_margin: 30% (pricing power indicator, Buffett prefers >40%)
                - intangibles: 20% (brand/patent value)
                - switching_costs: 15% (qualitative, sector-dependent)

            Fallback (if database unavailable): Equal 25% weights

        Args:
            symbol: Security symbol
            fundamentals: Dict with keys:
                - roe_5y_avg: Decimal
                - gross_margin_5y_avg: Decimal
                - intangible_assets_ratio: Decimal
                - switching_cost_score: Decimal (optional, default 5)
            security_id: Optional security UUID (for future database persistence)

        Returns:
            Dict with overall score and component breakdown
        """
        # Component 1: ROE consistency (SPEC LINES 290-299)
        roe = Decimal(str(fundamentals.get("roe_5y_avg", 0)))
        if roe > Decimal("0.20"):  # > 20%
            roe_score = Decimal("10")
        elif roe > Decimal("0.15"):
            roe_score = Decimal("8")
        elif roe > Decimal("0.10"):
            roe_score = Decimal("6")
        else:
            roe_score = Decimal("4")

        # Component 2: Gross margin (SPEC LINES 301-310)
        gross_margin = Decimal(str(fundamentals.get("gross_margin_5y_avg", 0)))
        if gross_margin > Decimal("0.60"):
            margin_score = Decimal("10")
        elif gross_margin > Decimal("0.40"):
            margin_score = Decimal("8")
        elif gross_margin > Decimal("0.25"):
            margin_score = Decimal("6")
        else:
            margin_score = Decimal("4")

        # Component 3: Intangible assets (SPEC LINES 312-319)
        intangibles = Decimal(str(fundamentals.get("intangible_assets_ratio", 0)))
        if intangibles > Decimal("0.30"):
            intangibles_score = Decimal("8")
        elif intangibles > Decimal("0.15"):
            intangibles_score = Decimal("6")
        else:
            intangibles_score = Decimal("4")

        # Component 4: Switching costs (SPEC LINE 322)
        switching_score = Decimal(str(fundamentals.get("switching_cost_score", 5)))

        # Load weights from database (research-based, see seed files)
        weights, weights_source = await self._get_weights("moat_strength")

        # Weighted average (SPEC LINES 325-331)
        overall = (
            roe_score * weights["roe_consistency"]
            + margin_score * weights["gross_margin"]
            + intangibles_score * weights["intangibles"]
            + switching_score * weights["switching_costs"]
        )

        return {
            "overall": overall,
            "rating_type": "moat_strength",
            "symbol": symbol,
            "security_id": str(security_id) if security_id else None,
            "_metadata": {
                "weights_source": weights_source,  # "rubric" or "fallback"
                "method_version": "v1"
            },
            "components": {
                "roe_consistency": {
                    "score": roe_score,
                    "value": roe,
                    "weight": weights["roe_consistency"],
                    "label": "ROE Consistency (5Y Avg)",
                },
                "gross_margin": {
                    "score": margin_score,
                    "value": gross_margin,
                    "weight": weights["gross_margin"],
                    "label": "Gross Margin (5Y Avg)",
                },
                "intangibles": {
                    "score": intangibles_score,
                    "value": intangibles,
                    "weight": weights["intangibles"],
                    "label": "Intangible Assets Ratio",
                },
                "switching_costs": {
                    "score": switching_score,
                    "value": switching_score,  # Qualitative score
                    "weight": weights["switching_costs"],
                    "label": "Switching Costs (Qualitative)",
                },
            },
        }

    async def calculate_resilience(
        self,
        symbol: str,
        fundamentals: Dict[str, Any],
        security_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Calculate financial resilience (0-10 scale).

        Specification: .claude/agents/business/RATINGS_ARCHITECT.md lines 335-407

        Components (SPEC LINES 355-393):
            1. Debt/Equity: <0.5=10, <1.0=8, <2.0=6, else=3
            2. Interest coverage: >10=10, >5=8, >2=6, else=3
            3. Current ratio: >2.0=10, >1.5=8, >1.0=7, else=4
            4. Operating margin stability (std dev): <2%=10, <5%=8, <10%=6, else=4

        Weights (Loaded from Database):
            Research-based weights from rating_rubrics.overall_weights:
                - debt_equity: 40% (Buffett strongly emphasizes low debt, <0.5 ideal)
                - current_ratio: 25% (short-term liquidity, Buffett wants >1.5)
                - interest_coverage: 20% (debt service capacity)
                - margin_stability: 15% (earnings consistency over 5 years)

            Fallback (if database unavailable): Equal 25% weights

        Args:
            symbol: Security symbol
            fundamentals: Dict with keys:
                - debt_equity_ratio: Decimal
                - interest_coverage: Decimal
                - current_ratio: Decimal
                - operating_margin_std_dev: Decimal (5-year)
            security_id: Optional security UUID (for future database persistence)

        Returns:
            Dict with overall score and component breakdown
        """
        # Component 1: Debt/Equity (SPEC LINES 355-364)
        debt_equity = Decimal(str(fundamentals.get("debt_equity_ratio", 0)))
        if debt_equity < Decimal("0.50"):
            de_score = Decimal("10")
        elif debt_equity < Decimal("1.00"):
            de_score = Decimal("8")
        elif debt_equity < Decimal("2.00"):
            de_score = Decimal("6")
        else:
            de_score = Decimal("3")

        # Component 2: Interest coverage (SPEC LINES 366-375)
        interest_cov = Decimal(str(fundamentals.get("interest_coverage", 0)))
        if interest_cov > Decimal("10.0"):
            ic_score = Decimal("10")
        elif interest_cov > Decimal("5.0"):
            ic_score = Decimal("8")
        elif interest_cov > Decimal("2.0"):
            ic_score = Decimal("6")
        else:
            ic_score = Decimal("3")

        # Component 3: Current ratio (SPEC LINES 377-386)
        current_ratio = Decimal(str(fundamentals.get("current_ratio", 0)))
        if current_ratio > Decimal("2.0"):
            cr_score = Decimal("10")
        elif current_ratio > Decimal("1.5"):
            cr_score = Decimal("8")
        elif current_ratio > Decimal("1.0"):
            cr_score = Decimal("7")
        else:
            cr_score = Decimal("4")

        # Component 4: Operating margin stability (SPEC LINES 388-393)
        margin_std = Decimal(str(fundamentals.get("operating_margin_std_dev", 0)))
        if margin_std < Decimal("0.02"):  # <2%
            stability_score = Decimal("10")
        elif margin_std < Decimal("0.05"):
            stability_score = Decimal("8")
        elif margin_std < Decimal("0.10"):
            stability_score = Decimal("6")
        else:
            stability_score = Decimal("4")

        # Load weights from database (research-based, see seed files)
        weights, weights_source = await self._get_weights("resilience")

        # Weighted average (SPEC LINES 400-406)
        overall = (
            de_score * weights["debt_equity"]
            + ic_score * weights["interest_coverage"]
            + cr_score * weights["current_ratio"]
            + stability_score * weights["margin_stability"]
        )

        return {
            "overall": overall,
            "rating_type": "resilience",
            "symbol": symbol,
            "security_id": str(security_id) if security_id else None,
            "_metadata": {
                "weights_source": weights_source,  # "rubric" or "fallback"
                "method_version": "v1"
            },
            "components": {
                "debt_equity": {
                    "score": de_score,
                    "value": debt_equity,
                    "weight": weights["debt_equity"],
                    "label": "Debt-to-Equity Ratio",
                },
                "interest_coverage": {
                    "score": ic_score,
                    "value": interest_cov,
                    "weight": weights["interest_coverage"],
                    "label": "Interest Coverage",
                },
                "current_ratio": {
                    "score": cr_score,
                    "value": current_ratio,
                    "weight": weights["current_ratio"],
                    "label": "Current Ratio",
                },
                "margin_stability": {
                    "score": stability_score,
                    "value": margin_std,
                    "weight": weights["margin_stability"],
                    "label": "Operating Margin Stability (Std Dev)",
                },
            },
        }

    async def aggregate(
        self,
        symbol: str,
        fundamentals: Dict[str, Any],
        security_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Calculate aggregate quality rating combining all three ratings.

        Specification: Buffett Quality Framework

        Aggregation Weights:
            - moat_strength: 40% (competitive advantage is paramount)
            - dividend_safety: 30% (income reliability)
            - resilience: 30% (financial strength during downturns)

        Args:
            symbol: Security symbol
            fundamentals: Dict with all required fundamental fields
            security_id: Optional security UUID (for future database persistence)

        Returns:
            Dict with:
                - overall_rating: Decimal (0-100 scale)
                - overall_grade: str (A-F letter grade)
                - moat: Dict (moat_strength result with 0-100 scale)
                - resilience: Dict (resilience result with 0-100 scale)
                - dividend: Dict (dividend_safety result with 0-100 scale)
                - symbol: str
                - security_id: Optional[UUID]
        """
        
        # Calculate individual ratings (0-10 scale)
        moat_result = await self.calculate_moat_strength(symbol, fundamentals)
        resilience_result = await self.calculate_resilience(symbol, fundamentals)
        dividend_result = await self.calculate_dividend_safety(symbol, fundamentals)

        # Convert to 0-100 scale
        moat_100 = moat_result["overall"] * Decimal("10")
        resilience_100 = resilience_result["overall"] * Decimal("10")
        dividend_100 = dividend_result["overall"] * Decimal("10")

        # Aggregate with weights (moat 40%, dividend 30%, resilience 30%)
        overall_rating = (
            moat_100 * Decimal("0.40")
            + dividend_100 * Decimal("0.30")
            + resilience_100 * Decimal("0.30")
        )

        # Convert to letter grade
        overall_grade = self._rating_to_grade(overall_rating)

        # Add grades and 0-100 scale to individual results
        moat_result["rating_100"] = moat_100
        moat_result["grade"] = self._rating_to_grade(moat_100)
        resilience_result["rating_100"] = resilience_100
        resilience_result["grade"] = self._rating_to_grade(resilience_100)
        dividend_result["rating_100"] = dividend_100
        dividend_result["grade"] = self._rating_to_grade(dividend_100)

        return {
            "overall_rating": overall_rating,
            "overall_grade": overall_grade,
            "symbol": symbol,
            "security_id": str(security_id) if security_id else None,
            "aggregation_weights": {
                "moat_strength": Decimal("0.40"),
                "dividend_safety": Decimal("0.30"),
                "resilience": Decimal("0.30"),
            },
            "moat": moat_result,
            "resilience": resilience_result,
            "dividend": dividend_result,
        }

    def _rating_to_grade(self, rating: Decimal) -> str:
        """
        Convert numeric rating (0-100 scale) to letter grade.

        Grading Scale:
            A: 90-100 (Exceptional quality - Buffett's "wonderful company")
            B: 80-89  (Strong quality - Buffett's "good company")
            C: 70-79  (Acceptable quality - requires fair price)
            D: 60-69  (Below average - avoid unless deeply discounted)
            F: <60    (Poor quality - stay away)

        Args:
            rating: Numeric rating on 0-100 scale

        Returns:
            Letter grade (A, B, C, D, F)
        """
        if rating >= Decimal("90"):
            return "A"
        elif rating >= Decimal("80"):
            return "B"
        elif rating >= Decimal("70"):
            return "C"
        elif rating >= Decimal("60"):
            return "D"
        else:
            return "F"


def get_ratings_service() -> RatingsService:
    """Get or create singleton ratings service."""
    global _ratings_service
    if _ratings_service is None:
        _ratings_service = RatingsService()
    return _ratings_service
