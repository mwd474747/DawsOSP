# Phase 2 Detailed Plan: Foundation & Code Quality

**Date:** January 14, 2025  
**Status:** 📋 **PLANNING**  
**Purpose:** Comprehensive Phase 2 plan incorporating Phase 1 learnings, integration patterns, anti-patterns, and duplication analysis

---

## 📊 Executive Summary

**Phase 2 Goal:** Prevent future issues, improve developer experience, eliminate duplication, and establish patterns for maintainability

**Key Differences from Phase 1:**
- Phase 1 focused on **user-facing critical fixes** (provenance warnings, pattern output extraction)
- Phase 2 focuses on **developer experience and code quality** (validation, contracts, helper functions)
- Phase 1 was reactive (fixing broken things)
- Phase 2 is proactive (preventing future issues)

**Integration Considerations:**
- Phase 1 output extraction fixes affect how patterns are validated
- Phase 1 pattern format standardization enables better validation
- Phase 1 provenance warnings establish pattern for capability contracts

**Timeline:** 3-4 weeks (60-80 hours)

---

## 🔍 Phase 1 Learnings & Impact on Phase 2

### Phase 1 Completed Work

1. **Provenance Warnings** ✅
   - Added `_provenance` field to stub data
   - Established pattern for capability metadata
   - **Impact on Phase 2:** Can extend this pattern to capability contracts

2. **Pattern Output Extraction** ✅
   - Fixed orchestrator to handle 3 output formats
   - Updated 6 patterns to standard list format
   - **Impact on Phase 2:** Validation can assume standard format, simplifies contract definition

3. **Scenario Analysis Fixes** ✅
   - Migration 009 applied (scenario tables created)
   - SQL query fixes (correct column names)
   - AttributeError fixes (shock_type handling)
   - **Impact on Phase 2:** No blocking issues, can focus on duplication cleanup

4. **Field Naming Standardization** ✅
   - Agent layer standardized to `quantity`
   - Database layer uses `quantity_open`, `quantity_original`
   - **Impact on Phase 2:** Helper functions can use standardized field names

### Phase 1 Discoveries Relevant to Phase 2

1. **Pattern Output Format Standardization**
   - **Discovery:** 3 incompatible formats existed, causing silent failures
   - **Phase 1 Fix:** Standardized to list format
   - **Phase 2 Impact:** Validation can enforce standard format, contracts can document expected outputs

2. **Pattern Orchestrator Complexity**
   - **Discovery:** Orchestrator had to handle multiple formats, causing complexity
   - **Phase 1 Fix:** Enhanced to handle all formats correctly
   - **Phase 2 Impact:** Can simplify orchestrator by enforcing standard format through validation

3. **Stub Data Pattern**
   - **Discovery:** Silent stub data without warnings
   - **Phase 1 Fix:** Added `_provenance` field with warnings
   - **Phase 2 Impact:** Capability contracts can document `implementation_status` and prevent silent stubs

---

## 📋 Phase 2 Detailed Plan

### Phase 2A: Helper Functions & Duplication Elimination (Week 1 - 20 hours)

**Goal:** Eliminate duplicate SQL queries and position extraction patterns

#### Task 2A.1: Create Position Extraction Helper Functions (8 hours)

**Problem Analysis:**
- **7 files** query `FROM lots` directly:
  - `backend/app/services/scenarios.py` - `get_position_betas()` (lines 315-377)
  - `backend/app/services/currency_attribution.py` - Position queries
  - `backend/app/services/risk_metrics.py` - Position queries
  - `backend/app/services/portfolio_helpers.py` - Position queries
  - `backend/app/services/optimizer.py` - Position queries
  - `backend/app/services/risk.py` - Position queries
  - `backend/app/agents/financial_analyst.py` - `ledger_positions()` (lines 145-219)

**Duplication Identified:**
1. **Position Query Pattern** (repeated 7+ times):
   ```sql
   SELECT
       l.symbol,
       l.quantity_open AS quantity,
       l.cost_basis_per_share,
       l.currency,
       l.quantity_open * l.cost_basis_per_share AS market_value,
       s.security_type,
       s.sector,
       -- ... additional fields
   FROM lots l
   LEFT JOIN securities s ON l.symbol = s.symbol
   WHERE l.portfolio_id = $1
     AND l.is_open = true
     AND l.quantity_open > 0
   ```

