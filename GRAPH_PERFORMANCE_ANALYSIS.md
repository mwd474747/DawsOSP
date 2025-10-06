# Graph Performance Analysis & Migration Options

**Date**: October 4, 2025
**Current System**: In-memory Python dict-based graph
**Status**: Performance bottlenecks identified

---

## Current Architecture Analysis

### Implementation
- **Technology**: Pure Python dict/list structures ([knowledge_graph.py](dawsos/core/knowledge_graph.py))
- **Storage**: JSON file serialization (82MB)
- **Query Method**: Linear scan through `self.edges` list (22 occurrences in code)

### Current Performance Metrics

```
File Size:        82 MB
Load Time:        0.35s (acceptable)
Nodes:            96,409
Edges:            96,526
Avg Degree:       1.0 (very sparse graph)
Memory Footprint: ~164 MB in-memory
```

### Identified Bottlenecks

#### 🔴 **Critical: O(n) Edge Lookups**

**Problem**: Every graph operation scans the entire edge list
```python
# Lines 82-86: trace_connections() - scans all edges for each node
for edge in self.edges:
    if edge['from'] == node and edge['strength'] >= min_strength:
        # ...

# Lines 103-110: forecast() - scans all edges multiple times
for edge in self.edges:
    if edge['to'] == target_node:
        # ...

# Lines 175-177: _discover_patterns() - nested edge scans
for edge in self.edges:
    if edge['from'] == to_node:
        # ...
```

**Impact**:
- **O(E)** lookup per operation where E = 96,526 edges
- Nested loops create **O(E²)** complexity in pattern discovery
- Each `trace_connections()` call: ~96K iterations
- Each `forecast()` call: 200K+ iterations (multiple scans)

#### 🟡 **Moderate: Memory Inefficiency**

**Problem**: Full graph loaded into memory
- 164MB for 96K nodes (only ~1.7KB per node)
- No lazy loading or pagination
- Duplicate edge references in node connection lists

#### 🟡 **Moderate: No Indexing**

**Problem**: No indexes on frequently queried fields
- Node type queries scan all 96K nodes
- Relationship type queries scan all 96K edges
- No spatial/temporal indexes

#### 🟢 **Minor: JSON Serialization**

**Problem**: Human-readable but slow
- 0.35s load time is acceptable for 82MB
- Could be faster with binary format (msgpack, pickle)

---

## Performance Projections

### Current Scale (100K nodes)
- **Load time**: 0.35s ✅
- **Single forecast**: ~200ms 🟡
- **Pattern discovery**: 1-2s 🔴
- **Batch analysis**: 10-20s 🔴

### At 1M nodes (10x growth)
- **Load time**: 3.5s 🟡
- **Single forecast**: 2s 🔴
- **Pattern discovery**: 100s+ 🔴
- **Memory**: 1.6GB 🔴

### At 10M nodes (100x growth)
- **Load time**: 35s+ 🔴
- **Operations**: Unusable (minutes per query) 🔴
- **Memory**: 16GB+ 🔴

---

## Open Source Graph Database Options

### Option 1: **NetworkX** (Lightweight Migration)
**What**: Pure Python graph library
**Complexity**: ⭐ Low (1-2 days)
**Performance**: ⭐⭐ Moderate improvement

**Pros**:
- Drop-in replacement for current dict/list structure
- Rich algorithm library (centrality, shortest paths, community detection)
- Same Python-only stack (no new dependencies)
- Efficient adjacency list representation (O(1) neighbor lookups)

**Cons**:
- Still in-memory only
- No built-in persistence (need custom JSON/pickle)
- Limited to ~10M edges before slowdown

**Migration Effort**:
```python
# Current: self.nodes = {}, self.edges = []
# New:     self.graph = nx.DiGraph()

# Current: for edge in self.edges if edge['from'] == node
# New:     for neighbor in self.graph.successors(node)  # O(k) not O(E)
```

**Use Case**: Best for <1M nodes, algorithmic focus, minimal migration

---

### Option 2: **SQLite with Graph Extension** (Pragmatic)
**What**: SQLite + graph queries via recursive CTEs or sqlite-graphdb
**Complexity**: ⭐⭐ Medium (3-5 days)
**Performance**: ⭐⭐⭐ Good for most queries

**Pros**:
- Single file database (like current JSON)
- Zero-config deployment (no server)
- Indexed lookups (O(log n) via B-tree)
- Native Python support (stdlib `sqlite3`)
- ACID transactions

