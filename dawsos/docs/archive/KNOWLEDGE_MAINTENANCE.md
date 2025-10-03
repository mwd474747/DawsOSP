# Knowledge Graph Maintenance Guide

## Core Principle: Knowledge as Data, Not Code

The system is designed so knowledge updates only affect agent decisions, not system operation.

## 1. Safe Knowledge Update Points

### Editable Without System Impact:
```
/knowledge/
├── enriched_data/        # ✅ Agent knowledge bases
├── governance_policies.json # ✅ Governance rules
├── market_data.json      # ✅ Market information
└── ui_configurations.json # ✅ UI settings

/patterns/
├── */                     # ✅ All pattern definitions
└── *.json                 # ✅ Pattern workflows

/storage/
├── knowledge_base/        # ✅ Persistent knowledge
└── graph_snapshots/       # ✅ Graph backups
```

### Never Edit (System Core):
```
/core/                     # ❌ System architecture
/agents/base_agent.py      # ❌ Agent framework
/core/knowledge_graph.py   # ❌ Graph engine
/core/pattern_engine.py    # ❌ Pattern executor
```

## 2. Knowledge Update Strategies

### A. Hot Reload Pattern
```python
# The system already supports live knowledge updates:
# 1. Update JSON files in /knowledge/
# 2. Pattern Engine reloads automatically
# 3. Agents use new knowledge on next request
```

### B. Versioned Knowledge
```bash
# Create versioned knowledge snapshots
cp -r knowledge/ knowledge_v1.0/
# Make changes
# Test with A/B comparison
# Rollback if needed
cp -r knowledge_v1.0/ knowledge/
```

### C. Graph Evolution
```python
# The graph self-maintains through governance
graph_governance.evolve_graph(auto_execute=True)
# This updates connections and quality scores
# Without changing system behavior
```

## 3. Testing Knowledge Changes

### Pattern Testing
```json
{
  "id": "test_knowledge_update",
  "name": "Knowledge Update Validator",
  "description": "Test knowledge changes before deployment",
  "steps": [
    {
      "agent": "governance",
      "action": "validate_knowledge",
      "parameters": {
        "old_knowledge": "{backup_path}",
        "new_knowledge": "{current_path}",
        "run_regression": true
      }
    }
  ]
}
```

### Impact Analysis
Before updating knowledge, ask:
- "What patterns use this knowledge?"
- "Which agents depend on this data?"
- "Show me downstream impacts of changing X"

## 4. Knowledge Schema Management

### Flexible Schema Design
```json
{
  "node_type": "market_data",
  "required_fields": ["symbol", "timestamp"],
  "optional_fields": ["price", "volume", "metadata"],
  "version": "1.0",
  "backward_compatible": true
}
```

### Migration Patterns
```python
# Add fields without breaking existing:
old_node["new_field"] = default_value

# Rename fields with compatibility:
if "old_name" in node:
    node["new_name"] = node.pop("old_name")
```

## 5. Governance for Knowledge Updates

### Pre-Update Checks
1. **Quality Gate**: New knowledge must pass quality threshold
2. **Schema Validation**: Must match expected structure
3. **Relationship Integrity**: Can't break existing connections
4. **Policy Compliance**: Must follow governance rules

### Post-Update Monitoring
- Track agent performance changes
- Monitor confidence scores
- Watch for anomalies
- Measure prediction accuracy

## 6. Knowledge Update Workflows

### Manual Update
```bash
# 1. Backup current knowledge
python3 -c "from core.knowledge_graph import KnowledgeGraph; g = KnowledgeGraph(); g.save_graph('backup.json')"

# 2. Update knowledge files
edit knowledge/enriched_data/*.json

# 3. Validate changes
python3 test_system_health.py

# 4. Deploy or rollback
```

### API-Based Update
```python
# Safe knowledge update via governance
governance_agent.process_request(
    "Update market data for AAPL",
    context={"validation": "required"}
)
```

### Pattern-Based Update
```
"Refresh all market data older than 24 hours"
"Update governance policies from template"
"Sync knowledge base with external source"
```

## 7. Knowledge Isolation Techniques

### Namespace Separation
```python
# Separate knowledge by domain
knowledge_graph.add_node('market.AAPL', {...})
knowledge_graph.add_node('governance.policy1', {...})
knowledge_graph.add_node('user.preferences', {...})
```

### Capability Boundaries
```python
# Agents only access their knowledge domain
class DataHarvester:
    allowed_namespaces = ['market', 'economic']

class GovernanceAgent:
    allowed_namespaces = ['governance', 'audit']
```

## 8. Rollback and Recovery

### Automatic Snapshots
```python
# System creates snapshots before major updates
def update_knowledge(self, new_data):
    self.create_snapshot(f"pre_update_{timestamp}")
    # Apply update
    if validation_fails:
        self.restore_snapshot()
```

### Manual Recovery
```bash
# List available snapshots
ls storage/graph_snapshots/

# Restore specific version
cp storage/graph_snapshots/graph_20251002.json knowledge/current.json
```

## 9. Knowledge Quality Metrics

Monitor these to ensure updates improve outcomes:
- **Accuracy**: Prediction vs actual
- **Completeness**: Required fields present
- **Freshness**: Age of data
- **Consistency**: No conflicting information
- **Coverage**: Breadth of knowledge

## 10. Best Practices

### DO:
✅ Version control knowledge files separately from code
✅ Test knowledge updates in isolation
✅ Monitor agent performance after updates
✅ Use governance patterns for validation
✅ Maintain backward compatibility
✅ Document knowledge schemas
✅ Create rollback points

### DON'T:
❌ Mix knowledge updates with code changes
❌ Update core graph structure
❌ Skip validation steps
❌ Make breaking schema changes
❌ Update during critical operations
❌ Ignore governance warnings

## Quick Commands

```bash
# Backup current knowledge
./backup_knowledge.sh

# Validate knowledge integrity
python3 -c "from agents.governance_agent import GovernanceAgent; g = GovernanceAgent(); g.validate_with_pattern('validate all', {})"

# Check knowledge quality
echo "Check data quality" | python3 main.py

# Evolution cycle
echo "Run self improvement" | python3 main.py
```

## Key Insight

The Trinity architecture (Pattern-Knowledge-Agent) naturally separates:
- **Patterns**: HOW to do things (workflows)
- **Knowledge**: WHAT to know (data)
- **Agents**: WHO does things (actors)

Updates to Knowledge only change WHAT agents know, not HOW they work or WHO they are.

This separation ensures system stability while allowing knowledge evolution.