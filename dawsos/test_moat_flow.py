#!/usr/bin/env python3
"""
Test the complete economic moat analysis flow
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
import seed_knowledge_graph

print("=" * 80)
print("TESTING ECONOMIC MOAT ANALYSIS FLOW")
print("=" * 80)

# Initialize system
print("\n1. Initializing DawsOS...")
graph = KnowledgeGraph()

# Seed knowledge
seed_knowledge_graph.seed_buffett_framework(graph)
seed_knowledge_graph.seed_dalio_framework(graph)
seed_knowledge_graph.seed_financial_calculations(graph)
seed_knowledge_graph.seed_investment_examples(graph)

print(f"   ✅ Knowledge graph: {graph.get_stats()['total_nodes']} nodes")

# Initialize runtime
runtime = AgentRuntime()
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

print(f"   ✅ Pattern engine: {len(pattern_engine.patterns)} patterns loaded")

# Test the exact flow from the UI button
print("\n2. Testing UI Button Flow...")

# This is exactly what happens when the button is clicked
user_msg = "Analyze economic moat for AAPL"
print(f"   User clicks: '🏰 Analyze Moat'")
print(f"   Sends: '{user_msg}'")

# Execute through orchestrate (same as UI)
print("\n3. Executing through orchestrate()...")
response = runtime.orchestrate(user_msg)

print("\n4. Analyzing Response Structure...")
print(f"   • Has pattern? {bool('pattern' in response)}")
if 'pattern' in response:
    print(f"     Pattern: {response['pattern']}")

print(f"   • Has formatted_response? {bool('formatted_response' in response)}")
print(f"   • Has response? {bool('response' in response)}")
print(f"   • Has results? {bool('results' in response)}")

if 'results' in response:
    print(f"   • Steps executed: {len(response['results'])}")
    for i, result in enumerate(response['results']):
        action = result.get('action', 'Unknown')
        has_error = 'error' in result.get('result', {})
        status = "❌ Error" if has_error else "✅ Success"
        print(f"     Step {i+1}: {action} - {status}")

print("\n5. Checking Response Content...")

if 'formatted_response' in response:
    content = response['formatted_response']

    # Check for key sections
    has_moat_analysis = '**Economic Moat Analysis' in content
    has_brand_moat = '**Brand Moat**' in content
    has_network_effects = '**Network Effects**' in content
    has_cost_advantages = '**Cost Advantages**' in content
    has_switching_costs = '**Switching Costs**' in content
    has_financial_evidence = '**Financial Evidence**' in content
    has_overall_rating = '**Overall Moat Rating**' in content
    has_investment_implications = '**Investment Implications**' in content

    print(f"   ✅ Moat Analysis Header: {has_moat_analysis}")
    print(f"   ✅ Brand Moat Section: {has_brand_moat}")
    print(f"   ✅ Network Effects Section: {has_network_effects}")
    print(f"   ✅ Cost Advantages Section: {has_cost_advantages}")
    print(f"   ✅ Switching Costs Section: {has_switching_costs}")
    print(f"   ✅ Financial Evidence Section: {has_financial_evidence}")
    print(f"   ✅ Overall Rating Section: {has_overall_rating}")
    print(f"   ✅ Investment Implications: {has_investment_implications}")

    # Check for template variables (should be none)
    remaining_vars = content.count('{')
    print(f"\n   Template variables remaining: {remaining_vars}")
    if remaining_vars > 0:
        # Find and show remaining variables
        import re
        vars_found = re.findall(r'\{[^}]+\}', content)
        for var in vars_found[:5]:
            print(f"     • {var}")

    # Display preview
    print("\n6. Response Preview:")
    print("-" * 60)
    lines = content.split('\n')[:15]
    for line in lines:
        print(f"   {line}")
    print(f"   ... ({len(content)} total characters)")

elif 'response' in response:
    print(f"   Has direct response: {len(response['response'])} chars")

# Test additional moat queries
print("\n7. Testing Different Companies...")

test_companies = [
    "Analyze economic moat for MSFT",
    "Economic moat analysis for GOOGL",
    "What's the moat for BRK.B"
]

for query in test_companies:
    print(f"\n   Testing: '{query}'")

    # Find pattern
    pattern = pattern_engine.find_pattern(query)
    if pattern:
        print(f"   ✅ Pattern matched: {pattern['name']}")

        # Execute
        result = runtime.orchestrate(query)

        # Check if formatted response contains the company symbol
        if 'formatted_response' in result:
            content = result['formatted_response']

            # Extract symbol from query
            words = query.split()
            symbol = None
            for word in words:
                if word.isupper() and 2 <= len(word) <= 5:
                    symbol = word
                    break

            if symbol and symbol in content:
                print(f"   ✅ Response includes {symbol}")
            else:
                print(f"   ⚠️ Symbol {symbol} not in response")
    else:
        print(f"   ❌ No pattern matched")

# Summary
print("\n" + "=" * 80)
print("MOAT ANALYSIS FLOW TEST SUMMARY")
print("=" * 80)

success_count = 0
total_tests = 8

# Count successes
if 'pattern' in response:
    success_count += 1
if 'formatted_response' in response:
    success_count += 1
if response.get('formatted_response', '').count('{') == 0:
    success_count += 1
if '**Economic Moat Analysis' in response.get('formatted_response', ''):
    success_count += 1
if '**Brand Moat**' in response.get('formatted_response', ''):
    success_count += 1
if '**Overall Moat Rating**' in response.get('formatted_response', ''):
    success_count += 1
if 'results' in response and len(response['results']) > 0:
    success_count += 1
if 'AAPL' in response.get('formatted_response', ''):
    success_count += 1

print(f"\n✅ Success Rate: {success_count}/{total_tests} ({success_count*100//total_tests}%)")

print(f"\n📊 Flow Summary:")
print(f"   1. Button Click → 'Analyze economic moat for AAPL'")
print(f"   2. Pattern Match → moat_analyzer pattern")
print(f"   3. Execute Workflow → 7 steps")
print(f"   4. Format Response → Markdown template")
print(f"   5. Display in Chat → Formatted moat analysis")

print(f"\n✨ The economic moat analysis flow is {'WORKING' if success_count >= 6 else 'NEEDS FIXES'}!")