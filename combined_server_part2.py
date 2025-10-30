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
        }