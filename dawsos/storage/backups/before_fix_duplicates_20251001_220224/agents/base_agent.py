from typing import Dict, List, Any
from datetime import datetime
import json

class BaseAgent:
    """Base class for all specialized agents"""

    def __init__(self, graph, name: str = None, focus_areas: List[str] = None, llm_client=None):
        self.graph = graph  # Shared knowledge graph
        self.name = name or self.__class__.__name__
        self.focus_areas = focus_areas or []
        self.memory = []  # Agent-specific memory
        self.llm_client = llm_client  # For LLM-based agents

    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method - called by runtime"""
        # Default implementation - override in subclasses
        user_input = context.get('user_input', context.get('request', ''))

        # Try process method if it exists
        if hasattr(self, 'process'):
            return self.process(user_input)

        # Otherwise use analyze
        analysis = self.analyze(user_input)
        return {
            'response': str(analysis),
            'data': analysis
        }
        
    def analyze(self, query: str) -> Dict:
        """Base analysis method - override in subclasses"""
        # Find relevant nodes
        relevant_nodes = self._find_relevant_nodes(query)
        
        # Trace connections
        insights = []
        for node_id in relevant_nodes:
            connections = self.graph.trace_connections(node_id, max_depth=2)
            if connections:
                insights.append({
                    'node': node_id,
                    'connections': len(connections),
                    'patterns': self._analyze_patterns(connections)
                })
        
        return {
            'agent': self.name,
            'query': query,
            'relevant_nodes': relevant_nodes,
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        }
    
    def _find_relevant_nodes(self, query: str) -> List[str]:
        """Find nodes relevant to the query"""
        relevant = []
        query_lower = query.lower()
        keywords = query_lower.split()
        
        for node_id, node in self.graph.nodes.items():
            # Check if node type matches focus areas
            if node['type'] in self.focus_areas:
                relevant.append(node_id)
                continue
            
            # Check if query mentions node
            node_text = f"{node_id} {node['type']} {json.dumps(node.get('data', {}))}".lower()
            if any(keyword in node_text for keyword in keywords):
                relevant.append(node_id)
        
        return list(set(relevant))[:20]  # Limit to 20 most relevant
    
    def _analyze_patterns(self, connections: List[List[Dict]]) -> Dict:
        """Analyze patterns in connections"""
        patterns = {
            'strong_paths': 0,
            'weak_paths': 0,
            'cycles': 0,
            'chains': 0
        }
        
        for path in connections:
            if not path:
                continue
                
            # Calculate path strength
            path_strength = 1.0
            for edge in path:
                path_strength *= edge.get('strength', 1.0)
            
            if path_strength > 0.6:
                patterns['strong_paths'] += 1
            else:
                patterns['weak_paths'] += 1
            
            # Check for cycles
            nodes_in_path = [edge['from'] for edge in path] + [path[-1]['to']] if path else []
            if len(nodes_in_path) != len(set(nodes_in_path)):
                patterns['cycles'] += 1
            
            # Count chains
            if len(path) > 2:
                patterns['chains'] += 1
        
        return patterns
    
    def forecast(self, target: str, horizon: str = '1d') -> Dict:
        """Forecast using graph connections"""
        return self.graph.forecast(target, horizon)
    
    def add_knowledge(self, node_type: str, data: Dict, node_id: str = None) -> str:
        """Add knowledge to the graph"""
        return self.graph.add_node(node_type, data, node_id)
    
    def connect_knowledge(self, from_id: str, to_id: str, 
                          relationship: str, strength: float = 1.0) -> bool:
        """Connect knowledge in the graph"""
        return self.graph.connect(from_id, to_id, relationship, strength)