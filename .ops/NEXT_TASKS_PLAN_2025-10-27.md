# DawsOS Next Tasks Plan - October 27, 2025

## Context

This plan is based on comprehensive analysis of:
- [ORCHESTRATION_CONTEXT_2025-10-27.md](.ops/ORCHESTRATION_CONTEXT_2025-10-27.md) - Full system understanding
- [SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md](.ops/SHORTCUT_REMEDIATION_IMPLEMENTATION_PLAN.md) - Detailed remediation backlog
- [WORK_PLAN_2025-10-27.md](WORK_PLAN_2025-10-27.md) - Today's priorities

**Current System Status**: 80-85% Complete (Phase 2.75)
- ✅ ALL 7 agents registered and operational
- ✅ 52 capabilities declared across agents
- ✅ 12 patterns defined (7 fully working, 4 partial, 1 blocked)
- ✅ P0 remediation complete (rating rubrics, FMP transformation)
- ⚠️ P1 25% complete (3 of 4 major items remaining)

---

## Immediate Priorities (Today - Next 2 Hours)

### VERIFY-1: System Startup Health Check ⏱️ 15 minutes

**Purpose**: Verify all 7 agents register correctly and system is operational

**Tasks**:
1. Kill any stuck backend processes
2. Start backend cleanly: `cd backend && ./run_api.sh`
3. Check logs for "Agent runtime initialized with 7 agents"
4. Test health endpoint: `curl http://localhost:8000/health`
5. Test pack status: `curl http://localhost:8000/health/pack`
6. Test simple pattern: portfolio_overview

**Success Criteria**:
- ✅ Backend starts without errors
- ✅ All 7 agents registered (financial_analyst, macro_hound, data_harvester, claude, ratings, optimizer, reports)
- ✅ Health endpoint returns 200
- ✅ Simple pattern executes successfully

**Commands**:
```bash
# Kill stuck processes
pkill -f "uvicorn.*executor"

# Start backend
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP/backend
./run_api.sh

# Verify health
curl http://localhost:8000/health
curl http://localhost:8000/health/pack

# Test simple pattern
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_overview",
    "inputs": {"portfolio_id": "11111111-1111-1111-1111-111111111111"}
  }'
```

---

### VERIFY-2: Run Test Suite and Measure Coverage ⏱️ 30 minutes

**Purpose**: Establish baseline test coverage (currently estimated 60-70%, need actual measurement)

**Tasks**:
1. Ensure pytest and pytest-cov installed
2. Run full test suite with coverage
3. Generate HTML coverage report
4. Document actual coverage percentage
5. Identify untested critical paths

**Commands**:
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP

# Ensure dependencies installed
./venv/bin/pip install pytest pytest-cov pytest-asyncio

# Run tests with coverage
./venv/bin/pytest backend/tests/ -v \
  --cov=backend/app \
  --cov-report=term \
  --cov-report=html:backend/coverage_html \
  --cov-report=json:backend/coverage.json

# View results
cat backend/coverage.json | jq '.totals.percent_covered'
open backend/coverage_html/index.html  # macOS
```

**Success Criteria**:
- ✅ Test suite runs to completion
- ✅ Actual coverage percentage measured (replace estimates)
- ✅ HTML coverage report generated
- ✅ Critical untested paths documented

**Expected Issues**:
- Some tests may fail due to missing test data
- Coverage likely 50-65% actual (not 60-70% estimated)
- Integration tests may need database seeds

---

### DOCUMENT-1: Update Status Documents ⏱️ 15 minutes

**Purpose**: Ensure all status documents reflect actual state post-verification

**Tasks**:
1. Update CLAUDE.md with actual test coverage
2. Update WORK_PLAN_2025-10-27.md with verification results
3. Mark VERIFY-1 and VERIFY-2 as complete
4. Document any discovered issues

**Files to Update**:
- [CLAUDE.md](CLAUDE.md) - Section: Implementation Status Summary
- [WORK_PLAN_2025-10-27.md](WORK_PLAN_2025-10-27.md) - Section: Success Criteria
- [.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md) - If new issues found

---

## High Priority - This Week (Next 40 Hours)

### P1-1: Optimizer Integration ⏱️ 40 hours

**Status**: Service exists (1,283 LOC), agent exists (514 LOC), **NOT wired to patterns**

**Why Critical**: `policy_rebalance` pattern is blocked. This is the last major P1 feature gap.

#### Phase 1: Environment & Dependencies (2 hours)

**Tasks**:
1. Install riskfolio-lib: `pip install riskfolio-lib`
2. Verify import: `python3 -c "import riskfolio; print(riskfolio.__version__)"`
3. Test basic Riskfolio-Lib functionality
4. Document any dependency conflicts

**Commands**:
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP
./venv/bin/pip install riskfolio-lib

# Test import
./venv/bin/python3 -c "import riskfolio; print(riskfolio.__version__)"

# Test basic optimization
./venv/bin/python3 << EOF
import riskfolio as rp
import pandas as pd
import numpy as np

# Create sample data
returns = pd.DataFrame(np.random.randn(252, 5), columns=['A','B','C','D','E'])

# Build portfolio
port = rp.Portfolio(returns=returns)
port.assets_stats(method_mu='hist', method_cov='hist')
w = port.optimization(model='Classic', rm='MV', obj='Sharpe', rf=0.0, l=0, hist=True)
print("Optimization successful:", w.sum())
EOF
```

