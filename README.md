# DawsOS - Portfolio Intelligence Platform

**Version**: 0.6 (60-65% Complete - Development Phase)
**Architecture**: Trinity 3.0 Framework
**Repository**: [DawsOSP](https://github.com/mwd474747/DawsOSP)

---

## Quick Start

```bash
# Clone the repository
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

# Start backend (FastAPI + PostgreSQL)
./backend/run_api.sh

# Start frontend (Streamlit) - separate terminal
./frontend/run_ui.sh
```

Visit **http://localhost:8501** for the UI.

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete development guide
- **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Product specification
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Quick-start guide
- **[.ops/TASK_INVENTORY_2025-10-28_CRITICAL_UPDATE.md](.ops/TASK_INVENTORY_2025-10-28_CRITICAL_UPDATE.md)** - Current backlog

---

## Repository Structure

```
DawsOSP/
├── backend/           FastAPI + PostgreSQL
├── frontend/          Streamlit UI
├── data/              Seed data
├── scripts/           Utilities
├── tests/             Integration tests
├── .ops/              Operations documentation
└── .claude/           Agent specifications
```

---

## What is DawsOS?

DawsOS is a **portfolio-first, explainable decision engine** that combines:

- **Dalio Macro** - Regime detection, factor analysis, scenario stress testing
- **Buffett Fundamentals** - Quality ratings, moat analysis, conservative metrics
- **Auditable Math** - Beancount ledger-of-record + immutable pricing packs for reproducibility

**Current Status** (60-65% Complete):
- ✅ **9 Agents** with 59 capabilities (DataHarvester, FinancialAnalyst, MacroHound, Claude, Ratings, Optimizer, Reports, Alerts, Charts)
- ✅ **12 Patterns** for portfolio analysis, macro regimes, scenarios, and exports
- ✅ **Core Infrastructure** - Database, API, pattern orchestration, agent runtime
- ⚠️ **Integration Gaps** - Some components not fully wired together
- ⚠️ **UI Prototype** - Next.js UI exists but not fully connected to backend
- ⚠️ **Testing** - Infrastructure exists but needs comprehensive test coverage

**Key Features**:
- Multi-currency portfolio analytics with accurate FX attribution
- Macro regime detection and cycle analysis (STDC, LTDC, Empire)
- Buffett quality ratings (dividend safety, moat strength, resilience)
- Portfolio optimization with policy constraints
- JWT authentication with role-based access control (RBAC)
- PDF export generation with WeasyPrint
- Rights-enforced exports and comprehensive observability
- Alert system with multiple delivery channels
- Chart formatting and visualization

---

## Architecture Notes

DawsOS uses the **Trinity 3.0 architecture** - a pattern-based execution framework:

```
UI → Executor API → Pattern Orchestrator → Agent Runtime → Services → Database
```

- **Patterns** (JSON) define workflows
- **Agents** provide atomic capabilities
- **Services** contain business logic
- **Every result** includes pricing_pack_id + ledger_commit_hash for reproducibility

See [DawsOSP/CLAUDE.md](DawsOSP/CLAUDE.md) for complete architecture documentation.

---

## Prerequisites

- Python 3.11+
- PostgreSQL with TimescaleDB
- Redis (optional, for caching)
- API Keys (FMP, Polygon, FRED, NewsAPI) - optional for seed data mode

---

## Development

```bash
cd DawsOSP/

# Set up environment
export DATABASE_URL='postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos'

# Load seed data
python scripts/seed_loader.py --all

# Run tests
pytest backend/tests/

# Start development
./backend/run_api.sh
./frontend/run_ui.sh
```

---

## Status

**Current State** (October 2025):
- ✅ Core execution stack operational
- ✅ Pricing pack + ledger reconciliation
- ✅ 12 production patterns
- ✅ 4 agents with 46 capabilities
- ✅ Streamlit UI functional
- 🚧 Macro scenarios, ratings, optimizer (in progress)

See [DawsOSP/.ops/TASK_INVENTORY_2025-10-24.md](DawsOSP/.ops/TASK_INVENTORY_2025-10-24.md) for detailed status.

---

## License

Proprietary - © 2025 DawsOS

---

**Last Updated**: October 25, 2025
**Maintainer**: Mike Dawson
