# Field Naming Inconsistency Audit
*Generated November 4, 2025*

## Current State: Mixed Naming Conventions

### Frontend (JavaScript/React) - camelCase
Found in `full_ui.html`:
- `portfolioId` (should be `portfolio_id`)
- `userId` (should be `user_id`)
- `createdAt` (should be `created_at`)
- `updatedAt` (should be `updated_at`)
- `assetClass` (should be `asset_class`)
- `totalValue` (should be `total_value`)
- `marketValue` (should be `market_value`)

### Backend (Python) - snake_case
Found in backend Python files:
- `portfolio_id` ✅
- `user_id` ✅
- `created_at` ✅
- `updated_at` ✅
- `asset_class` ✅
- `total_value` ✅
- `market_value` ✅

## Impact Analysis

### Frontend Files Affected
- **full_ui.html**: 72+ occurrences of camelCase fields
  - React components using camelCase state
  - API calls converting between formats
  - Chart configurations with camelCase

### Backend Files Affected (if we need compatibility)
- **combined_server.py**: Main server file
- **Pattern JSON files**: 13 files in `backend/patterns/`
- **Agent files**: 4 agent implementations
- **Service layer**: 15+ service files

## Recommended Approach

### Option 1: Fix Frontend (RECOMMENDED)
**Convert all frontend camelCase to snake_case to match backend**

Pros:
- Backend already consistent with Python conventions
- Database uses snake_case
- One-time frontend refactor

Cons:
- Large frontend refactor (72+ locations)
- Risk of missing some references

### Option 2: Add Compatibility Layer
**Keep both, add translation layer**

```python
# Backend compatibility layer
def to_camel_case(snake_dict):
    """Convert snake_case keys to camelCase for frontend"""
    return {to_camel(k): v for k, v in snake_dict.items()}

def to_snake_case(camel_dict):
    """Convert camelCase keys to snake_case for backend"""
    return {to_snake(k): v for k, v in camel_dict.items()}
```

Pros:
- No immediate breaking changes
- Gradual migration possible

Cons:
- Performance overhead
- Complexity increase
- Technical debt

## Conversion Mapping

```javascript
// Frontend field conversions needed
const FIELD_MAPPING = {
  // User & Portfolio
  'portfolioId': 'portfolio_id',
  'userId': 'user_id',
  'userName': 'user_name',
  
  // Timestamps
  'createdAt': 'created_at',
  'updatedAt': 'updated_at',
  'deletedAt': 'deleted_at',
  
  // Financial fields
  'marketValue': 'market_value',
  'totalValue': 'total_value',
  'costBasis': 'cost_basis',
  'unrealizedGain': 'unrealized_gain',
  'realizedGain': 'realized_gain',
  
  // Asset fields
  'assetClass': 'asset_class',
  'securityType': 'security_type',
  'tickerSymbol': 'ticker_symbol',
  
  // Metrics
  'sharpeRatio': 'sharpe_ratio',
  'maxDrawdown': 'max_drawdown',
  'annualReturn': 'annual_return',
  
  // Dates
  'startDate': 'start_date',
  'endDate': 'end_date',
  'tradeDate': 'trade_date',
  
  // Other
  'isActive': 'is_active',
  'baseCurrency': 'base_currency',
  'exchangeRate': 'exchange_rate'
};
```

## Migration Strategy

### Step 1: Create Compatibility Layer (Day 1)
```javascript
// frontend/utils/fieldConverter.js
function toSnakeCase(obj) {
  // Convert all keys from camelCase to snake_case
}

function toCamelCase(obj) {
  // Convert all keys from snake_case to camelCase
}
```

### Step 2: Update API Client (Day 2)
```javascript
// Wrap all API responses
const response = await fetch(url);
const data = await response.json();
return toCamelCase(data);  // Temporarily keep frontend as camelCase
```

### Step 3: Gradual Frontend Migration (Days 3-5)
- Update components one by one
- Test each component after update
- Remove compatibility layer when done

## Validation Checklist

### Pre-migration
- [ ] Full backup of database
- [ ] Document all field mappings
- [ ] Create test suite for field names
- [ ] Set up staging environment

### During migration
- [ ] Update frontend API client
- [ ] Update React components
- [ ] Update chart configurations
- [ ] Update pattern renderer
- [ ] Test all 13 patterns

### Post-migration
- [ ] Remove compatibility layer
- [ ] Performance testing
- [ ] Update documentation
- [ ] Production deployment

## Risk Mitigation

1. **Use Feature Flag**
```javascript
const USE_SNAKE_CASE = process.env.REACT_APP_USE_SNAKE_CASE === 'true';
const fieldName = USE_SNAKE_CASE ? 'portfolio_id' : 'portfolioId';
```

2. **Automated Testing**
```javascript
// Test both naming conventions work
test('field naming compatibility', () => {
  const camelData = { portfolioId: '123' };
  const snakeData = toSnakeCase(camelData);
  expect(snakeData.portfolio_id).toBe('123');
});
```

3. **Rollback Plan**
- Keep compatibility layer for 2 weeks post-deployment
- Monitor error rates
- Quick revert if issues arise

## Estimated Effort

- **Audit & Mapping**: 4 hours ✅ (DONE)
- **Compatibility Layer**: 4 hours
- **Frontend Updates**: 16 hours (2 days)
- **Testing**: 8 hours (1 day)
- **Deployment**: 4 hours

**Total**: 36 hours (4-5 days)

## Priority

**CRITICAL** - This blocks all other refactoring work

Must be completed before:
- Database migration 014/015
- Pattern system updates
- Performance optimization
- Any other system changes

## Next Actions

1. **Immediate**: Implement compatibility layer (prevents breaks)
2. **Day 1-2**: Update frontend API client
3. **Day 3-4**: Migrate React components
4. **Day 5**: Testing and validation
5. **Day 6**: Production deployment