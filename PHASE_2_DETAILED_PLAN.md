# Phase 2 Detailed Implementation Plan: Foundation & Validation

**Date:** January 14, 2025  
**Status:** ✅ **READY FOR EXECUTION**  
**Purpose:** Detailed implementation plan for Phase 2 that prevents future issues and improves developer experience

---

## Executive Summary

**Goal:** Prevent future issues, improve developer experience, enable confident development

**Root Issues:**
1. **No Validation** - Patterns can reference undefined steps, errors discovered at runtime
2. **No Capability Contracts** - No clear interfaces for capabilities, unclear expectations
3. **No Pattern Linter** - No automated validation, issues discovered at runtime

**Total Time:** 32 hours (Weeks 2-3)

**Success Criteria:**
- ✅ Capability contracts documented for all 70 capabilities
- ✅ Step dependency validation catches undefined references
- ✅ Pattern linter CLI validates all patterns automatically

---

## Task 2.1: Create Capability Contracts (16 hours)

### Root Issue

**Problem:** No clear interfaces for capabilities, unclear expectations, hard to identify stub vs real implementations.

**Current State:**
- Capabilities have no documented contracts
- No way to know if capability is stub or real
- No way to validate inputs/outputs
- Developer confusion about what each capability does

**Root Cause:** Lack of documentation and validation system for capabilities.

### Implementation Plan

#### Step 2.1.1: Design Capability Contract System (2 hours)

**Goal:** Design a system for documenting capability contracts.

**Design Requirements:**
1. **Self-documenting** - Contracts visible in code
2. **Compile-time validation** - Catch issues early
3. **Clear expectations** - Inputs, outputs, behavior documented
4. **Stub identification** - Mark stub vs real implementations

**Design Options:**

**Option A: Decorator-based (RECOMMENDED)**
```python
@capability(
    name="risk.compute_factor_exposures",
    inputs={"portfolio_id": str, "pack_id": str},
    outputs={"factors": dict, "r_squared": float, "_provenance": dict},
    fetches_positions=True,  # Documents internal behavior
    implementation_status="stub"  # BE HONEST
)
async def risk_compute_factor_exposures(...):
    ...
```

**Option B: Type hints + docstring**
```python
async def risk_compute_factor_exposures(
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: str,
    pack_id: str
) -> Dict[str, Any]:
    """
    Capability: risk.compute_factor_exposures
    
    Inputs:
        portfolio_id: Portfolio UUID
        pack_id: Pricing pack UUID
    
    Outputs:
        factors: Dict of factor exposures
        r_squared: R-squared value
        _provenance: Provenance metadata
    
    Implementation Status: stub
    """
    ...
```

**Recommendation:** Option A (Decorator-based) - More explicit, easier to validate

**Implementation:**
1. Create `capability` decorator
2. Store contract metadata in function `__capability_contract__` attribute
3. Generate capability documentation automatically
4. Validate contracts at runtime (optional)

---

#### Step 2.1.2: Create Capability Decorator (2 hours)

**File:** `backend/app/core/capability_contract.py` (new file)

**Implementation:**
```python
"""
Capability Contract System

Purpose: Document and validate capability contracts
"""

from typing import Dict, Any, Optional, Callable
from functools import wraps
import inspect

def capability(
    name: str,
    inputs: Dict[str, type],
    outputs: Dict[str, type],
    fetches_positions: bool = False,
    implementation_status: str = "real",  # "real" | "stub" | "partial"
    description: Optional[str] = None,
    dependencies: Optional[list] = None,
):
    """
    Decorator to document capability contracts.
    
    Args:
        name: Capability name (e.g., "risk.compute_factor_exposures")
        inputs: Dict of input parameter names and types
        outputs: Dict of output field names and types
        fetches_positions: Whether capability fetches positions internally
        implementation_status: "real" | "stub" | "partial"
        description: Human-readable description
        dependencies: List of capability dependencies
    """
    def decorator(func: Callable) -> Callable:
        # Store contract metadata
        contract = {
            "name": name,
            "inputs": inputs,
            "outputs": outputs,
            "fetches_positions": fetches_positions,
            "implementation_status": implementation_status,
            "description": description,
            "dependencies": dependencies or [],
        }
        
        # Attach to function
        func.__capability_contract__ = contract
        
        # Preserve original function metadata
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        wrapper.__capability_contract__ = contract
        return wrapper
    
    return decorator
```

