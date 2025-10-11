# DawsOS Development Memory

**System Version**: 3.0 (Trinity Architecture + Pydantic Validation)
**Grade**: A+ (100/100) 🎉
**Last Updated**: October 10, 2025
**Status**: ✅ Production Ready (100% API validation coverage achieved)
**Streamlit App**: ✅ Fully Operational (all launch errors fixed)

This file provides persistent context for all Claude Code sessions working on DawsOS.

---

## 🎯 Critical Development Principles

### 1. ALWAYS Use Specialist Agents

Before making ANY architectural, pattern, knowledge, or agent-related changes, **consult the appropriate specialist agent**:

- **🏛️ Trinity Architect** ([.claude/trinity_architect.md](.claude/trinity_architect.md)) - Architecture compliance, registry bypass detection, execution flow validation
- **🎯 Pattern Specialist** ([.claude/pattern_specialist.md](.claude/pattern_specialist.md)) - Pattern creation/debugging, enriched knowledge integration
- **📚 Knowledge Curator** ([.claude/knowledge_curator.md](.claude/knowledge_curator.md)) - Graph structure, 27 datasets, KnowledgeLoader usage
- **🤖 Agent Orchestrator** ([.claude/agent_orchestrator.md](.claude/agent_orchestrator.md)) - Agent development, capability-based routing, 50+ capabilities

**Usage Pattern**:
```
"I need to add a new financial analysis pattern. Let me consult the Pattern Specialist first..."
[Read .claude/pattern_specialist.md]
[Follow guidance for pattern structure, actions, triggers]
```

### 2. Trinity Architecture Compliance (Non-Negotiable)

**Execution Flow** (EVERY request must follow this):
```
Request → UniversalExecutor → PatternEngine → AgentRuntime/AgentRegistry → KnowledgeGraph
```

**❌ NEVER Do**:
```python
# Direct agent calls (bypasses registry)
agent = runtime.agents['claude']
result = agent.think(context)

# Ad-hoc file loading (bypasses cache)
with open('storage/knowledge/sector_performance.json') as f:
    data = json.load(f)
```

**✅ ALWAYS Do**:
```python
# Registry-compliant execution
result = runtime.exec_via_registry('claude', context)
# Or capability-based (preferred in 2.0)
result = runtime.execute_by_capability('can_analyze_text', context)

# Centralized knowledge loading
loader = get_knowledge_loader()
data = loader.get_dataset('sector_performance')
```

### 3. Capability-Based Routing (Trinity 2.0 Standard)

**ALWAYS prefer capability-based over name-based routing**:

```python
# Old way (still works but not preferred)
result = runtime.exec_via_registry('financial_analyst', context)

# New way (Trinity 2.0 - more flexible)
result = runtime.execute_by_capability('can_calculate_dcf', context)
```

See [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) for all 103 available capabilities.

---

## 📊 System State Reference

### Trinity 3.0 Refactoring (October 10, 2025)

**Status**: ✅ Core refactoring complete (Days 1-2 of 7)
**Timeline**: 2 days ahead of schedule

**Completed**:
- ✅ **Day 1**: Foundation cleanup - Removed 140+ lines of legacy code, simplified trinity_tabs initialization
- ✅ **Day 2**: Daily Events Calendar - 51 economic events (Q4 2025 - Q2 2026), functional calendar UI

**Key Changes**:
1. **Code Cleanup**:
   - Deleted 3 unused `display_*` functions (display_chat_interface, display_intelligence_dashboard, display_market_data)
   - Removed `_initialize_trinity_tabs()` function
   - Moved trinity_tabs initialization into `_render_main_tabs()` for encapsulation
   - Total: 140+ lines removed

2. **Daily Events Calendar**:
   - Created `economic_calendar.json` with 51 events (FOMC meetings, CPI, GDP, employment, etc.)
   - Integrated into KnowledgeLoader as 27th dataset
   - Replaced placeholder with functional UI: filters (time/importance/type), week grouping, visual indicators
   - Economic dashboard now has: Multi-indicator chart + Daily Events calendar

3. **Datasets**: 26 → 27 (added economic_calendar)

**Deferred to Future**:
- Pattern-driven UI (deferred to AG-UI Phase 1)

