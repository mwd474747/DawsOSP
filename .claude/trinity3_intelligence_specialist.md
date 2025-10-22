# Trinity 3.0 Intelligence Specialist

**Your Role**: Port the intelligence layer (entity extraction + conversation memory) from DawsOS 2.0 to Trinity 3.0

**Timeline**: Week 1-2
**Deliverable**: Natural language understanding with multi-turn memory

---

## Mission

Enable Trinity 3.0 to understand natural language queries with the same intelligence as DawsOS 2.0:
- Extract entities (symbol, analysis_type, depth, timeframe) from queries
- Resolve references across conversation turns ("it", "that stock")
- Route intents to appropriate patterns
- Remember context for suggested follow-ups

---

## Week 1 Tasks

### Day 1: Setup

**Create Structure**:
```bash
mkdir -p trinity3/intelligence/schemas
touch trinity3/intelligence/__init__.py
touch trinity3/intelligence/entity_extractor.py
touch trinity3/intelligence/conversation_memory.py
touch trinity3/intelligence/enhanced_chat_processor.py
```

**Install Dependencies**:
```bash
cd trinity3
pip install instructor anthropic pydantic
```

**Test API**:
```python
import os
from anthropic import Anthropic

api_key = os.getenv("ANTHROPIC_API_KEY")
assert api_key, "Missing ANTHROPIC_API_KEY"

client = Anthropic(api_key=api_key)
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{"role": "user", "content": "Test"}]
)
print(f"API working: {response.content[0].text[:50]}")
```

---

### Day 2-3: Entity Extraction (406 lines)

**Source**: `dawsos/core/entity_extractor.py`
**Destination**: `trinity3/intelligence/entity_extractor.py`

**Port These Components**:

1. **Enums** (lines 16-56):
```python
class AnalysisDepth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"

class AnalysisType(str, Enum):
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    VALUATION = "valuation"
    RISK = "risk"
    SENTIMENT = "sentiment"
    COMPREHENSIVE = "comprehensive"

class Timeframe(str, Enum):
    INTRADAY = "intraday"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"

# ... 3 more enums
```

2. **Pydantic Schemas** (lines 58-131):
```python
class StockAnalysisEntities(BaseModel):
    symbol: Optional[str]
    analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE
    depth: AnalysisDepth = AnalysisDepth.STANDARD
    timeframe: Optional[Timeframe] = None

class PortfolioEntities(BaseModel): ...
class MarketBriefingEntities(BaseModel): ...
class OpportunityEntities(BaseModel): ...
class RiskAnalysisEntities(BaseModel): ...
class EconomicBriefingEntities(BaseModel): ...
class EconomicOutlookEntities(BaseModel): ...
class QueryIntent(BaseModel): ...
```

3. **EntityExtractor Class** (lines 142-406):
```python
class EntityExtractor:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = instructor.from_anthropic(Anthropic(api_key=api_key))

    def classify_intent(self, query: str) -> QueryIntent: ...
    def extract_stock_analysis_entities(self, query: str) -> StockAnalysisEntities: ...
    def extract_portfolio_entities(self, query: str) -> PortfolioEntities: ...
    # ... 5 more extraction methods

    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Main entry point - classifies intent and extracts entities"""
        intent = self.classify_intent(query)
        # Routes to appropriate extraction method
        # Returns unified dict with 'intent' and 'entities' keys
```

**Test Suite** (create `trinity3/tests/test_entity_extractor.py`):
```python
def test_stock_analysis_extraction():
    extractor = EntityExtractor()

    # Test 1: Basic symbol
    result = extractor.extract_entities("Analyze AAPL")
    assert result['entities']['symbol'] == "AAPL"
    assert result['entities']['analysis_type'] == "comprehensive"
    assert result['entities']['depth'] == "standard"

    # Test 2: Quick analysis
    result = extractor.extract_entities("Quick check on MSFT")
    assert result['entities']['symbol'] == "MSFT"
    assert result['entities']['depth'] == "quick"

    # Test 3: Deep dive
    result = extractor.extract_entities("Deep dive into Tesla")
    assert result['entities']['symbol'] == "TSLA"
    assert result['entities']['depth'] == "deep"

    # Test 4: Fundamental focus
    result = extractor.extract_entities("Analyze GOOGL fundamentals")
    assert result['entities']['analysis_type'] == "fundamental"

    # Test 5: Technical focus
    result = extractor.extract_entities("Technical analysis of NVDA")
    assert result['entities']['analysis_type'] == "technical"

    # ... 15 more tests (20 total required)
```

**Success Criteria**:
- 20 test queries, 18/20 must pass (90%+ accuracy)
- Intent classification confidence > 0.8
- All Pydantic schemas validate correctly
- No crashes on edge cases (empty string, gibberish, etc.)

---

### Day 4: Conversation Memory (254 lines)

