# DawsOS Documentation

**Version:** 6.0.1  
**Last Updated:** November 4, 2025  
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

- **Phase 3 Consolidation** - `.archive/phase3/`
- **UI Integration** - `.archive/ui-integration/`
- **Code Reviews** - `.archive/code-reviews/`
- **Corporate Actions** - `.archive/corporate-actions/`
- **Database Analysis** - `.archive/database/`
- **Refactoring** - `.archive/refactoring/`
- **Replit Coordination** - `.archive/replit/`
- **Testing** - `.archive/testing/`
- **Field Naming** - `.archive/field-naming/`
- **Macro Cycles** - `.archive/macro-cycles/`
- **Completed Work** - `.archive/completed/`

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

### Field Naming Standardization
- **Phase 1 Complete:** Field naming standardized across agent layer
- **Standard:** Agent capabilities return `quantity` (not `qty` or `quantity_open`)
- **Database:** Uses `quantity_open`, `quantity_original` (columns)
- **See:** [ARCHITECTURE.md](ARCHITECTURE.md#field-naming-standards), [DATABASE.md](DATABASE.md#field-naming-standards)

### Corporate Actions Improvements
- **Enhanced:** Diagnostic logging and robust quantity handling
- **Fixed:** Symbol extraction from portfolio holdings
- **See:** [docs/guides/CORPORATE_ACTIONS_GUIDE.md](docs/guides/CORPORATE_ACTIONS_GUIDE.md)

**Last Updated:** January 14, 2025

