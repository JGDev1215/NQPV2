"""
Cache Service for retrieving cached predictions from database.

Handles the "database-first" approach where recent predictions are returned
from cache instead of recalculating from yfinance.
"""

import logging
import pytz
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..database.repositories.ticker_repository import TickerRepository
from ..database.repositories.market_data_repository import MarketDataRepository
from ..database.repositories.prediction_repository import PredictionRepository
from ..database.repositories.intraday_prediction_repository import IntradayPredictionRepository
from ..database.repositories.reference_levels_repository import ReferenceLevelsRepository
from ..utils.market_status import get_market_status

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for managing prediction cache from database.

    Implements database-first approach:
    1. Check database for recent prediction (< 5 min old during market hours)
    2. If found, return from database (fast)
    3. If not found, return None (caller will calculate fresh)
    """

    CACHE_DURATION_MINUTES = 5  # Reduced from 15 for fresher predictions during volatile periods

    def __init__(
        self,
        ticker_repo: TickerRepository,
        market_data_repo: MarketDataRepository,
        prediction_repo: PredictionRepository,
        intraday_repo: IntradayPredictionRepository,
        ref_levels_repo: ReferenceLevelsRepository
    ):
        """
        Initialize CacheService with injected dependencies.

        Args:
            ticker_repo: Repository for ticker data
            market_data_repo: Repository for market data
            prediction_repo: Repository for predictions
            intraday_repo: Repository for intraday predictions
            ref_levels_repo: Repository for reference levels
        """
        self.ticker_repo = ticker_repo
        self.market_data_repo = market_data_repo
        self.prediction_repo = prediction_repo
        self.intraday_repo = intraday_repo
        self.ref_levels_repo = ref_levels_repo

    def get_cached_prediction(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached prediction from database if recent.

        Args:
            ticker_symbol: Ticker symbol

        Returns:
            Formatted prediction if found and recent, None if cache miss
        """
        try:
            # Get ticker from database
            ticker = self.ticker_repo.get_ticker_by_symbol(ticker_symbol)
            if not ticker:
                logger.debug(f"Ticker {ticker_symbol} not found in database")
                return None

            # Get latest prediction
            prediction = self.prediction_repo.get_latest_prediction(ticker.id)
            if not prediction:
                logger.debug(f"No prediction found for {ticker_symbol}")
                return None

            # Check if prediction is recent (< 15 minutes old)
            age = datetime.utcnow() - prediction.timestamp.replace(tzinfo=None)
            if age > timedelta(minutes=self.CACHE_DURATION_MINUTES):
                logger.debug(f"Prediction for {ticker_symbol} is too old ({age.total_seconds()/60:.1f} min)")
                return None

            # Get latest market data
            latest_data = self.market_data_repo.get_latest_price(ticker.id, '1m')
            if not latest_data:
                logger.debug(f"No market data found for {ticker_symbol}")
                return None

            # Get reference levels
            ref_levels = self.ref_levels_repo.get_latest_reference_levels(ticker.id)

            # Format response from database
            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            ny_time = current_time.astimezone(pytz.timezone('US/Eastern'))
            london_time = current_time.astimezone(pytz.timezone('Europe/London'))

            # Get market status
            market_status = get_market_status(ticker_symbol, current_time)

            result = {
                'current_price': float(latest_data.close),
                'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'current_time_ny': ny_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'current_time_london': london_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'market_status': market_status.status,
                'next_open': market_status.next_open,
                'prediction': prediction.prediction,
                'confidence': float(prediction.confidence),
                'weighted_score': float(prediction.weighted_score),
                'bullish_count': prediction.bullish_count,
                'total_signals': prediction.total_signals,
                'signals': {},  # TODO: Load signals from database
                'signals_detail': {},
                'source': 'database',
                'data_age_minutes': age.total_seconds() / 60,
            }

            # Add reference levels if available
            if ref_levels:
                result['midnight_open'] = float(ref_levels.daily_open) if ref_levels.daily_open else None
                result['morning_reference_prices'] = {
                    '7am_open': float(ref_levels.seven_am_open) if ref_levels.seven_am_open else None,
                    '830am_open': float(ref_levels.eight_thirty_am_open) if ref_levels.eight_thirty_am_open else None
                }
                # Add reference levels data for UI table
                result['reference_levels'] = self._format_reference_levels(ref_levels)

            # Add intraday predictions from database
            try:
                intraday_preds = self.intraday_repo.get_24h_intraday_predictions(ticker.id)
                if intraday_preds:
                    result['intraday_predictions'] = self._format_intraday_predictions(intraday_preds, current_time)
            except Exception as e:
                logger.warning(f"Failed to load intraday predictions for {ticker_symbol}: {e}")

            logger.info(f"Returning {ticker_symbol} data from cache (cached)")
            return result

        except Exception as e:
            logger.warning(f"Error getting cached prediction for {ticker_symbol}: {e}")
            return None

    def _format_reference_levels(self, ref_levels) -> Dict[str, Any]:
        """Format reference levels from database."""
        return {
            'single_price': {
                'daily_open_midnight': float(ref_levels.daily_open) if ref_levels.daily_open else None,
                'ny_open_0830': float(ref_levels.eight_thirty_am_open) if ref_levels.eight_thirty_am_open else None,
                'thirty_min_open': float(ref_levels.thirty_min_open) if ref_levels.thirty_min_open else None,
                'ny_open_0700': float(ref_levels.seven_am_open) if ref_levels.seven_am_open else None,
                'four_hour_open': float(ref_levels.four_hourly_open) if ref_levels.four_hourly_open else None,
                'weekly_open': float(ref_levels.weekly_open) if ref_levels.weekly_open else None,
                'hourly_open': float(ref_levels.hourly_open) if ref_levels.hourly_open else None,
                'previous_hourly_open': float(ref_levels.previous_hourly_open) if ref_levels.previous_hourly_open else None,
                'previous_week_open': float(ref_levels.prev_week_open) if ref_levels.prev_week_open else None,
                'previous_day_high': float(ref_levels.prev_day_high) if ref_levels.prev_day_high else None,
                'previous_day_low': float(ref_levels.prev_day_low) if ref_levels.prev_day_low else None,
                'monthly_open': float(ref_levels.monthly_open) if ref_levels.monthly_open else None
            },
            'ranges': {
                'range_0700_0715': {'high': float(ref_levels.range_0700_0715_high), 'low': float(ref_levels.range_0700_0715_low)} if ref_levels.range_0700_0715_high and ref_levels.range_0700_0715_low else None,
                'range_0830_0845': {'high': float(ref_levels.range_0830_0845_high), 'low': float(ref_levels.range_0830_0845_low)} if ref_levels.range_0830_0845_high and ref_levels.range_0830_0845_low else None,
                'asian_kill_zone': {'high': float(ref_levels.asian_kill_zone_high), 'low': float(ref_levels.asian_kill_zone_low)} if ref_levels.asian_kill_zone_high and ref_levels.asian_kill_zone_low else None,
                'london_kill_zone': {'high': float(ref_levels.london_kill_zone_high), 'low': float(ref_levels.london_kill_zone_low)} if ref_levels.london_kill_zone_high and ref_levels.london_kill_zone_low else None,
                'ny_am_kill_zone': {'high': float(ref_levels.ny_am_kill_zone_high), 'low': float(ref_levels.ny_am_kill_zone_low)} if ref_levels.ny_am_kill_zone_high and ref_levels.ny_am_kill_zone_low else None,
                'ny_pm_kill_zone': {'high': float(ref_levels.ny_pm_kill_zone_high), 'low': float(ref_levels.ny_pm_kill_zone_low)} if ref_levels.ny_pm_kill_zone_high and ref_levels.ny_pm_kill_zone_low else None
            }
        }

    def _format_intraday_predictions(self, intraday_preds: list, current_time: datetime) -> Dict[str, Any]:
        """Format intraday predictions from database."""
        ny_tz = pytz.timezone('US/Eastern')
        ny_time = current_time.astimezone(ny_tz)

        result = {
            'current_time_utc': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'current_time_ny': ny_time.strftime('%Y-%m-%d %I:%M %p %Z'),
            'current_time_window': 'post_10am',
            'predictions_locked': False,
            'predictions_locked_at': None,
            'next_prediction_time': None,
            'seven_am_open': None,
            'eight_thirty_am_open': None,
            'previous_day_9am': None,
            'previous_day_10am': None
        }

        # Find 9am and 10am predictions
        nine_am_pred = None
        ten_am_pred = None

        for pred in intraday_preds:
            if pred.target_hour == 9:
                nine_am_pred = pred
            elif pred.target_hour == 10:
                ten_am_pred = pred

        # Format 9am prediction
        if nine_am_pred:
            status = 'VERIFIED' if nine_am_pred.actual_result and nine_am_pred.actual_result != 'PENDING' else 'ACTIVE'
            result['nine_am'] = {
                'prediction': nine_am_pred.prediction,
                'confidence': float(nine_am_pred.final_confidence),
                'base_confidence': float(nine_am_pred.base_confidence),
                'decay_factor': float(nine_am_pred.decay_factor),
                'reference_open': float(nine_am_pred.reference_price),
                'target_close': float(nine_am_pred.target_close_price) if nine_am_pred.target_close_price else None,
                'actual_result': nine_am_pred.actual_result if nine_am_pred.actual_result else 'PENDING',
                'status': status,
                'time_until_target': 'PASSED' if ny_time.hour >= 10 else f"{10 - ny_time.hour}h {60 - ny_time.minute}m"
            }
            result['seven_am_open'] = float(nine_am_pred.reference_price)

        # Format 10am prediction
        if ten_am_pred:
            status = 'VERIFIED' if ten_am_pred.actual_result and ten_am_pred.actual_result != 'PENDING' else 'ACTIVE'
            result['ten_am'] = {
                'prediction': ten_am_pred.prediction,
                'confidence': float(ten_am_pred.final_confidence),
                'base_confidence': float(ten_am_pred.base_confidence),
                'decay_factor': float(ten_am_pred.decay_factor),
                'reference_open': float(ten_am_pred.reference_price),
                'target_close': float(ten_am_pred.target_close_price) if ten_am_pred.target_close_price else None,
                'actual_result': ten_am_pred.actual_result if ten_am_pred.actual_result else 'PENDING',
                'status': status,
                'time_until_target': 'PASSED' if ny_time.hour >= 11 else f"{11 - ny_time.hour}h {60 - ny_time.minute}m"
            }
            result['eight_thirty_am_open'] = float(ten_am_pred.reference_price)

        # Determine current time window
        hour_ny = ny_time.hour
        if hour_ny < 9:
            result['current_time_window'] = 'pre_9am'
        elif hour_ny < 10:
            result['current_time_window'] = 'between_9am_10am'
        else:
            result['current_time_window'] = 'post_10am'
            result['predictions_locked'] = True
            result['predictions_locked_at'] = '11:16 AM EDT/EST'

        return result
