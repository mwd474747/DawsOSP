"""
FMP Fundamentals to Ratings Transformer

Purpose: Transform FMP API response format to rating-ready metrics
Created: 2025-11-02 for buffett_checklist pattern integration

Transforms raw FMP data (income_statement, balance_sheet, cash_flow) into
the specific metrics needed by RatingsService:
- dividend_safety: payout ratios, FCF coverage, dividend history  
- moat_strength: ROE, margins, intangibles
- resilience: debt ratios, liquidity, margin stability
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
import statistics

logger = logging.getLogger("DawsOS.FundamentalsTransformer")


def transform_fmp_to_ratings_format(fmp_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform FMP fundamentals response to ratings-ready metrics.
    
    Args:
        fmp_data: Dict with keys:
            - symbol: str
            - income_statement: List[Dict] (newest first)
            - balance_sheet: List[Dict] (newest first) 
            - cash_flow: List[Dict] (newest first)
            
    Returns:
        Dict with all metrics needed for ratings calculations:
            - payout_ratio_5y_avg: Decimal
            - fcf_dividend_coverage: Decimal
            - dividend_growth_streak_years: int
            - net_cash_position: Decimal
            - roe_5y_avg: Decimal
            - gross_margin_5y_avg: Decimal
            - intangible_assets_ratio: Decimal
            - switching_cost_score: Decimal (default 5)
            - debt_equity_ratio: Decimal
            - interest_coverage: Decimal
            - current_ratio: Decimal
            - operating_margin_std_dev: Decimal
    """
    result = {
        "symbol": fmp_data.get("symbol", ""),
    }
    
    # Extract statement lists
    income_stmts = fmp_data.get("income_statement", [])
    balance_sheets = fmp_data.get("balance_sheet", [])
    cash_flows = fmp_data.get("cash_flow", [])
    
    # Handle empty data gracefully
    if not income_stmts or not balance_sheets or not cash_flows:
        logger.warning(f"Missing financial statements for {result['symbol']}")
        return _get_default_metrics(result["symbol"])
    
    try:
        # === DIVIDEND SAFETY METRICS ===
        
        # 1. Payout Ratio (5-year average)
        payout_ratios = []
        for stmt, cf in zip(income_stmts[:5], cash_flows[:5]):
            net_income = _safe_decimal(stmt.get("netIncome", 0))
            dividends_paid = abs(_safe_decimal(cf.get("dividendsPaid", 0)))
            if net_income > 0 and dividends_paid > 0:
                payout_ratios.append(dividends_paid / net_income)
        
        result["payout_ratio_5y_avg"] = (
            sum(payout_ratios) / len(payout_ratios) if payout_ratios 
            else Decimal("0.5")  # Default 50% if no data
        )
        
        # 2. FCF Dividend Coverage 
        latest_cf = cash_flows[0] if cash_flows else {}
        fcf = _safe_decimal(latest_cf.get("freeCashFlow", 0))
        dividends = abs(_safe_decimal(latest_cf.get("dividendsPaid", 0)))
        
        if dividends > 0 and fcf > 0:
            result["fcf_dividend_coverage"] = fcf / dividends
        else:
            result["fcf_dividend_coverage"] = Decimal("1.5")  # Default coverage
        
        # 3. Dividend Growth Streak (count consecutive years of growth)
        dividend_history = []
        for cf in cash_flows[:10]:  # Look at up to 10 years
            div = abs(_safe_decimal(cf.get("dividendsPaid", 0)))
            dividend_history.append(div)
        
        streak = 0
        for i in range(1, len(dividend_history)):
            if dividend_history[i-1] > dividend_history[i]:
                streak += 1
            else:
                break
        result["dividend_growth_streak_years"] = streak
        
        # 4. Net Cash Position (cash - total debt)
        latest_bs = balance_sheets[0] if balance_sheets else {}
        cash = _safe_decimal(latest_bs.get("cashAndCashEquivalents", 0))
        total_debt = _safe_decimal(latest_bs.get("totalDebt", 0))
        result["net_cash_position"] = cash - total_debt
        
        # === MOAT STRENGTH METRICS ===
        
        # 1. ROE (5-year average)
        roe_values = []
        for stmt, bs in zip(income_stmts[:5], balance_sheets[:5]):
            net_income = _safe_decimal(stmt.get("netIncome", 0))
            shareholders_equity = _safe_decimal(bs.get("totalStockholdersEquity", 0))
            if shareholders_equity > 0:
                roe = net_income / shareholders_equity
                roe_values.append(roe)
        
        result["roe_5y_avg"] = (
            sum(roe_values) / len(roe_values) if roe_values
            else Decimal("0.10")  # Default 10% ROE
        )
        
        # 2. Gross Margin (5-year average)
        gross_margins = []
        for stmt in income_stmts[:5]:
            revenue = _safe_decimal(stmt.get("revenue", 0))
            gross_profit = _safe_decimal(stmt.get("grossProfit", 0))
            if revenue > 0:
                margin = gross_profit / revenue
                gross_margins.append(margin)
        
        result["gross_margin_5y_avg"] = (
            sum(gross_margins) / len(gross_margins) if gross_margins
            else Decimal("0.30")  # Default 30% margin
        )
        
        # 3. Intangible Assets Ratio
        intangibles = _safe_decimal(latest_bs.get("intangibleAssets", 0))
        goodwill = _safe_decimal(latest_bs.get("goodwill", 0))
        total_assets = _safe_decimal(latest_bs.get("totalAssets", 0))
        
        if total_assets > 0:
            result["intangible_assets_ratio"] = (intangibles + goodwill) / total_assets
        else:
            result["intangible_assets_ratio"] = Decimal("0.10")  # Default 10%
            
        # 4. Switching Cost Score (qualitative, default)
        result["switching_cost_score"] = Decimal("5")  # Mid-range default
        
        # === RESILIENCE METRICS ===
        
        # 1. Debt-to-Equity Ratio
        total_debt = _safe_decimal(latest_bs.get("totalDebt", 0))
        equity = _safe_decimal(latest_bs.get("totalStockholdersEquity", 0))
        
        if equity > 0:
            result["debt_equity_ratio"] = total_debt / equity
        else:
            result["debt_equity_ratio"] = Decimal("1.0")  # Default 1.0
            
        # 2. Interest Coverage
        latest_stmt = income_stmts[0] if income_stmts else {}
        ebit = _safe_decimal(latest_stmt.get("operatingIncome", 0))
        interest_expense = abs(_safe_decimal(latest_stmt.get("interestExpense", 0)))
        
        if interest_expense > 0 and ebit > 0:
            result["interest_coverage"] = ebit / interest_expense
        else:
            result["interest_coverage"] = Decimal("5.0")  # Default healthy coverage
            
        # 3. Current Ratio
        current_assets = _safe_decimal(latest_bs.get("totalCurrentAssets", 0))
        current_liabilities = _safe_decimal(latest_bs.get("totalCurrentLiabilities", 0))
        
        if current_liabilities > 0:
            result["current_ratio"] = current_assets / current_liabilities
        else:
            result["current_ratio"] = Decimal("1.5")  # Default healthy ratio
            
        # 4. Operating Margin Stability (standard deviation over 5 years)
        operating_margins = []
        for stmt in income_stmts[:5]:
            revenue = _safe_decimal(stmt.get("revenue", 0))
            operating_income = _safe_decimal(stmt.get("operatingIncome", 0))
            if revenue > 0:
                margin = operating_income / revenue
                operating_margins.append(float(margin))
        
        if len(operating_margins) >= 2:
            std_dev = statistics.stdev(operating_margins)
            result["operating_margin_std_dev"] = Decimal(str(std_dev))
        else:
            result["operating_margin_std_dev"] = Decimal("0.05")  # Default 5% std dev
            
    except Exception as e:
        logger.error(f"Error transforming fundamentals for {result['symbol']}: {e}", exc_info=True)
        return _get_default_metrics(result["symbol"])
    
    # Log the transformation
    logger.info(f"Transformed FMP data for {result['symbol']}: "
                f"payout={result['payout_ratio_5y_avg']:.2f}, "
                f"ROE={result['roe_5y_avg']:.2f}, "
                f"D/E={result['debt_equity_ratio']:.2f}")
    
    return result


