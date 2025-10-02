import urllib.request
import json
from datetime import datetime
from typing import Dict, List

class CryptoCapability:
    """Cryptocurrency market data capability"""
    
    def __init__(self):
        # Using CoinGecko API (free, no key needed for basic)
        self.base_url = 'https://api.coingecko.com/api/v3'
        self.cache = {}
        self.cache_ttl = 60  # 1 minute
    
    def get_price(self, coin_id: str = 'bitcoin', vs_currency: str = 'usd') -> Dict:
        """Get cryptocurrency price"""
        cache_key = f"{coin_id}_{vs_currency}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now().timestamp() - cached['time'] < self.cache_ttl:
                return cached['data']
        
        url = f"{self.base_url}/simple/price?ids={coin_id}&vs_currencies={vs_currency}&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                coin_data = data.get(coin_id, {})
                result = {
                    'coin': coin_id,
                    'price': coin_data.get(vs_currency, 0),
                    'market_cap': coin_data.get(f'{vs_currency}_market_cap', 0),
                    'volume_24h': coin_data.get(f'{vs_currency}_24h_vol', 0),
                    'change_24h': coin_data.get(f'{vs_currency}_24h_change', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update cache
                self.cache[cache_key] = {
                    'data': result,
                    'time': datetime.now().timestamp()
                }
                
                return result
                
        except Exception as e:
            return {'coin': coin_id, 'error': str(e)}
    
    def get_top_coins(self, limit: int = 20) -> List[Dict]:
        """Get top cryptocurrencies by market cap"""
        url = f"{self.base_url}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&page=1"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                coins = []
                for coin in data:
                    coins.append({
                        'id': coin.get('id'),
                        'symbol': coin.get('symbol'),
                        'name': coin.get('name'),
                        'price': coin.get('current_price'),
                        'market_cap': coin.get('market_cap'),
                        'volume_24h': coin.get('total_volume'),
                        'change_24h': coin.get('price_change_percentage_24h'),
                        'rank': coin.get('market_cap_rank')
                    })
                
                return coins
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_defi_data(self) -> Dict:
        """Get DeFi market data"""
        url = f"{self.base_url}/global/decentralized_finance_defi"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                defi_data = data.get('data', {})
                return {
                    'defi_market_cap': defi_data.get('defi_market_cap', 0),
                    'eth_market_cap': defi_data.get('eth_market_cap', 0),
                    'defi_to_eth_ratio': defi_data.get('defi_to_eth_ratio', 0),
                    'trading_volume_24h': defi_data.get('trading_volume_24h', 0),
                    'defi_dominance': defi_data.get('defi_dominance', 0),
                    'top_coin': defi_data.get('top_coin_name', 'Unknown')
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def get_trending(self) -> List[str]:
        """Get trending cryptocurrencies"""
        url = f"{self.base_url}/search/trending"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                trending = []
                for coin in data.get('coins', []):
                    trending.append({
                        'id': coin.get('item', {}).get('id'),
                        'symbol': coin.get('item', {}).get('symbol'),
                        'name': coin.get('item', {}).get('name'),
                        'rank': coin.get('item', {}).get('market_cap_rank')
                    })
                
                return trending
                
        except Exception as e:
            return [{'error': str(e)}]