"""FRED data source — wraps fredapi for series fetching."""
from __future__ import annotations

import time
from datetime import date
from typing import Optional

from fredapi import Fred

from tide.config import settings


class FredKeyMissing(RuntimeError):
    """Raised when FRED_API_KEY is not configured."""


def _client() -> Fred:
    if not settings.fred_api_key:
        raise FredKeyMissing(
            "FRED_API_KEY not set. Get one at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return Fred(api_key=settings.fred_api_key)


def fetch_series(
    series_id: str,
    start: Optional[str] = None,
    *,
    retries: int = 3,
) -> list[tuple[date, float]]:
    """Pull a FRED series. Returns (observation_date, value) tuples sorted ascending.

    NaN observations (FRED uses '.' for missing) are dropped. FRED occasionally
    returns transient 5xx errors; we retry with exponential backoff.
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            series = _client().get_series(series_id, observation_start=start)
            break
        except ValueError as exc:
            # fredapi raises ValueError for HTTP errors; the message is FRED's
            last_exc = exc
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    else:  # pragma: no cover - unreachable due to break/raise above
        raise last_exc or RuntimeError("fredapi exhausted retries")

    out: list[tuple[date, float]] = []
    for ts, val in series.items():
        if val is None or (isinstance(val, float) and (val != val)):  # NaN check
            continue
        out.append((ts.date(), float(val)))
    return out
