#!/usr/bin/env python3
"""
Apply Fixes Action - Apply automatic fixes for detected issues

Applies automatic fixes for agent configuration issues, particularly
constructor problems with graph initialization.

Priority: 🔧 Utility - Agent maintenance and auto-repair
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class ApplyFixesAction(ActionHandler):
    """
    Apply automatic fixes for detected issues.

    Currently supports:
    - Constructor fixes: Repair agent.graph initialization issues

    Pattern Example:
        {
            "action": "apply_fixes",
            "fixes": {
                "constructors": [
                    {"agent": "financial_analyst", "issue": "invalid_graph"}
                ]
            },
            "auto_fix": true
        }
    """

    @property
    def action_name(self) -> str:
        return "apply_fixes"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Apply automatic fixes.

        Args:
            params: Must contain 'fixes' (dict of issue types), optional 'auto_fix' (bool)
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Fix result with count and success status
        """
        fixes = params.get('fixes', {})
        auto_fix = params.get('auto_fix', False)

        if not auto_fix:
            self.logger.info("Auto-fix disabled, skipping fixes")
            return {"fixed_count": 0, "message": "Auto-fix disabled"}

        fixed_count = 0

        # Apply constructor fixes
        if 'constructors' in fixes:
            for issue in fixes['constructors']:
                if self._fix_constructor_issue(issue):
                    fixed_count += 1

        self.logger.info(f"Applied {fixed_count} fixes")

        return {
            "fixed_count": fixed_count,
            "fixes_applied": True
        }

    def _fix_constructor_issue(self, issue: dict) -> bool:
        """Fix a single constructor issue."""
        agent_name = issue.get('agent')
        if not agent_name:
            return False

        if not self.runtime or not self._has_agent(agent_name):
            self.logger.warning(f"Cannot fix {agent_name}: agent not found")
            return False

        agent = self._get_agent(agent_name)
        if not agent:
            return False

        # Fix graph initialization
        if hasattr(self.pattern_engine, 'graph') and self.pattern_engine.graph:
            agent.graph = self.pattern_engine.graph
            self.logger.info(f"Fixed constructor for {agent_name} (graph initialized)")
            return True

        return False

    def _has_agent(self, agent_name: str) -> bool:
        """Check if agent exists."""
        if hasattr(self.runtime, 'agents'):
            return agent_name in self.runtime.agents
        return False

    def _get_agent(self, agent_name: str):
        """Get agent instance."""
        if hasattr(self.runtime, 'agents'):
            return self.runtime.agents.get(agent_name)
        return None
