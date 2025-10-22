# Agent Wiring Plan - Trinity 3.0 Migration

**Issue**: Trinity3 contains mix of DawsOS agents and Trinity 3.0-specific agents
**Risk**: May have mocked/incomplete agents instead of production DawsOS agents
**Priority**: 🔴 CRITICAL - Must fix before Week 5

---

## Current State

### Agents in trinity3/agents/

| Agent | Source | Status | Action |
|-------|--------|--------|--------|
| base_agent.py | DawsOS | ✅ Correct | Keep |
| claude.py | DawsOS | ✅ Correct | Keep |
| financial_analyst.py | DawsOS | ⚠️ Broken | Fix analyzers |
| **equity_agent.py** | **Trinity 3.0** | ⚠️ **May be mock** | **REVIEW** |
| **macro_agent.py** | **Trinity 3.0** | ⚠️ **May be mock** | **REVIEW** |
| **market_agent.py** | **Trinity 3.0** | ⚠️ **May be mock** | **REVIEW** |
| **portfolio_manager.py** | **Week 3 Stub** | ⚠️ **STUB** | **REVIEW** |
| **risk_analyst.py** | **Week 3 Stub** | ⚠️ **STUB** | **REVIEW** |

### DawsOS Agents NOT Migrated

From `dawsos/agents/`:
- backtest_agent.py
- code_monkey.py
- data_digester.py
- data_harvester.py
- forecast_dreamer.py
- governance_agent.py
- graph_mind.py
- pattern_spotter.py
- refactor_elf.py
- relationship_hunter.py
- structure_bot.py
- ui_generator.py
- workflow_player.py
- workflow_recorder.py

**Total**: 14 DawsOS agents not migrated

---

## Critical Questions

### 1. Are Trinity 3.0 Agents Production-Quality or Mocks?

**equity_agent.py** (711 lines):
- Imports from `services.openbb_service` ✅
- Imports from `services.prediction_service` ✅
- Has 10 capabilities defined
- Full implementation (not stub)
- **Question**: Is this production code or demo/mock?

**macro_agent.py** (650 lines):
- Full implementation
- **Question**: Is this production code or demo/mock?

**market_agent.py** (792 lines):
- Full implementation
- **Question**: Is this production code or demo/mock?

### 2. Are Week 3 Stub Agents Needed?

**portfolio_manager.py** (207 lines):
- Created Week 3 as stub
- 11 capabilities with stub implementations
- **Question**: Does DawsOS have a better version? OR is this new for Trinity 3.0?

**risk_analyst.py** (218 lines):
- Created Week 3 as stub
- 11 capabilities with stub implementations
- **Question**: Does DawsOS have a better version? OR is this new for Trinity 3.0?

### 3. Which DawsOS Agents Are Actually Needed?

From the 14 unmigrated DawsOS agents, which are critical for production?

**Likely Critical**:
- forecast_dreamer.py (forecasting capabilities)
- pattern_spotter.py (pattern detection)
- graph_mind.py (graph operations)

**Likely Optional** (dev tools):
- code_monkey.py
- refactor_elf.py
- structure_bot.py
- ui_generator.py

**Unknown**:
- backtest_agent.py
- data_digester.py
- data_harvester.py
- governance_agent.py
- relationship_hunter.py
- workflow_player.py
- workflow_recorder.py

---

## Investigation Plan

### Step 1: Verify Trinity 3.0 Agent Quality

**Check equity_agent.py**:
```python
# Read full file
cat trinity3/agents/equity_agent.py

# Key questions:
# - Does it use real data or mocks?
# - Are methods fully implemented or stubs?
# - Does it import from services (good) or has hardcoded data (bad)?
```

**Check macro_agent.py and market_agent.py** similarly

**Decision Criteria**:
- ✅ If fully implemented with real data → **KEEP**
- ⚠️ If has some mock data → **ENHANCE**
- ❌ If mostly stubs → **REPLACE with DawsOS agent if exists**