**Testing:**
1. Test decorator on a capability
2. Verify contract metadata attached
3. Verify function still works correctly

---

#### Step 2.1.3: Document All 70 Capabilities (10 hours)

**Goal:** Add capability contracts to all 70 capabilities.

**Prioritization:**
1. **High Priority (8 hours):** Stub capabilities (need provenance warnings)
   - `risk.compute_factor_exposures` (stub)
   - `macro.compute_dar` (partial - error cases are stub)
   - Any other stub capabilities

2. **Medium Priority (2 hours):** Critical capabilities (used by many patterns)
   - `ledger.positions`
   - `pricing.apply_pack`
   - `portfolio.get_valued_positions`
   - `metrics.compute_twr`
   - `attribution.currency`

3. **Low Priority (deferred):** Other capabilities (document as needed)

**Implementation for Each Capability:**

**Example: `risk.compute_factor_exposures`**
```python
@capability(
    name="risk.compute_factor_exposures",
    inputs={
        "portfolio_id": str,
        "pack_id": str,
    },
    outputs={
        "factors": dict,
        "portfolio_volatility": float,
        "market_beta": float,
        "r_squared": float,
        "_provenance": dict,
    },
    fetches_positions=False,  # Uses portfolio_id directly
    implementation_status="stub",  # BE HONEST
    description="Compute portfolio factor exposures (currently stub implementation)",
    dependencies=["ledger.positions", "pricing.apply_pack"],
)
async def risk_compute_factor_exposures(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: str,
    pack_id: str,
) -> Dict[str, Any]:
    ...
```

**Steps:**
1. Identify all capabilities in each agent
2. Add capability decorator to each
3. Document inputs, outputs, implementation status
4. Test each capability still works

**Files to Update:**
- `backend/app/agents/financial_analyst.py` (~30 capabilities)
- `backend/app/agents/macro_hound.py` (~17 capabilities)
- `backend/app/agents/data_harvester.py` (~8 capabilities)
- `backend/app/agents/claude_agent.py` (~6 capabilities)

**Time Allocation:**
- High priority (stub): 8 hours
- Medium priority (critical): 2 hours
- Total: 10 hours

---

#### Step 2.1.4: Generate Capability Documentation (2 hours)

**Goal:** Automatically generate capability documentation from contracts.

**Implementation:**
1. Create script to extract all capability contracts
2. Generate markdown documentation
3. Include in `ARCHITECTURE.md` or separate `CAPABILITY_CONTRACTS.md`

**Script:** `scripts/generate_capability_docs.py`
```python
"""
Generate capability documentation from contracts.
"""

import inspect
from pathlib import Path
import json

def extract_capability_contracts():
    """Extract all capability contracts from agents."""
    contracts = {}
    
    # Import all agents
    from app.agents.financial_analyst import FinancialAnalyst
    from app.agents.macro_hound import MacroHound
    from app.agents.data_harvester import DataHarvester
    from app.agents.claude_agent import ClaudeAgent
    
    agents = [FinancialAnalyst, MacroHound, DataHarvester, ClaudeAgent]
    
    for agent_class in agents:
        for name, method in inspect.getmembers(agent_class, inspect.isfunction):
            if hasattr(method, '__capability_contract__'):
                contract = method.__capability_contract__
                contracts[contract['name']] = contract
    
    return contracts

def generate_docs(contracts):
    """Generate markdown documentation."""
    md = "# Capability Contracts\n\n"
    md += "Auto-generated from capability decorators.\n\n"
    
    for name, contract in sorted(contracts.items()):
        md += f"## {name}\n\n"
        md += f"**Status:** {contract['implementation_status']}\n\n"
        if contract.get('description'):
            md += f"{contract['description']}\n\n"
        
        md += "### Inputs\n\n"
        for param, param_type in contract['inputs'].items():
            md += f"- `{param}`: `{param_type.__name__}`\n"
        
        md += "\n### Outputs\n\n"
        for field, field_type in contract['outputs'].items():
            md += f"- `{field}`: `{field_type.__name__}`\n"
        
        if contract.get('dependencies'):
            md += "\n### Dependencies\n\n"
            for dep in contract['dependencies']:
                md += f"- `{dep}`\n"
        
        md += "\n---\n\n"
    
    return md

if __name__ == "__main__":
    contracts = extract_capability_contracts()
    docs = generate_docs(contracts)
    
    output_path = Path("CAPABILITY_CONTRACTS.md")
    output_path.write_text(docs)
    print(f"Generated {len(contracts)} capability contracts in {output_path}")
```

