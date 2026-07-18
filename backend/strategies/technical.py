"""
Technical indicators strategy: Moving Averages (SMA, EMA, WMA) and crossover signals.
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    """
    Generates buy/sell signals based on SMA, EMA, and WMA crossovers.

    Buy signal  (+1): short MA crosses above long MA
    Sell signal (-1): short MA crosses below long MA
    """

    name = "ma"
    description = "Moving Average Crossover (SMA, EMA, WMA)"

    def __init__(self, short: int = 20, long: int = 50):
        self.short = short
        self.long = long

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["Close"]

        # SMA
        df["SMA_20"] = close.rolling(window=self.short).mean()
        df["SMA_50"] = close.rolling(window=self.long).mean()

        # EMA
        df["EMA_20"] = close.ewm(span=self.short, adjust=False).mean()
        df["EMA_50"] = close.ewm(span=self.long, adjust=False).mean()

        # WMA (linearly weighted)
        weights_short = np.arange(1, self.short + 1)
        weights_long = np.arange(1, self.long + 1)
        df["WMA_20"] = (
            close.rolling(self.short)
            .apply(lambda x: np.dot(x, weights_short) / weights_short.sum(), raw=True)
        )
        df["WMA_50"] = (
            close.rolling(self.long)
            .apply(lambda x: np.dot(x, weights_long) / weights_long.sum(), raw=True)
        )

        # Signal: EMA crossover
        df["Signal"] = 0
        cross_up = (df["EMA_20"] > df["EMA_50"]) & (df["EMA_20"].shift(1) <= df["EMA_50"].shift(1))
        cross_down = (df["EMA_20"] < df["EMA_50"]) & (df["EMA_20"].shift(1) >= df["EMA_50"].shift(1))
        df.loc[cross_up, "Signal"] = 1
        df.loc[cross_down, "Signal"] = -1

        return df
