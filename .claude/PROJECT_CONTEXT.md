# DawsOS Project Context for Claude IDE

**Last Updated:** November 5, 2025
**Purpose:** Help Claude Code understand the current application state and development priorities

---

## 🔴 CRITICAL: Replit Deployment Guardrails

**READ THIS FIRST:** This application deploys on Replit. Certain files are SACRED and MUST NOT be modified.

**Full Documentation:** [REPLIT_DEPLOYMENT_GUARDRAILS.md](../.archive/deprecated/REPLIT_DEPLOYMENT_GUARDRAILS.md)

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

## 🎯 Current State (As of Nov 3, 2025)

### Production Stack
- **Server**: `combined_server.py` - Single FastAPI application (6,043 lines, 53 functional endpoints)
- **UI**: `full_ui.html` - React 18 SPA (11,594 lines, 18 pages including login, no build step)
- **Database**: PostgreSQL 14+ with TimescaleDB
- **Agents**: 4 specialized agents providing ~70 capabilities (Phase 3 consolidation complete, November 3, 2025)
- **Patterns**: 13 JSON pattern definitions (including corporate_actions_upcoming)

### Key Entry Points
- **Production**: `python combined_server.py` → http://localhost:8000
- **Testing**: `cd backend && uvicorn app.api.executor:executor_app --port 8001`
- **DO NOT USE**: `backend/api_server.py`, `backend/simple_api.py` (archived)

---

## ⚠️ Known Technical Debt (Identified Nov 5, 2025)

### Zombie Consolidation Code
- Phase 3 consolidation (Nov 3) left 2,345 lines of scaffolding code
- Feature flags at 100% rollout (no gradual deployment happening)
- Capability mapping maps deleted agents (old agents gone)
- Must be removed before other refactoring (blocks work)
- See: [ZOMBIE_CODE_VERIFICATION_REPORT.md](../ZOMBIE_CODE_VERIFICATION_REPORT.md)

### Critical Discovery: FactorAnalyzer EXISTS!
- `backend/app/services/factor_analysis.py` (438 lines) EXISTS with real implementation
- `risk_compute_factor_exposures` uses stub data instead of calling this service
- Inconsistency: `risk_get_factor_exposure_history` DOES use the real service
- Could save 40 hours if service works (needs testing)
- See: [COMPREHENSIVE_REFACTORING_PLAN.md](../COMPREHENSIVE_REFACTORING_PLAN.md) Phase 0 Task 0.5

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

### 4 Agents (All Registered in executor.py and combined_server.py)
**Phase 3 Consolidation Complete (November 3, 2025):**

1. **FinancialAnalyst** - Portfolio ledger, pricing, metrics, attribution, optimization, ratings, charts (~35+ capabilities)
   - **Consolidated from:** OptimizerAgent, RatingsAgent, ChartsAgent (Phase 3 Weeks 1-3)
   - Capabilities: `ledger.*`, `pricing.*`, `metrics.*`, `attribution.*`, `charts.*`, `risk.*`, `portfolio.*`, `optimizer.*`, `ratings.*`
2. **MacroHound** - Macro economic cycles, scenarios, regime detection, alerts (~17+ capabilities)
   - **Consolidated from:** AlertsAgent (Phase 3 Week 4)
   - Uses: IndicatorConfigManager for ~40 economic indicators
   - Configuration: backend/config/macro_indicators_defaults.json
   - Capabilities: `macro.*`, `scenarios.*`, `cycles.*`, `alerts.*`
3. **DataHarvester** - External data fetching, news, reports, corporate actions (~8+ capabilities)
   - **Consolidated from:** ReportsAgent (Phase 3 Week 5)
   - Capabilities: `data.*`, `news.*`, `reports.*`, `corporate_actions.*`
4. **ClaudeAgent** - AI-powered explanations and insights (~6 capabilities)
   - Capabilities: `claude.*`, `ai.*`

### 13 Patterns (All in backend/patterns/*.json)

**Used in UI (9 patterns):**
- ✅ portfolio_overview.json - Dashboard page
- ✅ portfolio_cycle_risk.json - Risk Analytics page
- ✅ portfolio_scenario_analysis.json - Scenarios page
- ✅ macro_cycles_overview.json - Cycles page
- ✅ buffett_checklist.json - Buffett page
- ✅ news_impact_analysis.json - News page
- ✅ export_portfolio_report.json - Export feature
- ✅ policy_rebalance.json - Rebalancing
- ✅ corporate_actions_upcoming.json - Corporate actions ✅ **NEW** (November 3, 2025)

