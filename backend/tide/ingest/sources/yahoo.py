"""Yahoo Finance chart API — direct HTTP, no yfinance dependency.

We hit https://query1.finance.yahoo.com/v8/finance/chart/<symbol> directly. The endpoint
is the same one yfinance scrapes; calling it ourselves avoids yfinance's auth churn (which
breaks every few months as Yahoo tweaks crumb/cookie requirements).

The response shape we consume:
  result[0].timestamp           — array of unix seconds, one per bar
  result[0].indicators.quote[0].close — array of closes (may contain nulls)
"""
from __future__ import annotations

import time
from datetime import date, datetime, timezone
from typing import Optional

import httpx

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


class YahooFetchError(RuntimeError):
    pass


def fetch_close_series(
    symbol: str,
    start: Optional[str] = None,
    *,
    interval: str = "1d",
    retries: int = 3,
) -> list[tuple[date, float]]:
    """Pull daily closes for a Yahoo ticker. Symbols with carets like '^VIX' are URL-safe.

    `start` is an ISO date string. If omitted, defaults to 1990-01-01 (Yahoo will clip
    to whatever its earliest data is).
    """
    period1 = int(datetime.fromisoformat(start or "1990-01-01").replace(tzinfo=timezone.utc).timestamp())
    period2 = int(datetime.now(tz=timezone.utc).timestamp())
    url = CHART_URL.format(symbol=symbol)
    params = {
        "period1": period1,
        "period2": period2,
        "interval": interval,
        "includePrePost": "false",
        "events": "div,splits",
    }
    headers = {"User-Agent": "Mozilla/5.0 (TIDE; +https://github.com/local)"}

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = httpx.get(url, params=params, headers=headers, timeout=30.0)
            r.raise_for_status()
            payload = r.json()
            break
        except (httpx.HTTPError, httpx.TimeoutException, ValueError) as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise YahooFetchError(f"Yahoo fetch failed for {symbol!r}: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))

    chart = payload.get("chart", {})
    err = chart.get("error")
    if err:
        raise YahooFetchError(f"Yahoo error for {symbol!r}: {err}")
    results = chart.get("result")
    if not results:
        raise YahooFetchError(f"Yahoo returned no result for {symbol!r}")
    r0 = results[0]
    timestamps: list[int] = r0.get("timestamp") or []
    closes: list[float | None] = (
        r0.get("indicators", {}).get("quote", [{}])[0].get("close") or []
    )
    if not timestamps:
        raise YahooFetchError(f"Yahoo returned empty timestamp array for {symbol!r}")

    out: list[tuple[date, float]] = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        out.append((d, float(close)))
    if not out:
        raise YahooFetchError(f"Yahoo returned no valid closes for {symbol!r}")
    return out


def fetch_close_volume(
    symbol: str,
    start: Optional[str] = None,
    *,
    retries: int = 3,
) -> list[tuple[date, float, float]]:
    """Pull (date, close, volume) for a Yahoo ticker. Used by Amihud illiquidity metrics.

    Volume is in raw shares; multiply by close to get dollar volume. Bars where either
    close or volume is null/zero are dropped.
    """
    period1 = int(datetime.fromisoformat(start or "1990-01-01").replace(tzinfo=timezone.utc).timestamp())
    period2 = int(datetime.now(tz=timezone.utc).timestamp())
    url = CHART_URL.format(symbol=symbol)
    params = {
        "period1": period1,
        "period2": period2,
        "interval": "1d",
        "includePrePost": "false",
        "events": "div,splits",
    }
    headers = {"User-Agent": "Mozilla/5.0 (TIDE; +https://github.com/local)"}

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = httpx.get(url, params=params, headers=headers, timeout=30.0)
            r.raise_for_status()
            payload = r.json()
            break
        except (httpx.HTTPError, httpx.TimeoutException, ValueError) as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise YahooFetchError(f"Yahoo fetch failed for {symbol!r}: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))

    chart = payload.get("chart", {})
    if chart.get("error"):
        raise YahooFetchError(f"Yahoo error for {symbol!r}: {chart['error']}")
    results = chart.get("result")
    if not results:
        raise YahooFetchError(f"Yahoo returned no result for {symbol!r}")
    r0 = results[0]
    timestamps = r0.get("timestamp") or []
    quote = r0.get("indicators", {}).get("quote", [{}])[0]
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    out: list[tuple[date, float, float]] = []
    for ts, close, vol in zip(timestamps, closes, volumes):
        if close is None or vol is None or vol == 0:
            continue
        d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        out.append((d, float(close), float(vol)))
    if not out:
        raise YahooFetchError(f"Yahoo returned no valid OHLCV bars for {symbol!r}")
    return out
