#!/usr/bin/env python3
"""
Execute Through Registry Action - Trinity-compliant agent execution

This is the most critical action in the pattern system, ensuring all agent
executions go through the AgentRegistry for proper tracking, compliance
monitoring, and Trinity Architecture enforcement.

Priority: ⭐ CRITICAL - Most frequently used action
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict
from core.capability_router import CapabilityRouter


class ExecuteThroughRegistryAction(ActionHandler):
    """
    Execute agent through runtime registry (Trinity compliance).

    This action enforces Trinity Architecture by routing all agent executions
    through the AgentRegistry, which provides:
    - Execution tracking and metrics
    - Compliance monitoring
    - Graph storage automation
    - Proper error handling

    Pattern Example:
        {
            "action": "execute_through_registry",
            "agent": "financial_analyst",
            "context": {
                "symbol": "{user_input}",
                "request": "analyze {SYMBOL}"
            }
        }
    """

    # Data capabilities that should route to CapabilityRouter
    DATA_CAPABILITIES = {
        'can_fetch_stock_quotes',
        'can_fetch_economic_data',
        'can_fetch_fundamentals',
        'can_fetch_news',
        'can_calculate_risk_metrics',
        'can_fetch_crypto_data'
    }

    def __init__(self, pattern_engine):
        """Initialize action handler with CapabilityRouter"""
        super().__init__(pattern_engine)
        self._capability_router = None

    @property
    def capability_router(self):
        """Lazy-load CapabilityRouter (singleton pattern)"""
        if self._capability_router is None:
            self._capability_router = CapabilityRouter(use_real_data=True)  # ✅ FIXED: Use real data (not mock)
        return self._capability_router

    @property
    def action_name(self) -> str:
        return "execute_through_registry"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Execute agent via registry for Trinity compliance.

        Args:
            params: Must contain 'agent' OR 'capability', optional 'method', 'context'
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Agent execution result

        Raises:
            ValueError: If runtime not available or routing parameter missing
        """
        # Extract parameters - support both agent and capability routing
        agent_name = params.get('agent')
        capability = params.get('capability')
        method = params.get('method', 'process')  # Default method (legacy)
        agent_context = params.get('context', {})

        # Validation - require either agent or capability
        if not agent_name and not capability:
            self.logger.error("execute_through_registry requires 'agent' or 'capability' parameter")
            return {"error": "'agent' or 'capability' parameter is required"}

        if not self.runtime:
            self.logger.error("Runtime not available for execute_through_registry")
            return {"error": "Runtime not available"}

        # Resolve context variables
        if agent_context:
            # Allow context to reference pattern context/outputs
            resolved_context = {}
            for key, value in agent_context.items():
                resolved_context[key] = self._resolve_param(value, context, outputs)
            agent_context = resolved_context
        else:
            # Use pattern context as default
            agent_context = context

        # Execute through registry (Trinity-compliant)
        try:
            # Route by capability if provided (modern pattern style)
            if capability:
                # WEEK 6 ENHANCEMENT: Route data capabilities to CapabilityRouter
                if capability in self.DATA_CAPABILITIES:
                    self.logger.debug(f"Routing data capability '{capability}' to CapabilityRouter")
                    result = self.capability_router.route(capability, agent_context)
                    self.logger.debug(f"Data capability '{capability}' execution completed")
                    return result

                # Route analysis capabilities to agents (via runtime)
                # CRITICAL: Add capability to context for AgentAdapter introspection
                agent_context['capability'] = capability
                self.logger.debug(f"Executing analysis capability '{capability}' via runtime")
                result = self.runtime.execute_by_capability(capability, agent_context)
                self.logger.debug(f"Capability '{capability}' execution completed")
                return result

            # Route by agent name (legacy pattern style)
            # Prefer execute_with_tracking if available (full Trinity compliance)
            if hasattr(self.runtime, 'agent_registry'):
                self.logger.debug(
                    f"Executing '{agent_name}' through registry with tracking"
                )
                result = self.runtime.agent_registry.execute_with_tracking(
                    agent_name,
                    agent_context
                )
            else:
                # Fallback to basic execute (still goes through runtime)
                self.logger.debug(
                    f"Executing '{agent_name}' through runtime (no tracking)"
                )
                result = self.runtime.execute(agent_name, agent_context)

            self.logger.debug(f"Agent '{agent_name}' execution completed")
            return result

        except Exception as e:
            self.logger.error(
                f"Agent execution failed: {agent_name}",
                exc_info=True,
                extra={
                    'agent': agent_name,
                    'context': agent_context
                }
            )
            return {
                "error": f"Agent execution failed: {str(e)}",
                "agent": agent_name
            }
