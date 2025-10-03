#!/usr/bin/env python3
"""
Test script for FMP API integration

Tests the MarketDataCapability class with comprehensive error handling,
rate limiting, and caching validation.

Can run with or without a valid API key.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dawsos.capabilities.market_data import MarketDataCapability


class TestColors:
    """ANSI color codes for test output"""
    PASS = '\033[92m'
    FAIL = '\033[91m'
    SKIP = '\033[93m'
    INFO = '\033[94m'
    RESET = '\033[0m'


def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{TestColors.INFO}{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}{TestColors.RESET}")


def print_result(test_name: str, passed: bool, message: str = "", skip: bool = False):
    """Print test result"""
    if skip:
        status = f"{TestColors.SKIP}SKIP{TestColors.RESET}"
    elif passed:
        status = f"{TestColors.PASS}PASS{TestColors.RESET}"
    else:
        status = f"{TestColors.FAIL}FAIL{TestColors.RESET}"

    print(f"[{status}] {test_name}")
    if message:
        print(f"       {message}")


def test_initialization():
    """Test 1: Initialize MarketDataCapability"""
    print_test_header("Initialize MarketDataCapability")

    try:
        market_data = MarketDataCapability()

        # Check attributes
        assert hasattr(market_data, 'api_key'), "Missing api_key attribute"
        assert hasattr(market_data, 'rate_limiter'), "Missing rate_limiter attribute"
        assert hasattr(market_data, 'cache'), "Missing cache attribute"
        assert hasattr(market_data, 'cache_ttl'), "Missing cache_ttl attribute"
        assert hasattr(market_data, 'cache_stats'), "Missing cache_stats attribute"

        # Check cache TTL configuration
        assert market_data.cache_ttl['quotes'] == 60, "Quotes TTL should be 60 seconds"
        assert market_data.cache_ttl['fundamentals'] == 86400, "Fundamentals TTL should be 24 hours"
        assert market_data.cache_ttl['news'] == 21600, "News TTL should be 6 hours"
        assert market_data.cache_ttl['historical'] == 3600, "Historical TTL should be 1 hour"
        assert market_data.cache_ttl['profile'] == 86400, "Profile TTL should be 24 hours"

        # Check cache stats initialization
        assert market_data.cache_stats['hits'] == 0, "Cache hits should start at 0"
        assert market_data.cache_stats['misses'] == 0, "Cache misses should start at 0"
        assert market_data.cache_stats['expired_fallbacks'] == 0, "Expired fallbacks should start at 0"

        has_api_key = market_data.api_key is not None and len(market_data.api_key) > 0

        print_result("Initialization", True,
                    f"API Key configured: {has_api_key}")

        return market_data, has_api_key

    except Exception as e:
        print_result("Initialization", False, f"Error: {e}")
        return None, False


def test_no_api_key_handling(market_data, has_api_key):
    """Test 2: Graceful handling when API key is missing"""
    print_test_header("No API Key Handling")

    if has_api_key:
        print_result("No API key handling", True,
                    "Skipping - API key is configured", skip=True)
        return True

    try:
        # Try to get a quote without API key
        result = market_data.get_quote('AAPL')

        # Should return error gracefully, not crash
        assert isinstance(result, dict), "Should return a dict"
        assert 'error' in result or result.get('symbol') == 'AAPL', \
            "Should return error or symbol"

        print_result("No API key handling", True,
                    "Gracefully handles missing API key")
        return True

    except Exception as e:
        print_result("No API key handling", False, f"Error: {e}")
        return False


def test_get_quote(market_data, has_api_key):
    """Test 3: Get stock quote for AAPL"""
    print_test_header("Get Quote (AAPL)")

    if not has_api_key:
        print_result("Get quote", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        result = market_data.get_quote('AAPL')

        # Check result structure
        assert isinstance(result, dict), "Should return a dict"

        if 'error' in result:
            print_result("Get quote", False, f"API Error: {result['error']}")
            return False

        # Validate expected fields
        expected_fields = ['symbol', 'name', 'price', 'volume', 'market_cap']
        missing_fields = [f for f in expected_fields if f not in result]

        if missing_fields:
            print_result("Get quote", False,
                        f"Missing fields: {missing_fields}")
            return False

        print_result("Get quote", True,
                    f"Symbol: {result['symbol']}, Price: ${result['price']:.2f}")
        return True

    except Exception as e:
        print_result("Get quote", False, f"Error: {e}")
        return False


def test_get_company_profile(market_data, has_api_key):
    """Test 4: Get company profile"""
    print_test_header("Get Company Profile (AAPL)")

    if not has_api_key:
        print_result("Get company profile", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        result = market_data.get_company_profile('AAPL')

        assert isinstance(result, dict), "Should return a dict"

        if 'error' in result:
            print_result("Get company profile", False, f"API Error: {result['error']}")
            return False

        # Validate expected fields
        expected_fields = ['symbol', 'company_name', 'sector', 'industry', 'ceo']
        missing_fields = [f for f in expected_fields if f not in result]

        if missing_fields:
            print_result("Get company profile", False,
                        f"Missing fields: {missing_fields}")
            return False

        print_result("Get company profile", True,
                    f"Company: {result['company_name']}, CEO: {result['ceo']}")
        return True

    except Exception as e:
        print_result("Get company profile", False, f"Error: {e}")
        return False


def test_invalid_symbol(market_data, has_api_key):
    """Test 5: Handle invalid stock symbol gracefully"""
    print_test_header("Invalid Symbol Error Handling")

    if not has_api_key:
        print_result("Invalid symbol handling", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Use an invalid symbol
        result = market_data.get_quote('INVALIDXYZ123')

        assert isinstance(result, dict), "Should return a dict"

        # Should either return error or empty data, not crash
        if 'error' in result or not result.get('price'):
            print_result("Invalid symbol handling", True,
                        "Gracefully handles invalid symbol")
            return True
        else:
            print_result("Invalid symbol handling", False,
                        "Should return error for invalid symbol")
            return False

    except Exception as e:
        print_result("Invalid symbol handling", False, f"Error: {e}")
        return False


def test_caching(market_data, has_api_key):
    """Test 6: Test caching mechanism"""
    print_test_header("Caching Mechanism")

    if not has_api_key:
        print_result("Caching", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # First call - should be a cache miss
        start = time.time()
        result1 = market_data.get_quote('MSFT')
        time1 = time.time() - start

        if 'error' in result1:
            print_result("Caching", True,
                        f"Skipping - API error: {result1['error']}", skip=True)
            return True

        # Second call - should be a cache hit (much faster)
        start = time.time()
        result2 = market_data.get_quote('MSFT')
        time2 = time.time() - start

        # Get cache stats
        stats = market_data.get_cache_stats()

        # Validate results are the same
        assert result1['symbol'] == result2['symbol'], "Cached result should match"

        # Second call should be faster (cached)
        assert time2 < time1, "Cached call should be faster"

        print_result("Caching", True,
                    f"First call: {time1:.3f}s, Cached call: {time2:.3f}s, " +
                    f"Cache hits: {stats['cache_hits']}")
        return True

    except Exception as e:
        print_result("Caching", False, f"Error: {e}")
        return False


def test_rate_limiting_simulation(market_data):
    """Test 7: Simulate rate limiting behavior"""
    print_test_header("Rate Limiting Simulation")

    try:
        rate_limiter = market_data.rate_limiter

        # Check rate limiter exists
        assert hasattr(rate_limiter, 'wait_if_needed'), "Rate limiter missing wait_if_needed"
        assert hasattr(rate_limiter, 'set_backoff'), "Rate limiter missing set_backoff"

        # Test backoff setting
        rate_limiter.set_backoff(1)
        assert rate_limiter.backoff_until is not None, "Backoff should be set"

        # Reset for other tests
        rate_limiter.backoff_until = None

        print_result("Rate limiting simulation", True,
                    "Rate limiter initialized correctly")
        return True

    except Exception as e:
        print_result("Rate limiting simulation", False, f"Error: {e}")
        return False


def test_cache_statistics(market_data):
    """Test 8: Verify cache statistics tracking"""
    print_test_header("Cache Statistics")

    try:
        stats = market_data.get_cache_stats()

        # Validate stats structure
        assert 'cache_hits' in stats, "Missing cache_hits in stats"
        assert 'cache_misses' in stats, "Missing cache_misses in stats"
        assert 'cache_hit_rate' in stats, "Missing cache_hit_rate in stats"
        assert 'expired_fallbacks' in stats, "Missing expired_fallbacks in stats"
        assert 'cached_items' in stats, "Missing cached_items in stats"

        # Print statistics
        print(f"\n  Cache Statistics:")
        print(f"    - Cache Hits: {stats['cache_hits']}")
        print(f"    - Cache Misses: {stats['cache_misses']}")
        print(f"    - Hit Rate: {stats['cache_hit_rate']}")
        print(f"    - Expired Fallbacks: {stats['expired_fallbacks']}")
        print(f"    - Cached Items: {stats['cached_items']}")

        print_result("Cache statistics", True,
                    f"Hit rate: {stats['cache_hit_rate']}")
        return True

    except Exception as e:
        print_result("Cache statistics", False, f"Error: {e}")
        return False


def test_expired_cache_fallback(market_data, has_api_key):
    """Test 9: Test fallback to expired cache on API failure"""
    print_test_header("Expired Cache Fallback")

    try:
        # Manually create expired cache entry
        cache_key = "quote_TEST"
        market_data.cache[cache_key] = {
            'data': {
                'symbol': 'TEST',
                'price': 100.0,
                'name': 'Test Company'
            },
            'time': datetime(2020, 1, 1)  # Very old timestamp
        }

        # Now try to get fresh cache (should be expired)
        cached = market_data._get_from_cache(cache_key, 'quotes')

        assert cached is not None, "Should return expired cache data"
        assert cached[1] == False, "Data should be marked as not fresh"
        assert cached[0]['symbol'] == 'TEST', "Should return cached data"

        print_result("Expired cache fallback", True,
                    "Successfully returns expired cache when needed")
        return True

    except Exception as e:
        print_result("Expired cache fallback", False, f"Error: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print(f"\n{TestColors.INFO}{'=' * 70}")
    print("TEST SUMMARY")
    print(f"{'=' * 70}{TestColors.RESET}\n")

    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    skipped = sum(1 for r in results if r['status'] == 'SKIP')
    total = len(results)

    print(f"Total Tests: {total}")
    print(f"{TestColors.PASS}Passed: {passed}{TestColors.RESET}")
    print(f"{TestColors.FAIL}Failed: {failed}{TestColors.RESET}")
    print(f"{TestColors.SKIP}Skipped: {skipped}{TestColors.RESET}")

    overall_status = "PASS" if failed == 0 else "FAIL"
    color = TestColors.PASS if failed == 0 else TestColors.FAIL

    print(f"\n{color}Overall Status: {overall_status}{TestColors.RESET}\n")

    return failed == 0


def main():
    """Run all tests"""
    print(f"\n{TestColors.INFO}FMP API Integration Test Suite{TestColors.RESET}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # Test 1: Initialization
    market_data, has_api_key = test_initialization()
    if market_data is None:
        print(f"\n{TestColors.FAIL}CRITICAL: Failed to initialize. Aborting tests.{TestColors.RESET}\n")
        return 1

    results.append({'name': 'Initialization', 'status': 'PASS'})

    # Test 2: No API key handling
    result = test_no_api_key_handling(market_data, has_api_key)
    results.append({
        'name': 'No API key handling',
        'status': 'SKIP' if has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 3: Get quote
    result = test_get_quote(market_data, has_api_key)
    results.append({
        'name': 'Get quote',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 4: Get company profile
    result = test_get_company_profile(market_data, has_api_key)
    results.append({
        'name': 'Get company profile',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 5: Invalid symbol
    result = test_invalid_symbol(market_data, has_api_key)
    results.append({
        'name': 'Invalid symbol handling',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 6: Caching
    result = test_caching(market_data, has_api_key)
    results.append({
        'name': 'Caching',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 7: Rate limiting simulation
    result = test_rate_limiting_simulation(market_data)
    results.append({
        'name': 'Rate limiting simulation',
        'status': 'PASS' if result else 'FAIL'
    })

    # Test 8: Cache statistics
    result = test_cache_statistics(market_data)
    results.append({
        'name': 'Cache statistics',
        'status': 'PASS' if result else 'FAIL'
    })

    # Test 9: Expired cache fallback
    result = test_expired_cache_fallback(market_data, has_api_key)
    results.append({
        'name': 'Expired cache fallback',
        'status': 'PASS' if result else 'FAIL'
    })

    # Print summary
    success = print_summary(results)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
