# Database Agent Prompts - Validation Questions

**Date:** November 3, 2025  
**Purpose:** Prompts to ask the database agent on the deployed app to validate and understand database implementation  
**Status:** 📋 PROMPTS ONLY (No Code Changes)

---

## 🔍 Database Schema Validation Prompts

### 1. Table Existence & Status

**Prompt:**
```
List all tables in the database and indicate which ones are:
1. Actively queried (have SELECT queries in code)
2. Actively written (have INSERT/UPDATE queries in code)
3. Exist but unused (table exists but no queries found)
4. Are hypertables (TimescaleDB)
5. Are views
```

**Purpose:** Validate our understanding of which tables exist vs are actually used.

---

**Prompt:**
```
For each of these tables, verify if they exist and are used:
- currency_attribution (hypertable)
- factor_exposures (hypertable)
- regime_history
- scenario_shocks
- position_factor_betas
- macro_indicators (hypertable)
- notifications
- dlq
- corporate_actions

For each, indicate:
1. Does the table exist? (Yes/No)
2. Is it actively queried? (Yes/No, with code location if Yes)
3. Is it actively written? (Yes/No, with code location if Yes)
4. Is it a hypertable? (Yes/No)
5. Current row count
```

**Purpose:** Validate our table-by-table assessment.

---

### 2. Corporate Actions Implementation

**Prompt:**
```
Examine the corporate actions feature:
1. Does a `corporate_actions` table exist? If yes, what is its schema?
2. What does migration 008 (`008_add_corporate_actions_support.sql`) actually create?
3. What columns does the `transactions` table have for corporate actions? (pay_date, pay_fx_rate_id, ex_date, etc.)
4. Is the `/api/corporate-actions` endpoint querying from a database table or returning mock data?
5. Is there any agent capability for corporate actions?
6. Is there any service that fetches corporate actions from external sources (Yahoo Finance, Alpha Vantage)?
```

**Purpose:** Validate corporate actions gaps we identified.

---

**Prompt:**
```
Analyze the corporate actions endpoint implementation:
1. Show me the code for `/api/corporate-actions` endpoint
2. Does it query the database? If so, which tables?
3. Does it accept `portfolio_id` parameter? Is it used?
4. Does it query actual portfolio holdings from the `lots` table?
5. Does it return real corporate actions or mock data?
```

**Purpose:** Verify if corporate actions endpoint is using mock data.

---

### 3. Pattern Response Structures

**Prompt:**
```
Examine pattern execution and response structures:
1. How does the pattern orchestrator store capability results in the state dictionary?
2. If a capability returns `{"historical_nav": [...]}`, how is it stored in state?
3. Is there any "nested storage pattern" where results are stored under keys that match the output structure?
4. How does the API transform pattern state to response format?
5. Are there any wrapper layers that modify the response structure (SuccessResponse, etc.)?
```

**Purpose:** Understand nested storage pattern issue.

---

**Prompt:**
```
Trace the data flow for `portfolio_historical_nav` capability:
1. What does the `portfolio_historical_nav` capability return?
2. How is it stored in the pattern orchestrator state?
3. How does the pattern JSON reference it (what key name)?
4. How does the API endpoint return it?
5. What structure does the frontend receive?
6. Is there any double nesting (e.g., `historical_nav.historical_nav`)?
```

**Purpose:** Validate nested storage pattern issue for chart rendering.

---

### 4. Computation vs Storage Patterns

**Prompt:**
```
For these tables that exist but may not be used:
- currency_attribution (hypertable)
- factor_exposures (hypertable)

1. Does the CurrencyAttributionService query from `currency_attribution` table or compute from `lots`?
2. Does the RiskService query from `factor_exposures` table or compute on-demand?
3. If they compute, why do the tables exist? Are they for future caching?
4. Are there any INSERT statements that write to these tables?
```

**Purpose:** Validate compute-first vs cache-optional architecture.

---

**Prompt:**
```
Examine the regime_history table:
1. Is the `regime_history` table actively used?
2. Does MacroService.store_regime_snapshot() write to it?
3. Does MacroService.get_regime_history() query from it?
4. Or is regime history computed on-demand from macro_indicators?
```

**Purpose:** Validate regime_history table usage.

---

### 5. Data Population & Dependencies

**Prompt:**
```
Analyze data population and dependencies:
1. What is the current row count for each table?
2. Which tables are empty (0 rows)?
3. For `portfolio_metrics`: Does it require `portfolio_daily_values` to be populated first?
4. Is there a computation dependency chain (e.g., daily_values → metrics)?
5. Which tables have minimal data (1-2 rows) vs active data (100+ rows)?
```

**Purpose:** Understand data population status and dependencies.

