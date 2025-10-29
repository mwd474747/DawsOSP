# End-to-End UI-Backend Integration Audit & Fix Plan
**Date**: October 28, 2025
**Status**: 🔴 CRITICAL ISSUES IDENTIFIED
**Completion Estimate**: 60-65% (down from claimed 80-85%)

---

## Executive Summary

This audit identifies every breaking issue when the Next.js UI attempts to communicate with the FastAPI backend. Each issue is referenced with exact file paths and line numbers for immediate remediation.

**Key Findings**:
- ✅ API contract (pattern vs pattern_id) is actually CORRECT - API client maps internally
- 🔴 Authentication is broken (no /auth/logout, bcrypt not in venv)
- 🔴 Multiple agents have broken import paths (from app. instead of from backend.app.)
- 🔴 Pattern-capability name mismatches will cause execution failures
- 🔴 Hardcoded portfolio IDs will fail UUID validation
- 🔴 Missing pattern inputs will cause agent errors

---

## 1. API Contract Issues

### ✅ ISSUE 1.1: Pattern vs Pattern_ID (FALSE ALARM)
**Status**: ALREADY FIXED
**Location**: [dawsos-ui/src/lib/api-client.ts:220](dawsos-ui/src/lib/api-client.ts#L220)

**Initial Report**: UI sends `{pattern: 'x'}` but backend expects `{pattern_id: 'x'}`

**Reality**: API client correctly maps:
```typescript
async executePattern(request: ExecuteRequest): Promise<ExecuteResponse> {
  const response = await this.client.post<ExecuteResponse>('/v1/execute', {
    pattern_id: request.pattern,  // ✅ Correctly maps pattern → pattern_id
    inputs: request.inputs,
    require_fresh: request.require_fresh || false
  });
  return response.data;
}
```

**Action**: None needed - working as designed

---

### 🔴 ISSUE 1.2: Missing /auth/logout Endpoint
**Status**: BROKEN
**Severity**: MEDIUM (breaks logout UX, not critical)
**Location**:
- UI calls: [dawsos-ui/src/lib/api-client.ts:202-210](dawsos-ui/src/lib/api-client.ts#L202-L210)
- Backend: [backend/app/api/routes/auth.py](backend/app/api/routes/auth.py) (endpoint missing)

**Problem**: UI calls `/auth/logout` but endpoint doesn't exist

**Current Code** (API Client):
```typescript
async logout(): Promise<void> {
  try {
    await this.client.post('/auth/logout');  // ❌ 404 Not Found
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    this.clearAuthToken();  // This works, but server-side token isn't blacklisted
  }
}
```

**Fix Options**:

**Option A: Add Endpoint** (Recommended)
```python
# backend/app/api/routes/auth.py
@router.post("/logout")
async def logout(claims: Dict = Depends(verify_token)):
    """
    Logout user and blacklist JWT token.

    Adds token to blacklist so it can't be reused.
    """
    try:
        auth_service = get_auth_service()

        # Extract token from request headers
        # (You'll need to modify verify_token to return both claims and raw token)
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        await auth_service.logout_user(
            token=token,
            user_id=claims["user_id"]
        )

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
```

**Option B: Remove UI Call** (Quick Fix)
```typescript
// dawsos-ui/src/lib/api-client.ts
async logout(): Promise<void> {
  // Skip server call, just clear local token
  this.clearAuthToken();
}
```

**Recommendation**: Use Option B for now (client-side logout), add Option A later when implementing token blacklist properly.

---

### 🔴 ISSUE 1.3: Hardcoded Portfolio IDs
**Status**: BROKEN
**Severity**: CRITICAL
**Affected Components**:
- [dawsos-ui/src/components/PortfolioOverview.tsx:12](dawsos-ui/src/components/PortfolioOverview.tsx#L12)
- [dawsos-ui/src/components/HoldingsDetail.tsx:13](dawsos-ui/src/components/HoldingsDetail.tsx#L13)
- [dawsos-ui/src/components/Scenarios.tsx:11](dawsos-ui/src/components/Scenarios.tsx#L11)
- [dawsos-ui/src/components/BuffettChecklist.tsx:10](dawsos-ui/src/components/BuffettChecklist.tsx#L10)
- [dawsos-ui/src/components/PolicyRebalance.tsx:10](dawsos-ui/src/components/PolicyRebalance.tsx#L10)

**Problem**: UI hardcodes `"main-portfolio"` but backend expects UUID

**Current Code**:
```typescript
const portfolioId = "main-portfolio";  // ❌ Not a valid UUID
const { data, isLoading, error } = usePortfolioOverview(portfolioId);
```

**Backend Validation** ([backend/app/agents/financial_analyst.py:94](backend/app/agents/financial_analyst.py#L94)):
```python
async def ledger_positions(self, inputs: dict) -> dict:
    portfolio_id = UUID(inputs["portfolio_id"])  # ❌ ValueError: badly formed hexadecimal UUID string
```

**Fix Options**:

**Option A: Fetch Real Portfolio** (Recommended)
```typescript
// 1. Add endpoint to get user's default portfolio
// backend/app/api/routes/portfolios.py (create if doesn't exist)
@router.get("/portfolios/default")
async def get_default_portfolio(claims: Dict = Depends(verify_token)):
    """Get user's default portfolio."""
    user_id = claims["user_id"]

    portfolio = await execute_query_one(
        """
        SELECT id, name FROM portfolios
        WHERE user_id = $1
        ORDER BY created_at ASC
        LIMIT 1
        """,
        UUID(user_id)
    )

    if not portfolio:
        raise HTTPException(404, "No portfolio found")

    return {"id": str(portfolio["id"]), "name": portfolio["name"]}

// 2. Update UI to fetch it
// dawsos-ui/src/lib/api-client.ts
async getDefaultPortfolio(): Promise<{ id: string; name: string }> {
  const response = await this.client.get('/portfolios/default');
  return response.data;
}

// 3. Use in components
const { data: portfolio } = useQuery({
  queryKey: ['default-portfolio'],
  queryFn: () => apiClient.getDefaultPortfolio()
});
const portfolioId = portfolio?.id || null;
```

**Option B: Create UUID Mapping** (Quick Fix)
```typescript
// dawsos-ui/src/lib/constants.ts
export const PORTFOLIO_ID_MAP: Record<string, string> = {
  "main-portfolio": "11111111-1111-1111-1111-111111111111"  // Use real UUID from DB
};

// In components:
const portfolioId = PORTFOLIO_ID_MAP["main-portfolio"];
```

**Option C: Seed Default Portfolio** (Database Fix)
```sql
-- Create a well-known default portfolio for testing
INSERT INTO portfolios (id, user_id, name, created_at)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  '50388565-976a-4580-9c01-c67e8b318d91',  -- michael@dawsos.com
  'Main Portfolio',
  NOW()
) ON CONFLICT (id) DO NOTHING;
```

**Recommendation**: Use Option C + Option B immediately, then implement Option A properly.

---

## 2. Authentication Issues

### 🔴 ISSUE 2.1: Bcrypt Not Installed
**Status**: BROKEN
**Severity**: CRITICAL
**Location**: venv dependencies

**Problem**: `bcrypt` module not in venv, password verification will fail

**Fix**:
```bash
./venv/bin/pip install bcrypt passlib[bcrypt]
```

**Verification**:
```bash
./venv/bin/python -c "import bcrypt; print('✅ bcrypt installed')"
```

---

### 🔴 ISSUE 2.2: No Seeded Users (ALREADY FIXED)
**Status**: ✅ FIXED (michael@dawsos.com created)
**Location**: Database

**What Was Done**:
- Created michael@dawsos.com with correct bcrypt hash
- Password: `mozzuq-byfqyQ-5tefvu`
- Role: ADMIN

**Verification**:
```bash
docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c \
  "SELECT email, role FROM users WHERE email = 'michael@dawsos.com';"
```

---

## 3. Backend Agent Issues

### 🔴 ISSUE 3.1: Broken Import Paths
**Status**: BROKEN
**Severity**: CRITICAL (causes 500 errors)
**Affected Files**:
- [backend/app/agents/macro_hound.py:129](backend/app/agents/macro_hound.py#L129)
- [backend/app/agents/data_harvester.py:115](backend/app/agents/data_harvester.py#L115)
- [backend/app/agents/financial_analyst.py:781](backend/app/agents/financial_analyst.py#L781)

**Problem**: Agents import `from app.services...` instead of `from backend.app.services...`

**Example Error**:
```
ModuleNotFoundError: No module named 'app.services'
```

**Fix**: Run global find-and-replace:
```bash
find backend/app/agents -name "*.py" -exec sed -i '' 's/from app\./from backend.app./g' {} \;
```

**Verification**:
```bash
grep -r "from app\." backend/app/agents/
# Should return no results
```

---

### 🔴 ISSUE 3.2: Pattern-Capability Name Mismatches
**Status**: BROKEN
**Severity**: CRITICAL

#### Issue 3.2a: News Capabilities

**Problem**: Pattern calls `news.search` but agent exports `news_search`

**Location**:
- Pattern: [backend/patterns/news_impact_analysis.json:71-85](backend/patterns/news_impact_analysis.json#L71-L85)
- Agent: [backend/app/agents/data_harvester.py](backend/app/agents/data_harvester.py)

**Pattern Definition**:
```json
{
  "capability": "news.search",  // ❌ Uses dot notation
  "inputs": {"query": "...", "portfolio_id": "..."}
}
```

**Agent Capabilities**:
```python
def get_capabilities(self) -> list[str]:
    return [
        "news_search",  // ❌ Uses underscore notation
        "news_compute_portfolio_impact"
    ]
```

**Fix**: Update pattern to use underscore notation:
```json
{
  "capability": "news_search",  // ✅ Matches agent
  "inputs": {"query": "...", "portfolio_id": "..."}
}
```

---

### 🔴 ISSUE 3.3: Missing Pattern Inputs

#### Issue 3.3a: Buffett Checklist Needs security_id

**UI Component**: [dawsos-ui/src/components/BuffettChecklist.tsx](dawsos-ui/src/components/BuffettChecklist.tsx)
**Pattern**: [backend/patterns/buffett_checklist.json](backend/patterns/buffett_checklist.json)
**UI Sends**: `{portfolio_id: "..."}`
**Pattern Expects**: `{portfolio_id: "...", security_id: "..."}`

**Fix**: UI needs to select a security first:
```typescript
const [selectedSecurity, setSelectedSecurity] = useState<string | null>(null);

const { data } = useQuery({
  queryKey: ['buffett-checklist', portfolioId, selectedSecurity],
  queryFn: () => apiClient.executePattern({
    pattern: 'buffett_checklist',
    inputs: {
      portfolio_id: portfolioId,
      security_id: selectedSecurity  // ✅ Now provided
    }
  }),
  enabled: !!portfolioId && !!selectedSecurity  // Only run when security selected
});
```

#### Issue 3.3b: Holding Deep Dive Needs security_id

**Same issue as 3.3a** - requires security selection before execution.

#### Issue 3.3c: Policy Rebalance Needs policies/constraints

**UI Component**: [dawsos-ui/src/components/PolicyRebalance.tsx](dawsos-ui/src/components/PolicyRebalance.tsx)
**Pattern**: [backend/patterns/policy_rebalance.json](backend/patterns/policy_rebalance.json)
**Agent**: [backend/app/agents/optimizer_agent.py:311-360](backend/app/agents/optimizer_agent.py#L311-L360)

**Problem**: OptimizerAgent ignores UI-provided policies and refetches from DB

**Current Code**:
```python
async def policy_rebalance(self, inputs: dict) -> dict:
    portfolio_id = UUID(inputs["portfolio_id"])
    # ❌ Ignores inputs["policies"] and inputs["constraints"]

    # Refetch from database
    policies = await self._get_rebalance_policies(portfolio_id)
```

**Fix**: Use inputs if provided:
```python
async def policy_rebalance(self, inputs: dict) -> dict:
    portfolio_id = UUID(inputs["portfolio_id"])

    # Use provided policies or fetch from DB
    if "policies" in inputs:
        policies = inputs["policies"]
    else:
        policies = await self._get_rebalance_policies(portfolio_id)

    if "constraints" in inputs:
        constraints = inputs["constraints"]
    else:
        constraints = await self._get_constraints(portfolio_id)
```

#### Issue 3.3d: Cycle Deleveraging Needs regime

**Pattern**: [backend/patterns/cycle_deleveraging_scenarios.json](backend/patterns/cycle_deleveraging_scenarios.json)
**Agent**: [backend/app/agents/optimizer_agent.py:409-453](backend/app/agents/optimizer_agent.py#L409-L453)

**Problem**: Pattern never supplies `regime` input that agent requires

**Current Pattern**:
```json
{
  "capability": "optimizer.suggest_deleveraging_hedges",
  "inputs": {
    "portfolio_id": "{{ledger.positions.portfolio_id}}"
    // ❌ Missing "regime" input
  }
}
```

**Agent Code**:
```python
async def suggest_deleveraging_hedges(self, inputs: dict) -> dict:
    regime = inputs["regime"]  // ❌ KeyError if not provided
```

**Fix**: Pattern should derive regime from macro analysis:
```json
{
  "steps": [
    {
      "capability": "macro.detect_regime",
      "inputs": {},
      "store_as": "current_regime"
    },
    {
      "capability": "optimizer.suggest_deleveraging_hedges",
      "inputs": {
        "portfolio_id": "{{ledger.positions.portfolio_id}}",
        "regime": "{{current_regime.regime}}"  // ✅ Now provided
      }
    }
  ]
}
```

---

## 4. UI-Specific Issues

### 🔴 ISSUE 4.1: Components Show Stub Data Instead of API Results

**Problem**: Even when API calls succeed, UI falls back to demo data

**Example** ([dawsos-ui/src/components/PortfolioOverview.tsx:47-106](dawsos-ui/src/components/PortfolioOverview.tsx#L47-L106)):
```typescript
if (isLoading) {
  return <LoadingSkeleton />;
}

if (error || !data) {
  // ❌ Falls back to demo data instead of showing error
  return <DemoData />;
}

// ✅ Should be:
if (error) {
  return <ErrorDisplay error={error} />;
}

if (!data) {
  return <EmptyState />;
}

return <RealData data={data} />;
```

**Fix**: Update all components to show errors properly instead of hiding them with demo data.

---

### 🔴 ISSUE 4.2: No Event Handlers for User Interactions

**Problem**: UI doesn't capture user selections to pass to patterns

**Example** - Holdings table doesn't set security_id:
```typescript
// ❌ Current: No onClick handler
<tr key={holding.id}>
  <td>{holding.symbol}</td>
  <td>{holding.quantity}</td>
</tr>

// ✅ Should be:
<tr
  key={holding.id}
  onClick={() => setSelectedSecurity(holding.security_id)}
  className={selectedSecurity === holding.security_id ? 'selected' : ''}
>
  <td>{holding.symbol}</td>
  <td>{holding.quantity}</td>
</tr>
```

---

## 5. Infrastructure Issues

### 🔴 ISSUE 5.1: Python venv Points to Wrong Path
**Status**: BROKEN
**Severity**: HIGH

**Problem**: venv points to old DawsOSB path

**Fix**:
```bash
cd /Users/mdawson/Documents/GitHub/DawsOSP
rm -rf venv
python3.11 -m venv venv
./venv/bin/pip install -r backend/requirements.txt
```

---

### 🔴 ISSUE 5.2: No Tests for API Contracts
**Status**: MISSING
**Severity**: MEDIUM

**Problem**: No contract tests to catch payload mismatches

**Fix**: Add contract tests:
```python
# backend/tests/integration/test_api_contracts.py
import pytest
from backend.app.api.executor import ExecuteRequest

def test_execute_request_schema():
    """Verify ExecuteRequest matches UI expectations."""
    req = ExecuteRequest(
        pattern_id="portfolio_overview",
        inputs={"portfolio_id": "11111111-1111-1111-1111-111111111111"}
    )
    assert req.pattern_id == "portfolio_overview"
    assert "portfolio_id" in req.inputs

def test_pattern_execution_response():
    """Verify response format matches UI expectations."""
    # Test that response has required fields
    pass
```

---

### 🔴 ISSUE 5.3: Knowledge Graph Not Implemented
**Status**: NOT STARTED (0%)
**Severity**: LOW (future feature)

**Problem**: UI plan assumes KG/RAG but backend has no Neo4j integration

**Fix**: Don't expose KG features in UI until:
1. Neo4j container added to docker-compose
2. Graph service implemented
3. Ingestion pipeline created
4. RAG endpoints added

---

## 6. Complete Fix Checklist

### Immediate (Day 1) - Critical Path to Working UI

- [ ] **Fix 1**: Install bcrypt in venv
  ```bash
  ./venv/bin/pip install bcrypt passlib[bcrypt]
  ```

- [ ] **Fix 2**: Seed default portfolio
  ```sql
  INSERT INTO portfolios (id, user_id, name, created_at)
  VALUES (
    '11111111-1111-1111-1111-111111111111',
    '50388565-976a-4580-9c01-c67e8b318d91',
    'Main Portfolio',
    NOW()
  );
  ```

- [ ] **Fix 3**: Update UI components to use real UUID
  ```typescript
  const PORTFOLIO_ID = "11111111-1111-1111-1111-111111111111";
  ```

- [ ] **Fix 4**: Fix agent import paths
  ```bash
  find backend/app/agents -name "*.py" -exec sed -i '' 's/from app\./from backend.app./g' {} \;
  ```

- [ ] **Fix 5**: Disable RLS on users table (already done)

- [ ] **Fix 6**: Implement simple logout (client-side only)
  ```typescript
  async logout(): Promise<void> {
    this.clearAuthToken();
  }
  ```

### Short-term (Week 1) - Pattern Execution Fixes

- [ ] **Fix 7**: Update news_impact_analysis pattern
  - Change `news.search` → `news_search`
  - Change `news.compute_portfolio_impact` → `news_compute_portfolio_impact`

- [ ] **Fix 8**: Fix cycle_deleveraging_scenarios pattern
  - Add `macro.detect_regime` step
  - Pass regime to `optimizer.suggest_deleveraging_hedges`

- [ ] **Fix 9**: Fix optimizer_agent to use input policies
  - Check for `inputs["policies"]` before refetching

- [ ] **Fix 10**: Add security selection to UI components
  - Buffett Checklist: Add holdings selector
  - Holding Deep Dive: Add holdings selector
  - Policy Rebalance: Add policy editor

### Medium-term (Week 2-3) - Polish & Error Handling

- [ ] **Fix 11**: Replace demo data fallbacks with proper error displays

- [ ] **Fix 12**: Add event handlers for user interactions

- [ ] **Fix 13**: Implement /auth/logout endpoint with token blacklist

- [ ] **Fix 14**: Add /portfolios/default endpoint

- [ ] **Fix 15**: Add contract tests for API payloads

- [ ] **Fix 16**: Rebuild Python venv from scratch

### Long-term (Month 2+) - Advanced Features

- [ ] **Fix 17**: Implement Knowledge Graph
  - Add Neo4j container
  - Build graph service
  - Create ingestion pipeline
  - Add RAG endpoints

- [ ] **Fix 18**: Add comprehensive test coverage
  - E2E tests for all patterns
  - UI component tests
  - API integration tests

---

## 7. Updated Completion Estimate

| Component | Previous Estimate | Actual Status | Notes |
|-----------|-------------------|---------------|-------|
| Backend API | 85% | 70% | Import paths broken, auth incomplete |
| Pattern Orchestrator | 90% | 85% | Working but patterns have bugs |
| Agents | 80% | 65% | Import errors, missing input handling |
| Patterns | 75% | 60% | Name mismatches, missing inputs |
| Authentication | 80% | 50% | Login works, logout missing, RLS disabled |
| Database | 85% | 75% | Schema good, migrations messy, RLS off |
| UI Components | 90% | 40% | Built but not wired, using demo data |
| API Client | 90% | 85% | Works but needs portfolio endpoint |
| **Overall** | **80-85%** | **60-65%** | Critical bugs block E2E flow |

---

## 8. Risk Assessment

### High Risk (Blocks MVP)
1. ✅ Authentication (partially fixed - login works)
2. 🔴 Portfolio ID mismatch (blocks all pattern execution)
3. 🔴 Agent import paths (500 errors on pattern execution)
4. 🔴 Missing pattern inputs (execution failures)

### Medium Risk (Degrades UX)
5. 🔴 No logout endpoint
6. 🔴 UI shows demo data instead of errors
7. 🔴 No user interaction handlers

### Low Risk (Future Features)
8. Knowledge Graph not implemented
9. Limited test coverage
10. Migration script conflicts

---

## 9. Recommended Execution Order

### Phase 1: Make Login → Dashboard → Holdings Work (1 Day)
1. Install bcrypt
2. Seed default portfolio
3. Update UI to use real UUID
4. Fix agent import paths
5. Test end-to-end flow

### Phase 2: Fix Pattern Execution (3-5 Days)
6. Fix pattern capability name mismatches
7. Add missing pattern inputs
8. Update agents to use provided inputs
9. Test each pattern individually

### Phase 3: Polish UI (1 Week)
10. Replace demo data with real error handling
11. Add user interaction handlers
12. Implement proper logout
13. Add portfolio selector

### Phase 4: Production Readiness (2 Weeks)
14. Re-enable RLS with proper policies
15. Add comprehensive tests
16. Implement Knowledge Graph
17. Performance optimization

---

## 10. Success Criteria

### MVP Success (End of Phase 1)
- [ ] User can login with michael@dawsos.com
- [ ] Dashboard loads real portfolio data
- [ ] Holdings table displays positions
- [ ] No 500 errors in console
- [ ] JWT auth works for all requests

### Beta Success (End of Phase 2)
- [ ] All 9 patterns execute without errors
- [ ] Buffett Checklist works with security selection
- [ ] Scenarios page loads data
- [ ] Policy Rebalance accepts user inputs
- [ ] Macro dashboard displays current regime

### Production Ready (End of Phase 4)
- [ ] All tests passing
- [ ] RLS enabled and tested
- [ ] Error handling polished
- [ ] Performance acceptable (<2s page loads)
- [ ] Knowledge Graph integrated

---

**Document Status**: FINAL
**Last Updated**: October 28, 2025, 22:30 UTC
**Issues Identified**: 18
**Critical Issues**: 6
**Estimated Fix Time**: 2-3 weeks for MVP, 6-8 weeks for production
