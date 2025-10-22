"""News Capability - NewsAPI integration for market news and sentiment analysis.

Phase 3.1: Comprehensive type hints added for improved type safety.
"""
import urllib.request
import urllib.parse
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from core.typing_compat import TypeAlias
from collections import deque
from core.credentials import get_credential_manager
from core.api_helper import APIHelper

# Type aliases for clarity
ArticleList: TypeAlias = List[Dict[str, Any]]
SentimentData: TypeAlias = Dict[str, Any]
TrendingTopics: TypeAlias = Dict[str, Any]
CacheStats: TypeAlias = Dict[str, Any]
RateLimitStatus: TypeAlias = Dict[str, Any]

# Set up logging
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for NewsAPI calls with daily limits and exponential backoff"""

    def __init__(self, max_requests_per_day: int = 100):
        """
        Initialize rate limiter for NewsAPI

        Args:
            max_requests_per_day: Maximum API requests per day
                                 Free tier: 100/day
                                 Developer: 250/day
                                 Business: 5000/day
        """
        self.max_requests = max_requests_per_day
        self.requests = deque()  # Stores (timestamp, request_info) tuples
        self.backoff_until = None
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    def _clean_old_requests(self) -> None:
        """Remove requests older than 24 hours."""
        now = time.time()
        twenty_four_hours_ago = now - 86400  # 24 hours in seconds

        while self.requests and self.requests[0] < twenty_four_hours_ago:
            self.requests.popleft()

    def get_requests_remaining(self) -> int:
        """Calculate requests remaining in current 24-hour window.

        Returns:
            Number of API requests remaining
        """
        self._clean_old_requests()
        return max(0, self.max_requests - len(self.requests))

    def get_usage_percentage(self) -> float:
        """Get current usage percentage.

        Returns:
            Percentage of daily quota used (0-100)
        """
        self._clean_old_requests()
        return (len(self.requests) / self.max_requests * 100) if self.max_requests > 0 else 0

    def wait_if_needed(self) -> None:
        """Wait if approaching rate limit or in backoff period.

        Raises:
            Exception: If daily rate limit is exceeded
        """
        now = time.time()

        # Check if we're in backoff period
        if self.backoff_until and now < self.backoff_until:
            wait_time = self.backoff_until - now
            logger.warning(f"Rate limit backoff: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            self.backoff_until = None
            return

        # Clean old requests
        self._clean_old_requests()

        # Check if we're approaching the daily limit
        usage_pct = self.get_usage_percentage()
        if usage_pct >= 80:
            logger.warning(f"Approaching daily rate limit: {usage_pct:.1f}% used "
                          f"({len(self.requests)}/{self.max_requests} requests)")

        # If at limit, calculate wait time until oldest request expires
        if len(self.requests) >= self.max_requests:
            oldest_request_time = self.requests[0]
            wait_time = 86400 - (now - oldest_request_time)

            if wait_time > 0:
                logger.error(f"Daily rate limit reached! Need to wait {wait_time/3600:.1f} hours. "
                           f"Consider upgrading API plan or using cached data.")
                # Don't actually wait 24 hours - raise error instead
                raise Exception(f"NewsAPI daily rate limit exceeded. Wait {wait_time/3600:.1f} hours or upgrade plan.")

        # Record this request
        self.requests.append(now)

    def set_backoff(self, retry_count: int = 1) -> None:
        """Set exponential backoff period.

        Args:
            retry_count: Number of retry attempts (default: 1)
        """
        backoff_seconds = min(2 ** retry_count, 60)  # Max 60 seconds
        self.backoff_until = time.time() + backoff_seconds
        logger.warning(f"Setting backoff for {backoff_seconds} seconds (retry {retry_count})")


class NewsCapability(APIHelper):
    """News and sentiment analysis capability with retry, fallback tracking, and caching"""

    # Spam/low-quality domains to filter out
    SPAM_DOMAINS: Set[str] = {
        'biztoc.com',
        'zerohedge.com',
        'benzinga.com',
        'fool.com',
        'seekingalpha.com',
        'investing.com',
        'insidermonkey.com',
        'gurufocus.com'
    }

    # Positive and negative sentiment keywords (expanded)
    POSITIVE_KEYWORDS: List[str] = [
        'surge', 'gain', 'profit', 'growth', 'rally', 'boom', 'strong', 'beat', 'exceed',
        'record', 'high', 'optimistic', 'bullish', 'success', 'breakthrough', 'soar',
        'rise', 'jump', 'advance', 'outperform', 'upgrade', 'innovative', 'expansion',
        'recover', 'rebound', 'accelerate', 'robust', 'thrive', 'prosper'
    ]

    NEGATIVE_KEYWORDS: List[str] = [
        'crash', 'fall', 'loss', 'decline', 'drop', 'weak', 'miss', 'concern', 'fear',
        'risk', 'low', 'pessimistic', 'bearish', 'failure', 'plunge', 'tumble', 'slump',
        'collapse', 'downgrade', 'warning', 'cut', 'slash', 'underperform', 'struggle',
        'recession', 'crisis', 'trouble', 'deteriorate', 'shrink'
    ]

    def __init__(self, api_key: Optional[str] = None, max_requests_per_day: int = 100) -> None:
        """
        Initialize NewsCapability

        Args:
            api_key: NewsAPI key (optional, will try to get from credentials)
            max_requests_per_day: Daily rate limit (default 100 for free tier)
        """
        # Initialize APIHelper mixin
        super().__init__()

        # Using NewsAPI (free tier available)
        # Get key at: https://newsapi.org/register
        if api_key:
            self.api_key: Optional[str] = api_key
        else:
            credentials = get_credential_manager()
            self.api_key: Optional[str] = credentials.get('NEWSAPI_KEY', required=False)

        self.base_url: str = 'https://newsapi.org/v2'
        self.cache: Dict[str, Dict[str, Any]] = {}

        # Configurable TTL by data type (in seconds)
        self.cache_ttl: Dict[str, int] = {
            'headlines': 3600,      # 1 hour - top headlines change frequently
            'search': 21600,        # 6 hours - search results are more stable
            'company': 21600,       # 6 hours - company-specific news
            'market': 21600         # 6 hours - market news
        }

        # Rate limiter (configurable for different plans)
        self.rate_limiter: RateLimiter = RateLimiter(max_requests_per_day=max_requests_per_day)

        # Cache statistics
        self.cache_stats: Dict[str, int] = {
            'hits': 0,
            'misses': 0,
            'expired_fallbacks': 0
        }

    def _get_from_cache(self, cache_key: str, data_type: str) -> Optional[Tuple[ArticleList, bool]]:
        """
        Get data from cache

        Args:
            cache_key: Cache key to lookup
            data_type: Type of data for TTL lookup ('headlines', 'search', etc.)

        Returns:
            Tuple of (data, is_fresh) or None if not in cache
        """
        if cache_key not in self.cache:
            self.cache_stats['misses'] += 1
            return None

        cached = self.cache[cache_key]
        age = (datetime.now() - cached['time']).total_seconds()
        ttl = self.cache_ttl.get(data_type, 3600)

        if age < ttl:
            self.cache_stats['hits'] += 1
            return (cached['data'], True)
        else:
            # Data exists but is expired
            return (cached['data'], False)

    def _update_cache(self, cache_key: str, data: ArticleList) -> None:
        """Update cache with new data.

        Args:
            cache_key: Key for cache storage
            data: Article list to cache
        """
        self.cache[cache_key] = {
            'data': data,
            'time': datetime.now()
        }

    def _fetch_url(self, url: str) -> Dict[str, Any]:
        """
        Internal method to fetch URL (wrapped by api_call for retry/fallback)

        Args:
            url: Full API URL

        Returns:
            Parsed JSON response

        Raises:
            Exception: On any error (handled by APIHelper)
        """
        # Check if API key is available
        if not self.api_key:
            raise ValueError("NewsAPI key not configured")

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        # Make request
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            logger.debug(f"API call successful: {url[:100]}...")
            return data

    def _make_api_call(self, url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Make API call with retry logic and fallback tracking (uses APIHelper)

        Args:
            url: Full API URL
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response or None on failure
        """
        return self.api_call(
            self._fetch_url,
            url,
            max_retries=max_retries,
            backoff=1.0,
            fallback=None,
            component_name='news_api'
        )

    def _is_spam_or_low_quality(self, article: Dict[str, Any]) -> bool:
        """
        Check if article is from spam/low-quality source

        Args:
            article: Article dictionary

        Returns:
            True if article should be filtered out
        """
        # Check if content is [Removed] (API limitation for older articles)
        description = article.get('description', '')
        content = article.get('content', '')
        if description == '[Removed]' or content == '[Removed]':
            return True

        # Check domain
        url = article.get('url', '')
        for spam_domain in self.SPAM_DOMAINS:
            if spam_domain in url.lower():
                return True

        # Check if source is None or empty
        source_name = article.get('source', {}).get('name', '')
        if not source_name or source_name.lower() == 'removed':
            return True

        return False

    def _filter_duplicates(self, articles: ArticleList) -> ArticleList:
        """
        Filter duplicate articles based on title similarity

        Args:
            articles: List of articles

        Returns:
            Filtered list without duplicates
        """
        seen_titles = set()
        filtered = []

        for article in articles:
            title = article.get('title', '').lower().strip()

            # Skip if we've seen a very similar title
            if title and title not in seen_titles:
                seen_titles.add(title)
                filtered.append(article)

        return filtered

    def _calculate_quality_score(self, article: Dict[str, Any]) -> float:
        """
        Calculate quality score for article (0-1)

        Args:
            article: Article dictionary

        Returns:
            Quality score between 0 and 1
        """
        score = 0.5  # Start with neutral score

        # High-quality sources
        source = article.get('source', {}).get('name', '').lower()
        quality_sources = ['reuters', 'bloomberg', 'wall street journal', 'financial times',
                          'cnbc', 'marketwatch', 'barron', 'yahoo finance', 'associated press']

        if any(q in source for q in quality_sources):
            score += 0.3

        # Has description and content
        if article.get('description') and article.get('description') != '[Removed]':
            score += 0.1

        if article.get('content') and article.get('content') != '[Removed]':
            score += 0.1

        # Ensure score is between 0 and 1
        return min(1.0, max(0.0, score))

    def get_headlines(self, query: Optional[str] = None, category: str = 'business') -> ArticleList:
        """
        Get top headlines

        Args:
            query: Optional search query
            category: Category (business, technology, etc.)

        Returns:
            List of articles with metadata
        """
        cache_key = f"headlines_{query}_{category}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'headlines')
        if cached and cached[1]:  # If data is fresh
            return cached[0]

        # Build URL
        endpoint = f"{self.base_url}/top-headlines"
        params = {
            'apiKey': self.api_key,
            'category': category,
            'country': 'us',
            'pageSize': 50  # Get more to account for filtering
        }

        if query:
            params['q'] = query

        url = f"{endpoint}?{urllib.parse.urlencode(params)}"

        # Make API call
        data = self._make_api_call(url)

        if data and data.get('articles'):
            articles = []
            for article in data.get('articles', []):
                # Filter spam/low-quality
                if self._is_spam_or_low_quality(article):
                    continue

                sentiment = self.analyze_sentiment(article)
                quality = self._calculate_quality_score(article)

                articles.append({
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'source': article.get('source', {}).get('name'),
                    'url': article.get('url'),
                    'published_at': article.get('publishedAt'),
                    'sentiment': sentiment['label'],
                    'sentiment_score': sentiment['score'],
                    'quality_score': quality
                })

            # Filter duplicates
            articles = self._filter_duplicates(articles)

            # Limit to 20 best quality articles
            articles = sorted(articles, key=lambda x: x['quality_score'], reverse=True)[:20]

            # Cache results
            self._update_cache(cache_key, articles)

            # VALIDATE with Pydantic before returning
            return self._validate_articles(articles, "headlines")

        # API call failed - try to return expired cache data
        if cached:
            logger.warning(f"API call failed, returning expired cache data for headlines")
            self.cache_stats['expired_fallbacks'] += 1
            result = [a.copy() for a in cached[0]]
            for article in result:
                article['_cached'] = True
                article['_warning'] = 'Using expired cached data due to API failure'
            return self._validate_articles(result, "cached headlines")

        return [{'error': 'No data available'}]
    
    def search_news(self, query: str, from_date: Optional[str] = None, days: int = 7) -> ArticleList:
        """
        Search news articles

        Args:
            query: Search query
            from_date: Start date (YYYY-MM-DD format)
            days: Number of days to search back (if from_date not specified)

        Returns:
            List of articles
        """
        if not from_date:
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cache_key = f"search_{query}_{from_date}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'search')
        if cached and cached[1]:  # If data is fresh
            return cached[0]

        endpoint = f"{self.base_url}/everything"
        params = {
            'apiKey': self.api_key,
            'q': query,
            'from': from_date,
            'sortBy': 'relevancy',
            'pageSize': 50,  # Get more to account for filtering
            'language': 'en'
        }

        url = f"{endpoint}?{urllib.parse.urlencode(params)}"

        # Make API call
        data = self._make_api_call(url)

        if data and data.get('articles'):
            articles = []
            for article in data.get('articles', []):
                # Filter spam/low-quality
                if self._is_spam_or_low_quality(article):
                    continue

                sentiment = self.analyze_sentiment(article)
                quality = self._calculate_quality_score(article)

                articles.append({
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'source': article.get('source', {}).get('name'),
                    'url': article.get('url'),
                    'published_at': article.get('publishedAt'),
                    'sentiment': sentiment['label'],
                    'sentiment_score': sentiment['score'],
                    'quality_score': quality
                })

            # Filter duplicates
            articles = self._filter_duplicates(articles)

            # Limit to 20 best quality articles
            articles = sorted(articles, key=lambda x: x['quality_score'], reverse=True)[:20]

            # Cache results
            self._update_cache(cache_key, articles)
            return articles

        # API call failed - try to return expired cache data
        if cached:
            logger.warning(f"API call failed, returning expired cache data for search: {query}")
            self.cache_stats['expired_fallbacks'] += 1
            result = [a.copy() for a in cached[0]]
            for article in result:
                article['_cached'] = True
                article['_warning'] = 'Using expired cached data due to API failure'
            return result

        return [{'error': 'No data available'}]

    def analyze_sentiment(self, article: Dict[str, Any]) -> SentimentData:
        """
        Enhanced sentiment analysis with score

        Args:
            article: Article dictionary

        Returns:
            Dict with 'score' (-1 to +1) and 'label' (positive/negative/neutral)
        """
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()

        # Count positive and negative words
        positive_count = sum(1 for word in self.POSITIVE_KEYWORDS if word in text)
        negative_count = sum(1 for word in self.NEGATIVE_KEYWORDS if word in text)

        # Calculate total for normalization
        total = positive_count + negative_count

        # Calculate sentiment score (-1 to +1)
        if total == 0:
            score = 0.0
            label = 'neutral'
        else:
            score = (positive_count - negative_count) / total

            if score > 0.2:
                label = 'positive'
            elif score < -0.2:
                label = 'negative'
            else:
                label = 'neutral'

        return {
            'score': round(score, 2),
            'label': label,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def get_company_news(self, symbol: str, days: int = 7) -> ArticleList:
        """
        Get company-specific news

        Args:
            symbol: Stock symbol (e.g., 'TSLA', 'AAPL')
            days: Number of days to look back

        Returns:
            List of articles about the company
        """
        cache_key = f"company_{symbol}_{days}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'company')
        if cached and cached[1]:
            return cached[0]

        # Search for company news
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return self.search_news(query=symbol, from_date=from_date, days=days)

    def get_market_news(self, category: str = 'business', days: int = 7) -> ArticleList:
        """
        Get market or sector-wide news

        Args:
            category: Category (business, technology, etc.)
            days: Number of days to look back

        Returns:
            List of market news articles
        """
        cache_key = f"market_{category}_{days}"

        # Check cache
        cached = self._get_from_cache(cache_key, 'market')
        if cached and cached[1]:
            return cached[0]

        # Get headlines
        return self.get_headlines(category=category)

    def extract_key_events(self, articles: ArticleList) -> List[Dict[str, Any]]:
        """
        Extract key events from articles and create timeline

        Args:
            articles: List of articles

        Returns:
            List of key events sorted by date
        """
        events = []

        for article in articles:
            # Skip if no date
            if not article.get('published_at'):
                continue

            # Consider high-impact events based on sentiment and quality
            sentiment_score = article.get('sentiment_score', 0)
            quality_score = article.get('quality_score', 0)

            # High impact if strong sentiment and high quality
            impact_score = abs(sentiment_score) * quality_score

            if impact_score > 0.3:  # Threshold for significance
                events.append({
                    'date': article['published_at'],
                    'title': article.get('title'),
                    'source': article.get('source'),
                    'sentiment': article.get('sentiment'),
                    'impact_score': round(impact_score, 2),
                    'url': article.get('url')
                })

        # Sort by date (newest first)
        events = sorted(events, key=lambda x: x['date'], reverse=True)

        return events

    def get_trending_topics(self, days: int = 7) -> TrendingTopics:
        """
        Get trending topics from recent news

        Args:
            days: Number of days to analyze

        Returns:
            Dict with topic frequencies and top articles
        """
        # Get recent market news
        articles = self.get_market_news(days=days)

        # Simple keyword extraction
        topic_counts = {}
        topic_articles = {}

        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()

            # Key financial topics
            topics = ['earnings', 'merger', 'acquisition', 'ipo', 'dividend', 'stock split',
                     'layoff', 'hiring', 'partnership', 'regulation', 'innovation',
                     'revenue', 'profit', 'loss', 'expansion', 'bankruptcy']

            for topic in topics:
                if topic in text:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

                    # Store sample article
                    if topic not in topic_articles:
                        topic_articles[topic] = {
                            'title': article.get('title'),
                            'source': article.get('source'),
                            'url': article.get('url')
                        }

        # Sort by frequency
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            'trending_topics': [
                {
                    'topic': topic,
                    'count': count,
                    'sample_article': topic_articles.get(topic)
                }
                for topic, count in sorted_topics[:10]
            ],
            'analysis_period_days': days,
            'total_articles_analyzed': len(articles),
            'timestamp': datetime.now().isoformat()
        }

    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            Dictionary with cache hit rate and usage metrics
        """
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'cache_hit_rate': f"{hit_rate:.1f}%",
            'expired_fallbacks': self.cache_stats['expired_fallbacks'],
            'cached_items': len(self.cache)
        }

    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get rate limit status.

        Returns:
            Dictionary with rate limit usage information
        """
        return {
            'requests_remaining': self.rate_limiter.get_requests_remaining(),
            'usage_percentage': f"{self.rate_limiter.get_usage_percentage():.1f}%",
            'max_requests_per_day': self.rate_limiter.max_requests,
            'requests_used': len(self.rate_limiter.requests)
        }

    def get_market_sentiment(self) -> SentimentData:
        """Get overall market sentiment.

        Returns:
            Dictionary with aggregated sentiment analysis
        """
        # Get headlines for market analysis
        headlines = self.get_headlines(category='business')

        sentiment_counts = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }

        total_score = 0.0

        for article in headlines:
            if 'sentiment' in article:
                sentiment_counts[article['sentiment']] += 1

            if 'sentiment_score' in article:
                total_score += article['sentiment_score']

        total = sum(sentiment_counts.values()) or 1
        avg_score = total_score / total if total > 0 else 0

        return {
            'overall': max(sentiment_counts, key=sentiment_counts.get),
            'average_score': round(avg_score, 2),
            'distribution': {
                'positive': sentiment_counts['positive'] / total,
                'negative': sentiment_counts['negative'] / total,
                'neutral': sentiment_counts['neutral'] / total
            },
            'article_count': total,
            'timestamp': datetime.now().isoformat()
        }

    def search(self, query: str, limit: int = 10, from_date: Optional[str] = None) -> ArticleList:
        """Search news articles (alias for search_news with limit).

        Args:
            query: Search query string
            limit: Maximum number of results to return
            from_date: Optional start date in YYYY-MM-DD format

        Returns:
            List of matching articles (limited to specified count)
        """
        articles = self.search_news(query, from_date)
        if isinstance(articles, list) and len(articles) > 0 and 'error' not in articles[0]:
            return articles[:limit]
        return articles

    def _validate_articles(self, articles: ArticleList, context: str = "articles") -> ArticleList:
        """Validate news articles with Pydantic before returning.

        Args:
            articles: List of article dictionaries
            context: Context for error messages

        Returns:
            Validated articles list or error list with validation details
        """
        try:
            from models.news import NewsArticle
            from pydantic import ValidationError as PydanticValidationError

            validated_articles = []
            errors = []

            for i, article_data in enumerate(articles):
                # Skip if this is an error dict
                if 'error' in article_data:
                    return articles

                try:
                    validated = NewsArticle(**article_data)
                    validated_articles.append(validated.model_dump())
                except PydanticValidationError as e:
                    logger.warning(f"Article {i} validation failed: {e}")
                    errors.append({
                        'article_index': i,
                        'title': article_data.get('title', 'Unknown'),
                        'validation_errors': [
                            {'field': '.'.join(str(loc) for loc in err['loc']), 'message': err['msg']}
                            for err in e.errors()
                        ]
                    })

            if validated_articles:
                logger.info(f"✓ Validated {len(validated_articles)}/{len(articles)} {context}")
                if errors:
                    logger.warning(f"⚠ {len(errors)} articles failed validation and were filtered")
                return validated_articles
            else:
                logger.error(f"❌ All {context} failed validation")
                return [{
                    'error': f'All {context} failed validation',
                    'validation_errors': errors
                }]

        except ImportError as e:
            logger.warning(f"Pydantic models not available, skipping validation: {e}")
            return articles