**Unused (4 patterns - Decision Needed):**
- ⚠️ holding_deep_dive.json - Could implement UI page (16h)
- ⚠️ portfolio_macro_overview.json - Redundant with portfolio_cycle_risk
- ⚠️ cycle_deleveraging_scenarios.json - Could merge into scenarios
- ⚠️ macro_trend_monitor.json - Implement alerts or delete?

**See [REFACTORING_MASTER_PLAN.md](../REFACTORING_MASTER_PLAN.md) Decision Point 1 for recommendations**

---

## ⚠️ Important: What NOT to Break

### Critical Files (DO NOT MODIFY without explicit approval)
- ✅ `combined_server.py` - Production server (working perfectly)
- ✅ `full_ui.html` - Production UI (working perfectly)
- ✅ `backend/patterns/*.json` - All 13 patterns (validated)
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

1. **Plan 1: Documentation Cleanup** ✅ COMPLETE (Nov 2-3, 2025)
   - Consolidated 42 files → 20 files (52% reduction)
   - Fixed 32 inaccuracies (pattern count, line counts, endpoint counts)
   - Added critical setup guides (database, security, environment variables)
   - Created comprehensive references (DATABASE.md, DEVELOPMENT_GUIDE.md, PATTERNS_REFERENCE.md)
   - Investigation reports: HOLDINGS_DETAIL_INVESTIGATION.md, DOCUMENTATION_FINAL_REVIEW_REPORT.md

2. **Plan 2: Complexity Reduction (Phase 0-5)** ✅ COMPLETE (Nov 2, 2025)
   - Phase 0: Made imports optional ✅
   - Phase 1: Removed unused modules (~88KB: compliance, observability, redis) ✅
   - Phase 2: Updated scripts (run_api.sh, executor.py) ✅
   - Phase 3: Cleaned requirements.txt (7 packages removed) ✅
   - Phase 5: Deleted dead files (4 files, ~62KB) ✅
   - Result: ~150KB of code removed, 7 dependencies eliminated
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

### Current Status: Refactoring Analysis Complete ✅

**Recently Completed (Nov 5, 2025):**
- ✅ Comprehensive codebase review (3+ documents)
- ✅ Zombie code verification (confirmed exists)
- ✅ Refactoring plan creation (88-134 hour roadmap)
- ✅ FactorAnalyzer discovery (potential 40h savings)

### Immediate Next Steps (Awaiting User Approval)

**Quick Win Opportunity (30 min):**
- Test FactorAnalyzer to see if it works with real portfolio data
- Location: `backend/app/services/factor_analysis.py`
- If YES: Wire up in Phase 1, skip Phase 3 implementation (save 40h)
- If NO: Document what data is missing (populate in Phase 3)

**Phase 0: Zombie Code Removal (14 hours)**
Must execute BEFORE Phase 1-4 to unblock refactoring:
1. Remove feature flags (feature_flags.py, feature_flags.json)
2. Remove capability mapping (capability_mapping.py)
3. Simplify agent runtime routing (~80 lines → ~10 lines)
4. Remove duplicate service (macro_aware_scenarios.py - unused)
5. Test FactorAnalyzer (critical decision point)
6. Update documentation

**Phase 1-4: Follow Comprehensive Plan**
- See [COMPREHENSIVE_REFACTORING_PLAN.md](../COMPREHENSIVE_REFACTORING_PLAN.md) for complete details
- Each phase delivers independent value
- Can pause between phases to evaluate

### When Cleanup is Requested (UPDATED Nov 5, 2025)

**⚠️ IMPORTANT: Zombie code cleanup is NOW PRIORITY 1**

Old context said "make imports optional first" (Phase 0 - already complete).
New context says "remove zombie code first" (Phase 0 - new focus).

**Correct Order:**
1. Phase 0: Remove zombie code (14h) - UNBLOCKS everything
2. Phase 1: Emergency fixes (16h) - Preserve user trust
3. Phase 2: Foundation (32h) - Prevent future bugs
4. Phase 3: Features (2-48h) - Real implementations
5. Phase 4: Quality (24h) - Tests and monitoring

