# Constants Extraction - Phases 9-19 Execution Plan

**Date**: November 7, 2025
**Current Status**: Phases 1-8 Complete (88% overall)
**Remaining Work**: Phases 9-19 (12% of original scope)

---

## Executive Summary

This document provides a **detailed execution plan** for completing the remaining constants extraction work (Phases 9-19). Based on the comprehensive analysis in [CONSTANTS_REMAINING_ANALYSIS.md](CONSTANTS_REMAINING_ANALYSIS.md), we've identified **~100-120 remaining magic numbers**.

**Key Recommendation**: The highest-value work is **already complete** (Phases 1-8). Remaining phases are **incremental improvements** with diminishing returns.

---

## 📋 Phase Breakdown

### 🔴 HIGH PRIORITY (Phases 9-11)

#### Phase 9: Alert & Notification Domain
- **Effort**: 3-4 hours
- **Impact**: 8 instances
- **Priority**: HIGH (user-facing functionality)

**Tasks**:
1. Create `backend/app/core/constants/alerts.py`
2. Migrate `backend/app/api/routes/alerts.py` (lines 77, 79, 90)
3. Migrate `backend/app/services/alert_delivery.py` (line 94)
4. Validate with `python3 -m py_compile`
5. Test alert cooldown functionality
6. Commit: "Constants extraction Phase 9 - Alerts domain COMPLETE"

**Constants**:
```python
DEFAULT_ALERT_COOLDOWN_HOURS = 24
ALERT_DEDUP_LOOKBACK_HOURS = 24
MAX_ALERT_COOLDOWN_HOURS = 8760
ALERT_COOLDOWN_EXTENDED = 48
ALERT_COOLDOWN_WEEKLY = 168
```

**Testing**:
- Verify alert cooldown respects new constants
- Check API validation accepts valid range (1 to 8760 hours)
- Ensure deduplication uses correct lookback window

---

#### Phase 10: DLQ (Dead Letter Queue) Domain
- **Effort**: 3-4 hours
- **Impact**: 6 instances
- **Priority**: HIGH (reliability critical)

**Tasks**:
1. Create `backend/app/core/constants/dlq.py`
2. Migrate `backend/app/services/dlq.py` (lines 73, 74, 218, 219, 421)
3. Update SQL queries to use constants
4. Validate with `python3 -m py_compile`
5. Test retry delay progression
6. Commit: "Constants extraction Phase 10 - DLQ domain COMPLETE"

**Constants**:
```python
DLQ_RETRY_DELAY_ATTEMPT_1_MIN = 1
DLQ_RETRY_DELAY_ATTEMPT_2_MIN = 5
DLQ_RETRY_DELAY_ATTEMPT_3_MIN = 30
DLQ_RETRY_DELAY_FALLBACK_MIN = 60
DLQ_DEFAULT_BATCH_SIZE = 100
FAILED_ALERTS_DEFAULT_BATCH_SIZE = 100
DLQ_CLEANUP_RETENTION_DAYS = 30
```

**Testing**:
- Verify retry delays match expected progression (1m → 5m → 30m)
- Check DLQ cleanup respects 30-day retention
- Ensure batch sizes work for pagination

---

#### Phase 11: Authentication & Security Domain
- **Effort**: 2-3 hours
- **Impact**: 5 instances
- **Priority**: HIGH (security critical)

**Tasks**:
1. Create `backend/app/core/constants/auth.py`
2. Migrate `backend/app/services/auth.py` (lines 91, 128, 130, 309)
3. Migrate `backend/app/api/routes/auth.py` (lines 68, 172, 428)
4. Validate with `python3 -m py_compile`
5. Test JWT expiration and password validation
6. Commit: "Constants extraction Phase 11 - Auth domain COMPLETE"

**Constants**:
```python
JWT_TOKEN_EXPIRY_HOURS = 24
JWT_TOKEN_EXPIRY_SECONDS = 86400
MIN_PASSWORD_LENGTH = 8
ACCOUNT_LOCKOUT_DURATION_MINUTES = 30
DEFAULT_LOCALHOST_IP = "127.0.0.1"
```

