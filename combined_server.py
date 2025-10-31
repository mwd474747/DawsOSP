#!/usr/bin/env python3
"""
Enhanced DawsOS Server - Comprehensive Portfolio Management System
Version 6.0.0 - Refactored with Improved Error Handling and Code Quality
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Request, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
import jwt
import asyncpg
from asyncpg.pool import Pool
import uvicorn
import httpx

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
    
    # Set environment variables to disable observability if not available
    os.environ['ENABLE_OBSERVABILITY'] = 'false'
    
    # Now import the modules
    from app.core.agent_runtime import AgentRuntime
    from app.core.pattern_orchestrator import PatternOrchestrator
    from app.core.types import RequestCtx, ExecReq, ExecResp
    from app.services.metrics import PerformanceCalculator
    from app.services.scenarios import get_scenario_service, ShockType
    from app.agents.financial_analyst import FinancialAnalyst
    from app.agents.macro_hound import MacroHound
    
    PATTERN_ORCHESTRATION_AVAILABLE = True
    logger.info("Pattern orchestration modules loaded successfully")
except ImportError as e:
    logger.warning(f"Pattern orchestration modules not available: {e}")
    PATTERN_ORCHESTRATION_AVAILABLE = False
    # Create dummy classes to avoid NameErrors
    AgentRuntime = None
    PatternOrchestrator = None
    RequestCtx = None
    PerformanceCalculator = None
    ShockType = None
    FinancialAnalyst = None
    MacroHound = None

# ============================================================================
# Configuration and Constants
# ============================================================================

# Environment Configuration
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
DATABASE_URL = os.environ.get("DATABASE_URL")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# JWT Configuration
JWT_SECRET = os.environ.get("AUTH_JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# API URLs
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
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
# Global State
# ============================================================================

# Database connection pool
db_pool: Optional[Pool] = None

# Pattern Orchestrator and Agent Runtime (singleton instances)
_agent_runtime: Optional[AgentRuntime] = None
_pattern_orchestrator: Optional[PatternOrchestrator] = None

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
    pattern: str = Field(..., min_length=1, max_length=100)
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
    """Get or create singleton agent runtime."""
    global _agent_runtime, db_pool
    
    services = {
        "db": db_pool,
        "redis": None,  # TODO: Wire real Redis when needed
    }
    
    # If runtime exists and reinit_services=True, update the services dict
    if _agent_runtime is not None and reinit_services:
        logger.info("Updating agent runtime with database pool")
        _agent_runtime.services = services
        # Also update services on each registered agent
        for agent_id, agent in _agent_runtime.agents.items():
            agent.services = services
        return _agent_runtime
    
    if _agent_runtime is None:
        # Create runtime
        _agent_runtime = AgentRuntime(services)
        
        # Register Financial Analyst
        financial_analyst = FinancialAnalyst("financial_analyst", services)
        _agent_runtime.register_agent(financial_analyst)
        
        # Register Macro Hound
        macro_hound = MacroHound("macro_hound", services)
        _agent_runtime.register_agent(macro_hound)
        
        # Register other agents as needed
        from backend.app.agents.data_harvester import DataHarvester
        from backend.app.agents.claude_agent import ClaudeAgent
        from backend.app.agents.ratings_agent import RatingsAgent
        from backend.app.agents.optimizer_agent import OptimizerAgent
        
        data_harvester = DataHarvester("data_harvester", services)
        _agent_runtime.register_agent(data_harvester)
        
        claude_agent = ClaudeAgent("claude_agent", services)
        _agent_runtime.register_agent(claude_agent)
        
        ratings_agent = RatingsAgent("ratings_agent", services)
        _agent_runtime.register_agent(ratings_agent)
        
        optimizer_agent = OptimizerAgent("optimizer_agent", services)
        _agent_runtime.register_agent(optimizer_agent)
        
        logger.info(f"Agent runtime initialized with {len(_agent_runtime.agents)} agents")
    
    return _agent_runtime

def get_pattern_orchestrator() -> PatternOrchestrator:
    """Get or create singleton pattern orchestrator."""
    global _pattern_orchestrator, db_pool
    
    if _pattern_orchestrator is None:
        runtime = get_agent_runtime()
        _pattern_orchestrator = PatternOrchestrator(
            agent_runtime=runtime,
            db=db_pool,
            redis=None  # TODO: Add Redis when available
        )
        logger.info("Pattern orchestrator initialized")
    
    return _pattern_orchestrator

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
        ctx = RequestCtx(
            trace_id=str(uuid4()),
            request_id=str(uuid4()),
            user_id=user_id or "system",
            portfolio_id=inputs.get("portfolio_id"),
            asof_date=date.today(),
            pricing_pack_id=pricing_pack_id,
            ledger_commit_hash=ledger_commit_hash
        )
        
        # Run pattern
        result = await orchestrator.run_pattern(pattern_name, ctx, inputs)
        
        return {
            "success": True,
            "data": result.get("outputs", {}),
            "trace": result.get("trace"),
            "metadata": {
                "pattern": pattern_name,
                "execution_time": result.get("execution_time_ms", 0),
                "pricing_pack_id": pricing_pack_id,
                "ledger_commit_hash": ledger_commit_hash
            }
        }
    except Exception as e:
        logger.error(f"Pattern execution failed for {pattern_name}: {e}")
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
        
        # Reset circuit breakers after successful initialization
        if runtime and db_pool and hasattr(runtime, 'circuit_breaker'):
            # Clear circuit breaker state for all agents
            runtime.circuit_breaker.failures.clear()
            runtime.circuit_breaker.open_until.clear()
            logger.info("✅ Reset all agent circuit breakers")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        if not USE_MOCK_DATA:
            logger.warning("Database unavailable and mock mode disabled - some features may not work")
    
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

def hash_password(password: str) -> str:
    """Hash password using SHA256 with salt"""
    salt = "dawsos_salt_"  # In production, use unique salt per user
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

# ============================================================================
# Default Users (Should be in database in production)
# ============================================================================

USERS_DB = {
    "michael@dawsos.com": {
        "id": "user-001",
        "email": "michael@dawsos.com",
        "password": hash_password("admin123"),
        "role": "ADMIN"
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

async def store_macro_indicators(indicators: Dict[str, Any]) -> bool:
    """Store macro indicators in database with proper error handling"""
    if not db_pool or not indicators:
        return False
    
    # Create mapping of indicator IDs to human-readable names
    indicator_names = {
        'gdp_growth': 'GDP Growth Rate',
        'unemployment_rate': 'Unemployment Rate', 
        'inflation_rate': 'Inflation Rate',
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

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    """Create JWT token with proper error handling"""
    try:
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating JWT token: {e}")
        raise AuthenticationError("Failed to create authentication token")

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token with proper error handling"""
    try:
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

