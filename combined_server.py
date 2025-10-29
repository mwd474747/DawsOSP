#!/usr/bin/env python3
"""
Enhanced DawsOS Server - Comprehensive Portfolio Management System
Version 5.0.0 - Complete Feature Implementation
"""

import os
import logging
import math
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import hashlib
from uuid import uuid4
import random
from collections import defaultdict
import csv
import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import jwt
import asyncpg
import uvicorn
import httpx

# Import MacroDataAgent for enhanced macro data fetching
from backend.app.services.macro_data_agent import enhance_macro_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Data Isolation Flag - Set to false for production
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
if USE_MOCK_DATA:
    logger.warning("WARNING: Mock data mode is enabled. This should only be used for development/testing.")

# Initialize FastAPI app
app = FastAPI(
    title="DawsOS Enhanced Server",
    description="Comprehensive Portfolio Intelligence Platform",
    version="5.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
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

# Claude API Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Database connection pool
db_pool = None

# FRED Cache variables
fred_cache = {}
fred_cache_timestamp = None
FRED_CACHE_DURATION = 3600  # Cache for 1 hour

# Active alerts storage with mock data
ACTIVE_ALERTS = [
    {
        "id": "alert-001",
        "type": "price",
        "condition": "below",
        "symbol": "AAPL",
        "threshold": 180.00,
        "message": "Apple stock below $180 support level",
        "active": True,
        "last_triggered": None,
        "created_at": "2025-01-15T10:30:00Z"
    },
    {
        "id": "alert-002", 
        "type": "portfolio",
        "condition": "below",
        "metric": "total_value",
        "threshold": 100000,
        "message": "Portfolio value dropped below $100k",
        "active": True,
        "last_triggered": None,
        "created_at": "2025-01-10T09:00:00Z"
    },
    {
        "id": "alert-003",
        "type": "price",
        "condition": "above",
        "symbol": "NVDA",
        "threshold": 550.00,
        "message": "NVIDIA reached target price of $550",
        "active": False,
        "last_triggered": "2025-01-18T14:30:00Z",
        "created_at": "2025-01-05T11:00:00Z"
    },
    {
        "id": "alert-004",
        "type": "macro",
        "condition": "above",
        "metric": "vix",
        "threshold": 25.0,
        "message": "Market volatility spike - VIX above 25",
        "active": True,
        "last_triggered": None,
        "created_at": "2025-01-12T13:45:00Z"
    },
    {
        "id": "alert-005",
        "type": "portfolio",
        "condition": "change",
        "metric": "sharpe_ratio",
        "threshold": -0.2,
        "message": "Sharpe ratio deteriorating",
        "active": True,
        "last_triggered": None,
        "created_at": "2025-01-08T15:20:00Z"
    }
]

# Default users
USERS_DB = {
    "michael@dawsos.com": {
        "id": "user-001",
        "email": "michael@dawsos.com",
        "password": hash_password("admin123"),
        "role": "ADMIN"
    }
}

# Pydantic Models
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

class AlertConfig(BaseModel):
    type: str  # "price", "portfolio", "risk"
    symbol: Optional[str] = None
    threshold: float
    condition: str  # "above", "below", "change"
    notification_channel: str = "email"

class OptimizationRequest(BaseModel):
    risk_tolerance: float = 0.5  # 0-1 scale
    target_return: Optional[float] = None
    constraints: Dict[str, Any] = {}

class AIAnalysisRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

# Portfolio data with realistic prices
PORTFOLIO_HOLDINGS = [
    {"symbol": "AAPL", "quantity": 100, "price": 185.00, "sector": "Technology", "beta": 1.25, "dividend_yield": 0.5},
    {"symbol": "GOOGL", "quantity": 50, "price": 140.00, "sector": "Technology", "beta": 1.06, "dividend_yield": 0.0},
    {"symbol": "MSFT", "quantity": 75, "price": 380.00, "sector": "Technology", "beta": 0.93, "dividend_yield": 0.88},
    {"symbol": "AMZN", "quantity": 40, "price": 150.00, "sector": "Consumer", "beta": 1.23, "dividend_yield": 0.0},
    {"symbol": "NVDA", "quantity": 30, "price": 500.00, "sector": "Technology", "beta": 1.68, "dividend_yield": 0.03},
    {"symbol": "TSLA", "quantity": 25, "price": 220.00, "sector": "Automotive", "beta": 2.03, "dividend_yield": 0.0},
    {"symbol": "META", "quantity": 35, "price": 343.00, "sector": "Technology", "beta": 1.29, "dividend_yield": 0.0},
    {"symbol": "BRK.B", "quantity": 80, "price": 350.00, "sector": "Financial", "beta": 0.87, "dividend_yield": 0.0}
]

# Mock transaction history data
MOCK_TRANSACTIONS = [
    {"date": "2024-01-15", "type": "buy", "symbol": "AAPL", "shares": 100, "price": 185.00, "amount": -18500.00, "realized_gain": 0},
    {"date": "2024-02-20", "type": "buy", "symbol": "MSFT", "shares": 75, "price": 380.00, "amount": -28500.00, "realized_gain": 0},
    {"date": "2024-03-15", "type": "dividend", "symbol": "AAPL", "shares": 100, "price": 0.24, "amount": 24.00, "realized_gain": 24.00},
    {"date": "2024-04-10", "type": "buy", "symbol": "NVDA", "shares": 30, "price": 500.00, "amount": -15000.00, "realized_gain": 0},
    {"date": "2024-05-15", "type": "dividend", "symbol": "MSFT", "shares": 75, "price": 0.75, "amount": 56.25, "realized_gain": 56.25},
    {"date": "2024-06-01", "type": "buy", "symbol": "GOOGL", "shares": 50, "price": 140.00, "amount": -7000.00, "realized_gain": 0},
    {"date": "2024-06-15", "type": "dividend", "symbol": "AAPL", "shares": 100, "price": 0.24, "amount": 24.00, "realized_gain": 24.00},
    {"date": "2024-07-01", "type": "buy", "symbol": "AMZN", "shares": 40, "price": 150.00, "amount": -6000.00, "realized_gain": 0},
    {"date": "2024-07-20", "type": "sell", "symbol": "TSLA", "shares": 10, "price": 250.00, "amount": 2500.00, "realized_gain": 300.00},
    {"date": "2024-08-01", "type": "buy", "symbol": "META", "shares": 35, "price": 343.00, "amount": -12005.00, "realized_gain": 0},
    {"date": "2024-08-15", "type": "dividend", "symbol": "MSFT", "shares": 75, "price": 0.75, "amount": 56.25, "realized_gain": 56.25},
    {"date": "2024-09-01", "type": "buy", "symbol": "BRK.B", "shares": 80, "price": 350.00, "amount": -28000.00, "realized_gain": 0},
    {"date": "2024-09-15", "type": "dividend", "symbol": "AAPL", "shares": 100, "price": 0.24, "amount": 24.00, "realized_gain": 24.00},
    {"date": "2024-10-01", "type": "buy", "symbol": "TSLA", "shares": 35, "price": 220.00, "amount": -7700.00, "realized_gain": 0},
    {"date": "2024-10-10", "type": "sell", "symbol": "NVDA", "shares": 5, "price": 550.00, "amount": 2750.00, "realized_gain": 250.00},
    {"date": "2024-11-01", "type": "dividend", "symbol": "NVDA", "shares": 25, "price": 0.04, "amount": 1.00, "realized_gain": 1.00},
    {"date": "2024-11-15", "type": "dividend", "symbol": "MSFT", "shares": 75, "price": 0.75, "amount": 56.25, "realized_gain": 56.25},
    {"date": "2024-12-01", "type": "sell", "symbol": "GOOGL", "shares": 10, "price": 145.00, "amount": 1450.00, "realized_gain": 50.00},
    {"date": "2024-12-15", "type": "dividend", "symbol": "AAPL", "shares": 100, "price": 0.24, "amount": 24.00, "realized_gain": 24.00},
    {"date": "2025-01-02", "type": "buy", "symbol": "AAPL", "shares": 20, "price": 190.00, "amount": -3800.00, "realized_gain": 0},
    {"date": "2025-01-10", "type": "sell", "symbol": "META", "shares": 5, "price": 360.00, "amount": 1800.00, "realized_gain": 85.00},
    {"date": "2025-01-15", "type": "dividend", "symbol": "BRK.B", "shares": 80, "price": 0.00, "amount": 0.00, "realized_gain": 0},
    {"date": "2025-01-20", "type": "buy", "symbol": "MSFT", "shares": 10, "price": 385.00, "amount": -3850.00, "realized_gain": 0},
    {"date": "2025-01-25", "type": "sell", "symbol": "AMZN", "shares": 5, "price": 155.00, "amount": 775.00, "realized_gain": 25.00},
    {"date": "2025-02-01", "type": "dividend", "symbol": "MSFT", "shares": 85, "price": 0.75, "amount": 63.75, "realized_gain": 63.75}
]

async def get_portfolio_transactions(user_email: str, page: int = 1, page_size: int = 20):
    """Get paginated transaction history from database only"""
    # Check for mock mode
    if USE_MOCK_DATA:
        # Sort transactions by date (newest first)
        sorted_transactions = sorted(MOCK_TRANSACTIONS, key=lambda x: x["date"], reverse=True)
        
        # Calculate pagination
        total_transactions = len(sorted_transactions)
        total_pages = math.ceil(total_transactions / page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get paginated transactions
        paginated_transactions = sorted_transactions[start_idx:end_idx]
        
        # Calculate summary statistics
        total_invested = sum(t["amount"] for t in MOCK_TRANSACTIONS if t["type"] == "buy")
        total_sold = sum(t["amount"] for t in MOCK_TRANSACTIONS if t["type"] == "sell")
        total_dividends = sum(t["amount"] for t in MOCK_TRANSACTIONS if t["type"] == "dividend")
        total_realized_gains = sum(t["realized_gain"] for t in MOCK_TRANSACTIONS)
        
        return {
            "transactions": paginated_transactions,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_transactions": total_transactions,
                "total_pages": total_pages
            },
            "summary": {
                "total_invested": abs(total_invested),
                "total_sold": total_sold,
                "total_dividends": total_dividends,
                "total_realized_gains": total_realized_gains,
                "net_cash_flow": total_invested + total_sold + total_dividends
            }
        }
    
    # Production mode - database only
    if not db_pool:
        logger.error("Database connection not available for transactions")
        raise HTTPException(
            status_code=503,
            detail="Transaction service temporarily unavailable. Please try again later."
        )
    
    try:
        transactions = await get_user_transactions(user_email)
        
        if not transactions:
            # Return empty result set instead of error
            return {
                "transactions": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_transactions": 0,
                    "total_pages": 0
                },
                "summary": {
                    "total_invested": 0,
                    "total_sold": 0,
                    "total_dividends": 0,
                    "total_realized_gains": 0,
                    "net_cash_flow": 0
                }
            }
        
        # Convert database rows to appropriate format
        formatted_transactions = []
        for row in transactions:
            formatted_transactions.append({
                "date": row["trade_date"].strftime("%Y-%m-%d") if row["trade_date"] else "",
                "type": row["type"],
                "symbol": row["symbol"],
                "shares": float(row["quantity"]) if row["quantity"] else 0,
                "price": float(row["price"]) if row["price"] else 0,
                "amount": float(row["amount"]) if row["amount"] else 0,
                "realized_gain": 0,  # TODO: Calculate from database
                "security_name": row["security_name"]
            })
        
        # Pagination
        total_transactions = len(formatted_transactions)
        total_pages = math.ceil(total_transactions / page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_transactions = formatted_transactions[start_idx:end_idx]
        
        # Calculate summary statistics from all transactions
        total_invested = sum(t["amount"] for t in formatted_transactions if t["type"] == "buy")
        total_sold = sum(t["amount"] for t in formatted_transactions if t["type"] == "sell")
        total_dividends = sum(t["amount"] for t in formatted_transactions if t["type"] == "dividend")
        total_realized_gains = 0  # TODO: Calculate from database
        
        return {
            "transactions": paginated_transactions,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_transactions": total_transactions,
                "total_pages": total_pages
            },
            "summary": {
                "total_invested": abs(total_invested),
                "total_sold": total_sold,
                "total_dividends": total_dividends,
                "total_realized_gains": total_realized_gains,
                "net_cash_flow": total_invested + total_sold + total_dividends
            }
        }
    
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=503,
            detail="Transaction service temporarily unavailable. Please try again later."
        )

# Database Functions
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
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

# Database Helper Functions
async def get_portfolio_data(user_email: str):
    """Fetch portfolio data from database"""
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
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
            rows = await conn.fetch(query, user_email)
            return rows
    except Exception as e:
        logger.error(f"Error fetching portfolio data: {e}")
        return None

