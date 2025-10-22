"""WorkflowRecorder - Records successful patterns for reuse

Phase 3.1: Comprehensive type hints added for all methods
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from core.typing_compat import TypeAlias
from datetime import datetime
import json
import logging

# Type aliases for clarity
WorkflowDict: TypeAlias = Dict[str, Any]
PatternDict: TypeAlias = Dict[str, Any]
InteractionDict: TypeAlias = Dict[str, Any]
SimilarList: TypeAlias = List[Dict[str, Any]]

logger = logging.getLogger(__name__)

class WorkflowRecorder(BaseAgent):
    """Records successful interaction patterns"""

    def __init__(
        self,
        graph: Optional[Any] = None,
        llm_client: Optional[Any] = None
    ) -> None:
        """Initialize WorkflowRecorder with graph and optional LLM client.

        Args:
            graph: Optional knowledge graph instance
            llm_client: Optional LLM client for workflow analysis
        """
        super().__init__(graph=graph, name="WorkflowRecorder", llm_client=llm_client)
        self.vibe: str = "studious"
        self.workflows: List[WorkflowDict] = []
        self.patterns: Dict[str, PatternDict] = {}

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

    def record(self, interaction: InteractionDict) -> Dict[str, Any]:
        """Record a successful interaction.

        Args:
            interaction: Dictionary containing interaction data with intent, actions, and result

        Returns:
            Dictionary with recording status and workflow ID if recorded
        """
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

            # Return success result
            result = {
                "status": "recorded",
                "workflow_id": workflow['id'],
                "pattern": workflow.get('pattern_name')
            }
        else:
            # Not significant enough to record
            result = {"status": "not_recorded", "reason": "Not significant enough"}

        # Store result in knowledge graph
        if self.graph and hasattr(self, 'store_result') and isinstance(result, dict):
            stored_node_id = self.store_result(result)
            result['stored_node_id'] = stored_node_id

        return result

    def _create_workflow(self, interaction: InteractionDict, decision: Dict[str, Any]) -> WorkflowDict:
        """Create a workflow from an interaction.

        Args:
            interaction: Interaction data
            decision: Analysis decision about recording

        Returns:
            Workflow dictionary with steps and metadata
        """
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

    def _identify_pattern(self, workflow: WorkflowDict) -> None:
        """Check if workflow matches existing patterns.

        Args:
            workflow: Workflow to analyze for pattern membership
        """
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

    def _save_pattern(self, pattern: PatternDict) -> None:
        """Save an established pattern.

        Args:
            pattern: Pattern dictionary to save to storage/patterns.json
        """
        # Save to storage/patterns.json
        try:
            with open('storage/patterns.json', 'r') as f:
                all_patterns = json.load(f)
        except FileNotFoundError:
            logger.info("Creating new patterns.json file")
            all_patterns = {}
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupted patterns.json, starting fresh: {e}")
            all_patterns = {}
        except Exception as e:
            logger.error(f"Unexpected error reading patterns.json: {e}", exc_info=True)
            all_patterns = {}

        all_patterns[pattern['name']] = pattern

        with open('storage/patterns.json', 'w') as f:
            json.dump(all_patterns, f, indent=2)

    def find_similar(self, interaction: InteractionDict) -> SimilarList:
        """Find workflows similar to current interaction.

        Args:
            interaction: Current interaction to find similar workflows for

        Returns:
            List of similar workflows with similarity scores, top 5
        """
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

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize StepLogger.

        Args:
            llm_client: Optional LLM client
        """
        super().__init__(graph=None, name="StepLogger", llm_client=llm_client)
        self.vibe: str = "meticulous"

class SuccessJudge(BaseAgent):
    """Sub-agent that judges if something succeeded"""

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize SuccessJudge.

        Args:
            llm_client: Optional LLM client
        """
        super().__init__(graph=None, name="SuccessJudge", llm_client=llm_client)
        self.vibe: str = "fair"

    def judge(self, result: Any, expectation: Any) -> bool:
        """Judge if result meets expectation.

        Args:
            result: Actual result to evaluate
            expectation: Expected result

        Returns:
            True if result meets expectation
        """
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

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize TemplateExtractor.

        Args:
            llm_client: Optional LLM client
        """
        super().__init__(graph=None, name="TemplateExtractor", llm_client=llm_client)
        self.vibe: str = "abstract"