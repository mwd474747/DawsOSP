# Pattern Migration Plan - Trinity Compliance

## Executive Summary

**Goal**: Migrate 36 patterns from direct agent calls to Trinity-compliant registry execution.

**Timeline**: 2-3 hours with automation
- 30 min: Build migration script
- 60 min: Automated migration + review
- 30 min: Add versioning metadata
- 30 min: Testing and validation

**Strategy**: Automated transformation with manual review of complex cases.

---

## Pattern Analysis

### Current State
- **36 patterns** need migration
- **3 anti-patterns** detected:
  1. Direct agent references: `"agent": "agent_name"`
  2. Method specifications: `"method": "process"` (not needed with adapter)
  3. Missing version metadata: All patterns lack `version` and `last_updated`

### Migration Taxonomy

#### Type A: Simple Agent Calls (28 patterns)
**Pattern**: Direct agent call with params
```json
{
  "agent": "data_harvester",
  "method": "process",
  "params": {...},
  "output": "result"
}
```

**Fix**: Use registry action
```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "data_harvester",
    "context": {...}
  },
  "save_as": "result"
}
```

**Affected Patterns**:
- Root: `sector_rotation.json`, `comprehensive_analysis.json`
- Queries: All 6 patterns
- Workflows: All 4 patterns
- Actions: All 5 patterns
- UI: Most steps in 6 patterns
- Analysis: Most steps in 9 patterns

#### Type B: Already Compliant (9 patterns)
**Pattern**: Uses actions, not direct agent calls
```json
{
  "action": "knowledge_lookup",
  "params": {...}
}
```

**Fix**: None needed, just add versioning

**Affected Patterns**:
- `analysis/moat_analyzer.json` (fully action-based)
- `analysis/buffett_checklist.json`
- System/meta patterns (already designed for Trinity)

#### Type C: Hybrid Patterns (7 patterns)
**Pattern**: Mix of agent calls and actions
```json
[
  {"agent": "data_harvester", ...},
  {"action": "enriched_lookup", ...},
  {"agent": "pattern_spotter", ...}
]
```

**Fix**: Convert agent steps to registry actions

**Affected Patterns**:
- `sector_rotation.json` (has both)
- `comprehensive_analysis.json`
- Several analysis patterns

---

## Migration Strategy

### Phase 1: Automated Transformation (60 min)

**Script**: `scripts/migrate_patterns.py`

**Transformations**:

1. **Agent Call → Registry Action**
   ```python
   # Before
   {
     "agent": "agent_name",
     "method": "process",  # Remove this
     "params": {...},
     "output": "var"
   }

   # After
   {
     "action": "execute_through_registry",
     "params": {
       "agent": "agent_name",
       "context": {...}  # Wrap params
     },
     "save_as": "var"  # Rename output → save_as
   }
   ```

2. **Field Normalization**
   - `output` → `save_as`
   - `outputs` → `save_as` (if single value) or keep `outputs` (if array)
   - `params` → `params.context` (for registry actions)
   - Remove `method` field entirely
   - `workflow` → `steps` (standardize)
   - `parameters` → `params` (standardize)

3. **Add Versioning**
   ```python
   pattern['version'] = '1.0'
   pattern['last_updated'] = datetime.now().strftime('%Y-%m-%d')
   ```

4. **Clean Unknown Fields**
   - Remove `step` field (just description, not needed)
   - Remove `method` field (adapter handles this)
   - Remove `order` field (sequential by default)
   - Remove `condition` field (not yet implemented)

### Phase 2: Special Cases (30 min)

**Manual Review Needed**:

1. **Governance Patterns** - Missing agent references
   - `policy_validation.json` - References "governance" agent (not registered)
   - `audit_everything.json` - Same issue
   - **Fix**: Change to `governance_agent` or create wrapper action

2. **Empty Patterns** - Missing steps
   - `data_quality_check.json`
   - `compliance_audit.json`
   - `cost_optimization.json`
   - **Fix**: Add placeholder steps or mark as templates

3. **Meta Patterns** - Already complex
   - `system/meta/*.json` - Review for Trinity compliance
   - May need manual adjustment

### Phase 3: Validation (30 min)

1. **Linter Check**
   ```bash
   python scripts/lint_patterns.py
   ```
   - Should show 0 errors
   - Warnings only for unknown fields (acceptable)

2. **Smoke Test**
   ```bash
   python -m pytest dawsos/tests/validation/test_all_patterns.py
   ```
   - Load each pattern
   - Validate structure
   - Test execution (dry run)

3. **Manual Spot Check**
   - Pick 5 patterns across categories
   - Execute with real data
   - Verify registry tracking works

---

## Implementation Script

### `scripts/migrate_patterns.py`

**Features**:
- Recursive pattern directory scan
- Automatic backup to `storage/backups/patterns_pre_migration/`
- Dry-run mode for preview
- Detailed change log
- Skip already-migrated patterns

