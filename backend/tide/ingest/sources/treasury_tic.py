"""Treasury TIC source — Securities, Long-Term Transactions (SLT) global holdings.

URL: https://ticdata.treasury.gov/Publish/slt1d_globl.csv

The CSV is per-country monthly holdings of US long-term securities. Columns include
Treasury, Agency, Corporate Bonds, and Corporate Stocks (in millions USD). We sum
the "Corporate Stocks" column across all countries per month to get global foreign
holdings of US equities.

Note this is the *holdings* table, not the *flows* table. Treasury publishes flows
separately as part of the monthly TIC press release (Excel attachments) which are
harder to scrape. Holdings YoY % growth captures the same accumulation/disposal
dynamic — when foreigners are buying, holdings grow faster than the market; when
selling, slower or shrinking.
"""
from __future__ import annotations

import csv
import io
import time
from datetime import date, datetime
from typing import Optional

import httpx

URL = "https://ticdata.treasury.gov/Publish/slt1d_globl.csv"


class TICFetchError(RuntimeError):
    pass


def fetch_global_corporate_stock_holdings(
    *,
    retries: int = 3,
) -> list[tuple[date, float]]:
    """Returns monthly (date, total_millions_usd) of foreign-held US corporate stocks.

    The first day of the month is used as the date stamp. Values are aggregated across
    all reporting countries.
    """
    headers = {"User-Agent": "Mozilla/5.0 (TIDE; +https://github.com/local)"}
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = httpx.get(URL, headers=headers, timeout=60.0, follow_redirects=True)
            r.raise_for_status()
            text = r.text
            break
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise TICFetchError(f"TIC fetch failed: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))
    else:
        raise last_exc or TICFetchError("unreachable")

    # CSV has many leading blank rows + a multi-line header. Data rows are
    # ("Country", country_code, "YYYY-MM", total, treasury, agency, corp_bonds, corp_stocks)
    by_month: dict[str, float] = {}
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if len(row) < 8:
            continue
        country, _code, month, _total, _tres, _agency, _corp_bonds, corp_stocks, *_ = row
        country = country.strip()
        month = month.strip()
        if not country or country in ("Country Name", "------------"):
            continue
        if not (len(month) == 7 and month[4] == "-"):
            continue  # not YYYY-MM
        try:
            val = float(corp_stocks.strip().replace(",", ""))
        except (ValueError, AttributeError):
            continue
        # Skip "Grand Total" / "Major" aggregate rows — sum only individual countries.
        # The data file is country-grouped; aggregate rows have country names like
        # "Grand Total" / "Major Foreign Holders" which we must exclude.
        low = country.lower()
        if any(tag in low for tag in ("grand total", "major foreign", "all other", "subtotal")):
            continue
        by_month[month] = by_month.get(month, 0.0) + val

    if not by_month:
        raise TICFetchError("TIC SLT parsed but no monthly totals computed")

    out: list[tuple[date, float]] = []
    for month in sorted(by_month):
        d = datetime.strptime(month + "-01", "%Y-%m-%d").date()
        out.append((d, by_month[month]))
    return out
