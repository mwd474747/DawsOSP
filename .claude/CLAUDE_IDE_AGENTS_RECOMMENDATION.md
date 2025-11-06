# Claude Code IDE Agents Recommendation for DawsOS

**Date:** November 5, 2025
**Purpose:** Recommend optimal Claude Code IDE agent configuration for building DawsOS portfolio management application
**Status:** 🎯 **ACTIONABLE RECOMMENDATIONS**

---

## Executive Summary

**Current IDE Agent Configuration:**
- ✅ Context files: 1 active (PROJECT_CONTEXT.md) - now accurate
- ✅ Permission settings: 1 file (settings.local.json) - working
- ❌ Slash commands: None configured
- ❌ Hooks: None configured
- ❌ MCP servers: None configured

**Recommended Configuration:**
- ✅ Keep: PROJECT_CONTEXT.md (recently updated)
- ✅ Keep: settings.local.json (permission allowlist)
- ✅ Add: 8 custom slash commands for common workflows
- ✅ Add: 2 hooks for quality assurance
- ✅ Consider: MCP server for database inspection (optional)

---

## Analysis: What This Application Needs

### Application Characteristics

**DawsOS is a Financial Portfolio Management System:**
- **Backend:** FastAPI monolith (21,000 lines) with 4 agents, 13 patterns
- **Frontend:** React SPA (11,594 lines) - no build step
- **Database:** PostgreSQL 14+ with TimescaleDB
- **Architecture:** Pattern-driven orchestration (JSON patterns → agents → services)
- **Current Phase:** Refactoring (Phase 0-4, 102-134 hours planned)

**Key Development Activities:**
1. **Refactoring phases** (current priority)
   - Phase 0: Zombie code removal (14h)
   - Phase 1: Emergency fixes (16h)
   - Phase 2: Foundation/validation (32h)
   - Phase 3: Feature implementation (16-48h)
   - Phase 4: Quality/testing (24h)

2. **Bug fixes** (critical bugs identified)
   - Field name mismatches (valuation_date vs asof_date)
   - Import errors (FactorAnalysisService vs FactorAnalyzer)
   - Missing database tables (economic_indicators)

3. **Pattern development** (13 patterns, 4 unused)
   - Validating JSON pattern definitions
   - Testing pattern orchestration
   - Debugging capability routing

4. **Service integration** (70+ capabilities across 4 agents)
   - Wiring services to capabilities
   - Testing database queries
   - Validating data provenance

5. **Database operations** (PostgreSQL + TimescaleDB)
   - Schema migrations
   - Query optimization
   - Data validation

---

## Recommended Slash Commands

### Command 1: `/verify-setup` - Development Environment Check

**Purpose:** Quickly verify development environment is configured correctly

**File:** `.claude/commands/verify-setup.md`

