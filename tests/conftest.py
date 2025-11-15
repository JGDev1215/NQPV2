"""
Pytest configuration and fixtures
"""
import pytest
from datetime import datetime
import pandas as pd
import pytz


@pytest.fixture
def sample_ohlc_data():
    """Sample OHLC data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=24, freq='H', tz=pytz.UTC)
    data = {
        'Open': [100 + i for i in range(24)],
        'High': [101 + i for i in range(24)],
        'Low': [99 + i for i in range(24)],
        'Close': [100.5 + i for i in range(24)],
        'Volume': [1000000] * 24
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def sample_daily_data():
    """Sample daily OHLC data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=7, freq='D', tz=pytz.UTC)
    data = {
        'Open': [100, 102, 104, 103, 105, 107, 106],
        'High': [102, 104, 106, 105, 108, 109, 108],
        'Low': [99, 101, 103, 102, 104, 106, 105],
        'Close': [101, 103, 105, 104, 107, 108, 107],
        'Volume': [1000000] * 7
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def current_time():
    """Sample current time for testing"""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
