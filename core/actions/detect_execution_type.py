#!/usr/bin/env python3
"""
Detect Execution Type Action - Classify request execution strategy

Analyzes request structure to determine optimal execution type (agent direct,
pattern-driven, UI action, API call, or legacy bypass).

Priority: 🎯 Routing - Critical for Trinity Architecture compliance
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class DetectExecutionTypeAction(ActionHandler):
    """
    Detect execution type from request structure.

    Classifies requests into execution categories:
    - agent_direct: Direct agent execution request
    - pattern: Pattern-driven execution (preferred)
    - ui_action: UI component action
    - api_call: API endpoint invocation
    - legacy: Legacy bypass (needs migration)
    - unknown: Unable to classify

    Pattern Example:
        {
            "action": "detect_execution_type",
            "request": "{user_request}"
        }
    """

    @property
    def action_name(self) -> str:
        return "detect_execution_type"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Detect execution type from request.

        Args:
            params: Must contain 'request' (request dict or string)
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            String indicating execution type
        """
        request = self._resolve_param(params.get('request', {}), context, outputs)

        # Check for specific request patterns
        if isinstance(request, dict):
            # Agent direct execution
            if 'agent_name' in request:
                self.logger.debug("Detected execution type: agent_direct")
                return 'agent_direct'

            # Pattern-driven (Trinity-compliant)
            elif 'pattern_id' in request or 'pattern' in request:
                self.logger.debug("Detected execution type: pattern")
                return 'pattern'

            # UI component action
            elif 'ui_component' in request:
                self.logger.debug("Detected execution type: ui_action")
                return 'ui_action'

            # API endpoint call
            elif 'api' in request or 'endpoint' in request:
                self.logger.debug("Detected execution type: api_call")
                return 'api_call'

        # Check for legacy bypass indicators (needs migration)
        request_str = str(request)
        legacy_indicators = ['_direct', 'bypass', 'analyze', 'harvest']
        if any(indicator in request_str for indicator in legacy_indicators):
            self.logger.warning("Detected execution type: legacy (bypass detected)")
            return 'legacy'

        # Unable to classify
        self.logger.debug("Detected execution type: unknown")
        return 'unknown'