2. **Position with Pricing Pattern** (repeated 6+ times):
   - Get positions from ledger
   - Apply pricing pack
   - Convert currencies
   - Calculate values

**Solution:**
Create helper functions in `backend/app/services/portfolio_helpers.py`:

```python
async def get_portfolio_positions(
    portfolio_id: str,
    include_fields: Optional[List[str]] = None,
    include_security_metadata: bool = True,
    include_factor_betas: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get portfolio positions from database.
    
    Standardized position extraction that all services should use.
    
    Args:
        portfolio_id: Portfolio UUID
        include_fields: Optional list of additional fields to include
        include_security_metadata: Include security type, sector, etc.
        include_factor_betas: Include factor betas from position_factor_betas table
    
    Returns:
        List of position dicts with standardized fields:
        - symbol: str
        - quantity: Decimal (standardized from quantity_open)
        - cost_basis_per_share: Decimal
        - currency: str
        - market_value: Decimal (quantity * cost_basis_per_share)
        - security_type: str (if include_security_metadata)
        - sector: str (if include_security_metadata)
        - real_rate_beta: Decimal (if include_factor_betas)
        - inflation_beta: Decimal (if include_factor_betas)
        - ... other factor betas
    """
    # Implementation uses standardized query pattern
    # All services use this instead of duplicating SQL
```

**Integration Points:**
- Replace `get_position_betas()` in `scenarios.py` to use helper
- Replace `ledger_positions()` in `financial_analyst.py` to use helper
- Replace position queries in `currency_attribution.py`, `risk_metrics.py`, `optimizer.py`, `risk.py`
- Update `portfolio.get_valued_positions` capability to use helper internally

**Validation:**
- All existing functionality preserved
- Field names standardized (`quantity` in results, `quantity_open` in database)
- No regression in pattern execution

**Files to Modify:**
1. `backend/app/services/portfolio_helpers.py` - Create helper functions
2. `backend/app/services/scenarios.py` - Replace `get_position_betas()` with helper
3. `backend/app/agents/financial_analyst.py` - Replace `ledger_positions()` with helper
4. `backend/app/services/currency_attribution.py` - Replace position queries
5. `backend/app/services/risk_metrics.py` - Replace position queries
6. `backend/app/services/optimizer.py` - Replace position queries
7. `backend/app/services/risk.py` - Replace position queries

**Estimated Time:** 8 hours
- 2 hours: Design helper function interface
- 4 hours: Implement helper function
- 2 hours: Refactor all 7 files to use helper
- 2 hours: Testing and validation

---

#### Task 2A.2: Create Pricing Pack Helper Functions (4 hours)

**Problem Analysis:**
- **5 services** duplicate `_get_pack_date()` logic:
  - `backend/app/services/pricing.py`
  - `backend/app/services/scenarios.py`
  - `backend/app/services/metrics.py`
  - `backend/app/services/currency_attribution.py`
  - `backend/app/services/optimizer.py`

**Duplication Identified:**
```python
# Pattern repeated 5 times:
def _get_pack_date(pack: Dict) -> date:
    """Extract date from pricing pack."""
    # Inconsistent field names: "date" vs "asof_date" vs "as_of_date"
    # Causes bugs when field name changes
```

**Solution:**
Create standardized helper in `backend/app/services/pricing.py`:

```python
def extract_pack_date(pack: Dict[str, Any]) -> date:
    """
    Extract date from pricing pack.
    
    Standardized date extraction that handles all field name variations.
    
    Args:
        pack: Pricing pack dict
    
    Returns:
        date object
    
    Raises:
        ValueError: If date cannot be extracted
    """
    # Try multiple field names (date, asof_date, as_of_date)
    # Handle both string and date types
    # Provide clear error messages
```

**Integration Points:**
- All services use `extract_pack_date()` instead of custom logic
- Pricing service becomes single source of truth for pack date extraction
- Field name changes only need to be updated in one place

**Files to Modify:**
1. `backend/app/services/pricing.py` - Create `extract_pack_date()` helper
2. `backend/app/services/scenarios.py` - Use helper
3. `backend/app/services/metrics.py` - Use helper
4. `backend/app/services/currency_attribution.py` - Use helper
5. `backend/app/services/optimizer.py` - Use helper

