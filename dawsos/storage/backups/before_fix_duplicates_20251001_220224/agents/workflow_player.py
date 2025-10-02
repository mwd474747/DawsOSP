"""WorkflowPlayer - Replays recorded workflows"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
import json

class WorkflowPlayer(BaseAgent):
    """Replays successful workflows"""

    def __init__(self, llm_client=None):
        super().__init__("WorkflowPlayer", None, llm_client)
        self.vibe = "efficient"
        self.loaded_workflows = {}
        self.load_workflows()

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are WorkflowPlayer, replaying successful patterns.

        Current context: {context.get('current', {})}
        Available workflow: {context.get('workflow', {})}
        Parameters to fill: {context.get('parameters', [])}

        How should we adapt this workflow?
        Return:
        - can_use: true/false
        - adaptations: what to change
        - parameters: filled parameters
        - confidence: how well does it match (0-1)
        """

    def load_workflows(self):
        """Load saved workflows from storage"""
        try:
            with open('storage/workflows.json', 'r') as f:
                self.loaded_workflows = json.load(f)
        except:
            self.loaded_workflows = {}

        try:
            with open('storage/patterns.json', 'r') as f:
                patterns = json.load(f)
                # Convert patterns to playable workflows
                for name, pattern in patterns.items():
                    self.loaded_workflows[f"pattern_{name}"] = {
                        "trigger": pattern.get('common_trigger'),
                        "steps": pattern.get('common_steps'),
                        "pattern": True
                    }
        except:
            pass

    def find_applicable(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find workflows applicable to current context"""
        applicable = []

        user_input = context.get('user_input', '')
        intent = context.get('intent', '')

        for workflow_id, workflow in self.loaded_workflows.items():
            # Check if trigger matches
            if self._matches_trigger(workflow.get('trigger'), intent, user_input):
                applicable.append({
                    "workflow_id": workflow_id,
                    "workflow": workflow,
                    "match_score": self._calculate_match_score(workflow, context)
                })

        return sorted(applicable, key=lambda x: x['match_score'], reverse=True)

    def play(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_id not in self.loaded_workflows:
            return {"error": f"Workflow {workflow_id} not found"}

        workflow = self.loaded_workflows[workflow_id]

        # Check if we can use this workflow
        adaptation_context = {
            "current": context,
            "workflow": workflow,
            "parameters": self._extract_parameters(workflow)
        }
        adaptation = self.think(adaptation_context)

        if not adaptation.get('can_use', False):
            return {"error": "Workflow not applicable to current context"}

        # Execute steps
        results = []
        for step in workflow.get('steps', []):
            step_result = self._execute_step(step, context, adaptation.get('parameters', {}))
            results.append(step_result)

            # Stop on error
            if isinstance(step_result, dict) and 'error' in step_result:
                break

        return {
            "workflow_id": workflow_id,
            "executed": True,
            "results": results,
            "success": all(r.get('success', False) if isinstance(r, dict) else True for r in results)
        }

    def _matches_trigger(self, trigger: Any, intent: str, user_input: str) -> bool:
        """Check if trigger matches current context"""
        if not trigger:
            return False

        trigger_str = str(trigger).lower()
        return (intent.lower() in trigger_str or
                trigger_str in intent.lower() or
                trigger_str in user_input.lower())

    def _calculate_match_score(self, workflow: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate how well workflow matches context"""
        score = 0.0

        # Trigger match
        if self._matches_trigger(workflow.get('trigger'), context.get('intent', ''), context.get('user_input', '')):
            score += 0.5

        # Check if context has required data
        required_data = self._extract_parameters(workflow)
        available_data = set(context.keys())
        if required_data:
            overlap = len(set(required_data).intersection(available_data))
            score += 0.3 * (overlap / len(required_data))

        # Pattern workflows get bonus
        if workflow.get('pattern'):
            score += 0.2

        return min(score, 1.0)

    def _extract_parameters(self, workflow: Dict[str, Any]) -> List[str]:
        """Extract parameters needed for workflow"""
        parameters = []

        # Simple extraction from steps
        for step in workflow.get('steps', []):
            if isinstance(step, dict):
                # Look for placeholders like {symbol} or <parameter>
                step_str = str(step)
                if '{' in step_str:
                    # Extract {param} style parameters
                    import re
                    params = re.findall(r'{(\w+)}', step_str)
                    parameters.extend(params)

        return list(set(parameters))

    def _execute_step(self, step: Any, context: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        # Fill in parameters
        if isinstance(step, str):
            for param, value in parameters.items():
                step = step.replace(f'{{{param}}}', str(value))

        # In real implementation, would execute actual actions
        # For now, return mock success
        return {
            "step": step,
            "success": True,
            "result": "Step executed"
        }

class ContextMatcher(BaseAgent):
    """Sub-agent that matches contexts"""

    def __init__(self, llm_client=None):
        super().__init__("ContextMatcher", None, llm_client)
        self.vibe = "precise"

class ParameterFiller(BaseAgent):
    """Sub-agent that fills workflow parameters"""

    def __init__(self, llm_client=None):
        super().__init__("ParameterFiller", None, llm_client)
        self.vibe = "adaptive"

class Executor(BaseAgent):
    """Sub-agent that executes workflow steps"""

    def __init__(self, llm_client=None):
        super().__init__("Executor", None, llm_client)
        self.vibe = "action-oriented"