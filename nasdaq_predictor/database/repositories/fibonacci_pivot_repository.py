"""
Fibonacci Pivot Repository

Provides CRUD operations for Fibonacci pivot point calculations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pytz

from ..supabase_client import get_supabase_client
from ..models.fibonacci_pivot import FibonacciPivot
from ...analysis.fibonacci_pivots import FibonacciPivotLevels

logger = logging.getLogger(__name__)


class FibonacciPivotRepository:
    """
    Repository for Fibonacci Pivot CRUD operations.

    Provides methods to store, retrieve, and manage Fibonacci pivot calculations
    in the Supabase database.
    """

    def __init__(self):
        """Initialize the FibonacciPivotRepository."""
        self.client = get_supabase_client()
        self.table_name = 'fibonacci_pivots'
        self.utc = pytz.UTC

    def insert_or_update(self, pivot_levels: FibonacciPivotLevels) -> Optional[FibonacciPivot]:
        """
        Insert or update Fibonacci pivot calculation.

        Uses upsert to handle updates for existing records.

        Args:
            pivot_levels: FibonacciPivotLevels object with calculation results

        Returns:
            FibonacciPivot: Created/updated pivot record or None if error

        Example:
            >>> repo = FibonacciPivotRepository()
            >>> calculator = FibonacciPivotCalculator()
            >>> pivots = calculator.calculate_for_ticker('NQ=F', 'daily')
            >>> result = repo.insert_or_update(pivots)
        """
        try:
            data = {
                'ticker_symbol': pivot_levels.ticker_symbol,
                'timeframe': pivot_levels.timeframe,
                'calculation_date': pivot_levels.calculation_date.isoformat(),
                'period_high': float(pivot_levels.period_high),
                'period_low': float(pivot_levels.period_low),
                'period_close': float(pivot_levels.period_close),
                'pivot_point': float(pivot_levels.pivot_point),
                'resistance_1': float(pivot_levels.resistance_1),
                'resistance_2': float(pivot_levels.resistance_2),
                'resistance_3': float(pivot_levels.resistance_3),
                'support_1': float(pivot_levels.support_1),
                'support_2': float(pivot_levels.support_2),
                'support_3': float(pivot_levels.support_3)
            }

            # Upsert (insert or update on conflict)
            response = (
                self.client.table(self.table_name)
                .upsert(data, on_conflict='ticker_symbol,timeframe,calculation_date')
                .execute()
            )

            if response.data and len(response.data) > 0:
                logger.info(
                    f"Stored Fibonacci pivots: {pivot_levels.ticker_symbol} "
                    f"{pivot_levels.timeframe} {pivot_levels.calculation_date}"
                )
                return FibonacciPivot.from_row(tuple(response.data[0].values()))
            else:
                logger.warning(f"No data returned after upsert for {pivot_levels.ticker_symbol}")
                return None

        except Exception as e:
            logger.error(f"Error inserting/updating Fibonacci pivots: {e}", exc_info=True)
            return None

    def get_latest(
        self,
        ticker_symbol: str,
        timeframe: str
    ) -> Optional[FibonacciPivot]:
        """
        Get the most recent Fibonacci pivot calculation for a ticker and timeframe.

        Args:
            ticker_symbol: Ticker symbol (e.g., 'NQ=F')
            timeframe: Timeframe ('daily', 'weekly', 'monthly')

        Returns:
            FibonacciPivot: Most recent pivot calculation or None if not found

        Example:
            >>> repo = FibonacciPivotRepository()
            >>> pivots = repo.get_latest('NQ=F', 'daily')
        """
        try:
            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('ticker_symbol', ticker_symbol)
                .eq('timeframe', timeframe)
                .order('calculation_date', desc=True)
                .limit(1)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.info(f"No pivots found for {ticker_symbol} {timeframe}")
                return None

            return FibonacciPivot.from_row(tuple(response.data[0].values()))

        except Exception as e:
            logger.error(f"Error retrieving latest pivots for {ticker_symbol} {timeframe}: {e}")
            return None

    def get_all_latest(
        self,
        ticker_symbol: str
    ) -> Dict[str, Optional[FibonacciPivot]]:
        """
        Get the most recent pivot calculations for all timeframes.

        Args:
            ticker_symbol: Ticker symbol (e.g., 'NQ=F')

        Returns:
            Dict with timeframe as key and FibonacciPivot as value

        Example:
            >>> repo = FibonacciPivotRepository()
            >>> all_pivots = repo.get_all_latest('NQ=F')
            >>> daily = all_pivots['daily']
            >>> weekly = all_pivots['weekly']
        """
        timeframes = ['daily', 'weekly', 'monthly']
        results = {}

        for timeframe in timeframes:
            results[timeframe] = self.get_latest(ticker_symbol, timeframe)

        return results

    def get_historical(
        self,
        ticker_symbol: str,
        timeframe: str,
        days: int = 30
    ) -> List[FibonacciPivot]:
        """
        Get historical Fibonacci pivot calculations.

        Args:
            ticker_symbol: Ticker symbol (e.g., 'NQ=F')
            timeframe: Timeframe ('daily', 'weekly', 'monthly')
            days: Number of days to look back (default 30)

        Returns:
            List of FibonacciPivot objects ordered by date descending

        Example:
            >>> repo = FibonacciPivotRepository()
            >>> history = repo.get_historical('NQ=F', 'daily', days=7)
        """
        try:
            cutoff_date = datetime.now(self.utc) - timedelta(days=days)

            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('ticker_symbol', ticker_symbol)
                .eq('timeframe', timeframe)
                .gte('calculation_date', cutoff_date.isoformat())
                .order('calculation_date', desc=True)
                .execute()
            )

            if not response.data:
                logger.info(f"No historical pivots found for {ticker_symbol} {timeframe}")
                return []

            return [FibonacciPivot.from_row(tuple(row.values())) for row in response.data]

        except Exception as e:
            logger.error(f"Error retrieving historical pivots: {e}")
            return []

    def delete_old_records(
        self,
        days_to_keep: int = 90
    ) -> int:
        """
        Delete pivot records older than specified days.

        Args:
            days_to_keep: Keep records from last N days (default 90)

        Returns:
            int: Number of records deleted

        Example:
            >>> repo = FibonacciPivotRepository()
            >>> deleted = repo.delete_old_records(days_to_keep=60)
        """
        try:
            cutoff_date = datetime.now(self.utc) - timedelta(days=days_to_keep)

            response = (
                self.client.table(self.table_name)
                .delete()
                .lt('calculation_date', cutoff_date.isoformat())
                .execute()
            )

            count = len(response.data) if response.data else 0
            logger.info(f"Deleted {count} old pivot records (older than {cutoff_date.date()})")
            return count

        except Exception as e:
            logger.error(f"Error deleting old pivot records: {e}")
            return 0

    def get_all_for_ticker(
        self,
        ticker_symbol: str
    ) -> List[FibonacciPivot]:
        """
        Get all pivot records for a specific ticker (all timeframes).

        Args:
            ticker_symbol: Ticker symbol (e.g., 'NQ=F')

        Returns:
            List of all FibonacciPivot objects for the ticker

        Example:
            >>> repo = FibonacciPivotRepository()
            >>> all_pivots = repo.get_all_for_ticker('NQ=F')
        """
        try:
            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('ticker_symbol', ticker_symbol)
                .order('calculation_date', desc=True)
                .execute()
            )

            if not response.data:
                logger.info(f"No pivots found for {ticker_symbol}")
                return []

            return [FibonacciPivot.from_row(tuple(row.values())) for row in response.data]

        except Exception as e:
            logger.error(f"Error retrieving all pivots for {ticker_symbol}: {e}")
            return []

    def bulk_insert(
        self,
        pivot_levels_list: List[FibonacciPivotLevels]
    ) -> int:
        """
        Bulk insert multiple Fibonacci pivot calculations.

        Args:
            pivot_levels_list: List of FibonacciPivotLevels objects

        Returns:
            int: Number of records successfully inserted

        Example:
            >>> repo = FibonacciPivotRepository()
            >>> calculator = FibonacciPivotCalculator()
            >>> all_pivots = calculator.calculate_all_tickers(['NQ=F', 'ES=F'])
            >>> flat_list = [p for ticker in all_pivots.values() for p in ticker.values() if p]
            >>> count = repo.bulk_insert(flat_list)
        """
        try:
            data_list = []
            for pivot_levels in pivot_levels_list:
                if pivot_levels is None:
                    continue

                data_list.append({
                    'ticker_symbol': pivot_levels.ticker_symbol,
                    'timeframe': pivot_levels.timeframe,
                    'calculation_date': pivot_levels.calculation_date.isoformat(),
                    'period_high': float(pivot_levels.period_high),
                    'period_low': float(pivot_levels.period_low),
                    'period_close': float(pivot_levels.period_close),
                    'pivot_point': float(pivot_levels.pivot_point),
                    'resistance_1': float(pivot_levels.resistance_1),
                    'resistance_2': float(pivot_levels.resistance_2),
                    'resistance_3': float(pivot_levels.resistance_3),
                    'support_1': float(pivot_levels.support_1),
                    'support_2': float(pivot_levels.support_2),
                    'support_3': float(pivot_levels.support_3)
                })

            if not data_list:
                logger.warning("No valid pivot data to insert")
                return 0

            # Bulk upsert
            response = (
                self.client.table(self.table_name)
                .upsert(data_list, on_conflict='ticker_symbol,timeframe,calculation_date')
                .execute()
            )

            count = len(response.data) if response.data else 0
            logger.info(f"Bulk inserted/updated {count} Fibonacci pivot records")
            return count

        except Exception as e:
            logger.error(f"Error bulk inserting Fibonacci pivots: {e}", exc_info=True)
            return 0
