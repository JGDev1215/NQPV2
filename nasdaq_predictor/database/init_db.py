"""
Database initialization script for NQP application.

This script initializes the database by:
1. Testing the connection to Supabase
2. Running SQL migrations (creating tables)
3. Seeding initial data (tickers)
4. Verifying the setup

Usage:
    python -m nasdaq_predictor.database.init_db
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """Test the connection to Supabase."""
    logger.info("Testing Supabase connection...")

    try:
        from .supabase_client import test_connection as test_supabase_connection

        if test_supabase_connection():
            logger.info("✓ Supabase connection successful")
            return True
        else:
            logger.error("✗ Supabase connection failed")
            return False

    except Exception as e:
        logger.error(f"✗ Error testing connection: {e}")
        return False


def run_migrations():
    """Run SQL migrations to create tables."""
    logger.info("Running SQL migrations...")

    try:
        from .supabase_client import get_supabase_client

        # Read migration SQL file
        migrations_dir = Path(__file__).parent / 'migrations'
        migration_file = migrations_dir / '001_initial_schema.sql'

        if not migration_file.exists():
            logger.error(f"✗ Migration file not found: {migration_file}")
            return False

        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        logger.info("Migration SQL file loaded")
        logger.info("=" * 80)
        logger.info("IMPORTANT: Manual SQL Execution Required")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Please execute the migration SQL manually in your Supabase SQL Editor:")
        logger.info("")
        logger.info(f"1. Go to: https://kwhvnfcvqvbqbjmdakrm.supabase.co/project/_/sql")
        logger.info(f"2. Open the SQL Editor")
        logger.info(f"3. Copy and paste the contents of: {migration_file}")
        logger.info(f"4. Click 'Run' to execute the migration")
        logger.info("")
        logger.info("=" * 80)
        logger.info("")

        # Note: Supabase Python client doesn't support direct SQL execution
        # The migration needs to be run manually in the Supabase SQL Editor
        logger.warning("⚠ SQL migrations must be run manually in Supabase SQL Editor")
        logger.info("Once you've run the migration, press Enter to continue...")
        input()

        return True

    except Exception as e:
        logger.error(f"✗ Error running migrations: {e}")
        return False


def seed_initial_data():
    """Seed initial data (tickers)."""
    logger.info("Seeding initial data...")

    try:
        from .repositories.ticker_repository import TickerRepository

        ticker_repo = TickerRepository()
        tickers = ticker_repo.seed_initial_tickers()

        logger.info(f"✓ Seeded {len(tickers)} tickers:")
        for ticker in tickers:
            logger.info(f"  - {ticker.symbol}: {ticker.name}")

        return True

    except Exception as e:
        logger.error(f"✗ Error seeding initial data: {e}")
        return False


def verify_setup():
    """Verify the database setup."""
    logger.info("Verifying database setup...")

    try:
        from .repositories.ticker_repository import TickerRepository

        ticker_repo = TickerRepository()

        # Test: Get all tickers
        tickers = ticker_repo.get_all_tickers()
        logger.info(f"✓ Found {len(tickers)} tickers in database")

        # Test: Get enabled tickers
        enabled_tickers = ticker_repo.get_enabled_tickers()
        logger.info(f"✓ Found {len(enabled_tickers)} enabled tickers")

        # Test: Get ticker by symbol
        nq_ticker = ticker_repo.get_ticker_by_symbol('NQ=F')
        if nq_ticker:
            logger.info(f"✓ Successfully retrieved NQ=F ticker (ID: {nq_ticker.id})")
        else:
            logger.warning("⚠ NQ=F ticker not found")

        return True

    except Exception as e:
        logger.error(f"✗ Error verifying setup: {e}")
        return False


def main():
    """Main initialization function."""
    logger.info("=" * 80)
    logger.info("NQP Database Initialization")
    logger.info("=" * 80)
    logger.info("")

    # Step 1: Test connection
    if not test_connection():
        logger.error("Database initialization failed: Cannot connect to Supabase")
        sys.exit(1)

    logger.info("")

    # Step 2: Run migrations
    if not run_migrations():
        logger.error("Database initialization failed: Migration error")
        sys.exit(1)

    logger.info("")

    # Step 3: Seed initial data
    if not seed_initial_data():
        logger.error("Database initialization failed: Seeding error")
        sys.exit(1)

    logger.info("")

    # Step 4: Verify setup
    if not verify_setup():
        logger.error("Database initialization failed: Verification error")
        sys.exit(1)

    logger.info("")
    logger.info("=" * 80)
    logger.info("✓ Database initialization completed successfully!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. The database is ready to use")
    logger.info("2. You can now run the NQP application")
    logger.info("3. The scheduler will automatically fetch and store market data")
    logger.info("")


if __name__ == '__main__':
    main()
