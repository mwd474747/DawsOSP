# Namespace Normalization Plan - DawsOS Architecture

**Date**: November 7, 2025
**Status**: PLANNING (Emergency fixes complete, ready for Phase 2)
**Goal**: Normalize namespace structure to reflect pattern-driven DawsOS architecture

---

## Current State Analysis

### Current Namespace Chaos (Phase 1.1.6 Emergency State)

```javascript
// 7 different namespace patterns in use:
global.DawsOS.Utils.*              // format functions, components
global.DawsOS.Panels.*             // panel components
global.DawsOS.PatternSystem.*      // pattern rendering
global.DawsOS.Pages.*              // page components
global.DawsOS.Context.*            // React context
global.DawsOS.CacheManager         // cache singleton
global.DawsOS.FormValidator        // validation
global.DawsOS.ErrorHandler         // error handling
global.apiClient                   // ❌ WRONG - should be DawsOS.Core.API
global.TokenManager                // ❌ WRONG - should be DawsOS.Core.Auth
global.getCurrentPortfolioId       // ❌ WRONG - duplicate (exists in Context too)
global.handleApiError              // ❌ WRONG - duplicate (exists in ErrorHandler)
```

**Problems**:
- ❌ api-client.js pollutes global namespace (8 exports)
- ❌ Inconsistent pattern: 7 modules use `DawsOS.*`, 1 uses `global.*`
- ❌ No logical grouping (Utils contains both formatting AND components)
- ❌ Duplications: getCurrentPortfolioId (2×), TokenManager (conceptually), handleApiError (2×)
- ❌ No domain boundaries (Portfolio vs Macro components mixed together)

**Emergency Fixes Applied** (Phase 1.1.6):
- ✅ Added fallbacks for namespace inconsistency: `global.DawsOS.APIClient || global.apiClient`
- ✅ Fixed pages.js imports to work with current chaos
- ✅ Module validation enhanced
- ⚠️ **Status**: STABLE but architecturally incorrect

---

## Proposed Namespace Structure (Replit Version - Enhanced)

### Philosophy: Pattern-First, Domain-Aware Architecture

