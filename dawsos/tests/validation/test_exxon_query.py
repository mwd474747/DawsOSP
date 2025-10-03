#!/usr/bin/env python3
"""
Test why "what is the economic moat of Exxon?" doesn't work
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
print("TESTING EXXON MOAT QUERY")
print("=" * 80)

# Initialize
graph = KnowledgeGraph()
seed_knowledge_graph.seed_buffett_framework(graph)

runtime = AgentRuntime()
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

# Test different query variations
test_queries = [
    "what is the economic moat of Exxon?",
    "What is the economic moat of Exxon",
    "economic moat of Exxon",
    "analyze economic moat for XOM",
    "Exxon moat analysis",
    "what's the moat for XOM",
    "analyze moat for Exxon"
]

print("\n1. Testing Pattern Matching for Various Queries:\n")

for query in test_queries:
    print(f"Query: '{query}'")

    # Find pattern
    pattern = pattern_engine.find_pattern(query)

    if pattern:
        print(f"  ✅ Pattern matched: {pattern['name']} (id: {pattern['id']})")
        print(f"     Priority: {pattern.get('priority', 'N/A')}")

        # Check triggers
        if 'triggers' in pattern:
            triggers = pattern['triggers']
            matching_triggers = [t for t in triggers if t.lower() in query.lower()]
            if matching_triggers:
                print(f"     Matched triggers: {matching_triggers}")

        if 'trigger_phrases' in pattern:
            phrases = pattern['trigger_phrases']
            for phrase in phrases:
                # Simple check if phrase words are in query
                phrase_words = phrase.lower().replace('{symbol}', '').replace('{', '').replace('}', '').split()
                if all(word in query.lower() for word in phrase_words if word):
                    print(f"     Matched phrase: '{phrase}'")
                    break
    else:
        print("  ❌ No pattern matched")

    print()

# Now test the actual execution
print("\n2. Testing Execution of Best Query:\n")

best_query = "what is the economic moat of Exxon?"
print(f"Executing: '{best_query}'")

try:
    response = runtime.orchestrate(best_query)

    print("\nResponse Structure:")
    print(f"  • Has pattern: {bool('pattern' in response)}")
    print(f"  • Has formatted_response: {bool('formatted_response' in response)}")
    print(f"  • Has response: {bool('response' in response)}")

    if 'pattern' in response:
        print(f"  • Pattern used: {response['pattern']}")

    if 'formatted_response' in response:
        content = response['formatted_response']
        print(f"\n  Response Preview ({len(content)} chars):")
        print("-" * 60)
        lines = content.split('\n')[:10]
        for line in lines:
            print(f"  {line}")

        # Check if Exxon/XOM is mentioned
        if 'Exxon' in content or 'XOM' in content:
            print("\n  ✅ Company name/symbol included in response")
        else:
            print("\n  ❌ Company name/symbol NOT in response")

    elif 'response' in response:
        print(f"\n  Direct response: {response['response'][:200]}...")

except Exception as e:
    print(f"  ❌ Error: {str(e)}")

# Analyze the problem
print("\n" + "=" * 80)
print("PROBLEM ANALYSIS")
print("=" * 80)

# Check moat_analyzer pattern
import json
import os

moat_pattern_path = 'patterns/analysis/moat_analyzer.json'
if os.path.exists(moat_pattern_path):
    with open(moat_pattern_path, 'r') as f:
        moat_pattern = json.load(f)

    print("\nMoat Analyzer Pattern Configuration:")
    print(f"  Triggers: {moat_pattern.get('triggers', [])}")
    print(f"  Trigger Phrases: {moat_pattern.get('trigger_phrases', [])[:3]}...")
    print(f"  Priority: {moat_pattern.get('priority', 'N/A')}")

print("\nIssues Found:")
issues = []

# Check if "what is" is handled
if not pattern_engine.find_pattern("what is the economic moat of Exxon?"):
    issues.append("Pattern doesn't match 'what is...' questions")

# Check if company names are handled
if not pattern_engine.find_pattern("economic moat of Exxon"):
    issues.append("Pattern doesn't match company names (only symbols)")

# Check if questions with ? are handled
if not pattern_engine.find_pattern("what's the moat for XOM?"):
    issues.append("Pattern doesn't handle questions with '?'")

if issues:
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
else:
    print("  No issues found - pattern matching seems to work")

print("\nRecommended Fixes:")
print("  1. Add 'what is', 'what's', 'tell me about' to trigger phrases")
print("  2. Add company name to symbol mapping (Exxon → XOM)")
print("  3. Ensure pattern matching ignores punctuation like '?'")
print("  4. Consider adding more natural language variations")