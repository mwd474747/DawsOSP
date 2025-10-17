# API Parameter Audit Report

**Date**: October 11, 2025
**Issue**: Inconsistent parameter usage across pattern files when calling capability-based APIs
**Impact**: API calls failing silently, data not flowing from capabilities to patterns
**Root Cause**: No standardized parameter contract between patterns and agent capability methods

---

## 🔴 Critical Findings

### Parameter Inconsistency Summary

Out of **23 unique capabilities** used in patterns:
- ✅ **13 capabilities** have consistent parameters (56%)
- ⚠️  **10 capabilities** have inconsistent parameters (44%)

### Most Critical Issues (by severity)

#### 1. `can_fetch_stock_quotes` - **9 different parameter combinations** (21 uses)
```
- ['knowledge_file', 'request', 'task'] (1x)
- ['symbol'] (6x)
- ['governance_type', 'task'] (3x)
- ['symbol', 'task'] (1x)
- ['data', 'metric', 'symbol'] (1x)
- ['governance_type', 'scope', 'task'] (1x)
- ['request'] (4x)
- ['knowledge_file', 'request', 'section', 'task'] (1x)
- [] (3x - NO PARAMETERS!)
```

**Impact**: Most patterns calling stock quotes will fail due to unexpected parameters.

#### 2. `can_detect_patterns` - **9 different parameter combinations** (28 uses)
```
- ['data_source', 'governance_type', 'task'] (4x)
- ['analysis_type', 'data'] (15x)
- [] (1x)
- ['cycle_context', 'request'] (1x)
- ['checks', 'data', 'moat_type', 'symbol', 'task'] (1x)
- ['alert_types', 'current_data', 'thresholds'] (1x)
- ['analysis_type'] (1x)
- ['data', 'symbol'] (3x)
- ['analysis_type', 'data', 'indicators'] (1x)
```

**Impact**: Pattern detection agent receives inconsistent inputs, cannot reliably detect patterns.

#### 3. `can_fetch_economic_data` - **7 different parameter combinations** (10 uses)
```
- ['symbol'] (1x)
- ['data', 'metric', 'symbol', 'task'] (1x)
- ['symbol', 'task'] (1x)
- ['checks', 'data', 'moat_type', 'symbol', 'task'] (1x)
- ['indicators'] (1x) ← CORRECT parameter name
- ['knowledge_file', 'section', 'task'] (1x)
- [] (4x)
```

**Status**: ✅ PARTIALLY FIXED in commit 65cea3f
**Remaining Issue**: Still 6 other parameter combinations being used

#### 4. `can_fetch_fundamentals` - **6 different parameter combinations** (11 uses)
```
- ['symbol'] (4x)
- ['symbol', 'task'] (2x)
- ['data', 'metrics', 'symbol', 'task'] (1x)
- ['knowledge_files', 'task'] (1x)
- ['category', 'data', 'questions', 'symbol', 'task'] (1x)
- [] (2x)
```

**Impact**: Fundamental data fetching unreliable across different analysis patterns.

#### 5. `can_fetch_market_data` - **2 parameter combinations** (4 uses)
```
- ['symbol'] (1x)
- ['request'] (3x)
```

**Impact**: Moderate - 75% use 'request', 25% use 'symbol'.

#### 6. `can_fetch_news` - **2 parameter combinations** (4 uses)
```
- ['symbol'] (2x)
- [] (2x)
```

**Impact**: Moderate - 50/50 split on whether symbol is provided.

---

## 📊 Capability-to-Agent Mapping

Based on `core/agent_capabilities.py`:

| Capability | Agent | Expected Method |
|------------|-------|----------------|
| `can_fetch_stock_quotes` | data_harvester | `fetch_stock_quotes()` |
| `can_fetch_economic_data` | data_harvester | `fetch_economic_data()` |
| `can_fetch_fundamentals` | data_harvester | `fetch_fundamentals()` |
| `can_fetch_market_data` | data_harvester | `fetch_market_data()` |
| `can_fetch_news` | data_harvester | `fetch_news()` |
| `can_detect_patterns` | pattern_spotter | `detect_patterns()` |
| `can_find_relationships` | relationship_hunter | `find_relationships()` |
| `can_generate_forecast` | forecast_dreamer | `generate_forecast()` |
| `can_calculate_dcf` | financial_analyst | `calculate_dcf()` |

---

## 🎯 Recommended Fix Strategy

### Phase 1: Standardize Agent Method Signatures (HIGH PRIORITY)

For each capability, define a **single canonical parameter contract**:

