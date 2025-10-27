# [Agent/Service Name] - [Role Title]

**Role**: [One-line description of agent's purpose]
**Context**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md) | [Parent Layer](./PARENT_LAYER.md)
**Status**: [SEEDED / PARTIAL / COMPLETE]
**Priority**: [P0 / P1 / P2]
**Last Updated**: [YYYY-MM-DD]

---

## Mission

[2-3 sentences describing the agent's core responsibility and deliverables]

### Scope
**In Scope**:
- [Specific capability 1]
- [Specific capability 2]
- [Specific capability 3]

**Out of Scope**:
- [What this agent does NOT handle]
- [Related functionality owned by other agents]

---

## Prerequisites

### Required Reading
Before implementing this agent/service:
- [ ] [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md) - Understand acceptance criteria
- [ ] [Related spec file if any]
- [ ] [Database schema if applicable]

### Required Infrastructure
- [ ] Database migrations applied: [migration file names]
- [ ] Services available: [service dependencies]
- [ ] API keys configured (if needed): [provider names]
- [ ] Seed data loaded: [seed file names]

### Required Files (Verify Existence)
```bash
# Check these files exist before starting
ls backend/app/services/<service_name>.py
ls backend/app/agents/<agent_name>.py
ls backend/patterns/<pattern_name>.json
ls backend/db/schema/<schema_name>.sql
```

---

## Implementation Steps

### Step 1: Service Implementation (if needed)
**Timeline**: [X hours]
**File**: `backend/app/services/<service_name>.py`

**Sub-steps**:
1. Create service class with async methods
2. Implement business logic (NO shortcuts)
3. Add error handling and graceful degradation
4. Add logging with appropriate log levels
5. Return results as `Dict[str, Any]` with Decimal types

**Verification**:
```bash
# Verify Python syntax
python3 -m py_compile backend/app/services/<service_name>.py

# Test service method directly (optional)
python3 -c "
from backend.app.services.<service_name> import <ServiceClass>
import asyncio
service = <ServiceClass>()
result = asyncio.run(service.<method_name>(<test_args>))
print(result)
"
```

### Step 2: Agent Creation/Update
**Timeline**: [X hours]
**File**: `backend/app/agents/<agent_name>.py`

**Sub-steps**:
1. Add capability to `get_capabilities()` list
   ```python
   def get_capabilities(self) -> List[str]:
       return [
           "existing.capability",
           "new.capability",  # ADD THIS
       ]
   ```

2. Implement agent method (convert dots to underscores)
   ```python
   async def new_capability(
       self,
       ctx: RequestCtx,
       state: Dict[str, Any],
       **kwargs
   ) -> Dict[str, Any]:
       """
       [Description of what this capability does]

       Capability: new.capability
       """
       # 1. Extract args
       arg1 = kwargs.get("arg1")

       # 2. Call service
       from backend.app.services.<service> import get_service
       service = get_service()
       result = await service.<method>(arg1)

       # 3. Attach metadata
       metadata = self._create_metadata(
           source=f"<service>:{ctx.pricing_pack_id}",
           asof=ctx.asof_date,
           ttl=300
       )

       return self._attach_metadata(result, metadata)
   ```

3. Add docstring with capability reference
4. Add logging for capability execution

**Verification**:
```bash
# Verify Python syntax
python3 -m py_compile backend/app/agents/<agent_name>.py

# Verify capability declared
grep -A 10 "def get_capabilities" backend/app/agents/<agent_name>.py | grep "new.capability"

# Verify method exists
grep "async def new_capability" backend/app/agents/<agent_name>.py
```

### Step 3: Agent Registration (CRITICAL)
**Timeline**: 5 minutes
**File**: `backend/app/api/executor.py`

**⚠️ CRITICAL**: This step is often forgotten. Verify registration explicitly.

**Sub-steps**:
1. Add import at top of file:
   ```python
   from backend.app.agents.<agent_name> import <AgentClass>
   ```

2. Register agent in `get_agent_runtime()` function:
   ```python
   # Around line 100-139
   <agent_var> = <AgentClass>("<agent_name>", services)
   _agent_runtime.register_agent(<agent_var>)
   ```

3. Update log message with new agent count

**Verification**:
```bash
# MUST verify registration
grep -A 5 "register_agent" backend/app/api/executor.py | grep "<agent_name>"

# Count registered agents
grep -c "register_agent" backend/app/api/executor.py
```

### Step 4: Pattern Creation/Update (if needed)
**Timeline**: [X hours]
**File**: `backend/patterns/<pattern_name>.json`

**Sub-steps**:
1. Create pattern JSON with steps
2. Reference capability with dot notation
3. Define inputs and outputs
4. Test pattern execution via executor API

**Example**:
```json
{
  "id": "pattern_name",
  "description": "Pattern description",
  "steps": [
    {
      "capability": "new.capability",
      "args": {
        "arg1": "{{inputs.arg1}}"
      },
      "as": "result_var"
    }
  ],
  "outputs": ["result_var"]
}
```

**Verification**:
```bash
# Verify JSON syntax
python3 -m json.tool backend/patterns/<pattern_name>.json > /dev/null

# Test pattern execution
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"pattern_id":"<pattern_name>","inputs":{...}}'
```

### Step 5: Unit Tests
**Timeline**: [X hours]
**File**: `backend/tests/unit/test_<service_name>.py`

**Minimum test coverage**:
- [ ] Test happy path (valid inputs → expected outputs)
- [ ] Test edge cases (empty inputs, extreme values, zero values)
- [ ] Test error handling (missing data, invalid inputs)
- [ ] Test graceful degradation (service unavailable)
- [ ] Test metadata attachment (verify `_metadata` in result)

**Example**:
```python
@pytest.mark.asyncio
@pytest.mark.unit
async def test_capability_happy_path():
    """Test capability with valid inputs."""
    service = <ServiceClass>()
    result = await service.<method>(<valid_args>)

    assert "expected_field" in result
    assert result["expected_field"] == expected_value
```

**Verification**:
```bash
# Run tests
pytest backend/tests/unit/test_<service_name>.py -v

# Check coverage
pytest backend/tests/unit/test_<service_name>.py --cov=backend/app/services/<service_name> --cov-report=term
```

### Step 6: Integration Test (optional but recommended)
**Timeline**: [X hours]
**File**: `backend/tests/integration/test_<feature>.py`

**What to test**:
- Pattern execution end-to-end
- Capability routing through agent runtime
- Metadata attachment and traceability
- Database state changes (if applicable)

**Verification**:
```bash
# Run integration tests
pytest backend/tests/integration/test_<feature>.py -v
```

---

## Integration Checklist

Before claiming COMPLETE:

### Code Integration
- [ ] Service method implemented and syntax-verified
- [ ] Agent method implemented and syntax-verified
- [ ] Capability added to `get_capabilities()` list
- [ ] ⚠️ **CRITICAL**: Agent registered in executor.py (lines 100-139)
- [ ] Pattern JSON created/updated (if needed)
- [ ] All Python files pass `python3 -m py_compile`

### Testing
- [ ] Unit tests written (minimum 5 tests)
- [ ] Unit tests passing (`pytest -v`)
- [ ] Integration test written (if applicable)
- [ ] Coverage measured (run `pytest --cov`, don't guess)

### Verification
- [ ] Verified agent registration: `grep "register_agent.*<agent>" backend/app/api/executor.py`
- [ ] Verified capability declared: `grep "<capability>" backend/app/agents/<agent>.py`
- [ ] Tested pattern execution: `curl POST /v1/execute`
- [ ] Checked database state (if applicable): `docker exec ... psql`

### Documentation
- [ ] Updated [CLAUDE.md](../../CLAUDE.md) with current status
- [ ] Updated this spec with actual timeline (if different from estimate)
- [ ] Noted any deviations from plan in this spec
- [ ] Listed known issues or limitations

---

## Definition of Done

**SEEDED**:
- Service returns stub data
- Agent calls service
- Not registered in executor
- No tests

**PARTIAL**:
- Service implemented
- Agent implemented
- NOT registered in executor OR tests missing
- Code exists but not integrated

**COMPLETE**:
- Service implemented and tested
- Agent implemented and tested
- ✅ Registered in executor.py (verified)
- ✅ Pattern execution works end-to-end (verified)
- ✅ Tests passing (verified)
- Ready for production use

---

## Common Pitfalls

### Pitfall 1: Forgot to Register Agent
**Symptom**: "No agent registered for capability X" error
**Solution**: Add 3 lines to executor.py (import, instantiate, register)
**Verification**: `grep "register_agent.*<agent>" backend/app/api/executor.py`

### Pitfall 2: Capability Naming Mismatch
**Symptom**: Pattern references `new.capability` but agent method is `new_capability2`
**Solution**: Method name MUST be capability with dots → underscores
**Verification**: Capability `new.capability` → method `new_capability`

### Pitfall 3: Claimed Complete Without Testing
**Symptom**: Code exists but crashes at runtime
**Solution**: Run pytest, don't assume tests pass
**Verification**: `pytest backend/tests/unit/test_<service>.py -v`

### Pitfall 4: Assumed Migration Ran
**Symptom**: "table does not exist" error at runtime
**Solution**: Check actual database, don't trust "should have"
**Verification**: `docker exec dawsos-postgres psql -U dawsos_app -d dawsos -c "\d <table>"`

### Pitfall 5: Background Processes Accumulated
**Symptom**: Port 8000 already in use, multiple uvicorn instances
**Solution**: Kill all at end of session
**Verification**: `killall -9 python python3 uvicorn`

---

## Time Estimates

**Realistic Timeline** (based on actual implementation sessions):
- Service implementation: [X hours] (estimated) → [Y hours] (actual)
- Agent wiring: [X hours] (estimated) → [Y hours] (actual)
- Testing: [X hours] (estimated) → [Y hours] (actual)
- Integration verification: [X hours] (estimated) → [Y hours] (actual)

**Total**: [X hours] (add 1.5-2x buffer for unknowns)

---

## Success Criteria

### Functional
- [ ] Pattern execution returns expected data structure
- [ ] Results include `_metadata` with pricing_pack_id, asof_date
- [ ] No errors in logs during normal execution
- [ ] Graceful degradation on provider failures (if applicable)

### Technical
- [ ] All tests passing
- [ ] Python syntax clean (`python3 -m py_compile`)
- [ ] Agent registered and routing correctly
- [ ] Coverage ≥ 60% on new code (measured, not guessed)

### Integration
- [ ] End-to-end pattern execution works
- [ ] Database state correct (if applicable)
- [ ] No regression on existing patterns
- [ ] Executor health check passes

---

## Links

- **Product Spec**: [PRODUCT_SPEC.md](../../PRODUCT_SPEC.md)
- **Task Inventory**: [.ops/TASK_INVENTORY_2025-10-24.md](../../.ops/TASK_INVENTORY_2025-10-24.md)
- **Executor Code**: [backend/app/api/executor.py](../../backend/app/api/executor.py)
- **Agent Registration Lines**: executor.py:100-139
- **Pattern Definitions**: [backend/patterns/](../../backend/patterns/)

---

**Template Version**: 1.0 (2025-10-27)
**Based on**: Lessons learned from 2025-10-26/10-27 implementation sessions
**Purpose**: Prevent common integration issues and ensure honest status reporting