### When User Asks About Refactoring

**DO:**
- ✅ Reference [COMPREHENSIVE_REFACTORING_PLAN.md](../COMPREHENSIVE_REFACTORING_PLAN.md) for details
- ✅ Start with Phase 0 Task 0.5 (test FactorAnalyzer) - quick win
- ✅ Follow decision tree based on test results
- ✅ Execute phases sequentially (0 → 1 → 2 → 3 → 4)

**DON'T:**
- ❌ Skip Phase 0 (zombie code blocks other work)
- ❌ Implement factor analysis from scratch without testing existing service
- ❌ Modify working code without Phase 0 cleanup first

---

## 📚 Documentation Status

### Core Documentation (Recently Updated - Nov 3, 2025)
- ✅ `README.md` - Updated with security warnings, AUTH_JWT_SECRET requirements
- ✅ `ARCHITECTURE.md` - Fixed counts, auth coverage, environment variables reference
- ✅ `DATABASE.md` - Added complete 160-line database setup guide (NEW)
- ✅ `DEVELOPMENT_GUIDE.md` - Developer reference (NEW)
- ✅ `PATTERNS_REFERENCE.md` - Pattern system reference (NEW)
- ✅ `PRODUCT_SPEC.md` - Product specifications
- ✅ `TROUBLESHOOTING.md` - Troubleshooting guide

### Investigation Reports (Nov 3, 2025)
- 📝 `DOCUMENTATION_FINAL_REVIEW_REPORT.md` - Comprehensive review (47 issues identified) (NEW)
- 📝 `DOCUMENTATION_IMPROVEMENTS_SUMMARY.md` - Summary of all improvements (NEW)
- 📝 `HOLDINGS_DETAIL_INVESTIGATION.md` - Proves holdings_detail was a typo (NEW)

### Development Artifacts (Archived)
- 📦 `.archive/docs-development-artifacts-2025-11-02/` - 29 files
  - Historical snapshots from development iterations
  - Useful for understanding evolution, but not current state

### Active Analysis Documents (Keep in Root)
- 📝 `UNNECESSARY_COMPLEXITY_REVIEW.md` - Recent complexity audit
- 📝 `CLEANUP_DEPENDENCY_AUDIT.md` - Recent dependency analysis

---

## 🗺️ Active Refactoring Plans (Nov 5, 2025)

### Comprehensive Refactoring Analysis Complete
Following extensive code review, 4 major planning documents created:

1. **[ZOMBIE_CODE_VERIFICATION_REPORT.md](../ZOMBIE_CODE_VERIFICATION_REPORT.md)** (500+ lines)
   - Verified zombie consolidation code exists (2,345 lines)
   - Identified duplicate services (MacroAwareScenarioService unused)
   - Discovered FactorAnalyzer exists but unused
   - Status: ✅ Analysis complete, Phase 0 ready to execute

2. **[COMPREHENSIVE_REFACTORING_PLAN.md](../COMPREHENSIVE_REFACTORING_PLAN.md)** (2,800+ lines)
   - Complete 88-134 hour execution plan
   - Phase 0: Zombie code removal (14h)
   - Phase 1: Emergency fixes (16h)
   - Phase 2: Foundation (32h)
   - Phase 3: Features (2-48h depending on test results)
   - Phase 4: Quality (24h)
   - Status: 🎯 Ready for execution

3. **[REFACTORING_MASTER_PLAN.md](../REFACTORING_MASTER_PLAN.md)** (540 lines)
   - User-centric, feature-driven approach
   - 11 of 18 UI pages work correctly
   - 1 UI page shows fake data (Risk Analytics - critical trust issue)
   - 4 patterns unused (holding_deep_dive, portfolio_macro_overview, etc.)
   - Status: ✅ Analysis complete

4. **[INTEGRATED_REFACTORING_ANALYSIS.md](../INTEGRATED_REFACTORING_ANALYSIS.md)**
   - Synthesis of all review findings
   - Combines codebase review, pattern analysis, Replit analysis
   - Status: ✅ Complete

### Next Steps (Awaiting User Decision)
- **Immediate:** Execute Phase 0 Task 0.5 - Test FactorAnalyzer (2 hours)
  - If works: Save 40 hours
  - If needs data: Add 8 hours to populate tables
  - If broken: Proceed with library/scratch implementation
