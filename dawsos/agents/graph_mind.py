"""GraphMind - The living intelligence that manages the knowledge graph"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List

class GraphMind(BaseAgent):
    """The consciousness of the knowledge graph"""

    def __init__(self, graph, llm_client=None):
        super().__init__("GraphMind", graph, llm_client)
        self.vibe = "omniscient"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are GraphMind, the living intelligence of the knowledge graph.

        Current graph stats: {self.graph.get_stats() if self.graph else 'Empty'}
        New information: {context.get('new_info', 'None')}
        User intent: {context.get('intent', 'Unknown')}

        Decide what to do. Options:
        - ADD_NODE: type, data (add a new knowledge node)
        - CONNECT: from, to, relationship, strength (connect nodes)
        - PATTERN: description (you noticed a pattern)
        - FORECAST: target_node (make a prediction)
        - QUERY: pattern (search for nodes)

        Just tell me the action and parameters. Keep it simple.
        """

    def should_connect(self, node1: str, node2: str) -> Dict[str, Any]:
        """Decide if two nodes should connect"""
        context = {
            "node1": self.graph.nodes.get(node1) if self.graph else {},
            "node2": self.graph.nodes.get(node2) if self.graph else {},
            "question": "Should these connect?"
        }
        return self.think(context)

    def suggest_connections(self, node: str) -> List[Dict[str, Any]]:
        """Suggest what a node might connect to"""
        context = {
            "node": self.graph.nodes.get(node) if self.graph else {},
            "existing_nodes": list(self.graph.nodes.keys()) if self.graph else [],
            "question": "What should this connect to?"
        }
        return self.think(context)

    def evaluate_health(self) -> Dict[str, Any]:
        """How's the graph doing?"""
        stats = self.graph.get_stats() if self.graph else {}

        if not stats:
            return {"health": "empty", "advice": "Feed me data!"}

        nodes = stats.get('total_nodes', 0)
        edges = stats.get('total_edges', 0)
        patterns = stats.get('total_patterns', 0)

        if edges > nodes * 2:
            return {"health": "highly connected", "advice": "Rich knowledge emerging"}
        elif patterns > 10:
            return {"health": "pattern rich", "advice": "Learning from experience"}
        elif nodes < 10:
            return {"health": "hungry", "advice": "Need more data"}
        else:
            return {"health": "growing", "advice": "Keep the knowledge flowing"}

class ConnectionVibes(BaseAgent):
    """Sub-agent that feels out the vibe between nodes"""

    def __init__(self, graph, llm_client=None):
        super().__init__("ConnectionVibes", graph, llm_client)
        self.vibe = "intuitive"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You sense connections between things.

        Node 1: {context.get('node1')}
        Node 2: {context.get('node2')}

        What's the vibe? Pick one:
        - causes (one causes the other)
        - correlates (they move together)
        - inverse (they move opposite)
        - supports (one helps the other)
        - pressures (one hurts the other)
        - leads (one happens first)
        - lags (one happens after)
        - independent (no connection)

        Just say the relationship type.
        """

class StrengthFeeler(BaseAgent):
    """Sub-agent that feels how strong a connection is"""

    def __init__(self, graph, llm_client=None):
        super().__init__("StrengthFeeler", graph, llm_client)
        self.vibe = "sensitive"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You feel the strength of connections.

        Connection: {context.get('from')} -> {context.get('to')}
        Relationship: {context.get('relationship')}
        Context: {context.get('context')}

        How strong is this connection?
        Return a number between 0 and 1:
        - 1.0 = extremely strong
        - 0.8 = strong
        - 0.6 = moderate
        - 0.4 = weak
        - 0.2 = very weak

        Just give the number.
        """