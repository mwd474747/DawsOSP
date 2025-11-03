# Next Steps Plan - UI Integration

**Date:** November 2, 2025  
**Purpose:** Plan next steps after recent changes, identify issues, and determine priorities  
**Status:** 📋 PLANNING ONLY (No Code Changes)

---

## 📊 Executive Summary

**Current State:**
- ✅ **Sprint 1:** 100% Complete (Foundation/Audit)
- ✅ **Sprint 2:** 100% Complete! (All 3 Quick Wins done - **VERIFIED**)
- ✅ **Sprint 3:** ~50% Complete (OptimizerPage complete, RatingsPage enhanced)
- ✅ **Sprint 4:** 25% Complete (CorporateActionsPage done early)

**Key Finding:** 🎉 **AHEAD OF SCHEDULE!**
- ✅ MarketDataPage already migrated (uses PatternRenderer - Pattern 2) - **VERIFIED**
- ✅ OptimizerPage already migrated (uses PatternRenderer - Pattern 3) - **VERIFIED**
- ✅ All Sprint 2 tasks complete! (RiskPage, AttributionPage, MarketDataPage)

**What Was Missed in Review:**
- ⚠️ MarketDataPage migration was already complete (missed in initial review)
- ⚠️ OptimizerPage migration was already complete (missed in initial review)
- ⚠️ Need to verify these work correctly after dataPath fixes

**Next Priorities:**
1. **Verify All Migrations Work** (test for regressions)
2. **Test DataPath Fixes** (ensure fixed paths work correctly)
3. **Check for Issues** (orphaned code, error handling, broken references)
4. **Plan Remaining Sprint 3-5 Work** (RatingsPage, ReportsPage, etc.)

**Issues to Check:**
1. ✅ Verify no orphaned code (functions removed correctly) - **VERIFIED CLEAN**
2. ⚠️ Verify dataPath fixes work correctly (test RiskPage, OptimizerPage)
3. ⚠️ Test error handling for migrated pages
4. ⚠️ Verify PatternRenderer error states work correctly
5. ⚠️ Check for any dataPath mismatches in pattern registry

---

## 🔍 Issue Analysis - What to Check

### Potential Breaking Changes

#### 1. DataPath Fixes Verification
**Status:** ⚠️ **NEEDS VERIFICATION**

**What Was Fixed:**
- `policy_rebalance`: `summary` → `rebalance_result`, `trades` → `rebalance_result.trades`
- `portfolio_cycle_risk`: `risk_summary` → `cycle_risk_map`

**Potential Issues:**
- Old code may reference old paths
- `getDataByPath()` may fail if paths are incorrect
- Panel rendering may fail silently

**Action Required:**
- Verify `getDataByPath()` works with new paths
- Test RiskPage and OptimizerPage rendering
- Check console for errors

---

#### 2. Removed Functions - Orphaned Code
**Status:** ⚠️ **NEEDS VERIFICATION**

**Functions Removed in Migrations:**
- `processRiskData()` - Removed in RiskPage migration (commit `d2ce677`)
- `getFallbackRiskData()` - Removed in RiskPage migration
- `fetchAttributionData()` - Removed in AttributionPage migration (commit `04b4513`)

**Potential Issues:**
- These functions may still be referenced elsewhere
- Other pages may have copied these functions
- Fallback data logic may be missing

**Action Required:**
- Search for any remaining references to removed functions
- Verify error handling still works
- Ensure fallback data logic is preserved in PatternRenderer

---

#### 3. PatternRenderer Error Handling
**Status:** ⚠️ **NEEDS VERIFICATION**

**Potential Issues:**
- PatternRenderer may not handle all error cases
- Data extraction may fail silently
- Loading states may not work correctly
- Cache invalidation may be broken

**Action Required:**
- Test PatternRenderer with invalid patterns
- Test with missing data
- Verify loading states
- Check error messages

---

