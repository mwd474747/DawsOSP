"""Claude - The main personality that interprets user intent"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List

class Claude(BaseAgent):
    """The conversational interface to the system"""

    def __init__(self, graph, llm_client=None):
        super().__init__("Claude", graph, llm_client)
        self.vibe = "friendly and curious"
        self.conversation_history = []

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are Claude, the friendly interface to DawsOS - a living knowledge graph for financial markets.

        User said: {context.get('user_input', '')}
        Graph stats: {self.graph.get_stats() if self.graph else 'empty'}

        Analyze what the user wants and respond with a JSON object containing:
        {{
            "intent": "ADD_DATA|QUERY|FORECAST|EXPLAIN|BUILD|ANALYZE|CONNECT",
            "entities": ["list", "of", "mentioned", "things"],
            "action": "specific action to take",
            "parameters": {{"any": "needed parameters"}},
            "friendly_response": "1-2 sentence casual response to user"
        }}

        Examples:
        User: "What's Apple's stock price?"
        {{
            "intent": "QUERY",
            "entities": ["AAPL", "stock price"],
            "action": "fetch_stock_quote",
            "parameters": {{"symbol": "AAPL"}},
            "friendly_response": "Let me check Apple's current price for you."
        }}

        User: "How will inflation affect tech stocks?"
        {{
            "intent": "FORECAST",
            "entities": ["inflation", "tech stocks"],
            "action": "analyze_relationship",
            "parameters": {{"from": "inflation", "to": "tech_sector"}},
            "friendly_response": "I'll analyze how inflation typically impacts tech stocks."
        }}

        Now analyze: {context.get('user_input', '')}
        """

    def process(self, user_input: str) -> Dict[str, Any]:
        """Process user input and coordinate response"""
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Get intent
        context = {"user_input": user_input}
        intent_response = self.think(context)

        # Remember assistant response
        self.conversation_history.append({
            "role": "assistant",
            "content": intent_response.get("friendly_response", "Let me think about that...")
        })

        return intent_response

    def _recent_history(self) -> str:
        """Get recent conversation context"""
        recent = self.conversation_history[-5:] if len(self.conversation_history) > 5 else self.conversation_history
        return str(recent)

class IntentParser(BaseAgent):
    """Sub-agent that extracts intent from user input"""

    def __init__(self, graph, llm_client=None):
        super().__init__("IntentParser", graph, llm_client)
        self.vibe = "analytical"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Extract the core intent from this user input.

        User said: {context.get('user_input', '')}

        What do they REALLY want? Be specific.
        Extract:
        - primary_intent (one word)
        - entities (list of things mentioned)
        - urgency (high/medium/low)
        """

class ResponseCrafter(BaseAgent):
    """Sub-agent that crafts human-friendly responses"""

    def __init__(self, graph, llm_client=None):
        super().__init__("ResponseCrafter", graph, llm_client)
        self.vibe = "articulate"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Craft a friendly response.

        What happened: {context.get('action_taken', '')}
        Result: {context.get('result', '')}
        User's original question: {context.get('original_input', '')}

        Write a 1-2 sentence casual response. Be friendly but concise.
        Don't be corporate. Be a bit playful if appropriate.
        """

class MemoryKeeper(BaseAgent):
    """Sub-agent that maintains conversation context"""

    def __init__(self, graph, llm_client=None):
        super().__init__("MemoryKeeper", graph, llm_client)
        self.vibe = "nostalgic"
        self.important_memories = []

    def should_remember(self, interaction: Dict[str, Any]) -> bool:
        """Decide if something is worth remembering long-term"""
        context = {"interaction": interaction}
        response = self.think(context)
        return response.get("remember", False)

    def recall_relevant(self, context: str) -> List[Dict[str, Any]]:
        """Recall relevant memories for current context"""
        relevant = []
        for memory in self.important_memories:
            if context.lower() in str(memory).lower():
                relevant.append(memory)
        return relevant[-5:]  # Last 5 relevant memories