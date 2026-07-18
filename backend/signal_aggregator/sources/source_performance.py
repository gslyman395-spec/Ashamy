from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SourceMetric:
    name: str
    weight: float
    accuracy: float
    previous_accuracy: float = field(default=0.0)
    signals_tracked: int = field(default=0)

    def apply_accuracy(self, new_accuracy: float) -> None:
        self.previous_accuracy = self.accuracy
        self.accuracy = new_accuracy


class SourcePerformanceTracker:
    """Tracks source performance and updates dynamic weights."""

    MIN_WEIGHT = 0.02
    MAX_WEIGHT = 0.25

    def __init__(self) -> None:
        self._sources: Dict[str, SourceMetric] = {
            "polygon_io": SourceMetric("polygon_io", 0.10, 0.94),
            "tradingview": SourceMetric("tradingview", 0.10, 0.87),
            "bloomberg": SourceMetric("bloomberg", 0.10, 0.90),
            "finviz": SourceMetric("finviz", 0.10, 0.86),
            "seeking_alpha": SourceMetric("seeking_alpha", 0.10, 0.85),
            "yahoo_finance": SourceMetric("yahoo_finance", 0.10, 0.86),
            "alphavantage": SourceMetric("alphavantage", 0.10, 0.88),
            "marketwatch": SourceMetric("marketwatch", 0.10, 0.88),
            "thinkorswim": SourceMetric("thinkorswim", 0.10, 0.89),
            "stocktwits": SourceMetric("stocktwits", 0.10, 0.76),
        }

    def register_signal_result(self, source_name: str, correct: bool) -> None:
        if source_name not in self._sources:
            self._sources[source_name] = SourceMetric(source_name, 0.10, 0.50)
        source = self._sources[source_name]
        source.signals_tracked += 1
        hits = round(source.accuracy * (source.signals_tracked - 1))
        hits = hits + 1 if correct else hits
        source.apply_accuracy(hits / source.signals_tracked)

    def recalculate_weights(self) -> Dict[str, float]:
        """Weekly weight update:
        new_weight = old_weight * (1 + accuracy_delta * 0.1)
        """
        updated = {}
        for name, source in self._sources.items():
            accuracy_delta = source.accuracy - source.previous_accuracy
            weight = source.weight * (1 + (accuracy_delta * 0.1))
            weight = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, weight))
            updated[name] = weight

        total = sum(updated.values()) or 1.0
        for name, weight in updated.items():
            self._sources[name].weight = weight / total
        return {name: item.weight for name, item in self._sources.items()}

    def snapshot(self) -> Dict[str, Dict]:
        return {
            name: {
                "weight": round(source.weight, 4),
                "accuracy": round(source.accuracy, 4),
                "change_from_last_week": round(source.accuracy - source.previous_accuracy, 4),
                "signals_tracked": source.signals_tracked,
            }
            for name, source in self._sources.items()
        }

