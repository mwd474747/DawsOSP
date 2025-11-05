# Alpha Stability Plan - Database Architecture & Integration Analysis

**Date:** November 3, 2025  
**Purpose:** Understand what's necessary to finish integration and bring application to stable alpha  
**Status:** 📋 PLANNING ONLY (No Code Changes)

---

## 📊 Executive Summary

After comprehensive analysis of gaps, database architecture, and integration issues, I've identified **critical blockers** preventing alpha stability. The database architecture uses a **compute-first with optional storage** pattern, which is **intentional but creates complexity**. The core issues are **integration gaps**, not fundamental architecture problems.

**Key Finding:** The database design is **sound for the intended architecture**, but **integration layers** (API → UI, pattern → capability) have mismatches that prevent functionality from working.

**Alpha Stability Requirements:**
1. Fix pattern/capability return structure mismatches
2. Fix nested storage pattern causing data structure issues
3. Implement corporate actions properly (or remove mock endpoint)
4. Align field naming across layers
5. Complete metrics agent capability (return all fields)

---

## 🎯 Why Database Was Designed This Way

### Original Intent: Compute-First with Optional Storage

**Design Philosophy:**

1. **Performance Optimization Ready:**
   - Tables like `factor_exposures` and `currency_attribution` are **pre-created for future caching**
   - Services compute on-demand now (fast enough for alpha)
   - Can switch to caching later without schema changes

2. **TimescaleDB for Time-Series:**
   - Hypertables (`portfolio_daily_values`, `portfolio_metrics`, `macro_indicators`) optimize time-series queries
   - Automatic compression and retention policies
   - Efficient for historical analysis

3. **Reproducibility:**
   - `pricing_packs` ensure point-in-time consistency
   - All metrics stored with `pricing_pack_id` for auditability
   - Historical queries return same results

4. **Scalability:**
   - Compute-first allows adding portfolios without storage bloat
   - Can cache hot data when needed
   - Architecture supports both strategies

**Why This Makes Sense:**
- ✅ **Flexible** - Can switch compute/store strategy without code changes
- ✅ **Scalable** - No storage bloat for infrequently accessed data
- ✅ **Fast Development** - Don't need caching logic for alpha
- ✅ **Future-Proof** - Tables ready when optimization needed

---

## ⚠️ Is This Still The Best Design?

### Assessment: YES, But With Clarifications Needed

**Strengths:**
1. ✅ **Intentional Architecture** - Compute-first is appropriate for alpha
2. ✅ **Future Optimization Ready** - Tables exist for caching when needed
3. ✅ **TimescaleDB Benefits** - Hypertables provide real performance gains
4. ✅ **Reproducibility** - Pricing packs ensure consistency

**Weaknesses:**
1. ⚠️ **Unclear Intent** - Documentation doesn't explain compute vs store pattern
2. ⚠️ **Unused Tables** - Creates confusion about what's actually used
3. ⚠️ **No Decision Point** - When to switch to caching is undefined
4. ⚠️ **Resource Waste** - Tables created but never populated

**Recommendation:**
- ✅ **Keep Architecture** - It's sound for alpha and beyond
- ⚠️ **Document Intent** - Clearly explain compute-first with optional storage
- ⚠️ **Define Decision Point** - When will caching be implemented?
- ⚠️ **Remove Confusion** - Either use tables or document why they're unused

---

## 🔴 Critical Blockers for Alpha Stability

### Blocker 1: Pattern/Capability Return Structure Mismatch (CRITICAL)

**Issue:**
- Pattern JSON references `{{twr.total_return}}`, `{{twr.volatility}}`, `{{twr.sharpe}}`
- Capability result stored as `perf_metrics` (not `twr`)
- Agent returns `twr_ytd` (not `total_return`)
- Agent doesn't return `volatility`, `sharpe`, `max_drawdown`

**Impact:**
- ❌ Pattern presentation fails to resolve template variables
- ❌ UI metrics grid can't display values
- ❌ Dashboard shows no performance metrics

**Fix Required:**
1. Update agent to return all required fields: `volatility`, `sharpe`, `max_drawdown`
2. Fix pattern references: `{{perf_metrics.twr_ytd}}` instead of `{{twr.total_return}}`
3. Or: Change storage key to match pattern expectations

