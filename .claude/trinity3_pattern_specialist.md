# Trinity 3.0 Pattern Specialist

**Your Role**: Port the pattern system (engine + actions + templates) from DawsOS 2.0 to Trinity 3.0

**Timeline**: Week 2-3, 6, 9
**Deliverables**:
- Week 2: Pattern Engine with 24 actions
- Week 3: 5 smart patterns working
- Week 6: 3 workflow patterns working
- Week 9: 6 economic patterns working

---

## Mission

Enable Trinity 3.0 to execute the same pattern-driven workflows as DawsOS 2.0:
- Port pattern_engine.py (2,291 lines) with template validation fixes
- Port 24 action implementations
- Migrate 14 patterns (5 smart, 3 workflows, 6 economic)
- Fix template field fragility issues
- Validate all patterns execute correctly

---

## Week 2 Tasks

### Day 1-2: Pattern Engine Core (2,291 lines)

**Source**: `dawsos/core/pattern_engine.py`
**Destination**: `trinity3/core/pattern_engine.py`

**Port These Components**:

1. **PatternEngine Class** (lines 1-2291):
```python
class PatternEngine:
    def __init__(self, runtime, knowledge_loader, config):
        self.runtime = runtime
        self.knowledge_loader = knowledge_loader
        self.config = config
        self.patterns_dir = Path(config.patterns_dir)
        self.logger = logging.getLogger(__name__)
        self.available_patterns = {}
        self._load_all_patterns()

    def execute_pattern(self, pattern_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point - loads pattern JSON and executes steps"""
        # Validate pattern exists
        # Resolve variables in context
        # Execute steps sequentially
        # Apply template to results
        # Return formatted response

    def _execute_step(self, step: Dict, context: Dict) -> Any:
        """Executes single pattern step - routes to action implementations"""
        # Look up action from core/actions/
        # Execute with context
        # Handle errors with fallback

    def _apply_template(self, template: str, data: Dict) -> str:
        """Substitute {variables} in template with data values"""
        # Use _smart_extract_value for nested paths
        # Handle missing fields gracefully
```

2. **Variable Resolution** (lines 450-680):
```python
def _resolve_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves {SYMBOL}, {TIMEFRAME}, etc. from user input"""
    resolved = context.copy()

    # Symbol resolution priority:
    # 1. Exact ticker match (AAPL)
    # 2. Company alias lookup (Apple → AAPL)
    # 3. Company name match
    # 4. First uppercase word in query

    if 'query' in context:
        query = context['query']
        # Extract symbol
        # Extract timeframe
        # Extract depth
        resolved.update({...})

    return resolved
```

3. **Template Field Extraction** (lines 1100-1350):
```python
def _smart_extract_value(self, data: Any, field: str) -> str:
    """Fallback logic for missing nested fields"""
    # Try exact path first: data['step_3']['score']
    if isinstance(data, dict):
        try:
            # Navigate nested path
            value = data
            for key in field.split('.'):
                value = value[key]
            return str(value)
        except (KeyError, TypeError):
            pass

    # Fallback to common response keys:
    # 1. data['response']
    # 2. data['friendly_response']
    # 3. data['result']['synthesis']
    # 4. data['result']
    # 5. str(data)

    # If all fail, return literal {field} (known issue)
    return f"{{{field}}}"
```

**CRITICAL FIX - Template Validation**:

Add new validation layer to prevent template fragility:

```python
def _validate_template(self, template: str, available_fields: Set[str]) -> List[str]:
    """Validate all {fields} in template can be resolved"""
    import re

    # Extract all {field} references
    pattern = r'\{([^}]+)\}'
    fields = re.findall(pattern, template)

    missing = []
    for field in fields:
        # Check if field exists in data
        # For nested paths (step_3.score), verify step_3 returns dict with 'score'
        if field not in available_fields:
            missing.append(field)

    return missing

def execute_pattern(self, pattern_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # Execute all steps
    results = {}
    for step in pattern['steps']:
        step_result = self._execute_step(step, context)
        results[step['id']] = step_result

    # NEW: Validate template before applying
    template = pattern.get('template', pattern.get('response_template', ''))
    available_fields = set(results.keys())
    missing_fields = self._validate_template(template, available_fields)

    if missing_fields:
        self.logger.warning(f"Template has unresolvable fields: {missing_fields}")
        # Either: fail with error, or: strip unresolvable fields

    # Apply template
    response = self._apply_template(template, results)
    return {'response': response, 'pattern': pattern_id, 'results': results}
```

