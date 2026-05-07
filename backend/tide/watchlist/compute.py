"""Watchlist compute — joins stored prices with hardcoded metadata."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import duckdb

from tide.watchlist import BENCHMARK, TICKERS, WatchlistTicker


@dataclass(frozen=True)
class WatchlistRow:
    ticker: str
    name: str
    sub: str
    price: Optional[float]
    target: float
    fwd_pe: str
    status: str
    return_30d: Optional[float]               # ticker total return over last 30 trading days
    return_30d_relative: Optional[float]      # ticker minus benchmark over same window
    sparkline: list[float]                    # last 30 closes, raw price
    as_of: Optional[date]


def _load_closes(conn: duckdb.DuckDBPyConnection, ticker: str, n: int = 60) -> list[tuple[date, float]]:
    rows = conn.execute(
        "SELECT ts, value FROM observations WHERE metric_id = ? ORDER BY ts DESC LIMIT ?",
        [f"wl_{ticker}", n],
    ).fetchall()
    return [(r[0], r[1]) for r in reversed(rows)]


def _return_n_back(closes: list[tuple[date, float]], n: int) -> Optional[float]:
    if len(closes) < n + 1:
        return None
    latest = closes[-1][1]
    prior = closes[-(n + 1)][1]
    if prior <= 0:
        return None
    return latest / prior - 1


def compute_watchlist(conn: duckdb.DuckDBPyConnection) -> list[WatchlistRow]:
    bench_closes = _load_closes(conn, BENCHMARK, n=60)
    bench_30d = _return_n_back(bench_closes, 30)

    out: list[WatchlistRow] = []
    for t in TICKERS:
        closes = _load_closes(conn, t.ticker, n=60)
        if not closes:
            out.append(WatchlistRow(
                ticker=t.ticker, name=t.name, sub=t.sub,
                price=None, target=t.target_price, fwd_pe=t.fwd_pe, status=t.status,
                return_30d=None, return_30d_relative=None,
                sparkline=[], as_of=None,
            ))
            continue
        latest_ts, latest_close = closes[-1]
        ret_30 = _return_n_back(closes, 30)
        rel = (ret_30 - bench_30d) if (ret_30 is not None and bench_30d is not None) else None
        spark = [c for _, c in closes[-30:]]

        out.append(WatchlistRow(
            ticker=t.ticker, name=t.name, sub=t.sub,
            price=latest_close, target=t.target_price, fwd_pe=t.fwd_pe, status=t.status,
            return_30d=ret_30, return_30d_relative=rel,
            sparkline=spark, as_of=latest_ts,
        ))
    return out