**Source**: `dawsos/core/conversation_memory.py`
**Destination**: `trinity3/intelligence/conversation_memory.py`

**Port These Components**:

1. **ConversationTurn** (lines 13-31):
```python
class ConversationTurn:
    def __init__(self, user_query, assistant_response, entities, pattern_used):
        self.timestamp = datetime.now()
        self.user_query = user_query
        self.assistant_response = assistant_response
        self.entities = entities
        self.pattern_used = pattern_used

    def to_dict(self) -> Dict[str, Any]: ...
```

2. **ConversationMemory** (lines 34-254):
```python
class ConversationMemory:
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.history: List[ConversationTurn] = []
        self.recent_symbols: List[str] = []
        self.recent_sectors: List[str] = []
        self.recent_strategies: List[str] = []

    def add_turn(self, user_query, assistant_response, entities, pattern_used): ...
    def resolve_references(self, query: str) -> str: ...
    def get_context_for_llm(self, turns: int = 3) -> str: ...
    def get_recent_entities(self) -> Dict[str, List[str]]: ...
    def suggest_follow_up(self) -> List[str]: ...
    def clear(self): ...
```

**Key Method - Reference Resolution** (lines 121-157):
```python
def resolve_references(self, query: str) -> str:
    resolved = query
    query_lower = query.lower()

    # "it" or "that stock" → most recent symbol
    if re.search(r'\b(it|that stock|this stock)\b', query_lower):
        if self.recent_symbols:
            most_recent = self.recent_symbols[0]
            resolved = re.sub(r'\b(it|that stock|this stock)\b', most_recent, resolved, flags=re.IGNORECASE)

    # "them" or "those stocks" → recent holdings
    if re.search(r'\b(them|those stocks)\b', query_lower):
        if len(self.recent_symbols) > 1:
            symbols_str = ", ".join(self.recent_symbols[:5])
            resolved = re.sub(r'\b(them|those stocks)\b', symbols_str, resolved, flags=re.IGNORECASE)

    return resolved
```

**Add File Persistence**:
```python
def save_to_file(self, filepath: str = "trinity3/storage/conversation_history.json"):
    """Save conversation history to file"""
    with open(filepath, 'w') as f:
        json.dump([turn.to_dict() for turn in self.history], f, indent=2)

def load_from_file(self, filepath: str = "trinity3/storage/conversation_history.json"):
    """Load conversation history from file"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            for turn_data in data:
                # Reconstruct turns
                # Update recent_symbols, etc.
```

**Test Suite**:
```python
def test_reference_resolution():
    memory = ConversationMemory()

    # Turn 1: Analyze AAPL
    memory.add_turn(
        user_query="Analyze AAPL",
        assistant_response="[analysis]",
        entities={'symbol': 'AAPL'},
        pattern_used='smart_stock_analysis'
    )

    # Turn 2: "Compare it to MSFT"
    resolved = memory.resolve_references("Compare it to MSFT")
    assert "AAPL" in resolved
    assert "it" not in resolved.lower()

    # Turn 3: "Do the same for tech sector"
    # Should carry forward analysis type

    # Test persistence
    memory.save_to_file("test_history.json")
    new_memory = ConversationMemory()
    new_memory.load_from_file("test_history.json")
    assert len(new_memory.recent_symbols) == 1
    assert new_memory.recent_symbols[0] == 'AAPL'
```

**Success Criteria**:
- Reference resolution: 100% on basic cases ("it", "that stock")
- File persistence: Survives save/load cycle
- Recent entities tracking: Correct order (most recent first)
- Max turns enforcement: Trims to 20

---

### Day 5: Enhanced Chat Processor (207 lines)

**Source**: `dawsos/core/enhanced_chat_processor.py`
**Destination**: `trinity3/intelligence/enhanced_chat_processor.py`

**Port This Component**:

```python
class EnhancedChatProcessor:
    def __init__(self, pattern_engine, runtime):
        self.pattern_engine = pattern_engine
        self.runtime = runtime
        self.entity_extractor = EntityExtractor()  # From Day 2-3
        self.memory = ConversationMemory()  # From Day 4

        # Map intents to patterns
        self.intent_to_pattern = {
            "stock_analysis": "smart_stock_analysis",
            "portfolio_review": "smart_portfolio_review",
            "market_briefing": "smart_market_briefing",
            "opportunity_scan": "smart_opportunity_finder",
            "risk_analysis": "smart_risk_analyzer",
            "economic_briefing": "smart_economic_briefing",
            "economic_outlook": "smart_economic_outlook"
        }

    def process_query(self, query: str, use_entity_extraction: bool = True) -> Dict[str, Any]:
        # Step 1: Resolve references
        resolved_query = self.memory.resolve_references(query)

        # Step 2: Extract entities (if enabled)
        extracted = self.entity_extractor.extract_entities(resolved_query) if use_entity_extraction else None

        # Step 3: Route to pattern
        if extracted:
            intent_type = extracted['intent']['intent_type']
            pattern_id = self.intent_to_pattern.get(intent_type)
            if pattern_id:
                # Build context with extracted entities
                # Execute pattern via pattern_engine

        # Step 4: Store in memory
        self.memory.add_turn(user_query=query, assistant_response=result, entities=extracted['entities'], pattern_used=pattern_used)

        # Step 5: Return enriched result
        return {
            **result,
            'pattern': pattern_used,
            'used_entity_extraction': extracted is not None,
            'intent': extracted['intent'] if extracted else None,
            'extracted_entities': extracted['entities'] if extracted else {}
        }
```

