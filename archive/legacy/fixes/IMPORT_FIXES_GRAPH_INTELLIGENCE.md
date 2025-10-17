# Import Fixes for Graph Intelligence Module

**Status**: ✅ **COMPLETE** (October 16, 2025)

**Issue**: Graph intelligence module files have incorrect imports causing "No module named 'dawsos.ui'" error

**Root Cause**: Files within `dawsos/ui/graph_intelligence/` are using `from ui.utils.graph_utils` when they should use `from dawsos.ui.utils.graph_utils` or relative imports.

**Resolution**: All 10 files fixed (8 feature files + __init__.py + trinity_dashboard_tabs.py)

## Import Pattern Analysis

### Current Working Pattern (existing code)
- `main.py` imports: `from core.X`, `from agents.X`, `from ui.X`
- `ui/*.py` files import: `from core.X`, `from agents.X`
- When running `streamlit run dawsos/main.py`, Python's working directory is project root
- The `dawsos` directory is implicitly on the path

### Problem with New Files
Files in `dawsos/ui/graph_intelligence/*.py` use:
```python
from ui.utils.graph_utils import get_node_display_name  # ❌ WRONG
```

Should be:
```python
from dawsos.ui.utils.graph_utils import get_node_display_name  # ✅ CORRECT
```

## Files That Need Fixing

1. `dawsos/ui/graph_intelligence/__init__.py` ✅ (uses correct pattern already)
2. `dawsos/ui/graph_intelligence/live_stats.py`
3. `dawsos/ui/graph_intelligence/connection_tracer.py`
4. `dawsos/ui/graph_intelligence/impact_forecaster.py`
5. `dawsos/ui/graph_intelligence/related_suggestions.py`
6. `dawsos/ui/graph_intelligence/sector_correlations.py`
7. `dawsos/ui/graph_intelligence/query_builder.py`
8. `dawsos/ui/graph_intelligence/comparative_analysis.py`
9. `dawsos/ui/graph_intelligence/analysis_history.py`

## Fix Pattern

### Before (Broken):
```python
from ui.utils.graph_utils import get_node_display_name
```

### After (Fixed):
```python
from dawsos.ui.utils.graph_utils import get_node_display_name
```

## Implementation

Run the following command to fix all files at once:

```bash
cd /Users/mdawson/Dawson/DawsOSB
find dawsos/ui/graph_intelligence -name "*.py" -type f ! -name "__init__.py" -exec sed -i '' 's/from ui\.utils\./from dawsos.ui.utils./g' {} +
```

This will replace all instances of `from ui.utils.` with `from dawsos.ui.utils.` in all graph_intelligence files except __init__.py.

## Verification

After fixing, verify imports:
```bash
grep "from ui.utils" dawsos/ui/graph_intelligence/*.py
```

Should return no results (all should now be `from dawsos.ui.utils`).

## Testing

1. Kill all Streamlit processes
2. Start fresh: `./start.sh`
3. Navigate to Knowledge Graph page
4. Test each of the 9 tabs
5. Verify no import errors

## Related Files

The `__init__.py` file already uses the correct pattern:
```python
from ui.graph_intelligence.live_stats import render_live_stats  # Called from trinity_dashboard_tabs.py
```

This is correct because `trinity_dashboard_tabs.py` (which imports these) uses:
```python
from ui.graph_intelligence import render_live_stats
```

And since `trinity_dashboard_tabs.py` is at `dawsos/ui/trinity_dashboard_tabs.py`, the import `from ui.graph_intelligence` resolves correctly to `dawsos/ui/graph_intelligence`.

The issue is ONLY within the graph_intelligence module files when they try to import from `ui.utils`.

---

## ✅ Completion Report

**Date Completed**: October 16, 2025

### Files Fixed

#### 1. Feature Files (8 files) - Applied sed fix
All files in `dawsos/ui/graph_intelligence/*.py` (except __init__.py):
- ✅ live_stats.py
- ✅ connection_tracer.py
- ✅ impact_forecaster.py
- ✅ related_suggestions.py
- ✅ sector_correlations.py
- ✅ query_builder.py
- ✅ comparative_analysis.py
- ✅ analysis_history.py

**Fix applied**: `from ui.utils.graph_utils` → `from dawsos.ui.utils.graph_utils`

#### 2. Module __init__.py - Manual edit
Changed from absolute imports to relative imports:
- ✅ `from ui.graph_intelligence.X` → `from .X`

#### 3. Trinity Dashboard Integration - Applied sed fix
- ✅ trinity_dashboard_tabs.py: `from ui.graph_intelligence` → `from dawsos.ui.graph_intelligence`

### Verification Results

```bash
# ✅ All feature files using correct imports
grep "from dawsos.ui.utils" dawsos/ui/graph_intelligence/*.py
# Result: 8 files confirmed

# ✅ No incorrect imports remain
grep "from ui\.utils" dawsos/ui/graph_intelligence/*.py
# Result: (empty)

# ✅ __init__.py using relative imports
grep "^from \." dawsos/ui/graph_intelligence/__init__.py
# Result: 8 relative imports confirmed

# ✅ Trinity dashboard using full paths
grep "from dawsos.ui.graph_intelligence" dawsos/ui/trinity_dashboard_tabs.py
# Result: 8 imports confirmed
```

### Next Steps

1. **Kill background processes**: `pkill -9 streamlit`
2. **Test the app**: `./start.sh`
3. **Verify functionality**: Navigate to Knowledge Graph → test all 9 tabs
4. **Expected result**: All tabs load without import errors

### Related Documentation

See [GRAPH_INTELLIGENCE_IMPORT_FIXES_COMPLETE.md](GRAPH_INTELLIGENCE_IMPORT_FIXES_COMPLETE.md) for comprehensive fix report.
