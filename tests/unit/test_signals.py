"""
Unit tests for signal calculations
"""
import pytest
from nasdaq_predictor.models.market_data import ReferenceLevels
from nasdaq_predictor.analysis.signals import calculate_signals


def test_calculate_signals_bullish():
    """Test signal calculation with bullish scenario"""
    current_price = 110.0
    reference_levels = ReferenceLevels(
        daily_open=100.0,
        hourly_open=105.0,
        four_hourly_open=102.0,
        prev_day_high=108.0,
        prev_day_low=98.0,
        prev_week_open=100.0,
        thirty_min_open=107.0,
        weekly_open=101.0,
        monthly_open=99.0
    )

    result = calculate_signals(current_price, reference_levels)

    # All signals should be bullish (1) since current price > all reference levels
    assert result['prediction'] == 'BULLISH'
    assert result['bullish_count'] == 9
    assert result['total_signals'] == 9
    assert result['weighted_score'] == 1.0
    assert result['confidence'] == 100.0


def test_calculate_signals_bearish():
    """Test signal calculation with bearish scenario"""
    current_price = 95.0
    reference_levels = ReferenceLevels(
        daily_open=100.0,
        hourly_open=105.0,
        four_hourly_open=102.0,
        prev_day_high=108.0,
        prev_day_low=98.0,
        prev_week_open=100.0,
        thirty_min_open=107.0,
        weekly_open=101.0,
        monthly_open=99.0
    )

    result = calculate_signals(current_price, reference_levels)

    # Most signals should be bearish (0) since current price < most reference levels
    assert result['prediction'] == 'BEARISH'
    assert result['bullish_count'] == 0
    assert result['total_signals'] == 9
    assert result['weighted_score'] == 0.0
    assert result['confidence'] == 100.0


def test_calculate_signals_mixed():
    """Test signal calculation with mixed signals"""
    current_price = 103.0
    reference_levels = ReferenceLevels(
        daily_open=100.0,  # Bullish
        hourly_open=105.0,  # Bearish
        four_hourly_open=102.0,  # Bullish
        prev_day_high=108.0,  # Bearish
        prev_day_low=98.0,  # Bullish
        prev_week_open=104.0,  # Bearish
        thirty_min_open=102.5,  # Bullish
        weekly_open=101.0,  # Bullish
        monthly_open=99.0  # Bullish
    )

    result = calculate_signals(current_price, reference_levels)

    # Should have mixed signals
    assert result['total_signals'] == 9
    assert 0 < result['bullish_count'] < 9
    assert 0 < result['weighted_score'] < 1.0
    assert result['prediction'] in ['BULLISH', 'BEARISH']


def test_calculate_signals_with_none_values():
    """Test signal calculation with some None reference levels"""
    current_price = 105.0
    reference_levels = ReferenceLevels(
        daily_open=100.0,
        hourly_open=None,  # Missing data
        four_hourly_open=102.0,
        prev_day_high=None,  # Missing data
        prev_day_low=98.0,
        prev_week_open=100.0,
        thirty_min_open=103.0,
        weekly_open=101.0,
        monthly_open=99.0
    )

    result = calculate_signals(current_price, reference_levels)

    # Should handle None values gracefully
    assert result['total_signals'] == 7  # Only 7 valid signals
    assert result['signals']['hourly_open']['status'] == 'N/A'
    assert result['signals']['prev_day_high']['status'] == 'N/A'
