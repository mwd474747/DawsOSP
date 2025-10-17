# Archived Development Scripts

This directory contains one-time scripts used during DawsOS development and debugging (2025).

## Analysis Scripts
- **analyze_patterns.py** - Pattern structure analysis (one-time inventory)
- **analyze_refactoring_opportunities.py** - Code refactoring opportunity detection

## Migration Scripts
- **migrate_patterns_bulk.py** - Bulk pattern migration to Trinity 2.0 format

## Test/Validation Scripts
- **test_capability_routing.py** - Capability routing validation
- **test_economic_data_fix.py** - Economic data system testing
- **test_graph_intelligence_imports.py** - Graph intelligence import validation
- **test_options_flow_complete.py** - Options flow integration testing
- **validate_markets.py** - Markets tab validation

## Notes
- All scripts were used for one-time development tasks
- Functionality has been integrated into main codebase
- Preserved for historical reference only
- For current testing, see: `dawsos/tests/validation/`

## Current Testing
Active test suites are located in:
- `dawsos/tests/validation/` - Automated pytest suites
- `dawsos/tests/unit/` - Unit tests
- `scripts/lint_patterns.py` - Pattern validation (active)
