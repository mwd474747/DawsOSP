"""
Agent Adapter - Provides consistent interface for all agents
This allows agents with different method signatures to work uniformly
"""
from typing import Dict, Any, Optional, Protocol, runtime_checkable
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
        Execute agent with consistent interface

        Args:
            context: Execution context with user_input, data, etc.

        Returns:
            Standardized response dictionary
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

                    return result

                except Exception as e:
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
    Registry for managing agent capabilities and routing
    """

    def __init__(self):
        self.agents = {}
        self.capabilities_map = {}

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