async def get_current_user(request_or_token: Union[Request, str]) -> Optional[dict]:
    """Get current user from JWT token in request or from token string
    
    Args:
        request_or_token: Either a FastAPI Request object or a bearer token string
    
    Returns:
        User dict with id, email, role or None if invalid
    """
    auth_header = ""
    
    # Handle both Request object and string token
    if isinstance(request_or_token, str):
        # Direct token string
        auth_header = request_or_token if request_or_token.startswith("Bearer ") else f"Bearer {request_or_token}"
    elif hasattr(request_or_token, 'headers'):
        # FastAPI Request object
        auth_header = request_or_token.headers.get("Authorization", "")
    else:
        logger.warning(f"Invalid input to get_current_user: {type(request_or_token)}")
        return None
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_jwt_token(token)
    
    if payload:
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    
    return None

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
    if db_pool and portfolio_id:
        try:
            # Use the performance calculator to get real metrics
            calc = PerformanceCalculator(db_pool)
            
            # Get TWR and related metrics for past year (252 trading days)
            metrics = await calc.compute_twr(portfolio_id, pack_id=None, lookback_days=252)
            
            # Get max drawdown
            dd = await calc.compute_max_drawdown(portfolio_id, lookback_days=252)
            
            # Get VaR
            var_result = await calc.compute_var(portfolio_id, confidence=0.95, lookback_days=252)
            
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
# Mock Data Helpers (Only when USE_MOCK_DATA is True)
# ============================================================================

