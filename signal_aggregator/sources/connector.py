"""
Source connectors for 10 global signal providers
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SignalDirection(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class SourceName(str, Enum):
    POLYGON = "Polygon.io"
    TRADINGVIEW = "TradingView"
    BLOOMBERG = "Bloomberg"
    FINVIZ = "FinViz"
    SEEKING_ALPHA = "SeekingAlpha"
    YAHOO_FINANCE = "YahooFinance"
    ALPHA_VANTAGE = "AlphaVantage"
    MARKET_WATCH = "MarketWatch"
    THINKORSWIM = "ThinkorSwim"
    STOCKTWITS = "StockTwits"


# Historical accuracy weights per source
SOURCE_ACCURACY = {
    SourceName.POLYGON: 0.94,
    SourceName.BLOOMBERG: 0.90,
    SourceName.THINKORSWIM: 0.89,
    SourceName.ALPHA_VANTAGE: 0.88,
    SourceName.MARKET_WATCH: 0.88,
    SourceName.TRADINGVIEW: 0.87,
    SourceName.YAHOO_FINANCE: 0.86,
    SourceName.FINVIZ: 0.86,
    SourceName.SEEKING_ALPHA: 0.85,
    SourceName.STOCKTWITS: 0.76,
}


@dataclass
class SourceSignal:
    """Signal from a single source"""
    source: SourceName
    symbol: str
    timeframe: str
    direction: SignalDirection
    confidence: float          # 0.0 – 1.0
    price: float
    timestamp: datetime
    indicators: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0  # set by validator


class BaseSourceConnector(ABC):
    """Abstract base for every source connector"""

    source_name: SourceName
    base_accuracy: float

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_accuracy = SOURCE_ACCURACY.get(self.source_name, 0.80)

    @abstractmethod
    async def fetch_signal(
        self,
        symbol: str,
        timeframe: str,
        *,
        session: Optional[Any] = None,
    ) -> Optional[SourceSignal]:
        """Fetch signal for a given symbol + timeframe."""

    async def fetch_signals_batch(
        self,
        symbols: List[str],
        timeframe: str,
        *,
        session: Optional[Any] = None,
    ) -> List[SourceSignal]:
        tasks = [self.fetch_signal(sym, timeframe, session=session) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: List[SourceSignal] = []
        for res in results:
            if isinstance(res, SourceSignal):
                signals.append(res)
            elif isinstance(res, Exception):
                logger.warning("[%s] fetch error: %s", self.source_name.value, res)
        return signals


# ─── Concrete connectors ──────────────────────────────────────────────────────

class PolygonConnector(BaseSourceConnector):
    source_name = SourceName.POLYGON

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._polygon import fetch_polygon_signal
        return await fetch_polygon_signal(self, symbol, timeframe, session=session)


class TradingViewConnector(BaseSourceConnector):
    source_name = SourceName.TRADINGVIEW

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._tradingview import fetch_tradingview_signal
        return await fetch_tradingview_signal(self, symbol, timeframe, session=session)


class BloombergConnector(BaseSourceConnector):
    source_name = SourceName.BLOOMBERG

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._bloomberg import fetch_bloomberg_signal
        return await fetch_bloomberg_signal(self, symbol, timeframe, session=session)


class FinVizConnector(BaseSourceConnector):
    source_name = SourceName.FINVIZ

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._finviz import fetch_finviz_signal
        return await fetch_finviz_signal(self, symbol, timeframe, session=session)


class SeekingAlphaConnector(BaseSourceConnector):
    source_name = SourceName.SEEKING_ALPHA

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._seeking_alpha import fetch_seeking_alpha_signal
        return await fetch_seeking_alpha_signal(self, symbol, timeframe, session=session)


class YahooFinanceConnector(BaseSourceConnector):
    source_name = SourceName.YAHOO_FINANCE

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._yahoo import fetch_yahoo_signal
        return await fetch_yahoo_signal(self, symbol, timeframe, session=session)


class AlphaVantageConnector(BaseSourceConnector):
    source_name = SourceName.ALPHA_VANTAGE

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._alpha_vantage import fetch_alpha_vantage_signal
        return await fetch_alpha_vantage_signal(self, symbol, timeframe, session=session)


class MarketWatchConnector(BaseSourceConnector):
    source_name = SourceName.MARKET_WATCH

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._marketwatch import fetch_marketwatch_signal
        return await fetch_marketwatch_signal(self, symbol, timeframe, session=session)


class ThinkorSwimConnector(BaseSourceConnector):
    source_name = SourceName.THINKORSWIM

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._thinkorswim import fetch_thinkorswim_signal
        return await fetch_thinkorswim_signal(self, symbol, timeframe, session=session)


class StockTwitsConnector(BaseSourceConnector):
    source_name = SourceName.STOCKTWITS

    async def fetch_signal(self, symbol: str, timeframe: str, *, session=None) -> Optional[SourceSignal]:
        from signal_aggregator.sources._stocktwits import fetch_stocktwits_signal
        return await fetch_stocktwits_signal(self, symbol, timeframe, session=session)


# ─── Registry ─────────────────────────────────────────────────────────────────

ALL_CONNECTORS: Dict[SourceName, type] = {
    SourceName.POLYGON: PolygonConnector,
    SourceName.TRADINGVIEW: TradingViewConnector,
    SourceName.BLOOMBERG: BloombergConnector,
    SourceName.FINVIZ: FinVizConnector,
    SourceName.SEEKING_ALPHA: SeekingAlphaConnector,
    SourceName.YAHOO_FINANCE: YahooFinanceConnector,
    SourceName.ALPHA_VANTAGE: AlphaVantageConnector,
    SourceName.MARKET_WATCH: MarketWatchConnector,
    SourceName.THINKORSWIM: ThinkorSwimConnector,
    SourceName.STOCKTWITS: StockTwitsConnector,
}


class SourceConnector:
    """Facade: collects signals from all 10 sources in parallel."""

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        api_keys = api_keys or {}
        self._connectors: List[BaseSourceConnector] = [
            cls(api_key=api_keys.get(name.value))
            for name, cls in ALL_CONNECTORS.items()
        ]

    async def collect_all(
        self,
        symbol: str,
        timeframe: str,
        *,
        session: Optional[Any] = None,
    ) -> List[SourceSignal]:
        """Fetch signals from all 10 sources concurrently."""
        tasks = [
            connector.fetch_signal(symbol, timeframe, session=session)
            for connector in self._connectors
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals: List[SourceSignal] = []
        for res in results:
            if isinstance(res, SourceSignal):
                signals.append(res)
            elif isinstance(res, Exception):
                logger.warning("Source error: %s", res)
        return signals
