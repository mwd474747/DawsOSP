# Pattern-UI Integration Plan

**Date:** November 2, 2025  
**Purpose:** Plan integration of patterns into usable UI and user functions  
**Status:** 📋 PLANNING ONLY (No Code Changes)  
**Last Updated:** November 2, 2025 (Refined with MacroCyclesPage analysis)

---

## 🎯 Goal

Integrate all 12 patterns into the UI so users can access pattern-driven functionality through the UI pages, while respecting pages that need custom rendering for advanced features.

---

## 🔍 Key Understanding: Pattern Architecture

### Pattern Execution Flow
```
User Action → UI Page
  → PatternRenderer / Custom Implementation
  → apiClient.executePattern(patternName, inputs)
  → POST /api/patterns/execute
  → PatternOrchestrator.run_pattern()
  → Executes steps (capabilities)
  → Returns { data: { outputs }, charts, trace }
  → PatternRenderer extracts panels from patternRegistry
  → PanelRenderer renders each panel using getDataByPath()
```

### PatternRenderer Capabilities
- ✅ Executes patterns via `apiClient.executePattern()`
- ✅ Handles dynamic inputs (useEffect depends on `JSON.stringify(inputs)`)
- ✅ Extracts panels from `patternRegistry[pattern].display.panels`
- ✅ Uses `getDataByPath()` for nested data extraction
- ✅ Supports all 12 panel types
- ✅ Handles loading states and error states

### PatternRenderer Limitations
- ⚠️ Only renders panels defined in `patternRegistry`
- ⚠️ No built-in support for interactive features (tabs, filters, custom charts)
- ⚠️ No support for historical data generation (pattern only returns current state)
- ⚠️ Cannot customize panel layout or add custom UI elements around panels

### PatternRenderer Extension Patterns

**Pattern 1: PatternRenderer + Custom Controls** ✅ **WORKING EXAMPLE**
- **Example:** `ScenariosPage` (lines 8286-8312)
- **Approach:** Combine PatternRenderer with custom UI controls
- **Implementation:**
  ```javascript
  const [selectedScenario, setSelectedScenario] = useState('late_cycle_rates_up');
  return e('div', null,
      e('select', { 
          value: selectedScenario,
          onChange: (e) => setSelectedScenario(e.target.value)
      }, /* options */),
      e(PatternRenderer, {
          pattern: 'portfolio_scenario_analysis',
          inputs: { 
              portfolio_id: portfolioId,
              scenario_id: selectedScenario  // Dynamic input from dropdown
          }
      })
  );
  ```
- **Key:** PatternRenderer automatically re-executes when inputs change (useEffect dependency on `JSON.stringify(inputs)`)

**Pattern 2: Pattern Data + Custom Rendering** ✅ **WORKING EXAMPLE**
- **Example:** `MacroCyclesPage` (lines 6800-7730)
- **Approach:** Use pattern for data, extend with custom rendering
- **Implementation:**
  ```javascript
  const response = await cachedApiClient.executePattern('macro_cycles_overview', {...});
  const macroData = response.result || response.data || response;
  // Use pattern data for cycle states
  // Extend with custom Chart.js rendering, tabs, historical data
  ```
- **Key:** Pattern provides data, custom rendering provides advanced UI features

**Pattern 3: PatternRenderer with Callback** ⚠️ **AVAILABLE BUT NOT USED**
- **Example:** `PatternRenderer` has `onDataLoaded` callback (line 3218)
- **Approach:** Use callback to get pattern data for custom processing
- **Implementation:**
  ```javascript
  e(PatternRenderer, {
      pattern: 'portfolio_overview',
      inputs: { portfolio_id: portfolioId },
      onDataLoaded: (data) => {
          // Custom processing of pattern data
          // Custom rendering beyond panels
      }
  })
  ```
- **Key:** Can extract pattern data for custom rendering while still using PatternRenderer for panels

---

## 📊 Current State Analysis

### ✅ What's Already Integrated

#### Pattern Registry in UI ✅
**Location:** `full_ui.html` lines 2784-3117

**Status:** ✅ **Pattern registry exists with all 12 patterns defined**

**Patterns Registered:**
1. `portfolio_overview` ✅ - Defined in registry
2. `holding_deep_dive` ✅ - Defined in registry
3. `policy_rebalance` ✅ - Defined in registry
4. `portfolio_scenario_analysis` ✅ - Defined in registry
5. `portfolio_cycle_risk` ✅ - Defined in registry
6. `portfolio_macro_overview` ✅ - Defined in registry
7. `buffett_checklist` ✅ - Defined in registry
8. `news_impact_analysis` ✅ - Defined in registry
9. `export_portfolio_report` ✅ - Defined in registry
10. `macro_cycles_overview` ✅ - Defined in registry
11. `macro_trend_monitor` ✅ - Defined in registry
12. `cycle_deleveraging_scenarios` ✅ - Defined in registry

**Registry Structure:**
- Each pattern has: `name`, `description`, `category`, `display.panels[]`, `icon`
- Panels configured with: `id`, `title`, `type`, `dataPath`, `config`

---

#### PatternRenderer Component ✅
**Location:** `full_ui.html` lines 3170-3256

**Status:** ✅ **PatternRenderer component exists and works**

**Functionality:**
- Executes patterns via `apiClient.executePattern()`
- Receives pattern response: `{ data: { outputs }, charts, trace }`
- Extracts panels from `patternRegistry[pattern].display.panels`
- Renders panels using `PanelRenderer`
- Uses `getDataByPath()` for template resolution

**Data Flow:**
```
PatternRenderer
  → executePattern(pattern, inputs)
  → receives { data: { perf_metrics, valued_positions, ... } }
  → gets panels from patternRegistry
  → for each panel: PanelRenderer(data: getDataByPath(data, panel.dataPath))
```

---

#### PanelRenderer System ✅
**Location:** `full_ui.html` lines 3261-3298

**Status:** ✅ **Panel rendering system exists**

**Supported Panel Types:**
- `metrics_grid` → MetricsGridPanel
- `table` → TablePanel
- `line_chart` → LineChartPanel
- `pie_chart` → PieChartPanel
- `donut_chart` → DonutChartPanel
- `bar_chart` → BarChartPanel
- `action_cards` → ActionCardsPanel
- `cycle_card` → CycleCardPanel
- `scorecard` → ScorecardPanel
- `dual_list` → DualListPanel
- `news_list` → NewsListPanel
- `report_viewer` → ReportViewerPanel

---

### 🟡 What's Partially Integrated

#### Pages Using PatternRenderer 🟡

