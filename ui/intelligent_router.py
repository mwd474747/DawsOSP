"""
Intelligent Router - Routes queries to appropriate agents
Uses NLP to classify intent and distribute work
"""

from typing import Dict, Any, List, Tuple, Optional
import re
from agents.base_agent import BaseAgent

class IntelligentRouter:
    """Routes queries to the most appropriate agent(s)"""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        """
        Initialize router with available agents
        
        Args:
            agents: Dictionary of agent_name -> agent_instance
        """
        self.agents = agents
        self.intent_patterns = self._build_intent_patterns()
    
    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """Build pattern matching for intent classification"""
        return {
            'macro': [
                'recession', 'inflation', 'gdp', 'economy', 'fed', 'central bank',
                'interest rate', 'unemployment', 'cycle', 'dalio', 'currency',
                'dollar', 'yield curve', 'macro', 'global', 'liquidity'
            ],
            'equity': [
                'stock', 'share', 'valuation', 'earnings', 'revenue', 'fundamental',
                'pe', 'ratio', 'dividend', 'insider', 'peer', 'compare', 'analysis',
                'dcf', 'fair value', 'buy', 'sell', 'hold', 'analyze'
            ],
            'market': [
                'market', 'breadth', 'internal', 'options', 'flow', 'sector',
                'rotation', 'volatility', 'vix', 'correlation', 'sentiment',
                'positioning', 'risk', 'spy', 'index', 'momentum'
            ]
        }
    
    def classify_intent(self, query: str) -> List[Tuple[str, float]]:
        """
        Classify the intent of a query
        
        Args:
            query: User's question/request
            
        Returns:
            List of (agent_name, confidence) tuples
        """
        query_lower = query.lower()
        scores = {}
        
        # Check for explicit symbol mentions (equity focused)
        symbol_pattern = r'\b[A-Z]{1,5}\b'
        if re.search(symbol_pattern, query):
            scores['equity'] = scores.get('equity', 0) + 0.5
        
        # Pattern matching
        for agent_name, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in query_lower:
                    score += 1
            
            if score > 0:
                # Normalize score
                scores[agent_name] = score / len(patterns)
        
        # If no clear match, check agent capabilities
        if not scores:
            for agent_name, agent in self.agents.items():
                can_handle, confidence = agent.can_handle(query)
                if can_handle:
                    scores[agent_name] = confidence
        
        # Sort by confidence
        results = [(agent, conf) for agent, conf in scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top matches (threshold 0.1)
        return [(agent, conf) for agent, conf in results if conf > 0.1]
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Route query to appropriate agent(s) and aggregate results
        
        Args:
            query: User's question/request
            
        Returns:
            Dictionary with agent responses and metadata
        """
        # Classify intent
        intent_matches = self.classify_intent(query)
        
        if not intent_matches:
            # Default to market agent for general queries
            intent_matches = [('market', 0.5)]
        
        # Execute query on selected agents
        results = {
            'query': query,
            'agents': {},
            'predictions': [],
            'confidence': 0
        }
        
        # Handle multi-agent queries
        for agent_name, confidence in intent_matches[:2]:  # Limit to top 2 agents
            if agent_name in self.agents:
                try:
                    # Extract context from query
                    context = self._extract_context(query)
                    
                    # Execute agent analysis
                    agent_result = self.agents[agent_name].analyze(query, context)
                    
                    # Store result
                    results['agents'][agent_name] = agent_result
                    
                    # Aggregate predictions if any
                    if 'prediction' in agent_result:
                        results['predictions'].append(agent_result['prediction'])
                    
                except Exception as e:
                    results['agents'][agent_name] = {
                        'error': str(e),
                        'analysis_type': 'error',
                        'data': {},
                        'confidence': 0
                    }
        
        # Calculate overall confidence
        if results['agents']:
            confidences = [r.get('confidence', 0) for r in results['agents'].values()]
            results['confidence'] = sum(confidences) / len(confidences)
        
        # Add routing metadata
        results['routing'] = {
            'intent_matches': intent_matches,
            'primary_agent': intent_matches[0][0] if intent_matches else None
        }
        
        return results
    
    def _extract_context(self, query: str) -> Dict[str, Any]:
        """
        Extract context from query (symbols, dates, etc.)
        
        Args:
            query: User's question
            
        Returns:
            Context dictionary
        """
        context = {}
        
        # Extract stock symbols
        symbol_pattern = r'\b[A-Z]{1,5}\b'
        symbols = re.findall(symbol_pattern, query)
        if symbols:
            # Filter out common words that might match
            common_words = ['I', 'A', 'THE', 'AND', 'OR', 'FOR', 'TO', 'IS', 'IT', 'AT', 'BY']
            symbols = [s for s in symbols if s not in common_words]
            if symbols:
                context['symbol'] = symbols[0]  # Primary symbol
                context['symbols'] = symbols    # All symbols
        
        # Extract time horizons
        time_patterns = {
            '1D': r'\b(?:today|1\s*day|daily)\b',
            '1W': r'\b(?:week|weekly|7\s*days?)\b',
            '1M': r'\b(?:month|monthly|30\s*days?)\b',
            '3M': r'\b(?:quarter|quarterly|3\s*months?)\b',
            '6M': r'\b(?:6\s*months?|half\s*year)\b',
            '1Y': r'\b(?:year|yearly|annual|12\s*months?)\b'
        }
        
        for horizon, pattern in time_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                context['horizon'] = horizon
                break
        
        # Extract specific analysis types
        if 'backtest' in query.lower():
            context['analysis_type'] = 'backtest'
        elif 'predict' in query.lower() or 'forecast' in query.lower():
            context['analysis_type'] = 'prediction'
        elif 'simulate' in query.lower() or 'simulation' in query.lower():
            context['analysis_type'] = 'simulation'
        
        return context
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """
        Get capabilities of all agents
        
        Returns:
            Dictionary of agent_name -> capabilities list
        """
        capabilities = {}
        for name, agent in self.agents.items():
            capabilities[name] = agent.capabilities
        return capabilities
    
    def suggest_queries(self, current_context: Dict[str, Any]) -> List[str]:
        """
        Suggest follow-up queries based on current context
        
        Args:
            current_context: Current analysis context
            
        Returns:
            List of suggested queries
        """
        suggestions = []
        
        # Based on last agent used
        if 'primary_agent' in current_context:
            agent = current_context['primary_agent']
            
            if agent == 'macro':
                suggestions.extend([
                    "What's the impact on different sectors?",
                    "Show historical recession indicators",
                    "Predict GDP growth next quarter",
                    "Analyze Fed policy implications"
                ])
            elif agent == 'equity':
                symbol = current_context.get('symbol', 'AAPL')
                suggestions.extend([
                    f"Compare {symbol} to peers",
                    f"Predict {symbol} earnings",
                    f"Backtest momentum strategy on {symbol}",
                    f"Show insider trading for {symbol}"
                ])
            elif agent == 'market':
                suggestions.extend([
                    "Show sector rotation signals",
                    "Analyze options flow",
                    "What's the volatility forecast?",
                    "Detect market regime"
                ])
        
        # Generic suggestions
        suggestions.extend([
            "What's the market outlook?",
            "Show top opportunities",
            "Run portfolio simulation"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions