"""
Signal combiner - merges technical signals with ML model predictions.
"""
import pandas as pd
import numpy as np
from loguru import logger
from typing import Optional


class SignalCombiner:
    """
    Combines validated technical signals with ML price direction predictions
    to produce a single high-confidence trading recommendation.

    Scoring:
        - Each validated technical signal contributes ±1 * weight_technical
        - ML model direction prediction contributes ±1 * weight_ml
        - Final signal = sign(combined_score) if abs(score) >= threshold
    """

    STRATEGY_WEIGHTS = {
        "ma": 0.10,
        "rsi": 0.12,
        "macd": 0.12,
        "bb": 0.10,
        "stoch": 0.10,
        "atr": 0.05,
        "vwap": 0.12,
        "fib": 0.08,
        "ichimoku": 0.12,
        "camarilla": 0.09,
    }

    def __init__(
        self,
        ml_weight: float = 0.40,
        signal_threshold: float = 0.50,
    ):
        self.ml_weight = ml_weight
        self.signal_threshold = signal_threshold
        # Remaining weight goes to technical signals
        self.tech_weight = 1.0 - ml_weight

    def combine(
        self,
        df: pd.DataFrame,
        ml_predictions: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """
        Produce a 'Final_Signal' and 'Confidence' column.

        Args:
            df: DataFrame with 'Valid_Signal' and individual strategy signal columns.
            ml_predictions: Optional array of ML-predicted price changes
                            (positive = up, negative = down).
        Returns:
            df with 'Final_Signal', 'Confidence', and 'Recommendation' columns.
        """
        df = df.copy()

        # Weighted technical score
        tech_score = pd.Series(0.0, index=df.index)
        for strategy_name, weight in self.STRATEGY_WEIGHTS.items():
            col = f"{strategy_name}_Signal"
            if col in df.columns:
                tech_score += df[col].fillna(0) * weight

        # Normalize to [-1, 1]
        total_weight = sum(
            w for s, w in self.STRATEGY_WEIGHTS.items() if f"{s}_Signal" in df.columns
        )
        if total_weight > 0:
            tech_score = tech_score / total_weight

        # ML score
        ml_score = pd.Series(0.0, index=df.index)
        if ml_predictions is not None:
            ml_direction = np.sign(ml_predictions.flatten())
            ml_score = pd.Series(ml_direction[: len(df)], index=df.index[: len(ml_direction)])
            ml_score = ml_score.reindex(df.index, fill_value=0.0)

        combined = self.tech_weight * tech_score + self.ml_weight * ml_score

        df["Combined_Score"] = combined
        df["Final_Signal"] = np.where(
            combined >= self.signal_threshold, 1,
            np.where(combined <= -self.signal_threshold, -1, 0),
        )
        df["Confidence"] = combined.abs().clip(upper=1.0)

        df["Recommendation"] = df["Final_Signal"].map(
            {1: "BUY", -1: "SELL", 0: "HOLD"}
        ).fillna("HOLD")

        logger.info(
            f"Final signals: BUY={( df['Final_Signal']==1).sum()}, "
            f"SELL={(df['Final_Signal']==-1).sum()}, "
            f"HOLD={(df['Final_Signal']==0).sum()}"
        )
        return df