**Test Suite** (create `trinity3/tests/test_pattern_engine.py`):
```python
def test_pattern_execution():
    engine = PatternEngine(runtime, knowledge_loader, config)

    # Test 1: Load pattern
    pattern = engine.load_pattern('smart_stock_analysis')
    assert pattern is not None
    assert 'steps' in pattern

    # Test 2: Variable resolution
    context = {'query': 'Analyze Apple', 'depth': 'quick'}
    resolved = engine._resolve_variables(context)
    assert resolved['SYMBOL'] == 'AAPL'

    # Test 3: Template validation
    template = "Score: {step_3.score}\nRating: {step_3.rating}"
    available = {'step_1', 'step_2', 'step_3'}  # step_3 is dict
    missing = engine._validate_template(template, available)
    # Should warn if step_3 doesn't have 'score' key

    # Test 4: Execute full pattern
    result = engine.execute_pattern('smart_stock_analysis', context)
    assert 'response' in result
    assert result['pattern'] == 'smart_stock_analysis'
```

**Success Criteria**:
- Pattern engine loads all patterns from JSON
- Variable resolution: 100% on common cases (AAPL, Apple, apple)
- Template validation: Catches all unresolvable fields
- No crashes on missing fields

---

### Day 3-5: Action Registry (24 files)

**Source**: `dawsos/core/actions/`
**Destination**: `trinity3/core/actions/`

**Port All 24 Actions**:

1. **execute_through_registry.py** (Primary action)
```python
def execute(context: Dict, runtime) -> Dict[str, Any]:
    """Execute capability via agent registry"""
    agent_name = context.get('agent')
    capability = context.get('capability')

    if capability:
        return runtime.execute_by_capability(capability, context)
    elif agent_name:
        return runtime.exec_via_registry(agent_name, context)
    else:
        raise ValueError("Need either 'agent' or 'capability'")
```

2. **execute_by_capability.py**
```python
def execute(context: Dict, runtime) -> Dict[str, Any]:
    """Capability-based routing (Trinity 2.0 standard)"""
    capability = context.get('capability')
    return runtime.execute_by_capability(capability, context)
```

3. **synthesize.py**
```python
def execute(context: Dict, runtime) -> Dict[str, Any]:
    """LLM synthesis of analysis results"""
    prompt = context.get('synthesis_prompt')
    data = context.get('data_to_synthesize')

    # Call Claude to create friendly summary
    response = runtime.execute_by_capability('can_synthesize_analysis', {
        'prompt': prompt,
        'data': data
    })

    return response
```

4. **enriched_lookup.py**
```python
def execute(context: Dict, knowledge_loader) -> Dict[str, Any]:
    """Load knowledge file (not FRED API!)"""
    dataset_name = context.get('dataset')

    # Use KnowledgeLoader with 30-min cache
    data = knowledge_loader.get_dataset(dataset_name)

    return {'data': data, 'source': 'knowledge_graph'}
```

5. **normalize_response.py**
```python
def execute(context: Dict) -> Dict[str, Any]:
    """Standardize response format"""
    data = context.get('data')

    # Convert to standard format
    normalized = {
        'response': data.get('response', str(data)),
        'friendly_response': data.get('friendly_response'),
        'metadata': data.get('metadata', {})
    }

    return normalized
```

**Remaining 19 Actions to Port**:
- fetch_stock_data.py
- fetch_fundamentals.py
- fetch_economic_data.py
- calculate_metrics.py
- analyze_sentiment.py
- detect_patterns.py
- compare_entities.py
- rank_opportunities.py
- assess_risk.py
- generate_signals.py
- build_allocation.py
- optimize_portfolio.py
- backtest_strategy.py
- format_output.py
- validate_input.py
- handle_error.py
- cache_result.py
- log_event.py
- measure_performance.py