**Fully Integrated (Using PatternRenderer):**
1. ✅ **DashboardPage** (line 7817)
   - Uses: `PatternRenderer` with `portfolio_overview` pattern
   - Status: ✅ **FULLY INTEGRATED**

2. ✅ **PerformancePage** (line 8202)
   - Uses: `PatternRenderer` with `portfolio_overview` pattern
   - Status: ✅ **FULLY INTEGRATED**

3. ✅ **ScenariosPage** (line 8286)
   - Uses: `PatternRenderer` with `portfolio_scenario_analysis` pattern
   - Status: ✅ **FULLY INTEGRATED**

**Partially Integrated:**
4. 🟡 **MacroCyclesPage** (line 6800)
   - Uses: `cachedApiClient.executePattern('macro_cycles_overview')` (line 6846)
   - **WHY CUSTOM:** Page needs features beyond pattern output:
     - **Historical Chart Data**: Pattern only returns current cycle states (`stdc`, `ltdc`, `empire`, `civil`)
     - Page needs historical data for Chart.js visualization (`short_term_history`, `long_term_history`, `empire_history`, `dar_history`)
     - **Interactive Tabs**: 5 tabs (overview, short-term, long-term, empire, dar) with different chart types
     - **Custom Chart Rendering**: Direct Chart.js integration with custom configurations per cycle
     - **Custom Snapshot Tables**: Complex indicator mapping per cycle type
   - **Pattern Registry**: Already configured with 4 `cycle_card` panels (lines 2893-2926)
   - **Decision**: **HYBRID APPROACH** - Use pattern for cycle data, extend with custom rendering
   - Status: 🟡 **USING PATTERN BUT EXTENDED WITH CUSTOM RENDERING**

---

### ❌ What's Not Integrated

#### Pages Using Direct API Calls ❌

**Not Using Patterns:**
1. ❌ **HoldingsPage** (line 8105)
   - Uses: `apiClient.getHoldings()` (direct API call)
   - Should use: `portfolio_overview` pattern → extract `valued_positions.positions`
   - Status: ❌ **NOT USING PATTERN**

2. ❌ **TransactionsPage** (line 8131)
   - Uses: `apiClient.getTransactions()` (direct API call)
   - Should use: Pattern or direct endpoint (transactions might not need pattern)
   - Status: ❌ **NOT USING PATTERN** (may not need pattern)

3. ❌ **RiskPage** (line 8524)
   - Uses: `apiClient.executePattern('portfolio_cycle_risk', ...)` directly
   - Should use: `PatternRenderer` component
   - Status: ❌ **NOT USING PATTERN**

4. ❌ **AttributionPage** (line 8755)
   - Uses: `apiClient.executePattern('portfolio_overview', ...)` directly
   - Should use: `PatternRenderer` component
   - Status: ❌ **NOT USING PATTERN**

5. ❌ **OptimizerPage** (line 8924)
   - Uses: `apiClient.executePattern('policy_rebalance', ...)` directly
   - Should use: `PatternRenderer` component
   - Status: ❌ **NOT USING PATTERN**

6. ❌ **RatingsPage** (line 9302)
   - Uses: `apiClient.executePattern('buffett_checklist', ...)` directly
   - Should use: `PatternRenderer` component
   - Status: ❌ **NOT USING PATTERN**

7. ❌ **AIInsightsPage** (line 9660)
   - Uses: Chat interface (POST to `/api/ai/chat`)
   - **Purpose:** Interactive chat with Claude, not pattern display
   - **Decision:** Keep as chat interface (not pattern-based)
   - **Note:** `news_impact_analysis` pattern is used by `MarketDataPage` instead
   - Status: ❌ **NOT PATTERN-BASED** (intentional - chat interface)

8. 🟡 **MarketDataPage** (line 10483)
   - Uses: `apiClient.executePattern('news_impact_analysis', ...)` (line 10511)
   - Also uses: `apiClient.getHoldings()`, `apiClient.getQuote()`
   - Should use: `PatternRenderer` for news pattern
   - May need: `macro_trend_monitor` pattern for macro trends (if needed)
   - Status: 🟡 **USING PATTERN BUT NOT PatternRenderer**

9. ❌ **AlertsPage** (line 9869)
   - Uses: Direct API calls (CRUD operations: GET `/api/alerts`, POST `/api/alerts`, PATCH `/api/alerts/{id}`)
   - **Purpose:** Alert management (create, update, delete, list alerts)
   - **Decision:** Keep as CRUD interface (not pattern-based)
   - **Note:** `macro_trend_monitor` pattern can suggest alerts, but alert management is CRUD
   - Status: ❌ **NOT PATTERN-BASED** (intentional - CRUD interface)

10. 🟡 **ReportsPage** (line 10243)
    - Uses: POST to `/api/reports/generate` (not pattern execution)
    - **Purpose:** PDF generation and download
    - **Current:** Generates PDF blob and triggers download
    - **Decision:** May need `export_portfolio_report` pattern for generation
    - **Note:** Report generation might be better as pattern, but download UI is separate
    - Status: 🟡 **MAY NEED PATTERN** (investigate if pattern generates PDF)

11. ❌ **CorporateActionsPage** (line 10443)
    - Uses: Static data display (hardcoded table)
    - **Purpose:** Display corporate actions (dividends, splits)
    - **Decision:** May need direct endpoint or pattern (depends on data source)
    - **Note:** Currently shows static mock data
    - Status: ❌ **STATIC DATA** (needs investigation for data source)

---

## 📋 Integration Requirements

### Phase 1: Audit Current State

#### Task 1.1: Map UI Pages to Patterns
**Goal:** Create complete mapping of which pages should use which patterns

**Actions:**
1. List all 17 UI pages from `navigationStructure`
2. For each page, identify:
   - Current implementation (PatternRenderer vs direct API)
   - Which pattern should be used
   - What data the page needs
   - What panels the page should display

**Expected Output:**
- Complete page-to-pattern mapping
- Gap analysis (pages without patterns)

---

#### Task 1.2: Verify Pattern Registry Completeness
**Goal:** Ensure all patterns in backend match registry in UI

**Actions:**
1. List all 12 patterns from `backend/patterns/*.json`
2. Check each pattern in `patternRegistry` (full_ui.html lines 2784-3117)
3. Verify:
   - All backend patterns have UI registry entries
   - Panel configurations match pattern outputs
   - `dataPath` values match pattern response structure

**Expected Output:**
- Pattern registry completeness report
- List of missing or misconfigured patterns

---

#### Task 1.3: Verify Panel Configurations
**Goal:** Ensure panel dataPaths match pattern outputs

