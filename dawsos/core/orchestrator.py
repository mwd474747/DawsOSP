"""Agent Orchestrator - Coordinates agent execution"""
from typing import Dict, Any, List, Optional
from core.agent_runtime import AgentRuntime

class AgentOrchestrator:
    """Coordinates multiple agents to accomplish complex tasks"""

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.execution_plan = []

    def plan(self, user_input: str) -> List[Dict[str, Any]]:
        """Plan which agents to use for a task"""
        # Get Claude's interpretation
        claude_response = self.runtime.execute('claude', {"user_input": user_input})

        intent = claude_response.get('intent', 'unknown')

        # Create execution plan based on intent
        plan = []

        if intent == 'ADD_DATA':
            plan = [
                {"agent": "data_harvester", "purpose": "fetch data"},
                {"agent": "data_digester", "purpose": "create nodes"},
                {"agent": "relationship_hunter", "purpose": "find connections"}
            ]

        elif intent == 'FORECAST':
            plan = [
                {"agent": "graph_mind", "purpose": "analyze graph state"},
                {"agent": "pattern_spotter", "purpose": "find patterns"},
                {"agent": "forecast_dreamer", "purpose": "make prediction"}
            ]

        elif intent == 'ANALYZE':
            plan = [
                {"agent": "pattern_spotter", "purpose": "spot patterns"},
                {"agent": "relationship_hunter", "purpose": "hunt relationships"},
                {"agent": "graph_mind", "purpose": "synthesize insights"}
            ]

        elif intent == 'BUILD':
            plan = [
                {"agent": "structure_bot", "purpose": "find file location"},
                {"agent": "code_monkey", "purpose": "write code"},
                {"agent": "refactor_elf", "purpose": "check complexity"}
            ]

        self.execution_plan = plan
        return plan

    def execute_plan(self) -> List[Dict[str, Any]]:
        """Execute the planned agent sequence"""
        results = []

        for step in self.execution_plan:
            agent = step['agent']
            result = self.runtime.execute(agent, {})
            results.append({
                "agent": agent,
                "purpose": step['purpose'],
                "result": result
            })

            # Stop on error
            if isinstance(result, dict) and 'error' in result:
                break

        return results

    def coordinate(self, user_input: str) -> Dict[str, Any]:
        """Full coordination: plan and execute"""
        # Plan
        plan = self.plan(user_input)

        # Execute
        results = self.execute_plan()

        # Check if workflow should be recorded
        if all('error' not in r['result'] for r in results if isinstance(r['result'], dict)):
            self.runtime.execute('workflow_recorder', {
                "interaction": {
                    "user_input": user_input,
                    "plan": plan,
                    "results": results,
                    "success": True
                }
            })

        return {
            "plan": plan,
            "results": results,
            "summary": self._summarize_results(results)
        }

    def _summarize_results(self, results: List[Dict[str, Any]]) -> str:
        """Create a summary of execution results"""
        if not results:
            return "No actions taken"

        successful = sum(1 for r in results if 'error' not in r.get('result', {}))
        total = len(results)

        if successful == total:
            return f"Successfully executed {total} agents"
        elif successful > 0:
            return f"Partially complete: {successful}/{total} agents succeeded"
        else:
            return "Execution failed"