**Complexity:** LOW - Field mapping and pattern update
**Priority:** P0 - Blocks dashboard functionality

---

### Blocker 2: Nested Storage Pattern (HIGH)

**Issue:**
- Capability returns `{"historical_nav": [...]}`
- Orchestrator stores as `state["historical_nav"] = {"historical_nav": [...]}`
- Creates `data.historical_nav.historical_nav` double nesting
- UI had to be fixed to handle this pattern

**Impact:**
- ❌ Data structure confusion
- ❌ Frontend needs special handling
- ⚠️ Works but creates maintenance burden

**Fix Required:**
- Flatten orchestrator state storage
- Or: Document pattern and standardize frontend handling

**Complexity:** MEDIUM - Requires orchestrator changes and testing
**Priority:** P1 - Works but creates technical debt

---

### Blocker 3: Corporate Actions Mock Endpoint (MEDIUM)

**Issue:**
- `/api/corporate-actions` endpoint returns hardcoded mock data
- No database table for upcoming corporate actions
- Migration 008 only handles past dividends (via transactions table)

**Impact:**
- ❌ Feature appears to work but returns fake data
- ❌ User confusion about data accuracy
- ⚠️ Not core to alpha stability

**Fix Required:**
- Option A: Implement properly (create table, fetch data, rewrite endpoint)
- Option B: Remove endpoint to avoid confusion

**Complexity:** HIGH (Option A) or LOW (Option B)
**Priority:** P2 - Nice to have, not critical for alpha

---

### Blocker 4: Field Naming Inconsistency (MEDIUM)

**Issue:**
- Database: `qty_open`
- Service: `qty_open`
- API: `qty` or `quantity`
- UI: `quantity`

**Impact:**
- ⚠️ Confusion across layers
- ⚠️ Potential bugs from field name mismatches
- ✅ Currently works but fragile

**Fix Required:**
- Create standardized mapping layer at API boundary
- Or: Standardize on single naming convention

**Complexity:** MEDIUM - Requires mapping layer or refactoring
**Priority:** P2 - Works but creates technical debt

---

### Blocker 5: Missing Metrics Fields in Agent (CRITICAL)

**Issue:**
- `metrics_compute_twr()` queries database for metrics
- Only returns TWR fields (`twr_1d`, `twr_mtd`, `twr_ytd`, etc.)
- **Doesn't return**: `volatility`, `sharpe`, `max_drawdown`
- Database HAS these fields (`volatility_1y`, `sharpe_1y`, `max_drawdown_1y`)

**Impact:**
- ❌ UI expects `volatility`, `sharpe`, `max_drawdown` but doesn't get them
- ❌ Dashboard performance metrics incomplete

**Fix Required:**
- Update agent to extract and return `volatility`, `sharpe`, `max_drawdown` from database

**Complexity:** LOW - Just add field extraction
**Priority:** P0 - Blocks dashboard functionality

---

## 📋 What Complexity Is Needed vs Not Needed

### ✅ NEEDED Complexity

#### 1. Pattern Orchestrator (NEEDED)

**Why:**
- Enables declarative JSON-based workflows
- Allows pattern composition and reuse
- Supports agent capability routing

**Complexity Level:** Medium-High
**Value:** High - Core to application architecture
**Keep:** ✅ YES

---

#### 2. Pricing Packs (NEEDED)

**Why:**
- Ensures point-in-time reproducibility
- Critical for accurate historical analysis
- Enables auditability

**Complexity Level:** Medium
**Value:** High - Core feature for financial accuracy
**Keep:** ✅ YES

---

#### 3. Agent Capability System (NEEDED)

**Why:**
- Enables modular, testable capabilities
- Supports rights-based access control
- Allows capability reuse across patterns

**Complexity Level:** Medium-High
**Value:** High - Core to application architecture
**Keep:** ✅ YES

---

#### 4. TimescaleDB Hypertables (NEEDED)

**Why:**
- Optimizes time-series queries (portfolio_daily_values, portfolio_metrics)
- Automatic compression and retention
- Significant performance gains for historical analysis

