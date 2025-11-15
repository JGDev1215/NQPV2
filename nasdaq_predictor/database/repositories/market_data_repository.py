"""Market Data repository for NQP application."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from ..supabase_client import get_supabase_client
from ..models.market_data import MarketData
from ...config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class MarketDataRepository:
    """Repository for MarketData CRUD operations."""

    def __init__(self):
        self.client = get_supabase_client()
        self.table_name = DatabaseConfig.TABLE_MARKET_DATA

    def store_ohlc_data(self, ticker_id: str, data: List[MarketData]) -> int:
        """Store OHLC data in bulk (upsert)."""
        try:
            if not data:
                return 0

            data_dicts = [item.to_db_dict() for item in data]
            # Use on_conflict parameter to specify which columns to check for duplicates
            response = self.client.table(self.table_name).upsert(
                data_dicts,
                on_conflict='ticker_id,timestamp,interval'
            ).execute()

            count = len(response.data) if response.data else 0
            logger.info(f"Stored {count} market data records for ticker {ticker_id}")
            return count

        except Exception as e:
            logger.error(f"Error storing market data: {e}")
            raise

    def get_latest_price(self, ticker_id: str, interval: str = '1m') -> Optional[MarketData]:
        """Get the latest price for a ticker."""
        try:
            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('ticker_id', ticker_id)
                .eq('interval', interval)
                .order('timestamp', desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                return None

            return MarketData.from_dict(response.data[0])

        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            raise

    def get_historical_data(
        self, ticker_id: str, start: datetime, end: datetime, interval: str = '1h'
    ) -> List[MarketData]:
        """Get historical data for a date range."""
        try:
            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('ticker_id', ticker_id)
                .eq('interval', interval)
                .gte('timestamp', start.isoformat())
                .lte('timestamp', end.isoformat())
                .order('timestamp', desc=False)
                .execute()
            )

            return [MarketData.from_dict(row) for row in response.data] if response.data else []

        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            raise

    def get_historical_data_paginated(
        self,
        ticker_id: str,
        interval: str = '1h',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[MarketData], int]:
        """
        Get paginated historical data with optional date filtering.

        Args:
            ticker_id: Ticker UUID
            interval: Time interval (1m, 1h, 1d)
            start: Start datetime (optional)
            end: End datetime (optional)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Tuple of (data_list, total_count)
        """
        try:
            # Build query
            query = (
                self.client.table(self.table_name)
                .select('*', count='exact')
                .eq('ticker_id', ticker_id)
                .eq('interval', interval)
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

            data = [MarketData.from_dict(row) for row in response.data] if response.data else []
            total_count = response.count if hasattr(response, 'count') else len(data)

            logger.info(
                f"Retrieved {len(data)} of {total_count} historical records "
                f"for ticker {ticker_id} (interval: {interval})"
            )

            return data, total_count

        except Exception as e:
            logger.error(f"Error getting paginated historical data: {e}")
            raise

    def get_recent_data(
        self,
        ticker_id: str,
        interval: str = '1h',
        hours: int = 24
    ) -> List[MarketData]:
        """
        Get recent market data for the specified number of hours.

        Args:
            ticker_id: Ticker UUID
            interval: Time interval (1m, 1h, 1d)
            hours: Number of hours to look back

        Returns:
            List of MarketData objects
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('ticker_id', ticker_id)
                .eq('interval', interval)
                .gte('timestamp', cutoff_time.isoformat())
                .order('timestamp', desc=False)
                .execute()
            )

            data = [MarketData.from_dict(row) for row in response.data] if response.data else []
            logger.info(f"Retrieved {len(data)} records from last {hours} hours for ticker {ticker_id}")

            return data

        except Exception as e:
            logger.error(f"Error getting recent data: {e}")
            raise
