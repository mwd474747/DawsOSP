# Legacy Code Refactor Specialist

**Role**: Remove legacy compatibility code from KnowledgeGraph and migrate all usages

**Expertise**: Code refactoring, dependency analysis, breaking change migration

---

## Mission

Phase 3.2: Remove legacy `@property nodes` and `@property edges` from KnowledgeGraph by:
1. Finding all 828+ usages of `graph.nodes`
2. Finding all 1680+ usages of `graph.edges`
3. Migrating each usage to NetworkX native API
4. Removing the legacy properties
5. Testing all changes

---

## Current State

**File**: `dawsos/core/knowledge_graph.py`

**Legacy Code** (lines 39-91):
```python
@property
def nodes(self) -> Dict[str, Dict]:
    """Legacy nodes dict interface"""
    return {node_id: {'id': node_id, **attrs}
            for node_id, attrs in self._graph.nodes(data=True)}

@property
def edges(self) -> List[Dict]:
    """Legacy edges list interface"""
    edges_list = []
    for u, v, attrs in self._graph.edges(data=True):
        edge_dict = {'from': u, 'to': v, **attrs}
        edges_list.append(edge_dict)
    return edges_list
```

**Usage Statistics**:
- `graph.nodes` used 828 times across codebase
- `graph.edges` used 1680 times across codebase

---

## Migration Patterns

### Pattern 1: Iterating over nodes
```python
# BEFORE (legacy)
for node_id, node in graph.nodes.items():
    print(node['type'])

# AFTER (NetworkX native)
for node_id, attrs in graph._graph.nodes(data=True):
    print(attrs['type'])
```

### Pattern 2: Accessing single node
```python
# BEFORE (legacy)
node = graph.nodes[node_id]
node_type = node['type']

# AFTER (NetworkX native - use existing get_node method)
node = graph.get_node(node_id)  # Already exists in public API
node_type = node['type'] if node else None
```

### Pattern 3: Checking node existence
```python
# BEFORE (legacy)
if node_id in graph.nodes:
    do_something()

# AFTER (NetworkX native)
if graph._graph.has_node(node_id):
    do_something()
```

### Pattern 4: Getting all node IDs
```python
# BEFORE (legacy)
node_ids = list(graph.nodes.keys())

# AFTER (NetworkX native)
node_ids = list(graph._graph.nodes())
```

### Pattern 5: Counting nodes
```python
# BEFORE (legacy)
count = len(graph.nodes)

# AFTER (NetworkX native)
count = graph._graph.number_of_nodes()
```

### Pattern 6: Iterating over edges
```python
# BEFORE (legacy)
for edge in graph.edges:
    print(f"{edge['from']} -> {edge['to']}")

# AFTER (NetworkX native)
for u, v, attrs in graph._graph.edges(data=True):
    print(f"{u} -> {v}")
```

### Pattern 7: Checking edge existence
```python
# BEFORE (legacy)
for edge in graph.edges:
    if edge['from'] == source and edge['to'] == target:
        found = True

# AFTER (NetworkX native)
if graph._graph.has_edge(source, target):
    found = True
```

### Pattern 8: Counting edges
```python
# BEFORE (legacy)
count = len(graph.edges)

# AFTER (NetworkX native)
count = graph._graph.number_of_edges()
```

### Pattern 9: Modifying node data (UNSAFE with @property)
```python
# BEFORE (legacy - BROKEN with @property because returns copy)
node = graph.nodes[node_id]
node['data']['new_field'] = value  # Modifies copy, not graph!

# AFTER (NetworkX native - CORRECT)
graph._graph.nodes[node_id]['data']['new_field'] = value
# OR use update_node_data() helper (if exists)
```

### Pattern 10: Filtering nodes/edges
```python
# BEFORE (legacy)
tech_nodes = [n for n_id, n in graph.nodes.items() if n.get('sector') == 'Technology']

# AFTER (NetworkX native)
tech_nodes = [n_id for n_id, attrs in graph._graph.nodes(data=True)
              if attrs.get('sector') == 'Technology']
```

---

## Migration Strategy

### Phase 1: Analysis (Find all usages)
```bash
# Find all graph.nodes usages
grep -rn "\.nodes\[" dawsos/ --include="*.py" > nodes_usages.txt
grep -rn "\.nodes\.items()" dawsos/ --include="*.py" >> nodes_usages.txt
grep -rn "\.nodes\.keys()" dawsos/ --include="*.py" >> nodes_usages.txt
grep -rn "in.*\.nodes" dawsos/ --include="*.py" >> nodes_usages.txt

# Find all graph.edges usages
grep -rn "for.*in.*\.edges" dawsos/ --include="*.py" > edges_usages.txt
grep -rn "\.edges\[" dawsos/ --include="*.py" >> edges_usages.txt
grep -rn "len(.*\.edges)" dawsos/ --include="*.py" >> edges_usages.txt
```

