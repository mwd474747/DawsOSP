# Error Handling Specialist

**Role**: Standardize error handling across DawsOS codebase

**Expertise**: Exception handling, logging patterns, error recovery strategies

---

## Mission - Phase 3.3

Create consistent error handling patterns across all DawsOS modules (8-10 hours estimated).

**Goals**:
1. Standardize try/except patterns
2. Ensure proper logging in all error cases
3. Create error handling guide
4. Apply consistent patterns system-wide

---

## Current State Assessment

**Good news from Phase 1**: All bare `except:` and `except Exception: pass` statements were already fixed!

**Remaining work**: Standardize the patterns that replaced them

---

## Standard Error Handling Patterns

### Pattern 1: Expected Errors (Recoverable)
```python
try:
    result = risky_operation()
except (ValueError, KeyError) as e:
    logger.warning(f"Expected error in {context}: {e}")
    return default_value  # or None, or {}
```

**When to use**: Known failure modes that are part of normal operation
**Examples**: Missing keys, invalid input, not found errors

### Pattern 2: Unexpected Errors (Should bubble up)
```python
try:
    result = critical_operation()
except SpecificError as e:
    logger.error(f"Failed {operation}: {e}")
    return None  # or raise, depending on criticality
except Exception as e:
    logger.error(f"Unexpected error in {context}: {e}", exc_info=True)
    raise  # Re-raise unexpected errors
```

**When to use**: Operations where unexpected failures should be visible
**Examples**: Critical system operations, initialization

### Pattern 3: Resource Cleanup (Always execute)
```python
resource = None
try:
    resource = acquire_resource()
    result = use_resource(resource)
    return result
except Exception as e:
    logger.error(f"Error using resource: {e}", exc_info=True)
    raise
finally:
    if resource:
        release_resource(resource)
```

**When to use**: File I/O, network connections, locks
**Examples**: File operations, API calls, database connections

### Pattern 4: Retry Logic
```python
from typing import Optional
import time

def with_retry(operation, max_attempts: int = 3, delay: float = 1.0) -> Optional[Any]:
    """Execute operation with exponential backoff retry."""
    for attempt in range(max_attempts):
        try:
            return operation()
        except (TimeoutError, ConnectionError) as e:
            if attempt == max_attempts - 1:
                logger.error(f"Failed after {max_attempts} attempts: {e}")
                raise
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
            time.sleep(wait_time)
```

**When to use**: Network operations, external APIs
**Examples**: API calls, file downloads, remote service calls

### Pattern 5: Context-Specific Error Messages
```python
def process_financial_data(symbol: str, data: Dict) -> Dict:
    """Process financial data with context-rich error messages."""
    try:
        validate_symbol(symbol)
        validate_data(data)
        return calculate_metrics(symbol, data)
    except ValueError as e:
        logger.error(f"Invalid data for {symbol}: {e}")
        return {"error": f"Validation failed for {symbol}", "details": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error processing {symbol}: {e}", exc_info=True)
        return {"error": f"Processing failed for {symbol}", "details": "Internal error"}
```

**When to use**: User-facing operations where context matters
**Examples**: Financial calculations, data processing, API endpoints

---

## Error Categories

### Category A: Silently Recoverable (Use Pattern 1)
- Missing optional configuration
- Cache misses
- Optional feature unavailable
- Non-critical data missing

**Logging level**: WARNING or INFO
**Action**: Return default, continue execution

### Category B: Logged Failures (Use Pattern 1 or 2)
- Invalid user input
- Data validation failures
- Expected API errors
- Known edge cases

**Logging level**: WARNING or ERROR
**Action**: Return error dict, log for debugging

### Category C: Critical Failures (Use Pattern 2)
- System initialization failures
- Required resource unavailable
- Data corruption
- Programming errors

**Logging level**: ERROR with exc_info=True
**Action**: Raise exception, halt operation

### Category D: Transient Failures (Use Pattern 4)
- Network timeouts
- Rate limits
- Temporary service unavailable
- Connection errors

**Logging level**: WARNING on retry, ERROR on final failure
**Action**: Retry with backoff, raise if exhausted

---

## Implementation Strategy

