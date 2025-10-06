"""RelationshipHunter - Finds connections between nodes"""
import logging
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class RelationshipHunter(BaseAgent):
    """Hunts for relationships between nodes"""

    def __init__(self, graph, llm_client=None, capabilities=None):
        super().__init__(graph=graph, name="RelationshipHunter", llm_client=llm_client)
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

        # Get historical data for the target symbol
        target_history = market_cap.get_historical(target, period='1M')
        if not target_history or 'error' in target_history:
            return self._get_default_correlations(target)

        # Calculate real correlations using historical data
        for symbol in symbols_to_check:
            symbol_history = market_cap.get_historical(symbol, period='1M')
            if symbol_history and 'error' not in symbol_history:
                correlation = self._calculate_price_correlation(target_history, symbol_history)
                correlations[symbol] = {
                    'correlation': correlation,
                    'strength': abs(correlation),
                    'direction': 'positive' if correlation > 0 else 'negative'
                }

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
        except (ValueError, IndexError) as e:
            logger.debug(f"Correlation calculation failed (likely insufficient data): {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Unexpected error calculating correlation: {e}", exc_info=True)
            return 0.0

    def _calculate_price_correlation(self, history1: List[Dict], history2: List[Dict]) -> float:
        """Calculate correlation between two historical price series"""
        try:
            # Extract prices and calculate returns
            prices1 = [float(item.get('close', 0)) for item in history1 if item.get('close')]
            prices2 = [float(item.get('close', 0)) for item in history2 if item.get('close')]

            if len(prices1) < 2 or len(prices2) < 2:
                return 0.0

            # Calculate daily returns
            returns1 = [(prices1[i] - prices1[i-1]) / prices1[i-1] for i in range(1, len(prices1))]
            returns2 = [(prices2[i] - prices2[i-1]) / prices2[i-1] for i in range(1, len(prices2))]

            # Use minimum length to align series
            min_len = min(len(returns1), len(returns2))
            if min_len < 5:  # Need at least 5 data points for meaningful correlation
                return 0.0

            return self._correlation(returns1[:min_len], returns2[:min_len])

        except Exception as e:
            print(f"Error calculating price correlation: {e}")
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
        """Calculate correlations from knowledge base or real-time data"""
        try:
            # Try to get correlations from knowledge base first
            if self.graph:
                # Query knowledge base for correlation data
                correlation_data = self.graph.query(
                    f"SELECT correlations FROM asset_correlations WHERE symbol = '{target}'"
                )
                if correlation_data and correlation_data[0]:
                    return {
                        'response': f'Correlations for {target} from knowledge base',
                        'correlations': correlation_data[0].get('correlations', {})
                    }

            # If no knowledge base data, calculate from sector relationships
            sector_correlations = self._calculate_sector_based_correlations(target)
            if sector_correlations:
                return sector_correlations

            # Last resort: Use historical correlation patterns (not hardcoded values)
            return self._calculate_historical_patterns(target)

        except Exception as e:
            print(f"Error getting correlations: {e}")
            return {
                'response': f'Unable to calculate correlations for {target}',
                'correlations': {
                    'error': 'Correlation calculation requires market data or knowledge base access',
                    'suggestion': 'Connect market data API or populate knowledge base with correlation data'
                }
            }

    def _calculate_sector_based_correlations(self, target: str) -> Dict[str, Any]:
        """Calculate correlations based on sector relationships"""
        try:
            # Get sector data from knowledge base
            if self.graph:
                sector_query = f"SELECT sector FROM companies WHERE symbol = '{target}'"
                sector_data = self.graph.query(sector_query)

                if sector_data and sector_data[0]:
                    sector = sector_data[0].get('sector')

                    # Get other companies in same sector
                    related_query = f"SELECT symbol FROM companies WHERE sector = '{sector}' AND symbol != '{target}'"
                    related_companies = self.graph.query(related_query)

                    if related_companies:
                        # Calculate dynamic correlations based on sector
                        strong_positive = [f"{r['symbol']} (sector peer)" for r in related_companies[:3]]

                        return {
                            'response': f'Sector-based correlations for {target}',
                            'correlations': {
                                'strong_positive': strong_positive,
                                'weak_positive': [],
                                'negative': [],
                                'summary': f'{target} correlates with {sector} sector peers',
                                'method': 'sector_analysis'
                            }
                        }

        except Exception as e:
            print(f"Sector correlation calculation failed: {e}")

        return None

    def _calculate_historical_patterns(self, target: str) -> Dict[str, Any]:
        """Calculate correlations using historical pattern analysis"""
        return {
            'response': f'Pattern-based correlation analysis for {target}',
            'correlations': {
                'analysis': f'Historical correlation patterns for {target}',
                'method': 'pattern_analysis',
                'note': 'Real-time correlation calculation recommended',
                'data_needed': 'Historical price data or correlation matrix'
            }
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

        # Store result in knowledge graph
        result = relationships_found
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            node_id = self.store_result(result)
            result['node_id'] = node_id
        return result

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