**Action Registry Loader**:
```python
# trinity3/core/action_registry.py
import importlib
from pathlib import Path

class ActionRegistry:
    def __init__(self):
        self.actions = {}
        self._load_actions()

    def _load_actions(self):
        """Dynamically load all actions from core/actions/"""
        actions_dir = Path(__file__).parent / 'actions'

        for action_file in actions_dir.glob('*.py'):
            if action_file.name == '__init__.py':
                continue

            module_name = action_file.stem
            module = importlib.import_module(f'core.actions.{module_name}')

            # Each action must have execute() function
            if hasattr(module, 'execute'):
                self.actions[module_name] = module.execute

    def execute_action(self, action_name: str, context: Dict) -> Any:
        """Execute action by name"""
        if action_name not in self.actions:
            raise ValueError(f"Unknown action: {action_name}")

        return self.actions[action_name](context)
```

**Test Suite**:
```python
def test_action_registry():
    registry = ActionRegistry()

    # Test 1: All actions loaded
    assert len(registry.actions) == 24

    # Test 2: Execute through registry
    result = registry.execute_action('execute_through_registry', {
        'capability': 'can_analyze_text',
        'data': 'test'
    })
    assert result is not None

    # Test 3: Enriched lookup
    result = registry.execute_action('enriched_lookup', {
        'dataset': 'sector_performance'
    })
    assert 'data' in result
    assert result['source'] == 'knowledge_graph'
```

**Success Criteria**:
- All 24 actions port successfully
- ActionRegistry loads all dynamically
- Pattern engine can call actions via registry
- No hardcoded action paths

---

## Week 3 Tasks

### Day 1-5: Smart Patterns (5 patterns)

**Patterns to Port**:
1. `smart_stock_analysis.json` - Conditional execution based on analysis_type
2. `smart_portfolio_review.json` - Dynamic depth routing
3. `smart_market_briefing.json` - Timeframe-based data selection
4. `smart_opportunity_finder.json` - Strategy-aware scanning
5. `smart_risk_analyzer.json` - Multi-factor risk assessment

**Example Port - smart_stock_analysis.json**:

**Source**: `dawsos/patterns/smart/smart_stock_analysis.json`
**Destination**: `trinity3/patterns/smart/smart_stock_analysis.json`

**Key Changes**:
1. Validate all template fields exist
2. Fix capability misuse (use enriched_lookup for knowledge, not can_fetch_economic_data)
3. Add error handling for missing data

**Original (with issues)**:
```json
{
  "steps": [
    {
      "id": "step_1",
      "description": "Fetch fundamentals",
      "action": "execute_through_registry",
      "capability": "can_fetch_economic_data",  // WRONG - loads knowledge file
      "context": {
        "dataset": "financial_calculations"
      }
    }
  ],
  "template": "{step_3.score} - {step_3.nested.field}"  // FRAGILE - nested path
}
```

**Fixed**:
```json
{
  "steps": [
    {
      "id": "step_1",
      "description": "Load financial calculations knowledge",
      "action": "enriched_lookup",  // CORRECT
      "context": {
        "dataset": "financial_calculations"
      }
    },
    {
      "id": "step_2",
      "description": "Fetch fundamentals from market data",
      "action": "execute_by_capability",
      "capability": "can_fetch_fundamentals",  // CORRECT - API call
      "context": {
        "symbol": "{SYMBOL}",
        "metrics": ["pe_ratio", "revenue_growth", "profit_margin"]
      }
    },
    {
      "id": "step_3",
      "description": "Analyze fundamentals",
      "action": "execute_by_capability",
      "capability": "can_analyze_fundamentals",
      "context": {
        "fundamentals": "{step_2}",
        "benchmarks": "{step_1}"
      }
    }
  ],
  "template": "**Analysis for {SYMBOL}**\n\n{step_3}"  // SAFE - top-level only
}
```

**Test Each Pattern**:
```python
def test_smart_stock_analysis():
    engine = PatternEngine(runtime, knowledge_loader, config)

    # Test 1: Quick analysis
    result = engine.execute_pattern('smart_stock_analysis', {
        'query': 'Quick check on AAPL',
        'depth': 'quick',
        'analysis_type': 'fundamental'
    })
    assert 'AAPL' in result['response']
    assert len(result['results']) >= 3  # At least 3 steps executed

    # Test 2: Deep dive
    result = engine.execute_pattern('smart_stock_analysis', {
        'query': 'Deep dive into MSFT',
        'depth': 'deep',
        'analysis_type': 'comprehensive'
    })
    assert 'MSFT' in result['response']
    # Deep dive should have more steps

    # Test 3: Template fields all resolve
    assert '{step_' not in result['response']  # No unresolved fields
```

