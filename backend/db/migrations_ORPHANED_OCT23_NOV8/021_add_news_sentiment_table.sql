-- Migration 021: Add News Sentiment Table
-- Created: 2025-11-08
-- Purpose: Store news sentiment analysis for securities

-- Create news_sentiment table
CREATE TABLE IF NOT EXISTS news_sentiment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    headline TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    source TEXT,  -- 'reuters', 'bloomberg', 'cnbc', 'marketwatch', etc.
    source_url TEXT,
    sentiment_score NUMERIC(5,4) NOT NULL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    sentiment_label TEXT,  -- 'very_negative', 'negative', 'neutral', 'positive', 'very_positive'
    confidence NUMERIC(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    relevance_score NUMERIC(5,4) CHECK (relevance_score >= 0 AND relevance_score <= 1),
    impact_score NUMERIC(5,4),  -- Expected impact on price (-1 to 1)
    categories TEXT[],  -- ['earnings', 'merger', 'regulatory', 'product', 'management']
    entities JSONB,  -- Named entities extracted from the article
    metadata JSONB,  -- Additional metadata (author, tags, etc.)
    published_at TIMESTAMPTZ NOT NULL,
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol, source_url)  -- Prevent duplicate articles
);

-- Indexes for performance
CREATE INDEX idx_news_sentiment_symbol ON news_sentiment(symbol);
CREATE INDEX idx_news_sentiment_portfolio ON news_sentiment(portfolio_id);
CREATE INDEX idx_news_sentiment_published ON news_sentiment(published_at DESC);
CREATE INDEX idx_news_sentiment_sentiment ON news_sentiment(sentiment_score);
CREATE INDEX idx_news_sentiment_symbol_date ON news_sentiment(symbol, published_at DESC);
CREATE INDEX idx_news_sentiment_symbol_sentiment ON news_sentiment(symbol, sentiment_score);

-- Index for full-text search on headlines and summary
CREATE INDEX idx_news_sentiment_text_search ON news_sentiment 
    USING GIN(to_tsvector('english', headline || ' ' || COALESCE(summary, '')));

-- Comments for documentation
COMMENT ON TABLE news_sentiment IS 
    'Store news articles with sentiment analysis for securities.
     Used by alert system to trigger conditions based on sentiment changes.';

COMMENT ON COLUMN news_sentiment.sentiment_score IS 
    'Sentiment score ranging from -1 (very negative) to +1 (very positive)';

COMMENT ON COLUMN news_sentiment.sentiment_label IS 
    'Human-readable sentiment classification';

COMMENT ON COLUMN news_sentiment.confidence IS 
    'Confidence level of the sentiment analysis (0-1)';

COMMENT ON COLUMN news_sentiment.relevance_score IS 
    'How relevant this news is to the security (0-1)';

COMMENT ON COLUMN news_sentiment.impact_score IS 
    'Expected price impact based on historical patterns (-1 to +1)';

COMMENT ON COLUMN news_sentiment.categories IS 
    'Array of news categories this article belongs to';

COMMENT ON COLUMN news_sentiment.entities IS 
    'Named entities extracted from article. 
     Example: {"companies": ["Apple", "Microsoft"], "people": ["Tim Cook"], "products": ["iPhone 15"]}';

-- Row-Level Security policies
ALTER TABLE news_sentiment ENABLE ROW LEVEL SECURITY;

-- Users can read their own portfolio's news or public news
CREATE POLICY news_sentiment_read ON news_sentiment
    FOR SELECT
    USING (
        portfolio_id IS NULL  -- Public news
        OR portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

-- Users can insert news for their own portfolios
CREATE POLICY news_sentiment_write ON news_sentiment
    FOR INSERT
    WITH CHECK (
        portfolio_id IS NULL  -- Allow public news insertion
        OR portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

-- Users can update news for their own portfolios
CREATE POLICY news_sentiment_update ON news_sentiment
    FOR UPDATE
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

-- Users can delete their own news
CREATE POLICY news_sentiment_delete ON news_sentiment
    FOR DELETE
    USING (
        portfolio_id IN (
            SELECT id FROM portfolios 
            WHERE user_id = current_setting('app.user_id', true)::uuid
        )
    );

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON news_sentiment TO dawsos_app;
GRANT USAGE ON SEQUENCE news_sentiment_id_seq TO dawsos_app;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_news_sentiment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_news_sentiment_timestamp
    BEFORE UPDATE ON news_sentiment
    FOR EACH ROW
    EXECUTE FUNCTION update_news_sentiment_updated_at();

-- Create function to calculate average sentiment for a symbol over a time period
CREATE OR REPLACE FUNCTION get_average_sentiment(
    p_symbol TEXT,
    p_lookback_days INTEGER DEFAULT 7
)
RETURNS NUMERIC AS $$
DECLARE
    avg_sentiment NUMERIC;
BEGIN
    SELECT AVG(sentiment_score) INTO avg_sentiment
    FROM news_sentiment
    WHERE symbol = p_symbol
    AND published_at >= NOW() - INTERVAL '1 day' * p_lookback_days;
    
    RETURN COALESCE(avg_sentiment, 0);
END;
$$ LANGUAGE plpgsql;