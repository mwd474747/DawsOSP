"""
DawsOS Macro Regime API Routes

Purpose: REST API endpoints for macro regime detection and scenario analysis
Created: 2025-10-23
Priority: P0 (Critical for risk management)

Endpoints:
    GET /api/v1/macro/regime - Get current regime classification
    GET /api/v1/macro/regime/history - Get historical regime transitions
    GET /api/v1/macro/indicators - Get macro indicators with z-scores
    POST /api/v1/macro/scenarios - Run scenario stress tests
    POST /api/v1/macro/dar - Compute Drawdown at Risk (DaR)

Usage:
    # Get current regime
    curl http://localhost:8000/api/v1/macro/regime

    # Get regime history
    curl "http://localhost:8000/api/v1/macro/regime/history?start_date=2025-01-01"

    # Run scenario
    curl -X POST http://localhost:8000/api/v1/macro/scenarios \
      -H "Content-Type: application/json" \
      -d '{"portfolio_id": "...", "shock_type": "rates_up", "pack_id": "..."}'

    # Compute DaR
    curl -X POST http://localhost:8000/api/v1/macro/dar \
      -H "Content-Type: application/json" \
      -d '{"portfolio_id": "...", "confidence": 0.95}'
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, Path, Body, Header, Depends
from pydantic import BaseModel, Field, validator

from app.services.macro import get_macro_service, Regime
from app.services.scenarios import get_scenario_service, ShockType
from app.services.risk import get_risk_service
from app.db.connection import get_db_connection_with_rls
from app.middleware.auth_middleware import verify_token
from app.services.auth import get_auth_service
from app.core.constants.http_status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/macro",
    tags=["macro"],
)


# ============================================================================
# Request/Response Models
# ============================================================================


class RegimeResponse(BaseModel):
    """Current regime classification response."""

    regime: str = Field(..., description="Current regime (EARLY_EXPANSION, MID_EXPANSION, etc.)")
    regime_name: str = Field(..., description="Human-readable regime name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in classification (0-1)")
    asof_date: date = Field(..., description="As-of date for classification")

    # Probabilities for all regimes
    probabilities: Dict[str, float] = Field(
        ..., description="Probability distribution over all 5 regimes"
    )

    # Drivers (indicators with z-scores)
    drivers: Dict[str, float] = Field(
        ..., description="Z-scores for key indicators (T10Y2Y, UNRATE, CPI, credit spreads)"
    )

    # Raw indicator values
    indicators: Dict[str, float] = Field(
        ..., description="Raw indicator values"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "regime": "MID_EXPANSION",
                "regime_name": "Mid Expansion",
                "confidence": 0.78,
                "date": "2025-10-23",
                "probabilities": {
                    "EARLY_EXPANSION": 0.05,
                    "MID_EXPANSION": 0.78,
                    "LATE_EXPANSION": 0.12,
                    "EARLY_CONTRACTION": 0.03,
                    "DEEP_CONTRACTION": 0.02,
                },
                "drivers": {
                    "T10Y2Y": 0.5,
                    "UNRATE": -0.8,
                    "CPIAUCSL": 0.2,
                    "BAA10Y": -0.3,
                },
                "indicators": {
                    "T10Y2Y": 0.45,
                    "UNRATE": 3.8,
                    "CPIAUCSL": 3.2,
                    "BAA10Y": 2.1,
                },
            }
        }


class RegimeHistoryResponse(BaseModel):
    """Historical regime transitions response."""

    regimes: List[RegimeResponse] = Field(..., description="Historical regime classifications")
    transitions: int = Field(..., description="Number of regime transitions in period")

    class Config:
        json_schema_extra = {
            "example": {
                "regimes": [
                    {
                        "regime": "MID_EXPANSION",
                        "regime_name": "Mid Expansion",
                        "confidence": 0.78,
                        "date": "2025-10-23",
                        "probabilities": {...},
                        "drivers": {...},
                        "indicators": {...},
                    },
                ],
                "transitions": 2,
            }
        }


class IndicatorsResponse(BaseModel):
    """Macro indicators with z-scores response."""

    indicators: Dict[str, float] = Field(..., description="Raw indicator values")
    zscores: Dict[str, float] = Field(..., description="Z-scores (252-day rolling window)")
    asof_date: date = Field(..., description="As-of date")

    class Config:
        json_schema_extra = {
            "example": {
                "indicators": {
                    "T10Y2Y": 0.45,
                    "UNRATE": 3.8,
                    "CPIAUCSL": 3.2,
                    "BAA10Y": 2.1,
                },
                "zscores": {
                    "T10Y2Y": 0.5,
                    "UNRATE": -0.8,
                    "CPIAUCSL": 0.2,
                    "BAA10Y": -0.3,
                },
                "date": "2025-10-23",
            }
        }


class ScenarioRequest(BaseModel):
    """Scenario stress test request."""

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    shock_type: str = Field(..., description="Shock type (rates_up, rates_down, usd_up, etc.)")
    pack_id: str = Field(..., description="Pricing pack ID")
    custom_shocks: Optional[Dict[str, float]] = Field(
        None, description="Custom factor shocks (optional, overrides pre-defined)"
    )

    @validator("shock_type")
    def validate_shock_type(cls, v):
        """Validate shock_type is a valid ShockType enum."""
        valid_types = [e.value for e in ShockType]
        if v not in valid_types:
            raise ValueError(f"shock_type must be one of: {', '.join(valid_types)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "shock_type": "rates_up",
                "pack_id": "PP_2025-10-23-WM4PM-USD",
            }
        }


class ScenarioResponse(BaseModel):
    """Scenario stress test response."""

    shock_type: str = Field(..., description="Shock type applied")
    portfolio_id: UUID = Field(..., description="Portfolio UUID")

    # Delta P&L
    total_delta_pnl: Decimal = Field(..., description="Total portfolio delta P&L")
    total_delta_pnl_pct: Decimal = Field(..., description="Delta P&L as % of NAV")

    # Winners and losers
    winners: List[Dict[str, Any]] = Field(..., description="Top 5 winners (positive delta P&L)")
    losers: List[Dict[str, Any]] = Field(..., description="Top 5 losers (negative delta P&L)")

    # Hedges
    suggested_hedges: List[Dict[str, str]] = Field(
        ..., description="Suggested hedge ideas for scenario"
    )

    # Metadata
    pack_id: str = Field(..., description="Pricing pack used")
    shock_definition: Dict[str, float] = Field(..., description="Factor shocks applied")

    class Config:
        json_schema_extra = {
            "example": {
                "shock_type": "rates_up",
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_delta_pnl": -12500.0,
                "total_delta_pnl_pct": -2.5,
                "winners": [
                    {"symbol": "GLD", "delta_pnl": 800.0, "reason": "Gold rallies on rate shock"},
                ],
                "losers": [
                    {"symbol": "AAPL", "delta_pnl": -5000.0, "reason": "Growth stock with high duration"},
                ],
                "suggested_hedges": [
                    {
                        "hedge": "Buy TLT puts",
                        "rationale": "Hedge duration risk from rate increase",
                    },
                ],
                "pack_id": "PP_2025-10-23-WM4PM-USD",
                "shock_definition": {"real_rates_bps": 100.0},
            }
        }


class DaRRequest(BaseModel):
    """Drawdown at Risk (DaR) request."""

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="Confidence level (0.95 = 95%)")
    regime: Optional[str] = Field(
        None, description="Regime to condition on (if None, uses current detected regime)"
    )
    horizon_days: int = Field(default=30, ge=1, le=365, description="Forecast horizon in days")
    num_simulations: int = Field(default=10000, ge=1000, le=50000, description="Number of Monte Carlo simulations")

    @validator("regime")
    def validate_regime(cls, v):
        """Validate regime is a valid Regime enum."""
        if v is not None:
            valid_regimes = [e.value for e in Regime]
            if v not in valid_regimes:
                raise ValueError(f"regime must be one of: {', '.join(valid_regimes)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "confidence": 0.95,
                "horizon_days": 30,
                "num_simulations": 10000,
            }
        }


class DaRResponse(BaseModel):
    """Drawdown at Risk (DaR) response."""

    portfolio_id: UUID = Field(..., description="Portfolio UUID")
    confidence: float = Field(..., description="Confidence level used")
    regime: str = Field(..., description="Regime conditioned on")

    # DaR results
    dar: Decimal = Field(..., description="Drawdown at Risk (in portfolio base currency)")
    dar_pct: Decimal = Field(..., description="DaR as % of NAV")

    # Distribution statistics
    mean_drawdown: Decimal = Field(..., description="Mean simulated drawdown")
    median_drawdown: Decimal = Field(..., description="Median simulated drawdown")
    max_drawdown: Decimal = Field(..., description="Maximum simulated drawdown (worst case)")

    # Metadata
    horizon_days: int = Field(..., description="Forecast horizon (days)")
    num_simulations: int = Field(..., description="Number of simulations run")
    current_nav: Decimal = Field(..., description="Current portfolio NAV")

    class Config:
        json_json_schema_extra = {
            "example": {
                "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
                "confidence": 0.95,
                "regime": "MID_EXPANSION",
                "dar": -15000.0,
                "dar_pct": -3.0,
                "mean_drawdown": -5000.0,
                "median_drawdown": -4800.0,
                "max_drawdown": -28000.0,
                "horizon_days": 30,
                "num_simulations": 10000,
                "current_nav": 500000.0,
            }
        }


# ============================================================================
# Helper: Get User ID from JWT Claims
# ============================================================================


def get_user_id_from_claims(claims: dict) -> str:
    """
    Extract user_id from JWT claims.

    Args:
        claims: JWT claims (user_id, email, role)

    Returns:
        User ID string

    Raises:
        HTTPException: If user_id missing
    """
    user_id = claims.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="JWT token missing user_id claim"
        )
    return user_id


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/regime",
    response_model=RegimeResponse,
    summary="Get current macro regime classification",
    description="""
    Detect current macro regime using z-score analysis of key indicators.

    Returns probabilistic classification over 5 regimes:
    - EARLY_EXPANSION: Recovery phase, yield curve steepening
    - MID_EXPANSION: Growth phase, stable indicators
    - LATE_EXPANSION: Overheating, inflation rising
    - EARLY_CONTRACTION: Slowdown begins, yield curve inverted
    - DEEP_CONTRACTION: Recession, unemployment rising sharply

    Indicators used: T10Y2Y, UNRATE, CPIAUCSL, BAA10Y
    """,
)
async def get_current_regime(
    asof_date: Optional[date] = Query(
        default=None,
        description="As-of date for regime classification (defaults to today)",
    ),
) -> RegimeResponse:
    """
    Get current macro regime classification.

    Args:
        asof_date: As-of date (defaults to today)

    Returns:
        RegimeResponse with classification, confidence, probabilities, and drivers

    Raises:
        HTTPException 500: Error detecting regime
    """
    try:
        # Get macro service
        macro_service = get_macro_service()

        # Detect regime
        if asof_date is None:
            asof_date = date.today()

        classification = await macro_service.detect_current_regime(asof_date=asof_date)

        # Build response
        return RegimeResponse(
            regime=classification.regime.value,
            regime_name=classification.regime_name,
            confidence=classification.confidence,
            asof_date=classification.date,
            probabilities=classification.regime_probabilities,
            drivers=classification.drivers,
            indicators=classification.indicators,
        )

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error detecting regime: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error (programming error): {str(e)}",
        )
    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Error detecting regime: {e}", exc_info=True)
        # Don't raise DatabaseError here - convert to HTTPException is intentional
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting regime: {str(e)}",
        )


@router.get(
    "/regime/history",
    response_model=RegimeHistoryResponse,
    summary="Get historical regime classifications",
    description="""
    Get historical regime transitions over a time period.

    Useful for:
    - Understanding regime persistence (how long regimes last)
    - Identifying regime transition dates
    - Backtesting regime-aware strategies
    """,
)
async def get_regime_history(
    start_date: date = Query(..., description="Start date"),
    end_date: Optional[date] = Query(
        default=None,
        description="End date (defaults to today)",
    ),
) -> RegimeHistoryResponse:
    """
    Get historical regime classifications.

    Args:
        start_date: Start date
        end_date: End date (defaults to today)

    Returns:
        RegimeHistoryResponse with list of classifications and transition count

    Raises:
        HTTPException 500: Error fetching regime history
    """
    try:
        # Get macro service
        macro_service = get_macro_service()

        # Fetch history
        if end_date is None:
            end_date = date.today()

        classifications = await macro_service.get_regime_history(
            start_date=start_date,
            end_date=end_date,
        )

        # Build regime responses
        regime_responses = [
            RegimeResponse(
                regime=c.regime.value,
                regime_name=c.regime_name,
                confidence=c.confidence,
                date=c.date,
                probabilities=c.regime_probabilities,
                drivers=c.drivers,
                indicators=c.indicators,
            )
            for c in classifications
        ]

        # Count transitions (regime changes)
        transitions = 0
        for i in range(1, len(classifications)):
            if classifications[i].regime != classifications[i - 1].regime:
                transitions += 1

        return RegimeHistoryResponse(
            regimes=regime_responses,
            transitions=transitions,
        )

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error fetching regime history: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error (programming error): {str(e)}",
        )
    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Error fetching regime history: {e}", exc_info=True)
        # Don't raise DatabaseError here - convert to HTTPException is intentional
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching regime history: {str(e)}",
        )


@router.get(
    "/indicators",
    response_model=IndicatorsResponse,
    summary="Get macro indicators with z-scores",
    description="""
    Get raw macro indicator values and their z-scores.

    Z-scores are computed using a 252-day (1-year) rolling window:
    z = (current_value - rolling_mean) / rolling_std

    Indicators:
    - T10Y2Y: 10Y-2Y Treasury spread (yield curve)
    - UNRATE: Unemployment rate
    - CPIAUCSL: Consumer Price Index (inflation)
    - BAA10Y: Credit spreads (Baa corporate - 10Y Treasury)
    """,
)
async def get_indicators(
    asof_date: Optional[date] = Query(
        default=None,
        description="As-of date for indicators (defaults to today)",
    ),
) -> IndicatorsResponse:
    """
    Get macro indicators with z-scores.

    Args:
        asof_date: As-of date (defaults to today)

    Returns:
        IndicatorsResponse with raw values and z-scores

    Raises:
        HTTPException 500: Error fetching indicators
    """
    try:
        # Get macro service
        macro_service = get_macro_service()

        # Fetch indicators
        if asof_date is None:
            asof_date = date.today()

        # Note: This assumes the macro service has a method to get indicators with z-scores
        # If not available, we call detect_current_regime and extract from it
        classification = await macro_service.detect_current_regime(asof_date=asof_date)

        return IndicatorsResponse(
            indicators=classification.indicators,
            zscores=classification.drivers,  # drivers = z-scores
            asof_date=classification.date,
        )

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error fetching indicators: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error (programming error): {str(e)}",
        )
    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Error fetching indicators: {e}", exc_info=True)
        # Don't raise DatabaseError here - convert to HTTPException is intentional
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching indicators: {str(e)}",
        )


@router.post(
    "/scenarios",
    response_model=ScenarioResponse,
    summary="Run scenario stress test",
    description="""
    Apply a scenario shock to a portfolio and compute delta P&L.

    Pre-defined shock types:
    - rates_up: +100bp rate shock
    - rates_down: -100bp rate shock
    - usd_up: +5% USD appreciation
    - usd_down: -5% USD depreciation
    - cpi_surprise: +1% inflation shock
    - credit_spread_widening: +50bp credit spread shock
    - credit_spread_tightening: -50bp credit spread shock
    - equity_selloff: -10% equity shock
    - equity_rally: +10% equity shock

    Returns winners, losers, and suggested hedges.
    """,
)
async def run_scenario(
    request: ScenarioRequest = Body(...),
    claims: dict = Depends(verify_token),
) -> ScenarioResponse:
    """
    Run scenario stress test.

    Args:
        request: ScenarioRequest with portfolio_id, shock_type, pack_id
        claims: JWT claims (user_id, email, role)

    Returns:
        ScenarioResponse with delta P&L, winners, losers, and hedge suggestions

    Raises:
        HTTPException 400: Invalid shock_type
        HTTPException 404: Portfolio not found
        HTTPException 500: Error running scenario
    """
    user_id = get_user_id_from_claims(claims)
    user_role = claims.get("role", "USER")
    
    # RBAC: Check permission to read analytics
    auth_service = get_auth_service()
    if not auth_service.check_permission(user_role, "read_analytics"):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to run scenario analysis"
        )
    try:
        # Get scenario service
        scenario_service = get_scenario_service()

        # Apply scenario
        result = await scenario_service.apply_scenario(
            portfolio_id=request.portfolio_id,
            shock_type=ShockType(request.shock_type),
            pack_id=request.pack_id,
            custom_shocks=request.custom_shocks,
        )

        # Suggest hedges
        hedges = await scenario_service.suggest_hedges(
            losers=result.losers,
            shock_type=request.shock_type,
        )

        # Build response
        return ScenarioResponse(
            shock_type=request.shock_type,
            portfolio_id=request.portfolio_id,
            total_delta_pnl=result.total_delta_pnl,
            total_delta_pnl_pct=result.total_delta_pnl_pct,
            winners=result.winners,
            losers=result.losers,
            suggested_hedges=hedges,
            pack_id=request.pack_id,
            shock_definition=result.shock_definition,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error running scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error (programming error): {str(e)}",
        )
    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Error running scenario: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running scenario: {str(e)}",
        )


@router.post(
    "/dar",
    response_model=DaRResponse,
    summary="Compute Drawdown at Risk (DaR)",
    description="""
    Compute regime-conditioned Drawdown at Risk using Monte Carlo simulation.

    DaR measures the worst expected drawdown over a time horizon at a given confidence level.

    Example: "At 95% confidence, the portfolio could experience a -3.0% drawdown over
    the next 30 days given the current MID_EXPANSION regime."

    Methodology:
    1. Detect current macro regime (or use specified regime)
    2. Load regime-specific factor covariance matrix
    3. Compute portfolio factor exposures (betas)
    4. Run Monte Carlo simulation (default: 10,000 scenarios)
    5. Extract drawdown at specified confidence level (default: 95%)

    Unlike VaR (Value at Risk), DaR focuses on peak-to-trough drawdown rather than
    single-period loss.
    """,
)
async def compute_dar(
    request: DaRRequest = Body(...),
    claims: dict = Depends(verify_token),
) -> DaRResponse:
    """
    Compute Drawdown at Risk (DaR).

    Args:
        request: DaRRequest with portfolio_id, confidence, regime, horizon_days
        claims: JWT claims (user_id, email, role)

    Returns:
        DaRResponse with DaR, distribution statistics, and metadata

    Raises:
        HTTPException 404: Portfolio not found
        HTTPException 500: Error computing DaR
    """
    user_id = get_user_id_from_claims(claims)
    user_role = claims.get("role", "USER")
    
    # RBAC: Check permission to read analytics
    auth_service = get_auth_service()
    if not auth_service.check_permission(user_role, "read_analytics"):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to compute risk analytics"
        )
    try:
        # Get services
        risk_service = get_risk_service()
        macro_service = get_macro_service()

        # Determine regime (use specified or detect current)
        if request.regime is None:
            classification = await macro_service.detect_current_regime()
            regime = classification.regime.value
        else:
            regime = request.regime

        # Compute DaR
        dar_result = await risk_service.compute_dar(
            portfolio_id=request.portfolio_id,
            regime=regime,
            confidence=request.confidence,
            horizon_days=request.horizon_days,
            num_simulations=request.num_simulations,
        )

        # Build response
        return DaRResponse(
            portfolio_id=request.portfolio_id,
            confidence=request.confidence,
            regime=regime,
            dar=dar_result.dar,
            dar_pct=dar_result.dar_pct,
            mean_drawdown=dar_result.mean_drawdown,
            median_drawdown=dar_result.median_drawdown,
            max_drawdown=dar_result.max_drawdown,
            horizon_days=request.horizon_days,
            num_simulations=request.num_simulations,
            current_nav=dar_result.current_nav,
        )

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error computing DaR: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error (programming error): {str(e)}",
        )
    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Error computing DaR: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing DaR: {str(e)}",
        )
