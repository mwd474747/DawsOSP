# DawsOS Function Behavior Under Different Options

## 🎯 Overview
This document details how each system function behaves under different configuration options, particularly focusing on Mock Mode vs Production Mode, user permissions, and feature flags.

---

## 🔀 Configuration Options

### Primary Modes
1. **USE_MOCK_DATA** (true/false) - Controls data source
2. **USE_PRODUCTION_DB** (true/false) - Database connection
3. **ENABLE_AI** (true/false) - Claude AI integration
4. **DEBUG_MODE** (true/false) - Verbose logging

### User Roles
1. **ADMIN** - Full system access
2. **MANAGER** - Portfolio management
3. **USER** - Standard access
4. **VIEWER** - Read-only

---

## 📊 Core Functions Behavior

### 1. Portfolio Data Retrieval

#### Function: `calculate_portfolio_metrics()`

**Mock Mode (USE_MOCK_DATA=true)**
```python
def calculate_portfolio_metrics():
    return {
        "holdings": [
            {"symbol": "AAPL", "shares": 100, "value": 17500},
            {"symbol": "GOOGL", "shares": 50, "value": 6500},
            # ... 6 more hardcoded positions
        ],
        "total_value": 125000,
        "metrics": {
            "sharpe_ratio": 1.4,
            "beta": 1.1,
            "var_95": -5200
        }
    }
```

**Production Mode (USE_MOCK_DATA=false)**
```python
async def calculate_portfolio_metrics_from_db(user_email):
    # Query real database
    holdings = await db.query("""
        SELECT h.*, p.last_price 
        FROM holdings h 
        JOIN prices p ON h.symbol = p.symbol
        WHERE user_id = (SELECT id FROM users WHERE email = $1)
    """, user_email)
    
    # Calculate metrics from actual data
    metrics = await compute_real_metrics(holdings)
    return {"holdings": holdings, "metrics": metrics}
```

**Behavior Differences**:
| Aspect | Mock Mode | Production Mode |
|--------|-----------|-----------------|
| Data Source | Hardcoded array | PostgreSQL query |
| Holdings Count | Fixed 8 stocks | Variable (user-specific) |
| Prices | Static values | Real-time from pricing_packs |
| Metrics | Pre-calculated | Computed dynamically |
| Performance | Instant (0ms) | Query time (50-200ms) |
| Multi-currency | No | Yes (FX conversion) |

---

### 2. Scenario Analysis

#### Function: `calculate_scenario_impact(scenario)`

**Mock Mode**
```python
def calculate_scenario_impact(scenario):
    portfolio_value = 125000
    if scenario == "market_crash":
        impact = portfolio_value * -0.20  # Simple 20% loss
        return {
            "impact": impact,
            "new_value": portfolio_value + impact,
            "affected_holdings": ["All holdings affected equally"]
        }
```

**Production Mode (Currently Broken - Returns 501)**
```python
async def calculate_scenario_impact(scenario):
    # Should use ScenarioService but disconnected
    raise HTTPException(
        status_code=501,
        detail="Scenario analysis not yet implemented for production mode"
    )
```

**Intended Production Behavior (ScenarioService)**
```python
async def calculate_scenario_impact(scenario):
    # Professional multi-factor model
    service = ScenarioService()
    
    # Get factor exposures
    exposures = await service.calculate_factor_exposures(portfolio)
    
    # Apply shock based on scenario type
    shocks = {
        "market_crash": {
            "equity_factor": -0.20,
            "credit_spread": +0.03,
            "volatility": +0.50,
            "correlation": 0.8
        },
        "interest_rate": {
            "rate_factor": +0.02,
            "duration_impact": -0.15,
            "credit_spread": +0.01
        }
    }
    
    # Calculate correlated impacts
    impacts = await service.apply_correlated_shocks(
        exposures, 
        shocks[scenario],
        correlation_matrix
    )
    
    return {
        "impact": impacts.total,
        "by_factor": impacts.breakdown,
        "by_holding": impacts.holdings,
        "hedging_suggestions": impacts.hedges
    }
```

**Gap Analysis**:
- Mock: Beta-only calculation
- Production (broken): 501 error
- Intended: 9 shock types with factor models

---

### 3. Macro Regime Detection

#### Function: `detect_macro_regime()`

**Mock Mode**
```python
async def detect_macro_regime():
    # Simulated regime changes
    regimes = ["EARLY_RECOVERY", "MID_EXPANSION", "LATE_EXPANSION", "RECESSION"]
    current = random.choice(regimes)
    
    return {
        "current_regime": current,
        "indicators": {
            "gdp_growth": random.uniform(1, 4),
            "inflation": random.uniform(2, 5),
            "unemployment": random.uniform(3, 7)
        },
        "stdc_phase": "Simulated",
        "ltdc_phase": "Simulated"
    }
```