**Actions:**
1. For each pattern, check:
   - Pattern JSON `outputs` array (e.g., `["perf_metrics", "valued_positions"]`)
   - Pattern JSON `display.panels[]` (if exists)
   - UI `patternRegistry[pattern].display.panels[]` configuration
   - Panel `dataPath` matches output keys

**Example:**
- Pattern: `portfolio_overview`
- Outputs: `["perf_metrics", "currency_attr", "valued_positions", "sector_allocation", "historical_nav"]`
- UI Registry Panel: `{ id: 'holdings', dataPath: 'valued_positions.positions' }`
- ✅ Correct: `valued_positions` is an output, `.positions` is nested property

**Expected Output:**
- Panel configuration validation report
- List of incorrect `dataPath` values

---

### Phase 2: Migrate Pages to PatternRenderer

#### Task 2.1: Convert RiskPage to PatternRenderer
**Current:** Line 8524 - Uses `apiClient.executePattern('portfolio_cycle_risk')` directly  
**Target:** Use `PatternRenderer` component

**Pattern:** `portfolio_cycle_risk`

**Current Implementation Analysis:**
- Line 8540: `apiClient.executePattern('portfolio_cycle_risk', { portfolio_id })`
- Lines 8550-8568: Custom data processing (`processRiskData()`, fallback handling)
- Lines 8573-8623: Complex data extraction from pattern response
- **Issue:** Pattern response structure not matching UI expectations

**Pattern Registry Status:**
- ✅ Pattern in registry (line 2870): `portfolio_cycle_risk`
- ✅ Panels configured: `cycle_risk_summary` (metrics_grid), `vulnerabilities` (table)
- ⚠️ Panel dataPaths: `risk_summary`, `vulnerabilities`
- ⚠️ Need to verify pattern actually returns these keys

**Pattern Outputs (from JSON):**
- `cycle_risk_map`: Cycle-aware risk mapping
- `factor_exposures`: Factor exposures
- `dar`: Drawdown at Risk
- ⚠️ Pattern JSON doesn't explicitly list `risk_summary` or `vulnerabilities` as outputs

**Actions:**
1. Verify what `portfolio_cycle_risk` pattern actually returns
2. Check if pattern returns `risk_summary` and `vulnerabilities` keys
3. If pattern output structure differs, either:
   - Update pattern JSON to match UI expectations, OR
   - Update panel dataPaths in registry to match pattern outputs
4. Replace custom `fetchRiskData()` with `PatternRenderer`
5. Add dynamic input support for confidence level (if needed)
6. Remove custom data processing (rely on PatternRenderer)

**Expected Output:**
- RiskPage uses PatternRenderer
- Pattern output structure matches panel dataPaths
- All panels render correctly

---

#### Task 2.2: Convert AttributionPage to PatternRenderer
**Current:** Line 8755 - Uses `portfolio_overview` pattern directly  
**Target:** Use `PatternRenderer` component

**Pattern:** `portfolio_overview` (currency attribution data)

**Actions:**
1. Replace custom `fetchAttributionData()` with `PatternRenderer`
2. Use `portfolio_overview` pattern (already in registry)
3. Configure panel to show only currency attribution data
4. Filter panels to show only relevant attribution panels

**Expected Output:**
- AttributionPage uses PatternRenderer
- Only attribution panels displayed

---

#### Task 2.3: Convert OptimizerPage to PatternRenderer
**Current:** Line 8924 - Uses `apiClient.executePattern('policy_rebalance')` directly  
**Target:** Use `PatternRenderer` component with dynamic inputs

**Pattern:** `policy_rebalance`

**Current Implementation Analysis:**
- Line 8941: `apiClient.executePattern('policy_rebalance', { portfolio_id, policies, constraints })`
- Lines 8943-8952: Hardcoded policies and constraints
- Lines 8974-9006: Custom data processing
- **Issue:** User cannot adjust policies/constraints dynamically

**Pattern Registry Status:**
- ✅ Pattern in registry (line 3032): `policy_rebalance`
- ✅ Panels configured: `rebalance_summary` (metrics_grid), `trade_proposals` (table)
- ⚠️ Panel dataPaths: `summary`, `trades`
- Need to verify pattern returns these keys

**Pattern Outputs (from JSON):**
- `rebalance_summary`: Summary metrics
- `proposed_trades`: Array of trade proposals
- `impact_analysis`: Before/after comparison

**Pattern Inputs (from JSON):**
- `portfolio_id`: Required
- `policies`: Optional array (default: [])
- `constraints`: Optional object (default: { max_te_pct: 2.0, max_turnover_pct: 10.0, min_lot_value: 500 })

**Actions:**
1. Replace custom `fetchOptimizationData()` with `PatternRenderer`
2. Add UI controls for policies and constraints (if needed)
3. Use PatternRenderer's dynamic input support (inputs prop updates trigger re-execution)
4. Verify pattern returns `summary` and `trades` keys (or update registry dataPaths)
5. Remove custom data processing

**Expected Output:**
- OptimizerPage uses PatternRenderer
- Dynamic inputs work (policies/constraints can be adjusted if UI controls added)
- All panels render correctly

---

#### Task 2.4: Convert RatingsPage to PatternRenderer
**Current:** Line 9302 - Uses `apiClient.executePattern('buffett_checklist')` per security  
**Target:** Use `PatternRenderer` component (may need per-symbol rendering)

**Pattern:** `buffett_checklist`

**Current Implementation Analysis:**
- Line 9266: Gets holdings first via `apiClient.getHoldings()`
- Lines 9304-9328: Loops through securities, calls pattern for each:
  ```javascript
  const result = await apiClient.executePattern('buffett_checklist', {
      security_id: securityId
  });
  ```
- **Issue:** Pattern requires `security_id` input, so needs per-symbol calls
- **Question:** Can `buffett_checklist` pattern accept multiple securities?

**Pattern Registry Status:**
- ✅ Pattern in registry (line 2951): `buffett_checklist`
- ✅ Panels configured: `quality_score` (scorecard), `moat_analysis` (scorecard), `dividend_safety` (scorecard), `resilience` (metrics_grid)
- ⚠️ Panel dataPaths: `moat_strength`, `dividend_safety`, `resilience`

**Pattern Inputs (from JSON):**
- `security_id`: Required UUID
- Pattern appears designed for single security analysis

**Options:**

**Option A: PatternRenderer Per Security** ⭐ **RECOMMENDED**
- Keep current approach but use `PatternRenderer` instead of direct `executePattern()`
- Render multiple `PatternRenderer` instances (one per security)
- **Pros:** Works with current pattern design
- **Cons:** Multiple pattern calls (but can be parallel)