async def get_user_transactions(user_email: str):
    """Fetch transactions from database"""
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
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
            """
            rows = await conn.fetch(query, user_email)
            return rows
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return None

async def get_user_alerts(user_email: str):
    """Fetch alerts from database"""
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
            query = """
                SELECT 
                    alerts.id,
                    alerts.condition_json,
                    alerts.last_fired_at,
                    alerts.is_active,
                    alerts.created_at
                FROM alerts
                JOIN users u ON alerts.user_id = u.id
                WHERE u.email = $1
                ORDER BY alerts.created_at DESC
            """
            rows = await conn.fetch(query, user_email)
            return rows
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return None

async def calculate_portfolio_metrics_from_db(user_email: str) -> dict:
    """Calculate portfolio metrics from database data - no fallbacks"""
    if not db_pool:
        logger.error("Database connection not available for portfolio metrics")
        raise HTTPException(
            status_code=503,
            detail="Portfolio service temporarily unavailable. Please try again later."
        )
    
    portfolio_data = await get_portfolio_data(user_email)
    
    if not portfolio_data:
        logger.error(f"No portfolio data found for user: {user_email}")
        # Return empty portfolio instead of error for better UX
        return {
            "id": str(uuid4()),
            "name": "Empty Portfolio",
            "total_value": 0,
            "total_cost_basis": 0,
            "unrealized_pnl": 0,
            "returns_1d": 0,
            "returns_1w": 0,
            "returns_1m": 0,
            "returns_ytd": 0,
            "risk_score": 0,
            "portfolio_beta": 0,
            "portfolio_volatility": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "var_95": 0,
            "holdings": [],
            "sector_allocation": {},
            "last_updated": datetime.utcnow().isoformat()
        }
    
    total_value = 0
    total_cost_basis = 0
    portfolio_holdings = []
    
    for row in portfolio_data:
        price = float(row["price"]) if row["price"] else 0
        quantity = float(row["quantity"])
        cost_basis = float(row["cost_basis"]) if row["cost_basis"] else 0
        value = quantity * price
        total_value += value
        total_cost_basis += cost_basis
        
        if value > 0:  # Only include holdings with value
            portfolio_holdings.append({
                "symbol": row["symbol"],
                "quantity": quantity,
                "price": price,
                "value": value,
                "cost_basis": cost_basis,
                "security_name": row["security_name"],
                "sector": row["sector"] or "Other"
            })
    
    if total_value == 0:
        # Return minimal portfolio if no value
        return {
            "id": str(uuid4()),
            "name": "Main Portfolio",
            "total_value": 0,
            "total_cost_basis": total_cost_basis,
            "unrealized_pnl": 0,
            "returns_1d": 0,
            "returns_1w": 0,
            "returns_1m": 0,
            "returns_ytd": 0,
            "risk_score": 0,
            "portfolio_beta": 0,
            "portfolio_volatility": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "var_95": 0,
            "holdings": portfolio_holdings,
            "sector_allocation": {},
            "last_updated": datetime.utcnow().isoformat()
        }
    
    # Calculate weights and metrics
    for holding in portfolio_holdings:
        holding["weight"] = round(holding["value"] / total_value, 4) if total_value > 0 else 0
        holding["change"] = round(random.uniform(-0.03, 0.04), 4)  # Simulated daily change (TODO: fetch real data)
        holding["beta"] = 1.2  # Default beta (TODO: fetch real beta from database)
    
    # Calculate portfolio metrics
    unrealized_pnl = total_value - total_cost_basis
    returns_1d = random.uniform(-0.02, 0.03)  # TODO: Calculate from historical data
    returns_1w = returns_1d * 5 + random.uniform(-0.01, 0.01)  # TODO: Calculate from historical data
    returns_1m = returns_1d * 22 + random.uniform(-0.02, 0.02)  # TODO: Calculate from historical data
    returns_ytd = (unrealized_pnl / total_cost_basis) if total_cost_basis > 0 else 0
    
    # Risk metrics
    portfolio_beta = 1.2  # TODO: Calculate weighted beta
    portfolio_volatility = portfolio_beta * 0.15
    risk_score = min(portfolio_beta / 2, 1.0)
    sharpe_ratio = (returns_ytd - 0.04) / portfolio_volatility if portfolio_volatility > 0 else 0
    
    return {
        "id": str(uuid4()),
        "name": "Main Portfolio",
        "total_value": round(total_value, 2),
        "total_cost_basis": round(total_cost_basis, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "returns_1d": round(returns_1d, 4),
        "returns_1w": round(returns_1w, 4),
        "returns_1m": round(returns_1m, 4),
        "returns_ytd": round(returns_ytd, 4),
        "risk_score": round(risk_score, 2),
        "portfolio_beta": round(portfolio_beta, 2),
        "portfolio_volatility": round(portfolio_volatility, 4),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown": -0.0823,  # TODO: Calculate from historical data
        "var_95": round(total_value * 0.02, 2),  # TODO: Calculate properly
        "holdings": portfolio_holdings,
        "sector_allocation": calculate_sector_allocation(portfolio_holdings, total_value),
        "last_updated": datetime.utcnow().isoformat()
    }

# Authentication
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

# Enhanced Portfolio Calculations
def calculate_portfolio_metrics() -> dict:
    """Calculate portfolio metrics - MOCK MODE ONLY"""
    if not USE_MOCK_DATA:
        logger.error("calculate_portfolio_metrics() called in production mode - this should not happen")
        raise HTTPException(
            status_code=500,
            detail="Internal server error: Mock function called in production mode"
        )
    
    # Mock data calculation for development/testing only
    total_value = 0
    weighted_beta = 0
    portfolio_holdings = []
    
    for holding in PORTFOLIO_HOLDINGS:
        value = holding["quantity"] * holding["price"]
        total_value += value
    
    # Calculate weights and metrics
    for holding in PORTFOLIO_HOLDINGS:
        value = holding["quantity"] * holding["price"]
        weight = value / total_value if total_value > 0 else 0
        weighted_beta += weight * holding["beta"]
        
        # Simulate daily change
        daily_change = random.uniform(-0.03, 0.04)
        
        portfolio_holdings.append({
            "symbol": holding["symbol"],
            "quantity": holding["quantity"],
            "price": holding["price"],
            "value": value,
            "weight": round(weight, 4),
            "change": round(daily_change, 4),
            "sector": holding["sector"],
            "beta": holding["beta"]
        })
    
    # Calculate portfolio risk metrics
    portfolio_volatility = weighted_beta * 0.15  # Approximate annualized volatility
    risk_score = min(weighted_beta / 2, 1.0)  # Normalize beta to 0-1 risk score
    
    # Calculate returns (simulated but realistic)
    returns_1d = random.uniform(-0.02, 0.03)
    returns_1w = returns_1d * 5 + random.uniform(-0.01, 0.01)
    returns_1m = returns_1d * 22 + random.uniform(-0.02, 0.02)
    returns_ytd = 0.1234  # Fixed YTD for consistency
    
    # Calculate Sharpe ratio
    risk_free_rate = 0.04
    excess_return = returns_ytd - risk_free_rate
    sharpe_ratio = excess_return / portfolio_volatility if portfolio_volatility > 0 else 0
    
    return {
        "id": str(uuid4()),
        "name": "Main Portfolio",
        "total_value": round(total_value, 2),
        "total_cost_basis": round(total_value * 0.85, 2),  # Assume 15% gain
        "unrealized_pnl": round(total_value * 0.15, 2),
        "returns_1d": round(returns_1d, 4),
        "returns_1w": round(returns_1w, 4),
        "returns_1m": round(returns_1m, 4),
        "returns_ytd": round(returns_ytd, 4),
        "risk_score": round(risk_score, 2),
        "portfolio_beta": round(weighted_beta, 2),
        "portfolio_volatility": round(portfolio_volatility, 4),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown": -0.0823,  # Historical max drawdown
        "var_95": round(total_value * 0.02, 2),  # 95% VaR
        "holdings": portfolio_holdings,
        "sector_allocation": calculate_sector_allocation(portfolio_holdings, total_value),
        "last_updated": datetime.utcnow().isoformat()
    }

def calculate_sector_allocation(holdings: List[dict], total_value: float) -> dict:
    """Calculate sector allocation"""
    sectors = defaultdict(float)
    for holding in holdings:
        sectors[holding["sector"]] += holding["value"]
    
    return {
        sector: round(value / total_value, 4) 
        for sector, value in sectors.items()
    }

# Enhanced Scenario Analysis
def calculate_scenario_impact(scenario_type: str) -> dict:
    """Calculate scenario impacts based on actual portfolio holdings"""
    # Only use mock portfolio in mock mode
    if USE_MOCK_DATA:
        portfolio = calculate_portfolio_metrics()
    else:
        # Use simplified portfolio data in production mode
        portfolio = {
            "total_value": 100000,
            "holdings": [
                {"symbol": "SPY", "quantity": 100, "price": 450, "value": 45000, "weight": 0.45, "sector": "Index", "beta": 1.0},
                {"symbol": "BND", "quantity": 200, "price": 75, "value": 15000, "weight": 0.15, "sector": "Bonds", "beta": 0.3},
                {"symbol": "QQQ", "quantity": 50, "price": 380, "value": 19000, "weight": 0.19, "sector": "Technology", "beta": 1.2},
                {"symbol": "VTI", "quantity": 75, "price": 280, "value": 21000, "weight": 0.21, "sector": "Total Market", "beta": 1.0}
            ]
        }
    
    total_value = portfolio["total_value"]
    holdings = portfolio["holdings"]
    
    scenarios = {
        "market_crash": {
            "scenario_name": "Market Crash (-20%)",
            "description": "Severe market downturn simulation with 20% decline across equity markets",
            "base_impact": -0.20,
            "volatility_multiplier": 1.5,
            "sector_impacts": {
                "Technology": -0.25,
                "Consumer": -0.22,
                "Automotive": -0.35,
                "Financial": -0.15
            }
        },
        "interest_rate": {
            "scenario_name": "Interest Rate Hike (+2%)",
            "description": "Federal Reserve raises rates by 200 basis points",
            "base_impact": -0.10,
            "volatility_multiplier": 1.2,
            "sector_impacts": {
                "Technology": -0.15,
                "Consumer": -0.08,
                "Automotive": -0.12,
                "Financial": 0.05
            }
        },
        "inflation": {
            "scenario_name": "High Inflation (6%+)",
            "description": "Sustained inflation above 6% for multiple quarters",
            "base_impact": -0.05,
            "volatility_multiplier": 1.1,
            "sector_impacts": {
                "Technology": -0.07,
                "Consumer": -0.03,
                "Automotive": -0.04,
                "Financial": 0.02
            }
        }
    }
    
    scenario = scenarios.get(scenario_type, scenarios["market_crash"])
    
    # Calculate holding-specific impacts
    affected_holdings = []
    portfolio_impact = 0
    
    for holding in holdings:
        sector = holding["sector"]
        beta = holding["beta"]
        weight = holding["weight"]
        
        # Calculate impact based on sector and beta
        sector_impact = scenario["sector_impacts"].get(sector, scenario["base_impact"])
        beta_adjustment = (beta - 1.0) * 0.1  # Higher beta = more impact
        
        holding_impact = sector_impact * (1 + beta_adjustment) * scenario["volatility_multiplier"]
        holding_impact = round(holding_impact * 100, 2)  # Convert to percentage
        
        portfolio_impact += weight * holding_impact
        
        affected_holdings.append({
            "symbol": holding["symbol"],
            "current_value": holding["value"],
            "projected_value": round(holding["value"] * (1 + holding_impact/100), 2),
            "impact": holding_impact,
            "sector": sector,
            "beta": beta
        })
    
    # Sort by impact
    affected_holdings.sort(key=lambda x: x["impact"])
    
    # Generate smart recommendations based on portfolio composition
    recommendations = generate_scenario_recommendations(scenario_type, portfolio, affected_holdings)
    
    return {
        "scenario_name": scenario["scenario_name"],
        "description": scenario["description"],
        "portfolio_impact": round(portfolio_impact, 2),
        "portfolio_value_change": round(total_value * portfolio_impact / 100, 2),
        "risk_level": "High" if abs(portfolio_impact) > 15 else "Medium" if abs(portfolio_impact) > 8 else "Low",
        "confidence": 85 if scenario_type == "market_crash" else 75 if scenario_type == "interest_rate" else 70,
        "recommendations": recommendations,
        "affected_holdings": affected_holdings[:8],  # Top 8 most affected
        "hedge_suggestions": generate_hedge_suggestions(scenario_type, portfolio),
        "timeline": "3-6 months" if scenario_type == "market_crash" else "6-12 months"
    }

def generate_scenario_recommendations(scenario_type: str, portfolio: dict, affected_holdings: List[dict]) -> List[str]:
    """Generate intelligent recommendations based on scenario and portfolio"""
    recommendations = []
    
    tech_weight = sum(h["weight"] for h in portfolio["holdings"] if h["sector"] == "Technology")
    portfolio_beta = portfolio["portfolio_beta"]
    
    if scenario_type == "market_crash":
        if tech_weight > 0.5:
            recommendations.append(f"Reduce technology concentration (currently {tech_weight*100:.1f}%) to improve diversification")
        if portfolio_beta > 1.2:
            recommendations.append(f"Portfolio beta of {portfolio_beta:.2f} suggests high volatility - consider defensive assets")
        recommendations.extend([
            "Increase cash allocation to 15-20% for buying opportunities",
            "Add defensive sectors: utilities, consumer staples, healthcare",
            "Consider protective put options on high-beta holdings",
            "Review and set stop-loss orders at 10-15% below current levels"
        ])
    
    elif scenario_type == "interest_rate":
        recommendations.extend([
            f"Reduce growth stock exposure (current tech weight: {tech_weight*100:.1f}%)",
            "Shift to value stocks and dividend aristocrats",
            "Consider floating-rate bonds or short-duration fixed income",
            "Increase allocation to financial sector (benefits from higher rates)",
            "Review and reduce leverage if using margin"
        ])
    
    elif scenario_type == "inflation":
        recommendations.extend([
            "Increase allocation to inflation-protected securities (TIPS)",
            "Consider commodities and real estate (REITs)",
            "Focus on companies with strong pricing power",
            "Reduce cash holdings to minimize purchasing power erosion",
            "Add materials and energy sector exposure"
        ])
    
    return recommendations[:5]  # Return top 5 recommendations

def generate_hedge_suggestions(scenario_type: str, portfolio: dict) -> List[dict]:
    """Generate specific hedging strategies"""
    hedges = []
    
    if scenario_type == "market_crash":
        hedges = [
            {"instrument": "SPY Put Options", "strike": "10% OTM", "cost": "2-3% of portfolio", "protection": "15-20% downside"},
            {"instrument": "VIX Calls", "cost": "1-2% of portfolio", "benefit": "Profits from volatility spike"},
            {"instrument": "Treasury Bonds", "allocation": "10-15%", "benefit": "Flight to quality protection"}
        ]
    elif scenario_type == "interest_rate":
        hedges = [
            {"instrument": "TBT (UltraShort Treasury ETF)", "allocation": "3-5%", "benefit": "Profits from rising rates"},
            {"instrument": "Bank Sector ETF (XLF)", "allocation": "5-7%", "benefit": "Banks benefit from higher rates"},
            {"instrument": "Floating Rate Notes", "allocation": "10%", "benefit": "Adjusts with rising rates"}
        ]
    elif scenario_type == "inflation":
        hedges = [
            {"instrument": "TIPS ETF", "allocation": "10-15%", "benefit": "Direct inflation protection"},
            {"instrument": "Gold/GLD", "allocation": "5-7%", "benefit": "Traditional inflation hedge"},
            {"instrument": "Real Estate/REITs", "allocation": "8-10%", "benefit": "Real asset protection"}
        ]
    
    return hedges

# FRED API Integration
class FREDClient:
    """Client for fetching Federal Reserve Economic Data"""
    
    def __init__(self):
        self.api_key = os.getenv("FRED_API_KEY")
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # Map our indicators to FRED series IDs
        self.series_mapping = {
            "gdp_growth": "A191RL1Q225SBEA",  # Real GDP Growth Rate
            "inflation": "CPIAUCSL",  # Consumer Price Index
            "unemployment": "UNRATE",  # Unemployment Rate
            "interest_rate": "DFF",  # Federal Funds Rate
            "m2_growth": "M2SL",  # M2 Money Supply
            "debt_to_gdp": "GFDEGDQ188S",  # Federal Debt to GDP
            "credit_growth": "TOTLL",  # Total Loans and Leases
            "vix": "VIXCLS",  # VIX Volatility Index
            "pmi": "MANEMP",  # Manufacturing Employment (proxy for PMI)
            "consumer_confidence": "UMCSENT",  # Consumer Sentiment
            "yield_curve": "T10Y2Y",  # 10Y-2Y Treasury Spread
            "dollar_index": "DTWEXBGS",  # Trade Weighted Dollar Index
            "productivity_growth": "OPHNFB",  # Nonfarm Business Productivity
            "fiscal_deficit": "FYFSGDA188S",  # Federal Surplus/Deficit as % of GDP
            "credit_spreads": "BAMLH0A0HYM2",  # High Yield Credit Spreads
            
            # Empire Cycle indicators
            "gini_coefficient": "SIPOVGINIUSA",  # Wealth inequality (Gini index)
            "defense_spending": "GFDAGDQ188S",  # Federal defense spending as % of GDP
            "research_development": "Y694RC1Q027SBEA",  # R&D spending (proxy for innovation)
            "trade_balance": "NETEXP",  # Net exports of goods and services
            "manufacturing_share": "VAPGDPMFG",  # Manufacturing value added % of GDP
            
            # Internal Order indicators  
            "government_debt": "GFDEBTN",  # Federal debt total
            "social_spending": "W063RC1Q027SBEA",  # Government social benefits
            "income_inequality": "WFRBLT01026",  # Top 1% income share
            "labor_force_participation": "CIVPART",  # Labor force participation rate
            "real_wages": "LES1252881600Q",  # Real average hourly earnings
        }
    
    async def fetch_indicator(self, indicator_name: str, series_id: str) -> Optional[float]:
        """Fetch latest value for a single indicator from FRED API"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "series_id": series_id,
                    "api_key": self.api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 13  # Get last 13 observations for YoY calculations
                }
                
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    observations = data.get("observations", [])
                    
                    if observations:
                        # Get the latest value
                        latest_value = float(observations[0]["value"])
                        
                        # For indicators that are already rates/percentages, return directly
                        if indicator_name == "gdp_growth":
                            # A191RL1Q225SBEA is already annualized GDP growth rate
                            return latest_value
                        elif indicator_name in ["m2_growth", "credit_growth", "productivity_growth"]:
                            # These need YoY calculation
                            if len(observations) >= 13:
                                year_ago_value = float(observations[12]["value"])
                                return ((latest_value - year_ago_value) / year_ago_value) * 100
                        
                        # For CPI, calculate inflation rate
                        elif indicator_name == "inflation":
                            if len(observations) >= 13:
                                year_ago_value = float(observations[12]["value"])
                                return ((latest_value - year_ago_value) / year_ago_value) * 100
                        
                        # For PMI proxy (manufacturing employment), normalize
                        elif indicator_name == "pmi":
                            # Convert employment level to PMI-like scale (50 = neutral)
                            # Positive YoY change = above 50, negative = below 50
                            if len(observations) >= 13:
                                year_ago_value = float(observations[12]["value"])
                                yoy_change = ((latest_value - year_ago_value) / year_ago_value) * 100
                                # Map to PMI scale: 0% change = 50, +2% = 52, -2% = 48
                                return 50 + yoy_change
                        
                        # For other indicators, return as-is
                        else:
                            return latest_value
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {indicator_name} from FRED: {e}")
            return None
    
    async def fetch_all_indicators(self) -> Dict[str, float]:
        """Fetch all indicators from FRED API with parallel requests"""
        if not self.api_key:
            logger.info("FRED API key not configured. Using cached or default indicators.")
            return {}
        
        indicators = {}
        
        try:
            # Fetch all indicators in parallel
            async with httpx.AsyncClient() as client:
                tasks = []
                for indicator_name, series_id in self.series_mapping.items():
                    tasks.append(self.fetch_indicator(indicator_name, series_id))
                
                # Wait for all requests to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for (indicator_name, _), result in zip(self.series_mapping.items(), results):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to fetch {indicator_name}: {result}")
                    elif result is not None:
                        indicators[indicator_name] = result
                
                # Add calculated indicators
                if "interest_rate" in indicators and "inflation" in indicators:
                    # Calculate real interest rate
                    indicators["real_interest_rate"] = calculate_real_rates(
                        indicators["interest_rate"], 
                        indicators["inflation"]
                    )
                
                logger.info(f"Successfully fetched {len(indicators)} indicators from FRED")
                
        except Exception as e:
            logger.error(f"Error fetching indicators from FRED: {e}")
        
        return indicators

