"""
Authentication Service - JWT and RBAC Implementation

Purpose: Handle JWT token generation/verification, password hashing, and role-based permissions
Updated: 2025-10-27
Priority: P0 (Critical for security)

Architecture:
    - JWT tokens with 24-hour expiration
    - bcrypt password hashing with salt rounds
    - Role hierarchy: ADMIN > MANAGER > USER > VIEWER
    - Permissions mapped to roles with inheritance

Usage:
    from backend.app.services.auth import get_auth_service

    auth_service = get_auth_service()

    # Generate JWT
    token = auth_service.generate_jwt(user_id, email, role)

    # Verify JWT
    claims = auth_service.verify_jwt(token)

    # Check permission
    has_permission = auth_service.check_permission(user_role, "write_trades")

    # Hash password
    hashed = auth_service.hash_password(password)

    # Verify password
    is_valid = auth_service.verify_password(password, hashed)
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import bcrypt
import jwt

logger = logging.getLogger(__name__)

# ============================================================================
# Role-Based Access Control (RBAC) Configuration
# ============================================================================

# Role hierarchy and permissions
ROLES = {
    "VIEWER": {
        "permissions": ["read_portfolio", "read_metrics"],
        "level": 1,
        "description": "Read-only access to portfolios and metrics"
    },
    "USER": {
        "permissions": ["read_portfolio", "read_metrics", "execute_patterns"],
        "level": 2,
        "description": "Execute patterns and view results"
    },
    "MANAGER": {
        "permissions": [
            "read_portfolio",
            "read_metrics",
            "execute_patterns",
            "export_reports",
            "write_trades"
        ],
        "level": 3,
        "description": "Execute trades and export reports"
    },
    "ADMIN": {
        "permissions": ["*"],  # All permissions
        "level": 4,
        "description": "Full system access including user management"
    }
}

# All defined permissions in the system
ALL_PERMISSIONS = [
    "read_portfolio",      # View portfolio data
    "read_metrics",        # View metrics and analytics
    "execute_patterns",    # Execute analysis patterns
    "export_reports",      # Export PDF/CSV reports
    "write_trades",        # Execute and record trades
    "admin_users",         # User management (admin only)
    "admin_system",        # System configuration (admin only)
]


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when user lacks required permission."""
    pass