**Option B: Enhance Pattern for Multiple Securities**
- Modify `buffett_checklist` pattern to accept `security_ids` array
- Return ratings for all securities in one call
- **Pros:** Single pattern call
- **Cons:** Requires backend pattern changes

**Actions:**
1. Verify pattern accepts single `security_id` only
2. If single security: Use Option A - Multiple PatternRenderer instances
3. If pattern can be enhanced: Consider Option B for future optimization
4. Replace per-security `executePattern()` calls with `PatternRenderer`
5. Ensure panels match pattern outputs

**Expected Output:**
- RatingsPage uses PatternRenderer (possibly multiple instances)
- All securities display ratings correctly

---

#### Task 2.5: Review AIInsightsPage Pattern Integration
**Current:** Line 9660 - Uses chat interface, not pattern directly  
**Analysis:** Page is a chat interface, not a pattern display page

**Current Implementation:**
- Line 9660: `AIInsightsPage` - Chat interface with Claude
- Line 9700: POST to `/api/ai/chat` (not pattern execution)
- **Question:** Should this page use `news_impact_analysis` pattern?

**Pattern:** `news_impact_analysis`

**Pattern Purpose:** Analyze news impact on portfolio (not a chat interface)

**MarketDataPage Usage:**
- Line 10511: `apiClient.executePattern('news_impact_analysis', ...)` 
- This page actually uses the pattern for news analysis

**Decision:**
- **AIInsightsPage**: Keep as chat interface (not pattern-based)
- **MarketDataPage**: Convert to use PatternRenderer with `news_impact_analysis` pattern

**Actions:**
1. Verify AIInsightsPage is correctly a chat interface (not pattern display)
2. If AI insights should show pattern results, add pattern display section
3. Convert MarketDataPage to use PatternRenderer (see Task 2.9)

**Expected Output:**
- AIInsightsPage purpose clarified (chat vs pattern display)
- MarketDataPage uses PatternRenderer for news analysis

---

#### Task 2.6: Review ReportsPage Pattern Integration
**Current:** Line 10243 - Uses POST to `/api/reports/generate` (not pattern execution)  
**Analysis:** Page generates PDF reports, not displays pattern data

**Current Implementation:**
- Line 10254: `generateReport()` function
- Line 10262: POST to `/api/reports/generate?report_type=${reportType}`
- Line 10275: Gets PDF blob from response
- Line 10282: Triggers download
- **Purpose:** PDF generation and download, not pattern display

**Pattern:** `export_portfolio_report`

**Pattern Purpose:** Generate PDF reports with rights enforcement

**Options:**

**Option A: Keep Current Approach** ⭐ **RECOMMENDED**
- Keep direct API call for PDF generation
- PDF generation may be better as direct endpoint (file download)
- Pattern might be overkill for simple PDF generation
- **Pros:** Simple, direct file download
- **Cons:** Doesn't use pattern system
- **Action:** Verify if `/api/reports/generate` uses pattern internally

**Option B: Use Pattern for Report Generation**
- Use `export_portfolio_report` pattern to generate PDF
- Pattern returns PDF data, page handles download
- **Pros:** Uses pattern system
- **Cons:** May need special handling for binary data
- **Action:** Check if pattern returns PDF blob or URL

**Actions:**
1. Verify what `/api/reports/generate` endpoint does (does it use pattern internally?)
2. Check if `export_portfolio_report` pattern returns PDF blob or URL
3. If pattern is used internally, keep current approach (endpoint wraps pattern)
4. If pattern can be called directly, consider Option B
5. Document decision (pattern vs direct endpoint)

**Expected Output:**
- ReportsPage approach clarified (pattern vs direct endpoint)
- PDF generation works correctly

---

#### Task 2.7: Enhance MacroCyclesPage Pattern Integration
**Current:** Line 6800 - Uses pattern but with extensive custom rendering  
**Analysis:** Page ALREADY uses `macro_cycles_overview` pattern (line 6846), but extends it with:
- Custom Chart.js rendering (5 different chart types)
- Historical data generation (not provided by pattern)
- Interactive tab navigation
- Custom snapshot tables

**Pattern:** `macro_cycles_overview`

**Pattern Returns:**
- `stdc`: Short-term debt cycle state
- `ltdc`: Long-term debt cycle state  
- `empire`: Empire cycle state
- `civil`: Civil/internal order cycle state

**Pattern Does NOT Return:**
- `short_term_history`: Historical data for charts
- `long_term_history`: Historical data for charts
- `empire_history`: Historical data for charts
- `dar_history`: DAR historical data
- `regime_detection`: Regime classification

**Options:**

**Option A: Keep Current Hybrid Approach** ⭐ **RECOMMENDED**
- Keep pattern execution for cycle data
- Keep custom rendering for charts, tabs, historical data
- **Pros:** Preserves rich interactive UI, historical visualizations
- **Cons:** More code to maintain
- **Action:** Document that this is intentional architecture

**Option B: Simplify to PatternRenderer Only**
- Replace custom rendering with `PatternRenderer` using `cycle_card` panels
- Remove historical charts and tabs
- **Pros:** Simpler, consistent with other pages
- **Cons:** Loses rich interactive features, historical context
- **Action:** Only if user wants simpler UI

**Option C: Enhance Pattern to Include Historical Data**
- Extend `macro_cycles_overview` pattern to return historical data
- Use `PatternRenderer` with custom `line_chart` panels
- **Pros:** Uses pattern system fully
- **Cons:** Requires backend pattern changes, historical data might not be available
- **Action:** Investigate if backend can provide historical cycle data

**Recommended Approach:**
- **Keep Option A** - Document the hybrid approach as intentional
- Add comments explaining why custom rendering is needed
- Verify pattern data extraction is correct (currently uses `response.result || response.data || response`)
- Ensure fallback data matches pattern output structure

**Expected Output:**
- MacroCyclesPage pattern integration documented
- Pattern data extraction verified
- Custom rendering justified and documented

---

#### Task 2.8: Convert MarketDataPage to PatternRenderer
**Current:** Line 10483 - Uses `apiClient.executePattern('news_impact_analysis')` directly  
**Target:** Use `PatternRenderer` component for news analysis

**Pattern:** `news_impact_analysis`

**Current Implementation:**
- Line 10511: `apiClient.executePattern('news_impact_analysis', { portfolio_id, lookback_hours, min_impact_threshold })`
- Lines 10483-10566: Custom data fetching for holdings and prices
- **Note:** Page also shows real-time prices (may need to keep direct API calls for this)

