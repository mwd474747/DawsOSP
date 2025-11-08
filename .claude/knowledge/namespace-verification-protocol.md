# Namespace Verification Protocol

**Purpose**: Prevent false bug reports by always verifying current code state before analysis

## Critical Rule: ALWAYS READ CURRENT FILE STATE

**Before making ANY claim about bugs or issues**:

1. ✅ Read the ACTUAL current file (not summaries, not memory)
2. ✅ Verify the exact line numbers mentioned
3. ✅ Check git history for recent changes
4. ✅ Test claims against running code when possible

## Common Mistakes to Avoid

### ❌ Mistake #1: Analyzing Stale Code
**Bad**: "Line 401 has `isTokenExpired: TokenManager.isTokenExpired.bind(TokenManager)`"
**Why bad**: File may have been updated since last read
**Good**: Read file first, then make claim based on current state

### ❌ Mistake #2: Ignoring System Reminders
**Bad**: Missing that user already fixed the issue
**Why bad**: System reminders contain recent file changes
**Good**: Check system reminders for recent modifications before analysis

### ❌ Mistake #3: Assuming Without Verifying
**Bad**: "apiClient doesn't have HTTP methods"
**Why bad**: Assumption not verified against actual code
**Good**: Search for method definitions before claiming they don't exist

### ❌ Mistake #4: Overstating Severity
**Bad**: Calling everything "CRITICAL - WILL CRASH"
**Why bad**: Silent failures (via `|| {}` fallbacks) don't crash, they fail quietly
**Good**: Distinguish between:
- 🔴 CRITICAL: App crashes immediately (no fallback)
- 🟡 MAJOR: Silent failure (fallback exists but wrong behavior)
- 🟢 MINOR: Works but not ideal (documentation, style)

## Verification Checklist

Before claiming a bug exists:

- [ ] Read current file state (not summary)
- [ ] Verify exact line numbers
- [ ] Check for `|| {}` fallbacks (prevents crashes)
- [ ] Search for method definitions before claiming "doesn't exist"
- [ ] Check system reminders for recent changes
- [ ] Verify severity: crash vs silent failure vs documentation
- [ ] Test claim if possible (syntax check, grep search)

## Example: Correct Analysis Process

### ❌ Wrong Approach
```
"CRITICAL BUG: TokenManager.isTokenExpired doesn't exist at line 401"
(based on old summary, not verified against current file)
```

### ✅ Right Approach
```
1. Read frontend/api-client.js current state
2. Check line 401 actual content
3. Search for "isTokenExpired" in file
4. Verify: Line 401 shows "refreshToken: TokenManager.refreshToken.bind(TokenManager)"
5. Conclusion: "isTokenExpired" was already removed - not a current bug
```

## Namespace Reference Truth (Current State)

**After Phase 2 Refactoring (Current)**:

```javascript
// ✅ CORRECT - Where things actually are:
DawsOS.Core.API.TokenManager           // Token management
DawsOS.Core.API.executePattern()       // API methods
DawsOS.Core.API.request/get/post/put/delete  // HTTP methods (ADDED)
DawsOS.Core.Auth.getCurrentPortfolioId // Auth utilities
DawsOS.Core.Errors.handleApiError      // Error handling
DawsOS.CacheManager                    // Cache (flat namespace)
DawsOS.ErrorHandler                    // Error handler (flat namespace)
DawsOS.FormValidator                   // Form validation (flat namespace)

// ❌ WRONG - These don't exist:
global.TokenManager                    // Moved to DawsOS.Core.API.TokenManager
global.apiClient                       // Moved to DawsOS.Core.API
DawsOS.APIClient                       // Never existed (wrong name)
```

## When Analyzing Module Imports

**Check for these patterns**:

1. **Silent Failure Pattern**:
   ```javascript
   const TokenManager = global.TokenManager || {};  // ⚠️ Gets {} if undefined
   ```
   - **Impact**: Silent failure (not a crash, but wrong behavior)
   - **Severity**: 🟡 MAJOR (not 🔴 CRITICAL)

2. **Fail-Fast Pattern**:
   ```javascript
   const TokenManager = global.TokenManager;
   if (!TokenManager) throw new Error('...');  // 🔴 Crashes immediately
   ```
   - **Impact**: Immediate crash with clear error
   - **Severity**: 🔴 CRITICAL

3. **Correct Pattern**:
   ```javascript
   const TokenManager = DawsOS.Core.API.TokenManager;
   if (!TokenManager) throw new Error('...');  // ✅ Correct namespace + validation
   ```

## Memory Aid: Recent Fixes Already Applied

**Don't report these as bugs** (already fixed):

1. ✅ `isTokenExpired` - Already removed from exports
2. ✅ HTTP methods (`request/get/post/put/delete`) - Already added to apiClient
3. ✅ Diagnostic logging - Already added to api-client.js

**Real issues that remain**:

1. ⚠️ Namespace mismatches in context.js (line 34) - uses `global.TokenManager`
2. ⚠️ Namespace mismatches in pattern-system.js (lines 55, 76) - uses wrong namespaces
3. ⚠️ Documentation inconsistencies - comments reference wrong namespaces

## Confidence Calibration

**Before saying "100% confidence"**:
- Have I read the current file?
- Have I verified this isn't already fixed?
- Have I checked for fallback patterns?
- Have I distinguished crash vs silent failure?

**If any answer is "no"**: Lower confidence to 70% or less.

## Summary

**Golden Rule**: Read first, analyze second, claim third.

**Never**: Analyze from memory/summary → Make claims → Read file to confirm
**Always**: Read file → Verify current state → Make claims based on evidence

---

This protocol was created after incorrectly claiming 7 CRITICAL bugs when:
- 2 were already fixed (isTokenExpired, HTTP methods)
- 1 was misidentified (ErrorHandler "duplication")
- 2-3 were real but overstated severity (namespace issues are 🟡 MAJOR not 🔴 CRITICAL)

**Lesson**: Always verify before claiming bugs exist.
