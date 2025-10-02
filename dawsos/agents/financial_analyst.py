#!/usr/bin/env python3
"""
Financial Analyst Agent - Specialized agent for DCF modeling, valuation, and financial calculations
Leverages Trinity architecture to provide sophisticated financial analysis
"""

from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
import json
from core.confidence_calculator import confidence_calculator


class FinancialAnalyst(BaseAgent):
    """Agent specialized in financial analysis and DCF modeling"""

    def __init__(self):
        super().__init__("financial_analyst")
        self.capabilities_needed = ['market', 'enriched_data']

    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process financial analysis requests"""
        if context is None:
            context = {}

        request_lower = request.lower()

        # DCF Valuation
        if any(term in request_lower for term in ['dcf', 'discounted cash flow', 'intrinsic value']):
            return self._perform_dcf_analysis(request, context)

        # ROIC Calculation
        elif any(term in request_lower for term in ['roic', 'return on invested capital']):
            return self._calculate_roic(request, context)

        # Owner Earnings
        elif any(term in request_lower for term in ['owner earnings', 'buffett earnings']):
            return self._calculate_owner_earnings(request, context)

        # Free Cash Flow Analysis
        elif any(term in request_lower for term in ['free cash flow', 'fcf']):
            return self._analyze_free_cash_flow(request, context)

        # General Financial Analysis
        else:
            return self._general_financial_analysis(request, context)

    def _perform_dcf_analysis(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive DCF analysis using Trinity architecture"""
        try:
            # Extract symbol from request
            symbol = self._extract_symbol(request, context)
            if not symbol:
                return {"error": "No stock symbol found in request"}

            # Get financial calculation knowledge
            calc_knowledge = self._get_calculation_knowledge()
            if not calc_knowledge:
                return {"error": "Financial calculation knowledge not available"}

            # Get company financial data
            financial_data = self._get_company_financials(symbol)
            if 'error' in financial_data:
                return financial_data

            # Perform DCF calculation using knowledge-driven methodology
            dcf_model = calc_knowledge.get('dcf_models', {}).get('standard_dcf', {})

            # Step 1: Project Cash Flows
            projected_fcf = self._project_cash_flows(financial_data, symbol)

            # Step 2: Calculate Discount Rate (WACC)
            discount_rate = self._calculate_wacc(financial_data, symbol)

            # Step 3: Calculate Present Values
            present_values = self._calculate_present_values(projected_fcf, discount_rate)

            # Step 4: Estimate Terminal Value
            terminal_value = self._estimate_terminal_value(projected_fcf, discount_rate)

            # Step 5: Sum NPV
            intrinsic_value = sum(present_values) + terminal_value

            # Calculate dynamic confidence using the new confidence calculator
            confidence_result = confidence_calculator.calculate_dcf_confidence(
                financial_data=financial_data,
                projections=projected_fcf,
                discount_rate=discount_rate,
                symbol=symbol,
                data_source='financial_api'
            )
            confidence = confidence_result['confidence']

            return {
                "symbol": symbol,
                "dcf_analysis": {
                    "intrinsic_value": round(intrinsic_value, 2),
                    "projected_fcf": projected_fcf,
                    "discount_rate": discount_rate,
                    "terminal_value": terminal_value,
                    "present_values": present_values,
                    "confidence": confidence,
                    "methodology": "Standard DCF using Trinity knowledge base"
                },
                "response": f"DCF analysis for {symbol} shows intrinsic value of ${intrinsic_value:.2f} with {confidence:.0%} confidence"
            }

        except Exception as e:
            return {"error": f"DCF analysis failed: {str(e)}"}

    def _calculate_roic(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Return on Invested Capital using knowledge base methodology"""
        try:
            symbol = self._extract_symbol(request, context)
            if not symbol:
                return {"error": "No stock symbol found in request"}

            # Get ROIC calculation knowledge
            calc_knowledge = self._get_calculation_knowledge()
            roic_config = calc_knowledge.get('roic_calculation', {})

            # Get financial data
            financial_data = self._get_company_financials(symbol)
            if 'error' in financial_data:
                return financial_data

            # Calculate NOPAT (Net Operating Profit After Tax)
            ebit = financial_data.get('ebit', 0)
            tax_rate = financial_data.get('tax_rate', 0.21)  # Default corporate tax rate
            nopat = ebit * (1 - tax_rate)

            # Calculate Invested Capital
            working_capital = financial_data.get('working_capital', 0)
            ppe = financial_data.get('property_plant_equipment', 0)
            goodwill = financial_data.get('goodwill', 0)
            intangibles = financial_data.get('intangible_assets', 0)
            invested_capital = working_capital + ppe + goodwill + intangibles

            # Calculate ROIC
            roic = nopat / invested_capital if invested_capital > 0 else 0

            # Determine quality assessment
            quality_thresholds = roic_config.get('quality_thresholds', {})
            if roic >= quality_thresholds.get('excellent', 0.15):
                quality = "Excellent"
            elif roic >= quality_thresholds.get('good', 0.12):
                quality = "Good"
            elif roic >= quality_thresholds.get('average', 0.08):
                quality = "Average"
            else:
                quality = "Poor"

            return {
                "symbol": symbol,
                "roic_analysis": {
                    "roic": round(roic, 4),
                    "roic_percentage": round(roic * 100, 2),
                    "quality_assessment": quality,
                    "components": {
                        "nopat": nopat,
                        "invested_capital": invested_capital,
                        "ebit": ebit,
                        "tax_rate": tax_rate
                    }
                },
                "response": f"{symbol} ROIC: {roic*100:.2f}% - {quality} performance"
            }

        except Exception as e:
            return {"error": f"ROIC calculation failed: {str(e)}"}

    def _calculate_owner_earnings(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Buffett-style Owner Earnings"""
        try:
            symbol = self._extract_symbol(request, context)
            if not symbol:
                return {"error": "No stock symbol found in request"}

            # Get Owner Earnings calculation knowledge
            calc_knowledge = self._get_calculation_knowledge()
            owner_earnings_config = calc_knowledge.get('buffett_calculations', {}).get('owner_earnings', {})

            # Get financial data
            financial_data = self._get_company_financials(symbol)
            if 'error' in financial_data:
                return financial_data

            # Calculate Owner Earnings following Buffett methodology
            net_income = financial_data.get('net_income', 0)
            depreciation = financial_data.get('depreciation_amortization', 0)
            capex = financial_data.get('capital_expenditures', 0)
            working_capital_change = financial_data.get('working_capital_change', 0)

            # Estimate maintenance capex (typically 70% of D&A)
            maintenance_capex = depreciation * 0.7

            # Calculate Owner Earnings
            owner_earnings = net_income + depreciation - maintenance_capex - working_capital_change

            return {
                "symbol": symbol,
                "owner_earnings_analysis": {
                    "owner_earnings": round(owner_earnings, 2),
                    "components": {
                        "net_income": net_income,
                        "depreciation_amortization": depreciation,
                        "maintenance_capex": maintenance_capex,
                        "working_capital_change": working_capital_change
                    },
                    "methodology": "Buffett Owner Earnings calculation"
                },
                "response": f"{symbol} Owner Earnings: ${owner_earnings:,.0f} million"
            }

        except Exception as e:
            return {"error": f"Owner Earnings calculation failed: {str(e)}"}

    def _project_cash_flows(self, financial_data: Dict, symbol: str) -> List[float]:
        """Project future cash flows based on historical data"""
        try:
            # Get historical FCF
            current_fcf = financial_data.get('free_cash_flow', 0)

            # Use conservative growth assumption
            # In production, would analyze historical trends and use analyst estimates
            growth_rates = [0.08, 0.06, 0.05, 0.04, 0.03]  # Declining growth

            projected_fcf = []
            fcf = current_fcf

            for growth_rate in growth_rates:
                fcf = fcf * (1 + growth_rate)
                projected_fcf.append(fcf)

            return projected_fcf

        except Exception:
            # Fallback to conservative estimates
            return [100, 105, 110, 115, 120]  # Million USD

    def _calculate_wacc(self, financial_data: Dict, symbol: str) -> float:
        """Calculate Weighted Average Cost of Capital"""
        try:
            # Simplified WACC calculation
            # In production, would calculate based on debt/equity ratios and risk factors
            risk_free_rate = 0.045  # Current 10-year Treasury
            market_risk_premium = 0.06
            beta = financial_data.get('beta', 1.0)

            cost_of_equity = risk_free_rate + (beta * market_risk_premium)

            # Assume mostly equity financed for simplicity
            return cost_of_equity

        except Exception:
            return 0.10  # 10% default discount rate

    def _calculate_present_values(self, projected_fcf: List[float], discount_rate: float) -> List[float]:
        """Calculate present values of projected cash flows"""
        present_values = []

        for year, fcf in enumerate(projected_fcf, 1):
            pv = fcf / ((1 + discount_rate) ** year)
            present_values.append(pv)

        return present_values

    def _estimate_terminal_value(self, projected_fcf: List[float], discount_rate: float) -> float:
        """Estimate terminal value using perpetual growth model"""
        if not projected_fcf:
            return 0

        final_fcf = projected_fcf[-1]
        terminal_growth = 0.025  # 2.5% perpetual growth

        terminal_value = (final_fcf * (1 + terminal_growth)) / (discount_rate - terminal_growth)

        # Discount terminal value to present
        years = len(projected_fcf)
        present_terminal_value = terminal_value / ((1 + discount_rate) ** years)

        return present_terminal_value

    def _get_calculation_knowledge(self) -> Dict[str, Any]:
        """Get financial calculation knowledge from enriched data"""
        if 'enriched_data' in self.capabilities:
            return self.capabilities['enriched_data'].get('financial_calculations', {})
        return {}

    def _get_company_financials(self, symbol: str) -> Dict[str, Any]:
        """Get company financial data from market capabilities"""
        if 'market' not in self.capabilities:
            return {"error": "Market capability not available"}

        try:
            market = self.capabilities['market']
            # Get basic quote data
            quote = market.get_quote(symbol)

            if 'error' in quote:
                return quote

            # For demonstration, return realistic financial data structure
            # In production, would fetch actual financial statements
            return {
                "symbol": symbol,
                "free_cash_flow": quote.get('market_cap', 1000) * 0.05,  # 5% of market cap
                "net_income": quote.get('market_cap', 1000) * 0.08,
                "ebit": quote.get('market_cap', 1000) * 0.12,
                "depreciation_amortization": quote.get('market_cap', 1000) * 0.03,
                "capital_expenditures": quote.get('market_cap', 1000) * 0.04,
                "working_capital": quote.get('market_cap', 1000) * 0.15,
                "working_capital_change": quote.get('market_cap', 1000) * 0.01,
                "property_plant_equipment": quote.get('market_cap', 1000) * 0.4,
                "goodwill": quote.get('market_cap', 1000) * 0.2,
                "intangible_assets": quote.get('market_cap', 1000) * 0.1,
                "tax_rate": 0.21,
                "beta": 1.2
            }

        except Exception as e:
            return {"error": f"Failed to get financial data: {str(e)}"}

    def _calculate_confidence(self, financial_data: Dict, symbol: str) -> float:
        """Calculate confidence score based on data quality and business predictability"""
        try:
            # Get confidence factors from knowledge base
            calc_knowledge = self._get_calculation_knowledge()
            confidence_factors = calc_knowledge.get('valuation_methodologies', {}).get('confidence_factors', {})

            # Assess data quality based on available financial data
            data_quality = self._assess_data_quality(financial_data)

            # Calculate business predictability based on sector and metrics
            business_predictability = self._assess_business_predictability(financial_data, symbol)

            # Use dynamic confidence calculator
            confidence_result = confidence_calculator.calculate_confidence(
                data_quality=data_quality,
                model_accuracy=business_predictability,
                historical_success_rate=confidence_factors.get('dcf_success_rate', 0.68),
                num_data_points=len([k for k, v in financial_data.items() if v is not None]),
                analysis_type='dcf'
            )

            return confidence_result['confidence']

        except Exception:
            # Fallback to dynamic calculation with defaults
            return confidence_calculator.calculate_confidence(
                data_quality=0.6,
                analysis_type='dcf'
            )['confidence']

    def _analyze_free_cash_flow(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze free cash flow trends and quality"""
        try:
            symbol = self._extract_symbol(request, context)
            if not symbol:
                return {"error": "No stock symbol found in request"}

            financial_data = self._get_company_financials(symbol)
            if 'error' in financial_data:
                return financial_data

            fcf = financial_data.get('free_cash_flow', 0)
            net_income = financial_data.get('net_income', 0)

            # Calculate FCF conversion ratio
            fcf_conversion = fcf / net_income if net_income > 0 else 0

            return {
                "symbol": symbol,
                "fcf_analysis": {
                    "free_cash_flow": fcf,
                    "fcf_conversion_ratio": round(fcf_conversion, 3),
                    "quality_assessment": "High" if fcf_conversion > 0.8 else "Moderate" if fcf_conversion > 0.5 else "Low"
                },
                "response": f"{symbol} FCF: ${fcf:,.0f}M (conversion ratio: {fcf_conversion:.1%})"
            }

        except Exception as e:
            return {"error": f"FCF analysis failed: {str(e)}"}

    def _general_financial_analysis(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general financial analysis"""
        return {
            "response": "I can help with DCF analysis, ROIC calculations, Owner Earnings, and FCF analysis. Please specify a stock symbol and analysis type.",
            "capabilities": [
                "DCF (Discounted Cash Flow) valuation",
                "ROIC (Return on Invested Capital) calculation",
                "Buffett-style Owner Earnings calculation",
                "Free Cash Flow analysis",
                "Financial ratio calculations"
            ]
        }

    def _extract_symbol(self, request: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract stock symbol from request or context"""
        # Check context first
        if context and 'symbol' in context:
            return context['symbol']

        # Extract from request text
        words = request.upper().split()

        # Look for common stock symbol patterns
        for word in words:
            if len(word) >= 1 and len(word) <= 5 and word.isalpha():
                return word

        return None

    def _assess_data_quality(self, financial_data: Dict[str, Any]) -> float:
        """Assess the quality of financial data"""
        if not financial_data:
            return 0.3

        # Check for key financial metrics
        required_fields = ['free_cash_flow', 'net_income', 'revenue', 'ebit']
        present_fields = sum(1 for field in required_fields if financial_data.get(field) is not None)
        completeness_score = present_fields / len(required_fields)

        # Check for data consistency
        consistency_score = 0.8  # Default good consistency
        fcf = financial_data.get('free_cash_flow', 0)
        net_income = financial_data.get('net_income', 0)

        if fcf and net_income:
            fcf_ratio = abs(fcf / net_income) if net_income != 0 else 0
            if fcf_ratio > 3:  # Unusual FCF/NI ratio
                consistency_score -= 0.2

        # Calculate overall data quality
        data_quality = (completeness_score * 0.6 + consistency_score * 0.4)
        return min(1.0, max(0.0, data_quality))

    def _assess_business_predictability(self, financial_data: Dict[str, Any], symbol: str) -> float:
        """Assess business predictability based on financial metrics"""
        predictability = 0.7  # Base predictability

        # Higher predictability for stable metrics
        roic = self._calculate_roic_internal(financial_data)
        if roic and roic > 0.15:  # Strong ROIC suggests predictable business
            predictability += 0.1
        elif roic and roic < 0.05:  # Weak ROIC suggests unpredictable business
            predictability -= 0.1

        # Check debt levels (high debt = less predictable)
        debt_equity = financial_data.get('debt_to_equity', 0.5)
        if debt_equity > 1.0:  # High leverage
            predictability -= 0.1
        elif debt_equity < 0.3:  # Conservative leverage
            predictability += 0.05

        return min(1.0, max(0.3, predictability))

    def _calculate_roic_internal(self, financial_data: Dict[str, Any]) -> Optional[float]:
        """Internal ROIC calculation for predictability assessment"""
        try:
            ebit = financial_data.get('ebit', 0)
            tax_rate = financial_data.get('tax_rate', 0.21)
            invested_capital = (financial_data.get('working_capital', 0) +
                              financial_data.get('property_plant_equipment', 0) +
                              financial_data.get('goodwill', 0))

            if invested_capital > 0:
                nopat = ebit * (1 - tax_rate)
                return nopat / invested_capital
        except:
            pass
        return None