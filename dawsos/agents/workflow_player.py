"""WorkflowPlayer - Replays recorded workflows"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

class WorkflowPlayer(BaseAgent):
    """Replays successful workflows"""

    def __init__(self, graph=None, llm_client=None):
        super().__init__("WorkflowPlayer", graph, llm_client)
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
        except FileNotFoundError:
            logger.info("No workflows.json found, starting with empty workflows")
            self.loaded_workflows = {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse workflows.json: {e}")
            self.loaded_workflows = {}
        except Exception as e:
            logger.error(f"Unexpected error loading workflows: {e}", exc_info=True)
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
        except FileNotFoundError:
            logger.debug("No patterns.json found, skipping pattern loading")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse patterns.json: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading patterns: {e}", exc_info=True)

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
            # Workflow not found error
            result = {"error": f"Workflow {workflow_id} not found"}

            # Store result in knowledge graph
            if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
                stored_node_id = self.store_result(result)
                result['stored_node_id'] = stored_node_id

            return result

        workflow = self.loaded_workflows[workflow_id]

        # Check if we can use this workflow
        adaptation_context = {
            "current": context,
            "workflow": workflow,
            "parameters": self._extract_parameters(workflow)
        }
        adaptation = self.think(adaptation_context)

        if not adaptation.get('can_use', False):
            # Workflow not applicable error
            result = {"error": "Workflow not applicable to current context"}

            # Store result in knowledge graph
            if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
                stored_node_id = self.store_result(result)
                result['stored_node_id'] = stored_node_id

            return result

        # Execute steps
        results = []
        for step in workflow.get('steps', []):
            step_result = self._execute_step(step, context, adaptation.get('parameters', {}))
            results.append(step_result)

            # Stop on error
            if isinstance(step_result, dict) and 'error' in step_result:
                break

        # Build result
        result = {
            "workflow_id": workflow_id,
            "executed": True,
            "results": results,
            "success": all(r.get('success', False) if isinstance(r, dict) else True for r in results)
        }

        # Store result in knowledge graph
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            stored_node_id = self.store_result(result)
            result['stored_node_id'] = stored_node_id

        return result

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
        """Execute a single workflow step using Pattern Engine"""
        try:
            # Fill in parameters in step
            if isinstance(step, str):
                for param, value in parameters.items():
                    step = step.replace(f'{{{param}}}', str(value))

            # If step is a pattern reference or action, delegate to Pattern Engine
            if isinstance(step, dict):
                # Step is a structured action
                if 'agent' in step and 'action' in step:
                    # Get pattern engine from capabilities
                    if 'pattern_engine' in self.capabilities:
                        pattern_engine = self.capabilities['pattern_engine']
                        # Execute the action through pattern engine
                        result = pattern_engine._execute_action(step, context)
                        return {
                            "step": step,
                            "success": True,
                            "result": result
                        }
                    else:
                        return {
                            "step": step,
                            "success": False,
                            "error": "Pattern Engine not available"
                        }

                # Step is a pattern execution request
                elif 'pattern' in step:
                    if 'pattern_engine' in self.capabilities:
                        pattern_engine = self.capabilities['pattern_engine']
                        result = pattern_engine.execute_pattern(step['pattern'], parameters, context)
                        return {
                            "step": step,
                            "success": True,
                            "result": result
                        }
                    else:
                        return {
                            "step": step,
                            "success": False,
                            "error": "Pattern Engine not available"
                        }

            # For simple string steps, try to execute as agent requests
            elif isinstance(step, str):
                # Try to parse as agent action
                if 'pattern_engine' in self.capabilities:
                    pattern_engine = self.capabilities['pattern_engine']
                    # Create an action from the string step
                    action = {
                        "action": "process_request",
                        "agent": "claude",  # Default to Claude agent
                        "request": step
                    }
                    result = pattern_engine._execute_action(action, context)
                    return {
                        "step": step,
                        "success": True,
                        "result": result
                    }

            # Fallback for unknown step types
            return {
                "step": step,
                "success": False,
                "error": f"Unknown step type: {type(step)}"
            }

        except Exception as e:
            return {
                "step": step,
                "success": False,
                "error": f"Execution failed: {str(e)}"
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