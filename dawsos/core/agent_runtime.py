"""Agent Runtime - Executes and coordinates agents"""
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union, Callable
from core.typing_compat import TypeAlias
from types import MappingProxyType
import json
import os
import traceback
import logging
from datetime import datetime
from core.agent_adapter import AgentRegistry

# Avoid circular imports
if TYPE_CHECKING:
    from core.pattern_engine import PatternEngine
    from core.universal_executor import UniversalExecutor
    from core.knowledge_graph import KnowledgeGraph


# Type aliases for robustness and clarity
AgentName: TypeAlias = str
AgentContext: TypeAlias = Dict[str, Any]
AgentResult: TypeAlias = Dict[str, Any]
ExecutionMetrics: TypeAlias = Dict[str, Any]
CapabilityDict: TypeAlias = Dict[str, Any]
TelemetryData: TypeAlias = Dict[str, Any]

class AgentRuntime:
    """Simple runtime for executing agents"""

    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.active_agents: List[str] = []
        self.pattern_engine: Optional['PatternEngine'] = None  # Will be initialized after agents
        self.agent_registry: AgentRegistry = AgentRegistry()  # Agent registry for capabilities
        self.use_adapter: bool = True  # Flag to enable/disable adapter usage
        self.executor: Optional['UniversalExecutor'] = None  # Will be set by outer orchestration
        self.graph: Optional['KnowledgeGraph'] = None  # Optional shared graph reference

        # Trinity compliance guardrails
        self._access_warnings_enabled: bool = True
        self._strict_mode: bool = os.getenv('TRINITY_STRICT_MODE', 'false').lower() == 'true'
        self.logger: logging.Logger = logging.getLogger('AgentRuntime')

        # Telemetry tracking
        self.telemetry: List[Dict[str, Any]] = []
        self.telemetry_summary: Dict[str, Any] = {
            'total_executions': 0,
            'success_count': 0,
            'total_duration_ms': 0.0,
            'executions_by_agent': {},
            'executions_by_pattern': {},
            'last_execution_time': None
        }

    def register_agent(self, name: AgentName, agent: Any, capabilities: Optional[CapabilityDict] = None) -> None:
        """Register an agent with the runtime"""
        self._agents[name] = agent

        # Also register with adapter if enabled
        if self.use_adapter:
            self.agent_registry.register(name, agent, capabilities)

        self.logger.info(f"Registered agent: {name}")

    def execute(self, agent_name: AgentName, context: AgentContext) -> AgentResult:
        """Execute agent through unified adapter with automatic Trinity compliance"""
        adapter = self.agent_registry.get_agent(agent_name)
        if not adapter:
            return {"error": f"Agent {agent_name} not found"}

        # Mark as active
        self.active_agents.append(agent_name)

        try:
            # ALWAYS use registry for Trinity compliance
            result = self.agent_registry.execute_with_tracking(agent_name, context)

            # Log execution
            self._log_execution(agent_name, context, result)

            return result
        except Exception as e:
            return {"error": str(e)}
        finally:
            # Remove from active
            if agent_name in self.active_agents:
                self.active_agents.remove(agent_name)

    def delegate(self, task: AgentContext) -> AgentResult:
        """Delegate task to appropriate agent"""
        task_type = task.get('type', 'unknown')

        # Map task types to agents
        agent_map = {
            'add_data': 'data_harvester',
            'create_node': 'data_digester',
            'find_relationship': 'relationship_hunter',
            'make_forecast': 'forecast_dreamer',
            'spot_pattern': 'pattern_spotter',
            'write_code': 'code_monkey',
            'organize_files': 'structure_bot',
            'simplify_code': 'refactor_elf',
            'record_workflow': 'workflow_recorder',
            'replay_workflow': 'workflow_player'
        }

        agent_name = agent_map.get(task_type)
        if agent_name and self.has_agent(agent_name):
            return self.execute(agent_name, task)

        return {"error": f"No agent for task type: {task_type}"}

    def orchestrate(self, user_input: str) -> AgentResult:
        """Main orchestration entry point that delegates to the UniversalExecutor."""
        if self.executor:
            request = {
                'type': 'chat_input',
                'user_input': user_input
            }
            return self.executor.execute(request)

        # Executor not configured - fall back to local pattern engine if available
        if self.pattern_engine:
            pattern = self.pattern_engine.find_pattern(user_input)
            if pattern:
                context = {'user_input': user_input}
                return self.pattern_engine.execute_pattern(pattern, context)

        return {"error": "Executor not configured"}

    def get_compliance_metrics(self) -> ExecutionMetrics:
        """Get Trinity Architecture compliance metrics for all agents"""
        return self.agent_registry.get_compliance_metrics()

    def _log_execution(self, agent_name: AgentName, context: AgentContext, result: AgentResult) -> None:
        """Log agent execution"""
        execution = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "result": result
        }

        self.execution_history.append(execution)

        # Keep last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

        # Also save to file
        self._save_to_agent_memory(execution)

    def _save_to_agent_memory(self, execution: Dict[str, Any]) -> None:
        """Save execution to agent memory with automatic rotation"""
        memory_file = 'storage/agent_memory/decisions.json'

        try:
            # Rotate if file is too large (>5MB)
            if os.path.exists(memory_file):
                file_size_mb = os.path.getsize(memory_file) / (1024 * 1024)
                if file_size_mb > 5:
                    self._rotate_decisions_file(memory_file)

            # Load existing
            if os.path.exists(memory_file):
                with open(memory_file, 'r') as f:
                    decisions = json.load(f)
            else:
                decisions = []

            # Add new
            decisions.append(execution)

            # Keep last 1000
            if len(decisions) > 1000:
                decisions = decisions[-1000:]

            # Save
            os.makedirs(os.path.dirname(memory_file), exist_ok=True)
            with open(memory_file, 'w') as f:
                json.dump(decisions, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving to agent memory for {agent_name}: {e}", exc_info=True)

    def track_execution(self, metrics: ExecutionMetrics) -> None:
        """
        Track execution metrics for telemetry.
        Called by PatternEngine's track_execution action.

        Args:
            metrics: Dictionary containing:
                - success: bool
                - error: Optional error message
                - duration_ms: Execution duration in milliseconds
                - timestamp: ISO format timestamp
                - pattern_id: Pattern identifier
                - agent_used: Agent name
                - graph_stored: Whether data was stored in graph
        """
        # Append to telemetry list
        self.telemetry.append(metrics)

        # Keep last 1000 executions
        if len(self.telemetry) > 1000:
            self.telemetry = self.telemetry[-1000:]

        # Update summary stats
        self.telemetry_summary['total_executions'] += 1

        if metrics.get('success', True):
            self.telemetry_summary['success_count'] += 1

        if metrics.get('duration_ms') is not None:
            self.telemetry_summary['total_duration_ms'] += metrics['duration_ms']

        # Track by agent
        agent_name = metrics.get('agent_used')
        if agent_name:
            if agent_name not in self.telemetry_summary['executions_by_agent']:
                self.telemetry_summary['executions_by_agent'][agent_name] = 0
            self.telemetry_summary['executions_by_agent'][agent_name] += 1

        # Track by pattern
        pattern_id = metrics.get('pattern_id')
        if pattern_id:
            if pattern_id not in self.telemetry_summary['executions_by_pattern']:
                self.telemetry_summary['executions_by_pattern'][pattern_id] = 0
            self.telemetry_summary['executions_by_pattern'][pattern_id] += 1

        # Update last execution time
        self.telemetry_summary['last_execution_time'] = metrics.get('timestamp')

        self.logger.debug(f"Telemetry tracked: {pattern_id} by {agent_name}")

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """
        Get aggregated telemetry summary.

        Returns:
            Dictionary containing:
                - total_executions: Total number of executions tracked
                - success_rate: Success percentage
                - avg_duration_ms: Average execution duration
                - executions_by_agent: Top 10 agents by execution count
                - executions_by_pattern: Top 10 patterns by execution count
                - last_execution_time: ISO timestamp of last execution
        """
        total = self.telemetry_summary['total_executions']
        success_count = self.telemetry_summary['success_count']
        total_duration = self.telemetry_summary['total_duration_ms']

        # Calculate success rate
        success_rate = (success_count / total * 100) if total > 0 else 0.0

        # Calculate average duration
        avg_duration_ms = (total_duration / total) if total > 0 else 0.0

        # Get top 10 agents
        agents_sorted = sorted(
            self.telemetry_summary['executions_by_agent'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        top_agents = dict(agents_sorted)

        # Get top 10 patterns
        patterns_sorted = sorted(
            self.telemetry_summary['executions_by_pattern'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        top_patterns = dict(patterns_sorted)

        return {
            'total_executions': total,
            'success_rate': round(success_rate, 2),
            'avg_duration_ms': round(avg_duration_ms, 2),
            'executions_by_agent': top_agents,
            'executions_by_pattern': top_patterns,
            'last_execution_time': self.telemetry_summary['last_execution_time']
        }

    def _rotate_decisions_file(self, memory_file: str):
        """Rotate decisions file when it gets too large"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_dir = 'storage/agent_memory/archive'
            os.makedirs(archive_dir, exist_ok=True)

            archive_file = os.path.join(archive_dir, f'decisions_{timestamp}.json')
            os.rename(memory_file, archive_file)
            self.logger.info(f"Rotated decisions file to {archive_file}")
        except Exception as e:
            self.logger.error(f"Error rotating decisions file: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get runtime status"""
        return {
            "registered_agents": list(self._agents.keys()),
            "active_agents": self.active_agents,
            "total_executions": len(self.execution_history),
            "recent_executions": self.execution_history[-5:]
        }

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down agent runtime...")
        # Save final state
        self._save_state()

    def _save_state(self):
        """Save runtime state"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "agents": list(self._agents.keys()),
            "execution_count": len(self.execution_history)
        }

        try:
            with open('storage/agent_memory/runtime_state.json', 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving runtime state: {e}", exc_info=True)

    def execute_by_capability(self, capability: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using an agent with specific capability"""
        if self.use_adapter:
            return self.agent_registry.execute_by_capability(capability, context)

        # Fallback: find agent by name pattern
        capability_to_agent = {
            'fetch_data': 'data_harvester',
            'detect_patterns': 'pattern_spotter',
            'find_correlations': 'relationship_hunter',
            'forecast': 'forecast_dreamer',
            'structure_data': 'data_digester'
        }

        agent_name = capability_to_agent.get(capability)
        if agent_name and self.has_agent(agent_name):
            return self.execute(agent_name, context)

        return {'error': f'No agent found with capability: {capability}'}

    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all registered agents"""
        if self.use_adapter:
            return self.agent_registry.get_all_capabilities()

        # Basic capability listing
        capabilities = {}
        for name, agent in self._agents.items():
            capabilities[name] = {
                'name': name,
                'class': agent.__class__.__name__,
                'has_graph': hasattr(agent, 'graph'),
                'has_llm': hasattr(agent, 'llm_client')
            }
        return capabilities

    def has_agent(self, name: str) -> bool:
        """Check if an agent is registered"""
        return name in self._agents

    def get_agent_instance(self, name: str) -> Optional[Any]:
        """Get the raw agent instance by name"""
        adapter = self.agent_registry.get_agent(name)
        if adapter:
            return adapter.agent
        return self._agents.get(name)

    def iter_agent_instances(self):
        """Iterate over registered agent instances"""
        for name, adapter in self.agent_registry.agents.items():
            yield name, adapter.agent

    @property
    def agents(self) -> MappingProxyType:
        """
        Read-only view of registered agent instances (DEPRECATED - legacy access)

        WARNING: Direct agent access bypasses Trinity Architecture compliance.
        Use exec_via_registry() instead for proper graph storage and tracking.

        Example:
            # DEPRECATED (bypasses Trinity):
            agent = runtime.agents['agent_name']
            result = agent.process(context)

            # RECOMMENDED (Trinity compliant):
            result = runtime.exec_via_registry('agent_name', context)

        This property logs bypass warnings and will raise errors in strict mode.
        Set TRINITY_STRICT_MODE=true environment variable to enforce compliance.
        """
        if self._access_warnings_enabled:
            # Get caller information from stack trace
            stack = traceback.extract_stack()
            # Go back 2 frames: current property -> caller
            if len(stack) >= 2:
                caller_frame = stack[-2]
                caller_info = f"{caller_frame.filename}:{caller_frame.lineno} in {caller_frame.name}"
            else:
                caller_info = "Unknown caller"

            # Log bypass warning
            warning_msg = (
                f"TRINITY BYPASS WARNING: Direct .agents access from {caller_info}. "
                f"Use exec_via_registry() instead for Trinity compliance."
            )

            if self._strict_mode:
                # In strict mode, raise an error
                error_msg = (
                    f"TRINITY STRICT MODE: Direct agent access is prohibited!\n"
                    f"Caller: {caller_info}\n"
                    f"Use runtime.exec_via_registry(agent_name, context) instead of runtime.agents[agent_name]"
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                # In warning mode, just log
                self.logger.warning(warning_msg)

            # Log to registry for tracking
            self.agent_registry.log_bypass_warning(caller_info, "agents", "property_access")

        return MappingProxyType(self._agents)

    def exec_via_registry(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanctioned path for executing agents through the registry.
        This is the recommended way to call agents from patterns, UI, and other code.
        """
        return self.execute(agent_name, context)

    def disable_access_warnings(self):
        """
        Disable access warnings for internal use cases where direct access is legitimate.

        WARNING: Only use this for backward compatibility during migration.
        Should be removed once all code is updated to use exec_via_registry().

        Example:
            runtime.disable_access_warnings()
            agent = runtime.agents['agent_name']  # No warning
        """
        self._access_warnings_enabled = False
        self.logger.info("Trinity access warnings disabled (legacy compatibility mode)")