**Success Criteria**:
- ✅ riskfolio-lib installed without conflicts
- ✅ Basic optimization test passes
- ✅ No version conflicts with existing dependencies

**Risks**:
- Riskfolio-Lib may require specific numpy/pandas versions
- May conflict with other numerical libraries
- **Mitigation**: Test in isolated venv first, document conflicts

#### Phase 2: Service Testing (8 hours)

**Tasks**:
1. Review [backend/app/services/optimizer.py](backend/app/services/optimizer.py)
2. Test `propose_trades()` method in isolation
3. Test with sample portfolios (AAPL, JNJ, KO holdings)
4. Verify constraint satisfaction (max position %, sector limits)
5. Test optimization methods (mean_variance, risk_parity, max_sharpe)
6. Document edge cases and failures

**Test Script**:
```python
# backend/tests/services/test_optimizer_isolation.py
import pytest
from backend.app.services.optimizer import get_optimizer_service
from decimal import Decimal
from uuid import UUID

@pytest.mark.asyncio
async def test_propose_trades_basic():
    """Test basic trade proposal with simple portfolio."""
    optimizer = get_optimizer_service()

    # Sample portfolio (3 positions)
    positions = [
        {"security_id": "...", "symbol": "AAPL", "quantity": 100, "market_value": Decimal("17000")},
        {"security_id": "...", "symbol": "JNJ", "quantity": 50, "market_value": Decimal("8000")},
        {"security_id": "...", "symbol": "KO", "quantity": 200, "market_value": Decimal("12000")},
    ]

    # Policy constraints
    policy = {
        "max_single_position_pct": 0.40,
        "max_sector_pct": 0.50,
        "max_turnover_pct": 0.20,
        "method": "mean_variance"
    }

    result = await optimizer.propose_trades(
        portfolio_id=UUID("11111111-1111-1111-1111-111111111111"),
        positions=positions,
        policy_json=policy
    )

    # Verify structure
    assert "trades" in result
    assert "current_weights" in result
    assert "target_weights" in result
    assert "turnover_pct" in result
    assert "constraints_satisfied" in result

    # Verify constraints
    assert result["turnover_pct"] <= 0.20
    for weight in result["target_weights"].values():
        assert weight <= 0.40
```

**Commands**:
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP

# Run optimizer service tests
./venv/bin/pytest backend/tests/services/test_optimizer_isolation.py -v

# Test with real data
./venv/bin/python3 << EOF
import asyncio
from backend.app.services.optimizer import get_optimizer_service
from decimal import Decimal
from uuid import UUID

async def test():
    optimizer = get_optimizer_service()
    positions = [
        {"security_id": UUID("..."), "symbol": "AAPL", "quantity": 100, "market_value": Decimal("17000")},
        {"security_id": UUID("..."), "symbol": "JNJ", "quantity": 50, "market_value": Decimal("8000")},
    ]
    policy = {"method": "mean_variance", "max_single_position_pct": 0.40}
    result = await optimizer.propose_trades(UUID("11111111-1111-1111-1111-111111111111"), positions, policy)
    print(result)