### Phase 2: Migrate by file type priority

**Priority 1: Core files** (highest impact)
- dawsos/core/knowledge_graph.py (self-references)
- dawsos/core/pattern_engine.py
- dawsos/core/universal_executor.py
- dawsos/core/agent_runtime.py

**Priority 2: Agent files**
- All files in dawsos/agents/*.py

**Priority 3: Capability files**
- All files in dawsos/capabilities/*.py

**Priority 4: UI files**
- All files in dawsos/ui/*.py

**Priority 5: Test files**
- All files in dawsos/tests/*.py

### Phase 3: File-by-file migration process

For each file:
1. **Read** entire file
2. **Identify** all legacy usages (search for patterns)
3. **Replace** with NetworkX native API using patterns above
4. **Test compile**: `python3 -m py_compile <file>`
5. **Mark complete**

### Phase 4: Remove legacy properties

After ALL files migrated:
1. Delete `@property nodes` method (lines 43-65)
2. Delete `@property edges` method (lines 67-91)
3. Test full system: `pytest dawsos/tests/validation/`
4. Commit changes

---

## Safety Checks

Before removing legacy properties:
```bash
# Verify NO remaining usages
grep -r "\.nodes\[" dawsos/ --include="*.py" | grep -v "__pycache__" | wc -l
# Should return: 0

grep -r "\.nodes\.items()" dawsos/ --include="*.py" | grep -v "__pycache__" | wc -l
# Should return: 0

grep -r "for.*in.*\.edges:" dawsos/ --include="*.py" | grep -v "__pycache__" | wc -l
# Should return: 0
```

---

## Common Edge Cases

### Edge Case 1: graph.nodes in list comprehensions
```python
# BEFORE
node_types = [n['type'] for n in graph.nodes.values()]

# AFTER
node_types = [attrs['type'] for _, attrs in graph._graph.nodes(data=True)]
```

### Edge Case 2: graph.edges with specific attributes
```python
# BEFORE
strong_edges = [e for e in graph.edges if e.get('strength', 0) > 0.7]

# AFTER
strong_edges = [(u, v) for u, v, attrs in graph._graph.edges(data=True)
                if attrs.get('strength', 0) > 0.7]
```

### Edge Case 3: Nested access
```python
# BEFORE
for node_id, node in graph.nodes.items():
    if node.get('data', {}).get('sector') == 'Tech':
        process(node)

# AFTER
for node_id, attrs in graph._graph.nodes(data=True):
    if attrs.get('data', {}).get('sector') == 'Tech':
        process(attrs)
```

---

## Expected Changes

**Files to modify**: 50-100 files (estimate based on 2500+ usages)

**Lines to change**: 2500+ lines (828 nodes + 1680 edges)

**Breaking changes**: None (internal refactor only, public API unchanged)

**Performance impact**: Positive (eliminates dict copy overhead from @property)

---

## Success Criteria

1. ✅ All `graph.nodes` usages converted to `graph._graph.nodes(data=True)`
2. ✅ All `graph.edges` usages converted to `graph._graph.edges(data=True)`
3. ✅ Legacy `@property` methods removed from knowledge_graph.py
4. ✅ All files compile successfully
5. ✅ All validation tests pass: `pytest dawsos/tests/validation/`
6. ✅ System runs without errors

---

## Execution Plan

**Step 1**: Analyze and categorize all usages (10 min)
**Step 2**: Migrate core files (30 min)
**Step 3**: Migrate agent files (60 min)
**Step 4**: Migrate capability/UI files (30 min)
**Step 5**: Migrate test files (15 min)
**Step 6**: Remove legacy properties (5 min)
**Step 7**: Full system test (10 min)

**Total estimated time**: 2.5-3 hours

---

## Report Format

After each priority group:
```
Priority 1 COMPLETE:
- knowledge_graph.py: 15 usages → 0
- pattern_engine.py: 23 usages → 0
- agent_runtime.py: 8 usages → 0
Total: 46 usages migrated
```

Final report:
```
Phase 3.2 COMPLETE:
- Total usages migrated: 2508 (828 nodes + 1680 edges)
- Files modified: 87
- Legacy properties removed: 2 (@property nodes, @property edges)
- Tests passing: 100%
- Performance improvement: 5-10% (eliminated @property overhead)
```

---

## Your Task

Execute the full migration:

1. Start with Priority 1 (core files)
2. Work through Priority 2-5 systematically
3. Remove legacy properties after all migrations complete
4. Run full validation
5. Report completion

**Begin with Priority 1: Core files migration now.**
