# Replit Agent Testing Prompts - Phase 1 Validation

**Date:** January 14, 2025  
**Purpose:** Test Phase 1 changes (provenance warnings, pattern output extraction, UI warning banner)  
**Status:** Ready for Runtime Testing

---

## 🎯 Testing Overview

Phase 1 changes have been implemented and validated statically. Now we need runtime testing to verify:
1. Provenance warnings display correctly in UI
2. Pattern output extraction works for all formats
3. Updated patterns execute correctly
4. No regressions in existing functionality

---

## 📋 Testing Prompts for Replit Agent

### Prompt 1: Test Risk Analytics Page (Critical - User Trust Issue)

```
Test the Risk Analytics page to verify that provenance warnings are displayed correctly.

1. Start the DawsOS application if not already running
2. Navigate to the Risk Analytics page (or page that uses portfolio_cycle_risk pattern)
3. Verify that:
   - A yellow warning banner appears at the top of the page
   - The banner shows "⚠️ Data Quality Warning" title
   - The banner lists warnings about stub data
   - The banner includes: "This data is not suitable for investment decisions"
   - The Risk Analytics data still displays (charts, metrics)
   - No JavaScript errors in browser console

4. Check the browser console for:
   - "Provenance warnings detected:" log message
   - No errors related to ProvenanceWarningBanner component
   - No errors related to checkProvenance function

5. Take a screenshot of the warning banner if it displays correctly
6. Report any issues or errors found
```

---

### Prompt 2: Test Pattern Output Extraction

```
Test that pattern output extraction works correctly for all updated patterns.

1. Execute the following patterns via API or UI:
   - portfolio_cycle_risk
   - portfolio_macro_overview
   - cycle_deleveraging_scenarios
   - macro_trend_monitor
   - holding_deep_dive
   - portfolio_scenario_analysis

2. For each pattern, verify:
   - Pattern executes without errors
   - Response includes expected outputs in `data` field
   - No "No data" errors
   - No "Output not found in state" warnings in logs
   - All step results are correctly extracted

3. Check backend logs for:
   - "Added {output_key} to outputs for pattern {pattern_id}" messages
   - No "Output {output_key} not found in state" warnings
   - No errors related to output extraction

4. Verify that patterns that previously failed (due to output format issues) now work correctly

5. Report any patterns that fail or show unexpected behavior
```

---

### Prompt 3: Test Provenance Detection in API Response

```
Test that the _provenance field is correctly included in API responses.

1. Make an API request to execute the portfolio_cycle_risk pattern:
   POST /api/patterns/execute
   Body: {
     "pattern": "portfolio_cycle_risk",
     "inputs": {
       "portfolio_id": "<valid_portfolio_id>"
     }
   }

2. Check the response JSON for:
   - `data.factor_exposures._provenance` field exists
   - `_provenance.type` equals "stub"
   - `_provenance.warnings` is an array with 3 warnings
   - `_provenance.confidence` equals 0.0
   - `_provenance.implementation_status` equals "stub"
   - `_provenance.recommendation` exists

3. Verify the response structure:
   {
     "success": true,
     "data": {
       "factor_exposures": {
         "factors": {...},
         "_provenance": {
           "type": "stub",
           "warnings": [...],
           ...
         }
       },
       ...
     },
     "trace": {...}
   }

4. Report if _provenance field is missing or incorrectly structured
```

---

### Prompt 4: Regression Testing - Existing Patterns

```
Test that existing working patterns are not affected by Phase 1 changes.

1. Test the following patterns that should NOT show warnings:
   - portfolio_overview (Dashboard)
   - corporate_actions_upcoming (Corporate Actions)
   - macro_cycles_overview (Macro Cycles)
   - portfolio_scenario_analysis (Scenarios)

2. For each pattern, verify:
   - Pattern executes without errors
   - No warning banner appears (unless they use stub data)
   - Data displays correctly
   - No JavaScript errors in console
   - No backend errors in logs

3. Specifically test:
   - Dashboard page loads and displays data
   - Holdings page loads and displays data
   - Performance page loads and displays data
   - Corporate Actions page loads (should not show warnings unless using stub data)
   - Macro Cycles page loads and displays data

4. Report any regressions or unexpected behavior
```

---

### Prompt 5: Test UI Component Integration

```
Test that the ProvenanceWarningBanner component works correctly in different scenarios.

1. Test with stub data:
   - Navigate to Risk Analytics page
   - Verify warning banner displays
   - Verify banner styling is correct (yellow background, warning icon)
   - Verify warnings are readable and formatted correctly

2. Test with real data:
   - Navigate to Dashboard or Holdings page
   - Verify NO warning banner appears
   - Verify data displays normally

3. Test with mixed data (if possible):
   - If a pattern returns both stub and real data
   - Verify warning banner appears for stub data only
   - Verify real data displays correctly

4. Test UI responsiveness:
   - Verify banner displays correctly on different screen sizes
   - Verify banner doesn't break page layout
   - Verify banner is positioned correctly (top of pattern content)

5. Check browser console for:
   - No React/JavaScript errors
   - Warning logs appear when stub data is detected
   - No errors related to component rendering

6. Report any UI issues or styling problems
```

