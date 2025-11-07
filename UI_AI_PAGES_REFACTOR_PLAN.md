# UI AI Pages Refactor Plan

**Date:** January 14, 2025  
**Status:** 📋 **PLANNING COMPLETE**  
**Purpose:** Transform AI pages from simple chat interfaces into powerful, pattern-driven intelligence hubs

---

## Executive Summary

**Current State:**
- ❌ AI Insights: Basic chat interface, no pattern integration
- ❌ AI Assistant: Basic chat interface, minimal portfolio context
- ❌ No visualizations or structured insights
- ❌ No proactive recommendations
- ❌ No access to portfolio analysis capabilities

**Target State:**
- ✅ **AI Insights:** Proactive intelligence dashboard with pattern-driven insights
- ✅ **AI Assistant:** Conversational interface with pattern execution and visualizations
- ✅ Real-time portfolio analysis integration
- ✅ Interactive charts and visualizations
- ✅ Context-aware recommendations
- ✅ Pattern-driven multi-step analysis

**Key Innovation:**
Leverage the **Pattern Orchestrator** system to execute complex multi-step analyses on-demand, with AI-powered explanations and visualizations.

---

## Page 1: AI Insights (Proactive Intelligence Dashboard)

### Current Implementation
- Simple chat interface
- Calls `/api/ai/chat` endpoint
- Basic message history
- No pattern integration

### Refactored Vision: "Intelligence Dashboard"

**Core Concept:** Transform from reactive chat to **proactive intelligence hub** that:
1. **Auto-generates insights** using pattern system
2. **Visualizes findings** with interactive charts
3. **Explains metrics** using Claude AI
4. **Surfaces recommendations** based on portfolio state

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  AI Insights Dashboard                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Auto Insights    │  │ Risk Alerts      │           │
│  │ (Pattern-driven) │  │ (Real-time)      │           │
│  └──────────────────┘  └──────────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │ Portfolio Health Score                   │           │
│  │ [Visual Gauge + AI Explanation]         │           │
│  └──────────────────────────────────────────┘           │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Top Opportunities│  │ Risk Factors     │           │
│  │ (AI-ranked)      │  │ (AI-identified)  │           │
│  └──────────────────┘  └──────────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │ Interactive Charts                       │           │
│  │ (Pattern outputs visualized)            │           │
│  └──────────────────────────────────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │ AI-Generated Summary                      │           │
│  │ (Claude summarizes pattern results)      │           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### 1. Auto-Insights Panel (Pattern-Driven)

**Patterns to Execute:**
- `portfolio_overview` - Core metrics
- `portfolio_scenario_analysis` - Risk scenarios
- `portfolio_cycle_risk` - Macro cycle risks
- `buffett_checklist` - Quality assessment

**UI Component:**
```javascript
function AutoInsightsPanel() {
    const [insights, setInsights] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        // Execute multiple patterns in parallel
        const patterns = [
            'portfolio_overview',
            'portfolio_scenario_analysis',
            'portfolio_cycle_risk'
        ];
        
        Promise.all(patterns.map(pattern => 
            apiClient.executePattern(pattern, { portfolio_id: portfolioId })
        )).then(results => {
            // Generate AI insights from pattern results
            generateInsights(results);
        });
    }, [portfolioId]);
    
    const generateInsights = async (patternResults) => {
        // Use Claude to analyze pattern outputs
        const insightPromises = patternResults.map(result => 
            apiClient.aiChat(
                `Analyze this portfolio data and generate 3 key insights: ${JSON.stringify(result.data)}`,
                { portfolioId, source: 'insights' }
            )
        );
        
        const insights = await Promise.all(insightPromises);
        setInsights(insights);
    };
    
    return (
        <div className="insights-panel">
            {insights.map((insight, i) => (
                <InsightCard 
                    key={i}
                    title={insight.title}
                    content={insight.content}
                    pattern={insight.pattern}
                    charts={insight.charts}
                    actions={insight.actions}
                />
            ))}
        </div>
    );
}
```

