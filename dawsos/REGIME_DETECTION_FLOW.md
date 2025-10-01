# What Happens When "Detect Market Regime" is Clicked

## UI Flow Sequence

### 1. Button Click (main.py line 434)
```python
if st.button("Detect Market Regime"):
    response = st.session_state.agent_runtime.orchestrate("What economic regime are we in?")
    st.success("Regime detected! Check the chat tab.")
```

### 2. Orchestration (agent_runtime.py line 73-130)
The `orchestrate()` method coordinates multiple agents:

```python
def orchestrate(self, user_input: str) -> Dict[str, Any]:
    # Step 1: Claude interprets the query
    claude_response = self.execute('claude', {"user_input": user_input})
    # Returns: {intent: 'ANALYZE', entities: ['economic regime']}

    # Step 2: Based on intent, delegate to specialized agents
    if intent == 'ANALYZE':
        # Pattern Spotter analyzes regime
        pattern_result = self.execute('pattern_spotter', {...})

        # Data Harvester fetches indicators
        data_result = self.execute('data_harvester', {...})
```

## Detailed Agent Actions

### Claude Agent (Step 1)
**Input:** "What economic regime are we in?"

**Process:**
1. Parses natural language
2. Identifies intent: ANALYZE
3. Extracts entities: [economic regime]
4. Maps to action: analyze_regime

**Output:**
```json
{
    "intent": "ANALYZE",
    "entities": ["economic regime"],
    "action": "analyze_regime",
    "friendly_response": "Let me analyze the current economic regime..."
}
```

### Data Harvester Agent (Step 2)
**Process:**
1. Fetches current economic indicators:
   - GDP from FRED API
   - CPI (inflation) from FRED API
   - Unemployment Rate from FRED API
   - Federal Funds Rate from FRED API
   - 10-Year Treasury from FRED API

2. Adds/updates nodes in knowledge graph:
```python
graph.add_node('indicator', {'value': 30485.729, 'date': '2025-04-01'}, 'GDP')
graph.add_node('indicator', {'value': 323.364, 'date': '2025-08-01'}, 'CPI')
graph.add_node('indicator', {'value': 4.3, 'date': '2025-08-01'}, 'UNEMPLOYMENT')
graph.add_node('indicator', {'value': 4.09, 'date': '2025-09-29'}, 'FED_RATE')
```

### Pattern Spotter Agent (Step 3)
**Process:**
1. Analyzes indicator values
2. Compares to regime thresholds:
```python
if gdp > 28000 and cpi < 350 and fed_rate > 3:
    regime = "GOLDILOCKS"  # Moderate growth, controlled inflation
elif gdp > 28000 and cpi > 350:
    regime = "OVERHEATING"  # Strong growth, high inflation
elif gdp < 28000 and fed_rate < 2:
    regime = "RECESSION_RISK"  # Slow growth, accommodative policy
else:
    regime = "TRANSITIONAL"  # Mixed signals
```

3. Updates ECONOMIC_REGIME node:
```python
graph.nodes['ECONOMIC_REGIME'] = {
    'current_state': 'GOLDILOCKS',
    'description': 'Moderate growth, controlled inflation, normalized rates',
    'confidence': 0.8,
    'indicators': {
        'gdp': 30485.729,
        'cpi': 323.364,
        'unemployment': 4.3,
        'fed_rate': 4.09
    }
}
```

### Relationship Hunter Agent (Step 4)
**Process:**
1. Establishes regime relationships:
```python
graph.connect('ECONOMIC_REGIME', 'TECHNOLOGY', 'favors', 0.8)
graph.connect('ECONOMIC_REGIME', 'FINANCIALS', 'favors', 0.75)
graph.connect('ECONOMIC_REGIME', 'HEALTHCARE', 'neutral', 0.5)
```

### Forecast Dreamer Agent (Step 5)
**Process:**
1. Makes sector predictions based on regime:
```python
if regime == 'GOLDILOCKS':
    predictions = {
        'TECHNOLOGY': 'bullish',
        'FINANCIALS': 'bullish',
        'CONSUMER_DISC': 'bullish',
        'UTILITIES': 'neutral'
    }
```

## Final Response Structure

The orchestrated response combines all agent outputs:

```json
{
    "interpretation": {
        "intent": "ANALYZE",
        "entities": ["economic regime"]
    },
    "results": [
        {
            "agent": "data_harvester",
            "data": {
                "GDP": 30485.729,
                "CPI": 323.364,
                "UNEMPLOYMENT": 4.3,
                "FED_RATE": 4.09
            }
        },
        {
            "agent": "pattern_spotter",
            "regime": "GOLDILOCKS",
            "confidence": 0.8,
            "description": "Moderate growth, controlled inflation"
        },
        {
            "agent": "forecast_dreamer",
            "sectors": {
                "favored": ["TECHNOLOGY", "FINANCIALS"],
                "neutral": ["HEALTHCARE", "CONSUMER_STAPLES"],
                "avoid": ["UTILITIES", "REAL_ESTATE"]
            }
        }
    ],
    "friendly_response": "We're currently in a GOLDILOCKS regime - moderate growth with controlled inflation. This favors growth sectors like Technology and Financials."
}
```

## UI Display

After processing, the response is:
1. Added to chat history
2. Success message shown: "Regime detected! Check the chat tab."
3. Graph automatically saved with new data
4. User can switch to Chat tab to see detailed analysis

## Side Effects

1. **Knowledge Graph Updated:**
   - Economic indicator nodes updated with latest values
   - ECONOMIC_REGIME node updated with current state
   - Sector relationships adjusted for regime

2. **Persistence:**
   - Graph saved to `storage/graph.json`
   - Workflow recorded if significant

3. **Cache:**
   - API responses cached (FRED data for 1 hour)
   - Regime analysis cached until indicators change

## Visual Feedback

In the Chat tab, user sees:
```
🤖 DawsOS: Analyzing current economic regime...

📊 Current Indicators:
• GDP: $30,485.7B (healthy growth)
• CPI: 323.4 (moderate inflation ~3.5%)
• Unemployment: 4.3% (near full employment)
• Fed Rate: 4.09% (normalized)

🎯 Regime: GOLDILOCKS
Moderate growth with controlled inflation creates favorable conditions for risk assets.

📈 Sector Recommendations:
• Overweight: Technology, Financials
• Neutral: Healthcare, Consumer Staples
• Underweight: Utilities, Real Estate

This regime historically favors growth stocks and cyclical sectors.
```

## Error Handling

If any step fails:
1. API timeout → Use cached data if available
2. Missing data → Proceed with partial analysis
3. Agent failure → Fallback to simpler analysis
4. Complete failure → Return error message to user