**Output:** `CAPABILITY_CONTRACTS.md` - Auto-generated documentation

---

### Task 2.1 Summary

**Time:** 16 hours  
**Files Changed:** 4 agent files + 1 new file
- `backend/app/core/capability_contract.py` (new)
- `backend/app/agents/financial_analyst.py`
- `backend/app/agents/macro_hound.py`
- `backend/app/agents/data_harvester.py`
- `backend/app/agents/claude_agent.py`
- `CAPABILITY_CONTRACTS.md` (generated)

**Result:** All capabilities have documented contracts, self-documenting code

---

## Task 2.2: Add Step Dependency Validation (8 hours)

### Root Issue

**Problem:** Patterns can reference undefined steps, errors discovered at runtime with cryptic messages.

**Current State:**
- Patterns validated at runtime only
- Undefined step references cause runtime errors
- Cryptic error messages
- Forward references not caught

**Root Cause:** No compile-time validation for pattern step dependencies.

### Implementation Plan

#### Step 2.2.1: Design Validation System (1 hour)

**Goal:** Design a system to validate pattern step dependencies.

**Validation Requirements:**
1. **Catch undefined references** - Step references must exist
2. **Prevent forward references** - Steps can only reference previous steps
3. **Clear error messages** - Show what's wrong and what's available
4. **Template validation** - Validate template references ({{foo.bar}})

**Validation Checks:**
1. All referenced steps exist
2. No forward references (step references only previous steps)
3. Template variables resolve correctly
4. Required inputs provided

---

#### Step 2.2.2: Implement Validation Function (3 hours)

**File:** `backend/app/core/pattern_orchestrator.py`

**Location:** Add validation method to `PatternOrchestrator` class

**Implementation:**
```python
def validate_pattern_dependencies(self, pattern_id: str) -> Dict[str, Any]:
    """
    Validate pattern step dependencies.
    
    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    spec = self.patterns.get(pattern_id)
    if not spec:
        return {
            "valid": False,
            "errors": [f"Pattern '{pattern_id}' not found"],
            "warnings": []
        }
    
    errors = []
    warnings = []
    steps = spec.get("steps", [])
    defined_outputs = set(["ctx", "inputs"])  # Always available
    
    for i, step in enumerate(steps):
        step_name = step.get("as", f"step_{i}")
        defined_outputs.add(step_name)
        
        # Check template references in args
        args = step.get("args", {})
        for key, value in args.items():
            if isinstance(value, str) and "{{" in value:
                # Extract template references
                template_refs = self._extract_template_references(value)
                for ref in template_refs:
                    # Check if reference exists
                    if not self._validate_template_reference(ref, defined_outputs):
                        errors.append(
                            f"Step {i} ({step.get('capability', 'unknown')}): "
                            f"Template reference '{{{{ {ref} }}}}' not found. "
                            f"Available: {sorted(list(defined_outputs))}"
                        )
        
        # Check condition template references
        if "condition" in step:
            condition = step["condition"]
            template_refs = self._extract_template_references(condition)
            for ref in template_refs:
                if not self._validate_template_reference(ref, defined_outputs):
                    errors.append(
                        f"Step {i} condition: "
                        f"Template reference '{{{{ {ref} }}}}' not found. "
                        f"Available: {sorted(list(defined_outputs))}"
                    )
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def _extract_template_references(self, text: str) -> List[str]:
    """Extract template references from text."""
    import re
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, text)
    return [match.strip() for match in matches]

def _validate_template_reference(self, ref: str, defined_outputs: set) -> bool:
    """Validate template reference exists."""
    # Handle nested references (e.g., "positions.positions")
    parts = ref.split(".")
    first_part = parts[0]
    
    # Check if first part exists
    if first_part not in defined_outputs:
        return False
    
    # If nested, validate path exists (basic check)
    # Full validation would require actual state, so we just check first part
    return True
```

