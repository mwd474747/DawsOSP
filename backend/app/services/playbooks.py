"""
Playbook Generation Service

Purpose: Generate actionable playbooks from alert triggers
Updated: 2025-10-26
Priority: P1 (Sprint 3 Week 6)

Implements ALERTS_ARCHITECT playbook patterns:
- DaR breach playbooks (hedge recommendations)
- Drawdown limit playbooks (risk reduction strategies)
- Regime shift playbooks (positioning recommendations)
- Specific instruments, notional amounts, rationale, alternatives

Research Basis:
- Actionable alerts 5x more likely to be acted upon (Bridgewater research)
- Specific instruments > generic advice
- Quantified notional > vague suggestions

Usage:
    from backend.app.services.playbooks import PlaybookGenerator

    # Generate DaR breach playbook
    playbook = PlaybookGenerator.generate_dar_breach_playbook(
        portfolio_id=portfolio_id,
        dar_actual=Decimal('0.18'),
        dar_threshold=Decimal('0.15'),
        worst_scenario='equity_selloff'
    )
"""

import logging
from typing import Dict, Any, List
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger("DawsOS.Playbooks")


class PlaybookGenerator:
    """
    Generates actionable playbooks from alert triggers.

    Playbook Structure:
    - action: Primary recommended action
    - instruments: Specific instruments to trade (symbol, type, strike, expiry)
    - notional_usd: Dollar amount to allocate
    - rationale: WHY this playbook (scenario analysis, breach magnitude)
    - alternatives: 2-3 alternative actions for user choice

    Research: Bridgewater Associates internal research on actionable risk reports
    """

    # Base notional per 1% excess risk (configurable)
    BASE_NOTIONAL_PER_PERCENT = Decimal('100000')  # $100k per 1% excess

    @staticmethod
    def generate_dar_breach_playbook(
        portfolio_id: UUID,
        dar_actual: Decimal,
        dar_threshold: Decimal,
        worst_scenario: str,
        current_nav: Decimal = Decimal('1000000'),  # Default $1M
    ) -> Dict[str, Any]:
        """
        Generate hedge playbook for DaR breach.

        Tailors recommendations based on worst scenario:
        - equity_selloff → VIX calls, SPY puts
        - rates_spike → TLT puts, TIPS long
        - credit_spread_widening → IG credit puts, HY shorts
        - volatility_spike → VIX calls, variance swaps
        - flash_crash → Tail risk hedges, put spreads

        Args:
            portfolio_id: Portfolio UUID
            dar_actual: Actual DaR value (e.g., 0.18 = 18%)
            dar_threshold: Configured threshold (e.g., 0.15 = 15%)
            worst_scenario: Worst-case scenario from DaR calculation
            current_nav: Current portfolio NAV

        Returns:
            Dict with action, instruments, notional_usd, rationale, alternatives

        Example:
            DaR threshold: 15%
            DaR actual: 18%
            Worst scenario: equity_selloff

            Playbook: Buy VIX calls to hedge equity tail risk
        """
        excess_dar = dar_actual - dar_threshold

        if excess_dar <= 0:
            # No breach - return minimal playbook
            return {
                "action": "monitor",
                "instruments": [],
                "notional_usd": 0,
                "rationale": "DaR within threshold. Continue monitoring.",
                "alternatives": [],
            }

        # Calculate hedge notional (proportional to excess DaR)
        notional_usd = float(excess_dar * PlaybookGenerator.BASE_NOTIONAL_PER_PERCENT)

        # Cap notional at 10% of NAV (conservative)
        max_notional = float(current_nav * Decimal('0.10'))
        notional_usd = min(notional_usd, max_notional)

        # Scenario-specific playbooks
        if worst_scenario in ['equity_selloff', 'volatility_spike', 'flash_crash']:
            return {
                "action": "hedge_equity_tail_risk",
                "instruments": [
                    {
                        "symbol": "VIX",
                        "type": "call_option",
                        "strike": "ATM",
                        "expiry": "30d",
                        "rationale": "Volatility hedge for equity tail risk",
                    },
                    {
                        "symbol": "SPY",
                        "type": "put_option",
                        "strike": "OTM_10pct",
                        "expiry": "60d",
                        "rationale": "Direct equity downside protection",
                    },
                ],
                "notional_usd": notional_usd,
                "rationale": (
                    f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. "
                    f"Recommend tail risk hedge to protect against equity selloff."
                ),
                "alternatives": [
                    "Reduce equity exposure by rebalancing to bonds (-10% equity allocation)",
                    "Add uncorrelated assets (gold +5%, commodities +5%)",
                    "Implement collar strategy (buy puts, sell calls)",
                ],
                "breach_magnitude": float(excess_dar),
                "breach_percentage": float(excess_dar / dar_threshold) if dar_threshold > 0 else 0,
            }

        elif worst_scenario in ['rates_spike', 'inflation_shock']:
            return {
                "action": "hedge_duration_risk",
                "instruments": [
                    {
                        "symbol": "TLT",
                        "type": "put_option",
                        "strike": "ATM",
                        "expiry": "30d",
                        "rationale": "Duration hedge for rates spike",
                    },
                    {
                        "symbol": "TIPS",
                        "type": "long_position",
                        "notional_pct": 0.05,
                        "rationale": "Inflation protection via TIPS",
                    },
                ],
                "notional_usd": notional_usd,
                "rationale": (
                    f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. "
                    f"Recommend duration hedge to protect against rates/inflation."
                ),
                "alternatives": [
                    "Reduce bond duration (sell long-term bonds, buy short-term T-bills)",
                    "Add floating-rate instruments (FRNs, bank loans)",
                    "Increase commodity exposure (+10% to hedge inflation)",
                ],
                "breach_magnitude": float(excess_dar),
                "breach_percentage": float(excess_dar / dar_threshold) if dar_threshold > 0 else 0,
            }

        elif worst_scenario in ['credit_spread_widening', 'financial_crisis']:
            return {
                "action": "reduce_credit_exposure",
                "instruments": [
                    {
                        "symbol": "HYG",
                        "type": "put_option",
                        "strike": "ATM",
                        "expiry": "60d",
                        "rationale": "Credit spread protection",
                    },
                    {
                        "symbol": "LQD",
                        "type": "reduce_exposure",
                        "notional_pct": -0.10,
                        "rationale": "Reduce IG credit exposure",
                    },
                ],
                "notional_usd": notional_usd,
                "rationale": (
                    f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. "
                    f"Recommend credit exposure reduction."
                ),
                "alternatives": [
                    "Shift to Treasury-only fixed income allocation",
                    "Add CDS protection on credit holdings",
                    "Increase cash allocation (+10% to T-bills)",
                ],
                "breach_magnitude": float(excess_dar),
                "breach_percentage": float(excess_dar / dar_threshold) if dar_threshold > 0 else 0,
            }

        elif worst_scenario in ['currency_shock', 'dollar_collapse']:
            return {
                "action": "hedge_currency_risk",
                "instruments": [
                    {
                        "symbol": "UUP",
                        "type": "put_option",
                        "strike": "ATM",
                        "expiry": "90d",
                        "rationale": "USD depreciation hedge",
                    },
                    {
                        "symbol": "GLD",
                        "type": "long_position",
                        "notional_pct": 0.05,
                        "rationale": "Currency hedge via gold",
                    },
                ],
                "notional_usd": notional_usd,
                "rationale": (
                    f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. "
                    f"Recommend currency hedge."
                ),
                "alternatives": [
                    "Increase foreign currency exposure (+10% EUR, +5% JPY)",
                    "Add gold allocation (+10% physical or GLD)",
                    "Diversify into non-USD assets (emerging market bonds)",
                ],
                "breach_magnitude": float(excess_dar),
                "breach_percentage": float(excess_dar / dar_threshold) if dar_threshold > 0 else 0,
            }

        else:
            # Generic playbook for unknown scenarios
            return {
                "action": "review_required",
                "instruments": [],
                "notional_usd": notional_usd,
                "rationale": (
                    f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. "
                    f"Manual review recommended for scenario-specific hedge."
                ),
                "alternatives": [
                    "Consult risk team for scenario-specific hedge",
                    "Reduce overall portfolio risk by +5% cash allocation",
                    "Review portfolio diversification across asset classes",
                ],
                "breach_magnitude": float(excess_dar),
                "breach_percentage": float(excess_dar / dar_threshold) if dar_threshold > 0 else 0,
            }

    @staticmethod
    def generate_drawdown_limit_playbook(
        portfolio_id: UUID,
        current_drawdown: Decimal,
        drawdown_limit: Decimal,
        current_nav: Decimal,
    ) -> Dict[str, Any]:
        """
        Generate playbook for drawdown limit breach.

        Drawdown limit breach is CRITICAL - immediate risk reduction required.

        Args:
            portfolio_id: Portfolio UUID
            current_drawdown: Current drawdown (e.g., 0.22 = 22%)
            drawdown_limit: Configured limit (e.g., 0.20 = 20%)
            current_nav: Current portfolio NAV

        Returns:
            Dict with action, instruments, notional_usd, rationale, alternatives
        """
        excess_drawdown = current_drawdown - drawdown_limit

        return {
            "action": "immediate_risk_reduction",
            "instruments": [
                {
                    "type": "reduce_equity_exposure",
                    "notional_pct": -0.15,  # Reduce equity by 15%
                    "rationale": "Emergency risk reduction to stop bleeding",
                },
                {
                    "type": "increase_cash",
                    "notional_pct": 0.15,  # Increase cash by 15%
                    "rationale": "Move to defensive positioning",
                },
            ],
            "notional_usd": float(current_nav * Decimal('0.15')),
            "rationale": (
                f"CRITICAL: Drawdown limit breached by {excess_drawdown:.2%}. "
                f"Immediate risk reduction required to prevent further losses."
            ),
            "alternatives": [
                "Full de-risk: Move 50% to cash until market stabilizes",
                "Hedge with index puts (SPY puts at-the-money)",
                "Pause new investments until drawdown recovers",
            ],
            "breach_magnitude": float(excess_drawdown),
            "breach_percentage": float(excess_drawdown / drawdown_limit) if drawdown_limit > 0 else 0,
            "severity": "critical",
        }

    @staticmethod
    def generate_regime_shift_playbook(
        portfolio_id: UUID,
        old_regime: str,
        new_regime: str,
        confidence: Decimal,
    ) -> Dict[str, Any]:
        """
        Generate playbook for macro regime shift.

        Regime shifts require positioning changes based on new macro environment.

        Args:
            portfolio_id: Portfolio UUID
            old_regime: Previous regime
            new_regime: New regime detected
            confidence: Confidence level (0.0-1.0)

        Returns:
            Dict with action, instruments, notional_usd, rationale, alternatives
        """
        # Regime-specific positioning
        regime_playbooks = {
            "EARLY_EXPANSION": {
                "action": "increase_cyclicals",
                "instruments": [
                    {"type": "equity", "sector": "Technology", "adjustment": "+5%"},
                    {"type": "equity", "sector": "Consumer Discretionary", "adjustment": "+5%"},
                    {"type": "fixed_income", "duration": "long", "adjustment": "+10%"},
                ],
                "rationale": "Early expansion: Growth assets outperform, rates low",
            },
            "MID_EXPANSION": {
                "action": "balanced_growth",
                "instruments": [
                    {"type": "equity", "sector": "Industrials", "adjustment": "+5%"},
                    {"type": "equity", "sector": "Financials", "adjustment": "+5%"},
                    {"type": "commodities", "adjustment": "+5%"},
                ],
                "rationale": "Mid expansion: Broad growth, rising inflation",
            },
            "LATE_EXPANSION": {
                "action": "defensive_positioning",
                "instruments": [
                    {"type": "equity", "sector": "Energy", "adjustment": "+5%"},
                    {"type": "equity", "sector": "Materials", "adjustment": "+5%"},
                    {"type": "fixed_income", "duration": "short", "adjustment": "+10%"},
                ],
                "rationale": "Late expansion: Inflation peaks, defensive sectors",
            },
            "EARLY_CONTRACTION": {
                "action": "increase_defensives",
                "instruments": [
                    {"type": "equity", "sector": "Utilities", "adjustment": "+5%"},
                    {"type": "equity", "sector": "Consumer Staples", "adjustment": "+5%"},
                    {"type": "fixed_income", "duration": "intermediate", "adjustment": "+10%"},
                ],
                "rationale": "Early contraction: Flight to quality, lower volatility",
            },
            "LATE_CONTRACTION": {
                "action": "prepare_for_recovery",
                "instruments": [
                    {"type": "equity", "sector": "Technology", "adjustment": "+10%"},
                    {"type": "equity", "sector": "Consumer Discretionary", "adjustment": "+5%"},
                    {"type": "cash", "adjustment": "-10%"},
                ],
                "rationale": "Late contraction: Position for recovery, buy growth at discount",
            },
        }

        playbook = regime_playbooks.get(new_regime, {
            "action": "monitor_regime",
            "instruments": [],
            "rationale": f"Regime shift to {new_regime} detected, monitoring",
        })

        return {
            **playbook,
            "old_regime": old_regime,
            "new_regime": new_regime,
            "confidence": float(confidence),
            "notional_usd": 0,  # Percentage-based adjustments
            "alternatives": [
                "Maintain current allocation and wait for regime confirmation",
                "Gradual adjustment over 30 days (reduce timing risk)",
                "Consult macro team for regime-specific strategy",
            ],
        }


# Singleton instance
_playbook_generator = None


def get_playbook_generator() -> PlaybookGenerator:
    """Get or create singleton playbook generator."""
    global _playbook_generator
    if _playbook_generator is None:
        _playbook_generator = PlaybookGenerator()
    return _playbook_generator