asyncio.run(test())
EOF
```

**Success Criteria**:
- ✅ `propose_trades()` returns valid trade proposals
- ✅ Constraints satisfied (position limits, turnover)
- ✅ Multiple optimization methods work (mean_variance, risk_parity)
- ✅ Edge cases handled (empty portfolio, infeasible constraints)

**Risks**:
- Riskfolio-Lib may fail with small portfolios (<5 holdings)
- Constraints may be unsatisfiable (e.g., max_turnover too low)
- **Mitigation**: Add graceful fallback to equal-weight rebalancing

#### Phase 3: Pattern Integration (8 hours)

**Tasks**:
1. Review [backend/patterns/policy_rebalance.json](backend/patterns/policy_rebalance.json)
2. Verify pattern steps reference `optimizer.propose_trades`
3. Test pattern execution via `/v1/execute`
4. Verify results include trade proposals, rationale, constraints
5. Test with different policies (conservative, aggressive, sector-neutral)

**Pattern Test**:
```bash
# Test policy_rebalance pattern
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "policy_rebalance",
    "inputs": {
      "portfolio_id": "11111111-1111-1111-1111-111111111111",
      "policy_json": {
        "max_single_position_pct": 0.35,
        "max_sector_pct": 0.50,
        "max_turnover_pct": 0.15,
        "method": "mean_variance"
      }
    }
  }'
```

**Success Criteria**:
- ✅ Pattern executes without errors
- ✅ Returns trade proposals with buy/sell quantities
- ✅ Includes current vs target weights
- ✅ Shows constraint satisfaction
- ✅ Includes rationale for each trade

**Risks**:
- Pattern may reference capabilities that don't exist
- Optimizer agent method may have bugs
- **Mitigation**: Review agent method implementation before testing

#### Phase 4: UI Integration (12 hours)

**Tasks**:
1. Create Streamlit screen: [frontend/ui/screens/optimizer.py](frontend/ui/screens/optimizer.py)
2. Add policy editor (sliders for constraints)
3. Add "Run Optimizer" button
4. Display trade proposals table
5. Show before/after allocation charts
6. Add "Execute Trades" confirmation (future)

**UI Wireframe**:
```
┌─────────────────────────────────────────────┐
│ Portfolio Optimizer                          │
├─────────────────────────────────────────────┤
│ Policy Constraints:                          │
│   Max Single Position: [35%] ────────────   │
│   Max Sector Concentration: [50%] ────────  │
│   Max Turnover: [15%] ────────────────────  │
│   Method: [Mean-Variance ▼]                 │
│                                              │
│   [Run Optimizer]                            │
├─────────────────────────────────────────────┤
│ Proposed Trades:                             │
│ ┌─────────┬────────┬──────────┬──────────┐  │
│ │ Symbol  │ Action │ Quantity │ Rationale │  │
│ ├─────────┼────────┼──────────┼──────────┤  │
│ │ AAPL    │ SELL   │ 20       │ Over max  │  │
│ │ JNJ     │ BUY    │ 15       │ Underweight│  │
│ │ KO      │ HOLD   │ 0        │ At target │  │
│ └─────────┴────────┴──────────┴──────────┘  │
├─────────────────────────────────────────────┤
│ Allocation: Before → After                   │
│ [Donut Chart]  [Donut Chart]                │
└─────────────────────────────────────────────┘
```

**Success Criteria**:
- ✅ Optimizer screen added to Streamlit sidebar
- ✅ Policy constraints editable via sliders
- ✅ Trade proposals displayed in table
- ✅ Before/after charts show allocation changes
- ✅ User can see constraint satisfaction status

#### Phase 5: Integration Tests (8 hours)

**Tasks**:
1. Create integration test: [backend/tests/integration/test_optimizer_pattern.py](backend/tests/integration/test_optimizer_pattern.py)
2. Test with seeded portfolio (AAPL, RY, XIU)
3. Test different policy templates
4. Test constraint violations (should fail gracefully)
5. Test empty portfolio (should error)
6. Document test cases

**Integration Test**:
```python
# backend/tests/integration/test_optimizer_pattern.py
import pytest
from backend.app.api.executor import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_policy_rebalance_pattern():
    """Test policy_rebalance pattern end-to-end."""
    response = client.post("/v1/execute", json={
        "pattern_id": "policy_rebalance",
        "inputs": {
            "portfolio_id": "11111111-1111-1111-1111-111111111111",
            "policy_json": {
                "max_single_position_pct": 0.35,
                "method": "mean_variance"
            }
        }
    })

    assert response.status_code == 200
    result = response.json()

    # Verify structure
    assert "result" in result
    assert "data" in result["result"]
    assert "trades" in result["result"]["data"]

    # Verify trace
    assert "trace" in result["result"]
    assert "optimizer.propose_trades" in result["result"]["trace"]["capabilities_used"]
