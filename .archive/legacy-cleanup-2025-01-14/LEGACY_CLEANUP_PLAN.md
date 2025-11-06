# Legacy Code Cleanup Plan

**Date:** January 14, 2025  
**Status:** 🔧 **IN PROGRESS**  
**Purpose:** Remove Prometheus, Docker, and OpenTelemetry legacy elements that escaped refactoring

---

## Executive Summary

**Git History Analysis:**
- `c371cdc` (Nov 2, 2025): Removed `prometheus-client` and `opentelemetry` packages from `requirements.txt`
- `d8f404b` (Nov 5, 2025): Attempted to remove Prometheus code but **incomplete**
- `ddff1b3` (Oct 28, 2025): Removed `observability` module but **imports still exist**

**Current State:**
- ✅ Packages removed from requirements.txt
- ❌ **Code still imports** `opentelemetry`, `observability.metrics`, `observability.tracing`
- ❌ **Observability directory** still exists (13 config files)
- ❌ **Docker references** in scripts (run_api.sh, init_database.sh)
- ❌ **Pattern JSON files** have `observability` sections
- ❌ **RequestCtx** requires `trace_id` (only for observability)

**Impact:** Code will crash on import if packages are missing, or silently fail with fallbacks

---

## 1. Files Requiring Cleanup

### 1.1 OpenTelemetry Code

**File:** `backend/app/integrations/base_provider.py`
- **Line 31:** `from opentelemetry import trace`
- **Line 36:** `tracer = trace.get_tracer(__name__)`
- **Lines 172-181:** `tracer.start_as_current_span()` and `span.set_attribute()` calls

**Status:** ❌ **WILL CRASH** - `opentelemetry` package not in requirements.txt

**Action:** Remove all OpenTelemetry code

---

### 1.2 Observability Imports

**Files with observability imports:**
1. `backend/app/api/executor.py` - Lines 58-92, 321, 328-337, 393, 460-470, 483
2. `backend/app/core/agent_runtime.py` - Lines 42-49
3. `backend/app/core/pattern_orchestrator.py` - Lines 32-38
4. `backend/jobs/build_pricing_pack.py` - Lines 77-81
5. `backend/jobs/alert_retry_worker.py` - Line 29

**Status:** ✅ **GRACEFUL DEGRADATION** - All wrapped in try/except with fallbacks

**Action:** Remove imports and fallbacks (simplify code)

---

### 1.3 Observability Directory

**Directory:** `observability/`
- 13 configuration files (Prometheus, Grafana, OpenTelemetry)
- Not used by application (no Docker deployment)

**Status:** ✅ **UNUSED** - Can be deleted

**Action:** Delete entire directory

---

### 1.4 Docker References

**Files:**
1. `backend/run_api.sh` - Lines 9, 51-65 (Docker container checks)
2. `backend/db/init_database.sh` - Lines 12, 36-38, 54-55 (Docker references)

**Status:** ⚠️ **OPTIONAL** - Scripts mention Docker but don't require it

**Action:** Remove Docker-specific checks, keep generic database connection

---

### 1.5 Pattern JSON Observability Sections

**Files:** All 13 pattern JSON files have `observability` sections
- `portfolio_overview.json` - Lines 181-187
- `portfolio_scenario_analysis.json` - Lines 140-146
- `portfolio_macro_overview.json` - Lines 124-130
- `portfolio_cycle_risk.json` - Lines 128-134
- `macro_trend_monitor.json` - Lines 151-157
- `holding_deep_dive.json` - Lines 372-378
- `cycle_deleveraging_scenarios.json` - Lines 187-193
- `news_impact_analysis.json` - Lines 152-158
- `export_portfolio_report.json` - Lines 117-123
- `policy_rebalance.json` - Lines 180-186
- `buffett_checklist.json` - Lines 216-222
- `corporate_actions_upcoming.json` - Lines 113-119

**Status:** ✅ **UNUSED** - No code reads these sections

**Action:** Remove `observability` sections from all pattern files

---

### 1.6 RequestCtx trace_id

**File:** `backend/app/core/types.py`
- **Line 68:** `trace_id: str` field
- **Line 104:** Validation: `if not self.trace_id: raise ValueError("trace_id is required for observability")`
- **Line 649:** Validation: `if not ctx.trace_id: raise ValueError("trace_id is required")`

**Status:** ⚠️ **REQUIRED** - But only for observability (not used elsewhere)

**Action:** Make `trace_id` optional or remove requirement

---

## 2. Cleanup Execution Plan

### Phase 1: Remove OpenTelemetry (CRITICAL - Will Crash)

**Task 1.1: Remove OpenTelemetry from base_provider.py**
- Remove `from opentelemetry import trace` (line 31)
- Remove `tracer = trace.get_tracer(__name__)` (line 36)
- Remove `with tracer.start_as_current_span()` block (lines 172-181)
- Keep retry logic and caching (not observability-related)

**Estimated Time:** 15 minutes

---

### Phase 2: Remove Observability Imports (Simplify Code)

**Task 2.1: Remove from executor.py**
- Remove try/except block (lines 57-92)
- Remove `setup_metrics()` call (line 321)
- Remove `setup_observability()` block (lines 323-337)
- Remove `/metrics` endpoint (lines 386-396) or simplify to basic health
- Remove `trace_context()` usage (lines 460-470)
- Remove `capture_exception()` call (lines 483-493)
- Remove `metrics_registry` usage (lines 457, 466, 472)

**Estimated Time:** 30 minutes

