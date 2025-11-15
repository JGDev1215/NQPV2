"""Block Prediction repository for NQP application."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from ..supabase_client import get_supabase_client
from ..models.block_prediction import BlockPrediction
from ...config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class BlockPredictionRepository:
    """Repository for Block Prediction CRUD operations."""

    def __init__(self):
        self.client = get_supabase_client()
        self.table = DatabaseConfig.TABLE_BLOCK_PREDICTIONS

    def store_block_prediction(self, prediction: BlockPrediction) -> BlockPrediction:
        """
        Store a single block prediction.

        Args:
            prediction: BlockPrediction object to store

        Returns:
            BlockPrediction: Created prediction with ID
        """
        try:
            pred_data = prediction.to_db_dict()
            response = self.client.table(self.table).insert(pred_data).execute()

            if not response.data:
                raise Exception("Failed to store block prediction")

            created = BlockPrediction.from_dict(response.data[0])
            logger.info(
                f"Stored block prediction for ticker {prediction.ticker_id} "
                f"hour {prediction.get_hour_number():02d}:00"
            )
            return created

        except Exception as e:
            logger.error(f"Error storing block prediction: {e}")
            raise

    def bulk_store_block_predictions(
        self,
        predictions: List[BlockPrediction]
    ) -> int:
        """
        Store multiple block predictions in bulk.

        Args:
            predictions: List of BlockPrediction objects

        Returns:
            int: Number of predictions stored
        """
        try:
            if not predictions:
                return 0

            # Convert to database format
            pred_dicts = [p.to_db_dict() for p in predictions]

            # Insert in batches to avoid hitting size limits
            batch_size = DatabaseConfig.BATCH_INSERT_SIZE
            total_stored = 0

            for i in range(0, len(pred_dicts), batch_size):
                batch = pred_dicts[i:i + batch_size]
                response = self.client.table(self.table).insert(batch).execute()

                count = len(response.data) if response.data else 0
                total_stored += count
                logger.info(f"Stored batch of {count} block predictions")

            logger.info(f"Bulk stored {total_stored} block predictions")
            return total_stored

        except Exception as e:
            logger.error(f"Error bulk storing block predictions: {e}")
            raise

    def get_24h_block_predictions(
        self,
        ticker_id: str
    ) -> List[BlockPrediction]:
        """
        Get all block predictions from today (midnight NY time until now).

        Returns all 24 hourly block predictions generated during today.

        Args:
            ticker_id: Ticker UUID

        Returns:
            List of BlockPrediction objects from today
        """
        try:
            import pytz

            # Get today's date in NY timezone
            ny_tz = pytz.timezone('America/New_York')
            now_ny = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(ny_tz)
            today_start_ny = now_ny.replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_utc = today_start_ny.astimezone(pytz.UTC)

            response = (
                self.client.table(self.table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .gte('hour_start_timestamp', today_start_utc.isoformat())
                .order('hour_start_timestamp', desc=False)
                .execute()
            )

            predictions = [
                BlockPrediction.from_dict(row)
                for row in response.data
            ] if response.data else []

            logger.info(
                f"Retrieved {len(predictions)} block predictions from today (NY timezone) "
                f"for ticker {ticker_id}"
            )
            return predictions

        except Exception as e:
            logger.error(f"Error getting today's block predictions: {e}")
            raise

    def get_block_predictions_by_date(
        self,
        ticker_id: str,
        date: datetime
    ) -> List[BlockPrediction]:
        """
        Get all block predictions for a specific date (NY timezone).

        Args:
            ticker_id: Ticker UUID
            date: Date to get predictions for

        Returns:
            List of BlockPrediction objects
        """
        try:
            import pytz
            ny_tz = pytz.timezone('America/New_York')

            # Get start and end of day in NY timezone
            start_ny = ny_tz.localize(date.replace(hour=0, minute=0, second=0, microsecond=0))
            end_ny = start_ny + timedelta(days=1)

            # Convert to UTC for database query
            start_utc = start_ny.astimezone(pytz.UTC)
            end_utc = end_ny.astimezone(pytz.UTC)

            response = (
                self.client.table(self.table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .gte('hour_start_timestamp', start_utc.isoformat())
                .lt('hour_start_timestamp', end_utc.isoformat())
                .order('hour_start_timestamp', desc=False)
                .execute()
            )

            predictions = [
                BlockPrediction.from_dict(row)
                for row in response.data
            ] if response.data else []

            logger.info(
                f"Retrieved {len(predictions)} block predictions for "
                f"ticker {ticker_id} on {date.date()}"
            )
            return predictions

        except Exception as e:
            logger.error(f"Error getting block predictions by date: {e}")
            raise

    def get_block_prediction_by_hour(
        self,
        ticker_id: str,
        hour_start: datetime
    ) -> Optional[BlockPrediction]:
        """
        Get block prediction for a specific hour.

        Args:
            ticker_id: Ticker UUID
            hour_start: Start of the hour (as UTC timestamp)

        Returns:
            BlockPrediction object or None if not found
        """
        try:
            # Ensure hour_start is at the beginning of an hour
            hour_start_normalized = hour_start.replace(minute=0, second=0, microsecond=0)

            response = (
                self.client.table(self.table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .eq('hour_start_timestamp', hour_start_normalized.isoformat())
                .single()
                .execute()
            )

            if response.data:
                prediction = BlockPrediction.from_dict(response.data)
                logger.info(
                    f"Retrieved block prediction for ticker {ticker_id} "
                    f"at {hour_start_normalized.isoformat()}"
                )
                return prediction
            return None

        except Exception as e:
            logger.error(f"Error getting block prediction by hour: {e}")
            return None

    def get_pending_verifications(self) -> List[BlockPrediction]:
        """
        Get all block predictions pending verification.

        Returns predictions where actual_result is NULL/None.

        Returns:
            List of BlockPrediction objects pending verification
        """
        try:
            response = (
                self.client.table(self.table)
                .select('*')
                .is_('actual_result', 'null')
                .execute()
            )

            predictions = [
                BlockPrediction.from_dict(row)
                for row in response.data
            ] if response.data else []

            logger.info(f"Retrieved {len(predictions)} block predictions pending verification")
            return predictions

        except Exception as e:
            logger.error(f"Error getting pending verifications: {e}")
            raise

    def update_verification(
        self,
        prediction_id: str,
        actual_result: str,
        blocks_6_7_close: float,
        verified_at: datetime
    ) -> bool:
        """
        Update a block prediction with verification results.

        Args:
            prediction_id: Block prediction UUID
            actual_result: CORRECT or WRONG
            blocks_6_7_close: Closing price of block 7
            verified_at: When verification occurred

        Returns:
            bool: True if successful
        """
        try:
            response = (
                self.client.table(self.table)
                .update({
                    'actual_result': actual_result,
                    'blocks_6_7_close': blocks_6_7_close,
                    'verified_at': verified_at.isoformat() if verified_at else None
                })
                .eq('id', prediction_id)
                .execute()
            )

            if response.data:
                logger.info(
                    f"Updated verification for block prediction {prediction_id}: {actual_result}"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Error updating verification: {e}")
            raise

    def get_accuracy_metrics(
        self,
        ticker_id: str,
        hours: int = 24
    ) -> dict:
        """
        Calculate accuracy metrics for block predictions.

        Args:
            ticker_id: Ticker UUID
            hours: Number of hours to analyze (default 24)

        Returns:
            dict with accuracy_percentage, correct_count, wrong_count, total_count
        """
        try:
            # Get recent verified predictions
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            cutoff_iso = cutoff_time.isoformat()

            response = (
                self.client.table(self.table)
                .select('actual_result')
                .eq('ticker_id', ticker_id)
                .gte('verified_at', cutoff_iso)
                .not_('actual_result', 'is', 'null')
                .execute()
            )

            results = [row['actual_result'] for row in response.data] if response.data else []

            total = len(results)
            correct = sum(1 for r in results if r == 'CORRECT')
            wrong = sum(1 for r in results if r == 'WRONG')

            accuracy_pct = (correct / total * 100) if total > 0 else 0

            metrics = {
                'accuracy_percentage': round(accuracy_pct, 2),
                'correct_count': correct,
                'wrong_count': wrong,
                'total_count': total,
                'period_hours': hours,
                'ticker_id': ticker_id
            }

            logger.info(
                f"Accuracy metrics for {ticker_id} (last {hours}h): "
                f"{accuracy_pct:.2f}% ({correct}/{total})"
            )
            return metrics

        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {e}")
            raise

    def delete_old_predictions(self, days: int = 30) -> int:
        """
        Delete block predictions older than specified days.

        Args:
            days: Delete predictions older than this many days

        Returns:
            int: Number of predictions deleted
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            cutoff_iso = cutoff_time.isoformat()

            response = (
                self.client.table(self.table)
                .delete()
                .lt('created_at', cutoff_iso)
                .execute()
            )

            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Deleted {deleted_count} block predictions older than {days} days")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting old predictions: {e}")
            raise