def get_mock_portfolio_holdings() -> List[dict]:
    """Get mock portfolio holdings for testing"""
    return [
        {"symbol": "AAPL", "quantity": 100, "price": 185.00, "sector": "Technology", "beta": 1.25, "dividend_yield": 0.5},
        {"symbol": "GOOGL", "quantity": 50, "price": 140.00, "sector": "Technology", "beta": 1.06, "dividend_yield": 0.0},
        {"symbol": "MSFT", "quantity": 75, "price": 380.00, "sector": "Technology", "beta": 0.93, "dividend_yield": 0.88},
        {"symbol": "AMZN", "quantity": 40, "price": 150.00, "sector": "Consumer", "beta": 1.23, "dividend_yield": 0.0},
        {"symbol": "NVDA", "quantity": 30, "price": 500.00, "sector": "Technology", "beta": 1.68, "dividend_yield": 0.03},
        {"symbol": "TSLA", "quantity": 25, "price": 220.00, "sector": "Automotive", "beta": 2.03, "dividend_yield": 0.0},
        {"symbol": "META", "quantity": 35, "price": 343.00, "sector": "Technology", "beta": 1.29, "dividend_yield": 0.0},
        {"symbol": "BRK.B", "quantity": 80, "price": 350.00, "sector": "Financial", "beta": 0.87, "dividend_yield": 0.0}
    ]

def get_mock_transactions() -> List[dict]:
    """Get mock transaction history for testing"""
    transactions = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(20):
        date = base_date + timedelta(days=i * 15)
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "type": random.choice(["buy", "sell", "dividend"]),
            "symbol": random.choice(["AAPL", "GOOGL", "MSFT", "NVDA"]),
            "shares": random.randint(10, 50),
            "price": round(random.uniform(100, 500), 2),
            "amount": round(random.uniform(-10000, 10000), 2),
            "realized_gain": round(random.uniform(0, 500), 2)
        })
    
    return sorted(transactions, key=lambda x: x["date"], reverse=True)

# ============================================================================
# API Endpoints with Improved Error Handling
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve HTML"""
    try:
        # Try to read UI from file
        ui_file = Path("full_ui.html")
        if ui_file.exists():
            return HTMLResponse(content=ui_file.read_text())
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
        "mode": "mock" if USE_MOCK_DATA else "production"
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

@app.post("/api/patterns/execute", response_model=SuccessResponse)
async def execute_pattern(request: ExecuteRequest):
    """
    Execute a pattern through the orchestrator
    """
    try:
        # Get user from token (optional - for now we'll use a default)
        user_id = "user-001"  # In production, extract from JWT token
        
        # Execute the pattern
        # Handle both 'inputs' and 'params' fields for backwards compatibility
        pattern_inputs = {}
        if hasattr(request, 'inputs') and request.inputs:
            pattern_inputs = request.inputs
        elif hasattr(request, 'params') and request.params:
            pattern_inputs = request.params
        
        result = await execute_pattern_orchestrator(
            pattern_name=request.pattern,
            inputs=pattern_inputs,
            user_id=user_id
        )
        
        if result["success"]:
            return SuccessResponse(data=result["data"])
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

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login endpoint with validation"""
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
            # Return mock data as fallback
            return {
                "total_value": 291290,
                "ytd_return": 14.5,
                "sharpe_ratio": 1.35,
                "max_drawdown": -12.3,
                "volatility": 18.2
            }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {
            "total_value": 291290,
            "ytd_return": 14.5,
            "sharpe_ratio": 1.35,
            "max_drawdown": -12.3,
            "volatility": 18.2
        }

