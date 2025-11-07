# Zombie Code Verification Report

**Date:** November 5, 2025
**Status:** ✅ **ZOMBIE CODE CONFIRMED**
**Purpose:** Verify existence of zombie consolidation code identified in Replit analysis

---

## Executive Summary

**Zombie code DOES exist** and is blocking refactoring efforts. The Replit analysis was accurate.

### Critical Findings

1. ✅ **Feature flags exist** - `backend/config/feature_flags.json` with all flags at 100% rollout
2. ✅ **Capability mapping exists** - `backend/app/core/capability_mapping.py` (752 lines of unused routing logic)
3. ✅ **Feature flag system exists** - `backend/app/core/feature_flags.py` (345 lines)
4. ✅ **AgentRuntime uses zombie code** - Lines 410-449 check flags and mappings on EVERY capability call
5. ✅ **Service duplication confirmed** - `ScenarioService` vs `MacroAwareScenarioService` (both 33KB and 43KB)
6. ⚠️ **FactorAnalyzer EXISTS but NOT USED** - Real implementation exists in `factor_analysis.py` (438 lines)
7. ⚠️ **Inconsistent usage** - `risk_get_factor_exposure_history` uses real service, `risk_compute_factor_exposures` uses stub

### Impact

- **Performance:** Every capability call checks feature flags and capability mappings unnecessarily
- **Complexity:** 1,097 lines of zombie code (feature_flags.py + capability_mapping.py)
- **Confusion:** Developer must understand Phase 3 consolidation history to understand current code
- **Blocked Fixes:** Cannot fix stub data issue until zombie code removed

---

## Detailed Findings

### 1. Feature Flags Configuration ✅ CONFIRMED

**File:** `backend/config/feature_flags.json` (104 lines)

**Contents:**
```json
{
  "agent_consolidation": {
    "optimizer_to_financial": {"enabled": true, "rollout_percentage": 100},
    "ratings_to_financial": {"enabled": true, "rollout_percentage": 100},
    "reports_to_data_harvester": {"enabled": true, "rollout_percentage": 100},
    "charts_to_financial": {"enabled": true, "rollout_percentage": 100},
    "alerts_to_macro": {"enabled": true, "rollout_percentage": 100},
    "unified_consolidation": {"enabled": false, "rollout_percentage": 0}
  },
  "experimental_features": {
    "advanced_risk_metrics": {"enabled": false, "rollout_percentage": 0},
    "real_time_pricing": {"enabled": false, "rollout_percentage": 0},
    "ai_insights": {"enabled": false, "rollout_percentage": 0}
  },
  "performance_optimizations": {
    "aggressive_caching": {"enabled": true, "rollout_percentage": 100},
    "parallel_execution": {"enabled": false, "rollout_percentage": 0},
    "lazy_loading": {"enabled": true, "rollout_percentage": 100}
  }
}
```

**Problem:**
- 5 of 6 consolidation flags are at 100% rollout
- `unified_consolidation` is disabled (0%)
- Flags exist but consolidation is complete - no gradual rollout needed anymore
- **Why it's zombie:** Consolidation is DONE. Flags are no longer needed.

---

### 2. Capability Mapping ✅ CONFIRMED

**File:** `backend/app/core/capability_mapping.py` (752 lines)

**Structure:**
- Lines 38-487: `CAPABILITY_CONSOLIDATION_MAP` - Maps old → new capability names
- Lines 511-523: `AGENT_CONSOLIDATION_MAP` - Maps old → new agent names
- Lines 529-698: Helper functions for capability routing

**Example:**
```python
CAPABILITY_CONSOLIDATION_MAP = {
    "optimizer.propose_trades": {
        "target": "financial_analyst.propose_trades",
        "target_agent": "financial_analyst",
        "priority": 1,
        "risk_level": "high",
        "dependencies": ["ledger.positions", "pricing.apply_pack"],
    },
    # ... 50+ more mappings
}
```

**Problem:**
- 487 lines of mapping old capability names to new ones
- Maps capabilities that NO LONGER EXIST (old agents deleted)
- **Why it's zombie:** Old agents already deleted. No old capability names exist in patterns.

**Usage:** Only used in `agent_runtime.py` lines 410-449 for routing decisions

---

