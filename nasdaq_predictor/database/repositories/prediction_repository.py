"""Prediction repository for NQP application."""

import logging
from typing import List, Optional
from datetime import datetime

from ..supabase_client import get_supabase_client
from ..models.prediction import Prediction
from ..models.signal import Signal
from ...config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class PredictionRepository:
    """Repository for Prediction and Signal CRUD operations."""

    def __init__(self):
        self.client = get_supabase_client()
        self.predictions_table = DatabaseConfig.TABLE_PREDICTIONS
        self.signals_table = DatabaseConfig.TABLE_SIGNALS

    def store_prediction(self, prediction: Prediction) -> Prediction:
        """Store a new prediction."""
        try:
            pred_data = prediction.to_db_dict()
            response = self.client.table(self.predictions_table).insert(pred_data).execute()

            if not response.data:
                raise Exception("Failed to store prediction")

            created = Prediction.from_dict(response.data[0])
            logger.info(f"Stored prediction for ticker {prediction.ticker_id}")
            return created

        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            raise

    def store_signals(self, prediction_id: str, signals: List[Signal]) -> int:
        """Store signals for a prediction in bulk."""
        try:
            if not signals:
                return 0

            signal_dicts = [s.to_db_dict() for s in signals]
            for sig_dict in signal_dicts:
                sig_dict['prediction_id'] = prediction_id

            response = self.client.table(self.signals_table).insert(signal_dicts).execute()

            count = len(response.data) if response.data else 0
            logger.info(f"Stored {count} signals for prediction {prediction_id}")
            return count

        except Exception as e:
            logger.error(f"Error storing signals: {e}")
            raise

    def get_latest_prediction(self, ticker_id: str) -> Optional[Prediction]:
        """Get the most recent prediction for a ticker."""
        try:
            response = (
                self.client.table(self.predictions_table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .order('timestamp', desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                return None

            return Prediction.from_dict(response.data[0])

        except Exception as e:
            logger.error(f"Error getting latest prediction: {e}")
            raise

    def get_predictions_paginated(
        self,
        ticker_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Prediction], int]:
        """
        Get paginated predictions with optional date filtering.

        Args:
            ticker_id: Ticker UUID
            start: Start datetime (optional)
            end: End datetime (optional)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Tuple of (predictions_list, total_count)
        """
        try:
            # Build query
            query = (
                self.client.table(self.predictions_table)
                .select('*', count='exact')
                .eq('ticker_id', ticker_id)
            )

            # Apply date filters if provided
            if start:
                query = query.gte('timestamp', start.isoformat())
            if end:
                query = query.lte('timestamp', end.isoformat())

            # Apply pagination and ordering
            response = (
                query
                .order('timestamp', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            predictions = [Prediction.from_dict(row) for row in response.data] if response.data else []
            total_count = response.count if hasattr(response, 'count') else len(predictions)

            logger.info(
                f"Retrieved {len(predictions)} of {total_count} predictions for ticker {ticker_id}"
            )

            return predictions, total_count

        except Exception as e:
            logger.error(f"Error getting paginated predictions: {e}")
            raise

    def get_prediction_accuracy(
        self,
        ticker_id: str,
        days: int = 30
    ) -> dict:
        """
        Calculate prediction accuracy statistics for the specified period.

        Args:
            ticker_id: Ticker UUID
            days: Number of days to analyze

        Returns:
            Dictionary with accuracy metrics
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # Get predictions from the specified period
            response = (
                self.client.table(self.predictions_table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .gte('timestamp', cutoff_time.isoformat())
                .order('timestamp', desc=False)
                .execute()
            )

            predictions = [Prediction.from_dict(row) for row in response.data] if response.data else []

            if not predictions:
                return {
                    'total_predictions': 0,
                    'accuracy_rate': 0.0,
                    'bullish_predictions': 0,
                    'bearish_predictions': 0,
                    'neutral_predictions': 0,
                    'avg_confidence': 0.0,
                    'period_days': days
                }

            # Calculate statistics
            total = len(predictions)
            bullish_count = sum(1 for p in predictions if p.prediction == 'BULLISH')
            bearish_count = sum(1 for p in predictions if p.prediction == 'BEARISH')
            neutral_count = sum(1 for p in predictions if p.prediction == 'NEUTRAL')
            avg_confidence = sum(p.confidence for p in predictions) / total

            # Calculate accuracy from verified predictions
            verified_predictions = [p for p in predictions if p.actual_result is not None]

            if verified_predictions:
                correct_count = sum(1 for p in verified_predictions if p.actual_result == 'CORRECT')
                accuracy_rate = (correct_count / len(verified_predictions)) * 100

                # Calculate accuracy by prediction type
                bullish_verified = [p for p in verified_predictions if p.prediction == 'BULLISH']
                bearish_verified = [p for p in verified_predictions if p.prediction == 'BEARISH']
                neutral_verified = [p for p in verified_predictions if p.prediction == 'NEUTRAL']

                bullish_accuracy = (
                    sum(1 for p in bullish_verified if p.actual_result == 'CORRECT') / len(bullish_verified) * 100
                    if bullish_verified else 0.0
                )
                bearish_accuracy = (
                    sum(1 for p in bearish_verified if p.actual_result == 'CORRECT') / len(bearish_verified) * 100
                    if bearish_verified else 0.0
                )
                neutral_accuracy = (
                    sum(1 for p in neutral_verified if p.actual_result == 'CORRECT') / len(neutral_verified) * 100
                    if neutral_verified else 0.0
                )
            else:
                accuracy_rate = 0.0
                bullish_accuracy = 0.0
                bearish_accuracy = 0.0
                neutral_accuracy = 0.0

            result = {
                'total_predictions': total,
                'verified_predictions': len(verified_predictions) if verified_predictions else 0,
                'pending_verification': total - (len(verified_predictions) if verified_predictions else 0),
                'accuracy_rate': round(accuracy_rate, 2),
                'bullish_predictions': bullish_count,
                'bearish_predictions': bearish_count,
                'neutral_predictions': neutral_count,
                'bullish_accuracy': round(bullish_accuracy, 2),
                'bearish_accuracy': round(bearish_accuracy, 2),
                'neutral_accuracy': round(neutral_accuracy, 2),
                'avg_confidence': round(avg_confidence, 2),
                'period_days': days,
                'start_date': cutoff_time.isoformat(),
                'end_date': datetime.utcnow().isoformat()
            }

            logger.info(f"Calculated accuracy metrics for ticker {ticker_id}: {total} predictions over {days} days")

            return result

        except Exception as e:
            logger.error(f"Error calculating prediction accuracy: {e}")
            raise

    def get_signals_by_prediction(
        self,
        prediction_id: str
    ) -> List[Signal]:
        """
        Get all signals for a specific prediction.

        Args:
            prediction_id: Prediction UUID

        Returns:
            List of Signal objects
        """
        try:
            response = (
                self.client.table(self.signals_table)
                .select('*')
                .eq('prediction_id', prediction_id)
                .order('weight', desc=True)
                .execute()
            )

            signals = [Signal.from_dict(row) for row in response.data] if response.data else []
            logger.info(f"Retrieved {len(signals)} signals for prediction {prediction_id}")

            return signals

        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            raise

    def get_signal_analysis(
        self,
        ticker_id: str,
        days: int = 30
    ) -> dict:
        """
        Analyze signal performance by reference level for the specified period.

        Args:
            ticker_id: Ticker UUID
            days: Number of days to analyze

        Returns:
            Dictionary with signal analysis by reference level
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # Get predictions from the period
            predictions_response = (
                self.client.table(self.predictions_table)
                .select('id, timestamp')
                .eq('ticker_id', ticker_id)
                .gte('timestamp', cutoff_time.isoformat())
                .execute()
            )

            if not predictions_response.data:
                return {
                    'period_days': days,
                    'total_signals': 0,
                    'by_reference_level': {}
                }

            prediction_ids = [p['id'] for p in predictions_response.data]

            # Get all signals for these predictions
            signals_response = (
                self.client.table(self.signals_table)
                .select('*')
                .in_('prediction_id', prediction_ids)
                .execute()
            )

            signals = [Signal.from_dict(row) for row in signals_response.data] if signals_response.data else []

            # Group by reference level
            by_level = {}
            for signal in signals:
                level = signal.reference_level_name
                if level not in by_level:
                    by_level[level] = {
                        'count': 0,
                        'bullish_count': 0,
                        'bearish_count': 0,
                        'avg_weight': 0.0,
                        'avg_distance_pct': 0.0
                    }

                by_level[level]['count'] += 1
                if signal.signal > 0:
                    by_level[level]['bullish_count'] += 1
                elif signal.signal < 0:
                    by_level[level]['bearish_count'] += 1

            # Calculate averages
            for level, data in by_level.items():
                level_signals = [s for s in signals if s.reference_level_name == level]
                data['avg_weight'] = round(sum(s.weight for s in level_signals) / len(level_signals), 2)
                data['avg_distance_pct'] = round(
                    sum(abs(s.distance_percentage) for s in level_signals) / len(level_signals), 2
                )

            result = {
                'period_days': days,
                'total_signals': len(signals),
                'by_reference_level': by_level,
                'start_date': cutoff_time.isoformat(),
                'end_date': datetime.utcnow().isoformat()
            }

            logger.info(f"Analyzed {len(signals)} signals for ticker {ticker_id} over {days} days")

            return result

        except Exception as e:
            logger.error(f"Error analyzing signals: {e}")
            raise

    def get_verified_predictions_24h(self, ticker_id: str) -> List[Prediction]:
        """
        Get verified predictions from the last 24 hours.

        Args:
            ticker_id: Ticker UUID

        Returns:
            List of Prediction objects with verification data
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            response = (
                self.client.table(self.predictions_table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .gte('timestamp', cutoff_time.isoformat())
                .order('timestamp', desc=True)
                .execute()
            )

            predictions = [Prediction.from_dict(row) for row in response.data] if response.data else []

            logger.info(f"Retrieved {len(predictions)} predictions from last 24h for ticker {ticker_id}")

            return predictions

        except Exception as e:
            logger.error(f"Error getting 24h predictions: {e}")
            raise

    def get_daily_accuracy(self, ticker_id: str) -> dict:
        """
        Calculate prediction accuracy for today only (NY timezone).

        Args:
            ticker_id: Ticker UUID

        Returns:
            Dictionary with today's accuracy metrics
        """
        try:
            import pytz
            from datetime import timedelta

            # Get today's date in NY timezone
            ny_tz = pytz.timezone('America/New_York')
            now_ny = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(ny_tz)
            today_start_ny = now_ny.replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_utc = today_start_ny.astimezone(pytz.UTC)

            # Get predictions from today (in NY timezone)
            response = (
                self.client.table(self.predictions_table)
                .select('*')
                .eq('ticker_id', ticker_id)
                .gte('timestamp', today_start_utc.isoformat())
                .order('timestamp', desc=False)
                .execute()
            )

            predictions = [Prediction.from_dict(row) for row in response.data] if response.data else []

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
            verified = [p for p in predictions if p.actual_result in ['CORRECT', 'WRONG']]
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
                f"Daily accuracy for ticker {ticker_id}: "
                f"{correct}/{len(verified)} correct ({accuracy_rate:.1f}%)"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating daily accuracy: {e}")
            raise
