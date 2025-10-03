#!/usr/bin/env python3
"""Comprehensive API validation tests for DawsOS"""
import json
from datetime import datetime
import time

# Load environment
from load_env import load_env
load_env()

print("=" * 80)
print("DawsOS API VALIDATION TESTS")
print("=" * 80)

# Import capabilities
from capabilities.fred import FREDCapability
from capabilities.market_data import MarketDataCapability
from capabilities.news import NewsCapability
from core.llm_client import get_llm_client

# Initialize
fred = FREDCapability()
market = MarketDataCapability()
news = NewsCapability()
llm = get_llm_client()

test_results = []

print("\n" + "=" * 80)
print("1. FRED API - ECONOMIC INDICATORS")
print("=" * 80)

# Test various FRED indicators
fred_indicators = {
    'GDP': 'Gross Domestic Product',
    'CPIAUCSL': 'Consumer Price Index',
    'UNRATE': 'Unemployment Rate',
    'DFF': 'Federal Funds Rate',
    'DEXUSEU': 'USD/EUR Exchange Rate',
    'DGS10': '10-Year Treasury Rate',
    'HOUST': 'Housing Starts',
    'INDPRO': 'Industrial Production Index',
    'PAYEMS': 'Nonfarm Payrolls',
    'UMCSENT': 'Consumer Sentiment'
}

for code, name in fred_indicators.items():
    print(f"\n📊 Testing {name} ({code})...")
    try:
        data = fred.get_latest(code)
        if data and 'error' not in data:
            print(f"   ✅ Value: {data.get('value')}")
            print(f"   📅 Date: {data.get('date')}")
            test_results.append({
                'api': 'FRED',
                'indicator': code,
                'name': name,
                'success': True,
                'value': data.get('value'),
                'date': data.get('date')
            })
        else:
            print(f"   ❌ Error: {data.get('error', 'Unknown')}")
            test_results.append({
                'api': 'FRED',
                'indicator': code,
                'name': name,
                'success': False,
                'error': data.get('error', 'Unknown')
            })
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        test_results.append({
            'api': 'FRED',
            'indicator': code,
            'name': name,
            'success': False,
            'error': str(e)
        })
    time.sleep(0.1)  # Rate limiting

print("\n" + "=" * 80)
print("2. FINANCIAL MODELING PREP - STOCK QUOTES")
print("=" * 80)

# Test various stock symbols
stocks = [
    'AAPL',  # Apple
    'MSFT',  # Microsoft
    'GOOGL', # Google
    'AMZN',  # Amazon
    'TSLA',  # Tesla
    'NVDA',  # Nvidia
    'META',  # Meta
    'SPY',   # S&P 500 ETF
    'QQQ',   # Nasdaq ETF
    'GLD'    # Gold ETF
]

for symbol in stocks:
    print(f"\n📈 Testing {symbol}...")
    try:
        quote = market.get_quote(symbol)
        if quote and 'error' not in quote:
            print(f"   ✅ Price: ${quote.get('price')}")
            print(f"   📊 Change: {quote.get('change_percent')}%")
            print(f"   💰 Market Cap: ${quote.get('market_cap', 0):,.0f}")
            print(f"   📉 Day Range: ${quote.get('day_low')} - ${quote.get('day_high')}")
            test_results.append({
                'api': 'FMP',
                'symbol': symbol,
                'success': True,
                'price': quote.get('price'),
                'change': quote.get('change_percent'),
                'volume': quote.get('volume')
            })
        else:
            print(f"   ❌ Error: {quote.get('error', 'Unknown')}")
            test_results.append({
                'api': 'FMP',
                'symbol': symbol,
                'success': False,
                'error': quote.get('error', 'Unknown')
            })
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        test_results.append({
            'api': 'FMP',
            'symbol': symbol,
            'success': False,
            'error': str(e)
        })
    time.sleep(0.3)  # FMP rate limiting

print("\n" + "=" * 80)
print("3. CLAUDE API - NATURAL LANGUAGE PROCESSING")
print("=" * 80)

# Test various Claude prompts
test_prompts = [
    {
        'prompt': "Analyze the relationship between GDP growth and stock market performance. Return a JSON with 'relationship' and 'confidence' fields.",
        'description': 'Economic Analysis'
    },
    {
        'prompt': "Given these values: GDP=30000, CPI=3.5%, Unemployment=4.3%, predict market direction. Return JSON with 'direction' (up/down/neutral) and 'reasoning'.",
        'description': 'Market Prediction'
    },
    {
        'prompt': "Extract entities from: 'Apple stock rose 5% after earnings beat expectations'. Return JSON with 'entities' array.",
        'description': 'Entity Extraction'
    },
    {
        'prompt': "Classify this sentiment: 'Markets rallied on strong jobs data'. Return JSON with 'sentiment' (positive/negative/neutral) and 'confidence'.",
        'description': 'Sentiment Analysis'
    },
    {
        'prompt': "Calculate the correlation strength between oil prices and energy stocks. Return JSON with 'correlation' (-1 to 1) and 'relationship_type'.",
        'description': 'Correlation Analysis'
    }
]

