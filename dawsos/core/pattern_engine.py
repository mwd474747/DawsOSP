#!/usr/bin/env python3
"""
Pattern Engine - The brain that executes pattern-based workflows
This enables DawsOS to work through JSON-defined patterns rather than hard-coded logic
"""
import os
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class PatternEngine:
    """Execute JSON-defined patterns to coordinate agent actions"""

    def __init__(self, pattern_dir: str = 'patterns', runtime=None):
        """
        Initialize the Pattern Engine

        Args:
            pattern_dir: Directory containing pattern JSON files
            runtime: AgentRuntime instance for executing agents
        """
        self.pattern_dir = Path(pattern_dir)
        self.runtime = runtime
        self.patterns = {}
        self.load_patterns()

    def load_patterns(self) -> None:
        """Load all pattern files from the patterns directory"""
        if not self.pattern_dir.exists():
            print(f"Creating pattern directory: {self.pattern_dir}")
            self.pattern_dir.mkdir(parents=True, exist_ok=True)
            return

        # Recursively load all JSON files
        for pattern_file in self.pattern_dir.rglob('*.json'):
            try:
                with open(pattern_file, 'r') as f:
                    pattern = json.load(f)
                    pattern_id = pattern.get('id', pattern_file.stem)
                    self.patterns[pattern_id] = pattern
                    print(f"Loaded pattern: {pattern_id}")
            except Exception as e:
                print(f"Error loading pattern {pattern_file}: {e}")

    def find_pattern(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Find the best matching pattern for user input

        Args:
            user_input: The user's query or command

        Returns:
            Matching pattern dict or None
        """
        user_input_lower = user_input.lower()
        best_match = None
        best_score = 0

        for pattern_id, pattern in self.patterns.items():
            # Check triggers
            triggers = pattern.get('triggers', [])
            score = 0

            for trigger in triggers:
                if trigger.lower() in user_input_lower:
                    score += 1

            # Check for entity mentions
            entities = pattern.get('entities', [])
            for entity in entities:
                # Look for stock symbols (e.g., AAPL, TSLA)
                if re.search(r'\b' + entity + r'\b', user_input, re.IGNORECASE):
                    score += 2  # Entity matches are worth more

            if score > best_score:
                best_score = score
                best_match = pattern

        return best_match if best_score > 0 else None

    def execute_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a pattern by running its steps in sequence

        Args:
            pattern: The pattern to execute
            context: Initial context (user_input, entities, etc.)

        Returns:
            Final response with results from all steps
        """
        if not self.runtime:
            return {"error": "No runtime configured for pattern execution"}

        context = context or {}
        results = []
        step_outputs = {}  # Store outputs from each step

        # Execute each step in sequence
        for i, step in enumerate(pattern.get('steps', [])):
            try:
                # Resolve parameters with variable substitution
                params = self._resolve_params(step.get('params', {}), context, step_outputs)

                # Execute the agent
                agent = step.get('agent')
                method = step.get('method', 'process')

                # Call the agent
                if agent in self.runtime.agents:
                    result = self.runtime.execute(agent, params)
                else:
                    result = {"error": f"Agent {agent} not found"}

                # Store the output
                output_key = step.get('output', f'step_{i}')
                step_outputs[output_key] = result
                results.append({
                    'step': i + 1,
                    'agent': agent,
                    'result': result
                })

            except Exception as e:
                results.append({
                    'step': i + 1,
                    'agent': step.get('agent'),
                    'error': str(e)
                })

        # Format the final response
        return self.format_response(pattern, results, step_outputs)

    def _resolve_params(self, params: Dict[str, Any], context: Dict[str, Any], outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve parameter variables like {user_input}, {SYMBOL}, {step_1.price}

        Args:
            params: Parameters with potential variables
            context: Context variables
            outputs: Previous step outputs

        Returns:
            Resolved parameters
        """
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str):
                # Replace context variables
                for ctx_key, ctx_value in context.items():
                    value = value.replace(f"{{{ctx_key}}}", str(ctx_value))

                # Replace output references
                for out_key, out_value in outputs.items():
                    if isinstance(out_value, dict):
                        # Handle nested references like {quote_data.price}
                        for nested_key, nested_value in out_value.items():
                            value = value.replace(f"{{{out_key}.{nested_key}}}", str(nested_value))
                    else:
                        value = value.replace(f"{{{out_key}}}", str(out_value))

                # Extract stock symbols from user input
                if '{SYMBOL}' in value:
                    # Look for stock symbols in user input
                    symbols = re.findall(r'\b[A-Z]{1,5}\b', context.get('user_input', ''))
                    if symbols:
                        value = value.replace('{SYMBOL}', symbols[0])

                resolved[key] = value
            else:
                resolved[key] = value

        return resolved

    def format_response(self, pattern: Dict[str, Any], results: List[Dict], outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the final response based on pattern template

        Args:
            pattern: The executed pattern
            results: Results from each step
            outputs: Step outputs

        Returns:
            Formatted response
        """
        response = {
            'pattern': pattern.get('name', 'Unknown'),
            'type': pattern.get('response_type', 'generic'),
            'results': results
        }

        # Use pattern's response template if available
        template = pattern.get('response_template')
        if template:
            # Substitute variables in template
            for key, value in outputs.items():
                if isinstance(value, dict):
                    for nested_key, nested_value in value.items():
                        template = template.replace(f"{{{key}.{nested_key}}}", str(nested_value))
                else:
                    template = template.replace(f"{{{key}}}", str(value))

            response['formatted_response'] = template

        # Add any specific response formatting
        response_type = pattern.get('response_type')
        if response_type == 'stock_quote':
            # Format as stock quote
            response['display'] = 'price_card'
        elif response_type == 'regime_analysis':
            # Format as regime analysis
            response['display'] = 'regime_card'
        elif response_type == 'forecast':
            # Format as forecast
            response['display'] = 'forecast_chart'

        return response

    def reload_patterns(self) -> None:
        """Reload all patterns from disk"""
        self.patterns = {}
        self.load_patterns()

    def get_pattern_list(self) -> List[str]:
        """Get list of available pattern IDs"""
        return list(self.patterns.keys())

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by ID"""
        return self.patterns.get(pattern_id)