#!/usr/bin/env python3
"""
Configuration Package - Phase 2.4

Centralized constants for financial calculations and system configuration.
Eliminates magic numbers throughout the codebase.
"""

from .financial_constants import FinancialConstants, FinancialFormulas
from .system_constants import SystemConstants

__all__ = [
    'FinancialConstants',
    'FinancialFormulas',
    'SystemConstants',
]
