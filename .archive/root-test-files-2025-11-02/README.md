# Root-Level Test Files Archive

**Archived:** November 2, 2025  
**Reason:** Root-level test files are NOT used by the application

---

## Overview

These test files were standalone development scripts that:
- Were created to manually test API endpoints during development
- Run independently by developers using `python test_xxx.py` or `bash test_xxx.sh`
- Make HTTP requests to localhost:5000 to verify functionality
- Generate output files for human inspection
- Were never cleaned up after testing phases

**Impact:** Zero impact on application functionality - files were not imported, executed, or referenced by production code.

---

## Archived Files

### Python Test Scripts
- `test_auth.py` - Manual authentication testing
- `test_auth_service_standalone.py` - Standalone auth service test
- `test_pdf_generation.py` - PDF generation testing
- `quick_validation_test.py` - Quick validation script (hardcoded credentials, port 5000)

### HTML Test Files
- `test_ratings_fix.html` - UI component testing
- `test_ratings_parse.html` - Ratings parsing testing
- `interactive_ui_test.html` - Interactive UI testing (may have debugging value)

### Shell Test Scripts
- `test_integration.sh` - Integration testing script (outdated: port 5000, Docker references)
- `test_enhanced_features.sh` - Enhanced features testing (outdated: port 5000, Docker references)

---

## Why These Files Were Removed

### 1. Not Used by Application
- ❌ NOT imported by `combined_server.py`
- ❌ NOT imported by `full_ui.html`
- ❌ NOT referenced in configuration files
- ❌ NOT part of pytest test suite

### 2. Outdated Code
- Hardcoded URLs (port 5000) don't match production (port 8000)
- Hardcoded credentials (security risk)
- Assumes Docker containers (doesn't match Replit deployment)

### 3. Maintenance Burden
- Confusion about which tests are part of test suite
- Outdated code that doesn't work with current deployment
- Clutter in root directory

---

## Proper Test Suite Location

**Actual test suite:** `backend/tests/`
- Proper pytest test suite
- Used by `pytest.ini` configuration
- Used by `backend/run_tests.sh`
- Used by `backend/run_integration_tests.sh`
- CI/CD compatible

**These tests are KEPT and MAINTAINED.**

---

## Generated Output Files (Deleted)

The following generated output files were deleted (not archived):
- `test_dashboard_results.json`
- `test_dashboard_results.txt`
- `test_portfolio_report.pdf`
- `test_quarterly_report.pdf`
- `test_ytd_report.pdf`

**Reason:** Generated artifacts that can be recreated if needed.

---

## Restoration Instructions

If you need to restore any of these files:

```bash
# Restore specific file
cp .archive/root-test-files-2025-11-02/test_auth.py .

# Restore all files
cp .archive/root-test-files-2025-11-02/* .
```

**Note:** Files will need to be updated to work with current deployment:
- Change port from 5000 to 8000
- Update credentials
- Remove Docker references
- Use Replit deployment instead

---

## Related Documentation

See `TEST_FILES_VALUE_ASSESSMENT.md` for detailed analysis of test files value to the application.

