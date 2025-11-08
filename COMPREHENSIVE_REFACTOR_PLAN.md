# Comprehensive Refactor Plan: Import Error Handling & Architecture Consistency

**Date:** January 15, 2025  
**Status:** 📋 PLAN READY  
**Priority:** P1 (Critical for reliability)  
**Estimated Time:** 4-6 hours

---

## Executive Summary

This plan addresses the root cause of the Replit import failure and prevents similar issues. It refactors import error handling to be granular, adds architecture validation, and ensures all services use proper DI container patterns.

**Key Issues Identified:**
1. ❌ Broad import error handling masks specific failures
2. ❌ Critical imports set to `None` causing runtime errors
3. ❌ No distinction between critical and optional imports
4. ❌ No architecture validation to prevent anti-patterns
5. ⚠️ Debug logging hardcoded to DEBUG level
6. ⚠️ No None value validation in constructors

**Architecture Context:**
- **Database Patterns:** Services use helper functions (`execute_query`, etc.) OR accept `db_pool` parameter for DI
- **RLS Pattern:** User-scoped data uses `get_db_connection_with_rls(user_id)` (agents, API routes)
- **DI Container:** Services registered in `service_initializer.py`, initialized via `initialize_services()`
- **Connection Pool:** Managed via `app.db.connection` module with cross-module storage

---

## Phase 1: Granular Import Error Handling (P1 - Critical)

### Problem

**Current Pattern (combined_server.py:96-119):**
```python
try:
    from app.core.agent_runtime import AgentRuntime
    from app.core.pattern_orchestrator import PatternOrchestrator
    from app.core.types import RequestCtx, ExecReq, ExecResp
    from app.services.metrics import PerformanceCalculator
    from app.services.scenarios import ScenarioService, ShockType
    from app.agents.financial_analyst import FinancialAnalyst
    from app.agents.macro_hound import MacroHound
    from app.agents.data_harvester import DataHarvester
    
    PATTERN_ORCHESTRATION_AVAILABLE = True
    logger.info("Pattern orchestration modules loaded successfully")
except ImportError as e:
    logger.warning(f"Pattern orchestration modules not available: {e}")
    PATTERN_ORCHESTRATION_AVAILABLE = False
    # Create dummy classes to avoid NameErrors
    AgentRuntime = None
    PatternOrchestrator = None
    RequestCtx = None  # ❌ This causes runtime errors!
    PerformanceCalculator = None
    ScenarioService = None
    ShockType = None
    FinancialAnalyst = None
    MacroHound = None
    DataHarvester = None
```

**Issues:**
- ❌ One try/except for all imports - can't identify which failed
- ❌ Critical imports (RequestCtx) set to None - causes runtime errors
- ❌ No distinction between critical and optional imports
- ❌ Masking import failures makes debugging impossible

### Solution

**Refactor to Granular Imports:**

