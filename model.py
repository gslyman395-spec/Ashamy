import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class TradingModel:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = df[["Close", "MA_20", "MA_50", "RSI"]].dropna()
        return features

    def prepare_labels(self, df: pd.DataFrame) -> pd.Series:
        future_close = df["Close"].shift(-1)
        labels = (future_close > df["Close"]).astype(int)
        return labels.loc[self.prepare_features(df).index]

    def train(self, df: pd.DataFrame):
        X = self.prepare_features(df)
        y = self.prepare_labels(df)

        # إزالة الصفوف التي تحتوي على NaN
        mask = X.notna().all(axis=1)
        X = X[mask]
        y = y[mask]

        self.model.fit(X, y)

    def predict_proba(self, row: pd.Series) -> float:
        X = row[["Close", "MA_20", "MA_50", "RSI"]].values.reshape(1, -1)
        prob = self.model.predict_proba(X)[0][1]
        return prob
