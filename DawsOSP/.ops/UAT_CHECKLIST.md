# DawsOS User Acceptance Testing (UAT) Checklist

**Purpose**: Production readiness validation with Go/No-Go criteria
**Environment**: Staging (anonymized prod snapshot + real provider APIs)
**Updated**: 2025-10-21
**Priority**: P0 (Blocks production deployment)

---

## Go/No-Go Decision Framework

### **GO Criteria** (All must pass)
- ✅ All Critical (P0) tests pass (100% success rate)
- ✅ ≥ 95% High (P1) tests pass
- ✅ No data corruption in any scenario
- ✅ All SLOs met in staging environment
- ✅ Product owner sign-off

### **NO-GO Criteria** (Any single failure blocks)
- ❌ Any Critical (P0) test fails
- ❌ < 95% High (P1) test success rate
- ❌ Data corruption detected
- ❌ Any SLO breach in staging
- ❌ Security vulnerability (High/Critical)
- ❌ Pricing pack build failure
- ❌ Ledger reconciliation discrepancy > ±1bp

---

## Test Execution Summary

**Total Tests**: 47
**Critical (P0)**: 18
**High (P1)**: 19
**Medium (P2)**: 10

**Execution Time**: ~45 minutes (can run in parallel)

---

## Section 1: Core Portfolio Operations (P0 Critical)

### 1.1 Portfolio Creation & Initialization
**Priority**: P0
**Owner**: Portfolio Team

- [ ] **UAT-001**: Create new portfolio with valid user_id
  - **Steps**:
    1. POST `/v1/portfolios` with `{"name": "UAT Test", "base_currency": "USD"}`
    2. Verify response contains `portfolio_id` (UUID)
    3. Verify `ledger_path` is set to `ledger/portfolios/{portfolio_id}.bean`
  - **Expected**: Portfolio created, Beancount journal initialized
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-002**: Verify RLS policy isolates portfolios
  - **Steps**:
    1. Create portfolio for `user_a` (set `app.user_id = 'user_a'`)
    2. Try to read portfolio as `user_b` (set `app.user_id = 'user_b'`)
  - **Expected**: 403 Forbidden or empty result
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 1.2 Trade Entry & Lot Creation
**Priority**: P0

- [ ] **UAT-003**: Execute buy trade (100 AAPL @ $150 USD)
  - **Steps**:
    1. POST `/v1/trades` with buy order
    2. Verify `transactions` row created with `action = 'buy'`
    3. Verify `lots` row created with `qty_open = 100`, `cost_basis_per_share_base = 150.00`
    4. Verify `ledger_tx_id` links to Beancount transaction
  - **Expected**: Trade recorded, lot opened, ledger updated
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-004**: Execute sell trade (40 AAPL, FIFO lot selection)
  - **Steps**:
    1. Sell 40 shares from UAT-003 lot
    2. Verify `lots.qty_open` reduced to 60
    3. Verify realized P&L calculated correctly
  - **Expected**: Lot partially closed, P&L recorded
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-005**: Multi-currency trade (buy 50 BMW.DE @ €90 EUR)
  - **Steps**:
    1. Execute trade with `currency = 'EUR'`
    2. Verify `trade_fx_rate_id` populated (EUR/USD rate at trade time)
    3. Verify `cost_basis_per_share_base` converted to USD
  - **Expected**: Trade recorded with correct FX conversion
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 2: Pricing & Valuation (P0 Critical)

### 2.1 Pricing Pack Build
**Priority**: P0
**Owner**: Data Team

- [ ] **UAT-006**: Build pricing pack for current date
  - **Steps**:
    1. Trigger nightly job: `python -m jobs.build_pricing_pack --date=$(date +%Y-%m-%d)`
    2. Verify `pricing_pack` row created with `is_fresh = FALSE` initially
    3. Verify `prices` table populated for all securities in universe
    4. Verify `fx_rates` table populated for all currency pairs
  - **Expected**: Pack built successfully, all assets priced
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-007**: Verify pricing pack immutability
  - **Steps**:
    1. Build pack for 2024-10-20
    2. Attempt to UPDATE existing pack row
    3. Verify database rejects update (append-only constraint)
  - **Expected**: UPDATE fails, must use supersede chain
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-008**: Test pack supersede (restatement)
  - **Steps**:
    1. Build pack A for 2024-10-20
    2. Build pack B for 2024-10-20 with corrected prices
    3. Set `pack_b.supersedes = pack_a.pricing_pack_id`
    4. Verify `GET /v1/pricing/latest?date=2024-10-20` returns pack B
  - **Expected**: Latest pack (B) served, pack A retained for audit
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 2.2 Multi-Currency Valuation
**Priority**: P0

