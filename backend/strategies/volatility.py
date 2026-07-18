"""
Volatility strategies: Bollinger Bands, Stochastic Oscillator, ATR.
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands strategy.

    Buy  (+1): price crosses below lower band (mean-reversion entry)
    Sell (-1): price crosses above upper band (mean-reversion exit)
    """

    name = "bb"
    description = "Bollinger Bands"

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df["BB_Middle"] = df["Close"].rolling(window=self.period).mean()
        rolling_std = df["Close"].rolling(window=self.period).std()
        df["BB_Upper"] = df["BB_Middle"] + self.std_dev * rolling_std
        df["BB_Lower"] = df["BB_Middle"] - self.std_dev * rolling_std
        df["BB_Width"] = self._safe_div(df["BB_Upper"] - df["BB_Lower"], df["BB_Middle"])
        df["BB_Pct"] = self._safe_div(df["Close"] - df["BB_Lower"], df["BB_Upper"] - df["BB_Lower"])

        # Signal
        df["Signal"] = 0
        buy = (df["Close"] < df["BB_Lower"]) & (df["Close"].shift(1) >= df["BB_Lower"].shift(1))
        sell = (df["Close"] > df["BB_Upper"]) & (df["Close"].shift(1) <= df["BB_Upper"].shift(1))
        df.loc[buy, "Signal"] = 1
        df.loc[sell, "Signal"] = -1

        return df


class StochasticStrategy(BaseStrategy):
    """
    Stochastic Oscillator strategy.

    Buy  (+1): %K crosses above %D from oversold (<20)
    Sell (-1): %K crosses below %D from overbought (>80)
    """

    name = "stoch"
    description = "Stochastic Oscillator (%K, %D)"

    def __init__(self, k_period: int = 14, d_period: int = 3, oversold: float = 20.0, overbought: float = 80.0):
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        low_min = df["Low"].rolling(window=self.k_period).min()
        high_max = df["High"].rolling(window=self.k_period).max()
        diff = high_max - low_min
        df["Stoch_K"] = 100 * self._safe_div(df["Close"] - low_min, diff)
        df["Stoch_D"] = df["Stoch_K"].rolling(window=self.d_period).mean()

        # Signal
        df["Signal"] = 0
        buy = (
            (df["Stoch_K"] > df["Stoch_D"])
            & (df["Stoch_K"].shift(1) <= df["Stoch_D"].shift(1))
            & (df["Stoch_K"] < self.overbought)
        )
        sell = (
            (df["Stoch_K"] < df["Stoch_D"])
            & (df["Stoch_K"].shift(1) >= df["Stoch_D"].shift(1))
            & (df["Stoch_K"] > self.oversold)
        )
        df.loc[buy, "Signal"] = 1
        df.loc[sell, "Signal"] = -1

        return df


class ATRStrategy(BaseStrategy):
    """
    Average True Range (ATR) - primarily a risk measure, not a directional strategy.
    Generates signals when volatility spikes occur.
    """

    name = "atr"
    description = "Average True Range (ATR)"

    def __init__(self, period: int = 14, multiplier: float = 2.0):
        self.period = period
        self.multiplier = multiplier

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift(1)).abs()
        low_close = (df["Low"] - df["Close"].shift(1)).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = true_range.ewm(com=self.period - 1, adjust=False).mean()

        # Volatility regime: high when ATR > multiplier * rolling mean
        atr_mean = df["ATR"].rolling(window=self.period * 2).mean()
        df["ATR_High_Vol"] = df["ATR"] > self.multiplier * atr_mean

        # No directional signal from ATR alone
        df["Signal"] = 0
        return df