**Success Criteria**:
- All 5 smart patterns execute without errors
- Template fields 100% resolved (no literal `{field}` in output)
- Capability routing correct (no API calls for knowledge files)
- Conditional execution works based on depth/type/timeframe

---

## Week 6 Tasks

### Day 1-5: Workflow Patterns (3 complex patterns)

**Patterns to Port**:
1. `deep_dive.json` - 6-step orchestrated analysis (80-line template)
2. `buffett_checklist.json` - 8-step investment checklist
3. `moat_analyzer.json` - Multi-step competitive analysis

**Challenges**:
- Complex templates with 15+ nested field references
- Multi-step orchestration (step 3 depends on step 1 + step 2)
- Knowledge file integration
- Synthesis of multiple agent outputs

**Example - deep_dive.json**:

**Original Template (Fragile)**:
```json
"template": "🔍 **Company Deep Dive: {SYMBOL}**\n\n{investment_thesis.response}\n\n---\n\n📋 **Executive Summary**\n{investment_thesis.executive_summary}\n\n🏢 **Business Analysis**\n{structured_analysis.business_model}\n\n💰 **Financial Health**\n{structured_analysis.financial_health.score}/10\n..."
```

**Fixed Template (Validated)**:
```json
"steps": [
  {
    "id": "investment_thesis",
    "description": "Generate investment thesis",
    "action": "execute_by_capability",
    "capability": "can_generate_investment_thesis",
    "context": {
      "symbol": "{SYMBOL}",
      "depth": "{DEPTH}"
    }
  },
  {
    "id": "structured_analysis",
    "description": "Structured business analysis",
    "action": "execute_by_capability",
    "capability": "can_analyze_business_model",
    "context": {
      "symbol": "{SYMBOL}",
      "thesis": "{investment_thesis}"
    }
  },
  {
    "id": "synthesis",
    "description": "Synthesize all findings",
    "action": "synthesize",
    "context": {
      "synthesis_prompt": "Create executive summary for {SYMBOL} based on thesis and analysis",
      "data_to_synthesize": {
        "thesis": "{investment_thesis}",
        "analysis": "{structured_analysis}"
      }
    }
  }
],
"template": "**Company Deep Dive: {SYMBOL}**\n\n{synthesis}"  // SAFE - synthesis guaranteed to be string
```

**Key Changes**:
1. Add synthesis step to flatten nested responses
2. Avoid nested template paths (`{step.nested.field}`)
3. Validate each step returns expected structure
4. Add error handling for missing capabilities

**Test Workflow Patterns**:
```python
def test_deep_dive_pattern():
    engine = PatternEngine(runtime, knowledge_loader, config)

    # Test 1: Full execution
    result = engine.execute_pattern('deep_dive', {
        'query': 'Deep dive into AAPL',
        'depth': 'deep'
    })

    # Verify all 6 steps executed
    assert 'investment_thesis' in result['results']
    assert 'structured_analysis' in result['results']
    assert 'synthesis' in result['results']

    # Verify template fully resolved
    assert '{' not in result['response'] or result['response'].count('{') == result['response'].count('${')  # Allow ${} but not {}

    # Test 2: Step dependencies
    # structured_analysis should receive investment_thesis output
    assert result['results']['structured_analysis']['context']['thesis'] is not None
```

**Success Criteria**:
- All 3 workflow patterns execute 100% (6-8 steps each)
- Templates fully resolve (zero unresolved fields)
- Step dependencies work correctly
- No capability misuse
- Synthesis integrates cleanly

---

## Week 9 Tasks

### Day 1-5: Economic Patterns (6 Bloomberg-quality patterns)

**Patterns to Port**:
1. `recession_risk_dashboard.json` - Multi-indicator probability analysis
2. `macro_aware_sector_allocation.json` - Regime-driven rotation
3. `multi_timeframe_economic_outlook.json` - Scenario planning
4. `fed_policy_impact_analyzer.json` - Transmission mechanism
5. `housing_credit_cycle.json` - Real estate + debt cycle
6. `labor_market_deep_dive.json` - Employment analysis

**Data Sources**:
- FRED API for economic indicators
- Knowledge files for regime frameworks
- Prediction models for scenario forecasting

**Example - recession_risk_dashboard.json**:

