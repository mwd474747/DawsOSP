# Pattern Authoring Guide

**Version**: 1.0  
**Date**: October 17, 2025  
**Audience**: DawsOS pattern developers

---

## Overview

This guide provides best practices for creating robust, maintainable patterns in DawsOS. It addresses common pitfalls identified through pattern analysis and provides templates for common scenarios.

---

## Quick Reference

| Task | Use This | NOT This |
|------|----------|----------|
| Load knowledge file | `enriched_lookup` action | `can_fetch_economic_data` capability |
| Get live FRED data | `can_fetch_economic_data` capability | `enriched_lookup` action |
| Get live stock quote | `can_fetch_stock_quotes` capability | `enriched_lookup` action |
| Run agent analysis | `execute_through_registry` + capability | `"agent": "claude"` direct call |
| Reference step output | `{step_1}` | `{step_1.nested.field}` (fragile) |

---

## 1. Template Best Practices

### ✅ DO: Use Top-Level Variables

**Good**:
```json
{
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {"capability": "can_analyze_moat"},
      "save_as": "moat_analysis"
    }
  ],
  "response_template": "Moat Analysis:\n{moat_analysis}"
}
```

**Why**: `_smart_extract_value()` will try common response keys (response, friendly_response, result) automatically.

---

### ❌ DON'T: Use Nested Field References Without Validation

**Bad**:
```json
{
  "response_template": "Score: {moat_analysis.score}\nRating: {moat_analysis.rating}\nThesis: {moat_analysis.investment_thesis.summary}"
}
```

**Why**: If agent response structure changes or field is missing, template renders literal `{moat_analysis.score}` string.

**Solution**:
```json
{
  "response_template": "Moat Analysis:\n{moat_analysis}"
}
```

Let the agent format its own output, or use top-level variables only.

---

### Template Fallback Behavior

The `_smart_extract_value()` function tries these keys in order:
1. `data['response']` - Claude/LLM formatted responses
2. `data['friendly_response']` - Agent-formatted outputs
3. `data['result']['synthesis']` - Nested synthesis fields
4. `data['result']` - Raw result dict
5. `data` - Entire dict as-is

**Example**:
```json
{
  "save_as": "analysis"
}
```

If step returns:
```python
{
  "response": "The company has a strong moat...",
  "raw_data": {...}
}
```

