"""Agent Runtime - Executes and coordinates agents"""
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime
from core.agent_adapter import AgentAdapter, AgentRegistry

class AgentRuntime:
    """Simple runtime for executing agents"""

    def __init__(self):
        self.agents = {}
        self.execution_history = []
        self.active_agents = []
        self.pattern_engine = None  # Will be initialized after agents are registered
        self.agent_registry = AgentRegistry()  # New: Agent registry for capabilities
        self.use_adapter = True  # Flag to enable/disable adapter usage

    def register_agent(self, name: str, agent: Any, capabilities: Optional[Dict] = None):
        """Register an agent with the runtime"""
        self.agents[name] = agent

        # Also register with adapter if enabled
        if self.use_adapter:
            self.agent_registry.register(name, agent, capabilities)

        print(f"Registered agent: {name}")

    def execute(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent"""
        if agent_name not in self.agents:
            return {"error": f"Agent {agent_name} not found"}

        # Mark as active
        self.active_agents.append(agent_name)

        try:
            # Try to use adapter if available
            if self.use_adapter and self.agent_registry.get_agent(agent_name):
                adapter = self.agent_registry.get_agent(agent_name)
                result = adapter.execute(context)
            else:
                # Fallback to direct execution for backward compatibility
                agent = self.agents[agent_name]
                result = agent.think(context)

            # Log execution
            self._log_execution(agent_name, context, result)

            return result
        except Exception as e:
            return {"error": str(e)}
        finally:
            # Remove from active
            if agent_name in self.active_agents:
                self.active_agents.remove(agent_name)

    def delegate(self, task: Dict[str, Any]) -> Dict[str, Any]:
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
        if agent_name and agent_name in self.agents:
            return self.execute(agent_name, task)

        # Default to Claude
        if 'claude' in self.agents:
            return self.execute('claude', task)

        return {"error": f"No agent for task type: {task_type}"}

    def orchestrate(self, user_input: str) -> Dict[str, Any]:
        """Main orchestration - Claude interprets, delegates to others"""
        # Try pattern engine first
        if self.pattern_engine:
            pattern = self.pattern_engine.find_pattern(user_input)
            if pattern:
                # Execute the pattern
                context = {'user_input': user_input}
                result = self.pattern_engine.execute_pattern(pattern, context)
                return result

        # Fall back to Claude interpretation
        if 'claude' not in self.agents:
            return {"error": "Claude not available"}

        # Get Claude's interpretation
        claude_response = self.execute('claude', {"user_input": user_input})

        # Based on intent, delegate to specialized agents
        intent = claude_response.get('intent', 'unknown')
        results = []

        if intent == 'ADD_DATA':
            # Use data harvester
            harvest_result = self.execute('data_harvester', {
                "request": user_input
            })
            results.append(harvest_result)

            # Then digest it
            if harvest_result and 'error' not in harvest_result:
                digest_result = self.execute('data_digester', {
                    "data": harvest_result,
                    "data_type": "mixed"
                })
                results.append(digest_result)

        elif intent == 'FORECAST':
            # Use forecast dreamer
            target = claude_response.get('entities', [''])[0]
            forecast_result = self.execute('forecast_dreamer', {
                "target": target,
                "horizon": "1d"
            })
            results.append(forecast_result)

        elif intent == 'BUILD':
            # Use code monkey
            code_result = self.execute('code_monkey', {
                "task": claude_response.get('action', 'write code'),
                "file_path": "new_feature.py"
            })
            results.append(code_result)

        elif intent == 'ANALYZE':
            # Use pattern spotter
            pattern_result = self.execute('pattern_spotter', {})
            results.append(pattern_result)

            # And relationship hunter
            relationship_result = self.execute('relationship_hunter', {})
            results.append(relationship_result)

        # Record this workflow if successful
        if all('error' not in r for r in results if isinstance(r, dict)):
            self.execute('workflow_recorder', {
                "interaction": {
                    "user_input": user_input,
                    "intent": intent,
                    "actions": [claude_response] + results,
                    "result": results,
                    "success": True
                }
            })

        return {
            "interpretation": claude_response,
            "results": results,
            "friendly_response": claude_response.get('friendly_response', 'Done!')
        }

    def _log_execution(self, agent_name: str, context: Dict[str, Any], result: Dict[str, Any]):
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

    def _save_to_agent_memory(self, execution: Dict[str, Any]):
        """Save execution to agent memory"""
        memory_file = 'storage/agent_memory/decisions.json'

        try:
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
            print(f"Error saving to agent memory: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get runtime status"""
        return {
            "registered_agents": list(self.agents.keys()),
            "active_agents": self.active_agents,
            "total_executions": len(self.execution_history),
            "recent_executions": self.execution_history[-5:]
        }

    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down agent runtime...")
        # Save final state
        self._save_state()

    def _save_state(self):
        """Save runtime state"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "agents": list(self.agents.keys()),
            "execution_count": len(self.execution_history)
        }

        try:
            with open('storage/agent_memory/runtime_state.json', 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving runtime state: {e}")

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
        if agent_name and agent_name in self.agents:
            return self.execute(agent_name, context)

        return {'error': f'No agent found with capability: {capability}'}

    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all registered agents"""
        if self.use_adapter:
            return self.agent_registry.get_all_capabilities()

        # Basic capability listing
        capabilities = {}
        for name, agent in self.agents.items():
            capabilities[name] = {
                'name': name,
                'class': agent.__class__.__name__,
                'has_graph': hasattr(agent, 'graph'),
                'has_llm': hasattr(agent, 'llm_client')
            }
        return capabilities