```javascript
window.DawsOS = {
    // ===================================================================
    // CORE INFRASTRUCTURE LAYER
    // ===================================================================
    Core: {
        API: {
            // Centralized API client (from api-client.js)
            request: function(endpoint, options) { ... },
            get: function(url, config) { ... },
            post: function(url, data, config) { ... },
            put: function(url, data, config) { ... },
            delete: function(url, config) { ... },

            // Token management (moved from global.TokenManager)
            TokenManager: {
                getToken: function() { ... },
                setToken: function(token) { ... },
                clearToken: function() { ... },
                isTokenExpired: function() { ... }
            },

            // Retry configuration
            retryConfig: {
                maxRetries: 3,
                retryDelay: 1000,
                retryableStatuses: [408, 429, 500, 502, 503, 504]
            }
        },

        Cache: {
            // Cache manager (from cache-manager.js)
            get: function(key) { ... },
            set: function(key, value, ttl) { ... },
            invalidate: function(key) { ... },
            clear: function() { ... }
        },

        Auth: {
            // Authentication utilities
            getCurrentUser: function() { ... },
            getCurrentPortfolioId: function() { ... },  // SINGLE SOURCE OF TRUTH
            login: function(credentials) { ... },
            logout: function() { ... }
        },

        Errors: {
            // Centralized error handling (from error-handler.js)
            handle: function(error, context) { ... },
            handleApiError: function(error) { ... },  // SINGLE SOURCE OF TRUTH
            show: function(message, type) { ... },
            ErrorBoundary: ReactComponent  // React error boundary
        }
    },

    // ===================================================================
    // PATTERN SYSTEM - THE HEART OF DAWSOS
    // ===================================================================
    Patterns: {
        // Pattern rendering orchestrator
        Renderer: {
            render: function(patternConfig, data) { ... },
            PatternRenderer: ReactComponent  // Main pattern renderer component
        },

        // Pattern registry and metadata
        Registry: {
            patterns: {
                portfolio_overview: { ... },
                holdings_analysis: { ... },
                macro_cycles: { ... },
                // ... all 15 patterns
            },
            get: function(patternName) { ... },
            list: function() { ... },
            validate: function(patternName, data) { ... }
        },

        // Pattern utilities and helpers
        Helpers: {
            getDataByPath: function(obj, path) { ... },
            queryKeys: { ... },
            queryHelpers: { ... },
            PanelRenderer: ReactComponent  // Panel dispatcher
        }
    },

    // ===================================================================
    // UI COMPONENT LIBRARY
    // ===================================================================
    UI: {
        // Primitive/Generic Components (domain-agnostic)
        Primitives: {
            LoadingSpinner: ReactComponent,
            ErrorMessage: ReactComponent,
            EmptyState: ReactComponent,
            RetryableError: ReactComponent,
            DataBadge: ReactComponent,
            FormField: ReactComponent,
            NetworkStatusIndicator: ReactComponent
        },

        // Panel Components (pattern-driven, domain-agnostic renderers)
        Panels: {
            MetricsGridPanel: ReactComponent,
            TablePanel: ReactComponent,
            LineChartPanel: ReactComponent,
            PieChartPanel: ReactComponent,
            DonutChartPanel: ReactComponent,
            BarChartPanel: ReactComponent,
            NewsListPanel: ReactComponent,
            ScorecardPanel: ReactComponent,
            ActionCardsPanel: ReactComponent,
            CycleCardPanel: ReactComponent,
            DualListPanel: ReactComponent,
            ReportViewerPanel: ReactComponent
        },

        // Portfolio Domain Components (business logic specific)
        Portfolio: {
            HoldingsTable: ReactComponent,
            PerformanceChart: ReactComponent,
            AttributionPanel: ReactComponent,
            TransactionHistory: ReactComponent,
            PositionDetails: ReactComponent
        },

        // Macro Domain Components (business logic specific)
        Macro: {
            RegimeIndicator: ReactComponent,
            FactorExposure: ReactComponent,
            ScenarioAnalysis: ReactComponent,
            CyclePhaseChart: ReactComponent
        },

        // Risk Domain Components
        Risk: {
            VaRCalculator: ReactComponent,
            StressTesting: ReactComponent,
            CorrelationMatrix: ReactComponent
        }
    },

    // ===================================================================
    // APPLICATION PAGES
    // ===================================================================
    Pages: {
        // Authentication
        LoginPage: ReactComponent,

        // Core Dashboard
        DashboardPage: ReactComponent,
        DashboardPageLegacy: ReactComponent,

        // Portfolio Management
        HoldingsPage: ReactComponent,
        TransactionsPage: ReactComponent,
        PerformancePage: ReactComponent,

        // Macro Analysis
        MacroCyclesPage: ReactComponent,

        // Risk & Analytics
        RiskPage: ReactComponent,
        AttributionPage: ReactComponent,
        ScenariosPage: ReactComponent,
        ScenariosPageLegacy: ReactComponent,

        // Tools
        OptimizerPage: ReactComponent,
        RatingsPage: ReactComponent,

        // AI Features
        AIInsightsPage: ReactComponent,
        AIAssistantPage: ReactComponent,

        // Operations
        AlertsPage: ReactComponent,
        ReportsPage: ReactComponent,
        CorporateActionsPage: ReactComponent,
        MarketDataPage: ReactComponent,

        // System
        SettingsPage: ReactComponent
    },

    // ===================================================================
    // SHARED UTILITIES
    // ===================================================================
    Utils: {
        // Formatting utilities (pure functions)
        Formatting: {
            currency: function(value, decimals) { ... },
            percentage: function(value, decimals) { ... },
            number: function(value, decimals) { ... },
            date: function(dateString) { ... },
            value: function(value, format) { ... },  // Generic formatter
            getColorClass: function(value, thresholds) { ... }
        },

        // Validation utilities (pure functions)
        Validation: {
            email: function(email) { ... },
            required: function(value) { ... },
            numeric: function(value, min, max) { ... },
            date: function(dateString) { ... },
            FormValidator: {  // Collection of validators
                validate: function(formData, schema) { ... },
                validateField: function(value, rules) { ... }
            }
        },

        // React hooks (stateful utilities)
        Hooks: {
            useCachedQuery: function(queryKey, queryFn, options) { ... },
            useCachedMutation: function(mutationFn, options) { ... },
            useDataProvenance: function(data) { ... }
        },

        // Data utilities
        Data: {
            getDataSourceFromResponse: function(response) { ... },
            withDataProvenance: function(Component) { ... },
            ProvenanceWarningBanner: ReactComponent
        }
    },

    // ===================================================================
    // APPLICATION CONTEXT
    // ===================================================================
    Context: {
        // User and portfolio context
        UserContext: {
            Provider: ReactComponent,
            useUserContext: ReactHook,
            getCurrentPortfolioId: function() { ... }  // DEPRECATED - use DawsOS.Core.Auth
        },

        // UI theme context
        ThemeContext: {
            Provider: ReactComponent,
            useTheme: ReactHook
        },

        // App configuration context
        ConfigContext: {
            Provider: ReactComponent,
            useConfig: ReactHook
        }
    }
};
```

