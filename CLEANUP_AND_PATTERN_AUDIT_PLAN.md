# Comprehensive Cleanup and Pattern Audit Plan

**Created**: October 10, 2025
**Purpose**: Clean up temporary files, validate legacy code, audit all 49 patterns, ensure Trinity compliance
**Status**: Ready for execution

---

## Phase 1: Temporary File Cleanup

### 1.1 Python Cache Files (15,610 files)
**Action**: Remove all __pycache__ directories and .pyc files
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
```

**Impact**: ~15,610 files removed, no functional impact (cache will regenerate)

### 1.2 Temporary Session Documentation (26 files)
**Action**: Archive or remove temporary session reports

**Files to Remove** (session-specific, no longer needed):
- SESSION_COMPLETE_SUMMARY.md
- SESSION_SUMMARY.md
- FINAL_SESSION_COMPLETE.md
- REMEDIATION_SESSION_SUMMARY.md
- PHASE0_DAY1_COMPLETE.md
- PHASE0_DAY2-3_COMPLETE.md
- PHASE0_DAY4_COMPLETE.md
- PHASE0_WEEK1_DAYS1-4_COMPLETE.md
- PHASE1_EMERGENCY_FIX_COMPLETE.md
- ECONOMIC_DASHBOARD_COMPLETE.md
- REFACTORING_PHASE2_COMPLETE.md
- PATTERN_REMEDIATION_COMPLETE.md
- INTEGRATION_TEST_SUMMARY.md
- DEAD_CODE_VALIDATION_REPORT.md
- TEMPLATE_GENERATION_REPORT.md
- UI_STRUCTURE_IMPROVEMENT_REPORT.md
- TRINITY_3.0_COMPLETION_REPORT.md
- TRINITY_3.0_DETAILED_EXECUTION_PLAN.md

**Files to Keep** (permanent reference):
- README.md
- CLAUDE.md
- TROUBLESHOOTING.md
- DEPLOYMENT_CHECKLIST.md
- CAPABILITY_ROUTING_GUIDE.md
- SYSTEM_STATUS.md
- TECHNICAL_DEBT_AUDIT.md
- COMPLETION_FINAL.md (final summary)
- REMEDIATION_COMPLETE.md (final remediation summary)

**Impact**: ~18 temporary docs removed

---

## Phase 2: Legacy Code Validation

### 2.1 Already Removed
- ✅ dawsos/capabilities/fred.py (removed in Phase 4)

### 2.2 Candidates for Review
**Action**: Verify these files are still used or can be safely removed

```bash
# Search for unused imports/references
grep -r "from deprecated" dawsos/ --include="*.py"
grep -r "# TODO: Remove" dawsos/ --include="*.py"
grep -r "# DEPRECATED" dawsos/ --include="*.py"
```

**Files to Investigate**:
1. `dawsos/core/api_normalizer.py` - Check if still used (replaced by Pydantic)
2. Any files in `dawsos/agents/` that reference removed agents (equity_agent, macro_agent, risk_agent)
3. Archived pattern files (if any exist)

---

## Phase 3: Pattern Audit (49 Patterns)

### 3.1 Trinity Compliance Audit
**Goal**: Ensure all 49 patterns follow Trinity execution flow

**Validation Criteria**:
1. ✅ Primary action is `execute_through_registry` or `execute_by_capability`
2. ✅ No direct agent calls (e.g., `agent: "claude"`)
3. ✅ Proper trigger structure
4. ✅ Valid JSON syntax
5. ✅ All referenced capabilities exist in AGENT_CAPABILITIES
6. ✅ Proper error handling patterns
7. ✅ Metadata complete (version, last_updated)

**Validation Command**:
```bash
python scripts/lint_patterns.py
```

**Expected Result**: 0 errors, 1 warning (cosmetic)

### 3.2 Pattern Functionality Test
**Goal**: Verify each pattern executes end-to-end

**Test Categories**:
1. **Analysis Patterns** (15): Stock analysis, economy, portfolio, risk
2. **Data Retrieval** (10): Fetch stock, news, economic data
3. **Calculation** (8): DCF, ratios, valuation
4. **Comparison** (5): Stock vs stock, sector comparison
5. **Workflow** (11): Multi-step processes

**Test Approach**:
```python
# For each pattern:
# 1. Load pattern
# 2. Execute with test context
# 3. Verify result structure
# 4. Check for errors
```

### 3.3 Pattern Categorization Review
**Current**: 90% categorized (44/49)

**Uncategorized Patterns** (5):
- schema.json (system file, not a pattern)
- 4 others to identify and categorize

**Action**: Complete categorization to 100%

### 3.4 Pattern Deduplication
**Goal**: Identify and merge duplicate/overlapping patterns

**Potential Duplicates**:
- Check for patterns with similar triggers
- Check for patterns calling same capability with similar params
- Verify uniqueness of functionality

---

## Phase 4: Code Quality Checks

### 4.1 Import Cleanup
**Action**: Remove unused imports

```bash
# Find files with unused imports
python -m pyflakes dawsos/ | grep "imported but unused"
```

### 4.2 Type Hint Coverage
**Current**: 85%+

**Action**: Add type hints to remaining untyped functions

### 4.3 Error Handling Audit
**Goal**: Ensure no bare except blocks or silent failures

```bash
# Find bare except
grep -rn "except:" dawsos/ --include="*.py" | grep -v "except Exception"

