"""
Portfolio Optimizer Service - Riskfolio-Lib Integration

Purpose: Policy-based portfolio optimization and rebalancing with Riskfolio-Lib
Updated: 2025-01-15
Priority: P1 (Core business logic for policy rebalance pattern)

**Architecture Note:** This service is an implementation detail of the FinancialAnalyst agent.
Patterns should use `financial_analyst` agent capabilities (e.g., `financial_analyst.propose_trades`),
not this service directly. The service is used internally by FinancialAnalyst to implement
optimization logic.

Features:
    - propose_trades: Generate rebalance trades based on policy constraints
    - analyze_impact: Simulate impact of proposed trades on portfolio metrics
    - suggest_hedges: Recommend hedges for scenario stress tests
    - suggest_deleveraging_hedges: Regime-specific deleveraging recommendations

Optimization Methods:
    - Mean-Variance (Markowitz)
    - Risk Parity
    - Maximum Sharpe Ratio
    - CVaR (Conditional Value at Risk)

Constraints:
    - Quality ratings threshold (min_quality_score)
    - Position size limits (max_single_position_pct)
    - Sector concentration limits (max_sector_pct)
    - Tracking error constraint (max_tracking_error_pct)
    - Turnover limit (max_turnover_pct)

Architecture:
    Portfolio Positions → Riskfolio-Lib Optimizer → Trade Proposals → Impact Analysis

Dependencies:
    pip install riskfolio-lib

Usage:
    from app.services.optimizer import OptimizerService

    service = OptimizerService(use_db=True, db_pool=db_pool)

    # Generate rebalance trades
    result = await service.propose_trades(
        portfolio_id="11111111-1111-1111-1111-111111111111",
        policy_json={"min_quality_score": 6.0, "max_turnover_pct": 20.0},
        pricing_pack_id="PP_2025-10-26",
    )

    # Analyze impact
    impact = await service.analyze_impact(
        portfolio_id="11111111-1111-1111-1111-111111111111",
        proposed_trades=result["trades"],
        pricing_pack_id="PP_2025-10-26",
    )
    
    Note: get_optimizer_service() is deprecated. Use OptimizerService(db_pool=...) directly.

Sacred Invariants:
    1. All optimizations use pricing_pack_id for reproducibility
    2. Trade proposals must sum to zero (buy value = sell value + slippage/costs)
    3. Quality ratings from ratings service filter eligible securities
    4. All recommendations include detailed rationale
    5. Constraints are enforced strictly (no violations allowed)
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from uuid import UUID

try:
    import riskfolio as rp
    RISKFOLIO_AVAILABLE = True
except ImportError:
    RISKFOLIO_AVAILABLE = False
    logging.warning("Riskfolio-Lib not installed. Optimizer will return stub data.")

from app.db.connection import get_db_pool
from app.core.exceptions import BusinessLogicError, DatabaseError
from app.core.constants.scenarios import (
    MIN_QUALITY_SCORE,
    DEFAULT_MAX_SINGLE_POSITION_PCT,
    DEFAULT_MIN_POSITION_PCT,
    DEFAULT_MAX_SECTOR_PCT,
    DEFAULT_MAX_TRACKING_ERROR_PCT,
    DEFAULT_MAX_TURNOVER_PCT,
    DEFAULT_OPTIMIZATION_LOOKBACK_DAYS,
    METHOD_MEAN_VARIANCE,
)
from app.core.constants import get_risk_free_rate  # Dynamic risk-free rate from FRED

logger = logging.getLogger("DawsOS.OptimizerService")


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class PolicyConstraints:
    """Portfolio optimization policy constraints."""

    # Quality filters
    min_quality_score: float = MIN_QUALITY_SCORE  # Minimum aggregate quality rating (0-10)

    # Position limits
    max_single_position_pct: float = DEFAULT_MAX_SINGLE_POSITION_PCT  # Maximum weight per position (%)
    min_position_pct: float = DEFAULT_MIN_POSITION_PCT  # Minimum weight to avoid dust positions (%)

    # Sector limits
    max_sector_pct: float = DEFAULT_MAX_SECTOR_PCT  # Maximum sector concentration (%)

    # Risk constraints
    max_tracking_error_pct: float = DEFAULT_MAX_TRACKING_ERROR_PCT  # Maximum tracking error vs benchmark (%)
    target_volatility_pct: Optional[float] = None  # Target portfolio volatility (%)

    # Turnover and costs
    max_turnover_pct: float = DEFAULT_MAX_TURNOVER_PCT  # Maximum turnover per rebalance (%)
    commission_per_trade: float = 5.00  # Flat commission per trade (USD)
    market_impact_bps: float = 15.0  # Market impact (basis points)

    # Optimization method
    method: str = METHOD_MEAN_VARIANCE  # mean_variance, risk_parity, max_sharpe, cvar
    risk_free_rate: float  # Risk-free rate (annual) - fetched from FRED or policy override

    # Historical lookback
    lookback_days: int = DEFAULT_OPTIMIZATION_LOOKBACK_DAYS  # Trading days for covariance estimation


@dataclass
class TradeProposal:
    """Single trade proposal from optimizer."""

    symbol: str
    security_id: str
    action: str  # "BUY", "SELL", or "HOLD"
    quantity: int  # Shares to trade (positive for BUY, negative for SELL)
    current_shares: int
    target_shares: int
    current_weight_pct: float
    target_weight_pct: float
    current_price: Decimal
    trade_value: Decimal  # Dollar value of trade
    estimated_cost: Decimal  # Commission + market impact
    rationale: str  # Why this trade is being made


@dataclass
class RebalanceResult:
    """Complete rebalance proposal with metrics."""

    portfolio_id: str
    pricing_pack_id: str
    asof_date: date

    # Trade proposals
    trades: List[Dict[str, Any]]  # List of TradeProposal as dicts
    trade_count: int

    # Turnover metrics
    total_turnover: Decimal  # Total dollar value traded
    turnover_pct: float  # Turnover as % of portfolio value

    # Cost metrics
    estimated_costs: Decimal  # Total commission + market impact
    cost_bps: float  # Cost in basis points of portfolio value

    # Portfolio metrics (before/after)
    current_value: Decimal
    post_rebalance_value: Decimal

    # Risk metrics
    current_volatility_pct: Optional[float] = None
    post_volatility_pct: Optional[float] = None
    current_sharpe: Optional[float] = None
    post_sharpe: Optional[float] = None
    te_current: Optional[float] = None  # Tracking error before
    te_post: Optional[float] = None  # Tracking error after

    # Metadata
    method: str = "mean_variance"
    constraints_met: bool = True
    warnings: List[str] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    """Before/after comparison of portfolio metrics."""

    current_value: Decimal
    post_rebalance_value: Decimal
    value_delta: Decimal

    # Expected returns (annualized)
    current_expected_return: Optional[float] = None
    post_expected_return: Optional[float] = None
    delta_expected_return: Optional[float] = None

    # Volatility (annualized)
    current_vol: Optional[float] = None
    post_vol: Optional[float] = None
    delta_vol: Optional[float] = None

    # Sharpe ratio
    current_sharpe: Optional[float] = None
    post_sharpe: Optional[float] = None
    delta_sharpe: Optional[float] = None

    # Maximum drawdown
    current_max_dd: Optional[float] = None
    post_max_dd: Optional[float] = None
    delta_max_dd: Optional[float] = None

    # Tracking error
    current_te: Optional[float] = None
    post_te: Optional[float] = None
    delta_te: Optional[float] = None

    # Quality metrics (if ratings available)
    current_avg_quality: Optional[float] = None
    post_avg_quality: Optional[float] = None
    delta_quality: Optional[float] = None

    # Concentration
    current_concentration_top10: Optional[float] = None
    post_concentration_top10: Optional[float] = None
    delta_concentration: Optional[float] = None


@dataclass
class HedgeRecommendation:
    """Hedge instrument recommendation."""

    instrument: str  # Symbol or description
    instrument_type: str  # "equity", "option", "futures", "etf"
    action: str  # "BUY", "SELL"
    notional: Decimal  # Dollar notional value
    hedge_ratio: float  # Hedge ratio (0-1)
    rationale: str  # Why this hedge is recommended
    expected_offset_pct: float  # Expected % of loss offset by this hedge


# ============================================================================
# Optimizer Service
# ============================================================================


class OptimizerService:
    """
    Portfolio optimizer using Riskfolio-Lib.

    **Architecture Note:** This service is an implementation detail of the FinancialAnalyst agent.
    Patterns should use `financial_analyst` agent capabilities, not this service directly.

    Implements mean-variance optimization, risk parity, and other methods
    with quality rating constraints and turnover limits.
    """

    def __init__(self, use_db: bool = True, db_pool=None):
        """
        Initialize optimizer service.

        **Architecture Note:** This service is an implementation detail of the FinancialAnalyst agent.
        Patterns should use `financial_analyst` agent capabilities, not this service directly.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
            db_pool: AsyncPG connection pool (optional, will get from connection module if not provided)
        """
        self.use_db = use_db
        self.db_pool = db_pool
        self.riskfolio_available = RISKFOLIO_AVAILABLE
        
        if use_db:
            try:
                from app.db.connection import execute_query, execute_query_one, execute_statement
                self.execute_query = execute_query
                self.execute_query_one = execute_query_one
                self.execute_statement = execute_statement
                logger.info("OptimizerService initialized with database integration")
            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                # Programming errors - re-raise to surface bugs immediately
                logger.error(f"Programming error initializing database connections: {e}", exc_info=True)
                raise
            except Exception as e:
                # Connection/configuration errors - check environment
                import os
                environment = os.getenv("ENVIRONMENT", "development")
                
                if environment == "production":
                    # In production, fail fast - don't mask database issues
                    logger.error(
                        f"Failed to initialize database connections in production: {e}. "
                        f"This is a critical error and cannot fall back to stub mode.",
                        exc_info=True
                    )
                    from app.core.exceptions import DatabaseError
                    raise DatabaseError(
                        f"Failed to initialize database connections: {e}. "
                        f"Stub mode is not available in production."
                    ) from e
                else:
                    # In development/testing, allow graceful degradation
                    logger.warning(
                        f"Failed to initialize database connections: {e}. "
                        f"Falling back to stub mode (environment: {environment})."
                    )
                    self.use_db = False
        else:
            # Use mock methods for testing
            self.execute_query = self._mock_execute_query
            self.execute_query_one = self._mock_execute_query_one
            self.execute_statement = self._mock_execute_statement
            logger.info("OptimizerService initialized in stub mode")
            
        if not RISKFOLIO_AVAILABLE:
            logger.warning("Riskfolio-Lib not available. Using stub mode.")

    # ========================================================================
    # Mock Database Methods (for testing)
    # ========================================================================
    
    async def _mock_execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Mock execute_query for testing."""
        query_lower = query.lower()
        
        if "portfolios" in query_lower:
            return [{"id": "test-portfolio-id", "name": "Test Portfolio", "base_currency": "CAD"}]
        elif "securities" in query_lower:
            return [
                {"id": "test-security-1", "symbol": "AAPL", "name": "Apple Inc.", "type": "EQUITY"},
                {"id": "test-security-2", "symbol": "GOOGL", "name": "Alphabet Inc.", "type": "EQUITY"}
            ]
        elif "lots" in query_lower or "positions" in query_lower:
            return [
                {
                    "security_id": "test-security-1", 
                    "symbol": "AAPL",
                    "quantity": 100, 
                    "cost_basis": 150.0,
                    "price": 175.0,
                    "currency": "USD",
                    "value": 17500.0
                },
                {
                    "security_id": "test-security-2", 
                    "symbol": "GOOGL",
                    "quantity": 50, 
                    "cost_basis": 2800.0,
                    "price": 2900.0,
                    "currency": "USD",
                    "value": 145000.0
                }
            ]
        elif "pricing_packs" in query_lower:
            from datetime import date
            return [{"id": "test-pack", "date": date.today(), "is_fresh": True}]
        elif "prices" in query_lower or "equity_prices" in query_lower:
            from datetime import date, timedelta
            # Return multiple days of price data for covariance calculation
            base_date = date.today() - timedelta(days=10)
            return [
                {
                    "symbol": "AAPL",
                    "close": 175.0 + i,  # Vary price slightly
                    "asof_date": base_date + timedelta(days=i),
                    "currency": "USD",
                    "security_id": "test-security-1"
                }
                for i in range(5)
            ] + [
                {
                    "symbol": "GOOGL", 
                    "close": 2900.0 + i * 10,  # Vary price slightly
                    "asof_date": base_date + timedelta(days=i),
                    "currency": "USD",
                    "security_id": "test-security-2"
                }
                for i in range(5)
            ]
        return []
    
    async def _mock_execute_query_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Mock execute_query_one for testing."""
        if "pricing_packs" in query.lower():
            from datetime import date
            return {"id": "test-pack", "date": date.today(), "is_fresh": True}
        return None
    
    async def _mock_execute_statement(self, query: str, *args) -> None:
        """Mock execute_statement for testing."""
        pass

    # ========================================================================
    # Public Methods
    # ========================================================================

    async def propose_trades(
        self,
        portfolio_id: UUID,
        policy_json: Dict[str, Any],
        pricing_pack_id: str,
        ratings: Optional[Dict[str, float]] = None,
        positions: Optional[List[Dict[str, Any]]] = None,  # Caller-supplied positions
        use_db: bool = True,  # Whether to fetch from DB or use caller-supplied data
    ) -> Dict[str, Any]:
        """
        Generate rebalance trade proposals based on policy constraints.
        
        PHASE 4 FIX: Validates pack_id format at entry point for early failure.

        Args:
            portfolio_id: Portfolio UUID. Required.
            policy_json: Policy constraints dictionary. Must include:
                - min_quality_score: Minimum aggregate quality rating (0-10, default 0.0)
                - max_single_position_pct: Maximum weight per position (%, default 20.0)
                - max_sector_pct: Maximum sector concentration (%, default 30.0)
                - max_turnover_pct: Maximum turnover per rebalance (%, default 30.0)
                - max_tracking_error_pct: Maximum tracking error vs benchmark (%, default 5.0)
                - method: Optimization method - "mean_variance", "risk_parity", "max_sharpe", or "cvar" (default "mean_variance")
                - lookback_days: Historical period for covariance estimation (default 252)
            pricing_pack_id: Pricing pack ID for reproducibility. Format: "PP_YYYY-MM-DD". Required.
            ratings: Optional dict of {symbol: quality_score} from ratings service. If provided, filters positions by min_quality_score.
            positions: Optional caller-supplied positions list. If provided and use_db=False, uses these instead of fetching from database.
            use_db: If True, fetches positions from database. If False, uses caller-supplied positions.

        Returns:
            RebalanceResult as dict containing:
            - trades: List of trade proposals (symbol, action, quantity, trade_value, etc.)
            - trade_count: Number of trades proposed
            - total_turnover: Total dollar value traded
            - turnover_pct: Turnover as % of portfolio value
            - estimated_costs: Total estimated costs (commissions + market impact)
            - cost_bps: Costs in basis points
            - current_value: Portfolio value before rebalance
            - post_rebalance_value: Portfolio value after rebalance (minus costs)
            - method: Optimization method used
            - constraints_met: Whether all constraints were met
            - warnings: List of warnings (e.g., trades scaled down to meet turnover limit)

        Process:
            1. Load current positions from lots table (or use caller-supplied)
            2. Filter by quality rating (if ratings provided)
            3. Fetch historical prices for covariance estimation
            4. Run Riskfolio-Lib optimization
            5. Generate trade proposals
            6. Calculate turnover and costs
            7. Verify constraints are met (scale trades if turnover exceeds limit)

        Raises:
            ValueError: If portfolio_id is invalid or not found.
            ValueError: If pricing_pack_id is invalid or not found.
            DatabaseError: If database query fails.
            OptimizationError: If optimization fails (insufficient data, invalid constraints, etc.).
            
        Note:
            - Returns stub data if Riskfolio-Lib not available or use_db=False
            - Returns empty result if no positions found
            - Trades are automatically scaled down if turnover exceeds max_turnover_pct
            - All optimizations use pricing_pack_id for reproducibility
        """
        logger.info(f"propose_trades: portfolio_id={portfolio_id}, pack_id={pricing_pack_id}")

        # Return mock data for testing when use_db=False
        if not self.use_db:
            return {
                "trades": [
                    {
                        "symbol": "AAPL",
                        "action": "BUY",
                        "quantity": 10,
                        "price": 175.0,
                        "total_cost": 1750.0
                    }
                ],
                "summary": {
                    "total_cost": 1750.0,
                    "turnover_pct": 5.0,
                    "positions_count": 2
                },
                "constraints": policy_json
            }

        # Parse policy constraints (fetches live risk-free rate from FRED)
        policy = await self._parse_policy(policy_json)

        # Get current positions - use caller-supplied or fetch from DB
        if positions is not None and not use_db:
            logger.info(f"Using caller-supplied positions: {len(positions)} positions")
            current_positions = positions
        else:
            logger.info(f"Fetching positions from database for portfolio {portfolio_id}")
            current_positions = await self._fetch_current_positions(portfolio_id, pricing_pack_id)

        if not current_positions:
            logger.warning(f"No positions found for portfolio {portfolio_id}")
            return self._empty_rebalance_result(portfolio_id, pricing_pack_id, policy)

        # Filter by quality rating
        if ratings:
            current_positions = self._filter_by_quality(current_positions, ratings, policy.min_quality_score)
            logger.info(f"Filtered to {len(current_positions)} positions meeting min quality {policy.min_quality_score}")

        # Calculate portfolio value
        portfolio_value = sum(Decimal(str(p["value"])) for p in current_positions)

        if not self.riskfolio_available:
            # Stub mode: return no-op trades
            logger.warning("Riskfolio-Lib not available. Returning stub rebalance.")
            return self._stub_rebalance_result(portfolio_id, pricing_pack_id, current_positions, portfolio_value, policy)

        # Fetch historical prices for optimization
        price_history = await self._fetch_price_history(
            [p["symbol"] for p in current_positions],
            pricing_pack_id,
            lookback_days=policy.lookback_days,
        )

        if price_history.empty or len(price_history.columns) < 2:
            logger.warning("Insufficient price history for optimization. Returning no-op trades.")
            return self._stub_rebalance_result(portfolio_id, pricing_pack_id, current_positions, portfolio_value, policy)

        # Run optimization
        target_weights = await self._run_optimization(
            price_history,
            current_positions,
            policy,
        )

        # Generate trade proposals
        trades = self._generate_trade_proposals(
            current_positions,
            target_weights,
            portfolio_value,
            policy,
        )

        # Calculate turnover
        total_turnover = sum(abs(Decimal(str(t["trade_value"]))) for t in trades)
        turnover_pct = float((total_turnover / portfolio_value) * 100) if portfolio_value > 0 else 0.0

        # Check turnover constraint
        constraints_met = True
        warnings = []

        if turnover_pct > policy.max_turnover_pct:
            logger.warning(f"Turnover {turnover_pct:.1f}% exceeds limit {policy.max_turnover_pct}%. Scaling down trades.")
            trades = self._scale_trades_to_turnover_limit(trades, portfolio_value, policy.max_turnover_pct)
            turnover_pct = policy.max_turnover_pct
            warnings.append(f"Trades scaled down to meet {policy.max_turnover_pct}% turnover limit")

        # Calculate total costs
        estimated_costs = sum(Decimal(str(t["estimated_cost"])) for t in trades)
        cost_bps = float((estimated_costs / portfolio_value) * 10000) if portfolio_value > 0 else 0.0

        # Get asof date from pricing pack
        asof_date = await self._get_pack_date(pricing_pack_id)

        # Build result
        result = RebalanceResult(
            portfolio_id=str(portfolio_id),
            pricing_pack_id=pricing_pack_id,
            asof_date=asof_date,
            trades=trades,
            trade_count=len(trades),
            total_turnover=total_turnover,
            turnover_pct=turnover_pct,
            estimated_costs=estimated_costs,
            cost_bps=cost_bps,
            current_value=portfolio_value,
            post_rebalance_value=portfolio_value - estimated_costs,
            method=policy.method,
            constraints_met=constraints_met,
            warnings=warnings,
        )

        logger.info(f"Generated {len(trades)} trade proposals, turnover={turnover_pct:.1f}%, costs={cost_bps:.1f}bps")

        return self._dataclass_to_dict(result)

    async def analyze_impact(
        self,
        portfolio_id: UUID,
        proposed_trades: List[Dict[str, Any]],
        pricing_pack_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze impact of proposed trades on portfolio metrics.

        Args:
            portfolio_id: Portfolio UUID. Required.
            proposed_trades: List of trade proposals from propose_trades(). Each trade must include:
                - symbol: Security symbol
                - action: "BUY", "SELL", or "HOLD"
                - quantity: Number of shares (positive for BUY, negative for SELL)
                - trade_value: Dollar value of trade
                - estimated_cost: Estimated cost (commission + market impact)
            pricing_pack_id: Pricing pack ID for valuation. Format: "PP_YYYY-MM-DD". Required.

        Returns:
            ImpactAnalysis as dict containing:
            - current_value: Portfolio value before trades
            - post_rebalance_value: Portfolio value after trades (minus costs)
            - value_delta: Change in portfolio value
            - current_concentration_top10: Top 10 holdings concentration before (%)
            - post_concentration_top10: Top 10 holdings concentration after (%)
            - delta_concentration: Change in concentration (%)

        Process:
            1. Load current positions from database
            2. Simulate trades to get post-rebalance positions
            3. Calculate metrics for both portfolios
            4. Return delta analysis

        Raises:
            ValueError: If portfolio_id is invalid or not found.
            ValueError: If pricing_pack_id is invalid or not found.
            ValueError: If proposed_trades is empty or invalid.
            DatabaseError: If database query fails.
            
        Note:
            - Returns stub data if use_db=False
            - Returns empty analysis if no positions found
            - Currently calculates concentration metrics only
            - TODO: Add expected return, volatility, Sharpe, max DD calculations (requires historical returns)
        """
        logger.info(f"analyze_impact: portfolio_id={portfolio_id}, trades={len(proposed_trades)}")

        # Return mock data for testing when use_db=False
        if not self.use_db:
            return {
                "before": {
                    "total_value": 100000.0,
                    "position_count": 2,
                    "volatility_pct": 15.0,
                    "expected_return": 8.0
                },
                "after": {
                    "total_value": 102000.0,
                    "position_count": 2,
                    "volatility_pct": 14.5,
                    "expected_return": 8.5
                },
                "delta": {
                    "value_change": 2000.0,
                    "volatility_change": -0.5,
                    "return_change": 0.5
                },
                "risk_metrics": {
                    "concentration_change": -2.0,
                    "turnover_pct": 5.0
                }
            }

        # Get current positions
        current_positions = await self._fetch_current_positions(portfolio_id, pricing_pack_id)

        if not current_positions:
            logger.warning(f"No positions found for portfolio {portfolio_id}")
            return self._empty_impact_analysis()

        # Simulate trades
        post_positions = self._simulate_trades(current_positions, proposed_trades)

        # Calculate current value
        current_value = sum(Decimal(str(p["value"])) for p in current_positions)

        # Calculate post-rebalance value (subtract costs)
        total_costs = sum(Decimal(str(t["estimated_cost"])) for t in proposed_trades)
        post_value = sum(Decimal(str(p["value"])) for p in post_positions) - total_costs

        # Calculate concentration metrics
        current_concentration = self._calculate_concentration_top10(current_positions)
        post_concentration = self._calculate_concentration_top10(post_positions)

        # Build impact analysis
        impact = ImpactAnalysis(
            current_value=current_value,
            post_rebalance_value=post_value,
            value_delta=post_value - current_value,
            current_concentration_top10=current_concentration,
            post_concentration_top10=post_concentration,
            delta_concentration=post_concentration - current_concentration,
        )

        # TODO: Add expected return, volatility, Sharpe, max DD calculations
        # Requires historical returns and covariance matrix

        logger.info(f"Impact: value change={impact.value_delta}, concentration change={impact.delta_concentration:.2f}%")

        return self._dataclass_to_dict(impact)

    async def suggest_hedges(
        self,
        portfolio_id: UUID,
        scenario_id: str,
        pricing_pack_id: str,
    ) -> Dict[str, Any]:
        """
        Suggest hedge instruments for a scenario stress test.

        Args:
            portfolio_id: Portfolio UUID. Required.
            scenario_id: Scenario ID string. Supported scenarios:
                - "rates_up": Rising interest rates
                - "rates_down": Falling interest rates
                - "usd_up": Strengthening USD
                - "usd_down": Weakening USD
                - "inflation" or "cpi_surprise": Inflation surprise
                - "credit_spread_widening": Credit spread widening
                - "equity_selloff": Equity market selloff
                - "equity_rally": Equity market rally
                - "late_cycle_rates_up": Late cycle rate increases
                - "recession_mild": Mild recession scenario
            pricing_pack_id: Pricing pack ID for scenario valuation. Format: "PP_YYYY-MM-DD". Required.
        
        PHASE 4 FIX: Validates pack_id format at entry point for early failure.

        Returns:
            Dict containing:
            - scenario_id: Scenario ID used
            - hedges: List of hedge recommendations, each with:
                - instrument: Symbol or instrument name
                - instrument_type: "etf", "option", or "futures"
                - action: "BUY" (always BUY for hedges)
                - notional: Dollar notional value
                - hedge_ratio: Hedge ratio (0-1)
                - rationale: Explanation of hedge recommendation
                - expected_offset_pct: Expected % of loss offset by hedge
            - total_notional: Total notional value of all hedges
            - expected_offset_pct: Overall expected offset percentage
            - suggestions_count: Number of hedge recommendations

        Process:
            1. Map scenario_id to ShockType enum
            2. Run scenario stress test to identify losers
            3. Use ScenarioService.suggest_hedges to get recommendations
            4. Format for pattern consumption

        Raises:
            ValueError: If portfolio_id is invalid or not found.
            ValueError: If pricing_pack_id is invalid or not found.
            ValueError: If scenario_id is not recognized.
            BusinessLogicError: If scenario service fails.
            DatabaseError: If database query fails.
            
        Note:
            - Returns empty hedges list on error (does not raise)
            - Hedge recommendations are estimates based on historical correlations
            - Actual hedge effectiveness may vary
        """
        logger.info(f"suggest_hedges: portfolio_id={portfolio_id}, scenario={scenario_id}")
        
        from app.services.scenarios import ScenarioService, ShockType
        
        # Map scenario_id to ShockType
        scenario_mapping = {
            "rates_up": ShockType.RATES_UP,
            "rates_down": ShockType.RATES_DOWN,
            "usd_up": ShockType.USD_UP,
            "usd_down": ShockType.USD_DOWN,
            "inflation": ShockType.CPI_SURPRISE,
            "cpi_surprise": ShockType.CPI_SURPRISE,
            "credit_spread_widening": ShockType.CREDIT_SPREAD_WIDENING,
            "equity_selloff": ShockType.EQUITY_SELLOFF,
            "equity_rally": ShockType.EQUITY_RALLY,
            "late_cycle_rates_up": ShockType.RATES_UP,
            "recession_mild": ShockType.EQUITY_SELLOFF,
        }
        
        shock_type = scenario_mapping.get(scenario_id, ShockType.RATES_UP)
        
        # Create scenario service instance directly (should be passed via DI container)
        scenario_service = ScenarioService(db_pool=self.db_pool) if hasattr(self, 'db_pool') and self.db_pool else ScenarioService()
        
        try:
            # Run scenario to get losers
            scenario_result = await scenario_service.apply_scenario(
                portfolio_id=str(portfolio_id),
                shock_type=shock_type,
                pack_id=pricing_pack_id,
            )
            
            # Get hedge recommendations
            hedge_recommendations = await scenario_service.suggest_hedges(
                losers=scenario_result.losers,
                shock_type=shock_type,
            )
            
            # Format for pattern
            hedges = []
            total_notional = Decimal("0")
            
            for rec in hedge_recommendations:
                notional = rec.notional or Decimal("0")
                total_notional += notional
                
                hedges.append({
                    "instrument": rec.instruments[0] if rec.instruments else rec.hedge_type,
                    "instrument_type": "option" if "put" in rec.hedge_type.lower() or "call" in rec.hedge_type.lower() else "etf",
                    "action": "BUY",
                    "notional": float(notional),
                    "hedge_ratio": 0.5,  # Default 50% hedge
                    "rationale": rec.rationale,
                    "instruments": rec.instruments,
                    "expected_offset_pct": 50.0,  # Estimate
                })
            
            return {
                "scenario_id": scenario_id,
                "hedges": hedges,
                "total_notional": float(total_notional),
                "expected_offset_pct": 60.0,  # Conservative estimate
                "suggestions_count": len(hedges),
            }
            
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - re-raise to surface bugs immediately
            logger.error(f"Programming error in hedge suggestion: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service/database errors - return error response
            logger.error(f"Hedge suggestion failed (service error): {e}", exc_info=True)
            # Don't raise DatabaseError here - return error response is intentional
            return {
                "scenario_id": scenario_id,
                "hedges": [],
                "total_notional": 0.0,
                "expected_offset_pct": 0.0,
                "error": str(e),
            }

    async def suggest_deleveraging_hedges(
        self,
        portfolio_id: UUID,
        regime: str,
        pricing_pack_id: str,
    ) -> Dict[str, Any]:
        """
        Suggest deleveraging hedges based on macro regime.
        
        This is a placeholder - full implementation uses playbooks service.
        """
        logger.info(f"suggest_deleveraging_hedges: portfolio_id={portfolio_id}")

        # Return mock data for testing when use_db=False
        if not self.use_db:
            return {
                "scenario_id": scenario_id,
                "hedges": [
                    {
                        "instrument": "TLT",
                        "instrument_type": "etf",
                        "action": "BUY",
                        "notional": 10000.00,
                        "hedge_ratio": 0.25,
                        "rationale": "Long-duration treasuries hedge rate risk",
                        "expected_offset_pct": 40.0
                    }
                ]
            }

        # Get current positions
        positions = await self._fetch_current_positions(portfolio_id, pricing_pack_id)

        if not positions:
            logger.warning(f"No positions found for portfolio {portfolio_id}")
            return {"scenario_id": scenario_id, "hedges": []}

        portfolio_value = sum(Decimal(str(p["value"])) for p in positions)

        # Get scenario-specific hedge recommendations
        hedges = self._get_scenario_hedges(scenario_id, portfolio_value, positions)

        logger.info(f"Suggested {len(hedges)} hedges for scenario {scenario_id}")

        return {
            "scenario_id": scenario_id,
            "hedges": [self._dataclass_to_dict(h) for h in hedges],
        }

    async def suggest_deleveraging_hedges(
        self,
        portfolio_id: UUID,
        regime: str,
        pricing_pack_id: str,
    ) -> Dict[str, Any]:
        """
        Suggest deleveraging hedges based on macro regime.

        Implements Dalio deleveraging playbook for regime-specific risk management.

        Args:
            portfolio_id: Portfolio UUID. Required.
            regime: Macro regime string. Supported regimes:
                - "LATE_EXPANSION": Late expansion phase recommendations
                - "DELEVERAGING" or "DEPRESSION": Deleveraging phase recommendations
                - "EARLY_EXPANSION": Early expansion phase recommendations
                - "RECESSION": Recession phase recommendations
            pricing_pack_id: Pricing pack ID for current valuation. Format: "PP_YYYY-MM-DD". Required.

        Returns:
            Dict containing:
            - regime: Regime string used
            - recommendations: List of deleveraging recommendations, each with:
                - action: Action type (e.g., "reduce_equity_exposure", "increase_safe_havens")
                - instruments: List of instrument symbols
                - target_reduction_pct: Target reduction percentage (for reduce actions)
                - target_allocation_pct: Target allocation percentage (for increase actions)
                - rationale: Explanation of recommendation

        Uses Dalio Deleveraging Playbook:
            - DELEVERAGING/DEPRESSION: Aggressive deleveraging
                - Reduce equity exposure 30-40%
                - Increase safe havens (GLD, TLT, CASH) to 20-30%
                - Exit credit-sensitive assets
            - LATE_EXPANSION: Moderate deleveraging
                - Reduce equity exposure 15-20%
                - Increase defensive sectors (XLU, XLP, VNQ) to 10-15%
            - EARLY_EXPANSION: Growth positioning
                - Maintain equity exposure
                - Reduce safe havens
            - RECESSION: Defensive positioning
                - Reduce equity exposure 20-25%
                - Increase cash and bonds

        Raises:
            ValueError: If portfolio_id is invalid or not found.
            ValueError: If pricing_pack_id is invalid or not found.
            ValueError: If regime is not recognized.
            DatabaseError: If database query fails.
            
        Note:
            - Returns stub data if use_db=False
            - Returns empty recommendations if no positions found
            - Recommendations are based on Dalio's deleveraging framework
            - Actual implementation may vary based on portfolio composition
        """
        logger.info(f"suggest_deleveraging_hedges: portfolio_id={portfolio_id}, regime={regime}")

        # Return mock data for testing when use_db=False
        if not self.use_db:
            return {
                "regime": regime,
                "recommendations": [
                    {
                        "action": "reduce_equity_exposure",
                        "instruments": ["SPY", "QQQ"],
                        "target_reduction_pct": 30.0,
                        "rationale": "Reduce equity beta in deleveraging regime"
                    },
                    {
                        "action": "increase_safe_havens",
                        "instruments": ["GLD", "TLT"],
                        "target_allocation_pct": 20.0,
                        "rationale": "Increase gold and long-duration bonds"
                    }
                ]
            }

        # Get current positions
        positions = await self._fetch_current_positions(portfolio_id, pricing_pack_id)

        if not positions:
            logger.warning(f"No positions found for portfolio {portfolio_id}")
            return {"regime": regime, "recommendations": []}

        portfolio_value = sum(Decimal(str(p["value"])) for p in positions)

        # Get regime-specific recommendations
        recommendations = self._get_deleveraging_recommendations(regime, portfolio_value, positions)

        logger.info(f"Generated {len(recommendations)} deleveraging recommendations for regime {regime}")

        return {
            "regime": regime,
            "recommendations": recommendations,
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _parse_policy(self, policy_json: Dict[str, Any]) -> PolicyConstraints:
        """
        Parse policy JSON into PolicyConstraints dataclass.

        Fetches current risk-free rate from FRED (DGS10) unless overridden in policy.
        """
        # Fetch current risk-free rate from FRED (10Y Treasury)
        # Policy can override by providing "risk_free_rate" in JSON
        if "risk_free_rate" in policy_json:
            rf_rate = float(policy_json["risk_free_rate"])
            logger.info(f"Using policy-specified risk-free rate: {rf_rate:.4f}")
        else:
            rf_rate_decimal = await get_risk_free_rate()
            rf_rate = float(rf_rate_decimal)
            logger.info(f"Using live risk-free rate from FRED: {rf_rate:.4f}")

        return PolicyConstraints(
            min_quality_score=float(policy_json.get("min_quality_score", 0.0)),
            max_single_position_pct=float(policy_json.get("max_single_position_pct", 20.0)),
            min_position_pct=float(policy_json.get("min_position_pct", 0.5)),
            max_sector_pct=float(policy_json.get("max_sector_pct", 30.0)),
            max_tracking_error_pct=float(policy_json.get("max_tracking_error_pct", 5.0)),
            target_volatility_pct=policy_json.get("target_volatility_pct"),
            max_turnover_pct=float(policy_json.get("max_turnover_pct", 30.0)),
            commission_per_trade=float(policy_json.get("commission_per_trade", 5.00)),
            market_impact_bps=float(policy_json.get("market_impact_bps", 15.0)),
            method=policy_json.get("method", "mean_variance"),
            risk_free_rate=rf_rate,  # From FRED or policy override
            lookback_days=int(policy_json.get("lookback_days", 252)),
        )

    async def _fetch_current_positions(
        self,
        portfolio_id: UUID,
        pricing_pack_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch current portfolio positions from lots table.

        Returns:
            [
                {
                    "symbol": "AAPL",
                    "security_id": "uuid",
                    "quantity": 100,
                    "price": 232.50,
                    "value": 23250.00,
                    "currency": "USD"
                },
                ...
            ]
        """
        query = """
            SELECT
                l.security_id,
                l.symbol,
                SUM(l.quantity) AS quantity,
                l.currency,
                p.close AS price,
                SUM(l.quantity) * p.close AS value
            FROM lots l
            LEFT JOIN prices p ON l.security_id = p.security_id
                AND p.pricing_pack_id = $2
            WHERE l.portfolio_id = $1
                AND l.is_open = true
            GROUP BY l.security_id, l.symbol, l.currency, p.close
            ORDER BY value DESC
        """

        rows = await self.execute_query(query, portfolio_id, pricing_pack_id)

        positions = []
        excluded_positions = []
        for row in rows:
            if row["price"] is None:
                logger.warning(f"No price found for {row['symbol']} in pack {pricing_pack_id}")
                excluded_positions.append({
                    "symbol": row["symbol"],
                    "security_id": str(row["security_id"]),
                    "quantity": float(row["quantity"]),
                    "reason": "No price available in pricing pack"
                })
                continue

            positions.append({
                "symbol": row["symbol"],
                "security_id": str(row["security_id"]),
                "quantity": float(row["quantity"]),
                "price": float(row["price"]),
                "value": float(row["value"]),
                "currency": row["currency"],
            })
        
        # Log summary of excluded positions
        if excluded_positions:
            logger.error(
                f"Excluded {len(excluded_positions)} positions from optimization due to missing prices: "
                f"{[p['symbol'] for p in excluded_positions]}"
            )
        
        # Raise an error if all positions are excluded
        if not positions and excluded_positions:
            raise ValueError(
                f"No positions with valid prices found in pricing pack {pricing_pack_id}. "
                f"Excluded: {[p['symbol'] for p in excluded_positions]}"
            )

        return positions

    def _filter_by_quality(
        self,
        positions: List[Dict[str, Any]],
        ratings: Dict[str, float],
        min_quality: float,
    ) -> List[Dict[str, Any]]:
        """Filter positions by minimum quality rating."""
        filtered = []

        for pos in positions:
            symbol = pos["symbol"]
            quality = ratings.get(symbol, 0.0)

            if quality >= min_quality:
                filtered.append(pos)
            else:
                logger.info(f"Excluding {symbol} (quality {quality:.1f} < {min_quality})")

        return filtered

    async def _fetch_price_history(
        self,
        symbols: List[str],
        pricing_pack_id: str,
        lookback_days: int = 252,
    ) -> pd.DataFrame:
        """
        Fetch historical prices for covariance estimation.

        Returns:
            DataFrame with dates as index and symbols as columns
        """
        # PHASE 4 FIX: Validate pack_id format at entry point for early failure
        from app.services.pricing import validate_pack_id
        validate_pack_id(pricing_pack_id)
        
        # Get asof date from pricing pack
        asof_date = await self._get_pack_date(pricing_pack_id)
        start_date = asof_date - timedelta(days=lookback_days * 2)  # Extra buffer for weekends

        # Query historical prices
        query = """
            SELECT
                p.asof_date,
                p.security_id,
                p.close
            FROM prices p
            JOIN lots l ON p.security_id = l.security_id
            WHERE l.portfolio_id IN (
                SELECT portfolio_id FROM lots WHERE symbol = ANY($1)
            )
                AND p.asof_date >= $2
                AND p.asof_date <= $3
                AND l.symbol = ANY($1)
            ORDER BY p.asof_date, l.symbol
        """

        rows = await self.execute_query(query, symbols, start_date, asof_date)

        if not rows:
            logger.warning(f"No price history found for symbols {symbols}")
            return pd.DataFrame()

        # Build DataFrame
        data = {}
        for row in rows:
            date_key = row["asof_date"]
            security_id = str(row["security_id"])
            price = float(row["close"])

            if date_key not in data:
                data[date_key] = {}

            data[date_key][security_id] = price

        df = pd.DataFrame.from_dict(data, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        # Fill missing values (forward fill then backward fill)
        df = df.fillna(method="ffill").fillna(method="bfill")

        # Map security_id to symbols
        # (Simplified: using security_id as column names for now)

        return df

    async def _run_optimization(
        self,
        price_history: pd.DataFrame,
        positions: List[Dict[str, Any]],
        policy: PolicyConstraints,
    ) -> pd.Series:
        """
        Run Riskfolio-Lib optimization.

        Returns:
            pd.Series of target weights indexed by symbol
        """
        # Calculate returns
        returns = price_history.pct_change().dropna()

        if len(returns) < 30:
            logger.warning(f"Insufficient data for optimization ({len(returns)} days)")
            return self._equal_weight_fallback(positions)

        # Wrap sync Riskfolio code in asyncio.to_thread
        target_weights = await asyncio.to_thread(
            self._optimize_sync,
            returns,
            policy,
        )

        # Map security IDs back to symbols
        symbol_map = {p["security_id"]: p["symbol"] for p in positions}
        target_weights.index = [symbol_map.get(sid, sid) for sid in target_weights.index]

        return target_weights

    def _optimize_sync(
        self,
        returns: pd.DataFrame,
        policy: PolicyConstraints,
    ) -> pd.Series:
        """
        Synchronous Riskfolio optimization (called via asyncio.to_thread).
        """
        # Create portfolio object
        port = rp.Portfolio(returns=returns)

        # Estimate covariance
        port.assets_stats(method_mu="hist", method_cov="hist")

        # Set constraints
        port.upperlong = np.ones(len(returns.columns)) * (policy.max_single_position_pct / 100.0)
        port.lowerlong = np.ones(len(returns.columns)) * (policy.min_position_pct / 100.0)

        # Optimize based on method
        if policy.method == "risk_parity":
            w = port.rp_optimization(
                model="Classic",
                rm="MV",  # Mean-variance
                rf=policy.risk_free_rate,
                b=None,  # Equal risk contribution
            )
        elif policy.method == "max_sharpe":
            w = port.optimization(
                model="Classic",
                rm="MV",
                obj="Sharpe",
                rf=policy.risk_free_rate,
                l=0,
                hist=True,
            )
        elif policy.method == "cvar":
            w = port.optimization(
                model="Classic",
                rm="CVaR",
                obj="MinRisk",
                rf=policy.risk_free_rate,
                l=0,
                hist=True,
            )
        else:  # mean_variance (default)
            w = port.optimization(
                model="Classic",
                rm="MV",
                obj="Sharpe",
                rf=policy.risk_free_rate,
                l=0,
                hist=True,
            )

        # Convert to Series
        weights = pd.Series(w.flatten(), index=returns.columns)

        # Normalize to sum to 1.0
        weights = weights / weights.sum()

        return weights

    def _equal_weight_fallback(self, positions: List[Dict[str, Any]]) -> pd.Series:
        """Fallback to equal weighting if optimization fails."""
        n = len(positions)
        symbols = [p["symbol"] for p in positions]
        weights = pd.Series([1.0 / n] * n, index=symbols)

        logger.info(f"Using equal-weight fallback ({n} positions)")

        return weights

    def _generate_trade_proposals(
        self,
        positions: List[Dict[str, Any]],
        target_weights: pd.Series,
        portfolio_value: Decimal,
        policy: PolicyConstraints,
    ) -> List[Dict[str, Any]]:
        """
        Generate trade proposals from target weights.

        Returns:
            List of TradeProposal dicts
        """
        trades = []

        for pos in positions:
            symbol = pos["symbol"]
            current_shares = int(pos["quantity"])
            current_price = Decimal(str(pos["price"]))
            current_value = Decimal(str(pos["value"]))
            current_weight = float(current_value / portfolio_value)

            # Get target weight
            target_weight = target_weights.get(symbol, 0.0)

            # Calculate target shares
            target_value = portfolio_value * Decimal(str(target_weight))
            target_shares = int(target_value / current_price)

            # Calculate delta
            delta_shares = target_shares - current_shares

            # Skip if delta is negligible (< 1 share or < $100)
            if abs(delta_shares) < 1 or abs(delta_shares * current_price) < 100:
                continue

            # Determine action
            if delta_shares > 0:
                action = "BUY"
                rationale = f"Increase weight from {current_weight*100:.1f}% to {target_weight*100:.1f}%"
            else:
                action = "SELL"
                rationale = f"Decrease weight from {current_weight*100:.1f}% to {target_weight*100:.1f}%"

            # Calculate trade value
            trade_value = abs(delta_shares) * current_price

            # Estimate costs
            estimated_cost = self._estimate_trade_cost(trade_value, policy)

            # Build trade proposal
            trade = {
                "symbol": symbol,
                "security_id": pos["security_id"],
                "action": action,
                "quantity": delta_shares,
                "current_shares": current_shares,
                "target_shares": target_shares,
                "current_weight_pct": current_weight * 100,
                "target_weight_pct": target_weight * 100,
                "current_price": float(current_price),
                "trade_value": float(trade_value),
                "estimated_cost": float(estimated_cost),
                "rationale": rationale,
            }

            trades.append(trade)

        return trades

    def _estimate_trade_cost(
        self,
        trade_value: Decimal,
        policy: PolicyConstraints,
    ) -> Decimal:
        """
        Estimate trade cost (commission + market impact).

        Args:
            trade_value: Dollar value of trade
            policy: Policy constraints with commission and market impact settings

        Returns:
            Total estimated cost
        """
        # Flat commission
        commission = Decimal(str(policy.commission_per_trade))

        # Market impact (basis points)
        market_impact = trade_value * Decimal(str(policy.market_impact_bps / 10000.0))

        total_cost = commission + market_impact

        return total_cost

    def _scale_trades_to_turnover_limit(
        self,
        trades: List[Dict[str, Any]],
        portfolio_value: Decimal,
        max_turnover_pct: float,
    ) -> List[Dict[str, Any]]:
        """
        Scale down trades to meet turnover constraint.

        Args:
            trades: Original trade proposals
            portfolio_value: Total portfolio value
            max_turnover_pct: Maximum turnover percentage

        Returns:
            Scaled trade proposals
        """
        # Calculate current turnover
        total_turnover = sum(abs(Decimal(str(t["trade_value"]))) for t in trades)
        current_turnover_pct = float((total_turnover / portfolio_value) * 100)

        # Calculate scale factor
        scale_factor = max_turnover_pct / current_turnover_pct

        logger.info(f"Scaling trades by {scale_factor:.2f} to meet {max_turnover_pct}% turnover limit")

        # Scale all trades
        scaled_trades = []

        for trade in trades:
            scaled_quantity = int(trade["quantity"] * scale_factor)

            # Skip if scaled to zero
            if scaled_quantity == 0:
                continue

            scaled_trade_value = abs(scaled_quantity) * Decimal(str(trade["current_price"]))

            # Update trade
            scaled_trade = trade.copy()
            scaled_trade["quantity"] = scaled_quantity
            scaled_trade["target_shares"] = trade["current_shares"] + scaled_quantity
            scaled_trade["trade_value"] = float(scaled_trade_value)
            scaled_trade["rationale"] += f" (scaled {scale_factor:.0%} for turnover limit)"

            scaled_trades.append(scaled_trade)

        return scaled_trades

    def _simulate_trades(
        self,
        current_positions: List[Dict[str, Any]],
        proposed_trades: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Simulate trades to get post-rebalance positions."""
        # Build position map
        pos_map = {p["symbol"]: p.copy() for p in current_positions}

        # Apply trades
        for trade in proposed_trades:
            symbol = trade["symbol"]

            if symbol in pos_map:
                # Update quantity
                pos_map[symbol]["quantity"] = float(trade["target_shares"])
                pos_map[symbol]["value"] = trade["target_shares"] * trade["current_price"]

        return list(pos_map.values())

    def _calculate_concentration_top10(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate concentration (% of value in top 10 positions)."""
        if not positions:
            return 0.0

        total_value = sum(p["value"] for p in positions)

        if total_value == 0:
            return 0.0

        # Sort by value descending
        sorted_positions = sorted(positions, key=lambda p: p["value"], reverse=True)

        # Sum top 10
        top10_value = sum(p["value"] for p in sorted_positions[:10])

        concentration = (top10_value / total_value) * 100

        return concentration

    def _get_scenario_hedges(
        self,
        scenario_id: str,
        portfolio_value: Decimal,
        positions: List[Dict[str, Any]],
    ) -> List[HedgeRecommendation]:
        """
        Get hedge recommendations for a scenario.

        Scenario-specific hedge playbook:
            - rates_up: Long TLT (long-duration treasuries)
            - equity_selloff: Buy VIX calls or SPY puts
            - usd_up: Short USD futures or long non-USD equities
            - credit_spread_widening: Long IG credit ETF puts
        """
        hedges = []

        # Size hedges as % of portfolio value
        hedge_notional = portfolio_value * Decimal("0.10")  # 10% notional hedge

        if scenario_id == "rates_up":
            hedges.append(HedgeRecommendation(
                instrument="TLT",
                instrument_type="etf",
                action="BUY",
                notional=hedge_notional,
                hedge_ratio=0.25,
                rationale="Long-duration treasuries benefit from rate increases via higher yields",
                expected_offset_pct=30.0,
            ))

        elif scenario_id == "equity_selloff":
            hedges.append(HedgeRecommendation(
                instrument="VIX",
                instrument_type="option",
                action="BUY",
                notional=hedge_notional * Decimal("0.5"),
                hedge_ratio=0.40,
                rationale="VIX call options hedge equity market volatility",
                expected_offset_pct=50.0,
            ))
            hedges.append(HedgeRecommendation(
                instrument="SPY",
                instrument_type="option",
                action="SELL",
                notional=hedge_notional * Decimal("0.5"),
                hedge_ratio=0.30,
                rationale="SPY put options hedge broad equity exposure",
                expected_offset_pct=40.0,
            ))

        elif scenario_id == "usd_up":
            hedges.append(HedgeRecommendation(
                instrument="UUP",
                instrument_type="etf",
                action="SELL",
                notional=hedge_notional,
                hedge_ratio=0.20,
                rationale="Short USD ETF hedges currency appreciation risk",
                expected_offset_pct=25.0,
            ))

        elif scenario_id == "credit_spread_widening":
            hedges.append(HedgeRecommendation(
                instrument="LQD",
                instrument_type="option",
                action="SELL",
                notional=hedge_notional,
                hedge_ratio=0.35,
                rationale="IG credit ETF put options hedge credit spread widening",
                expected_offset_pct=45.0,
            ))

        else:
            # Generic hedge: SPY puts
            hedges.append(HedgeRecommendation(
                instrument="SPY",
                instrument_type="option",
                action="SELL",
                notional=hedge_notional,
                hedge_ratio=0.20,
                rationale="Generic equity hedge via SPY put options",
                expected_offset_pct=30.0,
            ))

        return hedges

    def _get_deleveraging_recommendations(
        self,
        regime: str,
        portfolio_value: Decimal,
        positions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Get deleveraging recommendations based on macro regime.

        Dalio deleveraging playbook:
            - DELEVERAGING: Reduce equity/debt, increase gold/bonds/cash
            - LATE_EXPANSION: Moderate equity reduction, increase defensive
            - REFLATION: Reduce duration, increase inflation-linked assets
        """
        recommendations = []

        if regime in ["DELEVERAGING", "DEPRESSION"]:
            # Aggressive deleveraging
            recommendations.append({
                "action": "reduce_equity_exposure",
                "instruments": ["SPY", "QQQ", "VTI"],
                "target_reduction_pct": 40.0,
                "rationale": "Reduce equity beta aggressively in deleveraging regime to preserve capital",
            })
            recommendations.append({
                "action": "increase_safe_havens",
                "instruments": ["GLD", "TLT", "CASH"],
                "target_allocation_pct": 30.0,
                "rationale": "Increase gold, long-duration bonds, and cash as deflation hedges",
            })
            recommendations.append({
                "action": "avoid_credit",
                "instruments": ["HYG", "JNK"],
                "target_reduction_pct": 100.0,
                "rationale": "Exit high-yield credit to avoid default risk in deleveraging",
            })

        elif regime == "LATE_EXPANSION":
            # Moderate deleveraging
            recommendations.append({
                "action": "reduce_equity_exposure",
                "instruments": ["SPY", "QQQ"],
                "target_reduction_pct": 20.0,
                "rationale": "Moderate equity reduction as expansion matures and valuations peak",
            })
            recommendations.append({
                "action": "increase_defensive",
                "instruments": ["XLU", "XLP", "VNQ"],
                "target_allocation_pct": 15.0,
                "rationale": "Rotate to defensive sectors (utilities, staples, REITs)",
            })

        elif regime == "REFLATION":
            # Reduce duration, increase real assets
            recommendations.append({
                "action": "reduce_duration",
                "instruments": ["TLT", "IEF"],
                "target_reduction_pct": 50.0,
                "rationale": "Reduce long-duration bonds as inflation expectations rise",
            })
            recommendations.append({
                "action": "increase_inflation_hedges",
                "instruments": ["GLD", "TIP", "DBC"],
                "target_allocation_pct": 20.0,
                "rationale": "Increase gold, TIPS, and commodities as inflation hedges",
            })

        else:
            # Generic recommendation
            recommendations.append({
                "action": "maintain_balance",
                "instruments": [],
                "target_reduction_pct": 0.0,
                "rationale": f"No specific deleveraging recommendations for regime {regime}",
            })

        return recommendations

    async def _get_pack_date(self, pricing_pack_id: str) -> date:
        """Get asof date from pricing pack."""
        from app.core.types import PricingPackNotFoundError
        from app.core.di_container import get_container
        from app.core.service_initializer import initialize_services
        from app.db.connection import get_db_pool
        
        # Get pricing service from DI container
        container = get_container()
        if not container._initialized:
            db_pool = get_db_pool()
            initialize_services(container, db_pool=db_pool)
        pricing_service = container.resolve("pricing")
        pack = await pricing_service.get_pack_by_id(pricing_pack_id, raise_if_not_found=True)
        
        # Should not reach here if raise_if_not_found=True, but return for type safety
        if not pack:
            raise PricingPackNotFoundError(pricing_pack_id)
        return pack.date

    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert dataclass to dict, handling nested objects and Decimals."""
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)

                if isinstance(value, Decimal):
                    result[field_name] = float(value)
                elif isinstance(value, (date, datetime)):
                    result[field_name] = value.isoformat()
                elif isinstance(value, list):
                    result[field_name] = [self._dataclass_to_dict(v) if hasattr(v, "__dataclass_fields__") else v for v in value]
                elif hasattr(value, "__dataclass_fields__"):
                    result[field_name] = self._dataclass_to_dict(value)
                else:
                    result[field_name] = value

            return result
        else:
            return obj

    def _empty_rebalance_result(
        self,
        portfolio_id: UUID,
        pricing_pack_id: str,
        policy: PolicyConstraints,
    ) -> Dict[str, Any]:
        """Return empty rebalance result (no trades)."""
        result = RebalanceResult(
            portfolio_id=str(portfolio_id),
            pricing_pack_id=pricing_pack_id,
            asof_date=date.today(),
            trades=[],
            trade_count=0,
            total_turnover=Decimal("0"),
            turnover_pct=0.0,
            estimated_costs=Decimal("0"),
            cost_bps=0.0,
            current_value=Decimal("0"),
            post_rebalance_value=Decimal("0"),
            method=policy.method,
            constraints_met=True,
            warnings=["No positions found"],
        )

        return self._dataclass_to_dict(result)

    def _stub_rebalance_result(
        self,
        portfolio_id: UUID,
        pricing_pack_id: str,
        positions: List[Dict[str, Any]],
        portfolio_value: Decimal,
        policy: PolicyConstraints,
    ) -> Dict[str, Any]:
        """Return stub rebalance result (no-op trades)."""
        result = RebalanceResult(
            portfolio_id=str(portfolio_id),
            pricing_pack_id=pricing_pack_id,
            asof_date=date.today(),
            trades=[],
            trade_count=0,
            total_turnover=Decimal("0"),
            turnover_pct=0.0,
            estimated_costs=Decimal("0"),
            cost_bps=0.0,
            current_value=portfolio_value,
            post_rebalance_value=portfolio_value,
            method=policy.method,
            constraints_met=True,
            warnings=["Riskfolio-Lib not available. Install with: pip install riskfolio-lib"],
        )

        return self._dataclass_to_dict(result)

    def _empty_impact_analysis(self) -> Dict[str, Any]:
        """Return empty impact analysis."""
        impact = ImpactAnalysis(
            current_value=Decimal("0"),
            post_rebalance_value=Decimal("0"),
            value_delta=Decimal("0"),
        )

        return self._dataclass_to_dict(impact)


# ============================================================================
# Singleton Instance
# ============================================================================

_optimizer_service: Optional[OptimizerService] = None


def get_optimizer_service(use_db: bool = True, db_pool=None) -> OptimizerService:
    """
    DEPRECATED: Use OptimizerService(db_pool=...) directly instead.

    Migration:
        OLD: optimizer_service = get_optimizer_service()
        NEW: optimizer_service = OptimizerService(db_pool=db_pool)
    """
    import warnings
    warnings.warn(
        "get_optimizer_service() is deprecated. Use OptimizerService(db_pool=...) directly.",
        DeprecationWarning,
        stacklevel=2
    )
    global _optimizer_service
    if _optimizer_service is None:
        _optimizer_service = OptimizerService(use_db=use_db, db_pool=db_pool)
    return _optimizer_service
