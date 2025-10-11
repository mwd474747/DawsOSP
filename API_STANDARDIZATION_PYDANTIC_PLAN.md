# API Standardization & Pydantic Migration Plan
**Date**: October 10, 2025
**Scope**: All 7 capability classes + agent integrations
**Goal**: Type-safe, validated API integrations with zero silent failures

---

## 📊 Current API Landscape

### API Capabilities Inventory

| Capability | Lines | API Provider | Auth | Status | Data Types |
|------------|-------|--------------|------|--------|------------|
| **FredDataCapability** | 909 | Federal Reserve FRED | API Key | 🔴 Broken (double normalization) | Economic indicators |
| **MarketDataCapability** | 705 | Financial Modeling Prep (FMP) | API Key | 🟡 Unvalidated | Stock quotes, profiles, historical |
| **NewsCapability** | 775 | NewsAPI / Custom | API Key | 🟡 Unvalidated | News articles, sentiment |
| **PolygonOptionsCapability** | 445 | Polygon.io | API Key | 🟡 Unvalidated | Options contracts, chains |
| **FREDCapability** (legacy) | 116 | Federal Reserve FRED | API Key | 🟠 Deprecated | Economic data (old format) |
| **FundamentalsCapability** | 109 | FMP | API Key | 🟡 Unvalidated | Financial ratios, statements |
| **CryptoCapability** | 68 | CoinGecko | None | 🟡 Unvalidated | Cryptocurrency prices |

**Total API surface**: 3,127 lines of code
**Type validation**: 0% (TypeAlias only, no runtime validation)
**Error handling**: Inconsistent (mix of silent failures and logging)

---

## 🔬 Detailed Capability Analysis

### 1. FredDataCapability (FRED Economic Data)

**Current Issues**:
- ❌ Double normalization (capability + normalizer)
- ❌ Silent parsing failures (`try/except: continue`)
- ❌ Format incompatibility with PatternEngine
- ❌ No schema validation

**API Methods**:
```python
get_series(series_id, start_date, end_date) → SeriesData
get_multiple_series(series_ids, start_date, end_date) → Dict[str, SeriesData]
fetch_economic_indicators(series, start_date, end_date, frequency) → Dict[str, Any]
get_latest_value(series_id) → SeriesData
```

**Response Format** (Current - Unvalidated):
```python
{
    'series': {
        'GDP': {
            'series_id': 'GDP',
            'name': 'Gross Domestic Product',
            'units': 'Billions of Dollars',
            'frequency': 'Quarterly',
            'observations': [{'date': '2025-01-01', 'value': 27000.0}, ...],
            'latest_value': 27500.0,
            'latest_date': '2025-04-01'
        }
    },
    'source': 'live',  # or 'cache', 'fallback'
    'timestamp': '2025-10-10T12:00:00',
    'cache_age_seconds': 0,
    'health': {...},
    '_metadata': {...}
}
```

**Pydantic Schema** (Proposed):
```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Literal
from datetime import datetime

class Observation(BaseModel):
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    value: float

    class Config:
        frozen = True  # Immutable

class SeriesData(BaseModel):
    series_id: str = Field(..., min_length=1)
    name: str
    units: str
    frequency: str
    observations: List[Observation] = Field(..., min_items=1)
    latest_value: float
    latest_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')

    @validator('observations')
    def check_observations(cls, v):
        if not v:
            raise ValueError("Observations cannot be empty")
        return sorted(v, key=lambda x: x.date)  # Ensure sorted

    @validator('latest_value')
    def validate_latest_matches(cls, v, values):
        if 'observations' in values and values['observations']:
            last_obs = values['observations'][-1].value
            if abs(v - last_obs) > 0.01:
                raise ValueError(f"Latest value {v} != last observation {last_obs}")
        return v

class FREDHealthStatus(BaseModel):
    api_available: bool
    rate_limit_remaining: int = Field(..., ge=0)
    last_error: Optional[str]
    error_count: int = Field(..., ge=0)

class EconomicDataResponse(BaseModel):
    series: Dict[str, SeriesData] = Field(..., min_items=1)
    source: Literal['live', 'cache', 'fallback']
    timestamp: datetime
    cache_age_seconds: int = Field(..., ge=0)
    health: FREDHealthStatus
    _metadata: dict

    @validator('series')
    def check_all_series_valid(cls, v):
        for series_id, data in v.items():
            if series_id != data.series_id:
                raise ValueError(f"Key '{series_id}' doesn't match series_id '{data.series_id}'")
        return v
```

