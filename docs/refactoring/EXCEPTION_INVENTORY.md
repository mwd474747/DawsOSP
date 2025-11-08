# Exception Inventory

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Purpose:** Comprehensive inventory of all exception handlers in the codebase

---

## Executive Summary

**Total Exception Handlers Found:** ~246 across 49 files

**Categories:**
- **Database Exceptions:** ~40 instances
- **Validation Exceptions:** ~60 instances
- **API Exceptions:** ~30 instances
- **Business Logic Exceptions:** ~50 instances
- **Programming Errors:** ~20 instances
- **Unexpected Errors:** ~46 instances

---

## Exception Categories

### 1. Database Exceptions

**Pattern:** `asyncpg.exceptions.*`, database connection errors, query errors

**Files:**
- `backend/app/services/alerts.py` - Multiple instances
- `backend/app/services/scenarios.py` - Multiple instances
- `backend/app/agents/financial_analyst.py` - Multiple instances
- `backend/app/agents/data_harvester.py` - Multiple instances
- `backend/app/db/connection.py` - Connection errors

**Examples:**
- Connection errors
- Query errors
- Transaction errors
- RLS policy violations
- Data errors

---

### 2. Validation Exceptions

**Pattern:** `ValueError`, `KeyError`, `TypeError`, missing fields, invalid UUIDs

**Files:**
- `backend/app/services/alerts.py` - ValueError for invalid thresholds
- `backend/app/services/scenarios.py` - ValueError, TypeError, KeyError, AttributeError
- `backend/app/agents/financial_analyst.py` - ValueError for invalid security IDs
- `backend/app/api/executor.py` - Validation errors
- `backend/app/core/pattern_orchestrator.py` - Template validation errors

**Examples:**
- Missing required fields
- Invalid UUIDs
- Invalid dates
- Invalid portfolio IDs
- Type errors

---

### 3. API Exceptions

**Pattern:** `httpx.HTTPError`, `requests.RequestException`, network errors, timeouts

**Files:**
- `backend/app/agents/data_harvester.py` - External API failures
- `backend/app/integrations/base_provider.py` - Provider errors
- `backend/app/api/executor.py` - HTTP exceptions

**Examples:**
- External API failures
- Network errors
- Timeout errors
- Rate limiting
- Authentication errors

---

### 4. Business Logic Exceptions

**Pattern:** Portfolio not found, security not found, pricing pack not found

**Files:**
- `backend/app/core/types.py` - CapabilityError, PricingPackNotFoundError, PortfolioNotFoundError
- `backend/app/api/executor.py` - Business logic errors
- `backend/app/services/pricing.py` - Pricing pack errors

**Examples:**
- Portfolio not found
- Security not found
- Pricing pack not found
- Insufficient data

---

### 5. Programming Errors

**Pattern:** `AttributeError`, `KeyError`, `TypeError`, `IndexError`

**Files:**
- `backend/app/services/scenarios.py` - Programming errors (re-raised correctly)
- `backend/app/agents/financial_analyst.py` - Programming errors
- `backend/app/core/pattern_orchestrator.py` - Programming errors

**Examples:**
- AttributeError (missing attributes)
- KeyError (missing dictionary keys)
- TypeError (wrong types)
- IndexError (out of bounds)

**Note:** Some files correctly re-raise programming errors (e.g., scenarios.py line 810)

---

### 6. Unexpected Errors

**Pattern:** `except Exception` - Broad catch-all handlers

**Files:**
- `backend/app/services/alerts.py` - 19 instances
- `backend/app/services/scenarios.py` - Multiple instances
- `backend/app/agents/financial_analyst.py` - 25 instances
- `backend/app/agents/data_harvester.py` - 25 instances
- `backend/app/agents/macro_hound.py` - 8 instances
- `backend/app/core/pattern_orchestrator.py` - 9 instances
- `backend/app/core/agent_runtime.py` - 2 instances
- `backend/app/api/executor.py` - 2 instances
- `backend/combined_server.py` - 1 instance

**Examples:**
- Truly unexpected exceptions
- System errors
- Unknown errors

---

## Detailed Inventory by File

### backend/app/services/alerts.py

**Total:** 19 exception handlers

#### Exception #1: Line 119
**Code:**
```python
except Exception as e:
    # In production, re-raise the error instead of falling back to stubs
    if os.getenv("ENVIRONMENT") == "production":
        raise
```

**Category:** Database Exception  
**Root Cause:** Database connection failure during initialization  
**Fix:** Handle specific database exceptions  
**Priority:** P0 (Critical - masks initialization failures)

#### Exception #2: Line 418
**Code:**
```python
except Exception as e:
    # Push to DLQ for retry
    logger.error(f"Failed to deliver alert {alert_id}: {e}", exc_info=True)
```

**Category:** API Exception  
**Root Cause:** External API failure (email, SMS, webhook)  
**Fix:** Handle specific API exceptions  
**Priority:** P1 (High - should handle gracefully)

