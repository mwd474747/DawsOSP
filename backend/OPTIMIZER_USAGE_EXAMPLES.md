# Optimizer Usage Examples

Examples of using the portfolio optimizer service.

## Basic Usage

```python
from backend.app.services.optimizer import get_optimizer_service

optimizer = get_optimizer_service()
result = await optimizer.optimize_portfolio(portfolio_id, constraints)
```

## Advanced Examples

See the optimizer service implementation for detailed examples.
