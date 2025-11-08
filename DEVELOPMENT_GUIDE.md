# DawsOSP Development Guide

**Version:** 1.0
**Last Updated:** November 3, 2025
**Purpose:** Developer reference for contributing to DawsOSP

---

## Getting Started

### Development Environment Setup

**Prerequisites:**
- Python 3.11+
- PostgreSQL 14+ with TimescaleDB
- Git

**Quick Setup:**
```bash
# Clone repository
git clone https://github.com/mwd474747/DawsOSP.git
cd DawsOSP

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://localhost/dawsos"
export AUTH_JWT_SECRET="your-secret-key"
export ANTHROPIC_API_KEY="sk-ant-..."  # Optional

# Start development server
python combined_server.py
```

---

## Code Structure

### Repository Layout

```
DawsOSP/
├── combined_server.py          # ⭐ PRIMARY SERVER (6,043 lines, 59 endpoints)
├── full_ui.html                # ⭐ PRIMARY UI (React SPA, 20 pages)
├── backend/
│   ├── app/
│   │   ├── agents/             # 4 agents (financial_analyst, macro_hound, data_harvester, claude_agent)
│   │   │                       # Phase 3 consolidation complete (November 3, 2025) - 9 agents → 4 agents
│   │   ├── core/               # AgentRuntime, PatternOrchestrator
│   │   ├── services/           # Business logic
│   │   ├── db/                 # Database layer
│   │   └── auth/               # Authentication (JWT, RBAC)
│   ├── patterns/               # 15 pattern definitions (JSON)
│   ├── db/
│   │   ├── migrations/         # Sequential SQL migrations
│   │   └── seeds/              # Seed data
│   └── requirements.txt
├── frontend/
│   └── api-client.js           # API client for full_ui.html
└── .archive/                   # Historical documentation
```

---

## Architecture Overview

### Pattern Execution Flow

```
User clicks UI button
  ↓
frontend/api-client.js: executePattern()
  → POST /api/patterns/execute
    ↓
combined_server.py: execute_pattern() (line 1106)
  → Calls PatternOrchestrator
    ↓
PatternOrchestrator.run_pattern()
  → Loads JSON from backend/patterns/{pattern_id}.json
  → Executes steps sequentially with template substitution
  → Routes capabilities to AgentRuntime
    ↓
AgentRuntime.get_agent_for_capability()
  → Routes to appropriate agent
    ↓
Agent.execute() → Service.method() → Database query
  ↓
Results flow back: Agent → Orchestrator → Endpoint → UI
```

**Key Concept:** Patterns are declarative JSON workflows. The orchestrator handles execution.

### Field Naming Standards (January 14, 2025)

**Important:** Field naming is standardized across layers for consistency:

**Database Layer:**
- Use `quantity_open` and `quantity_original` in SQL queries
- Legacy `quantity` field is deprecated (see Migration 014)

**Agent Layer:**
- All agent capabilities return `quantity` (not `quantity_open` or `qty`)
- This is the standard field name for position quantities in agent responses
- Example: `ledger.positions` returns `{"quantity": Decimal("100")}`

**Service Layer:**
- Service layer can use `qty` internally (acceptable for service-to-service communication)
- When interfacing with agents, use `quantity`

**Rationale:**
- Database columns use verbose names (`quantity_open`) for clarity
- Agent API uses standardized `quantity` for consistency
- Service layer can use abbreviations (`qty`) for internal APIs

**See Also:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - Field naming standards section
- [DATABASE.md](DATABASE.md) - Database field naming and migrations
- `FIELD_NAMING_SYSTEM_ANALYSIS.md` - Detailed analysis

---

## Backend Development

### Adding a New Agent