**Testing**:
- Verify JWT tokens expire after 24 hours
- Check password validation enforces 8-character minimum
- Ensure account lockout lasts 30 minutes

---

### 🟡 MEDIUM PRIORITY (Phases 12-16)

#### Phase 12: API & Pagination Domain
- **Effort**: 2-3 hours
- **Impact**: 7 instances
- **Priority**: MEDIUM (API consistency)

**Tasks**:
1. Create `backend/app/core/constants/api.py`
2. Migrate `backend/app/api/routes/alerts.py` (line 313)
3. Migrate `backend/app/api/routes/auth.py` (line 325)
4. Validate with `python3 -m py_compile`
5. Test pagination limits
6. Commit: "Constants extraction Phase 12 - API domain COMPLETE"

**Constants**:
```python
DEFAULT_API_LIMIT = 100
MIN_API_LIMIT = 1
MAX_API_LIMIT = 1000
USERS_LIST_DEFAULT_LIMIT = 100
ALERTS_LIST_DEFAULT_LIMIT = 100
```

---

#### Phase 13: Corporate Actions & Sync Domain
- **Effort**: 2-3 hours
- **Impact**: 5 instances
- **Priority**: MEDIUM (data sync)

**Tasks**:
1. Create `backend/app/core/constants/corporate_actions.py`
2. Migrate `backend/app/services/corporate_actions_sync.py` (lines 52, 211, 213, 267)
3. Validate with `python3 -m py_compile`
4. Test sync windows and backoff strategy
5. Commit: "Constants extraction Phase 13 - Corporate Actions COMPLETE"

**Constants**:
```python
CORPORATE_ACTIONS_LOOKBACK_DAYS = 30
CORPORATE_ACTIONS_LOOKAHEAD_DAYS = 30
CORPORATE_ACTIONS_BACKOFF_BASE_SECONDS = 30
CORPORATE_ACTIONS_RECOVERY_TIMEOUT_SECONDS = 60
```

---

#### Phase 14: Portfolio & Hedge Domain
- **Effort**: 3-4 hours
- **Impact**: 15 instances
- **Priority**: MEDIUM (trading operations)

**Tasks**:
1. Create `backend/app/core/constants/portfolio.py`
2. Migrate `backend/app/services/macro_aware_scenarios.py` (lines 943, 947, 970, 973-975, 1029, 1034-1063)
3. Migrate `backend/app/services/optimizer.py` (lines 126, 127, 1174, 1296, 1465)
4. Migrate `backend/app/services/cycles.py` (lines 477, 482, 608)
5. Validate with `python3 -m py_compile`
6. Test hedge allocations and optimization
7. Commit: "Constants extraction Phase 14 - Portfolio domain COMPLETE"

**Constants**:
```python
DEFAULT_COMMISSION_PER_TRADE_USD = 5.00
DEFAULT_MARKET_IMPACT_BPS = 15.0
MIN_TRADE_SHARES = 1
MIN_TRADE_VALUE_USD = 100
HEDGE_BUDGET_PCT = 0.10
# ... (see full list in CONSTANTS_REMAINING_ANALYSIS.md)
```

---

#### Phase 15: Numeric Precision Domain
- **Effort**: 2 hours
- **Impact**: 6 instances
- **Priority**: MEDIUM (calculation accuracy)

**Tasks**:
1. Create `backend/app/core/constants/precision.py`
2. Migrate `backend/app/services/currency_attribution.py` (lines 246, 248, 263-272)
3. Validate with `python3 -m py_compile`
4. Test rounding precision
5. Commit: "Constants extraction Phase 15 - Precision domain COMPLETE"

**Constants**:
```python
BPS_CONVERSION_FACTOR = 10000
DECIMAL_PRECISION_RETURN = 6
DECIMAL_PRECISION_WEIGHT = 4
DECIMAL_PRECISION_CURRENCY = 2
ATTRIBUTION_ERROR_TOLERANCE_BPS = 1.0
```

