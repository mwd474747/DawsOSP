#!/usr/bin/env python3
"""
Enriched Lookup Action - Query enriched knowledge data

Looks up enriched data from Phase 3 JSON files or graph nodes.
Supports graph node queries, dataset lookups, and section extraction.

Priority: 📚 Knowledge - Second most frequently used knowledge action
"""

from typing import Any
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class EnrichedLookupAction(ActionHandler):
    """
    Look up enriched data from JSON files or graph nodes.

    Supports multiple lookup modes:
    - graph_nodes: Get all nodes of a specific type
    - graph_node: Get single node by ID
    - Standard: Load enriched dataset from storage/knowledge/

    Pattern Example:
        {
            "action": "enriched_lookup",
            "data_type": "sector_performance",
            "query": "technology"
        }
    """

    @property
    def action_name(self) -> str:
        return "enriched_lookup"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Look up enriched data from files or graph.

        Args:
            params: Must contain 'data_type', optional 'query'
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Enriched data with found status and metadata
        """
        data_type = params.get('data_type', '')
        query = params.get('query', '')

        if not data_type:
            self.logger.warning("enriched_lookup requires 'data_type' parameter")
            return {
                'data': "data_type parameter is required",
                'found': False
            }

        # Special handling for graph node lookups
        if data_type == "graph_nodes":
            return self._lookup_graph_nodes(query)
        elif data_type == "graph_node":
            return self._lookup_graph_node(query)

        # Standard enriched data lookup via KnowledgeLoader
        enriched_data = self._load_enriched_data(data_type)

        if enriched_data:
            # Extract specific query if provided
            if query:
                result = self._extract_enriched_section(enriched_data, query, params)
                return result
            else:
                self.logger.info(f"Loaded enriched data '{data_type}'")
                return {
                    'data': enriched_data,
                    'found': True,
                    'source': data_type
                }

        self.logger.debug(f"Enriched data '{data_type}' not found")
        return {
            'data': f"Enriched data '{data_type}' not found",
            'found': False
        }

    def _lookup_graph_nodes(self, node_type: str) -> ResultDict:
        """Get all graph nodes of a specific type."""
        if not self.graph:
            return {'data': [], 'found': False, 'error': 'Graph not available'}

        try:
            # Access graph nodes via @property (returns copy for safety)
            all_nodes = self.graph.nodes
            nodes = [
                {'id': nid, **ndata}
                for nid, ndata in all_nodes.items()
                if ndata.get('type') == node_type
            ]

            self.logger.info(f"Found {len(nodes)} graph nodes of type '{node_type}'")
            return {
                'data': nodes,
                'found': len(nodes) > 0,
                'count': len(nodes),
                'type': node_type
            }
        except Exception as e:
            self.logger.error(f"Error looking up graph nodes: {e}", exc_info=True)
            return {'data': [], 'found': False, 'error': str(e)}

    def _lookup_graph_node(self, node_id: str) -> ResultDict:
        """Get single graph node by ID."""
        if not self.graph:
            return {'data': None, 'found': False, 'error': 'Graph not available'}

        if not node_id:
            return {'data': None, 'found': False, 'error': 'node_id required'}

        try:
            # Access graph nodes via @property (safe read-only access)
            all_nodes = self.graph.nodes
            if node_id in all_nodes:
                self.logger.info(f"Found graph node '{node_id}'")
                return {
                    'data': {'id': node_id, **all_nodes[node_id]},
                    'found': True
                }
        except Exception as e:
            self.logger.error(f"Error looking up graph node: {e}", exc_info=True)
            return {'data': None, 'found': False, 'error': str(e)}

        return {'data': None, 'found': False}

    def _load_enriched_data(self, data_type: str) -> Any:
        """Load enriched data via PatternEngine's loader."""
        try:
            # Use PatternEngine's load_enriched_data method if available
            if hasattr(self.pattern_engine, 'load_enriched_data'):
                return self.pattern_engine.load_enriched_data(data_type)

            # Fallback: use KnowledgeLoader directly
            if self.knowledge_loader:
                return self.knowledge_loader.get_dataset(data_type)

        except Exception as e:
            self.logger.error(f"Error loading enriched data '{data_type}': {e}", exc_info=True)

        return None

    def _extract_enriched_section(self, enriched_data: Any, query: str, params: ParamsDict) -> ResultDict:
        """Extract specific section from enriched data."""
        try:
            # Use PatternEngine's extract method if available
            if hasattr(self.pattern_engine, 'extract_enriched_section'):
                return self.pattern_engine.extract_enriched_section(enriched_data, query, params)

            # Fallback: simple dict lookup
            if isinstance(enriched_data, dict) and query in enriched_data:
                return {
                    'data': enriched_data[query],
                    'found': True,
                    'query': query
                }

        except Exception as e:
            self.logger.error(f"Error extracting section '{query}': {e}", exc_info=True)

        return {
            'data': f"Section '{query}' not found in enriched data",
            'found': False
        }
