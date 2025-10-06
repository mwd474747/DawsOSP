"""Crypto capability - Cryptocurrency data integration"""
import urllib.request
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

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
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                if coin_id in data:
                    return {
                        'symbol': symbol,
                        'price': data[coin_id]['usd'],
                        'change_24h': data[coin_id].get('usd_24h_change', 0)
                    }
        except urllib.error.URLError as e:
            if hasattr(e, 'reason') and 'timed out' in str(e.reason):
                logger.warning(f"CoinGecko API timeout for {symbol}")
            else:
                logger.warning(f"CoinGecko API request failed for {symbol}: {e}")
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"CoinGecko response parsing failed for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching crypto price for {symbol}: {e}", exc_info=True)

        return {'symbol': symbol, 'error': 'Could not fetch price'}