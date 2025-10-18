# 🚀 DawsOS Extension Quick Reference

## Three Ways to Extend DawsOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    Extension Hierarchy                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣  SIMPLE PATTERNS (15-30 min)                              │
│     ├─ Add JSON file to patterns/                              │
│     ├─ Use existing capabilities                               │
│     └─ No code changes needed                                  │
│                                                                 │
│  2️⃣  SMART PATTERNS (1-2 hours)                               │
│     ├─ Add entity extraction (Claude NLU)                      │
│     ├─ Add chat routing                                        │
│     ├─ Create smart pattern JSON                               │
│     └─ Conversational + intelligent                            │
│                                                                 │
│  3️⃣  NEW CAPABILITIES (4-8 hours)                             │
│     ├─ Create agent implementation                             │
│     ├─ Register in agent registry                              │
│     ├─ Add new data sources                                    │
│     └─ Create patterns using capability                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure for Extensions

```
dawsos/
│
├── patterns/                          👈 Add new patterns here
│   ├── smart/                         Smart (conversational) patterns
│   │   ├── smart_stock_analysis.json
│   │   ├── smart_economic_briefing.json
│   │   └── YOUR_SMART_PATTERN.json    ← Add here
│   │
│   ├── market/                        Market analysis patterns
│   ├── economy/                       Economic patterns
│   └── YOUR_CATEGORY/                 ← Create new category
│       └── your_pattern.json
│
├── core/
│   ├── entity_extractor.py            👈 Add entity models here
│   ├── enhanced_chat_processor.py     👈 Add routing here
│   ├── pattern_engine.py              (Don't modify)
│   └── agent_registry.py              👈 Register new agents
│
├── agents/                            👈 Add new agents here
│   ├── fred_agent.py                  Economic data agent
│   ├── market_agent.py                Market analysis agent
│   └── YOUR_AGENT.py                  ← Create new agent
│
└── capabilities/                      👈 Standalone capabilities
    ├── fred_data.py
    └── your_capability.py
```

---

## ⚡ Quick Start Examples

### Example 1: Simple Pattern (Sector Rotation)

**File**: `dawsos/patterns/market/sector_rotation.json`

```json
{
  "id": "sector_rotation",
  "name": "Sector Rotation Analysis",
  "triggers": ["sector rotation", "which sectors are leading"],
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "capability": "can_analyze_sector_performance"
      },
      "save_as": "sectors"
    }
  ],
  "template": "# Sector Rotation\n\n{sectors}"
}
```

**That's it!** Pattern loads automatically on restart.

---

### Example 2: Smart Pattern (Dividend Analysis)

**Step 1**: Add entity model to `entity_extractor.py`
```python
class DividendAnalysisEntities(BaseModel):
    min_yield: float = 3.0
    sectors: Optional[List[str]] = None
    strategy: Literal["high_yield", "growth"] = "balanced"
```

**Step 2**: Add intent routing to `enhanced_chat_processor.py`
```python
self.intent_to_pattern = {
    # ... existing ...
    "dividend_analysis": "smart_dividend_analysis"
}
```

**Step 3**: Create pattern
```json
{
  "id": "smart_dividend_analysis",
  "category": "smart",
  "entities": ["min_yield", "sectors", "strategy"],
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "capability": "can_screen_stocks",
        "context": {
          "min_dividend_yield": "{min_yield}",
          "sectors": "{sectors}"
        }
      }
    }
  ]
}
```

---

### Example 3: New Capability (Twitter Sentiment)

**Step 1**: Create agent (`agents/social_agent.py`)
```python
class SocialSentimentAgent:
    def can_analyze_twitter_sentiment(self, context):
        ticker = context.get("ticker")
        # Fetch & analyze tweets
        return {
            "sentiment": 0.65,
            "sentiment_label": "Bullish",
            "volume": 1250
        }
```

**Step 2**: Register in `agent_registry.py`
```python
from dawsos.agents.social_agent import SocialSentimentAgent

self.agents = {
    # ... existing ...
    "social": SocialSentimentAgent()
}

self.capability_map = {
    # ... existing ...
    "can_analyze_twitter_sentiment": "social"
}
```