**Features:**
- **Auto-refresh:** Refresh insights every 5 minutes
- **Pattern badges:** Show which pattern generated each insight
- **Deep dive:** Click to see full pattern results
- **AI explanation:** Claude explains why this insight matters

#### 2. Portfolio Health Score (AI-Powered)

**Pattern:** `portfolio_overview` + `buffett_checklist`

**UI Component:**
```javascript
function PortfolioHealthScore() {
    const [score, setScore] = useState(null);
    const [explanation, setExplanation] = useState(null);
    
    useEffect(() => {
        // Execute portfolio_overview pattern
        apiClient.executePattern('portfolio_overview', { portfolio_id: portfolioId })
            .then(result => {
                // Calculate health score from metrics
                const healthScore = calculateHealthScore(result.data);
                setScore(healthScore);
                
                // Get AI explanation
                apiClient.aiChat(
                    `Explain this portfolio health score: ${healthScore.score}/100. ` +
                    `Metrics: ${JSON.stringify(healthScore.metrics)}`,
                    { portfolioId, source: 'health_score' }
                ).then(response => {
                    setExplanation(response.data);
                });
            });
    }, [portfolioId]);
    
    const calculateHealthScore = (data) => {
        // Combine multiple metrics into health score
        const metrics = {
            performance: data.perf_metrics?.twr_ytd || 0,
            sharpe: data.perf_metrics?.sharpe_ratio || 0,
            diversification: calculateDiversificationScore(data.sector_allocation),
            risk: data.perf_metrics?.volatility || 0
        };
        
        // Weighted scoring
        const score = (
            metrics.performance * 0.3 +
            metrics.sharpe * 0.3 +
            metrics.diversification * 0.2 +
            (1 - metrics.risk) * 0.2
        ) * 100;
        
        return { score, metrics };
    };
    
    return (
        <div className="health-score-panel">
            <CircularProgress value={score} />
            <div className="score-explanation">
                <h3>Portfolio Health: {score}/100</h3>
                <p>{explanation}</p>
            </div>
        </div>
    );
}
```

**Features:**
- **Visual gauge:** Circular progress indicator
- **AI explanation:** Claude explains the score
- **Metric breakdown:** Click to see component scores
- **Trend indicator:** Show if score is improving/declining

#### 3. Top Opportunities Panel (AI-Ranked)

**Pattern:** `portfolio_overview` + `holding_deep_dive` (for top positions)

**UI Component:**
```javascript
function TopOpportunitiesPanel() {
    const [opportunities, setOpportunities] = useState([]);
    
    useEffect(() => {
        // Get portfolio overview
        apiClient.executePattern('portfolio_overview', { portfolio_id: portfolioId })
            .then(result => {
                const topPositions = result.data.valued_positions
                    .slice(0, 5)
                    .sort((a, b) => b.value - a.value);
                
                // For each position, get deep dive
                const deepDives = topPositions.map(pos => 
                    apiClient.executePattern('holding_deep_dive', {
                        portfolio_id: portfolioId,
                        security_id: pos.security_id
                    })
                );
                
                Promise.all(deepDives).then(results => {
                    // Use Claude to rank opportunities
                    rankOpportunities(results);
                });
            });
    }, [portfolioId]);
    
    const rankOpportunities = async (deepDives) => {
        const prompt = `Rank these portfolio positions by investment opportunity. ` +
            `Consider: performance, risk, fundamentals, and portfolio fit. ` +
            `Data: ${JSON.stringify(deepDives)}`;
        
        const response = await apiClient.aiChat(prompt, { portfolioId, source: 'opportunities' });
        
        // Parse ranked opportunities
        const opportunities = parseRankedOpportunities(response.data);
        setOpportunities(opportunities);
    };
    
    return (
        <div className="opportunities-panel">
            {opportunities.map((opp, i) => (
                <OpportunityCard
                    key={i}
                    rank={i + 1}
                    symbol={opp.symbol}
                    opportunity={opp.opportunity}
                    reasoning={opp.reasoning}
                    action={opp.recommended_action}
                />
            ))}
        </div>
    );
}
```

