# DawsOS Archived Legacy Code

This directory contains code that has been superseded by the Trinity Architecture (October 2025).

⚠️ **DO NOT USE** - This code is **NOT** imported or used by the active system.
It is kept for historical reference only.

---

## Archived Agents (Replaced by 15-Agent Model)

### equity_agent.py
- **Replaced by:** `financial_analyst`
- **Reason:** Functionality consolidated into financial_analyst agent
- **Date Archived:** 2025-10-04
- **Last Known Working:** Pre-Trinity (before October 2025)
- **Migration:** Use `financial_analyst` with `company_analysis` pattern

**Old usage:**
```python
equity = runtime.get_agent('equity_agent')
result = equity.analyze_stock('AAPL')
```

**New usage:**
```python
# Direct agent call
analyst = runtime.get_agent('financial_analyst')
result = analyst.process_request('analyze company', {'symbol': 'AAPL'})

# Pattern-driven (recommended)
result = pattern_engine.execute_pattern('company_analysis', {'symbol': 'AAPL'})
```

---

### macro_agent.py
- **Replaced by:** `financial_analyst` + `pattern_spotter` (via patterns)
- **Reason:** Macro analysis now handled by pattern-driven approach
- **Date Archived:** 2025-10-04
- **Migration:** Use `macro_analysis` pattern

**Old usage:**
```python
macro = runtime.get_agent('macro_agent')
result = macro.analyze_economy()
```

**New usage:**
```python
result = pattern_engine.execute_pattern('macro_analysis', {
    'indicators': ['GDP', 'UNRATE', 'CPI', 'FEDFUNDS']
})
```

---

### risk_agent.py
- **Replaced by:** `financial_analyst` + `governance_agent`
- **Reason:** Risk analysis split between financial analysis and compliance governance
- **Date Archived:** 2025-10-04
- **Migration:** Use `risk_assessment` pattern or `compliance_audit` pattern

**Old usage:**
```python
risk = runtime.get_agent('risk_agent')
result = risk.assess_risk('AAPL')
```

**New usage:**
```python
# Financial risk assessment
result = pattern_engine.execute_pattern('risk_assessment', {'symbol': 'AAPL'})

# Compliance/governance risk
result = pattern_engine.execute_pattern('compliance_audit', {'scope': 'portfolio'})
```

---

## Archived Orchestrators (Replaced by UniversalExecutor)

### claude_orchestrator.py
- **Replaced by:** `core/universal_executor.py`
- **Reason:** Trinity Architecture uses unified execution path
   (Request → UniversalExecutor → PatternEngine → AgentRuntime → Agents)
- **Date Archived:** 2025-10-02
- **Migration:** All orchestration now flows through `UniversalExecutor`

---

### orchestrator.py
- **Replaced by:** `core/universal_executor.py`
- **Reason:** Pre-Trinity orchestration logic superseded
- **Date Archived:** 2025-10-02
- **Migration:** Use Trinity execution flow

---

## Why These Were Removed

### Agent Consolidation Benefits
1. **Simplicity** - 15 focused agents vs 18+ specialized agents
2. **Trinity Alignment** - Pattern-driven routing instead of agent sprawl
3. **Maintainability** - Less code duplication, clearer responsibilities
4. **Performance** - Reduced overhead from fewer agent instances
5. **Testing** - Easier to test and validate agent interactions

### Functionality Preservation
All functionality from removed agents is preserved through:
- **Pattern-driven execution** - Patterns route to appropriate agents
- **Agent capability consolidation** - Related capabilities merged into core agents
- **Knowledge base** - Business logic moved to patterns and knowledge files

---

## Current Active Agents (15)

| Agent | Purpose |
|-------|---------|
| `graph_mind` | Knowledge graph operations |
| `claude` | LLM orchestration and reasoning |
| `data_harvester` | External data collection (APIs) |
| `data_digester` | Data normalization and ingestion |
| `relationship_hunter` | Graph relationship discovery |
| `pattern_spotter` | Pattern recognition and analysis |
| `forecast_dreamer` | Forecasting and predictions |
| `code_monkey` | Code generation |
| `structure_bot` | File/directory organization |
| `refactor_elf` | Code refactoring |
| `workflow_recorder` | Workflow capture |
| `workflow_player` | Workflow replay |
| `ui_generator` | UI component generation |
| `financial_analyst` | Financial analysis and metrics |
| `governance_agent` | Compliance and governance |

---

## Need Help Migrating?

See documentation:
- `docs/LEGACY_AGENT_MIGRATION.md` - Complete migration guide
- `docs/AGENT_PATTERN_MAPPING.md` - Which agents handle which patterns
- `docs/TRINITY_ARCHITECTURE.md` - Architecture overview

---

**Archive Created:** 2025-10-04
**Consolidation Plan:** See `/AGENT_CONSOLIDATION_PLAN.md`
