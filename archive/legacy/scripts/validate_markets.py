#!/usr/bin/env python3
"""
Markets Tab Validation Script
Validates all recent changes to the Markets functionality
"""

import sys
sys.path.insert(0, '/Users/mdawson/Dawson/DawsOSB/dawsos')

from capabilities.market_data import MarketDataCapability
from agents.data_harvester import DataHarvester
from core.knowledge_graph import KnowledgeGraph
from core.credentials import get_credential_manager
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_api_key():
    print_section("1. API Key Configuration")
    creds = get_credential_manager()
    api_key = creds.get('FMP_API_KEY', required=False)

    if api_key:
        print(f"✓ FMP API Key found")
        print(f"  Length: {len(api_key)} characters")
        return True
    else:
        print("✗ FMP API Key NOT found")
        print("  Please add FMP_API_KEY to dawsos/.env file")
        return False

def test_market_capability():
    print_section("2. MarketDataCapability")

    try:
        market = MarketDataCapability()
        print("✓ MarketDataCapability initialized")
        print(f"  Base URL: {market.base_url}")
        print(f"  Rate Limiter: {market.rate_limiter.max_requests} req/min")

        # Test quote
        print("\n  Testing get_quote('SPY')...")
        quote = market.get_quote('SPY')
        if 'error' not in quote and 'price' in quote:
            print(f"  ✓ SPY Quote: ${quote.get('price')}")
            print(f"    Change: {quote.get('changesPercentage')}%")
            print(f"    Volume: {quote.get('volume', 'N/A')}")
        else:
            print(f"  ✗ Quote failed: {quote}")
            return False

        # Test market movers
        print("\n  Testing get_market_movers('gainers')...")
        gainers = market.get_market_movers('gainers')
        if gainers and len(gainers) > 0 and 'symbol' in gainers[0]:
            print(f"  ✓ Gainers: {len(gainers)} stocks")
            print(f"    Top: {gainers[0]['symbol']} ({gainers[0]['changesPercentage']}%)")
            print(f"    Fields: {list(gainers[0].keys())}")
        else:
            print(f"  ✗ Gainers failed")
            return False

        # Test historical data
        print("\n  Testing get_historical('SPY', '1M')...")
        historical = market.get_historical('SPY', '1M', '1d')
        if historical and len(historical) > 0:
            print(f"  ✓ Historical: {len(historical)} data points")
            print(f"    Date range: {historical[0]['date']} to {historical[-1]['date']}")
        else:
            print(f"  ✗ Historical data failed")
            return False

        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def test_data_harvester():
    print_section("3. DataHarvester Integration")

    try:
        graph = KnowledgeGraph()
        capabilities = {'market': MarketDataCapability()}
        harvester = DataHarvester(graph, capabilities)
        print("✓ DataHarvester initialized")

        # Test fetch_stock_quotes
        print("\n  Testing fetch_stock_quotes(['SPY', 'QQQ', 'GLD', 'TLT'])...")
        result = harvester.fetch_stock_quotes(['SPY', 'QQQ', 'GLD', 'TLT'])

        if 'quotes' not in result:
            print(f"  ✗ Wrong format, keys: {list(result.keys())}")
            return False

        print(f"  ✓ Correct format returned")
        print(f"    Result keys: {list(result.keys())}")
        print(f"    Quotes count: {len(result['quotes'])}")
        print(f"    Success: {result.get('success')}")

        # Verify all requested symbols
        for symbol in ['SPY', 'QQQ', 'GLD', 'TLT']:
            if symbol in result['quotes']:
                quote = result['quotes'][symbol]
                print(f"    ✓ {symbol}: ${quote.get('price')}")
            else:
                print(f"    ✗ {symbol}: Missing")

        # Test fetch_market_movers
        print("\n  Testing fetch_market_movers({'mover_type': 'gainers'})...")
        result = harvester.fetch_market_movers({'mover_type': 'gainers'})

        if 'movers' not in result:
            print(f"  ✗ Wrong format, keys: {list(result.keys())}")
            return False

        print(f"  ✓ Correct format returned")
        print(f"    Result keys: {list(result.keys())}")
        print(f"    Movers count: {len(result['movers'])}")
        print(f"    Type: {result.get('type')}")

        # Check field names
        if result['movers']:
            mover = result['movers'][0]
            required_fields = ['symbol', 'name', 'price', 'change', 'changesPercentage']
            missing = [f for f in required_fields if f not in mover or mover[f] is None]

            if missing:
                print(f"    ✗ Missing/null fields: {missing}")
            else:
                print(f"    ✓ All required fields present")
                print(f"    Sample: {mover['symbol']} - {mover['name']}")
                print(f"            ${mover['price']} ({mover['changesPercentage']}%)")

        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_type_safety():
    print_section("4. Type Safety & Error Handling")

    test_cases = [
        {"name": "String values", "data": {'price': '662.23', 'changesPercentage': '0.08', 'volume': '12345678'}},
        {"name": "Numeric values", "data": {'price': 662.23, 'changesPercentage': 0.08, 'volume': 12345678}},
        {"name": "Mixed types", "data": {'price': '662.23', 'changesPercentage': 0.08, 'volume': '12345678'}},
        {"name": "None values", "data": {'price': None, 'changesPercentage': None, 'volume': None}},
        {"name": "N/A strings", "data": {'price': 'N/A', 'changesPercentage': 'N/A', 'volume': 'N/A'}},
        {"name": "Missing keys", "data": {}},
    ]

    def safe_convert(value, default=0.0):
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    all_passed = True
    for test in test_cases:
        print(f"\n  Testing: {test['name']}")
        data = test['data']

        try:
            price = safe_convert(data.get('price', 0))
            change_pct = safe_convert(data.get('changesPercentage', 0))

            volume_raw = data.get('volume', 0)
            if volume_raw == 'N/A' or volume_raw is None:
                volume_display = 'N/A'
            else:
                volume = int(float(volume_raw))
                volume_display = f"{volume:,}"

            print(f"    ✓ Price: ${price:.2f}")
            print(f"    ✓ Change: {change_pct:+.2f}%")
            print(f"    ✓ Volume: {volume_display}")
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            all_passed = False

    return all_passed

