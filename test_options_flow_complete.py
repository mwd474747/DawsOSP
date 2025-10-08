#!/usr/bin/env python3
"""
Complete execution trace for options flow analysis
Tests every step from pattern matching through to API call
"""
import sys
import os
sys.path.insert(0, '/Users/mdawson/Dawson/DawsOSB/dawsos')
os.chdir('/Users/mdawson/Dawson/DawsOSB')

print("=" * 80)
print("COMPLETE OPTIONS FLOW EXECUTION TRACE")
print("=" * 80)
print()

# Step 1: Load environment
print("STEP 1: Load Environment")
print("-" * 40)
from load_env import load_env
load_env()
polygon_key = os.environ.get('POLYGON_API_KEY', '')
print(f"POLYGON_API_KEY loaded: {bool(polygon_key)}")
print(f"Key length: {len(polygon_key)} characters")
print(f"Key preview: {polygon_key[:10]}..." if polygon_key else "NO KEY")
print()

# Step 2: Initialize components
print("STEP 2: Initialize Core Components")
print("-" * 40)
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.pattern_engine import PatternEngine
from core.agent_capabilities import AGENT_CAPABILITIES
from agents.financial_analyst import FinancialAnalyst
from agents.data_harvester import DataHarvester
from capabilities.polygon_options import PolygonOptionsCapability

graph = KnowledgeGraph()
polygon_cap = PolygonOptionsCapability()
print(f"✓ PolygonOptionsCapability initialized")
print(f"  API key set: {bool(polygon_cap.api_key)}")
print(f"  API key length: {len(polygon_cap.api_key) if polygon_cap.api_key else 0}")
print()

capabilities = {'polygon': polygon_cap}

# Step 3: Create and register agents
print("STEP 3: Create and Register Agents")
print("-" * 40)
fa = FinancialAnalyst(graph, capabilities, 'financial_analyst')
dh = DataHarvester(graph, capabilities, 'data_harvester')
print(f"✓ FinancialAnalyst created")
print(f"  Has polygon capability: {'polygon' in fa.capabilities}")
print(f"✓ DataHarvester created")
print(f"  Has polygon capability: {'polygon' in dh.capabilities}")
print()

runtime = AgentRuntime(graph)
runtime.register_agent('financial_analyst', fa, AGENT_CAPABILITIES['financial_analyst'])
runtime.register_agent('data_harvester', dh, AGENT_CAPABILITIES['data_harvester'])
print(f"✓ Agents registered with runtime")
print(f"  Registered agents: {list(runtime.agent_registry.list_agents())}")
print()

# Step 4: Pattern matching
print("STEP 4: Pattern Matching")
print("-" * 40)
pe = PatternEngine('dawsos/patterns', runtime)
user_input = "Analyze options flow for SPY"
pattern = pe.find_pattern(user_input)
print(f"Input: '{user_input}'")
print(f"Matched pattern: {pattern.get('id') if pattern else 'NONE'}")
if pattern:
    print(f"Pattern name: {pattern.get('name')}")
    print(f"Pattern priority: {pattern.get('priority')}")
    print(f"Pattern entities: {pattern.get('entities')}")
print()

# Step 5: Entity extraction
print("STEP 5: Entity Extraction")
print("-" * 40)
if pattern:
    entities = pe.extract_entities(pattern, user_input)
    print(f"Extracted entities: {entities}")
    print()

# Step 6: Execute pattern with full tracing
print("STEP 6: Execute Pattern (Full Trace)")
print("-" * 40)
if pattern and entities:
    context = {'user_input': user_input}
    context.update(entities)
    print(f"Execution context: {context}")
    print()

    print("Executing pattern steps...")
    result = pe.execute_pattern(pattern, context)

    print()
    print("EXECUTION RESULT:")
    print(f"  Keys: {list(result.keys())}")
    if 'results' in result:
        print(f"  Step results:")
        for i, step_result in enumerate(result['results'], 1):
            print(f"    Step {i}: {step_result.get('action', 'unknown')}")
            if 'error' in step_result.get('result', {}):
                print(f"      ERROR: {step_result['result']['error']}")
            else:
                print(f"      Result keys: {list(step_result.get('result', {}).keys())}")

    if 'formatted_response' in result:
        print()
        print("FORMATTED RESPONSE:")
        print(result['formatted_response'])

    print()
    print("RAW RESULT:")
    import json
    print(json.dumps(result, indent=2, default=str))

print()
print("=" * 80)
print("TRACE COMPLETE")
print("=" * 80)