**Testing:**
1. Test with valid patterns
2. Test with invalid patterns (undefined references)
3. Test with forward references
4. Verify error messages are clear

---

#### Step 2.2.3: Integrate Validation into Pattern Execution (2 hours)

**File:** `backend/app/core/pattern_orchestrator.py`

**Location:** Add validation call in `run_pattern` method

**Implementation:**
```python
async def run_pattern(
    self,
    pattern_id: str,
    ctx: RequestCtx,
    inputs: Dict[str, Any],
) -> Dict[str, Any]:
    """Run pattern with dependency validation."""
    
    # Validate pattern dependencies
    validation_result = self.validate_pattern_dependencies(pattern_id)
    if not validation_result["valid"]:
        error_msg = "Pattern validation failed:\n" + "\n".join(validation_result["errors"])
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if validation_result["warnings"]:
        for warning in validation_result["warnings"]:
            logger.warning(f"Pattern validation warning: {warning}")
    
    # Continue with existing pattern execution...
    ...
```

**Testing:**
1. Test with valid patterns (should work)
2. Test with invalid patterns (should fail with clear error)
3. Verify error messages are helpful

---

#### Step 2.2.4: Add Validation to Pattern Loading (2 hours)

**File:** `backend/app/core/pattern_orchestrator.py`

**Location:** Add validation call in `_load_patterns` method

**Implementation:**
```python
def _load_patterns(self):
    """Load all patterns and validate dependencies."""
    patterns_dir = Path(__file__).parent.parent.parent / "patterns"
    if not patterns_dir.exists():
        logger.warning(f"Patterns directory not found: {patterns_dir}")
        return

    pattern_count = 0
    for pattern_file in patterns_dir.rglob("*.json"):
        try:
            spec = json.loads(pattern_file.read_text())
            
            # Validate required fields
            required = ["id", "name", "steps", "outputs"]
            missing = [f for f in required if f not in spec]
            if missing:
                logger.error(
                    f"Pattern {pattern_file.name} missing required fields: {missing}"
                )
                continue
            
            pattern_id = spec["id"]
            self.patterns[pattern_id] = spec
            
            # Validate pattern dependencies
            validation_result = self.validate_pattern_dependencies(pattern_id)
            if not validation_result["valid"]:
                logger.error(
                    f"Pattern {pattern_id} failed validation:\n"
                    + "\n".join(validation_result["errors"])
                )
                # Still load pattern, but log error
            elif validation_result["warnings"]:
                for warning in validation_result["warnings"]:
                    logger.warning(f"Pattern {pattern_id}: {warning}")
            
            pattern_count += 1
            
        except Exception as e:
            logger.error(f"Error loading pattern {pattern_file}: {e}")
    
    logger.info(f"Loaded {pattern_count} patterns")
```

**Testing:**
1. Test pattern loading with valid patterns
2. Test pattern loading with invalid patterns
3. Verify errors are logged but don't crash

---

### Task 2.2 Summary

**Time:** 8 hours  
**Files Changed:** 1 file
- `backend/app/core/pattern_orchestrator.py`

**Result:** Pattern dependencies validated, clear error messages

---

## Task 2.3: Build Pattern Linter CLI (8 hours)

### Root Issue

**Problem:** No automated validation, issues discovered at runtime.

**Current State:**
- Patterns validated only at runtime
- No way to validate all patterns before deployment
- No CI/CD integration

**Root Cause:** Lack of automated validation tool.

### Implementation Plan

#### Step 2.3.1: Design CLI Tool (1 hour)

**Goal:** Design a CLI tool to validate all patterns.

**Requirements:**
1. Validate single pattern or all patterns
2. Check dependencies, contracts, formats
3. Output clear errors and warnings
4. CI/CD friendly (exit codes)

**CLI Interface:**
```bash
# Validate single pattern
python -m app.core.pattern_linter --pattern portfolio_cycle_risk

# Validate all patterns
python -m app.core.pattern_linter --all

# Validate and output JSON
python -m app.core.pattern_linter --all --json

# Exit with error code if validation fails
python -m app.core.pattern_linter --all --strict
```