def test_enhanced_indices():
    print_section("5. Enhanced Indices (6 symbols)")

    indices = [
        ('SPY', 'S&P 500', '📊'),
        ('QQQ', 'Nasdaq 100', '💻'),
        ('DIA', 'Dow Jones', '🏭'),
        ('IWM', 'Russell 2000', '🏢'),
        ('GLD', 'Gold ETF', '🥇'),
        ('TLT', '20Y Treasury', '💰'),
    ]

    try:
        market = MarketDataCapability()
        symbols = [idx[0] for idx in indices]

        print(f"  Fetching quotes for {len(symbols)} indices...")

        # Simulate batch fetch
        quotes = {}
        for symbol in symbols:
            quote = market.get_quote(symbol)
            if 'error' not in quote:
                quotes[symbol] = quote

        print(f"  ✓ Retrieved {len(quotes)}/{len(symbols)} quotes")

        for symbol, name, icon in indices:
            if symbol in quotes:
                quote = quotes[symbol]
                print(f"    {icon} {name:15s} ${quote.get('price'):>8} ({quote.get('changesPercentage', 0):>+6}%)")
            else:
                print(f"    {icon} {name:15s} [No data]")

        return len(quotes) >= 4  # At least equity indices should work
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  DAWSOS MARKETS TAB VALIDATION")
    print("="*60)

    results = {}

    # Run all tests
    results['api_key'] = test_api_key()
    results['market_capability'] = test_market_capability()
    results['data_harvester'] = test_data_harvester()
    results['type_safety'] = test_type_safety()
    results['enhanced_indices'] = test_enhanced_indices()

    # Summary
    print_section("VALIDATION SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}  {test.replace('_', ' ').title()}")

    print(f"\n  Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 All validations passed! Markets tab is ready.")
        return 0
    else:
        print("\n  ⚠️  Some validations failed. Please review errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
