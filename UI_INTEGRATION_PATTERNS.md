# UI Integration Patterns Reference

**Date:** November 4, 2025  
**Status:** ✅ **REFERENCE GUIDE**  
**Purpose:** Document proper integration patterns for remaining UI integration work

---

## 📋 Integration Patterns

### Pattern 1: Simple Panel Display

**Use Case:** Pages that can use PatternRenderer panels directly

**Example:** HoldingsPage, AttributionPage

**Implementation:**
```javascript
function MyPage() {
    const { portfolioId } = useUserContext();
    
    return e('div', { className: 'my-page' },
        e('div', { className: 'page-header' },
            e('h1', { className: 'page-title' }, 'Page Title'),
            e('p', { className: 'page-description' }, 'Description')
        ),
        e(PatternRenderer, {
            pattern: 'portfolio_overview',
            inputs: { portfolio_id: portfolioId },
            config: {
                showPanels: ['holdings_table'] // Show specific panels
            }
        })
    );
}
```

**Key Points:**
- No loading state management needed (PatternRenderer handles it)
- No error handling needed (PatternRenderer handles it)
- Simple and clean
- Use when panels from pattern registry are sufficient

---

### Pattern 2: Hidden PatternRenderer with Custom Rendering

**Use Case:** Pages that need pattern data but use custom rendering

**Example:** MacroCyclesPage, OptimizerPage, ReportsPage

**Implementation:**
```javascript
function MyPage() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);
    
    // Timeout protection - prevent stuck loading state
    useEffect(() => {
        if (loading) {
            const timeout = setTimeout(() => {
                console.warn('Page: Pattern loading timeout, using fallback');
                setLoading(false);
                setError('Data loading timed out. Using fallback data.');
                // Use fallback data
                setData(getFallbackData());
            }, 30000); // 30 second timeout
            
            return () => clearTimeout(timeout);
        }
    }, [loading]);
    
    // Data handler
    const handleDataLoaded = (data) => {
        try {
            // Always check for error first
            if (data?.error) {
                console.error('Page: Pattern execution failed:', data.error);
                setError(data.error);
                setLoading(false);
                // Use fallback data
                setData(getFallbackData());
                return;
            }
            
            // Handle multiple nested structures
            let result = data;
            if (data?.data) {
                result = data.data;
            } else if (data?.result) {
                result = data.result;
            } else if (data?.result?.data) {
                result = data.result.data;
            }
            
            // Validate and normalize data structure
            if (result && /* validation */) {
                // Normalize data if needed
                const normalizedData = normalizeData(result);
                setData(normalizedData);
                setError(null);
            } else {
                console.warn('Page: Unexpected data structure:', result);
                setError('Invalid data structure');
                setData(getFallbackData());
            }
            
            setLoading(false); // ALWAYS clear loading
        } catch (err) {
            console.error('Page: Error processing data:', err);
            setError(err.message);
            setData(getFallbackData());
            setLoading(false);
        }
    };
    
    if (loading) {
        return e('div', { className: 'loading' }, e('div', { className: 'spinner' }));
    }
    
    if (error) {
        return e('div', { className: 'error-message' },
            e('p', null, error),
            e('button', { onClick: () => window.location.reload() }, 'Retry')
        );
    }
    
    return e('div', { className: 'my-page' },
        e('div', { className: 'page-header' },
            e('h1', { className: 'page-title' }, 'Page Title')
        ),
        
        // Hidden PatternRenderer for data fetching
        e(PatternRenderer, {
            pattern: 'pattern_name',
            inputs: { /* pattern inputs */ },
            config: {
                showPanels: [], // Hide panels, we use custom rendering
                hidden: true   // Return null when hidden
            },
            onDataLoaded: handleDataLoaded // Required callback
        }),
        
        // Custom rendering using data
        data && renderCustomUI(data)
    );
}
```

**Key Points:**
- Always add timeout protection (30 seconds)
- Always check for error first in `handleDataLoaded`
- Handle multiple nested data structures
- Always clear loading state (even on error)
- Use fallback data on error to keep page functional
- Use `config.hidden: true` to avoid rendering

---

### Pattern 3: Hybrid (Panel Display + Custom Processing)

**Use Case:** Pages that show some panels directly but also need custom processing

**Example:** HoldingsPage (with summary stats), PerformancePage

**Implementation:**
```javascript
function MyPage() {
    const { portfolioId } = useUserContext();
    const [customData, setCustomData] = useState(null);
    
    // Extract custom data from pattern result
    const handleDataLoaded = (data) => {
        try {
            if (data?.error) {
                console.error('Page: Pattern execution failed:', data.error);
                return; // PatternRenderer will show error
            }
            
            // Extract custom data for custom rendering
            const result = data?.data || data;
            if (result && result.custom_field) {
                setCustomData(result.custom_field);
            }
        } catch (err) {
            console.error('Page: Error processing data:', err);
            // Don't set error - let PatternRenderer handle it
        }
    };
    
    return e('div', { className: 'my-page' },
        e('div', { className: 'page-header' },
            e('h1', { className: 'page-title' }, 'Page Title')
        ),
        
        // Custom rendering using customData
        customData && renderCustomSummary(customData),
        
        // PatternRenderer shows panels directly
        e(PatternRenderer, {
            pattern: 'portfolio_overview',
            inputs: { portfolio_id: portfolioId },
            config: {
                showPanels: ['holdings_table'], // Show specific panels
                onDataLoaded: handleDataLoaded  // Extract custom data
            }
        })
    );
}
```

