# Pattern Output Rendering Guide

**Date**: October 3, 2025
**Purpose**: Ensure consistent, formatted output from pattern execution in DawsOS

---

## Problem Statement

When patterns execute through the Trinity Architecture, raw JSON results are returned instead of formatted, user-friendly output. This guide explains how to configure patterns for proper output rendering.

### Example of Raw Output (Bad)
```json
{
  "pattern": "Sector Performance Analysis",
  "type": "analysis",
  "results": [
    {
      "step": 1,
      "action": "execute_through_registry",
      "result": {
        "response": "Processed request: Get sector ETFs performance...",
        "data": {},
        "agent": "DataHarvester"
      }
    }
  ],
  "formatted_response": "{sector_report}"
}
```

### Example of Formatted Output (Good)
```markdown
📊 **Sector Performance Analysis**

🏆 Leading Sectors (Past Month):
1. **Technology (XLK)**: +5.2% - AI momentum continues
2. **Communications (XLC)**: +4.8% - META/GOOGL strength
3. **Financials (XLF)**: +3.9% - Rate environment favorable

📉 Lagging Sectors:
7. **Energy (XLE)**: -2.1% - Oil price weakness
8. **Utilities (XLU)**: -2.8% - Rising yields pressure

💡 Opportunities:
• Tech pullbacks on profit-taking
• Financial strength on NIM expansion
```

---

## Solution: Proper Template Configuration

### 1. **Add a Template Field**

Every pattern must include a `template` field that defines how the output should be formatted.

```json
{
  "id": "buffett_checklist",
  "name": "Buffett Investment Checklist",
  "template": "✅ **Buffett Investment Checklist: {symbol}**\n\n{step_8.response}\n\n---\n\n💡 **Key Buffett Principles Applied**:\n• Circle of competence\n• Economic moat\n• Management matters\n\n*Analysis powered by DawsOS Trinity Architecture*",
  "steps": [...]
}
```

### 2. **Use Variable Substitution**

Templates support variable substitution from:
- **Input parameters**: `{symbol}`, `{request}`, etc.
- **Step results**: `{step_1.response}`, `{step_2.data}`, etc.
- **Nested fields**: `{step_4.owner_earnings}`, `{step_7.recommendation}`, etc.

### 3. **Template Syntax**

#### Basic Substitution
```
{variable_name}           → Simple substitution
{step_3.response}         → Step result field
{step_4.metrics.roic}     → Nested field access
```

#### Conditional Display
```
{#step_4.recommendations}
- {.}
{/step_4.recommendations}
```
This iterates over arrays/lists.

#### Formatting
```
{step_4.score:.0%}        → Format as percentage (85%)
{step_5.value:.2f}        → Format as decimal (12.34)
${step_4.value}M          → Add currency/units
```

---

## Pattern Template Examples

### Example 1: Buffett Checklist Pattern

```json
{
  "id": "buffett_checklist",
  "template": "✅ **Buffett Investment Checklist: {symbol}**\n\n{step_8.response}\n\n---\n\n💡 **Key Buffett Principles Applied**:\n• Circle of competence - only invest in businesses you understand\n• Economic moat - durable competitive advantage is essential\n• Management matters - integrity and capital allocation skills\n• Price is what you pay, value is what you get\n• Margin of safety - always demand a discount to intrinsic value\n\n*Analysis powered by DawsOS Trinity Architecture*",
  "steps": [
    {
      "description": "Synthesize Buffett checklist results",
      "action": "execute_through_registry",
      "params": {
        "agent": "claude",
        "context": {
          "task": "synthesize_buffett_analysis",
          "request": "Provide formatted analysis with clear sections"
        }
      },
      "save_as": "step_8"
    }
  ]
}
```

### Example 2: Economic Moat Pattern

