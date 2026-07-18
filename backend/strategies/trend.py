"""
Trend strategies: VWAP, Fibonacci Retracement, Ichimoku Cloud,
Camarilla Pivot Points.
"""
import pandas as pd
import numpy as np
from .base import BaseStrategy


class VWAPStrategy(BaseStrategy):
    """
    Volume Weighted Average Price (VWAP).

    Buy  (+1): price crosses above VWAP
    Sell (-1): price crosses below VWAP
    """

    name = "vwap"
    description = "Volume Weighted Average Price (VWAP)"

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        cumulative_tp_vol = (typical_price * df["Volume"]).cumsum()
        cumulative_vol = df["Volume"].cumsum()
        df["VWAP"] = self._safe_div(cumulative_tp_vol, cumulative_vol)

        # Signal
        df["Signal"] = 0
        buy = (df["Close"] > df["VWAP"]) & (df["Close"].shift(1) <= df["VWAP"].shift(1))
        sell = (df["Close"] < df["VWAP"]) & (df["Close"].shift(1) >= df["VWAP"].shift(1))
        df.loc[buy, "Signal"] = 1
        df.loc[sell, "Signal"] = -1

        return df


class FibonacciStrategy(BaseStrategy):
    """
    Fibonacci Retracement levels.

    Generates buy signals near support levels and sell signals near resistance.
    """

    name = "fib"
    description = "Fibonacci Retracement"

    def __init__(self, lookback: int = 50):
        self.lookback = lookback
        self.fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        swing_high = df["High"].rolling(window=self.lookback).max()
        swing_low = df["Low"].rolling(window=self.lookback).min()
        diff = swing_high - swing_low

        for level in self.fib_levels:
            col = f"Fib_{int(level * 1000):04d}"
            df[col] = swing_high - level * diff

        # Signal: price near 38.2% or 61.8% retracement levels
        df["Signal"] = 0
        tol = 0.005  # 0.5% tolerance
        fib_618 = df["Fib_0618"]
        fib_382 = df["Fib_0382"]

        buy = (df["Close"] >= fib_618 * (1 - tol)) & (df["Close"] <= fib_618 * (1 + tol))
        sell = (df["Close"] >= fib_382 * (1 - tol)) & (df["Close"] <= fib_382 * (1 + tol))
        df.loc[buy, "Signal"] = 1
        df.loc[sell, "Signal"] = -1

        return df


class IchimokuStrategy(BaseStrategy):
    """
    Ichimoku Cloud strategy.

    Buy  (+1): price crosses above the cloud (Senkou Span A and B)
    Sell (-1): price crosses below the cloud
    """

    name = "ichimoku"
    description = "Ichimoku Cloud"

    def __init__(
        self,
        tenkan: int = 9,
        kijun: int = 26,
        senkou_b: int = 52,
        chikou: int = 26,
        displacement: int = 26,
    ):
        self.tenkan = tenkan
        self.kijun = kijun
        self.senkou_b = senkou_b
        self.chikou = chikou
        self.displacement = displacement

    def _midpoint(self, df: pd.DataFrame, period: int) -> pd.Series:
        return (df["High"].rolling(period).max() + df["Low"].rolling(period).min()) / 2

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Tenkan_Sen"] = self._midpoint(df, self.tenkan)
        df["Kijun_Sen"] = self._midpoint(df, self.kijun)
        df["Senkou_A"] = ((df["Tenkan_Sen"] + df["Kijun_Sen"]) / 2).shift(self.displacement)
        df["Senkou_B"] = self._midpoint(df, self.senkou_b).shift(self.displacement)
        df["Chikou_Span"] = df["Close"].shift(-self.chikou)

        cloud_top = df[["Senkou_A", "Senkou_B"]].max(axis=1)
        cloud_bottom = df[["Senkou_A", "Senkou_B"]].min(axis=1)

        # Signal
        df["Signal"] = 0
        above_cloud = (df["Close"] > cloud_top) & (df["Close"].shift(1) <= cloud_top.shift(1))
        below_cloud = (df["Close"] < cloud_bottom) & (df["Close"].shift(1) >= cloud_bottom.shift(1))
        df.loc[above_cloud, "Signal"] = 1
        df.loc[below_cloud, "Signal"] = -1

        return df


class CamarillaPivotStrategy(BaseStrategy):
    """
    Camarilla Pivot Points strategy.

    Uses previous day's OHLC to compute 8 support/resistance levels.
    Buy near S3/S4; Sell near R3/R4.
    """

    name = "camarilla"
    description = "Camarilla Pivot Points"

    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        prev_high = df["High"].shift(1)
        prev_low = df["Low"].shift(1)
        prev_close = df["Close"].shift(1)
        diff = prev_high - prev_low

        df["Cam_R4"] = prev_close + diff * 1.1 / 2
        df["Cam_R3"] = prev_close + diff * 1.1 / 4
        df["Cam_R2"] = prev_close + diff * 1.1 / 6
        df["Cam_R1"] = prev_close + diff * 1.1 / 12
        df["Cam_S1"] = prev_close - diff * 1.1 / 12
        df["Cam_S2"] = prev_close - diff * 1.1 / 6
        df["Cam_S3"] = prev_close - diff * 1.1 / 4
        df["Cam_S4"] = prev_close - diff * 1.1 / 2

        # Signal
        df["Signal"] = 0
        buy = df["Close"] <= df["Cam_S3"]
        sell = df["Close"] >= df["Cam_R3"]
        df.loc[buy, "Signal"] = 1
        df.loc[sell, "Signal"] = -1

        return df
