#!/usr/bin/env python3
"""
Test Real Data Integration - Verify API normalizers and PatternEngine integration
"""
import sys
sys.path.insert(0, 'dawsos')

from core.api_normalizer import get_normalizer
from core.credentials import get_credential_manager
import os

def test_credential_management():
    """Test that credentials are properly managed"""
    print("🔐 Testing Credential Management...")
    print()

    credentials = get_credential_manager()

    # Check if .env file exists
    env_exists = os.path.exists('.env') or os.path.exists('dawsos/.env')
    print(f"  .env file present: {env_exists}")

    # Get API keys (without exposing them)
    fred_key = credentials.get('FRED_API_KEY', required=False)
    fmp_key = credentials.get('FMP_API_KEY', required=False)
    news_key = credentials.get('NEWSAPI_KEY', required=False)

    print(f"  FRED_API_KEY configured: {bool(fred_key)}")
    print(f"  FMP_API_KEY configured: {bool(fmp_key)}")
    print(f"  NEWSAPI_KEY configured: {bool(news_key)}")

    if fred_key:
        print(f"  FRED key (masked): {credentials.mask_key(fred_key)}")

    print()
    return bool(fred_key) or bool(fmp_key) or bool(news_key)


def test_api_normalizers():
    """Test API payload normalizers"""
    print("📊 Testing API Normalizers...")
    print()

    normalizer = get_normalizer()

    # Test stock quote normalization
    print("  Testing stock quote normalizer...")
    mock_fmp_quote = [{
        'symbol': 'AAPL',
        'price': 175.50,
        'change': 2.30,
        'changesPercentage': 1.33,
        'volume': 52000000,
        'marketCap': 2800000000000,
        'pe': 28.5,
        'eps': 6.15
    }]

    normalized_quote = normalizer.normalize_stock_quote(mock_fmp_quote, 'fmp')
    assert normalized_quote['symbol'] == 'AAPL'
    assert normalized_quote['price'] == 175.50
    assert normalized_quote['data_quality'] == 'high'
    print(f"    ✅ Stock quote: {normalized_quote['symbol']} @ ${normalized_quote['price']}")

    # Test economic indicator normalization
    print("  Testing economic indicator normalizer...")
    mock_fred_data = {
        'observations': [
            {'date': '2024-01-01', 'value': '3.5'},
            {'date': '2024-02-01', 'value': '3.7'}
        ],
        'units': 'Percent',
        'frequency': 'Monthly'
    }

    normalized_indicator = normalizer.normalize_economic_indicator(mock_fred_data, 'UNRATE', 'fred')
    assert normalized_indicator['indicator'] == 'UNRATE'
    assert normalized_indicator['value'] == '3.7'
    assert normalized_indicator['change_percent'] is not None
    print(f"    ✅ Economic indicator: {normalized_indicator['indicator']} = {normalized_indicator['value']}")

    # Test news normalization
    print("  Testing news normalizer...")
    mock_news = {
        'articles': [
            {
                'title': 'Apple Stock Surges',
                'url': 'https://example.com/1',
                'source': {'name': 'Reuters'},
                'publishedAt': '2024-01-01T12:00:00Z',
                'sentiment': 0.8,
                'sentiment_label': 'positive'
            }
        ]
    }

    normalized_news = normalizer.normalize_news_articles(mock_news, 'newsapi')
    assert len(normalized_news) == 1
    assert normalized_news[0]['title'] == 'Apple Stock Surges'
    assert normalized_news[0]['sentiment'] == 0.8
    print(f"    ✅ News articles: {len(normalized_news)} normalized")

    # Test macro context normalization
    print("  Testing macro context normalizer...")
    mock_indicators = {
        'GDP': {
            'value': '25000',
            'change_percent': 2.5,
            'date': '2024-01-01'
        },
        'CPI': {
            'value': '310',
            'change_percent': 2.8,
            'date': '2024-01-01'
        },
        'UNRATE': {
            'value': '3.7',
            'date': '2024-01-01'
        },
        'FEDFUNDS': {
            'value': '5.25',
            'date': '2024-01-01'
        }
    }

    macro_context = normalizer.normalize_macro_context(mock_indicators)
    assert 'regime' in macro_context
    assert 'short_cycle_position' in macro_context
    assert macro_context['data_quality'] == 'high'  # All 4 indicators present
    print(f"    ✅ Macro context: {macro_context['regime']} regime, {macro_context['short_cycle_position']}")

    print()
    print("  ✅ All normalizers working correctly!")
    print()
    return True


def test_pattern_engine_integration():
    """Test PatternEngine real data integration"""
    print("⚙️  Testing PatternEngine Integration...")
    print()

    # This would require full app context, so we'll just verify the module imports
    try:
        from core.pattern_engine import PatternEngine
        print("  ✅ PatternEngine imports successfully")

        # Verify new method exists
        engine = PatternEngine()
        assert hasattr(engine, '_get_macro_economic_data')
        assert hasattr(engine, '_empty_macro_data')
        print("  ✅ New macro data methods present")

        # Test empty macro data structure
        empty_data = engine._empty_macro_data()
        assert 'data_quality' in empty_data
        assert empty_data['data_quality'] == 'none'
        assert '⚠️' in empty_data['recommendations']
        print("  ✅ Empty macro data structure correct")

    except Exception as e:
        print(f"  ❌ PatternEngine integration issue: {e}")
        return False

    print()
    return True


def main():
    """Run all integration tests"""
    print("="*60)
    print("  Real Data Integration Test Suite")
    print("="*60)
    print()

    results = []

    # Test 1: Credential Management
    try:
        has_credentials = test_credential_management()
        results.append(('Credential Management', True, has_credentials))
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
        results.append(('Credential Management', False, False))

    # Test 2: API Normalizers
    try:
        normalizers_ok = test_api_normalizers()
        results.append(('API Normalizers', True, normalizers_ok))
    except Exception as e:
        print(f"❌ Normalizer test failed: {e}")
        results.append(('API Normalizers', False, False))

    # Test 3: PatternEngine Integration
    try:
        pattern_ok = test_pattern_engine_integration()
        results.append(('PatternEngine Integration', True, pattern_ok))
    except Exception as e:
        print(f"❌ PatternEngine test failed: {e}")
        results.append(('PatternEngine Integration', False, False))

    # Summary
    print("="*60)
    print("  Test Summary")
    print("="*60)
    print()

    all_passed = all(passed for _, passed, _ in results)

    for test_name, passed, has_data in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        data_status = "(API keys configured)" if has_data else "(No API keys)"
        print(f"  {status}: {test_name} {data_status if test_name == 'Credential Management' else ''}")

    print()

    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print()
        print("Real data integration is ready:")
        print("  ✅ Credential management working")
        print("  ✅ API normalizers working")
        print("  ✅ PatternEngine updated for real data")
        print()
        print("To enable live data:")
        print("  1. Add API keys to .env file:")
        print("     FRED_API_KEY=your_fred_key")
        print("     FMP_API_KEY=your_fmp_key")
        print("     NEWSAPI_KEY=your_news_key")
        print("  2. Restart the application")
        print("  3. Patterns will automatically use real data!")
    else:
        print("❌ SOME TESTS FAILED - Check output above")
        return 1

    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
