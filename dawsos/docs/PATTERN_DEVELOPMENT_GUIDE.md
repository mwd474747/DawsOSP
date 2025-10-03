# DawsOS Pattern Development Guide

**Version:** 1.0
**Last Updated:** 2025-10-03
**Author:** DawsOS Development Team

## Table of Contents

1. [Pattern Basics](#pattern-basics)
2. [Pattern Structure](#pattern-structure)
3. [Trigger Matching](#trigger-matching)
4. [Step Actions](#step-actions)
5. [Variable Substitution](#variable-substitution)
6. [Response Templates](#response-templates)
7. [Testing Patterns](#testing-patterns)
8. [Common Pattern Types](#common-pattern-types)
9. [Trinity Compliance](#trinity-compliance)
10. [Error Handling](#error-handling)
11. [Complete Examples](#complete-examples)
12. [Pattern Template](#pattern-template)

---

## Pattern Basics

### What Are Patterns?

Patterns are JSON-defined workflows that enable DawsOS to execute complex multi-step operations without hard-coded logic. They act as the "playbooks" for how agents collaborate to accomplish specific tasks.

### When to Use Patterns

Use patterns when you need to:

- **Orchestrate multiple agents** in a specific sequence
- **Standardize responses** to common user requests
- **Combine data from multiple sources** into a coherent analysis
- **Create reusable workflows** that can be triggered by user input
- **Ensure consistency** in how the system handles specific types of queries

### When NOT to Use Patterns

Don't create patterns for:

- Simple single-agent tasks (use direct agent calls instead)
- One-off operations that won't be reused
- Highly dynamic workflows where steps can't be predetermined
- Operations better suited for UI components or API endpoints

---

## Pattern Structure

### Required Fields

Every pattern must include these fields:

```json
{
  "id": "unique_pattern_identifier",
  "name": "Human-Readable Pattern Name",
  "description": "What this pattern does and when to use it",
  "triggers": ["keyword1", "keyword2", "phrase"],
  "steps": [],
  "version": "1.0",
  "last_updated": "2025-10-03"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String | Yes | Unique identifier for the pattern (lowercase, underscores) |
| `name` | String | Yes | Display name for the pattern |
| `description` | String | Yes | Explains what the pattern does |
| `triggers` | Array | Yes | Keywords/phrases that activate this pattern |
| `entities` | Array | No | Entity types to extract (e.g., `["SYMBOL"]`) |
| `steps` | Array | Yes | Workflow steps to execute in sequence |
| `response_template` | String | No | Template for formatting the final response |
| `response_type` | String | No | Type of response (e.g., `stock_quote`, `analysis`) |
| `error_handling` | String | No | How to handle errors: `"stop"` or `"continue"` (default: `"stop"`) |
| `priority` | Number | No | Pattern matching priority (higher = checked first) |
| `cache_ttl` | Number | No | Cache time-to-live in seconds |
| `version` | String | Yes | Semantic version number |
| `last_updated` | String | Yes | Date of last modification (YYYY-MM-DD) |

---

## Trigger Matching

### How Triggers Work

The Pattern Engine searches user input for trigger keywords and phrases. Patterns with more matching triggers score higher and are selected for execution.

### Best Practices for Triggers

1. **Use diverse variations**: Include synonyms and common phrasings
   ```json
   "triggers": [
     "stock price",
     "price",
     "quote",
     "trading",
     "cost",
     "worth"
   ]
   ```

2. **Include domain-specific terms**: Add technical vocabulary users might employ
   ```json
   "triggers": [
     "moat",
     "economic moat",
     "competitive advantage",
     "moat analysis"
   ]
   ```

3. **Lowercase only**: All triggers are matched case-insensitively
4. **Avoid overly generic triggers**: Don't use single common words like "the", "what", "how"
5. **Test for conflicts**: Ensure your triggers don't overlap too much with other patterns

### Entity Extraction

Define entities to extract specific data from user input:

```json
{
  "entities": ["SYMBOL"],
  "triggers": ["stock price", "quote"]
}
```

Common entity types:
- `SYMBOL`: Stock ticker symbols (e.g., AAPL, TSLA)
- `DATE`: Dates and time periods
- `NUMBER`: Numeric values
- `COMPANY`: Company names

---

## Step Actions

Each step in a pattern's workflow specifies an action to perform. Here are all available actions:

### 1. execute_through_registry

Execute an agent through the AgentRuntime registry (Trinity-compliant).

```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "data_harvester",
    "context": {
      "request": "Get quote for {SYMBOL}"
    }
  },
  "save_as": "quote_data"
}
```

**Available Agents:**
- `graph_mind` - Knowledge graph operations
- `claude` - General AI reasoning and formatting
- `data_harvester` - Fetch market and financial data
- `data_digester` - Process and summarize data
- `relationship_hunter` - Find connections between entities
- `pattern_spotter` - Identify trends and patterns
- `forecast_dreamer` - Generate forecasts
- `financial_analyst` - Financial analysis and metrics
- `equity_agent` - Stock-specific analysis
- `macro_agent` - Macroeconomic analysis
- `risk_agent` - Risk assessment
- `governance_agent` - Governance and compliance checks

### 2. knowledge_lookup

Retrieve data from the knowledge graph.

```json
{
  "action": "knowledge_lookup",
  "params": {
    "knowledge_file": "buffett_framework.json",
    "section": "economic_moat"
  },
  "save_as": "moat_knowledge"
}
```

### 3. enriched_lookup

Query enriched data from Phase 3 JSON files.

```json
{
  "action": "enriched_lookup",
  "params": {
    "data_type": "sector_performance",
    "query": "cycle_performance",
    "phase": "{cycle_phase.phase}"
  },
  "save_as": "historical_performance"
}
```

**Common Data Types:**
- `sector_performance` - Sector rotation and performance data
- `company_database` - Company information and aliases
- `economic_cycles` - Historical economic cycle data
- `sp500_companies` - S&P 500 company classifications

### 4. evaluate

Perform qualitative evaluations based on predefined criteria.

```json
{
  "action": "evaluate",
  "params": {
    "type": "brand_moat",
    "checks": [
      "premium_pricing_ability",
      "customer_loyalty",
      "mind_share_leadership"
    ]
  },
  "save_as": "brand_score"
}
```

**Evaluation Types:**
- `brand_moat` - Brand strength assessment
- `network_effects` - Network effects evaluation
- `cost_advantages` - Cost structure analysis
- `switching_costs` - Customer switching barriers
- `debt_cycle_position` - Economic cycle positioning

### 5. calculate

Perform financial calculations.

```json
{
  "action": "calculate",
  "params": {
    "formula": "ROIC - WACC spread",
    "target": ">15% for wide moat"
  },
  "save_as": "roic_spread"
}
```

**Common Calculations:**
- `ROIC - WACC spread` - Return on invested capital vs. cost of capital
- `FCF / Market Cap` - Free cash flow yield
- `NOPAT / Invested Capital` - Return on invested capital
- `Net Income + D&A - Maintenance CapEx` - Owner earnings

**Calculation Methods:**
- `short_term_debt_cycle_score` - Short-term economic cycle position
- `long_term_debt_cycle_score` - Long-term debt cycle position
- `dcf_simplified` - Simplified discounted cash flow valuation

### 6. synthesize

Combine multiple data points into a coherent conclusion.

```json
{
  "action": "synthesize",
  "params": {
    "scores": [
      "{brand_score}",
      "{network_score}",
      "{cost_score}",
      "{switching_score}"
    ]
  },
  "save_as": "moat_rating"
}
```

---

## Variable Substitution

### Basic Syntax

Use curly braces `{variable}` to reference variables in your pattern steps.

### Variable Sources

1. **Context Variables**: Data passed when the pattern is executed
   ```json
   "request": "Analyze {user_input}"
   ```

2. **Entity Extraction**: Entities extracted from user input
   ```json
   "request": "Get quote for {SYMBOL}"
   ```

3. **Previous Step Outputs**: Results from earlier steps (using `save_as`)
   ```json
   "context": {
     "data": "{quote_data}"
   }
   ```

4. **Nested Data Access**: Access nested fields in step outputs
   ```json
   "template": "{SYMBOL} is trading at ${quote_data.price} ({quote_data.change_percent}%)"
   ```

### The save_as Parameter

Use `save_as` to store step results for later use:

```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "data_harvester",
    "context": {
      "request": "Get quote for {SYMBOL}"
    }
  },
  "save_as": "quote_data"  // Store result as "quote_data"
}
```

Later steps can reference this data:

```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "claude",
    "context": {
      "user_input": "Format this nicely: {quote_data}"  // Use stored data
    }
  },
  "save_as": "formatted_response"
}
```

### Alternative Output Formats

The pattern engine also supports:

- `outputs` (array): Store result under multiple variable names
- `output` (string): Alias for `save_as`

```json
{
  "action": "evaluate",
  "outputs": ["brand_score", "brand_analysis"],
  "params": {
    "type": "brand_moat",
    "checks": ["premium_pricing_ability"]
  }
}
```

---

## Response Templates

### Template Basics

Response templates format the final output using data from all pattern steps.

```json
{
  "response_template": "{SYMBOL} is trading at ${quote_data.price}"
}
```

### Template Features

1. **Variable Substitution**: Use `{variable}` syntax
2. **Nested Field Access**: Access nested data with dot notation
3. **Agent Response Extraction**: Automatically extracts `response`, `friendly_response`, or `result` fields
4. **Markdown Formatting**: Full Markdown support for rich output

### Complex Template Example

```json
{
  "response_template": "## Sector Rotation Strategy\n\n### Economic Cycle Position\nWe are currently in the **{cycle_phase.phase}** phase.\n\n### Recommended Sectors\n- **Outperformers**: {sector_recommendations.data.outperformers}\n- **Underperformers**: {sector_recommendations.data.underperformers}\n\n### Current Momentum\n{momentum_analysis.response}"
}
```

### Alternative Response Format

You can also use the `response` object format:

```json
{
  "response": {
    "template": "Your template here",
    "format": "markdown"
  }
}
```

### Response Types

Set `response_type` to indicate how the UI should display the result:

- `stock_quote` → Price card display
- `regime_analysis` → Regime analysis card
- `forecast` → Forecast chart
- `generic` → Default text display

---

## Testing Patterns

### Validation with lint_patterns.py

Always validate your patterns before deployment:

```bash
python scripts/lint_patterns.py
```

The linter checks for:

- **Schema Compliance**: All required fields present
- **Valid Agent References**: Agents exist in the runtime
- **Duplicate IDs**: No conflicting pattern identifiers
- **Versioning Metadata**: Version and last_updated fields present
- **Step Structure**: Proper step formatting
- **Deprecated Fields**: Legacy syntax detection

### Common Linting Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Missing required field 'id' | No ID specified | Add unique `"id"` field |
| Duplicate pattern ID | Two patterns with same ID | Use unique identifiers |
| Step X missing 'agent' or 'action' | Invalid step format | Add `"action"` or `"agent"` field |
| References unknown agent 'xyz' | Agent doesn't exist | Use valid agent name |
| Invalid JSON | Syntax error | Validate JSON syntax |

### Manual Testing

Test patterns by triggering them through the UI or directly:

```python
from dawsos.core.pattern_engine import PatternEngine
from dawsos.core.agent_runtime import AgentRuntime

runtime = AgentRuntime()
engine = PatternEngine(runtime=runtime)

# Find pattern
pattern = engine.find_pattern("What is the stock price of AAPL?")

# Execute pattern
result = engine.execute_pattern(pattern, {
    "user_input": "What is the stock price of AAPL?",
    "SYMBOL": "AAPL"
})

print(result['formatted_response'])
```

### Testing Checklist

- [ ] Pattern passes `lint_patterns.py` validation
- [ ] All triggers properly match expected user inputs
- [ ] Entity extraction works correctly
- [ ] Each step executes without errors
- [ ] Variable substitution resolves all references
- [ ] Response template formats correctly
- [ ] Error handling behaves as expected
- [ ] Pattern doesn't conflict with existing patterns

---

## Common Pattern Types

### 1. Query Patterns

Simple data retrieval and formatting.

**Characteristics:**
- Few steps (typically 2-3)
- Focus on data fetching and formatting
- Fast execution
- High cache potential

**Use Cases:**
- Stock quotes
- Company information lookups
- Quick market data queries

**Example:** See `dawsos/patterns/queries/stock_price.json`

### 2. Analysis Patterns

Complex multi-step analytical workflows.

**Characteristics:**
- Multiple evaluation steps
- Combines qualitative and quantitative analysis
- Synthesizes results from multiple sources
- Rich, detailed output

**Use Cases:**
- Economic moat analysis
- Financial health assessment
- Competitive positioning

**Example:** See `dawsos/patterns/analysis/moat_analyzer.json`

### 3. Multi-Step Workflows

Complex orchestrations involving multiple agents.

**Characteristics:**
- 5+ steps
- Sequential dependencies between steps
- Data flows from step to step
- Comprehensive final output

**Use Cases:**
- Sector rotation analysis
- Full investment research workflow
- Complex scenario modeling

**Example:** See `dawsos/patterns/sector_rotation.json`

---

## Trinity Compliance

### What Makes a Pattern Trinity-Compliant?

Trinity is DawsOS's architectural framework ensuring all components work through standardized interfaces. A Trinity-compliant pattern:

1. **Uses execute_through_registry**: All agent calls go through the AgentRuntime registry
2. **Avoids direct agent instantiation**: No `new Agent()` or direct agent references
3. **Returns standardized responses**: Consistent response format with metadata
4. **Tracks execution**: All calls are logged and monitored

### Migrating from Legacy Syntax

**Legacy (Non-Compliant):**
```json
{
  "agent": "financial_analyst",
  "method": "analyze_stock",
  "params": {
    "symbol": "{SYMBOL}"
  }
}
```

**Trinity (Compliant):**
```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "financial_analyst",
    "context": {
      "request": "Analyze {SYMBOL}"
    }
  },
  "save_as": "analysis"
}
```

### Compliance Checklist

- [ ] All agent calls use `execute_through_registry` action
- [ ] No direct agent method calls
- [ ] All steps have proper `save_as` or `outputs` fields
- [ ] Response template uses only stored outputs
- [ ] No references to deprecated orchestrators
- [ ] Pattern validated by linter

---

## Error Handling

### Error Handling Strategies

Set the `error_handling` field to control how the pattern responds to errors:

```json
{
  "error_handling": "stop"  // or "continue"
}
```

### Stop vs. Continue

**Stop (Default):**
- Pattern execution halts at first error
- Returns error information
- Use for critical workflows where partial results are not useful

**Continue:**
- Pattern proceeds to next step even if a step fails
- Failed steps return error data that can be handled
- Use for exploratory workflows where partial results have value

### Fallback Strategies

Implement fallback logic using multiple steps:

```json
{
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {
          "request": "Get real-time quote for {SYMBOL}"
        }
      },
      "save_as": "quote_data"
    },
    {
      "action": "evaluate",
      "params": {
        "type": "check_data_quality",
        "data": "{quote_data}"
      },
      "save_as": "quality_check"
    },
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "claude",
        "context": {
          "user_input": "If data quality is poor in {quality_check}, use fallback data source"
        }
      },
      "save_as": "final_data"
    }
  ]
}
```

### Error Response Fields

When a step fails, the error is captured in the results:

```json
{
  "step": 2,
  "action": "data_harvester",
  "error": "API timeout after 30 seconds"
}
```

Your response template can check for errors:

```json
{
  "response_template": "{% if error %}Data unavailable: {error}{% else %}{data}{% endif %}"
}
```

---

## Complete Examples

### Example 1: Simple Query Pattern

**File:** `patterns/queries/stock_price.json`

```json
{
  "id": "stock_price",
  "name": "Get Stock Price",
  "description": "Fetches current stock price and displays key metrics",

  // Triggers: Keywords that activate this pattern
  "triggers": [
    "stock price",
    "price",
    "quote",
    "trading",
    "cost",
    "worth"
  ],

  // Entities: Data to extract from user input
  "entities": ["SYMBOL"],

  // Priority: Higher priority patterns are checked first
  "priority": 10,

  // Steps: Sequential workflow
  "steps": [
    {
      // Step 1: Fetch quote data
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {
          "request": "Get quote for {SYMBOL}"  // {SYMBOL} extracted from user input
        }
      },
      "save_as": "quote_data"  // Store result for later use
    },
    {
      // Step 2: Format response nicely
      "action": "execute_through_registry",
      "params": {
        "agent": "claude",
        "context": {
          "user_input": "Format this nicely: {quote_data}"  // Use saved quote_data
        }
      },
      "save_as": "formatted_response"
    }
  ],

  // Response: How to display the final result
  "response_type": "stock_quote",
  "response_template": "{SYMBOL} is trading at ${quote_data.price} ({quote_data.change_percent}%)",

  // Error handling: Stop on first error
  "error_handling": "stop",

  // Cache: Cache results for 60 seconds
  "cache_ttl": 60,

  // Metadata: Version tracking
  "version": "1.0",
  "last_updated": "2025-10-02"
}
```

### Example 2: Complex Analysis Pattern

**File:** `patterns/analysis/moat_analyzer.json`

```json
{
  "id": "moat_analyzer",
  "name": "Economic Moat Analyzer",
  "description": "Deep analysis of a company's economic moat using multiple evaluation criteria",

  // Multiple trigger variations
  "triggers": [
    "moat",
    "economic moat",
    "competitive advantage",
    "moat analysis"
  ],

  "priority": 95,

  "steps": [
    {
      // Step 1: Load Buffett framework knowledge
      "action": "knowledge_lookup",
      "params": {
        "knowledge_file": "buffett_framework.json",
        "section": "economic_moat"
      },
      "save_as": "moat_framework"
    },
    {
      // Step 2: Evaluate brand moat (score out of 10)
      "action": "evaluate",
      "params": {
        "type": "brand_moat",
        "checks": [
          "premium_pricing_ability",
          "customer_loyalty",
          "mind_share_leadership"
        ]
      },
      "save_as": "brand_score"
    },
    {
      // Step 3: Evaluate network effects
      "action": "evaluate",
      "params": {
        "type": "network_effects",
        "checks": [
          "value_increases_with_users",
          "high_switching_costs",
          "winner_take_all_dynamics"
        ]
      },
      "save_as": "network_score"
    },
    {
      // Step 4: Evaluate cost advantages
      "action": "evaluate",
      "params": {
        "type": "cost_advantages",
        "checks": [
          "lowest_cost_producer",
          "economies_of_scale",
          "unique_assets"
        ]
      },
      "save_as": "cost_score"
    },
    {
      // Step 5: Evaluate switching costs
      "action": "evaluate",
      "params": {
        "type": "switching_costs",
        "checks": [
          "painful_to_switch",
          "embedded_in_operations",
          "long_term_contracts"
        ]
      },
      "save_as": "switching_score"
    },
    {
      // Step 6: Calculate ROIC spread
      "action": "calculate",
      "params": {
        "formula": "ROIC - WACC spread",
        "target": ">15% for wide moat"
      },
      "save_as": "roic_spread"
    },
    {
      // Step 7: Synthesize all scores into final rating
      "action": "synthesize",
      "params": {
        "scores": [
          "{brand_score}",
          "{network_score}",
          "{cost_score}",
          "{switching_score}",
          "{roic_spread}"
        ]
      },
      "save_as": "moat_rating"
    }
  ],

  // Rich Markdown response template using all step outputs
  "response": {
    "template": "## Economic Moat Analysis for {symbol}\n\n### Moat Sources Evaluation\n\n**Brand Moat**: {brand_score.score}/10\n{brand_details}\n\n**Network Effects**: {network_score.score}/10\n{network_details}\n\n**Cost Advantages**: {cost_score.score}/10\n{cost_details}\n\n**Switching Costs**: {switching_score.score}/10\n{switching_details}\n\n### Financial Evidence\n- ROIC-WACC Spread: {roic_spread.value}%\n- Gross Margin Stability: {margin_stability}\n- 10-Year Avg ROIC: {avg_roic}%\n\n### Overall Moat Rating\n**Rating**: {moat_rating.moat_rating}\n- Width: {moat_rating.moat_width}\n- Durability: {moat_rating.moat_durability}\n- Trend: {moat_rating.moat_trend}\n\n### Investment Implications\n{moat_rating.investment_action}",
    "format": "markdown"
  },

  "version": "1.0",
  "last_updated": "2025-10-02"
}
```

### Example 3: Multi-Agent Workflow

**File:** `patterns/sector_rotation.json`

```json
{
  "id": "sector_rotation",
  "name": "Sector Rotation Analysis",
  "description": "Identify which sectors to rotate into based on economic cycle",

  "triggers": [
    "sector rotation",
    "which sectors",
    "sector analysis",
    "sector allocation"
  ],

  "steps": [
    {
      // Step 1: Get economic indicators
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {
          "request": "Get economic indicators GDP, CPI, unemployment, yield curve"
        }
      },
      "save_as": "economic_data"
    },
    {
      // Step 2: Determine current cycle phase
      "action": "evaluate",
      "params": {
        "type": "debt_cycle_position",
        "data": "{economic_data}"
      },
      "save_as": "cycle_phase"
    },
    {
      // Step 3: Look up historical sector performance in this phase
      "action": "enriched_lookup",
      "params": {
        "data_type": "sector_performance",
        "query": "cycle_performance",
        "phase": "{cycle_phase.phase}"
      },
      "save_as": "historical_performance"
    },
    {
      // Step 4: Get rotation strategy recommendations
      "action": "enriched_lookup",
      "params": {
        "data_type": "sector_performance",
        "query": "rotation_strategies",
        "phase": "{cycle_phase.phase}"
      },
      "save_as": "sector_recommendations"
    },
    {
      // Step 5: Get current sector ETF data
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {
          "request": "Get sector ETFs XLF XLK XLE XLV XLI XLY XLP XLB XLU"
        }
      },
      "save_as": "sector_data"
    },
    {
      // Step 6: Analyze current momentum
      "action": "execute_through_registry",
      "params": {
        "agent": "pattern_spotter",
        "context": {
          "analysis_type": "momentum",
          "data": "{sector_data}"
        }
      },
      "save_as": "momentum_analysis"
    },
    {
      // Step 7: Synthesize final strategy
      "action": "synthesize",
      "params": {
        "cycle_phase": "{cycle_phase}",
        "recommended_sectors": "{sector_recommendations}",
        "current_momentum": "{momentum_analysis}"
      },
      "save_as": "rotation_strategy"
    }
  ],

  "response_template": "## Sector Rotation Strategy\n\n### Economic Cycle Position\nWe are currently in the **{cycle_phase.phase}** phase of the economic cycle.\n\n### Historical Performance in {cycle_phase.phase} Phase\n{historical_performance.data}\n\n### Recommended Sectors\nBased on historical performance in this phase:\n- **Outperformers**: {sector_recommendations.data.outperformers}\n- **Underperformers**: {sector_recommendations.data.underperformers}\n\n### Current Momentum\n{momentum_analysis.response}\n\n### Rotation Strategy\n{rotation_strategy.recommendation}",

  "version": "1.0",
  "last_updated": "2025-10-02"
}
```

---

## Pattern Template

Use this template to create new patterns:

```json
{
  "id": "pattern_id",
  "name": "Pattern Name",
  "description": "What this pattern does",

  "triggers": [
    "keyword1",
    "keyword2",
    "phrase"
  ],

  "entities": [
    "ENTITY_TYPE"
  ],

  "priority": 50,

  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "agent_name",
        "context": {
          "request": "What to do"
        }
      },
      "save_as": "step_1_output"
    },
    {
      "action": "action_type",
      "params": {
        "param1": "value1",
        "param2": "{step_1_output}"
      },
      "save_as": "step_2_output"
    }
  ],

  "response_template": "Final output: {step_2_output}",
  "response_type": "generic",

  "error_handling": "stop",
  "cache_ttl": 300,

  "version": "1.0",
  "last_updated": "2025-10-03"
}
```

---

## Best Practices Summary

1. **Always validate** patterns with `lint_patterns.py` before deployment
2. **Use descriptive IDs** that clearly indicate the pattern's purpose
3. **Include diverse triggers** to maximize pattern matching
4. **Store step outputs** with `save_as` for reuse in later steps
5. **Use Trinity-compliant** `execute_through_registry` actions
6. **Version your patterns** and update `last_updated` on changes
7. **Test thoroughly** with various user inputs
8. **Document complex patterns** with inline comments (in your notes, not in JSON)
9. **Keep patterns focused** - one primary purpose per pattern
10. **Monitor pattern execution** through logs to identify issues

---

## Additional Resources

- **Pattern Examples**: `dawsos/patterns/` directory
- **Pattern Linter**: `scripts/lint_patterns.py`
- **Pattern Engine Source**: `dawsos/core/pattern_engine.py`
- **Agent Runtime**: `dawsos/core/agent_runtime.py`
- **Trinity Architecture Docs**: `dawsos/docs/TRINITY_ARCHITECTURE.md`

---

**Questions or Issues?**

For pattern development support, consult the DawsOS development team or open an issue in the project repository.
