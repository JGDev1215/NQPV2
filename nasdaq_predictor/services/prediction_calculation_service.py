"""
Prediction Calculation Service.

Handles calculating fresh market predictions from yfinance data.
Implements the core analysis and signal generation logic.
"""

import logging
import pytz
from typing import Optional, Dict, Any
from dataclasses import asdict

from ..data.fetcher import YahooFinanceDataFetcher
from ..analysis.reference_levels import (
    calculate_all_reference_levels,
    get_hourly_movement,
    get_ny_open
)
from ..analysis.signals import calculate_signals
from ..analysis.sessions import get_all_session_ranges
from ..analysis.confidence import calculate_intraday_predictions
from ..analysis.volatility import calculate_volatility
from ..utils.market_status import get_market_status

logger = logging.getLogger(__name__)


class PredictionCalculationService:
    """
    Service for calculating fresh market predictions from yfinance.

    Handles:
    1. Fetching market data from yfinance
    2. Calculating reference levels
    3. Generating signals
    4. Computing intraday predictions
    5. Formatting response
    """

    def __init__(self, data_fetcher: YahooFinanceDataFetcher):
        """
        Initialize PredictionCalculationService.

        Args:
            data_fetcher: YahooFinanceDataFetcher for market data
        """
        self.data_fetcher = data_fetcher

    def calculate_fresh_data(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Calculate fresh prediction data from yfinance.

        Args:
            ticker_symbol: Ticker symbol to analyze

        Returns:
            Calculated market data or None if calculation fails
        """
        try:
            # Fetch data from yfinance
            data = self.data_fetcher.fetch_ticker_data(ticker_symbol)
            if not data:
                logger.warning(f"Failed to fetch data for {ticker_symbol}")
                return None

            return self._process_fetched_data(ticker_symbol, data)

        except Exception as e:
            logger.error(f"Error calculating fresh data for {ticker_symbol}: {str(e)}", exc_info=True)
            return None

    def _process_fetched_data(self, ticker_symbol: str, data: Dict) -> Dict[str, Any]:
        """
        Process fetched data through analysis pipeline.

        Args:
            ticker_symbol: Ticker symbol
            data: Fetched market data from yfinance

        Returns:
            Processed market analysis result
        """
        current_price = data['current_price']
        current_time = data['current_time']
        hourly_hist = data['hourly_hist']
        minute_hist = data['minute_hist']
        daily_hist = data['daily_hist']

        # Calculate reference levels
        reference_levels = calculate_all_reference_levels(
            hourly_hist,
            minute_hist,
            daily_hist,
            current_time
        )

        # Calculate signals
        signals = calculate_signals(current_price, reference_levels)

        # Get midnight and NY open
        midnight_open = reference_levels.daily_open
        ny_open = get_ny_open(hourly_hist, current_time)

        # Get hourly movement for volatility calculation
        hourly_movement = get_hourly_movement(hourly_hist, current_time, midnight_open)

        # Calculate session ranges
        session_ranges = get_all_session_ranges(
            ticker_symbol,
            current_time,
            current_price,
            self.data_fetcher
        )

        # Get market status
        market_status = get_market_status(ticker_symbol, current_time)

        # Calculate intraday predictions
        intraday_predictions = calculate_intraday_predictions(
            base_confidence=signals['confidence'],
            base_prediction=signals['prediction'],
            current_time_utc=current_time,
            hourly_data=hourly_hist,
            ticker_symbol=ticker_symbol,
            seven_am_open=reference_levels.seven_am_open,
            eight_thirty_am_open=reference_levels.eight_thirty_am_open,
            previous_day_predictions=None
        )

        # Calculate volatility
        volatility = calculate_volatility(hourly_movement)

        # Format timestamps for display
        ny_time = current_time.astimezone(pytz.timezone('US/Eastern'))
        london_time = current_time.astimezone(pytz.timezone('Europe/London'))

        # Build response
        result = {
            'current_price': current_price,
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'current_time_ny': ny_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'current_time_london': london_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'market_status': market_status.status,
            'next_open': market_status.next_open,
            'midnight_open': midnight_open,
            'ny_open': ny_open,
            'session_ranges': session_ranges,
            'intraday_predictions': asdict(intraday_predictions),
            'morning_reference_prices': {
                '7am_open': reference_levels.seven_am_open,
                '830am_open': reference_levels.eight_thirty_am_open
            },
            'volatility': {
                'hourly_range_pct': volatility.hourly_range_pct,
                'level': volatility.level
            },
            # Reference levels data for UI table
            'reference_levels': self._format_reference_levels(reference_levels),
            # Signals detail for each level (for UI table display)
            'signals_detail': signals['signals'],
            'source': 'yfinance',
            **signals
        }

        logger.info(f"Calculated fresh data for {ticker_symbol} from yfinance")
        return result

    def _format_reference_levels(self, reference_levels) -> Dict[str, Any]:
        """Format reference levels for response."""
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