```markdown
---
description: Verify DawsOS development environment setup
---

Run comprehensive setup verification:

1. Check pattern count: `ls -1 backend/patterns/*.json | wc -l` (should be 13)
2. Check agent count: `grep -c "register_agent" combined_server.py` (should be 4)
3. Check database connection: `psql $DATABASE_URL -c "\dt" | wc -l` (should show tables)
4. Check environment variables:
   - `echo $DATABASE_URL` (should be set)
   - `echo $AUTH_JWT_SECRET` (should be 32+ chars)
5. Check server health: `curl -s http://localhost:8000/health | jq .`
6. Check endpoints: `curl -s http://localhost:8000/docs` (should return OpenAPI spec)

Report any failures clearly.
```

---

### Command 2: `/fix-field-bug` - Fix Critical Field Name Bug

**Purpose:** Quick access to field name bug fix instructions (valuation_date vs asof_date)

**File:** `.claude/commands/fix-field-bug.md`

```markdown
---
description: Fix critical field name bug in FactorAnalyzer
---

Fix the critical field name mismatch bug:

**Bug:** FactorAnalyzer uses `asof_date` but schema has `valuation_date`
**File:** `backend/app/services/factor_analysis.py`
**Line:** 287-290

**Fix:**
Change:
```sql
SELECT asof_date, total_value
FROM portfolio_daily_values
WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3
```

To:
```sql
SELECT valuation_date as asof_date, total_value
FROM portfolio_daily_values
WHERE portfolio_id = $1 AND valuation_date BETWEEN $2 AND $3
```

**Verify:** Run factor analysis query and ensure no SQL errors.

See: REPLIT_BACKEND_TASKS.md Task 1 for complete details.
```

---

### Command 3: `/validate-pattern` - Pattern Validation Workflow

**Purpose:** Validate a pattern JSON file before deploying

**File:** `.claude/commands/validate-pattern.md`

```markdown
---
description: Validate a pattern JSON file for correctness
---

Validate pattern JSON file:

**Input:** Pattern file path (e.g., `backend/patterns/portfolio_overview.json`)

**Validation Steps:**
1. **JSON Syntax:** Verify valid JSON with `jq . $PATTERN_FILE`
2. **Required Fields:** Check `id`, `steps`, `name` fields exist
3. **Step Format:** Each step has `capability`, `args`, `as` fields
4. **Template Syntax:** All `{{...}}` references are valid
5. **Capability References:** All capabilities exist in agents
6. **Step Dependencies:** Referenced steps exist (e.g., `{{step1.data}}`)

**Capability Check:**
```bash
# Extract capabilities from pattern
jq -r '.steps[].capability' $PATTERN_FILE

# Check each capability exists in agents
grep "async def capability_name" backend/app/agents/*.py
```

**Output:** Report validation status (PASS/FAIL with specific errors)

See: PHASE_2_DETAILED_PLAN.md Task 2.2 for validation requirements.
```

---

### Command 4: `/test-factor-analyzer` - Test FactorAnalyzer Service

**Purpose:** Test FactorAnalyzer service with real portfolio data (Phase 0 Task 0.5)

**File:** `.claude/commands/test-factor-analyzer.md`

```markdown
---
description: Test FactorAnalyzer service with real data (Phase 0 critical decision)
---

Test FactorAnalyzer to determine if we can use it or must reimplement:

**This is a CRITICAL DECISION POINT:**
- If works: Save 40 hours (skip Phase 3 implementation)
- If needs data: Add 8 hours (populate tables)
- If broken: Proceed with library/scratch implementation (40h)

**Test Script:**
```python
import asyncio
from app.services.factor_analysis import FactorAnalyzer
from app.db.connection import get_db_pool

async def test_factor_analyzer():
    db = await get_db_pool()
    analyzer = FactorAnalyzer(db)

    # Get real portfolio_id and pack_id
    portfolio_row = await db.fetchrow("SELECT portfolio_id FROM portfolios LIMIT 1")
    pack_row = await db.fetchrow("SELECT pack_id FROM pricing_packs ORDER BY date DESC LIMIT 1")

    result = await analyzer.compute_factor_exposure(
        portfolio_id=str(portfolio_row["portfolio_id"]),
        pack_id=str(pack_row["pack_id"]),
        lookback_days=252
    )

    if "error" in result:
        print(f"⚠️  FactorAnalyzer returned error: {result['error']}")
        print("Check if portfolio_daily_values and economic_indicators tables populated")
    else:
        print(f"✅ FactorAnalyzer works! R² = {result.get('r_squared', 0):.2%}")
        print("Can use this instead of stub, save 40 hours")

asyncio.run(test_factor_analyzer())
```

**Decision Tree:**
- ✅ Works → Wire up in Phase 1, skip Phase 3 implementation
- ⚠️ Missing data → Populate tables (8h), then wire up
- ❌ Broken → Implement from scratch (40h)

See: COMPREHENSIVE_REFACTORING_PLAN.md Phase 0 Task 0.5
```

---

### Command 5: `/phase-status` - Check Refactoring Phase Status

**Purpose:** Get current status of refactoring phases

**File:** `.claude/commands/phase-status.md`

```markdown
---
description: Check status of refactoring phases
---

Check refactoring phase status:

**Phase 0: Zombie Code Removal (14h)**
- [ ] Task 0.1: Remove feature flags (2h)
- [ ] Task 0.2: Remove capability mapping (3h)
- [ ] Task 0.3: Simplify agent runtime (4h)
- [ ] Task 0.4: Remove duplicate services (3h)
- [ ] Task 0.5: Test FactorAnalyzer (2h) - **CRITICAL DECISION**

Check:
```bash
# Feature flags still exist?
ls backend/config/feature_flags.json 2>/dev/null && echo "❌ Phase 0.1 not done" || echo "✅ Phase 0.1 done"

# Capability mapping still exists?
ls backend/app/core/capability_mapping.py 2>/dev/null && echo "❌ Phase 0.2 not done" || echo "✅ Phase 0.2 done"

# MacroAwareScenarioService still exists?
ls backend/app/services/macro_aware_scenarios.py 2>/dev/null && echo "❌ Phase 0.4 not done" || echo "✅ Phase 0.4 done"
```

**Phase 1: Emergency Fixes (16h)**
- [ ] Task 1.1: Add provenance warnings (4h)
- [ ] Task 1.2: Fix critical bugs (8h)
- [ ] Task 1.3: Wire FactorAnalyzer (4h)

**Phase 2: Foundation (32h)**
- [ ] Task 2.1: Define capability contracts (8h)
- [ ] Task 2.2: Implement pattern validation (12h)
- [ ] Task 2.3: Standardize response format (8h)
- [ ] Task 2.4: Update documentation (4h)

**Phase 3: Features (16-48h)**
- Depends on FactorAnalyzer test results

**Phase 4: Quality (24h)**
- [ ] Task 4.1: Write tests (16h)
- [ ] Task 4.2: Add monitoring (8h)

See: COMPREHENSIVE_REFACTORING_PLAN.md for complete details
```

---

### Command 6: `/check-stub-data` - Find Stub Data in Codebase

**Purpose:** Identify capabilities returning stub/fake data

**File:** `.claude/commands/check-stub-data.md`

```markdown
---
description: Find capabilities returning stub/fake data
---

Search for stub data in codebase:

**Known Stub Data Locations:**
1. **risk.compute_factor_exposures** (line 1086-1110 in financial_analyst.py)
   - Returns hardcoded factor exposures
   - Used by: portfolio_cycle_risk pattern (Risk Analytics page)
   - Impact: **CRITICAL USER TRUST ISSUE**

2. **macro.compute_dar** (macro_hound.py)
   - Falls back to stub data on errors
   - Used by: portfolio_cycle_risk pattern

**Search Commands:**
```bash
# Find logger.warning about fallback/stub
grep -rn "fallback" backend/app/agents/*.py
grep -rn "stub" backend/app/agents/*.py

# Find hardcoded return values
grep -rn "# HARDCODED" backend/app/agents/*.py

# Find _provenance fields indicating stub
grep -rn '"type": "stub"' backend/app/agents/*.py
```

**Report:**
- File path:line number
- Capability name
- Patterns that use it
- User impact (which UI page shows fake data)

See: REFACTORING_MASTER_PLAN.md Issue 1 for details
```

---

### Command 7: `/db-schema` - Quick Database Schema Reference

**Purpose:** Quick reference for database schema (tables, columns, relationships)

**File:** `.claude/commands/db-schema.md`

```markdown
---
description: Quick database schema reference
---

Display database schema summary:

**Core Tables:**
```bash
psql $DATABASE_URL -c "\dt" | grep -v "List of relations" | grep -v "^$"
```

**Key Tables for Development:**

**Portfolio Data:**
- `portfolios` - Portfolio definitions
- `lots` - Portfolio positions/holdings
- `portfolio_daily_values` - Historical portfolio values (**uses valuation_date**)
- `pricing_packs` - Price data snapshots

**Economic Data:**
- `economic_indicators` - Factor analysis data (series_id, asof_date, value)
- `macro_indicators` - Economic indicators config

**Reference Data:**
- `securities` - Security master data
- `currencies` - Currency reference

**Auth:**
- `users` - User accounts
- `audit_log` - Audit trail

**Common Queries:**
```bash
# Show table structure
psql $DATABASE_URL -c "\d portfolio_daily_values"

# Count rows
psql $DATABASE_URL -c "SELECT COUNT(*) FROM portfolios"

# Show recent pricing packs
psql $DATABASE_URL -c "SELECT pack_id, date FROM pricing_packs ORDER BY date DESC LIMIT 5"
```

**CRITICAL FIELD NAME:**
- ❌ `asof_date` - WRONG (code uses this)
- ✅ `valuation_date` - CORRECT (schema uses this)

See: DATABASE.md for complete schema documentation
```

---

### Command 8: `/run-migration` - Database Migration Workflow

**Purpose:** Run database migration safely

**File:** `.claude/commands/run-migration.md`

```markdown
---
description: Run database migration safely
---

Run database migration with safety checks:

**Input:** Migration file path (e.g., `backend/db/migrations/015_add_economic_indicators.sql`)

**Safety Checks:**
1. **Backup:** Create backup before migration
   ```bash
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Dry Run:** Check SQL syntax
   ```bash
   psql $DATABASE_URL -f $MIGRATION_FILE --dry-run
   ```

3. **Review:** Show migration contents
   ```bash
   cat $MIGRATION_FILE
   ```

4. **Run:** Execute migration
   ```bash
   psql $DATABASE_URL -f $MIGRATION_FILE
   ```

5. **Verify:** Check table was created
   ```bash
   psql $DATABASE_URL -c "\d table_name"
   ```

**Example: Run migration 015**
```bash
psql $DATABASE_URL -f backend/db/migrations/015_add_economic_indicators.sql
psql $DATABASE_URL -c "\d economic_indicators"
```

**Rollback:** If migration fails, restore backup
```bash
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
```

See: DATABASE.md section on migrations
```

---

## Recommended Hooks

### Hook 1: Pre-Commit Pattern Validation

**Purpose:** Validate pattern JSON files before committing

**File:** `.claude/hooks/pre-commit.json`

```json
{
  "trigger": "before_commit",
  "description": "Validate pattern JSON files before commit",
  "command": "bash",
  "args": [
    "-c",
    "for f in backend/patterns/*.json; do jq empty $f || exit 1; done && echo '✅ All patterns valid'"
  ]
}
```

**Benefit:** Catch JSON syntax errors before they reach repository

---

### Hook 2: Post-Read Context Refresh

**Purpose:** Remind to check refactoring phase status when reading key files

**File:** `.claude/hooks/post-read.json`

```json
{
  "trigger": "after_read",
  "description": "Remind to check phase status when reading refactoring plans",
  "file_patterns": [
    "COMPREHENSIVE_REFACTORING_PLAN.md",
    "PHASE_*_DETAILED_PLAN.md",
    "REFACTORING_MASTER_PLAN.md"
  ],
  "command": "echo",
  "args": [
    "💡 Tip: Run /phase-status to see current refactoring progress"
  ]
}
```

**Benefit:** Contextual reminders to check progress when reviewing plans

---

## Optional: MCP Server for Database Inspection

### MCP Server: PostgreSQL Inspection

**Purpose:** Real-time database inspection without leaving IDE

**Setup:** Install PostgreSQL MCP server

```bash
# Install MCP server (if available)
npm install -g @modelcontextprotocol/server-postgres

# Configure in Claude Code settings
# Add to mcp_servers section:
{
  "postgres": {
    "command": "mcp-postgres",
    "args": ["--connection-string", "$DATABASE_URL"]
  }
}
```

**Benefits:**
- Query database directly from IDE
- Inspect table schemas without psql
- Validate data during development

**Note:** This is optional - can continue using psql directly

---

## Implementation Priority

### Phase 1: High Priority (Implement Now)

**Must Have:**
1. ✅ `/verify-setup` - Essential for onboarding and troubleshooting
2. ✅ `/test-factor-analyzer` - **CRITICAL DECISION POINT** (saves 40h)
3. ✅ `/phase-status` - Track refactoring progress
4. ✅ `/check-stub-data` - Find user trust issues

**Estimated Setup Time:** 1-2 hours

---

### Phase 2: Medium Priority (Implement Soon)

**Should Have:**
5. ✅ `/validate-pattern` - Prevent pattern errors
6. ✅ `/fix-field-bug` - Quick access to critical bug fix
7. ✅ `/db-schema` - Database reference

**Estimated Setup Time:** 1-2 hours

---

### Phase 3: Low Priority (Implement Later)

**Nice to Have:**
8. ✅ `/run-migration` - Safe migration workflow
9. ✅ Pre-commit hook - Catch JSON errors
10. ✅ Post-read hook - Contextual reminders
11. ❓ MCP server - Database inspection (optional)

**Estimated Setup Time:** 2-3 hours

---

## Benefits Analysis

### Without Custom IDE Agents (Current State)

**Developer Experience:**
- ❌ Must remember refactoring phase order
- ❌ Must manually search for stub data
- ❌ Must manually validate patterns
- ❌ Must remember field name bug details
- ❌ Must switch to terminal for database operations
- ⚠️ Higher cognitive load
- ⚠️ More context switching

**Estimated Time Loss:** 2-3 hours/week looking up references, switching contexts

---

### With Custom IDE Agents (Recommended State)

**Developer Experience:**
- ✅ `/phase-status` shows current progress instantly
- ✅ `/check-stub-data` finds user trust issues immediately
- ✅ `/validate-pattern` catches errors before deployment
- ✅ `/test-factor-analyzer` executes critical decision quickly
- ✅ `/db-schema` shows schema without leaving IDE
- ✅ Lower cognitive load
- ✅ Less context switching

**Estimated Time Savings:** 2-3 hours/week, better focus, fewer errors

---

## Summary

**Current State:**
- ✅ Context files accurate (PROJECT_CONTEXT.md updated Nov 5)
- ✅ Permission settings working (settings.local.json)
- ❌ No custom slash commands
- ❌ No hooks
- ❌ No MCP servers

**Recommended State:**
- ✅ Keep context files (accurate, comprehensive)
- ✅ Add 8 slash commands (workflow automation)
- ✅ Add 2 hooks (quality gates)
- ❓ Consider MCP server (optional convenience)

**Implementation Effort:**
- Phase 1: 1-2 hours (critical commands)
- Phase 2: 1-2 hours (helpful commands)
- Phase 3: 2-3 hours (nice-to-haves)
- **Total: 4-7 hours** for complete setup

**ROI:**
- Time savings: 2-3 hours/week
- Error reduction: Fewer pattern validation errors, fewer field name bugs
- Better focus: Less context switching, less cognitive load
- Faster onboarding: New developers can use `/verify-setup` immediately

**Recommendation:** Implement Phase 1 commands immediately (1-2h), implement Phase 2/3 as time permits.

---

**Status:** ✅ **READY FOR IMPLEMENTATION**