```json
{
  "id": "recession_risk_dashboard",
  "name": "Recession Risk Dashboard",
  "description": "Multi-indicator recession probability with scenario forecasts",
  "version": "1.0",
  "steps": [
    {
      "id": "fetch_indicators",
      "description": "Fetch economic indicators from FRED",
      "action": "execute_by_capability",
      "capability": "can_fetch_economic_data",
      "context": {
        "indicators": ["GDP", "UNRATE", "T10Y2Y", "CPALTT01USM659N"],
        "lookback_quarters": 12
      }
    },
    {
      "id": "load_framework",
      "description": "Load recession framework from knowledge",
      "action": "enriched_lookup",
      "context": {
        "dataset": "economic_cycles"
      }
    },
    {
      "id": "calculate_probability",
      "description": "Calculate recession probability",
      "action": "execute_by_capability",
      "capability": "can_assess_recession_risk",
      "context": {
        "indicators": "{fetch_indicators}",
        "framework": "{load_framework}"
      }
    },
    {
      "id": "scenario_forecast",
      "description": "Generate scenario forecasts",
      "action": "execute_by_capability",
      "capability": "can_forecast_scenarios",
      "context": {
        "current_state": "{calculate_probability}",
        "timeframes": ["3m", "6m", "12m"]
      }
    },
    {
      "id": "synthesis",
      "description": "Create executive dashboard",
      "action": "synthesize",
      "context": {
        "synthesis_prompt": "Create recession risk dashboard with probability, key indicators, and scenario forecasts",
        "data_to_synthesize": {
          "probability": "{calculate_probability}",
          "scenarios": "{scenario_forecast}"
        }
      }
    }
  ],
  "template": "**Recession Risk Dashboard**\n\n{synthesis}"
}
```

**Test Economic Patterns**:
```python
def test_recession_risk_dashboard():
    engine = PatternEngine(runtime, knowledge_loader, config)

    # Test 1: Execute pattern
    result = engine.execute_pattern('recession_risk_dashboard', {})

    # Verify FRED data fetched
    assert 'fetch_indicators' in result['results']
    assert 'GDP' in str(result['results']['fetch_indicators'])

    # Verify knowledge loaded
    assert 'load_framework' in result['results']

    # Verify synthesis
    assert 'synthesis' in result['results']
    assert 'Recession' in result['response']
```

**Success Criteria**:
- All 6 economic patterns execute with real FRED data
- No mock data (PredictionService, CycleService removed)
- Templates resolve correctly
- Synthesis creates Bloomberg-quality output

---

## Common Issues & Solutions

### Issue 1: Template Field Not Resolving
**Symptom**: Output shows literal `{step_3.score}`
**Root Cause**: step_3 doesn't return dict with 'score' key
**Solution**:
1. Check step_3 action output structure
2. Either: Fix action to return dict with 'score', or: Use `{step_3}` instead

### Issue 2: Capability Misuse
**Symptom**: Pattern slow, unnecessary API calls
**Root Cause**: Using `can_fetch_economic_data` to load knowledge files
**Solution**: Use `enriched_lookup` action for knowledge, `can_fetch_economic_data` for FRED API

### Issue 3: Pattern Not Loading
**Symptom**: `PatternEngine.load_pattern()` returns None
**Root Cause**: JSON syntax error or missing required fields
**Solution**:
1. Validate JSON syntax
2. Check required fields: id, name, description, version, steps
3. Run `python scripts/lint_patterns.py`

### Issue 4: Step Dependencies Broken
**Symptom**: step_3 gets empty context
**Root Cause**: Variable substitution `{step_1}` not resolving
**Solution**: Ensure step_1 ID matches exactly in context reference

---

## Resources

- **Pattern Examples**: `dawsos/patterns/` (50 patterns)
- **Action Implementations**: `dawsos/core/actions/` (24 files)
- **Template Authoring**: [PATTERN_AUTHORING_GUIDE.md](../PATTERN_AUTHORING_GUIDE.md)
- **Known Issues**: [archive/legacy/technical_debt/KNOWN_PATTERN_ISSUES.md](../archive/legacy/technical_debt/KNOWN_PATTERN_ISSUES.md)

**Report to**: Migration Lead
**Update**: MIGRATION_STATUS.md weekly
**Escalate**: Template validation failures, capability routing errors
