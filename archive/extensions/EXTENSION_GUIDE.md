# 🏗️ DawsOS Extension Guide: Patterns & Functions

## Overview

DawsOS uses a **Trinity Architecture** designed for extensibility:

```
User Query → Entity Extractor → Pattern Engine → Executor → Registry → Agents
                  ↓                    ↓              ↓          ↓         ↓
              (Claude AI)        (JSON Patterns)  (Actions)  (Caps)   (15 Agents)
```

This guide shows how to extend each component to add new functionality.

---

## 📊 Extension Hierarchy

### 1. **Adding Simple Patterns** (Easy)
For new analysis types that use existing capabilities.
- ✅ No code changes needed
- ✅ Just add JSON pattern file
- ⏱️ 15-30 minutes

### 2. **Adding Smart Patterns** (Medium)
For intelligent conversational patterns with entity extraction.
- ⚠️ Requires entity extractor updates
- ⚠️ Requires chat processor routing
- ⏱️ 1-2 hours

### 3. **Adding New Capabilities** (Advanced)
For entirely new data sources or analysis methods.
- 🔴 Requires agent implementation
- 🔴 Requires registry updates
- ⏱️ 4-8 hours

---

## 🎯 Extension Path 1: Adding Simple Patterns

**Use Case**: You want to add a new analysis type using existing capabilities.

### Example: Add "Sector Rotation" Pattern

**Step 1: Create Pattern File**
```bash
dawsos/patterns/market/sector_rotation.json
```

**Step 2: Define Pattern**
```json
{
  "id": "sector_rotation",
  "name": "Sector Rotation Analysis",
  "description": "Analyze sector momentum and rotation signals",
  "category": "market",
  "priority": 70,
  "triggers": [
    "sector rotation",
    "which sectors are leading",
    "sector momentum",
    "sector trends"
  ],
  "steps": [
    {
      "description": "Fetch sector performance data",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_analyze_sector_performance",
        "context": {
          "sectors": ["Technology", "Healthcare", "Energy", "Financials"],
          "timeframe": "3_months"
        }
      },
      "save_as": "sector_data"
    },
    {
      "description": "Detect rotation signals",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_detect_regime_shifts",
        "context": {
          "data": "{sector_data}"
        }
      },
      "save_as": "rotation_signals"
    }
  ],
  "template": "# Sector Rotation Analysis\n\n## Current Leaders\n{sector_data.top_performers}\n\n## Rotation Signals\n{rotation_signals}\n\n## Recommendation\nBased on momentum, consider rotating into: {rotation_signals.recommended_sectors}",
  "response_type": "analysis"
}
```

**Step 3: Test**
Pattern automatically loads on next app restart. Trigger with: "Show me sector rotation"

**✅ That's it!** No code changes needed.

---

## 🧠 Extension Path 2: Adding Smart Patterns

**Use Case**: You want intelligent, conversational patterns with natural language understanding.

### Example: Add "Smart Dividend Analysis" Pattern

**Step 1: Define Entity Model**

Edit: `dawsos/core/entity_extractor.py`

```python
class DividendAnalysisEntities(BaseModel):
    """Entities for dividend analysis queries"""
    min_yield: Optional[float] = Field(default=3.0, description="Minimum dividend yield")
    sectors: Optional[List[str]] = Field(default=None, description="Sectors to focus on")
    growth_preference: Optional[Literal["high_yield", "dividend_growth", "balanced"]] = Field(
        default="balanced", 
        description="Dividend strategy preference"
    )
    risk_tolerance: Optional[Literal["conservative", "moderate", "aggressive"]] = Field(
        default="moderate",
        description="Risk tolerance"
    )
    depth: Optional[Literal["quick", "standard", "deep"]] = Field(
        default="standard",
        description="Analysis depth"
    )
```

**Step 2: Add Intent Type**

Edit `QueryIntent` enum in same file:
```python
intent_type: Literal[
    "stock_analysis", 
    "portfolio_review", 
    "market_briefing", 
    "opportunity_scan", 
    "risk_analysis", 
    "economic_briefing", 
    "economic_outlook",
    "dividend_analysis",  # NEW
    "unknown"
]
```

