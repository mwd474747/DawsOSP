# Full Roadmap Implementation Guide

**Date**: 2025-10-22
**Status**: Sprint 2 Complete, Ready for Sprint 3-4
**Total Estimate**: 110-167 hours (~3-4 weeks solo)

---

## Progress Summary

### ✅ Completed (48% of roadmap)
- **Sprint 2**: 100% complete
  - Metrics database (TimescaleDB)
  - Currency attribution (±0.1bp accuracy)
  - UI Portfolio Overview
  - Agent capability wiring
  - E2E integration tests
  - Backfill rehearsal tool
  - Visual regression tests
  - Governance remediation

- **P0 Critical Items**: Partially complete
  - ✅ RLS policies migration created
  - ✅ Alerts/notifications schema created
  - ⏳ Beancount ledger parser (next)
  - ⏳ Rights registry (next)

---

## Implementation Order (Recommended)

### Phase 1: P0 Critical Path (16-25 hours)

This phase must be completed for production readiness.

#### 1.1 Beancount Ledger Parser (10-15 hours)
**File**: `backend/app/services/ledger.py`

**Requirements**:
- Parse Beancount ledger from git repo
- Extract transactions, balances
- Store in `ledger_transactions` table
- Git integration for commit hash

**Key Functions**:
```python
def parse_beancount_ledger(ledger_path: str, commit_hash: str) -> List[Transaction]
def extract_portfolio_transactions(account_pattern: str) -> List[Transaction]
def store_transactions(transactions: List[Transaction], commit_hash: str)
```

**Dependencies**:
- `beancount` library
- Git subprocess calls
- `ledger_transactions` table

**Testing**:
- Unit tests for parser
- Integration test with sample ledger
- Edge cases (splits, dividends, currency conversions)

---

#### 1.2 Ledger Reconciliation Job (4-6 hours)
**File**: `backend/jobs/reconcile_ledger.py`

**Requirements**:
- Compare ledger NAV vs pricing pack NAV
- ±1bp tolerance
- Store results in `reconciliation_results`
- Nightly scheduler

**Key Functions**:
```python
async def reconcile_portfolio(portfolio_id: UUID, pack_id: str, ledger_hash: str) -> ReconciliationResult
async def compute_ledger_nav(portfolio_id: UUID, date: date, ledger_hash: str) -> Decimal
async def compute_pricing_nav(portfolio_id: UUID, pack_id: str) -> Decimal
```

**Acceptance**:
- Error <= 1bp for all test portfolios
- Reconciliation runs nightly
- Failed reconciliation alerts sent

---

#### 1.3 Rights Registry (4-6 hours)
**Files**:
- `.ops/RIGHTS_REGISTRY.yaml`
- `backend/app/core/rights_registry.py`

**Requirements**:
- YAML definitions for FMP, Polygon, FRED, NewsAPI
- Rights loader
- `ensure_allowed()` gate function
- PDF export rights check

**Example YAML**:
```yaml
providers:
  FMP:
    allows_display: true
    allows_export_pdf: true
    allows_export_csv: true
    allows_redistribution: false
    attribution_text: "Data provided by Financial Modeling Prep"
```

**Key Functions**:
```python
def load_rights_registry() -> Dict[str, ProviderRights]
def ensure_allowed(providers: List[str], operation: str) -> Tuple[List[str], List[str]]
def get_attribution_text(providers: List[str]) -> str
```

---

### Phase 2: Sprint 3 Week 5 - Macro (20-30 hours)

#### 2.1 Macro Service (8-10 hours)
**File**: `backend/app/services/macro.py`

**Requirements**:
- Regime detection (5 regimes)
- Z-score normalization
- FRED API integration for indicators

**Database**:
```sql
CREATE TABLE macro_indicators (...);
CREATE TABLE regime_history (...);
```

**Key Functions**:
```python
def detect_regime(indicators: Dict[str, float]) -> Regime
def zscore(value: float, window: int = 252) -> float
```

---

#### 2.2 Macro Cycles (8-10 hours)
**File**: `backend/app/services/cycles.py`

**Requirements**:
- STDC/LTDC/Empire cycle definitions
- Composite score computation
- Phase matching

**Config**: `storage/macro_cycles/cycle_definitions.json`

**Key Functions**:
```python
def detect_cycle_phase(cycle_id: str, indicators: Dict) -> CyclePhase
def compute_composite_score(indicators: Dict, weights: Dict) -> float
```

---

#### 2.3 DaR (Drawdown at Risk) (4-6 hours)
**File**: `backend/app/services/risk.py`

