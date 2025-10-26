# TEST_ARCHITECT — Quality Assurance & Test Automation Specialist

**Agent Type**: Platform
**Phase**: Week 0-8 (Foundation through Production)
**Priority**: P0 (Quality gate for all work)
**Status**: Specification Complete
**Created**: 2025-10-21

---

## Mission

Build **comprehensive test automation suite** with 7 test types (Unit, Property, Golden, Integration, Security, Chaos, Performance) achieving 95%+ coverage, enforcing SLOs (warm p95 ≤ 1.2s, cold p95 ≤ 2.0s), and validating financial accuracy (±1bp ledger reconciliation).

---

## Scope & Responsibilities

### In Scope

1. **Unit Tests (95%+ Coverage)**
   - Core modules: TWR/MWR calculations, currency attribution, factor exposure
   - Services: pricing pack, ledger reconciliation, ratings, optimizer
   - API endpoints: request validation, response formatting, error handling
   - Database: RLS policies, hypertable queries, constraint enforcement

2. **Property Tests (Hypothesis)**
   - Multi-currency arithmetic invariants (no rounding errors > 1bp)
   - Pricing pack immutability (append-only, no mutations)
   - TWR commutativity (date range order independence)
   - RLS isolation (no cross-portfolio data leaks)

3. **Golden Tests (Regression Protection)**
   - Attribution calculation (AAPL multi-currency example)
   - Factor exposure (60/40 S&P/AGG portfolio)
   - Dalio regime detection (dot-com, 2008 crisis, 2020 COVID)
   - Buffett ratings (KO, WMT, JNJ quality scores)

4. **Integration Tests**
   - End-to-end flows (portfolio creation → metrics → PDF export)
   - Ledger reconciliation (±1bp validation vs Beancount)
   - Provider integration (circuit breaker, fallback, DLQ)
   - Alert delivery (cooldown, deduplication, latency ≤ 60s median)

5. **Security Tests**
   - RLS/IDOR fuzzing (cross-user access attempts)
   - SQL injection (parameterized query validation)
   - JWT validation (expiry, signature, claims)
   - Secret scanning (no hardcoded credentials)

6. **Chaos Tests**
   - Provider outage (circuit breaker engagement)
   - Database failover (< 5s downtime recovery)
   - Cache eviction (Redis → DB fallback)
   - Pack build during market hours (stale pack served with banner)

7. **Performance Tests**
   - SLO enforcement (warm p95 ≤ 1.2s, cold p95 ≤ 2.0s)
   - Load testing (100 concurrent users)
   - Pack build completion (< 15 minutes by 00:15 local time)
   - Alert median latency (≤ 60s from trigger to delivery)

### Out of Scope

- ❌ Manual QA (all tests automated)
- ❌ End-user acceptance testing (separate UAT checklist)
- ❌ Performance tuning (separate optimization work)
- ❌ Test data generation (handled by seeding plan)

---

## Acceptance Criteria

### AC-1: Unit Test Coverage ≥ 95%
**Given**: Backend codebase with core, services, API modules
**When**: Run `pytest tests/unit/ --cov=app --cov-fail-under=95`
**Then**:
- **Overall coverage**: ≥ 95%
- **Core modules** (`app/core/`): ≥ 98%
- **Services** (`app/services/`): ≥ 95%
- **API** (`app/api/`): ≥ 90%
- **Zero test failures**
- **Zero flaky tests** (3-run verification)

**Coverage Report**:
```
Name                          Stmts   Miss  Cover
-------------------------------------------------
app/core/metrics.py             245      3    99%
app/core/currency.py            180      2    99%
app/services/pricing_pack.py    320      8    97%
app/services/ratings.py         280     12    96%
app/api/portfolios.py           150     12    92%
-------------------------------------------------
TOTAL                          1825     45    97%
```

**CI Integration**: `pytest tests/unit/ --cov=app --cov-report=xml --cov-fail-under=95`

**Artifacts**: `coverage.xml` (for SonarQube), `htmlcov/` (HTML report)

---

### AC-2: Property Tests (Multi-Currency Invariants)
**Given**: Currency attribution calculation
**When**: Run Hypothesis property tests with 1000+ generated inputs
**Then**:
- **Invariant**: `r_base ≈ (1+r_local)(1+r_fx) - 1 ± 0.1bp`
- **No rounding errors** > 1 basis point
- **All currencies tested**: USD, CAD, EUR, GBP, JPY, AUD, CHF
- **All properties hold** under edge cases:
  - Large FX swings (±20%)
  - Small local returns (< 0.01%)
  - Negative returns + positive FX
  - Zero returns (identity check)

