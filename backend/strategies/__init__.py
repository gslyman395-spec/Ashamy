"""
Strategies package.
"""
from .base import BaseStrategy
from .technical import MovingAverageStrategy
from .momentum import RSIStrategy, MACDStrategy
from .volatility import BollingerBandsStrategy, StochasticStrategy, ATRStrategy
from .trend import VWAPStrategy, FibonacciStrategy, IchimokuStrategy, CamarillaPivotStrategy

ALL_STRATEGIES = [
    MovingAverageStrategy(),
    RSIStrategy(),
    MACDStrategy(),
    BollingerBandsStrategy(),
    StochasticStrategy(),
    ATRStrategy(),
    VWAPStrategy(),
    FibonacciStrategy(),
    IchimokuStrategy(),
    CamarillaPivotStrategy(),
]

__all__ = [
    "BaseStrategy",
    "MovingAverageStrategy",
    "RSIStrategy",
    "MACDStrategy",
    "BollingerBandsStrategy",
    "StochasticStrategy",
    "ATRStrategy",
    "VWAPStrategy",
    "FibonacciStrategy",
    "IchimokuStrategy",
    "CamarillaPivotStrategy",
    "ALL_STRATEGIES",
]
