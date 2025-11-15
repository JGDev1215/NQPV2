"""
Block Verification Service for 7-Block Framework.

Service layer for verifying block predictions after hour completion.
Compares predicted direction against actual block 6-7 movement.

Implements dependency injection pattern for external dependencies.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from ..data.fetcher import YahooFinanceDataFetcher
from ..database.repositories.block_prediction_repository import BlockPredictionRepository
from ..database.models.block_prediction import BlockPrediction
from ..analysis.block_segmentation import BlockSegmentation

logger = logging.getLogger(__name__)


class BlockVerificationService:
    """
    Service for verifying 7-block predictions after hour completion.

    Verifies that a prediction made at the 5/7 point was accurate by:
    1. Fetching actual blocks 6-7 data (after hour completes)
    2. Determining actual direction (UP, DOWN, NEUTRAL)
    3. Comparing to predicted direction
    4. Storing verification results with accuracy metrics
    """

    def __init__(
        self,
        fetcher: YahooFinanceDataFetcher,
        block_prediction_repo: BlockPredictionRepository
    ):
        """
        Initialize BlockVerificationService with injected dependencies.

        Args:
            fetcher: YahooFinanceDataFetcher for market data retrieval
            block_prediction_repo: BlockPredictionRepository for storing verification
        """
        self.fetcher = fetcher
        self.block_prediction_repo = block_prediction_repo
        logger.debug("BlockVerificationService initialized")

    def verify_block_prediction(
        self,
        block_prediction: BlockPrediction,
        actual_bars: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[BlockPrediction]:
        """
        Verify a block prediction after the hour completes.

        This is the main verification entry point. It:
        1. Gets the completed block prediction
        2. Fetches actual blocks 6-7 OHLC data
        3. Determines actual direction
        4. Compares to predicted direction
        5. Stores verification results

        Args:
            block_prediction: BlockPrediction object to verify
            actual_bars: Optional list of OHLC bars for blocks 6-7. If None, will be fetched.

        Returns:
            Updated BlockPrediction object with verification results, or None if verification fails

        Raises:
            ValueError: If inputs are invalid
        """
        try:
            logger.info(
                f"Verifying block prediction for {block_prediction.ticker_id} "
                f"at {block_prediction.hour_start_timestamp.isoformat()}"
            )

            # Step 1: Validate that prediction is ready for verification
            # (hour should be complete: prediction_timestamp + time for blocks 6-7)
            if not self._is_ready_for_verification(block_prediction):
                logger.warning(f"Prediction not ready for verification yet")
                return None

            # Step 2: Get actual blocks 6-7 data
            if actual_bars is None:
                actual_bars = self._fetch_blocks_6_7_bars(
                    ticker=block_prediction.ticker_id,
                    hour_start=block_prediction.hour_start_timestamp
                )

            if not actual_bars:
                logger.warning(
                    f"No bars available for verification of "
                    f"{block_prediction.ticker_id} at {block_prediction.hour_start_timestamp}"
                )
                return None

            logger.debug(f"Fetched {len(actual_bars)} bars for blocks 6-7")

            # Step 3: Determine actual direction
            actual_direction, actual_strength = self._determine_actual_direction(
                actual_bars=actual_bars,
                reference_price=block_prediction.reference_levels.get('opening_price'),
                volatility=block_prediction.volatility
            )
            logger.info(
                f"Actual direction: {actual_direction} ({actual_strength}) "
                f"vs Predicted: {block_prediction.prediction}"
            )

            # Step 4: Compare and determine if prediction was correct
            is_correct = (actual_direction == block_prediction.prediction)
            logger.debug(f"Prediction accuracy: {'CORRECT' if is_correct else 'INCORRECT'}")

            # Step 5: Get closing price for blocks 6-7
            closing_price = float(actual_bars[-1]['close']) if actual_bars else None

            # Step 6: Update BlockPrediction with verification results
            updated_prediction = self._update_verification_results(
                block_prediction=block_prediction,
                actual_direction=actual_direction,
                actual_strength=actual_strength,
                actual_close=closing_price,
                is_correct=is_correct
            )

            # Step 7: Store in database
            stored_prediction = self.block_prediction_repo.update_verification(
                prediction_id=block_prediction.id,
                actual_result=actual_direction,
                verified_at=datetime.utcnow(),
                is_correct=is_correct
            )
            logger.info(f"Stored verification results for {block_prediction.ticker_id}")

            return stored_prediction

        except Exception as e:
            logger.error(
                f"Error verifying block prediction: {e}",
                exc_info=True
            )
            return None

    def verify_pending_predictions(
        self,
        limit: int = 100
    ) -> Dict[str, int]:
        """
        Batch verify all pending block predictions.

        Verifies all predictions where:
        - verified_at is NULL (not yet verified)
        - prediction_timestamp is in the past (hour complete)

        Args:
            limit: Maximum number of predictions to verify (default 100)

        Returns:
            Dictionary with stats: {verified: int, correct: int, incorrect: int, failed: int}
        """
        logger.info(f"Verifying pending predictions (limit={limit})")

        # Get pending predictions
        pending = self.block_prediction_repo.get_pending_verifications(limit=limit)
        logger.debug(f"Found {len(pending)} pending predictions")

        stats = {
            'verified': 0,
            'correct': 0,
            'incorrect': 0,
            'failed': 0
        }

        for prediction in pending:
            result = self.verify_block_prediction(prediction)
            if result:
                stats['verified'] += 1
                if result.is_correct:
                    stats['correct'] += 1
                else:
                    stats['incorrect'] += 1
            else:
                stats['failed'] += 1

        logger.info(
            f"Verification batch complete: {stats['verified']} verified, "
            f"{stats['correct']} correct, {stats['incorrect']} incorrect, "
            f"{stats['failed']} failed"
        )

        return stats

    def get_verification_accuracy(
        self,
        ticker: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get accuracy metrics for a ticker on a specific date.

        Args:
            ticker: Asset ticker symbol
            date: Date to calculate accuracy for (default today)

        Returns:
            Dictionary with accuracy metrics:
            {
                'total_predictions': int,
                'correct': int,
                'incorrect': int,
                'accuracy_pct': float,
                'avg_confidence': float
            }
        """
        if date is None:
            date = datetime.utcnow().date()

        metrics = self.block_prediction_repo.get_accuracy_metrics(
            ticker_id=ticker,
            date=date
        )
        logger.info(f"Accuracy for {ticker} on {date}: {metrics['accuracy_pct']:.1f}%")

        return metrics

    @staticmethod
    def _is_ready_for_verification(block_prediction: BlockPrediction) -> bool:
        """
        Check if a prediction is ready for verification.

        Ready means the hour has completed and blocks 6-7 time has passed.
        This is approximately 1 hour after the hour_start_timestamp.

        Args:
            block_prediction: BlockPrediction to check

        Returns:
            True if ready for verification, False otherwise
        """
        # Verification can happen after the prediction timestamp + time for blocks 6-7
        # Blocks 6-7 = 2/7 of hour = ~17.14 minutes
        # So earliest verification time = prediction_timestamp + ~17 minutes
        hour_end = block_prediction.hour_start_timestamp + timedelta(hours=1)
        now = datetime.utcnow()

        # Allow some buffer (5 minutes) for data availability
        earliest_verification = hour_end + timedelta(minutes=5)

        is_ready = now >= earliest_verification

        if not is_ready:
            minutes_until = int((earliest_verification - now).total_seconds() / 60)
            logger.debug(
                f"Verification ready in {minutes_until} minutes "
                f"(at {earliest_verification.isoformat()})"
            )

        return is_ready

    @staticmethod
    def _fetch_blocks_6_7_bars(
        ticker: str,
        hour_start: datetime,
        fetcher: Optional[YahooFinanceDataFetcher] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLC bars for blocks 6-7 of an hour.

        Args:
            ticker: Asset ticker symbol
            hour_start: Start time of the hour
            fetcher: Optional YahooFinanceDataFetcher (for testing)

        Returns:
            List of OHLC bars for blocks 6-7
        """
        hour_end = hour_start + timedelta(hours=1)

        try:
            # For now, return empty list (would need fetcher injected)
            # This is a placeholder for actual implementation
            logger.debug(f"Would fetch blocks 6-7 for {ticker} from {hour_end}")
            return []

        except Exception as e:
            logger.error(f"Error fetching blocks 6-7 bars: {e}")
            return []

    @staticmethod
    def _determine_actual_direction(
        actual_bars: List[Dict[str, Any]],
        reference_price: float,
        volatility: float
    ) -> Tuple[str, str]:
        """
        Determine actual direction from blocks 6-7 OHLC data.

        Direction is determined by final close relative to opening price (reference).

        Args:
            actual_bars: List of OHLC bars for blocks 6-7
            reference_price: Opening price (equilibrium reference)
            volatility: Hour volatility for deviation calculation

        Returns:
            Tuple of (direction: UP/DOWN/NEUTRAL, strength: weak/moderate/strong)
        """
        if not actual_bars:
            return 'NEUTRAL', 'weak'

        closing_price = float(actual_bars[-1]['close'])
        deviation = (closing_price - reference_price) / volatility if volatility > 0 else 0

        # Classify direction
        if abs(deviation) < 0.5:
            return 'NEUTRAL', 'weak'
        elif deviation > 0:
            if abs(deviation) >= 2.0:
                return 'UP', 'strong'
            else:
                return 'UP', 'moderate'
        else:  # deviation < 0
            if abs(deviation) >= 2.0:
                return 'DOWN', 'strong'
            else:
                return 'DOWN', 'moderate'

    @staticmethod
    def _update_verification_results(
        block_prediction: BlockPrediction,
        actual_direction: str,
        actual_strength: str,
        actual_close: Optional[float],
        is_correct: bool
    ) -> BlockPrediction:
        """
        Update BlockPrediction with verification results.

        Args:
            block_prediction: Original BlockPrediction
            actual_direction: Actual direction (UP/DOWN/NEUTRAL)
            actual_strength: Actual strength (weak/moderate/strong)
            actual_close: Actual closing price
            is_correct: Whether prediction was correct

        Returns:
            Updated BlockPrediction object
        """
        # Create updated copy with verification data
        block_prediction.blocks_6_7_close = actual_close
        block_prediction.actual_result = actual_direction
        block_prediction.is_correct = is_correct
        block_prediction.verified_at = datetime.utcnow()

        logger.debug(
            f"Updated prediction with verification: "
            f"actual={actual_direction} ({actual_strength}), "
            f"correct={is_correct}"
        )

        return block_prediction

    def get_24h_verification_summary(
        self,
        ticker: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get a complete 24-hour verification summary.

        Provides hourly breakdown of predictions and actual results.

        Args:
            ticker: Asset ticker symbol
            date: Date to get summary for (default today)

        Returns:
            Dictionary with 24-hour hourly results
        """
        if date is None:
            date = datetime.utcnow().date()

        predictions = self.block_prediction_repo.get_24h_block_predictions(
            ticker_id=ticker,
            date=datetime.combine(date, datetime.min.time())
        )

        summary = {
            'ticker': ticker,
            'date': date.isoformat(),
            'total_predictions': len(predictions),
            'verified': sum(1 for p in predictions if p.verified_at),
            'correct': sum(1 for p in predictions if p.is_correct),
            'incorrect': sum(1 for p in predictions if p.verified_at and not p.is_correct),
            'hourly_results': {}
        }

        # Build hourly breakdown
        for pred in predictions:
            hour = pred.hour_start_timestamp.hour
            summary['hourly_results'][hour] = {
                'predicted': pred.prediction,
                'actual': pred.actual_result,
                'confidence': pred.confidence,
                'correct': pred.is_correct,
                'verified': pred.verified_at is not None
            }

        if summary['verified'] > 0:
            summary['accuracy_pct'] = (summary['correct'] / summary['verified']) * 100
        else:
            summary['accuracy_pct'] = None

        logger.info(
            f"24h summary for {ticker} on {date}: "
            f"{summary['correct']}/{summary['verified']} correct "
            f"({summary['accuracy_pct']:.1f}%)"
        )

        return summary
