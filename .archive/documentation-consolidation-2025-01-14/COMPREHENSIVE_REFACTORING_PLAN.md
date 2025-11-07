# Comprehensive Context-Heavy Refactoring Plan
# DawsOSP - Complete Technical Debt Resolution

**Date:** November 5, 2025
**Status:** 🎯 **READY FOR EXECUTION**
**Purpose:** Detailed implementation plan integrating all analysis findings with full context

---

## 📊 Executive Summary

**Current State:**
- ✅ **11 of 18 UI pages work** - Core functionality stable
- ⚠️ **1 UI page shows fake data** - Risk Analytics (critical trust issue)
- ⚠️ **1,240+ lines of zombie code** - Phase 3 consolidation remnants block fixes
- ⚠️ **FactorAnalyzer exists but unused** - 438 lines of real implementation ignored
- ⚠️ **4 patterns defined but unused** - Missing features or redundant

**Critical Path:**
```
Phase 0 (14h) → Phase 1 (16h) → Phase 2 (32h) → Phase 3 (16-48h) → Phase 4 (24h)
Zombie Cleanup   Emergency Fixes   Foundation      Features          Quality
```

**Total Timeline:** 102-134 hours (2.5-3.5 weeks)

**Key Discovery:** 🔥 FactorAnalyzer already implemented - might save 40 hours if it works!

---

## 🎯 Strategic Context

### Why This Plan Exists

**Historical Context:**
1. **Oct 2025:** Week 3/4 pattern optimization reduced 6 patterns from 2-step to 1-step
2. **Nov 2025:** Phase 3 agent consolidation (9 agents → 4 agents) left zombie code
3. **Nov 2025:** User updated 4 patterns to standard format during analysis
4. **Now:** Multiple reviews identified layered technical debt requiring systematic cleanup

**Problem Stack:**
```
Layer 1: User Trust Issues     ← Risk Analytics shows fake data
Layer 2: Zombie Code            ← Phase 3 consolidation incomplete
Layer 3: Pattern Inconsistency  ← 3 incompatible output formats
Layer 4: No Validation          ← Runtime errors, cryptic messages
Layer 5: Architecture Debt      ← Unused services, unclear patterns
```

**Why Layered Approach:**
- **Phase 0 unblocks everything** - Zombie code confuses developers
- **Phase 1 preserves trust** - Users see warnings on stub data
- **Phase 2 prevents regression** - Validation catches bugs early
- **Phase 3 delivers value** - Real features work properly
- **Phase 4 ensures quality** - Tests prevent future breakage

---

## 🧟 Phase 0: Zombie Code Removal (14 hours) ← **PREREQUISITE**

**Goal:** Remove Phase 3 consolidation remnants blocking all other work

**Why First:**
- Feature flags at 100% rollout (no gradual deployment happening)
- Capability mapping maps deleted agents (old agents gone)
- Runtime checks zombie code on EVERY capability call
- Developer confusion: "Why does this routing code exist?"
- Blocks Phase 1-4: Unclear which service to use, which flags matter

### Context: What is Zombie Code?

**Phase 3 Consolidation (Nov 2025):**
- Consolidated 9 agents → 4 agents (FinancialAnalyst, MacroHound, DataHarvester, ClaudeAgent)
- Created feature flags for gradual rollout
- Created capability mapping for old→new routing
- Started rollout, reached 100%
- **Never removed the scaffolding!**

**Result:** Production code checks flags/mappings that are effectively no-ops.

---

### Task 0.1: Remove Feature Flags System (2 hours)

**Files to Delete:**
- `backend/config/feature_flags.json` (104 lines)
- `backend/app/core/feature_flags.py` (345 lines)

**Files to Update:**
- `backend/app/core/agent_runtime.py`:
  - Lines 52-59: Remove optional feature_flags import
  - Lines 418-449: Remove flag checks in routing logic

**Context:**

**Feature Flags JSON Structure:**
```json
{
  "agent_consolidation": {
    "optimizer_to_financial": {"enabled": true, "rollout_percentage": 100},
    "ratings_to_financial": {"enabled": true, "rollout_percentage": 100},
    // ... 5 more flags, all at 100% or 0%
  },
  "experimental_features": {
    "advanced_risk_metrics": {"enabled": false},  // ← Might be relevant
    "real_time_pricing": {"enabled": false},
    "parallel_execution": {"enabled": false}
  }
}
```

**Why Remove:**
- All consolidation flags at 100% (rollout complete)
- `advanced_risk_metrics` disabled but FactorAnalyzer exists (check if related)
- No gradual rollout happening
- Runtime overhead checking these flags

**How Feature Flags Are Used:**
```python
# agent_runtime.py lines 418-449
if FEATURE_FLAGS_AVAILABLE and get_feature_flags is not None:
    flags = get_feature_flags()

    # Check unified consolidation flag first
    if flags.is_enabled("agent_consolidation.unified_consolidation", context):
        # Route to consolidated agent
        if target_agent in self.agents:
            routing_decision["override_agent"] = target_agent
            routing_decision["reason"] = "unified_consolidation_flag"
```

**Problem:** This runs on EVERY capability call, but:
- `unified_consolidation` is disabled (0%)
- Individual flags all at 100% (always enabled)
- Effectively a no-op with performance cost

**Deletion Steps:**
1. Remove feature_flags.py import (lines 52-59)
2. Remove flag checks from routing (lines 418-449)
3. Simplify routing to direct lookup (no flag checking)
4. Delete feature_flags.py file
5. Delete feature_flags.json file

**Testing:**
- Run all patterns before/after
- Verify routing still works (should be identical)
- Check for import errors

**Estimated Time:** 2 hours (including testing)

---

### Task 0.2: Remove Capability Mapping System (3 hours)

**Files to Delete:**
- `backend/app/core/capability_mapping.py` (752 lines)

**Files to Update:**
- `backend/app/core/agent_runtime.py`:
  - Lines 62-77: Remove optional capability_mapping import
  - Lines 410-417: Remove mapping lookup logic

**Context:**

**Capability Mapping Structure:**
```python
CAPABILITY_CONSOLIDATION_MAP = {
    "optimizer.propose_trades": {
        "target": "financial_analyst.propose_trades",
        "target_agent": "financial_analyst",
        "priority": 1,
        "risk_level": "high",
    },
    "ratings.dividend_safety": {
        "target": "financial_analyst.dividend_safety",
        "target_agent": "financial_analyst",
    },
    # ... 50+ more mappings
}
```

**Why This Exists:**
- Phase 3 consolidated agents
- Old capability names (optimizer.*, ratings.*) → New names (financial_analyst.*)
- Backward compatibility during migration

**Problem:**
- Old agents DELETED - no old capability names exist
- All patterns use NEW names already
- User updated 4 patterns during analysis (already using new format)
- Mapping is dead code

**Usage:**
```python
# agent_runtime.py lines 410-417
if CAPABILITY_MAPPING_AVAILABLE and get_target_agent is not None:
    consolidation_info = get_consolidation_info(capability)
    target_agent = consolidation_info.get("target_agent")

    if target_agent and target_agent != original_agent:
        # Route to consolidated agent
```

**Why Remove:**
- No patterns use old capability names
- Mapping always returns same agent (no routing change)
- 752 lines of unused complexity

**Deletion Steps:**
1. **Verify no old names in patterns:**
   ```bash
   grep -r "optimizer\." backend/patterns/
   grep -r "ratings\." backend/patterns/
   grep -r "charts\." backend/patterns/
   grep -r "reports\." backend/patterns/
   grep -r "alerts\." backend/patterns/
   ```
   Expected: No matches (all use new names)

2. Remove capability_mapping import (lines 62-77)
3. Remove mapping logic from routing (lines 410-417)
4. Delete capability_mapping.py file

**Testing:**
- Verify patterns still execute
- Check routing logs (should show direct routing)
- Run pattern test suite

**Estimated Time:** 3 hours (includes verification + testing)

---

### Task 0.3: Simplify AgentRuntime Routing (2 hours)

**File:** `backend/app/core/agent_runtime.py`

**Context:**

**Current Routing Logic (lines 400-449):**
```python
def _resolve_agent_for_capability(self, capability, original_agent, context):
    routing_decision = {...}

    # Check capability mapping (lines 410-417)
    if CAPABILITY_MAPPING_AVAILABLE:
        # ... 7 lines of mapping logic

    # Check feature flags (lines 418-449)
    if FEATURE_FLAGS_AVAILABLE:
        # ... 31 lines of flag logic

    return routing_decision
```

**After Phase 0:**
```python
def _resolve_agent_for_capability(self, capability, original_agent, context):
    # Direct routing - capability prefix determines agent
    # e.g., "financial_analyst.dividend_safety" → "financial_analyst"

    if "." in capability:
        agent_name = capability.split(".")[0]
        if agent_name in self.agents:
            return agent_name

    return original_agent  # Fallback to registered agent
```

**Why Simplify:**
- No more feature flags to check
- No more capability mapping to lookup
- Direct prefix-based routing (already how it works)
- ~80 lines removed from routing logic

**Changes:**
1. Remove conditional imports (lines 52-77)
2. Remove routing complexity (lines 410-449)
3. Implement simple prefix-based routing (10 lines)
4. Update routing logs (remove "unified_consolidation" messages)

**Testing:**
- All patterns should route identically
- Performance improvement (no flag/mapping lookups)
- Clearer logs

**Estimated Time:** 2 hours

---

### Task 0.4: Remove Duplicate Service (2 hours)

**Context:**

**Two Scenario Services:**
1. **ScenarioService** (`scenarios.py`, 33KB, 938 lines)
   - Base scenario stress testing
   - Used by: optimizer, alerts, macro_hound, API routes
   - **6 imports found**

2. **MacroAwareScenarioService** (`macro_aware_scenarios.py`, 43KB, 1064 lines)
   - Extends ScenarioService
   - Adds regime-aware scenario adjustments
   - **0 imports found** (only self-definition)

**Why Duplication Exists:**
- MacroAwareScenarioService was planned enhancement
- Wraps ScenarioService with regime adjustments
- Never integrated into agents/patterns
- Never removed after deciding not to use it

**Decision: Delete MacroAwareScenarioService**

**Why:**
- Zero usage in codebase
- Adds 43KB of unused complexity
- ScenarioService is sufficient for current needs
- Can restore from git if needed later

**Steps:**
1. **Verify no imports:**
   ```bash
   grep -r "MacroAwareScenarioService" backend/
   grep -r "macro_aware_scenarios" backend/
   ```
   Expected: Only self-references in macro_aware_scenarios.py

2. Delete `backend/app/services/macro_aware_scenarios.py`

3. Update `backend/app/services/__init__.py` if it imports the service

**Testing:**
- Verify no import errors
- Run scenario patterns (portfolio_scenario_analysis, etc.)
- Confirm all scenario functionality works

**Estimated Time:** 2 hours (includes verification)

---

### Task 0.5: Test FactorAnalyzer (2 hours) 🔥 **CRITICAL**

**Context:**

**Major Discovery:** Real factor analysis implementation exists but is unused!

**Files:**
- `backend/app/services/factor_analysis.py` (438 lines) - Real implementation
- `backend/app/agents/financial_analyst.py`:
  - Lines 1085-1126: `risk_compute_factor_exposures()` - Uses STUB data
  - Lines 1148-1154: `risk_get_factor_exposure_history()` - Uses REAL service

**Inconsistency:**
```python
# risk_compute_factor_exposures (line 1086)
logger.warning("Using fallback factor exposures - FactorAnalysisService not available")
result = {"factors": {"Real Rates": 0.5, ...}}  # HARDCODED

# risk_get_factor_exposure_history (line 1148)
from app.services.factor_analysis import FactorAnalysisService
factor_service = FactorAnalysisService()
current = await factor_service.compute_factor_exposure(...)  # REAL CALL
```

**Why This Matters:**
- Phase 3 assumes 40 hours to implement factor analysis
- But implementation ALREADY EXISTS in factor_analysis.py
- Just not wired up to `risk_compute_factor_exposures`

**FactorAnalyzer Implementation:**
```python
class FactorAnalyzer:
    async def compute_factor_exposure(self, portfolio_id, pack_id, lookback_days=252):
        # 1. Get portfolio returns from portfolio_daily_values table
        portfolio_returns = await self._get_portfolio_returns(...)

        # 2. Get factor returns from economic_indicators table (FRED data)
        factor_returns = await self._get_factor_returns(...)

        # 3. Run sklearn LinearRegression
        model = LinearRegression()
        model.fit(X, y)

        # 4. Return alpha, betas, R², factor attribution
        return {
            "alpha": float(model.intercept_),
            "beta": {factor: float(coef) for factor, coef in ...},
            "r_squared": float(model.score(X, y)),
            "factor_attribution": {...}
        }
```

