#!/usr/bin/env python3
"""
Fallback Tracker - Centralized fallback event tracking for UI transparency

Tracks when the system uses cached/fallback data instead of live API responses,
enabling transparent UI warnings and API health monitoring.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from core.logger import get_logger

logger = get_logger('FallbackTracker')


class FallbackTracker:
    """Track when system uses cached/fallback data instead of live APIs"""

    def __init__(self):
        """Initialize fallback tracker"""
        self.fallback_events: List[Dict[str, Any]] = []
        self.stats = {
            'llm_fallbacks': 0,
            'api_fallbacks': 0,
            'cache_hits': 0,
            'total_fallbacks': 0
        }

    def mark_fallback(
        self,
        component: str,
        reason: str,
        data_type: str = 'cached'
    ) -> Dict[str, Any]:
        """
        Mark a fallback event and return UI metadata

        Args:
            component: Component using fallback (e.g., 'llm', 'fred_api', 'claude_agent')
            reason: Why fallback was used (e.g., 'api_key_missing', 'api_error', 'rate_limit')
            data_type: Type of fallback ('cached', 'default', 'stale')

        Returns:
            Dict with UI display metadata including:
            - source: 'fallback'
            - fallback_reason: reason string
            - data_type: type of fallback
            - ui_message: user-friendly message
            - timestamp: when fallback occurred
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'reason': reason,
            'data_type': data_type
        }

        self.fallback_events.append(event)

        # Update stats
        self.stats['total_fallbacks'] += 1
        if component == 'llm':
            self.stats['llm_fallbacks'] += 1
        elif 'api' in component:
            self.stats['api_fallbacks'] += 1
        elif data_type == 'cached':
            self.stats['cache_hits'] += 1

        logger.warning(
            f"Fallback triggered: {component} - {reason} - using {data_type} data"
        )

        return {
            'source': 'fallback',
            'fallback_reason': reason,
            'data_type': data_type,
            'ui_message': self._generate_ui_message(component, reason, data_type),
            'timestamp': event['timestamp']
        }

    def _generate_ui_message(
        self,
        component: str,
        reason: str,
        data_type: str
    ) -> str:
        """
        Generate user-friendly UI message for fallback event

        Args:
            component: Component that triggered fallback
            reason: Reason for fallback
            data_type: Type of fallback data

        Returns:
            User-friendly message string with emoji
        """
        # Reason-specific messages
        messages = {
            'api_key_missing': f"⚠️ API key not configured - using {data_type} data",
            'api_error': f"⚠️ API temporarily unavailable - using {data_type} data",
            'rate_limit': f"⏱️ Rate limit reached - using {data_type} data",
            'timeout': f"⏱️ Request timeout - using {data_type} data",
            'connection_error': f"🔌 Connection error - using {data_type} data",
            'quota_exceeded': f"📊 API quota exceeded - using {data_type} data"
        }

        # Use reason-specific message or generic fallback
        return messages.get(
            reason,
            f"⚠️ Using {data_type} data for {component}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get fallback statistics for monitoring

        Returns:
            Dict with:
            - total_fallbacks: Total number of fallback events
            - llm_fallbacks: Number of LLM fallbacks
            - api_fallbacks: Number of API fallbacks
            - cache_hits: Number of cache hits
            - recent_events: Last 10 fallback events
        """
        return {
            **self.stats,
            'recent_events': self.fallback_events[-10:]
        }

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent fallback events

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent fallback events (most recent first)
        """
        return list(reversed(self.fallback_events[-limit:]))

    def clear_stats(self) -> None:
        """Clear all fallback statistics and events"""
        self.fallback_events.clear()
        self.stats = {
            'llm_fallbacks': 0,
            'api_fallbacks': 0,
            'cache_hits': 0,
            'total_fallbacks': 0
        }
        logger.info("Fallback statistics cleared")

    def get_component_stats(self, component: str) -> Dict[str, Any]:
        """
        Get statistics for a specific component

        Args:
            component: Component name to get stats for

        Returns:
            Dict with component-specific statistics
        """
        component_events = [
            e for e in self.fallback_events
            if e['component'] == component
        ]

        return {
            'component': component,
            'total_events': len(component_events),
            'recent_events': component_events[-10:],
            'reasons': self._count_reasons(component_events)
        }

    def _count_reasons(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count fallback reasons in event list

        Args:
            events: List of fallback events

        Returns:
            Dict mapping reason to count
        """
        reasons = {}
        for event in events:
            reason = event.get('reason', 'unknown')
            reasons[reason] = reasons.get(reason, 0) + 1
        return reasons


# Global singleton instance
_fallback_tracker: Optional[FallbackTracker] = None


def get_fallback_tracker() -> FallbackTracker:
    """
    Get global fallback tracker instance (singleton pattern)

    Returns:
        Global FallbackTracker instance
    """
    global _fallback_tracker
    if _fallback_tracker is None:
        _fallback_tracker = FallbackTracker()
        logger.info("Fallback tracker initialized")
    return _fallback_tracker