**Complexity Level:** Low (PostgreSQL extension)
**Value:** High - Real performance benefits
**Keep:** ✅ YES

---

### ❌ NOT NEEDED Complexity

#### 1. Dual Storage Pattern (REMOVED ✅)

**Status:** Already removed in recent refactoring
**Why Removed:**
- Created confusion about template reference styles
- Doubled storage for every operation
- All patterns now use direct `{{foo}}` style

**Result:** ✅ Complexity reduced

---

#### 2. Unused Cache Tables (NOT NEEDED YET)

**Tables:** `factor_exposures`, `currency_attribution`
**Status:** Exist but unused (computed on-demand)

**Decision Needed:**
- **Option A:** Remove tables (reduce complexity, lose future optimization)
- **Option B:** Keep tables (future optimization ready, creates confusion)
- **Option C:** Document intent (keep tables but clarify why unused)

**Recommendation:** Option C (document intent) for alpha, decide on Option A/B later

**Complexity:** Low (just documentation) vs Medium (remove tables)

---

#### 3. Multiple Metrics Implementations (SIMPLIFY NEEDED)

**Current:** 4 different implementations:
1. `PerformanceCalculator.compute_twr()` - Used by patterns
2. `MetricsComputer.compute_portfolio_metrics()` - Comprehensive, stores in DB
3. `PerformanceSeeder.calculate_metrics()` - For seeding only
4. `populate_portfolio_metrics_simple.py` - Simple script

**Issue:** Inconsistency between implementations

**Fix Required:**
- **Option A:** Consolidate to single implementation
- **Option B:** Document which to use when (patterns vs batch vs seeding)

**Recommendation:** Option B for alpha (document), Option A for later (consolidate)

**Complexity:** High (consolidate) vs Low (document)

---

#### 4. Pattern Presentation Layer (QUESTIONABLE COMPLEXITY)

**Current:** Pattern JSON has both `display` and `presentation` sections
**Issue:** Duplication, unclear separation

**Decision:**
- **For Alpha:** Simplify to single display format
- **For Future:** May need both for flexibility

**Complexity:** Medium (simplify) vs Keep (future flexibility)

**Recommendation:** Keep for alpha, simplify later if not needed

---

## 🎯 Alpha Stability Requirements

### Core Features That Must Work

#### 1. Dashboard Rendering (CRITICAL)

**Requirements:**
- ✅ Portfolio overview page loads
- ✅ Performance metrics display (TWR, volatility, sharpe, max drawdown)
- ✅ Historical NAV chart renders
- ✅ Sector allocation chart renders
- ✅ Holdings table displays

**Current Status:**
- ⚠️ Metrics not displaying (agent missing fields)
- ⚠️ Charts may not render (nested storage issue)
- ✅ Holdings table works

**Fix Required:**
- Fix agent to return all metrics fields
- Fix pattern references
- Verify chart data structures

**Complexity:** LOW-MEDIUM
**Priority:** P0

---

#### 2. Pattern Execution (CRITICAL)

**Requirements:**
- ✅ Patterns execute without errors
- ✅ Capability results stored correctly
- ✅ Template references resolve
- ✅ API returns correct structure

**Current Status:**
- ⚠️ Pattern template references don't match storage keys
- ⚠️ Nested storage creates confusion
- ✅ Patterns execute but references fail

**Fix Required:**
- Align pattern references with capability return structures
- Fix nested storage pattern
- Standardize data flow

**Complexity:** MEDIUM
**Priority:** P0

---

#### 3. Data Integrity (CRITICAL)

**Requirements:**
- ✅ Portfolio valuations accurate
- ✅ FX rates correct
- ✅ Metrics calculations correct
- ✅ Historical data consistent

**Current Status:**
- ✅ FX rates fixed (CAD/USD, EUR/USD present)
- ✅ Pricing packs ensure reproducibility
- ✅ Metrics computed correctly (just not returned by agent)

**Fix Required:**
- Agent returns complete metrics
- No additional data integrity fixes needed

**Complexity:** LOW
**Priority:** P0

---

#### 4. Core Workflows (HIGH)

**Requirements:**
- ✅ View portfolio
- ✅ View holdings
- ✅ View performance metrics
- ✅ View charts

