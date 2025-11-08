"""
Authentication API Routes

Purpose: Login, token refresh, user management endpoints
Updated: 2025-01-14
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
from starlette.requests import Request
from pydantic import BaseModel, EmailStr, Field

from app.services.auth import AuthenticationError, ROLES
from app.middleware.auth_middleware import verify_token, require_role
from app.db.connection import get_db_pool
from app.core.di_container import ensure_initialized

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
async def login(
    request: LoginRequest,
    http_request: Request
):
    """
    Authenticate user and return JWT token.

    Validates email/password against database and returns JWT if valid.

    Args:
        request: Login credentials (email, password)
        http_request: FastAPI Request object for extracting IP and user agent

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
        # Get auth service from DI container
        container = ensure_initialized()
        auth_service = container.resolve("auth")
        
        # Extract IP address from request (handles proxies via X-Forwarded-For)
        client_ip = http_request.client.host if http_request.client else None
        forwarded_for = http_request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP from X-Forwarded-For header (client IP)
            client_ip = forwarded_for.split(",")[0].strip()
        elif http_request.headers.get("X-Real-IP"):
            # Fallback to X-Real-IP header
            client_ip = http_request.headers.get("X-Real-IP")
        
        # Extract user agent from request
        user_agent = http_request.headers.get("User-Agent", "Unknown")
        
        # Use unified authentication service
        auth_data = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=client_ip or "127.0.0.1",
            user_agent=user_agent
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

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error in login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error (programming error)"
        )

    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Login error: {e}")
        # Don't raise DatabaseError here - convert to HTTPException is intentional
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
    # Get auth service from DI container
    container = ensure_initialized()
    auth_service = container.resolve("auth")

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
    # Get auth service from DI container
    container = ensure_initialized()
    auth_service = container.resolve("auth")
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
    # Get auth service from DI container
    container = ensure_initialized()
    auth_service = container.resolve("auth")

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
        from app.db.connection import execute_query

        query = """
            SELECT id, email, role, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """

        rows = await execute_query(query, limit, offset)

        return [dict(row) for row in rows]

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        # Programming errors - should not happen, log and re-raise as HTTPException
        logger.error(f"Programming error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error (programming error)"
        )
    except Exception as e:
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Failed to list users: {e}")
        # Don't raise DatabaseError here - convert to HTTPException is intentional
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.post("/users", dependencies=[Depends(require_role("ADMIN"))])
async def create_user(
    email: EmailStr,
    password: str,
    role: str = "USER",
    http_request: Request = None
) -> Dict:
    """
    Create new user (ADMIN only).

    Args:
        email: User email
        password: User password (will be hashed)
        role: User role (default: USER)
        http_request: FastAPI Request object for extracting IP and user agent

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
        # Get auth service from DI container
        container = ensure_initialized()
        auth_service = container.resolve("auth")
        
        # Extract IP address from request (handles proxies via X-Forwarded-For)
        client_ip = None
        user_agent = "API Client"
        if http_request:
            client_ip = http_request.client.host if http_request.client else None
            forwarded_for = http_request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # Take first IP from X-Forwarded-For header (client IP)
                client_ip = forwarded_for.split(",")[0].strip()
            elif http_request.headers.get("X-Real-IP"):
                # Fallback to X-Real-IP header
                client_ip = http_request.headers.get("X-Real-IP")
            
            # Extract user agent from request
            user_agent = http_request.headers.get("User-Agent", "API Client")
        
        # Use unified authentication service
        user_data = await auth_service.register_user(
            email=email,
            password=password,
            role=role,
            ip_address=client_ip or "127.0.0.1",
            user_agent=user_agent
        )

        logger.info(f"User created: id={user_data['user_id']}, email={email}, role={role}")

        # Get actual creation time from database
        from app.db.connection import execute_query_one
        user_record = await execute_query_one(
            "SELECT created_at FROM users WHERE id = $1",
            user_data["user_id"]
        )
        created_at = user_record["created_at"] if user_record else None

        return {
            "id": user_data["user_id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "created_at": created_at.isoformat() if created_at else None
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
        # Service/database errors - log and re-raise as HTTPException
        logger.error(f"Failed to create user: {e}")
        # Don't raise DatabaseError here - convert to HTTPException is intentional
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