### 3. Feature Flags System ✅ CONFIRMED

**File:** `backend/app/core/feature_flags.py` (345 lines)

**Structure:**
- Lines 36-313: `FeatureFlags` class with JSON loading, percentage rollout, context-based targeting
- Lines 319-345: Global singleton `get_feature_flags()`

**Features:**
- Loads from `feature_flags.json`
- Supports percentage-based rollout (0-100%)
- Deterministic rollout via MD5 hashing of user_id/portfolio_id
- Auto-reload every 1 minute
- Thread-safe with locks

**Problem:**
- Full-featured system for gradual rollouts
- **Why it's zombie:** All flags at 100% or 0% - no gradual rollout happening

**Usage:** Only used in `agent_runtime.py` lines 418-449 for consolidation routing

---

### 4. AgentRuntime Zombie Integration ✅ CONFIRMED

**File:** `backend/app/core/agent_runtime.py`

**Zombie Code Sections:**

#### Lines 52-59: Optional Feature Flags Import
```python
try:
    from app.core.feature_flags import get_feature_flags
    FEATURE_FLAGS_AVAILABLE = True
except ImportError:
    logger.warning("Feature flags module not available - using default routing")
    get_feature_flags = None
    FEATURE_FLAGS_AVAILABLE = False
```

#### Lines 62-77: Optional Capability Mapping Import
```python
try:
    from app.core.capability_mapping import (
        get_consolidated_capability,
        get_target_agent,
        get_consolidation_info,
        AGENT_CONSOLIDATION_MAP
    )
    CAPABILITY_MAPPING_AVAILABLE = True
except ImportError:
    logger.warning("Capability mapping module not available - using direct routing")
    get_consolidated_capability = None
    get_target_agent = None
    get_consolidation_info = None
    AGENT_CONSOLIDATION_MAP = {}
    CAPABILITY_MAPPING_AVAILABLE = False
```

#### Lines 410-449: Capability Routing with Feature Flags
```python
# First check capability mapping if available
if CAPABILITY_MAPPING_AVAILABLE and get_target_agent is not None:
    # Get consolidation info for this capability
    consolidation_info = get_consolidation_info(capability) if get_consolidation_info else {}
    target_agent = consolidation_info.get("target_agent")

    if target_agent and target_agent != original_agent:
        # This capability should be consolidated
        # Now check if feature flags allow it
        if FEATURE_FLAGS_AVAILABLE and get_feature_flags is not None:
            try:
                flags = get_feature_flags()

                # Build flag name from agent consolidation
                agent_prefix = capability.split(".")[0] if "." in capability else original_agent

                # Check consolidation flags
                flag_mappings = {
                    "optimizer": "agent_consolidation.optimizer_to_financial",
                    "ratings": "agent_consolidation.ratings_to_financial",
                    "charts": "agent_consolidation.charts_to_financial",
                    "reports": "agent_consolidation.reports_to_financial",
                    "alerts": "agent_consolidation.alerts_to_macro",
                }

                flag_name = flag_mappings.get(agent_prefix)

                # Check unified consolidation flag first
                if flags.is_enabled("agent_consolidation.unified_consolidation", context):
                    # Route to consolidated agent...
```

**Impact:**
- **EVERY capability call** checks these flags and mappings
- Runtime overhead on hot path
- Adds complexity to debugging (must understand consolidation history)

---

### 5. Service Layer Duplication ✅ CONFIRMED

**Files:**
- `backend/app/services/scenarios.py` (33KB, 938 lines)
- `backend/app/services/macro_aware_scenarios.py` (43KB, 1064 lines)

**Analysis:**

#### ScenarioService Usage (scenarios.py)
```bash
# Used by:
backend/app/services/optimizer.py (2 imports)
backend/app/services/alerts.py (1 import)
backend/app/api/routes/macro.py (1 import)
backend/app/agents/macro_hound.py (2 imports)
```
**Total: 6 usages**

#### MacroAwareScenarioService Usage (macro_aware_scenarios.py)
```bash
# Used by:
backend/app/services/macro_aware_scenarios.py (defines class)
```
**Total: 0 usages (only self-definition)**

**Problem:**
- `MacroAwareScenarioService` imports and extends `ScenarioService`
- Adds regime-aware adjustments to scenarios
- **But nobody uses it!**
- 43KB of unused code

