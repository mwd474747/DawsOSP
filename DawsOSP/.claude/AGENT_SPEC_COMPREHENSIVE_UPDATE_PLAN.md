# Comprehensive Agent Spec Update Plan
## Context-Aware Design for DawsOS Roadmap

**Date**: October 27, 2025
**Purpose**: Update agent specs based on (1) recent lessons learned + (2) PRODUCT_SPEC requirements + (3) remaining roadmap work

---

## Part 1: Understanding the Complete Context

### Critical PRODUCT_SPEC Requirements (Non-Negotiable)

From comprehensive PRODUCT_SPEC review, these are **acceptance gates**:

#### 1. **ADR Pay-Date FX** (S1-W1 Gate - CRITICAL)
```
REQUIREMENT: ADR dividends MUST use pay-date FX (not ex-date FX)
ACCEPTANCE: AAPL 100 shares @ $0.24/share
  - Ex-date FX: 1.34 USD/CAD → Wrong: $32.16 CAD
  - Pay-date FX: 1.36 USD/CAD → Correct: $32.64 CAD
  - Accuracy impact: 42¢ per transaction
STATUS: ❌ NOT IMPLEMENTED (blocking)
```

#### 2. **Ledger Reconciliation** (±1bp tolerance)
```
REQUIREMENT: Beancount ledger vs DB NAV must match within ±1 basis point
ACCEPTANCE: 100% of portfolios pass ±1bp check
STATUS: ⚠️ Service exists but not verified with ADR pay-date FX
```

#### 3. **Sacred Nightly Job Order** (NON-NEGOTIABLE sequence)
```
REQUIREMENT: Jobs MUST run in this exact order:
  1. build_pack → 2. reconcile_ledger → 3. compute_daily_metrics →
  4. prewarm_factors → 5. prewarm_ratings → 6. mark_pack_fresh → 7. evaluate_alerts

BLOCKING: If reconcile_ledger fails (±1bp violated), halt all subsequent jobs
STATUS: ✅ Implemented but not tested end-to-end
```

#### 4. **Reproducibility Contract**
```
REQUIREMENT: Every result MUST include:
  - pricing_pack_id (immutable daily snapshot)
  - ledger_commit_hash (Beancount git commit)
  - asof_date (temporal anchor)
ACCEPTANCE: Same inputs → bitwise identical outputs
STATUS: ✅ Metadata structure exists
```

#### 5. **Rights Registry Enforcement**
```
REQUIREMENT: Provider rights MUST be enforced before exports
  - FMP: Display/redistribution license → attribution required
  - NewsAPI: Dev tier → metadata only (no full text)
  - Polygon: Corporate actions allowed
ACCEPTANCE: Blocked exports show clear error, allowed exports show attribution
STATUS: ⚠️ Code exists but not tested
```

#### 6. **Multi-Currency Truth Rules**
```
REQUIREMENT:
  - Valuation: P_base = P_local × FX(pack rate)
  - Returns: r_base = (1+r_local)(1+r_fx) - 1 → store local/fx/interaction separately
  - Dividends: pay-date FX for ADRs
ACCEPTANCE: Currency attribution decomposes correctly, ±0.1bp accuracy
STATUS: ⚠️ Attribution service exists but ADR pay-date FX missing
```

#### 7. **Pack Freshness Gate**
```
REQUIREMENT: Executor MUST reject requests if pack.is_fresh = false
ACCEPTANCE: HTTP 503 with "warming in progress" message
STATUS: ⚠️ Code exists (/health/pack endpoint) but not enforced in executor
```

### Remaining Roadmap Work (From TASK_INVENTORY)

#### P0 (Critical)
1. **Rights-enforced exports** - WeasyPrint PDF generation with attribution
2. **Authentication & RBAC** - JWT, role enforcement, audit logging
3. **Testing uplift** - ≥60% coverage
4. **ADR pay-date FX** - Database schema + service logic (MISSING FROM INVENTORY)

#### P1 (High)
5. **Ratings service** - Already implemented, needs UI wiring
6. **Optimizer service** - Already implemented, needs dependencies + testing
7. **Nightly job orchestration** - Already implemented, needs end-to-end testing
8. **Observability** - Already implemented (opt-in), needs Jaeger/Prometheus config

### Patterns Across Planned Work

Looking at what remains, these themes emerge:

