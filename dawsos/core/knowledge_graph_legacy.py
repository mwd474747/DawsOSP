import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
class KnowledgeGraph:
    """The living intelligence - stores all knowledge and relationships"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.patterns = {}
        self.forecasts = {}
        self.version = 1
        
    def add_node(self, node_type: str, data: dict, node_id: str = None) -> str:
        """Add a knowledge node to the graph"""
        if not node_id:
            node_id = f"{node_type}_{uuid.uuid4().hex[:8]}"
            
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'data': data,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'connections_in': [],
            'connections_out': [],
            'metadata': {
                'access_count': 0,
                'last_accessed': None,
                'confidence': 1.0
            }
        }
        return node_id
    
    def connect(self, from_id: str, to_id: str, 
                relationship: str, strength: float = 1.0, 
                metadata: dict = None) -> bool:
        """Create a connection between nodes"""
        if from_id not in self.nodes or to_id not in self.nodes:
            return False
            
        edge = {
            'id': f"edge_{uuid.uuid4().hex[:8]}",
            'from': from_id,
            'to': to_id,
            'type': relationship,
            'strength': max(0.0, min(1.0, strength)),  # Clamp between 0 and 1
            'metadata': metadata or {},
            'created': datetime.now().isoformat(),
            'activations': 0
        }
        
        self.edges.append(edge)
        
        # Update node connections
        self.nodes[from_id]['connections_out'].append(edge['id'])
        self.nodes[to_id]['connections_in'].append(edge['id'])
        
        # Discover transitive patterns
        self._discover_patterns(from_id, to_id, relationship)
        
        return True
    
    def trace_connections(self, start_node: str, 
                         max_depth: int = 3, 
                         min_strength: float = 0.3) -> List[List[Dict]]:
        """Trace all paths from a node"""
        if start_node not in self.nodes:
            return []
            
        paths = []
        visited = set()
        
        def trace(node: str, path: List[Dict], depth: int):
            if depth > max_depth or node in visited:
                return
                
            visited.add(node)
            
            for edge in self.edges:
                if edge['from'] == node and edge['strength'] >= min_strength:
                    new_path = path + [edge]
                    paths.append(new_path)
                    trace(edge['to'], new_path, depth + 1)
            
            visited.remove(node)
        
        trace(start_node, [], 0)
        return paths
    
    def forecast(self, target_node: str, horizon: str = '1d') -> dict:
        """Forecast future state using all connections"""
        if target_node not in self.nodes:
            return {'error': f'Node {target_node} not found'}
            
        # Find all influences
        influences = []
        influence_nodes = set()
        
        # Direct influences
        for edge in self.edges:
            if edge['to'] == target_node:
                influences.append({
                    'path': [edge],
                    'direct': True,
                    'strength': edge['strength']
                })
                influence_nodes.add(edge['from'])
        
        # Indirect influences (2nd degree)
        for node in influence_nodes:
            for edge in self.edges:
                if edge['to'] == node:
                    # Found 2nd degree influence
                    first_edge = next(e for e in self.edges 
                                     if e['from'] == node and e['to'] == target_node)
                    influences.append({
                        'path': [edge, first_edge],
                        'direct': False,
                        'strength': edge['strength'] * first_edge['strength']
                    })
        
        # Calculate weighted forecast
        positive_signal = 0
        negative_signal = 0
        total_weight = 0
        
        for influence in influences:
            strength = influence['strength']
            # Check relationship type for direction
            rel_type = influence['path'][-1]['type']
            
            if rel_type in ['causes', 'correlates', 'supports']:
                positive_signal += strength
            elif rel_type in ['inverse', 'pressures', 'weakens']:
                negative_signal += strength
            
            total_weight += strength
        
        # Generate forecast
        if total_weight > 0:
            net_signal = (positive_signal - negative_signal) / total_weight
            confidence = min(total_weight / 5, 1.0)  # More connections = higher confidence
        else:
            net_signal = 0
            confidence = 0
        
        # Store forecast
        forecast_id = f"forecast_{target_node}_{datetime.now().timestamp()}"
        self.forecasts[forecast_id] = {
            'target': target_node,
            'horizon': horizon,
            'signal': net_signal,
            'confidence': confidence,
            'positive_factors': positive_signal,
            'negative_factors': negative_signal,
            'influence_count': len(influences),
            'created': datetime.now().isoformat()
        }
        
        return {
            'target': target_node,
            'forecast': 'bullish' if net_signal > 0.2 else 'bearish' if net_signal < -0.2 else 'neutral',
            'signal_strength': abs(net_signal),
            'confidence': confidence,
            'key_drivers': self._get_key_drivers(influences),
            'influences': len(influences)
        }
    
    def _discover_patterns(self, from_node: str, to_node: str, relationship: str):
        """Discover transitive and emergent patterns"""
        # If A→B and B→C exists, infer A→C
        for edge in self.edges:
            if edge['from'] == to_node:
                pattern_key = f"{from_node}_to_{edge['to']}"
                if pattern_key not in self.patterns:
                    self.patterns[pattern_key] = {
                        'type': 'transitive',
                        'from': from_node,
                        'to': edge['to'],
                        'via': to_node,
                        'strength': 0.7,  # Weakened transitive strength
                        'discovered': datetime.now().isoformat(),
                        'activations': 0
                    }
        
        # Check for cycles
        for edge in self.edges:
            if edge['from'] == to_node and edge['to'] == from_node:
                cycle_key = f"cycle_{from_node}_{to_node}"
                if cycle_key not in self.patterns:
                    self.patterns[cycle_key] = {
                        'type': 'cycle',
                        'nodes': [from_node, to_node],
                        'discovered': datetime.now().isoformat()
                    }
    
    def _get_key_drivers(self, influences: List[Dict]) -> List[Dict]:
        """Extract the most important influences"""
        sorted_influences = sorted(influences, 
                                  key=lambda x: x['strength'], 
                                  reverse=True)
        
        key_drivers = []
        for inf in sorted_influences[:5]:  # Top 5
            path_description = []
            for edge in inf['path']:
                from_node = self.nodes.get(edge['from'], {})
                to_node = self.nodes.get(edge['to'], {})
                path_description.append({
                    'from': edge['from'],
                    'to': edge['to'],
                    'relationship': edge['type'],
                    'strength': edge['strength']
                })
            
            key_drivers.append({
                'path': path_description,
                'impact': inf['strength'],
                'direct': inf['direct']
            })
        
        return key_drivers
    
    def query(self, pattern: dict) -> List[str]:
        """Query nodes matching a pattern"""
        results = []
        
        for node_id, node in self.nodes.items():
            match = True
            
            # Check type
            if 'type' in pattern and node['type'] != pattern['type']:
                match = False
            
            # Check data attributes
            if 'data' in pattern:
                for key, value in pattern['data'].items():
                    if key not in node['data'] or node['data'][key] != value:
                        match = False
                        break
            
            # Check connections
            if 'has_connection_to' in pattern:
                has_connection = any(
                    edge['to'] == pattern['has_connection_to'] 
                    for edge in self.edges if edge['from'] == node_id
                )
                if not has_connection:
                    match = False
            
            if match:
                results.append(node_id)
                
        return results
    
    def get_stats(self) -> dict:
        """Get graph statistics"""
        node_types = {}
        for node in self.nodes.values():
            node_types[node['type']] = node_types.get(node['type'], 0) + 1

        edge_types = {}
        for edge in self.edges:
            edge_types[edge['type']] = edge_types.get(edge['type'], 0) + 1

        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'total_patterns': len(self.patterns),
            'node_types': node_types,
            'edge_types': edge_types,
            'avg_connections': len(self.edges) / max(len(self.nodes), 1)
        }

    def get_node(self, node_id: str) -> Optional[Dict]:
        """
        Get a single node by ID safely.

        Args:
            node_id: The ID of the node to retrieve

        Returns:
            Node data dictionary or None if not found
        """
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: str) -> Dict[str, Dict]:
        """
        Get all nodes of a specific type.

        Args:
            node_type: The type of nodes to retrieve

        Returns:
            Dictionary of {node_id: node_data} for nodes matching the type
        """
        return {node_id: node_data for node_id, node_data in self.nodes.items()
                if node_data.get('type') == node_type}

    def has_edge(self, from_id: str, to_id: str, relationship: Optional[str] = None) -> bool:
        """
        Check if an edge exists between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relationship: Optional relationship type to check for

        Returns:
            True if edge exists, False otherwise
        """
        for edge in self.edges:
            if edge['from'] == from_id and edge['to'] == to_id:
                if relationship is None or edge['type'] == relationship:
                    return True
        return False

    def get_edge(self, from_id: str, to_id: str, relationship: Optional[str] = None) -> Optional[Dict]:
        """
        Get edge data between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relationship: Optional relationship type filter

        Returns:
            Edge dictionary or None if not found
        """
        for edge in self.edges:
            if edge['from'] == from_id and edge['to'] == to_id:
                if relationship is None or edge['type'] == relationship:
                    return edge
        return None

    def safe_query(self, pattern: dict, default: Any = None) -> List[str]:
        """
        Query nodes with safe fallback.

        Args:
            pattern: Query pattern dictionary
            default: Default value if query fails or returns empty

        Returns:
            List of matching node IDs or default value
        """
        try:
            results = self.query(pattern)
            return results if results else (default if default is not None else [])
        except Exception as e:
            print(f"Query failed: {e}")
            return default if default is not None else []

    def get_node_data(self, node_id: str, key: str, default: Any = None) -> Any:
        """
        Safely get data from a node.

        Args:
            node_id: Node ID to query
            key: Data key to retrieve
            default: Default value if node or key not found

        Returns:
            Node data value or default
        """
        node = self.get_node(node_id)
        if node and 'data' in node:
            return node['data'].get(key, default)
        return default

    def get_connected_nodes(self, node_id: str, direction: str = 'out',
                           relationship: Optional[str] = None) -> List[str]:
        """
        Get all nodes connected to a given node.

        Args:
            node_id: Source node ID
            direction: 'out' for outgoing, 'in' for incoming, 'both' for all
            relationship: Optional relationship type filter

        Returns:
            List of connected node IDs
        """
        connected = []

        if direction in ['out', 'both']:
            for edge in self.edges:
                if edge['from'] == node_id:
                    if relationship is None or edge['type'] == relationship:
                        connected.append(edge['to'])

        if direction in ['in', 'both']:
            for edge in self.edges:
                if edge['to'] == node_id:
                    if relationship is None or edge['type'] == relationship:
                        connected.append(edge['from'])

        return connected

    def save(self, filepath: str = 'storage/graph.json'):
        """Save graph to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump({
                'version': self.version,
                'nodes': self.nodes,
                'edges': self.edges,
                'patterns': self.patterns,
                'forecasts': self.forecasts,
                'metadata': {
                    'last_saved': datetime.now().isoformat(),
                    'stats': self.get_stats()
                }
            }, f, indent=2)
    
    def load(self, filepath: str = 'storage/graph.json'):
        """Load graph from file"""
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.version = data.get('version', 1)
                self.nodes = data.get('nodes', {})
                self.edges = data.get('edges', [])
                self.patterns = data.get('patterns', {})
                self.forecasts = data.get('forecasts', {})
            return True
        except Exception as e:
            print(f"Error loading graph: {e}")
            return False

    def sample_for_visualization(self, max_nodes: int = 500, strategy: str = 'importance') -> Dict:
        """
        Sample graph for visualization to handle large graphs (96K+ nodes)

        Args:
            max_nodes: Maximum number of nodes to include
            strategy: Sampling strategy - 'importance', 'recent', 'random', or 'connected'

        Returns:
            Dict with sampled nodes and edges suitable for visualization
        """
        import random

        total_nodes = len(self.nodes)

        # If graph is small enough, return all
        if total_nodes <= max_nodes:
            return {
                'nodes': self.nodes,
                'edges': self.edges,
                'sampled': False,
                'total_nodes': total_nodes,
                'total_edges': len(self.edges)
            }

        # Sample nodes based on strategy
        if strategy == 'importance':
            # Sort by access count and connection degree
            node_scores = {}
            for node_id, node in self.nodes.items():
                access_count = node.get('metadata', {}).get('access_count', 0)
                connections = len(node.get('connections_in', [])) + len(node.get('connections_out', []))
                node_scores[node_id] = access_count + connections

            sampled_ids = sorted(node_scores.keys(), key=lambda x: node_scores[x], reverse=True)[:max_nodes]

        elif strategy == 'recent':
            # Sort by most recently modified
            sampled_ids = sorted(
                self.nodes.keys(),
                key=lambda x: self.nodes[x].get('modified', ''),
                reverse=True
            )[:max_nodes]

        elif strategy == 'connected':
            # Start with most connected node and expand
            sampled_ids = set()
            # Find most connected node
            if self.nodes:
                start_node = max(
                    self.nodes.keys(),
                    key=lambda x: len(self.nodes[x].get('connections_in', [])) + len(self.nodes[x].get('connections_out', []))
                )
                sampled_ids.add(start_node)

                # BFS expansion
                queue = [start_node]
                while queue and len(sampled_ids) < max_nodes:
                    current = queue.pop(0)
                    node = self.nodes[current]

                    for neighbor in node.get('connections_out', []):
                        if neighbor not in sampled_ids and len(sampled_ids) < max_nodes:
                            sampled_ids.add(neighbor)
                            queue.append(neighbor)

                    for neighbor in node.get('connections_in', []):
                        if neighbor not in sampled_ids and len(sampled_ids) < max_nodes:
                            sampled_ids.add(neighbor)
                            queue.append(neighbor)

            sampled_ids = list(sampled_ids)

        else:  # random
            sampled_ids = random.sample(list(self.nodes.keys()), min(max_nodes, total_nodes))

        # Build sampled nodes
        sampled_nodes = {node_id: self.nodes[node_id] for node_id in sampled_ids}

        # Build sampled edges (only edges between sampled nodes)
        sampled_edges = [
            edge for edge in self.edges
            if edge['from'] in sampled_ids and edge['to'] in sampled_ids
        ]

        return {
            'nodes': sampled_nodes,
            'edges': sampled_edges,
            'sampled': True,
            'total_nodes': total_nodes,
            'total_edges': len(self.edges),
            'sampled_nodes': len(sampled_nodes),
            'sampled_edges': len(sampled_edges),
            'strategy': strategy
        }