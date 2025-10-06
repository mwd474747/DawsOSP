#!/usr/bin/env python3
"""
Fix Constructor Args Action - Auto-fix agent constructor issues

Dynamically fixes agent constructor argument issues, particularly for agents
with incorrect graph configuration (string instead of object reference).

Priority: 🔧 Utility - Agent maintenance and auto-repair
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class FixConstructorArgsAction(ActionHandler):
    """
    Fix agent constructor arguments on the fly.

    Detects and repairs common constructor issues like incorrect graph
    configuration (string vs object). Used for dynamic agent repair during
    pattern execution.

    Pattern Example:
        {
            "action": "fix_constructor_args",
            "agent": "financial_analyst"
        }
    """

    @property
    def action_name(self) -> str:
        return "fix_constructor_args"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Fix agent constructor arguments.

        Args:
            params: Must contain 'agent' (agent name to fix)
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Dictionary with fix status and details
        """
        agent_name = params.get('agent')

        if not self.runtime or not self._has_agent(agent_name):
            return {"fixed": False, "agent": agent_name, "error": "Agent not found"}

        agent = self._get_agent(agent_name)

        # Check for string graph issue (common constructor problem)
        if hasattr(agent, 'graph') and isinstance(agent.graph, str):
            # Graph is incorrectly a string, fix it
            if hasattr(self.pattern_engine, 'graph'):
                agent.graph = self.pattern_engine.graph
                agent.name = agent_name
                self.logger.info(f"Fixed constructor args for agent '{agent_name}' (graph was string)")
                return {
                    "fixed": True,
                    "agent": agent_name,
                    "issue": "constructor_args",
                    "detail": "Replaced string graph with object reference"
                }

        # No issues found
        return {"fixed": False, "agent": agent_name, "reason": "No issues detected"}

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