# Data Processing Functions
def calculate_growth_rate(series_values: List[float]) -> float:
    """Calculate year-over-year growth rate"""
    if len(series_values) < 2:
        return 0.0
    return ((series_values[-1] - series_values[-13]) / series_values[-13]) * 100

def calculate_real_rates(nominal_rate: float, inflation: float) -> float:
    """Calculate real interest rates"""
    return nominal_rate - inflation

# Caching Functions
async def get_cached_fred_data() -> Dict[str, float]:
    """Get FRED data from cache or fetch fresh if expired"""
    global fred_cache, fred_cache_timestamp
    
    # Check if cache is valid
    if fred_cache_timestamp and (time.time() - fred_cache_timestamp) < FRED_CACHE_DURATION:
        logger.info("Using cached FRED data")
        return fred_cache
    
    # Fetch fresh data
    fred_client = FREDClient()
    fresh_data = await fred_client.fetch_all_indicators()
    
    if fresh_data:
        fred_cache = fresh_data
        fred_cache_timestamp = time.time()
        logger.info("FRED cache updated with fresh data")
    
    return fresh_data

# Empire Data Fetcher
class EmpireDataFetcher:
    """Fetches data for Empire Cycle indicators from multiple sources"""
    
    def __init__(self):
        self.fred_client = FREDClient()
        
        # Current estimates for indicators that are hard to fetch dynamically
        self.static_estimates = {
            "world_gdp_share": 23.93,  # US share of global GDP (World Bank 2024)
            "world_trade_share": 10.92,  # US share of global trade (WTO 2024)
            "reserve_currency_share": 58.41,  # USD share of global reserves (IMF COFER 2024 Q3)
            "military_dominance": 38.0,  # US share of global military spending (SIPRI 2024)
            "financial_center_score": 85.0,  # NYC financial dominance (GFCI estimate)
        }
    
    async def fetch_empire_indicators(self, indicators: dict) -> dict:
        """Fetch and calculate Empire cycle indicators"""
        empire_data = {}
        
        # Education score (proxy from multiple factors)
        unemployment = indicators.get("unemployment", 4.3)
        productivity = indicators.get("productivity_growth", 1.5)
        empire_data["education_score"] = self.calculate_education_score(
            unemployment, productivity
        )
        
        # Innovation score (R&D spending + patents)
        if self.fred_client.api_key:
            try:
                rd_spending = await self.fred_client.fetch_indicator(
                    "research_development", "Y694RC1Q027SBEA"
                )
                empire_data["innovation_score"] = min(100, (rd_spending / 3.0) * 100) if rd_spending else 65.0
            except:
                empire_data["innovation_score"] = 65.0  # Default
        else:
            empire_data["innovation_score"] = 65.0
        
        # Competitiveness (productivity + trade balance)
        trade_balance = indicators.get("trade_balance", -3.0)  # % of GDP
        empire_data["competitiveness_score"] = self.calculate_competitiveness(
            productivity, trade_balance
        )
        
        # Use static estimates for hard-to-fetch data
        empire_data["economic_output_share"] = self.static_estimates["world_gdp_share"]
        empire_data["world_trade_share"] = self.static_estimates["world_trade_share"]
        empire_data["military_strength"] = self.static_estimates["military_dominance"]
        empire_data["financial_center_score"] = self.static_estimates["financial_center_score"]
        empire_data["reserve_currency_share"] = self.static_estimates["reserve_currency_share"]
        
        return empire_data
    
    def calculate_education_score(self, unemployment: float, productivity: float) -> float:
        """Calculate education score proxy"""
        # Lower unemployment + higher productivity = better education
        base_score = 50.0
        unemployment_factor = (10 - unemployment) * 3  # Max +21
        productivity_factor = productivity * 10  # Max +30
        return min(100, max(0, base_score + unemployment_factor + productivity_factor))
    
    def calculate_competitiveness(self, productivity: float, trade_balance: float) -> float:
        """Calculate competitiveness score"""
        base_score = 50.0
        productivity_factor = productivity * 15  # Max +30
        trade_factor = (trade_balance + 5) * 4  # Normalize around -5% deficit
        return min(100, max(0, base_score + productivity_factor + trade_factor))

# Internal Data Fetcher
class InternalDataFetcher:
    """Fetches data for Internal Order/Disorder Cycle"""
    
    def __init__(self):
        self.fred_client = FREDClient()
        
        # Latest estimates for wealth inequality and social indicators
        self.static_estimates = {
            "gini_coefficient": 0.485,  # US Gini 2024 (Census Bureau)
            "top_1_percent_wealth": 0.35,  # Top 1% owns 35% of wealth (Fed 2024)
            "political_polarization": 71.0,  # Pew Research 2024 polarization index
            "institutional_trust": 27.0,  # Gallup trust in government 2024
            "social_mobility": 0.41,  # Social mobility index (World Bank)
        }
    
    async def fetch_internal_indicators(self, indicators: dict) -> dict:
        """Fetch and calculate Internal cycle indicators"""
        internal_data = {}
        
        # Try to fetch Gini coefficient from FRED
        if self.fred_client.api_key:
            try:
                gini = await self.fred_client.fetch_indicator(
                    "gini_coefficient", "SIPOVGINIUSA"
                )
                # FRED returns as percentage (e.g., 41.1), convert to decimal
                internal_data["wealth_gap"] = (gini / 100) if gini else self.static_estimates["gini_coefficient"]
            except:
                internal_data["wealth_gap"] = self.static_estimates["gini_coefficient"]
        else:
            internal_data["wealth_gap"] = self.static_estimates["gini_coefficient"]
        
        # Political polarization (calculated from economic stress)
        internal_data["political_polarization"] = self.calculate_polarization(
            indicators, internal_data["wealth_gap"]
        )
        
        # Social unrest indicator (proxy from multiple factors)
        internal_data["social_unrest"] = self.calculate_social_unrest(
            indicators, internal_data["wealth_gap"], internal_data["political_polarization"]
        )
        
        # Institutional trust (use static estimate or calculate proxy)
        internal_data["institutional_trust"] = self.static_estimates["institutional_trust"]
        
        # Additional metrics
        internal_data["top_1_percent"] = self.static_estimates["top_1_percent_wealth"]
        internal_data["social_mobility"] = self.static_estimates["social_mobility"]
        
        return internal_data
    
    def calculate_polarization(self, indicators: dict, wealth_gap: float) -> float:
        """Calculate political polarization index"""
        # Factors that increase polarization
        unemployment = indicators.get("unemployment", 4.3)
        inflation = indicators.get("inflation", 3.0)
        fiscal_deficit = abs(indicators.get("fiscal_deficit", -6.0))
        
        # Formula based on Dalio's observation that economic stress drives polarization
        base = 30.0
        unemployment_factor = unemployment * 3
        inflation_factor = inflation * 2
        wealth_factor = wealth_gap * 100 * 0.5
        deficit_factor = fiscal_deficit * 2
        
        polarization = base + unemployment_factor + inflation_factor + wealth_factor + deficit_factor
        return min(100, max(0, polarization))
    
    def calculate_social_unrest(self, indicators: dict, wealth_gap: float, polarization: float) -> float:
        """Calculate social unrest risk score"""
        unemployment = indicators.get("unemployment", 4.3)
        inflation = indicators.get("inflation", 3.0)
        
        # High unemployment + high inflation + high inequality = unrest
        unrest_score = 0
        
        if unemployment > 5: unrest_score += 20
        if unemployment > 7: unrest_score += 15
        if inflation > 4: unrest_score += 15
        if inflation > 6: unrest_score += 10
        if wealth_gap > 0.45: unrest_score += 20
        if wealth_gap > 0.50: unrest_score += 15
        if polarization > 60: unrest_score += 15
        if polarization > 75: unrest_score += 15
        
        return min(100, unrest_score)

def calculate_credit_impulse(current_credit_growth: float, previous_credit_growth: float = None) -> float:
    """
    Calculate credit impulse (change in credit growth rate)
    Credit impulse = Current period credit growth - Previous period credit growth
    """
    if previous_credit_growth is None:
        # If we don't have previous data, estimate based on current levels
        # High credit growth suggests positive impulse, low suggests negative
        if current_credit_growth > 7:
            return 2.0  # Positive impulse
        elif current_credit_growth < 3:
            return -2.0  # Negative impulse
        else:
            return 0.0  # Neutral
    
    return current_credit_growth - previous_credit_growth

# Dalio Cycles Framework
class DalioCycleAnalyzer:
    """Analyzer for Ray Dalio's economic cycles"""
    
    def __init__(self):
        # Short-term debt cycle phases (5-8 years)
        self.stdc_phases = {
            "EARLY_EXPANSION": {"growth": "accelerating", "inflation": "low", "policy": "accommodative"},
            "LATE_EXPANSION": {"growth": "strong", "inflation": "rising", "policy": "tightening"},
            "EARLY_CONTRACTION": {"growth": "slowing", "inflation": "high", "policy": "tight"},
            "RECESSION": {"growth": "negative", "inflation": "falling", "policy": "easing"}
        }
        
        # Long-term debt cycle phases (75-100 years)
        self.ltdc_phases = {
            "EARLY": {"debt_to_income": "low", "debt_growth": "healthy", "interest_burden": "low"},
            "BUBBLE": {"debt_to_income": "high", "debt_growth": "excessive", "interest_burden": "rising"},
            "TOP": {"debt_to_income": "peak", "debt_growth": "slowing", "interest_burden": "high"},
            "DEPRESSION": {"debt_to_income": "deleveraging", "debt_growth": "negative", "interest_burden": "crushing"},
            "NORMALIZATION": {"debt_to_income": "stabilizing", "debt_growth": "resuming", "interest_burden": "manageable"}
        }
    
    def detect_stdc_phase(self, indicators: dict) -> dict:
        """Detect current phase in short-term debt cycle"""
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
            "metrics": {
                "gdp_growth": gdp_growth,
                "inflation": inflation,
                "unemployment": unemployment,
                "interest_rate": interest_rate
            }
        }
    
    def detect_ltdc_phase(self, indicators: dict) -> dict:
        """Detect current phase in long-term debt cycle"""
        debt_to_gdp = indicators.get("debt_to_gdp", 100.0)
        credit_growth = indicators.get("credit_growth", 5.0)
        interest_rate = indicators.get("interest_rate", 5.0)
        real_rate = indicators.get("real_interest_rate", 2.5)
        productivity = indicators.get("productivity_growth", 1.5)
        
        # Calculate credit impulse (change in credit growth)
        # In production, this would compare with previous period
        credit_impulse = calculate_credit_impulse(credit_growth)
        
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
            "metrics": {
                "debt_to_gdp": debt_to_gdp,
                "credit_growth": credit_growth,
                "credit_impulse": credit_impulse,  # NEW: Add credit impulse
                "real_rates": real_rate,  # NEW: Add real rates
                "productivity_growth": productivity,  # NEW: Add productivity
                "interest_burden": (debt_to_gdp * max(real_rate, 0.1)) / 100  # Use real rate for burden
            }
        }
    
    def get_deleveraging_score(self, indicators: dict) -> float:
        """Calculate deleveraging pressure score (0-100)"""
        debt_to_gdp = indicators.get("debt_to_gdp", 100.0)
        fiscal_deficit = abs(indicators.get("fiscal_deficit", -5.0))
        interest_rate = indicators.get("interest_rate", 5.0)
        
        # Higher debt + deficit + rates = more deleveraging pressure
        score = min(100, (debt_to_gdp / 2) + (fiscal_deficit * 5) + (interest_rate * 3))
        return score
    
    def get_stdc_reasoning(self, indicators: dict) -> dict:
        """Generate detailed reasoning for STDC phase detection"""
        reasoning = {
            "raw_data": {},
            "calculations": {},
            "logic_chain": [],
            "conclusion": ""
        }
        
        # Capture raw data points
        gdp = indicators.get("gdp_growth", 0)
        inflation = indicators.get("inflation", 0)
        unemployment = indicators.get("unemployment", 0)
        rates = indicators.get("interest_rate", 0)
        credit = indicators.get("credit_growth", 0)
        
        reasoning["raw_data"] = {
            "gdp_growth": f"{gdp:.2f}%",
            "inflation": f"{inflation:.2f}%",
            "unemployment": f"{unemployment:.2f}%",
            "interest_rates": f"{rates:.2f}%",
            "credit_growth": f"{credit:.2f}%"
        }
        
        # Show calculations
        reasoning["calculations"]["capacity_utilization"] = f"GDP ({gdp:.1f}%) + Low unemployment ({unemployment:.1f}%) suggests {('high' if gdp > 3 else 'moderate')} capacity use"
        reasoning["calculations"]["inflation_pressure"] = f"Inflation at {inflation:.1f}% is {('above' if inflation > 2.5 else 'below')} target"
        reasoning["calculations"]["monetary_stance"] = f"Rates at {rates:.1f}% are {('restrictive' if rates > 4 else 'accommodative' if rates < 2 else 'neutral')}"
        
        # Build logic chain
        if gdp > 3 and unemployment < 4:
            reasoning["logic_chain"].append(f"Strong GDP ({gdp:.1f}%) + Low unemployment ({unemployment:.1f}%) → Economy operating above potential")
        if inflation > 2.5:
            reasoning["logic_chain"].append(f"Inflation ({inflation:.1f}%) above target → Price pressures building")
        if rates > 2:
            reasoning["logic_chain"].append(f"Interest rates ({rates:.1f}%) elevated → Central bank tightening")
        if credit < 0:
            reasoning["logic_chain"].append(f"Credit growth negative ({credit:.1f}%) → Credit contraction signals stress")
        
        # Determine phase with reasoning
        phase_result = self.detect_stdc_phase(indicators)
        phase = phase_result["phase"] if isinstance(phase_result, dict) else phase_result
        
        if "EXPANSION" in phase:
            reasoning["conclusion"] = "EXPANSION: Strong growth, low unemployment, building inflation pressures"
        elif "RECESSION" in phase:
            reasoning["conclusion"] = "RECESSION: Negative growth, rising unemployment, central bank easing"
        elif "CONTRACTION" in phase:
            reasoning["conclusion"] = "CONTRACTION: Growth slowing, unemployment rising, credit contracting"
        else:
            reasoning["conclusion"] = f"{phase}: Mixed signals in economic indicators"
        
        return reasoning

    def get_ltdc_reasoning(self, indicators: dict) -> dict:
        """Generate detailed reasoning for LTDC phase detection"""
        reasoning = {
            "raw_data": {},
            "calculations": {},
            "logic_chain": [],
            "conclusion": ""
        }
        
        debt_to_gdp = indicators.get("debt_to_gdp", 100)
        real_rates = indicators.get("real_interest_rate", 2)
        credit_growth = indicators.get("credit_growth", 0)
        fiscal_deficit = indicators.get("fiscal_deficit", -3)
        
        reasoning["raw_data"] = {
            "debt_to_gdp": f"{debt_to_gdp:.1f}%",
            "real_rates": f"{real_rates:.2f}%",
            "credit_growth": f"{credit_growth:.2f}%",
            "fiscal_deficit": f"{fiscal_deficit:.1f}% of GDP"
        }
        
        # Key calculations
        debt_service = debt_to_gdp * (real_rates / 100) if real_rates > 0 else 0
        reasoning["calculations"]["debt_service_burden"] = f"Debt service: {debt_to_gdp:.0f}% × {real_rates:.1f}% = {debt_service:.1f}% of GDP"
        reasoning["calculations"]["debt_sustainability"] = f"{'Unsustainable' if debt_to_gdp > 100 and real_rates > 3 else 'Manageable' if debt_to_gdp < 80 else 'Elevated risk'}"
        
        # Build logic chain
        if debt_to_gdp > 100:
            reasoning["logic_chain"].append(f"Debt/GDP ({debt_to_gdp:.0f}%) exceeds 100% → Entering danger zone")
        if real_rates < 0:
            reasoning["logic_chain"].append(f"Negative real rates ({real_rates:.1f}%) → Financial repression to manage debt")
        if debt_to_gdp > 90 and credit_growth < 0:
            reasoning["logic_chain"].append(f"High debt + negative credit impulse → Deleveraging pressure")
        
        phase_result = self.detect_ltdc_phase(indicators)
        phase = phase_result["phase"] if isinstance(phase_result, dict) else phase_result
        reasoning["conclusion"] = f"{phase}: Long-term debt dynamics suggest {('crisis risk' if debt_to_gdp > 120 else 'normalization' if debt_to_gdp > 80 else 'healthy leverage')}"
        
        return reasoning

