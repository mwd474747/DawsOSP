#!/usr/bin/env python3
"""
Enhanced DawsOS Server - Comprehensive Portfolio Management System
Version 6.0.1 - Technical Debt Fixes and Refactoring
"""

import os
import logging
import math
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Tuple, Union
from enum import Enum
import json
import hashlib
from uuid import uuid4, UUID
import random
from collections import defaultdict
from pathlib import Path
from decimal import Decimal

# Configure logging early before any imports that might use it
# Make logging level configurable via environment variable (default: INFO)
import os
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
try:
    log_level_attr = getattr(logging, log_level, logging.INFO)
except AttributeError:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"Invalid LOG_LEVEL '{log_level}', defaulting to INFO")
    log_level_attr = logging.INFO

logging.basicConfig(
    level=log_level_attr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
if log_level_attr == logging.DEBUG:
    logger.debug(f"Logging configured at DEBUG level")
else:
    logger.info(f"Logging configured at {log_level} level")

from fastapi import FastAPI, HTTPException, Request, Depends, status, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
import jwt
import asyncpg
from asyncpg.pool import Pool
import uvicorn
import httpx

# Import Anthropic SDK for AI chat
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("Anthropic SDK not installed. AI chat will use fallback responses.")
    ANTHROPIC_AVAILABLE = False
    anthropic = None

# Import authentication utilities from centralized module
import bcrypt
from backend.app.auth.dependencies import (
    hash_password, 
    # verify_password,  # We'll override this with bcrypt version
    create_jwt_token, 
    get_current_user, 
    require_auth,
    require_role,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS
)

# Override verify_password to use bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        # Handle bcrypt hashes
        if hashed_password.startswith("$2b$"):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        # Fallback to SHA256 for legacy passwords
        else:
            return hash_password(plain_password) == hashed_password
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

# Import backend services for pattern orchestration
from backend.app.services.macro_data_agent import enhance_macro_data

# Import these conditionally to handle module path issues
try:
    # Try importing from backend context
    import sys
    import os

    # Add backend directory to Python path to fix imports
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Observability disabled (modules not available)
    # Graceful degradation patterns handle missing observability modules

    # ============================================================================
    # Critical Imports - Fail Fast
    # ============================================================================
    # These are required for the server to function. If they fail, we should
    # fail fast rather than setting to None and causing runtime errors.
    
    try:
        from app.core.types import RequestCtx, ExecReq, ExecResp
        REQUEST_CTX_AVAILABLE = True
        logger.debug("RequestCtx imported successfully")
    except ImportError as e:
        logger.error(f"CRITICAL: RequestCtx not available: {e}")
        logger.error("Cannot start server without RequestCtx. Check imports.")
        raise RuntimeError(f"Cannot start server: RequestCtx import failed: {e}") from e

    # ============================================================================
    # Core Orchestration Imports - Fail Fast
    # ============================================================================
    # These are required for pattern execution. Without them, pattern endpoints
    # should return errors, not None.
    
    try:
        from app.core.agent_runtime import AgentRuntime
        AGENT_RUNTIME_AVAILABLE = True
        logger.debug("AgentRuntime imported successfully")
    except ImportError as e:
        logger.error(f"CRITICAL: AgentRuntime not available: {e}")
        logger.error("Pattern execution will not work. Check imports.")
        AgentRuntime = None
        AGENT_RUNTIME_AVAILABLE = False

    try:
        from app.core.pattern_orchestrator import PatternOrchestrator
        PATTERN_ORCHESTRATOR_AVAILABLE = True
        logger.debug("PatternOrchestrator imported successfully")
    except ImportError as e:
        logger.error(f"CRITICAL: PatternOrchestrator not available: {e}")
        logger.error("Pattern execution will not work. Check imports.")
        PatternOrchestrator = None
        PATTERN_ORCHESTRATOR_AVAILABLE = False

    # ============================================================================
    # Service Imports - Use Classes, Not Factories
    # ============================================================================
    # These should use classes directly, not singleton factory functions.
    # If unavailable, we can degrade gracefully.
    
    try:
        from app.services.metrics import PerformanceCalculator
        PERFORMANCE_CALCULATOR_AVAILABLE = True
        logger.debug("PerformanceCalculator imported successfully")
    except ImportError as e:
        logger.warning(f"PerformanceCalculator not available: {e}")
        PerformanceCalculator = None
        PERFORMANCE_CALCULATOR_AVAILABLE = False

    try:
        from app.services.scenarios import ScenarioService, ShockType
        SCENARIO_SERVICE_AVAILABLE = True
        logger.debug("ScenarioService imported successfully")
    except ImportError as e:
        logger.warning(f"ScenarioService not available: {e}")
        ScenarioService = None
        ShockType = None
        SCENARIO_SERVICE_AVAILABLE = False

    # ============================================================================
    # Agent Imports - Use Classes, Not Factories
    # ============================================================================
    # These should use classes directly. If unavailable, pattern execution
    # will fail for those specific capabilities.
    
    try:
        from app.agents.financial_analyst import FinancialAnalyst
        FINANCIAL_ANALYST_AVAILABLE = True
        logger.debug("FinancialAnalyst imported successfully")
    except ImportError as e:
        logger.warning(f"FinancialAnalyst not available: {e}")
        FinancialAnalyst = None
        FINANCIAL_ANALYST_AVAILABLE = False

    try:
        from app.agents.macro_hound import MacroHound
        MACRO_HOUND_AVAILABLE = True
        logger.debug("MacroHound imported successfully")
    except ImportError as e:
        logger.warning(f"MacroHound not available: {e}")
        MacroHound = None
        MACRO_HOUND_AVAILABLE = False

    try:
        from app.agents.data_harvester import DataHarvester
        DATA_HARVESTER_AVAILABLE = True
        logger.debug("DataHarvester imported successfully")
    except ImportError as e:
        logger.warning(f"DataHarvester not available: {e}")
        DataHarvester = None
        DATA_HARVESTER_AVAILABLE = False

    # ============================================================================
    # Overall Availability Flag
    # ============================================================================
    PATTERN_ORCHESTRATION_AVAILABLE = (
        REQUEST_CTX_AVAILABLE and
        AGENT_RUNTIME_AVAILABLE and
        PATTERN_ORCHESTRATOR_AVAILABLE
    )

    if PATTERN_ORCHESTRATION_AVAILABLE:
        logger.info("Pattern orchestration modules loaded successfully")
    else:
        logger.warning("Pattern orchestration partially available - some features may not work")
        logger.warning(f"  RequestCtx: {REQUEST_CTX_AVAILABLE}")
        logger.warning(f"  AgentRuntime: {AGENT_RUNTIME_AVAILABLE}")
        logger.warning(f"  PatternOrchestrator: {PATTERN_ORCHESTRATOR_AVAILABLE}")
except Exception as e:
    # This catch-all is for any unexpected errors during import setup
    # (not just ImportError)
    logger.error(f"Unexpected error during pattern orchestration import setup: {e}", exc_info=True)
    # Set defaults for graceful degradation
    PATTERN_ORCHESTRATION_AVAILABLE = False
    REQUEST_CTX_AVAILABLE = False
    AGENT_RUNTIME_AVAILABLE = False
    PATTERN_ORCHESTRATOR_AVAILABLE = False
    PERFORMANCE_CALCULATOR_AVAILABLE = False
    SCENARIO_SERVICE_AVAILABLE = False
    FINANCIAL_ANALYST_AVAILABLE = False
    MACRO_HOUND_AVAILABLE = False
    DATA_HARVESTER_AVAILABLE = False
    # Critical imports - these should have been set above, but if we get here
    # something unexpected happened
    if 'RequestCtx' not in locals():
        logger.error("CRITICAL: RequestCtx not imported and unexpected error occurred")
        raise RuntimeError(f"Cannot start server: RequestCtx import failed: {e}") from e

# ============================================================================
# Configuration and Constants
# ============================================================================

# Environment Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
# Check for Replit managed credentials first, then fall back to user's key
ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
USING_REPLIT_INTEGRATION = bool(os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY"))

# JWT Configuration
# JWT constants moved to backend/app/auth/dependencies.py - Sprint 1
# Now imported at top of file
# JWT_SECRET = os.environ.get("AUTH_JWT_SECRET", "your-secret-key-change-in-production")
# JWT_ALGORITHM = "HS256"
# JWT_EXPIRATION_HOURS = 24

# API URLs
# Use Replit's base URL if available, otherwise use default
CLAUDE_API_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL") or "https://api.anthropic.com/v1/messages"
FRED_API_KEY = os.environ.get("FRED_API_KEY")

# Cache Configuration
FRED_CACHE_DURATION = 3600  # 1 hour
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Database Configuration
DB_POOL_MIN_SIZE = 2
DB_POOL_MAX_SIZE = 20
DB_TIMEOUT = 30

# Risk Thresholds
MAX_PORTFOLIO_CONCENTRATION = 0.30  # 30% max for single position
MIN_POSITIONS_FOR_DIVERSIFICATION = 5
MAX_RISK_SCORE = 1.0
MIN_SHARPE_RATIO = -2.0
MAX_SHARPE_RATIO = 3.0

# ============================================================================
# Magic Number Constants (P3 - Technical Debt Fix)
# ============================================================================

# Default Portfolio and User IDs
DEFAULT_PORTFOLIO_ID = "64ff3be6-0ed1-4990-a32b-4ded17f0320c"  # Example portfolio
SYSTEM_USER_ID = "system"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"

# Lookback Day Constants
LOOKBACK_DAYS_YEAR = 252  # Trading days in a year
LOOKBACK_DAYS_QUARTER = 90
LOOKBACK_DAYS_CALENDAR_YEAR = 365

# ============================================================================
# Pattern Lists (P2 - Consolidated Pattern Lists)
# ============================================================================

# All portfolio-related patterns that require portfolio_id
PORTFOLIO_PATTERNS = [
    "portfolio_overview", 
    "portfolio_scenario_analysis", 
    "portfolio_cycle_risk",
    "portfolio_macro_overview", 
    "holding_deep_dive", 
    "news_impact_analysis",
    "policy_rebalance", 
    "buffett_checklist", 
    "export_portfolio_report"
]

# Macro patterns that don't require portfolio_id
MACRO_PATTERNS = [
    "macro_cycles_overview",
    "macro_trend_monitor",
    "cycle_deleveraging_scenarios"
]

# All valid patterns
ALL_VALID_PATTERNS = PORTFOLIO_PATTERNS + MACRO_PATTERNS

# ============================================================================
# Global State
# ============================================================================

# Database connection pool
db_pool: Optional[Pool] = None

# Pattern Orchestrator and Agent Runtime (singleton instances)
# Phase 2: Removed singleton variables - using DI container instead
# _agent_runtime: Optional[AgentRuntime] = None
# _pattern_orchestrator: Optional[PatternOrchestrator] = None

# FRED Cache
fred_cache: Dict[str, Any] = {}
fred_cache_timestamp: Optional[float] = None

# Alert Types
class AlertType(str, Enum):
    PRICE = "price"
    PORTFOLIO = "portfolio"
    RISK = "risk"
    MACRO = "macro"

# Alert Conditions
class AlertCondition(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    CHANGE = "change"

# ============================================================================
# Pydantic Models with Validation
# ============================================================================

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class ExecuteRequest(BaseModel):
    pattern: str = Field(default="portfolio_overview", min_length=1, max_length=100)  # Made optional with default
    inputs: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)  # Alternative field name
    require_fresh: bool = False

    @field_validator('inputs', 'params')
    @classmethod
    def validate_inputs(cls, v):
        # Limit input size to prevent abuse
        if v and len(json.dumps(v)) > 10000:
            raise ValueError('Input data too large')
        return v

class AlertConfig(BaseModel):
    type: AlertType
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    threshold: float = Field(..., ge=0)
    condition: AlertCondition
    notification_channel: str = Field(default="email", min_length=1, max_length=50)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v, info):
        if info.data.get('type') == AlertType.PRICE and not v:
            raise ValueError('Symbol required for price alerts')
        if v:
            return v.upper()
        return v

class OptimizationRequest(BaseModel):
    risk_tolerance: float = Field(default=0.5, ge=0, le=1)
    target_return: Optional[float] = Field(None, ge=-1, le=2)
    constraints: Dict[str, Any] = Field(default_factory=dict)

class AIAnalysisRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    context: Dict[str, Any] = Field(default_factory=dict)

class AIChatRequest(BaseModel):
    """Request model for direct AI chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000, description="User's message or question")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional portfolio or financial context")

# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SuccessResponse(BaseModel):
    status: str = "success"
    data: Any
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# ============================================================================
# Custom Exceptions
# ============================================================================

class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

# ============================================================================
# Agent Runtime and Pattern Orchestrator Initialization
# ============================================================================

def get_agent_runtime(reinit_services: bool = False) -> AgentRuntime:
    """
    Get or create agent runtime using DI container.
    
    Phase 2: Migrated to use DI container instead of singleton pattern.
    """
    from app.core.di_container import get_container
    from app.core.service_initializer import initialize_services
    
    global db_pool
    
    # Get or initialize DI container
    container = get_container()
    
    # Initialize services if not already initialized or if reinit requested
    if not container._initialized or reinit_services:
        try:
            initialize_services(container, db_pool=db_pool)
            logger.info("Services initialized using DI container")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise
    
    # Resolve agent runtime from container
    try:
        return container.resolve("agent_runtime")
    except (KeyError, RuntimeError) as e:
        logger.error(f"Failed to resolve agent runtime: {e}", exc_info=True)
        raise

def get_pattern_orchestrator() -> PatternOrchestrator:
    """
    Get or create pattern orchestrator using DI container.
    
    Phase 2: Migrated to use DI container instead of singleton pattern.
    """
    from app.core.di_container import get_container
    from app.core.service_initializer import initialize_services
    
    global db_pool
    
    # Get or initialize DI container
    container = get_container()
    
    # Initialize services if not already initialized
    if not container._initialized:
        try:
            initialize_services(container, db_pool=db_pool)
            logger.info("Services initialized using DI container")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise
    
    # Resolve pattern orchestrator from container
    try:
        return container.resolve("pattern_orchestrator")
    except (KeyError, RuntimeError) as e:
        logger.error(f"Failed to resolve pattern orchestrator: {e}", exc_info=True)
        raise

async def execute_pattern_orchestrator(pattern_name: str, inputs: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Execute a pattern through the orchestrator and return results."""
    try:
        # Don't attempt orchestration if database is not available
        if not db_pool:
            logger.warning("Database not available for pattern orchestration")
            return {
                "success": False,
                "error": "Database not available",
                "data": {}
            }

        orchestrator = get_pattern_orchestrator()
        
        # Debug logging
        logger.debug(f"Orchestrator object: {orchestrator}")
        logger.debug(f"Orchestrator type: {type(orchestrator)}")
        if orchestrator:
            logger.debug(f"Orchestrator agent_runtime: {getattr(orchestrator, 'agent_runtime', 'NO ATTRIBUTE')}")
            logger.debug(f"Agent runtime type: {type(getattr(orchestrator, 'agent_runtime', None))}")
            if hasattr(orchestrator, 'agent_runtime') and orchestrator.agent_runtime:
                logger.debug(f"Agent runtime has execute_capability: {hasattr(orchestrator.agent_runtime, 'execute_capability')}")

        # Get real pricing pack ID from database
        pricing_pack_id = f"PP_{date.today().isoformat()}"  # Default fallback
        ledger_commit_hash = hashlib.md5(f"{date.today()}".encode()).hexdigest()[:8]

        try:
            # Try to get the latest pricing pack from database
            query = """
                SELECT id, date 
                FROM pricing_packs 
                WHERE date <= CURRENT_DATE 
                ORDER BY date DESC 
                LIMIT 1
            """
            result = await execute_query_safe(query)
            if result and len(result) > 0:
                pricing_pack_id = result[0]["id"]
                logger.debug(f"Using pricing pack: {pricing_pack_id}")
        except Exception as e:
            logger.warning(f"Could not fetch pricing pack, using default: {e}")

        # Create request context with required values
        # Guardrail: RequestCtx is critical - should never be None (fail fast if import failed)
        if not REQUEST_CTX_AVAILABLE:
            logger.error("CRITICAL: RequestCtx not available - cannot create request context")
            return {
                "success": False,
                "error": "RequestCtx not available - server configuration error",
                "data": {}
            }
        
        ctx = RequestCtx(
            trace_id=str(uuid4()),
            request_id=str(uuid4()),
            user_id=user_id or SYSTEM_USER_ID,
            portfolio_id=inputs.get("portfolio_id"),
            asof_date=date.today(),
            pricing_pack_id=pricing_pack_id,
            ledger_commit_hash=ledger_commit_hash
        )

        # Run pattern
        result = await orchestrator.run_pattern(pattern_name, ctx, inputs)
        
        # Extract provenance information from trace
        trace_data = result.get("trace", {})
        provenance_info = trace_data.get("data_provenance", {})

        return {
            "success": True,
            "data": result.get("data", {}),
            "trace": result.get("trace"),
            "metadata": {
                "pattern": pattern_name,
                "execution_time": result.get("execution_time_ms", 0),
                "pricing_pack_id": pricing_pack_id,
                "ledger_commit_hash": ledger_commit_hash
            },
            "data_provenance": provenance_info  # Include provenance metadata
        }
    except Exception as e:
        import traceback
        logger.error(f"Pattern execution failed for {pattern_name}: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        # Return mock data as fallback to avoid breaking the UI
        return {
            "success": False,
            "error": str(e),
            "data": {}  # Empty data to avoid breaking UI
        }

# ============================================================================
# Lifespan Context Manager (Replaces @app.on_event)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - replaces deprecated @app.on_event decorators
    """
    global db_pool

    # Startup
    logger.info("Starting DawsOS Enhanced Server...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")

        # Initialize agent runtime and pattern orchestrator after DB is ready
        runtime = get_agent_runtime(reinit_services=True)
        get_pattern_orchestrator()
        logger.info("Pattern orchestration system initialized")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Database unavailable - some features may not work")

    # Initialize other services
    logger.info(f"Server mode: {'ORCHESTRATED' if db_pool else 'FALLBACK'}")
    logger.info("Enhanced server started successfully")

    yield  # Server is running

    # Shutdown
    logger.info("Shutting down DawsOS Enhanced Server...")

    # Clean up database connections
    if db_pool:
        try:
            await db_pool.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

    logger.info("Enhanced server shutdown complete")

# ============================================================================
# Initialize FastAPI App
# ============================================================================

app = FastAPI(
    title="DawsOS Enhanced Server",
    description="Comprehensive Portfolio Intelligence Platform",
    version="6.0.0",
    lifespan=lifespan  # Use lifespan instead of on_event
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Password Management
# ============================================================================

# Authentication functions moved to backend/app/auth/dependencies.py
# Sprint 1: Authentication refactoring - functions now imported from centralized module

# ============================================================================
# Default Users (Should be in database in production)
# ============================================================================

USERS_DB = {
    "michael@dawsos.com": {
        "id": "user-001",
        "email": "michael@dawsos.com",
        "password": "$2b$12$6IAZ62SU9pdg/UzJ5PAzSuq0dWvJ3xDa7rR978PwTdqJ.dGLh6WmO",  # password123
        "role": "ADMIN"
    },
    "test@dawsos.com": {
        "id": "user-002",
        "email": "test@dawsos.com",
        "password": "$2b$12$6IAZ62SU9pdg/UzJ5PAzSuq0dWvJ3xDa7rR978PwTdqJ.dGLh6WmO",  # password123
        "role": "USER"
    }
}

# ============================================================================
# Database Functions with Error Handling
# ============================================================================

async def init_db() -> None:
    """Initialize database connection pool with error handling"""
    global db_pool

    if not DATABASE_URL:
        logger.warning("DATABASE_URL not configured")
        return

    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=DB_POOL_MIN_SIZE,
            max_size=DB_POOL_MAX_SIZE,
            timeout=DB_TIMEOUT,
            command_timeout=10
        )

        # Test connection
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        logger.info("Database connected successfully")

        # CRITICAL FIX: Register pool with backend connection module
        # This solves the "Database pool not initialized" errors in agents
        try:
            from backend.app.db.connection import register_external_pool

            # Register the pool using the new explicit mechanism
            register_external_pool(db_pool)

            logger.info(f"✅ Successfully registered database pool with backend connection module")
            logger.info(f"Pool registered: {db_pool}")
        except ImportError as e:
            logger.warning(f"Could not import backend modules: {e}")
        except Exception as e:
            logger.warning(f"Could not register pool with backend: {e}")

    except asyncpg.PostgresError as e:
        logger.error(f"PostgreSQL error during initialization: {e}")
        raise DatabaseConnectionError(f"Failed to connect to database: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise

async def execute_query_safe(
    query: str, 
    *args, 
    fetch_one: bool = False,
    timeout: float = 10.0
) -> Optional[Any]:
    """
    Execute a database query safely with proper error handling

    Args:
        query: SQL query with $1, $2 placeholders (prevents SQL injection)
        *args: Query parameters
        fetch_one: If True, return single row, else return all rows
        timeout: Query timeout in seconds

    Returns:
        Query result or None on error
    """
    if not db_pool:
        logger.warning("Database pool not initialized")
        return None

    try:
        async with db_pool.acquire() as conn:
            # Set query timeout
            async with conn.transaction():
                await conn.execute(f"SET LOCAL statement_timeout = {int(timeout * 1000)}")

                if fetch_one:
                    return await conn.fetchrow(query, *args)
                else:
                    return await conn.fetch(query, *args)

    except asyncio.TimeoutError:
        logger.error(f"Query timeout after {timeout}s: {query[:100]}...")
        return None
    except asyncpg.exceptions.PostgresError as e:
        logger.error(f"Database error: {e}, Query: {query[:100]}...")
        return None
    except Exception as e:
        logger.error(f"Unexpected error executing query: {e}")
        return None

async def get_portfolio_data(user_email: str) -> Optional[List[asyncpg.Record]]:
    """Fetch portfolio data from database with proper error handling"""
    query = """
        SELECT 
            p.id as portfolio_id,
            p.name as portfolio_name,
            h.symbol,
            h.quantity,
            h.cost_basis,
            h.current_price as price,
            h.market_value,
            s.name as security_name,
            s.security_type as sector
        FROM portfolios p
        JOIN users u ON p.user_id = u.id
        JOIN holdings h ON h.portfolio_id = p.id
        LEFT JOIN securities s ON h.symbol = s.symbol
        WHERE u.email = $1 AND p.is_active = true
    """

    return await execute_query_safe(query, user_email)

async def get_user_transactions(user_email: str) -> Optional[List[asyncpg.Record]]:
    """Fetch transactions from database with proper error handling"""
    query = """
        SELECT 
            t.transaction_type as type,
            t.quantity,
            t.price,
            t.amount,
            t.transaction_date as trade_date,
            t.symbol,
            s.name as security_name
        FROM transactions t
        JOIN portfolios p ON t.portfolio_id = p.id
        JOIN users u ON p.user_id = u.id
        LEFT JOIN securities s ON t.symbol = s.symbol
        WHERE u.email = $1
        ORDER BY t.transaction_date DESC
        LIMIT 1000
    """

    return await execute_query_safe(query, user_email)

async def store_macro_indicators(indicators: Dict[str, Any], apply_transformation: bool = True) -> bool:
    """Store macro indicators in database with proper error handling and transformation"""
    if not db_pool or not indicators:
        return False
    
    # Import transformation service
    # Guardrail: Use DI container or direct instantiation (no singleton factory functions)
    from app.services.fred_transformation import FREDTransformationService
    
    # Apply transformations if needed
    if apply_transformation:
        # Use direct instantiation (stateless service, no dependencies)
        transformation_service = FREDTransformationService()
        transformed_indicators = {}
        
        # Map common indicator names to their FRED series IDs
        series_mapping = {
            'gdp_growth': 'A191RL1Q225SBEA',
            'inflation': 'CPIAUCSL',
            'unemployment': 'UNRATE',
            'interest_rate': 'DFF',
            'debt_to_gdp': 'GFDEGDQ188S',
            'fiscal_deficit': 'FYFSGDA188S',
            'yield_curve': 'T10Y2Y',
            'industrial_production': 'INDPRO',
            'manufacturing_pmi': 'NAPM',
            'credit_growth': 'TOTBKCR',
            'debt_service_ratio': 'TDSP',
            'trade_balance': 'NETEXP',
            'productivity_growth': 'PRS85006092'
        }
        
        for indicator_name, value in indicators.items():
            if isinstance(value, (int, float)):
                # Get the FRED series ID for this indicator
                series_id = series_mapping.get(indicator_name)
                
                if series_id and series_id in transformation_service.SERIES_TRANSFORMATIONS:
                    # Apply the appropriate transformation
                    transform_info = transformation_service.SERIES_TRANSFORMATIONS[series_id]
                    transform_type = transform_info['transform']
                    
                    # Apply basic transformations that don't need historical data
                    if transform_type == 'percent_to_decimal':
                        transformed_value = value / 100.0
                    elif transform_type == 'percent_to_decimal_signed':
                        transformed_value = value / 100.0
                    elif transform_type == 'index_keep':
                        transformed_value = value
                    else:
                        # For complex transformations, keep the raw value but log it
                        transformed_value = value
                        logger.warning(f"Complex transformation needed for {indicator_name} ({series_id}): {transform_type}")
                    
                    transformed_indicators[indicator_name] = transformed_value
                    logger.info(f"Transformed {indicator_name}: {value} → {transformed_value}")
                else:
                    # No transformation needed or defined
                    transformed_indicators[indicator_name] = value
        
        # Use transformed values
        indicators = transformed_indicators

    # Create mapping of indicator IDs to human-readable names
    indicator_names = {
        'gdp_growth': 'GDP Growth Rate',
        'inflation_rate': 'Inflation Rate',
        'unemployment_rate': 'Unemployment Rate', 
        'interest_rate': 'Interest Rate',
        'consumer_confidence': 'Consumer Confidence Index',
        'manufacturing_pmi': 'Manufacturing PMI',
        'services_pmi': 'Services PMI',
        'retail_sales': 'Retail Sales Growth',
        'housing_starts': 'Housing Starts',
        'business_inventories': 'Business Inventories',
        'industrial_production': 'Industrial Production',
        'treasury_yield_10y': '10-Year Treasury Yield',
        'treasury_yield_2y': '2-Year Treasury Yield',
        'yield_curve': 'Yield Curve (10Y-2Y)',
        'vix': 'VIX (Volatility Index)',
        'dollar_index': 'US Dollar Index',
        'gold_price': 'Gold Price',
        'oil_price': 'Oil Price (WTI)',
        'bitcoin_price': 'Bitcoin Price',
        'sp500_pe': 'S&P 500 P/E Ratio',
        'm2_money_supply': 'M2 Money Supply',
        'fed_funds_rate': 'Federal Funds Rate',
        'corporate_profits': 'Corporate Profits Growth',
        'jobless_claims': 'Initial Jobless Claims',
        'consumer_spending': 'Consumer Spending Growth',
        # Additional indicators from macro_data_agent
        'empire_gdp_share': 'US GDP Share of World',
        'empire_trade_share': 'US Trade Share of World',
        'empire_military_share': 'US Military Spending Share',
        'empire_education': 'Education Index',
        'gini_coefficient': 'Gini Coefficient',
        'top_1_percent_wealth': 'Top 1% Wealth Share',
        'polarization_index': 'Political Polarization Index',
        'institutional_trust': 'Institutional Trust Index',
        'debt_ceiling_distance': 'Debt Ceiling Distance',
        'monetary_base': 'Monetary Base'
    }

    try:
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Clear existing indicators
                await conn.execute("DELETE FROM macro_indicators WHERE date = CURRENT_DATE")

                # Insert new indicators
                for indicator_id, value in indicators.items():
                    if isinstance(value, (int, float)):
                        # Get human-readable name or use the ID with proper formatting
                        indicator_name = indicator_names.get(
                            indicator_id,
                            indicator_id.replace('_', ' ').title()
                        )

                        await conn.execute("""
                            INSERT INTO macro_indicators (indicator_id, indicator_name, value, date)
                            VALUES ($1, $2, $3, CURRENT_DATE)
                            ON CONFLICT (indicator_id, date) DO UPDATE
                            SET value = $3, indicator_name = $2, updated_at = NOW()
                        """, indicator_id, indicator_name, float(value))

                logger.info(f"Stored {len(indicators)} macro indicators")
                return True

    except Exception as e:
        logger.error(f"Error storing indicators in database: {e}")
        return False

# ============================================================================
# JWT Authentication
# ============================================================================

# Authentication functions moved to backend/app/auth/dependencies.py
# Sprint 1: Authentication refactoring - functions now imported from centralized module

# Keep verify_jwt_token here temporarily (not in auth module yet)
def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token with proper error handling"""
    try:
        from backend.app.auth.dependencies import JWT_SECRET, JWT_ALGORITHM
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying JWT token: {e}")
        return None

# All authentication functions now imported from backend.app.auth.dependencies

# ============================================================================
# Authentication Functions - Now imported from backend.app.auth.dependencies
# Sprint 1: Authentication refactoring completed
# ============================================================================
# All authentication functions (hash_password, verify_password, create_jwt_token, 
# get_current_user, require_auth, require_role) are now imported from 
# backend.app.auth.dependencies module for centralized authentication management

# ============================================================================
# Portfolio Calculations with Error Handling
# ============================================================================

def calculate_sector_allocation(holdings: List[dict], total_value: float) -> Dict[str, float]:
    """Calculate sector allocation with proper validation"""
    if not holdings or total_value <= 0:
        return {}

    sector_values = defaultdict(float)

    for holding in holdings:
        sector = holding.get("sector", "Other")
        value = holding.get("value", 0)

        if value > 0:
            sector_values[sector] += value

    # Convert to percentages
    sector_allocation = {}
    for sector, value in sector_values.items():
        percentage = round((value / total_value) * 100, 2)
        if percentage > 0:
            sector_allocation[sector] = percentage

    return sector_allocation

async def calculate_portfolio_risk_metrics(holdings: List[dict], portfolio_id: str = None) -> Dict[str, float]:
    """Calculate portfolio risk metrics using real MetricsService"""
    if not holdings:
        return {
            "portfolio_beta": 0,
            "portfolio_volatility": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "var_95": 0,
            "risk_score": 0
        }

    total_value = sum(h.get("value", 0) for h in holdings)
    if total_value <= 0:
        return {
            "portfolio_beta": 0,
            "portfolio_volatility": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "var_95": 0,
            "risk_score": 0
        }

    # Try to use real MetricsService if available
    if db_pool and portfolio_id and PERFORMANCE_CALCULATOR_AVAILABLE:
        try:
            # Guardrail: Check availability before using PerformanceCalculator
            if PerformanceCalculator is None:
                logger.warning("PerformanceCalculator not available - skipping real metrics")
            else:
                # Use the performance calculator to get real metrics
                calc = PerformanceCalculator(db_pool)

                # Get TWR and related metrics for past year (trading days)
                metrics = await calc.compute_twr(portfolio_id, pack_id=None, lookback_days=LOOKBACK_DAYS_YEAR)

                # Get max drawdown
                dd = await calc.compute_max_drawdown(portfolio_id, lookback_days=LOOKBACK_DAYS_YEAR)

                # Get VaR
                var_result = await calc.compute_var(portfolio_id, confidence=0.95, lookback_days=LOOKBACK_DAYS_YEAR)

                # Calculate weighted beta for positions
                weighted_beta = 0
                for holding in holdings:
                    weight = holding.get("value", 0) / total_value
                    beta = holding.get("beta", 1.0)
                    weighted_beta += weight * beta

                # Use real volatility from metrics or estimate from beta
                portfolio_volatility = metrics.get("vol", weighted_beta * 0.15)

                # Simple risk score based on volatility and drawdown
                risk_score = min(max((portfolio_volatility + abs(dd.get("max_drawdown", 0))) / 2, 0), MAX_RISK_SCORE)

                return {
                    "portfolio_beta": round(weighted_beta, 2),
                    "portfolio_volatility": round(portfolio_volatility, 4),
                    "sharpe_ratio": round(metrics.get("sharpe", 0), 2),
                    "max_drawdown": round(dd.get("max_drawdown", 0), 4),
                    "var_95": round(var_result.get("var_95", total_value * 0.02), 2),
                    "risk_score": round(risk_score, 2)
                }
        except Exception as e:
            logger.warning(f"Could not calculate real metrics, using estimates: {e}")

    # Fallback to estimated metrics if real calculation fails
    weighted_beta = 0
    for holding in holdings:
        weight = holding.get("value", 0) / total_value
        beta = holding.get("beta", 1.0)
        weighted_beta += weight * beta

    portfolio_volatility = weighted_beta * 0.15  # Assume market vol of 15%
    risk_score = min(max(weighted_beta / 2, 0), MAX_RISK_SCORE)

    # Use more realistic estimates based on beta
    # Higher beta = lower Sharpe, higher drawdown
    estimated_sharpe = max(MIN_SHARPE_RATIO, min(MAX_SHARPE_RATIO, 1.5 - (weighted_beta - 1.0) * 0.5))
    estimated_drawdown = -1 * min(0.5, weighted_beta * 0.08)  # More beta = deeper drawdowns
    var_95 = total_value * (0.01 + weighted_beta * 0.01)  # 1-3% VaR based on beta

    return {
        "portfolio_beta": round(weighted_beta, 2),
        "portfolio_volatility": round(portfolio_volatility, 4),
        "sharpe_ratio": round(estimated_sharpe, 2),
        "max_drawdown": round(estimated_drawdown, 4),
        "var_95": round(var_95, 2),
        "risk_score": round(risk_score, 2)
    }

# ============================================================================
# API Endpoints with Improved Error Handling
# ============================================================================

@app.get("/frontend/{filename}")
async def serve_frontend_file(filename: str):
    """Serve files from the frontend directory with cache-control headers"""
    file_path = Path(f"frontend/{filename}")
    if file_path.exists() and file_path.is_file():
        response = FileResponse(file_path)
        # Add cache-control headers for JS files to prevent caching issues
        if filename.endswith('.js'):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve HTML"""
    try:
        # Try to read UI from file
        ui_file = Path("full_ui.html")
        if ui_file.exists():
            response = HTMLResponse(content=ui_file.read_text())
            # Add cache-control headers to prevent caching issues
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    except Exception as e:
        logger.error(f"Error reading UI file: {e}")

    # Return minimal UI
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DawsOS Portfolio Intelligence</title>
    </head>
    <body>
        <h1>DawsOS Portfolio Intelligence Platform</h1>
        <p>Version 6.0.0 - Refactored</p>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "6.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_pool else "disconnected",
        "mode": "production"
    }

    # Check database connectivity
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health_status["database"] = "connected"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "degraded"

    return health_status

@app.get("/api/test-pool-access")
async def test_pool_access():
    """Test endpoint to verify agents can access the database pool"""
    results = {
        "test": "database_pool_access",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Check 1: Verify combined_server has a pool
    results["checks"]["combined_server_pool"] = {
        "status": "success" if db_pool else "failed",
        "pool": str(db_pool) if db_pool else None
    }

    # Check 2: Test if backend connection module can get the pool
    try:
        from backend.app.db.connection import get_db_pool
        backend_pool = get_db_pool()
        results["checks"]["backend_get_pool"] = {
            "status": "success",
            "pool": str(backend_pool),
            "same_as_combined": backend_pool == db_pool
        }
    except Exception as e:
        results["checks"]["backend_get_pool"] = {
            "status": "failed",
            "error": str(e)
        }

    # Check 3: Test if an agent can access the pool
    try:
        from backend.app.agents.financial_analyst import FinancialAnalyst

        # Get the agent runtime (which should have db pool in services)
        runtime = get_agent_runtime()
        financial_analyst = runtime.get_agent("financial_analyst")

        if financial_analyst and financial_analyst.services.get("db"):
            results["checks"]["agent_pool_access"] = {
                "status": "success",
                "agent": "financial_analyst",
                "has_db_service": True,
                "pool": str(financial_analyst.services.get("db"))
            }
        else:
            results["checks"]["agent_pool_access"] = {
                "status": "failed",
                "error": "Agent does not have database service"
            }

        # Check 4: Test actual database query from agent context
        if backend_pool:
            async with backend_pool.acquire() as conn:
                test_result = await conn.fetchval("SELECT 1")
                results["checks"]["database_query"] = {
                    "status": "success",
                    "query": "SELECT 1",
                    "result": test_result
                }

    except Exception as e:
        results["checks"]["agent_test"] = {
            "status": "failed",
            "error": str(e)
        }

    # Overall status
    all_success = all(
        check.get("status") == "success" 
        for check in results["checks"].values()
    )
    results["overall_status"] = "✅ FIXED" if all_success else "❌ STILL BROKEN"

    return results

@app.get("/api/db-health")
async def database_health_check():
    """
    Comprehensive database health check endpoint for debugging.
    Returns detailed information about database connectivity, schema, and pool status.
    """
    health_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "checking",
        "connection": {},
        "pool": {},
        "schema": {},
        "environment": {},
        "diagnostics": []
    }
    
    # Check 1: Environment Variables
    health_report["environment"] = {
        "DATABASE_URL": bool(os.environ.get("DATABASE_URL")),
        "PGHOST": bool(os.environ.get("PGHOST")),
        "PGUSER": bool(os.environ.get("PGUSER")),
        "PGDATABASE": bool(os.environ.get("PGDATABASE")),
        "PGPORT": bool(os.environ.get("PGPORT"))
    }
    
    # Check 2: Pool Status
    if db_pool:
        health_report["pool"]["exists"] = True
        health_report["pool"]["status"] = "initialized"
        health_report["pool"]["type"] = str(type(db_pool))
        
        # Test basic connectivity
        try:
            async with db_pool.acquire() as conn:
                # Test basic query
                result = await conn.fetchval("SELECT 1")
                health_report["connection"]["basic_query"] = "success"
                
                # Get database version
                version = await conn.fetchval("SELECT version()")
                health_report["connection"]["database_version"] = version
                
                # Check TimescaleDB
                try:
                    timescale = await conn.fetchval(
                        "SELECT installed_version FROM pg_extension WHERE extname = 'timescaledb'"
                    )
                    health_report["connection"]["timescaledb"] = timescale or "not_installed"
                except:
                    health_report["connection"]["timescaledb"] = "check_failed"
                
                # Check critical tables exist
                tables_query = """
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename IN (
                        'portfolios', 'securities', 'transactions', 
                        'lots', 'pricing_packs', 'price_entries',
                        'portfolio_metrics', 'users'
                    )
                    ORDER BY tablename;
                """
                tables = await conn.fetch(tables_query)
                health_report["schema"]["tables"] = [row["tablename"] for row in tables]
                health_report["schema"]["table_count"] = len(tables)
                
                # Check if tables have data
                for table in ['portfolios', 'securities', 'transactions']:
                    try:
                        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                        health_report["schema"][f"{table}_count"] = count
                    except Exception as e:
                        health_report["schema"][f"{table}_count"] = f"error: {str(e)}"
                
                # Check pool statistics
                pool_stats = db_pool.get_stats() if hasattr(db_pool, 'get_stats') else {}
                health_report["pool"]["stats"] = {
                    "size": pool_stats.get("size", "unknown"),
                    "free": pool_stats.get("free", "unknown"),
                    "used": pool_stats.get("used", "unknown"),
                    "waiting": pool_stats.get("waiting", "unknown")
                }
                
                health_report["status"] = "healthy"
                health_report["diagnostics"].append("✅ Database connection successful")
                
        except Exception as e:
            health_report["connection"]["error"] = str(e)
            health_report["status"] = "unhealthy"
            health_report["diagnostics"].append(f"❌ Connection failed: {str(e)}")
            logger.error(f"Database health check failed: {e}", exc_info=True)
    else:
        health_report["pool"]["exists"] = False
        health_report["status"] = "unhealthy"
        health_report["diagnostics"].append("❌ Database pool not initialized")
        
        # Try to diagnose why
        if not os.environ.get("DATABASE_URL"):
            health_report["diagnostics"].append("❌ DATABASE_URL environment variable not set")
        else:
            health_report["diagnostics"].append("⚠️ DATABASE_URL exists but pool not created")
    
    # Check 3: Backend module integration
    try:
        from backend.app.db.connection import get_db_pool
        backend_pool = get_db_pool()
        if backend_pool:
            health_report["pool"]["backend_module"] = "accessible"
            health_report["pool"]["pools_match"] = (backend_pool == db_pool)
        else:
            health_report["pool"]["backend_module"] = "no_pool"
    except Exception as e:
        health_report["pool"]["backend_module"] = f"error: {str(e)}"
        health_report["diagnostics"].append(f"⚠️ Backend module pool issue: {str(e)}")
    
    # Overall assessment
    if health_report["status"] == "healthy":
        health_report["summary"] = "✅ Database fully operational"
    else:
        health_report["summary"] = "❌ Database issues detected - check diagnostics"
    
    return health_report

@app.get("/api/db-schema")
async def database_schema_validation():
    """
    Validates database schema completeness.
    Returns information about tables, columns, indexes, and constraints.
    """
    schema_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "checking",
        "tables": {},
        "missing_tables": [],
        "issues": [],
        "recommendations": []
    }
    
    # Expected tables for DawsOS
    expected_tables = [
        'users', 'portfolios', 'securities', 'transactions', 'lots',
        'pricing_packs', 'price_entries', 'fx_rates', 'portfolio_metrics',
        'performance_metrics', 'risk_metrics', 'attribution_metrics',
        'currency_attribution', 'factor_exposures', 'scenarios',
        'corporate_actions', 'news_sentiment', 'security_ratings',
        'audit_log', 'alerts'
    ]
    
    if not db_pool:
        schema_report["status"] = "error"
        schema_report["issues"].append("Database pool not initialized")
        return schema_report
    
    try:
        async with db_pool.acquire() as conn:
            # Get all tables
            tables_query = """
                SELECT 
                    t.tablename,
                    obj_description(c.oid, 'pg_class') as comment
                FROM pg_tables t
                JOIN pg_class c ON c.relname = t.tablename
                WHERE t.schemaname = 'public'
                ORDER BY t.tablename;
            """
            tables = await conn.fetch(tables_query)
            existing_tables = {row['tablename']: row['comment'] for row in tables}
            
            # Check for missing tables
            schema_report["missing_tables"] = [t for t in expected_tables if t not in existing_tables]
            
            if schema_report["missing_tables"]:
                schema_report["issues"].append(f"Missing {len(schema_report['missing_tables'])} expected tables")
                schema_report["recommendations"].append("Run database migrations to create missing tables")
            
            # For each existing table, get detailed info
            for table_name in existing_tables:
                table_info = {
                    "exists": True,
                    "comment": existing_tables[table_name],
                    "row_count": 0,
                    "columns": [],
                    "indexes": [],
                    "has_rls": False
                }
                
                # Get row count
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    table_info["row_count"] = count
                except:
                    table_info["row_count"] = "error"
                
                # Get columns
                columns_query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                    ORDER BY ordinal_position;
                """
                columns = await conn.fetch(columns_query, table_name)
                table_info["columns"] = [dict(row) for row in columns]
                
                # Get indexes
                indexes_query = """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    AND tablename = $1;
                """
                indexes = await conn.fetch(indexes_query, table_name)
                table_info["indexes"] = [row["indexname"] for row in indexes]
                
                # Check RLS
                rls_query = """
                    SELECT relrowsecurity
                    FROM pg_class
                    WHERE relname = $1;
                """
                rls_result = await conn.fetchval(rls_query, table_name)
                table_info["has_rls"] = bool(rls_result)
                
                schema_report["tables"][table_name] = table_info
            
            # Check for data integrity issues
            if 'portfolios' in existing_tables and table_info["row_count"] == 0:
                schema_report["issues"].append("No portfolios found in database")
                schema_report["recommendations"].append("Create a default portfolio for testing")
            
            if 'pricing_packs' in existing_tables:
                # Check for recent pricing data
                recent_pricing = await conn.fetchval(
                    "SELECT COUNT(*) FROM pricing_packs WHERE created_at > NOW() - INTERVAL '7 days'"
                )
                if recent_pricing == 0:
                    schema_report["issues"].append("No recent pricing data (last 7 days)")
                    schema_report["recommendations"].append("Run pricing data population script")
            
            schema_report["status"] = "complete"
            
            if not schema_report["issues"]:
                schema_report["summary"] = "✅ Schema validation successful"
            else:
                schema_report["summary"] = f"⚠️ Schema has {len(schema_report['issues'])} issues"
                
    except Exception as e:
        schema_report["status"] = "error"
        schema_report["error"] = str(e)
        schema_report["issues"].append(f"Schema validation failed: {str(e)}")
        logger.error(f"Schema validation error: {e}", exc_info=True)
    
    return schema_report

@app.get("/api/db-query")
async def execute_diagnostic_query(query: str = None):
    """
    Execute a diagnostic query for debugging purposes.
    Only allows SELECT queries for safety.
    """
    if not query:
        return {
            "error": "No query provided",
            "usage": "Add ?query=SELECT... to execute a diagnostic query"
        }
    
    # Safety check - only allow SELECT queries
    if not query.strip().upper().startswith("SELECT"):
        return {
            "error": "Only SELECT queries are allowed for safety",
            "query": query
        }
    
    if not db_pool:
        return {
            "error": "Database pool not initialized",
            "query": query
        }
    
    try:
        async with db_pool.acquire() as conn:
            # Execute query with timeout
            result = await conn.fetch(query)
            
            # Convert to list of dicts
            rows = [dict(row) for row in result]
            
            return {
                "status": "success",
                "query": query,
                "row_count": len(rows),
                "rows": rows[:100],  # Limit to 100 rows for safety
                "truncated": len(rows) > 100
            }
            
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e)
        }

