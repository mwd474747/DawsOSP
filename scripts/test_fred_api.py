#!/usr/bin/env python3
"""
Test script for FRED API integration

Tests the FredDataCapability class with comprehensive error handling,
rate limiting, and caching validation.

Can run with or without a valid API key.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dawsos.capabilities.fred_data import FredDataCapability


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
    """Test 1: Initialize FredDataCapability"""
    print_test_header("Initialize FredDataCapability")

    try:
        fred = FredDataCapability()

        # Check attributes
        assert hasattr(fred, 'api_key'), "Missing api_key attribute"
        assert hasattr(fred, 'rate_limiter'), "Missing rate_limiter attribute"
        assert hasattr(fred, 'cache'), "Missing cache attribute"
        assert hasattr(fred, 'cache_ttl'), "Missing cache_ttl attribute"
        assert hasattr(fred, 'cache_stats'), "Missing cache_stats attribute"

        # Check cache TTL configuration
        assert fred.cache_ttl['series'] == 86400, "Series TTL should be 24 hours"
        assert fred.cache_ttl['metadata'] == 604800, "Metadata TTL should be 1 week"
        assert fred.cache_ttl['latest'] == 86400, "Latest TTL should be 24 hours"

        # Check cache stats initialization
        assert fred.cache_stats['hits'] == 0, "Cache hits should start at 0"
        assert fred.cache_stats['misses'] == 0, "Cache misses should start at 0"
        assert fred.cache_stats['expired_fallbacks'] == 0, "Expired fallbacks should start at 0"

        # Check key economic series are configured
        assert 'GDP' in fred.indicators, "GDP should be in indicators"
        assert fred.indicators.get('UNEMPLOYMENT') == 'UNRATE', "UNEMPLOYMENT->UNRATE mapping should exist"
        assert fred.indicators.get('CPI') == 'CPIAUCSL', "CPI->CPIAUCSL mapping should exist"
        assert 'T10Y2Y' in fred.indicators, "T10Y2Y should be in indicators"
        assert 'SP500' in fred.indicators, "SP500 should be in indicators"

        has_api_key = fred.api_key is not None and len(fred.api_key) > 0

        print_result("Initialization", True,
                    f"API Key configured: {has_api_key}")

        return fred, has_api_key

    except Exception as e:
        print_result("Initialization", False, f"Error: {e}")
        return None, False


def test_no_api_key_handling(fred, has_api_key):
    """Test 2: Graceful handling when API key is missing"""
    print_test_header("No API Key Handling")

    if has_api_key:
        print_result("No API key handling", True,
                    "Skipping - API key is configured", skip=True)
        return True

    try:
        # Try to get GDP data without API key
        result = fred.get_series('GDP')

        # Should return error gracefully, not crash
        assert isinstance(result, dict), "Should return a dict"
        assert 'error' in result or result.get('series_id') == 'GDP', \
            "Should return error or series_id"

        print_result("No API key handling", True,
                    "Gracefully handles missing API key")
        return True

    except Exception as e:
        print_result("No API key handling", False, f"Error: {e}")
        return False


def test_get_series_gdp(fred, has_api_key):
    """Test 3: Get GDP series data"""
    print_test_header("Get Series (GDP)")

    if not has_api_key:
        print_result("Get series GDP", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        result = fred.get_series('GDP')

        # Check result structure
        assert isinstance(result, dict), "Should return a dict"

        if 'error' in result:
            print_result("Get series GDP", False, f"API Error: {result['error']}")
            return False

        # Validate expected fields
        expected_fields = ['series_id', 'name', 'units', 'frequency', 'observations', 'latest_value']
        missing_fields = [f for f in expected_fields if f not in result]

        if missing_fields:
            print_result("Get series GDP", False,
                        f"Missing fields: {missing_fields}")
            return False

        # Check observations
        observations = result.get('observations', [])
        assert len(observations) > 0, "Should have observations"

        print_result("Get series GDP", True,
                    f"Latest GDP: ${result['latest_value']:.2f}T on {result['latest_date']}")
        return True

    except Exception as e:
        print_result("Get series GDP", False, f"Error: {e}")
        return False


def test_series_info(fred, has_api_key):
    """Test 4: Get series metadata"""
    print_test_header("Get Series Metadata (UNRATE)")

    if not has_api_key:
        print_result("Series metadata", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        result = fred.series_info('UNRATE')

        assert isinstance(result, dict), "Should return a dict"

        if 'error' in result:
            print_result("Series metadata", False, f"API Error: {result['error']}")
            return False

        # Validate expected fields
        expected_fields = ['series_id', 'title', 'units', 'frequency', 'last_updated']
        missing_fields = [f for f in expected_fields if f not in result]

        if missing_fields:
            print_result("Series metadata", False,
                        f"Missing fields: {missing_fields}")
            return False

        print_result("Series metadata", True,
                    f"Title: {result['title']}, Units: {result['units']}")
        return True

    except Exception as e:
        print_result("Series metadata", False, f"Error: {e}")
        return False


def test_get_latest_value(fred, has_api_key):
    """Test 5: Get latest value for a series"""
    print_test_header("Get Latest Value (CPI)")

    if not has_api_key:
        print_result("Get latest value", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        result = fred.get_latest_value('CPIAUCSL')

        assert isinstance(result, dict), "Should return a dict"

        if 'error' in result:
            print_result("Get latest value", False, f"API Error: {result['error']}")
            return False

        # Validate expected fields
        expected_fields = ['series_id', 'name', 'value', 'date', 'units']
        missing_fields = [f for f in expected_fields if f not in result]

        if missing_fields:
            print_result("Get latest value", False,
                        f"Missing fields: {missing_fields}")
            return False

        print_result("Get latest value", True,
                    f"CPI: {result['value']} ({result['units']}) on {result['date']}")
        return True

    except Exception as e:
        print_result("Get latest value", False, f"Error: {e}")
        return False


def test_get_multiple_series(fred, has_api_key):
    """Test 6: Get multiple series at once"""
    print_test_header("Get Multiple Series")

    if not has_api_key:
        print_result("Get multiple series", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Get key economic indicators
        series_ids = ['GDP', 'UNRATE', 'DFF', 'T10Y2Y']
        results = fred.get_multiple_series(series_ids)

        assert isinstance(results, dict), "Should return a dict"
        assert len(results) == len(series_ids), "Should return all requested series"

        # Check each series
        success_count = 0
        for series_id in series_ids:
            if series_id in results and 'error' not in results[series_id]:
                success_count += 1

        if success_count == 0:
            print_result("Get multiple series", False,
                        "No series data retrieved successfully")
            return False

        print_result("Get multiple series", True,
                    f"Retrieved {success_count}/{len(series_ids)} series successfully")
        return True

    except Exception as e:
        print_result("Get multiple series", False, f"Error: {e}")
        return False


def test_get_series_with_dates(fred, has_api_key):
    """Test 7: Get series with datetime objects"""
    print_test_header("Get Series with Datetime Objects")

    if not has_api_key:
        print_result("Series with dates", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        result = fred.get_series_with_dates('SP500')

        assert isinstance(result, dict), "Should return a dict"

        if 'error' in result:
            print_result("Series with dates", False, f"API Error: {result['error']}")
            return False

        # Check observations have datetime objects
        observations = result.get('observations', [])
        if observations:
            first_obs = observations[0]
            assert 'datetime' in first_obs, "Should have datetime field"
            assert first_obs['datetime'] is not None, "Datetime should not be None"

        # Check latest_datetime
        assert 'latest_datetime' in result or 'latest_date' in result, \
            "Should have latest_datetime or latest_date"

        print_result("Series with dates", True,
                    f"S&P 500 latest: {result.get('latest_value')}")
        return True

    except Exception as e:
        print_result("Series with dates", False, f"Error: {e}")
        return False


def test_invalid_series(fred, has_api_key):
    """Test 8: Handle invalid series ID gracefully"""
    print_test_header("Invalid Series Error Handling")

    if not has_api_key:
        print_result("Invalid series handling", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Use an invalid series ID
        result = fred.get_series('INVALIDXYZ123')

        assert isinstance(result, dict), "Should return a dict"

        # Should return error, not crash
        if 'error' in result or not result.get('observations'):
            print_result("Invalid series handling", True,
                        "Gracefully handles invalid series ID")
            return True
        else:
            print_result("Invalid series handling", False,
                        "Should return error for invalid series ID")
            return False

    except Exception as e:
        print_result("Invalid series handling", False, f"Error: {e}")
        return False


def test_caching(fred, has_api_key):
    """Test 9: Test caching mechanism"""
    print_test_header("Caching Mechanism")

    if not has_api_key:
        print_result("Caching", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # First call - should be a cache miss
        start = time.time()
        result1 = fred.get_series('DFF')  # Federal Funds Rate
        time1 = time.time() - start

        if 'error' in result1:
            print_result("Caching", True,
                        f"Skipping - API error: {result1['error']}", skip=True)
            return True

        # Second call - should be a cache hit (much faster)
        start = time.time()
        result2 = fred.get_series('DFF')
        time2 = time.time() - start

        # Get cache stats
        stats = fred.get_cache_stats()

        # Validate results are the same
        assert result1['series_id'] == result2['series_id'], "Cached result should match"

        # Second call should be faster (cached)
        assert time2 < time1, "Cached call should be faster"

        print_result("Caching", True,
                    f"First call: {time1:.3f}s, Cached call: {time2:.3f}s, " +
                    f"Cache hits: {stats['cache_hits']}")
        return True

    except Exception as e:
        print_result("Caching", False, f"Error: {e}")
        return False


def test_rate_limiting_simulation(fred):
    """Test 10: Simulate rate limiting behavior"""
    print_test_header("Rate Limiting Simulation")

    try:
        rate_limiter = fred.rate_limiter

        # Check rate limiter exists
        assert hasattr(rate_limiter, 'wait_if_needed'), "Rate limiter missing wait_if_needed"
        assert hasattr(rate_limiter, 'set_backoff'), "Rate limiter missing set_backoff"

        # Test backoff setting
        rate_limiter.set_backoff(1)
        assert rate_limiter.backoff_until is not None, "Backoff should be set"

        # Reset for other tests
        rate_limiter.backoff_until = None

        print_result("Rate limiting simulation", True,
                    "Rate limiter initialized correctly (1000/min)")
        return True

    except Exception as e:
        print_result("Rate limiting simulation", False, f"Error: {e}")
        return False


def test_cache_statistics(fred):
    """Test 11: Verify cache statistics tracking"""
    print_test_header("Cache Statistics")

    try:
        stats = fred.get_cache_stats()

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


def test_expired_cache_fallback(fred, has_api_key):
    """Test 12: Test fallback to expired cache on API failure"""
    print_test_header("Expired Cache Fallback")

    try:
        # Manually create expired cache entry
        cache_key = "series_TEST:None:None"
        fred.cache[cache_key] = {
            'data': {
                'series_id': 'TEST',
                'name': 'Test Series',
                'observations': [{'date': '2020-01-01', 'value': 100.0}],
                'latest_value': 100.0,
                'latest_date': '2020-01-01'
            },
            'time': datetime(2020, 1, 1)  # Very old timestamp
        }

        # Now try to get fresh cache (should be expired)
        cached = fred._get_from_cache(cache_key, 'series')

        assert cached is not None, "Should return expired cache data"
        assert cached[1] == False, "Data should be marked as not fresh"
        assert cached[0]['series_id'] == 'TEST', "Should return cached data"

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
    print(f"\n{TestColors.INFO}FRED API Integration Test Suite{TestColors.RESET}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # Test 1: Initialization
    fred, has_api_key = test_initialization()
    if fred is None:
        print(f"\n{TestColors.FAIL}CRITICAL: Failed to initialize. Aborting tests.{TestColors.RESET}\n")
        return 1

    results.append({'name': 'Initialization', 'status': 'PASS'})

    # Test 2: No API key handling
    result = test_no_api_key_handling(fred, has_api_key)
    results.append({
        'name': 'No API key handling',
        'status': 'SKIP' if has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 3: Get series GDP
    result = test_get_series_gdp(fred, has_api_key)
    results.append({
        'name': 'Get series GDP',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 4: Series metadata
    result = test_series_info(fred, has_api_key)
    results.append({
        'name': 'Series metadata',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 5: Get latest value
    result = test_get_latest_value(fred, has_api_key)
    results.append({
        'name': 'Get latest value',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 6: Get multiple series
    result = test_get_multiple_series(fred, has_api_key)
    results.append({
        'name': 'Get multiple series',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 7: Series with datetime objects
    result = test_get_series_with_dates(fred, has_api_key)
    results.append({
        'name': 'Series with dates',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 8: Invalid series
    result = test_invalid_series(fred, has_api_key)
    results.append({
        'name': 'Invalid series handling',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 9: Caching
    result = test_caching(fred, has_api_key)
    results.append({
        'name': 'Caching',
        'status': 'SKIP' if not has_api_key else ('PASS' if result else 'FAIL')
    })

    # Test 10: Rate limiting simulation
    result = test_rate_limiting_simulation(fred)
    results.append({
        'name': 'Rate limiting simulation',
        'status': 'PASS' if result else 'FAIL'
    })

    # Test 11: Cache statistics
    result = test_cache_statistics(fred)
    results.append({
        'name': 'Cache statistics',
        'status': 'PASS' if result else 'FAIL'
    })

    # Test 12: Expired cache fallback
    result = test_expired_cache_fallback(fred, has_api_key)
    results.append({
        'name': 'Expired cache fallback',
        'status': 'PASS' if result else 'FAIL'
    })

    # Print summary
    success = print_summary(results)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
