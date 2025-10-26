# Implementation Guardrails - Zero Shortcuts Policy

**Status**: MANDATORY - No exceptions without approval
**Created**: 2025-10-26
**Purpose**: Prevent shortcuts when encountering difficulties during remediation
**Enforcement**: Code review + automated checks + governance oversight

---

## Executive Summary

### The Problem

This codebase already contains **54 TODOs**, **186 stub references**, and **4 governance deviations** precisely because developers took shortcuts when facing difficulties:

- **"I'll load rubrics from database later"** → Hardcoded 25% weights
- **"I'll implement transformation later"** → Return stubs even after fetching FMP data
- **"I'll wire the service later"** → Return "not yet implemented" errors
- **"I'll document this later"** → Undocumented env vars, missing governance approvals

### The Solution

**Zero Shortcuts Policy**: When you encounter difficulty, you have **three approved options**:

1. **Ask for help** (team member, architect, tech lead)
2. **Research the solution** (docs, examples, specs)
3. **Escalate to product owner** (if truly blocked, discuss scope reduction)

**NOT allowed**:
- ❌ Hardcode values "temporarily"
- ❌ Return stubs "for now"
- ❌ Add TODO comments "to fix later"
- ❌ Skip documentation "we'll update docs later"
- ❌ Comment "Phase 1/Phase 2" without spec approval

---

## Part 1: Mandatory Pre-Implementation Checklist

### Before Starting ANY Task

