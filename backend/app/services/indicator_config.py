"""
Indicator Configuration Manager

Purpose: Manage macro economic indicator configuration from JSON
Created: 2025-11-02
Priority: P1

Features:
    - Load indicator configuration from JSON
    - Provide fallback mechanism (real data > configured defaults)
    - Handle indicator aliases and scaling
    - Validate indicator ranges
    - Support scenario overrides
    - Cache configuration for performance

Usage:
    manager = IndicatorConfigManager()
    
    # Get indicator value with metadata
    indicator = manager.get_indicator("gdp_growth")
    
    # Get all indicators for a category
    stdc_indicators = manager.get_category_indicators("stdc")
    
    # Apply scenario overrides
    recession_indicators = manager.get_scenario_indicators("recession_scenario")
    
    # Validate indicator value
    is_valid = manager.validate_indicator("inflation", 0.03)
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from decimal import Decimal
import os

logger = logging.getLogger("DawsOS.IndicatorConfig")


@dataclass
class IndicatorMetadata:
    """Metadata for a single indicator."""
    
    value: float
    unit: str
    display_unit: str
    range: Dict[str, float]
    source: str
    confidence: str
    last_updated: str
    notes: str
    aliases: List[str] = field(default_factory=list)
    calculation: Optional[str] = None


@dataclass
class IndicatorCategory:
    """Category of indicators."""
    
    name: str
    description: str
    indicators: Dict[str, IndicatorMetadata]


class IndicatorConfigManager:
    """
    Manages macro economic indicator configuration.
    
    Provides centralized access to indicator values, metadata, and validation.
    """
    
    # Default configuration file path
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "macro_indicators_defaults.json"
    
    # Confidence level priorities (higher = more trusted)
    CONFIDENCE_PRIORITY = {
        "high": 4,
        "medium": 3,
        "low": 2,
        "default": 1
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file (uses default if None)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Optional[Dict[str, Any]] = None
        self._indicators_cache: Optional[Dict[str, IndicatorMetadata]] = None
        self._alias_map: Optional[Dict[str, str]] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Configuration file not found: {self.config_path}")
                self._config = {}
                return
                
            with open(self.config_path, 'r') as f:
                self._config = json.load(f)
                
            # Build indicators cache and alias map
            self._build_caches()
            
            logger.info(f"Loaded indicator configuration from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = {}
    
    def _build_caches(self) -> None:
        """Build internal caches for efficient access."""
        self._indicators_cache = {}
        self._alias_map = {}
        
        if not self._config or "categories" not in self._config:
            return
            
        for category_key, category_data in self._config["categories"].items():
            if "indicators" not in category_data:
                continue
                
            for indicator_key, indicator_data in category_data["indicators"].items():
                # Create metadata object
                metadata = IndicatorMetadata(
                    value=float(indicator_data.get("value", 0.0)),
                    unit=indicator_data.get("unit", "unknown"),
                    display_unit=indicator_data.get("display_unit", "unknown"),
                    range=indicator_data.get("range", {"min": -1e6, "max": 1e6}),
                    source=indicator_data.get("source", "Unknown"),
                    confidence=indicator_data.get("confidence", "default"),
                    last_updated=indicator_data.get("last_updated", "Unknown"),
                    notes=indicator_data.get("notes", ""),
                    aliases=indicator_data.get("aliases", []),
                    calculation=indicator_data.get("calculation")
                )
                
                # Store in cache
                self._indicators_cache[indicator_key] = metadata
                
                # Build alias map
                for alias in metadata.aliases:
                    self._alias_map[alias] = indicator_key
    
    def get_indicator(
        self, 
        key: str,
        with_metadata: bool = False
    ) -> Union[float, IndicatorMetadata]:
        """
        Get indicator value or metadata.
        
        Args:
            key: Indicator key or alias
            with_metadata: If True, return full metadata; if False, just value
            
        Returns:
            Indicator value (float) or metadata (IndicatorMetadata)
        """
        # Resolve alias if needed
        actual_key = self._alias_map.get(key, key)
        
        if self._indicators_cache and actual_key in self._indicators_cache:
            metadata = self._indicators_cache[actual_key]
            return metadata if with_metadata else metadata.value
            
        # Return default if not found
        logger.warning(f"Indicator not found in configuration: {key}")
        if with_metadata:
            return IndicatorMetadata(
                value=0.0,
                unit="unknown",
                display_unit="unknown",
                range={"min": -1e6, "max": 1e6},
                source="Default",
                confidence="default",
                last_updated="Unknown",
                notes=f"Default value for {key}",
                aliases=[]
            )
        else:
            return 0.0
    
    def get_all_indicators(
        self,
        include_aliases: bool = False
    ) -> Dict[str, float]:
        """
        Get all indicator values.
        
        Args:
            include_aliases: If True, include aliased keys in output
            
        Returns:
            Dictionary of indicator keys to values
        """
        result = {}
        
        if not self._indicators_cache:
            return result
            
        for key, metadata in self._indicators_cache.items():
            result[key] = metadata.value
            
            if include_aliases:
                for alias in metadata.aliases:
                    result[alias] = metadata.value
                    
        return result
    
    def get_category_indicators(
        self,
        category: str,
        include_aliases: bool = False
    ) -> Dict[str, float]:
        """
        Get all indicators for a specific category.
        
        Args:
            category: Category name (e.g., "stdc", "ltdc", "empire", "civil")
            include_aliases: If True, include aliased keys in output
            
        Returns:
            Dictionary of indicator keys to values
        """
        result = {}
        
        if not self._config or "categories" not in self._config:
            return result
            
        category_data = self._config["categories"].get(category)
        if not category_data or "indicators" not in category_data:
            logger.warning(f"Category not found: {category}")
            return result
            
        for indicator_key, indicator_data in category_data["indicators"].items():
            value = float(indicator_data.get("value", 0.0))
            result[indicator_key] = value
            
            if include_aliases:
                for alias in indicator_data.get("aliases", []):
                    result[alias] = value
                    
        return result
    
    def validate_indicator(
        self,
        key: str,
        value: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate an indicator value against configured ranges.
        
        Args:
            key: Indicator key or alias
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Resolve alias if needed
        actual_key = self._alias_map.get(key, key)
        
        if self._indicators_cache and actual_key in self._indicators_cache:
            metadata = self._indicators_cache[actual_key]
            
            # Check range
            if "min" in metadata.range and value < metadata.range["min"]:
                return False, f"Value {value} below minimum {metadata.range['min']} for {key}"
                
            if "max" in metadata.range and value > metadata.range["max"]:
                return False, f"Value {value} above maximum {metadata.range['max']} for {key}"
                
            # Check unit-specific validations
            if metadata.unit == "coefficient" and (value < 0 or value > 1):
                return False, f"Coefficient {key} must be between 0 and 1, got {value}"
                
            if metadata.unit == "index" and metadata.display_unit == "score":
                if value < 0 or value > 1:
                    return False, f"Score {key} must be between 0 and 1, got {value}"
                    
        return True, None
    
    def get_scenario_indicators(
        self,
        scenario_name: str,
        base_indicators: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Get indicators with scenario overrides applied.
        
        Args:
            scenario_name: Name of the scenario to apply
            base_indicators: Base indicators to override (uses defaults if None)
            
        Returns:
            Dictionary of indicator keys to values with scenario applied
        """
        # Start with base indicators or defaults
        if base_indicators:
            result = base_indicators.copy()
        else:
            result = self.get_all_indicators(include_aliases=True)
            
        # Apply scenario overrides
        if self._config and "scenarios" in self._config:
            scenarios = self._config["scenarios"].get("scenarios", {})
            scenario = scenarios.get(scenario_name)
            
            if scenario and "overrides" in scenario:
                for key, value in scenario["overrides"].items():
                    result[key] = float(value)
                    
                    # Also update aliases
                    if key in self._indicators_cache:
                        for alias in self._indicators_cache[key].aliases:
                            result[alias] = float(value)
            else:
                logger.warning(f"Scenario not found: {scenario_name}")
                
        return result
    
    def get_scaling_rule(self, indicator_key: str) -> Optional[Dict[str, str]]:
        """
        Get scaling rule for an indicator.
        
        Args:
            indicator_key: Indicator key
            
        Returns:
            Scaling rule dictionary or None
        """
        if self._config and "scaling_rules" in self._config:
            for rule in self._config["scaling_rules"].get("rules", []):
                if rule.get("indicator") == indicator_key:
                    return rule
                    
        return None
    
    def merge_with_database_values(
        self,
        db_values: Dict[str, float],
        prefer_db: bool = True
    ) -> Dict[str, float]:
        """
        Merge configuration values with database values.
        
        Args:
            db_values: Values from database
            prefer_db: If True, prefer DB values over config when both exist
            
        Returns:
            Merged dictionary with appropriate values and aliases
        """
        # Start with all configured values (including aliases)
        result = self.get_all_indicators(include_aliases=True)
        
        # Process database values
        if prefer_db:
            # Database values override configuration
            for key, value in db_values.items():
                result[key] = value
                
                # Update aliases if this is a primary key
                if key in self._indicators_cache:
                    for alias in self._indicators_cache[key].aliases:
                        result[alias] = value
        else:
            # Configuration values take precedence, but add any missing DB values
            for key, value in db_values.items():
                if key not in result:
                    result[key] = value
                    
        # Apply any calculated fields
        if "real_interest_rate" in result:
            if "interest_rate" in result and "inflation" in result:
                result["real_interest_rate"] = result["interest_rate"] - result["inflation"]
                
        return result
    
    def get_confidence_priority(self, key: str) -> int:
        """
        Get confidence priority for an indicator.
        
        Higher values indicate more trusted data.
        
        Args:
            key: Indicator key or alias
            
        Returns:
            Priority value (1-4)
        """
        actual_key = self._alias_map.get(key, key)
        
        if self._indicators_cache and actual_key in self._indicators_cache:
            metadata = self._indicators_cache[actual_key]
            return self.CONFIDENCE_PRIORITY.get(metadata.confidence, 1)
            
        return 1
    
    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        Get summary of configuration metadata.
        
        Returns:
            Summary dictionary with version, counts, quality metrics
        """
        if not self._config:
            return {}
            
        summary = {
            "version": self._config.get("version", "Unknown"),
            "last_updated": self._config.get("last_updated", "Unknown"),
            "total_indicators": len(self._indicators_cache) if self._indicators_cache else 0,
            "categories": [],
            "confidence_breakdown": {
                "high": 0,
                "medium": 0,
                "low": 0,
                "default": 0
            },
            "data_freshness": {}
        }
        
        if self._config and "categories" in self._config:
            for category_key, category_data in self._config["categories"].items():
                indicator_count = len(category_data.get("indicators", {}))
                summary["categories"].append({
                    "key": category_key,
                    "name": category_data.get("name", category_key),
                    "indicator_count": indicator_count
                })
                
        if self._indicators_cache:
            for key, metadata in self._indicators_cache.items():
                # Count confidence levels
                confidence = metadata.confidence
                if confidence in summary["confidence_breakdown"]:
                    summary["confidence_breakdown"][confidence] += 1
                    
                # Track data freshness
                if metadata.last_updated != "Unknown":
                    summary["data_freshness"][key] = metadata.last_updated
                    
        return summary


# ============================================================================
# Singleton Pattern - REMOVED
# ============================================================================
#
# DEPRECATED: Singleton pattern removed as part of Phase 2 refactoring.
# Use IndicatorConfigManager() directly instead.
#
# Migration:
#     OLD: manager = get_config_manager()
#     NEW: manager = IndicatorConfigManager()  # Stateless, no parameters needed
#     OR:  manager = container.resolve("indicator_config")
#