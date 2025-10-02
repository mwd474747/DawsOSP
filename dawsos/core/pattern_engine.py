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

        # Get steps - support both 'steps' and 'workflow' formats
        steps = pattern.get('steps', pattern.get('workflow', []))

        # Execute each step in sequence
        for i, step in enumerate(steps):
            try:
                # Resolve parameters with variable substitution
                params = self._resolve_params(step.get('params', step.get('parameters', {})), context, step_outputs)

                # Get the action type (supports both 'agent' and 'action' formats)
                agent = step.get('agent')
                action = step.get('action')

                # Execute based on action type
                if agent and agent in self.runtime.agents:
                    # Direct agent call
                    result = self.runtime.execute(agent, params)
                elif action:
                    # Handle special actions
                    result = self.execute_action(action, params, context, step_outputs)
                else:
                    result = {"error": f"No valid agent or action found in step"}

                # Store the outputs
                outputs = step.get('outputs', step.get('output', []))
                if isinstance(outputs, str):
                    outputs = [outputs]

                # Store result for each output variable
                if outputs:
                    for output_var in outputs:
                        if output_var:
                            step_outputs[output_var] = result
                else:
                    # Default output key
                    output_key = f'step_{i}'
                    step_outputs[output_key] = result

                results.append({
                    'step': i + 1,
                    'action': action or agent,
                    'result': result
                })

            except Exception as e:
                results.append({
                    'step': i + 1,
                    'agent': step.get('agent'),
                    'error': str(e)
                })

        # Format the final response
        return self.format_response(pattern, results, step_outputs, context)

    def execute_action(self, action: str, params: Dict[str, Any], context: Dict[str, Any], outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a special action (not a direct agent call)

        Args:
            action: Action type (knowledge_lookup, evaluate, calculate, etc.)
            params: Action parameters
            context: Current context
            outputs: Previous step outputs

        Returns:
            Action result
        """
        # Handle different action types
        if action == "knowledge_lookup":
            # Look up knowledge from the graph
            knowledge_file = params.get('knowledge_file', '')
            section = params.get('section', '')

            # For now, return mock data - in production this would query the knowledge graph
            return {
                'data': f"Knowledge from {knowledge_file}:{section}",
                'found': True
            }

        elif action == "evaluate":
            # Evaluate criteria
            eval_type = params.get('type', '')
            checks = params.get('checks', [])

            # Mock evaluation scores
            import random
            score = random.randint(5, 10)
            return {
                'score': score,
                'type': eval_type,
                'checks_passed': len(checks)
            }

        elif action == "calculate":
            # Perform calculation
            formula = params.get('formula', '')

            # Mock calculation
            import random
            value = round(random.uniform(10, 25), 2)
            return {
                'value': value,
                'formula': formula
            }

        elif action == "synthesize":
            # Synthesize multiple scores
            scores = params.get('scores', [])

            # Calculate average of scores
            numeric_scores = []
            for score_ref in scores:
                # Extract numeric value from score references
                if isinstance(score_ref, str) and score_ref.startswith('{') and score_ref.endswith('}'):
                    # This is a reference to a previous output
                    var_name = score_ref.strip('{}')
                    if var_name in outputs:
                        score_data = outputs[var_name]
                        if isinstance(score_data, dict) and 'score' in score_data:
                            numeric_scores.append(score_data['score'])
                        elif isinstance(score_data, dict) and 'value' in score_data:
                            numeric_scores.append(score_data['value'])
                        elif isinstance(score_data, (int, float)):
                            numeric_scores.append(score_data)

            avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 7

            # Determine moat rating based on average
            if avg_score >= 8:
                rating = "Wide Moat"
                durability = "20+ years"
                width = "Very Wide"
                trend = "Strengthening"
                action_text = "Strong Buy - Hold Forever"
            elif avg_score >= 6:
                rating = "Narrow Moat"
                durability = "10-20 years"
                width = "Moderate"
                trend = "Stable"
                action_text = "Buy at Fair Price"
            else:
                rating = "No Moat"
                durability = "< 10 years"
                width = "Minimal"
                trend = "Weakening"
                action_text = "Avoid Unless Deep Discount"

            return {
                'moat_rating': rating,
                'moat_durability': durability,
                'moat_width': width,
                'moat_trend': trend,
                'investment_action': action_text,
                'overall_score': avg_score
            }

        elif action.startswith("agent:"):
            # Extract agent name and call it
            agent_name = action.replace("agent:", "")
            if agent_name in self.runtime.agents:
                return self.runtime.execute(agent_name, params)
            else:
                return {"error": f"Agent {agent_name} not found"}

        else:
            # Unknown action - return mock success
            return {
                'status': 'completed',
                'action': action,
                'params': params
            }

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

    def format_response(self, pattern: Dict[str, Any], results: List[Dict], outputs: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format the final response based on pattern template

        Args:
            pattern: The executed pattern
            results: Results from each step
            outputs: Step outputs
            context: Execution context

        Returns:
            Formatted response
        """
        context = context or {}
        response = {
            'pattern': pattern.get('name', 'Unknown'),
            'type': pattern.get('response_type', 'generic'),
            'results': results
        }

        # Use pattern's response template if available (support both 'response_template' and 'response.template')
        template = pattern.get('response_template')
        if not template and isinstance(pattern.get('response'), dict):
            template = pattern['response'].get('template')

        if template:
            # Substitute variables in template
            for key, value in outputs.items():
                # Extract the actual response from agent output
                if isinstance(value, dict):
                    # Check if this is an agent response with 'response' field
                    if 'response' in value:
                        template = template.replace(f"{{{key}}}", str(value['response']))
                    elif 'friendly_response' in value:
                        template = template.replace(f"{{{key}}}", str(value['friendly_response']))
                    elif 'result' in value:
                        template = template.replace(f"{{{key}}}", str(value['result']))
                    else:
                        # Handle nested references
                        for nested_key, nested_value in value.items():
                            template = template.replace(f"{{{key}.{nested_key}}}", str(nested_value))
                        # Also replace the whole object reference
                        template = template.replace(f"{{{key}}}", str(value))
                else:
                    template = template.replace(f"{{{key}}}", str(value))

            # Extract symbol from context if available
            symbol = context.get('symbol', 'AAPL')
            user_input = str(context.get('user_input', '')).lower()

            # Company name to symbol mapping
            company_symbols = {
                'exxon': 'XOM',
                'apple': 'AAPL',
                'microsoft': 'MSFT',
                'google': 'GOOGL',
                'amazon': 'AMZN',
                'tesla': 'TSLA',
                'berkshire': 'BRK.B',
                'meta': 'META',
                'nvidia': 'NVDA',
                'jpmorgan': 'JPM',
                'visa': 'V',
                'walmart': 'WMT',
                'johnson': 'JNJ',
                'procter': 'PG',
                'coca': 'KO',
                'coca-cola': 'KO',
                'pepsi': 'PEP',
                'disney': 'DIS',
                'netflix': 'NFLX',
                'intel': 'INTC',
                'adobe': 'ADBE',
                'salesforce': 'CRM',
                'oracle': 'ORCL',
                'ibm': 'IBM',
                'chevron': 'CVX',
                'pfizer': 'PFE',
                'boeing': 'BA',
                'verizon': 'VZ',
                'at&t': 'T',
                'att': 'T'
            }

            # First try to find company name
            for company_name, ticker in company_symbols.items():
                if company_name in user_input:
                    symbol = ticker
                    break
            else:
                # Try to extract uppercase symbol from user input
                words = str(context.get('user_input', '')).split()
                for word in words:
                    # Remove punctuation
                    word = word.strip('.,?!;:')
                    if word.isupper() and 2 <= len(word) <= 5:
                        symbol = word
                        break

            # Replace remaining template variables with default/mock values
            template = template.replace('{symbol}', symbol)
            template = template.replace('{brand_details}', '• Strong brand recognition\n• Premium pricing power\n• Customer loyalty high')
            template = template.replace('{network_details}', '• Network effects present\n• High switching costs\n• Platform dominance')
            template = template.replace('{cost_details}', '• Scale advantages\n• Operational efficiency\n• Cost leadership position')
            template = template.replace('{switching_details}', '• Embedded in workflows\n• Long-term contracts\n• High migration costs')
            template = template.replace('{margin_stability}', 'Stable (±2%)')
            template = template.replace('{avg_roic}', '18.5')

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