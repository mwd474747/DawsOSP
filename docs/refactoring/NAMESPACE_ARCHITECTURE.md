# Namespace Architecture - Post-Refactoring

**Date:** January 15, 2025  
**Purpose:** Document the namespace architecture established in November 2025 refactoring

---

## Namespace Hierarchy

### Structure

```
DawsOS
├── Core.*              # Infrastructure layer
│   ├── API.*           # API client, TokenManager
│   ├── Auth.*          # Authentication utilities
│   ├── Cache.*         # Cache management
│   └── Errors.*        # Error handling
├── Patterns.*          # Pattern system (PRIME NAMESPACE)
│   ├── Renderer.*      # PatternRenderer component
│   ├── Registry.*      # Pattern registry
│   └── Helpers.*       # Pattern utilities
├── UI.*                # Presentation layer
│   └── Primitives.*    # UI components (moved from Utils)
└── Utils.*             # Cross-cutting utilities
    ├── Formatting.*    # Formatting functions
    ├── Hooks.*         # React hooks
    └── Data.*          # Data utilities
```

---

## Namespace Principles

### 1. Domain Boundaries
- **Core.*** - Infrastructure (API, Auth, Cache, Errors)
- **Patterns.*** - Core business abstraction (prime namespace)
- **UI.*** - Presentation layer
- **Utils.*** - Cross-cutting utilities

### 2. Logical Grouping
- Related functionality grouped together
- Clear hierarchy reflects importance
- Easy to discover functionality

### 3. No Global Pollution
- All exports under `DawsOS.*` namespace
- Zero global namespace pollution
- Deprecation aliases guide migration

---

## Module Exports

### Core Modules

**api-client.js:**
```javascript
DawsOS.Core.API = {
  apiClient: {...},
  TokenManager: {...}
}
```

**error-handler.js:**
```javascript
DawsOS.Core.Errors = {
  ErrorHandler: {...},
  handleApiError: {...}
}
```

**cache-manager.js:**
```javascript
DawsOS.Core.Cache = {
  CacheManager: {...}
}
```

**context.js:**
```javascript
DawsOS.Core.Auth = {
  getCurrentPortfolioId: {...}
}

DawsOS.Context = {
  UserContext: {...},
  UserContextProvider: {...},
  useUserContext: {...},
  PortfolioSelector: {...}
}
```

### Pattern System

**pattern-system.js:**
```javascript
DawsOS.Patterns = {
  PatternRenderer: {...},
  PanelRenderer: {...},
  patternRegistry: {...},
  queryKeys: {...},
  queryHelpers: {...}
}
```

### UI Components

**panels.js:**
```javascript
DawsOS.UI.Primitives = {
  MetricsGridPanel: {...},
  TablePanel: {...},
  LineChartPanel: {...},
  // ... 13 panel components
}
```

**utils.js:**
```javascript
DawsOS.Utils.Formatting = {
  formatValue: {...},
  formatPercentage: {...},
  formatCurrency: {...},
  // ... formatting functions
}

DawsOS.Utils.Hooks = {
  usePortfolioData: {...},
  // ... React hooks
}

DawsOS.Utils.Data = {
  getDataSourceFromResponse: {...},
  // ... data utilities
}
```

---

## Backward Compatibility

### Deprecation Strategy

All refactored modules maintain **100% backward compatibility** via:

1. **New namespaces** (correct structure)
2. **Old namespaces** (deprecated but functional)
3. **Deprecation warnings** (console.warn guides migration)

### Example

```javascript
// OLD WAY (still works, shows deprecation warning)
const client = global.apiClient;
// Console: "[DEPRECATED] global.apiClient is deprecated. Use DawsOS.Core.API instead."

// NEW WAY (correct)
const client = DawsOS.Core.API.apiClient;
```

---

## Migration Status

### Completed
- ✅ All modules refactored to use `DawsOS.*` namespace
- ✅ Deprecation aliases in place
- ✅ Zero global namespace pollution
- ✅ Logical grouping established

### In Progress
- ⏳ Updating all references to use new namespaces
- ⏳ Removing deprecation aliases (after migration complete)

---

## Namespace Issues Addressed

### Problem 1: Global Namespace Pollution
**Before:**
```javascript
global.apiClient = {...};
global.TokenManager = {...};
global.LoadingSpinner = {...};
// ... 17+ global exports
```

**After:**
```javascript
DawsOS.Core.API.apiClient = {...};
DawsOS.Core.API.TokenManager = {...};
DawsOS.UI.Primitives.LoadingSpinner = {...};
// ... all under DawsOS.* namespace
```

### Problem 2: Duplicate Exports
**Before:**
- `getCurrentPortfolioId` exported from both `api-client.js` and `context.js`
- `handleApiError` exported from both `api-client.js` and `error-handler.js`

**After:**
- Single source of truth: `DawsOS.Core.Auth.getCurrentPortfolioId`
- Single source of truth: `DawsOS.Core.Errors.handleApiError`
- Old exports deprecated with pointers to correct location

### Problem 3: Utils Junk Drawer
**Before:**
- 17 mixed exports (formatting + components + hooks + data)
- No logical grouping

**After:**
- 4 focused namespaces:
  - `DawsOS.Utils.Formatting` - Pure formatting functions
  - `DawsOS.Utils.Hooks` - React hooks
  - `DawsOS.Utils.Data` - Data utilities
  - `DawsOS.UI.Primitives` - UI components (moved out of Utils!)

---

## Pattern System Namespace

### Elevation to Prime Namespace

**Before:**
- `DawsOS.PatternSystem` (buried with other modules)

**After:**
- `DawsOS.Patterns` (prime namespace, reflects importance)
- Clear sub-organization: Renderer, Registry, Helpers

### Rationale
- Pattern system is the **primary abstraction** for business logic
- Deserves prime namespace position
- Clear hierarchy reflects architectural importance

---

## Technical Debt Removal Impact

### Namespace Cleanup
- ✅ No global namespace pollution
- ✅ Clear domain boundaries
- ✅ Logical grouping
- ✅ Easy to discover functionality

### Remaining Work
- ⏳ Remove deprecation aliases (after all references updated)
- ⏳ Update all internal references to use new namespaces
- ⏳ Document namespace conventions

---

## Key Takeaways

1. **Namespace hierarchy reflects architecture** - Core, Patterns, UI, Utils
2. **Pattern system is prime namespace** - Reflects its importance
3. **Backward compatibility maintained** - Deprecation aliases guide migration
4. **Zero global pollution** - All exports under `DawsOS.*`
5. **Clear domain boundaries** - Infrastructure vs business logic vs presentation

---

**Status:** Architecture Documented  
**Last Updated:** January 15, 2025

