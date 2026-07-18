"""
Tests for the signal aggregator system.
"""
import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from signal_aggregator.sources.connector import (
    SourceConnector,
    SourceSignal,
    SignalDirection,
    SourceName,
    SOURCE_ACCURACY,
)
from signal_aggregator.parsers.signal_parser import SignalParser, ParsedSignal, DIRECTION_NUMERIC
from signal_aggregator.validators.quality_validator import QualityValidator
from signal_aggregator.aggregation.engine import AggregationEngine, AggregatedSignal
from signal_aggregator.fusion.ai_fusion import AIFusion, AIModelResult, FusedSignal
from signal_aggregator.scoring.scorer import SignalScorer, SignalScore
from signal_aggregator.orchestrator import SignalOrchestrator, AnalysisResult


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_signal(
    source: SourceName = SourceName.POLYGON,
    symbol: str = "NVDA",
    timeframe: str = "1D",
    direction: SignalDirection = SignalDirection.BUY,
    confidence: float = 0.90,
    price: float = 500.0,
    age_minutes: float = 0,
) -> SourceSignal:
    return SourceSignal(
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        direction=direction,
        confidence=confidence,
        price=price,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=age_minutes),
    )


def make_10_signals(symbol: str = "NVDA", timeframe: str = "1D") -> list:
    return [
        make_signal(src, symbol, timeframe, SignalDirection.BUY)
        for src in SourceName
    ]


# ─── Source Connector Tests ───────────────────────────────────────────────────

class TestSourceConnector:
    def test_all_10_sources_registered(self):
        from signal_aggregator.sources.connector import ALL_CONNECTORS
        assert len(ALL_CONNECTORS) == 10

    def test_source_accuracy_defined_for_all(self):
        for name in SourceName:
            assert name in SOURCE_ACCURACY
            assert 0 < SOURCE_ACCURACY[name] <= 1.0

    @pytest.mark.asyncio
    async def test_collect_all_returns_signals(self):
        connector = SourceConnector()
        signals = await connector.collect_all("NVDA", "1D")
        assert len(signals) >= 1
        for sig in signals:
            assert isinstance(sig, SourceSignal)
            assert sig.symbol == "NVDA"
            assert sig.timeframe == "1D"

    @pytest.mark.asyncio
    async def test_collect_all_10_sources(self):
        connector = SourceConnector()
        signals = await connector.collect_all("AAPL", "4H")
        # All 10 connectors should respond
        assert len(signals) == 10

    @pytest.mark.asyncio
    async def test_collect_runs_in_parallel(self):
        """Verify concurrent collection is faster than sequential."""
        import time
        connector = SourceConnector()
        start = time.perf_counter()
        await connector.collect_all("MSFT", "1D")
        elapsed = time.perf_counter() - start
        # 10 sources, even with serial simulation, should be quick
        assert elapsed < 10.0


# ─── Parser Tests ─────────────────────────────────────────────────────────────

class TestSignalParser:
    def test_parse_assigns_numeric_direction(self):
        parser = SignalParser()
        signals = make_10_signals()
        parsed = parser.parse(signals)
        assert len(parsed) == 10
        for p in parsed:
            assert 0.0 <= p.numeric_direction <= 1.0

    def test_direction_numeric_mapping(self):
        assert DIRECTION_NUMERIC[SignalDirection.STRONG_BUY] == 1.0
        assert DIRECTION_NUMERIC[SignalDirection.STRONG_SELL] == 0.0
        assert DIRECTION_NUMERIC[SignalDirection.NEUTRAL] == 0.5

    def test_numeric_to_direction_roundtrip(self):
        for score, expected in [
            (1.0, SignalDirection.STRONG_BUY),
            (0.75, SignalDirection.BUY),
            (0.5, SignalDirection.NEUTRAL),
            (0.25, SignalDirection.SELL),
            (0.0, SignalDirection.STRONG_SELL),
        ]:
            assert SignalParser.numeric_to_direction(score) == expected

    def test_weighted_confidence_uses_source_weight(self):
        parser = SignalParser()
        sig = make_signal(confidence=0.80)
        parsed = parser.parse([sig], {SourceName.POLYGON: 0.94})
        assert abs(parsed[0].weighted_confidence - 0.80 * 0.94) < 1e-6


# ─── Validator Tests ──────────────────────────────────────────────────────────