def _safe_decimal(value: Any) -> Decimal:
    """Safely convert a value to Decimal, handling None and invalid values."""
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return Decimal("0")


def _get_default_metrics(symbol: str) -> Dict[str, Any]:
    """
    Return conservative default metrics when data is unavailable.
    
    These defaults produce mid-range ratings (~5/10) to avoid
    misleading extremely good or bad ratings with no data.
    """
    logger.warning(f"Using default metrics for {symbol} due to missing/invalid data")
    
    return {
        "symbol": symbol,
        # Dividend Safety defaults (will score ~5/10)
        "payout_ratio_5y_avg": Decimal("0.50"),  # 50% payout
        "fcf_dividend_coverage": Decimal("1.5"),  # 1.5x coverage
        "dividend_growth_streak_years": 3,  # 3 years
        "net_cash_position": Decimal("500000000"),  # $500M
        
        # Moat Strength defaults (will score ~5/10)
        "roe_5y_avg": Decimal("0.12"),  # 12% ROE
        "gross_margin_5y_avg": Decimal("0.30"),  # 30% margin
        "intangible_assets_ratio": Decimal("0.10"),  # 10% intangibles
        "switching_cost_score": Decimal("5"),  # Mid-range
        
        # Resilience defaults (will score ~5/10)
        "debt_equity_ratio": Decimal("1.0"),  # 1.0 D/E
        "interest_coverage": Decimal("3.0"),  # 3x coverage
        "current_ratio": Decimal("1.2"),  # 1.2 current
        "operating_margin_std_dev": Decimal("0.07"),  # 7% std dev
    }