**Features:**
- **AI ranking:** Claude ranks opportunities
- **Actionable recommendations:** Specific actions for each opportunity
- **Visual indicators:** Color-coded by opportunity type
- **Deep dive link:** Click to see full analysis

#### 4. Risk Factors Panel (AI-Identified)

**Pattern:** `portfolio_scenario_analysis` + `portfolio_cycle_risk`

**UI Component:**
```javascript
function RiskFactorsPanel() {
    const [risks, setRisks] = useState([]);
    
    useEffect(() => {
        // Execute risk analysis patterns
        Promise.all([
            apiClient.executePattern('portfolio_scenario_analysis', { portfolio_id: portfolioId }),
            apiClient.executePattern('portfolio_cycle_risk', { portfolio_id: portfolioId })
        ]).then(results => {
            // Use Claude to identify and explain risks
            identifyRisks(results);
        });
    }, [portfolioId]);
    
    const identifyRisks = async (patternResults) => {
        const prompt = `Identify the top 5 risk factors for this portfolio. ` +
            `Consider: scenario analysis, cycle risks, concentration, volatility. ` +
            `Data: ${JSON.stringify(patternResults)}`;
        
        const response = await apiClient.aiChat(prompt, { portfolioId, source: 'risks' });
        const risks = parseRiskFactors(response.data);
        setRisks(risks);
    };
    
    return (
        <div className="risks-panel">
            {risks.map((risk, i) => (
                <RiskCard
                    key={i}
                    title={risk.title}
                    severity={risk.severity}
                    explanation={risk.explanation}
                    mitigation={risk.mitigation}
                />
            ))}
        </div>
    );
}
```

**Features:**
- **Severity indicators:** Color-coded risk levels
- **AI explanations:** Claude explains each risk
- **Mitigation strategies:** AI-suggested actions
- **Scenario links:** Link to scenario analysis

#### 5. Interactive Charts (Pattern Outputs)

**Pattern:** Any pattern with chart outputs

**UI Component:**
```javascript
function InsightCharts() {
    const [charts, setCharts] = useState([]);
    
    useEffect(() => {
        // Execute patterns that generate charts
        apiClient.executePattern('portfolio_overview', { portfolio_id: portfolioId })
            .then(result => {
                // Extract chart configurations from pattern output
                const charts = result.data.charts || [];
                setCharts(charts);
            });
    }, [portfolioId]);
    
    return (
        <div className="charts-panel">
            {charts.map((chart, i) => (
                <ChartCard
                    key={i}
                    type={chart.type}
                    data={chart.data}
                    config={chart.config}
                    aiExplanation={chart.ai_explanation}
                />
            ))}
        </div>
    );
}
```

**Features:**
- **Pattern-driven:** Charts generated from pattern outputs
- **AI tooltips:** Claude explains chart insights
- **Interactive:** Zoom, filter, drill-down
- **Export:** Download charts as images

#### 6. AI-Generated Summary

**Pattern:** All executed patterns

**UI Component:**
```javascript
function AISummary() {
    const [summary, setSummary] = useState(null);
    
    useEffect(() => {
        // Collect all pattern results
        const allResults = collectAllPatternResults();
        
        // Use Claude to generate executive summary
        const prompt = `Generate an executive summary of this portfolio analysis. ` +
            `Include: key metrics, opportunities, risks, and recommendations. ` +
            `Data: ${JSON.stringify(allResults)}`;
        
        apiClient.aiChat(prompt, { portfolioId, source: 'summary' })
            .then(response => {
                setSummary(response.data);
            });
    }, [portfolioId]);
    
    return (
        <div className="summary-panel">
            <h3>Portfolio Intelligence Summary</h3>
            <div className="summary-content">
                {summary && <Markdown content={summary} />}
            </div>
        </div>
    );
}
```

