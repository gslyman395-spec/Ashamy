"""
Momentum strategies: RSI and MACD.
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) strategy.

    Buy  (+1): RSI crosses above oversold level (default 30)
    Sell (-1): RSI crosses below overbought level (default 70)
    """

    name = "rsi"
    description = "Relative Strength Index (RSI)"

    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=self.period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=self.period - 1, adjust=False).mean()

        rs = self._safe_div(avg_gain, avg_loss)
        df["RSI"] = 100 - (100 / (1 + rs))

        # Signal
        df["Signal"] = 0
        buy_signal = (df["RSI"] > self.oversold) & (df["RSI"].shift(1) <= self.oversold)
        sell_signal = (df["RSI"] < self.overbought) & (df["RSI"].shift(1) >= self.overbought)
        df.loc[buy_signal, "Signal"] = 1
        df.loc[sell_signal, "Signal"] = -1

        return df


class MACDStrategy(BaseStrategy):
    """
    MACD (Moving Average Convergence Divergence) strategy.

    Buy  (+1): MACD line crosses above signal line
    Sell (-1): MACD line crosses below signal line
    """

    name = "macd"
    description = "MACD with Signal Line"

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        ema_fast = df["Close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=self.slow, adjust=False).mean()

        df["MACD"] = ema_fast - ema_slow
        df["MACD_Signal"] = df["MACD"].ewm(span=self.signal_period, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

        # Signal
        df["Signal"] = 0
        cross_up = (df["MACD"] > df["MACD_Signal"]) & (df["MACD"].shift(1) <= df["MACD_Signal"].shift(1))
        cross_down = (df["MACD"] < df["MACD_Signal"]) & (df["MACD"].shift(1) >= df["MACD_Signal"].shift(1))
        df.loc[cross_up, "Signal"] = 1
        df.loc[cross_down, "Signal"] = -1

        return df
