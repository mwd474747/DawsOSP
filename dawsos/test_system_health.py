#!/usr/bin/env python3
"""
Comprehensive system health check for DawsOS
Tests all major components and integrations
"""

import json
import sys
from datetime import datetime

def test_imports():
    """Test all critical imports"""
    print("=== Testing Imports ===")
    errors = []

    try:
        print("✅ KnowledgeGraph imported")
    except Exception as e:
        errors.append(f"❌ KnowledgeGraph import failed: {e}")

    try:
        print("✅ PatternEngine imported")
    except Exception as e:
        errors.append(f"❌ PatternEngine import failed: {e}")

    try:
        print("✅ AgentRuntime imported")
    except Exception as e:
        errors.append(f"❌ AgentRuntime import failed: {e}")

    try:
        print("✅ GraphGovernance imported")
    except Exception as e:
        errors.append(f"❌ GraphGovernance import failed: {e}")

    try:
        print("✅ GovernanceHooks imported")
    except Exception as e:
        errors.append(f"❌ GovernanceHooks import failed: {e}")

    try:
        print("✅ GovernanceAgent imported")
    except Exception as e:
        errors.append(f"❌ GovernanceAgent import failed: {e}")

    return errors

def test_governance_policies():
    """Test governance policies loading"""
    print("\n=== Testing Governance Policies ===")
    errors = []

    try:
        with open('knowledge/governance_policies.json', 'r') as f:
            policies = json.load(f)
        print(f"✅ Loaded {len(policies.get('governance_policies', {}))} policy categories")
    except Exception as e:
        errors.append(f"❌ Governance policies loading failed: {e}")

    return errors

def test_pattern_loading():
    """Test pattern loading"""
    print("\n=== Testing Pattern Loading ===")
    errors = []

    try:
        from core.pattern_engine import PatternEngine
        from core.knowledge_graph import KnowledgeGraph

        graph = KnowledgeGraph()
        pattern_engine = PatternEngine(graph)
        patterns = pattern_engine.patterns
        print(f"✅ Loaded {len(patterns)} patterns")

        # Check governance patterns
        governance_patterns = [p for p in patterns if 'governance' in patterns[p].get('category', '')]
        print(f"✅ Found {len(governance_patterns)} governance patterns")

    except Exception as e:
        errors.append(f"❌ Pattern loading failed: {e}")

    return errors

def test_agent_initialization():
    """Test agent initialization with proper parameters"""
    print("\n=== Testing Agent Initialization ===")
    errors = []

    try:
        from core.knowledge_graph import KnowledgeGraph
        from core.agent_runtime import AgentRuntime

        graph = KnowledgeGraph()
        runtime = AgentRuntime()
        runtime.graph = graph  # Set graph after initialization

        print(f"✅ Initialized {len(runtime.agent_registry.agents)} agents")

        # Test governance agent specifically
        gov_adapter = runtime.agent_registry.get_agent('governance')
        if gov_adapter:
            gov_agent = gov_adapter.agent
            if hasattr(gov_agent, 'graph_governance'):
                print("✅ GovernanceAgent has graph_governance")
            if hasattr(gov_agent, 'governance_hooks'):
                print("✅ GovernanceAgent has governance_hooks")
        else:
            errors.append("❌ GovernanceAgent not found in runtime")

    except Exception as e:
        errors.append(f"❌ Agent initialization failed: {e}")

    return errors

def test_governance_integration():
    """Test governance integration"""
    print("\n=== Testing Governance Integration ===")
    errors = []

    try:
        from core.knowledge_graph import KnowledgeGraph
        from core.graph_governance import GraphGovernance
        from agents.governance_agent import GovernanceAgent

        graph = KnowledgeGraph()

        # Add test node
        node_id = graph.add_node('test', {'value': 100, 'timestamp': datetime.now().isoformat()})

        # Test graph governance
        graph_gov = GraphGovernance(graph)
        gov_check = graph_gov.check_governance(node_id)

        if 'quality_score' in gov_check:
            print(f"✅ Governance check returned quality score: {gov_check['quality_score']}")
        else:
            errors.append("❌ Governance check missing quality score")

        # Test governance agent
        gov_agent = GovernanceAgent(graph=graph)
        if gov_agent.graph_governance:
            print("✅ GovernanceAgent properly initialized with graph_governance")

            # Test validate_with_pattern
            result = gov_agent.validate_with_pattern("test validation", {'target_nodes': [node_id]})
            if result['status'] == 'success':
                print("✅ Pattern validation successful")
            else:
                errors.append(f"❌ Pattern validation failed: {result}")
        else:
            errors.append("❌ GovernanceAgent missing graph_governance")

    except Exception as e:
        errors.append(f"❌ Governance integration failed: {e}")

    return errors

def main():
    """Run all tests"""
    print("🏥 DawsOS System Health Check")
    print("=" * 40)

    all_errors = []

    # Run all tests
    all_errors.extend(test_imports())
    all_errors.extend(test_governance_policies())
    all_errors.extend(test_pattern_loading())
    all_errors.extend(test_agent_initialization())
    all_errors.extend(test_governance_integration())

    # Summary
    print("\n" + "=" * 40)
    print("📊 SUMMARY")
    print("=" * 40)

    if all_errors:
        print(f"❌ Found {len(all_errors)} errors:")
        for error in all_errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ All systems operational!")
        print("🎉 DawsOS is healthy and ready to use")
        sys.exit(0)

if __name__ == "__main__":
    main()
