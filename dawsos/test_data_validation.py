#!/usr/bin/env python3
"""Data validation tests - checking actual values from APIs"""
import os
from datetime import datetime
import json

# Load environment
from load_env import load_env
load_env()

print("=" * 80)
print("DawsOS DATA VALIDATION - VERIFYING REAL-TIME DATA")
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Import capabilities
from capabilities.fred import FREDCapability
from capabilities.market_data import MarketDataCapability
from core.llm_client import get_llm_client

# Initialize
fred = FREDCapability()
market = MarketDataCapability()
llm = get_llm_client()

print("\n📊 ECONOMIC INDICATORS - FRED API")
print("-" * 80)

# Test critical economic indicators with validation
indicators = [
    {'code': 'GDP', 'name': 'GDP', 'expected_range': (25000, 35000), 'unit': 'Billion $'},
    {'code': 'CPIAUCSL', 'name': 'CPI', 'expected_range': (250, 400), 'unit': 'Index'},
    {'code': 'UNRATE', 'name': 'Unemployment', 'expected_range': (2, 10), 'unit': '%'},
    {'code': 'DFF', 'name': 'Fed Rate', 'expected_range': (0, 10), 'unit': '%'},
    {'code': 'DGS10', 'name': '10Y Treasury', 'expected_range': (0, 10), 'unit': '%'}
]

valid_count = 0
for ind in indicators:
    data = fred.get_latest(ind['code'])
    if data and 'value' in data:
        value = data['value']
        date = data['date']
        min_val, max_val = ind['expected_range']

        if min_val <= value <= max_val:
            print(f"✅ {ind['name']:15} {value:10.2f} {ind['unit']:8} [{date}] - VALID")
            valid_count += 1
        else:
            print(f"⚠️  {ind['name']:15} {value:10.2f} {ind['unit']:8} [{date}] - OUT OF RANGE")
    else:
        print(f"❌ {ind['name']:15} FAILED TO FETCH")

print(f"\nValidation: {valid_count}/{len(indicators)} indicators within expected ranges")

print("\n📈 STOCK MARKET DATA - FMP API")
print("-" * 80)

# Test major stocks with validation
stocks = [
    {'symbol': 'AAPL', 'name': 'Apple', 'expected_range': (150, 300)},
    {'symbol': 'SPY', 'name': 'S&P 500', 'expected_range': (400, 700)},
    {'symbol': 'QQQ', 'name': 'Nasdaq 100', 'expected_range': (300, 700)},
    {'symbol': 'TSLA', 'name': 'Tesla', 'expected_range': (100, 1000)},
    {'symbol': 'NVDA', 'name': 'Nvidia', 'expected_range': (50, 300)}
]

valid_stocks = 0
for stock in stocks:
    quote = market.get_quote(stock['symbol'])
    if quote and 'price' in quote:
        price = quote['price']
        change = quote.get('change_percent', 0)
        volume = quote.get('volume', 0)
        min_val, max_val = stock['expected_range']

        if min_val <= price <= max_val:
            print(f"✅ {stock['name']:12} ${price:7.2f} ({change:+6.2f}%) Vol:{volume:>12,} - VALID")
            valid_stocks += 1
        else:
            print(f"⚠️  {stock['name']:12} ${price:7.2f} ({change:+6.2f}%) - PRICE OUT OF RANGE")
    else:
        print(f"❌ {stock['name']:12} FAILED TO FETCH")

print(f"\nValidation: {valid_stocks}/{len(stocks)} stocks within expected ranges")

print("\n🤖 CLAUDE API - INTELLIGENCE VALIDATION")
print("-" * 80)

# Test Claude with specific finance questions
test_queries = [
    {
        'prompt': "What is 256.59 / 254.63? Return just the number rounded to 4 decimals.",
        'expected': lambda x: 1.006 < float(x) < 1.008,
        'description': 'Math Calculation'
    },
    {
        'prompt': "If GDP is 30000 and growing at 2%, what will it be next year? Return just the number.",
        'expected': lambda x: 30500 < float(x) < 30700,
        'description': 'Growth Projection'
    },
    {
        'prompt': "Is a P/E ratio of 35 high or low? Return 'high' or 'low'.",
        'expected': lambda x: x.lower().strip() == 'high',
        'description': 'Financial Analysis'
    }
]