- [ ] **UAT-009**: Value multi-currency portfolio (USD base)
  - **Steps**:
    1. Portfolio contains: 100 AAPL (USD), 50 BMW.DE (EUR), 200 HSBC.L (GBP)
    2. GET `/v1/portfolios/{id}/valuation?pricing_pack_id={pack}`
    3. Verify each position valued in base currency (USD)
    4. Verify `total_value` = Σ(qty × price × fx_rate)
  - **Expected**: All positions converted to USD correctly
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-010**: Verify pricing pack reproducibility
  - **Steps**:
    1. Value portfolio with `pricing_pack_id = pack_20241020_v1`
    2. Wait 1 hour, re-request same `pricing_pack_id`
    3. Verify valuations are byte-for-byte identical
  - **Expected**: Identical results (immutable pack guarantee)
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 3: Corporate Actions (P0 Critical)

### 3.1 Dividend Processing
**Priority**: P0

- [ ] **UAT-011**: Process cash dividend (AAPL $0.25/share)
  - **Steps**:
    1. Record dividend: `POST /v1/corporate-actions/dividends`
    2. Verify `transactions` row with `action = 'dividend'`
    3. Verify cash balance increased by `qty × amount_per_share`
  - **Expected**: Dividend recorded, cash updated
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-012**: Process ADR dividend with withholding tax
  - **Steps**:
    1. Record dividend for ADR security (e.g., BABA)
    2. Provide `gross_ccy = 1.00 USD`, `withholding_ccy = 0.10 USD`, `net_ccy = 0.90 USD`
    3. Verify `pay_fx_rate_id` used for pay-date conversion
    4. Verify ledger shows gross, withholding, and net amounts
  - **Expected**: Tax withholding tracked, net amount received
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 3.2 Stock Splits
**Priority**: P0

- [ ] **UAT-013**: Process 2:1 stock split (NVDA)
  - **Steps**:
    1. Before split: 100 shares @ $500/share
    2. Record split: `POST /v1/corporate-actions/splits` with `ratio = 2.0`
    3. Verify `lots.qty_open` doubled to 200
    4. Verify `cost_basis_per_share` halved to $250
    5. Verify total cost basis unchanged
  - **Expected**: Quantity and cost basis adjusted, total value preserved
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 4: Ledger Reconciliation (P0 Critical)

### 4.1 Beancount Integration
**Priority**: P0
**Owner**: Ledger Team

- [ ] **UAT-014**: Verify ledger journal created on portfolio creation
  - **Steps**:
    1. Create new portfolio
    2. Verify file exists at `ledger/portfolios/{portfolio_id}.bean`
    3. Verify opening balance entry present
  - **Expected**: Beancount journal initialized
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-015**: Nightly reconciliation (±1bp validation)
  - **Steps**:
    1. Run `python -m jobs.reconcile_ledger --portfolio_id={id}`
    2. Verify `reconciliations` table row created with `status = 'OK'`
    3. If FAIL, verify `discrepancies_json` contains details
    4. Verify `ledger_commit_hash` recorded
  - **Expected**: Ledger and DB match within ±1 basis point
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-016**: Detect reconciliation discrepancy
  - **Steps**:
    1. Manually edit Beancount journal (change qty)
    2. Run reconciliation job
    3. Verify `status = 'FAIL'` with discrepancy details
  - **Expected**: Discrepancy detected and logged
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 5: Performance Metrics (P0 Critical)

### 5.1 TWR Calculation
**Priority**: P0

