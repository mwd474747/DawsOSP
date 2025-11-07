# Stub and Mock Implementation Refactor Plan

**Date:** January 14, 2025  
**Status:** 📋 **PLANNING COMPLETE**  
**Purpose:** Comprehensive plan to remove or properly implement all stub/mock/placeholder code

---

## Executive Summary

**Current State:**
- ✅ **Provenance Tracking:** System correctly tracks stub data via `_provenance` fields
- ⚠️ **Stub Fallbacks:** Multiple services fall back to stub data on errors
- ⚠️ **Mock Data in UI:** Frontend has fallback mock data for several pages
- ⚠️ **Stub Mode Services:** Several services have stub mode for testing
- ⚠️ **Placeholder Implementations:** Some capabilities return empty results
- ⚠️ **Hardcoded Test Data:** Hardcoded values (291290, 14.5, 1.35, AAPL) in multiple places

**Goal:**
- Remove all stub/mock implementations from production code
- Replace with proper error handling or real implementations
- Keep stub mode only for explicit testing (guarded by environment)
- Remove hardcoded test data
- Document all remaining placeholders

**Estimated Effort:** 40-60 hours across 5 phases

---

## 1. Critical Stub Implementations (P0 - Must Fix)

### 1.1 Agent Stub Fallbacks 🔴 **CRITICAL**

**Location:** `backend/app/agents/financial_analyst.py`

**Issues:**
1. **`ledger.positions`** - Falls back to stub AAPL position in development mode (line 290-303)
2. **`pricing.apply_pack`** - Falls back to stub prices if pricing pack unavailable (line 552)
3. **`get_security_fundamentals`** - Falls back to stub fundamentals if FMP_API_KEY not configured (line 2361)

**Current Behavior:**
```python
# Development mode fallback
if os.getenv("ENVIRONMENT") == "development":
    logger.warning("Falling back to stub positions (development mode)")
    positions = [{"security_id": "...", "symbol": "AAPL", ...}]
    provenance = DataProvenance.STUB
```

**Refactor Plan:**
- ✅ **Keep development fallback** - Already properly guarded
- ⚠️ **Remove production fallbacks** - Should raise errors instead
- ✅ **Provenance tracking** - Already correctly implemented
- **Action:** Verify all production paths raise errors instead of returning stubs

**Priority:** P0 (Production safety)

---

### 1.2 UI Mock Data Fallbacks 🔴 **CRITICAL**

**Location:** `full_ui.html`

**Issues:**
1. **`getComprehensiveMockData()`** - MacroCyclesPage fallback (line 7959)
2. **`getFallbackScenarios()`** - ScenariosPage fallback (line 9510)
3. **`getFallbackOptimizationData()`** - OptimizerPage fallback (line 9785)
4. **`getFallbackRating()`** - RatingsPage fallback (line 10387)

**Current Behavior:**
```javascript
// Always falls back to mock data on error
setMacroData(getComprehensiveMockData());
```

**Refactor Plan:**
- ⚠️ **Remove mock data fallbacks** - Show error messages instead
- ⚠️ **Use PatternRenderer error handling** - Let PatternRenderer handle errors
- ⚠️ **Remove hardcoded values** - No more `291290`, `14.5`, `1.35`
- **Action:** Replace all mock data with proper error handling

**Priority:** P0 (User experience)

---

## 2. Service Stub Modes (P1 - High Priority)

### 2.1 OptimizerService Stub Mode ⚠️ **HIGH PRIORITY**

**Location:** `backend/app/services/optimizer.py`

**Issues:**
1. **Stub mode initialization** - `use_db=False` enables stub mode (line 262)
2. **Mock database methods** - `_mock_execute_query()`, `_mock_execute_query_one()`, `_mock_execute_statement()` (lines 305-373)
3. **Stub rebalance result** - `_stub_rebalance_result()` returns no-op trades (line 1660)
4. **Equal weight fallback** - `_equal_weight_fallback()` when optimization fails (line 1240)

**Current Behavior:**
```python
if not use_db:
    self.execute_query = self._mock_execute_query
    # ... stub mode
```

**Refactor Plan:**
- ✅ **Keep stub mode for testing** - Already properly guarded
- ⚠️ **Remove production stub mode** - Already guarded in production
- ⚠️ **Improve error handling** - Better error messages when optimization fails
- **Action:** Verify production guard works, improve error messages

**Priority:** P1 (Testing infrastructure)

---

### 2.2 PricingService Stub Mode ⚠️ **HIGH PRIORITY**

**Location:** `backend/app/services/pricing.py`

**Issues:**
1. **Stub mode initialization** - `use_db=False` enables stub mode (line 154)
2. **Production guard** - Prevents stub mode in production (line 157)
3. **Stub price return** - Returns mock price of 100.00 USD (line 338)

