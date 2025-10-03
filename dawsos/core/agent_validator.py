#!/usr/bin/env python3
"""
Agent Validator - Ensures all agents properly use Trinity Architecture
Part of the governance framework to enforce system-wide consistency
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import inspect
import logging

logger = logging.getLogger(__name__)

class AgentValidator:
    """Validates agent compliance with Trinity Architecture principles"""

    def __init__(self, graph=None):
        self.graph = graph
        self.validation_results = {}
        self.compliance_rules = self._load_compliance_rules()

    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Define compliance rules for agents"""
        return {
            'required_methods': {
                'data_producers': [  # Agents that generate data
                    'add_knowledge'  # Only require the essential method
                ],
                'data_consumers': [],  # No strict requirements, they inherit from BaseAgent
                'orchestrators': [  # Only workflow agents need these
                    'execute_workflow'
                ]
            },
            'best_practices': {
                'always_store_results': True,
                'connect_to_context': True,
                'track_lineage': True,
                'validate_inputs': True
            },
            'trinity_principles': {
                'separation_of_concerns': {
                    'knowledge': 'Only data, no logic',
                    'patterns': 'Only workflows, no data',
                    'agents': 'Only actors, no persistent state'
                },
                'graph_integration': {
                    'store_results': 'All computation results must be stored',
                    'maintain_connections': 'All nodes must be connected',
                    'track_provenance': 'All nodes must track their source'
                }
            }
        }

    def validate_agent(self, agent_class, agent_instance=None) -> Dict[str, Any]:
        """Validate a single agent's compliance"""
        validation = {
            'agent_name': agent_class.__name__,
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'warnings': [],
            'compliance_score': 1.0
        }

        # Check if agent uses BaseAgent
        if not self._inherits_from_base_agent(agent_class):
            validation['issues'].append('Does not inherit from BaseAgent')
            validation['compliance_score'] -= 0.5

        # Check for graph usage
        graph_usage = self._check_graph_usage(agent_class)
        validation['graph_integration'] = graph_usage

        if not graph_usage['uses_graph']:
            validation['warnings'].append('No knowledge graph integration detected')
            validation['compliance_score'] -= 0.3

        # Check for proper methods
        method_compliance = self._check_method_compliance(agent_class)
        validation['method_compliance'] = method_compliance

        if method_compliance['missing_critical']:
            validation['issues'].extend([
                f"Missing critical method: {m}"
                for m in method_compliance['missing_critical']
            ])
            validation['compliance_score'] -= 0.2 * len(method_compliance['missing_critical'])

        # Check for anti-patterns
        anti_patterns = self._detect_anti_patterns(agent_class)
        if anti_patterns:
            validation['warnings'].extend(anti_patterns)
            validation['compliance_score'] -= 0.1 * len(anti_patterns)

        # Ensure score is between 0 and 1
        validation['compliance_score'] = max(0, min(1, validation['compliance_score']))

        return validation

    def _inherits_from_base_agent(self, agent_class) -> bool:
        """Check if agent inherits from BaseAgent"""
        try:
            from agents.base_agent import BaseAgent
            return issubclass(agent_class, BaseAgent)
        except:
            return False

    def _check_graph_usage(self, agent_class) -> Dict[str, Any]:
        """Check how agent uses the knowledge graph"""
        try:
            source = inspect.getsource(agent_class)
        except (OSError, TypeError):
            # Can't get source for built-in classes or some dynamic classes
            source = ""

        return {
            'uses_graph': 'self.graph' in source,
            'adds_nodes': 'add_knowledge' in source or 'add_node' in source,
            'creates_connections': 'connect_knowledge' in source or 'connect' in source,
            'queries_graph': 'query_knowledge' in source or 'find_node' in source,
            'stores_results': 'add_knowledge' in source and 'return' in source
        }

    def _check_method_compliance(self, agent_class) -> Dict[str, Any]:
        """Check if agent has required methods"""
        methods = [m for m in dir(agent_class) if not m.startswith('_')]

        # Determine agent type based on name/methods
        agent_type = self._determine_agent_type(agent_class)
        required = self.compliance_rules['required_methods'].get(agent_type, [])

        missing = [m for m in required if m not in methods]

        return {
            'agent_type': agent_type,
            'required_methods': required,
            'missing_critical': missing,
            'has_process': 'process' in methods or 'process_request' in methods
        }

    def _determine_agent_type(self, agent_class) -> str:
        """Determine what type of agent this is"""
        name = agent_class.__name__.lower()

        if any(term in name for term in ['data', 'harvest', 'digest', 'analyst']):
            return 'data_producers'
        elif any(term in name for term in ['pattern', 'spot', 'hunt', 'find', 'relationship']):
            return 'data_consumers'
        elif any(term in name for term in ['workflow', 'orchestrat', 'coordinator']):
            return 'orchestrators'
        else:
            # Default to data_producers as most agents should produce data
            return 'data_producers'

    def _detect_anti_patterns(self, agent_class) -> List[str]:
        """Detect common anti-patterns in agent implementation"""
        anti_patterns = []
        try:
            source = inspect.getsource(agent_class)
        except (OSError, TypeError):
            # Can't get source, skip anti-pattern detection
            return []

        # Check for state storage outside graph
        if 'self._cache' in source or 'self._state' in source:
            if 'self.graph' not in source:
                anti_patterns.append('Stores state locally instead of in graph')

        # Check for hardcoded data
        if 'hardcoded_data = {' in source or 'CONSTANTS = {' in source:
            anti_patterns.append('Contains hardcoded data (should be in knowledge)')

        # Check for workflow logic in agent
        if 'workflow = [' in source or 'steps = [' in source:
            anti_patterns.append('Contains workflow logic (should be in patterns)')

        # Check for missing error handling
        if 'try:' not in source and 'except' not in source:
            anti_patterns.append('No error handling detected')

        return anti_patterns

    def validate_all_agents(self, runtime) -> Dict[str, Any]:
        """Validate all registered agents with runtime metrics"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_agents': 0,
            'compliant': 0,
            'non_compliant': 0,
            'warnings': 0,
            'agents': {},
            'runtime_metrics': None
        }

        # Get runtime compliance metrics if available
        if hasattr(runtime, 'get_compliance_metrics'):
            results['runtime_metrics'] = runtime.get_compliance_metrics()
        elif hasattr(runtime, 'agent_registry') and hasattr(runtime.agent_registry, 'get_compliance_metrics'):
            results['runtime_metrics'] = runtime.agent_registry.get_compliance_metrics()

        if hasattr(runtime, 'iter_agent_instances'):
            agent_iter = runtime.iter_agent_instances()
        elif hasattr(runtime, 'agent_registry'):
            agent_iter = ((name, adapter.agent) for name, adapter in runtime.agent_registry.agents.items())
        else:
            agent_iter = getattr(runtime, 'agents', {}).items()

        for agent_name, agent_instance in agent_iter:
            agent_class = agent_instance.__class__
            validation = self.validate_agent(agent_class, agent_instance)

            # Add runtime metrics if available
            if results['runtime_metrics'] and 'agents' in results['runtime_metrics']:
                agent_runtime_metrics = results['runtime_metrics']['agents'].get(agent_name, {})
                if agent_runtime_metrics:
                    validation['runtime_metrics'] = agent_runtime_metrics
                    # Adjust compliance score based on actual runtime behavior
                    if agent_runtime_metrics.get('compliance_rate', 0) < 50:
                        validation['compliance_score'] *= 0.8
                        validation['warnings'].append(
                            f"Low runtime compliance: {agent_runtime_metrics.get('compliance_rate', 0):.0f}%"
                        )

            results['agents'][agent_name] = validation
            results['total_agents'] += 1

            if validation['compliance_score'] >= 0.8:
                results['compliant'] += 1
            elif validation['compliance_score'] >= 0.5:
                results['warnings'] += 1
            else:
                results['non_compliant'] += 1

        results['overall_compliance'] = (
            results['compliant'] / results['total_agents']
            if results['total_agents'] > 0 else 0
        )

        return results

    def generate_compliance_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable compliance report"""
        report = ["# Agent Compliance Report", ""]
        report.append(f"Generated: {validation_results['timestamp']}")
        report.append(f"Overall Compliance: {validation_results['overall_compliance']:.0%}")
        report.append("")

        report.append("## Summary")
        report.append(f"- Total Agents: {validation_results['total_agents']}")
        report.append(f"- Compliant: {validation_results['compliant']}")
        report.append(f"- Warnings: {validation_results['warnings']}")
        report.append(f"- Non-Compliant: {validation_results['non_compliant']}")
        report.append("")

        report.append("## Agent Details")

        for agent_name, validation in validation_results['agents'].items():
            score = validation['compliance_score']
            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.5 else "❌"

            report.append(f"\n### {status} {agent_name} (Score: {score:.0%})")

            if validation['issues']:
                report.append("**Issues:**")
                for issue in validation['issues']:
                    report.append(f"- {issue}")

            if validation['warnings']:
                report.append("**Warnings:**")
                for warning in validation['warnings']:
                    report.append(f"- {warning}")

            if validation.get('graph_integration'):
                gi = validation['graph_integration']
                report.append("**Graph Integration:**")
                report.append(f"- Uses graph: {gi['uses_graph']}")
                report.append(f"- Adds nodes: {gi['adds_nodes']}")
                report.append(f"- Creates connections: {gi['creates_connections']}")
                report.append(f"- Stores results: {gi['stores_results']}")

            if validation.get('runtime_metrics'):
                rm = validation['runtime_metrics']
                report.append("**Runtime Metrics:**")
                report.append(f"- Total executions: {rm.get('executions', 0)}")
                report.append(f"- Results stored: {rm.get('stored', 0)}")
                report.append(f"- Compliance rate: {rm.get('compliance_rate', 0):.0f}%")
                report.append(f"- Failures: {rm.get('failures', 0)}")

        # Add overall runtime metrics if available
        if validation_results.get('runtime_metrics'):
            metrics = validation_results['runtime_metrics']
            report.append("\n## Runtime Compliance Summary")
            report.append(f"- Overall compliance: {metrics.get('overall_compliance', 0):.0f}%")
            report.append(f"- Total executions: {metrics.get('total_executions', 0)}")
            report.append(f"- Total stored: {metrics.get('total_stored', 0)}")

        return "\n".join(report)

    def enforce_compliance(self, agent_instance, method_name: str, *args, **kwargs):
        """Runtime enforcement wrapper for agent methods"""
        # Pre-execution validation
        if not hasattr(agent_instance, 'graph') or agent_instance.graph is None:
            logger.warning(f"{agent_instance.__class__.__name__}.{method_name} called without graph")

        # Execute method
        result = None
        error = None
        try:
            method = getattr(agent_instance, method_name)
            result = method(*args, **kwargs)
        except Exception as e:
            error = e
            logger.error(f"Error in {agent_instance.__class__.__name__}.{method_name}: {e}")

        # Post-execution validation
        if result and isinstance(result, dict):
            # Check if results were stored in graph
            if 'node_id' not in result and agent_instance.graph:
                logger.warning(
                    f"{agent_instance.__class__.__name__}.{method_name} "
                    "returned results without storing in graph"
                )

        if error:
            raise error

        return result