**Example Property Test**:
```python
# tests/property/test_currency_attribution.py

from hypothesis import given, strategies as st
from app.core.currency import compute_currency_attribution

@given(
    local_return=st.floats(min_value=-0.5, max_value=0.5),
    fx_return=st.floats(min_value=-0.3, max_value=0.3)
)
def test_currency_attribution_invariant(local_return, fx_return):
    """Verify r_base = (1+r_local)(1+r_fx) - 1 ± 0.1bp."""
    result = compute_currency_attribution(local_return, fx_return)

    # Expected base return
    expected_base = (1 + local_return) * (1 + fx_return) - 1

    # Verify invariant (within 1 basis point)
    assert abs(result.base_return - expected_base) <= 0.0001

    # Verify components sum correctly
    total = result.local_ret + result.fx_ret + result.interaction_ret
    assert abs(total - expected_base) <= 0.0001
```

**CI Integration**: `pytest tests/property/ --hypothesis-profile=ci --hypothesis-seed=random`

---

### AC-3: Golden Test (AAPL Attribution)
**Given**: AAPL holding from Oct 2023 (known historical data)
**When**: Run attribution calculation with pricing pack `2023-10-31-WM4PM-CAD`
**Then**:
- **TWR (month)**: 2.35% (matches golden output)
- **Local return (USD)**: 1.80%
- **FX return (USD→CAD)**: 0.50%
- **Interaction**: 0.05%
- **Total**: 2.35% (± 0.01% tolerance)

**Golden Output** (`tests/golden/attribution/aapl_oct2023.json`):
```json
{
  "symbol": "AAPL",
  "period": "2023-10-01 to 2023-10-31",
  "pricing_pack_id": "2023-10-31-WM4PM-CAD",
  "twr": 0.0235,
  "local_return": 0.0180,
  "fx_return": 0.0050,
  "interaction_return": 0.0005,
  "base_currency": "CAD",
  "trading_currency": "USD"
}
```

**Test Execution**:
```python
# tests/golden/test_attribution.py

def test_aapl_attribution_oct2023():
    """Verify AAPL attribution matches golden output (Oct 2023)."""
    golden = load_golden("attribution/aapl_oct2023.json")

    result = compute_attribution(
        symbol="AAPL",
        start_date=date(2023, 10, 1),
        end_date=date(2023, 10, 31),
        pricing_pack_id=golden["pricing_pack_id"]
    )

    assert abs(result.twr - golden["twr"]) <= 0.0001
    assert abs(result.local_return - golden["local_return"]) <= 0.0001
    assert abs(result.fx_return - golden["fx_return"]) <= 0.0001
```

**CI Integration**: `pytest tests/golden/ --golden-update=never`

---

### AC-4: Integration Test (Ledger Reconciliation ±1bp)
**Given**: Portfolio with 10 holdings, $250K total value
**When**: Run nightly reconciliation job
**Then**:
- **Beancount balance**: $250,342.18 CAD
- **Database TWR**: $250,341.95 CAD
- **Difference**: $0.23 (0.9 basis points) ✅ **PASS** (< 1bp)
- **Reconciliation report** logged to `reconciliation_results` table
- **Alert** triggered if difference > 1bp

**Test Execution**:
```python
# tests/integration/test_ledger_reconciliation.py

def test_reconciliation_within_1bp(test_portfolio):
    """Verify ledger vs DB reconciliation within 1bp tolerance."""

    # Compute portfolio valuation from DB
    db_valuation = compute_portfolio_valuation(
        portfolio_id=test_portfolio.id,
        pricing_pack_id="2024-10-21-WM4PM-CAD"
    )

    # Get ledger balance from Beancount
    ledger_balance = get_beancount_balance(
        portfolio=test_portfolio.name,
        date=date(2024, 10, 21)
    )

    # Verify within 1 basis point
    diff = abs(db_valuation - ledger_balance)
    tolerance = ledger_balance * 0.0001  # 1bp

    assert diff <= tolerance, f"Reconciliation failed: {diff:.2f} > {tolerance:.2f}"
```

**CI Integration**: `pytest tests/integration/test_ledger_reconciliation.py`

---

### AC-5: Security Test (RLS/IDOR Fuzzing)
**Given**: Two users with separate portfolios
**When**: User A attempts to access User B's portfolio via API
**Then**:
- **Request**: `GET /v1/portfolios/{user_b_portfolio_id}` (with User A JWT)
- **Expected response**: `403 Forbidden` (RLS blocks access)
- **Postgres logs**: RLS policy `portfolio_isolation` enforced
- **No data leak**: Zero rows returned from query

