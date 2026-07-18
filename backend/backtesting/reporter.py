"""
Backtesting reporter - formats backtest results into human-readable reports.
"""
import json
import pandas as pd
from typing import Dict
from loguru import logger


class BacktestReporter:
    """
    Generates text and JSON reports from backtest metrics.
    """

    def generate(self, metrics: Dict, symbol: str = "", period: str = "") -> str:
        """
        Return a formatted text report.
        """
        lines = [
            "=" * 60,
            f"  BACKTEST REPORT  |  Symbol: {symbol}  |  Period: {period}",
            "=" * 60,
            "",
            "--- Performance ---",
            f"  Total Return     : {metrics.get('total_return', 0):.2f}%",
            f"  CAGR             : {metrics.get('cagr', 0):.2f}%",
            f"  Initial Capital  : ${metrics.get('initial_capital', 0):,.2f}",
            f"  Final Equity     : ${metrics.get('final_equity', 0):,.2f}",
            "",
            "--- Risk ---",
            f"  Max Drawdown     : {metrics.get('max_drawdown', 0):.2f}%",
            f"  Sharpe Ratio     : {metrics.get('sharpe_ratio', 0):.4f}",
            f"  Sortino Ratio    : {metrics.get('sortino_ratio', 0):.4f}",
            f"  Calmar Ratio     : {metrics.get('calmar_ratio', 0):.4f}",
            "",
            "--- Trades ---",
            f"  Total Trades     : {metrics.get('total_trades', 0)}",
            f"  Win Rate         : {metrics.get('win_rate', 0):.2f}%",
            f"  Avg Win          : {metrics.get('avg_win_pct', 0):.2f}%",
            f"  Avg Loss         : {metrics.get('avg_loss_pct', 0):.2f}%",
            f"  Profit Factor    : {metrics.get('profit_factor', 0):.4f}",
            f"  Expectancy       : {metrics.get('expectancy', 0):.4f}%",
            "",
            "=" * 60,
        ]
        report = "\n".join(lines)
        logger.info(f"Report generated for {symbol}")
        return report

    def to_json(self, metrics: Dict) -> str:
        """Return metrics as a JSON string."""
        return json.dumps(metrics, indent=2, default=str)

    def to_dataframe(self, trades: list) -> pd.DataFrame:
        """Convert trade list to a DataFrame."""
        if not trades:
            return pd.DataFrame()
        return pd.DataFrame(trades)
