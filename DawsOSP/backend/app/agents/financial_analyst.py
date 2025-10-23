"""
DawsOS Financial Analyst Agent

Purpose: Portfolio analysis, pricing, metrics computation
Updated: 2025-10-22 (Phase 4 Task 2: Database integration)
Priority: P0 (Critical for Phase 4)

Capabilities:
    - ledger.positions: Get portfolio positions from Beancount ledger
    - pricing.apply_pack: Apply pricing pack to positions
    - metrics.compute_twr: Compute Time-Weighted Return (database-backed)
    - metrics.compute_sharpe: Compute Sharpe Ratio (database-backed)
    - attribution.currency: Compute currency attribution (database-backed)
    - charts.overview: Generate overview charts

Architecture:
    Agent → Database Layer (Phase 3) → TimescaleDB

Usage:
    agent = FinancialAnalyst("financial_analyst", services)
    runtime.register_agent(agent)
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx
from app.db import get_metrics_queries, get_pricing_pack_queries
from jobs.currency_attribution import CurrencyAttribution

logger = logging.getLogger("DawsOS.FinancialAnalyst")


class FinancialAnalyst(BaseAgent):
    """
    Financial Analyst Agent.

    Provides capabilities for portfolio analysis, pricing, and metrics.
    Integrates with:
        - Beancount ledger (via ledger service)
        - Pricing packs (via pricing service)
        - Metrics service (TWR, MWR, Sharpe, etc.)
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "ledger.positions",
            "pricing.apply_pack",
            "metrics.compute_twr",
            "metrics.compute_sharpe",
            "attribution.currency",
            "charts.overview",
        ]

    async def ledger_positions(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get portfolio positions from Beancount ledger.

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Portfolio ID (optional, uses ctx.portfolio_id if not provided)

        Returns:
            Dict with positions list
        """
        portfolio_id = portfolio_id or (str(ctx.portfolio_id) if ctx.portfolio_id else None)

        if not portfolio_id:
            raise ValueError("portfolio_id required for ledger.positions")

        logger.info(f"ledger.positions: portfolio_id={portfolio_id}, asof_date={ctx.asof_date}")

        # TODO: Call ledger service to get real positions
        # For now, return stub data
        positions = [
            {
                "symbol": "AAPL",
                "qty": Decimal("100"),
                "cost_basis": Decimal("15000.00"),
                "currency": "USD",
            },
            {
                "symbol": "MSFT",
                "qty": Decimal("50"),
                "cost_basis": Decimal("12500.00"),
                "currency": "USD",
            },
        ]

        result = {
            "portfolio_id": portfolio_id,
            "asof_date": str(ctx.asof_date) if ctx.asof_date else None,
            "positions": positions,
            "total_positions": len(positions),
        }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"ledger:{ctx.ledger_commit_hash[:8]}",
            asof=ctx.asof_date,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def pricing_apply_pack(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        positions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Apply pricing pack to positions.

        Args:
            ctx: Request context
            state: Execution state
            positions: List of positions to price

        Returns:
            Dict with valued positions
        """
        logger.info(
            f"pricing.apply_pack: pack_id={ctx.pricing_pack_id}, "
            f"positions_count={len(positions)}"
        )

        # TODO: Load pricing pack and apply to positions
        # For now, return stub data with dummy prices
        valued_positions = []
        for pos in positions:
            # Dummy pricing
            dummy_price = Decimal("150.00") if pos["symbol"] == "AAPL" else Decimal("350.00")
            value = pos["qty"] * dummy_price

            valued_positions.append({
                **pos,
                "price": dummy_price,
                "value": value,
                "fx_rate": Decimal("1.0"),  # Assume USD for now
            })

        total_value = sum(p["value"] for p in valued_positions)

        result = {
            "positions": valued_positions,
            "total_value": total_value,
            "currency": "USD",
            "pricing_pack_id": ctx.pricing_pack_id,
        }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"pricing_pack:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def metrics_compute_twr(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute Time-Weighted Return from metrics database.

        Args:
            ctx: Request context (contains portfolio_id, asof_date)
            state: Execution state
            portfolio_id: Override portfolio ID (optional)
            asof_date: Override as-of date (optional)

        Returns:
            Dict with TWR metrics and provenance

        Example:
            {
                "twr_1d": 0.0125,
                "twr_mtd": 0.0234,
                "twr_ytd": 0.0850,
                "twr_1y": 0.1240,
                "twr_3y": 0.2450,
                "twr_5y": 0.4120,
                "twr_itd": 0.5230,
                "pricing_pack_id": "20251022_v1",
                "asof_date": "2025-10-22",
                "__metadata__": {...}
            }
        """
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id
        asof = asof_date or ctx.asof_date

        if not portfolio_id_uuid:
            raise ValueError("portfolio_id required for metrics.compute_twr")

        logger.info(
            f"metrics.compute_twr: portfolio_id={portfolio_id_uuid}, asof_date={asof}"
        )

        # Fetch from database
        queries = get_metrics_queries()

        try:
            if asof:
                metrics = await queries.get_latest_metrics(portfolio_id_uuid, asof)
            else:
                metrics = await queries.get_latest_metrics_any_date(portfolio_id_uuid)

            if not metrics:
                logger.warning(
                    f"No metrics found in database for portfolio {portfolio_id_uuid}, "
                    f"asof={asof}. Returning empty result."
                )
                result = {
                    "portfolio_id": str(portfolio_id_uuid),
                    "asof_date": str(asof) if asof else None,
                    "error": "Metrics not found in database",
                    "twr_1d": None,
                    "twr_mtd": None,
                    "twr_ytd": None,
                }
            else:
                result = {
                    "portfolio_id": str(metrics["portfolio_id"]),
                    "asof_date": str(metrics["asof_date"]),
                    "pricing_pack_id": metrics["pricing_pack_id"],
                    # TWR metrics
                    "twr_1d": float(metrics["twr_1d"]) if metrics.get("twr_1d") else None,
                    "twr_mtd": float(metrics["twr_mtd"]) if metrics.get("twr_mtd") else None,
                    "twr_ytd": float(metrics["twr_ytd"]) if metrics.get("twr_ytd") else None,
                    "twr_1y": float(metrics["twr_1y"]) if metrics.get("twr_1y") else None,
                    "twr_3y": float(metrics["twr_3y"]) if metrics.get("twr_3y") else None,
                    "twr_5y": float(metrics["twr_5y"]) if metrics.get("twr_5y") else None,
                    "twr_itd": float(metrics["twr_itd"]) if metrics.get("twr_itd") else None,
                }

        except Exception as e:
            logger.error(f"Error fetching metrics from database: {e}", exc_info=True)
            result = {
                "portfolio_id": str(portfolio_id_uuid),
                "asof_date": str(asof) if asof else None,
                "error": f"Database error: {str(e)}",
                "twr_1d": None,
                "twr_mtd": None,
                "twr_ytd": None,
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"metrics_database:{ctx.pricing_pack_id}",
            asof=asof,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def metrics_compute_sharpe(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Compute Sharpe Ratio from metrics database.

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Override portfolio ID (optional)
            asof_date: Override as-of date (optional)

        Returns:
            Dict with Sharpe ratios for different periods

        Example:
            {
                "sharpe_30d": 1.45,
                "sharpe_90d": 1.32,
                "sharpe_1y": 1.28,
                "sharpe_3y": 1.42,
                "sharpe_5y": 1.38,
                "sharpe_itd": 1.41,
                "pricing_pack_id": "20251022_v1",
                "asof_date": "2025-10-22",
                "__metadata__": {...}
            }
        """
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id
        asof = asof_date or ctx.asof_date

        if not portfolio_id_uuid:
            raise ValueError("portfolio_id required for metrics.compute_sharpe")

        logger.info(
            f"metrics.compute_sharpe: portfolio_id={portfolio_id_uuid}, asof_date={asof}"
        )

        # Fetch from database
        queries = get_metrics_queries()

        try:
            if asof:
                metrics = await queries.get_latest_metrics(portfolio_id_uuid, asof)
            else:
                metrics = await queries.get_latest_metrics_any_date(portfolio_id_uuid)

            if not metrics:
                logger.warning(
                    f"No metrics found in database for portfolio {portfolio_id_uuid}"
                )
                result = {
                    "portfolio_id": str(portfolio_id_uuid),
                    "asof_date": str(asof) if asof else None,
                    "error": "Metrics not found in database",
                    "sharpe_30d": None,
                    "sharpe_1y": None,
                }
            else:
                result = {
                    "portfolio_id": str(metrics["portfolio_id"]),
                    "asof_date": str(metrics["asof_date"]),
                    "pricing_pack_id": metrics["pricing_pack_id"],
                    # Sharpe ratios
                    "sharpe_30d": float(metrics["sharpe_30d"]) if metrics.get("sharpe_30d") else None,
                    "sharpe_90d": float(metrics["sharpe_90d"]) if metrics.get("sharpe_90d") else None,
                    "sharpe_1y": float(metrics["sharpe_1y"]) if metrics.get("sharpe_1y") else None,
                    "sharpe_3y": float(metrics["sharpe_3y"]) if metrics.get("sharpe_3y") else None,
                    "sharpe_5y": float(metrics["sharpe_5y"]) if metrics.get("sharpe_5y") else None,
                    "sharpe_itd": float(metrics["sharpe_itd"]) if metrics.get("sharpe_itd") else None,
                }

        except Exception as e:
            logger.error(f"Error fetching metrics from database: {e}", exc_info=True)
            result = {
                "portfolio_id": str(portfolio_id_uuid),
                "asof_date": str(asof) if asof else None,
                "error": f"Database error: {str(e)}",
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"metrics_database:{ctx.pricing_pack_id}",
            asof=asof,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def attribution_currency(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        asof_date: Optional[date] = None,
        base_currency: str = "CAD",
    ) -> Dict[str, Any]:
        """
        Compute currency attribution (local/FX/interaction).

        Args:
            ctx: Request context
            state: Execution state
            portfolio_id: Override portfolio ID (optional)
            asof_date: Override as-of date (optional)
            base_currency: Base currency for attribution (default: CAD)

        Returns:
            Dict with attribution breakdown

        Example:
            {
                "local_return": 0.0850,
                "fx_return": -0.0120,
                "interaction_return": -0.0010,
                "total_return": 0.0720,
                "error_bps": 0.05,
                "base_currency": "CAD",
                "pricing_pack_id": "20251022_v1",
                "asof_date": "2025-10-22",
                "__metadata__": {...}
            }
        """
        portfolio_id_str = portfolio_id or (str(ctx.portfolio_id) if ctx.portfolio_id else None)
        asof = asof_date or ctx.asof_date

        if not portfolio_id_str:
            raise ValueError("portfolio_id required for attribution.currency")

        logger.info(
            f"attribution.currency: portfolio_id={portfolio_id_str}, "
            f"asof_date={asof}, base_currency={base_currency}"
        )

        # Compute currency attribution
        attr_service = CurrencyAttribution(base_currency=base_currency)

        try:
            attribution = attr_service.compute_portfolio_attribution(
                portfolio_id=portfolio_id_str,
                asof_date=asof,
            )

            result = {
                "portfolio_id": portfolio_id_str,
                "asof_date": str(asof) if asof else None,
                "pricing_pack_id": ctx.pricing_pack_id,
                "base_currency": base_currency,
                # Attribution components
                "local_return": float(attribution.local_return),
                "fx_return": float(attribution.fx_return),
                "interaction_return": float(attribution.interaction_return),
                "total_return": float(attribution.total_return),
                # Validation
                "error_bps": float(attribution.error_bps) if attribution.error_bps else None,
            }

        except Exception as e:
            logger.error(f"Error computing currency attribution: {e}", exc_info=True)
            result = {
                "portfolio_id": portfolio_id_str,
                "asof_date": str(asof) if asof else None,
                "error": f"Attribution error: {str(e)}",
                "local_return": None,
                "fx_return": None,
                "total_return": None,
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"currency_attribution:{ctx.pricing_pack_id}",
            asof=asof,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def charts_overview(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        positions: List[Dict[str, Any]],
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate overview charts.

        Args:
            ctx: Request context
            state: Execution state
            positions: Valued positions
            metrics: Performance metrics

        Returns:
            Dict with chart configurations
        """
        logger.info(f"charts.overview: positions_count={len(positions)}")

        # TODO: Generate real chart configs
        # For now, return stub data
        charts = [
            {
                "type": "pie",
                "title": "Portfolio Allocation",
                "data": [
                    {"label": pos["symbol"], "value": float(pos.get("value", 0))}
                    for pos in positions
                ],
            },
            {
                "type": "line",
                "title": "Performance (TWR)",
                "data": [
                    {"x": p["date"], "y": float(p["return_pct"]) * 100}
                    for p in metrics.get("periods", [])
                ],
            },
        ]

        result = {
            "charts": charts,
            "chart_count": len(charts),
        }

        # Attach metadata
        metadata = self._create_metadata(
            source="chart_generator",
            asof=ctx.asof_date,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result
