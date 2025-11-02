# DawsOS Development Roadmap

**Last Updated:** November 2, 2025
**Current State:** Production Ready (Commit 78a92b6)
**Purpose:** Single source of truth for development priorities and execution plan

---

## 📊 Current Status

### Working Application ✅
- **Server**: `combined_server.py` (6,046 lines, 59 endpoints)
- **UI**: `full_ui.html` (14,075 lines, 17 pages)
- **Agents**: 9 agents, 73 capabilities
- **Patterns**: 12 patterns, all validated and working
- **Database**: PostgreSQL + TimescaleDB
- **Deployment**: Single command (`python combined_server.py`)

### Known Issues (Documented)
1. **Unnecessary Complexity**: ~2100 lines of unused code (Redis, Observability, Compliance)
2. **Duplicate Code**: 4 unused files, 1 duplicate endpoint
3. **Import Dependencies**: Will break if modules removed without Phase 0
4. **Circuit Breaker**: Over-engineered but actually used (can't remove)

---

## 🎯 Active Plans (From Chat History)

### Plan 1: Documentation Cleanup ✅ COMPLETE
**Status:** Completed November 2, 2025
**Goal:** Align all documentation with current reality

**Completed:**
- ✅ README.md rewritten (52 → 389 lines)
- ✅ ARCHITECTURE.md rewritten (42 → 354 lines)
- ✅ .claude/PROJECT_CONTEXT.md created
- ✅ 29 development artifacts archived
- ✅ All 10 agent docstrings updated
- ✅ Removed "Phase" and "Priority" labels
- ✅ Fixed "Beancount" → "database" terminology

**Outcome:** Documentation now 100% accurate

---

### Plan 2: Complexity Reduction ⏳ IN PROGRESS
**Status:** Phase 0 pending, Docker infrastructure removed
**Goal:** Remove ~2100 lines of unused code
**Documents:** UNNECESSARY_COMPLEXITY_REVIEW.md, SANITY_CHECK_REPORT.md

**✅ COMPLETED:** Docker Compose files removed (docker-compose.yml, etc.)
**⚠️ CRITICAL: Must follow Phase 0 → 5 order**

#### Phase 0: Make Code Resilient (MUST DO FIRST)
**Effort:** 2 hours
**Risk:** High if skipped (ImportErrors on startup)

**Tasks:**
1. Make imports optional in `agent_runtime.py`:
   ```python
   try:
       from compliance.attribution import get_attribution_manager
       from compliance.rights_registry import get_rights_registry
   except ImportError:
       get_attribution_manager = None
       get_rights_registry = None

   try:
       from observability.metrics import get_metrics
   except ImportError:
       def get_metrics(): return None
   ```

2. Make imports optional in `pattern_orchestrator.py`:
   ```python
   try:
       from observability.metrics import get_metrics
   except ImportError:
       def get_metrics(): return None
   ```

3. Make Redis coordinator optional in `db/connection.py`:
   ```python
   try:
       from app.db.redis_pool_coordinator import coordinator
   except ImportError:
       coordinator = None
   ```

4. Test application still works

**Verification:**
- [ ] Application starts without errors
- [ ] Patterns execute successfully
- [ ] No ImportErrors in logs

---

#### Phase 1: Remove Modules
**Effort:** 1 hour
**Dependencies:** Must complete Phase 0 first

**Tasks:**
1. Archive `backend/compliance/` to `.archive/compliance/`
2. Delete `backend/observability/`
3. Delete `backend/app/db/redis_pool_coordinator.py`
4. Test imports gracefully degrade

**Verification:**
- [ ] Application still starts
- [ ] No import errors
- [ ] Patterns still execute

---

#### Phase 2: Update Scripts and Documentation
**Effort:** 30 minutes
**Dependencies:** Must complete Phase 1 first

**Tasks:**
1. Update `backend/run_api.sh`:
   - Remove `REDIS_URL` export (if present)
   - Remove Redis URL display (if present)
   - Remove Docker Compose references
2. Update analysis documents:
   - Mark Docker-related issues as RESOLVED in SANITY_CHECK_REPORT.md
   - Update UNNECESSARY_COMPLEXITY_REVIEW.md status

**Files to Update:**
- `backend/run_api.sh`
- `SANITY_CHECK_REPORT.md`
- `UNNECESSARY_COMPLEXITY_REVIEW.md`

**Verification:**
- [ ] `./backend/run_api.sh` works (or document that it's not needed for Replit)
- [ ] Documentation reflects Replit-first deployment
- [ ] No references to removed Docker files

---

#### Phase 3: Clean Requirements
**Effort:** 15 minutes
**Dependencies:** Must complete Phase 2 first

**Tasks:**
1. Edit `backend/requirements.txt`:
   - Remove `prometheus-client>=0.18.0`
   - Remove `opentelemetry-api>=1.21.0`
   - Remove `opentelemetry-sdk>=1.21.0`
   - Remove `opentelemetry-exporter-jaeger>=1.21.0`
   - Remove `opentelemetry-instrumentation-fastapi>=0.42b0`
   - Remove `sentry-sdk[fastapi]>=1.38.0`
   - Remove `redis>=` (if present)
2. Test `pip install -r backend/requirements.txt`

**Verification:**
- [ ] Pip install succeeds
- [ ] No dependency conflicts
- [ ] Application still runs

---

#### Phase 4: Simplify CircuitBreaker (Optional)
**Effort:** 2 hours
**Dependencies:** Phase 3 complete
**Note:** Can skip - CircuitBreaker works fine

**Tasks:**
1. Simplify `CircuitBreaker` class in `agent_runtime.py`:
   - Remove OPEN/HALF_OPEN states
   - Keep basic failure counting
   - **DO NOT delete** - it's used in production
2. Test failure tracking still works

**Verification:**
- [ ] Agent failures still tracked
- [ ] No breaking changes

---

#### Phase 5: Delete Safe Unused Files (Low Risk)
**Effort:** 15 minutes
**Dependencies:** None (can do anytime)

**Tasks:**
1. Delete `backend/app/core/database.py` (unused wrapper)
2. Delete `backend/api_server.py` (different namespace)
3. Delete `backend/simple_api.py` (standalone demo)
4. Delete `backend/app/services/trade_execution_old.py` (deprecated)
5. Delete duplicate `/execute` endpoint in `combined_server.py` (line 1960-2000)

**Verification:**
- [ ] Application still starts
- [ ] No import errors
- [ ] UI still works

**Expected Outcome:**
- Remove ~2100 lines of code
- Remove 4 unused files
- Simplify codebase for Replit deployment
- No functional changes

---

### Plan 3: Backend Refactoring ⏳ LOCKED (Awaiting Approval)
**Status:** Planned, not started
**Goal:** Consolidate to single coherent backend structure
**Approach:** Conservative (build alongside, test in parallel)

**Phase 1: Create New Structure**
**Effort:** 4-6 hours

**Tasks:**
1. Create `backend/app/main.py`:
   ```python
   from fastapi import FastAPI
   from app.core.agent_runtime import AgentRuntime
   from app.core.pattern_orchestrator import PatternOrchestrator
   # ... import all agents

   app = FastAPI(title="DawsOS", version="2.0.0")

   @app.on_event("startup")
   async def startup():
       # Initialize agents, orchestrator
       pass

   # Import routes from combined_server.py gradually
   ```

2. Create `backend/app/core/agent_factory.py`:
   - Consolidate agent initialization logic
   - Extract from `combined_server.py:239-304`

3. Test on port 8001:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8001
   ```

**Verification:**
- [ ] New server starts on port 8001
- [ ] Health check responds
- [ ] Pattern execution works
- [ ] Old server still works on port 8000

---

**Phase 2: Parallel Operation**
**Effort:** 2-3 weeks testing

**Tasks:**
1. Run both servers in parallel
2. Compare responses from port 8000 vs 8001
3. Verify all 17 UI pages work identically
4. Load test both servers
5. Monitor for differences

**Verification:**
- [ ] All endpoints return same data
- [ ] Performance is comparable
- [ ] No regressions found

---

**Phase 3: Migration** (Future, after 2-3 weeks)
**Effort:** 1 day

**Tasks:**
1. Update README to use `backend/app/main.py`
2. Update deployment scripts
3. Archive `combined_server.py` (keep as fallback)

**Verification:**
- [ ] Default startup uses new server
- [ ] Documentation updated
- [ ] Old server still available

**Expected Outcome:**
- Cleaner code organization
- Easier to maintain
- Better separation of concerns
- Old server preserved as fallback

---

## 🔮 Future Work (Not Planned)

### Not Started / Low Priority

1. **Pattern Fixes** (from old PATTERN_FIX_PRIORITY.md)
   - Register missing chart capabilities
   - Fix pattern orchestrator state management
   - UUID vs ticker resolution
   - **Note:** May not be needed - all patterns currently working

2. **Redis Integration** (from ARCHITECTURE.md)
   - Currently not needed (in-memory works)
   - Can add later if horizontal scaling needed

3. **Horizontal Scaling**
   - Not needed for current scale
   - Monolith works fine

4. **Microservices Extraction**
   - Backend structure ready
   - No immediate need

---

## 🚫 Explicitly Rejected / Out of Scope

1. **Next.js UI** - Archived, using full_ui.html instead
2. **Beancount Integration** - Never implemented, database-only
3. **Full Observability Stack** - Over-engineered for alpha
4. **Enterprise Compliance Features** - Not needed yet
5. **Redis for Caching** - In-memory sufficient

---

## 📋 Decision Log

### November 2, 2025
- ✅ **Decision:** Use `combined_server.py` as production entry point
- ✅ **Decision:** Use `full_ui.html` (React SPA) instead of Next.js
- ✅ **Decision:** Replit-first deployment (removed Docker Compose infrastructure)
- ✅ **Decision:** Archive (don't delete) complexity for potential future use
- ✅ **Decision:** Follow Phase 0-5 order for cleanup (CRITICAL)
- ✅ **Decision:** Simplify (don't remove) CircuitBreaker
- ✅ **Decision:** Remove Docker infrastructure (completed - all docker-compose files deleted)

### October 2025 (Historical)
- Pattern-driven architecture chosen
- Agent-based capability system implemented
- PostgreSQL + TimescaleDB selected
- Monolith deployment strategy confirmed

---

## 📊 Execution Tracking

### Completed Work
- [x] Documentation cleanup (Nov 2)
- [x] Agent docstring updates (Nov 2)
- [x] Analysis documents created (Nov 2)
- [x] Docker infrastructure removed (Nov 2)
- [x] Git rollback to stable state (Nov 1)
- [x] Pattern validation (Oct 25-31)

### In Progress
- [ ] None (awaiting user approval)

### Blocked / Waiting
- [ ] Complexity reduction (waiting for approval)
- [ ] Backend refactoring (waiting for approval)

### Not Started
- [ ] Pattern fixes (may not be needed)
- [ ] Redis integration (future consideration)

---

## 🎯 Success Criteria

### For Complexity Reduction (Plan 2)
- ✅ All imports optional (no ImportErrors)
- ✅ Application still starts and runs
- ✅ All 12 patterns still execute
- ✅ All 17 UI pages still work
- ✅ ~2100 lines of code removed
- ✅ Application works on Replit (primary deployment)
- ✅ Docker infrastructure removed (no longer needed)

### For Backend Refactoring (Plan 3)
- ✅ New server runs on port 8001
- ✅ All endpoints return same data as port 8000
- ✅ Performance is comparable
- ✅ No regressions in functionality
- ✅ Code is cleaner and more maintainable
- ✅ Old server preserved as fallback

---

## 📞 Contact / Stakeholders

**Primary Developer:** michaeldawson3 (based on git commits)
**AI Assistant:** Claude Code (documentation and analysis)
**Repository:** https://github.com/mwd474747/DawsOSP

---

**Last Review:** November 2, 2025
**Next Review:** When user approves next phase of work
