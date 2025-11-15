"""
Database package for NQP (NASDAQ Predictor) application.

This package provides database connectivity, models, and repositories
for persistent storage using Supabase (PostgreSQL).

Modules:
    - supabase_client: Connection manager and client singleton
    - models: Data models (Ticker, MarketData, Prediction, Signal)
    - repositories: CRUD operations for each model
    - migrations: SQL migration scripts

Usage:
    from nasdaq_predictor.database import get_supabase_client
    from nasdaq_predictor.database.repositories import TickerRepository

    client = get_supabase_client()
    ticker_repo = TickerRepository()
    tickers = ticker_repo.get_enabled_tickers()
"""

from .supabase_client import get_supabase_client, test_connection

__all__ = ['get_supabase_client', 'test_connection']