```json
{
  "id": "moat_analyzer",
  "template": "🏰 **Economic Moat Analysis: {symbol}**\n\n{step_8.response}\n\n---\n\n📊 **Moat Sources Evaluated**\n\n🏷️ **Brand Moat**: {step_3.score}/10\n{step_3.summary}\n\n🌐 **Network Effects**: {step_4.score}/10\n{step_4.summary}\n\n💰 **Cost Advantages**: {step_5.score}/10\n{step_5.summary}\n\n🔒 **Switching Costs**: {step_6.score}/10\n{step_6.summary}\n\n📈 **Financial Evidence**\n• ROIC-WACC Spread: {step_7.spread}%\n• 10-Year Avg ROIC: {step_7.avg_roic}%\n• Margin Stability: {step_7.margin_stability}\n\n🎯 **Overall Moat Rating**: {step_8.moat_rating}\n• Width: {step_8.moat_width}\n• Durability: {step_8.moat_durability}\n• Trend: {step_8.moat_trend}\n\n💡 **Investment Implications**\n{step_8.investment_action}\n\n*Moat analysis powered by DawsOS Trinity Architecture*"
}
```

### Example 3: Governance Pattern

```json
{
  "id": "compliance_audit",
  "template": "**Compliance Audit Report**\n\n**Audit Request**: {request}\n\n**Compliance Score**: {step_4.compliance_score:.0%}\n\n**Regulatory Frameworks**:\n{#step_4.regulatory_frameworks}\n- {.}\n{/step_4.regulatory_frameworks}\n\n**Compliant Areas**:\n{#step_4.findings.compliant_areas}\n- ✅ {.}\n{/step_4.findings.compliant_areas}\n\n**Violations Found**:\n{#step_4.findings.violations}\n- ❌ {.}\n{/step_4.findings.violations}\n\n**Remediation Recommendations**:\n{#step_4.findings.recommendations}\n- {.}\n{/step_4.findings.recommendations}\n\n*Compliance monitoring powered by DawsOS Trinity Architecture*"
}
```

---

## Agent Response Structure

For proper rendering, agents should return structured responses that match the template expectations.

### Good Agent Response Structure

```python
# In Claude agent or other agents
def synthesize_buffett_analysis(self, context):
    """Return structured response for template rendering"""
    return {
        "response": """
        📊 **Overall Score**: 16/20 (Strong Buy)

        🏆 **Strengths**:
        • Simple, understandable business model (4/4)
        • Wide economic moat with pricing power (4/4)
        • Excellent management with 15% ROIC (3/4)

        ⚠️ **Concerns**:
        • Valuation slightly rich - limited margin of safety (2/4)

        🎯 **Investment Decision**: BUY
        Strong company, fair price. Watch for pullbacks.
        """,
        "total_score": 16,
        "max_score": 20,
        "recommendation": "BUY",
        "conviction": "High"
    }
```

### What PatternEngine Does

1. **Execute Steps**: Run each step through `execute_through_registry`
2. **Collect Results**: Store results as `step_1`, `step_2`, etc.
3. **Apply Template**: Substitute variables in template
4. **Return Formatted**: Return rendered template as `formatted_response`

### PatternEngine Template Rendering

Located in `dawsos/core/pattern_engine.py`:

```python
def _format_response(self, template: str, variables: Dict) -> str:
    """
    Apply template substitution to format final response

    Variables available:
    - Input parameters: {symbol}, {request}, etc.
    - Step results: {step_1.response}, {step_2.data}, etc.
    - Nested access: {step_4.metrics.roic}
    """
    formatted = template

    # Simple substitution
    for key, value in variables.items():
        formatted = formatted.replace(f"{{{key}}}", str(value))

    # Nested field access (step_4.score)
    for match in re.findall(r'\{(\w+\.\w+(?:\.\w+)*)\}', formatted):
        value = self._get_nested_value(variables, match)
        formatted = formatted.replace(f"{{{match}}}", str(value))

    return formatted
```

---

## Checklist for Pattern Authors

### ✅ Pattern Must Have:

1. **`template` field** - Defines output format
2. **Clear step descriptions** - Explains what each step does
3. **`save_as` for each step** - Stores results for template access
4. **Structured agent responses** - Agents return dict/object, not just strings
5. **Trinity compliance** - All agent calls use `execute_through_registry`

