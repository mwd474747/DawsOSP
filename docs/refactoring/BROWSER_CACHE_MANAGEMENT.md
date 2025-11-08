# Browser Cache Management Guide

**Date:** January 15, 2025  
**Purpose:** Document cache-busting strategies, module loading order, and namespace structure

---

## Executive Summary

This document provides comprehensive guidance on browser cache management, module loading order, and namespace validation to prevent circular debugging issues and ensure reliable application behavior.

---

## Cache-Busting Strategies

### 1. Version Query Parameters

**Purpose:** Force browser to fetch new versions of files by appending version query parameters.

**Implementation:**
```html
<!-- Static version (manual) -->
<script src="frontend/api-client.js?v=20250115"></script>

<!-- Dynamic version (automatic) -->
<script src="frontend/version.js"></script>
<script>
    const version = window.DawsOS?.Version?.getQueryString() || Date.now();
    // Scripts are automatically updated with version query parameters
</script>
```

**How It Works:**
- Version query parameters (`?v=...`) make each file URL unique
- Browser treats `file.js?v=1` and `file.js?v=2` as different files
- Forces browser to fetch new version instead of using cache

**Best Practices:**
- Use timestamp for development (always fresh)
- Use version string for production (stable versioning)
- Update version when files change

---

### 2. Cache-Control Headers

**Purpose:** Tell browser not to cache files during development.

**Implementation:**

**Frontend (Meta Tags):**
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

**Backend (HTTP Headers):**
```python
response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
response.headers["Pragma"] = "no-cache"
response.headers["Expires"] = "0"
```

**When to Use:**
- Development: Always use no-cache headers
- Production: Use version query parameters instead

---

### 3. Version Management System

**File:** `frontend/version.js`

**Purpose:** Centralized version management for cache-busting.

**Features:**
- Version information (major.minor.patch)
- Build timestamp for development
- Query string generation
- Automatic version detection

**Usage:**
```javascript
// Get version string
const version = window.DawsOS.Version.toString(); // "20250115"

// Get query string for cache-busting
const queryString = window.DawsOS.Version.getQueryString(); // timestamp or version
```

---

## Module Loading Order

### Dependency Graph

```
api-client.js (no dependencies)
    ↓
utils.js (no dependencies)
    ↓
panels.js (depends on: utils.js)
    ↓
context.js (depends on: api-client.js, utils.js)
    ↓
pattern-system.js (depends on: context.js, panels.js, utils.js)
    ↓
pages.js (depends on: context.js, pattern-system.js, panels.js, utils.js)
```

### Load Order in HTML

```html
<!-- 1. Core Systems (no dependencies) -->
<script src="frontend/cache-manager.js"></script>
<script src="frontend/error-handler.js"></script>
<script src="frontend/form-validator.js"></script>

<!-- 2. Version Management -->
<script src="frontend/version.js"></script>

<!-- 3. Module Dependency Validation -->
<script src="frontend/module-dependencies.js"></script>

<!-- 4. API Client (no dependencies) -->
<script src="frontend/api-client.js"></script>

<!-- 5. Utils (no dependencies) -->
<script src="frontend/utils.js"></script>

<!-- 6. Panels (depends on utils) -->
<script src="frontend/panels.js"></script>

<!-- 7. Context (depends on api-client, utils) -->
<script src="frontend/context.js"></script>

<!-- 8. Pattern System (depends on context, panels, utils) -->
<script src="frontend/pattern-system.js"></script>

<!-- 9. Pages (depends on all above) -->
<script src="frontend/pages.js"></script>

<!-- 10. Namespace Validation (load after all modules) -->
<script src="frontend/namespace-validator.js"></script>
```

### Validation

**Module Dependency Validator:**
- Validates module load order
- Checks dependencies exist before use
- Reports missing dependencies
- Shows clear error messages

**Usage:**
```javascript
// Check validation results
const errors = window.DawsOS.ModuleValidator.getErrors();
const warnings = window.DawsOS.ModuleValidator.getWarnings();
const loaded = window.DawsOS.ModuleValidator.getLoadedModules();
```

---

## Namespace Structure

### Expected Namespaces

```
DawsOS
├── APIClient
│   ├── TokenManager
│   │   ├── getToken()
│   │   ├── setToken()
│   │   ├── removeToken()
│   │   ├── getUser()
│   │   ├── setUser()
│   │   ├── removeUser()
│   │   └── refreshToken()
│   └── [apiClient methods]
├── Utils
│   └── [utility functions]
├── Panels
│   └── [panel components]
├── Context
│   ├── UserContext
│   ├── UserContextProvider
│   ├── useUserContext()
│   └── PortfolioSelector
├── PatternSystem
│   └── [pattern orchestration]
└── Pages
    └── [page components]
```

### Deprecated Namespaces

