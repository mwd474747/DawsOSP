"""LLM Client - Wrapper for Claude API"""
import os
import json
from typing import Dict, Any, Optional
from anthropic import Anthropic
import re

class LLMClient:
    """Simple wrapper for Claude API"""

    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not set. Using mock mode.")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)
            print("Claude API connected successfully!")

        # Default settings
        self.model = "claude-3-haiku-20240307"  # Cheaper, faster model for agents
        self.max_tokens = 1000
        self.temperature = 0.7

    def complete(self, prompt: str, parse_json: bool = False) -> Any:
        """Send prompt to Claude and get response"""
        if not self.client:
            # Mock mode
            return self._mock_response(prompt)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text response
            text = response.content[0].text

            # Parse JSON if requested
            if parse_json:
                return self._parse_json_response(text)

            return text

        except Exception as e:
            print(f"Claude API error: {e}")
            return {"error": str(e)}

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from Claude's response"""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try to parse structured response
        result = {}

        # Look for key: value patterns
        lines = text.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                # Try to parse value as JSON
                try:
                    value = json.loads(value)
                except:
                    # Keep as string
                    pass

                result[key] = value

        if result:
            return result

        # Return raw text if can't parse
        return {"response": text}

    def _mock_response(self, prompt: str) -> Dict[str, Any]:
        """Generate mock response when API not available"""
        # Simple pattern matching for mock responses
        prompt_lower = prompt.lower()

        if 'intent' in prompt_lower or 'what do they want' in prompt_lower:
            return {
                "intent": "ADD_DATA",
                "entities": ["AAPL"],
                "action": "fetch_stock",
                "response": "I'll help you with that!"
            }
        elif 'relationship' in prompt_lower:
            return {
                "exists": True,
                "type": "correlates",
                "strength": 0.7,
                "confidence": 0.8
            }
        elif 'pattern' in prompt_lower:
            return {
                "pattern_type": "cycle",
                "description": "Mock pattern detected",
                "confidence": 0.6
            }
        elif 'forecast' in prompt_lower:
            return {
                "forecast": "bullish",
                "confidence": 0.7,
                "signal_strength": 0.5
            }
        else:
            return {
                "action": "thinking",
                "response": "Mock response - set ANTHROPIC_API_KEY for real responses"
            }

    def set_model(self, model: str):
        """Change the model (haiku, sonnet, opus)"""
        model_map = {
            'haiku': 'claude-3-haiku-20240307',
            'sonnet': 'claude-3-sonnet-20240229',
            'opus': 'claude-3-opus-20240229'
        }
        self.model = model_map.get(model, model)

    def set_temperature(self, temp: float):
        """Set temperature (0-1)"""
        self.temperature = max(0, min(1, temp))

    def set_max_tokens(self, tokens: int):
        """Set max tokens"""
        self.max_tokens = tokens


# Singleton instance
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get singleton LLM client"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client