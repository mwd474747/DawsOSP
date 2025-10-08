# Parallel Refactoring Guide - Trinity 2.0 Completion

**Status**: Ready for Execution
**Duration**: 2 weeks (with 4 parallel agents)
**Output**: 100% capability routing, Trinity 2.0 complete

---

## Overview

This guide enables **4 Claude Code sessions** to work in parallel, completing Trinity 2.0 in 2 weeks instead of 6-8 weeks sequential.

### The 4 Specialized Agents

| Agent | Role | Files | Duration | Can Start |
|-------|------|-------|----------|-----------|
| **[parallel_refactor_coordinator.md](.claude/parallel_refactor_coordinator.md)** | Orchestrate all 4 streams | - | 2 weeks | ✅ Immediately |
| **[pattern_migration_specialist.md](.claude/pattern_migration_specialist.md)** | Migrate 48 patterns | `dawsos/patterns/*/*.json` | 10-12 hrs | ✅ Immediately |
| **[agent_capability_extractor.md](.claude/agent_capability_extractor.md)** | Refactor 15 agents | `dawsos/agents/*.py` | 12-15 hrs | ✅ Immediately |
| **[infrastructure_builder.md](.claude/infrastructure_builder.md)** | Build capability routing | `dawsos/core/*.py` | 8-10 hrs | ⏳ After Stream 2 at 80% |
| **[integration_validator.md](.claude/integration_validator.md)** | Test & validate | `dawsos/tests/trinity_2.0/` | 6-8 hrs | ⏳ After all 3 complete |

---

## Quick Start

### Step 1: Launch Coordinator (Session 1)

```bash
# In Claude Code, open this file:
.claude/parallel_refactor_coordinator.md

# Say: "I am the Parallel Refactor Coordinator. Begin coordination."
```

### Step 2: Launch Stream 1 (Session 2)

```bash
# In new Claude Code window, open:
.claude/pattern_migration_specialist.md

# Say: "I am the Pattern Migration Specialist. Start Stream 1."
```

### Step 3: Launch Stream 2 (Session 3)

```bash
# In new Claude Code window, open:
.claude/agent_capability_extractor.md

# Say: "I am the Agent Capability Extractor. Start Stream 2."
```

### Step 4: Coordinator Monitors

Coordinator checks in with Stream 1 and 2 daily, tracks progress.

### Step 5: Launch Stream 3 (Day 3-4)

When Stream 2 reaches 80%, coordinator launches Stream 3 in Session 4:

```bash
# In new Claude Code window, open:
.claude/infrastructure_builder.md

# Say: "I am the Infrastructure Builder. Start Stream 3."
```

### Step 6: Launch Stream 4 (Day 5-6)

When Streams 1, 2, 3 complete, coordinator launches Stream 4:

```bash
# Session 4 (reuse after Stream 3 done), open:
.claude/integration_validator.md

# Say: "I am the Integration Validator. Start Stream 4."
```

---

## Timeline

### Week 1

**Day 1-3**: Streams 1 & 2 in parallel
- Pattern migration (Stream 1): 50% → 100%
- Agent refactoring (Stream 2): 50% → 80%

**Day 3 Checkpoint**:
- Stream 1: 100% complete ✅
- Stream 2: 80% complete (method signatures stable)
- **Launch Stream 3** ✅

**Day 4-5**: Stream 2 finishes, Stream 3 builds
- Agent refactoring (Stream 2): 80% → 100%
- Infrastructure (Stream 3): 0% → 80%

**Day 5 Checkpoint**:
- Stream 1: 100% complete ✅
- Stream 2: 100% complete ✅
- Stream 3: 80% complete

### Week 2

**Day 6-7**: Stream 3 finishes
- Infrastructure (Stream 3): 80% → 100%

**Day 7 Checkpoint**:
- Streams 1, 2, 3: 100% complete ✅
- **Launch Stream 4** ✅

**Day 8-9**: Integration & Testing
- Pattern execution tests
- Capability routing tests
- Regression tests
- Performance benchmarks

**Day 10**: Final integration, commit, done

---

## Work Stream Dependencies

```
Day 1-3:  Stream 1 (Patterns)  ────┐
          Stream 2 (Agents)     ────┤
                                    ├──→ Day 7: Merge
Day 4-5:  Stream 3 (Infrastructure) ┤
                                    │
Day 8-9:  Stream 4 (Testing)    ────┘
```

**Critical Path**: Stream 2 → Stream 3 → Stream 4

**Parallel Efficiency**: 2 streams run simultaneously (Days 1-3)

---

## Coordination Protocol

### Daily Standup

**Time**: Start of each day (or first coordinator message)

**Template**:
```markdown
🗓️ Day N - Trinity 2.0 Parallel Refactoring

**Stream 1** (Patterns): [N/48 complete]
**Stream 2** (Agents): [N/15 complete]
**Stream 3** (Infrastructure): [status]
**Stream 4** (Testing): [status]

**Today's Focus**: [priorities]
**Blockers**: [any issues]
**Decisions Needed**: [any coordination needs]
```

### Progress Updates

Each stream reports to coordinator:
- **Morning**: Plan for the day
- **Midday**: Progress update
- **Evening**: Completion status

### Conflict Resolution

If streams conflict (e.g., both editing same file):
1. Coordinator pauses lower-priority stream
2. Higher-priority stream completes
3. Lower-priority stream resumes with changes

---

## Quality Gates

### Gate 1: Pattern Migration Complete
- ✅ 48/48 patterns using capability routing
- ✅ Pattern linter passes (0 errors)
- ✅ Entity extraction preserved

**Command**: `python scripts/lint_patterns.py`

