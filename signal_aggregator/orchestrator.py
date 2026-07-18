"""
Main orchestrator – drives the full pipeline:
  1. Collect from all 10 sources (parallel)
  2. Validate quality
  3. Aggregate (global score)
  4. Fuse with AI (final score)
  5. Score & rank
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from signal_aggregator.aggregation.engine import AggregationEngine
from signal_aggregator.fusion.ai_fusion import AIFusion, FusedSignal
from signal_aggregator.scoring.scorer import SignalScore, SignalScorer
from signal_aggregator.sources.connector import SourceConnector

logger = logging.getLogger(__name__)

SUPPORTED_TIMEFRAMES = ["1D", "4H", "30M"]


@dataclass
class AnalysisResult:
    """Full result for one symbol across all requested timeframes."""

    symbol: str
    timeframes: Dict[str, FusedSignal] = field(default_factory=dict)
    scores: Dict[str, SignalScore] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def best_timeframe(self) -> Optional[str]:
        if not self.scores:
            return None
        return max(self.scores, key=lambda tf: self.scores[tf].composite_score)


class SignalOrchestrator:
    """
    High-level entry point for the signal aggregator system.

    Usage::

        orchestrator = SignalOrchestrator()
        results = await orchestrator.analyse(["NVDA", "AAPL"], ["1D", "4H"])
        leaderboard = orchestrator.leaderboard(results)
    """

    def __init__(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        timeframes: Optional[List[str]] = None,
    ):
        self._connector = SourceConnector(api_keys=api_keys)
        self._aggregator = AggregationEngine()
        self._fusion = AIFusion()
        self._scorer = SignalScorer()
        self._timeframes = timeframes or SUPPORTED_TIMEFRAMES

    # ── public API ───────────────────────────────────────────────────────────

    async def analyse(
        self,
        symbols: List[str],
        timeframes: Optional[List[str]] = None,
        *,
        session: Optional[Any] = None,
    ) -> List[AnalysisResult]:
        """
        Analyse a list of symbols across the requested timeframes.
        All fetches run concurrently.
        """
        tfs = timeframes or self._timeframes
        tasks = [
            self._analyse_symbol(sym, tfs, session=session)
            for sym in symbols
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def leaderboard_async(
        self,
        symbols: List[str],
        timeframe: str = "1D",
        n: int = 10,
        *,
        session: Optional[Any] = None,
    ) -> Dict[str, List[SignalScore]]:
        """
        Fetch, analyse and return a leaderboard for `symbols` on `timeframe`.
        """
        results = await self.analyse(symbols, [timeframe], session=session)
        all_scores = [
            res.scores[timeframe]
            for res in results
            if timeframe in res.scores
        ]
        return self._scorer.leaderboard(all_scores, n=n)

    def leaderboard(
        self,
        results: List[AnalysisResult],
        timeframe: str = "1D",
        n: int = 10,
    ) -> Dict[str, List[SignalScore]]:
        """Build leaderboard from already-computed results."""
        all_scores = [
            res.scores[timeframe]
            for res in results
            if timeframe in res.scores
        ]
        return self._scorer.leaderboard(all_scores, n=n)

    # ── internal ─────────────────────────────────────────────────────────────

    async def _analyse_symbol(
        self,
        symbol: str,
        timeframes: List[str],
        *,
        session: Optional[Any],
    ) -> AnalysisResult:
        result = AnalysisResult(symbol=symbol)
        tasks = {
            tf: self._analyse_one(symbol, tf, session=session)
            for tf in timeframes
        }
        gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for tf, outcome in zip(tasks.keys(), gathered):
            if isinstance(outcome, Exception):
                logger.warning("Error analysing %s/%s: %s", symbol, tf, outcome)
            elif outcome is not None:
                fused, score = outcome
                result.timeframes[tf] = fused
                result.scores[tf] = score
        return result

    async def _analyse_one(
        self,
        symbol: str,
        timeframe: str,
        *,
        session: Optional[Any],
    ):
        raw = await self._connector.collect_all(symbol, timeframe, session=session)
        agg = self._aggregator.aggregate(raw, symbol, timeframe)
        if agg is None:
            return None
        fused = self._fusion.fuse(agg)
        score = self._scorer.score(fused)
        signal_score = SignalScore(
            symbol=symbol,
            timeframe=timeframe,
            rank=0,
            composite_score=score,
            direction=fused.direction,
            stars=fused.stars,
            final_confidence=fused.final_confidence,
            entry_price=fused.entry_price,
            target_price=fused.target_price,
            stop_loss=fused.stop_loss,
            risk_reward=fused.risk_reward,
            win_probability=fused.win_probability,
            alert_level=fused.alert_level,
            fused_signal=fused,
        )
        return fused, signal_score
