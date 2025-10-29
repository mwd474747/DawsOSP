#!/usr/bin/env python3
"""
Combined DawsOS Server - Serves both frontend and API on port 5000
This solves the Replit networking issues between different ports
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import hashlib
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import jwt
import asyncpg
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DawsOS Combined Server",
    description="Portfolio Intelligence Platform",
    version="4.0.0"
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

# Database connection pool
db_pool = None

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

# Mock Data Generators
def get_portfolio_data() -> dict:
    """Generate portfolio data"""
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
    """Generate macro economic data"""
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

# HTML Content
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DawsOS Portfolio Intelligence</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

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

        .header p {
            color: #666;
            font-size: 1.1rem;
        }

        .auth-section {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            max-width: 400px;
            margin: 2rem auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .auth-section h2 {
            margin-bottom: 1.5rem;
            color: #333;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

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

        .dashboard {
            display: none;
        }

        .dashboard.active {
            display: block;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }

        .stat-label {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }

        .stat-value.positive {
            color: #10b981;
        }

        .stat-value.negative {
            color: #ef4444;
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s;
        }

        .feature-card:hover::before {
            transform: scaleX(1);
        }

        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }

        .feature-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        .feature-card h3 {
            margin-bottom: 0.5rem;
            color: #333;
        }

        .feature-card p {
            color: #666;
            line-height: 1.6;
        }

        .holdings-table {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-top: 2rem;
        }

        .holdings-table h3 {
            margin-bottom: 1.5rem;
            color: #333;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
        }

        .table th {
            text-align: left;
            padding: 1rem;
            border-bottom: 2px solid #e0e0e0;
            color: #666;
            font-weight: 600;
        }

        .table td {
            padding: 1rem;
            border-bottom: 1px solid #f0f0f0;
        }

        .table tr:hover {
            background: rgba(102, 126, 234, 0.05);
        }

        .scenario-section {
            display: none;
            background: white;
            border-radius: 20px;
            padding: 2rem;
            margin-top: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .scenario-section.active {
            display: block;
        }

        .scenario-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }

        .scenario-card {
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 1.5rem;
            transition: all 0.3s;
            cursor: pointer;
        }

        .scenario-card:hover {
            border-color: #667eea;
            background: rgba(102, 126, 234, 0.05);
        }

        .logout-btn {
            position: absolute;
            top: 2rem;
            right: 2rem;
            padding: 0.75rem 1.5rem;
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid white;
            color: white;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }

        .logout-btn:hover {
            background: white;
            color: #764ba2;
        }

        .error-message {
            color: #ef4444;
            margin-top: 1rem;
            text-align: center;
            font-size: 0.9rem;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading-pulse {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DawsOS Portfolio Intelligence</h1>
            <p>Advanced AI-Powered Portfolio Management Platform</p>
        </div>

        <button class="logout-btn" id="logoutBtn" style="display: none;">Logout</button>

        <div class="auth-section" id="authSection">
            <h2>Login to Your Account</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>Email Address</label>
                    <input type="email" id="email" value="michael@dawsos.com" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" placeholder="Enter password" required>
                </div>
                <button type="submit" class="btn">Login</button>
                <div class="error-message" id="errorMessage"></div>
            </form>
        </div>

        <div class="dashboard" id="dashboard">
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="stat-label">Total Portfolio Value</div>
                    <div class="stat-value" id="totalValue">Loading...</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Day Return</div>
                    <div class="stat-value" id="dayReturn">Loading...</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">YTD Return</div>
                    <div class="stat-value" id="ytdReturn">Loading...</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Risk Score</div>
                    <div class="stat-value" id="riskScore">Loading...</div>
                </div>
            </div>

            <div class="feature-grid">
                <div class="feature-card" onclick="showScenarios()">
                    <div class="feature-icon" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white;">📊</div>
                    <h3>Portfolio Analysis</h3>
                    <p>Deep dive into your portfolio performance with AI-powered insights and recommendations.</p>
                </div>
                <div class="feature-card" onclick="showScenarios()">
                    <div class="feature-icon" style="background: linear-gradient(135deg, #10b981, #059669); color: white;">🎯</div>
                    <h3>Scenario Planning</h3>
                    <p>Test your portfolio against market scenarios and stress conditions to understand risk exposure.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white;">🌍</div>
                    <h3>Macro Insights</h3>
                    <p>Track economic indicators and market regimes to make informed investment decisions.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon" style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white;">🔔</div>
                    <h3>Smart Alerts</h3>
                    <p>Set up intelligent alerts for price movements, risk thresholds, and market conditions.</p>
                </div>
            </div>

            <div class="holdings-table" id="holdingsSection">
                <h3>Portfolio Holdings</h3>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Quantity</th>
                            <th>Value</th>
                            <th>Weight</th>
                            <th>Daily Change</th>
                        </tr>
                    </thead>
                    <tbody id="holdingsBody">
                        <tr>
                            <td colspan="5" class="loading">Loading holdings...</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="scenario-section" id="scenarioSection">
                <h3>Scenario Analysis</h3>
                <p style="color: #666; margin-bottom: 1rem;">Select a scenario to see its impact on your portfolio</p>
                <div class="scenario-grid">
                    <div class="scenario-card" onclick="runScenario('market_crash')">
                        <h4>Market Crash (-20%)</h4>
                        <p>Simulate a severe market downturn</p>
                    </div>
                    <div class="scenario-card" onclick="runScenario('interest_rate')">
                        <h4>Interest Rate Hike</h4>
                        <p>Impact of rising interest rates</p>
                    </div>
                    <div class="scenario-card" onclick="runScenario('inflation')">
                        <h4>High Inflation</h4>
                        <p>Effects of sustained inflation</p>
                    </div>
                </div>
                <div id="scenarioResults" style="margin-top: 2rem;"></div>
            </div>
        </div>
    </div>

    <script>
        let authToken = null;
        // API is on same origin since we're serving both from same server
        const API_BASE = '';

        // Check if already logged in
        if (localStorage.getItem('auth_token')) {
            authToken = localStorage.getItem('auth_token');
            showDashboard();
        }

        // Login form handler
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (response.ok) {
                    const data = await response.json();
                    authToken = data.access_token;
                    localStorage.setItem('auth_token', authToken);
                    document.getElementById('errorMessage').textContent = '';
                    showDashboard();
                } else {
                    document.getElementById('errorMessage').textContent = 'Invalid credentials. Password: admin123';
                }
            } catch (error) {
                document.getElementById('errorMessage').textContent = 'Connection error: ' + error.message;
            }
        });

        // Logout handler
        document.getElementById('logoutBtn').addEventListener('click', () => {
            localStorage.removeItem('auth_token');
            authToken = null;
            document.getElementById('authSection').style.display = 'block';
            document.getElementById('dashboard').classList.remove('active');
            document.getElementById('logoutBtn').style.display = 'none';
        });

        // Show dashboard
        async function showDashboard() {
            document.getElementById('authSection').style.display = 'none';
            document.getElementById('dashboard').classList.add('active');
            document.getElementById('logoutBtn').style.display = 'block';
            
            await loadPortfolioData();
        }

        // Load portfolio data
        async function loadPortfolioData() {
            try {
                const response = await fetch(`${API_BASE}/execute`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        pattern: 'portfolio_overview',
                        inputs: {}
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    const portfolio = data.result;
                    
                    // Update stats
                    document.getElementById('totalValue').textContent = `$${portfolio.total_value.toLocaleString()}`;
                    document.getElementById('dayReturn').textContent = `${(portfolio.returns_1d * 100).toFixed(2)}%`;
                    document.getElementById('dayReturn').className = portfolio.returns_1d >= 0 ? 'stat-value positive' : 'stat-value negative';
                    document.getElementById('ytdReturn').textContent = `${(portfolio.returns_ytd * 100).toFixed(2)}%`;
                    document.getElementById('ytdReturn').className = portfolio.returns_ytd >= 0 ? 'stat-value positive' : 'stat-value negative';
                    document.getElementById('riskScore').textContent = `${(portfolio.risk_score * 100).toFixed(0)}%`;

                    // Update holdings
                    if (portfolio.holdings) {
                        const holdingsBody = document.getElementById('holdingsBody');
                        holdingsBody.innerHTML = portfolio.holdings.map(h => `
                            <tr>
                                <td><strong>${h.symbol}</strong></td>
                                <td>${h.quantity}</td>
                                <td>$${h.value.toLocaleString()}</td>
                                <td>${(h.weight * 100).toFixed(1)}%</td>
                                <td class="${h.change >= 0 ? 'positive' : 'negative'}">
                                    ${h.change >= 0 ? '+' : ''}${(h.change * 100).toFixed(2)}%
                                </td>
                            </tr>
                        `).join('');
                    }
                }
            } catch (error) {
                console.error('Error loading portfolio data:', error);
            }
        }

        // Show scenarios
        function showScenarios() {
            const scenarioSection = document.getElementById('scenarioSection');
            scenarioSection.classList.toggle('active');
            if (scenarioSection.classList.contains('active')) {
                scenarioSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        // Run scenario
        async function runScenario(scenario) {
            const resultsDiv = document.getElementById('scenarioResults');
            resultsDiv.innerHTML = '<div class="loading loading-pulse">Running scenario analysis...</div>';
            
            try {
                const response = await fetch(`${API_BASE}/execute`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        pattern: 'portfolio_scenario_analysis',
                        inputs: { scenario }
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    const result = data.result;
                    
                    resultsDiv.innerHTML = `
                        <div style="background: rgba(102, 126, 234, 0.1); border-radius: 15px; padding: 1.5rem;">
                            <h4 style="margin-bottom: 1rem;">Scenario Results: ${result.scenario_name}</h4>
                            <p style="margin-bottom: 1rem;">${result.description}</p>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                                <div>
                                    <div style="color: #666; font-size: 0.9rem;">Expected Impact</div>
                                    <div style="font-size: 1.5rem; font-weight: bold; color: ${result.portfolio_impact < 0 ? '#ef4444' : '#10b981'}">
                                        ${result.portfolio_impact > 0 ? '+' : ''}${result.portfolio_impact}%
                                    </div>
                                </div>
                                <div>
                                    <div style="color: #666; font-size: 0.9rem;">Risk Level</div>
                                    <div style="font-size: 1.5rem; font-weight: bold; color: ${result.risk_level === 'High' ? '#ef4444' : '#f59e0b'}">
                                        ${result.risk_level}
                                    </div>
                                </div>
                                <div>
                                    <div style="color: #666; font-size: 0.9rem;">Confidence</div>
                                    <div style="font-size: 1.5rem; font-weight: bold; color: #667eea">
                                        ${result.confidence}%
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e0e0e0;">
                                <strong>Recommendations:</strong>
                                <ul style="margin-top: 0.5rem; padding-left: 1.5rem; color: #666;">
                                    ${result.recommendations.map(r => `<li>${r}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = '<div class="error-message">Failed to run scenario analysis. Please try again.</div>';
                }
            } catch (error) {
                resultsDiv.innerHTML = '<div class="error-message">Error running scenario. Please check your connection.</div>';
            }
        }
    </script>
</body>
</html>"""

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await init_db()
    logger.info("Combined server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
    logger.info("Combined server shutdown")

# Serve HTML at root
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    return HTML_CONTENT

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
    logger.info("Starting DawsOS Combined Server on port 5000...")
    logger.info("Frontend: http://localhost:5000/")
    logger.info("API: http://localhost:5000/health")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")