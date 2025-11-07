# Knowledge Sources - Technical Debt Removal

**Date:** January 15, 2025  
**Purpose:** Comprehensive list of knowledge sources for technical debt removal work

---

## Core Architecture Documents

### 1. ARCHITECTURE.md
**Location:** `/ARCHITECTURE.md`  
**Purpose:** System architecture overview  
**Key Sections:**
- Pattern Orchestration Layer
- Agent Runtime Layer
- Backend (FastAPI)
- Frontend (React SPA)
- Database Layer

**Relevance:** Understanding system architecture before making changes

---

### 2. PATTERNS_REFERENCE.md
**Location:** `/docs/reference/PATTERNS_REFERENCE.md`  
**Purpose:** Complete reference for pattern system  
**Key Sections:**
- Pattern System Overview
- Pattern Inventory (13 patterns)
- Pattern Execution
- Template Substitution
- Pattern Development

**Relevance:** Understanding pattern system before standardizing formats

---

## Recent Refactoring Work

### 3. UI_REFACTORING_COMPLETE.md
**Location:** `/UI_REFACTORING_COMPLETE.md`  
**Purpose:** UI refactoring completion report  
**Key Sections:**
- MarketDataPage Refactoring
- AIInsightsPage Optimization
- Legacy Code Cleanup
- UI Page Status Review

**Relevance:** Understanding recent UI changes to avoid breaking them

---

### 4. PHASE_1_STUB_REMOVAL_COMPLETE.md
**Location:** `/PHASE_1_STUB_REMOVAL_COMPLETE.md`  
**Purpose:** Phase 1 stub removal completion  
**Key Sections:**
- Mock Data Removal
- Fallback Function Removal
- Hardcoded Values Removal
- Production Guards Verified

**Relevance:** Understanding what stub removal work was done

---

### 5. PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md
**Location:** `/PHASE_2_SERVICE_STUB_REVIEW_COMPLETE.md`  
**Purpose:** Phase 2 service stub review completion  
**Key Sections:**
- Production Guard Implementation
- Stub Implementations Documented
- Deprecation Status

**Relevance:** Understanding service stub status before removing singletons

---

## Namespace Architecture

### 6. NAMESPACE_ARCHITECTURE.md (This Document Set)
**Location:** `/docs/refactoring/NAMESPACE_ARCHITECTURE.md`  
**Purpose:** Namespace architecture documentation  
**Key Sections:**
- Namespace Hierarchy
- Module Exports
- Backward Compatibility
- Migration Status

**Relevance:** Understanding namespace structure to avoid breaking changes

---

### 7. REFACTORING_STABILITY_REPORT.md
**Location:** `/REFACTORING_STABILITY_REPORT.md`  
**Purpose:** Post-refactoring stability assessment  
**Key Sections:**
- Phase 1 Review
- Phase 2 Review
- Critical Bugs Found & Fixed

**Relevance:** Understanding what bugs were fixed in recent refactoring

---

## Pattern System Deep Dive

### 8. PATTERN_SYSTEM_DEEP_DIVE.md (This Document Set)
**Location:** `/docs/refactoring/PATTERN_SYSTEM_DEEP_DIVE.md`  
**Purpose:** Comprehensive pattern system understanding  
**Key Sections:**
- Pattern System Philosophy
- Core Components
- Template Substitution
- Pattern Execution Flow
- Pattern System Power

**Relevance:** Understanding pattern system before standardizing formats

---

## Code Review Documents

### 9. Code Review Inventory
**Location:** (User-provided code review)  
**Purpose:** Comprehensive code review findings  
**Key Sections:**
- Critical Anti-Patterns
- Code Duplication
- Legacy Artifacts
- Missed TODOs

**Relevance:** Source of technical debt inventory

---

## Implementation Guides

### 10. IMPLEMENTATION_GUIDE.md (This Document Set)
**Location:** `/docs/refactoring/IMPLEMENTATION_GUIDE.md`  
**Purpose:** Step-by-step implementation guide  
**Key Sections:**
- Phase-by-phase implementation steps
- Code patterns to follow
- Testing strategy
- Success criteria

