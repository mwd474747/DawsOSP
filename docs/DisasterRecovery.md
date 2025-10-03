# Disaster Recovery Guide

This document outlines the procedures for backing up, verifying, and restoring
the DawsOS knowledge graph and related state.

---

## Backup Overview

Backups are managed by `core/persistence.py`:
- Graph saved to `dawsos/storage/graph.json` with sidecar metadata
  (`graph.json.meta`), including checksum, node/edge counts, and timestamp.
- Timestamped backups in `dawsos/storage/backups/graph_YYYYMMDD_HHMMSS.json`
  with corresponding `.meta` files.
- 30-day retention by default (see `PersistenceManager._rotate_backups`).

### Manual Backup

```python
from core.persistence import PersistenceManager
from core.knowledge_graph import KnowledgeGraph

graph = KnowledgeGraph()
graph.load('dawsos/storage/graph.json')
pm = PersistenceManager(base_path='dawsos/storage')
stats = pm.save_graph_with_backup(graph)
print(stats['backup_path'])
```

---

## Integrity Verification

Each backup has a SHA-256 checksum stored in its `.meta` file. To verify:

```python
from core.persistence import PersistenceManager
pm = PersistenceManager(base_path='dawsos/storage')
check = pm.verify_integrity('dawsos/storage/backups/graph_20250101_000000.json')
assert check['valid']
```

---

## Restoring a Backup

1. Identify the desired backup via `PersistenceManager.list_backups()`.
2. Restore into a `KnowledgeGraph` instance:

```python
graph = KnowledgeGraph()
pm = PersistenceManager(base_path='dawsos/storage')
pm.restore_from_backup('dawsos/storage/backups/graph_20250101_000000.json', graph)
graph.save('dawsos/storage/graph.json')
```

3. Restart the application or reload session state so the in-memory graph uses
   the restored file.

---

## Decisions Log Rotation

Agent execution decisions are kept in `dawsos/storage/agent_memory/decisions.json`.
When this file exceeds 5 MB, `AgentRuntime` archives it under
`dawsos/storage/agent_memory/archive/decisions_YYYYMMDD_HHMMSS.json`. To review:

```python
ls dawsos/storage/agent_memory/archive/
```

Keep the archive directory backed up alongside the main graph.

---

## Disaster Recovery Checklist

1. **Validate Backups** – Ensure `verify_integrity()` passes for the latest
   snapshot.
2. **Restore Graph** – Use `restore_from_backup()` and save to the live path.
3. **Restore Decisions** – Copy archived decision files if needed.
4. **Restart App** – Restart Streamlit or services consuming the graph.
5. **Smoke Test** – Run `python3 -m pytest dawsos/tests/validation/test_trinity_smoke.py`.
6. **Monitor** – Check logs (`dawsos/logs/`) for errors and verify the dashboard
   shows expected node/edge counts.

---

## Additional Considerations

- Store backups off-site or in cloud storage for redundancy.
- Schedule regular backup verification via CI or cron.
- Document the recovery process in team runbooks and rehearse periodically.

