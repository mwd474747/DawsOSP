import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class NewsCapability:
    """News and sentiment analysis capability"""
    
    def __init__(self, api_key: str = None):
        # Using NewsAPI (free tier available)
        # Get key at: https://newsapi.org/register
        self.api_key = api_key or os.getenv('NEWSAPI_KEY', 'your_newsapi_key_here')
        self.base_url = 'https://newsapi.org/v2'
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_headlines(self, query: str = None, category: str = 'business') -> List[Dict]:
        """Get top headlines"""
        cache_key = f"headlines_{query}_{category}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached['time'] < timedelta(seconds=self.cache_ttl):
                return cached['data']
        
        # Build URL
        endpoint = f"{self.base_url}/top-headlines"
        params = {
            'apiKey': self.api_key,
            'category': category,
            'country': 'us',
            'pageSize': 20
        }
        
        if query:
            params['q'] = query
        
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'source': article.get('source', {}).get('name'),
                        'url': article.get('url'),
                        'published_at': article.get('publishedAt'),
                        'sentiment': self._analyze_sentiment(article)
                    })
                
                # Cache results
                self.cache[cache_key] = {
                    'data': articles,
                    'time': datetime.now()
                }
                
                return articles
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def search_news(self, query: str, from_date: str = None) -> List[Dict]:
        """Search news articles"""
        if not from_date:
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        endpoint = f"{self.base_url}/everything"
        params = {
            'apiKey': self.api_key,
            'q': query,
            'from': from_date,
            'sortBy': 'relevancy',
            'pageSize': 20,
            'language': 'en'
        }
        
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'source': article.get('source', {}).get('name'),
                        'url': article.get('url'),
                        'published_at': article.get('publishedAt'),
                        'sentiment': self._analyze_sentiment(article)
                    })
                
                return articles
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def _analyze_sentiment(self, article: Dict) -> str:
        """Simple sentiment analysis based on keywords"""
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        
        positive_words = ['surge', 'gain', 'profit', 'growth', 'rally', 'boom', 
                         'strong', 'beat', 'exceed', 'record', 'high', 'optimistic']
        negative_words = ['crash', 'fall', 'loss', 'decline', 'drop', 'weak',
                         'miss', 'concern', 'fear', 'risk', 'low', 'pessimistic']
        
        positive_score = sum(1 for word in positive_words if word in text)
        negative_score = sum(1 for word in negative_words if word in text)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def get_market_sentiment(self) -> Dict:
        """Get overall market sentiment"""
        # Get headlines for market analysis
        headlines = self.get_headlines(category='business')
        
        sentiment_counts = {
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        for article in headlines:
            if 'sentiment' in article:
                sentiment_counts[article['sentiment']] += 1
        
        total = sum(sentiment_counts.values()) or 1
        
        return {
            'overall': max(sentiment_counts, key=sentiment_counts.get),
            'distribution': {
                'positive': sentiment_counts['positive'] / total,
                'negative': sentiment_counts['negative'] / total,
                'neutral': sentiment_counts['neutral'] / total
            },
            'article_count': total,
            'timestamp': datetime.now().isoformat()
        }

    def search(self, query: str, limit: int = 10, from_date: str = None) -> List[Dict]:
        """Search news articles (alias for search_news with limit)"""
        articles = self.search_news(query, from_date)
        if isinstance(articles, list) and len(articles) > 0 and 'error' not in articles[0]:
            return articles[:limit]
        return articles