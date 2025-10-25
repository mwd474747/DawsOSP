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
from app.db import (
    get_metrics_queries,
    get_pricing_pack_queries,
    get_db_connection_with_rls,
)
from app.services.pricing import get_pricing_service
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