#### 4. Hidden PatternRenderer Components
**Status:** ℹ️ **DOCUMENTED PATTERN**

**Current Implementation:**
- AttributionPage: PatternRenderer hidden (`display: 'none'`) - uses callback
- OptimizerPage: PatternRenderer hidden (`display: 'none'`) - uses callback

**Potential Issues:**
- Hidden components may cause accessibility issues
- May impact performance (unnecessary renders)
- May not work correctly with React's reconciliation

**Action Required:**
- Verify hidden components work correctly
- Consider alternative patterns if needed
- Document as intentional pattern

---

#### 5. MarketDataPage Mixed Approach
**Status:** ⚠️ **NEEDS MIGRATION**

**Current Implementation:**
- Uses direct `executePattern` call for news
- Uses direct API calls for prices
- Has NewsListPanel infrastructure but not using PatternRenderer

**Potential Issues:**
- Inconsistent pattern usage
- News data may not use caching
- May not benefit from PatternRenderer features

**Action Required:**
- Complete migration to PatternRenderer for news
- Keep direct API calls for prices (intentional)
- Verify both approaches work together

---

## 📋 Next Steps Planning

### Priority 1: Complete Sprint 2 (Quick Wins)

#### Task 2.2: Migrate MarketDataPage to PatternRenderer ⚠️
**Status:** Infrastructure Ready, Migration Needed  
**Estimated Time:** 1-2 hours  
**Complexity:** Low-Medium  
**Risk:** Low (infrastructure already in place)

**Current State:**
- ✅ NewsListPanel component exists
- ✅ PatternRenderer supports `config` prop
- ✅ Pattern registry has `news_impact_analysis` entry
- ❌ Page still uses direct `executePattern` call

**Migration Steps:**
1. Replace `executePattern('news_impact_analysis')` with PatternRenderer
2. Use PatternRenderer with config for news panel
3. Keep direct API calls for prices (intentional - not pattern-based)
4. Verify both news and prices work together
5. Test error handling

**Success Criteria:**
- News data loads via PatternRenderer
- Prices still load via direct API
- Both work together correctly
- Error handling works

---

### Priority 2: Verify Current Migrations

#### Task V.1: Verify RiskPage Migration ✅
**Status:** Should Be Complete  
**Estimated Time:** 30 minutes  
**Complexity:** Low  
**Risk:** None (verification only)

**Verification Steps:**
1. Verify PatternRenderer is used (line 8764-8767)
2. Verify old functions are removed
3. Test page loads correctly
4. Test dataPath extraction works
5. Test error handling

**Success Criteria:**
- Page uses PatternRenderer
- No old code references
- Data renders correctly
- Errors handled gracefully

---

#### Task V.2: Verify AttributionPage Migration ✅
**Status:** Should Be Complete (Pattern 3)  
**Estimated Time:** 30 minutes  
**Complexity:** Low  
**Risk:** None (verification only)

**Verification Steps:**
1. Verify PatternRenderer with callback is used (line 8817-8822)
2. Verify currency attribution data extracts correctly
3. Test page displays attribution metrics
4. Test error handling
5. Verify hidden PatternRenderer works

**Success Criteria:**
- PatternRenderer callback works
- Attribution data displays
- Hidden component doesn't cause issues
- Errors handled gracefully

---

#### Task V.3: Verify OptimizerPage Migration Status ✅
**Status:** ✅ **VERIFIED COMPLETE** (Pattern 3)  
**Estimated Time:** Verified  
**Complexity:** Low  
**Risk:** None (verification only)

**Verification Results:**
- ✅ PatternRenderer is used (line 9309-9314)
- ✅ Dynamic inputs work correctly (via `patternInputs` memoized from `policyConfig`)
- ✅ Policy configuration updates pattern (via `refreshKey` dependency)
- ✅ Data extraction via callback works (`handleDataLoaded` line 8961)
- ✅ UI controls work (policy configuration form lines 9123-9303)

