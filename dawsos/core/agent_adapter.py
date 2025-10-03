"""
Agent Adapter - Provides consistent interface for all agents
This allows agents with different method signatures to work uniformly
"""
from typing import Dict, Any, Optional, Protocol, runtime_checkable, List
from datetime import datetime


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol defining expected agent interface"""
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]: ...
    def process(self, context: Any) -> Dict[str, Any]: ...
    def analyze(self, query: str) -> Dict[str, Any]: ...


class AgentAdapter:
    """
    Wraps agents to provide consistent interface across all agent types
    Handles method resolution and parameter adaptation
    """

    def __init__(self, agent: Any, capabilities: Optional[Dict] = None):
        """
        Initialize adapter with an agent instance

        Args:
            agent: The agent to wrap
            capabilities: Optional capabilities to inject
        """
        self.agent = agent
        self.capabilities = capabilities or {}
        self.method_priority = ['process', 'think', 'analyze', 'interpret', 'harvest', 'execute']
        self._detect_methods()

    def _detect_methods(self):
        """Detect which methods the agent implements"""
        self.available_methods = {}
        for method_name in self.method_priority:
            if hasattr(self.agent, method_name) and callable(getattr(self.agent, method_name)):
                self.available_methods[method_name] = getattr(self.agent, method_name)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent with consistent interface and automatic Trinity compliance

        Args:
            context: Execution context with user_input, data, etc.

        Returns:
            Standardized response dictionary with automatic graph storage
        """
        # Inject capabilities if agent supports them
        if hasattr(self.agent, 'capabilities'):
            self.agent.capabilities = {**self.agent.capabilities, **self.capabilities}

        # Add capabilities to context
        context_with_caps = {**context, 'capabilities': self.capabilities}

        # Try methods in priority order
        for method_name in self.method_priority:
            if method_name in self.available_methods:
                try:
                    method = self.available_methods[method_name]

                    # Adapt parameters based on method signature
                    if method_name == 'analyze':
                        # Analyze typically takes a string query
                        query = context.get('query') or context.get('user_input', '')
                        result = method(query)
                    elif method_name == 'interpret':
                        # Claude's interpret method
                        user_input = context.get('user_input', '')
                        result = method(user_input)
                    elif method_name == 'harvest':
                        # DataHarvester's harvest method
                        request = context.get('request') or context.get('user_input', '')
                        result = method(request)
                    else:
                        # Standard methods take context
                        result = method(context_with_caps)

                    # Ensure result is a dictionary
                    if not isinstance(result, dict):
                        result = {'response': str(result)}

                    # Add metadata
                    result['agent'] = self.agent.__class__.__name__
                    result['method_used'] = method_name
                    result['timestamp'] = datetime.now().isoformat()

                    # AUTO-STORE RESULT IN GRAPH (Trinity Compliance)
                    if hasattr(self.agent, 'graph') and self.agent.graph:
                        try:
                            # Use store_result if available, otherwise add directly
                            if hasattr(self.agent, 'store_result'):
                                node_id = self.agent.store_result(result, context)
                            elif hasattr(self.agent, 'add_knowledge'):
                                node_id = self.agent.add_knowledge(
                                    f'{self.agent.__class__.__name__.lower()}_result',
                                    result
                                )
                            else:
                                # Direct graph access
                                node_id = self.agent.graph.add_node(
                                    f'{self.agent.__class__.__name__.lower()}_result',
                                    {'result': result, 'context': context, 'timestamp': result['timestamp']}
                                )

                            if node_id:
                                result['node_id'] = node_id
                                result['graph_stored'] = True
                        except Exception:
                            # Silent fail - don't break execution
                            result['graph_stored'] = False

                    return result

                except Exception:
                    # Log error but continue trying other methods
                    continue

        # No suitable method found
        return {
            'error': f"No execution method found for {self.agent.__class__.__name__}",
            'available_methods': list(self.available_methods.keys()),
            'agent': self.agent.__class__.__name__
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent's declared capabilities"""
        if hasattr(self.agent, 'capabilities'):
            return self.agent.capabilities

        # Infer capabilities from class name and methods
        capabilities = {
            'name': self.agent.__class__.__name__,
            'methods': list(self.available_methods.keys()),
            'has_llm': hasattr(self.agent, 'llm_client'),
            'has_graph': hasattr(self.agent, 'graph')
        }

        # Infer specific capabilities
        class_name = self.agent.__class__.__name__.lower()
        if 'data' in class_name or 'harvest' in class_name:
            capabilities['can_fetch_data'] = True
        if 'pattern' in class_name:
            capabilities['can_detect_patterns'] = True
        if 'relationship' in class_name or 'correlation' in class_name:
            capabilities['can_find_relationships'] = True
        if 'forecast' in class_name or 'predict' in class_name:
            capabilities['can_forecast'] = True

        return capabilities

    def supports_method(self, method_name: str) -> bool:
        """Check if agent supports a specific method"""
        return method_name in self.available_methods

    def __repr__(self) -> str:
        return f"AgentAdapter({self.agent.__class__.__name__}, methods={list(self.available_methods.keys())})"


class AgentRegistry:
    """
    Registry for managing agent capabilities and routing with Trinity compliance tracking
    """

    def __init__(self):
        self.agents = {}
        self.capabilities_map = {}
        self.execution_metrics = {}  # Track compliance metrics
        self.bypass_warnings = []  # Track registry bypasses

    def register(self, name: str, agent: Any, capabilities: Optional[Dict] = None):
        """Register an agent with optional capabilities"""
        adapter = AgentAdapter(agent, capabilities)
        self.agents[name] = adapter
        self.capabilities_map[name] = adapter.get_capabilities()

    def get_agent(self, name: str) -> Optional[AgentAdapter]:
        """Get agent by name"""
        return self.agents.get(name)

    def find_capable_agent(self, capability: str) -> Optional[str]:
        """Find agent with specific capability"""
        for name, caps in self.capabilities_map.items():
            if caps.get(capability):
                return name
        return None

    def execute_by_capability(self, capability: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using first agent with required capability"""
        agent_name = self.find_capable_agent(capability)
        if agent_name:
            return self.agents[agent_name].execute(context)
        return {'error': f'No agent found with capability: {capability}'}

    def get_all_capabilities(self) -> Dict[str, Dict]:
        """Get capabilities of all registered agents"""
        return self.capabilities_map.copy()

    def execute_with_tracking(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent and track Trinity compliance"""
        if agent_name not in self.agents:
            return {'error': f'Agent {agent_name} not found'}

        # Execute through adapter
        result = self.agents[agent_name].execute(context)

        # Track metrics with enhanced telemetry
        if agent_name not in self.execution_metrics:
            self.execution_metrics[agent_name] = {
                'total_executions': 0,
                'graph_stored': 0,
                'failures': 0,
                'last_success': None,
                'last_failure': None,
                'failure_reasons': [],
                'capability_tags': self.capabilities_map.get(agent_name, {})
            }

        self.execution_metrics[agent_name]['total_executions'] += 1

        if result.get('graph_stored'):
            self.execution_metrics[agent_name]['graph_stored'] += 1
            self.execution_metrics[agent_name]['last_success'] = datetime.now().isoformat()
        elif 'error' in result:
            self.execution_metrics[agent_name]['failures'] += 1
            self.execution_metrics[agent_name]['last_failure'] = datetime.now().isoformat()

            # Track failure reason
            failure_reason = result.get('error', 'Unknown error')
            self.execution_metrics[agent_name]['failure_reasons'].append({
                'timestamp': datetime.now().isoformat(),
                'reason': failure_reason
            })

            # Keep only last 10 failure reasons
            if len(self.execution_metrics[agent_name]['failure_reasons']) > 10:
                self.execution_metrics[agent_name]['failure_reasons'] = \
                    self.execution_metrics[agent_name]['failure_reasons'][-10:]

        return result

    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get Trinity Architecture compliance metrics for all agents"""
        metrics = {
            'agents': {},
            'overall_compliance': 0,
            'total_executions': 0,
            'total_stored': 0
        }

        for agent_name, agent_metrics in self.execution_metrics.items():
            total = agent_metrics['total_executions']
            stored = agent_metrics['graph_stored']

            compliance_rate = (stored / total * 100) if total > 0 else 0

            metrics['agents'][agent_name] = {
                'executions': total,
                'stored': stored,
                'compliance_rate': compliance_rate,
                'failures': agent_metrics['failures']
            }

            metrics['total_executions'] += total
            metrics['total_stored'] += stored

        if metrics['total_executions'] > 0:
            metrics['overall_compliance'] = (
                metrics['total_stored'] / metrics['total_executions'] * 100
            )

        return metrics

    def log_bypass_warning(self, caller: str, agent_name: str, method: str):
        """Log when code bypasses the registry to call agents directly"""
        warning = {
            'timestamp': datetime.now().isoformat(),
            'caller': caller,
            'agent': agent_name,
            'method': method,
            'message': f'BYPASS WARNING: {caller} called {agent_name}.{method}() directly, bypassing registry'
        }
        self.bypass_warnings.append(warning)

        # Keep only last 100 warnings
        if len(self.bypass_warnings) > 100:
            self.bypass_warnings = self.bypass_warnings[-100:]

        # Also log to console for visibility
        import logging
        logger = logging.getLogger('AgentRegistry')
        logger.warning(warning['message'])

    def get_bypass_warnings(self, limit: int = 50) -> List[Dict]:
        """Get recent bypass warnings"""
        return self.bypass_warnings[-limit:]