#!/usr/bin/env python3
"""
Integration test for DawsOS - tests complete workflows
"""
from load_env import load_env
load_env()

import time
from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime
from core.knowledge_graph import KnowledgeGraph
from core.logger import get_logger
from agents.claude import Claude
from agents.data_harvester import DataHarvester
from agents.pattern_spotter import PatternSpotter
from agents.relationship_hunter import RelationshipHunter
from capabilities.market_data import MarketDataCapability
from capabilities.fred_data import FredDataCapability
import seed_knowledge_graph

# Initialize logger
logger = get_logger('IntegrationTest')

print("=" * 80)
print("DAWSOS INTEGRATION TEST")
print("=" * 80)

# Test setup
def setup_system():
    """Initialize the complete DawsOS system"""
    logger.info("Setting up DawsOS system")

    # Initialize knowledge graph
    graph = KnowledgeGraph()
    seed_knowledge_graph.seed_buffett_framework(graph)
    seed_knowledge_graph.seed_dalio_framework(graph)
    seed_knowledge_graph.seed_financial_calculations(graph)
    seed_knowledge_graph.seed_investment_examples(graph)

    logger.info(f"Knowledge graph initialized with {graph.get_stats()['total_nodes']} nodes")

    # Initialize capabilities
    capabilities = {
        'market': MarketDataCapability(),
        'fred': FredDataCapability()
    }

    # Initialize runtime and agents
    runtime = AgentRuntime()
    runtime.register_agent('claude', Claude(graph))
    runtime.register_agent('data_harvester', DataHarvester(graph, capabilities))
    runtime.register_agent('pattern_spotter', PatternSpotter(graph))
    runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

    # Initialize pattern engine
    pattern_engine = PatternEngine('patterns', runtime)
    runtime.pattern_engine = pattern_engine

    logger.info(f"Pattern engine loaded with {len(pattern_engine.patterns)} patterns")

    return runtime, graph, capabilities

