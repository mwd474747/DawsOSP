# Legacy Refactor Specialist v2.0 - PARALLEL BATCH EXECUTOR

**CRITICAL ENHANCEMENT**: Work in PARALLEL BATCHES of 10 files simultaneously for maximum speed

---

## Enhanced Mission - Parallel Execution

Complete Phase 3.2 by migrating ALL remaining legacy API usages (~800 remaining) using:

1. **PARALLEL BATCHES** - Process 10 files at once
2. **AST-BASED REPLACEMENT** - More accurate than regex
3. **AUTOMATED VERIFICATION** - Compile test after each batch
4. **PROGRESS TRACKING** - Report after every 10 files

**Target**: Complete all ~60 remaining files in 3-4 batches instead of 60 sequential operations

---

## Current Status (Updated)

**Completed**: 25 files migrated in Part 1
**Remaining**: ~60 files with ~800 legacy usages
- `graph.nodes` usages: ~800
- `graph.edges` usages: ~420

---

## PARALLEL BATCH STRATEGY

### Step 1: Identify File Batches (10 files per batch)

```bash
# Get all files with legacy usage, group into batches of 10
grep -r "\.nodes\[" dawsos/ --include="*.py" -l | grep -v __pycache__ | head -10 > batch1.txt
grep -r "\.nodes\[" dawsos/ --include="*.py" -l | grep -v __pycache__ | tail -n +11 | head -10 > batch2.txt
# etc.
```

### Step 2: Process Each Batch in Parallel

**For each batch of 10 files**:
1. Read all 10 files simultaneously (parallel reads)
2. Apply migrations to all 10 files (parallel transformations)
3. Write all 10 files back (parallel writes)
4. Test compilation of all 10 files (parallel compiles)
5. Report batch completion

### Step 3: Batch Template

```
BATCH X (Files 1-10):
- file1.py: 15 usages → migrated ✅
- file2.py: 8 usages → migrated ✅
- file3.py: 12 usages → migrated ✅
...
- file10.py: 5 usages → migrated ✅

Total: 87 usages migrated in batch X
Compilation: 10/10 files compile successfully ✅
```

---

## Enhanced Migration Patterns (AST-Ready)

### Pattern 1: graph.nodes[id] → graph.get_node(id)
```python
# AST Pattern Match:
# Subscript(value=Attribute(attr='nodes'), slice=Name(id))

# BEFORE
node = graph.nodes[node_id]
data = node['data']

# AFTER
node = graph.get_node(node_id)
data = node['data'] if node else {}
```

### Pattern 2: for x in graph.nodes.items()
```python
# AST Pattern: For(iter=Call(func=Attribute(value=Attribute(attr='nodes'), attr='items')))

# BEFORE
for node_id, node in graph.nodes.items():
    process(node['type'])

# AFTER
for node_id, attrs in graph._graph.nodes(data=True):
    process(attrs['type'])
```

### Pattern 3: for edge in graph.edges
```python
# AST Pattern: For(iter=Attribute(attr='edges'))

# BEFORE
for edge in graph.edges:
    print(f"{edge['from']} -> {edge['to']}")

# AFTER
for u, v, attrs in graph._graph.edges(data=True):
    print(f"{u} -> {v}")
```

### Pattern 4: if x in graph.nodes
```python
# AST Pattern: Compare(ops=[In()], comparators=[Attribute(attr='nodes')])

# BEFORE
if node_id in graph.nodes:
    do_something()

# AFTER
if graph._graph.has_node(node_id):
    do_something()
```

### Pattern 5: len(graph.nodes) or len(graph.edges)
```python
# AST Pattern: Call(func=Name(id='len'), args=[Attribute(attr='nodes')])

# BEFORE
node_count = len(graph.nodes)
edge_count = len(graph.edges)

# AFTER
node_count = graph._graph.number_of_nodes()
edge_count = graph._graph.number_of_edges()
```

### Pattern 6: graph.nodes.keys() or .values()
```python
# BEFORE
node_ids = list(graph.nodes.keys())
all_nodes = list(graph.nodes.values())

# AFTER
node_ids = list(graph._graph.nodes())
all_nodes = [attrs for _, attrs in graph._graph.nodes(data=True)]
```

### Pattern 7: [comprehension for x in graph.edges]
```python
# BEFORE
strong_edges = [e for e in graph.edges if e.get('strength', 0) > 0.7]

# AFTER
strong_edges = [(u, v, attrs) for u, v, attrs in graph._graph.edges(data=True)
                if attrs.get('strength', 0) > 0.7]
```