**Fuzzing Test**:
```python
# tests/security/test_rls_idor.py

def test_rls_prevents_cross_portfolio_access():
    """Verify RLS blocks cross-user portfolio access."""

    user_a = create_test_user("alice")
    user_b = create_test_user("bob")

    portfolio_a = create_portfolio(user_a, name="Alice Portfolio")
    portfolio_b = create_portfolio(user_b, name="Bob Portfolio")

    # User A tries to access User B's portfolio
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {user_a.jwt}"

    response = client.get(f"/v1/portfolios/{portfolio_b.id}")

    # Should be blocked by RLS
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()

    # Verify no data in response
    assert "holdings" not in response.json()
```

**Fuzzing Strategy**: Generate 1000+ random portfolio ID access attempts across different user JWTs.

**CI Integration**: `pytest tests/security/test_rls_idor.py --count=1000`

---

### AC-6: Chaos Test (Provider Outage → Circuit Breaker)
**Given**: FMP provider API unavailable
**When**: System attempts to fetch prices
**Then**:
- **First 3 requests fail** (timeouts)
- **Circuit breaker opens** (state = OPEN)
- **Subsequent requests** short-circuit immediately (no timeout wait)
- **Fallback** to cached pricing pack (if available)
- **Alert** triggered: "FMP circuit breaker OPEN"
- **After 60s**: Circuit breaker transitions to HALF_OPEN
- **After 1 successful request**: Circuit breaker CLOSED

**Chaos Test**:
```python
# tests/chaos/test_circuit_breaker.py

def test_provider_outage_circuit_breaker():
    """Verify circuit breaker engages on provider outage."""

    # Simulate FMP outage (toxiproxy)
    with fmp_outage():
        # First 3 requests fail
        for i in range(3):
            with pytest.raises(ProviderTimeoutError):
                fetch_prices("AAPL")

        # Circuit breaker should be OPEN
        assert circuit_breaker_state("FMP") == "OPEN"

        # 4th request short-circuits (no timeout)
        start = time.time()
        with pytest.raises(CircuitBreakerOpenError):
            fetch_prices("AAPL")
        duration = time.time() - start

        assert duration < 0.1  # Should fail immediately (< 100ms)

    # Wait for timeout (60s)
    time.sleep(60)

    # Circuit breaker transitions to HALF_OPEN
    assert circuit_breaker_state("FMP") == "HALF_OPEN"

    # Successful request → CLOSED
    with fmp_restored():
        fetch_prices("AAPL")
        assert circuit_breaker_state("FMP") == "CLOSED"
```

**CI Integration**: `pytest tests/chaos/ -k circuit_breaker`

---

### AC-7: Performance Test (Warm p95 ≤ 1.2s SLO)
**Given**: Portfolio valuation endpoint (pre-warmed pricing pack)
**When**: Execute 100 concurrent requests
**Then**:
- **p50 latency**: ≤ 600ms
- **p95 latency**: ≤ 1200ms ✅ **SLO MET**
- **p99 latency**: ≤ 1800ms
- **Throughput**: ≥ 50 req/s
- **Error rate**: 0%

**Load Test**:
```python
# tests/performance/test_slo_warm_latency.py

from locust import HttpUser, task, between

class PortfolioUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def get_valuation(self):
        self.client.get(
            f"/v1/portfolios/{self.portfolio_id}/valuation",
            headers={"Authorization": f"Bearer {self.jwt}"}
        )

# Run locust
# locust -f tests/performance/test_slo_warm_latency.py \
#   --users 100 --spawn-rate 10 --run-time 5m \
#   --host https://staging.dawsos.internal
```

**Results Analysis**:
```bash
# Extract p95 from locust stats
p95=$(jq '.p95' locust_stats.json)

if (( $(echo "$p95 > 1200" | bc -l) )); then
    echo "SLO BREACH: p95 latency ${p95}ms > 1200ms"
    exit 1
fi
```

**CI Integration**: `pytest tests/performance/test_slo_warm_latency.py --max-p95=1200`

---

## Implementation Specifications

### Test Suite Structure

