# UI Integration Context

**Date:** November 4, 2025  
**Status:** ✅ **READY TO EXECUTE**  
**Purpose:** Gather full context for UI integration work

---

## 📊 Current State Summary

### ✅ Fully Integrated Pages (5 pages)

1. **Dashboard** - Uses PatternRenderer with `portfolio_overview` ✅
2. **Scenarios** - Uses PatternRenderer with `portfolio_scenario_analysis` ✅
3. **Risk Analytics** - Uses PatternRenderer with `portfolio_cycle_risk` ✅
4. **Optimizer** - Uses PatternRenderer with `policy_rebalance` (custom processing) ✅
5. **Reports** - Uses PatternRenderer with `export_portfolio_report` ✅ **MIGRATED**

### ⚠️ Partially Integrated Pages (6 pages)

1. **PerformancePage** - ✅ **ALREADY MIGRATED** (uses PatternRenderer, legacy function exists)
2. **AttributionPage** - Hidden PatternRenderer, should show panels directly
3. **MacroCyclesPage** - Direct API calls, complex tab-based UI
4. **RatingsPage** - Direct API calls for multi-security ratings
5. **AIInsightsPage** - Chat interface, may need pattern for context
6. **HoldingsPage** - Direct API call, should use `portfolio_overview` for holdings list

### ⚠️ Missing Integration (1 page)

1. **AlertsPage** - Direct API calls, should use `macro_trend_monitor` for alert presets

---

## 🔍 PatternRenderer Component

### Location
- **File:** `full_ui.html`
- **Lines:** 3322-3408

### Props
```javascript
PatternRenderer({
  pattern: 'portfolio_overview',  // Pattern name (required)
  inputs: { portfolio_id: '...' }, // Pattern inputs (optional, defaults to {})
  config: {},                      // Additional config (optional)
  onDataLoaded: (data) => {...}    // Callback when data loads (optional)
})
```

### How It Works

1. **Executes Pattern:**
   ```javascript
   const result = await apiClient.executePattern(pattern, finalInputs);
   ```

2. **Extracts Panels:**
   ```javascript
   const metadata = patternRegistry[pattern];
   const panels = metadata.display.panels || [];
   ```

3. **Renders Panels:**
   ```javascript
   panels.map(panel => 
     e(PanelRenderer, {
       key: panel.id,
       panel: panel,
       data: getDataByPath(data, panel.dataPath),
       fullData: data
     })
   )
   ```

4. **Calls Callback:**
   ```javascript
   if (onDataLoaded) {
     onDataLoaded(result.data || result);
   }
   ```

### Data Flow

```
PatternRenderer
  ↓
apiClient.executePattern(pattern, inputs)
  ↓
POST /api/patterns/execute
  ↓
PatternOrchestrator.run_pattern()
  ↓
Returns: { success: true, data: {...}, trace: {...} }
  ↓
PatternRenderer extracts panels from patternRegistry
  ↓
PanelRenderer renders each panel using getDataByPath()
```

---

## 📋 Pattern Registry Structure

### Location
- **File:** `full_ui.html`
- **Lines:** 2832-3245

### Structure
```javascript
const patternRegistry = {
  pattern_name: {
    category: 'portfolio',
    name: 'Pattern Name',
    description: 'Pattern description',
    icon: '📊',
    display: {
      panels: [
        {
          id: 'panel_id',
          title: 'Panel Title',
          type: 'metrics_grid',  // or 'table', 'line_chart', 'pie_chart', etc.
          dataPath: 'data.path.to.field',
          config: {
            // Panel-specific configuration
          }
        }
      ]
    }
  }
}
```

### Available Panel Types

1. `metrics_grid` - Grid of metric cards
2. `table` - Data table
3. `line_chart` - Line chart (Chart.js)
4. `pie_chart` - Pie chart (Chart.js)
5. `donut_chart` - Donut chart (Chart.js)
6. `bar_chart` - Bar chart (Chart.js)
7. `news_list` - News items list
8. `action_cards` - Action buttons/cards
9. `dual_list` - Two-column list (urgent/informational)
10. `scorecard` - Scorecard display
11. `cycle_card` - Cycle phase card
12. `report_viewer` - Report viewer

---

## 🎯 Migration Patterns

### Pattern 1: Simple Replacement

