#!/usr/bin/env python3
"""
Execute By Capability Action - Direct capability-based routing for patterns

This action enables patterns to route execution by capability without specifying
agent names, making patterns more flexible and maintainable.

Priority: ⭐ HIGH - New Trinity 2.0 capability-based routing
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class ExecuteByCapabilityAction(ActionHandler):
    """
    Execute agent by capability (Trinity 2.0 capability-based routing).

    This action allows patterns to specify a capability instead of an agent name,
    enabling more flexible agent selection and graceful degradation.

    Pattern Example:
        {
            "action": "execute_by_capability",
            "capability": "can_calculate_dcf",
            "context": {
                "symbol": "{user_input}",
                "projection_years": 5
            }
        }

    Advantages over execute_through_registry:
    - More flexible: Any agent with the capability can execute
    - Better degradation: Automatic fallback to alternative agents
    - Easier maintenance: Agents can be swapped without changing patterns
    """

    @property
    def action_name(self) -> str:
        return "execute_by_capability"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Execute agent via capability routing (Trinity 2.0).

        Args:
            params: Must contain 'capability', optional 'context'
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Agent execution result from first matching capable agent

        Raises:
            ValueError: If runtime not available or capability missing
        """
        # Extract parameters
        capability = params.get('capability')
        agent_context = params.get('context', {})

        # Validation
        if not capability:
            self.logger.error("execute_by_capability requires 'capability' parameter")
            return {"error": "'capability' parameter is required"}

        if not self.runtime:
            self.logger.error("Runtime not available for execute_by_capability")
            return {"error": "Runtime not available"}

        # Resolve context variables
        if agent_context:
            resolved_context = {}
            for key, value in agent_context.items():
                resolved_context[key] = self._resolve_param(value, context, outputs)
            agent_context = resolved_context
        else:
            # Use pattern context as default
            agent_context = context

        # Add capability to context for agent introspection
        agent_context['capability'] = capability

        # Execute through capability-based routing (Trinity 2.0)
        try:
            self.logger.debug(f"Executing by capability: '{capability}'")

            # Use runtime's execute_by_capability method
            result = self.runtime.execute_by_capability(capability, agent_context)

            # Check if capability was found
            if result.get('error') and 'not found' in result.get('error', '').lower():
                self.logger.warning(f"No agent found with capability '{capability}'")
                return {
                    "error": f"No agent found with capability: {capability}",
                    "capability": capability,
                    "suggestion": "Check AGENT_CAPABILITIES for available capabilities"
                }

            self.logger.debug(f"Capability '{capability}' execution completed successfully")
            return result

        except Exception as e:
            self.logger.error(
                f"Capability execution failed: {capability}",
                exc_info=True,
                extra={
                    'capability': capability,
                    'context': agent_context
                }
            )
            return {
                "error": f"Capability execution failed: {str(e)}",
                "capability": capability
            }