**Migration Impact**: HIGH
- Breaks existing PatternEngine code (already broken)
- Requires updating data_harvester.fetch_economic_data()
- Benefits: Type safety, clear errors, self-documenting

---

### 2. MarketDataCapability (FMP Stock Data)

**API Methods**:
```python
get_quote(symbol) → QuoteData
get_profile(symbol) → ProfileData
get_historical_daily(symbol, from_date, to_date) → HistoricalData
get_income_statement(symbol, period='annual') → FinancialData
get_balance_sheet(symbol) → FinancialData
get_cash_flow(symbol) → FinancialData
search_stocks(query, limit) → ScreenerResults
```

**Current Issues**:
- 🟡 No validation of FMP API responses
- 🟡 Assumes FMP always returns lists
- 🟡 Silent failures on malformed data
- 🟡 No schema for complex nested objects

**Usage Frequency**: HIGH (used by data_harvester for stock quotes)

**Pydantic Schema** (Proposed):
```python
class StockQuote(BaseModel):
    symbol: str = Field(..., regex=r'^[A-Z]{1,5}$')
    price: float = Field(..., gt=0)
    change: float
    change_percent: float = Field(..., alias='changesPercentage')
    volume: int = Field(..., ge=0)
    market_cap: int = Field(..., ge=0)
    day_low: float = Field(..., gt=0)
    day_high: float = Field(..., gt=0)
    year_low: float = Field(..., gt=0)
    year_high: float = Field(..., gt=0)
    pe: Optional[float] = Field(None, gt=0)
    eps: Optional[float]
    timestamp: int
    exchange: str

    @validator('day_high')
    def check_day_range(cls, v, values):
        if 'day_low' in values and v < values['day_low']:
            raise ValueError(f"day_high {v} < day_low {values['day_low']}")
        return v

    @validator('year_high')
    def check_year_range(cls, v, values):
        if 'year_low' in values and v < values['year_low']:
            raise ValueError(f"year_high {v} < year_low {values['year_low']}")
        return v

    class Config:
        allow_population_by_field_name = True  # Allow both 'change_percent' and 'changesPercentage'

class CompanyProfile(BaseModel):
    symbol: str
    company_name: str = Field(..., alias='companyName')
    exchange: str
    industry: Optional[str]
    sector: Optional[str]
    description: Optional[str]
    ceo: Optional[str]
    website: Optional[str]
    market_cap: int = Field(..., alias='mktCap')
    employees: Optional[int] = Field(None, alias='fullTimeEmployees')

    class Config:
        allow_population_by_field_name = True

class HistoricalPrice(BaseModel):
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)

    @validator('high')
    def validate_high_low(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError(f"high {v} < low {values['low']}")
        return v
```

**Migration Impact**: MEDIUM
- Used frequently by data_harvester
- FMP API is generally reliable
- Benefits: Catch malformed API responses early

---

### 3. NewsCapability (News Articles)

**API Methods**:
```python
get_news(symbols=None, limit=50) → List[Dict]
get_sentiment_news(symbols=None, limit=20) → List[Dict]
get_stock_news(symbol, limit=10) → List[Dict]
```

**Current Issues**:
- 🟡 No validation of news article structure
- 🟡 Sentiment scores not validated (-1 to 1 range)
- 🟡 Quality scores assumed but not enforced

**Pydantic Schema** (Proposed):
```python
class NewsArticle(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str]
    url: str = Field(..., regex=r'^https?://')
    published_at: datetime = Field(..., alias='publishedAt')
    source_name: str = Field(..., min_length=1)
    author: Optional[str]
    content: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, alias='urlToImage')
    sentiment: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: Literal['positive', 'neutral', 'negative']
    quality_score: float = Field(..., ge=0.0, le=1.0)
    symbols_mentioned: List[str] = []

    @validator('sentiment_label')
    def validate_sentiment_label_matches_score(cls, v, values):
        if 'sentiment' in values:
            score = values['sentiment']
            if v == 'positive' and score <= 0:
                raise ValueError(f"Label 'positive' but score {score} <= 0")
            elif v == 'negative' and score >= 0:
                raise ValueError(f"Label 'negative' but score {score} >= 0")
        return v

    class Config:
        allow_population_by_field_name = True

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    total_results: int = Field(..., ge=0)
    source: str
    timestamp: datetime

    @validator('total_results')
    def check_total_matches_articles(cls, v, values):
        if 'articles' in values and v != len(values['articles']):
            # Log warning but don't fail (total_results might be API-wide count)
            pass
        return v
```