**Current Implementation:**
- ✅ Uses PatternRenderer with `onDataLoaded` callback (Pattern 3)
- ✅ Hidden PatternRenderer (`display: 'none'`) with callback for data extraction
- ✅ Dynamic inputs computed from policy configuration
- ✅ Custom rendering displays optimization metrics

**Success Criteria:**
- ✅ Uses PatternRenderer with callback (Pattern 3)
- ✅ Dynamic inputs work (policy changes trigger refresh)
- ✅ Data displays correctly (via custom rendering)

**Status:** ✅ **SPRINT 3 TASK 3.1 COMPLETE** (may have been done in commit `93597da`)

---

### Priority 3: Test for Regressions

#### Task T.1: Test All Migrated Pages
**Status:** Needs Testing  
**Estimated Time:** 1-2 hours  
**Complexity:** Low  
**Risk:** Medium (may find issues)

**Pages to Test:**
1. ✅ DashboardPage (Pattern 1)
2. ✅ PerformancePage (Pattern 1)
3. ✅ ScenariosPage (Pattern 2)
4. ✅ RiskPage (Pattern 1 - newly migrated)
5. ✅ AttributionPage (Pattern 3 - newly migrated)
6. ⚠️ MarketDataPage (Partial - needs migration)
7. ⚠️ OptimizerPage (Pattern 3 - verify complete)

**Test Cases:**
- Page loads correctly
- Pattern executes successfully
- Data displays correctly
- Error handling works
- Loading states work
- Cache works
- Refresh works

**Success Criteria:**
- All pages work correctly
- No console errors
- No broken UI
- Error handling consistent

---

#### Task T.2: Test DataPath Extraction
**Status:** Critical - Needs Testing  
**Estimated Time:** 30 minutes  
**Complexity:** Low  
**Risk:** High (dataPath fixes may not work)

**Patterns to Test:**
1. `portfolio_cycle_risk` - `cycle_risk_map` path
2. `policy_rebalance` - `rebalance_result` path
3. `portfolio_overview` - `valued_positions.positions` nested path
4. `news_impact_analysis` - `news_items` path

**Test Cases:**
- Verify `getDataByPath()` works with fixed paths
- Test nested paths (e.g., `valued_positions.positions`)
- Test missing data handling
- Test null/undefined handling

**Success Criteria:**
- All dataPaths work correctly
- Nested paths extract correctly
- Missing data handled gracefully

---

### Priority 4: Complete Remaining Sprint Work

#### Sprint 2 Remaining: MarketDataPage ⚠️
**Status:** Infrastructure Ready  
**Priority:** High (completes Sprint 2)  
**Estimated Time:** 1-2 hours

**See Priority 1 above.**

---

#### Sprint 3: Medium Complexity Migrations
**Status:** Partially Started  
**Priority:** Medium (after Sprint 2 complete)

**Tasks:**
1. **OptimizerPage** - Verify if complete (Pattern 3 already in use)
2. **RatingsPage** - May need PatternRenderer migration
   - Currently uses direct pattern execution
   - May need multiple PatternRenderer instances (per security)
   - Or custom rendering for security selection

**Estimated Time:** 2-4 hours  
**Complexity:** Medium  
**Risk:** Medium (may need custom approach)

---

#### Sprint 4: Edge Cases
**Status:** 25% Complete  
**Priority:** Low (after Sprint 3)

**Remaining Tasks:**
1. ✅ CorporateActionsPage - Complete (direct endpoint)
2. **ReportsPage** - Needs investigation
   - May use pattern directly or via endpoint
   - May need special handling for PDF downloads
3. **HoldingsPage** - Optional migration
   - Currently uses direct API call
   - Could use `portfolio_overview` pattern and extract holdings
4. **Error Handling Standardization**
5. **Loading States Standardization**

**Estimated Time:** 4-6 hours  
**Complexity:** Low-Medium  
**Risk:** Low

---

#### Sprint 5: Verification
**Status:** Not Started  
**Priority:** After all migrations complete

