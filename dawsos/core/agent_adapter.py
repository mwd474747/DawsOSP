"""
Agent Adapter - Provides consistent interface for all agents
This allows agents with different method signatures to work uniformly
"""
from typing import Dict, Any, Optional, Protocol, runtime_checkable, List
from core.typing_compat import TypeAlias
from datetime import datetime


# Type aliases for robustness and clarity
AgentName: TypeAlias = str
AgentContext: TypeAlias = Dict[str, Any]
AgentResult: TypeAlias = Dict[str, Any]
CapabilityDict: TypeAlias = Dict[str, Any]
MethodName: TypeAlias = str
ComplianceMetrics: TypeAlias = Dict[str, Any]


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

    def __init__(self, agent: Any, capabilities: Optional[CapabilityDict] = None) -> None:
        """
        Initialize adapter with an agent instance

        Args:
            agent: The agent to wrap
            capabilities: Optional capabilities metadata from AGENT_CAPABILITIES
        """
        self.agent = agent
        self.metadata_capabilities = capabilities  # Store metadata separately for capability routing
        self.capabilities = capabilities or {}  # Keep for backward compatibility
        self.method_priority = ['process', 'think', 'analyze', 'interpret', 'harvest', 'execute']
        self._detect_methods()

    def _detect_methods(self) -> None:
        """Detect which methods the agent implements"""
        self.available_methods = {}
        for method_name in self.method_priority:
            if hasattr(self.agent, method_name) and callable(getattr(self.agent, method_name)):
                self.available_methods[method_name] = getattr(self.agent, method_name)

    def execute(self, context: AgentContext) -> AgentResult:
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

        # NEW: Check for capability-based routing
        if 'capability' in context:
            capability_result = self._execute_by_capability(context)
            if capability_result:
                return capability_result
            # If capability routing fails, fall through to legacy routing

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

    def _execute_by_capability(self, context: AgentContext) -> Optional[AgentResult]:
        """
        Execute agent method via capability routing

        Maps capability to method name and extracts parameters using introspection.
        Returns None if capability routing fails (allows fallback to legacy routing).
        """
        import inspect
        import logging

        logger = logging.getLogger('AgentAdapter')
        capability = context.get('capability', '')

        # Map capability to method name (remove 'can_' prefix)
        method_name = capability.replace('can_', '') if capability.startswith('can_') else capability

        # Check if agent has this method
        if not hasattr(self.agent, method_name) or not callable(getattr(self.agent, method_name)):
            logger.warning(f"Agent {self.agent.__class__.__name__} does not have method '{method_name}' for capability '{capability}'")
            return None

        method = getattr(self.agent, method_name)

        try:
            # Extract method parameters using introspection
            sig = inspect.signature(method)
            params = {}

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Try exact match first
                if param_name in context:
                    params[param_name] = context[param_name]
                # Try common variations
                elif param_name == 'symbol' and 'ticker' in context:
                    params[param_name] = context['ticker']
                elif param_name == 'ticker' and 'symbol' in context:
                    params[param_name] = context['symbol']
                elif param_name == 'tickers' and 'symbols' in context:
                    params[param_name] = context['symbols']
                elif param_name == 'symbols' and 'tickers' in context:
                    params[param_name] = context['tickers']
                # Use default if available
                elif param.default != inspect.Parameter.empty:
                    params[param_name] = param.default
                # If context is expected, pass full context
                elif param_name == 'context':
                    params[param_name] = context

            # Call method with extracted parameters
            result = method(**params)

            # Ensure result is a dictionary
            if not isinstance(result, dict):
                result = {'response': str(result)}

            # Add metadata
            result['agent'] = self.agent.__class__.__name__
            result['method_used'] = method_name
            result['capability'] = capability
            result['timestamp'] = datetime.now().isoformat()

            # AUTO-STORE RESULT IN GRAPH (Trinity Compliance)
            if hasattr(self.agent, 'graph') and self.agent.graph:
                try:
                    if hasattr(self.agent, 'store_result'):
                        node_id = self.agent.store_result(result, context)
                    elif hasattr(self.agent, 'add_knowledge'):
                        node_id = self.agent.add_knowledge(
                            f'{self.agent.__class__.__name__.lower()}_result',
                            result
                        )
                    else:
                        node_id = self.agent.graph.add_node(
                            f'{self.agent.__class__.__name__.lower()}_result',
                            {'result': result, 'context': context, 'timestamp': result['timestamp']}
                        )

                    if node_id:
                        result['node_id'] = node_id
                        result['graph_stored'] = True
                except Exception as e:
                    logger.warning(f"Failed to store result in graph: {e}")
                    result['graph_stored'] = False

            logger.info(f"Successfully executed capability '{capability}' via method '{method_name}'")
            return result

        except Exception as e:
            logger.error(f"Error executing capability '{capability}' via method '{method_name}': {e}")
            return None

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get agent's declared capabilities for capability-based routing.

        Returns metadata capabilities (strings) instead of runtime capabilities (objects)
        to enable proper capability lookups in AgentRegistry.find_capable_agent().
        """
        # PRIORITY 1: Return metadata capabilities if available
        if self.metadata_capabilities:
            # Convert list format to dict format for compatibility
            if isinstance(self.metadata_capabilities.get('capabilities'), list):
                caps_dict = {cap: True for cap in self.metadata_capabilities['capabilities']}
                return caps_dict
            return self.metadata_capabilities

        # PRIORITY 2: Use agent.capabilities only if it's capability strings (not objects)
        if hasattr(self.agent, 'capabilities'):
            caps = self.agent.capabilities
            # Check if it's capability objects (has 'market', 'fred', etc.) vs strings
            if caps and not isinstance(next(iter(caps.values()), None), type):
                return caps  # It's already capability strings

        # PRIORITY 3: Infer capabilities from class name and methods
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

    @property
    def adapters(self) -> Dict[str, AgentAdapter]:
        """
        Backward compatibility property for accessing agents.

        Note: In Trinity 2.0, the internal attribute is 'agents' not 'adapters',
        but this property maintains compatibility with documentation and legacy code.

        Returns:
            Dict mapping agent names to AgentAdapter instances
        """
        return self.agents

    def register(self, name: AgentName, agent: Any, capabilities: Optional[CapabilityDict] = None) -> None:
        """Register an agent with optional capabilities"""
        adapter = AgentAdapter(agent, capabilities)
        self.agents[name] = adapter
        self.capabilities_map[name] = adapter.get_capabilities()

    def get_agent(self, name: AgentName) -> Optional[AgentAdapter]:
        """Get agent by name"""
        return self.agents.get(name)

    def find_capable_agent(self, capability: str) -> Optional[str]:
        """
        Find agent with specific capability.

        Handles both dict and list capability formats for robustness.
        """
        for name, caps in self.capabilities_map.items():
            # Handle dict format: {'can_fetch_data': True, 'can_analyze': True}
            if isinstance(caps, dict) and (capability in caps or caps.get(capability)):
                return name
            # Handle list format: ['can_fetch_data', 'can_analyze']
            elif isinstance(caps, list) and capability in caps:
                return name
        return None

    def execute_by_capability(self, capability: str, context: AgentContext) -> AgentResult:
        """Execute using first agent with required capability"""
        agent_name = self.find_capable_agent(capability)
        if agent_name:
            return self.agents[agent_name].execute(context)
        return {'error': f'No agent found with capability: {capability}'}

    def get_all_capabilities(self) -> Dict[str, Dict]:
        """Get capabilities of all registered agents"""
        return self.capabilities_map.copy()

    def execute_with_tracking(self, agent_name: AgentName, context: AgentContext) -> AgentResult:
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

    def get_compliance_metrics(self) -> ComplianceMetrics:
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