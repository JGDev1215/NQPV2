"""
Pytest configuration and comprehensive fixtures for all tests.

Provides:
- Flask app and test client fixtures
- Sample data fixtures (OHLC bars, tickers, etc.)
- Mock service fixtures (yfinance, Supabase, etc.)
- Database fixtures
- Market status fixtures

Usage:
    pytest tests/ -v
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
import pytz
from unittest.mock import Mock, MagicMock, patch
from flask import Flask

# Suppress warnings during testing
import warnings
warnings.filterwarnings('ignore')


# ========================================
# APP AND CLIENT FIXTURES
# ========================================

@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['FLASK_ENV'] = 'testing'

    # Initialize DI container
    try:
        from nasdaq_predictor.container import create_container
        app.container = create_container()
    except Exception:
        app.container = None

    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create app context for testing."""
    with app.app_context():
        yield app


# ========================================
# LEGACY FIXTURES (for backward compatibility)
# ========================================

@pytest.fixture
def sample_ohlc_data():
    """Sample OHLC data for testing (hourly)"""
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


# ========================================
# ENHANCED FIXTURES
# ========================================

@pytest.fixture
def sample_ohlc_bar():
    """Sample valid OHLC bar as dictionary"""
    return {
        'open': 100.0,
        'high': 105.0,
        'low': 99.0,
        'close': 103.0,
        'volume': 1000000,
        'timestamp': datetime.now(pytz.UTC).isoformat()
    }


@pytest.fixture
def sample_ohlc_bars_24h():
    """24 hours of OHLC data (hourly bars)"""
    bars = []
    base_time = datetime.now(pytz.UTC).replace(hour=13, minute=30)
    price = 100.0

    for i in range(24):
        bar_time = base_time + timedelta(hours=i)
        bars.append({
            'open': price,
            'high': price * 1.02,
            'low': price * 0.98,
            'close': price * 1.01,
            'volume': 1000000 + i * 10000,
            'timestamp': bar_time.isoformat()
        })
        price = price * 1.01

    return bars


@pytest.fixture
def supported_tickers():
    """List of supported tickers"""
    return ['NQ=F', 'ES=F', '^FTSE']


@pytest.fixture
def sample_request_data():
    """Sample request data for testing"""
    return {
        'ticker': 'NQ=F',
        'interval': '1h',
        'limit': 100,
        'offset': 0
    }


@pytest.fixture
def sample_success_response():
    """Sample successful API response"""
    return {
        'success': True,
        'status': 'success',
        'data': {'result': 'value'},
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
    }


@pytest.fixture
def sample_error_response():
    """Sample error API response"""
    return {
        'success': False,
        'status': 'error',
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': 'Validation failed',
            'details': {'field': 'Invalid value'}
        },
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
    }


@pytest.fixture
def create_ohlc_bar():
    """Factory for creating OHLC bars with custom values"""
    def _create(
        open_price=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000000,
        hours_ago=0,
        ticker='NQ=F'
    ):
        base_time = datetime.now(pytz.UTC)
        bar_time = base_time - timedelta(hours=hours_ago)

        return {
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'timestamp': bar_time.isoformat(),
            'ticker': ticker
        }

    return _create


# ========================================
# PYTEST CONFIGURATION
# ========================================

def pytest_configure(config):
    """Configure pytest markers and plugins"""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "requires_market: tests needing market data")
    config.addinivalue_line("markers", "requires_db: tests needing database")
