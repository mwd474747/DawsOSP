# Frontend Module Load Order

**Date**: 2025-11-08
**Purpose**: Document required module load order for DawsOS frontend
**Context**: Phase -1.4 of UNIFIED_REFACTOR_PLAN_V2.md

---

## Critical: Module Load Order Matters

The DawsOS frontend uses a **hybrid architecture** with modular JavaScript loaded via `<script>` tags. Because modules use IIFE (Immediately Invoked Function Expressions) and register to global namespaces, **load order is critical**.

**Incorrect order** = `ReferenceError: X is not defined`

---

## Required Load Order (from `full_ui.html`)

### 1. Foundation Layer (Load First)

```html
<script src="frontend/version.js?v=20250115"></script>
<script src="frontend/logger.js?v=20250115"></script>
```

**Why**:
- `version.js` initializes the `DawsOS` namespace
- `logger.js` provides logging used by all other modules

**Dependencies**: None

---

### 2. Module Dependencies & Utilities

```html
<script src="frontend/module-dependencies.js?v=20250115"></script>
<script src="frontend/api-client.js?v=20250115"></script>
<script src="frontend/form-validator.js?v=20250115"></script>
<script src="frontend/error-handler.js?v=20250115"></script>
<script src="frontend/utils.js?v=20250115"></script>
```

**Why**:
- `module-dependencies.js` tracks dependency graph
- `api-client.js` provides `DawsOS.APIClient` namespace (used by pages)
- `utils.js` provides `DawsOS.Utils` namespace (used by panels and pages)
- Other utilities provide error handling and validation

**Dependencies**: Logger

---

### 3. UI Components Layer

```html
<script src="frontend/panels.js?v=20250115"></script>
```

**Why**: Panels provide UI components used by pages

**Dependencies**: Utils, Logger

**Exports**: `DawsOS.Panels.*` (MetricsGridPanel, TablePanel, LineChartPanel, etc.)

---

### 4. State Management & Context

```html
<script src="frontend/context.js?v=20250115"></script>
```

**Why**: Provides React context used by pages and pattern system

**Dependencies**: Logger, APIClient

**Exports**: `DawsOS.Context.*` (UserContextProvider, useUserContext, etc.)

---

### 5. Pattern System

```html
<script src="frontend/pattern-system.js?v=20250115"></script>
```

**Why**: Orchestrates pattern execution (used by pages)

**Dependencies**: Logger, APIClient, Utils, Context, Panels

**Exports**: `DawsOS.PatternSystem.*` (PatternRenderer, PanelRenderer, etc.)

---

### 6. Pages (Load Last)

```html
<script src="frontend/pages.js?v=20250115"></script>
```

**Why**: Pages use everything above

**Dependencies**: Logger, APIClient, Utils, Panels, Context, PatternSystem

**Exports**: `DawsOS.Pages.*` (DashboardPage, HoldingsPage, etc.)

---

### 7. Validation & Initialization

```html
<script src="frontend/namespace-validator.js?v=20250115"></script>
```

**Why**: Validates all namespaces loaded correctly

**Dependencies**: All modules above

---

## Dependency Graph

```
version.js (DawsOS namespace)
    ↓
logger.js (DawsOS.Logger)
    ↓
module-dependencies.js, api-client.js, utils.js, error-handler.js, form-validator.js
    ↓
panels.js (DawsOS.Panels) ← depends on Utils
    ↓
context.js (DawsOS.Context) ← depends on APIClient, Logger
    ↓
pattern-system.js (DawsOS.PatternSystem) ← depends on Context, Panels, Utils, APIClient
    ↓
pages.js (DawsOS.Pages) ← depends on EVERYTHING
    ↓
namespace-validator.js (validates all loaded)
```

---

## Common Errors

### Error: `ReferenceError: Utils is not defined`

**Cause**: `utils.js` not loaded before code that uses it

**Fix**: Ensure `utils.js` loads before `panels.js` or `pages.js`

### Error: `TypeError: Cannot read property 'Context' of undefined`

**Cause**: `context.js` not loaded before `pattern-system.js` or `pages.js`

**Fix**: Ensure `context.js` loads before `pattern-system.js`

### Error: `ReferenceError: formatDate is not defined`

**Cause**: Using `formatDate` directly without importing from `Utils` namespace

**Fix**: Import at top of file:
```javascript
const formatDate = Utils.formatDate || ((dateString) => dateString || '-');
```

---

## Testing Module Load Order

After any changes to `full_ui.html` `<script>` tag order:

1. **Clear browser cache** (hard refresh: Cmd+Shift+R or Ctrl+Shift+R)
2. **Open browser console** (F12)
3. **Check for errors**:
   - `ReferenceError: X is not defined` → load order issue
   - `TypeError: Cannot read property 'Y' of undefined` → namespace not loaded
4. **Verify namespaces**:
   ```javascript
   console.log(DawsOS.Logger);        // Should be object
   console.log(DawsOS.Utils);         // Should be object
   console.log(DawsOS.Panels);        // Should be object
   console.log(DawsOS.Context);       // Should be object
   console.log(DawsOS.PatternSystem); // Should be object
   console.log(DawsOS.Pages);         // Should be object
   ```

---

## Why Not Use ES6 Modules?

**Current**: IIFE + global namespaces (requires specific load order)

**Alternative**: ES6 modules with `import`/`export` (automatic dependency resolution)

**Reasons for Current Approach**:
1. No build step required (fast iteration)
2. Works in all browsers without transpilation
3. Simpler deployment (just copy files)

**Future Migration**:
- Consider Vite or Webpack for bundling
- Migrate to ES6 modules with explicit imports
- Automatic dependency resolution
- Better dev experience

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-11-07 | Initial modularization (Phase 1) |
| 1.1 | 2025-11-08 | Documented load order (Phase -1.4) |

---

**Last Updated**: 2025-11-08
**Related Docs**:
- [REFACTORING_HISTORY_FORENSICS.md](../REFACTORING_HISTORY_FORENSICS.md) - Why modularization happened
- [UNIFIED_REFACTOR_PLAN_V2.md](../UNIFIED_REFACTOR_PLAN_V2.md) - Phase -1.4
