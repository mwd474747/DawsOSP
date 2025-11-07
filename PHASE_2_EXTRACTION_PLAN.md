# Phase 2: UI Monolith Refactoring - Extraction Plan

**Status**: READY TO EXECUTE
**Phase**: Context and Pattern System Extraction
**Estimated Time**: 2-3 hours
**Target Reduction**: 1,300+ lines

---

## Current State

**full_ui.html**: 3,332 lines (181 KB)
**Status**: Phase 1 complete, ready for Phase 2

### What Remains (Analysis)

**Context System (~500 lines)**:
- getCurrentPortfolioId() - Line 112 (~20 lines)
- UserContext - Line 136 (1 line)
- UserContextProvider() - Line 139 (~145 lines)
- useUserContext() - Line 284 (~12 lines)
- PortfolioSelector() - Line 296 (~320 lines)

**Pattern System (~850 lines)**:
- getDataByPath() - Line 901 (~20 lines)
- PatternRenderer() - Line 921 (~196 lines)
- PanelRenderer() - Line 1117 (~70 lines)
- patternRegistry object - (~550 lines, complex config)
- queryKeys object - (~50 lines)
- queryHelpers functions - (~20 lines)

**Core Systems (~1,000 lines)**:
- CacheManager - Line 2188 (~560 lines)
- ErrorHandler - Line 2747 (~146 lines)
- FormValidator - Line 2893 (~275 lines)

**Application Shell (~980 lines)**:
- navigationStructure array - (~400 lines)
- App component - Line 3168 (~580 lines)
- ReactDOM.render - (~1 line)

---

## Phase 2 Extraction Strategy

### 2.1: Extract Context System

**Target File**: `frontend/context.js` (~500 lines)

**Extract**:
1. getCurrentPortfolioId()
2. UserContext
3. UserContextProvider()
4. useUserContext()
5. PortfolioSelector()

**Expose via**: `DawsOS.Context`
```javascript
DawsOS.Context = {
    getCurrentPortfolioId,
    UserContext,
    UserContextProvider,
    useUserContext,
    PortfolioSelector
};
```

**Dependencies**:
- React (useState, useEffect, useCallback)
- TokenManager (from api-client.js)
- apiClient (from api-client.js)
- CacheManager (stays in full_ui.html for now)

**Risk**: MEDIUM (has dependencies on CacheManager and apiClient)
**Mitigation**: Load context.js after api-client.js

---

### 2.2: Extract Pattern System

**Target File**: `frontend/pattern-system.js` (~850 lines)

**Extract**:
1. getDataByPath()
2. PatternRenderer()
3. PanelRenderer()
4. patternRegistry object
5. queryKeys object
6. queryHelpers functions

**Expose via**: `DawsOS.PatternSystem`
```javascript
DawsOS.PatternSystem = {
    getDataByPath,
    PatternRenderer,
    PanelRenderer,
    patternRegistry,
    queryKeys,
    queryHelpers
};
```

**Dependencies**:
- React (useState, useEffect)
- DawsOS.Utils (formatValue, LoadingSpinner, ErrorMessage)
- DawsOS.Panels (all panel components)
- DawsOS.Context (useUserContext, getCurrentPortfolioId)
- apiClient (from api-client.js)
- CacheManager (stays in full_ui.html for now)
- ErrorHandler (stays in full_ui.html for now)

**Risk**: HIGH (many dependencies, complex system)
**Mitigation**: Load pattern-system.js AFTER utils.js, panels.js, and context.js

---

### 2.3: Decide on Core Systems

**Option A**: Leave in full_ui.html (RECOMMENDED)
- CacheManager, ErrorHandler, FormValidator stay in full_ui.html
- Reason: Too many dependencies, used everywhere
- Would require circular dependency handling

**Option B**: Extract to separate modules (NOT RECOMMENDED)
- Would require complex dependency injection
- High risk of breaking changes

**Decision**: Keep CacheManager, ErrorHandler, FormValidator in full_ui.html

---

## Phase 2 Execution Plan

### Step 1: Extract Context System
1. Create `frontend/context.js`
2. Extract all context-related functions
3. Add script tag in full_ui.html (after api-client.js)
4. Add import statements in full_ui.html
5. Remove extracted code from full_ui.html
6. Test: Verify portfolio context works

**Expected Reduction**: ~500 lines

### Step 2: Extract Pattern System
1. Create `frontend/pattern-system.js`
2. Extract pattern-related functions and data
3. Add script tag in full_ui.html (after context.js)
4. Add import statements in full_ui.html
5. Remove extracted code from full_ui.html
6. Test: Verify pattern rendering works

**Expected Reduction**: ~850 lines

### Step 3: Final Cleanup
1. Review remaining code
2. Clean up comments
3. Verify all imports
4. Test full application

**Final Target**: ~1,500-1,800 lines remaining

---

## Expected Results

### Before Phase 2
- full_ui.html: 3,332 lines (181 KB)

### After Phase 2
- full_ui.html: ~1,500-1,800 lines (~90 KB)
- frontend/context.js: ~500 lines (NEW)
- frontend/pattern-system.js: ~850 lines (NEW)

### Total Reduction
- Lines removed: ~1,350-1,800 lines
- Percentage reduction: ~45-54% from Phase 2 start
- **Total from original**: ~87-85% reduction (12,021 → 1,500-1,800)

---

## Load Order (After Phase 2)

```
1. React/ReactDOM (CDN)
2. Axios (CDN)
3. Chart.js (CDN)
4. frontend/api-client.js (386 lines)
5. frontend/utils.js (571 lines)
6. frontend/panels.js (907 lines)
7. frontend/context.js (500 lines) ← NEW Phase 2
8. frontend/pattern-system.js (850 lines) ← NEW Phase 2
9. frontend/pages.js (4,553 lines)
10. Inline script (full_ui.html - 1,500-1,800 lines)
```

---

## What Will Remain in full_ui.html

**Core Systems** (~1,000 lines):
- CacheManager
- ErrorHandler
- FormValidator

**Application Shell** (~500-800 lines):
- navigationStructure
- App component
- ReactDOM.render

**React Setup** (~50 lines):
- React initialization
- Import statements

---

## Risk Assessment

### Risk 1: Circular Dependencies
**Risk Level**: MEDIUM
**Mitigation**: Careful load order, explicit dependencies documented

### Risk 2: Context Breaking
**Risk Level**: MEDIUM
**Mitigation**: Test portfolio switching after extraction

### Risk 3: Pattern Rendering Breaking
**Risk Level**: HIGH
**Mitigation**: Test all pattern types after extraction

---

## Testing Checklist

**After Context Extraction**:
- [ ] Portfolio selector works
- [ ] Portfolio switching works
- [ ] User context available in all components
- [ ] No console errors

**After Pattern System Extraction**:
- [ ] All patterns render correctly
- [ ] Data loading works for all patterns
- [ ] Panel rendering works
- [ ] No console errors

**After Phase 2 Complete**:
- [ ] Full app loads without errors
- [ ] All pages navigate correctly
- [ ] All data loads correctly
- [ ] Pattern orchestration works
- [ ] Dashboard renders all patterns

---

## Rollback Plan

If issues arise:
```bash
git log --oneline -5  # Find commit before Phase 2
git revert <commit-hash>  # Revert Phase 2 changes
```

---

**Status**: Ready to execute Phase 2.1 (Context Extraction)
**Next Step**: Extract context system to frontend/context.js
