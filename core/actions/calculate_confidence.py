#!/usr/bin/env python3
"""
Calculate Confidence Action - Calculate confidence scores for analysis

Calculates confidence scores using the confidence calculator module.
Integrates with financial analyst for symbol-specific calculations.

Priority: 📊 Analysis - Important for quality scoring
"""

from core.confidence_calculator import confidence_calculator
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class CalculateConfidenceAction(ActionHandler):
    """
    Calculate confidence score for analysis.

    Uses the centralized confidence_calculator module to generate
    confidence scores based on data quality, model accuracy, and
    analysis type. Can integrate with financial_analyst for
    symbol-specific confidence calculations.

    Pattern Example:
        {
            "action": "calculate_confidence",
            "symbol": "{SYMBOL}",
            "analysis_type": "dcf",
            "factors": [...]
        }
    """

    @property
    def action_name(self) -> str:
        return "calculate_confidence"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Calculate confidence score for analysis.

        Args:
            params: Must contain 'analysis_type', optional 'symbol', 'factors'
            context: Current execution context (may contain 'symbol')
            outputs: Previous step outputs

        Returns:
            Confidence data with score, level, and metadata
        """
        # Extract parameters
        symbol = self._resolve_param(
            params.get('symbol') or context.get('symbol', 'AAPL'),
            context,
            outputs
        )
        analysis_type = params.get('analysis_type', 'general')
        factors = params.get('factors', [])

        # Try to use financial analyst for symbol-specific confidence
        if symbol and symbol != 'AAPL':
            financial_analyst = self._get_agent('financial_analyst')
            if financial_analyst and hasattr(financial_analyst, '_calculate_confidence'):
                try:
                    # Get confidence from financial analyst
                    confidence_data = financial_analyst._calculate_confidence({}, symbol)

                    # Calculate confidence level dynamically
                    confidence_level = confidence_calculator._get_confidence_level(confidence_data)

                    self.logger.info(
                        f"Calculated confidence for {symbol}: "
                        f"{confidence_data:.2f} ({confidence_level})"
                    )

                    return {
                        'confidence': confidence_data,
                        'confidence_level': confidence_level,
                        'analysis_type': analysis_type,
                        'symbol': symbol,
                        'factors_considered': len(factors),
                        'source': 'financial_analyst'
                    }
                except Exception as e:
                    self.logger.warning(
                        f"Financial analyst confidence calculation failed: {e}, using fallback"
                    )

        # Fallback: use dynamic confidence calculation from confidence_calculator
        confidence_result = confidence_calculator.calculate_confidence(
            analysis_type=analysis_type,
            num_data_points=len(factors),
            data_quality=0.6,  # Default moderate quality
            model_accuracy=0.7  # Default moderate accuracy
        )

        self.logger.info(
            f"Calculated confidence (fallback): "
            f"{confidence_result['confidence']:.2f} ({confidence_result['confidence_level']})"
        )

        return {
            'confidence': confidence_result['confidence'],
            'confidence_level': confidence_result['confidence_level'],
            'analysis_type': analysis_type,
            'symbol': symbol,
            'factors_considered': len(factors),
            'source': 'confidence_calculator'
        }

    def _get_agent(self, agent_name: str):
        """Get agent from runtime if available."""
        if self.runtime and hasattr(self.runtime, 'agents'):
            return self.runtime.agents.get(agent_name)
        return None
