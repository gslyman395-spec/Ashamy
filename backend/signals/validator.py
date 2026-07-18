"""
Signal validator - filters out low-quality and false signals.
"""
import pandas as pd
import numpy as np
from loguru import logger
from typing import List


class SignalValidator:
    """
    Post-processes raw strategy signals to reduce false positives.

    Filters applied:
      1. Minimum signal count threshold - a signal must appear in at least
         `min_agreeing` strategies.
      2. Volatility filter - suppress signals during extreme volatility spikes
         (ATR > 2× its rolling mean).
      3. Volume confirmation - require above-average volume on signal bars.
    """

    def __init__(
        self,
        min_agreeing: int = 2,
        use_volatility_filter: bool = True,
        use_volume_filter: bool = True,
        vol_multiplier: float = 2.0,
        vol_window: int = 20,
    ):
        self.min_agreeing = min_agreeing
        self.use_volatility_filter = use_volatility_filter
        self.use_volume_filter = use_volume_filter
        self.vol_multiplier = vol_multiplier
        self.vol_window = vol_window

    def validate(self, df: pd.DataFrame, signal_columns: List[str]) -> pd.DataFrame:
        """
        Return a copy of df with a 'Valid_Signal' column:
          +1 = validated buy, -1 = validated sell, 0 = no signal.
        """
        df = df.copy()
        available = [c for c in signal_columns if c in df.columns]

        buy_count = (df[available] == 1).sum(axis=1)
        sell_count = (df[available] == -1).sum(axis=1)

        raw_signal = np.where(
            buy_count >= self.min_agreeing, 1,
            np.where(sell_count >= self.min_agreeing, -1, 0)
        )
        df["Raw_Signal"] = raw_signal
        df["Buy_Count"] = buy_count
        df["Sell_Count"] = sell_count

        mask = pd.Series(True, index=df.index)

        if self.use_volatility_filter and "ATR" in df.columns:
            atr_mean = df["ATR"].rolling(window=self.vol_window * 2).mean()
            high_vol = df["ATR"] > self.vol_multiplier * atr_mean
            suppressed = (raw_signal != 0) & high_vol
            logger.debug(f"Volatility filter suppressed {suppressed.sum()} signals")
            mask = mask & ~high_vol

        if self.use_volume_filter and "Volume" in df.columns:
            vol_mean = df["Volume"].rolling(window=self.vol_window).mean()
            low_vol = df["Volume"] < vol_mean
            suppressed = (raw_signal != 0) & low_vol
            logger.debug(f"Volume filter suppressed {suppressed.sum()} signals")
            mask = mask & ~low_vol

        df["Valid_Signal"] = df["Raw_Signal"].where(mask, 0)
        return df
