#!/usr/bin/env python3
"""
API Payload Normalizer - Normalize API responses to consistent format
Handles market data, economic indicators, and news from various sources
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class APIPayloadNormalizer:
    """Normalize API payloads from different sources to consistent internal format"""

    @staticmethod
    def normalize_stock_quote(raw_data: Any, source: str = 'fmp') -> Dict[str, Any]:
        """
        Normalize stock quote from FMP API

        Args:
            raw_data: Raw API response (list or dict)
            source: API source (fmp, yahoo, etc.)

        Returns:
            Normalized quote dict with standard fields
        """
        try:
            # FMP returns list with single dict
            if isinstance(raw_data, list) and len(raw_data) > 0:
                data = raw_data[0]
            elif isinstance(raw_data, dict):
                data = raw_data
            else:
                logger.warning(f"Unexpected stock quote format: {type(raw_data)}")
                return APIPayloadNormalizer._empty_quote()

            return {
                'symbol': data.get('symbol', 'UNKNOWN'),
                'price': float(data.get('price', 0)),
                'change': float(data.get('change', 0)),
                'change_percent': float(data.get('changesPercentage', 0)),
                'volume': int(data.get('volume', 0)),
                'market_cap': int(data.get('marketCap', 0)),
                'day_low': float(data.get('dayLow', 0)),
                'day_high': float(data.get('dayHigh', 0)),
                'year_low': float(data.get('yearLow', 0)),
                'year_high': float(data.get('yearHigh', 0)),
                'pe': float(data.get('pe', 0)) if data.get('pe') else None,
                'eps': float(data.get('eps', 0)) if data.get('eps') else None,
                'timestamp': data.get('timestamp', int(datetime.now().timestamp())),
                'exchange': data.get('exchange', 'UNKNOWN'),
                'source': source,
                'data_quality': 'high' if data.get('price') and data.get('volume') else 'low'
            }

        except Exception as e:
            logger.error(f"Error normalizing stock quote: {e}")
            return APIPayloadNormalizer._empty_quote()

    @staticmethod
    def normalize_economic_indicator(raw_data: Any, indicator_name: str, source: str = 'fred') -> Dict[str, Any]:
        """
        Normalize economic indicator from FRED API

        Args:
            raw_data: Raw API response
            indicator_name: Name of indicator (GDP, CPI, UNEMPLOYMENT, etc.)
            source: API source

        Returns:
            Normalized indicator dict
        """
        try:
            # FRED returns dict with 'observations' list
            if isinstance(raw_data, dict) and 'observations' in raw_data:
                observations = raw_data['observations']
                if not observations:
                    return APIPayloadNormalizer._empty_indicator(indicator_name)

                # Get most recent observation
                latest = observations[-1]

                # Calculate change if we have multiple observations
                change_value = None
                change_percent = None
                if len(observations) >= 2:
                    prev = observations[-2]
                    try:
                        current_val = float(latest.get('value', 0))
                        prev_val = float(prev.get('value', 0))
                        if prev_val != 0:
                            change_value = current_val - prev_val
                            change_percent = (change_value / prev_val) * 100
                    except (ValueError, TypeError):
                        pass

                return {
                    'indicator': indicator_name,
                    'value': latest.get('value'),
                    'date': latest.get('date'),
                    'change': change_value,
                    'change_percent': change_percent,
                    'unit': raw_data.get('units', 'Index'),
                    'frequency': raw_data.get('frequency', 'Monthly'),
                    'observations_count': len(observations),
                    'source': source,
                    'data_quality': 'high' if latest.get('value') != '.' else 'low'
                }

            # Handle single value response
            elif isinstance(raw_data, dict) and 'value' in raw_data:
                return {
                    'indicator': indicator_name,
                    'value': raw_data.get('value'),
                    'date': raw_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'change': None,
                    'change_percent': None,
                    'unit': 'Index',
                    'frequency': 'Unknown',
                    'observations_count': 1,
                    'source': source,
                    'data_quality': 'medium'
                }

            else:
                return APIPayloadNormalizer._empty_indicator(indicator_name)

        except Exception as e:
            logger.error(f"Error normalizing economic indicator {indicator_name}: {e}")
            return APIPayloadNormalizer._empty_indicator(indicator_name)

    @staticmethod
    def normalize_news_articles(raw_data: Any, source: str = 'newsapi') -> List[Dict[str, Any]]:
        """
        Normalize news articles from NewsAPI

        Args:
            raw_data: Raw API response
            source: API source

        Returns:
            List of normalized article dicts
        """
        try:
            articles = []

            # NewsAPI returns dict with 'articles' list
            if isinstance(raw_data, dict) and 'articles' in raw_data:
                raw_articles = raw_data['articles']
            elif isinstance(raw_data, list):
                raw_articles = raw_data
            else:
                return []

            for article in raw_articles:
                normalized = {
                    'title': article.get('title', 'No Title'),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', datetime.now().isoformat()),
                    'source_name': article.get('source', {}).get('name', 'Unknown') if isinstance(article.get('source'), dict) else 'Unknown',
                    'author': article.get('author', 'Unknown'),
                    'content': article.get('content', '')[:200] if article.get('content') else '',  # Truncate
                    'image_url': article.get('urlToImage', ''),
                    'sentiment': article.get('sentiment', 0),  # From our enhanced NewsCapability
                    'sentiment_label': article.get('sentiment_label', 'neutral'),
                    'quality_score': article.get('quality_score', 0.5),
                    'source': source,
                    'data_quality': 'high' if article.get('title') and article.get('url') else 'low'
                }
                articles.append(normalized)

            return articles

        except Exception as e:
            logger.error(f"Error normalizing news articles: {e}")
            return []

    @staticmethod
    def normalize_financial_ratios(raw_data: Any, symbol: str, source: str = 'fmp') -> Dict[str, Any]:
        """
        Normalize financial ratios from FMP API

        Args:
            raw_data: Raw API response
            symbol: Stock symbol
            source: API source

        Returns:
            Normalized ratios dict
        """
        try:
            # FMP returns list with single dict
            if isinstance(raw_data, list) and len(raw_data) > 0:
                data = raw_data[0]
            elif isinstance(raw_data, dict):
                data = raw_data
            else:
                return APIPayloadNormalizer._empty_ratios(symbol)

            return {
                'symbol': symbol,
                'pe_ratio': float(data.get('peRatio', 0)) if data.get('peRatio') else None,
                'price_to_book': float(data.get('priceToBookRatio', 0)) if data.get('priceToBookRatio') else None,
                'price_to_sales': float(data.get('priceToSalesRatio', 0)) if data.get('priceToSalesRatio') else None,
                'roe': float(data.get('returnOnEquity', 0)) if data.get('returnOnEquity') else None,
                'roa': float(data.get('returnOnAssets', 0)) if data.get('returnOnAssets') else None,
                'roic': float(data.get('returnOnCapitalEmployed', 0)) if data.get('returnOnCapitalEmployed') else None,
                'current_ratio': float(data.get('currentRatio', 0)) if data.get('currentRatio') else None,
                'quick_ratio': float(data.get('quickRatio', 0)) if data.get('quickRatio') else None,
                'debt_to_equity': float(data.get('debtToEquity', 0)) if data.get('debtToEquity') else None,
                'gross_margin': float(data.get('grossProfitMargin', 0)) if data.get('grossProfitMargin') else None,
                'operating_margin': float(data.get('operatingProfitMargin', 0)) if data.get('operatingProfitMargin') else None,
                'net_margin': float(data.get('netProfitMargin', 0)) if data.get('netProfitMargin') else None,
                'dividend_yield': float(data.get('dividendYield', 0)) if data.get('dividendYield') else None,
                'source': source,
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
                'data_quality': 'high' if data.get('peRatio') and data.get('roe') else 'medium'
            }

        except Exception as e:
            logger.error(f"Error normalizing financial ratios for {symbol}: {e}")
            return APIPayloadNormalizer._empty_ratios(symbol)

    @staticmethod
    def normalize_macro_context(economic_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Normalize multiple economic indicators into macro context

        Args:
            economic_data: Dict of normalized indicators keyed by name

        Returns:
            Macro context with derived insights
        """
        try:
            # Extract key indicators
            gdp = economic_data.get('GDP', {})
            cpi = economic_data.get('CPI', {})
            unemployment = economic_data.get('UNRATE', {})
            fed_rate = economic_data.get('FEDFUNDS', {})

            # Determine economic regime
            regime = 'transitional'
            if gdp.get('change_percent', 0) > 2 and cpi.get('change_percent', 0) < 3:
                regime = 'goldilocks'
            elif cpi.get('change_percent', 0) > 4:
                regime = 'overheating'
            elif gdp.get('change_percent', 0) < 0:
                regime = 'recession'
            elif gdp.get('change_percent', 0) < 1 and cpi.get('change_percent', 0) > 3:
                regime = 'stagflation'

            # Map regime to cycle
            cycle_mapping = {
                'goldilocks': ('Mid Expansion', 'Sustained Growth'),
                'overheating': ('Late Expansion', 'Overheating'),
                'stagflation': ('Late Expansion', 'Slowing Growth'),
                'recession': ('Contraction', 'Economic Decline'),
                'transitional': ('Uncertain', 'Mixed Signals')
            }

            short_cycle, short_phase = cycle_mapping.get(regime, ('Data Pending', 'Analysis Required'))

            return {
                'regime': regime,
                'short_cycle_position': short_cycle,
                'short_cycle_phase': short_phase,
                'gdp_growth': gdp.get('change_percent'),
                'inflation_rate': cpi.get('change_percent'),
                'unemployment_rate': unemployment.get('value'),
                'fed_funds_rate': fed_rate.get('value'),
                'credit_growth': cpi.get('change_percent'),  # Proxy
                'indicators_available': len(economic_data),
                'data_quality': 'high' if len(economic_data) >= 4 else 'medium',
                'last_updated': max([ind.get('date', '1900-01-01') for ind in economic_data.values()] or ['1900-01-01'])
            }

        except Exception as e:
            logger.error(f"Error normalizing macro context: {e}")
            return {
                'regime': 'error',
                'short_cycle_position': 'Data Error',
                'short_cycle_phase': 'Unable to determine',
                'data_quality': 'low',
                'error': str(e)
            }

    # Helper methods for empty responses
    @staticmethod
    def _empty_quote() -> Dict[str, Any]:
        """Return empty quote structure"""
        return {
            'symbol': 'UNKNOWN',
            'price': 0,
            'change': 0,
            'change_percent': 0,
            'volume': 0,
            'market_cap': 0,
            'data_quality': 'none',
            'error': 'No data available'
        }

    @staticmethod
    def _empty_indicator(indicator_name: str) -> Dict[str, Any]:
        """Return empty indicator structure"""
        return {
            'indicator': indicator_name,
            'value': None,
            'data_quality': 'none',
            'error': 'No data available'
        }

    @staticmethod
    def _empty_ratios(symbol: str) -> Dict[str, Any]:
        """Return empty ratios structure"""
        return {
            'symbol': symbol,
            'data_quality': 'none',
            'error': 'No data available'
        }


# Singleton instance
_normalizer = APIPayloadNormalizer()

def get_normalizer() -> APIPayloadNormalizer:
    """Get the singleton normalizer instance"""
    return _normalizer
