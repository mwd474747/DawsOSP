#!/usr/bin/env python3
"""Initialize DawsOS database with schema and migrations."""
import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def run_sql_file(conn, filepath):
    """Run SQL file against database."""
    with open(filepath, 'r') as f:
        sql = f.read()
        # Split by semicolon but handle complex statements
        statements = [s.strip() for s in sql.split(';\n') if s.strip()]
        for statement in statements:
            if statement:
                try:
                    await conn.execute(statement + ';')
                    print(f"✓ Executed: {filepath.name}")
                except Exception as e:
                    print(f"⚠ Warning in {filepath.name}: {e}")

async def init_database():
    """Initialize database with schema and migrations."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False
    
    try:
        conn = await asyncpg.connect(database_url)
        print("Connected to database")
        
        # Run schema files
        schema_dir = Path('db/schema')
        if schema_dir.exists():
            print("\n=== Running Schema Files ===")
            for sql_file in sorted(schema_dir.glob('*.sql')):
                await run_sql_file(conn, sql_file)
        
        # Run migrations  
        migrations_dir = Path('db/migrations')
        if migrations_dir.exists():
            print("\n=== Running Migrations ===")
            for sql_file in sorted(migrations_dir.glob('*.sql')):
                await run_sql_file(conn, sql_file)
        
        # Create super admin user
        print("\n=== Creating Super Admin ===")
        hashed_password = pwd_context.hash('mozzuq-byfqyQ-5tefvu')
        
        # First ensure users table exists
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'USER',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert/update super admin
        await conn.execute('''
            INSERT INTO users (email, hashed_password, role, is_active) 
            VALUES ($1, $2, 'ADMIN', true)
            ON CONFLICT (email) DO UPDATE 
            SET hashed_password = EXCLUDED.hashed_password, 
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                updated_at = CURRENT_TIMESTAMP
        ''', 'michael@dawsos.com', hashed_password)
        
        print("✓ Super admin user created/updated")
        
        await conn.close()
        print("\n✅ Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)