### Step 2: Search for Better DawsOS Equivalents

**Check if DawsOS has alternatives**:
```bash
# Search DawsOS for similar functionality
grep -r "EquityAgent" dawsos/
grep -r "MacroAgent" dawsos/
grep -r "MarketAgent" dawsos/
grep -r "PortfolioManager" dawsos/
grep -r "RiskAnalyst" dawsos/
```

**If found in DawsOS**:
- Compare implementations
- Choose better version
- Migrate if DawsOS is superior

### Step 3: Review AGENT_CAPABILITIES Registry

**Check what the system expects**:
```python
# From core/agent_capabilities.py
AGENT_CAPABILITIES = {
    'claude': [...],
    'financial_analyst': [...],
    'equity_agent': [...],  # Expected?
    'macro_agent': [...],   # Expected?
    'market_agent': [...],  # Expected?
    'portfolio_manager': [...],  # Expected?
    'risk_analyst': [...],  # Expected?
    # ... etc
}
```

**Questions**:
- Which agents are in AGENT_CAPABILITIES?
- Are Trinity 3.0 agents aligned with this registry?
- Are we missing any agents from the registry?

### Step 4: Fix agents.analyzers Module

**Critical for financial_analyst.py**:
```bash
# Check if analyzers exist in DawsOS
ls -la dawsos/agents/analyzers/

# Expected files:
# - dcf_analyzer.py
# - moat_analyzer.py
# - financial_data_fetcher.py
# - financial_confidence_calculator.py

# If exists:
cp -r dawsos/agents/analyzers trinity3/agents/

# If doesn't exist:
# - Check where these modules are
# - May be in different location
# - May need refactoring
```

---

## Decision Matrix

### Scenario A: Trinity 3.0 Agents Are Production Quality

**If** equity/macro/market agents are fully implemented:
- ✅ **KEEP** Trinity 3.0 agents
- ✅ **ENHANCE** Week 3 stubs (portfolio_manager, risk_analyst)
- ✅ **MIGRATE** critical DawsOS agents (forecast_dreamer, pattern_spotter, graph_mind)
- ✅ **FIX** financial_analyst (add analyzers)

**Result**: 8 agents (3 DawsOS + 5 Trinity) + 3 more migrated = 11 total

### Scenario B: Trinity 3.0 Agents Are Mocks/Demos

**If** equity/macro/market agents have mock data:
- ⚠️ **ENHANCE** to use real services
- ⚠️ **KEEP** structure but replace mock logic
- ✅ **ENHANCE** Week 3 stubs
- ✅ **MIGRATE** critical DawsOS agents
- ✅ **FIX** financial_analyst

**Result**: Same 11 agents, but more work needed

### Scenario C: Replace Trinity 3.0 with DawsOS

**If** DawsOS has better equivalents:
- ❌ **REMOVE** Trinity 3.0 agents
- ✅ **MIGRATE** DawsOS equivalents
- ✅ **MIGRATE** critical DawsOS agents
- ✅ **FIX** financial_analyst

**Result**: All agents from DawsOS (may need more migration work)

---

## Recommended Actions (Week 5 Day 1)

### Morning (2 hours)

**1. Read Trinity 3.0 Agent Files**
```bash
# Read each Trinity 3.0 agent completely
cat trinity3/agents/equity_agent.py
cat trinity3/agents/macro_agent.py
cat trinity3/agents/market_agent.py
cat trinity3/agents/portfolio_manager.py
cat trinity3/agents/risk_analyst.py

# Document:
# - Are they production quality?
# - Do they use real data or mocks?
# - What capabilities do they have?
```

**2. Check DawsOS for Equivalents**
```bash
# Search DawsOS agents
ls -la dawsos/agents/
grep -r "class.*Agent" dawsos/agents/*.py

# Document which exist
```

