#!/usr/bin/env python3
"""
Example: How to Use DawsOS Credential Manager

This script demonstrates various ways to use the CredentialManager
in your DawsOS applications.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dawsos.core.credentials import CredentialManager, get_credential_manager


def example_1_basic_usage():
    """Example 1: Basic usage with CredentialManager"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)

    # Initialize credential manager
    credentials = CredentialManager(verbose=True)

    # Get a credential (with warning if missing)
    api_key = credentials.get('ANTHROPIC_API_KEY', required=True)

    if api_key:
        print(f"\n✓ Got API key: {credentials.mask_key(api_key)}")
    else:
        print("\n○ API key not configured")


def example_2_singleton_pattern():
    """Example 2: Using the singleton pattern"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Singleton Pattern (Recommended)")
    print("="*60)

    # Get singleton instance (no validation output)
    credentials = get_credential_manager()

    # Get credentials without warnings
    anthropic_key = credentials.get_raw('ANTHROPIC_API_KEY')
    fmp_key = credentials.get_raw('FMP_API_KEY')

    print(f"Anthropic: {credentials.mask_key(anthropic_key) if anthropic_key else 'not set'}")
    print(f"FMP:       {credentials.mask_key(fmp_key) if fmp_key else 'not set'}")


def example_3_conditional_features():
    """Example 3: Conditional features based on available credentials"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Conditional Features")
    print("="*60)

    credentials = get_credential_manager()

    # Check which features are available
    features = {
        'Claude API': credentials.has_credential('ANTHROPIC_API_KEY'),
        'Market Data': credentials.has_credential('FMP_API_KEY'),
        'Economic Data': credentials.has_credential('FRED_API_KEY'),
        'News': credentials.has_credential('NEWSAPI_KEY'),
    }

    print("\nAvailable Features:")
    for feature, available in features.items():
        status = "✓" if available else "○"
        print(f"  {status} {feature}")

    # Enable features conditionally
    if credentials.has_credential('FMP_API_KEY'):
        print("\n✓ Market data capability enabled")
    else:
        print("\n○ Market data capability not available (no API key)")


def example_4_validation():
    """Example 4: Validate all credentials"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Credential Validation")
    print("="*60)

    credentials = get_credential_manager()

    # Validate all
    validation = credentials.validate_all()

    print("\nCredential Status:")
    for key, is_available in validation.items():
        status = "✓" if is_available else "○"
        masked = credentials.mask_key(credentials.get_raw(key))
        value = masked if masked else "(not configured)"
        print(f"  {status} {key:25} {value}")

    # Summary
    total = len(validation)
    available = sum(validation.values())
    print(f"\nSummary: {available}/{total} credentials configured")


def example_5_custom_capability():
    """Example 5: Creating a custom capability with CredentialManager"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Custom Capability Class")
    print("="*60)

    class MyCustomCapability:
        """Example custom capability using CredentialManager"""

        def __init__(self):
            # Get credentials in __init__
            credentials = get_credential_manager()
            self.api_key = credentials.get('FMP_API_KEY', required=False)

        def is_available(self) -> bool:
            """Check if this capability can be used"""
            return bool(self.api_key)

        def do_something(self):
            """Example method"""
            if not self.is_available():
                print("  ○ Feature not available (missing API key)")
                return

            # Use the API key
            print(f"  ✓ Using API key: {self.api_key[:8]}...")

    # Use the custom capability
    print("\nCreating custom capability:")
    capability = MyCustomCapability()
    capability.do_something()


def example_6_error_handling():
    """Example 6: Proper error handling"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Error Handling")
    print("="*60)

    credentials = get_credential_manager()

    # Graceful handling of missing credentials
    def use_market_data():
        """Function that needs market data API"""
        api_key = credentials.get('FMP_API_KEY', required=False)

        if not api_key:
            print("  ⚠ Market data not available: missing FMP_API_KEY")
            print("  → Using fallback data source or cached data")
            return False

        print(f"  ✓ Market data available with key: {credentials.mask_key(api_key)}")
        return True

    print("\nAttempting to use market data:")
    success = use_market_data()

    if not success:
        print("\n  Continuing with limited functionality...")


def example_7_masking_for_logs():
    """Example 7: Masking keys for safe logging"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Safe Logging with Key Masking")
    print("="*60)

    credentials = get_credential_manager()

    # NEVER do this - logs full key!
    # print(f"API Key: {api_key}")  # ✗ BAD

    # ALWAYS mask keys for logging
    api_key = credentials.get_raw('ANTHROPIC_API_KEY')
    if api_key:
        masked = credentials.mask_key(api_key)
        print(f"✓ Safe log: API Key: {masked}")  # ✓ GOOD
    else:
        print("○ No API key to log")

    # Mask any credential
    test_key = "sk-ant-1234567890abcdefghijklmnopqrstuvwxyz"
    masked_test = credentials.mask_key(test_key)
    print(f"✓ Masked example: {masked_test}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print(" DawsOS Credential Manager - Usage Examples")
    print("="*70)

    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Singleton Pattern", example_2_singleton_pattern),
        ("Conditional Features", example_3_conditional_features),
        ("Validation", example_4_validation),
        ("Custom Capability", example_5_custom_capability),
        ("Error Handling", example_6_error_handling),
        ("Safe Logging", example_7_masking_for_logs),
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")

    print("\n" + "="*70)
    print("Examples complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