**Dependencies:**
- `portfolio_daily_values` table - Need portfolio NAV history
- `economic_indicators` table - Need FRED factor data (DFII10, T10YIE, BAMLC0A0CM, DTWEXBGS, SP500)
- `sklearn` - Already in requirements

**Test Script:**
```python
# test_factor_analyzer.py
import asyncio
from app.services.factor_analysis import FactorAnalyzer
from app.db.connection import get_db_pool

async def test_factor_analyzer():
    db = await get_db_pool()
    analyzer = FactorAnalyzer(db)

    # Get real portfolio_id and pack_id from database
    portfolio_row = await db.fetchrow("SELECT portfolio_id FROM portfolios LIMIT 1")
    pack_row = await db.fetchrow("SELECT pack_id FROM pricing_packs ORDER BY asof_date DESC LIMIT 1")

    if not portfolio_row or not pack_row:
        print("❌ No portfolio or pricing pack found in database")
        return

    portfolio_id = str(portfolio_row["portfolio_id"])
    pack_id = str(pack_row["pack_id"])

    print(f"Testing with portfolio_id={portfolio_id}, pack_id={pack_id}")

    result = await analyzer.compute_factor_exposure(
        portfolio_id=portfolio_id,
        pack_id=pack_id,
        lookback_days=252
    )

    if "error" in result:
        print(f"\n⚠️  FactorAnalyzer returned error: {result['error']}")
        print("\nPossible causes:")
        print("  1. portfolio_daily_values table empty (no NAV history)")
        print("  2. economic_indicators table empty (no FRED data)")
        print("  3. Insufficient data (< 30 days)")
        print("\nNext steps:")
        print("  - Check portfolio_daily_values: SELECT COUNT(*) FROM portfolio_daily_values")
        print("  - Check economic_indicators: SELECT COUNT(*) FROM economic_indicators")
        print("  - If empty, Phase 3 needs to populate these tables")
    else:
        print("\n✅ FactorAnalyzer works! Use it instead of stub!")
        print(f"   R² = {result['r_squared']:.2%}")
        print(f"   Betas: {result['beta']}")
        print("\nNext steps:")
        print("  - Update risk_compute_factor_exposures to use FactorAnalyzer")
        print("  - Skip Phase 3 Option A (40h) and Option B (16h)")
        print("  - Save 16-40 hours!")

asyncio.run(test_factor_analyzer())
```

**Expected Outcomes:**

**Outcome 1: Works! (BEST CASE)**
```
✅ FactorAnalyzer works!
   R² = 0.85
   Betas: {'real_rate': -0.15, 'inflation': 0.05, ...}
```
**Action:** Wire it up in Phase 1, skip Phase 3 factor implementation (save 16-40 hours!)

**Outcome 2: Missing Data (LIKELY)**
```
⚠️ FactorAnalyzer returned error: Insufficient data
   portfolio_daily_values: 0 rows
   economic_indicators: 0 rows
```
**Action:** Add data population to Phase 3 (8 hours to backfill tables)

**Outcome 3: Implementation Incomplete (POSSIBLE)**
```
❌ Error: Module 'sklearn' has no attribute 'LinearRegression'
```
**Action:** Fix bugs, proceed with Phase 3 implementation as planned

**Steps:**
1. Create test script above
2. Run against production database
3. Check results
4. Document findings in ZOMBIE_CODE_VERIFICATION_REPORT.md

**Estimated Time:** 2 hours (includes test creation, execution, analysis)

**CRITICAL:** Do this BEFORE Phase 1 - might change Phase 3 entirely!

---

### Task 0.6: Update Documentation (3 hours)

**Files to Update:**
- `ARCHITECTURE.md` - Remove feature flag mentions
- `backend/app/core/README.md` - Update agent runtime docs
- `ZOMBIE_CODE_VERIFICATION_REPORT.md` - Add completion status

**Context:**

**Current Documentation Issues:**
- ARCHITECTURE.md references Phase 3 consolidation as "in progress"
- Mentions feature flags for gradual rollout
- Shows old capability routing flow
- Developer onboarding confusing

**Updates:**

**1. ARCHITECTURE.md**

Remove:
```markdown
### Agent Consolidation (Phase 3)

Feature flags enable gradual rollout:
- `agent_consolidation.optimizer_to_financial` - Route optimizer to FinancialAnalyst
- Rollout percentage controls gradual migration
```

Add:
```markdown
### Agent Architecture

Four agents handle all capabilities:
- **FinancialAnalyst**: Portfolio metrics, ratings, optimization, charts, risk
- **MacroHound**: Macro regime detection, cycles, scenarios, alerts
- **DataHarvester**: External data fetching, reports
- **ClaudeAgent**: AI-powered insights

Routing: Direct prefix-based (e.g., "financial_analyst.dividend_safety" → FinancialAnalyst)
```

**2. Agent Runtime Documentation**

Update routing flow diagram:
```
BEFORE (with zombie code):
Pattern → Orchestrator → AgentRuntime → Check Flags → Check Mapping → Route to Agent

AFTER (clean):
Pattern → Orchestrator → AgentRuntime → Direct Route → Agent
```

**3. Zombie Code Report**

Add completion section:
```markdown
## Phase 0 Completion

**Date:** [COMPLETION_DATE]
**Status:** ✅ COMPLETE

**Removed:**
- feature_flags.py (345 lines)
- feature_flags.json (104 lines)
- capability_mapping.py (752 lines)
- macro_aware_scenarios.py (1064 lines)
- Agent runtime zombie code (~80 lines)

**Total:** 2,345 lines removed

**Result:**
- Routing simplified
- No more consolidation flags
- No more capability mapping
- Developer onboarding clearer
- Phase 1-4 unblocked
```

**Estimated Time:** 3 hours

---

### Phase 0 Deliverables

**Code Removed:**
- `backend/config/feature_flags.json` (104 lines)
- `backend/app/core/feature_flags.py` (345 lines)
- `backend/app/core/capability_mapping.py` (752 lines)
- `backend/app/services/macro_aware_scenarios.py` (1064 lines)
- Agent runtime zombie code (~80 lines)

**Total Removed:** 2,345 lines

**Code Updated:**
- `backend/app/core/agent_runtime.py` - Simplified routing (~60 lines removed, ~10 added)
- `ARCHITECTURE.md` - Updated agent routing docs
- `ZOMBIE_CODE_VERIFICATION_REPORT.md` - Completion status

**Tests:**
- All patterns execute identically before/after
- No import errors
- Routing logs clearer
- Performance slightly improved (no flag/mapping lookups)

**Critical Discovery:**
- FactorAnalyzer test results documented
- Decision on Phase 3 factor analysis approach

**Time:** 14 hours total

---

## 🚨 Phase 1: Emergency Fixes (16 hours)

**Goal:** Stop user trust destruction immediately

**Prerequisites:** Phase 0 complete (zombie code removed)

**Why After Phase 0:**
- Zombie code removed, clearer which services to use
- FactorAnalyzer tested, know if stub is temporary or permanent
- Routing simplified, provenance tracking clearer

---

### Task 1.1: Add Provenance to Stub Data (4 hours)

**Context:**

**Current Problem:**
```python
# financial_analyst.py line 1086
async def risk_compute_factor_exposures(...):
    logger.warning("Using fallback factor exposures")  # ← Only in logs

    result = {
        "factors": {"Real Rates": 0.5, ...},  # HARDCODED
        "market_beta": 1.15,                   # HARDCODED
        # NO _provenance field!
    }
    return result
```

**User sees:** Plausible-looking numbers with no warning
**Reality:** Completely fake data
**Result:** If discovered, destroys user trust

**Orchestrator Already Handles Provenance:**
```python
# pattern_orchestrator.py lines 132-146
result_meta = result_raw.get("_provenance", {})
if result_meta.get("type") == "stub":
    warnings = result_meta.get("warnings", [])
    # Display warning banner in UI
```

**Fix:** Add `_provenance` to stub responses

---

**File 1: backend/app/agents/financial_analyst.py**

**Location:** `risk_compute_factor_exposures()` method (lines 1085-1126)

**Current Code:**
```python
async def risk_compute_factor_exposures(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    pack_id: Optional[str] = None,
) -> Dict[str, Any]:
    portfolio_id_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "risk.compute_factor_exposures")
    pack = self._resolve_pricing_pack_id(pack_id, ctx)

    logger.info(f"risk.compute_factor_exposures: portfolio_id={portfolio_id_uuid}, pack={pack}")

    # Use fallback data for factor exposures since FactorAnalysisService is not fully implemented
    logger.warning("Using fallback factor exposures - FactorAnalysisService not available")

    # Generate reasonable factor exposures based on portfolio
    result = {
        "portfolio_id": str(portfolio_id_uuid),
        "pack_id": str(pack) if pack else None,
        "timestamp": str(ctx.asof_date) if ctx.asof_date else None,
        "factors": {
            "Real Rates": 0.5,
            "Inflation": 0.3,
            "Credit": 0.7,
            "FX": 0.4,
            "Equity": 0.6,
            "market": 1.15,
            "size": 0.2,
            "value": -0.1,
            "momentum": 0.3
        },
        "portfolio_volatility": 0.185,
        "market_beta": 1.15,
        "equity_beta": 1.15,
        "r_squared": 0.82,
        "tracking_error": 0.045,
        "information_ratio": 0.67
    }

    return result
```

**Updated Code:**
```python
async def risk_compute_factor_exposures(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    pack_id: Optional[str] = None,
) -> Dict[str, Any]:
    portfolio_id_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "risk.compute_factor_exposures")
    pack = self._resolve_pricing_pack_id(pack_id, ctx)

    logger.info(f"risk.compute_factor_exposures: portfolio_id={portfolio_id_uuid}, pack={pack}")

    # PHASE 0 DECISION: Check if FactorAnalyzer test passed
    # If yes: Use real service (see Task 1.1 Option B)
    # If no: Use stub with provenance (this code)

    logger.warning("Using fallback factor exposures - FactorAnalysisService not available")

    result = {
        "portfolio_id": str(portfolio_id_uuid),
        "pack_id": str(pack) if pack else None,
        "timestamp": str(ctx.asof_date) if ctx.asof_date else None,
        "factors": {
            "Real Rates": 0.5,
            "Inflation": 0.3,
            "Credit": 0.7,
            "FX": 0.4,
            "Equity": 0.6,
            "market": 1.15,
            "size": 0.2,
            "value": -0.1,
            "momentum": 0.3
        },
        "portfolio_volatility": 0.185,
        "market_beta": 1.15,
        "equity_beta": 1.15,
        "r_squared": 0.82,
        "tracking_error": 0.045,
        "information_ratio": 0.67,

        # PHASE 1 FIX: Add provenance to prevent user trust issues
        "_provenance": {
            "type": "stub",
            "source": "fallback_stub_data",
            "confidence": 0.0,
            "implementation_status": "stub",
            "warnings": [
                "⚠️ Factor exposures are HARDCODED and not based on actual portfolio analysis",
                "⚠️ Values shown are placeholder data only",
                "⚠️ DO NOT use these numbers for investment decisions",
                "ℹ️ Real factor analysis implementation in progress"
            ],
            "recommendation": "Do not use for investment decisions",
            "next_steps": "Phase 3 will implement real factor analysis using portfolio returns and economic indicators",
            "issue_tracker": "See REFACTORING_MASTER_PLAN.md Phase 3"
        }
    }

    return result
```

**Changes:**
1. Added `_provenance` field with:
   - `type: "stub"` - Orchestrator checks this
   - `confidence: 0.0` - Zero confidence in data
   - `warnings: [...]` - User-visible warnings (displayed in UI banner)
   - `recommendation` - Clear guidance
   - `next_steps` - Transparency about roadmap

2. Comment references Phase 0 decision (use real service if test passed)

