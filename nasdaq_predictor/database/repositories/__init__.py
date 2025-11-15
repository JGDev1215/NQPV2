"""
Database repositories for NQP application.

This package contains repository classes that provide CRUD operations
for each database model.

Repositories:
    - TickerRepository: Ticker CRUD operations
    - MarketDataRepository: Market data CRUD operations
    - PredictionRepository: Prediction and signal CRUD operations
    - ReferenceLevelsRepository: Reference levels CRUD operations

Usage:
    from nasdaq_predictor.database.repositories import TickerRepository

    ticker_repo = TickerRepository()
    tickers = ticker_repo.get_enabled_tickers()
"""

from .ticker_repository import TickerRepository
from .market_data_repository import MarketDataRepository
from .prediction_repository import PredictionRepository
from .reference_levels_repository import ReferenceLevelsRepository

__all__ = [
    'TickerRepository',
    'MarketDataRepository',
    'PredictionRepository',
    'ReferenceLevelsRepository',
]