**Documentation**:
- [TRINITY_3.0_COMPLETION_REPORT.md](TRINITY_3.0_COMPLETION_REPORT.md) - Full refactoring report
- [TRINITY_3.0_OPTIMIZED_EXECUTION.md](TRINITY_3.0_OPTIMIZED_EXECUTION.md) - 7-day execution plan

---

### Current Metrics
- **Patterns**: 49 files (48 executable patterns + schema.json, 0 errors, 1 warning)
- **Pattern Organization**: 90% categorized (44/49 patterns across 7 categories)
- **Pattern Templates**: 9 critical templates added (markdown-formatted output)
- **Legacy Routing Migration**: 68% converted (60 steps from legacy to capability-based)
- **Agents**: 15 registered agents (21 files total including base classes)
- **Capabilities**: 103 unique capabilities across all agents
- **Datasets**: 27 (100% coverage in KnowledgeLoader - includes economic_calendar)
- **Functions Refactored**: 49+ functions decomposed (1,738 → 85 lines main functions)
- **Complexity Reduction**: 45% reduction in cyclomatic complexity (174 → 95 branches)
- **Tests**: 39 test modules, all passing (validation suite)
- **CI/CD**: `.github/workflows/compliance-check.yml` validates on push
- **Error Handling**: Standardized across codebase
- **Type Coverage**: 85%+ (320+ methods with type hints)
- **Graph Backend**: NetworkX 3.5 (10x performance improvement over legacy dict/list)

### Key Architectural Components

1. **UniversalExecutor** (`core/universal_executor.py`) - Single entry point
2. **PatternEngine** (`core/pattern_engine.py`) - 48 JSON patterns, primary action: `execute_through_registry`
3. **AgentRuntime** (`core/agent_runtime.py`) - Registry + capability routing
4. **AGENT_CAPABILITIES** (`core/agent_capabilities.py`) - 103 capabilities across 15 agents
5. **KnowledgeGraph** (`core/knowledge_graph.py`) - NetworkX backend, 96K+ nodes, **get_all_edges()** method
6. **KnowledgeLoader** (`core/knowledge_loader.py`) - 27 datasets, 30-min TTL cache
7. **PersistenceManager** (`core/persistence.py`) - Auto-rotation, 30-day backups, checksums
8. **TypingCompat** (`core/typing_compat.py`) - Python 3.9+ TypeAlias compatibility shim

### Pattern System (Post-Remediation)
- **48 executable patterns** organized across 7 categories
- **90% categorized** (44/49 patterns, excluding schema and system/meta)
- **68% capability-based routing** (60 legacy steps converted)
- **9 critical templates** added for user-facing markdown output
- **0 pattern errors, 1 cosmetic warning** (linter validated)
- **100% trigger uniqueness** (0 conflicts)

### 27 Enriched Datasets (100% Coverage)

**Core (7)**: sector_performance, economic_cycles, sp500_companies, sector_correlations, relationships, ui_configurations, company_database

**Investment Frameworks (4)**: buffett_checklist, buffett_framework, dalio_cycles, dalio_framework

**Financial Data (4)**: financial_calculations, financial_formulas, earnings_surprises, dividend_buyback

**Factor/Alt Data (4)**: factor_smartbeta, insider_institutional, alt_data_signals, esg_governance

**Market Indicators (6)**: cross_asset_lead_lag, econ_regime_watchlist, fx_commodities, thematic_momentum, volatility_stress, yield_curve

**System Metadata (2)**: agent_capabilities, economic_calendar

### Financial Analyst Capabilities (Migrated Oct 2025)

The **financial_analyst** agent now contains all functionality from archived equity_agent, macro_agent, and risk_agent:

**Equity Analysis** (from equity_agent):
- `analyze_stock_comprehensive()` - Full stock analysis with macro influences and catalysts
- `compare_stocks()` - Side-by-side comparison with peer analysis
- Graph-based macro influence tracing (inflation → sector → stock)
- Catalyst identification (SUPPORTS/STRENGTHENS relationships)
- Risk detection (PRESSURES/WEAKENS relationships)

**Macro Economy Analysis** (from macro_agent):
- `analyze_economy()` - Economic regime analysis (goldilocks/stagflation/recession)
- Economic indicator aggregation (GDP, CPI, unemployment, etc.)
- Regime-based sector opportunity identification
- Macro risk detection (recession signals, inflation spikes)