**Estimated Time:** 4 hours
- 1 hour: Design helper function interface
- 1 hour: Implement helper function
- 2 hours: Refactor all 5 files to use helper

---

#### Task 2A.3: Create Portfolio Value Helper Functions (4 hours)

**Problem Analysis:**
- **3+ services** duplicate portfolio NAV calculation:
  - `backend/app/services/scenarios.py` - `SUM(quantity_open * cost_basis_per_share)`
  - `backend/app/services/metrics.py` - Portfolio value calculations
  - `backend/app/services/currency_attribution.py` - Portfolio value calculations

**Duplication Identified:**
```sql
-- Pattern repeated 3+ times:
SELECT SUM(quantity_open * cost_basis_per_share) AS nav
FROM lots
WHERE portfolio_id = $1
  AND is_open = true
  AND quantity_open > 0
```

**Solution:**
Create helper function in `backend/app/services/portfolio_helpers.py`:

```python
async def get_portfolio_nav(
    portfolio_id: str,
    pack_id: Optional[str] = None,
    base_currency: Optional[str] = None,
) -> Decimal:
    """
    Get portfolio NAV (Net Asset Value).
    
    Standardized NAV calculation that all services should use.
    
    Args:
        portfolio_id: Portfolio UUID
        pack_id: Optional pricing pack ID (uses current prices if provided)
        base_currency: Optional base currency for conversion
    
    Returns:
        Decimal NAV value
    """
    # Implementation:
    # - If pack_id provided: Use current prices from pack
    # - If base_currency provided: Convert to base currency
    # - Otherwise: Use cost basis (quantity_open * cost_basis_per_share)
```

**Integration Points:**
- Replace NAV calculations in `scenarios.py`
- Replace NAV calculations in `metrics.py`
- Replace NAV calculations in `currency_attribution.py`
- Update `portfolio.get_valued_positions` to use helper for total value

**Files to Modify:**
1. `backend/app/services/portfolio_helpers.py` - Create `get_portfolio_nav()` helper
2. `backend/app/services/scenarios.py` - Use helper
3. `backend/app/services/metrics.py` - Use helper
4. `backend/app/services/currency_attribution.py` - Use helper

**Estimated Time:** 4 hours
- 1 hour: Design helper function interface
- 1 hour: Implement helper function
- 2 hours: Refactor all 3 files to use helper

---

#### Task 2A.4: Consolidate Pattern Position Extraction (4 hours)

**Problem Analysis:**
- **6 patterns** use 2-step sequence: `ledger.positions` → `pricing.apply_pack`
- **1 pattern** uses optimized capability: `portfolio.get_valued_positions`
- **Pattern:** Created in Phase 3 Week 3/4 (November 5, 2025) but not used consistently

**Duplication Identified:**
```json
// Pattern repeated 6 times:
{
  "steps": [
    {"capability": "ledger.positions", "as": "positions"},
    {"capability": "pricing.apply_pack", "args": {"positions": "{{positions}}"}, "as": "valued_positions"}
  ]
}
```

**Solution:**
Update all 6 patterns to use `portfolio.get_valued_positions`:

```json
// Optimized single step:
{
  "steps": [
    {"capability": "portfolio.get_valued_positions", "as": "valued_positions"}
  ]
}
```

**Integration Points:**
- Patterns become simpler (1 step instead of 2)
- Consistent with optimized pattern introduced in Phase 3
- Reduces pattern execution time
- Easier to maintain

**Patterns to Update:**
1. `backend/patterns/portfolio_overview.json` - Already uses optimized pattern ✅
2. `backend/patterns/portfolio_scenario_analysis.json` - Update to use optimized pattern
3. `backend/patterns/cycle_deleveraging_scenarios.json` - Update to use optimized pattern
4. `backend/patterns/portfolio_cycle_risk.json` - Update to use optimized pattern
5. `backend/patterns/portfolio_macro_overview.json` - Update to use optimized pattern
6. `backend/patterns/holding_deep_dive.json` - Update to use optimized pattern

**Files to Modify:**
1. `backend/patterns/portfolio_scenario_analysis.json`
2. `backend/patterns/cycle_deleveraging_scenarios.json`
3. `backend/patterns/portfolio_cycle_risk.json`
4. `backend/patterns/portfolio_macro_overview.json`
5. `backend/patterns/holding_deep_dive.json`