**Migration Impact**: LOW
- News API usage is less critical than market data
- Mostly used for enrichment, not core functionality
- Benefits: Prevent bad sentiment scores from breaking analysis

---

### 4. PolygonOptionsCapability (Options Data)

**API Methods**:
```python
get_options_chain(symbol, expiration_date=None) → List[Dict]
get_options_activity(symbol, days=5) → List[Dict]
get_unusual_activity(min_volume=1000, min_premium=100000) → List[Dict]
```

**Current Issues**:
- 🟡 Complex nested structures not validated
- 🟡 Options greeks assumed but not type-checked
- 🟡 Expiration dates as strings, not validated

**Pydantic Schema** (Proposed):
```python
class OptionsGreeks(BaseModel):
    delta: float = Field(..., ge=-1.0, le=1.0)
    gamma: float = Field(..., ge=0.0)
    theta: float
    vega: float = Field(..., ge=0.0)
    rho: float
    implied_volatility: float = Field(..., ge=0.0, le=10.0, alias='iv')

    class Config:
        allow_population_by_field_name = True

class OptionsContract(BaseModel):
    symbol: str
    underlying_symbol: str = Field(..., alias='underlying')
    strike_price: float = Field(..., gt=0, alias='strike')
    expiration_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    option_type: Literal['call', 'put']
    bid: float = Field(..., ge=0)
    ask: float = Field(..., ge=0)
    last: Optional[float] = Field(None, ge=0)
    volume: int = Field(..., ge=0)
    open_interest: int = Field(..., ge=0)
    greeks: Optional[OptionsGreeks]

    @validator('ask')
    def validate_bid_ask_spread(cls, v, values):
        if 'bid' in values and v < values['bid']:
            raise ValueError(f"ask {v} < bid {values['bid']}")
        return v

    class Config:
        allow_population_by_field_name = True

class UnusualOptionsActivity(BaseModel):
    contract: OptionsContract
    unusual_volume: int = Field(..., gt=0)
    premium: float = Field(..., gt=0)
    sentiment: Literal['bullish', 'bearish', 'neutral']
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected_at: datetime

class OptionsChainResponse(BaseModel):
    underlying_symbol: str
    contracts: List[OptionsContract]
    timestamp: datetime
    source: str = 'polygon'

    @validator('contracts')
    def ensure_sorted_by_strike(cls, v):
        return sorted(v, key=lambda x: x.strike_price)
```

**Migration Impact**: LOW-MEDIUM
- Options trading features are advanced/optional
- Not used in critical paths
- Benefits: Prevent invalid greeks from causing calculation errors

---

### 5. FundamentalsCapability (Financial Statements)

**API Methods**:
```python
get_key_metrics(symbol) → Dict
get_financial_ratios(symbol) → Dict
get_earnings_calendar(from_date, to_date) → List[Dict]
```

**Current Issues**:
- 🟡 Financial ratios not range-validated
- 🟡 Negative values allowed where impossible (e.g., P/E < 0)
- 🟡 No validation of financial statement structure

