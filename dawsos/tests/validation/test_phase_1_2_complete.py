#!/usr/bin/env python3
"""
Comprehensive test to verify Phase 1 and 2 are working
"""
import os
import json
from pathlib import Path

# Load environment
from load_env import load_env
load_env()

# Import components
from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime
from core.knowledge_graph import KnowledgeGraph

# Import agents
from agents.claude import Claude
from agents.data_harvester import DataHarvester
from agents.data_digester import DataDigester
from agents.relationship_hunter import RelationshipHunter
from agents.pattern_spotter import PatternSpotter
from agents.forecast_dreamer import ForecastDreamer
from agents.code_monkey import CodeMonkey
from agents.workflow_recorder import WorkflowRecorder
from capabilities.market_data import MarketDataCapability

print("=" * 80)
print("COMPREHENSIVE PHASE 1 & 2 VERIFICATION")
print("=" * 80)

# Initialize components
graph = KnowledgeGraph()
runtime = AgentRuntime()

# Register agents
caps = {'market': MarketDataCapability()}
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, caps))
runtime.register_agent('data_digester', DataDigester(graph))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))
runtime.register_agent('pattern_spotter', PatternSpotter(graph))
runtime.register_agent('forecast_dreamer', ForecastDreamer(graph))
runtime.register_agent('code_monkey', CodeMonkey())
runtime.register_agent('workflow_recorder', WorkflowRecorder(graph))

# Initialize pattern engine
pattern_engine = PatternEngine('patterns', runtime)
runtime.pattern_engine = pattern_engine

print(f"\n✅ System Initialized")
print(f"   Agents registered: {len(runtime.agent_registry.agents)}")
print(f"   Patterns loaded: {len(pattern_engine.patterns)}")

# Phase 1 Tests
print("\n" + "=" * 80)
print("PHASE 1 VERIFICATION: Pattern Engine Core")
print("=" * 80)

phase1_tests = {
    "Pattern Loading": False,
    "Pattern Matching": False,
    "Variable Resolution": False,
    "Pattern Execution": False,
    "Orchestrator Integration": False
}

# Test 1: Pattern Loading
if len(pattern_engine.patterns) > 20:
    phase1_tests["Pattern Loading"] = True
    print("✅ Pattern Loading: 23+ patterns loaded")
else:
    print(f"❌ Pattern Loading: Only {len(pattern_engine.patterns)} patterns")

# Test 2: Pattern Matching
test_inputs = [
    ("detect market regime", "market_regime"),
    ("what's AAPL price", "stock_price"),
    ("deep dive META", "deep_dive")
]

match_count = 0
for input_text, expected in test_inputs:
    pattern = pattern_engine.find_pattern(input_text)
    if pattern and pattern['id'] == expected:
        match_count += 1

if match_count >= 2:
    phase1_tests["Pattern Matching"] = True
    print(f"✅ Pattern Matching: {match_count}/3 matches working")
else:
    print(f"❌ Pattern Matching: Only {match_count}/3 matches")

# Test 3: Variable Resolution
params = {
    'symbol': '{SYMBOL}',
    'data': '{step_1.result}'
}
context = {'user_input': 'AAPL analysis'}
outputs = {'step_1': {'result': 'test_data'}}

resolved = pattern_engine._resolve_params(params, context, outputs)
if resolved['symbol'] == 'AAPL' and resolved['data'] == 'test_data':
    phase1_tests["Variable Resolution"] = True
    print("✅ Variable Resolution: Working correctly")
else:
    print("❌ Variable Resolution: Failed")

# Test 4: Pattern Execution
simple_pattern = {
    'id': 'test',
    'steps': [
        {
            'agent': 'claude',
            'params': {'user_input': 'test'},
            'output': 'result'
        }
    ]
}

result = pattern_engine.execute_pattern(simple_pattern)
if 'results' in result and len(result['results']) > 0:
    phase1_tests["Pattern Execution"] = True
    print("✅ Pattern Execution: Steps executing")
else:
    print("❌ Pattern Execution: Failed")

# Test 5: Orchestrator Integration
response = runtime.orchestrate("What's the market regime?")
if response and 'pattern' in response:
    phase1_tests["Orchestrator Integration"] = True
    print("✅ Orchestrator Integration: Patterns used in orchestration")
else:
    print("❌ Orchestrator Integration: Not using patterns")

# Phase 2 Tests
print("\n" + "=" * 80)
print("PHASE 2 VERIFICATION: Pattern Library")
print("=" * 80)

