#!/usr/bin/env python3
"""
Financial Constants - Phase 2.4

Centralized financial calculation constants and assumptions.
Eliminates magic numbers throughout the codebase for better
maintainability and self-documenting code.

All constants are well-documented with sources and rationale.
"""

from typing import List


class FinancialConstants:
    """Financial calculation constants and market assumptions"""

    # ==================== MARKET ASSUMPTIONS ====================

    # Risk-free rate (10-year US Treasury yield as of 2024)
    RISK_FREE_RATE = 0.045  # 4.5%

    # Market risk premium (historical equity premium)
    # Source: Damodaran, Ibbotson SBBI
    MARKET_RISK_PREMIUM = 0.06  # 6%

    # Default discount rate (WACC) when calculation fails
    DEFAULT_DISCOUNT_RATE = 0.10  # 10%

    # Default beta for unknown companies
    DEFAULT_BETA = 1.0  # Market beta

    # ==================== GROWTH RATE SCENARIOS ====================

    # Conservative growth scenario (mature, stable companies)
    CONSERVATIVE_GROWTH_RATES: List[float] = [0.08, 0.06, 0.05, 0.04, 0.03]

    # Moderate growth scenario (balanced growth companies)
    MODERATE_GROWTH_RATES: List[float] = [0.12, 0.10, 0.08, 0.06, 0.04]

    # Aggressive growth scenario (high-growth companies)
    AGGRESSIVE_GROWTH_RATES: List[float] = [0.20, 0.15, 0.12, 0.10, 0.08]

    # Default growth rates (used in DCF if not specified)
    DEFAULT_GROWTH_RATES: List[float] = CONSERVATIVE_GROWTH_RATES

    # Terminal growth rate (perpetuity assumption)
    TERMINAL_GROWTH_RATE = 0.03  # 3% (long-term GDP growth)

    # ==================== VALUATION THRESHOLDS ====================

    # Moat rating thresholds (0-50 scale)
    WIDE_MOAT_THRESHOLD = 30.0  # Score > 30 = Wide moat
    NARROW_MOAT_THRESHOLD = 15.0  # Score 15-30 = Narrow moat
    # Score < 15 = No moat

    # Individual moat factor thresholds (0-10 each)
    BRAND_MOAT_GROSS_MARGIN_THRESHOLD = 0.50  # >50% gross margin
    NETWORK_EFFECTS_GROWTH_THRESHOLD = 0.20  # >20% revenue growth
    COST_ADVANTAGES_MARGIN_THRESHOLD = 0.20  # >20% operating margin
    SWITCHING_COSTS_RECURRING_THRESHOLD = 0.70  # >70% recurring revenue

    # Moat factor multipliers
    BRAND_MOAT_MULTIPLIER = 15.0  # gross_margin * 15 = brand score
    NETWORK_EFFECTS_MULTIPLIER = 30.0  # revenue_growth * 30 = network score
    COST_ADVANTAGES_MULTIPLIER = 30.0  # operating_margin * 30 = cost score
    SWITCHING_COSTS_BASE_SCORE = 8.0  # Fixed score if threshold met

    # DCF margin of safety
    MINIMUM_MARGIN_OF_SAFETY = 0.25  # 25% discount to intrinsic value

    # ==================== TAX ASSUMPTIONS ====================

    # US corporate tax rate (Tax Cuts and Jobs Act of 2017)
    CORPORATE_TAX_RATE = 0.21  # 21%

    # ==================== ROIC THRESHOLDS ====================

    # ROIC predictability thresholds
    STRONG_ROIC_THRESHOLD = 0.15  # >15% indicates predictable business
    WEAK_ROIC_THRESHOLD = 0.05  # <5% indicates unpredictable business

    # ROIC predictability adjustments
    STRONG_ROIC_PREDICTABILITY_BONUS = 0.1  # +0.1 to predictability
    WEAK_ROIC_PREDICTABILITY_PENALTY = 0.1  # -0.1 to predictability

    # ==================== LEVERAGE THRESHOLDS ====================

    # Debt-to-Equity ratio thresholds
    HIGH_LEVERAGE_THRESHOLD = 1.0  # D/E > 1.0 = high leverage
    LOW_LEVERAGE_THRESHOLD = 0.3  # D/E < 0.3 = conservative leverage

    # Leverage predictability adjustments
    HIGH_LEVERAGE_PREDICTABILITY_PENALTY = 0.1  # -0.1 to predictability
    LOW_LEVERAGE_PREDICTABILITY_BONUS = 0.05  # +0.05 to predictability

    # Default D/E ratio when unknown
    DEFAULT_DEBT_TO_EQUITY = 0.5  # Moderate leverage

    # ==================== CONFIDENCE SCORING ====================

    # Base predictability score
    BASE_PREDICTABILITY = 0.7  # 70% base predictability

    # Predictability bounds
    MIN_PREDICTABILITY = 0.3  # 30% minimum
    MAX_PREDICTABILITY = 1.0  # 100% maximum

    # Data quality scoring
    DEFAULT_DATA_QUALITY = 0.6  # 60% when cannot assess
    GOOD_CONSISTENCY_SCORE = 0.8  # 80% for consistent data
    CONSISTENCY_COMPLETENESS_WEIGHT = (0.6, 0.4)  # Weights for DQ components

    # FCF/Net Income consistency threshold
    FCF_NI_RATIO_THRESHOLD = 3.0  # Flag if FCF/NI > 3.0
    FCF_NI_CONSISTENCY_PENALTY = 0.2  # -0.2 to consistency score

    # Historical success rate for DCF
    DCF_HISTORICAL_SUCCESS_RATE = 0.68  # 68% (from knowledge base)

    # Confidence thresholds
    MINIMUM_CONFIDENCE_SCORE = 0.5  # 50% minimum confidence
    HIGH_CONFIDENCE_THRESHOLD = 0.8  # 80% = high confidence

    # ==================== DCF PROJECTION PARAMETERS ====================

    # Number of years to project cash flows
    DCF_PROJECTION_YEARS = 5  # Industry standard

    # Number of stages in DCF (projection + terminal)
    DCF_STAGES = 2  # Projection period + terminal value

    # ==================== SECTORS WITH NETWORK EFFECTS ====================

    # Sectors likely to have network effects
    NETWORK_EFFECTS_SECTORS = ['Technology', 'Communication Services']


