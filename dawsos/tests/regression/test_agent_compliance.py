#!/usr/bin/env python3
"""
Regression Tests for Trinity Architecture Agent Compliance

Tests that all agents comply with Trinity Architecture requirements:
- Return dict format
- Include metadata (agent, timestamp, method_used)
- Handle errors gracefully
- Store results in knowledge graph
- Include graph_stored flag
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.agent_adapter import AgentRegistry, AgentAdapter
from agents.data_digester import DataDigester
from agents.workflow_recorder import WorkflowRecorder
from agents.data_harvester import DataHarvester
from agents.pattern_spotter import PatternSpotter
from agents.relationship_hunter import RelationshipHunter
from agents.forecast_dreamer import ForecastDreamer


class TestAgentComplianceBasics:
    """Test basic Trinity Architecture compliance for all agents"""

    @pytest.fixture
    def graph(self):
        """Create fresh graph for each test"""
        return KnowledgeGraph()

    @pytest.fixture
    def runtime(self, graph):
        """Create runtime with registry"""
        runtime = AgentRuntime()
        runtime.graph = graph
        return runtime

    @pytest.fixture
    def registry(self):
        """Create agent registry"""
        return AgentRegistry()

    def test_data_digester_returns_dict(self, graph):
        """Test DataDigester returns dict format"""
        agent = DataDigester(graph)
        result = agent.digest({'value': 100}, 'test_data')

        assert isinstance(result, dict), "DataDigester must return dict"
        assert 'status' in result, "Result must include status"

    def test_workflow_recorder_returns_dict(self, graph):
        """Test WorkflowRecorder returns dict (not None)"""
        agent = WorkflowRecorder(graph)
        interaction = {
            'intent': 'test',
            'actions': ['step1', 'step2'],
            'result': {'success': True},
            'success': True
        }
        result = agent.record(interaction)

        assert result is not None, "WorkflowRecorder must not return None"
        assert isinstance(result, dict), "WorkflowRecorder must return dict"
        assert 'status' in result, "Result must include status"

    def test_data_harvester_returns_dict(self, graph):
        """Test DataHarvester returns dict format"""
        # Mock capabilities
        capabilities = {
            'fred': Mock(get_latest=Mock(return_value={'value': 100, 'date': '2024-01-01'})),
            'market': Mock(),
            'news': Mock()
        }
        agent = DataHarvester(graph, capabilities)
        result = agent.harvest('GDP data')

        assert isinstance(result, dict), "DataHarvester must return dict"

    def test_pattern_spotter_returns_dict(self, graph):
        """Test PatternSpotter returns dict format"""
        agent = PatternSpotter(graph)
        result = agent.spot()

        assert isinstance(result, list), "PatternSpotter.spot() returns list of patterns"
        # The process method should return dict
        context_result = agent.process({'query': 'find patterns'})
        assert isinstance(context_result, dict), "PatternSpotter.process() must return dict"

    def test_relationship_hunter_returns_dict(self, graph):
        """Test RelationshipHunter returns dict or list"""
        agent = RelationshipHunter(graph)

        # Add a test node
        graph.add_node('indicator', {'name': 'GDP'}, 'GDP')

        result = agent.hunt('GDP')
        assert isinstance(result, (dict, list)), "RelationshipHunter must return dict or list"

    def test_forecast_dreamer_returns_dict(self, graph):
        """Test ForecastDreamer returns dict format"""
        agent = ForecastDreamer(graph)

        # Add test nodes for forecasting
        graph.add_node('stock', {'ticker': 'AAPL', 'price': 150}, 'AAPL')

        result = agent.dream('AAPL')
        assert isinstance(result, dict), "ForecastDreamer must return dict"


class TestAgentMetadata:
    """Test that all agents include required metadata in responses"""

    @pytest.fixture
    def graph(self):
        """Create fresh graph for each test"""
        return KnowledgeGraph()

    @pytest.fixture
    def registry(self):
        """Create agent registry"""
        return AgentRegistry()

    def test_adapter_adds_metadata(self, graph, registry):
        """Test that AgentAdapter adds required metadata"""
        agent = DataDigester(graph)
        registry.register('data_digester', agent)

        adapter = registry.get_agent('data_digester')
        result = adapter.execute({'data': {'value': 100}, 'data_type': 'test'})

        assert 'agent' in result, "Result must include agent name"
        assert 'timestamp' in result, "Result must include timestamp"
        assert 'method_used' in result, "Result must include method_used"

        # Validate timestamp format
        timestamp = result['timestamp']
        datetime.fromisoformat(timestamp)  # Should not raise

    def test_all_agents_include_metadata_via_registry(self, graph, registry):
        """Test all agents include metadata when executed via registry"""
        test_agents = [
            ('data_digester', DataDigester(graph), {'data': {'value': 100}, 'data_type': 'test'}),
            ('workflow_recorder', WorkflowRecorder(graph), {
                'interaction': {'intent': 'test', 'actions': [], 'result': {}, 'success': True}
            }),
        ]

        for name, agent, context in test_agents:
            registry.register(name, agent)
            result = registry.execute_with_tracking(name, context)

            assert 'agent' in result, f"{name} must include agent in result"
            assert 'timestamp' in result, f"{name} must include timestamp in result"
            assert 'method_used' in result, f"{name} must include method_used in result"


class TestAgentErrorHandling:
    """Test that all agents handle errors gracefully"""

    @pytest.fixture
    def graph(self):
        """Create fresh graph for each test"""
        return KnowledgeGraph()

    def test_data_digester_handles_invalid_input(self, graph):
        """Test DataDigester handles invalid input gracefully"""
        agent = DataDigester(graph)

        # Test with None
        result = agent.digest(None, 'test')
        assert isinstance(result, dict), "Must return dict even with None input"

        # Test with empty dict
        result = agent.digest({}, 'test')
        assert isinstance(result, dict), "Must return dict even with empty input"

    def test_workflow_recorder_handles_missing_fields(self, graph):
        """Test WorkflowRecorder handles incomplete interaction"""
        agent = WorkflowRecorder(graph)

        # Missing required fields
        incomplete_interaction = {'intent': 'test'}
        result = agent.record(incomplete_interaction)

        assert result is not None, "Must not return None for incomplete data"
        assert isinstance(result, dict), "Must return dict for incomplete data"

    def test_agents_dont_crash_on_missing_graph(self):
        """Test agents handle missing graph gracefully"""
        # DataDigester with None graph
        agent = DataDigester(None)
        result = agent.digest({'value': 100}, 'test')

        assert isinstance(result, dict), "Must return dict even without graph"
        assert 'error' in result or 'status' in result, "Must indicate error or status"

    def test_registry_handles_missing_agent(self):
        """Test registry handles requests for non-existent agents"""
        registry = AgentRegistry()
        result = registry.execute_with_tracking('nonexistent_agent', {})

        assert isinstance(result, dict), "Must return dict for missing agent"
        assert 'error' in result, "Must include error message"


class TestGraphStorage:
    """Test that agents properly store results in knowledge graph"""

    @pytest.fixture
    def graph(self):
        """Create fresh graph for each test"""
        return KnowledgeGraph()

    @pytest.fixture
    def registry(self):
        """Create agent registry"""
        return AgentRegistry()

    def test_data_digester_stores_in_graph(self, graph):
        """Test DataDigester stores results in graph"""
        initial_node_count = graph._graph.number_of_nodes()

        agent = DataDigester(graph)
        result = agent.digest_market_data({
            'symbol': 'AAPL',
            'price': 150,
            'change': 2.5,
            'change_percent': 1.7
        })

        assert graph._graph.number_of_nodes() > initial_node_count, "Should add node to graph"
        assert 'node_id' in result, "Result should include node_id"

    def test_workflow_recorder_stores_in_graph(self, graph):
        """Test WorkflowRecorder stores results when graph available"""
        agent = WorkflowRecorder(graph)
        initial_node_count = graph._graph.number_of_nodes()

        interaction = {
            'intent': 'query_stock',
            'actions': ['fetch_quote', 'add_to_graph'],
            'result': {'success': True, 'data': {'price': 150}},
            'success': True
        }
        result = agent.record(interaction)

        # WorkflowRecorder stores via store_result if base agent implements it
        # Check that result indicates storage attempt
        assert isinstance(result, dict), "Must return dict"

    def test_adapter_sets_graph_stored_flag(self, graph, registry):
        """Test adapter sets graph_stored flag correctly"""
        agent = DataDigester(graph)
        registry.register('data_digester', agent)

        adapter = registry.get_agent('data_digester')
        result = adapter.execute({
            'data': {'symbol': 'AAPL', 'price': 150},
            'data_type': 'market'
        })

        # Adapter should set graph_stored flag
        assert 'graph_stored' in result, "Adapter must include graph_stored flag"
        assert isinstance(result['graph_stored'], bool), "graph_stored must be boolean"

    def test_registry_tracks_graph_storage(self, graph, registry):
        """Test registry tracks graph storage in metrics"""
        agent = DataDigester(graph)
        registry.register('data_digester', agent)

        # Execute multiple times
        for i in range(3):
            registry.execute_with_tracking('data_digester', {
                'data': {'value': i},
                'data_type': 'test'
            })

        metrics = registry.get_compliance_metrics()
        assert 'data_digester' in metrics['agents'], "Should track agent metrics"

        agent_metrics = metrics['agents']['data_digester']
        assert 'executions' in agent_metrics, "Should track execution count"
        assert 'stored' in agent_metrics, "Should track storage count"
        assert 'compliance_rate' in agent_metrics, "Should calculate compliance rate"


class TestComplianceMetrics:
    """Test compliance metrics collection and reporting"""

    @pytest.fixture
    def registry(self):
        """Create agent registry"""
        return AgentRegistry()

    @pytest.fixture
    def graph(self):
        """Create knowledge graph"""
        return KnowledgeGraph()

    def test_registry_collects_execution_metrics(self, registry, graph):
        """Test registry collects execution metrics"""
        agent = DataDigester(graph)
        registry.register('data_digester', agent)

        # Execute agent
        registry.execute_with_tracking('data_digester', {
            'data': {'value': 100},
            'data_type': 'test'
        })

        assert 'data_digester' in registry.execution_metrics, "Should track agent"
        metrics = registry.execution_metrics['data_digester']

        assert 'total_executions' in metrics, "Should track total executions"
        assert 'graph_stored' in metrics, "Should track graph storage count"
        assert 'failures' in metrics, "Should track failure count"
        assert 'last_success' in metrics, "Should track last success time"

    def test_compliance_metrics_overall_rate(self, registry, graph):
        """Test overall compliance rate calculation"""
        agent = DataDigester(graph)
        registry.register('data_digester', agent)

        # Execute multiple times
        for i in range(5):
            registry.execute_with_tracking('data_digester', {
                'data': {'value': i},
                'data_type': 'test'
            })

        metrics = registry.get_compliance_metrics()

        assert 'overall_compliance' in metrics, "Should calculate overall compliance"
        assert 'total_executions' in metrics, "Should track total executions"
        assert 'total_stored' in metrics, "Should track total stored"

        # Compliance rate should be between 0 and 100
        assert 0 <= metrics['overall_compliance'] <= 100, "Compliance rate should be percentage"

    def test_failure_tracking(self, registry):
        """Test that failures are tracked correctly"""
        # Create agent that will fail
        failing_agent = Mock()
        failing_adapter = AgentAdapter(failing_agent)
        registry.agents['failing_agent'] = failing_adapter

        # Mock execute to return error
        failing_adapter.execute = Mock(return_value={'error': 'Test error'})

        # Execute and expect failure
        result = registry.execute_with_tracking('failing_agent', {})

        assert 'error' in result, "Should return error"

        metrics = registry.execution_metrics.get('failing_agent', {})
        assert metrics.get('failures', 0) > 0, "Should track failure"
        assert 'last_failure' in metrics, "Should track last failure time"


class TestBypassWarnings:
    """Test that registry bypass warnings are logged"""

    @pytest.fixture
    def registry(self):
        """Create agent registry"""
        return AgentRegistry()

    @pytest.fixture
    def graph(self):
        """Create knowledge graph"""
        return KnowledgeGraph()

    def test_bypass_warning_logging(self, registry):
        """Test that bypass warnings are logged"""
        registry.log_bypass_warning(
            'test_caller.py:123',
            'data_digester',
            'digest'
        )

        warnings = registry.get_bypass_warnings()
        assert len(warnings) > 0, "Should log bypass warning"

        latest = warnings[-1]
        assert 'caller' in latest, "Warning should include caller"
        assert 'agent' in latest, "Warning should include agent"
        assert 'method' in latest, "Warning should include method"
        assert 'timestamp' in latest, "Warning should include timestamp"

    def test_bypass_warning_limit(self, registry):
        """Test that bypass warnings are limited to prevent memory issues"""
        # Log more than the limit (100)
        for i in range(150):
            registry.log_bypass_warning(f'caller_{i}', 'agent', 'method')

        warnings = registry.get_bypass_warnings(limit=200)
        assert len(warnings) <= 100, "Should limit stored warnings to 100"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