**Step 3**: Create pattern using it
```json
{
  "id": "social_sentiment",
  "triggers": ["twitter sentiment", "social buzz"],
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "capability": "can_analyze_twitter_sentiment",
        "context": {"ticker": "{ticker}"}
      }
    }
  ]
}
```

---

## 🎯 High-Impact Extension Ideas

| Extension | Effort | Impact | Files to Add |
|-----------|--------|--------|--------------|
| **Options Analysis** | Medium | High | `agents/options_agent.py` + pattern |
| **Crypto Markets** | Medium | High | `agents/crypto_agent.py` + patterns |
| **Portfolio Tracking** | High | Very High | `agents/portfolio_agent.py` + UI |
| **Real-time Alerts** | High | High | `agents/alert_agent.py` + webhook |
| **Backtesting** | Very High | Very High | `agents/backtest_agent.py` + integration |
| **More Economy Patterns** | Low | Medium | Just add JSON patterns |
| **Sector Deep Dives** | Low | Medium | Just add JSON patterns |

---

## 🔑 Key Concepts

### Pattern Actions

| Action | Purpose | Example |
|--------|---------|---------|
| `execute_through_registry` | Call agent capability | Fetch data, analyze |
| `synthesize` | Claude synthesis | Combine multiple data sources |
| `query_knowledge` | Knowledge graph lookup | Historical patterns |

### Entity Extraction Flow

```
User Query → Claude (via Instructor) → Pydantic Model → Pattern Context
    ↓              ↓                        ↓                  ↓
"Find high     Detects intent:        DividendEntities    min_yield: 4.0
 yield stocks"  dividend_analysis      (validated)         sectors: null
```

### Capability Response Format

```python
{
    "result": {...},           # Your data
    "agent": "Agent Name",     # Which agent processed
    "capability": "can_xxx",   # Which capability
    "timestamp": "...",        # When processed
    "error": None              # Or error message
}
```

---

## ✅ Testing Your Extension

### 1. Test Simple Pattern
```bash
# Restart app
# Go to Trinity Chat
# Type trigger phrase: "sector rotation"
```

### 2. Test Smart Pattern
```bash
# Restart app
# Go to Trinity Chat
# Type natural query: "Find me high-yield dividend stocks in tech"
# Check logs for entity extraction
```

### 3. Test New Capability
```python
# Test capability directly first
from dawsos.core.agent_registry import AgentRegistry

registry = AgentRegistry()
result = registry.execute_by_capability(
    "can_your_capability",
    {"param": "value"}
)
print(result)
```

---

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| Pattern not triggering | Check trigger phrases, pattern loaded in logs |
| Capability not found | Verify registered in `agent_registry.py` |
| Entity extraction failing | Check intent type in `QueryIntent` enum |
| Data not showing | Check template variable names match step `save_as` |
| API errors | Verify secrets set, check API key validity |

---

## 📚 Current System Status

**Loaded**: 58 patterns (5 market smart + 2 economy smart + 51 traditional)
**Agents**: 15 specialized agents
**Capabilities**: 40+ registered capabilities
**Categories**: market, economy, smart, portfolio, risk

**Ready for extension!**

---

## 🎓 Learning Path

1. **Day 1**: Read `EXTENSION_GUIDE.md` (comprehensive)
2. **Day 2**: Add a simple pattern (practice)
3. **Day 3**: Add a smart pattern (entity extraction)
4. **Week 2**: Add a new capability (full integration)
5. **Week 3**: Build complex multi-step workflows

---

## 💡 Pro Tips

1. **Start Small**: Copy existing pattern, modify incrementally
2. **Test Incrementally**: Test each component separately
3. **Use Logs**: Enable debug logging to see execution flow
4. **Reuse Capabilities**: Check existing capabilities before creating new
5. **Follow Conventions**: Match naming patterns for consistency
6. **Document**: Add clear descriptions to help future you

---

## 🔗 Related Files

- **Full Guide**: `EXTENSION_GUIDE.md` (comprehensive 400+ lines)
- **Economic Chat**: `ECONOMIC_CHAT_GUIDE.md` (usage examples)
- **Architecture**: `replit.md` (system overview)
- **Patterns**: `dawsos/patterns/` (browse examples)

---

**The Trinity architecture makes DawsOS infinitely extensible.** 

**Add new features without modifying core code!** 🚀
