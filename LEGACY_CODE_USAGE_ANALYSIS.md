# Legacy and Archived Code Usage Analysis

## Executive Summary
After thorough analysis, **NO legacy or archived code is being actively used** in the DawsOS application. The `.legacy` and `.archive` folders contain old code that has been successfully deprecated and isolated from the active codebase.

## Folders Identified

### 1. `.legacy/` Folder
**Status:** NOT IN USE

Contains the old Streamlit UI implementation:
```
.legacy/
├── frontend/
│   ├── ui/
│   │   ├── screens/
│   │   │   ├── holdings.py
│   │   │   ├── macro_dashboard.py
│   │   │   ├── portfolio_overview.py
│   │   │   ├── scenarios.py
│   │   │   └── settings.py
│   │   ├── components/
│   │   │   └── dawsos_theme.py
│   │   ├── api_client.py
│   │   └── client_factory.py
│   ├── tests/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── run_ui.sh
└── scripts/
    ├── deploy_old.sh
    └── start_old.sh
```

**Evidence of Non-Usage:**
- No imports from `.legacy` found in any active Python files
- No references to legacy scripts in active code
- README.md explicitly marks it as "Legacy Streamlit UI (archived)"
- Current UI uses `full_ui.html` (React-based), not Streamlit

### 2. `.archive/` Folder
**Status:** NOT IN USE

Contains extensive documentation and old compliance modules:
```
.archive/
├── compliance-archived-20251102/
│   ├── __init__.py
│   ├── attribution.py
│   ├── export_blocker.py
│   ├── rights_registry.py
│   └── watermark.py
├── deprecated/
├── documentation-reviews/
├── phase2/
├── phase3-week1/
├── tests/
└── [various documentation folders]
```

**Evidence of Non-Usage:**
- No imports of `app.core.compliance` found in backend code
- Compliance modules were explicitly archived on 2025-11-02
- combined_server.py contains comment: "Legacy agents removed"

## Active Code vs Legacy Code

### Currently Active:
- `backend/app/services/currency_attribution.py` - Actively imported by financial_analyst
- `combined_server.py` - Main server entry point
- `full_ui.html` - Current React-based UI

### Confirmed Legacy/Unused:
- Everything in `.legacy/` folder
- Everything in `.archive/` folder
- Scripts in `.legacy/scripts/` (start_old.sh, deploy_old.sh)
- Old Streamlit UI components

## Migration Script Found
- `scripts/migrate_legacy_graph_api.py` - A utility script for migrating NetworkX API usage
- Not related to the UI legacy code
- Not being actively imported or used

## Recommendations

1. **Safe to Delete:** Both `.legacy` and `.archive` folders can be safely removed as they contain no actively used code.

2. **Documentation Value:** The `.archive` folder contains extensive documentation that might have historical value for understanding system evolution.

3. **Space Savings:** Removing these folders would clean up the repository and reduce confusion about what code is active.

4. **Version Control:** Since these folders are in git history, they can always be recovered if needed.

## Verification Commands Used
```bash
# Check for imports from legacy folders
grep -r "\.legacy" . --include="*.py"
grep -r "from.*compliance import" backend/
grep -r "import compliance" backend/

# Check for specific file references
grep -r "start_old\.sh\|deploy_old\.sh" .
grep -r "holdings\.py\|macro_dashboard\.py" .

# List folder structures
ls -R .legacy/
ls -R .archive/
```

## Conclusion
The legacy and archived folders are completely isolated from the active codebase. The application has successfully migrated from the Streamlit UI to a React-based single-page application (full_ui.html) served by combined_server.py, and all legacy code has been properly deprecated and contained in clearly marked archive folders.