**Portfolio Risk Analysis** (from risk_agent):
- `analyze_portfolio_risk()` - Comprehensive portfolio analysis
- Concentration risk detection (>20% single, >60% top-5)
- Sector correlation proxy via graph relationships
- Portfolio-level macro sensitivity aggregation

All methods use Trinity-compliant execution through `runtime.execute_by_capability()` and graph-based analysis.

---

## 🚀 Common Development Tasks

### Launching the Streamlit App

**Quick Launch**:
```bash
./start.sh  # Handles everything automatically
```

**Manual Launch**:
```bash
# 1. Ensure venv exists and has dependencies
python3 -m venv dawsos/venv  # If venv doesn't exist
dawsos/venv/bin/pip install -r requirements.txt

# 2. Create .env if needed (optional - app works without it)
cp .env.example .env

# 3. Launch app
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501

# 4. Open http://localhost:8501
```

**Troubleshooting**:
- Port conflict: `lsof -ti:8501 | xargs kill -9`
- Import errors: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Python version: 3.10+ required, 3.13+ recommended

**Important Notes**:
- NEVER use relative imports (use absolute: `from core.X` not `from ..core.X`)
- ALWAYS use `self.logger` in class methods (not bare `logger`)
- ALWAYS use `get_stats()`, `get_all_edges()` for graph access (not direct `.nodes`, `.edges`)
- ALL imports from `dawsos/` use absolute paths from package root

### Adding a New Pattern

1. **Read** [.claude/pattern_specialist.md](.claude/pattern_specialist.md)
2. Create JSON in `dawsos/patterns/<category>/`
3. Required fields: `id`, `name`, `description`, `version`, `last_updated`, `triggers`, `steps`
4. Primary action: `execute_through_registry` (not direct agent calls)
5. Run linter: `python scripts/lint_patterns.py`
6. Test: `pytest dawsos/tests/validation/test_integration.py`

### Adding a New Agent

1. **Read** [.claude/agent_orchestrator.md](.claude/agent_orchestrator.md)
2. **Read** [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md)
3. Implement with standard methods: `process()`, `think()`, `analyze()`
4. Register with capabilities from `AGENT_CAPABILITIES`
5. Ensure results stored in graph (auto via AgentAdapter)
6. Test with smoke tests: `pytest dawsos/tests/validation/test_trinity_smoke.py`

### Modifying Knowledge Graph

1. **Read** [.claude/knowledge_curator.md](.claude/knowledge_curator.md)
2. **Read** [docs/KnowledgeMaintenance.md](docs/KnowledgeMaintenance.md)
3. Use safe methods: `get_node()`, `safe_query()`, never direct dict access
4. Load data via KnowledgeLoader (30-min cache)
5. Include `_meta` header in dataset files (version, last_updated, source)
6. Track confidence and metadata on all nodes

### Architecture Review

1. **Read** [.claude/trinity_architect.md](.claude/trinity_architect.md)
2. Check execution flows through UniversalExecutor
3. Verify no registry bypasses (direct agent calls)
4. Confirm KnowledgeLoader usage (not ad-hoc file reads)
5. Run full validation: `pytest dawsos/tests/validation/`

---

## 📚 Essential Documentation

