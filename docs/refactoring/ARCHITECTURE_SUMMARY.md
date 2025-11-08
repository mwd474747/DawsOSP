# DawsOS Architecture Summary

**Last Updated:** January 15, 2025

This document provides a high-level overview of the DawsOS architecture after the V3 refactoring effort.

---

## Architecture Overview

### Frontend Architecture

**Single-Page Application (SPA)**
- **Entry Point:** `full_ui.html` - React-based SPA
- **Module System:** Namespace-based module loading with validation
- **Logger:** Centralized logging utility (`frontend/logger.js`)
- **Module Loading:** Dependency validation with retry logic

**Key Frontend Modules:**
- `api-client.js` - API client with token management
- `pattern-system.js` - Pattern orchestration and rendering
- `panels.js` - Panel components (metrics, charts, tables)
- `context.js` - User context and portfolio management
- `module-dependencies.js` - Module dependency validation
- `namespace-validator.js` - Namespace validation

**Architecture Principles:**
- Namespace-based organization (`DawsOS.*`)
- Dependency validation at load time
- Retry logic for race conditions
- Environment-based logging

---

### Backend Architecture

**Dependency Injection Container**
- **Location:** `backend/app/core/di_container.py`
- **Purpose:** Manage service initialization and dependencies
- **Status:** ~95% integrated (all singleton calls migrated)

**Service Layer**
- Services registered in DI container
- No singleton pattern (deprecated functions remain for backward compatibility)
- Services initialized in dependency order

**Key Services:**
- `PricingService` - Pricing pack queries
- `MacroService` - Macro regime detection
- `ScenarioService` - Scenario stress testing
- `RiskService` - Risk metrics (VaR, DaR)
- `AuthService` - Authentication and authorization
- `AlertService` - Alert evaluation (deprecated, migrating to MacroHound)
- `RatingsService` - Quality ratings (deprecated, migrating to FinancialAnalyst)
- `OptimizerService` - Portfolio optimization (deprecated, migrating to FinancialAnalyst)

**Agent Layer**
- **Base Agent:** `BaseAgent` - Common functionality
- **Active Agents:**
  - `MacroHound` - Macro analysis and alerts
  - `FinancialAnalyst` - Financial analysis and ratings
  - `DataHarvester` - Data collection and reports
  - `ClaudeAgent` - AI assistant

**Pattern Orchestration**
- **Location:** `backend/app/core/pattern_orchestrator.py`
- **Purpose:** Execute patterns and coordinate agents
- **Pattern Registry:** JSON pattern files define capabilities

---

## Exception Handling

**Exception Hierarchy**
- **Location:** `backend/app/core/exceptions.py`
- **Base:** `DawsOSException`
- **Categories:**
  - Database exceptions (`DatabaseError`, `QueryError`)
  - External API exceptions (`ExternalAPIError`, `APIError`)
  - Business logic exceptions (`BusinessLogicError`, `ValidationError`)
  - Programming errors (not caught - should be fixed)

**Principles:**
- Catch specific exceptions first
- Broad `Exception` only as final fallback
- Root causes fixed, not just symptoms

---

## Security

**SQL Injection Protection**
- **Location:** `backend/app/services/alert_validation.py`
- **Method:** Whitelist-based validation
- **Coverage:** Metric names, symbols, UUIDs

**Authentication**
- JWT-based authentication
- Role-based access control (RBAC)
- Row-Level Security (RLS) for multi-tenant isolation

---

## Constants Management

**Constants Modules**
- **Location:** `backend/app/core/constants/`
- **Organization:** Domain-driven (financial, risk, macro, etc.)
- **Status:** ~64% of magic numbers extracted

**Modules:**
- `financial.py` - Trading calendar, performance metrics
- `risk.py` - VaR/CVaR, statistical thresholds
- `macro.py` - Macro regime detection
- `scenarios.py` - Monte Carlo simulation
- `validation.py` - Data quality thresholds
- `integration.py` - External API configuration

---

## Code Quality Improvements

**Removed Technical Debt:**
- ~2,288 lines of code removed
- ~2,115 lines of legacy code removed
- ~173 lines of duplicate code extracted
- 21 singleton calls migrated to DI container

**Remaining Work:**
- ~115 console.log statements (frontend)
- ~36% magic numbers remaining
- 50 TODOs (mostly P2-P4)

---

## Testing Strategy

**Test Coverage:**
- Unit tests for services
- Integration tests for patterns
- End-to-end tests for critical flows

**Test Status:**
- ⏳ Comprehensive tests pending (P4)

---

## Migration Status

**Completed Migrations:**
- ✅ Singleton pattern → DI container (~95%)
- ✅ Exception handling → Exception hierarchy (~85%)
- ✅ Duplicate code → BaseAgent helpers (100%)
- ✅ Legacy code → Removed (100%)

**Services as Implementation Details:**
- ✅ AlertService → Used by MacroHound agent (implementation detail)
- ✅ RatingsService → Used by FinancialAnalyst agent (implementation detail)
- ✅ OptimizerService → Used by FinancialAnalyst agent (implementation detail)
- ✅ ReportService → Used by DataHarvester agent (implementation detail)

**Deprecated (but still used):**
- Singleton factory functions (marked DEPRECATED, will be removed after migration period)

---

## Key Principles

1. **Dependency Injection:** All services use DI container
2. **Exception Handling:** Specific exceptions caught first
3. **Code Reuse:** Common patterns extracted to BaseAgent
4. **Security:** Input validation, SQL injection protection
5. **Maintainability:** Constants extracted, documentation updated

---

**For detailed refactoring status, see:** `V3_PLAN_FINAL_STATUS.md`