**Features:**
- **Executive summary:** High-level overview
- **Markdown formatting:** Rich text with formatting
- **Auto-refresh:** Updates when portfolio changes
- **Export:** Download as PDF

---

## Page 2: AI Assistant (Conversational Intelligence)

### Current Implementation
- Simple chat interface
- Uses `apiClient.aiChat()`
- Has portfolio context
- No pattern integration

### Refactored Vision: "Conversational Pattern Executor"

**Core Concept:** Transform from simple chat to **intelligent conversational interface** that:
1. **Understands intent** and maps to patterns
2. **Executes patterns** on-demand
3. **Visualizes results** in conversation
4. **Explains findings** using Claude AI
5. **Suggests follow-ups** based on context

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  AI Assistant (Conversational)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │ Chat Messages                             │           │
│  │                                            │           │
│  │ User: "How is my portfolio performing?"   │           │
│  │                                            │           │
│  │ AI: [Executes portfolio_overview pattern]  │           │
│  │     [Shows chart + explanation]           │           │
│  │                                            │           │
│  │ User: "What about risks?"                │           │
│  │                                            │           │
│  │ AI: [Executes portfolio_scenario_analysis] │           │
│  │     [Shows risk breakdown + recommendations]│          │
│  └──────────────────────────────────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │ Suggested Actions                         │           │
│  │ • Analyze specific holding                │           │
│  │ • Run scenario analysis                   │           │
│  │ • Check tax opportunities                 │           │
│  └──────────────────────────────────────────┘           │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │ Input: "Ask about portfolio..."           │           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### 1. Intent Recognition & Pattern Mapping

**New Component:**
```javascript
class IntentRecognizer {
    // Map user queries to patterns
    static mapIntentToPattern(query) {
        const intents = {
            // Performance queries
            'performance': 'portfolio_overview',
            'how is my portfolio': 'portfolio_overview',
            'portfolio metrics': 'portfolio_overview',
            
            // Risk queries
            'risks': 'portfolio_scenario_analysis',
            'what are my risks': 'portfolio_scenario_analysis',
            'scenario analysis': 'portfolio_scenario_analysis',
            
            // Holding queries
            'holding': 'holding_deep_dive',
            'position analysis': 'holding_deep_dive',
            'AAPL': 'holding_deep_dive',
            
            // Tax queries
            'tax': 'tax_harvesting_opportunities',
            'tax loss': 'tax_harvesting_opportunities',
            'wash sale': 'portfolio_tax_report',
            
            // Macro queries
            'macro': 'portfolio_macro_overview',
            'cycle': 'portfolio_cycle_risk',
            'regime': 'macro_cycles_overview',
            
            // Optimization queries
            'rebalance': 'policy_rebalance',
            'optimize': 'policy_rebalance',
            'suggest trades': 'policy_rebalance'
        };
        
        // Simple keyword matching (can be enhanced with NLP)
        const queryLower = query.toLowerCase();
        for (const [intent, pattern] of Object.entries(intents)) {
            if (queryLower.includes(intent)) {
                return { pattern, intent };
            }
        }
        
        // Default: use Claude to determine intent
        return { pattern: null, intent: 'general' };
    }
}
```

#### 2. Pattern Execution in Chat

