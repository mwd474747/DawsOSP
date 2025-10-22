#!/usr/bin/env python3
"""
Knowledge Lookup Action - Query knowledge graph

Looks up knowledge from the graph by section/type or node ID.
Provides access to stored knowledge nodes with their properties.

Priority: 📚 Knowledge - Most frequently used knowledge action
"""

from typing import Dict, Any
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class KnowledgeLookupAction(ActionHandler):
    """
    Look up knowledge from the graph.

    Queries the knowledge graph for:
    - Nodes by type (section parameter)
    - Specific node by ID
    - All knowledge in a section

    Pattern Example:
        {
            "action": "knowledge_lookup",
            "knowledge_file": "sector_performance",
            "section": "technology"
        }
    """

    @property
    def action_name(self) -> str:
        return "knowledge_lookup"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Look up knowledge from the graph.

        Args:
            params: Must contain 'section' (node type or ID), optional 'knowledge_file'
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Knowledge data with found status and count
        """
        knowledge_file = params.get('knowledge_file', '')
        section = params.get('section', '')

        if not section:
            self.logger.warning("knowledge_lookup requires 'section' parameter")
            return {
                'data': "Section parameter is required",
                'found': False
            }

        # Try to get knowledge from graph through any agent with graph access
        if self.runtime:
            for agent_name, agent in self._iter_agents():
                if hasattr(agent, 'graph') and agent.graph is not None:
                    # Try to get nodes by type
                    nodes = self._get_nodes_by_type(agent.graph, section)
                    if nodes:
                        # Format the knowledge data
                        knowledge_data = {}
                        for node_id, node_data in nodes.items():
                            knowledge_data[node_id] = node_data.get('properties', {})

                        self.logger.info(f"Found {len(nodes)} knowledge nodes for section '{section}'")
                        return {
                            'data': knowledge_data,
                            'found': True,
                            'count': len(nodes)
                        }

                    # Try to find by ID if section matches a node ID
                    node = self._get_node(agent.graph, section)
                    if node:
                        self.logger.info(f"Found knowledge node '{section}'")
                        return {
                            'data': node.get('properties', {}),
                            'found': True,
                            'count': 1
                        }

                    # Found agent with graph, stop looking
                    break

        # Fallback if no knowledge found
        self.logger.debug(f"Knowledge section '{section}' not found in graph")
        return {
            'data': f"Knowledge section '{section}' not found in graph",
            'found': False
        }

    def _iter_agents(self):
        """Iterate through runtime agents."""
        if hasattr(self.runtime, 'agents') and isinstance(self.runtime.agents, dict):
            return self.runtime.agents.items()
        return []

    def _get_nodes_by_type(self, graph, node_type: str) -> Dict[str, Any]:
        """Get nodes by type from graph."""
        try:
            if hasattr(graph, 'get_nodes_by_type'):
                return graph.get_nodes_by_type(node_type)
        except Exception as e:
            self.logger.debug(f"Error getting nodes by type: {e}")
        return {}

    def _get_node(self, graph, node_id: str) -> Dict[str, Any]:
        """Get single node from graph."""
        try:
            if hasattr(graph, 'get_node'):
                return graph.get_node(node_id)
        except Exception as e:
            self.logger.debug(f"Error getting node: {e}")
        return None
