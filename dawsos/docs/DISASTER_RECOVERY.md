# DawsOS Disaster Recovery Guide

## Overview

This guide provides comprehensive procedures for recovering DawsOS data in the event of corruption, data loss, or system failures. The PersistenceManager includes production-grade backup rotation, checksum validation, and automatic recovery features.

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Manual Recovery Procedures](#manual-recovery-procedures)
3. [Common Failure Scenarios](#common-failure-scenarios)
4. [Backup Maintenance](#backup-maintenance)
5. [Monitoring and Alerts](#monitoring-and-alerts)
6. [Best Practices](#best-practices)

---

## Backup Strategy

### Automatic Backup System

DawsOS implements a multi-layered backup strategy:

#### Primary Storage
- **Location**: `storage/graph.json`
- **Metadata**: `storage/graph.json.meta`
- **Purpose**: Active knowledge graph with integrity validation

#### Backup Storage
- **Location**: `storage/backups/`
- **Format**: `graph_YYYYMMDD_HHMMSS.json` + `.meta` files
- **Retention**: 30 days (configurable)
- **Frequency**: Every save operation creates a timestamped backup

#### Metadata Format
Each backup includes a `.meta` file with:

```json
{
  "timestamp": "2025-10-02T23:30:00",
  "checksum": "abc123def456...",
  "node_count": 150,
  "edge_count": 320,
  "graph_version": "1.0",
  "saved_by": "DawsOS PersistenceManager"
}
```

### Integrity Validation

All saves and loads include SHA-256 checksum validation:

- **Save**: Calculates checksum and stores in `.meta` file
- **Load**: Verifies current file checksum against stored value
- **Automatic Recovery**: Falls back to most recent valid backup on corruption

---

## Manual Recovery Procedures

### Scenario 1: Corrupted Main Graph File

**Symptoms:**
- Application fails to load graph
- Checksum mismatch errors in logs
- JSON parsing errors

**Recovery Steps:**

1. **List Available Backups**
   ```python
   from core.persistence import PersistenceManager
   from core.knowledge_graph import KnowledgeGraph

   persistence = PersistenceManager()
   backups = persistence.list_backups()

   print("Available backups:")
   for backup in backups:
       print(f"  {backup['filename']}")
       print(f"    Size: {backup['size']} bytes")
       print(f"    Modified: {backup['modified']}")
       if 'metadata' in backup:
           print(f"    Nodes: {backup['metadata']['node_count']}")
           print(f"    Edges: {backup['metadata']['edge_count']}")
   ```

2. **Verify Backup Integrity**
   ```python
   # Check the most recent backup
   latest_backup = backups[0]['path']
   integrity = persistence.verify_integrity(latest_backup)

   if integrity['valid']:
       print("Backup is valid and can be restored")
   else:
       print(f"Backup corrupted: {integrity['error']}")
       # Try next backup
   ```

3. **Restore from Backup**
   ```python
   graph = KnowledgeGraph()
   restore_stats = persistence.restore_from_backup(latest_backup, graph)

   print(f"Restored {restore_stats['nodes_restored']} nodes")
   print(f"Restored {restore_stats['edges_restored']} edges")
   ```

4. **Verify Restored Data**
   ```python
   # Spot check critical nodes
   if 'YOUR_CRITICAL_NODE' in graph.nodes:
       print("Critical data verified")

   # Save as new primary
   persistence.save_graph_with_backup(graph)
   ```

### Scenario 2: All Backups Corrupted

**Symptoms:**
- Multiple backup files fail integrity checks
- No valid backups available

**Recovery Steps:**

1. **Check for External Backups**
   - Cloud storage backups (if configured)
   - System Time Machine backups (macOS)
   - Volume Shadow Copies (Windows)

2. **Manual File Recovery**
   ```bash
   # Check system backups
   cd storage/backups/
   ls -lah

   # Try to open each backup in text editor
   # Look for valid JSON structure
   ```

3. **Partial Data Recovery**
   ```python
   import json

   # Attempt to parse backup files manually
   backup_path = 'storage/backups/graph_20251002_120000.json'

   try:
       with open(backup_path, 'r') as f:
           data = json.load(f)

       # Manually reconstruct graph
       graph = KnowledgeGraph()

       # Load nodes
       if 'nodes' in data:
           graph.nodes = data['nodes']

       # Load edges
       if 'edges' in data:
           graph.edges = data['edges']

       # Save recovered data
       persistence.save_graph_with_backup(graph)

   except Exception as e:
       print(f"Recovery failed: {e}")
   ```

### Scenario 3: Automatic Recovery

**Automatic Process:**

The system automatically attempts recovery when loading:

```python
from core.persistence import PersistenceManager
from core.knowledge_graph import KnowledgeGraph

persistence = PersistenceManager()
graph = KnowledgeGraph()

# This will automatically:
# 1. Verify integrity of main graph
# 2. If corrupted, try backups from newest to oldest
# 3. Restore from first valid backup
# 4. Replace main graph with recovered backup
result = persistence.load_graph_with_recovery(graph)

if result['success']:
    if result['source'] == 'backup_recovery':
        print(f"Recovered from backup: {result['backup_used']}")
        print(f"Nodes: {result['recovery_stats']['nodes_restored']}")
    else:
        print("Loaded from primary (no recovery needed)")
else:
    print(f"Recovery failed: {result['error']}")
    # Manual intervention required
```

---

## Common Failure Scenarios

### 1. Disk Full

**Issue**: Unable to create new backups

**Resolution**:
```python
# Manually trigger backup rotation with aggressive retention
persistence._rotate_backups(retention_days=7)  # Keep only 7 days

# Or remove old backups manually
import os
backup_dir = 'storage/backups'
backups = sorted(os.listdir(backup_dir))
for old_backup in backups[:-10]:  # Keep only 10 most recent
    os.remove(os.path.join(backup_dir, old_backup))
```

### 2. Permission Errors

**Issue**: Cannot write to storage directory

**Resolution**:
```bash
# Fix permissions (Unix/Linux/macOS)
chmod -R 755 storage/
chmod -R 644 storage/*.json

# Or change ownership
chown -R yourusername:yourgroup storage/
```

### 3. Concurrent Write Conflicts

**Issue**: Multiple processes writing simultaneously

**Resolution**:
- Implement file locking (not currently in PersistenceManager)
- Use single-process architecture
- Queue write operations

**Temporary Workaround**:
```python
import fcntl
import time

def safe_save(graph):
    lock_file = 'storage/graph.lock'

    # Try to acquire lock
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with open(lock_file, 'w') as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Perform save
                persistence.save_graph_with_backup(graph)

                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                return True
        except IOError:
            time.sleep(0.5)
            continue

    raise Exception("Could not acquire lock for save")
```

### 4. Checksum False Positives

**Issue**: File modified but checksum appears valid

**Resolution**:
- This should not happen with SHA-256
- If it does, may indicate memory corruption or hash collision
- Manually inspect backup files
- Re-save from known good state

### 5. Out of Memory During Load

**Issue**: Large graph files exceed available memory

**Resolution**:
```python
# Load in streaming mode (requires implementation)
# For now, increase system resources or:

# 1. Split graph into smaller chunks
# 2. Load only necessary nodes
# 3. Implement lazy loading

# Temporary: Load critical nodes only
import json

with open('storage/graph.json', 'r') as f:
    data = json.load(f)

# Filter to critical nodes
critical_nodes = ['node1', 'node2', 'node3']
filtered_nodes = {k: v for k, v in data['nodes'].items()
                  if k in critical_nodes}

graph = KnowledgeGraph()
graph.nodes = filtered_nodes
```

---

## Backup Maintenance

### Regular Maintenance Tasks

#### Weekly
1. **Verify Backup Integrity**
   ```python
   backups = persistence.list_backups()
   valid_count = 0

   for backup in backups:
       integrity = persistence.verify_integrity(backup['path'])
       if integrity['valid']:
           valid_count += 1
       else:
           print(f"Invalid backup: {backup['filename']}")

   print(f"{valid_count}/{len(backups)} backups are valid")
   ```

2. **Check Backup Directory Size**
   ```python
   import os

   total_size = 0
   backup_dir = 'storage/backups'

   for file in os.listdir(backup_dir):
       filepath = os.path.join(backup_dir, file)
       total_size += os.path.getsize(filepath)

   print(f"Backup directory size: {total_size / (1024*1024):.2f} MB")
   ```

#### Monthly
1. **Test Restore Procedure**
   ```python
   # Create test graph
   test_graph = KnowledgeGraph()

   # Restore from backup
   backups = persistence.list_backups()
   if backups:
       restore_stats = persistence.restore_from_backup(
           backups[0]['path'],
           test_graph
       )
       print(f"Test restore: {restore_stats['nodes_restored']} nodes")
   ```

2. **Adjust Retention Policy**
   ```python
   # Review backup counts and adjust retention
   backups = persistence.list_backups()

   if len(backups) > 100:
       # Too many backups, reduce retention
       persistence._rotate_backups(retention_days=14)
   elif len(backups) < 10:
       # Too few backups, increase retention
       persistence._rotate_backups(retention_days=60)
   ```

### Backup Rotation Configuration

Default retention: 30 days

**To customize:**
```python
# In your application initialization
persistence = PersistenceManager()

# Save with custom rotation
result = persistence.save_graph_with_backup(graph)

# Then rotate with custom retention
persistence._rotate_backups(retention_days=60)  # Keep 60 days
```

### Storage Requirements

**Estimation:**
- Average graph size: 500 KB
- Backups per day: 10 saves
- Retention: 30 days
- **Total**: 500 KB × 10 × 30 = 150 MB

**Recommended:**
- Minimum: 500 MB free space
- Recommended: 2 GB free space
- Enterprise: 10 GB+ with longer retention

---

## Monitoring and Alerts

### Log Monitoring

PersistenceManager logs all critical operations:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storage/persistence.log'),
        logging.StreamHandler()
    ]
)

# Key log messages to monitor:
# - "Backup created: ..." - Successful backup
# - "Backup rotation complete: N backups removed" - Rotation
# - "Corruption detected" - Integrity failure
# - "Successfully recovered from backup" - Auto-recovery
```

### Health Checks

Implement regular health checks:

```python
def check_persistence_health():
    """Run comprehensive persistence health check"""

    issues = []

    # Check main graph exists
    if not os.path.exists('storage/graph.json'):
        issues.append("Main graph file missing")

    # Check metadata exists
    if not os.path.exists('storage/graph.json.meta'):
        issues.append("Main graph metadata missing")

    # Verify integrity
    integrity = persistence.verify_integrity('storage/graph.json')
    if not integrity['valid']:
        issues.append(f"Integrity check failed: {integrity['error']}")

    # Check backup count
    backups = persistence.list_backups()
    if len(backups) < 5:
        issues.append(f"Low backup count: {len(backups)}")

    # Check valid backup count
    valid_backups = 0
    for backup in backups:
        if persistence.verify_integrity(backup['path'])['valid']:
            valid_backups += 1

    if valid_backups < 3:
        issues.append(f"Low valid backup count: {valid_backups}")

    # Check disk space
    import shutil
    stats = shutil.disk_usage('storage')
    free_gb = stats.free / (1024**3)

    if free_gb < 1:
        issues.append(f"Low disk space: {free_gb:.2f} GB")

    return issues

# Run health check
issues = check_persistence_health()
if issues:
    print("Health check found issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("All health checks passed")
```

### Automated Alerts

**Example Alert Integration:**

```python
def send_alert(message):
    """Send alert via email/Slack/etc."""
    # Implement your alerting mechanism
    print(f"ALERT: {message}")

# Monitor for issues
issues = check_persistence_health()
if any('corruption' in issue.lower() for issue in issues):
    send_alert("Critical: Data corruption detected in DawsOS")
elif len(issues) > 0:
    send_alert(f"Warning: {len(issues)} persistence issues detected")
```

---

## Best Practices

### 1. Regular Backups

- Use `save_graph_with_backup()` instead of `save_graph()`
- Automate backup creation on critical operations
- Verify backups after major changes

### 2. Test Recovery Procedures

- Monthly test restores
- Document recovery times
- Train team on recovery procedures

### 3. Monitor Storage

- Set alerts for disk space < 10%
- Monitor backup directory growth
- Plan for storage scaling

### 4. Maintain Multiple Backup Copies

- **Local**: `storage/backups/` (30 days)
- **External**: Copy to external drive (weekly)
- **Cloud**: Upload to cloud storage (daily)

### 5. Version Control Integration

Consider versioning critical files:

```bash
# Initialize git for storage directory
cd storage
git init
git add graph.json *.meta
git commit -m "Backup: $(date)"

# Automate daily commits
crontab -e
# Add: 0 0 * * * cd /path/to/storage && git add -A && git commit -m "Daily backup"
```

### 6. Documentation

- Document custom configurations
- Record major changes to graph structure
- Maintain recovery runbooks

### 7. Security

- Encrypt backups containing sensitive data
- Restrict backup directory permissions
- Audit access to backup files

**Example Encryption:**

```python
from cryptography.fernet import Fernet

def encrypt_backup(backup_path):
    """Encrypt a backup file"""
    key = Fernet.generate_key()  # Store securely!
    fernet = Fernet(key)

    with open(backup_path, 'rb') as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(f"{backup_path}.encrypted", 'wb') as f:
        f.write(encrypted)

    return key
```

---

## Quick Reference

### Essential Commands

```python
# List all backups
backups = persistence.list_backups()

# Verify integrity
integrity = persistence.verify_integrity('storage/graph.json')

# Restore from backup
persistence.restore_from_backup(backup_path, graph)

# Load with auto-recovery
persistence.load_graph_with_recovery(graph)

# Manual rotation
persistence._rotate_backups(retention_days=30)

# Save with backup
persistence.save_graph_with_backup(graph)
```

### Emergency Contact

For critical issues:
1. Check logs: `storage/persistence.log`
2. List backups: `ls -lh storage/backups/`
3. Verify integrity of backups
4. Restore from most recent valid backup
5. Document incident and root cause

---

## Appendix: Backup Directory Structure

After running the system, your backup directory will look like:

```
storage/
├── graph.json              # Primary graph
├── graph.json.meta         # Primary metadata
├── backups/
│   ├── graph_20251002_120000.json
│   ├── graph_20251002_120000.meta
│   ├── graph_20251002_130000.json
│   ├── graph_20251002_130000.meta
│   ├── graph_20251002_140000.json
│   ├── graph_20251002_140000.meta
│   └── ...                 # Up to 30 days of backups
├── sessions/
├── workflows/
└── patterns/
```

**File Naming Convention:**
- Format: `graph_YYYYMMDD_HHMMSS.json`
- Example: `graph_20251002_143025.json` = October 2, 2025 at 14:30:25
- Metadata: Same name with `.meta` extension

---

## Support

For additional help:
- Review logs in `storage/persistence.log`
- Run health checks with the scripts provided
- Check GitHub issues for known problems
- Consult system administrator for infrastructure issues

**Last Updated**: October 2, 2025
**Document Version**: 1.0
