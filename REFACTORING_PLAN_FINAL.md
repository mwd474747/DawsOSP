# COMPREHENSIVE SYSTEM REFACTORING PLAN
# Purpose: Eliminate all root causes and prevent recurring issues
# Date: 2025-10-29

## EXECUTIVE SUMMARY

This plan addresses all recurring issues by:
1. **Unifying startup mechanisms** - Single entry point with validation
2. **Implementing proper migration system** - No more manual schema changes
3. **Fixing pattern execution** - Hot reload and proper template resolution
4. **Standardizing authentication** - Consistent endpoints and configuration
5. **Removing legacy code** - Eliminate all anti-patterns and duplicate code
6. **Adding comprehensive validation** - Startup checks prevent configuration errors

## PHASE 1: UNIFIED STARTUP SYSTEM

### Problem Analysis
- Multiple startup scripts with different PYTHONPATH configurations
- No validation that environment is correct
- Inconsistent module import paths
- No standardized entry point

### Solution: Single Entry Point with Validation

**File: `backend/start.py`** (NEW - replaces all startup scripts)
```python
#!/usr/bin/env python3
"""
Unified Backend Startup Script
Purpose: Single entry point with comprehensive validation
"""
import sys
import os
from pathlib import Path

# Set PYTHONPATH before any imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

# Validate environment before importing
if not (PROJECT_ROOT / "backend" / "app" / "api" / "executor.py").exists():
    print(f"❌ Error: Must run from project root. Current: {PROJECT_ROOT}")
    sys.exit(1)

# Now import and run
import uvicorn
from backend.app.api.executor import app

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.api.executor:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # No reload - prevents module reloading issues
    )
```

**File: `scripts/start-backend.sh`** (NEW - standardized startup script)
```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Validate environment
if [ ! -f "backend/app/api/executor.py" ]; then
    echo "❌ Error: Must run from project root"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export DATABASE_URL="${DATABASE_URL:-postgresql://dawsos:dawsos@localhost:5432/dawsos}"
export PYTHONPATH="$PROJECT_ROOT"

# Start backend
python backend/start.py
```

## PHASE 2: DATABASE MIGRATION SYSTEM

### Problem Analysis
- No migration system - manual schema changes
- Missing tables cause runtime errors
- No validation that schema is complete
- Migration files exist but aren't applied

### Solution: Proper Migration Manager

**File: `backend/app/db/migration_manager.py`** (NEW)
```python
"""
Database Migration Manager
Purpose: Apply migrations in order and validate schema
"""
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any

from backend.app.db.connection import execute_statement, execute_query

logger = logging.getLogger(__name__)

class MigrationManager:
    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir
        self.applied_migrations: List[str] = []

    async def initialize(self):
        """Initialize migration tracking table."""
        await execute_statement("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                checksum VARCHAR(64) NOT NULL
            )
        """)
        await self._load_applied_migrations()

    async def _load_applied_migrations(self):
        """Load list of applied migrations."""
        try:
            result = await execute_query("SELECT migration_name FROM schema_migrations ORDER BY applied_at")
            self.applied_migrations = [row[0] for row in result]
        except Exception:
            # Table doesn't exist yet - will be created in initialize()
            self.applied_migrations = []

    async def run_migrations(self):
        """Run all pending migrations."""
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            migration_name = migration_file.stem
            
            if migration_name in self.applied_migrations:
                logger.debug(f"Migration {migration_name} already applied")
                continue

            logger.info(f"Running migration: {migration_name}")
            
            try:
                migration_sql = migration_file.read_text()
                checksum = hashlib.md5(migration_sql.encode()).hexdigest()
                
                # Run migration
                await execute_statement(migration_sql)
                
                # Record migration
                await execute_statement("""
                    INSERT INTO schema_migrations (migration_name, checksum)
                    VALUES ($1, $2)
                """, migration_name, checksum)
                
                self.applied_migrations.append(migration_name)
                logger.info(f"✅ Migration {migration_name} applied successfully")
                
            except Exception as e:
                logger.error(f"❌ Migration {migration_name} failed: {e}")
                raise

    async def validate_schema(self):
        """Validate that required tables exist."""
        required_tables = [
            'users', 'portfolios', 'securities', 'positions', 'prices',
            'fx_rates', 'pricing_packs', 'macro_indicators', 'alerts',
            'audit_log', 'refresh_tokens', 'token_blacklist', 'cycle_phases',
            'portfolio_metrics', 'schema_migrations'
        ]
        
        result = await execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        existing_tables = {row[0] for row in result}
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            raise RuntimeError(f"Missing required tables: {missing_tables}")
        
        logger.info("✅ Database schema validation passed")
```

