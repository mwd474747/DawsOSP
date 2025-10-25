# Development Guardrails for AI Assistants

**Created**: 2025-10-24
**Purpose**: Prevent bypassing application intent and ensure root cause fixes

---

## 🚨 MANDATORY CHECKS BEFORE ANY CODE CHANGE

### 1. Data Integrity Check (ALWAYS FIRST)

Before fixing any "bug", verify the data layer is complete:

```bash
# Run this checklist for EVERY error:

# 1. Check pricing pack status
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c \
  "SELECT id, date, status, is_fresh, prewarm_done FROM pricing_packs WHERE id = 'PP_2025-10-21'"

# 2. Verify prices exist for ALL portfolio securities
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c \
  "SELECT COUNT(*) FROM prices WHERE pricing_pack_id = 'PP_2025-10-21'"

# 3. Check security ID alignment (lots vs prices)
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c \
  "SELECT l.security_id, s.symbol,
   EXISTS(SELECT 1 FROM prices p WHERE p.security_id = l.security_id AND p.pricing_pack_id = 'PP_2025-10-21') as has_price
   FROM lots l
   JOIN securities s ON l.security_id = s.id
   WHERE l.portfolio_id = '11111111-1111-1111-1111-111111111111'"

# 4. Verify metrics computed
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c \
  "SELECT COUNT(*) FROM portfolio_metrics WHERE portfolio_id = '11111111-1111-1111-1111-111111111111'"
```

**RULE**: If ANY of the above return 0 rows or is_fresh=false, **DO NOT FIX CODE**. Fix seed data first.

---

### 2. Sacred Job Chain Verification

Per PRODUCT_SPEC.md line 64:
> `build_pack → reconcile_ledger → compute_daily_metrics → prewarm_factors → mark_pack_fresh → evaluate_alerts`

Before testing ANY capability:

```bash
# Verify job chain completion
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c \
  "SELECT
    id,
    status,
    is_fresh,
    prewarm_done,
    reconciliation_passed,
    reconciliation_error_bps
   FROM pricing_packs
   WHERE id = 'PP_2025-10-21'"
```

**Expected**:
- `status = 'fresh'`
- `is_fresh = true`
- `prewarm_done = true`
- `reconciliation_passed = true`
- `reconciliation_error_bps < 1.0` or NULL

**RULE**: If job chain incomplete, run jobs. Do NOT mock/stub data.

---

### 3. Execution Path Compliance

Per PRODUCT_SPEC.md Guardrail #1:
> "Single path: UI → Executor API → Pattern Orchestrator → Agents → Services → Data"

**FORBIDDEN**:
- ❌ Direct database queries from UI
- ❌ Bypassing pattern orchestrator
- ❌ Mocking services with placeholder data
- ❌ Hardcoding portfolio_id/pack_id in agents

**REQUIRED**:
- ✅ All inputs via pattern JSON `{{inputs.X}}`
- ✅ All context via `ctx.pricing_pack_id`, `ctx.asof_date`
- ✅ All results include `_metadata` with `pricing_pack_id`

---

### 4. Reproducibility Contract

Per PRODUCT_SPEC.md Guardrail #2:
> "every Result includes `pricing_pack_id` + `ledger_commit_hash`"

**Before accepting any agent result as "working"**:

```python
# Verify metadata structure
result = {
    "data": {...},
    "_metadata": {
        "pricing_pack_id": "PP_2025-10-21",  # REQUIRED
        "ledger_commit_hash": "abc123",      # REQUIRED
        "asof": "2025-10-21",                # REQUIRED
        "source": "service_name:PP_2025-10-21"
    }
}
```

**RULE**: If metadata missing or null, fix metadata attachment, NOT the data.

---

### 5. Error Classification

When encountering an error, classify FIRST:

#### Type A: Missing Data (FIX DATA, NOT CODE)
- "No price for security_id X in pack Y"
- "No metrics found for portfolio Z"
- "invalid input syntax for type uuid: ''"
- "Pricing pack not found"

**Action**: Run seed loader + job chain, retest

#### Type B: Schema Mismatch (FIX CODE)
- "column 'asof_date' does not exist" (should be 'date')
- "relation 'base_ccy' does not exist" (should be 'base_currency')

**Action**: Update service queries to match actual schema

#### Type C: Logic Error (FIX CODE)
- "Agent X not registered for capability Y"
- "Pattern validation failed"
- "Method signature mismatch"

**Action**: Fix agent registration or method implementation

**RULE**: 90% of errors in testing are Type A. Always check data BEFORE changing code.

---

### 6. The "Why Is This Broken?" Decision Tree

