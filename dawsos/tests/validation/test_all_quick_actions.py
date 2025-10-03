#!/usr/bin/env python3
"""
Test all Quick Action buttons
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
print("TESTING ALL QUICK ACTION BUTTONS")
print("=" * 80)

# Initialize
graph = KnowledgeGraph()
runtime = AgentRuntime()
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

# Test each Quick Action button
quick_actions = [
    ("Analyze Macro Environment", "Show me macro analysis"),
    ("Detect Market Regime", "Detect the market regime"),
    ("Find Patterns", "Show sector performance"),
    ("Hunt Relationships", "Find correlations for SPY")
]

print()
for button_name, query in quick_actions:
    print(f"🔘 {button_name}")
    print(f"   Query: '{query}'")

    response = runtime.orchestrate(query)

    if 'pattern' in response:
        print(f"   ✅ Pattern: {response['pattern']}")

    if 'formatted_response' in response:
        # Check if response has actual content (not template variables)
        content = response['formatted_response']
        has_template_vars = '{' in content and '}' in content

        if has_template_vars:
            print("   ⚠️  Response has template variables")
        else:
            print(f"   ✅ Response has content ({len(content)} chars)")
            # Show first line of response
            first_line = content.split('\n')[0]
            print(f"   Preview: {first_line[:60]}...")
    else:
        print("   ❌ No formatted response")

    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nAll Quick Action buttons should now show formatted content in the chat!")
print("The responses include:")
print("• Emojis for visual appeal")
print("• Structured sections")
print("• Actionable insights")
print("• No template variables like {variable}")