**Impact:**
- User sees warning banner: "⚠️ Factor exposures are HARDCODED..."
- Trust preserved (honest about limitations)
- Still shows data (UI doesn't break)
- Clear path to real implementation

---

**File 2: backend/app/agents/macro_hound.py**

**Location:** `macro_compute_dar()` method (need to verify if stub)

**First, Check if Stub:**
```bash
grep -A 20 "macro_compute_dar" backend/app/agents/macro_hound.py | grep -i "stub\|hardcoded\|fallback"
```

**If stub, add similar provenance:**
```python
"_provenance": {
    "type": "stub",
    "source": "fallback_stub_data",
    "confidence": 0.0,
    "implementation_status": "stub",
    "warnings": [
        "⚠️ Drawdown at Risk (DaR) is HARDCODED and not based on actual scenario analysis",
        "⚠️ Values shown are placeholder data only",
        "⚠️ DO NOT use these numbers for risk management decisions"
    ],
    "recommendation": "Do not use for investment decisions",
    "next_steps": "Phase 3 will implement real DaR using historical simulation"
}
```

**Context: What is DaR?**
- Drawdown at Risk - Maximum expected portfolio loss at confidence level
- Requires historical scenario simulation
- Current stub likely returns hardcoded percentage

---

**Testing:**

**Test 1: Orchestrator Extracts Provenance**
```python
# Run portfolio_cycle_risk pattern
result = await orchestrator.execute_pattern("portfolio_cycle_risk", {...})

# Check provenance extracted
assert "factor_exposures" in result
assert "_provenance" in result["factor_exposures"]
assert result["factor_exposures"]["_provenance"]["type"] == "stub"
```

**Test 2: UI Shows Warning Banner**
```javascript
// In full_ui.html or Next.js UI
const factorData = patternResult.factor_exposures;

if (factorData._provenance?.type === "stub") {
  // Show warning banner
  const warnings = factorData._provenance.warnings || [];
  return (
    <div className="alert alert-warning">
      <h4>⚠️ Data Quality Warning</h4>
      {warnings.map((w, i) => <p key={i}>{w}</p>)}
    </div>
  );
}
```

**Test 3: Risk Analytics Page**
- Navigate to Risk Analytics page
- Verify warning banner appears above charts
- Verify data still renders (doesn't break)
- Verify warnings are clear and actionable

**Estimated Time:** 4 hours (2 files + testing + UI verification)

---

### Task 1.2: Fix Pattern Output Extraction (4 hours)

**Context:**

**Problem:** Orchestrator extracts wrong data from capability responses

**Current Code:**
```python
# pattern_orchestrator.py lines 722-744
async def _extract_step_result(self, raw_result, step_name):
    # Format 1: {"data": {"panels": [...]}}
    if isinstance(raw_result, dict) and "data" in raw_result:
        return raw_result["data"]  # ← Extracts wrapped response, not actual data!

    # Format 2: {"factors": {...}}
    # Format 3: {"positions": [...]}
    return raw_result
```

**Issue:** When capability returns `{"data": {"panels": [...]}}`, orchestrator extracts `{"panels": [...]}` instead of step results.

**Example Failure:**
```python
# Pattern: portfolio_cycle_risk.json
# Step 1: risk.compute_factor_exposures
#   Returns: {"factors": {...}, "r_squared": 0.82}
#   Stored as: state["factor_exposures"] = {"factors": {...}, "r_squared": 0.82}  ✅

# Step 2: risk.overlay_cycle_phases (hypothetical bad capability)
#   Returns: {"data": {"panels": [...], "heatmap_data": [...]}}
#   Stored as: state["cycle_risk_map"] = {"panels": [...], "heatmap_data": [...]}  ❌
#   Should be: state["cycle_risk_map"] = {...}  (actual data, not wrapped)
```

**Root Cause:** Some capabilities wrap responses in `{"data": {...}}` format from older patterns.

---

**Analysis: Which Capabilities Return Wrapped Data?**

Need to grep agent methods:
```bash
# Find capabilities that return {"data": {...}}
grep -r "return {\"data\":" backend/app/agents/
grep -r "\"data\":" backend/app/agents/ | grep -i "return\|result"
```

**Expected Findings:**
- Old chart capabilities might wrap data
- Report generation might wrap data
- Most capabilities return direct data

---

**Fix Approach:**

**Option A: Unwrap at Orchestrator Level (SAFER)**
```python
async def _extract_step_result(self, raw_result, step_name):
    """
    Extract actual step result from capability response.

    Handles multiple response formats:
    - Direct: {"factors": {...}}
    - Wrapped: {"data": {"factors": {...}}}
    - Panels: {"data": {"panels": [...]}}
    """

    # If not a dict, return as-is (primitive values)
    if not isinstance(raw_result, dict):
        return raw_result

    # Extract provenance if present (preserve across formats)
    provenance = raw_result.get("_provenance")

    # Check for wrapped format
    if "data" in raw_result and len(raw_result) <= 2:  # Only "data" and maybe "_provenance"
        # Unwrap: {"data": {...}} → {...}
        extracted = raw_result["data"]

        # Preserve provenance
        if provenance and isinstance(extracted, dict):
            extracted["_provenance"] = provenance

        return extracted

    # Direct format - return as-is
    return raw_result
```

**Option B: Fix at Capability Level (CLEANER but more work)**
- Find all capabilities returning `{"data": {...}}`
- Update to return direct data
- More changes, higher risk

**Recommendation:** Option A (orchestrator-level fix)

---

**Implementation:**

**File:** `backend/app/core/pattern_orchestrator.py`

**Location:** `_extract_step_result()` method (lines 722-744)

**Updated Code:**
```python
async def _extract_step_result(self, raw_result: Any, step_name: str, capability: str) -> Any:
    """
    Extract actual step result from capability response.

    Handles multiple response formats:
    1. Direct: {"factors": {...}, "r_squared": 0.82}
    2. Wrapped: {"data": {"factors": {...}}, "_provenance": {...}}
    3. Primitive: "some_string" or 42 or ["list"]

    Always preserves _provenance metadata.

    Args:
        raw_result: Raw response from capability
        step_name: Step name for logging
        capability: Capability name for logging

    Returns:
        Extracted step result with provenance preserved
    """

    # Handle primitive values (strings, numbers, lists)
    if not isinstance(raw_result, dict):
        logger.debug(f"Step '{step_name}' ({capability}): primitive result type {type(raw_result)}")
        return raw_result

    # Extract provenance if present (must preserve across unwrapping)
    provenance = raw_result.get("_provenance")

    # Detect wrapped format: {"data": {...}, "_provenance": {...}}
    # Only unwrap if "data" is the primary content (max 2 keys including provenance)
    if "data" in raw_result:
        # Check if this is a wrapped response (minimal keys)
        other_keys = [k for k in raw_result.keys() if k not in ("data", "_provenance")]

        if len(other_keys) == 0:
            # This is wrapped format - unwrap
            logger.debug(f"Step '{step_name}' ({capability}): unwrapping 'data' envelope")
            extracted = raw_result["data"]

            # Preserve provenance in unwrapped result
            if provenance and isinstance(extracted, dict):
                extracted["_provenance"] = provenance

            return extracted
        else:
            # "data" is just one field among many - not wrapped format
            logger.debug(f"Step '{step_name}' ({capability}): direct result (has 'data' field)")
            return raw_result

    # Direct format - return as-is
    logger.debug(f"Step '{step_name}' ({capability}): direct result")
    return raw_result
```

**Changes:**
1. Better detection of wrapped vs direct format
2. Preserves provenance across unwrapping
3. Logs extraction decisions (helpful for debugging)
4. Handles edge cases (primitive values, mixed keys)

---

**Testing:**

**Test 1: Direct Format (No Change)**
```python
# Capability returns direct format
result = {"factors": {"Real Rates": 0.5}, "_provenance": {"type": "stub"}}

# Orchestrator extracts
extracted = await orchestrator._extract_step_result(result, "factor_exposures", "risk.compute_factor_exposures")

# Should be unchanged
assert extracted == result
assert extracted["_provenance"]["type"] == "stub"
```

**Test 2: Wrapped Format (Unwrapped)**
```python
# Capability returns wrapped format
result = {
    "data": {"factors": {"Real Rates": 0.5}},
    "_provenance": {"type": "real"}
}

# Orchestrator extracts
extracted = await orchestrator._extract_step_result(result, "factor_exposures", "risk.compute_factor_exposures")

# Should unwrap and preserve provenance
assert extracted == {"factors": {"Real Rates": 0.5}, "_provenance": {"type": "real"}}
```

**Test 3: Panels Format (Edge Case)**
```python
# Capability returns panels (should unwrap)
result = {"data": {"panels": [...], "charts": [...]}}

extracted = await orchestrator._extract_step_result(result, "charts", "financial_analyst.macro_overview_charts")

# Should unwrap
assert "panels" in extracted
assert "data" not in extracted
```

**Test 4: All Patterns Execute**
```bash
# Run all 13 patterns
python3 -m pytest backend/tests/test_patterns.py -v
```

**Estimated Time:** 4 hours (implementation + testing + edge cases)

---

### Task 1.3: Update Patterns to Standard Format (8 hours)

**Context:**

**Status Check:**
- ✅ User already updated 4 patterns during analysis:
  - `portfolio_cycle_risk.json` - ✅ List format
  - `portfolio_macro_overview.json` - ✅ List format
  - `macro_trend_monitor.json` - ✅ List format
  - `holding_deep_dive.json` - ✅ List format

**Still Need to Check:**
- `cycle_deleveraging_scenarios.json` - Check format
- `portfolio_scenario_analysis.json` - Check format
- Any other patterns with non-list outputs

**Standard Format:**
```json
{
  "id": "pattern_id",
  "outputs": ["step1_result", "step2_result", "step3_result"],
  "steps": [
    {"capability": "...", "as": "step1_result"},
    {"capability": "...", "as": "step2_result"},
    {"capability": "...", "as": "step3_result"}
  ]
}
```

---

**File 1: cycle_deleveraging_scenarios.json**

**Check Current Format:**
```bash
jq '.outputs' backend/patterns/cycle_deleveraging_scenarios.json
```

**Expected:** Either list format or needs update

**If needs update:**
```json
{
  "outputs": ["austerity", "default", "money_printing", "ranked_scenarios"],
  "steps": [
    {"capability": "scenarios.deleveraging_austerity", "as": "austerity"},
    {"capability": "scenarios.deleveraging_default", "as": "default"},
    {"capability": "scenarios.deleveraging_money_printing", "as": "money_printing"},
    {"capability": "scenarios.macro_aware_rank", "args": {...}, "as": "ranked_scenarios"}
  ]
}
```

---

**File 2: portfolio_scenario_analysis.json**

**Check Current Format:**
```bash
jq '.outputs' backend/patterns/portfolio_scenario_analysis.json
```

**Context:** This pattern was updated in Week 4 to use `portfolio.get_valued_positions`.

**Expected Structure:**
```json
{
  "outputs": ["valued_positions", "scenario", "hedge_suggestions"],
  "steps": [
    {"capability": "portfolio.get_valued_positions", "as": "valued_positions"},
    {"capability": "macro.run_scenario", "args": {...}, "as": "scenario"},
    {"capability": "financial_analyst.suggest_hedges", "args": {...}, "as": "hedge_suggestions"}
  ]
}
```

---

**Verification:**

**Check ALL patterns:**
```bash
# List all patterns and their output formats
for file in backend/patterns/*.json; do
  echo "=== $(basename $file) ==="
  jq '.outputs' "$file"
done
```

**Expected Output:**
```
=== portfolio_cycle_risk.json ===
["stdc", "ltdc", "factor_exposures", "cycle_risk_map", "dar"]

=== portfolio_macro_overview.json ===
["positions", "regime", "indicators", "factor_exposures", "dar", "charts"]

=== macro_trend_monitor.json ===
["regime_history", "factor_history", "trend_analysis", "alert_suggestions"]

=== holding_deep_dive.json ===
["position", "position_perf", "contribution", "currency_attr", "risk", "transactions", "fundamentals", "comparables"]

=== cycle_deleveraging_scenarios.json ===
[check if list]

=== portfolio_scenario_analysis.json ===
[check if list]
```

**Update any that are not list format.**

---

**Testing:**

**Test 1: Pattern Validation**
```python
# Validate all patterns load correctly
import json
import glob

for pattern_file in glob.glob("backend/patterns/*.json"):
    with open(pattern_file) as f:
        pattern = json.load(f)

    # Check outputs is list
    assert isinstance(pattern["outputs"], list), f"{pattern['id']}: outputs must be list"

    # Check all outputs referenced in steps
    step_names = [step["as"] for step in pattern["steps"]]
    for output in pattern["outputs"]:
        assert output in step_names, f"{pattern['id']}: output '{output}' not in steps"
```

**Test 2: Orchestrator Extraction**
```python
# Run patterns and verify outputs correct
for pattern_id in ["portfolio_cycle_risk", "cycle_deleveraging_scenarios", ...]:
    result = await orchestrator.execute_pattern(pattern_id, {...})

    # Check all expected outputs present
    pattern = load_pattern(pattern_id)
    for output_name in pattern["outputs"]:
        assert output_name in result, f"Missing output: {output_name}"
```

**Test 3: UI Rendering**
- Load Risk Analytics page (uses portfolio_cycle_risk)
- Load Scenarios page (uses cycle_deleveraging_scenarios)
- Verify data renders correctly
- Verify no "No data" errors

**Estimated Time:** 8 hours (check all patterns + updates + testing + UI verification)

---

### Phase 1 Deliverables

**Code Updated:**
1. `backend/app/agents/financial_analyst.py`:
   - `risk_compute_factor_exposures()` - Added `_provenance` field

2. `backend/app/agents/macro_hound.py`:
   - `macro_compute_dar()` - Added `_provenance` field (if stub)

3. `backend/app/core/pattern_orchestrator.py`:
   - `_extract_step_result()` - Fixed unwrapping logic

4. Pattern Files (2-4 patterns):
   - Standardized to list output format

**Documentation:**
- Updated REFACTORING_MASTER_PLAN.md with Phase 1 completion

**Tests:**
- Provenance extraction test
- UI warning banner test
- Pattern output extraction test
- All patterns execute successfully

**User Impact:**
- ✅ Risk Analytics shows warning banner
- ✅ Users know data is placeholder
- ✅ Trust preserved
- ✅ No "No data" errors

**Time:** 16 hours total

---

## 🏗️ Phase 2: Foundation (32 hours)

**Goal:** Prevent future issues, improve developer experience

**Prerequisites:** Phase 0 + Phase 1 complete

**Why After Phase 1:**
- Emergency fixed (users safe)
- Clean codebase (zombie code gone)
- Clear patterns (standard format)
- Can focus on developer experience

---

### Task 2.1: Create Capability Contracts (16 hours)

**Context:**

**Current Problem:** No clear contracts for capabilities

**Example Confusion:**
```python
# In pattern: risk.compute_factor_exposures
# What does it need? portfolio_id? pack_id? both?
# What does it return? factors? betas? r_squared?
# Does it fetch positions internally? Or expect them in state?
# Is it implemented or stub?
```

**Developer has to:**
1. Read capability code (1086-1126 lines deep)
2. Check all arg names
3. Check return structure
4. Hope nothing changed since docs were written

---

**Solution: Capability Decorators**

**Create decorator system:**
```python
# backend/app/core/capability_contract.py (NEW FILE)

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ImplementationStatus(Enum):
    """Implementation status of a capability."""
    COMPLETE = "complete"      # Fully implemented, production ready
    STUB = "stub"              # Returns placeholder data
    PARTIAL = "partial"        # Some features work, some stub
    EXPERIMENTAL = "experimental"  # Works but may change
    DEPRECATED = "deprecated"   # Old capability, use alternative


@dataclass
class CapabilityContract:
    """
    Contract defining a capability's interface and behavior.

    Used for:
    - Self-documenting code
    - Compile-time validation
    - Runtime type checking
    - Documentation generation
    """

    # Identity
    name: str                          # e.g., "risk.compute_factor_exposures"
    agent: str                         # e.g., "financial_analyst"
    description: str                   # Human-readable description

    # Interface
    inputs: Dict[str, type]            # e.g., {"portfolio_id": str, "pack_id": str}
    outputs: Dict[str, type]           # e.g., {"factors": dict, "r_squared": float}

    # Behavior
    implementation_status: ImplementationStatus = ImplementationStatus.COMPLETE
    fetches_positions: bool = False    # Does it query portfolio_positions internally?
    requires_pricing_pack: bool = False  # Does it need ctx.pricing_pack_id?
    modifies_data: bool = False        # Does it write to database?

    # Metadata
    version: str = "1.0.0"
    author: str = "DawsOS"
    created: str = ""
    updated: str = ""

    # Alternative capabilities
    deprecated_by: Optional[str] = None  # If deprecated, which capability replaces it?
    supersedes: Optional[List[str]] = field(default_factory=list)  # Which capabilities does this replace?

    # Performance
    avg_duration_ms: Optional[float] = None  # Average execution time
    cache_ttl_seconds: Optional[int] = None  # How long to cache results


# Global registry
_capability_contracts: Dict[str, CapabilityContract] = {}


def capability(
    name: str,
    description: str,
    inputs: Dict[str, type],
    outputs: Dict[str, type],
    implementation_status: ImplementationStatus = ImplementationStatus.COMPLETE,
    fetches_positions: bool = False,
    requires_pricing_pack: bool = False,
    modifies_data: bool = False,
) -> Callable:
    """
    Decorator to define a capability contract.

    Usage:
        @capability(
            name="risk.compute_factor_exposures",
            description="Compute factor exposures via multi-factor regression",
            inputs={"portfolio_id": str, "pack_id": str},
            outputs={"factors": dict, "r_squared": float},
            implementation_status=ImplementationStatus.STUB,
            requires_pricing_pack=True
        )
        async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
            ...
    """

    def decorator(func: Callable) -> Callable:
        # Extract agent name from function class
        agent_name = func.__qualname__.split(".")[0].lower() if "." in func.__qualname__ else "unknown"

        # Create contract
        contract = CapabilityContract(
            name=name,
            agent=agent_name,
            description=description,
            inputs=inputs,
            outputs=outputs,
            implementation_status=implementation_status,
            fetches_positions=fetches_positions,
            requires_pricing_pack=requires_pricing_pack,
            modifies_data=modifies_data
        )

        # Register
        _capability_contracts[name] = contract

        # Add contract to function metadata
        func.__capability_contract__ = contract

        # Log registration
        logger.info(f"Registered capability: {name} ({implementation_status.value})")

        return func

    return decorator


def get_contract(capability_name: str) -> Optional[CapabilityContract]:
    """Get contract for a capability."""
    return _capability_contracts.get(capability_name)


def list_contracts(agent: Optional[str] = None, status: Optional[ImplementationStatus] = None) -> List[CapabilityContract]:
    """List all contracts, optionally filtered."""
    contracts = list(_capability_contracts.values())

    if agent:
        contracts = [c for c in contracts if c.agent == agent]

    if status:
        contracts = [c for c in contracts if c.implementation_status == status]

    return contracts
```

---

**Apply to Capabilities:**

**Example 1: risk.compute_factor_exposures (STUB)**

```python
# backend/app/agents/financial_analyst.py

from app.core.capability_contract import capability, ImplementationStatus

class FinancialAnalyst(BaseAgent):

    @capability(
        name="risk.compute_factor_exposures",
        description="Compute portfolio factor exposures via multi-factor regression (5 factors: Real Rates, Inflation, Credit, FX, Equity)",
        inputs={
            "portfolio_id": str,  # Portfolio UUID (optional if in ctx)
            "pack_id": str        # Pricing pack UUID (optional if in ctx)
        },
        outputs={
            "factors": dict,      # Factor betas: {"Real Rates": 0.5, "Inflation": 0.3, ...}
            "r_squared": float,   # Model fit (0-1)
            "market_beta": float, # Overall market beta
            "_provenance": dict   # Provenance metadata
        },
        implementation_status=ImplementationStatus.STUB,  # ← BE HONEST
        requires_pricing_pack=True,
        fetches_positions=False  # ← Documents that it doesn't fetch (unlike old patterns)
    )
    async def risk_compute_factor_exposures(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        pack_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Implementation...
```

**Example 2: portfolio.get_valued_positions (COMPLETE)**

```python
@capability(
    name="portfolio.get_valued_positions",
    description="Week 4 abstraction: fetch positions + apply pricing in one step",
    inputs={
        "portfolio_id": str,
        "pack_id": str
    },
    outputs={
        "positions": list,     # List of valued positions
        "total_value": float,  # Portfolio total market value
        "count": int           # Number of positions
    },
    implementation_status=ImplementationStatus.COMPLETE,
    requires_pricing_pack=True,
    fetches_positions=True  # ← Abstracts ledger.positions + pricing.apply_pack
)
async def portfolio_get_valued_positions(self, ctx, state, portfolio_id, pack_id):
    # Implementation...
```

**Example 3: ledger.positions (COMPLETE)**

```python
@capability(
    name="ledger.positions",
    description="Fetch raw portfolio positions from ledger (no pricing)",
    inputs={
        "portfolio_id": str
    },
    outputs={
        "positions": list  # List of Position objects
    },
    implementation_status=ImplementationStatus.COMPLETE,
    modifies_data=False,
    fetches_positions=True
)
async def ledger_positions(self, ctx, state, portfolio_id):
    # Implementation...
```

---

**Apply to All Capabilities:**

**Count:** ~80 capabilities across 4 agents

**Estimated Time per Capability:** ~10 minutes
- Read capability code
- Identify inputs/outputs
- Check implementation status
- Add decorator

**Total:** 80 * 10min = 13.3 hours

---

**Generate Documentation:**

```python
# backend/scripts/generate_capability_docs.py (NEW FILE)

from app.core.capability_contract import list_contracts, ImplementationStatus
import json

def generate_markdown():
    """Generate capability reference documentation."""

    contracts = list_contracts()
    contracts.sort(key=lambda c: (c.agent, c.name))

    doc = ["# Capability Reference\n"]
    doc.append(f"**Total Capabilities:** {len(contracts)}\n")
    doc.append(f"**Generated:** {datetime.now().isoformat()}\n\n")

    # Group by agent
    by_agent = {}
    for contract in contracts:
        by_agent.setdefault(contract.agent, []).append(contract)

    for agent, agent_contracts in by_agent.items():
        doc.append(f"## {agent.title()} ({len(agent_contracts)} capabilities)\n\n")

        for contract in agent_contracts:
            # Capability header
            status_emoji = {
                ImplementationStatus.COMPLETE: "✅",
                ImplementationStatus.STUB: "⚠️",
                ImplementationStatus.PARTIAL: "🔶",
                ImplementationStatus.EXPERIMENTAL: "🧪",
                ImplementationStatus.DEPRECATED: "❌"
            }[contract.implementation_status]

            doc.append(f"### {status_emoji} `{contract.name}`\n\n")
            doc.append(f"**Description:** {contract.description}\n\n")

            # Inputs
            doc.append(f"**Inputs:**\n")
            for name, type_ in contract.inputs.items():
                doc.append(f"- `{name}`: {type_.__name__}\n")
            doc.append("\n")

            # Outputs
            doc.append(f"**Outputs:**\n")
            for name, type_ in contract.outputs.items():
                doc.append(f"- `{name}`: {type_.__name__}\n")
            doc.append("\n")

            # Behavior flags
            flags = []
            if contract.fetches_positions:
                flags.append("📊 Fetches positions internally")
            if contract.requires_pricing_pack:
                flags.append("💰 Requires pricing pack")
            if contract.modifies_data:
                flags.append("✏️ Modifies database")

            if flags:
                doc.append(f"**Behavior:** {', '.join(flags)}\n\n")

            # Implementation status
            doc.append(f"**Status:** {contract.implementation_status.value}\n\n")

            if contract.implementation_status == ImplementationStatus.STUB:
                doc.append(f"⚠️ **Warning:** This capability returns stub data. See `_provenance` field in response.\n\n")

            doc.append("---\n\n")

    return "".join(doc)

# Generate
markdown = generate_markdown()
with open("docs/reference/CAPABILITY_REFERENCE.md", "w") as f:
    f.write(markdown)

print("✅ Generated docs/reference/CAPABILITY_REFERENCE.md")
```

---

**Validation:**

```python
# backend/scripts/validate_capabilities.py (NEW FILE)

from app.core.capability_contract import list_contracts, ImplementationStatus

def validate_contracts():
    """Validate all capability contracts."""

    issues = []
    contracts = list_contracts()

    for contract in contracts:
        # Check: Stub capabilities must return _provenance
        if contract.implementation_status == ImplementationStatus.STUB:
            if "_provenance" not in contract.outputs:
                issues.append(
                    f"❌ {contract.name}: STUB capability must include '_provenance' in outputs"
                )

        # Check: Capabilities with pack_id input should set requires_pricing_pack=True
        if "pack_id" in contract.inputs and not contract.requires_pricing_pack:
            issues.append(
                f"⚠️ {contract.name}: Has 'pack_id' input but requires_pricing_pack=False"
            )

        # Check: Capabilities that fetch positions should document it
        if "positions" in contract.outputs and not contract.fetches_positions:
            issues.append(
                f"⚠️ {contract.name}: Returns 'positions' but fetches_positions=False"
            )

    if issues:
        print("\n".join(issues))
        return False
    else:
        print(f"✅ All {len(contracts)} capability contracts valid")
        return True

# Run validation
validate_contracts()
```

---

**Estimated Time Breakdown:**

| Task | Time |
|------|------|
| Create capability_contract.py | 2 hours |
| Apply decorators to 80 capabilities | 13 hours |
| Create documentation generator | 1 hour |
| Create validation script | 1 hour |
| Run validation, fix issues | 2 hours |
| Update ARCHITECTURE.md with contract system | 1 hour |

**Total:** 16 hours (might go faster if capabilities are simple)

---

### Task 2.2: Add Step Dependency Validation (8 hours)

**Context:**

**Current Problem:** Patterns can reference undefined steps

**Example:**
```json
{
  "steps": [
    {"capability": "ledger.positions", "as": "positions"},
    {"capability": "metrics.compute", "args": {
      "positions": "{{valued_positions.positions}}"  // ← UNDEFINED! Should be {{positions}}
    }}
  ]
}
```

**What happens:**
- Runtime error: `NoneType has no attribute 'positions'`
- Cryptic message
- Hard to debug
- Discovered only when pattern runs

---

**Solution: Pattern Validator**

**Create validator:**
```python
# backend/app/core/pattern_validator.py (NEW FILE)

from typing import Dict, List, Any, Set
import re
import json
import logging

logger = logging.getLogger(__name__)


class PatternValidationError(Exception):
    """Pattern validation error."""
    pass


class PatternValidator:
    """
    Validates pattern definitions before execution.

    Checks:
    - All step references exist
    - All capabilities are registered
    - Template variables reference valid steps
    - No circular dependencies
    - Input types match capability contracts
    """

    def __init__(self, capability_contracts: Dict[str, Any]):
        """
        Initialize validator.

        Args:
            capability_contracts: Capability contract registry
        """
        self.contracts = capability_contracts

    def validate_pattern(self, pattern: Dict[str, Any]) -> List[str]:
        """
        Validate a pattern definition.

        Args:
            pattern: Pattern JSON

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Extract pattern metadata
        pattern_id = pattern.get("id", "unknown")
        steps = pattern.get("steps", [])
        outputs = pattern.get("outputs", [])

        # Track available variables in state
        available_vars = {"inputs", "ctx"}  # Always available

        for idx, step in enumerate(steps):
            step_num = idx + 1
            capability = step.get("capability")
            step_name = step.get("as", f"step_{step_num}")
            args = step.get("args", {})

            # Validate capability exists
            if capability not in self.contracts:
                errors.append(
                    f"❌ Step {step_num} ({step_name}): "
                    f"Unknown capability '{capability}'"
                )

            # Validate template references in args
            for arg_name, arg_value in args.items():
                if isinstance(arg_value, str) and "{{" in arg_value:
                    # Extract template variables: {{foo.bar}} → ["foo"]
                    template_vars = re.findall(r'\{\{(\w+)', arg_value)

                    for var in template_vars:
                        if var not in available_vars:
                            errors.append(
                                f"❌ Step {step_num} ({step_name}): "
                                f"Argument '{arg_name}' references undefined variable '{var}'\n"
                                f"   Available: {sorted(available_vars)}"
                            )

            # Add this step's output to available vars
            available_vars.add(step_name)

        # Validate outputs reference existing steps
        for output in outputs:
            if output not in available_vars:
                errors.append(
                    f"❌ Output '{output}' not found in step results\n"
                    f"   Available: {sorted(available_vars - {'inputs', 'ctx'})}"
                )

        return errors

    def validate_capability_args(self, capability: str, args: Dict[str, Any]) -> List[str]:
        """
        Validate arguments against capability contract.

        Args:
            capability: Capability name
            args: Arguments to validate

        Returns:
            List of validation errors
        """
        errors = []

        if capability not in self.contracts:
            return [f"Unknown capability: {capability}"]

        contract = self.contracts[capability]
        required_inputs = contract.inputs

        # Check for missing required arguments
        for input_name, input_type in required_inputs.items():
            if input_name not in args:
                # Check if it might come from ctx or state (template)
                # For now, just warn
                logger.debug(f"Capability {capability}: missing arg '{input_name}' (might come from ctx)")

        # Check for unexpected arguments
        for arg_name in args.keys():
            if arg_name not in required_inputs:
                errors.append(
                    f"⚠️ Capability {capability}: unexpected argument '{arg_name}'\n"
                    f"   Expected: {list(required_inputs.keys())}"
                )

        return errors


def validate_all_patterns(patterns_dir: str = "backend/patterns") -> bool:
    """
    Validate all patterns in directory.

    Args:
        patterns_dir: Path to patterns directory

    Returns:
        True if all valid, False otherwise
    """
    from app.core.capability_contract import _capability_contracts

    validator = PatternValidator(_capability_contracts)

    all_valid = True

    for pattern_file in glob.glob(f"{patterns_dir}/*.json"):
        with open(pattern_file) as f:
            pattern = json.load(f)

        pattern_id = pattern.get("id", pattern_file)
        errors = validator.validate_pattern(pattern)

        if errors:
            print(f"\n❌ {pattern_id}:")
            for error in errors:
                print(f"  {error}")
            all_valid = False
        else:
            print(f"✅ {pattern_id}")

    return all_valid
```

---

**Integration with Orchestrator:**

```python
# backend/app/core/pattern_orchestrator.py

from app.core.pattern_validator import PatternValidator, PatternValidationError

class PatternOrchestrator:

    def __init__(self, agent_runtime, capability_contracts):
        self.agent_runtime = agent_runtime
        self.validator = PatternValidator(capability_contracts)

    async def execute_pattern(self, pattern_id, inputs):
        # Load pattern
        pattern = self.load_pattern(pattern_id)

        # VALIDATE BEFORE EXECUTION
        errors = self.validator.validate_pattern(pattern)
        if errors:
            error_msg = f"Pattern validation failed for '{pattern_id}':\n" + "\n".join(errors)
            logger.error(error_msg)
            raise PatternValidationError(error_msg)

        # Execute (now safe)
        return await self._execute_steps(pattern, inputs)
```

---

**CLI Tool:**

```bash
# backend/scripts/lint_patterns.py (NEW FILE)

#!/usr/bin/env python3
"""
Pattern linter - validates all patterns before deployment.

Usage:
    python3 scripts/lint_patterns.py
    python3 scripts/lint_patterns.py --pattern portfolio_overview
"""

import argparse
from app.core.pattern_validator import validate_all_patterns

def main():
    parser = argparse.ArgumentParser(description="Validate pattern definitions")
    parser.add_argument("--pattern", help="Specific pattern to validate")
    parser.add_argument("--patterns-dir", default="backend/patterns", help="Patterns directory")

    args = parser.parse_args()

    if args.pattern:
        # Validate single pattern
        pattern_file = f"{args.patterns_dir}/{args.pattern}.json"
        # ... validate single
    else:
        # Validate all
        valid = validate_all_patterns(args.patterns_dir)

        if valid:
            print("\n✅ All patterns valid")
            exit(0)
        else:
            print("\n❌ Some patterns have errors")
            exit(1)

if __name__ == "__main__":
    main()
```

**Make executable:**
```bash
chmod +x backend/scripts/lint_patterns.py
```

---

**CI/CD Integration:**

```yaml
# .github/workflows/validate-patterns.yml (NEW FILE)

name: Validate Patterns

on:
  pull_request:
    paths:
      - 'backend/patterns/**'
      - 'backend/app/agents/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Validate patterns
        run: |
          cd backend
          python3 scripts/lint_patterns.py

      - name: Validate capability contracts
        run: |
          cd backend
          python3 scripts/validate_capabilities.py
```

---

**Estimated Time Breakdown:**

| Task | Time |
|------|------|
| Create pattern_validator.py | 3 hours |
| Integrate with orchestrator | 1 hour |
| Create CLI tool | 1 hour |
| Set up CI/CD workflow | 1 hour |
| Test all patterns | 2 hours |

**Total:** 8 hours

---

### Task 2.3: Build Pattern Linter CLI (Already Done in 2.2!)

**This task merged into Task 2.2** - The pattern linter CLI was created as part of step dependency validation.

**No additional time needed.**

---

### Phase 2 Deliverables

**New Files:**
- `backend/app/core/capability_contract.py` (300 lines) - Contract system
- `backend/app/core/pattern_validator.py` (250 lines) - Pattern validation
- `backend/scripts/generate_capability_docs.py` (150 lines) - Doc generator
- `backend/scripts/validate_capabilities.py` (100 lines) - Contract validator
- `backend/scripts/lint_patterns.py` (100 lines) - Pattern linter CLI
- `.github/workflows/validate-patterns.yml` - CI/CD validation
- `docs/reference/CAPABILITY_REFERENCE.md` (generated) - Full capability docs

**Code Updated:**
- All 80 capabilities across 4 agents - Added `@capability` decorators
- `backend/app/core/pattern_orchestrator.py` - Integrated validation
- `backend/app/core/agent_runtime.py` - Pass contracts to orchestrator

**Documentation:**
- `ARCHITECTURE.md` - Added capability contract system section
- `CAPABILITY_REFERENCE.md` - Auto-generated from contracts

**CI/CD:**
- GitHub Actions workflow validates patterns on PR
- Pre-commit hook runs pattern linter

**Developer Experience:**
- ✅ Self-documenting capabilities (decorators show contracts)
- ✅ Clear error messages (validation explains exactly what's wrong)
- ✅ Compile-time validation (catch errors before runtime)
- ✅ Generated documentation (always up-to-date)

**Time:** 32 hours total (16h contracts + 8h validation + 8h linter merged)

---

## 🚀 Phase 3: Feature Implementation (16-48 hours)

**Goal:** Make Risk Analytics work with real data

**Prerequisites:** Phase 0 + Phase 1 + Phase 2 complete

**Critical Decision Point:** Phase 0 Task 0.5 test results determine approach

---

### Decision Tree

```
Did FactorAnalyzer test pass? (Phase 0 Task 0.5)
│
├─ YES (✅ Works!)
│  └─ Execute Option D: Wire Up Existing Service (2 hours)
│     → SAVES 38-46 HOURS! 🎉
│
├─ NO - Missing Data (⚠️ Likely)
│  └─ Execute Option E: Populate Data + Wire Up (10 hours)
│     → Still saves 28-36 hours!
│
└─ NO - Implementation Broken (❌ Unlikely)
   ├─ Option A: Implement from Scratch (40 hours)
   ├─ Option B: Use External Library (16 hours) ← Recommended
   └─ Option C: Keep Stub (0 hours, but Risk Analytics stays broken)
```

---

### Option A: Implement Real Factor Analysis from Scratch (40 hours)

**When to Use:** FactorAnalyzer test failed AND you want full control

**Context:**

**Factor Analysis Model:**
```
r_portfolio(t) = α + β₁·RealRate(t) + β₂·Inflation(t) + β₃·Credit(t) + β₄·USD(t) + β₅·ERP(t) + ε(t)

Where:
- r_portfolio = Daily portfolio return
- RealRate = 10Y TIPS yield (FRED: DFII10)
- Inflation = Breakeven inflation (FRED: T10YIE)
- Credit = IG corp spread (FRED: BAMLC0A0CM)
- USD = Dollar index (FRED: DTWEXBGS)
- ERP = Equity risk premium (S&P 500 - risk-free)
- α = Alpha (excess return)
- β = Factor betas (sensitivities)
- ε = Idiosyncratic return
```

**Implementation Plan:**

**Step 1: Data Collection (8 hours)**
- Fetch FRED data via existing FREDProvider
- Store in `economic_indicators` table
- Create indices for fast querying
- Backfill 2+ years of history

**Step 2: Portfolio Returns Calculation (8 hours)**
- Query `portfolio_daily_values` table
- Calculate daily returns
- Handle cash flows (use TWR methodology)
- Store results efficiently

**Step 3: Factor Returns Calculation (8 hours)**
- Convert FRED levels to returns
- Align dates with portfolio returns
- Handle missing data (interpolation)
- Compute equity risk premium

**Step 4: Regression Implementation (8 hours)**
- Use sklearn LinearRegression
- Run multi-factor regression
- Extract alpha, betas, R²
- Compute residual volatility

**Step 5: Factor Attribution (4 hours)**
- Compute factor contributions (β × factor_return)
- Decompose total return
- Create visualizations

**Step 6: Testing & Validation (4 hours)**
- Unit tests for each component
- Integration test with real portfolio
- Validate R² > 0.7 for equity portfolios
- Compare to benchmarks

**Total:** 40 hours

**Pros:**
- Full control over implementation
- No external dependencies
- Can customize to specific needs

**Cons:**
- Most time-consuming
- Requires deep financial knowledge
- More code to maintain

**Recommendation:** Only if Options D/E fail and you need custom implementation

---

### Option B: Use External Library (16 hours) ← **RECOMMENDED IF FACTORALYZER FAILS**

**When to Use:** FactorAnalyzer test failed AND you want speed

**Libraries:**

**1. empyrical (Quantopian)**
- Portfolio performance metrics
- Sharpe, Sortino, Calmar ratios
- Drawdown analysis
- Factor attribution

**2. pyfolio (Quantopian)**
- Complete portfolio analytics
- Factor model analysis
- Risk decomposition
- Visualization

**3. QuantLib**
- Advanced quantitative finance
- Risk metrics
- Factor models

**Recommendation:** **pyfolio** - most comprehensive

---

**Implementation with pyfolio:**

**Step 1: Install Library (1 hour)**
```bash
pip install pyfolio empyrical matplotlib seaborn
```

**Step 2: Data Preparation (4 hours)**
```python
# backend/app/services/factor_analysis_pyfolio.py (NEW FILE)

import pyfolio as pf
import empyrical as ep
import pandas as pd
from datetime import date, timedelta

class PyfolioFactorAnalyzer:
    """Factor analysis using pyfolio library."""

    async def compute_factor_exposure(self, portfolio_id, pack_id, lookback_days=252):
        # 1. Get portfolio returns
        portfolio_returns = await self._get_portfolio_returns(portfolio_id, lookback_days)

        # 2. Get factor returns (Fama-French or custom)
        factor_returns = await self._get_factor_returns(lookback_days)

        # 3. Convert to pandas Series/DataFrame
        returns_series = pd.Series(portfolio_returns, name='portfolio')
        factors_df = pd.DataFrame(factor_returns)

        # 4. Run factor analysis
        # pyfolio provides create_returns_tear_sheet, perf_stats, etc.
        factor_exposures = pf.timeseries.perf_attrib(
            returns=returns_series,
            factor_returns=factors_df,
            factor_exposures=None  # Will be computed
        )

        # 5. Extract results
        return {
            "alpha": float(factor_exposures["alpha"]),
            "beta": {
                factor: float(factor_exposures["factor_exposures"][factor])
                for factor in factors_df.columns
            },
            "r_squared": float(factor_exposures["r_squared"]),
            "specific_return": float(factor_exposures["specific_returns"].mean()),
            "_provenance": {
                "type": "real",
                "source": "pyfolio",
                "library_version": pf.__version__,
                "confidence": 0.95
            }
        }
```

**Step 3: Integration (4 hours)**
- Update `risk_compute_factor_exposures` to use PyfolioFactorAnalyzer
- Remove stub data
- Add real provenance

**Step 4: Testing (4 hours)**
- Test with real portfolios
- Validate results
- Compare to expected values

**Step 5: Documentation (3 hours)**
- Update CAPABILITY_REFERENCE.md
- Add pyfolio to requirements.txt
- Document factor model

**Total:** 16 hours

**Pros:**
- Fast implementation
- Well-tested library
- Industry standard

**Cons:**
- External dependency
- Less control over calculations
- Might not match exact factor definitions

**Recommendation:** Best balance of speed and quality if FactorAnalyzer fails

---

### Option C: Keep Stub with Warning (0 hours)

**When to Use:** Deprioritizing Risk Analytics feature

**Already done in Phase 1** - Added provenance warnings

**Impact:**
- Risk Analytics shows stub data
- Users see warning banner
- Trust preserved (honest about limitations)
- But feature not functional

**Recommendation:** Only if time-constrained and Risk Analytics not critical

---

### Option D: Wire Up Existing FactorAnalyzer (2 hours) 🔥 **BEST CASE**

**When to Use:** Phase 0 Task 0.5 test passed! FactorAnalyzer works!

**Context:**

FactorAnalyzer EXISTS in `backend/app/services/factor_analysis.py` (438 lines) and test showed it works.

**Implementation:**

**File:** `backend/app/agents/financial_analyst.py`

**Current (Stub):**
```python
async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
    logger.warning("Using fallback factor exposures - FactorAnalysisService not available")

    result = {
        "factors": {"Real Rates": 0.5, ...},  # HARDCODED
        "_provenance": {"type": "stub", ...}
    }
    return result
```

**Updated (Real):**
```python
async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
    portfolio_id_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "risk.compute_factor_exposures")
    pack = self._resolve_pricing_pack_id(pack_id, ctx)

    logger.info(f"risk.compute_factor_exposures: portfolio_id={portfolio_id_uuid}, pack={pack}")

    # PHASE 3: Use real FactorAnalyzer (Phase 0 test confirmed it works!)
    from app.services.factor_analysis import FactorAnalyzer

    try:
        analyzer = FactorAnalyzer(self.db)  # self.db from services
        result = await analyzer.compute_factor_exposure(
            portfolio_id=str(portfolio_id_uuid),
            pack_id=str(pack),
            lookback_days=252
        )

        # Check for errors
        if "error" in result:
            # Fallback to stub with clear error message
            logger.warning(f"FactorAnalyzer returned error: {result['error']}")
            return self._factor_exposure_stub(portfolio_id_uuid, pack, error=result["error"])

        # Success! Add provenance
        result["_provenance"] = {
            "type": "real",
            "source": "FactorAnalyzer",
            "confidence": 0.95,
            "implementation_status": "complete",
            "r_squared": result.get("r_squared", 0),
            "data_points": result.get("data_points", 0)
        }

        logger.info(f"FactorAnalyzer success: R²={result.get('r_squared'):.2f}")
        return result

    except Exception as e:
        # Fallback to stub on error
        logger.error(f"FactorAnalyzer failed: {e}", exc_info=True)
        return self._factor_exposure_stub(portfolio_id_uuid, pack, error=str(e))


def _factor_exposure_stub(self, portfolio_id, pack, error=None):
    """Fallback stub data when real service fails."""
    return {
        "portfolio_id": str(portfolio_id),
        "pack_id": str(pack) if pack else None,
        "factors": {"Real Rates": 0.5, ...},  # Keep stub values
        "_provenance": {
            "type": "stub",
            "source": "fallback_due_to_error",
            "confidence": 0.0,
            "error": error,
            "warnings": [
                f"⚠️ FactorAnalyzer failed: {error}",
                "⚠️ Showing placeholder data",
                "⚠️ DO NOT use for investment decisions"
            ]
        }
    }
```

**Changes:**
1. Import FactorAnalyzer
2. Call real service
3. Handle errors gracefully (fallback to stub)
4. Add real provenance on success
5. Extract stub logic to helper method

**Testing:**
- Run portfolio_cycle_risk pattern
- Verify real data returned
- Verify R² > 0.7
- Verify no stub warning in UI

**Estimated Time:** 2 hours (including testing)

**🎉 SAVES 38-46 HOURS compared to Options A/B!**

---

### Option E: Populate Data + Wire Up (10 hours) ⚠️ **LIKELY CASE**

**When to Use:** Phase 0 Task 0.5 test failed with "Insufficient data" error

**Context:**

Test returned:
```
⚠️ FactorAnalyzer returned error: Insufficient data
   portfolio_daily_values: 0 rows
   economic_indicators: 0 rows
```

**Problem:** Tables exist but empty. Need to populate with historical data.

---

**Step 1: Populate economic_indicators (4 hours)**

```python
# backend/scripts/populate_fred_data.py (NEW FILE)

"""
Populate economic_indicators table with FRED data.

Fetches:
- DFII10: 10-Year TIPS Yield (Real Rate)
- T10YIE: 10-Year Breakeven Inflation
- BAMLC0A0CM: IG Corporate Spread (Credit)
- DTWEXBGS: Dollar Index (FX)
- SP500: S&P 500 Index (Equity)
"""

import asyncio
from datetime import date, timedelta
from app.providers.fred_provider import FREDProvider
from app.db.connection import get_db_pool

FRED_SERIES = {
    "DFII10": "Real Rate",
    "T10YIE": "Inflation",
    "BAMLC0A0CM": "Credit Spread",
    "DTWEXBGS": "USD",
    "SP500": "Equity"
}

async def populate_fred_data(start_date: date, end_date: date):
    """Populate FRED data for date range."""

    db = await get_db_pool()
    fred = FREDProvider(api_key=os.getenv("FRED_API_KEY"))

    for series_id, description in FRED_SERIES.items():
        print(f"Fetching {series_id} ({description})...")

        # Fetch from FRED
        data = await fred.fetch_series(series_id, start_date, end_date)

        # Insert into database
        for obs in data:
            await db.execute(
                """
                INSERT INTO economic_indicators (series_id, asof_date, value, source)
                VALUES ($1, $2, $3, 'FRED')
                ON CONFLICT (series_id, asof_date) DO UPDATE
                SET value = EXCLUDED.value
                """,
                series_id,
                obs["date"],
                obs["value"]
            )

        print(f"  ✅ Inserted {len(data)} observations")

    print(f"\n✅ FRED data populated ({start_date} to {end_date})")

# Run
asyncio.run(populate_fred_data(
    start_date=date.today() - timedelta(days=365*2),  # 2 years
    end_date=date.today()
))
```

**Estimated Time:** 4 hours (script + FRED API + testing)

---

**Step 2: Populate portfolio_daily_values (3 hours)**

```python
# backend/scripts/populate_portfolio_nav.py (NEW FILE)

"""
Populate portfolio_daily_values table with historical NAV.

Calculates daily portfolio values using:
- Position quantities from ledger
- Historical prices from pricing packs
"""

import asyncio
from datetime import date, timedelta
from app.db.connection import get_db_pool

async def populate_portfolio_nav(portfolio_id: str, start_date: date, end_date: date):
    """Calculate and store daily portfolio NAV."""

    db = await get_db_pool()

    # For each date in range
    current_date = start_date
    while current_date <= end_date:
        # Get pricing pack for date
        pack = await db.fetchrow(
            "SELECT pack_id FROM pricing_packs WHERE asof_date = $1",
            current_date
        )

        if not pack:
            current_date += timedelta(days=1)
            continue

        # Get positions and prices
        positions = await db.fetch(
            """
            SELECT p.security_id, p.quantity, pr.price
            FROM portfolio_positions p
            JOIN pricing_pack_prices pr ON p.security_id = pr.security_id
            WHERE p.portfolio_id = $1 AND pr.pack_id = $2
            """,
            portfolio_id,
            pack["pack_id"]
        )

        # Calculate total value
        total_value = sum(pos["quantity"] * pos["price"] for pos in positions)

        # Insert
        await db.execute(
            """
            INSERT INTO portfolio_daily_values (portfolio_id, asof_date, total_value)
            VALUES ($1, $2, $3)
            ON CONFLICT (portfolio_id, asof_date) DO UPDATE
            SET total_value = EXCLUDED.total_value
            """,
            portfolio_id,
            current_date,
            total_value
        )

        print(f"{current_date}: ${total_value:,.2f}")
        current_date += timedelta(days=1)

    print(f"\n✅ Portfolio NAV populated for {portfolio_id}")

# Run for all portfolios
async def populate_all_portfolios():
    db = await get_db_pool()
    portfolios = await db.fetch("SELECT portfolio_id FROM portfolios")

    for portfolio in portfolios:
        await populate_portfolio_nav(
            portfolio["portfolio_id"],
            start_date=date.today() - timedelta(days=365*2),
            end_date=date.today()
        )

asyncio.run(populate_all_portfolios())
```

**Estimated Time:** 3 hours (script + database logic + testing)

---

**Step 3: Wire Up FactorAnalyzer (Same as Option D) (2 hours)**

Same code as Option D - update `risk_compute_factor_exposures` to use real service.

---

**Step 4: Test End-to-End (1 hour)**

- Run data population scripts
- Test FactorAnalyzer with real data
- Verify R² > 0.7
- Run Risk Analytics page
- Verify real data displays

---

**Total Time:** 10 hours (4h FRED + 3h NAV + 2h wiring + 1h testing)

**🎉 SAVES 30-38 HOURS compared to Options A/B!**

---

### DaR (Drawdown at Risk) Implementation

**Parallel to Factor Analysis:**

**Context:**

DaR is also likely stub data in `macro_hound.py`.

**Options:**

**Option 1: Use FactorAnalyzer VaR (if exists)**
- FactorAnalyzer has `compute_factor_var()` method
- Could adapt for DaR

**Option 2: Implement Historical Simulation (16 hours)**
- Use portfolio returns history
- Run Monte Carlo scenarios
- Calculate 95th percentile drawdown

**Option 3: Keep Stub (0 hours)**
- Wait for Phase 4+

**Recommendation:** If FactorAnalyzer works, implement DaR using similar approach (add 8 hours to Option D/E)

---

### Phase 3 Deliverables (Depends on Option)

**Option D (Best Case - 2 hours):**
- Updated `risk_compute_factor_exposures` to use FactorAnalyzer
- Real factor analysis working
- Risk Analytics shows real data

**Option E (Likely - 10 hours):**
- Scripts to populate `economic_indicators` and `portfolio_daily_values`
- Historical data loaded (2+ years)
- Updated `risk_compute_factor_exposures` to use FactorAnalyzer
- Real factor analysis working
- Risk Analytics shows real data

**Option A (Fallback - 40 hours):**
- Complete factor analysis implementation from scratch
- All tests passing
- Risk Analytics shows real data

**Option B (Fallback - 16 hours):**
- pyfolio integrated
- Risk Analytics shows real data

**DaR (Optional +8-16 hours):**
- Real DaR implementation
- Historical simulation or factor-based VaR

**Time:** 2-48 hours (depends on Phase 0 test results)

---

## ✅ Phase 4: Quality (24 hours)

**Goal:** Tests, monitoring, documentation

**Prerequisites:** Phase 0 + Phase 1 + Phase 2 + Phase 3 complete

---

### Task 4.1: Integration Tests (12 hours)

**Context:**

Need end-to-end tests for all 13 patterns to prevent regression.

**Test Framework:**

```python
# backend/tests/integration/test_patterns.py (NEW FILE)

import pytest
import asyncio
from app.core.pattern_orchestrator import PatternOrchestrator
from app.core.agent_runtime import AgentRuntime
from app.db.connection import get_db_pool

@pytest.fixture
async def orchestrator():
    """Create orchestrator for testing."""
    db = await get_db_pool()

    # Initialize agent runtime with all agents
    runtime = AgentRuntime(services={"db": db})

    # Register agents
    from app.agents.financial_analyst import FinancialAnalyst
    from app.agents.macro_hound import MacroHound
    from app.agents.data_harvester import DataHarvester
    from app.agents.claude_agent import ClaudeAgent

    await runtime.register_agent(FinancialAnalyst(db=db, ...))
    await runtime.register_agent(MacroHound(db=db, ...))
    await runtime.register_agent(DataHarvester(db=db, ...))
    await runtime.register_agent(ClaudeAgent(db=db, ...))

    # Create orchestrator
    orchestrator = PatternOrchestrator(runtime)

    return orchestrator


@pytest.mark.asyncio
async def test_portfolio_overview(orchestrator):
    """Test portfolio_overview pattern."""

    # Get test portfolio
    portfolio_id = await get_test_portfolio_id()

    # Execute pattern
    result = await orchestrator.execute_pattern(
        pattern_id="portfolio_overview",
        inputs={"portfolio_id": portfolio_id}
    )

    # Validate structure
    assert "positions" in result
    assert "metrics" in result
    assert "charts" in result

    # Validate data
    assert len(result["positions"]) > 0
    assert result["metrics"]["total_value"] > 0

    # Validate provenance
    if "_provenance" in result["positions"]:
        assert result["positions"]["_provenance"]["type"] in ("real", "stub")


@pytest.mark.asyncio
async def test_portfolio_cycle_risk(orchestrator):
    """Test portfolio_cycle_risk pattern (Risk Analytics)."""

    portfolio_id = await get_test_portfolio_id()

    result = await orchestrator.execute_pattern(
        pattern_id="portfolio_cycle_risk",
        inputs={"portfolio_id": portfolio_id}
    )

    # Validate all outputs present
    assert "stdc" in result
    assert "ltdc" in result
    assert "factor_exposures" in result
    assert "cycle_risk_map" in result
    assert "dar" in result

    # Validate factor exposures
    factor_exposures = result["factor_exposures"]

    # Check provenance
    assert "_provenance" in factor_exposures
    provenance = factor_exposures["_provenance"]

    # If Phase 3 complete, should be real
    if provenance["type"] == "real":
        assert provenance["confidence"] > 0.9
        assert factor_exposures.get("r_squared", 0) > 0.5  # Reasonable fit
    else:
        # Still stub - show warnings
        assert provenance["type"] == "stub"
        assert len(provenance.get("warnings", [])) > 0


# Test all 13 patterns
@pytest.mark.parametrize("pattern_id", [
    "portfolio_overview",
    "portfolio_cycle_risk",
    "portfolio_macro_overview",
    "portfolio_scenario_analysis",
    "cycle_deleveraging_scenarios",
    "macro_trend_monitor",
    "holding_deep_dive",
    "corporate_actions",
    "news_impact_analysis",
    "export_portfolio_report",
    "policy_rebalance",
    "cycles_overview",
    "alerts_overview"
])
@pytest.mark.asyncio
async def test_pattern_execution(orchestrator, pattern_id):
    """Test that pattern executes without errors."""

    portfolio_id = await get_test_portfolio_id()

    # Execute pattern
    try:
        result = await orchestrator.execute_pattern(
            pattern_id=pattern_id,
            inputs={"portfolio_id": portfolio_id}
        )

        # Basic validation
        assert result is not None
        assert isinstance(result, dict)

        # Check expected outputs present
        pattern = load_pattern(pattern_id)
        for output_name in pattern["outputs"]:
            assert output_name in result, f"Missing output: {output_name}"

    except Exception as e:
        pytest.fail(f"Pattern {pattern_id} failed: {e}")
```

---

**Error Handling Tests:**

```python
# backend/tests/integration/test_pattern_errors.py

@pytest.mark.asyncio
async def test_missing_input_error(orchestrator):
    """Test that missing required input shows clear error."""

    with pytest.raises(Exception) as exc_info:
        await orchestrator.execute_pattern(
            pattern_id="portfolio_overview",
            inputs={}  # Missing portfolio_id
        )

    error_msg = str(exc_info.value)
    assert "portfolio_id" in error_msg.lower()
    assert "required" in error_msg.lower()


@pytest.mark.asyncio
async def test_invalid_capability_error(orchestrator):
    """Test that invalid capability shows clear error."""

    # Create pattern with invalid capability
    bad_pattern = {
        "id": "test_bad",
        "steps": [
            {"capability": "nonexistent.capability", "as": "result"}
        ]
    }

    with pytest.raises(Exception) as exc_info:
        await orchestrator._execute_steps(bad_pattern, {})

    error_msg = str(exc_info.value)
    assert "nonexistent.capability" in error_msg


@pytest.mark.asyncio
async def test_undefined_step_reference_error(orchestrator):
    """Test that undefined step reference shows clear error."""

    bad_pattern = {
        "id": "test_bad_ref",
        "steps": [
            {"capability": "ledger.positions", "as": "positions"},
            {"capability": "metrics.compute", "args": {
                "positions": "{{undefined_step.positions}}"  # ← ERROR
            }}
        ]
    }

    # Should be caught by validator
    from app.core.pattern_validator import PatternValidator
    validator = PatternValidator({})
    errors = validator.validate_pattern(bad_pattern)

    assert len(errors) > 0
    assert "undefined_step" in errors[0].lower()
```

---

**Provenance Tests:**

```python
# backend/tests/integration/test_provenance.py

@pytest.mark.asyncio
async def test_stub_provenance_preserved(orchestrator):
    """Test that stub provenance is preserved through orchestrator."""

    # If risk.compute_factor_exposures is still stub
    result = await orchestrator.execute_pattern(
        pattern_id="portfolio_cycle_risk",
        inputs={"portfolio_id": await get_test_portfolio_id()}
    )

    factor_exposures = result["factor_exposures"]

    if "_provenance" in factor_exposures and factor_exposures["_provenance"]["type"] == "stub":
        # Check warnings present
        assert "warnings" in factor_exposures["_provenance"]
        assert len(factor_exposures["_provenance"]["warnings"]) > 0

        # Check confidence is 0
        assert factor_exposures["_provenance"]["confidence"] == 0.0


@pytest.mark.asyncio
async def test_real_provenance_has_confidence(orchestrator):
    """Test that real data has high confidence."""

    result = await orchestrator.execute_pattern(
        pattern_id="portfolio_overview",
        inputs={"portfolio_id": await get_test_portfolio_id()}
    )

    # Positions should be real (from database)
    positions = result["positions"]

    if "_provenance" in positions:
        provenance = positions["_provenance"]
        assert provenance["type"] == "real"
        assert provenance["confidence"] > 0.9
```

---

**Estimated Time Breakdown:**

| Task | Time |
|------|------|
| Create test framework | 2 hours |
| Write pattern execution tests (13 patterns) | 4 hours |
| Write error handling tests | 2 hours |
| Write provenance tests | 2 hours |
| Run tests, fix issues | 2 hours |

**Total:** 12 hours

---

### Task 4.2: Performance Monitoring (8 hours)

**Context:**

Need visibility into pattern execution performance to identify bottlenecks.

**Metrics to Track:**
- Pattern execution duration
- Step execution duration
- Database query times
- Cache hit rates

---

**Implementation:**

```python
# backend/app/core/performance_monitor.py (NEW FILE)

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class StepMetrics:
    """Metrics for a single pattern step."""
    step_name: str
    capability: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    cache_hit: bool = False
    error: Optional[str] = None


@dataclass
class PatternMetrics:
    """Metrics for a pattern execution."""
    pattern_id: str
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    steps: list[StepMetrics] = field(default_factory=list)
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    cache_hits: int = 0
    error: Optional[str] = None


class PerformanceMonitor:
    """
    Monitor pattern and capability performance.

    Tracks:
    - Pattern execution times
    - Step execution times
    - Cache hit rates
    - Error rates
    """

    def __init__(self):
        self.current_metrics: Dict[str, PatternMetrics] = {}
        self.completed_metrics: list[PatternMetrics] = []
        self.max_history = 1000  # Keep last 1000 executions

    def start_pattern(self, pattern_id: str, request_id: str) -> PatternMetrics:
        """Start tracking a pattern execution."""
        metrics = PatternMetrics(
            pattern_id=pattern_id,
            request_id=request_id,
            start_time=time.time()
        )
        self.current_metrics[request_id] = metrics
        return metrics

    def start_step(self, request_id: str, step_name: str, capability: str) -> StepMetrics:
        """Start tracking a step execution."""
        step_metrics = StepMetrics(
            step_name=step_name,
            capability=capability,
            start_time=time.time()
        )

        if request_id in self.current_metrics:
            self.current_metrics[request_id].steps.append(step_metrics)

        return step_metrics

    def end_step(self, request_id: str, step_name: str, cache_hit: bool = False, error: Optional[str] = None):
        """End tracking a step execution."""
        if request_id not in self.current_metrics:
            return

        pattern_metrics = self.current_metrics[request_id]

        # Find step
        step = next((s for s in pattern_metrics.steps if s.step_name == step_name), None)
        if not step:
            return

        # Update step metrics
        step.end_time = time.time()
        step.duration_ms = (step.end_time - step.start_time) * 1000
        step.cache_hit = cache_hit
        step.error = error

        # Update pattern metrics
        pattern_metrics.total_steps += 1
        if error:
            pattern_metrics.failed_steps += 1
        else:
            pattern_metrics.successful_steps += 1

        if cache_hit:
            pattern_metrics.cache_hits += 1

        # Log slow steps
        if step.duration_ms > 1000:  # > 1 second
            logger.warning(
                f"Slow step: {step_name} ({step.capability}) took {step.duration_ms:.0f}ms"
            )

    def end_pattern(self, request_id: str, error: Optional[str] = None):
        """End tracking a pattern execution."""
        if request_id not in self.current_metrics:
            return

        metrics = self.current_metrics[request_id]
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.error = error

        # Log summary
        logger.info(
            f"Pattern {metrics.pattern_id} completed in {metrics.duration_ms:.0f}ms "
            f"({metrics.successful_steps}/{metrics.total_steps} steps, "
            f"{metrics.cache_hits} cache hits)"
        )

        # Move to completed
        self.completed_metrics.append(metrics)
        del self.current_metrics[request_id]

        # Trim history
        if len(self.completed_metrics) > self.max_history:
            self.completed_metrics = self.completed_metrics[-self.max_history:]

    def get_stats(self, pattern_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        metrics = self.completed_metrics

        if pattern_id:
            metrics = [m for m in metrics if m.pattern_id == pattern_id]

        if not metrics:
            return {}

        durations = [m.duration_ms for m in metrics if m.duration_ms]
        cache_hit_rates = [m.cache_hits / m.total_steps if m.total_steps > 0 else 0 for m in metrics]

        return {
            "total_executions": len(metrics),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "avg_cache_hit_rate": sum(cache_hit_rates) / len(cache_hit_rates) if cache_hit_rates else 0,
            "error_count": sum(1 for m in metrics if m.error)
        }


# Global monitor
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return _performance_monitor
```

---

**Integration with Orchestrator:**

```python
# backend/app/core/pattern_orchestrator.py

from app.core.performance_monitor import get_performance_monitor

class PatternOrchestrator:

    async def execute_pattern(self, pattern_id, inputs):
        monitor = get_performance_monitor()
        request_id = str(uuid.uuid4())

        # Start monitoring
        monitor.start_pattern(pattern_id, request_id)

        try:
            result = await self._execute_steps(pattern, inputs, request_id)
            monitor.end_pattern(request_id)
            return result

        except Exception as e:
            monitor.end_pattern(request_id, error=str(e))
            raise

    async def _execute_step(self, step, state, request_id):
        monitor = get_performance_monitor()

        # Start step monitoring
        monitor.start_step(request_id, step["as"], step["capability"])

        try:
            # Check cache
            cache_key = self._get_cache_key(step, state)
            if cache_key in self._cache:
                result = self._cache[cache_key]
                monitor.end_step(request_id, step["as"], cache_hit=True)
                return result

            # Execute capability
            result = await self.agent_runtime.execute_capability(...)

            # Cache result
            self._cache[cache_key] = result

            monitor.end_step(request_id, step["as"], cache_hit=False)
            return result

        except Exception as e:
            monitor.end_step(request_id, step["as"], error=str(e))
            raise
```

---

**API Endpoint for Metrics:**

```python
# backend/app/api/routes/admin.py

from fastapi import APIRouter
from app.core.performance_monitor import get_performance_monitor

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics/patterns")
async def get_pattern_metrics(pattern_id: Optional[str] = None):
    """Get pattern performance metrics."""
    monitor = get_performance_monitor()
    stats = monitor.get_stats(pattern_id)
    return stats


@router.get("/metrics/patterns/{pattern_id}/recent")
async def get_recent_pattern_executions(pattern_id: str, limit: int = 10):
    """Get recent executions for a pattern."""
    monitor = get_performance_monitor()

    recent = [m for m in monitor.completed_metrics if m.pattern_id == pattern_id][-limit:]

    return {
        "pattern_id": pattern_id,
        "executions": [
            {
                "request_id": m.request_id,
                "duration_ms": m.duration_ms,
                "steps": m.total_steps,
                "cache_hits": m.cache_hits,
                "error": m.error
            }
            for m in recent
        ]
    }
```

---

**Estimated Time Breakdown:**

| Task | Time |
|------|------|
| Create performance_monitor.py | 3 hours |
| Integrate with orchestrator | 2 hours |
| Create API endpoints | 2 hours |
| Testing | 1 hour |

**Total:** 8 hours

---

### Task 4.3: Documentation (4 hours)

**Files to Update:**

1. **DATA_ARCHITECTURE.md**
   - Add Phase 0-3 changes
   - Document FactorAnalyzer (if implemented)
   - Update service layer patterns
   - Remove zombie code references

2. **ARCHITECTURE.md**
   - Update pattern validation section
   - Document capability contracts
   - Update agent routing (no more flags/mapping)

3. **CAPABILITY_REFERENCE.md** (Already generated in Phase 2)
   - Run generator script to refresh

4. **REFACTORING_COMPLETION_REPORT.md** (NEW)
   - Summary of all phases
   - Before/after metrics
   - Lines of code removed
   - Features implemented
   - Lessons learned

---

**Create Completion Report:**

```markdown
# Refactoring Completion Report

**Date Completed:** [DATE]
**Total Time:** [HOURS] hours
**Status:** ✅ COMPLETE

---

## Executive Summary

Successfully refactored DawsOSP codebase to remove technical debt and implement real features.

**Key Achievements:**
- ✅ Removed 2,345 lines of zombie code (Phase 0)
- ✅ Added provenance warnings to protect user trust (Phase 1)
- ✅ Implemented capability contracts (80 capabilities documented) (Phase 2)
- ✅ Implemented real factor analysis [or kept stub with warnings] (Phase 3)
- ✅ Created comprehensive test suite (Phase 4)

---

## Phase 0: Zombie Code Removal

**Removed:**
- feature_flags.py (345 lines)
- feature_flags.json (104 lines)
- capability_mapping.py (752 lines)
- macro_aware_scenarios.py (1064 lines)
- Agent runtime zombie code (~80 lines)

**Total:** 2,345 lines removed

**Impact:**
- Routing simplified from ~80 lines to ~10 lines
- No more consolidation flag checks
- Developer onboarding clearer
- Phase 1-4 unblocked

---

## Phase 1: Emergency Fixes

**Updated:**
- risk.compute_factor_exposures - Added _provenance
- macro.compute_dar - Added _provenance (if stub)
- pattern_orchestrator.py - Fixed output extraction
- 2-4 patterns - Standardized to list format

**Impact:**
- ✅ Users see warning banner on stub data
- ✅ Trust preserved (honest about limitations)
- ✅ No more "No data" errors
- ✅ Consistent pattern structure

---

## Phase 2: Foundation

**Created:**
- capability_contract.py (300 lines) - Contract system
- pattern_validator.py (250 lines) - Validation system
- 80 capability contracts - All documented
- CI/CD validation workflow

**Impact:**
- ✅ Self-documenting code
- ✅ Compile-time validation
- ✅ Clear error messages
- ✅ Auto-generated docs

---

## Phase 3: Feature Implementation

**Approach:** [Option D/E/A/B]

[If Option D/E - FactorAnalyzer:]
**Updated:**
- risk.compute_factor_exposures - Now uses FactorAnalyzer
- Populated economic_indicators table (2 years FRED data)
- Populated portfolio_daily_values table
- Real factor analysis working

**Results:**
- ✅ Risk Analytics shows real data
- ✅ R² = [VALUE] (good model fit)
- ✅ Factor betas: [VALUES]
- ✅ Users can make informed decisions

[If Option A/B - New Implementation:]
**Implemented:**
- Complete factor analysis from scratch / pyfolio integration
- Multi-factor regression model
- All tests passing

---

## Phase 4: Quality

**Created:**
- 13 pattern integration tests
- Error handling tests
- Provenance tests
- Performance monitoring system
- Admin metrics API

**Results:**
- ✅ All patterns tested end-to-end
- ✅ 100% test coverage for patterns
- ✅ Performance metrics tracked
- ✅ Documentation complete

---

## Metrics

**Before Refactoring:**
- Lines of code: [COUNT]
- Zombie code: 2,345 lines
- Documented capabilities: 0
- Tested patterns: 0
- Stub capabilities: 2+ with no warnings

**After Refactoring:**
- Lines of code: [COUNT] (-2,345 zombie code +new features)
- Zombie code: 0
- Documented capabilities: 80 (100%)
- Tested patterns: 13 (100%)
- Stub capabilities: 0 (or clearly marked with warnings)

---

## Lessons Learned

1. **Zombie code blocks everything** - Phase 3 consolidation should have removed scaffolding
2. **Test real services early** - FactorAnalyzer existed but was assumed broken
3. **Provenance is critical** - Users need to know what's real vs fake
4. **Validation saves time** - Pattern validator catches bugs before runtime
5. **Documentation must be automated** - Hand-written docs go stale

---

## Future Work

**Phase 5+ (Optional):**
- Implement DaR (Drawdown at Risk) properly
- Add more factor models (Fama-French, etc.)
- Implement real-time pricing
- Add advanced risk metrics
- Performance optimizations

**Maintenance:**
- Run pattern linter on every PR (CI/CD)
- Update capability contracts when adding features
- Regenerate docs monthly
- Monitor performance metrics

---

## Conclusion

Refactoring complete. Codebase is cleaner, safer, better documented, and more maintainable.

**ROI:**
- Phase 0: Unblocked all work (priceless)
- Phase 1: Preserved user trust (priceless)
- Phase 2: 10x developer productivity
- Phase 3: Real features work properly
- Phase 4: Prevent future regressions

**Total Investment:** [HOURS] hours
**Total Value:** Immeasurable (technical debt eliminated, trust preserved, features working)
```

---

**Estimated Time Breakdown:**

| Task | Time |
|------|------|
| Update DATA_ARCHITECTURE.md | 1 hour |
| Update ARCHITECTURE.md | 1 hour |
| Create REFACTORING_COMPLETION_REPORT.md | 2 hours |

**Total:** 4 hours

---

### Phase 4 Deliverables

**New Files:**
- `backend/tests/integration/test_patterns.py` (500 lines) - Pattern tests
- `backend/tests/integration/test_pattern_errors.py` (200 lines) - Error tests
- `backend/tests/integration/test_provenance.py` (100 lines) - Provenance tests
- `backend/app/core/performance_monitor.py` (300 lines) - Monitoring system
- `backend/app/api/routes/admin.py` - Admin metrics API
- `REFACTORING_COMPLETION_REPORT.md` - Final report

**Documentation Updated:**
- `DATA_ARCHITECTURE.md` - Phase 0-3 changes documented
- `ARCHITECTURE.md` - Contract system, validation documented
- `CAPABILITY_REFERENCE.md` - Refreshed from contracts

**Tests:**
- 13 pattern integration tests
- Error handling tests
- Provenance tests
- All tests passing

**Monitoring:**
- Performance metrics tracked
- Admin API for metrics
- Slow step warnings

**Time:** 24 hours total

---

## 📊 Complete Timeline Summary

```
Phase 0: Zombie Code Removal       14 hours  (Nov 5-6)
Phase 1: Emergency Fixes           16 hours  (Nov 7-8)
Phase 2: Foundation                32 hours  (Nov 11-14)
Phase 3: Features                  2-48 hours (Nov 15-22)
  - Option D: Wire Up               2 hours   ← Best case
  - Option E: Populate + Wire      10 hours   ← Likely
  - Option B: Use Library          16 hours   ← Fallback
  - Option A: From Scratch         40 hours   ← Last resort
Phase 4: Quality                   24 hours  (Nov 25-27)

Total: 88-134 hours (2.2-3.4 weeks)
```

---

## 🎯 Success Criteria

**Phase 0:**
- ✅ 2,345 lines of zombie code removed
- ✅ Routing simplified to <10 lines
- ✅ All patterns execute identically

**Phase 1:**
- ✅ Users see warning banner on stub data
- ✅ No "No data" errors
- ✅ All patterns use standard format

**Phase 2:**
- ✅ 80 capabilities documented with contracts
- ✅ Pattern validator catches all errors
- ✅ CI/CD validates patterns on PR

**Phase 3:**
- ✅ Risk Analytics shows real or clearly-warned data
- ✅ R² > 0.7 (if real implementation)
- ✅ Users can make informed decisions

**Phase 4:**
- ✅ All 13 patterns tested
- ✅ Performance metrics tracked
- ✅ Documentation complete

---

## 🚀 Getting Started

**To execute this plan:**

1. **Read zombie verification report:**
   - `ZOMBIE_CODE_VERIFICATION_REPORT.md`
   - Understand what was found

2. **Start Phase 0:**
   - Begin with Task 0.5 (Test FactorAnalyzer) - CRITICAL
   - Results determine Phase 3 approach
   - Then proceed with zombie code removal

3. **Decision Points:**
   - After Phase 0: Decide Phase 3 approach based on FactorAnalyzer test
   - After Phase 1: Evaluate if Phase 2 needed immediately
   - After Phase 2: Evaluate if Phase 3 needed immediately

4. **Iterate:**
   - Phases can be executed in sprints
   - Each phase delivers value independently
   - Can pause between phases to evaluate

---

## 📎 Related Documentation

- **[ZOMBIE_CODE_VERIFICATION_REPORT.md](ZOMBIE_CODE_VERIFICATION_REPORT.md)** - Verification findings
- **[REFACTORING_MASTER_PLAN.md](REFACTORING_MASTER_PLAN.md)** - High-level plan
- **[INTEGRATED_REFACTORING_ANALYSIS.md](INTEGRATED_REFACTORING_ANALYSIS.md)** - Synthesis of all reviews
- **[DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md)** - Data architecture
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture

---

**Status:** 🎯 READY TO EXECUTE

**Next Step:** Phase 0 Task 0.5 - Test FactorAnalyzer (2 hours)