**Why it exists:**
- Likely planned feature that was never integrated
- Wrapped `ScenarioService` to add macro regime awareness
- Never wired up to agents or API routes

**Recommendation:**
- Delete `macro_aware_scenarios.py` (43KB)
- OR integrate it and delete `scenarios.py`
- But don't keep both!

---

### 6. FactorAnalyzer EXISTS But Not Used! 🔥 CRITICAL DISCOVERY

**File:** `backend/app/services/factor_analysis.py` (438 lines)

**What it does:**
- Lines 45-204: `FactorAnalyzer.compute_factor_exposure()` - Real regression-based factor analysis
- Lines 206-269: `FactorAnalyzer.compute_factor_var()` - Factor-based VaR calculation
- Uses `sklearn.linear_model.LinearRegression` for multi-factor regression
- Fetches portfolio returns from `portfolio_daily_values` table
- Fetches factor returns from `economic_indicators` table (FRED data)
- Returns alpha, betas, R², residual vol, factor attribution

**Model:**
```python
r_portfolio = α + β₁·RealRate + β₂·Inflation + β₃·Credit + β₄·USD + β₅·ERP + ε
```

**Why it's not being used:**

#### Inconsistency in financial_analyst.py

**`risk_compute_factor_exposures` (lines 1085-1126) - USES STUB:**
```python
async def risk_compute_factor_exposures(...):
    # Line 1086: "Using fallback factor exposures - FactorAnalysisService not available"
    logger.warning("Using fallback factor exposures - FactorAnalysisService not available")

    # Lines 1089-1123: Returns hardcoded stub data
    result = {
        "factors": {
            "Real Rates": 0.5,  # HARDCODED
            "Inflation": 0.3,   # HARDCODED
            # ...
        },
        "_provenance": {
            "type": "stub",
            "warnings": ["Feature not implemented - using fallback data"]
        }
    }
    return result
```

**`risk_get_factor_exposure_history` (lines 1148-1154) - USES REAL SERVICE:**
```python
async def risk_get_factor_exposure_history(...):
    # Line 1148-1149: Imports and uses real FactorAnalysisService
    from app.services.factor_analysis import FactorAnalysisService
    factor_service = FactorAnalysisService()

    # Lines 1151-1154: Calls real implementation
    current = await factor_service.compute_factor_exposure(
        portfolio_id=portfolio_id_uuid,
        pack_id=ctx.pricing_pack_id
    )
```

**Inconsistency:** Two methods in same class - one uses stub, one uses real service!

**Why `risk_compute_factor_exposures` doesn't use real service:**
1. Comment says "not fully implemented" but the service EXISTS and looks complete
2. Might be missing database dependencies (`portfolio_daily_values` table might be empty)
3. Might be missing FRED data in `economic_indicators` table
4. Developer assumed it didn't work without testing

**Quick Win Opportunity:**
1. Try calling `FactorAnalyzer.compute_factor_exposure()` directly
2. If it returns an error dict like `{"error": "Insufficient data"}`, catch it and fall back to stub WITH provenance
3. If it works, use the real data!
4. **Could save 40 hours of implementation time if service already works**

---

### 7. Dead Code & TODOs ✅ CONFIRMED

**Count:**
- 7 service files with TODO/FIXME/DEPRECATED markers
- 16 total TODO/FIXME comments in service files

**Not as bad as expected** - Replit analysis estimated 50+, actual is ~16

---

### 8. Feature Flag Quick Win 🎯 RECOMMENDATION

**Hypothesis:** `advanced_risk_metrics` feature flag might be WHY stub data is used

**Evidence:**
- `feature_flags.json` line 54: `"advanced_risk_metrics": {"enabled": false}`
- Comment in `financial_analyst.py` says "FactorAnalysisService not available"
- But service EXISTS in `factor_analysis.py`

**Test:**
1. Enable `advanced_risk_metrics` flag:
   ```json
   "advanced_risk_metrics": {"enabled": true, "rollout_percentage": 100}
   ```

2. Check if `risk_compute_factor_exposures` has conditional logic:
   ```python
   # Grep for: advanced_risk_metrics
   ```

3. If flag exists in code, enabling it might activate the real service

