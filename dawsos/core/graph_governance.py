#!/usr/bin/env python3
"""
Graph-Native Governance - Simple, powerful governance using knowledge graph relationships
Extends the existing KnowledgeGraph to make governance a first-class citizen
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class GraphGovernance:
    """Simple graph-based governance that leverages existing architecture"""

    def __init__(self, knowledge_graph):
        self.graph = knowledge_graph
        self._init_governance_nodes()

    def _init_governance_nodes(self):
        """Initialize core governance node types in the graph"""
        # Define governance node types (but don't require a central registry)
        self.governance_types = [
            'data_policy',      # What rules apply
            'quality_metric',   # How good is the data
            'lineage_trace',    # Where data flows
            'governance_alert'  # What needs attention
        ]
        # These types are simply used when creating nodes, no central registry needed

    def add_governance_policy(self, name: str, rule: str, applies_to: List[str]) -> str:
        """Add a simple governance policy that watches specific nodes"""
        policy_id = self.graph.add_node('data_policy', {
            'name': name,
            'rule': rule,
            'active': True,
            'violations': 0
        })

        # Connect policy to what it governs
        for target in applies_to:
            if target in self.graph.nodes:
                self.graph.connect(policy_id, target, 'governs', strength=1.0)

        return policy_id

    def check_governance(self, node_id: str) -> Dict[str, Any]:
        """Simple governance check - what policies apply to this node?"""
        if node_id not in self.graph.nodes:
            return {'status': 'not_found'}

        # Find all policies governing this node
        policies = []
        for edge in self.graph.edges:
            if edge['to'] == node_id and edge['type'] == 'governs':
                policy = self.graph.nodes[edge['from']]
                if policy['type'] == 'data_policy':
                    policies.append({
                        'policy': policy['data']['name'],
                        'rule': policy['data']['rule'],
                        'active': policy['data']['active']
                    })

        # Check data quality through relationships
        quality_score = self._calculate_quality_from_graph(node_id)

        return {
            'node': node_id,
            'policies': policies,
            'quality_score': quality_score,
            'governance_status': 'compliant' if quality_score > 0.7 else 'needs_attention'
        }

    def _calculate_quality_from_graph(self, node_id: str) -> float:
        """Calculate data quality based on graph relationships"""
        node = self.graph.nodes[node_id]

        # Quality based on:
        # 1. Number of connections (more connections = more validated)
        connections = len(node.get('connections_in', [])) + len(node.get('connections_out', []))
        connection_score = min(connections / 10, 1.0)  # Max out at 10 connections

        # 2. Age of data (newer = better)
        age_hours = (datetime.now() - datetime.fromisoformat(node['modified'])).total_seconds() / 3600
        age_score = max(0, 1.0 - (age_hours / 168))  # Decay over a week

        # 3. Relationship strength (stronger relationships = better quality)
        avg_strength = 0
        strength_count = 0
        for edge in self.graph.edges:
            if edge['from'] == node_id or edge['to'] == node_id:
                avg_strength += edge.get('strength', 0.5)
                strength_count += 1

        strength_score = avg_strength / strength_count if strength_count > 0 else 0.5

        # Weighted average
        quality_score = (connection_score * 0.3 + age_score * 0.3 + strength_score * 0.4)

        return round(quality_score, 2)

    def trace_data_lineage(self, node_id: str, max_depth: int = 5) -> List[List[str]]:
        """Trace data lineage through graph relationships"""
        if node_id not in self.graph.nodes:
            return []

        lineage_paths = []
        visited = set()

        def trace_path(current_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)
            current_path = path + [current_id]

            # Find upstream nodes (data sources)
            has_upstream = False
            for edge in self.graph.edges:
                if edge['to'] == current_id and edge['type'] in ['flows_to', 'feeds', 'influences']:
                    has_upstream = True
                    trace_path(edge['from'], current_path, depth + 1)

            # If no upstream, this is a source
            if not has_upstream and len(current_path) > 1:
                lineage_paths.append(current_path)

        trace_path(node_id, [], 0)
        return lineage_paths

    def auto_govern(self, request: str) -> Dict[str, Any]:
        """Simple conversational governance using graph structure"""
        request_lower = request.lower()

        # Parse intent
        if 'quality' in request_lower:
            # Find nodes mentioned in request
            nodes_to_check = self._extract_nodes_from_request(request)
            results = []

            for node_id in nodes_to_check:
                gov_result = self.check_governance(node_id)
                results.append(gov_result)

            return {
                'action': 'quality_check',
                'results': results,
                'summary': self._summarize_quality_results(results)
            }

        elif 'lineage' in request_lower or 'flow' in request_lower:
            nodes_to_trace = self._extract_nodes_from_request(request)
            lineage_results = {}

            for node_id in nodes_to_trace:
                lineage_results[node_id] = self.trace_data_lineage(node_id)

            return {
                'action': 'lineage_trace',
                'lineage': lineage_results,
                'summary': f"Traced {len(lineage_results)} data lineage paths"
            }

        elif 'policy' in request_lower or 'rule' in request_lower:
            # Add a new governance policy
            if 'add' in request_lower or 'create' in request_lower:
                # Extract policy details from request
                policy_name = f"Policy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                rule = request  # Use the request as the rule description

                # Find nodes to apply to
                applies_to = self._extract_nodes_from_request(request)
                if not applies_to:
                    # Apply to all financial data nodes
                    applies_to = [n for n, data in self.graph.nodes.items()
                                if data['type'] in ['stock', 'indicator', 'sector']][:10]

                policy_id = self.add_governance_policy(policy_name, rule, applies_to)

                return {
                    'action': 'add_policy',
                    'policy_id': policy_id,
                    'applies_to': applies_to,
                    'summary': f"Added governance policy to {len(applies_to)} nodes"
                }

        # Default: comprehensive governance check
        all_governance = self.comprehensive_governance_check()
        return all_governance

    def comprehensive_governance_check(self) -> Dict[str, Any]:
        """Run comprehensive governance check across the graph"""
        results = {
            'total_nodes': len(self.graph.nodes),
            'total_edges': len(self.graph.edges),
            'governance_policies': 0,
            'quality_issues': [],
            'lineage_gaps': [],
            'overall_health': 0.0
        }

        quality_scores = []

        for node_id, node in self.graph.nodes.items():
            # Check each node's governance
            gov_check = self.check_governance(node_id)
            quality_scores.append(gov_check['quality_score'])

            if gov_check['quality_score'] < 0.5:
                results['quality_issues'].append({
                    'node': node_id,
                    'score': gov_check['quality_score'],
                    'type': node['type']
                })

            # Count policies
            results['governance_policies'] += len(gov_check['policies'])

        # Calculate overall health
        results['overall_health'] = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0

        # Check for orphan nodes (lineage gaps)
        for node_id, node in self.graph.nodes.items():
            incoming = len(node.get('connections_in', []))
            outgoing = len(node.get('connections_out', []))

            if incoming == 0 and outgoing == 0:
                results['lineage_gaps'].append({
                    'node': node_id,
                    'type': node['type'],
                    'issue': 'orphan_node'
                })

        return results

    def _extract_nodes_from_request(self, request: str) -> List[str]:
        """Extract node IDs mentioned in the request"""
        nodes = []

        # Look for known node patterns
        for node_id, node in self.graph.nodes.items():
            if node_id.lower() in request.lower():
                nodes.append(node_id)
            elif 'data' in node and isinstance(node['data'], dict):
                # Check if node name/symbol is mentioned
                if 'symbol' in node['data'] and node['data']['symbol'].lower() in request.lower():
                    nodes.append(node_id)
                elif 'name' in node['data'] and node['data']['name'].lower() in request.lower():
                    nodes.append(node_id)

        return nodes[:10]  # Limit to 10 nodes

    def _summarize_quality_results(self, results: List[Dict]) -> str:
        """Create human-readable summary of quality results"""
        if not results:
            return "No quality data available"

        avg_quality = sum(r['quality_score'] for r in results) / len(results)
        compliant = sum(1 for r in results if r['governance_status'] == 'compliant')

        return (f"Checked {len(results)} nodes: "
                f"Average quality {avg_quality:.0%}, "
                f"{compliant}/{len(results)} compliant")


    def evolve_graph(self, auto_execute: bool = False) -> Dict[str, Any]:
        """Graph evolves based on quality and usage patterns"""
        evolution_actions = []

        for node_id, node in self.graph.nodes.items():
            quality = self._calculate_quality_from_graph(node_id)

            # Weak nodes get marked for refresh
            if quality < 0.3:
                evolution_actions.append({
                    'action': 'refresh_node',
                    'target': node_id,
                    'reason': f'Low quality score: {quality:.0%}',
                    'priority': 'high'
                })

                if auto_execute:
                    # Add governance event for auto-refresh
                    self.graph.add_node('governance_event', {
                        'action': 'refresh_required',
                        'target': node_id,
                        'quality_score': quality,
                        'auto_execute': True,
                        'timestamp': datetime.now().isoformat()
                    })

            # Strong nodes strengthen their connections
            elif quality > 0.8:
                for edge in self.graph.edges:
                    if edge['from'] == node_id or edge['to'] == node_id:
                        # Strengthen good relationships
                        old_strength = edge.get('strength', 0.5)
                        edge['strength'] = min(1.0, old_strength * 1.1)

                        if old_strength != edge['strength']:
                            evolution_actions.append({
                                'action': 'strengthen_edge',
                                'from': edge['from'],
                                'to': edge['to'],
                                'old_strength': old_strength,
                                'new_strength': edge['strength']
                            })

        # Auto-prune very weak edges
        original_edge_count = len(self.graph.edges)
        self.graph.edges = [e for e in self.graph.edges if e.get('strength', 0.5) > 0.1]
        pruned_count = original_edge_count - len(self.graph.edges)

        if pruned_count > 0:
            evolution_actions.append({
                'action': 'prune_edges',
                'count': pruned_count,
                'reason': 'Strength below threshold (0.1)'
            })

        return {
            'evolved': True,
            'actions_taken': evolution_actions,
            'summary': {
                'nodes_flagged_for_refresh': len([a for a in evolution_actions if a.get('action') == 'refresh_node']),
                'edges_strengthened': len([a for a in evolution_actions if a.get('action') == 'strengthen_edge']),
                'edges_pruned': pruned_count
            }
        }


def integrate_graph_governance(knowledge_graph) -> GraphGovernance:
    """Simple integration function"""
    return GraphGovernance(knowledge_graph)