**Estimated Time:** 4 hours
- 1 hour: Review all patterns for position extraction
- 2 hours: Update 5 patterns to use optimized capability
- 1 hour: Testing and validation

---

### Phase 2B: Capability Contracts & Validation (Week 2 - 24 hours)

**Goal:** Prevent future issues through compile-time validation and self-documenting code

#### Task 2B.1: Create Capability Contract System (12 hours)

**Problem Analysis:**
- No clear interface definition for capabilities
- Stub vs real implementation not documented
- Input/output types not defined
- Errors discovered at runtime

**Solution:**
Create capability contract decorator system:

```python
# backend/app/core/capability_contract.py

from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

class ImplementationStatus(Enum):
    REAL = "real"
    STUB = "stub"
    PARTIAL = "partial"

@dataclass
class CapabilityContract:
    """Contract definition for a capability."""
    name: str
    inputs: Dict[str, type]  # Input parameter types
    outputs: Dict[str, type]  # Output field types
    implementation_status: ImplementationStatus
    description: str
    warnings: Optional[List[str]] = None
    fetches_positions: bool = False  # Documents internal behavior
    requires_pricing_pack: bool = False
    requires_ledger: bool = False

def capability(
    name: str,
    inputs: Dict[str, type],
    outputs: Dict[str, type],
    implementation_status: ImplementationStatus = ImplementationStatus.REAL,
    description: str = "",
    warnings: Optional[List[str]] = None,
    fetches_positions: bool = False,
    requires_pricing_pack: bool = False,
    requires_ledger: bool = False,
):
    """
    Decorator to define capability contract.
    
    Example:
        @capability(
            name="risk.compute_factor_exposures",
            inputs={"portfolio_id": str, "pack_id": str},
            outputs={"factors": dict, "r_squared": float, "_provenance": dict},
            implementation_status=ImplementationStatus.STUB,
            description="Compute factor exposures via regression",
            warnings=["Feature not implemented - using fallback data"],
            fetches_positions=True,
            requires_pricing_pack=True,
        )
        async def risk_compute_factor_exposures(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Attach contract to function
        func._capability_contract = CapabilityContract(
            name=name,
            inputs=inputs,
            outputs=outputs,
            implementation_status=implementation_status,
            description=description,
            warnings=warnings or [],
            fetches_positions=fetches_positions,
            requires_pricing_pack=requires_pricing_pack,
            requires_ledger=requires_ledger,
        )
        return func
    return decorator
```

**Integration Points:**
- Agent capabilities use `@capability` decorator
- Pattern orchestrator validates contracts at runtime
- Pattern linter validates contracts at development time
- Documentation generated from contracts

**Files to Create:**
1. `backend/app/core/capability_contract.py` - Contract system

**Files to Modify:**
1. `backend/app/agents/financial_analyst.py` - Add contracts to all 30 capabilities
2. `backend/app/agents/macro_hound.py` - Add contracts to all 17+ capabilities
3. `backend/app/agents/data_harvester.py` - Add contracts to all 8+ capabilities
4. `backend/app/agents/claude_agent.py` - Add contracts to all 6 capabilities

**Estimated Time:** 12 hours
- 2 hours: Design contract system
- 2 hours: Implement contract decorator
- 6 hours: Add contracts to all 60+ capabilities
- 2 hours: Testing and validation

---

#### Task 2B.2: Add Step Dependency Validation (8 hours)

**Problem Analysis:**
- Patterns can reference undefined steps
- Errors discovered at runtime with cryptic messages
- No validation before pattern execution

**Solution:**
Enhance pattern validation to check step dependencies:

