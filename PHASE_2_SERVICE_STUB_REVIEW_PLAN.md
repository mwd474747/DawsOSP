# Phase 2: Service Stub Mode Review - PLAN

**Date:** January 14, 2025  
**Status:** 📋 **READY TO START**  
**Phase:** Phase 2 - Service Stub Mode Review (P1)

---

## Overview

Phase 2 focuses on reviewing and improving service stub modes, with particular emphasis on implementing real alert logic in AlertsService.

**Estimated Effort:** 6-8 hours  
**Priority:** P1 (High Priority)

---

## Tasks

### 1. ✅ Verify OptimizerService Production Guard (COMPLETE)

**Status:** ✅ Already verified in Phase 1

**Location:** `backend/app/services/optimizer.py`

**Current State:**
- Production guard prevents stub mode in production (line 262)
- Stub mode only available for testing
- Mock database methods properly implemented

**Action:** ✅ No action needed - already verified

---

### 2. ✅ Verify PricingService Production Guard (COMPLETE)

**Status:** ✅ Already verified in Phase 1

**Location:** `backend/app/services/pricing.py`

**Current State:**
- Production guard prevents stub mode in production (line 155)
- Stub mode only available for development/testing
- Proper error handling in place

**Action:** ✅ No action needed - already verified

---

### 3. ⚠️ Review AlertsService Stub Implementations (TODO)

**Status:** ⚠️ **TODO** - **IMPORTANT: Service is DEPRECATED**

**Location:** `backend/app/services/alerts.py`

**⚠️ CRITICAL FINDING:**
The service is **DEPRECATED** (line 4):
```python
⚠️ DEPRECATED: This service is deprecated and will be removed in a future release.
The functionality has been consolidated into the MacroHound agent.
Use `macro_hound` agent capabilities instead.
```

**Issues Identified:**
1. **Stub singleton** - `get_alert_service_stub()` returns stub instance (line 1455)
2. **Stub implementations** - Multiple methods return random values:
   - `_get_price_value()` - Returns random price (line ~648)
   - `_get_sentiment_value()` - Returns random sentiment (line ~513)
   - `_get_portfolio_metric()` - Returns random metrics (line ~580)
   - `_evaluate_price_condition()` - Uses stub price values (line ~618)
   - `_evaluate_sentiment_condition()` - Uses stub sentiment values (line ~766)
3. **Stub deduplication** - No deduplication in stub mode (line ~1196)

**Current Behavior:**
```python
# Stub: return random value
return Decimal(str(random.uniform(10, 50)))
```

**Refactor Plan:**
- ⚠️ **Option A: Document deprecation** - Since service is deprecated, stub mode is acceptable
- ⚠️ **Option B: Add production guard** - Prevent stub mode in production (if still used)
- ⚠️ **Option C: Mark for removal** - Document that stub mode is acceptable for deprecated service
- ⚠️ **Verify usage** - Check if service is still used anywhere
- **Action:** Decide on approach based on usage

**Priority:** P1 (Documentation/Deprecation handling)

---

### 4. ⚠️ Implement Real Alert Logic (TODO)

**Status:** ⚠️ **TODO**

**Location:** `backend/app/services/alerts.py`

**Required Implementations:**

#### 4.1 Real Price Alert Logic
- **Current:** Returns random price
- **Required:** Fetch real price from pricing service
- **Method:** `get_current_price(security_id, currency)`
- **Integration:** Use `PricingService` to get current price

#### 4.2 Real Sentiment Alert Logic
- **Current:** Returns random sentiment
- **Required:** Fetch real sentiment from data providers
- **Method:** `get_current_sentiment(security_id)`
- **Integration:** Use `DataHarvester` or external API

#### 4.3 Real Portfolio Metrics Alert Logic
- **Current:** Returns random metrics
- **Required:** Calculate real portfolio metrics
- **Method:** `get_portfolio_metrics(portfolio_id)`
- **Integration:** Use `PortfolioService` or `FinancialAnalyst`

#### 4.4 Real Alert Evaluation
- **Current:** Returns random result
- **Required:** Evaluate alerts against real data
- **Methods:** 
  - `check_price_alert(alert, current_price)`
  - `check_portfolio_alert(alert, portfolio_metrics)`
- **Logic:** Compare alert thresholds with actual values

#### 4.5 Real Deduplication
- **Current:** No deduplication in stub mode
- **Required:** Implement deduplication logic
- **Method:** `_deduplicate_alerts(alerts)`
- **Logic:** Prevent duplicate alerts within time window

---

## Implementation Strategy

### Step 1: Review Current Stub Implementations
1. Identify all stub methods in AlertsService
2. Document what each stub method should do
3. Identify dependencies (PricingService, DataHarvester, etc.)

### Step 2: Implement Real Logic
1. Replace `get_current_price()` with real pricing service call
2. Replace `get_current_sentiment()` with real data provider call
3. Replace `get_portfolio_metrics()` with real portfolio service call
4. Implement real alert evaluation logic
5. Implement deduplication logic

### Step 3: Add Production Guard
1. Add production guard to prevent stub mode in production
2. Ensure stub mode only available in test environment
3. Add proper error handling

### Step 4: Testing
1. Test real alert evaluation
2. Test deduplication logic
3. Test error handling
4. Verify production guard works

---

## Files to Modify

### Primary File
- `backend/app/services/alerts.py` - Implement real alert logic

### Dependencies
- `backend/app/services/pricing.py` - For price data
- `backend/app/agents/data_harvester.py` - For sentiment data
- `backend/app/services/portfolio.py` - For portfolio metrics (if exists)
- `backend/app/agents/financial_analyst.py` - For portfolio metrics (if needed)

---

## Success Criteria

### Phase 2 Complete When:
- ✅ All production guards verified
- ✅ AlertsService stub implementations reviewed
- ✅ Real alert logic implemented
- ✅ Real price fetching implemented
- ✅ Real sentiment fetching implemented
- ✅ Real portfolio metrics implemented
- ✅ Real alert evaluation implemented
- ✅ Deduplication logic implemented
- ✅ Production guard added to AlertsService
- ✅ All tests passing
- ✅ Error handling improved

---

## Risk Assessment

### High Risk
- **Implementing real alert logic** - May introduce bugs
- **Integrating with external services** - May fail if services unavailable

### Medium Risk
- **Removing stub implementations** - May break tests
- **Adding production guard** - May affect development workflow

### Low Risk
- **Reviewing stub implementations** - Read-only operation
- **Documentation** - Low impact

---

## Next Steps

1. **Review AlertsService** - Identify all stub methods
2. **Implement real price logic** - Use PricingService
3. **Implement real sentiment logic** - Use DataHarvester
4. **Implement real portfolio metrics** - Use PortfolioService/FinancialAnalyst
5. **Implement real alert evaluation** - Compare thresholds with actual values
6. **Implement deduplication** - Prevent duplicate alerts
7. **Add production guard** - Prevent stub mode in production
8. **Test thoroughly** - Verify all functionality works

---

**Estimated Time:** 6-8 hours  
**Priority:** P1 (High Priority)  
**Risk Level:** Medium (requires careful implementation and testing)

