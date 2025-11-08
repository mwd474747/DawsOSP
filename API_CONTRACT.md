# API Contract Documentation

**⚠️ HISTORICAL DOCUMENT**  
*Version 1.0 - November 4, 2025*  
**Note:** This is a historical progress document. Numbers may be outdated. See [ARCHITECTURE.md](../ARCHITECTURE.md) for current specifications.

## Overview

This document defines the contract between the DawsOS backend (Replit) and frontend (Claude) during the field naming standardization refactor.

## Field Naming Convention

### Current State (Updated January 14, 2025)
- **Backend (Python/Database)**: snake_case ✅
- **Frontend (JavaScript/React)**: camelCase ⚠️
- **Agent Layer**: Standardized to `quantity` (not `qty` or `quantity_open`) ✅
- **Database Layer**: Uses `quantity_open`, `quantity_original` (columns) ✅

### Target State  
- **Both**: snake_case everywhere
- **Agent Layer**: Continue using `quantity` (standardized)
- **Database Layer**: Continue using `quantity_open`, `quantity_original` (columns)

### Transition Strategy
Using a compatibility layer controlled by environment variable:
```bash
USE_FIELD_COMPATIBILITY=true   # During migration
USE_FIELD_COMPATIBILITY=false  # After migration complete
```

## Field Mapping Reference

| Frontend (camelCase) | Backend (snake_case) | Data Type | Description |
|---------------------|---------------------|-----------|-------------|
| portfolioId | portfolio_id | UUID | Portfolio identifier |
| userId | user_id | UUID | User identifier |
| userName | user_name | string | User display name |
| createdAt | created_at | timestamp | Creation timestamp |
| updatedAt | updated_at | timestamp | Update timestamp |
| deletedAt | deleted_at | timestamp | Soft delete timestamp |
| isActive | is_active | boolean | Active status flag |
| marketValue | market_value | decimal | Current market value |
| totalValue | total_value | decimal | Total portfolio value |
| costBasis | cost_basis | decimal | Original cost basis |
| unrealizedGain | unrealized_gain | decimal | Unrealized P&L |
| realizedGain | realized_gain | decimal | Realized P&L |
| assetClass | asset_class | string | Asset classification |
| securityType | security_type | string | Security type |
| tickerSymbol | ticker_symbol | string | Trading symbol |
| sharpeRatio | sharpe_ratio | decimal | Risk-adjusted return |
| maxDrawdown | max_drawdown | decimal | Maximum drawdown |
| annualReturn | annual_return | decimal | Annualized return |
| startDate | start_date | date | Period start date |
| endDate | end_date | date | Period end date |
| tradeDate | trade_date | date | Transaction date |
| baseCurrency | base_currency | string | Base currency code |
| exchangeRate | exchange_rate | decimal | FX conversion rate |
| lookbackDays | lookback_days | integer | Historical period |

## API Endpoints

### Pattern Execution
**POST** `/api/patterns/execute`

#### Request (with compatibility)
```json
{
  "patternId": "portfolio_overview",
  "inputs": {
    "portfolioId": "123e4567-e89b-12d3-a456-426614174000",
    "lookbackDays": 252
  }
}
```

#### Request (target state)
```json
{
  "pattern_id": "portfolio_overview",
  "inputs": {
    "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
    "lookback_days": 252
  }
}
```

#### Response (with compatibility)
```json
{
  "status": "success",
  "data": {
    "portfolioId": "123e4567-e89b-12d3-a456-426614174000",
    "perfMetrics": {
      "sharpeRatio": 1.25,
      "maxDrawdown": -0.15
    }
  }
}
```

#### Response (target state)
```json
{
  "status": "success",
  "data": {
    "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
    "perf_metrics": {
      "sharpe_ratio": 1.25,
      "max_drawdown": -0.15
    }
  }
}
```

### Authentication
**POST** `/api/auth/login`

#### Request
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Response (with compatibility)
```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "userName": "John Doe"
}
```

