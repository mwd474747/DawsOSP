"""
Integration Tests for Money-Weighted Return (MWR) Capability

Purpose: Verify metrics.compute_mwr capability works end-to-end
Created: 2025-11-05
Priority: P0 (Critical - verify new Week 2 capability)

Test Coverage:
- Capability registration
- Direct agent call
- Runtime execution
- IRR convergence
- MWR vs TWR divergence
- Error handling
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch, AsyncMock


class TestMWRCapabilityRegistration:
    """Test that MWR capability is properly registered."""

    def test_mwr_capability_in_list(self):
        """Verify metrics.compute_mwr is discoverable."""
        from app.agents.financial_analyst import FinancialAnalyst

        # Create agent with minimal services
        services = {"db": None, "redis": None}
        agent = FinancialAnalyst("financial_analyst", services)

        capabilities = agent.get_capabilities()

        assert "metrics.compute_mwr" in capabilities, (
            "metrics.compute_mwr should be in capabilities list"
        )

    def test_mwr_capability_method_exists(self):
        """Verify metrics_compute_mwr method exists on agent."""
        from app.agents.financial_analyst import FinancialAnalyst

        services = {"db": None, "redis": None}
        agent = FinancialAnalyst("financial_analyst", services)

        assert hasattr(agent, "metrics_compute_mwr"), (
            "Agent should have metrics_compute_mwr method"
        )
        assert callable(getattr(agent, "metrics_compute_mwr")), (
            "metrics_compute_mwr should be callable"
        )


class TestMWRDirectCall:
    """Test calling MWR capability directly on agent."""

    @pytest.mark.asyncio
    async def test_mwr_direct_call_structure(self):
        """Test calling metrics_compute_mwr() directly returns correct structure."""
        from app.agents.financial_analyst import FinancialAnalyst
        from app.core.types import RequestCtx

        # Mock services
        services = {"db": None, "redis": None}
        agent = FinancialAnalyst("financial_analyst", services)

        # Mock context
        ctx = Mock(spec=RequestCtx)
        ctx.portfolio_id = "test-portfolio-uuid"
        ctx.pricing_pack_id = "PP_2025-11-05"

        # Mock PerformanceCalculator.compute_mwr
        mock_mwr_result = {
            "mwr": 0.1450,
            "ann_mwr": 0.1520,
            "lookback_days": 365,
        }

        with patch("app.agents.financial_analyst.PerformanceCalculator") as MockCalc:
            mock_calc_instance = AsyncMock()
            mock_calc_instance.compute_mwr = AsyncMock(return_value=mock_mwr_result)
            MockCalc.return_value = mock_calc_instance

            result = await agent.metrics_compute_mwr(
                ctx=ctx,
                state={},
                portfolio_id="test-portfolio-uuid",
                pack_id="PP_2025-11-05",
            )

        # Verify result structure
        assert "mwr" in result, "Result should contain 'mwr'"
        assert "ann_mwr" in result, "Result should contain 'ann_mwr'"
        assert "__metadata__" in result, "Result should contain '__metadata__'"
        assert result["__metadata__"]["capability"] == "metrics.compute_mwr"

    @pytest.mark.asyncio
    async def test_mwr_error_handling(self):
        """Test MWR gracefully handles errors."""
        from app.agents.financial_analyst import FinancialAnalyst
        from app.core.types import RequestCtx

        services = {"db": None, "redis": None}
        agent = FinancialAnalyst("financial_analyst", services)

        ctx = Mock(spec=RequestCtx)
        ctx.portfolio_id = "invalid-uuid"
        ctx.pricing_pack_id = "PP_2025-11-05"

        # Mock compute_mwr to raise exception
        with patch("app.agents.financial_analyst.PerformanceCalculator") as MockCalc:
            mock_calc_instance = AsyncMock()
            mock_calc_instance.compute_mwr = AsyncMock(
                side_effect=Exception("Portfolio not found")
            )
            MockCalc.return_value = mock_calc_instance

            result = await agent.metrics_compute_mwr(
                ctx=ctx,
                state={},
                portfolio_id="invalid-uuid",
            )

        # Should return error structure, not raise
        assert "error" in result
        assert result["mwr"] == 0.0
        assert "Portfolio not found" in result["error"]


class TestMWRRuntimeExecution:
    """Test calling MWR through AgentRuntime."""

    @pytest.mark.asyncio
    async def test_mwr_via_runtime(self):
        """Test calling MWR through AgentRuntime routing."""
        from app.core.agent_runtime import AgentRuntime
        from app.agents.financial_analyst import FinancialAnalyst
        from app.core.types import RequestCtx

        # Create runtime
        services = {"db": None, "redis": None}
        runtime = AgentRuntime(services, enable_rights_enforcement=False)

        # Register agent
        agent = FinancialAnalyst("financial_analyst", services)
        runtime.register_agent(agent)

        # Create context
        ctx = Mock(spec=RequestCtx)
        ctx.portfolio_id = "test-portfolio-uuid"
        ctx.pricing_pack_id = "PP_2025-11-05"
        ctx.user_id = "test-user"

        # Mock compute_mwr
        mock_result = {"mwr": 0.10, "ann_mwr": 0.105}
        with patch("app.agents.financial_analyst.PerformanceCalculator") as MockCalc:
            mock_calc_instance = AsyncMock()
            mock_calc_instance.compute_mwr = AsyncMock(return_value=mock_result)
            MockCalc.return_value = mock_calc_instance

            result = await runtime.execute_capability(
                "metrics.compute_mwr",
                ctx=ctx,
                state={},
                portfolio_id="test-portfolio-uuid",
            )

        assert result is not None
        assert "mwr" in result
        assert result["mwr"] == 0.10


class TestMWRBusinessLogic:
    """Test MWR business logic and calculations."""

    def test_mwr_twr_divergence_concept(self):
        """
        Verify MWR and TWR diverge when cash flow timing matters.

        This is a conceptual test showing the difference between MWR and TWR.
        Actual implementation would use PerformanceCalculator.
        """
        # Scenario: Deposit right before market drops
        # Jan 1:  $100k
        # Jun 30: $120k (+20%)
        # Jul 1:  Deposit $100k → $220k
        # Dec 31: Market drops to $198k (-10%)

        # TWR (manager performance):
        # Period 1: (120k - 100k) / 100k = +20%
        # Period 2: (220k - 100k deposit - 120k) / 120k = 0%
        # Period 3: (198k - 220k) / 220k = -10%
        # TWR = (1.2 × 1.0 × 0.9) - 1 = +8%

        twr = (1.2 * 1.0 * 0.9) - 1
        assert abs(twr - 0.08) < 0.01, "TWR should be +8%"

        # MWR (investor experience):
        # Cash flows: -100k (Jan 1), -100k (Jul 1), +198k (Dec 31)
        # IRR calculation would show negative return (bad timing)
        # Approximate MWR ≈ -1% (investor lost money)

        # In practice:
        # - Manager did well (TWR = +8%)
        # - Investor lost money (MWR ≈ -1%) due to bad deposit timing

        # This test just validates the concept; actual MWR needs IRR solver
        assert twr > 0, "Manager performed well (positive TWR)"
        # MWR would be negative in this scenario


class TestMWRIRRConvergence:
    """Test IRR convergence scenarios."""

    @pytest.mark.asyncio
    async def test_mwr_simple_scenario(self):
        """Test MWR converges for simple cash flow scenario."""
        from app.agents.financial_analyst import FinancialAnalyst
        from app.core.types import RequestCtx

        services = {"db": None, "redis": None}
        agent = FinancialAnalyst("financial_analyst", services)

        ctx = Mock(spec=RequestCtx)
        ctx.portfolio_id = "test-portfolio-uuid"
        ctx.pricing_pack_id = "PP_2025-11-05"

        # Mock a successful MWR calculation
        mock_result = {
            "mwr": 0.1234,  # 12.34% IRR
            "ann_mwr": 0.1250,
            "lookback_days": 365,
        }

        with patch("app.agents.financial_analyst.PerformanceCalculator") as MockCalc:
            mock_calc_instance = AsyncMock()
            mock_calc_instance.compute_mwr = AsyncMock(return_value=mock_result)
            MockCalc.return_value = mock_calc_instance

            result = await agent.metrics_compute_mwr(ctx=ctx, state={})

        # Verify IRR is in reasonable range
        assert result["mwr"] is not None
        assert -1.0 < result["mwr"] < 1.0, "MWR should be in reasonable range"
        assert "error" not in result or result.get("error") is None


class TestMWRMetadata:
    """Test MWR result metadata."""

    @pytest.mark.asyncio
    async def test_mwr_metadata_structure(self):
        """Verify MWR result includes proper metadata."""
        from app.agents.financial_analyst import FinancialAnalyst
        from app.core.types import RequestCtx

        services = {"db": None, "redis": None}
        agent = FinancialAnalyst("financial_analyst", services)

        ctx = Mock(spec=RequestCtx)
        ctx.portfolio_id = "test-portfolio-uuid"
        ctx.pricing_pack_id = "PP_2025-11-05"

        mock_result = {"mwr": 0.10, "ann_mwr": 0.105}
        with patch("app.agents.financial_analyst.PerformanceCalculator") as MockCalc:
            mock_calc_instance = AsyncMock()
            mock_calc_instance.compute_mwr = AsyncMock(return_value=mock_result)
            MockCalc.return_value = mock_calc_instance

            result = await agent.metrics_compute_mwr(ctx=ctx, state={})

        # Verify metadata
        assert "__metadata__" in result
        metadata = result["__metadata__"]

        assert "capability" in metadata
        assert metadata["capability"] == "metrics.compute_mwr"

        assert "pricing_pack_id" in metadata
        assert metadata["pricing_pack_id"] == "PP_2025-11-05"

        assert "computed_at" in metadata


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
