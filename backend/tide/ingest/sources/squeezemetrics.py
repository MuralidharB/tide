"""SqueezeMetrics source — public CSV for DIX (Dark Index, dealer-positioning proxy).

DIX series at https://squeezemetrics.com/monitor/static/DIX.csv goes back to 2011-05.
CSV columns: date, price (SPX close), dix, gex. We only consume `dix` and `date`.
"""
from __future__ import annotations

import csv
import io
import time
from datetime import date, datetime
from typing import Optional

import httpx

DIX_URL = "https://squeezemetrics.com/monitor/static/DIX.csv"


class SqueezeMetricsFetchError(RuntimeError):
    pass


def fetch_dix(start: Optional[str] = None, *, retries: int = 3) -> list[tuple[date, float]]:
    headers = {"User-Agent": "Mozilla/5.0 (TIDE; +https://github.com/local)"}
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = httpx.get(DIX_URL, headers=headers, timeout=30.0)
            r.raise_for_status()
            break
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise SqueezeMetricsFetchError(f"DIX fetch failed: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))

    out: list[tuple[date, float]] = []
    cutoff = datetime.fromisoformat(start).date() if start else None
    reader = csv.DictReader(io.StringIO(r.text))
    for row in reader:
        try:
            d = datetime.fromisoformat(row["date"]).date()
            v = float(row["dix"])
        except (KeyError, ValueError):
            continue
        if cutoff and d < cutoff:
            continue
        out.append((d, v))
    if not out:
        raise SqueezeMetricsFetchError("DIX CSV parsed but contained no rows")
    out.sort(key=lambda x: x[0])
    return out
