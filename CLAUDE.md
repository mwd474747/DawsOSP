# DawsOS - AI Assistant Context

**Application Name**: DawsOS
**Architecture**: Trinity 3.0
**Version**: 1.0.0
**Status**: Development (60-70% complete - CORRECTED)
**Repository**: [DawsOSP](https://github.com/mwd474747/DawsOSP)
**Last Updated**: October 27, 2025

This file provides context for AI assistants (Claude) working on DawsOS.

---

## 🏷️ NAMING CONVENTION (CRITICAL)

> **DawsOS** is the APPLICATION (product name)
> **Trinity 3.0** is the ARCHITECTURE VERSION (execution framework)
> **DawsOSP** is the REPOSITORY (GitHub repo name)

**When to use what**:
- **User-facing** (UI, docs, marketing): "DawsOS" or "Trinity"
- **Technical docs**: "Trinity 3.0 architecture" or "DawsOS (Trinity 3.0)"
- **Code comments**: "Trinity 3.0 execution flow"
- **NEVER**: Mix "Trinity 3.0" and "DawsOS" as if they're different systems

**Key Understanding**:
> Trinity 3.0 is NOT a separate system - it's the execution framework FOR DawsOS.
> Like "React 18" is the framework version for a React app, "Trinity 3.0" is the framework version for DawsOS.

---

## CRITICAL: Read This First

**ALWAYS start every session by reading**:
1. **[.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md)** - SINGLE SOURCE OF TRUTH for all tasks, gaps, fixes
2. This file (CLAUDE.md) - Quick reference

**RULES**:
- NEVER create separate task lists
- ALWAYS update TASK_INVENTORY when discovering gaps
- ALWAYS verify claims against actual code
- NEVER reference non-existent directories

---

## Current State (Verified October 27, 2025)

### Application Structure

**Location**: ROOT directory (`./`)  
**Status**: 60-70% complete, development phase (CORRECTED)  
**Architecture**: FastAPI backend + Streamlit frontend

```
DawsOSP/
├── backend/                    ✅ FastAPI application
│   ├── app/                    ✅ Core application
│   │   ├── agents/             ✅ 9 agents (11 files: 9 agents + base + __init__)
│   │   ├── core/               ✅ Pattern orchestrator, agent runtime
│   │   ├── services/           ✅ 26 service files (mixed implementation status)
│   │   ├── api/                ✅ FastAPI routes
│   │   └── providers/          ✅ External API clients
│   ├── tests/                  ⚠️ 48 test files (pytest collection failed)
│   └── requirements.txt        ✅ All dependencies
├── frontend/                   ✅ Streamlit UI
├── data/                       ✅ Seed data
├── scripts/                    ✅ Utilities
└── .ops/                       ✅ Operations documentation
```

### Import Structure

**Status**: ✅ RESOLVED (October 27, 2025)
- **19 `__init__.py` files** - Proper Python package structure
- **0 files using `from app.X`** - All imports standardized
- **All imports use `from backend.app.X`** - Consistent pattern
- **Test suite functional** - 668 tests collected successfully

### Current Capabilities

**Agents**: 9 agents registered and functional
- `financial_analyst` - Portfolio data, pricing, metrics (18 capabilities)
- `macro_hound` - Macro regime detection, scenarios, DaR (14 capabilities)
- `data_harvester` - External provider integration (6 capabilities)
- `claude` - AI explanations and analysis (4 capabilities)
- `ratings` - Buffett quality ratings (4 capabilities)
- `optimizer` - Portfolio optimization (4 capabilities)
- `reports` - PDF exports and reporting (3 capabilities)
- `alerts` - Alert suggestions and threshold-based creation (2 capabilities) ✨ NEW
- `charts` - Visualization formatting and chart specifications (2 capabilities) ✨ NEW

**Total Capabilities**: 57 (verified via code inspection October 27, 2025)

**Patterns**: 12 production patterns operational
- `portfolio_overview` - Core portfolio analysis
- `buffett_checklist` - Quality ratings
- `policy_rebalance` - Optimization
- `portfolio_scenario_analysis` - Stress testing
- `holding_deep_dive` - Single security analysis
- `portfolio_macro_overview` - Macro + portfolio integration
- `macro_cycles_overview` - Regime classification
- `portfolio_cycle_risk` - Cycle risk exposure
- `cycle_deleveraging_scenarios` - Dalio deleveraging
- `news_impact_analysis` - News impact analysis
- `export_portfolio_report` - PDF export
- `macro_trend_monitor` - Trend monitoring

**Capabilities**: 53 total capabilities across 7 agents
- `financial_analyst` (18 capabilities)
- `macro_hound` (14 capabilities)
- `data_harvester` (6 capabilities)
- `claude` (4 capabilities)
- `ratings` (4 capabilities)
- `optimizer` (4 capabilities)
- `reports` (3 capabilities)

---

## Execution Flows

### Current (Pattern-Based)
```
UI → FastAPI Executor → Pattern Orchestrator → Agent Runtime → Agent → Service → Database
```
**Status**: ✅ Fully operational

### Data Flow
```
Pattern JSON → Agent Capabilities → Service Methods → Database Queries → Results
```
**Status**: ✅ Fully operational

---

## Development Workflow

### Environment Setup
```bash
# Clone repository
git clone https://github.com/mwd474747/DawsOSP.git
cd DawsOSP

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Set up database
export DATABASE_URL='postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos'

# Load seed data
python scripts/seed_loader.py --all

# Start development
./backend/run_api.sh
./frontend/run_ui.sh
```

### Testing
```bash
# Run test suite
pytest backend/tests/

# Run specific test categories
pytest backend/tests/unit/
pytest backend/tests/integration/
pytest backend/tests/e2e/
```

---

## Key Files Reference

### Critical Code
- **[backend/app/api/executor.py](backend/app/api/executor.py)** - FastAPI application entry point
- **[backend/app/core/pattern_orchestrator.py](backend/app/core/pattern_orchestrator.py)** - Pattern execution engine
- **[backend/app/core/agent_runtime.py](backend/app/core/agent_runtime.py)** - Agent capability routing
- **[backend/app/agents/base_agent.py](backend/app/agents/base_agent.py)** - Base agent class

### Documentation
- **[README.md](README.md)** - Quick start and overview
- **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Complete product specification
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development workflow
- **[.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md)** - Current backlog

### Configuration
- **[backend/requirements.txt](backend/requirements.txt)** - Python dependencies
- **[docker-compose.yml](docker-compose.yml)** - Full stack deployment
- **[.env.example](.env.example)** - Environment template

---

## Architecture Compliance

**ALWAYS** follow the pattern-based execution model:
- Patterns (JSON) define workflows
- Capabilities use dot notation (e.g., `ledger.positions`)
- Agent methods use underscore notation (e.g., `ledger_positions`)
- Base agent converts: `capability.replace(".", "_")` → method name
- NO direct service calls from UI
- NO bypassing pattern orchestrator

---

## Development Guidelines

### DO
- ✅ Verify ALL claims by reading actual code
- ✅ Use `get_capabilities()` to see what agents declare
- ✅ Check if service method exists before creating new one
- ✅ Follow naming: `capability.with.dots` → `method_with_underscores`
- ✅ Update TASK_INVENTORY when you find inaccuracies
- ✅ Run `python3 -m py_compile` before committing

### DON'T
- ❌ Trust documentation percentage estimates
- ❌ Assume features need building from scratch
- ❌ Create new services without checking existing ones
- ❌ Bypass pattern orchestration
- ❌ Reference non-existent directories
- ❌ Enable uvicorn `--reload` in production

---

## Quick Reference

**Ports**:
- Backend: http://localhost:8000
- Frontend: http://localhost:8501
- Database: postgresql://localhost:5432/dawsos

**Health Checks**:
```bash
curl http://localhost:8000/health
```

**Key Commands**:
```bash
# Start backend
./backend/run_api.sh

# Start frontend
./frontend/run_ui.sh

# Run tests
pytest backend/tests/

# Load seed data
python scripts/seed_loader.py --all
```

---

**Last Updated**: October 27, 2025
**Repository**: [DawsOSP](https://github.com/mwd474747/DawsOSP)
**Status**: Production-ready with clean import structure

---

## Component Inventory

**Agents**: 7 files, 2 registered  
**Core Modules**: 13 files  
**Patterns**: 16 JSON files (economy/6, smart/7, workflows/3)  
**Knowledge Datasets**: 27 JSON files  
**Services**: 8 files (OpenBBService uses yfinance)  
**Intelligence**: 3 files (EnhancedChatProcessor, entity extraction)  
**UI**: 7 component files

---

## Documentation (8 Files)

1. **MASTER_TASK_LIST.md** - All gaps/fixes/TODOs (READ THIS FIRST)
2. **README.md** - Project overview
3. **ARCHITECTURE.md** - System design
4. **CONFIGURATION.md** - API setup
5. **DEVELOPMENT.md** - Developer guide
6. **DEPLOYMENT.md** - Production deployment
7. **TROUBLESHOOTING.md** - Common issues
8. **CLAUDE.md** - This file

**Reference**:
- CAPABILITY_ROUTING_GUIDE.md - 103 capabilities
- PATTERN_AUTHORING_GUIDE.md - Pattern creation
- EXTENSION_GUIDE.md - System extensions

---

## Verification Commands

```bash
# Verify structure
ls -1 agents/*.py core/*.py patterns/*/*.json storage/knowledge/*.json | wc -l

# Verify API status
venv/bin/python -c "from config.api_config import APIConfig; print(APIConfig.get_status())"

# Verify market data
venv/bin/python -c "from services.openbb_service import OpenBBService; print(OpenBBService().get_equity_quote('SPY'))"

# Verify agent registration
grep "register_agent" main.py | wc -l  # Should be 2
```

---

## Development Rules

**DO**:
- Read MASTER_TASK_LIST.md at session start
- Update MASTER_TASK_LIST.md with discoveries
- Verify all claims against code
- Use UniversalExecutor → PatternEngine flow
- Use KnowledgeLoader for data (not direct file loads)

**DON'T**:
- Reference trinity3/ directory (doesn't exist)
- Reference dawsos/ directory (doesn't exist - except in archive)
- Create separate TODO lists
- Make claims without code verification
- Bypass architecture (use execution stack)

---

## Quick Reference

**Launch**: `./start.sh`  
**Port**: 8501  
**Python**: 3.11 (required)  
**Main File**: `main.py`  
**Task List**: MASTER_TASK_LIST.md  
**API Setup**: CONFIGURATION.md  
**Architecture**: ARCHITECTURE.md

---

**Last Verified**: October 21, 2025 20:00 UTC
