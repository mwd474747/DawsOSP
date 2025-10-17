# DawsOS Development Memory

**System Version**: 3.0 (Trinity Architecture)  
**Grade**: A+ (98-100/100)  
**Last Updated**: October 17, 2025  
**Status**: ✅ Production Ready

This file provides persistent context for all AI assistant sessions working on DawsOS.

---

## 🎯 Current System State (Oct 17, 2025)

### Architecture
- **Trinity Execution Flow**: Request → UniversalExecutor → PatternEngine → AgentRegistry → KnowledgeGraph
- **48 Patterns** (JSON-defined workflows in `dawsos/patterns/`)
- **15 Agents** with 103 capabilities (registered in `AGENT_CAPABILITIES`)
- **NetworkX Graph** (96K+ nodes, 10x performance vs legacy)
- **27 Datasets** via KnowledgeLoader (30-min cache)

### API Integration (Fixed Oct 11, 2025)
- ✅ **FRED API** - Economic data (GDP, CPI, unemployment)
- ✅ **FMP API** - Market data and fundamentals
- ✅ **Anthropic Claude** - AI analysis
- ✅ **NewsAPI** - Financial news
- **Critical Fix**: load_env.py no longer overwrites Replit secrets with empty .env values

### Known Issues (Active)
1. **LSP Warnings**: 29 diagnostics in `dawsos/ui/trinity_dashboard_tabs.py` (type hints)
2. **Hybrid Routing**: 88 pattern instances use `agent + capability` instead of pure `capability`
3. **Missing Templates**: 38 patterns lack response templates (users see raw JSON)
4. **Underutilized Functions**: Options analysis, portfolio risk, backtesting not exposed in patterns

### Past Issues (Resolved - See archive/legacy/)
- **Double Normalization** (Fixed Oct 10) - FredDataCapability → PatternEngine mismatch
- **Silent Failures** (Fixed Oct 10) - 75% → 0% via Pydantic validation
- **Economic Data System** (Fixed Oct 9) - 100% failure → operational

**Historical Documentation**: See [archive/legacy/INDEX.md](archive/legacy/INDEX.md) for session reports, fixes, and refactoring history.

---

## 🏛️ Critical Development Principles

### 1. ALWAYS Consult Specialist Agents

Before making architectural, pattern, knowledge, or agent changes:

- **🏛️ Trinity Architect** ([.claude/trinity_architect.md](.claude/trinity_architect.md)) - Architecture compliance, execution flow
- **🎯 Pattern Specialist** ([.claude/pattern_specialist.md](.claude/pattern_specialist.md)) - Pattern creation/debugging
- **📚 Knowledge Curator** ([.claude/knowledge_curator.md](.claude/knowledge_curator.md)) - Graph structure, 27 datasets
- **🤖 Agent Orchestrator** ([.claude/agent_orchestrator.md](.claude/agent_orchestrator.md)) - Agent development, capabilities

**Why**: These specialists contain deep system knowledge and ensure consistency across sessions.

### 2. Trinity Architecture Compliance (Non-Negotiable)

**Execution Flow** (EVERY request must follow):
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

# Capability-based routing (preferred)
result = runtime.execute_by_capability('can_analyze_text', context)

# Centralized knowledge loading
loader = get_knowledge_loader()
data = loader.get_dataset('sector_performance')
```

### 3. Capability-Based Routing (Trinity 2.0 Standard)

**ALWAYS prefer capability-based over name-based routing**:

```python
# Old way (works but not preferred)
result = runtime.exec_via_registry('financial_analyst', context)

