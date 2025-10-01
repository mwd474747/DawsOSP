import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
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