# ComplianceChecker Integration Guide

## Overview

The `ComplianceChecker` module enforces Trinity Architecture compliance at runtime by validating patterns and monitoring agent access. It ensures that all agent interactions flow through the proper registry-based execution path rather than direct references.

## Core Features

1. **Pattern Validation** - Validates pattern structure before execution
2. **Agent Access Monitoring** - Tracks who accesses agents at runtime
3. **Compliance Reporting** - Generates detailed compliance metrics
4. **Strict Mode Support** - Respects `TRINITY_STRICT_MODE` environment variable

## Integration Points

### 1. PatternEngine Integration

The PatternEngine should call `check_pattern()` before executing patterns:

```python
from core.compliance_checker import get_compliance_checker

class PatternEngine:
    def __init__(self, pattern_dir: str = 'patterns', runtime=None):
        self.runtime = runtime
        self.compliance_checker = get_compliance_checker(
            agent_registry=runtime.agent_registry if runtime else None
        )
        # ... rest of initialization

    def execute_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any] = None):
        # Validate pattern compliance before execution
        compliance_result = self.compliance_checker.check_pattern(pattern)

        if not compliance_result['compliant']:
            # Log violations
            for violation in compliance_result['violations']:
                if violation['severity'] == 'error':
                    self.logger.error(f"Pattern compliance error: {violation['message']}")

        # Continue with execution (warnings don't block execution)
        # ... rest of execute_pattern logic
```

### 2. AgentRuntime Integration

The AgentRuntime should call `check_agent_access()` when the `.agents` property is accessed:

```python
from core.compliance_checker import get_compliance_checker

class AgentRuntime:
    def __init__(self):
        self.compliance_checker = get_compliance_checker()
        # ... rest of initialization

    @property
    def agents(self):
        """Monitor direct agent access"""
        # Get caller information
        import traceback
        stack = traceback.extract_stack()
        caller_frame = stack[-2]
        caller_module = caller_frame.filename

        # Log access
        self.compliance_checker.check_agent_access(caller_module)

        return MappingProxyType(self._agents)
```

### 3. Dashboard Integration

The dashboard should call `get_compliance_report()` to display metrics:

```python
from core.compliance_checker import get_compliance_checker

def render_governance_tab():
    checker = get_compliance_checker()
    report = checker.get_compliance_report()

    # Display metrics
    st.metric("Pattern Compliance Rate", f"{report['overall']['pattern_compliance_rate']}%")
    st.metric("Compliant Patterns", report['overall']['compliant_patterns'])
    st.metric("Total Violations", report['violations']['total'])

    # Show recommendations
    st.subheader("Recommendations")
    for rec in report['recommendations']:
        st.info(rec)
```

## Validation Rules

### Pattern Structure Rules

1. **Required Metadata**
   - `version` field (warning if missing)
   - `last_updated` field (warning if missing)
   - `id` field (error if missing)

2. **Agent Reference Rules**
   - Steps with `agent` field MUST use `action='execute_through_registry'` (error)
   - All agent names must exist in registry (error)

3. **Legacy Format Detection**
   - `action='agent:name'` generates migration warning

### Compliant Pattern Example

```json
{
  "id": "my_pattern",
  "name": "My Pattern",
  "version": "1.0",
  "last_updated": "2025-10-02",
  "steps": [
    {
      "agent": "data_harvester",
      "action": "execute_through_registry",
      "params": {
        "request": "fetch data"
      }
    }
  ]
}
```

### Non-Compliant Pattern Example

```json
{
  "id": "legacy_pattern",
  "name": "Legacy Pattern",
  "steps": [
    {
      "agent": "data_harvester",
      "action": "harvest",  // ERROR: Should be execute_through_registry
      "params": {
        "request": "fetch data"
      }
    }
  ]
}
```

## Usage Examples

### Basic Pattern Validation