**Task 2.2: Remove from agent_runtime.py**
- Remove try/except block (lines 42-49)
- Remove `get_metrics()` usage (if any)

**Estimated Time:** 10 minutes

**Task 2.3: Remove from pattern_orchestrator.py**
- Remove try/except block (lines 32-38)
- Remove `get_metrics()` usage (if any)

**Estimated Time:** 10 minutes

**Task 2.4: Remove from build_pricing_pack.py**
- Remove try/except block (lines 77-81)
- Remove `METRICS_AVAILABLE` flag usage (if any)

**Estimated Time:** 10 minutes

**Task 2.5: Remove from alert_retry_worker.py**
- Remove `from observability.metrics import get_metrics` (line 29)
- Remove `get_metrics()` usage (if any)

**Estimated Time:** 10 minutes

---

### Phase 3: Remove Observability Directory

**Task 3.1: Delete observability/ directory**
- Delete entire `observability/` directory
- 13 files total

**Estimated Time:** 1 minute

---

### Phase 4: Remove Docker References

**Task 4.1: Update run_api.sh**
- Remove Docker container checks (lines 51-65)
- Keep generic database connection check
- Update comments to remove Docker references

**Estimated Time:** 15 minutes

**Task 4.2: Update init_database.sh**
- Remove Docker references from comments (lines 12, 36-38, 54-55)
- Keep generic database connection instructions

**Estimated Time:** 10 minutes

---

### Phase 5: Remove Pattern JSON Observability Sections

**Task 5.1: Remove from all 13 pattern files**
- Remove `observability` section from each pattern JSON file
- Keep all other sections intact

**Estimated Time:** 20 minutes

---

### Phase 6: Make trace_id Optional

**Task 6.1: Update RequestCtx**
- Make `trace_id` optional: `trace_id: Optional[str] = None`
- Remove validation requirement (line 104)
- Remove validation in `validate()` method (line 649)
- Update docstring to remove observability reference

**Estimated Time:** 15 minutes

---

## 3. Verification Checklist

After cleanup, verify:

- [ ] Application imports successfully (no ModuleNotFoundError)
- [ ] Application runs without errors
- [ ] All observability imports removed
- [ ] All OpenTelemetry code removed
- [ ] Observability directory deleted
- [ ] Docker references removed from scripts
- [ ] Pattern JSON files cleaned
- [ ] trace_id made optional
- [ ] No broken imports or references

---

## 4. Risk Assessment

### 4.1 High Risk Areas

**None Identified**

**Reasoning:**
- All observability code has fallbacks (won't break if removed)
- OpenTelemetry code will crash if not removed (package missing)
- Observability directory is unused
- Docker references are informational only

---

### 4.2 Medium Risk Areas

**trace_id Usage:**
- ⚠️ Need to verify `trace_id` is not used elsewhere
- **Mitigation:** Make optional instead of removing

**Pattern JSON Changes:**
- ⚠️ Need to verify no code reads `observability` sections
- **Mitigation:** Search for references before removing

---

## 5. Execution Order

1. **Phase 1:** Remove OpenTelemetry (critical - will crash)
2. **Phase 2:** Remove observability imports (simplify code)
3. **Phase 3:** Delete observability directory (cleanup)
4. **Phase 4:** Remove Docker references (documentation)
5. **Phase 5:** Remove pattern JSON sections (cleanup)
6. **Phase 6:** Make trace_id optional (cleanup)

**Total Estimated Time:** 1.5-2 hours

---

## 6. Files to Modify

### 6.1 Python Files (7 files)

1. `backend/app/integrations/base_provider.py` - Remove OpenTelemetry
2. `backend/app/api/executor.py` - Remove observability imports and usage
3. `backend/app/core/agent_runtime.py` - Remove observability import
4. `backend/app/core/pattern_orchestrator.py` - Remove observability import
5. `backend/jobs/build_pricing_pack.py` - Remove observability import
6. `backend/jobs/alert_retry_worker.py` - Remove observability import
7. `backend/app/core/types.py` - Make trace_id optional

---

### 6.2 Shell Scripts (2 files)

1. `backend/run_api.sh` - Remove Docker checks
2. `backend/db/init_database.sh` - Remove Docker references

---

### 6.3 Pattern JSON Files (13 files)

1. `backend/patterns/portfolio_overview.json`
2. `backend/patterns/portfolio_scenario_analysis.json`
3. `backend/patterns/portfolio_macro_overview.json`
4. `backend/patterns/portfolio_cycle_risk.json`
5. `backend/patterns/macro_trend_monitor.json`
6. `backend/patterns/holding_deep_dive.json`
7. `backend/patterns/cycle_deleveraging_scenarios.json`
8. `backend/patterns/news_impact_analysis.json`
9. `backend/patterns/export_portfolio_report.json`
10. `backend/patterns/policy_rebalance.json`
11. `backend/patterns/buffett_checklist.json`
12. `backend/patterns/corporate_actions_upcoming.json`

---

### 6.4 Directories to Delete

1. `observability/` - Entire directory (13 files)

---

## 7. Next Steps

1. Execute Phase 1 (OpenTelemetry removal)
2. Execute Phase 2 (Observability imports removal)
3. Execute Phase 3 (Delete observability directory)
4. Execute Phase 4 (Docker references removal)
5. Execute Phase 5 (Pattern JSON cleanup)
6. Execute Phase 6 (trace_id optional)
7. Verify application runs
8. Test critical paths

---

**Status:** ✅ **PLAN COMPLETE** - Ready for execution

