"""RelationshipHunter - Finds connections between nodes"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Tuple

class RelationshipHunter(BaseAgent):
    """Hunts for relationships between nodes"""

    def __init__(self, graph, llm_client=None):
        super().__init__("RelationshipHunter", graph, llm_client)
        self.vibe = "curious"

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
        else:
            data = {}
            target = 'SPY'

        # Return mock correlations for testing
        return {
            'response': f'Found correlations for {target}',
            'correlations': {
                'strong_positive': ['QQQ (0.85)', 'IWM (0.78)'],
                'weak_positive': ['TLT (0.35)', 'VXX (0.25)'],
                'negative': ['DXY (-0.45)', 'GLD (-0.35)'],
                'summary': f'{target} shows strong correlation with tech indices'
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