"""
Market Aggregation Service.

Handles batch processing of multiple tickers and market-wide operations.
Orchestrates cache service, prediction calculation service, and formatting service.
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class AggregationService:
    """
    Service for aggregating market data across multiple tickers.

    Handles:
    1. Batch processing of multiple tickers
    2. Multi-ticker market summary
    3. Performance statistics across tickers
    4. Market-wide condition analysis
    """

    def __init__(
        self,
        cache_service: 'CacheService',
        prediction_service: 'PredictionCalculationService',
        formatting_service: 'FormattingService',
        ticker_repo: 'TickerRepository',
        intraday_repo: 'IntradayPredictionRepository'
    ):
        """
        Initialize AggregationService with injected dependencies.

        Args:
            cache_service: CacheService for database-first caching
            prediction_service: PredictionCalculationService for fresh calculations
            formatting_service: FormattingService for response formatting
            ticker_repo: TickerRepository for getting enabled tickers
            intraday_repo: IntradayPredictionRepository for accuracy metrics
        """
        self.cache_service = cache_service
        self.prediction_service = prediction_service
        self.formatting_service = formatting_service
        self.ticker_repo = ticker_repo
        self.intraday_repo = intraday_repo

    def analyze_all_tickers(
        self,
        tickers: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch and calculate market data for multiple instruments.

        Uses database-first approach for improved performance.

        Args:
            tickers: List of ticker symbols to analyze.
                    If None, loads enabled tickers from database.

        Returns:
            Dictionary with prediction data for each ticker
        """
        try:
            # Get tickers from database if not specified
            if tickers is None:
                try:
                    ticker_objects = self.ticker_repo.get_enabled_tickers()
                    tickers = [t.symbol for t in ticker_objects]
                    logger.info(f"Loaded {len(tickers)} enabled tickers from database: {tickers}")
                except Exception as e:
                    logger.warning(f"Failed to load tickers from database: {e}")
                    tickers = ['NQ=F', 'ES=F']  # Fallback to default
            else:
                logger.info(f"Analyzing {len(tickers)} specified tickers: {tickers}")

            result = {}

            # Target tickers for 24h history feature
            history_tickers = ['NQ=F', 'ES=F', 'BTC-USD', '^FTSE']

            # Process each ticker
            for ticker in tickers:
                ticker_data = self._process_single_ticker(ticker)

                if not ticker_data:
                    result[ticker] = {'error': 'Failed to fetch data'}
                    continue

                # Add daily accuracy for target tickers (from intraday predictions)
                if ticker in history_tickers:
                    try:
                        daily_accuracy = self._get_daily_accuracy(ticker)
                        if daily_accuracy:
                            ticker_data['daily_accuracy'] = daily_accuracy
                            logger.debug(f"Added daily_accuracy to {ticker}")
                    except Exception as e:
                        logger.warning(f"Failed to get daily accuracy for {ticker}: {e}")
                        # Continue without daily accuracy

                result[ticker] = ticker_data

            logger.info(f"Completed analysis for {len(result)} tickers")
            return result

        except Exception as e:
            logger.error(f"Error analyzing tickers: {str(e)}", exc_info=True)
            return {}

    def get_market_summary(
        self,
        tickers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics across multiple tickers.

        Analyzes market-wide conditions and aggregates statistics.

        Args:
            tickers: List of ticker symbols. If None, uses enabled tickers.

        Returns:
            Market summary dict with aggregated statistics
        """
        try:
            # Get all ticker data
            all_data = self.analyze_all_tickers(tickers)

            if not all_data:
                logger.warning("No ticker data available for market summary")
                return {
                    'error': 'No data available',
                    'timestamp': None,
                    'ticker_count': 0
                }

            # Aggregate statistics
            summary = self._aggregate_statistics(all_data)

            logger.info(f"Generated market summary for {summary['ticker_count']} tickers")
            return summary

        except Exception as e:
            logger.error(f"Error generating market summary: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def get_batch_response(
        self,
        tickers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get formatted batch response with all ticker data.

        Args:
            tickers: List of ticker symbols. If None, uses enabled tickers.

        Returns:
            Formatted batch response ready for API
        """
        try:
            all_data = self.analyze_all_tickers(tickers)
            batch_response = self.formatting_service.format_batch_response(all_data)
            return batch_response

        except Exception as e:
            logger.error(f"Error creating batch response: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'count': 0,
                'data': {},
                'status': 'error'
            }

    def force_refresh_ticker(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Force a fresh calculation from yfinance, bypassing database cache.

        Args:
            ticker_symbol: Ticker symbol to refresh

        Returns:
            Freshly calculated market data
        """
        try:
            logger.info(f"Force refresh requested for {ticker_symbol}")
            return self.prediction_service.calculate_fresh_data(ticker_symbol)

        except Exception as e:
            logger.error(f"Error force refreshing {ticker_symbol}: {str(e)}", exc_info=True)
            return None

    def _process_single_ticker(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Process data for a single ticker using cache-first approach.

        Args:
            ticker_symbol: Ticker symbol

        Returns:
            Formatted prediction data or None if processing fails
        """
        try:
            # Try cache first
            cached = self.cache_service.get_cached_prediction(ticker_symbol)
            if cached:
                logger.debug(f"Retrieved {ticker_symbol} from cache")
                return cached

            # Cache miss - calculate fresh
            fresh = self.prediction_service.calculate_fresh_data(ticker_symbol)
            if fresh:
                logger.debug(f"Calculated fresh data for {ticker_symbol}")
                return fresh

            logger.warning(f"Failed to get data for {ticker_symbol}")
            return None

        except Exception as e:
            logger.error(f"Error processing {ticker_symbol}: {str(e)}", exc_info=True)
            return None

    def _get_daily_accuracy(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get daily accuracy metrics for a ticker.

        Args:
            ticker_symbol: Ticker symbol

        Returns:
            Daily accuracy dict or None if not available
        """
        try:
            ticker_obj = self.ticker_repo.get_ticker_by_symbol(ticker_symbol)
            if not ticker_obj:
                logger.debug(f"Ticker object not found for {ticker_symbol}")
                return None

            daily_accuracy = self.intraday_repo.get_daily_intraday_accuracy(ticker_obj.id)
            return daily_accuracy if daily_accuracy else None

        except Exception as e:
            logger.warning(f"Failed to get daily accuracy for {ticker_symbol}: {e}")
            return None

    def _aggregate_statistics(self, all_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate statistics across all ticker data.

        Args:
            all_data: Dict of ticker -> prediction data

        Returns:
            Aggregated statistics dict
        """
        summary = {
            'ticker_count': 0,
            'bullish_count': 0,
            'bearish_count': 0,
            'neutral_count': 0,
            'average_confidence': 0.0,
            'average_weighted_score': 0.0,
            'from_cache': 0,
            'from_yfinance': 0,
            'errors': 0,
            'by_source': {
                'database': 0,
                'yfinance': 0,
                'error': 0
            },
            'market_consensus': 'UNKNOWN'
        }

        total_confidence = 0.0
        total_score = 0.0
        predictions = []

        for ticker, data in all_data.items():
            if 'error' in data:
                summary['errors'] += 1
                summary['by_source']['error'] += 1
                continue

            summary['ticker_count'] += 1

            # Track source
            source = data.get('source', 'unknown')
            if source == 'database':
                summary['from_cache'] += 1
                summary['by_source']['database'] += 1
            elif source == 'yfinance':
                summary['from_yfinance'] += 1
                summary['by_source']['yfinance'] += 1

            # Aggregate prediction counts
            prediction = data.get('prediction', 'NEUTRAL').upper()
            if prediction == 'BULLISH':
                summary['bullish_count'] += 1
            elif prediction == 'BEARISH':
                summary['bearish_count'] += 1
            else:
                summary['neutral_count'] += 1

            predictions.append(prediction)

            # Aggregate confidence and score
            confidence = data.get('confidence', 0.0)
            weighted_score = data.get('weighted_score', 0.0)
            total_confidence += confidence
            total_score += weighted_score

        # Calculate averages
        if summary['ticker_count'] > 0:
            summary['average_confidence'] = round(total_confidence / summary['ticker_count'], 2)
            summary['average_weighted_score'] = round(total_score / summary['ticker_count'], 2)

            # Determine market consensus
            bullish_ratio = summary['bullish_count'] / summary['ticker_count']
            bearish_ratio = summary['bearish_count'] / summary['ticker_count']

            if bullish_ratio > 0.6:
                summary['market_consensus'] = 'BULLISH'
            elif bearish_ratio > 0.6:
                summary['market_consensus'] = 'BEARISH'
            else:
                summary['market_consensus'] = 'MIXED'

        return summary
