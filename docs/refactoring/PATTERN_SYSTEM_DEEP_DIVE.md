# Pattern System Deep Dive

**Date:** January 15, 2025  
**Purpose:** Comprehensive understanding of the pattern system's architecture and power

---

## Pattern System Philosophy

The pattern system is the **primary abstraction** for business logic in DawsOS. It provides:

1. **Declarative Workflows:** Business logic defined in JSON, not code
2. **Composability:** Patterns can reference other patterns' outputs
3. **Reproducibility:** All operations traceable via RequestCtx
4. **Flexibility:** Dynamic template substitution enables powerful workflows
5. **Testability:** Patterns can be tested independently

---

## Core Components

### 1. Pattern Definition (JSON)

**Location:** `backend/patterns/*.json`

**Structure:**
```json
{
  "id": "pattern_name",
  "name": "Human Readable Name",
  "description": "What this pattern does",
  "version": "1.0.0",
  "category": "portfolio|macro|analysis|workflow",
  "tags": ["tag1", "tag2"],
  "author": "DawsOS",
  "created": "2025-01-15",
  
  "inputs": {
    "portfolio_id": {
      "type": "uuid",
      "required": true,
      "description": "Portfolio UUID"
    },
    "lookback_days": {
      "type": "integer",
      "default": 252,
      "description": "Historical period in days"
    }
  },
  
  "steps": [
    {
      "capability": "portfolio.get_valued_positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "pack_id": "{{ctx.pricing_pack_id}}"
      },
      "as": "valued_positions",
      "description": "Get positions with prices",
      "condition": "{{inputs.portfolio_id}} != null"
    }
  ],
  
  "outputs": {
    "panels": [
      {"id": "panel1", "dataPath": "valued_positions"},
      {"id": "panel2", "dataPath": "perf_metrics"}
    ],
    "data": {
      "valued_positions": "{{valued_positions}}",
      "perf_metrics": "{{perf_metrics}}"
    }
  },
  
  "presentation": {
    "panel1": {
      "type": "table",
      "columns": [...]
    }
  },
  
  "rights_required": ["portfolio_read"],
  "export_allowed": {
    "pdf": true,
    "csv": true
  }
}
```

---

### 2. Pattern Orchestrator

**Location:** `backend/app/core/pattern_orchestrator.py`

**Responsibilities:**
1. Load patterns from `backend/patterns/` directory
2. Validate pattern structure and inputs
3. Execute steps sequentially
4. Resolve template variables
5. Route capabilities to AgentRuntime
6. Build execution trace
7. Extract outputs from state

**Key Methods:**
- `load_patterns()` - Load all patterns from directory
- `validate_pattern()` - Validate pattern structure and inputs
- `run_pattern()` - Execute pattern with context and inputs
- `_resolve_args()` - Resolve template variables
- `_resolve_value()` - Resolve single template value
- `_eval_condition()` - Evaluate conditional step execution

---

### 3. Template Substitution

**Template Variables:**
- `{{inputs.x}}` - User-provided inputs
- `{{ctx.y}}` - Request context (pricing_pack_id, ledger_commit_hash, etc.)
- `{{step_result}}` - Previous step's result (via "as" key)
- `{{step_result.nested}}` - Nested property access

**Example:**
```json
{
  "capability": "metrics.compute_twr",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    "positions": "{{valued_positions.positions}}",
    "pack_id": "{{ctx.pricing_pack_id}}"
  },
  "as": "perf_metrics"
}
```

**Resolution:**
1. Extract template path: `{{valued_positions.positions}}` → `["valued_positions", "positions"]`
2. Look up in state: `state["valued_positions"]["positions"]`
3. Return resolved value

---

### 4. Agent Runtime

**Location:** `backend/app/core/agent_runtime.py`

**Responsibilities:**
1. Register agents and their capabilities
2. Route capability calls to appropriate agent
3. Handle retries and error recovery
4. Enforce rights and permissions
5. Build execution trace

**Capability Routing:**
```
"ledger.positions" → FinancialAnalyst.ledger_positions()
"macro.detect_regime" → MacroHound.macro_detect_regime()
"data.fetch_news" → DataHarvester.data_fetch_news()
```

---

### 5. Request Context (RequestCtx)

**Location:** `backend/app/core/types.py`

**Purpose:** Ensure reproducibility of all operations

**Fields:**
- `user_id` - User UUID
- `portfolio_id` - Portfolio UUID (optional)
- `pricing_pack_id` - Pricing pack ID (SACRED - required for reproducibility)
- `ledger_commit_hash` - Ledger commit hash (SACRED - required for reproducibility)
- `asof_date` - As-of date for calculations
- `trace_id` - Trace ID for debugging
- `request_id` - Request ID for caching

**Immutability:** RequestCtx is immutable - cannot be modified after creation

---

## Pattern Execution Flow

### Step-by-Step Execution

```
1. User Request
   POST /api/patterns/execute
   {
     "pattern": "portfolio_overview",
     "inputs": {"portfolio_id": "abc-123"}
   }
   
2. PatternOrchestrator.run_pattern()
   - Load pattern JSON
   - Validate inputs
   - Initialize state: {ctx: {...}, inputs: {...}}
   
3. Execute Step 1
   - Resolve args: {"portfolio_id": "abc-123", "pack_id": "PP_2025-01-15"}
   - Route capability: "portfolio.get_valued_positions"
   - AgentRuntime routes to FinancialAnalyst.portfolio_get_valued_positions()
   - Store result in state: state["valued_positions"] = {...}
   
4. Execute Step 2
   - Resolve args: {"portfolio_id": "abc-123", "positions": state["valued_positions"]["positions"]}
   - Route capability: "metrics.compute_twr"
   - AgentRuntime routes to FinancialAnalyst.metrics_compute_twr()
   - Store result in state: state["perf_metrics"] = {...}
   
5. Extract Outputs
   - Extract from state: {valued_positions: {...}, perf_metrics: {...}}
   - Build response: {data: {...}, charts: [...], trace: {...}}
   
6. Return Response
   {
     "status": "success",
     "data": {
       "valued_positions": {...},
       "perf_metrics": {...}
     },
     "trace": {...}
   }
```

