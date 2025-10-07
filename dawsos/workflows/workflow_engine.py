# workflows/workflow_engine.py
# Phase 3.1: Comprehensive type hints added
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.typing_compat import TypeAlias

# Type aliases for clarity
WorkflowDict: TypeAlias = Dict[str, Any]
WorkflowList: TypeAlias = List[WorkflowDict]
PatternDict: TypeAlias = Dict[str, Any]
ContextDict: TypeAlias = Dict[str, Any]

class WorkflowRecorder:
    def __init__(self) -> None:
        """Initialize WorkflowRecorder with empty workflows list.

        Loads existing workflows from storage on initialization.
        """
        self.workflows: WorkflowList = []
        self.load_existing()

    def record(self, trigger: str, actions: List[str], results: Dict[str, Any]) -> None:
        """Every successful interaction becomes a reusable workflow.

        Args:
            trigger: The trigger that initiated the workflow
            actions: List of actions performed
            results: Results dictionary from workflow execution
        """
        workflow: WorkflowDict = {
            'id': f"workflow_{datetime.now().timestamp()}",
            'trigger': trigger,
            'actions': actions,
            'results': results,
            'success_rate': 1.0,
            'uses': 1,
            'created': datetime.now().isoformat()
        }
        self.workflows.append(workflow)
        self._identify_pattern(workflow)

    def _identify_pattern(self, workflow: WorkflowDict) -> None:
        """After 3+ similar workflows, create a pattern.

        Args:
            workflow: The workflow to check for pattern matches
        """
        similar: WorkflowList = self._find_similar(workflow)
        if len(similar) >= 3:
            pattern: PatternDict = {
                'name': self._generate_pattern_name(workflow),
                'template': self._extract_template(similar),
                'success_rate': self._calculate_success(similar)
            }
            self.save_pattern(pattern)

    def find_applicable(self, context: ContextDict) -> WorkflowList:
        """Find workflows that might apply to current context.

        Args:
            context: Current execution context dictionary

        Returns:
            List of applicable workflows sorted by success rate
        """
        applicable: WorkflowList = []
        for workflow in self.workflows:
            if self._matches_context(workflow, context):
                applicable.append(workflow)
        return sorted(applicable, key=lambda w: w['success_rate'], reverse=True)