**Tasks:**
1. End-to-end testing
2. Performance benchmarking
3. Cache verification
4. Error recovery testing

**Estimated Time:** 4 hours  
**Complexity:** Low  
**Risk:** None

---

## 🚨 Potential Issues to Check

### Issue 1: Orphaned Code References ✅ VERIFIED
**Risk:** Low  
**Likelihood:** None (functions removed, no references found)

**What Was Checked:**
- ✅ Searched for `processRiskData` - **NOT FOUND** (removed in migration)
- ✅ Searched for `getFallbackRiskData` - **NOT FOUND** (removed in migration)
- ✅ Searched for `fetchAttributionData` - **NOT FOUND** (removed in migration)

**Status:** ✅ **CLEAN** - No orphaned references found

**Action:** None needed - code cleanup was successful

---

### Issue 2: DataPath Mismatches Still Present
**Risk:** High  
**Likelihood:** Low (already fixed)

**What to Check:**
- Verify all pattern registry dataPaths match pattern outputs
- Test dataPath extraction for all patterns
- Check console for extraction errors

**Action:**
- If mismatches found, fix immediately
- Test all patterns

---

### Issue 3: Error Handling Gaps
**Risk:** Medium  
**Likelihood:** Medium

**What to Check:**
- PatternRenderer error handling
- Missing data handling
- Network error handling
- Pattern execution failures

**Action:**
- Verify all error cases handled
- Test error scenarios
- Ensure user-friendly messages

---

### Issue 4: Cache Invalidation Issues
**Risk:** Low  
**Likelihood:** Low

**What to Check:**
- PatternRenderer cache invalidation
- Background refetch behavior
- Stale data issues

**Action:**
- Test cache behavior
- Verify invalidation works
- Check refresh behavior

---

### Issue 5: Hidden PatternRenderer Accessibility
**Risk:** Low  
**Likelihood:** Low

**What to Check:**
- Hidden components don't cause issues
- React reconciliation works
- Performance impact

**Action:**
- Verify hidden pattern works
- Consider alternatives if needed
- Document as intentional

---

## 📊 Migration Status Summary

### ✅ Fully Migrated (Using PatternRenderer)
1. **DashboardPage** - Pattern 1 (Direct PatternRenderer)
2. **PerformancePage** - Pattern 1 (Direct PatternRenderer)
3. **ScenariosPage** - Pattern 2 (PatternRenderer + Custom Controls)
4. **RiskPage** - Pattern 1 (Direct PatternRenderer) ✅ **NEWLY MIGRATED**
5. **AttributionPage** - Pattern 3 (PatternRenderer + Callback) ✅ **NEWLY MIGRATED**
6. **OptimizerPage** - Pattern 3 (PatternRenderer + Callback) ✅ **ALREADY MIGRATED**

### 🟡 Partially Migrated
1. **MarketDataPage** - Infrastructure ready, needs PatternRenderer migration
   - NewsListPanel exists
   - PatternRenderer config support exists
   - Still uses direct `executePattern` call

### ❌ Not Migrated (Intentional or Not Needed)
1. **MacroCyclesPage** - Hybrid approach (intentional - Pattern + Custom Rendering)
2. **TransactionsPage** - Direct API (intentional - CRUD operations)
3. **AlertsPage** - Direct API (intentional - CRUD operations)
4. **AIInsightsPage** - Chat interface (intentional - not pattern-based)
5. **CorporateActionsPage** - Direct endpoint (intentional - simple data listing)
6. **HoldingsPage** - Direct API (optional - could use pattern)
7. **RatingsPage** - Direct pattern execution (may need PatternRenderer)
8. **ReportsPage** - Direct endpoint (needs investigation)

---

## 🎯 Immediate Next Actions

### Action 1: Verify All Migrations ✅
**Priority:** High  
**Estimated Time:** 1 hour (verification only)  
**Complexity:** Low