- **Then:** Execute Phase 0 zombie code removal (14 hours)
- **Then:** Execute Phase 1-4 per comprehensive plan

---

## 🔧 Environment and Commands

### Development Startup

**⚠️ REQUIRED Environment Variables:**
```bash
# Database connection (REQUIRED)
export DATABASE_URL="postgresql://localhost/dawsos"

# JWT authentication secret (REQUIRED - 32+ characters)
# Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
export AUTH_JWT_SECRET="<generated-secure-random-key>"
```

**Optional Environment Variables:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # For AI insights (claude.* capabilities)
export FRED_API_KEY="..."              # For economic data (macro indicators)
export CORS_ORIGINS="https://yourdomain.com"  # CORS allowed origins
export LOG_LEVEL="INFO"                # Logging level
```

**Start Server:**
```bash
# Production server
python combined_server.py  # → http://localhost:8000

# OR test server
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

**Database Setup (NEW - Added Nov 3, 2025):**

See [DATABASE.md](../DATABASE.md) for complete setup guide.

**Quick Setup:**
```bash
# 1. Install PostgreSQL 14+ and TimescaleDB
brew install postgresql@14 timescaledb

# 2. Create database
createdb dawsos
psql -d dawsos -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"

# 3. Run migrations
psql -d dawsos < backend/db/migrations/001_core_schema.sql
psql -d dawsos < backend/db/migrations/002_seed_data.sql
psql -d dawsos < backend/db/migrations/003_create_portfolio_metrics.sql
psql -d dawsos < backend/db/migrations/004_create_currency_attribution.sql
psql -d dawsos < backend/db/migrations/010_add_users_and_audit_log.sql.disabled

# 4. Verify
psql -d dawsos -c "\dt"
```

**Daily Operations:**
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
- 11,594 lines of working React code
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

### 4. DO NOT Use Weak AUTH_JWT_SECRET
- ❌ NEVER use `AUTH_JWT_SECRET="your-secret"`
- ✅ ALWAYS generate with: `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`

### 5. DO NOT Deploy with Default Credentials
- ❌ Default password: mozzuq-byfqyQ-5tefvu (DEVELOPMENT ONLY)
- ✅ See README.md security checklist before production

### 6. DO NOT Add Services Without Necessity
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

## 📊 Metrics (Verified Nov 3, 2025)

### Codebase Size
- `combined_server.py`: 6,043 lines (53 functional endpoints)
- `full_ui.html`: 11,594 lines (18 pages including login)
- `backend/app/`: ~15,000 lines (agents, services, core)
- **Total Backend**: ~21,000 lines
- **Total UI**: ~11,500 lines
- **Code Removed**: ~150KB (Phase 1-5 cleanup)

### Pattern/Agent Coverage
- **Patterns**: 13 defined, 9 used in UI (69%), 4 unused
- **Agents**: 4 registered, 4 working (100%) ← Phase 3 consolidation complete
- **Auth Coverage**: 44/53 endpoints use Depends(require_auth) (83%)
- **Capabilities**: ~80 total methods (per COMPREHENSIVE_REFACTORING_PLAN.md Task 2.1)

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

---

## 🤖 Claude Code IDE Agent Configuration

**Current Configuration:**
- ✅ Context files: PROJECT_CONTEXT.md (this file) - accurate as of Nov 5, 2025
- ✅ Permission settings: settings.local.json - Bash command allowlist
- ✅ Slash commands: 4 Phase 1 commands implemented ← **NEW**
- ❌ Hooks: None configured
- ❌ MCP servers: None configured

**Implemented Slash Commands (Phase 1):**
- ✅ `/verify-setup` - Verify development environment
- ✅ `/test-factor-analyzer` - Test FactorAnalyzer service (CRITICAL: saves 40h if works)
- ✅ `/phase-status` - Check refactoring phase progress
- ✅ `/check-stub-data` - Find stub data locations (user trust issues)

**Available for Implementation:**
See [CLAUDE_IDE_AGENTS_RECOMMENDATION.md](CLAUDE_IDE_AGENTS_RECOMMENDATION.md) for:
- 4 additional Phase 2/3 slash commands (validate-pattern, fix-field-bug, db-schema, run-migration)
- 2 hooks for quality assurance
- Optional MCP server for database inspection

**Status:** ✅ Phase 1 complete (4 commands), Phase 2/3 optional
