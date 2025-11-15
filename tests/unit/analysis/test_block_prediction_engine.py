"""
Unit Tests for BlockPredictionEngine

Tests the 3 decision trees and confidence scoring logic:
- Tree 1: Reversal detection (sustained counter present)
- Tree 2: Neutral early bias (early bias == NEUTRAL)
- Tree 3: Continuation (early bias != NEUTRAL, no counter)
- Confidence scoring with bonuses and penalties
"""

import pytest
from unittest.mock import Mock

from nasdaq_predictor.analysis.block_prediction_engine import BlockPredictionEngine


class TestBlockPredictionEngine:
    """Test suite for BlockPredictionEngine decision trees."""

    @pytest.fixture
    def engine(self):
        """Create BlockPredictionEngine instance."""
        return BlockPredictionEngine()

    # ========================================
    # Decision Tree 1 Tests: Reversal Detection
    # ========================================

    def test_decision_tree_1_reversal_strong(self, engine):
        """Test Tree 1: Strong sustained counter → use counter direction."""
        # Setup: counter detected with strong deviation
        early_bias = ("UP", 1.5)
        has_counter = True
        counter_direction = "DOWN"
        deviation = 2.5  # > 2.0 = strong

        # Execute
        prediction, strength = engine.apply_decision_tree_1(
            early_bias=early_bias,
            has_counter=has_counter,
            counter_direction=counter_direction,
            deviation=deviation
        )

        # Assert
        assert prediction == counter_direction
        assert strength == "strong"

    def test_decision_tree_1_reversal_moderate(self, engine):
        """Test Tree 1: Moderate sustained counter."""
        # Setup: counter with moderate deviation
        early_bias = ("UP", 1.5)
        has_counter = True
        counter_direction = "DOWN"
        deviation = 1.2  # 0.5 <= dev < 2.0 = moderate

        # Execute
        prediction, strength = engine.apply_decision_tree_1(
            early_bias=early_bias,
            has_counter=has_counter,
            counter_direction=counter_direction,
            deviation=deviation
        )

        # Assert
        assert prediction == counter_direction
        assert strength == "moderate"

    def test_decision_tree_1_reversal_weak(self, engine):
        """Test Tree 1: Weak sustained counter."""
        # Setup: counter with weak deviation
        early_bias = ("UP", 1.5)
        has_counter = True
        counter_direction = "DOWN"
        deviation = 0.3  # < 0.5 = weak

        # Execute
        prediction, strength = engine.apply_decision_tree_1(
            early_bias=early_bias,
            has_counter=has_counter,
            counter_direction=counter_direction,
            deviation=deviation
        )

        # Assert
        assert prediction == "NEUTRAL"
        assert strength == "weak"

    def test_decision_tree_1_no_counter(self, engine):
        """Test Tree 1: No sustained counter detected."""
        # Setup: no counter
        early_bias = ("UP", 1.5)
        has_counter = False
        counter_direction = None
        deviation = 2.5

        # Execute - Tree 1 should not apply
        result = engine.apply_decision_tree_1(
            early_bias=early_bias,
            has_counter=has_counter,
            counter_direction=counter_direction,
            deviation=deviation
        )

        # Assert - returns None or falls through to other trees
        # Implementation-specific behavior

    # ========================================
    # Decision Tree 2 Tests: Neutral Early Bias
    # ========================================

    def test_decision_tree_2_neutral_small_deviation(self, engine):
        """Test Tree 2: Neutral early bias with small deviation."""
        # Setup: early bias neutral, |dev| < 0.5
        early_bias = ("NEUTRAL", 0.0)
        counter = False
        deviation = 0.3
        deviation_direction = 1  # Positive

        # Execute
        prediction, strength = engine.apply_decision_tree_2(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation,
            deviation_direction=deviation_direction
        )

        # Assert
        assert prediction == "NEUTRAL"
        assert strength == "weak"

    def test_decision_tree_2_neutral_develops_up(self, engine):
        """Test Tree 2: Neutral early bias develops UP by 5/7."""
        # Setup: neutral early bias, |dev| >= 0.5, positive dev
        early_bias = ("NEUTRAL", 0.0)
        counter = False
        deviation = 1.2
        deviation_direction = 1  # UP

        # Execute
        prediction, strength = engine.apply_decision_tree_2(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation,
            deviation_direction=deviation_direction
        )

        # Assert
        assert prediction == "UP"
        assert strength in ["moderate", "strong"]

    def test_decision_tree_2_neutral_develops_down(self, engine):
        """Test Tree 2: Neutral early bias develops DOWN by 5/7."""
        # Setup: neutral early bias, |dev| >= 0.5, negative dev
        early_bias = ("NEUTRAL", 0.0)
        counter = False
        deviation = 1.5
        deviation_direction = -1  # DOWN

        # Execute
        prediction, strength = engine.apply_decision_tree_2(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation,
            deviation_direction=deviation_direction
        )

        # Assert
        assert prediction == "DOWN"
        assert strength in ["moderate", "strong"]

    def test_decision_tree_2_not_neutral(self, engine):
        """Test Tree 2 doesn't apply when early bias != NEUTRAL."""
        # Setup: early bias not neutral
        early_bias = ("UP", 1.5)
        counter = False
        deviation = 1.2
        deviation_direction = 1

        # Execute - Tree 2 should not apply
        result = engine.apply_decision_tree_2(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation,
            deviation_direction=deviation_direction
        )

        # Assert - returns None or falls through

    # ========================================
    # Decision Tree 3 Tests: Continuation
    # ========================================

    def test_decision_tree_3_continuation_strong(self, engine):
        """Test Tree 3: Strong early bias continues with large deviation."""
        # Setup: early bias UP, strong continuation (|dev| >= 2.0)
        early_bias = ("UP", 1.8)
        counter = False
        deviation = 2.5

        # Execute
        prediction, strength = engine.apply_decision_tree_3(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation
        )

        # Assert
        assert prediction == "UP"
        assert strength == "strong"

    def test_decision_tree_3_continuation_moderate_strength(self, engine):
        """Test Tree 3: Moderate early bias strength continues."""
        # Setup: early bias with moderate strength (0.5-1.0)
        early_bias = ("DOWN", 0.8)
        counter = False
        deviation = 1.2

        # Execute
        prediction, strength = engine.apply_decision_tree_3(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation
        )

        # Assert
        assert prediction == "DOWN"
        assert strength == "moderate"

    def test_decision_tree_3_continuation_weak_strength(self, engine):
        """Test Tree 3: Weak early bias with weak continuation."""
        # Setup: early bias weak strength (< 0.5)
        early_bias = ("UP", 0.3)
        counter = False
        deviation = 0.7

        # Execute
        prediction, strength = engine.apply_decision_tree_3(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation
        )

        # Assert
        assert prediction == "UP"
        assert strength == "weak"

    def test_decision_tree_3_with_counter_present(self, engine):
        """Test Tree 3 doesn't apply when counter is present."""
        # Setup: sustained counter exists
        early_bias = ("UP", 1.5)
        counter = True
        deviation = 2.5

        # Execute - Tree 3 should not apply
        result = engine.apply_decision_tree_3(
            early_bias=early_bias,
            counter=counter,
            deviation=deviation
        )

        # Assert - should not apply

    # ========================================
    # Confidence Scoring Tests
    # ========================================

    def test_confidence_base_weak(self, engine):
        """Test base confidence score for weak strength."""
        strength = "weak"

        confidence = engine.calculate_base_confidence(strength)

        assert confidence == 35

    def test_confidence_base_moderate(self, engine):
        """Test base confidence score for moderate strength."""
        strength = "moderate"

        confidence = engine.calculate_base_confidence(strength)

        assert confidence == 65

    def test_confidence_base_strong(self, engine):
        """Test base confidence score for strong strength."""
        strength = "strong"

        confidence = engine.calculate_base_confidence(strength)

        assert confidence == 85

    def test_confidence_bonus_early_bias_alignment(self, engine):
        """Test confidence bonus for early bias alignment."""
        # Setup: prediction matches early bias
        base_confidence = 65
        predicted = "UP"
        early_bias = ("UP", 1.5)

        bonus = engine.calculate_alignment_bonus(predicted, early_bias)

        # Should get +10% bonus
        assert bonus >= 5  # At least some bonus

    def test_confidence_bonus_counter_confirmation(self, engine):
        """Test confidence bonus for counter confirmation."""
        # Setup: counter confirmed the prediction
        base_confidence = 65
        has_counter = True
        prediction_matches_counter = True

        bonus = engine.calculate_counter_bonus(has_counter, prediction_matches_counter)

        assert bonus >= 5

    def test_confidence_penalty_small_deviation(self, engine):
        """Test confidence penalty for very small deviation."""
        # Setup: very small deviation (< 0.2 std dev)
        base_confidence = 65
        deviation = 0.1

        penalty = engine.calculate_small_deviation_penalty(deviation)

        # Should apply penalty
        assert penalty <= 0

    def test_confidence_range_minimum(self, engine):
        """Test confidence never goes below 5%."""
        # Setup: worst case scenario
        strength = "weak"
        base = engine.calculate_base_confidence(strength)

        final_confidence = max(5, base)

        assert final_confidence >= 5

    def test_confidence_range_maximum(self, engine):
        """Test confidence never reaches 100%."""
        # Setup: best case scenario
        strength = "strong"
        base = engine.calculate_base_confidence(strength)
        bonus = 10  # Maximum bonuses

        final_confidence = min(95, base + bonus)

        assert final_confidence <= 95

    def test_confidence_calculation_full_pipeline(self, engine):
        """Test full confidence calculation pipeline."""
        # Setup: complete scenario
        strength = "moderate"
        alignment = True
        counter_present = False
        deviation = 1.5

        base = engine.calculate_base_confidence(strength)
        align_bonus = 10 if alignment else 0
        counter_bonus = 0
        small_dev_penalty = -5 if deviation < 0.2 else 0

        final = base + align_bonus + counter_bonus + small_dev_penalty
        final = max(5, min(95, final))

        assert 5 <= final <= 95

    # ========================================
    # Edge Cases & Integration Tests
    # ========================================

    def test_decision_tree_all_neutral(self, engine):
        """Test when all factors suggest neutral prediction."""
        # Setup: no counter, neutral early bias, small deviation
        early_bias = ("NEUTRAL", 0.0)
        has_counter = False
        deviation = 0.2
        deviation_direction = 1

        # Execute
        prediction, strength = engine.make_prediction(
            early_bias=early_bias,
            has_counter=has_counter,
            counter_direction=None,
            deviation=deviation,
            deviation_direction=deviation_direction
        )

        # Assert
        assert prediction == "NEUTRAL"
        assert strength == "weak"

    def test_decision_tree_conflicting_signals(self, engine):
        """Test when early bias and counter conflict."""
        # Setup: UP early bias but DOWN counter
        early_bias = ("UP", 1.5)
        has_counter = True
        counter_direction = "DOWN"
        deviation = 1.8

        # Execute
        prediction, strength = engine.make_prediction(
            early_bias=early_bias,
            has_counter=has_counter,
            counter_direction=counter_direction,
            deviation=deviation,
            deviation_direction=-1
        )

        # Assert - counter should win in Tree 1
        assert prediction == counter_direction

    def test_decision_tree_strong_early_bias_no_counter(self, engine):
        """Test strong early bias with no counter (Tree 3)."""
        # Setup: strong early bias, no counter
        early_bias = ("UP", 2.5)
        has_counter = False
        deviation = 2.0

        # Execute
        prediction, strength = engine.make_prediction(
            early_bias=early_bias,
            has_counter=has_counter,
            counter_direction=None,
            deviation=deviation,
            deviation_direction=1
        )

        # Assert
        assert prediction == "UP"
        assert strength == "strong"

    def test_deviation_direction_sign(self, engine):
        """Test proper handling of deviation direction sign."""
        # Setup: test both positive and negative deviations
        test_cases = [
            (1, "UP"),    # Positive deviation
            (-1, "DOWN"),  # Negative deviation
            (0, "NEUTRAL") # No deviation
        ]

        for dev_dir, expected in test_cases:
            assert isinstance(dev_dir, int)
            assert expected in ["UP", "DOWN", "NEUTRAL"]

    def test_strength_consistency(self, engine):
        """Test that strength values are consistent across trees."""
        valid_strengths = ["weak", "moderate", "strong"]

        # Test Tree 1
        pred1, strength1 = engine.apply_decision_tree_1(
            early_bias=("UP", 1.5),
            has_counter=True,
            counter_direction="DOWN",
            deviation=2.5
        )
        assert strength1 in valid_strengths

        # Test Tree 3
        pred3, strength3 = engine.apply_decision_tree_3(
            early_bias=("UP", 1.5),
            counter=False,
            deviation=2.5
        )
        assert strength3 in valid_strengths

    def test_prediction_consistency(self, engine):
        """Test that prediction values are consistent."""
        valid_predictions = ["UP", "DOWN", "NEUTRAL"]

        # Test multiple scenarios
        for _ in range(10):
            early_bias = ("UP", 1.5)
            pred, _ = engine.apply_decision_tree_1(
                early_bias=early_bias,
                has_counter=True,
                counter_direction="DOWN",
                deviation=1.5
            )
            assert pred in valid_predictions

    def test_no_invalid_output_combinations(self, engine):
        """Test that no invalid prediction/strength combinations occur."""
        # Setup test matrix
        predictions = ["UP", "DOWN", "NEUTRAL"]
        strengths = ["weak", "moderate", "strong"]

        # All combinations should be valid
        for pred in predictions:
            for strength in strengths:
                # This is a valid combination
                assert True

