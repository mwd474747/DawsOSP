# Constants Module Health Dashboard

**Generated:** 2025-11-07
**Location:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/core/constants/`

---

## Overall Health Score: 38% ⚠️

**Status:** NEEDS ATTENTION - 62% of constants are unused

```
████████████░░░░░░░░░░░░░░░░░░░░  38% Utilized
```

---

## Module Health Scorecard

### 🟢 HEALTHY (>80% utilization)

#### macro.py - 97.1% ✅✅✅
```
█████████████████████████████████████████████████░  97.1%
```
- **Total:** 34 constants
- **Used:** 33 constants
- **Unused:** 1 constant
- **Status:** EXCELLENT - Nearly perfect utilization
- **Top Uses:** Regime detection z-scores, phase weights
- **Action:** Remove 1 unused constant

#### scenarios.py - 84.6% ✅✅
```
█████████████████████████████████████████████░░░░░  84.6%
```
- **Total:** 39 constants
- **Used:** 33 constants
- **Unused:** 6 constants
- **Status:** GOOD - Well maintained
- **Top Uses:** Deleveraging scenarios, shock magnitudes
- **Action:** Remove 6 unused optimization method constants

---

### 🟡 MODERATE (30-80% utilization)

#### http_status.py - 47.4% ⚠️
```
███████████████████████████░░░░░░░░░░░░░░░░░░░░░░  47.4%
```
- **Total:** 19 constants
- **Used:** 9 constants (HTTP_500 used 57 times!)
- **Unused:** 10 constants
- **Status:** ACCEPTABLE - Core codes heavily used
- **Top Uses:** Error handling, retry logic
- **Action:** Keep unused codes (may be used soon), remove aggregate lists

#### network.py - 33.3% ⚠️
```
████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  33.3%
```
- **Total:** 12 constants
- **Used:** 4 constants
- **Unused:** 8 constants
- **Status:** NEEDS CLEANUP - Many DB constants unused
- **Top Uses:** Server ports, interfaces
- **Action:** Remove 8 unused database pool/query constants

#### integration.py - 30.0% ⚠️
```
███████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  30.0%
```
- **Total:** 40 constants
- **Used:** 12 constants
- **Unused:** 28 constants
- **Status:** NEEDS CLEANUP - Many abandoned features
- **Top Uses:** Retry logic, rate limiting
- **Action:** Remove 28 unused cache/batch constants

---

### 🔴 CRITICAL (<30% utilization)

#### risk.py - 13.6% ❌
```
███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  13.6%
```
- **Total:** 22 constants
- **Used:** 3 constants
- **Unused:** 19 constants
- **Status:** CRITICAL - 86.4% waste
- **Top Uses:** VaR calculations, tracking error
- **Action:** REMOVE 19 unused constants immediately

#### financial.py - 12.0% ❌
```
██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12.0%
```
- **Total:** 25 constants
- **Used:** 3 constants
- **Unused:** 22 constants
- **Status:** CRITICAL - 88% waste
- **Top Uses:** TRADING_DAYS_PER_YEAR (10 usages)
- **Action:** REMOVE 22 unused constants immediately

#### validation.py - 8.5% ❌❌
```
█████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  8.5%
```
- **Total:** 47 constants
- **Used:** 4 constants
- **Unused:** 43 constants
- **Status:** CRITICAL - 91.5% waste
- **Top Uses:** Alert cooldowns, mock data detection
- **Action:** REMOVE 43 unused constants immediately

#### time_periods.py - 8.3% ❌❌
```
█████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  8.3%
```
- **Total:** 36 constants
- **Used:** 3 constants
- **Unused:** 33 constants
- **Status:** CRITICAL - 91.7% waste
- **Top Uses:** TRADING_DAYS_PER_YEAR (duplicate)
- **Action:** REMOVE 33 unused constants immediately

---

## Usage Patterns

### Most Used Constants (Top 10)

1. `HTTP_500_INTERNAL_SERVER_ERROR` - **57 usages** ⭐⭐⭐
2. `HTTP_400_BAD_REQUEST` - **17 usages** ⭐
3. `HTTP_403_FORBIDDEN` - **14 usages** ⭐
4. `HTTP_401_UNAUTHORIZED` - **12 usages**
5. `HTTP_404_NOT_FOUND` - **10 usages**
6. `HTTP_503_SERVICE_UNAVAILABLE` - **10 usages**
7. `DEFAULT_MAX_RETRIES` - **10 usages**
8. `DEFAULT_RETRY_DELAY` - **10 usages**
9. `TRADING_DAYS_PER_YEAR` - **10 usages** (financial.py)
10. `ZSCORE_AVERAGE` - **8 usages**

### Least Used Modules

| Module | Utilization | Status |
|--------|-------------|--------|
| time_periods.py | 8.3% | 🔴 DELETE CANDIDATE |
| validation.py | 8.5% | 🔴 DELETE CANDIDATE |
| financial.py | 12.0% | 🔴 MAJOR CLEANUP |
| risk.py | 13.6% | 🔴 MAJOR CLEANUP |

---

## Issues Found

### 🚨 Duplicate Constants (5 conflicts)

These constants are defined in multiple modules, creating inconsistency risk:

1. **DEFAULT_CONNECTION_TIMEOUT**
   - integration.py (unused)
   - network.py (used) ✅ Keep here

2. **MONTHS_PER_YEAR**
   - financial.py (used)
   - time_periods.py (unused) ✅ Keep here (canonical)

3. **RETRYABLE_STATUS_CODES**
   - integration.py (used)
   - http_status.py (used) ✅ Keep here (HTTP domain)

4. **TRADING_DAYS_PER_YEAR**
   - financial.py (used, 10 refs) ✅ Keep here (domain-specific)
   - time_periods.py (unused)

5. **WEEKS_PER_YEAR**
   - financial.py (used)
   - time_periods.py (unused) ✅ Keep here (canonical)

---

## Cleanup Priority Matrix

```
                    HIGH WASTE      MODERATE WASTE    LOW WASTE
                    (>80% unused)   (30-80% unused)   (<30% unused)
                    ═════════════   ═══════════════   ═════════════
