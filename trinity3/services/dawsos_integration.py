"""
DawsOS Integration Service - Bridges Trinity 3.0 with DawsOS v2.0 Agents
Connects the existing analytical capabilities to the Trinity UI
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import numpy as np

# Add dawsos to path for imports
dawsos_path = Path(__file__).parent.parent.parent / 'dawsos'
if str(dawsos_path) not in sys.path:
    sys.path.insert(0, str(dawsos_path))

# Import DawsOS components
from dawsos.capabilities.fred_data import FredDataCapability
from dawsos.agents.financial_analyst import FinancialAnalyst
from dawsos.models.economic_data import EconomicDataResponse, SeriesData


class DawsOSIntegration:
    """Integrates DawsOS v2.0 agents with Trinity 3.0"""
    
    def __init__(self):
        """Initialize DawsOS integration"""
        self.fred_capability = FredDataCapability()
        self.financial_analyst = FinancialAnalyst()
        self._cache = {}
        
    def get_economic_indicators(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetch real economic indicators from FRED
        
        Returns:
            Dict with GDP, CPI, UNRATE, DFF, etc.
        """
        cache_key = 'economic_indicators'
        
        if use_cache and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < 3600:  # 1 hour cache
                return cached_data
        
        try:
            # Fetch from FRED using existing capability
            series_ids = ['GDP', 'CPIAUCSL', 'UNRATE', 'DFF', 'DGS10', 'DGS2', 
                         'DEXUSEU', 'T10Y2Y', 'DFEDTARU']
            
            economic_data = {}
            for series_id in series_ids:
                try:
                    result = self.fred_capability.fetch_single_series(
                        series_id,
                        start_date=(datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                        end_date=datetime.now().strftime('%Y-%m-%d')
                    )
                    if result and result.observations:
                        economic_data[series_id] = {
                            'value': result.latest_value,
                            'date': result.latest_date,
                            'history': [{'date': obs.date, 'value': obs.value} 
                                       for obs in result.observations[-24:]]  # Last 24 periods
                        }
                except Exception as e:
                    print(f"Error fetching {series_id}: {e}")
                    continue
            
            # Cache the results
            self._cache[cache_key] = (economic_data, datetime.now())
            return economic_data
            
        except Exception as e:
            print(f"Error fetching economic indicators: {e}")
            return {}
    
    def calculate_recession_risk(self, economic_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Calculate recession risk using FinancialAnalyst's methods
        
        Returns:
            Dict with recession probability, indicators, and analysis
        """
        if economic_data is None:
            economic_data = self.get_economic_indicators()
        
        # Extract key metrics
        gdp_value = economic_data.get('GDP', {}).get('value', 2.1)
        cpi_value = economic_data.get('CPIAUCSL', {}).get('value', 3.2)
        unemployment = economic_data.get('UNRATE', {}).get('value', 3.8)
        fed_rate = economic_data.get('DFF', {}).get('value', 5.33)
        yield_curve = economic_data.get('T10Y2Y', {}).get('value', 0.5)
        
        # Calculate GDP growth (simplified - should use quarter-over-quarter)
        gdp_history = economic_data.get('GDP', {}).get('history', [])
        if len(gdp_history) >= 2:
            gdp_growth = ((gdp_history[-1]['value'] / gdp_history[-5]['value']) ** 0.25 - 1) * 100
        else:
            gdp_growth = 2.1
        
        # Calculate CPI YoY
        cpi_history = economic_data.get('CPIAUCSL', {}).get('history', [])
        if len(cpi_history) >= 13:
            cpi_yoy = ((cpi_history[-1]['value'] / cpi_history[-13]['value']) - 1) * 100
        else:
            cpi_yoy = 3.2
        
        # Use FinancialAnalyst's regime determination
        regime = self.financial_analyst._determine_economic_regime(
            gdp_qoq=gdp_growth,
            cpi_yoy=cpi_yoy,
            cycle_phase='unknown'
        )
        
        # Calculate recession probability based on indicators
        recession_score = 0
        indicators = []
        
        # GDP growth check
        if gdp_growth < 0:
            recession_score += 40
            indicators.append({'name': 'GDP Growth', 'value': gdp_growth, 'signal': 'negative'})
        elif gdp_growth < 1:
            recession_score += 20
            indicators.append({'name': 'GDP Growth', 'value': gdp_growth, 'signal': 'warning'})
        else:
            indicators.append({'name': 'GDP Growth', 'value': gdp_growth, 'signal': 'positive'})
        
        # Yield curve inversion
        if yield_curve < 0:
            recession_score += 30
            indicators.append({'name': 'Yield Curve', 'value': yield_curve, 'signal': 'inverted'})
        elif yield_curve < 0.5:
            recession_score += 15
            indicators.append({'name': 'Yield Curve', 'value': yield_curve, 'signal': 'flat'})
        else:
            indicators.append({'name': 'Yield Curve', 'value': yield_curve, 'signal': 'normal'})
        
        # Unemployment trend (simplified)
        if unemployment > 4.5:
            recession_score += 20
            indicators.append({'name': 'Unemployment', 'value': unemployment, 'signal': 'elevated'})
        else:
            indicators.append({'name': 'Unemployment', 'value': unemployment, 'signal': 'normal'})
        
        # Fed policy stance
        if fed_rate > 5:
            recession_score += 10
            indicators.append({'name': 'Fed Rate', 'value': fed_rate, 'signal': 'restrictive'})
        else:
            indicators.append({'name': 'Fed Rate', 'value': fed_rate, 'signal': 'neutral'})
        
        return {
            'probability': min(recession_score, 100) / 100.0,
            'risk_level': 'high' if recession_score > 70 else 'moderate' if recession_score > 40 else 'low',
            'regime': regime,
            'indicators': indicators,
            'analysis': {
                'gdp_growth': gdp_growth,
                'cpi_yoy': cpi_yoy,
                'unemployment': unemployment,
                'fed_rate': fed_rate,
                'yield_curve': yield_curve
            }
        }
    
    def analyze_debt_cycle(self, economic_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze debt cycle using FinancialAnalyst's credit cycle methods
        
        Returns:
            Dict with cycle phase, stress level, and risks
        """
        if economic_data is None:
            economic_data = self.get_economic_indicators()
        
        # Get debt metrics (would need additional FRED series for full analysis)
        # Using simplified approach with available data
        debt_gdp = 120.0  # This would come from GFDEBTN/GDP series
        household_debt = 75.0  # Would come from HDTGPDUSQ163N
        delinquency = 2.5  # Would come from DRCCLACBS
        debt_service = 9.5  # Would come from TDSP
        
        # Use FinancialAnalyst's credit cycle analysis
        credit_cycle = self.financial_analyst._analyze_credit_cycle(
            debt_gdp=debt_gdp,
            household_debt_gdp=household_debt,
            credit_delinquency=delinquency,
            debt_service=debt_service
        )
        
        return credit_cycle
    
    def analyze_empire_cycle(self, economic_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze empire cycle using FinancialAnalyst's methods
        
        Returns:
            Dict with empire stage, structural risk, and outlook
        """
        if economic_data is None:
            economic_data = self.get_economic_indicators()
        
        # Get required metrics
        debt_gdp = 120.0  # Would come from GFDEBTN/GDP
        inequality_gini = 41.5  # Would need external data source
        policy_uncertainty = 100.0  # Would come from EPU index
        
        # Get credit cycle phase for context
        credit_cycle = self.analyze_debt_cycle(economic_data)
        
        # Use FinancialAnalyst's empire cycle analysis
        empire_cycle = self.financial_analyst._analyze_empire_cycle(
            debt_gdp=debt_gdp,
            inequality_gini=inequality_gini,
            sovereign_debt_uncertainty=policy_uncertainty,
            credit_cycle_phase=credit_cycle.get('cycle_phase', 'unknown')
        )
        
        return empire_cycle
    
    def generate_fed_policy_forecast(self, economic_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate Fed policy forecast based on economic conditions
        
        Returns:
            Dict with rate projections and policy stance
        """
        if economic_data is None:
            economic_data = self.get_economic_indicators()
        
        current_rate = economic_data.get('DFF', {}).get('value', 5.33)
        cpi_value = economic_data.get('CPIAUCSL', {}).get('value', 3.2)
        unemployment = economic_data.get('UNRATE', {}).get('value', 3.8)
        
        # Determine policy direction based on dual mandate
        if cpi_value > 3.0 and unemployment < 4.0:
            # Inflation above target, low unemployment -> hawkish
            terminal_rate = current_rate + 0.5
            policy_stance = 'restrictive'
            next_move = 'hold' if current_rate > 5 else 'hike'
        elif cpi_value < 2.0 or unemployment > 4.5:
            # Low inflation or high unemployment -> dovish
            terminal_rate = max(current_rate - 1.0, 2.5)
            policy_stance = 'accommodative'
            next_move = 'cut'
        else:
            # Balanced conditions
            terminal_rate = current_rate
            policy_stance = 'neutral'
            next_move = 'hold'
        
        # Generate projection path (simplified)
        months = 24
        projections = []
        rate = current_rate
        
        for i in range(months):
            if i < 6:
                # Near term - gradual moves
                if next_move == 'hike':
                    rate = min(rate + 0.25, terminal_rate)
                elif next_move == 'cut':
                    rate = max(rate - 0.25, terminal_rate)
            else:
                # Converge to terminal rate
                rate = rate * 0.9 + terminal_rate * 0.1
            
            projections.append({
                'month': i + 1,
                'rate': rate,
                'lower_bound': max(rate - 0.5, 0),
                'upper_bound': rate + 0.5
            })
        
        return {
            'current_rate': current_rate,
            'terminal_rate': terminal_rate,
            'policy_stance': policy_stance,
            'next_move': next_move,
            'projections': projections,
            'neutral_rate': 3.5,  # Estimated neutral rate
            'probability_cut': 0.3 if next_move == 'cut' else 0.1,
            'probability_hold': 0.7 if next_move == 'hold' else 0.3,
            'probability_hike': 0.3 if next_move == 'hike' else 0.0
        }
    
    def generate_sector_rotation_signals(self, economic_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate sector rotation recommendations based on economic regime
        
        Returns:
            Dict with sector recommendations and rationale
        """
        recession_risk = self.calculate_recession_risk(economic_data)
        regime = recession_risk.get('regime', 'transitional')
        
        # Sector rotation based on economic regime
        sector_scores = {}
        
        if regime == 'goldilocks':
            # Good growth, moderate inflation - risk-on
            sector_scores = {
                'Technology': 90,
                'Consumer Discretionary': 85,
                'Financials': 80,
                'Industrials': 75,
                'Materials': 70,
                'Energy': 65,
                'Real Estate': 60,
                'Healthcare': 55,
                'Consumer Staples': 45,
                'Utilities': 40,
                'Communications': 70
            }
            rationale = "Risk-on environment favors growth sectors"
            
        elif regime == 'recession':
            # Defensive positioning
            sector_scores = {
                'Utilities': 90,
                'Consumer Staples': 85,
                'Healthcare': 80,
                'Real Estate': 50,
                'Communications': 60,
                'Technology': 40,
                'Financials': 30,
                'Consumer Discretionary': 25,
                'Industrials': 35,
                'Materials': 30,
                'Energy': 45
            }
            rationale = "Defensive sectors preferred in recession"
            
        elif regime == 'stagflation':
            # High inflation, weak growth
            sector_scores = {
                'Energy': 90,
                'Materials': 85,
                'Utilities': 70,
                'Consumer Staples': 75,
                'Real Estate': 65,
                'Healthcare': 60,
                'Financials': 50,
                'Technology': 30,
                'Consumer Discretionary': 25,
                'Industrials': 40,
                'Communications': 35
            }
            rationale = "Commodities and inflation hedges preferred"
            
        else:  # transitional or overheating
            # Balanced approach
            sector_scores = {
                'Healthcare': 70,
                'Technology': 65,
                'Financials': 60,
                'Consumer Staples': 65,
                'Industrials': 60,
                'Energy': 60,
                'Materials': 55,
                'Real Estate': 55,
                'Consumer Discretionary': 50,
                'Utilities': 60,
                'Communications': 55
            }
            rationale = "Balanced allocation during transition"
        
        # Sort by score
        recommended = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        avoid = sorted(sector_scores.items(), key=lambda x: x[1])[:3]
        
        return {
            'regime': regime,
            'scores': sector_scores,
            'recommended': [{'sector': s[0], 'score': s[1]} for s in recommended],
            'avoid': [{'sector': s[0], 'score': s[1]} for s in avoid],
            'rationale': rationale
        }