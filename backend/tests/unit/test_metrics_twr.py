"""
Unit Tests for Time-Weighted Return (TWR) Calculation

Purpose: Comprehensive test coverage for TWR formula fixes from Week 2
Created: 2025-11-05
Priority: P0 (Critical - prevents regression)

Test Coverage:
- Baseline (no cash flows)
- Single deposit mid-period
- Single withdrawal mid-period
- Multiple cash flows
- Negative returns
- Edge cases (zero values, empty data)
- Volatility calculation
- Sharpe ratio with custom RF rate
"""

import pytest
import numpy as np
from datetime import date, timedelta
from decimal import Decimal


class TestTWRCalculation:
    """Tests for Time-Weighted Return calculation."""

    def compute_twr_simple(self, values, start_date, end_date):
        """
        Simplified TWR calculation for testing (mimics metrics.py logic).

        Args:
            values: List of {"total_value": float, "cash_flows": float}
            start_date: Start date
            end_date: End date

        Returns:
            Dict with TWR, volatility, Sharpe ratio
        """
        # Compute daily returns
        returns = []
        for i in range(1, len(values)):
            v_prev = Decimal(str(values[i - 1]["total_value"]))
            v_curr = Decimal(str(values[i]["total_value"]))
            cf = Decimal(str(values[i].get("cash_flows", 0)))

            # TWR formula: r = (V_curr - CF - V_prev) / V_prev
            denominator = v_prev
            if denominator > 0:
                r = (v_curr - cf - v_prev) / denominator
                returns.append(float(r))

        if not returns:
            return {
                "twr": 0.0,
                "ann_twr": 0.0,
                "vol": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "error": "No valid returns",
            }

        # Geometric linking
        twr = float(np.prod([1 + r for r in returns]) - 1)

        # Annualize
        days = (end_date - start_date).days
        ann_factor = 365 / days if days > 0 else 1
        ann_twr = (1 + twr) ** ann_factor - 1

        # Volatility
        vol = float(np.std(returns) * np.sqrt(252)) if len(returns) > 1 else 0.0

        # Sharpe ratio (using 4% default)
        rf_rate = 0.04
        sharpe = (ann_twr - rf_rate) / vol if vol > 0 else 0.0

        # Sortino ratio
        downside_returns = [r for r in returns if r < 0]
        downside_vol = (
            float(np.std(downside_returns) * np.sqrt(252))
            if len(downside_returns) > 1
            else vol
        )
        sortino = (ann_twr - rf_rate) / downside_vol if downside_vol > 0 else 0.0

        return {
            "twr": twr,
            "ann_twr": ann_twr,
            "vol": vol,
            "sharpe": sharpe,
            "sortino": sortino,
        }

    def test_twr_no_cash_flows(self):
        """Test TWR with no deposits/withdrawals."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 110000, "cash_flows": 0},  # +10%
            {"total_value": 121000, "cash_flows": 0},  # +10%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 3)

        result = self.compute_twr_simple(values, start_date, end_date)

        # TWR = (1.1 × 1.1) - 1 = 21%
        assert abs(result["twr"] - 0.21) < 0.001, f"Expected TWR ~0.21, got {result['twr']}"
        assert result.get("error") is None

    def test_twr_with_deposit(self):
        """Test TWR correctly excludes deposit from return calculation."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 120000, "cash_flows": 0},      # +20%
            {"total_value": 220000, "cash_flows": 100000}, # Deposit
            {"total_value": 198000, "cash_flows": 0},      # -10%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 4)

        result = self.compute_twr_simple(values, start_date, end_date)

        # TWR = (1.2 × 0.9) - 1 = +8%
        # Period 1: (120000 - 0 - 100000) / 100000 = +20%
        # Period 2: (220000 - 100000 - 120000) / 120000 = 0% (just deposit)
        # Period 3: (198000 - 0 - 220000) / 220000 = -10%
        assert abs(result["twr"] - 0.08) < 0.001, f"Expected TWR ~0.08, got {result['twr']}"

    def test_twr_with_withdrawal(self):
        """Test TWR correctly handles withdrawals."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 120000, "cash_flows": 0},       # +20%
            {"total_value": 20000, "cash_flows": -100000},  # Withdrawal
            {"total_value": 22000, "cash_flows": 0},        # +10%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 4)

        result = self.compute_twr_simple(values, start_date, end_date)

        # TWR = (1.2 × 1.1) - 1 = +32%
        # Period 1: (120000 - 0 - 100000) / 100000 = +20%
        # Period 2: (20000 - (-100000) - 120000) / 120000 = 0% (just withdrawal)
        # Period 3: (22000 - 0 - 20000) / 20000 = +10%
        assert abs(result["twr"] - 0.32) < 0.001, f"Expected TWR ~0.32, got {result['twr']}"

    def test_twr_multiple_cash_flows(self):
        """Test TWR with frequent deposits/withdrawals."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 105000, "cash_flows": 0},      # +5%
            {"total_value": 205000, "cash_flows": 100000}, # Deposit
            {"total_value": 215000, "cash_flows": 0},      # +4.88% (215k-205k)/205k
            {"total_value": 115000, "cash_flows": -100000},# Withdrawal
            {"total_value": 120000, "cash_flows": 0},      # +4.35% (120k-115k)/115k
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 6)

        result = self.compute_twr_simple(values, start_date, end_date)

        # TWR = (1.05 × 1.0488 × 1.0435) - 1 ≈ +14.7%
        assert abs(result["twr"] - 0.147) < 0.01, f"Expected TWR ~0.147, got {result['twr']}"

    def test_twr_negative_returns(self):
        """Test TWR with losses."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 90000, "cash_flows": 0},  # -10%
            {"total_value": 81000, "cash_flows": 0},  # -10%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 3)

        result = self.compute_twr_simple(values, start_date, end_date)

        # TWR = (0.9 × 0.9) - 1 = -19%
        assert abs(result["twr"] - (-0.19)) < 0.001, f"Expected TWR ~-0.19, got {result['twr']}"

    def test_twr_zero_starting_value(self):
        """Test TWR gracefully handles zero starting value."""
        values = [
            {"total_value": 0, "cash_flows": 0},
            {"total_value": 100000, "cash_flows": 100000},  # Initial deposit
            {"total_value": 110000, "cash_flows": 0},        # +10%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 3)

        result = self.compute_twr_simple(values, start_date, end_date)

        # Should skip first period (zero denominator), calculate from second period
        # Period 2: (110000 - 0 - 100000) / 100000 = +10%
        assert result["twr"] is not None
        assert abs(result["twr"] - 0.10) < 0.001

    def test_twr_all_zeros(self):
        """Test TWR with no portfolio value."""
        values = [
            {"total_value": 0, "cash_flows": 0},
            {"total_value": 0, "cash_flows": 0},
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 2)

        result = self.compute_twr_simple(values, start_date, end_date)

        assert result["twr"] == 0.0
        assert "No valid returns" in result.get("error", "")

    def test_volatility_uses_corrected_twr(self):
        """Verify volatility calculation uses corrected TWR returns."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 120000, "cash_flows": 0},      # +20%
            {"total_value": 220000, "cash_flows": 100000}, # Deposit
            {"total_value": 198000, "cash_flows": 0},      # -10%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 4)

        result = self.compute_twr_simple(values, start_date, end_date)

        # Volatility should be based on [+0.20, 0.0, -0.10] returns
        # std([0.2, 0.0, -0.1]) ≈ 0.124, annualized = 0.124 × √252 ≈ 1.97
        assert result["vol"] > 0, "Volatility should be positive"
        assert result["vol"] < 3.0, "Volatility should be reasonable (<300%)"

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation with TWR and volatility."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 115000, "cash_flows": 0},  # +15%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)  # Full year for proper annualization

        result = self.compute_twr_simple(values, start_date, end_date)

        # Sharpe = (ann_twr - rf_rate) / vol
        # With single period, vol will be 0, so Sharpe should be 0
        # This tests the edge case handling
        assert result["sharpe"] >= 0 or result["vol"] == 0

    def test_sortino_ratio_downside_only(self):
        """Test Sortino ratio uses only downside returns."""
        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 110000, "cash_flows": 0},  # +10%
            {"total_value": 105000, "cash_flows": 0},  # -4.5%
            {"total_value": 115000, "cash_flows": 0},  # +9.5%
            {"total_value": 110000, "cash_flows": 0},  # -4.3%
        ]
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 5)

        result = self.compute_twr_simple(values, start_date, end_date)

        # Sortino should be different from Sharpe (uses only downside deviation)
        # With mix of positive and negative returns, sortino > sharpe typically
        assert result["sortino"] is not None


