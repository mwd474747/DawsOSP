# Error Handling Guide

**Version**: 1.0
**Last Updated**: October 6, 2025
**Status**: Official DawsOS Standard

This guide establishes consistent error handling patterns across the DawsOS codebase.

---

## Table of Contents

1. [Standard Patterns](#standard-patterns)
2. [Decision Tree](#decision-tree)
3. [Error Categories](#error-categories)
4. [Helper Utilities](#helper-utilities)
5. [Examples from Codebase](#examples-from-codebase)
6. [Common Anti-Patterns](#common-anti-patterns)

---

## Standard Patterns

### Pattern 1: Expected Errors (Recoverable)

**Use when**: Known failure modes that are part of normal operation

**Pattern**:
```python
try:
    result = risky_operation()
except (ValueError, KeyError) as e:
    logger.warning(f"Expected error in {context}: {e}")
    return default_value  # or None, or {}
```

**Examples**:
- Missing keys in dictionaries
- Invalid user input
- Not found errors
- Cache misses

**Logging level**: WARNING or INFO
**Action**: Return default value, continue execution

---

### Pattern 2: Unexpected Errors (Should bubble up)

**Use when**: Operations where unexpected failures should be visible

**Pattern**:
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

**Examples**:
- Critical system operations
- Initialization failures
- Programming errors

**Logging level**: ERROR with exc_info=True
**Action**: Raise exception, halt operation

---

### Pattern 3: Resource Cleanup (Always execute)

**Use when**: Operations involving resources that must be released

**Pattern**:
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

**Examples**:
- File I/O operations
- Network connections
- Database connections
- Locks and semaphores

**Logging level**: ERROR with exc_info=True
**Action**: Clean up resource, then raise

**Note**: Consider using context managers (`with` statement) when possible:
```python
with open(file_path) as f:
    result = process_file(f)
```

---

### Pattern 4: Retry Logic (Transient Failures)

**Use when**: Operations that may fail temporarily

**Pattern**:
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

**Examples**:
- API calls
- Network requests
- Remote service calls
- Rate-limited operations

**Logging level**: WARNING on retry, ERROR on final failure
**Action**: Retry with exponential backoff, raise if exhausted

**Tip**: Use the `retry_on_failure()` helper from `dawsos/core/error_utils.py`

---

### Pattern 5: Context-Specific Error Messages

**Use when**: User-facing operations where context matters

**Pattern**:
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

**Examples**:
- Financial calculations
- Data processing pipelines
- API endpoints
- User-facing features

**Logging level**: ERROR with context
**Action**: Return error dict with details

---

## Decision Tree

Use this flowchart to choose the right pattern:

```
Is this error expected in normal operation?
├─ YES → Is it recoverable?
│  ├─ YES → Pattern 1 (Expected Errors)
│  └─ NO → Pattern 2 (Unexpected Errors)
└─ NO → Does it involve resources (files, network, locks)?
   ├─ YES → Pattern 3 (Resource Cleanup)
   └─ NO → Is it transient (network, API, timeout)?
      ├─ YES → Pattern 4 (Retry Logic)
      └─ NO → Does it need rich context for users?
         ├─ YES → Pattern 5 (Context-Specific)
         └─ NO → Pattern 2 (Unexpected Errors)
```

**Quick reference**:

| Situation | Pattern | Example |
|-----------|---------|---------|
| Missing optional config | 1 | `cache.get(key)` returns None |
| Invalid user input | 1 | `validate_email(email)` fails |
| System initialization | 2 | `load_required_config()` fails |
| File operation | 3 | `open(file)` needs cleanup |
| API call | 4 | `fetch_market_data()` may timeout |
| Financial calculation | 5 | `calculate_dcf(symbol)` with context |

---

## Error Categories

### Category A: Silently Recoverable

**Use Pattern 1**

**Examples**:
- Missing optional configuration
- Cache misses
- Optional feature unavailable
- Non-critical data missing

**Logging**: WARNING or INFO
**Action**: Return default, continue execution

**Code**:
```python
try:
    config = load_optional_config()
except FileNotFoundError as e:
    logger.info(f"Optional config not found, using defaults: {e}")
    config = default_config()
```

---

### Category B: Logged Failures

**Use Pattern 1 or 2**

**Examples**:
- Invalid user input
- Data validation failures
- Expected API errors
- Known edge cases

**Logging**: WARNING or ERROR
**Action**: Return error dict, log for debugging

**Code**:
```python
try:
    data = validate_input(user_input)
except ValueError as e:
    logger.warning(f"Validation failed: {e}")
    return {"error": "Invalid input", "details": str(e)}
```

---

### Category C: Critical Failures

**Use Pattern 2**

**Examples**:
- System initialization failures
- Required resource unavailable
- Data corruption
- Programming errors

**Logging**: ERROR with exc_info=True
**Action**: Raise exception, halt operation

**Code**:
```python
try:
    graph = initialize_knowledge_graph()
except Exception as e:
    logger.error(f"Critical: Failed to initialize knowledge graph: {e}", exc_info=True)
    raise
```

---

### Category D: Transient Failures

**Use Pattern 4**

**Examples**:
- Network timeouts
- Rate limits
- Temporary service unavailable
- Connection errors

**Logging**: WARNING on retry, ERROR on final failure
**Action**: Retry with backoff, raise if exhausted

**Code**:
```python
from dawsos.core.error_utils import retry_on_failure

data = retry_on_failure(
    lambda: fetch_market_data(symbol),
    max_attempts=3,
    exceptions=(TimeoutError, ConnectionError),
    logger=logger
)
```

---

## Helper Utilities

DawsOS provides helper functions in `dawsos/core/error_utils.py`:

### 1. `with_logging()` Decorator

**Use**: Automatic error logging for any function

**Example**:
```python
from dawsos.core.error_utils import with_logging

@with_logging("calculate_metrics", logger)
def calculate_metrics(data):
    # Any exception will be logged with context
    return process(data)
```

---

### 2. `safe_get()` Function

**Use**: Recoverable operations with default fallback

**Example**:
```python
from dawsos.core.error_utils import safe_get

# Returns None if fetch fails
data = safe_get(
    lambda: fetch_data(symbol),
    default=None,
    error_types=(ValueError, KeyError),
    logger=logger
)
```

---

### 3. `retry_on_failure()` Function

**Use**: Network operations with automatic retry

**Example**:
```python
from dawsos.core.error_utils import retry_on_failure

# Retries up to 3 times with exponential backoff
result = retry_on_failure(
    lambda: api_call(endpoint),
    max_attempts=3,
    delay=1.0,
    backoff=2.0,
    exceptions=(TimeoutError, ConnectionError),
    logger=logger
)
```

---

## Examples from Codebase

### Example 1: Knowledge Graph (Pattern 1 + 3)

```python
# dawsos/core/knowledge_graph.py

def get_node(self, node_id: str) -> Optional[Dict]:
    """Safely get node with error handling."""
    try:
        # Pattern 1: Expected error - node may not exist
        if node_id not in self.nodes:
            logger.warning(f"Node not found: {node_id}")
            return None
        return self.nodes[node_id]
    except Exception as e:
        logger.error(f"Unexpected error getting node {node_id}: {e}", exc_info=True)
        return None
```

---

### Example 2: LLM Client (Pattern 4 + 3)

```python
# dawsos/core/llm_client.py

def call_with_retry(self, prompt: str) -> str:
    """Call LLM with retry logic."""
    def make_call():
        # Pattern 3: Resource cleanup for API connection
        try:
            response = self.client.create(prompt=prompt)
            return response.text
        except Exception as e:
            logger.error(f"API call failed: {e}", exc_info=True)
            raise

    # Pattern 4: Retry transient failures
    return retry_on_failure(
        make_call,
        max_attempts=3,
        exceptions=(TimeoutError, ConnectionError),
        logger=logger
    )
```

---

### Example 3: Financial Analyst (Pattern 5)

```python
# dawsos/agents/financial_analyst.py

def calculate_dcf(self, symbol: str, financials: Dict) -> Dict:
    """Calculate DCF with context-rich errors."""
    try:
        validate_financials(financials)
        fcf = calculate_free_cash_flow(financials)
        discount_rate = estimate_wacc(financials)
        terminal_value = calculate_terminal_value(fcf, discount_rate)
        return {"dcf_value": terminal_value, "symbol": symbol}
    except ValueError as e:
        logger.error(f"Invalid financials for {symbol}: {e}")
        return {
            "error": f"DCF calculation failed for {symbol}",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in DCF for {symbol}: {e}", exc_info=True)
        return {
            "error": f"Internal error calculating DCF for {symbol}",
            "details": "Please contact support"
        }
```

---

### Example 4: Market Data (Pattern 4)

```python
# dawsos/capabilities/market_data.py

def fetch_quote(self, symbol: str) -> Optional[Dict]:
    """Fetch quote with retry logic."""
    return retry_on_failure(
        lambda: self._fetch_quote_internal(symbol),
        max_attempts=3,
        delay=1.0,
        exceptions=(TimeoutError, ConnectionError),
        logger=logger
    )
```

---

## Common Anti-Patterns

### Anti-Pattern 1: Bare `except`

**Bad**:
```python
try:
    result = risky_operation()
except:
    pass
```

**Why**: Silently swallows all errors including KeyboardInterrupt

**Fix**:
```python
try:
    result = risky_operation()
except (ValueError, KeyError) as e:
    logger.warning(f"Expected error: {e}")
    result = None
```

---

### Anti-Pattern 2: `except Exception: pass`

**Bad**:
```python
try:
    result = risky_operation()
except Exception:
    pass
```

**Why**: No logging, debugging is impossible

**Fix**:
```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

---

### Anti-Pattern 3: Logging without Context

**Bad**:
```python
except Exception as e:
    logger.error(f"Error: {e}")
```

**Why**: Doesn't include stack trace or operation context

**Fix**:
```python
except Exception as e:
    logger.error(f"Failed to process {symbol}: {e}", exc_info=True)
```

---

### Anti-Pattern 4: Missing Resource Cleanup

**Bad**:
```python
f = open(file_path)
result = process_file(f)
f.close()  # Never executes if process_file() raises
```

**Why**: Resource leak if exception occurs

**Fix**:
```python
with open(file_path) as f:
    result = process_file(f)
# OR
f = None
try:
    f = open(file_path)
    result = process_file(f)
finally:
    if f:
        f.close()
```

---

### Anti-Pattern 5: Retrying Non-Transient Errors

**Bad**:
```python
for _ in range(3):
    try:
        result = calculate(data)
        break
    except ValueError:
        time.sleep(1)  # Retrying a logic error won't help
```

**Why**: Logic errors won't be fixed by retrying

**Fix**:
```python
# Only retry transient errors
result = retry_on_failure(
    lambda: api_call(endpoint),
    exceptions=(TimeoutError, ConnectionError),  # Not ValueError
    logger=logger
)
```

---

### Anti-Pattern 6: Too Broad Exception Handling

**Bad**:
```python
try:
    validate_input(data)
    process_data(data)
    save_results(results)
except Exception as e:
    logger.error(f"Something failed: {e}")
```

**Why**: Can't tell which operation failed

**Fix**:
```python
try:
    validate_input(data)
except ValueError as e:
    logger.error(f"Validation failed: {e}")
    return {"error": "Invalid input"}

try:
    processed = process_data(data)
except Exception as e:
    logger.error(f"Processing failed: {e}", exc_info=True)
    raise

try:
    save_results(processed)
except IOError as e:
    logger.error(f"Save failed: {e}")
    raise
```

---

## Best Practices Summary

1. **Be Specific**: Catch specific exceptions, not `Exception`
2. **Always Log**: Every error should be logged with context
3. **Include Stack Traces**: Use `exc_info=True` for unexpected errors
4. **Clean Up Resources**: Use `finally` or context managers
5. **Retry Smartly**: Only retry transient failures
6. **Provide Context**: Include operation details in error messages
7. **Use Helpers**: Leverage `error_utils.py` for common patterns
8. **Test Error Paths**: Write tests for error conditions
9. **Document Errors**: Explain what errors mean in docstrings
10. **Fail Fast**: Don't hide critical errors

---

## Checklist for Code Review

When reviewing error handling in pull requests, verify:

- [ ] No bare `except:` or `except Exception: pass`
- [ ] All errors are logged with appropriate level
- [ ] Specific exceptions caught, not broad `Exception`
- [ ] Resources cleaned up in `finally` blocks
- [ ] Network operations use retry logic
- [ ] Error messages include context (symbol, operation, etc.)
- [ ] Critical errors raise with `exc_info=True`
- [ ] Expected errors return sensible defaults
- [ ] User-facing errors have helpful messages
- [ ] Tests cover error conditions

---

**Version History**:
- v1.0 (2025-10-06): Initial guide with 5 standard patterns
