# JWT Authentication Agent - Implementation Specification

**Agent Type**: JWT_AUTH_AGENT  
**Priority**: P0 (Critical)  
**Estimated Time**: 20 hours  
**Status**: 🚧 Ready for Implementation  

---

## Mission

Replace the stub `X-User-ID` header authentication with proper JWT-based authentication, implement role-based access control (RBAC), and add comprehensive audit logging for all authentication events.

---

## Current State Analysis

### ✅ What's Already Implemented
- **Auth Service**: `backend/app/services/auth.py` exists with basic structure
- **Auth Middleware**: `backend/app/middleware/auth_middleware.py` implemented
- **JWT Dependencies**: PyJWT, bcrypt, python-multipart already installed
- **Database Schema**: Users table with roles and permissions
- **API Routes**: Auth endpoints exist but need JWT integration

### ⚠️ What Needs Implementation
- **JWT Token Generation**: Replace stub headers with real JWT tokens
- **Token Validation**: Verify JWT signatures and expiration
- **Role-Based Access Control**: Enforce permissions based on user roles
- **Password Hashing**: Implement secure password storage
- **Session Management**: Handle token refresh and revocation
- **Audit Logging**: Log all authentication events

---

## Implementation Tasks

### Task 1: JWT Token Management (6 hours)

**File**: `backend/app/services/auth.py`

**Current State**:
```python
class AuthService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        # TODO: Implement JWT secret management
```

**Target Implementation**:
```python
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from backend.app.core.types import User, UserRole

class AuthService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expiry_hours = 24
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        async with self.db_pool.acquire() as conn:
            # Get user from database
            user_row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1 AND is_active = true",
                email
            )
            
            if not user_row:
                return None
            
            # Verify password
            if not self.pwd_context.verify(password, user_row["password_hash"]):
                await self._log_auth_failure(user_row["id"], "invalid_password")
                return None
            
            # Update last login
            await conn.execute(
                "UPDATE users SET last_login_at = NOW() WHERE id = $1",
                user_row["id"]
            )
            
            await self._log_auth_success(user_row["id"])
            
            return User(
                id=user_row["id"],
                email=user_row["email"],
                role=UserRole(user_row["role"]),
                permissions=user_row["permissions"],
                is_active=user_row["is_active"]
            )
    
    def generate_access_token(self, user: User) -> str:
        """Generate JWT access token."""
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "permissions": user.permissions,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours),
            "type": "access"
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token."""
        payload = {
            "sub": str(user.id),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=30),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
    
    async def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
```

### Task 2: Role-Based Access Control (4 hours)

**File**: `backend/app/core/rbac.py`