**1. Create Agent File:**
```python
# backend/app/agents/my_agent.py
from typing import Dict, List
from app.agents.base_agent import BaseAgent
from app.core.types import RequestCtx
from app.core.capability_contract import capability

class MyAgent(BaseAgent):
    """My Agent - Provides custom capabilities."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "my.capability1",
            "my.capability2"
        ]
    
    @capability(
        inputs={"portfolio_id": "uuid", "lookback_days": "integer"},
        outputs={"result": "dict"},
        status="production",
        dependencies=["pricing.apply_pack"]
    )
    async def my_capability1(
        self, 
        ctx: RequestCtx, 
        state: Dict, 
        portfolio_id: str,
        lookback_days: int = 252,
        **kwargs
    ) -> Dict:
        """
        My capability implementation.
        
        Args:
            ctx: Request context (pricing_pack_id, ledger_commit_hash, trace_id)
            state: Execution state from previous steps
            portfolio_id: Portfolio UUID
            lookback_days: Historical period in days (default: 252)
        
        Returns:
            Dict with result data
        
        Raises:
            ValueError: If portfolio_id is invalid
            PricingPackNotFoundError: If pricing pack not found
        """
        # Validate inputs
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        
        # Get database pool
        pool = self.services.get("db")
        if not pool:
            raise RuntimeError("Database pool not available")
        
        # Example: Query database
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM portfolios WHERE id = $1",
                portfolio_id
            )
        
        # Process results
        result = {
            "portfolio_id": portfolio_id,
            "data": [dict(row) for row in rows],
            "lookback_days": lookback_days
        }
        
        return result
    
    async def my_capability2(self, ctx: RequestCtx, state: Dict, **kwargs) -> Dict:
        """Another capability."""
        # Implementation
        return {"result": "data"}
```

**2. Register Agent:**
```python
# combined_server.py (in get_agent_runtime function, around line 261-300)
def get_agent_runtime(reinit_services: bool = False) -> AgentRuntime:
    services = {"db": db_pool, "redis": None}
    _agent_runtime = AgentRuntime(services)
    
    # ... existing agents ...
    
    # Register My Agent
    my_agent = MyAgent("my_agent", services)
    _agent_runtime.register_agent(my_agent)
    
    return _agent_runtime
```

**3. Use in Pattern:**
```json
{
  "id": "my_pattern",
  "steps": [
    {
      "capability": "my.capability1",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "lookback_days": "{{inputs.lookback_days}}"
      },
      "as": "my_result"
    }
  ]
}
```

**Best Practices:**
- ✅ Use `@capability` decorator for contract definition
- ✅ Validate inputs at method entry
- ✅ Use database pool from `self.services["db"]`
- ✅ Handle errors with specific exceptions
- ✅ Return structured data (dict with clear keys)
- ✅ Document method with docstring
- ✅ Use type hints for all parameters

### Adding a New Endpoint

**Direct Endpoint (Simple):**
```python
# combined_server.py
@app.get("/api/my-endpoint")
async def my_endpoint(user: dict = Depends(require_auth)):
    # Implementation
    return SuccessResponse(data={"result": "value"})
```

**Pattern-Based Endpoint (Recommended):**
1. Create pattern JSON in `backend/patterns/`
2. Use existing `/api/patterns/execute` endpoint
3. No new endpoint code needed!

### Authentication Pattern

**All endpoints must use centralized auth:**
```python
from backend.app.auth.dependencies import require_auth

@app.get("/api/protected")
async def protected_route(user: dict = Depends(require_auth)):
    # user = {"email": "...", "role": "...", "portfolio_id": "..."}
    return SuccessResponse(data={})
```

**DO NOT use:**
```python
# ❌ OLD PATTERN (removed in auth refactor)
user = await get_current_user(request)
if not user:
    raise HTTPException(401)
```

---

## Frontend Development

### React Component Patterns

**full_ui.html uses React 18 (no build step):**
```javascript
// Create component
function MyComponent({ data }) {
    const [state, setState] = useState(null);

    return e('div', { className: 'my-component' },
        e('h2', null, 'My Component'),
        e('p', null, JSON.stringify(data))
    );
}

// Use component
e(MyComponent, { data: myData })
```

### Pattern Integration

**Use PatternRenderer (Recommended):**
```javascript
function MyPage() {
    const { portfolioId } = useUserContext();

    return e('div', { className: 'my-page' },
        e(PatternRenderer, {
            pattern: 'my_pattern',
            inputs: { portfolio_id: portfolioId }
        })
    );
}
```

