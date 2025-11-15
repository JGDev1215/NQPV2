"""
Data Synchronization Service for NQP application.

This service orchestrates the fetching of market data from yfinance,
calculation of predictions, and storage in Supabase.
"""

import logging
import pandas as pd
import pytz
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..data.fetcher import YahooFinanceDataFetcher
from ..database.repositories.ticker_repository import TickerRepository
from ..database.repositories.market_data_repository import MarketDataRepository
from ..database.repositories.prediction_repository import PredictionRepository
from ..database.repositories.reference_levels_repository import ReferenceLevelsRepository
from ..database.models.market_data import MarketData
from ..database.models.reference_levels import ReferenceLevels
from ..database.models.prediction import Prediction
from ..database.models.signal import Signal
from ..analysis import reference_levels, signals
from ..analysis.volatility import calculate_volatility
from ..analysis.reference_levels import get_hourly_movement
from ..utils.market_status import get_market_status
from ..config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class DataSyncService:
    """Service to synchronize market data and predictions.

    Implements full dependency injection for all repository and data fetcher dependencies.
    """

    def __init__(
        self,
        fetcher: YahooFinanceDataFetcher,
        ticker_repo: TickerRepository,
        market_data_repo: MarketDataRepository,
        prediction_repo: PredictionRepository,
        ref_levels_repo: ReferenceLevelsRepository
    ):
        """Initialize DataSyncService with injected dependencies.

        Args:
            fetcher: YahooFinanceDataFetcher for market data retrieval
            ticker_repo: TickerRepository for ticker management
            market_data_repo: MarketDataRepository for OHLC data storage
            prediction_repo: PredictionRepository for prediction storage
            ref_levels_repo: ReferenceLevelsRepository for reference level storage
        """
        self.fetcher = fetcher
        self.ticker_repo = ticker_repo
        self.market_data_repo = market_data_repo
        self.prediction_repo = prediction_repo
        self.ref_levels_repo = ref_levels_repo

    def sync_all_tickers(self) -> Dict[str, Any]:
        """
        Sync market data for all enabled tickers.

        Returns:
            Dict[str, Any]: Summary of sync results
        """
        logger.info("Starting market data sync for all enabled tickers...")

        tickers = self.ticker_repo.get_enabled_tickers()

        if not tickers:
            logger.warning("No enabled tickers found")
            return {'success': False, 'message': 'No enabled tickers', 'tickers': []}

        results = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'total_tickers': len(tickers),
            'tickers': []
        }

        for ticker in tickers:
            try:
                # Use ticker.id (UUID) as primary key for market data
                # and symbol for human-readable reference
                ticker_result = self.sync_ticker_data(ticker.id, ticker.symbol)
                results['tickers'].append({
                    'symbol': ticker.symbol,
                    'success': True,
                    'records_stored': ticker_result.get('records_stored', 0)
                })
                logger.info(f"Successfully synced {ticker.symbol}")

            except Exception as e:
                logger.error(f"Error syncing {ticker.symbol}: {e}")
                results['tickers'].append({
                    'symbol': ticker.symbol,
                    'success': False,
                    'error': str(e)
                })

        successful = sum(1 for t in results['tickers'] if t['success'])
        results['successful'] = successful
        results['failed'] = len(tickers) - successful

        logger.info(
            f"Market data sync completed: {successful}/{len(tickers)} successful"
        )

        return results

    def sync_ticker_data(self, ticker_id: str, symbol: str) -> Dict[str, Any]:
        """
        Sync market data for a specific ticker with retry logic.

        Args:
            ticker_id: Ticker UUID
            symbol: Ticker symbol (e.g., 'NQ=F')

        Returns:
            Dict[str, Any]: Sync results for this ticker
        """
        logger.info(f"Syncing market data for {symbol}...")

        # Fetch data from yfinance with retry logic (optimized for 6-min job gap)
        # Reduced delays to prevent blocking prediction calculation at :08
        max_retries = 3
        retry_delays = [10, 20]  # seconds (30s total, was 420s)

        data = None
        for attempt in range(max_retries):
            try:
                data = self.fetcher.fetch_ticker_data(symbol)
                if data:
                    break

                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        f"No data from yfinance for {symbol}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    import time
                    time.sleep(delay)

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        f"Error fetching data for {symbol}: {e}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    import time
                    time.sleep(delay)
                else:
                    raise Exception(f"Failed to fetch data for {symbol} after {max_retries} attempts: {e}")

        if not data:
            raise Exception(f"No data returned from yfinance for {symbol} after {max_retries} retries")

        # Validate data completeness before storing (all intervals must meet minimum thresholds)
        self._validate_data_completeness(data, symbol)

        # Track fetch time for data freshness metrics
        fetch_time = datetime.utcnow()
        records_stored = 0
        quality_metrics = {
            'symbol': symbol,
            'fetch_time': fetch_time.isoformat(),
            'intervals': {}
        }

        # Store minute data (1m)
        if 'minute_hist' in data and data['minute_hist'] is not None:
            minute_data = self._convert_to_market_data(
                ticker_id, data['minute_hist'], '1m', fetch_time
            )
            count = self.market_data_repo.store_ohlc_data(ticker_id, minute_data)
            records_stored += count
            quality_metrics['intervals']['1m'] = {'records': count, 'age_seconds': 0}
            logger.debug(f"Stored {count} minute records for {symbol}")

        # Store 5-minute data (5m)
        if 'five_min_hist' in data and data['five_min_hist'] is not None:
            five_min_data = self._convert_to_market_data(
                ticker_id, data['five_min_hist'], '5m', fetch_time
            )
            count = self.market_data_repo.store_ohlc_data(ticker_id, five_min_data)
            records_stored += count
            quality_metrics['intervals']['5m'] = {'records': count, 'age_seconds': 0}
            logger.debug(f"Stored {count} 5-minute records for {symbol}")

        # Store 15-minute data (15m)
        if 'fifteen_min_hist' in data and data['fifteen_min_hist'] is not None:
            fifteen_min_data = self._convert_to_market_data(
                ticker_id, data['fifteen_min_hist'], '15m', fetch_time
            )
            count = self.market_data_repo.store_ohlc_data(ticker_id, fifteen_min_data)
            records_stored += count
            quality_metrics['intervals']['15m'] = {'records': count, 'age_seconds': 0}
            logger.debug(f"Stored {count} 15-minute records for {symbol}")

        # Store 30-minute data (30m)
        if 'thirty_min_hist' in data and data['thirty_min_hist'] is not None:
            thirty_min_data = self._convert_to_market_data(
                ticker_id, data['thirty_min_hist'], '30m', fetch_time
            )
            count = self.market_data_repo.store_ohlc_data(ticker_id, thirty_min_data)
            records_stored += count
            quality_metrics['intervals']['30m'] = {'records': count, 'age_seconds': 0}
            logger.debug(f"Stored {count} 30-minute records for {symbol}")

        # Store hourly data (1h)
        if 'hourly_hist' in data and data['hourly_hist'] is not None:
            hourly_data = self._convert_to_market_data(
                ticker_id, data['hourly_hist'], '1h', fetch_time
            )
            count = self.market_data_repo.store_ohlc_data(ticker_id, hourly_data)
            records_stored += count
            quality_metrics['intervals']['1h'] = {'records': count, 'age_seconds': 0}
            logger.debug(f"Stored {count} hourly records for {symbol}")

        # Store daily data (1d)
        if 'daily_hist' in data and data['daily_hist'] is not None:
            daily_data = self._convert_to_market_data(
                ticker_id, data['daily_hist'], '1d', fetch_time
            )
            count = self.market_data_repo.store_ohlc_data(ticker_id, daily_data)
            records_stored += count
            quality_metrics['intervals']['1d'] = {'records': count, 'age_seconds': 0}
            logger.debug(f"Stored {count} daily records for {symbol}")

        # Log quality metrics for data quality tracking
        quality_metrics['total_records'] = records_stored
        logger.info(
            f"Synced {symbol}: {records_stored} total records stored | "
            f"Quality: 1m={quality_metrics['intervals'].get('1m', {}).get('records', 0)}, "
            f"5m={quality_metrics['intervals'].get('5m', {}).get('records', 0)}, "
            f"15m={quality_metrics['intervals'].get('15m', {}).get('records', 0)}, "
            f"30m={quality_metrics['intervals'].get('30m', {}).get('records', 0)}, "
            f"1h={quality_metrics['intervals'].get('1h', {}).get('records', 0)}, "
            f"1d={quality_metrics['intervals'].get('1d', {}).get('records', 0)}"
        )

        return {
            'ticker_id': ticker_id,
            'symbol': symbol,
            'records_stored': records_stored,
            'timestamp': datetime.utcnow().isoformat()
        }

    def calculate_predictions_for_all(self) -> Dict[str, Any]:
        """
        Calculate and store predictions for all enabled tickers.

        Returns:
            Dict[str, Any]: Summary of prediction results
        """
        logger.info("Starting prediction calculation for all enabled tickers...")

        tickers = self.ticker_repo.get_enabled_tickers()

        if not tickers:
            logger.warning("No enabled tickers found")
            return {'success': False, 'message': 'No enabled tickers', 'predictions': []}

        results = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'total_tickers': len(tickers),
            'predictions': []
        }

        for ticker in tickers:
            try:
                prediction = self.calculate_and_store_prediction(ticker.id, ticker.symbol)
                results['predictions'].append({
                    'symbol': ticker.symbol,
                    'success': True,
                    'prediction': prediction.prediction if prediction else None
                })
                logger.info(f"Successfully calculated prediction for {ticker.symbol}")

            except Exception as e:
                logger.error(f"Error calculating prediction for {ticker.symbol}: {e}")
                results['predictions'].append({
                    'symbol': ticker.symbol,
                    'success': False,
                    'error': str(e)
                })

        successful = sum(1 for p in results['predictions'] if p['success'])
        results['successful'] = successful
        results['failed'] = len(tickers) - successful

        logger.info(
            f"Prediction calculation completed: {successful}/{len(tickers)} successful"
        )

        return results

    def calculate_and_store_prediction(
        self, ticker_id: str, symbol: str
    ) -> Prediction:
        """
        Calculate prediction and signals for a ticker and store in database.

        Args:
            ticker_id: Ticker UUID
            symbol: Ticker symbol

        Returns:
            Prediction: Created prediction object
        """
        logger.info(f"Calculating prediction for {symbol}...")

        # Get current time
        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)

        # Get latest market data
        latest_data = self.market_data_repo.get_latest_price(ticker_id, '1m')

        if not latest_data:
            raise Exception(f"No market data found for {symbol}")

        # Validate data freshness (must be <5 minutes old)
        data_age_seconds = (current_time - latest_data.timestamp.replace(tzinfo=None)).total_seconds()
        if data_age_seconds > 300:  # 5 minutes
            raise Exception(f"Market data for {symbol} is stale ({data_age_seconds:.0f}s old). Data sync may still be running. Aborting prediction.")

        current_price = float(latest_data.close)

        # Calculate reference levels using real market data
        ref_levels_dict = self._calculate_reference_levels_dict(ticker_id, symbol)

        if not ref_levels_dict:
            logger.warning(f"No reference levels calculated for {symbol}, skipping prediction")
            raise Exception(f"Cannot calculate prediction without reference levels for {symbol}")

        # Calculate signals
        signals_result = signals.calculate_signals(current_price, ref_levels_dict)

        # Get market status
        market_status_obj = get_market_status(symbol, current_time)
        market_status = market_status_obj.status

        # Calculate volatility (if we have hourly data)
        volatility_level = 'MODERATE'  # Default
        try:
            hourly_data_list = self.market_data_repo.get_recent_data(ticker_id, '1h', hours=24)
            if hourly_data_list and len(hourly_data_list) > 1:
                hourly_hist = self._market_data_to_dataframe(hourly_data_list)
                midnight_open = ref_levels_dict.get('daily_open')
                if midnight_open:
                    hourly_movement = get_hourly_movement(hourly_hist, current_time, midnight_open)
                    volatility = calculate_volatility(hourly_movement)
                    volatility_level = volatility.level
        except Exception as e:
            logger.warning(f"Could not calculate volatility for {symbol}: {e}")

        # Create prediction object with baseline_price for verification
        prediction = Prediction(
            ticker_id=ticker_id,
            timestamp=current_time,
            prediction=signals_result['prediction'],
            confidence=signals_result['confidence'],
            weighted_score=signals_result['weighted_score'],
            bullish_count=signals_result['bullish_count'],
            bearish_count=len(signals_result['signals']) - signals_result['bullish_count'],
            total_signals=len(signals_result['signals']),
            market_status=market_status,
            volatility_level=volatility_level,
            # Store baseline price in metadata for verification
            metadata={'baseline_price': current_price, 'baseline_timestamp': current_time.isoformat()}
        )

        # Store prediction
        stored_prediction = self.prediction_repo.store_prediction(prediction)

        # Create and store signals (skip N/A signals where signal is None)
        signal_objects = []
        for sig_data in signals_result['signals'].values():
            # Skip N/A signals (where signal is None) - they don't contribute to predictions
            if sig_data['signal'] is None:
                continue

            # Handle None values for distance calculations
            weighted_contribution = sig_data['signal'] * sig_data['weight']
            distance_percentage = ((sig_data['distance'] / sig_data['value']) * 100) if (sig_data['value'] and sig_data['distance'] is not None) else 0.0

            signal = Signal(
                prediction_id=stored_prediction.id,
                reference_level_name=sig_data['level'],
                reference_level_value=sig_data['value'],
                current_price=current_price,
                signal=sig_data['signal'],
                weight=sig_data['weight'],
                weighted_contribution=weighted_contribution,
                distance=sig_data['distance'],
                distance_percentage=distance_percentage,
                status=sig_data['status']
            )
            signal_objects.append(signal)

        self.prediction_repo.store_signals(stored_prediction.id, signal_objects)

        logger.info(
            f"Stored prediction for {symbol}: {prediction.prediction} "
            f"(confidence: {prediction.confidence:.2f}%)"
        )

        return stored_prediction

    def cleanup_expired_data(self) -> Dict[str, Any]:
        """
        Clean up old data based on retention policies.

        Returns:
            Dict[str, Any]: Summary of cleanup results
        """
        logger.info("Starting data cleanup...")

        # Placeholder for cleanup logic
        # In production, implement actual cleanup based on DatabaseConfig retention settings

        results = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'deleted_records': {
                'minute_data': 0,
                'hourly_data': 0,
                'predictions': 0
            }
        }

        logger.info("Data cleanup completed")

        return results

    def _convert_to_market_data(
        self, ticker_id: str, df, interval: str, fetched_at: datetime = None
    ) -> List[MarketData]:
        """
        Convert pandas DataFrame to MarketData objects.

        Args:
            ticker_id: Ticker UUID
            df: Pandas DataFrame with OHLC data
            interval: Time interval (1m, 1h, 1d)
            fetched_at: Timestamp when data was fetched (for freshness tracking)

        Returns:
            List[MarketData]: List of MarketData objects
        """
        if df is None or df.empty:
            return []

        if fetched_at is None:
            fetched_at = datetime.utcnow()

        market_data_list = []

        for index, row in df.iterrows():
            try:
                market_data = MarketData(
                    ticker_id=ticker_id,
                    timestamp=index.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if 'Volume' in row else None,
                    interval=interval,
                    fetched_at=fetched_at
                )
                market_data_list.append(market_data)

            except Exception as e:
                logger.warning(f"Error converting row to MarketData: {e}")
                continue

        return market_data_list

    def _market_data_to_dataframe(self, market_data_list: List[MarketData]) -> pd.DataFrame:
        """
        Convert list of MarketData objects to pandas DataFrame.

        Args:
            market_data_list: List of MarketData objects

        Returns:
            pd.DataFrame: DataFrame with OHLC data indexed by timestamp
        """
        if not market_data_list:
            return pd.DataFrame()

        data = []
        for md in market_data_list:
            data.append({
                'Open': md.open,
                'High': md.high,
                'Low': md.low,
                'Close': md.close,
                'Volume': md.volume if md.volume else 0
            })

        df = pd.DataFrame(data, index=[md.timestamp for md in market_data_list])
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize('UTC') if df.index.tz is None else df.index.tz_convert('UTC')

        return df

    def _calculate_reference_levels_dict(
        self, ticker_id: str, symbol: str
    ) -> Dict[str, float]:
        """
        Calculate reference levels for a ticker using real market data.

        Args:
            ticker_id: Ticker UUID
            symbol: Ticker symbol

        Returns:
            Dict[str, float]: Reference levels dictionary
        """
        try:
            # Get current time
            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)

            # Fetch historical data from database
            hourly_data_list = self.market_data_repo.get_recent_data(ticker_id, '1h', hours=168)  # 7 days
            minute_data_list = self.market_data_repo.get_recent_data(ticker_id, '1m', hours=48)   # 2 days
            daily_data_list = self.market_data_repo.get_recent_data(ticker_id, '1d', hours=720)   # 30 days

            if not hourly_data_list:
                raise Exception(f"Insufficient market data for {symbol} - no hourly data available. Cannot calculate reliable predictions without complete reference data.")

            if not minute_data_list:
                raise Exception(f"Insufficient market data for {symbol} - no minute data available. Cannot calculate reliable predictions without complete reference data.")

            if not daily_data_list:
                raise Exception(f"Insufficient market data for {symbol} - no daily data available. Cannot calculate reliable predictions without complete reference data.")

            # Convert to DataFrames
            hourly_hist = self._market_data_to_dataframe(hourly_data_list)
            minute_hist = self._market_data_to_dataframe(minute_data_list) if minute_data_list else pd.DataFrame()
            daily_hist = self._market_data_to_dataframe(daily_data_list) if daily_data_list else pd.DataFrame()

            logger.debug(f"Fetched data for {symbol}: {len(hourly_hist)} hourly, {len(minute_hist)} minute, {len(daily_hist)} daily records")

            # Calculate reference levels using the analysis module
            ref_levels = reference_levels.calculate_all_reference_levels(
                hourly_hist=hourly_hist,
                minute_hist=minute_hist,
                daily_hist=daily_hist,
                current_time=current_time
            )

            # Store reference levels to database (including ranges)
            try:
                self._store_reference_levels(ticker_id, ref_levels, current_time)
            except Exception as e:
                logger.warning(f"Failed to store reference levels for {symbol}: {e}")

            # Convert to dictionary (handle both dict and ReferenceLevels object)
            ref_levels_dict = ref_levels if isinstance(ref_levels, dict) else ref_levels.to_dict()

            logger.info(f"Calculated {len(ref_levels_dict)} reference levels for {symbol}")

            return ref_levels_dict

        except Exception as e:
            logger.error(f"Error calculating reference levels for {symbol}: {e}", exc_info=True)
            # Fallback: return minimal set with latest price
            try:
                latest = self.market_data_repo.get_latest_price(ticker_id, '1m')
                if latest:
                    logger.warning(f"Using fallback reference levels for {symbol}")
                    return {'daily_open': float(latest.close)}
            except:
                pass

            # Last resort: return empty dict (signals calculation will handle this)
            logger.error(f"Failed to calculate any reference levels for {symbol}")
            return {}

    def _store_reference_levels(
        self, ticker_id: str, analysis_ref_levels, current_time: datetime
    ) -> None:
        """
        Convert analysis ReferenceLevels to database ReferenceLevels and store.

        Args:
            ticker_id: Ticker UUID
            analysis_ref_levels: ReferenceLevels object from analysis module
            current_time: Current timestamp
        """
        # Import RangeLevel for type checking
        from ..models.market_data import RangeLevel

        # Convert analysis ReferenceLevels to database ReferenceLevels
        db_ref_levels = ReferenceLevels(
            ticker_id=ticker_id,
            timestamp=current_time,
            # Single-price levels
            daily_open=analysis_ref_levels.daily_open,
            hourly_open=analysis_ref_levels.hourly_open,
            four_hourly_open=analysis_ref_levels.four_hourly_open,
            thirty_min_open=analysis_ref_levels.thirty_min_open,
            prev_day_high=analysis_ref_levels.prev_day_high or analysis_ref_levels.previous_day_high,
            prev_day_low=analysis_ref_levels.prev_day_low or analysis_ref_levels.previous_day_low,
            prev_week_open=analysis_ref_levels.prev_week_open,
            weekly_open=analysis_ref_levels.weekly_open,
            monthly_open=analysis_ref_levels.monthly_open,
            seven_am_open=analysis_ref_levels.seven_am_open,
            eight_thirty_am_open=analysis_ref_levels.eight_thirty_am_open,
            # Range-based levels (extract high/low from RangeLevel objects)
            range_0700_0715_high=analysis_ref_levels.range_0700_0715.high if analysis_ref_levels.range_0700_0715 else None,
            range_0700_0715_low=analysis_ref_levels.range_0700_0715.low if analysis_ref_levels.range_0700_0715 else None,
            range_0830_0845_high=analysis_ref_levels.range_0830_0845.high if analysis_ref_levels.range_0830_0845 else None,
            range_0830_0845_low=analysis_ref_levels.range_0830_0845.low if analysis_ref_levels.range_0830_0845 else None,
            asian_kill_zone_high=analysis_ref_levels.asian_kill_zone.high if analysis_ref_levels.asian_kill_zone else None,
            asian_kill_zone_low=analysis_ref_levels.asian_kill_zone.low if analysis_ref_levels.asian_kill_zone else None,
            london_kill_zone_high=analysis_ref_levels.london_kill_zone.high if analysis_ref_levels.london_kill_zone else None,
            london_kill_zone_low=analysis_ref_levels.london_kill_zone.low if analysis_ref_levels.london_kill_zone else None,
            ny_am_kill_zone_high=analysis_ref_levels.ny_am_kill_zone.high if analysis_ref_levels.ny_am_kill_zone else None,
            ny_am_kill_zone_low=analysis_ref_levels.ny_am_kill_zone.low if analysis_ref_levels.ny_am_kill_zone else None,
            ny_pm_kill_zone_high=analysis_ref_levels.ny_pm_kill_zone.high if analysis_ref_levels.ny_pm_kill_zone else None,
            ny_pm_kill_zone_low=analysis_ref_levels.ny_pm_kill_zone.low if analysis_ref_levels.ny_pm_kill_zone else None,
        )

        # Store to database (upsert)
        self.ref_levels_repo.store_reference_levels(db_ref_levels)
        logger.debug(f"Stored reference levels (including ranges) for ticker {ticker_id}")

    def _validate_data_completeness(self, data: Dict[str, Any], symbol: str) -> None:
        """
        Validate that all required data intervals have sufficient records.

        Args:
            data: Dictionary with all interval data (1m, 5m, 15m, 30m, 1h, 1d)
            symbol: Ticker symbol for logging

        Raises:
            Exception: If any interval has fewer records than required minimum
        """
        # Define minimum required records for each interval
        required_intervals = {
            'minute_hist': 100,         # ~1.5+ hours of minute data (1m bars)
            'five_min_hist': 84,        # ~7+ hours of 5-minute data
            'fifteen_min_hist': 28,     # ~7+ hours of 15-minute data
            'thirty_min_hist': 48,      # ~1 day of 30-min data
            'hourly_hist': 24,          # ~1 day of hourly data
            'daily_hist': 5             # ~1 week of daily data
        }

        missing_intervals = []
        incomplete_intervals = []

        # Check each required interval
        for interval_name, min_records in required_intervals.items():
            # Check if interval is missing or empty (handle pandas DataFrames)
            if interval_name not in data or data[interval_name] is None:
                missing_intervals.append(interval_name)
            elif hasattr(data[interval_name], 'empty') and data[interval_name].empty:
                # DataFrame is empty
                missing_intervals.append(interval_name)
            elif len(data[interval_name]) < min_records:
                incomplete_intervals.append({
                    'interval': interval_name,
                    'records': len(data[interval_name]),
                    'required': min_records
                })

        # Raise exception if any intervals are missing or incomplete
        if missing_intervals:
            raise Exception(
                f"Missing required data for {symbol}: {', '.join(missing_intervals)}. "
                f"Data fetch may be incomplete. Aborting to prevent storing partial data."
            )

        if incomplete_intervals:
            incomplete_str = '; '.join([
                f"{i['interval']}: {i['records']}/{i['required']} records"
                for i in incomplete_intervals
            ])
            raise Exception(
                f"Insufficient data for {symbol}: {incomplete_str}. "
                f"Minimum thresholds not met. Aborting to ensure prediction accuracy."
            )

        # Log successful validation
        record_counts = ', '.join([
            f"{k}: {len(data[k]) if (k in data and data[k] is not None) else 0}"
            for k in required_intervals.keys()
        ])
        logger.info(f"Data completeness validation passed for {symbol}: {record_counts}")