**Current Status:**
- ✅ View portfolio works
- ✅ View holdings works
- ⚠️ View performance metrics broken (agent missing fields)
- ⚠️ View charts may be broken (nested storage)

**Fix Required:**
- Fix agent metrics return
- Fix chart data structures

**Complexity:** LOW-MEDIUM
**Priority:** P1

---

## 🔧 Integration Work Needed

### Phase 1: Fix Critical Blockers (P0) - 8-12 hours

**Tasks:**
1. **Fix Agent Metrics Return** (2 hours)
   - Update `FinancialAnalyst.metrics_compute_twr()` to return `volatility`, `sharpe`, `max_drawdown`
   - Extract from database (`volatility_1y`, `sharpe_1y`, `max_drawdown_1y`)

2. **Fix Pattern References** (2 hours)
   - Update `portfolio_overview.json` to reference `{{perf_metrics.*}}` instead of `{{twr.*}}`
   - Update all pattern presentation references

3. **Verify Chart Data Structures** (2 hours)
   - Test `historical_nav` chart rendering
   - Test `sector_allocation` chart rendering
   - Fix data structure issues if found

4. **Integration Testing** (2-4 hours)
   - Test dashboard end-to-end
   - Verify all metrics display
   - Verify all charts render

**Result:** Dashboard fully functional

---

### Phase 2: Fix High Priority Issues (P1) - 4-8 hours

**Tasks:**
1. **Document Compute-First Architecture** (1 hour)
   - Update DATABASE.md to explain compute vs store pattern
   - Document why tables exist but aren't used
   - Clarify future optimization strategy

2. **Fix Nested Storage Pattern** (3-5 hours)
   - Flatten orchestrator state storage
   - Or: Document pattern and standardize frontend
   - Test all patterns after change

3. **Standardize Field Naming** (2 hours)
   - Create mapping layer at API boundary
   - Or: Standardize on single convention
   - Update UI expectations

**Result:** Technical debt reduced, architecture clarified

---

### Phase 3: Fix Medium Priority Issues (P2) - 4-6 hours

**Tasks:**
1. **Corporate Actions Decision** (1 hour)
   - Decide: Implement or remove
   - If remove: Remove mock endpoint
   - If implement: Create table, fetch data, rewrite endpoint (3-5 hours)

2. **Consolidate Metrics Implementations** (3-5 hours)
   - Document which implementation to use when
   - Or: Consolidate to single implementation
   - Test after changes

**Result:** Nice-to-have features completed or removed

---

## 🎯 Database Architecture Assessment

### Is Current Design Best? YES, with Clarifications

**Strengths:**
1. ✅ **Compute-first is appropriate for alpha** - Fast development, good enough performance
2. ✅ **TimescaleDB provides real value** - Hypertables optimize time-series queries
3. ✅ **Pricing packs ensure reproducibility** - Critical for financial accuracy
4. ✅ **Tables ready for future optimization** - Can switch to caching when needed

**Needs Clarification:**
1. ⚠️ **Document compute vs store pattern** - Why tables exist but aren't used
2. ⚠️ **Define decision point** - When will caching be implemented?
3. ⚠️ **Standardize usage** - Either use tables or document why not

**Recommendation:**
- ✅ **Keep architecture** - It's sound and appropriate
- ⚠️ **Document intent** - Explain compute-first with optional storage
- ⚠️ **For alpha:** Use compute-first (no caching logic needed)
- ⚠️ **For later:** Implement caching using existing tables when performance requires it

---

## 📊 Complexity Analysis

### Essential Complexity (Keep)

| Component | Complexity | Value | Reason |
|-----------|-----------|-------|--------|
| Pattern Orchestrator | High | High | Core to application architecture |
| Agent Capability System | Medium-High | High | Enables modular, testable capabilities |
| Pricing Packs | Medium | High | Ensures financial accuracy |
| TimescaleDB Hypertables | Low | High | Real performance benefits |
| Compute-First Pattern | Low | High | Appropriate for alpha, scalable for future |

**Total Essential Complexity:** Medium-High
**Justification:** Provides real value, core to application

---