---

#### Step 2.3.2: Implement CLI Tool (5 hours)

**File:** `backend/app/core/pattern_linter.py` (new file)

**Implementation:**
```python
"""
Pattern Linter CLI Tool

Purpose: Validate all patterns before deployment
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from app.core.pattern_orchestrator import PatternOrchestrator
from app.core.agent_runtime import AgentRuntime


class PatternLinter:
    """Pattern linter for validation."""
    
    def __init__(self, orchestrator: PatternOrchestrator):
        self.orchestrator = orchestrator
    
    def lint_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """Lint a single pattern."""
        results = {
            "pattern_id": pattern_id,
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        # Check if pattern exists
        if pattern_id not in self.orchestrator.patterns:
            results["valid"] = False
            results["errors"].append(f"Pattern '{pattern_id}' not found")
            return results
        
        spec = self.orchestrator.patterns[pattern_id]
        
        # Check 1: Dependency validation
        validation_result = self.orchestrator.validate_pattern_dependencies(pattern_id)
        results["checks"]["dependencies"] = validation_result
        if not validation_result["valid"]:
            results["valid"] = False
            results["errors"].extend(validation_result["errors"])
        results["warnings"].extend(validation_result["warnings"])
        
        # Check 2: Output format validation
        outputs = spec.get("outputs", [])
        if not isinstance(outputs, list):
            results["valid"] = False
            results["errors"].append(
                f"Outputs must be a list, got {type(outputs).__name__}"
            )
        else:
            results["checks"]["output_format"] = {"valid": True, "format": "list"}
        
        # Check 3: Step "as" keys match output keys
        steps = spec.get("steps", [])
        step_keys = {step.get("as") for step in steps if step.get("as")}
        output_keys = set(outputs)
        
        missing_in_outputs = step_keys - output_keys
        missing_in_steps = output_keys - step_keys
        
        if missing_in_outputs:
            results["valid"] = False
            results["errors"].append(
                f"Step 'as' keys not in outputs: {sorted(missing_in_outputs)}"
            )
        
        if missing_in_steps:
            results["warnings"].append(
                f"Output keys not in step 'as' keys: {sorted(missing_in_steps)}"
            )
        
        results["checks"]["step_output_match"] = {
            "valid": len(missing_in_outputs) == 0,
            "missing_in_outputs": list(missing_in_outputs),
            "missing_in_steps": list(missing_in_steps),
        }
        
        # Check 4: Capability validation
        capabilities = [step.get("capability") for step in steps if step.get("capability")]
        missing_capabilities = []
        for capability in capabilities:
            if capability not in self.orchestrator.agent_runtime.capability_map:
                missing_capabilities.append(capability)
        
        if missing_capabilities:
            results["valid"] = False
            results["errors"].append(
                f"Capabilities not found: {missing_capabilities}"
            )
        
        results["checks"]["capabilities"] = {
            "valid": len(missing_capabilities) == 0,
            "missing": missing_capabilities,
        }
        
        return results
    
    def lint_all(self) -> Dict[str, Any]:
        """Lint all patterns."""
        all_results = {
            "valid": True,
            "patterns": {},
            "summary": {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "errors": 0,
                "warnings": 0,
            }
        }
        
        for pattern_id in self.orchestrator.patterns.keys():
            result = self.lint_pattern(pattern_id)
            all_results["patterns"][pattern_id] = result
            
            all_results["summary"]["total"] += 1
            if result["valid"]:
                all_results["summary"]["valid"] += 1
            else:
                all_results["summary"]["invalid"] += 1
                all_results["valid"] = False
            
            all_results["summary"]["errors"] += len(result["errors"])
            all_results["summary"]["warnings"] += len(result["warnings"])
        
        return all_results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Pattern linter")
    parser.add_argument("--pattern", help="Pattern ID to validate")
    parser.add_argument("--all", action="store_true", help="Validate all patterns")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--strict", action="store_true", help="Exit with error code if validation fails")
    
    args = parser.parse_args()
    
    # Initialize orchestrator (requires agent runtime)
    # This is a simplified version - real implementation would need proper initialization
    from app.db.connection import get_db_pool
    from combined_server import get_agent_runtime
    
    agent_runtime = get_agent_runtime()
    db_pool = get_db_pool()
    
    orchestrator = PatternOrchestrator(agent_runtime, db_pool)
    linter = PatternLinter(orchestrator)
    
    if args.pattern:
        result = linter.lint_pattern(args.pattern)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Pattern: {result['pattern_id']}")
            print(f"Valid: {result['valid']}")
            if result['errors']:
                print("\nErrors:")
                for error in result['errors']:
                    print(f"  - {error}")
            if result['warnings']:
                print("\nWarnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
        
        if args.strict and not result['valid']:
            sys.exit(1)
    
    elif args.all:
        results = linter.lint_all()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Total patterns: {results['summary']['total']}")
            print(f"Valid: {results['summary']['valid']}")
            print(f"Invalid: {results['summary']['invalid']}")
            print(f"Errors: {results['summary']['errors']}")
            print(f"Warnings: {results['summary']['warnings']}")
            
            for pattern_id, result in results['patterns'].items():
                if not result['valid']:
                    print(f"\n{pattern_id}:")
                    for error in result['errors']:
                        print(f"  ERROR: {error}")
        
        if args.strict and not results['valid']:
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

**Testing:**
1. Test with single pattern
2. Test with all patterns
3. Test JSON output
4. Test strict mode (exit codes)

---

#### Step 2.3.3: Add CI/CD Integration Documentation (2 hours)

**Goal:** Document how to use pattern linter in CI/CD.

**Files to Create:**
1. `scripts/lint_patterns.sh` - Shell script wrapper
2. `docs/PATTERN_LINTER.md` - Documentation

**Content:**
```markdown
# Pattern Linter