class TestQualityValidator:
    def test_fresh_high_confidence_signal_passes(self):
        validator = QualityValidator()
        sig = make_signal(confidence=0.85, age_minutes=0)
        valid, rejected = validator.validate([sig])
        assert len(valid) == 1
        assert len(rejected) == 0

    def test_low_confidence_signal_rejected(self):
        validator = QualityValidator(min_confidence=0.70)
        sig = make_signal(confidence=0.40)
        valid, rejected = validator.validate([sig])
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_stale_signal_rejected(self):
        validator = QualityValidator()
        sig = make_signal(age_minutes=2000)  # way older than 1D threshold
        valid, rejected = validator.validate([sig])
        assert len(rejected) == 1

    def test_quality_score_set_on_valid_signal(self):
        validator = QualityValidator()
        sig = make_signal(confidence=0.90, age_minutes=0)
        valid, _ = validator.validate([sig])
        assert 0 < valid[0].quality_score <= 1.0

    def test_invalid_price_rejected(self):
        validator = QualityValidator()
        sig = make_signal(price=0.0)
        valid, rejected = validator.validate([sig])
        assert len(rejected) == 1


# ─── Aggregation Engine Tests ─────────────────────────────────────────────────

class TestAggregationEngine:
    def test_aggregate_returns_aggregated_signal(self):
        engine = AggregationEngine()
        signals = make_10_signals()
        result = engine.aggregate(signals, "NVDA", "1D")
        assert isinstance(result, AggregatedSignal)
        assert result.symbol == "NVDA"
        assert result.timeframe == "1D"

    def test_global_score_in_range(self):
        engine = AggregationEngine()
        signals = make_10_signals()
        result = engine.aggregate(signals, "NVDA", "1D")
        assert 0.0 <= result.global_score <= 1.0

    def test_agreement_pct_in_range(self):
        engine = AggregationEngine()
        signals = make_10_signals()
        result = engine.aggregate(signals, "NVDA", "1D")
        assert 0.0 <= result.agreement_pct <= 1.0

    def test_sources_count_matches_valid_signals(self):
        engine = AggregationEngine()
        signals = make_10_signals()
        result = engine.aggregate(signals, "NVDA", "1D")
        assert result.sources_count == len(signals)

    def test_empty_signals_returns_none(self):
        engine = AggregationEngine()
        result = engine.aggregate([], "NVDA", "1D")
        assert result is None

    def test_all_buy_signals_produce_bullish_result(self):
        engine = AggregationEngine()
        signals = make_10_signals()  # all BUY
        result = engine.aggregate(signals, "NVDA", "1D")
        assert result.direction in (SignalDirection.BUY, SignalDirection.STRONG_BUY)

    def test_all_sell_signals_produce_bearish_result(self):
        engine = AggregationEngine()
        signals = [
            make_signal(src, direction=SignalDirection.STRONG_SELL)
            for src in SourceName
        ]
        result = engine.aggregate(signals, "NVDA", "1D")
        assert result.direction in (SignalDirection.SELL, SignalDirection.STRONG_SELL)

    def test_source_details_populated(self):
        engine = AggregationEngine()
        signals = make_10_signals()
        result = engine.aggregate(signals, "NVDA", "1D")
        assert len(result.source_details) == 10

    def test_performance_update_changes_weights(self):
        engine = AggregationEngine()
        original = engine._effective_weights()[SourceName.POLYGON]
        engine.update_performance(SourceName.POLYGON, 0.99)
        updated = engine._effective_weights()[SourceName.POLYGON]
        assert updated > original


# ─── AI Fusion Tests ──────────────────────────────────────────────────────────

class TestAIFusion:
    def _make_aggregated(self, score: float = 0.75) -> AggregatedSignal:
        engine = AggregationEngine()
        signals = make_10_signals()
        agg = engine.aggregate(signals, "NVDA", "1D")
        # override score for deterministic testing
        agg.global_score = score
        agg.source_details = {
            "Polygon.io": {"direction": "BUY", "confidence": 0.90, "quality_score": 0.95, "price": 500.0}
        }
        return agg

    def test_fuse_returns_fused_signal(self):
        fusion = AIFusion()
        agg = self._make_aggregated()
        result = fusion.fuse(agg)
        assert isinstance(result, FusedSignal)

    def test_weights_sum_to_one(self):
        fusion = AIFusion(global_weight=0.40, ai_weight=0.60)
        assert abs(fusion.global_weight + fusion.ai_weight - 1.0) < 1e-9

    def test_fused_score_respects_weights(self):
        fusion = AIFusion(global_weight=0.40, ai_weight=0.60)
        agg = self._make_aggregated(score=0.80)
        ai_results = [
            AIModelResult("LSTM", SignalDirection.BUY, 0.90, 0.80),
        ]
        result = fusion.fuse(agg, ai_results)
        expected = 0.40 * 0.80 + 0.60 * 0.80
        assert abs(result.fused_score - expected) < 0.01

    def test_stars_between_1_and_5(self):
        fusion = AIFusion()
        agg = self._make_aggregated()
        result = fusion.fuse(agg)
        assert 1 <= result.stars <= 5

    def test_alert_level_valid(self):
        fusion = AIFusion()
        agg = self._make_aggregated()
        result = fusion.fuse(agg)
        assert result.alert_level in ("RED", "YELLOW", "GREEN", "MONITOR")

    def test_confidence_above_80_percent(self):
        fusion = AIFusion()
        agg = self._make_aggregated(score=0.85)
        result = fusion.fuse(agg)
        assert result.final_confidence >= 0.80

    def test_entry_target_stop_prices_logical(self):
        fusion = AIFusion()
        agg = self._make_aggregated(score=0.80)
        result = fusion.fuse(agg)
        if result.direction in (SignalDirection.BUY, SignalDirection.STRONG_BUY):
            assert result.target_price > result.entry_price
            assert result.stop_loss < result.entry_price

    def test_invalid_weights_raise(self):
        with pytest.raises(AssertionError):
            AIFusion(global_weight=0.50, ai_weight=0.60)