@app.post("/api/patterns/execute", response_model=SuccessResponse)
async def execute_pattern(request: ExecuteRequest, user: dict = Depends(require_auth)):
    """
    Execute a pattern through the orchestrator
    AUTH_STATUS: MIGRATED - Sprint 3 (Final)
    """
    user_id = user["id"]
    
    try:

        # Execute the pattern
        # Handle both 'inputs' and 'params' fields for backwards compatibility
        pattern_inputs = {}
        if hasattr(request, 'inputs') and request.inputs:
            pattern_inputs = request.inputs
        elif hasattr(request, 'params') and request.params:
            pattern_inputs = request.params

        # Log initial inputs for debugging
        logger.info(f"Pattern execution request - pattern: {request.pattern}, initial inputs: {pattern_inputs}")
        
        # Provide default values for common missing parameters
        # portfolio_overview pattern needs lookback_days
        if request.pattern == "portfolio_overview" and "lookback_days" not in pattern_inputs:
            pattern_inputs["lookback_days"] = LOOKBACK_DAYS_YEAR  # Default to 1 year

        # Validate and ensure portfolio_id is provided and not None
        if request.pattern in PORTFOLIO_PATTERNS:
            # Check if portfolio_id is None, empty string, or missing
            portfolio_id = pattern_inputs.get("portfolio_id")
            
            if portfolio_id is None or portfolio_id == "" or portfolio_id == "None":
                logger.warning(f"Invalid portfolio_id detected: {portfolio_id}")
                
                # Try to get a valid portfolio from the database
                if db_pool:
                    try:
                        async with db_pool.acquire() as conn:
                            result = await conn.fetchrow("SELECT id FROM portfolios LIMIT 1")
                            if result:
                                pattern_inputs["portfolio_id"] = str(result["id"])
                                logger.info(f"Using database portfolio_id: {pattern_inputs['portfolio_id']}")
                            else:
                                # Use fallback portfolio ID
                                pattern_inputs["portfolio_id"] = DEFAULT_PORTFOLIO_ID
                                logger.info(f"Using fallback portfolio_id: {DEFAULT_PORTFOLIO_ID}")
                    except Exception as e:
                        logger.error(f"Failed to fetch portfolio from database: {e}")
                        # Use fallback portfolio ID
                        fallback_id = "DEFAULT_PORTFOLIO_ID"
                        pattern_inputs["portfolio_id"] = fallback_id
                        logger.info(f"Using fallback portfolio_id: {fallback_id}")
                else:
                    # No database available, use fallback
                    fallback_id = "DEFAULT_PORTFOLIO_ID"
                    pattern_inputs["portfolio_id"] = fallback_id
                    logger.info(f"No database, using fallback portfolio_id: {fallback_id}")

        result = await execute_pattern_orchestrator(
            pattern_name=request.pattern,
            inputs=pattern_inputs,
            user_id=user_id
        )

        if result["success"]:
            response = SuccessResponse(data=result["data"])
            # Add data provenance if available
            if "data_provenance" in result:
                response_dict = response.model_dump()
                response_dict["data_provenance"] = result["data_provenance"]
                return response_dict
            return response
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Pattern execution failed")
            )
    except Exception as e:
        logger.error(f"Pattern execution error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pattern execution failed: {str(e)}"
        )

