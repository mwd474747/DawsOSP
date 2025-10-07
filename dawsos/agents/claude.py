"""Claude - The main personality that interprets user intent

Phase 3.1: Comprehensive type hints added for better IDE support and type safety.
"""
from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from core.typing_compat import TypeAlias
from core.fallback_tracker import get_fallback_tracker

# Type aliases for clarity
ContextDict: TypeAlias = Dict[str, Any]
IntentResult: TypeAlias = Dict[str, Any]
ConversationHistory: TypeAlias = List[Dict[str, Any]]
MemoryList: TypeAlias = List[Dict[str, Any]]

class Claude(BaseAgent):
    """The conversational interface to the system"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize Claude with graph and optional LLM client.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client for AI-powered responses
        """
        super().__init__(graph=graph, name="Claude", llm_client=llm_client)
        self.vibe: str = "friendly and curious"
        self.conversation_history: ConversationHistory = []

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

    def think(self, context: ContextDict) -> IntentResult:
        """Main method for processing context - called by runtime.

        Args:
            context: Dictionary containing user_input and other context

        Returns:
            Dictionary with intent, entities, action, parameters, and friendly_response
        """
        user_input = context.get('user_input', '')

        # If no LLM client, use fallback responses
        if not self.llm_client:
            tracker = get_fallback_tracker()
            fallback_meta = tracker.mark_fallback(
                component='llm',
                reason='api_key_missing',
                data_type='cached'
            )
            result = self._fallback_response(user_input, context)
            result.update(fallback_meta)
            return result

        # Generate prompt for LLM
        prompt = self.get_prompt(context)

        # Call Claude API with JSON parsing
        try:
            response = self.llm_client.complete(prompt, parse_json=True)

            # Ensure response has required fields
            if not isinstance(response, dict):
                response = {"response": str(response)}

            if 'friendly_response' not in response:
                response['friendly_response'] = f"Analyzing: {user_input}"

            return response

        except Exception as e:
            # Fallback on error
            print(f"LLM API error, using fallback: {e}")
            tracker = get_fallback_tracker()
            fallback_meta = tracker.mark_fallback(
                component='llm',
                reason='api_error',
                data_type='cached'
            )
            result = self._fallback_response(user_input, context)
            result.update(fallback_meta)
            return result

    def _fallback_response(
        self,
        user_input: str,
        context: Optional[ContextDict] = None
    ) -> IntentResult:
        """Fallback responses when LLM is unavailable.

        Args:
            user_input: User's query or command
            context: Optional context dictionary

        Returns:
            Intent result with fallback cached response
        """
        user_input_lower = str(user_input).lower()

        # Generate a clean response based on the input
        if 'macro' in user_input_lower and ('data' in user_input_lower or 'patterns' in user_input_lower):
            return {
                "intent": "ANALYSIS",
                "entities": ["macro", "economy"],
                "action": "analyze",
                "parameters": {},
                "friendly_response": "Analyzing macroeconomic environment (cached response)",
                "response": """⚠️ **Using Cached Analysis - LLM Unavailable**

📊 Macroeconomic Analysis (FALLBACK)

🔄 Economic Cycle Stage: **Late Cycle**
• GDP Growth: 2.1% (Slowing from 2.8%)
• Inflation: 3.2% (Above target, cooling slowly)
• Unemployment: 3.9% (Near full employment)
• Fed Funds: 5.33% (Restrictive territory)

📈 Key Trends:
• **Growth Deceleration**: Economy slowing but avoiding recession
• **Disinflation Process**: Inflation cooling but sticky above 3%
• **Labor Market Resilience**: Unemployment remains low
• **Yield Curve Normalizing**: 10Y-2Y spread improving

⚠️ Risk Factors:
• Sticky services inflation may keep Fed hawkish
• Commercial real estate stress building
• Regional bank vulnerabilities remain
• Geopolitical tensions elevated
• Consumer savings depleted

💡 Investment Implications:
• **Favor Quality**: Focus on strong balance sheets
• **Defensive Tilt**: Increase allocation to staples, utilities
• **Fixed Income Attractive**: Lock in yields above 4%
• **International Diversification**: Consider non-US exposure
• **Maintain Hedges**: Volatility likely to increase

ℹ️ For real-time AI analysis, configure ANTHROPIC_API_KEY""",
                "source": "fallback"
            }
        elif 'regime' in user_input_lower:
            return {
                "intent": "ANALYSIS",
                "entities": ["market", "regime"],
                "action": "analyze",
                "parameters": {},
                "friendly_response": "Analyzing market regime (cached response)",
                "response": """⚠️ **Using Cached Analysis - LLM Unavailable**

🎯 Current Market Regime: RISK-ON (FALLBACK)

📊 Key Indicators:
• VIX: 15.2 (Low - Complacency)
• DXY: 104.5 (Neutral)
• Credit Spreads: Tight
• Equity Momentum: Positive

🔍 Regime Characteristics:
• High risk appetite
• Growth outperforming value
• Tech sector leadership
• Low volatility environment

⚠️ Confidence Level: 75%

📝 Recommendations:
• Maintain equity exposure
• Overweight growth sectors
• Keep hedges minimal
• Watch for regime shift signals

ℹ️ For real-time AI analysis, configure ANTHROPIC_API_KEY""",
                "source": "fallback"
            }
        elif 'correlations' in user_input_lower:
            # Extract correlations if passed in
            if '{correlations}' in user_input:
                # This is a template, so provide a formatted response
                return {
                    "intent": "ANALYSIS",
                    "entities": ["SPY", "correlations"],
                    "action": "analyze",
                    "parameters": {},
                    "friendly_response": "Analyzing correlations (cached response)",
                    "response": """⚠️ **Using Cached Analysis - LLM Unavailable**

SPY Correlation Analysis (FALLBACK):

📈 Strong Positive Correlations:
• QQQ: 0.85 - Tech sector moves closely with SPY
• IWM: 0.78 - Small caps follow market direction

📉 Inverse Relationships:
• DXY: -0.45 - Dollar strength weakens equities
• GLD: -0.35 - Gold as risk-off hedge

💡 Trading Implications:
• Use QQQ for leveraged SPY exposure
• Watch DXY for market reversals
• Consider GLD for portfolio hedging

🛡️ Hedge Opportunities:
• Long DXY or UUP when SPY overbought
• Gold allocation for tail risk protection
• VXX for short-term volatility hedges

ℹ️ For real-time AI analysis, configure ANTHROPIC_API_KEY""",
                    "source": "fallback"
                }

        elif 'sector' in user_input_lower:
            return {
                "intent": "ANALYSIS",
                "entities": ["sectors", "performance"],
                "action": "analyze",
                "parameters": {},
                "friendly_response": "Analyzing sector performance (cached response)",
                "response": """⚠️ **Using Cached Analysis - LLM Unavailable**

📊 Sector Performance Analysis (FALLBACK)

🏆 Leading Sectors (Past Month):
1. **Technology (XLK)**: +5.2% - AI momentum continues
2. **Communications (XLC)**: +4.8% - META/GOOGL strength
3. **Financials (XLF)**: +3.9% - Rate environment favorable

😐 Neutral Performers:
4. **Healthcare (XLV)**: +1.2% - Biotech recovery offset by managed care
5. **Industrials (XLI)**: +0.8% - Mixed signals on growth
6. **Consumer Disc. (XLY)**: +0.5% - Bifurcated market

📉 Lagging Sectors:
7. **Energy (XLE)**: -2.1% - Oil price weakness
8. **Utilities (XLU)**: -2.8% - Rising yields pressure
9. **Real Estate (XLRE)**: -3.4% - Rate sensitive weakness

🔄 Rotation Patterns:
• **Growth → Value**: Early signs of rotation
• **Defensive Underperformance**: Risk-on sentiment
• **Small Cap Weakness**: Quality flight continues

💡 Opportunities:
• Tech pullbacks on profit-taking
• Financial strength on NIM expansion
• Energy oversold on seasonal weakness

ℹ️ For real-time AI analysis, configure ANTHROPIC_API_KEY""",
                "source": "fallback"
            }

        # Default response
        return {
            "intent": "QUERY",
            "entities": [],
            "action": "process",
            "parameters": {},
            "friendly_response": f"Processing: {user_input} (LLM unavailable)",
            "response": f"⚠️ **LLM Unavailable - Using Fallback**\n\nI'll help you with: {user_input}\n\nℹ️ For AI-powered insights, configure ANTHROPIC_API_KEY in your .env file",
            "source": "fallback"
        }

    def process(self, user_input: str) -> IntentResult:
        """Process user input and coordinate response.

        Args:
            user_input: User's query or command

        Returns:
            Intent result with response and optional node_id
        """
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

        # Store result in knowledge graph
        result = intent_response
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            node_id = self.store_result(result)
            result['node_id'] = node_id
        return result

    def _recent_history(self) -> str:
        """Get recent conversation context (last 5 messages).

        Returns:
            String representation of recent conversation history
        """
        recent = self.conversation_history[-5:] if len(self.conversation_history) > 5 else self.conversation_history
        return str(recent)

