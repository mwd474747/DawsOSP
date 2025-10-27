# DawsOS - AI Assistant Context

**Application Name**: DawsOS
**Architecture**: Trinity 3.0
**Version**: 1.0.0
**Status**: ≈75% complete (P0 remediation complete; remaining: P1 scenarios/optimizer, P2 charts/provider wiring)
**Last Updated**: October 26, 2025

This file provides context for AI assistants (Claude) working on DawsOS.

---

## 🚨 CRITICAL: READ THIS FIRST

### Current State (October 26, 2025 - Post P0 Remediation COMPLETE)

✅ **ALL P0 REMEDIATION COMPLETE** - Rating Rubrics + FMP Transformation (commits 5d24e04, 8fd4d9e, e5cf939, 26f636a, 72de052, fa8bcf8)

**Working today**
- AsyncPG pool initialises once and is reused across requests
- `python scripts/seed_loader.py --all` hydrates demo symbols, portfolio, pricing pack, macro cycles, **ratings rubrics**
- Executor `/v1/execute` executes seeded patterns (portfolio overview, holdings, **buffett_checklist with real FMP data**)
- Streamlit UI renders seeded valuations and attribution
- Observability hooks (trace IDs, pricing_pack_id, ledger_commit_hash) attached to responses
- **✅ NEW**: Ratings service loads research-based weights from `rating_rubrics` table (moat_strength, resilience, dividend_safety)
- **✅ NEW**: Data Harvester transforms real FMP fundamentals data (no more stub fundamentals when API key configured)

