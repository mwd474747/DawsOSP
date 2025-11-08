"""
Macro-Aware Scenario Service
Integrates scenario analysis with macro regime detection for dynamic risk assessment.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum

# Core imports
from app.services.scenarios import (
    ScenarioService,
    ShockType,
    Shock,
    ScenarioResult,
    PositionShockResult,
    HedgeRecommendation,
    SCENARIO_LIBRARY
)
from app.services.macro import MacroService, Regime, RegimeClassification

logger = logging.getLogger(__name__)


class RegimeScenarioAdjustment:
    """Defines how scenarios adjust based on macro regime."""
    
    def __init__(
        self,
        probability_multiplier: float = 1.0,
        severity_multiplier: float = 1.0,
        additional_shocks: Optional[Dict[str, float]] = None
    ):
        self.probability_multiplier = probability_multiplier
        self.severity_multiplier = severity_multiplier
        self.additional_shocks = additional_shocks or {}


# Define regime-specific adjustments for each shock type
REGIME_ADJUSTMENTS = {
    Regime.EARLY_EXPANSION: {
        ShockType.RATES_UP: RegimeScenarioAdjustment(
            probability_multiplier=0.5,  # Less likely in early recovery
            severity_multiplier=0.8
        ),
        ShockType.RATES_DOWN: RegimeScenarioAdjustment(
            probability_multiplier=0.3,  # Very unlikely
            severity_multiplier=0.5
        ),
        ShockType.EQUITY_RALLY: RegimeScenarioAdjustment(
            probability_multiplier=2.0,  # More likely in recovery
            severity_multiplier=1.2
        ),
        ShockType.CREDIT_SPREAD_TIGHTENING: RegimeScenarioAdjustment(
            probability_multiplier=2.5,  # Very likely as risk-on returns
            severity_multiplier=1.3
        ),
    },
    Regime.MID_EXPANSION: {
        ShockType.RATES_UP: RegimeScenarioAdjustment(
            probability_multiplier=1.2,  # Slightly more likely
            severity_multiplier=1.0
        ),
        ShockType.EQUITY_RALLY: RegimeScenarioAdjustment(
            probability_multiplier=1.3,
            severity_multiplier=1.0
        ),
        ShockType.CPI_SURPRISE: RegimeScenarioAdjustment(
            probability_multiplier=0.8,  # Less inflation risk mid-cycle
            severity_multiplier=0.9
        ),
    },
    Regime.LATE_EXPANSION: {
        ShockType.RATES_UP: RegimeScenarioAdjustment(
            probability_multiplier=2.0,  # Very likely as Fed tightens
            severity_multiplier=1.3
        ),
        ShockType.CPI_SURPRISE: RegimeScenarioAdjustment(
            probability_multiplier=2.5,  # High inflation risk
            severity_multiplier=1.5
        ),
        ShockType.EQUITY_SELLOFF: RegimeScenarioAdjustment(
            probability_multiplier=3.0,  # 3x crash probability!
            severity_multiplier=1.5,
            additional_shocks={"volatility_spike": 0.5}  # Add vol component
        ),
        ShockType.CREDIT_SPREAD_WIDENING: RegimeScenarioAdjustment(
            probability_multiplier=2.5,
            severity_multiplier=1.4
        ),
    },
    Regime.DEEP_CONTRACTION: {
        ShockType.RATES_DOWN: RegimeScenarioAdjustment(
            probability_multiplier=3.0,  # Fed cuts aggressively
            severity_multiplier=2.0
        ),
        ShockType.EQUITY_SELLOFF: RegimeScenarioAdjustment(
            probability_multiplier=4.0,  # Very high crash risk
            severity_multiplier=2.0,
            additional_shocks={"volatility_spike": 1.0}
        ),
        ShockType.CREDIT_SPREAD_WIDENING: RegimeScenarioAdjustment(
            probability_multiplier=5.0,  # Credit stress very likely
            severity_multiplier=2.5
        ),
        ShockType.USD_UP: RegimeScenarioAdjustment(
            probability_multiplier=2.0,  # Flight to quality
            severity_multiplier=1.5
        ),
    },
}


class CyclePhaseAdjustment:
    """Adjustments based on specific cycle phases."""
    
    # LTDC phase adjustments
    LTDC_ADJUSTMENTS = {
        "LEVERAGING": {
            "risk_multiplier": 0.7,  # Lower risk early in cycle
            "correlation_reduction": 0.2
        },
        "BUBBLE": {
            "risk_multiplier": 1.5,  # Higher risk in bubble
            "correlation_increase": 0.3,
            "volatility_multiplier": 1.5
        },
        "TOP": {
            "risk_multiplier": 2.0,  # Maximum risk at top
            "correlation_increase": 0.5,
            "volatility_multiplier": 2.0
        },
        "DEPRESSION": {
            "risk_multiplier": 1.8,
            "correlation_increase": 0.7,  # Everything correlates to 1
            "deflation_risk": 0.5
        },
        "BEAUTIFUL_DELEVERAGING": {
            "risk_multiplier": 0.9,
            "correlation_reduction": 0.3
        },
        "NORMALIZATION": {
            "risk_multiplier": 0.8,
            "correlation_reduction": 0.2
        }
    }
    
    # Empire cycle adjustments
    EMPIRE_ADJUSTMENTS = {
        "RISE": {
            "innovation_boost": 1.2,
            "risk_appetite": 1.3
        },
        "PEAK": {
            "complacency_factor": 1.5,
            "hidden_risk_multiplier": 1.4
        },
        "DECLINE": {
            "structural_risk_multiplier": 1.8,
            "currency_risk": 1.5
        }
    }


class MacroAwareScenarioService:
    """
    Enhanced scenario service that adjusts for macro regime and cycles.
    Bridges the gap between static scenarios and dynamic market conditions.
    """
    
    def __init__(self, use_db: bool = True):
        self.scenario_service = ScenarioService()  # No parameters needed
        self.macro_service = MacroService()
        self.use_db = use_db
        logger.info("Initialized MacroAwareScenarioService")
    
    async def get_current_macro_state(self) -> Dict:
        """Get comprehensive macro state including all cycles."""
        try:
            # Get regime detection
            regime_data = await self.macro_service.detect_regime()
            
            # Extract cycle phases from RegimeClassification
            macro_state = {
                "regime": regime_data.regime,
                "regime_probability": regime_data.regime_probabilities,
                "stdc_phase": regime_data.drivers.get("stdc_phase", "UNKNOWN"),
                "ltdc_phase": regime_data.drivers.get("ltdc_phase", "UNKNOWN"),
                "empire_phase": regime_data.drivers.get("empire_phase", "UNKNOWN"),
                "internal_order_stage": regime_data.drivers.get("internal_order_stage", 3),
                "risk_level": regime_data.drivers.get("risk_level", "MEDIUM"),
                "indicators": regime_data.indicators,
                "z_scores": regime_data.zscores
            }
            
            logger.info(f"Current macro state: Regime={macro_state['regime']}, LTDC={macro_state['ltdc_phase']}")
            return macro_state
            
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - re-raise to surface bugs immediately
            logger.error(f"Programming error getting macro state: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service/database errors - return neutral state on error (graceful degradation)
            logger.error(f"Failed to get macro state: {e}")
            return {
                "regime": Regime.MID_EXPANSION,  # Default to mid-expansion
                "regime_probability": {},
                "stdc_phase": "UNKNOWN",
                "ltdc_phase": "UNKNOWN",
                "empire_phase": "UNKNOWN",
                "internal_order_stage": 3,
                "risk_level": "MEDIUM"
            }
    
    def adjust_shock_for_regime(
        self,
        base_shock: Shock,
        macro_state: Dict
    ) -> Shock:
        """
        Adjust shock parameters based on current macro regime and cycles.
        
        This is where the magic happens - we dynamically adjust probabilities
        and severities based on where we are in various cycles.
        """
        
        # Start with base shock
        adjusted_shock = Shock(
            shock_type=base_shock.shock_type,
            name=base_shock.name,
            description=base_shock.description,
            real_rates_bps=base_shock.real_rates_bps,
            inflation_bps=base_shock.inflation_bps,
            credit_spread_bps=base_shock.credit_spread_bps,
            usd_pct=base_shock.usd_pct,
            equity_pct=base_shock.equity_pct,
            probability=base_shock.probability,
            severity=base_shock.severity
        )
        
        # Apply regime adjustments
        regime = macro_state.get("regime", Regime.MID_EXPANSION)
        if regime in REGIME_ADJUSTMENTS:
            regime_adj = REGIME_ADJUSTMENTS[regime].get(
                base_shock.shock_type,
                RegimeScenarioAdjustment()
            )
            
            # Adjust probability
            adjusted_shock.probability *= regime_adj.probability_multiplier
            adjusted_shock.probability = min(adjusted_shock.probability, 0.95)  # Cap at 95%
            
            # Adjust severity (scale the shock magnitudes)
            if regime_adj.severity_multiplier != 1.0:
                adjusted_shock.real_rates_bps *= regime_adj.severity_multiplier
                adjusted_shock.inflation_bps *= regime_adj.severity_multiplier
                adjusted_shock.credit_spread_bps *= regime_adj.severity_multiplier
                adjusted_shock.usd_pct *= regime_adj.severity_multiplier
                adjusted_shock.equity_pct *= regime_adj.severity_multiplier
                
                # Update severity label
                if regime_adj.severity_multiplier > 1.5:
                    adjusted_shock.severity = "extreme"
                elif regime_adj.severity_multiplier > 1.2:
                    adjusted_shock.severity = "high"
        
        # Apply LTDC adjustments
        ltdc_phase = macro_state.get("ltdc_phase", "UNKNOWN")
        if ltdc_phase in CyclePhaseAdjustment.LTDC_ADJUSTMENTS:
            ltdc_adj = CyclePhaseAdjustment.LTDC_ADJUSTMENTS[ltdc_phase]
            risk_mult = ltdc_adj.get("risk_multiplier", 1.0)
            
            # Scale all shocks by LTDC risk multiplier
            adjusted_shock.equity_pct *= risk_mult
            adjusted_shock.credit_spread_bps *= risk_mult
            
            # Adjust correlation assumptions if needed
            if "correlation_increase" in ltdc_adj:
                # This would affect how we calculate portfolio impact
                adjusted_shock.description += f" (High correlation regime: {ltdc_adj['correlation_increase']})"
        
        # Apply Empire cycle adjustments
        empire_phase = macro_state.get("empire_phase", "UNKNOWN")
        if empire_phase == "DECLINE":
            # Add currency risk to all scenarios
            adjusted_shock.usd_pct *= 1.5
            adjusted_shock.description += " (Empire decline: heightened currency risk)"
        
        # Internal order adjustments
        internal_stage = macro_state.get("internal_order_stage", 3)
        if internal_stage >= 5:  # Stage 5-6: High conflict/revolution risk
            adjusted_shock.probability *= 1.5
            adjusted_shock.description += " (Internal disorder: heightened tail risks)"
        
        # Add contextual information to description
        adjusted_shock.description = f"[{regime.value}] {adjusted_shock.description}"
        
        return adjusted_shock
    
    async def apply_macro_aware_scenario(
        self,
        portfolio_id: str,
        shock_type: ShockType,
        pack_id: str,
        as_of_date: Optional[date] = None
    ) -> Dict:
        """
        Apply scenario with macro-aware adjustments.
        
        Returns enhanced result with macro context and adjusted impacts.
        """
        
        # Get current macro state
        macro_state = await self.get_current_macro_state()
        
        # Get base shock definition
        base_shock = SCENARIO_LIBRARY.get(shock_type)
        if not base_shock:
            raise ValueError(f"Unknown shock type: {shock_type}")
        
        # Adjust shock for current regime
        adjusted_shock = self.adjust_shock_for_regime(base_shock, macro_state)
        
        # Temporarily replace the shock in the service
        original_shock = self.scenario_service.scenarios[shock_type]
        self.scenario_service.scenarios[shock_type] = adjusted_shock
        
        try:
            # Apply the adjusted scenario
            result = await self.scenario_service.apply_scenario(
                portfolio_id=portfolio_id,
                shock_type=shock_type,
                pack_id=pack_id,
                as_of_date=as_of_date
            )
            
            # Enhance result with macro context
            enhanced_result = {
                "scenario_result": result.__dict__ if hasattr(result, '__dict__') else result,
                "macro_context": {
                    "current_regime": macro_state["regime"],
                    "regime_probability": macro_state.get("regime_probability", {}),
                    "stdc_phase": macro_state["stdc_phase"],
                    "ltdc_phase": macro_state["ltdc_phase"],
                    "empire_phase": macro_state["empire_phase"],
                    "internal_order_stage": macro_state["internal_order_stage"],
                    "risk_level": macro_state["risk_level"]
                },
                "adjustments_applied": {
                    "original_probability": base_shock.probability,
                    "adjusted_probability": adjusted_shock.probability,
                    "probability_change": f"{(adjusted_shock.probability / base_shock.probability - 1) * 100:.1f}%",
                    "severity_change": self._calculate_severity_change(base_shock, adjusted_shock),
                    "regime_factor": macro_state["regime"],
                    "cycle_factors": {
                        "ltdc": macro_state["ltdc_phase"],
                        "empire": macro_state["empire_phase"]
                    }
                },
                "enhanced_insights": self._generate_insights(
                    result, 
                    macro_state, 
                    adjusted_shock
                )
            }
            
            return enhanced_result
            
        finally:
            # Restore original shock
            self.scenario_service.scenarios[shock_type] = original_shock
    
    def _calculate_severity_change(self, base_shock: Shock, adjusted_shock: Shock) -> str:
        """Calculate how much severity changed."""
        base_magnitude = abs(base_shock.equity_pct or 0) + abs(base_shock.credit_spread_bps or 0) / 10000
        adj_magnitude = abs(adjusted_shock.equity_pct or 0) + abs(adjusted_shock.credit_spread_bps or 0) / 10000
        
        if base_magnitude > 0:
            change = (adj_magnitude / base_magnitude - 1) * 100
            return f"{change:+.1f}%"
        return "0%"
    
    def _generate_insights(
        self,
        result: ScenarioResult,
        macro_state: Dict,
        adjusted_shock: Shock
    ) -> List[str]:
        """Generate contextual insights based on scenario results and macro state."""
        insights = []
        
        # Regime-specific insights
        regime = macro_state["regime"]
        if regime == Regime.LATE_EXPANSION:
            insights.append(
                "⚠️ Late Expansion regime significantly increases crash probability. "
                "Consider defensive positioning."
            )
        elif regime == Regime.DEEP_CONTRACTION:
            insights.append(
                "🔴 Recession regime amplifies downside risks. "
                "Flight to quality likely."
            )
        elif regime == Regime.EARLY_EXPANSION:
            insights.append(
                "🟢 Early Recovery regime favors risk-on scenarios. "
                "Consider increasing equity exposure."
            )
        
        # LTDC insights
        ltdc_phase = macro_state["ltdc_phase"]
        if ltdc_phase == "BUBBLE":
            insights.append(
                "🎈 Long-Term Debt Cycle in Bubble phase. "
                "Correlations will spike in a crisis - diversification may fail."
            )
        elif ltdc_phase == "TOP":
            insights.append(
                "📊 LTDC at Top. Historical analogues: 1929, 2007. "
                "Deleveraging event probability elevated."
            )
        
        # Empire cycle insights
        empire_phase = macro_state["empire_phase"]
        if empire_phase == "DECLINE":
            insights.append(
                "🏛️ Empire in Decline phase. "
                "Structural headwinds and currency debasement risks rising."
            )
        
        # Internal order insights
        internal_stage = macro_state["internal_order_stage"]
        if internal_stage >= 5:
            insights.append(
                f"⚡ Internal Order Stage {internal_stage}: High social instability. "
                "Expect increased volatility and policy uncertainty."
            )
        
        # Impact-based insights
        if hasattr(result, 'total_delta_pl_pct'):
            impact_pct = result.total_delta_pl_pct
            if impact_pct < -0.15:
                insights.append(
                    f"💥 Severe portfolio impact ({impact_pct:.1%}). "
                    "Urgent hedging recommended."
                )
            elif impact_pct < -0.05:
                insights.append(
                    f"📉 Moderate portfolio impact ({impact_pct:.1%}). "
                    "Consider partial hedging."
                )
        
        # Probability insights
        if adjusted_shock.probability > 0.3:
            insights.append(
                f"🎯 High scenario probability ({adjusted_shock.probability:.1%}) "
                "given current macro conditions."
            )
        
        return insights
    
    async def get_regime_weighted_scenarios(
        self,
        portfolio_id: str,
        pack_id: str
    ) -> List[Dict]:
        """
        Get all scenarios ranked by regime-adjusted probability.
        
        This helps users focus on the most likely risks given current conditions.
        """
        
        # Get current macro state
        macro_state = await self.get_current_macro_state()
        
        scenarios_ranked = []
        
        for shock_type in ShockType:
            base_shock = SCENARIO_LIBRARY.get(shock_type)
            if not base_shock:
                continue
            
            # Adjust for regime
            adjusted_shock = self.adjust_shock_for_regime(base_shock, macro_state)
            
            scenarios_ranked.append({
                "shock_type": shock_type.value,
                "name": adjusted_shock.name,
                "description": adjusted_shock.description,
                "base_probability": base_shock.probability,
                "adjusted_probability": adjusted_shock.probability,
                "severity": adjusted_shock.severity,
                "regime_factor": macro_state["regime"],
                "relevance_score": adjusted_shock.probability * (
                    2.0 if adjusted_shock.severity == "high" else
                    3.0 if adjusted_shock.severity == "extreme" else
                    1.0
                )
            })
        
        # Sort by relevance score (probability × severity)
        scenarios_ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Add ranking and insights
        for i, scenario in enumerate(scenarios_ranked, 1):
            scenario["rank"] = i
            scenario["priority"] = (
                "CRITICAL" if scenario["relevance_score"] > 0.3 else
                "HIGH" if scenario["relevance_score"] > 0.15 else
                "MEDIUM" if scenario["relevance_score"] > 0.05 else
                "LOW"
            )
        
        return scenarios_ranked
    
    async def suggest_regime_appropriate_hedges(
        self,
        portfolio_id: str,
        pack_id: str
    ) -> Dict[str, List[HedgeRecommendation]]:
        """
        Suggest hedges appropriate for current macro regime.
        
        Different regimes require different hedging strategies.
        """
        
        macro_state = await self.get_current_macro_state()
        regime = macro_state["regime"]
        
        hedges_by_priority = {
            "immediate": [],
            "recommended": [],
            "consider": []
        }
        
        # Get top risks for this regime
        ranked_scenarios = await self.get_regime_weighted_scenarios(portfolio_id, pack_id)
        top_risks = ranked_scenarios[:3]  # Top 3 risks
        
        # Generate hedges for each top risk
        for risk in top_risks:
            shock_type = ShockType(risk["shock_type"])
            
            # Run scenario to identify vulnerable positions
            result = await self.scenario_service.apply_scenario(
                portfolio_id, shock_type, pack_id
            )
            
            if result.losers:
                hedge_recs = await self.scenario_service.suggest_hedges(
                    result.losers, shock_type
                )
                
                # Categorize by priority based on probability
                if risk["adjusted_probability"] > 0.3:
                    hedges_by_priority["immediate"].extend(hedge_recs)
                elif risk["adjusted_probability"] > 0.15:
                    hedges_by_priority["recommended"].extend(hedge_recs)
                else:
                    hedges_by_priority["consider"].extend(hedge_recs)
        
        # Add regime-specific strategic hedges
        if regime == Regime.LATE_EXPANSION:
            hedges_by_priority["immediate"].append(
                HedgeRecommendation(
                    hedge_type="Volatility Protection",
                    rationale="VIX calls crucial in late expansion - correlations spike in crashes",
                    instruments=["VXX", "VIXY", "VIX calls"],
                    notional=Decimal("10000")
                )
            )
            hedges_by_priority["recommended"].append(
                HedgeRecommendation(
                    hedge_type="Quality Rotation",
                    rationale="Rotate from growth to quality factors before downturn",
                    instruments=["QUAL", "USMV", "SPLV"]
                )
            )
            
        elif regime == Regime.DEEP_CONTRACTION:
            hedges_by_priority["immediate"].append(
                HedgeRecommendation(
                    hedge_type="Long Duration Treasuries",
                    rationale="Fed will cut aggressively - long bonds outperform",
                    instruments=["TLT", "EDV", "ZROZ"],
                    notional=Decimal("20000")
                )
            )
            hedges_by_priority["immediate"].append(
                HedgeRecommendation(
                    hedge_type="Credit Protection",
                    rationale="Credit spreads blow out in recession",
                    instruments=["HYG puts", "LQD puts", "CDX"]
                )
            )
            
        # LTDC-specific hedges
        ltdc_phase = macro_state["ltdc_phase"]
        if ltdc_phase in ["BUBBLE", "TOP"]:
            hedges_by_priority["immediate"].append(
                HedgeRecommendation(
                    hedge_type="Tail Risk Protection",
                    rationale=f"LTDC {ltdc_phase} phase - fat tail events likely",
                    instruments=["SPY puts (20% OTM)", "Tail risk funds"],
                    notional=Decimal("5000")
                )
            )
        
        return hedges_by_priority
    
    async def generate_comprehensive_risk_report(
        self,
        portfolio_id: str,
        pack_id: str
    ) -> Dict:
        """
        Generate a comprehensive risk report combining scenarios and macro analysis.
        
        This is the crown jewel - everything integrated into one actionable report.
        """
        
        # Get macro state
        macro_state = await self.get_current_macro_state()
        
        # Get ranked scenarios
        ranked_scenarios = await self.get_regime_weighted_scenarios(portfolio_id, pack_id)
        
        # Run top 3 scenarios
        scenario_results = []
        for scenario in ranked_scenarios[:3]:
            shock_type = ShockType(scenario["shock_type"])
            result = await self.apply_macro_aware_scenario(
                portfolio_id, shock_type, pack_id
            )
            scenario_results.append(result)
        
        # Get hedge recommendations
        hedges = await self.suggest_regime_appropriate_hedges(portfolio_id, pack_id)
        
        # Compile comprehensive report
        report = {
            "report_date": datetime.now().isoformat(),
            "executive_summary": self._generate_executive_summary(
                macro_state, ranked_scenarios, scenario_results
            ),
            "macro_assessment": {
                "current_regime": macro_state["regime"],
                "regime_confidence": max(macro_state.get("regime_probability", {}).values(), default=0),
                "cycle_positions": {
                    "short_term_debt": macro_state["stdc_phase"],
                    "long_term_debt": macro_state["ltdc_phase"],
                    "empire": macro_state["empire_phase"],
                    "internal_order": f"Stage {macro_state['internal_order_stage']}"
                },
                "risk_level": macro_state["risk_level"],
                "key_indicators": macro_state.get("indicators", {})
            },
            "top_risks": [
                {
                    "rank": s["rank"],
                    "scenario": s["name"],
                    "probability": f"{s['adjusted_probability']:.1%}",
                    "impact": self._get_scenario_impact(s, scenario_results),
                    "priority": s["priority"]
                }
                for s in ranked_scenarios[:5]
            ],
            "scenario_analysis": scenario_results,
            "hedging_recommendations": hedges,
            "action_items": self._generate_action_items(
                macro_state, ranked_scenarios, hedges
            ),
            "historical_context": self._get_historical_analogues(macro_state)
        }
        
        return report
    
    def _generate_executive_summary(
        self,
        macro_state: Dict,
        ranked_scenarios: List[Dict],
        scenario_results: List[Dict]
    ) -> str:
        """Generate executive summary for risk report."""
        
        regime = macro_state["regime"]
        top_risk = ranked_scenarios[0] if ranked_scenarios else None
        
        summary = f"""
        PORTFOLIO RISK ASSESSMENT - {datetime.now().strftime('%Y-%m-%d')}
        
        MACRO ENVIRONMENT: {regime}
        The portfolio operates in a {regime} regime with {macro_state['risk_level']} risk level.
        
        KEY FINDING: 
        """
        
        if regime == Regime.LATE_EXPANSION:
            summary += """
        Late cycle dynamics create elevated crash risk. Historical patterns suggest 
        3x normal probability of significant correction. Defensive positioning recommended.
        """
        elif regime == Regime.DEEP_CONTRACTION:
            summary += """
        Recessionary conditions confirmed. Credit stress and equity weakness expected
        to persist. Flight to quality underway. Duration and quality factors outperform.
        """
        else:
            summary += f"""
        Current conditions suggest {top_risk['name'] if top_risk else 'moderate risk'} 
        as the primary concern with {top_risk['adjusted_probability']:.1%} probability.
        """
        
        # Add LTDC warning if applicable
        if macro_state["ltdc_phase"] in ["BUBBLE", "TOP"]:
            summary += f"""
        
        ⚠️ CRITICAL WARNING: Long-term debt cycle in {macro_state['ltdc_phase']} phase.
        Historical precedents (1929, 2007) suggest extreme caution warranted.
        """
        
        return summary.strip()
    
    def _get_scenario_impact(
        self,
        scenario: Dict,
        results: List[Dict]
    ) -> str:
        """Extract impact for a specific scenario from results."""
        for result in results:
            if result.get("scenario_result", {}).get("shock_type") == scenario["shock_type"]:
                impact = result["scenario_result"].get("total_delta_pl_pct", 0)
                return f"{impact:.1%}"
        return "N/A"
    
    def _generate_action_items(
        self,
        macro_state: Dict,
        ranked_scenarios: List[Dict],
        hedges: Dict
    ) -> List[str]:
        """Generate prioritized action items."""
        
        actions = []
        
        # Immediate actions based on regime
        if macro_state["regime"] == Regime.LATE_EXPANSION:
            actions.append("1. IMMEDIATE: Reduce equity allocation by 20%")
            actions.append("2. IMMEDIATE: Add volatility protection (VIX calls)")
            actions.append("3. THIS WEEK: Rotate from growth to quality factors")
            
        elif macro_state["regime"] == Regime.DEEP_CONTRACTION:
            actions.append("1. IMMEDIATE: Increase duration (buy TLT/EDV)")
            actions.append("2. IMMEDIATE: Exit high-yield credit positions")
            actions.append("3. THIS WEEK: Add defensive sectors (XLU, XLP)")
        
        # Add hedge implementations
        if hedges.get("immediate"):
            actions.append(
                f"4. IMPLEMENT HEDGES: {', '.join(h.hedge_type for h in hedges['immediate'][:2])}"
            )
        
        # LTDC-specific actions
        if macro_state["ltdc_phase"] == "BUBBLE":
            actions.append("5. CRITICAL: Implement tail risk protection (far OTM puts)")
        
        return actions
    
    def _get_historical_analogues(self, macro_state: Dict) -> List[str]:
        """Find historical periods with similar macro configurations using all 4 Dalio cycles."""
        
        analogues = []
        
        regime = macro_state["regime"]
        stdc = macro_state.get("stdc_phase", "UNKNOWN")
        ltdc = macro_state["ltdc_phase"]
        empire = macro_state.get("empire_phase", "UNKNOWN")
        internal = macro_state.get("internal_phase", "STABLE")
        
        # Comprehensive historical database with market outcomes
        historical_db = {
            # Perfect storms (all cycles negative)
            (Regime.DEEP_CONTRACTION, "RECESSION", "DELEVERAGING", "DECLINING"): [
                "1929-1933: Great Depression | All 4 cycles negative | S&P -89%, 25% unemployment",
                "2008-2009: Global Financial Crisis | STDC/LTDC double stress | S&P -57%, credit freeze",
                "1973-1974: Oil crisis + stagflation | Empire challenged | S&P -48%, inflation 12%+"
            ],
            
            # Bubble configurations
            (Regime.LATE_EXPANSION, "EXPANSION", "BUBBLE", "DOMINANT"): [
                "1929 Q2-Q3: Roaring Twenties peak | LTDC bubble, empire strong | Crash -89% followed",
                "1999-2000: Dot-com bubble | Tech revolution, US hegemony | Nasdaq -78% crash",
                "2007 Q1-Q2: Housing bubble | Credit excess pre-GFC | S&P -57% crash coming",
                "1989 Japan: Asset bubble peak | Real estate + stocks | Nikkei -82%, Lost Decades"
            ],
            
            # Recovery sweet spots
            (Regime.EARLY_EXPANSION, "RECOVERY", "STABLE", "DOMINANT"): [
                "2009 Q2-Q4: Post-GFC recovery | QE driven | S&P +26% year, +400% decade",
                "2020 Q3-Q4: Post-COVID rebound | Fiscal + monetary | +68% from lows",
                "1933-1937: New Deal recovery | Post-Depression | +300% rally",
                "1982-1984: Volcker recovery | Inflation defeated | New secular bull"
            ],
            
            # Goldilocks periods
            (Regime.MID_EXPANSION, "MID_CYCLE", "STABLE", "DOMINANT"): [
                "1994-1996: Soft landing | Goldilocks economy | Steady 20%+ annual gains",
                "2004-2005: Mid-cycle pause | Measured hikes | Continued growth",
                "2016-2017: Global synchronized growth | All economies expanding | Low vol",
                "1964-1965: Great Society | Strong growth, low inflation | S&P +13% annually"
            ]
        }
        
        # Find exact matches
        current_key = (regime, stdc, ltdc, empire)
        for pattern_key, pattern_analogues in historical_db.items():
            if current_key == pattern_key:
                analogues.extend(pattern_analogues[:3])  # Top 3 matches
                break
        
        # If no exact match, find partial matches (3/4 cycles matching)
        if not analogues:
            matches = []
            for pattern_key, pattern_analogues in historical_db.items():
                score = 0
                if regime == pattern_key[0]: score += 1
                if stdc == pattern_key[1]: score += 1
                if ltdc == pattern_key[2]: score += 1
                if empire == pattern_key[3]: score += 1
                
                if score >= 3:
                    matches.append((score, pattern_analogues[0]))
            
            # Sort by match quality
            matches.sort(reverse=True)
            for score, analogue in matches[:3]:
                analogues.append(f"[{score}/4 match] {analogue}")
        
        # Add critical warnings for dangerous configurations
        danger_configs = []
        
        if ltdc == "BUBBLE" and regime == Regime.LATE_EXPANSION:
            danger_configs.append("⚠️ CRITICAL: Late-cycle bubble = Major crash risk (historical: -40% to -89%)")
            
        if ltdc == "DELEVERAGING" and stdc == "RECESSION":
            danger_configs.append("⚠️ CRITICAL: Double-cycle contraction = Extended bear market (2-4 years typical)")
            
        if empire == "DECLINING" and internal == "HIGH_CONFLICT":
            danger_configs.append("⚠️ CRITICAL: Empire decline + internal conflict = Extreme volatility & capital flight")
            
        if stdc == "RECESSION" and regime == Regime.DEEP_CONTRACTION:
            danger_configs.append("⚠️ WARNING: Recession confirmed = Average -35% drawdown historically")
        
        # Prepend warnings
        if danger_configs:
            analogues = danger_configs + analogues
        
        return analogues if analogues else [
            f"Current configuration ({regime.value}, STDC:{stdc}, LTDC:{ltdc}) has no strong historical precedent",
            "Heightened uncertainty - consider defensive positioning"
        ]
    
    async def analyze_scenario_impact(
        self, 
        shock_type: str,
        portfolio_value: float,
        portfolio_holdings: List[Dict] = None
    ) -> Dict:
        """
        Analyze scenario impact on portfolio with macro-aware adjustments.
        
        This is the main entry point for API calls.
        
        Args:
            shock_type: String identifier for the shock (e.g., "MARKET_CRASH")
            portfolio_value: Total portfolio value in base currency
            portfolio_holdings: List of holdings (optional)
            
        Returns:
            Comprehensive scenario analysis with macro context
        """
        # Map string shock types to ShockType enum
        shock_mapping = {
            "MARKET_CRASH": ShockType.EQUITY_SELLOFF,
            "INTEREST_RATE_HIKE": ShockType.RATES_UP,
            "HIGH_INFLATION": ShockType.CPI_SURPRISE,
            "TECH_CRASH": ShockType.EQUITY_SELLOFF,  # Tech-focused equity selloff
            "ENERGY_CRISIS": ShockType.CPI_SURPRISE,  # Energy drives inflation
            "CREDIT_CRUNCH": ShockType.CREDIT_SPREAD_WIDENING,
            "GEOPOLITICAL_CONFLICT": ShockType.USD_UP,  # Flight to safety
            "CURRENCY_CRISIS": ShockType.USD_DOWN,
            "RECOVERY_RALLY": ShockType.EQUITY_RALLY
        }
        
        # Get the ShockType enum value
        mapped_shock = shock_mapping.get(shock_type, ShockType.EQUITY_SELLOFF)
        
        # Get current macro state
        try:
            macro_state = await self._get_macro_state()
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - re-raise to surface bugs immediately
            logger.error(f"Programming error getting macro state: {e}", exc_info=True)
            raise
        except Exception as e:
            # Service/database errors - use defaults (graceful degradation)
            logger.warning(f"Failed to get macro state: {e}, using defaults")
            macro_state = {
                "regime": Regime.MID_EXPANSION,
                "stdc_phase": "MID_CYCLE",
                "ltdc_phase": "STABLE",
                "empire_phase": "DOMINANT",
                "internal_phase": "STABLE"
            }
        
        # Get base scenario from parent service
        base_scenario = self.scenario_service._build_scenario(mapped_shock)
        
        # Apply regime adjustments
        regime = macro_state.get("regime", Regime.MID_EXPANSION)
        probability_multiplier = 1.0
        severity_multiplier = 1.0
        reasoning_parts = []
        
        # Check for regime-specific adjustments
        if regime in REGIME_ADJUSTMENTS:
            if mapped_shock in REGIME_ADJUSTMENTS[regime]:
                adjustment = REGIME_ADJUSTMENTS[regime][mapped_shock]
                probability_multiplier = adjustment.probability_multiplier
                severity_multiplier = adjustment.severity_multiplier
                reasoning_parts.append(adjustment.reasoning or "")
        
        # Apply cycle-based modifiers
        stdc_phase = macro_state.get("stdc_phase", "MID_CYCLE")
        ltdc_phase = macro_state.get("ltdc_phase", "STABLE")
        
        # LTDC modifiers
        if ltdc_phase == "BUBBLE":
            if mapped_shock in [ShockType.EQUITY_SELLOFF, ShockType.CREDIT_SPREAD_WIDENING]:
                severity_multiplier *= 1.5
                reasoning_parts.append("LTDC bubble phase amplifies downside risks")
        elif ltdc_phase == "DELEVERAGING":
            if mapped_shock == ShockType.EQUITY_RALLY:
                probability_multiplier *= 0.5
                reasoning_parts.append("Deleveraging phase limits upside potential")
                
        # Calculate base impact
        base_impact = base_scenario.severity * severity_multiplier
        
        # Calculate portfolio impact
        portfolio_impact = portfolio_value * (base_impact / 100)
        
        # Build comprehensive response
        result = {
            "scenario_name": f"{shock_type} Scenario",
            "description": base_scenario.description,
            "macro_context": {
                "current_regime": str(regime),
                "stdc_phase": stdc_phase,
                "ltdc_phase": ltdc_phase,
                "regime_influence": " ".join(reasoning_parts) if reasoning_parts else "Neutral regime impact"
            },
            "impact_analysis": {
                "base_impact_percent": round(base_impact, 2),
                "portfolio_impact_amount": round(portfolio_impact, 2),
                "adjusted_probability": round(base_scenario.probability * probability_multiplier, 1),
                "confidence_level": 75 if regime == Regime.MID_EXPANSION else 85
            },
            "risk_metrics": {
                "var_95": round(portfolio_impact * 0.7, 2),
                "cvar_95": round(portfolio_impact * 0.85, 2),
                "max_drawdown": round(base_impact * 1.2, 2)
            },
            "recommendations": self._generate_recommendations(
                shock_type, regime, stdc_phase, ltdc_phase
            ),
            "historical_analogues": self._get_historical_analogues(macro_state),
            "hedge_suggestions": self._generate_hedge_suggestions(
                shock_type, regime, portfolio_value
            )
        }
        
        return result
    
    def _generate_recommendations(
        self, shock_type: str, regime: Regime, stdc_phase: str, ltdc_phase: str
    ) -> List[str]:
        """Generate regime-aware recommendations."""
        recommendations = []
        
        if shock_type == "MARKET_CRASH":
            if regime == Regime.LATE_EXPANSION:
                recommendations.extend([
                    "Reduce equity exposure - late cycle crash risks elevated",
                    "Increase allocation to defensive sectors (utilities, consumer staples)",
                    "Consider put options or VIX calls for downside protection"
                ])
            elif regime == Regime.DEEP_CONTRACTION:
                recommendations.extend([
                    "Maintain dry powder for opportunistic buying",
                    "Focus on quality names with strong balance sheets",
                    "Consider dollar-cost averaging strategy"
                ])
        
        elif shock_type == "RECOVERY_RALLY":
            if regime == Regime.EARLY_EXPANSION:
                recommendations.extend([
                    "Increase equity exposure, particularly cyclicals",
                    "Rotate into small-caps and emerging markets",
                    "Consider leveraged positions with risk controls"
                ])
        
        # Add LTDC-specific recommendations
        if ltdc_phase == "BUBBLE":
            recommendations.append("⚠️ LTDC bubble detected - prioritize capital preservation")
        elif ltdc_phase == "DELEVERAGING":
            recommendations.append("Focus on income generation and safe havens during deleveraging")
            
        return recommendations if recommendations else ["Monitor market conditions closely"]
    
    def _generate_hedge_suggestions(
        self, shock_type: str, regime: Regime, portfolio_value: float
    ) -> List[Dict]:
        """Generate specific hedge suggestions based on scenario and regime."""
        hedges = []
        hedge_size = portfolio_value * 0.1  # 10% hedge budget
        
        if shock_type in ["MARKET_CRASH", "TECH_CRASH"]:
            hedges.append({
                "instrument": "SPY Put Options",
                "size": round(hedge_size * 0.5, 2),
                "rationale": "Direct downside protection for equity exposure"
            })
            hedges.append({
                "instrument": "VIX Calls",
                "size": round(hedge_size * 0.3, 2),
                "rationale": "Volatility hedge benefits from market stress"
            })
            
        elif shock_type == "INTEREST_RATE_HIKE":
            hedges.append({
                "instrument": "TLT Puts",
                "size": round(hedge_size * 0.4, 2),
                "rationale": "Profit from falling bond prices as rates rise"
            })
            hedges.append({
                "instrument": "Floating Rate Notes",
                "size": round(hedge_size * 0.6, 2),
                "rationale": "Income increases with rising rates"
            })
            
        elif shock_type == "HIGH_INFLATION":
            hedges.append({
                "instrument": "TIPS (Inflation-Protected Securities)",
                "size": round(hedge_size * 0.5, 2),
                "rationale": "Direct inflation protection"
            })
            hedges.append({
                "instrument": "Commodity ETFs (DJP, DBA)",
                "size": round(hedge_size * 0.5, 2),
                "rationale": "Commodities typically outperform during inflation"
            })
            
        return hedges


# Singleton instance for easy access
_macro_aware_service = None

def get_macro_aware_scenario_service(use_db: bool = True) -> MacroAwareScenarioService:
    """Get or create singleton instance of MacroAwareScenarioService."""
    global _macro_aware_service
    if _macro_aware_service is None:
        _macro_aware_service = MacroAwareScenarioService(use_db=use_db)
    return _macro_aware_service