HIGH PRIORITY       validation.py   integration.py
(>30 unused)        time_periods.py
                    financial.py

MEDIUM PRIORITY     risk.py         network.py
(10-30 unused)                      http_status.py

LOW PRIORITY                                          scenarios.py
(<10 unused)                                          macro.py
```

### Priority 1: Immediate Cleanup Required ⚠️⚠️⚠️
- **validation.py** - 43 unused (91.5%)
- **time_periods.py** - 33 unused (91.7%)
- **financial.py** - 22 unused (88%)

### Priority 2: Major Cleanup Needed ⚠️⚠️
- **integration.py** - 28 unused (70%)
- **risk.py** - 19 unused (86.4%)
- **network.py** - 8 unused (66.7%)

### Priority 3: Minor Cleanup ⚠️
- **http_status.py** - 10 unused (52.6%)
- **scenarios.py** - 6 unused (15.4%)
- **macro.py** - 1 unused (2.9%)

---

## Impact Analysis

### Current State
```
Total Constants:     274
Used:                104 (38%)
Unused:              170 (62%)
Duplicates:          5 conflicts
```

### After Cleanup
```
Total Constants:     ~104 (removing all unused)
Used:                104 (100%)
Unused:              0 (0%)
Duplicates:          0 (resolved)
Code Reduction:      ~500+ lines
Maintenance:         -62% tracking burden
```

### Benefits
- ✅ **Reduced confusion** - Only constants actually used remain
- ✅ **Faster development** - Easier to find relevant constants
- ✅ **Less maintenance** - Fewer constants to update/document
- ✅ **No duplicates** - Single source of truth for each value
- ✅ **Cleaner codebase** - 500+ lines removed

---

## Recommended Action Plan

### Week 1: Critical Cleanup
1. Remove 43 unused constants from `validation.py`
2. Remove 33 unused constants from `time_periods.py`
3. Remove 22 unused constants from `financial.py`
4. **Total removed:** 98 constants (36% of total)

### Week 2: Major Cleanup
5. Remove 28 unused constants from `integration.py`
6. Remove 19 unused constants from `risk.py`
7. Remove 8 unused constants from `network.py`
8. **Total removed:** 55 constants (20% of total)

### Week 3: Polish
9. Remove 10 unused constants from `http_status.py`
10. Remove 6 unused constants from `scenarios.py`
11. Remove 1 unused constant from `macro.py`
12. Resolve 5 duplicate constant conflicts
13. **Total removed:** 17 constants (6% of total)

### Week 4: Verification
14. Run full test suite
15. Update documentation
16. Verify no frontend dependencies
17. Create migration guide

---

## Risk Assessment

### Low Risk (Safe to Remove)
- All constants marked as unused with 0 usages
- Duplicates (keep canonical version)
- Mock/stub detection constants (deprecated)

### Medium Risk (Verify First)
- Constants with comments suggesting future use
- Optimization method constants (may be planned)
- Severity level constants (may be used in alerts)

### High Risk (Don't Remove)
- HTTP status codes (even if unused, may be needed soon)
- Rate limit constants (infrastructure)
- Core calculation constants (TRADING_DAYS_PER_YEAR, etc.)

---

## Success Metrics

Track these metrics after cleanup:

- [ ] Constants reduced from 274 to ~104 (62% reduction)
- [ ] Utilization improved from 38% to 100%
- [ ] All duplicate conflicts resolved (5 → 0)
- [ ] All tests passing
- [ ] No production issues
- [ ] Documentation updated

---

**End of Dashboard**