**Step 3: Add Extraction Method**

```python
def extract_dividend_analysis_entities(self, query: str) -> DividendAnalysisEntities:
    """Extract entities for dividend analysis queries"""
    try:
        return self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Extract dividend analysis parameters from this query.

Query: "{query}"

Focus on:
- Minimum yield requirement
- Sector preferences
- Strategy (high yield vs growth)
- Risk tolerance
"""
            }],
            response_model=DividendAnalysisEntities
        )
    except Exception as e:
        return DividendAnalysisEntities()
```

**Step 4: Add to Entity Extraction Router**

In `extract_entities` method:
```python
elif intent.intent_type == "dividend_analysis":
    entities = self.extract_dividend_analysis_entities(query)
```

**Step 5: Add Chat Processor Routing**

Edit: `dawsos/core/enhanced_chat_processor.py`

```python
self.intent_to_pattern = {
    "stock_analysis": "smart_stock_analysis",
    "portfolio_review": "smart_portfolio_review",
    "market_briefing": "smart_market_briefing",
    "opportunity_scan": "smart_opportunity_finder",
    "risk_analysis": "smart_risk_analyzer",
    "economic_briefing": "smart_economic_briefing",
    "economic_outlook": "smart_economic_outlook",
    "dividend_analysis": "smart_dividend_analysis"  # NEW
}
```

**Step 6: Create Smart Pattern**

`dawsos/patterns/smart/smart_dividend_analysis.json`

```json
{
  "id": "smart_dividend_analysis",
  "name": "Smart Dividend Analysis",
  "description": "Intelligent dividend stock screening with NLU",
  "category": "smart",
  "priority": 95,
  "triggers": [
    "dividend stocks",
    "dividend analysis",
    "high yield stocks",
    "dividend growth",
    "income investing"
  ],
  "entities": [
    "min_yield",
    "sectors",
    "growth_preference",
    "risk_tolerance",
    "depth"
  ],
  "steps": [
    {
      "description": "Screen dividend stocks",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_screen_stocks",
        "context": {
          "criteria": {
            "min_dividend_yield": "{min_yield}",
            "sectors": "{sectors}",
            "strategy": "{growth_preference}"
          }
        }
      },
      "save_as": "dividend_stocks"
    },
    {
      "description": "Analyze dividend sustainability",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_analyze_fundamentals",
        "context": {
          "stocks": "{dividend_stocks.tickers}",
          "focus": "dividend_metrics"
        }
      },
      "save_as": "sustainability_analysis"
    },
    {
      "description": "Generate intelligent dividend recommendations",
      "action": "synthesize",
      "params": {
        "template": "# Dividend Analysis\n\n## Screened Stocks\n{dividend_stocks}\n\n## Sustainability Analysis\n{sustainability_analysis}\n\nBased on your preferences (min yield: {min_yield}%, strategy: {growth_preference}, risk: {risk_tolerance}), provide:\n\n1. Top 5 dividend stock recommendations\n2. Dividend safety scores\n3. Growth outlook\n4. Risk assessment\n5. Portfolio allocation suggestion",
        "outputs": {
          "dividend_stocks": "{dividend_stocks}",
          "sustainability_analysis": "{sustainability_analysis}"
        }
      },
      "save_as": "recommendations"
    }
  ],
  "template": "# Smart Dividend Analysis\n\n{recommendations}",
  "response_type": "recommendations"
}
```

**Step 7: Test**

Restart app, then ask: "Find me high-yield dividend stocks in healthcare"

---

## 🔧 Extension Path 3: Adding New Capabilities

**Use Case**: You need entirely new data sources or analysis methods.

### Example: Add Twitter Sentiment Capability

**Step 1: Create Agent Implementation**

Create: `dawsos/agents/social_sentiment_agent.py`