**Enhanced Chat Component:**
```javascript
function AIAssistantPage() {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [loading, setLoading] = useState(false);
    
    const sendMessage = async () => {
        if (!inputValue.trim() || loading) return;
        
        const userMessage = { 
            role: 'user', 
            content: inputValue,
            timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setLoading(true);
        
        try {
            // Step 1: Recognize intent
            const { pattern, intent } = IntentRecognizer.mapIntentToPattern(inputValue);
            
            if (pattern) {
                // Step 2: Execute pattern
                const patternResult = await apiClient.executePattern(pattern, {
                    portfolio_id: portfolioId,
                    // Extract additional params from query
                    ...extractParamsFromQuery(inputValue)
                });
                
                // Step 3: Generate AI explanation
                const explanation = await apiClient.aiChat(
                    `Explain these portfolio analysis results to the user: ${JSON.stringify(patternResult.data)}. ` +
                    `User asked: "${inputValue}"`,
                    { portfolioId, source: 'assistant' }
                );
                
                // Step 4: Create rich message with charts and data
                const aiMessage = {
                    role: 'assistant',
                    content: explanation.data.response,
                    pattern: pattern,
                    data: patternResult.data,
                    charts: patternResult.data.charts || [],
                    timestamp: new Date().toISOString()
                };
                
                setMessages(prev => [...prev, aiMessage]);
            } else {
                // Fallback: General AI chat
                const response = await apiClient.aiChat(inputValue, {
                    portfolioId,
                    source: 'assistant'
                });
                
                const aiMessage = {
                    role: 'assistant',
                    content: response.data?.response || response.response,
                    timestamp: new Date().toISOString()
                };
                
                setMessages(prev => [...prev, aiMessage]);
            }
        } catch (error) {
            console.error('AI Assistant error:', error);
            // Error handling...
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div className="ai-assistant-page">
            <div className="chat-messages">
                {messages.map((msg, i) => (
                    <MessageComponent
                        key={i}
                        message={msg}
                        // Render charts if pattern was executed
                        showCharts={msg.charts && msg.charts.length > 0}
                        showData={msg.data}
                    />
                ))}
            </div>
            {/* Input area */}
        </div>
    );
}
```

#### 3. Rich Message Rendering

**New Component:**
```javascript
function MessageComponent({ message, showCharts, showData }) {
    return (
        <div className={`chat-message ${message.role}`}>
            <div className="message-content">
                {/* Text content */}
                <div className="message-text">
                    {formatMessage(message.content)}
                </div>
                
                {/* Pattern badge */}
                {message.pattern && (
                    <div className="pattern-badge">
                        <span className="badge-icon">📊</span>
                        <span>Analysis: {message.pattern}</span>
                    </div>
                )}
                
                {/* Charts */}
                {showCharts && message.charts.map((chart, i) => (
                    <ChartCard
                        key={i}
                        type={chart.type}
                        data={chart.data}
                        config={chart.config}
                    />
                ))}
                
                {/* Data table (collapsible) */}
                {showData && (
                    <DataTable
                        data={message.data}
                        collapsible={true}
                    />
                )}
                
                {/* Suggested follow-ups */}
                {message.suggested_followups && (
                    <SuggestedActions
                        actions={message.suggested_followups}
                    />
                )}
            </div>
        </div>
    );
}
```

#### 4. Suggested Actions

**New Component:**
```javascript
function SuggestedActions({ actions }) {
    const handleAction = (action) => {
        // Auto-fill input and send
        setInputValue(action.query);
        sendMessage();
    };
    
    return (
        <div className="suggested-actions">
            <h4>You might also ask:</h4>
            {actions.map((action, i) => (
                <button
                    key={i}
                    className="action-chip"
                    onClick={() => handleAction(action)}
                >
                    {action.label}
                </button>
            ))}
        </div>
    );
}
```

