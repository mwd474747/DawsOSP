"""
DawsOS Charts Agent

Purpose: Chart formatting and visualization specifications
Updated: 2025-10-27
Priority: P0 (Critical for pattern execution)

Capabilities:
    - charts.macro_overview: Format macro data for visualization
    - charts.scenario_deltas: Format scenario delta comparisons

Used by Patterns:
    - portfolio_macro_overview.json
    - portfolio_scenario_analysis.json

Architecture:
    Agent → Pure formatting logic (no external dependencies)
"""

import logging
from typing import Any, Dict, List, Optional
from decimal import Decimal

from backend.app.agents.base_agent import BaseAgent, AgentMetadata
from backend.app.core.types import RequestCtx

logger = logging.getLogger("DawsOS.ChartsAgent")


class ChartsAgent(BaseAgent):
    """
    Charts Agent.

    Provides capabilities for chart formatting and visualization specs.
    Pure formatting logic - no external service dependencies.
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "charts.macro_overview",
            "charts.scenario_deltas"
        ]

    async def charts_macro_overview(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        regime: Dict[str, Any],
        indicators: Dict[str, Any],
        factor_exposures: Dict[str, Any],
        dar: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format macro data for visualization.

        Capability: charts.macro_overview
        Pattern: portfolio_macro_overview.json

        Args:
            ctx: Request context
            state: Pattern state
            regime: Regime classification results
            indicators: Economic indicators
            factor_exposures: Portfolio factor exposures
            dar: Drawdown at Risk calculation

        Returns:
            {
                "regime_card": {...},
                "factor_exposures": {...},
                "dar_widget": {...},
                "indicators_table": {...}
            }
        """
        logger.info("charts.macro_overview: formatting macro visualization data")

        # Format regime card
        regime_scores = regime.get("regime_scores", {})
        regime_card = {
            "type": "regime_probabilities",
            "data": [
                {"regime": name, "probability": float(score)}
                for name, score in regime_scores.items()
            ],
            "current": regime.get("regime_name", "Unknown"),
            "confidence": float(regime.get("confidence", 0.0)),
            "date": str(regime.get("date", ctx.asof_date)),
            "chart_config": {
                "type": "stacked_bar",
                "colors": {
                    "Expansion": "#2ecc71",
                    "Slowdown": "#f39c12",
                    "Recession": "#e74c3c",
                    "Recovery": "#3498db",
                    "Stagflation": "#9b59b6"
                },
                "height": 120
            }
        }

        # Format factor exposures
        exposures_data = factor_exposures.get("exposures", {})
        factor_chart = {
            "type": "horizontal_bar",
            "data": [
                {
                    "factor": factor_name,
                    "exposure": float(exposure),
                    "color": self._get_factor_color(exposure)
                }
                for factor_name, exposure in exposures_data.items()
            ],
            "chart_config": {
                "x_axis": "Exposure",
                "y_axis": "Factor",
                "bar_height": 30,
                "show_grid": True,
                "highlight_threshold": 0.3
            }
        }

        # Format DaR widget
        dar_pct = float(dar.get("dar_pct", 0.0))
        confidence_level = float(dar.get("confidence_level", 0.95))
        dar_widget = {
            "type": "gauge",
            "value": abs(dar_pct),
            "threshold": confidence_level,
            "regime_context": regime.get("regime_name", "Unknown"),
            "severity": self._get_dar_severity(dar_pct),
            "chart_config": {
                "min": 0,
                "max": 0.5,  # 50% max drawdown
                "zones": [
                    {"from": 0, "to": 0.1, "color": "#2ecc71"},    # Green: 0-10%
                    {"from": 0.1, "to": 0.2, "color": "#f39c12"},  # Orange: 10-20%
                    {"from": 0.2, "to": 0.5, "color": "#e74c3c"}   # Red: 20-50%
                ],
                "show_current_regime": True
            }
        }

        # Format indicators table
        indicator_list = indicators.get("indicators", [])
        indicators_table = {
            "type": "indicator_table",
            "data": [
                {
                    "name": ind.get("name", "Unknown"),
                    "value": float(ind.get("value", 0.0)),
                    "zscore": float(ind.get("zscore", 0.0)),
                    "trend": self._get_trend_arrow(ind.get("zscore", 0.0)),
                    "formatted_value": self._format_indicator_value(
                        ind.get("value", 0.0),
                        ind.get("format", "percent")
                    )
                }
                for ind in indicator_list
            ]
        }

        result = {
            "regime_card": regime_card,
            "factor_exposures": factor_chart,
            "dar_widget": dar_widget,
            "indicators_table": indicators_table,
            "chart_count": 4
        }

        metadata = self._create_metadata(
            source="charts_agent:macro_overview",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def charts_scenario_deltas(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        base: Dict[str, Any],
        shocked: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format scenario delta comparison tables.

        Capability: charts.scenario_deltas
        Pattern: portfolio_scenario_analysis.json

        Args:
            ctx: Request context
            state: Pattern state
            base: Base portfolio valuations
            shocked: Shocked portfolio valuations (post-scenario)

        Returns:
            {
                "position_deltas": [...],
                "portfolio_delta": {...},
                "waterfall_chart": {...}
            }
        """
        logger.info("charts.scenario_deltas: formatting scenario delta visualization")

        # Calculate position-level deltas
        base_positions = base.get("positions", [])
        shocked_positions = shocked.get("positions", [])

        # Create lookup dict for shocked positions
        shocked_lookup = {
            p.get("security_id"): p
            for p in shocked_positions
        }

        position_deltas = []
        for base_pos in base_positions:
            security_id = base_pos.get("security_id")
            shocked_pos = shocked_lookup.get(security_id)

            if shocked_pos:
                base_value = float(base_pos.get("market_value", 0.0))
                shocked_value = float(shocked_pos.get("market_value", 0.0))
                delta_value = shocked_value - base_value
                delta_pct = (delta_value / base_value) if base_value != 0 else 0.0

                position_deltas.append({
                    "security_id": security_id,
                    "symbol": base_pos.get("symbol", "Unknown"),
                    "name": base_pos.get("name", base_pos.get("symbol", "Unknown")),
                    "base_value": base_value,
                    "shocked_value": shocked_value,
                    "delta_value": delta_value,
                    "delta_pct": delta_pct,
                    "severity": self._get_delta_severity(delta_pct),
                    "contribution": delta_value  # For waterfall chart
                })

        # Sort by absolute delta (largest changes first)
        position_deltas.sort(key=lambda x: abs(x["delta_value"]), reverse=True)

        # Calculate portfolio-level delta
        base_nav = sum(float(p.get("market_value", 0.0)) for p in base_positions)
        shocked_nav = sum(float(p.get("market_value", 0.0)) for p in shocked_positions)
        total_impact = shocked_nav - base_nav
        total_impact_pct = (total_impact / base_nav) if base_nav != 0 else 0.0

        portfolio_delta = {
            "base_nav": base_nav,
            "shocked_nav": shocked_nav,
            "total_impact": total_impact,
            "total_impact_pct": total_impact_pct,
            "currency": base.get("base_currency", "CAD"),
            "scenario_id": shocked.get("scenario_id", "Unknown")
        }

        # Format waterfall chart
        waterfall_chart = {
            "type": "waterfall",
            "data": [
                {"label": "Base Portfolio", "value": base_nav, "type": "start"},
                *[
                    {
                        "label": d["symbol"],
                        "value": d["delta_value"],
                        "type": "positive" if d["delta_value"] > 0 else "negative"
                    }
                    for d in position_deltas[:10]  # Top 10 contributors
                ],
                {"label": "Shocked Portfolio", "value": shocked_nav, "type": "end"}
            ],
            "chart_config": {
                "colors": {
                    "positive": "#2ecc71",
                    "negative": "#e74c3c",
                    "start": "#3498db",
                    "end": "#3498db"
                },
                "show_connectors": True,
                "format": "currency"
            }
        }

        result = {
            "position_deltas": position_deltas,
            "portfolio_delta": portfolio_delta,
            "waterfall_chart": waterfall_chart,
            "delta_count": len(position_deltas)
        }

        metadata = self._create_metadata(
            source="charts_agent:scenario_deltas",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    # Helper methods

    def _get_factor_color(self, exposure: float) -> str:
        """Get color for factor exposure based on magnitude."""
        abs_exp = abs(exposure)
        if abs_exp > 0.5:
            return "#e74c3c"  # Red: High exposure
        elif abs_exp > 0.3:
            return "#f39c12"  # Orange: Medium exposure
        else:
            return "#2ecc71"  # Green: Low exposure

    def _get_dar_severity(self, dar_pct: float) -> str:
        """Get severity level for DaR value."""
        abs_dar = abs(dar_pct)
        if abs_dar > 0.2:
            return "high"
        elif abs_dar > 0.1:
            return "medium"
        else:
            return "low"

    def _get_trend_arrow(self, zscore: float) -> str:
        """Get trend arrow based on z-score."""
        if zscore > 1.0:
            return "↑↑"  # Strong uptrend
        elif zscore > 0.5:
            return "↑"   # Uptrend
        elif zscore < -1.0:
            return "↓↓"  # Strong downtrend
        elif zscore < -0.5:
            return "↓"   # Downtrend
        else:
            return "→"   # Neutral

    def _format_indicator_value(self, value: float, format_type: str) -> str:
        """Format indicator value based on type."""
        if format_type == "percent":
            return f"{value:.2%}"
        elif format_type == "decimal":
            return f"{value:.2f}"
        elif format_type == "integer":
            return f"{int(value):,}"
        else:
            return f"{value:.2f}"

    def _get_delta_severity(self, delta_pct: float) -> str:
        """Get severity level for delta percentage."""
        abs_delta = abs(delta_pct)
        if abs_delta > 0.15:
            return "high"
        elif abs_delta > 0.05:
            return "medium"
        else:
            return "low"
