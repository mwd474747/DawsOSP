"""
Authentication Middleware - JWT Verification and Permission Enforcement

Purpose: FastAPI dependencies for JWT verification and permission checking
Updated: 2025-10-27
Priority: P0 (Critical for security)

Architecture:
    - verify_token: Dependency to verify JWT from Authorization header
    - require_permission: Decorator to enforce specific permission
    - Optional authentication: Some endpoints allow unauthenticated access

Usage:
    from app.middleware.auth_middleware import verify_token, require_permission

    # Protected endpoint (requires valid JWT)
    @app.post("/v1/execute")
    async def execute_pattern(
        request: ExecuteRequest,
        claims: Dict = Depends(verify_token)
    ):
        user_id = claims["user_id"]
        user_role = claims["role"]
        ...

    # Permission-gated endpoint
    @app.post("/v1/trades")
    async def execute_trade(
        request: TradeRequest,
        claims: Dict = Depends(require_permission("write_trades"))
    ):
        ...

    # Optional authentication
    @app.get("/v1/public/patterns")
    async def list_patterns(
        claims: Optional[Dict] = Depends(optional_auth)
    ):
        # claims is None if no token provided
        ...
"""

import logging
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth import AuthenticationError, AuthorizationError
from app.core.di_container import ensure_initialized

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for Swagger UI
security = HTTPBearer(auto_error=False)


# ============================================================================
# JWT Verification Dependencies
# ============================================================================


async def verify_token(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Dict[str, any]:
    """
    Verify JWT token from Authorization header.

    This is a FastAPI dependency that validates the JWT and returns the claims.
    Use this for any protected endpoint that requires authentication.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        Dict with JWT claims: {user_id, email, role, exp, iat}

    Raises:
        HTTPException 401: If token is missing, invalid, or expired

    Example:
        >>> @app.post("/v1/execute")
        >>> async def execute_pattern(claims: Dict = Depends(verify_token)):
        ...     user_id = claims["user_id"]
        ...     role = claims["role"]
    """
    # Check for Authorization header
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check Bearer format
    if not authorization.startswith("Bearer "):
        logger.warning(f"Invalid Authorization header format: {authorization[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token
    token = authorization[7:]  # Remove "Bearer " prefix

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify token
    container = ensure_initialized()
    auth_service = container.resolve("auth")

    try:
        claims = auth_service.verify_jwt(token)
        logger.debug(f"JWT verified: user_id={claims['user_id']}, role={claims['role']}")
        return claims

    except AuthenticationError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

    except Exception as e:
        logger.error(f"Unexpected error verifying JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def optional_auth(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Optional[Dict[str, any]]:
    """
    Optional JWT verification.

    Returns claims if valid token provided, None otherwise.
    Does not raise exception for missing/invalid tokens.

    Args:
        authorization: Authorization header value (optional)

    Returns:
        Dict with JWT claims if valid, None if missing or invalid

    Example:
        >>> @app.get("/v1/public/data")
        >>> async def get_data(claims: Optional[Dict] = Depends(optional_auth)):
        ...     if claims:
        ...         # User is authenticated
        ...         user_id = claims["user_id"]
        ...     else:
        ...         # Anonymous access
        ...         user_id = None
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]
    if not token:
        return None

    container = ensure_initialized()
    auth_service = container.resolve("auth")

    try:
        claims = auth_service.verify_jwt(token)
        return claims
    except Exception:
        # Silent failure for optional auth
        return None


# ============================================================================
# Permission Enforcement
# ============================================================================


def require_permission(permission: str):
    """
    Create a dependency that enforces a specific permission.

    This is a higher-order function that returns a FastAPI dependency.
    The dependency verifies JWT AND checks if the user has the required permission.

    Args:
        permission: Required permission (e.g., "write_trades", "export_reports")

    Returns:
        FastAPI dependency function that enforces permission

    Raises:
        HTTPException 401: If JWT is invalid
        HTTPException 403: If user lacks permission

    Example:
        >>> @app.post("/v1/trades")
        >>> async def execute_trade(
        ...     request: TradeRequest,
        ...     claims: Dict = Depends(require_permission("write_trades"))
        ... ):
        ...     # Only users with write_trades permission reach here
        ...     user_id = claims["user_id"]
    """
    async def permission_checker(claims: Dict = Depends(verify_token)) -> Dict[str, any]:
        """
        Check if user has required permission.

        Args:
            claims: JWT claims from verify_token dependency

        Returns:
            JWT claims if permission granted

        Raises:
            HTTPException 403: If user lacks permission
        """
        container = ensure_initialized()
        auth_service = container.resolve("auth")
        user_role = claims.get("role")

        if not user_role:
            logger.error(f"JWT claims missing 'role' field: {claims}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid JWT claims: missing role"
            )

        # Check permission
        has_permission = auth_service.check_permission(user_role, permission)

        if not has_permission:
            logger.warning(
                f"Permission denied: user_id={claims['user_id']}, "
                f"role={user_role}, required_permission={permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )

        logger.debug(
            f"Permission granted: user_id={claims['user_id']}, "
            f"role={user_role}, permission={permission}"
        )

        return claims

    return permission_checker


def require_role(required_role: str):
    """
    Create a dependency that enforces a minimum role level.

    This checks role hierarchy: ADMIN > MANAGER > USER > VIEWER

    Args:
        required_role: Minimum required role (VIEWER, USER, MANAGER, ADMIN)

    Returns:
        FastAPI dependency function that enforces role

    Raises:
        HTTPException 401: If JWT is invalid
        HTTPException 403: If user role is insufficient

    Example:
        >>> @app.post("/admin/users")
        >>> async def manage_users(
        ...     claims: Dict = Depends(require_role("ADMIN"))
        ... ):
        ...     # Only ADMIN users reach here
    """
    async def role_checker(claims: Dict = Depends(verify_token)) -> Dict[str, any]:
        """
        Check if user has required role level.

        Args:
            claims: JWT claims from verify_token dependency

        Returns:
            JWT claims if role sufficient

        Raises:
            HTTPException 403: If user role insufficient
        """
        from app.services.auth import ROLES

        user_role = claims.get("role")

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid JWT claims: missing role"
            )

        if user_role not in ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid role: {user_role}"
            )

        if required_role not in ROLES:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid required_role configuration: {required_role}"
            )

        user_level = ROLES[user_role]["level"]
        required_level = ROLES[required_role]["level"]

        if user_level < required_level:
            logger.warning(
                f"Role check failed: user_id={claims['user_id']}, "
                f"user_role={user_role} (level {user_level}), "
                f"required_role={required_role} (level {required_level})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required role: {required_role}"
            )

        logger.debug(
            f"Role check passed: user_id={claims['user_id']}, "
            f"user_role={user_role}, required_role={required_role}"
        )

        return claims

    return role_checker


# ============================================================================
# Helper Functions
# ============================================================================


def get_user_id_from_claims(claims: Dict) -> str:
    """
    Extract user_id from JWT claims.

    Args:
        claims: JWT claims dict

    Returns:
        User ID as string

    Example:
        >>> user_id = get_user_id_from_claims(claims)
    """
    return claims.get("user_id")


def get_user_role_from_claims(claims: Dict) -> str:
    """
    Extract role from JWT claims.

    Args:
        claims: JWT claims dict

    Returns:
        User role as string

    Example:
        >>> role = get_user_role_from_claims(claims)
    """
    return claims.get("role")
