"""
Authentication API Routes

Purpose: Login, token refresh, user management endpoints
Updated: 2025-10-27
Priority: P0 (Critical for authentication)

Endpoints:
    POST /auth/login - Authenticate user and return JWT
    POST /auth/refresh - Refresh JWT token
    GET /auth/me - Get current user info
    GET /auth/permissions - Get user permissions

Architecture:
    - Login validates credentials and returns JWT
    - JWT required for protected endpoints
    - Token expires after 24 hours

Usage:
    # Login
    curl -X POST http://localhost:8000/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email": "user@example.com", "password": "password"}'

    # Response:
    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "bearer",
      "expires_in": 86400,
      "user": {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "user@example.com",
        "role": "USER"
      }
    }

    # Use token in requests
    curl -X POST http://localhost:8000/v1/execute \
      -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
      -d '{"pattern_id": "portfolio_overview"}'
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field

from backend.app.services.auth import get_auth_service, AuthenticationError
from backend.app.middleware.auth_middleware import verify_token, require_role
from backend.app.db.connection import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Request/Response Models
# ============================================================================


class LoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "secure_password_123"
            }
        }


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Dict = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "email": "user@example.com",
                    "role": "USER"
                }
            }
        }


class UserResponse(BaseModel):
    """User information response."""
    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    permissions: List[str] = Field(..., description="User permissions")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "11111111-1111-1111-1111-111111111111",
                "email": "user@example.com",
                "role": "USER",
                "permissions": ["read_portfolio", "read_metrics", "execute_patterns"]
            }
        }


# ============================================================================
# Authentication Endpoints
# ============================================================================


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Validates email/password against database and returns JWT if valid.

    Args:
        request: Login credentials (email, password)

    Returns:
        LoginResponse with JWT token and user info

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 500: If database error occurs

    Example:
        >>> response = await login(LoginRequest(
        ...     email="user@example.com",
        ...     password="password123"
        ... ))
        >>> token = response.access_token
    """
    try:
        auth_service = get_auth_service()
        
        # Use unified authentication service
        auth_data = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address="127.0.0.1",  # TODO: Get real IP from request
            user_agent="API Client"  # TODO: Get real user agent
        )

        logger.info(f"Login successful: user_id={auth_data['user_id']}, email={request.email}")

        # Return token and user info
        return LoginResponse(
            access_token=auth_data["token"],
            token_type="bearer",
            expires_in=auth_data["expires_in"],
            user={
                "id": auth_data["user_id"],
                "email": auth_data["email"],
                "role": auth_data["role"]
            }
        )

    except AuthenticationError as e:
        logger.warning(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(claims: Dict = Depends(verify_token)):
    """
    Get current authenticated user info.

    Requires valid JWT token.

    Args:
        claims: JWT claims (from verify_token dependency)

    Returns:
        UserResponse with user info and permissions

    Example:
        >>> # With Authorization: Bearer <token>
        >>> response = await get_current_user()
        >>> print(response.permissions)
    """
    auth_service = get_auth_service()

    user_id = claims["user_id"]
    email = claims["email"]
    role = claims["role"]

    # Get permissions for role
    permissions = auth_service.get_user_permissions(role)

    return UserResponse(
        id=user_id,
        email=email,
        role=role,
        permissions=permissions
    )


@router.get("/permissions")
async def get_user_permissions(claims: Dict = Depends(verify_token)) -> List[str]:
    """
    Get list of permissions for current user.

    Requires valid JWT token.

    Args:
        claims: JWT claims (from verify_token dependency)

    Returns:
        List of permission strings

    Example:
        >>> # With Authorization: Bearer <token>
        >>> permissions = await get_user_permissions()
        >>> print(permissions)
        ['read_portfolio', 'read_metrics', 'execute_patterns']
    """
    auth_service = get_auth_service()
    role = claims["role"]

    permissions = auth_service.get_user_permissions(role)

    return permissions


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(claims: Dict = Depends(verify_token)):
    """
    Refresh JWT token.

    Issues a new token with extended expiration. Current token must be valid.

    Args:
        claims: JWT claims (from verify_token dependency)

    Returns:
        LoginResponse with new JWT token

    Example:
        >>> # With Authorization: Bearer <old_token>
        >>> response = await refresh_token()
        >>> new_token = response.access_token
    """
    auth_service = get_auth_service()

    user_id = claims["user_id"]
    email = claims["email"]
    role = claims["role"]

    # Generate new token
    new_token = auth_service.generate_jwt(user_id, email, role)

    logger.info(f"Token refreshed: user_id={user_id}")

    return LoginResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=86400,
        user={
            "id": user_id,
            "email": email,
            "role": role
        }
    )


# ============================================================================
# Admin Endpoints (User Management)
# ============================================================================


@router.get("/users", dependencies=[Depends(require_role("ADMIN"))])
async def list_users(
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    List all users (ADMIN only).

    Args:
        limit: Max number of users (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of user records (without password hashes)

    Example:
        >>> # With Authorization: Bearer <admin_token>
        >>> users = await list_users()
    """
    try:
        pool = get_db_pool()

        query = """
            SELECT id, email, role, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """

        rows = await pool.fetch(query, limit, offset)

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.post("/users", dependencies=[Depends(require_role("ADMIN"))])
async def create_user(
    email: EmailStr,
    password: str,
    role: str = "USER"
) -> Dict:
    """
    Create new user (ADMIN only).

    Args:
        email: User email
        password: User password (will be hashed)
        role: User role (default: USER)

    Returns:
        Created user record (without password hash)

    Raises:
        HTTPException 400: If email already exists
        HTTPException 500: If database error occurs

    Example:
        >>> # With Authorization: Bearer <admin_token>
        >>> user = await create_user(
        ...     email="newuser@example.com",
        ...     password="secure_password",
        ...     role="USER"
        ... )
    """
    try:
        auth_service = get_auth_service()
        
        # Use unified authentication service
        user_data = await auth_service.register_user(
            email=email,
            password=password,
            role=role,
            ip_address="127.0.0.1",  # TODO: Get real IP from request
            user_agent="API Client"  # TODO: Get real user agent
        )

        logger.info(f"User created: id={user_data['user_id']}, email={email}, role={role}")

        return {
            "id": user_data["user_id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "created_at": "NOW()"  # TODO: Get actual creation time
        }

    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {email} already exists"
            )
        elif "Invalid role" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {list(ROLES.keys())}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
