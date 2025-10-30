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
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import json
import hashlib
from uuid import uuid4
import random
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import jwt
import asyncpg
from asyncpg.pool import Pool
import uvicorn
import httpx

# Import MacroDataAgent for enhanced macro data fetching
from backend.app.services.macro_data_agent import enhance_macro_data

# ============================================================================
# Configuration and Constants
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    
    @validator('email')
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
    require_fresh: bool = False
    
    @validator('inputs')
    def validate_inputs(cls, v):
        # Limit input size to prevent abuse
        if len(json.dumps(v)) > 10000:
            raise ValueError('Input data too large')
        return v

class AlertConfig(BaseModel):
    type: AlertType
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    threshold: float = Field(..., ge=0)
    condition: AlertCondition
    notification_channel: str = Field(default="email", min_length=1, max_length=50)
    
    @validator('symbol')
    def validate_symbol(cls, v, values):
        if values.get('type') == AlertType.PRICE and not v:
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
# Lifespan Context Manager (Replaces @app.on_event)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - replaces deprecated @app.on_event decorators
    """
    # Startup
    logger.info("Starting DawsOS Enhanced Server...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        if not USE_MOCK_DATA:
            logger.warning("Database unavailable and mock mode disabled - some features may not work")
    
    # Initialize other services
    logger.info(f"Server mode: {'MOCK' if USE_MOCK_DATA else 'PRODUCTION'}")
    logger.info("Enhanced server started successfully")
    
    yield  # Server is running
    
    # Shutdown
    logger.info("Shutting down DawsOS Enhanced Server...")
    
    # Clean up database connections
    global db_pool
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
                    
    except asyncpg.exceptions.TimeoutError:
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
    
    try:
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Clear existing indicators
                await conn.execute("DELETE FROM macro_indicators WHERE date = CURRENT_DATE")
                
                # Insert new indicators
                for name, value in indicators.items():
                    if isinstance(value, (int, float)):
                        await conn.execute("""
                            INSERT INTO macro_indicators (indicator_id, value, date)
                            VALUES ($1, $2, CURRENT_DATE)
                            ON CONFLICT (indicator_id, date) DO UPDATE
                            SET value = $2, updated_at = NOW()
                        """, name, float(value))
                
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

async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from JWT token in request"""
    auth_header = request.headers.get("Authorization", "")
    
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

def calculate_portfolio_risk_metrics(holdings: List[dict]) -> Dict[str, float]:
    """Calculate portfolio risk metrics with validation"""
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
    
    # Calculate weighted beta
    weighted_beta = 0
    for holding in holdings:
        weight = holding.get("value", 0) / total_value
        beta = holding.get("beta", 1.0)
        weighted_beta += weight * beta
    
    # Estimate other metrics
    portfolio_volatility = weighted_beta * 0.15  # Assume market vol of 15%
    
    # Simple risk score based on beta
    risk_score = min(max(weighted_beta / 2, 0), MAX_RISK_SCORE)
    
    # Placeholder for other metrics (should be calculated from historical data)
    sharpe_ratio = 0.8  # Placeholder
    max_drawdown = -0.08  # Placeholder
    var_95 = total_value * 0.02  # 2% VaR
    
    return {
        "portfolio_beta": round(weighted_beta, 2),
        "portfolio_volatility": round(portfolio_volatility, 4),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown": round(max_drawdown, 4),
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

@app.get("/api/portfolio")
async def get_portfolio(request: Request):
    """Get portfolio data with proper error handling"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Use mock data if enabled
        if USE_MOCK_DATA:
            holdings = get_mock_portfolio_holdings()
            total_value = sum(h["quantity"] * h["price"] for h in holdings)
            
            # Calculate metrics
            for holding in holdings:
                holding["value"] = holding["quantity"] * holding["price"]
                holding["weight"] = holding["value"] / total_value if total_value > 0 else 0
                holding["change"] = round(random.uniform(-0.03, 0.04), 4)
            
            risk_metrics = calculate_portfolio_risk_metrics(holdings)
            sector_allocation = calculate_sector_allocation(holdings, total_value)
            
            return SuccessResponse(data={
                "id": str(uuid4()),
                "name": "Mock Portfolio",
                "total_value": round(total_value, 2),
                "holdings": holdings,
                "sector_allocation": sector_allocation,
                **risk_metrics,
                "last_updated": datetime.utcnow().isoformat()
            })
        
        # Get data from database
        portfolio_data = await get_portfolio_data(user["email"])
        
        if not portfolio_data:
            return SuccessResponse(data={
                "id": str(uuid4()),
                "name": "Empty Portfolio",
                "total_value": 0,
                "holdings": [],
                "sector_allocation": {},
                "portfolio_beta": 0,
                "portfolio_volatility": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "var_95": 0,
                "risk_score": 0,
                "last_updated": datetime.utcnow().isoformat()
            })
        
        # Process portfolio data
        holdings = []
        total_value = 0
        
        for row in portfolio_data:
            holding = {
                "symbol": row["symbol"],
                "quantity": float(row["quantity"]),
                "price": float(row["price"]) if row["price"] else 0,
                "value": 0,
                "sector": row["sector"] or "Other",
                "beta": 1.0  # Default beta
            }
            holding["value"] = holding["quantity"] * holding["price"]
            total_value += holding["value"]
            
            if holding["value"] > 0:
                holdings.append(holding)
        
        # Calculate weights
        for holding in holdings:
            holding["weight"] = round(holding["value"] / total_value, 4) if total_value > 0 else 0
        
        risk_metrics = calculate_portfolio_risk_metrics(holdings)
        sector_allocation = calculate_sector_allocation(holdings, total_value)
        
        return SuccessResponse(data={
            "id": portfolio_data[0]["portfolio_id"] if portfolio_data else str(uuid4()),
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
        ).dict()
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
        ).dict()
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
        ).dict()
    )

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
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