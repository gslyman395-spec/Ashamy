"""
Aggregation engine – combines signals from all validated sources using
a dynamic weight system based on historical accuracy.

Formula: Global Consensus = weighted average of all source signals
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from signal_aggregator.parsers.signal_parser import ParsedSignal, SignalParser
from signal_aggregator.sources.connector import (
    SOURCE_ACCURACY,
    SignalDirection,
    SourceName,
    SourceSignal,
)
from signal_aggregator.validators.quality_validator import QualityValidator

logger = logging.getLogger(__name__)


@dataclass
class AggregatedSignal:
    """Result of aggregating all source signals."""

    symbol: str
    timeframe: str
    direction: SignalDirection
    global_score: float            # 0-1 weighted consensus
    agreement_pct: float           # % of sources that agree with majority
    sources_count: int             # number of valid sources used
    source_details: Dict[str, dict] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AggregationEngine:
    """
    Aggregates SourceSignals into a single AggregatedSignal using
    historically-calibrated weights.
    """

    def __init__(
        self,
        accuracy_weights: Optional[Dict[SourceName, float]] = None,
        performance_tracker: Optional[dict] = None,
    ):
        self._base_weights = accuracy_weights or SOURCE_ACCURACY
        self._performance = performance_tracker or {}
        self._parser = SignalParser()
        self._validator = QualityValidator()

    # ── public API ───────────────────────────────────────────────────────────

    def aggregate(
        self,
        raw_signals: List[SourceSignal],
        symbol: str,
        timeframe: str,
    ) -> Optional[AggregatedSignal]:
        """Validate, parse and aggregate raw signals."""
        if not raw_signals:
            return None

        valid, _ = self._validator.validate(raw_signals)
        if not valid:
            logger.warning("No valid signals for %s/%s", symbol, timeframe)
            return None

        weights = self._effective_weights()
        parsed = self._parser.parse(valid, weights)

        return self._compute(parsed, symbol, timeframe, valid)

    def update_performance(self, source: SourceName, accuracy: float) -> None:
        """Feed back real accuracy to adjust future weights dynamically."""
        self._performance[source] = max(0.0, min(1.0, accuracy))

    # ── internal ─────────────────────────────────────────────────────────────

    def _effective_weights(self) -> Dict[SourceName, float]:
        """Blend base accuracy weights with real-time performance feedback."""
        weights: Dict[SourceName, float] = {}
        for source, base_w in self._base_weights.items():
            perf_w = self._performance.get(source, base_w)
            weights[source] = 0.70 * base_w + 0.30 * perf_w
        return weights

    @staticmethod
    def _compute(
        parsed: List[ParsedSignal],
        symbol: str,
        timeframe: str,
        valid_raw: List[SourceSignal],
    ) -> AggregatedSignal:
        total_weight = sum(p.source_weight for p in parsed)
        if total_weight == 0:
            total_weight = 1.0

        # Weighted directional score (0-1)
        global_score = sum(
            p.numeric_direction * p.source_weight for p in parsed
        ) / total_weight

        # Overall direction
        direction = SignalParser.numeric_to_direction(global_score)

        # Agreement: % of sources whose direction matches the overall
        matching = sum(1 for p in parsed if _coarse(p.numeric_direction) == _coarse(global_score))
        agreement_pct = matching / len(parsed) if parsed else 0.0

        # Per-source detail
        details: Dict[str, dict] = {}
        for sig in valid_raw:
            details[sig.source.value] = {
                "direction": sig.direction.value,
                "confidence": round(sig.confidence, 4),
                "quality_score": round(sig.quality_score, 4),
                "price": sig.price,
            }

        return AggregatedSignal(
            symbol=symbol,
            timeframe=timeframe,
            direction=direction,
            global_score=round(global_score, 4),
            agreement_pct=round(agreement_pct, 4),
            sources_count=len(parsed),
            source_details=details,
        )


def _coarse(score: float) -> int:
    """Map 0-1 numeric score to coarse bucket: -1=bearish, 0=neutral, 1=bullish."""
    if score >= 0.625:
        return 1
    if score >= 0.375:
        return 0
    return -1
