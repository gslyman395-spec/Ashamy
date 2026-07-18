from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class SignalOutcome:
    signal_id: str
    symbol: str
    predicted_direction: str
    actual_direction: str
    entry: float
    exit: float
    profit: float
    win: bool
    timestamp: str

    @classmethod
    def from_payload(cls, payload: Dict) -> "SignalOutcome":
        timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
        return cls(
            signal_id=payload["signal_id"],
            symbol=payload["symbol"],
            predicted_direction=payload["predicted_direction"],
            actual_direction=payload["actual_direction"],
            entry=float(payload["entry"]),
            exit=float(payload["exit"]),
            profit=float(payload["profit"]),
            win=bool(payload["win"]),
            timestamp=timestamp,
        )


class OutcomeTracker:
    """Tracks historical outcomes for issued signals."""

    def __init__(self) -> None:
        self._outcomes: List[SignalOutcome] = []

    def add(self, payload: Dict) -> SignalOutcome:
        outcome = SignalOutcome.from_payload(payload)
        self._outcomes.append(outcome)
        return outcome

    def all(self) -> List[Dict]:
        return [asdict(item) for item in self._outcomes]

    def summary(self) -> Dict:
        total = len(self._outcomes)
        wins = sum(1 for outcome in self._outcomes if outcome.win)
        accuracy = round((wins / total) * 100, 2) if total else 0.0
        return {
            "predictions_made": total,
            "correct_predictions": wins,
            "win_rate": accuracy,
            "accuracy": accuracy,
        }

