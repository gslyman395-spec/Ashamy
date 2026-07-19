import pandas as pd
from model import TradingModel
from ai_models import TransformerPredictor

class Strategy:
    def __init__(self, min_prob: float = 0.6):
        self.model = TradingModel()
        self.ai = TransformerPredictor()
        self.min_prob = min_prob

    def train(self, df: pd.DataFrame):
        self.model.train(df)
        self.ai.train(df)

    def generate_signal(self, row: pd.Series) -> str:
        prob = self.model.predict_proba(row)

        # لاحقًا سنضيف توصيات Transformer هنا
        if prob >= self.min_prob:
            return "BUY"
        else:
            return "HOLD"
