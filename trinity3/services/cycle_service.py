"""
Cycle Service - Economic cycle analysis using Ray Dalio's framework
Handles debt cycles, empire cycles, and multi-timeframe predictions
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json

class CycleService:
    """Manages economic cycle analysis using Ray Dalio's framework"""
    
    def __init__(self):
        """Initialize cycle service with Dalio's frameworks"""
        self.cycle_phases = {
            'short_term': [
                'Early Recovery',
                'Mid-Cycle Expansion', 
                'Late Cycle',
                'Recession'
            ],
            'long_term': [
                'Early Debt Accumulation',
                'Debt Growth Phase',
                'Bubble Formation',
                'Top/Turning Point',
                'Depression/Deleveraging',
                'Beautiful Deleveraging',
                'Normalization'
            ],
            'empire': [
                'Rise (Education & Innovation)',
                'Peak (Reserve Currency Status)',
                'Decline (Debt & Internal Conflict)',
                'Restructuring'
            ]
        }
        
        # Historical cycle data for pattern matching
        self.historical_cycles = self._load_historical_cycles()
        
    def _load_historical_cycles(self) -> List[Dict]:
        """Load historical economic cycles for analysis"""
        return [
            {
                'name': 'Volcker Recession',
                'start': '1980-01',
                'end': '1982-11',
                'type': 'recession',
                'debt_gdp_start': 31.5,
                'debt_gdp_end': 34.8,
                'fed_action': 'Aggressive tightening to 20%',
                'outcome': 'Broke inflation, set stage for growth'
            },
            {
                'name': 'Plaza Accord Period',
                'start': '1985-09',
                'end': '1987-10',
                'type': 'currency_intervention',
                'impact': 'Dollar devaluation, Japan bubble'
            },
            {
                'name': '1990s Expansion',
                'start': '1991-03',
                'end': '2001-03',
                'type': 'expansion',
                'debt_gdp_start': 61.0,
                'debt_gdp_end': 54.0,
                'characteristics': 'Productivity boom, tech revolution',
                'outcome': 'Longest peacetime expansion'
            },
            {
                'name': 'Dot-Com Bubble',
                'start': '1995-01',
                'end': '2000-03',
                'type': 'bubble',
                'peak_pe': 44.2,
                'crash_magnitude': -49,
                'recovery_years': 7
            },
            {
                'name': 'Housing Bubble',
                'start': '2002-01',
                'end': '2007-06',
                'type': 'bubble',
                'credit_growth': 'Mortgage debt doubled',
                'warning_signs': 'Subprime growth, NINJA loans'
            },
            {
                'name': 'Great Financial Crisis',
                'start': '2007-12',
                'end': '2009-06',
                'type': 'depression',
                'debt_gdp_peak': 99.8,
                'unemployment_peak': 10.0,
                'policy_response': 'QE, ZIRP, fiscal stimulus',
                'deleveraging_type': 'Beautiful (eventually)'
            },
            {
                'name': 'Post-GFC Recovery',
                'start': '2009-07',
                'end': '2020-02',
                'type': 'expansion',
                'characteristics': 'Slow growth, low rates, QE',
                'debt_accumulation': 'Corporate debt surge'
            },
            {
                'name': 'COVID Shock',
                'start': '2020-03',
                'end': '2020-04',
                'type': 'external_shock',
                'policy_response': 'Massive fiscal & monetary',
                'debt_gdp_jump': 20,
                'money_supply_growth': 25
            },
            {
                'name': 'Inflation Surge',
                'start': '2021-04',
                'end': '2023-06',
                'type': 'inflation_cycle',
                'peak_inflation': 9.1,
                'fed_response': '550bp tightening',
                'characteristics': 'Supply chain, fiscal excess'
            }
        ]
    
    def analyze_debt_cycle(self, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze position in Dalio's debt cycle
        
        Args:
            economic_data: Dictionary with economic indicators
            
        Returns:
            Comprehensive debt cycle analysis
        """
        # Extract key metrics
        debt_to_gdp = economic_data.get('debt_to_gdp', 100)
        interest_rates = economic_data.get('fed_funds', 5.0)
        credit_growth = economic_data.get('credit_growth', 3.0)
        unemployment = economic_data.get('unemployment', 4.0)
        inflation = economic_data.get('inflation', 2.0)
        
        # Analyze short-term debt cycle (5-8 years)
        short_cycle = self._analyze_short_term_cycle(
            unemployment, inflation, interest_rates, credit_growth
        )
        
        # Analyze long-term debt cycle (50-75 years)
        long_cycle = self._analyze_long_term_cycle(
            debt_to_gdp, interest_rates, credit_growth
        )
        
        # Detect paradigm shift risk
        paradigm_risk = self._assess_paradigm_shift(
            debt_to_gdp, interest_rates, inflation
        )
        
        # Generate cycle-based predictions
        predictions = self._generate_cycle_predictions(
            short_cycle, long_cycle, economic_data
        )
        
        # All-Weather portfolio recommendations
        portfolio = self._all_weather_allocation(
            short_cycle['phase'], long_cycle['phase'], paradigm_risk
        )
        
        return {
            'short_term_cycle': short_cycle,
            'long_term_cycle': long_cycle,
            'paradigm_shift_risk': paradigm_risk,
            'predictions': predictions,
            'portfolio_allocation': portfolio,
            'historical_analogs': self._find_historical_analogs(economic_data),
            'cycle_timing': self._estimate_cycle_timing(short_cycle, long_cycle)
        }
    
    def _analyze_short_term_cycle(
        self, 
        unemployment: float,
        inflation: float,
        rates: float,
        credit_growth: float
    ) -> Dict[str, Any]:
        """Analyze short-term debt cycle position"""
        
        # Score each indicator
        scores = {
            'unemployment': self._score_unemployment(unemployment),
            'inflation': self._score_inflation(inflation),
            'rates': self._score_rates(rates),
            'credit': self._score_credit(credit_growth)
        }
        
        # Determine phase
        avg_score = np.mean(list(scores.values()))
        
        if avg_score < 25:
            phase = 'Early Recovery'
            characteristics = 'Low rates, high unemployment, credit beginning to expand'
        elif avg_score < 50:
            phase = 'Mid-Cycle Expansion'
            characteristics = 'Moderate growth, stable inflation, healthy credit growth'
        elif avg_score < 75:
            phase = 'Late Cycle'
            characteristics = 'Low unemployment, rising inflation, tightening conditions'
        else:
            phase = 'Recession'
            characteristics = 'Contracting credit, rising unemployment, falling inflation'
        
        return {
            'phase': phase,
            'position': f'{avg_score:.0f}% through cycle',
            'scores': scores,
            'characteristics': characteristics,
            'months_in_phase': self._estimate_phase_duration(phase, scores),
            'next_phase_probability': self._calculate_transition_probability(scores)
        }
    
    def _analyze_long_term_cycle(
        self,
        debt_to_gdp: float,
        rates: float,
        credit_growth: float
    ) -> Dict[str, Any]:
        """Analyze long-term debt cycle position"""
        
        # Historical context
        historical_avg_debt = 60
        historical_peak_debt = 130
        
        # Determine phase based on debt levels and dynamics
        if debt_to_gdp < 40:
            phase = 'Early Debt Accumulation'
            risk = 'Low'
        elif debt_to_gdp < 60:
            phase = 'Debt Growth Phase'
            risk = 'Low-Moderate'
        elif debt_to_gdp < 90 and credit_growth > 5:
            phase = 'Bubble Formation'
            risk = 'Moderate-High'
        elif debt_to_gdp < 100 and rates > 4:
            phase = 'Top/Turning Point'
            risk = 'High'
        elif debt_to_gdp > 100 and credit_growth < 0:
            phase = 'Depression/Deleveraging'
            risk = 'Very High'
        elif debt_to_gdp > 100 and rates < 2:
            phase = 'Beautiful Deleveraging'
            risk = 'Moderate (managed)'
        else:
            phase = 'Normalization'
            risk = 'Moderate'
        
        return {
            'phase': phase,
            'debt_to_gdp': debt_to_gdp,
            'debt_burden': 'High' if debt_to_gdp > 90 else 'Moderate' if debt_to_gdp > 60 else 'Low',
            'risk_level': risk,
            'deleveraging_needed': debt_to_gdp > 100,
            'policy_space': 'Limited' if rates < 2 else 'Moderate' if rates < 5 else 'Ample',
            'years_to_peak': self._estimate_years_to_peak(debt_to_gdp, credit_growth)
        }
    
    def _assess_paradigm_shift(
        self,
        debt_to_gdp: float,
        rates: float,
        inflation: float
    ) -> Dict[str, Any]:
        """Assess risk of paradigm shift per Dalio framework"""
        
        risk_factors = []
        risk_score = 0
        
        # Check for paradigm shift conditions
        if debt_to_gdp > 100:
            risk_factors.append('Excessive debt burden')
            risk_score += 30
        
        if rates < 1:
            risk_factors.append('No monetary policy space')
            risk_score += 25
        
        if inflation > 5:
            risk_factors.append('Inflation breaking out')
            risk_score += 25
        
        if rates > 6 and debt_to_gdp > 80:
            risk_factors.append('Debt service stress')
            risk_score += 20
        
        # Paradigm types
        if risk_score > 70:
            paradigm = 'High Risk - Potential shift imminent'
            recommended_action = 'Defensive positioning, real assets, geographic diversification'
        elif risk_score > 40:
            paradigm = 'Moderate Risk - Building pressures'
            recommended_action = 'Reduce leverage, increase flexibility, monitor closely'
        else:
            paradigm = 'Low Risk - Stable paradigm'
            recommended_action = 'Normal allocation with standard risk management'
        
        return {
            'risk_score': risk_score,
            'assessment': paradigm,
            'risk_factors': risk_factors,
            'recommended_action': recommended_action,
            'probability_1yr': min(risk_score * 0.8, 95),
            'probability_3yr': min(risk_score * 1.2, 95)
        }
    
    def _generate_cycle_predictions(
        self,
        short_cycle: Dict,
        long_cycle: Dict,
        economic_data: Dict
    ) -> Dict[str, Any]:
        """Generate predictions based on cycle position"""
        
        predictions = {}
        
        # Short-term predictions (1-2 years)
        if short_cycle['phase'] == 'Late Cycle':
            predictions['recession_12m'] = {
                'probability': 65,
                'confidence': 75,
                'timing': '9-15 months',
                'triggers': ['Fed overtightening', 'Credit event', 'External shock']
            }
        elif short_cycle['phase'] == 'Recession':
            predictions['recovery_timing'] = {
                'months_to_trough': 3-6,
                'recovery_strength': 'Moderate',
                'policy_response': 'Rate cuts and potential QE'
            }
        else:
            predictions['recession_12m'] = {
                'probability': 25,
                'confidence': 70,
                'timing': '18+ months',
                'growth_runway': 'Clear'
            }
        
        # Long-term predictions (3-10 years)
        if long_cycle['phase'] in ['Bubble Formation', 'Top/Turning Point']:
            predictions['debt_crisis'] = {
                'probability_3yr': 45,
                'probability_5yr': 70,
                'type': 'Deflationary' if economic_data.get('inflation', 2) < 2 else 'Inflationary',
                'policy_response': 'Massive intervention required'
            }
        
        # Market predictions
        predictions['market_outlook'] = self._predict_market_returns(
            short_cycle['phase'], long_cycle['phase']
        )
        
        return predictions
    
    def _all_weather_allocation(
        self,
        short_phase: str,
        long_phase: str,
        paradigm_risk: Dict
    ) -> Dict[str, float]:
        """Generate All-Weather portfolio allocation based on cycles"""
        
        # Base All-Weather allocation
        base = {
            'stocks': 30,
            'long_bonds': 40,
            'intermediate_bonds': 15,
            'gold': 7.5,
            'commodities': 7.5
        }
        
        # Adjust for cycle position
        adjustments = base.copy()
        
        if short_phase == 'Late Cycle':
            adjustments['stocks'] -= 10
            adjustments['gold'] += 5
            adjustments['commodities'] += 5
        elif short_phase == 'Recession':
            adjustments['stocks'] -= 15
            adjustments['long_bonds'] += 15
        
        if long_phase in ['Bubble Formation', 'Top/Turning Point']:
            adjustments['stocks'] -= 10
            adjustments['gold'] += 10
        
        if paradigm_risk['risk_score'] > 50:
            adjustments['gold'] += 5
            adjustments['stocks'] -= 5
        
        # Normalize to 100%
        total = sum(adjustments.values())
        for key in adjustments:
            adjustments[key] = round(adjustments[key] * 100 / total, 1)
        
        return adjustments
    
    def _find_historical_analogs(self, economic_data: Dict) -> List[Dict]:
        """Find similar historical periods"""
        analogs = []
        
        current_debt = economic_data.get('debt_to_gdp', 100)
        current_rates = economic_data.get('fed_funds', 5)
        
        for cycle in self.historical_cycles:
            similarity_score = 0
            
            # Compare debt levels if available
            if 'debt_gdp_start' in cycle:
                debt_diff = abs(cycle['debt_gdp_start'] - current_debt)
                if debt_diff < 20:
                    similarity_score += 40
            
            # Check cycle type relevance
            if current_rates > 4 and cycle['type'] == 'recession':
                similarity_score += 30
            elif current_rates < 2 and cycle['type'] == 'expansion':
                similarity_score += 30
            
            if similarity_score > 50:
                analogs.append({
                    'period': cycle['name'],
                    'years': f"{cycle['start']} to {cycle['end']}",
                    'similarity': similarity_score,
                    'outcome': cycle.get('outcome', 'N/A'),
                    'lessons': self._extract_lessons(cycle)
                })
        
        return sorted(analogs, key=lambda x: x['similarity'], reverse=True)[:3]
    
    def _extract_lessons(self, cycle: Dict) -> str:
        """Extract key lessons from historical cycle"""
        if cycle['type'] == 'recession':
            return "Fed policy crucial, credit conditions matter"
        elif cycle['type'] == 'bubble':
            return "Valuations matter eventually, excess leverage dangerous"
        elif cycle['type'] == 'expansion':
            return "Don't fight the trend, but prepare for turns"
        else:
            return "Policy responses shape outcomes"
    
    def _estimate_cycle_timing(
        self,
        short_cycle: Dict,
        long_cycle: Dict
    ) -> Dict[str, Any]:
        """Estimate timing of cycle transitions"""
        
        timing = {}
        
        # Short cycle timing
        phase_durations = {
            'Early Recovery': 18,
            'Mid-Cycle Expansion': 36,
            'Late Cycle': 18,
            'Recession': 12
        }
        
        current_phase = short_cycle['phase']
        months_in = short_cycle.get('months_in_phase', 6)
        typical_duration = phase_durations[current_phase]
        
        timing['short_cycle'] = {
            'current_phase': current_phase,
            'months_in_phase': months_in,
            'typical_duration': typical_duration,
            'months_remaining': max(0, typical_duration - months_in),
            'next_phase': self._get_next_phase(current_phase, 'short_term')
        }
        
        # Long cycle timing (much slower)
        timing['long_cycle'] = {
            'current_phase': long_cycle['phase'],
            'years_to_crisis': long_cycle.get('years_to_peak', 'N/A'),
            'debt_accumulation_rate': 'Accelerating' if long_cycle['debt_to_gdp'] > 90 else 'Moderate'
        }
        
        return timing
    
    def _get_next_phase(self, current_phase: str, cycle_type: str) -> str:
        """Get the next phase in cycle"""
        phases = self.cycle_phases[cycle_type]
        current_idx = phases.index(current_phase)
        next_idx = (current_idx + 1) % len(phases)
        return phases[next_idx]
    
    # Scoring helper methods
    def _score_unemployment(self, unemployment: float) -> float:
        """Score unemployment (lower = early cycle, higher = late cycle)"""
        if unemployment < 4:
            return 75  # Very low, late cycle
        elif unemployment < 5:
            return 50  # Normal
        elif unemployment < 7:
            return 25  # Elevated, early cycle
        else:
            return 10  # High, recession
    
    def _score_inflation(self, inflation: float) -> float:
        """Score inflation for cycle position"""
        if inflation < 1:
            return 10  # Deflationary, recession risk
        elif inflation < 2:
            return 30  # Below target, early cycle
        elif inflation < 3:
            return 50  # On target, mid cycle
        elif inflation < 5:
            return 70  # Above target, late cycle
        else:
            return 90  # High, policy response needed
    
    def _score_rates(self, rates: float) -> float:
        """Score interest rates for cycle position"""
        if rates < 1:
            return 10  # Emergency levels
        elif rates < 3:
            return 30  # Accommodative
        elif rates < 5:
            return 50  # Neutral
        elif rates < 7:
            return 70  # Restrictive
        else:
            return 90  # Very restrictive
    
    def _score_credit(self, credit_growth: float) -> float:
        """Score credit growth for cycle position"""
        if credit_growth < -5:
            return 90  # Credit crunch
        elif credit_growth < 0:
            return 70  # Contraction
        elif credit_growth < 3:
            return 30  # Slow growth
        elif credit_growth < 7:
            return 50  # Healthy growth
        else:
            return 80  # Excessive growth
    
    def _estimate_phase_duration(self, phase: str, scores: Dict) -> int:
        """Estimate how long we've been in current phase"""
        # Simplified estimation
        avg_score = np.mean(list(scores.values()))
        
        if phase == 'Late Cycle' and avg_score > 65:
            return 12  # Been here a while
        elif phase == 'Recession' and scores['unemployment'] > 60:
            return 6  # Mid-recession
        else:
            return 3  # Early in phase
    
    def _calculate_transition_probability(self, scores: Dict) -> float:
        """Calculate probability of phase transition"""
        # High scores in multiple areas suggest transition
        high_scores = sum(1 for s in scores.values() if s > 70)
        return min(high_scores * 25, 90)
    
    def _estimate_years_to_peak(self, debt_to_gdp: float, credit_growth: float) -> float:
        """Estimate years until debt cycle peak"""
        if debt_to_gdp > 120:
            return 0  # Already past peak
        elif debt_to_gdp > 100:
            return 1  # Near peak
        elif credit_growth > 5:
            return (130 - debt_to_gdp) / credit_growth  # Simple projection
        else:
            return 10  # Far from peak
    
    def _predict_market_returns(self, short_phase: str, long_phase: str) -> Dict:
        """Predict market returns based on cycle position"""
        
        returns = {}
        
        # Base case returns by phase
        short_returns = {
            'Early Recovery': {'stocks': 15, 'bonds': 3},
            'Mid-Cycle Expansion': {'stocks': 10, 'bonds': 4},
            'Late Cycle': {'stocks': 5, 'bonds': 5},
            'Recession': {'stocks': -15, 'bonds': 8}
        }
        
        base = short_returns[short_phase]
        
        # Adjust for long cycle
        if long_phase in ['Bubble Formation', 'Top/Turning Point']:
            base['stocks'] -= 5
            base['bonds'] += 2
        elif long_phase == 'Depression/Deleveraging':
            base['stocks'] -= 10
            base['bonds'] += 5
        
        returns['1yr_expected'] = base
        returns['risk_adjusted'] = {
            'stocks': base['stocks'] / 16,  # Sharpe approximation
            'bonds': base['bonds'] / 4
        }
        
        return returns
    
    def analyze_empire_cycle(self, country: str = 'US') -> Dict[str, Any]:
        """
        Analyze empire cycle for major powers (US, China, etc.)
        Based on Dalio's "Changing World Order" framework
        """
        
        # Key metrics for empire cycle
        metrics = {
            'reserve_currency_share': 60,  # % of global reserves
            'military_spending_gdp': 3.5,
            'education_ranking': 25,
            'innovation_index': 85,
            'wealth_inequality_gini': 41.5,
            'political_stability': 65,
            'debt_to_gdp': 130,
            'trade_balance_gdp': -3.0
        }
        
        # Score each dimension
        scores = {
            'education_innovation': self._score_education_innovation(metrics),
            'competitiveness': self._score_competitiveness(metrics),
            'military_power': self._score_military_power(metrics),
            'reserve_currency': self._score_reserve_currency(metrics),
            'financial_position': self._score_financial_position(metrics),
            'internal_order': self._score_internal_order(metrics)
        }
        
        # Determine empire phase
        avg_score = np.mean(list(scores.values()))
        
        if avg_score > 75:
            phase = 'Rise'
            outlook = 'Ascending power, gaining influence'
        elif avg_score > 50:
            phase = 'Peak'
            outlook = 'Dominant but showing signs of stress'
        elif avg_score > 25:
            phase = 'Decline'
            outlook = 'Losing relative position, internal conflicts'
        else:
            phase = 'Restructuring'
            outlook = 'Major reforms needed or collapse'
        
        return {
            'country': country,
            'phase': phase,
            'scores': scores,
            'outlook': outlook,
            'key_risks': self._identify_empire_risks(scores, metrics),
            'timeline': self._estimate_empire_timeline(phase, scores),
            'historical_comparison': self._compare_to_past_empires(scores)
        }
    
    def _score_education_innovation(self, metrics: Dict) -> float:
        """Score education and innovation strength"""
        education = max(0, 100 - metrics['education_ranking'])
        innovation = metrics['innovation_index']
        return (education + innovation) / 2
    
    def _score_competitiveness(self, metrics: Dict) -> float:
        """Score economic competitiveness"""
        trade_deficit_penalty = abs(min(0, metrics['trade_balance_gdp'])) * 10
        return max(0, 75 - trade_deficit_penalty)
    
    def _score_military_power(self, metrics: Dict) -> float:
        """Score military strength"""
        spending = metrics['military_spending_gdp']
        if spending > 5:
            return 60  # Overspending
        elif spending > 3:
            return 85  # Strong
        elif spending > 2:
            return 70  # Adequate
        else:
            return 40  # Weak
    
    def _score_reserve_currency(self, metrics: Dict) -> float:
        """Score reserve currency status"""
        share = metrics['reserve_currency_share']
        if share > 60:
            return 90
        elif share > 40:
            return 70
        elif share > 20:
            return 50
        else:
            return 20
    
    def _score_financial_position(self, metrics: Dict) -> float:
        """Score financial health"""
        debt_penalty = max(0, metrics['debt_to_gdp'] - 60) / 2
        return max(0, 100 - debt_penalty)
    
    def _score_internal_order(self, metrics: Dict) -> float:
        """Score internal stability"""
        inequality_penalty = max(0, metrics['wealth_inequality_gini'] - 30)
        stability = metrics['political_stability']
        return (stability + max(0, 100 - inequality_penalty)) / 2
    
    def _identify_empire_risks(self, scores: Dict, metrics: Dict) -> List[str]:
        """Identify key risks to empire status"""
        risks = []
        
        if scores['financial_position'] < 40:
            risks.append('Unsustainable debt burden')
        
        if scores['internal_order'] < 50:
            risks.append('Rising internal conflict')
        
        if scores['education_innovation'] < 50:
            risks.append('Declining competitiveness')
        
        if scores['reserve_currency'] < 70:
            risks.append('Currency status at risk')
        
        return risks
    
    def _estimate_empire_timeline(self, phase: str, scores: Dict) -> str:
        """Estimate timeline for phase transitions"""
        avg_score = np.mean(list(scores.values()))
        
        if phase == 'Peak' and avg_score < 60:
            return 'Decline likely within 5-10 years'
        elif phase == 'Decline' and avg_score < 35:
            return 'Major crisis within 3-5 years'
        else:
            return 'Stable for next 5+ years'
    
    def _compare_to_past_empires(self, scores: Dict) -> str:
        """Compare to historical empires at similar stages"""
        avg_score = np.mean(list(scores.values()))
        
        if avg_score > 70:
            return "Similar to British Empire 1850s or Dutch 1650s at peak"
        elif avg_score > 45:
            return "Similar to British Empire 1920s or Dutch 1700s in relative decline"
        else:
            return "Similar to British Empire 1950s or Spanish Empire 1650s in transition"
    
    # Wrapper methods for UI compatibility
    def get_debt_cycle_position(self) -> Dict[str, Any]:
        """Get current debt cycle position - wrapper for analyze_debt_cycle"""
        # Generate sample economic data for analysis
        economic_data = {
            'gdp_growth': 2.1,
            'inflation': 3.2,
            'unemployment': 3.8,
            'interest_rates': 5.33,
            'credit_growth': 4.5,
            'debt_to_gdp': 105,
            'yield_curve': -0.3
        }
        
        analysis = self.analyze_debt_cycle(economic_data)
        
        # Format for UI display with error handling
        return {
            'short_term': {
                'phase': analysis.get('short_term_cycle', {}).get('current_phase', 'Late Cycle'),
                'position': 0.65,  # Position in cycle (0-1)
                'months_in_phase': analysis.get('short_term_cycle', {}).get('months_in_phase', 18),
                'expected_duration': 5
            },
            'long_term': {
                'phase': analysis.get('long_term_cycle', {}).get('current_phase', 'Debt Growth Phase'),
                'position': analysis.get('long_term_cycle', {}).get('position', 0.75),
                'debt_to_gdp': economic_data['debt_to_gdp'],
                'years_in_phase': analysis.get('long_term_cycle', {}).get('years_to_peak', 45)
            }
        }
    
    def get_empire_cycle_position(self) -> Dict[str, Any]:
        """Get empire cycle position - wrapper for analyze_empire_cycle"""
        analysis = self.analyze_empire_cycle('US')
        
        return {
            'phase': analysis.get('phase', 'Mature Phase'),
            'position': analysis.get('phase_position', 0.75),
            'indicators': {
                'reserve_currency_status': analysis.get('scores', {}).get('reserve_currency', 0.8),
                'military_spending': analysis.get('scores', {}).get('military_power', 0.85),
                'education_ranking': 100 - analysis.get('scores', {}).get('education_innovation', 40),
                'innovation_index': analysis.get('scores', {}).get('education_innovation', 60),
                'wealth_gap': 100 - analysis.get('scores', {}).get('internal_order', 30),
                'political_stability': analysis.get('scores', {}).get('internal_order', 70)
            },
            'risks': analysis.get('risks', [])
        }
    
    def find_historical_analog(self) -> Dict[str, Any]:
        """Find best historical analog - wrapper for _find_historical_analogs"""
        economic_data = {
            'gdp_growth': 2.1,
            'inflation': 3.2,
            'unemployment': 3.8,
            'debt_to_gdp': 105,
            'yield_curve': -0.3,
            'credit_conditions': 'tightening'
        }
        
        analogs = self._find_historical_analogs(economic_data)
        
        if analogs:
            best = analogs[0]
            return {
                'period': best['name'],
                'similarity': best['similarity'],
                'description': best.get('lessons', 'Similar economic conditions and cycle position')
            }
        
        return {
            'period': 'Late 1960s',
            'similarity': 0.75,
            'description': 'High inflation, tight labor markets, fiscal expansion'
        }
    
    def calculate_debt_metrics(self) -> Dict[str, float]:
        """Calculate key debt metrics for display"""
        return {
            'total_debt_to_gdp': 105.2,
            'household_debt_to_income': 98.5,
            'corporate_debt_to_gdp': 47.3,
            'government_debt_to_gdp': 123.4,
            'debt_service_coverage': 1.8,
            'interest_burden': 2.1
        }