**Requirements**:
- Scenario stress testing
- 95% confidence DaR
- Scenario definitions

**Key Functions**:
```python
def compute_dar(portfolio_id: UUID, scenarios: List[Scenario], confidence: float = 0.95) -> float
def apply_scenario(portfolio_id: UUID, scenario: Scenario) -> float
```

---

### Phase 3: Sprint 3 Week 6 - Alerts + News (20-30 hours)

#### 3.1 Alert Service (10-12 hours)
**File**: `backend/app/services/alerts.py`

**Requirements**:
- Condition evaluation (nightly cron)
- Cooldown enforcement
- Email/in-app notifications

**Key Functions**:
```python
@scheduler.scheduled_job("cron", hour=0, minute=10)
async def evaluate_alerts()

async def evaluate_condition(condition: Dict) -> bool
async def send_notification(alert: Alert)
```

---

#### 3.2 DLQ + Deduplication (6-8 hours)
**File**: `backend/app/jobs/dlq_replay.py`

**Requirements**:
- Failed notification handler
- DLQ push/pop/ack/nack
- Hourly replay job

**Key Functions**:
```python
async def dlq_push(alert: Alert, error: Exception)
async def dlq_pop_batch(limit: int = 100) -> List[DLQMessage]
```

---

#### 3.3 News Service (4-6 hours)
**File**: `backend/app/services/news.py`

**Requirements**:
- NewsAPI integration (dev plan: metadata only)
- 24h delay handling
- UI panel with dev plan notice

**Key Functions**:
```python
async def fetch_news(symbol: str) -> List[NewsArticle]
def render_news_panel(symbol: str)  # Streamlit
```

---

### Phase 4: Sprint 4 Week 7 - Ratings + Optimizer (25-35 hours)

#### 4.1 Ratings Service (15-20 hours)
**File**: `backend/app/services/ratings.py`

**Requirements**:
- DivSafety score (0-10)
- Moat score (0-10)
- Resilience score (0-10)
- Method versioning

**Database**:
```sql
CREATE TABLE security_ratings (...);
```

**Key Functions**:
```python
def compute_dividend_safety(symbol: str, pack_id: UUID) -> float
def compute_moat(symbol: str, pack_id: UUID) -> float
def compute_resilience(symbol: str, pack_id: UUID) -> float
```

---

#### 4.2 Fundamentals Fetcher (5-7 hours)
**File**: `backend/app/services/fundamentals.py`

**Requirements**:
- FMP API integration
- Income statement, balance sheet, cash flow
- Caching

**Key Functions**:
```python
async def fetch_income_statement(symbol: str) -> IncomeStatement
async def fetch_balance_sheet(symbol: str) -> BalanceSheet
async def fetch_cash_flow(symbol: str) -> CashFlowStatement
```

---

#### 4.3 Optimizer Service (5-8 hours)
**File**: `backend/app/services/optimizer.py`

**Requirements**:
- Mean-variance optimization
- Tracking error constraints
- Transaction cost modeling

**Key Functions**:
```python
def optimize_portfolio(holdings: List[Holding], benchmark: List[Weight], max_te: float) -> List[Trade]
def compute_expected_return(weights: np.array, returns: np.array) -> float
def compute_expected_risk(weights: np.array, cov_matrix: np.array) -> float
```

---

### Phase 5: Sprint 4 Week 8 - Reporting + Polish (15-25 hours)

#### 5.1 PDF Exporter (8-12 hours)
**File**: `backend/app/services/reporting.py`

**Requirements**:
- HTML template rendering
- Rights gate enforcement
- PDF generation (WeasyPrint)

**Key Functions**:
```python
def generate_portfolio_pdf(portfolio_id: UUID, ctx: ExecutorContext) -> bytes
def ensure_export_allowed(providers: List[str]) -> bool
```

---

#### 5.2 Hedged Benchmark (2-3 hours)
**File**: `backend/app/services/benchmarks.py`

**Requirements**:
- Toggle for currency hedging
- Strip FX return when hedged

**Key Functions**:
```python
def compute_benchmark_return(benchmark_id: str, hedged: bool = False) -> float
```

---

#### 5.3 DaR Calibration View (3-5 hours)
**File**: `ui/screens/dar_calibration.py`

**Requirements**:
- Walk-forward calibration
- MAD calculation
- Hit rate display

**Key Functions**:
```python
def compute_dar_calibration(portfolio_id: UUID, lookback_days: int = 252) -> DaRCalibration
def render_dar_calibration(portfolio_id: UUID)  # Streamlit
```

---

#### 5.4 Performance SLO Validation (2-5 hours)
**File**: `tests/performance/test_slo.py`

