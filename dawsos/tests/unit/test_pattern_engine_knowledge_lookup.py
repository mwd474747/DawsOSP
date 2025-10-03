#!/usr/bin/env python3
"""
Test PatternEngine knowledge_lookup functionality
Ensures get_node and get_nodes_by_type work correctly in knowledge_lookup action
"""

import unittest
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.knowledge_graph import KnowledgeGraph
from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime
from agents.base_agent import BaseAgent


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    def __init__(self, graph):
        super().__init__(graph, "MockAgent", None)


class TestPatternEngineKnowledgeLookup(unittest.TestCase):
    """Test knowledge_lookup action in PatternEngine"""

    def setUp(self):
        """Create fresh components for each test"""
        self.graph = KnowledgeGraph()
        self.runtime = AgentRuntime()
        self.pattern_engine = PatternEngine(runtime=self.runtime)

        # Create agent with graph access
        self.agent = MockAgent(self.graph)
        self.runtime.register_agent('mock_agent', self.agent)

    def test_knowledge_lookup_with_get_nodes_by_type(self):
        """Test knowledge_lookup uses get_nodes_by_type correctly"""
        # Add test nodes to graph
        self.graph.add_node('stock', {'symbol': 'AAPL', 'price': 150}, 'AAPL')
        self.graph.add_node('stock', {'symbol': 'GOOGL', 'price': 2800}, 'GOOGL')

        # Execute knowledge_lookup action
        result = self.pattern_engine.execute_action(
            action='knowledge_lookup',
            params={'section': 'stock'},
            context={},
            outputs={}
        )

        # Should find stocks and return them
        self.assertTrue(result.get('found'))
        self.assertEqual(result.get('count'), 2)
        self.assertIn('data', result)
        self.assertIsInstance(result['data'], dict)

    def test_knowledge_lookup_with_get_node(self):
        """Test knowledge_lookup uses get_node correctly"""
        # Add test node with specific ID
        node_id = self.graph.add_node('stock', {'symbol': 'AAPL', 'price': 150}, 'AAPL')

        # Execute knowledge_lookup for specific node ID
        result = self.pattern_engine.execute_action(
            action='knowledge_lookup',
            params={'section': 'AAPL'},  # Matches node ID
            context={},
            outputs={}
        )

        # Should find the specific node
        self.assertTrue(result.get('found'))
        self.assertEqual(result.get('count'), 1)

    def test_knowledge_lookup_empty_result(self):
        """Test knowledge_lookup handles missing data gracefully"""
        # Don't add any nodes

        result = self.pattern_engine.execute_action(
            action='knowledge_lookup',
            params={'section': 'nonexistent'},
            context={},
            outputs={}
        )

        # Should return not found
        self.assertFalse(result.get('found'))

    def test_get_nodes_by_type_returns_dict(self):
        """Test get_nodes_by_type returns dict, not list"""
        # Add test nodes
        self.graph.add_node(node_type='stock', data={'symbol': 'AAPL'})
        self.graph.add_node(node_type='stock', data={'symbol': 'GOOGL'})

        # Get nodes by type
        nodes = self.graph.get_nodes_by_type('stock')

        # Must be dict (not list) so .items() works
        self.assertIsInstance(nodes, dict)

        # Should be able to iterate with .items()
        for node_id, node_data in nodes.items():
            self.assertIsInstance(node_id, str)
            self.assertIsInstance(node_data, dict)
            self.assertEqual(node_data.get('type'), 'stock')

    def test_get_node_works_correctly(self):
        """Test get_node returns node or None"""
        # Add test node
        node_id = self.graph.add_node(node_type='stock', data={'symbol': 'AAPL'})

        # Get node should return the node
        node = self.graph.get_node(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.get('type'), 'stock')
        self.assertEqual(node.get('data', {}).get('symbol'), 'AAPL')

        # Get non-existent node should return None
        missing = self.graph.get_node('nonexistent')
        self.assertIsNone(missing)


class TestPatternEngineIntegration(unittest.TestCase):
    """Integration tests for pattern engine with real patterns"""

    def setUp(self):
        """Create components"""
        self.graph = KnowledgeGraph()
        self.runtime = AgentRuntime()
        self.pattern_engine = PatternEngine(runtime=self.runtime)

        # Register agent with graph
        agent = MockAgent(self.graph)
        self.runtime.register_agent('mock_agent', agent)

    def test_pattern_engine_can_access_graph_methods(self):
        """Test pattern engine can call both graph methods"""
        # Add test data
        self.graph.add_node('indicator', {'name': 'GDP', 'value': 30000}, 'GDP')
        self.graph.add_node('indicator', {'name': 'CPI', 'value': 3.5}, 'CPI')

        # Pattern engine should be able to lookup by type
        result1 = self.pattern_engine.execute_action(
            action='knowledge_lookup',
            params={'section': 'indicator'},
            context={},
            outputs={}
        )
        self.assertTrue(result1.get('found'))
        self.assertEqual(result1.get('count'), 2)

        # Pattern engine should be able to lookup by ID
        result2 = self.pattern_engine.execute_action(
            action='knowledge_lookup',
            params={'section': 'GDP'},
            context={},
            outputs={}
        )
        self.assertTrue(result2.get('found'))
        self.assertEqual(result2.get('count'), 1)


if __name__ == '__main__':
    print("=" * 70)
    print("PATTERN ENGINE KNOWLEDGE LOOKUP TESTS")
    print("Validates that get_node and get_nodes_by_type work in knowledge_lookup")
    print("=" * 70)
    print()

    # Run tests with verbose output
    unittest.main(verbosity=2)
