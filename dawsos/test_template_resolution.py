#!/usr/bin/env python3
"""
Debug template resolution in detail
"""
from load_env import load_env
load_env()

from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime
from core.knowledge_graph import KnowledgeGraph

from agents.claude import Claude
from agents.data_harvester import DataHarvester
from agents.relationship_hunter import RelationshipHunter
from capabilities.market_data import MarketDataCapability

# Initialize
graph = KnowledgeGraph()
runtime = AgentRuntime()

# Register agents
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

# Initialize pattern engine
pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

# Get pattern
pattern = pattern_engine.get_pattern('correlation_finder')
print(f"Pattern: {pattern['name']}")
print(f"Response Template: {pattern.get('response_template')}")

# Execute pattern
context = {'user_input': 'Find correlations for SPY'}
print(f"\nExecuting pattern...")

# Manually execute steps to see outputs
step_outputs = {}

# Step 1: data_harvester
step1_params = {'request': 'Get historical data for SPY and major assets: SPY QQQ DXY GLD TLT VIX'}
print(f"\n1. data_harvester with params: {step1_params}")
result1 = runtime.execute('data_harvester', step1_params)
print(f"   Result keys: {list(result1.keys())}")
print(f"   Response: {result1.get('response', 'N/A')[:50]}...")
step_outputs['price_data'] = result1

# Step 2: relationship_hunter
step2_params = {'data': result1, 'target': 'SPY'}
print(f"\n2. relationship_hunter with data from step 1")
result2 = runtime.execute('relationship_hunter', step2_params)
print(f"   Result keys: {list(result2.keys())}")
print(f"   Response: {result2.get('response', 'N/A')}")
step_outputs['correlations'] = result2

# Step 3: claude
step3_params = {'user_input': f"Analyze correlations for SPY: {result2}. Explain: 1) Strong correlations found 2) Inverse relationships 3) Trading implications 4) Hedge opportunities"}
print(f"\n3. claude with correlation analysis request")
result3 = runtime.execute('claude', step3_params)
print(f"   Result keys: {list(result3.keys())}")
print(f"   Response: {result3.get('response', 'N/A')[:100]}...")
step_outputs['correlation_report'] = result3

# Now test template substitution
print("\n" + "=" * 80)
print("TEMPLATE SUBSTITUTION TEST")
print("=" * 80)

template = pattern.get('response_template', '')
print(f"Original template: {template}")

# Try substitution as the pattern engine does it
for key, value in step_outputs.items():
    print(f"\nSubstituting {key}:")
    print(f"  Value type: {type(value)}")
    if isinstance(value, dict):
        print(f"  Value keys: {list(value.keys())}")
        if 'response' in value:
            print(f"  Has 'response': {value['response'][:50]}...")
            template = template.replace(f"{{{key}}}", str(value['response']))
        elif 'correlations' in value:
            print(f"  Has 'correlations': {value['correlations']}")
            template = template.replace(f"{{{key}}}", str(value['correlations']))

print(f"\nFinal template: {template[:200]}...")

print("\n✅ Template should now show the actual response instead of {correlation_report}")