**Create new RBAC module**:
```python
from enum import Enum
from typing import List, Set
from dataclasses import dataclass

class Permission(Enum):
    # Portfolio permissions
    PORTFOLIO_READ = "portfolio:read"
    PORTFOLIO_WRITE = "portfolio:write"
    PORTFOLIO_DELETE = "portfolio:delete"
    
    # Trade permissions
    TRADE_READ = "trade:read"
    TRADE_WRITE = "trade:write"
    TRADE_EXECUTE = "trade:execute"
    
    # Report permissions
    REPORT_GENERATE = "report:generate"
    REPORT_EXPORT = "report:export"
    
    # Admin permissions
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"

class Role(Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    PORTFOLIO_MANAGER = "portfolio_manager"
    ADMIN = "admin"

@dataclass
class RolePermissions:
    role: Role
    permissions: Set[Permission]

# Role-permission mappings
ROLE_PERMISSIONS = {
    Role.VIEWER: {
        Permission.PORTFOLIO_READ,
        Permission.TRADE_READ,
    },
    Role.ANALYST: {
        Permission.PORTFOLIO_READ,
        Permission.TRADE_READ,
        Permission.REPORT_GENERATE,
    },
    Role.PORTFOLIO_MANAGER: {
        Permission.PORTFOLIO_READ,
        Permission.PORTFOLIO_WRITE,
        Permission.TRADE_READ,
        Permission.TRADE_WRITE,
        Permission.TRADE_EXECUTE,
        Permission.REPORT_GENERATE,
        Permission.REPORT_EXPORT,
    },
    Role.ADMIN: {
        Permission.PORTFOLIO_READ,
        Permission.PORTFOLIO_WRITE,
        Permission.PORTFOLIO_DELETE,
        Permission.TRADE_READ,
        Permission.TRADE_WRITE,
        Permission.TRADE_EXECUTE,
        Permission.REPORT_GENERATE,
        Permission.REPORT_EXPORT,
        Permission.USER_MANAGE,
        Permission.SYSTEM_CONFIG,
        Permission.AUDIT_READ,
    }
}

class RBACService:
    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS
    
    def has_permission(self, user_role: Role, required_permission: Permission) -> bool:
        """Check if user role has required permission."""
        user_permissions = self.role_permissions.get(user_role, set())
        return required_permission in user_permissions
    
    def get_user_permissions(self, user_role: Role) -> Set[Permission]:
        """Get all permissions for a user role."""
        return self.role_permissions.get(user_role, set())
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract user from context
                user = kwargs.get('user') or args[0] if args else None
                if not user:
                    raise PermissionError("User context required")
                
                if not self.has_permission(user.role, permission):
                    raise PermissionError(f"Permission {permission.value} required")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

### Task 3: Middleware Integration (3 hours)

**File**: `backend/app/middleware/auth_middleware.py`

**Update middleware to use JWT**:
```python
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.services.auth import AuthService
from backend.app.core.rbac import RBACService, Permission

security = HTTPBearer()

class AuthMiddleware:
    def __init__(self, auth_service: AuthService, rbac_service: RBACService):
        self.auth_service = auth_service
        self.rbac_service = rbac_service
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> User:
        """Extract and validate current user from JWT token."""
        token = credentials.credentials
        
        # Verify token
        payload = self.auth_service.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        async with self.auth_service.db_pool.acquire() as conn:
            user_row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1 AND is_active = true",
                payload["sub"]
            )
            
            if not user_row:
                raise HTTPException(
                    status_code=401,
                    detail="User not found or inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return User(
                id=user_row["id"],
                email=user_row["email"],
                role=UserRole(user_row["role"]),
                permissions=user_row["permissions"],
                is_active=user_row["is_active"]
            )
    
    def require_permission(self, permission: Permission):
        """Dependency to require specific permission."""
        async def permission_checker(user: User = Depends(self.get_current_user)):
            if not self.rbac_service.has_permission(user.role, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission {permission.value} required"
                )
            return user
        return permission_checker
```

### Task 4: API Endpoints (3 hours)

**File**: `backend/app/api/routes/auth.py`

**Update auth endpoints**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from backend.app.services.auth import AuthService
from backend.app.middleware.auth_middleware import AuthMiddleware

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    permissions: List[str]
    is_active: bool

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return JWT tokens."""
    user = await auth_service.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = auth_service.generate_access_token(user)
    refresh_token = auth_service.generate_refresh_token(user)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.jwt_expiry_hours * 3600,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            permissions=user.permissions,
            is_active=user.is_active
        )
    )

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    payload = auth_service.verify_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    async with auth_service.db_pool.acquire() as conn:
        user_row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1 AND is_active = true",
            payload["sub"]
        )
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user = User(
            id=user_row["id"],
            email=user_row["email"],
            role=UserRole(user_row["role"]),
            permissions=user_row["permissions"],
            is_active=user_row["is_active"]
        )
    
    # Generate new tokens
    access_token = auth_service.generate_access_token(user)
    refresh_token = auth_service.generate_refresh_token(user)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.jwt_expiry_hours * 3600,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            permissions=user.permissions,
            is_active=user.is_active
        )
    )

@router.post("/logout")
async def logout(
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user (invalidate tokens)."""
    # In a production system, you'd add tokens to a blacklist
    # For now, we'll just log the logout event
    await auth_service._log_logout(user.id)
    
    return {"message": "Successfully logged out"}
```

### Task 5: Audit Logging (2 hours)

**File**: `backend/app/services/audit.py`

