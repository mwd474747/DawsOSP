#!/usr/bin/env python3
"""
Store In Graph Action - Persist results to knowledge graph

Stores pattern execution results in the knowledge graph for future reference
and relationship building.
"""

from datetime import datetime
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class StoreInGraphAction(ActionHandler):
    """
    Store execution results in the knowledge graph.

    Creates nodes and relationships in the graph to persist pattern execution
    results, enabling knowledge accumulation and relationship discovery.

    Pattern Example:
        {
            "action": "store_in_graph",
            "node_type": "analysis",
            "data": "{step_1.result}",
            "connect_to": "{SYMBOL}"
        }
    """

    @property
    def action_name(self) -> str:
        return "store_in_graph"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Store data in knowledge graph.

        Args:
            params: Must contain 'node_type' and 'data', optional 'connect_to', 'relationship'
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Dictionary with node_id and storage status
        """
        if not self.graph:
            self.logger.warning("Graph not available for store_in_graph action")
            return {"error": "Graph not available", "stored": False}

        # Extract parameters
        node_type = self._resolve_param(params.get('node_type', 'pattern_result'), context, outputs)
        data = self._resolve_param(params.get('data'), context, outputs)
        connect_to = self._resolve_param(params.get('connect_to'), context, outputs)
        relationship = params.get('relationship', 'generated_by')
        node_id = params.get('node_id')  # Optional specific ID

        if not data:
            self.logger.warning("No data provided to store_in_graph")
            return {"error": "No data to store", "stored": False}

        try:
            # Prepare node data
            if not isinstance(data, dict):
                # Wrap non-dict data
                node_data = {
                    'value': data,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'pattern_execution'
                }
            else:
                node_data = data.copy()
                if 'timestamp' not in node_data:
                    node_data['timestamp'] = datetime.now().isoformat()
                if 'source' not in node_data:
                    node_data['source'] = 'pattern_execution'

            # Add context metadata
            if 'user_input' in context:
                node_data['context'] = {'user_input': context['user_input']}

            # Create node
            created_node_id = self.graph.add_node(node_type, node_data, node_id=node_id)
            self.logger.debug(f"Stored node '{created_node_id}' of type '{node_type}' in graph")

            result = {
                "stored": True,
                "node_id": created_node_id,
                "node_type": node_type
            }

            # Create relationship if requested
            if connect_to:
                # connect_to might be a node ID or need to be found
                target_node_id = None

                # Try as direct node ID first
                if self.graph.get_node(connect_to):
                    target_node_id = connect_to
                else:
                    # Try to find node by querying
                    matches = self.graph.query({'data.symbol': connect_to})
                    if matches:
                        target_node_id = matches[0]

                if target_node_id:
                    self.graph.connect(
                        created_node_id,
                        target_node_id,
                        relationship,
                        strength=1.0
                    )
                    self.logger.debug(
                        f"Connected '{created_node_id}' to '{target_node_id}' "
                        f"via '{relationship}'"
                    )
                    result["connected_to"] = target_node_id
                    result["relationship"] = relationship
                else:
                    self.logger.warning(
                        f"Could not find target node for connection: {connect_to}"
                    )
                    result["connection_failed"] = connect_to

            return result

        except Exception as e:
            self.logger.error(f"Failed to store in graph: {e}", exc_info=True)
            return {
                "error": f"Storage failed: {str(e)}",
                "stored": False
            }
