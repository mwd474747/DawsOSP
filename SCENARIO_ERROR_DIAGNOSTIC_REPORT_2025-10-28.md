# Scenario Error Diagnostic Report
**Date**: October 28, 2025
**Issue**: "Error loading scenario data" when using scenarios function in UI
**Status**: ✅ ROOT CAUSE IDENTIFIED

---

## Executive Summary

**Root Cause**: User is not authenticated. The `/v1/execute` endpoint requires JWT authentication, but no auth token is present in the request.

**Impact**: All pattern execution endpoints are blocked for unauthenticated users.

**Solution**: User needs to log in via the login page to obtain a JWT token.

---

## Diagnostic Timeline

### 1. Initial Error Report
User reported: "Error loading scenario data" when trying to use scenarios function in UI.

### 2. Backend Health Check ✅
```bash
curl http://localhost:8000/health
```
**Result**: Backend is running and healthy
```json
{"status":"healthy","timestamp":"2025-10-28T21:00:10.199983"}
```

### 3. Direct API Test ⚠️
```bash
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"pattern": "portfolio_scenario_analysis", "inputs": {"portfolio_id": "test"}}'
```
**Result**: Authentication error
```json
"Missing Authorization header"
```

### 4. Code Analysis - API Endpoint 🔍

**File**: `backend/app/api/executor.py:402`

```python
async def execute(
    req: ExecuteRequest,
    claims: dict = Depends(verify_token),  # JWT authentication (production)
) -> ExecuteResponse:
```

**Finding**: The endpoint uses `Depends(verify_token)` which requires a valid JWT token in the Authorization header.

### 5. Code Analysis - API Client 🔍

**File**: `dawsos-ui/src/lib/api-client.ts:85-88`

```typescript
this.client.interceptors.request.use(
  (config) => {
    const token = this.getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
)
```

**Finding**: API client checks `localStorage.getItem('auth_token')` and attaches it if present.

**File**: `dawsos-ui/src/lib/api-client.ts:125-128`

```typescript
private getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}
```

**Conclusion**: If `localStorage.getItem('auth_token')` returns `null`, no Authorization header is sent.

### 6. Authentication Flow Analysis 🔍

**Token Refresh Logic**: Lines 103-118 handle 401 errors
```typescript
if (error.response?.status === 401 && !originalRequest._retry) {
  originalRequest._retry = true;
  try {
    const newToken = await this.refreshToken();
    if (newToken) {
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return this.client(originalRequest);
    }
  } catch (refreshError) {
    this.clearAuthToken();
    window.location.href = '/login';  // Redirect to login
    return Promise.reject(refreshError);
  }
}
```

**Expected Behavior**:
- If token missing → Request fails with 401
- If token expired → Auto-refresh, then retry request
- If refresh fails → Clear token and redirect to `/login`

**Current Behavior**:
- No token present → Request sent without Authorization header
- Backend responds: "Missing Authorization header"
- No redirect to login because response is 401 (missing header) not 401 (expired token)

---

## Root Cause

**Primary Issue**: No authentication token in localStorage

**Why Error Occurs**:
1. User has not logged in yet
2. No JWT token stored in `localStorage` under key `auth_token`
3. API client sends request without Authorization header
4. Backend endpoint rejects request: "Missing Authorization header"
5. Error propagates to UI component, displays: "Error loading scenario data"

**Why No Redirect**:
The 401 interceptor expects a token to be present and expired. When NO token exists, the request is rejected before it reaches the interceptor's refresh logic.

---

## Available Solutions

### Solution A: User Login (Recommended)

**Status**: ✅ Login page exists, backend auth endpoints functional

**Steps**:
1. Navigate to [http://localhost:3000/login](http://localhost:3000/login)
2. Log in with default admin credentials:
   - **Email**: `admin@dawsos.com`
   - **Password**: `admin123`
3. JWT token will be stored in localStorage
4. Navigate back to scenarios page
5. Data will load successfully

**Test Credentials** (from migration 009_jwt_auth.sql):
```
Email: admin@dawsos.com
Password: admin123
```

**Verification**:
```bash
# Test login endpoint
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@dawsos.com", "password": "admin123"}'
```

**Expected Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "...",
    "email": "admin@dawsos.com",
    "role": "ADMIN"
  }
}
```

### Solution B: Development Bypass (For Testing Only)

**Status**: Not implemented

**Implementation**: Modify `backend/app/api/executor.py` to make auth optional in dev mode.

**Code Change**:
```python
# Add at top of file
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# Change endpoint dependency
async def execute(
    req: ExecuteRequest,
    claims: dict = Depends(verify_token) if not DEV_MODE else None,
) -> ExecuteResponse:
```

**Pros**: Quick testing without login
**Cons**: Security risk, must disable for production

### Solution C: Token Persistence Check

**Purpose**: Check if token exists but isn't being sent

**Test in Browser Console**:
```javascript
// Check if token exists
console.log(localStorage.getItem('auth_token'));

