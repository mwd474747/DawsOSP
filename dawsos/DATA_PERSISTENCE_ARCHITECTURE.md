# DawsOS Data Persistence Architecture
## How the System Saves and Retrieves Data

### Overview
DawsOS uses a multi-layered persistence strategy to maintain knowledge between sessions, cache API responses, and track workflow history.

---

## 1. KNOWLEDGE GRAPH PERSISTENCE (Primary Storage)

### Storage Location
```
storage/
├── graph.json           # Main knowledge graph
├── seeded_graph.json    # Investment framework seed
├── test_graph.json      # Test data
└── workflow_history.json # Workflow execution history
```

### Save Mechanism (core/knowledge_graph.py)
```python
def save(self, filepath: str = 'storage/graph.json') -> bool:
    """Saves entire graph state to JSON"""
    data = {
        'nodes': self.nodes,        # All entities
        'edges': self.edges,        # All relationships
        'patterns': self.patterns,  # Discovered patterns
        'metadata': {
            'created': self.created_at,
            'modified': datetime.now().isoformat(),
            'stats': self.get_stats()
        }
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Write with pretty formatting
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
```

### Load Mechanism
```python
def load(self, filepath: str = 'storage/graph.json') -> bool:
    """Loads graph state from JSON"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.nodes = data.get('nodes', {})
        self.edges = data.get('edges', [])
        self.patterns = data.get('patterns', {})

        return True
    return False
```

### What Gets Saved

#### Nodes (Entities)
```json
{
  "AAPL": {
    "id": "AAPL",
    "type": "stock",
    "data": {
      "symbol": "AAPL",
      "price": 255.53,
      "pe": 35.2,
      "market_cap": 3800000000000
    },
    "created_at": "2024-12-20T10:00:00"
  },
  "ECONOMIC_REGIME": {
    "id": "ECONOMIC_REGIME",
    "type": "regime",
    "data": {
      "current_state": "GOLDILOCKS",
      "description": "Moderate growth, controlled inflation"
    }
  }
}
```

#### Edges (Relationships)
```json
[
  {
    "from": "GDP",
    "to": "ECONOMIC_REGIME",
    "type": "indicates_growth",
    "strength": 0.9,
    "created_at": "2024-12-20T10:00:00"
  },
  {
    "from": "ECONOMIC_REGIME",
    "to": "TECHNOLOGY",
    "type": "favors",
    "strength": 0.8
  }
]
```

#### Patterns
```json
{
  "pattern_001": {
    "type": "REGIME_SHIFT",
    "description": "Goldilocks to Overheating",
    "trigger_conditions": ["CPI > 4%", "GDP > 3%"],
    "confidence": 0.75
  }
}
```

---

## 2. API DATA CACHING

### FRED Data Cache (capabilities/fred.py)
```python
class FREDCapability:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour

    def get_latest(self, series_id: str):
        # Check cache first
        if series_id in self.cache:
            cached = self.cache[series_id]
            if datetime.now() - cached['time'] < timedelta(seconds=self.cache_ttl):
                return cached['data']

        # Fetch fresh data
        data = self._fetch_from_api(series_id)

        # Cache it
        self.cache[series_id] = {
            'data': data,
            'time': datetime.now()
        }

        return data
```

### Market Data Cache (capabilities/market_data.py)
```python
class MarketDataCapability:
    def __init__(self):
        self.quote_cache = {}
        self.cache_ttl = 60  # 1 minute for quotes

    def get_quote(self, symbol: str):
        cache_key = f"quote_{symbol}"

        # Check cache
        if cache_key in self.quote_cache:
            cached = self.quote_cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['data']

        # Fetch and cache
        quote = self._fetch_quote(symbol)
        self.quote_cache[cache_key] = {
            'data': quote,
            'timestamp': time.time()
        }

        return quote
```

---

## 3. WORKFLOW HISTORY PERSISTENCE

### Storage Structure (workflows/investment_workflows.py)
```python
def save_workflow_result(self, result: Dict):
    """Saves workflow execution to history"""
    history = self.get_workflow_history()
    history.append(result)

    # Keep only last 100 executions
    history = history[-100:]

    with open('storage/workflow_history.json', 'w') as f:
        json.dump(history, f, indent=2)
```

### History Format
```json
[
  {
    "workflow": "morning_briefing",
    "timestamp": "2024-12-20T09:00:00",
    "steps": [
      {
        "step": 1,
        "agent": "claude",
        "action": "greet_and_context",
        "result": {"status": "completed"}
      },
      {
        "step": 2,
        "agent": "data_harvester",
        "action": "fetch_overnight_moves",
        "result": {"data": [...]}
      }
    ]
  }
]
```

---

## 4. SESSION STATE (Streamlit)

### In-Memory Storage (main.py)
```python
def init_session_state():
    """Initialize session state variables"""
    if 'graph' not in st.session_state:
        st.session_state.graph = KnowledgeGraph()
        # Load persisted graph on startup
        if os.path.exists('storage/graph.json'):
            st.session_state.graph.load('storage/graph.json')

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'workflows' not in st.session_state:
        st.session_state.workflows = InvestmentWorkflows(...)
```

### Auto-Save on Changes
```python
# After any modification
response = runtime.orchestrate(user_input)
# Auto-save graph
st.session_state.graph.save('storage/graph.json')
```

---

## 5. PERSISTENCE MANAGER (core/persistence.py)

