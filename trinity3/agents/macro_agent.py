"""
MacroAgent - Global economic analysis and predictions
Handles recession risk, economic cycles, central bank analysis, etc.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent
from services.openbb_service import OpenBBService
from services.prediction_service import PredictionService

class MacroAgent(BaseAgent):
    """Specializes in macroeconomic analysis and predictions"""
    
    def __init__(self):
        capabilities = [
            "economic_regime_detection",
            "recession_prediction", 
            "inflation_forecasting",
            "cycle_analysis",
            "central_bank_analysis",
            "currency_dynamics",
            "global_liquidity_tracking",
            "gdp_forecasting",
            "yield_curve_analysis",
            "systemic_risk_assessment"
        ]
        super().__init__("MacroAgent", capabilities)
        self.openbb = OpenBBService()
        self.prediction_service = PredictionService()
        
    def analyze(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main analysis method for macro queries
        """
        query_lower = query.lower()
        context = context or {}
        
        # Route to specific analysis based on query
        if 'recession' in query_lower:
            return self.analyze_recession_risk()
        elif 'inflation' in query_lower:
            return self.analyze_inflation()
        elif 'fed' in query_lower or 'central bank' in query_lower:
            return self.analyze_central_bank_policy()
        elif 'cycle' in query_lower or 'dalio' in query_lower:
            return self.analyze_economic_cycles()
        elif 'currency' in query_lower or 'dollar' in query_lower:
            return self.analyze_currency_dynamics()
        else:
            # Default comprehensive macro analysis
            return self.comprehensive_macro_analysis()
    
    def predict(
        self, 
        target: str, 
        horizon: str = "3M",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make macro predictions with persistence
        """
        # Get current data
        indicators = self.openbb.get_economic_indicators()
        
        # Calculate prediction based on target
        if target == "recession":
            prediction = self._predict_recession(indicators, horizon)
        elif target == "inflation":
            prediction = self._predict_inflation(indicators, horizon)
        elif target == "gdp":
            prediction = self._predict_gdp(indicators, horizon)
        else:
            prediction = {'error': f'Unknown prediction target: {target}'}
        
        # Store prediction if successful
        if 'error' not in prediction:
            prediction_id = self.prediction_service.store_prediction(
                prediction_type=f"macro_{target}",
                prediction_data=prediction,
                confidence=prediction.get('confidence', 50),
                target_date=(datetime.now() + self._parse_horizon(horizon)).strftime('%Y-%m-%d'),
                agent=self.name
            )
            prediction['prediction_id'] = prediction_id
        
        return self.format_response(
            f"macro_prediction_{target}",
            prediction,
            prediction.get('confidence', 50)
        )
    
    def analyze_recession_risk(self) -> Dict[str, Any]:
        """
        Analyze recession risk using multiple indicators
        """
        # Fetch key indicators
        indicators = self.openbb.get_economic_indicators([
            'T10Y2Y',      # Yield curve
            'UNRATE',      # Unemployment
            'CPIAUCSL',    # Inflation
            'DFF',         # Fed Funds
            'GDPC1',       # Real GDP
            'DRCCLACBS',   # Credit card delinquencies
            'SAHMCURRENT', # Sahm Rule
            'CFNAI'        # Chicago Fed National Activity Index
        ])
        
        # Calculate individual risk scores
        risk_scores = {}
        
        # Yield curve inversion
        if 'T10Y2Y' in indicators:
            latest_spread = self._get_latest_value(indicators['T10Y2Y'])
            risk_scores['yield_curve'] = {
                'value': latest_spread,
                'risk': 90 if latest_spread < 0 else 30,
                'signal': 'Inverted - High Risk' if latest_spread < 0 else 'Normal'
            }
        
        # Unemployment trend
        if 'UNRATE' in indicators:
            unemployment = self._get_series_data(indicators['UNRATE'])
            trend = self._calculate_trend(unemployment)
            risk_scores['unemployment'] = {
                'value': unemployment[-1] if len(unemployment) > 0 else None,
                'trend': trend,
                'risk': 70 if trend > 0.5 else 30,
                'signal': 'Rising' if trend > 0 else 'Stable'
            }
        
        # Sahm Rule
        if 'SAHMCURRENT' in indicators:
            sahm_value = self._get_latest_value(indicators['SAHMCURRENT'])
            risk_scores['sahm_rule'] = {
                'value': sahm_value,
                'risk': 95 if sahm_value > 0.5 else 20,
                'signal': 'Triggered!' if sahm_value > 0.5 else 'Not Triggered'
            }
        
        # Calculate composite risk score
        composite_risk = np.mean([v['risk'] for v in risk_scores.values() if 'risk' in v])
        
        # Make prediction
        recession_prediction = {
            'probability_6m': min(composite_risk * 1.2, 100),
            'probability_12m': min(composite_risk * 1.5, 100),
            'key_risks': risk_scores,
            'composite_score': composite_risk,
            'assessment': self._get_risk_assessment(composite_risk)
        }
        
        # Store prediction
        self.prediction_service.store_prediction(
            prediction_type="recession_risk",
            prediction_data=recession_prediction,
            confidence=composite_risk,
            target_date=(datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'),
            agent=self.name
        )
        
        return self.format_response(
            'recession_risk_analysis',
            recession_prediction,
            composite_risk
        )
    
    def analyze_inflation(self) -> Dict[str, Any]:
        """Analyze inflation trends and pressures"""
        indicators = self.openbb.get_economic_indicators([
            'CPIAUCSL',     # CPI
            'CPILFESL',     # Core CPI
            'PCEPI',        # PCE
            'DFEDTARU',     # Fed target rate
            'T5YIE',        # 5-year inflation expectations
            'DCOILWTICO',   # Oil prices
            'DEXUSEU'       # Dollar strength
        ])
        
        analysis = {
            'current_levels': {},
            'trends': {},
            'pressures': {},
            'forecast': {}
        }
        
        # Analyze each component
        if 'CPIAUCSL' in indicators:
            cpi_data = self._get_series_data(indicators['CPIAUCSL'])
            yoy_change = self._calculate_yoy_change(cpi_data)
            analysis['current_levels']['cpi_yoy'] = yoy_change[-1] if yoy_change else None
            analysis['trends']['cpi'] = 'Rising' if yoy_change[-1] > yoy_change[-6] else 'Falling'
        
        # Inflation pressures
        if 'DCOILWTICO' in indicators:
            oil_data = self._get_series_data(indicators['DCOILWTICO'])
            oil_trend = self._calculate_trend(oil_data[-20:]) if len(oil_data) > 20 else 0
            analysis['pressures']['energy'] = 'Inflationary' if oil_trend > 0 else 'Disinflationary'
        
        return self.format_response('inflation_analysis', analysis, 75)
    
    def analyze_central_bank_policy(self) -> Dict[str, Any]:
        """Analyze central bank policy and implications"""
        indicators = self.openbb.get_economic_indicators([
            'DFF',          # Fed Funds Rate
            'DFEDTARU',     # Target Rate
            'BOGMBASE',     # Monetary Base
            'M2SL',         # M2 Money Supply
            'WALCL'         # Fed Balance Sheet
        ])
        
        policy_analysis = {
            'current_stance': self._determine_policy_stance(indicators),
            'rate_path': self._project_rate_path(indicators),
            'liquidity_conditions': self._analyze_liquidity(indicators),
            'market_impact': self._assess_policy_impact()
        }
        
        return self.format_response('central_bank_analysis', policy_analysis, 80)
    
    def analyze_economic_cycles(self) -> Dict[str, Any]:
        """
        Analyze economic cycles using Dalio framework
        """
        # Get comprehensive data
        indicators = self.openbb.get_economic_indicators()
        
        # Debt cycle analysis
        debt_cycle = {
            'short_term_position': self._analyze_short_term_cycle(indicators),
            'long_term_position': self._analyze_long_term_cycle(indicators),
            'credit_conditions': self._analyze_credit_conditions(indicators),
            'deleveraging_risk': self._assess_deleveraging_risk(indicators)
        }
        
        # Business cycle
        business_cycle = {
            'current_phase': self._identify_cycle_phase(indicators),
            'months_in_phase': self._estimate_phase_duration(indicators),
            'next_phase_probability': self._predict_phase_transition(indicators)
        }
        
        analysis = {
            'debt_cycle': debt_cycle,
            'business_cycle': business_cycle,
            'composite_outlook': self._generate_cycle_outlook(debt_cycle, business_cycle),
            'investment_implications': self._derive_investment_implications(debt_cycle, business_cycle)
        }
        
        return self.format_response('economic_cycle_analysis', analysis, 85)
    
    def analyze_currency_dynamics(self) -> Dict[str, Any]:
        """Analyze currency trends and relationships"""
        # Get forex data
        currency_data = {
            'dxy': self.openbb.get_economic_indicators(['DEXUSEU', 'DEXJPUS', 'DEXUSUK']),
            'commodity_currencies': self.openbb.get_economic_indicators(['DEXCAUS', 'DEXAUUS']),
            'em_currencies': self.openbb.get_economic_indicators(['DEXBZUS', 'DEXINUS', 'DEXMXUS'])
        }
        
        analysis = {
            'dollar_strength': self._analyze_dollar_index(currency_data),
            'carry_trades': self._identify_carry_opportunities(currency_data),
            'risk_sentiment': self._assess_currency_risk_sentiment(currency_data),
            'regime': self._identify_currency_regime(currency_data)
        }
        
        return self.format_response('currency_analysis', analysis, 75)
    
    def comprehensive_macro_analysis(self) -> Dict[str, Any]:
        """Provide comprehensive macro overview"""
        # Gather all analyses
        recession = self.analyze_recession_risk()
        inflation = self.analyze_inflation()
        cycles = self.analyze_economic_cycles()
        
        # Create synthesis
        synthesis = {
            'macro_regime': self._identify_macro_regime(recession, inflation, cycles),
            'key_risks': self._identify_key_risks(recession, inflation, cycles),
            'opportunities': self._identify_opportunities(recession, inflation, cycles),
            'timeline': self._create_event_timeline(),
            'recommendations': self._generate_recommendations(recession, inflation, cycles)
        }
        
        return self.format_response('comprehensive_macro', synthesis, 85)
    
    def backtest_recession_model(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Backtest recession prediction model"""
        # Get historical data
        historical_data = self.openbb.get_economic_indicators(
            indicators=['T10Y2Y', 'UNRATE', 'CFNAI', 'SAHMCURRENT'],
            start_date=start_date
        )
        
        # Define strategy logic
        def recession_signal_strategy(data):
            signals = {}
            # Simple rule: predict recession when yield curve inverts
            for date, row in data.iterrows():
                if row['T10Y2Y'] < 0:
                    signals[date] = 'recession_predicted'
                else:
                    signals[date] = 'no_recession'
            return signals
        
        # Run backtest
        results = self.prediction_service.backtest_strategy(
            strategy_name="Recession_Prediction_YieldCurve",
            strategy_logic=recession_signal_strategy,
            data=pd.DataFrame(historical_data),
            start_date=start_date,
            end_date=end_date
        )
        
        return results
    
    # Helper methods
    def _get_latest_value(self, indicator_data: Any) -> float:
        """Extract latest value from indicator data"""
        if isinstance(indicator_data, dict) and 'results' in indicator_data:
            results = indicator_data['results']
            if results and len(results) > 0:
                return results[-1].get('value', 0)
        return 0
    
    def _get_series_data(self, indicator_data: Any) -> List[float]:
        """Extract time series from indicator data"""
        if isinstance(indicator_data, dict) and 'results' in indicator_data:
            return [r.get('value', 0) for r in indicator_data['results']]
        return []
    
    def _calculate_trend(self, data: List[float]) -> float:
        """Calculate trend coefficient"""
        if len(data) < 2:
            return 0
        x = np.arange(len(data))
        y = np.array(data)
        return np.polyfit(x, y, 1)[0]
    
    def _calculate_yoy_change(self, data: List[float]) -> List[float]:
        """Calculate year-over-year change"""
        if len(data) < 12:
            return []
        return [(data[i] / data[i-12] - 1) * 100 for i in range(12, len(data))]
    
    def _get_risk_assessment(self, risk_score: float) -> str:
        """Convert risk score to assessment"""
        if risk_score >= 75:
            return "HIGH RISK - Recession highly probable within 6 months"
        elif risk_score >= 50:
            return "ELEVATED RISK - Recession possible within 12 months"
        elif risk_score >= 25:
            return "MODERATE RISK - Monitor closely"
        else:
            return "LOW RISK - No immediate recession signals"
    
    def _parse_horizon(self, horizon: str) -> timedelta:
        """Parse horizon string to timedelta"""
        if 'M' in horizon:
            months = int(horizon.replace('M', ''))
            return timedelta(days=30 * months)
        elif 'D' in horizon:
            days = int(horizon.replace('D', ''))
            return timedelta(days=days)
        else:
            return timedelta(days=90)  # Default 3 months
    
    def _predict_recession(self, indicators: Dict, horizon: str) -> Dict[str, Any]:
        """Generate recession prediction"""
        # Simplified prediction logic
        risk_factors = []
        
        if 'T10Y2Y' in indicators:
            if self._get_latest_value(indicators['T10Y2Y']) < 0:
                risk_factors.append('Yield curve inverted')
        
        if 'UNRATE' in indicators:
            unemployment_trend = self._calculate_trend(self._get_series_data(indicators['UNRATE'])[-6:])
            if unemployment_trend > 0.1:
                risk_factors.append('Unemployment rising')
        
        probability = min(len(risk_factors) * 35, 95)
        
        return {
            'target': 'recession',
            'horizon': horizon,
            'probability': probability,
            'risk_factors': risk_factors,
            'confidence': 70 + len(risk_factors) * 10
        }
    
    def _predict_inflation(self, indicators: Dict, horizon: str) -> Dict[str, Any]:
        """Generate inflation prediction"""
        current_cpi = self._get_latest_value(indicators.get('CPIAUCSL', {}))
        trend = self._calculate_trend(self._get_series_data(indicators.get('CPIAUCSL', {}))[-12:])
        
        # Simple projection
        projected = current_cpi + (trend * 3)  # 3 months forward
        
        return {
            'target': 'inflation',
            'horizon': horizon,
            'current': current_cpi,
            'projected': projected,
            'trend': 'Rising' if trend > 0 else 'Falling',
            'confidence': 65
        }
    
    def _predict_gdp(self, indicators: Dict, horizon: str) -> Dict[str, Any]:
        """Generate GDP growth prediction"""
        gdp_data = self._get_series_data(indicators.get('GDP', {}))
        if gdp_data:
            recent_growth = self._calculate_yoy_change(gdp_data)[-1] if self._calculate_yoy_change(gdp_data) else 2.0
        else:
            recent_growth = 2.0
            
        return {
            'target': 'gdp_growth',
            'horizon': horizon,
            'current_growth': recent_growth,
            'projected_growth': recent_growth * 0.9,  # Conservative projection
            'confidence': 60
        }
    
    # Stub methods for complex analyses
    def _determine_policy_stance(self, indicators: Dict) -> str:
        return "Restrictive" if self._get_latest_value(indicators.get('DFF', {})) > 4 else "Neutral"
    
    def _project_rate_path(self, indicators: Dict) -> List[Dict]:
        current_rate = self._get_latest_value(indicators.get('DFF', {}))
        return [
            {'quarter': 'Q1', 'projected_rate': current_rate},
            {'quarter': 'Q2', 'projected_rate': current_rate - 0.25},
            {'quarter': 'Q3', 'projected_rate': current_rate - 0.5},
            {'quarter': 'Q4', 'projected_rate': current_rate - 0.5}
        ]
    
    def _analyze_liquidity(self, indicators: Dict) -> str:
        m2_growth = self._calculate_trend(self._get_series_data(indicators.get('M2SL', {}))[-12:])
        return "Tightening" if m2_growth < 0 else "Ample"
    
    def _assess_policy_impact(self) -> Dict:
        return {
            'equities': 'Headwind',
            'bonds': 'Supportive',
            'dollar': 'Strengthening',
            'commodities': 'Weakening'
        }
    
    def _analyze_short_term_cycle(self, indicators: Dict) -> str:
        return "Late Cycle"
    
    def _analyze_long_term_cycle(self, indicators: Dict) -> str:
        return "Debt Accumulation Phase"
    
    def _analyze_credit_conditions(self, indicators: Dict) -> str:
        return "Tightening"
    
    def _assess_deleveraging_risk(self, indicators: Dict) -> float:
        return 35.0
    
    def _identify_cycle_phase(self, indicators: Dict) -> str:
        return "Late Expansion"
    
    def _estimate_phase_duration(self, indicators: Dict) -> int:
        return 18
    
    def _predict_phase_transition(self, indicators: Dict) -> float:
        return 65.0
    
    def _generate_cycle_outlook(self, debt_cycle: Dict, business_cycle: Dict) -> str:
        return "Caution warranted - approaching cycle peak"
    
    def _derive_investment_implications(self, debt_cycle: Dict, business_cycle: Dict) -> List[str]:
        return [
            "Reduce risk exposure",
            "Increase cash allocation",
            "Focus on quality companies",
            "Consider defensive sectors"
        ]
    
    def _analyze_dollar_index(self, currency_data: Dict) -> Dict:
        return {'strength': 'Strong', 'trend': 'Rising', 'level': 105}
    
    def _identify_carry_opportunities(self, currency_data: Dict) -> List:
        return ['USDJPY', 'USDMXN']
    
    def _assess_currency_risk_sentiment(self, currency_data: Dict) -> str:
        return "Risk-off"
    
    def _identify_currency_regime(self, currency_data: Dict) -> str:
        return "Dollar dominance"
    
    def _identify_macro_regime(self, *analyses) -> str:
        return "Stagflation risk"
    
    def _identify_key_risks(self, *analyses) -> List[str]:
        return ["Recession", "Persistent inflation", "Policy error"]
    
    def _identify_opportunities(self, *analyses) -> List[str]:
        return ["Bonds if recession", "Commodities if inflation persists"]
    
    def _create_event_timeline(self) -> List[Dict]:
        return [
            {'date': '2024-03', 'event': 'FOMC Meeting'},
            {'date': '2024-04', 'event': 'Q1 GDP Release'},
            {'date': '2024-05', 'event': 'CPI Release'}
        ]
    
    def _generate_recommendations(self, *analyses) -> List[str]:
        return [
            "Monitor yield curve daily",
            "Track unemployment claims weekly",
            "Prepare for volatility",
            "Consider defensive positioning"
        ]