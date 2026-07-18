"""
Backtesting engine - simulates trading on historical data using generated signals.
"""
import pandas as pd
import numpy as np
from loguru import logger
from typing import Optional


class BacktestEngine:
    """
    Event-driven backtesting engine.

    Simulates buy/sell trades based on 'Final_Signal' column.
    Handles commission and slippage.
    """

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        position_size: float = 1.0,  # fraction of capital per trade
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size

    def run(self, df: pd.DataFrame, signal_col: str = "Final_Signal") -> pd.DataFrame:
        """
        Run the backtest.

        Args:
            df: DataFrame with OHLCV data and a signal column.
            signal_col: Column name containing +1/-1/0 signals.

        Returns:
            DataFrame with portfolio value, positions, and trade log.
        """
        df = df.copy()
        n = len(df)

        capital = self.initial_capital
        position = 0.0         # number of shares held
        entry_price = 0.0

        equity_curve = np.zeros(n)
        positions = np.zeros(n)
        trade_returns = []
        trades = []

        for i in range(n):
            price = df["Close"].iloc[i]
            signal = df[signal_col].iloc[i] if signal_col in df.columns else 0

            # Execute signal
            if signal == 1 and position == 0:
                # Buy
                cost_price = price * (1 + self.slippage)
                shares = (capital * self.position_size) / cost_price
                cost = shares * cost_price * (1 + self.commission)
                if cost <= capital:
                    capital -= cost
                    position = shares
                    entry_price = cost_price
                    trades.append(
                        {"date": df.index[i], "action": "BUY", "price": cost_price, "shares": shares}
                    )

            elif signal == -1 and position > 0:
                # Sell
                sell_price = price * (1 - self.slippage)
                proceeds = position * sell_price * (1 - self.commission)
                ret = (sell_price - entry_price) / entry_price
                trade_returns.append(ret)
                capital += proceeds
                trades.append(
                    {
                        "date": df.index[i],
                        "action": "SELL",
                        "price": sell_price,
                        "shares": position,
                        "return": ret,
                    }
                )
                position = 0.0
                entry_price = 0.0

            equity_curve[i] = capital + position * price
            positions[i] = position

        # Close any open position at the last bar
        if position > 0:
            last_price = df["Close"].iloc[-1] * (1 - self.slippage)
            proceeds = position * last_price * (1 - self.commission)
            ret = (last_price - entry_price) / entry_price
            trade_returns.append(ret)
            capital += proceeds
            equity_curve[-1] = capital
            trades.append(
                {
                    "date": df.index[-1],
                    "action": "SELL (close)",
                    "price": last_price,
                    "shares": position,
                    "return": ret,
                }
            )

        df["Equity"] = equity_curve
        df["Position"] = positions
        self._trades = trades
        self._trade_returns = trade_returns
        logger.info(
            f"Backtest complete: {len(trades)} trades, "
            f"final equity={equity_curve[-1]:.2f}"
        )
        return df

    @property
    def trades(self) -> list:
        return getattr(self, "_trades", [])

    @property
    def trade_returns(self) -> list:
        return getattr(self, "_trade_returns", [])
