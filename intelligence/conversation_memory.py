"""
Conversation Memory Manager for Trinity Chat

Tracks conversation history, resolves entity references across turns,
and maintains context for multi-turn conversations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class ConversationTurn:
    """Single turn in a conversation"""
    
    def __init__(self, user_query: str, assistant_response: str, entities: Dict[str, Any], pattern_used: Optional[str] = None):
        self.timestamp = datetime.now()
        self.user_query = user_query
        self.assistant_response = assistant_response
        self.entities = entities
        self.pattern_used = pattern_used
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_query": self.user_query,
            "assistant_response": self.assistant_response,
            "entities": self.entities,
            "pattern_used": self.pattern_used
        }


class ConversationMemory:
    """
    Manages conversation context and entity resolution across turns.
    
    Features:
    - Tracks conversation history
    - Resolves entity references ("it", "that stock", etc.)
    - Maintains context window for LLM prompts
    - Tracks recently mentioned symbols, sectors, strategies
    """
    
    def __init__(self, max_turns: int = 20):
        """
        Initialize conversation memory.
        
        Args:
            max_turns: Maximum number of turns to keep in memory
        """
        self.max_turns = max_turns
        self.history: List[ConversationTurn] = []
        self.session_start = datetime.now()
        
        # Entity tracking
        self.recent_symbols: List[str] = []  # Most recent first
        self.recent_sectors: List[str] = []
        self.recent_strategies: List[str] = []
        self.last_analysis_type: Optional[str] = None
        self.last_intent: Optional[str] = None
    
    def add_turn(self, user_query: str, assistant_response: str, entities: Dict[str, Any], pattern_used: Optional[str] = None):
        """
        Add a conversation turn to memory.
        
        Args:
            user_query: User's query
            assistant_response: Assistant's response
            entities: Extracted entities from the query
            pattern_used: Pattern ID that was executed
        """
        turn = ConversationTurn(user_query, assistant_response, entities, pattern_used)
        self.history.append(turn)
        
        # Update entity tracking
        self._update_entity_tracking(entities)
        
        # Trim history if needed
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]
    
    def _update_entity_tracking(self, entities: Dict[str, Any]):
        """Update tracked entities from latest turn"""
        # Track symbols
        if "symbol" in entities and entities["symbol"]:
            symbol = entities["symbol"].upper()
            if symbol in self.recent_symbols:
                self.recent_symbols.remove(symbol)
            self.recent_symbols.insert(0, symbol)
            self.recent_symbols = self.recent_symbols[:5]  # Keep last 5
        
        if "holdings" in entities and entities["holdings"]:
            for symbol in entities["holdings"]:
                symbol = symbol.upper()
                if symbol in self.recent_symbols:
                    self.recent_symbols.remove(symbol)
                self.recent_symbols.insert(0, symbol)
            self.recent_symbols = self.recent_symbols[:10]
        
        # Track sectors
        if "sectors" in entities and entities["sectors"]:
            for sector in entities["sectors"]:
                if sector in self.recent_sectors:
                    self.recent_sectors.remove(sector)
                self.recent_sectors.insert(0, sector)
            self.recent_sectors = self.recent_sectors[:5]
        
        # Track strategies
        if "strategy_type" in entities and entities["strategy_type"]:
            strategy = entities["strategy_type"]
            if strategy in self.recent_strategies:
                self.recent_strategies.remove(strategy)
            self.recent_strategies.insert(0, strategy)
            self.recent_strategies = self.recent_strategies[:3]
        
        # Track last analysis type
        if "analysis_type" in entities and entities["analysis_type"]:
            self.last_analysis_type = entities["analysis_type"]
    
    def resolve_references(self, query: str) -> str:
        """
        Resolve pronoun and entity references in query.
        
        Handles:
        - "it" → most recent symbol
        - "that stock" → most recent symbol
        - "the same" → use previous context
        - "another" → same type, different target
        
        Args:
            query: User query with potential references
            
        Returns:
            Query with references resolved
        """
        resolved = query
        query_lower = query.lower()
        
        # Resolve "it" or "that stock" to most recent symbol
        if re.search(r'\b(it|that stock|this stock|that company|this company)\b', query_lower):
            if self.recent_symbols:
                most_recent = self.recent_symbols[0]
                resolved = re.sub(r'\b(it|that stock|this stock|that company|this company)\b', most_recent, resolved, flags=re.IGNORECASE)
        
        # Resolve "them" or "those stocks" to recent holdings
        if re.search(r'\b(them|those stocks|these stocks)\b', query_lower):
            if len(self.recent_symbols) > 1:
                symbols_str = ", ".join(self.recent_symbols[:5])
                resolved = re.sub(r'\b(them|those stocks|these stocks)\b', symbols_str, resolved, flags=re.IGNORECASE)
        
        # Resolve "the same analysis" to previous analysis type
        if "same analysis" in query_lower or "same kind" in query_lower:
            if self.last_analysis_type:
                resolved += f" ({self.last_analysis_type} analysis)"
        
        return resolved
    
    def get_context_for_llm(self, turns: int = 3) -> str:
        """
        Get recent conversation context formatted for LLM prompt.
        
        Args:
            turns: Number of recent turns to include
            
        Returns:
            Formatted context string
        """
        if not self.history:
            return ""
        
        recent_turns = self.history[-turns:]
        context_parts = ["Previous conversation context:"]
        
        for turn in recent_turns:
            context_parts.append(f"\nUser: {turn.user_query}")
            # Truncate long responses
            response = turn.assistant_response
            if isinstance(response, dict):
                response = response.get("formatted_response", str(response))
            if len(str(response)) > 200:
                response = str(response)[:200] + "..."
            context_parts.append(f"Assistant: {response}")
        
        return "\n".join(context_parts)
    
    def get_recent_entities(self) -> Dict[str, List[str]]:
        """
        Get recently mentioned entities.
        
        Returns:
            Dict with recent symbols, sectors, strategies
        """
        return {
            "symbols": self.recent_symbols,
            "sectors": self.recent_sectors,
            "strategies": self.recent_strategies,
            "last_analysis_type": self.last_analysis_type,
            "last_intent": self.last_intent
        }
    
    def suggest_follow_up(self) -> Optional[str]:
        """
        Suggest follow-up questions based on conversation history.
        
        Returns:
            Suggested follow-up question or None
        """
        if not self.history:
            return None
        
        last_turn = self.history[-1]
        entities = last_turn.entities
        
        # Suggest based on last action
        if "symbol" in entities and entities["symbol"]:
            symbol = entities["symbol"]
            if self.last_analysis_type == "fundamental":
                return f"Would you like a technical analysis of {symbol}?"
            elif self.last_analysis_type == "technical":
                return f"Would you like to see {symbol}'s fundamentals?"
            else:
                return f"Would you like a risk assessment for {symbol}?"
        
        if "holdings" in entities and entities["holdings"]:
            return "Would you like to scan for new opportunities to diversify your portfolio?"
        
        return None
    
    def clear(self):
        """Clear conversation memory (start new session)"""
        self.history.clear()
        self.recent_symbols.clear()
        self.recent_sectors.clear()
        self.recent_strategies.clear()
        self.last_analysis_type = None
        self.last_intent = None
        self.session_start = datetime.now()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session.
        
        Returns:
            Session statistics and summary
        """
        return {
            "session_duration_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
            "total_turns": len(self.history),
            "unique_symbols_discussed": len(set(self.recent_symbols)),
            "recent_symbols": self.recent_symbols[:5],
            "recent_sectors": self.recent_sectors[:3],
            "patterns_used": list(set([t.pattern_used for t in self.history if t.pattern_used])),
        }
