#!/usr/bin/env python3
"""
Input Validation Utilities for Trinity 2.0
Security hardening - validate and sanitize all user inputs
"""

import re
from typing import Any, List, Optional, Union


class InputValidator:
    """Validates and sanitizes user inputs for security"""

    # Maximum lengths
    MAX_SYMBOL_LENGTH = 10
    MAX_TEXT_LENGTH = 10000
    MAX_LIST_LENGTH = 100

    # Regex patterns
    SYMBOL_PATTERN = re.compile(r'^[A-Z0-9\.\-]{1,10}$')
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\s]+$')

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        Validate stock symbol

        Args:
            symbol: Stock ticker symbol

        Returns:
            True if valid, False otherwise

        Examples:
            >>> InputValidator.validate_symbol("AAPL")
            True
            >>> InputValidator.validate_symbol("INVALID_SYMBOL_TOO_LONG")
            False
        """
        if not symbol or not isinstance(symbol, str):
            return False

        symbol = symbol.strip().upper()

        if len(symbol) > InputValidator.MAX_SYMBOL_LENGTH:
            return False

        if not InputValidator.SYMBOL_PATTERN.match(symbol):
            return False

        return True

    @staticmethod
    def validate_symbols(symbols: Union[str, List[str]]) -> bool:
        """
        Validate list of stock symbols

        Args:
            symbols: Single symbol or list of symbols

        Returns:
            True if all valid, False otherwise
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        if not isinstance(symbols, list):
            return False

        if len(symbols) > InputValidator.MAX_LIST_LENGTH:
            return False

        return all(InputValidator.validate_symbol(s) for s in symbols)

    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize user text input

        Args:
            text: User-provided text
            max_length: Maximum allowed length (default: MAX_TEXT_LENGTH)

        Returns:
            Sanitized text string

        Examples:
            >>> InputValidator.sanitize_text("  Hello World  ")
            'Hello World'
        """
        if not isinstance(text, str):
            return ""

        # Strip whitespace
        text = text.strip()

        # Limit length
        if max_length is None:
            max_length = InputValidator.MAX_TEXT_LENGTH
        text = text[:max_length]

        # Remove potentially dangerous characters
        # Keep alphanumeric, spaces, basic punctuation
        text = re.sub(r'[^\w\s\.,\?!\-\(\)\'\"]+', '', text)

        return text

    @staticmethod
    def validate_numeric(value: Any, min_val: Optional[float] = None,
                        max_val: Optional[float] = None) -> bool:
        """
        Validate numeric input

        Args:
            value: Value to validate
            min_val: Minimum allowed value (optional)
            max_val: Maximum allowed value (optional)

        Returns:
            True if valid, False otherwise
        """
        try:
            num = float(value)

            if min_val is not None and num < min_val:
                return False

            if max_val is not None and num > max_val:
                return False

            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_date(date_str: str) -> bool:
        """
        Validate date string

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(date_str, str):
            return False

        # Check format YYYY-MM-DD
        pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        if not pattern.match(date_str):
            return False

        # Basic sanity check
        try:
            year, month, day = map(int, date_str.split('-'))
            if year < 1900 or year > 2100:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def sanitize_dict(data: dict, allowed_keys: Optional[List[str]] = None) -> dict:
        """
        Sanitize dictionary input

        Args:
            data: Input dictionary
            allowed_keys: List of allowed keys (optional)

        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return {}

        if allowed_keys:
            # Filter to only allowed keys
            sanitized = {k: v for k, v in data.items() if k in allowed_keys}
        else:
            sanitized = data.copy()

        # Sanitize string values
        for key, value in sanitized.items():
            if isinstance(value, str):
                sanitized[key] = InputValidator.sanitize_text(value)

        return sanitized


def validate_symbol(symbol: str) -> bool:
    """Convenience function for symbol validation"""
    return InputValidator.validate_symbol(symbol)


def sanitize_text(text: str) -> str:
    """Convenience function for text sanitization"""
    return InputValidator.sanitize_text(text)


# Example usage
if __name__ == "__main__":
    # Test symbol validation
    print("Symbol Validation:")
    print(f"  AAPL: {InputValidator.validate_symbol('AAPL')}")  # True
    print(f"  INVALID: {InputValidator.validate_symbol('INVALID_SYMBOL_TOO_LONG')}")  # False

    # Test text sanitization
    print("\nText Sanitization:")
    text = "  Hello <script>alert('xss')</script> World!  "
    sanitized = InputValidator.sanitize_text(text)
    print(f"  Original: {text}")
    print(f"  Sanitized: {sanitized}")

    # Test numeric validation
    print("\nNumeric Validation:")
    print(f"  42 (0-100): {InputValidator.validate_numeric(42, 0, 100)}")  # True
    print(f"  150 (0-100): {InputValidator.validate_numeric(150, 0, 100)}")  # False