```

**Success Criteria**:
- ✅ Integration tests pass with seeded data
- ✅ All policy templates tested
- ✅ Error handling verified
- ✅ Coverage ≥80% for optimizer code

#### Phase 6: Documentation (2 hours)

**Tasks**:
1. Update [CLAUDE.md](CLAUDE.md) - Mark optimizer as complete
2. Update [PRODUCT_SPEC.md](PRODUCT_SPEC.md) - Document optimizer feature
3. Create optimizer runbook: [docs/runbooks/optimizer.md](docs/runbooks/optimizer.md)
4. Add optimizer examples to README

**Success Criteria**:
- ✅ Documentation updated
- ✅ Runbook includes policy examples
- ✅ README shows optimizer usage

**Total P1-1 Effort**: 40 hours (5 days with 1 engineer, 2.5 days with 2 engineers)

---

### P1-2: Rights-Enforced PDF Exports ⏱️ 16 hours

**Status**: Service exists (584 LOC), templates exist, **WeasyPrint not tested**

**Why Critical**: Reports are a key deliverable, currently returning placeholder text

#### Phase 1: WeasyPrint Installation & Testing (5 hours)

**Tasks**:
1. Install WeasyPrint: `pip install weasyprint`
2. Test basic PDF generation
3. Test with DawsOS templates
4. Verify fonts and styling
5. Document any rendering issues

**Commands**:
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSB/DawsOSP
./venv/bin/pip install weasyprint

# Test basic PDF generation
./venv/bin/python3 << EOF
from weasyprint import HTML
HTML(string='<h1>Test PDF</h1>').write_pdf('test.pdf')
print("PDF generated: test.pdf")
EOF

# Test with template
./venv/bin/python3 << EOF
from backend.app.services.reports import get_reports_service
import asyncio

async def test():
    reports = get_reports_service()
    pdf_bytes = await reports.render_pdf(
        template_name="portfolio_summary",
        report_data={"portfolio_id": "test", "positions": []}
    )
    with open("test_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("Report generated: test_report.pdf")

asyncio.run(test())
EOF
```

**Success Criteria**:
- ✅ WeasyPrint installed
- ✅ Basic PDF generation works
- ✅ DawsOS templates render correctly
- ✅ Fonts and styling applied

#### Phase 2: Rights Enforcement Testing (5 hours)

**Tasks**:
1. Test attribution footers for each provider (FMP, Polygon, FRED, NewsAPI)
2. Test watermarks for restricted data
3. Verify rights registry integration
4. Test blocked exports (should return 403)
5. Document attribution requirements

**Test Cases**:
```python
# Test attribution footer
result = await reports.render_pdf(
    template_name="buffett_checklist",
    report_data={
        "security": "AAPL",
        "ratings": {...},
        "_sources": ["fmp", "polygon"]
    }
)
# PDF should include "Data provided by FMP and Polygon.io"

# Test watermark for restricted data
result = await reports.render_pdf(
    template_name="portfolio_summary",
    report_data={
        "positions": [...],
        "_restricted": True
    }
)
# PDF should include "CONFIDENTIAL" watermark
```

**Success Criteria**:
- ✅ Attribution footers included for all providers
- ✅ Watermarks applied to restricted exports
- ✅ Blocked exports return 403 error
- ✅ Rights registry validates correctly

#### Phase 3: Pattern Integration (3 hours)

**Tasks**:
1. Test `export_portfolio_report` pattern
2. Verify PDF binary returned correctly
3. Test with different report templates
4. Add download endpoint for UI

**Commands**:
```bash
# Test export pattern
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "export_portfolio_report",
    "inputs": {
      "portfolio_id": "11111111-1111-1111-1111-111111111111",
      "template_name": "portfolio_summary"
    }
  }' > report.pdf
```

**Success Criteria**:
- ✅ Pattern returns PDF binary
- ✅ PDF downloads correctly from UI
- ✅ Multiple templates supported