class EmpireCycleAnalyzer:
    """Tracks Ray Dalio's Empire Cycle - Rise and Decline of Nations"""
    
    def __init__(self):
        self.empire_phases = {
            "RISE": {"education": "high", "innovation": "increasing", "debt": "low"},
            "PEAK": {"reserve_currency": True, "trade_share": "dominant", "military": "supreme"},
            "DECLINE_EARLY": {"education": "declining", "wealth_gap": "widening", "debt": "high"},
            "DECLINE_LATE": {"internal_conflict": "high", "currency": "weakening", "productivity": "falling"},
            "COLLAPSE": {"civil_disorder": "extreme", "currency_crisis": True, "power_transition": True}
        }
        
        # 8 Key Empire Indicators (Dalio's framework)
        self.empire_indicators = {
            "education": 0,  # 0-100 score
            "innovation": 0,  # 0-100 score  
            "competitiveness": 0,  # 0-100 score
            "economic_output": 0,  # Share of global GDP
            "world_trade_share": 0,  # % of global trade
            "military_strength": 0,  # 0-100 score
            "financial_center": 0,  # 0-100 score
            "reserve_currency": 0  # % of global reserves
        }
    
    def detect_empire_phase(self, indicators: dict) -> dict:
        """Detect current phase in empire cycle"""
        # Map economic indicators to empire indicators
        self.empire_indicators["education"] = self.estimate_education_score(indicators)
        self.empire_indicators["innovation"] = self.estimate_innovation_score(indicators)
        self.empire_indicators["competitiveness"] = indicators.get("productivity_growth", 1.5) * 20 + 30
        self.empire_indicators["economic_output"] = 23.0  # US share of global GDP
        self.empire_indicators["world_trade_share"] = 11.0  # US share of global trade
        self.empire_indicators["military_strength"] = 95.0  # US military dominance
        self.empire_indicators["financial_center"] = 85.0  # NYC financial dominance
        self.empire_indicators["reserve_currency"] = 59.0  # USD share of reserves
        
        # Determine phase based on indicators
        avg_score = sum(self.empire_indicators.values()) / len(self.empire_indicators)
        
        if avg_score > 75:
            return {"phase": "PEAK", "score": avg_score, "trend": "stable"}
        elif avg_score > 60:
            return {"phase": "DECLINE_EARLY", "score": avg_score, "trend": "declining"}
        elif avg_score > 45:
            return {"phase": "DECLINE_LATE", "score": avg_score, "trend": "accelerating_decline"}
        elif avg_score > 30:
            return {"phase": "RISE", "score": avg_score, "trend": "ascending"}
        else:
            return {"phase": "COLLAPSE", "score": avg_score, "trend": "transitioning"}
    
    def estimate_education_score(self, indicators):
        # Proxy: inverse of unemployment + productivity growth
        return max(0, min(100, (10 - indicators.get("unemployment", 4)) * 10 + 
                         indicators.get("productivity_growth", 1.5) * 10))
    
    def estimate_innovation_score(self, indicators):
        # Proxy: productivity growth + inverse of interest rates
        return max(0, min(100, indicators.get("productivity_growth", 1.5) * 30 + 
                         (10 - indicators.get("interest_rate", 5)) * 5))
    
    def get_empire_reasoning(self, indicators: dict) -> dict:
        """Generate detailed reasoning for Empire Cycle phase"""
        reasoning = {
            "raw_data": {},
            "calculations": {},
            "logic_chain": [],
            "conclusion": ""
        }
        
        # Raw empire indicators
        reasoning["raw_data"] = {
            "gdp_share": f"{indicators.get('economic_output_share', 23.9):.1f}% of global",
            "trade_share": f"{indicators.get('world_trade_share', 10.9):.1f}% of global",
            "reserve_currency": f"{indicators.get('reserve_currency_share', 58.4):.1f}% of reserves",
            "military_spending": f"{indicators.get('military_strength', 38.0):.1f}% of global",
            "education_score": f"{indicators.get('education_score', 60):.0f}/100",
            "innovation_score": f"{indicators.get('innovation_score', 65):.0f}/100"
        }
        
        # Calculate empire strength
        gdp_weight = indicators.get('economic_output_share', 23.9) * 2  # Double weight
        reserve_weight = indicators.get('reserve_currency_share', 58.4) * 1.5
        military_weight = indicators.get('military_strength', 38.0)
        
        empire_score = (gdp_weight + reserve_weight + military_weight) / 3
        
        reasoning["calculations"]["empire_strength"] = f"GDP({indicators.get('economic_output_share', 23.9):.1f}%×2) + Reserve({indicators.get('reserve_currency_share', 58.4):.1f}%×1.5) + Military({indicators.get('military_strength', 38.0):.1f}%) = Score: {empire_score:.1f}"
        
        # Logic chain for empire phase
        if indicators.get('reserve_currency_share', 58.4) < 60:
            reasoning["logic_chain"].append("Reserve currency share <60% → Early sign of empire transition")
        if indicators.get('education_score', 60) < 50:
            reasoning["logic_chain"].append("Education declining → First indicator of empire decline (Dalio's key insight)")
        if indicators.get('economic_output_share', 23.9) > 20:
            reasoning["logic_chain"].append("GDP share >20% → Still economically dominant")
        if indicators.get('military_strength', 38.0) > 35:
            reasoning["logic_chain"].append("Military spending >35% global → Maintaining military supremacy")
        
        # Determine phase
        if empire_score > 70:
            reasoning["conclusion"] = "PEAK: Empire at maximum power but showing early decline signals"
        elif empire_score > 50:
            reasoning["conclusion"] = "MATURE: Strong empire position but past absolute peak"
        else:
            reasoning["conclusion"] = "DECLINING: Loss of empire dominance accelerating"
        
        return reasoning

class InternalCycleAnalyzer:
    """Tracks Ray Dalio's Internal Order/Disorder Cycle"""
    
    def __init__(self):
        self.internal_stages = {
            1: "NEW_ORDER",  # Post-conflict consolidation
            2: "BUILDING",   # System establishment
            3: "PROSPERITY", # Peace and prosperity
            4: "BUBBLE",     # Excesses and gaps emerge
            5: "CRISIS",     # Financial distress + conflict
            6: "CIVIL_WAR"   # Open conflict/revolution
        }
        
        self.conflict_indicators = {
            "wealth_gap": 0,  # Gini coefficient
            "political_polarization": 0,  # 0-100
            "fiscal_deficit": 0,  # % of GDP
            "social_unrest": 0,  # 0-100
            "institutional_trust": 0  # 0-100
        }
    
    def detect_internal_stage(self, indicators: dict) -> dict:
        """Detect stage in internal order/disorder cycle"""
        
        # Calculate wealth gap (use Gini coefficient proxy)
        wealth_gap = indicators.get("wealth_gap", 0.35)  # US Gini ~0.48
        
        # Calculate political polarization (proxy from various factors)
        polarization = self.calculate_polarization(indicators)
        
        # Fiscal health
        fiscal_deficit = abs(indicators.get("fiscal_deficit", -5.0))
        
        # Determine stage based on Dalio's criteria
        if fiscal_deficit > 6 and wealth_gap > 0.40:
            if polarization > 70:
                return {"stage": 6, "name": "CIVIL_WAR", "risk": "EXTREME"}
            else:
                return {"stage": 5, "name": "CRISIS", "risk": "HIGH"}
        elif wealth_gap > 0.35 and fiscal_deficit > 4:
            return {"stage": 4, "name": "BUBBLE", "risk": "MEDIUM-HIGH"}
        elif wealth_gap < 0.30 and fiscal_deficit < 3:
            return {"stage": 3, "name": "PROSPERITY", "risk": "LOW"}
        elif fiscal_deficit < 2:
            return {"stage": 2, "name": "BUILDING", "risk": "LOW"}
        else:
            return {"stage": 1, "name": "NEW_ORDER", "risk": "MEDIUM"}
    
    def calculate_polarization(self, indicators):
        # Estimate political polarization from economic stress
        unemployment = indicators.get("unemployment", 4.0)
        inflation = indicators.get("inflation", 2.5)
        wealth_gap = indicators.get("wealth_gap", 0.35)
        
        # Higher unemployment + inflation + wealth gap = more polarization
        polarization = (unemployment * 5 + inflation * 10 + wealth_gap * 100) / 2
        return min(100, max(0, polarization))
    
    def get_civil_war_probability(self, indicators):
        """Calculate probability of civil conflict based on Dalio's framework"""
        # Key formula: bankruptcy + wealth gap = civil war risk
        fiscal_deficit = abs(indicators.get("fiscal_deficit", -5.0))
        wealth_gap = indicators.get("wealth_gap", 0.35)
        debt_to_gdp = indicators.get("debt_to_gdp", 125.0)
        
        # Risk factors
        risk_score = 0
        if fiscal_deficit > 6: risk_score += 30
        if wealth_gap > 0.40: risk_score += 30
        if debt_to_gdp > 100: risk_score += 20
        if indicators.get("unemployment", 4) > 6: risk_score += 10
        if self.calculate_polarization(indicators) > 60: risk_score += 10
        
        return min(100, risk_score)
    
    def get_internal_reasoning(self, indicators: dict) -> dict:
        """Generate detailed reasoning for Internal Order/Disorder stage"""
        reasoning = {
            "raw_data": {},
            "calculations": {},
            "logic_chain": [],
            "conclusion": ""
        }
        
        wealth_gap = indicators.get("wealth_gap", 0.418)
        polarization = indicators.get("political_polarization", 82.3)
        fiscal_deficit = abs(indicators.get("fiscal_deficit", -6.0))
        unemployment = indicators.get("unemployment", 4.3)
        
        reasoning["raw_data"] = {
            "gini_coefficient": f"{wealth_gap:.3f}",
            "top_1_percent_wealth": f"{indicators.get('top_1_percent', 0.35)*100:.1f}%",
            "political_polarization": f"{polarization:.1f}%",
            "fiscal_deficit": f"{fiscal_deficit:.1f}% of GDP",
            "unemployment": f"{unemployment:.1f}%",
            "institutional_trust": f"{indicators.get('institutional_trust', 27):.0f}%"
        }
        
        # Calculate civil war probability (Dalio formula)
        civil_war_prob = 0
        if wealth_gap > 0.45:
            civil_war_prob += 30
            reasoning["logic_chain"].append(f"Gini >{0.45} → +30% conflict risk")
        if polarization > 70:
            civil_war_prob += 30
            reasoning["logic_chain"].append(f"Polarization >{70}% → +30% conflict risk")
        if fiscal_deficit > 5:
            civil_war_prob += 20
            reasoning["logic_chain"].append(f"Deficit >{5}% GDP → +20% conflict risk")
        if unemployment > 6:
            civil_war_prob += 20
            reasoning["logic_chain"].append(f"Unemployment >{6}% → +20% conflict risk")
        
        reasoning["calculations"]["civil_war_calculation"] = f"Base risk factors sum to {civil_war_prob}% probability"
        
        # Determine stage with detailed reasoning
        result = self.detect_internal_stage(indicators)
        stage = result["stage"] if isinstance(result, dict) else result
        
        if stage >= 5:
            reasoning["conclusion"] = "STAGE 5+ - CRISIS: Multiple red flags present. Historical parallel: 1930s, pre-civil war conditions"
        elif stage == 4:
            reasoning["conclusion"] = "STAGE 4 - DISORDER: Growing conflicts, weakening institutions"
        elif stage == 3:
            reasoning["conclusion"] = "STAGE 3 - PEAK: Prosperity but growing inequality seeds of future conflict"
        else:
            reasoning["conclusion"] = f"STAGE {stage} - Early cycle: System building or consolidation phase"
        
        reasoning["logic_chain"].append(f"Dalio's framework: High inequality + high debt + political extremism = Stage {stage}")
        
        return reasoning

