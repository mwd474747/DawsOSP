"""
Enhanced Chat Processor for Trinity Chat

Integrates entity extraction, conversation memory, and streaming
into the Trinity Chat interface for intelligent multi-turn conversations.
"""

import os
from typing import Dict, Any, Optional
from core.entity_extractor import EntityExtractor
from core.conversation_memory import ConversationMemory


class EnhancedChatProcessor:
    """
    Enhanced chat processor that adds intelligence to Trinity Chat.
    
    Features:
    - Entity extraction from natural language queries
    - Conversation memory and context tracking
    - Reference resolution across turns
    - Smart pattern routing based on intent
    """
    
    def __init__(self, pattern_engine, runtime):
        """
        Initialize enhanced chat processor.
        
        Args:
            pattern_engine: PatternEngine instance
            runtime: AgentRuntime instance
        """
        self.pattern_engine = pattern_engine
        self.runtime = runtime
        
        # Initialize entity extractor (only if API key is available)
        self.entity_extractor = None
        try:
            if os.getenv("ANTHROPIC_API_KEY"):
                self.entity_extractor = EntityExtractor()
        except Exception as e:
            print(f"Entity extractor not available: {e}")
        
        # Initialize conversation memory
        self.memory = ConversationMemory()
        
        # Map intents to smart patterns
        self.intent_to_pattern = {
            "stock_analysis": "smart_stock_analysis",
            "portfolio_review": "smart_portfolio_review",
            "market_briefing": "smart_market_briefing",
            "opportunity_scan": "smart_opportunity_finder",
            "risk_analysis": "smart_risk_analyzer"
        }
    
    def process_query(self, query: str, use_entity_extraction: bool = True) -> Dict[str, Any]:
        """
        Process user query with enhanced intelligence.
        
        Args:
            query: User's natural language query
            use_entity_extraction: Whether to use entity extraction (default: True)
            
        Returns:
            Response dict with result and metadata
        """
        # Step 1: Resolve references using conversation memory
        resolved_query = self.memory.resolve_references(query)
        
        # Step 2: Extract entities and classify intent (if enabled and available)
        extracted = None
        smart_pattern_id = None
        
        if use_entity_extraction and self.entity_extractor:
            try:
                extracted = self.entity_extractor.extract_entities(resolved_query)
                intent_type = extracted['intent']['intent_type']
                
                # Map intent to smart pattern
                if intent_type in self.intent_to_pattern:
                    smart_pattern_id = self.intent_to_pattern[intent_type]
            except Exception as e:
                print(f"Entity extraction failed: {e}")
                extracted = None
        
        # Step 3: Route to appropriate pattern
        result = None
        pattern_used = None
        
        # Try smart pattern first if entity extraction succeeded
        if smart_pattern_id:
            try:
                # Build context from extracted entities
                context = {
                    'user_input': resolved_query,
                    'original_query': query,
                    'conversation_context': self.memory.get_context_for_llm(turns=3)
                }
                
                # Add extracted entities to context (map to both lowercase and uppercase for compatibility)
                if extracted and extracted['entities']:
                    for key, value in extracted['entities'].items():
                        context[key.lower()] = value
                        context[key.upper()] = value
                        context[key] = value  # Also keep original case
                
                # Validate required entities for smart patterns
                pattern = self.pattern_engine.patterns.get(smart_pattern_id)
                if pattern:
                    # Check if pattern requires specific entities
                    required_entities = pattern.get('entities', [])
                    missing_entities = [e for e in required_entities if not context.get(e.lower())]
                    
                    if missing_entities:
                        # Ask user for missing information
                        result = {
                            'response': f"I'd like to help with that analysis, but I need more information. Please specify: {', '.join(missing_entities)}",
                            'missing_entities': missing_entities,
                            'pattern_attempted': smart_pattern_id
                        }
                        pattern_used = 'missing_entities'
                    else:
                        # Execute smart pattern
                        result = self.pattern_engine.execute_pattern(pattern, context)
                        pattern_used = smart_pattern_id
            except Exception as e:
                print(f"Smart pattern execution failed: {e}")
                result = None
        
        # Fallback to traditional pattern matching
        if not result:
            try:
                pattern = self.pattern_engine.find_pattern(resolved_query)
                
                if pattern:
                    # Extract entities using pattern's entity extraction
                    entities = self.pattern_engine.extract_entities(pattern, resolved_query)
                    
                    # Build context
                    context = {
                        'user_input': resolved_query,
                        'conversation_context': self.memory.get_context_for_llm(turns=3)
                    }
                    context.update(entities)
                    
                    # Execute pattern
                    result = self.pattern_engine.execute_pattern(pattern, context)
                    pattern_used = pattern.get('id', 'unknown')
                else:
                    # Final fallback to Claude
                    result = self._fallback_to_claude(resolved_query)
                    pattern_used = 'claude_fallback'
            except Exception as e:
                result = {'response': f'Error processing request: {str(e)}', 'error': True}
                pattern_used = 'error'
        
        # Step 4: Store in conversation memory
        if result:
            entities_for_memory = extracted['entities'] if extracted else {}
            self.memory.add_turn(
                user_query=query,
                assistant_response=result,
                entities=entities_for_memory,
                pattern_used=pattern_used
            )
        
        # Step 5: Add metadata to result
        response = {
            **result,
            'pattern': pattern_used,
            'used_entity_extraction': extracted is not None,
            'intent': extracted['intent'] if extracted else None,
            'extracted_entities': extracted['entities'] if extracted else {},
            'conversation_turn': len(self.memory.history)
        }
        
        return response
    
    def _fallback_to_claude(self, query: str) -> Dict[str, Any]:
        """Fallback to direct Claude processing"""
        try:
            claude_adapter = self.runtime.agent_registry.get_agent('claude')
            if claude_adapter and claude_adapter.agent:
                response = claude_adapter.agent.process({'query': query})
                return {'response': response}
            else:
                return {'response': 'No suitable pattern found. Try being more specific.', 'fallback': True}
        except Exception as e:
            return {'response': f'Error: {str(e)}', 'error': True}
    
    def get_recent_context(self) -> Dict[str, Any]:
        """Get recent conversation context for UI display"""
        return {
            'recent_entities': self.memory.get_recent_entities(),
            'session_summary': self.memory.get_session_summary(),
            'suggested_follow_up': self.memory.suggest_follow_up()
        }
    
    def clear_conversation(self):
        """Clear conversation memory (start new session)"""
        self.memory.clear()
    
    def get_conversation_history(self):
        """Get full conversation history"""
        return [turn.to_dict() for turn in self.memory.history]
