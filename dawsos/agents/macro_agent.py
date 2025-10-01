from agents.base_agent import BaseAgent
from core.relationships import Relationships
from typing import Dict, List, Optional

class MacroAgent(BaseAgent):
    """Specialized agent for macroeconomic analysis"""
    
    def __init__(self, graph):
        super().__init__(
            graph,
            name="MacroAgent",
            focus_areas=['indicator', 'economic', 'macro', 'gdp', 'inflation', 'rates']
        )
        self.key_indicators = [
            'GDP', 'CPI', 'UNEMPLOYMENT', 'FED_RATE', 
            'M2', 'TREASURY_10Y', 'VIX', 'DXY'
        ]
    
    def analyze_economy(self) -> Dict:
        """Comprehensive economic analysis"""
        analysis = {
            'indicators': {},
            'regime': None,
            'forecast': {},
            'risks': [],
            'opportunities': []
        }
        
        # Analyze each indicator
        for indicator in self.key_indicators:
            nodes = self.graph.query({'type': 'indicator', 'data': {'name': indicator}})
            if nodes:
                node_id = nodes[0]
                # Get current value
                node = self.graph.nodes.get(node_id, {})
                value = node.get('data', {}).get('value')
                
                # Forecast future
                forecast = self.graph.forecast(node_id)
                
                analysis['indicators'][indicator] = {
                    'current': value,
                    'forecast': forecast.get('forecast'),
                    'confidence': forecast.get('confidence'),
                    'key_drivers': forecast.get('key_drivers', [])
                }
        
        # Determine economic regime
        analysis['regime'] = self._determine_regime(analysis['indicators'])
        
        # Identify risks and opportunities
        analysis['risks'] = self._identify_risks(analysis)
        analysis['opportunities'] = self._identify_opportunities(analysis)
        
        return analysis
    
    def _determine_regime(self, indicators: Dict) -> str:
        """Determine current economic regime"""
        # Simple regime detection based on indicators
        gdp = indicators.get('GDP', {})
        inflation = indicators.get('CPI', {})
        rates = indicators.get('FED_RATE', {})
        
        if not all([gdp, inflation, rates]):
            return 'insufficient_data'
        
        # Check forecasts
        growth_outlook = gdp.get('forecast', 'neutral')
        inflation_outlook = inflation.get('forecast', 'neutral')
        
        if growth_outlook == 'bullish' and inflation_outlook == 'bearish':
            return 'goldilocks'  # Good growth, low inflation
        elif growth_outlook == 'bearish' and inflation_outlook == 'bullish':
            return 'stagflation'  # Low growth, high inflation
        elif growth_outlook == 'bullish' and inflation_outlook == 'bullish':
            return 'overheating'  # High growth, high inflation
        elif growth_outlook == 'bearish' and inflation_outlook == 'bearish':
            return 'recession'  # Low growth, low inflation
        else:
            return 'transitional'
    
    def _identify_risks(self, analysis: Dict) -> List[str]:
        """Identify economic risks"""
        risks = []
        
        regime = analysis['regime']
        if regime == 'stagflation':
            risks.append("Stagflation risk: Low growth with persistent inflation")
        elif regime == 'overheating':
            risks.append("Overheating risk: Fed may need aggressive tightening")
        elif regime == 'recession':
            risks.append("Recession risk: Economic contraction likely")
        
        # Check specific indicators
        vix = analysis['indicators'].get('VIX', {})
        if vix.get('current', 0) > 30:
            risks.append("High volatility: Market stress elevated")
        
        return risks
    
    def _identify_opportunities(self, analysis: Dict) -> List[str]:
        """Identify economic opportunities"""
        opportunities = []
        
        regime = analysis['regime']
        if regime == 'goldilocks':
            opportunities.append("Goldilocks environment: Favorable for risk assets")
        elif regime == 'recession':
            opportunities.append("Recession positioning: Bonds and defensive sectors")
        
        return opportunities
    
    def trace_inflation_impact(self, target_sector: str) -> Dict:
        """Trace how inflation impacts a specific sector"""
        # Find inflation node
        inflation_nodes = self.graph.query({'type': 'indicator', 'data': {'name': 'CPI'}})
        if not inflation_nodes:
            return {'error': 'No inflation data found'}
        
        # Find sector node
        sector_nodes = self.graph.query({'type': 'sector', 'data': {'name': target_sector}})
        if not sector_nodes:
            return {'error': f'Sector {target_sector} not found'}
        
        # Trace connections from inflation to sector
        paths = []
        for inflation_node in inflation_nodes:
            connections = self.graph.trace_connections(inflation_node, max_depth=3)
            for path in connections:
                # Check if path leads to target sector
                if path and path[-1]['to'] in sector_nodes:
                    paths.append(path)
        
        return {
            'sector': target_sector,
            'impact_paths': len(paths),
            'strongest_path': self._find_strongest_path(paths),
            'overall_impact': self._calculate_impact(paths)
        }
    
    def _find_strongest_path(self, paths: List[List[Dict]]) -> Optional[List[Dict]]:
        """Find the strongest influence path"""
        if not paths:
            return None
        
        strongest = None
        max_strength = 0
        
        for path in paths:
            strength = 1.0
            for edge in path:
                strength *= edge.get('strength', 1.0)
            
            if strength > max_strength:
                max_strength = strength
                strongest = path
        
        return strongest
    
    def _calculate_impact(self, paths: List[List[Dict]]) -> str:
        """Calculate overall impact from paths"""
        if not paths:
            return 'none'
        
        total_strength = 0
        for path in paths:
            strength = 1.0
            for edge in path:
                strength *= edge.get('strength', 1.0)
            total_strength += strength
        
        avg_strength = total_strength / len(paths)
        
        if avg_strength > 0.7:
            return 'strong'
        elif avg_strength > 0.4:
            return 'moderate'
        else:
            return 'weak'