"""
Unified Authentication Service - JWT and Database Integration

Purpose: Complete authentication service with JWT tokens, password management, and database operations
Updated: 2025-10-27
Priority: P0 (Critical for security)

Architecture:
    - JWT tokens with 24-hour expiration
    - bcrypt password hashing with salt rounds
    - Role hierarchy: ADMIN > MANAGER > USER > VIEWER
    - Database-integrated user management
    - Comprehensive audit logging
    - Account lockout and security features

Usage:
    from app.services.auth import get_auth_service

    auth_service = get_auth_service()

    # Register user
    user_data = await auth_service.register_user(
        email="user@example.com",
        password="secure_password",
        role="USER"
    )

    # Authenticate user
    auth_data = await auth_service.authenticate_user(
        email="user@example.com",
        password="secure_password"
    )

    # Verify JWT
    claims = auth_service.verify_jwt(auth_data["token"])

    # Check permission
    has_permission = auth_service.check_permission("USER", "read_portfolios")
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.db.connection import execute_query, execute_query_one, execute_statement

logger = logging.getLogger(__name__)

# ============================================================================
# Role-Based Access Control (RBAC) Configuration
# ============================================================================

# Role hierarchy and permissions
ROLES = {
    "VIEWER": {
        "level": 1,
        "permissions": ["read_portfolios", "read_reports"]
    },
    "USER": {
        "level": 2,
        "permissions": ["read_portfolios", "read_reports", "write_trades", "read_analytics"]
    },
    "MANAGER": {
        "level": 3,
        "permissions": ["read_portfolios", "read_reports", "write_trades", "read_analytics", 
                       "manage_portfolios", "export_data", "manage_alerts"]
    },
    "ADMIN": {
        "level": 4,
        "permissions": ["*"]  # Wildcard - all permissions
    }
}

# ============================================================================
# Custom Exceptions
# ============================================================================

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass

class ServiceError(Exception):
    """
    Base exception for service errors.
    
    **Deprecated:** Use exceptions from `app.core.exceptions` instead (e.g., `BusinessLogicError`).
    This class is kept for backward compatibility only.
    """
    pass

# ============================================================================
# Unified Authentication Service
# ============================================================================

class AuthService:
    """
    Unified authentication and authorization service.

    Handles:
        - JWT token generation and verification
        - Password hashing and verification
        - Role-based permission checking
        - User registration and management
        - Database operations
        - Audit logging
        - Security features (lockout, etc.)
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
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 30

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
            "iat": int(now.timestamp()) - 1,  # Issued at (1 second ago to avoid clock skew)
            "exp": int(exp.timestamp()),       # Expires at
            "iss": "DawsOS",                   # Issuer
            "sub": user_id,                    # Subject (user ID)
            "nbf": int(now.timestamp()) - 1,   # Not before (1 second ago)
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
                    "verify_iat": False,  # Disable iat verification for now
                    "verify_nbf": False,  # Disable nbf verification for now
                    "require": ["user_id", "email", "role", "exp"]
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

        user_config = ROLES[user_role]
        user_permissions = user_config["permissions"]

        # Check for wildcard permission
        if "*" in user_permissions:
            return True

        # Check for exact permission
        if required_permission in user_permissions:
            return True

        # Check role hierarchy - higher-level roles inherit lower-level permissions
        user_level = user_config["level"]
        for other_role, other_config in ROLES.items():
            if other_config["level"] < user_level:
                if required_permission in other_config["permissions"]:
                    return True

        return False

    def get_user_permissions(self, user_role: str) -> List[str]:
        """
        Get all permissions for a user role (including inherited).

        Args:
            user_role: User's role

        Returns:
            List of permission strings

        Example:
            >>> permissions = auth_service.get_user_permissions("MANAGER")
            >>> print(permissions)
            ["read_portfolios", "write_trades", "manage_portfolios", ...]
        """
        if user_role not in ROLES:
            return []

        user_config = ROLES[user_role]
        permissions = set(user_config["permissions"])

        # Add inherited permissions from lower-level roles
        user_level = user_config["level"]
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
            >>> is_valid = auth_service.verify_password("password", stored_hash)
        """
        try:
            result = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            logger.debug(f"Password verification: {'success' if result else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    # ========================================================================
    # Database Operations
    # ========================================================================

    async def register_user(
        self,
        email: str,
        password: str,
        role: str = "USER",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db_conn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            email: User email address
            password: Plain text password
            role: User role (default: USER)
            ip_address: Registration IP address
            user_agent: User agent string

        Returns:
            Dict with user info and JWT token

        Raises:
            ValueError: If email already exists or invalid data
            AuthenticationError: If registration fails
        """
        # Validate inputs
        if not email or not password:
            raise ValueError("Email and password are required")

        if role not in ["VIEWER", "USER", "MANAGER", "ADMIN"]:
            raise ValueError(f"Invalid role: {role}")

        # Check if user already exists
        if db_conn:
            existing_user = await db_conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                email
            )
        else:
            existing_user = await execute_query_one(
                "SELECT id FROM users WHERE email = $1",
                email
            )

        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = self.hash_password(password)

        # Create user
        user_id = uuid4()
        if db_conn:
            await db_conn.execute(
                """
                INSERT INTO users (id, email, role, permissions, is_active, password_hash, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                user_id, email, role, [], True, password_hash
            )
        else:
            await execute_statement(
                """
                INSERT INTO users (id, email, role, permissions, is_active, password_hash, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                user_id, email, role, [], True, password_hash
            )

        # Generate JWT token
        token = self.generate_jwt(str(user_id), email, role)

        # Log registration
        await self._log_auth_event(
            "user_registered",
            str(user_id),
            f"email={email}, role={role}",
            ip_address,
            user_agent,
            db_conn
        )

        logger.info(f"User registered: {email} ({role})")

        return {
            "user_id": str(user_id),
            "email": email,
            "role": role,
            "token": token,
            "expires_in": self.token_expiry_hours * 3600
        }

    async def authenticate_user(
        self, 
        email: str, 
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user with email and password.

        Args:
            email: User email address
            password: Plain text password
            ip_address: Login IP address
            user_agent: User agent string

        Returns:
            Dict with user info and JWT token

        Raises:
            AuthenticationError: If authentication fails
        """
        # Get user from database
        user = await execute_query_one(
            """
            SELECT id, email, role, permissions, is_active, password_hash, 
                   failed_login_attempts, locked_until
            FROM users 
            WHERE email = $1
            """,
            email
        )

        if not user:
            await self._log_auth_event(
                "login_failed",
                None,
                f"email={email}, reason=user_not_found",
                ip_address,
                user_agent
            )
            raise AuthenticationError("Invalid email or password")

        # Check if account is locked
        if user["locked_until"] and user["locked_until"] > datetime.utcnow():
            await self._log_auth_event(
                "login_failed",
                str(user["id"]),
                f"email={email}, reason=account_locked",
                ip_address,
                user_agent
            )
            raise AuthenticationError("Account is temporarily locked due to too many failed attempts")

        # Check if account is active
        if not user["is_active"]:
            await self._log_auth_event(
                "login_failed",
                str(user["id"]),
                f"email={email}, reason=account_inactive",
                ip_address,
                user_agent
            )
            raise AuthenticationError("Account is inactive")

        # Verify password
        if not self.verify_password(password, user["password_hash"]):
            # Increment failed login attempts
            new_attempts = user["failed_login_attempts"] + 1
            locked_until = None

            if new_attempts >= self.max_login_attempts:
                locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)

            await execute_statement(
                """
                UPDATE users 
                SET failed_login_attempts = $1, locked_until = $2
                WHERE id = $3
                """,
                new_attempts, locked_until, user["id"]
            )

            await self._log_auth_event(
                "login_failed",
                str(user["id"]),
                f"email={email}, reason=invalid_password, attempts={new_attempts}",
                ip_address,
                user_agent
            )

            if locked_until:
                raise AuthenticationError(f"Account locked due to too many failed attempts. Try again after {locked_until.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                raise AuthenticationError("Invalid email or password")

        # Successful login - reset failed attempts and update last login
        await execute_statement(
            """
            UPDATE users 
            SET failed_login_attempts = 0, locked_until = NULL, last_login_at = NOW()
            WHERE id = $1
            """,
            user["id"]
        )

        # Generate JWT token
        token = self.generate_jwt(str(user["id"]), user["email"], user["role"])

        # Log successful login
        await self._log_auth_event(
            "login_success",
            str(user["id"]),
            f"email={email}, role={user['role']}",
            ip_address,
            user_agent
        )

        logger.info(f"User authenticated: {email} ({user['role']})")

        return {
            "user_id": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
            "permissions": user["permissions"],
            "token": token,
            "expires_in": self.token_expiry_hours * 3600
        }

    async def logout_user(
        self, 
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Logout user by blacklisting their token.

        Args:
            token: JWT token to blacklist
            ip_address: Request IP address
            user_agent: User agent string
        """
        try:
            # Verify token to get user info
            claims = self.verify_jwt(token)
            user_id = claims["user_id"]

            # Add token to blacklist (using jti if available, otherwise hash the token)
            import hashlib
            token_jti = claims.get("jti", hashlib.sha256(token.encode()).hexdigest())
            expires_at = datetime.fromtimestamp(claims["exp"])

            await execute_statement(
                """
                INSERT INTO token_blacklist (token_jti, user_id, expires_at, created_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (token_jti) DO NOTHING
                """,
                token_jti, user_id, expires_at
            )

            # Log logout
            await self._log_auth_event(
                "user_logout",
                user_id,
                f"email={claims['email']}",
                ip_address,
                user_agent
            )

            logger.info(f"User logged out: {claims['email']}")

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            # Don't raise exception - logout should always succeed

    async def change_password(
        self, 
        user_id: str, 
        current_password: str, 
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            ip_address: Request IP address
            user_agent: User agent string

        Raises:
            AuthenticationError: If current password is incorrect
        """
        # Get user
        user = await execute_query_one(
            "SELECT email, password_hash FROM users WHERE id = $1",
            user_id
        )

        if not user:
            raise AuthenticationError("User not found")

        # Verify current password
        if not self.verify_password(current_password, user["password_hash"]):
            await self._log_auth_event(
                "password_change_failed",
                user_id,
                {"email": user["email"], "reason": "invalid_current_password"},
                ip_address,
                user_agent
            )
            raise AuthenticationError("Current password is incorrect")

        # Hash new password
        new_password_hash = self.hash_password(new_password)

        # Update password
        await execute_statement(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            new_password_hash, user_id
        )

        # Log password change
        await self._log_auth_event(
            "password_changed",
            user_id,
            f"email={user['email']}",
            ip_address,
            user_agent
        )

        logger.info(f"Password changed for user: {user['email']}")

    async def _log_auth_event(
        self,
        event_type: str,
        user_id: Optional[str],
        details: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db_conn: Optional[Any] = None
    ) -> None:
        """Log authentication event to audit log."""
        try:
            if db_conn:
                await db_conn.execute(
                    """
                    INSERT INTO audit_log (event_type, user_id, details, ip_address, user_agent, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    """,
                    event_type, user_id, details, ip_address, user_agent
                )
            else:
                await execute_statement(
                    """
                    INSERT INTO audit_log (event_type, user_id, details, ip_address, user_agent, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    """,
                    event_type, user_id, details, ip_address, user_agent
                )
        except Exception as e:
            logger.error(f"Failed to log auth event: {e}")
            # Don't raise exception - logging failure shouldn't break auth flow


# ============================================================================
# Singleton Instance
# ============================================================================

_auth_service = None


def get_auth_service() -> AuthService:
    """
    Get singleton auth service instance.

    Returns:
        AuthService instance

    Example:
        >>> from app.services.auth import get_auth_service
        >>> auth = get_auth_service()
        >>> token = auth.generate_jwt(user_id, email, role)
    """
    global _auth_service

    if _auth_service is None:
        _auth_service = AuthService()

    return _auth_service