**Theme 1: Integration Over Implementation**
- Most services are written but not wired/tested
- Need: Integration verification checklist in specs

**Theme 2: Multi-Step Dependencies**
- ADR FX → Ledger reconciliation → Nightly jobs → Production readiness
- Need: Dependency chain documentation in specs

**Theme 3: Acceptance Testing**
- Golden tests defined (AAPL dividend, ±1bp reconciliation)
- Need: Acceptance criteria linked to implementation steps

**Theme 4: Graceful Degradation**
- Many features work with stubs/seeds but not live data
- Need: Clear status taxonomy (seeded/partial/complete)

**Theme 5: System Dependencies**
- WeasyPrint needs cairo/pango, Riskfolio needs LAPACK, JWT needs secret
- Need: Prerequisites checklist before starting

---

## Part 2: Agent Spec Update Strategy

### Goals
1. **Prevent recent issues** (missing registration, stuck processes, inflated claims)
2. **Support remaining roadmap** (integration over implementation, dependencies, acceptance gates)
3. **Don't create new problems** (avoid overly rigid processes that slow down work)

### Principles for Updates

#### DO Add:
✅ **Verification checklists** - Clear, fast checks before claiming done
✅ **Integration steps** - Step-by-step wiring instructions
✅ **Common pitfalls** - Real examples from recent work
✅ **Acceptance criteria** - Link to PRODUCT_SPEC requirements
✅ **Dependency checks** - Prerequisites before starting
✅ **Definition of done** - Clear states (seeded/partial/complete)

#### DON'T Add:
❌ **Excessive bureaucracy** - No 20-step checklists for simple tasks
❌ **Duplicate guidance** - Don't repeat what's in PRODUCT_SPEC
❌ **Technology-specific details** - Keep general, link to detailed docs
❌ **Overly prescriptive** - Allow flexibility in approach
❌ **Discouraging language** - Focus on "how to succeed" not "how you'll fail"

---

## Part 3: Spec-by-Spec Update Plan

### ORCHESTRATOR.md (Master Coordinator)

**Current Issues**: No verification, no cleanup, claims "operational" when partial

**Add Sections**:

1. **Session Checklist** (at top, after Mission)
```markdown
## Before Starting Any Work

### Check Current State
- [ ] Kill any stuck processes: `killall -9 python python3 uvicorn`
- [ ] Verify clean: `ps aux | grep uvicorn` returns nothing
- [ ] Check git status: All previous work committed
- [ ] Review TASK_INVENTORY: Understand what's actually next

### After Completing Work
- [ ] Kill background processes (mandatory)
- [ ] Verify integration (not just files created)
- [ ] Document actual status (seeded/partial/complete)
- [ ] Commit with accurate message (no inflated claims)
```

2. **Status Taxonomy** (replace current status legend)
```markdown
## Status Definitions (Use Accurately)

- **✅ Complete**: Tested end-to-end, acceptance criteria met
- **⚠️ Partial**: Code exists, integration incomplete OR dependencies missing
- **🔧 Seeded**: Works with test data, not live providers
- **🚧 Planned**: Spec only, no code
- **❌ Blocked**: Dependency or blocker prevents work

**Examples**:
- ratings_agent.py exists + registered + tested with FMP = ✅ Complete
- ratings_agent.py exists + NOT registered = ⚠️ Partial
- ratings work with seed data only = 🔧 Seeded
```

3. **Critical Requirements Tracker** (link to PRODUCT_SPEC)
```markdown
## PRODUCT_SPEC Critical Requirements

### S1-W1 Gates (Blocking Production)
- [ ] ADR pay-date FX (transactions.pay_date, pay_fx_rate_id)
- [ ] Ledger reconciliation ±1bp (100% portfolios pass)
- [ ] Pack freshness gate (/health/pack enforced in executor)
- [ ] Rights enforcement (exports blocked/attributed correctly)

### Sacred Invariants (Never Violate)
- [ ] Nightly job order preserved (build→reconcile→metrics→prewarm→mark→alerts)
- [ ] Reproducibility metadata (pricing_pack_id + ledger_commit_hash in all results)
- [ ] Multi-currency truth (pay-date FX for ADRs, pack FX for valuation)
- [ ] Single execution path (UI→Executor→Pattern→Agent→Service, no shortcuts)
```