```
Error encountered
    │
    ├─ Is pricing_pack is_fresh=true? ──NO──> Run job chain, retest
    │                                          STOP
    ├─ Do prices exist for ALL securities? ──NO──> Fix seed data, rebuild pack
    │                                               STOP
    ├─ Do metrics exist in DB? ──NO──> Run compute_daily_metrics job
    │                                   STOP
    ├─ Does schema match code? ──NO──> Update code to match schema
    │                                   (Schema is truth, code follows)
    ├─ Is capability registered? ──NO──> Register agent capability
    │
    └─ NOW you can debug business logic
```

**RULE**: Follow tree top-to-bottom. Do NOT skip to bottom.

---

### 7. Seed Data Completeness Checklist

Before running ANY pattern test:

```bash
# MANDATORY: Verify ALL seed domains loaded
python scripts/seed_loader.py --verify

# Expected output:
# ✅ Securities: 10 rows
# ✅ Portfolios: 1 rows
# ✅ Lots: 3 rows
# ✅ Transactions: 5 rows
# ✅ Pricing packs: 1 rows
# ✅ Prices: 30 rows (10 securities × 3 packs)
# ✅ FX rates: 6 rows
# ✅ Macro data: 27 rows
# ✅ Cycles: 3 rows
```

If `--verify` doesn't exist, create it.

**RULE**: Zero shortcuts. If seed data incomplete, you're testing against air.

---

### 8. Test After Job Chain, Not After Seed Load

**WRONG Workflow**:
```bash
python scripts/seed_loader.py --domain portfolios
curl POST /v1/execute  # ❌ Data exists but not reconciled/computed
```

**CORRECT Workflow**:
```bash
# 1. Load base data
python scripts/seed_loader.py --all

# 2. Run job chain (or verify it auto-ran)
python backend/jobs/build_pricing_pack.py --date 2025-10-21
python backend/jobs/reconcile_ledger.py --pack-id PP_2025-10-21
python backend/jobs/metrics.py --pack-id PP_2025-10-21

# 3. Verify pack fresh
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c \
  "SELECT is_fresh FROM pricing_packs WHERE id = 'PP_2025-10-21'"
# Must return: is_fresh = t

# 4. NOW test patterns
curl POST /v1/execute
```

**RULE**: If `is_fresh=false`, you're testing unfinished data.

---

### 9. Logging != Debugging

**I violated this by**:
- Adding 10+ logger.info() statements
- Restarting backend 6+ times
- Not seeing logs (log level filtered)
- Continuing to debug code instead of checking data

**CORRECT Approach**:
```bash
# 1. Check data FIRST
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c "SELECT ..."

# 2. If data is wrong, logs don't matter
# 3. If data is right, THEN add ONE strategic log line
# 4. If log doesn't appear, check log level config, not code
```

**RULE**: Logs are for production observability, not for compensating for missing test data.

---

### 10. "End Product Vision" Sanity Check

Before every code change, ask:

**Question**: "In production, would this data/state exist?"

**Examples**:
- ❌ "Portfolio has no prices" → Would never happen in prod (job chain runs nightly)
- ❌ "Metrics table empty" → Would never happen in prod (computed daily)
- ❌ "Security IDs mismatched" → Would never happen in prod (seed consistency enforced)
- ✅ "Column name changed" → Could happen (schema evolution)
- ✅ "Agent not registered" → Could happen (deployment issue)

**RULE**: If the error state is impossible in production, fix test environment, not code.

---

## 📋 Pre-Change Checklist Template

Copy this for EVERY code change:

```markdown
## Change Proposal: [Brief description]

### 1. Data Verification
- [ ] Pricing pack is_fresh = true
- [ ] All securities have prices
- [ ] All portfolios have metrics
- [ ] Job chain completed successfully

### 2. Error Classification
- [ ] Type: [ ] Missing Data  [ ] Schema Mismatch  [ ] Logic Error
- [ ] Root cause identified (not symptom)

### 3. Execution Path Compliance
- [ ] Change maintains single execution path
- [ ] No UI → DB shortcuts
- [ ] Pattern orchestration preserved

### 4. Reproducibility
- [ ] Result includes pricing_pack_id
- [ ] Result includes ledger_commit_hash
- [ ] Metadata properly attached

### 5. Production Realism
- [ ] Error state could occur in production
- [ ] Fix applies to production scenario
- [ ] Not just making test pass

### 6. Alternatives Considered
- [ ] Checked if seed data incomplete
- [ ] Checked if job chain not run
- [ ] Verified schema matches reality
```

---

## 🎯 Summary: The Golden Rule

**"If the data were complete and the job chain had run, would this error still exist?"**

- **NO** → Fix data/jobs, not code
- **YES** → Proceed with code fix

---

**Last Updated**: 2025-10-24
**Enforcement**: MANDATORY for all AI assistant sessions
