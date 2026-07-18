"""
Data processor - cleans, normalizes, and enriches OHLCV data.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from loguru import logger
from typing import Tuple


class DataProcessor:
    """Processes and transforms raw OHLCV data."""

    def __init__(self):
        self.scalers: dict = {}

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicates, fill gaps, and handle missing values.
        """
        df = df.copy()

        # Remove duplicate indices
        df = df[~df.index.duplicated(keep="last")]

        # Sort by date
        df.sort_index(inplace=True)

        # Forward-fill then backward-fill missing values
        df.ffill(inplace=True)
        df.bfill(inplace=True)

        # Remove rows where all OHLCV are zero or NaN
        df = df[(df[["Open", "High", "Low", "Close", "Volume"]] != 0).any(axis=1)]
        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)

        # Fix OHLC consistency
        df["High"] = df[["Open", "High", "Low", "Close"]].max(axis=1)
        df["Low"] = df[["Open", "High", "Low", "Close"]].min(axis=1)

        logger.debug(f"Cleaned DataFrame: {len(df)} rows")
        return df

    def remove_anomalies(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect and remove anomalous price movements using Z-score method.
        """
        df = df.copy()
        returns = df["Close"].pct_change().dropna()
        z_scores = np.abs((returns - returns.mean()) / returns.std())
        anomaly_mask = z_scores > threshold
        anomaly_count = anomaly_mask.sum()
        if anomaly_count > 0:
            logger.warning(f"Detected {anomaly_count} anomalous rows; replacing with forward fill")
            df.loc[anomaly_mask.index[anomaly_mask], "Close"] = np.nan
            df["Close"].ffill(inplace=True)
        return df

    def add_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add daily return columns."""
        df = df.copy()
        df["Returns"] = df["Close"].pct_change()
        df["Log_Returns"] = np.log(df["Close"] / df["Close"].shift(1))
        df.dropna(subset=["Returns"], inplace=True)
        return df

    def normalize_minmax(
        self, df: pd.DataFrame, columns: list, feature_range: Tuple[float, float] = (0, 1)
    ) -> pd.DataFrame:
        """Apply Min-Max normalization to specified columns."""
        df = df.copy()
        scaler = MinMaxScaler(feature_range=feature_range)
        df[columns] = scaler.fit_transform(df[columns])
        self.scalers["minmax"] = scaler
        return df

    def normalize_standard(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """Apply Z-score (Standard) normalization to specified columns."""
        df = df.copy()
        scaler = StandardScaler()
        df[columns] = scaler.fit_transform(df[columns])
        self.scalers["standard"] = scaler
        return df

    def create_sequences(
        self, data: np.ndarray, sequence_length: int, horizon: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sliding-window sequences for time-series models.

        Returns:
            X: (samples, sequence_length, features)
            y: (samples, horizon)
        """
        X, y = [], []
        for i in range(len(data) - sequence_length - horizon + 1):
            X.append(data[i : i + sequence_length])
            y.append(data[i + sequence_length : i + sequence_length + horizon, 3])  # Close price index 3
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Select and prepare numerical feature matrix from an enriched DataFrame."""
        feature_cols = [
            "Open", "High", "Low", "Close", "Volume",
            "SMA_20", "SMA_50", "EMA_20", "EMA_50",
            "RSI", "MACD", "MACD_Signal",
            "BB_Upper", "BB_Middle", "BB_Lower",
            "Stoch_K", "Stoch_D",
            "ATR", "VWAP",
        ]
        available = [c for c in feature_cols if c in df.columns]
        data = df[available].copy()
        data.ffill(inplace=True)
        data.bfill(inplace=True)
        data.fillna(0, inplace=True)
        return data.values.astype(np.float32)