```python
"""
Social Sentiment Agent
Analyzes social media sentiment for stocks/market
"""

import tweepy
from typing import Dict, Any, List
import os

class SocialSentimentAgent:
    """Agent for social media sentiment analysis"""
    
    def __init__(self):
        self.name = "Social Sentiment Agent"
        self.capabilities = [
            "can_analyze_twitter_sentiment",
            "can_track_social_mentions",
            "can_detect_viral_trends"
        ]
        # Initialize Twitter API
        self.client = tweepy.Client(
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN")
        )
    
    def can_analyze_twitter_sentiment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Twitter sentiment for a stock or topic
        
        Args:
            context: {
                "ticker": "AAPL" or "topic": "AI stocks",
                "timeframe": "24h" | "7d" | "30d",
                "include_influencers": bool
            }
        
        Returns:
            {
                "sentiment_score": -1.0 to 1.0,
                "volume": int (number of mentions),
                "top_tweets": [...],
                "trending": bool,
                "influencer_sentiment": {...}
            }
        """
        ticker = context.get("ticker")
        topic = context.get("topic", f"${ticker}")
        timeframe = context.get("timeframe", "24h")
        
        # Search recent tweets
        query = f"{topic} -is:retweet lang:en"
        tweets = self.client.search_recent_tweets(
            query=query,
            max_results=100,
            tweet_fields=['created_at', 'public_metrics', 'author_id']
        )
        
        # Analyze sentiment (simplified - use real NLP in production)
        positive_keywords = ['bullish', 'moon', 'buy', 'strong', 'breakout']
        negative_keywords = ['bearish', 'sell', 'crash', 'weak', 'dump']
        
        sentiment_scores = []
        total_volume = 0
        
        for tweet in tweets.data or []:
            text = tweet.text.lower()
            score = 0
            
            for word in positive_keywords:
                if word in text:
                    score += 1
            for word in negative_keywords:
                if word in text:
                    score -= 1
            
            sentiment_scores.append(score)
            total_volume += 1
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        normalized_sentiment = max(-1, min(1, avg_sentiment / 3))  # Normalize to -1 to 1
        
        return {
            "sentiment_score": normalized_sentiment,
            "sentiment_label": self._label_sentiment(normalized_sentiment),
            "volume": total_volume,
            "top_tweets": [t.text for t in (tweets.data or [])[:5]],
            "trending": total_volume > 50,
            "timeframe": timeframe,
            "ticker": ticker,
            "agent": self.name,
            "capability": "can_analyze_twitter_sentiment"
        }
    
    def _label_sentiment(self, score: float) -> str:
        """Convert numeric score to label"""
        if score > 0.3:
            return "Very Bullish"
        elif score > 0.1:
            return "Bullish"
        elif score > -0.1:
            return "Neutral"
        elif score > -0.3:
            return "Bearish"
        else:
            return "Very Bearish"
    
    def can_track_social_mentions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Track mention volume trends"""
        # Implementation here
        pass
    
    def can_detect_viral_trends(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect viral stock trends"""
        # Implementation here
        pass
```

**Step 2: Register Agent in Trinity**

Edit: `dawsos/core/agent_registry.py`

```python
from dawsos.agents.social_sentiment_agent import SocialSentimentAgent

class AgentRegistry:
    def __init__(self):
        # ... existing agents ...
        self.agents = {
            # ... existing ...
            "social_sentiment": SocialSentimentAgent(),
        }
        
        # Register new capabilities
        self.capability_map = {
            # ... existing ...
            "can_analyze_twitter_sentiment": "social_sentiment",
            "can_track_social_mentions": "social_sentiment",
            "can_detect_viral_trends": "social_sentiment",
        }
```

**Step 3: Add Secret for API Key**

User will need to add `TWITTER_BEARER_TOKEN` to secrets.

**Step 4: Create Pattern Using New Capability**

`dawsos/patterns/social/social_sentiment.json`