claude_valid = 0
for test in test_queries:
    try:
        response = llm.complete(test['prompt'])
        # Clean response
        if isinstance(response, dict) and 'error' not in response:
            response = str(response.get('response', response))
        response = str(response).strip().replace(',', '')

        # Try to validate
        try:
            if test['expected'](response):
                print(f"✅ {test['description']:20} Response: {response[:50]} - CORRECT")
                claude_valid += 1
            else:
                print(f"⚠️  {test['description']:20} Response: {response[:50]} - INCORRECT")
        except:
            print(f"⚠️  {test['description']:20} Response: {response[:50]} - PARSE ERROR")
    except Exception as e:
        print(f"❌ {test['description']:20} FAILED: {str(e)[:30]}")

print(f"\nValidation: {claude_valid}/{len(test_queries)} Claude responses correct")

print("\n📊 CROSS-VALIDATION - DATA CONSISTENCY")
print("-" * 80)

# Cross-validate data relationships
print("\nChecking data relationships:")

# 1. Check if unemployment and Fed rate make sense together
unemployment = fred.get_latest('UNRATE')
fed_rate = fred.get_latest('DFF')

if unemployment and fed_rate:
    unemp_val = unemployment.get('value', 0)
    fed_val = fed_rate.get('value', 0)

    # Generally, high unemployment = lower rates, low unemployment = higher rates
    if unemp_val < 4 and fed_val > 3:
        print(f"✅ Low unemployment ({unemp_val}%) with higher rates ({fed_val}%) - CONSISTENT")
    elif unemp_val > 6 and fed_val < 2:
        print(f"✅ High unemployment ({unemp_val}%) with lower rates ({fed_val}%) - CONSISTENT")
    else:
        print(f"🔍 Unemployment ({unemp_val}%) and Fed Rate ({fed_val}%) - CHECK CONTEXT")

# 2. Check if stock valuations make sense
spy = market.get_quote('SPY')
qqq = market.get_quote('QQQ')

if spy and qqq:
    spy_price = spy.get('price', 0)
    qqq_price = qqq.get('price', 0)

    # QQQ is typically 85-95% of SPY price
    ratio = qqq_price / spy_price if spy_price > 0 else 0
    if 0.85 <= ratio <= 0.95:
        print(f"✅ SPY/QQQ ratio ({ratio:.2f}) - NORMAL RELATIONSHIP")
    else:
        print(f"⚠️  SPY/QQQ ratio ({ratio:.2f}) - UNUSUAL RELATIONSHIP")

# 3. Check market cap consistency for AAPL
aapl = market.get_quote('AAPL')
if aapl:
    price = aapl.get('price', 0)
    market_cap = aapl.get('market_cap', 0)

    # Apple has about 15.2B shares outstanding
    implied_shares = market_cap / price if price > 0 else 0
    if 14.5e9 < implied_shares < 16e9:
        print(f"✅ AAPL market cap calculation - CONSISTENT")
    else:
        print(f"⚠️  AAPL implied shares ({implied_shares/1e9:.1f}B) - CHECK DATA")

print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

# Create comprehensive summary
summary = {
    'timestamp': datetime.now().isoformat(),
    'economic_indicators': {
        'valid': valid_count,
        'total': len(indicators),
        'percentage': (valid_count/len(indicators))*100
    },
    'stock_data': {
        'valid': valid_stocks,
        'total': len(stocks),
        'percentage': (valid_stocks/len(stocks))*100
    },
    'claude_api': {
        'valid': claude_valid,
        'total': len(test_queries),
        'percentage': (claude_valid/len(test_queries))*100
    }
}

overall_valid = valid_count + valid_stocks + claude_valid
overall_total = len(indicators) + len(stocks) + len(test_queries)

print(f"\n📊 Economic Indicators: {valid_count}/{len(indicators)} ({summary['economic_indicators']['percentage']:.0f}%)")
print(f"📈 Stock Data: {valid_stocks}/{len(stocks)} ({summary['stock_data']['percentage']:.0f}%)")
print(f"🤖 Claude API: {claude_valid}/{len(test_queries)} ({summary['claude_api']['percentage']:.0f}%)")
print(f"\n✨ Overall Validation: {overall_valid}/{overall_total} ({(overall_valid/overall_total)*100:.0f}%)")

# Save validation report
with open('data_validation_report.json', 'w') as f:
    json.dump(summary, f, indent=2)
    print(f"\n💾 Validation report saved to data_validation_report.json")

if (overall_valid/overall_total) >= 0.8:
    print("\n🎉 DATA VALIDATION PASSED - System data is accurate and consistent!")
else:
    print("\n⚠️  Some data validation issues detected - review the report above")