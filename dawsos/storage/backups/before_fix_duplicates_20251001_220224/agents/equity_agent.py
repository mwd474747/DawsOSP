from agents.base_agent import BaseAgent
from core.relationships import Relationships
from typing import Dict, List

class EquityAgent(BaseAgent):
    """Specialized agent for equity/stock analysis"""
    
    def __init__(self, graph):
        super().__init__(
            graph,
            name="EquityAgent",
            focus_areas=['stock', 'equity', 'sector', 'earnings', 'valuation']
        )
    
    def analyze_stock(self, ticker: str) -> Dict:
        """Comprehensive stock analysis"""
        # Find stock node
        stock_nodes = self.graph.query({'type': 'stock', 'data': {'ticker': ticker}})
        
        if not stock_nodes:
            # Create node if doesn't exist
            node_id = self.graph.add_node('stock', {'ticker': ticker})
            stock_nodes = [node_id]
        
        stock_node = stock_nodes[0]
        
        # Get all connections
        connections = self.graph.trace_connections(stock_node, max_depth=3)
        
        # Analyze influences
        analysis = {
            'ticker': ticker,
            'connections': len(connections),
            'macro_influences': self._find_macro_influences(connections),
            'sector_position': self._analyze_sector_position(stock_node),
            'forecast': self.graph.forecast(stock_node),
            'risk_factors': self._identify_stock_risks(stock_node, connections),
            'catalysts': self._identify_catalysts(stock_node, connections)
        }
        
        return analysis
    
    def _find_macro_influences(self, connections: List[List[Dict]]) -> List[Dict]:
        """Find macroeconomic influences on stock"""
        macro_influences = []
        
        for path in connections:
            for edge in path:
                from_node = self.graph.nodes.get(edge['from'], {})
                if from_node.get('type') in ['indicator', 'economic', 'macro']:
                    influence = {
                        'factor': edge['from'],
                        'relationship': edge['type'],
                        'strength': edge['strength']
                    }
                    if influence not in macro_influences:
                        macro_influences.append(influence)
        
        return sorted(macro_influences, key=lambda x: x['strength'], reverse=True)[:5]
    
    def _analyze_sector_position(self, stock_node: str) -> Dict:
        """Analyze stock's position within sector"""
        # Find sector connections
        for edge in self.graph.edges:
            if edge['from'] == stock_node and edge['type'] == Relationships.PART_OF:
                sector_node = edge['to']
                
                # Get sector forecast
                sector_forecast = self.graph.forecast(sector_node)
                
                # Find peers
                peers = []
                for other_edge in self.graph.edges:
                    if (other_edge['to'] == sector_node and 
                        other_edge['type'] == Relationships.PART_OF and 
                        other_edge['from'] != stock_node):
                        peers.append(other_edge['from'])
                
                return {
                    'sector': sector_node,
                    'sector_outlook': sector_forecast.get('forecast'),
                    'peer_count': len(peers),
                    'peers': peers[:5]
                }
        
        return {'sector': 'unknown', 'sector_outlook': 'neutral', 'peer_count': 0}
    
    def _identify_stock_risks(self, stock_node: str, connections: List[List[Dict]]) -> List[str]:
        """Identify risks specific to the stock"""
        risks = []
        
        # Check for negative relationships
        for path in connections:
            for edge in path:
                if edge['to'] == stock_node:
                    if edge['type'] in [Relationships.PRESSURES, Relationships.WEAKENS]:
                        from_node = self.graph.nodes.get(edge['from'], {})
                        risks.append(f"{edge['from']} {edge['type']} stock (strength: {edge['strength']})")
        
        return risks[:5]  # Top 5 risks
    
    def _identify_catalysts(self, stock_node: str, connections: List[List[Dict]]) -> List[str]:
        """Identify potential catalysts"""
        catalysts = []
        
        # Check for positive relationships
        for path in connections:
            for edge in path:
                if edge['to'] == stock_node:
                    if edge['type'] in [Relationships.SUPPORTS, Relationships.STRENGTHENS]:
                        catalysts.append(f"{edge['from']} {edge['type']} stock (strength: {edge['strength']})")
        
        return catalysts[:5]  # Top 5 catalysts
    
    def compare_stocks(self, tickers: List[str]) -> Dict:
        """Compare multiple stocks"""
        comparisons = {}
        
        for ticker in tickers:
            analysis = self.analyze_stock(ticker)
            comparisons[ticker] = {
                'forecast': analysis['forecast'].get('forecast'),
                'confidence': analysis['forecast'].get('confidence'),
                'risk_count': len(analysis['risk_factors']),
                'catalyst_count': len(analysis['catalysts']),
                'macro_sensitivity': len(analysis['macro_influences'])
            }
        
        # Rank by forecast confidence
        ranked = sorted(
            comparisons.items(),
            key=lambda x: x[1]['confidence'],
            reverse=True
        )
        
        return {
            'comparisons': comparisons,
            'ranking': [ticker for ticker, _ in ranked],
            'best_pick': ranked[0][0] if ranked else None
        }