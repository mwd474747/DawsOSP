# Governance Violations Audit - 2025-10-26

**Status**: CRITICAL VIOLATIONS IDENTIFIED
**Severity**: P0 (Blocks Production Readiness)
**Auditor**: User Review
**Date**: October 26, 2025

---

## Executive Summary

After claiming governance remediation was complete (87% compliance), a manual code audit uncovered **3 critical violations** that directly contradict the completion claims made in previous remediation summaries.

**Findings**:
- ❌ **VIOLATION #1**: Moat/resilience weights deviate from spec (hardcoded 25% instead of rubric-driven)
- ⚠️  **ISSUE #2**: Fundamentals loading returns stubs despite fetching real data
- ✅ **NON-ISSUE #3**: Agent scoring logic duplication claim is false (code review shows thin agent pattern)
- ✅ **NON-ISSUE #4**: Integration script container names claim is inaccurate (only 2 references, not 7)
- ❌ **VIOLATION #5**: Governance document deleted during cleanup (no approval record)

---

## Violation #1: Hardcoded Rating Weights (CRITICAL)

### Location
- [backend/app/services/ratings.py:258-263](backend/app/services/ratings.py#L258-L263) - Moat strength weights
- [backend/app/services/ratings.py:392-397](backend/app/services/ratings.py#L392-L397) - Resilience weights

### Specification Requirement
From `.claude/agents/business/RATINGS_ARCHITECT.md`:
- Lines 325-330 (Moat): "Load from rating_rubrics.overall_weights table"
- Lines 400-405 (Resilience): "Load from rating_rubrics.overall_weights table"

### Actual Implementation
```python
# ⚠️ GOVERNANCE DEVIATION: Using equal 25% weights
# SPECIFICATION REQUIREMENT: Load from rating_rubrics.overall_weights table
# Phase 1: Hardcoded equal weights (documented limitation)
# Phase 2: TODO - Implement database rubric loading
weights = {
    "roe_consistency": Decimal("0.25"),
    "gross_margin": Decimal("0.25"),
    "intangibles": Decimal("0.25"),
    "switching_costs": Decimal("0.25"),
}
```

### Impact
- **Accuracy**: Moat and resilience ratings may be significantly inaccurate
- **Governance**: Explicit deviation from spec without approval
- **Compliance**: Violates "zero shortcuts" rule

### Remediation Required
1. Create `rating_rubrics` table with `overall_weights` column
2. Seed table with spec-defined weights from architect document
3. Update `ratings.py` to load weights from database
4. Add fallback to equal weights only if rubric not found
5. Add metadata flag `_weights_source: "rubric"` vs `"fallback"`

### Acceptance Criteria
```python
# Load weights from database
weights = await self._load_rubric_weights(symbol, "moat_strength")
if not weights:
    logger.warning("Rubric weights not found, using equal fallback")
    weights = self._default_weights()
    source_flag = "fallback"
else:
    source_flag = "rubric"
```

---

## Issue #2: Fundamentals Loading Returns Stubs

### Location
- [backend/app/agents/data_harvester.py:534-640](backend/app/agents/data_harvester.py#L534-L640) - `fundamentals_load` method

### Specification Requirement
- Pattern `buffett_checklist` requires real fundamentals for accurate ratings
- Architect spec requires "fetch from FMP and transform to ratings format"

### Actual Implementation
The code ATTEMPTS real lookup but ALWAYS returns stubs:

```python
# Lines 601-608: Fetches from provider
fundamentals_data = await self.provider_fetch_fundamentals(ctx, state, symbol=symbol)
ratios_data = await self.provider_fetch_ratios(ctx, state, symbol=symbol)

# Lines 611-621: Ignores fetched data and returns stubs anyway
if fundamentals_data.get("_real_data", False):
    source = f"fundamentals:fmp:{symbol}"
    logger.info(f"Successfully fetched real fundamentals for {symbol}")

    # Transform provider data to ratings format
    # TODO: Implement proper transformation logic
    # For now, still use stubs but mark as attempted
    result = self._stub_fundamentals_for_symbol(symbol)  # ❌ ALWAYS STUBS
```

### Impact
- **Accuracy**: `buffett_checklist` pattern produces inaccurate ratings (all stubs)
- **Provider Integration**: FMP API calls are wasted (fetches but doesn't use data)
- **Transparency**: Metadata claims `source: "fundamentals:fmp:AAPL"` but returns stubs

### Remediation Required
1. Implement `_transform_fmp_to_ratings_format()` method
2. Map FMP fundamental fields to ratings service format
3. Use transformed data instead of stubs when `_real_data: true`
4. Update metadata to reflect actual data source

### Transformation Mapping
```python
# Map FMP API response to ratings format
{
    "payout_ratio_5y_avg": fmp_data["avg_dividend_payout_ratio"],
    "fcf_dividend_coverage": fmp_data["fcf"] / fmp_data["dividends_paid"],
    "dividend_growth_streak_years": self._calculate_streak(fmp_data["dividend_history"]),
    "net_cash_position": fmp_data["cash_and_equivalents"] - fmp_data["total_debt"],
    "roe_5y_avg": fmp_data["avg_return_on_equity"],
    # ... etc
}
```

---

## Non-Issue #3: Agent Scoring Logic Duplication (FALSE CLAIM)

### Claim
> "backend/app/agents/ratings_agent.py:280-444 reimplements payout/coverage/ROE/etc. scoring helpers"

### Verification
```bash
$ wc -l backend/app/agents/ratings_agent.py
397 backend/app/agents/ratings_agent.py
```

The file only has 397 lines total, so lines 280-444 cannot exist.

### Code Review
Inspecting lines 280-397:
- Lines 280-289: Metadata attachment (not business logic)
- Lines 291-323: `_get_symbol_from_security_id()` - database lookup only
- Lines 325-347: `_stub_fundamentals_for_testing()` - test data generator
- Lines 349-397: `ratings_aggregate()` - capability method that calls service

### Conclusion
✅ **NO DUPLICATION FOUND** - Agent follows "thin agent, fat service" pattern correctly.

All scoring logic resides in `backend/app/services/ratings.py`. The agent only:
1. Fetches data from database/providers
2. Calls service methods
3. Attaches metadata

This is the CORRECT architectural pattern.

---

## Non-Issue #4: Integration Script Container Names (INACCURATE CLAIM)

### Claim
> "test_integration.sh:254,292,324,400,418,424,432 executes docker exec dawsos-postgres"

### Verification
```bash
$ grep -n "dawsos-postgres\|dawsos-redis\|dawsos-api" test_integration.sh | wc -l
2
```

Only **2 references** found, not 7 as claimed.

### Conclusion
✅ **CLAIM INACCURATE** - The script may have other issues, but the specific claim about 7 hardcoded container name references at those line numbers is false.

---

## Violation #5: Missing Governance Approval Documentation

### Issue
The file `.ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md` was deleted during the aggressive documentation cleanup on 2025-10-26.

### Requirement
Per DawsOS governance process:
- All Phase 1 implementations require documented governance review
- Status must be updated from "PRE-IMPLEMENTATION REVIEW" to "PHASE 1 APPROVED" with:
  - Reviewer name and date
  - Known deviations documented
  - Remediation plan for Phase 2
  - Sign-off for production use

### Impact
- **Traceability**: No record of what deviations were approved vs. discovered post-hoc
- **Compliance**: Cannot verify if hardcoded weights were intentional or oversight
- **Process**: Violates "document all decisions" governance rule

### Remediation Required
1. Restore or recreate governance document from git history
2. Document all Phase 1 deviations:
   - Hardcoded weights (moat, resilience)
   - Stub fundamentals transformation
   - Any other known limitations
3. Get explicit sign-off for Phase 1 release
4. Define Phase 2 remediation timeline

---

## Remediation Plan

### IMMEDIATE (P0 - This Week)

1. **Restore Governance Document** (2 hours)
   - Recover `.ops/RATINGS_IMPLEMENTATION_GOVERNANCE.md` from git commit 0721468
   - Update status from "PRE-IMPLEMENTATION REVIEW" to "PHASE 1 REVIEW"
   - Document all known deviations with justification
   - Get sign-off from product owner

2. **Create Honest Status Summary** (1 hour)
   - Update all claims of "87% compliance" to reflect actual state
   - Document that weights still deviate from spec
   - Document that fundamentals still return stubs
   - Mark as "Phase 1 - Limited Production Use Only"

### THIS SPRINT (P1 - Next 2 Weeks)

3. **Implement Rubric Weights** (3 days)
   - Create `rating_rubrics` table schema
   - Seed with weights from architect spec
   - Update `ratings.py` to load from database
   - Add fallback logic and metadata flags

4. **Implement Fundamentals Transformation** (2 days)
   - Create `_transform_fmp_to_ratings_format()` method
   - Map all required fields from FMP API
   - Use real data when available
   - Update metadata to reflect source accurately

5. **End-to-End Testing** (1 day)
   - Test `buffett_checklist` pattern with real FMP data
   - Verify ratings change based on fundamentals
   - Verify weights loaded from rubrics table
   - Verify metadata accuracy

### PHASE 2 (P2 - Sprint 4)

6. **Remove All Stubs and Fallbacks** (1 week)
   - Remove `_stub_fundamentals_for_symbol()` method
   - Remove hardcoded default weights
   - Require rubrics and fundamentals for all ratings
   - Add proper error handling for missing data

---

## Acceptance Criteria for Remediation Complete

- [ ] Governance document restored with status "PHASE 1 APPROVED" and all deviations documented
- [ ] Rubrics table created and seeded with spec-defined weights
- [ ] `ratings.py` loads weights from database (with fallback and metadata flag)
- [ ] Fundamentals transformation implemented and using real FMP data when available
- [ ] Metadata accurately reflects data sources (`rubric` vs `fallback`, `fmp` vs `stub`)
- [ ] `buffett_checklist` pattern produces different ratings for different securities
- [ ] Integration tests verify real data flows end-to-end
- [ ] Documentation updated to reflect "Phase 1 - Limited Production" status
- [ ] Phase 2 remediation timeline defined and approved

---

## Sign-Off

**Audit Completed**: 2025-10-26
**Next Review**: After P0/P1 remediation (2-3 weeks)
**Production Status**: ❌ **BLOCKED** - Critical violations must be fixed before production deployment

**Approval Required From**:
- [ ] Product Owner (governance violations acknowledged)
- [ ] Tech Lead (remediation plan approved)
- [ ] Security (no security implications identified)

---

## Appendix: False Positive Analysis

### Why Were Issues #3 and #4 Incorrect?

**Issue #3** (Agent duplication): The claim referenced lines 280-444 in a 397-line file, suggesting the audit was based on an outdated version of the code or incorrect line numbers.

**Issue #4** (Container names): The claim stated 7 hardcoded references at specific line numbers, but verification found only 2 total references. This suggests either:
- The audit was based on a different version of the script
- The line numbers were incorrect
- The issue was already partially fixed

### Lesson Learned
Always verify claims against current code state. Line number references must be validated before declaring violations.

---

**Last Updated**: 2025-10-26
**Status**: OPEN (Remediation in progress)
