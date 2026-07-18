from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


class AlertManager:
    def __init__(self) -> None:
        self._alerts: List[Dict] = []

    def add_warning(self, message: str) -> None:
        self._alerts.insert(
            0,
            {
                "level": "warning",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def check_accuracy(self, accuracy_percent: float) -> None:
        if accuracy_percent < 85:
            self.add_warning(f"Overall accuracy dropped below threshold: {accuracy_percent:.2f}%")

    def check_weight_change(self, source_name: str, change: float) -> None:
        if abs(change) > 0.10:
            self.add_warning(f"Source {source_name} weight change exceeded 10%")

    def list_alerts(self) -> Dict:
        return {"alerts": self._alerts}