---

#### Phase 16: Data Quality Domain
- **Effort**: 2-3 hours
- **Impact**: 8 instances
- **Priority**: MEDIUM (data validation)

**Tasks**:
1. Extend `backend/app/core/constants/validation.py`
2. Migrate `backend/app/services/macro.py` (line 227)
3. Migrate `backend/app/services/currency_attribution.py` (line 86)
4. Migrate `backend/app/services/benchmarks.py` (lines 141, 370)
5. Validate with `python3 -m py_compile`
6. Test minimum data point checks
7. Commit: "Constants extraction Phase 16 - Data Quality COMPLETE"

**Constants**:
```python
MIN_DATA_POINTS_FOR_ZSCORE = 30
MIN_PRICES_FOR_RETURN_CALC = 2
MIN_FX_RATES_FOR_CALC = 2
MIN_LOOKBACK_DAYS = 1
MAX_LOOKBACK_DAYS = 3650
```

---

### 🟢 LOW PRIORITY (Phases 17-18)

#### Phase 17: Network & Health Check Domain
- **Effort**: 1 hour
- **Impact**: 2 instances
- **Priority**: LOW (minor improvement)

**Tasks**:
1. Extend `backend/app/core/constants/network.py`
2. Migrate `backend/app/api/health.py` (line 199)
3. Validate with `python3 -m py_compile`
4. Commit: "Constants extraction Phase 17 - Network extended COMPLETE"

**Constants**:
```python
HEALTH_API_PORT = 8001
```

---

#### Phase 18: Stub/Test Data Domain
- **Effort**: 2 hours
- **Impact**: 9 instances
- **Priority**: LOW (test fixtures)

**Tasks**:
1. Create `backend/tests/constants/stub_data.py`
2. Migrate `backend/app/services/alerts.py` (lines 490, 655, 741, 743, 875)
3. Validate with `python3 -m py_compile`
4. Mark as DEPRECATED in documentation
5. Commit: "Constants extraction Phase 18 - Stub data COMPLETE"

**Constants**:
```python
STUB_VIX_MIN = 10
STUB_VIX_MAX = 50
STUB_RATING_MIN = 0
STUB_RATING_MAX = 10
# ... (see full list in CONSTANTS_REMAINING_ANALYSIS.md)
```

**Note**: These stub data constants should be **removed** after service migration is complete.

---

### ⚪ OPTIONAL (Phase 19)

#### Phase 19: Frontend CSS Variables
- **Effort**: 4-6 hours
- **Impact**: 30-40 instances
- **Priority**: OPTIONAL (already using CSS variables for colors)

**Tasks**:
1. Extend `:root` section in `frontend/styles.css`
2. Add CSS custom properties for:
   - Opacity levels (--opacity-subtle, --opacity-hover, etc.)
   - Border radius (--radius-sm, --radius-md, etc.)
   - Spacing (--spacing-xs, --spacing-sm, etc.)
   - Z-index layers (--z-header, --z-modal, etc.)
   - Transitions (--transition-fast, --transition-normal)
3. Replace magic numbers with `var(--property-name)`
4. Test UI rendering (visual regression)
5. Commit: "Frontend CSS variables expansion COMPLETE"

**Recommendation**: **SKIP THIS PHASE** unless:
- User explicitly requests it
- Team wants 100% completion
- Design system standardization is a priority

**Rationale**: Frontend already follows best practices with CSS variables for colors and shadows. Remaining magic numbers are standard CSS spacing values that are unlikely to change.

---

## 🎯 Execution Strategies

### Strategy A: High-Priority Only (RECOMMENDED)
**Complete Phases 9-11**
- **Effort**: 9-11 hours
- **Impact**: 19 instances
- **Result**: 93% total completion (195/210)
- **Benefit**: All security and reliability-critical constants extracted

