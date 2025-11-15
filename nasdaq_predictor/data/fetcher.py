"""
Data fetching layer for retrieving market data from Supabase and yfinance

Includes data quality validation to prevent corrupt OHLC data from being stored.
"""
import logging
import yfinance as yf
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from ..config.settings import (
    HIST_PERIOD_HOURLY,
    HIST_PERIOD_MINUTE,
    HIST_PERIOD_5MIN,
    HIST_PERIOD_15MIN,
    HIST_PERIOD_30MIN,
    HIST_INTERVAL_HOURLY,
    HIST_INTERVAL_MINUTE,
    HIST_INTERVAL_5MIN,
    HIST_INTERVAL_15MIN,
    HIST_INTERVAL_30MIN,
    TRADING_SESSIONS
)
from .processor import filter_trading_session_data
from ..utils.timezone import ensure_utc
from ..core.data_quality_validator import OHLCValidator

logger = logging.getLogger(__name__)


class YahooFinanceDataFetcher:
    """Fetches market data from Supabase (primary) and Yahoo Finance (fallback)"""

    def __init__(self, market_data_repo=None):
        self.trading_sessions = TRADING_SESSIONS
        self.market_data_repo = market_data_repo
        self.validators = {}  # Cache validators by ticker symbol

    def _get_validator(self, ticker_symbol: str) -> OHLCValidator:
        """Get or create a validator instance for a ticker"""
        if ticker_symbol not in self.validators:
            self.validators[ticker_symbol] = OHLCValidator(ticker_symbol)
        return self.validators[ticker_symbol]

    def _validate_ohlc_bars(self, df: pd.DataFrame, ticker_symbol: str) -> Tuple[pd.DataFrame, dict]:
        """
        Validate OHLC bars in a DataFrame and return cleaned data + validation stats

        Args:
            df: DataFrame with OHLC data (index=timestamp, columns=Open,High,Low,Close,Volume)
            ticker_symbol: Ticker symbol for logging and validation

        Returns:
            Tuple of (cleaned_dataframe, validation_stats_dict)
            - Cleaned DataFrame with only valid bars
            - Stats dict with validation results
        """
        if df.empty:
            return df, {'valid': 0, 'invalid': 0, 'removed_indices': []}

        validator = self._get_validator(ticker_symbol)
        valid_rows = []
        invalid_count = 0
        removed_indices = []

        # Validate each bar
        for timestamp, row in df.iterrows():
            bar = {
                'open': row.get('Open'),
                'high': row.get('High'),
                'low': row.get('Low'),
                'close': row.get('Close'),
                'volume': row.get('Volume', 0)
            }
            is_valid, errors = validator.validate_bar(bar)

            if is_valid:
                valid_rows.append(timestamp)
            else:
                invalid_count += 1
                removed_indices.append(str(timestamp))
                logger.warning(f"Invalid OHLC bar for {ticker_symbol} at {timestamp}: {errors}")

        # Create cleaned DataFrame with only valid bars
        cleaned_df = df.loc[valid_rows] if valid_rows else pd.DataFrame()

        stats = {
            'valid': len(valid_rows),
            'invalid': invalid_count,
            'removed_indices': removed_indices
        }

        if invalid_count > 0:
            logger.info(f"Validation for {ticker_symbol}: {len(valid_rows)} valid, {invalid_count} invalid bars removed")

        return cleaned_df, stats

    def fetch_ticker_data(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch all required data for a ticker symbol

        Args:
            ticker_symbol: Ticker symbol to fetch

        Returns:
            Dictionary containing:
                - hourly_hist: Hourly OHLC data (filtered to trading hours)
                - minute_hist: Minute OHLC data (filtered to trading hours)
                - five_min_hist: 5-minute OHLC data (filtered to trading hours)
                - fifteen_min_hist: 15-minute OHLC data (filtered to trading hours)
                - thirty_min_hist: 30-minute OHLC data (filtered to trading hours)
                - daily_hist: Daily OHLC data (filtered to trading days)
                - current_price: Most recent close price
                - current_time: Most recent timestamp
            Returns None if fetch fails
        """
        try:
            ticker = yf.Ticker(ticker_symbol)

            # Fetch hourly data
            hourly_hist = ticker.history(period=HIST_PERIOD_HOURLY, interval=HIST_INTERVAL_HOURLY)
            if hourly_hist.empty:
                logger.warning(f"No hourly data available for {ticker_symbol}")
                return None

            # Filter to only trading session hours
            hourly_hist = filter_trading_session_data(hourly_hist, ticker_symbol, self.trading_sessions)
            if hourly_hist.empty:
                logger.warning(f"No hourly data in trading session for {ticker_symbol}")
                return None

            # Validate hourly data quality
            hourly_hist, hourly_stats = self._validate_ohlc_bars(hourly_hist, f"{ticker_symbol}:1h")
            if hourly_hist.empty:
                logger.warning(f"No valid hourly data for {ticker_symbol} after quality validation")
                return None

            # Fetch 1-minute data for small timeframe calculations
            minute_hist = ticker.history(period=HIST_PERIOD_MINUTE, interval=HIST_INTERVAL_MINUTE)
            # Filter 1-minute data to trading session hours
            minute_hist = filter_trading_session_data(minute_hist, ticker_symbol, self.trading_sessions)
            # Validate 1-minute data quality
            minute_hist, minute_stats = self._validate_ohlc_bars(minute_hist, f"{ticker_symbol}:1m")

            # Fetch 5-minute data for block analysis and intraday predictions
            five_min_hist = ticker.history(period=HIST_PERIOD_5MIN, interval=HIST_INTERVAL_5MIN)
            # Filter 5-minute data to trading session hours
            five_min_hist = filter_trading_session_data(five_min_hist, ticker_symbol, self.trading_sessions)
            # Validate 5-minute data quality
            five_min_hist, five_min_stats = self._validate_ohlc_bars(five_min_hist, f"{ticker_symbol}:5m")

            # Fetch 15-minute data for mid-timeframe analysis
            fifteen_min_hist = ticker.history(period=HIST_PERIOD_15MIN, interval=HIST_INTERVAL_15MIN)
            # Filter 15-minute data to trading session hours
            fifteen_min_hist = filter_trading_session_data(fifteen_min_hist, ticker_symbol, self.trading_sessions)
            # Validate 15-minute data quality
            fifteen_min_hist, fifteen_min_stats = self._validate_ohlc_bars(fifteen_min_hist, f"{ticker_symbol}:15m")

            # Fetch 30-minute data for intraday predictions
            thirty_min_hist = ticker.history(period=HIST_PERIOD_30MIN, interval=HIST_INTERVAL_30MIN)
            # Filter 30-minute data to trading session hours
            thirty_min_hist = filter_trading_session_data(thirty_min_hist, ticker_symbol, self.trading_sessions)
            # Validate 30-minute data quality
            thirty_min_hist, thirty_min_stats = self._validate_ohlc_bars(thirty_min_hist, f"{ticker_symbol}:30m")

            # Get daily data for previous day high/low
            daily_hist = ticker.history(period='7d', interval='1d')
            # Filter daily data to trading session days
            daily_hist = filter_trading_session_data(daily_hist, ticker_symbol, self.trading_sessions)
            # Validate daily data quality
            daily_hist, daily_stats = self._validate_ohlc_bars(daily_hist, f"{ticker_symbol}:1d")

            # Get current price and time
            current_price = hourly_hist['Close'].iloc[-1]
            current_time = hourly_hist.index[-1]

            # Ensure UTC timezone
            current_time = ensure_utc(current_time)

            return {
                'hourly_hist': hourly_hist,
                'minute_hist': minute_hist,
                'five_min_hist': five_min_hist,
                'fifteen_min_hist': fifteen_min_hist,
                'thirty_min_hist': thirty_min_hist,
                'daily_hist': daily_hist,
                'current_price': current_price,
                'current_time': current_time
            }

        except Exception as e:
            logger.error(f"Error fetching data for {ticker_symbol}: {str(e)}", exc_info=True)
            return None

    def fetch_intraday_data(self, ticker_symbol: str, period: str = '2d', interval: str = '5m') -> Optional[pd.DataFrame]:
        """
        Fetch intraday data for session range calculations

        Args:
            ticker_symbol: Ticker symbol
            period: Data period (default '2d')
            interval: Data interval (default '5m')

        Returns:
            DataFrame with intraday OHLC data (validated), or None if fetch fails
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                logger.warning(f"No intraday data available for {ticker_symbol}")
                return None

            # Validate intraday data quality
            hist, validation_stats = self._validate_ohlc_bars(hist, f"{ticker_symbol}:intraday:{interval}")

            if hist.empty:
                logger.warning(f"No valid intraday data for {ticker_symbol} after quality validation")
                return None

            return hist

        except Exception as e:
            logger.error(f"Error fetching intraday data for {ticker_symbol}: {str(e)}", exc_info=True)
            return None

    def fetch_historical_data(
        self,
        ticker_id: str,
        ticker_symbol: str,
        start: datetime,
        end: datetime,
        interval: str = '5m'
    ) -> list:
        """
        Fetch historical OHLC data for a specific time range from Supabase (primary) or yfinance (fallback).

        Used by block prediction service to get intra-hour bars for block segmentation.

        Args:
            ticker_id: Asset ticker UUID (for Supabase queries)
            ticker_symbol: Asset ticker symbol (e.g., "NQ=F", "ES=F", "^FTSE") for yfinance fallback
            start: Start datetime (UTC)
            end: End datetime (UTC)
            interval: Bar interval ('5m', '1m', '15m', '30m', etc., default '5m')

        Returns:
            List of OHLC bar dictionaries with keys: timestamp, open, high, low, close, volume
            Returns empty list if no data available
        """
        bars = []

        # Try Supabase first (primary data source) - uses UUID
        if self.market_data_repo:
            try:
                logger.debug(f"Fetching {ticker_symbol} (UUID: {ticker_id}) from Supabase for {start} to {end}")
                market_data_list = self.market_data_repo.get_historical_data(
                    ticker_id=ticker_id,  # Use UUID for Supabase query
                    start=start,
                    end=end,
                    interval=interval
                )

                if market_data_list:
                    # Validate bars before adding to result
                    validator = self._get_validator(ticker_symbol)
                    valid_count = 0
                    invalid_count = 0

                    for md in market_data_list:
                        bar = {
                            'open': md.open,
                            'high': md.high,
                            'low': md.low,
                            'close': md.close,
                            'volume': md.volume or 0
                        }
                        is_valid, errors = validator.validate_bar(bar)

                        if is_valid:
                            bars.append({
                                'timestamp': md.timestamp,
                                'open': md.open,
                                'high': md.high,
                                'low': md.low,
                                'close': md.close,
                                'volume': md.volume or 0
                            })
                            valid_count += 1
                        else:
                            invalid_count += 1
                            logger.warning(f"Invalid OHLC bar for {ticker_symbol} from Supabase at {md.timestamp}: {errors}")

                    if invalid_count > 0:
                        logger.info(f"Supabase validation for {ticker_symbol}: {valid_count} valid, {invalid_count} invalid bars skipped")

                    if bars:
                        logger.debug(f"Fetched {len(bars)} validated bars for {ticker_symbol} from Supabase ({interval} interval)")
                        return bars
                else:
                    logger.debug(f"No Supabase data for {ticker_symbol} (UUID: {ticker_id}), falling back to yfinance")
            except Exception as e:
                logger.warning(f"Error fetching from Supabase for {ticker_symbol} (UUID: {ticker_id}): {e}, falling back to yfinance")

        # Fall back to yfinance if Supabase not available or returns no data
        # Uses ticker_symbol for yfinance API
        try:
            logger.debug(f"Fetching {ticker_symbol} from yfinance for {start} to {end}")
            ticker_obj = yf.Ticker(ticker_symbol)

            # Fetch data with start/end parameters
            # Note: yfinance expects start/end as strings in format YYYY-MM-DD HH:MM:SS or datetime objects
            hist = ticker_obj.history(start=start, end=end, interval=interval)

            if hist.empty:
                logger.debug(f"No data available for {ticker_symbol} between {start} and {end}")
                return []

            # Validate OHLC data quality before converting to dictionaries
            hist_validated, validation_stats = self._validate_ohlc_bars(hist, f"{ticker_symbol}:yfinance:{interval}")

            if hist_validated.empty:
                logger.warning(f"No valid yfinance data for {ticker_symbol} between {start} and {end} after quality validation")
                return []

            # Convert DataFrame to list of dictionaries
            for timestamp, row in hist_validated.iterrows():
                bar = {
                    'timestamp': timestamp,
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']) if 'Volume' in row else 0
                }
                bars.append(bar)

            logger.debug(f"Fetched {len(bars)} validated bars for {ticker_symbol} from yfinance ({interval} interval)")
            return bars

        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker_symbol}: {str(e)}", exc_info=True)
            return []
