"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Ashamy Stock Analysis API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Data Sources
    YAHOO_FINANCE_ENABLED: bool = True
    ALPHA_VANTAGE_API_KEY: str = ""
    DEFAULT_INTERVAL: str = "1d"
    DEFAULT_PERIOD: str = "2y"

    # ML Models
    MODEL_DIR: str = "models"
    LSTM_HIDDEN_SIZE: int = 128
    LSTM_NUM_LAYERS: int = 3
    GRU_HIDDEN_SIZE: int = 128
    GRU_NUM_LAYERS: int = 3
    TRANSFORMER_D_MODEL: int = 128
    TRANSFORMER_NHEAD: int = 8
    TRANSFORMER_NUM_LAYERS: int = 4
    SEQUENCE_LENGTH: int = 60
    PREDICTION_HORIZON: int = 5
    BATCH_SIZE: int = 32
    EPOCHS: int = 100
    LEARNING_RATE: float = 0.001
    DROPOUT: float = 0.2

    # Signals
    SIGNAL_CONFIDENCE_THRESHOLD: float = 0.7
    MIN_SIGNAL_STRENGTH: float = 0.6
    MAX_FALSE_SIGNAL_RATIO: float = 0.1

    # Backtesting
    INITIAL_CAPITAL: float = 100000.0
    COMMISSION: float = 0.001
    SLIPPAGE: float = 0.0005

    # Cache
    CACHE_TTL: int = 300  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
