# ComplianceChecker Quick Reference

## Import and Setup

```python
from core.compliance_checker import get_compliance_checker

# Get singleton instance
checker = get_compliance_checker(agent_registry)
```

## Validate a Pattern

```python
result = checker.check_pattern(pattern_dict)

if result['compliant']:
    print("✓ Pattern is Trinity-compliant")
else:
    print("✗ Violations found:")
    for v in result['violations']:
        print(f"  - [{v['severity']}] {v['message']}")
```

## Validate a Single Step

```python
violations, warnings = checker.validate_step(step_dict, step_index=0)

if violations:
    print(f"Step has {len(violations)} violations")
```

## Monitor Agent Access

```python
result = checker.check_agent_access('my_module', 'agent_name')

if not result['compliant']:
    print(f"Warning: {result['warning']}")
```

## Generate Compliance Report

```python
report = checker.get_compliance_report()

# Display key metrics
print(f"Compliance Rate: {report['overall']['pattern_compliance_rate']}%")
print(f"Total Violations: {report['violations']['total']}")

# Export to file
checker.export_report('compliance_report.json')
```

## Compliant Pattern Example

```json
{
  "id": "my_pattern",
  "version": "1.0",
  "last_updated": "2025-10-02",
  "steps": [
    {
      "agent": "data_harvester",
      "action": "execute_through_registry",
      "params": {"request": "test"}
    }
  ]
}
```

## Common Violations and Fixes

### ❌ Direct Agent Reference
```json
{
  "agent": "data_harvester",
  "action": "harvest",  // ❌ WRONG
  "params": {}
}
```

### ✅ Fixed
```json
{
  "agent": "data_harvester",
  "action": "execute_through_registry",  // ✅ CORRECT
  "params": {}
}
```

### ❌ Missing Metadata
```json
{
  "id": "my_pattern",
  // ❌ Missing version and last_updated
  "steps": [...]
}
```

### ✅ Fixed
```json
{
  "id": "my_pattern",
  "version": "1.0",           // ✅ Added
  "last_updated": "2025-10-02",  // ✅ Added
  "steps": [...]
}
```

### ❌ Invalid Agent Reference
```json
{
  "agent": "nonexistent_agent",  // ❌ Not in registry
  "action": "execute_through_registry"
}
```

### ✅ Fixed
```json
{
  "agent": "data_harvester",  // ✅ Exists in registry
  "action": "execute_through_registry"
}
```

## Validation Rules

| Rule | Severity | Description |
|------|----------|-------------|
| Missing `id` | Error | Pattern must have unique identifier |
| Missing `version` | Warning | Pattern should have version for tracking |
| Missing `last_updated` | Warning | Pattern should have update timestamp |
| Direct agent reference | Error | Must use `execute_through_registry` |
| Invalid agent name | Error | Agent must exist in registry |
| Legacy action format | Warning | `action='agent:name'` should be migrated |

## Strict Mode

Enable strict enforcement:
```bash
export TRINITY_STRICT_MODE=true
```

In strict mode:
- Warnings count as non-compliant
- All violations logged immediately
- Useful for testing/pre-production

## Running Tests

```bash
# Run compliance tests
cd dawsos
python3 tests/test_compliance.py

# Run demo
python3 examples/compliance_demo.py

# Analyze existing patterns
python3 examples/analyze_existing_patterns.py
```

## Integration Examples

### In PatternEngine
```python
def execute_pattern(self, pattern, context):
    # Validate before execution
    result = self.compliance_checker.check_pattern(pattern)

    if not result['compliant']:
        for v in result['violations']:
            if v['severity'] == 'error':
                self.logger.error(f"Pattern {pattern['id']}: {v['message']}")

    # Continue execution (warnings don't block)
    # ...
```

### In Dashboard
```python
def render_compliance_metrics():
    checker = get_compliance_checker()
    report = checker.get_compliance_report()

    st.metric("Pattern Compliance", f"{report['overall']['pattern_compliance_rate']}%")
    st.metric("Total Violations", report['violations']['total'])

    for rec in report['recommendations']:
        st.info(rec)
```

## Quick Checklist

- [ ] Pattern has `id`, `version`, `last_updated` fields
- [ ] All agent steps use `action='execute_through_registry'`
- [ ] All agent names exist in AgentRegistry
- [ ] No legacy `action='agent:name'` format
- [ ] Code uses `runtime.execute()` instead of direct agent access
- [ ] Compliance report shows 100% compliance rate

## Help

- Demo: `examples/compliance_demo.py`
- Tests: `tests/test_compliance.py`
- Full Guide: `docs/COMPLIANCE_CHECKER_INTEGRATION.md`
- Implementation: `core/compliance_checker.py`