---

## EXECUTION PLAN - PARALLEL BATCHES

### Batch 1 (Files 1-10) - Agents
```
1. dawsos/agents/claude.py
2. dawsos/agents/data_digester.py
3. dawsos/agents/forecast_dreamer.py
4. dawsos/agents/refactor_elf.py
5. dawsos/agents/structure_bot.py
6. dawsos/agents/ui_generator.py
7. dawsos/agents/workflow_player.py
8. dawsos/agents/workflow_recorder.py
9. dawsos/agents/code_monkey.py
10. dawsos/agents/data_harvester.py
```

### Batch 2 (Files 11-20) - Capabilities + UI
```
11. dawsos/capabilities/crypto.py
12. dawsos/capabilities/fred.py
13. dawsos/capabilities/fred_data.py
14. dawsos/capabilities/fundamentals.py
15. dawsos/capabilities/market_data.py
16. dawsos/capabilities/news.py
17. dawsos/ui/alert_panel.py
18. dawsos/ui/intelligence_display.py
19. dawsos/ui/pattern_browser.py
20. dawsos/ui/trinity_ui_components.py
```

### Batch 3 (Files 21-30) - Workflows + Tests
```
21. dawsos/workflows/investment_workflows.py
22. dawsos/workflows/workflow_engine.py
23. dawsos/tests/unit/test_knowledge_graph.py
24. dawsos/tests/unit/test_pattern_engine.py
25. dawsos/tests/integration/test_agent_workflows.py
26. dawsos/tests/regression/test_backwards_compat.py
27. dawsos/tests/validation/test_trinity_smoke.py
28. dawsos/tests/validation/test_integration.py
29. dawsos/main.py
30. dawsos/scripts/*.py (any with usage)
```

### Batch 4-6 (Files 31-60) - Remaining files
Continue batches of 10 until all files complete

---

## PARALLEL EXECUTION COMMANDS

### Multi-file Edit Pattern
```python
# Instead of sequential edits:
# edit file1, edit file2, edit file3... (slow)

# Use batch edits:
files_to_edit = [file1, file2, file3, ..., file10]
for file in files_to_edit:
    apply_migration(file)  # Apply all patterns

# Then verify all at once
for file in files_to_edit:
    compile_test(file)
```

### Verification Script
```bash
# After each batch, verify
for file in batch*.txt; do
    python3 -m py_compile "$file" && echo "✅ $file" || echo "❌ $file"
done
```

---

## CRITICAL INSTRUCTIONS FOR AGENT

**YOU MUST**:

1. **Work in batches of 10 files** - Do NOT process files one at a time
2. **Report after each batch** - Show progress every 10 files
3. **Verify compilation** - Test all 10 files compile before next batch
4. **Use consistent patterns** - Apply same transformations across all files
5. **Track progress** - Maintain count of total files/usages migrated

**DO NOT**:
- Process files sequentially (too slow)
- Skip verification steps
- Stop at first error (log and continue)
- Report after every single file (too verbose)

---

## BATCH COMPLETION REPORT FORMAT

```
BATCH X COMPLETE (Files XX-XX):
- Files migrated: 10/10 ✅
- Total usages in batch: 127
- Total usages migrated: 127
- Compilation success: 10/10 ✅
- Cumulative progress: XX/60 files (YY%)

Remaining: XX files, ~ZZZ usages
```

---

## FINAL STEPS AFTER ALL BATCHES

1. **Verify zero legacy usage**:
   ```bash
   grep -r "\.nodes\[" dawsos/ --include="*.py" | grep -v __pycache__ | grep -v "_graph.nodes" | wc -l
   # Must be 0

   grep -r "for.*in.*\.edges:" dawsos/ --include="*.py" | grep -v __pycache__ | grep -v "_graph.edges" | wc -l
   # Must be 0
   ```

2. **Remove legacy @property methods** from knowledge_graph.py

3. **Run full test suite**:
   ```bash
   pytest dawsos/tests/validation/ -v
   ```

4. **Final report**:
   ```
   Phase 3.2 COMPLETE:
   - Total files migrated: 60
   - Total usages migrated: ~800
   - Batches executed: 6
   - Legacy properties removed: YES ✅
   - All tests passing: YES ✅
   ```

---

## START EXECUTION NOW

Begin with Batch 1 (10 agent files). Process all 10 simultaneously, then report batch completion.

**GO!**
