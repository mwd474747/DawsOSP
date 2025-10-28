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

from backend.app.agents.base_agent import BaseAgent, AgentMetadata
from backend.app.core.types import RequestCtx
from backend.app.db import (
    get_metrics_queries,
    get_pricing_pack_queries,
    get_db_connection_with_rls,
)
from backend.app.services.pricing import get_pricing_service
from backend.app.services.currency_attribution import CurrencyAttributor

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
            "metrics.compute",  # Generic metrics computation (wrapper)
            "metrics.compute_twr",
            "metrics.compute_sharpe",
            "attribution.currency",
            "charts.overview",
            "risk.compute_factor_exposures",
            "risk.get_factor_exposure_history",
            "risk.overlay_cycle_phases",
            "get_position_details",
            "compute_position_return",
            "compute_portfolio_contribution",
            "compute_position_currency_attribution",
            "compute_position_risk",
            "get_transaction_history",
            "get_security_fundamentals",
            "get_comparable_positions",
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

        portfolio_base_currency = ctx.base_currency or "USD"

        # Query database for real positions using lots table (source of truth)
        try:
            if not ctx.user_id:
                raise ValueError("user_id missing from request context")

            portfolio_uuid = UUID(str(portfolio_id))

            async with get_db_connection_with_rls(str(ctx.user_id)) as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        l.security_id,
                        l.symbol,
                        l.qty_open AS qty,
                        l.cost_basis,
                        l.currency,
                        p.base_currency
                    FROM lots l
                    JOIN portfolios p ON p.id = l.portfolio_id
                    WHERE l.portfolio_id = $1
                      AND l.is_open = true
                      AND l.qty_open > 0
                    """,
                    portfolio_uuid,
                )

            if rows:
                portfolio_base_currency = rows[0]["base_currency"]

            positions = []
            for row in rows:
                qty = Decimal(str(row["qty"]))
                cost_basis = abs(Decimal(str(row["cost_basis"] or 0)))
                positions.append(
                    {
                        "security_id": str(row["security_id"]),
                        "symbol": row["symbol"] or "UNKNOWN",
                        "qty": qty,
                        "cost_basis": cost_basis,
                        "currency": row["currency"] or portfolio_base_currency,
                        "base_currency": portfolio_base_currency,
                    }
                )

            logger.info(f"Retrieved {len(positions)} positions from lots table")

        except Exception as e:
            logger.error(f"Error querying positions from database: {e}", exc_info=True)
            # Fall back to stub data
            positions = [
                {
                    "security_id": "048a0b1e-5fa7-507a-9854-af6a9d7360e9",
                    "symbol": "AAPL",
                    "qty": Decimal("100"),
                    "cost_basis": Decimal("15000.00"),
                    "currency": "USD",
                    "base_currency": portfolio_base_currency,
                },
            ]

        result = {
            "portfolio_id": portfolio_id,
            "asof_date": str(ctx.asof_date) if ctx.asof_date else None,
            "positions": positions,
            "total_positions": len(positions),
            "base_currency": portfolio_base_currency,
        }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"ledger:{ctx.ledger_commit_hash[:8]}",
            asof=ctx.asof_date,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        logger.info(f"✅ ledger_positions returning result with {len(positions)} positions")
        logger.info(f"Result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

        return result


    async def pricing_apply_pack(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        positions: List[Dict[str, Any]],
        pack_id: str = None,
    ) -> Dict[str, Any]:
        """
        Apply pricing pack to positions.

        Args:
            ctx: Request context
            state: Execution state
            positions: List of positions to price
            pack_id: Pricing pack ID (optional, uses ctx.pricing_pack_id if not provided)

        Returns:
            Dict with valued positions
        """
        pack_id = pack_id or ctx.pricing_pack_id
        if not pack_id:
            raise ValueError("pricing_pack_id is required to value positions")

        logger.info(
            f"pricing.apply_pack: pack_id={pack_id}, positions_count={len(positions)}"
        )

        pricing_service = get_pricing_service()

        # Collect security IDs for batch price loading
        security_ids: List[UUID] = []
        for pos in positions:
            sec_id = pos.get("security_id")
            if sec_id:
                try:
                    # Validate and normalize to string
                    security_ids.append(UUID(str(sec_id)))
                except ValueError:
                    logger.warning("Invalid security_id on position: %s", sec_id)

        # Load prices efficiently (plain Decimals, no dataclass overhead)
        price_map: Dict[str, Decimal] = {}
        if security_ids:
            try:
                price_map = await pricing_service.get_prices_as_decimals(
                    security_ids, pack_id
                )
                logger.info(f"Loaded {len(price_map)} prices from pack {pack_id}")
            except Exception as exc:
                logger.error(
                    "Failed to load prices for pack %s: %s", pack_id, exc, exc_info=True
                )

        base_currency = ctx.base_currency
        if not base_currency and positions:
            base_currency = positions[0].get("base_currency")
        if not base_currency:
            base_currency = "USD"

        fx_cache: Dict[tuple, Optional[Decimal]] = {}
        valued_positions: List[Dict[str, Any]] = []
        total_value_base = Decimal("0")

        for pos in positions:
            security_id = str(pos.get("security_id", ""))
            qty = pos.get("qty", Decimal("0"))
            if not security_id or qty == 0:
                logger.warning(
                    "Skipping position with missing security_id or zero quantity: %s",
                    pos,
                )
                continue

            currency = pos.get("currency", base_currency)

            # Direct Decimal lookup (no dataclass unpacking needed)
            price = price_map.get(security_id, Decimal("0"))

            if price == 0:
                logger.warning(
                    "No price for security_id=%s (symbol=%s) in pack %s",
                    security_id,
                    pos.get("symbol"),
                    pack_id,
                )

            value_local = qty * price

            fx_rate = Decimal("1")
            if currency != base_currency and value_local != 0:
                cache_key = (currency, base_currency)
                if cache_key not in fx_cache:
                    fx_record = await pricing_service.get_fx_rate(
                        currency, base_currency, pack_id
                    )
                    fx_cache[cache_key] = fx_record.rate if fx_record else None

                cached_rate = fx_cache.get(cache_key)
                if cached_rate:
                    fx_rate = cached_rate
                else:
                    logger.warning(
                        "No FX rate for %s/%s in pack %s; assuming 1.0",
                        currency,
                        base_currency,
                        pack_id,
                    )

            value_base = value_local * fx_rate

            valued_position = {
                **pos,
                "price": price,
                "value_local": value_local,
                "value": value_base,
                "fx_rate": fx_rate,
                "base_currency": base_currency,
            }
            valued_positions.append(valued_position)
            total_value_base += value_base

        if total_value_base > 0:
            for vp in valued_positions:
                vp["weight"] = vp["value"] / total_value_base
        else:
            for vp in valued_positions:
                vp["weight"] = Decimal("0")

        result = {
            "pricing_pack_id": pack_id,
            "positions": valued_positions,
            "total_value": total_value_base,
            "currency": base_currency,
        }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"pricing_pack:{pack_id}",
            asof=ctx.asof_date,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def metrics_compute_twr(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        asof_date: Optional[date] = None,
        pack_id: Optional[str] = None,
        lookback_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Compute Time-Weighted Return from metrics database.

        Args:
            ctx: Request context (contains portfolio_id, asof_date)
            state: Execution state
            portfolio_id: Override portfolio ID (optional)
            asof_date: Override as-of date (optional)
            pack_id: Pricing pack ID (optional)
            lookback_days: Historical period in days (optional)

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
            f"metrics.compute_twr: portfolio_id={portfolio_id_uuid}, asof_date={asof}, pack_id={pack_id}"
        )

        # Fetch pre-computed metrics from database
        queries = get_metrics_queries()

        # Use pack_id from context if not provided
        effective_pack_id = pack_id or ctx.pricing_pack_id

        try:
            # Get metrics for this portfolio and pricing pack
            metrics = await queries.get_latest_metrics(portfolio_id_uuid, effective_pack_id)

            if not metrics:
                logger.warning(
                    f"No metrics found in database for portfolio {portfolio_id_uuid}, "
                    f"asof={asof}. Returning empty result."
                )
                result = {
                    "portfolio_id": str(portfolio_id_uuid),
                    "asof_date": str(asof) if asof else None,
                    "pricing_pack_id": effective_pack_id,
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
                "pricing_pack_id": effective_pack_id,
                "error": f"Database error: {str(e)}",
                "twr_1d": None,
                "twr_mtd": None,
                "twr_ytd": None,
            }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"metrics_database:{effective_pack_id}",
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

        # Fetch pre-computed metrics from database
        queries = get_metrics_queries()

        # Use pack_id from context
        effective_pack_id = ctx.pricing_pack_id

        try:
            # Get metrics for this portfolio and pricing pack
            metrics = await queries.get_latest_metrics(portfolio_id_uuid, effective_pack_id)

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
        pack_id: Optional[str] = None,
        lookback_days: Optional[int] = None,
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

        logger.info(
            f"attribution.currency called with: portfolio_id={repr(portfolio_id)}, "
            f"ctx.portfolio_id={repr(ctx.portfolio_id)}, "
            f"resolved={repr(portfolio_id_str)}"
        )

        if not portfolio_id_str or portfolio_id_str.strip() == "":
            raise ValueError("portfolio_id required for attribution.currency")

        # Use pack_id and lookback_days
        pack_id = pack_id or ctx.pricing_pack_id
        days = lookback_days or 252

        logger.info(
            f"attribution.currency: portfolio_id={portfolio_id_str}, "
            f"pack_id={pack_id}, lookback_days={days}"
        )

        # Get database connection from services
        from backend.app.db.connection import get_db_pool
        db = get_db_pool()

        # Compute currency attribution using service
        attr_service = CurrencyAttributor(db)

        try:
            # Service computes attribution internally using portfolio positions
            attribution = await attr_service.compute_attribution(
                portfolio_id=portfolio_id_str,
                pack_id=pack_id,
                lookback_days=days
            )

            # Extract results from service response
            result = {
                "portfolio_id": portfolio_id_str,
                "asof_date": str(asof) if asof else None,
                "pricing_pack_id": pack_id,
                "base_currency": base_currency,
                # Attribution components
                "local_return": attribution.get("local_return"),
                "fx_return": attribution.get("fx_return"),
                "interaction_return": attribution.get("interaction"),
                "total_return": attribution.get("total_return"),
                # Validation
                "error_bps": attribution.get("verification", {}).get("error_bps"),
                "by_currency": attribution.get("by_currency", {}),
            }

        except Exception as e:
            logger.error(f"Error computing currency attribution: {e}", exc_info=True)
            result = {
                "portfolio_id": portfolio_id_str,
                "asof_date": str(asof) if asof else None,
                "pricing_pack_id": pack_id,
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
        positions: Dict[str, Any] = None,
        metrics: Dict[str, Any] = None,
        twr: Dict[str, Any] = None,
        currency_attr: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate overview charts using real data from metrics database.

        Args:
            ctx: Request context
            state: Execution state
            positions: Valued positions from pricing.apply_pack
            metrics: Performance metrics from metrics.compute_twr/sharpe
            twr: TWR data from metrics.compute_twr
            currency_attr: Currency attribution from attribution.currency

        Returns:
            Dict with chart configurations for UI rendering
        """
        portfolio_id = ctx.portfolio_id
        if not portfolio_id:
            raise ValueError("portfolio_id required for charts.overview")

        logger.info(f"charts.overview: portfolio_id={portfolio_id}, pack_id={ctx.pricing_pack_id}")

        charts = []

        # Chart 1: Portfolio Allocation (Pie Chart)
        if positions and isinstance(positions, dict) and "positions" in positions:
            position_list = positions["positions"]
            allocation_data = [
                {
                    "symbol": pos.get("symbol", "UNKNOWN"),
                    "value": float(pos.get("value", 0)),
                    "weight": float(pos.get("weight", 0)),
                }
                for pos in position_list
                if float(pos.get("value", 0)) > 0
            ]
            charts.append({
                "type": "pie",
                "title": "Portfolio Allocation by Security",
                "data": allocation_data,
                "total_value": float(positions.get("total_value", 0)),
                "currency": positions.get("currency", "CAD"),
            })

        # Chart 2: Currency Attribution (Donut Chart)
        if currency_attr and isinstance(currency_attr, dict):
            attr_data = [
                {"label": "Local Return", "value": float(currency_attr.get("local_return", 0))},
                {"label": "FX Return", "value": float(currency_attr.get("fx_return", 0))},
                {"label": "Interaction", "value": float(currency_attr.get("interaction_return", 0))},
            ]
            charts.append({
                "type": "donut",
                "title": "Currency Attribution Breakdown",
                "data": attr_data,
                "total_return": float(currency_attr.get("total_return", 0)),
                "base_currency": currency_attr.get("base_currency", "CAD"),
            })

        # Chart 3: Performance Metrics (Bar Chart)
        if twr and isinstance(twr, dict):
            perf_data = []
            for period_key in ["twr_1d", "twr_mtd", "twr_ytd", "twr_1y", "twr_3y", "twr_5y"]:
                period_value = twr.get(period_key)
                if period_value is not None:
                    perf_data.append({
                        "period": period_key.replace("twr_", "").upper(),
                        "return": float(period_value) * 100,  # Convert to percentage
                    })

            if perf_data:
                charts.append({
                    "type": "bar",
                    "title": "Time-Weighted Returns by Period",
                    "data": perf_data,
                    "unit": "%",
                })

        # Chart 4: Risk Metrics (Horizontal Bar)
        if metrics and isinstance(metrics, dict):
            risk_data = []
            if "volatility_30d" in metrics:
                risk_data.append({"metric": "Volatility (30d)", "value": float(metrics["volatility_30d"]) * 100})
            if "sharpe_30d" in metrics:
                risk_data.append({"metric": "Sharpe (30d)", "value": float(metrics["sharpe_30d"])})
            if "max_drawdown_1y" in metrics:
                risk_data.append({"metric": "Max DD (1y)", "value": float(metrics.get("max_drawdown_1y", 0)) * 100})

            if risk_data:
                charts.append({
                    "type": "horizontal_bar",
                    "title": "Risk-Adjusted Metrics",
                    "data": risk_data,
                })

        result = {
            "charts": charts,
            "chart_count": len(charts),
            "portfolio_id": str(portfolio_id),
            "pricing_pack_id": ctx.pricing_pack_id,
        }

        # Attach metadata
        metadata = self._create_metadata(
            source=f"chart_generator:{ctx.pricing_pack_id}",
            asof=ctx.asof_date,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def risk_compute_factor_exposures(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute factor exposures for portfolio.

        Capability: risk.compute_factor_exposures

        Returns factor betas (exposure to market, size, value, momentum factors)
        """
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id
        pack = pack_id or ctx.pricing_pack_id

        logger.info(f"risk.compute_factor_exposures: portfolio_id={portfolio_id_uuid}, pack={pack}")

        from backend.app.services.factor_analysis import FactorAnalysisService
        factor_service = FactorAnalysisService()

        result = await factor_service.compute_factor_exposure(
            portfolio_id=portfolio_id_uuid,
            pack_id=pack
        )

        metadata = self._create_metadata(
            source=f"factor_analysis_service:{pack}",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def risk_get_factor_exposure_history(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """
        Get historical factor exposures for portfolio.

        Capability: risk.get_factor_exposure_history

        Returns time series of factor betas over specified period
        """
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

        logger.info(f"risk.get_factor_exposure_history: portfolio_id={portfolio_id_uuid}, lookback={lookback_days}")

        # Get factor exposures from database for historical packs
        # TODO: Implement historical query - for now return current only
        from backend.app.services.factor_analysis import FactorAnalysisService
        factor_service = FactorAnalysisService()

        current = await factor_service.compute_factor_exposure(
            portfolio_id=portfolio_id_uuid,
            pack_id=ctx.pricing_pack_id
        )

        result = {
            "history": [current],  # TODO: Add historical lookback
            "lookback_days": lookback_days,
            "note": "Historical factor exposure tracking - currently showing latest only"
        }

        metadata = self._create_metadata(
            source=f"factor_analysis_service:history",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def risk_overlay_cycle_phases(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Overlay cycle phase information on risk metrics.

        Capability: risk.overlay_cycle_phases

        Combines factor exposures with current macro cycle phases
        to show how portfolio positioning aligns with cycle
        """
        portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id
        pack = pack_id or ctx.pricing_pack_id

        logger.info(f"risk.overlay_cycle_phases: portfolio_id={portfolio_id_uuid}, pack={pack}")

        # Get factor exposures
        from backend.app.services.factor_analysis import FactorAnalysisService
        factor_service = FactorAnalysisService()

        exposures = await factor_service.compute_factor_exposure(
            portfolio_id=portfolio_id_uuid,
            pack_id=pack
        )

        # Get current cycle phases
        from backend.app.services.cycles import CyclesService
        cycles_service = CyclesService()

        stdc = await cycles_service.detect_stdc_phase()
        ltdc = await cycles_service.detect_ltdc_phase()

        # Overlay analysis
        result = {
            "factor_exposures": exposures,
            "cycles": {
                "short_term": {
                    "phase": stdc.phase,
                    "score": float(stdc.composite_score),
                },
                "long_term": {
                    "phase": ltdc.phase,
                    "score": float(ltdc.composite_score),
                },
            },
            "alignment_analysis": {
                "note": "Factor positioning vs cycle phase alignment",
                "stdc_phase": stdc.phase,
                "ltdc_phase": ltdc.phase,
            }
        }

        metadata = self._create_metadata(
            source=f"risk_cycle_overlay:{pack}",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def get_position_details(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        security_id: str,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get detailed position information.

        Capability: get_position_details

        Returns position details including qty, cost basis, market value, unrealized P&L
        """
        portfolio_uuid = UUID(portfolio_id)
        security_uuid = UUID(security_id)
        pack = pack_id or ctx.pricing_pack_id

        logger.info(f"get_position_details: portfolio={portfolio_id}, security={security_id}, pack={pack}")

        # Query lots table for position details
        db_pool = self.services.get("db")
        if not db_pool:
            raise RuntimeError("Database pool not available")

        async with db_pool.acquire() as conn:
            # Get position from lots
            lots = await conn.fetch(
                """
                SELECT l.*, s.symbol, s.currency as security_currency
                FROM lots l
                JOIN securities s ON l.security_id = s.id
                WHERE l.portfolio_id = $1
                  AND l.security_id = $2
                  AND l.qty_open > 0
                ORDER BY l.open_date
                """,
                portfolio_uuid,
                security_uuid,
            )

            if not lots:
                raise ValueError(f"No open position found for security {security_id}")

            # Calculate aggregated position
            total_qty = sum(Decimal(str(lot["qty_open"])) for lot in lots)
            weighted_cost = sum(
                Decimal(str(lot["qty_open"])) * Decimal(str(lot["price"]))
                for lot in lots
            )
            avg_cost = weighted_cost / total_qty if total_qty > 0 else Decimal("0")

            symbol = lots[0]["symbol"]
            security_currency = lots[0]["security_currency"]

            # Get current price from pricing pack
            price_row = await conn.fetchrow(
                """
                SELECT price
                FROM prices
                WHERE security_id = $1 AND pricing_pack_id = $2
                """,
                security_uuid,
                pack,
            )

            current_price = Decimal(str(price_row["price"])) if price_row else Decimal("0")
            market_value = total_qty * current_price
            unrealized_pnl = market_value - weighted_cost
            unrealized_pnl_pct = (unrealized_pnl / weighted_cost) if weighted_cost > 0 else Decimal("0")

            # Get portfolio total value for weight calculation
            portfolio_value_row = await conn.fetchrow(
                """
                SELECT SUM(l.qty_open * p.price) as total_value
                FROM lots l
                JOIN prices p ON l.security_id = p.security_id
                WHERE l.portfolio_id = $1
                  AND p.pricing_pack_id = $2
                  AND l.qty_open > 0
                """,
                portfolio_uuid,
                pack,
            )

            portfolio_value = Decimal(str(portfolio_value_row["total_value"])) if portfolio_value_row and portfolio_value_row["total_value"] else Decimal("1")
            weight = market_value / portfolio_value if portfolio_value > 0 else Decimal("0")

        result = {
            "symbol": symbol,
            "security_id": str(security_uuid),
            "security_currency": security_currency,
            "qty_open": float(total_qty),
            "avg_cost": float(avg_cost),
            "current_price": float(current_price),
            "market_value": float(market_value),
            "weight": float(weight),
            "unrealized_pnl": float(unrealized_pnl),
            "unrealized_pnl_pct": float(unrealized_pnl_pct),
            "lot_count": len(lots),
        }

        metadata = self._create_metadata(
            source=f"lots_table:{pack}",
            asof=ctx.asof_date,
            ttl=300
        )

        return self._attach_metadata(result, metadata)

    async def compute_position_return(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        security_id: str,
        pack_id: Optional[str] = None,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """
        Compute position return metrics over lookback period using historical pricing data.

        Capability: compute_position_return

        Returns total return, volatility, Sharpe ratio, max drawdown
        """
        security_uuid = UUID(security_id)
        pack = pack_id or ctx.pricing_pack_id

        logger.info(f"compute_position_return: security={security_id}, lookback={lookback_days}, pack={pack}")

        # Get historical prices from pricing packs (last N days)
        db_pool = self.services.get("db")
        if not db_pool:
            raise RuntimeError("Database pool not available")

        async with db_pool.acquire() as conn:
            # Query historical prices for this security
            prices = await conn.fetch(
                """
                SELECT pp.asof_date, p.price
                FROM prices p
                JOIN pricing_packs pp ON p.pricing_pack_id = pp.id
                WHERE p.security_id = $1
                  AND pp.asof_date <= (SELECT asof_date FROM pricing_packs WHERE id = $2)
                  AND pp.asof_date >= (SELECT asof_date FROM pricing_packs WHERE id = $2) - INTERVAL '1 day' * $3
                ORDER BY pp.asof_date ASC
                """,
                security_uuid,
                pack,
                lookback_days,
            )

            if len(prices) < 2:
                logger.warning(f"Insufficient price data for security {security_id}: {len(prices)} data points")
                return self._attach_metadata(
                    {
                        "error": "Insufficient historical data",
                        "data_points": len(prices),
                        "required_minimum": 2,
                    },
                    self._create_metadata(source=f"position_returns:{security_id}", asof=ctx.asof_date, ttl=3600)
                )

            # Calculate daily returns
            daily_returns = []
            for i in range(1, len(prices)):
                prev_price = Decimal(str(prices[i - 1]["price"]))
                curr_price = Decimal(str(prices[i]["price"]))
                if prev_price > 0:
                    daily_return = (curr_price - prev_price) / prev_price
                    daily_returns.append({
                        "date": str(prices[i]["asof_date"]),
                        "return": float(daily_return),
                    })

            if not daily_returns:
                return self._attach_metadata(
                    {"error": "No valid returns calculated", "data_points": len(prices)},
                    self._create_metadata(source=f"position_returns:{security_id}", asof=ctx.asof_date, ttl=3600)
                )

            # Compute metrics
            returns_array = [r["return"] for r in daily_returns]

            # Total return (geometric linking)
            total_return = float(np.prod([1 + r for r in returns_array]) - 1)

            # Annualized volatility
            volatility = float(np.std(returns_array) * np.sqrt(252)) if len(returns_array) > 1 else 0.0

            # Sharpe ratio (assume 4% risk-free rate)
            rf_rate = 0.04
            days_actual = len(daily_returns)
            ann_return = (1 + total_return) ** (252 / days_actual) - 1 if days_actual > 0 else 0.0
            sharpe = (ann_return - rf_rate) / volatility if volatility > 0 else 0.0

            # Max drawdown
            prices_array = [float(p["price"]) for p in prices]
            running_max = np.maximum.accumulate(prices_array)
            drawdowns = (np.array(prices_array) - running_max) / running_max
            max_drawdown = float(np.min(drawdowns))
            max_dd_idx = int(np.argmin(drawdowns))

            # Recovery days (days from max drawdown to recovery)
            peak_value = running_max[max_dd_idx]
            recovery_days = -1
            for i in range(max_dd_idx, len(prices_array)):
                if prices_array[i] >= peak_value:
                    recovery_days = i - max_dd_idx
                    break

        result = {
            "security_id": security_id,
            "total_return": round(total_return, 6),
            "annualized_return": round(ann_return, 6),
            "volatility": round(volatility, 6),
            "sharpe": round(sharpe, 4),
            "max_drawdown": round(max_drawdown, 6),
            "recovery_days": recovery_days,
            "data_points": len(prices),
            "lookback_days": lookback_days,
            "daily_returns": daily_returns,  # For charting
        }

        metadata = self._create_metadata(
            source=f"position_returns:{pack}",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def compute_portfolio_contribution(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        security_id: str,
        pack_id: Optional[str] = None,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """
        Compute position's contribution to portfolio return.

        Capability: compute_portfolio_contribution

        Returns contribution = weight × return
        """
        logger.info(f"compute_portfolio_contribution: security={security_id}")

        # Get position weight
        position = await self.get_position_details(ctx, state, portfolio_id, security_id, pack_id)

        # Calculate contribution (simplified)
        weight = Decimal(str(position["weight"]))
        position_return = Decimal("0.15")  # TODO: Get actual return from compute_position_return

        total_contribution = weight * position_return
        pct_of_portfolio_return = total_contribution / Decimal("0.10")  # TODO: Get actual portfolio return

        result = {
            "total_contribution": float(total_contribution),
            "pct_of_portfolio_return": float(pct_of_portfolio_return),
            "weight": float(weight),
            "position_return": float(position_return),
            "note": "Contribution calculation - requires historical return data"
        }

        metadata = self._create_metadata(
            source=f"contribution:{security_id}",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def compute_position_currency_attribution(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        security_id: str,
        pack_id: Optional[str] = None,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """
        Decompose position return into local and FX components using real historical data.

        Capability: compute_position_currency_attribution

        Returns local, FX, and interaction contributions

        Formula:
            r_base = r_local + r_fx + (r_local × r_fx)
        """
        security_uuid = UUID(security_id)
        pack = pack_id or ctx.pricing_pack_id

        logger.info(f"compute_position_currency_attribution: security={security_id}, pack={pack}")

        # Get position details to determine currency
        position = await self.get_position_details(ctx, state, portfolio_id, security_id, pack)
        security_currency = position.get("security_currency", "USD")
        base_currency = ctx.base_currency or "CAD"

        # If security is in base currency, no FX attribution
        if security_currency == base_currency:
            result = {
                "security_id": security_id,
                "security_currency": security_currency,
                "base_currency": base_currency,
                "local_contribution": float(position.get("unrealized_pnl_pct", 0)),
                "fx_contribution": 0.0,
                "interaction_contribution": 0.0,
                "total_contribution": float(position.get("unrealized_pnl_pct", 0)),
                "note": "Position in base currency - no FX attribution"
            }
            metadata = self._create_metadata(
                source=f"currency_attr:{security_id}",
                asof=ctx.asof_date,
                ttl=3600
            )
            return self._attach_metadata(result, metadata)

        # Get historical prices and FX rates
        db_pool = self.services.get("db")
        if not db_pool:
            raise RuntimeError("Database pool not available")

        async with db_pool.acquire() as conn:
            # Query historical prices in local currency and FX rates
            data = await conn.fetch(
                """
                SELECT
                    pp.asof_date,
                    p.price as local_price,
                    COALESCE(fx.rate, 1.0) as fx_rate
                FROM prices p
                JOIN pricing_packs pp ON p.pricing_pack_id = pp.id
                LEFT JOIN fx_rates fx ON fx.pricing_pack_id = pp.id
                    AND fx.base_ccy = $4
                    AND fx.quote_ccy = $5
                WHERE p.security_id = $1
                  AND pp.asof_date <= (SELECT asof_date FROM pricing_packs WHERE id = $2)
                  AND pp.asof_date >= (SELECT asof_date FROM pricing_packs WHERE id = $2) - INTERVAL '1 day' * $3
                ORDER BY pp.asof_date ASC
                """,
                security_uuid,
                pack,
                lookback_days,
                security_currency,
                base_currency,
            )

            if len(data) < 2:
                logger.warning(f"Insufficient data for currency attribution: {len(data)} data points")
                result = {
                    "error": "Insufficient historical data",
                    "data_points": len(data),
                    "required_minimum": 2,
                }
                metadata = self._create_metadata(
                    source=f"currency_attr:{security_id}",
                    asof=ctx.asof_date,
                    ttl=3600
                )
                return self._attach_metadata(result, metadata)

            # Calculate returns
            start = data[0]
            end = data[-1]

            start_local_price = Decimal(str(start["local_price"]))
            end_local_price = Decimal(str(end["local_price"]))
            start_fx_rate = Decimal(str(start["fx_rate"]))
            end_fx_rate = Decimal(str(end["fx_rate"]))

            # Local return (in security's currency)
            r_local = (end_local_price - start_local_price) / start_local_price if start_local_price > 0 else Decimal("0")

            # FX return (currency move)
            r_fx = (end_fx_rate - start_fx_rate) / start_fx_rate if start_fx_rate > 0 else Decimal("0")

            # Interaction term
            r_interaction = r_local * r_fx

            # Total return in base currency
            r_total = r_local + r_fx + r_interaction

        result = {
            "security_id": security_id,
            "security_currency": security_currency,
            "base_currency": base_currency,
            "local_contribution": float(r_local),
            "fx_contribution": float(r_fx),
            "interaction_contribution": float(r_interaction),
            "total_contribution": float(r_total),
            "lookback_days": lookback_days,
            "data_points": len(data),
        }

        metadata = self._create_metadata(
            source=f"currency_attr:{pack}",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def compute_position_risk(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        security_id: str,
        pack_id: Optional[str] = None,
        lookback_days: int = 252,
    ) -> Dict[str, Any]:
        """
        Compute position risk metrics using historical data.

        Capability: compute_position_risk

        Returns VaR, marginal VaR, beta, correlation, diversification benefit
        """
        security_uuid = UUID(security_id)
        portfolio_uuid = UUID(portfolio_id)
        pack = pack_id or ctx.pricing_pack_id

        logger.info(f"compute_position_risk: security={security_id}, portfolio={portfolio_id}, pack={pack}")

        # Get position details
        position = await self.get_position_details(ctx, state, portfolio_id, security_id, pack)
        market_value = position.get("market_value", 0)

        # Get historical returns for position and portfolio
        db_pool = self.services.get("db")
        if not db_pool:
            raise RuntimeError("Database pool not available")

        async with db_pool.acquire() as conn:
            # Get position returns
            position_data = await conn.fetch(
                """
                SELECT pp.asof_date, p.price
                FROM prices p
                JOIN pricing_packs pp ON p.pricing_pack_id = pp.id
                WHERE p.security_id = $1
                  AND pp.asof_date <= (SELECT asof_date FROM pricing_packs WHERE id = $2)
                  AND pp.asof_date >= (SELECT asof_date FROM pricing_packs WHERE id = $2) - INTERVAL '1 day' * $3
                ORDER BY pp.asof_date ASC
                """,
                security_uuid,
                pack,
                lookback_days,
            )

            # Get portfolio returns (from metrics table)
            portfolio_metrics = await conn.fetch(
                """
                SELECT asof_date, twr_1d as daily_return
                FROM portfolio_metrics
                WHERE portfolio_id = $1
                  AND asof_date <= (SELECT asof_date FROM pricing_packs WHERE id = $2)
                  AND asof_date >= (SELECT asof_date FROM pricing_packs WHERE id = $2) - INTERVAL '1 day' * $3
                  AND twr_1d IS NOT NULL
                ORDER BY asof_date ASC
                """,
                portfolio_uuid,
                pack,
                lookback_days,
            )

            if len(position_data) < 2 or len(portfolio_metrics) < 2:
                logger.warning(f"Insufficient data for risk calculation: position={len(position_data)}, portfolio={len(portfolio_metrics)}")
                result = {
                    "error": "Insufficient historical data",
                    "position_data_points": len(position_data),
                    "portfolio_data_points": len(portfolio_metrics),
                }
                metadata = self._create_metadata(
                    source=f"position_risk:{security_id}",
                    asof=ctx.asof_date,
                    ttl=3600
                )
                return self._attach_metadata(result, metadata)

            # Calculate position returns
            position_returns = []
            for i in range(1, len(position_data)):
                prev_price = Decimal(str(position_data[i - 1]["price"]))
                curr_price = Decimal(str(position_data[i]["price"]))
                if prev_price > 0:
                    ret = float((curr_price - prev_price) / prev_price)
                    position_returns.append(ret)

            # Extract portfolio returns
            portfolio_returns = [float(m["daily_return"]) for m in portfolio_metrics if m["daily_return"] is not None]

            # Align arrays (use minimum length)
            min_len = min(len(position_returns), len(portfolio_returns))
            position_returns = position_returns[-min_len:]
            portfolio_returns = portfolio_returns[-min_len:]

            if min_len < 30:
                logger.warning(f"Insufficient aligned data points: {min_len}")
                result = {
                    "error": "Insufficient aligned data",
                    "aligned_data_points": min_len,
                    "required_minimum": 30,
                }
                metadata = self._create_metadata(
                    source=f"position_risk:{security_id}",
                    asof=ctx.asof_date,
                    ttl=3600
                )
                return self._attach_metadata(result, metadata)

            # Compute risk metrics
            position_vol = float(np.std(position_returns) * np.sqrt(252))
            portfolio_vol = float(np.std(portfolio_returns) * np.sqrt(252))

            # Correlation
            correlation = float(np.corrcoef(position_returns, portfolio_returns)[0, 1]) if min_len > 1 else 0.0

            # Beta (slope of regression: position returns vs portfolio returns)
            covariance = float(np.cov(position_returns, portfolio_returns)[0, 1])
            portfolio_variance = float(np.var(portfolio_returns))
            beta = covariance / portfolio_variance if portfolio_variance > 0 else 1.0

            # VaR at 95% confidence (parametric)
            var_1d_pct = -1.645 * position_vol / np.sqrt(252)  # 1-day VaR
            var_1d = var_1d_pct * market_value

            # Marginal VaR (contribution to portfolio VaR)
            # Approximation: beta × position_weight × portfolio_VaR
            position_weight = position.get("weight", 0)
            portfolio_var_pct = -1.645 * portfolio_vol / np.sqrt(252)
            marginal_var_pct = beta * position_weight * portfolio_var_pct
            marginal_var = marginal_var_pct * market_value

            # Diversification benefit (how much correlation < 1 reduces risk)
            standalone_risk = position_weight * position_vol
            portfolio_contribution = position_weight * beta * portfolio_vol
            diversification_benefit = (standalone_risk - portfolio_contribution) / standalone_risk if standalone_risk > 0 else 0.0

        result = {
            "security_id": security_id,
            "market_value": float(market_value),
            "position_weight": float(position_weight),
            "var_1d": round(var_1d, 2),
            "var_1d_pct": round(var_1d_pct, 6),
            "marginal_var": round(marginal_var, 2),
            "position_volatility": round(position_vol, 6),
            "portfolio_volatility": round(portfolio_vol, 6),
            "beta_to_portfolio": round(beta, 4),
            "correlation": round(correlation, 4),
            "diversification_benefit": round(diversification_benefit, 4),
            "data_points": min_len,
        }

        metadata = self._create_metadata(
            source=f"position_risk:{pack}",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def get_transaction_history(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        security_id: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get transaction history for position.

        Capability: get_transaction_history

        Returns list of buy/sell transactions
        """
        portfolio_uuid = UUID(portfolio_id)
        security_uuid = UUID(security_id)

        logger.info(f"get_transaction_history: portfolio={portfolio_id}, security={security_id}")

        db_pool = self.services.get("db")
        if not db_pool:
            raise RuntimeError("Database pool not available")

        async with db_pool.acquire() as conn:
            transactions = await conn.fetch(
                """
                SELECT
                    trade_date,
                    action,
                    quantity,
                    price,
                    (quantity * price) as total_value,
                    commission,
                    realized_pnl
                FROM transactions
                WHERE portfolio_id = $1
                  AND security_id = $2
                ORDER BY trade_date DESC
                LIMIT $3
                """,
                portfolio_uuid,
                security_uuid,
                limit,
            )

            result = {
                "transactions": [
                    {
                        "trade_date": str(t["trade_date"]),
                        "action": t["action"],
                        "quantity": float(t["quantity"]),
                        "price": float(t["price"]),
                        "total_value": float(t["total_value"]),
                        "commission": float(t["commission"]) if t["commission"] else 0.0,
                        "realized_pnl": float(t["realized_pnl"]) if t["realized_pnl"] else None,
                    }
                    for t in transactions
                ],
                "count": len(transactions),
            }

        metadata = self._create_metadata(
            source=f"transactions_table",
            asof=ctx.asof_date,
            ttl=60
        )

        return self._attach_metadata(result, metadata)

    async def get_security_fundamentals(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        security_id: str,
    ) -> Dict[str, Any]:
        """
        Get fundamental data for security using FMP provider.

        Capability: get_security_fundamentals

        Returns market cap, P/E, dividend yield, sector (for equities)
        """
        security_uuid = UUID(security_id)

        logger.info(f"get_security_fundamentals: security={security_id}")

        db_pool = self.services.get("db")
        if not db_pool:
            raise RuntimeError("Database pool not available")

        async with db_pool.acquire() as conn:
            security = await conn.fetchrow(
                """
                SELECT symbol, name, asset_class
                FROM securities
                WHERE id = $1
                """,
                security_uuid,
            )

            if not security:
                raise ValueError(f"Security not found: {security_id}")

            symbol = security["symbol"]
            name = security["name"]
            asset_class = security["asset_class"]

        # For non-equity securities, return basic info only
        if asset_class not in ["equity", "stock"]:
            result = {
                "security_id": security_id,
                "symbol": symbol,
                "name": name,
                "asset_class": asset_class,
                "note": f"Fundamentals not available for asset class: {asset_class}"
            }
            metadata = self._create_metadata(
                source="securities_table",
                asof=ctx.asof_date,
                ttl=86400
            )
            return self._attach_metadata(result, metadata)

        # Fetch from FMP provider
        try:
            from backend.app.integrations.fmp_provider import FMPProvider
            import os
            
            api_key = os.getenv("FMP_API_KEY")
            if not api_key:
                logger.warning("FMP_API_KEY not configured, using stub data")
                return self._get_stub_fundamentals(security_id, symbol, name)
                
            fmp = FMPProvider(api_key=api_key)
            profile = await fmp.get_profile(symbol)

            # Extract fundamental metrics
            result = {
                "security_id": security_id,
                "symbol": symbol,
                "name": profile.get("companyName", name),
                "asset_class": asset_class,
                "exchange": profile.get("exchangeShortName"),
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "market_cap": profile.get("mktCap"),
                "price": profile.get("price"),
                "beta": profile.get("beta"),
                "pe_ratio": profile.get("pe"),
                "eps": profile.get("eps"),
                "dividend_yield": profile.get("lastDiv"),
                "52_week_high": profile.get("range", "").split("-")[-1].strip() if profile.get("range") else None,
                "52_week_low": profile.get("range", "").split("-")[0].strip() if profile.get("range") else None,
                "volume_avg": profile.get("volAvg"),
                "description": profile.get("description"),
                "ceo": profile.get("ceo"),
                "website": profile.get("website"),
                "ipo_date": profile.get("ipoDate"),
                "country": profile.get("country"),
                "currency": profile.get("currency"),
                "employees": profile.get("fullTimeEmployees"),
            }

            # Get ratios for additional metrics
            try:
                ratios = await fmp.get_ratios(symbol, limit=1)
                if ratios and len(ratios) > 0:
                    latest_ratios = ratios[0]
                    result.update({
                        "roe": latest_ratios.get("returnOnEquity"),
                        "roa": latest_ratios.get("returnOnAssets"),
                        "debt_to_equity": latest_ratios.get("debtEquityRatio"),
                        "current_ratio": latest_ratios.get("currentRatio"),
                        "quick_ratio": latest_ratios.get("quickRatio"),
                        "gross_margin": latest_ratios.get("grossProfitMargin"),
                        "operating_margin": latest_ratios.get("operatingProfitMargin"),
                        "net_margin": latest_ratios.get("netProfitMargin"),
                        "payout_ratio": latest_ratios.get("payoutRatio"),
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch ratios for {symbol}: {e}")

            await fmp.close()

            metadata = self._create_metadata(
                source="FMP",
                asof=ctx.asof_date,
                ttl=86400  # Cache fundamentals for 24 hours
            )

            return self._attach_metadata(result, metadata)

        except Exception as e:
            logger.error(f"Failed to fetch fundamentals from FMP for {symbol}: {e}", exc_info=True)

            # Return basic info from database on FMP failure
            result = {
                "security_id": security_id,
                "symbol": symbol,
                "name": name,
                "asset_class": asset_class,
                "error": f"FMP provider unavailable: {str(e)}",
                "note": "Using database fallback - limited data available"
            }

            metadata = self._create_metadata(
                source="securities_table_fallback",
                asof=ctx.asof_date,
                ttl=3600
            )

            return self._attach_metadata(result, metadata)

    async def get_comparable_positions(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        security_id: str,
        sector: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Find comparable positions in same sector.

        Capability: get_comparable_positions

        Returns list of similar securities for comparison
        """
        logger.info(f"get_comparable_positions: security={security_id}, sector={sector}")

        # TODO: Implement sector-based security lookup
        # For now, return placeholder structure

        result = {
            "comparables": [],  # TODO: Query securities by sector
            "count": 0,
            "sector": sector,
            "note": "Comparables - requires sector classification data"
        }

        metadata = self._create_metadata(
            source=f"comparables:{security_id}",
            asof=ctx.asof_date,
            ttl=86400
        )

        return self._attach_metadata(result, metadata)
