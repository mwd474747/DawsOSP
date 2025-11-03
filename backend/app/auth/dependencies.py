"""
Authentication Dependencies Module

This module centralizes all authentication-related functions and dependencies
to avoid code duplication across the application.

Created as part of Sprint 1 of the authentication refactoring.
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Union

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

# ============================================================================
# Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# JWT Configuration - Exported for compatibility with verify_jwt_token
JWT_SECRET = os.environ.get("AUTH_JWT_SECRET", "dawsos-secret-key-2024")  # Use env var or fallback
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Export for backward compatibility
__all__ = ['JWT_SECRET', 'JWT_ALGORITHM', 'JWT_EXPIRATION_HOURS', 
           'hash_password', 'verify_password', 'create_jwt_token', 
           'get_current_user', 'require_auth', 'require_role']

# ============================================================================
# Password Utilities
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using SHA256 with salt"""
    salt = "dawsos_salt_"  # In production, use unique salt per user
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

# ============================================================================
# JWT Token Management
# ============================================================================

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    """Create JWT token with proper error handling"""
    try:
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        logger.error(f"Failed to create JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create authentication token"
        )

# ============================================================================
# Authentication Functions
# ============================================================================

async def get_current_user(request_or_token: Union[Request, str]) -> Optional[dict]:
    """Get current user from JWT token in request or from token string

    Args:
        request_or_token: Either a FastAPI Request object or a bearer token string

    Returns:
        User dict with id, email, role or None if invalid
    """
    auth_header = ""

    # Handle both Request object and string token
    if isinstance(request_or_token, str):
        # Direct token string
        auth_header = request_or_token if request_or_token.startswith("Bearer ") else f"Bearer {request_or_token}"
    elif hasattr(request_or_token, 'headers'):
        # FastAPI Request object
        auth_header = request_or_token.headers.get("Authorization", "")
    else:
        logger.warning(f"Invalid input to get_current_user: {type(request_or_token)}")
        return None

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user")
        }
    except JWTError as e:
        logger.debug(f"JWT validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        return None

async def require_auth(request: Request) -> dict:
    """
    FastAPI dependency for requiring authentication.
    
    This replaces the repeated pattern:
    ```
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    ```
    
    Usage:
    ```
    @app.get("/protected")
    async def protected_route(user: dict = Depends(require_auth)):
        return {"user": user}
    ```
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

# ============================================================================
# Role-Based Access Control
# ============================================================================

def require_role(required_role: str):
    """
    Dependency factory for role-based access control.
    
    Usage:
    ```
    @app.get("/admin")
    async def admin_route(user: dict = Depends(require_role("admin"))):
        return {"admin": user}
    ```
    """
    async def role_checker(request: Request):
        user = await require_auth(request)
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return user
    return role_checker