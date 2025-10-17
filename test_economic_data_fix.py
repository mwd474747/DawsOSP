#!/usr/bin/env python3
"""
Test script to verify economic data fix is working.

This script tests the complete flow: PatternEngine → Capability Routing → API Call
"""
import sys
sys.path.insert(0, 'dawsos')

from load_env import load_env
load_env()

from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.pattern_engine import PatternEngine
from core.agent_capabilities import AGENT_CAPABILITIES
from agents.data_harvester import DataHarvester
from capabilities.fred_data import FredDataCapability
from capabilities.market_data import MarketDataCapability
from capabilities.news import NewsCapability
from capabilities.crypto import CryptoCapability
from capabilities.fundamentals import FundamentalsCapability

print('='*60)
print('Testing Economic Data Flow After Fix')
print('='*60)

# Initialize like main.py does
print('\n1. Initializing runtime...')
graph = KnowledgeGraph()
runtime = AgentRuntime()
runtime.graph = graph

caps = {
    'fred': FredDataCapability(),
    'market': MarketDataCapability(),
    'news': NewsCapability(),
    'crypto': CryptoCapability(),
    'fundamentals': FundamentalsCapability()
}

runtime.register_agent(
    'data_harvester',
    DataHarvester(graph, caps),
    capabilities=AGENT_CAPABILITIES['data_harvester']
)
print('✓ Runtime initialized')

# Initialize PatternEngine
print('\n2. Initializing PatternEngine...')
pattern_engine = PatternEngine(runtime=runtime, graph=graph)
runtime.pattern_engine = pattern_engine
print('✓ PatternEngine initialized')

# Test the method that was broken
print('\n3. Testing PatternEngine._get_macro_economic_data()...')
print('   (This method now includes the fix: context["capability"] = ...)')

# This will call the fixed code in pattern_engine.py line 1879
result = pattern_engine._get_macro_economic_data({})

print(f'\n4. Results:')
print(f'   Indicators count: {result.get("indicators_count", 0)}')
print(f'   Has data: {result.get("indicators_count", 0) > 0}')

if result.get('indicators'):
    print(f'\n5. Sample indicators:')
    for indicator in list(result['indicators'])[:3]:
        print(f'   • {indicator["indicator"]}: {indicator["value"]} ({indicator["date"]})')
    print(f'\n✅ SUCCESS: Economic data is flowing correctly!')
    print(f'   Source: Live FRED API data')
    exit(0)
else:
    print(f'\n❌ FAILED: No indicators returned')
    print(f'   This means the fix may not have been applied or there is another issue')
    if 'error' in result:
        print(f'   Error: {result["error"]}')
    exit(1)
