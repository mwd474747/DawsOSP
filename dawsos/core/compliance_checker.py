#!/usr/bin/env python3
"""
Compliance Checker - Runtime validator for Trinity Architecture compliance

This module enforces Trinity execution patterns:
- Validates patterns before execution
- Monitors agent access at runtime
- Provides compliance reports
- Respects TRINITY_STRICT_MODE environment variable

All agent interactions must flow through the registry, not direct references.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ComplianceViolation:
    """Represents a single compliance violation"""

    def __init__(
        self,
        violation_type: str,
        severity: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        self.violation_type = violation_type
        self.severity = severity  # 'error', 'warning', 'info'
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary"""
        return {
            'type': self.violation_type,
            'severity': self.severity,
            'message': self.message,
            'context': self.context,
            'timestamp': self.timestamp
        }


class ComplianceChecker:
    """
    Runtime compliance validator for Trinity Architecture

    Validates that:
    - Patterns use execute_through_registry for agent access
    - No direct agent references in patterns
    - All patterns have required metadata
    - Agent names exist in registry
    """

    def __init__(self, agent_registry=None, strict_mode: Optional[bool] = None):
        """
        Initialize compliance checker

        Args:
            agent_registry: AgentRegistry instance for validation
            strict_mode: Override for TRINITY_STRICT_MODE env var
        """
        self.agent_registry = agent_registry

        # Determine strict mode
        if strict_mode is not None:
            self.strict_mode = strict_mode
        else:
            self.strict_mode = os.getenv('TRINITY_STRICT_MODE', 'false').lower() == 'true'

        # Tracking
        self.violations: List[ComplianceViolation] = []
        self.pattern_checks: Dict[str, Dict[str, Any]] = {}
        self.agent_access_log: List[Dict[str, Any]] = []

        # Statistics
        self.stats = {
            'patterns_checked': 0,
            'patterns_compliant': 0,
            'patterns_non_compliant': 0,
            'agent_accesses_monitored': 0,
            'violations_by_type': defaultdict(int),
            'violations_by_severity': defaultdict(int)
        }

        logger.info(f"ComplianceChecker initialized (strict_mode={self.strict_mode})")

    def check_pattern(self, pattern_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate pattern structure and compliance

        Args:
            pattern_dict: Pattern dictionary to validate

        Returns:
            Dictionary with validation results:
            {
                'compliant': bool,
                'violations': List[ComplianceViolation],
                'warnings': List[str],
                'pattern_id': str
            }
        """
        self.stats['patterns_checked'] += 1
        pattern_id = pattern_dict.get('id', 'unknown')

        violations = []
        warnings = []

        # Check 1: Pattern must have required metadata
        violations.extend(self._check_pattern_metadata(pattern_dict))

        # Check 2: Validate steps for Trinity compliance
        step_violations, step_warnings = self._check_pattern_steps(pattern_dict)
        violations.extend(step_violations)
        warnings.extend(step_warnings)

        # Check 3: Validate agent references
        violations.extend(self._check_agent_references(pattern_dict))

        # Determine compliance status
        # Pattern is compliant if it has no errors
        # Warnings are noted but don't affect compliance status
        has_errors = any(v.severity == 'error' for v in violations)
        has_warnings = any(v.severity == 'warning' for v in violations)

        # In strict mode, warnings count as non-compliant
        # In normal mode, only errors count as non-compliant
        compliant = not has_errors and (not has_warnings or not self.strict_mode)

        if compliant:
            self.stats['patterns_compliant'] += 1
        else:
            self.stats['patterns_non_compliant'] += 1

        # Store violations
        for v in violations:
            self.violations.append(v)
            self.stats['violations_by_type'][v.violation_type] += 1
            self.stats['violations_by_severity'][v.severity] += 1

        # Cache result
        result = {
            'compliant': compliant,
            'violations': [v.to_dict() for v in violations],
            'warnings': warnings,
            'pattern_id': pattern_id,
            'checked_at': datetime.now().isoformat()
        }

        self.pattern_checks[pattern_id] = result

        # In strict mode, log all violations
        if self.strict_mode and violations:
            for v in violations:
                if v.severity == 'error':
                    logger.error(f"Pattern {pattern_id}: {v.message}")
                else:
                    logger.warning(f"Pattern {pattern_id}: {v.message}")

        return result

    def _check_pattern_metadata(self, pattern: Dict[str, Any]) -> List[ComplianceViolation]:
        """Validate required pattern metadata"""
        violations = []

        # Required fields
        if 'version' not in pattern:
            violations.append(ComplianceViolation(
                violation_type='missing_metadata',
                severity='warning',
                message='Pattern missing version field',
                context={'pattern_id': pattern.get('id')}
            ))

        if 'last_updated' not in pattern:
            violations.append(ComplianceViolation(
                violation_type='missing_metadata',
                severity='warning',
                message='Pattern missing last_updated field',
                context={'pattern_id': pattern.get('id')}
            ))

        if 'id' not in pattern:
            violations.append(ComplianceViolation(
                violation_type='missing_metadata',
                severity='error',
                message='Pattern missing id field',
                context={}
            ))

        return violations

    def _check_pattern_steps(
        self,
        pattern: Dict[str, Any]
    ) -> tuple[List[ComplianceViolation], List[str]]:
        """
        Validate pattern steps for Trinity compliance

        Returns:
            (violations, warnings)
        """
        violations = []
        warnings = []

        steps = pattern.get('steps', pattern.get('workflow', []))

        for i, step in enumerate(steps):
            step_violations, step_warnings = self.validate_step(step, i)
            violations.extend(step_violations)
            warnings.extend(step_warnings)

        return violations, warnings

    def validate_step(self, step_dict: Dict[str, Any], step_index: int = 0) -> tuple[List[ComplianceViolation], List[str]]:
        """
        Check individual pattern step for compliance

        Args:
            step_dict: Step dictionary to validate
            step_index: Index of step in pattern

        Returns:
            (violations, warnings)
        """
        violations = []
        warnings = []

        action = step_dict.get('action')
        agent = step_dict.get('agent')

        # Rule: If step has 'agent' field, must use execute_through_registry
        if agent:
            if action != 'execute_through_registry':
                # Check if it's a legacy direct agent call
                # This is ALWAYS an error since it violates Trinity Architecture
                violations.append(ComplianceViolation(
                    violation_type='direct_agent_reference',
                    severity='error',  # Always error - direct references violate Trinity
                    message=f"Step {step_index} has direct agent reference '{agent}' but action is '{action}'. "
                            f"Must use action='execute_through_registry'",
                    context={
                        'step_index': step_index,
                        'agent': agent,
                        'action': action
                    }
                ))
            else:
                # Valid: using execute_through_registry
                # Verify agent exists in registry
                if self.agent_registry and not self.agent_registry.get_agent(agent):
                    warnings.append(
                        f"Step {step_index} references agent '{agent}' not found in registry"
                    )

        # Check for legacy action patterns that bypass registry
        if action and action.startswith('agent:'):
            # Old pattern: action='agent:data_harvester'
            warnings.append(
                f"Step {step_index} uses legacy action format '{action}'. "
                f"Consider migrating to execute_through_registry"
            )

        return violations, warnings

    def _check_agent_references(self, pattern: Dict[str, Any]) -> List[ComplianceViolation]:
        """Check that all agent references exist in registry"""
        violations = []

        if not self.agent_registry:
            return violations

        # Extract all agent references from pattern
        agent_refs = self._extract_agent_references(pattern)

        # Validate each reference
        for agent_name in agent_refs:
            if not self.agent_registry.get_agent(agent_name):
                violations.append(ComplianceViolation(
                    violation_type='invalid_agent_reference',
                    severity='error',
                    message=f"Pattern references unknown agent '{agent_name}'",
                    context={
                        'pattern_id': pattern.get('id'),
                        'agent': agent_name
                    }
                ))

        return violations

    def _extract_agent_references(self, pattern: Dict[str, Any]) -> Set[str]:
        """Extract all agent names referenced in pattern"""
        agent_refs = set()

        steps = pattern.get('steps', pattern.get('workflow', []))

        for step in steps:
            # Direct agent field
            if 'agent' in step:
                agent_refs.add(step['agent'])

            # Legacy action format: action='agent:name'
            action = step.get('action', '')
            if action.startswith('agent:'):
                agent_name = action.replace('agent:', '')
                agent_refs.add(agent_name)

        return agent_refs

    def check_agent_access(self, caller_module: str, agent_name: str = None) -> Dict[str, Any]:
        """
        Monitor who accesses agents at runtime

        Args:
            caller_module: Name of module accessing agents (e.g., 'pattern_engine', 'ui.dashboard')
            agent_name: Optional specific agent being accessed

        Returns:
            Dictionary with access check results
        """
        self.stats['agent_accesses_monitored'] += 1

        access_log = {
            'timestamp': datetime.now().isoformat(),
            'caller': caller_module,
            'agent': agent_name,
            'compliant': True,
            'warning': None
        }

        # Check if caller is allowed to access agents directly
        allowed_callers = [
            'agent_runtime',
            'agent_adapter',
            'universal_executor',
            'pattern_engine'  # Pattern engine can access via _get_agent
        ]

        # Check for direct access from unauthorized modules
        if caller_module not in allowed_callers:
            access_log['compliant'] = False
            access_log['warning'] = (
                f"Module '{caller_module}' accessing agents directly. "
                f"Should use AgentRuntime.execute() or pattern-based execution."
            )

            if self.strict_mode:
                logger.warning(access_log['warning'])

        self.agent_access_log.append(access_log)

        # Keep only recent 1000 accesses
        if len(self.agent_access_log) > 1000:
            self.agent_access_log = self.agent_access_log[-1000:]

        return access_log

    def get_compliance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive compliance summary

        Returns:
            Dictionary with:
            - Overall compliance rate
            - Violations by type and severity
            - Pattern-level compliance
            - Agent access patterns
            - Recommendations
        """
        total_patterns = self.stats['patterns_checked']
        compliant_patterns = self.stats['patterns_compliant']

        compliance_rate = (
            (compliant_patterns / total_patterns * 100)
            if total_patterns > 0 else 100.0
        )

        # Recent violations (last 50)
        recent_violations = [v.to_dict() for v in self.violations[-50:]]

        # Agent access analysis
        total_accesses = len(self.agent_access_log)
        non_compliant_accesses = sum(
            1 for log in self.agent_access_log if not log['compliant']
        )

        access_compliance_rate = (
            ((total_accesses - non_compliant_accesses) / total_accesses * 100)
            if total_accesses > 0 else 100.0
        )

        # Generate recommendations
        recommendations = self._generate_recommendations()

        report = {
            'generated_at': datetime.now().isoformat(),
            'strict_mode': self.strict_mode,
            'overall': {
                'pattern_compliance_rate': round(compliance_rate, 2),
                'agent_access_compliance_rate': round(access_compliance_rate, 2),
                'total_patterns_checked': total_patterns,
                'compliant_patterns': compliant_patterns,
                'non_compliant_patterns': self.stats['patterns_non_compliant']
            },
            'violations': {
                'total': len(self.violations),
                'by_type': dict(self.stats['violations_by_type']),
                'by_severity': dict(self.stats['violations_by_severity']),
                'recent': recent_violations
            },
            'agent_access': {
                'total_monitored': total_accesses,
                'non_compliant_accesses': non_compliant_accesses,
                'recent_access_log': self.agent_access_log[-20:]
            },
            'pattern_details': self.pattern_checks,
            'recommendations': recommendations
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on violations"""
        recommendations = []

        # Check for common violation patterns
        violation_types = self.stats['violations_by_type']

        if violation_types.get('direct_agent_reference', 0) > 0:
            recommendations.append(
                "Migrate patterns with direct agent references to use "
                "action='execute_through_registry'"
            )

        if violation_types.get('missing_metadata', 0) > 0:
            recommendations.append(
                "Add version and last_updated fields to all patterns"
            )

        if violation_types.get('invalid_agent_reference', 0) > 0:
            recommendations.append(
                "Verify all agent names in patterns match registered agents"
            )

        # Check agent access patterns
        non_compliant_callers = defaultdict(int)
        for log in self.agent_access_log:
            if not log['compliant']:
                non_compliant_callers[log['caller']] += 1

        if non_compliant_callers:
            top_offenders = sorted(
                non_compliant_callers.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]

            for caller, count in top_offenders:
                recommendations.append(
                    f"Module '{caller}' has {count} direct agent accesses. "
                    f"Refactor to use AgentRuntime.execute()"
                )

        if not recommendations:
            recommendations.append("All systems Trinity-compliant!")

        return recommendations

    def get_pattern_compliance_status(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get compliance status for specific pattern

        Args:
            pattern_id: ID of pattern to check

        Returns:
            Compliance status dictionary or None if not found
        """
        return self.pattern_checks.get(pattern_id)

    def reset_stats(self):
        """Reset all statistics and logs (useful for testing)"""
        self.violations = []
        self.pattern_checks = {}
        self.agent_access_log = []
        self.stats = {
            'patterns_checked': 0,
            'patterns_compliant': 0,
            'patterns_non_compliant': 0,
            'agent_accesses_monitored': 0,
            'violations_by_type': defaultdict(int),
            'violations_by_severity': defaultdict(int)
        }
        logger.info("ComplianceChecker stats reset")

    def export_report(self, filepath: str):
        """
        Export compliance report to JSON file

        Args:
            filepath: Path to save report
        """
        import json

        report = self.get_compliance_report()

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Compliance report exported to {filepath}")


# Singleton instance for global access
_compliance_checker_instance: Optional[ComplianceChecker] = None


def get_compliance_checker(
    agent_registry=None,
    strict_mode: Optional[bool] = None
) -> ComplianceChecker:
    """
    Get or create the global ComplianceChecker instance

    Args:
        agent_registry: AgentRegistry instance (only used on first call)
        strict_mode: Override for TRINITY_STRICT_MODE

    Returns:
        ComplianceChecker singleton
    """
    global _compliance_checker_instance

    if _compliance_checker_instance is None:
        _compliance_checker_instance = ComplianceChecker(agent_registry, strict_mode)

    return _compliance_checker_instance
