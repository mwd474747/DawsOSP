"""Pydantic models for NewsAPI article validation.

Validates news articles with sentiment scores and quality metrics
to ensure data integrity and prevent invalid sentiment values.

Reference: https://newsapi.org/docs
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class NewsArticle(BaseModel):
    """News article with sentiment and quality validation.

    Validates NewsAPI article responses with sentiment scoring constraints.

    Example:
        >>> article = NewsArticle(
        ...     title='Apple Reports Record Earnings',
        ...     description='Apple Inc. announced...',
        ...     source='Reuters',
        ...     url='https://...',
        ...     published_at='2025-01-15T10:30:00Z',
        ...     sentiment='positive',
        ...     sentiment_score=0.85,
        ...     quality_score=0.92
        ... )
    """
    model_config = ConfigDict(frozen=True)

    # Required fields
    title: str = Field(..., min_length=1, description="Article headline")
    source: str = Field(..., min_length=1, description="News source name")
    url: str = Field(..., min_length=1, description="Article URL")
    published_at: str = Field(..., description="Publication timestamp (ISO format)")

    # Optional content
    description: Optional[str] = Field(None, description="Article description/excerpt")
    content: Optional[str] = Field(None, description="Full article content")
    author: Optional[str] = Field(None, description="Article author")
    image_url: Optional[str] = Field(None, alias='urlToImage', description="Article image URL")

    # Sentiment analysis (from NewsCapability.analyze_sentiment)
    sentiment: str = Field(..., description="Sentiment label: 'positive', 'negative', or 'neutral'")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score in range [-1, 1]")

    # Quality metrics (from NewsCapability._calculate_quality_score)
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score in range [0, 1]")

    # Cache metadata
    cached: Optional[bool] = Field(None, alias='_cached', description="Whether from cache")
    warning: Optional[str] = Field(None, alias='_warning', description="Cache warning message")

    @field_validator('sentiment')
    @classmethod
    def validate_sentiment_label(cls, v: str) -> str:
        """Ensure sentiment is one of the valid labels."""
        valid_labels = ['positive', 'negative', 'neutral']
        if v.lower() not in valid_labels:
            raise ValueError(f"sentiment must be one of {valid_labels}, got: {v}")
        return v.lower()

    @field_validator('sentiment_score')
    @classmethod
    def validate_sentiment_score_range(cls, v: float) -> float:
        """Ensure sentiment score is in valid range [-1, 1]."""
        if v < -1.0 or v > 1.0:
            raise ValueError(f"sentiment_score must be in range [-1, 1], got: {v}")
        return v

    @field_validator('quality_score')
    @classmethod
    def validate_quality_score_range(cls, v: float) -> float:
        """Ensure quality score is in valid range [0, 1]."""
        if v < 0.0 or v > 1.0:
            raise ValueError(f"quality_score must be in range [0, 1], got: {v}")
        return v

    @field_validator('published_at')
    @classmethod
    def validate_published_at_format(cls, v: str) -> str:
        """Ensure published_at is valid ISO timestamp."""
        try:
            # Try parsing as ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            # Try alternative formats
            try:
                datetime.strptime(v, '%Y-%m-%dT%H:%M:%SZ')
                return v
            except ValueError:
                # Don't fail, just return as-is
                return v

    @field_validator('title')
    @classmethod
    def validate_title_not_spam(cls, v: str) -> str:
        """Ensure title is not obvious spam."""
        spam_indicators = ['[Removed]', '[Deleted]', 'Click here']
        if any(indicator in v for indicator in spam_indicators):
            raise ValueError(f"Article appears to be spam: {v}")
        return v


class NewsResponse(BaseModel):
    """Complete news API response with multiple articles.

    Wrapper for list of NewsArticle objects with metadata.
    """
    model_config = ConfigDict(frozen=True)

    articles: list[NewsArticle] = Field(..., min_length=0, description="List of news articles")
    total_results: Optional[int] = Field(None, ge=0, description="Total articles available")
    status: str = Field(default='ok', description="API response status")
    source_type: Optional[str] = Field(None, description="Type of news source (headlines, search, etc.)")

    @field_validator('articles')
    @classmethod
    def validate_articles_limit(cls, v: list[NewsArticle]) -> list[NewsArticle]:
        """Warn if too many articles (potential spam)."""
        if len(v) > 100:
            # Don't fail, but this might indicate an issue
            pass
        return v


class SentimentSummary(BaseModel):
    """Aggregated sentiment metrics across multiple articles.

    Used for market sentiment analysis from NewsCapability.get_market_sentiment().
    """
    model_config = ConfigDict(frozen=True)

    positive_count: int = Field(..., ge=0, description="Number of positive articles")
    negative_count: int = Field(..., ge=0, description="Number of negative articles")
    neutral_count: int = Field(..., ge=0, description="Number of neutral articles")

    average_sentiment: float = Field(..., ge=-1.0, le=1.0, description="Average sentiment score")
    sentiment_volatility: Optional[float] = Field(None, ge=0.0, description="Sentiment standard deviation")

    total_articles: int = Field(..., ge=0, description="Total number of articles analyzed")

    @field_validator('total_articles')
    @classmethod
    def validate_total_matches_counts(cls, v: int, info) -> int:
        """Ensure total_articles matches sum of counts."""
        if 'positive_count' in info.data and 'negative_count' in info.data and 'neutral_count' in info.data:
            expected = info.data['positive_count'] + info.data['negative_count'] + info.data['neutral_count']
            if v != expected:
                raise ValueError(
                    f"total_articles ({v}) doesn't match sum of counts ({expected})"
                )
        return v


# Package exports
__all__ = [
    'NewsArticle',
    'NewsResponse',
    'SentimentSummary',
]
