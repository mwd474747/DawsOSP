#!/usr/bin/env python3
"""
Dynamic Confidence Calculator - Replaces hardcoded confidence scores with real calculations
Based on data quality, model accuracy, historical success rates, and correlation strength
"""

import math
from typing import Dict, Any, List
from datetime import datetime
import numpy as np


class ConfidenceCalculator:
    """Calculates dynamic confidence scores based on multiple factors"""

    def __init__(self):
        self.base_weights = {
            'data_quality': 0.30,
            'model_accuracy': 0.25,
            'historical_success': 0.20,
            'data_points': 0.15,
            'correlation_strength': 0.10
        }

    def calculate_confidence(self,
                           data_quality: float = None,
                           model_accuracy: float = None,
                           historical_success_rate: float = None,
                           num_data_points: int = None,
                           correlation_strength: float = None,
                           analysis_type: str = 'general',
                           **kwargs) -> Dict[str, Any]:
        """
        Calculate dynamic confidence score based on real data factors

        Args:
            data_quality: Quality score of input data (0-1)
            model_accuracy: Historical model accuracy (0-1)
            historical_success_rate: Success rate of similar analyses (0-1)
            num_data_points: Number of data points in analysis
            correlation_strength: Strength of correlations found (0-1)
            analysis_type: Type of analysis (dcf, technical, fundamental, etc.)

        Returns:
            Dict with confidence score and breakdown
        """

        # Calculate individual confidence components
        components = {}

        # Data Quality Component (0-1)
        if data_quality is not None:
            components['data_quality'] = self._normalize_score(data_quality)
        else:
            components['data_quality'] = self._estimate_data_quality(kwargs)

        # Model Accuracy Component (0-1)
        if model_accuracy is not None:
            components['model_accuracy'] = self._normalize_score(model_accuracy)
        else:
            components['model_accuracy'] = self._estimate_model_accuracy(analysis_type)

        # Historical Success Component (0-1)
        if historical_success_rate is not None:
            components['historical_success'] = self._normalize_score(historical_success_rate)
        else:
            components['historical_success'] = self._estimate_historical_success(analysis_type)

        # Data Points Component (0-1)
        if num_data_points is not None:
            components['data_points'] = self._calculate_data_points_confidence(num_data_points)
        else:
            components['data_points'] = self._estimate_data_points(kwargs)

        # Correlation Strength Component (0-1)
        if correlation_strength is not None:
            components['correlation_strength'] = self._normalize_score(abs(correlation_strength))
        else:
            components['correlation_strength'] = self._estimate_correlation_strength(kwargs)

        # Calculate weighted confidence score
        confidence_score = 0.0
        total_weight = 0.0

        for component, score in components.items():
            weight = self.base_weights.get(component, 0.0)
            confidence_score += score * weight
            total_weight += weight

        # Normalize by total weight used
        if total_weight > 0:
            confidence_score = confidence_score / total_weight

        # Apply analysis type adjustments
        confidence_score = self._apply_analysis_type_adjustment(confidence_score, analysis_type)

        # Ensure bounds [0, 1]
        confidence_score = max(0.0, min(1.0, confidence_score))

        return {
            'confidence': confidence_score,
            'confidence_level': self._get_confidence_level(confidence_score),
            'components': components,
            'analysis_type': analysis_type,
            'factors_used': len([k for k, v in components.items() if v > 0])
        }

    def _normalize_score(self, score: float) -> float:
        """Normalize any score to 0-1 range"""
        if score is None:
            return 0.5
        return max(0.0, min(1.0, float(score)))

    def _estimate_data_quality(self, kwargs: Dict[str, Any]) -> float:
        """Estimate data quality from available context"""
        quality_score = 0.5  # Base score

        # Check for data source quality indicators
        source = kwargs.get('data_source', '').lower()
        if any(official in source for official in ['fred', 'sec', 'fmp', 'official']):
            quality_score += 0.3
        elif any(reliable in source for reliable in ['yahoo', 'bloomberg', 'reuters']):
            quality_score += 0.2

        # Check for data freshness
        timestamp = kwargs.get('timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    data_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    data_time = timestamp

                age_hours = (datetime.now() - data_time).total_seconds() / 3600
                if age_hours < 1:
                    quality_score += 0.2
                elif age_hours < 24:
                    quality_score += 0.1
                elif age_hours > 168:  # Week old
                    quality_score -= 0.1
            except:
                pass

        # Check for data completeness
        missing_fields = kwargs.get('missing_fields', 0)
        total_fields = kwargs.get('total_fields', 10)
        if total_fields > 0:
            completeness = 1 - (missing_fields / total_fields)
            quality_score = quality_score * completeness

        return self._normalize_score(quality_score)

    def _estimate_model_accuracy(self, analysis_type: str) -> float:
        """Estimate model accuracy based on analysis type and historical performance"""
        # Historical accuracy rates for different analysis types
        type_accuracies = {
            'dcf': 0.75,  # DCF models have moderate accuracy
            'technical': 0.60,  # Technical analysis is less reliable
            'fundamental': 0.80,  # Fundamental analysis is more reliable
            'sentiment': 0.55,  # Sentiment analysis is volatile
            'correlation': 0.70,  # Correlation analysis is moderately reliable
            'regression': 0.85,  # Statistical models can be quite accurate
            'ml_prediction': 0.65,  # ML predictions vary widely
            'general': 0.70
        }

        return type_accuracies.get(analysis_type, 0.70)

    def _estimate_historical_success(self, analysis_type: str) -> float:
        """Estimate historical success rate for analysis type"""
        # Success rates based on historical performance
        success_rates = {
            'dcf': 0.68,  # DCF has mixed success record
            'technical': 0.55,  # Technical analysis success is debated
            'fundamental': 0.72,  # Fundamental analysis has good track record
            'sentiment': 0.50,  # Sentiment is hit or miss
            'correlation': 0.65,  # Correlation-based predictions are moderate
            'regression': 0.75,  # Statistical models perform well
            'ml_prediction': 0.62,  # ML varies by implementation
            'general': 0.65
        }

        return success_rates.get(analysis_type, 0.65)

    def _calculate_data_points_confidence(self, num_points: int) -> float:
        """Calculate confidence based on number of data points"""
        if num_points < 5:
            return 0.2  # Very low confidence with few points
        elif num_points < 10:
            return 0.4
        elif num_points < 30:
            return 0.6
        elif num_points < 100:
            return 0.8
        else:
            return 0.95  # High confidence with many points

    def _estimate_data_points(self, kwargs: Dict[str, Any]) -> float:
        """Estimate data points from context"""
        # Look for indicators of data volume
        data_count = kwargs.get('data_count', kwargs.get('sample_size', 0))
        if data_count > 0:
            return self._calculate_data_points_confidence(data_count)

        # Estimate based on analysis scope
        if kwargs.get('timeframe') == 'daily':
            return 0.8  # Daily data usually has many points
        elif kwargs.get('timeframe') == 'weekly':
            return 0.6
        elif kwargs.get('timeframe') == 'monthly':
            return 0.4

        return 0.5  # Default moderate confidence

    def _estimate_correlation_strength(self, kwargs: Dict[str, Any]) -> float:
        """Estimate correlation strength from available data"""
        # Look for correlation indicators
        correlations = kwargs.get('correlations', [])
        if correlations:
            if isinstance(correlations, list):
                # Take average of absolute correlations
                abs_corrs = [abs(c) for c in correlations if isinstance(c, (int, float))]
                if abs_corrs:
                    return np.mean(abs_corrs)
            elif isinstance(correlations, (int, float)):
                return abs(correlations)

        # Look for R-squared or similar metrics
        r_squared = kwargs.get('r_squared', kwargs.get('r2'))
        if r_squared is not None:
            return math.sqrt(abs(r_squared))  # Convert R² to correlation

        return 0.5  # Default moderate correlation

    def _apply_analysis_type_adjustment(self, base_score: float, analysis_type: str) -> float:
        """Apply analysis-type specific adjustments"""
        adjustments = {
            'dcf': 0.05,  # DCF gets slight boost for being thorough
            'technical': -0.10,  # Technical analysis gets penalty for subjectivity
            'fundamental': 0.08,  # Fundamental analysis gets boost for rigor
            'sentiment': -0.15,  # Sentiment analysis gets penalty for volatility
            'correlation': 0.0,  # Correlation analysis is neutral
            'regression': 0.10,  # Statistical models get boost
            'ml_prediction': -0.05,  # ML gets slight penalty for black box nature
        }

        adjustment = adjustments.get(analysis_type, 0.0)
        return base_score + adjustment

    def _get_confidence_level(self, score: float) -> str:
        """Convert confidence score to categorical level"""
        if score >= 0.8:
            return "High"
        elif score >= 0.6:
            return "Moderate"
        elif score >= 0.4:
            return "Low"
        else:
            return "Very Low"

    def calculate_dcf_confidence(self,
                               financial_data: Dict[str, Any],
                               projections: List[float],
                               discount_rate: float,
                               **kwargs) -> Dict[str, Any]:
        """Calculate confidence specifically for DCF analysis"""

        # DCF-specific factors
        data_quality = self._assess_financial_data_quality(financial_data)
        projection_confidence = self._assess_projection_reliability(projections)
        discount_rate_confidence = self._assess_discount_rate_reliability(discount_rate)

        # Calculate weighted DCF confidence
        dcf_confidence = (
            data_quality * 0.4 +
            projection_confidence * 0.35 +
            discount_rate_confidence * 0.25
        )

        return self.calculate_confidence(
            data_quality=data_quality,
            model_accuracy=projection_confidence,
            historical_success_rate=self._estimate_historical_success('dcf'),
            num_data_points=len(projections) + len(financial_data),
            analysis_type='dcf',
            **kwargs
        )

    def _assess_financial_data_quality(self, financial_data: Dict[str, Any]) -> float:
        """Assess quality of financial data for DCF"""
        quality = 0.5  # Base quality

        # Check for required fields
        required_fields = ['free_cash_flow', 'revenue', 'net_income', 'debt', 'equity']
        present_fields = sum(1 for field in required_fields if financial_data.get(field) is not None)
        quality += (present_fields / len(required_fields)) * 0.3

        # Check for data consistency
        fcf = financial_data.get('free_cash_flow', 0)
        net_income = financial_data.get('net_income', 0)
        if fcf and net_income and abs(fcf / net_income) < 2:  # Reasonable FCF/NI ratio
            quality += 0.1

        # Check for recent data
        if financial_data.get('quarter') or financial_data.get('fiscal_year'):
            quality += 0.1

        return self._normalize_score(quality)

    def _assess_projection_reliability(self, projections: List[float]) -> float:
        """Assess reliability of cash flow projections"""
        if not projections or len(projections) < 3:
            return 0.3  # Low confidence for insufficient projections

        # Check for reasonable growth patterns
        growth_rates = []
        for i in range(1, len(projections)):
            if projections[i-1] != 0:
                growth = (projections[i] - projections[i-1]) / projections[i-1]
                growth_rates.append(growth)

        if growth_rates:
            # Penalize extreme growth rates
            avg_growth = np.mean(growth_rates)
            if abs(avg_growth) > 0.5:  # >50% average growth is suspicious
                return 0.4
            elif abs(avg_growth) > 0.3:  # >30% average growth is aggressive
                return 0.6
            else:
                return 0.8  # Reasonable growth projections

        return 0.5

    def _assess_discount_rate_reliability(self, discount_rate: float) -> float:
        """Assess reliability of discount rate"""
        # Typical discount rates are 8-15%
        if 0.05 <= discount_rate <= 0.20:  # 5-20% is reasonable range
            if 0.08 <= discount_rate <= 0.15:  # 8-15% is most common
                return 0.9
            else:
                return 0.7
        else:
            return 0.3  # Extreme discount rates are less reliable


# Global instance for easy access
confidence_calculator = ConfidenceCalculator()