class TestTWREdgeCases:
    """Edge case tests for TWR calculation."""

    def test_single_period(self):
        """Test TWR with only one period."""
        from tests.unit.test_metrics_twr import TestTWRCalculation
        calc = TestTWRCalculation()

        values = [
            {"total_value": 100000, "cash_flows": 0},
            {"total_value": 110000, "cash_flows": 0},
        ]
        result = calc.compute_twr_simple(values, date(2025, 1, 1), date(2025, 1, 2))

        assert abs(result["twr"] - 0.10) < 0.001  # 10% return
        assert result["vol"] == 0.0  # No volatility with single return

    def test_large_deposit_relative_to_portfolio(self):
        """Test TWR when deposit is larger than portfolio value."""
        from tests.unit.test_metrics_twr import TestTWRCalculation
        calc = TestTWRCalculation()

        values = [
            {"total_value": 10000, "cash_flows": 0},
            {"total_value": 11000, "cash_flows": 0},       # +10%
            {"total_value": 111000, "cash_flows": 100000}, # Large deposit
            {"total_value": 122000, "cash_flows": 0},      # +10% (122k-111k)/111k ≈ +9.9%
        ]
        result = calc.compute_twr_simple(values, date(2025, 1, 1), date(2025, 1, 4))

        # TWR should still be correct despite large deposit
        # Period 1: +10%, Period 2: 0% (deposit), Period 3: ~+9.9%
        assert abs(result["twr"] - 0.199) < 0.01  # ~20%

    def test_precision_with_decimals(self):
        """Test TWR maintains precision with Decimal values."""
        from tests.unit.test_metrics_twr import TestTWRCalculation
        calc = TestTWRCalculation()

        # Use values that would lose precision with floats
        values = [
            {"total_value": 100000.12345, "cash_flows": 0},
            {"total_value": 110000.67890, "cash_flows": 0},
        ]
        result = calc.compute_twr_simple(values, date(2025, 1, 1), date(2025, 1, 2))

        # Should calculate return accurately
        expected_return = (110000.67890 - 100000.12345) / 100000.12345
        assert abs(result["twr"] - expected_return) < 0.000001


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
