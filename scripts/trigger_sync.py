"""
Manual trigger script for syncing data to Supabase.

This script will:
1. Seed initial tickers (NQ=F, ES=F) into the database
2. Manually trigger the market data sync job
3. Manually trigger the prediction calculation job
"""

import logging
from nasdaq_predictor.database.supabase_client import get_supabase_client
from nasdaq_predictor.scheduler.jobs import (
    fetch_and_store_market_data,
    calculate_and_store_predictions
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_tickers():
    """Add initial tickers to the database."""
    logger.info("=" * 80)
    logger.info("SEEDING TICKERS")
    logger.info("=" * 80)

    try:
        client = get_supabase_client()

        # Define tickers to seed
        tickers = [
            {
                'symbol': 'NQ=F',
                'name': 'NASDAQ 100 E-mini Futures',
                'type': 'futures',
                'enabled': True,
                'timezone': 'America/New_York',
                'metadata': {
                    'exchange': 'CME',
                    'trading_hours': '18:00-17:00 ET',
                    'contract': 'E-mini'
                }
            },
            {
                'symbol': 'ES=F',
                'name': 'S&P 500 E-mini Futures',
                'type': 'futures',
                'enabled': True,
                'timezone': 'America/New_York',
                'metadata': {
                    'exchange': 'CME',
                    'trading_hours': '18:00-17:00 ET',
                    'contract': 'E-mini'
                }
            },
            {
                'symbol': '^N225',
                'name': 'Nikkei 225',
                'type': 'index',
                'enabled': True,
                'timezone': 'Asia/Tokyo',
                'metadata': {
                    'exchange': 'TSE',
                    'trading_hours': '09:00-15:00 JST',
                    'country': 'Japan'
                }
            },
            {
                'symbol': '^VIX',
                'name': 'CBOE Volatility Index',
                'type': 'index',
                'enabled': True,
                'timezone': 'America/Chicago',
                'metadata': {
                    'exchange': 'CBOE',
                    'trading_hours': '08:30-15:15 CT',
                    'description': 'Fear Index'
                }
            },
            {
                'symbol': 'RTY=F',
                'name': 'E-mini Russell 2000 Index Futures',
                'type': 'futures',
                'enabled': True,
                'timezone': 'America/New_York',
                'metadata': {
                    'exchange': 'CME',
                    'trading_hours': '18:00-17:00 ET',
                    'contract': 'E-mini'
                }
            },
            {
                'symbol': 'YM=F',
                'name': 'Mini Dow Jones Indus.-$5 Dec 25',
                'type': 'futures',
                'enabled': True,
                'timezone': 'America/New_York',
                'metadata': {
                    'exchange': 'CBOT',
                    'trading_hours': '18:00-17:00 ET',
                    'contract': 'Mini'
                }
            },
            {
                'symbol': '^FTSE',
                'name': 'FTSE 100',
                'type': 'index',
                'enabled': True,
                'timezone': 'Europe/London',
                'metadata': {
                    'exchange': 'LSE',
                    'trading_hours': '08:00-16:30 GMT',
                    'country': 'UK'
                }
            },
            {
                'symbol': 'BTC-USD',
                'name': 'Bitcoin',
                'type': 'index',
                'enabled': True,
                'timezone': 'UTC',
                'metadata': {
                    'exchange': 'Crypto',
                    'trading_hours': '24/7',
                    'description': 'Bitcoin to USD',
                    'category': 'crypto'
                }
            },
            {
                'symbol': 'SOL-USD',
                'name': 'Solana',
                'type': 'index',
                'enabled': True,
                'timezone': 'UTC',
                'metadata': {
                    'exchange': 'Crypto',
                    'trading_hours': '24/7',
                    'description': 'Solana to USD',
                    'category': 'crypto'
                }
            },
            {
                'symbol': 'ADA-USD',
                'name': 'Cardano',
                'type': 'index',
                'enabled': True,
                'timezone': 'UTC',
                'metadata': {
                    'exchange': 'Crypto',
                    'trading_hours': '24/7',
                    'description': 'Cardano to USD',
                    'category': 'crypto'
                }
            }
        ]

        for ticker_data in tickers:
            symbol = ticker_data['symbol']

            # Check if ticker already exists
            existing = client.table('tickers').select('*').eq('symbol', symbol).execute()

            if existing.data and len(existing.data) > 0:
                logger.info(f"✓ Ticker {symbol} already exists, skipping...")
                continue

            # Insert ticker
            result = client.table('tickers').insert(ticker_data).execute()

            if result.data:
                logger.info(f"✓ Successfully added ticker: {symbol}")
            else:
                logger.error(f"✗ Failed to add ticker: {symbol}")

        logger.info("=" * 80)
        logger.info("TICKER SEEDING COMPLETE")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"✗ Error seeding tickers: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("MANUAL SYNC TRIGGER")
    logger.info("=" * 80)

    # Step 1: Seed tickers
    logger.info("\nStep 1: Seeding tickers...")
    if not seed_tickers():
        logger.error("Failed to seed tickers. Aborting sync.")
        return

    # Step 2: Fetch and store market data
    logger.info("\nStep 2: Fetching and storing market data...")
    try:
        fetch_and_store_market_data()
        logger.info("✓ Market data sync completed")
    except Exception as e:
        logger.error(f"✗ Market data sync failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # Step 3: Calculate and store predictions
    logger.info("\nStep 3: Calculating and storing predictions...")
    try:
        calculate_and_store_predictions()
        logger.info("✓ Prediction calculation completed")
    except Exception as e:
        logger.error(f"✗ Prediction calculation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("\n" + "=" * 80)
    logger.info("MANUAL SYNC COMPLETE")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