**Pydantic Schema** (Proposed):
```python
class FinancialRatios(BaseModel):
    symbol: str
    pe_ratio: Optional[float] = Field(None, gt=0, alias='peRatio')
    price_to_book: Optional[float] = Field(None, gt=0, alias='priceToBookRatio')
    price_to_sales: Optional[float] = Field(None, gt=0, alias='priceToSalesRatio')
    roe: Optional[float] = Field(None, alias='returnOnEquity')  # Can be negative
    roa: Optional[float] = Field(None, alias='returnOnAssets')  # Can be negative
    roic: Optional[float] = Field(None, alias='returnOnCapitalEmployed')
    current_ratio: Optional[float] = Field(None, ge=0, alias='currentRatio')
    quick_ratio: Optional[float] = Field(None, ge=0, alias='quickRatio')
    debt_to_equity: Optional[float] = Field(None, ge=0, alias='debtToEquity')
    gross_margin: Optional[float] = Field(None, ge=-1.0, le=1.0, alias='grossProfitMargin')
    operating_margin: Optional[float] = Field(None, ge=-1.0, le=1.0, alias='operatingProfitMargin')
    net_margin: Optional[float] = Field(None, ge=-1.0, le=1.0, alias='netProfitMargin')
    dividend_yield: Optional[float] = Field(None, ge=0, le=1.0, alias='dividendYield')
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')

    class Config:
        allow_population_by_field_name = True

class KeyMetrics(BaseModel):
    symbol: str
    market_cap: int = Field(..., gt=0, alias='marketCap')
    pe_ratio: Optional[float] = Field(None, gt=0, alias='peRatio')
    revenue_per_share: Optional[float] = Field(None, alias='revenuePerShare')
    earnings_per_share: Optional[float] = Field(None, alias='eps')
    book_value_per_share: Optional[float] = Field(None, alias='bookValuePerShare')
    free_cash_flow_per_share: Optional[float] = Field(None, alias='freeCashFlowPerShare')
    date: str

    class Config:
        allow_population_by_field_name = True
```

**Migration Impact**: LOW
- Fundamentals used for analysis, not real-time trading
- Benefits: Prevent invalid ratios (e.g., negative P/E) from breaking DCF models

---

### 6. CryptoCapability (Cryptocurrency Prices)

**API Methods**:
```python
get_price(coin_id) → Dict
get_market_data(coin_ids) → List[Dict]
```

**Current Issues**:
- 🟡 Minimal validation
- 🟡 Not heavily used (crypto is secondary feature)

**Pydantic Schema** (Proposed):
```python
class CryptoPrice(BaseModel):
    id: str
    symbol: str = Field(..., regex=r'^[A-Z]+$')
    name: str
    current_price: float = Field(..., gt=0)
    market_cap: int = Field(..., gt=0)
    total_volume: int = Field(..., ge=0)
    price_change_24h: float
    price_change_percentage_24h: float
    last_updated: datetime

class CryptoMarketData(BaseModel):
    coins: List[CryptoPrice]
    timestamp: datetime
    source: str = 'coingecko'
```

**Migration Impact**: VERY LOW
- Crypto features are minimal
- Low usage priority
- Benefits: Consistency with other APIs

---

## 🎯 Standardization Strategy

### Approach: Incremental Pydantic Adoption

**Phase 1: Critical Path (Week 1-2)** ✅ HIGHEST PRIORITY
- FredDataCapability (already broken, needs immediate fix)
- MarketDataCapability (high usage, stock quotes critical)
- Impact: Fixes economic data + validates all stock quotes

**Phase 2: High Value (Week 3-4)**
- NewsCapability (prevent bad sentiment data)
- FundamentalsCapability (validate financial ratios)
- Impact: Prevents invalid data in analysis

**Phase 3: Optional (Week 5-6)**
- PolygonOptionsCapability (advanced features)
- CryptoCapability (low priority)
- Impact: Completeness, consistency

---

## 📐 Pydantic Architecture Design

### Unified Schema Package Structure

```
dawsos/
├── models/
│   ├── __init__.py
│   ├── base.py              # Base models, mixins
│   ├── economic_data.py      # FRED schemas
│   ├── market_data.py        # FMP stock schemas
│   ├── news.py               # News article schemas
│   ├── options.py            # Options contract schemas
│   ├── fundamentals.py       # Financial statement schemas
│   ├── crypto.py             # Cryptocurrency schemas
│   └── responses.py          # Common response wrappers
```

### Base Model Pattern

```python
# models/base.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper"""
    data: T
    source: str
    timestamp: datetime
    cache_age_seconds: int = Field(0, ge=0)
    error: Optional[str] = None

    class Config:
        frozen = True  # Immutable after creation

class DataQuality(BaseModel):
    """Data quality metadata"""
    completeness: float = Field(..., ge=0.0, le=1.0)
    freshness_seconds: int = Field(..., ge=0)
    source_reliability: float = Field(..., ge=0.0, le=1.0)
    validation_passed: bool

# models/responses.py
from models.base import APIResponse
from models.economic_data import EconomicDataResponse
from models.market_data import StockQuote

# Type aliases for common responses
EconomicAPIResponse = APIResponse[EconomicDataResponse]
StockQuoteResponse = APIResponse[StockQuote]
```

---

## 🔧 Implementation Pattern

### Step-by-Step Migration for Each Capability

**Example: MarketDataCapability.get_quote()**

**Before** (Unvalidated):
```python
def get_quote(self, symbol: str) -> QuoteData:
    """Get real-time quote"""
    url = f"{self.base_url}/quote/{symbol}?apikey={self.api_key}"
    data = self._make_api_call(url)

    if data and isinstance(data, list) and len(data) > 0:
        return data[0]  # Hope it's valid!
    return {}  # Silent failure
```

**After** (Pydantic Validated):
```python
from models.market_data import StockQuote, StockQuoteResponse
from pydantic import ValidationError

def get_quote(self, symbol: str) -> StockQuoteResponse:
    """Get real-time quote with validation"""
    url = f"{self.base_url}/quote/{symbol}?apikey={self.api_key}"
    raw_data = self._make_api_call(url)

    try:
        # Extract first element if list
        if isinstance(raw_data, list) and len(raw_data) > 0:
            raw_data = raw_data[0]

        # Validate with Pydantic
        quote = StockQuote(**raw_data)

        # Wrap in response
        return StockQuoteResponse(
            data=quote,
            source='fmp',
            timestamp=datetime.now(),
            cache_age_seconds=0
        )

    except ValidationError as e:
        logger.error(f"Quote validation failed for {symbol}: {e}")
        return StockQuoteResponse(
            data=None,  # Or raise exception
            source='fmp',
            timestamp=datetime.now(),
            error=f"Validation failed: {e}"
        )
```

**Benefits**:
1. ✅ Clear error messages when FMP API changes format
2. ✅ Type safety (IDE autocomplete for `quote.price`, `quote.volume`, etc.)
3. ✅ Automatic validation (day_high > day_low, volume >= 0, etc.)
4. ✅ Self-documenting (Pydantic model = API contract)
5. ✅ No silent failures

---

## 📈 Impact Assessment

### Benefits

**Immediate**:
- ✅ Fixes economic data system (remove double normalization)
- ✅ Catches malformed API responses before they corrupt the system
- ✅ Clear error messages instead of silent failures
- ✅ Type safety with IDE support

**Medium-term**:
- ✅ Self-documenting API contracts
- ✅ Easier debugging (validation errors pinpoint exact issue)
- ✅ Prevents data quality degradation
- ✅ Enables automatic schema documentation generation

**Long-term**:
- ✅ Confidence in data integrity
- ✅ Foundation for API versioning (Pydantic v1 vs v2 schemas)
- ✅ Easier onboarding (schemas show exactly what data looks like)
- ✅ Enables contract testing (schema violations = test failures)

### Risks

**Low Risk**:
- 🟢 Pydantic is battle-tested (used by FastAPI, SQLModel, etc.)
- 🟢 Incremental adoption (can migrate one capability at a time)
- 🟢 Backward compatible (old code continues to work)
- 🟢 Performance overhead is negligible (<1ms per validation)

**Medium Risk**:
- 🟡 Learning curve for team (Pydantic syntax, validators)
- 🟡 Initial time investment (writing schemas)
- 🟡 May expose existing bugs (currently silent)

**Mitigation**:
- Start with FredDataCapability (already broken, can't get worse)
- Provide code templates and examples
- Document common validation patterns
- Treat validation errors as success (they prevent bad data from propagating)

### Breaking Changes

**None** if implemented correctly:
- Old methods continue to return dicts
- New methods return Pydantic models
- Pydantic models can be converted to dicts with `.dict()`
- Gradual migration: validate at boundaries, convert internally

---

## 🚀 Recommended Implementation Order

### Week 1: Foundation
- [ ] Install Pydantic: `pip install pydantic`
- [ ] Create `models/` package structure
- [ ] Create base models (`base.py`, `responses.py`)
- [ ] Write Pydantic documentation guide for team

### Week 2: Critical Fix
- [ ] Implement `models/economic_data.py`
- [ ] Update FredDataCapability to validate responses
- [ ] Update PatternEngine to consume validated data (remove normalizer)
- [ ] Integration tests for economic data flow
- [ ] **Deploy fix** (economic dashboard works again)

### Week 3: High-Value APIs
- [ ] Implement `models/market_data.py`
- [ ] Update MarketDataCapability.get_quote() with validation
- [ ] Implement `models/news.py`
- [ ] Update NewsCapability with sentiment validation

### Week 4: Remaining APIs
- [ ] Implement `models/fundamentals.py`
- [ ] Implement `models/options.py`
- [ ] Implement `models/crypto.py`

### Week 5: Testing & Documentation
- [ ] Schema validation tests for all models
- [ ] Contract tests (API response → schema)
- [ ] Generate JSON schemas from Pydantic models
- [ ] API documentation with schema examples

### Week 6: Cleanup
- [ ] Remove deprecated normalizer functions
- [ ] Update all agent code to use validated responses
- [ ] Performance benchmarks
- [ ] Final documentation update

---

## 💡 Alternative: Specialized Agents

**Question**: Can we use specialized agents instead of normalizer?

**Answer**: No, but Pydantic is better.

### Why Specialized Agents Don't Solve This:

**Current Problem**: Double normalization (capability + normalizer)

**Specialized Agent Approach**:
```
API → Capability → NormalizerAgent → PatternEngine
```

**Issues**:
1. ❌ Still have two transformation steps (capability + agent)
2. ❌ Agents are for business logic, not data transformation
3. ❌ Adds another layer (more complexity, not less)
4. ❌ Doesn't provide type safety or validation

**Pydantic Approach**:
```
API → Capability (with Pydantic validation) → PatternEngine
```

**Benefits**:
1. ✅ Single transformation point (capability layer)
2. ✅ Type safety + validation at the boundary
3. ✅ Simpler architecture (fewer layers)
4. ✅ Self-documenting (schemas = contracts)

### When Specialized Agents ARE Appropriate:

Specialized agents should handle **business logic**, not data normalization:

**Good Use Cases**:
- `SentimentAnalysisAgent` - Analyzes news sentiment (business logic)
- `RiskCalculationAgent` - Calculates portfolio risk metrics (business logic)
- `TrendDetectionAgent` - Identifies market trends (business logic)

**Bad Use Cases**:
- `DataNormalizerAgent` - Just transforms data format ❌ (use Pydantic)
- `ValidationAgent` - Just validates structure ❌ (use Pydantic)
- `APIParserAgent` - Just parses API responses ❌ (use Pydantic)

**Rule of Thumb**:
- **Data transformation = Pydantic** (at capability layer)
- **Business logic = Specialized Agent** (after data is validated)

---

## 📊 Success Metrics

After full Pydantic migration:

1. ✅ **Zero silent API failures** - All validation errors logged with clear messages
2. ✅ **100% type coverage** - All API responses have Pydantic schemas
3. ✅ **Automatic schema docs** - Generate JSON schemas for API contracts
4. ✅ **Economic data works** - FRED integration functional end-to-end
5. ✅ **Faster debugging** - Validation errors pinpoint exact field/value issue
6. ✅ **Developer confidence** - IDE autocomplete + type checking for all API data
7. ✅ **Contract testing** - Schema violations caught in CI/CD

---

## 📚 Resources

### Pydantic Documentation
- Official docs: https://docs.pydantic.dev/
- FastAPI integration: https://fastapi.tiangolo.com/tutorial/body/
- Best practices: https://docs.pydantic.dev/latest/concepts/models/

### Example Projects Using Pydantic
- FastAPI (web framework)
- SQLModel (ORM)
- LangChain (LLM framework)
- Prefect (workflow orchestration)

### Code Templates

See `ARCHITECTURE_SIMPLIFICATION_PLAN.md` for detailed code examples.

---

**Next Steps**:
1. Get team buy-in on Pydantic approach
2. Install Pydantic and create models/ package
3. Implement FredDataCapability validation (fixes broken economic data)
4. Write integration tests
5. Incremental rollout to other capabilities
