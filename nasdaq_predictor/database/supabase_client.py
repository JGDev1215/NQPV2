"""
Supabase client connection manager for NQP application.

This module provides a singleton Supabase client with connection pooling,
error handling, and automatic reconnection logic.

Usage:
    from nasdaq_predictor.database.supabase_client import get_supabase_client

    client = get_supabase_client()
    response = client.table('tickers').select('*').execute()
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Singleton Supabase client manager.

    Provides a single instance of Supabase client for the application
    with connection pooling and error handling.

    Attributes:
        _instance: Singleton instance
        _client: Supabase client instance
        _url: Supabase project URL
        _key: Supabase API key
    """

    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    _url: Optional[str] = None
    _key: Optional[str] = None

    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the Supabase client if not already initialized."""
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize the Supabase client with credentials from environment variables.

        Raises:
            ValueError: If SUPABASE_URL or SUPABASE_KEY are not set
            Exception: If connection to Supabase fails
        """
        try:
            # Get credentials from environment
            self._url = os.getenv('SUPABASE_URL')
            self._key = os.getenv('SUPABASE_KEY')

            if not self._url or not self._key:
                raise ValueError(
                    "Missing Supabase credentials. "
                    "Please set SUPABASE_URL and SUPABASE_KEY in .env file."
                )

            # Create client with default options
            # Note: ClientOptions configuration changed in supabase v2.24.0
            self._client = create_client(self._url, self._key)

            logger.info("Successfully initialized Supabase client")

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    def get_client(self) -> Client:
        """
        Get the Supabase client instance.

        Returns:
            Client: Supabase client instance

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            raise RuntimeError("Supabase client is not initialized")
        return self._client

    def test_connection(self) -> bool:
        """
        Test the connection to Supabase by querying the tickers table.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to query the tickers table
            response = self._client.table('tickers').select('id').limit(1).execute()

            # Check if query was successful
            if response:
                logger.info("Supabase connection test successful")
                return True
            else:
                logger.error("Supabase connection test failed: No response")
                return False

        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False

    def close_connection(self) -> None:
        """
        Close the Supabase connection.

        Note: Supabase Python client doesn't require explicit connection closing,
        but this method is provided for consistency and future extensions.
        """
        if self._client:
            logger.info("Supabase client closed")
            self._client = None

    def reconnect(self) -> None:
        """
        Reconnect to Supabase by reinitializing the client.

        Useful for handling connection errors or timeouts.
        """
        logger.info("Reconnecting to Supabase...")
        self.close_connection()
        self._initialize_client()

    def execute_query(self, table: str, query_builder):
        """
        Execute a query with automatic retry on connection errors.

        Args:
            table: Table name
            query_builder: Function that builds and executes the query

        Returns:
            Query result

        Raises:
            Exception: If query fails after retry
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return query_builder()

            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"Query failed (attempt {retry_count}/{max_retries}): {e}"
                )

                if retry_count < max_retries:
                    logger.info("Attempting to reconnect...")
                    self.reconnect()
                else:
                    logger.error("Max retries reached. Query failed.")
                    raise

    def __repr__(self) -> str:
        """String representation of the SupabaseClient."""
        status = "connected" if self._client else "not connected"
        return f"<SupabaseClient status={status} url={self._url}>"


# Global singleton instance
_supabase_client_instance: Optional[SupabaseClient] = None


def get_supabase_client() -> Client:
    """
    Get the global Supabase client instance.

    This is the primary function to use for accessing the Supabase client
    throughout the application.

    Returns:
        Client: Supabase client instance

    Example:
        >>> client = get_supabase_client()
        >>> response = client.table('tickers').select('*').execute()
    """
    global _supabase_client_instance

    if _supabase_client_instance is None:
        _supabase_client_instance = SupabaseClient()

    return _supabase_client_instance.get_client()


def test_connection() -> bool:
    """
    Test the connection to Supabase.

    Returns:
        bool: True if connection is successful, False otherwise

    Example:
        >>> if test_connection():
        ...     print("Connected to Supabase!")
    """
    global _supabase_client_instance

    if _supabase_client_instance is None:
        _supabase_client_instance = SupabaseClient()

    return _supabase_client_instance.test_connection()


def close_connection() -> None:
    """
    Close the global Supabase connection.

    Example:
        >>> close_connection()
    """
    global _supabase_client_instance

    if _supabase_client_instance is not None:
        _supabase_client_instance.close_connection()
        _supabase_client_instance = None


def reconnect() -> None:
    """
    Reconnect to Supabase.

    Example:
        >>> reconnect()
    """
    global _supabase_client_instance

    if _supabase_client_instance is None:
        _supabase_client_instance = SupabaseClient()
    else:
        _supabase_client_instance.reconnect()
