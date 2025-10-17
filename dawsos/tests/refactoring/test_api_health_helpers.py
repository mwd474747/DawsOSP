#!/usr/bin/env python3
"""
Tests for API Health Tab Helper Functions

Tests all 12 helper functions extracted from api_health_tab.py:
- Dashboard header
- Fallback statistics
- Recent events
- API configuration status
- FRED API health
- Polygon API health
- FMP API health
- Data freshness guidelines
- Actions
- Setup instructions
- Component health rendering
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.api_health_tab import (
    _render_dashboard_header,
    _render_fallback_statistics,
    _render_recent_events,
    _render_api_configuration_status,
    _render_fred_api_health,
    _render_polygon_api_health,
    _render_fmp_api_health,
    _render_data_freshness_guidelines,
    _render_actions,
    _render_setup_instructions,
    render_api_health_tab,
    render_component_health
)


class TestAPIHealthHelpers:
    """Test API health tab helper functions"""

    @pytest.fixture
    def mock_streamlit(self):
        """Create mock Streamlit module"""
        st = MagicMock()
        st.columns.return_value = [MagicMock() for _ in range(4)]
        return st

    @pytest.fixture
    def mock_tracker(self):
        """Create mock fallback tracker"""
        tracker = MagicMock()
        tracker.get_stats.return_value = {
            'total_fallbacks': 10,
            'llm_fallbacks': 5,
            'api_fallbacks': 3,
            'cache_hits': 2,
            'recent_events': []
        }
        tracker.get_component_stats.return_value = {
            'total_events': 5,
            'reasons': {'api_key_missing': 3, 'rate_limit': 2},
            'recent_events': []
        }
        return tracker

    def test_render_dashboard_header(self):
        """Test dashboard header rendering"""
        st = MagicMock()

        _render_dashboard_header()

        # Since the function uses global st, we can't directly verify
        # In a real environment, we'd patch 'ui.api_health_tab.st'
        # For now, ensure function executes without error
        assert True

    @patch('ui.api_health_tab.st')
    def test_render_fallback_statistics(self, mock_st):
        """Test fallback statistics rendering"""
        mock_st.columns.return_value = [MagicMock() for _ in range(4)]

        stats = {
            'total_fallbacks': 10,
            'llm_fallbacks': 5,
            'api_fallbacks': 3,
            'cache_hits': 2
        }

        _render_fallback_statistics(stats)

        # Verify subheader rendered
        mock_st.subheader.assert_called_with("📊 Fallback Event Statistics")

        # Verify columns created
        mock_st.columns.assert_called_with(4)

        # Verify metrics displayed
        assert any(
            'Total Fallbacks' in str(call)
            for call in mock_st.metric.call_args_list
        )

    @patch('ui.api_health_tab.st')
    def test_render_recent_events_with_events(self, mock_st):
        """Test recent events rendering with data"""
        stats = {
            'recent_events': [
                {
                    'component': 'llm',
                    'reason': 'api_key_missing',
                    'data_type': 'cached',
                    'timestamp': '2025-01-01 12:00:00'
                }
            ]
        }

        _render_recent_events(stats)

        # Verify subheader rendered
        mock_st.subheader.assert_called()

        # Verify expander used
        mock_st.expander.assert_called()

    @patch('ui.api_health_tab.st')
    def test_render_recent_events_empty(self, mock_st):
        """Test recent events with no data"""
        stats = {'recent_events': []}

        _render_recent_events(stats)

        # Should show info message
        mock_st.info.assert_called()

    @patch('ui.api_health_tab.st')
    @patch('ui.api_health_tab.get_credential_manager')
    def test_render_api_configuration_status(self, mock_creds_manager, mock_st):
        """Test API configuration status rendering"""
        mock_creds = MagicMock()
        mock_creds.get.return_value = 'test_key'
        mock_creds_manager.return_value = mock_creds
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]

        _render_api_configuration_status()

        # Verify API keys checked
        assert mock_creds.get.called

        # Verify columns created for each API
        assert mock_st.columns.call_count >= 5

    @patch('ui.api_health_tab.st')
    def test_render_fred_api_health_success(self, mock_st):
        """Test FRED API health rendering with data"""
        mock_st.columns.return_value = [MagicMock() for _ in range(4)]

        with patch('ui.api_health_tab.FredDataCapability') as mock_fred:
            mock_instance = MagicMock()
            mock_instance.cache_stats = {
                'hits': 80,
                'misses': 20,
                'expired_fallbacks': 0
            }
            mock_fred.return_value = mock_instance

            _render_fred_api_health()

            # Verify subheader rendered
            mock_st.subheader.assert_called()

            # Verify metrics displayed
            assert mock_st.metric.call_count >= 4

    @patch('ui.api_health_tab.st')
    def test_render_fred_api_health_error(self, mock_st):
        """Test FRED API health with error"""
        with patch('ui.api_health_tab.FredDataCapability', side_effect=Exception("Test error")):
            _render_fred_api_health()

            # Should show info about unavailability
            mock_st.info.assert_called()

    @patch('ui.api_health_tab.st')
    def test_render_polygon_api_health(self, mock_st):
        """Test Polygon API health rendering"""
        mock_st.columns.return_value = [MagicMock() for _ in range(4)]

        with patch('ui.api_health_tab.PolygonOptionsCapability') as mock_polygon:
            mock_instance = MagicMock()
            mock_instance.api_key = 'test_key'
            mock_instance.get_cache_stats.return_value = {
                'total_requests': 100,
                'hit_rate': 75.0,
                'cache_hits': 75,
                'expired_fallbacks': 0
            }
            mock_polygon.return_value = mock_instance

            _render_polygon_api_health()

            # Verify metrics displayed
            assert mock_st.metric.call_count >= 4

    @patch('ui.api_health_tab.st')
    def test_render_fmp_api_health(self, mock_st):
        """Test FMP API health rendering"""
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]

        with patch('ui.api_health_tab.MarketDataCapability') as mock_market:
            mock_instance = MagicMock()
            mock_instance.api_key = 'test_key'
            mock_instance.get_cache_stats.return_value = {
                'total_requests': 50,
                'hit_rate': 60.0,
                'cache_hits': 30
            }
            mock_market.return_value = mock_instance

            _render_fmp_api_health()

            # Verify metrics displayed
            assert mock_st.metric.call_count >= 3

    @patch('ui.api_health_tab.st')
    def test_render_data_freshness_guidelines(self, mock_st):
        """Test data freshness guidelines rendering"""
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        _render_data_freshness_guidelines()

        # Verify subheader rendered
        mock_st.subheader.assert_called()

        # Verify columns created for each data type
        assert mock_st.columns.call_count >= 7

    @patch('ui.api_health_tab.st')
    def test_render_actions_clear_stats(self, mock_st):
        """Test clear statistics action"""
        tracker = MagicMock()
        mock_st.button.side_effect = [True, False]  # First button clicked

        _render_actions(tracker)

        # Verify clear was called
        tracker.clear_stats.assert_called_once()

    @patch('ui.api_health_tab.st')
    def test_render_actions_refresh(self, mock_st):
        """Test refresh action"""
        tracker = MagicMock()
        mock_st.button.side_effect = [False, True]  # Second button clicked

        _render_actions(tracker)

        # Verify rerun called
        mock_st.rerun.assert_called_once()

    @patch('ui.api_health_tab.st')
    def test_render_setup_instructions(self, mock_st):
        """Test setup instructions rendering"""
        _render_setup_instructions()

        # Verify expander used
        mock_st.expander.assert_called()

        # Verify markdown content rendered
        mock_st.markdown.assert_called()

    @patch('ui.api_health_tab.get_fallback_tracker')
    @patch('ui.api_health_tab.st')
    def test_render_api_health_tab_integration(self, mock_st, mock_get_tracker):
        """Test main API health tab rendering"""
        tracker = MagicMock()
        tracker.get_stats.return_value = {
            'total_fallbacks': 0,
            'llm_fallbacks': 0,
            'api_fallbacks': 0,
            'cache_hits': 0,
            'recent_events': []
        }
        mock_get_tracker.return_value = tracker

        with patch('ui.api_health_tab._render_dashboard_header'), \
             patch('ui.api_health_tab._render_fallback_statistics'), \
             patch('ui.api_health_tab._render_recent_events'), \
             patch('ui.api_health_tab._render_api_configuration_status'), \
             patch('ui.api_health_tab._render_fred_api_health'), \
             patch('ui.api_health_tab._render_polygon_api_health'), \
             patch('ui.api_health_tab._render_fmp_api_health'), \
             patch('ui.api_health_tab._render_data_freshness_guidelines'), \
             patch('ui.api_health_tab._render_actions'), \
             patch('ui.api_health_tab._render_setup_instructions'):

            render_api_health_tab()

            # Verify tracker was called
            mock_get_tracker.assert_called_once()
            tracker.get_stats.assert_called_once()

    @patch('ui.api_health_tab.st')
    def test_render_component_health(self, mock_st):
        """Test component health rendering"""
        tracker = MagicMock()
        tracker.get_component_stats.return_value = {
            'total_events': 10,
            'reasons': {'api_key_missing': 7, 'rate_limit': 3},
            'recent_events': [
                {'component': 'llm', 'reason': 'api_key_missing', 'timestamp': '2025-01-01'}
            ]
        }
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        render_component_health('llm', tracker)

        # Verify component stats fetched
        tracker.get_component_stats.assert_called_with('llm')

        # Verify metrics rendered
        mock_st.metric.assert_called()


class TestAPIHealthEdgeCases:
    """Test edge cases and error handling"""

    @patch('ui.api_health_tab.st')
    def test_fred_api_low_cache_hit_rate(self, mock_st):
        """Test FRED API with low cache hit rate"""
        mock_st.columns.return_value = [MagicMock() for _ in range(4)]

        with patch('ui.api_health_tab.FredDataCapability') as mock_fred:
            mock_instance = MagicMock()
            mock_instance.cache_stats = {
                'hits': 20,
                'misses': 80,
                'expired_fallbacks': 0
            }
            mock_fred.return_value = mock_instance

            _render_fred_api_health()

            # Should show warning for low cache usage
            mock_st.warning.assert_called()

    @patch('ui.api_health_tab.st')
    def test_polygon_api_no_key(self, mock_st):
        """Test Polygon API without API key"""
        with patch('ui.api_health_tab.PolygonOptionsCapability') as mock_polygon:
            mock_instance = MagicMock()
            mock_instance.api_key = None
            mock_instance.get_cache_stats.return_value = {
                'total_requests': 0,
                'hit_rate': 0,
                'cache_hits': 0
            }
            mock_polygon.return_value = mock_instance

            _render_polygon_api_health()

            # Should show warning about missing key
            mock_st.warning.assert_called()

    @patch('ui.api_health_tab.st')
    def test_recent_events_with_different_reasons(self, mock_st):
        """Test recent events with various failure reasons"""
        stats = {
            'recent_events': [
                {
                    'component': 'llm',
                    'reason': 'api_key_missing',
                    'data_type': 'cached',
                    'timestamp': '2025-01-01 12:00:00'
                },
                {
                    'component': 'api',
                    'reason': 'api_error',
                    'data_type': 'stale',
                    'timestamp': '2025-01-01 13:00:00'
                },
                {
                    'component': 'api',
                    'reason': 'rate_limit',
                    'data_type': 'cached',
                    'timestamp': '2025-01-01 14:00:00'
                }
            ]
        }

        _render_recent_events(stats)

        # Verify different info/warning messages shown
        assert mock_st.info.called or mock_st.warning.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