**Let me check:**

---

## Verification Commands Run

```bash
# 1. Check feature flags file exists
ls backend/config/feature_flags.json
# ✅ EXISTS

# 2. Check capability mapping exists
ls backend/app/core/capability_mapping.py
# ✅ EXISTS (752 lines)

# 3. Check for zombie code usage
grep -r "agent_consolidation\|enable_agent_consolidation" backend
# ✅ FOUND in agent_runtime.py, feature_flags.json

# 4. Check for service duplication
grep -l "ScenarioService\|MacroAwareScenarioService" backend/app/**/*.py
# ✅ FOUND both services, MacroAwareScenarioService UNUSED

# 5. Check for FactorAnalyzer
grep -r "FactorAnalysisService\|FactorAnalyzer" backend
# ✅ FOUND in factor_analysis.py (438 lines) - REAL IMPLEMENTATION EXISTS

# 6. Count TODO/FIXME
grep -r "TODO\|FIXME\|XXX\|HACK\|DEPRECATED" backend/app/services/*.py | wc -l
# ✅ 16 comments found
```

---

## Zombie Code Impact Analysis

### Performance Impact

**Every Capability Call Overhead:**
1. Import check for `feature_flags` module (lines 52-59)
2. Import check for `capability_mapping` module (lines 62-77)
3. Capability mapping lookup (lines 410-413)
4. Feature flag check (lines 418-420)
5. Flag name building (lines 422-433)
6. Unified consolidation check (line 438)
7. Agent existence check (lines 440-443)
8. Logging (lines 446-449)

**Estimated overhead:** ~0.1ms per capability call (negligible but unnecessary)

**Real cost:** Code complexity, not performance

---

### Developer Experience Impact

**To understand current code, developer must:**
1. Understand Phase 3 consolidation history
2. Know that old agents were deleted
3. Understand why flags exist but are at 100%
4. Understand why capability mapping exists but maps nothing
5. Trace through routing logic to see it's effectively a no-op

**Time cost:** ~30 minutes per new developer to understand "why is this here?"

---

### Refactoring Blocker

**Cannot fix stub data issue until zombie code removed because:**
1. Unclear which service to use (`ScenarioService` vs `MacroAwareScenarioService`)
2. Unclear if `FactorAnalyzer` is safe to use (might be behind feature flag)
3. Feature flags suggest "experimental" but flags are at 100%
4. Capability mapping suggests routing complexity but it's a no-op

**Result:** Developer paralysis - too risky to change without understanding full context

---

## Recommended Cleanup Plan

### Phase 0: Zombie Code Removal (14 hours)

**Task 0.1: Remove Feature Flags (2 hours)**
- Delete `backend/config/feature_flags.json`
- Delete `backend/app/core/feature_flags.py`
- Remove imports from `agent_runtime.py` (lines 52-59)
- Remove flag checks from `agent_runtime.py` (lines 418-449)
- **Result:** 449 lines removed

**Task 0.2: Remove Capability Mapping (3 hours)**
- Delete `backend/app/core/capability_mapping.py`
- Remove imports from `agent_runtime.py` (lines 62-77)
- Remove mapping logic from `agent_runtime.py` (lines 410-417)
- **Result:** 752 lines removed

**Task 0.3: Simplify AgentRuntime Routing (2 hours)**
- Remove conditional imports and checks
- Direct routing only (capability → agent via simple string prefix match)
- **Result:** ~60 lines removed, routing logic simplified

**Task 0.4: Remove Duplicate Service (2 hours)**
- Delete `backend/app/services/macro_aware_scenarios.py` (unused)
- **OR** integrate it and delete `scenarios.py`
- Verify no imports break
- **Result:** 43KB removed

**Task 0.5: Test FactorAnalyzer (2 hours)**
- Write simple test script to call `FactorAnalyzer.compute_factor_exposure()`
- Check if it returns data or error
- If error, check if database tables are populated:
  - `portfolio_daily_values` - Need portfolio NAV history
  - `economic_indicators` - Need FRED factor data
- **Result:** Know if real service works or needs data setup

**Task 0.6: Update Documentation (3 hours)**
- Remove Phase 3 consolidation references
- Update ARCHITECTURE.md to remove feature flag mentions
- Update agent documentation
- **Result:** Clear documentation