**Still Work But Should Migrate:**
- `global.TokenManager` → Use `DawsOS.APIClient.TokenManager`
- `global.apiClient` → Use `DawsOS.APIClient`

**Migration Path:**
- Old code using global namespace still works
- New code should use `DawsOS.*` namespace
- Gradual migration supported

### Validation

**Namespace Validator:**
- Validates all expected namespaces exist
- Checks for deprecated namespaces
- Detects namespace pollution
- Reports errors and warnings

**Usage:**
```javascript
// Validate namespaces
const result = window.DawsOS.NamespaceValidator.validate();
// Returns: { valid: boolean, errors: [], warnings: [] }

// Get errors and warnings
const errors = window.DawsOS.NamespaceValidator.getErrors();
const warnings = window.DawsOS.NamespaceValidator.getWarnings();
```

---

## Troubleshooting Guide

### Issue: Browser Shows Old Code

**Symptoms:**
- Changes not appearing after refresh
- Old code still running
- Hard refresh required

**Solutions:**
1. **Check Cache-Control Headers**
   - Verify meta tags in HTML
   - Check HTTP headers from server
   - Use browser DevTools Network tab

2. **Check Version Query Parameters**
   - Verify version query parameters added
   - Check version.js loaded correctly
   - Verify version updated when files change

3. **Clear Browser Cache**
   - Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
   - Clear cache in browser settings
   - Use incognito/private mode

4. **Check Server Headers**
   - Verify cache-control headers set
   - Check server logs for file serving
   - Test with curl: `curl -I http://localhost:8000/frontend/api-client.js`

---

### Issue: Module Loading Errors

**Symptoms:**
- "Module not found" errors
- "Dependency missing" errors
- Silent failures

**Solutions:**
1. **Check Module Load Order**
   - Verify modules load in correct order
   - Check dependency graph
   - Use ModuleValidator to check dependencies

2. **Check Namespace Exports**
   - Verify namespaces exported correctly
   - Check namespace structure
   - Use NamespaceValidator to validate

3. **Check Console Errors**
   - Look for module loading errors
   - Check for namespace errors
   - Verify all modules loaded

---

### Issue: Namespace Errors

**Symptoms:**
- "Namespace not found" errors
- "Deprecated namespace" warnings
- Namespace pollution warnings

**Solutions:**
1. **Check Namespace Exports**
   - Verify all namespaces exported
   - Check namespace structure
   - Use NamespaceValidator

2. **Migrate Deprecated Namespaces**
   - Update code to use new namespaces
   - Remove deprecated namespace usage
   - Test after migration

3. **Check Namespace Pollution**
   - Identify unexpected global exports
   - Remove or namespace unexpected exports
   - Use NamespaceValidator to detect

---

## Best Practices

### Development

1. **Always Use Cache-Busting**
   - Use version query parameters
   - Use cache-control headers
   - Use timestamp for development

2. **Validate Module Loading**
   - Check module load order
   - Validate dependencies
   - Use ModuleValidator

3. **Validate Namespaces**
   - Check namespace structure
   - Detect namespace pollution
   - Use NamespaceValidator

### Production

1. **Use Version Strings**
   - Use semantic versioning
   - Update version when files change
   - Use version query parameters

2. **Optimize Caching**
   - Use appropriate cache headers
   - Cache static assets
   - Don't cache HTML/JS files

3. **Monitor Validation**
   - Check validation errors
   - Monitor namespace warnings
   - Fix issues proactively

---

## Tools and Utilities

### Version Management

**File:** `frontend/version.js`

**API:**
```javascript
window.DawsOS.Version.toString()        // "20250115"
window.DawsOS.Version.getQueryString()  // timestamp or version
```

### Module Validation

**File:** `frontend/module-dependencies.js`

**API:**
```javascript
window.DawsOS.ModuleValidator.getErrors()      // Get errors
window.DawsOS.ModuleValidator.getWarnings()    // Get warnings
window.DawsOS.ModuleValidator.getLoadedModules() // Get loaded modules
```

### Namespace Validation

**File:** `frontend/namespace-validator.js`

**API:**
```javascript
window.DawsOS.NamespaceValidator.validate()    // Validate namespaces
window.DawsOS.NamespaceValidator.getErrors()   // Get errors
window.DawsOS.NamespaceValidator.getWarnings() // Get warnings
```

---

## Summary

**Cache-Busting:**
- ✅ Version query parameters
- ✅ Cache-control headers
- ✅ Version management system

**Module Loading:**
- ✅ Dependency graph defined
- ✅ Load order validated
- ✅ Dependencies checked

**Namespace:**
- ✅ Structure documented
- ✅ Validation added
- ✅ Deprecated namespaces tracked

**Troubleshooting:**
- ✅ Common issues documented
- ✅ Solutions provided
- ✅ Tools available

---

**Status:** Complete  
**Last Updated:** January 15, 2025