```python
# backend/app/core/pattern_orchestrator.py

def validate_pattern(
    self,
    pattern_id: str,
    inputs: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Validate pattern before execution.
    
    Enhanced validation that checks:
    - All referenced steps exist
    - All capabilities are registered
    - All inputs have correct types
    - Step dependency order is correct
    - Template variables are valid
    """
    errors = []
    warnings = []
    
    # ... existing validation ...
    
    # NEW: Step dependency validation
    step_results = {}
    for step_idx, step in enumerate(spec["steps"]):
        step_key = step.get("as", f"step_{step_idx}")
        step_results[step_key] = True
        
        # Check template references in args
        args = step.get("args", {})
        for arg_value in args.values():
            if isinstance(arg_value, str) and "{{" in arg_value:
                # Extract template variables
                template_vars = self._extract_template_vars(arg_value)
                for var in template_vars:
                    # Check if variable is defined
                    if not self._is_template_var_defined(var, step_results, inputs):
                        errors.append(
                            f"Step {step_idx} references undefined variable: {var}\n"
                            f"  Available: {list(step_results.keys()) + ['inputs', 'ctx']}"
                        )
    
    # NEW: Capability registration validation
    for step in spec["steps"]:
        capability = step["capability"]
        if not self.agent_runtime.has_capability(capability):
            errors.append(
                f"Capability '{capability}' is not registered\n"
                f"  Available: {self.agent_runtime.list_capabilities()}"
            )
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
```

**Integration Points:**
- Pattern orchestrator validates before execution
- Pattern linter validates at development time
- Clear error messages guide developers

**Files to Modify:**
1. `backend/app/core/pattern_orchestrator.py` - Enhance `validate_pattern()` method

**Estimated Time:** 8 hours
- 2 hours: Design validation logic
- 4 hours: Implement step dependency validation
- 2 hours: Testing and validation

---

#### Task 2B.3: Build Pattern Linter CLI (4 hours)

**Problem Analysis:**
- No automated validation before deployment
- Errors discovered at runtime
- No CI/CD integration

**Solution:**
Create CLI tool to validate all patterns:

```python
# backend/scripts/pattern_linter.py

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

def lint_patterns(pattern_dir: str = "backend/patterns") -> int:
    """
    Lint all patterns and report errors.
    
    Returns:
        Exit code (0 = success, 1 = errors found)
    """
    errors = []
    pattern_files = Path(pattern_dir).glob("*.json")
    
    for pattern_file in pattern_files:
        # Load pattern
        with open(pattern_file) as f:
            pattern = json.load(f)
        
        # Validate pattern structure
        errors.extend(validate_pattern_structure(pattern, pattern_file))
        
        # Validate step dependencies
        errors.extend(validate_step_dependencies(pattern, pattern_file))
        
        # Validate capability contracts
        errors.extend(validate_capability_contracts(pattern, pattern_file))
    
    # Report errors
    if errors:
        print(f"❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"  {error}")
        return 1
    else:
        print("✅ All patterns valid")
        return 0

if __name__ == "__main__":
    sys.exit(lint_patterns())
```

**Integration Points:**
- Run in CI/CD before deployment
- Run locally before committing
- IDE integration for real-time validation

**Files to Create:**
1. `backend/scripts/pattern_linter.py` - Pattern linter CLI

**Estimated Time:** 4 hours
- 2 hours: Implement linter
- 1 hour: Add CI/CD integration
- 1 hour: Testing and validation

---

### Phase 2C: Documentation & Cleanup (Week 3 - 16 hours)

**Goal:** Document patterns, clean up unused code, improve maintainability

#### Task 2C.1: Document Service Layer Patterns (4 hours)

**Problem Analysis:**
- No clear guidelines on when to use direct DB vs service layer
- Mixed patterns confuse developers
- Unused cache tables create confusion

**Solution:**
Create comprehensive documentation in `DATA_ARCHITECTURE.md`:

```markdown
## Service Layer Patterns

### When to Use Direct Database Access

**Use direct DB access when:**
- Simple CRUD operations
- No complex business logic
- Performance-critical (avoid service overhead)
- Example: `ledger.positions` capability

### When to Use Service Layer

**Use service layer when:**
- Complex business logic
- Multiple data sources
- Caching required
- Example: `metrics.compute_twr` uses `PerformanceCalculator`

### Compute vs Storage Pattern

**Compute On-Demand:**
- Services compute fresh every time
- No cache tables
- Example: `CurrencyAttributionService.compute_attribution()`

**Store and Query:**
- Services write to cache tables
- Subsequent queries read from cache
- Example: `portfolio_daily_values` hypertable

### Helper Functions

**Use helper functions for:**
- Common SQL queries (position extraction)
- Common calculations (portfolio NAV)
- Standardized field name handling
```

**Files to Modify:**
1. `DATA_ARCHITECTURE.md` - Add service layer patterns section

**Estimated Time:** 4 hours
- 2 hours: Document patterns
- 1 hour: Add examples
- 1 hour: Review and refine