```python
# ============================================================================
# Critical Imports - Fail Fast
# ============================================================================
# These are required for the server to function. If they fail, we should
# fail fast rather than setting to None and causing runtime errors.

try:
    from app.core.types import RequestCtx, ExecReq, ExecResp
    REQUEST_CTX_AVAILABLE = True
except ImportError as e:
    logger.error(f"CRITICAL: RequestCtx not available: {e}")
    logger.error("Cannot start server without RequestCtx. Check imports.")
    raise RuntimeError(f"Cannot start server: RequestCtx import failed: {e}") from e

# ============================================================================
# Core Orchestration Imports - Fail Fast
# ============================================================================
# These are required for pattern execution. Without them, pattern endpoints
# should return errors, not None.

try:
    from app.core.agent_runtime import AgentRuntime
    from app.core.pattern_orchestrator import PatternOrchestrator
    AGENT_RUNTIME_AVAILABLE = True
    PATTERN_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    logger.error(f"CRITICAL: Agent runtime not available: {e}")
    logger.error("Pattern execution will not work. Check imports.")
    # Don't set to None - fail fast or disable pattern endpoints
    AgentRuntime = None
    PatternOrchestrator = None
    AGENT_RUNTIME_AVAILABLE = False
    PATTERN_ORCHESTRATOR_AVAILABLE = False

# ============================================================================
# Service Imports - Use Classes, Not Factories
# ============================================================================
# These should use classes directly, not singleton factory functions.
# If unavailable, we can degrade gracefully.

try:
    from app.services.metrics import PerformanceCalculator
    PERFORMANCE_CALCULATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PerformanceCalculator not available: {e}")
    PerformanceCalculator = None
    PERFORMANCE_CALCULATOR_AVAILABLE = False

try:
    from app.services.scenarios import ScenarioService, ShockType
    SCENARIO_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ScenarioService not available: {e}")
    ScenarioService = None
    ShockType = None
    SCENARIO_SERVICE_AVAILABLE = False

# ============================================================================
# Agent Imports - Use Classes, Not Factories
# ============================================================================
# These should use classes directly. If unavailable, pattern execution
# will fail for those specific capabilities.

try:
    from app.agents.financial_analyst import FinancialAnalyst
    FINANCIAL_ANALYST_AVAILABLE = True
except ImportError as e:
    logger.warning(f"FinancialAnalyst not available: {e}")
    FinancialAnalyst = None
    FINANCIAL_ANALYST_AVAILABLE = False

try:
    from app.agents.macro_hound import MacroHound
    MACRO_HOUND_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MacroHound not available: {e}")
    MacroHound = None
    MACRO_HOUND_AVAILABLE = False

try:
    from app.agents.data_harvester import DataHarvester
    DATA_HARVESTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"DataHarvester not available: {e}")
    DataHarvester = None
    DATA_HARVESTER_AVAILABLE = False

# ============================================================================
# Overall Availability Flag
# ============================================================================
PATTERN_ORCHESTRATION_AVAILABLE = (
    REQUEST_CTX_AVAILABLE and
    AGENT_RUNTIME_AVAILABLE and
    PATTERN_ORCHESTRATOR_AVAILABLE
)

if PATTERN_ORCHESTRATION_AVAILABLE:
    logger.info("Pattern orchestration modules loaded successfully")
else:
    logger.warning("Pattern orchestration partially available - some features may not work")
```

### Implementation Steps

1. **Refactor Import Block** (1 hour)
   - Split into granular try/except blocks
   - Add availability flags for each import
   - Fail fast for critical imports
   - Graceful degradation for optional imports

2. **Update Usage Checks** (30 minutes)
   - Add availability checks before using imports
   - Return proper errors when services unavailable
   - Update pattern execution endpoint to check availability

3. **Test Import Failures** (30 minutes)
   - Test with missing modules
   - Verify error messages are clear
   - Ensure graceful degradation works

---

## Phase 2: Configurable Debug Logging (P2 - High)

### Problem

**Current Pattern (combined_server.py:23-26):**
```python
logging.basicConfig(
    level=logging.DEBUG,  # ❌ Hardcoded to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Issues:**
- ❌ Hardcoded to DEBUG level - too verbose for production
- ❌ No way to configure via environment variable
- ❌ Debug logging in constructors always runs

### Solution

**Make Logging Configurable:**

```python
# Configure logging early before any imports that might use it
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
try:
    log_level_attr = getattr(logging, log_level, logging.INFO)
except AttributeError:
    logger.warning(f"Invalid LOG_LEVEL '{log_level}', defaulting to INFO")
    log_level_attr = logging.INFO

