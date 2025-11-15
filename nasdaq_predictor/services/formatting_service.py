"""
Response Formatting Service.

Handles formatting market predictions into standardized API response format.
Separates formatting logic from calculation and caching logic.
"""

import logging
import pytz
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FormattingService:
    """
    Service for formatting market prediction data into API responses.

    Handles:
    1. Timestamp formatting (UTC, NY, London timezones)
    2. Reference level formatting
    3. Signal detail formatting
    4. Intraday prediction formatting
    5. Complete response assembly
    """

    def format_fresh_prediction(
        self,
        ticker_symbol: str,
        current_price: float,
        current_time: datetime,
        reference_levels: Any,
        signals: Dict[str, Any],
        session_ranges: Dict[str, Any],
        intraday_predictions: Any,
        volatility: Dict[str, Any],
        ny_open: Optional[float] = None,
        midnight_open: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Format fresh prediction data from yfinance calculation.

        Args:
            ticker_symbol: Ticker symbol
            current_price: Current market price
            current_time: Current UTC time
            reference_levels: Reference levels object
            signals: Signals calculation result dict
            session_ranges: Session ranges dict
            intraday_predictions: Intraday predictions object (from calculate_intraday_predictions)
            volatility: Volatility calculation dict
            ny_open: NY market open price (optional)
            midnight_open: Midnight open price (optional)

        Returns:
            Formatted prediction response dict
        """
        try:
            # Format timestamps
            ny_time = current_time.astimezone(pytz.timezone('US/Eastern'))
            london_time = current_time.astimezone(pytz.timezone('Europe/London'))

            # Build response
            result = {
                'current_price': current_price,
                'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'current_time_ny': ny_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'current_time_london': london_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'market_status': signals.get('market_status', 'UNKNOWN'),
                'next_open': signals.get('next_open'),
                'midnight_open': midnight_open,
                'ny_open': ny_open,
                'session_ranges': session_ranges,
                'intraday_predictions': asdict(intraday_predictions),
                'morning_reference_prices': {
                    '7am_open': reference_levels.seven_am_open,
                    '830am_open': reference_levels.eight_thirty_am_open
                },
                'volatility': {
                    'hourly_range_pct': volatility.get('hourly_range_pct'),
                    'level': volatility.get('level')
                },
                'reference_levels': self._format_reference_levels_from_object(reference_levels),
                'signals_detail': signals.get('signals', {}),
                'source': 'yfinance',
                **{k: v for k, v in signals.items() if k not in ['signals', 'market_status', 'next_open']}
            }

            logger.debug(f"Formatted fresh prediction for {ticker_symbol}")
            return result

        except Exception as e:
            logger.error(f"Error formatting fresh prediction for {ticker_symbol}: {str(e)}", exc_info=True)
            raise

    def format_cached_prediction(
        self,
        ticker_symbol: str,
        current_price: float,
        current_time: datetime,
        prediction_data: Dict[str, Any],
        market_data: Any,
        reference_levels: Any = None,
        intraday_preds: list = None,
        data_age_minutes: float = 0.0
    ) -> Dict[str, Any]:
        """
        Format cached prediction data from database.

        Args:
            ticker_symbol: Ticker symbol
            current_price: Current market price
            current_time: Current UTC time
            prediction_data: Prediction object with prediction, confidence, weighted_score, etc.
            market_data: Market data object with OHLC data
            reference_levels: Reference levels object (optional)
            intraday_preds: List of intraday prediction objects (optional)
            data_age_minutes: How old the cached data is in minutes

        Returns:
            Formatted cached prediction response dict
        """
        try:
            # Format timestamps
            ny_time = current_time.astimezone(pytz.timezone('US/Eastern'))
            london_time = current_time.astimezone(pytz.timezone('Europe/London'))

            # Base response from database prediction
            result = {
                'current_price': float(current_price),
                'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'current_time_ny': ny_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'current_time_london': london_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'prediction': prediction_data.get('prediction'),
                'confidence': float(prediction_data.get('confidence', 0)),
                'weighted_score': float(prediction_data.get('weighted_score', 0)),
                'bullish_count': prediction_data.get('bullish_count'),
                'total_signals': prediction_data.get('total_signals'),
                'signals': prediction_data.get('signals', {}),
                'signals_detail': prediction_data.get('signals_detail', {}),
                'source': 'database',
                'data_age_minutes': data_age_minutes,
            }

            # Add reference levels if available
            if reference_levels:
                result['midnight_open'] = float(reference_levels.get('daily_open')) if reference_levels.get('daily_open') else None
                result['morning_reference_prices'] = {
                    '7am_open': float(reference_levels.get('seven_am_open')) if reference_levels.get('seven_am_open') else None,
                    '830am_open': float(reference_levels.get('eight_thirty_am_open')) if reference_levels.get('eight_thirty_am_open') else None
                }
                result['reference_levels'] = self._format_reference_levels_from_dict(reference_levels)

            # Add intraday predictions if available
            if intraday_preds:
                result['intraday_predictions'] = self._format_intraday_predictions_from_list(intraday_preds, current_time)

            logger.debug(f"Formatted cached prediction for {ticker_symbol} (age: {data_age_minutes:.1f}m)")
            return result

        except Exception as e:
            logger.error(f"Error formatting cached prediction for {ticker_symbol}: {str(e)}", exc_info=True)
            raise

    def format_batch_response(
        self,
        predictions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format batch of predictions for API response.

        Args:
            predictions: Dict of ticker -> prediction data (from process_ticker_data calls)

        Returns:
            Formatted batch response
        """
        try:
            result = {
                'count': len(predictions),
                'data': predictions,
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S %Z'),
                'status': 'success' if predictions else 'empty'
            }

            logger.info(f"Formatted batch response with {len(predictions)} predictions")
            return result

        except Exception as e:
            logger.error(f"Error formatting batch response: {str(e)}", exc_info=True)
            raise

    def _format_reference_levels_from_object(self, reference_levels: Any) -> Dict[str, Any]:
        """
        Format reference levels from object (yfinance calculation result).

        Args:
            reference_levels: Reference levels object

        Returns:
            Formatted reference levels dict
        """
        return {
            'single_price': {
                'daily_open_midnight': reference_levels.daily_open,
                'ny_open_0830': reference_levels.eight_thirty_am_open,
                'thirty_min_open': reference_levels.thirty_min_open,
                'ny_open_0700': reference_levels.seven_am_open,
                'four_hour_open': reference_levels.four_hourly_open,
                'weekly_open': reference_levels.weekly_open,
                'hourly_open': reference_levels.hourly_open,
                'previous_hourly_open': reference_levels.previous_hourly_open,
                'previous_week_open': reference_levels.prev_week_open,
                'previous_day_high': reference_levels.previous_day_high or reference_levels.prev_day_high,
                'previous_day_low': reference_levels.previous_day_low or reference_levels.prev_day_low,
                'monthly_open': reference_levels.monthly_open
            },
            'ranges': {
                'range_0700_0715': {'high': reference_levels.range_0700_0715.high, 'low': reference_levels.range_0700_0715.low} if reference_levels.range_0700_0715 else None,
                'range_0830_0845': {'high': reference_levels.range_0830_0845.high, 'low': reference_levels.range_0830_0845.low} if reference_levels.range_0830_0845 else None,
                'asian_kill_zone': {'high': reference_levels.asian_kill_zone.high, 'low': reference_levels.asian_kill_zone.low} if reference_levels.asian_kill_zone else None,
                'london_kill_zone': {'high': reference_levels.london_kill_zone.high, 'low': reference_levels.london_kill_zone.low} if reference_levels.london_kill_zone else None,
                'ny_am_kill_zone': {'high': reference_levels.ny_am_kill_zone.high, 'low': reference_levels.ny_am_kill_zone.low} if reference_levels.ny_am_kill_zone else None,
                'ny_pm_kill_zone': {'high': reference_levels.ny_pm_kill_zone.high, 'low': reference_levels.ny_pm_kill_zone.low} if reference_levels.ny_pm_kill_zone else None
            }
        }

    def _format_reference_levels_from_dict(self, reference_levels: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format reference levels from dict (database result).

        Args:
            reference_levels: Reference levels dict from database

        Returns:
            Formatted reference levels dict
        """
        return {
            'single_price': {
                'daily_open_midnight': float(reference_levels.get('daily_open')) if reference_levels.get('daily_open') else None,
                'ny_open_0830': float(reference_levels.get('eight_thirty_am_open')) if reference_levels.get('eight_thirty_am_open') else None,
                'thirty_min_open': float(reference_levels.get('thirty_min_open')) if reference_levels.get('thirty_min_open') else None,
                'ny_open_0700': float(reference_levels.get('seven_am_open')) if reference_levels.get('seven_am_open') else None,
                'four_hour_open': float(reference_levels.get('four_hourly_open')) if reference_levels.get('four_hourly_open') else None,
                'weekly_open': float(reference_levels.get('weekly_open')) if reference_levels.get('weekly_open') else None,
                'hourly_open': float(reference_levels.get('hourly_open')) if reference_levels.get('hourly_open') else None,
                'previous_hourly_open': float(reference_levels.get('previous_hourly_open')) if reference_levels.get('previous_hourly_open') else None,
                'previous_week_open': float(reference_levels.get('prev_week_open')) if reference_levels.get('prev_week_open') else None,
                'previous_day_high': float(reference_levels.get('prev_day_high')) if reference_levels.get('prev_day_high') else None,
                'previous_day_low': float(reference_levels.get('prev_day_low')) if reference_levels.get('prev_day_low') else None,
                'monthly_open': float(reference_levels.get('monthly_open')) if reference_levels.get('monthly_open') else None
            },
            'ranges': {
                'range_0700_0715': self._format_range(reference_levels.get('range_0700_0715_high'), reference_levels.get('range_0700_0715_low')),
                'range_0830_0845': self._format_range(reference_levels.get('range_0830_0845_high'), reference_levels.get('range_0830_0845_low')),
                'asian_kill_zone': self._format_range(reference_levels.get('asian_kill_zone_high'), reference_levels.get('asian_kill_zone_low')),
                'london_kill_zone': self._format_range(reference_levels.get('london_kill_zone_high'), reference_levels.get('london_kill_zone_low')),
                'ny_am_kill_zone': self._format_range(reference_levels.get('ny_am_kill_zone_high'), reference_levels.get('ny_am_kill_zone_low')),
                'ny_pm_kill_zone': self._format_range(reference_levels.get('ny_pm_kill_zone_high'), reference_levels.get('ny_pm_kill_zone_low'))
            }
        }

    def _format_range(self, high: Optional[float], low: Optional[float]) -> Optional[Dict[str, float]]:
        """
        Format a price range (high/low).

        Args:
            high: High price
            low: Low price

        Returns:
            Formatted range dict or None if missing values
        """
        if high is not None and low is not None:
            return {'high': float(high), 'low': float(low)}
        return None

    def _format_intraday_predictions_from_list(
        self,
        intraday_preds: list,
        current_time: datetime
    ) -> Dict[str, Any]:
        """
        Format intraday predictions from database list into response format.

        Args:
            intraday_preds: List of IntradayPrediction objects from database
            current_time: Current UTC time

        Returns:
            Formatted intraday predictions dict
        """
        ny_tz = pytz.timezone('US/Eastern')
        ny_time = current_time.astimezone(ny_tz)

        # Initialize result structure
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
