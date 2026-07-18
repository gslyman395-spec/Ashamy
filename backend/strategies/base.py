"""
Base strategy class that all strategies inherit from.
"""
from abc import ABC, abstractmethod
import pandas as pd
from loguru import logger


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    name: str = "base"
    description: str = ""

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute indicators and signals for the strategy.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            df enriched with indicator columns and a 'Signal' column
              +1 = Buy, -1 = Sell, 0 = Hold
        """
        result = self._compute(df.copy())
        if "Signal" not in result.columns:
            result["Signal"] = 0
        result[f"{self.name}_Signal"] = result["Signal"]
        logger.debug(f"{self.name}: computed {len(result)} rows")
        return result

    @abstractmethod
    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Implement indicator computation in subclasses."""
        raise NotImplementedError

    @staticmethod
    def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
        """Safe division, returns 0 where denominator is 0."""
        return a.where(b != 0, 0) / b.where(b != 0, 1)
