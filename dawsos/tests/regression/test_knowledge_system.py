#!/usr/bin/env python3
"""
Regression Tests for Knowledge System (KnowledgeLoader and Graph Helpers)

Tests that:
- KnowledgeLoader caches correctly
- Stale datasets are detected
- Graph helpers work (get_node, safe_query, has_edge)
- Enriched data is accessible in patterns
- Dataset validation works
"""

import pytest
import sys
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.knowledge_loader import KnowledgeLoader
from core.knowledge_graph import KnowledgeGraph


class TestKnowledgeLoaderBasics:
    """Test basic KnowledgeLoader functionality"""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory with test data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_dir = Path(tmpdir)

            # Create test dataset
            test_data = {
                'sectors': {
                    'Technology': {'performance': 0.15},
                    'Healthcare': {'performance': 0.10}
                }
            }

            (knowledge_dir / 'sector_performance.json').write_text(
                json.dumps(test_data, indent=2)
            )

            yield knowledge_dir

    def test_knowledge_loader_initialization(self, temp_knowledge_dir):
        """Test KnowledgeLoader initializes correctly"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        assert loader is not None, "Should create loader instance"
        assert loader.knowledge_dir == temp_knowledge_dir, "Should set knowledge dir"
        assert len(loader.datasets) > 0, "Should have dataset registry"

    def test_load_dataset(self, temp_knowledge_dir):
        """Test loading a dataset"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        data = loader.get_dataset('sector_performance')

        assert data is not None, "Should load dataset"
        assert 'sectors' in data, "Should have correct structure"
        assert 'Technology' in data['sectors'], "Should have Technology sector"

    def test_dataset_not_found(self, temp_knowledge_dir):
        """Test loading non-existent dataset"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        data = loader.get_dataset('nonexistent_dataset')

        assert data is None, "Should return None for non-existent dataset"

    def test_list_datasets(self, temp_knowledge_dir):
        """Test listing available datasets"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        datasets = loader.list_datasets()

        assert isinstance(datasets, list), "Should return list"
        assert len(datasets) > 0, "Should have registered datasets"
        assert 'sector_performance' in datasets, "Should include sector_performance"


class TestKnowledgeLoaderCaching:
    """Test KnowledgeLoader caching functionality"""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_dir = Path(tmpdir)

            # Create test dataset
            test_data = {'test': 'data'}
            (knowledge_dir / 'sector_performance.json').write_text(
                json.dumps(test_data, indent=2)
            )

            yield knowledge_dir

    def test_dataset_cached_after_load(self, temp_knowledge_dir):
        """Test that dataset is cached after first load"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # First load
        data1 = loader.get_dataset('sector_performance')
        assert 'sector_performance' in loader.cache, "Should cache dataset"

        # Second load (should use cache)
        data2 = loader.get_dataset('sector_performance')
        assert data1 is data2, "Should return same cached object"

    def test_force_reload_bypasses_cache(self, temp_knowledge_dir):
        """Test that force_reload bypasses cache"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # First load
        data1 = loader.get_dataset('sector_performance')

        # Force reload
        data2 = loader.get_dataset('sector_performance', force_reload=True)

        # Should reload from disk (different object)
        assert isinstance(data2, dict), "Should load data"

    def test_cache_timestamps_tracked(self, temp_knowledge_dir):
        """Test that cache timestamps are tracked"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # Load dataset
        loader.get_dataset('sector_performance')

        assert 'sector_performance' in loader.cache_timestamps, "Should track timestamp"
        timestamp = loader.cache_timestamps['sector_performance']
        assert isinstance(timestamp, datetime), "Timestamp should be datetime"

    def test_clear_cache(self, temp_knowledge_dir):
        """Test clearing cache"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # Load and cache
        loader.get_dataset('sector_performance')
        assert 'sector_performance' in loader.cache, "Should be cached"

        # Clear specific cache
        loader.clear_cache('sector_performance')
        assert 'sector_performance' not in loader.cache, "Should clear cache"

    def test_clear_all_cache(self, temp_knowledge_dir):
        """Test clearing all cache"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # Load multiple datasets
        loader.get_dataset('sector_performance')

        # Clear all
        loader.clear_cache()
        assert len(loader.cache) == 0, "Should clear all cache"
        assert len(loader.cache_timestamps) == 0, "Should clear all timestamps"


class TestStaleDatasetDetection:
    """Test detection of stale cached datasets"""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_dir = Path(tmpdir)
            test_data = {'test': 'data'}
            (knowledge_dir / 'sector_performance.json').write_text(
                json.dumps(test_data, indent=2)
            )
            yield knowledge_dir

    def test_fresh_cache_not_stale(self, temp_knowledge_dir):
        """Test that freshly loaded data is not stale"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        loader.cache_ttl = timedelta(minutes=30)

        # Load dataset
        loader.get_dataset('sector_performance')

        # Check stale datasets
        stale = loader.get_stale_datasets()
        assert 'sector_performance' not in stale, "Fresh cache should not be stale"

    def test_old_cache_is_stale(self, temp_knowledge_dir):
        """Test that old cached data is detected as stale"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        loader.cache_ttl = timedelta(seconds=1)  # Very short TTL

        # Load dataset
        loader.get_dataset('sector_performance')

        # Wait for cache to become stale
        time.sleep(1.1)

        # Check stale datasets
        stale = loader.get_stale_datasets()
        assert 'sector_performance' in stale, "Old cache should be stale"

    def test_cache_validity_check(self, temp_knowledge_dir):
        """Test _is_cache_valid method"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        loader.cache_ttl = timedelta(seconds=1)

        # Load dataset
        loader.get_dataset('sector_performance')

        # Should be valid immediately
        assert loader._is_cache_valid('sector_performance'), "Should be valid"

        # Wait for expiration
        time.sleep(1.1)

        # Should be invalid
        assert not loader._is_cache_valid('sector_performance'), "Should be invalid"


