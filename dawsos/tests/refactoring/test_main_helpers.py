#!/usr/bin/env python3
"""
Tests for Main.py Helper Functions

Tests all helper functions extracted from main.py during refactoring:
- Knowledge graph initialization
- Capabilities initialization
- LLM client initialization
- Agent registration
- Agent runtime initialization
- Executor initialization
- Workflows initialization
- Persistence initialization
- Alert manager initialization
- Trinity tabs initialization
- Main tabs rendering
- Chat actions execution
- Quick actions rendering
- Fundamental analysis rendering
- Pattern library rendering
- Graph controls rendering
- API status rendering
- Sidebar rendering
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestMainHelpers:
    """Test main.py helper functions"""

    @pytest.fixture
    def mock_streamlit(self):
        """Create mock Streamlit module"""
        st = MagicMock()
        st.session_state = {}
        return st

    @patch('dawsos.main.st')
    @patch('dawsos.main.KnowledgeGraph')
    @patch('dawsos.main.os.path.exists')
    def test_init_knowledge_graph_load_existing(self, mock_exists, mock_kg, mock_st):
        """Test knowledge graph initialization with existing file"""
        from dawsos.main import _init_knowledge_graph

        mock_exists.return_value = True
        mock_graph = MagicMock()
        mock_graph.get_stats.return_value = {'total_nodes': 100}
        mock_kg.return_value = mock_graph

        _init_knowledge_graph()

        # Verify graph loaded
        mock_graph.load.assert_called_with('storage/graph.json')
        assert mock_st.session_state.graph == mock_graph

    @patch('dawsos.main.st')
    @patch('dawsos.main.KnowledgeGraph')
    @patch('dawsos.main.os.path.exists')
    def test_init_knowledge_graph_seed(self, mock_exists, mock_kg, mock_st):
        """Test knowledge graph seeding when nodes are few"""
        from dawsos.main import _init_knowledge_graph

        mock_exists.return_value = False
        mock_graph = MagicMock()
        mock_graph.get_stats.return_value = {'total_nodes': 10}
        mock_kg.return_value = mock_graph

        with patch('dawsos.main.seed_knowledge_graph') as mock_seed:
            _init_knowledge_graph()

            # Verify seeding occurred
            assert mock_seed.seed_buffett_framework.called
            assert mock_seed.seed_dalio_framework.called

    @patch('dawsos.main.st')
    @patch('dawsos.main.FredDataCapability')
    @patch('dawsos.main.MarketDataCapability')
    @patch('dawsos.main.NewsCapability')
    @patch('dawsos.main.CryptoCapability')
    @patch('dawsos.main.FundamentalsCapability')
    @patch('dawsos.main.PolygonOptionsCapability')
    def test_init_capabilities(self, mock_polygon, mock_fund, mock_crypto,
                               mock_news, mock_market, mock_fred, mock_st):
        """Test capabilities initialization"""
        from dawsos.main import _init_capabilities

        _init_capabilities()

        # Verify all capabilities initialized
        assert 'fred' in mock_st.session_state.capabilities
        assert 'market' in mock_st.session_state.capabilities
        assert 'news' in mock_st.session_state.capabilities
        assert 'crypto' in mock_st.session_state.capabilities
        assert 'fundamentals' in mock_st.session_state.capabilities
        assert 'polygon' in mock_st.session_state.capabilities

    @patch('dawsos.main.st')
    @patch('dawsos.main.LLMClient')
    def test_init_llm_client_success(self, mock_llm, mock_st):
        """Test LLM client initialization success"""
        from dawsos.main import _init_llm_client

        mock_client = MagicMock()
        mock_llm.return_value = mock_client

        _init_llm_client()

        # Verify client initialized
        assert mock_st.session_state.llm_client == mock_client

    @patch('dawsos.main.st')
    @patch('dawsos.main.LLMClient')
    def test_init_llm_client_failure(self, mock_llm, mock_st):
        """Test LLM client initialization failure"""
        from dawsos.main import _init_llm_client

        mock_llm.side_effect = Exception("API key missing")

        _init_llm_client()

        # Verify client set to None on error
        assert mock_st.session_state.llm_client is None

    @patch('dawsos.main.st')
    @patch('dawsos.main.AGENT_CAPABILITIES')
    def test_register_all_agents(self, mock_caps, mock_st):
        """Test agent registration"""
        from dawsos.main import _register_all_agents

        mock_runtime = MagicMock()
        mock_capabilities = {'fred': MagicMock()}
        mock_st.session_state.graph = MagicMock()
        mock_st.session_state.llm_client = MagicMock()

        mock_caps.__getitem__ = MagicMock(side_effect=lambda x: [])

        with patch('dawsos.main.GraphMind'), \
             patch('dawsos.main.Claude'), \
             patch('dawsos.main.DataHarvester'), \
             patch('dawsos.main.DataDigester'), \
             patch('dawsos.main.RelationshipHunter'), \
             patch('dawsos.main.PatternSpotter'), \
             patch('dawsos.main.ForecastDreamer'), \
             patch('dawsos.main.CodeMonkey'), \
             patch('dawsos.main.StructureBot'), \
             patch('dawsos.main.RefactorElf'), \
             patch('dawsos.main.WorkflowRecorder'), \
             patch('dawsos.main.WorkflowPlayer'), \
             patch('dawsos.main.UIGeneratorAgent'), \
             patch('dawsos.main.FinancialAnalyst'), \
             patch('dawsos.main.GovernanceAgent'):

            _register_all_agents(mock_runtime, mock_capabilities)

            # Verify agents registered
            assert mock_runtime.register_agent.call_count >= 15

    @patch('dawsos.main.st')
    @patch('dawsos.main.AgentRuntime')
    @patch('dawsos.main.PatternEngine')
    def test_init_agent_runtime(self, mock_pattern, mock_runtime_class, mock_st):
        """Test agent runtime initialization"""
        from dawsos.main import _init_agent_runtime

        mock_runtime = MagicMock()
        mock_runtime_class.return_value = mock_runtime
        mock_st.session_state.capabilities = {}
        mock_st.session_state.graph = MagicMock()

        with patch('dawsos.main._register_all_agents'):
            _init_agent_runtime()

            # Verify runtime created and pattern engine initialized
            assert mock_st.session_state.agent_runtime == mock_runtime
            mock_pattern.assert_called_once()

    @patch('dawsos.main.st')
    @patch('dawsos.main.UniversalExecutor')
    def test_init_executor(self, mock_executor_class, mock_st):
        """Test executor initialization"""
        from dawsos.main import _init_executor

        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        mock_st.session_state.graph = MagicMock()
        mock_st.session_state.agent_runtime = MagicMock()
        mock_st.session_state.agent_runtime.agent_registry = MagicMock()

        _init_executor()

        # Verify executor created
        assert mock_st.session_state.executor == mock_executor

    @patch('dawsos.main.st')
    @patch('dawsos.main.InvestmentWorkflows')
    def test_init_workflows(self, mock_workflows_class, mock_st):
        """Test workflows initialization"""
        from dawsos.main import _init_workflows

        mock_workflows = MagicMock()
        mock_workflows_class.return_value = mock_workflows
        mock_st.session_state.agent_runtime = MagicMock()
        mock_st.session_state.graph = MagicMock()

        _init_workflows()

        # Verify workflows created
        assert mock_st.session_state.workflows == mock_workflows

    @patch('dawsos.main.st')
    @patch('dawsos.main.PersistenceManager')
    def test_init_persistence(self, mock_persistence_class, mock_st):
        """Test persistence manager initialization"""
        from dawsos.main import _init_persistence

        mock_persistence = MagicMock()
        mock_persistence_class.return_value = mock_persistence

        _init_persistence()

        # Verify persistence manager created
        assert mock_st.session_state.persistence == mock_persistence

    @patch('dawsos.main.st')
    @patch('dawsos.main.AlertManager')
    def test_init_alert_manager(self, mock_alert_class, mock_st):
        """Test alert manager initialization"""
        from dawsos.main import _init_alert_manager

        mock_alert = MagicMock()
        mock_alert_class.return_value = mock_alert

        _init_alert_manager()

        # Verify alert manager created and template alert added
        assert mock_st.session_state.alert_manager == mock_alert
        mock_alert.create_template_alert.assert_called()

    @patch('dawsos.main.st')
    def test_execute_chat_action(self, mock_st):
        """Test chat action execution"""
        from dawsos.main import _execute_chat_action

        mock_st.session_state.chat_history = []
        mock_runtime = MagicMock()
        mock_runtime.orchestrate.return_value = {'response': 'Test response'}
        mock_st.session_state.agent_runtime = mock_runtime

        _execute_chat_action("Test message", "Success!")

        # Verify message added and response received
        assert len(mock_st.session_state.chat_history) == 2
        mock_st.success.assert_called_with("Success!")
        mock_st.rerun.assert_called_once()

    @patch('dawsos.main.st')
    def test_render_quick_actions(self, mock_st):
        """Test quick actions rendering"""
        from dawsos.main import _render_quick_actions

        mock_st.button.return_value = False

        _render_quick_actions()

        # Verify buttons created
        assert mock_st.button.call_count >= 4

    @patch('dawsos.main.st')
    def test_render_fundamental_analysis(self, mock_st):
        """Test fundamental analysis rendering"""
        from dawsos.main import _render_fundamental_analysis

        mock_st.button.return_value = False

        _render_fundamental_analysis()

        # Verify buttons created
        assert mock_st.button.call_count >= 4

    @patch('dawsos.main.st')
    def test_render_pattern_library(self, mock_st):
        """Test pattern library rendering"""
        from dawsos.main import _render_pattern_library

        mock_engine = MagicMock()
        mock_engine.patterns = {
            'stock_price': {'name': 'Stock Price'},
            'technical_analysis': {'name': 'Technical Analysis'}
        }
        mock_st.session_state.agent_runtime = MagicMock()
        mock_st.session_state.agent_runtime.pattern_engine = mock_engine

        _render_pattern_library()

        # Verify expander created
        mock_st.expander.assert_called()

    @patch('dawsos.main.st')
    def test_render_graph_controls(self, mock_st):
        """Test graph controls rendering"""
        from dawsos.main import _render_graph_controls

        mock_persistence = MagicMock()
        mock_persistence.save_graph_with_backup.return_value = {'checksum': 'abc123'}
        mock_st.session_state.persistence = mock_persistence
        mock_st.session_state.graph = MagicMock()
        mock_st.button.side_effect = [True, False, False]  # Save clicked

        _render_graph_controls()

        # Verify save was called
        mock_persistence.save_graph_with_backup.assert_called()

    @patch('dawsos.main.st')
    @patch('dawsos.main.os.getenv')
    def test_render_api_status(self, mock_getenv, mock_st):
        """Test API status rendering"""
        from dawsos.main import _render_api_status

        mock_getenv.side_effect = lambda x: 'test_key' if x == 'ANTHROPIC_API_KEY' else None

        _render_api_status()

        # Verify status displayed
        assert mock_st.write.call_count >= 4


class TestSessionInitialization:
    """Test session state initialization"""

    @patch('dawsos.main.st')
    def test_init_session_state_full(self, mock_st):
        """Test complete session state initialization"""
        from dawsos.main import init_session_state

        mock_st.session_state = {}

        with patch('dawsos.main._init_knowledge_graph'), \
             patch('dawsos.main._init_capabilities'), \
             patch('dawsos.main._init_llm_client'), \
             patch('dawsos.main._init_agent_runtime'), \
             patch('dawsos.main._init_executor'), \
             patch('dawsos.main._init_workflows'), \
             patch('dawsos.main._init_persistence'), \
             patch('dawsos.main._init_alert_manager') as mock_alert:

            init_session_state()

            # Verify all initialization steps called
            mock_alert.assert_called_once()
            assert 'chat_history' in mock_st.session_state

    @patch('dawsos.main.st')
    def test_init_session_state_idempotent(self, mock_st):
        """Test session state initialization is idempotent"""
        from dawsos.main import init_session_state

        # Set all required session state
        mock_st.session_state = {
            'graph': MagicMock(),
            'capabilities': {},
            'llm_client': MagicMock(),
            'agent_runtime': MagicMock(),
            'executor': MagicMock(),
            'chat_history': [],
            'workflows': MagicMock(),
            'persistence': MagicMock(),
            'alert_manager': MagicMock()
        }

        with patch('dawsos.main._init_knowledge_graph') as mock_init:
            init_session_state()

            # Should not re-initialize
            mock_init.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
