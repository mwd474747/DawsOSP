# Service Architecture

**Date:** January 15, 2025  
**Status:** ✅ ARCHITECTURE CLARIFIED

---

## Executive Summary

Services (`AlertService`, `RatingsService`, `OptimizerService`, `ReportService`) are **essential implementation details** of agents, not deprecated code. They are used internally by agents to implement business logic.

**Key Point:** Patterns use **agent capabilities**, not services directly. Services are internal to agents.

---

## Architecture Pattern

```
Pattern → Agent Capability → Service Method → Database/API
```

**Example:**
```
buffett_checklist.json
  → financial_analyst.dividend_safety
    → FinancialAnalyst.financial_analyst_dividend_safety()
      → RatingsService.calculate_dividend_safety()
        → Database (rating_rubrics table)
```

---

## Service Roles

### AlertService
- **Used by:** MacroHound agent
- **Purpose:** Alert evaluation and condition checking
- **Status:** Active implementation detail

### RatingsService
- **Used by:** FinancialAnalyst agent
- **Purpose:** Quality ratings calculation (dividend safety, quality scores)
- **Status:** Active implementation detail

### OptimizerService
- **Used by:** FinancialAnalyst agent
- **Purpose:** Portfolio optimization (mean-variance, risk parity)
- **Status:** Active implementation detail

### ReportService
- **Used by:** DataHarvester agent
- **Purpose:** PDF generation and export
- **Status:** Active implementation detail

---

## Documentation Standard

All services should include an "Architecture Note" in their docstrings:

```python
"""
**Architecture Note:** This service is an implementation detail of the [AgentName] agent.
Patterns should use `[agent_name]` agent capabilities, not this service directly.
"""
```

**See:** `SERVICE_DOCUMENTATION_STANDARD.md` for full standard

---

## History

### Phase 3 Consolidation (November 2025)
- Goal: Consolidate 9 agents → 4 agents
- Result: Services kept as implementation details
- Migration: Pattern level complete (patterns use agent capabilities)

### Service Deprecation Cleanup (January 2025)
- Issue: Services incorrectly marked as deprecated
- Fix: Removed misleading deprecation warnings
- Result: Services correctly documented as implementation details

---

**Status:** ✅ ARCHITECTURE CLARIFIED

