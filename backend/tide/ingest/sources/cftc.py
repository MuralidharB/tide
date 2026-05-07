"""CFTC source — Commitments of Traders weekly history.

Two endpoints in play:
  - history:    https://www.cftc.gov/files/dea/history/fut_fin_txt_<YEAR>.zip
                Contains FinFutYY.txt, the Traders in Financial Futures (TFF) report
                for the entire year. 2010+.
  - current week: https://www.cftc.gov/dea/newcot/FinFutWk.txt
                The single most recent week's TFF report.

TLS note: cftc.gov serves a cert chain that fails verification on many CA bundles
(curl errors with code 60 by default). We disable verification for cftc.gov only —
the data is public, we don't authenticate, and the alternative is shipping a
custom CA bundle. Don't extend `verify=False` to other sources.
"""
from __future__ import annotations

import csv
import io
import re
import time
import zipfile
from datetime import date, datetime
from typing import Optional

import httpx

YEAR_URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
CURRENT_URL = "https://www.cftc.gov/dea/newcot/FinFutWk.txt"

UA = "Mozilla/5.0 (TIDE; +https://github.com/local)"


class CftcFetchError(RuntimeError):
    pass


def _get(url: str, *, retries: int = 3) -> bytes:
    headers = {"User-Agent": UA}
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = httpx.get(url, headers=headers, timeout=60.0, verify=False, follow_redirects=True)
            r.raise_for_status()
            return r.content
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt == retries - 1:
                raise CftcFetchError(f"CFTC fetch failed: {url}: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))
    raise last_exc or CftcFetchError("unreachable")


EMINI_SP500_RE = re.compile(r"^E-MINI S&P 500( STOCK INDEX)? -")
"""Matches both the current ('E-MINI S&P 500 -') and legacy ('E-MINI S&P 500 STOCK INDEX -')
contract names CFTC has used. Excludes the Micro contract ('MICRO E-MINI S&P 500 INDEX -')."""


def fetch_tff_history(
    contract_pattern: re.Pattern[str],
    start_year: int = 2010,
    end_year: Optional[int] = None,
) -> list[list[str]]:
    """Pull weekly TFF rows where row[0] matches `contract_pattern` across multiple years.

    Returns raw CSV rows (lists of strings) in chronological order, deduplicated by date.
    The caller parses the columns — fields differ between TFF and legacy reports.
    """
    if end_year is None:
        end_year = datetime.now().year
    out: list[list[str]] = []
    for year in range(start_year, end_year + 1):
        url = YEAR_URL.format(year=year)
        try:
            blob = _get(url)
        except CftcFetchError:
            continue  # year may not exist yet (current year early in Jan); skip
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            txt_name = next((n for n in zf.namelist() if n.endswith(".txt")), None)
            if not txt_name:
                continue
            with zf.open(txt_name) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
                reader = csv.reader(text)
                next(reader, None)  # header
                for row in reader:
                    if row and contract_pattern.match(row[0].strip()):
                        out.append(row)
    # Append current week (in case it's newer than the latest year zip)
    try:
        current = _get(CURRENT_URL).decode("utf-8", errors="replace")
        for row in csv.reader(io.StringIO(current)):
            if row and contract_pattern.match(row[0].strip()):
                out.append(row)
    except CftcFetchError:
        pass

    # Deduplicate on report date (column index 2 in TFF)
    seen: set[str] = set()
    deduped: list[list[str]] = []
    for r in out:
        try:
            d = r[2].strip()
        except IndexError:
            continue
        if d in seen:
            continue
        seen.add(d)
        deduped.append(r)
    deduped.sort(key=lambda r: r[2])
    return deduped


def parse_emini_sp500_spec_net_pct(rows: list[list[str]]) -> list[tuple[date, float]]:
    """Compute net leveraged-money position as % of OI for E-MINI S&P 500.

    TFF columns (0-indexed):
       0  Market_and_Exchange_Names
       2  Report_Date_as_YYYY-MM-DD
       7  Open_Interest_All
       8  Dealer_Positions_Long_All
       9  Dealer_Positions_Short_All
      11  Asset_Mgr_Positions_Long_All
      12  Asset_Mgr_Positions_Short_All
      14  Lev_Money_Positions_Long_All
      15  Lev_Money_Positions_Short_All

    "Spec" in the mockup = leveraged money (hedge funds, CTAs, etc.) which is the
    cleanest fast-money proxy. Asset managers are slower / benchmark-oriented.
    """
    out: list[tuple[date, float]] = []
    for r in rows:
        try:
            d = datetime.strptime(r[2].strip(), "%Y-%m-%d").date()
            oi = float(r[7].strip().replace(",", ""))
            lev_long = float(r[14].strip().replace(",", ""))
            lev_short = float(r[15].strip().replace(",", ""))
        except (IndexError, ValueError):
            continue
        if oi <= 0:
            continue
        net_pct = (lev_long - lev_short) / oi * 100
        out.append((d, net_pct))
    out.sort(key=lambda x: x[0])
    return out
