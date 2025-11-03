# DawsOS Project Context for Claude IDE

**Last Updated:** November 2, 2025
**Purpose:** Help Claude Code understand the current application state and development priorities

---

## 🔴 CRITICAL: Replit Deployment Guardrails

**READ THIS FIRST:** This application deploys on Replit. Certain files are SACRED and MUST NOT be modified.

**Full Documentation:** [REPLIT_DEPLOYMENT_GUARDRAILS.md](../REPLIT_DEPLOYMENT_GUARDRAILS.md)

**DO NOT MODIFY:**
- ❌ `.replit` - Deployment configuration (run command, ports)
- ❌ `combined_server.py` - Application entry point (Replit runs this)
- ❌ `full_ui.html` - Primary UI (served at `/`)
- ❌ Port 5000 (hardcoded in server and .replit)

**MODIFY WITH CAUTION:**
- ⚠️ `requirements.txt` - Missing packages break imports
- ⚠️ `backend/app/db/connection.py` - Database pool management
- ⚠️ `backend/app/core/agent_runtime.py` - Agent system core
- ⚠️ `backend/app/core/pattern_orchestrator.py` - Pattern execution
- ⚠️ `backend/patterns/*.json` - Business logic definitions

**SAFE TO MODIFY:**
- ✅ Test files, documentation, scripts, archive files

---

## 🎯 Current State (As of Nov 2, 2025)

### Production Stack
- **Server**: `combined_server.py` - Single FastAPI application (6,052 lines, 54 endpoints)
- **UI**: `full_ui.html` - React 18 SPA (10,882 lines, 17 pages, no build step)
- **Database**: PostgreSQL 14+ with TimescaleDB
- **Agents**: 9 specialized agents providing ~70 capabilities
- **Patterns**: 12 JSON pattern definitions

### Key Entry Points
- **Production**: `python combined_server.py` → http://localhost:8000
- **Testing**: `cd backend && uvicorn app.api.executor:executor_app --port 8001`
- **DO NOT USE**: `backend/api_server.py`, `backend/simple_api.py` (archived)

---

## 📐 Architecture Understanding

### Pattern-Driven Orchestration
```
User Request (full_ui.html)
  ↓
POST /api/patterns/execute
  ↓
combined_server.py:execute_pattern_orchestrator()
  ↓
PatternOrchestrator.run_pattern()
  ↓
AgentRuntime.get_agent_for_capability()
  ↓
Agent.execute() (e.g., FinancialAnalyst, MacroHound)
  ↓
Service.method() (e.g., ratings.py, optimizer.py)
  ↓
Database query via get_db_connection_with_rls()
  ↓ (uses pool from sys.modules['__dawsos_db_pool_storage__'])
✅ Pool accessible across all module instances (fixed Nov 2, 2025)
```

### 9 Agents (All Registered in combined_server.py:239-304)
1. **FinancialAnalyst** - ledger, pricing, metrics, attribution (25+ capabilities)
2. **MacroHound** - macro cycles, scenarios, regime detection (15+ capabilities)
   - Uses: IndicatorConfigManager for ~40 economic indicators
   - Configuration: backend/config/macro_indicators_defaults.json
3. **DataHarvester** - external data fetching, news (5+ capabilities)
4. **ClaudeAgent** - AI-powered explanations (6 capabilities)
5. **RatingsAgent** - Buffett ratings, dividend safety, moat (4 capabilities)
6. **OptimizerAgent** - rebalancing, hedging (4 capabilities)
7. **ChartsAgent** - chart formatting (3 capabilities)
8. **ReportsAgent** - PDF, CSV, Excel export (3 capabilities)
9. **AlertsAgent** - alert suggestions, thresholds (2 capabilities)

### 12 Patterns (All in backend/patterns/*.json)
All patterns are valid and working:
- portfolio_overview.json
- portfolio_scenario_analysis.json
- macro_cycles_overview.json
- policy_rebalance.json
- buffett_checklist.json
- portfolio_cycle_risk.json
- holding_deep_dive.json
- export_portfolio_report.json
- macro_trend_monitor.json
- news_impact_analysis.json
- cycle_deleveraging_scenarios.json
- portfolio_macro_overview.json

---

## ⚠️ Important: What NOT to Break

### Critical Files (DO NOT MODIFY without explicit approval)
- ✅ `combined_server.py` - Production server (working perfectly)
- ✅ `full_ui.html` - Production UI (working perfectly)
- ✅ `backend/patterns/*.json` - All 12 patterns (validated)
- ✅ `backend/app/core/pattern_orchestrator.py` - Core architecture
- ✅ `backend/app/core/agent_runtime.py` - Core architecture
- ✅ `backend/app/agents/*.py` - All agent implementations
- ✅ `backend/app/db/connection.py` - Database connection (real implementation)

