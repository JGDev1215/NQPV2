#!/usr/bin/env python3
"""
Validation script to test the modular structure
"""
import sys

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing module imports...")

    tests = [
        ("Config", "from nasdaq_predictor.config import settings"),
        ("Models", "from nasdaq_predictor.models import market_data"),
        ("Cache", "from nasdaq_predictor.utils.cache import ThreadSafeCache"),
        ("Timezone", "from nasdaq_predictor.utils.timezone import ensure_utc"),
        ("Market Status", "from nasdaq_predictor.utils.market_status import get_market_status"),
        ("Data Fetcher", "from nasdaq_predictor.data.fetcher import YahooFinanceDataFetcher"),
        ("Data Processor", "from nasdaq_predictor.data.processor import filter_trading_session_data"),
        ("Reference Levels", "from nasdaq_predictor.analysis.reference_levels import calculate_all_reference_levels"),
        ("Signals", "from nasdaq_predictor.analysis.signals import calculate_signals"),
        ("Confidence", "from nasdaq_predictor.analysis.confidence import calculate_confidence_horizons"),
        ("Volatility", "from nasdaq_predictor.analysis.volatility import calculate_volatility"),
        ("Risk Metrics", "from nasdaq_predictor.analysis.risk_metrics import calculate_risk_metrics"),
        ("Sessions", "from nasdaq_predictor.analysis.sessions import get_all_session_ranges"),
        ("Market Service", "from nasdaq_predictor.services.market_service_refactored import MarketAnalysisService"),
        ("API Routes", "from nasdaq_predictor.api.routes import api_bp"),
    ]

    failed = []
    passed = []

    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            passed.append(name)
            print(f"  ✓ {name}")
        except Exception as e:
            failed.append((name, str(e)))
            print(f"  ✗ {name}: {e}")

    print(f"\n{'='*60}")
    print(f"Results: {len(passed)} passed, {len(failed)} failed")
    print(f"{'='*60}")

    if failed:
        print("\nFailed imports:")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return False
    else:
        print("\n✓ All imports successful!")
        return True

def test_configuration():
    """Test that configuration is valid"""
    print("\nTesting configuration...")

    try:
        from nasdaq_predictor.config.settings import WEIGHTS, ALLOWED_TICKERS, TRADING_SESSIONS

        # Check weights sum to 1.0
        weights_sum = sum(WEIGHTS.values())
        assert abs(weights_sum - 1.0) < 0.001, f"Weights sum to {weights_sum}, expected 1.0"
        print(f"  ✓ Weights sum to 1.0")

        # Check tickers
        assert len(ALLOWED_TICKERS) > 0, "No tickers defined"
        print(f"  ✓ Tickers configured: {ALLOWED_TICKERS}")

        # Check trading sessions
        for ticker in ['NQ=F', '^NDX']:
            assert ticker in TRADING_SESSIONS, f"Trading session not defined for {ticker}"
        print(f"  ✓ Trading sessions configured")

        return True

    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False

def test_dataclasses():
    """Test that dataclasses can be instantiated"""
    print("\nTesting dataclasses...")

    try:
        from nasdaq_predictor.models.market_data import (
            ReferenceLevels, SessionRange, SignalData,
            ConfidenceHorizon, Volatility, RiskMetrics, MarketStatus
        )

        # Test ReferenceLevels
        ref_levels = ReferenceLevels(daily_open=100.0, hourly_open=105.0)
        assert ref_levels.daily_open == 100.0
        print(f"  ✓ ReferenceLevels dataclass works")

        # Test SessionRange
        session = SessionRange(high=110.0, low=100.0, range=10.0)
        assert session.range == 10.0
        print(f"  ✓ SessionRange dataclass works")

        # Test MarketStatus
        status = MarketStatus(status='OPEN', next_open=None)
        assert status.status == 'OPEN'
        print(f"  ✓ MarketStatus dataclass works")

        return True

    except Exception as e:
        print(f"  ✗ Dataclass error: {e}")
        return False

def test_utilities():
    """Test utility functions"""
    print("\nTesting utilities...")

    try:
        from nasdaq_predictor.utils.cache import ThreadSafeCache
        from datetime import datetime

        # Test cache
        cache = ThreadSafeCache()
        cache.set("test_data", datetime.now())
        data, timestamp = cache.get()
        assert data == "test_data"
        print(f"  ✓ ThreadSafeCache works")

        from nasdaq_predictor.utils.timezone import ensure_utc
        import pytz

        # Test timezone
        dt = datetime(2024, 1, 1, 12, 0, 0)
        dt_utc = ensure_utc(dt)
        assert dt_utc.tzinfo == pytz.UTC
        print(f"  ✓ Timezone utilities work")

        return True

    except Exception as e:
        print(f"  ✗ Utility error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("="*60)
    print("NASDAQ Predictor - Modular Structure Validation")
    print("="*60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_configuration()))
    results.append(("Dataclasses", test_dataclasses()))
    results.append(("Utilities", test_utilities()))

    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {name}")

    all_passed = all(passed for _, passed in results)

    print(f"{'='*60}")
    if all_passed:
        print("\n🎉 All validation tests passed!")
        print("\nThe modular structure is working correctly.")
        print("\nYou can now run the application:")
        print("  python app.py")
        return 0
    else:
        print("\n❌ Some validation tests failed.")
        print("\nPlease review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
