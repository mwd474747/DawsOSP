"""Base Agent - Foundation for all agents in the system"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from core.llm_client import get_llm_client

class BaseAgent:
    """Simple base class for all agents - vibe coding style"""

    def __init__(self, name: str, graph=None, llm_client=None):
        self.name = name
        self.graph = graph
        self.llm = llm_client or get_llm_client()  # Use provided or get singleton
        self.memory = []
        self.vibe = "helpful"  # Each agent has a vibe
        self.use_real_llm = os.getenv('ANTHROPIC_API_KEY') is not None

    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Basic thinking pattern - just ask the LLM"""
        prompt = self.get_prompt(context)

        # Use real LLM if available, otherwise mock
        if self.use_real_llm:
            response = self.llm.complete(prompt, parse_json=True)
            # Ensure response is a dict
            if isinstance(response, str):
                response = {"response": response}
        else:
            response = self._mock_llm_response(prompt, context)

        # Remember what we did
        self.remember(context, response)

        return response

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get the prompt for this agent - override in subclasses"""
        return f"""
        You are {self.name}.
        Context: {json.dumps(context, indent=2)}
        What should we do?
        """

    def remember(self, context: Dict[str, Any], response: Dict[str, Any]):
        """Store memory of decisions"""
        self.memory.append({
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "response": response
        })
        # Keep last 100 memories only
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

    def _mock_llm_response(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock LLM response for testing - will be replaced with real LLM"""
        return {
            "action": "thinking",
            "thoughts": f"{self.name} is processing the request",
            "decision": None
        }

    def vibe_check(self) -> str:
        """How's this agent feeling?"""
        if len(self.memory) == 0:
            return "fresh and ready"
        elif len(self.memory) > 50:
            return "experienced and wise"
        else:
            return "learning and growing"