Then `{analysis}` resolves to `"The company has a strong moat..."` (uses key #1).

---

## 2. Capability Selection Matrix

### Data Fetching (Live APIs)

| Capability | Use For | Agent | Example |
|------------|---------|-------|---------|
| `can_fetch_economic_data` | Live FRED data (GDP, CPI) | macro_analyst | Get current unemployment rate |
| `can_fetch_stock_quotes` | Live market data (prices, volume) | data_harvester | Get AAPL current price |
| `can_fetch_fundamentals` | Live financial statements | financial_analyst | Get MSFT quarterly earnings |
| `can_fetch_news` | Real-time news articles | data_harvester | Get AI news from past 7 days |

**Pattern Example** (Live Data):
```json
{
  "action": "execute_by_capability",
  "params": {
    "capability": "can_fetch_economic_data",
    "context": {
      "indicators": ["GDP", "UNEMPLOYMENT"],
      "start_date": "2024-01-01"
    }
  },
  "save_as": "economic_data"
}
```

---

### Knowledge Loading (Static Files)

For **all** knowledge file loading, use `enriched_lookup` action:

**Pattern Example** (Knowledge File):
```json
{
  "action": "enriched_lookup",
  "params": {
    "knowledge_file": "buffett_checklist.json"
  },
  "save_as": "buffett_framework"
}
```

**Available Knowledge Files**:
- `buffett_checklist.json`, `buffett_framework.json`
- `dalio_cycles.json`, `dalio_framework.json`
- `sector_performance.json`, `economic_cycles.json`
- `financial_calculations.json`, `financial_formulas.json`
- See `dawsos/storage/knowledge/` for full list (27 datasets)

---

### Analysis Capabilities

| Capability | Use For | Agent |
|------------|---------|-------|
| `can_calculate_dcf` | DCF valuation | financial_analyst |
| `can_analyze_moat` | Competitive advantage | financial_analyst |
| `can_detect_patterns` | Pattern recognition | pattern_spotter |
| `can_analyze_market_regime` | Risk-on/risk-off detection | pattern_spotter |
| `can_query_relationships` | Graph traversal | graph_mind |

**Pattern Example** (Analysis):
```json
{
  "action": "execute_by_capability",
  "params": {
    "capability": "can_calculate_dcf",
    "context": {
      "symbol": "{SYMBOL}",
      "projection_years": 5
    }
  },
  "save_as": "dcf_valuation"
}
```

---

## 3. Variable Resolution

### Automatic Variable Extraction

The pattern engine automatically resolves these variables from user input:

| Variable | Resolution Strategy | Example |
|----------|---------------------|---------|
| `{SYMBOL}` | Ticker → Company alias → Name → First uppercase word | "AAPL", "Apple Inc", "Apple" |
| `{SECTOR}` | Exact match → Case-insensitive match | "Technology", "tech" |
| `{user_input}` | Full user message | "analyze apple's moat" |

**Symbol Resolution Examples**:
- "analyze AAPL" → `SYMBOL=AAPL`
- "analyze Apple Inc" → `SYMBOL=AAPL` (via company_database lookup)
- "what about Tesla?" → `SYMBOL=TSLA` (via company_database lookup)

---

### Edge Cases to Handle

**Problem**: Ambiguous input doesn't resolve
- User says: "analyze meta platforms"
- Symbol extractor may fail (name mismatch, no ticker)

**Solution**: Document expected input format in pattern description
```json
{
  "description": "Analyzes a company's competitive moat. Expects clear ticker symbol (e.g., 'AAPL') or company name (e.g., 'Apple').",
  "triggers": ["moat analysis", "competitive advantage"]
}
```

---

## 4. Action Types

### Trinity-Compliant Actions (Use These)

| Action | Purpose | Example |
|--------|---------|---------|
| `execute_through_registry` | Agent execution via registry | Financial analysis |
| `execute_by_capability` | Capability-based routing | DCF calculation |
| `enriched_lookup` | Load knowledge file | Load buffett_checklist.json |
| `knowledge_lookup` | Query knowledge graph | Find sector nodes |

**Example Pattern with Multiple Actions**:
```json
{
  "steps": [
    {
      "description": "Load investment framework",
      "action": "enriched_lookup",
      "params": {"knowledge_file": "buffett_checklist.json"},
      "save_as": "framework"
    },
    {
      "description": "Analyze company using framework",
      "action": "execute_by_capability",
      "params": {
        "capability": "can_analyze_moat",
        "context": {
          "symbol": "{SYMBOL}",
          "framework": "{framework}"
        }
      },
      "save_as": "moat_analysis"
    }
  ]
}
```

---

### ❌ Avoid: Direct Agent Calls (Legacy)

**Bad** (Bypasses capability layer):
```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "claude",
    "context": {"prompt": "analyze {SYMBOL}"}
  }
}
```

**Good** (Uses capability):
```json
{
  "action": "execute_by_capability",
  "params": {
    "capability": "can_analyze_text",
    "context": {"text": "analyze {SYMBOL}"}
  }
}
```

---

## 5. Error Handling

### Silent Failure Edge Cases

The pattern engine handles these cases automatically but may produce unexpected results:

| Edge Case | Behavior | Prevention |
|-----------|----------|------------|
| Missing template field | Renders literal `{field}` string | Use top-level vars only |
| Unresolved variable | Empty string or literal `{VAR}` | Document expected input |
| Missing capability | Error logged, step skipped | Test pattern before deploying |
| Invalid JSON | Pattern not loaded | Use `python scripts/lint_patterns.py` |
| Nested pattern not found | Error logged | Ensure referenced patterns exist |

---

### Testing Your Pattern

1. **Validate JSON Structure**:
   ```bash
   python scripts/lint_patterns.py
   ```

2. **Test Variable Resolution**:
   - Try with clear ticker: "analyze AAPL"
   - Try with company name: "analyze Apple Inc"
   - Try with ambiguous input: "analyze apple" (should fail gracefully)

3. **Check Template Output**:
   - Run pattern and verify `{variables}` are resolved
   - Look for literal `{field}` strings (indicates missing field)

4. **Verify Capability Routing**:
   - Check logs for correct agent execution
   - Ensure no "capability not found" warnings

---

## 6. Pattern Structure Template

### Minimal Pattern

```json
{
  "id": "my_pattern",
  "name": "My Pattern",
  "description": "What this pattern does and what input it expects",
  "version": "1.0",
  "last_updated": "2025-10-17",
  "triggers": ["keyword1", "keyword2"],
  "steps": [
    {
      "description": "Step 1 description",
      "action": "execute_by_capability",
      "params": {
        "capability": "can_analyze_text",
        "context": {"text": "{user_input}"}
      },
      "save_as": "result"
    }
  ],
  "response_template": "Result:\n{result}"
}
```

---

### Multi-Step Pattern with Knowledge Loading

```json
{
  "id": "framework_analysis",
  "name": "Framework-Based Analysis",
  "description": "Analyzes a company using an investment framework",
  "version": "1.0",
  "last_updated": "2025-10-17",
  "triggers": ["buffett analysis", "framework analysis"],
  "steps": [
    {
      "description": "Load investment framework",
      "action": "enriched_lookup",
      "params": {"knowledge_file": "buffett_checklist.json"},
      "save_as": "framework"
    },
    {
      "description": "Fetch company fundamentals",
      "action": "execute_by_capability",
      "params": {
        "capability": "can_fetch_fundamentals",
        "context": {"symbol": "{SYMBOL}"}
      },
      "save_as": "fundamentals"
    },
    {
      "description": "Apply framework to company",
      "action": "execute_by_capability",
      "params": {
        "capability": "can_analyze_text",
        "context": {
          "prompt": "Analyze {SYMBOL} using this framework",
          "framework": "{framework}",
          "data": "{fundamentals}"
        }
      },
      "save_as": "analysis"
    }
  ],
  "response_template": "{analysis}"
}
```

---

## 7. Common Patterns to Copy

### Pattern: Load Knowledge + Analyze

**Use Case**: Apply a framework to user input

```json
{
  "steps": [
    {
      "action": "enriched_lookup",
      "params": {"knowledge_file": "YOUR_FRAMEWORK.json"},
      "save_as": "framework"
    },
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_analyze_text",
        "context": {
          "framework": "{framework}",
          "subject": "{user_input}"
        }
      },
      "save_as": "analysis"
    }
  ],
  "response_template": "{analysis}"
}
```

---

### Pattern: Fetch Live Data + Analyze

**Use Case**: Get real-time data and analyze it

```json
{
  "steps": [
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_fetch_stock_quotes",
        "context": {"symbol": "{SYMBOL}", "period": "1y"}
      },
      "save_as": "market_data"
    },
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_detect_patterns",
        "context": {"data": "{market_data}"}
      },
      "save_as": "patterns"
    }
  ],
  "response_template": "{patterns}"
}
```

---

### Pattern: Multi-Source Synthesis

**Use Case**: Combine knowledge + live data + analysis

```json
{
  "steps": [
    {
      "action": "enriched_lookup",
      "params": {"knowledge_file": "economic_cycles.json"},
      "save_as": "cycles_framework"
    },
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_fetch_economic_data",
        "context": {"indicators": ["GDP", "UNEMPLOYMENT"]}
      },
      "save_as": "live_data"
    },
    {
      "action": "execute_by_capability",
      "params": {
        "capability": "can_analyze_text",
        "context": {
          "framework": "{cycles_framework}",
          "data": "{live_data}",
          "task": "Identify current economic regime"
        }
      },
      "save_as": "regime_analysis"
    }
  ],
  "response_template": "{regime_analysis}"
}
```

---

## 8. Validation Checklist

Before submitting a pattern, verify:

- [ ] **JSON Valid**: Runs through `python scripts/lint_patterns.py` without errors
- [ ] **Capability Correct**: Uses `enriched_lookup` for knowledge, `can_fetch_*` for APIs
- [ ] **No Nested Fields**: Template uses `{step_1}` not `{step_1.nested.field}`
- [ ] **Consistent Routing**: Uses capability routing OR agent calls (not both)
- [ ] **Variables Documented**: Description explains expected input format
- [ ] **Tested**: Run pattern with sample inputs and verify output
- [ ] **No Duplicates**: Has either `template` OR `response_template` (not both)
- [ ] **Trinity Compliant**: Uses `execute_through_registry` or `execute_by_capability`

---

## 9. Reference Documentation

- **Capability List**: [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - All 103 capabilities
- **Known Issues**: [KNOWN_PATTERN_ISSUES.md](KNOWN_PATTERN_ISSUES.md) - Patterns needing fixes
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common errors and solutions
- **Architecture**: [.claude/trinity_architect.md](.claude/trinity_architect.md) - Trinity execution flow
- **Pattern Specialist**: [.claude/pattern_specialist.md](.claude/pattern_specialist.md) - Advanced pattern techniques

---

## 10. Getting Help

- **Pattern not working?** → Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Capability question?** → See [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md)
- **Architecture question?** → Consult [.claude/trinity_architect.md](.claude/trinity_architect.md)
- **Need review?** → Ask Pattern Specialist agent in `.claude/pattern_specialist.md`

---

**Last Updated**: October 17, 2025  
**Version**: 1.0  
**Maintained By**: DawsOS Architecture Team
