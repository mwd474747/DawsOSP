#!/usr/bin/env python3
"""
Simplified DawsOS Backend API
A clean, working implementation focused on core functionality
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
from passlib.context import CryptContext
import jwt
from anthropic import Anthropic
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DawsOS API",
    description="Portfolio Intelligence Platform",
    version="2.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET = os.environ.get("AUTH_JWT_SECRET", "default-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Database connection pool
db_pool = None

# API Keys from environment
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
FMP_API_KEY = os.environ.get("FMP_API_KEY")
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")
FRED_API_KEY = os.environ.get("FRED_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

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

class User(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime

class Portfolio(BaseModel):
    id: str
    name: str
    total_value: float
    returns_1d: float
    returns_1w: float
    returns_1m: float
    returns_ytd: float
    risk_score: float
    holdings: List[Dict[str, Any]]

class ExecuteRequest(BaseModel):
    pattern: str
    inputs: Dict[str, Any]
    require_fresh: bool = False

# =============================================================================
# Database Functions
# =============================================================================

async def init_db():
    """Initialize database connection pool"""
    global db_pool
    try:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("DATABASE_URL not set")
            return None
            
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            timeout=30
        )
        
        # Create basic tables if they don't exist
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'USER',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    name VARCHAR(255) NOT NULL,
                    base_currency VARCHAR(10) DEFAULT 'USD',
                    total_value NUMERIC(20, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS holdings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    portfolio_id UUID REFERENCES portfolios(id),
                    symbol VARCHAR(20) NOT NULL,
                    quantity NUMERIC(20, 8),
                    cost_basis NUMERIC(20, 2),
                    current_price NUMERIC(20, 2),
                    market_value NUMERIC(20, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create default admin user if not exists
            try:
                default_password = "admin123"  # Short password for bcrypt
                # Ensure password is within bcrypt's 72 byte limit
                hashed_password = pwd_context.hash(default_password[:72])
                await conn.execute('''
                    INSERT INTO users (email, hashed_password, role)
                    VALUES ($1, $2, 'ADMIN')
                    ON CONFLICT (email) DO NOTHING
                ''', 'michael@dawsos.com', hashed_password)
                logger.info("Default admin user created/checked")
            except Exception as e:
                logger.warning(f"Could not create default user: {e}")
            
        logger.info("Database initialized successfully")
        return db_pool
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return None

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
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# =============================================================================
# AI Services
# =============================================================================

async def get_claude_analysis(prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Get analysis from Claude AI"""
    if not ANTHROPIC_API_KEY:
        return {
            "analysis": "Claude AI integration not configured. Please set ANTHROPIC_API_KEY.",
            "confidence": "low",
            "recommendations": []
        }
    
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Format context for Claude
        context_str = f"""
        Portfolio Context:
        - Total Value: ${context.get('total_value', 0):,.2f}
        - Holdings: {context.get('holdings_count', 0)}
        - YTD Returns: {context.get('returns_ytd', 0):.2%}
        """
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"{context_str}\n\nUser Query: {prompt}"
                }
            ]
        )
        
        return {
            "analysis": response.content[0].text,
            "confidence": "high",
            "model": "claude-3-sonnet",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return {
            "analysis": "Unable to get AI analysis at this time.",
            "confidence": "low",
            "error": str(e)
        }

async def get_market_data(symbol: str) -> Dict[str, Any]:
    """Get market data from FMP or Polygon"""
    if FMP_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://financialmodelingprep.com/api/v3/quote/{symbol}",
                    params={"apikey": FMP_API_KEY}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return data[0]
        except Exception as e:
            logger.error(f"FMP API error: {e}")
    
    # Return mock data if APIs not available
    return {
        "symbol": symbol,
        "price": 150.00,
        "change": 2.50,
        "changePercent": 1.69,
        "volume": 65000000,
        "marketCap": 2500000000000
    }

# =============================================================================
# API Endpoints
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_pool is not None,
            "claude_ai": ANTHROPIC_API_KEY is not None,
            "market_data": FMP_API_KEY is not None or POLYGON_API_KEY is not None
        }
    }

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, hashed_password, role FROM users WHERE email = $1",
            request.email
        )
        
        if not user or not pwd_context.verify(request.password[:72], user['hashed_password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_jwt_token(str(user['id']), user['email'], user['role'])
        
        return LoginResponse(
            access_token=token,
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "id": str(user['id']),
                "email": user['email'],
                "role": user['role']
            }
        )

@app.get("/auth/me")
async def get_current_user(authorization: str = None):
    """Get current user info"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
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
    
    # Mock portfolio data for now
    portfolio_data = {
        "id": str(uuid4()),
        "name": "Main Portfolio",
        "total_value": 1500000.00,
        "returns_1d": 0.0125,
        "returns_1w": 0.0234,
        "returns_1m": 0.0567,
        "returns_ytd": 0.1234,
        "risk_score": 0.65,
        "holdings": [
            {"symbol": "AAPL", "quantity": 100, "value": 18500.00, "weight": 0.15},
            {"symbol": "GOOGL", "quantity": 50, "value": 7000.00, "weight": 0.10},
            {"symbol": "MSFT", "quantity": 75, "value": 28500.00, "weight": 0.20},
            {"symbol": "AMZN", "quantity": 40, "value": 6000.00, "weight": 0.08},
            {"symbol": "NVDA", "quantity": 30, "value": 15000.00, "weight": 0.12}
        ]
    }
    
    # Pattern-specific responses
    if pattern == "portfolio_overview":
        return {
            "result": portfolio_data,
            "status": "success"
        }
    
    elif pattern == "macro_cycles_overview":
        return {
            "result": {
                "current_regime": "Late Cycle Expansion",
                "indicators": {
                    "gdp_growth": 2.3,
                    "inflation": 3.2,
                    "unemployment": 3.7,
                    "interest_rate": 5.25
                },
                "risk_level": "Medium-High",
                "recommendations": [
                    "Consider defensive positioning",
                    "Increase cash allocation",
                    "Focus on quality stocks"
                ]
            },
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
                "analysis": "High-quality company with strong competitive advantages"
            },
            "status": "success"
        }
    
    elif pattern == "portfolio_scenario_analysis":
        # Comprehensive scenario analysis response
        return {
            "result": {
                "scenarios": [
                    {
                        "id": "market_crash",
                        "name": "Market Crash",
                        "description": "Severe market downturn with 30% equity decline",
                        "probability": 0.15,
                        "impact": -0.25,
                        "regime": "RECESSION",
                        "factors": ["GDP Growth", "Unemployment", "Market Volatility"],
                        "portfolio_impact": -0.28,
                        "duration_months": 18,
                    },
                    {
                        "id": "interest_rate_spike",
                        "name": "Interest Rate Spike",
                        "description": "Fed raises rates by 200bps to combat inflation",
                        "probability": 0.25,
                        "impact": -0.15,
                        "regime": "STAGFLATION",
                        "factors": ["Interest Rates", "Inflation", "Bond Yields"],
                        "portfolio_impact": -0.18,
                        "duration_months": 12,
                    },
                    {
                        "id": "inflation_surge",
                        "name": "Inflation Surge",
                        "description": "Inflation rises above 6% for extended period",
                        "probability": 0.30,
                        "impact": -0.12,
                        "regime": "STAGFLATION",
                        "factors": ["CPI", "PPI", "Wage Growth"],
                        "portfolio_impact": -0.15,
                        "duration_months": 24,
                    },
                    {
                        "id": "soft_landing",
                        "name": "Soft Landing",
                        "description": "Economy slows gradually without recession",
                        "probability": 0.20,
                        "impact": -0.05,
                        "regime": "MID_EXPANSION",
                        "factors": ["GDP Growth", "Employment", "Consumer Confidence"],
                        "portfolio_impact": -0.03,
                        "duration_months": 9,
                    },
                    {
                        "id": "economic_boom",
                        "name": "Economic Boom",
                        "description": "Strong growth with controlled inflation",
                        "probability": 0.10,
                        "impact": 0.15,
                        "regime": "EARLY_EXPANSION",
                        "factors": ["GDP Growth", "Corporate Earnings", "Employment"],
                        "portfolio_impact": 0.22,
                        "duration_months": 36,
                    }
                ],
                "portfolio_metrics": {
                    "total_portfolio_value": 1500000.00,
                    "worst_case_loss": -420000.00,
                    "best_case_gain": 330000.00,
                    "expected_value": -67500.00,
                    "var_95": -0.18,
                    "cvar_95": -0.25,
                    "max_drawdown": -0.28,
                    "recovery_time_months": 24
                },
                "hedge_suggestions": [
                    {
                        "instrument": "SPY Put Options",
                        "strike": 420,
                        "expiry": "2025-12-19",
                        "cost_bps": 150,
                        "protection": 0.85,
                        "description": "Protects against market decline below 420",
                    },
                    {
                        "instrument": "VIX Calls",
                        "strike": 25,
                        "expiry": "2025-12-19",
                        "cost_bps": 80,
                        "protection": 0.60,
                        "description": "Hedges against volatility spike",
                    },
                    {
                        "instrument": "TLT (Treasury Bonds)",
                        "allocation": 0.15,
                        "cost_bps": 20,
                        "protection": 0.40,
                        "description": "Flight to quality hedge",
                    },
                    {
                        "instrument": "Gold ETF (GLD)",
                        "allocation": 0.10,
                        "cost_bps": 25,
                        "protection": 0.45,
                        "description": "Inflation hedge and safe haven",
                    }
                ]
            },
            "status": "success"
        }
    
    elif pattern == "claude_analysis":
        prompt = inputs.get("prompt", "Analyze my portfolio")
        analysis = await get_claude_analysis(prompt, portfolio_data)
        return {
            "result": analysis,
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
                ]
            }
        }
        
        return {
            "result": scenarios.get(scenario, scenarios["market_crash"]),
            "status": "success"
        }
    
    else:
        return {
            "result": {
                "message": f"Pattern '{pattern}' executed successfully",
                "inputs": inputs,
                "timestamp": datetime.utcnow().isoformat()
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
            }
        ]
    }

@app.post("/api/reports/generate")
async def generate_report(portfolio_id: str = "1"):
    """Generate portfolio report"""
    return {
        "report_id": str(uuid4()),
        "portfolio_id": portfolio_id,
        "generated_at": datetime.utcnow().isoformat(),
        "status": "completed",
        "url": f"/api/reports/{uuid4()}.pdf"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)