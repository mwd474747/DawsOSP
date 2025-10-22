#!/usr/bin/env python3
"""
Evaluate Action - Evaluate business criteria and moats

Evaluates business criteria like brand strength, network effects, cost advantages,
and switching costs. Returns scores based on checklist completion.

Priority: 📊 Analysis - Business evaluation and scoring
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class EvaluateAction(ActionHandler):
    """
    Evaluate criteria and calculate scores.

    Supports multiple evaluation types:
    - brand_moat: Brand strength indicators
    - network_effects: Network effect strength
    - cost_advantages: Cost leadership analysis
    - switching_costs: Customer switching barriers

    Pattern Example:
        {
            "action": "evaluate",
            "type": "brand_moat",
            "checks": ["premium_pricing_ability", "customer_loyalty", "mind_share_leadership"]
        }
    """

    @property
    def action_name(self) -> str:
        return "evaluate"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Evaluate criteria and calculate score.

        Args:
            params: Must contain 'type' and 'checks' (list of criteria)
            context: Current execution context
            outputs: Previous step outputs

        Returns:
            Evaluation result with score, type, and checks passed
        """
        eval_type = params.get('type', '')
        checks = params.get('checks', [])

        if not eval_type:
            self.logger.warning("evaluate action requires 'type' parameter")
            return {
                'score': 0,
                'type': 'unknown',
                'checks_passed': 0,
                'total_checks': 0,
                'error': 'Evaluation type required'
            }

        # Calculate score based on checks and context
        score = 7  # Base score
        checks_passed = 0

        # Evaluation logic based on type
        if eval_type == 'brand_moat':
            score, checks_passed = self._evaluate_brand_moat(checks)
        elif eval_type == 'network_effects':
            score, checks_passed = self._evaluate_network_effects(checks)
        elif eval_type == 'cost_advantages':
            score, checks_passed = self._evaluate_cost_advantages(checks)
        elif eval_type == 'switching_costs':
            score, checks_passed = self._evaluate_switching_costs(checks)
        else:
            self.logger.warning(f"Unknown evaluation type: {eval_type}")

        # Cap score at 10
        score = min(10, score)

        self.logger.info(
            f"Evaluated {eval_type}: score={score:.1f}, "
            f"checks_passed={checks_passed}/{len(checks)}"
        )

        return {
            'score': score,
            'type': eval_type,
            'checks_passed': checks_passed,
            'total_checks': len(checks)
        }

    def _evaluate_brand_moat(self, checks: list) -> tuple:
        """Evaluate brand strength indicators."""
        score = 7
        checks_passed = 0

        # Check for brand strength indicators
        if 'premium_pricing_ability' in checks:
            score += 1
            checks_passed += 1
        if 'customer_loyalty' in checks:
            score += 0.5
            checks_passed += 1
        if 'mind_share_leadership' in checks:
            score += 1.5
            checks_passed += 1

        return score, checks_passed

    def _evaluate_network_effects(self, checks: list) -> tuple:
        """Evaluate network effect strength."""
        score = 7
        checks_passed = 0

        if 'value_increases_with_users' in checks:
            score += 2
            checks_passed += 1
        if 'high_switching_costs' in checks:
            score += 1
            checks_passed += 1
        if 'winner_take_all_dynamics' in checks:
            score += 1
            checks_passed += 1

        return score, checks_passed

    def _evaluate_cost_advantages(self, checks: list) -> tuple:
        """Evaluate cost leadership."""
        score = 7
        checks_passed = 0

        if 'lowest_cost_producer' in checks:
            score += 1.5
            checks_passed += 1
        if 'economies_of_scale' in checks:
            score += 1
            checks_passed += 1
        if 'unique_assets' in checks:
            score += 1.5
            checks_passed += 1

        return score, checks_passed

    def _evaluate_switching_costs(self, checks: list) -> tuple:
        """Evaluate customer switching barriers."""
        score = 7
        checks_passed = 0

        if 'painful_to_switch' in checks:
            score += 2
            checks_passed += 1
        if 'embedded_in_operations' in checks:
            score += 1
            checks_passed += 1
        if 'long_term_contracts' in checks:
            score += 1
            checks_passed += 1

        return score, checks_passed