logging.basicConfig(
    level=log_level_attr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Logging configured at level: {log_level}")
```

**Update Constructor Logging:**

```python
# In PatternOrchestrator.__init__
def __init__(self, agent_runtime, db, redis=None):
    # Validate inputs first
    if agent_runtime is None:
        raise ValueError("agent_runtime cannot be None")
    if db is None:
        raise ValueError("db cannot be None")
    
    # Debug logging only if DEBUG level enabled
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Initializing PatternOrchestrator with agent_runtime: {agent_runtime}")
        logger.debug(f"Agent runtime type: {type(agent_runtime)}")
        logger.debug(f"Agent runtime has execute_capability: {hasattr(agent_runtime, 'execute_capability')}")
    
    self.agent_runtime = agent_runtime
    self.db = db
    self.redis = redis
    self.patterns: Dict[str, Dict[str, Any]] = {}
    self._load_patterns()
```

### Implementation Steps

1. **Make Logging Configurable** (15 minutes)
   - Read from environment variable
   - Default to INFO level
   - Validate log level

2. **Update Constructor Logging** (30 minutes)
   - Add None value validation
   - Make debug logging conditional
   - Update all constructors with debug logging

3. **Update Documentation** (15 minutes)
   - Document LOG_LEVEL environment variable
   - Update Architecture.md

---

## Phase 3: None Value Validation (P2 - High)

### Problem

**Current Pattern:**
- No validation that required dependencies are not None
- Runtime errors when None values are used
- Hard to diagnose where None came from

### Solution

**Add Validation in Constructors:**

```python
# PatternOrchestrator
def __init__(self, agent_runtime, db, redis=None):
    if agent_runtime is None:
        raise ValueError("agent_runtime cannot be None - required for pattern execution")
    if db is None:
        raise ValueError("db cannot be None - required for database operations")
    
    # ... rest of initialization

# AgentRuntime
def __init__(self, services: Dict[str, Any]):
    if services is None:
        raise ValueError("services cannot be None - required for agent runtime")
    if "db" not in services:
        raise ValueError("services must contain 'db' key")
    
    # ... rest of initialization

# ScenarioService
def __init__(self, db_pool=None):
    if db_pool is None:
        logger.warning("ScenarioService initialized without db_pool - some features may not work")
        # This is acceptable for some use cases, but log a warning
    
    # ... rest of initialization
```

### Implementation Steps

1. **Add Validation to Critical Constructors** (1 hour)
   - PatternOrchestrator
   - AgentRuntime
   - All agent classes
   - Critical services

2. **Add Validation to Service Constructors** (30 minutes)
   - Services that require db_pool
   - Services with optional dependencies

3. **Test Validation** (30 minutes)
   - Test with None values
   - Verify error messages are clear
   - Ensure proper error propagation

---

## Phase 4: Architecture Validation (P3 - Medium)

### Problem

- No checks to prevent singleton factory functions
- No validation that imports match architecture
- Easy to introduce anti-patterns

### Solution

**Create Architecture Validator:**

```python
# backend/app/core/architecture_validator.py
"""
Architecture Validation Utilities

Purpose: Validate codebase against architecture principles
Created: 2025-01-15
Priority: P3 (Prevents anti-patterns)
"""

import ast
import os
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


def validate_no_singleton_factories(root_dir: str = "backend/app") -> List[Tuple[str, str, int]]:
    """
    Check that no singleton factory functions exist.
    
    Returns:
        List of (file_path, function_name, line_number) violations
    """
    violations = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip test files
        if "test" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read(), filename=file_path)
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for get_*_service or get_*_agent patterns
                        if (node.name.startswith("get_") and 
                            (node.name.endswith("_service") or node.name.endswith("_agent"))):
                            violations.append((file_path, node.name, node.lineno))
                            
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
    
    return violations


def validate_imports_use_classes(root_dir: str = "backend") -> List[Tuple[str, str, int]]:
    """
    Check that imports use classes, not factory functions.
    
    Returns:
        List of (file_path, import_statement, line_number) violations
    """
    violations = []
    
    for root, dirs, files in os.walk(root_dir):
        if "test" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    # Check for imports of get_*_service or get_*_agent
                    if "import" in line and ("get_" in line and ("_service" in line or "_agent" in line)):
                        # Skip if it's a comment
                        if line.strip().startswith("#"):
                            continue
                        violations.append((file_path, line.strip(), i))
                        
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
    
    return violations