### Current Status (As of Nov 2, 2025)

#### 🟢 NO ACTIVE CRITICAL ISSUES

All previously blocking issues have been resolved:
- ✅ Database pool registration fixed (module boundary issue)
- ✅ Macro cycles parameter bugs fixed
- ✅ Import dependencies resolved
- ✅ Test files cleaned up

**For Details:** See [CURRENT_ISSUES.md](../CURRENT_ISSUES.md)

#### ✅ Recently Completed Work

1. **Plan 1: Documentation Cleanup** ✅ COMPLETE (Nov 2, 2025)
2. **Plan 2: Complexity Reduction (Phase 0-5)** ✅ COMPLETE (Nov 2, 2025)
   - Phase 0: Made imports optional ✅
   - Phase 1: Removed unused modules ✅
   - Phase 2: Updated scripts ✅
   - Phase 3: Cleaned requirements.txt ✅
   - Phase 5: Deleted dead files ✅
   - Result: ~5000 lines of code removed
3. **Database Pool Fix** ✅ COMPLETE (Nov 2, 2025, commits 4d15246, e54da93)
   - Solution: Cross-module storage using sys.modules
   - connection.py simplified: 600 → 382 lines
   - All agents can now access database pool
4. **Macro Indicator Configuration System** ✅ COMPLETE (Nov 2, 2025, commits d5d6945, 51b92f3)
   - Centralized JSON configuration for ~40 indicators
   - IndicatorConfigManager service (471 lines)
   - Data quality tracking and scenario support
   - 1,410 lines of new infrastructure added

#### 📋 Known Opportunities (Not Urgent)

1. **Tactical Code Cleanup** (LOW_RISK_REFACTORING_OPPORTUNITIES_V2.md)
   - 10 low-risk refactoring opportunities identified
   - Extract constants, helpers, standardize patterns
   - Independent of strategic refactoring (Plan 3)

2. **Duplicate Endpoint** (in ROADMAP.md)
   - `/execute` endpoint unused (line 1960 in combined_server.py)
   - UI uses `/api/patterns/execute` only
   - Safe to delete when convenient

3. **✅ RESOLVED: Docker Compose Dependencies**:
   - All Docker Compose files have been removed
   - Deployment is now Replit-first (no Docker needed)

4. **Scripts May Reference Removed Features**:
   - `backend/run_api.sh` may have Redis/Docker references
   - **Should be updated or documented as optional**

**⚠️ CORRECT EXECUTION ORDER (Updated After Docker Removal):**
1. **Phase 0**: Make imports optional (try/except in agent_runtime, pattern_orchestrator, db/connection)
2. **Phase 1**: Remove modules (compliance/, observability/, redis_pool_coordinator.py)
3. **Phase 2**: Update scripts and documentation (run_api.sh, analysis docs)
4. **Phase 3**: Clean requirements.txt (remove observability packages)
5. **Phase 5**: Delete safe unused files

---

## 🚀 Development Priorities

### Immediate (Do NOT pursue unless user requests)
1. **DO NOT** start refactoring without explicit approval
2. **DO NOT** modify working code preemptively
3. **DO NOT** remove complexity without user confirmation
4. **DO NOT** skip Phase 0 (making imports optional) - will cause ImportErrors

### When Cleanup is Requested (CRITICAL: Follow Correct Order)

**⚠️ WARNING: MUST follow Phase 0 → 1 → 2 → 3 → 4 → 5 order or will break application**

**Phase 0: Make Code Resilient** (MUST DO FIRST)
1. Make imports optional in `agent_runtime.py`:
   ```python
   try:
       from compliance.attribution import get_attribution_manager
   except ImportError:
       get_attribution_manager = None
   ```
2. Make imports optional in `pattern_orchestrator.py`
3. Make Redis coordinator optional in `db/connection.py`
4. Test that application still works

**Phase 1: Remove Modules** (After Phase 0 only)
1. Archive `backend/compliance/` to `.archive/compliance/`
2. Delete `backend/observability/`
3. Delete `backend/app/db/redis_pool_coordinator.py`
4. Test that imports gracefully degrade

**Phase 2: Update Scripts and Documentation** (After Phase 1 only)
1. Update `backend/run_api.sh` - remove REDIS_URL and Docker references
2. Mark Docker issues as RESOLVED in SANITY_CHECK_REPORT.md
3. Update UNNECESSARY_COMPLEXITY_REVIEW.md status
4. Test script execution (or document as optional for Replit)