---

### Prompt 6: Test Pattern Execution Logs

```
Check backend logs to verify pattern execution and output extraction.

1. Start the application with logging enabled
2. Execute the portfolio_cycle_risk pattern
3. Check logs for:
   - "Executing pattern: portfolio_cycle_risk"
   - "Added {output_key} to outputs for pattern portfolio_cycle_risk" messages
   - No "Output not found in state" warnings
   - No errors related to output extraction

4. Execute each of the 6 updated patterns and verify:
   - All patterns execute successfully
   - Output extraction works correctly
   - No missing output warnings

5. Check for any errors or warnings related to:
   - Pattern loading
   - Step execution
   - Output extraction
   - Provenance handling

6. Report any errors or warnings found in logs
```

---

### Prompt 7: Test Error Handling

```
Test error handling for edge cases and invalid inputs.

1. Test with invalid pattern ID:
   - Try to execute a non-existent pattern
   - Verify appropriate error message is returned
   - Verify no warning banner appears

2. Test with missing portfolio_id:
   - Try to execute portfolio_cycle_risk without portfolio_id
   - Verify appropriate error message is returned
   - Verify no warning banner appears

3. Test with invalid portfolio_id:
   - Try to execute with invalid UUID
   - Verify appropriate error message is returned
   - Verify no warning banner appears

4. Test pattern execution failure:
   - If possible, simulate a pattern execution failure
   - Verify error is displayed correctly
   - Verify warning banner doesn't appear on errors

5. Report any error handling issues
```

---

### Prompt 8: Performance Testing

```
Test that Phase 1 changes don't impact performance.

1. Measure pattern execution time:
   - Execute portfolio_cycle_risk pattern
   - Measure execution time before and after changes (if possible)
   - Verify no significant performance degradation

2. Measure UI rendering time:
   - Navigate to Risk Analytics page
   - Measure time to first render
   - Measure time to display warning banner
   - Verify no significant performance impact

3. Check for:
   - Memory leaks (if possible)
   - Excessive re-renders
   - Slow recursive checks (checkProvenance function)

4. Report any performance issues
```

---

## 📊 Expected Results

### Risk Analytics Page:
- ✅ Yellow warning banner displays at top
- ✅ Warning banner shows stub data warnings
- ✅ Risk Analytics data still displays
- ✅ No JavaScript errors

### Pattern Execution:
- ✅ All 6 updated patterns execute successfully
- ✅ No "No data" errors
- ✅ No "Output not found" warnings
- ✅ Outputs correctly extracted from state

### API Response:
- ✅ `_provenance` field included in factor_exposures
- ✅ `_provenance.type` equals "stub"
- ✅ Warnings array contains 3 warnings

### Regression Testing:
- ✅ Existing patterns work correctly
- ✅ No warning banners on pages without stub data
- ✅ No JavaScript errors
- ✅ No backend errors

---

## 🐛 Known Issues to Check

1. **Warning Banner Not Displaying:**
   - Check if `checkProvenance` function is working
   - Check if `provenanceWarnings` state is being set
   - Check browser console for errors

2. **Pattern Output Extraction Issues:**
   - Check if orchestrator is handling all 3 formats
   - Check backend logs for output extraction warnings
   - Verify step results are stored correctly in state

3. **UI Styling Issues:**
   - Check if warning banner styling is correct
   - Check if banner doesn't break page layout
   - Check responsive design

---

## 📝 Reporting Template

For each test, report:

1. **Test Name:** [Test name]
2. **Status:** ✅ PASS / ⚠️ WARN / ❌ FAIL
3. **Details:** [What was tested and results]
4. **Screenshots:** [If applicable]
5. **Logs:** [Relevant log entries]
6. **Issues Found:** [Any issues or errors]
7. **Recommendations:** [Any recommendations]

---

## 🎯 Priority Testing Order

1. **High Priority:**
   - Prompt 1: Risk Analytics Page (Critical user trust issue)
   - Prompt 2: Pattern Output Extraction (Core functionality)
   - Prompt 3: Provenance Detection (API response)

2. **Medium Priority:**
   - Prompt 4: Regression Testing (Ensure no breaking changes)
   - Prompt 5: UI Component Integration (User experience)

3. **Low Priority:**
   - Prompt 6: Pattern Execution Logs (Debugging)
   - Prompt 7: Error Handling (Edge cases)
   - Prompt 8: Performance Testing (Optimization)

---

## ✅ Success Criteria

Phase 1 is successful if:
- ✅ Risk Analytics page shows warning banner
- ✅ All 6 updated patterns execute correctly
- ✅ No regressions in existing functionality
- ✅ No JavaScript errors in console
- ✅ No backend errors in logs
- ✅ API responses include _provenance field correctly

---

**Ready for Testing:** Yes  
**Estimated Time:** 2-3 hours  
**Priority:** High (Critical user trust issue)

