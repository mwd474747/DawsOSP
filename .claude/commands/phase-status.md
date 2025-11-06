---
description: Check status of refactoring phases
---

Check refactoring phase status:

**Phase 0: Zombie Code Removal (14h)**
- [ ] Task 0.1: Remove feature flags (2h)
- [ ] Task 0.2: Remove capability mapping (3h)
- [ ] Task 0.3: Simplify agent runtime (4h)
- [ ] Task 0.4: Remove duplicate services (3h)
- [ ] Task 0.5: Test FactorAnalyzer (2h) - **CRITICAL DECISION**

Check:
```bash
# Feature flags still exist?
ls backend/config/feature_flags.json 2>/dev/null && echo "❌ Phase 0.1 not done" || echo "✅ Phase 0.1 done"

# Capability mapping still exists?
ls backend/app/core/capability_mapping.py 2>/dev/null && echo "❌ Phase 0.2 not done" || echo "✅ Phase 0.2 done"

# MacroAwareScenarioService still exists?
ls backend/app/services/macro_aware_scenarios.py 2>/dev/null && echo "❌ Phase 0.4 not done" || echo "✅ Phase 0.4 done"
```

**Phase 1: Emergency Fixes (16h)**
- [ ] Task 1.1: Add provenance warnings (4h)
- [ ] Task 1.2: Fix critical bugs (8h)
- [ ] Task 1.3: Wire FactorAnalyzer (4h)

**Phase 2: Foundation (32h)**
- [ ] Task 2.1: Define capability contracts (8h)
- [ ] Task 2.2: Implement pattern validation (12h)
- [ ] Task 2.3: Standardize response format (8h)
- [ ] Task 2.4: Update documentation (4h)

**Phase 3: Features (16-48h)**
- Depends on FactorAnalyzer test results

**Phase 4: Quality (24h)**
- [ ] Task 4.1: Write tests (16h)
- [ ] Task 4.2: Add monitoring (8h)

See: COMPREHENSIVE_REFACTORING_PLAN.md for complete details