**Phase 3: Clean Requirements** (After Phase 2 only)
1. Remove observability packages from `requirements.txt`
2. Test pip install

**Phase 5: Delete Safe Files** (Low risk, anytime)
1. Delete `backend/app/core/database.py`
2. Delete `backend/api_server.py`
3. Delete `backend/simple_api.py`
4. Delete `backend/app/services/trade_execution_old.py`
5. Delete duplicate `/execute` endpoint in combined_server.py (line 1960)

### When Backend Refactoring is Requested
1. **Conservative approach**: Build new structure alongside existing (port 8001)
2. **Test in parallel** before migrating
3. **Keep combined_server.py** as fallback

---

## 📚 Documentation Status

### Core Documentation (Up to Date)
- ✅ `README.md` - Recently updated (389 lines, accurate)
- ✅ `ARCHITECTURE.md` - Recently updated (354 lines, accurate)
- ✅ `PRODUCT_SPEC.md` - Product specifications
- ✅ `TROUBLESHOOTING.md` - Troubleshooting guide

### Development Artifacts (Archived)
- 📦 `.archive/docs-development-artifacts-2025-11-02/` - 29 files
  - Historical snapshots from development iterations
  - Useful for understanding evolution, but not current state

### Active Analysis Documents (Keep in Root)
- 📝 `UNNECESSARY_COMPLEXITY_REVIEW.md` - Recent complexity audit
- 📝 `CLEANUP_DEPENDENCY_AUDIT.md` - Recent dependency analysis

---

## 🔧 Environment and Commands

### Development Startup
```bash
export DATABASE_URL="postgresql://localhost/dawsos"
export ANTHROPIC_API_KEY="sk-ant-..."  # Optional
export FRED_API_KEY="..."              # Optional

# Start production server
python combined_server.py  # → http://localhost:8000

# OR start test server
cd backend
uvicorn app.api.executor:executor_app --reload --port 8001
```

### Testing
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

### Database
```bash
# Connect to database
psql $DATABASE_URL

# Check tables
\dt
```

---

## 🎨 Code Style and Patterns

### Request Flow Pattern
```python
# Pattern in combined_server.py
@app.post("/api/patterns/execute")
async def execute_pattern_orchestrator(request: ExecuteRequest):
    orchestrator = get_pattern_orchestrator()
    result = await orchestrator.run_pattern(
        pattern_id=request.pattern,
        inputs=request.inputs
    )
    return {"status": "success", "data": result}
```

### Agent Capability Pattern
```python
# Capability in agent (e.g., FinancialAnalyst)
async def ledger_positions(self, portfolio_id: str):
    """Capability: ledger.positions"""
    conn = await get_db_connection_with_rls(user_id)
    result = await conn.fetch("SELECT * FROM lots WHERE portfolio_id = $1", portfolio_id)
    return {"positions": result}
```

### Pattern Definition Pattern
```json
{
  "id": "portfolio_overview",
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}"},
      "as": "positions"
    },
    {
      "capability": "pricing.apply_pack",
      "args": {"positions": "{{positions.positions}}"},
      "as": "valued_positions"
    }
  ]
}
```

---

## 🚫 Anti-Patterns (Do NOT do these)

### 1. DO NOT Modify full_ui.html Without Testing
- 14,075 lines of working React code
- No build step means syntax errors break immediately
- Test changes in browser console first

### 2. DO NOT Change Pattern JSON Without Validation
- All 12 patterns are validated and working
- Changing capability names breaks agent routing
- Validate template substitution syntax

### 3. DO NOT Remove Files Without Dependency Check
- Use `grep -r "import.*filename" .` first
- Check CLEANUP_DEPENDENCY_AUDIT.md
- Verify UI doesn't reference deleted endpoints

### 4. DO NOT Add Services Without Necessity
- Redis: Not needed (in-memory caching works)
- Observability: Not needed for alpha (logging sufficient)
- Circuit Breaker: Not needed for monolith

---

## 💡 Quick Reference

### Find Pattern Usage in UI
```bash
grep -n "pattern.*portfolio_overview" full_ui.html
# Shows all lines where pattern is referenced
```

### Find Agent Capabilities
```bash
grep -r "async def " backend/app/agents/*.py | grep -v "^#"
# Lists all agent methods
```

### Verify Pattern Exists
```bash
ls -1 backend/patterns/*.json | wc -l
# Should return: 12
```

### Check Agent Registration
```bash
grep "register_agent" combined_server.py
# Shows all 9 agent registrations
```

---

## 🎯 Key Insights for Claude Code

