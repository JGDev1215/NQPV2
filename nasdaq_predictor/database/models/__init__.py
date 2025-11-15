"""
Database models for NQP application.

This package contains dataclass models that mirror the database schema
and provide type-safe data structures for database operations.

Models:
    - Ticker: Ticker symbols and metadata
    - MarketData: OHLC price data
    - ReferenceLevels: Calculated reference price levels
    - Prediction: Prediction results
    - Signal: Individual signal breakdowns
    - IntradayPrediction: Hourly intraday predictions
    - SessionRange: ICT killzone session ranges

Usage:
    from nasdaq_predictor.database.models import Ticker, MarketData, Prediction

    ticker = Ticker(symbol='NQ=F', name='NASDAQ-100 Futures', type='futures')
"""

from .ticker import Ticker
from .market_data import MarketData, MarketDataInterval
from .prediction import Prediction, PredictionResult
from .signal import Signal, SignalStatus
from .reference_levels import ReferenceLevels
from .intraday_prediction import IntradayPrediction
from .session_range import SessionRange, SessionName, VolatilityLevel

__all__ = [
    'Ticker',
    'MarketData',
    'MarketDataInterval',
    'Prediction',
    'PredictionResult',
    'Signal',
    'SignalStatus',
    'ReferenceLevels',
    'IntradayPrediction',
    'SessionRange',
    'SessionName',
    'VolatilityLevel',
]
