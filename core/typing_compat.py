"""
Typing compatibility shim for Python 3.9+

Provides backward-compatible type hints for Python 3.9.
"""
import sys

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    # Python 3.9 compatibility - TypeAlias not available
    # Use type comment style instead
    TypeAlias = type(None)  # Dummy for 3.9

__all__ = ['TypeAlias']
