"""
Block Prediction Service for 7-Block Framework.

Service layer that orchestrates the 7-block prediction generation pipeline.
Handles data fetching, analysis, and storage of block-based predictions.

Implements dependency injection pattern for all external dependencies.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from ..data.fetcher import YahooFinanceDataFetcher
from ..database.repositories.block_prediction_repository import BlockPredictionRepository
from ..database.repositories.ticker_repository import TickerRepository
from ..database.models.block_prediction import BlockPrediction
from ..analysis.volatility import calculate_hourly_volatility
from ..analysis.block_segmentation import BlockSegmentation
from ..analysis.block_prediction_engine import BlockPredictionEngine
from ..core.exceptions import TickerNotFoundException, DataNotFoundException, InsufficientDataException
from .market_status_service import MarketStatusService, MarketStatus

logger = logging.getLogger(__name__)


class BlockPredictionService:
    """
    Service for generating 7-block hourly predictions.

    Orchestrates the complete prediction pipeline:
    1. Fetch intra-hour OHLC bars (from Supabase or yfinance)
    2. Calculate volatility from close-to-close returns
    3. Segment hour into 7 blocks (each ~8.57 minutes)
    4. Apply BlockPredictionEngine to generate prediction
    5. Store prediction with all analysis details
    """

    def __init__(
        self,
        fetcher: YahooFinanceDataFetcher,
        block_prediction_repo: BlockPredictionRepository,
        ticker_repo: Optional[TickerRepository] = None,
        market_status_service: Optional[MarketStatusService] = None
    ):
        """
        Initialize BlockPredictionService with injected dependencies.

        Args:
            fetcher: YahooFinanceDataFetcher for market data retrieval
            block_prediction_repo: BlockPredictionRepository for storing predictions
            ticker_repo: TickerRepository for resolving ticker symbols to UUIDs
            market_status_service: MarketStatusService for market awareness
        """
        self.fetcher = fetcher
        self.block_prediction_repo = block_prediction_repo
        self.ticker_repo = ticker_repo
        self.market_status_service = market_status_service or MarketStatusService()
        logger.debug("BlockPredictionService initialized")

    def _resolve_ticker_uuid(self, ticker_symbol: str) -> str:
        """
        Resolve a ticker symbol to its UUID in Supabase.

        Args:
            ticker_symbol: Ticker symbol (e.g., "NQ=F")

        Returns:
            Ticker UUID if found, otherwise returns the original symbol for fallback to yfinance
        """
        if not self.ticker_repo:
            logger.debug(f"No ticker repository available, using symbol {ticker_symbol} as-is")
            return ticker_symbol

        try:
            tickers = self.ticker_repo.get_all_tickers()
            for ticker_obj in tickers:
                if ticker_obj.symbol == ticker_symbol:
                    logger.debug(f"Resolved {ticker_symbol} to UUID {ticker_obj.id}")
                    return ticker_obj.id

            logger.warning(f"Ticker {ticker_symbol} not found in database, using symbol as fallback")
            return ticker_symbol
        except Exception as e:
            logger.warning(f"Error resolving ticker {ticker_symbol}: {e}, using symbol as fallback")
            return ticker_symbol

    def _resolve_ticker_uuid_strict(self, ticker_symbol: str) -> str:
        """
        Resolve a ticker symbol to its UUID with strict validation (no fallbacks).

        This method is used for critical operations that MUST use Supabase data.
        It fails fast if ticker cannot be resolved, ensuring data integrity.

        Args:
            ticker_symbol: Ticker symbol (e.g., "NQ=F")

        Returns:
            Ticker UUID string

        Raises:
            TickerNotFoundException: If ticker symbol not found in database
            ValueError: If ticker repository is not available
        """
        if not self.ticker_repo:
            logger.error(f"Ticker repository not available - cannot resolve {ticker_symbol}")
            raise ValueError("Ticker repository is required for strict UUID resolution")

        try:
            # Try direct lookup first (more efficient)
            ticker_obj = self.ticker_repo.get_ticker_by_symbol(ticker_symbol)
            if ticker_obj:
                logger.debug(f"Strictly resolved {ticker_symbol} to UUID {ticker_obj.id}")
                return ticker_obj.id

            # If not found, raise exception (no fallback)
            logger.error(f"Ticker {ticker_symbol} not found in database")
            raise TickerNotFoundException(
                f"Ticker symbol '{ticker_symbol}' not found in database. "
                f"Available symbols must be configured in ticker database."
            )
        except TickerNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error during strict UUID resolution for {ticker_symbol}: {e}", exc_info=True)
            raise TickerNotFoundException(
                f"Failed to resolve ticker symbol '{ticker_symbol}': {str(e)}"
            )

    def generate_block_prediction(
        self,
        ticker: str,
        hour_start: datetime,
        bars: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[BlockPrediction]:
        """
        Generate a 7-block prediction for a specific hour.

        This is the main entry point. It:
        1. Strictly resolve ticker symbol to UUID (fail fast if not found)
        2. Fetches intra-hour OHLC bars (if not provided) from Supabase using UUID
        3. Calculates volatility
        4. Segments the hour into 7 blocks
        5. Applies prediction engine to blocks 1-5
        6. Creates and stores BlockPrediction object

        Args:
            ticker: Asset ticker symbol (e.g., "NQ=F", "ES=F", "^FTSE")
            hour_start: Start time of the hour (UTC)
            bars: Optional list of OHLC bars. If None, will be fetched.

        Returns:
            BlockPrediction object with prediction results, or None if generation fails

        Raises:
            TickerNotFoundException: If ticker symbol cannot be resolved to UUID
            DataNotFoundException: If no OHLC data available for the hour
            InsufficientDataException: If data exists but is insufficient for analysis
        """
        try:
            logger.info(f"Generating block prediction for {ticker} at {hour_start.isoformat()}")

            # Step 1: Strictly resolve ticker symbol to UUID BEFORE any data operations
            # This ensures we use Supabase queries with correct UUID format
            try:
                ticker_uuid = self._resolve_ticker_uuid_strict(ticker)
                logger.debug(f"Using UUID {ticker_uuid} for ticker {ticker}")
            except TickerNotFoundException as e:
                logger.error(f"Cannot generate prediction: ticker {ticker} not found in database")
                logger.error(f"Details: {str(e)}")
                return None

            # Step 2: Get OHLC bars for the hour
            if bars is None:
                # Pass both UUID (for Supabase) and symbol (for yfinance fallback)
                bars = self._fetch_hourly_bars(ticker_uuid, ticker, hour_start)

            if not bars:
                logger.warning(f"No bars available for {ticker} (UUID: {ticker_uuid}) at {hour_start}")
                return None

            logger.debug(f"Fetched {len(bars)} bars for {ticker}")

            # Step 3: Calculate volatility from close-to-close returns
            opening_price = float(bars[0]['open'])
            volatility = calculate_hourly_volatility(bars, opening_price)
            logger.debug(f"Calculated volatility: {volatility:.2f} (opening={opening_price:.2f})")

            # Step 4: Segment hour into 7 blocks
            blocks = BlockSegmentation.segment_hour_into_blocks(
                bars=bars,
                hour_start=hour_start,
                volatility=volatility
            )

            if not blocks or len(blocks) < 5:
                logger.warning(f"Insufficient block data: {len(blocks) if blocks else 0} blocks")
                return None

            logger.debug(f"Segmented hour into {len(blocks)} blocks")

            # Step 5: Extract blocks 1-5 for prediction
            blocks_1_5 = [b for b in blocks if 1 <= b.block_number <= 5]

            # Step 6: Generate prediction using decision trees
            prediction_result = BlockPredictionEngine.generate_block_prediction(
                blocks_1_5=blocks_1_5,
                opening_price=opening_price,
                volatility=volatility
            )
            logger.info(
                f"Prediction generated: {prediction_result['prediction']} "
                f"(confidence={prediction_result['confidence']:.1f}%, "
                f"strength={prediction_result['strength']})"
            )

            # Step 7: Create BlockPrediction object with resolved UUID
            block_prediction = self._create_block_prediction(
                ticker_id=ticker_uuid,
                ticker_symbol=ticker,
                hour_start=hour_start,
                opening_price=opening_price,
                volatility=volatility,
                blocks=blocks,
                prediction_result=prediction_result
            )

            # Step 8: Store in database
            stored_prediction = self.block_prediction_repo.store_block_prediction(
                block_prediction
            )
            logger.info(f"Stored block prediction for {ticker} at {hour_start}")

            return stored_prediction

        except TickerNotFoundException as e:
            # Already logged above, just return None for failed ticker resolution
            return None
        except Exception as e:
            logger.error(f"Error generating block prediction for {ticker}: {e}", exc_info=True)
            return None

    def generate_24h_block_predictions(
        self,
        ticker: str,
        date: datetime
    ) -> Dict[str, Any]:
        """
        Generate block predictions for all 24 hours of a trading day.

        Generates predictions for each hour from 00:00 to 23:00 UTC, with detailed
        tracking of which hours succeeded, which were skipped, and why.

        Args:
            ticker: Asset ticker symbol
            date: Trading date (will generate 24 hours starting from this date)

        Returns:
            Dictionary with:
            {
                "predictions": List[BlockPrediction],
                "generated": List[int],  # Hour numbers (0-23) that were successfully generated
                "skipped_future": List[int],  # Hours that are in the future
                "skipped_no_data": List[int],  # Hours where data was unavailable
                "total_generated": int
            }
        """
        logger.info(f"Generating 24h block predictions for {ticker} on {date.date()}")

        result = {
            "predictions": [],
            "generated": [],
            "skipped_future": [],
            "skipped_no_data": []
        }

        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)

        # Generate prediction for each hour (0-23)
        for hour_offset in range(24):
            hour_start = date.replace(hour=hour_offset, minute=0, second=0, microsecond=0)

            # Ensure hour_start is UTC timezone-aware for comparison
            if hour_start.tzinfo is None:
                hour_start = pytz.UTC.localize(hour_start)

            # Skip future hours
            if hour_start > current_time:
                result["skipped_future"].append(hour_offset)
                logger.debug(f"Skipping future hour {hour_offset} for {ticker}")
                continue

            # Attempt generation
            prediction = self.generate_block_prediction(ticker, hour_start)
            if prediction:
                result["predictions"].append(prediction)
                result["generated"].append(hour_offset)
            else:
                result["skipped_no_data"].append(hour_offset)
                logger.warning(f"No data available for {ticker} hour {hour_offset}")

        result["total_generated"] = len(result["generated"])

        logger.info(
            f"Generated {result['total_generated']}/24 predictions for {ticker} "
            f"(skipped_future: {len(result['skipped_future'])}, "
            f"skipped_no_data: {len(result['skipped_no_data'])})"
        )
        return result

    def _fetch_hourly_bars(
        self,
        ticker_id: str,
        ticker_symbol: str,
        hour_start: datetime,
        bar_interval_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLC bars for a specific hour.

        Args:
            ticker_id: Asset ticker UUID (for Supabase queries)
            ticker_symbol: Asset ticker symbol (for yfinance fallback)
            hour_start: Start time of the hour (UTC, naive or aware)
            bar_interval_minutes: Bar size in minutes (default 5-minute bars)

        Returns:
            List of OHLC bar dictionaries within the hour
        """
        # Ensure hour_start is UTC timezone-aware
        if hour_start.tzinfo is None:
            hour_start = pytz.UTC.localize(hour_start)
        elif hour_start.tzinfo != pytz.UTC:
            hour_start = hour_start.astimezone(pytz.UTC)

        hour_end = hour_start + timedelta(hours=1)

        try:
            bars = self.fetcher.fetch_historical_data(
                ticker_id=ticker_id,  # Use UUID for Supabase
                ticker_symbol=ticker_symbol,  # Use symbol for yfinance fallback
                start=hour_start,
                end=hour_end,
                interval='5m'  # Use 5-minute bars for intra-hour analysis
            )

            if not bars:
                logger.warning(f"No bars returned from fetcher for {ticker_symbol} (UUID: {ticker_id})")
                return []

            # Filter bars to only include those within the hour
            # Normalize all timestamps to UTC for consistent comparison
            filtered_bars = []
            for bar in bars:
                bar_timestamp = self._parse_timestamp(bar.get('timestamp'))

                # Ensure bar_timestamp is timezone-aware and in UTC
                if bar_timestamp.tzinfo is None:
                    bar_timestamp = pytz.UTC.localize(bar_timestamp)
                elif bar_timestamp.tzinfo != pytz.UTC:
                    bar_timestamp = bar_timestamp.astimezone(pytz.UTC)

                # Now safe to compare with hour_start (which is already UTC-aware)
                if hour_start <= bar_timestamp < hour_end:
                    # Update the bar's timestamp to normalized UTC version
                    bar['timestamp'] = bar_timestamp
                    filtered_bars.append(bar)

            logger.debug(f"Fetched {len(filtered_bars)} bars for {ticker_symbol} hour {hour_start}")
            return filtered_bars

        except Exception as e:
            logger.error(f"Error fetching bars for {ticker_symbol} (UUID: {ticker_id}): {e}")
            return []

    @staticmethod
    def _parse_timestamp(timestamp_value: Any) -> datetime:
        """
        Parse timestamp from various formats.

        Args:
            timestamp_value: Timestamp in string or datetime format

        Returns:
            datetime object
        """
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        elif isinstance(timestamp_value, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(timestamp_value)
            except (ValueError, AttributeError):
                # Fallback for other string formats
                logger.warning(f"Could not parse timestamp: {timestamp_value}")
                return datetime.now()
        return datetime.now()

    @staticmethod
    def _create_block_prediction(
        ticker_id: str,
        ticker_symbol: str,
        hour_start: datetime,
        opening_price: float,
        volatility: float,
        blocks: List,
        prediction_result: Dict
    ) -> BlockPrediction:
        """
        Create a BlockPrediction object from analysis results.

        Args:
            ticker_id: Asset ticker UUID
            ticker_symbol: Asset ticker symbol for logging
            hour_start: Start time of the hour
            opening_price: Opening price for the hour
            volatility: Calculated hourly volatility
            blocks: List of BlockAnalysis objects (all 7 blocks)
            prediction_result: Dictionary from BlockPredictionEngine

        Returns:
            BlockPrediction object ready for storage
        """
        # Get block data for storage
        block_data = {}
        for block in blocks:
            block_data[str(block.block_number)] = {
                'price_at_end': round(block.price_at_end, 2),
                'deviation_from_open': round(block.deviation_from_open, 2),
                'crosses_open': block.crosses_open,
                'time_above_open': round(block.time_above_open, 3),
                'time_below_open': round(block.time_below_open, 3),
                'high_price': round(block.high_price, 2),
                'low_price': round(block.low_price, 2),
                'volume': block.volume
            }

        # Prediction point is at 5/7 of the hour (~42m 51s)
        prediction_timestamp = BlockSegmentation.get_prediction_point_time(hour_start)

        # Create BlockPrediction object with proper UUID ticker_id
        return BlockPrediction(
            ticker_id=ticker_id,  # Using proper UUID ticker_id
            hour_start_timestamp=hour_start,
            prediction_timestamp=prediction_timestamp,
            prediction=prediction_result['prediction'],
            confidence=prediction_result['confidence'],
            prediction_strength=prediction_result['strength'],
            reference_price=opening_price,  # Hour opening price
            early_bias=prediction_result['early_bias'],
            early_bias_strength=prediction_result['early_bias_strength'],
            has_sustained_counter=prediction_result['has_sustained_counter'],
            counter_direction=prediction_result['counter_direction'],
            deviation_at_5_7=prediction_result['deviation_at_5_7'],
            block_data=block_data,
            reference_levels={
                'opening_price': round(opening_price, 2),
                'volatility': round(volatility, 2)
            },
            volatility=round(volatility, 2)
        )

    def get_hourly_prediction(
        self,
        ticker: str,
        hour_start: datetime
    ) -> Optional[BlockPrediction]:
        """
        Retrieve a previously stored block prediction.

        Args:
            ticker: Asset ticker symbol
            hour_start: Start time of the hour

        Returns:
            BlockPrediction if found, None otherwise
        """
        try:
            # Resolve ticker symbol to UUID (same strict resolution as generation)
            ticker_uuid = self._resolve_ticker_uuid_strict(ticker)
            logger.debug(f"Retrieving prediction for {ticker} (UUID: {ticker_uuid})")

            return self.block_prediction_repo.get_block_prediction_by_hour(
                ticker_id=ticker_uuid,
                hour_start=hour_start
            )
        except TickerNotFoundException as e:
            logger.error(f"Cannot retrieve prediction: ticker {ticker} not found - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving prediction for {ticker}: {e}", exc_info=True)
            return None

    def get_hourly_predictions_24h(
        self,
        ticker: str,
        date: datetime
    ) -> List[BlockPrediction]:
        """
        Retrieve all block predictions for a 24-hour period.

        Args:
            ticker: Asset ticker symbol
            date: Date to retrieve predictions for

        Returns:
            List of BlockPrediction objects for the day
        """
        try:
            # Resolve ticker symbol to UUID (same strict resolution as generation)
            ticker_uuid = self._resolve_ticker_uuid_strict(ticker)
            logger.debug(f"Retrieving 24h predictions for {ticker} (UUID: {ticker_uuid})")

            return self.block_prediction_repo.get_block_predictions_by_date(
                ticker_id=ticker_uuid,
                date=date
            )
        except TickerNotFoundException as e:
            logger.error(f"Cannot retrieve predictions: ticker {ticker} not found - {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving 24h predictions for {ticker}: {e}", exc_info=True)
            return []

    def get_market_aware_prediction(
        self,
        ticker: str,
        hour_start: datetime,
        at_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get block prediction with market status awareness.

        Returns prediction data with metadata about market status.
        During market hours: Returns LIVE current prediction
        During market closure: Returns HISTORICAL prediction from last trading day

        Args:
            ticker: Asset ticker symbol
            hour_start: Start time of the hour to predict
            at_time: Time to check market status (defaults to now)

        Returns:
            Dictionary with prediction data and market metadata:
                {
                    "data_source": "LIVE" | "HISTORICAL",
                    "market_status": MarketStatusInfo dict,
                    "prediction": BlockPrediction object or None,
                    "last_trading_date": date,
                    "next_market_event": {"type": "OPEN" | "CLOSE", "time": datetime}
                }
        """
        try:
            # Get market status
            market_status = self.market_status_service.get_market_status(ticker, at_time)

            if at_time is None:
                at_time = datetime.now(pytz.UTC)

            # Determine if market is open
            is_live = market_status.is_trading

            # Get next market event
            event_type, event_time = self.market_status_service.get_next_market_event(ticker, at_time)

            # Get the prediction
            if is_live:
                # Live market - use current time/prediction
                prediction = self.get_hourly_prediction(ticker, hour_start)
                prediction_date = hour_start.date() if isinstance(hour_start, datetime) else hour_start
            else:
                # Market closed - use last trading date
                last_trading_date = self.market_status_service.get_last_trading_date(ticker, at_time)
                # Adjust hour_start to last trading date
                hour_start_adjusted = hour_start.replace(day=last_trading_date.day,
                                                        month=last_trading_date.month,
                                                        year=last_trading_date.year)
                prediction = self.get_hourly_prediction(ticker, hour_start_adjusted)
                prediction_date = last_trading_date

            return {
                "data_source": "LIVE" if is_live else "HISTORICAL",
                "market_status": {
                    "status": market_status.status.value,
                    "is_trading": market_status.is_trading,
                    "session_type": market_status.session_type.value,
                    "timezone": market_status.timezone,
                    "current_time": market_status.current_time.isoformat(),
                },
                "prediction": prediction,
                "prediction_date": prediction_date.isoformat() if hasattr(prediction_date, 'isoformat') else str(prediction_date),
                "next_market_event": {
                    "type": event_type,
                    "time": event_time.isoformat() if event_time else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting market-aware prediction for {ticker}: {e}", exc_info=True)
            return None

    def get_market_aware_predictions_24h(
        self,
        ticker: str,
        at_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get 24h block predictions with market status awareness.

        Returns predictions with metadata about market status and data source.
        If market is open: Shows today's predictions (LIVE source)
        If market is closed: Shows yesterday's predictions (HISTORICAL source)

        Args:
            ticker: Asset ticker symbol
            at_time: Time to check market status (defaults to now)

        Returns:
            Dictionary with:
                {
                    "data_source": "LIVE" | "HISTORICAL",
                    "market_status": MarketStatusInfo dict,
                    "predictions_date": date of the predictions shown,
                    "predictions": List of BlockPrediction objects,
                    "last_trading_date": last trading date,
                    "next_market_event": {"type": "OPEN" | "CLOSE", "time": datetime}
                }
        """
        try:
            # Get market status
            market_status = self.market_status_service.get_market_status(ticker, at_time)

            if at_time is None:
                at_time = datetime.now(pytz.UTC)

            # Determine if market is open
            is_live = market_status.is_trading

            # Get next market event
            event_type, event_time = self.market_status_service.get_next_market_event(ticker, at_time)

            # Get the last trading date
            last_trading_date = self.market_status_service.get_last_trading_date(ticker, at_time)

            # Get predictions for appropriate date
            if is_live:
                # Live market - use today's predictions
                predictions_date = at_time.date() if isinstance(at_time, datetime) else at_time
            else:
                # Market closed - use last trading date
                predictions_date = last_trading_date

            # Retrieve predictions
            predictions = self.get_hourly_predictions_24h(
                ticker,
                datetime.combine(predictions_date, datetime.min.time())
            )

            return {
                "data_source": "LIVE" if is_live else "HISTORICAL",
                "market_status": {
                    "status": market_status.status.value,
                    "is_trading": market_status.is_trading,
                    "session_type": market_status.session_type.value,
                    "timezone": market_status.timezone,
                    "current_time": market_status.current_time.isoformat(),
                },
                "predictions_date": predictions_date.isoformat(),
                "predictions": predictions,
                "last_trading_date": last_trading_date.isoformat(),
                "next_market_event": {
                    "type": event_type,
                    "time": event_time.isoformat() if event_time else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting market-aware 24h predictions for {ticker}: {e}", exc_info=True)
            return {
                "data_source": "ERROR",
                "error": str(e),
                "predictions": []
            }