```json
{
  "id": "social_sentiment_analysis",
  "name": "Social Sentiment Analysis",
  "description": "Analyze Twitter sentiment for stocks",
  "category": "social",
  "priority": 75,
  "triggers": [
    "twitter sentiment",
    "social sentiment",
    "what's twitter saying",
    "social media buzz"
  ],
  "steps": [
    {
      "description": "Analyze Twitter sentiment",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_analyze_twitter_sentiment",
        "context": {
          "ticker": "{ticker}",
          "timeframe": "24h",
          "include_influencers": true
        }
      },
      "save_as": "sentiment"
    }
  ],
  "template": "# Social Sentiment: ${ticker}\n\n**Sentiment**: {sentiment.sentiment_label} ({sentiment.sentiment_score})\n**Volume**: {sentiment.volume} mentions\n**Trending**: {sentiment.trending}\n\n## Top Tweets\n{sentiment.top_tweets}",
  "response_type": "sentiment"
}
```

**Step 5: Test**

Ask: "What's the Twitter sentiment for TSLA?"

---

## 🎨 Advanced Extension Patterns

### 1. **Multi-Step Intelligent Workflows**

Combine multiple capabilities with conditional logic:

```json
{
  "steps": [
    {
      "description": "Check market conditions",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_detect_market_regime"
      },
      "save_as": "regime"
    },
    {
      "description": "If bullish, find growth stocks",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_screen_stocks",
        "context": {"style": "growth"}
      },
      "save_as": "opportunities",
      "condition": "{regime.sentiment} == 'bullish'"
    },
    {
      "description": "If bearish, find defensive stocks",
      "action": "execute_through_registry",
      "params": {
        "capability": "can_screen_stocks",
        "context": {"style": "defensive"}
      },
      "save_as": "opportunities",
      "condition": "{regime.sentiment} == 'bearish'"
    }
  ]
}
```

### 2. **Claude Synthesis for Complex Analysis**

Use "synthesize" action to combine multiple data sources:

```json
{
  "action": "synthesize",
  "params": {
    "template": "Analyze this company:\n\nFundamentals: {fundamentals}\nTechnicals: {technicals}\nSentiment: {sentiment}\nNews: {news}\n\nProvide: 1) Overall score, 2) Key strengths, 3) Key risks, 4) Recommendation",
    "outputs": {
      "fundamentals": "{fundamental_data}",
      "technicals": "{technical_data}",
      "sentiment": "{social_sentiment}",
      "news": "{recent_news}"
    }
  }
}
```

### 3. **Dynamic Parameter Injection**

Use entity extraction to customize analysis:

```json
{
  "entities": ["timeframe", "risk_level", "sectors"],
  "steps": [
    {
      "params": {
        "context": {
          "lookback_days": "{timeframe}",
          "max_volatility": "{risk_level}",
          "allowed_sectors": "{sectors}"
        }
      }
    }
  ]
}
```

---

## 🚀 Best Practices

### Pattern Design

1. **Single Responsibility**: One pattern = one analysis type
2. **Composability**: Use existing capabilities before creating new ones
3. **Clear Triggers**: 3-7 trigger phrases covering user intent variations
4. **Sensible Defaults**: Use defaults for optional entities
5. **Error Handling**: Patterns should gracefully handle missing data

### Capability Design

1. **Focused Purpose**: One capability = one specific function
2. **Standard Response Format**: Always return dict with standard keys
3. **Metadata**: Include `agent`, `capability`, `timestamp` in responses
4. **Error Returns**: Return `{"error": "message"}` on failure
5. **Documentation**: Document params and return format clearly

### Entity Extraction

1. **Minimal Entities**: Only extract what you'll actually use
2. **Sensible Defaults**: Avoid forcing user to specify everything
3. **Clear Descriptions**: Help Claude understand extraction intent
4. **Validation**: Use Pydantic for type safety

---

## 📊 Extension Opportunities

### High-Impact Extensions

1. **Options Analysis**
   - Capability: `can_analyze_options_flow`
   - Pattern: Smart options strategy recommendations
   - Data: Options chain, IV, flow data

2. **Crypto Integration**
   - Capability: `can_analyze_crypto_markets`
   - Pattern: Crypto market briefing, DeFi opportunities
   - Data: Coinbase/Binance APIs

