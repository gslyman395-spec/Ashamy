# توثيق API - Ashamy

Base URL: `http://localhost:8000/api/v1`

## GET /health

فحص حالة الخادم.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-01-15T12:00:00"
}
```

---

## POST /analyze

تحليل سهم وإرجاع الإشارات والتوصيات.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "period": "2y",
  "interval": "1d",
  "start": null,
  "end": null,
  "run_ml": false
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "period": "2y",
  "interval": "1d",
  "total_bars": 502,
  "candles": [...],
  "signals": [
    {
      "date": "2024-01-10",
      "price": 185.5,
      "signal": 1,
      "recommendation": "BUY",
      "confidence": 0.73,
      "indicators": {
        "rsi": 42.5,
        "macd": 0.234,
        ...
      }
    }
  ],
  "latest_recommendation": "BUY",
  "latest_confidence": 0.73,
  "latest_indicators": {...},
  "strategy_agreement": {
    "ma": 1,
    "rsi": 1,
    "macd": 0,
    ...
  }
}
```

---

## POST /backtest

اختبار استراتيجية على بيانات تاريخية.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "period": "2y",
  "initial_capital": 100000,
  "commission": 0.001,
  "slippage": 0.0005
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "period": "2y",
  "metrics": {
    "total_return": 35.2,
    "cagr": 16.8,
    "final_equity": 135200,
    "max_drawdown": -12.5,
    "sharpe_ratio": 1.85,
    "sortino_ratio": 2.1,
    "calmar_ratio": 1.34,
    "total_trades": 48,
    "win_rate": 62.5,
    "avg_win_pct": 3.2,
    "avg_loss_pct": -1.8,
    "profit_factor": 2.1,
    "expectancy": 1.25
  },
  "equity_curve": [
    {"date": "2022-01-03", "equity": 100000},
    ...
  ],
  "trades": [...],
  "report_text": "..."
}
```

---

## GET /symbols/search?q={symbol}

البحث عن معلومات شركة.

**Example:** `/symbols/search?q=AAPL`

**Response:**
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "market_cap": 3000000000000,
  "currency": "USD"
}
```
