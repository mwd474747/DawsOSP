"""
Entity Extraction System for Smart Patterns

Uses Instructor + Pydantic for reliable entity extraction from natural language queries.
Supports multiple entity types and provides structured output for pattern routing.
"""

import os
from typing import Optional, List, Literal
from enum import Enum
from pydantic import BaseModel, Field
import instructor
from anthropic import Anthropic


class AnalysisDepth(str, Enum):
    """Analysis depth preference"""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class AnalysisType(str, Enum):
    """Type of analysis requested"""
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    VALUATION = "valuation"
    RISK = "risk"
    SENTIMENT = "sentiment"
    COMPREHENSIVE = "comprehensive"


class RiskProfile(str, Enum):
    """Investor risk profile"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class StrategyType(str, Enum):
    """Investment strategy type"""
    VALUE = "value"
    GROWTH = "growth"
    DIVIDEND = "dividend"
    MOMENTUM = "momentum"
    GARP = "garp"  # Growth at Reasonable Price
    CONTRARIAN = "contrarian"


class Timeframe(str, Enum):
    """Analysis timeframe"""
    INTRADAY = "intraday"
    SHORT_TERM = "short_term"  # Days to weeks
    MEDIUM_TERM = "medium_term"  # Weeks to months
    LONG_TERM = "long_term"  # Months to years


class StockAnalysisEntities(BaseModel):
    """Entities for stock analysis queries"""
    symbol: Optional[str] = Field(None, description="Stock ticker symbol (e.g., AAPL, MSFT)")
    analysis_type: AnalysisType = Field(AnalysisType.COMPREHENSIVE, description="Type of analysis requested")
    depth: AnalysisDepth = Field(AnalysisDepth.STANDARD, description="Depth of analysis")
    timeframe: Optional[Timeframe] = Field(None, description="Analysis timeframe")
    
    class Config:
        use_enum_values = True


class PortfolioEntities(BaseModel):
    """Entities for portfolio analysis queries"""
    holdings: List[str] = Field(default_factory=list, description="List of stock symbols in portfolio")
    risk_profile: RiskProfile = Field(RiskProfile.MODERATE, description="Investor risk profile")
    focus_areas: List[str] = Field(default_factory=list, description="Specific areas to focus on (e.g., 'diversification', 'tech exposure')")
    depth: AnalysisDepth = Field(AnalysisDepth.STANDARD, description="Depth of analysis")
    
    class Config:
        use_enum_values = True


class MarketBriefingEntities(BaseModel):
    """Entities for market briefing queries"""
    interests: List[str] = Field(default_factory=list, description="Areas of interest (e.g., 'tech', 'energy', 'earnings')")
    sectors: List[str] = Field(default_factory=list, description="Specific sectors to cover")
    timeframe: Timeframe = Field(Timeframe.INTRADAY, description="Briefing timeframe")
    
    class Config:
        use_enum_values = True


class OpportunityEntities(BaseModel):
    """Entities for opportunity scanning queries"""
    strategy_type: StrategyType = Field(StrategyType.VALUE, description="Investment strategy to use")
    sectors: List[str] = Field(default_factory=list, description="Sectors to scan")
    risk_level: RiskProfile = Field(RiskProfile.MODERATE, description="Acceptable risk level")
    criteria: List[str] = Field(default_factory=list, description="Additional screening criteria")
    
    class Config:
        use_enum_values = True


class RiskAnalysisEntities(BaseModel):
    """Entities for risk analysis queries"""
    target: str = Field(..., description="Symbol or 'portfolio' to analyze")
    risk_factors: List[str] = Field(default_factory=list, description="Specific risk factors to evaluate")
    timeframe: Timeframe = Field(Timeframe.MEDIUM_TERM, description="Risk assessment timeframe")
    
    class Config:
        use_enum_values = True


class QueryIntent(BaseModel):
    """Classified user intent with extracted entities"""
    intent_type: Literal["stock_analysis", "portfolio_review", "market_briefing", "opportunity_scan", "risk_analysis", "unknown"] = Field(
        ..., description="The type of query the user is making"
    )
    confidence: float = Field(..., description="Confidence in intent classification (0-1)")
    reasoning: str = Field(..., description="Brief explanation of why this intent was chosen")


class EntityExtractor:
    """
    Extracts structured entities from natural language queries using Instructor.
    
    Uses Anthropic Claude with structured outputs for reliable entity extraction.
    """
    
    def __init__(self):
        """Initialize entity extractor with Anthropic client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        # Create Instructor client with Anthropic
        self.client = instructor.from_anthropic(Anthropic(api_key=api_key))
    
    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify user query intent.
        
        Args:
            query: Natural language query from user
            
        Returns:
            QueryIntent with classified intent type and confidence
        """
        try:
            intent = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Classify this financial query into one of these intent types:
- stock_analysis: Analyzing a specific stock
- portfolio_review: Reviewing a portfolio or multiple holdings
- market_briefing: Getting market overview or news summary
- opportunity_scan: Finding investment opportunities
- risk_analysis: Assessing risks
- unknown: Cannot determine intent

Query: "{query}"

Provide the intent type, your confidence (0-1), and reasoning."""
                }],
                response_model=QueryIntent
            )
            return intent
        except Exception as e:
            # Fallback to unknown intent
            return QueryIntent(
                intent_type="unknown",
                confidence=0.0,
                reasoning=f"Error in classification: {str(e)}"
            )
    
    def extract_stock_analysis_entities(self, query: str) -> StockAnalysisEntities:
        """Extract entities for stock analysis queries"""
        try:
            return self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Extract stock analysis entities from this query: "{query}"