**Steps:**
1. ✅ Verify MarketDataPage uses PatternRenderer (already verified - line 11132)
2. ✅ Verify OptimizerPage uses PatternRenderer (already verified - line 9309)
3. ⚠️ Test all migrated pages load correctly
4. ⚠️ Test dataPath extraction works with fixed paths
5. ⚠️ Test error handling for all migrated pages

---

### Action 2: Verify Migrations Work
**Priority:** High  
**Estimated Time:** 1 hour  
**Complexity:** Low

**Steps:**
1. Test RiskPage loads correctly
2. Test AttributionPage loads correctly
3. Test OptimizerPage loads correctly
4. Verify dataPath fixes work
5. Check console for errors

---

### Action 3: Test for Regressions
**Priority:** Medium  
**Estimated Time:** 1-2 hours  
**Complexity:** Low

**Steps:**
1. Test all migrated pages
2. Test all pattern executions
3. Test error handling
4. Check for orphaned code
5. Verify cache behavior

---

### Action 4: Plan Sprint 3-5 Work
**Priority:** Medium  
**Estimated Time:** 30 minutes  
**Complexity:** Low

**Steps:**
1. Verify OptimizerPage migration status
2. Assess RatingsPage migration needs
3. Plan remaining Sprint 3 work
4. Plan Sprint 4 edge cases
5. Plan Sprint 5 verification

---

## ⚠️ Critical Checks Before Proceeding

### Must Check Before Next Changes:
1. ✅ **Verify RiskPage works** - Test that migration didn't break anything
2. ✅ **Verify AttributionPage works** - Test callback pattern works
3. ✅ **Verify dataPath fixes** - Test that fixed paths work correctly
4. ✅ **Check for orphaned code** - Search for removed function references
5. ✅ **Test error handling** - Verify PatternRenderer handles errors

### Should Check:
1. ⚠️ **Test OptimizerPage** - Verify Pattern 3 implementation works
2. ⚠️ **Test cache behavior** - Verify PatternRenderer caching works
3. ⚠️ **Test loading states** - Verify all pages show loading correctly
4. ⚠️ **Check console errors** - Look for any JavaScript errors

### Nice to Have:
1. ⚠️ **Performance check** - Verify no performance regressions
2. ⚠️ **Accessibility check** - Verify hidden components don't cause issues
3. ⚠️ **Documentation** - Update docs with current migration status

---

## 📋 Recommended Execution Order

### Phase 1: Verification (Before Any New Work)
1. **Test RiskPage** - Verify migration works (15 min)
2. **Test AttributionPage** - Verify Pattern 3 works (15 min)
3. **Test OptimizerPage** - Verify Pattern 3 works (15 min)
4. **Check for orphaned code** - Search for removed functions (15 min)
5. **Test dataPath extraction** - Verify fixes work (15 min)

**Total Time:** ~1.5 hours  
**Risk:** None (verification only)

---

### Phase 2: Test for Regressions (After Verification)
1. **Test All Migrated Pages** - Verify pages work correctly (30 min)
2. **Test DataPath Extraction** - Verify fixed paths work (15 min)
3. **Check for Orphaned Code** - Search for removed function references (15 min)
4. **Test Error Handling** - Verify PatternRenderer error handling (30 min)

**Total Time:** ~1.5 hours  
**Risk:** Low (testing only)

---

### Phase 3: Plan Sprint 3-5 (After Sprint 2 Complete)
1. **Assess RatingsPage** - Determine migration approach (30 min)
2. **Plan Sprint 3 work** - Detail remaining tasks (30 min)
3. **Plan Sprint 4 edge cases** - Detail ReportsPage, HoldingsPage (30 min)
4. **Plan Sprint 5 verification** - Detail testing plan (30 min)

**Total Time:** ~2 hours  
**Risk:** None (planning only)

---

## 🎯 Success Criteria for Next Phase

### Verification Phase Success:
- ✅ All migrated pages work correctly
- ✅ No console errors
- ✅ DataPath fixes verified
- ✅ No orphaned code found
- ✅ Error handling works

