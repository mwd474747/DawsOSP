# DawsOS Documentation

**Version:** 6.0.1  
**Last Updated:** January 14, 2025  
**Status:** ✅ Production Ready

---

## 📚 Core Documentation

### Essential Guides
- **[README.md](README.md)** - Quick start guide and project overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design patterns
- **[DATABASE.md](DATABASE.md)** - Database schema, operations, and migrations
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development setup and guidelines
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### Product Documentation
- **[ROADMAP.md](ROADMAP.md)** - Product roadmap and future plans
- **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Product specification
- **[API_CONTRACT.md](API_CONTRACT.md)** - API endpoint documentation

### Technical Documentation
- **[FEATURE_FLAGS_EXPLANATION.md](FEATURE_FLAGS_EXPLANATION.md)** - Feature flags guide
- **[MIGRATION_HISTORY.md](MIGRATION_HISTORY.md)** - Database migration history
- **[PRICING_PACK_ARCHITECTURE.md](PRICING_PACK_ARCHITECTURE.md)** - Pricing pack architecture

### Agent Coordination
- **[AGENT_CONVERSATION_MEMORY.md](AGENT_CONVERSATION_MEMORY.md)** - Shared memory for agent coordination

### Refactoring Status
- **[REFACTOR_STATUS.md](REFACTOR_STATUS.md)** - Current refactoring status (Phases 0-3 Complete, Phase 4 Pending)

---

## 📁 Reference Documentation

### Patterns
- **[docs/reference/PATTERNS_REFERENCE.md](docs/reference/PATTERNS_REFERENCE.md)** - Pattern system reference

### Agent Coordination
- **[docs/reference/AGENT_COORDINATION_PLAN.md](docs/reference/AGENT_COORDINATION_PLAN.md)** - Agent coordination strategy

### Deployment
- **[docs/reference/replit.md](docs/reference/replit.md)** - Replit deployment guide
- **[docs/reference/REPLIT_DEPLOYMENT_GUARDRAILS.md](docs/reference/REPLIT_DEPLOYMENT_GUARDRAILS.md)** - Deployment guardrails

---

## 📖 User Guides

### Corporate Actions
- **[docs/guides/CORPORATE_ACTIONS_GUIDE.md](docs/guides/CORPORATE_ACTIONS_GUIDE.md)** - Corporate actions guide

### UI Error Handling
- **[docs/guides/UI_ERROR_HANDLING_COMPLETE.md](docs/guides/UI_ERROR_HANDLING_COMPLETE.md)** - UI error handling guide

---

## 📦 Archived Documentation

Historical documentation has been archived to `.archive/` directory:

- **Phase Completion** - `.archive/phase-completion/` - Phase completion reports and validation
- **Planning Documents** - `.archive/planning/` - Phase planning documents
- **Critical Fixes** - `.archive/critical-fixes/` - Critical fixes documentation
- **Git/Replit Fixes** - `.archive/git-replit-fixes/` - Git and Replit fix guides
- **Status Consolidation** - `.archive/status-consolidation/` - Consolidated status documents
- **Phase 1 Validation** - `.archive/phase1-validation/` - Phase 1 validation reports
- **Phase 3 Consolidation** - `.archive/phase3/`
- **UI Integration** - `.archive/ui-integration/`
- **Code Reviews** - `.archive/code-reviews/`
- **Corporate Actions** - `.archive/corporate-actions/`
- **Database Analysis** - `.archive/database/`
- **Refactoring** - `.archive/refactoring/`
- **Replit Coordination** - `.archive/replit/`
- **Testing** - `.archive/testing-docs/` - Testing prompts and validation reports
- **Analysis Documents** - `.archive/analysis-docs/` - Code reviews, pattern analysis, field naming analysis
- **Completed Work** - `.archive/completed-work/` - Status summaries and completion reports
- **Field Naming** - `.archive/field-naming/`
- **Macro Cycles** - `.archive/macro-cycles/`

---

## 🔍 Finding Documentation

### By Topic

**Architecture:**
- System Overview: [ARCHITECTURE.md](ARCHITECTURE.md)
- Database Schema: [DATABASE.md](DATABASE.md)
- Patterns: [docs/reference/PATTERNS_REFERENCE.md](docs/reference/PATTERNS_REFERENCE.md)

**Development:**
- Setup: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- Deployment: [DEPLOYMENT.md](DEPLOYMENT.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**API:**
- API Contract: [API_CONTRACT.md](API_CONTRACT.md)
- Endpoints: See [ARCHITECTURE.md](ARCHITECTURE.md#api-endpoints)

**Features:**
- Feature Flags: [FEATURE_FLAGS_EXPLANATION.md](FEATURE_FLAGS_EXPLANATION.md)
- Pricing Packs: [PRICING_PACK_ARCHITECTURE.md](PRICING_PACK_ARCHITECTURE.md)
- Corporate Actions: [docs/guides/CORPORATE_ACTIONS_GUIDE.md](docs/guides/CORPORATE_ACTIONS_GUIDE.md)

---

## 📝 Recent Updates (January 14, 2025)

### Phase 0-3 Complete: Refactoring Complete ✅
- **Phase 0:** Zombie code removal (1,197 lines removed) ✅ COMPLETE
- **Phase 1:** Emergency fixes (provenance warnings, pattern fixes) ✅ COMPLETE
- **Phase 2:** Foundation (capability contracts, validation) ✅ COMPLETE
- **Phase 3:** Real features (factor analysis, DaR hardening) ✅ COMPLETE
- **Phase 4:** Production readiness (pending) ⏳ PENDING

### Phase 1 Complete: Provenance Warnings & Pattern Output Extraction ✅
- **Provenance Warnings:** Stub data now explicitly marked with `_provenance` field
  - UI displays warning banner when stub data detected
  - Prevents user trust issues from silent fake data
- **Pattern Output Extraction:** Fixed orchestrator to handle 3 output formats
  - All 6 updated patterns return correct data
  - Scenario analysis working correctly (12 scenarios)
- **Migration 009:** Applied successfully - scenario analysis tables created
- **See:** [ARCHITECTURE.md](ARCHITECTURE.md) for details, [CHANGELOG.md](CHANGELOG.md) for complete changes

### Field Naming Standardization ✅
- **Phase 1 Complete:** Field naming standardized across agent layer
- **Standard:** Agent capabilities return `quantity` (not `qty` or `quantity_open`)
- **Database:** Uses `quantity_open`, `quantity_original` (columns)
- **See:** [ARCHITECTURE.md](ARCHITECTURE.md#field-naming-standards), [DATABASE.md](DATABASE.md#field-naming-standards)

### Corporate Actions Improvements ✅
- **Enhanced:** Diagnostic logging and robust quantity handling
- **Fixed:** Symbol extraction from portfolio holdings
- **See:** [docs/guides/CORPORATE_ACTIONS_GUIDE.md](docs/guides/CORPORATE_ACTIONS_GUIDE.md)

**Last Updated:** January 14, 2025