### Unnecessary Complexity (Reduce)

| Component | Complexity | Value | Fix |
|-----------|-----------|-------|-----|
| Dual Storage (Removed ✅) | High | None | Already removed |
| Unused Cache Tables | Low | Future | Document intent |
| Multiple Metrics Implementations | Medium | Low | Document which to use |
| Pattern Presentation Duplication | Low | Questionable | Simplify later if not needed |

**Total Unnecessary Complexity:** Medium (after dual storage removal)
**Action:** Document intent, clarify usage

---

### Acceptable Complexity for Alpha

**For Alpha (MVP):**
- ✅ Compute-first pattern (no caching logic)
- ✅ Pattern orchestrator (core feature)
- ✅ Agent capabilities (modular design)
- ✅ Pricing packs (accuracy requirement)

**For Later (Post-Alpha):**
- ⚠️ Implement caching using existing tables
- ⚠️ Consolidate metrics implementations
- ⚠️ Simplify pattern presentation if not needed

**Philosophy:** 
- **Alpha = Simple, Functional**
- **Post-Alpha = Optimize, Consolidate**

---

## 🚀 Path to Alpha Stability

### Step 1: Fix Critical Blockers (Week 1)

**Goal:** Dashboard fully functional

**Tasks:**
1. Fix agent metrics return (add missing fields)
2. Fix pattern references (align with storage keys)
3. Verify chart rendering (fix data structures if needed)
4. Integration testing

**Time:** 8-12 hours
**Result:** Core functionality works

---

### Step 2: Clarify Architecture (Week 1-2)

**Goal:** Document intent, reduce confusion

**Tasks:**
1. Document compute-first with optional storage pattern
2. Explain why tables exist but aren't used
3. Define decision point for caching implementation
4. Update DATABASE.md with architecture explanation

**Time:** 4-6 hours
**Result:** Clear architecture documentation

---

### Step 3: Reduce Technical Debt (Week 2)

**Goal:** Fix high-priority issues

**Tasks:**
1. Fix nested storage pattern (flatten or document)
2. Standardize field naming (mapping layer or refactor)
3. Test all patterns after changes

**Time:** 6-10 hours
**Result:** Technical debt reduced

---

### Step 4: Polish (Week 2-3)

**Goal:** Nice-to-have features

**Tasks:**
1. Corporate actions decision (implement or remove)
2. Consolidate metrics implementations (document or consolidate)
3. Final integration testing

**Time:** 4-8 hours
**Result:** Alpha ready for users

---

## 📋 Summary

### Database Architecture: Sound, Needs Documentation

**Verdict:** ✅ **Current design is best for alpha**

**Why:**
- Compute-first is appropriate (fast enough, simpler)
- TimescaleDB provides real value
- Tables ready for future optimization
- Architecture is scalable

**Needs:**
- Documentation of intent (compute vs store)
- Clarification of unused tables (why they exist)

---

### Alpha Stability: 3 Critical Blockers

**Blockers:**
1. ❌ Agent missing metrics fields (volatility, sharpe, max_drawdown)
2. ❌ Pattern references don't match storage keys
3. ⚠️ Nested storage pattern creates confusion

**Complexity Needed:**
- ✅ Pattern orchestrator (essential)
- ✅ Agent capabilities (essential)
- ✅ Pricing packs (essential)
- ✅ TimescaleDB (essential)

**Complexity Not Needed:**
- ❌ Dual storage (already removed ✅)
- ⚠️ Unused cache tables (document intent)
- ⚠️ Multiple metrics implementations (document usage)

---

### Path Forward: 18-36 hours to Alpha Stability

**Phase 1 (P0):** Fix critical blockers - 8-12 hours
**Phase 2 (P1):** Clarify architecture - 4-6 hours
**Phase 3 (P1):** Reduce technical debt - 6-10 hours
**Phase 4 (P2):** Polish - 4-8 hours

**Total:** 18-36 hours (2-4 days focused work)

**Result:** Stable alpha with dashboard fully functional, architecture documented, technical debt reduced

---

**Status:** Plan complete. Database architecture is sound, needs documentation. Alpha stability requires fixing 3 critical blockers and clarifying architecture intent.

