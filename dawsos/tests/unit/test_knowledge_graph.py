#!/usr/bin/env python3
"""
Unit tests for KnowledgeGraph API methods
Tests all core methods including new safe query helpers
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.knowledge_graph import KnowledgeGraph


class TestKnowledgeGraphAPI(unittest.TestCase):
    """Test KnowledgeGraph API methods"""

    def setUp(self):
        """Create fresh graph for each test"""
        self.graph = KnowledgeGraph()

        # Add test nodes
        self.node1 = self.graph.add_node('stock', {'symbol': 'AAPL', 'price': 150})
        self.node2 = self.graph.add_node('stock', {'symbol': 'GOOGL', 'price': 2800})
        self.node3 = self.graph.add_node('sector', {'name': 'Technology'})

        # Add test edges
        self.graph.connect(self.node1, self.node3, 'belongs_to', strength=0.9)
        self.graph.connect(self.node2, self.node3, 'belongs_to', strength=0.95)
        self.graph.connect(self.node1, self.node2, 'correlates', strength=0.7)

    def test_get_node_exists(self):
        """Test get_node returns node when it exists"""
        node = self.graph.get_node(self.node1)
        self.assertIsNotNone(node)
        self.assertEqual(node['type'], 'stock')
        self.assertEqual(node['data']['symbol'], 'AAPL')

    def test_get_node_not_exists(self):
        """Test get_node returns None when node doesn't exist"""
        node = self.graph.get_node('nonexistent_id')
        self.assertIsNone(node)

    def test_get_nodes_by_type(self):
        """Test get_nodes_by_type returns all matching nodes as dict"""
        stock_nodes = self.graph.get_nodes_by_type('stock')
        self.assertIsInstance(stock_nodes, dict)
        self.assertEqual(len(stock_nodes), 2)

        sector_nodes = self.graph.get_nodes_by_type('sector')
        self.assertIsInstance(sector_nodes, dict)
        self.assertEqual(len(sector_nodes), 1)

        nonexistent_nodes = self.graph.get_nodes_by_type('nonexistent')
        self.assertIsInstance(nonexistent_nodes, dict)
        self.assertEqual(len(nonexistent_nodes), 0)

    def test_has_edge_exists(self):
        """Test has_edge returns True when edge exists"""
        self.assertTrue(self.graph.has_edge(self.node1, self.node3))
        self.assertTrue(self.graph.has_edge(self.node1, self.node3, 'belongs_to'))

    def test_has_edge_not_exists(self):
        """Test has_edge returns False when edge doesn't exist"""
        self.assertFalse(self.graph.has_edge(self.node3, self.node1))  # Wrong direction
        self.assertFalse(self.graph.has_edge(self.node1, self.node3, 'wrong_type'))
        self.assertFalse(self.graph.has_edge('fake_id', self.node1))

    def test_get_edge_exists(self):
        """Test get_edge returns edge data when it exists"""
        edge = self.graph.get_edge(self.node1, self.node2)
        self.assertIsNotNone(edge)
        self.assertEqual(edge['type'], 'correlates')
        self.assertEqual(edge['strength'], 0.7)

    def test_get_edge_not_exists(self):
        """Test get_edge returns None when edge doesn't exist"""
        edge = self.graph.get_edge(self.node3, self.node1)
        self.assertIsNone(edge)

    def test_get_edge_with_relationship_filter(self):
        """Test get_edge filters by relationship type"""
        edge = self.graph.get_edge(self.node1, self.node3, 'belongs_to')
        self.assertIsNotNone(edge)

        edge = self.graph.get_edge(self.node1, self.node3, 'wrong_type')
        self.assertIsNone(edge)

    def test_safe_query_success(self):
        """Test safe_query returns results when query succeeds"""
        results = self.graph.safe_query({'type': 'stock'})
        self.assertEqual(len(results), 2)

    def test_safe_query_empty_with_default(self):
        """Test safe_query returns default when no matches"""
        results = self.graph.safe_query({'type': 'nonexistent'}, default=['default'])
        self.assertEqual(results, ['default'])

    def test_safe_query_empty_without_default(self):
        """Test safe_query returns empty list when no matches and no default"""
        results = self.graph.safe_query({'type': 'nonexistent'})
        self.assertEqual(results, [])

    def test_get_node_data_exists(self):
        """Test get_node_data returns data when key exists"""
        symbol = self.graph.get_node_data(self.node1, 'symbol')
        self.assertEqual(symbol, 'AAPL')

    def test_get_node_data_not_exists(self):
        """Test get_node_data returns default when key doesn't exist"""
        value = self.graph.get_node_data(self.node1, 'nonexistent_key', default='N/A')
        self.assertEqual(value, 'N/A')

    def test_get_node_data_node_not_exists(self):
        """Test get_node_data returns default when node doesn't exist"""
        value = self.graph.get_node_data('fake_id', 'symbol', default='N/A')
        self.assertEqual(value, 'N/A')

    def test_get_connected_nodes_outgoing(self):
        """Test get_connected_nodes returns outgoing connections"""
        connected = self.graph.get_connected_nodes(self.node1, direction='out')
        self.assertEqual(len(connected), 2)  # node3 and node2
        self.assertIn(self.node3, connected)
        self.assertIn(self.node2, connected)

    def test_get_connected_nodes_incoming(self):
        """Test get_connected_nodes returns incoming connections"""
        connected = self.graph.get_connected_nodes(self.node3, direction='in')
        self.assertEqual(len(connected), 2)  # node1 and node2
        self.assertIn(self.node1, connected)
        self.assertIn(self.node2, connected)

    def test_get_connected_nodes_both(self):
        """Test get_connected_nodes returns all connections"""
        connected = self.graph.get_connected_nodes(self.node1, direction='both')
        self.assertEqual(len(connected), 2)  # node3 (out) and node2 (out)

    def test_get_connected_nodes_with_relationship_filter(self):
        """Test get_connected_nodes filters by relationship"""
        connected = self.graph.get_connected_nodes(
            self.node1, direction='out', relationship='belongs_to'
        )
        self.assertEqual(len(connected), 1)
        self.assertEqual(connected[0], self.node3)

    def test_api_methods_chain(self):
        """Test chaining multiple API methods"""
        # Find all stock nodes
        stock_nodes = self.graph.get_nodes_by_type('stock')

        # Get first stock's data (dict now, not list of tuples)
        first_stock_id = list(stock_nodes.keys())[0]
        symbol = self.graph.get_node_data(first_stock_id, 'symbol')
        self.assertIn(symbol, ['AAPL', 'GOOGL'])

        # Find what it connects to
        connected = self.graph.get_connected_nodes(first_stock_id, direction='out')
        self.assertGreater(len(connected), 0)

        # Check if specific edge exists
        self.assertTrue(self.graph.has_edge(first_stock_id, connected[0]))


class TestKnowledgeGraphEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        """Create fresh graph for each test"""
        self.graph = KnowledgeGraph()

    def test_empty_graph_queries(self):
        """Test queries on empty graph"""
        self.assertIsNone(self.graph.get_node('any_id'))
        self.assertEqual(self.graph.get_nodes_by_type('any_type'), {})
        self.assertFalse(self.graph.has_edge('id1', 'id2'))
        self.assertIsNone(self.graph.get_edge('id1', 'id2'))
        self.assertEqual(self.graph.get_connected_nodes('any_id'), [])

    def test_safe_query_invalid_pattern(self):
        """Test safe_query handles invalid patterns gracefully"""
        # This should not crash even with malformed pattern
        results = self.graph.safe_query(None, default=[])
        self.assertEqual(results, [])

    def test_get_node_data_none_handling(self):
        """Test get_node_data handles None values properly"""
        node_id = self.graph.add_node('test', {'value': None})
        value = self.graph.get_node_data(node_id, 'value', default='default')
        self.assertIsNone(value)  # Should return actual None, not default

    def test_relationship_case_sensitivity(self):
        """Test relationship matching is case-sensitive"""
        node1 = self.graph.add_node('test', {})
        node2 = self.graph.add_node('test', {})
        self.graph.connect(node1, node2, 'TestRelation')

        self.assertTrue(self.graph.has_edge(node1, node2, 'TestRelation'))
        self.assertFalse(self.graph.has_edge(node1, node2, 'testrelation'))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