**Direct Pattern Execution (Advanced):**
```javascript
const result = await apiClient.executePattern('my_pattern', {
    portfolio_id: portfolioId
});
// result.data = { step1_result, step2_result, ... }
```

### Panel Configuration

**Register pattern display:**
```javascript
// In patternRegistry (lines 2784-3117)
const patternRegistry = {
    my_pattern: {
        name: 'My Pattern',
        display: {
            panels: [
                {
                    id: 'summary',
                    type: 'metrics_grid',
                    dataPath: 'summary_data'
                }
            ]
        }
    }
};
```

---

## Pattern Development

### Creating a New Pattern

**1. Create JSON File:**
```json
// backend/patterns/my_pattern.json
{
  "id": "my_pattern",
  "name": "My Pattern",
  "version": "1.0.0",
  "category": "analysis",
  "inputs": {
    "portfolio_id": { "type": "uuid", "required": true }
  },
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "positions"
    },
    {
      "capability": "my.analysis",
      "args": {
        "positions": "{{positions.positions}}"
      },
      "as": "analysis"
    }
  ],
  "outputs": ["positions", "analysis"]
}
```

**2. Test Pattern:**
```bash
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_name": "my_pattern",
    "inputs": {"portfolio_id": "..."}
  }'
```

### Template Substitution

