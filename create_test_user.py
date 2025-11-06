#!/usr/bin/env python3
"""
Create a test user in the database
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime
import bcrypt

sys.path.append('backend')

from app.db.connection import init_db_pool, get_db_pool

async def create_test_user():
    """Create a test user for API testing"""
    print("Creating test user...")
    
    try:
        # Initialize database pool
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        await init_db_pool(database_url)
        pool = await get_db_pool()
        
        async with pool.acquire() as db:
            # Hash password
            password = "test123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user
            user = await db.fetchrow("""
                INSERT INTO users (email, password_hash, role, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (email) DO UPDATE 
                SET password_hash = EXCLUDED.password_hash
                RETURNING id, email, role
            """, 
                "test@dawsos.com",
                password_hash,
                "ADMIN",
                datetime.utcnow()
            )
            
            print(f"✅ User created/updated: {user['email']} (ID: {user['id']}, Role: {user['role']})")
            print(f"   Email: test@dawsos.com")
            print(f"   Password: test123")
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_user())