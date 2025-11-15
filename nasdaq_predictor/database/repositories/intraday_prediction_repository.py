"""Intraday Prediction repository for NQP application."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from ..supabase_client import get_supabase_client
from ..models.intraday_prediction import IntradayPrediction
from ...config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class IntradayPredictionRepository:
    """Repository for Intraday Prediction CRUD operations."""

    def __init__(self):
        self.client = get_supabase_client()
        self.table = DatabaseConfig.TABLE_INTRADAY_PREDICTIONS

    def store_intraday_prediction(self, prediction: IntradayPrediction) -> IntradayPrediction:
        """
        Store a single intraday prediction.

        Args:
            prediction: IntradayPrediction object to store

        Returns:
            IntradayPrediction: Created prediction with ID
        """
        try:
            pred_data = prediction.to_db_dict()
            response = self.client.table(self.table).insert(pred_data).execute()

            if not response.data:
                raise Exception("Failed to store intraday prediction")

            created = IntradayPrediction.from_dict(response.data[0])
            logger.info(
                f"Stored intraday prediction for ticker {prediction.ticker_id} "
                f"target hour {prediction.target_hour}"
            )
            return created

        except Exception as e:
            logger.error(f"Error storing intraday prediction: {e}")
            raise

    def bulk_store_intraday_predictions(
        self,
        predictions: List[IntradayPrediction]
    ) -> int:
        """
        Store multiple intraday predictions in bulk.

        Args:
            predictions: List of IntradayPrediction objects

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
                logger.info(f"Stored batch of {count} intraday predictions")

            logger.info(f"Bulk stored {total_stored} intraday predictions")
            return total_stored

        except Exception as e:
            logger.error(f"Error bulk storing intraday predictions: {e}")
            raise

    def get_24h_intraday_predictions(
        self,
        ticker_id: str
    ) -> List[IntradayPrediction]:
        """
        Get all intraday predictions from midnight NY time today until now.

        Note: This returns predictions made TODAY (from midnight to now in NY timezone),
        not a rolling 24-hour window.

        Args:
            ticker_id: Ticker UUID

        Returns:
            List of IntradayPrediction objects from today
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
                .gte('prediction_made_at', today_start_utc.isoformat())
                .order('prediction_made_at', desc=True)
                .execute()
            )

            predictions = [
                IntradayPrediction.from_dict(row)
                for row in response.data
            ] if response.data else []

            logger.info(
                f"Retrieved {len(predictions)} intraday predictions from today (NY timezone) "
                f"for ticker {ticker_id}"
            )
            return predictions

        except Exception as e:
            logger.error(f"Error getting today's intraday predictions: {e}")
            raise

    def get_intraday_predictions_by_date(
        self,
        ticker_id: str,
        date: datetime
    ) -> List[IntradayPrediction]:
        """
        Get all intraday predictions for a specific date (NY timezone).

        Args:
            ticker_id: Ticker UUID
            date: Date to get predictions for

        Returns:
            List of IntradayPrediction objects
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
                .gte('prediction_made_at', start_utc.isoformat())
                .lt('prediction_made_at', end_utc.isoformat())
                .order('prediction_made_at', desc=False)
                .execute()
            )

            predictions = [
                IntradayPrediction.from_dict(row)
                for row in response.data
            ] if response.data else []

            logger.info(
                f"Retrieved {len(predictions)} intraday predictions for "
                f"ticker {ticker_id} on {date.date()}"
            )
            return predictions

        except Exception as e:
            logger.error(f"Error getting intraday predictions by date: {e}")
            raise

    def get_intraday_predictions_by_hour(
        self,
        ticker_id: str,
        hour: int,
        date: datetime
    ) -> List[IntradayPrediction]:
        """
        Get intraday predictions for a specific hour on a date.

        Args:
            ticker_id: Ticker UUID
            hour: Target hour (0-23)
            date: Date to get predictions for

        Returns:
            List of IntradayPrediction objects
        """
        try:
            import pytz
            ny_tz = pytz.timezone('America/New_York')

            # Get start and end of day in NY timezone
            start_ny = ny_tz.localize(date.replace(hour=0, minute=0, second=0, microsecond=0))
            end_ny = start_ny + timedelta(days=1)

            # Convert to UTC
            start_utc = start_ny.astimezone(pytz.UTC)
            end_utc = end_ny.astimezone(pytz.UTC)

            response = (
                self.client.table(self.table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .eq('target_hour', hour)
                .gte('prediction_made_at', start_utc.isoformat())
                .lt('prediction_made_at', end_utc.isoformat())
                .order('prediction_made_at', desc=False)
                .execute()
            )

            predictions = [
                IntradayPrediction.from_dict(row)
                for row in response.data
            ] if response.data else []

            logger.info(
                f"Retrieved {len(predictions)} intraday predictions for "
                f"ticker {ticker_id} hour {hour} on {date.date()}"
            )
            return predictions

        except Exception as e:
            logger.error(f"Error getting intraday predictions by hour: {e}")
            raise

    def get_daily_intraday_accuracy(self, ticker_id: str) -> dict:
        """
        Calculate intraday prediction accuracy for today only (NY timezone).

        Args:
            ticker_id: Ticker UUID

        Returns:
            Dictionary with today's accuracy metrics
        """
        try:
            import pytz

            # Get today's date in NY timezone
            ny_tz = pytz.timezone('America/New_York')
            now_ny = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(ny_tz)
            today_start_ny = now_ny.replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_utc = today_start_ny.astimezone(pytz.UTC)

            # Get predictions from today (in NY timezone)
            response = (
                self.client.table(self.table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .gte('prediction_made_at', today_start_utc.isoformat())
                .order('prediction_made_at', desc=False)
                .execute()
            )

            predictions = [
                IntradayPrediction.from_dict(row)
                for row in response.data
            ] if response.data else []

            if not predictions:
                return {
                    'total': 0,
                    'correct': 0,
                    'wrong': 0,
                    'pending': 0,
                    'accuracy_rate': 0.0,
                    'date_ny': today_start_ny.strftime('%Y-%m-%d')
                }

            # Calculate accuracy from verified predictions only
            verified = [
                p for p in predictions
                if p.actual_result in ['CORRECT', 'WRONG']
            ]
            correct = sum(1 for p in verified if p.actual_result == 'CORRECT')
            wrong = sum(1 for p in verified if p.actual_result == 'WRONG')
            pending = len(predictions) - len(verified)

            accuracy_rate = (correct / len(verified) * 100) if verified else 0.0

            result = {
                'total': len(predictions),
                'correct': correct,
                'wrong': wrong,
                'pending': pending,
                'accuracy_rate': round(accuracy_rate, 1),
                'date_ny': today_start_ny.strftime('%Y-%m-%d')
            }

            logger.info(
                f"Daily intraday accuracy for ticker {ticker_id}: "
                f"{correct}/{len(verified)} correct ({accuracy_rate:.1f}%)"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating daily intraday accuracy: {e}")
            raise

    def get_latest_prediction_by_hour(
        self,
        ticker_id: str,
        target_hour: int
    ) -> Optional[IntradayPrediction]:
        """
        Get the most recent prediction for a specific target hour.

        Args:
            ticker_id: Ticker UUID
            target_hour: Target hour (0-23)

        Returns:
            IntradayPrediction or None
        """
        try:
            response = (
                self.client.table(self.table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .eq('target_hour', target_hour)
                .order('prediction_made_at', desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                return None

            return IntradayPrediction.from_dict(response.data[0])

        except Exception as e:
            logger.error(f"Error getting latest prediction by hour: {e}")
            raise

    def update_verification(
        self,
        prediction_id: str,
        target_close_price: float,
        actual_result: str,
        verified_at: Optional[datetime] = None
    ) -> bool:
        """
        Update verification data for a prediction.

        Args:
            prediction_id: Prediction UUID
            target_close_price: Actual close price at target hour
            actual_result: Result (CORRECT, WRONG)
            verified_at: Verification timestamp (defaults to now)

        Returns:
            bool: True if update successful
        """
        try:
            if verified_at is None:
                verified_at = datetime.utcnow()

            update_data = {
                'target_close_price': target_close_price,
                'actual_result': actual_result,
                'verified_at': verified_at.isoformat()
            }

            response = (
                self.client.table(self.table)
                .update(update_data)
                .eq('id', prediction_id)
                .execute()
            )

            success = bool(response.data)
            if success:
                logger.info(
                    f"Updated verification for prediction {prediction_id}: {actual_result}"
                )
            return success

        except Exception as e:
            logger.error(f"Error updating verification: {e}")
            raise

    def delete_old_predictions(self, days: int = 90) -> int:
        """
        Delete predictions older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            int: Number of deleted predictions
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            response = (
                self.client.table(self.table)
                .delete()
                .lt('created_at', cutoff_time.isoformat())
                .execute()
            )

            count = len(response.data) if response.data else 0
            logger.info(f"Deleted {count} old intraday predictions (older than {days} days)")
            return count

        except Exception as e:
            logger.error(f"Error deleting old predictions: {e}")
            raise