**Enhance audit service**:
```python
from datetime import datetime
from typing import Dict, Any
from enum import Enum

class AuditEvent(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PERMISSION_DENIED = "permission_denied"
    PASSWORD_CHANGE = "password_change"
    ROLE_CHANGE = "role_change"

class AuditService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def log_auth_event(
        self,
        event_type: AuditEvent,
        user_id: Optional[str],
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log authentication event."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (
                    event_type, user_id, details, ip_address, user_agent, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                event_type.value,
                user_id,
                json.dumps(details),
                ip_address,
                user_agent,
                datetime.utcnow()
            )
    
    async def log_auth_success(self, user_id: str, ip_address: str = None):
        """Log successful authentication."""
        await self.log_auth_event(
            AuditEvent.LOGIN_SUCCESS,
            user_id,
            {"message": "User authenticated successfully"},
            ip_address
        )
    
    async def log_auth_failure(self, user_id: Optional[str], reason: str, ip_address: str = None):
        """Log failed authentication attempt."""
        await self.log_auth_event(
            AuditEvent.LOGIN_FAILURE,
            user_id,
            {"reason": reason},
            ip_address
        )
```

### Task 6: Database Schema Updates (2 hours)

**File**: `backend/db/migrations/009_jwt_auth.sql`

**Add JWT-specific fields**:
```sql
-- Add JWT-related fields to users table
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMPTZ;

-- Create audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for audit log
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- Create token blacklist table (for logout)
CREATE TABLE token_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for token blacklist
CREATE INDEX idx_token_blacklist_jti ON token_blacklist(token_jti);
CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);
```

---

## Integration Points

### FastAPI App Integration
**File**: `backend/app/api/executor.py`

Update to use JWT authentication:
```python
from backend.app.middleware.auth_middleware import AuthMiddleware

# Initialize auth middleware
auth_service = AuthService(db_pool)
rbac_service = RBACService()
auth_middleware = AuthMiddleware(auth_service, rbac_service)

# Update dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    return await auth_middleware.get_current_user(credentials)

# Update protected endpoints
@app.post("/v1/execute")
async def execute(
    request: ExecRequest,
    user: User = Depends(get_current_user)
):
    # Implementation with authenticated user
    pass
```

### Environment Configuration
**File**: `.env`

Add JWT configuration:
```bash
# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
JWT_REFRESH_EXPIRY_DAYS=30

# Password Security
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
```

---

## Testing Strategy

### Unit Tests
- JWT token generation and validation
- Password hashing and verification
- RBAC permission checking
- Audit logging

### Integration Tests
- Login/logout flow
- Token refresh
- Permission enforcement
- API endpoint protection

### Security Tests
- Token tampering resistance
- Brute force protection
- Session management
- Audit trail completeness

---

## Security Considerations

### Token Security
- Use strong JWT secret (256-bit minimum)
- Implement token rotation
- Add token blacklisting for logout
- Use HTTPS in production

### Password Security
- Bcrypt with appropriate rounds (12+)
- Password complexity requirements
- Account lockout after failed attempts
- Password history prevention

### Audit Requirements
- Log all authentication events
- Include IP addresses and user agents
- Retain logs for compliance period
- Monitor for suspicious patterns

---

## Success Criteria

### Functional Requirements
- [ ] JWT tokens generated and validated correctly
- [ ] RBAC permissions enforced on all endpoints
- [ ] Login/logout flow works end-to-end
- [ ] Token refresh mechanism functional
- [ ] Audit logging captures all events

### Security Requirements
- [ ] Passwords hashed with bcrypt
- [ ] JWT secrets properly managed
- [ ] Account lockout after failed attempts
- [ ] All authentication events logged
- [ ] HTTPS enforcement in production

### Performance Requirements
- [ ] Token validation completes in <10ms
- [ ] Database queries optimized
- [ ] Concurrent user support
- [ ] Memory usage within limits

---

**Estimated Completion**: 20 hours  
**Priority**: P0 (Critical for production)  
**Dependencies**: Database schema updates  
**Risk Level**: Medium (security-critical implementation)