class ComplianceEnforcer:
    """Decorator and runtime enforcer for agent compliance"""

    def __init__(self, validator: AgentValidator):
        self.validator = validator

    def enforce_method(self, require_graph=True, store_results=True):
        """Decorator to enforce compliance on agent methods"""
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                # Pre-execution checks
                if require_graph and (not hasattr(self, 'graph') or self.graph is None):
                    raise RuntimeError(
                        f"{self.__class__.__name__}.{func.__name__} requires graph but none provided"
                    )

                # Execute function
                result = func(self, *args, **kwargs)

                # Post-execution checks
                if store_results and result and isinstance(result, dict):
                    # Auto-store results if not already stored
                    if 'node_id' not in result and hasattr(self, 'graph') and self.graph:
                        node_data = {
                            'agent': self.__class__.__name__,
                            'method': func.__name__,
                            'result': result,
                            'timestamp': datetime.now().isoformat()
                        }

                        if hasattr(self, 'add_knowledge'):
                            node_id = self.add_knowledge('agent_result', node_data)
                            result['node_id'] = node_id
                            logger.info(f"Auto-stored result from {self.__class__.__name__}.{func.__name__}")

                return result

            return wrapper
        return decorator


def create_compliance_pattern():
    """Create a pattern for agent compliance checking"""
    return {
        "id": "agent_compliance_check",
        "name": "Agent Compliance Validation",
        "trigger": "validate compliance",
        "steps": [
            {
                "agent": "governance_agent",
                "action": "validate_all_agents",
                "save_as": "compliance_results"
            },
            {
                "agent": "governance_agent",
                "action": "generate_report",
                "parameters": {
                    "results": "{compliance_results}"
                },
                "save_as": "report"
            },
            {
                "agent": "governance_agent",
                "action": "store_validation",
                "parameters": {
                    "results": "{compliance_results}",
                    "report": "{report}"
                }
            }
        ],
        "response_template": "{report}"
    }