**AI-Generated Suggestions:**
```javascript
// After pattern execution, use Claude to suggest follow-ups
const generateFollowUps = async (patternResult, userQuery) => {
    const prompt = `Based on this portfolio analysis result and the user's question, ` +
        `suggest 3-5 relevant follow-up questions the user might want to ask. ` +
        `Pattern: ${patternResult.pattern}, Query: "${userQuery}", ` +
        `Results: ${JSON.stringify(patternResult.data)}`;
    
    const response = await apiClient.aiChat(prompt, { portfolioId, source: 'followups' });
    return parseFollowUps(response.data);
};
```

#### 5. Context-Aware Responses

**Enhanced AI Chat:**
```javascript
// Build context from conversation history
const buildContext = (messages, portfolioId) => {
    const recentMessages = messages.slice(-5); // Last 5 messages
    const context = {
        portfolio_id: portfolioId,
        conversation_history: recentMessages.map(m => ({
            role: m.role,
            content: m.content.substring(0, 200) // Truncate
        })),
        executed_patterns: messages
            .filter(m => m.pattern)
            .map(m => m.pattern)
    };
    
    return context;
};

// Use context in AI chat
const response = await apiClient.aiChat(inputValue, {
    portfolioId,
    source: 'assistant',
    context: buildContext(messages, portfolioId)
});
```

#### 6. Visual Pattern Results

**Chart Integration:**
```javascript
function PatternResultVisualization({ patternResult }) {
    const charts = patternResult.data.charts || [];
    
    return (
        <div className="pattern-visualization">
            {charts.map((chart, i) => {
                switch (chart.type) {
                    case 'line':
                        return <LineChart key={i} data={chart.data} config={chart.config} />;
                    case 'bar':
                        return <BarChart key={i} data={chart.data} config={chart.config} />;
                    case 'pie':
                        return <PieChart key={i} data={chart.data} config={chart.config} />;
                    default:
                        return null;
                }
            })}
        </div>
    );
}
```

---

## Creative Enhancements

### 1. Proactive Insights (AI Insights Page)

**Feature:** Auto-generate insights when portfolio changes

```javascript
// Monitor portfolio for changes
useEffect(() => {
    const interval = setInterval(() => {
        // Check if portfolio has changed
        checkPortfolioChanges().then(hasChanged => {
            if (hasChanged) {
                // Auto-generate new insights
                generateAutoInsights();
            }
        });
    }, 5 * 60 * 1000); // Every 5 minutes
    
    return () => clearInterval(interval);
}, [portfolioId]);
```

### 2. Pattern Chaining (AI Assistant)

**Feature:** Chain multiple patterns based on conversation

```javascript
// User: "How is my portfolio performing?"
// AI: Executes portfolio_overview
// AI: "Your portfolio is up 8.5%. Would you like to see risk analysis?"
// User: "Yes"
// AI: Executes portfolio_scenario_analysis (chained)
```

### 3. Smart Suggestions (Both Pages)

**Feature:** AI-generated suggestions based on portfolio state

```javascript
// Analyze portfolio and generate contextual suggestions
const generateSmartSuggestions = async (portfolioId) => {
    // Get portfolio overview
    const overview = await apiClient.executePattern('portfolio_overview', { portfolio_id: portfolioId });
    
    // Use Claude to generate suggestions
    const prompt = `Based on this portfolio analysis, suggest 5 actionable insights: ` +
        `${JSON.stringify(overview.data)}`;
    
    const response = await apiClient.aiChat(prompt, { portfolioId, source: 'suggestions' });
    return parseSuggestions(response.data);
};
```

### 4. Pattern Comparison (AI Insights)

**Feature:** Compare portfolio across different time periods

```javascript
// Execute same pattern with different date ranges
const comparePeriods = async (pattern, portfolioId) => {
    const periods = [
        { lookback_days: 30, label: 'Last 30 days' },
        { lookback_days: 90, label: 'Last 90 days' },
        { lookback_days: 252, label: 'Last year' }
    ];
    
    const results = await Promise.all(
        periods.map(period => 
            apiClient.executePattern(pattern, {
                portfolio_id: portfolioId,
                ...period
            })
        )
    );
    
    // Visualize comparison
    return visualizeComparison(results);
};
```

### 5. Pattern Templates (AI Assistant)

**Feature:** Save and reuse pattern configurations

```javascript
// User can save pattern configurations
const savePatternTemplate = (pattern, inputs, name) => {
    const template = {
        id: uuid(),
        name,
        pattern,
        inputs,
        created_at: new Date().toISOString()
    };
    
    localStorage.setItem(`pattern_template_${template.id}`, JSON.stringify(template));
};