**Phases**:
1. Phase 9: Alerts (3-4 hours)
2. Phase 10: DLQ (3-4 hours)
3. Phase 11: Auth (2-3 hours)

**Outcome**: Production-ready state with all critical operational constants documented.

---

### Strategy B: Backend Complete
**Complete Phases 9-18**
- **Effort**: 20-28 hours
- **Impact**: 70-80 instances
- **Result**: 98% backend completion (246/250)
- **Benefit**: Backend 100% magic-number free

**Phases**:
1. High-Priority (Phases 9-11): 9-11 hours
2. Medium-Priority (Phases 12-16): 11-17 hours
3. Low-Priority (Phases 17-18): 3 hours

**Outcome**: Entire backend follows constants best practices.

---

### Strategy C: Full Completion
**Complete Phases 9-19**
- **Effort**: 24-34 hours
- **Impact**: 100-120 instances
- **Result**: 100% completion
- **Benefit**: Entire codebase follows constants best practices

**Phases**:
1. Backend (Phases 9-18): 20-28 hours
2. Frontend (Phase 19): 4-6 hours

**Outcome**: Zero magic numbers in entire codebase.

---

## 📅 Suggested Timeline

### Week 1: High-Priority Backend (Strategy A)
**Monday-Tuesday**: Phase 9 (Alerts)
- Create constants module
- Migrate 2 files
- Test and commit

**Wednesday-Thursday**: Phase 10 (DLQ)
- Create constants module
- Migrate 1 file (complex SQL updates)
- Test retry logic
- Commit

**Friday**: Phase 11 (Auth)
- Create constants module
- Migrate 2 files
- Test security policies
- Commit

**Deliverable**: 93% completion, all critical constants extracted

---

### Week 2-3: Medium-Priority Backend (Strategy B extension)
**Days 6-7**: Phase 12 (API Pagination)
**Days 8-9**: Phase 13 (Corporate Actions)
**Days 10-12**: Phase 14 (Portfolio & Hedge)
**Day 13**: Phase 15 (Precision)
**Days 14-15**: Phase 16 (Data Quality)

**Deliverable**: 98% backend completion

---

### Week 4: Low-Priority Cleanup (Strategy B extension)
**Day 16**: Phase 17 (Network)
**Days 17-18**: Phase 18 (Stub Data)

**Deliverable**: Backend 100% complete

---

### Week 5: Frontend (Strategy C extension - OPTIONAL)
**Days 19-24**: Phase 19 (CSS Variables)

**Deliverable**: 100% overall completion

---

## 🧪 Testing Strategy

### Per-Phase Testing
After each phase migration:

1. **Syntax Validation**:
   ```bash
   python3 -m py_compile backend/app/core/constants/<module>.py
   python3 -m py_compile backend/app/services/<migrated_file>.py
   ```

2. **Import Testing**:
   ```python
   from app.core.constants.<module> import *
   # Verify all constants accessible
   ```

3. **Functional Testing**:
   - Run relevant service tests
   - Check numeric outputs match previous behavior
   - Verify edge cases (min/max values)

4. **Integration Testing**:
   - Start backend server
   - Test affected API endpoints
   - Verify error handling still works

---

### Regression Testing (End of Each Week)
After completing multiple phases:

1. **Full Test Suite**:
   ```bash
   pytest backend/tests/
   ```

2. **API Smoke Tests**:
   - Test all major endpoints
   - Verify authentication flow
   - Check alert creation/delivery
   - Test DLQ retry mechanism

3. **Manual Testing**:
   - Login/logout
   - Create portfolio
   - Generate alerts
   - Check error handling

---

## 🔄 Git Workflow

### Commit Strategy
**One commit per phase** (following Phases 1-8 pattern):