class TestDatasetValidation:
    """Test dataset validation"""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_valid_sector_performance(self, temp_knowledge_dir):
        """Test validation of valid sector_performance dataset"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # Valid structure
        valid_data = {
            'sectors': {
                'Technology': {'performance': 0.15}
            }
        }

        assert loader._validate_sector_performance(valid_data), \
            "Should validate correct structure"

    def test_invalid_sector_performance(self, temp_knowledge_dir):
        """Test validation rejects invalid structure"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # Invalid structure (missing 'sectors')
        invalid_data = {'data': 'wrong structure'}

        assert not loader._validate_sector_performance(invalid_data), \
            "Should reject invalid structure"

    def test_validation_with_invalid_json(self, temp_knowledge_dir):
        """Test that invalid JSON is handled gracefully"""
        # Create invalid JSON file
        (temp_knowledge_dir / 'sector_performance.json').write_text(
            '{invalid json content'
        )

        loader = KnowledgeLoader(str(temp_knowledge_dir))
        data = loader.get_dataset('sector_performance')

        assert data is None, "Should return None for invalid JSON"

    def test_validation_not_dict(self, temp_knowledge_dir):
        """Test validation rejects non-dict data"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        assert not loader._validate_dataset('test', [1, 2, 3]), \
            "Should reject non-dict data"
        assert not loader._validate_dataset('test', "string"), \
            "Should reject string data"


class TestDatasetSections:
    """Test getting specific sections from datasets"""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory with nested data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_dir = Path(tmpdir)

            # Create nested dataset
            nested_data = {
                'sectors': {
                    'Technology': {
                        'performance': 0.15,
                        'companies': ['AAPL', 'MSFT']
                    }
                },
                'metadata': {
                    'last_updated': '2024-01-01'
                }
            }

            (knowledge_dir / 'sector_performance.json').write_text(
                json.dumps(nested_data, indent=2)
            )

            yield knowledge_dir

    def test_get_top_level_section(self, temp_knowledge_dir):
        """Test getting top-level section"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        sectors = loader.get_dataset_section('sector_performance', 'sectors')

        assert sectors is not None, "Should get sectors"
        assert 'Technology' in sectors, "Should have Technology"

    def test_get_nested_section_with_dot_notation(self, temp_knowledge_dir):
        """Test getting nested section with dot notation"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        performance = loader.get_dataset_section(
            'sector_performance',
            'sectors.Technology.performance'
        )

        assert performance == 0.15, "Should get nested performance value"

    def test_get_section_with_default(self, temp_knowledge_dir):
        """Test getting section with default value"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        result = loader.get_dataset_section(
            'sector_performance',
            'nonexistent.section',
            default='default_value'
        )

        assert result == 'default_value', "Should return default for missing section"

    def test_get_section_from_missing_dataset(self, temp_knowledge_dir):
        """Test getting section from non-existent dataset"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        result = loader.get_dataset_section(
            'nonexistent_dataset',
            'some.section',
            default='default'
        )

        assert result == 'default', "Should return default for missing dataset"


class TestGraphHelpers:
    """Test KnowledgeGraph helper methods"""

    @pytest.fixture
    def graph(self):
        """Create fresh graph for each test"""
        graph = KnowledgeGraph()

        # Add test nodes
        graph.add_node('stock', {'symbol': 'AAPL', 'price': 150}, 'AAPL')
        graph.add_node('stock', {'symbol': 'MSFT', 'price': 300}, 'MSFT')
        graph.add_node('sector', {'name': 'Technology'}, 'tech_sector')

        # Add test edges
        graph.connect('AAPL', 'tech_sector', 'belongs_to', 0.9)
        graph.connect('MSFT', 'tech_sector', 'belongs_to', 0.9)

        return graph

    def test_get_node_exists(self, graph):
        """Test get_node returns node when it exists"""
        node = graph.get_node('AAPL')

        assert node is not None, "Should return node"
        assert node['type'] == 'stock', "Should have correct type"
        assert node['data']['symbol'] == 'AAPL', "Should have correct data"

    def test_get_node_not_exists(self, graph):
        """Test get_node returns None when node doesn't exist"""
        node = graph.get_node('NONEXISTENT')

        assert node is None, "Should return None for missing node"

    def test_has_edge_exists(self, graph):
        """Test has_edge returns True when edge exists"""
        assert graph.has_edge('AAPL', 'tech_sector'), \
            "Should return True for existing edge"

    def test_has_edge_not_exists(self, graph):
        """Test has_edge returns False when edge doesn't exist"""
        assert not graph.has_edge('AAPL', 'MSFT'), \
            "Should return False for non-existent edge"

    def test_has_edge_with_relationship_type(self, graph):
        """Test has_edge with specific relationship type"""
        assert graph.has_edge('AAPL', 'tech_sector', 'belongs_to'), \
            "Should return True for matching relationship"

        assert not graph.has_edge('AAPL', 'tech_sector', 'wrong_type'), \
            "Should return False for wrong relationship type"

    def test_safe_query_success(self, graph):
        """Test safe_query returns results when query succeeds"""
        results = graph.safe_query({'type': 'stock'})

        assert isinstance(results, list), "Should return list"
        assert len(results) == 2, "Should find both stocks"

    def test_safe_query_no_matches(self, graph):
        """Test safe_query returns empty list when no matches"""
        results = graph.safe_query({'type': 'nonexistent'})

        assert isinstance(results, list), "Should return list"
        assert len(results) == 0, "Should return empty list"

    def test_safe_query_with_default(self, graph):
        """Test safe_query returns default when no matches"""
        results = graph.safe_query(
            {'type': 'nonexistent'},
            default=['default_value']
        )

        assert results == ['default_value'], "Should return default"

    def test_get_edge_exists(self, graph):
        """Test get_edge returns edge data when it exists"""
        edge = graph.get_edge('AAPL', 'tech_sector')

        assert edge is not None, "Should return edge"
        assert edge['type'] == 'belongs_to', "Should have correct type"
        assert edge['strength'] == 0.9, "Should have correct strength"

    def test_get_edge_not_exists(self, graph):
        """Test get_edge returns None when edge doesn't exist"""
        edge = graph.get_edge('AAPL', 'MSFT')

        assert edge is None, "Should return None for non-existent edge"

    def test_get_nodes_by_type(self, graph):
        """Test get_nodes_by_type returns all matching nodes"""
        stocks = graph.get_nodes_by_type('stock')

        assert isinstance(stocks, dict), "Should return dict"
        assert len(stocks) == 2, "Should find both stocks"
        assert 'AAPL' in stocks, "Should include AAPL"
        assert 'MSFT' in stocks, "Should include MSFT"

    def test_get_connected_nodes(self, graph):
        """Test get_connected_nodes returns connected nodes"""
        connected = graph.get_connected_nodes('tech_sector', direction='in')

        assert isinstance(connected, list), "Should return list"
        assert len(connected) == 2, "Should find both connected stocks"
        assert 'AAPL' in connected, "Should include AAPL"
        assert 'MSFT' in connected, "Should include MSFT"


