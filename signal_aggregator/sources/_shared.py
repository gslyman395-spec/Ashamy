"""Shared utilities for source connectors."""
import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from signal_aggregator.sources.connector import SignalDirection, SourceName, SourceSignal


def _direction_from_score(score: float) -> SignalDirection:
    if score >= 0.70:
        return SignalDirection.STRONG_BUY
    if score >= 0.55:
        return SignalDirection.BUY
    if score >= 0.45:
        return SignalDirection.NEUTRAL
    if score >= 0.30:
        return SignalDirection.SELL
    return SignalDirection.STRONG_SELL


def _compute_technical_score(
    price: float,
    sma20: float,
    sma50: float,
    rsi: float,
    macd: float,
    volume_ratio: float,
) -> float:
    """Return a 0-1 bullish score from common technical indicators."""
    score = 0.0
    # Price vs moving averages
    if price > sma20:
        score += 0.20
    if price > sma50:
        score += 0.15
    if sma20 > sma50:
        score += 0.15
    # RSI
    if 40 <= rsi <= 70:
        score += 0.20
    elif rsi < 30:
        score += 0.10  # oversold → potential reversal
    elif rsi > 80:
        score -= 0.05   # overbought
    # MACD
    if macd > 0:
        score += 0.15
    # Volume confirmation
    if volume_ratio > 1.2:
        score += 0.15
    return max(0.0, min(1.0, score))


def _make_signal(
    source: SourceName,
    symbol: str,
    timeframe: str,
    price: float,
    score: float,
    indicators: Dict[str, Any],
    accuracy: float,
) -> SourceSignal:
    direction = _direction_from_score(score)
    confidence = accuracy * score if direction in (SignalDirection.STRONG_BUY, SignalDirection.BUY) else accuracy * (1 - score)
    confidence = max(0.60, min(0.99, confidence + 0.05))
    return SourceSignal(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        direction=direction,
        confidence=confidence,
        price=price,
        timestamp=datetime.now(timezone.utc),
        indicators=indicators,
    )


def _simulate_market_data(symbol: str, timeframe: str) -> Tuple[float, Dict[str, Any]]:
    """Return deterministic-ish simulated market data for a symbol."""
    seed = sum(ord(c) for c in symbol + timeframe)
    rng = random.Random(seed + int(datetime.now(timezone.utc).timestamp() // 300))  # 5-min buckets
    price = rng.uniform(50, 800)
    sma20 = price * rng.uniform(0.95, 1.05)
    sma50 = price * rng.uniform(0.90, 1.10)
    rsi = rng.uniform(25, 75)
    macd = rng.uniform(-2, 3)
    volume_ratio = rng.uniform(0.6, 2.0)
    indicators = {
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "rsi": round(rsi, 2),
        "macd": round(macd, 4),
        "volume_ratio": round(volume_ratio, 3),
    }
    return round(price, 2), indicators


async def fetch_generic_signal(
    connector: Any,
    symbol: str,
    timeframe: str,
    *,
    session: Optional[Any],
) -> Optional[SourceSignal]:
    """Generic fallback: compute signal from simulated (or injected) market data."""
    price, indicators = _simulate_market_data(symbol, timeframe)
    score = _compute_technical_score(
        price,
        indicators["sma20"],
        indicators["sma50"],
        indicators["rsi"],
        indicators["macd"],
        indicators["volume_ratio"],
    )
    return _make_signal(
        connector.source_name,
        symbol,
        timeframe,
        price,
        score,
        indicators,
        connector.base_accuracy,
    )
