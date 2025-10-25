# DawsOS - Portfolio Intelligence Platform

**Current Version**: DawsOSP (Production)
**Architecture**: Trinity 3.0 Framework
**Repository**: [DawsOSB](https://github.com/mwd474747/DawsOSB)

---

## Quick Start

The production application is in the `DawsOSP/` directory:

```bash
cd DawsOSP

# Start backend (FastAPI + PostgreSQL)
./backend/run_api.sh

# Start frontend (Streamlit) - separate terminal
./frontend/run_ui.sh
```

Visit **http://localhost:8501** for the UI.

---

## Documentation

- **[DawsOSP/CLAUDE.md](DawsOSP/CLAUDE.md)** - Complete development guide
- **[DawsOSP/PRODUCT_SPEC.md](DawsOSP/PRODUCT_SPEC.md)** - Product specification
- **[DawsOSP/DEVELOPMENT_GUIDE.md](DawsOSP/DEVELOPMENT_GUIDE.md)** - Quick-start guide
- **[DawsOSP/TESTING_GUIDE.md](DawsOSP/TESTING_GUIDE.md)** - Testing documentation

---

## Repository Structure

```
/DawsOSB/
├── DawsOSP/          Production application (use this)
│   ├── backend/       FastAPI + PostgreSQL
│   ├── frontend/      Streamlit UI
│   ├── data/          Seed data
│   ├── scripts/       Utilities
│   └── tests/         Integration tests
│
└── archive/          Historical reference (Trinity 3.0, legacy code)
```

---

## What is DawsOS?

DawsOS is a **portfolio-first, explainable decision engine** that combines:

- **Dalio Macro** - Regime detection, factor analysis, scenario stress testing
- **Buffett Fundamentals** - Quality ratings, moat analysis, conservative metrics
- **Auditable Math** - Beancount ledger-of-record + immutable pricing packs for reproducibility

**Key Features**:
- Multi-currency portfolio analytics with accurate FX attribution
- Macro regime detection and cycle analysis (STDC, LTDC, Empire)
- Buffett quality ratings (dividend safety, moat strength, resilience)
- Portfolio optimization with policy constraints
- Rights-enforced exports and comprehensive observability

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
