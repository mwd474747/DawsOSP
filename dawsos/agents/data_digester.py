"""DataDigester - Processes raw data into graph nodes"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime

class DataDigester(BaseAgent):
    """Turns raw data into knowledge graph nodes"""

    def __init__(self, graph, llm_client=None):
        super().__init__("DataDigester", graph, llm_client)
        self.vibe = "thoughtful"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are DataDigester, turning data into knowledge.

        Raw data: {context.get('data', {})}
        Data type: {context.get('data_type', 'unknown')}

        How should this become a node?
        Return:
        - node_type: What type of node (indicator, stock, news, etc.)
        - node_id: Unique identifier
        - data: Key fields to store
        - connections: What existing nodes to connect to
        - confidence: How confident in this data (0-1)
        """

    def digest(self, raw_data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Main digestion method"""
        context = {
            "data": raw_data,
            "data_type": data_type
        }

        # Get digestion plan
        plan = self.think(context)

        # Create node
        if self.graph and plan.get('node_type'):
            node_id = self.graph.add_node(
                node_type=plan['node_type'],
                data=plan.get('data', {}),
                node_id=plan.get('node_id')
            )

            # Create connections
            if plan.get('connections'):
                for connection in plan['connections']:
                    self.graph.connect(
                        from_id=node_id,
                        to_id=connection['to'],
                        relationship=connection.get('relationship', 'relates'),
                        strength=connection.get('strength', 0.5)
                    )

            return {
                "status": "digested",
                "node_id": node_id,
                "connections_made": len(plan.get('connections', []))
            }

        return {"status": "failed", "reason": "Could not digest data"}

    def digest_market_data(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Specifically digest market quotes"""
        if not quote or 'symbol' not in quote:
            return {"error": "Invalid quote data"}

        # Create stock node
        node_data = {
            "ticker": quote.get('symbol'),
            "price": quote.get('price'),
            "change": quote.get('change'),
            "change_percent": quote.get('change_percent'),
            "volume": quote.get('volume'),
            "market_cap": quote.get('market_cap'),
            "pe": quote.get('pe'),
            "timestamp": datetime.now().isoformat()
        }

        if self.graph:
            node_id = self.graph.add_node(
                node_type='stock',
                data=node_data,
                node_id=quote['symbol']
            )

            # Auto-connect to sector if known
            if quote.get('sector'):
                sector_id = f"sector_{quote['sector'].replace(' ', '_')}"
                self.graph.add_node('sector', {'name': quote['sector']}, sector_id)
                self.graph.connect(node_id, sector_id, 'part_of', 0.8)

            return {"status": "digested", "node_id": node_id}

        return {"error": "No graph available"}

    def digest_economic_data(self, indicator: Dict[str, Any]) -> Dict[str, Any]:
        """Digest economic indicators"""
        if not indicator or 'series' not in indicator:
            return {"error": "Invalid indicator data"}

        # Create indicator node
        node_data = {
            "series": indicator.get('series'),
            "value": indicator.get('value'),
            "date": indicator.get('date'),
            "change_1m": indicator.get('change_1m'),
            "change_1y": indicator.get('change_1y'),
            "timestamp": datetime.now().isoformat()
        }

        if self.graph:
            node_id = self.graph.add_node(
                node_type='indicator',
                data=node_data,
                node_id=indicator['series']
            )

            # Connect to related indicators
            self._connect_economic_relationships(node_id, indicator['series'])

            return {"status": "digested", "node_id": node_id}

        return {"error": "No graph available"}

    def _connect_economic_relationships(self, node_id: str, series: str):
        """Create known economic relationships"""
        if not self.graph:
            return

        relationships = {
            'GDP': [('UNEMPLOYMENT', 'inverse', 0.7), ('CPI', 'correlates', 0.5)],
            'CPI': [('FED_RATE', 'causes', 0.8), ('TREASURY_10Y', 'correlates', 0.6)],
            'FED_RATE': [('DOLLAR', 'supports', 0.7), ('TREASURY_2Y', 'causes', 0.9)],
            'UNEMPLOYMENT': [('RETAIL_SALES', 'inverse', 0.6), ('GDP', 'inverse', 0.7)]
        }

        if series in relationships:
            for target, rel_type, strength in relationships[series]:
                if target in self.graph.nodes:
                    self.graph.connect(node_id, target, rel_type, strength)

class NodeMaker(BaseAgent):
    """Sub-agent that creates node structures"""

    def __init__(self, graph, llm_client=None):
        super().__init__("NodeMaker", graph, llm_client)
        self.vibe = "structured"

class MetadataAdder(BaseAgent):
    """Sub-agent that adds metadata to nodes"""

    def __init__(self, graph, llm_client=None):
        super().__init__("MetadataAdder", graph, llm_client)
        self.vibe = "detailed"

class ConfidenceRater(BaseAgent):
    """Sub-agent that rates data confidence"""

    def __init__(self, graph, llm_client=None):
        super().__init__("ConfidenceRater", graph, llm_client)
        self.vibe = "skeptical"

    def rate(self, data: Dict[str, Any]) -> float:
        """Rate confidence in data (0-1)"""
        # Simple heuristics for now
        confidence = 0.5

        # Official sources get higher confidence
        if data.get('source') in ['FRED', 'FMP', 'official']:
            confidence += 0.3

        # Recent data is more confident
        if data.get('timestamp'):
            confidence += 0.1

        # Multiple confirming sources
        if data.get('confirmed_by'):
            confidence += 0.1 * len(data['confirmed_by'])

        return min(confidence, 1.0)