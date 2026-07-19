class RiskManager:
    def __init__(self, risk_percent=0.02, take_profit_ratio=1.5, stop_loss_ratio=1.0):
        self.risk_percent = risk_percent
        self.take_profit_ratio = take_profit_ratio
        self.stop_loss_ratio = stop_loss_ratio

    def calculate_position_size(self, balance, entry_price, stop_loss_price):
        risk_amount = balance * self.risk_percent
        stop_distance = abs(entry_price - stop_loss_price)

        if stop_distance == 0:
            return 0

        size = risk_amount / stop_distance
        return size

    def evaluate_trade(self, entry_price):
        stop_loss = entry_price - (entry_price * self.stop_loss_ratio / 100)
        take_profit = entry_price + (entry_price * self.take_profit_ratio / 100)
        return stop_loss, take_profit
