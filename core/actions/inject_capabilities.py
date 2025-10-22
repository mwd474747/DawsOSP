#!/usr/bin/env python3
"""
Inject Capabilities Action - Add capability metadata to context

Injects required capabilities from the capability registry into the execution
context, enabling capability-aware pattern execution.

Priority: 🔧 Utility - Capability-based routing support
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class InjectCapabilitiesAction(ActionHandler):
    """
    Inject required capabilities into execution context.

    Adds capability metadata from the capability registry to the context,
    enabling patterns to access capability information during execution.
    Used for capability-based routing and validation.

    Pattern Example:
        {
            "action": "inject_capabilities",
            "agent": "financial_analyst",
            "required": ["can_calculate_dcf", "can_analyze_financials"],
            "context": "{current_context}"
        }
    """

    @property
    def action_name(self) -> str:
        return "inject_capabilities"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Inject capabilities into context.

        Args:
            params: Must contain 'required' (list of capability names), optional 'context'
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Enhanced context dictionary with capability metadata
        """
        agent_name = params.get('agent')
        required = params.get('required', [])
        injection_context = params.get('context', context.copy())

        if not isinstance(injection_context, dict):
            self.logger.warning("inject_capabilities requires dict context, using empty dict")
            injection_context = {}

        injected_count = 0

        # Add capabilities to context if available
        if hasattr(self.pattern_engine, 'capabilities'):
            capabilities = self.pattern_engine.capabilities
            for cap in required:
                if cap in capabilities:
                    injection_context[f'capability_{cap}'] = capabilities[cap]
                    injected_count += 1
                    self.logger.debug(f"Injected capability '{cap}' into context")
                else:
                    self.logger.warning(f"Capability '{cap}' not found in registry")

        self.logger.debug(f"Injected {injected_count}/{len(required)} capabilities")

        return injection_context

    def _resolve_context(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ContextDict:
        """Resolve context parameter (may reference outputs)."""
        ctx = params.get('context')
        if isinstance(ctx, str):
            return self._resolve_param(ctx, context, outputs)
        return ctx or context.copy()
