"""
Quality validator – filters out low-quality or stale signals before
aggregation, and assigns a quality score to each signal.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from signal_aggregator.sources.connector import SourceSignal

logger = logging.getLogger(__name__)

# Maximum age (minutes) a signal can be before it is considered stale
STALE_THRESHOLD_MINUTES: dict[str, int] = {
    "1D": 1440,
    "4H": 240,
    "30M": 30,
}
DEFAULT_STALE_MINUTES = 60

# Minimum confidence required to keep a signal
MIN_CONFIDENCE = 0.50


class QualityValidator:
    """Validates raw signals and annotates them with a quality score."""

    def __init__(
        self,
        min_confidence: float = MIN_CONFIDENCE,
        stale_thresholds: dict | None = None,
    ):
        self.min_confidence = min_confidence
        self.stale_thresholds = stale_thresholds or STALE_THRESHOLD_MINUTES

    def validate(
        self,
        signals: List[SourceSignal],
        now: datetime | None = None,
    ) -> Tuple[List[SourceSignal], List[SourceSignal]]:
        """
        Returns (valid_signals, rejected_signals).

        Each kept signal has its quality_score set (0-1).
        """
        now = now or datetime.now(timezone.utc)
        valid: List[SourceSignal] = []
        rejected: List[SourceSignal] = []

        for sig in signals:
            reasons = self._check(sig, now)
            if reasons:
                logger.debug(
                    "Rejected %s/%s signal from %s: %s",
                    sig.symbol,
                    sig.timeframe,
                    sig.source.value,
                    "; ".join(reasons),
                )
                rejected.append(sig)
            else:
                sig.quality_score = self._quality_score(sig, now)
                valid.append(sig)

        return valid, rejected

    # ── helpers ──────────────────────────────────────────────────────────────

    def _check(self, sig: SourceSignal, now: datetime) -> List[str]:
        reasons: List[str] = []
        if sig.confidence < self.min_confidence:
            reasons.append(f"confidence {sig.confidence:.2f} < {self.min_confidence}")
        stale_min = self.stale_thresholds.get(sig.timeframe, DEFAULT_STALE_MINUTES)
        age = (now - sig.timestamp).total_seconds() / 60
        if age > stale_min:
            reasons.append(f"stale ({age:.0f}m > {stale_min}m)")
        if sig.price <= 0:
            reasons.append("invalid price")
        return reasons

    @staticmethod
    def _quality_score(sig: SourceSignal, now: datetime) -> float:
        """Compute 0-1 quality score considering freshness and confidence."""
        stale_min = STALE_THRESHOLD_MINUTES.get(sig.timeframe, DEFAULT_STALE_MINUTES)
        age_min = (now - sig.timestamp).total_seconds() / 60
        freshness = max(0.0, 1.0 - (age_min / stale_min))
        return round(0.60 * sig.confidence + 0.40 * freshness, 4)
