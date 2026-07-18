"""
Tests for signal generation, validation, and combination.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import pandas as pd
import numpy as np

from signals.generator import SignalGenerator
from signals.validator import SignalValidator
from signals.combiner import SignalCombiner
from strategies.technical import MovingAverageStrategy
from strategies.momentum import RSIStrategy


def _make_df(n: int = 200) -> pd.DataFrame:
    np.random.seed(7)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    df = pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.005,
            "Low": close * 0.995,
            "Close": close,
            "Volume": np.random.randint(500_000, 5_000_000, n).astype(float),
        },
        index=dates,
    )
    return df


class TestSignalGenerator:
    def test_generates_signal_columns(self):
        gen = SignalGenerator(strategies=[MovingAverageStrategy(), RSIStrategy()])
        df = _make_df()
        result = gen.generate(df)
        assert "ma_Signal" in result.columns
        assert "rsi_Signal" in result.columns

    def test_signal_values_valid(self):
        gen = SignalGenerator(strategies=[MovingAverageStrategy()])
        result = gen.generate(_make_df())
        assert result["ma_Signal"].isin([-1, 0, 1]).all()

    def test_get_signal_columns(self):
        gen = SignalGenerator(strategies=[MovingAverageStrategy(), RSIStrategy()])
        cols = gen.get_signal_columns()
        assert "ma_Signal" in cols
        assert "rsi_Signal" in cols


class TestSignalValidator:
    def setup_method(self):
        gen = SignalGenerator(strategies=[MovingAverageStrategy(), RSIStrategy()])
        self.df = gen.generate(_make_df())
        self.sig_cols = gen.get_signal_columns()
        self.validator = SignalValidator(min_agreeing=1, use_volatility_filter=False, use_volume_filter=False)

    def test_valid_signal_column_created(self):
        result = self.validator.validate(self.df, self.sig_cols)
        assert "Valid_Signal" in result.columns

    def test_valid_signal_values(self):
        result = self.validator.validate(self.df, self.sig_cols)
        assert result["Valid_Signal"].isin([-1, 0, 1]).all()

    def test_raw_signal_column_created(self):
        result = self.validator.validate(self.df, self.sig_cols)
        assert "Raw_Signal" in result.columns


class TestSignalCombiner:
    def setup_method(self):
        gen = SignalGenerator(strategies=[MovingAverageStrategy(), RSIStrategy()])
        df = gen.generate(_make_df())
        sig_cols = gen.get_signal_columns()
        val = SignalValidator(min_agreeing=1, use_volatility_filter=False, use_volume_filter=False)
        self.df = val.validate(df, sig_cols)
        self.combiner = SignalCombiner(signal_threshold=0.3)

    def test_final_signal_column_created(self):
        result = self.combiner.combine(self.df)
        assert "Final_Signal" in result.columns

    def test_recommendation_column(self):
        result = self.combiner.combine(self.df)
        assert "Recommendation" in result.columns
        assert result["Recommendation"].isin(["BUY", "SELL", "HOLD"]).all()

    def test_confidence_between_0_and_1(self):
        result = self.combiner.combine(self.df)
        conf = result["Confidence"].dropna()
        assert (conf >= 0).all() and (conf <= 1).all()

    def test_combine_with_ml_predictions(self):
        n = len(self.df)
        ml_preds = np.random.randn(n).astype(np.float32)
        result = self.combiner.combine(self.df, ml_predictions=ml_preds)
        assert "Final_Signal" in result.columns
