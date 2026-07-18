"""
FastAPI route definitions.
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import numpy as np
import pandas as pd
from loguru import logger

from .models import (
    AnalysisRequest,
    AnalysisResponse,
    BacktestRequest,
    BacktestResponse,
    BacktestMetricsModel,
    CandlestickBar,
    SignalPoint,
    IndicatorValues,
    HealthResponse,
)
from data import DataFetcher, DataProcessor, DataValidator
from signals import SignalGenerator, SignalValidator, SignalCombiner
from backtesting import BacktestEngine, BacktestMetrics, BacktestReporter
from config import settings

router = APIRouter()
fetcher = DataFetcher()
processor = DataProcessor()
validator = DataValidator()
signal_gen = SignalGenerator()
signal_val = SignalValidator()
signal_comb = SignalCombiner()
bt_engine = BacktestEngine(
    initial_capital=settings.INITIAL_CAPITAL,
    commission=settings.COMMISSION,
    slippage=settings.SLIPPAGE,
)
bt_metrics_calc = BacktestMetrics()
bt_reporter = BacktestReporter()


def _safe_float(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return round(float(val), 6)


def _build_indicators(row: pd.Series) -> IndicatorValues:
    return IndicatorValues(
        sma_20=_safe_float(row.get("SMA_20")),
        sma_50=_safe_float(row.get("SMA_50")),
        ema_20=_safe_float(row.get("EMA_20")),
        ema_50=_safe_float(row.get("EMA_50")),
        rsi=_safe_float(row.get("RSI")),
        macd=_safe_float(row.get("MACD")),
        macd_signal=_safe_float(row.get("MACD_Signal")),
        macd_hist=_safe_float(row.get("MACD_Hist")),
        bb_upper=_safe_float(row.get("BB_Upper")),
        bb_middle=_safe_float(row.get("BB_Middle")),
        bb_lower=_safe_float(row.get("BB_Lower")),
        stoch_k=_safe_float(row.get("Stoch_K")),
        stoch_d=_safe_float(row.get("Stoch_D")),
        atr=_safe_float(row.get("ATR")),
        vwap=_safe_float(row.get("VWAP")),
    )


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze(req: AnalysisRequest):
    """
    Full analysis pipeline:
      1. Fetch data
      2. Validate & clean
      3. Run all strategies
      4. Validate & combine signals
      5. Return enriched DataFrame
    """
    try:
        raw = fetcher.fetch(
            req.symbol,
            period=req.period,
            interval=req.interval,
            start=req.start,
            end=req.end,
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Data fetch failed: {exc}")

    validation = validator.validate(raw, req.symbol)
    if not validation["is_valid"]:
        logger.warning(f"Data quality issues: {validation['issues']}")

    df = processor.clean(raw)
    df = processor.remove_anomalies(df)
    df = processor.add_returns(df)

    df = signal_gen.generate(df)
    sig_cols = signal_gen.get_signal_columns()
    df = signal_val.validate(df, sig_cols)
    df = signal_comb.combine(df)

    # Latest bar info
    last = df.iloc[-1]
    latest_rec = str(last.get("Recommendation", "HOLD"))
    latest_conf = _safe_float(last.get("Confidence", 0.0)) or 0.0

    # Strategy agreement on the latest bar
    agreement = {}
    for col in sig_cols:
        if col in df.columns:
            name = col.replace("_Signal", "")
            agreement[name] = int(df[col].iloc[-1])

    # Build candles list (last 500 bars max)
    tail = df.tail(500)
    candles = []
    for idx, row in tail.iterrows():
        candles.append(
            CandlestickBar(
                date=str(idx.date() if hasattr(idx, "date") else idx),
                open=round(float(row["Open"]), 4),
                high=round(float(row["High"]), 4),
                low=round(float(row["Low"]), 4),
                close=round(float(row["Close"]), 4),
                volume=round(float(row["Volume"]), 0),
                signal=int(row.get("Final_Signal", 0)),
                recommendation=str(row.get("Recommendation", "HOLD")),
                confidence=_safe_float(row.get("Confidence", 0.0)) or 0.0,
            )
        )

    # Signal events only
    signals_df = tail[tail["Final_Signal"] != 0]
    signals_out = []
    for idx, row in signals_df.iterrows():
        signals_out.append(
            SignalPoint(
                date=str(idx.date() if hasattr(idx, "date") else idx),
                price=round(float(row["Close"]), 4),
                signal=int(row["Final_Signal"]),
                recommendation=str(row.get("Recommendation", "HOLD")),
                confidence=_safe_float(row.get("Confidence", 0.0)) or 0.0,
                indicators=_build_indicators(row),
            )
        )

    return AnalysisResponse(
        symbol=req.symbol.upper(),
        period=req.period,
        interval=req.interval,
        total_bars=len(df),
        candles=candles,
        signals=signals_out,
        latest_recommendation=latest_rec,
        latest_confidence=latest_conf,
        latest_indicators=_build_indicators(last),
        strategy_agreement=agreement,
    )


@router.post("/backtest", response_model=BacktestResponse, tags=["Backtesting"])
async def backtest(req: BacktestRequest):
    """Run a full backtest and return performance metrics."""
    try:
        raw = fetcher.fetch(req.symbol, period=req.period)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Data fetch failed: {exc}")

    df = processor.clean(raw)
    df = processor.add_returns(df)
    df = signal_gen.generate(df)
    sig_cols = signal_gen.get_signal_columns()
    df = signal_val.validate(df, sig_cols)
    df = signal_comb.combine(df)

    engine = BacktestEngine(
        initial_capital=req.initial_capital,
        commission=req.commission,
        slippage=req.slippage,
    )
    result_df = engine.run(df)

    metrics = bt_metrics_calc.compute(
        equity_curve=result_df["Equity"],
        trade_returns=engine.trade_returns,
        initial_capital=req.initial_capital,
    )
    report_text = bt_reporter.generate(metrics, symbol=req.symbol, period=req.period)

    equity_curve = [
        {"date": str(idx.date()), "equity": round(float(val), 2)}
        for idx, val in result_df["Equity"].items()
    ]

    return BacktestResponse(
        symbol=req.symbol.upper(),
        period=req.period,
        metrics=BacktestMetricsModel(**metrics),
        equity_curve=equity_curve,
        trades=engine.trades,
        report_text=report_text,
    )


@router.get("/symbols/search", tags=["Data"])
async def search_symbols(q: str = Query(..., min_length=1)):
    """Return basic info for a symbol."""
    try:
        info = fetcher.get_info(q.upper())
        return info
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