**Available Variables:**
- `{{inputs.field}}` - From pattern inputs
- `{{ctx.field}}` - From RequestCtx (portfolio_id, pricing_pack_id, etc.)
- `{{state.field}}` - From execution state
- `{{step_name.field}}` - From previous step result (use step's "as" name)

**Example:**
```json
{
  "capability": "metrics.compute_twr",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}",
    "positions": "{{valued_positions.positions}}",
    "asof_date": "{{ctx.asof_date}}"
  },
  "as": "performance"
}
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest

# Run specific test
pytest tests/test_agents.py::test_financial_analyst

# With coverage
pytest --cov=app --cov-report=html
```

### Manual API Testing

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Login:**
```bash
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"michael@dawsos.com","password":"admin123"}' \
  | jq -r .access_token)
```

**Execute Pattern:**
```bash
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern_name":"portfolio_overview","inputs":{"portfolio_id":"..."}}'
```

### UI Testing

1. Start server: `python combined_server.py`
2. Open browser: http://localhost:8000/
3. Login: michael@dawsos.com / admin123
4. Test all 20 pages manually

---

## Refactoring Guidelines

### Safe Refactoring Practices

**1. Never Refactor Without Tests:**
- Write test first
- Refactor code
- Verify test still passes

**2. Extract, Don't Rewrite:**
- Extract method/function
- Move to new location
- Update imports
- Delete old code only after verification

**3. One Change at a Time:**
- Don't mix refactoring with feature changes
- Commit refactoring separately
- Clear commit messages

### Low-Risk Refactoring Opportunities

**See archived analysis for 16 safe refactoring opportunities:**
- `.archive/deprecated/LOW_RISK_REFACTORING_OPPORTUNITIES_V2.md` (955 lines)

**Common Patterns:**
1. Extract duplicate code into utilities
2. Consolidate similar agent methods
3. Simplify pattern JSON (remove unused fields)
4. Extract magic numbers to constants

---

## Deployment Guardrails

### Replit Deployment Constraints

**CRITICAL: DO NOT introduce these changes:**

❌ **NO Docker** - Replit doesn't support Docker well
❌ **NO Build Steps** - Keep `full_ui.html` as single file
❌ **NO npm run build** - Use UMD React builds only
❌ **NO Complex Dependencies** - Avoid packages needing compilation
❌ **NO Port Changes** - Stay on 5000/8000 as configured

✅ **DO:**
- Keep direct Python execution (`python combined_server.py`)
- Use UMD builds for frontend libraries
- Keep single-file UI (`full_ui.html`)
- Minimize dependencies

**See:** `.archive/deprecated/REPLIT_DEPLOYMENT_GUARDRAILS.md` for full constraints

---

## Best Practices

### Code Organization

**1. Agent Capabilities:**
- ✅ Use `@capability` decorator for contract definition
- ✅ Follow naming convention: `category.operation` (e.g., `ledger.positions`)
- ✅ Method name: `category_operation` (e.g., `ledger_positions`)
- ✅ Always validate inputs at method entry
- ✅ Use specific exceptions (not generic `Exception`)
- ✅ Return structured data (dict with clear keys)

**2. Error Handling:**
```python
# ✅ GOOD: Specific exception handling
try:
    result = await service.method()
except PricingPackNotFoundError as e:
    logger.error(f"Pricing pack not found: {e}")
    raise
except asyncpg.PostgresError as e:
    logger.warning(f"Database error: {e}")
    return {"error": "Database error", "provenance": "error"}
except (ValueError, TypeError, KeyError) as e:
    # Programming errors - re-raise to surface bugs
    logger.error(f"Programming error: {e}", exc_info=True)
    raise

# ❌ BAD: Broad exception catch
try:
    result = await service.method()
except Exception as e:
    logger.warning(f"Error: {e}")
    return {"error": "Unknown error"}  # Masks bugs!
```

**3. Database Queries:**
```python
# ✅ GOOD: Parameterized queries
async with pool.acquire() as conn:
    rows = await conn.fetch(
        "SELECT * FROM lots WHERE portfolio_id = $1 AND qty_open > $2",
        portfolio_id,
        Decimal("0")
    )

# ❌ BAD: String formatting (SQL injection risk!)
query = f"SELECT * FROM lots WHERE portfolio_id = '{portfolio_id}'"
```

**4. Type Hints:**
```python
# ✅ GOOD: Type hints for all parameters
async def my_capability(
    self,
    ctx: RequestCtx,
    state: Dict,
    portfolio_id: str,
    lookback_days: int = 252,
    **kwargs
) -> Dict[str, Any]:
    """Method with type hints."""
    pass

# ❌ BAD: No type hints
async def my_capability(self, ctx, state, portfolio_id, lookback_days=252):
    pass
```

**5. Logging:**
```python
# ✅ GOOD: Structured logging
logger.info(f"Processing portfolio {portfolio_id}", extra={
    "portfolio_id": portfolio_id,
    "trace_id": ctx.trace_id
})

# ❌ BAD: Print statements
print(f"Processing portfolio {portfolio_id}")  # Don't use print()!
```

---

## Code Review Checklist

### Before Committing

- [ ] Code compiles without errors (`python -m py_compile`)
- [ ] All tests pass (`pytest`)
- [ ] No print() or console.log() debugging statements
- [ ] Docstrings added/updated for new functions
- [ ] Type hints added for all parameters
- [ ] Authentication using `Depends(require_auth)` pattern
- [ ] No hardcoded secrets or API keys
- [ ] Exception handling is specific (not broad `Exception`)
- [ ] Database queries use parameterized queries (not string formatting)
- [ ] Git commit message is descriptive

### Before Pull Request

- [ ] All endpoints tested manually
- [ ] UI pages tested in browser
- [ ] Database migrations tested
- [ ] Pattern execution tested
- [ ] Error handling tested (both success and failure cases)
- [ ] README.md updated if needed
- [ ] No breaking changes to existing patterns
- [ ] Follows existing code style
- [ ] Code review checklist completed

---

## Common Development Tasks

### Add New Security to Database

```sql
-- Insert new security
INSERT INTO securities (id, symbol, name, currency, security_type, sector)
VALUES (
    gen_random_uuid(),
    'AAPL',
    'Apple Inc.',
    'USD',
    'EQUITY',
    'Technology'
);

-- Verify insertion
SELECT id, symbol, name FROM securities WHERE symbol = 'AAPL';
```

### Create Test Portfolio

```sql
-- Create portfolio
INSERT INTO portfolios (id, user_id, name, base_currency)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    (SELECT id FROM users WHERE email = 'michael@dawsos.com'),
    'Test Portfolio',
    'USD'
);

-- Add position (use qty_open, not quantity - see DATABASE.md)
INSERT INTO lots (
    id, 
    portfolio_id, 
    security_id, 
    qty_open, 
    qty_original,
    cost_basis, 
    cost_basis_per_share,
    acquisition_date,
    currency
)
VALUES (
    gen_random_uuid(),
    '11111111-1111-1111-1111-111111111111',
    (SELECT id FROM securities WHERE symbol = 'AAPL'),
    100,      -- qty_open
    100,      -- qty_original
    15000.00, -- cost_basis
    150.00,   -- cost_basis_per_share
    '2024-01-01',
    'USD'
);

-- Verify portfolio
SELECT p.name, l.qty_open, s.symbol, s.name
FROM portfolios p
JOIN lots l ON l.portfolio_id = p.id
JOIN securities s ON s.id = l.security_id
WHERE p.id = '11111111-1111-1111-1111-111111111111';
```

### Add New Capability to Existing Agent

**Example: Adding a new capability to FinancialAnalyst**

```python
# In backend/app/agents/financial_analyst.py

@capability(
    inputs={"portfolio_id": "uuid", "metric_type": "string"},
    outputs={"metrics": "dict"},
    status="production"
)
async def metrics_compute_custom(
    self,
    ctx: RequestCtx,
    state: Dict,
    portfolio_id: str,
    metric_type: str = "custom",
    **kwargs
) -> Dict:
    """
    Compute custom portfolio metric.
    
    Args:
        ctx: Request context
        state: Execution state
        portfolio_id: Portfolio UUID
        metric_type: Type of metric to compute
    
    Returns:
        Dict with metric results
    """
    # Get database pool
    pool = self.services.get("db")
    if not pool:
        raise RuntimeError("Database pool not available")
    
    # Implementation
    async with pool.acquire() as conn:
        # Query database
        rows = await conn.fetch(
            "SELECT * FROM portfolio_metrics WHERE portfolio_id = $1 AND metric_type = $2",
            portfolio_id,
            metric_type
        )
    
    # Process and return
    return {
        "portfolio_id": portfolio_id,
        "metric_type": metric_type,
        "metrics": [dict(row) for row in rows]
    }

# Update get_capabilities() method
def get_capabilities(self) -> List[str]:
    capabilities = [
        # ... existing capabilities ...
        "metrics.compute_custom",  # Add new capability
    ]
    return capabilities
```

### Test New Capability

```bash
# Test capability directly
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_name": "test_pattern",
    "inputs": {
      "portfolio_id": "...",
      "metric_type": "custom"
    }
  }'

# Or create test pattern
cat > backend/patterns/test_custom_metric.json << EOF
{
  "id": "test_custom_metric",
  "steps": [
    {
      "capability": "metrics.compute_custom",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "metric_type": "{{inputs.metric_type}}"
      },
      "as": "custom_metrics"
    }
  ],
  "outputs": ["custom_metrics"]
}
EOF
```

### Debug Database Query

```python
# Enable query logging
import logging
logging.basicConfig(level=logging.DEBUG)

# In your code
async with pool.acquire() as conn:
    # Log query before execution
    logger.debug(f"Executing query: SELECT * FROM lots WHERE portfolio_id = {portfolio_id}")
    
    rows = await conn.fetch(
        "SELECT * FROM lots WHERE portfolio_id = $1",
        portfolio_id
    )
    
    logger.debug(f"Query returned {len(rows)} rows")
```

### Performance Optimization

**1. Database Query Optimization:**
```python
# ✅ GOOD: Use indexes, limit results
async with pool.acquire() as conn:
    rows = await conn.fetch(
        """
        SELECT * FROM lots 
        WHERE portfolio_id = $1 
          AND qty_open > 0
        ORDER BY acquisition_date DESC
        LIMIT 100
        """,
        portfolio_id
    )

# ❌ BAD: Full table scan
rows = await conn.fetch("SELECT * FROM lots")  # No WHERE clause!
```

**2. Caching:**
```python
# Use @cache_capability decorator for expensive operations
from app.agents.base_agent import cache_capability

@cache_capability(ttl=300)  # Cache for 5 minutes
async def expensive_computation(self, ctx, state, **kwargs):
    # Expensive computation here
    return result
```

**3. Batch Operations:**
```python
# ✅ GOOD: Batch database operations
async with pool.acquire() as conn:
    async with conn.transaction():
        await conn.executemany(
            "INSERT INTO portfolio_metrics (portfolio_id, date, metric_type, value) VALUES ($1, $2, $3, $4)",
            [(portfolio_id, date, metric_type, value) for ...]
        )

# ❌ BAD: Individual inserts in loop
for item in items:
    await conn.execute("INSERT INTO ...")  # N queries instead of 1!
```

### Debug Pattern Execution

**Enable Debug Logging:**
```python
# In combined_server.py or environment
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or set via environment variable
export LOG_LEVEL=DEBUG
```

**Check Execution Trace:**
```bash
# Pattern response includes trace
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern_name":"portfolio_overview","inputs":{"portfolio_id":"..."}}' \
  | jq '.trace'

# Expected trace structure:
{
  "pattern_id": "portfolio_overview",
  "steps": [
    {
      "step": 1,
      "capability": "portfolio.get_valued_positions",
      "status": "success",
      "duration_ms": 45
    },
    {
      "step": 2,
      "capability": "metrics.compute_twr",
      "status": "success",
      "duration_ms": 120
    }
  ],
  "agents_used": ["financial_analyst"],
  "capabilities_used": ["portfolio.get_valued_positions", "metrics.compute_twr"],
  "total_duration_ms": 165
}
```

**Debug Steps:**
1. **Check pattern JSON is valid:**
   ```bash
   python3 -m json.tool backend/patterns/portfolio_overview.json
   ```

2. **Verify all required inputs are provided:**
   ```python
   # Check pattern inputs definition
   pattern = json.load(open("backend/patterns/portfolio_overview.json"))
   required_inputs = [k for k, v in pattern["inputs"].items() if v.get("required")]
   print(f"Required inputs: {required_inputs}")
   ```

3. **Check template substitution works:**
   ```python
   # In PatternOrchestrator, enable debug logging
   logger.debug(f"Template substitution: {template} -> {resolved_value}")
   ```

4. **Verify each step executes successfully:**
   - Check step status in trace
   - Look for error messages in logs
   - Verify step outputs are correct

5. **Check agent routing works:**
   ```python
   # Test capability routing
   from backend.app.core.agent_runtime import get_agent_runtime
   runtime = get_agent_runtime()
   agent = runtime.get_agent_for_capability("ledger.positions")
   print(f"Agent: {agent.name if agent else None}")
   ```

**Common Debugging Issues:**
- **Template substitution fails:** Check variable names match exactly
- **Capability not found:** Verify agent is registered and capability exists
- **Database errors:** Check pool registration and connection
- **Type errors:** Verify input types match pattern definition

---

## Future Architecture

### Backend Modularization Plan

**Status:** Ready for approval (not yet executed)

**Goal:** Extract `combined_server.py` (6,043 lines) into modular structure

**Approach:**
- Build new modular backend in `backend/app/`
- Run in parallel on port 8001
- Migrate after full validation
- Can rollback anytime

**See:** `.archive/deprecated/PLAN_3_BACKEND_REFACTORING_REVALIDATED.md` (649 lines)

**Timeline:** 3-4 weeks (1 week build, 2-3 weeks testing)

---

## Documentation Standards

### Documentation Template

When creating new documentation, use the following template:

```markdown
# Document Title

**Date:** [Date]
**Status:** [Status]
**Purpose:** [Purpose]

---

## 📊 Executive Summary

[Brief summary of the document's content and purpose]

---

## [Section 1]

[Content]

---

## [Section 2]

[Content]

---

## ✅ Conclusion

[Summary and next steps]

---

**Last Updated:** [Date]
**Status:** [Status]
```

### Standard Header Format

**Required Fields:**
- **Date:** Date of creation or last update
- **Status:** Current status (✅ COMPLETE, ⏳ IN PROGRESS, 📋 PLANNING, ⚠️ BLOCKED)
- **Purpose:** Brief description of document purpose

**Optional Fields:**
- **Reviewer:** Person or agent reviewing
- **Assigned To:** Person or agent responsible
- **Coordinated By:** Person or agent coordinating

### Status Values

**Standard Status Values:**
- ✅ **COMPLETE** - Work finished
- ⏳ **IN PROGRESS** - Work ongoing
- ⏸️ **PAUSED** - Work paused
- 📋 **PLANNING** - Planning phase
- ⚠️ **BLOCKED** - Blocked by dependency
- ✅ **READY FOR TESTING** - Ready for testing
- ✅ **READY FOR ROLLOUT** - Ready for rollout

### Documentation Structure

**Standard Sections:**
1. **Executive Summary** - Brief overview
2. **Detailed Analysis/Content** - Main content
3. **Findings/Results** - Key findings
4. **Recommendations/Next Steps** - Actions to take
5. **Conclusion** - Summary and status

### File Naming Conventions

**Planning Documents:**
- `PHASE_X_PLAN.md` - Planning documents
- `PHASE_X_EXECUTION_PLAN.md` - Execution plans
- `PHASE_X_CURRENT_STATUS_REVIEW.md` - Status reviews

**Report Documents:**
- `PHASE_X_SUMMARY.md` - Consolidated summaries
- `PHASE_X_WEEKY_COMPLETION.md` - Week completion reports
- `*_REPORT.md` - Detailed reports (to be archived)

**Guide Documents:**
- `*_GUIDE.md` - Comprehensive guides
- `*_REFERENCE.md` - Reference documents

### Documentation Location

**Core Documentation (Root):**
- Core project files (README, ARCHITECTURE, DATABASE, etc.)
- Active status tracking (AGENT_CONVERSATION_MEMORY, PHASE_3_CURRENT_STATUS_REVIEW)
- Active planning (DOCUMENTATION_REFACTORING_OPPORTUNITIES)

**Organized Documentation (`docs/`):**
- `docs/planning/` - Planning documents
- `docs/reports/` - Report documents
- `docs/analysis/` - Analysis documents
- `docs/guides/` - Comprehensive guides
- `docs/reference/` - Reference documents

**Archived Documentation (`.archive/`):**
- Historical documents organized by category
- See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for full index

### Best Practices

1. **Update Immediately** - Update documentation when code changes
2. **Cross-Reference** - Link related documents
3. **Status Tracking** - Always include status section
4. **Consolidate Regularly** - Reduce redundancy
5. **Archive Promptly** - Move outdated docs to `.archive/`

For more details, see [DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md).

---

## Resources

**Code:**
- [combined_server.py](combined_server.py) - Main server
- [backend/app/agents/](backend/app/agents/) - Agent implementations
- [backend/patterns/](backend/patterns/) - Pattern definitions
- [full_ui.html](full_ui.html) - React UI

**Documentation:**
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Complete documentation index
- [DOCUMENTATION_MAINTENANCE_GUIDE.md](DOCUMENTATION_MAINTENANCE_GUIDE.md) - Documentation maintenance guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [README.md](README.md) - Quick start guide
- [DATABASE.md](DATABASE.md) - Database reference

**Archived Documentation:**
- [.archive/deprecated/](.archive/deprecated/) - Historical documentation
- See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for full archive index

---

## 📁 Project Structure

### Root-Level Files
- `combined_server.py` - Main FastAPI application server
- `full_ui.html` - React 18 SPA (single file)
- `requirements.txt` - Python dependencies
- `pytest.ini` - Pytest configuration
- `activate.sh` - Virtual environment activation script
- `load_env.py` - Environment variable loading utility
- `verify_ready.sh` - Setup verification script

### Organized Directories
- `scripts/data/` - Data population scripts
  - `populate_portfolio_metrics_simple.py` - Populate portfolio metrics
  - `populate_prices.py` - Populate security prices
  - `update_metrics.py` - Update portfolio metrics
- `scripts/validation/` - Validation scripts
  - `verify_ui_data.py` - Verify UI data integrity
  - `validate_pattern_ui_match.py` - Validate pattern UI matching
- `tests/integration/` - Integration test files
  - `test_dashboard.html` - Dashboard test page
  - `test_login_and_macro.js` - Login and macro test
  - `test_optimizer_routing.py` - Optimizer routing test
  - `test_db_pool_config.py` - Database pool config test
- `migrations/seeds/` - Database seed files
  - `seed_portfolio_data.sql` - Seed portfolio data
- `backend/` - Backend application code
- `docs/` - Documentation
- `.archive/` - Archived historical files

---

**Last Updated:** November 4, 2025