---

## Why This Structure?

### 1. **Reflects Pattern-First Architecture**
- `Patterns` namespace gets prime real estate
- Pattern rendering is central, not buried in utilities
- Clear separation: Pattern system vs Panel components vs Domain components

### 2. **Domain Boundaries Clear**
- **Core Infrastructure**: API, Auth, Cache, Errors (cross-cutting concerns)
- **Business Logic**: Portfolio, Macro, Risk domains have their own UI spaces
- **Generic Components**: Primitives and Panels are domain-agnostic

### 3. **Follows DawsOS 4-Agent Philosophy**
- **Data Integration Expert** → `DawsOS.Core.API`, `DawsOS.Core.Cache`
- **Portfolio Manager** → `DawsOS.UI.Portfolio.*`, portfolio patterns
- **Macro Expert** → `DawsOS.UI.Macro.*`, macro patterns
- **Risk Manager** → `DawsOS.UI.Risk.*`, risk patterns

### 4. **Practical Benefits**
- ✅ Easy to find: `DawsOS.Patterns.Renderer` is obviously the PatternRenderer
- ✅ Natural hierarchy: Primitives → Panels → Domain components → Pages
- ✅ Extension points clear: add new patterns, domains, pages
- ✅ No duplications: Single source of truth for each function
- ✅ Testable: Each namespace is independently testable

### 5. **TypeScript-Ready**
- Each namespace becomes a TypeScript module
- Type definitions map directly to namespace structure
- Intellisense works perfectly

---

## Migration Path

### Phase 2.1: Core Infrastructure Refactoring (Week 2, Days 1-2)

**Goal**: Normalize Core layer (API, Auth, Cache, Errors)

**Changes**:

#### 1. api-client.js → DawsOS.Core.API
```javascript
// BEFORE (frontend/api-client.js, lines 378-382):
global.getCurrentPortfolioId = getCurrentPortfolioId;
global.TokenManager = TokenManager;
global.handleApiError = handleApiError;
global.retryConfig = retryConfig;
global.apiClient = apiClient;

// AFTER:
global.DawsOS.Core = global.DawsOS.Core || {};
global.DawsOS.Core.API = {
    // API methods
    request: apiClient.request,
    get: apiClient.get,
    post: apiClient.post,
    put: apiClient.put,
    delete: apiClient.delete,

    // Token management
    TokenManager: {
        getToken: TokenManager.getToken,
        setToken: TokenManager.setToken,
        clearToken: TokenManager.clearToken,
        isTokenExpired: TokenManager.isTokenExpired
    },

    // Retry config
    retryConfig: retryConfig
};
```

#### 2. Move getCurrentPortfolioId to DawsOS.Core.Auth
```javascript
// Remove duplication from context.js
// Single source of truth in DawsOS.Core.Auth.getCurrentPortfolioId
global.DawsOS.Core.Auth = {
    getCurrentUser: getCurrentUser,
    getCurrentPortfolioId: getCurrentPortfolioId,  // ONLY HERE
    login: login,
    logout: logout
};
```

#### 3. Move handleApiError to DawsOS.Core.Errors
```javascript
// Remove duplication from error-handler.js
global.DawsOS.Core.Errors = {
    handle: handleError,
    handleApiError: handleApiError,  // ONLY HERE
    show: showError,
    ErrorBoundary: ErrorBoundary
};
```

#### 4. Update pages.js imports
```javascript
// BEFORE (Phase 1.1.6 emergency fix):
const apiClient = global.DawsOS.APIClient || global.apiClient || {};
const TokenManager = apiClient.TokenManager || apiClient?.TokenManager || {};

// AFTER (Phase 2.1):
const API = DawsOS.Core.API;
const TokenManager = DawsOS.Core.API.TokenManager;
const Auth = DawsOS.Core.Auth;
const Errors = DawsOS.Core.Errors;
```

