"""
Test script to verify the implementation of:
1. Real reference levels (not dummy data)
2. Prediction verification system
3. Accuracy calculation

Run this after the scheduler has been running for at least 30 minutes.
"""

import sys
import logging
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/soonjeongguan/Desktop/ClaudeCode/NQP')

from nasdaq_predictor.database.repositories.ticker_repository import TickerRepository
from nasdaq_predictor.database.repositories.market_data_repository import MarketDataRepository
from nasdaq_predictor.database.repositories.prediction_repository import PredictionRepository
from nasdaq_predictor.services.data_sync_service import DataSyncService
from nasdaq_predictor.services.verification_service import PredictionVerificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_reference_levels():
    """Test that reference levels are calculated with real data."""
    print("=" * 80)
    print("TEST 1: Reference Levels Calculation (Real vs Dummy)")
    print("=" * 80)

    try:
        ticker_repo = TickerRepository()
        sync_service = DataSyncService()

        # Get first enabled ticker
        tickers = ticker_repo.get_enabled_tickers()
        if not tickers:
            print("⚠ No tickers found")
            return False

        ticker = tickers[0]
        print(f"Testing with ticker: {ticker.symbol}")

        # Calculate reference levels
        ref_levels = sync_service._calculate_reference_levels_dict(ticker.id, ticker.symbol)

        if not ref_levels:
            print("✗ FAILED: No reference levels returned")
            return False

        # Check if we're getting dummy values (15200.0, 15210.0, etc.)
        dummy_values = [15200.0, 15210.0, 15205.0, 15215.0, 15250.0]
        is_dummy = any(abs(v - dummy) < 0.01 for v in ref_levels.values() for dummy in dummy_values)

        if is_dummy:
            print("✗ FAILED: Still using DUMMY reference levels!")
            print(f"  Values: {list(ref_levels.values())[:5]}")
            return False
        else:
            print("✓ SUCCESS: Using REAL reference levels")
            print(f"  Sample values: {list(ref_levels.items())[:3]}")
            print(f"  Total levels calculated: {len(ref_levels)}")
            return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prediction_with_baseline():
    """Test that predictions store baseline_price in metadata."""
    print("\n" + "=" * 80)
    print("TEST 2: Prediction Stores Baseline Price")
    print("=" * 80)

    try:
        ticker_repo = TickerRepository()
        prediction_repo = PredictionRepository()

        # Get first enabled ticker
        tickers = ticker_repo.get_enabled_tickers()
        if not tickers:
            print("⚠ No tickers found")
            return False

        ticker = tickers[0]
        print(f"Checking predictions for: {ticker.symbol}")

        # Get latest prediction
        latest = prediction_repo.get_latest_prediction(ticker.id)

        if not latest:
            print("⚠ No predictions found yet (scheduler hasn't run)")
            print("  Wait for prediction job to run (every 15 min)")
            return None

        # Check if metadata has baseline_price
        if not latest.metadata or 'baseline_price' not in latest.metadata:
            print("✗ FAILED: Prediction missing baseline_price in metadata")
            print(f"  Metadata: {latest.metadata}")
            return False

        baseline_price = latest.metadata['baseline_price']
        print("✓ SUCCESS: Prediction has baseline_price")
        print(f"  Prediction ID: {latest.id}")
        print(f"  Timestamp: {latest.timestamp}")
        print(f"  Prediction: {latest.prediction}")
        print(f"  Baseline Price: ${baseline_price:.2f}")
        print(f"  Market Status: {latest.market_status}")
        print(f"  Volatility: {latest.volatility_level}")
        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_verification_system():
    """Test that verification system works."""
    print("\n" + "=" * 80)
    print("TEST 3: Prediction Verification System")
    print("=" * 80)

    try:
        ticker_repo = TickerRepository()
        prediction_repo = PredictionRepository()

        # Get first enabled ticker
        tickers = ticker_repo.get_enabled_tickers()
        if not tickers:
            print("⚠ No tickers found")
            return False

        ticker = tickers[0]
        print(f"Checking verification for: {ticker.symbol}")

        # Get predictions from last 30 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=30)

        response = (
            prediction_repo.client.table(prediction_repo.predictions_table)
            .select('*')
            .eq('ticker_id', ticker.id)
            .gte('timestamp', cutoff.isoformat())
            .order('timestamp', desc=True)
            .limit(10)
            .execute()
        )

        predictions = response.data if response.data else []

        if not predictions:
            print("⚠ No recent predictions found")
            print("  Wait for prediction job to run")
            return None

        print(f"\nFound {len(predictions)} predictions in last 30 minutes:")

        verified_count = 0
        pending_count = 0

        for p in predictions:
            actual_result = p.get('actual_result')
            timestamp = datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00'))
            age_minutes = (datetime.utcnow().replace(tzinfo=timestamp.tzinfo) - timestamp).total_seconds() / 60

            status = "✓ VERIFIED" if actual_result else "⏳ PENDING"
            if actual_result:
                verified_count += 1
            else:
                pending_count += 1

            print(f"\n  {status}")
            print(f"    Time: {timestamp} ({age_minutes:.1f} min ago)")
            print(f"    Prediction: {p['prediction']}")
            print(f"    Result: {actual_result or 'Not yet verified'}")
            if actual_result:
                print(f"    Price Change: {p.get('actual_price_change', 'N/A')}")

        print(f"\nSummary:")
        print(f"  Verified: {verified_count}")
        print(f"  Pending: {pending_count}")

        if verified_count > 0:
            print("\n✓ SUCCESS: Verification system is working!")
            return True
        elif pending_count > 0:
            print("\n⏳ Verification pending (predictions not old enough yet)")
            print("  Wait 15+ minutes after prediction time")
            return None
        else:
            print("\n⚠ No predictions to verify")
            return None

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_accuracy_calculation():
    """Test that accuracy calculation returns real data."""
    print("\n" + "=" * 80)
    print("TEST 4: Accuracy Calculation (Real vs Placeholder)")
    print("=" * 80)

    try:
        ticker_repo = TickerRepository()
        prediction_repo = PredictionRepository()

        # Get first enabled ticker
        tickers = ticker_repo.get_enabled_tickers()
        if not tickers:
            print("⚠ No tickers found")
            return False

        ticker = tickers[0]
        print(f"Calculating accuracy for: {ticker.symbol}")

        # Get accuracy for last 30 days
        accuracy = prediction_repo.get_prediction_accuracy(ticker.id, days=30)

        print("\nAccuracy Metrics:")
        print(f"  Total Predictions: {accuracy['total_predictions']}")

        # Check if we have any predictions at all
        if accuracy['total_predictions'] == 0:
            print("\n⚠ No predictions found")
            print("  Wait for prediction job to run (every 15 min)")
            return None

        print(f"  Verified: {accuracy.get('verified_predictions', 0)}")
        print(f"  Pending: {accuracy.get('pending_verification', 0)}")
        print(f"  Accuracy Rate: {accuracy['accuracy_rate']}%")
        print(f"  Bullish Accuracy: {accuracy.get('bullish_accuracy', 0)}%")
        print(f"  Bearish Accuracy: {accuracy.get('bearish_accuracy', 0)}%")
        print(f"  Neutral Accuracy: {accuracy.get('neutral_accuracy', 0)}%")
        print(f"  Avg Confidence: {accuracy['avg_confidence']}%")

        # Check if we have verified predictions
        if accuracy.get('verified_predictions', 0) == 0:
            print("\n⚠ No verified predictions yet")
            print("  Wait for predictions to be verified (15+ min after creation)")
            return None

        # Check if accuracy is calculated (not 0.0 placeholder)
        if accuracy['accuracy_rate'] == 0.0 and accuracy['verified_predictions'] > 0:
            print("\n✗ FAILED: Accuracy is 0.0 despite having verified predictions")
            return False

        print("\n✓ SUCCESS: Accuracy calculation working!")
        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("NQP IMPLEMENTATION VALIDATION TESTS")
    print("=" * 80)
    print()

    results = {
        'reference_levels': test_reference_levels(),
        'baseline_price': test_prediction_with_baseline(),
        'verification': test_verification_system(),
        'accuracy': test_accuracy_calculation()
    }

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⏳ PENDING"

        print(f"{status} - {test_name.replace('_', ' ').title()}")

    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    pending = sum(1 for r in results.values() if r is None)

    print("\n" + "-" * 80)
    print(f"Passed: {passed} | Failed: {failed} | Pending: {pending}")
    print("=" * 80)

    if failed > 0:
        print("\n⚠ Some tests failed. Check the error messages above.")
        sys.exit(1)
    elif pending > 0:
        print("\n⏳ Some tests are pending. Wait for scheduler jobs to run.")
        sys.exit(0)
    else:
        print("\n✓ All tests passed! Implementation is working correctly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