4. **Integration Verification**
```markdown
## Verify Before Claiming Complete

### Quick Integration Check (5 min)
```bash
# 1. Application starts
cd backend && ./run_api.sh &
sleep 10
curl http://localhost:8000/health  # Expect: 200 OK

# 2. Agents registered
python3 -c "
from app.api.executor import get_agent_runtime
runtime = get_agent_runtime()
print(f'Agents: {list(runtime.agents.keys())}')
print(f'Total capabilities: {sum(len(a.get_capabilities()) for a in runtime.agents.values())}')
"
# Expect: List of agents, capability count

# 3. Cleanup
killall python3
```

### Pattern Execution Check (if applicable)
```bash
# Execute relevant pattern with test data
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"pattern_id":"portfolio_overview","inputs":{"portfolio_id":"11111111-1111-1111-1111-111111111111"}}'

# Verify: Result contains real data (not stubs or errors)
```
```

**Don't Add**: Excessive process steps, duplicate PRODUCT_SPEC content

---

### Implementation Agent Specs (RATINGS, OPTIMIZER, REPORTING, etc.)

**Standard Additions for ALL Implementation Specs**:

1. **Prerequisites** (before starting, 2-3 min check)
```markdown
## Before Starting

### Check Dependencies
```bash
# System libraries (if needed)
[specific commands for this agent]

# Python packages
python3 -c "import required_package" 2>/dev/null && echo "✅" || echo "❌ MISSING"

# Database state
psql -U dawsos_app -d dawsos -c "SELECT COUNT(*) FROM required_table"
```

### Expected State
- Database: [tables that must exist]
- Seeds: [data that must be loaded]
- Config: [environment variables needed]

### If Missing
Document in implementation report: "⚠️ Dependencies not met, using graceful fallback"
```

2. **Step-by-Step** (implementation + integration)
```markdown
## Implementation Steps

### Phase 1: Service (Est: X hours)
- [ ] Create backend/app/services/[name].py
- [ ] Implement methods: [list]
- [ ] Add graceful fallback for missing dependencies
- [ ] Test syntax: `python3 -m py_compile service_file.py`

### Phase 2: Agent (Est: X hours)
- [ ] Create backend/app/agents/[name]_agent.py
- [ ] Declare capabilities in get_capabilities()
- [ ] Implement agent methods (capability.dots → method_underscores)
- [ ] Test syntax: `python3 -m py_compile agent_file.py`

### Phase 3: Registration (Est: 15-30 min) ⚠️ CRITICAL
- [ ] Edit backend/app/api/executor.py
- [ ] Add import: `from app.agents.[name]_agent import [Name]Agent`
- [ ] Instantiate: `[name]_agent = [Name]Agent("[name]", services)`
- [ ] Register: `_agent_runtime.register_agent([name]_agent)`
- [ ] Update count: `logger.info("... N agents")` (update number)
- [ ] **VERIFY**: `grep register_agent executor.py | wc -l` (count increased)

### Phase 4: Verification (Est: 30-60 min)
- [ ] Start application cleanly (no errors)
- [ ] Check agent in runtime: [verification command]
- [ ] Test with pattern: [pattern_id to test]
- [ ] Verify real data (not stubs): [how to check]
```

3. **Acceptance Criteria** (link to PRODUCT_SPEC when applicable)
```markdown
## Done When

### Minimum Viable
- ✅ Service compiles and loads
- ✅ Agent registered in executor
- ✅ Application starts without errors
- ✅ At least one capability returns data (stub or real)

### Seeded Complete
- ✅ All above +
- ✅ Works with test/seed data
- ✅ Graceful fallback for missing dependencies
- ✅ Documentation notes limitations

### Fully Complete
- ✅ All above +
- ✅ Works with live provider data
- ✅ PRODUCT_SPEC acceptance criteria met (if applicable)
- ✅ End-to-end pattern execution verified

### PRODUCT_SPEC Links
[Link to specific requirements this agent must satisfy]
```