Extract:
- symbol: Stock ticker (e.g., AAPL, MSFT) 
- analysis_type: fundamental, technical, valuation, risk, sentiment, or comprehensive
- depth: quick, standard, or deep
- timeframe: intraday, short_term, medium_term, or long_term (if mentioned)

Use defaults if not explicitly stated."""
                }],
                response_model=StockAnalysisEntities
            )
        except Exception as e:
            # Return defaults on error
            return StockAnalysisEntities()
    
    def extract_portfolio_entities(self, query: str) -> PortfolioEntities:
        """Extract entities for portfolio analysis queries"""
        try:
            return self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Extract portfolio analysis entities from this query: "{query}"

Extract:
- holdings: List of stock tickers mentioned
- risk_profile: conservative, moderate, or aggressive
- focus_areas: Specific concerns like 'diversification', 'sector allocation', etc.
- depth: quick, standard, or deep

Use defaults if not explicitly stated."""
                }],
                response_model=PortfolioEntities
            )
        except Exception as e:
            return PortfolioEntities()
    
    def extract_market_briefing_entities(self, query: str) -> MarketBriefingEntities:
        """Extract entities for market briefing queries"""
        try:
            return self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Extract market briefing entities from this query: "{query}"

Extract:
- interests: Topics of interest (e.g., 'tech', 'earnings', 'fed policy')
- sectors: Specific sectors mentioned
- timeframe: intraday, short_term, medium_term, or long_term

Use defaults if not explicitly stated."""
                }],
                response_model=MarketBriefingEntities
            )
        except Exception as e:
            return MarketBriefingEntities()
    
    def extract_opportunity_entities(self, query: str) -> OpportunityEntities:
        """Extract entities for opportunity scanning queries"""
        try:
            return self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Extract opportunity scanning entities from this query: "{query}"

Extract:
- strategy_type: value, growth, dividend, momentum, garp, or contrarian
- sectors: Sectors to focus on
- risk_level: conservative, moderate, or aggressive
- criteria: Additional screening criteria

Use defaults if not explicitly stated."""
                }],
                response_model=OpportunityEntities
            )
        except Exception as e:
            return OpportunityEntities()
    
    def extract_risk_analysis_entities(self, query: str) -> RiskAnalysisEntities:
        """Extract entities for risk analysis queries"""
        try:
            return self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Extract risk analysis entities from this query: "{query}"

Extract:
- target: Stock symbol or 'portfolio'
- risk_factors: Specific risks to evaluate (e.g., 'market risk', 'credit risk')
- timeframe: intraday, short_term, medium_term, or long_term

The target field is required."""
                }],
                response_model=RiskAnalysisEntities
            )
        except Exception as e:
            # Need at least a target
            return RiskAnalysisEntities(target="unknown")
    
    def extract_entities(self, query: str) -> dict:
        """
        Main extraction method - classifies intent then extracts relevant entities.
        
        Args:
            query: Natural language query from user
            
        Returns:
            Dict with intent and extracted entities
        """
        # First classify intent
        intent = self.classify_intent(query)
        
        # Extract entities based on intent
        entities = None
        if intent.intent_type == "stock_analysis":
            entities = self.extract_stock_analysis_entities(query)
        elif intent.intent_type == "portfolio_review":
            entities = self.extract_portfolio_entities(query)
        elif intent.intent_type == "market_briefing":
            entities = self.extract_market_briefing_entities(query)
        elif intent.intent_type == "opportunity_scan":
            entities = self.extract_opportunity_entities(query)
        elif intent.intent_type == "risk_analysis":
            entities = self.extract_risk_analysis_entities(query)
        
        return {
            "intent": intent.model_dump(),
            "entities": entities.model_dump() if entities else {},
            "original_query": query
        }
