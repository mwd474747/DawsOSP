#!/usr/bin/env python3
"""
Pattern Action Handlers - Modular action execution system

This module provides a registry-based system for pattern actions, replacing the
monolithic execute_action() method with individual, testable handler classes.

Architecture:
- ActionHandler: Base class for all action handlers
- ActionRegistry: Central registry for action lookup and execution
- Individual handlers: One class per action type

Usage:
    from core.actions import ActionRegistry
    from core.actions.execute_through_registry import ExecuteThroughRegistryAction

    registry = ActionRegistry()
    handler = ExecuteThroughRegistryAction(pattern_engine)
    registry.register(handler)
    result = registry.execute('execute_through_registry', params, context, outputs)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.typing_compat import TypeAlias
import logging

logger = logging.getLogger(__name__)

# Type aliases for clarity
ParamsDict: TypeAlias = Dict[str, Any]
ContextDict: TypeAlias = Dict[str, Any]
OutputsDict: TypeAlias = Dict[str, Any]
ResultDict: TypeAlias = Dict[str, Any]
ActionName: TypeAlias = str


class ActionHandler(ABC):
    """
    Base class for all pattern action handlers.

    Each action handler encapsulates the logic for a specific pattern action,
    providing separation of concerns and improved testability.

    Attributes:
        pattern_engine: Reference to parent PatternEngine for shared resources
        graph: Knowledge graph instance
        runtime: Agent runtime instance
        knowledge_loader: Centralized knowledge loader
        logger: Logger instance for this handler
    """

    def __init__(self, pattern_engine):
        """
        Initialize action handler with pattern engine reference.

        Args:
            pattern_engine: PatternEngine instance for accessing shared resources
        """
        self.pattern_engine = pattern_engine
        self.graph = pattern_engine.graph
        self.runtime = pattern_engine.runtime
        self.knowledge_loader = pattern_engine.knowledge_loader
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def action_name(self) -> ActionName:
        """
        Return the action name for this handler.

        Returns:
            Action name string (e.g., 'knowledge_lookup', 'execute_through_registry')
        """
        pass

    @abstractmethod
    def execute(
        self,
        params: ParamsDict,
        context: ContextDict,
        outputs: OutputsDict
    ) -> ResultDict:
        """
        Execute this action with given parameters.

        Args:
            params: Action-specific parameters from pattern definition
            context: Current execution context (user_input, SYMBOL, etc.)
            outputs: Outputs from previous pattern steps

        Returns:
            Action result dictionary

        Raises:
            Exception: If action execution fails (caught by registry)
        """
        pass

    def _resolve_param(self, value: Any, context: ContextDict, outputs: OutputsDict) -> Any:
        """
        Helper method to resolve parameter variables like {user_input}, {SYMBOL}.

        This is a convenience method that delegates to the pattern engine's
        parameter resolution logic.

        Args:
            value: Parameter value (may contain variables)
            context: Current execution context
            outputs: Outputs from previous steps

        Returns:
            Resolved parameter value
        """
        if isinstance(value, str) and '{' in value:
            # Delegate to pattern engine's resolver
            resolved = self.pattern_engine._resolve_params(
                {'value': value},
                context,
                outputs
            )
            return resolved.get('value', value)
        return value


# Export base classes for external use
__all__ = [
    'ActionHandler',
    'ParamsDict',
    'ContextDict',
    'OutputsDict',
    'ResultDict',
    'ActionName'
]