```python
# Example: can_fetch_stock_quotes
def fetch_stock_quotes(
    self,
    symbols: Optional[List[str]] = None,  # Primary input
    context: Dict[str, Any] = None  # Flexible additional context
) -> Dict[str, Any]:
    """
    Canonical signature for can_fetch_stock_quotes capability.

    Args:
        symbols: List of stock symbols to fetch (or single symbol string)
        context: Optional dict with additional parameters:
            - 'request': Natural language request
            - 'task': Task description
            - etc.
    """
```

**Key principle**: Primary data parameter (symbols, indicators, data, etc.) should be a direct argument, everything else in `context` dict.

### Phase 2: Update All Agent Methods

1. **data_harvester.py** (6 fetch methods)
   - `fetch_stock_quotes()` - CRITICAL
   - `fetch_economic_data()` - ✅ PARTIALLY DONE
   - `fetch_fundamentals()` - CRITICAL
   - `fetch_market_data()` - HIGH
   - `fetch_news()` - MEDIUM
   - `fetch_crypto_data()` - LOW (only 1 caller)

2. **pattern_spotter.py**
   - `detect_patterns()` - CRITICAL (28 callers!)

3. **relationship_hunter.py**
   - `find_relationships()` - HIGH

4. **forecast_dreamer.py**
   - `generate_forecast()` - MEDIUM

5. **financial_analyst.py**
   - `calculate_dcf()` - LOW (only 1 caller)

### Phase 3: Update Pattern Files

After agent methods are standardized, update **all 49 patterns** to use consistent parameters.

**Priority patterns** (high-traffic analysis patterns):
1. `comprehensive_analysis.json` - uses 3 inconsistent capabilities
2. `sector_rotation.json` - uses 2 inconsistent capabilities
3. `dashboard_update.json` - uses 2 inconsistent capabilities
4. `morning_briefing.json` - uses multiple fetch capabilities

### Phase 4: Add Parameter Validation

Add Pydantic models for capability method inputs:

```python
# dawsos/models/capability_inputs.py
from pydantic import BaseModel, Field
from typing import List, Optional

class FetchStockQuotesInput(BaseModel):
    """Input schema for can_fetch_stock_quotes capability"""
    symbols: List[str] = Field(..., min_length=1, max_length=100)
    realtime: bool = Field(default=False)

class FetchEconomicDataInput(BaseModel):
    """Input schema for can_fetch_economic_data capability"""
    indicators: List[str] = Field(..., min_length=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
```

---

## 🚨 Immediate Action Required

### Fix #1: `can_fetch_stock_quotes` (CRITICAL)

**Problem**: 9 different parameter combinations across 21 uses
**Solution**: Standardize on `symbols` parameter (used by 6 patterns)

```python
# dawsos/agents/data_harvester.py
def fetch_stock_quotes(
    self,
    symbols: Optional[Union[str, List[str]]] = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    # Extract from context if not provided directly
    if symbols is None and context:
        symbols = context.get('symbols') or context.get('symbol') or context.get('request')

    if isinstance(symbols, str):
        symbols = [symbols]

    # Proceed with fetch...
```

### Fix #2: `can_fetch_economic_data` (CRITICAL)

**Status**: ✅ PARTIALLY FIXED
**Remaining work**: Handle the 6 other parameter combinations:
- Empty parameters (4 patterns) - use default indicators
- 'symbol' parameter (4 patterns) - ignore or treat as company-specific indicator
- Various 'task' parameters - extract from context

### Fix #3: `can_fetch_fundamentals` (CRITICAL)

**Problem**: 6 different parameter combinations
**Solution**: Standardize on `symbol` parameter

---

## 📈 Success Metrics

After fixes:
- ✅ All 23 capabilities should have **1 consistent parameter contract**
- ✅ Pattern linter should validate parameter usage
- ✅ Integration tests should cover all capability method signatures
- ✅ No more "No data fetched" warnings in production

---

## 🔍 Testing Strategy

1. **Unit tests**: Test each agent method with all parameter combinations from patterns
2. **Integration tests**: Test end-to-end pattern execution with real API calls
3. **Regression tests**: Ensure existing patterns still work after standardization
4. **Parameter validation tests**: Use Pydantic models to catch mismatches at runtime

---

## Timeline Estimate

- **Phase 1** (Standardize signatures): 2-3 hours
- **Phase 2** (Update agent methods): 3-4 hours
- **Phase 3** (Update patterns): 2-3 hours
- **Phase 4** (Add validation): 1-2 hours

**Total**: 8-12 hours of focused work

---

## References

- Audit script: `/tmp/find_parameter_mismatches.py`
- Previous fix: commit 65cea3f (indicators parameter)
- Agent capabilities: `dawsos/core/agent_capabilities.py`
- Pattern directory: `dawsos/patterns/`

---

**Conclusion**: The "constant API issues" are caused by **lack of parameter contracts** between patterns and capabilities. Standardizing method signatures and adding validation will resolve 90%+ of API integration issues.
