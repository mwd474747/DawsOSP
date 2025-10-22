"""
OpenBB Configuration Manager
Ensures proper API setup and provider configuration for OpenBB Platform v4
"""

import os
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

class OpenBBConfig:
    """Manages OpenBB API configuration and provider setup"""
    
    # Provider mappings for OpenBB v4
    PROVIDER_CONFIG = {
        'fmp': {
            'env_key': 'FMP_API_KEY',
            'endpoints': ['equity', 'fundamentals', 'calendar', 'news'],
            'tier': 'premium',
            'rate_limit': 250  # requests per minute for free tier
        },
        'fred': {
            'env_key': 'FRED_API_KEY', 
            'endpoints': ['economy', 'treasury', 'rates'],
            'tier': 'free',
            'rate_limit': 120
        },
        'polygon': {
            'env_key': 'POLYGON_API_KEY',
            'endpoints': ['equity', 'options', 'forex', 'crypto'],
            'tier': 'premium',
            'rate_limit': 5  # free tier
        },
        'alpha_vantage': {
            'env_key': 'ALPHA_VANTAGE_API_KEY',
            'endpoints': ['equity', 'forex', 'crypto', 'technical'],
            'tier': 'freemium',
            'rate_limit': 5  # per minute
        },
        'finnhub': {
            'env_key': 'FINNHUB_API_KEY',
            'endpoints': ['equity', 'news', 'sentiment'],
            'tier': 'freemium',
            'rate_limit': 60
        },
        'newsapi': {
            'env_key': 'NEWSAPI_KEY',
            'endpoints': ['news'],
            'tier': 'free',
            'rate_limit': 500  # per day
        },
        'yfinance': {
            'env_key': None,  # No API key needed
            'endpoints': ['equity', 'options', 'fundamentals'],
            'tier': 'free',
            'rate_limit': None
        },
        'intrinio': {
            'env_key': 'INTRINIO_API_KEY',
            'endpoints': ['equity', 'options', 'fundamentals', 'economic'],
            'tier': 'premium',
            'rate_limit': 100
        },
        'quandl': {
            'env_key': 'QUANDL_API_KEY',
            'endpoints': ['futures', 'commodities', 'economic'],
            'tier': 'premium',
            'rate_limit': 50
        },
        'benzinga': {
            'env_key': 'BENZINGA_API_KEY',
            'endpoints': ['news', 'sentiment', 'ratings'],
            'tier': 'premium',
            'rate_limit': 250
        }
    }
    
    @classmethod
    def get_configured_providers(cls) -> Dict[str, Dict]:
        """Get all configured providers with their API keys"""
        configured = {}
        
        for provider, config in cls.PROVIDER_CONFIG.items():
            if config['env_key']:
                api_key = os.getenv(config['env_key'])
                if api_key:
                    configured[provider] = {
                        'api_key': api_key,
                        'endpoints': config['endpoints'],
                        'tier': config['tier'],
                        'rate_limit': config['rate_limit']
                    }
            elif provider == 'yfinance':
                # yfinance doesn't need API key
                configured[provider] = {
                    'api_key': None,
                    'endpoints': config['endpoints'],
                    'tier': config['tier'],
                    'rate_limit': config['rate_limit']
                }
        
        return configured
    
    @classmethod
    def get_provider_hierarchy(cls) -> Dict[str, List[str]]:
        """Get optimal provider hierarchy for different data types"""
        configured = cls.get_configured_providers()
        
        # Build hierarchy based on available providers and their capabilities
        hierarchy = {
            'equity': [],
            'fundamentals': [],
            'options': [],
            'economy': [],
            'news': [],
            'technical': [],
            'sentiment': []
        }
        
        # Premium providers first, then freemium, then free
        for tier in ['premium', 'freemium', 'free']:
            for provider, config in configured.items():
                if config['tier'] == tier:
                    for endpoint in config['endpoints']:
                        if endpoint in hierarchy:
                            hierarchy[endpoint].append(provider)
        
        # Always add yfinance as fallback for equity data
        if 'yfinance' not in hierarchy['equity']:
            hierarchy['equity'].append('yfinance')
            
        return hierarchy
    
    @classmethod
    def setup_openbb_credentials(cls) -> tuple[bool, str]:
        """
        Setup OpenBB with all available credentials
        Returns: (success, message)
        """
        try:
            from openbb import obb
            
            configured_count = 0
            configured_providers = []
            
            # Set up each configured provider
            for provider, config in cls.get_configured_providers().items():
                if config['api_key']:
                    # Map provider names to OpenBB credential attributes
                    credential_map = {
                        'fmp': 'fmp_api_key',
                        'fred': 'fred_api_key',
                        'polygon': 'polygon_api_key',
                        'alpha_vantage': 'alpha_vantage_api_key',
                        'finnhub': 'finnhub_api_key',
                        'newsapi': 'newsapi_api_key',
                        'intrinio': 'intrinio_api_key',
                        'quandl': 'quandl_api_key',
                        'benzinga': 'benzinga_api_key'
                    }
                    
                    if provider in credential_map:
                        try:
                            setattr(obb.user.credentials, credential_map[provider], config['api_key'])
                            configured_count += 1
                            configured_providers.append(provider.upper())
                        except Exception as e:
                            print(f"Warning: Could not set {provider} credentials: {e}")
            
            if configured_count > 0:
                message = f"OpenBB configured with {configured_count} providers: {', '.join(configured_providers)}"
                return True, message
            else:
                return False, "No API providers configured. Using free data sources only."
                
        except ImportError:
            return False, "OpenBB not installed. Please install with: pip install openbb"
        except Exception as e:
            return False, f"Error configuring OpenBB: {str(e)}"
    
    @classmethod
    def validate_provider(cls, provider: str, endpoint: str) -> bool:
        """Check if a provider supports a specific endpoint"""
        if provider not in cls.PROVIDER_CONFIG:
            return False
        return endpoint in cls.PROVIDER_CONFIG[provider]['endpoints']
    
    @classmethod
    def get_best_provider(cls, endpoint: str) -> Optional[str]:
        """Get the best available provider for an endpoint"""
        hierarchy = cls.get_provider_hierarchy()
        if endpoint in hierarchy and hierarchy[endpoint]:
            return hierarchy[endpoint][0]
        return 'yfinance'  # Default fallback
    
    @classmethod
    def save_config(cls, filepath: str = 'openbb_config.json'):
        """Save current configuration to file"""
        config = {
            'configured_providers': list(cls.get_configured_providers().keys()),
            'provider_hierarchy': cls.get_provider_hierarchy(),
            'timestamp': str(Path(__file__).stat().st_mtime)
        }
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    @classmethod
    def get_api_recommendations(cls) -> List[Dict[str, str]]:
        """Get recommendations for API configuration"""
        recommendations = []
        missing_providers = []
        
        for provider, config in cls.PROVIDER_CONFIG.items():
            if config['env_key'] and not os.getenv(config['env_key']):
                missing_providers.append(provider)
        
        # Priority recommendations
        if 'polygon' in missing_providers:
            recommendations.append({
                'provider': 'Polygon',
                'reason': 'Best for real-time stock data and options chains',
                'url': 'https://polygon.io/dashboard/signup',
                'tier': 'Free tier: 5 API calls/minute'
            })
        
        if 'alpha_vantage' in missing_providers:
            recommendations.append({
                'provider': 'Alpha Vantage',
                'reason': 'Great for technical indicators and forex data',
                'url': 'https://www.alphavantage.co/support/#api-key',
                'tier': 'Free tier: 5 API calls/minute, 500/day'
            })
        
        if 'finnhub' in missing_providers:
            recommendations.append({
                'provider': 'Finnhub',
                'reason': 'Excellent for market sentiment and company news',
                'url': 'https://finnhub.io/register',
                'tier': 'Free tier: 60 API calls/minute'
            })
        
        if 'benzinga' in missing_providers:
            recommendations.append({
                'provider': 'Benzinga',
                'reason': 'Professional news and analyst ratings',
                'url': 'https://www.benzinga.com/apis',
                'tier': 'Paid service with trial'
            })
        
        return recommendations
    
    @classmethod
    def test_provider(cls, provider: str) -> Dict[str, Any]:
        """Test a specific provider's connectivity"""
        from openbb import obb
        
        test_results = {
            'provider': provider,
            'status': 'unknown',
            'test_data': None,
            'error': None
        }
        
        try:
            # Test based on provider capabilities
            if provider == 'fmp':
                data = obb.equity.price.quote('AAPL', provider='fmp')
                test_results['status'] = 'connected' if data else 'error'
                test_results['test_data'] = 'AAPL quote retrieved'
                
            elif provider == 'fred':
                data = obb.economy.fred_series('GDP', provider='fred')
                test_results['status'] = 'connected' if data else 'error'
                test_results['test_data'] = 'GDP data retrieved'
                
            elif provider == 'yfinance':
                data = obb.equity.price.historical('SPY', provider='yfinance', period='1d')
                test_results['status'] = 'connected' if data else 'error'
                test_results['test_data'] = 'SPY data retrieved'
                
            else:
                test_results['status'] = 'untested'
                test_results['error'] = f"No test implemented for {provider}"
                
        except Exception as e:
            test_results['status'] = 'error'
            test_results['error'] = str(e)
        
        return test_results


# Quick configuration function
def configure_openbb():
    """Quick function to configure OpenBB with all available APIs"""
    config = OpenBBConfig()
    success, message = config.setup_openbb_credentials()
    
    print("\n" + "="*60)
    print("OPENBB CONFIGURATION STATUS")
    print("="*60)
    print(f"\n{message}\n")
    
    # Show provider hierarchy
    hierarchy = config.get_provider_hierarchy()
    print("Provider Hierarchy by Data Type:")
    for data_type, providers in hierarchy.items():
        if providers:
            print(f"  {data_type}: {' → '.join(providers)}")
    
    # Show recommendations
    recommendations = config.get_api_recommendations()
    if recommendations:
        print("\n" + "="*60)
        print("RECOMMENDED API ADDITIONS")
        print("="*60)
        for rec in recommendations:
            print(f"\n• {rec['provider']}")
            print(f"  Why: {rec['reason']}")
            print(f"  Get it: {rec['url']}")
            print(f"  Tier: {rec['tier']}")
    
    return success

if __name__ == "__main__":
    configure_openbb()