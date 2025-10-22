# DawsOS — **Codex Governance v1.0**

**Scope:** Use of Codex (and similar coding copilots in VS Code) on top of Claude-as-Implementor
**Date:** 2025-10-21 • **Owner:** Mike (“portfolio-first, truth-first”)

> Purpose: make Codex a **force multiplier** for speed **without** allowing complexity creep, architectural drift, or compliance gaps. Codex is a *constrained assistant* that writes/refactors/tests **within guardrails**; Claude remains the planning/implementing “source of truth”.

---

## 0) First Principles (non-negotiable)

1. **No Drift**: Codex code must comply with the master spec (PRODUCT_SPEC.md) and the guardrails defined in PRODUCT_SPEC.md §“Guardrails”.
2. **Single Path**: UI → `/execute` → Pattern Orchestrator → Agents → Services → Data. No UI→provider or UI→DB calls, ever.
3. **Truth Spine**: Pack immutability + freshness gate; Beancount-first accounting; RLS enforced.
4. **Compliance**: Rights registry enforced for **every** export; attributions appended; watermark/block when required.
5. **Multi-Currency**: Trade FX (lots), Pack FX (valuation), Pay-date FX (dividends). Never mix these.
6. **Reproducibility**: Add/keep `pricing_pack_id` + `ledger_commit_hash` in any Result/PDF you touch.
7. **Observability**: OTel traces & Prom metrics for changed code; don’t merge if SLO histograms regress.

---

## 1) Roles & RACI for Codex

* **Codex (contributor)**: Proposes diffs, tests, docs, infra; *cannot* introduce new architecture/dependencies/flows.
* **Claude (implementor)**: Owns design intent, agents/patterns, and acceptance gates.
* **ORCHESTRATOR (human)**: Approves scope; blocks drift; owns ADR decisions.
* **Layer Architects (human)**: Review diffs in their domain (providers/macro/ratings/optimizer/ui/ops).
* **QA/SET, SRE (human)**: Enforce CI gates; run chaos, perf, rights, RLS fuzz.

---

## 2) Allowed vs Disallowed (Codex)

**Allowed**

* Implement capabilities already accepted (e.g., `macro.scenario_apply`, `ratings.dividend_safety`).
* Write/expand tests (unit, property, golden, chaos, RLS fuzz, visual).
* Refactor for purity/typing/observability; reduce duplication.
* Generate migrations for **already-approved** schema changes (with up/down).
* Infra: Terraform/Helm/ECS for **declared** components; no new provider services.

**Disallowed**

* New dependencies or external APIs.
* Direct provider calls from UI or patterns (must go via services facades).
* DB schema changes **without** an ADR & migration pair.
* Export paths without `rights.ensure_allowed()`.
* Disabling RLS, freshness gate, or guardrails even “temporarily”.
* Any change that increases cyclomatic complexity beyond budget (see §6).

---

## 3) Codex Working Modes (choose explicitly)

1. **Linter/Refactor Mode**

   * Goal: purity, typing, small complexity reductions, docstrings, OTel spans.
   * Diff budget: ≤ 200 LOC; no new deps.

2. **Test Writer Mode**

   * Goal: increase coverage; add property/golden/chaos/RLS tests; seed fixtures.
   * Must run tests locally and update CI config if needed.

3. **Scaffold Mode**

   * Goal: generate code from agent contracts/pattern specs **already approved**.
   * Must reference DTOs & acceptance tests; provide a single multi-file diff.

4. **Infra Mode**

   * Goal: Terraform/Helm/ECS changes from approved infra plan; no new cloud services.

5. **Seed Sync Mode**

   * Goal: reconcile seeds documented in `DawsOS_Seeding_Plan` with tests/patterns (schema_version/method_version).

> Codex **cannot** switch modes mid-task. Each PR declares its mode.

---

## 4) Required Context Pack (attach before using Codex)

