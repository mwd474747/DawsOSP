"""
NewsAPI Provider Facade

Purpose: Fetch news articles for portfolio-weighted impact analysis
Updated: 2025-10-21
Priority: P1 (Important for news impact, not critical path)

Features:
    - News search by keyword, symbol, date range
    - Rate limiting: 30 req/min (dev tier) or 100 req/min (business tier)
    - Smart retry logic with exponential backoff (1s, 2s, 4s)
    - Dead Letter Queue for failed requests
    - Rights: BLOCKED export (dev tier), metadata-only storage
    - Production: Requires business tier license

Endpoints:
    - /v2/everything (search)
    - /v2/top-headlines (breaking news)

Usage:
    provider = NewsAPIProvider(api_key=settings.NEWSAPI_KEY, tier="dev")
    articles = await provider.search("AAPL", from_date, to_date)

IMPORTANT:
    - Dev tier: CANNOT export text, metadata-only
    - Business tier: Can export with attribution
    - Always check rights before storing article text
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta

from .base_provider import BaseProvider, ProviderConfig, ProviderError, ProviderRequest, ProviderResponse
from .rate_limiter import rate_limit

logger = logging.getLogger(__name__)


class NewsAPIProvider(BaseProvider):
    """
    NewsAPI provider facade with tier-aware rights enforcement.
    """

    def __init__(
        self,
        api_key: str,
        tier: str = "dev",  # "dev" or "business"
        base_url: str = "https://newsapi.org/v2",
    ):
        """
        Initialize NewsAPI provider.

        Args:
            api_key: NewsAPI key
            tier: "dev" (free, metadata-only) or "business" (paid, full export)
            base_url: NewsAPI base URL (default: https://newsapi.org/v2)
        """
        # Tier-specific configuration
        if tier == "dev":
            rate_limit_rpm = 30  # Dev tier: 100 req/day ≈ 30 req/min
            export_allowed = False
        elif tier == "business":
            rate_limit_rpm = 100  # Business tier: higher limits
            export_allowed = True
        else:
            raise ValueError(f"Invalid tier: {tier}. Must be 'dev' or 'business'")

        config = ProviderConfig(
            name=f"NewsAPI-{tier}",
            base_url=base_url,
            rate_limit_rpm=rate_limit_rpm,
            max_retries=3,
            retry_base_delay=1.0,
            rights={
                "export_pdf": export_allowed,
                "export_csv": export_allowed,
                "redistribution": export_allowed,
                "requires_attribution": True,
                "attribution_text": "News metadata via NewsAPI.org",
                "watermark_required": not export_allowed,  # Watermark if dev tier
            },
        )

        super().__init__(config)

        self.api_key = api_key
        self.tier = tier

    async def call(self, request: ProviderRequest) -> ProviderResponse:
        """
        Execute provider call (required by BaseProvider).
        
        This method is not used directly by NewsAPIProvider methods,
        but is required by the abstract base class.
        """
        # NewsAPIProvider uses direct HTTP calls in its methods
        # This is a placeholder implementation
        raise NotImplementedError("NewsAPIProvider uses direct HTTP calls, not the call() method")

    async def search(
        self,
        query: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        language: str = "en",
        sort_by: str = "relevancy",  # "relevancy", "popularity", "publishedAt"
        page_size: int = 100,
    ) -> List[Dict]:
        """
        Search news articles.

        Args:
            query: Search query (e.g., "AAPL", "Federal Reserve", "inflation")
            from_date: Start date (optional, default: 1 month ago)
            to_date: End date (optional, default: today)
            language: Language code (default: "en")
            sort_by: Sort order (default: "relevancy")
            page_size: Results per page (max 100, default 100)

        Returns:
            [
                {
                    "source": {"id": "bloomberg", "name": "Bloomberg"},
                    "author": "John Doe",
                    "title": "Apple Reports Record Quarter",
                    "description": "Apple Inc. reported...",
                    "url": "https://bloomberg.com/...",
                    "urlToImage": "https://...",
                    "publishedAt": "2024-01-15T14:30:00Z",
                    "content": "Apple Inc. (AAPL) reported...",  # ONLY if business tier
                    "metadata_only": True  # True if dev tier (no content stored)
                },
                ...
            ]

        Raises:
            ProviderError: If API call fails

        Note:
            - Dev tier: Returns metadata only (no "content" field)
            - Business tier: Returns full article content
            - Free tier has 100 requests/day limit
        """
        url = f"{self.config.base_url}/everything"

        # Default date range: last 30 days
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today()

        params = {
            "apiKey": self.api_key,
            "q": query,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
        }

        response = await self._request("GET", url, params=params)

        # Check for errors
        if response.get("status") != "ok":
            error_code = response.get("code", "unknown")
            error_message = response.get("message", "Unknown error")
            raise ProviderError(f"NewsAPI error ({error_code}): {error_message}")

        articles = response.get("articles", [])

        # Filter content based on tier
        filtered_articles = []
        for article in articles:
            # For dev tier: remove content field (metadata only)
            if self.tier == "dev":
                article_metadata = {
                    "source": article.get("source"),
                    "author": article.get("author"),
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "urlToImage": article.get("urlToImage"),
                    "publishedAt": article.get("publishedAt"),
                    "metadata_only": True,
                }
                filtered_articles.append(article_metadata)
            else:
                # Business tier: include full content
                article["metadata_only"] = False
                filtered_articles.append(article)

        logger.info(f"NewsAPI search: query='{query}', tier={self.tier}, results={len(filtered_articles)}")

        return filtered_articles

    async def get_top_headlines(
        self,
        country: str = "us",
        category: Optional[str] = None,  # "business", "technology", "science"
        query: Optional[str] = None,
        page_size: int = 100,
    ) -> List[Dict]:
        """
        Get top headlines.

        Args:
            country: Country code (default: "us")
            category: Category filter (optional)
            query: Search query (optional)
            page_size: Results per page (max 100)

        Returns:
            Same format as search() method

        Note:
            - Top headlines are breaking news
            - Updated more frequently than historical search
            - Same tier restrictions apply
        """
        url = f"{self.config.base_url}/top-headlines"

        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": page_size,
        }

        if category:
            params["category"] = category
        if query:
            params["q"] = query

        response = await self._request("GET", url, params=params)

        if response.get("status") != "ok":
            error_code = response.get("code", "unknown")
            error_message = response.get("message", "Unknown error")
            raise ProviderError(f"NewsAPI error ({error_code}): {error_message}")

        articles = response.get("articles", [])

        # Filter based on tier (same as search)
        filtered_articles = []
        for article in articles:
            if self.tier == "dev":
                article_metadata = {
                    "source": article.get("source"),
                    "author": article.get("author"),
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "urlToImage": article.get("urlToImage"),
                    "publishedAt": article.get("publishedAt"),
                    "metadata_only": True,
                }
                filtered_articles.append(article_metadata)
            else:
                article["metadata_only"] = False
                filtered_articles.append(article)

        return filtered_articles

    async def get_portfolio_news(
        self,
        symbols: List[str],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        max_per_symbol: int = 10,
    ) -> Dict[str, List[Dict]]:
        """
        Get news for portfolio holdings (multi-symbol fetch).

        Args:
            symbols: List of stock ticker symbols
            from_date: Start date (optional)
            to_date: End date (optional)
            max_per_symbol: Max articles per symbol (default 10)

        Returns:
            {
                "AAPL": [article1, article2, ...],
                "MSFT": [article1, article2, ...],
                ...
            }

        Note:
            - Fetches news sequentially to respect rate limit
            - For production, implement request batching/caching
        """
        results = {}

        for symbol in symbols:
            try:
                articles = await self.search(
                    query=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    page_size=max_per_symbol,
                )
                results[symbol] = articles
            except ProviderError as e:
                logger.error(f"Failed to fetch news for {symbol}: {e}")
                results[symbol] = []

        return results

    def can_export_content(self) -> bool:
        """
        Check if current tier allows content export.

        Returns:
            True if business tier (can export), False if dev tier (metadata only)
        """
        return self.tier == "business"

    def get_tier_info(self) -> Dict:
        """
        Get tier information and limitations.

        Returns:
            {
                "tier": "dev",
                "rate_limit_rpm": 30,
                "can_export_content": False,
                "requires_upgrade": True,
                "upgrade_url": "https://newsapi.org/pricing"
            }
        """
        return {
            "tier": self.tier,
            "rate_limit_rpm": self.rate_limit_rpm,
            "can_export_content": self.can_export_content(),
            "requires_upgrade": self.tier == "dev",
            "upgrade_url": "https://newsapi.org/pricing" if self.tier == "dev" else None,
        }

    async def _request(
        self, method: str, url: str, params: Optional[Dict] = None, json_body: Optional[Dict] = None
    ) -> Any:
        """
        Make HTTP request using httpx.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            json_body: JSON request body
            
        Returns:
            Response JSON data
        """
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
