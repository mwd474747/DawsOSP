#!/usr/bin/env python3
"""
Trinity Architecture Smoke Tests
Quick tests to verify the executor can initialize and route sample requests
"""

import unittest
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.knowledge_graph import KnowledgeGraph
from core.agent_adapter import AgentRegistry
from core.universal_executor import UniversalExecutor, get_executor
from core.pattern_engine import PatternEngine


class TestTrinitySmoke(unittest.TestCase):
    """Quick smoke tests for Trinity Architecture"""

    def setUp(self):
        """Create fresh components for each test"""
        # Reset singleton
        import core.universal_executor as ue_module
        ue_module._executor_instance = None

        self.graph = KnowledgeGraph()
        self.registry = AgentRegistry()

    def test_executor_can_initialize(self):
        """SMOKE: Executor initializes without errors"""
        try:
            executor = UniversalExecutor(self.graph, self.registry)
            self.assertIsNotNone(executor)
        except Exception as e:
            self.fail(f"Executor initialization failed: {e}")

    def test_executor_accepts_simple_request(self):
        """SMOKE: Executor can process a simple request"""
        executor = UniversalExecutor(self.graph, self.registry)

        request = {
            'action': 'test',
            'data': 'hello world'
        }

        try:
            result = executor.execute(request)
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)
            # With no meta pattern available the executor should fall back gracefully
            self.assertTrue(result.get('fallback_mode', False))
        except Exception as e:
            self.fail(f"Executor failed to process request: {e}")

    def test_executor_handles_missing_meta_pattern_gracefully(self):
        """SMOKE: Executor falls back when meta pattern unavailable"""
        executor = UniversalExecutor(self.graph, self.registry)

        result = executor.execute({'action': 'test'})

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('fallback_mode'))

    def test_pattern_engine_has_guards(self):
        """SMOKE: Pattern engine has safety guards"""
        pattern_engine = PatternEngine()

        # Should not crash on missing pattern
        has_pattern = pattern_engine.has_pattern('nonexistent')
        self.assertFalse(has_pattern)

        get_pattern = pattern_engine.get_pattern('nonexistent')
        self.assertIsNone(get_pattern)

    def test_knowledge_graph_has_api(self):
        """SMOKE: KnowledgeGraph has expected API methods"""
        graph = KnowledgeGraph()

        # Check all new methods exist
        self.assertTrue(hasattr(graph, 'get_node'))
        self.assertTrue(hasattr(graph, 'get_nodes_by_type'))
        self.assertTrue(hasattr(graph, 'has_edge'))
        self.assertTrue(hasattr(graph, 'get_edge'))
        self.assertTrue(hasattr(graph, 'safe_query'))
        self.assertTrue(hasattr(graph, 'get_node_data'))
        self.assertTrue(hasattr(graph, 'get_connected_nodes'))

    def test_singleton_pattern_works(self):
        """SMOKE: Executor singleton pattern works"""
        executor1 = get_executor(self.graph, self.registry)
        executor2 = get_executor()

        self.assertIs(executor1, executor2)

    def test_fallback_execution_exists(self):
        """SMOKE: Fallback execution is implemented"""
        executor = UniversalExecutor(self.graph, self.registry)

        self.assertTrue(hasattr(executor, '_execute_fallback'))
        self.assertTrue(callable(executor._execute_fallback))

    def test_metrics_tracking_works(self):
        """SMOKE: Metrics are tracked correctly"""
        executor = UniversalExecutor(self.graph, self.registry)

        metrics_before = executor.get_metrics()
        self.assertEqual(metrics_before['total_executions'], 0)

        executor.execute({'action': 'test'})

        metrics_after = executor.get_metrics()
        self.assertEqual(metrics_after['total_executions'], 1)

    def test_context_preparation(self):
        """SMOKE: Context preparation injects Trinity components"""
        executor = UniversalExecutor(self.graph, self.registry)

        request = {'action': 'test'}
        context = executor._prepare_context(request)

        # Check Trinity components are injected
        self.assertIn('graph', context)
        self.assertIn('registry', context)
        self.assertIn('pattern_engine', context)
        self.assertIn('execution_id', context)

    def test_error_recovery_is_safe(self):
        """SMOKE: Error recovery doesn't crash system"""
        executor = UniversalExecutor(self.graph, self.registry)

        # Force error with None request
        result = executor.execute(None)

        # Should return error response, not crash
        self.assertIsNotNone(result)
        self.assertIn('error', result)


class TestAgentRegistry(unittest.TestCase):
    """Smoke tests for AgentRegistry"""

    def test_registry_initializes(self):
        """SMOKE: Registry initializes without errors"""
        try:
            registry = AgentRegistry()
            self.assertIsNotNone(registry)
        except Exception as e:
            self.fail(f"Registry initialization failed: {e}")

    def test_registry_has_compliance_tracking(self):
        """SMOKE: Registry tracks Trinity compliance"""
        registry = AgentRegistry()

        self.assertTrue(hasattr(registry, 'get_compliance_metrics'))
        metrics = registry.get_compliance_metrics()

        self.assertIn('overall_compliance', metrics)
        self.assertIn('total_executions', metrics)


class TestKnowledgeGraphAPI(unittest.TestCase):
    """Smoke tests for KnowledgeGraph API"""

    def test_get_node_is_safe(self):
        """SMOKE: get_node handles missing nodes safely"""
        graph = KnowledgeGraph()

        result = graph.get_node('nonexistent')
        self.assertIsNone(result)

    def test_has_edge_is_safe(self):
        """SMOKE: has_edge handles missing edges safely"""
        graph = KnowledgeGraph()

        result = graph.has_edge('node1', 'node2')
        self.assertFalse(result)

    def test_safe_query_doesnt_crash(self):
        """SMOKE: safe_query handles errors gracefully"""
        graph = KnowledgeGraph()

        # Should not crash with invalid pattern
        result = graph.safe_query(None, default=[])
        self.assertEqual(result, [])


if __name__ == '__main__':
    print("=" * 70)
    print("TRINITY ARCHITECTURE SMOKE TESTS")
    print("Quick validation that core systems can initialize and route requests")
    print("=" * 70)
    print()

    # Run tests with verbose output
    unittest.main(verbosity=2)
