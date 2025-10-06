#!/usr/bin/env python3
"""
Select Router Action - Determine optimal routing strategy

Analyzes request structure to determine optimal routing strategy
(pattern, agent, or direct). Part of Trinity Architecture meta-patterns.

Priority: 🎯 Routing - Trinity Architecture compliance
"""

from datetime import datetime
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class SelectRouterAction(ActionHandler):
    """
    Determine optimal routing strategy for request.

    Analyzes request to select routing strategy:
    - pattern: Pattern-driven execution (Trinity-compliant, preferred)
    - agent: Direct agent execution
    - direct: Direct method call

    Returns routing decision with strategy, reason, and metadata.

    Pattern Example:
        {
            "action": "select_router",
            "request": "{user_request}"
        }
    """

    @property
    def action_name(self) -> str:
        return "select_router"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Determine optimal routing strategy.

        Args:
            params: Must contain 'request' (dict or string)
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Routing decision with strategy, reason, and timestamp
        """
        request = params.get('request', {})
        request_type = request.get('type', 'unknown') if isinstance(request, dict) else 'unknown'

        # Simple routing logic (no creep - just functional)
        routing_decision = {
            'strategy': 'pattern',  # Default to pattern-driven
            'reason': 'Trinity compliance',
            'timestamp': datetime.now().isoformat()
        }

        if not isinstance(request, dict):
            self.logger.debug("Request not a dict, defaulting to pattern strategy")
            return routing_decision

        # Check if specific agent requested
        if 'agent' in request:
            routing_decision['strategy'] = 'agent'
            routing_decision['agent_name'] = request['agent']
            routing_decision['reason'] = 'Explicit agent request'

        # Check if pattern match exists
        elif 'pattern' in request or 'pattern_id' in request:
            routing_decision['strategy'] = 'pattern'
            routing_decision['pattern_id'] = request.get('pattern') or request.get('pattern_id')
            routing_decision['reason'] = 'Pattern-driven execution'

        # Check for user_input that might match pattern triggers
        elif 'user_input' in request:
            matched_pattern = self._find_pattern(request['user_input'])
            if matched_pattern:
                routing_decision['strategy'] = 'pattern'
                routing_decision['pattern_id'] = matched_pattern.get('id')
                routing_decision['reason'] = 'Pattern trigger match'
            else:
                routing_decision['strategy'] = 'agent'
                routing_decision['agent_name'] = 'claude'  # Default orchestrator
                routing_decision['reason'] = 'No pattern match, route to claude'

        self.logger.debug(
            f"Routing decision: {routing_decision['strategy']} "
            f"({routing_decision['reason']})"
        )

        return routing_decision

    def _find_pattern(self, user_input: str):
        """Find matching pattern for user input."""
        try:
            if hasattr(self.pattern_engine, 'find_pattern'):
                return self.pattern_engine.find_pattern(user_input)
        except Exception as e:
            self.logger.debug(f"Pattern matching failed: {e}")
        return None
