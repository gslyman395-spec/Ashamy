"""
Scoring module – assigns a final composite score and ranking to
FusedSignals, and builds the top gainers / losers leaderboard.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from signal_aggregator.fusion.ai_fusion import FusedSignal
from signal_aggregator.sources.connector import SignalDirection

logger = logging.getLogger(__name__)


@dataclass
class SignalScore:
    """Final ranked score for a symbol."""

    symbol: str
    timeframe: str
    rank: int
    composite_score: float         # 0-100
    direction: SignalDirection
    stars: int
    final_confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    risk_reward: float
    win_probability: float
    alert_level: str
    fused_signal: FusedSignal
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def label(self) -> str:
        return f"{'📈' if self.direction in (SignalDirection.BUY, SignalDirection.STRONG_BUY) else '📉'} {self.symbol}"


class SignalScorer:
    """
    Converts FusedSignals into ranked SignalScores and produces
    top gainers / losers leaderboards.
    """

    def score(self, fused: FusedSignal) -> float:
        """Compute composite 0-100 score from a FusedSignal."""
        # Strength of directional conviction (0-1)
        conviction = abs(fused.fused_score - 0.5) * 2

        # Reward high agreement and confidence
        raw = (
            0.40 * fused.final_confidence
            + 0.30 * conviction
            + 0.20 * fused.agreement_pct
            + 0.10 * min(fused.risk_reward / 5.0, 1.0)
        )
        return round(raw * 100, 2)

    def rank_signals(
        self,
        fused_signals: List[FusedSignal],
    ) -> List[SignalScore]:
        """Score and rank all fused signals."""
        scored: List[Tuple[float, FusedSignal]] = [
            (self.score(fs), fs) for fs in fused_signals
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        results: List[SignalScore] = []
        for rank, (score, fs) in enumerate(scored, start=1):
            results.append(
                SignalScore(
                    symbol=fs.symbol,
                    timeframe=fs.timeframe,
                    rank=rank,
                    composite_score=score,
                    direction=fs.direction,
                    stars=fs.stars,
                    final_confidence=fs.final_confidence,
                    entry_price=fs.entry_price,
                    target_price=fs.target_price,
                    stop_loss=fs.stop_loss,
                    risk_reward=fs.risk_reward,
                    win_probability=fs.win_probability,
                    alert_level=fs.alert_level,
                    fused_signal=fs,
                )
            )
        return results

    def top_gainers(
        self,
        scored: List[SignalScore],
        n: int = 10,
    ) -> List[SignalScore]:
        """Top N bullish signals."""
        bullish = [
            s for s in scored
            if s.direction in (SignalDirection.BUY, SignalDirection.STRONG_BUY)
        ]
        return sorted(bullish, key=lambda s: s.composite_score, reverse=True)[:n]

    def top_losers(
        self,
        scored: List[SignalScore],
        n: int = 10,
    ) -> List[SignalScore]:
        """Top N bearish signals."""
        bearish = [
            s for s in scored
            if s.direction in (SignalDirection.SELL, SignalDirection.STRONG_SELL)
        ]
        return sorted(bearish, key=lambda s: s.composite_score, reverse=True)[:n]

    def leaderboard(
        self,
        scored: List[SignalScore],
        n: int = 10,
    ) -> Dict[str, List[SignalScore]]:
        """Build full leaderboard: gainers, losers, neutral."""
        return {
            "top_gainers": self.top_gainers(scored, n),
            "top_losers": self.top_losers(scored, n),
            "neutral": [
                s for s in scored
                if s.direction == SignalDirection.NEUTRAL
            ][:n],
        }
