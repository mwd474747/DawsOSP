"""
DawsOS Factor Analysis Calculator

Purpose: Compute factor exposures and attribution via regression
Updated: 2025-10-21
Priority: P1 (Important for risk decomposition)

Factors:
    - Real Rate (10Y TIPS yield)
    - Inflation (breakeven inflation)
    - Credit Spread (IG corporate - treasury)
    - USD (DXY dollar index)
    - Equity Risk Premium (S&P 500 - risk-free rate)

Model:
    r_portfolio = α + β₁·RealRate + β₂·Inflation + β₃·Credit + β₄·USD + β₅·ERP + ε

Acceptance:
    - Factor loadings sum to ~1.0 for diversified portfolio
    - R² explains >70% of variance for equity-heavy portfolios
    - All calculations reference pricing_pack_id for reproducibility

Usage:
    analyzer = FactorAnalyzer(db)
    factors = await analyzer.compute_factor_exposure(portfolio_id, pack_id, lookback_days=252)
"""

import logging
import numpy as np
import pandas as pd
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class FactorAnalyzer:
    """
    Factor analysis calculator.

    Uses regression to decompose portfolio returns into factor exposures.
    """

    def __init__(self, db):
        """
        Initialize analyzer.

        Args:
            db: Async database connection pool
        """
        self.db = db

    async def compute_factor_exposure(
        self, portfolio_id: str, pack_id: str, lookback_days: int = 252
    ) -> Dict:
        """
        Compute factor exposures via regression.

        Model:
            r_portfolio = α + β₁·RealRate + β₂·Inflation + β₃·Credit + β₄·USD + β₅·ERP + ε

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack UUID
            lookback_days: Historical period (default 252 = 1 year)

        Returns:
            {
                "alpha": 0.002,  # Excess return not explained by factors
                "beta": {
                    "real_rate": -0.15,  # Negative = gains when rates fall
                    "inflation": 0.05,
                    "credit": 0.20,
                    "usd": -0.10,
                    "equity_risk_premium": 0.90
                },
                "r_squared": 0.85,  # 85% of variance explained
                "residual_vol": 0.05,  # Unexplained volatility
                "factor_attribution": {
                    "real_rate": -0.01,  # Contribution to total return
                    "inflation": 0.005,
                    "credit": 0.02,
                    "usd": -0.008,
                    "equity_risk_premium": 0.12
                },
                "total_explained": 0.127,
                "total_return": 0.15
            }

        Raises:
            ValueError: If insufficient data for regression
        """
        # Get date range
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        # Get portfolio returns
        portfolio_returns = await self._get_portfolio_returns(
            portfolio_id, start_date, end_date
        )

        # Get factor returns
        factor_returns = await self._get_factor_returns(start_date, end_date)

        if len(portfolio_returns) < 30:
            logger.warning(
                f"Insufficient data for factor analysis: {len(portfolio_returns)} days"
            )
            return {
                "error": "Insufficient data (minimum 30 days required)",
                "data_points": len(portfolio_returns),
            }

        # Align dates
        df = pd.DataFrame(portfolio_returns)
        df = df.set_index("asof_date")

        factor_df = pd.DataFrame(factor_returns)
        factor_df = factor_df.set_index("asof_date")

        # Merge on date
        merged = df.join(factor_df, how="inner")

        if len(merged) < 30:
            logger.warning(
                f"Insufficient aligned data: {len(merged)} days after merge"
            )
            return {
                "error": "Insufficient aligned data",
                "portfolio_days": len(df),
                "factor_days": len(factor_df),
                "aligned_days": len(merged),
            }

        # Prepare regression
        y = merged["portfolio_return"].values
        X = merged[
            ["real_rate", "inflation", "credit", "usd", "equity_risk_premium"]
        ].values

        # Run regression
        model = LinearRegression()
        model.fit(X, y)

        # Extract results
        alpha = float(model.intercept_)
        betas = {
            "real_rate": float(model.coef_[0]),
            "inflation": float(model.coef_[1]),
            "credit": float(model.coef_[2]),
            "usd": float(model.coef_[3]),
            "equity_risk_premium": float(model.coef_[4]),
        }

        # R²
        r_squared = float(model.score(X, y))

        # Residual volatility
        y_pred = model.predict(X)
        residuals = y - y_pred
        residual_vol = float(np.std(residuals) * np.sqrt(252))

        # Factor attribution (beta × factor_return)
        factor_means = {
            "real_rate": float(merged["real_rate"].mean()),
            "inflation": float(merged["inflation"].mean()),
            "credit": float(merged["credit"].mean()),
            "usd": float(merged["usd"].mean()),
            "equity_risk_premium": float(merged["equity_risk_premium"].mean()),
        }

        attribution = {
            factor: betas[factor] * factor_means[factor]
            for factor in betas.keys()
        }

        total_explained = sum(attribution.values())
        total_return = float(merged["portfolio_return"].mean() * len(merged))

        logger.info(
            f"Factor exposure for {portfolio_id}: "
            f"R²={r_squared:.2f}, "
            f"real_rate_beta={betas['real_rate']:.2f}, "
            f"erp_beta={betas['equity_risk_premium']:.2f}"
        )

        return {
            "alpha": round(alpha, 6),
            "beta": {k: round(v, 4) for k, v in betas.items()},
            "r_squared": round(r_squared, 4),
            "residual_vol": round(residual_vol, 4),
            "factor_attribution": {k: round(v, 6) for k, v in attribution.items()},
            "total_explained": round(total_explained, 6),
            "total_return": round(total_return, 6),
            "data_points": len(merged),
        }

    async def compute_factor_var(
        self, portfolio_id: str, pack_id: str, confidence: float = 0.95
    ) -> Dict:
        """
        Compute Value-at-Risk (VaR) using factor model.

        Uses factor covariance matrix to compute parametric VaR.

        Args:
            portfolio_id: Portfolio UUID
            pack_id: Pricing pack UUID
            confidence: Confidence level (default 0.95 = 95%)

        Returns:
            {
                "var_1d": -0.02,  # 1-day VaR (5th percentile loss)
                "var_10d": -0.065,  # 10-day VaR (scaled by sqrt(10))
                "confidence": 0.95,
                "method": "parametric_factor"
            }
        """
        # Get factor exposures
        exposures = await self.compute_factor_exposure(portfolio_id, pack_id)

        if "error" in exposures:
            return exposures

        # Get factor covariance matrix (from historical data)
        factor_cov = await self._get_factor_covariance(pack_id)

        # Portfolio variance = β' Σ β
        betas = np.array(
            [
                exposures["beta"]["real_rate"],
                exposures["beta"]["inflation"],
                exposures["beta"]["credit"],
                exposures["beta"]["usd"],
                exposures["beta"]["equity_risk_premium"],
            ]
        )

        portfolio_var = np.dot(betas, np.dot(factor_cov, betas))
        portfolio_vol = np.sqrt(portfolio_var)

        # VaR at confidence level (assume normal distribution)
        from scipy import stats

        z_score = stats.norm.ppf(1 - confidence)
        var_1d = z_score * portfolio_vol

        # Scale to 10-day (VaR scales with sqrt(time))
        var_10d = var_1d * np.sqrt(10)

        logger.info(
            f"Factor VaR for {portfolio_id}: "
            f"1d={var_1d:.4f}, 10d={var_10d:.4f} ({confidence:.0%} confidence)"
        )

        return {
            "var_1d": round(float(var_1d), 6),
            "var_10d": round(float(var_10d), 6),
            "confidence": confidence,
            "method": "parametric_factor",
        }

    async def _get_portfolio_returns(
        self, portfolio_id: str, start_date: date, end_date: date
    ) -> List[Dict]:
        """
        Get daily portfolio returns.

        Args:
            portfolio_id: Portfolio UUID
            start_date: Start date
            end_date: End date

        Returns:
            List of {asof_date, portfolio_return}
        """
        values = await self.db.fetch(
            """
            SELECT asof_date, total_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3
            ORDER BY asof_date
        """,
            portfolio_id,
            start_date,
            end_date,
        )

        if len(values) < 2:
            return []

        returns = []
        for i in range(1, len(values)):
            v_prev = float(values[i - 1]["total_value"])
            v_curr = float(values[i]["total_value"])

            if v_prev > 0:
                ret = (v_curr - v_prev) / v_prev
                returns.append(
                    {
                        "asof_date": values[i]["asof_date"],
                        "portfolio_return": ret,
                    }
                )

        return returns

    async def _get_factor_returns(
        self, start_date: date, end_date: date
    ) -> List[Dict]:
        """
        Get daily factor returns.

        Factors stored in economic_indicators table with FRED series IDs.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of {asof_date, real_rate, inflation, credit, usd, equity_risk_premium}
        """
        # Query factor time series
        # Note: This assumes economic_indicators table has daily factor data
        # In reality, may need to interpolate or use monthly data

        # Placeholder: Generate synthetic factor returns for demonstration
        # In production, would query from economic_indicators table

        factor_data = await self.db.fetch(
            """
            SELECT
                asof_date,
                MAX(CASE WHEN series_id = 'DFII10' THEN value END) as real_rate_level,
                MAX(CASE WHEN series_id = 'T10YIE' THEN value END) as inflation_level,
                MAX(CASE WHEN series_id = 'BAMLC0A0CM' THEN value END) as credit_level,
                MAX(CASE WHEN series_id = 'DTWEXBGS' THEN value END) as usd_level,
                MAX(CASE WHEN series_id = 'SP500' THEN value END) as sp500_level
            FROM economic_indicators
            WHERE asof_date BETWEEN $1 AND $2
                AND series_id IN ('DFII10', 'T10YIE', 'BAMLC0A0CM', 'DTWEXBGS', 'SP500')
            GROUP BY asof_date
            ORDER BY asof_date
        """,
            start_date,
            end_date,
        )

        # Convert levels to returns
        returns = []
        for i in range(1, len(factor_data)):
            prev = factor_data[i - 1]
            curr = factor_data[i]

            # Compute factor returns (change in levels)
            real_rate_ret = self._safe_return(
                prev["real_rate_level"], curr["real_rate_level"]
            )
            inflation_ret = self._safe_return(
                prev["inflation_level"], curr["inflation_level"]
            )
            credit_ret = self._safe_return(
                prev["credit_level"], curr["credit_level"]
            )
            usd_ret = self._safe_return(prev["usd_level"], curr["usd_level"])

            # Equity risk premium = S&P 500 return - risk-free rate (approx 4% annualized)
            sp500_ret = self._safe_return(
                prev["sp500_level"], curr["sp500_level"]
            )
            erp_ret = sp500_ret - (0.04 / 252)  # Daily risk-free rate

            returns.append(
                {
                    "asof_date": curr["asof_date"],
                    "real_rate": real_rate_ret,
                    "inflation": inflation_ret,
                    "credit": credit_ret,
                    "usd": usd_ret,
                    "equity_risk_premium": erp_ret,
                }
            )

        return returns

    def _safe_return(
        self, prev_value: Optional[float], curr_value: Optional[float]
    ) -> float:
        """Safely compute return, handling None values."""
        if prev_value is None or curr_value is None or prev_value == 0:
            return 0.0
        return (curr_value - prev_value) / prev_value

    async def _get_factor_covariance(self, pack_id: str) -> np.ndarray:
        """
        Get factor covariance matrix.

        Args:
            pack_id: Pricing pack UUID

        Returns:
            5x5 covariance matrix for factors
        """
        # Get date
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=252)

        # Get factor returns
        factor_returns = await self._get_factor_returns(start_date, end_date)

        if len(factor_returns) < 30:
            # Return identity matrix if insufficient data
            logger.warning("Insufficient data for factor covariance, using identity")
            return np.eye(5) * 0.01  # 1% daily volatility

        # Build dataframe
        df = pd.DataFrame(factor_returns)
        df = df.set_index("asof_date")

        # Compute covariance matrix
        cov_matrix = df.cov().values

        return cov_matrix

    async def _get_pack_date(self, pack_id: str) -> date:
        """Get as-of date for pricing pack."""
        row = await self.db.fetchrow(
            "SELECT asof_date FROM pricing_packs WHERE id = $1", pack_id
        )
        if not row:
            raise ValueError(f"Pricing pack not found: {pack_id}")
        return row["asof_date"]
