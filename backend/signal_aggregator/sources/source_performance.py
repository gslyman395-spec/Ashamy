from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SourceMetric:
    name: str
    weight: float
    accuracy: float
    previous_accuracy: float = field(default=0.0)
    signals_tracked: int = field(default=0)
    hits: int = field(default=0)

    def apply_accuracy(self, new_accuracy: float) -> None:
        self.previous_accuracy = self.accuracy
        self.accuracy = new_accuracy


class SourcePerformanceTracker:
    """Tracks source performance and updates dynamic weights."""

    MIN_WEIGHT = 0.02
    MAX_WEIGHT = 0.25
    WEIGHT_UPDATE_INTERVAL_DAYS = 7
    DEFAULT_WEIGHT = 0.10
    DEFAULT_ACCURACY = 0.50
    INITIAL_ACCURACY = {
        "polygon_io": 0.94,
        "tradingview": 0.87,
        "bloomberg": 0.90,
        "finviz": 0.86,
        "seeking_alpha": 0.85,
        "yahoo_finance": 0.86,
        "alphavantage": 0.88,
        "marketwatch": 0.88,
        "thinkorswim": 0.89,
        "stocktwits": 0.76,
    }

    def __init__(self) -> None:
        baseline_signals = 100
        default_weight = 1 / len(self.INITIAL_ACCURACY)
        self._sources: Dict[str, SourceMetric] = {
            name: SourceMetric(
                name=name,
                weight=default_weight,
                accuracy=accuracy,
                signals_tracked=baseline_signals,
                hits=int(accuracy * baseline_signals),
            )
            for name, accuracy in self.INITIAL_ACCURACY.items()
        }
        self._last_weight_update = datetime.now(timezone.utc)

    def register_signal_result(self, source_name: str, correct: bool) -> None:
        if source_name not in self._sources:
            self._sources[source_name] = SourceMetric(
                source_name, self.DEFAULT_WEIGHT, self.DEFAULT_ACCURACY
            )
        source = self._sources[source_name]
        source.signals_tracked += 1
        source.hits += 1 if correct else 0
        source.apply_accuracy(source.hits / source.signals_tracked)

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

        total = sum(updated.values())
        if total <= 0:
            raise ValueError(
                f"Source weights sum must be greater than zero during normalization. Current sum: {total}"
            )
        for name, weight in updated.items():
            self._sources[name].weight = weight / total
        self._last_weight_update = datetime.now(timezone.utc)
        return {name: item.weight for name, item in self._sources.items()}

    def recalculate_if_due(self) -> bool:
        due_at = self._last_weight_update + timedelta(days=self.WEIGHT_UPDATE_INTERVAL_DAYS)
        if datetime.now(timezone.utc) >= due_at:
            self.recalculate_weights()
            return True
        return False

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

    def get_weight(self, source_name: str) -> float:
        source = self._sources.get(source_name)
        if source is None:
            return 0.0
        return source.weight
