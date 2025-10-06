#!/usr/bin/env python3
"""
Scan Agents Action - Enumerate all registered agents

Scans the runtime registry and returns metadata about all registered agents,
including graph configuration status and class information.

Priority: 🔧 Utility - Agent discovery and introspection
"""

from typing import List, Dict, Any
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class ScanAgentsAction(ActionHandler):
    """
    Scan all registered agents in the runtime.

    Enumerates agents and collects metadata including:
    - Agent name and class
    - Graph configuration status
    - Initialization state

    Pattern Example:
        {
            "action": "scan_agents"
        }
    """

    @property
    def action_name(self) -> str:
        return "scan_agents"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Scan all agents in the runtime.

        Args:
            params: No required parameters
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            List of agent metadata dictionaries
        """
        if not self.runtime:
            self.logger.warning("Runtime not available for scan_agents")
            return []

        agents: List[Dict[str, Any]] = []

        # Iterate through all registered agents
        for name, agent in self._iter_agents():
            agent_info = {
                'name': name,
                'class': agent.__class__.__name__,
                'has_graph': hasattr(agent, 'graph'),
                'graph_valid': self._check_graph_valid(agent)
            }
            agents.append(agent_info)

        self.logger.info(f"Scanned {len(agents)} agents")
        return agents

    def _iter_agents(self):
        """Iterate through runtime agents."""
        if hasattr(self.runtime, 'agents') and isinstance(self.runtime.agents, dict):
            return self.runtime.agents.items()
        return []

    def _check_graph_valid(self, agent) -> bool:
        """Check if agent has valid graph configuration."""
        return (
            hasattr(agent, 'graph') and
            agent.graph is not None and
            not isinstance(agent.graph, str)
        )
