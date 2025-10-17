"""
Session state caching utilities for Streamlit.

Provides TTL-based caching with automatic expiration and refresh.
This is a NEW utility module that doesn't modify any existing code.
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Tuple, Callable, Any, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Unified session state caching for predictions and data fetching.

    This class provides a centralized caching mechanism that can be adopted
    incrementally without breaking existing code.
    """

    @staticmethod
    def get_cached_data(
        cache_key: str,
        ttl_seconds: int,
        fetch_fn: Callable[[], Any],
        force_refresh: bool = False,
        spinner_msg: str = "Loading..."
    ) -> Tuple[Any, Optional[datetime]]:
        """
        Get data from cache or fetch if expired.

        Args:
            cache_key: Unique key for this cached data
            ttl_seconds: Time-to-live in seconds
            fetch_fn: Function to call if cache miss/expired
            force_refresh: If True, bypass cache
            spinner_msg: Message to show during fetch

        Returns:
            Tuple of (data, timestamp)

        Example:
            data, ts = CacheManager.get_cached_data(
                'my_forecast',
                3600,
                lambda: generate_forecast(),
                force_refresh=st.button("Refresh")
            )
        """
        data_key = f'{cache_key}_data'
        timestamp_key = f'{cache_key}_timestamp'

        # Initialize if not exists
        if data_key not in st.session_state:
            st.session_state[data_key] = None
            st.session_state[timestamp_key] = None
            logger.debug(f"CacheManager: Initialized new cache key: {cache_key}")

        # Check if refresh needed
        needs_refresh = (
            st.session_state[data_key] is None or
            force_refresh or
            (st.session_state[timestamp_key] and
             (datetime.now() - st.session_state[timestamp_key]).total_seconds() > ttl_seconds)
        )

        if needs_refresh:
            try:
                with st.spinner(spinner_msg):
                    logger.info(f"CacheManager: Fetching data for {cache_key}")
                    st.session_state[data_key] = fetch_fn()
                    st.session_state[timestamp_key] = datetime.now()
                    logger.info(f"CacheManager: Successfully cached {cache_key}")
            except Exception as e:
                logger.error(f"CacheManager: Error fetching {cache_key}: {e}")
                # Don't overwrite existing cache on error
                if st.session_state[data_key] is None:
                    st.session_state[data_key] = {'error': str(e)}

        return st.session_state[data_key], st.session_state[timestamp_key]

    @staticmethod
    def clear_cache(cache_key: str) -> None:
        """
        Clear specific cache entry.

        Args:
            cache_key: Key to clear
        """
        data_key = f'{cache_key}_data'
        timestamp_key = f'{cache_key}_timestamp'

        if data_key in st.session_state:
            del st.session_state[data_key]
            logger.debug(f"CacheManager: Cleared {data_key}")
        if timestamp_key in st.session_state:
            del st.session_state[timestamp_key]
            logger.debug(f"CacheManager: Cleared {timestamp_key}")

    @staticmethod
    def get_cache_age(cache_key: str) -> Optional[float]:
        """
        Get age of cache in seconds.

        Args:
            cache_key: Key to check

        Returns:
            Age in seconds, or None if not cached
        """
        timestamp_key = f'{cache_key}_timestamp'

        if timestamp_key in st.session_state and st.session_state[timestamp_key]:
            age = (datetime.now() - st.session_state[timestamp_key]).total_seconds()
            return age

        return None