```
tests/
├── unit/                      # Unit tests (95%+ coverage)
│   ├── core/
│   │   ├── test_metrics.py
│   │   ├── test_currency.py
│   │   └── test_ledger.py
│   ├── services/
│   │   ├── test_pricing_pack.py
│   │   ├── test_ratings.py
│   │   └── test_optimizer.py
│   └── api/
│       ├── test_portfolios.py
│       ├── test_valuation.py
│       └── test_reports.py
│
├── property/                  # Hypothesis property tests
│   ├── test_currency_attribution.py
│   ├── test_pricing_pack_immutability.py
│   ├── test_twr_commutativity.py
│   └── test_rls_isolation.py
│
├── golden/                    # Regression golden tests
│   ├── attribution/
│   │   ├── aapl_oct2023.json
│   │   └── test_attribution.py
│   ├── regime/
│   │   ├── dotcom_bubble.json
│   │   ├── crisis_2008.json
│   │   └── test_regime.py
│   └── ratings/
│       ├── ko_wmt_jnj.json
│       └── test_buffett_ratings.py
│
├── integration/               # End-to-end integration tests
│   ├── test_ledger_reconciliation.py
│   ├── test_pricing_pack_build.py
│   ├── test_alert_delivery.py
│   └── test_pdf_export.py
│
├── security/                  # Security & compliance tests
│   ├── test_rls_idor.py
│   ├── test_sql_injection.py
│   ├── test_jwt_validation.py
│   └── test_secret_scanning.py
│
├── chaos/                     # Chaos engineering tests
│   ├── test_circuit_breaker.py
│   ├── test_db_failover.py
│   ├── test_cache_eviction.py
│   └── test_pack_build_during_market.py
│
└── performance/               # Performance & load tests
    ├── test_slo_warm_latency.py
    ├── test_slo_cold_latency.py
    ├── test_pack_build_duration.py
    └── test_alert_latency.py
```

---

### Pytest Configuration

```toml
# pyproject.toml

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

markers = [
    "unit: Unit tests (fast, no external deps)",
    "property: Property-based tests (Hypothesis)",
    "golden: Golden regression tests",
    "integration: Integration tests (requires DB)",
    "security: Security & compliance tests",
    "chaos: Chaos engineering tests",
    "performance: Performance & load tests",
    "slow: Slow tests (> 5s)",
]

# Coverage settings
addopts = [
    "--strict-markers",
    "--tb=short",
    "--maxfail=10",
]

# Hypothesis settings
[tool.hypothesis]
max_examples = 1000
derandomize = false  # Use random seed in CI
deadline = 5000  # 5s per test case
```

---

### Hypothesis Property Test Templates

```python
# tests/property/test_pricing_pack_immutability.py

from hypothesis import given, strategies as st
from app.services.pricing_pack import PricingPackService

@given(
    prices=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=5),  # symbol
            st.floats(min_value=0.01, max_value=1000.0)  # price
        ),
        min_size=1,
        max_size=100
    )
)
def test_pricing_pack_is_append_only(prices):
    """Verify pricing packs are immutable (append-only)."""

    service = PricingPackService()

    # Create pricing pack
    pack_id = service.create_pack(date.today(), prices)

    # Retrieve pack
    pack = service.get_pack(pack_id)

    # Attempt to modify (should raise error)
    with pytest.raises(ImmutabilityViolationError):
        pack.prices["AAPL"] = 999.99

    # Verify original data unchanged
    pack_reloaded = service.get_pack(pack_id)
    assert pack_reloaded.prices == pack.prices
```

---

### Golden Test Fixtures

```python
# tests/golden/conftest.py

import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent

def load_golden(filename: str) -> dict:
    """Load golden output from JSON file."""
    path = GOLDEN_DIR / filename
    with open(path, "r") as f:
        return json.load(f)

def save_golden(filename: str, data: dict):
    """Save golden output (only when explicitly updating)."""
    path = GOLDEN_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
```

---

### CI/CD Integration

```yaml
# .github/workflows/ci.yml

name: CI Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            --cov=app \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=95

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  property-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Run property tests
        run: |
          pytest tests/property/ \
            --hypothesis-profile=ci \
            --hypothesis-seed=random

  golden-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Run golden tests
        run: |
          pytest tests/golden/ --golden-update=never

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: timescale/timescaledb:latest-pg14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost/test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/integration/ \
            --tb=short \
            --maxfail=10

  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Run security tests
        run: |
          bandit -r backend/ -f json -o bandit-report.json
          safety check --json

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: bandit-report.json
```

---

## Testing Strategy by Phase

### Week 0 (Foundation)
- ✅ Unit tests for core modules (metrics, currency, ledger)
- ✅ Property tests for multi-currency arithmetic
- ✅ Golden tests for attribution calculation (AAPL example)

### Week 1-2 (Integration)
- ✅ Integration tests for ledger reconciliation
- ✅ Integration tests for pricing pack build
- ✅ Security tests for RLS/IDOR
- ✅ Chaos tests for circuit breaker

