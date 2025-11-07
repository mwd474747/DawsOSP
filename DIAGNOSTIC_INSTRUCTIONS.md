# Diagnostic Instructions for Module Loading Failure

**Status**: Need browser console output to diagnose
**Added**: Comprehensive logging in api-client.js (commit 07edbba)

---

## What We Need

Open the browser console on Replit and report **exactly what you see**.

### Expected Console Output (if working)

```
[api-client.js] 1. IIFE started
[api-client.js] 2. Constants defined
[api-client.js] 3. All objects defined (apiClient, TokenManager, retryConfig)
[api-client.js] 4. Namespace initialized
[api-client.js] 5. DawsOS.Core.API exported
[api-client.js] 6. DawsOS.Core.Auth exported
[api-client.js] 7. DawsOS.Core.Errors exported
✅ API Client module loaded successfully (DawsOS.Core.*)
```

### What Each Scenario Means

#### Scenario 1: No Logs At All
**Meaning**: api-client.js isn't loading
**Possible Causes**:
- 404 error (file not found)
- Syntax error preventing parse
- Script tag missing or wrong path

**What to check**:
1. Network tab: Is api-client.js returning 404?
2. Console: Any syntax errors?
3. View page source: Is `<script src="frontend/api-client.js"></script>` present?

#### Scenario 2: Logs Stop at Step 1 or 2
**Meaning**: Early runtime error (before apiClient definition)
**Possible Causes**:
- `axios` not loaded
- Interceptor setup failing

**What to check**:
1. Does axios exist? Type `axios` in console
2. Error message after log #2

#### Scenario 3: Logs Stop at Step 3
**Meaning**: Error creating apiClient, TokenManager, or retryConfig objects
**Possible Causes**:
- Circular reference issue
- Missing dependency

**What to check**:
- Error message in console after log #3

#### Scenario 4: Logs Stop at Step 4
**Meaning**: Error initializing namespace
**Possible Causes**:
- `DawsOS` already exists but is not an object
- `window` object issues

#### Scenario 5: Logs Stop at Step 5
**Meaning**: Error during spread operator or TokenManager export
**Possible Causes**:
- Spread operator not supported (old browser)
- TokenManager methods don't exist
- `.bind()` failing

**What to check**:
- Browser version (spread needs ES2018+)
- Error message after log #5

#### Scenario 6: All Logs Appear, But Validation Still Fails
**Meaning**: Timing issue - pages.js loads before api-client.js completes
**Possible Causes**:
- Script load order wrong
- pages.js IIFE runs before api-client IIFE

**What to check**:
1. Script order in full_ui.html
2. Does `DawsOS.Core.API` exist when you type it in console?

---

## How to Check Browser Console

### On Replit

1. Open your Replit project
2. Click the browser preview
3. **Press F12** or **Right-click → Inspect**
4. Click the **Console** tab
5. **Copy ALL console output** and send it

### What to Send

Please send:
1. **All console.log messages** (including the [api-client.js] ones)
2. **Any error messages** (red text)
3. **The exact point where logs stop** (if they don't complete)

---

## Example Reports

### Good Report Example

```
Console output:
[api-client.js] 1. IIFE started
[api-client.js] 2. Constants defined
[api-client.js] 3. All objects defined (apiClient, TokenManager, retryConfig)
[api-client.js] 4. Namespace initialized
❌ [api-client.js] FATAL ERROR during module load: TypeError: Cannot read property 'getToken' of undefined
Error stack: at Object.<anonymous> (api-client.js:394:24)

Logs stop at step 4. Error says TokenManager.getToken is undefined.
```

**This tells me**: TokenManager object exists but getToken method doesn't

### Bad Report Example

```
It's still not working.
```

**This tells me**: Nothing - I can't diagnose without actual error messages

---

## Quick Checks You Can Do

While in the browser console, try typing these commands and report the results:

### Check 1: Is axios loaded?
```javascript
typeof axios
```
**Expected**: `"object"`
**If "undefined"**: axios didn't load

### Check 2: Does DawsOS exist?
```javascript
typeof DawsOS
```
**Expected**: `"object"`
**If "undefined"**: No modules loaded at all

### Check 3: Does DawsOS.Core exist?
```javascript
typeof DawsOS.Core
```
**Expected**: `"object"`
**If "undefined"**: api-client.js didn't complete

### Check 4: Does DawsOS.Core.API exist?
```javascript
typeof DawsOS.Core.API
```
**Expected**: `"object"`
**If "undefined"**: Export failed at step 5

### Check 5: List API methods
```javascript
Object.keys(DawsOS.Core.API)
```
**Expected**: `['executePattern', 'getPortfolio', 'getHoldings', ..., 'TokenManager', 'retryConfig']`

### Check 6: Does executePattern exist?
```javascript
typeof DawsOS.Core.API.executePattern
```
**Expected**: `"function"`
**If "undefined"**: Spread operator didn't work

---

## Why We Need This

I've fixed 3 bugs so far:
1. ✅ TokenManager.clearToken → removeToken
2. ✅ apiClient.request (doesn't exist) → ...apiClient spread
3. ✅ Missing TokenManager methods

But the modules STILL aren't loading. This means there's a **runtime error** happening that I can't see because:
- `node -c` only checks syntax (passes)
- I can't see the browser console from here
- The error is preventing the IIFE from completing

**With the diagnostic logs, I'll see EXACTLY where it's failing.**

---

## What Happens Next

### If Logs Show Error at Specific Step

I'll know exactly which line is failing and can fix it immediately.

### If No Logs Appear

I'll know the file isn't loading at all and can check:
- File path issues
- Script tag issues
- Syntax errors preventing parse

### If All Logs Appear

I'll know the module IS loading, but there's a timing issue with validation.

---

## Summary

**Please send me the complete browser console output from Replit.**

This will show:
1. Which step the module fails at
2. The exact error message
3. Whether it's a timing issue or actual error

Without this information, I'm debugging blind and just guessing.

---

**Status**: Awaiting browser console output
**Next**: Fix the specific error shown in console logs

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
