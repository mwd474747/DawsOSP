#!/usr/bin/env python3
"""
Synthesize Action - Synthesize multiple scores into moat rating

Synthesizes multiple evaluation scores to produce overall moat assessment
including rating, durability, width, trend, and investment action.

Priority: 📊 Analysis - Final synthesis and investment recommendation
"""

from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class SynthesizeAction(ActionHandler):
    """
    Synthesize multiple scores into overall moat rating.

    Takes references to previous evaluation scores and calculates:
    - Average score
    - Moat rating (Wide/Narrow/No Moat)
    - Durability estimate
    - Moat width
    - Trend direction
    - Investment action recommendation

    Pattern Example:
        {
            "action": "synthesize",
            "scores": ["{brand_score}", "{network_score}", "{cost_score}"]
        }
    """

    @property
    def action_name(self) -> str:
        return "synthesize"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Synthesize multiple scores into moat rating.

        Args:
            params: Must contain 'scores' (list of score references like "{score_name}")
            context: Current execution context
            outputs: Previous step outputs (contains referenced scores)

        Returns:
            Synthesis result with moat rating, durability, and investment action
        """
        scores = params.get('scores', [])

        # Extract numeric scores from references
        numeric_scores = []
        for score_ref in scores:
            # Check if this is a reference to a previous output
            if isinstance(score_ref, str) and score_ref.startswith('{') and score_ref.endswith('}'):
                var_name = score_ref.strip('{}')
                if var_name in outputs:
                    score_data = outputs[var_name]
                    # Extract numeric value from various formats
                    if isinstance(score_data, dict) and 'score' in score_data:
                        numeric_scores.append(score_data['score'])
                    elif isinstance(score_data, dict) and 'value' in score_data:
                        numeric_scores.append(score_data['value'])
                    elif isinstance(score_data, (int, float)):
                        numeric_scores.append(score_data)

        # Calculate average score
        avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 7

        # Determine moat rating based on average
        if avg_score >= 8:
            rating = "Wide Moat"
            durability = "20+ years"
            width = "Very Wide"
            trend = "Strengthening"
            action_text = "Strong Buy - Hold Forever"
        elif avg_score >= 6:
            rating = "Narrow Moat"
            durability = "10-20 years"
            width = "Moderate"
            trend = "Stable"
            action_text = "Buy at Fair Price"
        else:
            rating = "No Moat"
            durability = "< 10 years"
            width = "Minimal"
            trend = "Weakening"
            action_text = "Avoid Unless Deep Discount"

        self.logger.info(
            f"Synthesized {len(numeric_scores)} scores: "
            f"avg={avg_score:.1f}, rating={rating}"
        )

        return {
            'moat_rating': rating,
            'moat_durability': durability,
            'moat_width': width,
            'moat_trend': trend,
            'investment_action': action_text,
            'overall_score': avg_score,
            'scores_synthesized': len(numeric_scores)
        }
