from __future__ import annotations

from typing import Dict

from backend.learning.outcome_tracker import OutcomeTracker
from backend.ml_models.models.model_manager import ModelManager
from backend.monitoring.alerts import AlertManager
from backend.signal_aggregator.sources.source_performance import SourcePerformanceTracker


class LearningAPI:
    """In-process API layer exposing required learning endpoints."""

    ACCURACY_THRESHOLD = 85.0
    DEFAULT_TRAINING_MODEL = "lstm"

    def __init__(self) -> None:
        self.outcomes = OutcomeTracker()
        self.source_tracker = SourcePerformanceTracker()
        self.model_manager = ModelManager()
        self.alerts = AlertManager()
        self._last_accuracy = 0.0
        self._previous_accuracy = 0.0

    def get_status(self) -> Dict:
        summary = self.outcomes.summary()
        self.alerts.check_accuracy(summary["accuracy"])
        return {
            "model_version": self.model_manager.current_version,
            "current_accuracy": summary["accuracy"],
            "last_update": self.model_manager.last_update.isoformat(),
            "next_retraining": self.model_manager.next_retraining.isoformat(),
            "source_weights": self.source_tracker.snapshot(),
            "alerts": self.alerts.list_alerts()["alerts"],
        }

    def get_performance(self) -> Dict:
        summary = self.outcomes.summary()
        summary_7d = self.outcomes.summary(days=7)
        summary_30d = self.outcomes.summary(days=30)
        if summary["predictions_made"] == 0:
            trend = "stable"
        elif self._last_accuracy > self._previous_accuracy:
            trend = "improving"
        elif self._last_accuracy < self._previous_accuracy:
            trend = "declining"
        else:
            trend = "stable"
        return {
            "accuracy": summary["accuracy"],
            "win_rate": summary["accuracy"],
            "trend": trend,
            "last_7_days": summary_7d["accuracy"],
            "last_30_days": summary_30d["accuracy"],
            "predictions_made": summary["predictions_made"],
            "correct_predictions": summary["correct_predictions"],
        }

    def get_source_weights(self) -> Dict:
        return {"sources": self.source_tracker.snapshot()}

    def get_training_history(self) -> Dict:
        return self.model_manager.training_history()

    def get_alerts(self) -> Dict:
        return self.alerts.list_alerts()

    def post_signal_outcome(self, payload: Dict) -> Dict:
        outcome = self.outcomes.add(payload)
        source_name = payload.get("source")
        if source_name:
            self.source_tracker.register_signal_result(source_name, outcome.win)
            old_weight = self.source_tracker.get_weight(source_name)
            if self.source_tracker.recalculate_if_due():
                new_weight = self.source_tracker.get_weight(source_name)
                self.alerts.check_weight_change(source_name, new_weight - old_weight)

        performance = self.outcomes.summary()
        self.alerts.check_accuracy(performance["accuracy"])
        self._previous_accuracy = self._last_accuracy
        self.model_manager.add_training_update(
            update_type="signal_outcome_update",
            model=self.DEFAULT_TRAINING_MODEL,
            before=self._last_accuracy,
            after=performance["accuracy"],
        )
        self._last_accuracy = performance["accuracy"]
        return {"status": "recorded", "signal": payload}

    def get_model_versions(self) -> Dict:
        return self.model_manager.versions()

    def rollback_version(self, version: str) -> Dict:
        return self.model_manager.rollback(version)
