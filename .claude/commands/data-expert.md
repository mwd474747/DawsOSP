---
description: Activate Data Integration Expert for data architecture analysis
---

Activate the **Data Integration Expert** agent to analyze and improve data flow, integration, and architecture.

**Agent Capabilities:**
- Analyze current data integration patterns
- Identify data flow bottlenecks and quality issues
- Recommend data architecture improvements
- Design robust data pipelines
- Ensure data provenance and lineage tracking

**Knowledge Sources:**
- `/.claude/agents/data-integration-expert.md` - Agent context and workflows
- `/.claude/knowledge/data-contracts.md` - Data contract specifications
- `/.claude/knowledge/data-lineage.md` - Lineage tracking patterns

**Available Workflows:**

### 1. Diagnose Data Flow Issues
```
/data-expert diagnose <entity_type> <entity_id>
```
**Example:** `/data-expert diagnose portfolio_value portfolio_123`

**Output:**
- Upstream dependencies (what data this depends on)
- Data quality checks
- Freshness validation
- Root cause identification

---

### 2. Analyze Data Architecture
```
/data-expert analyze-architecture
```

**Output:**
- Current data sources (external APIs, user input, computed)
- Data flow patterns (ingestion, computation, storage)
- Identified issues (missing validation, no lineage, inconsistent types)
- Recommendations (contracts, lineage, quality checks)

---

### 3. Design Data Pipeline
```
/data-expert design-pipeline <source> <destination>
```
**Example:** `/data-expert design-pipeline FRED economic_indicators`

**Output:**
- Pipeline architecture diagram
- Data contract definition
- Quality checks specification
- Lineage tracking approach
- Error handling strategy

---

### 4. Validate Data Contract
```
/data-expert validate-contract <entity_type>
```
**Example:** `/data-expert validate-contract economic_indicator`

**Output:**
- Contract validation results
- Data quality metrics
- Violations found (errors, warnings)
- Recommendations for fixes

---

### 5. Trace Data Lineage
```
/data-expert trace-lineage <entity_type> <entity_id>
```
**Example:** `/data-expert trace-lineage factor_exposure portfolio_123_pack_456`

**Output:**
- Lineage graph (upstream and downstream)
- Data provenance information
- Computation metadata
- Quality indicators

---

## Current DawsOS Data Issues (Known)

**Critical Issues:**
1. 🔴 **Field Name Bug:** `valuation_date` vs `asof_date` mismatch
   - Location: `backend/app/services/factor_analysis.py:287`
   - Impact: SQL errors in FactorAnalyzer
   - See: `REPLIT_BACKEND_TASKS.md` Task 1

2. 🔴 **Missing Table:** `economic_indicators` not created
   - Required by: FactorAnalyzer service
   - Migration: `015_add_economic_indicators.sql` not run
   - See: `REPLIT_BACKEND_TASKS.md` Task 3

3. 🔴 **Stub Data:** `risk.compute_factor_exposures` returns fake data
   - Location: `backend/app/agents/financial_analyst.py:1086-1110`
   - Impact: Risk Analytics page shows fake data (user trust issue)
   - See: `REFACTORING_MASTER_PLAN.md` Issue 1

**High Priority Issues:**
4. ⚠️ **No Data Provenance:** Can't tell stub data from real data
   - Impact: Users trust fake data, can't audit data quality
   - See: `DATA_ARCHITECTURE.md` Data Flow section

5. ⚠️ **No Data Validation:** No quality checks on ingestion/computation
   - Impact: Bad data → bad results, silent failures
   - See: `COMPREHENSIVE_REFACTORING_PLAN.md` Phase 2 Task 2.1

6. ⚠️ **Inconsistent Response Formats:** 3 incompatible pattern output formats
   - Impact: UI crashes or shows "No data"
   - See: `REFACTORING_MASTER_PLAN.md` Issue 2

---

## Recommended First Steps

**Quick Wins (Fix Critical Bugs First):**
1. Fix field name bug (`valuation_date` vs `asof_date`) - 1-2h
2. Create `economic_indicators` table - 2-3h
3. Fix import bug (`FactorAnalysisService` → `FactorAnalyzer`) - 1h
4. Test FactorAnalyzer with `/test-factor-analyzer` - 30min

**Then Improve Data Quality (Phase 2):**
5. Define data contracts for key entities - 8h
6. Implement pattern validation - 12h
7. Standardize response formats - 8h
8. Add provenance tracking - 4h

**Then Add Advanced Features (Optional):**
9. Implement data lineage tracking - 16-24h
10. Build lineage visualization UI - 8-12h

---

## Example Usage

### Analyze Current Data Architecture
```
/data-expert analyze-architecture
```

**Expected Output:**
```
Data Architecture Analysis
==========================

Data Sources (3):
1. External APIs:
   - FRED (economic indicators) - 40 series configured
   - Market Data (prices, corporate actions)
   - News APIs (financial news)

2. User Input:
   - Portfolio holdings (lots table)
   - Transactions
   - User preferences

3. Computed Data:
   - Portfolio metrics (daily values, returns)
   - Factor exposures (risk analytics) ⚠️ CURRENTLY STUB DATA
   - Macro regime detection

Data Flow Patterns (4):
1. External Data Ingestion (FRED)
   - Issues: ❌ No deduplication, ❌ No validation, ❌ No rate limiting

2. Portfolio Valuation
   - Issues: ⚠️ Field name mismatch, ⚠️ No price staleness check

3. Factor Analysis (BROKEN)
   - Issues: 🔴 Uses stub data, 🔴 Field name bug, 🔴 Missing table

4. Pattern Orchestration
   - Issues: ⚠️ No validation, ⚠️ 3 incompatible formats

Recommendations (4):
1. Implement data contracts (8h) - Phase 2 Task 2.1
2. Implement lineage tracking (16-24h) - New feature
3. Standardize field names (8h) - Phase 2 Task 2.3
4. Implement data quality checks (12h) - Phase 2 Task 2.2

See: /.claude/agents/data-integration-expert.md for details
```

---

## Documentation References

**Agent Context:**
- [Data Integration Expert Agent](../.claude/agents/data-integration-expert.md)

**Knowledge Base:**
- [Data Contracts](../.claude/knowledge/data-contracts.md)
- [Data Lineage Tracking](../.claude/knowledge/data-lineage.md)

**Data Architecture Docs:**
- [DATA_ARCHITECTURE.md](../../DATA_ARCHITECTURE.md)
- [DATABASE.md](../../DATABASE.md)
- [COMPREHENSIVE_REFACTORING_PLAN.md](../../COMPREHENSIVE_REFACTORING_PLAN.md)

**Bug Details:**
- [REPLIT_BACKEND_TASKS.md](../../REPLIT_BACKEND_TASKS.md)
- [REFACTORING_MASTER_PLAN.md](../../REFACTORING_MASTER_PLAN.md)
- [FIELD_NAME_ANALYSIS_COMPREHENSIVE.md](../../FIELD_NAME_ANALYSIS_COMPREHENSIVE.md)

---

**Status:** ✅ Ready to use - Activate expert with `/data-expert <workflow>`