---

#### Task 2C.2: Remove Unused Cache Tables (4 hours)

**Problem Analysis:**
- `currency_attribution` table exists but not used
- `factor_exposures` table exists but not used
- Services compute fresh every time
- Wasted database resources

**Solution:**
Create migration to remove unused tables:

```sql
-- Migration 015: Remove Unused Cache Tables

BEGIN;

-- Remove currency_attribution table (services compute on-demand)
DROP TABLE IF EXISTS currency_attribution CASCADE;

-- Remove factor_exposures table (services compute on-demand)
DROP TABLE IF EXISTS factor_exposures CASCADE;

COMMIT;
```

**Integration Points:**
- Document why tables were removed
- Update `DATA_ARCHITECTURE.md` to reflect compute-on-demand pattern
- No code changes needed (tables not used)

**Files to Create:**
1. `backend/db/migrations/015_remove_unused_cache_tables.sql`

**Files to Modify:**
1. `DATABASE.md` - Document Migration 015
2. `DATA_ARCHITECTURE.md` - Update compute vs storage section

**Estimated Time:** 4 hours
- 1 hour: Create migration
- 1 hour: Test migration
- 1 hour: Update documentation
- 1 hour: Validation

---

#### Task 2C.3: Update Development Guide (4 hours)

**Problem Analysis:**
- No guidelines for creating new capabilities
- No guidelines for creating new patterns
- No guidelines for helper functions

**Solution:**
Update `DEVELOPMENT_GUIDE.md` with comprehensive guidelines:

```markdown
## Creating New Capabilities

1. **Add capability contract:**
   ```python
   @capability(
       name="your.capability",
       inputs={"param1": str, "param2": int},
       outputs={"result": dict},
       implementation_status=ImplementationStatus.REAL,
       description="What this capability does",
   )
   async def your_capability(...):
       ...
   ```

2. **Use helper functions:**
   - Use `get_portfolio_positions()` instead of duplicating SQL
   - Use `extract_pack_date()` instead of custom date extraction
   - Use `get_portfolio_nav()` instead of duplicating NAV calculation

3. **Follow field naming standards:**
   - Database: `quantity_open`, `quantity_original`
   - Agent returns: `quantity`
   - Service internal: `qty` (acceptable)

## Creating New Patterns

1. **Use optimized capabilities:**
   - Use `portfolio.get_valued_positions` instead of `ledger.positions` + `pricing.apply_pack`

2. **Use standard output format:**
   ```json
   {
     "outputs": ["output1", "output2", "output3"]
   }
   ```

3. **Validate before committing:**
   ```bash
   python backend/scripts/pattern_linter.py
   ```
```

**Files to Modify:**
1. `DEVELOPMENT_GUIDE.md` - Add comprehensive guidelines

**Estimated Time:** 4 hours
- 2 hours: Write guidelines
- 1 hour: Add examples
- 1 hour: Review and refine

---

#### Task 2C.4: Code Review & Anti-Pattern Cleanup (4 hours)

**Problem Analysis:**
- Inconsistent singleton patterns
- Mixed dependency injection patterns
- Exception handling inconsistencies

**Solution:**
Review and standardize patterns:

1. **Singleton Pattern Standardization:**
   - Review all service singletons
   - Standardize on `get_service()` / `init_service()` pattern
   - Document pattern in `DEVELOPMENT_GUIDE.md`

2. **Exception Handling Standardization:**
   - Review all exception handling
   - Use custom exceptions consistently
   - Document exception hierarchy

3. **Dependency Injection Standardization:**
   - Review all dependency injection patterns
   - Standardize on constructor injection for agents
   - Document pattern in `DEVELOPMENT_GUIDE.md`

**Files to Review:**
1. All service files (28 files)
2. All agent files (4 files)

**Files to Modify:**
1. `DEVELOPMENT_GUIDE.md` - Add pattern guidelines
2. Service files - Standardize patterns (as needed)

**Estimated Time:** 4 hours
- 2 hours: Code review
- 1 hour: Standardize patterns
- 1 hour: Update documentation

---

## 🎯 Integration Points & Dependencies

### Phase 2A Dependencies

**Depends on Phase 1:**
- ✅ Field naming standardization (enables helper functions)
- ✅ Pattern output format standardization (enables pattern consolidation)