**NOTE**: Pattern engine not available yet in Week 1, so add stubs:
```python
def process_query(self, query: str, use_entity_extraction: bool = True) -> Dict[str, Any]:
    # Extract entities
    extracted = self.entity_extractor.extract_entities(query)

    # For Week 1: Return extracted data (pattern execution comes in Week 2)
    return {
        'response': f"Understood: {extracted['intent']['intent_type']} for {extracted['entities'].get('symbol', 'unknown')}",
        'pattern': 'stub',  # Will be real pattern ID in Week 2
        'extracted_entities': extracted['entities'],
        'intent': extracted['intent']
    }
```

**Test**:
```python
def test_enhanced_chat_processor():
    # Week 1: Test without pattern engine (stubs)
    processor = EnhancedChatProcessor(pattern_engine=None, runtime=None)

    # Query 1: "Analyze AAPL"
    result = processor.process_query("Analyze AAPL")
    assert result['intent']['intent_type'] == 'stock_analysis'
    assert result['extracted_entities']['symbol'] == 'AAPL'

    # Query 2: "Compare it to MSFT"
    result = processor.process_query("Compare it to MSFT")
    assert 'AAPL' in result.get('resolved_query', '')  # Reference was resolved

    # Query 3: "What's the recession risk?"
    result = processor.process_query("What's the recession risk?")
    assert result['intent']['intent_type'] == 'economic_briefing'
```

---

## Week 1 Deliverable

**Files Created**:
- `trinity3/intelligence/entity_extractor.py` (406 lines)
- `trinity3/intelligence/conversation_memory.py` (254 lines + persistence)
- `trinity3/intelligence/enhanced_chat_processor.py` (207 lines with stubs)
- `trinity3/tests/test_entity_extractor.py` (20 test cases)
- `trinity3/tests/test_conversation_memory.py` (10 test cases)
- `trinity3/tests/test_enhanced_chat.py` (5 test cases)

**Exit Criteria**:
- [ ] Entity extraction: 90%+ accuracy (18/20 tests pass)
- [ ] Conversation memory: Reference resolution 100% on basic cases
- [ ] Enhanced chat: Routes intents correctly
- [ ] File persistence: Works for conversation history
- [ ] No crashes on edge cases
- [ ] Code reviewed and documented

**Validation Command**:
```bash
cd trinity3
python -m pytest tests/ -v
# Must show: 35 passed
```

**If exit criteria met**: Week 1 complete ✅
**If not**: Continue work, do not proceed to Week 2

---

## Common Issues & Solutions

### Issue 1: Anthropic API Rate Limits
**Solution**: Add retry logic with exponential backoff
```python
import time
from anthropic import RateLimitError

def extract_with_retry(self, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return self.client.messages.create(...)
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
            else:
                raise
```

### Issue 2: Entity Extraction Low Accuracy
**Solution**: Improve prompts with examples
```python
"content": f"""Classify this financial query: "{query}"

Examples:
- "Analyze AAPL" → stock_analysis, symbol=AAPL
- "Quick check on MSFT" → stock_analysis, depth=quick
- "What's the recession risk?" → economic_briefing

Now classify: "{query}"
"""
```

### Issue 3: Reference Resolution Fails
**Solution**: Check recent_symbols is being populated
```python
def add_turn(self, user_query, assistant_response, entities, pattern_used):
    # Debug print
    print(f"Adding turn with entities: {entities}")

    # Ensure symbol extraction works
    if 'symbol' in entities and entities['symbol']:
        symbol = entities['symbol'].upper()
        if symbol not in self.recent_symbols:
            self.recent_symbols.insert(0, symbol)
```

---

## Resources

- **Source Files**: Check [trinity3/MIGRATION_SOURCES.md](trinity3/MIGRATION_SOURCES.md)
- **Testing Guide**: See Week 1 test requirements in [trinity3/MIGRATION_PLAN.md](trinity3/MIGRATION_PLAN.md)
- **Architecture**: Review Trinity flow in [CLAUDE.md](CLAUDE.md)

**Report to**: Migration Lead
**Update**: MIGRATION_STATUS.md daily
**Escalate**: If any exit criteria at risk
