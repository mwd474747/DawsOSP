#!/usr/bin/env python3
"""
Test Dynamic Confidence Calculator - Validate that hardcoded confidence values are replaced
with meaningful dynamic calculations based on real data factors.
"""

import unittest
from core.confidence_calculator import confidence_calculator


class TestConfidenceCalculator(unittest.TestCase):
    """Test the dynamic confidence calculation system"""

    def test_basic_confidence_calculation(self):
        """Test basic confidence calculation with known inputs"""
        result = confidence_calculator.calculate_confidence(
            data_quality=0.9,
            model_accuracy=0.8,
            historical_success_rate=0.7,
            num_data_points=100,
            correlation_strength=0.85
        )

        self.assertIsInstance(result, dict)
        self.assertIn('confidence', result)
        self.assertIn('confidence_level', result)
        self.assertTrue(0 <= result['confidence'] <= 1)
        self.assertIn(result['confidence_level'], ['Very Low', 'Low', 'Moderate', 'High'])

    def test_dcf_confidence_calculation(self):
        """Test DCF-specific confidence calculation"""
        financial_data = {
            'free_cash_flow': 1000,
            'net_income': 800,
            'revenue': 5000,
            'ebit': 1200,
            'debt': 2000,
            'equity': 3000
        }
        projections = [1000, 1100, 1200, 1300, 1400]
        discount_rate = 0.10

        result = confidence_calculator.calculate_dcf_confidence(
            financial_data=financial_data,
            projections=projections,
            discount_rate=discount_rate
        )

        self.assertIsInstance(result, dict)
        self.assertIn('confidence', result)
        self.assertTrue(0 <= result['confidence'] <= 1)

    def test_analysis_type_adjustments(self):
        """Test that different analysis types produce different confidence levels"""
        base_params = {
            'data_quality': 0.8,
            'model_accuracy': 0.7,
            'num_data_points': 50
        }

        dcf_result = confidence_calculator.calculate_confidence(
            analysis_type='dcf',
            **base_params
        )

        technical_result = confidence_calculator.calculate_confidence(
            analysis_type='technical',
            **base_params
        )

        fundamental_result = confidence_calculator.calculate_confidence(
            analysis_type='fundamental',
            **base_params
        )

        # Fundamental should be more confident than technical
        self.assertGreater(fundamental_result['confidence'], technical_result['confidence'])

    def test_data_quality_impact(self):
        """Test that data quality significantly impacts confidence"""
        high_quality = confidence_calculator.calculate_confidence(
            data_quality=0.95,
            analysis_type='general'
        )

        low_quality = confidence_calculator.calculate_confidence(
            data_quality=0.3,
            analysis_type='general'
        )

        # High quality data should result in higher confidence
        self.assertGreater(high_quality['confidence'], low_quality['confidence'])

    def test_data_points_impact(self):
        """Test that more data points increase confidence"""
        few_points = confidence_calculator.calculate_confidence(
            num_data_points=5,
            analysis_type='general'
        )

        many_points = confidence_calculator.calculate_confidence(
            num_data_points=1000,
            analysis_type='general'
        )

        # More data points should result in higher confidence
        self.assertGreater(many_points['confidence'], few_points['confidence'])

    def test_confidence_level_mapping(self):
        """Test confidence level categorical mapping"""
        # Test high confidence
        high_conf = confidence_calculator._get_confidence_level(0.85)
        self.assertEqual(high_conf, "High")

        # Test moderate confidence
        mod_conf = confidence_calculator._get_confidence_level(0.65)
        self.assertEqual(mod_conf, "Moderate")

        # Test low confidence (adjusted based on actual implementation)
        low_conf = confidence_calculator._get_confidence_level(0.45)
        self.assertEqual(low_conf, "Low")

        # Test very low confidence
        very_low_conf = confidence_calculator._get_confidence_level(0.35)
        self.assertEqual(very_low_conf, "Very Low")

    def test_bounds_enforcement(self):
        """Test that confidence is always bounded between 0 and 1"""
        # Test with extreme values that might push confidence out of bounds
        result = confidence_calculator.calculate_confidence(
            data_quality=2.0,  # Extreme high value
            model_accuracy=-0.5,  # Negative value
            correlation_strength=1.5,  # Out of bounds
            analysis_type='general'
        )

        self.assertTrue(0 <= result['confidence'] <= 1)

    def test_missing_parameters_handling(self):
        """Test that missing parameters are handled gracefully"""
        # Test with minimal parameters
        result = confidence_calculator.calculate_confidence(
            analysis_type='general'
        )

        self.assertIsInstance(result, dict)
        self.assertIn('confidence', result)
        self.assertTrue(0 <= result['confidence'] <= 1)

    def test_financial_data_quality_assessment(self):
        """Test financial data quality assessment"""
        # Complete financial data
        complete_data = {
            'free_cash_flow': 1000,
            'net_income': 800,
            'revenue': 5000,
            'ebit': 1200
        }

        incomplete_data = {
            'revenue': 5000
        }

        complete_quality = confidence_calculator._assess_financial_data_quality(complete_data)
        incomplete_quality = confidence_calculator._assess_financial_data_quality(incomplete_data)

        self.assertGreater(complete_quality, incomplete_quality)

    def test_projection_reliability_assessment(self):
        """Test cash flow projection reliability assessment"""
        # Reasonable projections
        reasonable_projections = [1000, 1050, 1100, 1150, 1200]

        # Extreme projections
        extreme_projections = [1000, 2000, 4000, 8000, 16000]

        reasonable_reliability = confidence_calculator._assess_projection_reliability(reasonable_projections)
        extreme_reliability = confidence_calculator._assess_projection_reliability(extreme_projections)

        self.assertGreater(reasonable_reliability, extreme_reliability)

    def test_discount_rate_reliability(self):
        """Test discount rate reliability assessment"""
        # Reasonable discount rate
        reasonable_rate = 0.10  # 10%

        # Extreme discount rate
        extreme_rate = 0.50  # 50%

        reasonable_reliability = confidence_calculator._assess_discount_rate_reliability(reasonable_rate)
        extreme_reliability = confidence_calculator._assess_discount_rate_reliability(extreme_rate)

        self.assertGreater(reasonable_reliability, extreme_reliability)


