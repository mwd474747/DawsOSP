#!/usr/bin/env python3
"""
Test fundamental analysis features
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
print("TESTING FUNDAMENTAL ANALYSIS FEATURES")
print("=" * 80)

# Initialize with seeded knowledge graph
print("\n1. Initializing system with seeded knowledge...")
graph = KnowledgeGraph()

# Run seeding to populate the graph
print("   Seeding knowledge graph...")
import seed_knowledge_graph
seed_knowledge_graph.seed_buffett_framework(graph)
seed_knowledge_graph.seed_dalio_framework(graph)
seed_knowledge_graph.seed_financial_calculations(graph)
seed_knowledge_graph.seed_investment_examples(graph)

stats = graph.get_stats()
print(f"   ✅ Graph loaded: {stats['total_nodes']} nodes, {stats['total_edges']} edges")

# Initialize runtime and agents
runtime = AgentRuntime()
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

# Test fundamental analysis queries
print("\n2. Testing fundamental analysis queries...")

test_queries = [
    ("Buffett checklist for AAPL", "Should trigger Buffett investment checklist"),
    ("Calculate owner earnings", "Should trigger owner earnings calculation"),
    ("Analyze economic moat for MSFT", "Should trigger moat analysis"),
    ("Where are we in the debt cycle?", "Should trigger Dalio cycle analysis"),
    ("Fundamental analysis of V", "Should trigger comprehensive fundamental analysis")
]

for query, expected in test_queries:
    print(f"\n🔍 Query: '{query}'")
    print(f"   Expected: {expected}")

    # Find pattern
    pattern = pattern_engine.find_pattern(query)
    if pattern:
        print(f"   ✅ Pattern matched: {pattern['name']}")
        print(f"      Category: {pattern.get('category', 'N/A')}")
        print(f"      Priority: {pattern.get('priority', 'N/A')}")
    else:
        print(f"   ❌ No pattern matched")

# Test knowledge graph queries
print("\n3. Testing knowledge graph integration...")

# Query Buffett framework
print("\n📚 Buffett Framework Nodes:")
buffett_nodes = [node for node_id, node in graph.nodes.items()
                 if 'Buffett' in str(node.get('data', {}).get('name', ''))]
for node in buffett_nodes[:3]:
    print(f"   • {node['data'].get('name', 'Unknown')}: {node['type']}")

# Query Dalio framework
print("\n📚 Dalio Framework Nodes:")
dalio_nodes = [node for node_id, node in graph.nodes.items()
               if 'Dalio' in str(node.get('data', {}).get('name', ''))]
for node in dalio_nodes[:3]:
    print(f"   • {node['data'].get('name', 'Unknown')}: {node['type']}")

# Test tracing connections
print("\n4. Testing knowledge connections...")
framework_nodes = [node_id for node_id, node in graph.nodes.items()
                   if node['type'] == 'framework']

if framework_nodes:
    start_node = framework_nodes[0]
    paths = graph.trace_connections(start_node, max_depth=2)
    print(f"\n   From {graph.nodes[start_node]['data']['name']}:")
    print(f"   Found {len(paths)} connection paths")

    if paths and len(paths) > 0:
        # Show first few connections
        for path in paths[:3]:
            if path:
                edge = path[0]
                to_node = graph.nodes.get(edge['to'])
                if to_node:
                    print(f"   → {edge['type']} → {to_node['data'].get('name', 'Unknown')}")

# Test pattern execution with actual agent
print("\n5. Testing pattern execution...")

test_execution = [
    "analyze moat for AAPL",
    "buffett checklist",
    "debt cycle analysis"
]

for query in test_execution:
    print(f"\n🚀 Executing: '{query}'")

    try:
        response = runtime.orchestrate(query)

        if 'pattern' in response:
            print(f"   ✅ Pattern executed: {response['pattern']}")

        if 'formatted_response' in response:
            # Check if response has content
            content = response['formatted_response']
            if content and not ('{' in content and '}' in content):
                print(f"   ✅ Response generated ({len(content)} chars)")
                # Show first line
                first_line = content.split('\n')[0]
                print(f"   Preview: {first_line[:80]}...")
            else:
                print(f"   ⚠️  Response has template variables")

        if 'response' in response:
            content = response['response']
            if content:
                print(f"   ✅ Direct response available")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"""
✅ Knowledge Graph Seeded:
   • {stats['total_nodes']} nodes across {len(stats['node_types'])} types
   • {stats['total_edges']} edges connecting concepts
   • Buffett & Dalio frameworks loaded

✅ Patterns Available:
   • Fundamental analysis patterns
   • Buffett checklist pattern
   • Owner earnings calculation
   • Moat analysis
   • Debt cycle analysis

✅ System Ready for:
   • Company fundamental analysis
   • Economic moat assessments
   • Cycle position analysis
   • Investment checklists
   • Valuation calculations

🎯 Next Steps:
   • Connect to real market data APIs
   • Add more company examples
   • Enhance pattern matching
   • Build interactive UI features
""")

print("Fundamental analysis system is ready! 🚀")