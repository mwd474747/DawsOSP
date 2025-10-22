# DawsOS - AI Assistant Context

**Application Name**: DawsOS
**Architecture**: Trinity 3.0
**Version**: 1.0.0
**Status**: Production-ready
**Last Updated**: October 21, 2025

This file provides context for AI assistants (Claude) working on DawsOS.

---

## 🏷️ NAMING CONVENTION (CRITICAL)

> **DawsOS** is the APPLICATION (product name)
> **Trinity 3.0** is the ARCHITECTURE VERSION (execution framework)
> **DawsOSB** is the REPOSITORY (GitHub repo name)

**When to use what**:
- **User-facing** (UI, docs, marketing): "Trinity" or "DawsOS"
- **Technical docs**: "Trinity 3.0 architecture" or "DawsOS (Trinity 3.0 Architecture)"
- **Code comments**: "Trinity 3.0 execution flow"
- **NEVER**: Mix "Trinity 3.0" and "DawsOS" as if they're different systems

**Key Understanding**:
> Trinity 3.0 is NOT a separate system - it's the execution framework FOR DawsOS.
> Like "React 18" is the framework version for a React app, "Trinity 3.0" is the framework version for DawsOS.

See [NAMING_CONSISTENCY_AUDIT.md](NAMING_CONSISTENCY_AUDIT.md) for complete details.

---

## CRITICAL: Read This First

**ALWAYS start every session by reading**:
1. **[MASTER_TASK_LIST.md](MASTER_TASK_LIST.md)** - SINGLE SOURCE OF TRUTH for all tasks, gaps, fixes
2. This file (CLAUDE.md) - Quick reference

**RULES**:
- NEVER create separate task lists
- ALWAYS update MASTER_TASK_LIST.md when discovering gaps
- ALWAYS verify claims against actual code
- NEVER reference non-existent directories (trinity3/, dawsos/)

---

## Current State (Verified October 21, 2025)

### Application Structure

**Location**: ROOT directory (`./`)  
**Status**: 100% complete, production-ready  
**Main File**: `main.py` (1,726 lines, operational)

```
./
├── main.py                  ✅ Streamlit UI
├── agents/                  ✅ 7 agent files
├── core/                    ✅ 13 core modules
├── patterns/                ✅ 16 JSON patterns
├── storage/knowledge/       ✅ 27 datasets
├── services/                ✅ 8 service files
├── intelligence/            ✅ 3 intelligence files
├── ui/                      ✅ 7 UI components
├── config/api_config.py     ✅ API configuration
└── .env.example             ✅ API template
```

### API Configuration

**Status**: 0/10 APIs configured (FREE MODE)  
**Impact**: System works but no AI analysis  
**Fix**: User must create .env file and add keys

### Known Architecture Issues

See [MASTER_TASK_LIST.md](MASTER_TASK_LIST.md) for full details:

1. **P1: Pattern engine not connected to UI** - UI bypasses execution stack
2. **P1: Only 2/7 agents registered** - financial_analyst, claude only
3. **P1: Knowledge loader path wrong** - Points to `./dawsos/` (doesn't exist)
4. **P2: Query processing bypasses UniversalExecutor** - No pattern routing
5. **P2: OpenBB 4.5.0 bug** - yfinance workaround in place (working)

---

## Execution Flows

### Current (UI Direct)
```
UI Click → render_method() → Direct JSON load → Display
```
**Problem**: Bypasses architecture

### Designed (Pattern-Based)
```
UI Click → UniversalExecutor → PatternEngine → AgentRuntime → Agent → KnowledgeGraph
```
**Status**: Architecture exists but not connected

---

## Component Inventory

**Agents**: 7 files, 2 registered  
**Core Modules**: 13 files  
**Patterns**: 16 JSON files (economy/6, smart/7, workflows/3)  
**Knowledge Datasets**: 27 JSON files  
**Services**: 8 files (OpenBBService uses yfinance)  
**Intelligence**: 3 files (EnhancedChatProcessor, entity extraction)  
**UI**: 7 component files

---

## Documentation (8 Files)

1. **MASTER_TASK_LIST.md** - All gaps/fixes/TODOs (READ THIS FIRST)
2. **README.md** - Project overview
3. **ARCHITECTURE.md** - System design
4. **CONFIGURATION.md** - API setup
5. **DEVELOPMENT.md** - Developer guide
6. **DEPLOYMENT.md** - Production deployment
7. **TROUBLESHOOTING.md** - Common issues
8. **CLAUDE.md** - This file

**Reference**:
- CAPABILITY_ROUTING_GUIDE.md - 103 capabilities
- PATTERN_AUTHORING_GUIDE.md - Pattern creation
- EXTENSION_GUIDE.md - System extensions

---

## Verification Commands

```bash
# Verify structure
ls -1 agents/*.py core/*.py patterns/*/*.json storage/knowledge/*.json | wc -l

# Verify API status
venv/bin/python -c "from config.api_config import APIConfig; print(APIConfig.get_status())"

# Verify market data
venv/bin/python -c "from services.openbb_service import OpenBBService; print(OpenBBService().get_equity_quote('SPY'))"

# Verify agent registration
grep "register_agent" main.py | wc -l  # Should be 2
```

---

## Development Rules

**DO**:
- Read MASTER_TASK_LIST.md at session start
- Update MASTER_TASK_LIST.md with discoveries
- Verify all claims against code
- Use UniversalExecutor → PatternEngine flow
- Use KnowledgeLoader for data (not direct file loads)

**DON'T**:
- Reference trinity3/ directory (doesn't exist)
- Reference dawsos/ directory (doesn't exist - except in archive)
- Create separate TODO lists
- Make claims without code verification
- Bypass architecture (use execution stack)

---

## Quick Reference

**Launch**: `./start.sh`  
**Port**: 8501  
**Python**: 3.11 (required)  
**Main File**: `main.py`  
**Task List**: MASTER_TASK_LIST.md  
**API Setup**: CONFIGURATION.md  
**Architecture**: ARCHITECTURE.md

---

**Last Verified**: October 21, 2025 20:00 UTC