**Before:**
```javascript
function MyPage() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    apiClient.executePattern('pattern_name', { portfolio_id: portfolioId })
      .then(result => setData(result.data));
  }, []);
  
  return e('div', null, /* custom rendering */);
}
```

**After:**
```javascript
function MyPage() {
  const { portfolioId } = useUserContext();
  
  return e('div', { className: 'my-page' },
    e(PatternRenderer, {
      pattern: 'pattern_name',
      inputs: { portfolio_id: portfolioId }
    })
  );
}
```

### Pattern 2: Hidden PatternRenderer (Extract Data)

**Before:**
```javascript
function MyPage() {
  const [data, setData] = useState(null);
  
  return e('div', null,
    e(PatternRenderer, {
      pattern: 'pattern_name',
      inputs: { portfolio_id: portfolioId },
      onDataLoaded: (data) => setData(data),
      style: { display: 'none' }  // Hidden!
    }),
    /* custom rendering using data */
  );
}
```

**After:**
```javascript
function MyPage() {
  const { portfolioId } = useUserContext();
  
  return e('div', { className: 'my-page' },
    e(PatternRenderer, {
      pattern: 'pattern_name',
      inputs: { portfolio_id: portfolioId }
      // Show panels directly, no hidden rendering
    })
  );
}
```

### Pattern 3: PatternRenderer + Custom Controls

**Before:**
```javascript
function MyPage() {
  const [selectedOption, setSelectedOption] = useState('option1');
  const [data, setData] = useState(null);
  
  useEffect(() => {
    apiClient.executePattern('pattern_name', {
      portfolio_id: portfolioId,
      option: selectedOption
    }).then(result => setData(result.data));
  }, [selectedOption]);
  
  return e('div', null,
    e('select', { onChange: (e) => setSelectedOption(e.target.value) }, /* options */),
    /* custom rendering */
  );
}
```

**After:**
```javascript
function MyPage() {
  const [selectedOption, setSelectedOption] = useState('option1');
  const { portfolioId } = useUserContext();
  
  return e('div', { className: 'my-page' },
    e('div', { className: 'controls' },
      e('select', {
        value: selectedOption,
        onChange: (e) => setSelectedOption(e.target.value)
      }, /* options */)
    ),
    e(PatternRenderer, {
      pattern: 'pattern_name',
      inputs: {
        portfolio_id: portfolioId,
        option: selectedOption
      }
    })
  );
}
```

---

## 📋 Specific Page Context

### PerformancePage ✅ **ALREADY MIGRATED**

**Current State:**
- ✅ Uses PatternRenderer with `portfolio_overview`
- ⚠️ Legacy function `PerformancePageLegacy` exists (should be removed)

**Action Required:**
- Remove `PerformancePageLegacy` function (lines 8578-8649)

---

### HoldingsPage ⚠️ **NEEDS MIGRATION**

**Current State:**
- Direct API call to `apiClient.getHoldings()`
- Shows all holdings in a table

**Target:**
- Use `portfolio_overview` pattern
- Use `holdings_table` panel from registry (dataPath: `valued_positions.positions`)

**Why `portfolio_overview` not `holding_deep_dive`:**
- `holding_deep_dive` requires `security_id` (single security)
- HoldingsPage shows all holdings (portfolio-level)
- `portfolio_overview` provides `valued_positions.positions` (all holdings)

**Action Required:**
- Replace `apiClient.getHoldings()` with PatternRenderer
- Use `portfolio_overview` pattern
- Show `holdings_table` panel

---

### AttributionPage ⚠️ **NEEDS REFACTORING**

**Current State:**
- Hidden PatternRenderer with `portfolio_overview`
- Extracts `currency_attr` via `onDataLoaded` callback
- Custom rendering of currency attribution

**Target:**
- Show PatternRenderer panels directly
- Use `currency_attr` panel from registry (dataPath: `currency_attr`)

**Action Required:**
- Remove hidden PatternRenderer
- Show PatternRenderer panels directly
- Remove custom currency attribution rendering

---

### MacroCyclesPage ⚠️ **COMPLEX MIGRATION**

**Current State:**
- Direct API calls to `macro_cycles_overview` and `macro_trend_monitor`
- Complex tab-based UI with 4 tabs
- Custom chart rendering

**Target:**
- Use PatternRenderer with custom controls for tab switching
- Use `macro_cycles_overview` pattern for cycle tabs
- Use `macro_trend_monitor` pattern for trend tab