**Production Mode**
```python
async def detect_macro_regime():
    # Real FRED data
    indicators = await fetch_fred_indicators()
    
    # Z-score normalization
    z_scores = normalize_indicators(indicators)
    
    # Regime classification
    regime = classify_regime(z_scores)
    
    # Cycle analysis
    stdc = analyze_short_term_debt_cycle(indicators)
    ltdc = analyze_long_term_debt_cycle(indicators)
    empire = analyze_empire_cycle(indicators)
    internal = analyze_internal_order_cycle(indicators)
    
    return {
        "current_regime": regime,
        "regime_probabilities": probabilities,
        "indicators": indicators,
        "z_scores": z_scores,
        "stdc_phase": stdc.phase,
        "stdc_reasoning": stdc.full_chain,
        "ltdc_phase": ltdc.phase,
        "ltdc_reasoning": ltdc.full_chain,
        "empire_phase": empire.phase,
        "empire_reasoning": empire.full_chain,
        "internal_phase": internal.phase,
        "internal_reasoning": internal.full_chain
    }
```

**Key Differences**:
| Feature | Mock Mode | Production Mode |
|---------|-----------|-----------------|
| Data Source | Random values | FRED API |
| Regime Logic | Random selection | Statistical model |
| Cycle Analysis | Placeholder text | Full calculations |
| Reasoning Chain | None | Complete transparency |
| Update Frequency | Every call | Daily cache |
| Historical Data | None | 30+ years |

---

### 4. Alert Management

#### Function: `check_alerts()`

**Mock Mode**
```python
def check_alerts():
    # In-memory list
    global ACTIVE_ALERTS
    
    triggered = []
    for alert in ACTIVE_ALERTS:
        if evaluate_mock_condition(alert):
            triggered.append(alert)
    
    return triggered
```

**Production Mode**
```python
async def check_alerts():
    # Database query with cooldown
    alerts = await db.query("""
        SELECT * FROM alerts
        WHERE is_active = true
        AND (last_fired_at IS NULL 
             OR last_fired_at < NOW() - cooldown_hours * INTERVAL '1 hour')
    """)
    
    triggered = []
    for alert in alerts:
        if await evaluate_real_condition(alert):
            # Update last_fired_at
            await db.execute("""
                UPDATE alerts 
                SET last_fired_at = NOW(), fire_count = fire_count + 1
                WHERE id = $1
            """, alert.id)
            
            # Send notifications
            await send_notifications(alert)
            triggered.append(alert)
    
    return triggered
```

**Behavioral Matrix**:
| Feature | Mock | Production |
|---------|------|------------|
| Storage | Memory (volatile) | Database (persistent) |
| Cooldown | None | Enforced per alert |
| History | Lost on restart | Full audit trail |
| Notifications | Console only | Email/SMS/Webhook |
| Batch Processing | Immediate | Queued with retry |

---

### 5. AI Analysis

#### Function: `ai_analyze(query, context)`

**AI Disabled (ENABLE_AI=false)**
```python
async def ai_analyze(query, context):
    return {
        "response": "AI analysis is currently disabled. Please enable Claude integration.",
        "status": "disabled"
    }
```

**Mock Mode with AI**
```python
async def ai_analyze(query, context):
    # Limited context
    mock_context = {
        "portfolio_value": 125000,
        "holdings": 8,
        "top_holding": "AAPL"
    }
    
    response = await claude.complete(
        prompt=query,
        context=mock_context,
        max_tokens=500
    )
    
    return {"response": response, "status": "success"}
```

**Production Mode with AI**
```python
async def ai_analyze(query, context):
    # Full context assembly
    full_context = {
        "portfolio": await get_full_portfolio(user_id),
        "metrics": await get_all_metrics(user_id),
        "transactions": await get_recent_transactions(user_id),
        "macro_regime": await detect_macro_regime(),
        "alerts": await get_active_alerts(user_id),
        "risk_analysis": await calculate_risk_metrics(user_id)
    }
    
    # Enhanced prompt with full context
    enhanced_prompt = f"""
    User Query: {query}
    
    Portfolio Context:
    - Holdings: {len(full_context['portfolio']['holdings'])}
    - Value: ${full_context['portfolio']['total_value']:,.2f}
    - YTD Return: {full_context['metrics']['ytd_return']:.2%}
    - Sharpe Ratio: {full_context['metrics']['sharpe']:.2f}
    - Current Regime: {full_context['macro_regime']['current']}
    
    Provide actionable insights based on this data.
    """
    
    response = await claude.complete(
        prompt=enhanced_prompt,
        max_tokens=2000,
        temperature=0.7
    )
    
    return {
        "response": response,
        "status": "success",
        "context_used": list(full_context.keys())
    }
```