4. **Common Pitfalls** (from recent experience)
```markdown
## Avoid These Mistakes

### Integration Failures
⚠️ **Agent not registered**: Most common issue
  - Symptom: "No agent for capability X" despite agent file existing
  - Fix: Add 3 lines to executor.py (import, instantiate, register)
  - Prevention: Always do Phase 3 immediately after Phase 2

⚠️ **Import path wrong**: Second most common
  - Symptom: ModuleNotFoundError when starting app
  - Fix: Verify path matches actual file location
  - Prevention: Test import before claiming done

### Claiming Done Too Early
⚠️ **"It should work" ≠ "It works"**
  - Don't claim complete without starting application
  - Don't claim complete without testing at least one capability
  - Partial progress is OK - be honest about status

### Background Processes
⚠️ **Stuck processes accumulate**
  - Always kill processes: `killall -9 python3 uvicorn`
  - Verify clean: `ps aux | grep uvicorn` returns nothing
  - Do this BEFORE starting app AND after finishing work
```

---

### CORPORATE_ACTIONS_ARCHITECT.md (Special: ADR Pay-Date FX)

**This spec needs special attention** - it covers the S1-W1 gate requirement that's currently missing.

**Add Prominent Section at Top**:

```markdown
## ⚠️ CRITICAL: ADR Pay-Date FX (S1-W1 Gate)

### PRODUCT_SPEC Requirement (Non-Negotiable)
ADR dividends MUST use pay-date FX rate, NOT ex-date FX rate.

### Why It Matters
- Accuracy impact: ~42¢ per $24 dividend (with 1.34 vs 1.36 FX rate)
- Financial accuracy: Critical for multi-currency portfolios
- Acceptance gate: Required before S1-W1 completion

### Implementation Requirements

1. **Database Schema** (MUST DO FIRST)
```sql
-- Add to transactions table
ALTER TABLE transactions ADD COLUMN pay_date DATE;
ALTER TABLE transactions ADD COLUMN pay_fx_rate_id UUID REFERENCES fx_rates(id);

-- Enforce constraint
ALTER TABLE transactions ADD CONSTRAINT dividend_pay_fx CHECK (
    NOT(type IN ('dividend','coupon') AND pay_fx_rate_id IS NULL)
);
```

2. **Service Logic** (corporate_actions.py or ledger.py)
```python
async def record_dividend(
    portfolio_id: UUID,
    security_id: UUID,
    ex_date: date,
    pay_date: date,
    amount_per_share: Decimal,
    currency: str
):
    """
    CRITICAL: Use pay_date FX for ADR dividends.
    """
    # Fetch FX rate for PAY DATE (not ex-date)
    pay_fx_rate = await get_fx_rate(currency, base_ccy="CAD", asof_date=pay_date)

    # Convert using pay-date FX
    amount_base = amount_per_share / pay_fx_rate

    # Store transaction with pay_fx_rate_id
    await db.execute("""
        INSERT INTO transactions (portfolio_id, security_id, type, ex_date, pay_date,
                                  amount_ccy, amount_base, pay_fx_rate_id, ...)
        VALUES ($1, $2, 'dividend', $3, $4, $5, $6, $7, ...)
    """, portfolio_id, security_id, ex_date, pay_date,
         amount_per_share, amount_base, pay_fx_rate.id)
```

3. **Golden Test** (tests/golden/multi_currency/adr_paydate_fx.json)
```json
{
  "symbol": "AAPL",
  "shares": 100,
  "dividend_per_share": 0.24,
  "ex_date": "2024-08-01",
  "pay_date": "2024-08-15",
  "ex_date_fx_usd_cad": 1.34,
  "pay_date_fx_usd_cad": 1.36,
  "expected_cad": 32.64,
  "wrong_if_ex_date": 32.16,
  "accuracy_impact": 0.48
}
```

4. **Acceptance Criteria**
- [ ] Schema migration applied (pay_date, pay_fx_rate_id columns exist)
- [ ] Constraint enforced (dividend without pay_fx_rate_id fails)
- [ ] Golden test passes (AAPL dividend = $32.64 CAD, not $32.16)
- [ ] Ledger reconciliation passes ±1bp with ADR dividends

### Status Tracking
- [ ] Schema changes
- [ ] Service implementation
- [ ] Golden test created
- [ ] Test passes
- [ ] Documentation updated

### Why This is S1-W1 Gate
This is NOT optional. ADR pay-date FX is a financial accuracy requirement that affects
every multi-currency portfolio with U.S. securities. It's the difference between correct
and incorrect accounting.
```

---

## Part 4: Update Process

### Step 1: ORCHESTRATOR.md (30 min)
- Add session checklist
- Add status taxonomy
- Add critical requirements tracker
- Add integration verification
- Keep concise - link to other specs for details

