"""
Data processing utilities for filtering and transforming market data
"""
import pandas as pd
from typing import Dict
from ..utils.market_status import is_within_trading_session


def filter_trading_session_data(hist: pd.DataFrame, ticker_symbol: str, trading_sessions: Dict) -> pd.DataFrame:
    """
    Filter historical data to only include trading session hours

    Args:
        hist: Historical OHLC dataframe from yfinance
        ticker_symbol: Ticker symbol
        trading_sessions: Trading session configuration dict

    Returns:
        Filtered dataframe
    """
    if hist.empty:
        return hist

    # Apply trading session filter
    mask = hist.index.map(lambda x: is_within_trading_session(x, ticker_symbol, trading_sessions))
    filtered_hist = hist[mask]

    return filtered_hist
