"""
Block Segmentation Module for 7-Block Analysis Framework.

Divides hourly OHLC data into 7 equal blocks and analyzes each block
for the prediction model.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BlockAnalysis:
    """Analysis results for a single block."""
    block_number: int                    # 1-7
    start_time: datetime                 # Block start timestamp
    end_time: datetime                   # Block end timestamp
    price_at_end: float                  # Closing price of block
    deviation_from_open: float           # (close - open) / volatility (std devs)
    crosses_open: bool                   # Did high/low cross open?
    time_above_open: float               # Fraction above open [0, 1]
    time_below_open: float               # Fraction below open [0, 1]

    # OHLC data for the block
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        # Convert datetime to ISO strings
        if isinstance(data['start_time'], datetime):
            data['start_time'] = data['start_time'].isoformat()
        if isinstance(data['end_time'], datetime):
            data['end_time'] = data['end_time'].isoformat()
        return data

    def __repr__(self) -> str:
        return (
            f"<Block{self.block_number} "
            f"close={self.price_at_end:.2f} "
            f"dev={self.deviation_from_open:.2f}σ "
            f"above={self.time_above_open:.1%}>"
        )


class BlockSegmentation:
    """
    Segments hourly OHLC data into 7 equal blocks for analysis.

    Each hour (60 minutes) is divided into 7 blocks of ~8.57 minutes each.
    Analysis includes price deviations, open crossings, and time spent
    above/below the opening price.
    """

    # Block constants
    BLOCKS_PER_HOUR = 7
    PREDICTION_POINT = 5 / 7  # Predict at 5/7 point (71.4% through hour)
    BLOCK_FRACTION = 1 / 7    # Each block is 1/7 of the hour

    @staticmethod
    def segment_hour_into_blocks(
        bars: List[Dict[str, Any]],
        hour_start: datetime,
        volatility: float
    ) -> List[BlockAnalysis]:
        """
        Segment hourly data into 7 blocks and analyze each.

        Args:
            bars: List of OHLC bars (each bar is a dict with: timestamp, open, high, low, close, volume)
            hour_start: Start time of the hour (UTC)
            volatility: Volatility in price units (std dev normalized)

        Returns:
            List of BlockAnalysis objects (7 blocks)

        Raises:
            ValueError: If bars list is empty or volatility is invalid
        """
        if not bars:
            raise ValueError("Bars list cannot be empty")

        if volatility <= 0:
            raise ValueError(f"Volatility must be positive: {volatility}")

        # Convert bars to DataFrame for easier manipulation
        df = pd.DataFrame(bars)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Get opening price from first bar
        opening_price = float(df['open'].iloc[0])

        # Calculate block boundaries
        hour_end = hour_start + timedelta(hours=1)
        block_duration = timedelta(hours=1 / BlockSegmentation.BLOCKS_PER_HOUR)

        blocks = []

        for block_num in range(1, BlockSegmentation.BLOCKS_PER_HOUR + 1):
            block_start = hour_start + (block_num - 1) * block_duration
            block_end = block_start + block_duration

            # Get bars within this block
            block_bars = df[
                (df['timestamp'] >= block_start) &
                (df['timestamp'] < block_end)
            ].copy()

            if block_bars.empty:
                logger.warning(
                    f"No data in block {block_num} "
                    f"({block_start.isoformat()} to {block_end.isoformat()})"
                )
                continue

            # Calculate block metrics
            price_at_end = float(block_bars['close'].iloc[-1])
            high = float(block_bars['high'].max())
            low = float(block_bars['low'].min())
            volume = int(block_bars['volume'].sum())

            # Deviation from opening price (in standard deviations)
            deviation = (price_at_end - opening_price) / volatility

            # Check if price crosses opening level
            crosses_open = (low <= opening_price <= high)

            # Calculate time above/below open
            bars_above = (block_bars['close'] > opening_price).sum()
            bars_below = (block_bars['close'] < opening_price).sum()
            bars_at_open = (block_bars['close'] == opening_price).sum()
            total_bars = len(block_bars)

            time_above = bars_above / total_bars if total_bars > 0 else 0.0
            time_below = bars_below / total_bars if total_bars > 0 else 0.0

            block_analysis = BlockAnalysis(
                block_number=block_num,
                start_time=block_start,
                end_time=block_end,
                price_at_end=price_at_end,
                deviation_from_open=deviation,
                crosses_open=crosses_open,
                time_above_open=time_above,
                time_below_open=time_below,
                open_price=float(block_bars['open'].iloc[0]),
                high_price=high,
                low_price=low,
                close_price=price_at_end,
                volume=volume
            )

            blocks.append(block_analysis)

        if len(blocks) != BlockSegmentation.BLOCKS_PER_HOUR:
            logger.warning(
                f"Expected {BlockSegmentation.BLOCKS_PER_HOUR} blocks, "
                f"got {len(blocks)}"
            )

        return blocks

    @staticmethod
    def get_blocks_1_5(blocks: List[BlockAnalysis]) -> List[BlockAnalysis]:
        """
        Get blocks 1-5 (the analysis period before prediction point).

        Args:
            blocks: Full list of 7 blocks

        Returns:
            Blocks 1-5 for analysis
        """
        return [b for b in blocks if 1 <= b.block_number <= 5]

    @staticmethod
    def get_blocks_6_7(blocks: List[BlockAnalysis]) -> List[BlockAnalysis]:
        """
        Get blocks 6-7 (the unknown future period being predicted).

        Args:
            blocks: Full list of 7 blocks

        Returns:
            Blocks 6-7 for verification
        """
        return [b for b in blocks if 6 <= b.block_number <= 7]

    @staticmethod
    def get_block_by_number(blocks: List[BlockAnalysis], number: int) -> BlockAnalysis:
        """
        Get a specific block by number.

        Args:
            blocks: List of blocks
            number: Block number (1-7)

        Returns:
            BlockAnalysis object

        Raises:
            ValueError: If block number not found
        """
        for block in blocks:
            if block.block_number == number:
                return block
        raise ValueError(f"Block {number} not found")

    @staticmethod
    def get_prediction_point_time(hour_start: datetime) -> datetime:
        """
        Calculate the exact time of the 5/7 prediction point.

        Args:
            hour_start: Start of the hour

        Returns:
            Datetime of the 5/7 point (~42m 51s into the hour)
        """
        prediction_offset = timedelta(hours=BlockSegmentation.PREDICTION_POINT)
        return hour_start + prediction_offset

    @staticmethod
    def blocks_to_dict(blocks: List[BlockAnalysis]) -> Dict[int, Dict[str, Any]]:
        """
        Convert blocks to dictionary format for storage.

        Args:
            blocks: List of BlockAnalysis objects

        Returns:
            Dictionary with block_number as key
        """
        return {
            block.block_number: block.to_dict()
            for block in blocks
        }

    @staticmethod
    def validate_blocks(blocks: List[BlockAnalysis]) -> bool:
        """
        Validate that blocks are properly structured.

        Args:
            blocks: List of blocks to validate

        Returns:
            True if valid, False otherwise
        """
        if not blocks or len(blocks) != BlockSegmentation.BLOCKS_PER_HOUR:
            logger.error(f"Expected {BlockSegmentation.BLOCKS_PER_HOUR} blocks, got {len(blocks)}")
            return False

        for i, block in enumerate(blocks):
            if block.block_number != i + 1:
                logger.error(f"Block numbering error: expected {i+1}, got {block.block_number}")
                return False

            if not (0 <= block.time_above_open <= 1):
                logger.error(f"Invalid time_above_open: {block.time_above_open}")
                return False

            if not (0 <= block.time_below_open <= 1):
                logger.error(f"Invalid time_below_open: {block.time_below_open}")
                return False

            if block.price_at_end <= 0:
                logger.error(f"Invalid price_at_end: {block.price_at_end}")
                return False

        return True