**Key Points:**
- PatternRenderer shows panels directly
- `onDataLoaded` extracts custom data for custom rendering
- No loading state management (PatternRenderer handles it)
- No error handling (PatternRenderer handles it)
- Use when you need both panels and custom processing

---

## 🔧 Common Patterns

### Data Extraction Pattern

**Always handle multiple nested structures:**
```javascript
let result = data;
if (data?.data) {
    result = data.data;
} else if (data?.result) {
    result = data.result;
} else if (data?.result?.data) {
    result = data.result.data;
}
```

### Error Handling Pattern

**Always check for error first:**
```javascript
if (data?.error) {
    console.error('Pattern execution failed:', data.error);
    setError(data.error);
    setLoading(false);
    // Use fallback data
    return;
}
```

### Timeout Protection Pattern

**Always add timeout to prevent stuck loading:**
```javascript
useEffect(() => {
    if (loading) {
        const timeout = setTimeout(() => {
            console.warn('Pattern loading timeout, using fallback');
            setLoading(false);
            setError('Data loading timed out');
            setData(getFallbackData());
        }, 30000); // 30 second timeout
        
        return () => clearTimeout(timeout);
    }
}, [loading]);
```

### Data Validation Pattern

**Always validate data structure:**
```javascript
// Check for expected fields
const hasExpectedData = result && (
    result.field1 || result.field2 || result.field3
);

if (hasExpectedData) {
    // Normalize data structure
    const normalizedData = {
        field1: result.field1 || {},
        field2: result.field2 || {},
        field3: result.field3 || {}
    };
    setData(normalizedData);
} else {
    console.warn('Unexpected data structure:', result);
    setError('Invalid data structure');
    setData(getFallbackData());
}
```

---

## 🚨 Common Issues & Fixes

### Issue 1: Stuck Loading State

**Problem:** Page stuck in loading state forever

**Root Cause:**
- `onDataLoaded` callback never called
- Pattern execution fails silently
- Error handling doesn't clear loading state

**Fix:**
- Add timeout protection (30 seconds)
- Always clear loading state in error handler
- Ensure `onDataLoaded` is always called (even on error)

### Issue 2: Authentication Blocking

**Problem:** Pattern execution blocked by authentication check

**Root Cause:**
- PatternRenderer checks for token before executing
- Some patterns don't require authentication
- Backend should handle authentication

**Fix:**
- Don't block execution in PatternRenderer
- Let backend handle authentication
- Backend will return appropriate error if auth required

### Issue 3: Data Structure Mismatch

**Problem:** Data structure doesn't match expectations

**Root Cause:**
- Pattern returns nested structure
- Data extraction too strict
- Pattern output structure changed

**Fix:**
- Handle multiple nested structures
- More flexible data extraction
- Normalize data structure

### Issue 4: Hidden PatternRenderer Still Renders

**Problem:** Hidden PatternRenderer still renders loading/error states

**Root Cause:**
- Using `style: { display: 'none' }` instead of `config.hidden: true`
- PatternRenderer doesn't check for hidden flag

**Fix:**
- Use `config.hidden: true` instead of `style: { display: 'none' }`
- PatternRenderer returns `null` when hidden

---

## 📋 Remaining Pages Integration Guide

### 1. AttributionPage

**Current:** Hidden PatternRenderer with custom rendering  
**Target:** Pattern 1 (Simple Panel Display)

**Changes:**
- Remove hidden PatternRenderer
- Show PatternRenderer panels directly
- Use `currency_attr` panel from registry

### 2. RatingsPage

**Current:** Direct API call  
**Target:** Pattern 2 (Hidden PatternRenderer with Custom Rendering)

**Changes:**
- Replace direct API call with hidden PatternRenderer
- Use `buffett_checklist` pattern
- Keep custom rendering
- Add timeout protection

### 3. AIInsightsPage

**Current:** Chat interface  
**Target:** Pattern 3 (Hybrid) or Pattern 1

**Changes:**
- Add PatternRenderer for context
- Use `portfolio_overview` or `news_impact_analysis` pattern
- Keep chat interface

### 4. AlertsPage

**Current:** Direct API calls  
**Target:** Pattern 3 (Hybrid)

**Changes:**
- Add PatternRenderer for alert suggestions
- Use `macro_trend_monitor` pattern
- Show `alert_suggestions` panel
- Keep custom alert management UI

---

## ✅ Checklist for Integration

### Before Integration
- [ ] Understand page requirements
- [ ] Identify which pattern to use
- [ ] Check pattern data structure
- [ ] Plan data extraction/normalization

### During Integration
- [ ] Add PatternRenderer (hidden or visible)
- [ ] Add `onDataLoaded` callback (if needed)
- [ ] Add timeout protection (if Pattern 2)
- [ ] Add error handling
- [ ] Add data validation
- [ ] Add fallback data

### After Integration
- [ ] Test loading state
- [ ] Test error handling
- [ ] Test timeout protection
- [ ] Test data extraction
- [ ] Test fallback data
- [ ] Test all UI elements
- [ ] Check console for errors

---

**Last Updated:** November 4, 2025  
**Status:** ✅ **REFERENCE GUIDE COMPLETE**

