#!/usr/bin/env python3
"""Test script to verify governance fixes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.knowledge_graph import KnowledgeGraph
from agents.governance_agent import GovernanceAgent
from core.graph_governance import GraphGovernance

def test_governance_initialization():
    """Test that governance initializes correctly after fixes"""
    print("Testing governance initialization...")

    # Create knowledge graph
    graph = KnowledgeGraph()
    print("✅ KnowledgeGraph created")

    # Add some test nodes
    graph.add_node('stock', {'symbol': 'AAPL', 'name': 'Apple Inc.'}, node_id='AAPL_stock')
    graph.add_node('stock', {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'}, node_id='GOOGL_stock')
    print("✅ Test nodes added")

    # Test 1: GovernanceAgent initialization
    try:
        governance_agent = GovernanceAgent(graph=graph)
        assert governance_agent.graph is graph, "Graph not properly assigned"
        assert governance_agent.name == "GovernanceAgent", "Name not properly assigned"
        print("✅ GovernanceAgent initialized correctly")
    except Exception as e:
        print(f"❌ GovernanceAgent initialization failed: {e}")
        return False

    # Test 2: GraphGovernance initialization
    try:
        graph_governance = GraphGovernance(graph)
        assert graph_governance.graph is graph, "Graph not properly assigned"
        assert hasattr(graph_governance, 'governance_types'), "governance_types not defined"
        print("✅ GraphGovernance initialized correctly")
    except Exception as e:
        print(f"❌ GraphGovernance initialization failed: {e}")
        return False

    # Test 3: Governance operations
    try:
        # Add a governance policy
        policy_id = graph_governance.add_governance_policy(
            "Test Policy",
            "All stock data must be updated daily",
            ['AAPL_stock', 'GOOGL_stock']
        )
        print(f"✅ Governance policy created: {policy_id}")

        # Check governance
        gov_check = graph_governance.check_governance('AAPL_stock')
        assert 'quality_score' in gov_check, "quality_score not in governance check"
        assert 'policies' in gov_check, "policies not in governance check"
        print(f"✅ Governance check successful: quality_score={gov_check['quality_score']}")

        # Trace lineage
        lineage = graph_governance.trace_data_lineage('AAPL_stock')
        print(f"✅ Lineage trace successful: {len(lineage)} paths found")

    except Exception as e:
        print(f"❌ Governance operations failed: {e}")
        return False

    # Test 4: Agent governance request
    try:
        result = governance_agent.process_request(
            "Check data quality for AAPL",
            {'source': 'test'}
        )
        assert 'status' in result, "No status in governance result"
        print(f"✅ Governance agent request successful: status={result['status']}")
    except Exception as e:
        print(f"❌ Governance agent request failed: {e}")
        return False

    print("\n✅ All governance tests passed!")
    return True

if __name__ == "__main__":
    success = test_governance_initialization()
    sys.exit(0 if success else 1)