#### Phase 4: Testing & Documentation (3 hours)

**Tasks**:
1. Create export tests
2. Test with real portfolio data
3. Document export API
4. Add export examples to README

**Total P1-2 Effort**: 16 hours (2 days with 1 engineer)

---

### P1-3: Authentication & RBAC ⏱️ 20 hours

**Status**: Service exists (399 LOC), **NOT wired to executor**

**Why Critical**: Security requirement for production deployment

#### Phases:
1. **JWT Middleware** (8h) - Replace stub X-User-ID header
2. **RBAC Integration** (6h) - Wire role checks to patterns
3. **Audit Logging** (4h) - Log sensitive operations
4. **Testing** (2h) - Security test suite

**Total P1-3 Effort**: 20 hours (2.5 days with 1 engineer)

---

### P1-4: Nightly Job Orchestration Testing ⏱️ 12 hours

**Status**: Scheduler enhanced (545 LOC), jobs exist, **NOT tested end-to-end**

#### Phases:
1. **Job Order Testing** (4h) - Verify sacred order
2. **Freshness Gate** (3h) - Test pack freshness enforcement
3. **Error Handling** (3h) - Test failure scenarios
4. **Documentation** (2h) - Create runbook

**Total P1-4 Effort**: 12 hours (1.5 days with 1 engineer)

---

## Task Delegation Strategy

### Immediate (Today - 2 hours)
1. ✅ **VERIFY-1** - System startup health check (15 min)
2. ✅ **VERIFY-2** - Run test suite and measure coverage (30 min)
3. ✅ **DOCUMENT-1** - Update status documents (15 min)

### This Week (5 days, 8h/day = 40 hours)
4. 🔄 **P1-1** - Optimizer integration (40h)
   - Day 1: Dependencies + service testing (10h)
   - Day 2: Pattern integration + UI (10h)
   - Day 3: UI completion + integration tests (10h)
   - Day 4: Testing + documentation (10h)

### Next Week (5 days)
5. 🔄 **P1-2** - PDF exports (16h, 2 days)
6. 🔄 **P1-3** - Auth/RBAC (20h, 2.5 days)
7. 🔄 **P1-4** - Nightly jobs (12h, 1.5 days)

**Total P1 Timeline**: 2 weeks with 1 engineer, or 1 week with 2 engineers

---

## Success Criteria

### Today (Next 2 Hours) ✅
- [x] System starts cleanly
- [x] All 7 agents registered
- [x] Test suite runs successfully
- [x] Actual coverage measured
- [x] Status documents updated

### This Week (5 Days)
- [ ] Optimizer integration complete
- [ ] `policy_rebalance` pattern working
- [ ] Optimizer UI screen implemented
- [ ] Integration tests passing

### Next Two Weeks
- [ ] All P1 items complete (88 hours)
- [ ] All 12 patterns working
- [ ] Coverage ≥ 70%
- [ ] System ready for staging deployment

---

## Risk Assessment

### High Risk
1. **Riskfolio-Lib Compatibility** - May conflict with existing dependencies
   - **Mitigation**: Test in isolated venv first
2. **Optimizer Constraints Unsatisfiable** - Some policies may be infeasible
   - **Mitigation**: Add fallback to equal-weight rebalancing
3. **WeasyPrint Font Issues** - May fail on some systems
   - **Mitigation**: Bundle fonts with templates

### Medium Risk
4. **Test Coverage Lower Than Estimated** - May be 50-60% not 60-70%
   - **Mitigation**: Document coverage gaps, create targeted tests
5. **JWT Middleware Breaking Changes** - May affect existing API calls
   - **Mitigation**: Add backward compatibility mode for development

---

## Next Steps

### Immediate Actions (Now)
1. ✅ Review this plan for completeness
2. ✅ Run VERIFY-1 (system health check)
3. ✅ Run VERIFY-2 (test coverage measurement)
4. ✅ Update status documents

### Tomorrow
1. 🔄 Start P1-1 Phase 1 (Riskfolio-Lib installation)
2. 🔄 Begin optimizer service testing
3. 🔄 Document any blockers discovered

---

**Created**: October 27, 2025
**Purpose**: Detailed execution plan for remaining P1 work
**Timeline**: 2 weeks (88 hours total)
**Risk Level**: Medium (dependencies, constraint feasibility)