### Step 2: Create AGENT_SPEC_TEMPLATE.md (45 min)
- Standard sections all implementation specs should have
- Prerequisites, step-by-step, acceptance criteria, pitfalls
- Can be copied/adapted for each spec

### Step 3: Update Implementation Specs (2-3 hours)
Priority order (based on remaining roadmap):
1. CORPORATE_ACTIONS_ARCHITECT (ADR pay-date FX - critical)
2. RATINGS_ARCHITECT (needs UI wiring guidance)
3. OPTIMIZER_ARCHITECT (needs dependency verification)
4. REPORTING_ARCHITECT (needs agent registration warning)
5. SECURITY_ARCHITECT (needs migration verification)
6. TEST_ARCHITECT (needs "run tests" requirement)
7. Others as time permits

### Step 4: Verification (30 min)
- Read through updated specs
- Check for:
  - Duplication (remove if found)
  - Over-specification (simplify if found)
  - Missing context (add PRODUCT_SPEC links)
  - Discouraging language (reframe positively)

### Step 5: Trial Run (optional, 1-2 hours)
- Pick small task from roadmap
- Follow updated spec exactly
- Document what works / what doesn't
- Refine based on experience

---

## Part 5: Guardrails

### What Makes a Good Update

✅ **Concise**: Each section < 20 lines
✅ **Actionable**: Clear commands to run, not just concepts
✅ **Linked**: Reference PRODUCT_SPEC, don't duplicate it
✅ **Proven**: Based on actual failures from recent work
✅ **Positive**: "Here's how to succeed" not "here's how you'll fail"

### What to Avoid

❌ **Too Detailed**: Don't document every possible edge case
❌ **Too Generic**: Must be specific to DawsOS context
❌ **Too Rigid**: Allow flexibility in implementation approach
❌ **Too Discouraging**: Don't make it sound impossible
❌ **Duplicate Content**: Link to other docs, don't repeat them

### Balance Point

The goal is specs that:
- **Prevent issues we've seen** (missing registration, no testing, inflated claims)
- **Support remaining work** (ADR FX, integration, acceptance criteria)
- **Don't slow progress** (fast checklists, not bureaucracy)

---

## Part 6: Success Metrics

### How We'll Know Updates Worked

**After Next Implementation Task**:
- ✅ Agent registered in executor (not forgotten)
- ✅ Application tested before claiming done (not assumed)
- ✅ Status accurately reported (seeded/partial/complete, not "100% ready")
- ✅ Background processes cleaned up (no accumulation)
- ✅ Dependencies checked before starting (not discovered during)
- ✅ Acceptance criteria linked to PRODUCT_SPEC (not invented)

**What We DON'T Want**:
- ❌ Agent not registered despite spec update (spec too buried)
- ❌ Still claiming done without testing (spec not clear enough)
- ❌ Updates create new friction (over-specified)
- ❌ Updates ignored as too long (too much text)

---

## Part 7: Implementation Timeline

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| **Research** | Read PRODUCT_SPEC, identify patterns | DONE | - |
| **Planning** | Create update plan (this doc) | DONE | - |
| **ORCHESTRATOR** | Add session checklist, status taxonomy | 30 min | HIGH |
| **Template** | Create standard spec sections | 45 min | HIGH |
| **CORPORATE_ACTIONS** | Add ADR pay-date FX (S1-W1 gate) | 45 min | CRITICAL |
| **Other Specs** | Update 5-6 implementation specs | 2-3 hours | MEDIUM |
| **Verification** | Review for quality, conciseness | 30 min | HIGH |
| **TOTAL** | | **4-5 hours** | |

---

## Conclusion

This update plan is comprehensive but focused:

1. **Addresses recent failures** (registration, testing, claims)
2. **Supports remaining roadmap** (ADR FX, integration, acceptance)
3. **Links to PRODUCT_SPEC** (S1-W1 gates, sacred invariants)
4. **Stays practical** (fast checklists, not bureaucracy)
5. **Proven from experience** (based on actual issues)

The updates will make specs more useful WITHOUT making them overwhelming.

**Next**: Execute update plan, starting with ORCHESTRATOR.md and CORPORATE_ACTIONS_ARCHITECT.md (ADR pay-date FX critical requirement).

---

**Created**: October 27, 2025
**Purpose**: Context-aware agent spec updates that support faithful roadmap implementation
**Outcome**: Better guidance without new problems
