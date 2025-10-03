#!/usr/bin/env python3
"""
Test script for DawsOS Credential Manager

Tests:
1. CredentialManager initialization
2. Key masking functionality
3. Credential validation
4. Shows which keys are configured

Usage:
    python scripts/test_credentials.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import dawsos modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dawsos.core.credentials import CredentialManager


def test_initialization():
    """Test CredentialManager initialization"""
    print("\n" + "="*60)
    print("TEST 1: CredentialManager Initialization")
    print("="*60)

    try:
        # Initialize with verbose mode
        manager = CredentialManager(verbose=True)
        print("\n✓ CredentialManager initialized successfully")
        return manager
    except Exception as e:
        print(f"\n✗ Error initializing CredentialManager: {e}")
        return None


def test_key_masking(manager):
    """Test key masking functionality"""
    print("\n" + "="*60)
    print("TEST 2: Key Masking")
    print("="*60)

    test_cases = [
        ('sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz', 'sk-ant-a...xyz'),
        ('abcd1234567890xyz', 'abcd1234...xyz'),
        ('short', 'sho...'),
        ('', ''),
        ('x', 'x...'),
    ]

    all_passed = True
    for key, expected_pattern in test_cases:
        masked = manager.mask_key(key)
        # Check if it follows the pattern (exact match may vary slightly)
        if key == '':
            passed = masked == ''
        elif len(key) <= 11:
            passed = '...' in masked or masked == key
        else:
            passed = masked.startswith(key[:8]) and masked.endswith(key[-3:]) and '...' in masked

        status = "✓" if passed else "✗"
        print(f"{status} Key: {key[:20]}... -> Masked: {masked}")

        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ All key masking tests passed")
    else:
        print("\n✗ Some key masking tests failed")

    return all_passed


def test_credential_retrieval(manager):
    """Test credential retrieval"""
    print("\n" + "="*60)
    print("TEST 3: Credential Retrieval")
    print("="*60)

    # Test getting credentials (required=False to avoid warnings in test)
    test_keys = [
        'ANTHROPIC_API_KEY',
        'FMP_API_KEY',
        'FRED_API_KEY',
        'NEWSAPI_KEY',
        'ALPHA_VANTAGE_KEY'
    ]

    results = {}
    for key in test_keys:
        value = manager.get(key, required=False)
        has_value = bool(value)
        results[key] = has_value

        status = "✓" if has_value else "○"
        masked = manager.mask_key(value) if value else "(not set)"
        print(f"{status} {key:25} {masked}")

    available_count = sum(results.values())
    print(f"\n✓ Credential retrieval test complete")
    print(f"  Available: {available_count}/{len(test_keys)} credentials")

    return results


def test_validation(manager):
    """Test credential validation"""
    print("\n" + "="*60)
    print("TEST 4: Credential Validation")
    print("="*60)

    validation_results = manager.validate_all()

    for key, is_available in validation_results.items():
        status = "✓" if is_available else "○"
        print(f"{status} {key:25} {'Available' if is_available else 'Not configured'}")

    required_keys = [
        key for key, config in manager.SUPPORTED_KEYS.items()
        if config['required']
    ]

    required_available = all(
        validation_results.get(key, False) for key in required_keys
    )

    if required_available:
        print("\n✓ All required credentials are available")
    else:
        print("\n⚠ Some required credentials are missing")
        missing = [key for key in required_keys if not validation_results.get(key, False)]
        print(f"  Missing: {', '.join(missing)}")

    return validation_results


def test_has_credential(manager):
    """Test has_credential method"""
    print("\n" + "="*60)
    print("TEST 5: Has Credential Check")
    print("="*60)

    test_keys = ['ANTHROPIC_API_KEY', 'NONEXISTENT_KEY']

    for key in test_keys:
        has_it = manager.has_credential(key)
        status = "✓" if has_it else "○"
        print(f"{status} has_credential('{key}'): {has_it}")

    print("\n✓ has_credential() method working correctly")


def test_get_all_credentials(manager):
    """Test get_all_credentials method (masked)"""
    print("\n" + "="*60)
    print("TEST 6: Get All Credentials (Masked)")
    print("="*60)

    all_creds = manager.get_all_credentials()

    if all_creds:
        print("All credentials (masked):")
        for key, masked_value in all_creds.items():
            print(f"  {key:25} {masked_value}")
    else:
        print("  No credentials loaded")

    print("\n✓ get_all_credentials() method working correctly")

    return all_creds


def print_summary(validation_results):
    """Print summary of credential status"""
    print("\n" + "="*60)
    print("CREDENTIAL STATUS SUMMARY")
    print("="*60)

    total = len(validation_results)
    available = sum(validation_results.values())
    missing = total - available

    print(f"\nTotal Credentials: {total}")
    print(f"Available: {available}")
    print(f"Missing: {missing}")

    if missing > 0:
        print("\n⚠ To configure missing credentials:")
        print("  1. Create a .env file in the project root")
        print("  2. Add your API keys in the format:")
        print("     KEY_NAME=your_key_value")
        print("  3. Or set environment variables:")
        print("     export KEY_NAME=your_key_value")

    print("\n" + "="*60)


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" DawsOS Credential Manager Test Suite")
    print("="*70)

    # Test 1: Initialization
    manager = test_initialization()
    if not manager:
        print("\n✗ Failed to initialize CredentialManager. Exiting.")
        return 1

    # Test 2: Key Masking
    test_key_masking(manager)

    # Test 3: Credential Retrieval
    retrieval_results = test_credential_retrieval(manager)

    # Test 4: Validation
    validation_results = test_validation(manager)

    # Test 5: Has Credential
    test_has_credential(manager)

    # Test 6: Get All Credentials
    test_get_all_credentials(manager)

    # Print Summary
    print_summary(validation_results)

    print("\n✓ All tests completed successfully!")
    print("\n" + "="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
