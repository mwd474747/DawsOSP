"""
Pytest configuration for refactoring tests.

Provides shared fixtures and configuration.
"""

import pytest
import sys
from pathlib import Path

# Ensure dawsos package is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