def run_architecture_validation() -> dict:
    """
    Run all architecture validation checks.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "singleton_factories": validate_no_singleton_factories(),
        "factory_imports": validate_imports_use_classes(),
        "valid": True
    }
    
    if results["singleton_factories"] or results["factory_imports"]:
        results["valid"] = False
        logger.error("Architecture validation failed!")
        logger.error(f"Found {len(results['singleton_factories'])} singleton factory functions")
        logger.error(f"Found {len(results['factory_imports'])} factory function imports")
    
    return results
```

**Add to CI/CD or Pre-commit Hook:**

```python
# scripts/validate_architecture.py
#!/usr/bin/env python3
"""Validate architecture before commit."""

from app.core.architecture_validator import run_architecture_validation
import sys

if __name__ == "__main__":
    results = run_architecture_validation()
    
    if not results["valid"]:
        print("❌ Architecture validation failed!")
        print("\nSingleton Factory Functions:")
        for file, func, line in results["singleton_factories"]:
            print(f"  {file}:{line} - {func}")
        print("\nFactory Function Imports:")
        for file, import_stmt, line in results["factory_imports"]:
            print(f"  {file}:{line} - {import_stmt}")
        sys.exit(1)
    else:
        print("✅ Architecture validation passed!")
        sys.exit(0)
```

### Implementation Steps

1. **Create Architecture Validator** (1 hour)
   - Implement validation functions
   - Add to core module
   - Create validation script

2. **Add to CI/CD** (30 minutes)
   - Add to pre-commit hook
   - Add to GitHub Actions
   - Document in README

3. **Test Validation** (30 minutes)
   - Test with known violations
   - Verify it catches issues
   - Ensure it doesn't have false positives

---

## Phase 5: Remove Remaining Singleton Factory Functions (P1 - Critical)

### Problem

**Remaining Singleton Factory Functions Found:**
1. `get_macro_hound()` - `backend/app/agents/macro_hound.py:1715`
2. `get_transformation_service()` - `backend/app/services/fred_transformation.py:413`
3. `get_macro_aware_scenario_service()` - `backend/app/services/macro_aware_scenarios.py:1073`
4. `get_audit_service()` - `backend/app/services/audit.py:362`
5. `get_config_manager()` - `backend/app/services/indicator_config.py:461`

**Usages Found:**
- `combined_server.py:710` - Uses `get_transformation_service()`
- Potentially other files using these functions

**Issues:**
- ❌ Contradicts Phase 2 singleton removal
- ❌ Creates architectural inconsistency
- ❌ Makes DI container migration incomplete

### Solution

**Remove All Singleton Factory Functions:**

1. **Remove `get_macro_hound()`**
   - Already registered in DI container as "macro_hound"
   - Use `container.resolve("macro_hound")` or direct instantiation

2. **Remove `get_transformation_service()`**
   - Already registered in DI container as "fred_transformation"
   - Use `container.resolve("fred_transformation")` or direct instantiation

3. **Remove `get_macro_aware_scenario_service()`**
   - Already registered in DI container as "macro_aware_scenarios"
   - Use `container.resolve("macro_aware_scenarios")` or direct instantiation

4. **Remove `get_audit_service()`**
   - Already registered in DI container as "audit"
   - Use `container.resolve("audit")` or direct instantiation

5. **Remove `get_config_manager()`**
   - Already registered in DI container as "indicator_config"
   - Use `container.resolve("indicator_config")` or direct instantiation

**Update Usages:**

```python
# OLD (combined_server.py:710):
from backend.app.services.fred_transformation import get_transformation_service
transformation_service = get_transformation_service()

# NEW (Option 1: Use DI container - preferred):
from app.core.di_container import get_container
from app.core.service_initializer import initialize_services
container = get_container()
if not container._initialized:
    initialize_services(container, db_pool=db_pool)
transformation_service = container.resolve("fred_transformation")

# NEW (Option 2: Direct instantiation - acceptable for standalone usage):
from app.services.fred_transformation import FREDTransformationService
transformation_service = FREDTransformationService()  # No parameters needed
```

**Note:** `FREDTransformationService` doesn't require `db_pool` - it's stateless. Use DI container if available, otherwise direct instantiation is fine.

**For cycles.py:646 (get_config_manager):**
```python
# OLD:
from app.services.indicator_config import get_config_manager
self.config_manager = get_config_manager()

# NEW (Option 1: Use DI container - preferred):
from app.core.di_container import get_container
container = get_container()
if not container._initialized:
    from app.core.service_initializer import initialize_services
    initialize_services(container, db_pool=db_pool)
self.config_manager = container.resolve("indicator_config")

# NEW (Option 2: Direct instantiation - acceptable):
from app.services.indicator_config import IndicatorConfigManager
self.config_manager = IndicatorConfigManager()  # No parameters needed
```

### Implementation Steps

1. **Audit All Usages** (30 minutes)
   - Find all usages of remaining singleton factory functions
   - Document migration path for each
   - Check if services are already registered in DI container

2. **Migrate Usages** (1 hour)
   - Update `combined_server.py:710` (get_transformation_service)
   - Update `backend/app/services/cycles.py:646` (get_config_manager)
   - Check for other usages in documentation/examples
   - Test each migration
   - Ensure database connection patterns are preserved

3. **Remove Function Definitions** (30 minutes)
   - Remove all singleton factory functions
   - Remove global singleton instances
   - Add migration comments explaining DI container usage
   - Update docstrings to show DI container examples

4. **Update Documentation** (30 minutes)
   - Update Architecture.md
   - Update migration guides
   - Update DATABASE.md if needed
   - Document completion

---

## Phase 6: Service Usage Pattern Updates (P2 - High)

### Problem

**Current Pattern (combined_server.py:3486):**
```python
# Fallback to direct ScenarioService or simplified calculation
if db_pool:
    try:
        service = ScenarioService(db_pool=db_pool)
        # ... use service
```

**Issues:**
- ⚠️ No check if ScenarioService is available
- ⚠️ No check if import succeeded
- ⚠️ Could fail if ScenarioService is None

### Solution

**Add Availability Checks:**

```python
# In scenario analysis endpoint
if db_pool and SCENARIO_SERVICE_AVAILABLE:
    try:
        service = ScenarioService(db_pool=db_pool)
        # ... use service
    except Exception as e:
        logger.error(f"Scenario analysis failed: {e}", exc_info=True)
        # Return error response
elif not SCENARIO_SERVICE_AVAILABLE:
    logger.warning("ScenarioService not available - returning error")
    return {
        "error": "Scenario analysis not available",
        "reason": "ScenarioService module not loaded"
    }
else:
    logger.warning("Database pool not available")
    return {
        "error": "Scenario analysis not available",
        "reason": "Database not connected"
    }
```

### Implementation Steps

1. **Update All Service Usage** (1 hour)
   - Add availability checks
   - Update error handling
   - Return proper error responses

2. **Update Pattern Execution** (30 minutes)
   - Check availability before execution
   - Return clear error messages
   - Handle missing services gracefully

3. **Test Service Availability** (30 minutes)
   - Test with missing services
   - Verify error messages
   - Ensure graceful degradation

---

## Implementation Order

### Immediate (P1 - Critical)
1. **Phase 1: Granular Import Error Handling** (2 hours)
   - Refactor import block
   - Add availability flags
   - Update usage checks

2. **Phase 5: Remove Remaining Singleton Factory Functions** (2.5 hours)
   - Audit all usages
   - Migrate usages to DI container or direct instantiation
   - Remove function definitions
   - Update documentation

### Short Term (P2 - High Priority)
3. **Phase 2: Configurable Debug Logging** (1 hour)
   - Make logging configurable
   - Update constructor logging
   - Update documentation

4. **Phase 6: Service Usage Pattern Updates** (2 hours)
   - Add availability checks
   - Update error handling
   - Test service availability

5. **Phase 3: None Value Validation** (2 hours)
   - Add validation to constructors
   - Test validation
   - Update error messages

### Medium Term (P3 - Medium Priority)
6. **Phase 4: Architecture Validation** (2 hours)
   - Create validator
   - Add to CI/CD
   - Test validation

---

## Testing Plan

### Unit Tests
1. Test granular import handling
2. Test availability flags
3. Test None value validation
4. Test architecture validator

### Integration Tests
1. Test with missing modules
2. Test graceful degradation
3. Test error messages
4. Test service availability checks

### Manual Testing
1. Test with LOG_LEVEL=DEBUG
2. Test with LOG_LEVEL=INFO
3. Test with missing imports
4. Test pattern execution with missing services

---

## Success Criteria

1. ✅ Import failures are clearly identified
2. ✅ Critical imports fail fast with clear errors
3. ✅ Optional imports degrade gracefully
4. ✅ Debug logging is configurable
5. ✅ None values are validated early
6. ✅ Architecture violations are caught automatically
7. ✅ Service usage checks availability
8. ✅ Error messages are clear and actionable

---

## Estimated Time

- **Phase 1:** 2 hours (P1 - Critical)
- **Phase 5:** 2.5 hours (P1 - Critical)
- **Phase 2:** 1 hour (P2 - High)
- **Phase 6:** 2 hours (P2 - High)
- **Phase 3:** 2 hours (P2 - High)
- **Phase 4:** 2 hours (P3 - Medium)
- **Testing:** 2 hours
- **Total:** ~13.5 hours (~2 days)

---

## Risk Assessment

### Low Risk
- Phase 2 (Configurable logging)
- Phase 4 (Architecture validation)

### Medium Risk
- Phase 3 (None value validation)
- Phase 5 (Service usage updates)

### High Risk
- Phase 1 (Import refactoring) - Could break if not careful

### Mitigation
- Test thoroughly after each phase
- Keep old code commented for rollback
- Deploy incrementally
- Monitor error logs after deployment

---

**Status:** 📋 Plan Ready for Implementation

