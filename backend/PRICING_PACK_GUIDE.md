# Pricing Pack Guide

Technical reference for pricing pack operations.

## Usage

```python
from backend.app.db.pricing_pack_queries import get_latest_pack
pack = await get_latest_pack()
```

## API Reference

- `get_latest_pack()` - Get most recent pricing pack
- `create_pricing_pack()` - Create new pricing pack
- `update_pack_status()` - Update pack freshness status