class FinancialFormulas:
    """
    Financial calculation formulas as constants.

    These are not configurable but serve as documentation
    of the formulas used throughout the system.
    """

    # WACC = (E/V × Re) + (D/V × Rd × (1-Tc))
    # where E = equity, D = debt, V = total value, Re = cost of equity,
    # Rd = cost of debt, Tc = corporate tax rate
    WACC_FORMULA = "WACC = (E/V × Re) + (D/V × Rd × (1-Tc))"

    # CAPM: Re = Rf + β × (Rm - Rf)
    # where Re = cost of equity, Rf = risk-free rate,
    # β = beta, Rm = market return
    CAPM_FORMULA = "Re = Rf + β × (Rm - Rf)"

    # ROIC = NOPAT / Invested Capital
    # where NOPAT = EBIT × (1 - Tax Rate)
    # Invested Capital = Working Capital + PPE + Goodwill
    ROIC_FORMULA = "ROIC = NOPAT / Invested Capital"

    # Terminal Value = (FCF_final × (1 + g)) / (r - g)
    # where g = terminal growth rate, r = discount rate
    TERMINAL_VALUE_FORMULA = "TV = (FCF_final × (1 + g)) / (r - g)"

    # Owner Earnings = Net Income + D&A - CapEx - Working Capital Changes
    OWNER_EARNINGS_FORMULA = "Owner Earnings = NI + D&A - CapEx - ΔWC"

    # Free Cash Flow = Operating Cash Flow - Capital Expenditures
    FCF_FORMULA = "FCF = OCF - CapEx"
