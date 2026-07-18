"""Source connector for yahoo."""
from typing import Any, Optional
from signal_aggregator.sources._shared import fetch_generic_signal


async def fetch_yahoo_signal(connector, symbol: str, timeframe: str, *, session: Optional[Any]) -> Optional[Any]:
    return await fetch_generic_signal(connector, symbol, timeframe, session=session)