3. **Backtesting**
   - Capability: `can_backtest_strategy`
   - Pattern: Strategy testing with historical data
   - Integration: Backtrader/QuantConnect

4. **Real-time Alerts**
   - Capability: `can_monitor_price_alerts`
   - Pattern: Custom alert rules
   - Integration: Webhook system

5. **Portfolio Tracking**
   - Capability: `can_track_portfolio_performance`
   - Pattern: Live P&L tracking, rebalancing alerts
   - Storage: JSON-based position tracking

### Quick Wins

1. **More Economic Patterns**
   - "Labor market analysis"
   - "Housing market trends"
   - "Commodity outlook"

2. **Sector-Specific Analysis**
   - "Tech sector deep dive"
   - "Healthcare regulatory analysis"
   - "Energy transition trends"

3. **Event-Driven Patterns**
   - "Earnings reaction analysis"
   - "Fed meeting impact"
   - "IPO evaluation"

---

## 🔍 Debugging Extensions

### Pattern Not Triggering?

1. Check pattern loaded: Look for "Loaded X patterns" in logs
2. Test trigger: Try exact trigger phrase from JSON
3. Check priority: Higher priority patterns match first
4. Review logs: Enable debug logging to see pattern matching

### Capability Not Working?

1. Check agent registered in `agent_registry.py`
2. Verify capability name matches exactly
3. Test capability directly: Call via registry
4. Check API keys: Ensure secrets are set

### Entity Extraction Failing?

1. Check intent type in `QueryIntent` enum
2. Verify extraction method exists
3. Test Claude prompt: Run extraction standalone
4. Check routing: Ensure `intent_to_pattern` mapping exists

---

## 📚 Reference Architecture

```
dawsos/
├── agents/                    # Agent implementations
│   ├── fred_agent.py         # Economic data
│   ├── market_agent.py       # Market analysis
│   └── YOUR_NEW_AGENT.py     # Add new agents here
│
├── core/
│   ├── entity_extractor.py   # Add new entity models here
│   ├── enhanced_chat_processor.py  # Add intent routing here
│   ├── pattern_engine.py     # Pattern loading & matching
│   └── agent_registry.py     # Register new agents here
│
├── patterns/
│   ├── smart/                 # Smart patterns (NLU)
│   │   └── YOUR_SMART_PATTERN.json
│   ├── market/                # Market analysis patterns
│   ├── economy/               # Economic patterns
│   └── YOUR_CATEGORY/         # Add new categories
│       └── YOUR_PATTERN.json
│
└── capabilities/              # Capability implementations
    ├── fred_data.py
    └── YOUR_CAPABILITY.py
```

---

## ✅ Extension Checklist

### Adding Simple Pattern
- [ ] Create pattern JSON file
- [ ] Define triggers (3-7 phrases)
- [ ] Define steps using existing capabilities
- [ ] Add template for response formatting
- [ ] Test with trigger phrases

### Adding Smart Pattern
- [ ] Define entity model in `entity_extractor.py`
- [ ] Add intent type to `QueryIntent`
- [ ] Implement extraction method
- [ ] Add routing in `enhanced_chat_processor.py`
- [ ] Create smart pattern JSON
- [ ] Test end-to-end flow

### Adding New Capability
- [ ] Create agent implementation
- [ ] Define capability methods
- [ ] Register agent in `agent_registry.py`
- [ ] Add capability to capability_map
- [ ] Create patterns using capability
- [ ] Add API keys to secrets (if needed)
- [ ] Test capability directly
- [ ] Test via pattern execution

---

## 🎯 Next Steps

Start with **simple patterns** to get familiar with the system, then progress to **smart patterns** and finally **new capabilities**.

**Recommended Learning Path**:
1. Add a simple market pattern (1 hour)
2. Add a smart conversational pattern (2-3 hours)
3. Add a new data source capability (1 day)
4. Combine multiple capabilities for advanced workflows (2-3 days)

**The Trinity architecture is designed for extensibility - you can add sophisticated new features without modifying core logic!**
