"""
Pydantic request/response models for the API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ---- Requests ----

class AnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol, e.g. AAPL")
    period: str = Field("2y", description="Data period (yfinance format)")
    interval: str = Field("1d", description="Data interval (yfinance format)")
    start: Optional[str] = Field(None, description="Start date YYYY-MM-DD")
    end: Optional[str] = Field(None, description="End date YYYY-MM-DD")
    run_ml: bool = Field(False, description="Run deep-learning ensemble prediction")


class BacktestRequest(BaseModel):
    symbol: str
    period: str = "2y"
    interval: str = "1d"
    initial_capital: float = Field(100_000.0, gt=0)
    commission: float = Field(0.001, ge=0, le=0.05)
    slippage: float = Field(0.0005, ge=0, le=0.01)


# ---- Responses ----

class CandlestickBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    signal: int = 0
    recommendation: str = "HOLD"
    confidence: float = 0.0


class IndicatorValues(BaseModel):
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    atr: Optional[float] = None
    vwap: Optional[float] = None


class SignalPoint(BaseModel):
    date: str
    price: float
    signal: int
    recommendation: str
    confidence: float
    indicators: IndicatorValues


class AnalysisResponse(BaseModel):
    symbol: str
    period: str
    interval: str
    total_bars: int
    candles: List[CandlestickBar]
    signals: List[SignalPoint]
    latest_recommendation: str
    latest_confidence: float
    latest_indicators: IndicatorValues
    strategy_agreement: Dict[str, int]


class BacktestMetricsModel(BaseModel):
    total_return: float
    cagr: float
    initial_capital: float
    final_equity: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    total_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    expectancy: float


class BacktestResponse(BaseModel):
    symbol: str
    period: str
    metrics: BacktestMetricsModel
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    report_text: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
