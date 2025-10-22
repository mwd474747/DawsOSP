# Trinity 3.0 Migration Specialist Agents

This directory contains specialized Claude agents configured to support the Trinity 3.0 migration from DawsOS 2.0.

## Migration Team Structure

### **Migration Lead** ([trinity3_migration_lead.md](trinity3_migration_lead.md))
- **Role**: Coordinates all migration activities across 12 weeks
- **Responsibilities**:
  - Validate deliverables at each phase
  - Enforce quality gates (90%+ accuracy, zero mock data, etc.)
  - Track MIGRATION_STATUS.md progress
  - Escalate blockers
- **When to Use**: Weekly progress reviews, phase transitions, quality validation

---

## Week-by-Week Specialist Assignments

### **Week 1-2: Intelligence Specialist** ([trinity3_intelligence_specialist.md](trinity3_intelligence_specialist.md))
- **Deliverables**:
  - Day 2-3: Entity extraction (406 lines, 20 test queries, 90%+ accuracy)
  - Day 4: Conversation memory (254 lines, reference resolution)
  - Day 5: Enhanced chat processor (207 lines, intent routing)
- **Exit Criteria**:
  - ✅ Entity extraction: 18/20 tests pass
  - ✅ Conversation memory: Reference resolution 100% on basic cases
  - ✅ Enhanced chat: Routes intents correctly

### **Week 2-3, 6, 9: Pattern Specialist** ([trinity3_pattern_specialist.md](trinity3_pattern_specialist.md))
- **Deliverables**:
  - Week 2: Pattern engine (2,291 lines) + 24 actions + template validation
  - Week 3: 5 smart patterns (conditional execution)
  - Week 6: 3 workflow patterns (deep_dive, buffett_checklist, moat_analyzer)
  - Week 9: 6 economic patterns (Bloomberg-quality)
- **Exit Criteria**:
  - ✅ All patterns execute without errors
  - ✅ Template fields 100% resolved (no literal `{field}` in output)
  - ✅ Capability routing correct (no API calls for knowledge files)

### **Week 4-5: Data Specialist** ([trinity3_data_specialist.md](trinity3_data_specialist.md))
- **Deliverables**:
  - Week 4: OpenBB adapter mapping 103 capabilities
  - Week 5: Remove PredictionService, CycleService (100% mock data)
  - Multi-tier caching (95%+ hit rate)
- **Exit Criteria**:
  - ✅ All 103 capabilities have real data sources
  - ✅ Zero mock data in codebase
  - ✅ Cache hit rate 95%+
  - ✅ < 2s average query response

### **Week 3, 10: Agent Specialist** ([trinity3_agent_specialist.md](trinity3_agent_specialist.md))
- **Deliverables**:
  - Week 3: Agent runtime + registry + 5 core agents (claude, financial_analyst, macro_analyst, portfolio_manager, risk_analyst)
  - Week 10: Remaining 10 agents (technical, options, sentiment, sector, quant, event, opportunity, compliance, performance, research)
- **Exit Criteria**:
  - ✅ All 15 agents ported
  - ✅ All 103 capabilities implemented
  - ✅ Capability routing works for all

### **Week 7-8: UI Specialist** ([trinity3_ui_specialist.md](trinity3_ui_specialist.md))
- **Deliverables**:
  - Week 7: Enhanced chat interface with entity extraction display, conversation memory
  - Week 8: 5 feature views (equity, portfolio, macro, economic, market)
- **Exit Criteria**:
  - ✅ Bloomberg aesthetic (purple-pink-blue gradient, glass morphism, dark theme)
  - ✅ **NO EMOJIS** (professional only)
  - ✅ < 2s UI response time
  - ✅ All views integrated with patterns

---

## Specialist Agent Usage Guide

### How to Work with Migration Specialists

1. **Start of Week**: Consult assigned specialist for that week
   - Example: Week 1 → Read `trinity3_intelligence_specialist.md`
   - Follow day-by-day breakdown
   - Use test requirements provided

2. **During Implementation**:
   - Reference specialist's code examples
   - Follow success criteria
   - Run tests as specified

3. **End of Week**: Report to Migration Lead
   - Validate exit criteria met
   - Update MIGRATION_STATUS.md
   - Escalate any blockers

### Example Workflow

**Week 1 - Intelligence Layer**:
```bash
# Day 1
1. Read .claude/trinity3_intelligence_specialist.md
2. Create directory structure (trinity3/intelligence/)
3. Install dependencies (instructor, anthropic, pydantic)
4. Test API connection

# Day 2-3
1. Port entity_extractor.py (406 lines)
2. Port all 11 Pydantic schemas
3. Create test_entity_extractor.py with 20 queries
4. Run tests: python -m pytest trinity3/tests/test_entity_extractor.py
5. Verify 18/20 pass (90%+ accuracy)

# Day 4
1. Port conversation_memory.py (254 lines)
2. Add file persistence
3. Test reference resolution
4. Verify 100% on basic cases ("it" → last symbol)

# Day 5
1. Port enhanced_chat_processor.py (207 lines)
2. Wire entity extractor + memory
3. Test intent routing
4. Report to migration lead

# Week End
1. Run full test suite: pytest trinity3/tests/ -v
2. Validate exit criteria (35 tests pass)
3. Update MIGRATION_STATUS.md
4. Get approval from migration lead to proceed to Week 2
```

---

## Migration Plan Context

These specialists implement the 12-week migration plan documented in:
- **[trinity3/MIGRATION_PLAN.md](../trinity3/MIGRATION_PLAN.md)** - Full 12-week plan
- **[trinity3/MIGRATION_STATUS.md](../MIGRATION_STATUS.md)** - Progress tracker
- **[trinity3/MIGRATION_SOURCES.md](../trinity3/MIGRATION_SOURCES.md)** - Source file inventory

---

## Key Principles (All Specialists Must Follow)

### 1. Preserve DawsOS 2.0 Intelligence
- ✅ Entity extraction (Instructor + Pydantic)
- ✅ Conversation memory (multi-turn context)
- ✅ Smart patterns (conditional routing)
- ✅ Workflow orchestration (6-step deep dives)
- ✅ 103 capabilities (agent system)

### 2. Eliminate Technical Debt
- ❌ Template field fragility → Add validation
- ❌ Capability misuse → Fix routing
- ❌ Mock data → Use OpenBB/FRED
- ❌ Hybrid routing → Pure capability-based

### 3. Bloomberg Terminal Quality
- Professional UI (NO EMOJIS)
- Real data only (zero mocks)
- < 2s response time
- 95%+ cache hit rate

---

## Contact & Escalation

**For Migration Questions**:
1. Consult specialist agent for current week
2. Check [trinity3/MIGRATION_PLAN.md](../trinity3/MIGRATION_PLAN.md)
3. Review DawsOS 2.0 source files
4. Escalate to migration lead if blocked

**Status Updates**:
- Daily: Comment in code
- Weekly: Update MIGRATION_STATUS.md
- Phase completion: Get migration lead approval

---

## Success Metrics (Week 12 Launch Criteria)

- ✅ 50 test scenarios 100% passing
- ✅ < 2s average query response
- ✅ 95%+ cache hit rate
- ✅ Zero critical bugs in beta
- ✅ 10 beta users positive feedback
- ✅ Zero mock data (100% real sources)
- ✅ All 14 patterns working (5 smart + 3 workflows + 6 economic)
- ✅ All 15 agents operational
- ✅ All 103 capabilities implemented

**If all criteria met**: Production launch ✅
**If any fail**: Continue work, do not launch
