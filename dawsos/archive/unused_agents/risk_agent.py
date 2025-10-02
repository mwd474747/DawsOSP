from agents.base_agent import BaseAgent
from core.relationships import Relationships
from typing import Dict, List, Set

class RiskAgent(BaseAgent):
    """Specialized agent for risk analysis"""
    
    def __init__(self, graph):
        super().__init__(
            graph,
            name="RiskAgent",
            focus_areas=['risk', 'volatility', 'correlation', 'portfolio']
        )
    
    def analyze_portfolio_risk(self, holdings: Dict[str, float]) -> Dict:
        """Analyze portfolio risk
        holdings: {'ticker': weight, ...}
        """
        analysis = {
            'total_risk_score': 0,
            'risk_factors': [],
            'correlations': {},
            'concentration_risk': {},
            'macro_sensitivity': {},
            'recommendations': []
        }
        
        # Analyze each holding
        holding_risks = {}
        for ticker, weight in holdings.items():
            # Find or create stock node
            stock_nodes = self.graph.query({'type': 'stock', 'data': {'ticker': ticker}})
            if not stock_nodes:
                node_id = self.graph.add_node('stock', {'ticker': ticker})
                stock_nodes = [node_id]
            
            stock_node = stock_nodes[0]
            
            # Get risk metrics
            forecast = self.graph.forecast(stock_node)
            connections = self.graph.trace_connections(stock_node, max_depth=2)
            
            holding_risks[ticker] = {
                'weight': weight,
                'forecast': forecast.get('forecast'),
                'confidence': forecast.get('confidence'),
                'connection_count': len(connections),
                'risk_score': self._calculate_risk_score(forecast, connections)
            }
        
        # Calculate portfolio-level metrics
        analysis['total_risk_score'] = sum(
            h['risk_score'] * h['weight'] 
            for h in holding_risks.values()
        )
        
        # Find common risk factors
        analysis['risk_factors'] = self._find_common_risks(holdings)
        
        # Check correlations
        analysis['correlations'] = self._analyze_correlations(holdings)
        
        # Concentration risk
        analysis['concentration_risk'] = self._check_concentration(holdings)
        
        # Macro sensitivity
        analysis['macro_sensitivity'] = self._analyze_macro_sensitivity(holdings)
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis, holding_risks)
        
        return analysis
    
    def _calculate_risk_score(self, forecast: Dict, connections: List) -> float:
        """Calculate risk score for a position"""
        score = 0.0
        
        # Penalize negative forecast
        if forecast.get('forecast') == 'bearish':
            score += 0.3
        
        # Penalize low confidence
        confidence = forecast.get('confidence', 0)
        if confidence < 0.5:
            score += 0.2
        
        # Penalize many negative connections
        for path in connections:
            for edge in path:
                if edge['type'] in [Relationships.PRESSURES, Relationships.WEAKENS]:
                    score += 0.1 * edge.get('strength', 1.0)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _find_common_risks(self, holdings: Dict[str, float]) -> List[str]:
        """Find risk factors affecting multiple holdings"""
        risk_factors = {}
        
        for ticker in holdings:
            stock_nodes = self.graph.query({'type': 'stock', 'data': {'ticker': ticker}})
            if stock_nodes:
                connections = self.graph.trace_connections(stock_nodes[0], max_depth=2)
                
                for path in connections:
                    for edge in path:
                        if edge['type'] in [Relationships.PRESSURES, Relationships.WEAKENS]:
                            risk = edge['from']
                            risk_factors[risk] = risk_factors.get(risk, 0) + 1
        
        # Return risks affecting multiple stocks
        common_risks = [
            risk for risk, count in risk_factors.items() 
            if count > 1
        ]
        
        return common_risks[:5]
    
    def _analyze_correlations(self, holdings: Dict[str, float]) -> Dict:
        """Analyze correlations between holdings"""
        correlations = {
            'high_correlation_pairs': [],
            'diversification_score': 0
        }
        
        tickers = list(holdings.keys())
        
        # Check pairwise relationships
        for i, ticker1 in enumerate(tickers):
            for ticker2 in tickers[i+1:]:
                correlation = self._calculate_correlation(ticker1, ticker2)
                if abs(correlation) > 0.7:
                    correlations['high_correlation_pairs'].append({
                        'pair': (ticker1, ticker2),
                        'correlation': correlation
                    })
        
        # Calculate diversification score
        if correlations['high_correlation_pairs']:
            avg_correlation = sum(
                abs(p['correlation']) 
                for p in correlations['high_correlation_pairs']
            ) / len(correlations['high_correlation_pairs'])
            correlations['diversification_score'] = 1 - avg_correlation
        else:
            correlations['diversification_score'] = 1.0
        
        return correlations
    
    def _calculate_correlation(self, ticker1: str, ticker2: str) -> float:
        """Calculate correlation between two stocks"""
        # Find common influences
        stock1_nodes = self.graph.query({'type': 'stock', 'data': {'ticker': ticker1}})
        stock2_nodes = self.graph.query({'type': 'stock', 'data': {'ticker': ticker2}})
        
        if not stock1_nodes or not stock2_nodes:
            return 0
        
        # Get influences for each
        influences1 = set()
        for edge in self.graph.edges:
            if edge['to'] == stock1_nodes[0]:
                influences1.add(edge['from'])
        
        influences2 = set()
        for edge in self.graph.edges:
            if edge['to'] == stock2_nodes[0]:
                influences2.add(edge['from'])
        
        # Calculate correlation based on shared influences
        shared = len(influences1 & influences2)
        total = len(influences1 | influences2)
        
        if total == 0:
            return 0
        
        return shared / total
    
    def _check_concentration(self, holdings: Dict[str, float]) -> Dict:
        """Check concentration risk"""
        concentration = {
            'top_holding': None,
            'top_weight': 0,
            'concentrated': False,
            'sector_concentration': {}
        }
        
        # Find largest position
        if holdings:
            top = max(holdings.items(), key=lambda x: x[1])
            concentration['top_holding'] = top[0]
            concentration['top_weight'] = top[1]
            concentration['concentrated'] = top[1] > 0.25
        
        # Check sector concentration
        sectors = {}
        for ticker, weight in holdings.items():
            stock_nodes = self.graph.query({'type': 'stock', 'data': {'ticker': ticker}})
            if stock_nodes:
                # Find sector
                for edge in self.graph.edges:
                    if edge['from'] == stock_nodes[0] and edge['type'] == Relationships.PART_OF:
                        sector = edge['to']
                        sectors[sector] = sectors.get(sector, 0) + weight
        
        concentration['sector_concentration'] = sectors
        
        return concentration
    
    def _analyze_macro_sensitivity(self, holdings: Dict[str, float]) -> Dict:
        """Analyze portfolio sensitivity to macro factors"""
        sensitivities = {}
        
        macro_factors = ['rates', 'inflation', 'gdp', 'dollar']
        
        for factor in macro_factors:
            sensitivity = 0
            
            for ticker, weight in holdings.items():
                stock_nodes = self.graph.query({'type': 'stock', 'data': {'ticker': ticker}})
                if stock_nodes:
                    # Check connections to macro factor
                    for edge in self.graph.edges:
                        if (factor in edge['from'].lower() and 
                            edge['to'] == stock_nodes[0]):
                            sensitivity += weight * edge.get('strength', 1.0)
            
            sensitivities[factor] = sensitivity
        
        return sensitivities
    
    def _generate_recommendations(self, analysis: Dict, holding_risks: Dict) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        # Check total risk
        if analysis['total_risk_score'] > 0.7:
            recommendations.append("High risk: Consider reducing exposure or hedging")
        
        # Check concentration
        concentration = analysis['concentration_risk']
        if concentration['concentrated']:
            recommendations.append(
                f"Concentrated position: {concentration['top_holding']} is "
                f"{concentration['top_weight']*100:.1f}% of portfolio"
            )
        
        # Check correlations
        if analysis['correlations']['diversification_score'] < 0.5:
            recommendations.append("Low diversification: Holdings are highly correlated")
        
        # Check macro sensitivity
        sensitivities = analysis['macro_sensitivity']
        for factor, sensitivity in sensitivities.items():
            if sensitivity > 0.5:
                recommendations.append(f"High sensitivity to {factor}")
        
        return recommendations