for test in test_prompts:
    print(f"\n🤖 Testing {test['description']}...")
    try:
        response = llm.complete(test['prompt'], parse_json=True)
        if isinstance(response, dict) and 'error' not in response:
            print(f"   ✅ Response: {json.dumps(response, indent=2)}")
            test_results.append({
                'api': 'Claude',
                'test': test['description'],
                'success': True,
                'response': response
            })
        else:
            print(f"   ❌ Error: {response}")
            test_results.append({
                'api': 'Claude',
                'test': test['description'],
                'success': False,
                'error': str(response)
            })
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        test_results.append({
            'api': 'Claude',
            'test': test['description'],
            'success': False,
            'error': str(e)
        })
    time.sleep(0.5)  # Rate limiting

print("\n" + "=" * 80)
print("4. NEWS API - MARKET NEWS")
print("=" * 80)

# Test news searches
news_queries = [
    'Apple earnings',
    'Federal Reserve',
    'inflation',
    'stock market',
    'cryptocurrency'
]

for query in news_queries:
    print(f"\n📰 Testing news for '{query}'...")
    try:
        articles = news.search(query, limit=3)
        if articles and not isinstance(articles, dict):  # Not an error dict
            print(f"   ✅ Found {len(articles)} articles")
            for i, article in enumerate(articles[:2], 1):
                print(f"   {i}. {article.get('title', 'No title')[:60]}...")
            test_results.append({
                'api': 'NewsAPI',
                'query': query,
                'success': True,
                'count': len(articles)
            })
        else:
            print("   ❌ Error or no results")
            test_results.append({
                'api': 'NewsAPI',
                'query': query,
                'success': False,
                'error': 'No results or API error'
            })
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        test_results.append({
            'api': 'NewsAPI',
            'query': query,
            'success': False,
            'error': str(e)
        })
    time.sleep(0.5)

print("\n" + "=" * 80)
print("5. COMBINED API TEST - FULL WORKFLOW")
print("=" * 80)

print("\n🔄 Testing full data pipeline...")
try:
    # 1. Get economic data
    gdp = fred.get_latest('GDP')
    cpi = fred.get_latest('CPIAUCSL')

    # 2. Get stock data
    spy = market.get_quote('SPY')

    # 3. Use Claude to analyze
    analysis_prompt = f"""
    Analyze this market data and return a JSON response:
    - GDP: {gdp.get('value') if gdp else 'N/A'}
    - CPI: {cpi.get('value') if cpi else 'N/A'}
    - S&P 500: {spy.get('price') if spy else 'N/A'}

    Return JSON with:
    - 'market_condition': 'bullish' or 'bearish' or 'neutral'
    - 'confidence': 0-1
    - 'key_factor': most important factor
    """

    analysis = llm.complete(analysis_prompt, parse_json=True)

    if isinstance(analysis, dict):
        print(f"   ✅ Market Condition: {analysis.get('market_condition')}")
        print(f"   ✅ Confidence: {analysis.get('confidence')}")
        print(f"   ✅ Key Factor: {analysis.get('key_factor')}")
        test_results.append({
            'api': 'Combined',
            'test': 'Full Pipeline',
            'success': True,
            'result': analysis
        })
    else:
        print("   ❌ Analysis failed")
        test_results.append({
            'api': 'Combined',
            'test': 'Full Pipeline',
            'success': False
        })

except Exception as e:
    print(f"   ❌ Pipeline error: {str(e)}")
    test_results.append({
        'api': 'Combined',
        'test': 'Full Pipeline',
        'success': False,
        'error': str(e)
    })

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

# Calculate statistics
total = len(test_results)
successful = sum(1 for t in test_results if t.get('success'))
by_api = {}

for result in test_results:
    api = result['api']
    if api not in by_api:
        by_api[api] = {'total': 0, 'success': 0}
    by_api[api]['total'] += 1
    if result.get('success'):
        by_api[api]['success'] += 1

print(f"\n📊 Overall Success Rate: {successful}/{total} ({(successful/total)*100:.1f}%)")
print("\n📈 Success by API:")
for api, stats in by_api.items():
    rate = (stats['success']/stats['total'])*100 if stats['total'] > 0 else 0
    status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
    print(f"   {status} {api}: {stats['success']}/{stats['total']} ({rate:.1f}%)")

# Save detailed results
results_file = {
    'timestamp': datetime.now().isoformat(),
    'summary': {
        'total_tests': total,
        'successful': successful,
        'success_rate': (successful/total)*100,
        'by_api': by_api
    },
    'detailed_results': test_results
}

with open('api_validation_results.json', 'w') as f:
    json.dump(results_file, f, indent=2, default=str)
    print("\n💾 Detailed results saved to api_validation_results.json")

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)