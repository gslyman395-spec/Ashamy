from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List


@dataclass
class TrainingUpdate:
    date: str
    type: str
    model: str
    accuracy_before: float
    accuracy_after: float

    @property
    def improvement(self) -> float:
        return round(self.accuracy_after - self.accuracy_before, 2)


class ModelManager:
    def __init__(self) -> None:
        self.current_version = "v2.3.1"
        self.available_versions: List[str] = ["v2.3.1", "v2.3.0", "v2.2.9"]
        self.archive: List[str] = ["v1.2", "v1.1", "v1.0"]
        now = datetime.now(timezone.utc)
        self.last_update = now
        self.next_retraining = now + timedelta(days=7)
        self.training_updates: List[TrainingUpdate] = []

    def add_training_update(self, update_type: str, model: str, before: float, after: float) -> None:
        entry = TrainingUpdate(
            date=datetime.now(timezone.utc).date().isoformat(),
            type=update_type,
            model=model,
            accuracy_before=before,
            accuracy_after=after,
        )
        self.training_updates.insert(0, entry)
        self.last_update = datetime.now(timezone.utc)
        self.next_retraining = self.last_update + timedelta(days=7)

    def versions(self) -> Dict:
        return {
            "current_version": self.current_version,
            "available_versions": self.available_versions,
            "archive": self.archive,
        }

    def rollback(self, version: str) -> Dict:
        if version not in self.available_versions:
            return {"status": "failed", "reason": "Requested version is unavailable"}
        self.current_version = version
        self.last_update = datetime.now(timezone.utc)
        return {
            "status": "success",
            "new_version": version,
            "reason": "Rolling back to stable version",
        }

    def training_history(self) -> Dict:
        return {
            "recent_updates": [
                {
                    "date": item.date,
                    "type": item.type,
                    "model": item.model,
                    "accuracy_before": item.accuracy_before,
                    "accuracy_after": item.accuracy_after,
                    "improvement": item.improvement,
                }
                for item in self.training_updates
            ]
        }
