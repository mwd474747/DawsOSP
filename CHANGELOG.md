# Changelog

All notable changes to DawsOS will be documented in this file.

---

## [2025-01-14] - Phase 1 Complete: Provenance Warnings & Pattern Output Extraction

### ✅ Fixed
- **Phase 1 Critical Issues:** Fixed all blocking issues identified in Phase 1 testing
  - **Migration 009:** Applied successfully to create `position_factor_betas` table for scenario analysis
  - **Scenarios SQL Query:** Fixed to use correct column names (`real_rate_beta`, `inflation_beta`, etc.)
  - **AttributeError:** Fixed `shock_type.value` handling in `scenarios.py` (lines 793, 800)
  - **Pattern Output Extraction:** Fixed orchestrator to handle 3 output formats correctly
  - **Corporate Actions:** Fixed field name mismatch (`qty` → `quantity`) in 3 locations

### ✅ Added
- **Provenance Warnings:** Added `_provenance` field to stub data in `risk.compute_factor_exposures` and `macro.compute_dar`
  - Stub data now explicitly marked with `type: "stub"`, `confidence: 0.0`, and warnings
  - UI displays warning banner when stub data is detected
- **Pattern Output Standardization:** Updated 6 patterns to use standard list format
- **Database Migration:** Migration 009 adds scenario analysis tables (`position_factor_betas`, `scenario_shocks`, etc.)
- **Database Documentation:** Migration 014 adds deprecation comment to legacy `quantity` field

### ✅ Changed
- **Field Naming Standards:** Standardized agent layer to use `quantity` (not `qty` or `quantity_open`)
  - `financial_analyst.py`: Removed transitional support for `qty` field
  - `get_position_details`: Returns `quantity` instead of `quantity_open`
  - All agent capabilities now consistently return `quantity`
- **Pattern Orchestrator:** Enhanced to handle multiple output formats (list, dict, dict with panels)

### 📚 Documentation
- Updated ARCHITECTURE.md with Phase 1 changes and provenance warnings
- Updated DATABASE.md with Migration 009 and Migration 014
- Updated DEVELOPMENT_GUIDE.md with Phase 1 patterns and field naming conventions
- Updated API_CONTRACT.md with provenance field documentation
- Updated CHANGELOG.md with Phase 1 completion

### ✅ Validated
- **Phase 1 Testing:** All 4 critical blocking issues fixed and validated
- **Runtime Verification:** All patterns tested successfully, scenario analysis working (12 scenarios)
- **Provenance Warnings:** Correctly displayed in UI for stub data

---

## [2025-11-04] - Database Refactoring & Cleanup

### ✅ Changed
- **Database Schema:** Field naming standardized (`qty_open` → `quantity_open`)
- **Migration 003:** Removed 8 unused tables (480 KB saved)

### ✅ Added
- **Database Documentation:** Comprehensive field naming documentation
- **Migration History:** Complete migration tracking

---

**Format:** [YYYY-MM-DD] - Description  
**Categories:** Added, Changed, Deprecated, Removed, Fixed, Security