**3. Read AGENT_CAPABILITIES Registry**
```python
# Check what system expects
cat trinity3/core/agent_capabilities.py

# List all agents
# Compare with what we have
```

### Afternoon (3 hours)

**4. Fix agents.analyzers**
```bash
# Find analyzers in DawsOS
find dawsos -name "*analyzer*.py"

# If found:
mkdir -p trinity3/agents/analyzers
cp dawsos/agents/analyzers/* trinity3/agents/analyzers/

# Test financial_analyst import
python3 -c "from trinity3.agents.financial_analyst import FinancialAnalyst; print('✅')"
```

**5. Make Decision**
- Review findings from steps 1-4
- Choose Scenario A, B, or C
- Document decision in WEEK5_PROGRESS.md

**6. Create Action Plan for Week 5**
- Based on chosen scenario
- List specific files to migrate/fix/enhance
- Estimate time for each task

---

## Week 5 Updated Plan

### If Scenario A (Trinity agents are good)

**Day 1**: Investigation + Fix analyzers
**Day 2**: Enhance portfolio_manager and risk_analyst to production quality
**Day 3**: Migrate forecast_dreamer, pattern_spotter, graph_mind from DawsOS
**Day 4**: Test all 11 agents
**Day 5**: Validate capabilities, create completion report

### If Scenario B (Trinity agents need enhancement)

**Day 1**: Investigation + Fix analyzers
**Day 2-3**: Remove mock data from equity/macro/market, wire to real services
**Day 4**: Enhance portfolio_manager and risk_analyst
**Day 5**: Test all agents, document remaining work

### If Scenario C (Replace with DawsOS)

**Day 1**: Investigation + Fix analyzers
**Day 2-3**: Find DawsOS equivalents, migrate to trinity3
**Day 4**: Wire all agents to trinity3 architecture
**Day 5**: Test all agents, document

---

## Success Criteria (Week 5)

**Must Have**:
- [x] Investigation complete (Scenario A/B/C chosen)
- [ ] agents.analyzers module working
- [ ] financial_analyst.py imports successfully
- [ ] All agents verified (production vs mock)
- [ ] Clear list of which agents to keep/enhance/replace

**Should Have**:
- [ ] All agents import successfully
- [ ] Critical DawsOS agents identified for migration
- [ ] Week 5 completion report with agent inventory

**Could Have**:
- [ ] All agents tested with sample capabilities
- [ ] Performance comparison (if replacing agents)

---

## Risk Assessment

### High Risk

- ⚠️ **Trinity 3.0 agents may be incomplete** → Investigation reveals truth
- ⚠️ **Missing agents.analyzers** → Can be copied from DawsOS
- ⚠️ **Database dependencies** → Can be refactored or PostgreSQL installed

### Medium Risk

- ⚠️ **DawsOS agents may not fit Trinity architecture** → May need adaptation
- ⚠️ **Capability mismatch** → AGENT_CAPABILITIES may need updating

### Low Risk

- ✅ **Core architecture solid** → Agent runtime works
- ✅ **We have options** → Multiple paths forward (A/B/C)

---

## Next Immediate Actions

**TODAY** (Next 30 minutes):
1. Read equity_agent.py completely
2. Search for "TODO", "MOCK", "STUB", "FIXME" in file
3. Check if it uses services.openbb_service properly
4. Document findings

**TODAY** (Next 1 hour):
5. Find dawsos/agents/analyzers/ directory
6. Copy to trinity3/agents/analyzers/
7. Test financial_analyst import

**TODAY** (Next 1 hour):
8. Read AGENT_CAPABILITIES.py
9. List all expected agents
10. Compare with what we have
11. Make go/no-go decision on Trinity 3.0 agents

---

**Priority**: 🔴 **CRITICAL**
**Timeline**: Today (before continuing Week 5)
**Owner**: Migration Team
**Decision Point**: End of Day 1 - Choose Scenario A, B, or C