#### Response (target state)
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_name": "John Doe"
}
```

### Portfolio Holdings
**GET** `/api/holdings?portfolio_id={id}`

#### Response (with compatibility)
```json
{
  "holdings": [
    {
      "securityId": "abc123",
      "tickerSymbol": "AAPL",
      "marketValue": 10000.00,
      "costBasis": 8000.00,
      "unrealizedGain": 2000.00
    }
  ],
  "totalValue": 10000.00
}
```

#### Response (target state)
```json
{
  "holdings": [
    {
      "security_id": "abc123",
      "ticker_symbol": "AAPL",
      "market_value": 10000.00,
      "cost_basis": 8000.00,
      "unrealized_gain": 2000.00
    }
  ],
  "total_value": 10000.00
}
```

## Error Response Format

### Standard Error Structure
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid portfolio ID format",
    "field": "portfolio_id",
    "timestamp": "2025-11-04T10:30:00Z"
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid input data |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMIT | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

## Headers

### Required Request Headers
```http
Content-Type: application/json
Authorization: Bearer {token}
```

### Response Headers
```http
Content-Type: application/json
X-Request-Id: {uuid}
X-Rate-Limit-Remaining: {number}
```

## Migration Timeline

### Phase 1: Backend Ready (Days 1-4)
- Compatibility layer implemented
- All endpoints accept both formats
- Returns format based on USE_FIELD_COMPATIBILITY flag

### Phase 2: Frontend Migration (Days 5-10)  
- Frontend gradually updates to snake_case
- Tests against backend with compatibility layer
- Backend continues accepting both formats

### Phase 3: Compatibility Removal (Day 15)
- Set USE_FIELD_COMPATIBILITY=false
- Backend only accepts/returns snake_case
- Frontend fully migrated

## Testing Requirements

### Backend Tests
```python
# Test both input formats work
def test_camelCase_input():
    response = post("/api/patterns/execute", {
        "patternId": "test",
        "portfolioId": "123"
    })
    assert response.status == 200

def test_snake_case_input():
    response = post("/api/patterns/execute", {
        "pattern_id": "test",
        "portfolio_id": "123"
    })
    assert response.status == 200
```

### Frontend Tests
```javascript
// Test handling both response formats
test('handles camelCase response', () => {
  const response = { portfolioId: '123' };
  expect(parseResponse(response)).toBeDefined();
});

test('handles snake_case response', () => {
  const response = { portfolio_id: '123' };
  expect(parseResponse(response)).toBeDefined();
});
```

## Coordination Protocol

### Daily Sync Points
1. **Morning**: Backend reports compatibility layer status
2. **Midday**: Frontend reports migration progress
3. **Evening**: Joint testing of migrated components

### Communication Channels
- Progress updates in `MIGRATION_STATUS.md`
- Issues logged in `MIGRATION_ISSUES.md`
- Success metrics tracked in `MIGRATION_METRICS.md`

## Rollback Procedures

### Backend Rollback
```bash
# Immediate rollback - re-enable compatibility
export USE_FIELD_COMPATIBILITY=true
systemctl restart dawsos-backend
```

### Frontend Rollback
```javascript
// Re-enable camelCase handling
window.USE_LEGACY_FIELDS = true;
```

## Success Criteria

- [ ] Zero field-related errors in production
- [ ] All 13 patterns execute successfully
- [ ] Frontend components handle both formats
- [ ] Performance impact < 5ms per request
- [ ] All tests passing (backend + frontend)

## Contact for Issues

**Backend (Replit Agent)**: Update this document with any changes
**Frontend (Claude Agent)**: Reference this for field mappings

## Appendix: Common Patterns

### List/Array Fields
```javascript
// Frontend (current)
portfolioIds: ['id1', 'id2']
securityTypes: ['STOCK', 'BOND']

// Target
portfolio_ids: ['id1', 'id2']
security_types: ['STOCK', 'BOND']
```

### Nested Objects
```javascript
// Frontend (current)
{
  userData: {
    userId: '123',
    userName: 'John'
  }
}

// Target
{
  user_data: {
    user_id: '123',
    user_name: 'John'
  }
}
```

### Boolean Flags
```javascript
// Frontend (current)
isActive: true
hasAlerts: false

// Target  
is_active: true
has_alerts: false
```