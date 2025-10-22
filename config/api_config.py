"""
Trinity API Configuration - Centralized API Settings
Per Integration Specialist recommendations

Centralizes all API keys, endpoints, and OpenBB provider configuration.
Merged functionality from openbb_config.py for unified API management.
"""
import os
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class APIConfig:
    """Centralized API configuration for Trinity with OpenBB provider management"""

    # Anthropic Claude API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

    # OpenBB Platform (Market Data)
    OPENBB_API_KEY = os.getenv('OPENBB_API_KEY')  # Optional for free tier
    OPENBB_TIMEOUT = int(os.getenv('OPENBB_TIMEOUT', '30'))

    # FRED (Economic Data)
    FRED_API_KEY = os.getenv('FRED_API_KEY')

    # FMP (Financial Modeling Prep) - PRIMARY MARKET DATA PROVIDER
    FMP_API_KEY = os.getenv('FMP_API_KEY')

    # NewsAPI
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')

    # Polygon (Options Data)
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

    # Additional OpenBB Providers
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
    BENZINGA_API_KEY = os.getenv('BENZINGA_API_KEY')
    INTRINIO_API_KEY = os.getenv('INTRINIO_API_KEY')

    # OpenBB Provider Configuration (merged from openbb_config.py)
    OPENBB_PROVIDERS = {
        'fmp': {
            'env_key': 'FMP_API_KEY',
            'credential_key': 'fmp_api_key',
            'endpoints': ['equity', 'fundamentals', 'calendar', 'news'],
            'tier': 'premium',
            'priority': 1  # HIGHEST PRIORITY
        },
        'fred': {
            'env_key': 'FRED_API_KEY',
            'credential_key': 'fred_api_key',
            'endpoints': ['economy', 'treasury', 'rates'],
            'tier': 'free',
            'priority': 2
        },
        'polygon': {
            'env_key': 'POLYGON_API_KEY',
            'credential_key': 'polygon_api_key',
            'endpoints': ['equity', 'options', 'forex', 'crypto'],
            'tier': 'premium',
            'priority': 3
        },
        'alpha_vantage': {
            'env_key': 'ALPHA_VANTAGE_API_KEY',
            'credential_key': 'alpha_vantage_api_key',
            'endpoints': ['equity', 'forex', 'crypto', 'technical'],
            'tier': 'freemium',
            'priority': 4
        },
        'finnhub': {
            'env_key': 'FINNHUB_API_KEY',
            'credential_key': 'finnhub_api_key',
            'endpoints': ['equity', 'news', 'sentiment'],
            'tier': 'freemium',
            'priority': 5
        },
        'newsapi': {
            'env_key': 'NEWSAPI_KEY',
            'credential_key': 'newsapi_api_key',
            'endpoints': ['news'],
            'tier': 'free',
            'priority': 6
        },
        'benzinga': {
            'env_key': 'BENZINGA_API_KEY',
            'credential_key': 'benzinga_api_key',
            'endpoints': ['news', 'sentiment', 'ratings'],
            'tier': 'premium',
            'priority': 7
        },
        'intrinio': {
            'env_key': 'INTRINIO_API_KEY',
            'credential_key': 'intrinio_api_key',
            'endpoints': ['equity', 'options', 'fundamentals', 'economic'],
            'tier': 'premium',
            'priority': 8
        },
        'yfinance': {
            'env_key': None,  # Free provider, no key needed
            'credential_key': None,
            'endpoints': ['equity', 'options', 'fundamentals'],
            'tier': 'free',
            'priority': 99  # Fallback
        }
    }
    
    @classmethod
    def validate(cls) -> Dict[str, bool]:
        """
        Validate API configuration.

        Returns:
            Dictionary of {api_name: is_configured}
        """
        return {
            'anthropic': bool(cls.ANTHROPIC_API_KEY),
            'openbb': True,  # Works with free tier
            'fred': bool(cls.FRED_API_KEY),
            'fmp': bool(cls.FMP_API_KEY),
            'news': bool(cls.NEWS_API_KEY),
            'polygon': bool(cls.POLYGON_API_KEY),
            'alpha_vantage': bool(cls.ALPHA_VANTAGE_API_KEY),
            'finnhub': bool(cls.FINNHUB_API_KEY),
            'benzinga': bool(cls.BENZINGA_API_KEY),
            'intrinio': bool(cls.INTRINIO_API_KEY)
        }

    @classmethod
    def get_status(cls) -> str:
        """Get API configuration status summary"""
        status = cls.validate()
        configured = [k for k, v in status.items() if v]
        return f"{len(configured)}/{len(status)} APIs configured: {', '.join(configured)}"

    @classmethod
    def log_status(cls):
        """Log API configuration status (NO EMOJIS - professional output)"""
        status = cls.validate()
        logger.info("API Configuration Status:")
        for api, configured in status.items():
            status_marker = "[OK]" if configured else "[--]"
            logger.info(f"  {status_marker} {api.upper()}: {'Configured' if configured else 'Not configured'}")

    @classmethod
    def check_required(cls) -> bool:
        """
        Check if required APIs are configured.

        Returns:
            True if all required APIs available
        """
        required = ['anthropic']  # Only Anthropic is strictly required
        status = cls.validate()
        missing = [api for api in required if not status[api]]

        if missing:
            logger.error(f"Missing required API keys: {', '.join(missing)}")
            return False
        return True

    # === OpenBB Provider Management (merged from openbb_config.py) ===

    @classmethod
    def get_configured_openbb_providers(cls) -> Dict[str, Dict]:
        """
        Get all configured OpenBB providers with their settings.

        Returns:
            Dict of {provider_name: {api_key, endpoints, tier, priority}}
        """
        configured = {}

        for provider, config in cls.OPENBB_PROVIDERS.items():
            if config['env_key']:
                api_key = os.getenv(config['env_key'])
                if api_key:
                    configured[provider] = {
                        'api_key': api_key,
                        'credential_key': config['credential_key'],
                        'endpoints': config['endpoints'],
                        'tier': config['tier'],
                        'priority': config['priority']
                    }
            elif provider == 'yfinance':
                # yfinance doesn't need API key
                configured[provider] = {
                    'api_key': None,
                    'credential_key': None,
                    'endpoints': config['endpoints'],
                    'tier': config['tier'],
                    'priority': config['priority']
                }

        return configured

    @classmethod
    def get_openbb_provider_hierarchy(cls) -> Dict[str, List[str]]:
        """
        Get OpenBB provider hierarchy for different data types.
        Providers are ordered by priority (FMP first for equity data).

        Returns:
            Dict of {data_type: [provider1, provider2, ...]}
        """
        configured = cls.get_configured_openbb_providers()

        # Build hierarchy based on available providers and their capabilities
        hierarchy = {
            'equity': [],
            'fundamentals': [],
            'options': [],
            'economy': [],
            'news': [],
            'technical': [],
            'sentiment': [],
            'forex': [],
            'crypto': []
        }

        # Sort providers by priority (FMP = 1, highest priority)
        sorted_providers = sorted(
            configured.items(),
            key=lambda x: x[1]['priority']
        )

        for provider, config in sorted_providers:
            for endpoint in config['endpoints']:
                if endpoint in hierarchy and provider not in hierarchy[endpoint]:
                    hierarchy[endpoint].append(provider)

        # Always add yfinance as fallback for equity data
        for data_type in ['equity', 'fundamentals', 'options']:
            if 'yfinance' not in hierarchy[data_type]:
                hierarchy[data_type].append('yfinance')

        return hierarchy

    @classmethod
    def setup_openbb_credentials(cls, obb) -> Tuple[bool, str]:
        """
        Setup OpenBB with all available credentials.

        Args:
            obb: OpenBB instance (from `from openbb import obb`)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            configured_count = 0
            configured_providers = []

            # Set up each configured provider
            for provider, config in cls.get_configured_openbb_providers().items():
                if config['api_key'] and config['credential_key']:
                    try:
                        setattr(obb.user.credentials, config['credential_key'], config['api_key'])
                        configured_count += 1
                        configured_providers.append(provider.upper())
                        logger.info(f"Configured OpenBB provider: {provider}")
                    except Exception as e:
                        logger.warning(f"Could not set {provider} credentials: {e}")

            if configured_count > 0:
                message = f"OpenBB configured with {configured_count} providers: {', '.join(configured_providers)}"
                logger.info(message)
                return True, message
            else:
                message = "No API providers configured. Using free data sources only."
                logger.warning(message)
                return False, message

        except Exception as e:
            message = f"Error configuring OpenBB: {str(e)}"
            logger.error(message)
            return False, message

    @classmethod
    def get_best_openbb_provider(cls, data_type: str) -> Optional[str]:
        """
        Get the best available provider for a data type.
        FMP is prioritized for equity data.

        Args:
            data_type: Type of data (equity, fundamentals, options, etc.)

        Returns:
            Provider name or 'yfinance' as fallback
        """
        hierarchy = cls.get_openbb_provider_hierarchy()
        if data_type in hierarchy and hierarchy[data_type]:
            return hierarchy[data_type][0]  # First = highest priority
        return 'yfinance'  # Default fallback

    @classmethod
    def test_fmp_connection(cls) -> Dict[str, any]:
        """
        Test FMP API connectivity via OpenBB.

        Returns:
            Dict with {status, test_data, error}
        """
        result = {
            'provider': 'fmp',
            'status': 'unknown',
            'test_data': None,
            'error': None
        }

        if not cls.FMP_API_KEY:
            result['status'] = 'not_configured'
            result['error'] = 'FMP_API_KEY not set'
            return result

        try:
            from openbb import obb

            # Test FMP with a simple quote
            data = obb.equity.price.quote('AAPL', provider='fmp')

            if data:
                result['status'] = 'connected'
                result['test_data'] = 'AAPL quote retrieved successfully'
            else:
                result['status'] = 'error'
                result['error'] = 'No data returned from FMP'

        except ImportError:
            result['status'] = 'error'
            result['error'] = 'OpenBB not installed'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    @classmethod
    def get_openbb_provider_summary(cls) -> Dict[str, any]:
        """
        Get comprehensive summary of OpenBB provider configuration.

        Returns:
            Dict with configured providers, hierarchy, and FMP status
        """
        configured = cls.get_configured_openbb_providers()
        hierarchy = cls.get_openbb_provider_hierarchy()

        return {
            'configured_providers': list(configured.keys()),
            'provider_count': len(configured),
            'fmp_configured': 'fmp' in configured,
            'fmp_priority': configured.get('fmp', {}).get('priority', None),
            'equity_hierarchy': hierarchy.get('equity', []),
            'default_equity_provider': hierarchy.get('equity', ['yfinance'])[0],
            'all_hierarchies': hierarchy
        }


# Auto-log status on import (NO EMOJIS - professional)
if __name__ != "__main__":
    APIConfig.log_status()
