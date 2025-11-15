"""
Intraday Prediction Verification Service for NQP application.

This service verifies hourly intraday predictions by comparing predicted direction
with actual price movements after the target hour has passed.
"""

import logging
import pytz
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..database.repositories.ticker_repository import TickerRepository
from ..database.repositories.market_data_repository import MarketDataRepository
from ..database.repositories.intraday_prediction_repository import IntradayPredictionRepository
from ..database.models.intraday_prediction import IntradayPrediction

logger = logging.getLogger(__name__)


class IntradayVerificationService:
    """Service to verify intraday prediction accuracy against actual market movements.

    Implements full dependency injection for all repository dependencies.
    """

    def __init__(
        self,
        ticker_repo: TickerRepository,
        market_data_repo: MarketDataRepository,
        intraday_repo: IntradayPredictionRepository
    ):
        """Initialize IntradayVerificationService with injected dependencies.

        Args:
            ticker_repo: TickerRepository for ticker management
            market_data_repo: MarketDataRepository for market data access
            intraday_repo: IntradayPredictionRepository for intraday prediction access
        """
        self.ticker_repo = ticker_repo
        self.market_data_repo = market_data_repo
        self.intraday_repo = intraday_repo

    def verify_pending_intraday_predictions(self) -> Dict[str, Any]:
        """
        Verify all pending intraday predictions where target hour has passed.

        Returns:
            Dict[str, Any]: Summary of verification results
        """
        logger.info("Starting intraday prediction verification...")

        current_time_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)

        tickers = self.ticker_repo.get_enabled_tickers()

        results = {
            'success': True,
            'timestamp': current_time_utc.isoformat(),
            'total_verified': 0,
            'correct': 0,
            'wrong': 0,
            'errors': []
        }

        for ticker in tickers:
            try:
                # Verify predictions for this ticker
                ticker_results = self._verify_ticker_intraday_predictions(
                    ticker.id,
                    ticker.symbol,
                    current_time_utc
                )

                results['total_verified'] += ticker_results['verified_count']
                results['correct'] += ticker_results['correct_count']
                results['wrong'] += ticker_results['wrong_count']

            except Exception as e:
                logger.error(f"Error verifying intraday predictions for {ticker.symbol}: {e}")
                results['errors'].append({
                    'ticker': ticker.symbol,
                    'error': str(e)
                })

        logger.info(
            f"Intraday verification completed: {results['total_verified']} predictions verified "
            f"({results['correct']} correct, {results['wrong']} wrong)"
        )

        return results

    def _verify_ticker_intraday_predictions(
        self,
        ticker_id: str,
        symbol: str,
        current_time_utc: datetime
    ) -> Dict[str, int]:
        """
        Verify intraday predictions for a specific ticker.

        Args:
            ticker_id: Ticker UUID
            symbol: Ticker symbol
            current_time_utc: Current UTC time

        Returns:
            Dict with verification counts
        """
        # Get today's predictions (NY timezone)
        predictions = self.intraday_repo.get_24h_intraday_predictions(ticker_id)

        if not predictions:
            logger.debug(f"No intraday predictions found for {symbol}")
            return {'verified_count': 0, 'correct_count': 0, 'wrong_count': 0}

        # Filter for PENDING predictions where target hour has passed
        pending_predictions = [
            p for p in predictions
            if (p.actual_result is None or p.actual_result == 'PENDING')
            and p.target_timestamp is not None
            and current_time_utc > p.target_timestamp + timedelta(hours=1)
        ]

        if not pending_predictions:
            logger.debug(f"No pending intraday predictions ready for verification for {symbol}")
            return {'verified_count': 0, 'correct_count': 0, 'wrong_count': 0}

        logger.info(
            f"Found {len(pending_predictions)} pending intraday predictions "
            f"ready for verification for {symbol}"
        )

        verified_count = 0
        correct_count = 0
        wrong_count = 0

        # Get market data for verification (last 2 days of 30-min data)
        try:
            data_30min = self._get_market_data(ticker_id, '30m', days=2)

            if data_30min.empty:
                logger.warning(
                    f"No 30-minute market data available for {symbol} verification. "
                    f"Market data sync may not have completed yet. "
                    f"Skipping {len(pending_predictions)} pending verifications."
                )
                return {'verified_count': 0, 'correct_count': 0, 'wrong_count': 0}

            # Additional validation: ensure market data is recent enough
            latest_data_time = data_30min.index[-1]
            hours_old = (current_time_utc - latest_data_time).total_seconds() / 3600
            if hours_old > 2:
                logger.warning(
                    f"30-minute market data for {symbol} is {hours_old:.1f} hours old. "
                    f"Waiting for fresher data before verification."
                )
                return {'verified_count': 0, 'correct_count': 0, 'wrong_count': 0}

        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return {'verified_count': 0, 'correct_count': 0, 'wrong_count': 0}

        for prediction in pending_predictions:
            try:
                success, is_correct = self._verify_single_prediction(
                    prediction,
                    data_30min,
                    current_time_utc
                )

                if success:
                    verified_count += 1
                    if is_correct:
                        correct_count += 1
                    else:
                        wrong_count += 1

            except Exception as e:
                logger.error(
                    f"Error verifying intraday prediction {prediction.id} for {symbol}: {e}"
                )
                continue

        logger.info(
            f"Verified {verified_count} intraday predictions for {symbol} "
            f"({correct_count} correct, {wrong_count} wrong)"
        )

        return {
            'verified_count': verified_count,
            'correct_count': correct_count,
            'wrong_count': wrong_count
        }

    def _verify_single_prediction(
        self,
        prediction: IntradayPrediction,
        data_30min,
        current_time_utc: datetime
    ) -> tuple[bool, bool]:
        """
        Verify a single intraday prediction.

        Args:
            prediction: IntradayPrediction object
            data_30min: 30-minute OHLC dataframe
            current_time_utc: Current UTC time

        Returns:
            tuple: (success: bool, is_correct: bool)
        """
        try:
            target_time_utc = prediction.target_timestamp

            # Find candles within the target hour
            target_close_candles = data_30min[
                (data_30min.index >= target_time_utc) &
                (data_30min.index < target_time_utc + timedelta(hours=1))
            ]

            if target_close_candles.empty:
                logger.debug(
                    f"No market data found for target hour {prediction.target_hour} "
                    f"at {target_time_utc}"
                )
                return (False, False)

            # Get the close price at the end of the target hour
            target_close_price = float(target_close_candles['Close'].iloc[-1])
            reference_price = float(prediction.reference_price)

            # Determine actual direction
            actual_direction = 'BULLISH' if target_close_price > reference_price else 'BEARISH'

            # Compare with prediction
            is_correct = prediction.prediction == actual_direction
            actual_result = 'CORRECT' if is_correct else 'WRONG'

            # Update prediction in database
            success = self.intraday_repo.update_verification(
                prediction_id=prediction.id,
                target_close_price=target_close_price,
                actual_result=actual_result,
                verified_at=current_time_utc
            )

            if success:
                logger.info(
                    f"Verified intraday prediction {prediction.id}: "
                    f"target_hour={prediction.target_hour}, "
                    f"predicted={prediction.prediction}, "
                    f"actual={actual_direction}, "
                    f"result={actual_result}, "
                    f"ref_price={reference_price:.2f}, "
                    f"target_close={target_close_price:.2f}"
                )

            return (success, is_correct)

        except Exception as e:
            logger.error(f"Error in _verify_single_prediction: {e}")
            return (False, False)

    def _get_market_data(self, ticker_id: str, interval: str, days: int):
        """
        Get market data from database.

        Args:
            ticker_id: Ticker UUID
            interval: Data interval ('30m', '1h', '1d')
            days: Number of days of data to fetch

        Returns:
            pd.DataFrame: Market data as OHLC dataframe
        """
        import pandas as pd

        try:
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

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return pd.DataFrame()