**Current Behavior:**
```python
# Production guard: prevent stub mode in production
if os.getenv("ENVIRONMENT") == "production" and not use_db:
    raise ValueError("Cannot use stub mode in production")
```

**Refactor Plan:**
- ✅ **Production guard** - Already properly implemented
- ✅ **Stub mode for testing** - Appropriate for development
- **Action:** Verify all production paths use `use_db=True`

**Priority:** P1 (Already properly guarded)

---

### 2.3 AlertsService Stub Mode ⚠️ **HIGH PRIORITY**

**Location:** `backend/app/services/alerts.py`

**Issues:**
1. **Stub singleton** - `get_alert_service_stub()` returns stub instance (line 1455)
2. **Stub implementations** - Multiple methods return random values (lines 437, 513, 580, 648, 766)
3. **Stub deduplication** - No deduplication in stub mode (line 1196)

**Current Behavior:**
```python
# Stub: return random value
return random.uniform(0, 1)
```

**Refactor Plan:**
- ⚠️ **Remove stub implementations** - Implement real alert logic
- ⚠️ **Keep stub mode for testing** - But guard properly
- **Action:** Implement real alert evaluation logic

**Priority:** P1 (Core functionality)

---

## 3. Placeholder Implementations (P2 - Medium Priority)

### 3.1 NotificationsService Stubs ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/services/notifications.py`

**Issues:**
1. **Stub notification ID** - Returns fake ID (line 196)
2. **Stub permission check** - Always allows (line 384)
3. **Stub email** - Returns fake email (line 448)
4. **Stub success** - Always succeeds (lines 485, 522)
5. **Stub list** - Returns empty list (line 560)

**Current Behavior:**
```python
# Stub: return fake notification ID
return "notification_123"
```

**Refactor Plan:**
- ⚠️ **Implement real notification system** - Database-backed notifications
- ⚠️ **Email integration** - Real email sending (SMTP/SendGrid)
- ⚠️ **Permission system** - Real permission checks
- **Action:** Implement full notification system

**Priority:** P2 (Feature completeness)

---

### 3.2 DLQ Service Stubs ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/services/dlq.py`

**Issues:**
1. **Stub job ID** - Returns fake ID (line 138)
2. **Stub list** - Returns empty list (line 199)
3. **Stub success** - Always succeeds (lines 285, 334)
4. **Stub metrics** - Returns zeros (line 387)
5. **Stub count** - Returns 0 (line 439)

**Current Behavior:**
```python
# Stub: return fake job ID
return "dlq_job_123"
```

**Refactor Plan:**
- ⚠️ **Implement real DLQ system** - Database-backed dead letter queue
- ⚠️ **Retry logic** - Real retry mechanism
- ⚠️ **Metrics tracking** - Real DLQ metrics
- **Action:** Implement full DLQ system

**Priority:** P2 (Reliability)

---

### 3.3 BenchmarksService Stub Data ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/services/benchmarks.py`

**Issues:**
1. **Stub price generation** - Generates synthetic prices (line 255)
2. **Stub FX rates** - Constant 1.36 CAD per USD (line 316)

**Current Behavior:**
```python
# Generate stub prices (1% daily return)
prices = [100 * (1.01 ** i) for i in range(days)]
```

**Refactor Plan:**
- ⚠️ **Use real benchmark data** - Fetch from data providers
- ⚠️ **Real FX rates** - Use pricing packs for FX rates
- **Action:** Integrate real benchmark providers

**Priority:** P2 (Data accuracy)

---

### 3.4 ReportsService Fallback ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/services/reports.py`

**Issues:**
1. **Fallback HTML generation** - `_generate_fallback_html()` (line 524)
2. **Simple HTML fallback** - Returns basic HTML when PDF generation fails (line 391)

**Current Behavior:**
```python
# Fallback: return simple HTML
return self._generate_fallback_html(report_data, attributions, watermark)
```

**Refactor Plan:**
- ⚠️ **Improve error handling** - Better error messages
- ⚠️ **Keep fallback** - But improve quality
- **Action:** Enhance fallback HTML generation

**Priority:** P2 (User experience)

---

### 3.5 RatingsService Fallback Weights ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/services/ratings.py`

**Issues:**
1. **Fallback weights** - `_get_fallback_weights()` when database unavailable (line 167)
2. **Hardcoded weights** - Hardcoded rating weights

**Current Behavior:**
```python
# Fallback to hardcoded weights if database unavailable
weights = self._get_fallback_weights(rating_type)
```

**Refactor Plan:**
- ✅ **Keep fallback** - Appropriate for resilience
- ⚠️ **Document fallback** - Make it clear this is fallback
- **Action:** Document fallback behavior, ensure it's only used when DB unavailable

**Priority:** P2 (Resilience - acceptable)

---

