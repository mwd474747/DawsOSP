"""
Symbol Normalization Utilities

Purpose: Handle symbol format conversions between database storage and external API providers
Created: 2025-11-06
Priority: P0 (Critical for FMP API integration)

Symbol Format Rules:
    Database Storage: Preserve original format (BRK.B, RY.TO, AAPL)
    FMP API: Hyphens for share classes (BRK-B), dots for exchanges (RY.TO)
    News Search: Hyphens for all dots (BRK-B, RY-TO)

Examples:
    # FMP API calls
    fmp_symbol = normalize_symbol_for_fmp("BRK.B")  # Returns "BRK-B"
    fmp_symbol = normalize_symbol_for_fmp("RY.TO")  # Returns "RY.TO"
    fmp_symbol = normalize_symbol_for_fmp("AAPL")   # Returns "AAPL"

    # News search
    news_symbol = normalize_symbol_for_news("BRK.B")  # Returns "BRK-B"
    news_symbol = normalize_symbol_for_news("RY.TO")  # Returns "RY-TO"
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Known exchange suffixes that use dots
EXCHANGE_SUFFIXES = {
    # Canadian exchanges
    ".TO",   # Toronto Stock Exchange
    ".V",    # TSX Venture Exchange
    ".CN",   # Canadian Securities Exchange

    # European exchanges
    ".L",    # London Stock Exchange
    ".PA",   # Euronext Paris
    ".AS",   # Euronext Amsterdam
    ".BR",   # Euronext Brussels
    ".DE",   # Deutsche Börse (Frankfurt)
    ".F",    # Frankfurt Stock Exchange
    ".SW",   # SIX Swiss Exchange
    ".MI",   # Borsa Italiana (Milan)
    ".MC",   # Bolsa de Madrid

    # Asian exchanges
    ".HK",   # Hong Kong Stock Exchange
    ".T",    # Tokyo Stock Exchange
    ".KS",   # Korea Stock Exchange
    ".SI",   # Singapore Exchange
    ".AX",   # Australian Securities Exchange

    # Other
    ".ME",   # Moscow Exchange
    ".SA",   # Bovespa (São Paulo)
}

# Share class suffixes (single letter after dot)
SHARE_CLASS_PATTERN = re.compile(r'\.([A-Z])$')


def normalize_symbol_for_fmp(symbol: str) -> str:
    """
    Normalize symbol for Financial Modeling Prep (FMP) API.

    FMP API Rules:
    - Share classes use hyphens: BRK.B -> BRK-B
    - Exchange suffixes use dots: RY.TO -> RY.TO (unchanged)
    - Standard symbols unchanged: AAPL -> AAPL

    Args:
        symbol: Raw symbol from database (e.g., "BRK.B", "RY.TO", "AAPL")

    Returns:
        FMP-formatted symbol (e.g., "BRK-B", "RY.TO", "AAPL")

    Examples:
        >>> normalize_symbol_for_fmp("BRK.B")
        'BRK-B'
        >>> normalize_symbol_for_fmp("BRK.A")
        'BRK-A'
        >>> normalize_symbol_for_fmp("RY.TO")
        'RY.TO'
        >>> normalize_symbol_for_fmp("TD.TO")
        'TD.TO'
        >>> normalize_symbol_for_fmp("AAPL")
        'AAPL'
        >>> normalize_symbol_for_fmp("GOOGL")
        'GOOGL'
    """
    if not symbol or "." not in symbol:
        return symbol

    # Check if symbol ends with known exchange suffix
    for exchange_suffix in EXCHANGE_SUFFIXES:
        if symbol.upper().endswith(exchange_suffix.upper()):
            # Exchange suffix - keep the dot
            logger.debug(f"Symbol {symbol} has exchange suffix {exchange_suffix}, keeping dot")
            return symbol

    # Check if it's a share class (single letter after dot)
    if SHARE_CLASS_PATTERN.search(symbol.upper()):
        # Share class - convert dot to hyphen
        fmp_symbol = symbol.replace(".", "-")
        logger.debug(f"Symbol {symbol} has share class suffix, converting to {fmp_symbol}")
        return fmp_symbol

    # If we can't determine, log warning and keep original
    logger.warning(
        f"Symbol {symbol} contains dot but doesn't match known patterns. "
        f"Keeping original format. If this causes API errors, add suffix to EXCHANGE_SUFFIXES."
    )
    return symbol


def normalize_symbol_for_news(symbol: str) -> str:
    """
    Normalize symbol for news search APIs.

    News APIs typically use hyphens instead of dots for better search matching.

    Args:
        symbol: Raw symbol from database (e.g., "BRK.B", "RY.TO")

    Returns:
        News-formatted symbol with all dots converted to hyphens

    Examples:
        >>> normalize_symbol_for_news("BRK.B")
        'BRK-B'
        >>> normalize_symbol_for_news("RY.TO")
        'RY-TO'
        >>> normalize_symbol_for_news("AAPL")
        'AAPL'
    """
    if not symbol:
        return symbol

    # For news search, convert all dots to hyphens
    return symbol.replace(".", "-")


def normalize_symbol_for_storage(symbol: str) -> str:
    """
    Normalize symbol for database storage.

    Storage Rules:
    - Uppercase
    - Trim whitespace
    - Preserve dots (for exchange suffixes and share classes)

    Args:
        symbol: Raw symbol input (e.g., "brk.b", " RY.TO ", "aapl")

    Returns:
        Normalized symbol for database storage

    Examples:
        >>> normalize_symbol_for_storage("brk.b")
        'BRK.B'
        >>> normalize_symbol_for_storage(" RY.TO ")
        'RY.TO'
        >>> normalize_symbol_for_storage("aapl")
        'AAPL'
    """
    if not symbol:
        return symbol

    # Uppercase and trim
    normalized = symbol.strip().upper()

    logger.debug(f"Normalized symbol for storage: {symbol} -> {normalized}")
    return normalized


def validate_symbol(symbol: str) -> tuple[bool, Optional[str]]:
    """
    Validate symbol format.

    Validation Rules:
    - Length: 1-10 characters
    - Characters: A-Z, 0-9, dots only
    - At least one letter
    - Dot not at start or end

    Args:
        symbol: Symbol to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, None)
        If invalid: (False, "error description")

    Examples:
        >>> validate_symbol("AAPL")
        (True, None)
        >>> validate_symbol("BRK.B")
        (True, None)
        >>> validate_symbol("RY.TO")
        (True, None)
        >>> validate_symbol("")
        (False, 'Symbol cannot be empty')
        >>> validate_symbol("TOOLONGSYMBOL123")
        (False, 'Symbol too long (max 10 characters)')
        >>> validate_symbol(".AAPL")
        (False, 'Symbol cannot start or end with a dot')
        >>> validate_symbol("123")
        (False, 'Symbol must contain at least one letter')
    """
    if not symbol:
        return (False, "Symbol cannot be empty")

    symbol = symbol.strip()

    # Length check
    if len(symbol) > 10:
        return (False, "Symbol too long (max 10 characters)")

    # Character check
    if not re.match(r'^[A-Z0-9.]+$', symbol, re.IGNORECASE):
        return (False, "Symbol can only contain letters, numbers, and dots")

    # Must have at least one letter
    if not re.search(r'[A-Z]', symbol, re.IGNORECASE):
        return (False, "Symbol must contain at least one letter")

    # Dot position check
    if symbol.startswith(".") or symbol.endswith("."):
        return (False, "Symbol cannot start or end with a dot")

    # No consecutive dots
    if ".." in symbol:
        return (False, "Symbol cannot have consecutive dots")

    return (True, None)


def detect_symbol_type(symbol: str) -> str:
    """
    Detect the type of symbol.

    Returns:
        "share_class" - Symbol with share class suffix (e.g., BRK.B)
        "exchange" - Symbol with exchange suffix (e.g., RY.TO)
        "standard" - Standard symbol with no suffix (e.g., AAPL)

    Examples:
        >>> detect_symbol_type("BRK.B")
        'share_class'
        >>> detect_symbol_type("RY.TO")
        'exchange'
        >>> detect_symbol_type("AAPL")
        'standard'
    """
    if not symbol or "." not in symbol:
        return "standard"

    # Check for exchange suffix
    for exchange_suffix in EXCHANGE_SUFFIXES:
        if symbol.upper().endswith(exchange_suffix.upper()):
            return "exchange"

    # Check for share class
    if SHARE_CLASS_PATTERN.search(symbol.upper()):
        return "share_class"

    return "standard"