- [ ] **UAT-017**: Calculate TWR over date range (no cash flows)
  - **Steps**:
    1. Portfolio: $100,000 on 2024-01-01, $110,000 on 2024-12-31
    2. GET `/v1/portfolios/{id}/twr?start=2024-01-01&end=2024-12-31`
  - **Expected**: TWR = 10.00%
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-018**: Calculate TWR with mid-period cash flow
  - **Steps**:
    1. Start: $100k, Mid (2024-07-01): +$50k deposit, End: $165k
    2. Expected TWR ≈ 10% (isolates cash flows)
  - **Expected**: TWR calculated correctly per formula
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 5.2 Attribution Analysis
**Priority**: P0

- [ ] **UAT-019**: Brinson-Fachler attribution (sector + security)
  - **Steps**:
    1. Run attribution for 60/40 portfolio vs benchmark (S&P 500 / AGG)
    2. Verify allocation effect + selection effect = total active return
    3. Verify results match golden test (AAPL Oct 2023 example)
  - **Expected**: Attribution factors sum correctly
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 6: Alerting System (P1 High)

### 6.1 Alert Delivery
**Priority**: P1

- [ ] **UAT-020**: Trigger threshold alert (portfolio value drop > 5%)
  - **Steps**:
    1. Configure alert rule
    2. Simulate market drop (update pricing pack)
    3. Run `python -m jobs.evaluate_alerts`
    4. Verify alert delivered to webhook/email
  - **Expected**: Alert delivered within 60 seconds (median SLO)
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-021**: Verify alert cooldown (prevents spam)
  - **Steps**:
    1. Trigger same alert condition twice within 15 minutes
    2. Verify second alert suppressed due to cooldown
  - **Expected**: Only one alert sent (cooldown enforced)
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-022**: Alert deduplication across recipients
  - **Steps**:
    1. Configure same alert for user_a and user_b (same portfolio)
    2. Trigger condition
    3. Verify deduplication logic (if applicable)
  - **Expected**: No duplicate processing
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 7: Provider Integration (P1 High)

### 7.1 Real-Time Market Data
**Priority**: P1

- [ ] **UAT-023**: Fetch real-time quote (FMP API)
  - **Steps**:
    1. GET `/v1/market/quote?symbol=AAPL`
    2. Verify response contains latest price, volume, timestamp
  - **Expected**: Data returned within 500ms
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-024**: Circuit breaker on provider timeout
  - **Steps**:
    1. Simulate FMP API timeout (toxiproxy or mock)
    2. Verify circuit breaker opens after 3 failures
    3. Verify fallback to cached data or graceful error
  - **Expected**: Circuit breaker engages, no cascading failure
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 7.2 Economic Data (FRED)
**Priority**: P1

- [ ] **UAT-025**: Fetch macro indicators (GDP, CPI, unemployment)
  - **Steps**:
    1. GET `/v1/economic/indicators?series=GDP,CPIAUCSL,UNRATE`
    2. Verify data freshness (< 24 hours old)
  - **Expected**: All series returned with metadata
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 8: Dalio Macro Framework (P1 High)

### 8.1 Regime Detection
**Priority**: P1

- [ ] **UAT-026**: Detect economic regime (expansion/contraction)
  - **Steps**:
    1. Load historical indicators (GDP growth, unemployment, inflation)
    2. GET `/v1/macro/regime?date=2024-10-20`
    3. Verify regime classification (e.g., "Late Expansion")
  - **Expected**: Regime matches economic conditions
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-027**: Factor exposure analysis (growth vs value)
  - **Steps**:
    1. Analyze portfolio holdings
    2. GET `/v1/macro/factor-exposure?portfolio_id={id}`
    3. Verify exposures: growth, value, momentum, quality
  - **Expected**: Factor tilts calculated correctly
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 8.2 Scenario Analysis
**Priority**: P1

- [ ] **UAT-028**: Run recession scenario (DaR - Drawdown at Risk)
  - **Steps**:
    1. POST `/v1/macro/scenarios/recession` with portfolio_id
    2. Verify expected drawdown calculated (historical recession analogs)
  - **Expected**: DaR estimate returned with confidence interval
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 9: Buffett Quality Ratings (P1 High)

### 9.1 Moat Analysis
**Priority**: P1