**Usage**:
```bash
# Dry run (preview changes)
python scripts/migrate_patterns.py --dry-run

# Execute migration
python scripts/migrate_patterns.py

# Migrate specific category
python scripts/migrate_patterns.py --category analysis

# Verbose output
python scripts/migrate_patterns.py --verbose
```

**Algorithm**:
```python
def migrate_pattern(pattern):
    # 1. Backup original
    backup_pattern(pattern)

    # 2. Add versioning
    pattern['version'] = '1.0'
    pattern['last_updated'] = today()

    # 3. Normalize field names
    if 'workflow' in pattern:
        pattern['steps'] = pattern.pop('workflow')

    # 4. Migrate each step
    for step in pattern['steps']:
        if 'agent' in step:
            # Convert to registry action
            step['action'] = 'execute_through_registry'
            step['params'] = {
                'agent': step.pop('agent'),
                'context': step.pop('params', {})
            }

        # Remove deprecated fields
        step.pop('method', None)
        step.pop('step', None)
        step.pop('order', None)

        # Normalize output field
        if 'output' in step:
            step['save_as'] = step.pop('output')
        if 'parameters' in step:
            step['params'] = step.pop('parameters')

    # 5. Validate
    validate_pattern(pattern)

    # 6. Save
    save_pattern(pattern)

    return changes_made
```

---

## Migration Order (Optimal)

### Batch 1: Simple Patterns (Low Risk)
**Time**: 15 min
- Queries (6) - Straightforward data retrieval
- Actions (5) - Simple single-purpose patterns
- **Total**: 11 patterns

### Batch 2: Analysis Patterns (Medium Risk)
**Time**: 20 min
- Analysis (9) - Financial calculations, mostly action-based
- **Total**: 9 patterns

### Batch 3: Workflows (Medium Risk)
**Time**: 15 min
- Workflows (4) - Multi-step but well-structured
- Root (2) - Similar to workflows
- **Total**: 6 patterns

### Batch 4: UI Patterns (Low-Medium Risk)
**Time**: 10 min
- UI (6) - Simple interaction patterns
- **Total**: 6 patterns

### Batch 5: System/Governance (High Risk - Manual)
**Time**: 30 min
- System/meta (1) - Complex, review carefully
- Governance (3) - Has errors, need manual fixes
- **Total**: 4 patterns

---

## Success Criteria

### Must Have
- [ ] All 36 patterns migrated
- [ ] 0 linter errors
- [ ] All patterns have version/last_updated
- [ ] No direct agent references (except in execute_through_registry params)
- [ ] Automated tests pass

### Should Have
- [ ] <50 linter warnings (down from 240)
- [ ] Backup of original patterns
- [ ] Migration changelog
- [ ] Documentation updated

### Nice to Have
- [ ] Pattern execution benchmarks
- [ ] Compliance metrics dashboard
- [ ] Migration statistics report

---

## Rollback Plan

If migration fails:
1. Restore from `storage/backups/patterns_pre_migration/`
2. Review migration logs in `logs/pattern_migration.log`
3. Fix script and retry
4. Run linter to verify restoration

---

## Post-Migration Tasks

1. **Update Documentation**
   - Mark patterns as Trinity-compliant
   - Update pattern development guide
   - Add migration notes to CHANGELOG

2. **Monitor Compliance**
   - Track registry execution metrics
   - Monitor bypass warnings
   - Analyze pattern success rates

3. **Optimize Performance**
   - Profile pattern execution times
   - Identify bottlenecks
   - Cache frequently-used enriched data

4. **Expand Coverage**
   - Add missing governance patterns
   - Create new capability-based patterns
   - Implement conditional execution

---

## Risk Mitigation

### High Risk Areas
1. **Governance patterns** - Agent references broken
   - Mitigation: Manual fix, register missing agents

2. **Meta patterns** - Complex Trinity logic
   - Mitigation: Manual review, extensive testing

3. **Breaking existing workflows** - Users depend on patterns
   - Mitigation: Backup + dry-run + gradual rollout

### Testing Strategy
1. **Unit Tests**: Each pattern loads without errors
2. **Integration Tests**: Pattern execution with mock agents
3. **E2E Tests**: Real pattern execution with live data
4. **Regression Tests**: Compare outputs before/after migration

---

## Timeline

| Task | Time | Status |
|------|------|--------|
| Build migration script | 30 min | Pending |
| Dry-run and review | 15 min | Pending |
| Batch 1: Queries + Actions | 15 min | Pending |
| Batch 2: Analysis | 20 min | Pending |
| Batch 3: Workflows + Root | 15 min | Pending |
| Batch 4: UI | 10 min | Pending |
| Batch 5: System/Governance | 30 min | Pending |
| Validation + Testing | 30 min | Pending |
| **Total** | **2h 45min** | |

---

## Next Steps

1. Review and approve this plan
2. Build `scripts/migrate_patterns.py`
3. Run dry-run mode
4. Execute migration in batches
5. Validate with linter and tests
6. Monitor production usage
7. Document lessons learned

**Ready to proceed? The migration script is the critical path.**