### Gate 2: Agent Refactoring Complete
- ✅ 15/15 agents refactored
- ✅ 0 routing methods remaining
- ✅ 103 capabilities registered
- ✅ Method signatures documented

**Command**: `python scripts/audit_agent_methods.py`

### Gate 3: Infrastructure Complete
- ✅ AgentAdapter supports capability→method mapping
- ✅ Discovery APIs functional
- ✅ Graceful degradation working

**Command**: `pytest dawsos/tests/trinity_2.0/test_capability_routing.py`

### Gate 4: Integration Complete
- ✅ All 48 patterns execute successfully
- ✅ 90%+ test coverage
- ✅ Performance benchmarks pass
- ✅ No regressions

**Command**: `pytest dawsos/tests/trinity_2.0/ -v --cov`

---

## Simulation Results

### Pattern Analysis
- **Total patterns**: 48
- **Total steps**: 203
- **161 steps** use `execute_through_registry` (need migration)
- **10 complex patterns** (>5 steps each)
- **Most complex**: Buffett Checklist (8 steps), Economic Moat (8 steps)

### Agent Analysis
- **15 agents** to refactor
- **~10 routing methods** to remove/deprecate
- **103 capabilities** to expose
- **FinancialAnalyst**: 9 public methods (1 routing, 6 analysis)

### Infrastructure Gaps
- AgentAdapter needs capability→method mapping
- No discovery APIs (get_agents_with_capability, etc.)
- No graceful degradation
- No method introspection

---

## Communication Channels

### Between Sessions

**Shared files** for coordination:
```
.claude/parallel_refactor_coordinator.md  # Coordinator reads all agent files
docs/agent_method_signatures.md          # Stream 2 → Stream 3 handoff
STATUS_DAILY.md                          # Daily progress (all streams update)
```

### Status Updates

Each stream updates `STATUS_DAILY.md`:
```markdown
## Day 3 Status

### Stream 1 (Patterns)
**Progress**: 48/48 complete ✅
**Issues**: None
**Next**: Done, awaiting integration

### Stream 2 (Agents)
**Progress**: 12/15 complete (80%)
**Issues**: None
**Next**: Complete remaining 3 utility agents

### Stream 3 (Infrastructure)
**Progress**: Starting today
**Issues**: Waiting for method signatures
**Next**: AgentAdapter enhancement

### Stream 4 (Testing)
**Progress**: Not started
**Issues**: None
**Next**: Awaiting Streams 1-3 completion
```

---

## Success Metrics

### Velocity Targets

**Week 1**:
- Day 3: 75% complete (Streams 1 & 2)
- Day 5: 90% complete (Stream 3 added)

**Week 2**:
- Day 7: 95% complete (Stream 3 done)
- Day 10: 100% complete (Stream 4 done)

### Quality Metrics

- **Pattern lint errors**: 0
- **Agent routing methods**: 0
- **Test pass rate**: 100%
- **Performance**: No degradation

---

## Risk Mitigation

### Risk 1: Stream conflicts
**Mitigation**: Coordinator sequences overlapping work

### Risk 2: Breaking changes
**Mitigation**: Frequent integration checkpoints (Days 3, 5, 7)

### Risk 3: Dependency blocking
**Mitigation**: Stream 2 provides method signatures at 80% (Day 3)

### Risk 4: Test failures
**Mitigation**: Stream 4 has 2 days for fixes (Days 8-9)

---

## Rollback Plan

**If critical issue discovered**:

1. **Identify**: Which stream caused issue?
2. **Pause**: Stop dependent streams
3. **Fix or Rollback**:
   - Minor: Fix in place
   - Major: Rollback stream, restart
4. **Resume**: Re-sync dependent streams

**Rollback commands**:
```bash
# Rollback specific stream branch
git revert --no-commit feature/stream-name

# Restart from checkpoint
git checkout checkpoint-day-N
```

---

## Final Deliverables

Upon completion:

1. **Merged codebase**: All 4 streams integrated
2. **Test report**: All tests passing (100%)
3. **Performance report**: Benchmarks vs. baseline
4. **Documentation**: Migration guide, updated CLAUDE.md
5. **Commits**: 4 feature branches merged with detailed messages

**Trinity 2.0 Status**: ✅ COMPLETE
- 100% capability routing
- 0 text-parsing legacy
- Ready for Trinity 3.0 (AI orchestration layer)

---

## Next Steps

**Your First Actions**:

1. **User**: Review this guide
2. **User**: Launch coordinator (Session 1)
3. **Coordinator**: Read all 4 agent files
4. **Coordinator**: Launch Streams 1 & 2 (Sessions 2 & 3)
5. **Coordinator**: Monitor daily progress
6. **Coordinator**: Launch Stream 3 when Stream 2 hits 80%
7. **Coordinator**: Launch Stream 4 when Streams 1-3 done
8. **Coordinator**: Merge all streams, final validation

**Launch Command** (say to coordinator):
```
"Launch parallel refactoring. Start Streams 1 and 2 simultaneously.
Monitor progress and coordinate dependencies. Target: 2 weeks completion."
```

---

## Comparison: Sequential vs Parallel

### Sequential (Old Way)
- **Duration**: 6-8 weeks
- **Pattern migration**: Week 1-2
- **Agent refactoring**: Week 3-4
- **Infrastructure**: Week 5-6
- **Testing**: Week 7-8

### Parallel (New Way) ⚡
- **Duration**: 2 weeks
- **Week 1**: Patterns + Agents + Infrastructure (parallel + sequential)
- **Week 2**: Testing + Integration
- **Speedup**: 3-4x faster

---

**Status**: All agents created, ready for parallel execution
**Documentation**: Complete
**Tools**: All in `.claude/` directory

**Launch when ready!** 🚀