- [ ] **UAT-029**: Calculate moat strength (KO, WMT, JNJ)
  - **Steps**:
    1. GET `/v1/quality/moat?symbols=KO,WMT,JNJ`
    2. Verify scores (0-10 scale) for intangibles, switching costs, network effects
  - **Expected**: Scores match golden test expectations
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 9.2 Dividend Safety
**Priority**: P1

- [ ] **UAT-030**: Assess dividend sustainability (5-year payout ratio trend)
  - **Steps**:
    1. GET `/v1/quality/dividend-safety?symbol=JNJ`
    2. Verify payout ratio, coverage, growth streak
  - **Expected**: Safety score (0-10) with supporting metrics
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 10: Rights Management (P2 Medium)

### 10.1 Data Usage Rights
**Priority**: P2

- [ ] **UAT-031**: Block export if rights prohibit
  - **Steps**:
    1. Request PDF export of data with `rights_registry.export_pdf = FALSE`
    2. Verify 403 Forbidden response
  - **Expected**: Export blocked with clear error message
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-032**: Allow export if rights permit
  - **Steps**:
    1. Request export with `export_pdf = TRUE`
    2. Verify PDF generated successfully
  - **Expected**: Export succeeds
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 11: Performance SLOs (P0 Critical)

### 11.1 API Latency
**Priority**: P0

- [ ] **UAT-033**: Warm request p95 ≤ 1.2s
  - **Steps**:
    1. Send 100 requests to `/v1/portfolios/{id}/valuation` (pre-warmed pack)
    2. Measure p95 latency
  - **Expected**: p95 ≤ 1200ms
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-034**: Cold request p95 ≤ 2.0s
  - **Steps**:
    1. Clear cache, send 100 requests (pack warming in progress)
    2. Measure p95 latency
  - **Expected**: p95 ≤ 2000ms
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 11.2 Nightly Jobs
**Priority**: P0

- [ ] **UAT-035**: Pack build completes by 00:15 local time
  - **Steps**:
    1. Trigger nightly job at 00:00
    2. Monitor completion time
  - **Expected**: `is_fresh = TRUE` by 00:15
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-036**: Verify sacred job order (6 steps)
  - **Steps**:
    1. Monitor nightly job sequence
    2. Verify order: build_pack → reconcile → metrics → prewarm → fresh → alerts
  - **Expected**: Jobs run in exact order (non-negotiable)
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 12: Security & Compliance (P0 Critical)

### 12.1 Authentication & Authorization
**Priority**: P0

- [ ] **UAT-037**: Reject unauthenticated requests
  - **Steps**:
    1. Send request without JWT token
  - **Expected**: 401 Unauthorized
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-038**: Reject expired JWT token
  - **Steps**:
    1. Use JWT with `exp` timestamp in past
  - **Expected**: 401 Unauthorized
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-039**: Verify RLS policies enforce user isolation
  - **Steps**:
    1. User A tries to access User B's portfolio
  - **Expected**: 403 Forbidden or empty result
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 12.2 Data Integrity
**Priority**: P0

- [ ] **UAT-040**: Verify foreign key constraints
  - **Steps**:
    1. Attempt to insert `transactions` row with invalid `portfolio_id`
  - **Expected**: Database rejects with FK violation
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-041**: Verify pricing pack immutability (no UPDATEs)
  - **Steps**:
    1. Attempt to UPDATE existing `pricing_pack` row
  - **Expected**: Database rejects (append-only)
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 13: Observability (P1 High)

### 13.1 Distributed Tracing
**Priority**: P1

- [ ] **UAT-042**: Verify OpenTelemetry trace propagation
  - **Steps**:
    1. Send request with `traceparent` header
    2. Check Jaeger UI for complete trace (API → DB → jobs)
  - **Expected**: Full trace visible with all spans
  - **Actual**: ___________
  - **Pass/Fail**: ___________

### 13.2 Metrics Collection
**Priority**: P1

- [ ] **UAT-043**: Verify Prometheus metrics exposed
  - **Steps**:
    1. GET `/metrics`
    2. Verify key metrics present: `http_requests_total`, `pricing_pack_build_duration_seconds`
  - **Expected**: All metrics scraped successfully
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 14: Error Handling (P1 High)