class TestDynamicConfidenceIntegration(unittest.TestCase):
    """Test integration with existing system components"""

    def test_replaces_hardcoded_confidence_85_percent(self):
        """Test that we can dynamically calculate what was previously hardcoded as 85%"""
        # Simulate the conditions that would warrant 85% confidence
        result = confidence_calculator.calculate_confidence(
            data_quality=0.92,  # High quality data
            model_accuracy=0.88,  # Good model accuracy
            historical_success_rate=0.76,  # Reasonable success rate
            num_data_points=100,  # Sufficient data points
            analysis_type='dcf'
        )

        # Should be in the high confidence range (around 0.8-0.9)
        self.assertGreaterEqual(result['confidence'], 0.75)
        self.assertLessEqual(result['confidence'], 0.95)

    def test_replaces_hardcoded_confidence_75_percent(self):
        """Test that we can dynamically calculate what was previously hardcoded as 75%"""
        # Simulate moderate confidence conditions
        result = confidence_calculator.calculate_confidence(
            data_quality=0.7,  # Moderate quality
            model_accuracy=0.7,  # Moderate accuracy
            historical_success_rate=0.65,  # Moderate success rate
            num_data_points=30,  # Moderate data points
            analysis_type='general'
        )

        # Should be in the moderate confidence range
        self.assertGreaterEqual(result['confidence'], 0.6)
        self.assertLessEqual(result['confidence'], 0.85)

    def test_low_confidence_scenarios(self):
        """Test scenarios that should produce low confidence"""
        result = confidence_calculator.calculate_confidence(
            data_quality=0.3,  # Poor quality
            model_accuracy=0.4,  # Poor accuracy
            num_data_points=3,  # Very few data points
            analysis_type='sentiment'  # Less reliable analysis type
        )

        # Should produce low confidence
        self.assertLessEqual(result['confidence'], 0.5)


def run_confidence_tests():
    """Run all confidence calculator tests"""
    print("🧪 Testing Dynamic Confidence Calculator...")

    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestConfidenceCalculator))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDynamicConfidenceIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    if result.wasSuccessful():
        print("✅ All confidence calculator tests passed!")
        print(f"📊 Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed:")
        print(f"🔍 Failures: {len(result.failures)}")
        print(f"💥 Errors: {len(result.errors)}")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_confidence_tests()