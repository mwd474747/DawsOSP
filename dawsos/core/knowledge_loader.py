#!/usr/bin/env python3
"""
Knowledge Loader - Centralized enriched dataset loading and caching

This module provides a single point of access for all enriched knowledge datasets,
replacing ad-hoc file loading throughout the codebase with a cached, validated system.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from core.logger import get_logger


class KnowledgeLoader:
    """Centralized loader for enriched knowledge datasets with caching and validation"""

    def __init__(self, knowledge_dir: str = 'dawsos/storage/knowledge'):
        """
        Initialize the knowledge loader.

        Args:
            knowledge_dir: Directory containing enriched knowledge JSON files
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = timedelta(minutes=30)  # Cache for 30 minutes
        self.logger = get_logger('KnowledgeLoader')

        # Dataset registry - maps friendly names to file paths
        self.datasets = {
            # Core datasets
            'sector_performance': 'sector_performance.json',
            'economic_cycles': 'economic_cycles.json',
            'sp500_companies': 'sp500_companies.json',
            'sector_correlations': 'sector_correlations.json',
            'relationships': 'relationship_mappings.json',
            'ui_configurations': 'ui_configurations.json',
            'company_database': 'company_database.json',

            # Investment frameworks
            'buffett_checklist': 'buffett_checklist.json',
            'buffett_framework': 'buffett_framework.json',
            'dalio_cycles': 'dalio_cycles.json',
            'dalio_framework': 'dalio_framework.json',

            # Financial data & calculations
            'financial_calculations': 'financial_calculations.json',
            'financial_formulas': 'financial_formulas.json',
            'earnings_surprises': 'earnings_surprises.json',
            'dividend_buyback': 'dividend_buyback_stats.json',

            # Factor & alternative data
            'factor_smartbeta': 'factor_smartbeta_profiles.json',
            'insider_institutional': 'insider_institutional_activity.json',
            'alt_data_signals': 'alt_data_signals.json',
            'esg_governance': 'esg_governance_scores.json',

            # Market structure & indicators
            'cross_asset_lead_lag': 'cross_asset_lead_lag.json',
            'econ_regime_watchlist': 'econ_regime_watchlist.json',
            'fx_commodities': 'fx_commodities_snapshot.json',
            'thematic_momentum': 'thematic_momentum.json',
            'volatility_stress': 'volatility_stress_indicators.json',
            'yield_curve': 'yield_curve_history.json',

            # System metadata
            'agent_capabilities': 'agent_capabilities.json'
        }

        self.logger.info(f"Knowledge Loader initialized with {len(self.datasets)} datasets")

    def get_dataset(self, name: str, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a dataset by name, using cache when available.

        Args:
            name: Dataset name (e.g., 'sector_performance', 'economic_cycles')
            force_reload: Force reload from disk, bypassing cache

        Returns:
            Dataset dictionary or None if not found
        """
        # Check if dataset exists
        if name not in self.datasets:
            self.logger.error(f"Dataset '{name}' not found in registry", available=list(self.datasets.keys()))
            return None

        # Check cache first (unless force reload)
        if not force_reload and self._is_cache_valid(name):
            self.logger.debug(f"Cache hit for dataset '{name}'")
            return self.cache[name]

        # Load from disk
        filepath = self.knowledge_dir / self.datasets[name]

        if not filepath.exists():
            self.logger.warning(f"Dataset file not found: {filepath}")
            return None

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Validate dataset
            if not self._validate_dataset(name, data):
                self.logger.error(f"Dataset '{name}' failed validation")
                return None

            # Cache the data
            self.cache[name] = data
            self.cache_timestamps[name] = datetime.now()

            self.logger.info(f"Loaded dataset '{name}' from {filepath}")
            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in dataset '{name}'", error=str(e), filepath=str(filepath))
            return None
        except Exception as e:
            self.logger.error(f"Error loading dataset '{name}'", error=str(e))
            return None

    def get_dataset_section(self, name: str, section: str, default: Any = None) -> Any:
        """
        Get a specific section from a dataset.

        Args:
            name: Dataset name
            section: Section key (supports dot notation, e.g., 'sectors.Technology')
            default: Default value if section not found

        Returns:
            Section data or default value
        """
        data = self.get_dataset(name)
        if not data:
            return default

        # Navigate nested keys with dot notation
        keys = section.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def list_datasets(self) -> List[str]:
        """Get list of available dataset names"""
        return list(self.datasets.keys())

    def get_dataset_info(self, name: str) -> Dict[str, Any]:
        """
        Get metadata about a dataset.

        Args:
            name: Dataset name

        Returns:
            Dictionary with metadata (exists, cached, last_loaded, file_size, etc.)
        """
        if name not in self.datasets:
            return {'exists': False, 'error': 'Dataset not found in registry'}

        filepath = self.knowledge_dir / self.datasets[name]
        info = {
            'name': name,
            'filename': self.datasets[name],
            'filepath': str(filepath),
            'exists': filepath.exists(),
            'cached': name in self.cache,
            'cache_valid': self._is_cache_valid(name)
        }

        if filepath.exists():
            stat = filepath.stat()
            info['file_size'] = stat.st_size
            info['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        if name in self.cache_timestamps:
            info['last_loaded'] = self.cache_timestamps[name].isoformat()
            info['cache_age_seconds'] = (datetime.now() - self.cache_timestamps[name]).total_seconds()

        return info

    def reload_all(self) -> Dict[str, bool]:
        """
        Reload all datasets from disk.

        Returns:
            Dictionary mapping dataset names to success status
        """
        results = {}
        for name in self.datasets.keys():
            data = self.get_dataset(name, force_reload=True)
            results[name] = data is not None

        loaded = sum(1 for success in results.values() if success)
        self.logger.info(f"Reloaded {loaded}/{len(results)} datasets")

        return results

    def clear_cache(self, name: Optional[str] = None):
        """
        Clear the cache.

        Args:
            name: Specific dataset to clear, or None to clear all
        """
        if name:
            if name in self.cache:
                del self.cache[name]
                del self.cache_timestamps[name]
                self.logger.debug(f"Cleared cache for '{name}'")
        else:
            self.cache.clear()
            self.cache_timestamps.clear()
            self.logger.info("Cleared all cached datasets")

    def get_stale_datasets(self) -> List[str]:
        """
        Get list of datasets that are cached but stale (older than TTL).

        Returns:
            List of stale dataset names
        """
        stale = []
        now = datetime.now()

        for name, timestamp in self.cache_timestamps.items():
            if now - timestamp > self.cache_ttl:
                stale.append(name)

        return stale

    def _is_cache_valid(self, name: str) -> bool:
        """Check if cached data is still valid"""
        if name not in self.cache:
            return False

        if name not in self.cache_timestamps:
            return False

        age = datetime.now() - self.cache_timestamps[name]
        return age < self.cache_ttl

    def _validate_dataset(self, name: str, data: Dict[str, Any]) -> bool:
        """
        Validate dataset structure and required fields.

        Args:
            name: Dataset name
            data: Dataset data

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            self.logger.error(f"Dataset '{name}' is not a dictionary")
            return False

        # Dataset-specific validation
        validators = {
            'sector_performance': self._validate_sector_performance,
            'economic_cycles': self._validate_economic_cycles,
            'sp500_companies': self._validate_sp500_companies,
            'sector_correlations': self._validate_sector_correlations,
            'company_database': self._validate_company_database
        }

        validator = validators.get(name)
        if validator:
            return validator(data)

        # Generic validation - just check it's not empty
        return len(data) > 0

    def _validate_sector_performance(self, data: Dict) -> bool:
        """Validate sector performance dataset"""
        return 'sectors' in data and isinstance(data['sectors'], dict)

    def _validate_economic_cycles(self, data: Dict) -> bool:
        """Validate economic cycles dataset"""
        return 'economic_cycles' in data or 'current_assessment' in data

    def _validate_sp500_companies(self, data: Dict) -> bool:
        """Validate S&P 500 companies dataset"""
        return 'sp500_companies' in data or any(key in data for key in ['Technology', 'Healthcare', 'Financials'])

    def _validate_sector_correlations(self, data: Dict) -> bool:
        """Validate sector correlations dataset"""
        return 'sector_correlations' in data or 'correlation_matrix' in data

    def _validate_company_database(self, data: Dict) -> bool:
        """Validate company database"""
        return 'companies' in data and 'aliases_to_symbol' in data


# Global singleton instance
_loader_instance = None


def get_knowledge_loader(knowledge_dir: str = 'dawsos/storage/knowledge') -> KnowledgeLoader:
    """
    Get or create the global knowledge loader instance.

    Args:
        knowledge_dir: Directory containing knowledge files

    Returns:
        KnowledgeLoader singleton
    """
    global _loader_instance

    if _loader_instance is None:
        _loader_instance = KnowledgeLoader(knowledge_dir)

    return _loader_instance


def load_dataset(name: str, force_reload: bool = False) -> Optional[Dict[str, Any]]:
    """
    Convenience function to load a dataset.

    Args:
        name: Dataset name
        force_reload: Force reload from disk

    Returns:
        Dataset dictionary or None
    """
    loader = get_knowledge_loader()
    return loader.get_dataset(name, force_reload)