**Pattern Registry Status:**
- ✅ Pattern in registry (line 2986): `news_impact_analysis`
- ✅ Panels configured: `news_summary` (metrics_grid), `news_items` (news_list)
- Panel dataPaths: `summary`, `news_items`

**Actions:**
1. Replace news pattern execution with `PatternRenderer`
2. Keep direct API calls for real-time prices (these aren't patterns)
3. Verify pattern returns `summary` and `news_items` keys
4. Test news panels render correctly

**Expected Output:**
- MarketDataPage uses PatternRenderer for news analysis
- Real-time price fetching remains direct API calls
- News panels display correctly

---

#### Task 2.9: Convert HoldingsPage (Optional - Pattern Extraction)
**Current:** Line 8105 - Uses `apiClient.getHoldings()` direct endpoint  
**Option 1:** Keep direct endpoint (simpler, faster)  
**Option 2:** Use `portfolio_overview` pattern and extract holdings

**Pattern:** `portfolio_overview` → `valued_positions.positions`

**Actions (if choosing Option 2):**
1. Replace `apiClient.getHoldings()` with `PatternRenderer`
2. Use `portfolio_overview` pattern
3. Configure to show only holdings panel
4. Extract holdings from pattern response

**Expected Output:**
- HoldingsPage uses pattern (if chosen)
- Or keeps direct endpoint for simplicity

---

### Phase 3: Handle Edge Cases

#### Task 3.1: Pages Without Patterns ✅ **ANALYZED**

**Pages That Don't Need Patterns (CRUD/Static/Chat):**
1. ✅ **TransactionsPage** (line 8131)
   - **Purpose:** Transaction history listing (read-only display)
   - **Current:** `apiClient.getTransactions()` (direct API call)
   - **Decision:** ✅ **Keep direct endpoint** - Simple data listing doesn't need pattern
   - **Reason:** No complex analysis, just data retrieval and display
   - **Status:** ✅ **DOCUMENTED** - Direct endpoint sufficient

2. ✅ **AlertsPage** (line 9869)
   - **Purpose:** Alert management (CRUD operations)
   - **Current:** Direct API calls (GET `/api/alerts`, POST `/api/alerts`, PATCH `/api/alerts/{id}`)
   - **Decision:** ✅ **Keep direct endpoint** - CRUD interface doesn't need pattern
   - **Reason:** Standard CRUD operations (create, read, update, delete)
   - **Note:** `macro_trend_monitor` pattern can suggest alerts, but alert management is CRUD
   - **Status:** ✅ **DOCUMENTED** - CRUD interface, not pattern-based

3. ✅ **AIInsightsPage** (line 9660)
   - **Purpose:** Interactive chat with Claude
   - **Current:** POST to `/api/ai/chat` (chat interface)
   - **Decision:** ✅ **Keep as chat interface** - Chat is not pattern-based
   - **Reason:** Conversational interface, not pattern execution
   - **Note:** `news_impact_analysis` pattern is used by `MarketDataPage` for news analysis
   - **Status:** ✅ **DOCUMENTED** - Chat interface, not pattern-based

4. ✅ **CorporateActionsPage** (line 10443)
   - **Purpose:** Display corporate actions (dividends, splits, earnings, mergers)
   - **Current:** Static data display (hardcoded table with mock data)
   - **Backend Endpoint:** `/api/corporate-actions` exists (line 4536 in `combined_server.py`)
   - **Endpoint Status:** ✅ **Endpoint exists** - Returns mock data with structured format
   - **Decision:** ✅ **Use direct endpoint** - Simple data listing doesn't need pattern
   - **Reason:** Endpoint already exists and returns structured data (actions array, summary, notifications)
   - **Action:** Update page to call `apiClient.getCorporateActions(portfolioId)` instead of static data
   - **Data Format:** `{ actions: [...], summary: {...}, notifications: {...} }`
   - **Status:** ✅ **RESOLVED** - Use direct endpoint, no pattern needed

5. ✅ **ReportsPage** (line 10243)
   - **Purpose:** PDF generation and download
   - **Current:** POST to `/api/reports/generate?report_type=${reportType}` (direct endpoint)
   - **Backend Endpoint:** ⚠️ **NOT FOUND** - Endpoint may not exist yet
   - **Pattern Available:** ✅ `export_portfolio_report` pattern exists (backend/patterns/export_portfolio_report.json)
   - **Pattern Capability:** Uses `reports.render_pdf` capability (ReportsAgent)
   - **Pattern Status:** Pattern returns `pdf_base64` in result (base64-encoded PDF bytes)
   - **Decision:** ⚠️ **Use pattern** - Pattern provides PDF generation with rights enforcement
   - **Reason:** Pattern orchestrates data collection and PDF generation, provides rights enforcement
   - **Action:** Either create `/api/reports/generate` endpoint that uses pattern, OR call pattern directly from UI
   - **Pattern Output:** `{ pdf_base64: "...", size_bytes: ..., download_filename: "...", status: "success" }`
   - **Status:** 🟡 **PENDING** - Verify endpoint exists or implement pattern-based generation

**Pages That Should Use Patterns:**
1. ✅ **RiskPage** - Should use `PatternRenderer` with `portfolio_cycle_risk` pattern
2. ✅ **AttributionPage** - Should use `PatternRenderer` with `portfolio_overview` pattern (filter to attribution panels)
3. ✅ **OptimizerPage** - Should use `PatternRenderer` with `policy_rebalance` pattern (add dynamic inputs)
4. ✅ **RatingsPage** - Should use `PatternRenderer` with `buffett_checklist` pattern (may need multiple instances)
5. ✅ **MarketDataPage** - Should use `PatternRenderer` with `news_impact_analysis` pattern

**Actions:**
1. ✅ Document pages that don't need patterns (CRUD, chat, static data)
2. ✅ Document pages that should use patterns
3. ✅ Investigate `CorporateActionsPage` data source - **RESOLVED**: Use `/api/corporate-actions` endpoint
4. ⚠️ Verify `ReportsPage` endpoint exists or implement pattern-based generation

---

#### Task 3.2: Pattern Input Handling ✅ **VERIFIED**

**Current State:** PatternRenderer receives `inputs` prop  
**Verification:** ✅ **PatternRenderer ALREADY supports dynamic inputs**

**Evidence:**
- `PatternRenderer` useEffect dependency: `[pattern, JSON.stringify(inputs)]` (line 3179)
- **ScenariosPage** already uses this successfully (lines 8286-8312):
  ```javascript
  const [selectedScenario, setSelectedScenario] = useState('late_cycle_rates_up');
  // ...
  e(PatternRenderer, {
      pattern: 'portfolio_scenario_analysis',
      inputs: { 
          portfolio_id: portfolioId,
          scenario_id: selectedScenario  // Dynamic input updates on dropdown change
      }
  })
  ```

**Patterns Needing Dynamic Inputs:**
1. ✅ **ScenariosPage** - Scenario dropdown (already working)
2. 🟡 **OptimizerPage** - Rebalancing constraints (needs conversion)
3. 🟡 **RiskPage** - Confidence level (needs conversion)
4. 🟡 **MacroCyclesPage** - Date selection (could add)

**Actions:**
1. ✅ Verify PatternRenderer handles dynamic inputs correctly - **VERIFIED**
2. ✅ Check if inputs update when user changes selections - **VERIFIED** (ScenariosPage example)
3. 🟡 Convert OptimizerPage to use PatternRenderer with dynamic inputs
4. 🟡 Convert RiskPage to use PatternRenderer with dynamic inputs

**Expected Output:**
- ✅ PatternRenderer supports dynamic inputs (already confirmed)
- Pattern re-execution on input change works (already confirmed)
- OptimizerPage and RiskPage converted to use PatternRenderer with dynamic inputs

---

#### Task 3.3: Error Handling

**Current State:** PatternRenderer has basic error handling  
**Challenge:** Need consistent error handling across all pages

**Actions:**
1. Verify PatternRenderer error display is user-friendly
2. Check if all panels handle missing data gracefully
3. Ensure error messages are informative
4. Test error recovery (retry functionality)

**Expected Output:**
- Consistent error handling across all pages
- User-friendly error messages
- Retry functionality works

---

#### Task 3.4: Loading States

**Current State:** PatternRenderer has loading spinner  
**Challenge:** Need consistent loading states

**Actions:**
1. Verify loading spinner appears during pattern execution
2. Check if loading messages are informative
3. Ensure smooth transitions between loading and loaded states
4. Test loading states for long-running patterns

**Expected Output:**
- Consistent loading states across all pages
- Informative loading messages

---

### Phase 4: Pattern Registry Enhancements

#### Task 4.1: Verify All Patterns in Registry

**Current State:** 12 patterns exist in backend  
**Challenge:** Verify all 12 are in UI registry

**Patterns to Verify:**
1. `portfolio_overview` ✅ (in registry)
2. `holding_deep_dive` ✅ (in registry)
3. `policy_rebalance` ✅ (in registry)
4. `portfolio_scenario_analysis` ✅ (in registry)
5. `portfolio_cycle_risk` ✅ (in registry)
6. `portfolio_macro_overview` ✅ (in registry)
7. `buffett_checklist` ✅ (in registry)
8. `news_impact_analysis` ✅ (in registry)
9. `export_portfolio_report` ✅ (in registry)
10. `macro_cycles_overview` ✅ (in registry)
11. `macro_trend_monitor` ✅ (in registry)
12. `cycle_deleveraging_scenarios` ✅ (in registry)

**Actions:**
1. Verify all 12 patterns in UI registry
2. Check panel configurations match backend pattern outputs
3. Verify `dataPath` values are correct
4. Test each pattern renders correctly

**Expected Output:**
- All 12 patterns verified in registry
- All panel configurations correct

---

#### Task 4.2: Add Missing Panel Configurations

**Current State:** Some patterns might have missing panel configs  
**Challenge:** Ensure all pattern outputs have corresponding panels

**Actions:**
1. For each pattern, check:
   - Pattern JSON `outputs` array
   - Pattern JSON `display.panels[]` (if exists in JSON)
   - UI `patternRegistry[pattern].display.panels[]`
2. Add missing panels to registry
3. Configure `dataPath` to match outputs
4. Choose appropriate panel type (table, chart, etc.)

**Expected Output:**
- All pattern outputs have panels configured
- All panels have correct `dataPath` values

---

#### Task 4.3: Panel Type Coverage

**Current State:** 12 panel types supported  
**Challenge:** Verify all panel types needed are available

**Panel Types Needed:**
1. `metrics_grid` ✅ - For performance metrics
2. `table` ✅ - For holdings, transactions
3. `line_chart` ✅ - For historical data
4. `pie_chart` ✅ - For allocations
5. `donut_chart` ✅ - For attribution
6. `bar_chart` ✅ - For comparisons
7. `action_cards` ✅ - For rebalancing actions
8. `cycle_card` ✅ - For macro cycles
9. `scorecard` ✅ - For ratings
10. `dual_list` ✅ - For before/after comparisons
11. `news_list` ✅ - For news/insights
12. `report_viewer` ✅ - For PDF reports

**Actions:**
1. Verify all panel types are implemented
2. Test each panel type renders correctly
3. Add missing panel types if needed

**Expected Output:**
- All required panel types available
- All panel types tested and working

---

### Phase 5: Data Flow Verification

#### Task 5.1: Verify Pattern Response Structure

**Current State:** Patterns return structured data  
**Challenge:** Ensure UI expects correct structure

**Pattern Response Format:**
```json
{
  "status": "success",
  "data": {
    "output1": {...},
    "output2": {...}
  },
  "charts": [...],
  "trace": {...}
}
```

**Actions:**
1. Verify PatternRenderer handles this structure correctly
2. Check `getDataByPath()` resolves paths correctly
3. Test nested data extraction (e.g., `valued_positions.positions`)
4. Verify all output keys match UI expectations

**Expected Output:**
- Pattern response structure verified
- Data extraction works correctly

---

#### Task 5.2: Verify Template Resolution

**Current State:** `getDataByPath()` function exists  
**Challenge:** Ensure template paths resolve correctly

**Example:**
- Panel `dataPath`: `'valued_positions.positions'`
- Pattern response: `{ data: { valued_positions: { positions: [...] } } }`
- Resolution: `getDataByPath(data, 'valued_positions.positions')` → `[...]`

**Actions:**
1. Test `getDataByPath()` with all panel dataPaths
2. Verify nested paths resolve correctly
3. Check error handling for missing paths
4. Test with actual pattern responses

**Expected Output:**
- All template paths resolve correctly
- Error handling for missing paths works

---

#### Task 5.3: Verify Caching Integration

**Current State:** `cachedApiClient` exists with pattern caching  
**Challenge:** Ensure PatternRenderer uses caching

**Current Implementation:**
- `cachedApiClient.executePattern()` has caching
- `PatternRenderer` uses `apiClient.executePattern()` (might not use cached)

**Actions:**
1. Verify PatternRenderer uses `cachedApiClient` if available
2. Check cache keys are correct
3. Test cache invalidation on pattern re-execution
4. Verify cache times are appropriate

**Expected Output:**
- PatternRenderer uses caching
- Cache invalidation works correctly

---

## 🎯 Success Criteria

### Phase 1: Audit Complete ✅
- [ ] All 17 pages mapped to patterns
- [ ] All 12 patterns verified in registry
- [ ] All panel configurations validated
- [ ] Gap analysis complete

### Phase 2: Migration Complete ✅
- [ ] RiskPage uses PatternRenderer
- [ ] AttributionPage uses PatternRenderer
- [ ] OptimizerPage uses PatternRenderer
- [ ] RatingsPage uses PatternRenderer (may need multiple instances)
- [ ] MarketDataPage uses PatternRenderer (for news analysis)
- [ ] ReportsPage pattern integration reviewed (pattern vs direct endpoint)
- [ ] MacroCyclesPage architecture documented (hybrid approach is intentional)
- [ ] HoldingsPage decision made (pattern vs direct)
- [ ] CorporateActionsPage data source investigated

### Phase 3: Edge Cases Handled ✅
- [ ] Pages without patterns documented (CRUD, chat, static data)
- [ ] Dynamic inputs work correctly (verified with ScenariosPage)
- [ ] Error handling consistent
- [ ] Loading states consistent
- [ ] Hybrid pattern approach documented (MacroCyclesPage example)

### Phase 4: Registry Complete ✅
- [ ] All patterns in registry
- [ ] All panels configured
- [ ] All panel types available

### Phase 5: Data Flow Verified ✅
- [ ] Pattern response structure verified
- [ ] Template resolution works
- [ ] Caching integration works

---

## 📊 Estimated Effort

### Phase 1: Audit (Planning)
- **Time:** 2-3 hours
- **Complexity:** Low
- **Risk:** None (no code changes)

### Phase 2: Migration
- **Time:** 8-12 hours
- **Complexity:** Medium
- **Risk:** Medium (UI changes, need testing)
- **Note:** Some pages may need Pattern 2 (PatternRenderer + Custom Controls) or Pattern 3 (Pattern Data + Custom Rendering)

### Phase 3: Edge Cases
- **Time:** 4-6 hours
- **Complexity:** Medium
- **Risk:** Low (mostly enhancements)

### Phase 4: Registry
- **Time:** 2-4 hours
- **Complexity:** Low
- **Risk:** Low (configuration only)

### Phase 5: Verification
- **Time:** 3-4 hours
- **Complexity:** Low
- **Risk:** None (testing only)

**Total Estimated Time:** 19-29 hours

---

## 🚧 Risks & Mitigations

### Risk 1: Pattern Response Structure Mismatch
**Risk:** UI expects different structure than pattern returns  
**Mitigation:** Verify all panel dataPaths match pattern outputs in Phase 1  
**Status:** ✅ **ScenariosPage verified** - Structure matches expectations

### Risk 2: Missing Panel Types
**Risk:** Pattern needs panel type that doesn't exist  
**Mitigation:** Identify missing panel types in Phase 1, add in Phase 4  
**Status:** ✅ **All panel types exist** - 12 panel types supported

### Risk 3: Performance Issues
**Risk:** PatternRenderer might be slower than direct calls  
**Mitigation:** Use caching, optimize pattern execution, benchmark performance  
**Status:** ⚠️ **Needs verification** - Test performance after migration

### Risk 4: Dynamic Input Handling ✅ **VERIFIED**
**Risk:** PatternRenderer might not handle dynamic inputs well  
**Mitigation:** Test dynamic inputs in Phase 3, enhance if needed  
**Status:** ✅ **VERIFIED** - ScenariosPage already uses dynamic inputs successfully

### Risk 5: Custom Rendering vs PatternRenderer Trade-offs
**Risk:** Pages may need custom rendering but lose pattern benefits  
**Mitigation:** Document hybrid approach (Pattern 3), consider `onDataLoaded` callback  
**Status:** ✅ **DOCUMENTED** - MacroCyclesPage shows hybrid approach

### Risk 6: Pattern Output Structure Changes
**Risk:** Backend pattern changes break UI panels  
**Mitigation:** Verify panel dataPaths match pattern outputs, test after backend changes  
**Status:** ⚠️ **Ongoing** - Needs verification in Phase 1

---

## 📋 Next Steps (After Planning)

1. **Review this plan** - Verify completeness and accuracy
2. **Prioritize phases** - Decide which phases to tackle first
3. **Create detailed task breakdown** - Break each phase into specific tasks
4. **Start with Phase 1** - Complete audit before making changes
5. **Execute incrementally** - One page at a time, test after each change

---

## 📚 Related Documentation

- **Pattern Registry:** `full_ui.html` lines 2784-3117
- **PatternRenderer:** `full_ui.html` lines 3170-3256
- **PanelRenderer:** `full_ui.html` lines 3261-3298
- **Pattern JSON Files:** `backend/patterns/*.json`
- **Backend Pattern Orchestrator:** `backend/app/core/pattern_orchestrator.py`
- **MacroCyclesPage:** `full_ui.html` lines 6800-7730 (hybrid pattern + custom rendering example)
- **ScenariosPage:** `full_ui.html` lines 8286-8312 (PatternRenderer with dynamic inputs example)

---

## 🔍 Detailed Analysis: Pattern Integration Patterns

### Pattern 1: Pure PatternRenderer (Simple Pages)
**Examples:** `DashboardPage`, `PerformancePage`, `ScenariosPage` (pattern display only)
- **Approach:** Use `PatternRenderer` directly with pattern inputs
- **Use Case:** Pages that only need to display pattern results
- **Benefits:** Simple, consistent, easy to maintain
- **Limitations:** No custom UI beyond panels

### Pattern 2: PatternRenderer + Custom Controls (Interactive Pages)
**Example:** `ScenariosPage` (lines 8286-8312)
- **Approach:** Combine `PatternRenderer` with custom UI controls (dropdowns, filters, buttons)
- **Use Case:** Pages that need user input to modify pattern execution
- **Implementation:**
  ```javascript
  const [selectedScenario, setSelectedScenario] = useState('late_cycle_rates_up');
  return e('div', null,
      // Custom UI controls
      e('select', { value: selectedScenario, onChange: ... }),
      // PatternRenderer uses dynamic inputs
      e(PatternRenderer, {
          pattern: 'portfolio_scenario_analysis',
          inputs: { scenario_id: selectedScenario }  // Updates trigger re-execution
      })
  );
  ```
- **Benefits:** Interactive while using pattern system
- **Key:** PatternRenderer automatically re-executes when inputs change

### Pattern 3: Pattern Data + Custom Rendering (Advanced Pages)
**Example:** `MacroCyclesPage` (lines 6800-7730)
- **Approach:** Execute pattern manually, use data for custom rendering
- **Use Case:** Pages that need advanced UI beyond standard panels
- **Implementation:**
  ```javascript
  const response = await cachedApiClient.executePattern('macro_cycles_overview', {...});
  const macroData = response.result || response.data || response;
  // Use pattern data for cycle states (stdc, ltdc, empire, civil)
  // Extend with custom Chart.js rendering, tabs, historical data
  ```
- **Benefits:** Full control over rendering, can add advanced features
- **Trade-offs:** More code, but enables rich interactive UI

---

## 🔍 Detailed Analysis: MacroCyclesPage Architecture

### Why MacroCyclesPage Uses Pattern 3 (Pattern Data + Custom Rendering)

**History:** Created around 2025-10-31 (commits: `0c1e938`, `dca293e`, `e97c66f`)
- Initially added as new page for macro cycles analysis
- Added civil and empire cycles integration
- Evolved to include interactive tabs and charts

**Pattern Integration:**
- ✅ Uses `macro_cycles_overview` pattern (line 6846)
- ✅ Pattern registered in UI (lines 2893-2926)
- ✅ Pattern returns: `stdc`, `ltdc`, `empire`, `civil` cycle states

**Custom Features Beyond Pattern:**
1. **Historical Data Generation** (lines 6946-6984)
   - Pattern only returns current cycle state
   - Page generates historical data for Chart.js visualization
   - `short_term_history`, `long_term_history`, `empire_history`, `dar_history`
   - **Backend doesn't provide this** - would require pattern enhancement

2. **Interactive Tab Navigation** (lines 7548-7562)
   - 5 tabs: overview, short-term, long-term, empire, dar
   - PatternRenderer doesn't support tab navigation
   - Each tab shows different chart type

3. **Custom Chart Rendering** (lines 7011-7371)
   - Direct Chart.js integration
   - 5 different chart configurations:
     - `renderShortTermChart()`: Multi-line chart (debt, GDP, credit)
     - `renderLongTermChart()`: Multi-line chart (debt/GDP, productivity, inequality)
     - `renderEmpireChart()`: Multi-line chart (power, education, military, trade)
     - `renderDarChart()`: Line chart with threshold
     - `renderOverviewChart()`: Radar chart comparing all 4 cycles
   - More sophisticated than standard `LineChartPanel`

4. **Custom Snapshot Tables** (lines 7386-7535)
   - Complex indicator mapping per cycle type
   - Handles multiple data key variations
   - Shows trend indicators and data sources

**Conclusion:**
MacroCyclesPage intentionally extends the pattern with custom rendering because:
- Pattern provides cycle state data (core functionality)
- Custom rendering provides rich interactive visualizations (UX enhancement)
- This is a valid architectural pattern: **Pattern for data, custom UI for advanced features**

**Recommendation:**
- ✅ Keep current hybrid approach (Pattern 3: Pattern Data + Custom Rendering)
- ✅ Document as intentional architecture
- ✅ Verify pattern data extraction is correct (currently uses `response.result || response.data || response`)
- ✅ Ensure fallback data matches pattern output structure
- ⚠️ Consider enhancing pattern in future to include historical data (if backend can provide it)
- ⚠️ Consider using `onDataLoaded` callback if PatternRenderer is enhanced to support custom rendering

**Future Enhancement Option:**
- If PatternRenderer is enhanced to support custom rendering hooks:
  ```javascript
  e(PatternRenderer, {
      pattern: 'macro_cycles_overview',
      inputs: { asof_date: ... },
      onDataLoaded: (data) => {
          // Use pattern data (data.stdс, data.ltdc, data.empire, data.civil)
          // Add custom rendering (charts, tabs, historical data)
      }
  })
  ```
- This would allow using PatternRenderer for data fetching while maintaining custom rendering

---

**Last Updated:** November 2, 2025  
**Status:** 📋 PLANNING COMPLETE & REFINED - Ready for execution after review

---

## 🔍 Summary of Key Findings

### ✅ Fully Integrated Pages (Using PatternRenderer)
1. **DashboardPage** - Uses `PatternRenderer` with `portfolio_overview` pattern
2. **PerformancePage** - Uses `PatternRenderer` with `portfolio_overview` pattern
3. **ScenariosPage** - Uses `PatternRenderer` with `portfolio_scenario_analysis` pattern + dynamic inputs

### 🟡 Partially Integrated Pages (Using Patterns but Not PatternRenderer)
1. **RiskPage** - Uses `portfolio_cycle_risk` pattern directly (should use PatternRenderer)
2. **AttributionPage** - Uses `portfolio_overview` pattern directly (should use PatternRenderer)
3. **OptimizerPage** - Uses `policy_rebalance` pattern directly (should use PatternRenderer)
4. **RatingsPage** - Uses `buffett_checklist` pattern directly (should use PatternRenderer)
5. **MarketDataPage** - Uses `news_impact_analysis` pattern directly (should use PatternRenderer)

### 🎨 Hybrid Architecture Pages (Pattern Data + Custom Rendering)
1. **MacroCyclesPage** - Uses `macro_cycles_overview` pattern for data, custom Chart.js rendering for UI
   - **Rationale:** Pattern provides cycle states, custom rendering provides historical charts, tabs, and interactive features
   - **Status:** ✅ **INTENTIONAL** - This is a valid architectural pattern

### ❌ Pages Without Patterns (CRUD/Static/Chat)
1. **TransactionsPage** - Direct endpoint (simple data listing)
2. **AlertsPage** - Direct endpoint (CRUD operations)
3. **AIInsightsPage** - Chat interface (not pattern-based)
4. **CorporateActionsPage** - Direct endpoint (`/api/corporate-actions` exists)
5. **ReportsPage** - Pattern available (`export_portfolio_report`) but endpoint verification needed

### 📋 Integration Patterns Identified
1. **Pattern 1: Pure PatternRenderer** - Simple pages (DashboardPage, PerformancePage)
2. **Pattern 2: PatternRenderer + Custom Controls** - Interactive pages (ScenariosPage)
3. **Pattern 3: Pattern Data + Custom Rendering** - Advanced pages (MacroCyclesPage)

### 🚧 Outstanding Tasks
1. **Phase 1: Audit** - Map all 17 pages to patterns, verify registry completeness
2. **Phase 2: Migration** - Convert 5 partially integrated pages to PatternRenderer
3. **Phase 3: Edge Cases** - Handle error states, loading states, dynamic inputs
4. **Phase 4: Registry** - Verify all panel configurations, add missing panels
5. **Phase 5: Verification** - Test pattern execution, data extraction, caching