* `/PRODUCT_SPEC.md` (current version; see §“Guardrails” for architectural rules)
* `.claude/CLAUDE_CODE_GUIDE.md` (prompt guardrails + implementation workflows)
* Relevant **Agent spec** (.claude/agents/**) for the change
* **DTOs** (`/backend/app/dto/*.py`)
* **Seeds** (`DawsOS_Seeding_Plan`) and **tests** (`/tests/**`)
* **Makefile** + CI config
* For infra: `.claude/agents/infrastructure/INFRASTRUCTURE_ARCHITECT.md` and staging tfvars/values as declared there

---

## 5) Prompt Patterns (safe & reproducible)

**Small refactor**

> “Refactor `/backend/app/services/metrics.py` to ensure `currency_attribution` is pure. Keep DTOs unchanged, add typing & docstrings, emit OTel spans, and add `tests/unit/test_metrics_currency.py` with property tests (`r_base≈(1+r_local)(1+r_fx)-1`). Return a single multi-file diff. Do not modify any other modules.”

**Capability implementation**

> “Using `.claude/agents/analytics/MACRO_ARCHITECT.md` and the macro cycle seeds described in `DawsOS_Seeding_Plan`, implement `cycles.compute_short_term/long_term/empire` under `/backend/app/services/cycles.py`. Add integration tests in `/tests/integration/test_macro_cycles.py` seeded from snapshots. No new deps, no changes outside these paths. Provide one diff.”

**Rights enforcement**

> “Wire `reports.ensure_allowed()` into `/backend/app/services/reports.py` and add tests in `/tests/rights/test_reports_rights.py`: block Polygon/FMP-only exports or watermark per registry; append attributions for allowed providers. Single diff; no other files.”

**Freshness gate**

> “Implement pack freshness gate in `/backend/app/main.py` using `packs.is_fresh(pack_id)`. Add `/backend/app/services/packs.py::status()` and `/tests/integration/test_pack_health.py`. One diff.”

---

## 6) Complexity Budget & Drift Checks

* **Diff budget**: default ≤ 300 LOC changed; > 300 requires ORCHESTRATOR pre-approval.
* **Cyclomatic complexity**: no function > 10 (flake8-complexity).
* **New files**: ≤ 5 per PR unless scaffolding a new, approved capability.
* **No deps**: PR adding dependencies auto-closed unless approved via ADR.

**Automated Drift Scans (pre-commit & CI)**

* **UI** importing `requests`/`httpx` → **block** (UI→provider drift).
* Export functions without `rights.ensure_allowed()` → **block**.
* Missing `pricing_pack_id`/`ledger_commit_hash` in Result/PDF code paths → **warn**.
* SQL without RLS predicate in portfolio-scoped tables → **block**.
* Disable/alter pack freshness gate → **block**.

---

## 7) PR Template (must fill)

```markdown
## Codex Mode
- [ ] Linter/Refactor
- [ ] Test Writer
- [ ] Scaffold (approved capability)
- [ ] Infra
- [ ] Seed Sync

## Linked Specs
- PRODUCT_SPEC.md §... (include §“Guardrails”)
- .claude/CLAUDE_CODE_GUIDE.md §...
- AGENT spec: .../AGENT_NAME.md

## Scope (max 3 bullets)
- ...

## Acceptance (tick all)
- [ ] No new deps
- [ ] Single execution path untouched
- [ ] Freshness gate preserved
- [ ] Rights gate enforced (if export path)
- [ ] RLS unchanged; IDOR fuzz passes
- [ ] OTel spans added for new code
- [ ] Tests added/updated (list)
- [ ] Seeds updated (if applicable), with schema_version/method_version

## Complexity
- Files changed: N
- LOC delta: N
- Max cyclomatic complexity: N (≤ 10)

## Results
- p95 (warm): ... ms
- Tests: unit N, integration N, golden N, chaos N, rls N, visual N

## Rollback
- Migration up/down paths (if any)
- Kill switch / feature flag
```

---

## 8) CI Gates (merge-only-on-green)

* **Lint/Type**: ruff/black/isort/mypy
* **Unit**: new/affected modules (≥ 80% coverage)
* **Property**: currency identity/triangulation
* **Golden**: Beancount ± 1 bp (includes ADR pay-date FX)
* **Integration**: pattern runs + freshness gate behavior
* **Rights**: export drills (block/watermark)
* **Security**: RLS/IDOR fuzz; SAST/SCA; no secrets committed
* **Chaos**: provider outage, Redis restart; DLQ replay
* **Visual** (if UI): Playwright snapshots stable
* **Perf Smoke**: API p95 histograms not regressing

Any red → no merge. Codex changes must include fixes or revert.

---

## 9) Observability & Performance Rules

* Add OTel spans around **each capability**; tag with `pattern_id`, `pricing_pack_id`, `ledger_commit_hash`.
* Export Prom histograms: API latency by pattern; pack durations; queue depth; DLQ size; alert latency.
* Don’t merge if warm p95 > 1.2 s on staging for affected endpoints.

---

## 10) Security & Compliance Rules

* No PII in logs/trace/error bodies.
* RLS in effect; any direct SQL must document the RLS predicate.
* Rights: block/watermark per registry; attributions present; export tests mandatory.
* Secrets from vault/env only (never in repo).
* Threat model assumptions not weakened in code.

---

## 11) ADR Triggers (Codex must not proceed without ADR)

* DB schema change (table/column/index semantics).
* Pattern JSON **schema change** or removal of fields.
* Rights policy changes or export logic changes.
* FX policy (pack policy, pay-date FX) changes.
* Benchmark or hedging methodology changes.
* Macro cycle definitions/weights/boundary edits.

---

## 12) Anti-patterns (stop immediately)

* “I simplified by calling the provider directly in the UI.” → **Reject PR**.
* “I inlined the rights check to speed things up.” → **Reject PR**.
* “I removed the pack freshness gate because it blocked my dev tests.” → **Reject PR**.
* “I added a small dependency to do X.” → **ADR first**; otherwise **Reject PR**.
* “I merged tests later.” → **Reject PR**; tests are part of the change.

---

## 13) Example “good” & “bad” prompts

**Good**

> “Use `.claude/agents/business/RATINGS_ARCHITECT.md`. Implement `ratings.resilience` using existing DTOs; keep method tag `resilience_v1`; add unit tests with seeded fundamentals; do not add dependencies; single multi-file diff.”

**Bad**

> “Write me a new ratings engine and wire it everywhere.” (scope creep, drift)

---

## 14) Governance Audits (weekly)

* Randomly sample 3 Codex PRs:

  * Check complexity deltas, RLS predicates, rights enforcement, freshness gate, observability, tests.
  * Track “Compliance Score” (0–100).
* If score < 90 → require remediation tasks next sprint (tests/observability/rights/FX correctness).

---

## 15) Kill Switches

* **Feature Flags**: any new pattern/service must be flag-gated.
* **Rollback**: migrations must include down scripts; PR includes rollback steps.
* **Disable Copilot/Codex**: if repeated drift violations, temporarily disable for the repo until audits pass.

---

## 16) Quick Reference (short table)

| Guardrail       | Check                                                    |
| --------------- | -------------------------------------------------------- |
| Single path     | No UI `requests`/`httpx`; patterns use capabilities only |
| Freshness       | `/execute` checks `packs.is_fresh()`                     |
| Rights          | `reports.ensure_allowed()` present; export tests pass    |
| RLS             | `SET LOCAL app.user_id`; IDOR fuzz green                 |
| FX truth        | lots.trade_fx, pack FX valuation, dividends pay-date FX  |
| Reproducibility | Results have `pricing_pack_id` + `ledger_commit_hash`    |
| Observability   | OTel spans present; Prom histograms updated              |
| Complexity      | LOC ≤ 300, cyclomatic ≤ 10, no new deps                  |

---

### Final note

Codex is **not** an architect; it is a **code assistant under governance**. If you keep it in these lanes—tight prompts, scoped diffs, test-first, and merge-only-on-green—you’ll get the speed without the drift, and you’ll keep the DawsOS spine (ledger + pack + patterns) intact and defensible.