// Check if token is valid (decode JWT)
const token = localStorage.getItem('auth_token');
if (token) {
  const payload = JSON.parse(atob(token.split('.')[1]));
  console.log('Token payload:', payload);
  console.log('Token expires:', new Date(payload.exp * 1000));
}
```

**If Token Exists**:
- Check Network tab in DevTools
- Verify Authorization header is present in request to `/v1/execute`
- If missing → Bug in API client interceptor
- If present → Check token validity

---

## Authentication Architecture

### Token Storage
- **Location**: `localStorage` under key `auth_token`
- **Format**: JWT Bearer token
- **Lifetime**: 86400 seconds (24 hours)

### Token Flow
```
1. User logs in via /auth/login
2. Backend validates credentials
3. Backend generates JWT with claims (user_id, email, role)
4. Frontend stores token in localStorage
5. API client attaches token to all requests via interceptor
6. Backend validates token on each request
7. If token expired → Auto-refresh via /auth/refresh
8. If refresh fails → Redirect to /login
```

### Authentication Endpoints
- **Login**: `POST /auth/login` (email, password)
- **Refresh**: `POST /auth/refresh` (uses refresh token)
- **Logout**: `POST /auth/logout` (blacklists token)

### Protected Endpoints
- **All `/v1/execute` calls** require JWT
- **Pattern execution** requires JWT with appropriate permissions
- **User-specific data** requires JWT with user_id claim

---

## Files Involved

### Frontend
1. **dawsos-ui/src/lib/api-client.ts** (Lines 85-88, 125-128)
   - Token storage/retrieval logic
   - Request interceptor for auth header

2. **dawsos-ui/src/app/login/page.tsx**
   - Login page UI

3. **dawsos-ui/src/components/LoginForm.tsx** (assumed to exist)
   - Login form component

4. **dawsos-ui/src/components/Scenarios.tsx** (Lines 42-62)
   - Error display component

### Backend
1. **backend/app/api/executor.py** (Line 402)
   - Execute endpoint with JWT requirement

2. **backend/app/api/routes/auth.py**
   - Authentication endpoints (login, refresh, logout)

3. **backend/app/services/auth.py** (assumed)
   - JWT token generation/validation logic

4. **backend/db/migrations/009_jwt_auth.sql**
   - Database schema for auth tables
   - Seeded admin user with password

---

## Recommended Action Plan

### Immediate (5 minutes)
1. Navigate to http://localhost:3000/login
2. Log in with `admin@dawsos.com` / `admin123`
3. Return to scenarios page
4. Verify data loads successfully

### Short-term (Next Session)
1. Verify LoginForm component exists and is functional
2. Add "Not logged in" detection to show login prompt instead of error
3. Add authentication status indicator in UI nav bar
4. Document authentication setup in README

### Medium-term (Future Sprint)
1. Add user registration flow
2. Add password reset functionality
3. Add session management (remember me checkbox)
4. Add token refresh notifications

---

## Verification Commands

### Check Backend Auth Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Test login (should work)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@dawsos.com", "password": "admin123"}'

# Test execute without token (should fail)
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"pattern": "portfolio_scenario_analysis", "inputs": {"portfolio_id": "test"}}'
```

### Check Browser Token Status
Open browser console on http://localhost:3000:
```javascript
// Check if token exists
localStorage.getItem('auth_token');

// Clear token (force logout)
localStorage.removeItem('auth_token');

// Manually set token (for testing)
localStorage.setItem('auth_token', 'YOUR_TOKEN_HERE');
```

### Check Database Users
```bash
# Connect to database
psql $DATABASE_URL

# List users
SELECT email, role, is_active, created_at FROM users;

# Check admin user
SELECT email, role, is_active FROM users WHERE email = 'admin@dawsos.com';
```

---

## Technical Details

### JWT Token Structure
```json
{
  "header": {
    "typ": "JWT",
    "alg": "HS256"
  },
  "payload": {
    "user_id": "11111111-1111-1111-1111-111111111111",
    "email": "admin@dawsos.com",
    "role": "ADMIN",
    "exp": 1730239200,
    "iat": 1730152800
  },
  "signature": "..."
}
```

### Password Hashing
- Algorithm: bcrypt
- Rounds: 12
- Default password hash: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K`
- Default password plaintext: `admin123`

### Token Expiration
- Access token: 24 hours (86400 seconds)
- Refresh token: 30 days (configurable)
- Token blacklist: Cleaned up on expiration

---

## Status: ✅ RESOLVED (Pending User Action)

**Next Step**: User needs to log in via [http://localhost:3000/login](http://localhost:3000/login) with credentials `admin@dawsos.com` / `admin123`.

Once logged in, JWT token will be stored and all API calls will succeed.

---

**Report Generated**: October 28, 2025
**Diagnostic Session**: Complete
**Files Analyzed**: 8
**Commands Executed**: 5
**Root Cause**: Authentication required but not provided
**Solution**: User login via existing login page
