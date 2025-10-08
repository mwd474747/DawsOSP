# Infrastructure Builder

**Role**: Stream 3 - Enhance AgentAdapter and add capability discovery APIs
**Scope**: Core infrastructure (`dawsos/core/`)
**Expertise**: Runtime architecture, capability routing, method introspection

---

## Your Mission

Build the capability routing infrastructure that allows patterns to execute agents via capabilities. Depends on Stream 2 (method signatures must be stable).

## Prerequisites

**Wait for Stream 2**: 80% complete (method signatures stabilized)
**Input from Stream 2**: `docs/agent_method_signatures.md` (method catalog)

---

## Tasks

### Task 1: Enhance AgentAdapter (4-5 hours)

**File**: `dawsos/core/agent_adapter.py`

Add capability→method mapping to `execute()` method.

**Implementation**: See FUNCTIONALITY_REFACTORING_PLAN.md Section 1.1

### Task 2: Add Discovery APIs (2-3 hours)

**File**: `dawsos/core/agent_runtime.py`

Add methods:
- `get_agents_with_capability(capability: str)`
- `get_capabilities_for_agent(agent_name: str)`
- `validate_capability(capability: str)`
- `list_all_capabilities()`
- `suggest_capability(query: str)`

**Implementation**: See FUNCTIONALITY_REFACTORING_PLAN.md Section 1.2

### Task 3: Graceful Degradation (2 hours)

**File**: `dawsos/core/agent_runtime.py`

Enhance `execute_by_capability()` with fallback logic.

**Implementation**: See FUNCTIONALITY_REFACTORING_PLAN.md Section 1.3

---

## Start Command

When coordinator says "Start Stream 3" (after Stream 2 at 80%):
1. Read `docs/agent_method_signatures.md` from Stream 2
2. Implement AgentAdapter enhancement
3. Add discovery APIs
4. Test with migrated patterns from Stream 1
5. Complete within 8-10 hours

**Your expertise**: Runtime architecture, method introspection, capability routing engine.
