"""
Fibonacci Pivot Data Model

Database model for storing Fibonacci pivot point calculations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from dateutil import parser


@dataclass
class FibonacciPivot:
    """
    Database model for Fibonacci pivot point calculations.

    Stores pivot levels calculated using Fibonacci ratios across different timeframes.
    """
    ticker_symbol: str
    timeframe: str  # 'daily', 'weekly', 'monthly'
    calculation_date: datetime

    # Source OHLC data
    period_high: float
    period_low: float
    period_close: float

    # Calculated pivot levels
    pivot_point: float
    resistance_1: float
    resistance_2: float
    resistance_3: float
    support_1: float
    support_2: float
    support_3: float

    # Optional fields
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ticker_symbol': self.ticker_symbol,
            'timeframe': self.timeframe,
            'calculation_date': self.calculation_date.isoformat() if self.calculation_date else None,
            'period_high': round(self.period_high, 4) if self.period_high is not None else None,
            'period_low': round(self.period_low, 4) if self.period_low is not None else None,
            'period_close': round(self.period_close, 4) if self.period_close is not None else None,
            'pivot_point': round(self.pivot_point, 4) if self.pivot_point is not None else None,
            'resistance_1': round(self.resistance_1, 4) if self.resistance_1 is not None else None,
            'resistance_2': round(self.resistance_2, 4) if self.resistance_2 is not None else None,
            'resistance_3': round(self.resistance_3, 4) if self.resistance_3 is not None else None,
            'support_1': round(self.support_1, 4) if self.support_1 is not None else None,
            'support_2': round(self.support_2, 4) if self.support_2 is not None else None,
            'support_3': round(self.support_3, 4) if self.support_3 is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_row(cls, row: tuple):
        """
        Create FibonacciPivot instance from database row

        Args:
            row: Database row tuple

        Returns:
            FibonacciPivot instance
        """
        # Parse calculation_date if it's a string
        calculation_date = row[3]
        if isinstance(calculation_date, str):
            calculation_date = parser.isoparse(calculation_date)

        # Parse created_at and updated_at if they exist and are strings
        created_at = row[14] if len(row) > 14 else None
        if isinstance(created_at, str):
            created_at = parser.isoparse(created_at)

        updated_at = row[15] if len(row) > 15 else None
        if isinstance(updated_at, str):
            updated_at = parser.isoparse(updated_at)

        return cls(
            id=row[0],
            ticker_symbol=row[1],
            timeframe=row[2],
            calculation_date=calculation_date,
            period_high=float(row[4]) if row[4] is not None else None,
            period_low=float(row[5]) if row[5] is not None else None,
            period_close=float(row[6]) if row[6] is not None else None,
            pivot_point=float(row[7]) if row[7] is not None else None,
            resistance_1=float(row[8]) if row[8] is not None else None,
            resistance_2=float(row[9]) if row[9] is not None else None,
            resistance_3=float(row[10]) if row[10] is not None else None,
            support_1=float(row[11]) if row[11] is not None else None,
            support_2=float(row[12]) if row[12] is not None else None,
            support_3=float(row[13]) if row[13] is not None else None,
            created_at=created_at,
            updated_at=updated_at
        )

    def __repr__(self) -> str:
        """String representation of the model"""
        return (
            f"FibonacciPivot(ticker={self.ticker_symbol}, "
            f"timeframe={self.timeframe}, "
            f"date={self.calculation_date.date() if self.calculation_date else 'None'}, "
            f"PP={self.pivot_point:.2f})"
        )
