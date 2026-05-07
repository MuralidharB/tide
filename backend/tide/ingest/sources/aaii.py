"""AAII Investor Sentiment Survey — weekly bullish/neutral/bearish poll.

URL: https://www.aaii.com/files/surveys/sentiment.xls

The file is a binary OLE2 .xls (Excel 97-2003 format), parseable with the `xlrd`
package. Sheet "SENTIMENT" has weekly rows with columns:
   0  Reported Date (Excel serial)
   1  Bullish (0..1 fraction)
   2  Neutral
   3  Bearish
   4  Total (always 1.0)
   5  8-week MA
   6  Bull-Bear Spread (Bullish - Bearish)
   7  Bullish historical average

History begins ~1987-08-14, updates each Thursday.

AAII gates the file behind browser-shaped headers (User-Agent + Referer) and
intermittently 403s automated clients. We retry on transient failures.
"""
from __future__ import annotations

import io
import time
from datetime import date
from typing import Optional

import httpx
import xlrd
from xlrd.xldate import xldate_as_datetime

URL = "https://www.aaii.com/files/surveys/sentiment.xls"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


class AAIIFetchError(RuntimeError):
    pass


def _fetch_xls_bytes(*, retries: int = 4) -> bytes:
    headers = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.aaii.com/sentimentsurvey",
    }
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = httpx.get(URL, headers=headers, timeout=60.0, follow_redirects=True)
            r.raise_for_status()
            # The 403 page is HTML; reject if we got that instead of the binary xls.
            if r.content[:4] != b"\xd0\xcf\x11\xe0":  # OLE2 magic
                raise AAIIFetchError(
                    f"AAII returned non-xls content (likely 403 page); attempt {attempt + 1}"
                )
            return r.content
        except (httpx.HTTPError, httpx.TimeoutException, AAIIFetchError) as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise AAIIFetchError(f"AAII fetch failed after {retries} attempts: {exc}") from exc
            time.sleep(2.0 * (attempt + 1))
    raise last_exc or AAIIFetchError("unreachable")


def fetch_bull_bear_spread() -> list[tuple[date, float]]:
    """Returns weekly (date, bull_bear_spread_in_percentage_points).

    The spread is in percentage points (e.g. +18.0 means 18pp more bulls than bears),
    matching the mockup's display convention.
    """
    blob = _fetch_xls_bytes()
    wb = xlrd.open_workbook(file_contents=blob, on_demand=True)
    sh = wb.sheet_by_name("SENTIMENT")
    out: list[tuple[date, float]] = []
    for r in range(sh.nrows):
        v0 = sh.cell_value(r, 0)
        v6 = sh.cell_value(r, 6)
        if not isinstance(v0, (int, float)) or v0 <= 0:
            continue  # skip header / count rows
        if not isinstance(v6, (int, float)):
            continue
        try:
            d = xldate_as_datetime(v0, wb.datemode).date()
        except (ValueError, OverflowError):
            continue
        out.append((d, float(v6) * 100))
    out.sort(key=lambda x: x[0])
    if not out:
        raise AAIIFetchError("AAII xls parsed but no rows extracted")
    return out
