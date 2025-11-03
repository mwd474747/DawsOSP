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
├── combined_server.py          # ⭐ PRIMARY SERVER (6,043 lines, 53 endpoints)
├── full_ui.html                # ⭐ PRIMARY UI (React SPA, 18 pages)
├── backend/
│   ├── app/
│   │   ├── agents/             # 9 agents (financial_analyst, macro_hound, etc.)
│   │   │                       # Phase 3 consolidation in progress (Weeks 1-3 complete)
│   │   ├── core/               # AgentRuntime, PatternOrchestrator
│   │   ├── services/           # Business logic
│   │   ├── db/                 # Database layer
│   │   └── auth/               # Authentication (JWT, RBAC)
│   ├── patterns/               # 12 pattern definitions (JSON)
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

---

## Backend Development

### Adding a New Agent

**1. Create Agent File:**
```python
# backend/app/agents/my_agent.py
from app.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def get_capabilities(self) -> List[str]:
        return ["my.capability1", "my.capability2"]

    async def my_capability1(self, ctx: RequestCtx, state: Dict, **kwargs):
        # Implementation
        return {"result": "data"}
```

**2. Register Agent:**
```python
# combined_server.py (in get_agent_runtime function)
my_agent = MyAgent("my_agent", services)
_agent_runtime.register_agent(my_agent)
```

**3. Use in Pattern:**
```json
{
  "steps": [
    {
      "capability": "my.capability1",
      "args": {},
      "as": "my_result"
    }
  ]
}
```

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
4. Test all 18 pages manually

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

## Code Review Checklist

### Before Committing

- [ ] Code compiles without errors (`python -m py_compile`)
- [ ] All tests pass (`pytest`)
- [ ] No print() or console.log() debugging statements
- [ ] Docstrings added/updated for new functions
- [ ] Authentication using `Depends(require_auth)` pattern
- [ ] No hardcoded secrets or API keys
- [ ] Git commit message is descriptive

### Before Pull Request

- [ ] All endpoints tested manually
- [ ] UI pages tested in browser
- [ ] Database migrations tested
- [ ] README.md updated if needed
- [ ] No breaking changes to existing patterns
- [ ] Follows existing code style

---

## Common Development Tasks

### Add New Security to Database

```sql
INSERT INTO securities (id, symbol, name, currency, security_type, sector)
VALUES (
    gen_random_uuid(),
    'AAPL',
    'Apple Inc.',
    'USD',
    'EQUITY',
    'Technology'
);
```

### Create Test Portfolio

```sql
-- Create portfolio
INSERT INTO portfolios (id, user_id, name, currency)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    (SELECT id FROM users WHERE email = 'michael@dawsos.com'),
    'Test Portfolio',
    'USD'
);

-- Add position
INSERT INTO lots (id, portfolio_id, security_id, quantity, acquisition_cost, acquisition_date)
VALUES (
    gen_random_uuid(),
    '11111111-1111-1111-1111-111111111111',
    (SELECT id FROM securities WHERE symbol = 'AAPL'),
    100,
    15000.00,
    '2024-01-01'
);
```

### Debug Pattern Execution

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check execution trace:**
```bash
# Pattern response includes trace
{
  "data": { ... },
  "trace": {
    "pattern_id": "portfolio_overview",
    "steps": [...],
    "agents_used": ["financial_analyst"],
    "capabilities_used": ["ledger.positions", "pricing.apply_pack"]
  }
}
```

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

**Last Updated:** November 3, 2025