# Find pass statements in except blocks
grep -A1 "except" dawsos/ --include="*.py" | grep "pass"
```

---

## Phase 5: Pattern Execution Plan

### 5.1 Sequential Execution
```bash
# 1. Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 2. Archive temporary docs
mkdir -p archive/session_reports
mv *SESSION*.md *PHASE*.md archive/session_reports/ 2>/dev/null

# 3. Run pattern linter
python scripts/lint_patterns.py

# 4. Run full validation suite
pytest dawsos/tests/validation/

# 5. Commit cleanup
git add -A
git commit -m "chore: Cleanup temporary files and validate all patterns"
git push
```

### 5.2 Validation Checklist
- [ ] All __pycache__ removed
- [ ] Temporary docs archived/removed
- [ ] Pattern linter: 0 errors
- [ ] All tests passing
- [ ] No import errors
- [ ] No broken references
- [ ] Trinity compliance verified
- [ ] Documentation updated

---

## Phase 6: Expected Outcomes

### Metrics Before Cleanup
- Total Files: ~2,500
- Documentation Files (root): 49
- Python Cache Files: 15,610
- Patterns: 49 (0 errors, 1 warning)
- API Validation: 100%

### Metrics After Cleanup
- Total Files: ~1,000 (reduction of ~16,500 cache files)
- Documentation Files (root): ~15 (permanent only)
- Python Cache Files: 0 (will regenerate as needed)
- Patterns: 49 (0 errors, 0 warnings - if cosmetic warning fixed)
- API Validation: 100% (maintained)
- Code Quality: A+ grade maintained

### Benefits
1. **Cleaner Repository**: Easier to navigate without temporary files
2. **Faster git operations**: Fewer files to track
3. **Clearer documentation**: Only permanent docs in root
4. **Validated patterns**: All 49 patterns tested and compliant
5. **Production ready**: Clean codebase ready for deployment

---

## Risk Assessment

**Low Risk Actions** (safe to execute):
- ✅ Removing __pycache__ (regenerates automatically)
- ✅ Archiving session reports (not referenced by code)
- ✅ Running linters and tests (read-only)

**Medium Risk Actions** (require validation):
- ⚠️ Removing legacy code (must verify not imported)
- ⚠️ Merging duplicate patterns (must verify functionality)

**High Risk Actions** (not recommended without thorough testing):
- ❌ Modifying pattern structure
- ❌ Removing core files

---

## Execution Timeline

**Total Estimated Time**: 2-3 hours

1. Phase 1 (Cache cleanup): 5 minutes
2. Phase 2 (Doc cleanup): 10 minutes
3. Phase 3 (Legacy code): 30 minutes
4. Phase 4 (Pattern audit): 60 minutes
5. Phase 5 (Validation): 30 minutes
6. Phase 6 (Commit): 10 minutes

**Recommended Approach**: Execute phases sequentially, commit after each phase

---

## Success Criteria

✅ **Cleanup Complete** when:
1. Zero __pycache__ directories
2. < 20 markdown files in root (permanent docs only)
3. Pattern linter: 0 errors, 0 warnings
4. All tests passing
5. Git working tree clean
6. No broken imports
7. Trinity compliance: 100%
8. API validation: 100% (maintained)

---

**Next Steps**: Execute Phase 1 (Python cache cleanup) and proceed sequentially through phases.