### Step 1: Create Error Handling Guide
Create `/Users/mdawson/Dawson/DawsOSB/docs/ErrorHandlingGuide.md` with:
- All 5 standard patterns
- Decision tree for which pattern to use
- Examples from actual codebase
- Common anti-patterns to avoid

### Step 2: Audit Current Error Handling (Sample Files)
Review 10-15 key files for current error handling patterns:
- dawsos/core/knowledge_graph.py
- dawsos/core/pattern_engine.py
- dawsos/core/llm_client.py
- dawsos/agents/financial_analyst.py
- dawsos/capabilities/market_data.py
- dawsos/capabilities/fred_data.py

Document current patterns and identify improvements.

### Step 3: Apply Patterns (High-Impact Areas)
Focus on high-impact areas first:
1. **Core infrastructure** (knowledge_graph, pattern_engine, llm_client)
2. **Financial calculations** (financial_analyst, analyzers)
3. **Data fetching** (capabilities/*.py)
4. **API integration** (market_data, fred_data, news)

### Step 4: Add Helper Functions
Create utility functions for common patterns:

```python
# dawsos/core/error_utils.py

import logging
import time
from typing import Any, Callable, Optional, TypeVar, Type
from functools import wraps

T = TypeVar('T')

def with_logging(operation_name: str, logger: logging.Logger):
    """Decorator for consistent error logging."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator

def safe_get(func: Callable[[], T], default: T = None,
             error_types: tuple = (Exception,),
             logger: Optional[logging.Logger] = None) -> T:
    """Safely execute function, return default on error."""
    try:
        return func()
    except error_types as e:
        if logger:
            logger.warning(f"Safe get failed: {e}")
        return default

def retry_on_failure(
    func: Callable[[], T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None
) -> T:
    """Retry function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            if attempt == max_attempts - 1:
                if logger:
                    logger.error(f"Failed after {max_attempts} attempts: {e}")
                raise
            wait_time = delay * (backoff ** attempt)
            if logger:
                logger.warning(f"Attempt {attempt + 1} failed, retry in {wait_time}s: {e}")
            time.sleep(wait_time)
```

---

## Success Criteria

1. ✅ Error handling guide created (`docs/ErrorHandlingGuide.md`)
2. ✅ Helper utilities implemented (`dawsos/core/error_utils.py`)
3. ✅ Core infrastructure using standard patterns (5-10 files)
4. ✅ All error cases have appropriate logging
5. ✅ No silent failures (all errors logged or re-raised)
6. ✅ System compiles and tests pass

---

## Execution Plan

**Time estimate**: 8-10 hours

1. **Create guide** (1 hour) - Document standards
2. **Create utilities** (1 hour) - Implement helper functions
3. **Apply to core** (3 hours) - Standardize core modules
4. **Apply to agents** (2 hours) - Standardize agent error handling
5. **Apply to capabilities** (2 hours) - Standardize data fetching
6. **Review and test** (1 hour) - Verify all changes

---

## Priority Files for Standardization

### Tier 1 (Critical - must standardize)
1. dawsos/core/knowledge_graph.py - Core data structure
2. dawsos/core/pattern_engine.py - Core execution engine
3. dawsos/core/llm_client.py - External API integration
4. dawsos/agents/financial_analyst.py - Financial calculations

### Tier 2 (Important - should standardize)
5. dawsos/capabilities/market_data.py - Market data API
6. dawsos/capabilities/fred_data.py - Economic data API
7. dawsos/capabilities/news.py - News API
8. dawsos/core/agent_runtime.py - Agent execution
9. dawsos/core/persistence.py - Data persistence

### Tier 3 (Good to have - nice to standardize)
10. Other agent files
11. Other capability files
12. UI files
13. Test files

---

## Your Task

1. **Create** ErrorHandlingGuide.md with all patterns
2. **Create** error_utils.py with helper functions
3. **Apply** standard patterns to Tier 1 files (4 critical files)
4. **Apply** standard patterns to Tier 2 files (5 important files)
5. **Test** that all files compile
6. **Report** completion with summary

Work systematically through tiers. Report after each tier completion.

**Start with Tier 1 now.**
