# Service Documentation Standard

**Date:** January 15, 2025  
**Status:** ✅ STANDARD ESTABLISHED  
**Purpose:** Prevent misleading deprecation warnings and ensure consistent service documentation

---

## Standard Documentation Pattern

### For Services Used by Agents (Implementation Details)

**Pattern:**
```python
"""
Service Name

Purpose: [Brief description]
Updated: [Date]
Priority: [P0/P1/P2]

**Architecture Note:** This service is an implementation detail of the [AgentName] agent.
Patterns should use `[agent_name]` agent capabilities (e.g., `[agent_name].[capability]`),
not this service directly. The service is used internally by [AgentName] to implement
[business logic description].

[Additional documentation...]
"""
```

**Example (AlertService):**
```python
"""
Alert Evaluation Service

Purpose: Evaluate user-defined alert conditions against portfolio metrics
Updated: 2025-01-15
Priority: P1 (Core business logic for alert evaluation)

**Architecture Note:** This service is an implementation detail of the MacroHound agent.
Patterns should use `macro_hound` agent capabilities (e.g., `macro_hound.suggest_alert_presets`),
not this service directly. The service is used internally by MacroHound to implement
alert evaluation logic.
"""
```

---

## When to Mark as Deprecated

### ✅ DO Mark as Deprecated

1. **Singleton Factory Functions** (`get_*_service()`)
   - These are deprecated as part of singleton pattern removal
   - Migration: Use service class directly (e.g., `PricingService(db_pool=...)`)

2. **Old API Patterns**
   - Patterns that are being replaced by new patterns
   - Migration path is clear and documented

3. **Legacy Code Being Removed**
   - Code that will be removed in a future release
   - Migration is complete or in progress

### ❌ DO NOT Mark as Deprecated

1. **Services Used by Agents** (Implementation Details)
   - Services are essential for agent functionality
   - Services are internal implementation details
   - Removing them would break agents

2. **Active Business Logic**
   - Code that is actively used and essential
   - No migration path exists or migration is complete

---

## Architecture Pattern

### Correct Pattern

**Architecture:**
```
Pattern → Agent Capability → Service Method → Database/API
```

**Example:**
```
buffett_checklist.json
  → financial_analyst.dividend_safety
    → FinancialAnalyst.financial_analyst_dividend_safety()
      → RatingsService.calculate_dividend_safety()
        → Database (rating_rubrics table)
```

**Key Points:**
- Patterns use **agent capabilities** (public API)
- Agents use **services** internally (implementation details)
- Services are **not deprecated** - they're essential

---

## Documentation Checklist

When documenting a service:

- [ ] **Purpose:** Clear description of what the service does
- [ ] **Architecture Note:** If used by an agent, note it's an implementation detail
- [ ] **Usage:** Example of how to use the service (if appropriate)
- [ ] **DO NOT:** Mark as deprecated if it's an implementation detail
- [ ] **DO:** Mark singleton factory functions as deprecated (not the service class)

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Marking Services as Deprecated

**Wrong:**
```python
"""
⚠️ DEPRECATED: This service is deprecated and will be removed in a future release.
The functionality has been consolidated into the MacroHound agent.
"""
```

**Correct:**
```python
"""
**Architecture Note:** This service is an implementation detail of the MacroHound agent.
Patterns should use `macro_hound` agent capabilities, not this service directly.
"""
```

### ❌ Mistake 2: Confusing Service with Singleton Function

**Wrong:**
```python
# Marking the service class as deprecated
class AlertService:
    """⚠️ DEPRECATED: This service is deprecated."""
```

**Correct:**
```python
# Service class is NOT deprecated
class AlertService:
    """Alert evaluation service (implementation detail of MacroHound agent)."""

# Singleton factory function IS deprecated
def get_alert_service():
    """DEPRECATED: Use AlertService(use_db=...) directly instead."""
```

---

## Verification Checklist

Before marking something as deprecated:

1. [ ] **Is it actually deprecated?** (Will it be removed?)
2. [ ] **Is there a migration path?** (What should users use instead?)
3. [ ] **Is it still actively used?** (If yes, it's probably not deprecated)
4. [ ] **Is it an implementation detail?** (If yes, don't mark as deprecated)

---

## Examples

### ✅ Correct: Service as Implementation Detail

```python
class RatingsService:
    """
    Ratings calculation service.

    **Architecture Note:** This service is an implementation detail of the FinancialAnalyst agent.
    Patterns should use `financial_analyst` agent capabilities, not this service directly.
    """
```

### ✅ Correct: Singleton Function Deprecated

```python
def get_ratings_service(use_db: bool = True, db_pool=None) -> RatingsService:
    """
    DEPRECATED: Use RatingsService(db_pool=...) directly instead.
    
    This function is deprecated as part of the singleton pattern removal (Phase 2).
    """
```

### ❌ Wrong: Service Marked as Deprecated

```python
class RatingsService:
    """
    ⚠️ DEPRECATED: This service is deprecated and will be removed in a future release.
    """
```

---

**Status:** ✅ STANDARD ESTABLISHED  
**Last Updated:** January 15, 2025