# Test cases
def test_economic_moat_analysis(runtime):
    """Test economic moat analysis workflow"""
    print("\n1. Testing Economic Moat Analysis")
    print("-" * 40)

    test_queries = [
        "What is the economic moat of Apple?",
        "Analyze economic moat for MSFT",
        "Economic moat of Exxon"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        start_time = time.time()

        try:
            response = runtime.orchestrate(query)
            duration = time.time() - start_time

            if 'error' in response:
                print(f"  ❌ Error: {response['error']}")
                logger.error(f"Moat analysis failed for: {query}", error=response.get('error'))
            elif 'formatted_response' in response:
                # Check if response contains key sections
                content = response['formatted_response']
                has_moat = '**Economic Moat' in content or 'Moat' in content
                has_rating = 'Rating' in content or 'rating' in content

                print(f"  ✅ Success ({duration:.2f}s)")
                print(f"     • Has moat analysis: {has_moat}")
                print(f"     • Has rating: {has_rating}")
                print(f"     • Response length: {len(content)} chars")

                logger.info("Moat analysis completed", query=query, duration=duration)
            else:
                print("  ⚠️ Unexpected response format")
                logger.warning(f"Unexpected response format for: {query}")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            logger.error("Exception in moat analysis", error=e, query=query)

def test_debt_cycle_analysis(runtime):
    """Test debt cycle analysis workflow"""
    print("\n2. Testing Debt Cycle Analysis")
    print("-" * 40)

    queries = [
        "Where are we in the debt cycle?",
        "What is our position in the debt cycle?",
        "Analyze debt cycle position"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        start_time = time.time()

        try:
            response = runtime.orchestrate(query)
            duration = time.time() - start_time

            if 'formatted_response' in response:
                content = response['formatted_response']
                has_short = 'Short-Term' in content or 'short cycle' in content.lower()
                has_long = 'Long-Term' in content or 'long cycle' in content.lower()

                print(f"  ✅ Success ({duration:.2f}s)")
                print(f"     • Has short-term cycle: {has_short}")
                print(f"     • Has long-term cycle: {has_long}")

                logger.info("Debt cycle analysis completed", query=query, duration=duration)
            else:
                print("  ⚠️ No formatted response")
                logger.warning(f"No formatted response for: {query}")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            logger.error("Exception in debt cycle analysis", error=e, query=query)

def test_market_data_fetching(capabilities):
    """Test market data capability"""
    print("\n3. Testing Market Data Fetching")
    print("-" * 40)

    market = capabilities.get('market')
    if not market:
        print("  ❌ Market capability not available")
        return

    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

    for symbol in symbols:
        print(f"\nFetching: {symbol}")
        start_time = time.time()

        try:
            quote = market.get_quote(symbol)
            duration = time.time() - start_time

            if 'error' in quote:
                print(f"  ❌ Error: {quote['error']}")
                logger.error("Failed to fetch quote", symbol=symbol, error=quote['error'])
            else:
                price = quote.get('price', 0)
                change = quote.get('change_percent', 0)

                print(f"  ✅ Price: ${price:.2f} ({change:+.2f}%)")
                print(f"     • Fetched in {duration:.3f}s")

                logger.log_api_call('market', 'get_quote', True, duration, symbol=symbol)

        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            logger.error("Exception fetching market data", error=e, symbol=symbol)

def test_fred_data_fetching(capabilities):
    """Test FRED data capability"""
    print("\n4. Testing FRED Economic Data")
    print("-" * 40)

    fred = capabilities.get('fred')
    if not fred:
        print("  ❌ FRED capability not available")
        return

    indicators = ['GDP', 'CPI', 'UNEMPLOYMENT']

    for indicator in indicators:
        print(f"\nFetching: {indicator}")
        start_time = time.time()

        try:
            data = fred.get_latest(indicator)
            duration = time.time() - start_time

            if 'error' in data:
                print(f"  ❌ Error: {data['error']}")
                logger.error("Failed to fetch indicator", indicator=indicator, error=data['error'])
            else:
                value = data.get('value', 0)
                trend = data.get('trend', 'unknown')

                print(f"  ✅ Value: {value:.2f}")
                print(f"     • Trend: {trend}")
                print(f"     • Fetched in {duration:.3f}s")

                logger.log_api_call('fred', 'get_latest', True, duration, indicator=indicator)

        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            logger.error("Exception fetching FRED data", error=e, indicator=indicator)

def test_pattern_matching(runtime):
    """Test pattern matching accuracy"""
    print("\n5. Testing Pattern Matching")
    print("-" * 40)

    pattern_engine = runtime.pattern_engine

    test_cases = [
        ("What's the stock price of AAPL?", "stock_price"),
        ("Analyze economic moat for Microsoft", "moat_analyzer"),
        ("Where are we in the debt cycle?", "dalio_cycle"),
        ("Show me correlations for SPY", "correlation_finder"),
        ("What is the market regime?", "market_regime")
    ]

    correct_matches = 0

    for query, expected_pattern in test_cases:
        print(f"\nQuery: '{query}'")
        print(f"Expected: {expected_pattern}")

        pattern = pattern_engine.find_pattern(query)

        if pattern:
            actual_id = pattern.get('id', 'unknown')
            if actual_id == expected_pattern:
                print(f"  ✅ Correct match: {actual_id}")
                correct_matches += 1
            else:
                print(f"  ❌ Wrong match: {actual_id}")
        else:
            print("  ❌ No pattern matched")

    accuracy = (correct_matches / len(test_cases)) * 100
    print(f"\nPattern matching accuracy: {accuracy:.1f}%")
    logger.info("Pattern matching test completed", accuracy=accuracy)

def test_data_harvester_integration(runtime):
    """Test DataHarvester with real capabilities"""
    print("\n6. Testing DataHarvester Integration")
    print("-" * 40)

    test_requests = [
        "Get price data for AAPL",
        "Fetch macro economic data",
        "Get correlations for SPY"
    ]

    harvester = runtime.get_agent_instance('data_harvester') if hasattr(runtime, 'get_agent_instance') else None
    if not harvester:
        print("  ❌ DataHarvester not available")
        return

    for request in test_requests:
        print(f"\nRequest: '{request}'")
        start_time = time.time()

        try:
            result = harvester.harvest(request)
            duration = time.time() - start_time

            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
            elif 'data' in result and result['data']:
                print(f"  ✅ Success ({duration:.2f}s)")
                print(f"     • Data keys: {list(result['data'].keys())[:5]}")
                print(f"     • Response: {result.get('response', 'N/A')}")

                logger.log_agent_execution('data_harvester', {'request': request}, result, duration)
            else:
                print("  ⚠️ No data returned")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            logger.error("DataHarvester exception", error=e, request=request)

# Main test execution
def main():
    """Run all integration tests"""
    print("\nInitializing DawsOS...")

    try:
        runtime, graph, capabilities = setup_system()
        print("✅ System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        logger.error("System initialization failed", error=e)
        return

    # Run test suites
    test_economic_moat_analysis(runtime)
    test_debt_cycle_analysis(runtime)
    test_market_data_fetching(capabilities)
    test_fred_data_fetching(capabilities)
    test_pattern_matching(runtime)
    test_data_harvester_integration(runtime)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    metrics = logger.get_metrics()

    print("\nMetrics:")
    print(f"  • API Calls: {metrics['api_calls']}")
    print(f"  • Pattern Matches: {metrics['pattern_matches']}")
    print(f"  • Agent Executions: {metrics['agent_executions']}")
    print(f"  • Errors: {metrics['errors']}")
    print(f"  • Warnings: {metrics['warnings']}")
    print(f"  • Cache Hit Rate: {metrics['cache_hit_rate']:.1%}")

    # Save metrics
    logger.write_metrics()
    print("\nMetrics saved to logs/")

    if metrics['errors'] == 0:
        print("\n✅ All tests completed successfully!")
    else:
        print(f"\n⚠️ Tests completed with {metrics['errors']} errors")

if __name__ == "__main__":
    main()
