"""
FastAPI application – REST + WebSocket endpoints for the signal aggregator.

Endpoints:
  GET  /api/v1/signals/{symbol}                – single symbol, all timeframes
  GET  /api/v1/leaderboard                     – top gainers / losers
  POST /api/v1/signals/batch                   – batch analysis
  WS   /ws/signals                             – real-time signal stream
  GET  /                                       – dashboard HTML
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from signal_aggregator.orchestrator import SignalOrchestrator, SUPPORTED_TIMEFRAMES
from signal_aggregator.sources.connector import SignalDirection

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ashamy Signal Aggregator API",
    description="نظام ذكي يربط أفضل 10 مصادر إشارات عالمية مع نماذج AI",
    version="1.0.0",
)

# ── global orchestrator instance ─────────────────────────────────────────────

_API_KEYS: Dict[str, str] = {
    "Polygon.io": os.getenv("POLYGON_API_KEY", ""),
    "AlphaVantage": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
}

_orchestrator = SignalOrchestrator(api_keys=_API_KEYS)

# Popular US stocks for leaderboard
DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN",
    "GOOGL", "META", "NFLX", "AMD", "INTC",
    "JPM", "BAC", "GS", "WFC", "V",
    "JNJ", "PFE", "MRNA", "UNH", "CVX",
]


# ── Pydantic models ───────────────────────────────────────────────────────────

class BatchRequest(BaseModel):
    symbols: List[str]
    timeframes: Optional[List[str]] = None


class SignalResponse(BaseModel):
    symbol: str
    timeframe: str
    direction: str
    final_confidence: float
    fused_score: float
    global_score: float
    ai_score: float
    agreement_pct: float
    stars: int
    entry_price: float
    target_price: float
    stop_loss: float
    risk_reward: float
    win_probability: float
    alert_level: str
    sources_count: int
    ai_models_count: int
    composite_score: float
    source_details: Dict[str, Any]
    ai_details: Dict[str, Any]
    timestamp: str


def _to_response(score, fused) -> SignalResponse:
    return SignalResponse(
        symbol=fused.symbol,
        timeframe=fused.timeframe,
        direction=fused.direction.value,
        final_confidence=fused.final_confidence,
        fused_score=fused.fused_score,
        global_score=fused.global_score,
        ai_score=fused.ai_score,
        agreement_pct=fused.agreement_pct,
        stars=fused.stars,
        entry_price=fused.entry_price,
        target_price=fused.target_price,
        stop_loss=fused.stop_loss,
        risk_reward=fused.risk_reward,
        win_probability=fused.win_probability,
        alert_level=fused.alert_level,
        sources_count=fused.sources_count,
        ai_models_count=fused.ai_models_count,
        composite_score=score.composite_score,
        source_details=fused.source_details,
        ai_details=fused.ai_details,
        timestamp=fused.timestamp.isoformat(),
    )


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/api/v1/signals/{symbol}", response_model=Dict[str, SignalResponse])
async def get_signal(
    symbol: str,
    timeframes: Optional[str] = Query(
        default=None,
        description="Comma-separated: 1D,4H,30M",
    ),
):
    """Analyse a single symbol across requested timeframes."""
    tfs = [t.strip() for t in timeframes.split(",")] if timeframes else SUPPORTED_TIMEFRAMES
    results = await _orchestrator.analyse([symbol.upper()], tfs)
    if not results:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")
    res = results[0]
    if not res.scores:
        raise HTTPException(status_code=404, detail=f"No signals for {symbol}")
    return {
        tf: _to_response(res.scores[tf], res.timeframes[tf])
        for tf in res.scores
    }


@app.get("/api/v1/leaderboard")
async def get_leaderboard(
    timeframe: str = Query(default="1D", description="1D | 4H | 30M"),
    n: int = Query(default=10, ge=1, le=50),
    symbols: Optional[str] = Query(default=None, description="Comma-separated symbols"),
):
    """Return top gainers and losers leaderboard."""
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else DEFAULT_SYMBOLS
    board = await _orchestrator.leaderboard_async(sym_list, timeframe=timeframe, n=n)

    def _format(score_list):
        out = []
        for s in score_list:
            out.append({
                "rank": s.rank,
                "symbol": s.symbol,
                "direction": s.direction.value,
                "composite_score": s.composite_score,
                "final_confidence": s.final_confidence,
                "stars": s.stars,
                "entry_price": s.entry_price,
                "target_price": s.target_price,
                "stop_loss": s.stop_loss,
                "risk_reward": s.risk_reward,
                "win_probability": s.win_probability,
                "alert_level": s.alert_level,
                "agreement_pct": s.fused_signal.agreement_pct,
                "source_details": s.fused_signal.source_details,
                "ai_details": s.fused_signal.ai_details,
            })
        return out

    return {
        "timeframe": timeframe,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_gainers": _format(board.get("top_gainers", [])),
        "top_losers": _format(board.get("top_losers", [])),
    }


@app.post("/api/v1/signals/batch")
async def batch_analysis(request: BatchRequest):
    """Batch analysis for multiple symbols."""
    tfs = request.timeframes or SUPPORTED_TIMEFRAMES
    results = await _orchestrator.analyse(
        [s.upper() for s in request.symbols], tfs
    )
    output = {}
    for res in results:
        output[res.symbol] = {
            tf: _to_response(res.scores[tf], res.timeframes[tf]).model_dump()
            for tf in res.scores
        }
    return {"symbols": output, "generated_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── WebSocket ─────────────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: str):
        for ws in list(self.active):
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001
                self.active.remove(ws)


manager = ConnectionManager()


@app.websocket("/ws/signals")
async def ws_signals(websocket: WebSocket):
    """
    Real-time signal stream.

    Send JSON: {"symbols": ["NVDA","AAPL"], "timeframe": "30M"}
    Receive: stream of SignalResponse objects.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            symbols = payload.get("symbols", DEFAULT_SYMBOLS[:5])
            timeframe = payload.get("timeframe", "30M")

            results = await _orchestrator.analyse(
                [s.upper() for s in symbols], [timeframe]
            )
            out = []
            for res in results:
                if timeframe in res.scores:
                    out.append(
                        _to_response(res.scores[timeframe], res.timeframes[timeframe]).model_dump()
                    )
            await websocket.send_text(json.dumps({
                "type": "signal_update",
                "timeframe": timeframe,
                "signals": out,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Dashboard ─────────────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>🚀 Ashamy – نظام الإشارات العالمية</title>
  <style>
    :root {
      --bg: #0d1117; --card: #161b22; --border: #30363d;
      --green: #3fb950; --red: #f85149; --yellow: #d29922;
      --blue: #58a6ff; --text: #c9d1d9; --muted: #8b949e;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; }
    header { background: var(--card); border-bottom: 1px solid var(--border);
             padding: 1rem 2rem; display: flex; align-items: center; gap: 1rem; }
    header h1 { font-size: 1.4rem; color: var(--blue); }
    .badge { background: var(--green); color: #000; padding: 2px 8px;
             border-radius: 12px; font-size: .75rem; font-weight: 700; }
    nav { display: flex; gap: 1rem; padding: .5rem 2rem; background: var(--card);
          border-bottom: 1px solid var(--border); }
    nav button { background: none; border: 1px solid var(--border); color: var(--text);
                 padding: .4rem 1rem; border-radius: 6px; cursor: pointer; font-size: .9rem; }
    nav button.active { background: var(--blue); color: #000; border-color: var(--blue); }
    main { padding: 1.5rem 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px;
            padding: 1rem; transition: transform .15s; }
    .card:hover { transform: translateY(-2px); border-color: var(--blue); }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem; }
    .symbol { font-size: 1.2rem; font-weight: 700; color: var(--blue); }
    .direction { font-size: .85rem; font-weight: 700; padding: 2px 8px;
                 border-radius: 4px; }
    .direction.buy { background: rgba(63,185,80,.15); color: var(--green); }
    .direction.sell { background: rgba(248,81,73,.15); color: var(--red); }
    .direction.neutral { background: rgba(88,166,255,.10); color: var(--muted); }
    .stars { color: var(--yellow); font-size: 1.1rem; }
    .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; font-size: .85rem; }
    .metric-label { color: var(--muted); }
    .metric-value { font-weight: 600; }
    .metric-value.green { color: var(--green); }
    .metric-value.red { color: var(--red); }
    .sources-bar { margin-top: .75rem; }
    .sources-title { font-size: .78rem; color: var(--muted); margin-bottom: .4rem; }
    .source-pill { display: inline-block; background: rgba(88,166,255,.08);
                   border: 1px solid rgba(88,166,255,.2); border-radius: 4px;
                   padding: 1px 6px; font-size: .72rem; margin: 2px; }
    .source-pill.agree { background: rgba(63,185,80,.1); border-color: rgba(63,185,80,.3); }
    .alert-dot { display: inline-block; width: 10px; height: 10px;
                 border-radius: 50%; margin-left: 4px; }
    .alert-RED { background: var(--red); }
    .alert-YELLOW { background: var(--yellow); }
    .alert-GREEN { background: var(--green); }
    .alert-MONITOR { background: var(--muted); }
    .loading { text-align: center; padding: 4rem; color: var(--muted); font-size: 1.2rem; }
    .error { color: var(--red); text-align: center; padding: 2rem; }
    .stats-bar { display: flex; gap: 2rem; padding: .75rem 2rem; background: var(--card);
                 border-bottom: 1px solid var(--border); font-size: .9rem; }
    .stat { display: flex; flex-direction: column; align-items: center; }
    .stat span:first-child { color: var(--muted); font-size: .75rem; }
    .stat span:last-child { font-weight: 700; font-size: 1.1rem; }
    #ws-status { font-size: .8rem; }
    .ws-on { color: var(--green); }
    .ws-off { color: var(--red); }
  </style>
</head>
<body>
<header>
  <h1>🚀 Ashamy – نظام الإشارات العالمية</h1>
  <span class="badge">10 مصادر عالمية</span>
  <span class="badge" style="background:var(--blue)">AI Fusion 92-96%</span>
  <span id="ws-status" class="ws-off" style="margin-right:auto">● غير متصل</span>
</header>
<div class="stats-bar">
  <div class="stat"><span>المصادر</span><span style="color:var(--blue)">10</span></div>
  <div class="stat"><span>وزن AI</span><span style="color:var(--green)">60%</span></div>
  <div class="stat"><span>وزن عالمي</span><span style="color:var(--yellow)">40%</span></div>
  <div class="stat"><span>دقة الإشارات</span><span style="color:var(--green)">92-96%</span></div>
  <div class="stat" id="stat-bull"><span>صاعدة</span><span>–</span></div>
  <div class="stat" id="stat-bear"><span>هابطة</span><span>–</span></div>
  <div class="stat" id="stat-upd"><span>آخر تحديث</span><span>–</span></div>
</div>
<nav>
  <button class="active" onclick="setTf('1D',this)">يومي (1D)</button>
  <button onclick="setTf('4H',this)">4 ساعات (4H)</button>
  <button onclick="setTf('30M',this)">30 دقيقة (30M)</button>
  <button onclick="setTf('ALL',this)">جميع الفريمات</button>
</nav>
<main>
  <div id="content" class="loading">⏳ جاري تحميل الإشارات...</div>
</main>
<script>
const SYMBOLS = ["AAPL","MSFT","NVDA","TSLA","AMZN","GOOGL","META","NFLX","AMD","INTC",
                 "JPM","BAC","GS","WFC","V","JNJ","PFE","MRNA","UNH","CVX"];
let currentTf = "1D";
let ws = null;

function setTf(tf, btn) {
  currentTf = tf;
  document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  loadData();
}

async function loadData() {
  const el = document.getElementById("content");
  el.innerHTML = '<div class="loading">⏳ جاري جمع الإشارات من 10 مصادر عالمية...</div>';
  try {
    const tf = currentTf === "ALL" ? "1D" : currentTf;
    const resp = await fetch(`/api/v1/leaderboard?timeframe=${tf}&n=20`);
    if (!resp.ok) throw new Error(resp.statusText);
    const data = await resp.json();
    renderBoard(data);
  } catch(e) {
    el.innerHTML = `<div class="error">❌ خطأ: ${e.message}</div>`;
  }
}

function dirClass(d) {
  if (d.includes("BUY")) return "buy";
  if (d.includes("SELL")) return "sell";
  return "neutral";
}

function stars(n) { return "⭐".repeat(n); }

function card(s) {
  const cls = dirClass(s.direction);
  const dirAr = {
    STRONG_BUY:"شراء قوي", BUY:"شراء", NEUTRAL:"محايد", SELL:"بيع", STRONG_SELL:"بيع قوي"
  }[s.direction] || s.direction;

  const pills = Object.keys(s.source_details || {}).map(src => {
    const d = (s.source_details[src]||{}).direction||"";
    const agrees = dirClass(d) === cls;
    return `<span class="source-pill ${agrees?'agree':''}">${src}</span>`;
  }).join("");

  return `
  <div class="card">
    <div class="card-header">
      <span class="symbol">${s.symbol}
        <span class="alert-dot alert-${s.alert_level}" title="${s.alert_level}"></span>
      </span>
      <span class="direction ${cls}">${dirAr}</span>
    </div>
    <div class="stars">${stars(s.stars)}</div>
    <div class="metrics" style="margin-top:.5rem">
      <span class="metric-label">الثقة</span>
      <span class="metric-value green">${(s.final_confidence*100).toFixed(1)}%</span>
      <span class="metric-label">الدرجة</span>
      <span class="metric-value">${s.composite_score.toFixed(1)}/100</span>
      <span class="metric-label">الدخول</span>
      <span class="metric-value">$${s.entry_price.toFixed(2)}</span>
      <span class="metric-label">الهدف</span>
      <span class="metric-value green">$${s.target_price.toFixed(2)}</span>
      <span class="metric-label">وقف الخسارة</span>
      <span class="metric-value red">$${s.stop_loss.toFixed(2)}</span>
      <span class="metric-label">R/R</span>
      <span class="metric-value">${s.risk_reward.toFixed(1)}x</span>
      <span class="metric-label">احتمالية الربح</span>
      <span class="metric-value green">${(s.win_probability*100).toFixed(1)}%</span>
      <span class="metric-label">الإجماع</span>
      <span class="metric-value">${(s.agreement_pct*100).toFixed(0)}%</span>
    </div>
    ${pills ? `<div class="sources-bar"><div class="sources-title">المصادر</div>${pills}</div>` : ""}
  </div>`;
}

function renderBoard(data) {
  const el = document.getElementById("content");
  const gainers = data.top_gainers || [];
  const losers = data.top_losers || [];

  document.querySelector("#stat-bull span:last-child").textContent = gainers.length;
  document.querySelector("#stat-bear span:last-child").textContent = losers.length;
  document.querySelector("#stat-upd span:last-child").textContent =
    new Date().toLocaleTimeString("ar");

  let html = "";
  if (gainers.length) {
    html += `<h2 style="color:var(--green);margin:.5rem 0 .75rem">📈 أفضل الأسهم الصاعدة</h2>
             <div class="grid">${gainers.map(card).join("")}</div>`;
  }
  if (losers.length) {
    html += `<h2 style="color:var(--red);margin:1.5rem 0 .75rem">📉 أفضل الأسهم الهابطة</h2>
             <div class="grid">${losers.map(card).join("")}</div>`;
  }
  if (!html) html = '<div class="loading">لا توجد إشارات في هذا الوقت</div>';
  el.innerHTML = html;
}

function connectWS() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/signals`);
  const status = document.getElementById("ws-status");

  ws.onopen = () => {
    status.textContent = "● متصل (بث مباشر)";
    status.className = "ws-on";
    ws.send(JSON.stringify({symbols: SYMBOLS.slice(0,8), timeframe: "30M"}));
  };
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (currentTf === "30M" && msg.signals) {
      // lightweight update: refresh stats
      const sigs = msg.signals;
      const bull = sigs.filter(s => s.direction.includes("BUY")).length;
      const bear = sigs.filter(s => s.direction.includes("SELL")).length;
      document.querySelector("#stat-bull span:last-child").textContent = bull;
      document.querySelector("#stat-bear span:last-child").textContent = bear;
      document.querySelector("#stat-upd span:last-child").textContent =
        new Date().toLocaleTimeString("ar");
    }
  };
  ws.onclose = () => {
    status.textContent = "● غير متصل";
    status.className = "ws-off";
    setTimeout(connectWS, 5000);
  };
}

loadData();
connectWS();
setInterval(loadData, 60000);  // refresh every minute
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)