class AuthService:
    """
    Authentication and authorization service.

    Handles:
        - JWT token generation and verification
        - Password hashing and verification
        - Role-based permission checking
    """

    def __init__(self, jwt_secret: Optional[str] = None, jwt_algorithm: str = "HS256"):
        """
        Initialize auth service.

        Args:
            jwt_secret: Secret key for JWT signing (defaults to env var AUTH_JWT_SECRET)
            jwt_algorithm: JWT algorithm (default: HS256)
        """
        self.jwt_secret = jwt_secret or os.getenv("AUTH_JWT_SECRET")
        if not self.jwt_secret:
            logger.warning("AUTH_JWT_SECRET not set, using insecure default (DEV ONLY)")
            self.jwt_secret = "INSECURE_DEV_SECRET_CHANGE_IN_PRODUCTION"

        self.jwt_algorithm = jwt_algorithm
        self.token_expiry_hours = 24  # JWT expires after 24 hours

        logger.info(f"AuthService initialized (algorithm={jwt_algorithm}, expiry={self.token_expiry_hours}h)")

    # ========================================================================
    # JWT Token Management
    # ========================================================================

    def generate_jwt(self, user_id: str, email: str, role: str) -> str:
        """
        Generate JWT token for authenticated user.

        Args:
            user_id: User UUID (as string)
            email: User email address
            role: User role (VIEWER, USER, MANAGER, ADMIN)

        Returns:
            Signed JWT token string

        Raises:
            ValueError: If role is invalid

        Example:
            >>> token = auth_service.generate_jwt(
            ...     "11111111-1111-1111-1111-111111111111",
            ...     "user@example.com",
            ...     "USER"
            ... )
        """
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of: {list(ROLES.keys())}")

        # Build JWT claims
        now = datetime.utcnow()
        exp = now + timedelta(hours=self.token_expiry_hours)

        claims = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(exp.timestamp()),   # Expires at
            "iss": "DawsOS",               # Issuer
            "sub": user_id,                # Subject (user ID)
        }

        # Sign token
        token = jwt.encode(claims, self.jwt_secret, algorithm=self.jwt_algorithm)

        logger.info(f"Generated JWT for user_id={user_id}, role={role}, expires={exp.isoformat()}")

        return token

    def verify_jwt(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and extract claims.

        Args:
            token: JWT token string

        Returns:
            Dict with claims: {user_id, email, role, exp, iat}

        Raises:
            AuthenticationError: If token is invalid, expired, or malformed

        Example:
            >>> claims = auth_service.verify_jwt(token)
            >>> user_id = claims["user_id"]
            >>> role = claims["role"]
        """
        try:
            # Verify signature and expiration
            claims = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "require": ["user_id", "email", "role", "exp", "iat"]
                }
            )

            logger.debug(f"JWT verified for user_id={claims['user_id']}, role={claims['role']}")

            return claims

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise AuthenticationError("Token has expired")

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise AuthenticationError(f"Invalid token: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error verifying JWT: {e}")
            raise AuthenticationError(f"Token verification failed: {str(e)}")

    # ========================================================================
    # Role-Based Access Control (RBAC)
    # ========================================================================

    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """
        Check if user role has required permission.

        Uses role hierarchy: higher-level roles inherit lower-level permissions.
        ADMIN role has all permissions (wildcard "*").

        Args:
            user_role: User's role (VIEWER, USER, MANAGER, ADMIN)
            required_permission: Permission to check (e.g., "write_trades")

        Returns:
            True if user has permission, False otherwise

        Example:
            >>> auth_service.check_permission("MANAGER", "write_trades")
            True
            >>> auth_service.check_permission("VIEWER", "write_trades")
            False
        """
        if user_role not in ROLES:
            logger.warning(f"Unknown role: {user_role}")
            return False

        role_config = ROLES[user_role]

        # ADMIN has wildcard permission
        if "*" in role_config["permissions"]:
            return True

        # Check direct permission
        if required_permission in role_config["permissions"]:
            return True

        # Check inherited permissions from lower-level roles
        user_level = role_config["level"]
        for other_role, other_config in ROLES.items():
            if other_config["level"] < user_level:
                if required_permission in other_config["permissions"]:
                    return True

        return False

    def get_user_permissions(self, user_role: str) -> List[str]:
        """
        Get all permissions for a given role.

        Args:
            user_role: User's role

        Returns:
            List of permission strings

        Example:
            >>> auth_service.get_user_permissions("MANAGER")
            ['read_portfolio', 'read_metrics', 'execute_patterns', 'export_reports', 'write_trades']
        """
        if user_role not in ROLES:
            return []

        role_config = ROLES[user_role]

        # ADMIN has all permissions
        if "*" in role_config["permissions"]:
            return ALL_PERMISSIONS

        # Collect permissions from this role and all lower-level roles
        user_level = role_config["level"]
        permissions = set(role_config["permissions"])

        for other_role, other_config in ROLES.items():
            if other_config["level"] < user_level:
                permissions.update(other_config["permissions"])

        return sorted(list(permissions))

    # ========================================================================
    # Password Management
    # ========================================================================

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.

        Uses 12 salt rounds for security/performance balance.

        Args:
            password: Plain text password

        Returns:
            Hashed password string (bcrypt format)

        Example:
            >>> hashed = auth_service.hash_password("secure_password_123")
            >>> # Store hashed in database
        """
        if not password:
            raise ValueError("Password cannot be empty")

        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

        logger.debug("Password hashed successfully")

        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plain text password
            hashed: Hashed password (from database)

        Returns:
            True if password matches, False otherwise

        Example:
            >>> is_valid = auth_service.verify_password("user_input", stored_hash)
            >>> if is_valid:
            ...     # Grant access
        """
        if not password or not hashed:
            return False

        try:
            is_valid = bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )

            if is_valid:
                logger.debug("Password verification succeeded")
            else:
                logger.debug("Password verification failed")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False


# ============================================================================
# Service Singleton
# ============================================================================

_auth_service = None


def get_auth_service() -> AuthService:
    """
    Get singleton auth service instance.

    Returns:
        AuthService instance

    Example:
        >>> from backend.app.services.auth import get_auth_service
        >>> auth = get_auth_service()
        >>> token = auth.generate_jwt(user_id, email, role)
    """
    global _auth_service

    if _auth_service is None:
        _auth_service = AuthService()

    return _auth_service
