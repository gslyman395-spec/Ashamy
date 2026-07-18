"""
Backtesting metrics - comprehensive performance measurement.
"""
import numpy as np
import pandas as pd
from typing import List, Dict


class BacktestMetrics:
    """
    Computes standard financial performance metrics from backtest results.
    """

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate

    def compute(
        self,
        equity_curve: pd.Series,
        trade_returns: List[float],
        initial_capital: float,
        trading_days: int = 252,
    ) -> Dict:
        """
        Compute all performance metrics.

        Args:
            equity_curve: Series of portfolio values over time.
            trade_returns: List of per-trade returns (e.g., 0.05 = 5%).
            initial_capital: Starting capital.
            trading_days: Number of trading days per year (default 252).

        Returns:
            Dictionary of metrics.
        """
        metrics: Dict = {}

        # ---- Basic ----
        final_equity = float(equity_curve.iloc[-1])
        total_return = (final_equity - initial_capital) / initial_capital
        metrics["total_return"] = round(total_return * 100, 2)
        metrics["final_equity"] = round(final_equity, 2)
        metrics["initial_capital"] = round(initial_capital, 2)

        # ---- CAGR ----
        n_years = len(equity_curve) / trading_days
        if n_years > 0 and initial_capital > 0:
            cagr = (final_equity / initial_capital) ** (1 / n_years) - 1
        else:
            cagr = 0.0
        metrics["cagr"] = round(cagr * 100, 2)

        # ---- Daily returns ----
        daily_returns = equity_curve.pct_change().dropna()
        metrics["daily_returns_mean"] = round(float(daily_returns.mean()) * 100, 4)
        metrics["daily_returns_std"] = round(float(daily_returns.std()) * 100, 4)

        # ---- Sharpe Ratio ----
        if daily_returns.std() > 0:
            excess = daily_returns - self.risk_free_rate / trading_days
            sharpe = np.sqrt(trading_days) * excess.mean() / excess.std()
        else:
            sharpe = 0.0
        metrics["sharpe_ratio"] = round(float(sharpe), 4)

        # ---- Sortino Ratio ----
        downside = daily_returns[daily_returns < 0]
        if len(downside) > 0 and downside.std() > 0:
            sortino = np.sqrt(trading_days) * daily_returns.mean() / downside.std()
        else:
            sortino = 0.0
        metrics["sortino_ratio"] = round(float(sortino), 4)

        # ---- Maximum Drawdown ----
        rolling_max = equity_curve.cummax()
        drawdown = (equity_curve - rolling_max) / rolling_max
        max_drawdown = float(drawdown.min())
        metrics["max_drawdown"] = round(max_drawdown * 100, 2)

        # ---- Calmar Ratio ----
        if max_drawdown != 0:
            calmar = cagr / abs(max_drawdown)
        else:
            calmar = 0.0
        metrics["calmar_ratio"] = round(float(calmar), 4)

        # ---- Trade-level metrics ----
        if trade_returns:
            returns_arr = np.array(trade_returns)
            wins = returns_arr[returns_arr > 0]
            losses = returns_arr[returns_arr <= 0]
            win_rate = len(wins) / len(returns_arr)
            avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
            avg_loss = float(losses.mean()) if len(losses) > 0 else 0.0
            profit_factor = (
                abs(wins.sum() / losses.sum()) if losses.sum() != 0 else float("inf")
            )
            metrics.update(
                {
                    "total_trades": len(returns_arr),
                    "win_rate": round(win_rate * 100, 2),
                    "avg_win_pct": round(avg_win * 100, 2),
                    "avg_loss_pct": round(avg_loss * 100, 2),
                    "profit_factor": round(profit_factor, 4),
                    "expectancy": round(
                        (win_rate * avg_win + (1 - win_rate) * avg_loss) * 100, 4
                    ),
                }
            )
        else:
            metrics.update(
                {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_win_pct": 0.0,
                    "avg_loss_pct": 0.0,
                    "profit_factor": 0.0,
                    "expectancy": 0.0,
                }
            )

        return metrics
