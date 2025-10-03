#!/usr/bin/env python3
"""Test script for agent compliance system"""

import sys
sys.path.append('/Users/mdawson/Dawson/DawsOSB/dawsos')

from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.agent_validator import AgentValidator
from agents.data_harvester import DataHarvester
from agents.claude import Claude
from agents.pattern_spotter import PatternSpotter
from agents.governance_agent import GovernanceAgent
from capabilities.market_data import MarketDataCapability

def test_compliance_system():
    """Test the complete agent compliance system"""
    print("=== Testing Agent Compliance System ===\n")

    # Initialize knowledge graph
    graph = KnowledgeGraph()

    # Initialize runtime
    runtime = AgentRuntime()

    # Register a few agents
    runtime.register_agent('claude', Claude(graph))
    runtime.register_agent('data_harvester', DataHarvester(graph, {'market': MarketDataCapability()}))
    runtime.register_agent('pattern_spotter', PatternSpotter(graph))
    runtime.register_agent('governance_agent', GovernanceAgent(graph))

    print(f"Registered {len(runtime.agent_registry.agents)} agents\n")

    # Test 1: Execute agents to generate runtime metrics
    print("Test 1: Executing agents to generate runtime metrics...")

    # Execute Claude
    result1 = runtime.execute('claude', {'user_input': 'What is the weather?'})
    print(f"Claude execution: {'✓' if 'error' not in result1 else '✗'}")

    # Execute Data Harvester
    result2 = runtime.execute('data_harvester', {'request': 'Get AAPL data'})
    print(f"DataHarvester execution: {'✓' if 'error' not in result2 else '✗'}")

    # Execute Pattern Spotter
    result3 = runtime.execute('pattern_spotter', {'context': {}})
    print(f"PatternSpotter execution: {'✓' if 'error' not in result3 else '✗'}")

    print()

    # Test 2: Get runtime compliance metrics
    print("Test 2: Getting runtime compliance metrics...")
    metrics = runtime.get_compliance_metrics()

    print(f"Overall compliance: {metrics.get('overall_compliance', 0):.0f}%")
    print(f"Total executions: {metrics.get('total_executions', 0)}")
    print(f"Total stored in graph: {metrics.get('total_stored', 0)}")
    print()

    # Test 3: Validate all agents
    print("Test 3: Validating all agents...")
    validator = AgentValidator(graph)
    validation_results = validator.validate_all_agents(runtime)

    print(f"Total agents validated: {validation_results['total_agents']}")
    print(f"Compliant: {validation_results['compliant']}")
    print(f"Warnings: {validation_results['warnings']}")
    print(f"Non-compliant: {validation_results['non_compliant']}")
    print(f"Overall compliance: {validation_results['overall_compliance']:.0%}")
    print()

    # Test 4: Generate compliance report
    print("Test 4: Generating compliance report...")
    report = validator.generate_compliance_report(validation_results)
    print(report[:500] + "..." if len(report) > 500 else report)
    print()

    # Test 5: Check if runtime metrics are included
    print("Test 5: Checking runtime metrics integration...")
    has_runtime_metrics = validation_results.get('runtime_metrics') is not None
    print(f"Runtime metrics included: {'✓' if has_runtime_metrics else '✗'}")

    if has_runtime_metrics:
        rm = validation_results['runtime_metrics']
        print(f"  - Agents with metrics: {len(rm.get('agents', {}))}")
        print(f"  - Overall runtime compliance: {rm.get('overall_compliance', 0):.0f}%")

    print("\n=== Test Complete ===")

    # Return success/failure
    return validation_results['overall_compliance'] > 0

if __name__ == "__main__":
    try:
        success = test_compliance_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
