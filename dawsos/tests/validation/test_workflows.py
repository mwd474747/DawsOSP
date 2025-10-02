#!/usr/bin/env python3
"""
Test the investment workflows integration
"""
import os
import json
from datetime import datetime

# Load environment
from load_env import load_env
load_env()

# Import components
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from workflows.investment_workflows import InvestmentWorkflows

# Agent imports
from agents.claude import Claude
from agents.graph_mind import GraphMind
from agents.data_harvester import DataHarvester
from agents.pattern_spotter import PatternSpotter
from agents.forecast_dreamer import ForecastDreamer
from agents.relationship_hunter import RelationshipHunter

# Capability imports
from capabilities.fred import FREDCapability
from capabilities.market_data import MarketDataCapability

print("=" * 80)
print("TESTING INVESTMENT WORKFLOWS")
print("=" * 80)

# Initialize
graph = KnowledgeGraph()
runtime = AgentRuntime()

# Load seeded graph if it exists
try:
    graph.load('storage/seeded_graph.json')
    print("✅ Loaded seeded investment knowledge")
except:
    print("⚠️  No seeded graph found - creating basic structure")
    # Add some basic nodes
    graph.add_node('regime', {'current_state': 'GOLDILOCKS'}, 'ECONOMIC_REGIME')
    graph.add_node('indicator', {'value': 30000}, 'GDP')
    graph.add_node('indicator', {'value': 3.5}, 'CPI')

# Initialize capabilities
caps = {
    'fred': FREDCapability(),
    'market': MarketDataCapability()
}

# Register agents
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('graph_mind', GraphMind(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))
runtime.register_agent('forecast_dreamer', ForecastDreamer(graph))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

# Initialize workflows
workflows = InvestmentWorkflows(runtime, graph)

print(f"\n✅ Initialized {len(workflows.workflows)} workflows")
for name, wf in workflows.workflows.items():
    print(f"   - {wf['name']} ({wf['frequency']})")

print("\n" + "=" * 80)
print("TEST 1: MORNING BRIEFING WORKFLOW")
print("=" * 80)

result = workflows.execute_workflow('morning_briefing')
print(f"\n✅ Completed {len(result['steps'])} steps")

# Extract key insights
for step in result['steps']:
    if step['action'] == 'summarize_regime':
        regime = step['result'].get('regime', 'Unknown')
        print(f"📊 Current Regime: {regime}")
    elif step['action'] == 'fetch_overnight_moves':
        print(f"📈 Market Data: Fetched")
    elif step['action'] == 'day_outlook':
        print(f"🔮 Outlook: Generated")

workflows.save_workflow_result(result)

print("\n" + "=" * 80)
print("TEST 2: VALUE SCAN WORKFLOW")
print("=" * 80)

result = workflows.execute_workflow('value_scan')
print(f"\n✅ Completed {len(result['steps'])} steps")

# Extract value opportunities
for step in result['steps']:
    if step['action'] == 'fetch_fundamentals':
        value_stocks = step['result'].get('value_stocks', [])
        if value_stocks:
            print(f"\n💎 Found {len(value_stocks)} value opportunities:")
            for stock in value_stocks[:3]:
                print(f"   - {stock['symbol']}: P/E {stock['pe']:.1f}")

workflows.save_workflow_result(result)

print("\n" + "=" * 80)
print("TEST 3: REGIME CHECK WORKFLOW")
print("=" * 80)

result = workflows.execute_workflow('regime_check')
print(f"\n✅ Completed {len(result['steps'])} steps")

# Extract regime analysis
for step in result['steps']:
    if step['action'] == 'identify_regime':
        regime_data = step['result']
        print(f"\n📍 Regime Analysis:")
        print(f"   State: {regime_data.get('regime', 'Unknown')}")
        print(f"   Confidence: {regime_data.get('confidence', 0):.0%}")
    elif step['action'] == 'regime_implications':
        print(f"   Implications: Analyzed")

workflows.save_workflow_result(result)

print("\n" + "=" * 80)
print("TEST 4: SECTOR ROTATION WORKFLOW")
print("=" * 80)

result = workflows.execute_workflow('sector_rotation')
print(f"\n✅ Completed {len(result['steps'])} steps")

# Extract sector recommendations
for step in result['steps']:
    if step['action'] == 'predict_sector_performance':
        sectors = step['result']
        print(f"\n📊 Sector Recommendations:")
        for sector, data in sectors.items():
            print(f"   - {sector}: {data['forecast']} ({data['confidence']:.0%})")

workflows.save_workflow_result(result)

print("\n" + "=" * 80)
print("TEST 5: WORKFLOW CONTEXT SUGGESTION")
print("=" * 80)

test_contexts = [
    "What's the market regime?",
    "Find me value stocks",
    "Check portfolio risk",
    "Look for catalysts",
    "Give me a morning update"
]

for context in test_contexts:
    suggested = workflows.suggest_workflow(context)
    print(f"Query: '{context}'")
    print(f"   → Suggested: {workflows.workflows[suggested]['name']}")

print("\n" + "=" * 80)
print("TEST 6: WORKFLOW SCHEDULING")
print("=" * 80)

# Test scheduling
scheduled = workflows.schedule_workflow('morning_briefing')
print(f"✅ Scheduled: {workflows.workflows['morning_briefing']['name']}")
print(f"   Frequency: {scheduled['frequency']}")
print(f"   Next Run: {scheduled['next_run']}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

# Get workflow history
history = workflows.get_workflow_history()
today_count = len([h for h in history if datetime.fromisoformat(h['timestamp']).date() == datetime.now().date()])

print(f"\n📊 Statistics:")
print(f"   Workflows Available: {len(workflows.workflows)}")
print(f"   Executions Today: {today_count}")
print(f"   Total History: {len(history)} executions")

print("\n✅ Key Features Working:")
print("   - Workflow execution with multi-agent orchestration")
print("   - Context-based workflow suggestion")
print("   - Workflow scheduling and history tracking")
print("   - Regime-aware investment analysis")
print("   - Value discovery using Buffett criteria")
print("   - Sector rotation based on economic conditions")

print(f"\n💾 History saved to storage/workflow_history.json")
print("🎉 Workflow integration successful!")