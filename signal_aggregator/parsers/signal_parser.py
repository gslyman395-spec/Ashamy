"""
Signal parser – normalises raw signals from different sources into a
uniform representation for downstream processing.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from signal_aggregator.sources.connector import SignalDirection, SourceSignal

logger = logging.getLogger(__name__)

DIRECTION_NUMERIC: dict[SignalDirection, float] = {
    SignalDirection.STRONG_BUY: 1.0,
    SignalDirection.BUY: 0.75,
    SignalDirection.NEUTRAL: 0.5,
    SignalDirection.SELL: 0.25,
    SignalDirection.STRONG_SELL: 0.0,
}


class ParsedSignal:
    """Normalised signal ready for aggregation."""

    __slots__ = (
        "source_signal",
        "numeric_direction",
        "weighted_confidence",
        "source_weight",
    )

    def __init__(self, source_signal: SourceSignal, source_weight: float):
        self.source_signal = source_signal
        self.source_weight = source_weight
        self.numeric_direction: float = DIRECTION_NUMERIC[source_signal.direction]
        self.weighted_confidence: float = source_signal.confidence * source_weight


class SignalParser:
    """Parse and normalise a list of raw source signals."""

    def parse(
        self,
        raw_signals: List[SourceSignal],
        source_weights: Optional[dict] = None,
    ) -> List[ParsedSignal]:
        parsed: List[ParsedSignal] = []
        for sig in raw_signals:
            weight = (source_weights or {}).get(sig.source, sig.quality_score)
            try:
                parsed.append(ParsedSignal(sig, weight))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to parse signal from %s: %s", sig.source, exc)
        return parsed

    @staticmethod
    def numeric_to_direction(value: float) -> SignalDirection:
        if value >= 0.875:
            return SignalDirection.STRONG_BUY
        if value >= 0.625:
            return SignalDirection.BUY
        if value >= 0.375:
            return SignalDirection.NEUTRAL
        if value >= 0.125:
            return SignalDirection.SELL
        return SignalDirection.STRONG_SELL
