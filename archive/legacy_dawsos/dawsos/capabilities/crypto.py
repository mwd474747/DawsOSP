"""Crypto capability - Cryptocurrency data integration.

Phase 3.1: Comprehensive type hints added for improved type safety.
"""
import urllib.request
import json
import logging
from typing import Dict, Any, Optional
from core.typing_compat import TypeAlias

# Type aliases for clarity
CryptoPrice: TypeAlias = Dict[str, Any]
CoinID: TypeAlias = str

logger = logging.getLogger(__name__)

class CryptoCapability:
    """Cryptocurrency market data"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Crypto Capability with CoinGecko API.

        Args:
            api_key: Optional API key for CoinGecko (not required for free tier)
        """
        # Can use CoinGecko (free tier available)
        self.base_url: str = 'https://api.coingecko.com/api/v3'
        self.cache: Dict[str, Any] = {}

    def get_price(self, symbol: str) -> CryptoPrice:
        """Get crypto price.

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'SOL')

        Returns:
            Dictionary with price and 24h change data
        """
        # Map common symbols
        coin_map: Dict[str, CoinID] = {
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
                    result = {
                        'symbol': symbol,
                        'price': data[coin_id]['usd'],
                        'change_24h': data[coin_id].get('usd_24h_change', 0)
                    }
                    # VALIDATE response with Pydantic
                    return self._validate_crypto_price(result)
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
    def _validate_crypto_price(self, price_data: dict) -> dict:
        """Validate crypto price data with Pydantic before returning.

        Args:
            price_data: Raw crypto price data

        Returns:
            Validated price dict or error dict with validation details
        """
        try:
            from models.crypto import CryptoPrice
            from pydantic import ValidationError as PydanticValidationError

            try:
                validated = CryptoPrice(**price_data)
                logger.info(f"✓ Validated crypto price for {price_data.get('symbol', 'UNKNOWN')}")
                return validated.model_dump()
            except PydanticValidationError as e:
                logger.error(f"❌ Crypto price validation failed: {e}")
                return {
                    'symbol': price_data.get('symbol', 'UNKNOWN'),
                    'error': 'Price validation failed',
                    'validation_errors': [
                        {'field': '.'.join(str(loc) for loc in err['loc']), 'message': err['msg']}
                        for err in e.errors()
                    ]
                }
        except ImportError as e:
            logger.warning(f"Pydantic models not available, skipping validation: {e}")
            return price_data
