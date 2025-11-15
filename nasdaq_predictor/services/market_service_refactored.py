"""
Market Service - Refactored for Phase 2.

Orchestrates all market analysis operations using split services with DI.

Responsibilities:
- Route requests to appropriate services (cache vs. calculation)
- Coordinate batch processing across multiple tickers
- Provide high-level market analysis API

Dependencies (Injected):
- CacheService: Database-first prediction caching
- PredictionCalculationService: Fresh yfinance calculations
- FormattingService: Response formatting
- AggregationService: Multi-ticker batch processing
"""

import logging
from typing import Optional, Dict, Any, List

from .cache_service import CacheService
from .prediction_calculation_service import PredictionCalculationService
from .formatting_service import FormattingService
from .aggregation_service import AggregationService

logger = logging.getLogger(__name__)


class MarketAnalysisService:
    """
    Refactored Market Analysis Service using split service architecture.

    Now uses composition of focused services instead of monolithic methods:
    1. CacheService - handles database prediction retrieval
    2. PredictionCalculationService - handles yfinance calculations
    3. FormattingService - handles response formatting
    4. AggregationService - handles batch and multi-ticker operations

    This service acts as a facade/orchestrator for these services.
    """

    def __init__(
        self,
        cache_service: CacheService,
        prediction_service: PredictionCalculationService,
        formatting_service: FormattingService,
        aggregation_service: AggregationService
    ):
        """
        Initialize refactored MarketAnalysisService with injected services.

        Args:
            cache_service: CacheService for database prediction retrieval
            prediction_service: PredictionCalculationService for fresh calculations
            formatting_service: FormattingService for response formatting
            aggregation_service: AggregationService for batch processing
        """
        self.cache_service = cache_service
        self.prediction_service = prediction_service
        self.formatting_service = formatting_service
        self.aggregation_service = aggregation_service
        logger.info("MarketAnalysisService initialized with injected services (refactored)")

    def process_ticker_data(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Process market data for a single ticker symbol.

        Uses database-first approach:
        1. Try to get latest prediction from database (if < 15 min old)
        2. If not available, fetch from yfinance and calculate

        This is the main entry point for single-ticker analysis.

        Args:
            ticker_symbol: The ticker to process

        Returns:
            Dictionary with processed market data or None if processing fails
        """
        try:
            # Try cache first
            cached = self.cache_service.get_cached_prediction(ticker_symbol)
            if cached:
                logger.info(f"Returning {ticker_symbol} data from cache (database-first)")
                return cached

            # Cache miss - calculate fresh
            fresh = self.prediction_service.calculate_fresh_data(ticker_symbol)
            if fresh:
                logger.info(f"Calculated fresh data for {ticker_symbol} from yfinance")
                return fresh

            # Both cache and fresh calculation failed
            logger.error(f"Failed to get data for {ticker_symbol} from cache or yfinance")
            return None

        except Exception as e:
            logger.error(f"Error processing ticker {ticker_symbol}: {str(e)}", exc_info=True)
            return None

    def get_market_data(self, tickers: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Fetch and calculate market data for multiple instruments.

        Uses database-first approach for improved performance.

        Delegates to AggregationService for batch processing.

        Args:
            tickers: List of ticker symbols to analyze.
                    If None, loads enabled tickers from database.

        Returns:
            Dictionary with prediction data for each ticker
        """
        try:
            return self.aggregation_service.analyze_all_tickers(tickers)

        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}", exc_info=True)
            return {}

    def get_market_summary(self, tickers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get summary statistics across multiple tickers.

        Analyzes market-wide conditions and aggregates statistics.

        Delegates to AggregationService for summary generation.

        Args:
            tickers: List of ticker symbols. If None, uses enabled tickers.

        Returns:
            Market summary dict with aggregated statistics
        """
        try:
            return self.aggregation_service.get_market_summary(tickers)

        except Exception as e:
            logger.error(f"Error getting market summary: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def get_batch_response(self, tickers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get formatted batch response with all ticker data.

        Delegates to AggregationService for batch response generation.

        Args:
            tickers: List of ticker symbols. If None, uses enabled tickers.

        Returns:
            Formatted batch response ready for API
        """
        try:
            return self.aggregation_service.get_batch_response(tickers)

        except Exception as e:
            logger.error(f"Error creating batch response: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'count': 0,
                'data': {},
                'status': 'error'
            }

    def force_refresh(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Force a fresh calculation from yfinance, bypassing database cache.

        Delegates to AggregationService for force refresh.

        Args:
            ticker_symbol: Ticker symbol to refresh

        Returns:
            Freshly calculated market data
        """
        try:
            logger.info(f"Force refresh requested for {ticker_symbol}")
            return self.aggregation_service.force_refresh_ticker(ticker_symbol)

        except Exception as e:
            logger.error(f"Error force refreshing {ticker_symbol}: {str(e)}", exc_info=True)
            return None


# Backward compatibility: Keep the old class name available
__all__ = ['MarketAnalysisService']
