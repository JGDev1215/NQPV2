"""
Thread-safe caching utilities
"""
import threading
import pytz
from datetime import datetime
from typing import Optional, Tuple, Any, Dict


class ThreadSafeCache:
    """Thread-safe cache for storing market data"""

    def __init__(self):
        self._cache = {'data': None, 'timestamp': None}
        self._predictions = {}  # Store daily predictions: {date: {hour: prediction_data}}
        self._lock = threading.Lock()

    def get(self) -> Tuple[Optional[Any], Optional[datetime]]:
        """
        Get cached data and timestamp

        Returns:
            Tuple of (data, timestamp)
        """
        with self._lock:
            return self._cache['data'], self._cache['timestamp']

    def set(self, data: Any, timestamp: datetime) -> None:
        """
        Set cache data and timestamp

        Args:
            data: Data to cache
            timestamp: Timestamp of the data
        """
        with self._lock:
            self._cache['data'] = data
            self._cache['timestamp'] = timestamp

    def is_valid(self, duration: int) -> bool:
        """
        Check if cache is valid (not expired)

        Args:
            duration: Cache validity duration in seconds

        Returns:
            True if cache is valid, False otherwise
        """
        with self._lock:
            if self._cache['data'] is None or self._cache['timestamp'] is None:
                return False
            # Use UTC-aware datetime for comparison to handle both naive and aware timestamps
            current_time = datetime.now(pytz.UTC)
            cached_time = self._cache['timestamp']

            # Ensure cached_time is aware (convert if naive)
            if cached_time.tzinfo is None:
                cached_time = pytz.UTC.localize(cached_time)

            time_diff = (current_time - cached_time).total_seconds()
            return time_diff < duration

    def clear(self) -> None:
        """Clear the cache"""
        with self._lock:
            self._cache['data'] = None
            self._cache['timestamp'] = None

    def store_prediction(self, date: str, hour: int, prediction_data: Dict[str, Any]) -> None:
        """
        Store a prediction for a specific date and hour

        Args:
            date: Date string (YYYY-MM-DD)
            hour: Hour (9 or 10)
            prediction_data: Prediction data dictionary
        """
        with self._lock:
            if date not in self._predictions:
                self._predictions[date] = {}
            self._predictions[date][hour] = prediction_data

    def get_prediction(self, date: str, hour: int) -> Optional[Dict[str, Any]]:
        """
        Get a stored prediction for a specific date and hour

        Args:
            date: Date string (YYYY-MM-DD)
            hour: Hour (9 or 10)

        Returns:
            Prediction data dictionary or None if not found
        """
        with self._lock:
            if date in self._predictions and hour in self._predictions[date]:
                return self._predictions[date][hour]
            return None

    def get_day_predictions(self, date: str) -> Dict[int, Dict[str, Any]]:
        """
        Get all predictions for a specific date

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            Dictionary of predictions by hour {9: {...}, 10: {...}}
        """
        with self._lock:
            return self._predictions.get(date, {})

    def clear_old_predictions(self, days_to_keep: int = 7) -> None:
        """
        Clear predictions older than specified days

        Args:
            days_to_keep: Number of days to keep (default 7)
        """
        with self._lock:
            current_date = datetime.now(pytz.UTC).date()
            dates_to_remove = []

            for date_str in self._predictions.keys():
                try:
                    pred_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    age_days = (current_date - pred_date).days
                    if age_days > days_to_keep:
                        dates_to_remove.append(date_str)
                except ValueError:
                    # Invalid date format, mark for removal
                    dates_to_remove.append(date_str)

            for date_str in dates_to_remove:
                del self._predictions[date_str]

    def clear_predictions(self) -> None:
        """Clear all stored predictions"""
        with self._lock:
            self._predictions = {}