**Testing**:
- [ ] Module validation passes
- [ ] All API calls work
- [ ] Authentication still functional
- [ ] Error handling unchanged
- [ ] No regressions in 21 pages

**Effort**: 4-6 hours
**Risk**: MEDIUM (core infrastructure, but well-tested)

---

### Phase 2.2: Utils Refactoring (Week 2, Day 3)

**Goal**: Split Utils into logical subnamespaces

**Current Problem**: Utils is a junk drawer (formatting + components + hooks + data)

**Changes**:

#### 1. Split Utils into 4 namespaces
```javascript
// BEFORE (frontend/utils.js):
global.DawsOS.Utils = {
    formatCurrency,        // → DawsOS.Utils.Formatting.currency
    formatPercentage,      // → DawsOS.Utils.Formatting.percentage
    LoadingSpinner,        // → DawsOS.UI.Primitives.LoadingSpinner
    ErrorMessage,          // → DawsOS.UI.Primitives.ErrorMessage
    useCachedQuery,        // → DawsOS.Utils.Hooks.useCachedQuery
    getDataSourceFromResponse,  // → DawsOS.Utils.Data.getDataSourceFromResponse
    // ...
};

// AFTER:
global.DawsOS.Utils.Formatting = {
    currency: formatCurrency,
    percentage: formatPercentage,
    number: formatNumber,
    date: formatDate,
    value: formatValue,
    getColorClass: getColorClass
};

global.DawsOS.UI.Primitives = {
    LoadingSpinner: LoadingSpinner,
    ErrorMessage: ErrorMessage,
    EmptyState: EmptyState,
    RetryableError: RetryableError,
    DataBadge: DataBadge,
    FormField: FormField,
    NetworkStatusIndicator: NetworkStatusIndicator
};

global.DawsOS.Utils.Hooks = {
    useCachedQuery: useCachedQuery,
    useCachedMutation: useCachedMutation
};

global.DawsOS.Utils.Data = {
    getDataSourceFromResponse: getDataSourceFromResponse,
    withDataProvenance: withDataProvenance,
    ProvenanceWarningBanner: ProvenanceWarningBanner
};
```

#### 2. Update pages.js imports
```javascript
// BEFORE (Phase 1.1.6):
const LoadingSpinner = Utils.LoadingSpinner;
const formatCurrency = Utils.formatCurrency;

// AFTER (Phase 2.2):
const LoadingSpinner = DawsOS.UI.Primitives.LoadingSpinner;
const formatCurrency = DawsOS.Utils.Formatting.currency;
```

**Effort**: 3-4 hours
**Risk**: LOW (mostly renaming)

---

### Phase 2.3: Pattern System Refactoring (Week 2, Day 4)

**Goal**: Elevate Patterns to top-level namespace

**Changes**:

#### 1. Reorganize PatternSystem
```javascript
// BEFORE:
global.DawsOS.PatternSystem = {
    getDataByPath,
    PatternRenderer,
    PanelRenderer,
    patternRegistry,
    queryKeys,
    queryHelpers
};

// AFTER:
global.DawsOS.Patterns = {
    Renderer: {
        render: renderPattern,
        PatternRenderer: PatternRenderer  // React component
    },

    Registry: {
        patterns: patternRegistry,
        get: getPattern,
        list: listPatterns,
        validate: validatePattern
    },

    Helpers: {
        getDataByPath: getDataByPath,
        queryKeys: queryKeys,
        queryHelpers: queryHelpers,
        PanelRenderer: PanelRenderer
    }
};
```

**Effort**: 2-3 hours
**Risk**: LOW (well-isolated module)

---

### Phase 2.4: Panel/Page Namespace (Week 2, Day 5)

**Goal**: Organize panels and pages hierarchically

**Changes**:

#### 1. Keep Panels as-is (already correct)
```javascript
global.DawsOS.UI.Panels = {
    MetricsGridPanel,
    TablePanel,
    LineChartPanel,
    // ... all 12 panels
};
```

#### 2. Pages stay at DawsOS.Pages (already correct)
```javascript
global.DawsOS.Pages = {
    LoginPage,
    DashboardPage,
    HoldingsPage,
    // ... all 21 pages
};
```