```bash
# Phase 9 example
git add backend/app/core/constants/alerts.py
git add backend/app/api/routes/alerts.py
git add backend/app/services/alert_delivery.py
git commit -m "$(cat <<'EOF'
Constants extraction Phase 9 - Alerts domain COMPLETE

Extracted alert and notification constants to improve maintainability.

**Changes**:
- Created backend/app/core/constants/alerts.py (5 constants)
- Migrated backend/app/api/routes/alerts.py (3 instances)
- Migrated backend/app/services/alert_delivery.py (1 instance)

**Constants**:
- DEFAULT_ALERT_COOLDOWN_HOURS = 24
- ALERT_DEDUP_LOOKBACK_HOURS = 24
- MAX_ALERT_COOLDOWN_HOURS = 8760
- ALERT_COOLDOWN_EXTENDED = 48
- ALERT_COOLDOWN_WEEKLY = 168

**Impact**: 8 magic numbers eliminated
**Testing**: ✅ All syntax checks passed
**Validation**: ✅ Alert cooldown functionality verified

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

### Branch Strategy (Optional)
For larger phases (14-16), consider feature branches:

```bash
git checkout -b constants-phase-14-portfolio
# Make changes
git commit -m "..."
git push origin constants-phase-14-portfolio
# Create PR for review
```

**Benefits**:
- Easier rollback if issues found
- Allows code review before merge
- Parallel work on multiple phases

**Drawback**:
- More complex workflow
- Potential merge conflicts

**Recommendation**: Use main branch (following Phases 1-8 pattern) unless team prefers PR workflow.

---

## 📊 Progress Tracking

### Completion Dashboard

| Phase | Domain | Status | Instances | Effort | Completion Date |
|-------|--------|--------|-----------|--------|-----------------|
| 1 | Financial | ✅ DONE | 15+ | 4h | Oct 2025 |
| 2 | Integration | ✅ DONE | 24+ | 6h | Oct 2025 |
| 3 | Risk | ✅ DONE | 9+ | 3h | Oct 2025 |
| 4 | Macro | ✅ DONE | 35+ | 5h | Nov 2025 |
| 5 | Scenarios | ✅ DONE | 30+ | 4h | Nov 2025 |
| 6 | Validation | ✅ DONE | 5+ | 2h | Nov 2025 |
| 7 | Infrastructure | ✅ DONE | 11+ | 3h | Nov 2025 |
| 8 | Network | ✅ DONE | 3+ | 2h | Nov 2025 |
| **9** | **Alerts** | ⏳ TODO | 8 | 3-4h | - |
| **10** | **DLQ** | ⏳ TODO | 6 | 3-4h | - |
| **11** | **Auth** | ⏳ TODO | 5 | 2-3h | - |
| 12 | API | ⏳ TODO | 7 | 2-3h | - |
| 13 | Corp Actions | ⏳ TODO | 5 | 2-3h | - |
| 14 | Portfolio | ⏳ TODO | 15 | 3-4h | - |
| 15 | Precision | ⏳ TODO | 6 | 2h | - |
| 16 | Data Quality | ⏳ TODO | 8 | 2-3h | - |
| 17 | Network Ext | ⏳ TODO | 2 | 1h | - |
| 18 | Stub Data | ⏳ TODO | 9 | 2h | - |
| 19 | CSS | ⏳ OPTIONAL | 30-40 | 4-6h | - |

**Current**: 176/200 (88%)
**After Phase 11**: 195/210 (93%)
**After Phase 18**: 246/250 (98%)
**After Phase 19**: 286/290 (99%)

---

## 🚨 Risk Assessment

### Low-Risk Phases (9-13, 17-18)
- Simple constant extraction
- No complex logic changes
- Well-defined constants
- Easy rollback if needed

**Mitigation**: Standard testing + syntax validation

---

### Medium-Risk Phases (14-16)
- Multiple files affected
- Complex calculations involved
- Numeric precision critical

**Mitigation**:
1. Extra testing of calculations
2. Compare before/after outputs
3. Feature flag for gradual rollout
4. Keep previous version for 1 week

---

### High-Risk Phase (19 - CSS)
- Visual changes affect entire UI
- Hard to test programmatically
- Potential browser compatibility issues

**Mitigation**:
1. Visual regression testing (screenshot comparison)
2. Test on multiple browsers
3. Feature flag for rollout
4. User acceptance testing

---

## 📝 Documentation Updates

After each phase, update:

1. **CONSTANTS_EXTRACTION_FINAL.md**
   - Update completion percentage
   - Add phase to completion list
   - Update statistics

2. **REFACTORING_PROGRESS.md**
   - Update Phase 7 status
   - Note new modules created
   - Link to commit

3. **Module README** (if needed)
   - Document new constants
   - Explain usage examples
   - Note migration from magic numbers

---

## ✅ Definition of Done

For each phase to be considered complete:

- [ ] Constants module created with comprehensive docstrings
- [ ] All magic numbers migrated to named constants
- [ ] Syntax validation passes (`python3 -m py_compile`)
- [ ] Import tests succeed
- [ ] Functional tests pass
- [ ] No regression in numeric outputs
- [ ] Git commit created with detailed message
- [ ] Changes pushed to remote
- [ ] Documentation updated
- [ ] Team notified of changes

---

## 💡 Best Practices Reminder

Based on Phases 1-8 success:

1. ✅ **One phase at a time** - Don't batch multiple phases
2. ✅ **Validate before commit** - Always run syntax checks
3. ✅ **Comprehensive docstrings** - Document sources and rationale
4. ✅ **Semantic naming** - `JWT_TOKEN_EXPIRY_HOURS` not `TOKEN_EXPIRY`
5. ✅ **Industry standards** - Cite OWASP, NIST, etc.
6. ✅ **Commit messages** - Include before/after examples
7. ✅ **Test thoroughly** - Verify numeric outputs unchanged
8. ✅ **Push immediately** - Don't accumulate unpushed commits

---

## 🎯 Success Criteria

### Minimum Success (Strategy A - Phases 9-11)
- ✅ 93% completion achieved
- ✅ All security constants documented
- ✅ All reliability constants extracted
- ✅ Zero syntax errors
- ✅ Zero regression bugs

---

### Full Success (Strategy B - Phases 9-18)
- ✅ 98% backend completion
- ✅ All backend magic numbers eliminated
- ✅ Professional constants architecture
- ✅ Comprehensive documentation
- ✅ Zero technical debt in backend

---

### Perfect Score (Strategy C - Phases 9-19)
- ✅ 99% overall completion
- ✅ Zero magic numbers in codebase
- ✅ CSS design system standardized
- ✅ Theme consistency achieved
- ✅ Industry best practices followed

---

## 📞 Communication Plan

### Weekly Status Updates
Send to team every Friday:

**Subject**: Constants Extraction - Week X Update

**Template**:
```
Phases Completed This Week: [9, 10, 11]
Instances Eliminated: 19
Total Completion: 93% (195/210)
Time Invested: 10 hours
Issues Encountered: None
Next Week Plan: [Phases 12-13]
```

---

### Phase Completion Notifications
After each phase commit:

**Template**:
```
✅ Constants Extraction Phase 9 (Alerts) - COMPLETE

- 8 magic numbers eliminated
- 2 files migrated
- Alert cooldown constants documented
- Commit: abc123f
- Testing: ✅ Passed

Next: Phase 10 (DLQ) starting tomorrow
```

---

## 🏁 Conclusion

**Recommended Approach**: Start with **Strategy A (Phases 9-11)** to achieve **93% completion** with all critical constants extracted. Then assess whether further work (Strategy B or C) provides sufficient ROI.

**Current Achievement**: The work already completed (Phases 1-8) represents **outstanding success** and covers all high-value business logic. Remaining phases are **incremental improvements**.

**Decision Point**: After Phase 11, evaluate:
- Is 93% completion sufficient?
- Does team have bandwidth for Phases 12-18? (11-17 additional hours)
- Is 100% completion (with CSS) worth 24-34 total hours?

---

**Plan Status**: Ready for execution
**Recommendation**: Start with Strategy A (High-Priority Only)
**Timeline**: 1 week (Phases 9-11)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
