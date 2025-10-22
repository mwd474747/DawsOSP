#!/usr/bin/env python3
"""
Normalize Response Action - Standardize agent response format

Ensures agent responses follow a consistent structure with 'response' and 'data' fields.
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class NormalizeResponseAction(ActionHandler):
    """
    Normalize agent response to standard format.

    Converts various agent response formats into a standard structure:
    {
        'response': <string for display>,
        'data': <structured data>,
        ...other fields preserved
    }
    """

    @property
    def action_name(self) -> str:
        return "normalize_response"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Normalize response from previous step.

        Args:
            params: Must contain 'response_key' (which output to normalize)
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Normalized response dictionary
        """
        response_key = params.get('response_key', 'agent_response')
        response = outputs.get(response_key, {})

        if not response:
            return {
                'response': 'No response available',
                'data': None
            }

        # If already normalized, return as-is
        if isinstance(response, dict) and 'response' in response:
            return response

        # If string, wrap it
        if isinstance(response, str):
            return {
                'response': response,
                'data': response
            }

        # If dict without 'response', add it
        if isinstance(response, dict):
            normalized = response.copy()
            if 'response' not in normalized:
                # Try to extract a reasonable response string
                if 'data' in normalized:
                    normalized['response'] = str(normalized['data'])
                elif 'result' in normalized:
                    normalized['response'] = str(normalized['result'])
                else:
                    normalized['response'] = 'Operation completed'
            return normalized

        # Default: convert to string
        return {
            'response': str(response),
            'data': response
        }