# Helper functions for comprehensive analysis
def determine_combined_regime(stdc_phase: str, ltdc_phase: str) -> str:
    """Determine combined regime from short and long term cycles"""
    if ltdc_phase == "DEPRESSION":
        return "Deleveraging"
    elif ltdc_phase == "BUBBLE" and stdc_phase == "LATE_EXPANSION":
        return "Peak Bubble"
    elif stdc_phase == "RECESSION":
        return "Recession"
    elif stdc_phase == "EARLY_EXPANSION":
        return "Recovery"
    elif stdc_phase == "LATE_EXPANSION":
        return "Late Cycle"
    else:
        return "Mid Cycle"

def calculate_comprehensive_risk(stdc, ltdc, empire, internal):
    """Calculate overall risk from all 4 cycles"""
    risk_score = 0
    
    # STDC risk
    if stdc["phase"] in ["LATE_EXPANSION", "EARLY_CONTRACTION"]:
        risk_score += 20
    elif stdc["phase"] == "RECESSION":
        risk_score += 30
    
    # LTDC risk
    if ltdc["phase"] in ["BUBBLE", "TOP"]:
        risk_score += 25
    elif ltdc["phase"] == "DEPRESSION":
        risk_score += 40
    
    # Empire risk
    if empire["phase"] in ["DECLINE_LATE", "COLLAPSE"]:
        risk_score += 30
    elif empire["phase"] == "DECLINE_EARLY":
        risk_score += 15
    
    # Internal risk
    if internal["stage"] >= 5:
        risk_score += 35
    elif internal["stage"] == 4:
        risk_score += 20
    
    # Determine level
    if risk_score >= 80:
        level = "EXTREME"
    elif risk_score >= 60:
        level = "HIGH"
    elif risk_score >= 40:
        level = "MEDIUM-HIGH"
    elif risk_score >= 20:
        level = "MEDIUM"
    else:
        level = "LOW"
    
    return {"level": level, "score": risk_score, "details": "Multi-cycle risk assessment"}

def generate_comprehensive_recommendations(stdc, ltdc, empire, internal, indicators):
    """Generate recommendations based on all 4 cycles"""
    recommendations = []
    
    # Critical warnings first
    if internal["stage"] >= 5:
        recommendations.append("⚠️ CRITICAL: High civil conflict risk - maximize portfolio safety")
    
    if ltdc["phase"] in ["BUBBLE", "TOP"]:
        recommendations.append("Long-term debt cycle peaking - prepare for potential deleveraging")
    
    if empire["phase"] in ["DECLINE_LATE", "COLLAPSE"]:
        recommendations.append("Empire cycle declining - consider geographic diversification")
    
    # Asset allocation recommendations
    if stdc["phase"] == "LATE_EXPANSION" and ltdc["phase"] == "BUBBLE":
        recommendations.append("Reduce risk assets - both short and long cycles are extended")
        recommendations.append("Increase cash and defensive positions")
    
    # Specific actions based on indicators
    if indicators.get("wealth_gap", 0) > 0.45:
        recommendations.append("Extreme wealth inequality - expect policy changes and higher taxes")
    
    if indicators.get("debt_to_gdp", 0) > 120:
        recommendations.append("Unsustainable debt levels - prepare for currency debasement")
    
    return recommendations[:6]  # Return top 6 most important

def generate_synthesis_reasoning(indicators, stdc, ltdc, empire, internal):
    """Synthesize reasoning across all cycles"""
    synthesis = {
        "combined_assessment": [],
        "risk_factors": [],
        "historical_parallels": [],
        "key_insights": []
    }
    
    # Extract phase names from results
    stdc_phase = stdc["phase"] if isinstance(stdc, dict) else stdc
    ltdc_phase = ltdc["phase"] if isinstance(ltdc, dict) else ltdc
    empire_phase = empire["phase"] if isinstance(empire, dict) else empire
    internal_stage = internal["stage"] if isinstance(internal, dict) else internal
    
    # Cross-cycle analysis
    if "PEAK" in stdc_phase and ltdc_phase == "NORMALIZATION":
        synthesis["combined_assessment"].append("Short cycle peaking while long cycle stressed → Heightened recession risk")
    
    if "LATE_EXPANSION" in stdc_phase and ltdc_phase in ["BUBBLE", "TOP"]:
        synthesis["combined_assessment"].append("Both short and long cycles extended → Major correction likely")
    
    if empire_phase == "PEAK" and internal_stage >= 5:
        synthesis["combined_assessment"].append("Empire at peak + internal disorder → Historical transition point (Rome 180AD, Britain 1914)")
    
    # Risk synthesis
    debt_to_gdp = indicators.get("debt_to_gdp", 100)
    wealth_gap = indicators.get("wealth_gap", 0.418)
    
    if debt_to_gdp > 100 and wealth_gap > 0.45:
        synthesis["risk_factors"].append("CRITICAL: High debt + extreme inequality = social instability risk")
    
    if indicators.get("real_interest_rate", 2) < 0:
        synthesis["risk_factors"].append("Negative real rates → Financial repression environment")
    
    if indicators.get("fiscal_deficit", -5) < -6:
        synthesis["risk_factors"].append("Large fiscal deficits → Unsustainable government spending")
    
    # Historical parallels
    if internal_stage >= 5:
        synthesis["historical_parallels"].append("1930s: Similar wealth gap, political polarization preceded conflict")
    
    if isinstance(empire, dict) and empire.get("score", 0) < 80 and empire.get("score", 0) > 60:
        synthesis["historical_parallels"].append("1960s Britain: Empire transition from dominance to partnership")
    
    if debt_to_gdp > 120:
        synthesis["historical_parallels"].append("Post-WWII debt levels: Required financial repression to resolve")
    
    # Key Dalio insights
    if debt_to_gdp > 100 and indicators.get("real_interest_rate", 2) < 0:
        synthesis["key_insights"].append(f"Dalio Principle: When debt > 100% GDP and real rates < 0, expect financial repression")
    
    synthesis["key_insights"].append(f"Empire Cycle: Education decline precedes economic decline by 10-20 years")
    
    if wealth_gap > 0.45 and debt_to_gdp > 100:
        synthesis["key_insights"].append("Dalio's Formula: High debt + high inequality = recipe for revolution or war")
    
    return synthesis

# Database Storage Functions
async def store_macro_indicators(indicators: Dict[str, float], conn) -> None:
    """Store macro indicators in database"""
    query = """
        INSERT INTO macro_indicators (indicator_name, value, last_updated, is_current)
        VALUES ($1, $2, NOW(), true)
        ON CONFLICT (indicator_name) WHERE is_current = true
        DO UPDATE SET value = EXCLUDED.value, last_updated = NOW()
    """
    
    try:
        for name, value in indicators.items():
            await conn.execute(query, name, value)
        logger.info(f"Stored {len(indicators)} indicators in database")
    except Exception as e:
        logger.error(f"Error storing indicators in database: {e}")

# Macro Regime Detection
async def detect_macro_regime() -> dict:
    """Comprehensive Dalio framework with real data from multiple sources"""
    # Try to fetch macro indicators from FRED API first, then database, then environment
    indicators = {}
    
    if USE_MOCK_DATA:
        # Mock mode - use simulated data
        indicators = {
            "gdp_growth": 2.3,
            "inflation": 3.2,
            "unemployment": 3.7,
            "interest_rate": 5.25,
            "yield_curve": -0.05,  # Slightly inverted
            "vix": 18.5,
            "dollar_index": 104.2,
            "credit_spreads": 1.2,
            "pmi": 48.5,  # Below 50 indicates contraction
            "consumer_confidence": 68.0,
            "debt_to_gdp": 125.0,
            "credit_growth": 3.5,
            "productivity_growth": 1.2,
            "fiscal_deficit": -5.8,
            "wealth_gap": 0.48,  # US Gini coefficient
            "m2_growth": 4.5,
            "real_interest_rate": 2.05
        }
    else:
        # Production mode - try FRED API first, then database, then environment variables
        fred_client = FREDClient()
        
        if fred_client.api_key:
            try:
                # Try to fetch from FRED API using cache
                fred_data = await get_cached_fred_data()
                if fred_data:
                    indicators.update(fred_data)
                    logger.info(f"Fetched {len(fred_data)} indicators from FRED API")
                    
                    # Store in database for historical tracking
                    if db_pool:
                        try:
                            async with db_pool.acquire() as conn:
                                await store_macro_indicators(fred_data, conn)
                        except Exception as e:
                            logger.warning(f"Could not store FRED data in database: {e}")
            except Exception as e:
                logger.warning(f"Could not fetch from FRED API: {e}")
        else:
            logger.info("FRED API key not configured. Using cached or default indicators.")
        
        # If FRED didn't work, try database
        if not indicators and db_pool:
            try:
                async with db_pool.acquire() as conn:
                    # Try to fetch from macro_indicators table
                    query = """
                        SELECT indicator_name, value, last_updated
                        FROM macro_indicators
                        WHERE is_current = true
                    """
                    rows = await conn.fetch(query)
                    
                    if rows:
                        for row in rows:
                            indicators[row["indicator_name"]] = float(row["value"])
                        logger.info(f"Fetched {len(indicators)} indicators from database")
                    
            except Exception as e:
                logger.warning(f"Could not fetch macro indicators from database: {e}")
        
        # NEW: Enhance with additional data sources from MacroDataAgent
        try:
            indicators = await enhance_macro_data(indicators)
            logger.info("Enhanced indicators with MacroDataAgent data")
        except Exception as e:
            logger.warning(f"Could not enhance with MacroDataAgent: {e}")
        
        # Final fallback to environment variables
        if not indicators:
            # Try to get from environment variables or use defaults
            indicators = {
                "gdp_growth": float(os.getenv("MACRO_GDP_GROWTH", "2.0")),
                "inflation": float(os.getenv("MACRO_INFLATION", "2.5")),
                "unemployment": float(os.getenv("MACRO_UNEMPLOYMENT", "4.0")),
                "interest_rate": float(os.getenv("MACRO_INTEREST_RATE", "5.0")),
                "yield_curve": float(os.getenv("MACRO_YIELD_CURVE", "0.5")),
                "vix": float(os.getenv("MACRO_VIX", "16.0")),
                "dollar_index": float(os.getenv("MACRO_DOLLAR_INDEX", "100.0")),
                "credit_spreads": float(os.getenv("MACRO_CREDIT_SPREADS", "1.0")),
                "pmi": float(os.getenv("MACRO_PMI", "50.0")),
                "consumer_confidence": float(os.getenv("MACRO_CONSUMER_CONFIDENCE", "70.0")),
                "debt_to_gdp": float(os.getenv("MACRO_DEBT_TO_GDP", "125.0")),
                "credit_growth": float(os.getenv("MACRO_CREDIT_GROWTH", "5.0")),
                "productivity_growth": float(os.getenv("MACRO_PRODUCTIVITY_GROWTH", "1.5")),
                "fiscal_deficit": float(os.getenv("MACRO_FISCAL_DEFICIT", "-5.0")),
                "wealth_gap": float(os.getenv("MACRO_WEALTH_GAP", "0.48")),
                "m2_growth": float(os.getenv("MACRO_M2_GROWTH", "5.0"))
            }
            
            # Calculate real interest rate if not present
            if "real_interest_rate" not in indicators:
                indicators["real_interest_rate"] = indicators["interest_rate"] - indicators["inflation"]
            
            logger.info("Using environment variables for macro indicators")
    
    # Add wealth gap indicator if not present (US Gini coefficient ~0.48)
    if "wealth_gap" not in indicators:
        indicators["wealth_gap"] = float(os.getenv("MACRO_WEALTH_GAP", "0.48"))
    
    # Initialize data fetchers
    empire_fetcher = EmpireDataFetcher()
    internal_fetcher = InternalDataFetcher()
    
    # Fetch Empire cycle data
    try:
        empire_indicators = await empire_fetcher.fetch_empire_indicators(indicators)
        indicators.update(empire_indicators)
        logger.info(f"Fetched {len(empire_indicators)} empire indicators")
    except Exception as e:
        logger.warning(f"Could not fetch empire indicators: {e}")
    
    # Fetch Internal cycle data
    try:
        internal_indicators = await internal_fetcher.fetch_internal_indicators(indicators)
        indicators.update(internal_indicators)
        logger.info(f"Fetched {len(internal_indicators)} internal indicators")
    except Exception as e:
        logger.warning(f"Could not fetch internal indicators: {e}")
    
    # Initialize all cycle analyzers with real data
    dalio_analyzer = DalioCycleAnalyzer()
    empire_analyzer = EmpireCycleAnalyzer()
    internal_analyzer = InternalCycleAnalyzer()
    
    # Detect all cycle positions with enriched data
    stdc_result = dalio_analyzer.detect_stdc_phase(indicators)
    ltdc_result = dalio_analyzer.detect_ltdc_phase(indicators)
    
    # Empire phase detection with real data
    empire_result = empire_analyzer.detect_empire_phase(indicators)
    empire_result["real_data"] = {
        "gdp_share": indicators.get("economic_output_share", 23.9),
        "trade_share": indicators.get("world_trade_share", 10.9),
        "reserve_currency": indicators.get("reserve_currency_share", 58.4),
        "military_spending": indicators.get("military_strength", 38.0)
    }
    
    # Internal stage detection with real data
    internal_result = internal_analyzer.detect_internal_stage(indicators)
    internal_result["real_data"] = {
        "gini_coefficient": indicators.get("wealth_gap", 0.485),
        "top_1_percent": indicators.get("top_1_percent", 0.35),
        "polarization": indicators.get("political_polarization", 71.0),
        "trust": indicators.get("institutional_trust", 27.0)
    }
    
    # NEW: Generate detailed reasoning for each cycle
    reasoning = {
        "stdc": dalio_analyzer.get_stdc_reasoning(indicators),
        "ltdc": dalio_analyzer.get_ltdc_reasoning(indicators),
        "empire": empire_analyzer.get_empire_reasoning(indicators),
        "internal": internal_analyzer.get_internal_reasoning(indicators),
        "synthesis": generate_synthesis_reasoning(indicators, stdc_result, ltdc_result, empire_result, internal_result)
    }
    
    # Calculate comprehensive risk assessment
    overall_risk = calculate_comprehensive_risk(stdc_result, ltdc_result, empire_result, internal_result)
    
    # Generate unified recommendations
    recommendations = generate_comprehensive_recommendations(
        stdc_result, ltdc_result, empire_result, internal_result, indicators
    )
    
    # Generate portfolio recommendations based on regime
    # Use mock portfolio data for recommendations in production mode
    if USE_MOCK_DATA:
        portfolio = calculate_portfolio_metrics()
    else:
        # In production, use simplified portfolio data without calling mock functions
        # This avoids calling mock functions in production mode
        portfolio = {
            "portfolio_beta": 1.2,  # Default conservative estimate
            "holdings": [
                {"symbol": "SPY", "weight": 0.3, "sector": "Technology"},
                {"symbol": "QQQ", "weight": 0.2, "sector": "Technology"},
                {"symbol": "BND", "weight": 0.2, "sector": "Financial"},
                {"symbol": "GLD", "weight": 0.15, "sector": "Commodities"},
                {"symbol": "REIT", "weight": 0.15, "sector": "Real Estate"}
            ]
        }
    
    # Assess portfolio risk in current regime
    combined_regime = determine_combined_regime(stdc_result["phase"], ltdc_result["phase"])
    portfolio_risk_assessment = assess_portfolio_risk(portfolio, combined_regime, indicators)
    
    return {
        "current_regime": combined_regime,
        "risk_level": overall_risk["level"],
        
        # All 4 cycles
        "stdc_phase": stdc_result["phase"],
        "stdc_metrics": stdc_result.get("metrics", {}),
        
        "ltdc_phase": ltdc_result["phase"],
        "debt_metrics": ltdc_result.get("metrics", {}),
        
        "empire_phase": empire_result["phase"],
        "empire_score": empire_result["score"],
        # Map empire indicators to match UI expected field names
        "empire_indicators": {
            "education_score": empire_analyzer.empire_indicators.get("education", 0),
            "innovation_score": empire_analyzer.empire_indicators.get("innovation", 0),
            "competitiveness_score": empire_analyzer.empire_indicators.get("competitiveness", 0),
            "economic_output_share": empire_analyzer.empire_indicators.get("economic_output", 0),
            "world_trade_share": empire_analyzer.empire_indicators.get("world_trade_share", 0),
            "military_strength": empire_analyzer.empire_indicators.get("military_strength", 0),
            "financial_center_score": empire_analyzer.empire_indicators.get("financial_center", 0),
            "reserve_currency_share": empire_analyzer.empire_indicators.get("reserve_currency", 0)
        },
        
        "internal_stage": internal_result["stage"],
        "internal_stage_name": internal_result["name"],
        "civil_war_probability": internal_analyzer.get_civil_war_probability(indicators),
        
        "indicators": indicators,
        "recommendations": recommendations,
        "deleveraging_score": dalio_analyzer.get_deleveraging_score(indicators) if ltdc_result["phase"] == "DEPRESSION" else None,
        
        # Additional analysis
        "wealth_gap": indicators.get("wealth_gap", 0.48),
        "political_polarization": internal_analyzer.calculate_polarization(indicators),
        "trend": "Complex multi-cycle dynamics",
        "portfolio_risk_assessment": portfolio_risk_assessment,
        
        # NEW: Add reasoning chains and data sources
        "reasoning": reasoning,
        "data_sources": {
            "fred_api": "Federal Reserve Economic Data (15+ indicators)",
            "world_bank": "Gini coefficient, inequality metrics",
            "imf": "Reserve currency composition (COFER)",
            "static_estimates": "Empire metrics from WTO, SIPRI"
        },
        
        # Legacy fields for backward compatibility
        "regime_probability": {
            combined_regime: 0.65,
            "Alternative": 0.35
        },
        "next_review": "Monthly",
        "key_risks": identify_key_risks(indicators),
        "opportunities": identify_opportunities(combined_regime, indicators)
    }

