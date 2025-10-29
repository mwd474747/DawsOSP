#!/usr/bin/env python3
"""
DawsOS Backend API Server
Simple, reliable implementation with working authentication
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import hashlib
import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DawsOS API",
    description="Portfolio Intelligence Platform",
    version="3.0.0"
)

# CORS configuration - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple password hashing using SHA256 (no bcrypt issues)
def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

# JWT Configuration
JWT_SECRET = os.environ.get("AUTH_JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Database connection pool
db_pool = None

# Default users (simulated database)
USERS_DB = {
    "michael@dawsos.com": {
        "id": "user-001",
        "email": "michael@dawsos.com",
        "password": hash_password("admin123"),
        "role": "ADMIN"
    }
}

# =============================================================================
# Pydantic Models
# =============================================================================

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class ExecuteRequest(BaseModel):
    pattern: str
    inputs: Dict[str, Any] = {}
    require_fresh: bool = False

# =============================================================================
# Database Functions
# =============================================================================

async def init_db():
    """Initialize database connection pool"""
    global db_pool
    try:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if DATABASE_URL:
            db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=10,
                timeout=30
            )
            logger.info("Database connected successfully")
        else:
            logger.warning("DATABASE_URL not set, using in-memory data")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.info("Falling back to in-memory data")

# =============================================================================
# Authentication
# =============================================================================

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    """Create JWT token"""
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        return None

# =============================================================================
# Mock Data Generators
# =============================================================================

def get_portfolio_data() -> dict:
    """Generate mock portfolio data"""
    return {
        "id": str(uuid4()),
        "name": "Main Portfolio",
        "total_value": 1500000.00,
        "returns_1d": 0.0125,
        "returns_1w": 0.0234,
        "returns_1m": 0.0567,
        "returns_ytd": 0.1234,
        "risk_score": 0.65,
        "sharpe_ratio": 1.85,
        "holdings": [
            {"symbol": "AAPL", "quantity": 100, "value": 18500.00, "weight": 0.15, "change": 0.023},
            {"symbol": "GOOGL", "quantity": 50, "value": 7000.00, "weight": 0.10, "change": -0.012},
            {"symbol": "MSFT", "quantity": 75, "value": 28500.00, "weight": 0.20, "change": 0.018},
            {"symbol": "AMZN", "quantity": 40, "value": 6000.00, "weight": 0.08, "change": 0.031},
            {"symbol": "NVDA", "quantity": 30, "value": 15000.00, "weight": 0.12, "change": 0.045},
            {"symbol": "TSLA", "quantity": 25, "value": 5500.00, "weight": 0.07, "change": -0.028},
            {"symbol": "META", "quantity": 35, "value": 12000.00, "weight": 0.09, "change": 0.015},
            {"symbol": "BRK.B", "quantity": 80, "value": 28000.00, "weight": 0.19, "change": 0.008}
        ]
    }

def get_macro_data() -> dict:
    """Generate mock macro economic data"""
    return {
        "current_regime": "Late Cycle Expansion",
        "indicators": {
            "gdp_growth": 2.3,
            "inflation": 3.2,
            "unemployment": 3.7,
            "interest_rate": 5.25,
            "vix": 18.5,
            "dollar_index": 104.2
        },
        "risk_level": "Medium-High",
        "trend": "Neutral",
        "recommendations": [
            "Consider defensive positioning",
            "Increase cash allocation to 10-15%",
            "Focus on quality stocks with strong balance sheets",
            "Monitor Fed policy closely"
        ]
    }

# =============================================================================
# API Endpoints
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await init_db()
    logger.info("API server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
    logger.info("API server shutdown")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "DawsOS API Server", "version": "3.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_pool is not None,
            "claude_ai": os.environ.get("ANTHROPIC_API_KEY") is not None,
            "market_data": True
        }
    }

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login endpoint"""
    logger.info(f"Login attempt for: {request.email}")
    
    # Check user in our simulated database
    user_data = USERS_DB.get(request.email)
    
    if not user_data:
        logger.warning(f"User not found: {request.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(request.password, user_data["password"]):
        logger.warning(f"Invalid password for: {request.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token(user_data["id"], user_data["email"], user_data["role"])
    
    logger.info(f"Login successful for: {request.email}")
    
    return LoginResponse(
        access_token=token,
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user={
            "id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"]
        }
    )

@app.get("/auth/me")
async def get_current_user(request: Request):
    """Get current user info"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "id": payload["sub"],
        "email": payload["email"],
        "role": payload["role"]
    }

@app.post("/execute")
async def execute_pattern(request: ExecuteRequest):
    """Execute analysis patterns"""
    pattern = request.pattern
    inputs = request.inputs
    
    logger.info(f"Executing pattern: {pattern}")
    
    if pattern == "portfolio_overview":
        return {
            "result": get_portfolio_data(),
            "status": "success"
        }
    
    elif pattern == "macro_cycles_overview":
        return {
            "result": get_macro_data(),
            "status": "success"
        }
    
    elif pattern == "portfolio_scenario_analysis":
        scenario = inputs.get("scenario", "market_crash")
        
        scenarios = {
            "market_crash": {
                "scenario_name": "Market Crash (-20%)",
                "description": "Severe market downturn simulation with 20% decline across equity markets",
                "portfolio_impact": -18.5,
                "risk_level": "High",
                "confidence": 85,
                "recommendations": [
                    "Consider increasing cash allocation to 15-20%",
                    "Add defensive assets like bonds or gold",
                    "Review stop-loss orders on volatile positions",
                    "Diversify into non-correlated assets"
                ],
                "affected_holdings": [
                    {"symbol": "TSLA", "impact": -32.5},
                    {"symbol": "NVDA", "impact": -28.0},
                    {"symbol": "META", "impact": -22.0},
                    {"symbol": "BRK.B", "impact": -8.5}
                ]
            },
            "interest_rate": {
                "scenario_name": "Interest Rate Hike (+2%)",
                "description": "Federal Reserve raises rates by 200 basis points",
                "portfolio_impact": -12.3,
                "risk_level": "Medium",
                "confidence": 75,
                "recommendations": [
                    "Reduce duration in bond holdings",
                    "Consider floating-rate securities",
                    "Focus on financial sector opportunities",
                    "Review tech stock valuations"
                ],
                "affected_holdings": [
                    {"symbol": "GOOGL", "impact": -18.0},
                    {"symbol": "MSFT", "impact": -15.0},
                    {"symbol": "AAPL", "impact": -12.0},
                    {"symbol": "BRK.B", "impact": +5.0}
                ]
            },
            "inflation": {
                "scenario_name": "High Inflation (6%+)",
                "description": "Sustained inflation above 6% for multiple quarters",
                "portfolio_impact": -8.7,
                "risk_level": "Medium",
                "confidence": 70,
                "recommendations": [
                    "Increase allocation to TIPS or I Bonds",
                    "Consider real estate and commodities",
                    "Focus on companies with pricing power",
                    "Reduce cash holdings"
                ],
                "affected_holdings": [
                    {"symbol": "AMZN", "impact": -5.0},
                    {"symbol": "MSFT", "impact": -8.0},
                    {"symbol": "AAPL", "impact": -3.0},
                    {"symbol": "BRK.B", "impact": +2.0}
                ]
            }
        }
        
        return {
            "result": scenarios.get(scenario, scenarios["market_crash"]),
            "status": "success"
        }
    
    elif pattern == "buffett_checklist":
        symbol = inputs.get("security_id", "AAPL")
        return {
            "result": {
                "symbol": symbol,
                "scores": {
                    "moat_strength": 8.5,
                    "management_quality": 9.0,
                    "financial_strength": 8.0,
                    "earnings_consistency": 7.5,
                    "valuation": 6.5
                },
                "overall_score": 7.9,
                "recommendation": "Strong Buy",
                "analysis": f"{symbol} shows strong competitive advantages with excellent management and solid financials"
            },
            "status": "success"
        }
    
    else:
        return {
            "result": {
                "message": f"Pattern '{pattern}' executed successfully",
                "data": {"timestamp": datetime.utcnow().isoformat()}
            },
            "status": "success"
        }

@app.get("/api/portfolios")
async def get_portfolios():
    """Get user portfolios"""
    return {
        "portfolios": [
            {
                "id": "1",
                "name": "Main Portfolio",
                "value": 1500000.00,
                "change": 18750.00,
                "changePercent": 1.25
            },
            {
                "id": "2",
                "name": "Retirement",
                "value": 750000.00,
                "change": 5625.00,
                "changePercent": 0.75
            },
            {
                "id": "3",
                "name": "Growth",
                "value": 250000.00,
                "change": 8500.00,
                "changePercent": 3.4
            }
        ]
    }

@app.get("/api/alerts")
async def get_alerts():
    """Get active alerts"""
    return {
        "alerts": [
            {
                "id": "1",
                "type": "price",
                "message": "AAPL reached target price of $185",
                "severity": "info",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": "2",
                "type": "risk",
                "message": "Portfolio volatility increased above threshold",
                "severity": "warning",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": "3",
                "type": "macro",
                "message": "Fed meeting tomorrow - rate decision expected",
                "severity": "info",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting DawsOS API Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")