**Cons**:
- Recursive CTEs slower than native graph engines
- Limited to ~100M rows (adequate for 10M nodes)
- No distributed scaling

**Migration Effort**:
```sql
CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, data JSON);
CREATE TABLE edges (id TEXT PRIMARY KEY, from_id TEXT, to_id TEXT,
                    relationship TEXT, strength REAL);
CREATE INDEX idx_edges_from ON edges(from_id);
CREATE INDEX idx_edges_to ON edges(to_id);
```

**Use Case**: Best for <10M nodes, ACID needs, simple deployment

---

### Option 3: **Neo4j** (Industry Standard)
**What**: Native graph database (Cypher query language)
**Complexity**: ⭐⭐⭐⭐ High (1-2 weeks)
**Performance**: ⭐⭐⭐⭐⭐ Excellent at any scale

**Pros**:
- Index-free adjacency (O(1) traversals)
- Cypher query language (expressive, optimized)
- Scales to billions of nodes
- Rich visualization tools (Neo4j Browser)
- Python driver (`neo4j-driver`)

**Cons**:
- Requires Java runtime (deployment overhead)
- Community edition limited to single server
- Higher operational complexity
- Learning curve for Cypher

**Migration Effort**:
```python
# Cypher example
query = """
MATCH (start:Node {id: $start_id})-[r:RELATES_TO*1..3]->(target)
WHERE r.strength > 0.3
RETURN target, collect(r) as path
"""
```

**Use Case**: Best for >10M nodes, production workloads, team with graph expertise

---

### Option 4: **ArangoDB** (Multi-Model)
**What**: Multi-model DB (graph + document + key-value)
**Complexity**: ⭐⭐⭐ Medium-High (1 week)
**Performance**: ⭐⭐⭐⭐ Very good

**Pros**:
- Native graph + document store (flexible schema)
- AQL query language (SQL-like + graph traversals)
- Horizontal scaling (sharding)
- Built-in full-text search
- Python driver (`python-arango`)

**Cons**:
- Less mature than Neo4j
- Smaller community/ecosystem
- Memory-hungry (caches graphs in RAM)

**Use Case**: Best for mixed workloads (graph + documents), need for scalability

---

### Option 5: **DuckDB with Graph Extension** (Modern Analytical)
**What**: In-process analytical DB with graph queries
**Complexity**: ⭐⭐ Medium (3-5 days)
**Performance**: ⭐⭐⭐⭐ Excellent for analytics

**Pros**:
- Zero-config like SQLite but columnar (fast aggregations)
- Native graph traversal support (DuckDB 0.9+)
- Parquet export/import (efficient storage)
- Python native (`duckdb`)
- Fast bulk loads

**Cons**:
- Newer technology (less battle-tested)
- Graph features still evolving
- Not optimized for OLTP (write-heavy workloads)

**Use Case**: Best for analytical queries, batch processing, modern stack

---

## Recommended Migration Path

### Phase 1: Quick Win - NetworkX (Week 1)
**Effort**: 1-2 days
**Impact**: 5-10x speedup on traversals

**Why First**:
- Minimal code changes (same Python paradigm)
- Immediate performance gains from adjacency lists
- Unlock graph algorithms (PageRank, community detection)
- No infrastructure changes

**Implementation**:
```python
# Replace knowledge_graph.py internals
import networkx as nx

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph

    def add_node(self, node_type, data, node_id=None):
        self.graph.add_node(node_id, type=node_type, data=data, ...)

    def connect(self, from_id, to_id, relationship, strength):
        self.graph.add_edge(from_id, to_id,
                           type=relationship, strength=strength)

    def trace_connections(self, start_node, max_depth=3):
        # O(k^d) instead of O(E * d)
        return nx.single_source_shortest_path(self.graph, start_node,
                                             cutoff=max_depth)
```

**Expected Results**:
- Traversal queries: 200ms → 20ms (10x faster)
- Pattern discovery: 2s → 200ms (10x faster)
- Memory: 164MB → 120MB (better structure)

---

### Phase 2: Persistent Storage - SQLite (Month 2)
**Effort**: 3-5 days
**Impact**: Indexed queries, ACID, persistence

**Why Second**:
- Build on NetworkX improvements
- Hybrid approach: SQLite for storage, NetworkX for algorithms
- Enable queries without loading full graph
- Add transaction safety