---

### 6. Portfolio Optimization

#### Function: `optimize_portfolio(risk_tolerance)`

**Mock Mode**
```python
def optimize_portfolio(risk_tolerance):
    # Simple linear adjustment
    if risk_tolerance < 0.3:
        return {
            "allocation": {"stocks": 40, "bonds": 60},
            "expected_return": 0.06,
            "expected_volatility": 0.08
        }
    elif risk_tolerance < 0.7:
        return {
            "allocation": {"stocks": 60, "bonds": 40},
            "expected_return": 0.08,
            "expected_volatility": 0.12
        }
    else:
        return {
            "allocation": {"stocks": 80, "bonds": 20},
            "expected_return": 0.10,
            "expected_volatility": 0.16
        }
```

**Production Mode**
```python
async def optimize_portfolio(risk_tolerance):
    # Get current holdings
    holdings = await get_user_holdings(user_id)
    
    # Historical returns and covariance
    returns = await get_historical_returns(holdings.symbols)
    cov_matrix = calculate_covariance(returns)
    
    # Riskfolio-lib optimization
    optimizer = riskfolio.Portfolio()
    optimizer.assets = holdings.symbols
    optimizer.returns = returns
    optimizer.cov_matrix = cov_matrix
    
    # Mean-variance optimization
    weights = optimizer.optimize(
        method='MV',
        risk_measure='std',
        risk_aversion=1 - risk_tolerance
    )
    
    # Generate rebalancing trades
    trades = calculate_rebalancing_trades(
        current_weights=holdings.weights,
        target_weights=weights
    )
    
    return {
        "current_allocation": holdings.weights,
        "optimal_allocation": weights,
        "trades_required": trades,
        "expected_return": optimizer.expected_return,
        "expected_volatility": optimizer.expected_volatility,
        "sharpe_improvement": optimizer.sharpe_delta,
        "transaction_costs": estimate_costs(trades)
    }
```

---

## 🔐 Role-Based Function Access

### Function Availability by Role

| Function | ADMIN | MANAGER | USER | VIEWER |
|----------|-------|---------|------|--------|
| View Portfolio | ✅ | ✅ | ✅ | ✅ |
| Execute Trades | ✅ | ✅ | ✅ | ❌ |
| Run Scenarios | ✅ | ✅ | ✅ | ✅ |
| Create Alerts | ✅ | ✅ | ✅ | ❌ |
| AI Analysis | ✅ | ✅ | ✅ | ✅ |
| Export Data | ✅ | ✅ | ✅ | ❌ |
| Optimize | ✅ | ✅ | ✅ | ❌ |
| System Config | ✅ | ❌ | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| View Logs | ✅ | ✅ | ❌ | ❌ |

### Permission Checks
```python
def check_permission(user_role, action):
    permissions = {
        "ADMIN": ["*"],  # All actions
        "MANAGER": ["view", "trade", "analyze", "export", "alert"],
        "USER": ["view", "trade", "analyze", "alert"],
        "VIEWER": ["view", "analyze"]
    }
    
    if user_role == "ADMIN":
        return True
    
    return action in permissions.get(user_role, [])
```

---

## 🎚️ Feature Flags Impact

### Feature Flag Configuration
```python
FEATURE_FLAGS = {
    "ENABLE_REAL_TIME_UPDATES": False,
    "ENABLE_OPTIONS_TRADING": False,
    "ENABLE_CRYPTO": False,
    "ENABLE_SOCIAL_FEATURES": False,
    "ENABLE_BACKTESTING": False,
    "ENABLE_CUSTOM_INDICATORS": False,
    "ENABLE_PAPER_TRADING": True,
    "ENABLE_MULTI_PORTFOLIO": False
}
```

### Function Behavior with Feature Flags

#### Real-Time Updates Flag
**Disabled (default)**:
- Portfolio refreshes on page load
- Prices update on manual refresh
- Alerts check every 5 minutes

**Enabled**:
- WebSocket connection established
- Live price streaming
- Instant alert notifications
- Real-time P&L updates

#### Paper Trading Flag
**Enabled (default)**:
```python
async def execute_trade(trade):
    if FEATURE_FLAGS["ENABLE_PAPER_TRADING"]:
        # Simulated execution
        return {
            "status": "simulated",
            "filled_price": trade.limit_price or current_price,
            "commission": 0  # No real costs
        }
```

**Disabled**:
```python
async def execute_trade(trade):
    # Real broker API
    broker_response = await broker_api.place_order(trade)
    return {
        "status": broker_response.status,
        "filled_price": broker_response.price,
        "commission": broker_response.fees
    }
```

