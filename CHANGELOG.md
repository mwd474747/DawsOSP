# Changelog

All notable changes to DawsOS will be documented in this file.

---

## [2025-01-14] - Field Naming Standardization & Corporate Actions Fixes

### ✅ Fixed
- **Corporate Actions:** Fixed field name mismatch (`qty` → `quantity`) in 3 locations
  - `corporate_actions.upcoming`: Now correctly extracts symbols from portfolio holdings
  - `corporate_actions.calculate_impact`: Now correctly calculates portfolio impact
  - Enhanced diagnostic logging for better debugging

### ✅ Changed
- **Field Naming Standards:** Standardized agent layer to use `quantity` (not `qty` or `quantity_open`)
  - `financial_analyst.py`: Removed transitional support for `qty` field
  - `get_position_details`: Returns `quantity` instead of `quantity_open`
  - All agent capabilities now consistently return `quantity`

### ✅ Added
- **Database Documentation:** Migration 014 adds deprecation comment to legacy `quantity` field
- **Architecture Documentation:** Field naming standards section added
- **Development Guide:** Field naming conventions documented

### 📚 Documentation
- Updated ARCHITECTURE.md with field naming standards
- Updated DATABASE.md with Migration 014
- Updated DEVELOPMENT_GUIDE.md with field naming conventions
- Updated API_CONTRACT.md with field naming verification
- Archived duplicate documentation files

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

