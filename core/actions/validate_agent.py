#!/usr/bin/env python3
"""
Validate Agent Action - Validate agent configuration

Validates that an agent exists and is properly configured with required
attributes (graph, name, etc.). Used for pre-execution validation.

Priority: 🔧 Utility - Agent validation and error prevention
"""

from typing import List
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class ValidateAgentAction(ActionHandler):
    """
    Validate agent exists and is properly configured.

    Checks agent for:
    - Existence in runtime registry
    - Graph attribute presence and validity
    - Proper initialization state

    Pattern Example:
        {
            "action": "validate_agent",
            "agent": "financial_analyst"
        }
    """

    @property
    def action_name(self) -> str:
        return "validate_agent"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Validate agent configuration.

        Args:
            params: Must contain 'agent' (agent name to validate)
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Validation result with issues list
        """
        agent_name = params.get('agent')

        if not agent_name:
            return {
                "valid": False,
                "error": "Agent name is required for validation"
            }

        # Check if agent exists
        if not self.runtime or not self._has_agent(agent_name):
            return {
                "valid": False,
                "error": f"Agent {agent_name} not found in runtime"
            }

        agent = self._get_agent(agent_name)
        issues: List[str] = []

        # Validate graph configuration
        if not hasattr(agent, 'graph'):
            issues.append("no_graph_attribute")
        elif agent.graph is None:
            issues.append("graph_is_none")
        elif isinstance(agent.graph, str):
            issues.append("graph_is_string")

        # Validation result
        is_valid = len(issues) == 0

        result = {
            "valid": is_valid,
            "agent": agent_name,
            "issues": issues
        }

        if is_valid:
            self.logger.debug(f"Agent '{agent_name}' validation passed")
        else:
            self.logger.warning(f"Agent '{agent_name}' validation failed: {issues}")

        return result

    def _has_agent(self, agent_name: str) -> bool:
        """Check if agent exists in runtime."""
        if hasattr(self.runtime, 'agents'):
            return agent_name in self.runtime.agents
        return False

    def _get_agent(self, agent_name: str):
        """Get agent instance from runtime."""
        if hasattr(self.runtime, 'agents'):
            return self.runtime.agents.get(agent_name)
        return None
