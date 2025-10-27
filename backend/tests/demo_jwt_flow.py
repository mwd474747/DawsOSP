"""
JWT Authentication Flow Demonstration

Purpose: Show complete JWT flow without requiring database
Updated: 2025-10-27

This demonstrates:
1. JWT token generation
2. JWT token verification
3. Role-based permission checking
4. Password hashing and verification
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.services.auth import get_auth_service, ROLES

print("=" * 80)
print("DawsOS JWT AUTHENTICATION FLOW DEMONSTRATION")
print("=" * 80)

# Initialize auth service
auth = get_auth_service()

# STEP 1: Generate JWT for a user
print("\n📝 STEP 1: Generate JWT Token")
print("-" * 80)

user_id = "11111111-1111-1111-1111-111111111111"
email = "manager@dawsos.com"
role = "MANAGER"

token = auth.generate_jwt(user_id, email, role)

print(f"User ID:  {user_id}")
print(f"Email:    {email}")
print(f"Role:     {role}")
print(f"\nGenerated JWT Token:")
print(f"{token}\n")
print(f"Token Length: {len(token)} characters")

# STEP 2: Verify JWT token
print("\n✅ STEP 2: Verify JWT Token")
print("-" * 80)

claims = auth.verify_jwt(token)

print(f"Token verified successfully!")
print(f"\nExtracted Claims:")
for key, value in claims.items():
    print(f"  {key}: {value}")

# STEP 3: Check permissions
print("\n🔐 STEP 3: Check Role Permissions")
print("-" * 80)

user_role = claims["role"]
permissions_to_check = [
    "read_portfolio",
    "execute_patterns",
    "write_trades",
    "export_reports",
    "admin_users"
]

print(f"Checking permissions for role: {user_role}\n")

for permission in permissions_to_check:
    has_permission = auth.check_permission(user_role, permission)
    status = "✅ GRANTED" if has_permission else "❌ DENIED"
    print(f"  {permission:<20} {status}")

# Show all permissions for this role
print(f"\nAll permissions for {user_role}:")
all_permissions = auth.get_user_permissions(user_role)
for perm in sorted(all_permissions):
    print(f"  - {perm}")

# STEP 4: Demonstrate role hierarchy
print("\n📊 STEP 4: Role Hierarchy Demonstration")
print("-" * 80)

print("\nPermission: 'write_trades'\n")

for role_name, role_config in ROLES.items():
    can_trade = auth.check_permission(role_name, "write_trades")
    level = role_config["level"]
    status = "✅ YES" if can_trade else "❌ NO"
    print(f"  {role_name:<10} (level {level})  {status}")

# STEP 5: Password hashing
print("\n🔑 STEP 5: Password Hashing & Verification")
print("-" * 80)

password = "secure_password_123"
hashed = auth.hash_password(password)

print(f"Original password: {password}")
print(f"Hashed password:   {hashed[:60]}...")

# Verify correct password
is_valid = auth.verify_password(password, hashed)
print(f"\nVerify correct password:   {'✅ SUCCESS' if is_valid else '❌ FAILED'}")

# Verify wrong password
is_invalid = auth.verify_password("wrong_password", hashed)
print(f"Verify incorrect password: {'❌ SUCCESS (should fail)' if is_invalid else '✅ FAILED (expected)'}")

# STEP 6: API Usage Example
print("\n🌐 STEP 6: API Usage Example")
print("-" * 80)

print("""
To use JWT authentication with the DawsOS API:

1. Login to get token:

   curl -X POST http://localhost:8000/auth/login \\
     -H "Content-Type: application/json" \\
     -d '{"email": "user@dawsos.com", "password": "user123"}'

   Response:
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "token_type": "bearer",
     "expires_in": 86400,
     "user": {"id": "...", "email": "user@dawsos.com", "role": "USER"}
   }

2. Use token in requests:

   curl -X POST http://localhost:8000/v1/execute \\
     -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \\
     -H "Content-Type: application/json" \\
     -d '{"pattern_id": "portfolio_overview", "inputs": {...}}'

3. Token expires after 24 hours. Refresh before expiry:

   curl -X POST http://localhost:8000/auth/refresh \\
     -H "Authorization: Bearer <old_token>"
""")

# SUMMARY
print("\n" + "=" * 80)
print("✅ DEMONSTRATION COMPLETE")
print("=" * 80)
print("""
Summary of implemented features:
  ✅ JWT token generation with 24-hour expiration
  ✅ JWT token verification and claims extraction
  ✅ Role-based access control (4 roles: VIEWER, USER, MANAGER, ADMIN)
  ✅ Permission hierarchy (higher roles inherit lower permissions)
  ✅ Password hashing with bcrypt (12 salt rounds)
  ✅ Password verification
  ✅ Login endpoint (/auth/login)
  ✅ Token refresh endpoint (/auth/refresh)
  ✅ User info endpoint (/auth/me)
  ✅ Audit logging service
  ✅ Portfolio access enforcement
  ✅ RLS context setting

Security features:
  🔒 JWT signed with HS256 algorithm
  🔒 Bcrypt password hashing (12 rounds)
  🔒 Row-level security (RLS) policies
  🔒 Immutable audit trail
  🔒 Fail-closed portfolio access checks
  🔒 ADMIN role for user management

Default users (from migration):
  - admin@dawsos.com (ADMIN, password: admin123)
  - user@dawsos.com (USER, password: user123)
  ⚠️  CHANGE PASSWORDS IN PRODUCTION!
""")
print("=" * 80)