# New way (Trinity 2.0 - more flexible)
result = runtime.execute_by_capability('can_calculate_dcf', context)
```

See [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) for all 103 capabilities.

---

## 📊 Key Components Reference

### Core Architecture
1. **UniversalExecutor** (`core/universal_executor.py`) - Single entry point
2. **PatternEngine** (`core/pattern_engine.py`) - 48 JSON patterns
3. **AgentRuntime** (`core/agent_runtime.py`) - Registry + capability routing
4. **AGENT_CAPABILITIES** (`core/agent_capabilities.py`) - 103 capabilities
5. **KnowledgeGraph** (`core/knowledge_graph.py`) - NetworkX backend (96K+ nodes)
6. **KnowledgeLoader** (`core/knowledge_loader.py`) - 27 datasets, 30-min TTL cache
7. **PersistenceManager** (`core/persistence.py`) - Auto-rotation, 30-day backups

### 27 Enriched Datasets
**Core (7)**: sector_performance, economic_cycles, sp500_companies, sector_correlations, relationships, ui_configurations, company_database

**Investment Frameworks (4)**: buffett_checklist, buffett_framework, dalio_cycles, dalio_framework

**Financial Data (4)**: financial_calculations, financial_formulas, earnings_surprises, dividend_buyback

**Factor/Alt Data (4)**: factor_smartbeta, insider_institutional, alt_data_signals, esg_governance

**Market Indicators (6)**: cross_asset_lead_lag, econ_regime_watchlist, fx_commodities, thematic_momentum, volatility_stress, yield_curve

**System Metadata (2)**: agent_capabilities, economic_calendar

### Financial Analyst Capabilities
The **financial_analyst** agent contains merged functionality from archived agents:

**Equity Analysis**: `analyze_stock_comprehensive()`, `compare_stocks()`  
**Macro Analysis**: `analyze_economy()` - regime detection (goldilocks/stagflation/recession)  
**Portfolio Risk**: `analyze_portfolio_risk()` - concentration, correlation, macro sensitivity  
**Options**: `analyze_options_greeks()`, `detect_unusual_options()`, `calculate_options_iv_rank()`

---

## 🚀 Common Development Tasks

### Launching the App
```bash
./start.sh  # Handles everything automatically
```

**Manual**:
```bash
python3 -m venv dawsos/venv  # If venv doesn't exist
dawsos/venv/bin/pip install -r requirements.txt
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501
```

**Important Rules**:
- NEVER use relative imports (use `from core.X` not `from ..core.X`)
- ALWAYS use `self.logger` in class methods (not bare `logger`)
- ALWAYS use `get_stats()`, `get_all_edges()` for graph access (not direct `.nodes`, `.edges`)

### Adding a New Pattern
1. **Read** [.claude/pattern_specialist.md](.claude/pattern_specialist.md)
2. Create JSON in `dawsos/patterns/<category>/`
3. Required fields: `id`, `name`, `description`, `version`, `triggers`, `steps`
4. Primary action: `execute_through_registry` (not direct agent calls)
5. Validate: `python scripts/lint_patterns.py`

### Adding a New Agent
1. **Read** [.claude/agent_orchestrator.md](.claude/agent_orchestrator.md)
2. **Read** [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md)
3. Implement standard methods: `process()`, `think()`, `analyze()`
4. Register capabilities from `AGENT_CAPABILITIES`
5. Test: `pytest dawsos/tests/validation/test_trinity_smoke.py`

### Modifying Knowledge Graph
1. **Read** [.claude/knowledge_curator.md](.claude/knowledge_curator.md)
2. **Read** [docs/KnowledgeMaintenance.md](docs/KnowledgeMaintenance.md)
3. Use safe methods: `get_node()`, `safe_query()` (never direct dict access)
4. Load data via KnowledgeLoader (30-min cache)
5. Include `_meta` header in dataset files

---

## ⚠️ Common Pitfalls to Avoid

1. **Registry Bypass** - Never call `agent.method()` directly, use `runtime.exec_via_registry()`
2. **Ad-hoc File Loading** - Never use `json.load()` for knowledge files, use `KnowledgeLoader`
3. **Pattern Direct Agent Calls** - Use `execute_through_registry` action
4. **Missing Capabilities** - Register agents with `AGENT_CAPABILITIES` metadata
5. **Graph Unsafe Access** - Use `get_node()` not `nodes[id]`, use `safe_query()` with defaults
6. **Dataset Without _meta** - All knowledge files need `_meta.version`, `_meta.last_updated`, `_meta.source`

---

## 📚 Essential Documentation

### Active Documentation (Project Root)
- [README.md](README.md) - Project overview & quickstart
- [SYSTEM_STATUS.md](SYSTEM_STATUS.md) - Current A+ grade status
- [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - 103 capabilities reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Active issue tracking

### Specialist Agents (.claude/)
- [.claude/trinity_architect.md](.claude/trinity_architect.md) - Architecture expert
- [.claude/pattern_specialist.md](.claude/pattern_specialist.md) - Pattern expert
- [.claude/knowledge_curator.md](.claude/knowledge_curator.md) - Knowledge graph expert
- [.claude/agent_orchestrator.md](.claude/agent_orchestrator.md) - Agent system expert

### Development Guides (docs/)
- [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md) - Agent implementation
- [docs/KnowledgeMaintenance.md](docs/KnowledgeMaintenance.md) - Dataset formats
- [docs/DisasterRecovery.md](docs/DisasterRecovery.md) - Backup/restore
- [docs/DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md) - Development environment setup
- [docs/ErrorHandlingGuide.md](docs/ErrorHandlingGuide.md) - Error handling patterns

### Historical Documentation (Archive)
- [archive/legacy/INDEX.md](archive/legacy/INDEX.md) - Master index of all historical docs
- [archive/legacy/sessions/](archive/legacy/sessions/) - Session reports & completion summaries
- [archive/legacy/fixes/](archive/legacy/fixes/) - Bug fixes & root cause analyses
- [archive/legacy/refactoring/](archive/legacy/refactoring/) - Architecture evolution & planning docs

---

## 🧪 Validation Commands

```bash
# Pattern validation
python scripts/lint_patterns.py

# Unit tests
pytest dawsos/tests/validation/test_trinity_smoke.py
pytest dawsos/tests/validation/test_integration.py

# Full suite
pytest dawsos/tests/validation/
```

---

## 🎓 Decision-Making Framework

When making ANY code change, ask:

1. **Does this follow Trinity flow?** → Check with [Trinity Architect](.claude/trinity_architect.md)
2. **Does this need a pattern?** → Check with [Pattern Specialist](.claude/pattern_specialist.md)
3. **Does this touch graph/datasets?** → Check with [Knowledge Curator](.claude/knowledge_curator.md)
4. **Does this involve agents/capabilities?** → Check with [Agent Orchestrator](.claude/agent_orchestrator.md)
5. **Is this Trinity-compliant?** → Run validation suite

**Example Workflow**:
```
User: "Add a new moat analysis feature"

1. Read .claude/trinity_architect.md (execution flow)
2. Read .claude/pattern_specialist.md (pattern structure)
3. Read .claude/agent_orchestrator.md (capability routing)
4. Check AGENT_CAPABILITIES (can_analyze_moat → financial_analyst)
5. Create pattern using execute_through_registry action
6. Run linter + tests
7. Commit with Trinity compliance verified
```

---

## 🔄 Session Continuity

Each new AI session should:

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
| Historical context | Master Index | [archive/legacy/INDEX.md](archive/legacy/INDEX.md) |

---

**Remember**: The specialist agents in [.claude/](.claude/) are your first stop for ANY architecture, pattern, knowledge, or agent changes. They contain deep, accurate knowledge of the Trinity 3.0 system and ensure consistency across all development sessions.
