from agents.base_agent import BaseAgent
from typing import Dict, List
from datetime import datetime, timedelta

class PatternAgent(BaseAgent):
    """Agent for discovering and analyzing patterns"""
    
    def __init__(self, graph):
        super().__init__(
            graph,
            name="PatternAgent",
            focus_areas=['pattern', 'trend', 'cycle', 'anomaly']
        )
        self.discovered_patterns = []
    
    def discover_patterns(self) -> Dict:
        """Discover new patterns in the graph"""
        patterns = {
            'cycles': self._find_cycles(),
            'chains': self._find_chains(),
            'hubs': self._find_hubs(),
            'clusters': self._find_clusters(),
            'anomalies': self._find_anomalies(),
            'emerging': self._find_emerging_patterns()
        }
        
        # Store discovered patterns
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                self._store_pattern(pattern_type, pattern)
        
        return patterns
    
    def _find_cycles(self) -> List[Dict]:
        """Find cyclical patterns in the graph"""
        cycles = []
        visited = set()
        
        def find_cycle_from_node(start, current, path, depth):
            if depth > 5:  # Limit depth
                return
            
            if current in path[:-1]:  # Found cycle
                cycle_start = path.index(current)
                cycle = path[cycle_start:]
                if len(cycle) > 2:  # Meaningful cycle
                    cycles.append({
                        'nodes': cycle,
                        'length': len(cycle),
                        'strength': self._calculate_cycle_strength(cycle)
                    })
                return
            
            for edge in self.graph.edges:
                if edge['from'] == current and edge['to'] not in visited:
                    find_cycle_from_node(start, edge['to'], path + [edge['to']], depth + 1)
        
        # Start from each node
        for node_id in self.graph.nodes:
            if node_id not in visited:
                find_cycle_from_node(node_id, node_id, [node_id], 0)
                visited.add(node_id)
        
        return cycles[:10]  # Top 10 cycles
    
    def _find_chains(self) -> List[Dict]:
        """Find chain patterns (A→B→C→D)"""
        chains = []
        
        for node_id in self.graph.nodes:
            paths = self.graph.trace_connections(node_id, max_depth=4)
            for path in paths:
                if len(path) >= 3:  # Meaningful chain
                    chains.append({
                        'start': node_id,
                        'end': path[-1]['to'] if path else node_id,
                        'length': len(path),
                        'strength': self._calculate_path_strength(path)
                    })
        
        # Sort by strength and return top 10
        chains.sort(key=lambda x: x['strength'], reverse=True)
        return chains[:10]
    
    def _find_hubs(self) -> List[Dict]:
        """Find hub nodes (many connections)"""
        hubs = []
        
        for node_id, node in self.graph.nodes.items():
            in_count = len(node.get('connections_in', []))
            out_count = len(node.get('connections_out', []))
            total = in_count + out_count
            
            if total > 5:  # Threshold for hub
                hubs.append({
                    'node': node_id,
                    'type': node['type'],
                    'in_connections': in_count,
                    'out_connections': out_count,
                    'total_connections': total,
                    'influence_score': self._calculate_influence(node_id)
                })
        
        # Sort by total connections
        hubs.sort(key=lambda x: x['total_connections'], reverse=True)
        return hubs[:10]
    
    def _find_clusters(self) -> List[Dict]:
        """Find clusters of related nodes"""
        clusters = []
        visited = set()
        
        for node_id in self.graph.nodes:
            if node_id not in visited:
                cluster = self._build_cluster(node_id, visited)
                if len(cluster) > 3:  # Meaningful cluster
                    clusters.append({
                        'center': node_id,
                        'nodes': list(cluster),
                        'size': len(cluster),
                        'density': self._calculate_cluster_density(cluster)
                    })
        
        return clusters[:10]
    
    def _build_cluster(self, start_node: str, visited: Set[str]) -> Set[str]:
        """Build a cluster from a starting node"""
        cluster = {start_node}
        visited.add(start_node)
        
        # Find directly connected nodes
        for edge in self.graph.edges:
            if edge['from'] == start_node and edge['to'] not in visited:
                cluster.add(edge['to'])
                visited.add(edge['to'])
            elif edge['to'] == start_node and edge['from'] not in visited:
                cluster.add(edge['from'])
                visited.add(edge['from'])
        
        return cluster
    
    def _find_anomalies(self) -> List[Dict]:
        """Find anomalous patterns"""
        anomalies = []
        
        # Find nodes with unusual connection patterns
        avg_connections = len(self.graph.edges) / max(len(self.graph.nodes), 1)
        
        for node_id, node in self.graph.nodes.items():
            connections = len(node.get('connections_in', [])) + len(node.get('connections_out', []))
            
            # Anomaly if too many or too few connections
            if connections > avg_connections * 3 or connections < avg_connections * 0.2:
                anomalies.append({
                    'node': node_id,
                    'type': 'connection_anomaly',
                    'connections': connections,
                    'expected': avg_connections,
                    'deviation': abs(connections - avg_connections) / max(avg_connections, 1)
                })
        
        return anomalies[:10]
    
    def _find_emerging_patterns(self) -> List[Dict]:
        """Find emerging patterns based on recent additions"""
        emerging = []
        
        # Look at recent patterns in graph
        recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        
        for pattern_id, pattern in self.graph.patterns.items():
            if pattern.get('discovered', '') > recent_cutoff:
                emerging.append({
                    'pattern_id': pattern_id,
                    'type': pattern.get('type'),
                    'strength': pattern.get('strength', 0),
                    'discovered': pattern.get('discovered'),
                    'activations': pattern.get('activations', 0)
                })
        
        return emerging[:10]
    
    def _calculate_cycle_strength(self, cycle: List[str]) -> float:
        """Calculate strength of a cycle"""
        if not cycle:
            return 0
        
        total_strength = 0
        count = 0
        
        for i in range(len(cycle) - 1):
            for edge in self.graph.edges:
                if edge['from'] == cycle[i] and edge['to'] == cycle[i + 1]:
                    total_strength += edge.get('strength', 1.0)
                    count += 1
        
        return total_strength / max(count, 1)
    
    def _calculate_path_strength(self, path: List[Dict]) -> float:
        """Calculate strength of a path"""
        if not path:
            return 0
        
        strength = 1.0
        for edge in path:
            strength *= edge.get('strength', 1.0)
        
        return strength
    
    def _calculate_influence(self, node_id: str) -> float:
        """Calculate influence score of a node"""
        influence = 0
        
        # Outgoing influence
        for edge in self.graph.edges:
            if edge['from'] == node_id:
                influence += edge.get('strength', 1.0)
        
        # Incoming influence (weighted less)
        for edge in self.graph.edges:
            if edge['to'] == node_id:
                influence += edge.get('strength', 1.0) * 0.5
        
        return influence
    
    def _calculate_cluster_density(self, cluster: Set[str]) -> float:
        """Calculate density of connections within cluster"""
        if len(cluster) < 2:
            return 0
        
        internal_edges = 0
        for edge in self.graph.edges:
            if edge['from'] in cluster and edge['to'] in cluster:
                internal_edges += 1
        
        # Maximum possible edges
        max_edges = len(cluster) * (len(cluster) - 1)
        
        return internal_edges / max_edges if max_edges > 0 else 0
    
    def _store_pattern(self, pattern_type: str, pattern: Dict):
        """Store discovered pattern in graph"""
        pattern_id = f"pattern_{pattern_type}_{datetime.now().timestamp()}"
        
        self.graph.add_node(
            node_type='pattern',
            data={
                'pattern_type': pattern_type,
                'pattern': pattern,
                'discovered_by': self.name
            },
            node_id=pattern_id
        )
        
        self.discovered_patterns.append(pattern_id)