## PHASE 3: PATTERN EXECUTION FIXES

### Problem Analysis
- Patterns loaded once and never reloaded
- Template resolution fails for None values
- Step execution logic bugs

### Solution: Enhanced Pattern Orchestrator

**File: `backend/app/core/pattern_orchestrator.py`** (MODIFIED)
- Add hot reload support
- Fix template resolution with fallbacks
- Ensure step execution is properly indented

## PHASE 4: AUTHENTICATION STANDARDIZATION

### Problem Analysis
- Inconsistent endpoint paths
- JWT secret not validated
- Configuration drift

### Solution: Centralized Auth Config

**File: `backend/app/config/auth_config.py`** (NEW)
```python
"""
Centralized Authentication Configuration
Purpose: Single source of truth for auth settings
"""
import os
import logging

logger = logging.getLogger(__name__)

class AuthConfig:
    def __init__(self):
        self.jwt_secret = self._get_jwt_secret()
        self.jwt_algorithm = "HS256"
        self.token_expiry_hours = 24
        self.validate()

    def _get_jwt_secret(self) -> str:
        """Get JWT secret with validation."""
        secret = os.getenv("AUTH_JWT_SECRET")
        if not secret:
            if os.getenv("ENVIRONMENT") == "production":
                raise RuntimeError("AUTH_JWT_SECRET must be set in production")
            logger.warning("AUTH_JWT_SECRET not set, using insecure default (DEV ONLY)")
            return "INSECURE_DEV_SECRET_CHANGE_IN_PRODUCTION"
        if len(secret) < 32:
            raise RuntimeError("AUTH_JWT_SECRET must be at least 32 characters")
        return secret

    def validate(self):
        """Validate auth configuration."""
        if not self.jwt_secret:
            raise RuntimeError("JWT secret not configured")
        logger.info("✅ Auth configuration validated")
```

## PHASE 5: STARTUP VALIDATION

### Problem Analysis
- No validation that system is ready
- Failures only discovered at runtime
- Configuration errors cause cascading failures

### Solution: Comprehensive Startup Validator

**File: `backend/app/startup/validator.py`** (NEW)
```python
"""
Startup Validation System
Purpose: Validate all systems before accepting requests
"""
import asyncio
import logging
from typing import List, Dict, Any, Callable

logger = logging.getLogger(__name__)

class StartupValidator:
    def __init__(self):
        self.checks: List[Dict[str, Any]] = []

    def add_check(self, name: str, check_func: Callable, critical: bool = True):
        """Add a startup check."""
        self.checks.append({
            "name": name,
            "function": check_func,
            "critical": critical
        })

    async def validate_all(self) -> bool:
        """Run all startup checks."""
        logger.info("🔍 Running startup validation...")
        
        all_passed = True
        for check in self.checks:
            try:
                result = await check["function"]()
                if result:
                    logger.info(f"✅ {check['name']}")
                else:
                    logger.error(f"❌ {check['name']}")
                    if check["critical"]:
                        all_passed = False
            except Exception as e:
                logger.error(f"❌ {check['name']}: {e}")
                if check["critical"]:
                    all_passed = False
        
        if all_passed:
            logger.info("✅ All startup checks passed")
        else:
            logger.error("❌ Some startup checks failed")
        
        return all_passed
```

## PHASE 6: LEGACY CODE REMOVAL

### Files to Remove/Consolidate:
1. `backend/run_api.sh` → Replace with `scripts/start-backend.sh`
2. `start.sh` → Review and consolidate
3. `launch.sh` → Review and consolidate
4. Duplicate startup event handlers in executor.py
5. Manual database initialization scripts

### Code to Refactor:
1. Consolidate duplicate `@app.on_event("startup")` handlers
2. Remove manual pattern loading workarounds
3. Remove manual database table creation scripts
4. Standardize all environment variable access

## IMPLEMENTATION ORDER

1. **P0: Create unified startup system** (immediate)
2. **P0: Implement migration manager** (immediate)
3. **P0: Fix pattern orchestrator** (immediate)
4. **P0: Standardize authentication** (immediate)
5. **P1: Add startup validation** (next)
6. **P1: Remove legacy code** (next)

## VALIDATION PLAN

After implementation, validate:
1. Backend starts successfully with new startup script
2. Database migrations apply automatically
3. Patterns load and execute correctly
4. Authentication works consistently
5. All startup checks pass
6. No legacy code remains

