"""
Legacy load_env compatibility shim
Replaced with standard python-dotenv for Trinity 3.0

This file exists only for backward compatibility with old scripts.
New code should use: from dotenv import load_dotenv; load_dotenv()
"""

from dotenv import load_dotenv

def load_env():
    """Load .env file using python-dotenv"""
    load_dotenv()
    return True

# Auto-load on import (for scripts that just import this module)
load_dotenv()