**Effort**: 1 hour (validation only)
**Risk**: NONE (no changes needed)

---

### Phase 2.5: Domain Components Extraction (Week 3)

**Goal**: Extract domain-specific components from Panels

**Analysis Required**:
- Identify Portfolio-specific components (HoldingsTable, PositionDetails, etc.)
- Identify Macro-specific components (RegimeIndicator, CyclePhaseChart, etc.)
- Identify Risk-specific components (VaRCalculator, StressTesting, etc.)

**Not Urgent**: Defer to Phase 3 (Panels work fine as generic renderers)

---

## Backward Compatibility Strategy

### Option 1: Dual Export (Recommended for Phase 2)

```javascript
// New namespace (correct)
global.DawsOS.Core.API = { ... };

// Legacy alias (deprecated, remove in Phase 3)
global.apiClient = global.DawsOS.Core.API;  // ⚠️ DEPRECATED

// Add deprecation warning
Object.defineProperty(global, 'apiClient', {
    get: function() {
        console.warn('[DEPRECATED] global.apiClient is deprecated. Use DawsOS.Core.API instead.');
        return global.DawsOS.Core.API;
    }
});
```

**Benefits**:
- ✅ Zero breaking changes during migration
- ✅ Clear deprecation warnings in console
- ✅ Easy to track usage with console warnings
- ✅ Remove aliases in Phase 3 (one breaking change)

### Option 2: Big Bang (NOT Recommended)

- Update all imports in one commit
- High risk, difficult to rollback
- No gradual migration path

---

## Testing Strategy

### 1. Module Validation Enhancement

Add namespace structure validation to full_ui.html:

```javascript
function validateNamespaceStructure() {
    const requiredNamespaces = {
        'DawsOS.Core.API': ['request', 'get', 'post', 'put', 'delete', 'TokenManager'],
        'DawsOS.Core.Auth': ['getCurrentUser', 'getCurrentPortfolioId'],
        'DawsOS.Core.Errors': ['handle', 'handleApiError', 'show'],
        'DawsOS.Patterns.Renderer': ['render', 'PatternRenderer'],
        'DawsOS.Patterns.Registry': ['patterns', 'get', 'list'],
        'DawsOS.UI.Primitives': ['LoadingSpinner', 'ErrorMessage', 'EmptyState'],
        'DawsOS.UI.Panels': ['MetricsGridPanel', 'TablePanel', 'LineChartPanel'],
        'DawsOS.Utils.Formatting': ['currency', 'percentage', 'number', 'date'],
        // ... full structure
    };

    const errors = [];
    for (const [namespace, exports] of Object.entries(requiredNamespaces)) {
        const obj = namespace.split('.').reduce((o, k) => o?.[k], window);
        if (!obj) {
            errors.push(`Namespace ${namespace} not found`);
            continue;
        }
        for (const exportName of exports) {
            if (typeof obj[exportName] === 'undefined') {
                errors.push(`${namespace}.${exportName} is undefined`);
            }
        }
    }

    return { errors, warnings: [] };
}
```

### 2. Integration Tests

Create test suite for each phase:

```javascript
// Phase 2.1 Tests (Core refactoring)
describe('DawsOS.Core.API', () => {
    it('should make API requests', async () => { ... });
    it('should handle authentication', () => { ... });
    it('should retry failed requests', async () => { ... });
});

// Phase 2.2 Tests (Utils refactoring)
describe('DawsOS.Utils.Formatting', () => {
    it('should format currency correctly', () => {
        expect(DawsOS.Utils.Formatting.currency(1500000)).toBe('$1.5M');
    });
});
```

### 3. Replit Testing Checklist

After each phase:
- [ ] Module validation passes
- [ ] All 21 pages load
- [ ] Pattern rendering works
- [ ] API calls successful
- [ ] No console errors (except deprecation warnings)
- [ ] Visual regression test (screenshots match)

---

## Timeline

### Week 2: Core Refactoring
- **Day 1-2**: Phase 2.1 - Core Infrastructure (API, Auth, Cache, Errors)
- **Day 3**: Phase 2.2 - Utils split (Formatting, Hooks, Data)
- **Day 4**: Phase 2.3 - Pattern System elevation
- **Day 5**: Phase 2.4 - Validation and testing