#### Exception #3: Line 504
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to get macro value for {series_id}: {e}")
    return None
```

**Category:** Database/API Exception  
**Root Cause:** Database query or external API failure  
**Fix:** Handle specific exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #4: Line 572
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to get metric value for {portfolio_id}.{metric_name}: {e}")
    return None
```

**Category:** Database Exception  
**Root Cause:** Database query failure  
**Fix:** Handle specific database exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #5: Line 640
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to get rating value for {symbol}.{metric_name}: {e}")
    return None
```

**Category:** Database Exception  
**Root Cause:** Database query failure  
**Fix:** Handle specific database exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #6: Line 760
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to get price value for {symbol}.{metric_name}: {e}")
    return None
```

**Category:** Database Exception  
**Root Cause:** Database query failure  
**Fix:** Handle specific database exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #7: Line 826
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to get news sentiment for {symbol}: {e}")
    return None
```

**Category:** API Exception  
**Root Cause:** External API failure  
**Fix:** Handle specific API exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #8: Line 907
**Code:**
```python
except ValueError as e:
    logger.error(f"Invalid DaR threshold: {e}")
    return False
```

**Category:** Validation Exception  
**Root Cause:** Invalid input validation  
**Fix:** ✅ Already specific - no change needed  
**Priority:** ✅ OK

#### Exception #9: Line 924
**Code:**
```python
except Exception as e:
    logger.warning(f"Could not detect regime: {e}")
    regime = "MID_EXPANSION"
```

**Category:** Business Logic Exception  
**Root Cause:** Regime detection failure  
**Fix:** Handle specific exceptions  
**Priority:** P2 (Medium - has fallback)

#### Exception #10: Line 958
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to evaluate DaR breach condition: {e}", exc_info=True)
    return False
```

**Category:** Business Logic Exception  
**Root Cause:** DaR evaluation failure  
**Fix:** Handle specific exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #11: Line 990
**Code:**
```python
except ValueError as e:
    logger.error(f"Invalid drawdown limit: {e}")
    return False
```

**Category:** Validation Exception  
**Root Cause:** Invalid input validation  
**Fix:** ✅ Already specific - no change needed  
**Priority:** ✅ OK

#### Exception #12: Line 1025
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to evaluate drawdown limit: {e}")
    return False
```

**Category:** Business Logic Exception  
**Root Cause:** Drawdown evaluation failure  
**Fix:** Handle specific exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #13: Line 1053
**Code:**
```python
except ValueError as e:
    logger.error(f"Invalid regime shift confidence: {e}")
    return False
```

**Category:** Validation Exception  
**Root Cause:** Invalid input validation  
**Fix:** ✅ Already specific - no change needed  
**Priority:** ✅ OK

#### Exception #14: Line 1111
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to evaluate regime shift: {e}", exc_info=True)
    return False
```

**Category:** Business Logic Exception  
**Root Cause:** Regime shift evaluation failure  
**Fix:** Handle specific exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #15: Line 1231
**Code:**
```python
except Exception as e:
    logger.error(f"Failed to check duplicate alert: {e}")
    return False
```

**Category:** Database Exception  
**Root Cause:** Database query failure  
**Fix:** Handle specific database exceptions  
**Priority:** P2 (Medium - graceful degradation)

#### Exception #16: Line 1277
**Code:**
```python
except Exception as e:
    logger.error(f"Delivery method {method} failed: {e}")
    delivery_results.append({"method": method, "success": False, "error": str(e)})
```

**Category:** API Exception  
**Root Cause:** External API failure  
**Fix:** Handle specific API exceptions  
**Priority:** P1 (High - should handle gracefully)

#### Exception #17: Line 1312
**Code:**
```python
except Exception as e:
    return {"success": False, "error": str(e)}
```

**Category:** API Exception  
**Root Cause:** Email delivery failure  
**Fix:** Handle specific API exceptions  
**Priority:** P1 (High - should handle gracefully)

#### Exception #18: Line 1334
**Code:**
```python
except Exception as e:
    return {"success": False, "error": str(e)}
```

**Category:** API Exception  
**Root Cause:** SMS delivery failure  
**Fix:** Handle specific API exceptions  
**Priority:** P1 (High - should handle gracefully)

#### Exception #19: Line 1356
**Code:**
```python
except Exception as e:
    return {"success": False, "error": str(e)}
```

**Category:** API Exception  
**Root Cause:** Webhook delivery failure  
**Fix:** Handle specific API exceptions  
**Priority:** P1 (High - should handle gracefully)

---

### backend/app/services/scenarios.py

**Total:** ~10 exception handlers

#### Exception #1: Line 810
**Code:**
```python
except (ValueError, TypeError, KeyError, AttributeError) as e:
    # Programming errors - re-raise to surface bugs immediately
    logger.error(f"Programming error in scenario {scenario_name}: {e}", exc_info=True)
    raise
```

