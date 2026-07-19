import unittest

from fastapi.testclient import TestClient

from backend.api.routes import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["mode"], "mock")

    def test_leaderboard_endpoint(self) -> None:
        response = self.client.get("/api/v1/leaderboard")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("top_gainers", payload)
        self.assertGreaterEqual(len(payload["top_gainers"]), 3)
        self.assertIn("symbol", payload["top_gainers"][0])

    def test_signal_endpoint(self) -> None:
        response = self.client.get("/api/v1/signals/NVDA?timeframes=1D,4H")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["symbol"], "NVDA")
        self.assertIn(payload["direction"], {"BUY", "SELL"})
        self.assertEqual(payload["timeframes"], ["1D", "4H"])

    def test_run_tests_endpoint(self) -> None:
        response = self.client.post("/api/v1/ai/run-tests", json={"test_type": "all"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["failed_tests"], 0)

    def test_other_ai_endpoints(self) -> None:
        endpoints = [
            ("/api/v1/ai/optimize", {"optimization_level": "high", "target": "all"}),
            ("/api/v1/ai/update-models", {"models": ["all"], "auto_optimize": True}),
            ("/api/v1/ai/cleanup", None),
            ("/api/v1/ai/security-scan", None),
        ]

        for path, payload in endpoints:
            with self.subTest(path=path):
                response = self.client.post(path, json=payload)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["success"])

    def test_websocket_stream(self) -> None:
        with self.client.websocket_connect("/ws/signals") as websocket:
            payload = websocket.receive_json()
            websocket.close()

        self.assertEqual(payload["type"], "signal_update")
        self.assertIn("symbol", payload)
        self.assertIn("final_confidence", payload)