### ✅ Template Should Include:

1. **Header** - Pattern name and input parameters
2. **Main Content** - Key results from final synthesis step
3. **Supporting Sections** - Detailed breakdowns from each step
4. **Footer** - Credits/branding
5. **Emojis/Formatting** - Makes output readable and scannable

### ✅ Agent Response Should Include:

1. **`response` field** - Main formatted text for display
2. **Structured data fields** - Scores, metrics, lists for template access
3. **Consistent field names** - Match template expectations

---

## Testing Pattern Output

### Test Script

```python
# test_pattern_rendering.py
from core.agent_runtime import AgentRuntime
from core.pattern_engine import PatternEngine

runtime = AgentRuntime()
pattern_engine = PatternEngine(runtime, 'dawsos/patterns')

# Execute pattern
result = pattern_engine.execute_pattern(
    pattern_id='buffett_checklist',
    inputs={'symbol': 'AAPL'}
)

# Check output
if 'formatted_response' in result:
    print("✅ Template rendered successfully:")
    print(result['formatted_response'])
else:
    print("❌ No formatted_response - check template")
    print(result)
```

### Expected vs Actual

**Expected**: Formatted markdown output
**Actual (if no template)**: Raw JSON dict

Always verify `formatted_response` is present and readable.

---

## Common Issues and Solutions

### Issue 1: Raw JSON Output
**Symptom**: User sees `{"step_1": {...}, "step_2": {...}}`
**Cause**: No `template` field in pattern
**Solution**: Add `template` field to pattern JSON

### Issue 2: Missing Variables
**Symptom**: Template shows `{step_4.score}` literally
**Cause**: Step result doesn't have `score` field
**Solution**: Update agent to return structured response with required fields

### Issue 3: Empty Sections
**Symptom**: Sections show no data
**Cause**: Agent returns `None` or empty string
**Solution**: Ensure agent always returns valid data, use fallbacks

### Issue 4: Template Not Applied
**Symptom**: Output is raw, even with template
**Cause**: PatternEngine not calling `_format_response`
**Solution**: Check pattern_engine.py processes template field

---

## Converted Patterns (Trinity-Compliant)

The following patterns have been converted to Trinity architecture with proper templates:

### ✅ Analysis Patterns
1. **buffett_checklist.json** - v2.0 (Trinity)
2. **moat_analyzer.json** - v2.0 (Trinity)
3. **owner_earnings.json** - v2.0 (Trinity)
4. **fundamental_analysis.json** - v2.0 (Trinity)

### ✅ Governance Patterns
1. **compliance_audit.json** - Has template
2. **cost_optimization.json** - Has template
3. **data_quality_check.json** - Has template
4. **policy_validation.json** - Has template
5. **governance_template.json** - Universal template

### ⚠️ Patterns Still Using Legacy Actions
- **dalio_cycle.json** - Uses `knowledge_lookup`, `calculate`
- **sector_rotation.json** - Uses `knowledge_lookup`
- **comprehensive_analysis.json** - Uses `knowledge_lookup`

These still work but should be converted to Trinity for consistency.

---

## Summary

### Key Principles

1. **Every pattern needs a `template` field**
2. **Templates use `{variable}` substitution**
3. **Agents return structured responses** (dicts with named fields)
4. **Final step synthesizes results** for clean summary
5. **PatternEngine applies template** automatically

### Expected Behavior

**Input**: User executes pattern via UI
**Process**: Pattern → Steps → Agents → Results → Template
**Output**: Formatted markdown displayed in Streamlit

### Validation

Run `test_buffett_integration.py` to verify:
- ✅ Data files load (buffett_checklist.json, dalio_cycles.json)
- ✅ Patterns have templates
- ✅ execute_through_registry works
- ✅ Output is formatted (not raw JSON)

---

**Status**: ✅ Buffett analysis patterns fully integrated with proper output rendering
**Next**: Convert remaining 3 patterns (dalio_cycle, sector_rotation, comprehensive_analysis) to Trinity