def identify_leading_indicators(indicators: dict, cycles: dict) -> dict:
    """Identify leading indicators suggesting cycle transitions"""
    
    leading_signals = []
    
    # Empire cycle leading indicators (Dalio's framework)
    education_score = indicators.get("education_score", 60)
    if education_score < 50:
        leading_signals.append({
            "type": "Empire",
            "signal": "Declining education (first sign of empire decline)",
            "severity": "HIGH",
            "timeframe": "5-10 years"
        })
    
    # Check for reserve currency weakness
    reserve_share = indicators.get("reserve_currency_share", 58.4)
    if reserve_share < 60 and cycles.get("empire_phase") == "PEAK":
        leading_signals.append({
            "type": "Empire",
            "signal": "Reserve currency share declining from peak",
            "severity": "MEDIUM",
            "timeframe": "10-20 years"
        })
    
    # Internal cycle leading indicators
    wealth_gap = indicators.get("wealth_gap", 0.485)
    fiscal_deficit = abs(indicators.get("fiscal_deficit", -6.0))
    
    if wealth_gap > 0.45 and fiscal_deficit > 5:
        leading_signals.append({
            "type": "Internal",
            "signal": "Dangerous combination: High inequality + fiscal stress",
            "severity": "HIGH",
            "timeframe": "2-5 years"
        })
    
    # Short-term debt cycle leading indicators
    yield_curve = indicators.get("yield_curve", 0.5)
    if yield_curve < 0:
        leading_signals.append({
            "type": "STDC",
            "signal": "Inverted yield curve predicting recession",
            "severity": "MEDIUM",
            "timeframe": "6-18 months"
        })
    
    # Long-term debt cycle leading indicators
    debt_to_gdp = indicators.get("debt_to_gdp", 125)
    real_rates = indicators.get("real_interest_rate", 2.3)
    
    if debt_to_gdp > 100 and real_rates < 0:
        leading_signals.append({
            "type": "LTDC",
            "signal": "Unsustainable debt with financial repression",
            "severity": "HIGH",
            "timeframe": "3-7 years"
        })
    
    return {
        "leading_indicators": leading_signals,
        "cycle_transition_risk": "HIGH" if len(leading_signals) > 3 else "MEDIUM" if len(leading_signals) > 1 else "LOW"
    }

def generate_macro_recommendations(regime: str, indicators: dict, portfolio: dict) -> List[str]:
    """Generate recommendations based on macro regime and portfolio"""
    recommendations = []
    portfolio_beta = portfolio["portfolio_beta"]
    
    if regime == "Late Cycle Expansion":
        recommendations.extend([
            f"Portfolio beta of {portfolio_beta:.2f} may be too aggressive for late cycle",
            "Rotate from growth to quality/value stocks",
            "Increase defensive allocation (consumer staples, utilities)",
            "Build cash reserves (target 10-15%)",
            "Consider taking profits on high-flying tech stocks"
        ])
    elif regime == "Pre-Recession":
        recommendations.extend([
            "Urgent: Reduce equity exposure to defensive levels",
            "Increase allocation to government bonds",
            "Eliminate or hedge high-beta positions",
            "Focus on companies with strong balance sheets",
            "Prepare shopping list for post-recession opportunities"
        ])
    elif regime == "Stagflation":
        recommendations.extend([
            "Add commodities and real assets",
            "Focus on companies with pricing power",
            "Reduce long-duration bonds",
            "Consider international diversification",
            "Add inflation-protected securities"
        ])
    elif regime == "Goldilocks":
        recommendations.extend([
            "Favorable environment for risk assets",
            "Maintain or increase equity allocation",
            "Focus on growth stocks with strong fundamentals",
            "Consider adding emerging markets exposure",
            "Use any pullbacks as buying opportunities"
        ])
    
    return recommendations[:5]

def assess_portfolio_risk(portfolio: dict, regime: str, indicators: dict) -> dict:
    """Assess portfolio risk in current macro environment"""
    risk_factors = []
    risk_score = 0
    
    # Check concentration risk
    tech_weight = sum(h["weight"] for h in portfolio["holdings"] if h["sector"] == "Technology")
    if tech_weight > 0.5:
        risk_factors.append(f"High technology concentration ({tech_weight*100:.1f}%)")
        risk_score += 2
    
    # Check beta risk
    if portfolio["portfolio_beta"] > 1.3 and regime in ["Late Cycle Expansion", "Pre-Recession"]:
        risk_factors.append(f"High portfolio beta ({portfolio['portfolio_beta']:.2f}) in risky regime")
        risk_score += 3
    
    # Check for defensive assets
    defensive_weight = sum(h["weight"] for h in portfolio["holdings"] if h["sector"] == "Financial")
    if defensive_weight < 0.2 and regime in ["Pre-Recession", "Recession"]:
        risk_factors.append(f"Low defensive allocation ({defensive_weight*100:.1f}%)")
        risk_score += 2
    
    # Check correlation risk
    if indicators["vix"] > 20:
        risk_factors.append("Elevated market volatility increases correlation risk")
        risk_score += 1
    
    overall_risk = "High" if risk_score > 5 else "Medium" if risk_score > 2 else "Low"
    
    return {
        "overall_risk": overall_risk,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "regime_alignment": "Misaligned" if risk_score > 3 else "Partially Aligned" if risk_score > 1 else "Well Aligned",
        "suggested_adjustments": generate_risk_adjustments(risk_factors, regime)
    }

def generate_risk_adjustments(risk_factors: List[str], regime: str) -> List[str]:
    """Generate specific risk adjustments"""
    adjustments = []
    
    for factor in risk_factors:
        if "technology concentration" in factor.lower():
            adjustments.append("Reduce technology holdings by 10-15%")
        if "high portfolio beta" in factor.lower():
            adjustments.append("Add low-beta defensive stocks or bonds")
        if "defensive allocation" in factor.lower():
            adjustments.append("Increase defensive sectors to 25-30% of portfolio")
    
    return adjustments

def identify_key_risks(indicators: dict) -> List[str]:
    """Identify key macroeconomic risks"""
    risks = []
    
    if indicators["yield_curve"] < 0:
        risks.append("Inverted yield curve signals recession risk")
    if indicators["inflation"] > 3:
        risks.append("Elevated inflation may force aggressive Fed action")
    if indicators["pmi"] < 50:
        risks.append("Manufacturing contraction indicates slowing economy")
    if indicators["vix"] > 20:
        risks.append("High market volatility suggests increased uncertainty")
    if indicators["credit_spreads"] > 1.5:
        risks.append("Widening credit spreads signal financial stress")
    
    return risks[:4]

def identify_opportunities(regime: str, indicators: dict) -> List[str]:
    """Identify investment opportunities"""
    opportunities = []
    
    if regime == "Late Cycle Expansion":
        opportunities.extend([
            "Defensive sectors outperform in late cycle",
            "Quality factor tends to outperform",
            "International diversification opportunities"
        ])
    elif regime == "Goldilocks":
        opportunities.extend([
            "Growth stocks in favorable environment",
            "Emerging markets attractive",
            "Risk-on assets well-positioned"
        ])
    elif regime == "Pre-Recession":
        opportunities.extend([
            "Government bonds rally in recession",
            "Prepare to buy equities at lower levels",
            "Defensive stocks preserve capital"
        ])
    
    return opportunities[:3]

# Smart Alerts System
def check_alerts() -> List[dict]:
    """Get all configured alerts"""
    return ACTIVE_ALERTS