class IntentParser(BaseAgent):
    """Sub-agent that extracts intent from user input (Phase 3.1: Type hints added)"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize IntentParser.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("IntentParser", graph, llm_client)
        self.vibe: str = "analytical"

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
    """Sub-agent that crafts human-friendly responses (Phase 3.1: Type hints added)"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize ResponseCrafter.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("ResponseCrafter", graph, llm_client)
        self.vibe: str = "articulate"

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
    """Sub-agent that maintains conversation context (Phase 3.1: Type hints added)"""

    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize MemoryKeeper.

        Args:
            graph: Knowledge graph instance
            llm_client: Optional LLM client
        """
        super().__init__("MemoryKeeper", graph, llm_client)
        self.vibe: str = "nostalgic"
        self.important_memories: MemoryList = []

    def should_remember(self, interaction: Dict[str, Any]) -> bool:
        """Decide if something is worth remembering long-term.

        Args:
            interaction: Dictionary representing an interaction to evaluate

        Returns:
            True if interaction should be remembered
        """
        context = {"interaction": interaction}
        response = self.think(context)
        return response.get("remember", False)

    def recall_relevant(self, context: str) -> MemoryList:
        """Recall relevant memories for current context.

        Args:
            context: Current context string to match against

        Returns:
            List of up to 5 relevant memories
        """
        relevant = []
        for memory in self.important_memories:
            if context.lower() in str(memory).lower():
                relevant.append(memory)
        return relevant[-5:]  # Last 5 relevant memories