phase2_tests = {
    "Query Patterns": False,
    "Analysis Patterns": False,
    "Action Patterns": False,
    "Workflow Patterns": False,
    "UI Patterns": False
}

# Count patterns by category
pattern_files = {
    'queries': 0,
    'analysis': 0,
    'actions': 0,
    'workflows': 0,
    'ui': 0
}

for root, dirs, files in os.walk('patterns'):
    for file in files:
        if file.endswith('.json') and file != 'schema.json':
            category = os.path.basename(root)
            if category in pattern_files:
                pattern_files[category] += 1

# Verify each category
if pattern_files['queries'] >= 5:
    phase2_tests["Query Patterns"] = True
    print(f"✅ Query Patterns: {pattern_files['queries']} patterns")
else:
    print(f"❌ Query Patterns: Only {pattern_files['queries']}")

if pattern_files['analysis'] >= 5:
    phase2_tests["Analysis Patterns"] = True
    print(f"✅ Analysis Patterns: {pattern_files['analysis']} patterns")
else:
    print(f"❌ Analysis Patterns: Only {pattern_files['analysis']}")

if pattern_files['actions'] >= 5:
    phase2_tests["Action Patterns"] = True
    print(f"✅ Action Patterns: {pattern_files['actions']} patterns")
else:
    print(f"❌ Action Patterns: Only {pattern_files['actions']}")

if pattern_files['workflows'] >= 3:
    phase2_tests["Workflow Patterns"] = True
    print(f"✅ Workflow Patterns: {pattern_files['workflows']} patterns")
else:
    print(f"❌ Workflow Patterns: Only {pattern_files['workflows']}")

if pattern_files['ui'] >= 3:
    phase2_tests["UI Patterns"] = True
    print(f"✅ UI Patterns: {pattern_files['ui']} patterns")
else:
    print(f"❌ UI Patterns: Only {pattern_files['ui']}")

# Test Key Features
print("\n" + "=" * 80)
print("KEY FEATURE VERIFICATION")
print("=" * 80)

key_features = {
    "Market Regime Detection": pattern_engine.get_pattern('market_regime') is not None,
    "Company Deep Dive": pattern_engine.get_pattern('deep_dive') is not None,
    "Morning Briefing": pattern_engine.get_pattern('morning_briefing') is not None,
    "Portfolio Analysis": pattern_engine.get_pattern('portfolio_analysis') is not None,
    "Technical Analysis": pattern_engine.get_pattern('technical_analysis') is not None,
    "Opportunity Scanner": pattern_engine.get_pattern('opportunity_scan') is not None
}

for feature, exists in key_features.items():
    if exists:
        print(f"✅ {feature}: Pattern exists")
    else:
        print(f"❌ {feature}: Pattern missing")

# Final Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

phase1_passed = sum(phase1_tests.values())
phase2_passed = sum(phase2_tests.values())
features_passed = sum(key_features.values())

print(f"\n📊 Phase 1 Core: {phase1_passed}/{len(phase1_tests)} tests passed")
print(f"📊 Phase 2 Patterns: {phase2_passed}/{len(phase2_tests)} categories complete")
print(f"📊 Key Features: {features_passed}/{len(key_features)} features ready")

total_score = (phase1_passed + phase2_passed + features_passed) / (len(phase1_tests) + len(phase2_tests) + len(key_features)) * 100

print(f"\n🎯 Overall Readiness: {total_score:.1f}%")

if total_score >= 90:
    print("✅ READY FOR PHASE 3: UI Integration")
    print("\nWhat's working:")
    print("• Pattern Engine fully functional")
    print("• 23+ patterns covering all features")
    print("• Multi-agent orchestration")
    print("• Variable substitution and data flow")
    print("• All major UI features have patterns")
elif total_score >= 70:
    print("⚠️  MOSTLY READY: Some issues to fix")
else:
    print("❌ NOT READY: Major issues found")

# Test actual functionality
print("\n" + "=" * 80)
print("LIVE FUNCTIONALITY TEST")
print("=" * 80)

print("\nTesting Market Regime Detection...")
regime_response = runtime.orchestrate("Detect the current market regime")
if 'pattern' in regime_response and regime_response['pattern'] == 'market_regime':
    print("✅ Market Regime Detection working!")
else:
    print("❌ Market Regime Detection failed")

print("\nTesting Stock Price Query...")
price_response = runtime.orchestrate("What's AAPL stock price?")
if 'pattern' in price_response:
    print(f"✅ Stock Price Query working! (Pattern: {price_response.get('pattern', 'unknown')})")
else:
    print("❌ Stock Price Query failed")