**Relevance:** Step-by-step guide for implementation

---

## Current State Assessment

### 11. CURRENT_STATE_ASSESSMENT.md (This Document Set)
**Location:** `/docs/refactoring/CURRENT_STATE_ASSESSMENT.md`  
**Purpose:** Current codebase state assessment  
**Key Sections:**
- Codebase Statistics
- Technical Debt Breakdown
- Dependencies & Relationships
- Testing Status
- Risk Assessment

**Relevance:** Understanding current state before making changes

---

## Master Plan

### 12. TECHNICAL_DEBT_REMOVAL_PLAN.md (This Document Set)
**Location:** `/docs/refactoring/TECHNICAL_DEBT_REMOVAL_PLAN.md`  
**Purpose:** Master plan for technical debt removal  
**Key Sections:**
- Executive Summary
- Context: Recent Refactoring Work
- Pattern System Architecture
- Technical Debt Inventory
- Implementation Phases

**Relevance:** Overall plan and context

---

## Key Code Files

### Backend Core
- `backend/app/core/pattern_orchestrator.py` - Pattern execution
- `backend/app/core/agent_runtime.py` - Agent routing
- `backend/app/core/types.py` - RequestCtx definition
- `backend/app/agents/base_agent.py` - Base agent with helpers

### Services
- `backend/app/services/optimizer.py` - Optimizer service
- `backend/app/services/ratings.py` - Ratings service
- `backend/app/services/pricing.py` - Pricing service
- `backend/app/services/alerts.py` - Alert service (deprecated)
- Others as needed

### Frontend
- `frontend/pattern-system.js` - Pattern system
- `frontend/pages.js` - Page components
- `frontend/utils.js` - Utilities
- `frontend/api-client.js` - API client

### Patterns
- `backend/patterns/*.json` - Pattern definitions

---

## Reference Patterns

### Good Patterns to Follow
1. **FinancialAnalyst** - Uses dependency injection correctly
2. **BaseAgent helpers** - Portfolio ID resolution, UUID conversion
3. **Pattern orchestrator** - Template resolution, output extraction

### Anti-Patterns to Avoid
1. **Global singletons** - Use dependency injection instead
2. **Broad exception handling** - Use specific exceptions
3. **Magic numbers** - Use constants
4. **Console.log in production** - Use proper logging

---

## Testing Resources

### Test Files
- `backend/tests/` - Unit and integration tests
- `backend/test_*.py` - Test files in root

### Test Patterns
- Pattern execution tests
- Service interaction tests
- Error handling tests

---

## Documentation Standards

### Code Documentation
- Docstrings for all functions
- Type hints for all parameters
- Clear error messages
- Examples in docstrings

### Pattern Documentation
- Clear pattern descriptions
- Input/output documentation
- Example usage
- Version tracking

---

## Key Principles

### 1. No Backwards Compatibility
- Remove deprecated code completely
- No deprecation aliases for removed code
- Clean break from legacy patterns

### 2. Pattern-First Architecture
- Leverage pattern system's power
- Standardize on pattern format
- Use patterns for business logic

### 3. Respect Recent Refactoring
- Build on Phase 1/2/2.5 work
- Don't break namespace structure
- Maintain UI refactoring benefits

### 4. Systematic Approach
- Phase-by-phase execution
- Test after each phase
- Document changes

---

## Quick Reference

### Exception Hierarchy
```
DawsOSError (base)
├── DatabaseError
├── ValidationError
├── ServiceError
├── ConfigurationError
├── ExternalAPIError
├── CapabilityError
└── PatternError
```

### Namespace Structure
```
DawsOS
├── Core.* (Infrastructure)
├── Patterns.* (Prime namespace)
├── UI.* (Presentation)
└── Utils.* (Cross-cutting)
```

### Pattern Output Format (Target)
```json
{
  "outputs": {
    "panels": [...],
    "data": {...}
  }
}
```

---

**Status:** Knowledge Sources Documented  
**Last Updated:** January 15, 2025

