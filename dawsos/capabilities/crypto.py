"""Crypto capability - Cryptocurrency data integration"""
import urllib.request
import json
from typing import Dict

class CryptoCapability:
    """Cryptocurrency market data"""

    def __init__(self, api_key: str = None):
        # Can use CoinGecko (free tier available)
        self.base_url = 'https://api.coingecko.com/api/v3'
        self.cache = {}

    def get_price(self, symbol: str) -> Dict:
        """Get crypto price"""
        # Map common symbols
        coin_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'DOGE': 'dogecoin'
        }

        coin_id = coin_map.get(symbol.upper(), symbol.lower())
        url = f"{self.base_url}/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                if coin_id in data:
                    return {
                        'symbol': symbol,
                        'price': data[coin_id]['usd'],
                        'change_24h': data[coin_id].get('usd_24h_change', 0)
                    }
        except:
            pass

        return {'symbol': symbol, 'error': 'Could not fetch price'}