---

**Prompt:**
```
Examine FX rates:
1. How many FX rate pairs are in the `fx_rates` table?
2. What currency pairs are present?
3. Are CAD/USD and EUR/USD present?
4. Which currency pairs are required for the application to function?
5. How does PricingService.get_fx_rate() handle missing pairs?
```

**Purpose:** Validate FX rates requirements.

---

### 6. Migration 008 - Corporate Actions Support

**Prompt:**
```
Examine migration 008 (`008_add_corporate_actions_support.sql`):
1. What exactly does this migration create?
2. Does it create a `corporate_actions` table? If yes, what is its schema?
3. Does it only add columns to `transactions` table? If yes, which columns?
4. What is the purpose of this migration - past dividends or upcoming corporate actions?
```

**Purpose:** Understand what migration 008 actually does.

---

### 7. Agent Capabilities

**Prompt:**
```
List all agent capabilities that interact with the database:
1. Which agents have capabilities that query the database?
2. Which agents have capabilities that write to the database?
3. Is there a corporate actions agent or capability?
4. Is there a capability for fetching corporate actions from external sources?
5. Which agents compute data on-demand vs query stored data?
```

**Purpose:** Understand agent capabilities and database interaction patterns.

---

### 8. Field Naming Transformations

**Prompt:**
```
Examine field naming across layers:
1. In the `lots` table, what is the field name for open quantity? (`qty_open` or `quantity`?)
2. When FinancialAnalyst queries lots, what field name does it use?
3. When the API returns lot data, what field name is used?
4. When the UI receives lot data, what field name does it expect?
5. Are there any field name transformations happening at different layers?
```

**Purpose:** Validate field naming transformation issue.

---

### 9. Pattern Execution Flow

**Prompt:**
```
Trace a complete pattern execution flow for `portfolio_overview` pattern:
1. What capabilities does it execute?
2. How are capability results stored in state (what keys)?
3. How does the pattern JSON reference these results?
4. How does the orchestrator transform state to response?
5. What structure does the API return?
6. How does the frontend extract data from the response?
```

**Purpose:** Understand complete data flow from database to UI.

---

### 10. Missing Gaps Validation

**Prompt:**
```
Based on your knowledge of the codebase, validate these gaps we identified:
1. Corporate Actions: Is there a `corporate_actions` table for upcoming events? Or only past dividends in `transactions`?
2. Pattern Responses: Are there nested storage issues (e.g., `historical_nav.historical_nav`)?
3. Computed vs Stored: Are `currency_attribution` and `factor_exposures` computed or queried?
4. Dependencies: Do `portfolio_metrics` require `portfolio_daily_values` to be populated first?
5. FX Rates: Are CAD/USD and EUR/USD present? Are there warnings about missing rates?
```

**Purpose:** Validate all identified gaps.

---

## 🎯 Priority Prompts (Start Here)

### Most Critical (Start with these)

1. **Corporate Actions Implementation:**
   ```
   Does a `corporate_actions` table exist? What does migration 008 create? Does the /api/corporate-actions endpoint query the database or return mock data?
   ```

2. **Pattern Response Nested Storage:**
   ```
   How does the pattern orchestrator store capability results? If a capability returns {"historical_nav": [...]}, is it stored as state["historical_nav"] = {"historical_nav": [...]} creating double nesting?
   ```

3. **Compute vs Store Pattern:**
   ```
   Does CurrencyAttributionService query from currency_attribution table or compute from lots? Does RiskService query from factor_exposures table or compute on-demand?
   ```

---

## 📊 Expected Responses Format

For each prompt, ask for:
1. **Direct answer** (Yes/No/Exists/Doesn't exist)
2. **Code evidence** (file path and line numbers)
3. **Current state** (row counts, usage patterns)
4. **Architecture explanation** (why it exists, how it's used)

---

## 🔄 Follow-up Prompts Based on Responses

If the agent confirms gaps exist:

**For Corporate Actions:**
```
What would be required to implement corporate actions properly? What tables, services, and agent capabilities would be needed?
```

**For Nested Storage:**
```
What would be required to fix the nested storage pattern? Would it break existing patterns?
```

**For Compute vs Store:**
```
Should we implement caching for currency_attribution and factor_exposures? What would be the implementation approach?
```

---

## 📋 Usage Instructions

1. **Start with Priority Prompts** - These address the most critical gaps
2. **Ask one prompt at a time** - More focused questions get better answers
3. **Request code evidence** - Ask for file paths and line numbers
4. **Ask for current state** - Row counts, usage patterns, etc.
5. **Follow up with implementation questions** - If gaps are confirmed, ask what's needed

---

**Status:** Prompts ready for database agent validation

