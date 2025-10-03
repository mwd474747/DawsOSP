"""RelationshipHunter - Finds connections between nodes"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Tuple

class RelationshipHunter(BaseAgent):
    """Hunts for relationships between nodes"""

    def __init__(self, graph, llm_client=None, capabilities=None):
        super().__init__("RelationshipHunter", graph, llm_client)
        self.vibe = "curious"
        self.capabilities = capabilities or {}

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are RelationshipHunter, finding hidden connections.

        Node 1: {context.get('node1', {})}
        Node 2: {context.get('node2', {})}
        Context: {context.get('context', 'none')}

        Is there a relationship? Consider:
        - Causal (one causes the other)
        - Correlation (they move together)
        - Inverse (they move opposite)
        - Temporal (one leads/lags the other)
        - Structural (part of same system)

        Return:
        - exists: true/false
        - type: relationship type
        - strength: 0-1
        - confidence: how sure are you
        - reason: one sentence why
        """

    def process(self, context: Any) -> Dict[str, Any]:
        """Process method for compatibility with patterns"""

        # Extract data from context
        if isinstance(context, dict):
            data = context.get('data', context)
            target = context.get('target', 'SPY')
            capabilities = context.get('capabilities', {})
        else:
            data = {}
            target = 'SPY'
            capabilities = {}

        # Get market capability for fetching price data
        market_cap = capabilities.get('market')
        if not market_cap:
            # If no capability passed, try to get from parent context
            if hasattr(self, 'capabilities'):
                market_cap = self.capabilities.get('market')

        if not market_cap:
            # Return basic correlations based on known relationships
            return self._get_default_correlations(target)

        # Symbols to check correlation against
        symbols_to_check = ['QQQ', 'IWM', 'TLT', 'GLD', 'DXY', 'VXX', 'XLE', 'XLF', 'ARKK']
        correlations = {}

        # For now, use default correlations since historical data requires a different API endpoint
        # TODO: Implement historical price fetching when API endpoint is available
        return self._get_default_correlations(target)

        # Future implementation when historical data is available:
        # target_history = market_cap.get_historical(target, days=30)
        # if 'error' in target_history or not target_history.get('prices'):
        #     return self._get_default_correlations(target)
        # ... calculate real correlations ...

        # Categorize correlations
        strong_positive = []
        weak_positive = []
        negative = []

        for symbol, corr in correlations.items():
            if corr > 0.7:
                strong_positive.append(f'{symbol} ({corr:.2f})')
            elif corr > 0.3:
                weak_positive.append(f'{symbol} ({corr:.2f})')
            elif corr < -0.3:
                negative.append(f'{symbol} ({corr:.2f})')

        # Generate summary
        summary = self._generate_correlation_summary(target, correlations)

        return {
            'response': f'Calculated correlations for {target}',
            'correlations': {
                'strong_positive': strong_positive,
                'weak_positive': weak_positive,
                'negative': negative,
                'summary': summary
            }
        }

    def _calculate_returns(self, prices: List[float]) -> List[float]:
        """Calculate daily returns from price series"""
        if len(prices) < 2:
            return []
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        return returns

    def _calculate_correlation(self, returns1: List[float], returns2: List[float]) -> float:
        """Calculate Pearson correlation between two return series"""
        import numpy as np
        if not returns1 or not returns2 or len(returns1) != len(returns2):
            return 0.0

        try:
            # Convert to numpy arrays
            r1 = np.array(returns1)
            r2 = np.array(returns2)

            # Calculate correlation coefficient
            corr_matrix = np.corrcoef(r1, r2)
            correlation = corr_matrix[0, 1]

            return round(correlation, 2) if not np.isnan(correlation) else 0.0
        except:
            return 0.0

    def _generate_correlation_summary(self, target: str, correlations: Dict[str, float]) -> str:
        """Generate summary of correlation findings"""
        if not correlations:
            return f"{target} correlation data unavailable"

        # Find strongest correlations
        strongest = max(correlations.items(), key=lambda x: abs(x[1]))

        if abs(strongest[1]) > 0.7:
            relation = "strong positive" if strongest[1] > 0 else "strong negative"
            return f"{target} shows {relation} correlation with {strongest[0]}"
        elif abs(strongest[1]) > 0.4:
            relation = "moderate positive" if strongest[1] > 0 else "moderate negative"
            return f"{target} has {relation} correlation with {strongest[0]}"
        else:
            return f"{target} shows weak correlations with tracked indices"

    def _get_default_correlations(self, target: str) -> Dict[str, Any]:
        """Return default correlations based on known relationships"""
        known_correlations = {
            'SPY': {
                'strong_positive': ['QQQ (0.85)', 'IWM (0.78)'],
                'weak_positive': ['TLT (0.35)'],
                'negative': ['VXX (-0.65)', 'DXY (-0.35)'],
                'summary': 'SPY typically correlates strongly with tech and small caps'
            },
            'QQQ': {
                'strong_positive': ['SPY (0.85)', 'ARKK (0.75)'],
                'weak_positive': ['IWM (0.55)'],
                'negative': ['VXX (-0.70)', 'TLT (-0.30)'],
                'summary': 'QQQ moves with growth and technology sectors'
            }
        }

        default = known_correlations.get(target, {
            'strong_positive': [],
            'weak_positive': [],
            'negative': [],
            'summary': f'Correlation data for {target} requires market data access'
        })

        return {
            'response': f'Correlations for {target} (estimated)',
            'correlations': default
        }

    def hunt(self, node_id: str = None) -> List[Dict[str, Any]]:
        """Hunt for relationships from a node or globally"""
        if not self.graph:
            return []

        relationships_found = []

        if node_id:
            # Hunt from specific node
            node = self.graph.nodes.get(node_id)
            if not node:
                return []

            # Check against all other nodes
            for other_id, other_node in self.graph.nodes.items():
                if other_id != node_id:
                    relationship = self._check_relationship(node_id, other_id)
                    if relationship.get('exists'):
                        relationships_found.append(relationship)
        else:
            # Global hunt - check recent nodes
            recent_nodes = self._get_recent_nodes(5)
            for node1 in recent_nodes:
                for node2 in recent_nodes:
                    if node1 != node2:
                        relationship = self._check_relationship(node1, node2)
                        if relationship.get('exists'):
                            relationships_found.append(relationship)

        return relationships_found

    def _check_relationship(self, node1_id: str, node2_id: str) -> Dict[str, Any]:
        """Check if two nodes should be related"""
        node1 = self.graph.nodes.get(node1_id)
        node2 = self.graph.nodes.get(node2_id)

        # Use heuristics for now (will use LLM later)
        relationship = {"exists": False}

        # Economic indicators often relate
        if node1.get('type') == 'indicator' and node2.get('type') == 'indicator':
            relationship = {
                "exists": True,
                "from": node1_id,
                "to": node2_id,
                "type": "correlates",
                "strength": 0.5,
                "confidence": 0.7,
                "reason": "Economic indicators often correlate"
            }

        # Stocks in same sector relate
        elif node1.get('type') == 'stock' and node2.get('type') == 'stock':
            if node1.get('data', {}).get('sector') == node2.get('data', {}).get('sector'):
                relationship = {
                    "exists": True,
                    "from": node1_id,
                    "to": node2_id,
                    "type": "correlates",
                    "strength": 0.6,
                    "confidence": 0.8,
                    "reason": "Same sector stocks often move together"
                }

        # News affects stocks
        elif node1.get('type') == 'news' and node2.get('type') == 'stock':
            if node2_id.lower() in str(node1.get('data', {})).lower():
                relationship = {
                    "exists": True,
                    "from": node1_id,
                    "to": node2_id,
                    "type": "influences",
                    "strength": 0.4,
                    "confidence": 0.6,
                    "reason": "News mentions this stock"
                }

        return relationship

    def _get_recent_nodes(self, count: int) -> List[str]:
        """Get most recently added nodes"""
        if not self.graph or not self.graph.nodes:
            return []

        # Sort by creation time and get most recent
        sorted_nodes = sorted(
            self.graph.nodes.items(),
            key=lambda x: x[1].get('created', ''),
            reverse=True
        )

        return [node_id for node_id, _ in sorted_nodes[:count]]

    def suggest_connections(self, node_id: str) -> List[Tuple[str, str, float]]:
        """Suggest what a node might connect to"""
        suggestions = []
        node = self.graph.nodes.get(node_id)

        if not node:
            return suggestions

        # Suggest connections based on type
        node_type = node.get('type')

        for other_id, other_node in self.graph.nodes.items():
            if other_id == node_id:
                continue

            score = 0

            # Same type nodes often relate
            if other_node.get('type') == node_type:
                score += 0.3

            # Complementary types
            complementary = {
                'indicator': ['stock', 'sector'],
                'stock': ['indicator', 'news', 'sector'],
                'news': ['stock', 'sector'],
                'sector': ['stock', 'indicator']
            }

            if other_node.get('type') in complementary.get(node_type, []):
                score += 0.4

            # Already connected nodes suggest patterns
            if self._share_connections(node_id, other_id):
                score += 0.2

            if score > 0.3:
                suggestions.append((other_id, self._suggest_relationship_type(node_type, other_node.get('type')), score))

        return sorted(suggestions, key=lambda x: x[2], reverse=True)[:5]

    def _share_connections(self, node1: str, node2: str) -> bool:
        """Check if two nodes share connections"""
        if not self.graph:
            return False

        connections1 = set()
        connections2 = set()

        for edge in self.graph.edges:
            if edge['from'] == node1:
                connections1.add(edge['to'])
            if edge['from'] == node2:
                connections2.add(edge['to'])

        return len(connections1.intersection(connections2)) > 0

    def _suggest_relationship_type(self, type1: str, type2: str) -> str:
        """Suggest relationship type based on node types"""
        suggestions = {
            ('indicator', 'indicator'): 'correlates',
            ('indicator', 'stock'): 'influences',
            ('stock', 'stock'): 'correlates',
            ('news', 'stock'): 'influences',
            ('sector', 'stock'): 'contains',
            ('indicator', 'sector'): 'affects'
        }

        return suggestions.get((type1, type2), 'relates')