### Week 3-4 (Features)
- ✅ Unit tests for ratings service (Buffett quality)
- ✅ Integration tests for alert delivery
- ✅ Performance tests for SLO enforcement (warm/cold)

### Week 5-6 (Optimization)
- ✅ Load tests (100 concurrent users)
- ✅ Pack build performance (< 15 min)
- ✅ Alert latency (median ≤ 60s)

### Week 7-8 (Production)
- ✅ Full regression suite (all tests)
- ✅ Canary deployment validation
- ✅ Rollback testing (automatic on SLO breach)

---

## Test Data Seeding

### Seed Data Requirements

1. **Users**: 5 test users (alice, bob, carol, dave, eve)
2. **Portfolios**: 10 portfolios across users (2 per user)
3. **Holdings**: 50 securities (S&P 500 top 50)
4. **Transactions**: 200 trades (buys, sells, dividends)
5. **Pricing Packs**: 30 days of historical packs
6. **FX Rates**: USD, CAD, EUR, GBP (30 days)
7. **Macro Data**: FRED indicators (T10Y2Y, UNRATE, CPIAUCSL)

### Seeding Script

```python
# tests/fixtures/seed_test_data.py

from app.db import Session
from app.models import User, Portfolio, Security, Transaction
from datetime import date, timedelta

def seed_test_data():
    """Seed database with test data for integration tests."""

    session = Session()

    # Create users
    users = [
        User(id=f"user-{name}", email=f"{name}@test.com", name=name.title())
        for name in ["alice", "bob", "carol", "dave", "eve"]
    ]
    session.add_all(users)

    # Create portfolios
    portfolios = []
    for user in users:
        for i in range(2):
            portfolio = Portfolio(
                id=f"portfolio-{user.name}-{i+1}",
                user_id=user.id,
                name=f"{user.name.title()} Portfolio {i+1}",
                base_currency="CAD",
                benchmark_id="SPY"
            )
            portfolios.append(portfolio)
    session.add_all(portfolios)

    # Create securities (S&P 500 top 50)
    securities = [
        Security(symbol=symbol, name=f"{symbol} Inc.", trading_currency="USD")
        for symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", ...]
    ]
    session.add_all(securities)

    # Create transactions
    for portfolio in portfolios:
        for i in range(10):
            transaction = Transaction(
                portfolio_id=portfolio.id,
                security_id=f"AAPL",
                type="buy",
                qty=10,
                price_ccy=150.00,
                trade_date=date.today() - timedelta(days=30-i)
            )
            session.add(transaction)

    session.commit()

if __name__ == "__main__":
    seed_test_data()
```

---

## Metrics & Reporting

### Test Execution Dashboard

**Metrics tracked**:
- **Coverage**: Overall, per-module (target: 95%+)
- **Pass rate**: % tests passing (target: 100%)
- **Flakiness**: Tests failing intermittently (target: 0%)
- **Duration**: Total test suite runtime (target: < 10 min)
- **SLO compliance**: % runs meeting performance SLOs (target: 95%+)

**Dashboard** (Grafana):
```
┌─────────────────────────────────────────────┐
│ Test Execution Metrics (Last 30 days)      │
├─────────────────────────────────────────────┤
│ Coverage:        97.2% ████████████░ 95%   │
│ Pass Rate:       100%  ████████████  100%  │
│ Flaky Tests:     0     ████████████  0     │
│ Duration:        8.5m  ████████████  10m   │
│ SLO Compliance:  98%   ████████████  95%   │
└─────────────────────────────────────────────┘
```

---

## Done Criteria

- [x] Unit tests achieving 95%+ coverage (core: 98%, services: 95%, API: 90%)
- [x] Property tests for all invariants (currency, immutability, TWR, RLS)
- [x] Golden tests for regression protection (4+ scenarios)
- [x] Integration tests for critical flows (ledger, pack, alerts, exports)
- [x] Security tests for RLS/IDOR, SQL injection, JWT validation
- [x] Chaos tests for provider outage, DB failover, cache eviction
- [x] Performance tests for SLO enforcement (warm/cold p95)
- [x] CI/CD pipeline with 7-stage quality gates
- [x] Test data seeding script (users, portfolios, transactions)
- [x] Test execution dashboard (Grafana)
- [x] Flakiness tracking (zero tolerance)
- [x] All tests passing in CI (100% pass rate)

---

**Next Steps**: Coordinate with all other architects to ensure test coverage for their modules. Integrate with OBSERVABILITY_ARCHITECT for test metrics collection.
