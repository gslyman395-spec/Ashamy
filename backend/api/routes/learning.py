from __future__ import annotations

from typing import Dict

from backend.learning.outcome_tracker import OutcomeTracker
from backend.ml_models.models.model_manager import ModelManager
from backend.monitoring.alerts import AlertManager
from backend.signal_aggregator.sources.source_performance import SourcePerformanceTracker


class LearningAPI:
    """In-process API layer exposing required learning endpoints."""

    def __init__(self) -> None:
        self.outcomes = OutcomeTracker()
        self.source_tracker = SourcePerformanceTracker()
        self.model_manager = ModelManager()
        self.alerts = AlertManager()

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
        trend = "improving" if summary["accuracy"] >= 85 else "declining"
        return {
            "accuracy": summary["accuracy"],
            "win_rate": summary["win_rate"],
            "trend": trend,
            "last_7_days": summary["accuracy"],
            "last_30_days": summary["accuracy"],
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
            old_weight = self.source_tracker.snapshot()[source_name]["weight"]
            self.source_tracker.recalculate_weights()
            new_weight = self.source_tracker.snapshot()[source_name]["weight"]
            self.alerts.check_weight_change(source_name, new_weight - old_weight)

        performance = self.outcomes.summary()
        self.alerts.check_accuracy(performance["accuracy"])
        self.model_manager.add_training_update(
            update_type="weekly_retrain",
            model="lstm",
            before=max(0.0, performance["accuracy"] - 1.0),
            after=performance["accuracy"],
        )
        return {"status": "recorded", "signal": payload}

    def get_model_versions(self) -> Dict:
        return self.model_manager.versions()

    def rollback_version(self, version: str) -> Dict:
        return self.model_manager.rollback(version)

