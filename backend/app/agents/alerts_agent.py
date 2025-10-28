"""
DawsOS Alerts Agent

Purpose: Alert suggestions and threshold-based alert creation
Updated: 2025-10-27
Priority: P0 (Critical for pattern execution)

Capabilities:
    - alerts.suggest_presets: Suggest alert presets based on trend analysis
    - alerts.create_if_threshold: Create alert if threshold exceeded

Used by Patterns:
    - macro_trend_monitor.json
    - news_impact_analysis.json

Architecture:
    Agent → AlertService → Database/Playbooks
"""

import logging
from typing import Any, Dict, List, Optional
from decimal import Decimal

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx

logger = logging.getLogger("DawsOS.AlertsAgent")


class AlertsAgent(BaseAgent):
    """
    Alerts Agent.

    Provides capabilities for alert suggestions and threshold-based creation.
    Integrates with:
        - AlertService (condition evaluation)
        - PlaybookGenerator (playbook generation)
    """

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "alerts.suggest_presets",
            "alerts.create_if_threshold"
        ]

    async def alerts_suggest_presets(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        portfolio_id: str,
    ) -> Dict[str, Any]:
        """
        Suggest alert presets based on trend analysis.

        Capability: alerts.suggest_presets
        Pattern: macro_trend_monitor.json

        Args:
            ctx: Request context
            state: Pattern state
            trend_analysis: Trend analysis results (from macro.detect_trend_shifts)
            portfolio_id: Portfolio UUID

        Returns:
            {
                "suggestions": [
                    {
                        "type": "regime_shift",
                        "priority": "high",
                        "condition": {...},
                        "playbook": {...}
                    },
                    ...
                ],
                "count": int
            }
        """
        logger.info(f"alerts.suggest_presets: portfolio_id={portfolio_id}")

        from app.services.playbooks import PlaybookGenerator

        playbook_gen = PlaybookGenerator()
        suggestions = []

        # Check for regime shift
        if trend_analysis.get("regime_shift_detected"):
            old_regime = trend_analysis.get("old_regime", "Unknown")
            new_regime = trend_analysis.get("new_regime", "Unknown")
            confidence = trend_analysis.get("confidence", 0.0)

            playbook = playbook_gen.generate_regime_shift_playbook(
                old_regime=old_regime,
                new_regime=new_regime,
                confidence=float(confidence)
            )

            suggestions.append({
                "type": "regime_shift",
                "priority": "high",
                "title": f"Regime Shift: {old_regime} → {new_regime}",
                "condition": {
                    "type": "macro",
                    "entity": "regime",
                    "metric": "classification",
                    "op": "!=",
                    "value": old_regime,
                    "window": "weekly"
                },
                "playbook": playbook,
                "confidence": confidence
            })

        # Check for DaR increase
        if trend_analysis.get("dar_increasing"):
            dar_change = trend_analysis.get("dar_change_pct", 0.0)
            current_dar = trend_analysis.get("current_dar", 0.0)

            playbook = playbook_gen.generate_dar_breach_playbook(
                threshold=float(current_dar),
                portfolio_id=portfolio_id,
                severity="warning"
            )

            suggestions.append({
                "type": "dar_increase",
                "priority": "medium",
                "title": f"DaR Increased by {dar_change:.1%}",
                "condition": {
                    "type": "metric",
                    "entity": portfolio_id,
                    "metric": "dar",
                    "op": ">",
                    "value": current_dar * 1.1,  # Alert if 10% higher
                    "window": "weekly"
                },
                "playbook": playbook,
                "dar_change": dar_change
            })

        # Check for factor exposure spikes
        if trend_analysis.get("factor_spike_detected"):
            factor_name = trend_analysis.get("spike_factor", "Unknown")
            spike_magnitude = trend_analysis.get("spike_magnitude", 0.0)

            suggestions.append({
                "type": "factor_spike",
                "priority": "low",
                "title": f"Factor Exposure Spike: {factor_name}",
                "condition": {
                    "type": "metric",
                    "entity": portfolio_id,
                    "metric": f"factor_{factor_name.lower()}_exposure",
                    "op": ">",
                    "value": spike_magnitude * 0.8,
                    "window": "weekly"
                },
                "playbook": {
                    "title": "Factor Exposure Monitoring",
                    "description": f"Monitor {factor_name} exposure for rebalancing opportunities",
                    "actions": [
                        f"Review positions contributing to {factor_name} exposure",
                        "Consider rebalancing to reduce concentration",
                        "Monitor correlation with other factors"
                    ]
                },
                "spike_magnitude": spike_magnitude
            })

        result = {
            "suggestions": suggestions,
            "count": len(suggestions),
            "portfolio_id": portfolio_id,
            "analysis_date": str(ctx.asof_date)
        }

        metadata = self._create_metadata(
            source="alerts_service:suggest_presets",
            asof=ctx.asof_date,
            ttl=3600
        )

        return self._attach_metadata(result, metadata)

    async def alerts_create_if_threshold(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: str,
        news_impact: Dict[str, Any],
        threshold: Optional[float] = 0.05,
    ) -> Dict[str, Any]:
        """
        Create alert if news impact exceeds threshold.

        Capability: alerts.create_if_threshold
        Pattern: news_impact_analysis.json

        Args:
            ctx: Request context
            state: Pattern state
            portfolio_id: Portfolio UUID
            news_impact: News impact analysis results
            threshold: Impact threshold (default 5%)

        Returns:
            {
                "alert_created": bool,
                "alert": {...} or None,
                "reason": str (if not created)
            }
        """
        logger.info(f"alerts.create_if_threshold: portfolio_id={portfolio_id}, threshold={threshold}")

        from app.services.alerts import AlertService

        alert_service = AlertService(use_db=self.services is not None)

        # Extract total impact
        total_impact = abs(float(news_impact.get("total_impact", 0.0)))
        threshold_value = threshold or 0.05

        if total_impact > threshold_value:
            # Create alert condition
            condition = {
                "type": "news_sentiment",
                "entity": portfolio_id,
                "metric": "total_impact",
                "op": ">",
                "value": threshold_value,
                "window": "intraday"
            }

            # Evaluate condition
            try:
                eval_result = await alert_service.evaluate_condition(
                    condition=condition,
                    ctx={"asof_date": ctx.asof_date}
                )

                alert_data = {
                    "type": "news_impact",
                    "portfolio_id": portfolio_id,
                    "condition": condition,
                    "triggered_at": str(ctx.asof_date),
                    "impact_magnitude": total_impact,
                    "threshold": threshold_value,
                    "evaluation": eval_result,
                    "news_summary": news_impact.get("summary", "Significant news impact detected"),
                    "affected_positions": news_impact.get("affected_positions", [])
                }

                result = {
                    "alert_created": True,
                    "alert": alert_data,
                    "reason": f"News impact ({total_impact:.2%}) exceeded threshold ({threshold_value:.2%})"
                }

                logger.info(f"Alert created for portfolio {portfolio_id}: impact={total_impact:.2%}")

            except Exception as e:
                logger.error(f"Failed to create alert: {e}")
                result = {
                    "alert_created": False,
                    "alert": None,
                    "reason": f"Alert creation failed: {str(e)}"
                }

        else:
            result = {
                "alert_created": False,
                "alert": None,
                "reason": f"Impact ({total_impact:.2%}) below threshold ({threshold_value:.2%})"
            }

            logger.debug(f"No alert created: impact below threshold")

        metadata = self._create_metadata(
            source="alerts_service:create_if_threshold",
            asof=ctx.asof_date,
            ttl=300  # 5 minutes
        )

        return self._attach_metadata(result, metadata)
