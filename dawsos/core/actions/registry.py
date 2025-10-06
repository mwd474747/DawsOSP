#!/usr/bin/env python3
"""
Action Registry - Central registry for pattern action handlers

Provides O(1) lookup and execution of action handlers, with proper error
handling and logging. Supports both the new handler-based system and
fallback to legacy execute_action for gradual migration.
"""

from typing import Dict, List, Any
import logging

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict, ActionName

logger = logging.getLogger(__name__)


class ActionRegistry:
    """
    Registry for all pattern action handlers.

    Maintains a dictionary of action_name -> ActionHandler mappings for fast
    lookup and execution. Provides proper error handling and logging for all
    action executions.

    Example:
        registry = ActionRegistry()
        registry.register(ExecuteThroughRegistryAction(pattern_engine))
        result = registry.execute('execute_through_registry', params, context, outputs)
    """

    def __init__(self):
        """Initialize empty action registry."""
        self.handlers: Dict[ActionName, ActionHandler] = {}
        logger.debug("ActionRegistry initialized")

    def register(self, handler: ActionHandler) -> None:
        """
        Register an action handler.

        Args:
            handler: ActionHandler instance to register

        Raises:
            Warning: If overwriting an existing handler (logged, not raised)
        """
        action_name = handler.action_name

        if action_name in self.handlers:
            logger.warning(
                f"Overwriting existing handler for action '{action_name}' "
                f"(old: {self.handlers[action_name].__class__.__name__}, "
                f"new: {handler.__class__.__name__})"
            )

        self.handlers[action_name] = handler
        logger.debug(f"Registered action handler: '{action_name}' ({handler.__class__.__name__})")

    def unregister(self, action_name: ActionName) -> bool:
        """
        Unregister an action handler.

        Args:
            action_name: Name of action to unregister

        Returns:
            True if handler was unregistered, False if not found
        """
        if action_name in self.handlers:
            handler = self.handlers.pop(action_name)
            logger.debug(f"Unregistered action handler: '{action_name}' ({handler.__class__.__name__})")
            return True
        else:
            logger.warning(f"Attempted to unregister unknown action: '{action_name}'")
            return False

    def has_action(self, action_name: ActionName) -> bool:
        """
        Check if an action is registered.

        Args:
            action_name: Name of action to check

        Returns:
            True if action is registered, False otherwise
        """
        return action_name in self.handlers

    def execute(
        self,
        action_name: ActionName,
        params: ParamsDict,
        context: ContextDict,
        outputs: OutputsDict
    ) -> ResultDict:
        """
        Execute an action by name.

        Args:
            action_name: Name of action to execute
            params: Action-specific parameters
            context: Current execution context
            outputs: Outputs from previous steps

        Returns:
            Action result dictionary

        Raises:
            ValueError: If action_name is not registered
            Exception: Any exception from action execution (logged and returned as error)
        """
        # Check if action exists
        handler = self.handlers.get(action_name)
        if not handler:
            error_msg = f"Unknown action: '{action_name}'"
            logger.error(f"{error_msg}. Available actions: {self.list_actions()}")
            raise ValueError(error_msg)

        # Execute action with error handling
        try:
            logger.debug(f"Executing action '{action_name}' via {handler.__class__.__name__}")
            result = handler.execute(params, context, outputs)
            logger.debug(f"Action '{action_name}' completed successfully")
            return result

        except Exception as e:
            logger.error(
                f"Action '{action_name}' failed: {e}",
                exc_info=True,
                extra={
                    'action': action_name,
                    'handler': handler.__class__.__name__,
                    'params': params
                }
            )
            # Return error result instead of raising (graceful degradation)
            return {
                'error': str(e),
                'action': action_name,
                'handler': handler.__class__.__name__,
                'params': params
            }

    def list_actions(self) -> List[ActionName]:
        """
        List all registered action names.

        Returns:
            Sorted list of registered action names
        """
        return sorted(self.handlers.keys())

    def get_handler(self, action_name: ActionName) -> ActionHandler:
        """
        Get the handler instance for an action.

        Args:
            action_name: Name of action

        Returns:
            ActionHandler instance

        Raises:
            KeyError: If action not registered
        """
        return self.handlers[action_name]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats (count, handlers)
        """
        return {
            'total_actions': len(self.handlers),
            'actions': self.list_actions(),
            'handlers': {
                name: handler.__class__.__name__
                for name, handler in self.handlers.items()
            }
        }

    def __len__(self) -> int:
        """Return number of registered actions."""
        return len(self.handlers)

    def __contains__(self, action_name: ActionName) -> bool:
        """Check if action is registered (supports 'in' operator)."""
        return action_name in self.handlers

    def __repr__(self) -> str:
        """String representation of registry."""
        return f"ActionRegistry({len(self.handlers)} actions: {self.list_actions()})"
