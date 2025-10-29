#!/usr/bin/env python3
"""
Enhanced DawsOS Server - Comprehensive Portfolio Management System
Version 5.0.0 - Complete Feature Implementation
"""

import os
import logging
import math
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

# Macro Regime Detection
async def detect_macro_regime() -> dict:
    """Implement macro regime detection logic using database or environment variables"""
    # Try to fetch macro indicators from database or environment
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
            "consumer_confidence": 68.0
        }
    else:
        # Production mode - try database first, then environment variables
        if db_pool:
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
                    
            except Exception as e:
                logger.warning(f"Could not fetch macro indicators from database: {e}")
        
        # If no database data, try environment variables as fallback
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
                "consumer_confidence": float(os.getenv("MACRO_CONSUMER_CONFIDENCE", "70.0"))
            }
    
    # Detect regime based on indicators
    regime = "Unknown"
    risk_level = "Medium"
    
    if indicators["gdp_growth"] > 3 and indicators["inflation"] < 2.5:
        regime = "Goldilocks"
        risk_level = "Low"
    elif indicators["gdp_growth"] > 2 and indicators["inflation"] > 3:
        regime = "Late Cycle Expansion"
        risk_level = "Medium-High"
    elif indicators["gdp_growth"] < 1 and indicators["inflation"] > 3:
        regime = "Stagflation"
        risk_level = "High"
    elif indicators["gdp_growth"] < 0:
        regime = "Recession"
        risk_level = "High"
    elif indicators["yield_curve"] < 0 and indicators["pmi"] < 50:
        regime = "Pre-Recession"
        risk_level = "High"
    else:
        regime = "Mid Cycle"
        risk_level = "Medium"
    
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
    
    recommendations = generate_macro_recommendations(regime, indicators, portfolio)
    
    # Assess portfolio risk in current regime
    portfolio_risk_assessment = assess_portfolio_risk(portfolio, regime, indicators)
    
    return {
        "current_regime": regime,
        "indicators": indicators,
        "risk_level": risk_level,
        "trend": "Deteriorating" if indicators["pmi"] < 50 else "Improving" if indicators["pmi"] > 52 else "Neutral",
        "regime_probability": {
            regime: 0.65,
            "Alternative": 0.35
        },
        "portfolio_risk_assessment": portfolio_risk_assessment,
        "recommendations": recommendations,
        "next_review": "Monthly",
        "key_risks": identify_key_risks(indicators),
        "opportunities": identify_opportunities(regime, indicators)
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
        # Get macro data and transform for UI
        macro_data = await detect_macro_regime()
        
        # Transform to match UI expectations
        result = {
            "regime": macro_data["current_regime"],  # Map current_regime to regime
            "risk_level": macro_data["risk_level"],
            "indicators": {
                "gdp_growth": macro_data["indicators"]["gdp_growth"],
                "inflation": macro_data["indicators"]["inflation"], 
                "unemployment": macro_data["indicators"]["unemployment"],
                "interest_rate": macro_data["indicators"]["interest_rate"],
                "vix": macro_data["indicators"]["vix"],
                "dollar_index": macro_data["indicators"]["dollar_index"]
            },
            "recommendations": macro_data["recommendations"],
            # Include additional useful fields
            "trend": macro_data.get("trend", "Unknown"),
            "portfolio_risk_assessment": macro_data.get("portfolio_risk_assessment", {})
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