### Development Guides (Read Before Coding)
- [README.md](README.md) - Quick start, system overview
- [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - Capability-based routing patterns
- [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md) - Agent implementation
- [docs/KnowledgeMaintenance.md](docs/KnowledgeMaintenance.md) - Dataset formats
- [docs/DisasterRecovery.md](docs/DisasterRecovery.md) - Backup/restore

### Status & Compliance
- [SYSTEM_STATUS.md](SYSTEM_STATUS.md) - Current A+ grade report (Oct 9, 2025)
- [COMPLETION_FINAL.md](COMPLETION_FINAL.md) - Final completion report with full timeline
- [REFACTORING_PHASE2_COMPLETE.md](REFACTORING_PHASE2_COMPLETE.md) - Phase 2 function decomposition
- [PATTERN_REMEDIATION_COMPLETE.md](PATTERN_REMEDIATION_COMPLETE.md) - Pattern remediation summary
- [TECHNICAL_DEBT_AUDIT.md](TECHNICAL_DEBT_AUDIT.md) - Technical debt audit (Oct 2025)

### Specialist Agents (Consult Before Changes)
- [.claude/README.md](.claude/README.md) - Agent system overview
- [.claude/trinity_architect.md](.claude/trinity_architect.md) - Architecture expert
- [.claude/pattern_specialist.md](.claude/pattern_specialist.md) - Pattern expert
- [.claude/knowledge_curator.md](.claude/knowledge_curator.md) - Knowledge graph expert
- [.claude/agent_orchestrator.md](.claude/agent_orchestrator.md) - Agent system expert
- [.claude/error_handling_specialist.md](.claude/error_handling_specialist.md) - Error pattern expert
- [.claude/type_hint_specialist.md](.claude/type_hint_specialist.md) - Type safety expert
- [.claude/legacy_refactor_specialist_v2.md](.claude/legacy_refactor_specialist_v2.md) - Migration expert

---

## ⚠️ Common Pitfalls to Avoid

1. **Registry Bypass** - Never call `agent.method()` directly, always use `runtime.exec_via_registry()`
2. **Ad-hoc File Loading** - Never use `json.load()` for knowledge files, always use `KnowledgeLoader`
3. **Bare Pass Statements** - Always replace with proper `logger.error()` or `logger.warning()`
4. **Pattern Direct Agent Calls** - Use `execute_through_registry` action, not `agent: "name"`
5. **Missing Capabilities** - Register agents with `AGENT_CAPABILITIES` metadata
6. **Graph Unsafe Access** - Use `get_node()` not `nodes[id]`, use `safe_query()` with defaults
7. **Dataset Without _meta** - All knowledge files need `_meta.version`, `_meta.last_updated`, `_meta.source`

---

## 🧪 Validation Commands

Run these before committing:

```bash
# Pattern validation
python scripts/lint_patterns.py

# Unit tests
pytest dawsos/tests/validation/test_trinity_smoke.py
pytest dawsos/tests/validation/test_integration.py
pytest dawsos/tests/validation/test_full_system.py

# Full suite
pytest dawsos/tests/validation/

# CI/CD (automatic on push)
# See .github/workflows/compliance-check.yml
```

---

## 🎓 Decision-Making Framework

When making ANY code change, ask:

1. **Does this follow Trinity flow?** → Check with Trinity Architect
2. **Does this need a pattern?** → Check with Pattern Specialist
3. **Does this touch the graph or datasets?** → Check with Knowledge Curator
4. **Does this involve agents or capabilities?** → Check with Agent Orchestrator
5. **Is this Trinity-compliant?** → Run validation suite

**Example Workflow**:
```
User: "Add a new moat analysis feature"

1. Read .claude/trinity_architect.md (execution flow)
2. Read .claude/pattern_specialist.md (pattern structure)
3. Read .claude/agent_orchestrator.md (which agent has moat capability)
4. Check AGENT_CAPABILITIES (can_analyze_moat → financial_analyst)
5. Create pattern using execute_through_registry action
6. Run linter + tests
7. Commit with Trinity compliance verified
```

---

## 🔄 Session Continuity

Each new Claude Code session should:

1. **Read this file** (CLAUDE.md) for context
2. **Reference specialist agents** in [.claude/](.claude/) before making changes
3. **Check current status** in [SYSTEM_STATUS.md](SYSTEM_STATUS.md)
4. **Follow Trinity principles** (UniversalExecutor → Pattern → Registry → Graph)
5. **Use capability-based routing** (Trinity 2.0 standard)
6. **Validate changes** with linter and tests

---

## 📞 Quick Reference

| Task | Specialist | Document |
|------|-----------|----------|
| Architecture review | Trinity Architect | [.claude/trinity_architect.md](.claude/trinity_architect.md) |
| Pattern creation | Pattern Specialist | [.claude/pattern_specialist.md](.claude/pattern_specialist.md) |
| Knowledge/graph work | Knowledge Curator | [.claude/knowledge_curator.md](.claude/knowledge_curator.md) |
| Agent development | Agent Orchestrator | [.claude/agent_orchestrator.md](.claude/agent_orchestrator.md) |
| Capability routing | Agent Orchestrator | [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) |
| Dataset maintenance | Knowledge Curator | [docs/KnowledgeMaintenance.md](docs/KnowledgeMaintenance.md) |
| Agent implementation | Agent Orchestrator | [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md) |

---

**Remember**: The specialist agents in [.claude/](.claude/) are your first stop for ANY architecture, pattern, knowledge, or agent changes. They contain deep, accurate knowledge of the Trinity 2.0 system and will ensure consistency across all development sessions.