**Implementation**:
```python
class KnowledgeGraph:
    def __init__(self, db_path='storage/graph.db'):
        self.db = sqlite3.connect(db_path)
        self._create_schema()
        self._cache = nx.DiGraph()  # In-memory cache

    def query(self, pattern):
        # Use SQL for filtering, NetworkX for traversal
        cursor = self.db.execute("""
            SELECT id FROM nodes
            WHERE type = ? AND json_extract(data, '$.sector') = ?
        """, (pattern['type'], pattern['data']['sector']))

        node_ids = [row[0] for row in cursor]
        return self._load_subgraph(node_ids)
```

**Expected Results**:
- Large queries: 10s → 1s (10x faster via indexes)
- Disk usage: 82MB → 40MB (normalized schema)
- Startup: Load only active nodes, not entire graph

---

### Phase 3: Production Scale - Neo4j or DuckDB (If Needed)
**Effort**: 1-2 weeks
**Impact**: Scale to millions of nodes

**Decision Point**: Only if you hit these limits:
- \>1M nodes in production
- \>100 concurrent users
- Need for graph visualizations
- Require horizontal scaling

**Why Third**:
- Most users won't need this scale
- SQLite + NetworkX handles 1M+ nodes well
- Defer complexity until proven necessary

---

## Migration Risks & Mitigations

### Risk 1: Data Loss During Migration
**Mitigation**:
- Keep `graph.json` as source of truth
- Export to new format (don't delete JSON)
- Implement bidirectional sync during transition
- Checksum validation after migration

### Risk 2: Breaking Existing Agents
**Mitigation**:
- Keep `KnowledgeGraph` API identical (facade pattern)
- Change internals, not public methods
- Comprehensive test suite before/after
- Gradual rollout (NetworkX first, SQLite later)

### Risk 3: Query Behavior Changes
**Mitigation**:
- Document query semantics (e.g., edge traversal order)
- A/B test results between old/new graph
- Benchmark suite for performance regression

---

## Simple Decision Matrix

| Scenario | Recommendation | Timeline |
|----------|---------------|----------|
| **Current system works fine** | No change needed | - |
| **Slow pattern discovery** | NetworkX (Phase 1) | 2 days |
| **Large graph (>500K nodes)** | SQLite (Phase 2) | 1 week |
| **Production app (>1M nodes)** | Neo4j/DuckDB (Phase 3) | 2 weeks |
| **Need graph algorithms** | NetworkX (Phase 1) | 2 days |
| **Need ACID transactions** | SQLite (Phase 2) | 1 week |
| **Need visualization** | Neo4j (Phase 3) | 2 weeks |

---

## Immediate Action Items

### Option A: Conservative (No Migration)
**Best if**: Current performance is acceptable
1. Add sampling to `trace_connections()` (limit edge scans)
2. Cache frequently accessed paths
3. Defer migration until proven bottleneck

### Option B: Incremental (Recommended)
**Best if**: Performance is degrading, growth expected
1. Week 1: Implement NetworkX backend
2. Week 2: Run A/B test (old vs new)
3. Week 3: Migrate production
4. Month 2: Add SQLite persistence

### Option C: Aggressive (Big Rewrite)
**Best if**: Building production product, known scale requirements
1. Week 1-2: Design Neo4j schema
2. Week 3: Migrate data + tests
3. Week 4: Deploy + monitor

---

## Cost-Benefit Summary

| Option | Effort | Speed Gain | Scale Limit | Complexity |
|--------|--------|------------|-------------|------------|
| **No Change** | 0 days | - | 100K nodes | ⭐ |
| **NetworkX** | 2 days | 10x | 1M nodes | ⭐ |
| **SQLite** | 1 week | 10-50x | 10M nodes | ⭐⭐ |
| **Neo4j** | 2 weeks | 100x+ | 1B+ nodes | ⭐⭐⭐⭐ |
| **DuckDB** | 1 week | 50x+ | 100M nodes | ⭐⭐⭐ |

---

## Final Recommendation

**Start with NetworkX (Phase 1)**:
- Lowest risk, highest immediate ROI
- 2-day migration preserves all existing code
- 10x performance improvement on bottleneck operations
- Natural stepping stone to Phase 2 (SQLite) if needed

**Only proceed to Phase 2/3 if**:
- Graph exceeds 1M nodes
- Production SLA requirements demand it
- Team has capacity for operational complexity

The current Python dict/list approach is simple and works well at current scale. NetworkX provides algorithmic power without operational overhead—the sweet spot for DawsOS.