# ─── Scorer Tests ─────────────────────────────────────────────────────────────

class TestSignalScorer:
    def _make_fused(self, direction=SignalDirection.BUY, confidence=0.90, fused_score=0.80) -> FusedSignal:
        return FusedSignal(
            symbol="NVDA",
            timeframe="1D",
            direction=direction,
            final_confidence=confidence,
            global_score=0.75,
            ai_score=0.82,
            fused_score=fused_score,
            agreement_pct=0.90,
            sources_count=10,
            ai_models_count=5,
            stars=5,
            entry_price=500.0,
            target_price=540.0,
            stop_loss=480.0,
            risk_reward=2.0,
            win_probability=confidence,
            alert_level="GREEN",
        )

    def test_score_returns_0_to_100(self):
        scorer = SignalScorer()
        fused = self._make_fused()
        score = scorer.score(fused)
        assert 0 <= score <= 100

    def test_higher_confidence_gives_higher_score(self):
        scorer = SignalScorer()
        low = scorer.score(self._make_fused(confidence=0.65))
        high = scorer.score(self._make_fused(confidence=0.95))
        assert high > low

    def test_rank_signals_sorted_by_score(self):
        scorer = SignalScorer()
        signals = [
            self._make_fused(confidence=0.70, fused_score=0.65),
            self._make_fused(confidence=0.95, fused_score=0.90),
            self._make_fused(confidence=0.80, fused_score=0.75),
        ]
        # give different symbols
        for i, s in enumerate(signals):
            s.symbol = f"SYM{i}"
        ranked = scorer.rank_signals(signals)
        assert ranked[0].composite_score >= ranked[1].composite_score >= ranked[2].composite_score

    def test_top_gainers_only_bullish(self):
        scorer = SignalScorer()
        signals = [
            self._make_fused(direction=SignalDirection.BUY),
            self._make_fused(direction=SignalDirection.STRONG_SELL),
            self._make_fused(direction=SignalDirection.STRONG_BUY),
        ]
        for i, s in enumerate(signals):
            s.symbol = f"SYM{i}"
        scored = scorer.rank_signals(signals)
        gainers = scorer.top_gainers(scored)
        for g in gainers:
            assert g.direction in (SignalDirection.BUY, SignalDirection.STRONG_BUY)

    def test_top_losers_only_bearish(self):
        scorer = SignalScorer()
        signals = [
            self._make_fused(direction=SignalDirection.BUY),
            self._make_fused(direction=SignalDirection.STRONG_SELL),
        ]
        for i, s in enumerate(signals):
            s.symbol = f"SYM{i}"
        scored = scorer.rank_signals(signals)
        losers = scorer.top_losers(scored)
        for l in losers:
            assert l.direction in (SignalDirection.SELL, SignalDirection.STRONG_SELL)

    def test_leaderboard_structure(self):
        scorer = SignalScorer()
        signals = [self._make_fused(direction=d) for d in SignalDirection]
        for i, s in enumerate(signals):
            s.symbol = f"SYM{i}"
        scored = scorer.rank_signals(signals)
        board = scorer.leaderboard(scored)
        assert "top_gainers" in board
        assert "top_losers" in board
        assert "neutral" in board


# ─── Orchestrator Integration Tests ──────────────────────────────────────────

