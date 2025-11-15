"""Reference Levels repository for NQP application."""

import logging
from typing import Optional
from datetime import datetime

from ..supabase_client import get_supabase_client
from ..models.reference_levels import ReferenceLevels
from ...config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class ReferenceLevelsRepository:
    """Repository for ReferenceLevels CRUD operations."""

    def __init__(self):
        self.client = get_supabase_client()
        self.table_name = DatabaseConfig.TABLE_REFERENCE_LEVELS

    def store_reference_levels(self, ref_levels: ReferenceLevels) -> ReferenceLevels:
        """Store reference levels (upsert)."""
        try:
            levels_data = ref_levels.to_db_dict()
            response = self.client.table(self.table_name).upsert(levels_data).execute()

            if not response.data:
                raise Exception("Failed to store reference levels")

            created = ReferenceLevels.from_dict(response.data[0])
            logger.info(f"Stored reference levels for ticker {ref_levels.ticker_id}")
            return created

        except Exception as e:
            logger.error(f"Error storing reference levels: {e}")
            raise

    def get_latest_reference_levels(self, ticker_id: str) -> Optional[ReferenceLevels]:
        """Get the most recent reference levels for a ticker."""
        try:
            response = (
                self.client.table(self.table_name)
                .select('*')
                .eq('ticker_id', ticker_id)
                .order('timestamp', desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                return None

            return ReferenceLevels.from_dict(response.data[0])

        except Exception as e:
            logger.error(f"Error getting latest reference levels: {e}")
            raise
