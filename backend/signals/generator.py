"""
Signal generator - runs all strategies and produces consolidated signals.
"""
import pandas as pd
import numpy as np
from typing import List, Dict
from loguru import logger

from strategies import ALL_STRATEGIES, BaseStrategy


class SignalGenerator:
    """
    Runs every strategy on the input DataFrame and produces individual signals.
    """

    def __init__(self, strategies: List[BaseStrategy] = None):
        self.strategies = strategies or ALL_STRATEGIES

    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all strategies and add per-strategy signal columns.

        Returns the enriched DataFrame with columns:
            <strategy_name>_Signal  for each strategy
        """
        result = df.copy()
        for strategy in self.strategies:
            try:
                enriched = strategy.compute(result)
                # Copy only the new columns
                new_cols = [c for c in enriched.columns if c not in result.columns]
                for col in new_cols:
                    result[col] = enriched[col]
            except Exception as exc:
                logger.warning(f"Strategy {strategy.name} failed: {exc}")
        logger.info(f"Generated signals from {len(self.strategies)} strategies")
        return result

    def get_signal_columns(self) -> List[str]:
        return [f"{s.name}_Signal" for s in self.strategies]
