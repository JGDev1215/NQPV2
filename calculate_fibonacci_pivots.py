#!/usr/bin/env python3
"""
Script to manually calculate and store Fibonacci pivot points.
This populates the fibonacci_pivots table with data for all tickers.
"""

import logging
import sys
from nasdaq_predictor.analysis.fibonacci_pivots import FibonacciPivotCalculator
from nasdaq_predictor.database.repositories.fibonacci_pivot_repository import FibonacciPivotRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Calculate and store Fibonacci pivots for all tickers"""

    # Tickers to calculate pivots for
    tickers = ['NQ=F', 'ES=F', '^FTSE']
    timeframes = ['daily', 'weekly', 'monthly']

    logger.info("=" * 80)
    logger.info("CALCULATING FIBONACCI PIVOT POINTS")
    logger.info("=" * 80)

    calculator = FibonacciPivotCalculator()
    repo = FibonacciPivotRepository()

    total_success = 0
    total_failed = 0

    for ticker in tickers:
        logger.info(f"\nProcessing {ticker}...")

        for timeframe in timeframes:
            try:
                logger.info(f"  Calculating {timeframe} pivots...")

                # Calculate pivots
                pivot_levels = calculator.calculate_for_ticker(ticker, timeframe)

                if pivot_levels is None:
                    logger.error(f"  ✗ Failed to calculate {timeframe} pivots for {ticker}")
                    total_failed += 1
                    continue

                # Store in database
                repo.insert_or_update(pivot_levels)

                logger.info(f"  ✓ Stored {timeframe} pivots for {ticker}")
                logger.info(f"    PP: {pivot_levels.pivot_point:.2f}")
                logger.info(f"    R1: {pivot_levels.resistance_1:.2f} | S1: {pivot_levels.support_1:.2f}")
                logger.info(f"    R2: {pivot_levels.resistance_2:.2f} | S2: {pivot_levels.support_2:.2f}")
                logger.info(f"    R3: {pivot_levels.resistance_3:.2f} | S3: {pivot_levels.support_3:.2f}")

                total_success += 1

            except Exception as e:
                logger.error(f"  ✗ Error calculating {timeframe} pivots for {ticker}: {e}", exc_info=True)
                total_failed += 1

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Successful: {total_success}")
    logger.info(f"Total Failed: {total_failed}")
    logger.info("=" * 80)

    if total_failed > 0:
        logger.warning(f"\n⚠️  {total_failed} calculation(s) failed")
        return 1
    else:
        logger.info("\n✓ All calculations completed successfully!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