class TestEnrichedDataAccessibility:
    """Test that enriched data is accessible in patterns"""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory with enriched data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_dir = Path(tmpdir)

            # Create enriched economic cycles data
            economic_data = {
                'economic_cycles': {
                    'current_assessment': {
                        'business_cycle_phase': 'mid_cycle',
                        'debt_level': 'moderate'
                    },
                    'historical_phases': [
                        {'year': 2020, 'phase': 'recession'},
                        {'year': 2021, 'phase': 'early_cycle'}
                    ]
                }
            }

            (knowledge_dir / 'economic_cycles.json').write_text(
                json.dumps(economic_data, indent=2)
            )

            yield knowledge_dir

    def test_enriched_data_loads(self, temp_knowledge_dir):
        """Test that enriched data loads successfully"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        data = loader.get_dataset('economic_cycles')

        assert data is not None, "Should load economic cycles"
        assert 'economic_cycles' in data, "Should have correct structure"

    def test_enriched_data_sections_accessible(self, temp_knowledge_dir):
        """Test that enriched data sections are accessible"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        current = loader.get_dataset_section(
            'economic_cycles',
            'economic_cycles.current_assessment'
        )

        assert current is not None, "Should access current assessment"
        assert 'business_cycle_phase' in current, "Should have phase data"

    def test_enriched_historical_data(self, temp_knowledge_dir):
        """Test accessing historical enriched data"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        historical = loader.get_dataset_section(
            'economic_cycles',
            'economic_cycles.historical_phases'
        )

        assert historical is not None, "Should access historical phases"
        assert isinstance(historical, list), "Should be a list"
        assert len(historical) > 0, "Should have historical data"


class TestDatasetInfo:
    """Test dataset information and metadata"""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            knowledge_dir = Path(tmpdir)
            test_data = {'test': 'data'}
            (knowledge_dir / 'sector_performance.json').write_text(
                json.dumps(test_data, indent=2)
            )
            yield knowledge_dir

    def test_get_dataset_info(self, temp_knowledge_dir):
        """Test getting dataset information"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        info = loader.get_dataset_info('sector_performance')

        assert 'name' in info, "Should include name"
        assert 'filename' in info, "Should include filename"
        assert 'filepath' in info, "Should include filepath"
        assert 'exists' in info, "Should include exists flag"

    def test_dataset_info_file_metadata(self, temp_knowledge_dir):
        """Test dataset info includes file metadata"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))
        info = loader.get_dataset_info('sector_performance')

        assert info['exists'], "File should exist"
        assert 'file_size' in info, "Should include file size"
        assert 'modified' in info, "Should include modification time"

    def test_dataset_info_cache_metadata(self, temp_knowledge_dir):
        """Test dataset info includes cache metadata after loading"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # Load dataset to cache it
        loader.get_dataset('sector_performance')

        info = loader.get_dataset_info('sector_performance')

        assert info['cached'], "Should be cached"
        assert 'last_loaded' in info, "Should include last loaded time"
        assert 'cache_age_seconds' in info, "Should include cache age"

    def test_reload_all_datasets(self, temp_knowledge_dir):
        """Test reloading all datasets"""
        loader = KnowledgeLoader(str(temp_knowledge_dir))

        # Load initial data
        loader.get_dataset('sector_performance')

        # Reload all
        results = loader.reload_all()

        assert isinstance(results, dict), "Should return results dict"
        assert 'sector_performance' in results, "Should include our dataset"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
