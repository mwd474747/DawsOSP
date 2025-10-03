# Knowledge Maintenance Guide

This guide documents the format, storage, and refresh process for enriched
datasets used by the KnowledgeLoader and Trinity patterns.

---

## Dataset Format

All files live under `dawsos/storage/knowledge/` and must be valid JSON with a
top-level `_meta` header:

```json
{
  "_meta": {
    "dataset": "factor_smartbeta_profiles",
    "version": "1.0",
    "as_of": "2025-10-03",
    "notes": "Brief methodology / units"
  },
  "entities": { ... }
}
```

**Requirements**
- `_meta.dataset` matches the key registered in `KnowledgeLoader.datasets`.
- `version` and `as_of` help patterns decide freshness; update for each refresh.
- Dataset body can be a dictionary or list, but should be structured so patterns
  can query sections directly (e.g., `entities.XLK.scores`).

---

## Adding / Refreshing a Dataset

1. Place the new JSON file in `dawsos/storage/knowledge/`.
2. Register it in `KnowledgeLoader.datasets` (e.g., `'earnings_surprises': 'earnings_surprises.json'`).
3. Implement a simple validator in `KnowledgeLoader` (e.g., `_validate_earnings_surprises`).
4. Update `_meta.as_of` and `version`.
5. Run the loader smoke test:
   ```bash
   python3 - <<'PY'
   from core.knowledge_loader import KnowledgeLoader
   loader = KnowledgeLoader()
   data = loader.get_dataset('earnings_surprises')
   assert data is not None
   PY
   ```
6. Update documentation or pattern references as needed.

---

## Loader API (Quick Reference)

```python
from core.knowledge_loader import load_dataset, get_knowledge_loader

data = load_dataset('factor_smartbeta_profiles')
section = get_knowledge_loader().get_dataset_section('factor_smartbeta_profiles', 'entities.XLK.scores')
info = get_knowledge_loader().get_dataset_info('factor_smartbeta_profiles')
```

- Cache TTL defaults to 30 minutes; use `force_reload=True` to bypass cache.
- `get_stale_datasets()` lists cached datasets older than the TTL.
- `clear_cache()` removes cached entries (single dataset or all).

---

## Refresh Cadence & Ownership

- **Static frameworks** (Buffett, Dalio, calculation formulas) rarely change—update when methodology evolves.
- **Market datasets** (factor profiles, earnings surprises, yield curves) should be refreshed periodically. Document the data source and cadence in `_meta.notes`.
- When automating refreshes, add a script (e.g., `scripts/update_enriched_data.py`) that downloads data, writes `_meta` timestamps, and runs loader validation.

---

## Validation Checklist

- JSON is valid and human-readable (pretty printed).
- `_meta.dataset` matches loader registry entry.
- `as_of` uses ISO date (`YYYY-MM-DD`).
- Patterns referencing the dataset succeed (use `scripts/lint_patterns.py`).
- Data types are consistent (numbers vs strings).

---

## Troubleshooting

- **Loader returns `None`**: Check registry entry and `_meta.dataset` name.
- **Validation fails**: Review `_validate_*` methods in `knowledge_loader.py`.
- **Stale data**: Check `get_dataset_info(name)` for `cache_age_seconds` and trigger `force_reload=True`.

