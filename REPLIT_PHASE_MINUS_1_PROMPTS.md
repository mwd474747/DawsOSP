# Replit Prompts for Phase -1 (Architecture Reconciliation)

**Date**: 2025-11-08
**Purpose**: Backend/database investigation prompts for Replit to execute
**Context**: Phase -1 of UNIFIED_REFACTOR_PLAN_V2.md requires backend/database knowledge

---

## Prompt 1: Production Database Schema Audit (Phase -1.1)

```
I need you to audit the production database schema and document what's actually there.

Execute these SQL queries against the production database and provide the results:

1. List all tables:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

2. Check if critical tables exist:
```sql
-- Does audit_log exist?
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'audit_log'
);

-- Does position_factor_betas exist?
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'position_factor_betas'
);

-- Does scenario_shocks exist?
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'scenario_shocks'
);
```

3. Verify transactions table field names:
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'transactions'
ORDER BY ordinal_position;
```

Key questions:
- Does `transaction_date` or `trade_date` exist?
- Does `transaction_type` or `action` exist?
- Does `realized_pl` or `realized_pnl` exist?

4. Verify portfolio_cash_flows table:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'portfolio_cash_flows'
ORDER BY ordinal_position;
```

Key question:
- Does `flow_date` or `trade_date` exist?

5. Check migration history:
```sql
-- If migration tracking table exists
SELECT * FROM schema_migrations ORDER BY version;

-- Or if different tracking
SELECT * FROM migrations ORDER BY id;
```

Please provide:
1. Complete list of all tables in production
2. Results of all existence checks
3. Full column list for transactions table
4. Full column list for portfolio_cash_flows table
5. Migration history if tracking table exists

Create a file called PRODUCTION_SCHEMA_AUDIT.md with these results.
```

---

## Prompt 2: Code Dependencies on Backend-Only Tables (Phase -1.2)

```
I need to check which code references tables that may have been deleted from production.

Search the codebase for references to these tables:

1. Search for audit_log references:
```bash
grep -r "audit_log" backend/app --include="*.py" -n
```

2. Search for position_factor_betas references:
```bash
grep -r "position_factor_betas" backend/app --include="*.py" -n
```

3. Search for scenario_shocks references:
```bash
grep -r "scenario_shocks" backend/app --include="*.py" -n
```

4. Check if audit.py service exists and what it does:
```bash
cat backend/app/services/audit.py 2>/dev/null || echo "audit.py does not exist"
```

For each reference found, tell me:
- File path and line number
- Whether it's a critical dependency (INSERT/UPDATE/DELETE) or just a SELECT
- Whether the code will break if the table doesn't exist

Based on the PRODUCTION_SCHEMA_AUDIT.md results:
- If audit_log DOESN'T exist in production but code references it → we need to either restore the table OR remove the code
- Same for position_factor_betas and scenario_shocks

Please provide:
1. List of all files that reference these tables
2. Severity assessment (will it break production?)
3. Recommendation: restore table OR remove code
```

---

## Prompt 3: Verify Root Server Imports (Phase -1.3)

```
I need to verify how the root combined_server.py uses the modular backend code.

1. Check imports from backend/app:
```bash
grep "from backend\.app\|from app\." combined_server.py | head -30
```

2. Check if it imports agents:
```bash
grep -i "financialanalyst\|macrohound\|dataharvester\|claudeagent" combined_server.py
```

3. Check if it imports services:
```bash
grep "from.*services" combined_server.py | head -20
```

4. Verify the orphaned backend/combined_server.py exists:
```bash
ls -lh backend/combined_server.py
wc -l backend/combined_server.py
```

5. Check .replit deployment config:
```bash
grep "combined_server" .replit
```

Please confirm:
1. Root combined_server.py DOES import from backend/app modules (yes/no)
2. Which agents/services it imports
3. Orphaned backend/combined_server.py exists and is 269 lines (yes/no)
4. .replit runs "python combined_server.py" (root version, not backend/)

This will tell us if we can safely archive the orphaned backend/combined_server.py
without losing functionality.
```

---

## Prompt 4: Check for Runtime Errors from Missing Tables (Phase -1.2)