- [ ] **Read the spec** (RATINGS_ARCHITECT.md, MACRO_ARCHITECT.md, etc.)
- [ ] **Understand acceptance criteria** (what "done" looks like)
- [ ] **Check if dependencies exist** (services, schemas, seed data)
- [ ] **Verify test data is available** (don't assume stubs are OK)
- [ ] **Ask questions upfront** (don't assume you'll "figure it out later")

### Before Writing ANY Code

- [ ] **Design reviewed** (pair with another engineer or architect)
- [ ] **Edge cases identified** (what can go wrong?)
- [ ] **Error handling planned** (graceful degradation, not stubs)
- [ ] **Test cases written** (TDD - write tests first)
- [ ] **Documentation skeleton created** (update docs as you code, not after)

---

## Part 2: Difficulty Response Framework

### When You Hit a Blocker

**Step 1: STOP and Document**
```markdown
## Blocker Encountered
- **Task**: P0-CODE-1 - Implement rubric loading
- **Issue**: Don't know how to query JSONB column in asyncpg
- **Attempted**: Read asyncpg docs, searched Stack Overflow
- **Time Spent**: 30 minutes
- **Status**: BLOCKED - Need help
```

**Step 2: Choose Approved Response**

#### Option A: Ask for Help (Preferred)
- Post in team chat with blocker documentation
- Tag relevant experts (@backend-lead, @database-expert)
- Expected response time: 2 hours during work hours
- **NOT allowed**: "I'll just hardcode it for now"

#### Option B: Research Deeper
- Read official docs (not just Stack Overflow)
- Check similar code in codebase (`grep -r "JSONB" backend/`)
- Review related PRs/commits
- Timebox research: 1-2 hours max
- **NOT allowed**: "I'll return stubs and research later"

#### Option C: Escalate to Product Owner
- If truly blocked after A + B
- Document: What's blocked, why, what's needed
- Propose: Reduce scope OR add dependency task
- Get approval BEFORE taking shortcut
- **NOT allowed**: Taking shortcut without approval

### Common Blockers & Approved Responses

| Blocker | ❌ Shortcut (Not Allowed) | ✅ Approved Response |
|---------|---------------------------|----------------------|
| **"Don't know how to query JSONB"** | Return hardcoded dict | Ask database expert OR read PostgreSQL JSONB docs |
| **"FMP API returns unexpected format"** | Use stubs instead | Log example response, ask data team OR add error handling |
| **"Schema migration breaks in test"** | Skip migration, hardcode | Fix migration OR rollback and get DBA help |
| **"Test is flaky"** | Comment out test | Debug flakiness OR add retry logic with jitter |
| **"Can't figure out Decimal arithmetic"** | Use floats "temporarily" | Read Python Decimal docs OR ask for code review |
| **"Transformation logic is complex"** | Return stubs | Break into smaller functions OR pair program |
| **"Don't have API key for testing"** | Skip real data test | Request API key OR use recorded fixtures |
| **"Documentation is outdated"** | Leave it outdated | Update docs as part of PR OR create doc update task |

---

## Part 3: Code Quality Gates

### Gate 1: No TODO Comments Without Tickets

**Rule**: Every TODO must reference a GitHub issue

❌ **Not Allowed**:
```python
# TODO: Load from database
weights = {"roe": 0.25, "margin": 0.25}
```

✅ **Allowed** (if truly deferred with approval):
```python
# TODO(#1234): Load from rating_rubrics table (approved by @product-owner)
# Approved deferral: Phase 1 uses hardcoded weights
# Remediation: P0-CODE-1 (20 hours, Week 1-2)
weights = {"roe": 0.25, "margin": 0.25}
```

**Enforcement**: CI check fails if `grep "TODO" | grep -v "#[0-9]"`

### Gate 2: No Stub Returns Without Metadata Flag

**Rule**: If returning stub data, metadata MUST indicate this

❌ **Not Allowed**:
```python
# User thinks this is real data!
return {
    "fundamentals": stub_data(),
    "_metadata": {"source": "fmp:AAPL"}  # LYING
}
```

✅ **Allowed**:
```python
# Honest about stub data
return {
    "fundamentals": stub_data(),
    "_metadata": {
        "source": "stub",  # HONEST
        "_is_stub": True,
        "_reason": "FMP transformation not implemented (P0-CODE-2)"
    }
}
```

**Enforcement**: CI check fails if `_is_stub` not present when returning stub data

### Gate 3: No "Phase 1/Phase 2" Without Spec Approval

**Rule**: Phased implementation must be documented in architect spec

❌ **Not Allowed**:
```python
# Phase 1: Hardcoded weights
# Phase 2: Load from database
weights = {...}
```

✅ **Allowed** (only if spec defines phases):
```python
# Approved phased implementation per RATINGS_ARCHITECT.md section 8.3
# Phase 1 (Week 1-2): Hardcoded equal weights
# Phase 2 (Week 3-4): Rubric-driven weights from database
# Sign-off: @product-owner (2025-10-26)
weights = {...}
```

**Enforcement**: Manual code review checks for phase comments against spec

### Gate 4: No Error Stubs

**Rule**: Never return error messages as "working" implementation

❌ **Not Allowed**:
```python
def macro_run_scenario(self, ...):
    return {"error": "Scenario service not yet implemented"}
```

✅ **Allowed**:
```python
def macro_run_scenario(self, ...):
    # Call actual service
    result = await self.scenarios_service.run_scenario(...)
    return result
```

✅ **Allowed** (if truly not ready):
```python
# Don't merge this method until service is ready!
# Keep in feature branch until P1-CODE-1 complete
def macro_run_scenario(self, ...):
    raise NotImplementedError(
        "Scenario service pending implementation (P1-CODE-1, Week 3-4)"
    )
```

**Enforcement**: CI check fails if `grep "not yet implemented"`

---

## Part 4: Testing Guardrails

### No Tests = No Merge

**Rule**: Every feature must have tests BEFORE merge

**Required Test Types**:
1. **Unit tests** - Test individual methods
2. **Integration tests** - Test end-to-end pattern execution
3. **Golden tests** - Test against spec acceptance criteria
4. **Error handling tests** - Test graceful degradation

❌ **Not Allowed**:
```python
# Ship code without tests, "will add tests later"
```

✅ **Required**:
```python
# tests/unit/test_ratings.py
async def test_moat_strength_loads_rubric_weights():
    """Test that moat_strength loads weights from database."""
    # Setup: Insert test rubric
    # Execute: Call moat_strength()
    # Assert: Weights match rubric, not hardcoded 25%

# tests/integration/test_buffett_checklist_pattern.py
async def test_buffett_checklist_with_real_data():
    """Test buffett_checklist pattern end-to-end."""
    # Given: AAPL fundamentals in database
    # When: Execute buffett_checklist pattern
    # Then: Rating != 7.0 (stub default)
    # And: Different securities get different ratings
```

### Test Data Must Be Real (or Explicitly Stub)

❌ **Not Allowed**:
```python
# Test passes with stubs, developer thinks it works
def test_fundamentals_loading():
    result = load_fundamentals("AAPL")
    assert result is not None  # Passes with stubs!
```

✅ **Required**:
```python
# Test explicitly checks for real data
def test_fundamentals_loading_with_real_fmp_data():
    result = load_fundamentals("AAPL")
    assert result["_is_stub"] == False, "Must use real FMP data"
    assert result["roe_5y_avg"] > 0, "Real data should have positive ROE"
    assert result["_source"] == "fmp", "Source must be FMP, not stub"
```

---

## Part 5: Documentation Guardrails

### No Code Without Docs

**Rule**: Documentation updated in SAME PR as code

**Required Updates**:
1. **README.md** - If feature is user-facing
2. **PRODUCT_SPEC.md** - If changing capabilities
3. **Agent architect doc** - If changing agent behavior
4. **FEATURE_STATUS_MATRIX.md** - Always update status
5. **GOVERNANCE_VIOLATIONS_AUDIT.md** - If remediating a violation

❌ **Not Allowed**:
```
PR #123: Implement rubric loading
Files changed:
  ✅ backend/app/services/ratings.py
  ❌ No documentation updates
```

✅ **Required**:
```
PR #123: Implement rubric loading (P0-CODE-1)
Files changed:
  ✅ backend/app/services/ratings.py
  ✅ README.md (remove "⚠️ Ratings use hardcoded weights")
  ✅ PRODUCT_SPEC.md (update line 231 capability status)
  ✅ .claude/agents/business/RATINGS_ARCHITECT.md (update limitations)
  ✅ .ops/FEATURE_STATUS_MATRIX.md (mark P0-CODE-1 complete)
  ✅ .ops/GOVERNANCE_VIOLATIONS_AUDIT.md (mark violation remediated)
```

### Honest Documentation

**Rule**: Documentation must match code reality

❌ **Not Allowed**:
```markdown
## Features
- ✅ Macro scenarios - Operational
```
(When code returns "not yet implemented")

✅ **Required**:
```markdown
## Features
- 🚧 Macro scenarios - In Progress (P1-CODE-1, Week 3-4)
  - Service exists (scenarios.py)
  - Agent wiring pending
  - Currently returns error stub
```

---

## Part 6: PR Review Checklist

### For PR Author (Self-Review)

Before submitting PR:
- [ ] All acceptance criteria met (not partially met)
- [ ] No TODO comments without GitHub issue numbers
- [ ] No stub returns without `_is_stub` metadata
- [ ] No "Phase 1/2" comments without spec approval
- [ ] No hardcoded values that should be from database
- [ ] Tests written and passing (unit + integration + golden)
- [ ] Documentation updated (README, PRODUCT_SPEC, architect docs)
- [ ] FEATURE_STATUS_MATRIX.md updated
- [ ] If remediating violation: GOVERNANCE_VIOLATIONS_AUDIT.md updated
- [ ] No `grep "not yet implemented"` in merged code
- [ ] No misleading logs (stubs logged as stubs)

### For Code Reviewer

Mandatory checks (block merge if any fail):
- [ ] **Spec compliance**: Compare code to architect spec requirements
- [ ] **No shortcuts**: No TODOs, stubs, or hardcoded values without approval
- [ ] **Tests verify claims**: If code claims to work, tests prove it
- [ ] **Documentation accurate**: Docs match what code actually does
- [ ] **Error handling**: Graceful degradation, not error stubs
- [ ] **Metadata honest**: `_source`, `_is_stub` flags match reality

### Automated CI Checks

```bash
# .github/workflows/quality-gates.yml

# Check 1: No TODOs without issue numbers
- name: Check TODOs have issue references
  run: |
    if grep -r "TODO" backend/ | grep -v "#[0-9]"; then
      echo "❌ Found TODO without issue number"
      exit 1
    fi

# Check 2: No "not yet implemented" errors
- name: Check for error stubs
  run: |
    if grep -r "not yet implemented" backend/app; then
      echo "❌ Found error stub in code"
      exit 1
    fi

# Check 3: Metadata flags for stubs
- name: Check stub metadata
  run: |
    python scripts/check_stub_metadata.py

# Check 4: Documentation updated
- name: Check docs updated with code
  run: |
    python scripts/check_docs_updated.py

# Check 5: Tests pass with real data
- name: Run integration tests with real providers
  env:
    FMP_API_KEY: ${{ secrets.FMP_API_KEY }}
  run: |
    pytest tests/integration/ --real-data
```

---

## Part 7: Escalation Process

### When You're Truly Blocked

**Definition of "Blocked"**:
- Tried asking for help (no response in 4 hours)
- Researched thoroughly (2+ hours, read official docs)
- Identified specific missing dependency or knowledge gap
- Can articulate exactly what's needed to unblock

**Escalation Steps**:

1. **Document Blocker** (15 minutes)
   ```markdown
   # Blocker: P0-CODE-1 - Rubric Loading

   ## What I'm Trying to Do
   Load component weights from rating_rubrics.overall_weights JSONB column

   ## What's Blocking Me
   Don't know how to deserialize JSONB to Python dict with asyncpg

   ## What I've Tried
   1. Read asyncpg docs (no JSONB examples)
   2. Searched codebase for JSONB usage (found none)
   3. Asked in #backend-help (no response yet, posted 3 hours ago)

   ## What I Need
   - Example of JSONB query with asyncpg
   - OR alternative approach (serialize as TEXT?)
   - OR database expert to pair program (30 min)

   ## Impact If Not Unblocked
   - Cannot complete P0-CODE-1 (critical path blocker)
   - Ratings will continue using hardcoded weights
   - Week 1-2 timeline at risk
   ```

2. **Escalate to Tech Lead** (via Slack/email)
   - Share blocker documentation
   - Request specific help needed
   - Propose workaround ONLY if approved

3. **Await Approval for Scope Change** (if workaround needed)
   - **Example Workaround**: "Store weights as TEXT JSON instead of JSONB"
   - Get written approval from tech lead + product owner
   - Document approval in code comments
   - Create follow-up ticket to fix properly

### What NOT to Do When Blocked

❌ **Silently take shortcut**:
```python
# No one knows I'm blocked, I'll just hardcode for now
weights = {"roe": 0.25, ...}
```

❌ **Add TODO and move on**:
```python
# TODO: Fix this later
weights = {"roe": 0.25, ...}
```

❌ **Assume stubs are OK**:
```python
# I'll implement real data later
return stub_data()
```

✅ **Proper escalation**:
1. Document blocker thoroughly
2. Ask for help publicly (team chat)
3. Research alternative approaches
4. Only take workaround if approved IN WRITING
5. Document approval + create remediation ticket

---

## Part 8: Consequences for Shortcuts

### First Offense (Warning)

- PR rejected with explanation
- Required to fix before re-review
- 1-on-1 with tech lead on guardrails
- Name added to "watched closely" list for next PRs

### Second Offense (Performance Plan)

- Meeting with tech lead + manager
- Written performance improvement plan
- All PRs require senior engineer review
- Pair programming required for 2 weeks

### Third Offense (Serious)

- Escalation to engineering director
- Possible removal from project
- Impact on performance review

### Why Strict Enforcement?

**The current codebase has**:
- 54 TODOs (shortcuts taken)
- 186 stub references (shortcuts taken)
- 4 governance deviations (shortcuts taken)
- 6 of 12 patterns broken (shortcuts taken)

**Each shortcut compounds**:
- Creates technical debt
- Misleads users
- Wastes future engineering time
- Erodes trust in documentation
- Delays production readiness

**One more shortcut cycle = 10 more weeks of remediation**

---

## Part 9: Success Stories (Proper Approach)

### Example 1: Rubric Loading Done Right

**Blocker**: Don't know how to query JSONB with asyncpg

**Wrong Approach** ❌:
```python
# I'll just hardcode for now, fix later
weights = {"roe": 0.25, "margin": 0.25}  # TODO: Load from DB
```

**Right Approach** ✅:
```python
# 1. Asked in #backend-help
# 2. Got answer from @database-expert in 30 minutes
# 3. Learned: row["overall_weights"] already deserializes JSON
# 4. Implemented properly:

async def _load_rubric_weights(self, rating_type: str):
    row = await conn.fetchrow(
        "SELECT overall_weights FROM rating_rubrics WHERE rating_type = $1",
        rating_type
    )
    # PostgreSQL JSONB auto-deserializes to dict!
    weights = {k: Decimal(str(v)) for k, v in row["overall_weights"].items()}
    return weights
```

**Result**: Feature works correctly, no technical debt, no remediation needed

### Example 2: FMP Transformation Done Right

**Blocker**: FMP API returns nested dict, transformation is complex

**Wrong Approach** ❌:
```python
# This is too hard, I'll use stubs for now
logger.info("Successfully fetched real fundamentals")  # LIE
return self._stub_fundamentals()  # SHORTCUT
```

**Right Approach** ✅:
```python
# 1. Broke transformation into small functions
# 2. Wrote unit tests for each helper
# 3. Asked for code review of transformation logic
# 4. Implemented properly:

def _transform_fmp_to_ratings_format(self, fmp_data, fmp_ratios):
    """Transform FMP API response to ratings format."""
    # Helper functions make this manageable
    roe = self._calculate_5y_avg(fmp_data, "returnOnEquity")
    margin = self._calculate_5y_avg(fmp_data, "grossProfitMargin")
    debt_equity = Decimal(str(fmp_ratios[0]["debtEquityRatio"]))

    return {
        "roe_5y_avg": roe,
        "gross_margin_5y_avg": margin,
        "debt_equity_ratio": debt_equity,
        "_is_stub": False,  # HONEST
        "_source": "fmp"
    }
```

**Result**: Real data flows through, accurate ratings, no shortcuts

---

## Part 10: Guardrail Enforcement Checklist

### Daily (Developer)
- [ ] Before committing: Self-review against checklist
- [ ] Before PR: Run automated checks locally
- [ ] After feedback: Address ALL comments (no "will fix later")

### Weekly (Tech Lead)
- [ ] Review all merged PRs for shortcuts
- [ ] Audit new TODOs (should be zero)
- [ ] Check FEATURE_STATUS_MATRIX.md is up-to-date
- [ ] Verify documentation matches code

### Sprint End (Team)
- [ ] Demo all completed features (prove they work)
- [ ] Review governance violations audit (should decrease)
- [ ] Update remediation plan progress
- [ ] Celebrate zero-shortcut sprints!

---

## Appendix A: Quick Reference

### When Facing Difficulty, Ask:

1. **"Have I read the spec?"** (Don't assume, verify)
2. **"Have I asked for help?"** (Don't struggle alone)
3. **"Have I researched alternatives?"** (Don't take first shortcut)
4. **"Is this shortcut approved?"** (Get it in writing)
5. **"Will this create technical debt?"** (If yes, don't do it)

### Red Flags (Stop and Escalate)

🚩 "I'll fix this later"
🚩 "This is just Phase 1"
🚩 "We can use stubs for now"
🚩 "I'll document this later"
🚩 "TODO: Implement properly"
🚩 "No one will notice"
🚩 "It's good enough for now"

### Green Flags (Proper Approach)

✅ "I asked for help and got unblocked"
✅ "I read the docs and found the solution"
✅ "I escalated and got approval for workaround"
✅ "I wrote tests to verify it works"
✅ "I updated docs to match code"
✅ "I refactored to avoid shortcuts"
✅ "I'm proud of this implementation"

---

## Appendix B: Approved Shortcuts Registry

**Rule**: Shortcuts require written approval and remediation plan

| Shortcut | Approved By | Date | Remediation | Status |
|----------|-------------|------|-------------|--------|
| Hardcoded rating weights | @product-owner | 2025-10-26 | P0-CODE-1 (20h, Week 1-2) | Open |
| Stub fundamentals transformation | @product-owner | 2025-10-26 | P0-CODE-2 (14h, Week 1-2) | Open |
| (Future shortcuts go here) | | | | |

**No shortcuts currently approved beyond those documented above.**

---

**Last Updated**: 2025-10-26
**Next Review**: Weekly (every Friday)
**Enforcement**: MANDATORY - No exceptions
**Approval Required**: Tech Lead + Product Owner for ANY new shortcut

**Remember**: Every shortcut creates 10x more work later. Do it right the first time.
