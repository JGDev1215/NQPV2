"""
Prediction Verification Service for NQP application.

This service verifies predictions by comparing predicted direction
with actual price movements after 15 minutes.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..database.repositories.ticker_repository import TickerRepository
from ..database.repositories.market_data_repository import MarketDataRepository
from ..database.repositories.prediction_repository import PredictionRepository
from ..database.models.prediction import Prediction

logger = logging.getLogger(__name__)


class PredictionVerificationService:
    """Service to verify prediction accuracy against actual market movements.

    Implements full dependency injection for all repository dependencies.
    """

    def __init__(
        self,
        ticker_repo: TickerRepository,
        market_data_repo: MarketDataRepository,
        prediction_repo: PredictionRepository,
        neutral_threshold_percent: float = 0.1
    ):
        """Initialize PredictionVerificationService with injected dependencies.

        Args:
            ticker_repo: TickerRepository for ticker management
            market_data_repo: MarketDataRepository for market data access
            prediction_repo: PredictionRepository for prediction data access
            neutral_threshold_percent: Threshold for neutral vs directional price change (default: 0.1%)
        """
        self.ticker_repo = ticker_repo
        self.market_data_repo = market_data_repo
        self.prediction_repo = prediction_repo
        self.neutral_threshold_percent = neutral_threshold_percent

    def verify_pending_predictions(self) -> Dict[str, Any]:
        """
        Verify all pending predictions that are older than 15 minutes.

        Returns:
            Dict[str, Any]: Summary of verification results
        """
        logger.info("Starting prediction verification...")

        # Find predictions older than 15 minutes with NULL actual_result
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)

        tickers = self.ticker_repo.get_enabled_tickers()

        results = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'total_verified': 0,
            'correct': 0,
            'wrong': 0,
            'errors': []
        }

        for ticker in tickers:
            try:
                # Get unverified predictions for this ticker
                verified_count = self._verify_ticker_predictions(ticker.id, ticker.symbol, cutoff_time)
                results['total_verified'] += verified_count

            except Exception as e:
                logger.error(f"Error verifying predictions for {ticker.symbol}: {e}")
                results['errors'].append({
                    'ticker': ticker.symbol,
                    'error': str(e)
                })

        # Get counts of correct/wrong (across all tickers)
        # This is a summary - actual counts are calculated per prediction
        logger.info(f"Verification completed: {results['total_verified']} predictions verified")

        return results

    def _verify_ticker_predictions(
        self,
        ticker_id: str,
        symbol: str,
        cutoff_time: datetime
    ) -> int:
        """
        Verify predictions for a specific ticker.

        Args:
            ticker_id: Ticker UUID
            symbol: Ticker symbol
            cutoff_time: Only verify predictions older than this time

        Returns:
            int: Number of predictions verified
        """
        # Get predictions that need verification
        # (older than cutoff and actual_result is NULL)
        predictions = self._get_unverified_predictions(ticker_id, cutoff_time)

        if not predictions:
            logger.debug(f"No unverified predictions for {symbol}")
            return 0

        logger.info(f"Found {len(predictions)} unverified predictions for {symbol}")

        verified_count = 0

        for prediction in predictions:
            try:
                success = self.verify_single_prediction(prediction.id, ticker_id, symbol)
                if success:
                    verified_count += 1

            except Exception as e:
                logger.error(f"Error verifying prediction {prediction.id} for {symbol}: {e}")
                continue

        return verified_count

    def _get_unverified_predictions(
        self,
        ticker_id: str,
        cutoff_time: datetime
    ) -> List[Prediction]:
        """
        Get predictions that need verification.

        Args:
            ticker_id: Ticker UUID
            cutoff_time: Only get predictions older than this time

        Returns:
            List[Prediction]: List of unverified predictions
        """
        try:
            # Query predictions where:
            # - ticker_id matches
            # - timestamp < cutoff_time (older than 15 min)
            # - actual_result IS NULL (not yet verified)
            response = (
                self.prediction_repo.client
                .table(self.prediction_repo.predictions_table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .lt('timestamp', cutoff_time.isoformat())
                .is_('actual_result', 'null')
                .order('timestamp', desc=False)
                .limit(100)  # Verify in batches
                .execute()
            )

            predictions = [Prediction.from_dict(row) for row in response.data] if response.data else []

            return predictions

        except Exception as e:
            logger.error(f"Error querying unverified predictions: {e}")
            return []

    def verify_single_prediction(
        self,
        prediction_id: str,
        ticker_id: str,
        symbol: str
    ) -> bool:
        """
        Verify a specific prediction by comparing predicted vs actual price movement.

        Args:
            prediction_id: Prediction UUID
            ticker_id: Ticker UUID
            symbol: Ticker symbol

        Returns:
            bool: True if verification succeeded, False otherwise
        """
        try:
            # Get the prediction
            response = (
                self.prediction_repo.client
                .table(self.prediction_repo.predictions_table)
                .select('*')
                .eq('id', prediction_id)
                .single()
                .execute()
            )

            if not response.data:
                logger.warning(f"Prediction {prediction_id} not found")
                return False

            prediction = Prediction.from_dict(response.data)

            # Get baseline price from metadata
            if not prediction.metadata or 'baseline_price' not in prediction.metadata:
                logger.warning(f"Prediction {prediction_id} has no baseline_price, skipping verification")
                return False

            baseline_price = float(prediction.metadata['baseline_price'])
            prediction_timestamp = prediction.timestamp

            # Get price 15 minutes later
            verification_time = prediction_timestamp + timedelta(minutes=15)

            # Find the closest market data to verification_time
            # Look for data within ±5 minutes of verification time
            start_window = verification_time - timedelta(minutes=5)
            end_window = verification_time + timedelta(minutes=5)

            verification_data = self.market_data_repo.get_historical_data(
                ticker_id=ticker_id,
                start=start_window,
                end=end_window,
                interval='1m'
            )

            if not verification_data:
                logger.warning(
                    f"No market data found for verification of {symbol} "
                    f"prediction at {verification_time}, will retry later"
                )
                return False

            # Get the closest data point to verification_time
            closest_data = min(
                verification_data,
                key=lambda x: abs((x.timestamp - verification_time).total_seconds())
            )

            verification_price = float(closest_data.close)

            # Calculate price change
            price_change = verification_price - baseline_price
            price_change_percent = (price_change / baseline_price) * 100

            # Determine if prediction was correct
            actual_result = self._evaluate_prediction(
                prediction.prediction,
                price_change_percent
            )

            # Update prediction with verification results
            update_data = {
                'actual_result': actual_result,
                'actual_price_change': price_change,
                'verification_timestamp': datetime.utcnow().isoformat(),
                'metadata': {
                    **prediction.metadata,
                    'verification_price': verification_price,
                    'verification_data_timestamp': closest_data.timestamp.isoformat(),
                    'price_change_percent': price_change_percent
                }
            }

            self.prediction_repo.client.table(self.prediction_repo.predictions_table).update(
                update_data
            ).eq('id', prediction_id).execute()

            logger.info(
                f"Verified prediction {prediction_id} for {symbol}: "
                f"{prediction.prediction} → {actual_result} "
                f"(price change: {price_change_percent:+.2f}%)"
            )

            return True

        except Exception as e:
            logger.error(f"Error verifying prediction {prediction_id}: {e}", exc_info=True)
            return False

    def _evaluate_prediction(
        self,
        prediction_type: str,
        price_change_percent: float
    ) -> str:
        """
        Evaluate if prediction was correct based on actual price movement.

        Args:
            prediction_type: BULLISH, BEARISH, or NEUTRAL
            price_change_percent: Actual price change percentage

        Returns:
            str: 'CORRECT', 'WRONG', or 'NEUTRAL_RANGE'
        """
        # Check if price movement was within neutral range
        if abs(price_change_percent) <= self.neutral_threshold_percent:
            # Price barely moved
            return 'CORRECT' if prediction_type == 'NEUTRAL' else 'NEUTRAL_RANGE'

        # Price moved significantly
        if prediction_type == 'BULLISH':
            return 'CORRECT' if price_change_percent > 0 else 'WRONG'
        elif prediction_type == 'BEARISH':
            return 'CORRECT' if price_change_percent < 0 else 'WRONG'
        elif prediction_type == 'NEUTRAL':
            # Predicted neutral but price moved significantly
            return 'WRONG'
        else:
            logger.warning(f"Unknown prediction type: {prediction_type}")
            return 'WRONG'

    def get_verification_status(self, ticker_id: str) -> Dict[str, Any]:
        """
        Get verification status for a ticker.

        Args:
            ticker_id: Ticker UUID

        Returns:
            Dict with verification statistics
        """
        try:
            # Get all predictions for this ticker
            response = (
                self.prediction_repo.client
                .table(self.prediction_repo.predictions_table)
                .select('actual_result, timestamp')
                .eq('ticker_id', ticker_id)
                .execute()
            )

            if not response.data:
                return {
                    'total_predictions': 0,
                    'verified': 0,
                    'pending': 0,
                    'verification_rate': 0.0
                }

            total = len(response.data)
            verified = sum(1 for p in response.data if p.get('actual_result') is not None)
            pending = total - verified

            return {
                'total_predictions': total,
                'verified': verified,
                'pending': pending,
                'verification_rate': round((verified / total * 100), 2) if total > 0 else 0.0
            }

        except Exception as e:
            logger.error(f"Error getting verification status: {e}")
            return {
                'error': str(e)
            }
