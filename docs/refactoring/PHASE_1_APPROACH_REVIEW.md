# Phase 1: Exception Handling - Approach Review

**Date:** January 15, 2025  
**Status:** 🔍 REVIEW COMPLETE  
**Purpose:** Review and validate the exception handling approach

---

## Executive Summary

After reviewing the changes made so far, the approach is **sound but can be improved**. The current pattern of distinguishing programming errors from service/database errors is correct, but we should:

1. **Use specific exception types** where possible (asyncpg.PostgresError, httpx.HTTPError, etc.)
2. **Keep the programming error distinction** (ValueError, TypeError, KeyError, AttributeError)
3. **Consider using the exception hierarchy** we created for better error messages
4. **Review edge cases** where the pattern might not apply

---

## Current Approach Review

### Pattern Applied

```python
# Before:
except Exception as e:
    logger.error(f"Failed: {e}")
    return None

# After:
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except Exception as e:
    # Service/database errors - handle gracefully
    logger.error(f"Failed: {e}")
    return None
```

### Strengths

1. ✅ **Programming errors surface immediately** - Bugs are caught early
2. ✅ **Service errors handled gracefully** - Application continues to work
3. ✅ **Better debugging** - `exc_info=True` for programming errors
4. ✅ **Consistent pattern** - Easy to apply across codebase

### Potential Issues

1. ⚠️ **Too broad for service errors** - Still catching all exceptions
2. ⚠️ **Missing specific exception types** - Not catching asyncpg.PostgresError, httpx.HTTPError, etc.
3. ⚠️ **Exception hierarchy not used** - Created but not integrated
4. ⚠️ **Some cases might need different handling** - API errors vs database errors

---

## Improved Approach

### Option 1: Use Specific Exception Types (Recommended)

```python
try:
    row = await self.execute_query_one(query, series_id, asof_date)
    # ...
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except asyncpg.PostgresError as e:
    # Database errors - handle gracefully
    logger.error(f"Database error: {e}")
    return None
except Exception as e:
    # Other unexpected errors - log and handle
    logger.error(f"Unexpected error: {e}")
    return None
```

**Pros:**
- More specific error handling
- Better error messages
- Can distinguish database vs API vs other errors

**Cons:**
- Requires importing exception types
- More verbose
- Need to know which exceptions each library raises

### Option 2: Use Exception Hierarchy (Future Improvement)

```python
from app.core.exceptions import DatabaseError, APIError, ValidationError

try:
    row = await self.execute_query_one(query, series_id, asof_date)
    # ...
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except DatabaseError as e:
    # Database errors - handle gracefully
    logger.error(f"Database error: {e}")
    return None
except APIError as e:
    # API errors - handle gracefully
    logger.error(f"API error: {e}")
    return None
except Exception as e:
    # Other unexpected errors - log and handle
    logger.error(f"Unexpected error: {e}")
    return None
```

**Pros:**
- Cleaner error handling
- Better error messages
- Can add retry logic based on error type

**Cons:**
- Requires wrapping exceptions in our hierarchy
- More work upfront
- Can be done in Phase 2

### Option 3: Current Approach (Simplified)

```python
try:
    row = await self.execute_query_one(query, series_id, asof_date)
    # ...
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except Exception as e:
    # Service/database errors - handle gracefully
    logger.error(f"Failed: {e}")
    return None
```

**Pros:**
- Simple and consistent
- Easy to apply
- Works for most cases

**Cons:**
- Still too broad for service errors
- Can't distinguish database vs API errors
- Less informative error messages

---

## Recommendation

**Use Option 1 (Specific Exception Types) for critical paths**, and **Option 3 (Current Approach) for non-critical paths**.

### Critical Paths (Use Option 1)
- Database queries (asyncpg.PostgresError)
- External API calls (httpx.HTTPError, httpx.TimeoutError)
- Pattern execution (specific exceptions)
- Agent runtime (specific exceptions)

### Non-Critical Paths (Use Option 3)
- Alert evaluation (graceful degradation)
- Data fetching (return None on error)
- Logging/audit (best-effort)

---

## Validation of Current Changes

### ✅ Good Changes

1. **alerts.py** - Correctly distinguishes programming errors from service errors
2. **scenarios.py** - Already had good pattern, we improved it
3. **financial_analyst.py** - Good distinction between errors
4. **data_harvester.py** - Good for API error handling
5. **macro_hound.py** - Good error handling
6. **pattern_orchestrator.py** - Good for validation errors
7. **agent_runtime.py** - **CRITICAL FIX** - Programming errors no longer retried
8. **executor.py** - Good for API error handling

### ⚠️ Areas for Improvement

1. **Database queries** - Should catch `asyncpg.PostgresError` specifically
2. **API calls** - Should catch `httpx.HTTPError`, `httpx.TimeoutError` specifically
3. **Exception hierarchy** - Should be used in Phase 2

---

## Revised Approach for Remaining Work

### For Database Operations

```python
try:
    row = await self.execute_query_one(query, series_id, asof_date)
    # ...
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except asyncpg.PostgresError as e:
    # Database errors - handle gracefully
    logger.error(f"Database error: {e}")
    return None
except Exception as e:
    # Other unexpected errors - log and handle
    logger.error(f"Unexpected error: {e}")
    return None
```

### For API Operations

```python
try:
    result = await provider.fetch_data(symbol)
    # ...
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except (httpx.HTTPError, httpx.TimeoutError) as e:
    # API errors - handle gracefully
    logger.error(f"API error: {e}")
    return {"error": str(e)}
except Exception as e:
    # Other unexpected errors - log and handle
    logger.error(f"Unexpected error: {e}")
    return {"error": str(e)}
```

### For Non-Critical Operations

```python
try:
    # Non-critical operation
    # ...
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise immediately
    logger.error(f"Programming error: {e}", exc_info=True)
    raise
except Exception as e:
    # Service errors - handle gracefully (current approach is fine)
    logger.error(f"Failed: {e}")
    return None
```

---

## Next Steps

1. ✅ **Review complete** - Approach validated
2. ⏳ **Continue with remaining work** - Apply improved approach
3. ⏳ **Use specific exceptions** for database and API operations
4. ⏳ **Keep current approach** for non-critical operations

---

## Conclusion

**Current approach is good, but can be improved by:**
1. Using specific exception types (asyncpg.PostgresError, httpx.HTTPError) for critical paths
2. Keeping the programming error distinction (already done)
3. Using exception hierarchy in Phase 2 (future improvement)

**The changes made so far are correct and improve the codebase.** The remaining work should use the improved approach for database and API operations.

---

**Status:** ✅ APPROACH VALIDATED  
**Last Updated:** January 15, 2025  
**Next Step:** Continue with remaining work using improved approach

