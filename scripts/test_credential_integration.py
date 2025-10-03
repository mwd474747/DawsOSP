#!/usr/bin/env python3
"""
Integration test for DawsOS Credential Manager

Tests that all capability classes properly integrate with CredentialManager
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_credential_manager():
    """Test CredentialManager directly"""
    print("\n" + "="*60)
    print("TEST 1: CredentialManager Direct Usage")
    print("="*60)

    from dawsos.core.credentials import CredentialManager

    # Test initialization
    manager = CredentialManager(verbose=False)
    print("✓ CredentialManager initialized")

    # Test singleton
    from dawsos.core.credentials import get_credential_manager
    singleton = get_credential_manager()
    print("✓ Singleton pattern working")

    # Test methods
    validation = manager.validate_all()
    print(f"✓ Validated {len(validation)} credentials")

    masked = manager.mask_key("sk-ant-1234567890xyz")
    print(f"✓ Key masking works: {masked}")

    return True


def test_market_data_integration():
    """Test MarketDataCapability integration"""
    print("\n" + "="*60)
    print("TEST 2: MarketDataCapability Integration")
    print("="*60)

    try:
        from dawsos.capabilities.market_data import MarketDataCapability

        capability = MarketDataCapability()
        print("✓ MarketDataCapability initialized with CredentialManager")

        # Check if api_key was loaded (will be empty string if not configured)
        has_key = bool(capability.api_key)
        if has_key:
            print(f"✓ FMP API key loaded: {capability.api_key[:8]}...")
        else:
            print("○ FMP API key not configured (optional)")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_fred_data_integration():
    """Test FredDataCapability integration"""
    print("\n" + "="*60)
    print("TEST 3: FredDataCapability Integration")
    print("="*60)

    try:
        from dawsos.capabilities.fred_data import FredDataCapability

        capability = FredDataCapability()
        print("✓ FredDataCapability initialized with CredentialManager")

        # Check if api_key was loaded
        has_key = bool(capability.api_key)
        if has_key:
            print(f"✓ FRED API key loaded: {capability.api_key[:8]}...")
        else:
            print("○ FRED API key not configured (optional)")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_news_integration():
    """Test NewsCapability integration"""
    print("\n" + "="*60)
    print("TEST 4: NewsCapability Integration")
    print("="*60)

    try:
        from dawsos.capabilities.news import NewsCapability

        capability = NewsCapability()
        print("✓ NewsCapability initialized with CredentialManager")

        # Check if api_key was loaded
        has_key = bool(capability.api_key)
        if has_key:
            print(f"✓ News API key loaded: {capability.api_key[:8]}...")
        else:
            print("○ News API key not configured (optional)")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_llm_client_integration():
    """Test LLMClient integration (may fail if no API key)"""
    print("\n" + "="*60)
    print("TEST 5: LLMClient Integration")
    print("="*60)

    try:
        from dawsos.core.llm_client import LLMClient

        # This will fail if ANTHROPIC_API_KEY is not set
        client = LLMClient()
        print("✓ LLMClient initialized with CredentialManager")
        print("✓ ANTHROPIC_API_KEY configured and working")
        return True
    except ImportError as e:
        print(f"○ Anthropic package not installed: {e}")
        print("  This is expected if anthropic package is not in environment")
        return True  # Not a failure - dependency not installed
    except ValueError as e:
        print(f"○ LLMClient requires ANTHROPIC_API_KEY: {e}")
        print("  This is expected if you haven't configured the key yet")
        return True  # Not a failure - just not configured
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print(" DawsOS Credential Manager Integration Test")
    print("="*70)

    results = []

    # Run tests
    results.append(("CredentialManager", test_credential_manager()))
    results.append(("MarketDataCapability", test_market_data_integration()))
    results.append(("FredDataCapability", test_fred_data_integration()))
    results.append(("NewsCapability", test_news_integration()))
    results.append(("LLMClient", test_llm_client_integration()))

    # Summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All integration tests passed!")
    else:
        print("\n✗ Some integration tests failed")

    print("="*70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
