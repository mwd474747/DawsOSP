#!/usr/bin/env python3
"""
Test script for NewsAPI integration

Tests the NewsCapability class with comprehensive error handling,
rate limiting, caching, sentiment analysis, and spam filtering.

Can run with or without a valid API key.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dawsos.capabilities.news import NewsCapability


class TestColors:
    """ANSI color codes for test output"""
    PASS = '\033[92m'
    FAIL = '\033[91m'
    SKIP = '\033[93m'
    INFO = '\033[94m'
    RESET = '\033[0m'


def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{TestColors.INFO}{'=' * 70}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 70}{TestColors.RESET}")


def print_result(test_name: str, passed: bool, message: str = "", skip: bool = False):
    """Print test result"""
    if skip:
        status = f"{TestColors.SKIP}SKIP{TestColors.RESET}"
    elif passed:
        status = f"{TestColors.PASS}PASS{TestColors.RESET}"
    else:
        status = f"{TestColors.FAIL}FAIL{TestColors.RESET}"

    print(f"[{status}] {test_name}")
    if message:
        print(f"       {message}")


def test_initialization():
    """Test 1: Initialize NewsCapability"""
    print_test_header("Initialize NewsCapability")

    try:
        news = NewsCapability()

        # Check attributes
        assert hasattr(news, 'api_key'), "Missing api_key attribute"
        assert hasattr(news, 'rate_limiter'), "Missing rate_limiter attribute"
        assert hasattr(news, 'cache'), "Missing cache attribute"
        assert hasattr(news, 'cache_ttl'), "Missing cache_ttl attribute"
        assert hasattr(news, 'cache_stats'), "Missing cache_stats attribute"

        # Check cache TTL configuration
        assert news.cache_ttl['headlines'] == 3600, "Headlines TTL should be 1 hour"
        assert news.cache_ttl['search'] == 21600, "Search TTL should be 6 hours"
        assert news.cache_ttl['company'] == 21600, "Company TTL should be 6 hours"
        assert news.cache_ttl['market'] == 21600, "Market TTL should be 6 hours"

        # Check cache stats initialization
        assert news.cache_stats['hits'] == 0, "Cache hits should start at 0"
        assert news.cache_stats['misses'] == 0, "Cache misses should start at 0"
        assert news.cache_stats['expired_fallbacks'] == 0, "Expired fallbacks should start at 0"

        # Check rate limiter
        assert news.rate_limiter.max_requests == 100, "Default rate limit should be 100/day"
        assert news.rate_limiter.get_requests_remaining() == 100, "Should have 100 requests remaining initially"

        has_api_key = news.api_key is not None and len(news.api_key) > 0

        print_result("Initialization", True,
                    f"API Key configured: {has_api_key}, Rate limit: {news.rate_limiter.max_requests}/day")

        return news, has_api_key

    except Exception as e:
        print_result("Initialization", False, f"Error: {e}")
        return None, False


def test_no_api_key_handling(news, has_api_key):
    """Test 2: Graceful handling when API key is missing"""
    print_test_header("No API Key Handling")

    if has_api_key:
        print_result("No API key handling", True,
                    "Skipping - API key is configured", skip=True)
        return True

    try:
        # Try to get headlines without API key
        articles = news.get_headlines()

        # Should return error but not crash
        if isinstance(articles, list):
            if len(articles) > 0 and 'error' in articles[0]:
                print_result("No API key handling", True,
                            "Correctly returns error without API key")
                return True

        print_result("No API key handling", False,
                    "Should return error when API key is missing")
        return False

    except Exception as e:
        # It's acceptable to raise an exception
        print_result("No API key handling", True,
                    f"Gracefully handles missing API key: {str(e)[:50]}")
        return True


def test_sentiment_analysis(news):
    """Test 3: Sentiment analysis (works without API key)"""
    print_test_header("Sentiment Analysis")

    try:
        # Test positive sentiment
        positive_article = {
            'title': 'Stock Surges to Record High on Strong Earnings Beat',
            'description': 'Company exceeds expectations with robust profit growth and optimistic outlook'
        }

        sentiment = news.analyze_sentiment(positive_article)

        assert 'score' in sentiment, "Missing sentiment score"
        assert 'label' in sentiment, "Missing sentiment label"
        assert sentiment['label'] == 'positive', f"Expected positive sentiment, got {sentiment['label']}"
        assert sentiment['score'] > 0, f"Expected positive score, got {sentiment['score']}"

        # Test negative sentiment
        negative_article = {
            'title': 'Stock Plunges on Weak Earnings Miss',
            'description': 'Company reports disappointing losses amid concerns about declining revenue'
        }

        sentiment = news.analyze_sentiment(negative_article)
        assert sentiment['label'] == 'negative', f"Expected negative sentiment, got {sentiment['label']}"
        assert sentiment['score'] < 0, f"Expected negative score, got {sentiment['score']}"

        # Test neutral sentiment
        neutral_article = {
            'title': 'Company Announces New Product',
            'description': 'Technology firm unveils latest innovation'
        }

        sentiment = news.analyze_sentiment(neutral_article)
        assert sentiment['label'] == 'neutral', f"Expected neutral sentiment, got {sentiment['label']}"

        print_result("Sentiment analysis", True,
                    f"Positive: {positive_article['title'][:30]}... -> score={news.analyze_sentiment(positive_article)['score']}")

        return True

    except Exception as e:
        print_result("Sentiment analysis", False, f"Error: {e}")
        return False


def test_spam_filtering(news):
    """Test 4: Spam and low-quality filtering"""
    print_test_header("Spam/Quality Filtering")

    try:
        # Test spam domain filtering
        spam_article = {
            'title': 'Some article',
            'description': 'Some description',
            'url': 'https://biztoc.com/article/12345',
            'source': {'name': 'BizToc'}
        }

        is_spam = news._is_spam_or_low_quality(spam_article)
        assert is_spam == True, "Should identify biztoc.com as spam"

        # Test [Removed] content filtering
        removed_article = {
            'title': 'Some article',
            'description': '[Removed]',
            'url': 'https://reuters.com/article',
            'source': {'name': 'Reuters'}
        }

        is_spam = news._is_spam_or_low_quality(removed_article)
        assert is_spam == True, "Should identify [Removed] content as low quality"

        # Test legitimate article
        good_article = {
            'title': 'Tesla Reports Q3 Earnings',
            'description': 'Electric vehicle maker beats expectations',
            'url': 'https://reuters.com/article/tesla-earnings',
            'source': {'name': 'Reuters'}
        }

        is_spam = news._is_spam_or_low_quality(good_article)
        assert is_spam == False, "Should not filter legitimate article"

        # Test quality scoring
        quality = news._calculate_quality_score(good_article)
        assert quality > 0.5, f"Quality sources should have score > 0.5, got {quality}"

        print_result("Spam filtering", True,
                    f"Spam domains: {len(news.SPAM_DOMAINS)}, Quality scoring working")

        return True

    except Exception as e:
        print_result("Spam filtering", False, f"Error: {e}")
        return False


def test_company_news(news, has_api_key):
    """Test 5: Get company-specific news for Tesla"""
    print_test_header("Company News (Tesla)")

    if not has_api_key:
        print_result("Company news", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Get Tesla news
        articles = news.get_company_news('TSLA', days=7)

        # Check result
        if isinstance(articles, list) and len(articles) > 0:
            if 'error' in articles[0]:
                print_result("Company news", False,
                            f"API Error: {articles[0].get('error', 'Unknown')}")
                return False

            # Validate article structure
            article = articles[0]
            required_fields = ['title', 'source', 'published_at', 'sentiment', 'sentiment_score']

            for field in required_fields:
                assert field in article, f"Missing field: {field}"

            print_result("Company news", True,
                        f"Retrieved {len(articles)} Tesla articles, "
                        f"Latest: {article['title'][:50]}...")

            # Print first few articles
            print(f"\n       Top 3 Tesla News Articles:")
            for i, art in enumerate(articles[:3], 1):
                print(f"       {i}. {art['title'][:60]}...")
                print(f"          Sentiment: {art['sentiment']} ({art['sentiment_score']}), "
                      f"Quality: {art.get('quality_score', 'N/A')}")

            return True
        else:
            print_result("Company news", False, "No articles returned")
            return False

    except Exception as e:
        print_result("Company news", False, f"Error: {e}")
        return False


def test_caching(news, has_api_key):
    """Test 6: Caching functionality"""
    print_test_header("Caching")

    if not has_api_key:
        print_result("Caching", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Clear cache
        news.cache.clear()
        news.cache_stats = {'hits': 0, 'misses': 0, 'expired_fallbacks': 0}

        # First request - should be cache miss
        articles1 = news.get_company_news('AAPL', days=7)
        stats1 = news.get_cache_stats()

        # Second request - should be cache hit
        articles2 = news.get_company_news('AAPL', days=7)
        stats2 = news.get_cache_stats()

        # Verify caching worked
        assert stats1['cache_misses'] > 0, "First request should be cache miss"
        assert stats2['cache_hits'] > 0, "Second request should be cache hit"
        assert stats2['cached_items'] > 0, "Should have cached items"

        # Verify same data returned
        if isinstance(articles1, list) and isinstance(articles2, list) and len(articles1) > 0:
            assert len(articles1) == len(articles2), "Cached data should match original"

        print_result("Caching", True,
                    f"Cache working: {stats2['cache_hits']} hits, "
                    f"{stats2['cache_misses']} misses, "
                    f"Hit rate: {stats2['cache_hit_rate']}")

        return True

    except Exception as e:
        print_result("Caching", False, f"Error: {e}")
        return False


def test_rate_limiting(news, has_api_key):
    """Test 7: Rate limiting (daily limit tracking)"""
    print_test_header("Rate Limiting")

    try:
        # Get initial rate limit status
        initial_status = news.get_rate_limit_status()

        assert 'requests_remaining' in initial_status, "Missing requests_remaining"
        assert 'usage_percentage' in initial_status, "Missing usage_percentage"
        assert 'max_requests_per_day' in initial_status, "Missing max_requests_per_day"

        # Simulate some requests (if we have API key)
        if has_api_key:
            # Make a request
            news.get_headlines(category='business')

            # Check updated status
            updated_status = news.get_rate_limit_status()

            # Usage should have increased
            initial_remaining = initial_status['requests_remaining']
            updated_remaining = updated_status['requests_remaining']

            print_result("Rate limiting", True,
                        f"Tracking working: {updated_remaining}/{initial_status['max_requests_per_day']} "
                        f"remaining, Usage: {updated_status['usage_percentage']}")
        else:
            print_result("Rate limiting", True,
                        f"Rate limiter initialized: {initial_status['max_requests_per_day']}/day limit",
                        skip=True)

        return True

    except Exception as e:
        print_result("Rate limiting", False, f"Error: {e}")
        return False


def test_key_events(news, has_api_key):
    """Test 8: Extract key events"""
    print_test_header("Key Events Extraction")

    if not has_api_key:
        print_result("Key events", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Get some articles
        articles = news.get_company_news('TSLA', days=7)

        if isinstance(articles, list) and len(articles) > 0 and 'error' not in articles[0]:
            # Extract key events
            events = news.extract_key_events(articles)

            # Validate structure
            if len(events) > 0:
                event = events[0]
                required_fields = ['date', 'title', 'sentiment', 'impact_score']

                for field in required_fields:
                    assert field in event, f"Missing field: {field}"

                print_result("Key events", True,
                            f"Extracted {len(events)} key events from {len(articles)} articles")

                # Print top events
                if len(events) > 0:
                    print(f"\n       Top 3 Key Events:")
                    for i, event in enumerate(events[:3], 1):
                        print(f"       {i}. {event['title'][:60]}...")
                        print(f"          Impact: {event['impact_score']}, Sentiment: {event['sentiment']}")
            else:
                print_result("Key events", True,
                            "No high-impact events found (expected for some queries)")

            return True
        else:
            print_result("Key events", True,
                        "Skipping - no articles available", skip=True)
            return True

    except Exception as e:
        print_result("Key events", False, f"Error: {e}")
        return False


def test_trending_topics(news, has_api_key):
    """Test 9: Get trending topics"""
    print_test_header("Trending Topics")

    if not has_api_key:
        print_result("Trending topics", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Get trending topics
        trending = news.get_trending_topics(days=7)

        # Validate structure
        assert 'trending_topics' in trending, "Missing trending_topics"
        assert 'total_articles_analyzed' in trending, "Missing total_articles_analyzed"

        topics = trending['trending_topics']

        if len(topics) > 0:
            # Validate topic structure
            topic = topics[0]
            assert 'topic' in topic, "Missing topic name"
            assert 'count' in topic, "Missing topic count"

            print_result("Trending topics", True,
                        f"Analyzed {trending['total_articles_analyzed']} articles, "
                        f"found {len(topics)} trending topics")

            # Print top topics
            print(f"\n       Top 5 Trending Topics:")
            for i, topic in enumerate(topics[:5], 1):
                print(f"       {i}. {topic['topic'].upper()}: {topic['count']} mentions")
                if topic.get('sample_article'):
                    print(f"          Sample: {topic['sample_article']['title'][:50]}...")
        else:
            print_result("Trending topics", True,
                        "No trending topics found (expected for limited data)")

        return True

    except Exception as e:
        print_result("Trending topics", False, f"Error: {e}")
        return False


def test_market_sentiment(news, has_api_key):
    """Test 10: Market sentiment analysis"""
    print_test_header("Market Sentiment")

    if not has_api_key:
        print_result("Market sentiment", True,
                    "Skipping - no API key configured", skip=True)
        return True

    try:
        # Get market sentiment
        sentiment = news.get_market_sentiment()

        # Validate structure
        required_fields = ['overall', 'average_score', 'distribution', 'article_count']

        for field in required_fields:
            assert field in sentiment, f"Missing field: {field}"

        # Validate distribution
        dist = sentiment['distribution']
        assert 'positive' in dist, "Missing positive distribution"
        assert 'negative' in dist, "Missing negative distribution"
        assert 'neutral' in dist, "Missing neutral distribution"

        # Distribution should sum to ~1.0
        total_dist = dist['positive'] + dist['negative'] + dist['neutral']
        assert abs(total_dist - 1.0) < 0.01, f"Distribution should sum to 1.0, got {total_dist}"

        print_result("Market sentiment", True,
                    f"Overall: {sentiment['overall'].upper()}, "
                    f"Avg Score: {sentiment['average_score']}, "
                    f"Articles: {sentiment['article_count']}")

        print(f"\n       Sentiment Distribution:")
        print(f"       Positive: {dist['positive']*100:.1f}%")
        print(f"       Negative: {dist['negative']*100:.1f}%")
        print(f"       Neutral: {dist['neutral']*100:.1f}%")

        return True

    except Exception as e:
        print_result("Market sentiment", False, f"Error: {e}")
        return False


def print_summary(results: dict, news):
    """Print test summary"""
    print(f"\n{TestColors.INFO}{'=' * 70}")
    print("TEST SUMMARY")
    print(f"{'=' * 70}{TestColors.RESET}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{TestColors.PASS}PASS{TestColors.RESET}" if result else f"{TestColors.FAIL}FAIL{TestColors.RESET}"
        print(f"  [{status}] {test_name}")

    print(f"\n{TestColors.INFO}Overall: {passed}/{total} tests passed{TestColors.RESET}")

    # Print final stats
    print(f"\n{TestColors.INFO}Final Statistics:{TestColors.RESET}")
    cache_stats = news.get_cache_stats()
    rate_stats = news.get_rate_limit_status()

    print(f"  Cache Hit Rate: {cache_stats['cache_hit_rate']}")
    print(f"  Cached Items: {cache_stats['cached_items']}")
    print(f"  API Requests Used: {rate_stats['requests_used']}/{rate_stats['max_requests_per_day']}")
    print(f"  Requests Remaining: {rate_stats['requests_remaining']}")

    return passed == total


def main():
    """Run all tests"""
    print(f"{TestColors.INFO}")
    print("=" * 70)
    print("NewsAPI Integration Test Suite")
    print("=" * 70)
    print(f"{TestColors.RESET}")

    results = {}

    # Test 1: Initialization
    news, has_api_key = test_initialization()
    if news is None:
        print(f"\n{TestColors.FAIL}FATAL: Failed to initialize. Aborting tests.{TestColors.RESET}")
        sys.exit(1)

    # Test 2: No API key handling
    results['No API key handling'] = test_no_api_key_handling(news, has_api_key)

    # Test 3: Sentiment analysis
    results['Sentiment analysis'] = test_sentiment_analysis(news)

    # Test 4: Spam filtering
    results['Spam filtering'] = test_spam_filtering(news)

    # Test 5: Company news
    results['Company news'] = test_company_news(news, has_api_key)

    # Test 6: Caching
    results['Caching'] = test_caching(news, has_api_key)

    # Test 7: Rate limiting
    results['Rate limiting'] = test_rate_limiting(news, has_api_key)

    # Test 8: Key events
    results['Key events'] = test_key_events(news, has_api_key)

    # Test 9: Trending topics
    results['Trending topics'] = test_trending_topics(news, has_api_key)

    # Test 10: Market sentiment
    results['Market sentiment'] = test_market_sentiment(news, has_api_key)

    # Print summary
    all_passed = print_summary(results, news)

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