### 14.1 Graceful Degradation
**Priority**: P1

- [ ] **UAT-044**: Serve stale pack if build fails
  - **Steps**:
    1. Simulate pack build failure (kill job)
    2. Verify API serves last-good pack with warning header
  - **Expected**: `X-Pricing-Pack-Stale: true` header present
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-045**: Handle provider outage gracefully
  - **Steps**:
    1. Simulate FMP API down (all requests timeout)
    2. Verify circuit breaker opens, cached data served
  - **Expected**: No 500 errors, degraded mode indicated
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Section 15: Data Migration (P2 Medium)

### 15.1 Schema Migrations
**Priority**: P2

- [ ] **UAT-046**: Apply migration 001 (ledger_commit_hash)
  - **Steps**:
    1. Run `psql < migrations/001_reproducibility_enhancements.sql`
    2. Verify column added: `\d pricing_pack`
  - **Expected**: Migration succeeds, no data loss
  - **Actual**: ___________
  - **Pass/Fail**: ___________

- [ ] **UAT-047**: Rollback migration 001
  - **Steps**:
    1. Run rollback section from migration file
    2. Verify column removed
  - **Expected**: Rollback succeeds, system still functional
  - **Actual**: ___________
  - **Pass/Fail**: ___________

---

## Final Go/No-Go Decision

### Critical (P0) Test Results
- **Total P0 Tests**: 18
- **Passed**: _____ / 18
- **Failed**: _____
- **Pass Rate**: _____ %

**Decision**:
- [ ] **GO** (100% P0 pass rate, all SLOs met)
- [ ] **NO-GO** (Any P0 failure or SLO breach)

### High (P1) Test Results
- **Total P1 Tests**: 19
- **Passed**: _____ / 19
- **Failed**: _____
- **Pass Rate**: _____ %

**Decision**:
- [ ] **GO** (≥ 95% P1 pass rate)
- [ ] **NO-GO** (< 95% P1 pass rate)

### Medium (P2) Test Results
- **Total P2 Tests**: 10
- **Passed**: _____ / 10
- **Failed**: _____
- **Pass Rate**: _____ %

**Note**: P2 failures may be accepted with mitigation plan

---

## SLO Validation Summary

| SLO | Target | Actual | Pass/Fail |
|-----|--------|--------|-----------|
| Warm p95 latency | ≤ 1.2s | _______ | _____ |
| Cold p95 latency | ≤ 2.0s | _______ | _____ |
| Pack build time | By 00:15 | _______ | _____ |
| Alert median latency | ≤ 60s | _______ | _____ |
| Reconciliation accuracy | ±1bp | _______ | _____ |

**SLO Compliance**:
- [ ] All SLOs met
- [ ] One or more SLO breaches (NO-GO)

---

## Sign-Off

**QA Lead**: _____________________________ Date: _____________
**Product Owner**: _______________________ Date: _____________
**Engineering Lead**: ____________________ Date: _____________

**Final Decision**:
- [ ] **GO** - Approved for production deployment
- [ ] **NO-GO** - Requires remediation (see failed tests above)

**Remediation Plan** (if NO-GO):
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

## Post-UAT Actions

### If GO:
1. Tag release: `git tag v1.0.0-rc1`
2. Proceed to CI/CD Stage 12 (Canary Production)
3. Monitor canary deployment per [CI_CD_PIPELINE.md](./CI_CD_PIPELINE.md)

### If NO-GO:
1. Create Jira tickets for all failed tests
2. Assign to responsible teams
3. Schedule re-test after remediation
4. Update this checklist with remediation notes

---

## Related Documents

- **[CI_CD_PIPELINE.md](./CI_CD_PIPELINE.md)** - Deployment pipeline
- **[RUNBOOKS.md](./RUNBOOKS.md)** - Incident response
- **[PRODUCT_SPEC.md](../.claude/PRODUCT_SPEC.md)** - Acceptance criteria
- **[SCHEMA_SPECIALIST.md](../.claude/agents/data/SCHEMA_SPECIALIST.md)** - Database reference

---

**Last Updated**: 2025-10-21
**Next Review**: After each UAT cycle
**Owner**: QA Team
