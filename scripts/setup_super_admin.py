#!/usr/bin/env python3
"""
DawsOS Super Admin Setup Script

Purpose: Create and configure super admin user account
Updated: 2025-10-28
Priority: P0 (Critical for system access)

Features:
    - Creates super admin user with full permissions
    - Configures all APIs for the account
    - Validates authentication setup
    - Provides clear usage instructions

Usage:
    python scripts/setup_super_admin.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.auth import AuthService
from backend.app.db.connection import init_db_pool

logger = logging.getLogger("DawsOS.SuperAdminSetup")
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)

# Super Admin Configuration
SUPER_ADMIN_EMAIL = "michael@dawsos.com"
SUPER_ADMIN_PASSWORD = "mozzuq-byfqyQ-5tefvu"
SUPER_ADMIN_ROLE = "ADMIN"


async def create_super_admin():
    """Create super admin user account."""
    try:
        print("🔧 Initializing database...")
        pool = await init_db_pool()
        print("✅ Database initialized")
        
        print("🔧 Creating auth service...")
        auth_service = AuthService()
        print("✅ Auth service created")
        
        print("🔧 Creating super admin user...")
        try:
            result = await auth_service.register_user(
                email=SUPER_ADMIN_EMAIL,
                password=SUPER_ADMIN_PASSWORD,
                role=SUPER_ADMIN_ROLE,
                ip_address='127.0.0.1',
                user_agent='DawsOS-SuperAdmin-Setup'
            )
            
            if result:
                print("✅ Super admin user created successfully")
                print(f"   📧 Email: {result.get('email')}")
                print(f"   🆔 User ID: {result.get('user_id')}")
                print(f"   🔑 Role: {result.get('role')}")
                print(f"   🎫 Token: {result.get('access_token', 'Generated')[:20]}...")
                return True
            else:
                print("❌ Failed to create super admin user")
                return False
                
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Super admin user already exists")
                print(f"   📧 Email: {SUPER_ADMIN_EMAIL}")
                print(f"   🔑 Role: {SUPER_ADMIN_ROLE}")
                print("   ℹ️  User is ready to use")
                return True
            else:
                print(f"❌ Failed to create super admin user: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Super admin creation failed: {e}")
        return False


async def validate_authentication():
    """Validate that authentication works correctly."""
    try:
        print("🔧 Testing authentication...")
        
        # Test login
        auth_service = AuthService()
        result = await auth_service.authenticate_user(
            email=SUPER_ADMIN_EMAIL,
            password=SUPER_ADMIN_PASSWORD
        )
        
        if result:
            print("✅ Authentication test successful")
            print(f"   📧 Email: {result.get('email')}")
            print(f"   🔑 Role: {result.get('role')}")
            print(f"   🎫 Token: {result.get('access_token', 'Generated')[:20]}...")
            return True
        else:
            print("❌ Authentication test failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication validation failed: {e}")
        return False


def print_usage_instructions():
    """Print clear usage instructions."""
    print("\n" + "="*60)
    print("🎉 SUPER ADMIN ACCOUNT SETUP COMPLETE")
    print("="*60)
    print()
    print("📧 LOGIN CREDENTIALS:")
    print(f"   Email: {SUPER_ADMIN_EMAIL}")
    print(f"   Password: {SUPER_ADMIN_PASSWORD}")
    print(f"   Role: {SUPER_ADMIN_ROLE}")
    print()
    print("🔗 API ENDPOINTS:")
    print("   Backend API: http://localhost:8000")
    print("   Frontend UI: http://localhost:3002")
    print("   API Docs: http://localhost:8000/docs")
    print()
    print("🚀 HOW TO USE:")
    print("   1. Start the backend: ./backend/run_api.sh")
    print("   2. Start the frontend: cd dawsos-ui && npm run dev")
    print("   3. Login with the credentials above")
    print("   4. All APIs are configured for this account")
    print()
    print("🔐 AUTHENTICATION:")
    print("   - JWT tokens are used for authentication")
    print("   - Tokens expire after 24 hours")
    print("   - Use 'Authorization: Bearer <token>' header")
    print("   - All endpoints require authentication except /health")
    print()
    print("⚠️  SECURITY NOTES:")
    print("   - This is a development setup")
    print("   - Change password in production")
    print("   - JWT secret should be set in production")
    print("   - Consider using environment variables for credentials")
    print()
    print("="*60)


async def main():
    """Main setup function."""
    print("🚀 DawsOS Super Admin Setup")
    print("="*40)
    
    # Create super admin user
    success = await create_super_admin()
    if not success:
        print("❌ Setup failed - could not create super admin user")
        return False
    
    # Validate authentication
    auth_success = await validate_authentication()
    if not auth_success:
        print("❌ Setup failed - authentication validation failed")
        return False
    
    # Print usage instructions
    print_usage_instructions()
    
    print("✅ Super admin setup completed successfully!")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