---

## 🔄 State Management Differences

### Mock Mode State
```python
# Global in-memory state
MOCK_STATE = {
    "portfolio": {...},
    "alerts": [...],
    "cache": {},
    "session": {}
}

# Lost on server restart
# No persistence
# Single user only
```

### Production Mode State
```python
# Database-backed state
async def get_state(user_id, key):
    return await db.query(
        "SELECT value FROM user_state WHERE user_id = $1 AND key = $2",
        user_id, key
    )

# Persistent across restarts
# Multi-user support
# Transaction safety
```

---

## 🚀 Performance Characteristics

### Response Time Comparison

| Operation | Mock Mode | Production Mode | Production + Cache |
|-----------|-----------|-----------------|-------------------|
| Login | 10ms | 150ms | N/A |
| Portfolio Load | 5ms | 200ms | 50ms |
| Scenario Run | 20ms | 501 (broken) | 500ms (intended) |
| Macro Analysis | 50ms | 2000ms | 100ms |
| AI Query | N/A | 3000ms | 3000ms |
| Alert Check | 5ms | 100ms | 20ms |
| Optimization | 30ms | 5000ms | 1000ms |
| Export PDF | 100ms | 800ms | 300ms |

### Caching Strategy

**Mock Mode**:
- No caching needed
- All data in memory

**Production Mode**:
```python
# Redis caching layer
CACHE_TTL = {
    "portfolio": 60,      # 1 minute
    "prices": 10,         # 10 seconds
    "macro": 3600,        # 1 hour
    "metrics": 300,       # 5 minutes
    "optimization": 1800  # 30 minutes
}

async def get_cached_or_fetch(key, fetch_func, ttl):
    # Check Redis
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    
    # Fetch fresh
    data = await fetch_func()
    
    # Store in cache
    await redis.setex(key, ttl, json.dumps(data))
    
    return data
```

---

## 🔍 Debugging Behavior

### Debug Mode (DEBUG_MODE=true)

**Enhanced Logging**:
```python
if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)
    logger.debug(f"SQL Query: {query}")
    logger.debug(f"Params: {params}")
    logger.debug(f"Execution time: {elapsed_ms}ms")
    logger.debug(f"Rows returned: {len(result)}")
```

**Additional Endpoints**:
```python
if DEBUG_MODE:
    @app.get("/debug/state")
    async def get_debug_state():
        return {
            "mock_mode": USE_MOCK_DATA,
            "db_connected": db_pool is not None,
            "cache_size": len(cache),
            "active_sessions": len(sessions),
            "feature_flags": FEATURE_FLAGS
        }
    
    @app.get("/debug/clear-cache")
    async def clear_cache():
        cache.clear()
        return {"status": "Cache cleared"}
```

**Error Details**:
```python
if DEBUG_MODE:
    # Full stack traces
    raise HTTPException(
        status_code=500,
        detail={
            "error": str(e),
            "traceback": traceback.format_exc(),
            "query": query,
            "params": params
        }
    )
else:
    # User-friendly message
    raise HTTPException(
        status_code=500,
        detail="An error occurred. Please try again."
    )
```

---

## 🎭 Environment-Specific Behaviors

### Development Environment
```python
if ENVIRONMENT == "development":
    # Relaxed CORS
    CORS_ORIGINS = ["*"]
    
    # Detailed errors
    SHOW_ERRORS = True
    
    # Mock external APIs
    USE_MOCK_APIS = True
    
    # Skip email verification
    SKIP_EMAIL_VERIFY = True
```

### Production Environment
```python
if ENVIRONMENT == "production":
    # Strict CORS
    CORS_ORIGINS = ["https://dawsos.com"]
    
    # Generic errors
    SHOW_ERRORS = False
    
    # Real APIs
    USE_MOCK_APIS = False
    
    # Enforce verification
    SKIP_EMAIL_VERIFY = False
    
    # Enable monitoring
    init_sentry()
    init_prometheus()
```

---

## 🏁 Summary

The DawsOS platform exhibits significantly different behavior based on configuration:

1. **Mock Mode**: Fast, simple, demo-ready
2. **Production Mode**: Complex, accurate, partially broken
3. **Role-Based**: Different features per user type
4. **Feature Flags**: Gradual rollout capability
5. **Debug Mode**: Developer-friendly diagnostics

**Critical Gaps**:
- Scenario analysis broken in production (501 error)
- No connection between ScenarioService and API
- Missing macro-aware scenario adjustments
- No historical pattern matching

**Recommended Fixes**:
1. Connect ScenarioService to production API
2. Implement MacroAwareScenarioService
3. Build EmpiricalScenarioEngine
4. Add proper caching layer
5. Enable WebSocket for real-time updates