### Centralized Persistence
```python
class PersistenceManager:
    def __init__(self, base_dir: str = 'storage'):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save_graph(self, graph, name: str = 'graph'):
        """Save graph with versioning"""
        filepath = f"{self.base_dir}/{name}.json"
        backup = f"{self.base_dir}/{name}_{datetime.now():%Y%m%d_%H%M%S}.json"

        # Create backup of existing
        if os.path.exists(filepath):
            shutil.copy(filepath, backup)

        # Save new version
        graph.save(filepath)

    def load_graph(self, name: str = 'graph'):
        """Load most recent graph"""
        filepath = f"{self.base_dir}/{name}.json"
        if os.path.exists(filepath):
            graph = KnowledgeGraph()
            graph.load(filepath)
            return graph
        return None
```

---

## 6. DATA RETRIEVAL PATTERNS

### Pattern 1: Check Cache → Load from Disk → Fetch from API
```python
def get_data(self, key):
    # 1. Check in-memory cache
    if key in self.cache:
        return self.cache[key]

    # 2. Check persistent storage
    stored = self.load_from_disk(key)
    if stored:
        self.cache[key] = stored
        return stored

    # 3. Fetch from API
    fresh = self.fetch_from_api(key)
    self.cache[key] = fresh
    self.save_to_disk(key, fresh)
    return fresh
```

### Pattern 2: Graph Traversal for Relationships
```python
def find_influences(self, node_id):
    """Find all nodes that influence given node"""
    influences = []
    for edge in self.edges:
        if edge['to'] == node_id:
            influences.append({
                'from': edge['from'],
                'type': edge['type'],
                'strength': edge['strength']
            })
    return influences
```

### Pattern 3: Pattern-Based Retrieval
```python
def get_nodes_by_pattern(self, pattern_type):
    """Retrieve nodes matching pattern"""
    matching = []
    for node_id, node in self.nodes.items():
        if self._matches_pattern(node, pattern_type):
            matching.append(node)
    return matching
```

---

## 7. BACKUP AND RECOVERY

### Automatic Backups
```python
def create_backup(self):
    """Create timestamped backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"storage/backups/{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    # Copy all storage files
    for file in os.listdir('storage'):
        if file.endswith('.json'):
            shutil.copy(f"storage/{file}", f"{backup_dir}/{file}")
```

### Recovery Process
```python
def restore_from_backup(self, backup_timestamp):
    """Restore from specific backup"""
    backup_dir = f"storage/backups/{backup_timestamp}"
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            shutil.copy(f"{backup_dir}/{file}", f"storage/{file}")
        return True
    return False
```

---

## 8. DATA LIFECYCLE

### Creation → Storage → Retrieval → Update

1. **Creation**
   ```python
   # User query creates new node
   graph.add_node('stock', {'symbol': 'TSLA', 'price': 460}, 'TSLA')
   ```

2. **Immediate Save**
   ```python
   # Auto-save after modification
   graph.save('storage/graph.json')
   ```

3. **Retrieval on Next Session**
   ```python
   # Load on startup
   graph.load('storage/graph.json')
   tesla = graph.nodes.get('TSLA')
   ```

4. **Update with Fresh Data**
   ```python
   # Fetch new price
   new_price = market.get_quote('TSLA')
   graph.nodes['TSLA']['data']['price'] = new_price['price']
   graph.save()
   ```

---

## 9. PERFORMANCE OPTIMIZATIONS

### Lazy Loading
```python
def get_node(self, node_id):
    """Load node only when needed"""
    if node_id not in self._loaded_nodes:
        self._loaded_nodes[node_id] = self._load_node_from_disk(node_id)
    return self._loaded_nodes[node_id]
```

### Batch Operations
```python
def save_batch(self, nodes):
    """Save multiple nodes efficiently"""
    updates = {}
    for node in nodes:
        updates[node['id']] = node

    # Single write operation
    self.nodes.update(updates)
    self.save()
```

### Incremental Updates
```python
def save_incremental(self, changes_only=True):
    """Save only changed data"""
    if changes_only:
        diff = self._calculate_diff()
        self._save_diff(diff)
    else:
        self.save()
```

---

## 10. DATA INTEGRITY

### Validation on Save
```python
def save(self, filepath):
    """Save with validation"""
    # Validate before saving
    if not self._validate_graph():
        raise ValueError("Graph validation failed")

    # Create checksums
    data = self._to_dict()
    data['checksum'] = self._calculate_checksum(data)

    # Atomic write
    temp_file = f"{filepath}.tmp"
    with open(temp_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Atomic rename
    os.rename(temp_file, filepath)
```

### Validation on Load
```python
def load(self, filepath):
    """Load with integrity check"""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Verify checksum
    stored_checksum = data.pop('checksum', None)
    calculated_checksum = self._calculate_checksum(data)

    if stored_checksum != calculated_checksum:
        raise ValueError("Data integrity check failed")

    self._from_dict(data)
```

---

## Summary

DawsOS uses a comprehensive data persistence strategy:

1. **Primary Storage**: JSON files in `storage/` directory
2. **Caching**: In-memory caches with TTL for API data
3. **Session State**: Streamlit session state for UI
4. **Auto-Save**: Graph saves automatically after changes
5. **History**: Workflow executions tracked separately
6. **Backup**: Timestamped backups for recovery
7. **Validation**: Integrity checks on save/load

This architecture ensures:
- ✅ Data survives application restarts
- ✅ API rate limits are respected through caching
- ✅ Fast retrieval through memory caching
- ✅ History tracking for audit trails
- ✅ Recovery from corruption through backups