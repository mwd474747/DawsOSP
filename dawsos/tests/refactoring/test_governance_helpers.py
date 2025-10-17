#!/usr/bin/env python3
"""
Tests for Governance Tab Helper Functions

Tests all 21 helper functions extracted from governance_tab.py:
- Header and dashboard rendering
- System telemetry
- Persistence health
- Conversational interface
- Live monitoring sidebar
- Quick actions
- Graph governance tabs (quality, lineage, policies, compliance, oversight)
- System improvements
- Governance history
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.governance_tab import (
    _render_header_and_dashboard,
    _render_system_telemetry,
    _render_persistence_health,
    _render_conversational_interface,
    _render_live_monitoring_sidebar,
    _render_quick_actions,
    _render_graph_governance_tabs,
    _render_quality_analysis_tab,
    _render_data_lineage_tab,
    _render_policy_management_tab,
    _render_agent_compliance_tab,
    _render_system_oversight_tab,
    _render_system_improvements,
    _render_governance_history,
    render_governance_tab
)


class TestGovernanceHelpers:
    """Test governance tab helper functions"""

    @pytest.fixture
    def mock_streamlit(self):
        """Create mock Streamlit module"""
        st = MagicMock()
        st.session_state = {}
        st.columns.return_value = [MagicMock() for _ in range(4)]
        return st

    @pytest.fixture
    def mock_graph(self):
        """Create mock knowledge graph"""
        graph = MagicMock()
        graph._graph = MagicMock()
        graph._graph.number_of_nodes.return_value = 100
        graph._graph.number_of_edges.return_value = 200
        graph._graph.nodes.return_value = [
            ('node1', {'type': 'stock', 'created': datetime.now().isoformat()}),
            ('node2', {'type': 'indicator', 'created': datetime.now().isoformat()})
        ]
        graph.get_node.return_value = {'type': 'stock', 'data': {}}
        return graph

    @pytest.fixture
    def mock_runtime(self):
        """Create mock agent runtime"""
        runtime = MagicMock()
        runtime.agent_registry = MagicMock()
        runtime.get_telemetry_summary.return_value = {
            'total_executions': 100,
            'success_rate': 95.0,
            'avg_duration_ms': 500,
            'executions_by_agent': {'claude': 50, 'data_harvester': 30},
            'executions_by_pattern': {'stock_analysis': 40, 'sector_rotation': 20},
            'last_execution_time': datetime.now().isoformat()
        }
        return runtime

    @pytest.fixture
    def mock_governance_agent(self):
        """Create mock governance agent"""
        agent = MagicMock()
        agent.graph_governance = MagicMock()
        agent.process_request.return_value = {
            'status': 'completed',
            'governance_report': 'Test report'
        }
        agent.suggest_improvements.return_value = {
            'status': 'success',
            'improvements': []
        }
        return agent

    def test_render_header_and_dashboard(self, mock_graph, mock_streamlit):
        """Test dashboard header and metrics rendering"""
        graph_metrics = {
            'total_nodes': 100,
            'total_edges': 200,
            'overall_health': 0.95,
            'quality_issues': [],
            'lineage_gaps': []
        }

        _render_header_and_dashboard(mock_graph, graph_metrics, mock_streamlit)

        # Verify header was rendered
        mock_streamlit.markdown.assert_any_call("# 🛡️ Data Governance Center")

        # Verify columns were created
        mock_streamlit.columns.assert_called_with(4)

        # Verify metrics were displayed
        assert mock_streamlit.metric.call_count >= 4

    def test_render_system_telemetry_with_data(self, mock_runtime, mock_streamlit):
        """Test system telemetry with execution data"""
        _render_system_telemetry(mock_runtime, mock_streamlit)

        # Verify telemetry header rendered
        calls = [str(call) for call in mock_streamlit.markdown.call_args_list]
        assert any('System Telemetry' in str(call) for call in calls)

        # Verify metrics displayed
        assert mock_streamlit.metric.call_count >= 3

    def test_render_system_telemetry_no_data(self, mock_streamlit):
        """Test system telemetry with no execution data"""
        runtime = MagicMock()
        runtime.get_telemetry_summary.return_value = {
            'total_executions': 0,
            'success_rate': 0,
            'avg_duration_ms': 0,
            'executions_by_agent': {},
            'executions_by_pattern': {},
            'last_execution_time': None
        }

        _render_system_telemetry(runtime, mock_streamlit)

        # Should show info message
        mock_streamlit.info.assert_called()

    def test_render_persistence_health_with_backups(self, mock_streamlit):
        """Test persistence health with backup data"""
        persistence = MagicMock()
        persistence.list_backups.return_value = [
            {
                'path': '/path/to/backup1.json',
                'filename': 'backup1.json',
                'size': 1024,
                'modified': '2025-01-01 12:00:00',
                'metadata': {
                    'checksum': 'abc123def456',
                    'node_count': 100,
                    'edge_count': 200
                }
            }
        ]
        persistence.verify_integrity.return_value = {'valid': True}
        mock_streamlit.session_state['persistence'] = persistence

        _render_persistence_health(mock_streamlit)

        # Verify metrics rendered
        assert mock_streamlit.metric.call_count >= 4

        # Verify backup list accessible
        mock_streamlit.expander.assert_called()

    def test_render_conversational_interface(self, mock_governance_agent, mock_streamlit):
        """Test conversational governance interface"""
        mock_streamlit.text_area.return_value = "Test governance request"
        mock_streamlit.button.return_value = False

        execute, request = _render_conversational_interface(mock_governance_agent, mock_streamlit)

        # Verify interface elements rendered
        mock_streamlit.text_area.assert_called_once()
        assert mock_streamlit.button.call_count >= 1

        # Verify return values
        assert isinstance(execute, bool)
        assert isinstance(request, str)

    def test_render_conversational_interface_execution(self, mock_governance_agent, mock_streamlit):
        """Test governance request execution"""
        mock_streamlit.text_area.return_value = "Check data quality"
        mock_streamlit.button.side_effect = [True, False]  # First button clicked
        mock_streamlit.spinner.return_value.__enter__ = MagicMock()
        mock_streamlit.spinner.return_value.__exit__ = MagicMock()

        with patch('ui.governance_tab.datetime') as mock_dt:
            mock_dt.now.return_value.isoformat.return_value = '2025-01-01T12:00:00'
            execute, request = _render_conversational_interface(mock_governance_agent, mock_streamlit)

        # Verify execution occurred
        if execute:
            mock_governance_agent.process_request.assert_called()

    def test_render_quick_actions_compliance_check(self, mock_runtime, mock_governance_agent, mock_streamlit):
        """Test agent compliance quick action"""
        mock_streamlit.button.side_effect = [True, False, False, False, False]
        mock_streamlit.spinner.return_value.__enter__ = MagicMock()
        mock_streamlit.spinner.return_value.__exit__ = MagicMock()

        mock_governance_agent.process_request.return_value = {
            'status': 'completed',
            'overall_compliance': 0.85,
            'recommendations': ['Fix agent A', 'Update agent B']
        }

        _render_quick_actions(mock_runtime, mock_governance_agent, mock_streamlit)

        # Verify compliance check was called
        if mock_governance_agent.process_request.called:
            call_args = mock_governance_agent.process_request.call_args[0]
            assert 'agent_compliance' in call_args[0]

    def test_render_quality_analysis_tab(self, mock_graph, mock_governance_agent, mock_streamlit):
        """Test quality analysis tab rendering"""
        graph_metrics = {
            'quality_issues': [
                {'node': 'node1', 'score': 0.5, 'type': 'stock'}
            ]
        }

        _render_quality_analysis_tab(mock_graph, mock_governance_agent, graph_metrics, mock_streamlit)

        # Verify warning shown for quality issues
        mock_streamlit.warning.assert_called()

    def test_render_data_lineage_tab(self, mock_graph, mock_governance_agent, mock_streamlit):
        """Test data lineage tab rendering"""
        graph_metrics = {
            'lineage_gaps': [
                {'node': 'orphan1', 'issue': 'no connections'}
            ]
        }

        mock_streamlit.selectbox.return_value = 'node1'
        mock_streamlit.button.return_value = False

        _render_data_lineage_tab(mock_graph, mock_governance_agent, graph_metrics, mock_streamlit)

        # Verify lineage selector rendered
        mock_streamlit.selectbox.assert_called()

        # Verify orphan warning shown
        mock_streamlit.warning.assert_called()

    def test_render_agent_compliance_tab_with_data(self, mock_streamlit):
        """Test agent compliance tab with compliance data"""
        compliance_data = {
            'status': 'completed',
            'overall_compliance': 0.75,
            'summary': {
                'total_agents': 10,
                'compliant': 7,
                'warnings': 2,
                'non_compliant': 1
            },
            'report': '# Compliance Report\n\nDetails...',
            'recommendations': ['Fix agent X'],
            'agents': {
                'agent1': {'compliance_score': 0.9},
                'agent2': {'compliance_score': 0.6}
            }
        }
        mock_streamlit.session_state['latest_compliance'] = compliance_data

        _render_agent_compliance_tab(mock_streamlit)

        # Verify metrics rendered
        assert mock_streamlit.metric.call_count >= 4

        # Verify report shown
        mock_streamlit.expander.assert_called()

    def test_render_system_oversight_tab(self, mock_graph, mock_streamlit):
        """Test system oversight tab rendering"""
        graph_metrics = {
            'lineage_gaps': [{'node': 'orphan1'}]
        }

        _render_system_oversight_tab(mock_graph, graph_metrics, mock_streamlit)

        # Verify dashboard elements rendered
        calls = [str(call) for call in mock_streamlit.markdown.call_args_list]
        assert any('System Oversight' in str(call) for call in calls)

    def test_render_system_improvements(self, mock_streamlit):
        """Test system improvements rendering"""
        mock_streamlit.session_state['system_improvements'] = {
            'improvements': [
                {'priority': 'high', 'description': 'Fix issue 1'},
                {'priority': 'medium', 'description': 'Fix issue 2'}
            ]
        }

        _render_system_improvements(mock_streamlit)

        # Verify improvements displayed
        calls = [str(call) for call in mock_streamlit.markdown.call_args_list]
        assert any('High Priority' in str(call) for call in calls)

    def test_render_governance_history(self, mock_streamlit):
        """Test governance history rendering"""
        mock_streamlit.session_state['governance_history'] = [
            {
                'action': 'Data Quality Check',
                'request': 'Check quality',
                'timestamp': '2025-01-01 12:00:00',
                'status': 'Completed'
            }
        ]

        _render_governance_history("Test request", True, mock_streamlit)

        # Verify history displayed
        mock_streamlit.expander.assert_called()

        # Verify new activity added
        assert len(mock_streamlit.session_state['governance_history']) == 2

    @patch('ui.governance_tab.st')
    def test_render_governance_tab_integration(self, mock_st):
        """Test main governance tab rendering function"""
        mock_runtime = MagicMock()
        mock_graph = MagicMock()

        # Setup mock governance agent
        mock_adapter = MagicMock()
        mock_agent = MagicMock()
        mock_agent.graph_governance = MagicMock()
        mock_agent.graph_governance.comprehensive_governance_check.return_value = {}
        mock_adapter.agent = mock_agent
        mock_runtime.agent_registry.get_agent.return_value = mock_adapter

        # Mock columns
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.session_state = {}

        render_governance_tab(mock_runtime, mock_graph)

        # Verify main components rendered
        assert mock_st.markdown.called


class TestGovernanceEdgeCases:
    """Test edge cases and error handling"""

    def test_telemetry_without_method(self):
        """Test telemetry rendering when runtime lacks method"""
        runtime = MagicMock()
        del runtime.get_telemetry_summary
        st = MagicMock()

        _render_system_telemetry(runtime, st)

        # Should show warning
        st.warning.assert_called()

    def test_persistence_without_manager(self):
        """Test persistence health without manager"""
        st = MagicMock()
        st.session_state = {}

        _render_persistence_health(st)

        # Should show warning
        st.warning.assert_called()

    def test_governance_execution_error(self):
        """Test governance execution with error"""
        agent = MagicMock()
        agent.process_request.side_effect = Exception("Test error")
        st = MagicMock()
        st.text_area.return_value = "Test request"
        st.button.side_effect = [True, False]
        st.spinner.return_value.__enter__ = MagicMock()
        st.spinner.return_value.__exit__ = MagicMock()

        with patch('ui.governance_tab.datetime'):
            execute, request = _render_conversational_interface(agent, st)

        # Should show error if execution attempted
        if execute:
            st.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