**Effort**: 10-13 hours
**Risk**: LOW-MEDIUM (incremental changes with backward compatibility)

### Week 3: Cleanup
- **Day 1-2**: Remove deprecation aliases
- **Day 3-5**: Phase 2.5 - Domain component extraction (optional)

---

## Success Criteria

### Phase 2 Complete When:
- ✅ All modules use `DawsOS.*` namespace pattern (no global pollution)
- ✅ No duplications (single source of truth for each function)
- ✅ Logical grouping (Core, Patterns, UI, Pages, Utils, Context)
- ✅ Module validation enhanced with namespace structure checks
- ✅ All 21 pages work on Replit
- ✅ No breaking changes (backward compatibility maintained)
- ✅ Clear deprecation path (aliases with warnings)

### Phase 3 Complete When:
- ✅ All deprecation aliases removed
- ✅ TypeScript definitions added
- ✅ Domain components extracted (Portfolio, Macro, Risk)
- ✅ ESM module system adopted
- ✅ Build process established (Webpack/Vite)

---

## Files to Modify

### Phase 2.1 (Core Infrastructure)
- `frontend/api-client.js` - Refactor to DawsOS.Core.API
- `frontend/context.js` - Move getCurrentPortfolioId to Core.Auth
- `frontend/error-handler.js` - Refactor to DawsOS.Core.Errors
- `frontend/pages.js` - Update Core imports
- `full_ui.html` - Update validation

### Phase 2.2 (Utils Split)
- `frontend/utils.js` - Split into 4 namespaces
- `frontend/pages.js` - Update Utils imports
- `full_ui.html` - Update validation

### Phase 2.3 (Pattern System)
- `frontend/pattern-system.js` - Reorganize to DawsOS.Patterns
- `frontend/pages.js` - Update Pattern imports
- `full_ui.html` - Update validation

### Phase 2.4 (Validation)
- `full_ui.html` - Enhanced namespace validation
- Create integration tests

---

## Risks and Mitigation

### Risk 1: Breaking Changes During Migration
**Mitigation**: Dual export strategy with deprecation warnings

### Risk 2: Testing Coverage Insufficient
**Mitigation**: Enhanced module validation + integration tests + Replit smoke tests

### Risk 3: Scope Creep (Domain Components)
**Mitigation**: Defer Phase 2.5 (domain extraction) to Week 3, not required for Phase 2 completion

### Risk 4: Merge Conflicts
**Mitigation**: Complete Phase 2 in single week, minimize parallel development

---

## Comparison: Current vs Phase 2

### Current (Phase 1.1.6 Emergency State)
```javascript
// 9 different top-level exports
global.DawsOS.Utils.*              // 12 mixed exports
global.DawsOS.Panels.*             // 12 panels
global.DawsOS.PatternSystem.*      // 6 exports
global.DawsOS.Pages.*              // 21 pages
global.DawsOS.Context.*            // 1 provider
global.DawsOS.CacheManager         // 1 singleton
global.DawsOS.FormValidator        // 1 object
global.DawsOS.ErrorHandler         // 1 object
global.apiClient                   // ❌ 8 exports (pollutes global)
```

### After Phase 2
```javascript
// Clean hierarchical structure
global.DawsOS = {
    Core: {
        API: { /* 8 exports */ },
        Auth: { /* 4 exports */ },
        Cache: { /* 4 exports */ },
        Errors: { /* 4 exports */ }
    },
    Patterns: {
        Renderer: { /* 2 exports */ },
        Registry: { /* 4 exports */ },
        Helpers: { /* 4 exports */ }
    },
    UI: {
        Primitives: { /* 7 exports */ },
        Panels: { /* 12 exports */ }
    },
    Pages: { /* 21 exports */ },
    Utils: {
        Formatting: { /* 6 exports */ },
        Hooks: { /* 2 exports */ },
        Data: { /* 3 exports */ },
        Validation: { /* 1 export */ }
    },
    Context: { /* 3 exports */ }
};
```

**Benefits**:
- ✅ Zero global pollution
- ✅ Clear logical grouping
- ✅ Easy to navigate
- ✅ TypeScript-ready
- ✅ Scalable architecture

---

**Status**: PLANNING (awaiting Replit validation results)
**Next**: Begin Phase 2.1 after emergency fixes confirmed stable
**Owner**: Data Integration Expert + Portfolio Manager

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
