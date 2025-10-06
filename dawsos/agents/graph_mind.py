"""GraphMind - The living intelligence that manages the knowledge graph

Phase 3.1: Added comprehensive type hints for better type safety.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional, TypeAlias

# Type aliases for clarity
ContextDict: TypeAlias = Dict[str, Any]
ResultDict: TypeAlias = Dict[str, Any]
ConnectionList: TypeAlias = List[Dict[str, Any]]
NodeStats: TypeAlias = Dict[str, Any]

class GraphMind(BaseAgent):
    """The consciousness of the knowledge graph"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize GraphMind with graph and optional LLM client.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client for generation
        """
        super().__init__(graph=graph, name="GraphMind", llm_client=llm_client)
        self.vibe: str = "omniscient"

    def get_prompt(self, context: ContextDict) -> str:
        """Generate prompt for graph operations.

        Args:
            context: Dictionary with new_info and intent

        Returns:
            Formatted prompt string
        """
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

    def should_connect(self, node1: str, node2: str) -> ResultDict:
        """Decide if two nodes should connect.

        Args:
            node1: First node ID
            node2: Second node ID

        Returns:
            Dictionary with connection decision
        """
        context = {
            "node1": self.graph.nodes.get(node1) if self.graph else {},
            "node2": self.graph.nodes.get(node2) if self.graph else {},
            "question": "Should these connect?"
        }
        return self.think(context)

    def suggest_connections(self, node: str) -> ConnectionList:
        """Suggest what a node might connect to.

        Args:
            node: Node ID to suggest connections for

        Returns:
            List of suggested connection dictionaries
        """
        context = {
            "node": self.graph.nodes.get(node) if self.graph else {},
            "existing_nodes": list(self.list(graph._graph.nodes())) if self.graph else [],
            "question": "What should this connect to?"
        }
        return self.think(context)

    def evaluate_health(self) -> NodeStats:
        """How's the graph doing?

        Returns:
            Dictionary with health status and advice
        """
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

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize ConnectionVibes with graph and optional LLM client.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("ConnectionVibes", graph, llm_client)
        self.vibe: str = "intuitive"

    def get_prompt(self, context: ContextDict) -> str:
        """Generate prompt for connection type detection.

        Args:
            context: Dictionary with node1 and node2

        Returns:
            Formatted prompt string
        """
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

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize StrengthFeeler with graph and optional LLM client.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("StrengthFeeler", graph, llm_client)
        self.vibe: str = "sensitive"

    def get_prompt(self, context: ContextDict) -> str:
        """Generate prompt for connection strength evaluation.

        Args:
            context: Dictionary with from, to, relationship, context

        Returns:
            Formatted prompt string
        """
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