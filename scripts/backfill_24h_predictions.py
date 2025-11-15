"""
NQP 24-Hour Prediction History Backfill Script

This script populates the intraday_predictions table with historical predictions
for the last 24 hours, generating predictions at market hours (9 AM - 4 PM).

Usage:
    python backfill_24h_predictions.py --tickers NQ=F ES=F BTC-USD --dry-run
    python backfill_24h_predictions.py --tickers NQ=F --hours-back 24
    python backfill_24h_predictions.py  # Defaults to NQ=F, ES=F, BTC-USD for 24h
"""

import yfinance as yf
import pandas as pd
import pytz
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add nasdaq_predictor to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nasdaq_predictor.database.repositories.ticker_repository import TickerRepository
from nasdaq_predictor.database.repositories.intraday_prediction_repository import IntradayPredictionRepository
from nasdaq_predictor.database.models.intraday_prediction import IntradayPrediction
from nasdaq_predictor.analysis.reference_levels import calculate_all_reference_levels
from nasdaq_predictor.analysis.signals import calculate_signals
from nasdaq_predictor.analysis.intraday import calculate_intraday_predictions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_timezone(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame has UTC timezone-aware index"""
    if df.empty:
        return df

    if hasattr(df.index, 'tz'):
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')
    return df


def fetch_historical_data(
    ticker_symbol: str,
    hours_back: int = 48
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fetch historical data for backfilling.

    Args:
        ticker_symbol: Ticker symbol
        hours_back: How many hours of data to fetch (default: 48 for buffer)

    Returns:
        Tuple of (data_30min, data_hourly, data_daily)
    """
    logger.info(f"📊 Fetching historical data for {ticker_symbol}...")

    ticker = yf.Ticker(ticker_symbol)

    # Determine period
    # For 30-min data: need at least 2 days for reference calculations
    period_30min = f"{min(hours_back, 60)}d"  # yfinance limit
    period_hourly = f"{min(hours_back * 2, 730)}d"  # More history for reference levels
    period_daily = "1y"  # Year for daily reference levels

    try:
        logger.info(f"  ⏳ Downloading 30-minute data ({period_30min})...")
        data_30min = ticker.history(period=period_30min, interval='30m')

        logger.info(f"  ⏳ Downloading hourly data ({period_hourly})...")
        data_hourly = ticker.history(period=period_hourly, interval='1h')

        logger.info(f"  ⏳ Downloading daily data ({period_daily})...")
        data_daily = ticker.history(period=period_daily, interval='1d')

        # Ensure UTC timezone
        data_30min = ensure_timezone(data_30min)
        data_hourly = ensure_timezone(data_hourly)
        data_daily = ensure_timezone(data_daily)

        logger.info(
            f"  ✅ Fetched {len(data_30min)} 30-min, {len(data_hourly)} hourly, "
            f"{len(data_daily)} daily candles"
        )

        return data_30min, data_hourly, data_daily

    except Exception as e:
        logger.error(f"  ❌ Error fetching data for {ticker_symbol}: {e}")
        raise


def generate_prediction_at_time(
    prediction_time: datetime,
    target_hour: int,
    data_30min: pd.DataFrame,
    data_hourly: pd.DataFrame,
    data_daily: pd.DataFrame,
    ticker_id: str,
    ticker_symbol: str
) -> Optional[IntradayPrediction]:
    """
    Generate a single intraday prediction at a specific time.

    Args:
        prediction_time: When the prediction is made (NY timezone, naive)
        target_hour: Target hour for prediction (0-23)
        data_30min: 30-minute OHLC data
        data_hourly: Hourly OHLC data
        data_daily: Daily OHLC data
        ticker_id: Ticker UUID
        ticker_symbol: Ticker symbol

    Returns:
        IntradayPrediction object or None if data unavailable
    """
    eastern = pytz.timezone('US/Eastern')

    # Convert to UTC (handle both naive and aware datetimes)
    if prediction_time.tzinfo is None:
        pred_time_utc = eastern.localize(prediction_time).astimezone(pytz.UTC)
    else:
        pred_time_utc = prediction_time.astimezone(pytz.UTC)

    target_time_ny = prediction_time.replace(hour=target_hour, minute=0, second=0)
    if target_time_ny.tzinfo is None:
        target_time_utc = eastern.localize(target_time_ny).astimezone(pytz.UTC)
    else:
        target_time_utc = target_time_ny.astimezone(pytz.UTC)

    # Get historical data UP TO prediction time (no look-ahead bias)
    hourly_hist = data_hourly[data_hourly.index < pred_time_utc].copy()
    minute_hist = data_30min[data_30min.index < pred_time_utc].copy()
    daily_hist = data_daily[data_daily.index < pred_time_utc].copy()

    # Check if we have sufficient data
    if minute_hist.empty or hourly_hist.empty:
        logger.warning(f"  ⚠️  Insufficient data for {prediction_time}")
        return None

    # Get current price at prediction time
    current_price = float(minute_hist['Close'].iloc[-1])

    try:
        # Calculate reference levels
        ref_levels = calculate_all_reference_levels(
            hourly_hist, minute_hist, daily_hist, pred_time_utc
        )

        # Generate signals
        signals = calculate_signals(current_price, ref_levels)

        # Calculate intraday predictions with time decay
        intraday_preds = calculate_intraday_predictions(
            signals,
            current_price,
            pred_time_utc,
            target_hours=[target_hour]
        )

        if not intraday_preds or target_hour not in intraday_preds:
            logger.warning(f"  ⚠️  No prediction generated for hour {target_hour}")
            return None

        pred_data = intraday_preds[target_hour]

        # Get reference price (open at prediction hour)
        # Find candle that contains prediction_time
        pred_candles = data_30min[
            (data_30min.index >= pred_time_utc - timedelta(minutes=30)) &
            (data_30min.index <= pred_time_utc)
        ]
        reference_price = float(pred_candles['Open'].iloc[0]) if not pred_candles.empty else current_price

        # Check if we can verify (target hour has passed)
        now_utc = datetime.now(pytz.UTC)
        can_verify = now_utc > target_time_utc + timedelta(hours=1)

        target_close_price = None
        actual_result = None
        verified_at = None

        if can_verify:
            # Get target close price
            target_close_candles = data_30min[
                (data_30min.index >= target_time_utc) &
                (data_30min.index < target_time_utc + timedelta(hours=1))
            ]

            if not target_close_candles.empty:
                target_close_price = float(target_close_candles['Close'].iloc[-1])

                # Determine if prediction was correct
                actual_direction = 'BULLISH' if target_close_price > reference_price else 'BEARISH'
                is_correct = pred_data['prediction'] == actual_direction

                actual_result = 'CORRECT' if is_correct else 'WRONG'
                verified_at = now_utc

        # Create IntradayPrediction object
        intraday_prediction = IntradayPrediction(
            ticker_id=ticker_id,
            target_hour=target_hour,
            target_timestamp=target_time_utc,
            prediction_made_at=pred_time_utc,
            prediction=pred_data['prediction'],
            base_confidence=pred_data['base_confidence'],
            decay_factor=pred_data['decay_factor'],
            final_confidence=pred_data['final_confidence'],
            reference_price=reference_price,
            target_close_price=target_close_price,
            actual_result=actual_result,
            verified_at=verified_at,
            metadata={
                'ticker_symbol': ticker_symbol,
                'weighted_score': signals['weighted_score'],
                'normalized_score': signals['normalized_score'],
                'bullish_signals': signals['bullish_count'],
                'total_signals': signals['total_signals'],
                'backfilled': True,
                'backfill_date': datetime.now(pytz.UTC).isoformat()
            }
        )

        return intraday_prediction

    except Exception as e:
        logger.error(f"  ❌ Error generating prediction for {prediction_time}: {e}")
        return None


def backfill_ticker(
    ticker_symbol: str,
    hours_back: int = 24,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    Backfill predictions for a single ticker.

    Args:
        ticker_symbol: Ticker symbol
        hours_back: How many hours back to backfill
        dry_run: If True, don't actually store predictions

    Returns:
        Tuple of (total_generated, total_stored)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🎯 Backfilling {ticker_symbol} - Last {hours_back} hours")
    logger.info(f"{'='*80}")

    # Get ticker from database
    ticker_repo = TickerRepository()
    ticker = ticker_repo.get_ticker_by_symbol(ticker_symbol)

    if not ticker:
        logger.error(f"❌ Ticker {ticker_symbol} not found in database")
        return 0, 0

    logger.info(f"✅ Found ticker: {ticker.name} (ID: {ticker.id})")

    # Fetch historical data
    try:
        data_30min, data_hourly, data_daily = fetch_historical_data(
            ticker_symbol,
            hours_back=hours_back * 2  # Fetch extra for buffer
        )
    except Exception as e:
        logger.error(f"❌ Failed to fetch data: {e}")
        return 0, 0

    # Generate prediction times (every hour from 9 AM to 4 PM market hours)
    eastern = pytz.timezone('US/Eastern')
    now_ny = datetime.now(eastern)
    cutoff_time = now_ny - timedelta(hours=hours_back)

    # All hours: Midnight to 4 PM (16:00)
    market_hours = list(range(0, 17))  # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16

    predictions_to_store = []

    # Generate all prediction timestamps within the backfill period
    # Start from cutoff_time and go forward to now
    current_check = cutoff_time.replace(minute=0, second=0, microsecond=0)

    while current_check <= now_ny:
        # Check if this hour is a market hour
        if current_check.hour in market_hours:
            # Prediction made at :59 minutes of previous hour
            pred_hour = current_check.hour - 1
            if pred_hour < 0:
                # If prediction would be before midnight, skip
                current_check += timedelta(hours=1)
                continue

            pred_minute = 59
            prediction_time = current_check.replace(
                hour=pred_hour,
                minute=pred_minute,
                second=0,
                microsecond=0
            )

            # Target hour is the current check hour
            target_hour = current_check.hour

            logger.info(
                f"  📍 Generating prediction made at {prediction_time.strftime('%Y-%m-%d %H:%M')} "
                f"for target hour {target_hour}:00"
            )

            intraday_pred = generate_prediction_at_time(
                prediction_time=prediction_time,
                target_hour=target_hour,
                data_30min=data_30min,
                data_hourly=data_hourly,
                data_daily=data_daily,
                ticker_id=ticker.id,
                ticker_symbol=ticker_symbol
            )

            if intraday_pred:
                predictions_to_store.append(intraday_pred)
                result_str = f"{intraday_pred.actual_result}" if intraday_pred.actual_result else "PENDING"
                logger.info(
                    f"    ✅ {intraday_pred.prediction} "
                    f"(Conf: {intraday_pred.final_confidence:.1f}%) - {result_str}"
                )

        # Move to next hour
        current_check += timedelta(hours=1)

    logger.info(f"\n📊 Summary for {ticker_symbol}:")
    logger.info(f"  • Total predictions generated: {len(predictions_to_store)}")

    if predictions_to_store:
        verified = [p for p in predictions_to_store if p.actual_result in ['CORRECT', 'WRONG']]
        correct = [p for p in verified if p.actual_result == 'CORRECT']
        accuracy = (len(correct) / len(verified) * 100) if verified else 0

        logger.info(f"  • Verified predictions: {len(verified)}")
        logger.info(f"  • Correct predictions: {len(correct)}")
        logger.info(f"  • Accuracy: {accuracy:.1f}%")

    # Store predictions
    stored_count = 0
    if not dry_run and predictions_to_store:
        try:
            intraday_repo = IntradayPredictionRepository()
            stored_count = intraday_repo.bulk_store_intraday_predictions(predictions_to_store)
            logger.info(f"  ✅ Stored {stored_count} predictions to database")
        except Exception as e:
            logger.error(f"  ❌ Error storing predictions: {e}")
    elif dry_run:
        logger.info(f"  🔍 DRY RUN: Would store {len(predictions_to_store)} predictions")
        stored_count = len(predictions_to_store)

    return len(predictions_to_store), stored_count


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Backfill 24-hour prediction history for NQP'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        default=['NQ=F', 'ES=F', 'BTC-USD'],
        help='Ticker symbols to backfill (default: NQ=F ES=F BTC-USD)'
    )
    parser.add_argument(
        '--hours-back',
        type=int,
        default=24,
        help='How many hours back to backfill (default: 24)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be stored without actually storing'
    )

    args = parser.parse_args()

    logger.info("\n" + "="*80)
    logger.info("🚀 NQP 24-HOUR PREDICTION BACKFILL")
    logger.info("="*80)
    logger.info(f"Tickers: {', '.join(args.tickers)}")
    logger.info(f"Hours Back: {args.hours_back}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info("="*80)

    total_generated = 0
    total_stored = 0

    for ticker_symbol in args.tickers:
        try:
            generated, stored = backfill_ticker(
                ticker_symbol=ticker_symbol,
                hours_back=args.hours_back,
                dry_run=args.dry_run
            )
            total_generated += generated
            total_stored += stored
        except Exception as e:
            logger.error(f"❌ Error processing {ticker_symbol}: {e}")
            continue

    # Print final summary
    logger.info("\n" + "="*80)
    logger.info("📈 BACKFILL COMPLETE")
    logger.info("="*80)
    logger.info(f"Total predictions generated: {total_generated}")
    logger.info(f"Total predictions stored: {total_stored}")
    logger.info("="*80)


if __name__ == '__main__':
    main()