### When User Asks to "Fix Patterns"
1. First check: CLEANUP_DEPENDENCY_AUDIT.md section 4 (Pattern Dependencies Trace)
2. Verify pattern JSON exists in `backend/patterns/`
3. Check agent capabilities exist (see Agent Capability Pattern above)
4. Test pattern via `/api/patterns/execute` endpoint

### When User Asks to "Refactor Backend"
1. First check: Locked refactoring plan from previous conversation
2. **Conservative approach**: Build new structure alongside existing (port 8001)
3. **Test in parallel** before migrating
4. **Keep combined_server.py** as fallback

### When User Asks to "Remove Complexity"
1. First check: UNNECESSARY_COMPLEXITY_REVIEW.md
2. Safe Phase 1 removals:
   - Redis infrastructure (~500 lines)
   - Observability stack (~500 lines)
3. Archive (don't delete): Compliance module (~1000 lines)

### When User Reports "UI Not Working"
1. Check `combined_server.py` is running on port 8000
2. Verify `full_ui.html` exists in root directory
3. Check browser console for errors
4. Verify `/api/patterns/execute` endpoint responds

---

## 📊 Metrics

### Codebase Size
- `combined_server.py`: 6,046 lines (59 endpoints)
- `full_ui.html`: 14,075 lines (17 pages)
- `backend/app/`: ~15,000 lines (agents, services, core)
- **Total Backend**: ~21,000 lines
- **Total UI**: ~14,000 lines
- **Unused Code**: ~2,100 lines (identified for removal)

### Pattern/Agent Coverage
- **Patterns**: 12 defined, 12 working (100%)
- **Agents**: 9 registered, 9 working (100%)
- **Capabilities**: 73 total methods, 46 used in patterns (63% utilization)
- **Endpoints**: 59 total, ~40 actively used by UI

---

## 🔄 Recent Changes (Last 24 Hours)

### Documentation Updates
- ✅ README.md rewritten (52 → 389 lines)
- ✅ ARCHITECTURE.md rewritten (42 → 354 lines)
- ✅ 29 development artifacts archived to `.archive/docs-development-artifacts-2025-11-02/`
- ✅ .claude/PROJECT_CONTEXT.md created (comprehensive current state)
- ✅ Agent docstrings updated (removed Phase/Priority refs, updated Beancount→database)

### Recent Analysis Documents Created
- 📝 UNNECESSARY_COMPLEXITY_REVIEW.md - Identifies ~2100 lines of unused code
- 📝 CLEANUP_DEPENDENCY_AUDIT.md - Validates all deletions are safe
- 📝 SANITY_CHECK_REPORT.md - **CRITICAL** - Identifies import dependencies that will break

### Code Changes
- ✅ Agent docstrings updated (all 10 agent files)
- ✅ Removed "Phase 4", "P0/P1/P2" priority labels
- ✅ Fixed "Beancount ledger" → "database ledger" terminology
- ✅ Updated dates to 2025-11-02
- ✅ Application still stable (no functional code changes)

### Planned Work (Awaiting User Approval)

- **Plan 3: Backend Refactoring** (See PLAN_3_BACKEND_REFACTORING_REVALIDATED.md)
  - Extract combined_server.py into modular structure
  - Build on port 8001, test in parallel with port 5000
  - Conservative approach: Keep old server as fallback
  - Timeline: 3-4 weeks (1 week build, 2-3 weeks testing, 1 day migration)

---

## 📚 Related Documentation for Multi-Agent Work

**Current Status & Issues:**
- [CURRENT_ISSUES.md](../CURRENT_ISSUES.md) - Active issues and recent fixes
- [DATABASE_OPERATIONS_VALIDATION.md](../DATABASE_OPERATIONS_VALIDATION.md) - Historical pool issue analysis

**Architecture & Planning:**
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture with pool solution
- [ROADMAP.md](../ROADMAP.md) - Development roadmap and completed work
- [PLAN_3_BACKEND_REFACTORING_REVALIDATED.md](../PLAN_3_BACKEND_REFACTORING_REVALIDATED.md) - Future refactoring plan

**Configuration:**
- [backend/config/INDICATOR_CONFIG_README.md](../backend/config/INDICATOR_CONFIG_README.md) - Macro indicator configuration

**Deployment & Operations:**
- [REPLIT_DEPLOYMENT_GUARDRAILS.md](../REPLIT_DEPLOYMENT_GUARDRAILS.md) - Critical files (DO NOT MODIFY)
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment steps
- [replit.md](../replit.md) - Replit-specific setup
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Common issues

---

**Remember:** This is a working production application. Preserve functionality first, optimize second. Always test changes on port 8001 before touching port 8000.