**Requirements**:
- Warm p95 ≤ 1.2s load test
- Cold p95 ≤ 2.0s load test

**Tests**:
```python
def test_slo_warm_p95_under_1200ms()
def test_slo_cold_p95_under_2000ms()
```

---

### Phase 6: Infrastructure (8-12 hours)

#### 6.1 Terraform Modules
**Directory**: `infra/terraform/`

**Modules**:
- PostgreSQL + TimescaleDB (RDS)
- Redis cluster (ElastiCache)
- S3 buckets
- Secrets Manager
- VPC, subnets, security groups
- WAF
- Monitoring (Prometheus, Jaeger)

**Files**:
```
infra/terraform/
├── db/main.tf
├── cache/main.tf
├── storage/main.tf
├── secrets/main.tf
├── network/main.tf
├── waf/main.tf
├── monitoring/main.tf
├── staging.tfvars
└── prod.tfvars
```

---

### Phase 7: Security (6-10 hours)

#### 7.1 Threat Model
**File**: `.security/THREAT_MODEL.md`

**Contents**:
- STRIDE analysis
- Attack trees
- Mitigations

---

#### 7.2 SBOM/SCA/SAST CI
**File**: `.github/workflows/security.yml`

**Steps**:
- Syft (SBOM generation)
- ORT (license compliance)
- Grype (vulnerability scan)
- CodeQL (SAST)

---

#### 7.3 RLS Fuzz Tests
**File**: `tests/security/test_rls_fuzz.py`

**Tests**:
```python
@pytest.mark.parametrize("user_a_jwt,user_b_portfolio_id", generate_fuzz_pairs(100))
def test_rls_blocks_cross_portfolio_access(user_a_jwt, user_b_portfolio_id)
```

---

## Implementation Checklist

### P0 Critical (Must Have) - 16-25 hours
- [x] RLS policies migration
- [x] Alerts/notifications schema
- [ ] Beancount ledger parser (10-15h)
- [ ] Ledger reconciliation job (4-6h)
- [ ] Rights registry (4-6h)

### Sprint 3 Week 5 - 20-30 hours
- [ ] Macro service (regime detection) (8-10h)
- [ ] Macro cycles (STDC/LTDC/Empire) (8-10h)
- [ ] DaR calculation (4-6h)
- [ ] FRED integration (included in macro service)

### Sprint 3 Week 6 - 20-30 hours
- [ ] Alert service (10-12h)
- [ ] DLQ + deduplication (6-8h)
- [ ] News service (4-6h)
- [ ] Chaos tests (included in alert tests)

### Sprint 4 Week 7 - 25-35 hours
- [ ] Ratings service (15-20h)
- [ ] Fundamentals fetcher (5-7h)
- [ ] Optimizer service (5-8h)
- [ ] Nightly pre-warm job (included in ratings)

### Sprint 4 Week 8 - 15-25 hours
- [ ] PDF exporter (8-12h)
- [ ] Hedged benchmark (2-3h)
- [ ] DaR calibration view (3-5h)
- [ ] Performance SLO validation (2-5h)

### Infrastructure - 8-12 hours
- [ ] Terraform modules (8-12h)

### Security - 6-10 hours
- [ ] Threat model (2-3h)
- [ ] SBOM/SCA/SAST CI (3-5h)
- [ ] RLS fuzz tests (1-2h)

---

## Total Estimate
- **P0 Critical**: 16-25 hours
- **Sprint 3**: 40-60 hours
- **Sprint 4**: 40-60 hours
- **Infrastructure**: 8-12 hours
- **Security**: 6-10 hours

**Grand Total**: 110-167 hours (~3-4 weeks solo, ~2-3 weeks with team)

---

## Next Steps

1. **Start with P0**: Complete ledger parser, reconciliation, rights registry
2. **Then Sprint 3**: Macro, alerts, news (high user value)
3. **Then Sprint 4**: Ratings, optimizer, reporting (polish features)
4. **Finally Infrastructure**: Terraform, security (deployment readiness)

---

## Files Already Created (This Session)

1. ✅ `backend/db/migrations/005_create_rls_policies.sql` (230 lines)
2. ✅ `backend/db/schema/alerts_notifications.sql` (280 lines)
3. ✅ `REMAINING_WORK.md` (comprehensive roadmap status)
4. ✅ `FULL_ROADMAP_IMPLEMENTATION_GUIDE.md` (this file)

**Progress**: RLS + schemas ready, ledger parser next

---

**Status**: Ready to continue with P0 critical path (Beancount ledger parser)
**Estimated Completion**: 3-4 weeks solo development
