#!/usr/bin/env python3
"""
Financial Analyst Agent - Specialized agent for DCF modeling, valuation, and financial calculations
Leverages Trinity architecture to provide sophisticated financial analysis
"""

from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
from datetime import datetime
from ..core.confidence_calculator import confidence_calculator
from .analyzers.dcf_analyzer import DCFAnalyzer
from .analyzers.moat_analyzer import MoatAnalyzer
import logging

logger = logging.getLogger(__name__)


class FinancialAnalyst(BaseAgent):
    """Agent specialized in financial analysis and DCF modeling"""

    def __init__(self, graph=None, llm_client=None):
        super().__init__(graph=graph, name="financial_analyst", llm_client=llm_client)
        self.capabilities_needed = ['market', 'enriched_data']

        # Initialize analyzers (Phase 2.1 extraction)
        self.dcf_analyzer = None  # Lazy initialization on first use
        self.moat_analyzer = None  # Lazy initialization on first use

    def _ensure_dcf_analyzer(self):
        """Lazy initialization of DCF analyzer (needs market capability)"""
        if self.dcf_analyzer is None and 'market' in self.capabilities:
            self.dcf_analyzer = DCFAnalyzer(
                self.capabilities['market'],
                self.logger
            )

    def _ensure_moat_analyzer(self):
        """Lazy initialization of moat analyzer"""
        if self.moat_analyzer is None:
            self.moat_analyzer = MoatAnalyzer(self.logger)

    def _find_or_create_company_node(self, symbol: str, financial_data: Dict = None) -> str:
        """Find existing company node or create a new one"""
        # Search for existing company node
        for node_id, node in self.graph.nodes.items():
            if node['type'] == 'company' and node['data'].get('symbol') == symbol:
                return node_id

        # Create new company node
        company_data = {
            'symbol': symbol,
            'name': financial_data.get('company_name', symbol) if financial_data else symbol,
            'sector': financial_data.get('sector', 'Unknown') if financial_data else 'Unknown',
            'created': datetime.now().isoformat()
        }

        return self.add_knowledge('company', company_data)

    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process financial analysis requests"""
        if context is None:
            context = {}

        request_lower = request.lower()

        # Store query node if this is a new analysis query
        query_node_id = None
        if self.graph and any(term in request_lower for term in ['analyze', 'calculate', 'evaluate']):
            symbol = self._extract_symbol(request, context)
            if symbol:
                query_data = {
                    'query': request,
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'financial_analysis'
                }
                query_node_id = self.add_knowledge('analysis_query', query_data)
                context['query_node_id'] = query_node_id

        # Economy analysis handler
        if any(term in request_lower for term in ['economy', 'economic regime', 'macro analysis', 'economic analysis']):
            return self.analyze_economy(context)

        # Portfolio risk analysis handler
        elif any(term in request_lower for term in ['portfolio risk', 'portfolio analysis', 'holdings risk']):
            holdings = context.get('holdings', {})
            if not holdings:
                return {"error": "Portfolio analysis requires 'holdings' in context (dict of symbol: weight)"}
            return self.analyze_portfolio_risk(holdings, context)

        # Comprehensive stock analysis handler
        elif any(term in request_lower for term in ['comprehensive stock', 'full stock analysis', 'stock comprehensive']):
            symbol = self._extract_symbol(request, context)
            if not symbol:
                return {"error": "No stock symbol found in request"}
            return self.analyze_stock_comprehensive(symbol, context)

        # Stock comparison handler
        elif any(term in request_lower for term in ['compare stocks', 'stock comparison']):
            symbols = context.get('symbols', [])
            if not symbols:
                return {"error": "Stock comparison requires 'symbols' list in context"}
            return self.compare_stocks(symbols, context)

        # DCF Valuation
        elif any(term in request_lower for term in ['dcf', 'discounted cash flow', 'intrinsic value']):
            return self._perform_dcf_analysis(request, context)

        # ROIC Calculation
        elif any(term in request_lower for term in ['roic', 'return on invested capital']):
            return self._calculate_roic(request, context)

        # Owner Earnings
        elif any(term in request_lower for term in ['owner earnings', 'buffett earnings']):
            return self._calculate_owner_earnings(request, context)

        # Moat Analysis
        elif any(term in request_lower for term in ['moat', 'competitive advantage', 'competitive position']):
            return self._analyze_moat(request, context)

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

            # Phase 2.1: Delegate DCF calculation to DCFAnalyzer
            self._ensure_dcf_analyzer()
            if self.dcf_analyzer:
                # Use extracted DCF analyzer
                dcf_result = self.dcf_analyzer.calculate_intrinsic_value(symbol, financial_data)
                projected_fcf = dcf_result['projected_fcf']
                discount_rate = dcf_result['discount_rate']
                present_values = dcf_result['present_values']
                terminal_value = dcf_result['terminal_value']
                intrinsic_value = dcf_result['intrinsic_value']
            else:
                # Fallback to legacy implementation if DCF analyzer not available
                projected_fcf = self._project_cash_flows(financial_data, symbol)
                discount_rate = self._calculate_wacc(financial_data, symbol)
                present_values = self._calculate_present_values(projected_fcf, discount_rate)
                terminal_value = self._estimate_terminal_value(projected_fcf, discount_rate)
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

            # Store DCF analysis in knowledge graph
            dcf_node_data = {
                "symbol": symbol,
                "intrinsic_value": round(intrinsic_value, 2),
                "projected_fcf": projected_fcf,
                "discount_rate": discount_rate,
                "terminal_value": terminal_value,
                "present_values": present_values,
                "confidence": confidence,
                "methodology": "Standard DCF using Trinity knowledge base",
                "timestamp": datetime.now().isoformat()
            }

            # Add DCF result node to graph if graph is available
            dcf_node_id = None
            if self.graph:
                dcf_node_id = self.add_knowledge('dcf_analysis', dcf_node_data)

                # Find or create company node
                company_node_id = self._find_or_create_company_node(symbol, financial_data)

                # Connect DCF to company
                self.connect_knowledge(dcf_node_id, company_node_id, 'analyzes', strength=confidence)

                # If this was from a query, connect to query node
                if context.get('query_node_id'):
                    self.connect_knowledge(context['query_node_id'], dcf_node_id, 'resulted_in', strength=0.9)

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
                "node_id": dcf_node_id,
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

            # Store ROIC analysis in knowledge graph
            roic_node_data = {
                "symbol": symbol,
                "roic": round(roic, 4),
                "roic_percentage": round(roic * 100, 2),
                "quality_assessment": quality,
                "nopat": nopat,
                "invested_capital": invested_capital,
                "ebit": ebit,
                "tax_rate": tax_rate,
                "timestamp": datetime.now().isoformat()
            }

            # Add ROIC node to graph if graph is available
            roic_node_id = None
            if self.graph:
                roic_node_id = self.add_knowledge('roic_analysis', roic_node_data)

                # Find or create company node
                company_node_id = self._find_or_create_company_node(symbol, financial_data)

                # Connect ROIC to company
                self.connect_knowledge(roic_node_id, company_node_id, 'analyzes', strength=0.9)

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
                "node_id": roic_node_id,
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

            # Store Owner Earnings analysis in knowledge graph
            owner_node_data = {
                "symbol": symbol,
                "owner_earnings": round(owner_earnings, 2),
                "net_income": net_income,
                "depreciation_amortization": depreciation,
                "maintenance_capex": maintenance_capex,
                "working_capital_change": working_capital_change,
                "methodology": "Buffett Owner Earnings calculation",
                "timestamp": datetime.now().isoformat()
            }

            # Add Owner Earnings node to graph if graph is available
            owner_node_id = None
            if self.graph:
                owner_node_id = self.add_knowledge('owner_earnings', owner_node_data)

                # Find or create company node
                company_node_id = self._find_or_create_company_node(symbol, financial_data)

                # Connect Owner Earnings to company
                self.connect_knowledge(owner_node_id, company_node_id, 'analyzes', strength=0.85)

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
                "node_id": owner_node_id,
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
        """Get company financial data from FMP API via market capability"""
        if 'market' not in self.capabilities:
            return {"error": "Market capability not available"}

        try:
            market = self.capabilities['market']

            # Get latest financial statements from FMP API
            income_statements = market.get_financials(symbol, statement='income', period='annual')
            balance_sheets = market.get_financials(symbol, statement='balance', period='annual')
            cash_flow_statements = market.get_financials(symbol, statement='cash-flow', period='annual')
            company_profile = market.get_company_profile(symbol)

            # Check for errors in any response
            if not income_statements or 'error' in income_statements[0]:
                return {"error": f"Failed to fetch income statement for {symbol}"}
            if not balance_sheets or 'error' in balance_sheets[0]:
                return {"error": f"Failed to fetch balance sheet for {symbol}"}
            if not cash_flow_statements or 'error' in cash_flow_statements[0]:
                return {"error": f"Failed to fetch cash flow statement for {symbol}"}

            # Get most recent period (index 0)
            income = income_statements[0]
            balance = balance_sheets[0]
            cash_flow = cash_flow_statements[0]

            # Calculate derived metrics
            total_debt = balance.get('debt', 0) or 0
            total_equity = balance.get('total_equity', 0) or 0
            total_capital = total_debt + total_equity

            # Get or calculate free cash flow
            free_cash_flow = cash_flow.get('free_cash_flow')
            if not free_cash_flow:
                # Calculate: Operating Cash Flow - Capital Expenditures
                operating_cf = cash_flow.get('operating_cash_flow', 0) or 0
                capex = abs(cash_flow.get('capex', 0) or 0)  # CapEx is usually negative
                free_cash_flow = operating_cf - capex

            # Build comprehensive financial data structure
            return {
                "symbol": symbol,
                # Core metrics for DCF
                "free_cash_flow": free_cash_flow or 0,
                "net_income": income.get('net_income', 0) or 0,
                "ebit": income.get('operating_income', 0) or 0,  # Operating income = EBIT
                "ebitda": income.get('ebitda', 0) or 0,
                "revenue": income.get('revenue', 0) or 0,

                # Cash flow components
                "operating_cash_flow": cash_flow.get('operating_cash_flow', 0) or 0,
                "capital_expenditures": abs(cash_flow.get('capex', 0) or 0),
                "depreciation_amortization": income.get('ebitda', 0) - income.get('operating_income', 0) if income.get('ebitda') and income.get('operating_income') else 0,

                # Balance sheet items
                "total_debt": total_debt,
                "total_equity": total_equity,
                "cash": balance.get('cash', 0) or 0,
                "total_assets": balance.get('total_assets', 0) or 0,
                "total_liabilities": balance.get('total_liabilities', 0) or 0,
                "working_capital": (balance.get('total_assets', 0) or 0) - (balance.get('total_liabilities', 0) or 0),
                "working_capital_change": 0,  # Would need historical data to calculate

                # Additional metrics from profile
                "tax_rate": 0.21,  # Default US corporate tax rate
                "beta": company_profile.get('beta', 1.0) if company_profile and 'error' not in company_profile else 1.0,
                "market_cap": company_profile.get('mktCap', 0) if company_profile and 'error' not in company_profile else 0,

                # Metadata
                "period": income.get('date', 'Unknown'),
                "data_source": "FMP API",
                "fetched_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get financial data for {symbol}: {e}", exc_info=True)
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

    def _analyze_moat(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze economic moat (competitive advantage) for a company"""
        try:
            symbol = self._extract_symbol(request, context)
            if not symbol:
                return {"error": "No stock symbol found in request"}

            # Get financial data for moat analysis
            financial_data = self._get_company_financials(symbol)
            if 'error' in financial_data:
                return financial_data

            # Phase 2.1: Delegate to MoatAnalyzer
            self._ensure_moat_analyzer()
            if self.moat_analyzer:
                # Use MoatAnalyzer for moat calculation
                moat_analysis = self.moat_analyzer.analyze_moat(symbol, financial_data)

                # Extract results for backward compatibility
                moat_rating = moat_analysis['moat_rating']
                total_score = moat_analysis['overall_score']
                moat_scores = moat_analysis['factors']

                # Store moat analysis in knowledge graph
                moat_node_data = {
                    'symbol': symbol,
                    'moat_rating': moat_rating,
                    'moat_score': total_score,
                    'brand_score': moat_scores['brand'],
                    'network_effects_score': moat_scores['network_effects'],
                    'cost_advantages_score': moat_scores['cost_advantages'],
                    'switching_costs_score': moat_scores['switching_costs'],
                    'intangible_assets_score': moat_scores['intangible_assets'],
                    'gross_margin': financial_data.get('gross_margin', 0),
                    'operating_margin': financial_data.get('operating_margin', 0),
                    'timestamp': moat_analysis['timestamp']
                }

                # Add moat analysis node to graph if graph is available
                moat_node_id = None
                if self.graph:
                    moat_node_id = self.add_knowledge('moat_analysis', moat_node_data)

                    # Find or create company node
                    company_node_id = self._find_or_create_company_node(symbol, financial_data)

                    # Connect moat analysis to company
                    self.connect_knowledge(moat_node_id, company_node_id, 'analyzes', strength=0.9)

                    # If this was from a query, connect to query node
                    if context.get('query_node_id'):
                        self.connect_knowledge(context['query_node_id'], moat_node_id, 'resulted_in', strength=0.95)

                return {
                    "symbol": symbol,
                    "moat_analysis": {
                        "moat_rating": moat_rating,
                        "overall_score": total_score,
                        "factors": moat_scores,
                        "financial_evidence": moat_analysis['financial_evidence']
                    },
                    "node_id": moat_node_id,
                    "response": f"{symbol} has a {moat_rating} moat with score {total_score:.1f}/50"
                }
            else:
                # Fallback to legacy inline implementation (should not happen)
                self.logger.warning("MoatAnalyzer not available, using fallback")
                return self._analyze_moat_legacy(symbol, financial_data, context)

        except Exception as e:
            return {"error": f"Moat analysis failed: {str(e)}"}

    def _analyze_moat_legacy(self, symbol: str, financial_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy moat analysis implementation (fallback only)"""
        # Calculate moat factors (inline legacy version)
        moat_scores = {
            'brand': 0,
            'network_effects': 0,
            'cost_advantages': 0,
            'switching_costs': 0,
            'intangible_assets': 0
        }

        # Brand moat (based on gross margin)
        gross_margin = financial_data.get('gross_margin', 0)
        if gross_margin > 0.5:
            moat_scores['brand'] = min(10, gross_margin * 15)

        # Network effects (for tech companies)
        if financial_data.get('sector') in ['Technology', 'Communication Services']:
            revenue_growth = financial_data.get('revenue_growth', 0)
            if revenue_growth > 0.2:
                moat_scores['network_effects'] = min(10, revenue_growth * 30)

        # Cost advantages (based on operating margin)
        operating_margin = financial_data.get('operating_margin', 0)
        if operating_margin > 0.2:
            moat_scores['cost_advantages'] = min(10, operating_margin * 30)

        # Switching costs
        if financial_data.get('recurring_revenue_pct', 0) > 0.7:
            moat_scores['switching_costs'] = 8

        # Calculate overall moat score
        total_score = sum(moat_scores.values())
        moat_rating = 'Wide' if total_score > 30 else 'Narrow' if total_score > 15 else 'None'

        # Store in graph
        moat_node_data = {
            'symbol': symbol,
            'moat_rating': moat_rating,
            'moat_score': total_score,
            'brand_score': moat_scores['brand'],
            'network_effects_score': moat_scores['network_effects'],
            'cost_advantages_score': moat_scores['cost_advantages'],
            'switching_costs_score': moat_scores['switching_costs'],
            'intangible_assets_score': moat_scores['intangible_assets'],
            'gross_margin': gross_margin,
            'operating_margin': operating_margin,
            'timestamp': datetime.now().isoformat()
        }

        moat_node_id = None
        if self.graph:
            moat_node_id = self.add_knowledge('moat_analysis', moat_node_data)
            company_node_id = self._find_or_create_company_node(symbol, financial_data)
            self.connect_knowledge(moat_node_id, company_node_id, 'analyzes', strength=0.9)
            if context.get('query_node_id'):
                self.connect_knowledge(context['query_node_id'], moat_node_id, 'resulted_in', strength=0.95)

        return {
            "symbol": symbol,
            "moat_analysis": {
                "moat_rating": moat_rating,
                "overall_score": total_score,
                "factors": moat_scores,
                "financial_evidence": {
                    "gross_margin": f"{gross_margin:.1%}",
                    "operating_margin": f"{operating_margin:.1%}"
                }
            },
            "node_id": moat_node_id,
            "response": f"{symbol} has a {moat_rating} moat with score {total_score:.1f}/50"
        }

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
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to calculate internal ROIC: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in ROIC calculation: {e}", exc_info=True)
            return None
        return None

    # ==================== MIGRATED FROM ARCHIVED AGENTS ====================
    # The following methods were migrated from equity_agent, macro_agent, and risk_agent
    # during the October 2025 legacy elimination refactor.
    # See git history at commit e2be11e for original implementations.

    def analyze_stock_comprehensive(self, symbol: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive stock analysis including fundamental + macro influences + catalysts

        Migrated from equity_agent.analyze_stock()
        Combines DCF/ROIC analysis with macro influence tracing and catalyst identification
        """
        if context is None:
            context = {}

        # Find or create stock node
        stock_node = self._find_or_create_company_node(symbol)

        # Get connections for influence analysis
        if hasattr(self.graph, 'trace_connections'):
            connections = self.graph.trace_connections(stock_node, max_depth=3)
        else:
            connections = []

        # Build comprehensive analysis
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),

            # Fundamental analysis (existing methods)
            'dcf_valuation': self._perform_dcf_analysis(f"DCF for {symbol}", {'symbol': symbol}),
            'roic': self._calculate_roic(f"ROIC for {symbol}", {'symbol': symbol}),

            # Macro influences (new)
            'macro_influences': self._find_macro_influences_for_stock(stock_node, connections),

            # Sector positioning (new)
            'sector_position': self._analyze_sector_position_for_stock(stock_node),

            # Risk factors (new)
            'risk_factors': self._identify_stock_risks(stock_node, connections),

            # Growth catalysts (new)
            'catalysts': self._identify_catalysts(stock_node, connections),

            # Metadata
            'connection_count': len(connections),
            'analysis_type': 'comprehensive'
        }

        return analysis

    def _find_macro_influences_for_stock(self, stock_node: str, connections: List[List[Dict]]) -> List[Dict]:
        """
        Find macroeconomic influences on stock through graph relationships

        Migrated from equity_agent._find_macro_influences()
        Traces paths from economic indicators to stock
        """
        macro_influences = []

        for path in connections:
            for edge in path:
                from_node = self.graph.nodes.get(edge['from'], {})
                from_type = from_node.get('type', '')

                # Check if node is a macro/economic indicator
                if from_type in ['indicator', 'economic', 'macro']:
                    influence = {
                        'factor': edge['from'],
                        'factor_name': from_node.get('data', {}).get('name', edge['from']),
                        'relationship': edge['type'],
                        'strength': edge.get('strength', 0.5),
                        'type': from_type
                    }

                    # Avoid duplicates
                    if influence not in macro_influences:
                        macro_influences.append(influence)

        # Return top 5 strongest influences
        return sorted(macro_influences, key=lambda x: x['strength'], reverse=True)[:5]

    def _analyze_sector_position_for_stock(self, stock_node: str) -> Dict:
        """
        Analyze stock's position within its sector including peer comparison

        Migrated from equity_agent._analyze_sector_position()
        """
        # Find sector connections (PART_OF relationship)
        for edge in self.graph.edges:
            if edge['from'] == stock_node and edge.get('type') == 'PART_OF':
                sector_node = edge['to']

                # Get sector forecast if available
                sector_forecast = {}
                if hasattr(self.graph, 'forecast'):
                    sector_forecast = self.graph.forecast(sector_node)

                # Find peer companies in same sector
                peers = []
                for other_edge in self.graph.edges:
                    if (other_edge.get('to') == sector_node and
                        other_edge.get('type') == 'PART_OF' and
                        other_edge['from'] != stock_node):
                        peers.append(other_edge['from'])

                return {
                    'sector': sector_node,
                    'sector_name': self.graph.nodes.get(sector_node, {}).get('data', {}).get('name', sector_node),
                    'sector_outlook': sector_forecast.get('forecast', 'neutral'),
                    'peer_count': len(peers),
                    'peers': peers[:5]  # Top 5 peers
                }

        return {
            'sector': 'unknown',
            'sector_outlook': 'neutral',
            'peer_count': 0,
            'peers': []
        }

    def _identify_stock_risks(self, stock_node: str, connections: List[List[Dict]]) -> List[str]:
        """
        Identify risks specific to the stock from graph relationships

        Migrated from equity_agent._identify_stock_risks()
        Looks for PRESSURES and WEAKENS relationships
        """
        risks = []

        # Check for negative relationships
        for path in connections:
            for edge in path:
                if edge.get('to') == stock_node:
                    relationship = edge.get('type', '')

                    # Negative relationship types
                    if relationship in ['PRESSURES', 'WEAKENS', 'THREATENS', 'COMPETES_WITH']:
                        from_node_id = edge['from']
                        from_node = self.graph.nodes.get(from_node_id, {})
                        from_name = from_node.get('data', {}).get('name', from_node_id)
                        strength = edge.get('strength', 0.5)

                        risks.append(f"{from_name} {relationship.lower()} stock (strength: {strength:.2f})")

        return risks[:5]  # Top 5 risks

    def _identify_catalysts(self, stock_node: str, connections: List[List[Dict]]) -> List[str]:
        """
        Identify potential growth catalysts from graph relationships

        Migrated from equity_agent._identify_catalysts()
        Looks for SUPPORTS and STRENGTHENS relationships
        """
        catalysts = []

        # Check for positive relationships
        for path in connections:
            for edge in path:
                if edge.get('to') == stock_node:
                    relationship = edge.get('type', '')

                    # Positive relationship types
                    if relationship in ['SUPPORTS', 'STRENGTHENS', 'BENEFITS_FROM', 'ALIGNED_WITH']:
                        from_node_id = edge['from']
                        from_node = self.graph.nodes.get(from_node_id, {})
                        from_name = from_node.get('data', {}).get('name', from_node_id)
                        strength = edge.get('strength', 0.5)

                        catalysts.append(f"{from_name} {relationship.lower()} stock (strength: {strength:.2f})")

        return catalysts[:5]  # Top 5 catalysts

    def compare_stocks(self, symbols: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Side-by-side comparison of multiple stocks

        Migrated from equity_agent.compare_stocks()
        Compares fundamentals, valuations, and relative strengths
        """
        if context is None:
            context = {}

        comparisons = {}

        for symbol in symbols:
            try:
                # Get comprehensive analysis for each stock
                analysis = self.analyze_stock_comprehensive(symbol, context)
                comparisons[symbol] = {
                    'dcf_value': analysis.get('dcf_valuation', {}).get('intrinsic_value'),
                    'roic': analysis.get('roic', {}).get('roic'),
                    'macro_risk_count': len(analysis.get('risk_factors', [])),
                    'catalyst_count': len(analysis.get('catalysts', [])),
                    'sector': analysis.get('sector_position', {}).get('sector_name'),
                    'peer_count': analysis.get('sector_position', {}).get('peer_count', 0)
                }
            except Exception as e:
                comparisons[symbol] = {'error': str(e)}

        return {
            'timestamp': datetime.now().isoformat(),
            'symbols_compared': symbols,
            'comparisons': comparisons,
            'analysis_type': 'stock_comparison'
        }
    # ==================== MACRO ECONOMY ANALYSIS ====================
    # Migrated from macro_agent.py

    def analyze_economy(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive macroeconomic analysis including regime detection

        Migrated from macro_agent.analyze_economy()
        Analyzes key economic indicators and determines current economic regime
        """
        if context is None:
            context = {}

        key_indicators = [
            'GDP', 'CPI', 'UNEMPLOYMENT', 'FED_RATE',
            'M2', 'TREASURY_10Y', 'VIX', 'DXY'
        ]

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'indicators': {},
            'regime': None,
            'risks': [],
            'opportunities': []
        }

        # Analyze each indicator
        for indicator in key_indicators:
            # Query graph for indicator node
            indicator_nodes = [
                node_id for node_id, node in self.graph.nodes.items()
                if node.get('type') == 'indicator' and 
                   node.get('data', {}).get('name') == indicator
            ]

            if indicator_nodes:
                node_id = indicator_nodes[0]
                node = self.graph.nodes.get(node_id, {})
                value = node.get('data', {}).get('value')

                # Get forecast if available
                forecast_data = {}
                if hasattr(self.graph, 'forecast'):
                    forecast_data = self.graph.forecast(node_id)

                analysis['indicators'][indicator] = {
                    'current': value,
                    'forecast': forecast_data.get('forecast', 'neutral'),
                    'confidence': forecast_data.get('confidence', 0.5),
                    'key_drivers': forecast_data.get('key_drivers', [])
                }

        # Determine economic regime
        analysis['regime'] = self._determine_economic_regime(analysis['indicators'])

        # Identify macro risks and opportunities
        analysis['risks'] = self._identify_macro_risks(analysis)
        analysis['opportunities'] = self._identify_sector_opportunities(analysis)

        return analysis

    def _determine_economic_regime(self, indicators: Dict) -> str:
        """
        Determine current economic regime based on indicator forecasts

        Migrated from macro_agent._determine_regime()
        Returns: goldilocks, stagflation, overheating, recession, or transitional
        """
        gdp = indicators.get('GDP', {})
        inflation = indicators.get('CPI', {})

        if not gdp or not inflation:
            return 'insufficient_data'

        growth_outlook = gdp.get('forecast', 'neutral')
        inflation_outlook = inflation.get('forecast', 'neutral')

        # Regime determination logic
        if growth_outlook == 'bullish' and inflation_outlook == 'bearish':
            return 'goldilocks'  # Good growth, low inflation
        elif growth_outlook == 'bearish' and inflation_outlook == 'bullish':
            return 'stagflation'  # Low growth, high inflation
        elif growth_outlook == 'bullish' and inflation_outlook == 'bullish':
            return 'overheating'  # High growth, high inflation
        elif growth_outlook == 'bearish' and inflation_outlook == 'bearish':
            return 'recession'  # Low growth, low inflation
        else:
            return 'transitional'

    def _identify_macro_risks(self, analysis: Dict) -> List[str]:
        """Identify macroeconomic risks based on indicator analysis"""
        risks = []

        indicators = analysis.get('indicators', {})

        # Check for recession signals
        if indicators.get('GDP', {}).get('forecast') == 'bearish':
            risks.append("GDP forecast bearish - recession risk")

        # Check for inflation concerns
        if indicators.get('CPI', {}).get('forecast') == 'bullish':
            risks.append("Inflation rising - purchasing power erosion")

        # Check for rate risk
        if indicators.get('FED_RATE', {}).get('forecast') == 'bullish':
            risks.append("Rising rates - valuation compression risk")

        # Check for market stress
        vix = indicators.get('VIX', {})
        if vix.get('current') and vix['current'] > 25:
            risks.append(f"Elevated market volatility (VIX: {vix['current']})")

        return risks

    def _identify_sector_opportunities(self, analysis: Dict) -> List[str]:
        """Identify sector opportunities based on economic regime"""
        opportunities = []
        regime = analysis.get('regime')

        # Regime-based sector recommendations
        if regime == 'goldilocks':
            opportunities.append("Technology sector - benefits from growth + low rates")
            opportunities.append("Consumer discretionary - strong demand environment")
        elif regime == 'stagflation':
            opportunities.append("Energy sector - inflation hedge")
            opportunities.append("Commodities - real asset protection")
        elif regime == 'recession':
            opportunities.append("Defensive sectors - utilities, healthcare")
            opportunities.append("Quality companies - pricing power")
        elif regime == 'overheating':
            opportunities.append("Financials - benefit from rising rates")
            opportunities.append("Materials - supply constraints")

        return opportunities

    # ==================== PORTFOLIO RISK ANALYSIS ====================
    # Migrated from risk_agent.py

    def analyze_portfolio_risk(self, holdings: Dict[str, float], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive portfolio risk analysis

        Migrated from risk_agent.analyze_portfolio_risk()

        Args:
            holdings: Dict of {symbol: position_size_percent}
            context: Additional context

        Returns:
            Dict with concentration, correlation, and risk metrics
        """
        if context is None:
            context = {}

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'holdings_count': len(holdings),
            'concentration': self._check_concentration_risk(holdings),
            'correlations': self._analyze_portfolio_correlations(holdings),
            'macro_sensitivity': self._analyze_macro_sensitivity(holdings),
            'recommendations': []
        }

        # Generate risk recommendations
        analysis['recommendations'] = self._generate_portfolio_recommendations(analysis)

        return analysis

    def _check_concentration_risk(self, holdings: Dict[str, float]) -> Dict:
        """
        Check for concentration risk in portfolio

        Migrated from risk_agent._check_concentration()
        """
        # Calculate concentration metrics
        total_weight = sum(holdings.values())
        if total_weight == 0:
            return {'error': 'Empty portfolio'}

        # Normalize weights
        normalized = {k: (v / total_weight) * 100 for k, v in holdings.items()}

        # Find largest positions
        sorted_positions = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        top_5 = sorted_positions[:5]
        top_5_weight = sum([pos[1] for pos in top_5])

        # Concentration flags
        flags = []
        if any(weight > 20 for _, weight in sorted_positions):
            flags.append("Single position >20% - high concentration risk")
        if top_5_weight > 60:
            flags.append(f"Top 5 positions = {top_5_weight:.1f}% - portfolio concentration")

        return {
            'largest_position': sorted_positions[0] if sorted_positions else None,
            'top_5_concentration': top_5_weight,
            'flags': flags,
            'positions': sorted_positions
        }

    def _analyze_portfolio_correlations(self, holdings: Dict[str, float]) -> Dict:
        """
        Analyze correlations between portfolio holdings

        Migrated from risk_agent._analyze_correlations()
        Simplified implementation - full correlation requires historical data
        """
        # Simplified: Check sector concentration as proxy for correlation
        sector_exposure = {}

        for symbol in holdings.keys():
            # Find company node
            company_node = self._find_or_create_company_node(symbol)
            node_data = self.graph.nodes.get(company_node, {})
            sector = node_data.get('data', {}).get('sector', 'Unknown')

            sector_exposure[sector] = sector_exposure.get(sector, 0) + holdings[symbol]

        # Identify high correlation risk (sector concentration)
        total = sum(sector_exposure.values())
        sector_pcts = {k: (v/total)*100 for k, v in sector_exposure.items()} if total > 0 else {}

        flags = []
        for sector, pct in sector_pcts.items():
            if pct > 40:
                flags.append(f"{sector} sector >40% - high sector correlation risk")

        return {
            'sector_exposure': sector_pcts,
            'flags': flags,
            'note': 'Sector concentration used as correlation proxy'
        }

    def _analyze_macro_sensitivity(self, holdings: Dict[str, float]) -> Dict:
        """
        Analyze portfolio sensitivity to macroeconomic factors

        Migrated from risk_agent._analyze_macro_sensitivity()
        """
        # Aggregate macro influences across portfolio
        macro_exposures = {}

        for symbol, weight in holdings.items():
            try:
                # Get comprehensive analysis
                analysis = self.analyze_stock_comprehensive(symbol)
                macro_influences = analysis.get('macro_influences', [])

                # Weight the influences by position size
                for influence in macro_influences:
                    factor = influence['factor_name']
                    strength = influence['strength'] * (weight / 100)  # Weight by position

                    macro_exposures[factor] = macro_exposures.get(factor, 0) + strength

            except Exception:
                pass  # Skip stocks with errors

        # Sort by exposure strength
        sorted_exposures = sorted(macro_exposures.items(), key=lambda x: x[1], reverse=True)

        return {
            'top_exposures': sorted_exposures[:5],
            'total_factors': len(macro_exposures),
            'note': 'Weighted by position size'
        }

    def _generate_portfolio_recommendations(self, analysis: Dict) -> List[str]:
        """Generate risk management recommendations based on portfolio analysis"""
        recommendations = []

        # Concentration recommendations
        conc_flags = analysis.get('concentration', {}).get('flags', [])
        if conc_flags:
            recommendations.append("Consider reducing largest positions to improve diversification")

        # Correlation recommendations
        corr_flags = analysis.get('correlations', {}).get('flags', [])
        if corr_flags:
            recommendations.append("High sector concentration detected - diversify across sectors")

        # Macro sensitivity recommendations
        top_exposures = analysis.get('macro_sensitivity', {}).get('top_exposures', [])
        if top_exposures and top_exposures[0][1] > 0.5:
            recommendations.append(f"High exposure to {top_exposures[0][0]} - consider hedging")

        if not recommendations:
            recommendations.append("Portfolio shows reasonable diversification")

        return recommendations