## Usage

```bash
# Validate all patterns
python -m app.core.pattern_linter --all

# Validate single pattern
python -m app.core.pattern_linter --pattern portfolio_cycle_risk

# CI/CD mode (exit with error if validation fails)
python -m app.core.pattern_linter --all --strict
```

## CI/CD Integration

Add to `.github/workflows/` (if restored) or run manually before deployment:

```yaml
- name: Validate Patterns
  run: python -m app.core.pattern_linter --all --strict
```
```

---

### Task 2.3 Summary

**Time:** 8 hours  
**Files Changed:** 2 new files
- `backend/app/core/pattern_linter.py` (new)
- `docs/PATTERN_LINTER.md` (new)

**Result:** Automated pattern validation, CI/CD ready

---

## Phase 2 Complete Validation

### Success Criteria

**Task 2.1: Capability Contracts**
- ✅ Capability decorator created
- ✅ All 70 capabilities documented
- ✅ Capability documentation generated

**Task 2.2: Step Dependency Validation**
- ✅ Pattern dependency validation implemented
- ✅ Clear error messages for undefined references
- ✅ Forward references prevented

**Task 2.3: Pattern Linter CLI**
- ✅ Pattern linter CLI tool created
- ✅ Validates all patterns automatically
- ✅ CI/CD integration documented

### End-to-End Testing

**Test Scenarios:**
1. Run pattern linter on all patterns
2. Verify capability contracts are documented
3. Test pattern dependency validation
4. Verify CI/CD integration works

---

## Phase 2 Summary

**Total Time:** 32 hours (Weeks 2-3)  
**Files Changed:** 7 files (4 agent files + 3 new files)
- `backend/app/core/capability_contract.py` (new)
- `backend/app/agents/financial_analyst.py`
- `backend/app/agents/macro_hound.py`
- `backend/app/agents/data_harvester.py`
- `backend/app/agents/claude_agent.py`
- `backend/app/core/pattern_orchestrator.py`
- `backend/app/core/pattern_linter.py` (new)
- `CAPABILITY_CONTRACTS.md` (generated)
- `docs/PATTERN_LINTER.md` (new)

**Result:**
- ✅ All capabilities have documented contracts
- ✅ Pattern dependencies validated
- ✅ Automated pattern validation
- ✅ No bad patterns can be deployed

---

## Next Steps

**After Phase 2:**
1. **Phase 3:** Feature implementation (48 hours)
2. **Phase 4:** Technical debt cleanup (conditional)
3. **Phase 5:** Quality & testing (24 hours)

---

**Status:** Ready for execution