## 4. Incomplete Capabilities (P2 - Medium Priority)

### 4.1 Tax-Related Capabilities ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/agents/financial_analyst.py`

**Issues:**
1. **No tax capabilities** - Tax harvesting, realized P&L, wash sale rules not implemented
2. **Patterns archived** - Tax patterns moved to archive (`.archive/tax-patterns-2025-01-14/`)

**Current State:**
- Tax patterns exist but are archived
- No agent capabilities for tax features

**Refactor Plan:**
- ⚠️ **Implement tax capabilities** - If needed for production
- ⚠️ **Or document as future work** - If not needed now
- **Action:** Decide if tax features are needed, implement or document

**Priority:** P2 (Feature completeness)

---

### 4.2 Factor Analysis Placeholder ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/services/factor_analysis.py`

**Issues:**
1. **Synthetic factor returns** - Placeholder comment (line 338)
2. **May not use real factor data** - Needs verification

**Current Behavior:**
```python
# Placeholder: Generate synthetic factor returns for demonstration
```

**Refactor Plan:**
- ⚠️ **Verify implementation** - Check if using real factor data
- ⚠️ **Remove placeholder comment** - If implementation is real
- **Action:** Review factor analysis implementation

**Priority:** P2 (Documentation)

---

### 4.3 Currency Attribution Placeholder ⚠️ **MEDIUM PRIORITY**

**Location:** `backend/app/services/currency_attribution.py`

**Issues:**
1. **Weight placeholder** - Comment says "should be computed from total portfolio value" (line 342)

**Current Behavior:**
```python
# Weight (placeholder - should be computed from total portfolio value)
```

**Refactor Plan:**
- ⚠️ **Verify implementation** - Check if weight is computed correctly
- ⚠️ **Remove placeholder comment** - If implementation is correct
- **Action:** Review currency attribution implementation

**Priority:** P2 (Documentation)

---

## 5. Hardcoded Test Data (P3 - Low Priority)

### 5.1 Hardcoded Portfolio Values ⚠️ **LOW PRIORITY**

**Locations:**
- `full_ui.html`: `291290`, `14.5`, `1.35`, `9 holdings`
- `combined_server.py`: Same hardcoded values
- `backend/app/agents/financial_analyst.py`: Hardcoded `AAPL` in stub data

**Issues:**
1. **Hardcoded total_value** - `291290` appears in multiple places
2. **Hardcoded returns** - `14.5`, `1.35` (Sharpe ratio)
3. **Hardcoded symbols** - `AAPL`, `MSFT`, `GOOGL` in test data

**Refactor Plan:**
- ⚠️ **Remove from production code** - Only in test files
- ⚠️ **Use real data** - Fetch from database/API
- **Action:** Replace hardcoded values with real data or remove

**Priority:** P3 (Code cleanliness)

---

### 5.2 Default Symbol in AI Assistant ⚠️ **LOW PRIORITY**

**Location:** `full_ui.html` (line 11102)

**Issues:**
1. **Default to AAPL** - `symbol: msg.pattern === 'holding_deep_dive' ? 'AAPL' : undefined`

**Current Behavior:**
```javascript
symbol: msg.pattern === 'holding_deep_dive' ? 'AAPL' : undefined
```

**Refactor Plan:**
- ⚠️ **Remove default** - Let user specify symbol
- ⚠️ **Or use portfolio holdings** - Use actual portfolio symbols
- **Action:** Remove hardcoded AAPL default

**Priority:** P3 (User experience)

---

## 6. Empty Return Implementations (P3 - Low Priority)

### 6.1 Empty List Returns ⚠️ **LOW PRIORITY**

**Locations:**
- Multiple services return `[]` or `{}` on error

**Issues:**
1. **Silent failures** - Return empty results instead of errors
2. **No error indication** - Caller doesn't know if empty = no data or error

**Refactor Plan:**
- ⚠️ **Return error objects** - Include error field in response
- ⚠️ **Use provenance** - Mark as error in provenance
- **Action:** Review all empty returns, add error indicators

**Priority:** P3 (Error handling)

---

## Refactor Execution Plan

### Phase 1: Critical Stub Removal (8-12 hours) 🔴 **P0**

**Tasks:**
1. ✅ Verify production guards work correctly
2. ⚠️ Remove UI mock data fallbacks
3. ⚠️ Replace with proper error handling
4. ⚠️ Test error scenarios

**Files:**
- `full_ui.html` - Remove `getComprehensiveMockData()`, `getFallbackScenarios()`, etc.
- `backend/app/agents/financial_analyst.py` - Verify production error handling

---

### Phase 2: Service Stub Mode Review (6-8 hours) ⚠️ **P1**

**Tasks:**
1. ✅ Verify OptimizerService production guard
2. ✅ Verify PricingService production guard
3. ⚠️ Review AlertsService stub implementations
4. ⚠️ Implement real alert logic

