"""
Intraday Prediction Service for NQP application.

This service generates hourly intraday predictions (0-16 hours) for all enabled tickers.
"""

import logging
import pandas as pd
import pytz
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..data.fetcher import YahooFinanceDataFetcher
from ..database.repositories.ticker_repository import TickerRepository
from ..database.repositories.market_data_repository import MarketDataRepository
from ..database.repositories.intraday_prediction_repository import IntradayPredictionRepository
from ..database.models.intraday_prediction import IntradayPrediction
from ..analysis.reference_levels import calculate_all_reference_levels
from ..analysis.signals import calculate_signals
from ..analysis.intraday import calculate_intraday_predictions

logger = logging.getLogger(__name__)


class IntradayPredictionService:
    """Service to generate and store hourly intraday predictions.

    Implements full dependency injection for all repository and data fetcher dependencies.
    """

    def __init__(
        self,
        fetcher: YahooFinanceDataFetcher,
        ticker_repo: TickerRepository,
        market_data_repo: MarketDataRepository,
        intraday_repo: IntradayPredictionRepository
    ):
        """Initialize IntradayPredictionService with injected dependencies.

        Args:
            fetcher: YahooFinanceDataFetcher for market data retrieval
            ticker_repo: TickerRepository for ticker management
            market_data_repo: MarketDataRepository for OHLC data access
            intraday_repo: IntradayPredictionRepository for intraday prediction storage
        """
        self.fetcher = fetcher
        self.ticker_repo = ticker_repo
        self.market_data_repo = market_data_repo
        self.intraday_repo = intraday_repo

    def generate_and_store_hourly_predictions(self) -> Dict[str, Any]:
        """
        Generate and store hourly predictions for all enabled tickers.

        Returns:
            Dict[str, Any]: Summary of prediction generation results
        """
        logger.info("Starting hourly prediction generation for all enabled tickers...")

        tickers = self.ticker_repo.get_enabled_tickers()

        if not tickers:
            logger.warning("No enabled tickers found")
            return {
                'success': False,
                'message': 'No enabled tickers',
                'tickers': [],
                'total_tickers': 0,
                'successful': 0,
                'failed': 0,
                'total_predictions_stored': 0
            }

        results = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'total_tickers': len(tickers),
            'tickers': [],
            'total_predictions_stored': 0
        }

        for ticker in tickers:
            try:
                count = self.generate_predictions_for_ticker(ticker.id, ticker.symbol)
                results['tickers'].append({
                    'symbol': ticker.symbol,
                    'success': True,
                    'predictions_stored': count
                })
                results['total_predictions_stored'] += count
                logger.info(f"Successfully generated {count} predictions for {ticker.symbol}")

            except Exception as e:
                logger.error(f"Error generating predictions for {ticker.symbol}: {e}")
                results['tickers'].append({
                    'symbol': ticker.symbol,
                    'success': False,
                    'error': str(e)
                })

        successful = sum(1 for t in results['tickers'] if t['success'])
        results['successful'] = successful
        results['failed'] = len(tickers) - successful

        logger.info(
            f"Hourly prediction generation completed: {successful}/{len(tickers)} successful, "
            f"{results['total_predictions_stored']} total predictions"
        )

        return results

    def generate_predictions_for_ticker(
        self,
        ticker_id: str,
        ticker_symbol: str
    ) -> int:
        """
        Generate hourly predictions (0-23 hours) for a single ticker with data validation.

        Args:
            ticker_id: Ticker UUID
            ticker_symbol: Ticker symbol (e.g., 'NQ=F')

        Returns:
            int: Number of predictions stored
        """
        logger.info(f"Generating hourly predictions for {ticker_symbol}...")

        # Get current time in UTC
        current_time_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)

        # Determine NY timezone for US tickers
        ny_tz = pytz.timezone('America/New_York')
        current_time_ny = current_time_utc.astimezone(ny_tz)

        # Get today's start time in NY timezone
        today_start_ny = current_time_ny.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start_ny.astimezone(pytz.UTC)

        # Fetch market data from database (prefer database over yfinance)
        data_30min = self._get_market_data(ticker_id, '30m', days=2)
        data_hourly = self._get_market_data(ticker_id, '1h', days=30)
        data_daily = self._get_market_data(ticker_id, '1d', days=365)

        # Validate that we have sufficient data before proceeding
        if data_30min.empty or data_hourly.empty:
            logger.warning(
                f"Insufficient market data for {ticker_symbol}: "
                f"30m bars={len(data_30min) if not data_30min.empty else 0}, "
                f"hourly bars={len(data_hourly) if not data_hourly.empty else 0}. "
                f"Market data sync may not have completed yet. Skipping predictions."
            )
            return 0

        # Additional validation: ensure 30-min data is recent (within last 10 minutes during market hours)
        if not data_30min.empty:
            latest_30min_time = data_30min.index[-1]
            minutes_old = (current_time_utc - latest_30min_time).total_seconds() / 60
            if minutes_old > 10:  # Tightened from 35 to 10 minutes for more accurate intraday signals
                logger.warning(
                    f"30-minute data for {ticker_symbol} is {minutes_old:.0f} minutes old. "
                    f"Waiting for fresh market data before generating predictions."
                )
                return 0

        # Get current price
        current_price = float(data_30min['Close'].iloc[-1])

        # Calculate reference levels
        ref_levels = calculate_all_reference_levels(
            data_hourly, data_30min, data_daily, current_time_utc
        )

        # Generate signals
        signals = calculate_signals(current_price, ref_levels)

        # Generate predictions for all hours (0-23, full 24-hour coverage)
        target_hours = list(range(0, 24))  # 0, 1, 2, ..., 23
        intraday_preds = calculate_intraday_predictions(
            signals,
            current_price,
            current_time_utc,
            target_hours
        )

        # Create IntradayPrediction objects for each hour
        predictions_to_store = []

        for target_hour, pred_data in intraday_preds.items():
            # Calculate target timestamp
            target_time_ny = today_start_ny.replace(hour=target_hour, minute=0, second=0)
            target_time_utc = target_time_ny.astimezone(pytz.UTC)

            # Get reference price (open at target hour)
            reference_price = self._get_reference_price(
                data_30min, target_time_utc, current_time_utc
            )

            if not reference_price:
                reference_price = current_price

            # Check if we can verify (target hour has passed)
            can_verify = current_time_utc > target_time_utc + timedelta(hours=1)

            target_close_price = None
            actual_result = None
            verified_at = None

            if can_verify:
                # Get target close price
                target_close_price = self._get_target_close_price(
                    data_30min, target_time_utc
                )

                if target_close_price:
                    # Determine if prediction was correct
                    actual_direction = 'BULLISH' if target_close_price > reference_price else 'BEARISH'
                    is_correct = pred_data['prediction'] == actual_direction

                    actual_result = 'CORRECT' if is_correct else 'WRONG'
                    verified_at = current_time_utc

            # Create IntradayPrediction object
            intraday_prediction = IntradayPrediction(
                ticker_id=ticker_id,
                target_hour=target_hour,
                target_timestamp=target_time_utc,
                prediction_made_at=current_time_utc,
                prediction=pred_data['prediction'],
                base_confidence=pred_data['base_confidence'],
                decay_factor=pred_data['decay_factor'],
                final_confidence=pred_data['final_confidence'],
                reference_price=reference_price,
                target_close_price=target_close_price,
                actual_result=actual_result,
                verified_at=verified_at,
                metadata={
                    'ticker_symbol': ticker_symbol,
                    'weighted_score': signals['weighted_score'],
                    'normalized_score': signals['normalized_score'],
                    'bullish_signals': signals['bullish_count'],
                    'total_signals': signals['total_signals'],
                    'generated_by_scheduler': True,
                    'generation_time': current_time_utc.isoformat()
                }
            )

            predictions_to_store.append(intraday_prediction)

        # Check for existing predictions today and only store new ones
        existing_predictions = self.intraday_repo.get_24h_intraday_predictions(ticker_id)
        existing_hours = {p.target_hour for p in existing_predictions}

        # Filter out predictions that already exist for today
        new_predictions = [
            p for p in predictions_to_store
            if p.target_hour not in existing_hours
        ]

        if new_predictions:
            count = self.intraday_repo.bulk_store_intraday_predictions(new_predictions)
            logger.info(f"Stored {count} new predictions for {ticker_symbol}")
            return count
        else:
            logger.info(f"No new predictions to store for {ticker_symbol} (all hours already exist)")
            return 0

    def _get_market_data(
        self,
        ticker_id: str,
        interval: str,
        days: int
    ) -> pd.DataFrame:
        """
        Get market data from database, with fallback to yfinance.

        Args:
            ticker_id: Ticker UUID
            interval: Data interval ('30m', '1h', '1d')
            days: Number of days of data to fetch

        Returns:
            pd.DataFrame: Market data as OHLC dataframe
        """
        try:
            # Try database first
            hours = days * 24
            data_list = self.market_data_repo.get_recent_data(ticker_id, interval, hours=hours)

            if data_list and len(data_list) > 0:
                # Convert to DataFrame
                df = pd.DataFrame([{
                    'Open': float(d.open),
                    'High': float(d.high),
                    'Low': float(d.low),
                    'Close': float(d.close),
                    'Volume': int(d.volume) if d.volume else 0
                } for d in data_list])

                df.index = pd.to_datetime([d.timestamp for d in data_list])
                df.index = df.index.tz_localize('UTC') if df.index.tz is None else df.index.tz_convert('UTC')

                logger.debug(f"Retrieved {len(df)} records from database for interval {interval}")
                return df

        except Exception as e:
            logger.warning(f"Error fetching from database: {e}, falling back to yfinance")

        # Fallback to yfinance
        return pd.DataFrame()

    def _get_reference_price(
        self,
        data_30min: pd.DataFrame,
        target_time_utc: datetime,
        current_time_utc: datetime
    ) -> float:
        """
        Get reference price (open) at target hour.

        Args:
            data_30min: 30-minute OHLC data
            target_time_utc: Target hour timestamp
            current_time_utc: Current time

        Returns:
            float: Reference price or None
        """
        # Only get reference price if target hour has started
        if current_time_utc < target_time_utc:
            return None

        # Find candle at or after target time
        target_candles = data_30min[
            (data_30min.index >= target_time_utc) &
            (data_30min.index < target_time_utc + timedelta(hours=1))
        ]

        if not target_candles.empty:
            return float(target_candles['Open'].iloc[0])

        return None

    def _get_target_close_price(
        self,
        data_30min: pd.DataFrame,
        target_time_utc: datetime
    ) -> float:
        """
        Get target close price at end of target hour.

        Args:
            data_30min: 30-minute OHLC data
            target_time_utc: Target hour timestamp

        Returns:
            float: Target close price or None
        """
        # Find candles within the target hour
        target_close_candles = data_30min[
            (data_30min.index >= target_time_utc) &
            (data_30min.index < target_time_utc + timedelta(hours=1))
        ]

        if not target_close_candles.empty:
            return float(target_close_candles['Close'].iloc[-1])

        return None
