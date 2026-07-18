import unittest

from backend.api.routes.learning import LearningAPI
from backend.signal_aggregator.sources.source_performance import SourcePerformanceTracker


class LearningAPITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api = LearningAPI()

    def test_status_contains_required_fields(self) -> None:
        status = self.api.get_status()
        self.assertIn("model_version", status)
        self.assertIn("current_accuracy", status)
        self.assertIn("next_retraining", status)
        self.assertIn("source_weights", status)
        self.assertIn("alerts", status)

    def test_post_signal_outcome_updates_performance_and_history(self) -> None:
        payload = {
            "signal_id": "sig_1",
            "symbol": "NVDA",
            "predicted_direction": "BUY",
            "actual_direction": "UP",
            "entry": 100,
            "exit": 110,
            "profit": 10,
            "win": True,
            "source": "polygon_io",
        }
        response = self.api.post_signal_outcome(payload)
        self.assertEqual("recorded", response["status"])
        performance = self.api.get_performance()
        self.assertEqual(1, performance["predictions_made"])
        self.assertEqual(1, performance["correct_predictions"])
        history = self.api.get_training_history()
        self.assertEqual(1, len(history["recent_updates"]))

    def test_model_rollback(self) -> None:
        result = self.api.rollback_version("v2.3.0")
        self.assertEqual("success", result["status"])
        versions = self.api.get_model_versions()
        self.assertEqual("v2.3.0", versions["current_version"])


class SourceWeightingTestCase(unittest.TestCase):
    def test_recalculate_weights_keeps_bounds_and_normalization(self) -> None:
        tracker = SourcePerformanceTracker()
        for _ in range(3):
            tracker.register_signal_result("polygon_io", True)
            tracker.register_signal_result("stocktwits", False)
        weights = tracker.recalculate_weights()
        self.assertAlmostEqual(1.0, sum(weights.values()), places=6)
        self.assertTrue(all(0.02 <= weight <= 0.25 for weight in weights.values()))


if __name__ == "__main__":
    unittest.main()

