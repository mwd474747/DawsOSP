#!/usr/bin/env python3
"""
Debug pattern execution to see why templates aren't resolving
"""
from load_env import load_env
load_env()

from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime
from core.knowledge_graph import KnowledgeGraph

from agents.claude import Claude
from agents.data_harvester import DataHarvester
from agents.pattern_spotter import PatternSpotter
from agents.relationship_hunter import RelationshipHunter
from capabilities.market_data import MarketDataCapability

print("=" * 80)
print("DEBUGGING PATTERN TEMPLATE RESOLUTION")
print("=" * 80)

# Initialize
graph = KnowledgeGraph()
runtime = AgentRuntime()

# Register agents
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

# Initialize pattern engine
pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

# Test correlation pattern
print("\nTesting 'Find correlations for SPY' pattern...")
pattern = pattern_engine.find_pattern("Find correlations for SPY")
print(f"Pattern found: {pattern['name']}")
print(f"Template: {pattern.get('response_template', 'No template')}")

# Execute pattern with detailed output
context = {'user_input': 'Find correlations for SPY'}
result = pattern_engine.execute_pattern(pattern, context)

print("\n📊 Pattern Results:")
print(f"Pattern: {result.get('pattern', 'Unknown')}")
print(f"Has formatted_response: {'formatted_response' in result}")

if 'formatted_response' in result:
    print("\nFormatted Response:")
    print(result['formatted_response'])

print("\n🔍 Step Outputs:")
if 'results' in result:
    for step_result in result['results']:
        print(f"\nStep {step_result['step']}: {step_result['agent']}")
        agent_result = step_result.get('result', {})
        if isinstance(agent_result, dict):
            print(f"  Keys: {list(agent_result.keys())}")
            if 'response' in agent_result:
                print(f"  Response: {str(agent_result['response'])[:100]}...")
            if 'friendly_response' in agent_result:
                print(f"  Friendly Response: {str(agent_result['friendly_response'])[:100]}...")
            if 'data' in agent_result:
                print("  Has data: Yes")

print("\n" + "=" * 80)