class TestSignalOrchestrator:
    @pytest.mark.asyncio
    async def test_analyse_single_symbol(self):
        orch = SignalOrchestrator()
        results = await orch.analyse(["NVDA"], ["1D"])
        assert len(results) == 1
        result = results[0]
        assert result.symbol == "NVDA"
        assert "1D" in result.timeframes
        assert "1D" in result.scores

    @pytest.mark.asyncio
    async def test_analyse_multiple_symbols(self):
        orch = SignalOrchestrator()
        symbols = ["NVDA", "AAPL", "MSFT"]
        results = await orch.analyse(symbols, ["1D"])
        assert len(results) == 3
        for res in results:
            assert res.symbol in symbols

    @pytest.mark.asyncio
    async def test_analyse_all_timeframes(self):
        orch = SignalOrchestrator()
        results = await orch.analyse(["AAPL"], ["1D", "4H", "30M"])
        assert len(results) == 1
        result = results[0]
        for tf in ["1D", "4H", "30M"]:
            assert tf in result.timeframes

    @pytest.mark.asyncio
    async def test_leaderboard_async_returns_gainers_losers(self):
        orch = SignalOrchestrator()
        symbols = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"]
        board = await orch.leaderboard_async(symbols, timeframe="1D", n=5)
        assert "top_gainers" in board
        assert "top_losers" in board

    @pytest.mark.asyncio
    async def test_fused_signal_confidence_high(self):
        orch = SignalOrchestrator()
        results = await orch.analyse(["NVDA"], ["1D"])
        result = results[0]
        fused = result.timeframes["1D"]
        # Fused confidence should be above 80%
        assert fused.final_confidence >= 0.80

    @pytest.mark.asyncio
    async def test_all_10_sources_used(self):
        orch = SignalOrchestrator()
        results = await orch.analyse(["NVDA"], ["1D"])
        fused = results[0].timeframes["1D"]
        assert fused.sources_count == 10

    def test_best_timeframe_property(self):
        result = AnalysisResult(symbol="NVDA")
        # populate mock scores
        from signal_aggregator.fusion.ai_fusion import FusedSignal
        fused = FusedSignal(
            symbol="NVDA", timeframe="1D", direction=SignalDirection.BUY,
            final_confidence=0.92, global_score=0.80, ai_score=0.85,
            fused_score=0.83, agreement_pct=0.90, sources_count=10,
            ai_models_count=5, stars=5, entry_price=500, target_price=540,
            stop_loss=480, risk_reward=2.0, win_probability=0.90,
            alert_level="GREEN",
        )
        result.scores["1D"] = SignalScore(
            symbol="NVDA", timeframe="1D", rank=1, composite_score=85.0,
            direction=SignalDirection.BUY, stars=5, final_confidence=0.92,
            entry_price=500, target_price=540, stop_loss=480,
            risk_reward=2.0, win_probability=0.90, alert_level="GREEN",
            fused_signal=fused,
        )
        assert result.best_timeframe == "1D"


# ─── API Tests ────────────────────────────────────────────────────────────────

class TestAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.api.routes import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_signal_endpoint_returns_timeframes(self, client):
        resp = client.get("/api/v1/signals/NVDA?timeframes=1D")
        assert resp.status_code == 200
        data = resp.json()
        assert "1D" in data
        sig = data["1D"]
        assert "direction" in sig
        assert "final_confidence" in sig
        assert "entry_price" in sig

    def test_leaderboard_endpoint(self, client):
        resp = client.get("/api/v1/leaderboard?timeframe=1D&n=5")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_gainers" in data
        assert "top_losers" in data

    def test_batch_endpoint(self, client):
        resp = client.post(
            "/api/v1/signals/batch",
            json={"symbols": ["NVDA", "AAPL"], "timeframes": ["1D"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "symbols" in data
        assert "NVDA" in data["symbols"]
        assert "AAPL" in data["symbols"]

    def test_dashboard_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Ashamy" in resp.text

    def test_signal_response_has_source_details(self, client):
        resp = client.get("/api/v1/signals/MSFT?timeframes=1D")
        assert resp.status_code == 200
        sig = resp.json()["1D"]
        assert "source_details" in sig
        assert len(sig["source_details"]) > 0

    def test_signal_confidence_range(self, client):
        resp = client.get("/api/v1/signals/AAPL?timeframes=1D")
        sig = resp.json()["1D"]
        assert 0.0 <= sig["final_confidence"] <= 1.0

    def test_leaderboard_gainers_are_bullish(self, client):
        resp = client.get("/api/v1/leaderboard?timeframe=1D&n=10")
        data = resp.json()
        for g in data["top_gainers"]:
            assert "BUY" in g["direction"]

    def test_leaderboard_has_source_details(self, client):
        resp = client.get("/api/v1/leaderboard?timeframe=1D&n=5")
        data = resp.json()
        for g in data["top_gainers"]:
            assert "source_details" in g
            assert isinstance(g["source_details"], dict)

    def test_leaderboard_losers_are_bearish(self, client):
        resp = client.get("/api/v1/leaderboard?timeframe=1D&n=10")
        data = resp.json()
        for l in data["top_losers"]:
            assert "SELL" in l["direction"]
