"""
Data fetcher - retrieves stock price data from multiple sources.
"""
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger
import yfinance as yf


class DataFetcher:
    """Fetches OHLCV data from financial data providers."""

    def __init__(self):
        self.cache: dict = {}

    def fetch(
        self,
        symbol: str,
        period: str = "2y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a given symbol.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'MSFT')
            period: Data period ('1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max')
            interval: Data interval ('1m','2m','5m','15m','30m','60m','90m','1h','1d','5d','1wk','1mo','3mo')
            start: Start date string 'YYYY-MM-DD'
            end: End date string 'YYYY-MM-DD'

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        cache_key = f"{symbol}_{period}_{interval}_{start}_{end}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key].copy()

        try:
            ticker = yf.Ticker(symbol)
            if start and end:
                df = ticker.history(start=start, end=end, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                raise ValueError(f"No data returned for symbol: {symbol}")

            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)

            self.cache[cache_key] = df.copy()
            logger.info(f"Fetched {len(df)} rows for {symbol}")
            return df

        except Exception as exc:
            logger.error(f"Error fetching data for {symbol}: {exc}")
            raise

    def fetch_multiple(
        self, symbols: list, period: str = "2y", interval: str = "1d"
    ) -> dict:
        """Fetch data for multiple symbols."""
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.fetch(symbol, period=period, interval=interval)
            except Exception as exc:
                logger.warning(f"Skipping {symbol} due to error: {exc}")
        return result

    def get_info(self, symbol: str) -> dict:
        """Get company info for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "currency": info.get("currency", "USD"),
            }
        except Exception as exc:
            logger.warning(f"Could not get info for {symbol}: {exc}")
            return {"symbol": symbol}

    def clear_cache(self):
        """Clear the in-memory cache."""
        self.cache.clear()
        logger.debug("Cache cleared")