---

## Pattern System Power

### 1. Composability

Patterns can reference other patterns' outputs:

```json
{
  "steps": [
    {
      "capability": "portfolio.get_valued_positions",
      "as": "valued_positions"
    },
    {
      "capability": "metrics.compute_twr",
      "args": {
        "positions": "{{valued_positions.positions}}"
      },
      "as": "perf_metrics"
    }
  ]
}
```

### 2. Conditional Execution

Steps can be conditionally executed:

```json
{
  "steps": [
    {
      "capability": "fundamentals.load",
      "as": "fundamentals",
      "condition": "{{inputs.include_fundamentals}} == true"
    }
  ]
}
```

### 3. Dynamic Template Resolution

Template variables enable powerful workflows:

```json
{
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    "pack_id": "{{ctx.pricing_pack_id}}",
    "asof_date": "{{ctx.asof_date}}"
  }
}
```

### 4. Reproducibility

RequestCtx ensures all operations are reproducible:

```python
ctx = RequestCtx(
    user_id=user_id,
    portfolio_id=portfolio_id,
    pricing_pack_id="PP_2025-01-15",  # SACRED
    ledger_commit_hash="abc123",       # SACRED
    asof_date=date.today()
)
```

### 5. Traceability

Execution trace tracks all operations:

```python
trace = {
    "pattern_id": "portfolio_overview",
    "pricing_pack_id": "PP_2025-01-15",
    "ledger_commit_hash": "abc123",
    "steps": [
        {
            "capability": "portfolio.get_valued_positions",
            "duration": 0.123,
            "agent": "financial_analyst"
        }
    ],
    "agents_used": ["financial_analyst"],
    "capabilities_used": ["portfolio.get_valued_positions", "metrics.compute_twr"]
}
```

---

## Pattern Output Formats

### Current State (3 Formats)

**Format 1: List**
```json
{
  "outputs": ["valued_positions", "perf_metrics"]
}
```

**Format 2: Dict**
```json
{
  "outputs": {
    "valued_positions": {},
    "perf_metrics": {}
  }
}
```

**Format 3: Panels**
```json
{
  "outputs": {
    "panels": [
      {"id": "panel1", "dataPath": "valued_positions"},
      {"id": "panel2", "dataPath": "perf_metrics"}
    ]
  }
}
```

### Target State (Single Format)

```json
{
  "outputs": {
    "panels": [
      {"id": "panel1", "dataPath": "valued_positions"},
      {"id": "panel2", "dataPath": "perf_metrics"}
    ],
    "data": {
      "valued_positions": "{{valued_positions}}",
      "perf_metrics": "{{perf_metrics}}"
    }
  }
}
```

---

## Pattern Registry (Frontend)

**Location:** `frontend/pattern-system.js`

**Purpose:** Frontend metadata for patterns

**Structure:**
```javascript
const patternRegistry = {
  portfolio_overview: {
    category: 'portfolio',
    name: 'Portfolio Overview',
    description: 'Comprehensive portfolio snapshot',
    icon: '📊',
    display: {
      panels: [
        {
          id: 'performance_strip',
          title: 'Performance Metrics',
          type: 'metrics_grid',
          dataPath: 'perf_metrics'
        }
      ]
    }
  }
};
```

---

## Pattern System Benefits

### 1. Business Logic Separation
- Business logic in JSON (patterns)
- Technical logic in Python (agents)
- Clear separation of concerns

### 2. Testability
- Patterns can be tested independently
- Mock agents for testing
- Reproducible execution

### 3. Maintainability
- Changes to business logic don't require code changes
- Patterns can be versioned
- Clear documentation in JSON

### 4. Flexibility
- New patterns can be added without code changes
- Patterns can be composed
- Dynamic template resolution

### 5. Observability
- Execution trace tracks all operations
- Reproducibility via RequestCtx
- Debugging made easy

---

## Pattern System Limitations

### 1. Output Format Inconsistency
- 3 different formats exist
- Orchestrator handles all 3 (complexity)
- UI must handle all 3 (complexity)

### 2. Template Resolution
- No validation of template variables
- Silent failures when variables don't exist
- Hard to debug template errors

### 3. Conditional Execution
- Simple condition evaluation
- No complex logic (if/else chains)
- Limited error handling in conditions

### 4. Error Handling
- Errors in steps stop execution
- No retry logic in patterns
- Limited error recovery

---

## Pattern System Future

### Planned Improvements
1. **Standardize Output Format** - Single format for all patterns
2. **Template Validation** - Validate template variables at pattern load time
3. **Error Recovery** - Retry logic in patterns
4. **Parallel Execution** - Execute independent steps in parallel
5. **Pattern Composition** - Patterns can call other patterns

---

## Key Takeaways

1. **Pattern system is the primary abstraction** - Business logic lives in patterns
2. **Template substitution is powerful** - Enables dynamic workflows
3. **RequestCtx ensures reproducibility** - All operations are traceable
4. **Composability is key** - Patterns can reference other patterns' outputs
5. **Standardization needed** - Output format inconsistency is a problem

---

**Status:** Deep Dive Complete  
**Last Updated:** January 15, 2025

