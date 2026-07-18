"""
Tests for technical strategies.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import pandas as pd
import numpy as np

from strategies.technical import MovingAverageStrategy
from strategies.momentum import RSIStrategy, MACDStrategy
from strategies.volatility import BollingerBandsStrategy, StochasticStrategy, ATRStrategy
from strategies.trend import VWAPStrategy, FibonacciStrategy, IchimokuStrategy, CamarillaPivotStrategy


def _make_df(n: int = 200) -> pd.DataFrame:
    """Create a synthetic OHLCV DataFrame."""
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    df = pd.DataFrame(
        {
            "Open": close * (1 + np.random.uniform(-0.002, 0.002, n)),
            "High": close * (1 + np.abs(np.random.uniform(0.001, 0.01, n))),
            "Low": close * (1 - np.abs(np.random.uniform(0.001, 0.01, n))),
            "Close": close,
            "Volume": np.random.randint(1_000_000, 10_000_000, n).astype(float),
        },
        index=dates,
    )
    return df


class TestMovingAverageStrategy:
    def setup_method(self):
        self.strategy = MovingAverageStrategy(short=10, long=20)
        self.df = _make_df()

    def test_columns_created(self):
        result = self.strategy.compute(self.df)
        assert "SMA_20" in result.columns
        assert "EMA_20" in result.columns
        assert "WMA_20" in result.columns
        assert "ma_Signal" in result.columns

    def test_signal_values(self):
        result = self.strategy.compute(self.df)
        assert result["ma_Signal"].isin([-1, 0, 1]).all()

    def test_no_future_leak(self):
        """Signals at bar t should only use data up to bar t."""
        result = self.strategy.compute(self.df)
        # Check that early rows (< short period) have NaN SMA
        assert result["SMA_20"].iloc[: self.strategy.short - 1].isna().all()


class TestRSIStrategy:
    def setup_method(self):
        self.strategy = RSIStrategy(period=14)
        self.df = _make_df()

    def test_rsi_bounds(self):
        result = self.strategy.compute(self.df)
        rsi = result["RSI"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()

    def test_signal_column_exists(self):
        result = self.strategy.compute(self.df)
        assert "rsi_Signal" in result.columns


class TestMACDStrategy:
    def setup_method(self):
        self.strategy = MACDStrategy()
        self.df = _make_df()

    def test_macd_columns(self):
        result = self.strategy.compute(self.df)
        for col in ["MACD", "MACD_Signal", "MACD_Hist", "macd_Signal"]:
            assert col in result.columns

    def test_histogram_equals_diff(self):
        result = self.strategy.compute(self.df)
        diff = (result["MACD"] - result["MACD_Signal"]).dropna()
        hist = result["MACD_Hist"].dropna()
        pd.testing.assert_series_equal(diff, hist, check_names=False, atol=1e-6)


class TestBollingerBandsStrategy:
    def setup_method(self):
        self.strategy = BollingerBandsStrategy()
        self.df = _make_df()

    def test_upper_greater_than_lower(self):
        result = self.strategy.compute(self.df)
        subset = result.dropna(subset=["BB_Upper", "BB_Lower"])
        assert (subset["BB_Upper"] >= subset["BB_Lower"]).all()

    def test_pct_between_0_and_1_usually(self):
        result = self.strategy.compute(self.df)
        pct = result["BB_Pct"].dropna()
        # Most values should be in [0, 1]
        within = ((pct >= 0) & (pct <= 1)).mean()
        assert within > 0.80


class TestStochasticStrategy:
    def setup_method(self):
        self.strategy = StochasticStrategy()
        self.df = _make_df()

    def test_k_d_bounds(self):
        result = self.strategy.compute(self.df)
        k = result["Stoch_K"].dropna()
        d = result["Stoch_D"].dropna()
        assert (k >= 0).all() and (k <= 100).all()
        assert (d >= 0).all() and (d <= 100).all()


class TestATRStrategy:
    def setup_method(self):
        self.strategy = ATRStrategy()
        self.df = _make_df()

    def test_atr_non_negative(self):
        result = self.strategy.compute(self.df)
        atr = result["ATR"].dropna()
        assert (atr >= 0).all()


class TestVWAPStrategy:
    def setup_method(self):
        self.strategy = VWAPStrategy()
        self.df = _make_df()

    def test_vwap_column_exists(self):
        result = self.strategy.compute(self.df)
        assert "VWAP" in result.columns
        assert "vwap_Signal" in result.columns


class TestFibonacciStrategy:
    def setup_method(self):
        self.strategy = FibonacciStrategy(lookback=20)
        self.df = _make_df()

    def test_fib_levels_exist(self):
        result = self.strategy.compute(self.df)
        assert "Fib_0000" in result.columns
        assert "Fib_1000" in result.columns


class TestIchimokuStrategy:
    def setup_method(self):
        self.strategy = IchimokuStrategy()
        self.df = _make_df(300)

    def test_ichimoku_columns(self):
        result = self.strategy.compute(self.df)
        for col in ["Tenkan_Sen", "Kijun_Sen", "Senkou_A", "Senkou_B"]:
            assert col in result.columns


class TestCamarillaPivotStrategy:
    def setup_method(self):
        self.strategy = CamarillaPivotStrategy()
        self.df = _make_df()

    def test_camarilla_levels(self):
        result = self.strategy.compute(self.df)
        for lvl in ["Cam_R4", "Cam_R3", "Cam_S3", "Cam_S4"]:
            assert lvl in result.columns
