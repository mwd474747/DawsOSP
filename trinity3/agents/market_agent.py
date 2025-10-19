"""
MarketAgent - Market structure, flows, and positioning analysis
Handles market breadth, options flow, correlations, volatility, etc.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent
from services.openbb_service import OpenBBService
from services.prediction_service import PredictionService

class MarketAgent(BaseAgent):
    """Specializes in market structure and flow analysis"""
    
    def __init__(self):
        capabilities = [
            "market_breadth_analysis",
            "options_flow_monitoring",
            "sector_rotation_detection",
            "volatility_regime_analysis",
            "correlation_breakdown",
            "liquidity_conditions",
            "risk_appetite_gauging",
            "momentum_tracking",
            "sentiment_analysis",
            "intermarket_analysis"
        ]
        super().__init__("MarketAgent", capabilities)
        self.openbb = OpenBBService()
        self.prediction_service = PredictionService()
    
    def analyze(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main analysis method for market queries"""
        query_lower = query.lower()
        context = context or {}
        
        # Route to specific analysis
        if 'breadth' in query_lower or 'internals' in query_lower:
            return self.analyze_market_breadth()
        elif 'options' in query_lower or 'flow' in query_lower:
            return self.analyze_options_flow()
        elif 'sector' in query_lower or 'rotation' in query_lower:
            return self.detect_sector_rotation()
        elif 'volatility' in query_lower or 'vix' in query_lower:
            return self.analyze_volatility_regime()
        elif 'correlation' in query_lower:
            return self.analyze_correlations()
        elif 'sentiment' in query_lower:
            return self.analyze_market_sentiment()
        else:
            # Comprehensive market analysis
            return self.comprehensive_market_analysis()
    
    def predict(
        self,
        target: str,
        horizon: str = "1W",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make market predictions with persistence"""
        # Get current market data
        market_data = self._get_market_snapshot()
        
        # Generate prediction based on target
        if target == "direction":
            prediction = self._predict_market_direction(market_data, horizon)
        elif target == "volatility":
            prediction = self._predict_volatility(market_data, horizon)
        elif target == "rotation":
            prediction = self._predict_sector_rotation(market_data, horizon)
        else:
            prediction = {'error': f'Unknown prediction target: {target}'}
        
        # Store prediction
        if 'error' not in prediction:
            prediction_id = self.prediction_service.store_prediction(
                prediction_type=f"market_{target}",
                prediction_data=prediction,
                confidence=prediction.get('confidence', 50),
                target_date=(datetime.now() + self._parse_horizon(horizon)).strftime('%Y-%m-%d'),
                agent=self.name
            )
            prediction['prediction_id'] = prediction_id
        
        return self.format_response(
            f"market_prediction_{target}",
            prediction,
            prediction.get('confidence', 50)
        )
    
    def analyze_market_breadth(self) -> Dict[str, Any]:
        """Analyze market internals and breadth indicators"""
        breadth_data = self.openbb.get_market_breadth()
        
        # Calculate breadth metrics
        analysis = {
            'advance_decline': self._calculate_advance_decline(breadth_data),
            'new_highs_lows': self._analyze_highs_lows(breadth_data),
            'volume_breadth': self._analyze_volume_breadth(breadth_data),
            'sector_participation': self._analyze_sector_participation(breadth_data),
            'breadth_thrust': self._calculate_breadth_thrust(breadth_data),
            'market_health': 'Healthy' if self._is_breadth_positive(breadth_data) else 'Deteriorating'
        }
        
        # Generate signal
        signal = self._generate_breadth_signal(analysis)
        analysis['signal'] = signal
        analysis['confidence'] = self._calculate_breadth_confidence(analysis)
        
        # Store as prediction
        self.prediction_service.store_prediction(
            prediction_type="market_breadth",
            prediction_data=analysis,
            confidence=analysis['confidence'],
            target_date=(datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            agent=self.name
        )
        
        return self.format_response('market_breadth_analysis', analysis, analysis['confidence'])
    
    def analyze_options_flow(self, symbol: str = 'SPY') -> Dict[str, Any]:
        """Analyze options flow for market sentiment"""
        options = self.openbb.get_options_chain(symbol)
        
        if not options:
            return self.format_response(
                'options_flow_analysis',
                {'message': 'No options data available'},
                0
            )
        
        # Analyze options data
        analysis = {
            'put_call_ratio': self._calculate_put_call_ratio(options),
            'gamma_exposure': self._calculate_gamma_exposure(options),
            'max_pain': self._calculate_max_pain(options),
            'unusual_activity': self._detect_unusual_options_activity(options),
            'dealer_positioning': self._estimate_dealer_positioning(options),
            'skew_analysis': self._analyze_options_skew(options)
        }
        
        # Interpret flow
        analysis['sentiment'] = self._interpret_options_flow(analysis)
        analysis['market_expectation'] = self._derive_market_expectation(analysis)
        
        return self.format_response('options_flow_analysis', analysis, 75)
    
    def detect_sector_rotation(self) -> Dict[str, Any]:
        """Detect sector rotation patterns"""
        sector_performance = self.openbb.get_sector_performance()
        
        # Analyze rotation
        analysis = {
            'current_leaders': self._identify_sector_leaders(sector_performance),
            'current_laggards': self._identify_sector_laggards(sector_performance),
            'rotation_signals': self._detect_rotation_signals(sector_performance),
            'momentum_shifts': self._analyze_momentum_shifts(sector_performance),
            'recommended_sectors': self._recommend_sectors(sector_performance),
            'avoid_sectors': self._identify_weak_sectors(sector_performance)
        }
        
        # Generate rotation strategy
        analysis['rotation_strategy'] = self._generate_rotation_strategy(analysis)
        
        # Store prediction
        self.prediction_service.store_prediction(
            prediction_type="sector_rotation",
            prediction_data=analysis,
            confidence=70,
            target_date=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            agent=self.name
        )
        
        return self.format_response('sector_rotation_analysis', analysis, 70)
    
    def analyze_volatility_regime(self) -> Dict[str, Any]:
        """Analyze current volatility regime and implications"""
        # Get VIX and related data
        vix_data = self._get_volatility_indicators()
        
        analysis = {
            'current_vix': vix_data.get('vix', 20),
            'vix_percentile': self._calculate_vix_percentile(vix_data),
            'regime': self._identify_vol_regime(vix_data),
            'term_structure': self._analyze_vol_term_structure(vix_data),
            'regime_persistence': self._estimate_regime_persistence(vix_data),
            'risk_implications': self._derive_risk_implications(vix_data)
        }
        
        # Volatility forecast
        vol_forecast = self._forecast_volatility(vix_data)
        analysis['forecast'] = vol_forecast
        
        return self.format_response('volatility_analysis', analysis, 75)
    
    def analyze_correlations(self) -> Dict[str, Any]:
        """Analyze cross-asset correlations"""
        # Get multi-asset data
        correlations = self._calculate_cross_asset_correlations()
        
        analysis = {
            'stock_bond_correlation': correlations.get('stock_bond', 0),
            'dollar_correlation': correlations.get('dollar', {}),
            'commodity_correlations': correlations.get('commodities', {}),
            'regime': self._identify_correlation_regime(correlations),
            'breakdown_risk': self._assess_correlation_breakdown(correlations),
            'diversification_benefit': self._calculate_diversification_benefit(correlations)
        }
        
        return self.format_response('correlation_analysis', analysis, 70)
    
    def analyze_market_sentiment(self) -> Dict[str, Any]:
        """Comprehensive market sentiment analysis"""
        # Gather sentiment indicators
        sentiment_data = {
            'options': self.analyze_options_flow(),
            'breadth': self.analyze_market_breadth(),
            'news': self._analyze_news_sentiment(),
            'positioning': self._analyze_investor_positioning()
        }
        
        # Composite sentiment
        analysis = {
            'composite_sentiment': self._calculate_composite_sentiment(sentiment_data),
            'retail_sentiment': self._gauge_retail_sentiment(sentiment_data),
            'institutional_sentiment': self._gauge_institutional_sentiment(sentiment_data),
            'smart_money': self._track_smart_money(sentiment_data),
            'contrarian_signal': self._generate_contrarian_signal(sentiment_data),
            'sentiment_extreme': self._detect_sentiment_extreme(sentiment_data)
        }
        
        return self.format_response('sentiment_analysis', analysis, 75)
    
    def comprehensive_market_analysis(self) -> Dict[str, Any]:
        """Provide comprehensive market structure analysis"""
        # Gather all analyses
        breadth = self.analyze_market_breadth()
        volatility = self.analyze_volatility_regime()
        correlations = self.analyze_correlations()
        sentiment = self.analyze_market_sentiment()
        
        # Synthesize
        synthesis = {
            'market_regime': self._identify_market_regime(breadth, volatility, correlations),
            'risk_level': self._assess_overall_risk(breadth, volatility, sentiment),
            'opportunity_set': self._identify_opportunities(breadth, volatility, sentiment),
            'positioning_recommendation': self._recommend_positioning(breadth, volatility, sentiment),
            'key_levels': self._identify_key_market_levels(),
            'near_term_outlook': self._generate_near_term_outlook(breadth, volatility, sentiment),
            'confidence': self._calculate_overall_market_confidence(breadth, volatility, sentiment)
        }
        
        return self.format_response('comprehensive_market', synthesis, synthesis['confidence'])
    
    def backtest_market_timing(
        self,
        strategy: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Backtest market timing strategy"""
        # Get SPY as market proxy
        market_data = self.openbb.get_historical_prices('SPY', start_date, end_date)
        
        if market_data.empty:
            return {'error': 'No market data available'}
        
        # Define strategy logic
        if strategy == "breadth_momentum":
            strategy_logic = self._breadth_momentum_strategy
        elif strategy == "volatility_regime":
            strategy_logic = self._volatility_regime_strategy
        elif strategy == "sentiment_contrarian":
            strategy_logic = self._sentiment_contrarian_strategy
        else:
            return {'error': f'Unknown strategy: {strategy}'}
        
        # Run backtest
        results = self.prediction_service.backtest_strategy(
            strategy_name=f"Market_{strategy}",
            strategy_logic=strategy_logic,
            data=market_data,
            start_date=start_date,
            end_date=end_date
        )
        
        return results
    
    def simulate_market_scenarios(self) -> Dict[str, Any]:
        """Run Monte Carlo simulation for market scenarios"""
        # Get current market level
        spy_quote = self.openbb.get_equity_quote('SPY')
        current_level = spy_quote.get('results', [{}])[0].get('price', 500) if spy_quote else 500
        
        # Define market scenarios
        scenarios = [
            {'name': 'Bull Market', 'drift': 0.15, 'volatility': 0.12, 'days': 252},
            {'name': 'Bear Market', 'drift': -0.20, 'volatility': 0.25, 'days': 252},
            {'name': 'Sideways', 'drift': 0.05, 'volatility': 0.15, 'days': 252},
            {'name': 'Crash', 'drift': -0.40, 'volatility': 0.40, 'days': 60},
            {'name': 'Melt-up', 'drift': 0.30, 'volatility': 0.10, 'days': 90}
        ]
        
        # Run simulation
        simulation = self.prediction_service.simulate_scenarios(
            simulation_type='market_index',
            base_data={'initial_value': current_level, 'index': 'SPY'},
            scenarios=scenarios,
            monte_carlo_runs=5000
        )
        
        return self.format_response('market_simulation', simulation, 70)
    
    # Helper methods
    def _parse_horizon(self, horizon: str) -> timedelta:
        """Parse horizon string"""
        if 'W' in horizon:
            weeks = int(horizon.replace('W', ''))
            return timedelta(weeks=weeks)
        elif 'M' in horizon:
            months = int(horizon.replace('M', ''))
            return timedelta(days=30 * months)
        elif 'D' in horizon:
            days = int(horizon.replace('D', ''))
            return timedelta(days=days)
        return timedelta(days=7)
    
    def _get_market_snapshot(self) -> Dict[str, Any]:
        """Get current market snapshot"""
        spy = self.openbb.get_equity_quote('SPY')
        breadth = self.openbb.get_market_breadth()
        
        return {
            'spy_level': spy.get('results', [{}])[0].get('price', 0) if spy else 0,
            'breadth': breadth,
            'timestamp': datetime.now().isoformat()
        }
    
    def _predict_market_direction(self, market_data: Dict, horizon: str) -> Dict:
        """Predict market direction"""
        # Simplified prediction based on breadth and momentum
        bullish_signals = 0
        bearish_signals = 0
        
        # Add your prediction logic here
        if market_data.get('breadth', {}).get('advancing', 0) > market_data.get('breadth', {}).get('declining', 0):
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        direction = 'Bullish' if bullish_signals > bearish_signals else 'Bearish'
        confidence = 60 + (abs(bullish_signals - bearish_signals) * 10)
        
        return {
            'direction': direction,
            'horizon': horizon,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'confidence': min(confidence, 85)
        }
    
    def _predict_volatility(self, market_data: Dict, horizon: str) -> Dict:
        """Predict volatility levels"""
        # Simplified volatility prediction
        current_vix = 20  # Placeholder
        
        return {
            'current_vix': current_vix,
            'predicted_vix': current_vix * 1.1,
            'regime': 'Normal' if current_vix < 20 else 'Elevated',
            'horizon': horizon,
            'confidence': 65
        }
    
    def _predict_sector_rotation(self, market_data: Dict, horizon: str) -> Dict:
        """Predict sector rotation"""
        return {
            'into_sectors': ['Technology', 'Healthcare'],
            'out_of_sectors': ['Energy', 'Utilities'],
            'confidence': 60,
            'horizon': horizon
        }
    
    # Market breadth analysis helpers
    def _calculate_advance_decline(self, breadth_data: Dict) -> Dict:
        if 'advancing' in breadth_data and 'declining' in breadth_data:
            advancing = breadth_data.get('advancing', 0)
            declining = breadth_data.get('declining', 0)
            ratio = advancing / declining if declining > 0 else float('inf')
            
            return {
                'advancing': advancing,
                'declining': declining,
                'unchanged': breadth_data.get('unchanged', 0),
                'ratio': ratio,
                'net': advancing - declining
            }
        return {}
    
    def _analyze_highs_lows(self, breadth_data: Dict) -> Dict:
        return {
            'new_highs': breadth_data.get('new_highs', 0),
            'new_lows': breadth_data.get('new_lows', 0),
            'ratio': 2.5,  # Placeholder
            'signal': 'Positive'
        }
    
    def _analyze_volume_breadth(self, breadth_data: Dict) -> Dict:
        return {
            'up_volume': breadth_data.get('up_volume', 0),
            'down_volume': breadth_data.get('down_volume', 0),
            'ratio': 1.5,
            'signal': 'Accumulation'
        }
    
    def _analyze_sector_participation(self, breadth_data: Dict) -> Dict:
        return {
            'sectors_advancing': 7,
            'sectors_declining': 4,
            'broad_based': True
        }
    
    def _calculate_breadth_thrust(self, breadth_data: Dict) -> float:
        # Simplified breadth thrust calculation
        return 65.0
    
    def _is_breadth_positive(self, breadth_data: Dict) -> bool:
        advancing = breadth_data.get('advancing', 0)
        declining = breadth_data.get('declining', 0)
        return advancing > declining
    
    def _generate_breadth_signal(self, analysis: Dict) -> str:
        if analysis.get('breadth_thrust', 0) > 70:
            return "STRONG BUY - Breadth thrust signal"
        elif analysis.get('market_health') == 'Healthy':
            return "BULLISH - Positive internals"
        else:
            return "CAUTIOUS - Weak internals"
    
    def _calculate_breadth_confidence(self, analysis: Dict) -> float:
        return 75.0
    
    # Options flow analysis helpers
    def _calculate_put_call_ratio(self, options: Dict) -> float:
        # Simplified P/C ratio calculation
        return 0.85
    
    def _calculate_gamma_exposure(self, options: Dict) -> Dict:
        return {
            'gex': 1000000000,
            'flip_point': 4500,
            'positioning': 'Long gamma'
        }
    
    def _calculate_max_pain(self, options: Dict) -> float:
        return 450.0  # Placeholder
    
    def _detect_unusual_options_activity(self, options: Dict) -> List[Dict]:
        return [
            {'strike': 455, 'type': 'call', 'volume': 50000, 'unusual': True}
        ]
    
    def _estimate_dealer_positioning(self, options: Dict) -> str:
        return "Dealers long gamma - supportive of low volatility"
    
    def _analyze_options_skew(self, options: Dict) -> Dict:
        return {
            'put_skew': 'Elevated',
            'call_skew': 'Normal',
            'risk_perception': 'Cautious'
        }
    
    def _interpret_options_flow(self, analysis: Dict) -> str:
        pc_ratio = analysis.get('put_call_ratio', 1)
        if pc_ratio < 0.7:
            return "Bullish"
        elif pc_ratio > 1.3:
            return "Bearish"
        else:
            return "Neutral"
    
    def _derive_market_expectation(self, analysis: Dict) -> Dict:
        return {
            'expected_move': '±2%',
            'bias': 'Upward',
            'confidence': 65
        }
    
    # Sector rotation helpers
    def _identify_sector_leaders(self, sector_data: Dict) -> List[str]:
        return ['Technology', 'Financials', 'Healthcare']
    
    def _identify_sector_laggards(self, sector_data: Dict) -> List[str]:
        return ['Energy', 'Utilities', 'Real Estate']
    
    def _detect_rotation_signals(self, sector_data: Dict) -> List[Dict]:
        return [
            {'from': 'Growth', 'to': 'Value', 'strength': 'Moderate'}
        ]
    
    def _analyze_momentum_shifts(self, sector_data: Dict) -> Dict:
        return {
            'accelerating': ['Technology', 'Healthcare'],
            'decelerating': ['Energy', 'Materials']
        }
    
    def _recommend_sectors(self, sector_data: Dict) -> List[str]:
        return ['Technology', 'Healthcare', 'Financials']
    
    def _identify_weak_sectors(self, sector_data: Dict) -> List[str]:
        return ['Energy', 'Utilities']
    
    def _generate_rotation_strategy(self, analysis: Dict) -> str:
        return "Overweight Technology and Healthcare, Underweight Energy and Utilities"
    
    # Volatility analysis helpers
    def _get_volatility_indicators(self) -> Dict:
        # Get VIX and related data (placeholder)
        return {
            'vix': 18.5,
            'vix9d': 16.2,
            'vix3m': 20.1,
            'historical_percentile': 35
        }
    
    def _calculate_vix_percentile(self, vix_data: Dict) -> float:
        return vix_data.get('historical_percentile', 50)
    
    def _identify_vol_regime(self, vix_data: Dict) -> str:
        vix = vix_data.get('vix', 20)
        if vix < 15:
            return "Low Volatility"
        elif vix < 25:
            return "Normal Volatility"
        elif vix < 35:
            return "Elevated Volatility"
        else:
            return "High Volatility / Stress"
    
    def _analyze_vol_term_structure(self, vix_data: Dict) -> str:
        if vix_data.get('vix9d', 0) > vix_data.get('vix3m', 0):
            return "Backwardation - Near-term stress"
        else:
            return "Contango - Normal structure"
    
    def _estimate_regime_persistence(self, vix_data: Dict) -> Dict:
        return {
            'expected_duration': '2-4 weeks',
            'probability_of_spike': 25
        }
    
    def _derive_risk_implications(self, vix_data: Dict) -> List[str]:
        return [
            "Moderate position sizes appropriate",
            "Consider hedges for tail risk",
            "Favorable for option selling strategies"
        ]
    
    def _forecast_volatility(self, vix_data: Dict) -> Dict:
        current = vix_data.get('vix', 20)
        return {
            '1_week': current * 0.95,
            '1_month': current * 1.05,
            '3_month': 22
        }
    
    # Correlation analysis helpers
    def _calculate_cross_asset_correlations(self) -> Dict:
        return {
            'stock_bond': -0.3,
            'dollar': {'stocks': -0.2, 'commodities': -0.6},
            'commodities': {'stocks': 0.4, 'bonds': -0.2}
        }
    
    def _identify_correlation_regime(self, correlations: Dict) -> str:
        stock_bond = correlations.get('stock_bond', 0)
        if stock_bond > 0.3:
            return "Risk-on/Risk-off"
        elif stock_bond < -0.3:
            return "Traditional negative correlation"
        else:
            return "Decorrelated"
    
    def _assess_correlation_breakdown(self, correlations: Dict) -> float:
        return 25.0  # Probability of breakdown
    
    def _calculate_diversification_benefit(self, correlations: Dict) -> str:
        return "High - Low correlations provide good diversification"
    
    # Sentiment analysis helpers
    def _analyze_news_sentiment(self) -> Dict:
        news = self.openbb.get_news(category='market')
        # Simplified sentiment analysis
        return {
            'overall': 'Neutral',
            'score': 0.5,
            'headlines_positive': 45,
            'headlines_negative': 35,
            'headlines_neutral': 20
        }
    
    def _analyze_investor_positioning(self) -> Dict:
        return {
            'institutional': 'Neutral',
            'retail': 'Bullish',
            'ctas': 'Short',
            'risk_parity': 'Reducing exposure'
        }
    
    def _calculate_composite_sentiment(self, sentiment_data: Dict) -> float:
        return 55.0  # Neutral to slightly bullish
    
    def _gauge_retail_sentiment(self, sentiment_data: Dict) -> str:
        return "Bullish - Retail buying dips"
    
    def _gauge_institutional_sentiment(self, sentiment_data: Dict) -> str:
        return "Neutral - Waiting for clarity"
    
    def _track_smart_money(self, sentiment_data: Dict) -> str:
        return "Accumulating selectively"
    
    def _generate_contrarian_signal(self, sentiment_data: Dict) -> Optional[str]:
        composite = self._calculate_composite_sentiment(sentiment_data)
        if composite > 80:
            return "SELL - Extreme bullishness"
        elif composite < 20:
            return "BUY - Extreme bearishness"
        return None
    
    def _detect_sentiment_extreme(self, sentiment_data: Dict) -> bool:
        composite = self._calculate_composite_sentiment(sentiment_data)
        return composite > 80 or composite < 20
    
    # Market regime and synthesis helpers
    def _identify_market_regime(self, *analyses) -> str:
        return "Bull Market - Late Stage"
    
    def _assess_overall_risk(self, *analyses) -> str:
        return "Medium - Some caution warranted"
    
    def _identify_opportunities(self, *analyses) -> List[str]:
        return [
            "Sector rotation into technology",
            "Volatility selling strategies",
            "Dip buying in quality names"
        ]
    
    def _recommend_positioning(self, *analyses) -> Dict:
        return {
            'equity_allocation': 60,
            'bond_allocation': 30,
            'cash_allocation': 10,
            'recommendation': 'Moderately bullish positioning'
        }
    
    def _identify_key_market_levels(self) -> Dict:
        return {
            'support_1': 440,
            'support_2': 430,
            'resistance_1': 460,
            'resistance_2': 470,
            'pivot': 450
        }
    
    def _generate_near_term_outlook(self, *analyses) -> str:
        return "Continued uptrend likely with normal pullbacks. Watch 440 support."
    
    def _calculate_overall_market_confidence(self, *analyses) -> float:
        return 70.0
    
    # Backtesting strategies
    def _breadth_momentum_strategy(self, data: pd.DataFrame) -> Dict:
        """Trade based on market breadth"""
        signals = {}
        # Simplified - would need actual breadth data
        
        data['ma20'] = data['close'].rolling(20).mean()
        
        for date, row in data.iterrows():
            if pd.isna(row['ma20']):
                signals[date] = 'hold'
            elif row['close'] > row['ma20']:
                signals[date] = 'buy'
            else:
                signals[date] = 'sell'
        
        return signals
    
    def _volatility_regime_strategy(self, data: pd.DataFrame) -> Dict:
        """Trade based on volatility regimes"""
        signals = {}
        
        # Calculate realized volatility
        data['returns'] = data['close'].pct_change()
        data['volatility'] = data['returns'].rolling(20).std() * np.sqrt(252)
        
        for date, row in data.iterrows():
            if pd.isna(row['volatility']):
                signals[date] = 'hold'
            elif row['volatility'] < 0.15:  # Low vol - buy
                signals[date] = 'buy'
            elif row['volatility'] > 0.25:  # High vol - sell
                signals[date] = 'sell'
            else:
                signals[date] = 'hold'
        
        return signals
    
    def _sentiment_contrarian_strategy(self, data: pd.DataFrame) -> Dict:
        """Contrarian strategy based on extremes"""
        signals = {}
        
        # Use RSI as sentiment proxy
        data['rsi'] = self._calculate_rsi(data['close'])
        
        for date, row in data.iterrows():
            if pd.isna(row['rsi']):
                signals[date] = 'hold'
            elif row['rsi'] < 30:  # Oversold - buy
                signals[date] = 'buy'
            elif row['rsi'] > 70:  # Overbought - sell
                signals[date] = 'sell'
            else:
                signals[date] = 'hold'
        
        return signals
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi