# Symbol Format Standards

**Created**: 2025-11-06
**Status**: Active
**Priority**: P0 (Critical for API integration)

---

## Overview

This document defines how DawsOS handles stock ticker symbols across different contexts: database storage, API providers (FMP, NewsAPI), and user interfaces.

**Key Principle**: Symbols are stored in their canonical form in the database but converted to provider-specific formats when making external API calls.

---

## Symbol Format Rules

### 1. Database Storage Format

**Rule**: Store symbols in their canonical format with dots for both share classes and exchange suffixes.

**Examples**:
- `AAPL` - Apple (standard US stock)
- `BRK.B` - Berkshire Hathaway Class B (share class)
- `BRK.A` - Berkshire Hathaway Class A (share class)
- `RY.TO` - Royal Bank (Toronto Stock Exchange)
- `TD.TO` - TD Bank (Toronto Stock Exchange)
- `HSBC.L` - HSBC (London Stock Exchange)

**Schema**:
```sql
CREATE TABLE securities (
    id UUID PRIMARY KEY,
    symbol TEXT NOT NULL,           -- Stored with dots: "BRK.B", "RY.TO"
    exchange TEXT,                  -- "NASDAQ", "NYSE", "TSX", "LSE"
    trading_currency TEXT,          -- "USD", "CAD", "GBP"
    dividend_currency TEXT          -- For ADRs where dividend currency differs
);

CREATE UNIQUE INDEX idx_securities_symbol ON securities(symbol);
```

**Normalization for Storage**:
```python
from app.core.symbol_utils import normalize_symbol_for_storage

# Uppercase and trim whitespace
normalized = normalize_symbol_for_storage(" brk.b ")  # Returns "BRK.B"
```

---

### 2. FMP API Format

**Rule**: Financial Modeling Prep (FMP) uses **hyphens for share classes** but **dots for exchange suffixes**.

**FMP Symbol Format**:
- Share classes: Use hyphens (`.` → `-`)
  - `BRK.B` → `BRK-B`
  - `BRK.A` → `BRK-A`
- Exchange suffixes: Keep dots unchanged
  - `RY.TO` → `RY.TO` (Toronto)
  - `HSBC.L` → `HSBC.L` (London)
- Standard symbols: Unchanged
  - `AAPL` → `AAPL`

**API Endpoints**:
```
GET https://financialmodelingprep.com/api/v3/profile/BRK-B?apikey=...
GET https://financialmodelingprep.com/api/v3/profile/RY.TO?apikey=...
GET https://financialmodelingprep.com/api/v3/income-statement/BRK-B?apikey=...
```

**Usage in Code**:
```python
from app.core.symbol_utils import normalize_symbol_for_fmp

# Automatic normalization for FMP API calls
db_symbol = "BRK.B"
fmp_symbol = normalize_symbol_for_fmp(db_symbol)  # Returns "BRK-B"

db_symbol = "RY.TO"
fmp_symbol = normalize_symbol_for_fmp(db_symbol)  # Returns "RY.TO"
```

**Implementation**: [data_harvester.py:689](backend/app/agents/data_harvester.py#L689)

---

### 3. News Search Format

**Rule**: News APIs (NewsAPI, etc.) use **hyphens for all dots** to improve search matching.

**News Symbol Format**:
- All dots converted to hyphens
  - `BRK.B` → `BRK-B`
  - `RY.TO` → `RY-TO`
  - `HSBC.L` → `HSBC-L`

**Rationale**: News articles often use hyphens in company names and stock mentions, so converting symbols to hyphens improves search recall.

**Usage in Code**:
```python
from app.core.symbol_utils import normalize_symbol_for_news

# For news search queries
db_symbol = "RY.TO"
news_symbol = normalize_symbol_for_news(db_symbol)  # Returns "RY-TO"
```

**Implementation**: [data_harvester.py:1742](backend/app/agents/data_harvester.py#L1742)

---

## Symbol Types

### Share Class Symbols

**Definition**: Stocks with multiple share classes (e.g., voting vs non-voting, different dividend rights).

**Format**: Single letter after dot (`.A`, `.B`, `.C`)

**Examples**:
- `BRK.A` - Berkshire Hathaway Class A
- `BRK.B` - Berkshire Hathaway Class B
- `GOOGL` - Alphabet Class A (no suffix for primary class)
- `GOOG` - Alphabet Class C

**Database Treatment**:
- Each share class is a separate security with unique `security_id`
- No automatic linking between share classes
- Each class has separate price history, fundamentals

**FMP API**: Convert dot to hyphen (`BRK.B` → `BRK-B`)

---

### Exchange Suffix Symbols

**Definition**: Stocks traded on non-US exchanges identified by exchange code suffix.

**Format**: 1-3 character exchange code after dot

**Supported Exchanges**:

| Suffix | Exchange | Country |
|--------|----------|---------|
| `.TO` | Toronto Stock Exchange | Canada |
| `.V` | TSX Venture Exchange | Canada |
| `.CN` | Canadian Securities Exchange | Canada |
| `.L` | London Stock Exchange | UK |
| `.PA` | Euronext Paris | France |
| `.AS` | Euronext Amsterdam | Netherlands |
| `.BR` | Euronext Brussels | Belgium |
| `.DE` | Deutsche Börse | Germany |
| `.F` | Frankfurt Stock Exchange | Germany |
| `.SW` | SIX Swiss Exchange | Switzerland |
| `.MI` | Borsa Italiana | Italy |
| `.MC` | Bolsa de Madrid | Spain |
| `.HK` | Hong Kong Stock Exchange | Hong Kong |
| `.T` | Tokyo Stock Exchange | Japan |
| `.KS` | Korea Stock Exchange | South Korea |
| `.SI` | Singapore Exchange | Singapore |
| `.AX` | Australian Securities Exchange | Australia |
| `.ME` | Moscow Exchange | Russia |
| `.SA` | Bovespa | Brazil |

**FMP API**: Keep dot unchanged (`RY.TO` → `RY.TO`)

---

### Standard Symbols

**Definition**: US stocks with no suffix.

**Format**: 1-5 uppercase letters

**Examples**:
- `AAPL` - Apple
- `MSFT` - Microsoft
- `GOOGL` - Alphabet

**All Formats**: Unchanged across all contexts

---

## Symbol Validation

### Validation Rules

1. **Length**: 1-10 characters
2. **Characters**: A-Z, 0-9, dots only
3. **Letters**: Must contain at least one letter
4. **Dot Position**: Cannot start or end with dot
5. **Consecutive Dots**: Not allowed

### Validation Function

```python
from app.core.symbol_utils import validate_symbol

# Valid symbols
is_valid, error = validate_symbol("AAPL")        # (True, None)
is_valid, error = validate_symbol("BRK.B")       # (True, None)
is_valid, error = validate_symbol("RY.TO")       # (True, None)

# Invalid symbols
is_valid, error = validate_symbol("")            # (False, "Symbol cannot be empty")
is_valid, error = validate_symbol(".AAPL")       # (False, "Symbol cannot start with dot")
is_valid, error = validate_symbol("123")         # (False, "Must contain at least one letter")
is_valid, error = validate_symbol("TOOLONG123") # (False, "Symbol too long (max 10 characters)")
```

---

## Symbol Detection

### Auto-Detect Symbol Type

```python
from app.core.symbol_utils import detect_symbol_type

symbol_type = detect_symbol_type("BRK.B")   # Returns "share_class"
symbol_type = detect_symbol_type("RY.TO")   # Returns "exchange"
symbol_type = detect_symbol_type("AAPL")    # Returns "standard"
```

**Use Cases**:
- UI display (show different icons for share classes vs exchanges)
- Validation (ensure exchange suffixes are valid)
- Analytics (group securities by type)

---

## ADR Handling

**Definition**: American Depositary Receipts (ADRs) are US-traded securities representing shares of foreign companies.

**Database Support**:
- `trading_currency` - Currency the ADR trades in (usually USD)
- `dividend_currency` - Currency dividends are paid in (often foreign currency)
- `domicile_country` - Country of the underlying company

**Example**:
```sql
INSERT INTO securities (symbol, trading_currency, dividend_currency, domicile_country)
VALUES ('HSBC', 'USD', 'GBP', 'GB');  -- HSBC ADR trades in USD, dividends in GBP
```

**Symbol Format**: ADRs typically use standard US symbols without suffixes (e.g., `HSBC`, not `HSBC.L`)

---

## Migration Guide

### For New Code

**Always use utility functions** instead of manual string replacement:

```python
# ❌ DON'T DO THIS
fmp_symbol = symbol.replace(".", "-")  # Wrong for Canadian stocks!

# ✅ DO THIS
from app.core.symbol_utils import normalize_symbol_for_fmp
fmp_symbol = normalize_symbol_for_fmp(symbol)
```

### For Existing Code

**Search for**:
```python
symbol.replace(".", "-")
symbol.replace(".", " ")
symbol.split(".")[0]
```

**Replace with**:
```python
from app.core.symbol_utils import normalize_symbol_for_fmp, normalize_symbol_for_news

# For FMP API calls
fmp_symbol = normalize_symbol_for_fmp(symbol)

# For news search
news_symbol = normalize_symbol_for_news(symbol)
```

---

## Common Mistakes

### ❌ Mistake 1: Converting All Dots to Hyphens for FMP

```python
# WRONG - Breaks Canadian stocks
fmp_symbol = symbol.replace(".", "-")
# "RY.TO" -> "RY-TO" (FMP will return 404)
```

```python
# CORRECT
from app.core.symbol_utils import normalize_symbol_for_fmp
fmp_symbol = normalize_symbol_for_fmp(symbol)
# "RY.TO" -> "RY.TO" (preserves exchange suffix)
# "BRK.B" -> "BRK-B" (converts share class)
```

### ❌ Mistake 2: Using Hyphens in Database

```python
# WRONG - Store canonical format
INSERT INTO securities (symbol) VALUES ('BRK-B');
```

```python
# CORRECT
INSERT INTO securities (symbol) VALUES ('BRK.B');
```

### ❌ Mistake 3: Not Validating Symbols

```python
# WRONG - No validation
INSERT INTO securities (symbol) VALUES (user_input);
```

```python
# CORRECT
from app.core.symbol_utils import validate_symbol, normalize_symbol_for_storage

is_valid, error = validate_symbol(user_input)
if not is_valid:
    raise ValueError(f"Invalid symbol: {error}")

normalized = normalize_symbol_for_storage(user_input)
INSERT INTO securities (symbol) VALUES (normalized);
```

---

## Testing

### Unit Tests

```python
# Test symbol normalization
from app.core.symbol_utils import normalize_symbol_for_fmp

def test_fmp_normalization():
    assert normalize_symbol_for_fmp("BRK.B") == "BRK-B"   # Share class
    assert normalize_symbol_for_fmp("RY.TO") == "RY.TO"   # Exchange
    assert normalize_symbol_for_fmp("AAPL") == "AAPL"     # Standard
```

### Integration Tests

```python
# Test FMP API call with normalized symbol
async def test_fmp_fundamentals():
    from app.integrations.fmp_provider import FMPProvider
    from app.core.symbol_utils import normalize_symbol_for_fmp

    provider = FMPProvider(api_key=API_KEY)

    # Test share class
    symbol = "BRK.B"
    fmp_symbol = normalize_symbol_for_fmp(symbol)  # "BRK-B"
    data = await provider.get_company_profile(fmp_symbol)
    assert data["symbol"] == "BRK-B"

    # Test Canadian stock
    symbol = "RY.TO"
    fmp_symbol = normalize_symbol_for_fmp(symbol)  # "RY.TO"
    data = await provider.get_company_profile(fmp_symbol)
    assert data["symbol"] == "RY.TO"
```

---

## References

### Code Files
- [app/core/symbol_utils.py](backend/app/core/symbol_utils.py) - Symbol normalization utilities
- [app/agents/data_harvester.py](backend/app/agents/data_harvester.py) - FMP and news API integration
- [app/integrations/fmp_provider.py](backend/app/integrations/fmp_provider.py) - FMP API client
- [backend/db/schema/pricing_packs.sql](backend/db/schema/pricing_packs.sql) - Securities table schema

### External Documentation
- [FMP API Documentation](https://site.financialmodelingprep.com/developer/docs)
- [FMP Symbol Search](https://site.financialmodelingprep.com/developer/docs/stable/search-symbol)
- [FMP TSX Documentation](https://site.financialmodelingprep.com/developer/docs/tsx-prices-api)

### Analysis Documents
- Symbol handling analysis (this session, 2025-11-06)
- FMP API research findings (web search results)

---

## Changelog

**2025-11-06** - Initial documentation
- Created symbol normalization utilities
- Fixed FMP API symbol conversion bug
- Documented exchange suffix handling
- Added validation functions

---

**End of Symbol Format Standards**