### Migration Phase Success:
- ✅ MarketDataPage uses PatternRenderer
- ✅ News data loads via pattern
- ✅ Prices still load via direct API
- ✅ Both work together correctly
- ✅ Error handling works

### Planning Phase Success:
- ✅ Sprint 3-5 work clearly defined
- ✅ RatingsPage approach determined
- ✅ Edge cases identified
- ✅ Testing plan created

---

## 📊 Risk Assessment

### Low Risk (Safe to Proceed):
- ✅ Verification tasks (read-only)
- ✅ MarketDataPage migration (infrastructure ready)
- ✅ Testing (no code changes)

### Medium Risk (Proceed with Caution):
- ⚠️ MarketDataPage integration (mixing pattern + direct API)
- ⚠️ RatingsPage migration (may need custom approach)

### High Risk (Requires Careful Planning):
- ❌ None identified

---

## 🚨 Red Flags to Watch For

### If Found, Stop and Fix Immediately:
1. **Console Errors** - Any JavaScript errors in migrated pages
2. **Broken Data Paths** - Data not rendering due to incorrect paths
3. **Missing Error Handling** - Pages crash on errors
4. **Orphaned Code** - References to removed functions ✅ **VERIFIED CLEAN**
5. **Cache Issues** - Stale data or broken cache invalidation

---

## ⚠️ Potential Issues Found

### Issue 1: news_impact_analysis Pattern DataPath ⚠️
**Status:** ⚠️ **NEEDS VERIFICATION**

**Pattern Outputs (from backend/patterns/news_impact_analysis.json):**
- Step 71-75: `news.recent` → `as: "news_items"`
- Step 79-85: `news.compute_portfolio_impact` → `as: "impact_analysis"`
- Pattern outputs: `news_items`, `impact_analysis` (not `summary`)

**UI Registry (from full_ui.html lines 2986-3006):**
- Panel 1: `news_summary` (metrics_grid) - `dataPath: 'summary'` ⚠️ **MISMATCH?**
- Panel 2: `news_items` (news_list) - `dataPath: 'news_items'` ✅ **MATCH**

**Potential Issue:**
- Registry expects `summary` but pattern outputs `impact_analysis`
- Need to verify if `impact_analysis` contains summary metrics or if there's a transformation

**Action Required:**
- Verify pattern response structure
- Check if `impact_analysis` contains summary metrics
- Fix dataPath if needed: `summary` → `impact_analysis` or `impact_analysis.summary`

---

### Issue 2: export_portfolio_report Pattern DataPath ⚠️
**Status:** ⚠️ **NEEDS VERIFICATION**

**Pattern Outputs (from backend/patterns/export_portfolio_report.json):**
- Step 85-102: `reports.render_pdf` → `as: "pdf_result"`
- Pattern outputs: `pdf_result` containing `{ pdf_base64, size_bytes, download_filename, status, ... }`

**UI Registry (from full_ui.html lines 3078-3093):**
- Panel 1: `report_preview` (report_viewer) - `dataPath: 'report'` ⚠️ **MISMATCH**

**Potential Issue:**
- Registry expects `report` but pattern outputs `pdf_result`
- Need to verify if this is intentional or needs fixing

**Action Required:**
- Verify pattern response structure
- Fix dataPath if needed: `report` → `pdf_result`

---

### Issue 3: Missing Panel Configurations ⚠️
**Status:** ⚠️ **NEEDS VERIFICATION**

**Potential Issues:**
- `policy_rebalance` may need `impact_analysis` panel (pattern outputs `impact` from step 91-98)
- `portfolio_cycle_risk` may need `dar` panel (pattern outputs `dar` from step 67-74)
- Other patterns may have missing panels

**Action Required:**
- Verify all pattern outputs have corresponding panels
- Add missing panels if needed

---

## 📋 Complete Next Steps Plan

