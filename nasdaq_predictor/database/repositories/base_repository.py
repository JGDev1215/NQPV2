"""
Base Repository class providing generic CRUD operations.

This class eliminates code duplication across repository implementations
by providing default implementations for common database operations.
Subclasses override _map_response() to provide entity-specific mapping.

Example:
    >>> class TickerRepository(BaseRepository):
    ...     def _map_response(self, data):
    ...         return Ticker.from_dict(data)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

from ..supabase_client import get_supabase_client
from ...core import DatabaseException

T = TypeVar("T")
logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Abstract base repository providing common CRUD operations.

    All concrete repositories should inherit from this class and implement
    the _map_response() method to convert database rows to domain entities.

    This eliminates ~250 lines of duplicated code across repositories.
    """

    def __init__(self, table_name: str):
        """Initialize repository with table name.

        Args:
            table_name: Name of the database table.
        """
        self.client = get_supabase_client()
        self.table_name = table_name

    # ========================================
    # Basic CRUD Operations
    # ========================================

    def select(self, filters: Dict[str, Any]) -> Optional[T]:
        """Select a single record matching filters.

        Args:
            filters: Dictionary of column:value filters to match.

        Returns:
            Mapped entity if found, None otherwise.

        Raises:
            DatabaseException: If query fails.

        Example:
            >>> ticker = repo.select({'symbol': 'NQ=F'})
        """
        try:
            query = self.client.table(self.table_name).select("*")

            # Apply filters
            for column, value in filters.items():
                query = query.eq(column, value)

            response = query.execute()

            if not response.data:
                logger.debug(f"No record found in {self.table_name} with filters {filters}")
                return None

            logger.debug(f"Found record in {self.table_name} with filters {filters}")
            return self._map_response(response.data[0])

        except Exception as e:
            logger.error(f"Error selecting from {self.table_name}: {e}")
            raise DatabaseException(f"Select failed on {self.table_name}: {str(e)}") from e

    def select_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Select all records, optionally filtered.

        Args:
            filters: Optional dictionary of filters.

        Returns:
            List of mapped entities.

        Raises:
            DatabaseException: If query fails.

        Example:
            >>> all_tickers = repo.select_all()
            >>> enabled_tickers = repo.select_all({'enabled': True})
        """
        try:
            query = self.client.table(self.table_name).select("*")

            # Apply filters if provided
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)

            response = query.execute()

            if not response.data:
                logger.debug(f"No records found in {self.table_name}")
                return []

            entities = [self._map_response(row) for row in response.data]
            logger.debug(f"Retrieved {len(entities)} records from {self.table_name}")
            return entities

        except Exception as e:
            logger.error(f"Error selecting all from {self.table_name}: {e}")
            raise DatabaseException(f"Select all failed on {self.table_name}: {str(e)}") from e

    def insert(self, data: Dict[str, Any]) -> T:
        """Insert a new record.

        Args:
            data: Dictionary of column:value pairs to insert.

        Returns:
            Mapped entity with generated ID.

        Raises:
            DatabaseException: If insert fails.

        Example:
            >>> ticker = repo.insert({
            ...     'symbol': 'RTY=F',
            ...     'name': 'Russell 2000 Futures',
            ...     'type': 'futures'
            ... })
        """
        try:
            response = self.client.table(self.table_name).insert(data).execute()

            if not response.data:
                raise DatabaseException("Insert failed: no data returned")

            logger.info(f"Inserted record into {self.table_name}")
            return self._map_response(response.data[0])

        except DatabaseException:
            raise
        except Exception as e:
            logger.error(f"Error inserting into {self.table_name}: {e}")
            raise DatabaseException(f"Insert failed on {self.table_name}: {str(e)}") from e

    def insert_many(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """Insert multiple records.

        Args:
            data_list: List of dictionaries to insert.

        Returns:
            List of mapped entities.

        Raises:
            DatabaseException: If insert fails.

        Example:
            >>> tickers = repo.insert_many([
            ...     {'symbol': 'NQ=F', ...},
            ...     {'symbol': 'ES=F', ...},
            ... ])
        """
        try:
            response = self.client.table(self.table_name).insert(data_list).execute()

            if not response.data:
                raise DatabaseException("Insert many failed: no data returned")

            entities = [self._map_response(row) for row in response.data]
            logger.info(f"Inserted {len(entities)} records into {self.table_name}")
            return entities

        except DatabaseException:
            raise
        except Exception as e:
            logger.error(f"Error inserting many into {self.table_name}: {e}")
            raise DatabaseException(f"Insert many failed on {self.table_name}: {str(e)}") from e

    def update(self, id: Any, data: Dict[str, Any]) -> T:
        """Update a record by ID.

        Args:
            id: Record ID.
            data: Dictionary of column:value pairs to update.

        Returns:
            Updated mapped entity.

        Raises:
            DatabaseException: If update fails or record not found.

        Example:
            >>> updated = repo.update('uuid-here', {'enabled': False})
        """
        try:
            response = (
                self.client.table(self.table_name).update(data).eq("id", id).execute()
            )

            if not response.data:
                logger.warning(f"Record with id {id} not found in {self.table_name}")
                raise DatabaseException(f"Record not found: {id}")

            logger.info(f"Updated record {id} in {self.table_name}")
            return self._map_response(response.data[0])

        except DatabaseException:
            raise
        except Exception as e:
            logger.error(f"Error updating {self.table_name}: {e}")
            raise DatabaseException(f"Update failed on {self.table_name}: {str(e)}") from e

    def delete(self, id: Any) -> bool:
        """Delete a record by ID.

        Args:
            id: Record ID.

        Returns:
            True if deleted, False if not found.

        Raises:
            DatabaseException: If delete fails.

        Example:
            >>> success = repo.delete('uuid-here')
        """
        try:
            response = self.client.table(self.table_name).delete().eq("id", id).execute()

            logger.info(f"Deleted record {id} from {self.table_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting from {self.table_name}: {e}")
            raise DatabaseException(f"Delete failed on {self.table_name}: {str(e)}") from e

    # ========================================
    # Counting & Existence Checks
    # ========================================

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records, optionally filtered.

        Args:
            filters: Optional dictionary of filters.

        Returns:
            Count of matching records.

        Raises:
            DatabaseException: If count fails.

        Example:
            >>> total = repo.count()
            >>> enabled_count = repo.count({'enabled': True})
        """
        try:
            query = self.client.table(self.table_name).select("count(*)")

            # Apply filters if provided
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)

            response = query.execute()

            if response.data:
                count = response.data[0]["count"]
                logger.debug(f"Count from {self.table_name}: {count}")
                return count

            return 0

        except Exception as e:
            logger.error(f"Error counting {self.table_name}: {e}")
            raise DatabaseException(f"Count failed on {self.table_name}: {str(e)}") from e

    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if a record matching filters exists.

        Args:
            filters: Dictionary of filters to check.

        Returns:
            True if record exists, False otherwise.

        Example:
            >>> if repo.exists({'symbol': 'NQ=F'}):
            ...     print("NQ=F exists")
        """
        try:
            return self.select(filters) is not None
        except Exception:
            return False

    # ========================================
    # Advanced Operations
    # ========================================

    def select_with_limit(
        self, limit: int = 100, offset: int = 0, filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Select records with pagination.

        Args:
            limit: Maximum records to return.
            offset: Number of records to skip.
            filters: Optional filters.

        Returns:
            List of mapped entities.

        Raises:
            DatabaseException: If query fails.

        Example:
            >>> page = repo.select_with_limit(limit=10, offset=0)
        """
        try:
            query = self.client.table(self.table_name).select("*")

            # Apply filters if provided
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)

            # Apply pagination
            response = query.range(offset, offset + limit - 1).execute()

            if not response.data:
                logger.debug(f"No records found in {self.table_name} with pagination")
                return []

            entities = [self._map_response(row) for row in response.data]
            logger.debug(f"Retrieved {len(entities)} paginated records from {self.table_name}")
            return entities

        except Exception as e:
            logger.error(f"Error with pagination on {self.table_name}: {e}")
            raise DatabaseException(f"Paginated select failed on {self.table_name}: {str(e)}") from e

    def select_with_order(
        self,
        order_by: str,
        order_desc: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[T]:
        """Select records ordered by column.

        Args:
            order_by: Column name to order by.
            order_desc: If True, order descending; otherwise ascending.
            filters: Optional filters.

        Returns:
            List of mapped entities.

        Raises:
            DatabaseException: If query fails.

        Example:
            >>> recent = repo.select_with_order(
            ...     order_by='created_at',
            ...     order_desc=True
            ... )
        """
        try:
            query = self.client.table(self.table_name).select("*")

            # Apply filters if provided
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)

            # Apply ordering
            response = query.order(order_by, desc=order_desc).execute()

            if not response.data:
                logger.debug(f"No records found in {self.table_name}")
                return []

            entities = [self._map_response(row) for row in response.data]
            logger.debug(f"Retrieved {len(entities)} ordered records from {self.table_name}")
            return entities

        except Exception as e:
            logger.error(f"Error with ordering on {self.table_name}: {e}")
            raise DatabaseException(f"Ordered select failed on {self.table_name}: {str(e)}") from e

    # ========================================
    # Abstract Method (Subclass Implementation)
    # ========================================

    @abstractmethod
    def _map_response(self, data: Dict[str, Any]) -> T:
        """Map database row to domain entity.

        Subclasses MUST implement this to convert database dictionaries
        to their specific entity types.

        Args:
            data: Database row as dictionary.

        Returns:
            Mapped domain entity.

        Example:
            >>> class TickerRepository(BaseRepository):
            ...     def _map_response(self, data):
            ...         return Ticker.from_dict(data)
        """
        pass