// Quick access to saved templates
const quickPatterns = [
    { name: 'Quick Health Check', pattern: 'portfolio_overview' },
    { name: 'Risk Analysis', pattern: 'portfolio_scenario_analysis' },
    { name: 'Tax Opportunities', pattern: 'tax_harvesting_opportunities' }
];
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Refactor AI Insights page structure
- [ ] Implement pattern execution in UI
- [ ] Add basic chart rendering
- [ ] Integrate Claude AI for explanations

### Phase 2: AI Insights Dashboard (Week 2)
- [ ] Auto-Insights Panel
- [ ] Portfolio Health Score
- [ ] Top Opportunities Panel
- [ ] Risk Factors Panel
- [ ] AI-Generated Summary

### Phase 3: AI Assistant Enhancement (Week 3)
- [ ] Intent recognition
- [ ] Pattern execution in chat
- [ ] Rich message rendering
- [ ] Suggested actions
- [ ] Context-aware responses

### Phase 4: Advanced Features (Week 4)
- [ ] Proactive insights
- [ ] Pattern chaining
- [ ] Smart suggestions
- [ ] Pattern comparison
- [ ] Pattern templates

---

## Technical Requirements

### New API Endpoints

```python
# backend/app/api/ai.py

@router.post("/ai/insights/generate")
async def generate_insights(
    portfolio_id: str,
    patterns: List[str] = None
) -> Dict[str, Any]:
    """Generate AI insights from multiple patterns."""
    # Execute patterns
    # Generate AI summaries
    # Return insights

@router.post("/ai/assistant/intent")
async def recognize_intent(
    query: str,
    portfolio_id: str
) -> Dict[str, Any]:
    """Recognize user intent and suggest pattern."""
    # Use Claude to determine intent
    # Map to pattern
    # Return pattern + params

@router.post("/ai/assistant/context")
async def get_conversation_context(
    messages: List[Dict[str, Any]],
    portfolio_id: str
) -> Dict[str, Any]:
    """Build context from conversation history."""
    # Extract context
    # Return context object
```

### New UI Components

```javascript
// frontend/components/InsightCard.jsx
// frontend/components/HealthScore.jsx
// frontend/components/OpportunityCard.jsx
// frontend/components/RiskCard.jsx
// frontend/components/PatternResultVisualization.jsx
// frontend/components/MessageComponent.jsx
// frontend/components/SuggestedActions.jsx
```

### Pattern Enhancements

```json
// Add to pattern JSON files
{
  "charts": [
    {
      "type": "line",
      "data": "{{historical_nav}}",
      "config": {
        "title": "Portfolio NAV Over Time"
      }
    }
  ],
  "ai_explanation": {
    "capability": "claude.explain",
    "subject": "portfolio_performance"
  }
}
```

---

## Success Metrics

1. **User Engagement:**
   - Time spent on AI pages: +200%
   - Pattern executions per session: +150%
   - Return visits: +100%

2. **Feature Adoption:**
   - Auto-insights viewed: 80% of users
   - Pattern execution in chat: 60% of conversations
   - Chart interactions: 40% of sessions

3. **User Satisfaction:**
   - AI explanation helpfulness: 4.5/5
   - Pattern relevance: 4.0/5
   - Overall satisfaction: 4.3/5

---

## Risk Mitigation

1. **Performance:**
   - Cache pattern results
   - Lazy load charts
   - Debounce auto-refresh

2. **API Costs:**
   - Rate limit Claude API calls
   - Cache AI responses
   - Batch pattern executions

3. **User Experience:**
   - Show loading states
   - Graceful error handling
   - Offline fallbacks

---

**Status:** ✅ **PLAN COMPLETE** - Ready for implementation