**Action Required:**
- Replace direct API calls with PatternRenderer
- Keep tab switching UI
- Use PatternRenderer conditionally based on selected tab

---

### RatingsPage ⚠️ **COMPLEX CASE**

**Current State:**
- Fetches holdings first
- Then fetches ratings for each security using `executePattern('buffett_checklist')`
- Shows ratings for all holdings in a table

**Challenge:**
- `buffett_checklist` pattern requires single `security_id`
- Page shows ratings for all holdings (multi-security)

**Options:**
1. Keep current implementation (works, but inconsistent)
2. Use PatternRenderer for detailed view only (when clicking a security)
3. Create new pattern for multi-security ratings (future work)

**Action Required:**
- Evaluate and document decision
- If keeping current: Document why
- If using PatternRenderer: Use for detail view only

---

### AIInsightsPage ⚠️ **HYBRID APPROACH**

**Current State:**
- Chat interface using `apiClient.aiChat()`
- Direct API call to `/api/ai/chat` endpoint

**Target:**
- Use PatternRenderer with `news_impact_analysis` pattern for context
- Keep chat interface for user interaction

**Action Required:**
- Add PatternRenderer for news impact data
- Keep chat interface
- Use pattern data as context for chat

---

### AlertsPage ⚠️ **NEEDS INTEGRATION**

**Current State:**
- Direct API calls to `/api/alerts/*`
- Alert management UI

**Target:**
- Use PatternRenderer with `macro_trend_monitor` pattern for alert presets
- Keep alert management UI

**Action Required:**
- Add PatternRenderer for alert suggestions
- Use `alert_suggestions` panel from registry
- Keep existing alert management UI

---

## 🎯 Execution Priority

### Phase 1: Quick Wins (Week 1)

1. **Remove PerformancePageLegacy** (30 minutes)
   - Simple cleanup
   - No risk

2. **HoldingsPage Migration** (2-3 hours)
   - Simple replacement
   - Use `portfolio_overview` pattern
   - Use `holdings_table` panel

3. **AttributionPage Refactoring** (2-3 hours)
   - Remove hidden PatternRenderer
   - Show panels directly
   - Remove custom rendering

---

### Phase 2: Complex Migrations (Week 2)

4. **MacroCyclesPage Migration** (3-4 hours)
   - Replace direct API calls
   - Keep tab switching
   - Use PatternRenderer conditionally

5. **AIInsightsPage Integration** (3-4 hours)
   - Add PatternRenderer for context
   - Keep chat interface
   - Use pattern data

6. **AlertsPage Integration** (2-3 hours)
   - Add PatternRenderer for presets
   - Keep alert management UI
   - Use `alert_suggestions` panel

---

### Phase 3: Evaluation (Week 3)

7. **RatingsPage Assessment** (1-2 hours)
   - Evaluate options
   - Document decision
   - Implement if feasible

---

## ✅ Validation Checklist

### Before Migration
- [ ] Verify pattern exists in backend
- [ ] Verify pattern registered in UI registry
- [ ] Verify panel configurations exist
- [ ] Verify dataPath mappings correct

### During Migration
- [ ] Replace direct API calls with PatternRenderer
- [ ] Remove custom data processing (use panels)
- [ ] Keep custom UI controls if needed
- [ ] Test data extraction with `getDataByPath()`

### After Migration
- [ ] Test page loads correctly
- [ ] Test data displays correctly
- [ ] Test error handling
- [ ] Test loading states
- [ ] Verify no console errors

---

## 📊 Success Criteria

### Phase 1 Complete
- ✅ PerformancePageLegacy removed
- ✅ HoldingsPage uses PatternRenderer
- ✅ AttributionPage shows panels directly

### Phase 2 Complete
- ✅ MacroCyclesPage uses PatternRenderer
- ✅ AIInsightsPage uses PatternRenderer
- ✅ AlertsPage uses PatternRenderer

### Phase 3 Complete
- ✅ RatingsPage evaluated and decision documented

---

## 🚀 Ready to Execute

**Status:** ✅ **READY TO BEGIN**

**Next Steps:**
1. Remove PerformancePageLegacy
2. Start with HoldingsPage migration
3. Continue with AttributionPage
4. Move to complex pages

---

**Last Updated:** November 4, 2025  
**Status:** ✅ **CONTEXT GATHERED - READY TO EXECUTE**