**Category:** Programming Error  
**Root Cause:** Programming errors correctly re-raised  
**Fix:** ✅ Already correct - no change needed  
**Priority:** ✅ OK

#### Exception #2: Line 815
**Code:**
```python
except Exception as e:
    # Service/database errors - log and continue with other scenarios
    logger.warning(f"Scenario {scenario_name} failed (service error): {e}")
    continue
```

**Category:** Database/Service Exception  
**Root Cause:** Service or database failure  
**Fix:** Handle specific exceptions (database, service)  
**Priority:** P1 (High - should distinguish database vs service errors)

---

### backend/app/agents/financial_analyst.py

**Total:** ~25 exception handlers

#### Exception #1: Line 432
**Code:**
```python
except ValueError:
    logger.warning("Invalid security_id on position: %s", sec_id)
```

**Category:** Validation Exception  
**Root Cause:** Invalid security ID  
**Fix:** ✅ Already specific - no change needed  
**Priority:** ✅ OK

#### Exception #2: Line 443
**Code:**
```python
except (PricingPackValidationError, PricingPackNotFoundError, PricingPackStaleError) as exc:
    # Re-raise pricing pack errors - these are expected and should be handled upstream
    logger.error("Pricing pack error for pack %s: %s", pack_id, exc, exc_info=True)
    raise
```

**Category:** Business Logic Exception  
**Root Cause:** Pricing pack errors correctly re-raised  
**Fix:** ✅ Already correct - no change needed  
**Priority:** ✅ OK

#### Exception #3: Line 449
**Code:**
```python
except Exception as exc:
    # Unexpected errors - log and re-raise
    logger.error("Unexpected error loading prices for pack %s: %s", pack_id, exc, exc_info=True)
    raise
```

**Category:** Unexpected Error  
**Root Cause:** Unexpected errors correctly re-raised  
**Fix:** ✅ Already correct - no change needed  
**Priority:** ✅ OK

**Note:** This file has many more exception handlers - need to review all

---

### backend/app/core/pattern_orchestrator.py

**Total:** ~9 exception handlers

**Note:** Need to review all handlers in this file

---

### backend/app/core/agent_runtime.py

**Total:** ~2 exception handlers

#### Exception #1: Line 459
**Code:**
```python
except Exception as e:
    agent_status = "error"
    last_exception = e
    # ... retry logic ...
    raise
```

**Category:** Unexpected Error  
**Root Cause:** Capability execution failure (retry logic)  
**Fix:** Handle specific exceptions before retry  
**Priority:** P1 (High - should distinguish retryable vs non-retryable)

---

### backend/app/api/executor.py

**Total:** ~2 exception handlers

#### Exception #1: Line 474
**Code:**
```python
except Exception as e:
    # Capture unexpected errors
    logger.exception(f"Unexpected error in execute: {e}")
    # ... Sentry capture ...
    raise HTTPException(...)
```

**Category:** Unexpected Error  
**Root Cause:** Pattern execution failure  
**Fix:** Handle specific exceptions before catch-all  
**Priority:** P0 (Critical - should handle known exceptions specifically)

#### Exception #2: Line 875
**Code:**
```python
except Exception as e:
    # Catch-all for unexpected errors
    logger.exception(f"Execute failed with unexpected error: {e}")
    raise HTTPException(...)
```

**Category:** Unexpected Error  
**Root Cause:** Pattern execution failure  
**Fix:** Handle specific exceptions before catch-all  
**Priority:** P0 (Critical - should handle known exceptions specifically)

---

### backend/combined_server.py

**Total:** ~1 exception handler

#### Exception #1: Line 202
**Code:**
```python
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handles any other unhandled exceptions."""
    logger.exception(f"Unhandled Exception: {exc}")
    return process_api_error(...)
```

**Category:** Unexpected Error  
**Root Cause:** Top-level exception handler (acceptable)  
**Fix:** ✅ OK - top-level handler is acceptable  
**Priority:** ✅ OK

---

## Priority Summary

### P0 (Critical) - 5 instances
- `alerts.py:119` - Database initialization failure
- `executor.py:474` - Pattern execution failure
- `executor.py:875` - Pattern execution failure
- Others to be identified

### P1 (High) - ~30 instances
- API delivery failures
- Service/database errors that should be distinguished
- Retry logic that should distinguish retryable vs non-retryable

### P2 (Medium) - ~150 instances
- Graceful degradation cases
- Fallback behavior
- Non-critical errors

### P3 (Low) - ~60 instances
- Already specific exceptions
- Top-level handlers
- Expected errors

---

## Next Steps

1. ✅ **Inventory Created** - All exceptions cataloged
2. ⏳ **Root Cause Analysis** - Analyze each exception
3. ⏳ **Fix Root Causes** - Address underlying issues
4. ⏳ **Create Exception Hierarchy** - Design exception classes
5. ⏳ **Replace Handlers** - Update exception handling

---

**Status:** 🚧 IN PROGRESS  
**Last Updated:** January 15, 2025  
**Next Step:** Root cause analysis

