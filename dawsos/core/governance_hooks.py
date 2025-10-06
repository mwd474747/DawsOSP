#!/usr/bin/env python3
"""
Governance Hooks - Creative integration patterns to make agents governance-aware
Automatically improves graph effectiveness and outcome tracking
"""

import logging
from typing import Dict, Any, Callable
from datetime import datetime
import functools

logger = logging.getLogger(__name__)


class GovernanceHooks:
    """Hooks that agents can use to become governance-aware"""

    def __init__(self, graph_governance):
        self.graph_governance = graph_governance
        self.graph = graph_governance.graph if graph_governance else None

    def before_action(self, agent_name: str, action: str, target: Any) -> Dict[str, Any]:
        """Check governance before any agent action"""
        if not self.graph_governance:
            return {'allowed': True}

        # Check if target node exists and has governance policies
        if isinstance(target, str) and self.graph._graph.has_node(target):
            governance_check = self.graph_governance.check_governance(target)

            # Block action if quality too low
            if governance_check['quality_score'] < 0.3:
                return {
                    'allowed': False,
                    'reason': f"Quality score too low: {governance_check['quality_score']:.0%}",
                    'suggestion': 'Improve data quality before proceeding'
                }

            # Warn if quality is marginal
            if governance_check['quality_score'] < 0.7:
                return {
                    'allowed': True,
                    'warning': f"Quality score marginal: {governance_check['quality_score']:.0%}",
                    'policies': governance_check.get('policies', [])
                }

        return {'allowed': True}

    def after_action(self, agent_name: str, action: str, target: Any, result: Any) -> None:
        """Track governance impact after agent actions"""
        if not self.graph or not isinstance(target, str):
            return

        # Record the action as a governance event
        event_id = f"gov_event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.graph.add_node('governance_event', {
            'agent': agent_name,
            'action': action,
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'result_quality': self._assess_result_quality(result)
        }, node_id=event_id)

        # Connect event to target
        if self.graph._graph.has_node(target):
            self.graph.connect(event_id, target, 'affected', strength=0.8)

        # Update node quality based on action success
        self._update_node_quality(target, action, result)

    def _assess_result_quality(self, result: Any) -> float:
        """Assess the quality of an action result"""
        if isinstance(result, dict):
            # Check for success indicators
            if result.get('status') == 'success':
                return 0.9
            elif result.get('status') == 'completed':
                return 0.8
            elif result.get('error'):
                return 0.2
            elif result.get('data'):
                # Data present indicates some success
                return 0.7

        return 0.5  # Default neutral quality

    def _update_node_quality(self, node_id: str, action: str, result: Any):
        """Update node quality based on action outcomes"""
        if not self.graph._graph.has_node(node_id):
            return

        # Get current quality history (safe read via get_node)
        node = self.graph.get_node(node_id)
        quality_history = node.get('data', {}).get('quality_history', [])

        # Add new quality entry
        quality_score = self._assess_result_quality(result)
        quality_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'quality': quality_score
        })

        # Keep only last 10 quality assessments
        quality_history = quality_history[-10:]

        # Update via new method (persists to NetworkX)
        self.graph.update_node_data(node_id, {
            'quality_history': quality_history
        })

    def quality_gate(self, min_quality: float = 0.7):
        """Decorator for agent methods that require quality gates"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(self_agent, *args, **kwargs):
                # Check if first argument is a node ID
                if args and isinstance(args[0], str):
                    target = args[0]
                    if self.graph_governance:
                        gov_check = self.graph_governance.check_governance(target)
                        if gov_check['quality_score'] < min_quality:
                            return {
                                'error': 'Quality gate failed',
                                'quality_score': gov_check['quality_score'],
                                'required_quality': min_quality,
                                'governance_status': gov_check.get('governance_status')
                            }

                # Proceed with original function
                result = func(self_agent, *args, **kwargs)

                # Track the outcome
                if args and isinstance(args[0], str):
                    self.after_action(
                        self_agent.__class__.__name__,
                        func.__name__,
                        args[0],
                        result
                    )

                return result

            return wrapper
        return decorator

    def lineage_tracker(self, func: Callable) -> Callable:
        """Decorator that automatically tracks data lineage"""
        @functools.wraps(func)
        def wrapper(self_agent, *args, **kwargs):
            # Track inputs
            input_nodes = []
            for arg in args:
                if isinstance(arg, str) and self.graph._graph.has_node(arg):
                    input_nodes.append(arg)

            # Execute function
            result = func(self_agent, *args, **kwargs)

            # Track outputs and create lineage
            if isinstance(result, dict) and 'output_node' in result:
                output_node = result['output_node']

                # Create lineage connections
                for input_node in input_nodes:
                    self.graph.connect(
                        input_node,
                        output_node,
                        'flows_to',
                        strength=0.9,
                        metadata={
                            'agent': self_agent.__class__.__name__,
                            'method': func.__name__,
                            'timestamp': datetime.now().isoformat()
                        }
                    )

            return result

        return wrapper

    def outcome_tracker(self, prediction_node: str, actual_outcome: Any) -> Dict[str, Any]:
        """Track prediction outcomes to improve graph effectiveness"""
        if not self.graph._graph.has_node(prediction_node):
            return {'error': 'Prediction node not found'}

        # Get current outcomes (safe read via get_node)
        node = self.graph.get_node(prediction_node)
        outcomes = node.get('data', {}).get('outcomes', [])
        predicted_value = node.get('data', {}).get('value')

        # Calculate accuracy
        accuracy = self._calculate_accuracy(predicted_value, actual_outcome)

        # Add new outcome
        outcomes.append({
            'predicted': predicted_value,
            'actual': actual_outcome,
            'timestamp': datetime.now().isoformat(),
            'accuracy': accuracy
        })

        # Keep only last 10 outcomes
        outcomes = outcomes[-10:]

        # Update via new method (persists to NetworkX)
        self.graph.update_node_data(prediction_node, {
            'outcomes': outcomes
        })

        # Calculate rolling accuracy
        accuracies = [o['accuracy'] for o in outcomes]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0

        # Update relationships based on accuracy
        self._adjust_relationship_strengths(prediction_node, avg_accuracy)

        return {
            'outcome_recorded': True,
            'accuracy': accuracy,
            'rolling_accuracy': avg_accuracy,
            'improvements_made': avg_accuracy > 0.7
        }

    def _calculate_accuracy(self, predicted: Any, actual: Any) -> float:
        """Calculate prediction accuracy"""
        try:
            if isinstance(predicted, (int, float)) and isinstance(actual, (int, float)):
                # For numeric predictions, use relative error
                if actual != 0:
                    error = abs(predicted - actual) / abs(actual)
                    return max(0, 1 - error)
                return 1.0 if predicted == actual else 0.0

            # For categorical predictions
            return 1.0 if predicted == actual else 0.0

        except (KeyError, TypeError) as e:
            logger.warning(f"Accuracy calculation failed: {e}")
            return 0.5  # Default neutral accuracy
        except Exception as e:
            logger.error(f"Unexpected error in accuracy calculation: {e}", exc_info=True)
            return 0.5

    def _adjust_relationship_strengths(self, node_id: str, accuracy: float):
        """Adjust relationship strengths based on prediction accuracy"""
        # Strengthen relationships that led to accurate predictions
        for u, v, attrs in self.graph._graph.edges(data=True):
            if v == node_id:
                if accuracy > 0.8:
                    # Strengthen good relationships
                    new_strength = min(1.0, attrs.get('strength', 0.5) * 1.1)
                    self.graph._graph.edges[u, v]['strength'] = new_strength
                elif accuracy < 0.4:
                    # Weaken poor relationships
                    new_strength = max(0.1, attrs.get('strength', 0.5) * 0.9)
                    self.graph._graph.edges[u, v]['strength'] = new_strength

    def governance_score(self, node_id: str) -> float:
        """Get overall governance score for a node"""
        if not self.graph_governance:
            return 0.5

        gov_check = self.graph_governance.check_governance(node_id)
        quality = gov_check.get('quality_score', 0.5)

        # Factor in outcome accuracy if available
        if self.graph._graph.has_node(node_id):
            # Safe read via get_node
            node = self.graph.get_node(node_id)
            outcomes = node.get('data', {}).get('outcomes', [])
            if outcomes:
                accuracies = [o['accuracy'] for o in outcomes[-5:]]
                avg_accuracy = sum(accuracies) / len(accuracies)
                # Weighted average of quality and accuracy
                return (quality * 0.6 + avg_accuracy * 0.4)

        return quality


def integrate_governance_hooks(agent_class):
    """Class decorator to automatically add governance hooks to an agent"""

    original_init = agent_class.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        # Add governance hooks if graph is available
        if hasattr(self, 'graph') and self.graph:
            try:
                from core.graph_governance import GraphGovernance
                graph_gov = GraphGovernance(self.graph)
                self.governance_hooks = GovernanceHooks(graph_gov)

                # Auto-wrap key methods
                if hasattr(self, 'process_request'):
                    original_process = self.process_request

                    def wrapped_process(request, context=None):
                        # Pre-check
                        gov_check = self.governance_hooks.before_action(
                            self.__class__.__name__,
                            'process_request',
                            request
                        )

                        if not gov_check.get('allowed', True):
                            return {
                                'error': 'Governance check failed',
                                'reason': gov_check.get('reason'),
                                'suggestion': gov_check.get('suggestion')
                            }

                        # Execute
                        result = original_process(request, context)

                        # Post-track
                        self.governance_hooks.after_action(
                            self.__class__.__name__,
                            'process_request',
                            request,
                            result
                        )

                        return result

                    self.process_request = wrapped_process

            except ImportError:
                pass  # Governance not available

    agent_class.__init__ = new_init
    return agent_class