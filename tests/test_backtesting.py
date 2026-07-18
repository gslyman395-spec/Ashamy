"""
Tests for backtesting engine and metrics.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import pandas as pd
import numpy as np

from backtesting.engine import BacktestEngine
from backtesting.metrics import BacktestMetrics
from backtesting.reporter import BacktestReporter


def _make_df_with_signals(n: int = 200) -> pd.DataFrame:
    np.random.seed(99)
    close = 100 + np.cumsum(np.random.randn(n) * 0.3)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    df = pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": np.random.randint(1_000_000, 5_000_000, n).astype(float),
        },
        index=dates,
    )
    # Alternate buy/sell every ~20 bars
    signals = np.zeros(n, dtype=int)
    for i in range(0, n, 20):
        if i + 10 < n:
            signals[i] = 1
            signals[i + 10] = -1
    df["Final_Signal"] = signals
    return df


class TestBacktestEngine:
    def setup_method(self):
        self.engine = BacktestEngine(initial_capital=100_000, commission=0.001)
        self.df = _make_df_with_signals()

    def test_equity_column_created(self):
        result = self.engine.run(self.df)
        assert "Equity" in result.columns

    def test_equity_starts_near_initial(self):
        result = self.engine.run(self.df)
        assert abs(result["Equity"].iloc[0] - 100_000) < 5_000

    def test_no_negative_equity(self):
        result = self.engine.run(self.df)
        assert (result["Equity"] > 0).all()

    def test_trades_list(self):
        self.engine.run(self.df)
        assert isinstance(self.engine.trades, list)

    def test_trade_returns_list(self):
        self.engine.run(self.df)
        assert isinstance(self.engine.trade_returns, list)

    def test_position_column_created(self):
        result = self.engine.run(self.df)
        assert "Position" in result.columns


class TestBacktestMetrics:
    def setup_method(self):
        self.calc = BacktestMetrics(risk_free_rate=0.02)
        engine = BacktestEngine(initial_capital=100_000)
        df = _make_df_with_signals()
        result = engine.run(df)
        self.equity = result["Equity"]
        self.trade_returns = engine.trade_returns

    def test_metrics_keys(self):
        metrics = self.calc.compute(self.equity, self.trade_returns, 100_000)
        expected_keys = [
            "total_return", "cagr", "final_equity", "max_drawdown",
            "sharpe_ratio", "win_rate", "total_trades",
        ]
        for k in expected_keys:
            assert k in metrics

    def test_max_drawdown_non_positive(self):
        metrics = self.calc.compute(self.equity, self.trade_returns, 100_000)
        assert metrics["max_drawdown"] <= 0.0

    def test_win_rate_in_valid_range(self):
        metrics = self.calc.compute(self.equity, self.trade_returns, 100_000)
        assert 0.0 <= metrics["win_rate"] <= 100.0

    def test_total_trades_non_negative(self):
        metrics = self.calc.compute(self.equity, self.trade_returns, 100_000)
        assert metrics["total_trades"] >= 0


class TestBacktestReporter:
    def test_generate_returns_string(self):
        reporter = BacktestReporter()
        metrics = {
            "total_return": 15.5,
            "cagr": 7.2,
            "initial_capital": 100_000,
            "final_equity": 115_500,
            "max_drawdown": -8.3,
            "sharpe_ratio": 1.2,
            "sortino_ratio": 1.5,
            "calmar_ratio": 0.9,
            "total_trades": 30,
            "win_rate": 60.0,
            "avg_win_pct": 2.5,
            "avg_loss_pct": -1.5,
            "profit_factor": 1.7,
            "expectancy": 0.9,
        }
        report = reporter.generate(metrics, symbol="AAPL", period="2y")
        assert "AAPL" in report
        assert "15.50%" in report

    def test_to_json(self):
        import json
        reporter = BacktestReporter()
        metrics = {"total_return": 10.0}
        json_str = reporter.to_json(metrics)
        parsed = json.loads(json_str)
        assert parsed["total_return"] == 10.0