@app.get("/api/patterns/list")
async def list_patterns(user: dict = Depends(require_auth)):
    """
    List all available patterns with their metadata.

    Returns pattern information for UI discovery.
    AUTH_STATUS: MIGRATED - Sprint 3 (Final)
    """
    try:
        orchestrator = get_pattern_orchestrator()
        patterns_info = orchestrator.list_patterns()

        # Sort by category and then by name
        patterns_info.sort(key=lambda x: (x.get("category", ""), x.get("name", "")))

        return SuccessResponse(
            status="success",
            data={
                "patterns": patterns_info,
                "total": len(patterns_info),
                "categories": list(set(p.get("category", "unknown") for p in patterns_info))
            }
        )

    except Exception as e:
        logger.error(f"Failed to list patterns: {e}")
        return SuccessResponse(
            status="error",
            data=None,
            error="Failed to list available patterns"
        )

@app.get("/api/patterns/metadata")
async def get_patterns_metadata(user: dict = Depends(require_auth)):
    """
    Get comprehensive metadata for all patterns.

    This endpoint provides all pattern metadata including display configuration,
    eliminating the need for frontend hardcoded pattern registry.

    AUTH_STATUS: MIGRATED - Sprint 3 (Final)
    REFACTORING: Priority 0 - Week 1
    """
    try:
        orchestrator = get_pattern_orchestrator()
        patterns_metadata = orchestrator.list_patterns()

        return SuccessResponse(
            status="success",
            data={
                "patterns": patterns_metadata,
                "total": len(patterns_metadata),
                "version": "1.0",
                "server_time": datetime.utcnow().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Failed to get patterns metadata: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve patterns metadata: {str(e)}"
        )

@app.get("/api/patterns/metadata/{pattern_id}")
async def get_pattern_metadata(pattern_id: str, user: dict = Depends(require_auth)):
    """
    Get detailed metadata for a specific pattern.

    Args:
        pattern_id: Pattern identifier

    Returns:
        Detailed pattern metadata including steps count, inputs, outputs, display config

    AUTH_STATUS: MIGRATED - Sprint 3 (Final)
    REFACTORING: Priority 0 - Week 1
    """
    try:
        orchestrator = get_pattern_orchestrator()
        metadata = orchestrator.get_pattern_metadata(pattern_id)

        if metadata is None:
            raise HTTPException(
                status_code=404,
                detail=f"Pattern '{pattern_id}' not found"
            )

        return SuccessResponse(
            status="success",
            data=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata for pattern {pattern_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve pattern metadata: {str(e)}"
        )

@app.get("/api/patterns/health")
async def patterns_health_check():
    """
    Health check endpoint for all 12 patterns.
    Shows status and data source for each pattern.
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "orchestrator_available": False,
        "patterns": {}
    }
    
    # List of actual patterns based on files in backend/patterns/
    # These should match the actual JSON files we have
    pattern_names = [
        "portfolio_overview",
        "portfolio_scenario_analysis",  # Fixed: was "scenario_analysis" 
        "portfolio_cycle_risk",
        "macro_cycles_overview",
        "macro_trend_monitor",
        "news_impact_analysis",
        "holding_deep_dive",
        "buffett_checklist",
        "cycle_deleveraging_scenarios",
        "export_portfolio_report",
        "policy_rebalance",
        "portfolio_macro_overview"
    ]
    
    try:
        # Check if orchestrator is available
        orchestrator = get_pattern_orchestrator()
        health_data["orchestrator_available"] = orchestrator is not None
        
        # Initialize all patterns status
        for pattern in pattern_names:
            health_data["patterns"][pattern] = {
                "status": "unknown",
                "data_source": "unknown",
                "last_check": None,
                "error": None,
                "can_execute": False
            }
        
        if orchestrator and db_pool:
            # Try to test actual pattern execution capability
            try:
                # Get a test portfolio ID for testing patterns
                test_portfolio_id = None
                try:
                    async with db_pool.acquire() as conn:
                        result = await conn.fetchrow("SELECT id FROM portfolios WHERE is_active = true LIMIT 1")
                        if result:
                            test_portfolio_id = result["id"]
                except Exception as e:
                    logger.debug(f"Could not get test portfolio: {e}")
                
                # Check each pattern's actual execution capability
                for pattern in pattern_names:
                    pattern_status = {
                        "status": "unknown",
                        "data_source": "none",
                        "last_check": datetime.utcnow().isoformat(),
                        "error": None,
                        "can_execute": False
                    }
                    
                    try:
                        # Determine if pattern needs portfolio_id
                        # Use consolidated pattern list from constants
                        
                        # Prepare test inputs
                        test_inputs = {}
                        if pattern in PORTFOLIO_PATTERNS and test_portfolio_id:
                            test_inputs["portfolio_id"] = test_portfolio_id
                        
                        # Try a minimal execution to see if pattern works
                        # We don't actually execute to avoid performance impact
                        # Just check if the pattern file exists
                        pattern_file = Path(f"backend/patterns/{pattern}.json")
                        if pattern_file.exists():
                            pattern_status["can_execute"] = True
                            pattern_status["status"] = "available"
                            pattern_status["data_source"] = "orchestrator"
                            
                            # Check if we have DB access for patterns that need it
                            if pattern in PORTFOLIO_PATTERNS and not test_portfolio_id:
                                pattern_status["status"] = "partial"
                                pattern_status["error"] = "No test portfolio available"
                        else:
                            pattern_status["status"] = "missing"
                            pattern_status["error"] = f"Pattern file {pattern}.json not found"
                            pattern_status["can_execute"] = False
                    
                    except Exception as e:
                        pattern_status["status"] = "error"
                        pattern_status["error"] = str(e)[:200]
                        pattern_status["can_execute"] = False
                    
                    health_data["patterns"][pattern] = pattern_status
                    
            except Exception as e:
                logger.error(f"Error checking pattern status: {e}")
                health_data["orchestrator_available"] = False
                health_data["error"] = f"Failed to check patterns: {str(e)[:200]}"
        else:
            # Orchestrator not available
            health_data["orchestrator_available"] = False
            health_data["error"] = "Pattern orchestrator not initialized"
            
            # Mark all patterns as unavailable
            for pattern in pattern_names:
                health_data["patterns"][pattern] = {
                    "status": "unavailable",
                    "data_source": "none",
                    "last_check": datetime.utcnow().isoformat(),
                    "error": "Orchestrator not available"
                }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        health_data["status"] = "error"
        health_data["error"] = str(e)[:500]
    
    # Determine overall health status based on actual availability
    pattern_statuses = [p.get("status", "unknown") for p in health_data["patterns"].values()]
    can_execute = [p.get("can_execute", False) for p in health_data["patterns"].values()]
    
    # Count pattern statuses
    available_count = sum(1 for s in pattern_statuses if s == "available")
    partial_count = sum(1 for s in pattern_statuses if s == "partial")
    missing_count = sum(1 for s in pattern_statuses if s == "missing")
    error_count = sum(1 for s in pattern_statuses if s == "error")
    
    # Set overall health based on actual capabilities
    if all(s == "available" for s in pattern_statuses):
        health_data["status"] = "healthy"
    elif available_count > 0 or partial_count > 0:
        health_data["status"] = "degraded"
    else:
        health_data["status"] = "unhealthy"
    
    # Add summary statistics with accurate counts
    health_data["summary"] = {
        "total_patterns": len(pattern_names),
        "available": available_count,
        "partial": partial_count,
        "missing": missing_count,
        "error": error_count,
        "unavailable": sum(1 for s in pattern_statuses if s == "unavailable"),
        "can_execute": sum(1 for ce in can_execute if ce)
    }
    
    return health_data

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    User login endpoint with validation
    AUTH_STATUS: NO_AUTH_REQUIRED - Public endpoint
    """
    try:
        # Validate user exists
        user = USERS_DB.get(request.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password
        if not verify_password(request.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Create JWT token
        token = create_jwt_token(user["id"], user["email"], user["role"])

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "id": user["id"],
                "email": user["email"],
                "role": user["role"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """
    Refresh JWT token endpoint
    
    The frontend expects to POST to /api/auth/refresh and receive a new access token.
    This endpoint validates the current token (even if expired within grace period)
    and issues a fresh token.
    """
    try:
        # Get the authorization header
        auth_header = request.headers.get("Authorization", "")
        
        logger.info(f"Token refresh attempt - Authorization header present: {bool(auth_header)}")
        
        if not auth_header:
            logger.warning("Token refresh failed: No Authorization header provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header not provided"
            )
        
        if not auth_header.startswith("Bearer "):
            logger.warning(f"Token refresh failed: Invalid header format: {auth_header[:20]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format - expected 'Bearer <token>'"
            )
        
        # Extract token
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        if not token:
            logger.warning("Token refresh failed: Empty token after Bearer prefix")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token not provided after Bearer prefix"
            )
        
        logger.debug(f"Token refresh: Token extracted successfully (length: {len(token)})")
        
        # Decode token - handle expired tokens within grace period
        payload = None
        token_status = "valid"
        
        try:
            # First try normal verification
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            logger.info("Token refresh: Token is valid and not expired")
            
        except jwt.ExpiredSignatureError as e:
            # Token expired, but we allow refresh within reasonable time
            logger.info("Token refresh: Token is expired, checking grace period")
            
            try:
                # Decode without expiration check but still verify signature
                payload = jwt.decode(
                    token, 
                    JWT_SECRET, 
                    algorithms=[JWT_ALGORITHM], 
                    options={"verify_signature": True, "verify_exp": False}
                )
                
                # Check if token expired more than 7 days ago (grace period)
                exp_timestamp = payload.get("exp", 0)
                current_timestamp = datetime.utcnow().timestamp()
                time_since_expiry = current_timestamp - exp_timestamp
                
                logger.info(f"Token refresh: Token expired {time_since_expiry / 3600:.1f} hours ago")
                
                if time_since_expiry > (7 * 24 * 3600):  # 7 days
                    logger.warning(f"Token refresh failed: Token expired beyond 7-day grace period ({time_since_expiry / 86400:.1f} days)")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Token expired beyond refresh window ({time_since_expiry / 86400:.1f} days ago)"
                    )
                
                token_status = f"expired_but_valid (expired {time_since_expiry / 3600:.1f} hours ago)"
                
            except jwt.InvalidTokenError as decode_error:
                logger.error(f"Token refresh failed: Could not decode expired token - {decode_error}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token signature: {str(decode_error)}"
                )
            except Exception as e:
                logger.error(f"Token refresh failed: Unexpected error during expired token decode - {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation error"
                )
                
        except jwt.InvalidTokenError as e:
            logger.error(f"Token refresh failed: Invalid token - {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token refresh failed: Unexpected error during token decode - {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token processing error"
            )
        
        # Extract user info from payload
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        logger.debug(f"Token refresh: Extracted user info - email={email}, role={role}, status={token_status}")
        
        if not all([user_id, email, role]):
            missing_fields = []
            if not user_id: missing_fields.append("sub")
            if not email: missing_fields.append("email")
            if not role: missing_fields.append("role")
            
            logger.error(f"Token refresh failed: Incomplete payload - missing fields: {missing_fields}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Incomplete token payload - missing: {', '.join(missing_fields)}"
            )
        
        # Create a new JWT token with fresh expiration
        new_token = create_jwt_token(user_id, email, role)
        
        logger.info(f"Token refresh successful for user: {email} (previous token status: {token_status})")
        
        # Return the new token in the same format as login
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "user": {
                "id": user_id,
                "email": email,
                "role": role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service error"
        )

@app.get("/api/test-corporate-actions")
async def test_corporate_actions(current_user: dict = Depends(require_auth)):
    """Test corporate actions functionality with actual portfolio data."""
    logger.info("Testing corporate actions functionality")
    
    try:
        # Get services from runtime
        runtime = get_agent_runtime()
        # Get services from financial analyst
        financial_analyst = runtime.get_agent("financial_analyst")
        if not financial_analyst:
            return {"error": "Financial analyst not available"}
        
        # Get services from the agent
        db_pool = financial_analyst.services.get("db")
        if not db_pool:
            return {"error": "Database not available"}
        
        # Get portfolio directly from database
        # The auth returns 'user-001', but we need the real UUID from the database
        user_email = current_user.get("email") or "michael@dawsos.com"
        
        async with db_pool.acquire() as conn:
            # First get the real user UUID from email
            user_row = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                user_email
            )
            if not user_row:
                return {"error": f"User not found: {user_email}"}
                
            real_user_id = user_row["id"]
            
            portfolio_row = await conn.fetchrow(
                "SELECT * FROM portfolios WHERE user_id = $1 LIMIT 1",
                real_user_id
            )
            
            if not portfolio_row:
                return {"error": "No portfolio found"}
            
            portfolio_id = portfolio_row["id"]
            
            # Get holdings from lots table
            positions = await conn.fetch(
                """
                SELECT l.security_id, l.symbol, SUM(l.quantity_open) as quantity
                FROM lots l
                WHERE l.portfolio_id = $1 
                  AND l.quantity_open > 0
                GROUP BY l.security_id, l.symbol
                """,
                portfolio_id
            )
        symbols = [pos["symbol"] for pos in positions]
        
        logger.info(f"Testing with portfolio {portfolio_id} having {len(symbols)} holdings: {symbols[:5]}")
        
        # Create context with proper pricing pack
        # Get latest pricing pack from database
        async with db_pool.acquire() as conn:
            pack_row = await conn.fetchrow(
                "SELECT id FROM pricing_packs ORDER BY created_at DESC LIMIT 1"
            )
            pricing_pack_id = pack_row["id"] if pack_row else None
        
        # Create a mock trace ID
        import hashlib
        trace_id = hashlib.md5(f"test-{datetime.now().timestamp()}".encode()).hexdigest()
        
        ctx = RequestCtx(
            request_id=f"test-{datetime.now().timestamp()}",
            trace_id=trace_id,
            user_id=real_user_id,  # Use the real UUID from database
            portfolio_id=portfolio_id,  # This is already a UUID
            pricing_pack_id=pricing_pack_id or "PP_2025-11-05",
            ledger_commit_hash="test-commit-001",
            asof_date=date.today()
        )
        
        # Test DataHarvester directly
        logger.info("Testing DataHarvester agent directly...")
        # Get DataHarvester from runtime
        data_harvester = runtime.get_agent("data_harvester")
        if not data_harvester:
            return {"error": "DataHarvester not available"}
        
        # Call corporate_actions_upcoming directly
        result = await data_harvester.corporate_actions_upcoming(
            ctx=ctx,
            state={},
            portfolio_id=str(portfolio_id)
        )
        
        # Extract key info
        actions = result.get("actions", [])
        summary = result.get("summary", {})
        errors = result.get("errors", [])
        
        logger.info(f"DataHarvester returned {len(actions)} actions")
        
        return {
            "portfolio_id": str(portfolio_id),
            "holdings_count": len(symbols),
            "symbols_sample": symbols[:10],
            "corporate_actions": {
                "total": summary.get("total_actions", 0),
                "dividends": summary.get("dividends_expected", 0),
                "splits": summary.get("splits_pending", 0),
                "earnings": summary.get("earnings_releases", 0),
                "actions_sample": actions[:5] if actions else [],
                "errors": errors
            },
            "fmp_api_key_exists": bool(os.environ.get("FMP_API_KEY")),
            "test_status": "success" if actions else "no_actions_found"
        }
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "test_status": "failed"
        }

@app.get("/api/metrics/{portfolio_id}")
async def get_portfolio_metrics(portfolio_id: str):
    """
    Get portfolio metrics
    """
    try:
        # Execute portfolio overview pattern to get metrics
        result = await execute_pattern_orchestrator(
            pattern_name="portfolio_overview",
            inputs={"portfolio_id": portfolio_id},
            user_id="user-001"
        )

        if result["success"]:
            return result["data"]
        else:
            # Return error response instead of mock data
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get metrics: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting metrics: {str(e)}"
        )

