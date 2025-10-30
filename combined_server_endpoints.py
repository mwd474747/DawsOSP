# ============================================================================
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
            uuid4(alert_id)  # Validate UUID format
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
    """Run scenario analysis on portfolio"""
    try:
        # Check authentication
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate scenario
        valid_scenarios = ["rates_up", "rates_down", "inflation", "recession", "market_crash"]
        if scenario not in valid_scenarios:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scenario. Valid options: {', '.join(valid_scenarios)}"
            )
        
        # Get portfolio
        if USE_MOCK_DATA:
            holdings = get_mock_portfolio_holdings()
            total_value = sum(h["quantity"] * h["price"] for h in holdings)
        else:
            portfolio_data = await get_portfolio_data(user["email"])
            if not portfolio_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No portfolio found"
                )
            
            holdings = []
            total_value = 0
            for row in portfolio_data:
                value = float(row["quantity"]) * float(row["price"]) if row["price"] else 0
                holdings.append({
                    "symbol": row["symbol"],
                    "value": value,
                    "sector": row["sector"] or "Other"
                })
                total_value += value
        
        # Define scenario impacts (simplified)
        scenario_impacts = {
            "rates_up": {
                "Technology": -0.08,
                "Financial": 0.03,
                "Consumer": -0.05,
                "Automotive": -0.10,
                "Other": -0.03
            },
            "rates_down": {
                "Technology": 0.10,
                "Financial": -0.04,
                "Consumer": 0.05,
                "Automotive": 0.08,
                "Other": 0.03
            },
            "inflation": {
                "Technology": -0.06,
                "Financial": 0.02,
                "Consumer": -0.08,
                "Automotive": -0.07,
                "Other": -0.05
            },
            "recession": {
                "Technology": -0.15,
                "Financial": -0.12,
                "Consumer": -0.18,
                "Automotive": -0.20,
                "Other": -0.10
            },
            "market_crash": {
                "Technology": -0.25,
                "Financial": -0.20,
                "Consumer": -0.22,
                "Automotive": -0.30,
                "Other": -0.15
            }
        }
        
        # Calculate impacts
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
        
        # Sort by impact
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