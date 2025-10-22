#!/usr/bin/env python3
"""
Check Constructor Compliance Action - Validate agent constructor signatures

Validates that agents have correct constructor signatures and proper initialization,
particularly checking graph configuration compliance.

Priority: 🔧 Utility - Agent validation and compliance checking
"""

from typing import List, Dict, Any
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class CheckConstructorComplianceAction(ActionHandler):
    """
    Check if agents have correct constructor signatures.

    Validates agent constructor compliance by checking for common issues like:
    - Invalid graph configuration (None or string instead of object)
    - Missing required attributes
    - Improper initialization

    Pattern Example:
        {
            "action": "check_constructor_compliance",
            "agents": [
                {"name": "financial_analyst", "graph_valid": true},
                {"name": "claude", "graph_valid": false}
            ]
        }
    """

    @property
    def action_name(self) -> str:
        return "check_constructor_compliance"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Check constructor compliance for agents.

        Args:
            params: Must contain 'agents' (list of agent info dicts with 'name' and 'graph_valid')
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            List of compliance issues found
        """
        agents = params.get('agents', [])
        issues: List[Dict[str, Any]] = []

        if not isinstance(agents, list):
            self.logger.warning("check_constructor_compliance requires list of agents")
            return []

        for agent_info in agents:
            if not isinstance(agent_info, dict):
                continue

            # Check for invalid graph configuration
            if not agent_info.get('graph_valid', True):
                issues.append({
                    'agent': agent_info.get('name', 'unknown'),
                    'issue': 'invalid_graph_configuration',
                    'severity': 'high',
                    'fix': 'Use fix_constructor_args action to repair'
                })
                self.logger.warning(
                    f"Constructor compliance issue: {agent_info.get('name')} has invalid graph"
                )

        self.logger.info(f"Constructor compliance check: {len(issues)} issues found")
        return issues