```
Check the application logs for errors related to the tables we're investigating.

1. Check recent logs for audit_log errors:
```bash
# If using systemd/journalctl
journalctl -u dawsos --since "1 day ago" | grep -i "audit_log"

# Or if logs in file
tail -1000 /var/log/dawsos/*.log | grep -i "audit_log"

# Or check recent application output
# (provide whatever log mechanism you use)
```

2. Check for table/column errors:
```bash
# Look for SQL errors
grep -i "column.*does not exist\|table.*does not exist" <your-log-file>

# Specifically check for these errors:
# - "column 'trade_date' does not exist"
# - "table 'audit_log' does not exist"
# - "column 'action' does not exist"
```

3. Check if application is currently running and healthy:
```bash
# Check process
ps aux | grep combined_server

# Check if responding
curl -s http://localhost:5000/health || echo "Health check failed"

# Check for recent errors in logs
tail -100 <your-log-file> | grep -i "error\|exception"
```

Please provide:
1. Any errors mentioning audit_log, position_factor_betas, scenario_shocks
2. Any "column does not exist" or "table does not exist" errors
3. Current application health status
4. Any other suspicious errors in recent logs

This will show us if the database issues are actively breaking production.
```

---

## Prompt 5: Migration Files Comparison (Phase -1.2)

```
I need to compare the root migrations with backend migrations to understand conflicts.

1. List root migration files:
```bash
ls -lh migrations/*.sql
```

2. List backend migration files:
```bash
ls -lh backend/db/migrations/*.sql
```

3. Show migration 003 (the one that deletes audit_log):
```bash
cat migrations/003_*.sql 2>/dev/null || cat migrations/003*.sql 2>/dev/null || echo "Migration 003 not found"
```

4. Show backend migration 010 (the one that creates audit_log):
```bash
cat backend/db/migrations/010_*.sql 2>/dev/null || echo "Backend migration 010 not found"
```

5. Check if there's a migration tracking table:
```bash
# Run SQL query to check migration history
psql $DATABASE_URL -c "SELECT * FROM schema_migrations ORDER BY version;" 2>/dev/null || \
psql $DATABASE_URL -c "SELECT * FROM migrations ORDER BY id;" 2>/dev/null || \
echo "No migration tracking table found"
```

Please provide:
1. List of all root migration files (with dates if in filename)
2. List of all backend migration files (with dates if in filename)
3. Content of migration 003 (that deletes audit_log)
4. Content of backend migration 010 (that creates audit_log)
5. Current migration tracking table contents (which migrations were applied)

This will show us exactly which migrations were applied and where the conflict is.
```

---

## Usage Instructions

**For Replit:**

1. Execute Prompt 1 first - this gives us the production schema
2. Execute Prompts 2-5 in any order - they're independent
3. Save results to these files:
   - Prompt 1 → `PRODUCTION_SCHEMA_AUDIT.md`
   - Prompt 2 → `CODE_DEPENDENCIES_AUDIT.md`
   - Prompt 3 → `ROOT_SERVER_IMPORTS_AUDIT.md`
   - Prompt 4 → `RUNTIME_ERRORS_AUDIT.md`
   - Prompt 5 → `MIGRATION_COMPARISON_AUDIT.md`

4. Commit all audit files to git

**For Claude Code (me):**

Once Replit provides the audit results, I will:
1. Analyze the findings
2. Make decisions on Phase -1.2 (database reconciliation)
3. Execute Phase -1.3 (archive orphaned files)
4. Execute Phase -1.4 (frontend bug fixes)
5. Execute Phase -1.5 (update documentation)

---

## Expected Timeline

**Replit execution**: 30-60 minutes (mostly query time)
**Claude Code execution**: 4-8 hours (fixes + testing)
**Total Phase -1**: 8-16 hours

---

## What I'll Do While Waiting

I can execute these parts of Phase -1 immediately:

**Phase -1.4: Frontend Bug Fixes** (2-4 hours)
- Fix TokenManager.isTokenExpired export
- Fix validator HTTP method checks
- Document module load order
- Test all pages

**Phase -1.5: Update Documentation** (1-2 hours)
- Update ARCHITECTURE.md
- Create architecture diagrams
- Update README.md

These don't depend on backend/database info.
