import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketState


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_signal(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    base_prices = {
        "NVDA": 131.45,
        "AAPL": 214.10,
        "MSFT": 468.22,
        "TSLA": 247.63,
        "AMZN": 198.41,
    }
    price = base_prices.get(symbol, 120.0 + (sum(ord(char) for char in symbol) % 80))
    drift = ((sum(ord(char) for char in symbol) % 9) - 4) / 100
    direction = "BUY" if drift >= 0 else "SELL"
    confidence = min(max(0.74 + abs(drift), 0.51), 0.96)
    entry_price = round(price, 2)
    target_price = round(price * (1.04 if direction == "BUY" else 0.96), 2)
    stop_loss = round(price * (0.97 if direction == "BUY" else 1.03), 2)

    return {
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "final_confidence": round(confidence, 2),
        "stars": max(1, min(5, round(confidence * 5))),
        "updated_at": utc_now(),
    }


def leaderboard_rows() -> list[dict[str, Any]]:
    return [
        {"symbol": "NVDA", "price": 131.45, "change": 4.2},
        {"symbol": "MSFT", "price": 468.22, "change": 2.7},
        {"symbol": "AAPL", "price": 214.10, "change": 1.9},
        {"symbol": "AMZN", "price": 198.41, "change": 1.3},
        {"symbol": "TSLA", "price": 247.63, "change": -0.8},
    ]


class RunTestsRequest(BaseModel):
    test_type: str = Field(default="all")


class OptimizeRequest(BaseModel):
    optimization_level: str = Field(default="balanced")
    target: str = Field(default="all")


class UpdateModelsRequest(BaseModel):
    models: list[str] = Field(default_factory=lambda: ["all"])
    auto_optimize: bool = True


app = FastAPI(
    title="Ashamy Mock Backend",
    version="0.1.0",
    description="Development-only FastAPI stubs for the Ashamy mobile screens.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "Ashamy",
        "mode": "mock",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "ashamy-backend", "mode": "mock", "timestamp": utc_now()}


@app.get("/api/v1/leaderboard")
def leaderboard() -> dict[str, Any]:
    rows = leaderboard_rows()
    return {
        "top_gainers": rows,
        "top_losers": sorted(rows, key=lambda row: row["change"])[:3],
        "generated_at": utc_now(),
    }


@app.get("/api/v1/signals/{symbol}")
def signal(symbol: str, timeframes: str | None = Query(default=None)) -> dict[str, Any]:
    payload = build_signal(symbol)
    payload["timeframes"] = [item for item in (timeframes or "").split(",") if item] or ["1D"]
    payload["analysis"] = "Mock analysis generated for development mode."
    return payload


@app.post("/api/v1/ai/run-tests")
def run_tests(request: RunTestsRequest) -> dict[str, Any]:
    return {
        "success": True,
        "test_type": request.test_type,
        "total_tests": 12,
        "passed_tests": 12,
        "failed_tests": 0,
        "code_coverage": 84,
        "execution_time": 0.42,
        "generated_at": utc_now(),
    }


@app.post("/api/v1/ai/optimize")
def optimize(request: OptimizeRequest) -> dict[str, Any]:
    return {
        "success": True,
        "target": request.target,
        "optimization_level": request.optimization_level,
        "improvement": 14.6,
        "new_execution_time": 87,
        "generated_at": utc_now(),
    }


@app.post("/api/v1/ai/update-models")
def update_models(request: UpdateModelsRequest) -> dict[str, Any]:
    return {
        "success": True,
        "requested_models": request.models,
        "auto_optimize": request.auto_optimize,
        "models": {
            "lstm": {"accuracy": 92.4, "status": "updated"},
            "gru": {"accuracy": 91.8, "status": "updated"},
            "transformer": {"accuracy": 93.1, "status": "updated"},
        },
        "generated_at": utc_now(),
    }


@app.post("/api/v1/ai/cleanup")
def cleanup() -> dict[str, Any]:
    return {"success": True, "memory_freed": 128, "generated_at": utc_now()}


@app.post("/api/v1/ai/security-scan")
def security_scan() -> dict[str, Any]:
    return {
        "success": True,
        "vulnerabilities": 0,
        "issues": [],
        "generated_at": utc_now(),
    }


@app.websocket("/ws/signals")
async def signal_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    symbols = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"]

    try:
        while websocket.client_state == WebSocketState.CONNECTED:
            symbol = random.choice(symbols)
            payload = build_signal(symbol)
            payload["type"] = "signal_update"
            await websocket.send_json(payload)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