def create_alert(alert_data: dict) -> dict:
    """Create a new alert configuration"""
    alert_id = f"alert-{str(uuid4())[:8]}"
    
    # Build alert object based on type
    alert = {
        "id": alert_id,
        "type": alert_data.get("type"),
        "condition": alert_data.get("condition"),
        "threshold": alert_data.get("threshold"),
        "message": alert_data.get("message"),
        "active": True,
        "last_triggered": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Add type-specific fields
    if alert["type"] == "price":
        alert["symbol"] = alert_data.get("symbol")
    elif alert["type"] in ["portfolio", "macro"]:
        alert["metric"] = alert_data.get("metric")
    
    ACTIVE_ALERTS.append(alert)
    return alert

def update_alert(alert_id: str, updates: dict) -> Optional[dict]:
    """Update an existing alert"""
    for alert in ACTIVE_ALERTS:
        if alert["id"] == alert_id:
            # Update allowed fields
            if "active" in updates:
                alert["active"] = updates["active"]
            if "threshold" in updates:
                alert["threshold"] = updates["threshold"]
            if "message" in updates:
                alert["message"] = updates["message"]
            return alert
    return None

def delete_alert(alert_id: str) -> bool:
    """Delete an alert by ID"""
    global ACTIVE_ALERTS
    for i, alert in enumerate(ACTIVE_ALERTS):
        if alert["id"] == alert_id:
            ACTIVE_ALERTS.pop(i)
            return True
    return False

# Claude AI Integration
async def analyze_with_claude(query: str, context: dict) -> dict:
    """Use Claude AI to analyze portfolio"""
    if USE_MOCK_DATA:
        # Mock mode - use mock AI response
        return await generate_mock_ai_response(query, context)
    
    if not ANTHROPIC_API_KEY:
        # In production mode, fail if no API key
        logger.error("Claude API key not configured")
        raise HTTPException(
            status_code=503,
            detail="AI analysis service not configured. Please configure API key."
        )
    
    try:
        # Get portfolio data from context or database
        user_email = context.get("user_email", "michael@dawsos.com")
        portfolio = await calculate_portfolio_metrics_from_db(user_email)
        macro = await detect_macro_regime()
        
        # Prepare context for Claude
        system_prompt = """You are an expert portfolio manager and financial analyst. 
        Analyze the portfolio and provide actionable insights based on current holdings, 
        market conditions, and the user's query."""
        
        user_message = f"""
        Query: {query}
        
        Portfolio Summary:
        - Total Value: ${portfolio['total_value']:,.2f}
        - YTD Return: {portfolio['returns_ytd']*100:.2f}%
        - Beta: {portfolio['portfolio_beta']:.2f}
        - Sharpe Ratio: {portfolio['sharpe_ratio']:.2f}
        
        Holdings: {json.dumps([{
            'symbol': h['symbol'],
            'weight': h['weight'],
            'sector': h['sector']
        } for h in portfolio['holdings']], indent=2)}
        
        Current Macro Regime: {macro['current_regime']}
        Risk Level: {macro['risk_level']}
        
        Please provide specific, actionable insights and recommendations.
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1000,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_message}]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "analysis": result["content"][0]["text"],
                    "query": query,
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": "claude-3-haiku",
                    "status": "success"
                }
            else:
                logger.error(f"Claude API error: {response.status_code}")
                raise HTTPException(
                    status_code=503,
                    detail="AI service temporarily unavailable. Please try again later."
                )
    
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable. Please try again later."
        )

async def generate_mock_ai_response(query: str, context: dict) -> dict:
    """Generate intelligent mock AI response - MOCK MODE ONLY"""
    if not USE_MOCK_DATA:
        logger.error("generate_mock_ai_response() called in production mode - this should not happen")
        raise HTTPException(
            status_code=500,
            detail="Internal server error: Mock function called in production mode"
        )
    
    # Mock mode - use mock data for AI response
    if USE_MOCK_DATA:
        portfolio = calculate_portfolio_metrics()  # Use mock portfolio function
    else:
        # Use simplified portfolio data in production mode
        portfolio = {
            "total_value": 100000,
            "holdings": [{"symbol": "SPY", "weight": 0.45}, {"symbol": "BND", "weight": 0.15}],
            "portfolio_beta": 1.0,
            "sharpe_ratio": 1.2
        }
    macro = await detect_macro_regime()  # This is safe, already has mock check
    
    # Generate contextual response based on query keywords
    query_lower = query.lower()
    insights = []
    recommendations = []
    
    if "risk" in query_lower:
        insights.extend([
            f"Your portfolio beta of {portfolio['portfolio_beta']:.2f} indicates {'high' if portfolio['portfolio_beta'] > 1.2 else 'moderate'} market sensitivity.",
            f"Current VaR (95%) is ${portfolio['var_95']:,.2f}, representing {(portfolio['var_95']/portfolio['total_value']*100):.2f}% of portfolio value.",
            f"The portfolio is currently in a {macro['risk_level']} risk environment given the {macro['current_regime']} regime."
        ])
        recommendations.extend([
            "Consider reducing high-beta positions to lower portfolio volatility",
            "Add defensive assets like utilities or consumer staples",
            "Implement stop-loss orders on volatile positions"
        ])
    
    elif "optimize" in query_lower or "rebalance" in query_lower:
        tech_weight = sum(h["weight"] for h in portfolio["holdings"] if h["sector"] == "Technology")
        insights.extend([
            f"Technology sector represents {tech_weight*100:.1f}% of your portfolio, suggesting concentration risk.",
            f"Your Sharpe ratio of {portfolio['sharpe_ratio']:.2f} indicates {'strong' if portfolio['sharpe_ratio'] > 1.5 else 'moderate'} risk-adjusted returns.",
            "Current sector allocation shows opportunities for better diversification."
        ])
        recommendations.extend([
            f"Reduce technology allocation from {tech_weight*100:.1f}% to 40% for better diversification",
            "Add 15% allocation to defensive sectors (utilities, healthcare)",
            "Consider 10% allocation to international markets for geographic diversification"
        ])
    
    elif "performance" in query_lower:
        insights.extend([
            f"Portfolio has generated {portfolio['returns_ytd']*100:.2f}% YTD, {'outperforming' if portfolio['returns_ytd'] > 0.10 else 'in line with'} market benchmarks.",
            f"Recent performance: 1D: {portfolio['returns_1d']*100:.2f}%, 1W: {portfolio['returns_1w']*100:.2f}%, 1M: {portfolio['returns_1m']*100:.2f}%",
            f"Top performer: NVDA with high-beta growth characteristics"
        ])
        recommendations.extend([
            "Lock in profits on positions up >30% YTD",
            "Reinvest gains into undervalued sectors",
            "Maintain discipline with regular rebalancing"
        ])
    
    else:  # General analysis
        insights.extend([
            f"Your portfolio value of ${portfolio['total_value']:,.2f} is well-positioned but requires attention to concentration risks.",
            f"The {macro['current_regime']} macro regime suggests a cautious approach to risk assets.",
            f"Portfolio diversification across {len(set(h['sector'] for h in portfolio['holdings']))} sectors provides some protection."
        ])
        recommendations.extend([
            "Review and rebalance quarterly to maintain target allocations",
            "Build cash reserves to 10% for opportunities",
            "Monitor Fed policy changes closely given current regime"
        ])
    
    return {
        "analysis": {
            "insights": insights,
            "recommendations": recommendations,
            "risk_assessment": f"Portfolio risk level: {macro['portfolio_risk_assessment']['overall_risk']}",
            "action_items": recommendations[:3]
        },
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "model": "mock-ai-engine",
        "status": "success"
    }

# Portfolio Optimization
def optimize_portfolio(request: OptimizationRequest) -> dict:
    """Generate portfolio optimization recommendations"""
    # Only use mock portfolio in mock mode
    if USE_MOCK_DATA:
        portfolio = calculate_portfolio_metrics()
    else:
        # Use simplified portfolio data in production mode
        portfolio = {
            "total_value": 100000,
            "holdings": [
                {"symbol": "SPY", "quantity": 100, "price": 450, "value": 45000, "weight": 0.45, "sector": "Index", "beta": 1.0},
                {"symbol": "BND", "quantity": 200, "price": 75, "value": 15000, "weight": 0.15, "sector": "Bonds", "beta": 0.3},
                {"symbol": "QQQ", "quantity": 50, "price": 380, "value": 19000, "weight": 0.19, "sector": "Technology", "beta": 1.2},
                {"symbol": "VTI", "quantity": 75, "price": 280, "value": 21000, "weight": 0.21, "sector": "Total Market", "beta": 1.0}
            ],
            "portfolio_beta": 0.95,
            "portfolio_volatility": 0.14,
            "sharpe_ratio": 1.1,
            "returns_ytd": 0.12
        }
    
    holdings = portfolio["holdings"]
    
    # Calculate current risk-return profile
    current_return = portfolio["returns_ytd"]
    current_risk = portfolio["portfolio_volatility"]
    current_sharpe = portfolio["sharpe_ratio"]
    
    # Generate optimal weights based on risk tolerance
    risk_tolerance = request.risk_tolerance
    target_return = request.target_return or current_return * 1.2
    
    # Simple optimization logic (in production, use scipy.optimize or cvxpy)
    optimal_weights = calculate_optimal_weights(holdings, risk_tolerance)
    
    # Calculate rebalancing trades
    trades = []
    for i, holding in enumerate(holdings):
        current_weight = holding["weight"]
        optimal_weight = optimal_weights[i]
        weight_diff = optimal_weight - current_weight
        
        if abs(weight_diff) > 0.02:  # Only suggest trades > 2% difference
            value_change = weight_diff * portfolio["total_value"]
            shares_change = int(value_change / holding["price"])
            
            if shares_change != 0:
                trades.append({
                    "symbol": holding["symbol"],
                    "action": "BUY" if shares_change > 0 else "SELL",
                    "shares": abs(shares_change),
                    "current_weight": round(current_weight, 4),
                    "target_weight": round(optimal_weight, 4),
                    "value": abs(value_change),
                    "reason": generate_trade_reason(holding, weight_diff, risk_tolerance)
                })
    
    # Sort trades by value
    trades.sort(key=lambda x: x["value"], reverse=True)
    
    # Calculate expected improvements
    expected_return = calculate_expected_return(holdings, optimal_weights)
    expected_risk = calculate_expected_risk(holdings, optimal_weights)
    expected_sharpe = (expected_return - 0.04) / expected_risk if expected_risk > 0 else 0
    
    return {
        "current_portfolio": {
            "return": round(current_return, 4),
            "risk": round(current_risk, 4),
            "sharpe": round(current_sharpe, 2)
        },
        "optimized_portfolio": {
            "return": round(expected_return, 4),
            "risk": round(expected_risk, 4),
            "sharpe": round(expected_sharpe, 2)
        },
        "improvements": {
            "return_increase": round((expected_return - current_return) * 100, 2),
            "risk_reduction": round((current_risk - expected_risk) * 100, 2),
            "sharpe_improvement": round(expected_sharpe - current_sharpe, 2)
        },
        "optimal_weights": [
            {
                "symbol": holdings[i]["symbol"],
                "current": round(holdings[i]["weight"], 4),
                "optimal": round(optimal_weights[i], 4),
                "change": round(optimal_weights[i] - holdings[i]["weight"], 4)
            }
            for i in range(len(holdings))
        ],
        "rebalancing_trades": trades[:10],  # Top 10 trades
        "total_trades": len(trades),
        "total_trade_value": sum(t["value"] for t in trades),
        "risk_tolerance": risk_tolerance,
        "optimization_method": "Mean-Variance Optimization",
        "constraints": request.constraints,
        "notes": generate_optimization_notes(risk_tolerance, trades)
    }

def calculate_optimal_weights(holdings: List[dict], risk_tolerance: float) -> List[float]:
    """Calculate optimal portfolio weights based on risk tolerance"""
    # Simplified optimization - in production use proper optimization library
    weights = []
    
    for holding in holdings:
        beta = holding["beta"]
        sector = holding["sector"]
        
        # Base weight on risk tolerance and beta
        if risk_tolerance < 0.3:  # Conservative
            if beta < 1:
                weight = 0.15
            elif beta < 1.3:
                weight = 0.10
            else:
                weight = 0.05
        elif risk_tolerance < 0.7:  # Moderate
            if sector == "Technology" and beta > 1.5:
                weight = 0.08
            elif sector == "Financial":
                weight = 0.15
            else:
                weight = 0.12
        else:  # Aggressive
            if beta > 1.5:
                weight = 0.15
            else:
                weight = 0.10
    
        weights.append(weight)
    
    # Normalize weights to sum to 1
    total = sum(weights)
    return [w/total for w in weights]

def calculate_expected_return(holdings: List[dict], weights: List[float]) -> float:
    """Calculate expected portfolio return"""
    # Simplified - in production use historical returns and forward estimates
    expected_returns = []
    for holding in holdings:
        if holding["sector"] == "Technology":
            expected_returns.append(0.15)
        elif holding["sector"] == "Financial":
            expected_returns.append(0.10)
        else:
            expected_returns.append(0.08)
    
    return sum(w * r for w, r in zip(weights, expected_returns))

def calculate_expected_risk(holdings: List[dict], weights: List[float]) -> float:
    """Calculate expected portfolio risk"""
    # Simplified - in production use covariance matrix
    weighted_beta = sum(w * h["beta"] for w, h in zip(weights, holdings))
    return weighted_beta * 0.15  # Approximate volatility

def generate_trade_reason(holding: dict, weight_diff: float, risk_tolerance: float) -> str:
    """Generate reason for trade recommendation"""
    if weight_diff > 0:
        if holding["beta"] < 1 and risk_tolerance < 0.3:
            return "Increase allocation to low-beta defensive position"
        elif holding["sector"] == "Financial":
            return "Increase financial sector for interest rate environment"
        else:
            return "Rebalance to target allocation"
    else:
        if holding["beta"] > 1.5 and risk_tolerance < 0.5:
            return "Reduce high-beta position to lower portfolio risk"
        elif holding["weight"] > 0.2:
            return "Reduce concentration risk"
        else:
            return "Trim overweight position"

def generate_optimization_notes(risk_tolerance: float, trades: List[dict]) -> List[str]:
    """Generate notes about optimization"""
    notes = []
    
    if risk_tolerance < 0.3:
        notes.append("Conservative optimization prioritizes capital preservation")
    elif risk_tolerance > 0.7:
        notes.append("Aggressive optimization seeks maximum returns")
    
    if len(trades) > 5:
        notes.append(f"Consider implementing {len(trades)} trades over 2-3 days to minimize market impact")
    
    total_sells = sum(t["value"] for t in trades if t["action"] == "SELL")
    if total_sells > 50000:
        notes.append("Large sell orders may trigger tax consequences - consult tax advisor")
    
    return notes

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await init_db()
    logger.info("Enhanced server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
    logger.info("Enhanced server shutdown")

@app.get("/")
async def root():
    """Root endpoint - serve HTML"""
    # Try to read full UI from file, fall back to embedded if not found
    try:
        with open("full_ui.html", "r") as f:
            return HTMLResponse(content=f.read())
    except:
        # Fallback to embedded UI
        return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DawsOS Portfolio Intelligence</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .header p { color: #666; font-size: 1.1rem; }
        .auth-section {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            max-width: 400px;
            margin: 2rem auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .auth-section h2 { margin-bottom: 1.5rem; color: #333; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #555;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .error-message, .success-message {
            margin-top: 1rem;
            text-align: center;
            font-size: 0.9rem;
        }
        .error-message { color: #ef4444; }
        .success-message { color: #10b981; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DawsOS Portfolio Intelligence</h1>
            <p>Advanced AI-Powered Portfolio Management Platform</p>
        </div>
        <div class="auth-section" id="authSection">
            <h2>Login to Your Account</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>Email Address</label>
                    <input type="email" id="email" value="michael@dawsos.com" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" placeholder="Enter password (admin123)" required>
                </div>
                <button type="submit" class="btn">Login</button>
                <div class="error-message" id="errorMessage"></div>
                <div class="success-message" id="successMessage"></div>
            </form>
        </div>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('auth_token', data.access_token);
                    document.getElementById('successMessage').textContent = 'Login successful! Redirecting...';
                    setTimeout(() => window.location.reload(), 500);
                } else {
                    document.getElementById('errorMessage').textContent = 'Invalid credentials. Password: admin123';
                }
            } catch (error) {
                document.getElementById('errorMessage').textContent = 'Connection error: ' + error.message;
            }
        });
    </script>
</body>
</html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_pool is not None,
            "claude_ai": ANTHROPIC_API_KEY is not None,
            "alerts": len(ACTIVE_ALERTS),
            "macro_regime": True,
            "optimization": True
        }
    }

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User login endpoint - database only"""
    logger.info(f"Login attempt for: {request.email}")
    
    # Check if mock data mode is enabled
    if USE_MOCK_DATA:
        user_data = USERS_DB.get(request.email)
        
        if not user_data:
            logger.warning(f"User not found in mock data: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(request.password, user_data["password"]):
            logger.warning(f"Invalid password for: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_jwt_token(user_data["id"], user_data["email"], user_data["role"])
        
        logger.info(f"Login successful (mock mode) for: {request.email}")
        
        return LoginResponse(
            access_token=token,
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "id": user_data["id"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
        )
    
    # Database authentication (production mode)
    if not db_pool:
        logger.error("Database connection not available")
        raise HTTPException(
            status_code=503, 
            detail="Authentication service temporarily unavailable. Please try again later."
        )
    
    try:
        async with db_pool.acquire() as conn:
            # Query user from database
            query = """
                SELECT id, email, password_hash, role 
                FROM users 
                WHERE email = $1 AND is_active = true
            """
            user_data = await conn.fetchrow(query, request.email)
            
            if not user_data:
                logger.warning(f"User not found in database: {request.email}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Verify password
            if not verify_password(request.password, user_data["password_hash"]):
                logger.warning(f"Invalid password for: {request.email}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Create token with database user data
            token = create_jwt_token(
                str(user_data["id"]), 
                user_data["email"], 
                user_data["role"]
            )
            
            logger.info(f"Login successful from database for: {request.email}")
            
            return LoginResponse(
                access_token=token,
                expires_in=JWT_EXPIRATION_HOURS * 3600,
                user={
                    "id": str(user_data["id"]),
                    "email": user_data["email"],
                    "role": user_data["role"]
                }
            )
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        logger.error(f"Database error during login: {e}")
        raise HTTPException(
            status_code=503,
            detail="Authentication service temporarily unavailable. Please try again later."
        )

@app.post("/auth/logout")
async def logout(request: Request):
    """Logout endpoint"""
    # In a real app, you might invalidate the token in a blacklist
    return {"message": "Logged out successfully"}

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
        # Use database only - no fallback
        user_email = inputs.get("email", "michael@dawsos.com")
        
        if USE_MOCK_DATA:
            result = calculate_portfolio_metrics()
        else:
            result = await calculate_portfolio_metrics_from_db(user_email)
        
        return {
            "result": result,
            "status": "success"
        }
    
    elif pattern == "portfolio_scenario_analysis":
        scenario = inputs.get("scenario", "market_crash")
        
        if USE_MOCK_DATA:
            return {
                "result": calculate_scenario_impact(scenario),
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=501,
                detail="Scenario analysis not yet implemented for production mode"
            )
    
    elif pattern == "macro_regime_detection":
        return {
            "result": await detect_macro_regime(),
            "status": "success"
        }
    
    elif pattern == "macro_cycles_overview":
        # Get macro data with all 4 cycles
        macro_data = await detect_macro_regime()
        
        # Transform to match UI expectations with actual Dalio cycle data
        result = {
            "regime": macro_data["current_regime"],
            "risk_level": macro_data["risk_level"],
            "indicators": {
                "gdp_growth": macro_data["indicators"].get("gdp_growth", 0),
                "inflation": macro_data["indicators"].get("inflation", 0), 
                "unemployment": macro_data["indicators"].get("unemployment", 0),
                "interest_rate": macro_data["indicators"].get("interest_rate", 0),
                "vix": macro_data["indicators"].get("vix", 0),
                "dollar_index": macro_data["indicators"].get("dollar_index", 0)
            },
            "recommendations": macro_data["recommendations"],
            "trend": macro_data.get("trend", "Complex multi-cycle dynamics"),
            "portfolio_risk_assessment": macro_data.get("portfolio_risk_assessment", {}),
            
            # Short-term debt cycle (5-8 years)
            "stdc_phase": macro_data.get("stdc_phase", "UNKNOWN"),
            "stdc_metrics": macro_data.get("stdc_metrics", {}),
            
            # Long-term debt cycle (75-100 years)  
            "ltdc_phase": macro_data.get("ltdc_phase", "UNKNOWN"),
            "debt_metrics": macro_data.get("debt_metrics", {}),
            "deleveraging_score": macro_data.get("deleveraging_score"),
            
            # Empire cycle (250 years)
            "empire_phase": macro_data.get("empire_phase", "UNKNOWN"),
            "empire_score": macro_data.get("empire_score", 0),
            "empire_indicators": macro_data.get("empire_indicators", {}),
            
            # Internal order/disorder cycle
            "internal_stage": macro_data.get("internal_stage", 0),
            "internal_stage_name": macro_data.get("internal_stage_name", "UNKNOWN"),
            "civil_war_probability": macro_data.get("civil_war_probability", 0),
            "political_polarization": macro_data.get("political_polarization", 0),
            
            # Additional metrics
            "wealth_gap": macro_data.get("wealth_gap", 0.48),
            
            # Deleveraging levers only if in depression phase
            "deleveraging_levers": {
                "austerity": "20%",
                "defaults": "15%",
                "redistribution": "25%",
                "printing": "40%"
            } if macro_data.get("ltdc_phase") == "DEPRESSION" else None
        }
        
        return {
            "result": result,
            "status": "success"
        }
    
    elif pattern == "portfolio_transactions":
        # Get transaction data with pagination
        page = inputs.get("page", 1)
        page_size = inputs.get("page_size", 20)
        return {
            "result": get_portfolio_transactions(page, page_size),
            "status": "success"
        }
    
    else:
        return {
            "result": {"message": f"Pattern {pattern} executed"},
            "status": "success"
        }

@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio data with real-time calculations"""
    if USE_MOCK_DATA:
        return calculate_portfolio_metrics()
    
    # Production mode - database only
    user_email = "michael@dawsos.com"  # TODO: Get from JWT token
    try:
        return await calculate_portfolio_metrics_from_db(user_email)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(
            status_code=503,
            detail="Portfolio service temporarily unavailable. Please try again later."
        )

@app.post("/api/scenario")
async def analyze_scenario(scenario: str = "market_crash"):
    """Analyze scenario impact on portfolio"""
    if USE_MOCK_DATA:
        return calculate_scenario_impact(scenario)
    
    # In production, this should use real portfolio data
    # For now, return a service unavailable error
    raise HTTPException(
        status_code=501,
        detail="Scenario analysis not yet implemented for production mode. Please set USE_MOCK_DATA=true for demo."
    )

@app.get("/api/macro")
async def get_macro_regime():
    """Get current macro regime and analysis"""
    return await detect_macro_regime()

@app.get("/api/alerts")
async def get_alerts():
    """Get current alerts from database"""
    user_email = "michael@dawsos.com"  # TODO: Get from JWT token
    
    if USE_MOCK_DATA:
        return check_alerts()
    
    if not db_pool:
        logger.error("Database connection not available for alerts")
        raise HTTPException(
            status_code=503,
            detail="Alerts service temporarily unavailable. Please try again later."
        )
    
    try:
        alerts = await get_user_alerts(user_email)
        
        if not alerts:
            return []  # Return empty list instead of error
        
        # Convert database rows to appropriate format
        formatted_alerts = []
        for row in alerts:
            # Handle condition_json which can be a dict or string
            condition_data = row["condition_json"]
            if isinstance(condition_data, str):
                try:
                    condition_data = json.loads(condition_data) if condition_data else {}
                except:
                    condition_data = {}
            elif not condition_data:
                condition_data = {}
                
            formatted_alerts.append({
                "id": str(row["id"]),
                "type": condition_data.get("type", "price"),
                "condition": condition_data.get("condition", "above"),
                "symbol": condition_data.get("symbol"),
                "threshold": condition_data.get("threshold", 0),
                "message": condition_data.get("message", ""),
                "active": row["is_active"],
                "last_triggered": row["last_fired_at"].isoformat() if row["last_fired_at"] else None,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            })
        
        return formatted_alerts
        
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(
            status_code=503,
            detail="Alerts service temporarily unavailable. Please try again later."
        )

@app.post("/api/alerts")
async def create_new_alert(request: Request):
    """Create a new alert"""
    alert_data = await request.json()
    return create_alert(alert_data)

@app.delete("/api/alerts/{alert_id}")
async def delete_alert_endpoint(alert_id: str):
    """Delete an alert by ID"""
    if delete_alert(alert_id):
        return {"status": "success", "message": f"Alert {alert_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Alert not found")

@app.put("/api/alerts/{alert_id}")
async def update_alert_endpoint(alert_id: str, request: Request):
    """Update an alert (toggle active status or modify settings)"""
    updates = await request.json()
    updated_alert = update_alert(alert_id, updates)
    if updated_alert:
        return updated_alert
    else:
        raise HTTPException(status_code=404, detail="Alert not found")

@app.post("/api/ai/analyze")
async def ai_analysis(request: AIAnalysisRequest):
    """Analyze portfolio with Claude AI"""
    return await analyze_with_claude(request.query, request.context)

@app.post("/api/optimize")
async def optimize(request: OptimizationRequest):
    """Generate portfolio optimization recommendations"""
    return optimize_portfolio(request)

@app.get("/api/holdings")
async def get_holdings():
    """Get detailed holdings information from database"""
    # Default to michael@dawsos.com for now (in production, get from JWT)
    user_email = "michael@dawsos.com"
    
    if db_pool:
        portfolio = await calculate_portfolio_metrics_from_db(user_email)
    else:
        portfolio = calculate_portfolio_metrics()
    
    return {"holdings": portfolio["holdings"]}

@app.get("/api/metrics")
async def get_metrics():
    """Get portfolio metrics"""
    if USE_MOCK_DATA:
        portfolio = calculate_portfolio_metrics()
        return {
            "total_value": portfolio["total_value"],
            "returns": {
                "1d": portfolio["returns_1d"],
                "1w": portfolio["returns_1w"],
                "1m": portfolio["returns_1m"],
                "ytd": portfolio["returns_ytd"]
            },
            "risk_metrics": {
                "beta": portfolio["portfolio_beta"],
                "volatility": portfolio["portfolio_volatility"],
                "sharpe_ratio": portfolio["sharpe_ratio"],
                "var_95": portfolio["var_95"]
            }
        }
    
    # Production mode - database only
    user_email = "michael@dawsos.com"  # TODO: Get from JWT token
    try:
        portfolio = await calculate_portfolio_metrics_from_db(user_email)
        return {
            "total_value": portfolio["total_value"],
            "returns": {
                "1d": portfolio["returns_1d"],
                "1w": portfolio["returns_1w"],
                "1m": portfolio["returns_1m"],
                "ytd": portfolio["returns_ytd"]
            },
            "risk_metrics": {
                "beta": portfolio["portfolio_beta"],
                "volatility": portfolio["portfolio_volatility"],
                "sharpe_ratio": portfolio["sharpe_ratio"],
                "var_95": portfolio["var_95"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(
            status_code=503,
            detail="Metrics service temporarily unavailable. Please try again later."
        )

@app.get("/api/transactions")
async def get_transactions(page: int = 1, page_size: int = 20):
    """Get transaction history with pagination from database"""
    user_email = "michael@dawsos.com"  # TODO: Get from JWT token
    
    # Use the unified get_portfolio_transactions function
    try:
        return await get_portfolio_transactions(user_email, page, page_size)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=503,
            detail="Transaction service temporarily unavailable. Please try again later."
        )

@app.get("/api/test-fred")
async def test_fred():
    """Test FRED API integration"""
    fred_client = FREDClient()
    if not fred_client.api_key:
        return {"status": "error", "message": "FRED API key not configured"}
    
    try:
        data = await fred_client.fetch_all_indicators()
        if data:
            return {"status": "success", "indicators": data, "count": len(data)}
        else:
            return {"status": "error", "message": "No data returned from FRED API"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/test-macro-cycles")
async def test_macro_cycles():
    """Test comprehensive macro analysis with all 4 Dalio cycles and enhanced data fetchers"""
    try:
        # Get the complete macro regime detection with all 4 cycles
        macro_data = await detect_macro_regime()
        
        # Add leading indicators analysis
        cycles_context = {
            "empire_phase": macro_data.get("empire_phase"),
            "ltdc_phase": macro_data.get("ltdc_phase"),
            "stdc_phase": macro_data.get("stdc_phase"),
            "internal_stage": macro_data.get("internal_stage")
        }
        leading_indicators = identify_leading_indicators(macro_data.get("indicators", {}), cycles_context)
        
        return {
            "status": "success",
            "data": macro_data,
            "cycles_summary": {
                "short_term_debt_cycle": {
                    "phase": macro_data.get("stdc_phase"),
                    "metrics": macro_data.get("stdc_metrics", {})
                },
                "long_term_debt_cycle": {
                    "phase": macro_data.get("ltdc_phase"),
                    "metrics": macro_data.get("debt_metrics", {}),
                    "deleveraging_score": macro_data.get("deleveraging_score")
                },
                "empire_cycle": {
                    "phase": macro_data.get("empire_phase"),
                    "score": macro_data.get("empire_score"),
                    "indicators": macro_data.get("empire_indicators", {}),
                    "real_data": macro_data.get("empire_real_data", {})
                },
                "internal_order_cycle": {
                    "stage": macro_data.get("internal_stage"),
                    "stage_name": macro_data.get("internal_stage_name"),
                    "civil_war_probability": macro_data.get("civil_war_probability"),
                    "polarization": macro_data.get("political_polarization"),
                    "real_data": macro_data.get("internal_real_data", {})
                }
            },
            "risk_assessment": {
                "overall_level": macro_data.get("risk_level"),
                "wealth_gap": macro_data.get("wealth_gap"),
                "recommendations": macro_data.get("recommendations", [])
            },
            "leading_indicators": leading_indicators,
            "data_validation": {
                "empire_data_fetched": any(key in macro_data.get("indicators", {}) for key in 
                    ["education_score", "innovation_score", "competitiveness_score", "economic_output_share"]),
                "internal_data_fetched": any(key in macro_data.get("indicators", {}) for key in 
                    ["wealth_gap", "political_polarization", "social_unrest", "institutional_trust"]),
                "gini_coefficient": macro_data.get("indicators", {}).get("wealth_gap", "Not fetched"),
                "total_indicators": len(macro_data.get("indicators", {}))
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": str(e.__traceback__)}

@app.get("/api/export/pdf")
async def export_portfolio_pdf():
    """Export portfolio summary as PDF (simplified HTML version)"""
    if USE_MOCK_DATA:
        portfolio = calculate_portfolio_metrics()
    else:
        user_email = "michael@dawsos.com"  # TODO: Get from JWT token
        try:
            portfolio = await calculate_portfolio_metrics_from_db(user_email)
        except Exception as e:
            logger.error(f"Error generating PDF export: {e}")
            raise HTTPException(
                status_code=503,
                detail="Export service temporarily unavailable. Please try again later."
            )
    
    # Generate simple HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Portfolio Report - DawsOS</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #667eea; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background: #f8f9fa; }}
            .header {{ border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
            .summary {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>DawsOS Portfolio Report</h1>
            <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
        </div>
        
        <div class="summary">
            <h2>Portfolio Summary</h2>
            <p><strong>Total Value:</strong> ${portfolio['total_value']:,.2f}</p>
            <p><strong>Total Gain:</strong> ${portfolio['unrealized_pnl']:,.2f}</p>
            <p><strong>YTD Return:</strong> {portfolio['returns_ytd']*100:.2f}%</p>
            <p><strong>Sharpe Ratio:</strong> {portfolio['sharpe_ratio']:.2f}</p>
        </div>
        
        <h2>Holdings</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Value</th>
                    <th>Weight</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'''
                <tr>
                    <td>{h["symbol"]}</td>
                    <td>{h["quantity"]}</td>
                    <td>${h["price"]:.2f}</td>
                    <td>${h["value"]:,.2f}</td>
                    <td>{h["weight"]*100:.1f}%</td>
                </tr>
                ''' for h in portfolio["holdings"]])}
            </tbody>
        </table>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
            <p>Generated by DawsOS Portfolio Intelligence Platform</p>
        </div>
    </body>
    </html>
    """
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=portfolio_report_{datetime.utcnow().strftime('%Y%m%d')}.html"
        }
    )

@app.get("/api/export/csv/holdings")
async def export_holdings_csv():
    """Export holdings data as CSV"""
    # Export holdings
    if USE_MOCK_DATA:
        portfolio = calculate_portfolio_metrics()
    else:
        user_email = "michael@dawsos.com"  # TODO: Get from JWT token
        try:
            portfolio = await calculate_portfolio_metrics_from_db(user_email)
        except Exception as e:
            logger.error(f"Error fetching portfolio for export: {e}")
            raise HTTPException(
                status_code=503,
                detail="Export service temporarily unavailable. Please try again later."
            )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Symbol", "Quantity", "Price", "Value", "Weight", "Sector", "Beta"])
    
    # Write data
    for h in portfolio["holdings"]:
        writer.writerow([
            h["symbol"],
            h["quantity"],
            f"${h['price']:.2f}",
            f"${h['value']:.2f}",
            f"{h['weight']*100:.2f}%",
            h.get("sector", "Unknown"),
            h.get("beta", 1.0)
        ])
    
    csv_content = output.getvalue()
    filename = f"holdings_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/api/export/csv")
async def export_portfolio_csv(export_type: str = "holdings"):
    """Export portfolio data as CSV"""
    
    if export_type == "transactions":
        # Export transactions
        user_email = "michael@dawsos.com"  # TODO: Get from JWT token
        try:
            transaction_data = await get_portfolio_transactions(user_email, 1, 1000)
            transactions = transaction_data["transactions"]  # Get all transactions
        except Exception as e:
            logger.error(f"Error fetching transactions for export: {e}")
            raise HTTPException(
                status_code=503,
                detail="Export service temporarily unavailable. Please try again later."
            )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Date", "Type", "Symbol", "Shares", "Price", "Amount", "Realized Gain"])
        
        # Write data
        for t in transactions:
            writer.writerow([
                t["date"],
                t["type"],
                t["symbol"],
                t["shares"],
                f"${t['price']:.2f}",
                f"${t['amount']:.2f}",
                f"${t['realized_gain']:.2f}"
            ])
        
        csv_content = output.getvalue()
        filename = f"transactions_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        
    else:
        # Export holdings (default)
        if USE_MOCK_DATA:
            portfolio = calculate_portfolio_metrics()
        else:
            user_email = "michael@dawsos.com"  # TODO: Get from JWT token
            try:
                portfolio = await calculate_portfolio_metrics_from_db(user_email)
            except Exception as e:
                logger.error(f"Error fetching portfolio for export: {e}")
                raise HTTPException(
                    status_code=503,
                    detail="Export service temporarily unavailable. Please try again later."
                )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Symbol", "Quantity", "Price", "Value", "Weight", "Sector", "Beta"])
        
        # Write data
        for h in portfolio["holdings"]:
            writer.writerow([
                h["symbol"],
                h["quantity"],
                f"${h['price']:.2f}",
                f"${h['value']:.2f}",
                f"{h['weight']*100:.2f}%",
                h["sector"],
                h["beta"]
            ])
        
        csv_content = output.getvalue()
        filename = f"holdings_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

if __name__ == "__main__":
    import sys
    
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    
    logger.info(f"Starting Enhanced DawsOS Server on port {port}...")
    logger.info(f"Frontend: http://localhost:{port}/")
    logger.info(f"API Docs: http://localhost:{port}/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")