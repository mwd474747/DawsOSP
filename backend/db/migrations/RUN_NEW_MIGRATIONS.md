# New Database Migrations - Security Ratings and News Sentiment

**Created:** November 8, 2025  
**Purpose:** Add security ratings and news sentiment tables for alert conditions

## Migration Files

### 020_add_security_ratings_table.sql
- Creates `security_ratings` table for storing quality ratings
- Supports rating types: moat_strength, dividend_safety, quality, resilience
- Includes RLS policies for multi-tenant isolation
- Adds indexes for performance optimization

### 021_add_news_sentiment_table.sql
- Creates `news_sentiment` table for storing sentiment analysis
- Sentiment scores range from -1 (very negative) to +1 (very positive)
- Includes full-text search capabilities
- Adds helper function `get_average_sentiment()` for calculations
- Includes RLS policies for multi-tenant isolation

### 022_update_rls_policies_comments.sql
- Adds comprehensive documentation to all RLS policies
- Creates helper view `rls_policy_status` for policy inspection
- Adds `test_rls_policy()` function for testing policies
- Adds `check_rls_status()` function for verification

## How to Apply These Migrations

### Option 1: Direct Application (Development)
```bash
# Connect to database and run migrations
psql $DATABASE_URL -f backend/db/migrations/020_add_security_ratings_table.sql
psql $DATABASE_URL -f backend/db/migrations/021_add_news_sentiment_table.sql
psql $DATABASE_URL -f backend/db/migrations/022_update_rls_policies_comments.sql
```

### Option 2: Using execute_sql_tool (Recommended for Replit)
```python
# From Python code
from backend.app.db.connection import get_db_connection

async def apply_migrations():
    async with get_db_connection() as conn:
        # Read and execute each migration file
        for migration in [
            '020_add_security_ratings_table.sql',
            '021_add_news_sentiment_table.sql',
            '022_update_rls_policies_comments.sql'
        ]:
            with open(f'backend/db/migrations/{migration}', 'r') as f:
                sql = f.read()
                await conn.execute(sql)
                print(f"Applied migration: {migration}")
```

## Verification

After applying migrations, verify they're working:

### 1. Check Tables Exist
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('security_ratings', 'news_sentiment');
```

### 2. Verify RLS Status
```sql
SELECT * FROM check_rls_status();
```

### 3. View All RLS Policies
```sql
SELECT * FROM rls_policy_status;
```

### 4. Test RLS for a User
```sql
-- Replace with actual user UUID
SELECT * FROM test_rls_policy('security_ratings', '123e4567-e89b-12d3-a456-426614174000');
```

## Integration with Alert System

The alert system in `backend/app/services/alerts.py` expects these tables to exist for:

### Security Ratings Conditions
```python
# Alert when moat strength drops below 70
{
    "type": "rating",
    "symbol": "AAPL",
    "rating_type": "moat_strength",
    "op": "<",
    "value": 70
}
```

### News Sentiment Conditions
```python
# Alert when sentiment turns negative
{
    "type": "news_sentiment",
    "symbol": "AAPL",
    "metric": "sentiment",
    "op": "<",
    "value": -0.5
}
```

## Sample Data (Optional)

### Insert Sample Security Rating
```sql
INSERT INTO security_ratings (
    symbol, rating_type, rating_value, rating_score, rating_grade,
    components, source, asof_date
) VALUES (
    'AAPL', 'moat_strength', 85.5, 85.5, 'A',
    '{"brand": 0.95, "switching_cost": 0.80, "network_effect": 0.75}'::jsonb,
    'system', CURRENT_DATE
);
```

### Insert Sample News Sentiment
```sql
INSERT INTO news_sentiment (
    symbol, headline, summary, source, sentiment_score, 
    sentiment_label, confidence, published_at
) VALUES (
    'AAPL', 
    'Apple Reports Record Q4 Earnings',
    'Apple exceeded analyst expectations with strong iPhone sales',
    'reuters', 
    0.75, 
    'positive', 
    0.92,
    NOW()
);
```

## Rollback (If Needed)

```sql
-- Rollback in reverse order
DROP TABLE IF EXISTS news_sentiment CASCADE;
DROP TABLE IF EXISTS security_ratings CASCADE;
DROP FUNCTION IF EXISTS test_rls_policy(TEXT, UUID);
DROP FUNCTION IF EXISTS check_rls_status();
DROP FUNCTION IF EXISTS get_average_sentiment(TEXT, INTEGER);
DROP VIEW IF EXISTS rls_policy_status;
```

## Notes

- The tables include proper foreign key constraints to `portfolios` table
- RLS policies ensure multi-tenant isolation
- Indexes are created for common query patterns
- Both tables support NULL portfolio_id for public/global data
- Timestamps use TIMESTAMPTZ for proper timezone handling
- JSONB fields allow flexible metadata storage

## Related Files

- `backend/app/services/alerts.py` - Uses these tables for alert conditions
- `backend/app/db/connection.py` - Manages RLS-aware connections

**Note:** `alert_validation.py` was removed during cleanup (2025-01-15) as it was unused. Validation is now handled directly in the alert service.