**Remediation Completed Across Two Sessions (2025-10-26)**
- ✅ **P0-CODE-1 (20h)**: Rating Rubrics Database Implementation
  - Created `rating_rubrics` schema with JSONB columns ([rating_rubrics.sql](backend/db/schema/rating_rubrics.sql))
  - Created 3 research-based seed files ([data/seeds/ratings/*.json](data/seeds/ratings/))
  - Extended seed_loader.py with RatingSeedLoader ([seed_loader.py:646-735](scripts/seed_loader.py#L646-L735))
  - Implemented database rubric loading in ratings.py ([ratings.py:57-165](backend/app/services/ratings.py#L57-L165))
  - **Removed hardcoded 25% weights** - now loads from database with fallback
  - All weights research-based and documented (Buffett investment philosophy)

- ✅ **Enhancement (30min)**: Weights Source Metadata (commit 72de052)
  - Added `_metadata.weights_source` field to rating results ("rubric" or "fallback")
  - Modified `_get_weights()` to return tuple: (weights, source)
  - Updated all 3 rating methods to track and expose weights source

- ✅ **P0-CODE-2 (14h)**: FMP Fundamentals Data Transformation (commit fa8bcf8)
  - Implemented `_transform_fmp_to_ratings_format()` method with 12 field mappings ([data_harvester.py:690-884](backend/app/agents/data_harvester.py#L690-L884))
  - Added 3 helper methods: `_calculate_5y_avg()`, `_calculate_std_dev()`, `_calculate_dividend_streak()` ([data_harvester.py:889-1025](backend/app/agents/data_harvester.py#L889-L1025))
  - Updated `fundamentals_load()` to use transformation instead of stubs ([data_harvester.py:610-644](backend/app/agents/data_harvester.py#L610-L644))
  - **Removed stub fundamentals shortcut** - now returns real FMP data with graceful fallback
  - 364 lines added, comprehensive error handling

- ✅ **P0-CODE-3 (3h)**: Database Init Script (commit 7f00f3e)
  - Updated [init_database.sh](backend/db/init_database.sh) to include rating_rubrics schema
  - Added schema validation for rating_rubrics table
  - All schemas applied in correct dependency order

**Governance Violations Eliminated**
- ✅ **Fixed**: Hardcoded 25% weights in moat_strength and resilience ratings
- ✅ **Fixed**: Stub fundamentals data when FMP API available
- ✅ **Fixed**: Missing rating_rubrics table initialization

**Comprehensive Remediation Plan**: [.ops/SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md](.ops/SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md)
- ~~**P0 (Critical)**: 3 items, 37 hours~~  → **✅ ALL P0 COMPLETE (37.5 hours)**
  - ✅ P0-CODE-1: Rating rubrics (20h) - COMPLETE
  - ✅ P0-CODE-2: FMP transformation (14h) - COMPLETE
  - ✅ P0-CODE-3: Schema init script (3h) - COMPLETE
  - ✅ Enhancement: Weights source metadata (30min) - COMPLETE
- **P1 (High)**: 4 items, 88 hours → **✅ 75% COMPLETE (48 of 88 hours)** - Session 2025-10-26
  - ✅ P1-CODE-1: macro.run_scenario (12h) - COMPLETE (commit 2876d86)
  - ✅ P1-CODE-2: macro.compute_dar (16h) - COMPLETE (commit bc6a7ee)
  - ⏳ P1-CODE-3: optimizer.propose_trades (40h) - NOT STARTED (requires new service)
  - ✅ P1-CODE-4: Provider transformations (20h) - COMPLETE (commit 5e28827)
- **P2 (Medium)**: 8 items, 60 hours - Chart placeholders, holding details
- **Total**: 125 hours remaining (85.5h completed) over 5-6 weeks with 2-3 engineers
- **Affected Patterns**: ~~buffett_checklist (FIXED)~~, ~~portfolio_scenario_analysis (FIXED)~~, ~~portfolio_cycle_risk (FIXED)~~, policy_rebalance

**P1 Work Completed (Session 2025-10-26)**:
- ✅ **Macro Scenarios** (12h): 22 Dalio-based scenarios (debt crisis, empire cycles, standard stress tests)
- ✅ **Drawdown-at-Risk** (16h): Regime-conditional DaR with scenario distribution analysis
- ✅ **Provider Transformations** (20h): Polygon prices, FRED macro, NewsAPI articles

**Still outstanding (see remediation plan for details)**:
- ⏳ **P1 Remaining**: Optimizer integration (40h) - Requires Riskfolio-Lib integration
- ⚠️  **P2 (Medium Priority)**: Chart placeholders + holding deep dive (60h)
- ℹ️  **P3 (Low Priority)**: 39 minor TODOs (cosmetic improvements, optimizations, 72h)

**Production Status**: ⚠️ **Phase 2.75 - Advanced Macro Features Ready** - All P0 blockers eliminated, 75% of P1 complete. Patterns now functional: buffett_checklist (real FMP data), portfolio_scenario_analysis (22 stress tests), portfolio_cycle_risk (regime-conditional DaR), macro_trend_monitor (real FRED data). See [SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md](.ops/SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md) for remaining work.

Use the sections below for navigation; update remediation plan as work progresses.

## Current Capability Summary (Verified 2025-10-26)

- **financial_analyst**: 7 capabilities implemented (`ledger.positions`, `pricing.apply_pack`, `metrics.*`, `attribution.currency`, `charts.overview`) pulling live data from seeded tables.
- **macro_hound**: ✅ **ALL 5 CAPABILITIES FULLY WIRED** (Session 2025-10-26)
  - `macro.detect_regime` - Real regime detection (5 regimes: Early Expansion → Late Contraction)
  - `macro.compute_cycles` - Aggregate cycle analysis (Dalio framework)
  - `macro.get_indicators` - Real FRED economic indicators
  - `macro.run_scenario` - ✅ **NEW**: 22 stress test scenarios (Dalio debt crisis + empire cycles + standard tests)
  - `macro.compute_dar` - ✅ **NEW**: Regime-conditional Drawdown-at-Risk calculation
- **data_harvester**: ✅ **ALL 6 CAPABILITIES FULLY WIRED** (Session 2025-10-26)
  - `provider.fetch_quote` - ✅ **NEW**: Real Polygon price quotes (OHLC transformations)
  - `provider.fetch_fundamentals` - ✅ Real FMP fundamentals (P0-CODE-2)
  - `provider.fetch_news` - ✅ **NEW**: Real NewsAPI articles with relevance scoring
  - `provider.fetch_macro` - ✅ **NEW**: Real FRED macro indicators (T10Y2Y, FEDFUNDS, etc.)
  - `provider.fetch_ratios` - ✅ Real FMP financial ratios
  - `fundamentals.load` - ✅ Real FMP transformation pipeline (12 rating fields)
- **claude_agent**: All three capabilities (`claude.explain`, `claude.summarize`, `claude.analyze`) return placeholder text until Anthropic API wiring is completed.

## Historical Audit Notes (Archived)

> Sections below were produced during earlier audits (pool/syntax issues) and are retained for reference only. Consult the summary above and `.ops/TASK_INVENTORY_2025-10-24.md` for authoritative status.
- *Historical status snapshot from 2025-10-22 follows; verify against code before relying on it.*
- ✅ `data/seeds/portfolios/portfolios.csv` - Test portfolio `11111111-1111-1111-1111-111111111111`
- ✅ `data/seeds/portfolios/lots.csv` - AAPL (300 shares), RY (400 shares), XIU (1000 shares)
- ✅ `data/seeds/portfolios/transactions.csv` - Buy transactions

**Fix**: Run `python scripts/seed_loader.py --domain portfolios`

**Timeline**: 30 minutes (includes verification)

#### P1: Missing Capabilities (25 of 45)

**Implemented** (20 capabilities across 4 agents):
- Financial Analyst (7): `ledger.positions`, `pricing.apply_pack`, `metrics.compute_twr`, `metrics.compute_sharpe`, `attribution.currency`, `charts.overview`, `metrics.compute`
- Macro Hound (5): `macro.detect_regime`, `macro.compute_cycles`, `macro.get_indicators`, `macro.run_scenario`, `macro.compute_dar`
- Data Harvester (5): `provider.fetch_quote`, `provider.fetch_fundamentals`, `provider.fetch_news`, `provider.fetch_macro`, `provider.fetch_ratios`
- Claude Agent (3): `claude.explain`, `claude.summarize`, `claude.analyze`

**Missing** (25 capabilities - some may need new services, some are wrappers):
- **Ratings** (4): `ratings.dividend_safety`, `ratings.moat_strength`, `ratings.resilience`, `ratings.aggregate`
  - **Blocker**: Service file `ratings.py` doesn't exist
- **Optimizer** (4): `optimizer.propose_trades`, `optimizer.analyze_impact`, `optimizer.suggest_hedges`, `optimizer.suggest_deleveraging_hedges`
  - **Blocker**: Service file `optimizer.py` doesn't exist
- **Holding Analysis** (5): `get_position_details`, `compute_position_return`, `compute_portfolio_contribution`, `compute_position_currency_attribution`, `compute_position_risk`
  - **May exist as services**, needs agent wiring
- **Cycles** (4): `cycles.compute_empire`, `cycles.compute_long_term`, `cycles.compute_short_term`, `cycles.aggregate_overview`
  - **Service exists**, needs agent methods
- **Other** (8): risk, alerts, reports, news capabilities
  - **Services exist**, needs agent methods or minor service additions

#### P2: Minor Issues

1. **Pattern file**: [holding_deep_dive.json](backend/patterns/holding_deep_dive.json) uses `pattern_id` instead of `id`
2. **Documentation**: Several .md files contain outdated information

---

## 📚 Essential Reading Order

1. **THIS FILE** ⭐ **START HERE** – Current system snapshot and quick reference
2. **[.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md)** – Canonical backlog and task ownership
3. **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** – Full product vision and guardrails
4. **[INDEX.md](INDEX.md)** – Complete documentation index
5. **[backend/LEDGER_RECONCILIATION.md](backend/LEDGER_RECONCILIATION.md)** – Ledger operations guide
6. **[backend/PRICING_PACK_GUIDE.md](backend/PRICING_PACK_GUIDE.md)** – Pricing pack operations

**Note**: Documentation was streamlined on 2025-10-26. Developer guides, architect files, and pattern mappings are being restored from the parent repository.

---

## 🚫 CRITICAL RULES FOR AI ASSISTANTS

### How to Assess Completion State

**ALWAYS verify claims by reading actual code, NOT documentation**:

1. **Check agent capabilities**: Read `get_capabilities()` in agent files
2. **Count LOC**: Use `wc -l` or Python scripts, not documentation estimates
3. **Check database**: Query actual tables, don't trust "should have" claims
4. **Verify syntax**: Run `python3 -m py_compile` on Python files
5. **Check seed data**: Look in `data/seeds/` directory for CSV files

**Example Commands**:
```bash
# Check what capabilities are actually declared
grep -A 10 "def get_capabilities" backend/app/agents/*.py

# Count real LOC
find backend -name "*.py" | xargs wc -l

# Check database state
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c "SELECT COUNT(*) FROM portfolios"

# Verify Python syntax
python3 -m py_compile backend/app/agents/financial_analyst.py
```

### Documentation Management
**NEVER** create new .md files unless explicitly requested.

**ALWAYS**:
- Update existing documentation when you discover inaccuracies
- Verify claims against code before updating docs
- Use `.claude/agents/*.md` for agent-specific documentation
- Use `DEVELOPMENT_GUIDE.md` for user-facing guides
- Use `.ops/TASK_INVENTORY_2025-10-24.md` for task planning (consolidated from all sources)

**Task Sources** (see [.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md) for canonical backlog):
1. **.ops/TASK_INVENTORY_2025-10-24.md** – Source of truth for scope, ownership, and sequencing
2. **Inline code TODOs** (48 found) – Minor improvements to triage into the inventory when needed
3. **CLAUDE.md** (this file) – Current status snapshot for assistants; keep aligned with the inventory
4. **Legacy planning docs** (`.claude/`) – Historical reference only; do not add new tasks there

### Architecture Compliance
**ALWAYS** follow the pattern-based execution model:
- Patterns (JSON) define workflows
- Capabilities use dot notation (e.g., `ledger.positions`)
- Agent methods use underscore notation (e.g., `ledger_positions`)
- Base agent converts: `capability.replace(".", "_")` → method name
- NO direct service calls from UI
- NO bypassing pattern orchestrator

### Development Workflow
**BEFORE** implementing new features:
1. Fix P0 blockers (syntax errors, missing data)
2. Check if service method exists (may just need agent wiring)
3. Check if pattern JSON exists
4. Verify agent declares the capability in `get_capabilities()`

---

## 🏷️ NAMING CONVENTION (CRITICAL)

> **DawsOS** is the APPLICATION (product name)
> **Trinity 3.0** is the ARCHITECTURE VERSION (execution framework)
> **DawsOSB** is the REPOSITORY (GitHub repo name)

**When to use what**:
- **User-facing**: "DawsOS" or "Trinity"
- **Technical docs**: "Trinity 3.0 architecture" or "DawsOS (Trinity 3.0)"
- **Code comments**: "Trinity 3.0 execution flow"
- **NEVER**: Mix "Trinity 3.0" and "DawsOS" as if they're different systems

---

## 📊 Implementation Status Summary (Verified)

### What EXISTS and WORKS (After Syntax Fix)

| Component | Files | LOC | Status | Notes |
|-----------|-------|-----|--------|-------|
| **Services** | 20 | 8,581 | 95% | All major services implemented |
| **Jobs** | 13 | 5,194 | 90% | Metrics, pack building, reconciliation |
| **Patterns** | 12 | - | 100% | All JSON definitions complete |
| **Agents** | 4 | 1,902 | 45% | 20/45 capabilities declared |
| **Database Schema** | - | - | 95% | 25 tables, RLS, hypertables |
| **Provider Integration** | 4 | 1,118 | 90% | FMP, Polygon, FRED |

### What NEEDS Implementation

| Feature | Priority | Effort | Status |
|---------|----------|--------|--------|
| **Syntax Error Fix** | P0 | 10 min | Ready to fix |
| **Load Seed Data** | P0 | 30 min | Seed files exist |
| **Ratings Service** | P1 | 2 days | File doesn't exist |
| **Optimizer Service** | P1 | 2 days | File doesn't exist |
| **Agent Wiring** | P1 | 1-2 days | Wire 15 capabilities to existing services |
| **New Service Methods** | P2 | 3-5 days | Add 10 missing methods to existing services |

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.11+
- PostgreSQL running (Docker)
- Database: `dawsos` user: `dawsos_app` password: `dawsos_app_pass`

### Steps

```bash
# 1. Fix syntax error (REQUIRED)
# Edit backend/app/agents/financial_analyst.py
# Delete lines 309-361
# Add "return result" after line 307

# 2. Set environment
export DATABASE_URL='postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos'

# 3. Load seed data
python scripts/seed_loader.py --domain portfolios

# 4. Start backend
cd backend && ./run_api.sh

# 5. Start frontend (separate terminal)
cd frontend && ./run_ui.sh

# 6. Open http://localhost:8501
```

---

## 📁 Application Structure

```
DawsOSP/
├── backend/
│   ├── app/
│   │   ├── agents/          # 4 agents, 20 capabilities
│   │   ├── api/             # FastAPI executor + 5 route modules
│   │   ├── core/            # Pattern orchestrator, agent runtime
│   │   ├── db/              # Connection pool (Redis coordinator), queries
│   │   ├── providers/       # FMP, Polygon, FRED clients
│   │   └── services/        # 20 services (ratings.py, optimizer.py missing)
│   ├── jobs/                # 13 jobs (metrics, pack, reconcile, etc.)
│   ├── patterns/            # 12 JSON pattern definitions
│   └── db/
│       ├── schema/          # SQL schema files
│       └── migrations/      # Migration files
├── frontend/
│   └── ui/
│       └── screens/         # 5 Streamlit screens
├── data/
│   └── seeds/               # ⭐ CSV seed data (NOT loaded yet)
│       └── portfolios/      # portfolios.csv, lots.csv, transactions.csv
└── scripts/                 # seed_loader.py, utilities
```

---

## 🔑 Key Architectural Patterns

### 1. Single Execution Path (SACRED)
```
UI → Executor API → Pattern Orchestrator → Agent Runtime → Agent → Service → Database
```

### 2. Pattern-Based Execution

Example pattern (`portfolio_overview.json`):

```json
{
  "id": "portfolio_overview",
  "steps": [
    {"capability": "ledger.positions", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}, "as": "positions"},
    {"capability": "pricing.apply_pack", "args": {"positions": "{{positions}}"}, "as": "valued_positions"},
    {"capability": "metrics.compute_twr", "args": {"portfolio_id": "{{inputs.portfolio_id}}"}, "as": "metrics"}
  ],
  "outputs": ["positions", "valued_positions", "metrics"]
}
```

### 3. Capability Routing

**How it works**:
1. Pattern references capability: `"ledger.positions"`
2. Agent declares in `get_capabilities()`: `["ledger.positions"]`
3. Agent runtime maps to agent: `"financial_analyst"`
4. Base agent converts to method: `capability.replace(".", "_")` → `"ledger_positions"`
5. Agent executes: `await agent.ledger_positions(ctx, state, **kwargs)`

### 4. Database Pool Management (ALREADY SOLVED)

**Current Implementation**:
```python
# backend/app/db/connection.py has RedisPoolCoordinator
# - Redis stores pool config (fallback: works without Redis)
# - Each module creates its own pool from shared config
# - Auto-reload disabled in run_api.sh
```

**Status**: ✅ WORKING (not a blocker)

### 5. Reproducibility Contract

Every result includes:
```json
{
  "result": {...},
  "_metadata": {
    "pricing_pack_id": "PP_2025-10-21",
    "ledger_commit_hash": "abc123",
    "asof_date": "2025-10-21"
  }
}
```

---

## 🐛 Known Issues & Fixes

### P0 (CRITICAL - Prevents Startup)

**1. Syntax Error in financial_analyst.py**
- **Lines**: 309-361
- **Issue**: Orphaned code block with unmatched `else:`
- **Fix**: Delete lines 309-361, add `return result` after line 307
- **Timeline**: 10 minutes

### P0 (CRITICAL - Cannot Test)

**2. Empty Database**
- **Issue**: 0 portfolios, 0 lots, 0 transactions
- **Root Cause**: Seed data exists but not loaded
- **Fix**: `python scripts/seed_loader.py --domain portfolios`
- **Timeline**: 30 minutes

### P1 (HIGH - Feature Gaps)

**3. Missing Service Files**
- **ratings.py**: Needed for `buffett_checklist` pattern (4 capabilities)
- **optimizer.py**: Needed for `policy_rebalance` pattern (4 capabilities)
- **Timeline**: 2 days per service

**4. Missing Agent Wiring**
- 15 capabilities have service methods but no agent declarations
- Examples: holding analysis (5), cycles detail (4), risk factors (3)
- **Timeline**: 1-2 days

### P2 (MINOR)

**5. Pattern ID Mismatch**
- **File**: `holding_deep_dive.json`
- **Issue**: Uses `pattern_id` instead of `id`
- **Fix**: Rename field
- **Timeline**: 5 minutes

---

## 🧪 Testing Protocol

### Level 1: Backend Startup (After Syntax Fix)

```bash
cd backend && ./run_api.sh
```

**Expected**:
```
✅ Database connection pool initialized
✅ Agent runtime initialized with 4 agents
✅ Pattern orchestrator initialized
✅ Loaded 12 patterns
✅ Uvicorn running on http://0.0.0.0:8000
```

### Level 2: Pattern Execution (After Seed Data Load)

```bash
curl -X POST "http://localhost:8000/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_overview",
    "inputs": {
      "portfolio_id": "11111111-1111-1111-1111-111111111111",
      "lookback_days": 252
    }
  }'
```

**Expected**: Real data for AAPL, RY, XIU positions

### Level 3: Frontend Integration

```bash
cd frontend && ./run_ui.sh
# Open http://localhost:8501
```

**Expected**: Portfolio Overview displays positions with metrics

---

## 📝 Development Guidelines

### DO
- ✅ Verify ALL claims by reading actual code
- ✅ Use `get_capabilities()` to see what agents declare
- ✅ Check if service method exists before creating new one
- ✅ Follow naming: `capability.with.dots` → `method_with_underscores`
- ✅ Update CLAUDE.md when you find inaccuracies
- ✅ Run `python3 -m py_compile` before committing

### DON'T
- ❌ Trust documentation percentage estimates
- ❌ Assume features need building from scratch
- ❌ Create new services without checking existing ones
- ❌ Bypass pattern orchestration
- ❌ Reference non-existent directories (trinity3/, dawsos/)
- ❌ Enable uvicorn `--reload` in production

---

## 🤖 Agent Orchestration Guide for AI Assistants

### Understanding the Agent Architecture

DawsOS uses a **multi-agent capability system** where specialized agents provide atomic operations (capabilities) that patterns orchestrate into complex workflows.

#### The 4 Current Agents

**1. Financial Analyst** ([backend/app/agents/financial_analyst.py](backend/app/agents/financial_analyst.py))
- **Purpose**: Portfolio data, pricing, metrics, attribution
- **Capabilities** (7):
  - `ledger.positions` - Fetch portfolio positions from lots table
  - `pricing.apply_pack` - Value positions using pricing pack
  - `metrics.compute` - Generic metrics wrapper
  - `metrics.compute_twr` - Time-weighted return calculation
  - `metrics.compute_sharpe` - Sharpe ratio calculation
  - `attribution.currency` - Multi-currency attribution
  - `charts.overview` - Portfolio overview charts
- **Services Used**: LedgerService, PricingService, MetricsQueries
- **LOC**: ~800 lines
- **Status**: ✅ WORKS (after syntax fix)

**2. Macro Hound** ([backend/app/agents/macro_hound.py](backend/app/agents/macro_hound.py))
- **Purpose**: Macro regime detection, cycle analysis, scenario analysis
- **Capabilities** (5):
  - `macro.detect_regime` - Classify current macro environment (5 regimes)
  - `macro.compute_cycles` - Aggregate cycle analysis
  - `macro.get_indicators` - Economic indicators (GDP, inflation, rates)
  - `macro.run_scenario` - Portfolio scenario stress testing
  - `macro.compute_dar` - Drawdown at Risk calculations
- **Services Used**: MacroService, CyclesService, ScenariosService
- **LOC**: ~600 lines
- **Status**: ✅ WORKS

**3. Data Harvester** ([backend/app/agents/data_harvester.py](backend/app/agents/data_harvester.py))
- **Purpose**: External data provider integration
- **Capabilities** (5):
  - `provider.fetch_quote` - Real-time equity quotes
  - `provider.fetch_fundamentals` - Company fundamentals (FMP)
  - `provider.fetch_news` - News articles (NewsAPI)
  - `provider.fetch_macro` - Economic data (FRED)
  - `provider.fetch_ratios` - Financial ratios (FMP)
- **Providers**: FMP, Polygon, FRED clients
- **LOC**: ~400 lines
- **Status**: ✅ WORKS (graceful fallback to stubs if no API keys)

**4. Claude Agent** ([backend/app/agents/claude_agent.py](backend/app/agents/claude_agent.py))
- **Purpose**: AI-powered explanations and analysis
- **Capabilities** (3):
  - `claude.explain` - Explain metrics, ratings, decisions
  - `claude.summarize` - Summarize portfolio analysis
  - `claude.analyze` - Deep dive AI analysis
- **API**: Anthropic Claude API
- **LOC**: ~100 lines
- **Status**: ✅ WORKS (graceful fallback if no API key)

### How to Add a New Capability

**Example**: Add `risk.compute_var` capability to calculate Value at Risk

#### Step 1: Check if Service Method Exists

```bash
# Search for existing VaR implementation
grep -r "value_at_risk\|compute_var" backend/app/services/risk.py
```

If method exists, skip to Step 3. If not, implement in service first.

#### Step 2: Implement Service Method (if needed)

```python
# backend/app/services/risk.py

async def compute_var(
    portfolio_id: UUID,
    confidence: float = 0.95,
    horizon_days: int = 1
) -> Dict[str, Any]:
    """
    Compute Value at Risk for portfolio.

    Returns:
        Dict with var_amount, var_pct, confidence, horizon
    """
    # Implementation here
    return {
        "var_amount": Decimal("1000.00"),
        "var_pct": Decimal("0.02"),
        "confidence": confidence,
        "horizon_days": horizon_days
    }
```

#### Step 3: Decide Which Agent Should Own It

**Decision Tree**:
- Portfolio/position data → **Financial Analyst**
- Macro/regime/cycle → **Macro Hound**
- External providers → **Data Harvester**
- AI explanations → **Claude Agent**
- Risk analysis → **Financial Analyst** (most common) or create new **Risk Agent**

For VaR, we'll add to Financial Analyst.

#### Step 4: Add to Agent's Capabilities

```python
# backend/app/agents/financial_analyst.py

def get_capabilities(self) -> List[str]:
    """Return list of capabilities."""
    return [
        "ledger.positions",
        "pricing.apply_pack",
        "metrics.compute_twr",
        "metrics.compute_sharpe",
        "attribution.currency",
        "charts.overview",
        "risk.compute_var",  # ← ADD THIS
    ]
```

#### Step 5: Implement Agent Method

```python
# backend/app/agents/financial_analyst.py

async def risk_compute_var(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    confidence: float = 0.95,
    horizon_days: int = 1,
) -> Dict[str, Any]:
    """
    Compute Value at Risk.

    Capability: risk.compute_var
    """
    portfolio_id_uuid = UUID(portfolio_id) if portfolio_id else ctx.portfolio_id

    logger.info(f"risk.compute_var: portfolio_id={portfolio_id_uuid}")

    # Call service
    from backend.app.services.risk import get_risk_service
    risk_service = get_risk_service()

    result = await risk_service.compute_var(
        portfolio_id_uuid,
        confidence,
        horizon_days
    )

    # Attach metadata
    metadata = self._create_metadata(
        source=f"risk_service:{ctx.pricing_pack_id}",
        asof=ctx.asof_date,
        ttl=300
    )

    return self._attach_metadata(result, metadata)
```

**Key Points**:
- Method name: `risk_compute_var` (dots → underscores)
- Signature: `async def method(self, ctx, state, **kwargs)`
- Metadata: Always attach for traceability
- Logging: Log capability execution

#### Step 6: Add to Pattern

```json
// backend/patterns/portfolio_risk_analysis.json
{
  "id": "portfolio_risk_analysis",
  "steps": [
    {
      "capability": "risk.compute_var",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "confidence": 0.95,
        "horizon_days": 1
      },
      "as": "var_1d"
    }
  ],
  "outputs": ["var_1d"]
}
```

#### Step 7: Test

```bash
# Test agent capability directly
python3 -c "
from backend.app.agents.financial_analyst import FinancialAnalyst
agent = FinancialAnalyst('test', {})
print(agent.get_capabilities())
" | grep risk.compute_var

# Test pattern execution
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_risk_analysis",
    "inputs": {"portfolio_id": "11111111-1111-1111-1111-111111111111"}
  }'
```

### How to Create a New Agent

**Example**: Create a **Risk Agent** to consolidate risk capabilities

#### Step 1: Create Agent File

```python
# backend/app/agents/risk_agent.py
"""
Risk Agent - Portfolio risk analysis and stress testing

Capabilities:
    - risk.compute_var: Value at Risk calculation
    - risk.compute_cvar: Conditional VaR
    - risk.compute_factor_exposures: Factor exposure analysis
    - risk.stress_test: Scenario stress testing
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import date

from backend.app.agents.base_agent import BaseAgent
from backend.app.core.types import RequestCtx
from backend.app.services.risk import get_risk_service
from backend.app.services.factor_analysis import get_factor_service

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Agent for portfolio risk analysis."""

    def get_capabilities(self) -> List[str]:
        """Return list of risk capabilities."""
        return [
            "risk.compute_var",
            "risk.compute_cvar",
            "risk.compute_factor_exposures",
            "risk.stress_test",
        ]

    async def risk_compute_var(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        portfolio_id: Optional[str] = None,
        confidence: float = 0.95,
        horizon_days: int = 1,
    ) -> Dict[str, Any]:
        """Compute Value at Risk."""
        # Implementation here
        pass

    async def risk_compute_cvar(self, ctx, state, **kwargs) -> Dict[str, Any]:
        """Compute Conditional VaR."""
        pass

    async def risk_compute_factor_exposures(self, ctx, state, **kwargs) -> Dict[str, Any]:
        """Compute factor exposures."""
        pass

    async def risk_stress_test(self, ctx, state, **kwargs) -> Dict[str, Any]:
        """Run stress test scenarios."""
        pass
```

#### Step 2: Register Agent in Runtime

```python
# backend/app/api/executor.py

def get_agent_runtime(reinit_services: bool = False) -> AgentRuntime:
    """Get or create singleton agent runtime."""
    global _agent_runtime

    if _agent_runtime is None:
        services = {"db": db_pool, "redis": None}
        _agent_runtime = AgentRuntime(services)

        # Register agents
        financial_analyst = FinancialAnalyst("financial_analyst", services)
        _agent_runtime.register_agent(financial_analyst)

        macro_hound = MacroHound("macro_hound", services)
        _agent_runtime.register_agent(macro_hound)

        data_harvester = DataHarvester("data_harvester", services)
        _agent_runtime.register_agent(data_harvester)

        claude_agent = ClaudeAgent("claude", services)
        _agent_runtime.register_agent(claude_agent)

        # ADD NEW AGENT HERE
        risk_agent = RiskAgent("risk_agent", services)
        _agent_runtime.register_agent(risk_agent)

        logger.info("Agent runtime initialized with 5 agents")

    return _agent_runtime
```

#### Step 3: Move Capabilities from Other Agents

If risk capabilities were previously in Financial Analyst:
1. Remove from Financial Analyst's `get_capabilities()`
2. Remove methods from financial_analyst.py
3. Add to Risk Agent's `get_capabilities()`
4. Implement methods in risk_agent.py

Patterns will automatically route to the new agent (no pattern changes needed).

### Agent Best Practices

#### 1. **Single Responsibility Principle**
Each agent should have a clear domain:
- ❌ BAD: Financial Analyst handles risk, metrics, pricing, macro
- ✅ GOOD: Financial Analyst handles portfolio data; Risk Agent handles risk; Macro Hound handles macro

#### 2. **Thin Agent, Fat Service**
Agents should orchestrate, not implement business logic:
```python
# ❌ BAD - Business logic in agent
async def metrics_compute_twr(self, ctx, state, **kwargs):
    # 200 lines of TWR calculation here...
    pass

# ✅ GOOD - Agent calls service
async def metrics_compute_twr(self, ctx, state, **kwargs):
    service = get_metrics_service()
    result = await service.compute_twr(portfolio_id, asof_date)
    return self._attach_metadata(result, metadata)
```

#### 3. **Always Attach Metadata**
Every capability result needs traceability:
```python
metadata = self._create_metadata(
    source=f"service_name:{ctx.pricing_pack_id}",
    asof=ctx.asof_date,
    ttl=300  # Cache for 5 minutes
)
return self._attach_metadata(result, metadata)
```

#### 4. **Use RequestCtx for Reproducibility**
Never use `datetime.now()` or random values:
```python
# ❌ BAD - Not reproducible
asof = datetime.now()

# ✅ GOOD - Use context
asof = ctx.asof_date or datetime.now()
```

#### 5. **Graceful Degradation**
Handle missing services/data gracefully:
```python
try:
    result = await service.compute_var(portfolio_id)
except Exception as e:
    logger.error(f"VaR computation failed: {e}")
    result = {
        "error": "VaR computation unavailable",
        "var_amount": None,
        "var_pct": None
    }
return self._attach_metadata(result, metadata)
```

### Debugging Agent Issues

#### Problem: "No agent registered for capability X"

**Check**:
1. Is capability declared in `get_capabilities()`?
2. Is agent registered in executor.py?
3. Is method name correct? (`capability.replace(".", "_")`)

```bash
# Verify capability declaration
grep -A 15 "def get_capabilities" backend/app/agents/*.py | grep "your.capability"

# Verify agent registration
grep "register_agent" backend/app/api/executor.py

# Verify method exists
grep "async def your_capability" backend/app/agents/*.py
```

#### Problem: "Capability execution fails"

**Check**:
1. Does service method exist and work?
2. Is database pool accessible?
3. Are method arguments correct?

```bash
# Test service directly
python3 -c "
from backend.app.services.your_service import get_service
import asyncio
service = get_service()
result = asyncio.run(service.your_method(args))
print(result)
"
```

#### Problem: "Pattern references wrong capability name"

**Check**: Pattern JSON uses dots, agent method uses underscores
```json
// Pattern uses: "capability": "risk.compute_var"
// Agent method:  async def risk_compute_var(...)
```

### Agent Development Checklist

When adding a new capability:
- [ ] Service method implemented and tested
- [ ] Capability added to agent's `get_capabilities()`
- [ ] Agent method implemented (name matches: dots → underscores)
- [ ] Method attaches metadata
- [ ] Pattern JSON references capability (if needed)
- [ ] Agent registered in executor.py
- [ ] Python syntax verified: `python3 -m py_compile agent_file.py`
- [ ] End-to-end test via pattern execution

### Future Agent Ideas

Based on missing capabilities, consider creating:

**5. Ratings Agent** (Priority: P1)
- `ratings.dividend_safety`
- `ratings.moat_strength`
- `ratings.resilience`
- `ratings.aggregate`

**6. Optimizer Agent** (Priority: P1)
- `optimizer.propose_trades`
- `optimizer.analyze_impact`
- `optimizer.suggest_hedges`
- `optimizer.suggest_deleveraging_hedges`

**7. Reports Agent** (Priority: P2)
- `reports.render_pdf`
- `reports.generate_csv`
- `reports.export_excel`

**8. Alerts Agent** (Priority: P2)
- `alerts.create_if_threshold`
- `alerts.suggest_presets`
- `alerts.evaluate_portfolio`

---

## 📂 Key Files Reference

### Critical Code
- **[backend/app/agents/financial_analyst.py:309](backend/app/agents/financial_analyst.py#L309)** - SYNTAX ERROR HERE (delete 309-361)
- **[backend/app/db/connection.py](backend/app/db/connection.py)** - Pool implementation (WORKING)
- **[backend/app/core/pattern_orchestrator.py](backend/app/core/pattern_orchestrator.py)** - Pattern loading & execution
- **[backend/app/core/agent_runtime.py](backend/app/core/agent_runtime.py)** - Capability routing
- **[backend/app/agents/base_agent.py](backend/app/agents/base_agent.py)** - Base class, capability naming

### Seed Data
- **[data/seeds/portfolios/portfolios.csv](data/seeds/portfolios/portfolios.csv)** - Test portfolio
- **[data/seeds/portfolios/lots.csv](data/seeds/portfolios/lots.csv)** - AAPL, RY, XIU positions
- **[scripts/seed_loader.py](scripts/seed_loader.py)** - Seed loading script

### Large Services (Most Complete)
1. **ledger.py** - 657 LOC
2. **macro.py** - 647 LOC
3. **alerts.py** - 554 LOC
4. **scenarios.py** - 538 LOC
5. **risk.py** - 526 LOC

### Large Jobs (Most Complete)
1. **metrics.py** - 839 LOC (most comprehensive)
2. **build_pricing_pack.py** - 544 LOC
3. **scheduler.py** - 545 LOC
4. **reconcile_ledger.py** - 463 LOC

---

## 🎬 Priority Action Plan

### TODAY (< 1 hour)

1. **Fix Syntax Error** (10 min)
   ```bash
   # Edit backend/app/agents/financial_analyst.py
   # Delete lines 309-361
   # Add "return result" after line 307
   ```

2. **Load Seed Data** (30 min)
   ```bash
   python scripts/seed_loader.py --domain portfolios
   # Verify: Should see 1 portfolio, 3 lots, 3+ transactions
   ```

3. **Test Startup** (10 min)
   ```bash
   cd backend && ./run_api.sh
   # Should start without errors
   ```

4. **Test Pattern** (10 min)
   ```bash
   curl -X POST http://localhost:8000/v1/execute \
     -H "Content-Type: application/json" \
     -d '{"pattern_id":"portfolio_overview","inputs":{"portfolio_id":"11111111-1111-1111-1111-111111111111"}}'
   # Should return real positions
   ```

### THIS WEEK (3-4 days)

5. **Implement Ratings Service** (2 days)
   - Create `backend/app/services/ratings.py`
   - Add 4 methods: dividend_safety, moat_strength, resilience, aggregate
   - Wire to agent (add to financial_analyst capabilities)

6. **Implement Optimizer Service** (2 days)
   - Create `backend/app/services/optimizer.py`
   - Add Riskfolio-Lib integration
   - Wire to agent

### NEXT WEEK (5 days)

7. **Complete Agent Wiring** (2 days)
   - Add 15 missing capabilities to agents
   - Wire to existing service methods

8. **Add Missing Service Methods** (3 days)
   - Cycles: compute_empire, compute_long_term, compute_short_term
   - Reports: render_pdf wrapper
   - Holding analysis methods

---

## 📊 Success Metrics

### Current (Before Fixes)
- Backend startup: ❌ (syntax error)
- Pattern execution: ❌ (cannot test)
- Real data in responses: ❌ (no data)
- Capability coverage: 45% (20/45)

### After P0 Fixes (< 1 hour)
- Backend startup: ✅
- Pattern execution: ✅ (portfolio_overview works)
- Real data in responses: ✅ (AAPL, RY, XIU)
- Capability coverage: 45% (20/45)

### After P1 Fixes (1 week)
- Backend startup: ✅
- Pattern execution: ✅ (10/12 patterns work)
- Real data in responses: ✅
- Capability coverage: 85% (38/45)

### Production Ready (2-3 weeks)
- Backend startup: ✅
- Pattern execution: ✅ (12/12 patterns work)
- Real data in responses: ✅
- Capability coverage: 100% (45/45)

---

## 💡 Key Insights for AI Assistants

### 1. Documentation Can Be Wrong
- CLAUDE.md claimed "pool issue" - actually syntax error
- CLAUDE.md claimed "15,000 LOC" - actually 23,407 LOC
- CLAUDE.md claimed "82% missing" - actually 55% missing
- **Always verify by reading code, not docs**

### 2. Seed Data vs Database State
- Seed files exist != Database has data
- Check both `data/seeds/` AND database tables
- Run seed loader after schema changes

### 3. Capability Declaration vs Implementation
- Agent must DECLARE in `get_capabilities()`
- Method name: `capability.replace(".", "_")`
- Don't count methods, count declarations

### 4. Service vs Agent Confusion
- Service has business logic
- Agent declares capability and calls service
- Missing capability != missing service (check both)

### 5. Pool Issue Was Already Fixed
- Redis coordinator exists with fallback
- Auto-reload disabled
- Syntax error masked this fix

---

## 🔗 Quick Reference

**Ports**:
- Backend: http://localhost:8000
- Frontend: http://localhost:8501
- Database: postgresql://localhost:5432/dawsos

**Health Checks**:
```bash
curl http://localhost:8000/health
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c "SELECT COUNT(*) FROM portfolios"
```

**Key Commands**:
```bash
# Syntax check
python3 -m py_compile backend/app/agents/financial_analyst.py

# Seed data
python scripts/seed_loader.py --domain portfolios

# Backend
cd backend && ./run_api.sh

# Frontend
cd frontend && ./run_ui.sh
```

---

**Last Updated**: October 24, 2025 (Post-Reconciliation Audit)
**Audited By**: AI Assistant (Deep Code Analysis)
**Accuracy**: High (verified against actual code, not documentation)
**Next Review**: After P0 fixes (< 1 hour)

---

## 🎯 TL;DR for New AI Assistants

**Application**: DawsOS - Portfolio intelligence with Dalio macro + Buffett ratings
**True Status**: **60-70% complete** (23,407 LOC verified)
**Current Blocker**: Syntax error in financial_analyst.py:309-361 (10 min fix)
**After Fix**: Load seed data (30 min), then 20/45 capabilities work
**Missing**: 2 service files (ratings, optimizer), 15 agent wirings, 8 service methods
**Timeline**: 2-3 weeks to 100% (not 3-4 days, but not 10 weeks either)

**Critical Rules**:
1. Verify ALL claims by reading code, not docs
2. Fix syntax error FIRST (backend won't start)
3. Load seed data SECOND (database is empty)
4. Check `get_capabilities()` for what's implemented
5. Pool issue is SOLVED (ignore old docs about it)

**Start Here**: Fix syntax error → Load seed data → Test startup → Implement missing services