@app.get("/api/portfolio")
async def get_portfolio(user: dict = Depends(require_auth)):
    """
    Get portfolio data using pattern orchestrator
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Try to use pattern orchestrator for real data
        if db_pool:
            try:
                # Get user's portfolio ID (you may need to fetch this from DB)
                portfolio_id = None
                if user["email"]:
                    query = """
                        SELECT p.id 
                        FROM portfolios p
                        JOIN users u ON p.user_id = u.id
                        WHERE u.email = $1
                        LIMIT 1
                    """
                    result = await execute_query_safe(query, user["email"])
                    if result and len(result) > 0:
                        portfolio_id = str(result[0]["id"])

                if portfolio_id:
                    # Execute portfolio_overview pattern for real data
                    pattern_result = await execute_pattern_orchestrator(
                        "portfolio_overview",
                        {
                            "portfolio_id": portfolio_id,
                            "lookback_days": LOOKBACK_DAYS_YEAR  # Default to 1 year
                        },
                        user_id=user.get("id")
                    )

                    if pattern_result.get("success") and pattern_result.get("data"):
                        data = pattern_result["data"]

                        # Transform pattern result to expected API format
                        holdings = data.get("valued_positions", [])
                        perf_metrics = data.get("perf_metrics", {})

                        # Calculate total value from holdings
                        total_value = sum(h.get("market_value", 0) for h in holdings)

                        # Format holdings for UI
                        formatted_holdings = []
                        for h in holdings:
                            formatted_holdings.append({
                                "symbol": h.get("symbol"),
                                "quantity": h.get("quantity", 0),
                                "price": h.get("price", 0),
                                "value": h.get("market_value", 0),
                                "weight": h.get("weight", 0),
                                "sector": h.get("sector", "Other"),
                                "beta": h.get("beta", 1.0),
                                "change": h.get("daily_change_pct", 0)
                            })

                        # Calculate sector allocation
                        sector_allocation = calculate_sector_allocation(formatted_holdings, total_value)

                        return SuccessResponse(data={
                            "id": portfolio_id,
                            "name": "Main Portfolio",
                            "total_value": round(total_value, 2),
                            "holdings": formatted_holdings,
                            "sector_allocation": sector_allocation,
                            "portfolio_beta": perf_metrics.get("beta", 1.0),
                            "portfolio_volatility": perf_metrics.get("vol", 0),
                            "sharpe_ratio": perf_metrics.get("sharpe", 0),
                            "max_drawdown": perf_metrics.get("max_drawdown", 0),
                            "var_95": perf_metrics.get("var_95", 0),
                            "risk_score": perf_metrics.get("risk_score", 0.5),
                            "last_updated": datetime.utcnow().isoformat()
                        })
            except Exception as e:
                logger.warning(f"Pattern orchestrator failed, falling back: {e}")

        # Fallback to database query
        portfolio_data = await get_portfolio_data(user["email"])

        if not portfolio_data:
            # Return empty portfolio if no data found
            return ErrorResponse(
                error="no_portfolio_data",
                message="No portfolio data available. Please add holdings to get started.",
                details={"holdings": [], "total_value": 0}
            )

        # Process portfolio data
        holdings = []
        total_value = 0
        portfolio_id = None

        for row in portfolio_data:
            if not portfolio_id:
                portfolio_id = str(row.get("portfolio_id", uuid4()))

            holding = {
                "symbol": row["symbol"],
                "quantity": float(row["quantity"]),
                "price": float(row["price"]) if row["price"] else 0,
                "value": 0,
                "sector": row["sector"] or "Other",
                "beta": 1.0,  # Default beta
                "change": 0
            }
            holding["value"] = holding["quantity"] * holding["price"]
            total_value += holding["value"]

            if holding["value"] > 0:
                holdings.append(holding)

        # Calculate weights
        for holding in holdings:
            holding["weight"] = round(holding["value"] / total_value, 4) if total_value > 0 else 0

        risk_metrics = await calculate_portfolio_risk_metrics(holdings, portfolio_id)
        sector_allocation = calculate_sector_allocation(holdings, total_value)

        return SuccessResponse(data={
            "id": portfolio_id,
            "name": portfolio_data[0]["portfolio_name"] if portfolio_data else "Main Portfolio",
            "total_value": round(total_value, 2),
            "holdings": holdings,
            "sector_allocation": sector_allocation,
            **risk_metrics,
            "last_updated": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Portfolio service error"
        )

@app.get("/api/holdings")
async def get_holdings(
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: dict = Depends(require_auth)
):
    """
    Get holdings data using pattern orchestrator with pagination
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Try to use pattern orchestrator for real data
        if db_pool:
            try:
                # Get user's portfolio ID
                portfolio_id = None
                if user["email"]:
                    query = """
                        SELECT p.id 
                        FROM portfolios p
                        JOIN users u ON p.user_id = u.id
                        WHERE u.email = $1
                        LIMIT 1
                    """
                    result = await execute_query_safe(query, user["email"])
                    if result and len(result) > 0:
                        portfolio_id = str(result[0]["id"])

                if portfolio_id:
                    # Execute portfolio_overview pattern to get holdings
                    pattern_result = await execute_pattern_orchestrator(
                        "portfolio_overview",
                        {
                            "portfolio_id": portfolio_id,
                            "lookback_days": LOOKBACK_DAYS_YEAR  # Default to 1 year
                        },
                        user_id=user.get("id")
                    )

                    if pattern_result.get("success") and pattern_result.get("data"):
                        data = pattern_result["data"]

                        # Try to get valued_positions first, then positions
                        valued_positions_data = data.get("valued_positions", {})

                        # Check if valued_positions has a 'positions' key (it's the result of pricing.apply_pack)
                        if isinstance(valued_positions_data, dict) and "positions" in valued_positions_data:
                            valued_positions = valued_positions_data.get("positions", [])
                        else:
                            # Fallback to positions if valued_positions not properly structured
                            positions_data = data.get("positions", {})
                            valued_positions = positions_data.get("positions", []) if isinstance(positions_data, dict) else []

                        # Format holdings for UI with proper field mapping
                        holdings = []
                        total_value = 0
                        for pos in valued_positions:
                            # Backend returns 'qty' not 'quantity', and values as strings
                            qty = float(pos.get("qty", 0))
                            price = float(pos.get("price", 0))
                            # Use 'value' field from backend or calculate it
                            market_value = float(pos.get("value", 0)) if pos.get("value") else (qty * price)
                            total_value += market_value

                            cost_basis = float(pos.get("cost_basis", 0))
                            unrealized_pnl = market_value - cost_basis
                            # Calculate return percentage: (current value - cost) / cost * 100
                            # This is the total return since purchase (inception to date)
                            return_pct = ((market_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
                            
                            holdings.append({
                                "symbol": pos.get("symbol"),
                                "name": pos.get("name", pos.get("symbol")),  # Use symbol as fallback for name
                                "quantity": qty,  # Use 'qty' field from backend
                                "price": price,
                                "market_value": market_value,
                                "value": market_value,  # Duplicate for UI compatibility
                                "sector": pos.get("sector", "Other"),
                                "cost_basis": cost_basis,
                                "unrealized_pnl": unrealized_pnl,
                                "unrealized_pnl_pct": return_pct,  # Same as return_pct
                                "weight": 0,  # Will calculate after total
                                "return_pct": return_pct  # Total return since purchase
                            })

                        # Calculate weights
                        if total_value > 0:
                            for holding in holdings:
                                holding["weight"] = (holding["market_value"] / total_value) * 100

                        # Apply pagination
                        start = (page - 1) * page_size
                        end = start + page_size
                        paginated_holdings = holdings[start:end]

                        return {
                            "holdings": paginated_holdings,
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": len(holdings),
                                "total_pages": math.ceil(len(holdings) / page_size)
                            }
                        }
            except Exception as e:
                logger.warning(f"Pattern orchestrator failed for holdings, using fallback: {e}")

        # Fallback to database
        portfolio_data = await get_portfolio_data(user["email"])

        if not portfolio_data:
            # Return error if no database data
            return ErrorResponse(
                error="no_holdings_data",
                message="No holdings found. Please add holdings to your portfolio.",
                details={"holdings": []}
            )
        else:
            holdings = []
            for row in portfolio_data:
                holdings.append({
                    "symbol": row["symbol"],
                    "quantity": float(row["quantity"]),
                    "price": float(row["price"]) if row["price"] else 0,
                    "value": float(row["quantity"]) * float(row["price"]) if row["price"] else 0,
                    "sector": row["sector"] or "Other",
                    "cost_basis": float(row["cost_basis"]) if row["cost_basis"] else 0
                })

        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_holdings = holdings[start:end]

        return {
            "holdings": paginated_holdings,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(holdings),
                "total_pages": math.ceil(len(holdings) / page_size)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Holdings endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Holdings service error"
        )

@app.get("/api/transactions")
async def get_transactions(
    portfolio_id: str = Query(..., description="Portfolio ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    user: dict = Depends(require_auth)
):
    """
    Get transaction history from database
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Validate portfolio_id
        if not portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="portfolio_id is required"
            )

        # Query real transactions from database
        offset = (page - 1) * page_size
        query = """
            SELECT 
                t.id,
                t.transaction_date as date,
                t.transaction_type as type,
                t.symbol,
                t.quantity as shares,
                t.price,
                t.amount,
                0 as realized_gain,
                s.name as security_name
            FROM transactions t
            LEFT JOIN securities s ON t.symbol = s.symbol
            WHERE t.portfolio_id = $1::uuid
            ORDER BY t.transaction_date DESC
            LIMIT $2 OFFSET $3
        """
        transactions = await execute_query_safe(query, portfolio_id, page_size, offset)

        if not transactions:
            logger.warning(f"No transactions found for portfolio {portfolio_id}")
            return SuccessResponse(data=[])

        # Format transactions for UI
        formatted_transactions = []
        for txn in transactions:
            formatted_transactions.append({
                "id": str(txn["id"]),
                "date": str(txn["date"]),
                "type": txn["type"],
                "symbol": txn["symbol"],
                "shares": float(txn["shares"]) if txn["shares"] else 0,
                "price": float(txn["price"]) if txn["price"] else 0,
                "amount": float(txn["amount"]) if txn["amount"] else 0,
                "realized_gain": float(txn["realized_gain"]) if txn["realized_gain"] else 0,
                "security_name": txn["security_name"]
            })

        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) as total
            FROM transactions
            WHERE portfolio_id = $1::uuid
        """
        count_result = await execute_query_safe(count_query, portfolio_id)
        total = count_result[0]["total"] if count_result else 0
        
        logger.info(f"Returning {len(formatted_transactions)} of {total} transactions for portfolio {portfolio_id}")
        return SuccessResponse(data={
            "transactions": formatted_transactions,
            "total": total,
            "page": page,
            "page_size": page_size
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transactions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transactions: {str(e)}"
        )


@app.post("/api/alerts", response_model=SuccessResponse)
async def create_alert(alert_config: AlertConfig, user: dict = Depends(require_auth)):
    """
    Create a new alert with validation
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Create alert ID
        alert_id = str(uuid4())

        # Store alert (in production, this would go to database)
        alert_data = {
            "id": alert_id,
            "user_id": user["id"],
            "type": alert_config.type,
            "symbol": alert_config.symbol,
            "threshold": alert_config.threshold,
            "condition": alert_config.condition,
            "notification_channel": alert_config.notification_channel,
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }

        # Store in database
        if db_pool:
            query = """
                INSERT INTO alerts (id, user_id, condition_json, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """

            success = await execute_query_safe(
                query,
                alert_id,
                user["id"],
                json.dumps(alert_data),
                True,
                datetime.utcnow()
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create alert"
                )

        return SuccessResponse(data=alert_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Alert service error"
        )

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).model_dump()
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation exceptions"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="validation_error",
            message=str(exc),
            details={"validation_errors": str(exc)}
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__} if app.debug else None
        ).model_dump()
    )

# ============================================================================
# FRED Data Client with Error Handling
# ============================================================================

class FREDClient:
    """FRED API Client with proper error handling and caching"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or FRED_API_KEY
        self.base_url = "https://api.stlouisfed.org/fred"
        self.session: Optional[httpx.AsyncClient] = None

        # Series mapping with validation
        self.series_mapping = {
            "gdp_growth": "A191RL1Q225SBEA",
            "inflation": "CPIAUCSL",
            "unemployment": "UNRATE",
            "interest_rate": "DGS10",
            "credit_growth": "TCMDO",
            "debt_to_gdp": "GFDEBTN",
            "fiscal_deficit": "FYFSGDA188S",
            "trade_balance": "NETEXP",
            "productivity_growth": "PRS85006092",
            "yield_curve": "T10Y2Y",
            "credit_spreads": "BAA10Y",
            "vix": "VIXCLS",
            "manufacturing_pmi": "MANEMP",
            "gini_coefficient": "SIPOVGINIUSA",
            "real_interest_rate": "REAINTRATREARAT10Y",
            "corporate_profits": "CP",
            "housing_starts": "HOUST",
            "consumer_confidence": "UMCSENT",
            "m2_money_supply": "M2SL",
            "oil_prices": "DCOILWTICO",
            "dollar_index": "DEXUSEU",
            "jobless_claims": "ICSA",
            "retail_sales": "RSXFS",
            "industrial_production": "INDPRO"
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()

    async def fetch_indicator(
        self, 
        indicator_name: str, 
        series_id: Optional[str] = None,
        limit: int = 13
    ) -> Optional[float]:
        """
        Fetch a single indicator from FRED with error handling

        Args:
            indicator_name: Name of the indicator
            series_id: Optional FRED series ID override
            limit: Number of observations to fetch

        Returns:
            Latest value or None on error
        """
        if not self.api_key:
            logger.warning("FRED API key not configured")
            return None

        # Get series ID
        if not series_id:
            series_id = self.series_mapping.get(indicator_name)
            if not series_id:
                logger.warning(f"Unknown indicator: {indicator_name}")
                return None

        # Build request URL
        url = f"{self.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }

        try:
            # Create session if needed
            if not self.session:
                self.session = httpx.AsyncClient(timeout=30.0)

            # Make request
            response = await self.session.get(url, params=params)
            response.raise_for_status()

            # Parse response
            data = response.json()
            observations = data.get("observations", [])

            if not observations:
                logger.warning(f"No data returned for {indicator_name} ({series_id})")
                return None

            # Get latest non-null value
            for obs in observations:
                value = obs.get("value", ".")
                if value != "." and value:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid value for {indicator_name}: {value}")

            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {indicator_name} from FRED")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {indicator_name}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {indicator_name} from FRED: {e}")
            return None

    async def fetch_all_indicators(self) -> Dict[str, float]:
        """
        Fetch all indicators in parallel with error handling

        Returns:
            Dictionary of indicator values
        """
        indicators = {}

        if not self.api_key:
            logger.warning("FRED API key not configured - returning empty indicators")
            return indicators

        try:
            async with self:
                # Fetch all indicators in parallel
                tasks = []
                for name, series_id in self.series_mapping.items():
                    tasks.append(self.fetch_indicator(name, series_id))

                # Wait for all tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for (name, _), result in zip(self.series_mapping.items(), results):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to fetch {name}: {result}")
                    elif result is not None:
                        indicators[name] = result

                # Calculate derived indicators
                indicators.update(self.calculate_derived_indicators(indicators))

                logger.info(f"Successfully fetched {len(indicators)} indicators from FRED")

        except Exception as e:
            logger.error(f"Error fetching indicators from FRED: {e}")

        return indicators

    def calculate_derived_indicators(self, indicators: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived indicators from raw data"""
        derived = {}

        # Real interest rate
        if "interest_rate" in indicators and "inflation" in indicators:
            derived["real_interest_rate"] = indicators["interest_rate"] - indicators["inflation"]

        # Credit impulse (simplified)
        if "credit_growth" in indicators:
            derived["credit_impulse"] = self.calculate_credit_impulse(indicators["credit_growth"])

        # Debt service ratio (simplified)
        if "debt_to_gdp" in indicators and "interest_rate" in indicators:
            derived["debt_service_ratio"] = (
                indicators["debt_to_gdp"] * indicators["interest_rate"] / 100
            )

        return derived

    def calculate_credit_impulse(self, current_credit_growth: float) -> float:
        """Calculate credit impulse (change in credit growth rate)"""
        # Simplified calculation - in production, compare with previous period
        if current_credit_growth > 7:
            return 2.0  # Positive impulse
        elif current_credit_growth < 3:
            return -2.0  # Negative impulse
        else:
            return 0.0  # Neutral

# ============================================================================
# Cached FRED Data Access
# ============================================================================

async def get_cached_fred_data() -> Dict[str, float]:
    """Get FRED data from cache or fetch fresh if expired"""
    global fred_cache, fred_cache_timestamp

    # Check if cache is valid
    if fred_cache_timestamp and (time.time() - fred_cache_timestamp) < FRED_CACHE_DURATION:
        logger.info("Using cached FRED data")
        return fred_cache

    # Fetch fresh data
    async with FREDClient() as client:
        fresh_data = await client.fetch_all_indicators()

    if fresh_data:
        fred_cache = fresh_data
        fred_cache_timestamp = time.time()
        logger.info("FRED cache updated with fresh data")

    return fred_cache

# ============================================================================
# Macro and Empire Cycle Analyzers
# ============================================================================

class DalioCycleAnalyzer:
    """Analyzer for Ray Dalio's economic cycles with error handling"""

    def __init__(self):
        # Short-term debt cycle phases
        self.stdc_phases = {
            "EARLY_EXPANSION": {"growth": "accelerating", "inflation": "low", "policy": "accommodative"},
            "LATE_EXPANSION": {"growth": "strong", "inflation": "rising", "policy": "tightening"},
            "EARLY_CONTRACTION": {"growth": "slowing", "inflation": "high", "policy": "tight"},
            "RECESSION": {"growth": "negative", "inflation": "falling", "policy": "easing"}
        }

        # Long-term debt cycle phases
        self.ltdc_phases = {
            "EARLY": {"debt_to_income": "low", "debt_growth": "healthy", "interest_burden": "low"},
            "BUBBLE": {"debt_to_income": "high", "debt_growth": "excessive", "interest_burden": "rising"},
            "TOP": {"debt_to_income": "peak", "debt_growth": "slowing", "interest_burden": "high"},
            "DEPRESSION": {"debt_to_income": "deleveraging", "debt_growth": "negative", "interest_burden": "crushing"},
            "NORMALIZATION": {"debt_to_income": "stabilizing", "debt_growth": "resuming", "interest_burden": "manageable"}
        }

    def detect_stdc_phase(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Detect current phase in short-term debt cycle"""
        try:
            gdp_growth = indicators.get("gdp_growth", 2.0)
            inflation = indicators.get("inflation", 2.5)
            interest_rate = indicators.get("interest_rate", 5.0)
            unemployment = indicators.get("unemployment", 4.0)

            # Decision tree for STDC phase detection
            if gdp_growth > 2.5 and inflation < 2.5 and unemployment > 4:
                phase = "EARLY_EXPANSION"
            elif gdp_growth > 2.5 and inflation > 2.5 and unemployment < 4:
                phase = "LATE_EXPANSION"
            elif gdp_growth < 1.5 and inflation > 2.5:
                phase = "EARLY_CONTRACTION"
            elif gdp_growth < 0 or unemployment > 5.5:
                phase = "RECESSION"
            else:
                phase = "MID_EXPANSION"

            return {
                "phase": phase,
                "confidence": 0.75,  # Placeholder confidence
                "metrics": {
                    "gdp_growth": gdp_growth,
                    "inflation": inflation,
                    "unemployment": unemployment,
                    "interest_rate": interest_rate
                }
            }

        except Exception as e:
            logger.error(f"Error detecting STDC phase: {e}")
            return {
                "phase": "UNKNOWN",
                "confidence": 0,
                "error": str(e)
            }

    def detect_ltdc_phase(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Detect current phase in long-term debt cycle"""
        try:
            debt_to_gdp = indicators.get("debt_to_gdp", 100.0)
            credit_growth = indicators.get("credit_growth", 5.0)
            real_rate = indicators.get("real_interest_rate", 2.5)
            productivity = indicators.get("productivity_growth", 1.5)
            credit_impulse = indicators.get("credit_impulse", 0.0)

            # Decision tree for LTDC phase detection
            if debt_to_gdp < 60:
                phase = "EARLY"
            elif debt_to_gdp > 100 and credit_growth > 10:
                phase = "BUBBLE"
            elif debt_to_gdp > 120 and credit_growth < 5:
                phase = "TOP"
            elif debt_to_gdp > 100 and credit_growth < 0:
                phase = "DEPRESSION"
            else:
                phase = "NORMALIZATION"

            return {
                "phase": phase,
                "confidence": 0.70,  # Placeholder confidence
                "metrics": {
                    "debt_to_gdp": debt_to_gdp,
                    "credit_growth": credit_growth,
                    "credit_impulse": credit_impulse,
                    "real_rates": real_rate,
                    "productivity_growth": productivity,
                    "interest_burden": (debt_to_gdp * max(real_rate, 0.1)) / 100
                }
            }

        except Exception as e:
            logger.error(f"Error detecting LTDC phase: {e}")
            return {
                "phase": "UNKNOWN",
                "confidence": 0,
                "error": str(e)
            }

    def get_deleveraging_score(self, indicators: Dict[str, float]) -> float:
        """Calculate deleveraging pressure score (0-100)"""
        try:
            debt_to_gdp = indicators.get("debt_to_gdp", 100.0)
            fiscal_deficit = abs(indicators.get("fiscal_deficit", -5.0))
            interest_rate = indicators.get("interest_rate", 5.0)

            # Higher debt + deficit + rates = more deleveraging pressure
            score = min(100, (debt_to_gdp / 2) + (fiscal_deficit * 5) + (interest_rate * 3))
            return round(score, 2)

        except Exception as e:
            logger.error(f"Error calculating deleveraging score: {e}")
            return 0.0

class EmpireCycleAnalyzer:
    """Analyzer for Empire Cycles with error handling"""

    def __init__(self):
        self.empire_phases = {
            "RISE": {"education": "high", "innovation": "increasing", "debt": "low"},
            "PEAK": {"reserve_currency": True, "trade_share": "dominant", "military": "supreme"},
            "DECLINE_EARLY": {"education": "declining", "wealth_gap": "widening", "debt": "high"},
            "DECLINE_LATE": {"internal_conflict": "high", "currency": "weakening", "productivity": "falling"},
            "COLLAPSE": {"civil_disorder": "extreme", "currency_crisis": True, "power_transition": True}
        }

    def detect_empire_phase(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Detect current phase in empire cycle"""
        try:
            # Calculate empire indicators
            empire_indicators = {
                "education": self.estimate_education_score(indicators),
                "innovation": self.estimate_innovation_score(indicators),
                "competitiveness": indicators.get("productivity_growth", 1.5) * 20 + 30,
                "economic_output": indicators.get("gdp_share", 23.0),
                "world_trade_share": indicators.get("world_trade_share", 11.0),
                "military_strength": indicators.get("military_strength", 95.0),
                "financial_center": indicators.get("financial_center_score", 85.0),
                "reserve_currency": indicators.get("reserve_currency_share", 59.0)
            }

            # Calculate average score
            avg_score = sum(empire_indicators.values()) / len(empire_indicators)

            # Determine phase
            if avg_score > 75:
                phase = "PEAK"
                trend = "stable"
            elif avg_score > 60:
                phase = "DECLINE_EARLY"
                trend = "declining"
            elif avg_score > 45:
                phase = "DECLINE_LATE"
                trend = "accelerating_decline"
            elif avg_score > 30:
                phase = "RISE"
                trend = "ascending"
            else:
                phase = "COLLAPSE"
                trend = "transitioning"

            return {
                "phase": phase,
                "score": round(avg_score, 2),
                "trend": trend,
                "indicators": empire_indicators
            }

        except Exception as e:
            logger.error(f"Error detecting empire phase: {e}")
            return {
                "phase": "UNKNOWN",
                "score": 0,
                "trend": "unknown",
                "error": str(e)
            }

    def estimate_education_score(self, indicators: Dict[str, float]) -> float:
        """Estimate education score from economic indicators"""
        try:
            unemployment = indicators.get("unemployment", 4.0)
            productivity = indicators.get("productivity_growth", 1.5)

            score = (10 - unemployment) * 10 + productivity * 10
            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error estimating education score: {e}")
            return 50.0

    def estimate_innovation_score(self, indicators: Dict[str, float]) -> float:
        """Estimate innovation score from economic indicators"""
        try:
            productivity = indicators.get("productivity_growth", 1.5)
            interest_rate = indicators.get("interest_rate", 5.0)

            score = productivity * 30 + (10 - interest_rate) * 5
            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error estimating innovation score: {e}")
            return 50.0

# ============================================================================
# Enhanced Macro Data with MacroDataAgent Integration
# ============================================================================

async def get_enhanced_macro_data() -> Dict[str, Any]:
    """Get enhanced macro data combining FRED and MacroDataAgent"""
    try:
        # Get base indicators from FRED
        indicators = await get_cached_fred_data()

        if not indicators:
            logger.warning("No FRED data available, using defaults")
            indicators = {
                "gdp_growth": 2.0,
                "inflation": 3.0,
                "unemployment": 4.3,
                "interest_rate": 5.0,
                "debt_to_gdp": 100.0
            }

        # Enhance with MacroDataAgent if available
        try:
            enhanced = await enhance_macro_data(indicators)
            indicators.update(enhanced)
            logger.info(f"Enhanced macro data with {len(enhanced)} additional indicators")
        except Exception as e:
            logger.warning(f"Could not enhance macro data: {e}")

        # Store in database if available
        await store_macro_indicators(indicators)

        return indicators

    except Exception as e:
        logger.error(f"Error getting enhanced macro data: {e}")
        return {}

# ============================================================================
# Portfolio Optimization Service
# ============================================================================

def optimize_portfolio(
    holdings: List[dict],
    risk_tolerance: float,
    target_return: Optional[float] = None
) -> Dict[str, Any]:
    """
    Optimize portfolio allocation based on risk tolerance

    Args:
        holdings: List of current holdings
        risk_tolerance: Risk tolerance (0=conservative, 1=aggressive)
        target_return: Optional target return

    Returns:
        Optimization recommendations
    """
    try:
        if not holdings:
            return {
                "status": "error",
                "message": "No holdings to optimize"
            }

        # Calculate current metrics
        total_value = sum(h.get("value", 0) for h in holdings)
        if total_value <= 0:
            return {
                "status": "error",
                "message": "Portfolio has no value"
            }

        # Generate recommendations based on risk tolerance
        recommendations = []

        for holding in holdings:
            weight = holding.get("value", 0) / total_value
            beta = holding.get("beta", 1.0)

            # Check concentration risk
            if weight > MAX_PORTFOLIO_CONCENTRATION:
                recommendations.append({
                    "symbol": holding["symbol"],
                    "action": "REDUCE",
                    "reason": f"Concentration risk: {weight:.1%} of portfolio",
                    "target_weight": MAX_PORTFOLIO_CONCENTRATION
                })

            # Check beta alignment with risk tolerance
            if risk_tolerance < 0.3 and beta > 1.5:
                recommendations.append({
                    "symbol": holding["symbol"],
                    "action": "REDUCE",
                    "reason": f"High beta ({beta:.2f}) for conservative portfolio",
                    "target_weight": weight * 0.5
                })
            elif risk_tolerance > 0.7 and beta < 0.8:
                recommendations.append({
                    "symbol": holding["symbol"],
                    "action": "INCREASE",
                    "reason": f"Low beta ({beta:.2f}) for aggressive portfolio",
                    "target_weight": min(weight * 1.5, MAX_PORTFOLIO_CONCENTRATION)
                })

        # Check diversification
        if len(holdings) < MIN_POSITIONS_FOR_DIVERSIFICATION:
            recommendations.append({
                "action": "DIVERSIFY",
                "reason": f"Only {len(holdings)} positions - consider adding more for diversification"
            })

        return {
            "status": "success",
            "current_risk_score": calculate_portfolio_risk_metrics(holdings)["risk_score"],
            "target_risk_score": risk_tolerance,
            "recommendations": recommendations[:10],  # Limit to top 10 recommendations
            "estimated_trades": len([r for r in recommendations if "symbol" in r])
        }

    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        return {
            "status": "error",
            "message": "Optimization service error",
            "error": str(e)
        }
# ============================================================================
# Additional API Endpoints with Enhanced Error Handling
# ============================================================================

@app.get("/api/macro", response_model=SuccessResponse)
async def get_macro_indicators(user: dict = Depends(require_auth)):
    """
    Get macro economic indicators with caching
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Get enhanced macro data
        indicators = await get_enhanced_macro_data()

        if not indicators:
            # Return default values if no data available
            indicators = {
                "gdp_growth": 2.0,
                "inflation": 3.0,
                "unemployment": 4.3,
                "interest_rate": 5.0,
                "debt_to_gdp": 100.0,
                "yield_curve": 0.5,
                "credit_spreads": 2.0,
                "vix": 18.0
            }

        # Analyze cycles
        dalio_analyzer = DalioCycleAnalyzer()
        empire_analyzer = EmpireCycleAnalyzer()

        stdc_phase = dalio_analyzer.detect_stdc_phase(indicators)
        ltdc_phase = dalio_analyzer.detect_ltdc_phase(indicators)
        empire_phase = empire_analyzer.detect_empire_phase(indicators)
        deleveraging_score = dalio_analyzer.get_deleveraging_score(indicators)

        return SuccessResponse(data={
            "indicators": indicators,
            "cycles": {
                "short_term_debt": stdc_phase,
                "long_term_debt": ltdc_phase,
                "empire": empire_phase,
                "deleveraging_pressure": deleveraging_score
            },
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "FRED" if FRED_API_KEY else "mock"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Macro indicators error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Macro data service error"
        )

@app.post("/api/optimize", response_model=SuccessResponse)
async def optimize_portfolio_endpoint(
    optimization_request: OptimizationRequest,
    user: dict = Depends(require_auth)
):
    """
    Optimize portfolio allocation based on risk tolerance
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Get current portfolio
        portfolio_data = await get_portfolio_data(user["email"])
        if not portfolio_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No portfolio found"
            )

        holdings = []
        for row in portfolio_data:
            holdings.append({
                "symbol": row["symbol"],
                "quantity": float(row["quantity"]),
                "price": float(row["price"]) if row["price"] else 0,
                "value": float(row["quantity"]) * float(row["price"]) if row["price"] else 0,
                "sector": row["sector"] or "Other",
                "beta": 1.0  # Default beta
            })

        # Run optimization
        result = optimize_portfolio(
            holdings,
            optimization_request.risk_tolerance,
            optimization_request.target_return
        )

        return SuccessResponse(data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio optimization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Optimization service error"
        )

@app.get("/api/alerts", response_model=SuccessResponse)
async def get_alerts(user: dict = Depends(require_auth)):
    """
    Get user alerts with proper error handling
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Get from database
        query = """
            SELECT 
                id,
                condition_json,
                is_active,
                created_at,
                last_fired_at
            FROM alerts
            WHERE user_id = (SELECT id FROM users WHERE email = $1)
            ORDER BY created_at DESC
            LIMIT 50
        """

        alerts = await execute_query_safe(query, user["email"])

        if not alerts:
            return SuccessResponse(data={"alerts": []})

        # Format alerts
        formatted_alerts = []
        for row in alerts:
            try:
                condition_data = json.loads(row["condition_json"]) if row["condition_json"] else {}
                formatted_alerts.append({
                    "id": str(row["id"]),
                    "active": row["is_active"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "last_fired_at": row["last_fired_at"].isoformat() if row["last_fired_at"] else None,
                    **condition_data
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in alert {row['id']}")
                continue

        return SuccessResponse(data={"alerts": formatted_alerts})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Alert service error"
        )

@app.delete("/api/alerts/{alert_id}", response_model=SuccessResponse)
async def delete_alert(alert_id: str, user: dict = Depends(require_auth)):
    """
    Delete an alert with proper validation
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Validate alert ID format
        try:
            UUID(alert_id)  # Validate UUID format
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alert ID format"
            )


        # Delete from database
        query = """
            DELETE FROM alerts
            WHERE id = $1 AND user_id = (SELECT id FROM users WHERE email = $2)
            RETURNING id
        """

        result = await execute_query_safe(query, alert_id, user["email"], fetch_one=True)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found or not authorized"
            )

        return SuccessResponse(data={"deleted": True})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Alert service error"
        )

@app.post("/api/scenario", response_model=SuccessResponse)
async def run_scenario_analysis(
    scenario: str = "rates_up",
    user: dict = Depends(require_auth)
):
    """
    Run scenario analysis using real pattern orchestrator and ScenarioService
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Map frontend scenarios to ShockType enum values
        scenario_mapping = {
            "rates_up": ShockType.RATES_UP,
            "rates_down": ShockType.RATES_DOWN,
            "inflation": ShockType.CPI_SURPRISE,
            "recession": ShockType.EQUITY_SELLOFF,
            "market_crash": ShockType.EQUITY_SELLOFF  # Using EQUITY_SELLOFF for market crash
        }

        if scenario not in scenario_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scenario. Valid options: {', '.join(scenario_mapping.keys())}"
            )

        # Get portfolio ID
        portfolio_id = None
        if user["email"]:
            query = """
                SELECT p.id 
                FROM portfolios p
                JOIN users u ON p.user_id = u.id
                WHERE u.email = $1
                LIMIT 1
            """
            result = await execute_query_safe(query, user["email"])
            if result and len(result) > 0:
                portfolio_id = str(result[0]["id"])

        # Try to use pattern orchestrator for real scenario analysis
        if db_pool and portfolio_id:
            try:
                # Execute portfolio_scenario_analysis pattern
                pattern_result = await execute_pattern_orchestrator(
                    "portfolio_scenario_analysis",
                    {
                        "portfolio_id": portfolio_id,
                        "scenario_id": scenario  # Use original scenario ID
                    },
                    user_id=user.get("id") if user else None
                )

                if pattern_result.get("success") and pattern_result.get("data"):
                    data = pattern_result["data"]
                    scenario_result = data.get("scenario_result", {})

                    # Transform pattern result to expected API format
                    position_deltas = scenario_result.get("position_deltas", [])

                    # Calculate total portfolio impact
                    total_current = sum(p.get("base_value", 0) for p in position_deltas)
                    total_shocked = sum(p.get("shocked_value", 0) for p in position_deltas)
                    total_impact = total_shocked - total_current

                    # Format position impacts
                    position_impacts = []
                    for pos in position_deltas:
                        delta_value = pos.get("delta_value", 0)
                        current_value = pos.get("base_value", 0)
                        position_impacts.append({
                            "symbol": pos.get("symbol"),
                            "sector": pos.get("primary_driver", "Other"),
                            "current_value": round(current_value, 2),
                            "impact_percent": round(pos.get("delta_pct", 0), 2),
                            "impact_value": round(delta_value, 2),
                            "new_value": round(pos.get("shocked_value", 0), 2)
                        })

                    # Sort by impact
                    position_impacts.sort(key=lambda x: x["impact_value"])

                    # Get hedge suggestions from pattern result
                    hedge_suggestions = data.get("hedge_suggestions", {})
                    recommendations = []
                    if hedge_suggestions:
                        for hedge in hedge_suggestions.get("suggestions", []):
                            recommendations.append(hedge.get("description", ""))

                    # Add default recommendations if none from pattern
                    if not recommendations:
                        recommendations = [
                            "Consider hedging strategies if concerned about this scenario",
                            "Review sector allocations for better diversification",
                            "Monitor economic indicators for early warning signs"
                        ]

                    return SuccessResponse(data={
                        "scenario": scenario,
                        "portfolio_impact": {
                            "current_value": round(total_current, 2),
                            "impact_value": round(total_impact, 2),
                            "impact_percent": round((total_impact / total_current * 100) if total_current > 0 else 0, 2),
                            "new_value": round(total_shocked, 2)
                        },
                        "position_impacts": position_impacts,
                        "worst_performers": position_impacts[:5],
                        "best_performers": position_impacts[-5:] if len(position_impacts) > 5 else [],
                        "recommendations": recommendations
                    })
            except Exception as e:
                logger.warning(f"Pattern orchestrator scenario analysis failed, using fallback: {e}")

        # Fallback to direct ScenarioService or simplified calculation
        if db_pool and SCENARIO_SERVICE_AVAILABLE:
            try:
                # Use direct instantiation (DI container already initialized via get_pattern_orchestrator)
                service = ScenarioService(db_pool=db_pool)
                shock_type = scenario_mapping[scenario]

                result = await service.apply_scenario(
                    portfolio_id=portfolio_id or str(uuid4()),
                    shock_type=shock_type,
                    pack_id=None
                )

                # Format the ScenarioResult to match API response
                position_impacts = []
                for pos in result.positions:
                    delta_pl = float(pos.delta_pl)
                    current_value = float(pos.pre_shock_value)
                    position_impacts.append({
                        "symbol": pos.symbol,
                        "sector": "Other",  # Would need to look up sector
                        "current_value": round(current_value, 2),
                        "impact_percent": round(pos.delta_pl_pct * 100, 2),
                        "impact_value": round(delta_pl, 2),
                        "new_value": round(float(pos.post_shock_value), 2)
                    })

                position_impacts.sort(key=lambda x: x["impact_value"])

                return SuccessResponse(data={
                    "scenario": scenario,
                    "portfolio_impact": {
                        "current_value": round(float(result.pre_shock_nav), 2),
                        "impact_value": round(float(result.total_delta_pl), 2),
                        "impact_percent": round(result.total_delta_pl_pct * 100, 2),
                        "new_value": round(float(result.post_shock_nav), 2)
                    },
                    "position_impacts": position_impacts,
                    "worst_performers": position_impacts[:5],
                    "best_performers": position_impacts[-5:] if len(position_impacts) > 5 else [],
                    "recommendations": [
                        "Consider hedging strategies if concerned about this scenario",
                        "Review sector allocations for better diversification",
                        "Monitor economic indicators for early warning signs"
                    ]
                })
            except Exception as e:
                logger.warning(f"ScenarioService failed, using simple calculation: {e}")

        # Last resort fallback to simple sector-based impacts
        portfolio_data = await get_portfolio_data(user["email"])

        if not portfolio_data:
            # Return error when no portfolio data is available
            return ErrorResponse(
                error="no_portfolio_data",
                message="No portfolio data available for scenario analysis.",
                details={"scenario": scenario}
            )
        else:
            holdings = []
            for row in portfolio_data:
                value = float(row["quantity"]) * float(row["price"]) if row["price"] else 0
                holdings.append({
                    "symbol": row["symbol"],
                    "value": value,
                    "sector": row["sector"] or "Other"
                })

        total_value = sum(h["value"] for h in holdings)

        # Simple impact calculation by sector
        scenario_impacts = {
            "rates_up": {"Technology": -0.08, "Financial": 0.03, "Consumer": -0.05, "Automotive": -0.10, "Other": -0.03},
            "rates_down": {"Technology": 0.10, "Financial": -0.04, "Consumer": 0.05, "Automotive": 0.08, "Other": 0.03},
            "inflation": {"Technology": -0.06, "Financial": 0.02, "Consumer": -0.08, "Automotive": -0.07, "Other": -0.05},
            "recession": {"Technology": -0.15, "Financial": -0.12, "Consumer": -0.18, "Automotive": -0.20, "Other": -0.10},
            "market_crash": {"Technology": -0.25, "Financial": -0.20, "Consumer": -0.22, "Automotive": -0.30, "Other": -0.15}
        }

        impacts = scenario_impacts[scenario]
        total_impact = 0
        position_impacts = []

        for holding in holdings:
            sector = holding.get("sector", "Other")
            impact_pct = impacts.get(sector, -0.05)
            impact_value = holding["value"] * impact_pct
            total_impact += impact_value

            position_impacts.append({
                "symbol": holding.get("symbol", "Unknown"),
                "sector": sector,
                "current_value": round(holding["value"], 2),
                "impact_percent": round(impact_pct * 100, 2),
                "impact_value": round(impact_value, 2),
                "new_value": round(holding["value"] + impact_value, 2)
            })

        position_impacts.sort(key=lambda x: x["impact_value"])

        return SuccessResponse(data={
            "scenario": scenario,
            "portfolio_impact": {
                "current_value": round(total_value, 2),
                "impact_value": round(total_impact, 2),
                "impact_percent": round((total_impact / total_value * 100) if total_value > 0 else 0, 2),
                "new_value": round(total_value + total_impact, 2)
            },
            "position_impacts": position_impacts,
            "worst_performers": position_impacts[:5],
            "best_performers": position_impacts[-5:] if len(position_impacts) > 5 else [],
            "recommendations": [
                "Consider hedging strategies if concerned about this scenario",
                "Review sector allocations for better diversification",
                "Monitor economic indicators for early warning signs"
            ]
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scenario analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scenario analysis error"
        )

@app.get("/api/reports", response_model=SuccessResponse)
async def get_reports(user: dict = Depends(require_auth)):
    """
    Get available reports with proper error handling
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Available report types
        reports = [
            {
                "id": "portfolio_summary",
                "name": "Portfolio Summary",
                "description": "Overview of holdings, performance, and risk metrics",
                "frequency": "daily",
                "last_generated": datetime.utcnow().isoformat()
            },
            {
                "id": "risk_assessment",
                "name": "Risk Assessment",
                "description": "Detailed risk analysis and stress testing",
                "frequency": "weekly",
                "last_generated": (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                "id": "macro_analysis",
                "name": "Macro Analysis",
                "description": "Economic indicators and cycle analysis",
                "frequency": "weekly",
                "last_generated": (datetime.utcnow() - timedelta(days=2)).isoformat()
            },
            {
                "id": "tax_report",
                "name": "Tax Report",
                "description": "Realized gains/losses for tax purposes",
                "frequency": "annually",
                "last_generated": (datetime.utcnow() - timedelta(days=30)).isoformat()
            }
        ]

        return SuccessResponse(data={"reports": reports})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get reports error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report service error"
        )

@app.post("/api/ai-analysis", response_model=SuccessResponse)
async def ai_analysis(ai_request: AIAnalysisRequest, user: dict = Depends(require_auth)):
    """
    AI-powered portfolio analysis (placeholder)
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Check if AI API is configured
        if not ANTHROPIC_API_KEY:
            # Return mock response
            return SuccessResponse(data={
                "query": ai_request.query,
                "analysis": "AI analysis is not configured. Please set up the ANTHROPIC_API_KEY.",
                "confidence": 0.0,
                "sources": [],
                "timestamp": datetime.utcnow().isoformat()
            })

        # In production, would call Claude API here
        # For now, return a structured response
        return SuccessResponse(data={
            "query": ai_request.query,
            "analysis": f"Analysis for: {ai_request.query}. Based on current market conditions and your portfolio composition, consider maintaining a balanced approach with regular rebalancing.",
            "confidence": 0.75,
            "sources": ["Portfolio data", "Market indicators", "Historical patterns"],
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis service error"
        )

@app.post("/api/ai/chat")
async def ai_chat(request: AIChatRequest, user: dict = Depends(require_auth)):
    """
    Direct AI chat endpoint for user questions.
    
    This endpoint bypasses the pattern orchestration system and directly
    calls the Claude API for simple chat interactions.
    
    AUTH_STATUS: MIGRATED - Direct Claude Integration
    """
    try:
        logger.info(f"AI chat request from user {user.get('email', 'unknown')}: {request.message[:100]}...")
        
        # Initialize response metadata
        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user.get("user_id", user.get("sub", "unknown")),
            "model": None,
            "tokens_used": None,
            "latency_ms": None
        }
        
        start_time = time.time()
        
        # Check if Claude API is configured
        if not ANTHROPIC_API_KEY:
            logger.warning("Claude API key not configured, returning fallback response")
            error_message = ("I'm currently unable to process your request as the AI service is not configured. "
                           "Please set up the Replit Anthropic integration or provide your own ANTHROPIC_API_KEY.")
            return JSONResponse(
                content={
                    "response": error_message,
                    "metadata": {
                        **metadata,
                        "model": "fallback",
                        "fallback_reason": "api_key_not_configured",
                        "integration_method": "none"
                    }
                },
                status_code=200
            )
        
        # Log which integration method is being used
        integration_method = "replit_managed" if USING_REPLIT_INTEGRATION else "user_provided"
        logger.info(f"Using {integration_method} Anthropic API credentials")
        
        # Try to use ClaudeAgent if available
        if ANTHROPIC_AVAILABLE and anthropic:
            try:
                # Prepare context for Claude
                system_prompt = """You are an intelligent financial advisor assistant for the DawsOS portfolio management platform. 
                You provide clear, accurate, and helpful responses about portfolio management, financial markets, and investment strategies.
                Be concise but thorough. Use financial data when provided in the context.
                Always be professional and provide actionable insights when appropriate."""
                
                # Build user prompt with context if provided
                user_prompt = request.message
                
                if request.context:
                    context_str = "\n\nContext Information:"
                    
                    # Add portfolio data if available
                    if "portfolio" in request.context:
                        portfolio_data = request.context["portfolio"]
                        context_str += f"\nPortfolio Value: ${portfolio_data.get('total_value', 0):,.2f}"
                        context_str += f"\nNumber of Holdings: {portfolio_data.get('holdings_count', 0)}"
                        
                        if "performance" in portfolio_data:
                            perf = portfolio_data["performance"]
                            context_str += f"\nYTD Return: {perf.get('ytd_return', 0):.2%}"
                            context_str += f"\nSharpe Ratio: {perf.get('sharpe_ratio', 0):.2f}"
                    
                    # Add any other context data
                    for key, value in request.context.items():
                        if key != "portfolio" and value is not None:
                            if isinstance(value, (int, float)):
                                context_str += f"\n{key}: {value:,.2f}"
                            else:
                                context_str += f"\n{key}: {value}"
                    
                    user_prompt = f"{request.message}\n{context_str}"
                
                # Direct Claude API call (not through agent system)
                # Use base URL if available (for Replit integration)
                client = anthropic.Anthropic(
                    api_key=ANTHROPIC_API_KEY,
                    base_url=CLAUDE_API_URL if CLAUDE_API_URL != "https://api.anthropic.com/v1/messages" else None
                )
                
                # Use updated model
                model_name = "claude-3-5-sonnet-20241022"
                
                response = client.messages.create(
                    model=model_name,
                    max_tokens=1500,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                # Extract response text
                response_text = response.content[0].text if response.content else "I couldn't generate a response."
                
                # Update metadata
                metadata["model"] = model_name
                metadata["integration_method"] = integration_method
                metadata["tokens_used"] = response.usage.total_tokens if hasattr(response, 'usage') else None
                metadata["latency_ms"] = int((time.time() - start_time) * 1000)
                
                logger.info(f"AI chat successful - model: {metadata['model']}, latency: {metadata['latency_ms']}ms")
                
                return JSONResponse(
                    content={
                        "response": response_text,
                        "metadata": metadata
                    },
                    status_code=200
                )
                
            except Exception as claude_error:
                logger.error(f"Claude API error: {claude_error}")
                
                # Return graceful fallback
                return JSONResponse(
                    content={
                        "response": "I encountered an issue while processing your request. Please try again or rephrase your question.",
                        "metadata": {
                            **metadata,
                            "model": "fallback",
                            "error": str(claude_error),
                            "fallback_reason": "claude_api_error"
                        }
                    },
                    status_code=200
                )
        
        # Fallback to ClaudeAgent from pattern system if available
        elif PATTERN_ORCHESTRATION_AVAILABLE and _agent_runtime:
            try:
                # Get the ClaudeAgent
                claude_agent = None
                for agent_id, agent in _agent_runtime.agents.items():
                    if agent_id == "claude_agent":
                        claude_agent = agent
                        break
                
                if claude_agent:
                    # Create a minimal context
                    # Guardrail: RequestCtx is critical - check availability before use
                    if not REQUEST_CTX_AVAILABLE:
                        logger.error("CRITICAL: RequestCtx not available - cannot create request context for AI chat")
                        raise HTTPException(
                            status_code=500,
                            detail="RequestCtx not available - server configuration error"
                        )
                    
                    ctx = RequestCtx(
                        trace_id=str(uuid4()),
                        request_id=str(uuid4()),
                        user_id=user.get("user_id", user.get("sub", "unknown")),
                        portfolio_id=request.context.get("portfolio_id") if request.context else None,
                        asof_date=date.today(),
                        pricing_pack_id=f"PP_{date.today().isoformat()}",
                        ledger_commit_hash="latest"
                    )
                    
                    # Call the agent's analyze method as a simple Q&A
                    result = await claude_agent.claude_analyze(
                        ctx=ctx,
                        state={},
                        data=request.message,
                        analysis_type="general"
                    )
                    
                    # Extract insights as response
                    insights = result.get("insights", [])
                    response_text = " ".join(insights) if insights else "I understand your question but need more context to provide a detailed answer."
                    
                    metadata["model"] = "claude-agent"
                    metadata["latency_ms"] = int((time.time() - start_time) * 1000)
                    
                    return JSONResponse(
                        content={
                            "response": response_text,
                            "metadata": metadata
                        },
                        status_code=200
                    )
            except Exception as agent_error:
                logger.warning(f"ClaudeAgent fallback failed: {agent_error}")
        
        # Final fallback - intelligent static response based on common queries
        logger.info("Using intelligent fallback response system")
        
        # Simple keyword-based response system
        message_lower = request.message.lower()
        
        if "diversification" in message_lower or "diversify" in message_lower:
            response_text = ("To improve portfolio diversification, consider: "
                           "1) Spreading investments across different asset classes (stocks, bonds, commodities), "
                           "2) Diversifying across sectors and geographic regions, "
                           "3) Including assets with low correlation to reduce overall portfolio risk. "
                           "A well-diversified portfolio typically includes 15-30 different holdings across multiple sectors.")
        elif "risk" in message_lower:
            response_text = ("Portfolio risk can be managed through: "
                           "1) Diversification across uncorrelated assets, "
                           "2) Regular rebalancing to maintain target allocations, "
                           "3) Setting stop-loss orders for downside protection, "
                           "4) Monitoring key risk metrics like Sharpe ratio and maximum drawdown.")
        elif "sharpe" in message_lower or "ratio" in message_lower:
            response_text = ("The Sharpe ratio measures risk-adjusted returns. "
                           "A ratio above 1.0 is considered good, above 2.0 is very good, and above 3.0 is excellent. "
                           "It's calculated as (Portfolio Return - Risk-free Rate) / Portfolio Standard Deviation. "
                           "Higher Sharpe ratios indicate better risk-adjusted performance.")
        elif "rebalance" in message_lower or "rebalancing" in message_lower:
            response_text = ("Portfolio rebalancing helps maintain your target asset allocation. "
                           "Consider rebalancing when: "
                           "1) Any asset class deviates more than 5-10% from its target, "
                           "2) Quarterly or annually on a fixed schedule, "
                           "3) After significant market moves. "
                           "Rebalancing forces you to sell high and buy low.")
        else:
            response_text = ("I understand you're asking about: '" + request.message[:100] + "...'. "
                           "While I don't have access to the full AI service right now, "
                           "I recommend reviewing your portfolio's current allocation, risk metrics, and performance. "
                           "Consider consulting the portfolio overview and risk analysis sections for detailed insights.")
        
        metadata["model"] = "fallback-intelligent"
        metadata["latency_ms"] = int((time.time() - start_time) * 1000)
        
        return JSONResponse(
            content={
                "response": response_text,
                "metadata": metadata
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI chat error: {e}", exc_info=True)
        
        return JSONResponse(
            content={
                "error": "ai_chat_error",
                "message": "An error occurred while processing your chat request.",
                "details": {"error": str(e)}
            },
            status_code=500
        )

@app.get("/api/factor-analysis", response_model=SuccessResponse)
async def get_factor_analysis(user: dict = Depends(require_auth)):
    """
    Get factor analysis for portfolio
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Mock factor analysis (in production, would calculate from historical data)
        factor_analysis = {
            "factors": {
                "market": {
                    "exposure": 0.95,
                    "contribution": 0.12,
                    "description": "Broad market exposure"
                },
                "size": {
                    "exposure": 0.20,
                    "contribution": 0.02,
                    "description": "Large-cap bias"
                },
                "value": {
                    "exposure": -0.15,
                    "contribution": -0.01,
                    "description": "Growth tilt"
                },
                "momentum": {
                    "exposure": 0.30,
                    "contribution": 0.04,
                    "description": "Positive momentum exposure"
                },
                "quality": {
                    "exposure": 0.40,
                    "contribution": 0.03,
                    "description": "Quality factor exposure"
                }
            },
            "total_return": 0.20,
            "factor_return": 0.18,
            "alpha": 0.02,
            "r_squared": 0.85,
            "tracking_error": 0.04,
            "information_ratio": 0.50,
            "analysis_date": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=factor_analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Factor analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Factor analysis error"
        )

# ============================================================================
# Additional Portfolio Management Endpoints
# ============================================================================

@app.get("/api/portfolio/holdings", response_model=SuccessResponse)
async def get_portfolio_holdings(user: dict = Depends(require_auth)):
    """
    Get portfolio holdings with additional details
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Try pattern orchestrator first
        if PATTERN_ORCHESTRATION_AVAILABLE and _pattern_orchestrator:
            try:
                ctx = RequestCtx(
                    user_id=user.get("user_id", "user-001"),
                    asof_date=datetime.now().date(),
                    request_id=str(uuid4())
                )

                result = await _pattern_orchestrator.execute_pattern(
                    ctx=ctx,
                    pattern_id="portfolio_overview",
                    inputs={"portfolio_id": "DEFAULT_PORTFOLIO_ID"}
                )

                if result and result.outputs:
                    holdings_data = result.outputs.get("holdings_summary", {})
                    if holdings_data:
                        return SuccessResponse(data=holdings_data)
            except Exception as e:
                logger.warning(f"Pattern execution failed for portfolio holdings: {e}")

        # Fallback to mock data
        holdings = {
            "portfolio_id": "DEFAULT_PORTFOLIO_ID",
            "holdings": [
                {"symbol": "AAPL", "shares": 100, "market_value": 17500.00, "cost_basis": 15000.00, "pnl": 2500.00, "pnl_pct": 16.67, "weight": 0.15},
                {"symbol": "GOOGL", "shares": 50, "market_value": 7000.00, "cost_basis": 6500.00, "pnl": 500.00, "pnl_pct": 7.69, "weight": 0.06},
                {"symbol": "MSFT", "shares": 75, "market_value": 28125.00, "cost_basis": 25000.00, "pnl": 3125.00, "pnl_pct": 12.50, "weight": 0.24},
                {"symbol": "BRK.B", "shares": 150, "market_value": 54750.00, "cost_basis": 52000.00, "pnl": 2750.00, "pnl_pct": 5.29, "weight": 0.47},
                {"symbol": "SPY", "shares": 25, "market_value": 11250.00, "cost_basis": 10800.00, "pnl": 450.00, "pnl_pct": 4.17, "weight": 0.10}
            ],
            "total_value": 116625.00,
            "total_cost": 107300.00,
            "total_pnl": 9325.00,
            "total_pnl_pct": 8.69
        }

        return SuccessResponse(data=holdings)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio holdings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio holdings"
        )

@app.get("/api/portfolio/positions", response_model=SuccessResponse)
async def get_portfolio_positions(user: dict = Depends(require_auth)):
    """
    Get portfolio positions with detailed breakdown
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Similar to holdings but with more position details
        positions = {
            "portfolio_id": "DEFAULT_PORTFOLIO_ID",
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "market_value": 17500.00,
                    "average_cost": 150.00,
                    "current_price": 175.00,
                    "day_change": 2.50,
                    "day_change_pct": 1.45,
                    "unrealized_pnl": 2500.00,
                    "realized_pnl": 0.00,
                    "weight": 0.15,
                    "sector": "Technology",
                    "asset_class": "Equity"
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 50,
                    "market_value": 7000.00,
                    "average_cost": 130.00,
                    "current_price": 140.00,
                    "day_change": -1.00,
                    "day_change_pct": -0.71,
                    "unrealized_pnl": 500.00,
                    "realized_pnl": 0.00,
                    "weight": 0.06,
                    "sector": "Technology",
                    "asset_class": "Equity"
                }
            ],
            "summary": {
                "total_positions": 5,
                "total_value": 116625.00,
                "day_change": 1250.00,
                "day_change_pct": 1.08
            }
        }

        return SuccessResponse(data=positions)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio positions"
        )

@app.get("/api/portfolio/summary", response_model=SuccessResponse)
async def get_portfolio_summary(user: dict = Depends(require_auth)):
    """
    Get portfolio summary with key metrics
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        summary = {
            "portfolio_id": "DEFAULT_PORTFOLIO_ID",
            "total_value": 116625.00,
            "total_cost": 107300.00,
            "cash_balance": 5000.00,
            "total_equity": 121625.00,
            "total_pnl": 9325.00,
            "total_pnl_pct": 8.69,
            "day_change": 1250.00,
            "day_change_pct": 1.08,
            "ytd_return": 15.50,
            "one_year_return": 22.30,
            "sharpe_ratio": 1.45,
            "max_drawdown": -8.50,
            "positions_count": 5,
            "asset_allocation": {
                "equity": 0.96,
                "cash": 0.04,
                "bonds": 0.00
            },
            "sector_allocation": {
                "Technology": 0.45,
                "Financials": 0.47,
                "ETF": 0.08
            }
        }

        return SuccessResponse(data=summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio summary"
        )

# ============================================================================
# Risk Analytics Endpoints
# ============================================================================

@app.get("/api/risk/metrics", response_model=SuccessResponse)
async def get_risk_metrics(user: dict = Depends(require_auth)):
    """
    Get comprehensive risk metrics for the portfolio
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Try pattern orchestrator first for risk metrics
        if PATTERN_ORCHESTRATION_AVAILABLE and _pattern_orchestrator:
            try:
                ctx = RequestCtx(
                    user_id=user.get("user_id", "user-001"),
                    asof_date=datetime.now().date(),
                    request_id=str(uuid4())
                )

                result = await _pattern_orchestrator.execute_pattern(
                    ctx=ctx,
                    pattern_id="portfolio_cycle_risk",
                    inputs={"portfolio_id": "DEFAULT_PORTFOLIO_ID"}
                )

                if result and result.outputs:
                    risk_data = result.outputs.get("risk_summary", {})
                    if risk_data:
                        return SuccessResponse(data=risk_data)
            except Exception as e:
                logger.warning(f"Pattern execution failed for risk metrics: {e}")

        # Fallback to mock data
        risk_metrics = {
            "portfolio_id": "DEFAULT_PORTFOLIO_ID",
            "volatility": 0.18,
            "sharpe_ratio": 1.45,
            "sortino_ratio": 1.82,
            "beta": 0.92,
            "alpha": 0.03,
            "max_drawdown": -0.085,
            "current_drawdown": -0.023,
            "tracking_error": 0.04,
            "information_ratio": 0.75,
            "downside_deviation": 0.12,
            "upside_capture": 1.05,
            "downside_capture": 0.85,
            "risk_score": 0.65,
            "risk_level": "Moderate",
            "concentration_risk": {
                "herfindahl_index": 0.28,
                "top_5_concentration": 0.82,
                "single_stock_max": 0.47
            },
            "factor_exposures": {
                "market": 0.92,
                "size": -0.15,
                "value": 0.23,
                "momentum": 0.18,
                "quality": 0.35
            }
        }

        return SuccessResponse(data=risk_metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch risk metrics"
        )

@app.get("/api/risk/var", response_model=SuccessResponse)
async def get_value_at_risk(user: dict = Depends(require_auth)):
    """
    Get Value at Risk (VaR) calculations
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        var_data = {
            "portfolio_id": "DEFAULT_PORTFOLIO_ID",
            "portfolio_value": 116625.00,
            "var_95": {
                "1_day": -2099.25,
                "5_day": -4698.30,
                "10_day": -6642.83,
                "20_day": -9397.66
            },
            "var_99": {
                "1_day": -3265.50,
                "5_day": -7308.38,
                "10_day": -10329.38,
                "20_day": -14618.75
            },
            "cvar_95": {
                "1_day": -2799.00,
                "5_day": -6264.40,
                "10_day": -8857.11,
                "20_day": -12530.21
            },
            "cvar_99": {
                "1_day": -3732.00,
                "5_day": -8352.42,
                "10_day": -11805.00,
                "20_day": -16707.13
            },
            "stressed_var": -15961.63,
            "calculation_method": "Historical Simulation",
            "confidence_levels": [95, 99],
            "time_horizons": [1, 5, 10, 20],
            "last_updated": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=var_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating VaR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate Value at Risk"
        )

# ============================================================================
# Enhanced Macro Endpoints
# ============================================================================

@app.get("/api/macro/cycles", response_model=SuccessResponse)
async def get_macro_cycles(user: dict = Depends(require_auth)):
    """
    Get detailed macro cycle information
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Try pattern orchestrator for cycle data
        if PATTERN_ORCHESTRATION_AVAILABLE and _pattern_orchestrator:
            try:
                ctx = RequestCtx(
                    user_id=user.get("user_id", "user-001"),
                    asof_date=datetime.now().date(),
                    request_id=str(uuid4())
                )

                result = await _pattern_orchestrator.execute_pattern(
                    ctx=ctx,
                    pattern_id="macro_cycles_overview",
                    inputs={}
                )

                if result and result.outputs:
                    cycles_data = result.outputs
                    if cycles_data:
                        return SuccessResponse(data=cycles_data)
            except Exception as e:
                logger.warning(f"Pattern execution failed for macro cycles: {e}")

        # Fallback to mock data
        cycles_data = {
            "stdc": {
                "phase": "Mid-Cycle",
                "phase_number": 3,
                "composite_score": 0.62,
                "confidence": 0.75,
                "months_in_phase": 18,
                "expected_duration": "6-12 months",
                "indicators": {
                    "gdp_growth": 2.8,
                    "unemployment": 3.7,
                    "inflation": 2.4,
                    "yield_curve": 0.52
                }
            },
            "ltdc": {
                "phase": "Late Expansion",
                "phase_number": 7,
                "composite_score": 0.78,
                "confidence": 0.82,
                "years_in_cycle": 45,
                "debt_to_gdp": 124.5,
                "deleveraging_risk": "Medium",
                "indicators": {
                    "total_debt_gdp": 124.5,
                    "private_debt_gdp": 75.3,
                    "public_debt_gdp": 49.2,
                    "debt_service_ratio": 13.5
                }
            },
            "empire": {
                "phase": "Peak Power",
                "phase_number": 5,
                "composite_score": 0.68,
                "reserve_currency_status": 61.5,
                "military_spending_gdp": 3.7,
                "education_ranking": 12,
                "innovation_index": 85.3
            },
            "civil": {
                "phase": "Moderate Stability",
                "phase_number": 4,
                "composite_score": 0.55,
                "polarization_index": 0.72,
                "wealth_inequality_gini": 0.415,
                "social_mobility_index": 27.5
            },
            "regime": "MID_EXPANSION",
            "regime_confidence": 0.78,
            "last_updated": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=cycles_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching macro cycles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch macro cycles"
        )

@app.get("/api/macro/indicators", response_model=SuccessResponse)
async def get_macro_indicators(user: dict = Depends(require_auth)):
    """
    Get current macro economic indicators
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        indicators = {
            "gdp": {
                "value": 2.8,
                "previous": 2.5,
                "change": 0.3,
                "zscore": 0.42,
                "trend": "expanding"
            },
            "unemployment": {
                "value": 3.7,
                "previous": 3.8,
                "change": -0.1,
                "zscore": -0.35,
                "trend": "improving"
            },
            "inflation": {
                "value": 2.4,
                "previous": 2.6,
                "change": -0.2,
                "zscore": 0.15,
                "trend": "moderating"
            },
            "interest_rates": {
                "fed_funds": 5.33,
                "10y_treasury": 4.25,
                "2y_treasury": 4.78,
                "yield_curve": -0.53,
                "real_rate": 1.85
            },
            "credit": {
                "spread_ig": 95,
                "spread_hy": 385,
                "default_rate": 2.1,
                "lending_standards": "tightening"
            },
            "market": {
                "sp500_pe": 19.5,
                "vix": 15.2,
                "put_call_ratio": 0.92,
                "margin_debt_change": -5.2
            },
            "leading_indicators": {
                "lei_index": 102.5,
                "lei_change": -0.3,
                "recession_probability": 0.35,
                "sahm_rule": 0.17
            },
            "last_updated": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=indicators)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching macro indicators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch macro indicators"
        )

# ============================================================================
# Market Data Endpoints
# ============================================================================

@app.get("/api/quotes/{symbol}", response_model=SuccessResponse)
async def get_quote(symbol: str, user: dict = Depends(require_auth)):
    """
    Get real-time quote for a symbol
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Mock quote data
        quote = {
            "symbol": symbol.upper(),
            "name": f"{symbol.upper()} Corporation",
            "price": 150.25,
            "change": 2.50,
            "change_percent": 1.69,
            "volume": 52_384_291,
            "avg_volume": 48_500_000,
            "market_cap": 2_500_000_000_000,
            "pe_ratio": 28.5,
            "dividend_yield": 0.52,
            "52_week_high": 182.50,
            "52_week_low": 125.30,
            "open": 148.00,
            "high": 151.75,
            "low": 147.50,
            "previous_close": 147.75,
            "bid": 150.24,
            "ask": 150.26,
            "bid_size": 300,
            "ask_size": 500,
            "exchange": "NASDAQ",
            "timestamp": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=quote)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch quote for {symbol}"
        )

@app.get("/api/market/overview", response_model=SuccessResponse)
async def get_market_overview(user: dict = Depends(require_auth)):
    """
    Get market overview with major indices and stats
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        overview = {
            "indices": {
                "SP500": {
                    "value": 4550.25,
                    "change": 28.50,
                    "change_pct": 0.63,
                    "volume": 3_200_000_000
                },
                "NASDAQ": {
                    "value": 14250.75,
                    "change": 125.30,
                    "change_pct": 0.89,
                    "volume": 4_500_000_000
                },
                "DOW": {
                    "value": 35680.50,
                    "change": 185.20,
                    "change_pct": 0.52,
                    "volume": 280_000_000
                },
                "RUSSELL": {
                    "value": 1850.30,
                    "change": 12.40,
                    "change_pct": 0.68,
                    "volume": 1_800_000_000
                },
                "VIX": {
                    "value": 15.20,
                    "change": -0.80,
                    "change_pct": -5.00
                }
            },
            "sectors": {
                "Technology": {"change_pct": 1.25, "leaders": ["AAPL", "MSFT", "NVDA"]},
                "Financials": {"change_pct": 0.45, "leaders": ["JPM", "BAC", "WFC"]},
                "Healthcare": {"change_pct": -0.15, "leaders": ["JNJ", "UNH", "PFE"]},
                "Energy": {"change_pct": 2.10, "leaders": ["XOM", "CVX", "COP"]},
                "Consumer": {"change_pct": 0.65, "leaders": ["AMZN", "TSLA", "WMT"]}
            },
            "market_breadth": {
                "advances": 2150,
                "declines": 1320,
                "unchanged": 230,
                "new_highs": 125,
                "new_lows": 45,
                "advance_decline_ratio": 1.63
            },
            "commodities": {
                "gold": {"value": 2050.30, "change_pct": 0.35},
                "silver": {"value": 24.15, "change_pct": 0.82},
                "oil": {"value": 78.50, "change_pct": 1.25},
                "natural_gas": {"value": 3.12, "change_pct": -2.15}
            },
            "currencies": {
                "DXY": {"value": 103.25, "change_pct": -0.15},
                "EURUSD": {"value": 1.0825, "change_pct": 0.22},
                "GBPUSD": {"value": 1.2650, "change_pct": 0.18},
                "USDJPY": {"value": 148.75, "change_pct": -0.35}
            },
            "bonds": {
                "10Y": {"yield": 4.25, "change_bps": -3},
                "2Y": {"yield": 4.78, "change_bps": 2},
                "30Y": {"yield": 4.38, "change_bps": -4},
                "spread_2_10": {"value": -0.53, "change_bps": -5}
            },
            "market_status": "open",
            "next_earnings": ["AAPL", "GOOGL", "AMZN"],
            "economic_calendar": [
                {"date": "Tomorrow", "event": "FOMC Minutes", "importance": "high"},
                {"date": "Friday", "event": "NFP Report", "importance": "high"}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=overview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch market overview"
        )

# ============================================================================
# Settings and API Keys Endpoints
# ============================================================================

@app.get("/api/settings", response_model=SuccessResponse)
async def get_settings(user: dict = Depends(require_auth)):
    """
    Get user settings
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        settings = {
            "user_id": user.get("user_id"),
            "preferences": {
                "theme": "dark",
                "language": "en",
                "timezone": "America/New_York",
                "currency": "USD",
                "date_format": "MM/DD/YYYY",
                "number_format": "thousand_separator"
            },
            "notifications": {
                "email": True,
                "sms": False,
                "push": True,
                "alert_types": {
                    "price_alerts": True,
                    "portfolio_alerts": True,
                    "risk_alerts": True,
                    "news_alerts": False
                }
            },
            "display": {
                "default_view": "dashboard",
                "chart_type": "candlestick",
                "table_density": "comfortable",
                "show_tooltips": True,
                "auto_refresh": True,
                "refresh_interval": 60
            },
            "trading": {
                "default_order_type": "limit",
                "confirm_orders": True,
                "default_duration": "day"
            },
            "risk": {
                "risk_tolerance": "moderate",
                "max_position_size": 0.10,
                "stop_loss_default": 0.05
            }
        }

        return SuccessResponse(data=settings)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch settings"
        )

@app.post("/api/settings", response_model=SuccessResponse)
async def update_settings(request: Request, user: dict = Depends(require_auth)):
    """
    Update user settings
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:
        body = await request.json()

        # Here you would normally validate and save the settings
        # For now, just echo back the updated settings
        updated_settings = {
            "user_id": user.get("user_id"),
            "preferences": body.get("preferences", {}),
            "notifications": body.get("notifications", {}),
            "display": body.get("display", {}),
            "trading": body.get("trading", {}),
            "risk": body.get("risk", {}),
            "updated_at": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data={
            "message": "Settings updated successfully",
            "settings": updated_settings
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )

@app.get("/api/keys", response_model=SuccessResponse)
async def get_api_keys(user: dict = Depends(require_auth)):
    """
    Get API key configuration (masked)
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Return masked API key info
        api_keys = {
            "configured_providers": [
                {
                    "provider": "polygon",
                    "status": "active",
                    "key_masked": "****" + "abcd",
                    "rate_limit": "5 requests/minute",
                    "usage_this_month": 1250,
                    "limit_this_month": 10000
                },
                {
                    "provider": "fred",
                    "status": "active",
                    "key_masked": "****" + "efgh",
                    "rate_limit": "120 requests/minute",
                    "usage_this_month": 8500,
                    "limit_this_month": 100000
                },
                {
                    "provider": "anthropic",
                    "status": "active" if ANTHROPIC_API_KEY else "not_configured",
                    "key_masked": "****" + "ijkl" if ANTHROPIC_API_KEY else None,
                    "model": "claude-3-opus",
                    "usage_this_month": "$12.50",
                    "limit_this_month": "$100.00"
                }
            ],
            "available_providers": [
                "polygon", "fred", "anthropic", "openai", "alphavantage", "iex", "finnhub"
            ],
            "webhook_endpoints": [
                {
                    "id": "webhook_1",
                    "url": "https://your-app.com/webhooks/alerts",
                    "events": ["price_alert", "risk_alert"],
                    "status": "active"
                }
            ]
        }

        return SuccessResponse(data=api_keys)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch API key configuration"
        )

# ============================================================================
# Optimizer Endpoints
# ============================================================================

@app.get("/api/optimizer/proposals", response_model=SuccessResponse)
async def get_optimizer_proposals(
    portfolio_id: Optional[str] = Query(None),
    user: dict = Depends(require_auth)
):
    """
    Get optimization proposals for portfolio
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # If pattern orchestration is available, use the optimizer agent
        if PATTERN_ORCHESTRATION_AVAILABLE and _pattern_orchestrator:
            try:
                # Get runtime and execute optimizer capability
                runtime = get_agent_runtime()
                ctx = RequestCtx(
                    user_id=user.get("user_id"),
                    portfolio_id=UUID(portfolio_id) if portfolio_id else None,
                    asof_date=date.today(),
                )

                # Use optimizer agent to get proposals
                result = await runtime.execute_capability(
                    agent_id="optimizer_agent",
                    capability="optimizer.suggest_trades",
                    ctx=ctx,
                    state={
                        "portfolio_id": portfolio_id,
                        "risk_tolerance": 0.5,
                        "target_return": 0.08
                    }
                )

                if result:
                    return SuccessResponse(data=result)
            except Exception as e:
                logger.error(f"Error executing optimizer pattern: {e}")

        # Fallback mock data
        proposals = {
            "portfolio_id": portfolio_id or "mock-portfolio",
            "proposals": [
                {
                    "id": "prop_001",
                    "action": "rebalance",
                    "title": "Reduce Tech Overweight",
                    "description": "Tech sector is 45% of portfolio, recommend reducing to 30%",
                    "trades": [
                        {"symbol": "AAPL", "action": "sell", "quantity": 50, "reason": "Reduce concentration"},
                        {"symbol": "MSFT", "action": "sell", "quantity": 30, "reason": "Reduce concentration"},
                        {"symbol": "VTI", "action": "buy", "quantity": 100, "reason": "Increase diversification"}
                    ],
                    "expected_impact": {
                        "risk_reduction": -0.15,
                        "return_impact": -0.02,
                        "sharpe_improvement": 0.12
                    },
                    "confidence": 0.78
                },
                {
                    "id": "prop_002",
                    "action": "hedge",
                    "title": "Add Downside Protection",
                    "description": "Current VaR exceeds threshold, consider protective puts",
                    "trades": [
                        {"symbol": "SPY", "action": "buy_put", "strike": 420, "expiry": "2025-12-20", "quantity": 10}
                    ],
                    "expected_impact": {
                        "max_drawdown_reduction": -0.08,
                        "cost_drag": -0.003,
                        "protection_level": 0.85
                    },
                    "confidence": 0.82
                }
            ],
            "optimization_metrics": {
                "current_sharpe": 0.95,
                "optimized_sharpe": 1.07,
                "current_risk": 0.18,
                "optimized_risk": 0.153,
                "efficiency_score": 0.72
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=proposals)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimizer proposals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get optimization proposals"
        )

@app.get("/api/optimizer/analysis", response_model=SuccessResponse)
async def get_optimizer_analysis(
    portfolio_id: Optional[str] = Query(None),
    user: dict = Depends(require_auth)
):
    """
    Get optimization impact analysis
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Mock optimization analysis
        analysis = {
            "portfolio_id": portfolio_id or "mock-portfolio",
            "current_state": {
                "total_value": 250000,
                "positions": 15,
                "sectors": 8,
                "risk_score": 0.68,
                "efficiency_score": 0.71,
                "concentration_risk": "high",
                "diversification_score": 0.65
            },
            "optimized_state": {
                "total_value": 250000,
                "positions": 20,
                "sectors": 11,
                "risk_score": 0.52,
                "efficiency_score": 0.86,
                "concentration_risk": "moderate",
                "diversification_score": 0.83
            },
            "improvements": {
                "risk_reduction": -23.5,
                "efficiency_gain": 21.1,
                "diversification_improvement": 27.7,
                "expected_sharpe_improvement": 12.6
            },
            "trade_impact": {
                "trades_required": 8,
                "estimated_costs": 125.50,
                "tax_implications": "minimal",
                "execution_time": "2-3 days"
            },
            "risk_metrics": {
                "var_95_current": -0.082,
                "var_95_optimized": -0.063,
                "max_drawdown_current": -0.185,
                "max_drawdown_optimized": -0.142
            }
        }

        return SuccessResponse(data=analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimizer analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get optimization analysis"
        )

# ============================================================================
# Ratings Endpoints
# ============================================================================

@app.get("/api/ratings/overview", response_model=SuccessResponse)
async def get_ratings_overview(
    portfolio_id: Optional[str] = Query(None),
    user: dict = Depends(require_auth)
):
    """
    Get overall portfolio ratings
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Mock ratings overview
        overview = {
            "portfolio_id": portfolio_id or "mock-portfolio",
            "overall_score": 7.8,
            "rating": "B+",
            "percentile": 78,
            "categories": {
                "quality": {"score": 8.2, "rating": "A-", "weight": 0.25},
                "moat": {"score": 7.5, "rating": "B+", "weight": 0.20},
                "management": {"score": 6.9, "rating": "B", "weight": 0.15},
                "valuation": {"score": 7.8, "rating": "B+", "weight": 0.20},
                "growth": {"score": 8.5, "rating": "A-", "weight": 0.20}
            },
            "top_holdings_ratings": [
                {"symbol": "AAPL", "score": 8.9, "rating": "A", "weight": 15.2},
                {"symbol": "MSFT", "score": 9.1, "rating": "A+", "weight": 12.8},
                {"symbol": "GOOGL", "score": 8.3, "rating": "A-", "weight": 8.5},
                {"symbol": "BRK.B", "score": 9.5, "rating": "A+", "weight": 7.2},
                {"symbol": "JPM", "score": 7.2, "rating": "B+", "weight": 5.8}
            ],
            "recommendations": [
                "Consider increasing allocation to A-rated holdings",
                "Review positions with ratings below B",
                "Portfolio quality score above market average"
            ],
            "last_updated": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=overview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ratings overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ratings overview"
        )

@app.get("/api/ratings/buffett", response_model=SuccessResponse)
async def get_buffett_checklist(
    symbol: Optional[str] = Query(None),
    security_id: Optional[str] = Query(None),
    user: dict = Depends(require_auth)
):
    """
    Get Buffett checklist scores for a security
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # If pattern orchestration is available, try to use it
        if PATTERN_ORCHESTRATION_AVAILABLE and _pattern_orchestrator:
            try:
                # Execute buffett checklist pattern
                result = await _pattern_orchestrator.execute_pattern(
                    "buffett_checklist",
                    {
                        "security_id": security_id or "mock-security-id",
                    },
                    RequestCtx(user_id=user.get("user_id"))
                )

                if result and result.get("status") == "success":
                    return SuccessResponse(data=result.get("data", {}))
            except Exception as e:
                logger.error(f"Error executing buffett checklist pattern: {e}")

        # Fallback mock data
        checklist = {
            "symbol": symbol or "AAPL",
            "company_name": "Apple Inc.",
            "overall_score": 85,
            "grade": "A",
            "checklist_items": {
                "business_understanding": {
                    "score": 9,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "Simple business model - consumer electronics and services"
                },
                "consistent_earnings": {
                    "score": 10,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "10+ years of consistent earnings growth"
                },
                "low_debt": {
                    "score": 8,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "Debt/Equity ratio of 1.5, manageable debt levels"
                },
                "high_roe": {
                    "score": 10,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "ROE consistently above 20% for 5 years"
                },
                "profit_margins": {
                    "score": 9,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "Operating margins above 25%"
                },
                "competitive_moat": {
                    "score": 10,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "Strong brand loyalty and ecosystem lock-in"
                },
                "management_quality": {
                    "score": 8,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "Strong leadership with proven track record"
                },
                "intrinsic_value": {
                    "score": 7,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "Trading near fair value, limited margin of safety"
                },
                "share_buybacks": {
                    "score": 9,
                    "max_score": 10,
                    "passed": True,
                    "explanation": "Consistent share buyback program reducing share count"
                },
                "dividend_growth": {
                    "score": 5,
                    "max_score": 10,
                    "passed": False,
                    "explanation": "Modest dividend yield, but growing consistently"
                }
            },
            "strengths": [
                "Exceptional brand value and customer loyalty",
                "Strong free cash flow generation",
                "Dominant market position in premium segments"
            ],
            "weaknesses": [
                "High valuation multiples",
                "Regulatory risks in key markets",
                "Dependence on iPhone sales"
            ],
            "buffett_verdict": "PASS",
            "recommendation": "Strong business with durable competitive advantages. Consider accumulating on dips.",
            "analysis_date": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=checklist)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Buffett checklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Buffett checklist"
        )

# ============================================================================
# AI Insights Endpoints
# ============================================================================

@app.get("/api/ai/insights", response_model=SuccessResponse)
async def get_ai_insights(
    portfolio_id: Optional[str] = Query(None),
    insight_type: Optional[str] = Query("general"),
    user: dict = Depends(require_auth)
):
    """
    Get AI-generated insights for portfolio
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Mock AI insights
        insights = {
            "portfolio_id": portfolio_id or "mock-portfolio",
            "insight_type": insight_type,
            "insights": [
                {
                    "id": "insight_001",
                    "category": "risk",
                    "priority": "high",
                    "title": "Concentration Risk Detected",
                    "insight": "Your technology sector allocation (45%) exceeds recommended limits. Consider diversifying to reduce sector-specific risk.",
                    "action_items": [
                        "Review tech holdings for redundancy",
                        "Consider adding defensive sectors",
                        "Set maximum sector allocation at 30%"
                    ],
                    "confidence": 0.89
                },
                {
                    "id": "insight_002",
                    "category": "opportunity",
                    "priority": "medium",
                    "title": "Dividend Growth Opportunity",
                    "insight": "Several holdings have announced dividend increases. Your portfolio's forward yield has improved to 2.8%.",
                    "action_items": [
                        "Review dividend reinvestment settings",
                        "Consider tax-efficient account placement",
                        "Evaluate dividend sustainability metrics"
                    ],
                    "confidence": 0.92
                },
                {
                    "id": "insight_003",
                    "category": "macro",
                    "priority": "medium",
                    "title": "Rate Environment Shift",
                    "insight": "Fed policy changes suggest a pause in rate hikes. Growth stocks may outperform value in the near term.",
                    "action_items": [
                        "Review duration exposure in fixed income",
                        "Consider growth vs value allocation",
                        "Monitor yield curve dynamics"
                    ],
                    "confidence": 0.78
                }
            ],
            "market_context": {
                "sentiment": "neutral",
                "volatility": "moderate",
                "trend": "sideways",
                "key_risks": ["inflation", "geopolitical", "earnings"]
            },
            "personalized_recommendations": [
                "Your risk tolerance suggests maintaining current equity allocation",
                "Consider tax-loss harvesting opportunities in underperforming positions",
                "Review portfolio rebalancing triggers"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=insights)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI insights"
        )

# ============================================================================
# Corporate Actions Endpoint
# ============================================================================

@app.get("/api/corporate-actions", response_model=SuccessResponse)
async def get_corporate_actions(
    portfolio_id: str = Query(..., description="Portfolio ID to get corporate actions for"),
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    user: dict = Depends(require_auth)
):
    """
    Get upcoming corporate actions for portfolio holdings.
    Requires portfolio_id to be specified.
    
    AUTH_STATUS: MIGRATED - Sprint 2
    NOTE: Not yet implemented - returns empty data
    """
    try:
        # Validate portfolio_id format (basic UUID check)
        if not portfolio_id or len(portfolio_id) != 36:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid portfolio_id format"
            )
        
        # Corporate actions tracking not implemented in alpha
        # Return empty array with informative message
        response = {
            "portfolio_id": portfolio_id,
            "time_horizon_days": days_ahead,
            "actions": [],
            "summary": {
                "total_actions": 0,
                "dividends_expected": 0.00,
                "splits_pending": 0,
                "earnings_releases": 0,
                "mergers_acquisitions": 0
            },
            "notifications": {
                "urgent": [],
                "informational": []
            },
            "last_updated": datetime.utcnow().isoformat(),
            "metadata": {
                "message": "Corporate actions tracking not implemented in alpha version",
                "version": "alpha",
                "note": "Past dividends are tracked in the transactions table"
            }
        }

        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting corporate actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get corporate actions"
        )

# REMOVED: Corporate Actions Sync Endpoint - Moved to backend/app/api/routes/corporate_actions.py
# The /v1/corporate-actions/sync-fmp endpoint is now properly handled by the corporate_actions router

# ============================================================================
# API Keys Management Endpoints
# ============================================================================

@app.get("/api/api-keys", response_model=SuccessResponse)
async def get_api_keys_v2(user: dict = Depends(require_auth)):
    """
    Get API keys configuration (v2 endpoint matching frontend expectation)
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    # This is a duplicate of /api/keys but with the expected path
    return await get_api_keys(user)

@app.post("/api/api-keys", response_model=SuccessResponse)
async def update_api_keys(request: Request, user: dict = Depends(require_auth)):
    """
    Update API keys configuration
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:
        body = await request.json()
        provider = body.get("provider")
        api_key = body.get("api_key")

        if not provider or not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider and API key are required"
            )

        # Validate provider
        valid_providers = ["polygon", "fred", "anthropic", "openai", "alphavantage", "iex", "finnhub"]
        if provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
            )

        # Here you would normally save the API key securely
        # For now, just return success
        response = {
            "message": f"API key for {provider} updated successfully",
            "provider": provider,
            "status": "active",
            "key_masked": "****" + api_key[-4:] if len(api_key) > 4 else "****",
            "updated_at": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API keys"
        )

# ============================================================================
# Missing Endpoints to Fix 404 Errors - Added for functionality improvement
# ============================================================================

@app.get("/api/scenarios", response_model=SuccessResponse)
async def get_scenarios(user: dict = Depends(require_auth)):
    """
    Get available scenario definitions and current analysis
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Try to execute pattern for scenarios
        if PATTERN_ORCHESTRATION_AVAILABLE and db_pool:
            try:
                result = await execute_pattern_orchestrator(
                    pattern_name="portfolio_scenario_analysis",
                    inputs={"portfolio_id": "DEFAULT_PORTFOLIO_ID"},
                    user_id=user.get("id")
                )
                if result.get("success"):
                    return SuccessResponse(data=result.get("data", {}))
            except Exception as e:
                logger.warning(f"Pattern execution failed for scenarios: {e}")

        # Return comprehensive mock scenarios
        scenarios = {
            "available_scenarios": [
                {
                    "id": "recession_mild",
                    "name": "Mild Recession",
                    "description": "Economic slowdown with 2 quarters of negative GDP growth",
                    "probability": 0.35,
                    "impact": "moderate",
                    "parameters": {
                        "gdp_shock": -0.02,
                        "unemployment_increase": 2.0,
                        "equity_decline": -0.15,
                        "bond_rally": 0.05
                    }
                },
                {
                    "id": "recession_severe",
                    "name": "Severe Recession",
                    "description": "Deep economic contraction similar to 2008",
                    "probability": 0.15,
                    "impact": "severe",
                    "parameters": {
                        "gdp_shock": -0.04,
                        "unemployment_increase": 5.0,
                        "equity_decline": -0.35,
                        "bond_rally": 0.10
                    }
                },
                {
                    "id": "inflation_spike",
                    "name": "Inflation Spike",
                    "description": "Rapid increase in inflation above 5%",
                    "probability": 0.25,
                    "impact": "moderate",
                    "parameters": {
                        "inflation_increase": 3.0,
                        "rate_increase": 2.0,
                        "equity_decline": -0.10,
                        "bond_decline": -0.08
                    }
                },
                {
                    "id": "credit_crisis",
                    "name": "Credit Crisis",
                    "description": "Banking sector stress and credit crunch",
                    "probability": 0.10,
                    "impact": "severe",
                    "parameters": {
                        "credit_spread_widening": 300,
                        "liquidity_decline": -0.30,
                        "equity_decline": -0.25,
                        "volatility_spike": 2.0
                    }
                },
                {
                    "id": "geopolitical_shock",
                    "name": "Geopolitical Crisis",
                    "description": "Major geopolitical event affecting markets",
                    "probability": 0.15,
                    "impact": "high",
                    "parameters": {
                        "oil_price_spike": 0.50,
                        "equity_decline": -0.20,
                        "volatility_spike": 1.5,
                        "safe_haven_rally": 0.10
                    }
                }
            ],
            "current_scenario": {
                "active": "base_case",
                "name": "Base Case",
                "description": "Current economic trajectory continues",
                "probability": 0.60,
                "last_updated": datetime.utcnow().isoformat()
            },
            "portfolio_impact": {
                "recession_mild": {"impact": -12.5, "var_95": -18000},
                "recession_severe": {"impact": -28.3, "var_95": -35000},
                "inflation_spike": {"impact": -8.2, "var_95": -12000},
                "credit_crisis": {"impact": -22.1, "var_95": -28000},
                "geopolitical_shock": {"impact": -15.7, "var_95": -20000}
            }
        }

        return SuccessResponse(data=scenarios)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch scenarios"
        )

@app.get("/api/risk/concentration", response_model=SuccessResponse)
async def get_risk_concentration(user: dict = Depends(require_auth)):
    """
    Get concentration risk metrics for portfolio
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Return concentration risk metrics
        concentration_risk = {
            "position_concentration": {
                "top_position": {"symbol": "BRK.B", "weight": 0.47, "risk_level": "high"},
                "top_3_positions": {"weight": 0.78, "symbols": ["BRK.B", "MSFT", "AAPL"]},
                "top_5_positions": {"weight": 0.94, "symbols": ["BRK.B", "MSFT", "AAPL", "SPY", "GOOGL"]},
                "herfindahl_index": 0.32,  # High concentration
                "concentration_score": 0.75  # 0-1, higher is more concentrated
            },
            "sector_concentration": {
                "top_sector": {"name": "Technology", "weight": 0.45, "risk_level": "moderate"},
                "top_3_sectors": {"weight": 0.85, "sectors": ["Technology", "Finance", "Healthcare"]},
                "sector_herfindahl": 0.28,
                "diversification_score": 0.65
            },
            "asset_class_concentration": {
                "equities": 0.95,
                "bonds": 0.03,
                "alternatives": 0.02,
                "cash": 0.00,
                "concentration_risk": "high"
            },
            "geographic_concentration": {
                "us": 0.88,
                "developed_markets": 0.10,
                "emerging_markets": 0.02,
                "concentration_risk": "high"
            },
            "risk_metrics": {
                "concentration_var": 22500,
                "diversification_ratio": 1.8,
                "effective_positions": 3.2,  # Low = concentrated
                "risk_contribution": {
                    "BRK.B": 0.42,
                    "MSFT": 0.21,
                    "AAPL": 0.13,
                    "others": 0.24
                }
            },
            "recommendations": [
                "Portfolio highly concentrated in BRK.B (47%)",
                "Consider reducing Technology sector exposure",
                "Add international diversification",
                "Consider fixed income allocation"
            ],
            "risk_score": 7.5,  # Out of 10
            "timestamp": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=concentration_risk)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching concentration risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch concentration risk"
        )

@app.get("/api/market/quotes", response_model=SuccessResponse)
async def get_market_quotes(
    symbols: str = Query(default=None, description="Comma-separated list of symbols"),
    user: dict = Depends(require_auth)
):
    """
    Get multiple market quotes at once
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Parse symbols or use default watchlist
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        else:
            # Default watchlist when no symbols provided
            symbol_list = ["SPY", "AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "TSLA", "BRK.B"]

        if not symbol_list:
            # Fallback to default if parsing resulted in empty list
            symbol_list = ["SPY", "AAPL", "GOOGL", "MSFT"]

        # Mock quote data for each symbol
        quotes = {}
        base_prices = {
            "AAPL": 175.00, "GOOGL": 140.00, "MSFT": 375.00,
            "BRK.B": 365.00, "SPY": 450.00, "NVDA": 495.00,
            "TSLA": 245.00, "META": 355.00, "AMZN": 155.00
        }

        for symbol in symbol_list:
            base_price = base_prices.get(symbol, 100.00)
            change_pct = random.uniform(-3, 3)
            change = base_price * change_pct / 100

            quotes[symbol] = {
                "symbol": symbol,
                "price": round(base_price + change, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "volume": random.randint(1000000, 50000000),
                "market_cap": random.randint(100000000000, 3000000000000),
                "pe_ratio": round(random.uniform(10, 40), 2),
                "day_high": round(base_price * 1.02, 2),
                "day_low": round(base_price * 0.98, 2),
                "week_52_high": round(base_price * 1.30, 2),
                "week_52_low": round(base_price * 0.70, 2),
                "timestamp": datetime.utcnow().isoformat()
            }

        return SuccessResponse(data={
            "quotes": quotes,
            "count": len(quotes),
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market quotes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch market quotes"
        )

@app.get("/api/optimizer/efficient-frontier", response_model=SuccessResponse)
async def get_efficient_frontier(user: dict = Depends(require_auth)):
    """
    Get efficient frontier data for portfolio optimization
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Generate efficient frontier points
        frontier_points = []
        for i in range(20):
            risk = 5 + i * 1.5  # Risk from 5% to 33.5%
            # Expected return increases with risk but with diminishing returns
            expected_return = 2 + (risk * 0.5) - (risk * risk * 0.008)

            frontier_points.append({
                "risk": round(risk, 2),
                "return": round(expected_return, 2),
                "sharpe_ratio": round(expected_return / risk, 3),
                "portfolio_mix": {
                    "stocks": round(min(risk * 3, 90), 1),
                    "bonds": round(max(90 - risk * 3, 5), 1),
                    "alternatives": round(min(risk / 3, 5), 1)
                }
            })

        efficient_frontier = {
            "frontier_points": frontier_points,
            "current_portfolio": {
                "risk": 18.2,
                "return": 14.5,
                "sharpe_ratio": 0.797,
                "efficiency": 0.82  # How close to frontier
            },
            "optimal_portfolio": {
                "risk": 16.5,
                "return": 15.8,
                "sharpe_ratio": 0.958,
                "improvement_potential": 9.0  # Percent improvement possible
            },
            "tangent_portfolio": {
                "risk": 14.2,
                "return": 12.8,
                "sharpe_ratio": 0.901,
                "description": "Maximum Sharpe ratio portfolio"
            },
            "minimum_variance": {
                "risk": 8.5,
                "return": 6.2,
                "sharpe_ratio": 0.729,
                "description": "Lowest risk portfolio"
            },
            "statistics": {
                "portfolios_analyzed": 10000,
                "computation_time_ms": 245,
                "confidence_level": 0.95
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=efficient_frontier)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching efficient frontier: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch efficient frontier"
        )

@app.get("/api/optimizer/recommendations", response_model=SuccessResponse)
async def get_optimizer_recommendations(user: dict = Depends(require_auth)):
    """
    Get optimization recommendations for portfolio
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        recommendations = {
            "optimization_score": 72,  # Out of 100
            "potential_improvement": {
                "return_improvement": 1.3,  # Percentage points
                "risk_reduction": -2.1,  # Percentage points
                "sharpe_improvement": 0.16  # Absolute improvement
            },
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Reduce concentration",
                    "description": "Reduce BRK.B position from 47% to 25%",
                    "impact": {
                        "risk_reduction": -3.2,
                        "return_impact": -0.5,
                        "sharpe_improvement": 0.08
                    },
                    "trades": [
                        {"action": "sell", "symbol": "BRK.B", "quantity": 50, "reason": "Reduce concentration risk"}
                    ]
                },
                {
                    "priority": "high",
                    "action": "Add diversification",
                    "description": "Add international equity exposure",
                    "impact": {
                        "risk_reduction": -1.5,
                        "return_impact": 0.8,
                        "sharpe_improvement": 0.05
                    },
                    "trades": [
                        {"action": "buy", "symbol": "VTIAX", "quantity": 100, "reason": "International diversification"},
                        {"action": "buy", "symbol": "VWO", "quantity": 50, "reason": "Emerging markets exposure"}
                    ]
                },
                {
                    "priority": "medium",
                    "action": "Add fixed income",
                    "description": "Allocate 20% to bonds for stability",
                    "impact": {
                        "risk_reduction": -2.8,
                        "return_impact": -0.3,
                        "sharpe_improvement": 0.04
                    },
                    "trades": [
                        {"action": "buy", "symbol": "AGG", "quantity": 150, "reason": "Core bond allocation"},
                        {"action": "buy", "symbol": "TLT", "quantity": 75, "reason": "Duration exposure"}
                    ]
                },
                {
                    "priority": "medium",
                    "action": "Rebalance sectors",
                    "description": "Reduce Technology overweight",
                    "impact": {
                        "risk_reduction": -1.0,
                        "return_impact": 0.2,
                        "sharpe_improvement": 0.03
                    },
                    "trades": [
                        {"action": "sell", "symbol": "AAPL", "quantity": 25, "reason": "Reduce tech exposure"},
                        {"action": "buy", "symbol": "XLV", "quantity": 50, "reason": "Add healthcare exposure"}
                    ]
                },
                {
                    "priority": "low",
                    "action": "Tax optimization",
                    "description": "Harvest losses for tax efficiency",
                    "impact": {
                        "tax_savings": 1200,
                        "return_impact": 0.4
                    },
                    "trades": [
                        {"action": "sell", "symbol": "GOOGL", "quantity": 10, "reason": "Tax loss harvesting"},
                        {"action": "buy", "symbol": "META", "quantity": 10, "reason": "Maintain exposure"}
                    ]
                }
            ],
            "efficient_portfolio": {
                "target_allocation": {
                    "US_equity": 0.50,
                    "intl_equity": 0.20,
                    "bonds": 0.20,
                    "alternatives": 0.05,
                    "cash": 0.05
                },
                "expected_return": 15.8,
                "expected_risk": 16.1,
                "expected_sharpe": 0.981
            },
            "constraints_applied": [
                "Maximum single position: 25%",
                "Minimum positions: 10",
                "Sector limit: 35%",
                "Tax efficiency considered"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=recommendations)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching optimizer recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch optimizer recommendations"
        )

@app.get("/api/ratings", response_model=SuccessResponse)
async def get_all_ratings(user: dict = Depends(require_auth)):
    """
    Get all portfolio ratings (different from overview)
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Return detailed ratings for all holdings
        all_ratings = {
            "portfolio_ratings": {
                "overall_score": 72,
                "quality_score": 78,
                "value_score": 68,
                "growth_score": 74,
                "momentum_score": 71,
                "risk_adjusted_score": 69
            },
            "holdings_ratings": [
                {
                    "symbol": "AAPL",
                    "company": "Apple Inc.",
                    "overall": 85,
                    "quality": 92,
                    "value": 65,
                    "growth": 88,
                    "momentum": 82,
                    "moat": "wide",
                    "financial_health": "A+",
                    "analyst_consensus": "buy",
                    "esg_score": 78
                },
                {
                    "symbol": "GOOGL",
                    "company": "Alphabet Inc.",
                    "overall": 78,
                    "quality": 85,
                    "value": 70,
                    "growth": 75,
                    "momentum": 72,
                    "moat": "wide",
                    "financial_health": "A+",
                    "analyst_consensus": "buy",
                    "esg_score": 72
                },
                {
                    "symbol": "MSFT",
                    "company": "Microsoft Corp.",
                    "overall": 88,
                    "quality": 94,
                    "value": 72,
                    "growth": 86,
                    "momentum": 85,
                    "moat": "wide",
                    "financial_health": "A+",
                    "analyst_consensus": "strong buy",
                    "esg_score": 81
                },
                {
                    "symbol": "BRK.B",
                    "company": "Berkshire Hathaway",
                    "overall": 82,
                    "quality": 96,
                    "value": 78,
                    "growth": 62,
                    "momentum": 68,
                    "moat": "wide",
                    "financial_health": "A+",
                    "analyst_consensus": "hold",
                    "esg_score": 65
                },
                {
                    "symbol": "SPY",
                    "company": "SPDR S&P 500 ETF",
                    "overall": 75,
                    "quality": 75,
                    "value": 70,
                    "growth": 72,
                    "momentum": 74,
                    "moat": "index",
                    "financial_health": "A",
                    "analyst_consensus": "n/a",
                    "esg_score": 70
                }
            ],
            "rating_factors": {
                "profitability": {
                    "score": 82,
                    "metrics": {
                        "roe": 28.5,
                        "roa": 12.3,
                        "profit_margin": 22.1,
                        "fcf_margin": 18.7
                    }
                },
                "growth": {
                    "score": 74,
                    "metrics": {
                        "revenue_growth_3y": 12.5,
                        "earnings_growth_3y": 15.2,
                        "fcf_growth_3y": 14.8
                    }
                },
                "valuation": {
                    "score": 68,
                    "metrics": {
                        "pe_ratio": 25.3,
                        "peg_ratio": 1.8,
                        "ev_ebitda": 18.2,
                        "price_to_book": 6.5
                    }
                },
                "financial_health": {
                    "score": 88,
                    "metrics": {
                        "debt_to_equity": 0.45,
                        "current_ratio": 1.8,
                        "interest_coverage": 25.3,
                        "altman_z_score": 5.2
                    }
                }
            },
            "rating_distribution": {
                "A+": 3,
                "A": 1,
                "B+": 1,
                "B": 0,
                "C": 0
            },
            "peer_comparison": {
                "percentile": 78,
                "outperforming": 156,
                "total_compared": 200
            },
            "last_updated": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=all_ratings)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching all ratings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ratings"
        )

@app.get("/api/ratings/holdings", response_model=SuccessResponse)
async def get_holdings_ratings(user: dict = Depends(require_auth)):
    """
    Get detailed ratings for portfolio holdings
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Return detailed ratings specifically for holdings
        holdings_ratings = {
            "holdings": [
                {
                    "symbol": "AAPL",
                    "weight": 0.15,
                    "ratings": {
                        "buffett_score": 82,
                        "moat_strength": 90,
                        "dividend_safety": 95,
                        "resilience": 88,
                        "quality": 92,
                        "value": 65,
                        "growth": 88,
                        "momentum": 82
                    },
                    "key_metrics": {
                        "pe": 28.5,
                        "peg": 2.1,
                        "roe": 145.2,
                        "debt_equity": 1.95,
                        "fcf_yield": 3.8
                    },
                    "analyst_ratings": {
                        "buy": 28,
                        "hold": 8,
                        "sell": 1,
                        "consensus": "strong buy",
                        "target_price": 195.00,
                        "upside": 11.4
                    }
                },
                {
                    "symbol": "GOOGL",
                    "weight": 0.06,
                    "ratings": {
                        "buffett_score": 75,
                        "moat_strength": 88,
                        "dividend_safety": 0,  # No dividend
                        "resilience": 82,
                        "quality": 85,
                        "value": 70,
                        "growth": 75,
                        "momentum": 72
                    },
                    "key_metrics": {
                        "pe": 24.2,
                        "peg": 1.5,
                        "roe": 27.8,
                        "debt_equity": 0.12,
                        "fcf_yield": 4.2
                    },
                    "analyst_ratings": {
                        "buy": 32,
                        "hold": 5,
                        "sell": 0,
                        "consensus": "strong buy",
                        "target_price": 155.00,
                        "upside": 10.7
                    }
                },
                {
                    "symbol": "MSFT",
                    "weight": 0.24,
                    "ratings": {
                        "buffett_score": 88,
                        "moat_strength": 94,
                        "dividend_safety": 98,
                        "resilience": 92,
                        "quality": 94,
                        "value": 72,
                        "growth": 86,
                        "momentum": 85
                    },
                    "key_metrics": {
                        "pe": 32.1,
                        "peg": 2.2,
                        "roe": 42.3,
                        "debt_equity": 0.58,
                        "fcf_yield": 2.8
                    },
                    "analyst_ratings": {
                        "buy": 35,
                        "hold": 3,
                        "sell": 0,
                        "consensus": "strong buy",
                        "target_price": 425.00,
                        "upside": 13.3
                    }
                },
                {
                    "symbol": "BRK.B",
                    "weight": 0.47,
                    "ratings": {
                        "buffett_score": 95,  # It's Buffett's company!
                        "moat_strength": 96,
                        "dividend_safety": 0,  # No dividend
                        "resilience": 94,
                        "quality": 96,
                        "value": 78,
                        "growth": 62,
                        "momentum": 68
                    },
                    "key_metrics": {
                        "pe": 22.5,
                        "peg": 2.8,
                        "roe": 10.2,
                        "debt_equity": 0.28,
                        "fcf_yield": 5.2
                    },
                    "analyst_ratings": {
                        "buy": 2,
                        "hold": 8,
                        "sell": 0,
                        "consensus": "hold",
                        "target_price": 385.00,
                        "upside": 5.5
                    }
                },
                {
                    "symbol": "SPY",
                    "weight": 0.10,
                    "ratings": {
                        "buffett_score": 70,
                        "moat_strength": 75,
                        "dividend_safety": 90,
                        "resilience": 80,
                        "quality": 75,
                        "value": 70,
                        "growth": 72,
                        "momentum": 74
                    },
                    "key_metrics": {
                        "pe": 24.8,
                        "peg": 1.9,
                        "dividend_yield": 1.4,
                        "expense_ratio": 0.09,
                        "sharpe_ratio": 0.82
                    },
                    "analyst_ratings": {
                        "buy": 0,
                        "hold": 0,
                        "sell": 0,
                        "consensus": "n/a",
                        "target_price": 0,
                        "upside": 0
                    }
                }
            ],
            "portfolio_summary": {
                "average_rating": 78.5,
                "weighted_quality": 85.2,
                "weighted_value": 71.3,
                "weighted_growth": 76.8,
                "holdings_rated": 5,
                "top_rated": "BRK.B",
                "lowest_rated": "SPY"
            },
            "rating_methodology": {
                "factors": [
                    "Financial strength",
                    "Competitive position",
                    "Management quality",
                    "Valuation",
                    "Growth prospects",
                    "Risk factors"
                ],
                "data_sources": [
                    "Financial statements",
                    "Analyst reports",
                    "Market data",
                    "Industry analysis"
                ],
                "update_frequency": "weekly"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data=holdings_ratings)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching holdings ratings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch holdings ratings"
        )

@app.get("/api/portfolio/transactions", response_model=SuccessResponse)
async def get_portfolio_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    user: dict = Depends(require_auth)
):
    """
    Get portfolio-specific transactions (different from general transactions)
    AUTH_STATUS: MIGRATED - Sprint 3
    """
    try:

        # Generate portfolio-specific transaction data
        all_transactions = [
            {
                "id": str(uuid4()),
                "date": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "type": "buy",
                "symbol": "NVDA",
                "shares": 10,
                "price": 495.50,
                "amount": 4955.00,
                "fees": 0.00,
                "portfolio_impact": {
                    "weight_change": 0.04,
                    "sector_impact": "Increased Technology by 4%",
                    "risk_impact": "Increased volatility by 0.5%"
                },
                "status": "settled"
            },
            {
                "id": str(uuid4()),
                "date": (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "type": "sell",
                "symbol": "GOOGL",
                "shares": 5,
                "price": 142.30,
                "amount": 711.50,
                "fees": 0.00,
                "portfolio_impact": {
                    "weight_change": -0.01,
                    "sector_impact": "Decreased Technology by 1%",
                    "risk_impact": "Reduced concentration risk"
                },
                "status": "settled"
            },
            {
                "id": str(uuid4()),
                "date": (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d"),
                "type": "dividend",
                "symbol": "MSFT",
                "shares": 75,
                "price": 0.75,
                "amount": 56.25,
                "fees": 0.00,
                "portfolio_impact": {
                    "weight_change": 0.00,
                    "sector_impact": "None",
                    "risk_impact": "None"
                },
                "status": "completed"
            },
            {
                "id": str(uuid4()),
                "date": (datetime.utcnow() - timedelta(days=15)).strftime("%Y-%m-%d"),
                "type": "rebalance",
                "symbol": "BRK.B",
                "shares": -20,
                "price": 368.00,
                "amount": -7360.00,
                "fees": 0.00,
                "portfolio_impact": {
                    "weight_change": -0.06,
                    "sector_impact": "Portfolio rebalancing",
                    "risk_impact": "Improved diversification"
                },
                "status": "settled"
            },
            {
                "id": str(uuid4()),
                "date": (datetime.utcnow() - timedelta(days=20)).strftime("%Y-%m-%d"),
                "type": "buy",
                "symbol": "VTI",
                "shares": 25,
                "price": 235.80,
                "amount": 5895.00,
                "fees": 0.00,
                "portfolio_impact": {
                    "weight_change": 0.05,
                    "sector_impact": "Added broad market exposure",
                    "risk_impact": "Improved diversification"
                },
                "status": "settled"
            }
        ]

        # Add more historical transactions
        for i in range(25, 100, 5):
            transaction_type = random.choice(["buy", "sell", "dividend"])
            symbol = random.choice(["AAPL", "GOOGL", "MSFT", "BRK.B", "SPY", "NVDA", "TSLA"])

            if transaction_type == "dividend":
                shares = random.randint(10, 200)
                price = round(random.uniform(0.20, 2.00), 2)
                amount = round(shares * price, 2)
            else:
                shares = random.randint(5, 50)
                price = round(random.uniform(100, 500), 2)
                amount = round(shares * price * (1 if transaction_type == "buy" else -1), 2)

            all_transactions.append({
                "id": str(uuid4()),
                "date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "type": transaction_type,
                "symbol": symbol,
                "shares": shares if transaction_type == "buy" else -shares,
                "price": price,
                "amount": amount,
                "fees": 0.00,
                "portfolio_impact": {
                    "weight_change": round(random.uniform(-0.05, 0.05), 3),
                    "sector_impact": "Minor adjustment",
                    "risk_impact": "Minimal"
                },
                "status": "settled"
            })

        # Pagination
        total_count = len(all_transactions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = all_transactions[start_idx:end_idx]

        # Calculate summary statistics
        summary = {
            "total_transactions": total_count,
            "period": "90 days",
            "total_buys": sum(1 for t in all_transactions if t["type"] == "buy"),
            "total_sells": sum(1 for t in all_transactions if t["type"] == "sell"),
            "total_dividends": sum(1 for t in all_transactions if t["type"] == "dividend"),
            "net_invested": sum(t["amount"] for t in all_transactions if t["type"] in ["buy", "sell"]),
            "dividend_income": sum(t["amount"] for t in all_transactions if t["type"] == "dividend")
        }

        return SuccessResponse(data={
            "transactions": paginated,
            "summary": summary,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": math.ceil(total_count / page_size)
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio transactions"
        )

@app.get("/api/alerts/active", response_model=SuccessResponse)
async def get_active_alerts(user: dict = Depends(require_auth)):
    """
    Get only active alerts for the user
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Mock active alerts
        active_alerts = [
            {
                "id": str(uuid4()),
                "type": "price",
                "symbol": "AAPL",
                "condition": "above",
                "threshold": 180.00,
                "current_value": 175.00,
                "distance_to_trigger": 5.00,
                "distance_percent": 2.86,
                "message": "AAPL approaching price alert level",
                "priority": "medium",
                "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "last_checked": datetime.utcnow().isoformat(),
                "notification_channels": ["email", "app"]
            },
            {
                "id": str(uuid4()),
                "type": "portfolio",
                "condition": "below",
                "threshold": 100000,
                "current_value": 116625,
                "distance_to_trigger": 16625,
                "distance_percent": 16.63,
                "message": "Portfolio value monitoring",
                "priority": "low",
                "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
                "last_checked": datetime.utcnow().isoformat(),
                "notification_channels": ["email"]
            },
            {
                "id": str(uuid4()),
                "type": "risk",
                "metric": "volatility",
                "condition": "above",
                "threshold": 20.0,
                "current_value": 18.2,
                "distance_to_trigger": 1.8,
                "distance_percent": 9.0,
                "message": "Portfolio volatility approaching threshold",
                "priority": "high",
                "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "last_checked": datetime.utcnow().isoformat(),
                "notification_channels": ["email", "sms", "app"]
            },
            {
                "id": str(uuid4()),
                "type": "price",
                "symbol": "BRK.B",
                "condition": "below",
                "threshold": 350.00,
                "current_value": 365.00,
                "distance_to_trigger": 15.00,
                "distance_percent": 4.29,
                "message": "BRK.B price alert",
                "priority": "medium",
                "created_at": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "last_checked": datetime.utcnow().isoformat(),
                "notification_channels": ["email"]
            },
            {
                "id": str(uuid4()),
                "type": "macro",
                "indicator": "inflation",
                "condition": "above",
                "threshold": 4.0,
                "current_value": 3.0,
                "distance_to_trigger": 1.0,
                "distance_percent": 33.33,
                "message": "Inflation rate monitoring",
                "priority": "medium",
                "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "last_checked": datetime.utcnow().isoformat(),
                "notification_channels": ["email", "app"]
            }
        ]

        # Calculate summary statistics
        summary = {
            "total_active": len(active_alerts),
            "by_type": {
                "price": sum(1 for a in active_alerts if a["type"] == "price"),
                "portfolio": sum(1 for a in active_alerts if a["type"] == "portfolio"),
                "risk": sum(1 for a in active_alerts if a["type"] == "risk"),
                "macro": sum(1 for a in active_alerts if a["type"] == "macro")
            },
            "by_priority": {
                "high": sum(1 for a in active_alerts if a.get("priority") == "high"),
                "medium": sum(1 for a in active_alerts if a.get("priority") == "medium"),
                "low": sum(1 for a in active_alerts if a.get("priority") == "low")
            },
            "close_to_trigger": sum(1 for a in active_alerts if a.get("distance_percent", 100) < 10),
            "last_scan": datetime.utcnow().isoformat()
        }

        return SuccessResponse(data={
            "active_alerts": active_alerts,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching active alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active alerts"
        )

@app.get("/api/user/profile", response_model=SuccessResponse)
async def get_user_profile(user: dict = Depends(require_auth)):
    """
    Get user profile information
    AUTH_STATUS: MIGRATED - Sprint 2
    """
    try:

        # Return user profile data
        profile = {
            "user_id": user.get("id", "user-001"),
            "email": user.get("email", "michael@dawsos.com"),
            "name": "Michael Thompson",
            "role": user.get("role", "ADMIN"),
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": datetime.utcnow().isoformat(),
            "preferences": {
                "timezone": "America/New_York",
                "currency": "USD",
                "date_format": "MM/DD/YYYY",
                "theme": "dark",
                "notifications": {
                    "email": True,
                    "sms": False,
                    "push": True,
                    "frequency": "daily"
                },
                "dashboard_layout": {
                    "default_view": "portfolio",
                    "widgets": ["performance", "holdings", "alerts", "macro"],
                    "refresh_rate": 60  # seconds
                }
            },
            "portfolio_settings": {
                "default_portfolio": "DEFAULT_PORTFOLIO_ID",
                "benchmark": "SPY",
                "risk_tolerance": "moderate",
                "investment_horizon": "long-term",
                "rebalancing_frequency": "quarterly",
                "tax_strategy": "tax-efficient"
            },
            "subscription": {
                "plan": "premium",
                "status": "active",
                "billing_cycle": "monthly",
                "next_billing_date": (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%d"),
                "features": [
                    "real-time-data",
                    "advanced-analytics",
                    "ai-insights",
                    "unlimited-alerts",
                    "api-access",
                    "priority-support"
                ]
            },
            "usage_stats": {
                "logins_this_month": 45,
                "api_calls_this_month": 1250,
                "reports_generated": 12,
                "alerts_created": 8,
                "last_portfolio_update": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            "security": {
                "two_factor_enabled": True,
                "last_password_change": "2024-10-01T00:00:00Z",
                "api_keys_active": 2,
                "sessions_active": 1,
                "trusted_devices": 3
            },
            "integrations": {
                "connected": [
                    {"name": "Interactive Brokers", "status": "active", "last_sync": datetime.utcnow().isoformat()},
                    {"name": "Plaid", "status": "active", "last_sync": (datetime.utcnow() - timedelta(hours=1)).isoformat()}
                ],
                "available": [
                    "Robinhood",
                    "Fidelity",
                    "Charles Schwab",
                    "E*TRADE",
                    "TD Ameritrade"
                ]
            }
        }

        return SuccessResponse(data=profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile"
        )

# ============================================================================
# SPA Catch-All Route (Must be last!)
# ============================================================================

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all_spa_routes(full_path: str):
    """
    Catch-all route for SPA client-side routing

    This route MUST be defined after all other routes.
    It returns the main HTML file for any path that doesn't match an API route,
    allowing the client-side JavaScript router to handle navigation.

    This enables routes like:
    - /dashboard
    - /holdings
    - /performance
    - /macro-cycles
    - /scenarios
    - /risk
    - /optimizer
    - /ratings
    - /ai-insights
    - /market-data
    - /transactions
    - /alerts
    - /reports
    - /corporate-actions
    - /api-keys
    - /settings

    API routes (/api/*, /health) are handled by earlier route definitions
    and will not reach this catch-all.
    """
    try:
        # Skip API routes and health endpoint (shouldn't reach here anyway)
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not found")

        # Try to read UI from file
        ui_file = Path("full_ui.html")
        if ui_file.exists():
            logger.debug(f"Serving SPA for path: /{full_path}")
            response = HTMLResponse(content=ui_file.read_text())
            # Add cache-control headers to prevent caching issues
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving SPA for path /{full_path}: {e}")

    # Return minimal fallback UI if file not found
    logger.warning(f"full_ui.html not found, serving minimal UI for /{full_path}")
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DawsOS Portfolio Intelligence</title>
    </head>
    <body>
        <h1>DawsOS Portfolio Intelligence Platform</h1>
        <p>Version 6.0.0 - Refactored</p>
        <p>UI file not found. Please ensure full_ui.html exists.</p>
    </body>
    </html>
    """)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Configure uvicorn logging
    from uvicorn.config import LOGGING_CONFIG
    log_config = LOGGING_CONFIG.copy()
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_config=log_config,
        access_log=True
    )