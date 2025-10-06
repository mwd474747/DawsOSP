#!/usr/bin/env python3
"""
Execute Pattern Action - Execute nested patterns

Executes a pattern by ID with given context. Handles nested pattern
execution with recursion guard to prevent infinite loops.

Priority: 🎯 Meta - Nested pattern execution
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class ExecutePatternAction(ActionHandler):
    """
    Execute a pattern by ID with given context.

    Handles nested pattern execution with:
    - Recursion guard (max depth 5)
    - Parent pattern tracking
    - Context inheritance
    - Error handling

    Pattern Example:
        {
            "action": "execute_pattern",
            "pattern_id": "financial_analysis",
            "context": "{current_context}"
        }
    """

    @property
    def action_name(self) -> str:
        return "execute_pattern"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Execute a pattern by ID.

        Args:
            params: Must contain 'pattern_id', optional 'context'
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Pattern execution result with nested_execution flag
        """
        pattern_id = params.get('pattern_id')
        pattern_context = params.get('context', context.copy())

        if not pattern_id:
            self.logger.error("execute_pattern requires 'pattern_id' parameter")
            return {
                'error': 'pattern_id parameter required',
                'nested_execution': False
            }

        # Recursion guard (prevent infinite loops)
        recursion_depth = context.get('_recursion_depth', 0)
        if recursion_depth > 5:
            self.logger.error(f"Max recursion depth exceeded for pattern {pattern_id}")
            return {
                'error': 'Max recursion depth exceeded',
                'pattern_id': pattern_id,
                'depth': recursion_depth
            }

        # Get pattern
        pattern = self._get_pattern(pattern_id)
        if not pattern:
            self.logger.error(f"Pattern not found: {pattern_id}")
            return {
                'error': 'Pattern not found',
                'pattern_id': pattern_id
            }

        # Add recursion tracking
        if isinstance(pattern_context, dict):
            pattern_context['_recursion_depth'] = recursion_depth + 1
            pattern_context['_parent_pattern'] = context.get('pattern_id')

        # Execute pattern
        try:
            result = self._execute_pattern(pattern, pattern_context)

            # Add nested execution metadata
            if isinstance(result, dict):
                result['nested_execution'] = True
                result['parent_pattern'] = context.get('pattern_id')
                result['recursion_depth'] = recursion_depth + 1

            self.logger.info(
                f"Nested pattern executed: {pattern_id} "
                f"(depth={recursion_depth + 1})"
            )

            return result

        except Exception as e:
            self.logger.error(f"Nested pattern execution failed: {e}", exc_info=True)
            return {
                'error': str(e),
                'pattern_id': pattern_id,
                'recursion_depth': recursion_depth + 1
            }

    def _get_pattern(self, pattern_id: str):
        """Get pattern by ID."""
        try:
            if hasattr(self.pattern_engine, 'get_pattern'):
                return self.pattern_engine.get_pattern(pattern_id)
        except Exception as e:
            self.logger.error(f"Error getting pattern {pattern_id}: {e}")
        return None

    def _execute_pattern(self, pattern, context):
        """Execute pattern."""
        try:
            if hasattr(self.pattern_engine, 'execute_pattern'):
                return self.pattern_engine.execute_pattern(pattern, context)
        except Exception as e:
            self.logger.error(f"Error executing pattern: {e}", exc_info=True)
            raise
        return {'error': 'PatternEngine execute_pattern method not available'}