```python
from core.compliance_checker import ComplianceChecker
from core.agent_adapter import AgentRegistry

# Setup
registry = AgentRegistry()
registry.register('my_agent', agent_instance)

checker = ComplianceChecker(agent_registry=registry)

# Validate pattern
pattern = {
    'id': 'test_pattern',
    'version': '1.0',
    'last_updated': '2025-10-02',
    'steps': [...]
}

result = checker.check_pattern(pattern)

if result['compliant']:
    print("Pattern is compliant!")
else:
    print("Violations found:")
    for v in result['violations']:
        print(f"  - {v['message']}")
```

### Individual Step Validation

```python
step = {
    'agent': 'data_harvester',
    'action': 'execute_through_registry',
    'params': {}
}

violations, warnings = checker.validate_step(step, step_index=0)

if violations:
    print(f"Step has {len(violations)} violations")
```

### Agent Access Monitoring

```python
# Monitor access from different modules
result = checker.check_agent_access('ui.dashboard', 'financial_analyst')

if not result['compliant']:
    print(f"Warning: {result['warning']}")
```

### Generate Compliance Report

```python
report = checker.get_compliance_report()

print(f"Pattern Compliance: {report['overall']['pattern_compliance_rate']}%")
print(f"Total Violations: {report['violations']['total']}")

# Export to file
checker.export_report('compliance_report.json')
```

## Strict Mode

Set the `TRINITY_STRICT_MODE` environment variable to enforce stricter compliance:

```bash
export TRINITY_STRICT_MODE=true
```

In strict mode:
- Warnings count as non-compliant (not just errors)
- All violations are logged immediately
- Useful for pre-production testing

## Compliance Report Structure

```json
{
  "generated_at": "2025-10-02T12:00:00",
  "strict_mode": false,
  "overall": {
    "pattern_compliance_rate": 75.0,
    "agent_access_compliance_rate": 90.0,
    "total_patterns_checked": 20,
    "compliant_patterns": 15,
    "non_compliant_patterns": 5
  },
  "violations": {
    "total": 8,
    "by_type": {
      "direct_agent_reference": 3,
      "missing_metadata": 4,
      "invalid_agent_reference": 1
    },
    "by_severity": {
      "error": 4,
      "warning": 4
    },
    "recent": [...]
  },
  "agent_access": {
    "total_monitored": 100,
    "non_compliant_accesses": 10,
    "recent_access_log": [...]
  },
  "pattern_details": {...},
  "recommendations": [
    "Migrate patterns with direct agent references...",
    "Add version and last_updated fields..."
  ]
}
```

## Testing

Run the compliance tests:

```bash
cd dawsos
python3 tests/test_compliance.py
```

Run the demo:

```bash
cd dawsos
python3 examples/compliance_demo.py
```

## Migration Checklist

To migrate legacy patterns to Trinity-compliant format:

- [ ] Add `version` field to all patterns
- [ ] Add `last_updated` field to all patterns
- [ ] Replace direct agent actions with `execute_through_registry`
- [ ] Verify all agent names exist in registry
- [ ] Remove legacy `action='agent:name'` format
- [ ] Update UI/API code to use `AgentRuntime.execute()`
- [ ] Run compliance report to verify

## Common Issues

### Issue: "Pattern references unknown agent"

**Solution**: Verify agent is registered in AgentRegistry:

```python
runtime.register_agent('my_agent', agent_instance)
```

### Issue: "Direct agent reference" violation

**Solution**: Change step action to `execute_through_registry`:

```json
{
  "agent": "data_harvester",
  "action": "execute_through_registry",  // Fixed
  "params": {...}
}
```

### Issue: High non-compliant access rate

**Solution**: Refactor code to use proper execution path:

```python
# BEFORE (non-compliant)
agent = runtime.agents['my_agent']
result = agent.process(context)

# AFTER (compliant)
result = runtime.execute('my_agent', context)
```

## Future Enhancements

Planned improvements:

1. Auto-migration tool for legacy patterns
2. Real-time compliance dashboard
3. Integration with CI/CD pipeline
4. Pattern versioning and deprecation tracking
5. Automated remediation suggestions

## Support

For questions or issues:
- Check the demo: `examples/compliance_demo.py`
- Review tests: `tests/test_compliance.py`
- See core implementation: `core/compliance_checker.py`
