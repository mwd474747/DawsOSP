"""
API Status Checker - Verify all financial data API connections
Ensures OpenBB and all providers are properly integrated
"""

import os
import requests
from typing import Dict, Any, List
import json
from datetime import datetime

class APIStatusChecker:
    """Check and verify all API connections for Trinity 3.0"""
    
    def __init__(self):
        self.api_status = {}
        
    def check_all_apis(self) -> Dict[str, Any]:
        """Check status of all configured APIs"""
        
        # Check FRED API
        self.api_status['FRED'] = self._check_fred_api()
        
        # Check FMP API
        self.api_status['FMP'] = self._check_fmp_api()
        
        # Check NewsAPI
        self.api_status['NewsAPI'] = self._check_newsapi()
        
        # Check OpenBB connectivity
        self.api_status['OpenBB'] = self._check_openbb()
        
        # Check yfinance (free provider)
        self.api_status['YFinance'] = self._check_yfinance()
        
        # Check database
        self.api_status['Database'] = self._check_database()
        
        return self.api_status
    
    def _check_fred_api(self) -> Dict[str, Any]:
        """Verify FRED API connection"""
        api_key = os.getenv('FRED_API_KEY')
        if not api_key:
            return {'status': 'Not Configured', 'message': 'FRED_API_KEY not set'}
        
        try:
            url = "https://api.stlouisfed.org/fred/series"
            params = {
                'series_id': 'GDP',
                'api_key': api_key,
                'file_type': 'json'
            }
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                return {
                    'status': 'Connected',
                    'message': 'FRED API working',
                    'test_data': 'GDP series accessible'
                }
            else:
                return {
                    'status': 'Error',
                    'message': f'FRED API returned {response.status_code}'
                }
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}
    
    def _check_fmp_api(self) -> Dict[str, Any]:
        """Verify FMP (Financial Modeling Prep) API"""
        api_key = os.getenv('FMP_API_KEY')
        if not api_key:
            return {'status': 'Not Configured', 'message': 'FMP_API_KEY not set'}
        
        try:
            url = f"https://financialmodelingprep.com/api/v3/quote/AAPL"
            params = {'apikey': api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        'status': 'Connected',
                        'message': 'FMP API working',
                        'test_data': f'AAPL price: ${data[0].get("price", "N/A")}'
                    }
            return {
                'status': 'Error',
                'message': f'FMP API returned {response.status_code}'
            }
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}
    
    def _check_newsapi(self) -> Dict[str, Any]:
        """Verify NewsAPI connection"""
        api_key = os.getenv('NEWSAPI_KEY')
        if not api_key:
            return {'status': 'Not Configured', 'message': 'NEWSAPI_KEY not set'}
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            headers = {'X-Api-Key': api_key}
            params = {'category': 'business', 'country': 'us', 'pageSize': 1}
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'Connected',
                    'message': 'NewsAPI working',
                    'test_data': f'{data.get("totalResults", 0)} articles available'
                }
            return {
                'status': 'Error',
                'message': f'NewsAPI returned {response.status_code}'
            }
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}
    
    def _check_openbb(self) -> Dict[str, Any]:
        """Check OpenBB platform integration"""
        try:
            from openbb import obb
            
            # Check if OpenBB is importable and initialized
            configured_providers = []
            if hasattr(obb, 'user') and hasattr(obb.user, 'credentials'):
                # Check which providers are configured
                creds = obb.user.credentials
                if creds.fmp_api_key:
                    configured_providers.append('FMP')
                if creds.fred_api_key:
                    configured_providers.append('FRED')
                if creds.newsapi_api_key:
                    configured_providers.append('NewsAPI')
                    
            return {
                'status': 'Connected',
                'message': 'OpenBB Platform v4 initialized',
                'configured_providers': configured_providers,
                'version': 'v4.x'
            }
        except ImportError:
            return {'status': 'Error', 'message': 'OpenBB not installed'}
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}
    
    def _check_yfinance(self) -> Dict[str, Any]:
        """Check yfinance (free backup provider)"""
        try:
            import yfinance as yf
            
            # Test with a simple ticker
            ticker = yf.Ticker("SPY")
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                return {
                    'status': 'Connected',
                    'message': 'yfinance working (free backup)',
                    'test_data': f'SPY price: ${info.get("regularMarketPrice", "N/A")}'
                }
            return {
                'status': 'Partial',
                'message': 'yfinance connected but limited data'
            }
        except ImportError:
            return {'status': 'Not Installed', 'message': 'yfinance not installed'}
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connection"""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return {'status': 'Not Configured', 'message': 'DATABASE_URL not set'}
        
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            # Parse database URL
            parsed = urlparse(db_url)
            
            # Test connection
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'Connected',
                'message': 'PostgreSQL database connected',
                'test_data': f'{count} predictions stored'
            }
        except ImportError:
            return {'status': 'Error', 'message': 'psycopg2 not installed'}
        except Exception as e:
            return {'status': 'Error', 'message': str(e)}
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on API status"""
        recommendations = []
        
        if self.api_status.get('FRED', {}).get('status') != 'Connected':
            recommendations.append("Configure FRED_API_KEY for economic data (free at https://fred.stlouisfed.org/docs/api/api_key.html)")
            
        if self.api_status.get('FMP', {}).get('status') != 'Connected':
            recommendations.append("Configure FMP_API_KEY for real-time stock data (free tier at https://site.financialmodelingprep.com/developer/docs)")
            
        if self.api_status.get('NewsAPI', {}).get('status') != 'Connected':
            recommendations.append("Configure NEWSAPI_KEY for news sentiment (free at https://newsapi.org/register)")
            
        if self.api_status.get('YFinance', {}).get('status') == 'Not Installed':
            recommendations.append("Install yfinance for free backup data: pip install yfinance")
            
        if not recommendations:
            recommendations.append("All APIs properly configured! Trinity 3.0 has full data access.")
            
        return recommendations
    
    def print_status_report(self):
        """Print a formatted status report"""
        print("\n" + "="*60)
        print("TRINITY 3.0 API STATUS REPORT")
        print("="*60 + "\n")
        
        for api_name, status in self.api_status.items():
            status_emoji = "✅" if status['status'] == 'Connected' else "⚠️" if status['status'] == 'Partial' else "❌"
            print(f"{status_emoji} {api_name}: {status['status']}")
            print(f"   {status['message']}")
            if 'test_data' in status:
                print(f"   Test: {status['test_data']}")
            if 'configured_providers' in status:
                print(f"   Providers: {', '.join(status['configured_providers'])}")
            print()
        
        print("="*60)
        print("RECOMMENDATIONS:")
        print("="*60)
        for rec in self.get_recommendations():
            print(f"• {rec}")
        print()
    
    def to_json(self) -> str:
        """Export status as JSON"""
        return json.dumps({
            'timestamp': datetime.now().isoformat(),
            'api_status': self.api_status,
            'recommendations': self.get_recommendations()
        }, indent=2)


# Quick test function
def check_apis():
    """Quick function to check all API connections"""
    checker = APIStatusChecker()
    checker.check_all_apis()
    checker.print_status_report()
    return checker.api_status


if __name__ == "__main__":
    check_apis()