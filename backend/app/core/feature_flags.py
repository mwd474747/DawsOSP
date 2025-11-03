"""
DawsOS Feature Flag System

Purpose: Enable gradual rollout of agent consolidation and other features
Created: 2025-11-03
Priority: P1 (Critical for safe production deployment)

Features:
    - JSON-based flag configuration  
    - Boolean and percentage rollout flags
    - Deterministic rollout based on user_id hash
    - Runtime reloading without restart
    - Backward compatible (system works with flags disabled)
    - Thread-safe operations
    
Usage:
    flags = FeatureFlags()
    if flags.is_enabled("agent_consolidation.optimizer_to_financial", {"user_id": "123"}):
        # Use new consolidated agent
    else:
        # Use existing separate agent
"""

import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


class FeatureFlags:
    """
    Simple feature flag system for safe production rollouts.
    
    Supports:
    - Boolean on/off flags
    - Percentage-based gradual rollouts
    - User/context-based targeting
    - Runtime reloading
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize feature flags.
        
        Args:
            config_path: Path to JSON config file. Defaults to backend/config/feature_flags.json
        """
        if config_path is None:
            # Default to backend/config/feature_flags.json
            current_dir = Path(__file__).parent.parent.parent  # backend/
            config_path = current_dir / "config" / "feature_flags.json"
        
        self.config_path = Path(config_path)
        self._flags: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._last_loaded: Optional[datetime] = None
        self._auto_reload_interval = timedelta(minutes=1)  # Auto-reload every minute
        
        # Load initial configuration
        self.reload()
        
        # Log available flags
        self._log_available_flags()
    
    def _log_available_flags(self):
        """Log all available feature flags for visibility."""
        if not self._flags:
            logger.info("No feature flags configured")
            return
            
        flag_count = 0
        for category, flags in self._flags.items():
            if isinstance(flags, dict):
                for flag_name, config in flags.items():
                    if isinstance(config, dict):
                        enabled = config.get("enabled", False)
                        percentage = config.get("rollout_percentage", 0)
                        logger.info(
                            f"Feature flag: {category}.{flag_name} - "
                            f"enabled={enabled}, rollout={percentage}%"
                        )
                        flag_count += 1
        
        logger.info(f"Loaded {flag_count} feature flags from {self.config_path}")
    
    def reload(self) -> bool:
        """
        Reload flags from configuration file.
        
        Returns:
            True if reload successful, False otherwise
        """
        with self._lock:
            try:
                # Check if file exists
                if not self.config_path.exists():
                    logger.warning(f"Feature flag config not found: {self.config_path}")
                    self._flags = {}
                    self._last_loaded = datetime.now()
                    return False
                
                # Load JSON configuration
                with open(self.config_path, 'r') as f:
                    new_flags = json.load(f)
                
                # Validate structure
                if not isinstance(new_flags, dict):
                    logger.error(f"Invalid flag config: expected dict, got {type(new_flags)}")
                    return False
                
                # Update flags
                self._flags = new_flags
                self._last_loaded = datetime.now()
                
                logger.info(f"Reloaded feature flags from {self.config_path}")
                return True
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse feature flags JSON: {e}")
                return False
            except Exception as e:
                logger.error(f"Failed to reload feature flags: {e}")
                return False
    
    def _auto_reload_if_needed(self):
        """Auto-reload configuration if interval has passed."""
        if self._last_loaded is None:
            return
        
        elapsed = datetime.now() - self._last_loaded
        if elapsed > self._auto_reload_interval:
            self.reload()
    
    def _get_flag_config(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific flag.
        
        Args:
            flag_name: Dot-separated flag path (e.g., "agent_consolidation.optimizer_to_financial")
            
        Returns:
            Flag configuration dict or None if not found
        """
        # Auto-reload if needed
        self._auto_reload_if_needed()
        
        with self._lock:
            parts = flag_name.split('.')
            current = self._flags
            
            for part in parts:
                if not isinstance(current, dict):
                    return None
                current = current.get(part)
                if current is None:
                    return None
            
            # Ensure we return a dict with expected structure
            if isinstance(current, dict):
                return current
            elif isinstance(current, bool):
                # Handle simple boolean flags
                return {"enabled": current, "rollout_percentage": 100 if current else 0}
            else:
                return None
    
    def is_enabled(self, flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        For percentage rollouts, uses deterministic hashing based on user_id or request_id.
        
        Args:
            flag_name: Dot-separated flag path (e.g., "agent_consolidation.optimizer_to_financial")
            context: Optional context dict containing user_id, request_id, etc.
            
        Returns:
            True if feature is enabled for this context
        """
        config = self._get_flag_config(flag_name)
        
        # If flag doesn't exist, default to disabled
        if config is None:
            return False
        
        # Check if globally disabled
        if not config.get("enabled", False):
            return False
        
        # Check percentage rollout
        rollout_percentage = config.get("rollout_percentage", 0)
        
        # If 0%, disabled
        if rollout_percentage <= 0:
            return False
        
        # If 100%, enabled for all
        if rollout_percentage >= 100:
            return True
        
        # Calculate if this context falls within rollout percentage
        # Use deterministic hashing for consistent behavior
        if context:
            # Try to get a stable identifier
            identifier = (
                context.get("user_id") or 
                context.get("portfolio_id") or 
                context.get("request_id") or 
                "default"
            )
            
            # Create hash of flag + identifier for deterministic rollout
            hash_input = f"{flag_name}:{identifier}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            
            # Map to 0-100 range
            rollout_value = hash_value % 100
            
            # Check if within rollout percentage
            return rollout_value < rollout_percentage
        
        # No context provided, use random rollout
        import random
        return random.randint(0, 99) < rollout_percentage
    
    def get_percentage(self, flag_name: str) -> int:
        """
        Get rollout percentage for a flag.
        
        Args:
            flag_name: Dot-separated flag path
            
        Returns:
            Rollout percentage (0-100)
        """
        config = self._get_flag_config(flag_name)
        
        if config is None:
            return 0
        
        if not config.get("enabled", False):
            return 0
        
        return config.get("rollout_percentage", 0)
    
    def get_all_flags(self) -> Dict[str, Any]:
        """
        Get all configured flags.
        
        Returns:
            Dict of all flags and their configurations
        """
        with self._lock:
            return self._flags.copy()
    
    def list_flags(self, category: Optional[str] = None) -> Set[str]:
        """
        List all flag names, optionally filtered by category.
        
        Args:
            category: Optional category to filter by (e.g., "agent_consolidation")
            
        Returns:
            Set of flag names
        """
        flags = set()
        
        with self._lock:
            if category:
                # List flags in specific category
                cat_flags = self._flags.get(category, {})
                if isinstance(cat_flags, dict):
                    for flag_name in cat_flags.keys():
                        flags.add(f"{category}.{flag_name}")
            else:
                # List all flags
                for cat_name, cat_flags in self._flags.items():
                    if isinstance(cat_flags, dict):
                        for flag_name in cat_flags.keys():
                            flags.add(f"{cat_name}.{flag_name}")
        
        return flags
    
    def get_flag_info(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a flag.
        
        Args:
            flag_name: Dot-separated flag path
            
        Returns:
            Dict with flag info or None if not found
        """
        config = self._get_flag_config(flag_name)
        
        if config is None:
            return None
        
        return {
            "name": flag_name,
            "enabled": config.get("enabled", False),
            "rollout_percentage": config.get("rollout_percentage", 0),
            "description": config.get("description", ""),
            "created_at": config.get("created_at"),
            "updated_at": config.get("updated_at"),
        }


# Global singleton instance
_feature_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """
    Get or create singleton feature flags instance.
    
    Returns:
        FeatureFlags instance
    """
    global _feature_flags
    
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    
    return _feature_flags


def is_feature_enabled(flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Convenience function to check if a feature is enabled.
    
    Args:
        flag_name: Dot-separated flag path
        context: Optional context for percentage rollouts
        
    Returns:
        True if feature is enabled
    """
    return get_feature_flags().is_enabled(flag_name, context)