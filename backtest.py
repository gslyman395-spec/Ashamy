import pandas as pd
from strategy import Strategy
from risk_manager import RiskManager

def backtest(df: pd.DataFrame, initial_balance: float = 10000.0) -> dict:
    df = df.dropna()

    strat = Strategy(min_prob=0.6)
    risk = RiskManager(risk_percent=0.02, take_profit_ratio=1.5, stop_loss_ratio=1.0)

    strat.train(df)

    balance = initial_balance
    equity_curve = []

    for idx in range(len(df) - 1):
        row = df.iloc[idx]
        next_row = df.iloc[idx + 1]

        signal = strat.generate_signal(row)

        if signal == "BUY":
            entry_price = row["Close"]

            stop_loss, take_profit = risk.evaluate_trade(entry_price)
            size = risk.calculate_position_size(balance, entry_price, stop_loss)

            if size <= 0:
                continue

            exit_price = next_row["Close"]

            if exit_price <= stop_loss:
                pnl = (stop_loss - entry_price) * size
            elif exit_price >= take_profit:
                pnl = (take_profit - entry_price) * size
            else:
                pnl = (exit_price - entry_price) * size

            balance += pnl

        equity_curve.append(balance)

    return {
        "final_balance": balance,
        "equity_curve": equity_curve
    }