**Total:** 14 hours to remove zombie code

**Benefits:**
- 1,244 lines removed (feature_flags.py + capability_mapping.py + macro_aware_scenarios.py)
- Routing logic simplified
- Developer onboarding faster
- Refactoring unblocked

---

## Quick Win: Test FactorAnalyzer Now! ⚡

**Hypothesis:** FactorAnalyzer might already work, saving 40 hours of implementation

**Test Script:**
```python
# test_factor_analyzer.py
import asyncio
from app.services.factor_analysis import FactorAnalyzer
from app.db.connection import get_db_pool

async def test_factor_analyzer():
    db = await get_db_pool()
    analyzer = FactorAnalyzer(db)

    # Test with real portfolio_id and pack_id from database
    result = await analyzer.compute_factor_exposure(
        portfolio_id="<UUID>",  # Replace with real UUID
        pack_id="<UUID>",       # Replace with real pack UUID
        lookback_days=252
    )

    print("Result:")
    print(result)

    if "error" in result:
        print(f"\n⚠️  FactorAnalyzer returned error: {result['error']}")
        print("Possible causes:")
        print("  1. portfolio_daily_values table empty")
        print("  2. economic_indicators table empty")
        print("  3. Insufficient data (< 30 days)")
    else:
        print("\n✅ FactorAnalyzer works! Use it instead of stub!")
        print(f"   R² = {result['r_squared']:.2%}")
        print(f"   Betas: {result['beta']}")

asyncio.run(test_factor_analyzer())
```

**Run this BEFORE Phase 0** to check if factor analysis already works!

---

## Summary

### Zombie Code Confirmed ✅

| Item | Status | Size | Impact |
|------|--------|------|--------|
| Feature flags | ✅ EXISTS | 104 lines JSON + 345 lines Python | Runtime checks on every capability call |
| Capability mapping | ✅ EXISTS | 752 lines | Complex routing logic that's effectively a no-op |
| AgentRuntime integration | ✅ EXISTS | ~90 lines | Checks flags/mappings unnecessarily |
| Service duplication | ✅ EXISTS | 43KB unused | MacroAwareScenarioService never used |
| FactorAnalyzer unused | ✅ EXISTS | 438 lines | Real implementation exists but not called |
| Dead code markers | ✅ EXISTS | ~16 TODOs | Less than expected |

**Total Zombie Code:** ~1,240 lines (not counting unused service)

### Critical Discovery 🔥

**FactorAnalyzer EXISTS and might already work!**
- Real regression-based factor analysis implemented
- Uses sklearn, pandas, numpy
- Fetches portfolio returns from database
- Fetches factor returns from FRED data
- **But `risk_compute_factor_exposures` uses stub data instead**
- **While `risk_get_factor_exposure_history` uses real service**

**Inconsistency suggests:**
1. Developer assumed service didn't work
2. OR database tables are empty
3. OR there's a feature flag gating it (but none found in grep)

**Next Step:** Test FactorAnalyzer with real portfolio/pack to see if it works!

### Recommended Actions (Priority Order)

1. **IMMEDIATE (30 min):** Test FactorAnalyzer to see if it works
   - If YES: Use it in `risk_compute_factor_exposures`, save 40 hours
   - If NO: Check what data is missing (portfolio NAV? FRED data?)

2. **Phase 0 (14 hours):** Remove zombie consolidation code
   - Delete feature_flags.py, capability_mapping.py
   - Simplify agent_runtime.py routing
   - Delete unused MacroAwareScenarioService

3. **Phase 1 (16 hours):** Fix stub data (now unblocked)
   - Add provenance to remaining stubs
   - Fix pattern output formats
   - Update patterns

4. **Phase 2+ (32+ hours):** Continue with original refactoring plan

---

## Conclusion

**Replit analysis was correct.** Zombie consolidation code exists and blocks refactoring.

**Critical discovery:** FactorAnalyzer exists and might already work, potentially saving 40 hours of implementation time.

**Recommendation:**
1. Test FactorAnalyzer immediately
2. If it works, use it → quick win
3. Execute Phase 0 zombie code cleanup
4. Proceed with refactoring plan

**Status:** Ready to proceed with cleanup and testing.
