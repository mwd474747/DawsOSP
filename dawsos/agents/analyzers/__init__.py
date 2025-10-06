"""
Financial Analyzers - Modular components for financial analysis

This package contains specialized analyzer classes extracted from
the FinancialAnalyst god object as part of Phase 2 refactoring.

Each analyzer focuses on a specific type of analysis:
- DCFAnalyzer: DCF valuation calculations
- MoatAnalyzer: Competitive moat analysis
- FinancialDataFetcher: Financial data aggregation
- FinancialConfidenceCalculator: Confidence scoring

These analyzers use composition to provide focused, testable functionality
while maintaining backward compatibility through the FinancialAnalyst orchestrator.
"""

__all__ = [
    'DCFAnalyzer',
    'MoatAnalyzer',
    'FinancialDataFetcher',
]

from .dcf_analyzer import DCFAnalyzer
from .moat_analyzer import MoatAnalyzer
from .financial_data_fetcher import FinancialDataFetcher