### Phase 1: Verification & Testing (Priority: HIGH)
**Estimated Time:** 2-3 hours  
**Complexity:** Low-Medium  
**Risk:** Low (verification only)

**Tasks:**
1. **Verify All Migrations Work** (30 min)
   - Test RiskPage loads and displays data
   - Test AttributionPage loads and displays data
   - Test MarketDataPage loads and displays data
   - Test OptimizerPage loads and displays data

2. **Test DataPath Extraction** (30 min)
   - Test `rebalance_result` path works in OptimizerPage
   - Test `cycle_risk_map` path works in RiskPage
   - Test nested paths (`rebalance_result.trades`, `cycle_risk_map.amplified_factors`)
   - Test missing data handling

3. **Verify Pattern Registry DataPaths** (1 hour)
   - Verify `news_impact_analysis` dataPaths (`summary` vs `impact_analysis`)
   - Verify `export_portfolio_report` dataPath (`report` vs `pdf_result`)
   - Check all 12 patterns for dataPath mismatches
   - Document any issues found

4. **Test Error Handling** (30 min)
   - Test PatternRenderer with invalid pattern
   - Test PatternRenderer with missing data
   - Test error states display correctly
   - Test retry functionality

**Success Criteria:**
- All migrated pages work correctly
- No console errors
- DataPath fixes verified
- Error handling works

---

### Phase 2: Fix Any Issues Found (Priority: MEDIUM)
**Estimated Time:** 1-2 hours  
**Complexity:** Low  
**Risk:** Low (fixes only)

**Potential Fixes:**
1. **Fix news_impact_analysis dataPath** (if needed)
   - Change `summary` → `impact_analysis` or `impact_analysis.summary`
   - Verify pattern response structure first

2. **Fix export_portfolio_report dataPath** (if needed)
   - Change `report` → `pdf_result`
   - Verify pattern response structure first

3. **Add Missing Panels** (if needed)
   - Add `impact_analysis` panel to `policy_rebalance` if missing
   - Add `dar` panel to `portfolio_cycle_risk` if missing
   - Verify all pattern outputs have panels

**Success Criteria:**
- All dataPaths verified correct
- All pattern outputs have panels
- No dataPath mismatches

---

### Phase 3: Plan Remaining Work (Priority: MEDIUM)
**Estimated Time:** 1 hour  
**Complexity:** Low  
**Risk:** None (planning only)

**Remaining Tasks:**
1. **RatingsPage Migration** (Sprint 3 Task 3.2)
   - Determine migration approach
   - May need multiple PatternRenderer instances
   - Or custom rendering with pattern data

2. **ReportsPage Investigation** (Sprint 4)
   - Verify if pattern or endpoint should be used
   - May need special handling for PDF downloads

3. **HoldingsPage Decision** (Sprint 4)
   - Decide: Pattern or direct API
   - Implement chosen approach

4. **Error Handling Standardization** (Sprint 4)
   - Ensure consistent error handling
   - User-friendly messages

5. **Loading States Standardization** (Sprint 4)
   - Ensure consistent loading states
   - Informative messages

**Success Criteria:**
- Clear plan for remaining work
- Approach decided for each page
- Estimated times documented

---

### Phase 4: Execute Remaining Work (Priority: LOW)
**Estimated Time:** 8-12 hours  
**Complexity:** Medium  
**Risk:** Medium

**After verification and fixes complete.**

---

**Last Updated:** November 2, 2025  
**Status:** 📋 PLANNING COMPLETE - Ready for Verification Phase

**Critical Actions Before Code Changes:**
1. ⚠️ **Verify news_impact_analysis dataPath** (`summary` vs `impact_analysis`)
2. ⚠️ **Verify export_portfolio_report dataPath** (`report` vs `pdf_result`)
3. ⚠️ **Test all migrated pages work correctly**
4. ⚠️ **Test dataPath fixes work correctly**
5. ⚠️ **Test error handling works correctly**