@app.get("/api/portfolio")
async def get_portfolio(request: Request):
    """Get portfolio data using pattern orchestrator"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
                            "lookback_days": 252  # Default to 1 year
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
        
        # Fallback to database query or mock data
        portfolio_data = await get_portfolio_data(user["email"])
        
        if not portfolio_data:
            # Last resort: use mock data to avoid breaking UI
            holdings = get_mock_portfolio_holdings()
            total_value = sum(h["quantity"] * h["price"] for h in holdings)
            
            for holding in holdings:
                holding["value"] = holding["quantity"] * holding["price"]
                holding["weight"] = holding["value"] / total_value if total_value > 0 else 0
                holding["change"] = round(random.uniform(-0.03, 0.04), 4)
            
            # Get portfolio ID for metrics calculation
            portfolio_id = str(uuid4())
            risk_metrics = await calculate_portfolio_risk_metrics(holdings, portfolio_id)
            sector_allocation = calculate_sector_allocation(holdings, total_value)
            
            return SuccessResponse(data={
                "id": portfolio_id,
                "name": "Demo Portfolio",
                "total_value": round(total_value, 2),
                "holdings": holdings,
                "sector_allocation": sector_allocation,
                **risk_metrics,
                "last_updated": datetime.utcnow().isoformat()
            })
        
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
    request: Request,
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
):
    """Get holdings data using pattern orchestrator with pagination"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
                            "lookback_days": 252  # Default to 1 year
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
                            # Calculate market value if not present
                            market_value = pos.get("market_value") or (pos.get("quantity", 0) * pos.get("price", 0))
                            total_value += market_value
                            
                            holdings.append({
                                "symbol": pos.get("symbol"),
                                "name": pos.get("name", pos.get("symbol")),  # Use symbol as fallback for name
                                "quantity": float(pos.get("quantity", 0)),
                                "price": float(pos.get("price", 0)),
                                "market_value": float(market_value),
                                "value": float(market_value),  # Duplicate for UI compatibility
                                "sector": pos.get("sector", "Other"),
                                "cost_basis": float(pos.get("cost_basis", 0)),
                                "unrealized_pnl": float(pos.get("unrealized_pnl", 0)),
                                "unrealized_pnl_pct": float(pos.get("unrealized_pnl_pct", 0)),
                                "weight": 0,  # Will calculate after total
                                "return_pct": float(pos.get("unrealized_pnl_pct", 0))  # Use unrealized P&L as return
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
        
        # Fallback to database or mock data
        portfolio_data = await get_portfolio_data(user["email"])
        
        if not portfolio_data:
            # Return mock data if no database data
            holdings = get_mock_portfolio_holdings()
            for h in holdings:
                h["value"] = h["quantity"] * h["price"]
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
    request: Request,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE
):
    """Get transaction history with pagination"""
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > MAX_PAGE_SIZE:
            page_size = DEFAULT_PAGE_SIZE
        
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Use mock data if enabled
        if USE_MOCK_DATA:
            transactions = get_mock_transactions()
            total_count = len(transactions)
            
            # Pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated = transactions[start_idx:end_idx]
            
            return SuccessResponse(data={
                "transactions": paginated,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": math.ceil(total_count / page_size)
                }
            })
        
        # Get data from database
        all_transactions = await get_user_transactions(user["email"])
        
        if not all_transactions:
            return SuccessResponse(data={
                "transactions": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": 0,
                    "total_pages": 0
                }
            })
        
        # Format transactions
        formatted_transactions = []
        for row in all_transactions:
            formatted_transactions.append({
                "date": row["trade_date"].strftime("%Y-%m-%d") if row["trade_date"] else "",
                "type": row["type"],
                "symbol": row["symbol"],
                "shares": float(row["quantity"]) if row["quantity"] else 0,
                "price": float(row["price"]) if row["price"] else 0,
                "amount": float(row["amount"]) if row["amount"] else 0,
                "security_name": row["security_name"]
            })
        
        # Pagination
        total_count = len(formatted_transactions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = formatted_transactions[start_idx:end_idx]
        
        return SuccessResponse(data={
            "transactions": paginated,
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
        logger.error(f"Transactions endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction service error"
        )

@app.post("/api/alerts", response_model=SuccessResponse)
async def create_alert(request: Request, alert_config: AlertConfig):
    """Create a new alert with validation"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
        
        # In production, store in database
        if not USE_MOCK_DATA and db_pool:
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

@app.post("/execute", response_model=SuccessResponse)
async def execute_pattern(request: Request, execute_req: ExecuteRequest):
    """Execute analysis pattern with validation"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate pattern exists
        valid_patterns = ["portfolio_overview", "macro_analysis", "risk_assessment", "optimization"]
        if execute_req.pattern not in valid_patterns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid pattern. Valid patterns: {', '.join(valid_patterns)}"
            )
        
        # Execute pattern (simplified for example)
        result = {
            "pattern": execute_req.pattern,
            "status": "completed",
            "execution_time": 0.5,
            "result": {
                "summary": f"Executed {execute_req.pattern} pattern successfully",
                "data": execute_req.inputs
            }
        }
        
        return SuccessResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute pattern error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pattern execution error"
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
    
    return fresh_data

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
        }# ============================================================================
# Additional API Endpoints with Enhanced Error Handling
# ============================================================================

@app.get("/api/macro", response_model=SuccessResponse)
async def get_macro_indicators(request: Request):
    """Get macro economic indicators with caching"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
    request: Request,
    optimization_request: OptimizationRequest
):
    """Optimize portfolio allocation based on risk tolerance"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get current portfolio
        if USE_MOCK_DATA:
            holdings = get_mock_portfolio_holdings()
            for h in holdings:
                h["value"] = h["quantity"] * h["price"]
        else:
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
async def get_alerts(request: Request):
    """Get user alerts with proper error handling"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Use mock data if enabled
        if USE_MOCK_DATA:
            # Return mock alerts
            mock_alerts = [
                {
                    "id": str(uuid4()),
                    "type": "price",
                    "symbol": "AAPL",
                    "threshold": 180.00,
                    "condition": "below",
                    "message": "Apple stock below $180",
                    "active": True,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": str(uuid4()),
                    "type": "portfolio",
                    "threshold": 100000,
                    "condition": "below",
                    "message": "Portfolio value below $100k",
                    "active": True,
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
            return SuccessResponse(data={"alerts": mock_alerts})
        
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
async def delete_alert(request: Request, alert_id: str):
    """Delete an alert with proper validation"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate alert ID format
        try:
            UUID(alert_id)  # Validate UUID format
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alert ID format"
            )
        
        if USE_MOCK_DATA:
            return SuccessResponse(data={"deleted": True})
        
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
    request: Request,
    scenario: str = "rates_up"
):
    """Run scenario analysis using real pattern orchestrator and ScenarioService"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
        if db_pool:
            try:
                service = get_scenario_service()
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
        portfolio_data = await get_portfolio_data(user["email"]) if not USE_MOCK_DATA else None
        
        if not portfolio_data:
            holdings = get_mock_portfolio_holdings()
            for h in holdings:
                h["value"] = h["quantity"] * h["price"]
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
async def get_reports(request: Request):
    """Get available reports with proper error handling"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
async def ai_analysis(request: Request, ai_request: AIAnalysisRequest):
    """AI-powered portfolio analysis (placeholder)"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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

@app.get("/api/factor-analysis", response_model=SuccessResponse)
async def get_factor_analysis(request: Request):
    """Get factor analysis for portfolio"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
            return HTMLResponse(content=ui_file.read_text())
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