**Enables Phase 2B:**
- Helper functions establish patterns for capability contracts
- Pattern consolidation simplifies validation

### Phase 2B Dependencies

**Depends on Phase 2A:**
- Helper functions provide examples for capability contracts
- Pattern consolidation enables better validation

**Enables Phase 2C:**
- Capability contracts provide documentation source
- Validation enables pattern linter

### Phase 2C Dependencies

**Depends on Phase 2A & 2B:**
- Helper functions documented
- Capability contracts documented
- Validation patterns documented

---

## 📊 Success Criteria

### Phase 2A Success Criteria

- [ ] All 7 files use `get_portfolio_positions()` helper
- [ ] All 5 files use `extract_pack_date()` helper
- [ ] All 3 files use `get_portfolio_nav()` helper
- [ ] All 5 patterns use `portfolio.get_valued_positions` capability
- [ ] No duplicate SQL queries remain
- [ ] All existing functionality preserved
- [ ] No regression in pattern execution

### Phase 2B Success Criteria

- [ ] All 60+ capabilities have contracts
- [ ] Pattern validation catches undefined step references
- [ ] Pattern linter runs in CI/CD
- [ ] Clear error messages for validation failures
- [ ] Documentation generated from contracts

### Phase 2C Success Criteria

- [ ] Service layer patterns documented
- [ ] Unused cache tables removed
- [ ] Development guide updated with comprehensive guidelines
- [ ] Code patterns standardized
- [ ] Documentation reflects current state

---

## ⚠️ Risks & Mitigations

### Risk 1: Breaking Changes in Helper Functions

**Risk:** Helper functions may not match all use cases

**Mitigation:**
- Comprehensive parameter design (include_fields, include_security_metadata, etc.)
- Extensive testing before refactoring
- Gradual rollout (one file at a time)

### Risk 2: Capability Contracts Too Restrictive

**Risk:** Contracts may prevent valid use cases

**Mitigation:**
- Contracts are documentation, not strict type checking
- Runtime validation is informative, not blocking
- Contracts can be updated as patterns evolve

### Risk 3: Pattern Linter Too Strict

**Risk:** Linter may flag valid patterns

**Mitigation:**
- Start with warnings, not errors
- Gradual enforcement (warnings → errors)
- Allow exceptions for legacy patterns

---

## 📋 Execution Order

### Week 1: Helper Functions (20 hours)

**Monday (4 hours):** Task 2A.1 - Position extraction helper
**Tuesday (4 hours):** Task 2A.1 - Continue position extraction helper
**Wednesday (4 hours):** Task 2A.2 - Pricing pack helper
**Thursday (4 hours):** Task 2A.3 - Portfolio NAV helper
**Friday (4 hours):** Task 2A.4 - Pattern consolidation

### Week 2: Validation (24 hours)

**Monday (4 hours):** Task 2B.1 - Capability contract system design
**Tuesday (4 hours):** Task 2B.1 - Capability contract implementation
**Wednesday (4 hours):** Task 2B.1 - Add contracts to capabilities
**Thursday (4 hours):** Task 2B.2 - Step dependency validation
**Friday (8 hours):** Task 2B.3 - Pattern linter CLI

### Week 3: Documentation (16 hours)

**Monday (4 hours):** Task 2C.1 - Document service layer patterns
**Tuesday (4 hours):** Task 2C.2 - Remove unused cache tables
**Wednesday (4 hours):** Task 2C.3 - Update development guide
**Thursday (4 hours):** Task 2C.4 - Code review & cleanup

---

## ✅ Summary

**Phase 2 Goal:** Prevent future issues, improve developer experience, eliminate duplication

**Key Deliverables:**
1. Helper functions eliminate duplicate SQL queries
2. Capability contracts provide self-documenting code
3. Pattern validation catches errors before runtime
4. Pattern linter enables CI/CD validation
5. Comprehensive documentation guides developers

**Timeline:** 3-4 weeks (60-80 hours)

**Integration:** Builds on Phase 1 learnings, enables Phase 3 features

**Success Metrics:**
- Zero duplicate SQL queries
- All capabilities documented
- All patterns validated
- Clear developer guidelines

---

**Report Generated:** January 14, 2025  
**Status:** 📋 **PLANNING COMPLETE - READY FOR EXECUTION**

