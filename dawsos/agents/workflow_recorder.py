"""WorkflowRecorder - Records successful patterns for reuse"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
from datetime import datetime
import json

class WorkflowRecorder(BaseAgent):
    """Records successful interaction patterns"""

    def __init__(self, graph=None, llm_client=None):
        super().__init__("WorkflowRecorder", graph, llm_client)
        self.vibe = "studious"
        self.workflows = []
        self.patterns = {}

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are WorkflowRecorder, learning from success.

        Interaction: {context.get('interaction', {})}
        User intent: {context.get('intent', 'unknown')}
        Actions taken: {context.get('actions', [])}
        Result: {context.get('result', {})}
        Success: {context.get('success', False)}

        Should we remember this as a workflow?
        If yes, extract:
        - trigger: what started this
        - steps: what we did
        - outcome: what happened
        - reusable: can we do this again?
        - pattern_name: short name for this pattern
        """

    def record(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Record a successful interaction"""
        context = {
            "interaction": interaction,
            "intent": interaction.get('intent'),
            "actions": interaction.get('actions', []),
            "result": interaction.get('result'),
            "success": interaction.get('success', False)
        }

        # Decide if worth recording
        decision = self.think(context)

        if decision.get('remember', False):
            workflow = self._create_workflow(interaction, decision)
            self.workflows.append(workflow)

            # Check if this forms a pattern
            self._identify_pattern(workflow)

        # Store result in knowledge graph
        result = {
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            node_id = self.store_result(result)
            result['node_id'] = node_id
        return result
                "status": "recorded",
                "workflow_id": workflow['id'],
                "pattern": workflow.get('pattern_name')
            }

        # Store result in knowledge graph
        result = {"status": "not_recorded", "reason": "Not significant enough"}
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            node_id = self.store_result(result)
            result['node_id'] = node_id
        return result

    def _create_workflow(self, interaction: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
        """Create a workflow from an interaction"""
        workflow = {
            "id": f"workflow_{datetime.now().timestamp()}",
            "trigger": decision.get('trigger', interaction.get('intent')),
            "steps": decision.get('steps', interaction.get('actions', [])),
            "outcome": decision.get('outcome', interaction.get('result')),
            "pattern_name": decision.get('pattern_name', 'unnamed'),
            "created": datetime.now().isoformat(),
            "uses": 1,
            "success_rate": 1.0,
            "reusable": decision.get('reusable', True)
        }
        return workflow

    def _identify_pattern(self, workflow: Dict[str, Any]):
        """Check if workflow matches existing patterns"""
        pattern_name = workflow.get('pattern_name')

        if pattern_name not in self.patterns:
            self.patterns[pattern_name] = {
                "name": pattern_name,
                "workflows": [],
                "common_trigger": workflow.get('trigger'),
                "common_steps": workflow.get('steps'),
                "success_count": 0
            }

        # Add to pattern
        self.patterns[pattern_name]['workflows'].append(workflow['id'])
        self.patterns[pattern_name]['success_count'] += 1

        # After 3 similar workflows, mark as established pattern
        if len(self.patterns[pattern_name]['workflows']) >= 3:
            self._save_pattern(self.patterns[pattern_name])

    def _save_pattern(self, pattern: Dict[str, Any]):
        """Save an established pattern"""
        # Save to storage/patterns.json
        try:
            with open('storage/patterns.json', 'r') as f:
                all_patterns = json.load(f)
        except:
            all_patterns = {}

        all_patterns[pattern['name']] = pattern

        with open('storage/patterns.json', 'w') as f:
            json.dump(all_patterns, f, indent=2)

    def find_similar(self, interaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find workflows similar to current interaction"""
        similar = []

        intent = interaction.get('intent', '')

        for workflow in self.workflows:
            similarity = 0

            # Check trigger similarity
            if workflow.get('trigger') == intent:
                similarity += 0.5

            # Check if steps overlap
            current_steps = set(str(s) for s in interaction.get('actions', []))
            workflow_steps = set(str(s) for s in workflow.get('steps', []))
            if current_steps.intersection(workflow_steps):
                similarity += 0.3

            # Check if outcomes similar
            if str(workflow.get('outcome')) in str(interaction.get('expected_outcome', '')):
                similarity += 0.2

            if similarity > 0.3:
                similar.append({
                    "workflow": workflow,
                    "similarity": similarity
                })

        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:5]

class StepLogger(BaseAgent):
    """Sub-agent that logs individual steps"""

    def __init__(self, llm_client=None):
        super().__init__("StepLogger", None, llm_client)
        self.vibe = "meticulous"

class SuccessJudge(BaseAgent):
    """Sub-agent that judges if something succeeded"""

    def __init__(self, llm_client=None):
        super().__init__("SuccessJudge", None, llm_client)
        self.vibe = "fair"

    def judge(self, result: Any, expectation: Any) -> bool:
        """Judge if result meets expectation"""
        # Simple heuristic for now
        if result is None:
            return False
        if isinstance(result, dict) and 'error' in result:
            return False
        if isinstance(result, dict) and 'success' in result:
            return result['success']
        return True

class TemplateExtractor(BaseAgent):
    """Sub-agent that extracts reusable templates"""

    def __init__(self, llm_client=None):
        super().__init__("TemplateExtractor", None, llm_client)
        self.vibe = "abstract"