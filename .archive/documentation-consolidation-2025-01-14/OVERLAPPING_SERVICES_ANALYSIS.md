# Overlapping Services Analysis

**Date:** January 14, 2025  
**Status:** ✅ **ANALYSIS COMPLETE**  
**Purpose:** Analyze overlapping services to determine if they are duplicates or serve different purposes

---

## Executive Summary

**Finding:** The services are **NOT duplicates** - they serve **complementary purposes** with clear separation of concerns.

**Services Analyzed:**
1. `ScenarioService` vs `MacroAwareScenarioService` - ✅ **Complementary** (composition pattern)
2. `AlertService` vs `AlertDeliveryService` - ✅ **Complementary** (composition pattern)

---

## 1. ScenarioService vs MacroAwareScenarioService

### ScenarioService
**Purpose:** Basic scenario stress testing  
**Location:** `backend/app/services/scenarios.py`  
**Responsibilities:**
- Apply static macro shocks to portfolio positions
- Compute delta P&L from factor exposures
- Rank winners and losers by impact
- Suggest hedge ideas based on scenario type
- Pre-defined scenario library (rates, USD, CPI, etc.)

**Usage:**
```python
from app.services.scenarios import ScenarioService

service = ScenarioService()
result = await service.apply_scenario(
    portfolio_id="...",
    shock_type=ShockType.RATES_UP,
    pack_id="...",
)
```

**Key Features:**
- Static scenario definitions
- Direct shock application
- No macro regime awareness

---

### MacroAwareScenarioService
**Purpose:** Enhanced scenario analysis with macro regime awareness  
**Location:** `backend/app/services/macro_aware_scenarios.py`  
**Responsibilities:**
- Wraps `ScenarioService` (composition pattern)
- Detects current macro regime
- Adjusts scenario probabilities based on regime
- Adjusts scenario severity based on regime
- Adds regime-specific additional shocks
- Provides macro context in results

**Usage:**
```python
from app.services.macro_aware_scenarios import MacroAwareScenarioService

service = MacroAwareScenarioService()
result = await service.apply_macro_aware_scenario(
    portfolio_id="...",
    shock_type=ShockType.RATES_UP,
    pack_id="...",
)
```

**Key Features:**
- Dynamic scenario adjustments
- Regime-aware probability multipliers
- Regime-aware severity multipliers
- Additional shocks based on regime
- Uses `ScenarioService` internally

---

### Relationship
**Pattern:** **Composition** (not duplication)

```
MacroAwareScenarioService
  └── uses ScenarioService (wraps it)
  └── uses MacroService (for regime detection)
```

**Example:**
- `ScenarioService`: "Apply +100bp rate shock" (static)
- `MacroAwareScenarioService`: "Apply +100bp rate shock, but if we're in LATE_EXPANSION regime, multiply probability by 2.0 and severity by 1.3" (dynamic)

---

### Recommendation
✅ **KEEP BOTH** - They serve different purposes:
- Use `ScenarioService` for basic static scenario analysis
- Use `MacroAwareScenarioService` for regime-aware dynamic scenario analysis
- `MacroAwareScenarioService` is an enhancement layer, not a duplicate

**Current Usage:**
- `ScenarioService`: Used directly in `macro_hound.py` for basic scenarios
- `MacroAwareScenarioService`: Used in `macro_hound.py` for deleveraging scenarios (needs regime awareness)

---

## 2. AlertService vs AlertDeliveryService

### AlertService
**Purpose:** Alert condition evaluation  
**Location:** `backend/app/services/alerts.py`  
**Responsibilities:**
- Evaluate user-defined alert conditions
- Check if conditions are met (macro, metric, rating, price, news_sentiment)
- Enforce cooldown periods (prevent notification spam)
- Retrieve values from database
- Support multiple operators (>, <, >=, <=, ==, !=)
- Determine if alert should trigger

**Usage:**
```python
from app.services.alerts import AlertService

service = AlertService()
result = await service.evaluate_condition(condition, ctx)
should_trigger = await service.should_trigger(alert, ctx)
```

**Key Features:**
- Condition evaluation logic
- Cooldown enforcement
- Value retrieval from database
- Operator support

---

### AlertDeliveryService
**Purpose:** Alert delivery tracking and DLQ management  
**Location:** `backend/app/services/alert_delivery.py`  
**Responsibilities:**
- Track successful alert deliveries
- Content-based deduplication (MD5 hash)
- DLQ insertion for failed deliveries
- Retry scheduling
- Delivery history tracking

**Usage:**
```python
from app.services.alert_delivery import AlertDeliveryService

service = AlertDeliveryService()
await service.track_delivery(alert_id, alert_data, delivery_methods)
await service.push_to_dlq(alert_id, alert_data, error_message)
```

**Key Features:**
- Delivery tracking
- Deduplication
- DLQ management
- Retry scheduling

---

### Relationship
**Pattern:** **Composition** (not duplication)

```
AlertService
  └── uses AlertDeliveryService (for delivery tracking)
  └── uses NotificationService (for actual delivery)
```

**Flow:**
1. `AlertService.evaluate_condition()` - Check if condition is met
2. `AlertService.should_trigger()` - Check cooldown and if should trigger
3. `AlertService.deliver_alert()` - Deliver alert
   - Uses `AlertDeliveryService.track_delivery()` - Track delivery
   - Uses `NotificationService` - Send notification

---

### Recommendation
✅ **KEEP BOTH** - They serve different purposes:
- Use `AlertService` for condition evaluation and triggering logic
- Use `AlertDeliveryService` for delivery tracking and DLQ management
- `AlertService` uses `AlertDeliveryService` internally (composition pattern)

**Current Usage:**
- `AlertService`: Used in `macro_hound.py`, `evaluate_alerts.py`, `api/routes/alerts.py`
- `AlertDeliveryService`: Used in `AlertService.deliver_alert()`, `alert_retry_worker.py`

---

## Summary

### Services Are NOT Duplicates

| Service Pair | Relationship | Recommendation |
|--------------|--------------|---------------|
| `ScenarioService` vs `MacroAwareScenarioService` | Composition (wrapper) | ✅ Keep both - different purposes |
| `AlertService` vs `AlertDeliveryService` | Composition (dependency) | ✅ Keep both - different responsibilities |

### Architecture Pattern

Both pairs follow the **Composition Pattern**:
- Higher-level service wraps lower-level service
- Each service has distinct responsibilities
- Clear separation of concerns
- No circular dependencies

### Action Items

✅ **No changes needed** - Services are correctly architected:
1. `MacroAwareScenarioService` correctly wraps `ScenarioService`
2. `AlertService` correctly uses `AlertDeliveryService`
3. Both pairs follow composition pattern (not duplication)

### Documentation

**Recommendation:** Add clear documentation to each service explaining:
- What it does
- When to use it vs. the related service
- How it relates to the other service

---

## Conclusion

**Status:** ✅ **NO ACTION REQUIRED**

The services are **not duplicates** - they are **complementary services** with clear separation of concerns. The architecture follows the composition pattern correctly.

**Next Steps:**
- Consider adding documentation to clarify when to use each service
- No refactoring needed

