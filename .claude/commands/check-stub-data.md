---
description: Find capabilities returning stub/fake data
---

Search for stub data in codebase:

**Known Stub Data Locations:**
1. **risk.compute_factor_exposures** (line 1086-1110 in financial_analyst.py)
   - Returns hardcoded factor exposures
   - Used by: portfolio_cycle_risk pattern (Risk Analytics page)
   - Impact: **CRITICAL USER TRUST ISSUE**

2. **macro.compute_dar** (macro_hound.py)
   - Falls back to stub data on errors
   - Used by: portfolio_cycle_risk pattern

**Search Commands:**
```bash
# Find logger.warning about fallback/stub
grep -rn "fallback" backend/app/agents/*.py
grep -rn "stub" backend/app/agents/*.py

# Find hardcoded return values
grep -rn "# HARDCODED" backend/app/agents/*.py

# Find _provenance fields indicating stub
grep -rn '"type": "stub"' backend/app/agents/*.py
```

**Report:**
- File path:line number
- Capability name
- Patterns that use it
- User impact (which UI page shows fake data)

See: REFACTORING_MASTER_PLAN.md Issue 1 for details