**Files:**
- `backend/app/services/optimizer.py` - Review stub mode
- `backend/app/services/pricing.py` - Review stub mode
- `backend/app/services/alerts.py` - Implement real logic

---

### Phase 3: Placeholder Implementation (12-16 hours) ⚠️ **P2**

**Tasks:**
1. ⚠️ Implement NotificationsService
2. ⚠️ Implement DLQ Service
3. ⚠️ Integrate real benchmark data
4. ⚠️ Improve ReportsService fallback

**Files:**
- `backend/app/services/notifications.py` - Full implementation
- `backend/app/services/dlq.py` - Full implementation
- `backend/app/services/benchmarks.py` - Real data integration
- `backend/app/services/reports.py` - Improve fallback

---

### Phase 4: Incomplete Capabilities (8-12 hours) ⚠️ **P2**

**Tasks:**
1. ⚠️ Review factor analysis implementation
2. ⚠️ Review currency attribution implementation
3. ⚠️ Document or implement tax capabilities
4. ⚠️ Remove placeholder comments

**Files:**
- `backend/app/services/factor_analysis.py` - Review and document
- `backend/app/services/currency_attribution.py` - Review and document
- `backend/app/agents/financial_analyst.py` - Document tax capabilities

---

### Phase 5: Code Cleanup (4-6 hours) ⚠️ **P3**

**Tasks:**
1. ⚠️ Remove hardcoded test data
2. ⚠️ Remove default AAPL symbol
3. ⚠️ Improve empty return error handling
4. ⚠️ Document all remaining placeholders

**Files:**
- `full_ui.html` - Remove hardcoded values
- `combined_server.py` - Remove hardcoded values
- All services - Improve error handling

---

## Success Criteria

### Phase 1 ✅
- ✅ No UI mock data fallbacks in production
- ✅ All errors properly displayed to users
- ✅ PatternRenderer handles all errors gracefully

### Phase 2 ✅
- ✅ All production guards verified
- ✅ Stub mode only available in test environment
- ✅ Real alert logic implemented

### Phase 3 ✅
- ✅ NotificationsService fully implemented
- ✅ DLQ Service fully implemented
- ✅ Real benchmark data integrated

### Phase 4 ✅
- ✅ All placeholder comments removed or resolved
- ✅ Tax capabilities documented or implemented
- ✅ Factor analysis verified

### Phase 5 ✅
- ✅ No hardcoded test data in production code
- ✅ All empty returns include error indicators
- ✅ All placeholders documented

---

## Risk Assessment

### High Risk
- **Removing UI mock data** - May break error handling
- **Removing service stubs** - May break tests

### Medium Risk
- **Implementing real services** - May introduce bugs
- **Removing hardcoded data** - May break demos

### Low Risk
- **Removing placeholder comments** - Documentation only
- **Code cleanup** - Low impact

---

## Recommendations

### Immediate Actions (This Week)
1. ✅ **Verify production guards** - Ensure stub mode can't be enabled in production
2. ⚠️ **Remove UI mock data** - Replace with proper error handling
3. ⚠️ **Review AlertsService** - Implement real alert logic

### Short Term (Next 2 Weeks)
1. ⚠️ **Implement NotificationsService** - Full notification system
2. ⚠️ **Implement DLQ Service** - Dead letter queue
3. ⚠️ **Integrate benchmark data** - Real benchmark providers

### Medium Term (Next Month)
1. ⚠️ **Review incomplete capabilities** - Document or implement
2. ⚠️ **Code cleanup** - Remove hardcoded data
3. ⚠️ **Error handling improvements** - Better error messages

---

## Files Requiring Changes

### Critical (P0)
1. `full_ui.html` - Remove mock data fallbacks
2. `backend/app/agents/financial_analyst.py` - Verify production error handling

### High Priority (P1)
1. `backend/app/services/alerts.py` - Implement real alert logic
2. `backend/app/services/optimizer.py` - Review stub mode
3. `backend/app/services/pricing.py` - Review stub mode

### Medium Priority (P2)
1. `backend/app/services/notifications.py` - Full implementation
2. `backend/app/services/dlq.py` - Full implementation
3. `backend/app/services/benchmarks.py` - Real data integration
4. `backend/app/services/reports.py` - Improve fallback
5. `backend/app/services/factor_analysis.py` - Review implementation
6. `backend/app/services/currency_attribution.py` - Review implementation

### Low Priority (P3)
1. `full_ui.html` - Remove hardcoded values
2. `combined_server.py` - Remove hardcoded values
3. All services - Improve error handling

---

**Total Estimated Effort:** 40-60 hours  
**Priority Order:** P0 → P1 → P2 → P3  
**Risk Level:** Medium (most changes are safe, some require careful testing)

